"""Species identity, elemental formulae and the polynomial data contract."""

from __future__ import annotations

import dataclasses
import math

import pytest

from rocketforge.physics.thermochemistry import (
    ElementalComposition,
    ElementalCompositionError,
    Phase,
    PolynomialForm,
    Species,
    SpeciesError,
    ThermoPolynomial,
)
from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT


# ---------------------------------------------------------------------------
# identity
# ---------------------------------------------------------------------------


def test_phase_is_part_of_identity(water_gas, water_liquid):
    """H2O(g) and H2O(l) are different species and never compare equal.

    They share a name, a formula and a molar mass, so anything that identified
    a species by those alone would collapse them -- and lose the latent heat.
    """
    assert water_gas != water_liquid
    assert water_gas.canonical_id != water_liquid.canonical_id
    assert water_gas.canonical_id == "H2O:gas"
    assert water_liquid.canonical_id == "H2O:liquid"
    assert len({water_gas, water_liquid}) == 2


def test_canonical_id_is_separate_from_display_label():
    species = Species("H2O", Phase.GAS, 18.01528e-3, display_name="H₂O")
    assert species.canonical_id == "H2O:gas"
    assert species.label == "H₂O"
    assert species.name == "H2O"


def test_label_falls_back_to_name():
    assert Species("OH", Phase.GAS, 17.0e-3).label == "OH"


def test_phase_has_no_default_and_must_be_a_phase_member():
    with pytest.raises(SpeciesError, match="never silently treated as GAS"):
        Species("X", "gas", 1.0e-3)  # type: ignore[arg-type]


def test_condensed_classification():
    assert Phase.LIQUID.is_condensed
    assert Phase.SOLID.is_condensed
    assert not Phase.GAS.is_condensed
    # A supercritical fluid is not a condensed phase in the two-phase-flow
    # sense; counting it as one would wrongly refuse valid chamber states.
    assert not Phase.SUPERCRITICAL.is_condensed


# ---------------------------------------------------------------------------
# immutability
# ---------------------------------------------------------------------------


def test_species_is_frozen(water_gas):
    with pytest.raises(dataclasses.FrozenInstanceError):
        water_gas.molar_mass = 1.0  # type: ignore[misc]


def test_elemental_composition_is_frozen():
    formula = ElementalComposition.from_mapping({"C": 1.0})
    with pytest.raises(dataclasses.FrozenInstanceError):
        formula.entries = ()  # type: ignore[misc]


def test_atoms_view_is_read_only():
    formula = ElementalComposition.from_mapping({"C": 1.0})
    with pytest.raises(TypeError):
        formula.atoms["C"] = 99.0  # type: ignore[index]


# ---------------------------------------------------------------------------
# molar mass domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0.0, -1.0e-3, float("nan"), float("inf")])
def test_molar_mass_must_be_positive_and_finite(bad):
    with pytest.raises(SpeciesError):
        Species("X", Phase.GAS, bad)


def test_molar_mass_in_kg_per_kmol_is_rejected_by_the_ceiling():
    """A species handed 16.04 instead of 16.04e-3 is caught, not accepted.

    This is the provider unit trap: Phase 5B-0 measured both candidates
    reporting kg/kmol while this package's canonical unit is kg/mol. The
    ceiling makes the mistake loud.
    """
    with pytest.raises(SpeciesError, match="kg/mol"):
        Species("CH4", Phase.GAS, 16.04246)


def test_molar_mass_is_stored_not_recomputed():
    """A stated molar mass is trusted, even when a formula is present.

    Different databases use different atomic weights; silently recomputing
    would bind every species to one table (09 section 2.2).
    """
    stated = 16.5e-3
    species = Species("CH4", Phase.GAS, stated,
                      ElementalComposition.from_mapping({"C": 1.0, "H": 4.0}))
    assert species.molar_mass == stated


def test_formula_molar_mass_cross_check_needs_caller_supplied_weights():
    species = Species("CH4", Phase.GAS, 16.04246e-3,
                      ElementalComposition.from_mapping({"C": 1.0, "H": 4.0}))
    weights = {"C": 12.0107e-3, "H": 1.00794e-3}
    implied = species.formula_molar_mass(weights)
    assert implied == pytest.approx(16.04246e-3, rel=1e-4)
    with pytest.raises(SpeciesError, match="no atomic weight supplied"):
        species.formula_molar_mass({"C": 12.0107e-3})


# ---------------------------------------------------------------------------
# elemental composition
# ---------------------------------------------------------------------------


