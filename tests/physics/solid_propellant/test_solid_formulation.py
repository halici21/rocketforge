"""The solid formulation domain model, with no provider present.

These run in the base environment, which has no chemistry library. What they
pin down is the part a provider cannot check for us: that a formulation refuses
to close on anything but 1.0, that a percent typed where a fraction belongs is
caught rather than silently solved, and that the solid request is deliberately
*not* a bipropellant request wearing a different name.
"""

from __future__ import annotations

import dataclasses

import pytest

from rocketforge.physics.solid_propellant import (
    MASS_FRACTION_SUM_TOL,
    CustomReactant,
    MassFractionSumError,
    SolidFormulation,
    SolidFormulationEquilibriumRequest,
    SolidFormulationError,
    SolidIngredient,
)
from rocketforge.physics.thermochemistry import ChamberEquilibriumRequest
from rocketforge.physics.thermochemistry.errors import ThermochemistryError


def a_formulation(**overrides) -> SolidFormulation:
    base = dict(
        name="test grain",
        ingredients=(
            SolidIngredient("NH4CLO4(I)", 0.72),
            SolidIngredient("AL(cr)", 0.28),
        ),
    )
    base.update(overrides)
    return SolidFormulation(**base)


# ---------------------------------------------------------------------------
# fractions
# ---------------------------------------------------------------------------


def test_a_formulation_that_does_not_close_is_refused():
    with pytest.raises(MassFractionSumError) as excinfo:
        SolidFormulation(name="short", ingredients=(
            SolidIngredient("NH4CLO4(I)", 0.72),
            SolidIngredient("AL(cr)", 0.26),
        ))
    assert "sum to 1.0" in str(excinfo.value)


def test_the_sum_check_is_tight_enough_to_catch_a_real_typo():
    """A negative control: the check must actually be able to fail.

    A tolerance loose enough to accept a missing 1 % ingredient would let the
    error through while still reporting a plausible chamber temperature.
    """
    off_by = MASS_FRACTION_SUM_TOL * 1000.0
    with pytest.raises(MassFractionSumError):
        SolidFormulation(name="slightly off", ingredients=(
            SolidIngredient("NH4CLO4(I)", 0.72),
            SolidIngredient("AL(cr)", 0.28 + off_by),
        ))


def test_a_percent_where_a_fraction_belongs_is_refused():
    """72 instead of 0.72 is the single most likely data-entry error here."""
    with pytest.raises(SolidFormulationError) as excinfo:
        SolidIngredient("NH4CLO4(I)", 72.0)
    assert "percent" in str(excinfo.value)


def test_an_ingredient_at_zero_is_allowed():
    """Section 14 asks for >= 0. Dialling an ingredient out is a real state."""
    assert SolidIngredient("AL(cr)", 0.0).mass_fraction == 0.0


def test_a_negative_fraction_is_refused():
    with pytest.raises(SolidFormulationError):
        SolidIngredient("AL(cr)", -0.01)


def test_a_zero_ingredient_still_needs_the_rest_to_close():
    formulation = SolidFormulation(name="with a zero", ingredients=(
        SolidIngredient("NH4CLO4(I)", 1.0),
        SolidIngredient("AL(cr)", 0.0),
    ))
    assert formulation.mass_fractions == (1.0, 0.0)


def test_a_custom_reactant_must_name_its_source():
    """Section 15: a full definition *and* its provenance."""
    for source in ("", "   "):
        with pytest.raises(SolidFormulationError) as excinfo:
            CustomReactant(formula={"C": 1.0}, molecular_weight=12.0,
                           enthalpy=-1.0, enthalpy_units="cal/mol",
                           temperature=298.15, source=source)
        assert "source" in str(excinfo.value)


def test_a_repeated_ingredient_is_refused_rather_than_summed():
    with pytest.raises(SolidFormulationError) as excinfo:
        SolidFormulation(name="doubled", ingredients=(
            SolidIngredient("AL(cr)", 0.5),
            SolidIngredient("AL(cr)", 0.5),
        ))
    assert "twice" in str(excinfo.value)


def test_the_weight_vector_keeps_ingredient_order():
    """CEA pairs names and weights positionally; order is part of the value."""
    formulation = a_formulation()
    assert formulation.names == ("NH4CLO4(I)", "AL(cr)")
    assert formulation.mass_fractions == (0.72, 0.28)


