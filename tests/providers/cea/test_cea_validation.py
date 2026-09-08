"""Mutation proofs for the CEA adapter.

The provider tolerances are looser than RocketForge's own -- 1e-5 for state
identities and 1e-6 for element conservation, both because CEA's own constants
and solver residual demand it. Loosening a tolerance is only defensible if the
check still catches what it is for, so every relaxation here is paired with a
proof that a real defect still fails by orders of magnitude.

Each proof asserts the fixture **actually changed** before asserting that the
check notices. That is the Phase 4G lesson: a mutation test that mutates
nothing reports success on unmodified data and is worse than no test.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.physics.thermochemistry import (
    DEFAULT_THERMO_TOLERANCES,
    ChamberEquilibriumRequest,
    Composition,
    CompositionBasis,
    ElementalComposition,
    ElementalInventoryBasis,
    MixtureRatio,
    Species,
    ThermochemistryTolerances,
    check_element_balance,
    validate_chamber_gas,
)
from rocketforge.providers.cea import check_availability

_AVAILABILITY = check_availability()
CEA_PRESENT = _AVAILABILITY.is_usable
requires_cea = pytest.mark.skipif(
    not CEA_PRESENT,
    reason=(f"NASA CEA provider unavailable ({_AVAILABILITY.status.value}): "
            f"{_AVAILABILITY.detail or 'install requirements-thermochemistry.txt'}"),
)

#: The tolerances the provider actually validates with.
PROVIDER_TOLERANCES = ThermochemistryTolerances(
    state_identity_rel_tol=DEFAULT_THERMO_TOLERANCES.provider_identity_rel_tol,
    element_balance_rel_tol=DEFAULT_THERMO_TOLERANCES.provider_element_balance_rel_tol,
)

pytestmark = requires_cea


# ---------------------------------------------------------------------------
# the relaxations are real, and bounded
# ---------------------------------------------------------------------------


def test_the_provider_tolerances_are_looser_than_the_strict_ones():
    """Stated explicitly, so the relaxation is visible rather than buried."""
    assert (PROVIDER_TOLERANCES.state_identity_rel_tol
            > DEFAULT_THERMO_TOLERANCES.state_identity_rel_tol)
    assert (PROVIDER_TOLERANCES.element_balance_rel_tol
            > DEFAULT_THERMO_TOLERANCES.element_balance_rel_tol)
    assert PROVIDER_TOLERANCES.state_identity_rel_tol == 1e-5
    assert PROVIDER_TOLERANCES.element_balance_rel_tol == 1e-6


def test_a_real_solve_sits_well_inside_the_provider_tolerances(
        provider, lox_methane_request):
    """The relaxation is not sized to barely admit the provider."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    species = provider._species_for(state.provenance.species_set)
    report = validate_chamber_gas(state, species, tolerances=PROVIDER_TOLERANCES)
    assert report.valid
    assert report.max_residual < 1.0e-5
    # And the residual is dominated by the known constant difference, not noise.
    assert report.max_residual > 1.0e-9


