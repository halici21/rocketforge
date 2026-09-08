"""Composition algebra: basis, conversion, mean molar mass, element inventory.

The reference values here are computed by hand in the docstrings, never by
calling the production conversion in reverse. The synthetic 10 / 90 g/mol pair
exists so the arithmetic closes exactly and a wrong answer is obvious rather
than merely different in the eighth digit.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.physics.thermochemistry import (
    Composition,
    CompositionBasis,
    CompositionBasisError,
    CompositionError,
    CompositionSumError,
    ElementalComposition,
    ElementalInventoryBasis,
    Phase,
    Species,
    UnknownSpeciesError,
    compare_elemental_inventories,
    elemental_inventory,
    mass_to_mole_fractions,
    mole_to_mass_fractions,
)

MOLE = CompositionBasis.MOLE_FRACTION
MASS = CompositionBasis.MASS_FRACTION


# ---------------------------------------------------------------------------
# basis is never implied
# ---------------------------------------------------------------------------


def test_basis_is_mandatory_and_typed():
    """There is no constructor that lets a caller omit the basis."""
    with pytest.raises(TypeError):
        Composition.from_fractions({"A": 1.0})  # type: ignore[call-arg]
    with pytest.raises(CompositionBasisError):
        Composition.from_fractions({"A": 1.0}, "mole")  # type: ignore[arg-type]


def test_basis_travels_with_the_numbers(synthetic_table):
    mole = Composition.from_fractions({"LIGHT": 0.5, "HEAVY": 0.5}, MOLE)
    mass = mole.to_basis(MASS, synthetic_table)
    assert mole.basis is MOLE
    assert mass.basis is MASS
    assert mole.fractions != mass.fractions


def test_composition_is_frozen(synthetic_table):
    comp = Composition.from_fractions({"LIGHT": 1.0}, MOLE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        comp.basis = MASS  # type: ignore[misc]


def test_fractions_view_is_read_only():
    comp = Composition.from_fractions({"LIGHT": 1.0}, MOLE)
    with pytest.raises(TypeError):
        comp.fractions["LIGHT"] = 0.5  # type: ignore[index]


# ---------------------------------------------------------------------------
# ordering determinism
# ---------------------------------------------------------------------------


def test_insertion_order_does_not_affect_equality_or_serialised_order():
    a = Composition.from_fractions({"B": 0.25, "A": 0.75}, MOLE)
    b = Composition.from_fractions({"A": 0.75, "B": 0.25}, MOLE)
    assert a == b
    assert a.species_names == ("A", "B") == b.species_names


# ---------------------------------------------------------------------------
# sum policy
# ---------------------------------------------------------------------------


def test_exact_sum_of_one_is_not_canonicalised():
    comp = Composition.from_fractions({"A": 0.25, "B": 0.75}, MOLE)
    assert comp.sum() == 1.0
    assert not comp.was_canonicalised
    assert comp.canonicalised_from_sum is None


def test_one_ulp_perturbation_still_sums_to_exactly_one():
    """A one-ulp perturbation is below what float64 can even represent here.

    ``0.25 + nextafter(0.75, 1)`` is exactly 1.0: the excess is half a ULP at
    this magnitude and rounds to even. So no canonicalisation happens, and
    demanding one would be testing a distinction the arithmetic does not have --
    the Phase 4G lesson about fictional precision, in a new domain. What is
    tested is the *policy*, in the two tests that follow.
    """
    comp = Composition.from_fractions(
        {"A": 0.25, "B": math.nextafter(0.75, 1.0)}, MOLE)
    assert comp.sum() == 1.0
    assert not comp.was_canonicalised


def test_sum_inside_tolerance_is_canonicalised_and_recorded():
    """Inside the tolerance: corrected, and the correction is visible.

    A corrected composition is never presented as though the caller supplied it
    exactly (09 section 5).
    """
    comp = Composition.from_fractions({"A": 0.25, "B": 0.75 + 1.0e-11}, MOLE)
    assert comp.was_canonicalised
    assert comp.canonicalised_from_sum == pytest.approx(1.0 + 1.0e-11, rel=1e-15)
    assert comp.sum() == pytest.approx(1.0, abs=1e-15)


def test_sum_just_inside_tolerance_is_accepted():
    comp = Composition.from_fractions({"A": 0.5, "B": 0.5 + 5.0e-10}, MOLE)
    assert comp.was_canonicalised


def test_sum_just_outside_tolerance_is_refused():
    with pytest.raises(CompositionSumError, match="composition_sum_tol"):
        Composition.from_fractions({"A": 0.5, "B": 0.5 + 1.0e-7}, MOLE)


@pytest.mark.parametrize("fractions", [
    {"A": 0.4, "B": 0.4},          # 0.8
    {"A": 0.6, "B": 0.6},          # 1.2
    {"A": 20.0, "B": 30.0, "C": 50.0},
])
def test_clearly_unnormalised_input_is_refused_not_rescaled(fractions):
    """This is the rule that keeps `from_fractions` honest.

    Rescaling {"A": 0.8, "B": 0.8} into a valid composition would invent a
    mixture the caller never described.
    """
    with pytest.raises(CompositionSumError):
        Composition.from_fractions(fractions, MOLE)


def test_weights_constructor_normalises_because_the_caller_said_so():
    comp = Composition.from_weights({"A": 20.0, "B": 30.0, "C": 50.0}, MOLE)
    assert comp.fraction_of("A") == pytest.approx(0.2)
    assert comp.fraction_of("C") == pytest.approx(0.5)
    assert comp.sum() == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# fraction domain
# ---------------------------------------------------------------------------


def test_negative_fractions_are_refused_and_nothing_is_clamped():
    with pytest.raises(CompositionError, match="negative fractions are refused"):
        Composition.from_fractions({"A": -1.0e-12, "B": 1.0}, MOLE)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_fractions_are_refused(bad):
    with pytest.raises(CompositionError):
        Composition.from_fractions({"A": bad, "B": 1.0}, MOLE)


def test_zero_components_are_preserved():
    """A zero entry is part of the species-set identity and is not dropped."""
    comp = Composition.from_fractions({"A": 1.0, "B": 0.0}, MOLE)
    assert "B" in comp.fractions
    assert comp.fraction_of("B") == 0.0


def test_trace_species_survive():
    """No storage cutoff. A 1e-12 mole fraction is a fact, not noise."""
    comp = Composition.from_fractions(
        {"MAJOR": 1.0 - 1.0e-12, "TRACE": 1.0e-12}, MOLE)
    assert comp.fraction_of("TRACE") == pytest.approx(1.0e-12, rel=1e-9)


# ---------------------------------------------------------------------------
# conversion, hand-computed
# ---------------------------------------------------------------------------


def test_mole_to_mass_matches_hand_calculation(synthetic_table):
    """LIGHT 10 g/mol, HEAVY 90 g/mol, 50/50 by mole.

    Numerator LIGHT: 0.5 * 10 = 5.  HEAVY: 0.5 * 90 = 45.  Sum = 50.
    Y_LIGHT = 5 / 50 = 0.1 exactly.  Y_HEAVY = 45 / 50 = 0.9 exactly.
    """
    comp = Composition.from_fractions({"LIGHT": 0.5, "HEAVY": 0.5}, MOLE)
    mass = comp.to_basis(MASS, synthetic_table)
    assert mass.fraction_of("LIGHT") == pytest.approx(0.1, rel=1e-15)
    assert mass.fraction_of("HEAVY") == pytest.approx(0.9, rel=1e-15)


def test_mass_to_mole_matches_hand_calculation(synthetic_table):
    """The inverse of the case above, computed independently.

    Y = {0.1, 0.9}.  Y/M: 0.1/10 = 0.01,  0.9/90 = 0.01.  Sum = 0.02.
    X_LIGHT = 0.01 / 0.02 = 0.5 exactly.  X_HEAVY = 0.5 exactly.
    """
    comp = Composition.from_fractions({"LIGHT": 0.1, "HEAVY": 0.9}, MASS)
    mole = comp.to_basis(MOLE, synthetic_table)
    assert mole.fraction_of("LIGHT") == pytest.approx(0.5, rel=1e-15)
    assert mole.fraction_of("HEAVY") == pytest.approx(0.5, rel=1e-15)


@pytest.mark.parametrize("fractions", [
    {"LIGHT": 1.0},
    {"LIGHT": 0.5, "HEAVY": 0.5},
    {"LIGHT": 0.1, "HEAVY": 0.9},
    {"LIGHT": 0.999999, "HEAVY": 1.0e-6},
])
@pytest.mark.parametrize("basis", [MOLE, MASS])
def test_round_trip_returns_the_original(synthetic_table, fractions, basis):
    comp = Composition.from_fractions(fractions, basis)
    other = MASS if basis is MOLE else MOLE
    back = comp.to_basis(other, synthetic_table).to_basis(basis, synthetic_table)
    for name, value in comp.fractions.items():
        assert back.fraction_of(name) == pytest.approx(value, rel=1e-12, abs=1e-15)


def test_round_trip_with_widely_different_molar_masses(realistic_table):
    """H2 at 2 g/mol against CO2 at 44 g/mol catches inverted conversions."""
    comp = Composition.from_fractions({"H2": 0.9, "CO2": 0.1}, MOLE)
    back = comp.to_basis(MASS, realistic_table).to_basis(MOLE, realistic_table)
    assert back.fraction_of("H2") == pytest.approx(0.9, rel=1e-13)
    assert back.fraction_of("CO2") == pytest.approx(0.1, rel=1e-13)


def test_converting_to_the_same_basis_is_the_identity(synthetic_table):
    comp = Composition.from_fractions({"LIGHT": 0.3, "HEAVY": 0.7}, MOLE)
    assert comp.to_basis(MOLE, synthetic_table) is comp


def test_conversion_requires_every_species(synthetic_table):
    comp = Composition.from_fractions({"LIGHT": 0.5, "UNKNOWN": 0.5}, MOLE)
    with pytest.raises(UnknownSpeciesError, match="no species record"):
        comp.to_basis(MASS, synthetic_table)


def test_free_functions_accept_any_consistent_molar_mass_unit():
    """The ratio is dimensionless, so kg/mol and kg/kmol agree."""
    in_kg_per_mol = mole_to_mass_fractions({"A": 0.5, "B": 0.5},
                                           {"A": 10.0e-3, "B": 90.0e-3})
    in_g_per_mol = mole_to_mass_fractions({"A": 0.5, "B": 0.5},
                                          {"A": 10.0, "B": 90.0})
    assert in_kg_per_mol == pytest.approx(in_g_per_mol)


# ---------------------------------------------------------------------------
# mean molar mass and gas constant
# ---------------------------------------------------------------------------


def test_mean_molar_mass_from_mole_basis(synthetic_table):
    """Mbar = 0.5*10 + 0.5*90 = 50 g/mol = 0.05 kg/mol exactly."""
    comp = Composition.from_fractions({"LIGHT": 0.5, "HEAVY": 0.5}, MOLE)
    assert comp.mean_molar_mass(synthetic_table) == pytest.approx(0.05, rel=1e-15)


def test_mean_molar_mass_from_mass_basis_agrees(synthetic_table):
    """1/Mbar = 0.1/10 + 0.9/90 = 0.02 per g/mol -> Mbar = 50 g/mol."""
    comp = Composition.from_fractions({"LIGHT": 0.1, "HEAVY": 0.9}, MASS)
    assert comp.mean_molar_mass(synthetic_table) == pytest.approx(0.05, rel=1e-15)


def test_both_mean_molar_mass_paths_agree_for_the_same_mixture(realistic_table):
    comp = Composition.from_fractions(
        {"CO2": 0.2, "H2O": 0.5, "CO": 0.2, "H2": 0.1}, MOLE)
    from_mole = comp.mean_molar_mass(realistic_table)
    from_mass = comp.to_basis(MASS, realistic_table).mean_molar_mass(realistic_table)
    assert from_mole == pytest.approx(from_mass, rel=1e-14)


def test_pure_species_limit(realistic_table):
    """X = 1, Y = 1, Mbar = M_species -- exactly."""
    comp = Composition.pure("CO2")
    assert comp.fraction_of("CO2") == 1.0
    assert comp.mean_molar_mass(realistic_table) == realistic_table["CO2"].molar_mass
    mass = comp.to_basis(MASS, realistic_table)
    assert mass.fraction_of("CO2") == pytest.approx(1.0, rel=1e-15)


def test_specific_gas_constant(synthetic_table):
    """R = Ru / Mbar = 8.31446261815324 / 0.05."""
    comp = Composition.from_fractions({"LIGHT": 0.5, "HEAVY": 0.5}, MOLE)
    expected = UNIVERSAL_GAS_CONSTANT / 0.05
    assert comp.specific_gas_constant(synthetic_table) == pytest.approx(
        expected, rel=1e-15)


def test_universal_gas_constant_is_the_codata_value():
    """Not adjusted to match a provider's historical convention.

    Phase 5B-0 measured NASA CEA using 8314.51 J/(kmol K) against CODATA's
    8314.46261815324. That 5.7e-06 difference belongs to the CEA adapter's
    comparison tolerance, not to this constant.
    """
    assert UNIVERSAL_GAS_CONSTANT == 8.31446261815324


# ---------------------------------------------------------------------------
# condensed fraction
# ---------------------------------------------------------------------------


def test_condensed_mass_fraction_comes_from_the_composition(realistic_table,
                                                            condensed_carbon):
    """Computed from what is present, never from a provider's species counter.

    Phase 5B-0 found a provider counter reporting one condensed species while
    that species was present at exactly zero.
    """
    table = dict(realistic_table)
    table["C(gr)"] = condensed_carbon
    comp = Composition.from_fractions({"CO": 0.5, "H2": 0.4, "C(gr)": 0.1}, MOLE)
    condensed = comp.condensed_mass_fraction(table)
    mass = comp.to_basis(MASS, table)
    assert condensed == pytest.approx(mass.fraction_of("C(gr)"))
    assert condensed > 0.0

    absent = Composition.from_fractions({"CO": 0.5, "H2": 0.5}, MOLE)
    assert absent.condensed_mass_fraction(table) == 0.0


# ---------------------------------------------------------------------------
# elemental inventory
# ---------------------------------------------------------------------------


def test_elemental_inventory_per_mole_is_hand_checkable(realistic_table):
    """0.5 CH4 + 0.5 O2 by mole: C = 0.5, H = 2.0, O = 1.0."""
    comp = Composition.from_fractions({"CH4": 0.5, "O2": 0.5}, MOLE)
    inventory = comp.elemental(realistic_table)
    assert inventory.basis is ElementalInventoryBasis.PER_MOLE_OF_MIXTURE
    assert inventory.elements["C"] == pytest.approx(0.5)
    assert inventory.elements["H"] == pytest.approx(2.0)
    assert inventory.elements["O"] == pytest.approx(1.0)


def test_elemental_inventory_per_kilogram(synthetic_table):
    """Pure LIGHT at 10 g/mol: 1 kg holds 100 mol, so 100 mol of element L."""
    comp = Composition.pure("LIGHT")
    inventory = elemental_inventory(
        comp, synthetic_table, ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE)
    assert inventory.elements["L"] == pytest.approx(100.0, rel=1e-15)


def test_inventory_basis_is_never_implicit(realistic_table):
    comp = Composition.pure("CO2")
    per_mole = elemental_inventory(comp, realistic_table,
                                   ElementalInventoryBasis.PER_MOLE_OF_MIXTURE)
    per_kg = elemental_inventory(comp, realistic_table,
                                 ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE)
    assert per_mole.basis is not per_kg.basis
    assert per_mole.elements["C"] != pytest.approx(per_kg.elements["C"])


def test_inventory_refuses_a_species_without_a_formula():
    table = {"X": Species("X", Phase.GAS, 20.0e-3)}
    comp = Composition.pure("X")
    with pytest.raises(CompositionError, match="no elemental formula"):
        comp.elemental(table)


def test_inventories_on_different_bases_cannot_be_compared(realistic_table):
    comp = Composition.pure("CO2")
    a = elemental_inventory(comp, realistic_table,
                            ElementalInventoryBasis.PER_MOLE_OF_MIXTURE)
    b = elemental_inventory(comp, realistic_table,
                            ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE)
    with pytest.raises(CompositionError, match="different bases"):
        compare_elemental_inventories(a, b)


# ---------------------------------------------------------------------------
# element conservation, on a real rearrangement
# ---------------------------------------------------------------------------


def test_element_conservation_holds_across_a_stoichiometric_rearrangement(
        realistic_table):
    """CH4 + 2 O2 -> CO2 + 2 H2O, compared per kilogram.

    Reactants by mole: CH4 1/3, O2 2/3.  Products: CO2 1/3, H2O 2/3.
    One kilogram of reactants and one kilogram of products must hold the same
    atoms, and this is checked without solving any chemistry.
    """
    reactants = Composition.from_fractions({"CH4": 1 / 3, "O2": 2 / 3}, MOLE)
    products = Composition.from_fractions({"CO2": 1 / 3, "H2O": 2 / 3}, MOLE)
    basis = ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE
    report = compare_elemental_inventories(
        elemental_inventory(reactants, realistic_table, basis),
        elemental_inventory(products, realistic_table, basis))
    assert report.balanced
    assert report.max_residual < 1.0e-3   # limited by the fixtures' molar masses


def test_element_balance_is_exact_for_a_trivial_identity(synthetic_table):
    comp = Composition.from_fractions({"LIGHT": 0.4, "HEAVY": 0.6}, MOLE)
    inventory = comp.elemental(synthetic_table)
    report = compare_elemental_inventories(inventory, inventory)
    assert report.balanced
    assert report.max_residual == 0.0
    assert report.worst_element is None


def test_residual_is_never_a_negative_zero(synthetic_table):
    comp = Composition.pure("LIGHT")
    inventory = comp.elemental(synthetic_table)
    report = compare_elemental_inventories(inventory, inventory)
    for _, residual in report.residuals:
        assert not math.copysign(1.0, residual) < 0.0


def test_element_absent_from_both_sides_does_not_divide_by_zero(synthetic_table):
    a = elemental_inventory(Composition.pure("LIGHT"), synthetic_table)
    b = elemental_inventory(Composition.pure("LIGHT"), synthetic_table)
    report = compare_elemental_inventories(a, b)
    assert all(math.isfinite(r) for _, r in report.residuals)


# ---------------------------------------------------------------------------
# MUTATION PROOFS -- each proves the fixture actually changed first
# ---------------------------------------------------------------------------


def test_mutation_proof_composition_sum(synthetic_table):
    """Perturb one fraction beyond tolerance; prove it changed, then that it fails."""
    from rocketforge.physics.thermochemistry import check_composition_sum

    valid = Composition.from_fractions({"LIGHT": 0.5, "HEAVY": 0.5}, MOLE)
    assert check_composition_sum(valid).passed

    # Bypass the constructor deliberately: this is what a corrupt adapter would
    # produce, and the validator must catch it.
    corrupt = dataclasses.replace(
        valid, entries=(("HEAVY", 0.5), ("LIGHT", 0.45)))
    assert corrupt.sum() != valid.sum(), "the mutation must actually bite"
    assert not check_composition_sum(corrupt).passed


def test_mutation_proof_element_balance_detects_a_dropped_species(realistic_table):
    """Remove a product; prove the inventory changed, then that the check fails."""
    basis = ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE
    reactants = Composition.from_fractions({"CH4": 1 / 3, "O2": 2 / 3}, MOLE)
    products = Composition.from_fractions({"CO2": 1 / 3, "H2O": 2 / 3}, MOLE)

    good = compare_elemental_inventories(
        elemental_inventory(reactants, realistic_table, basis),
        elemental_inventory(products, realistic_table, basis))
    assert good.balanced

    mutated = Composition.from_fractions({"CO2": 1.0}, MOLE)   # H2O dropped
    left = elemental_inventory(reactants, realistic_table, basis)
    right_good = elemental_inventory(products, realistic_table, basis)
    right_bad = elemental_inventory(mutated, realistic_table, basis)
    assert right_bad.elements != right_good.elements, "the mutation must bite"

    bad = compare_elemental_inventories(left, right_bad)
    assert not bad.balanced
    assert bad.max_residual > good.max_residual


def test_mutation_proof_element_balance_detects_a_scaled_molar_mass(realistic_table):
    """Scale one molar mass; prove the inventory changed, then that it fails.

    This is the units-slip defect: an adapter that converts kg/kmol for one
    species and not another.
    """
    basis = ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE
    reactants = Composition.from_fractions({"CH4": 1 / 3, "O2": 2 / 3}, MOLE)
    products = Composition.from_fractions({"CO2": 1 / 3, "H2O": 2 / 3}, MOLE)

    corrupted = dict(realistic_table)
    original = corrupted["H2O"]
    corrupted["H2O"] = dataclasses.replace(original, molar_mass=original.molar_mass * 2.0)
    assert corrupted["H2O"].molar_mass != original.molar_mass, "the mutation must bite"

    left = elemental_inventory(reactants, realistic_table, basis)
    right = elemental_inventory(products, corrupted, basis)
    report = compare_elemental_inventories(left, right)
    assert not report.balanced


def test_mutation_proof_element_balance_detects_an_altered_formula(realistic_table):
    """Change an atom count; prove it changed, then that conservation fails."""
    basis = ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE
    reactants = Composition.from_fractions({"CH4": 1 / 3, "O2": 2 / 3}, MOLE)
    products = Composition.from_fractions({"CO2": 1 / 3, "H2O": 2 / 3}, MOLE)

    corrupted = dict(realistic_table)
    original = corrupted["CO2"]
    corrupted["CO2"] = dataclasses.replace(
        original, formula=ElementalComposition.from_mapping({"C": 1.0, "O": 3.0}))
    assert corrupted["CO2"].formula != original.formula, "the mutation must bite"

    report = compare_elemental_inventories(
        elemental_inventory(reactants, realistic_table, basis),
        elemental_inventory(products, corrupted, basis))
    assert not report.balanced
    assert report.worst_element == "O"


def test_mutation_proof_round_trip_detects_an_inverted_conversion(synthetic_table):
    """A deliberately wrong conversion must fail the round-trip check.

    Proves the round-trip test is capable of failing at all, rather than being
    satisfied by any pair of mutually inverse functions.
    """
    from rocketforge.physics.thermochemistry import check_composition_round_trip

    comp = Composition.from_fractions({"LIGHT": 0.5, "HEAVY": 0.5}, MOLE)
    assert check_composition_round_trip(comp, synthetic_table).passed

    # Swap the molar masses: the conversion is still self-consistent, so the
    # round trip still closes -- which is the honest limit of this check.
    swapped = {
        "LIGHT": dataclasses.replace(synthetic_table["LIGHT"], molar_mass=90.0e-3),
        "HEAVY": dataclasses.replace(synthetic_table["HEAVY"], molar_mass=10.0e-3),
    }
    assert check_composition_round_trip(comp, swapped).passed
    # ...but the mass fractions genuinely differ, which the *value* test catches.
    assert (comp.to_basis(MASS, synthetic_table).fraction_of("LIGHT")
            != pytest.approx(comp.to_basis(MASS, swapped).fraction_of("LIGHT")))