# ---------------------------------------------------------------------------
# custom reactants
# ---------------------------------------------------------------------------


def test_a_custom_reactant_accepts_a_fractional_atom_count():
    """A binder's formula is an average over a polymer, so H: 1.86955 is real."""
    binder = CustomReactant(
        formula={"C": 1.0, "H": 1.86955},
        molecular_weight=14.665,
        enthalpy=-2999.082,
        enthalpy_units="cal/mol",
        temperature=298.15,
        source="test fixture",
    )
    assert binder.formula["H"] == pytest.approx(1.86955)


def test_a_custom_reactant_needs_a_formula():
    with pytest.raises(SolidFormulationError):
        CustomReactant(formula={}, molecular_weight=14.0, enthalpy=-1.0,
                       enthalpy_units="cal/mol", temperature=298.15, source="test fixture")


def test_an_unknown_enthalpy_unit_is_refused_rather_than_assumed():
    """Guessing cal/mol when the caller meant kJ/mol is a factor-of-4 error."""
    with pytest.raises(SolidFormulationError):
        CustomReactant(formula={"C": 1.0}, molecular_weight=12.0,
                       enthalpy=-1.0, enthalpy_units="BTU/lb",
                       temperature=298.15, source="test fixture")


def test_a_negative_assigned_enthalpy_is_normal_and_accepted():
    binder = CustomReactant(formula={"C": 1.0}, molecular_weight=12.0,
                            enthalpy=-2999.082, enthalpy_units="cal/mol",
                            temperature=298.15, source="test fixture")
    assert binder.enthalpy < 0.0


def test_custom_ingredients_are_reported_separately():
    binder = CustomReactant(formula={"C": 1.0}, molecular_weight=12.0,
                            enthalpy=-1.0, enthalpy_units="cal/mol",
                            temperature=298.15, source="test fixture")
    formulation = SolidFormulation(name="mixed", ingredients=(
        SolidIngredient("AL(cr)", 0.5),
        SolidIngredient("binder", 0.5, custom=binder),
    ))
    assert [i.name for i in formulation.custom_ingredients] == ["binder"]
    assert formulation.ingredients[0].is_custom is False
    assert formulation.ingredients[1].is_custom is True


# ---------------------------------------------------------------------------
# the request, and what it deliberately is not
# ---------------------------------------------------------------------------


def test_a_non_positive_chamber_pressure_is_refused():
    with pytest.raises(ThermochemistryError):
        SolidFormulationEquilibriumRequest(formulation=a_formulation(),
                                           chamber_pressure=0.0)


def test_the_solid_request_is_not_a_bipropellant_request():
    """The separation is the design, not an oversight.

    ``ChamberEquilibriumRequest`` requires a fuel stream, an oxidiser stream
    and a mixture ratio. A solid grain has none of the three, and inventing
    them to reach the bipropellant entry point is the fabrication this work is
    specifically not allowed to perform. If a later change makes the solid
    request a subclass, that decision should be argued rather than inherited.
    """
    request = SolidFormulationEquilibriumRequest(
        formulation=a_formulation(), chamber_pressure=3.4e6)
    assert not isinstance(request, ChamberEquilibriumRequest)
    for absent in ("fuel", "oxidiser", "oxidiser_fuel_ratio"):
        assert not hasattr(request, absent)


def test_the_request_shares_the_chamber_pressure_field_name():
    """So a call site reads the same way in both paths, units included."""
    solid_fields = {f.name for f in dataclasses.fields(
        SolidFormulationEquilibriumRequest)}
    bipropellant_fields = {f.name for f in dataclasses.fields(
        ChamberEquilibriumRequest)}
    assert "chamber_pressure" in solid_fields & bipropellant_fields


def test_product_species_may_be_none_to_derive_them_from_the_reactants():
    """None is a real capability, not a missing value.

    NASA's own solid examples derive the product set from the reactants; an
    explicit list would be the deviation.
    """
    request = SolidFormulationEquilibriumRequest(
        formulation=a_formulation(), chamber_pressure=3.4e6)
    assert request.product_species is None


def test_an_empty_product_species_tuple_is_refused():
    """Empty is not the same as None, and must not be read as 'choose for me'."""
    with pytest.raises(ThermochemistryError):
        SolidFormulationEquilibriumRequest(
            formulation=a_formulation(), chamber_pressure=3.4e6,
            product_species=())