# ---------------------------------------------------------------------------
# state identity mutation proofs, at the PROVIDER tolerance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field,factor,identity", [
    ("density", 1.01, "p = rho R T"),
    ("cv", 1.01, "cp - cv = R"),
    ("gas_constant", 1.01, "R = Ru / M"),
])
def test_a_one_percent_corruption_still_fails_at_provider_tolerance(
        provider, lox_methane_request, field, factor, identity):
    """1 % is three orders of magnitude above the constants discrepancy."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    original = getattr(state, field)
    corrupt = dataclasses.replace(state, **{field: original * factor})
    assert getattr(corrupt, field) != original, "the mutation must bite"

    report = validate_chamber_gas(corrupt, tolerances=PROVIDER_TOLERANCES)
    assert not report.valid
    assert identity in {c.identity for c in report.failures}


def test_a_corrupted_gamma_still_fails(provider, lox_methane_request):
    state = provider.solve_chamber(lox_methane_request).unwrap()
    corrupt = dataclasses.replace(state, gamma_frozen=state.gamma_frozen * 1.01)
    assert corrupt.gamma_frozen != state.gamma_frozen, "the mutation must bite"
    report = validate_chamber_gas(corrupt, tolerances=PROVIDER_TOLERANCES)
    assert not report.valid
    assert "gamma_frozen = cp / cv" in {c.identity for c in report.failures}


def test_a_thousandfold_molar_mass_error_is_caught(provider, lox_methane_request,
                                                   realistic_species=None):
    """The kg/kmol-versus-kg/mol slip, the classic adapter defect.

    Two variants, and they fail through different checks -- which is worth
    knowing, because only one of them is caught by the identity alone:

    * **M scaled, R not** -- the realistic bug, where a converted molar mass
      meets an unconverted gas constant. ``R = Ru / M`` catches it at once.
    * **M and R scaled together** -- self-consistent, so the identities are
      satisfied and cannot catch it. It is caught instead by comparing the
      state's molar mass against the one its own composition implies.
    """
    state = provider.solve_chamber(lox_methane_request).unwrap()
    species = provider._species_for(state.provenance.species_set)

    inconsistent = dataclasses.replace(state, molar_mass=state.molar_mass * 1000.0)
    assert inconsistent.molar_mass != state.molar_mass, "the mutation must bite"
    report = validate_chamber_gas(inconsistent, tolerances=PROVIDER_TOLERANCES)
    assert not report.valid
    assert "R = Ru / M" in {c.identity for c in report.failures}

    consistent = dataclasses.replace(
        state, molar_mass=state.molar_mass * 1000.0,
        gas_constant=state.gas_constant / 1000.0)
    assert consistent.molar_mass != state.molar_mass, "the mutation must bite"
    identities_only = validate_chamber_gas(consistent,
                                           tolerances=PROVIDER_TOLERANCES)
    assert "R = Ru / M" not in {c.identity for c in identities_only.failures}, (
        "a consistently scaled pair satisfies the identity, by construction")

    with_composition = validate_chamber_gas(consistent, species,
                                            tolerances=PROVIDER_TOLERANCES)
    assert not with_composition.valid
    assert "state M = composition M" in {
        c.identity for c in with_composition.failures}


def test_a_thousandfold_enthalpy_error_is_visible(provider, lox_methane_request):
    """kJ/kg left unconverted is a factor of 1000, not a nuance."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    unconverted = state.enthalpy / 1000.0
    assert abs(state.enthalpy - unconverted) > 1.0e5
    # A plausible chamber enthalpy is order 1e6 J/kg; 1e3 would be absurd.
    assert abs(state.enthalpy) > 1.0e5


# ---------------------------------------------------------------------------
# element balance mutation proofs, at the PROVIDER tolerance
# ---------------------------------------------------------------------------


def _reactant_composition(request: ChamberEquilibriumRequest) -> Composition:
    of = request.of_mass
    return Composition.from_fractions(
        {"CH4(L)": 1.0 / (1.0 + of), "O2(L)": of / (1.0 + of)},
        CompositionBasis.MASS_FRACTION)


def test_element_balance_passes_on_the_real_solve(provider, lox_methane_request):
    state = provider.solve_chamber(lox_methane_request).unwrap()
    species = provider._species_for(state.provenance.species_set,
                                    ("CH4(L)", "O2(L)"))
    check = check_element_balance(
        _reactant_composition(lox_methane_request), state.composition, species,
        basis=ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE,
        tolerances=PROVIDER_TOLERANCES)
    assert check.passed
    assert check.residual < 1.0e-7


def test_a_dropped_product_species_still_fails(provider, lox_methane_request):
    """The largest class of real defect, and it fails by orders of magnitude."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    species = provider._species_for(state.provenance.species_set,
                                    ("CH4(L)", "O2(L)"))
    fractions = dict(state.composition.fractions)
    removed = fractions.pop("H2O")
    assert removed > 0.4, "the species removed must actually matter"
    mutated = Composition.from_weights(fractions, CompositionBasis.MOLE_FRACTION)
    assert dict(mutated.fractions) != dict(state.composition.fractions), \
        "the mutation must bite"

    check = check_element_balance(
        _reactant_composition(lox_methane_request), mutated, species,
        basis=ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE,
        tolerances=PROVIDER_TOLERANCES)
    assert not check.passed
    assert check.residual > 1.0e-2, (
        "a dropped major species should fail by orders of magnitude, not "
        f"marginally; got {check.residual:.3e}")


def test_an_inverted_of_ratio_still_fails(provider, lox_methane_request):
    """F/O instead of O/F: the reactants no longer match the products."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    species = provider._species_for(state.provenance.species_set,
                                    ("CH4(L)", "O2(L)"))
    inverted = dataclasses.replace(
        lox_methane_request,
        oxidiser_fuel_ratio=MixtureRatio(1.0 / lox_methane_request.of_mass))
    correct_side = _reactant_composition(lox_methane_request)
    inverted_side = _reactant_composition(inverted)
    assert dict(inverted_side.fractions) != dict(correct_side.fractions), \
        "the mutation must bite"

    check = check_element_balance(
        inverted_side, state.composition, species,
        basis=ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE,
        tolerances=PROVIDER_TOLERANCES)
    assert not check.passed
    assert check.residual > 1.0e-2