def test_element_order_does_not_affect_equality_or_hash():
    a = ElementalComposition.from_mapping({"H": 4.0, "C": 1.0})
    b = ElementalComposition.from_mapping({"C": 1.0, "H": 4.0})
    assert a == b
    assert hash(a) == hash(b)
    assert a.symbols == ("C", "H")


def test_arbitrary_element_symbols_are_supported():
    """Not just C, H, O, N. Fluorine, metals and future labels need no change."""
    formula = ElementalComposition.from_mapping(
        {"F": 6.0, "AL": 2.0, "CL": 1.0, "e-": 1.0})
    assert formula.count("AL") == 2.0
    assert formula.count("e-") == 1.0
    assert formula.count("Xx") == 0.0


def test_fractional_atom_counts_are_allowed():
    """An empirical surrogate formula is fractional by construction."""
    rp1 = ElementalComposition.from_mapping({"C": 1.0, "H": 1.9423})
    assert rp1.count("H") == pytest.approx(1.9423)


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
def test_atom_counts_reject_negative_and_nonfinite(bad):
    with pytest.raises(ElementalCompositionError):
        ElementalComposition.from_mapping({"C": bad})


def test_addition_and_scaling():
    a = ElementalComposition.from_mapping({"C": 1.0, "H": 4.0})
    b = ElementalComposition.from_mapping({"O": 2.0, "C": 0.5})
    total = a + b
    assert total.count("C") == 1.5
    assert total.count("H") == 4.0
    assert total.count("O") == 2.0
    assert a.scaled(2.0).count("H") == 8.0
    with pytest.raises(ElementalCompositionError):
        a.scaled(-1.0)


def test_elemental_mass_fractions_use_the_stored_molar_mass():
    species = Species("H2O", Phase.GAS, 18.0e-3,
                      ElementalComposition.from_mapping({"H": 2.0, "O": 1.0}))
    fractions = species.elemental_mass_fractions()
    assert fractions["H"] == pytest.approx(2.0 / 18.0e-3)
    assert fractions["O"] == pytest.approx(1.0 / 18.0e-3)


def test_species_without_a_formula_cannot_give_elemental_fractions():
    species = Species("MYSTERY", Phase.GAS, 20.0e-3)
    assert not species.has_formula
    with pytest.raises(SpeciesError, match="no elemental formula"):
        species.elemental_mass_fractions()


# ---------------------------------------------------------------------------
# surrogates
# ---------------------------------------------------------------------------


def test_surrogate_must_name_its_source():
    """Two RP-1 fits are two species; only provenance separates them."""
    with pytest.raises(SpeciesError, match="must name its source"):
        Species("RP-1", Phase.LIQUID, 0.0139761,
                ElementalComposition.from_mapping({"C": 1.0, "H": 1.9423}),
                is_surrogate=True)


def test_two_surrogate_fits_are_distinguishable():
    common = dict(phase=Phase.LIQUID, is_surrogate=True)
    a = Species("RP-1", molar_mass=0.0139761, source="fit A",
                formula=ElementalComposition.from_mapping({"C": 1.0, "H": 1.9423}),
                **common)
    b = Species("RP-1", molar_mass=0.0139761, source="fit B",
                formula=ElementalComposition.from_mapping({"C": 1.0, "H": 1.9500}),
                **common)
    assert a != b


def test_long_names_are_allowed():
    """A provider's 15-character limit is a provider constraint, not ours.

    Phase 5B-0 measured NASA CEA raising CEA_INVALID_SIZE above 15 characters.
    That belongs in the CEA adapter's name mapping; restricting the domain model
    globally would let one provider's Fortran field width define RocketForge.
    """
    long_name = "A" * 64
    assert Species(long_name, Phase.GAS, 1.0e-3).name == long_name


# ---------------------------------------------------------------------------
# thermo polynomials
# ---------------------------------------------------------------------------


@pytest.fixture
def constant_cp_nasa7() -> ThermoPolynomial:
    """A NASA-7 fit whose cp/R is exactly 3.5, i.e. cp = 3.5 R.

    Synthetic and hand-checkable: only a1 is nonzero, so cp/R = a1 = 3.5.
    """
    coeffs = (3.5, 0.0, 0.0, 0.0, 0.0, -1000.0, 5.0)
    return ThermoPolynomial(form=PolynomialForm.NASA7,
                            temperature_ranges=((200.0, 1000.0),),
                            coefficients=(coeffs,))


def test_nasa7_cp_is_hand_checkable(constant_cp_nasa7):
    assert constant_cp_nasa7.cp_molar(500.0) == pytest.approx(
        3.5 * UNIVERSAL_GAS_CONSTANT, rel=1e-15)


def test_nasa7_enthalpy_is_hand_checkable(constant_cp_nasa7):
    """h/(R T) = a1 + a6/T, so h = R (a1 T + a6)."""
    t = 500.0
    expected = UNIVERSAL_GAS_CONSTANT * (3.5 * t + (-1000.0))
    assert constant_cp_nasa7.enthalpy_molar(t) == pytest.approx(expected, rel=1e-14)


def test_entropy_includes_the_pressure_term(constant_cp_nasa7):
    at_reference = constant_cp_nasa7.entropy_molar(500.0)
    at_ten_bar = constant_cp_nasa7.entropy_molar(500.0, 1.0e6)
    assert at_ten_bar - at_reference == pytest.approx(
        -UNIVERSAL_GAS_CONSTANT * math.log(10.0), rel=1e-14)


def test_evaluation_outside_the_range_is_refused_not_extrapolated(constant_cp_nasa7):
    """A fit evaluated past its range can return a negative cp.

    Same rule as the compressible module's refusal beyond nu_max: a number
    outside the model's domain is not a number the model may return.
    """
    assert constant_cp_nasa7.covers(200.0)
    assert not constant_cp_nasa7.covers(1000.1)
    with pytest.raises(SpeciesError, match="outside the fit's validity range"):
        constant_cp_nasa7.cp_molar(1500.0)
    with pytest.raises(SpeciesError, match="outside the fit's validity range"):
        constant_cp_nasa7.enthalpy_molar(100.0)


def test_range_join_is_continuous_in_value_but_slope_is_not_required():
    """Value continuity is tested; derivative continuity deliberately is not.

    Published NASA fits are matched in value at the join and generally not in
    slope. Demanding slope continuity would test a property the data does not
    have -- the Phase 4G lesson about fictional precision, in a new domain.
    """
    # Two ranges that agree in cp at 1000 K (both give cp/R = 3.5) but have
    # different slopes there.
    low = (3.5, 0.0, 0.0, 0.0, 0.0, -1000.0, 5.0)
    high = (3.5 - 1.0e-3 * 1000.0, 1.0e-3, 0.0, 0.0, 0.0, -1000.0, 5.0)
    fit = ThermoPolynomial(
        form=PolynomialForm.NASA7,
        temperature_ranges=((200.0, 1000.0), (1000.0, 3000.0)),
        coefficients=(low, high))
    join = 1000.0
    below = fit.cp_molar(math.nextafter(join, 0.0))
    above = fit.cp_molar(math.nextafter(join, 1e9))
    assert below == pytest.approx(above, rel=1e-9)


def test_polynomial_rejects_wrong_coefficient_count():
    with pytest.raises(SpeciesError, match="needs 7 coefficients"):
        ThermoPolynomial(form=PolynomialForm.NASA7,
                         temperature_ranges=((200.0, 1000.0),),
                         coefficients=((1.0, 2.0),))


def test_polynomial_rejects_descending_or_overlapping_ranges():
    coeffs = tuple([1.0] * 7)
    with pytest.raises(SpeciesError, match="not ascending"):
        ThermoPolynomial(form=PolynomialForm.NASA7,
                         temperature_ranges=((1000.0, 200.0),),
                         coefficients=(coeffs,))
    with pytest.raises(SpeciesError, match="ascending and non-overlapping"):
        ThermoPolynomial(form=PolynomialForm.NASA7,
                         temperature_ranges=((200.0, 1000.0), (500.0, 2000.0)),
                         coefficients=(coeffs, coeffs))


def test_nasa9_cp_is_hand_checkable():
    """NASA-9 cp/R = a1 T^-2 + a2 T^-1 + a3 + ... ; only a3 nonzero gives cp/R = a3."""
    coeffs = (0.0, 0.0, 4.0, 0.0, 0.0, 0.0, 0.0, -500.0, 2.0)
    fit = ThermoPolynomial(form=PolynomialForm.NASA9,
                           temperature_ranges=((200.0, 6000.0),),
                           coefficients=(coeffs,))
    assert fit.cp_molar(1200.0) == pytest.approx(4.0 * UNIVERSAL_GAS_CONSTANT,
                                                 rel=1e-15)
    # h/(R T) = a3 + b1/T  ->  h = R (a3 T + b1)
    assert fit.enthalpy_molar(1200.0) == pytest.approx(
        UNIVERSAL_GAS_CONSTANT * (4.0 * 1200.0 - 500.0), rel=1e-14)