def test_a_scaled_species_molar_mass_still_fails(provider, lox_methane_request):
    """A units slip on one species only -- the hardest of these to see."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    species = dict(provider._species_for(state.provenance.species_set,
                                         ("CH4(L)", "O2(L)")))
    original = species["H2O"]
    species["H2O"] = dataclasses.replace(original,
                                         molar_mass=original.molar_mass * 2.0)
    assert species["H2O"].molar_mass != original.molar_mass, "the mutation must bite"

    check = check_element_balance(
        _reactant_composition(lox_methane_request), state.composition, species,
        basis=ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE,
        tolerances=PROVIDER_TOLERANCES)
    assert not check.passed
    assert check.residual > 1.0e-2


def test_an_altered_elemental_formula_still_fails(provider, lox_methane_request):
    """CO2 declared as CO3 -- a curated-table error, which is the risk here."""
    state = provider.solve_chamber(lox_methane_request).unwrap()
    species = dict(provider._species_for(state.provenance.species_set,
                                         ("CH4(L)", "O2(L)")))
    original = species["CO2"]
    species["CO2"] = dataclasses.replace(
        original,
        formula=ElementalComposition.from_mapping({"C": 1.0, "O": 3.0}))
    assert species["CO2"].formula != original.formula, "the mutation must bite"

    check = check_element_balance(
        _reactant_composition(lox_methane_request), state.composition, species,
        basis=ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE,
        tolerances=PROVIDER_TOLERANCES)
    assert not check.passed
    # check_element_balance reports an IdentityCheck; the offending element is
    # named in its detail rather than as a field.
    assert "worst element O" in check.detail
    assert check.residual > 1.0e-2


def test_the_curated_formulas_agree_with_ceas_molar_masses(provider):
    """The curated table is checkable against the provider's own numbers.

    Multiplying each formula by standard atomic weights must reproduce CEA's
    molar mass to within the atomic-weight vintage difference. This is what
    makes a hand-curated formula table safe: it is verified, not trusted.
    """
    from rocketforge.providers.cea.species import (
        CEA_FORMULAS,
        CHO_PRODUCT_SPECIES,
        cea_molar_masses,
    )

    # IUPAC 2021 abridged standard atomic weights, used only as a cross-check.
    weights = {"C": 12.011, "H": 1.008, "O": 15.999}
    masses = cea_molar_masses(provider._cea(), CHO_PRODUCT_SPECIES)
    worst = 0.0
    for name in CHO_PRODUCT_SPECIES:
        implied = sum(weights[e] * n for e, n in CEA_FORMULAS[name].items())
        relative = abs(implied - masses[name]) / masses[name]
        worst = max(worst, relative)
        assert relative < 1.0e-3, (
            f"{name}: formula implies {implied:.6f} but CEA says "
            f"{masses[name]:.6f} kg/kmol")
    # The residual is the atomic-weight vintage difference, not an error.
    assert worst < 1.0e-4


# ---------------------------------------------------------------------------
# the provider rejects a converged-but-wrong result
# ---------------------------------------------------------------------------


def test_a_converged_result_failing_conservation_is_not_returned(
        provider, lox_methane_request, monkeypatch):
    """"The solver converged" is not the same claim as "atoms are conserved".

    A corrupted composition is injected after the solve; the provider must
    reject it with a diagnostic naming element conservation, not return it
    because CEA said it was fine.
    """
    import rocketforge.providers.cea.provider as provider_module

    real = provider_module.to_chamber_gas

    def corrupting(raw, species, request, provenance):
        state = real(raw, species, request, provenance)
        fractions = dict(state.composition.fractions)
        fractions.pop("H2O")
        return dataclasses.replace(
            state,
            composition=Composition.from_weights(
                fractions, CompositionBasis.MOLE_FRACTION,
                database=state.composition.database,
                database_version=state.composition.database_version))

    monkeypatch.setattr(provider_module, "to_chamber_gas", corrupting)
    solution = provider.solve_chamber(lox_methane_request)

    assert not solution.ok
    assert solution.value is None
    codes = {d.code for d in solution.diagnostics}
    assert "ELEMENT_BALANCE_VIOLATED" in codes
    message = next(d.message for d in solution.diagnostics
                   if d.code == "ELEMENT_BALANCE_VIOLATED")
    assert "conserve" in message, "the refusal must say what actually failed"
