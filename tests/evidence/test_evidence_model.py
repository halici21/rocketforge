"""The evidence data model: what a record must carry, and what it refuses.

Each invariant is shown both ways -- a valid construction passes, the one-field
violation fails -- so a check that silently stopped checking would be caught.
"""

from __future__ import annotations

import dataclasses

import pytest

from rocketforge.core.errors import InputError
from rocketforge.evidence import (
    CustomDefinition,
    Dimension,
    EvidenceError,
    EvidenceStatus,
    IngredientReference,
    Missing,
    MissingReason,
    RecordKind,
    ReportedValue,
    ShippingPolicy,
    ValueStatus,
    reported_values,
    validate_against_sources,
)

from evidence_fixtures import SRC, capabilities, propellant, record, source, value


# ------------------------------------------------------------------ values


def test_a_reported_value_keeps_the_source_representation():
    v = value(-2999.082, "cal/mol", decimals=3, note="as printed")
    assert (v.value, v.unit, v.source_id, v.locator, v.status, v.decimals) == (
        -2999.082, "cal/mol", SRC, "p.1, Table 1", ValueStatus.REPORTED, 3)


def test_evidence_errors_are_input_errors():
    assert issubclass(EvidenceError, InputError)


@pytest.mark.parametrize("field,bad", [
    ("locator", ""), ("locator", "   "), ("source_id", ""), ("unit", ""),
])
def test_a_reported_value_needs_its_unit_source_and_locator(field, bad):
    with pytest.raises(EvidenceError):
        value(**{field: bad})


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "1.0", None])
def test_a_reported_value_must_be_a_finite_real_number(bad):
    with pytest.raises(EvidenceError):
        value(bad)


def test_printed_precision_is_one_kind_or_the_other():
    with pytest.raises(EvidenceError):
        value(decimals=2, significant_figures=4)
    with pytest.raises(EvidenceError):
        value(significant_figures=0)


def test_a_status_must_be_a_value_status():
    with pytest.raises(EvidenceError):
        ReportedValue(1.0, "K", SRC, "p.1", "REPORTED")


def test_missing_carries_a_reason():
    m = Missing(MissingReason.WITHHELD_RIGHTS, "Under Copyright")
    assert m.reason is MissingReason.WITHHELD_RIGHTS
    with pytest.raises(EvidenceError):
        Missing("NOT_REPORTED")


def test_gold_is_not_an_evidence_status():
    assert "GOLD" not in {s.value for s in EvidenceStatus}
    with pytest.raises(ValueError):
        EvidenceStatus("GOLD")


@pytest.mark.parametrize("obj", [
    value(), Missing(MissingReason.UNKNOWN), source(), propellant(), record()])
def test_every_evidence_type_is_immutable(obj):
    field = dataclasses.fields(obj)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(obj, field, getattr(obj, field))


def test_nested_mappings_are_read_only():
    r = record()
    with pytest.raises(TypeError):
        r.capabilities[Dimension.VA] = EvidenceStatus.REGRESSION_LOCKED
    with pytest.raises(TypeError):
        r.propellant.ingredients[1].custom.formula["H"] = value()
    with pytest.raises(TypeError):
        source().identifiers["doi"] = "x"


# ---------------------------------------------------------- scientific fields


def test_a_scientific_field_is_never_simply_absent():
    with pytest.raises(EvidenceError):
        propellant(density=None)
    with pytest.raises(EvidenceError):
        IngredientReference("X", None)
    with pytest.raises(EvidenceError):
        CustomDefinition(formula={"C": value()}, enthalpy=None,
                         reference_temperature=value(), molecular_weight=value())


def test_a_formula_is_reported_atom_by_atom_or_missing_as_a_whole():
    CustomDefinition(formula=Missing(MissingReason.NOT_REPORTED), enthalpy=value(),
                     reference_temperature=value(), molecular_weight=value())
    with pytest.raises(EvidenceError):
        CustomDefinition(formula={}, enthalpy=value(), reference_temperature=value(),
                         molecular_weight=value())
    with pytest.raises(EvidenceError):
        CustomDefinition(formula={"C": 1.0}, enthalpy=value(),
                         reference_temperature=value(), molecular_weight=value())


def test_an_exact_formulation_needs_every_fraction_reported():
    ingredients = (IngredientReference("A", value(0.5, "mass fraction")),
                   IngredientReference("B", Missing(MissingReason.NOT_REPORTED)))
    propellant(exact_formulation=False, ingredients=ingredients)
    with pytest.raises(EvidenceError):
        propellant(exact_formulation=True, ingredients=ingredients)


def test_fractions_are_held_as_stated_not_normalised():
    """Closing a formulation is a later, provider-side check; evidence keeps the
    source's numbers even when they do not sum to one."""
    ingredients = (IngredientReference("A", value(0.5, "mass fraction")),
                   IngredientReference("B", value(0.4, "mass fraction")))
    p = propellant(ingredients=ingredients)
    assert [i.fraction.value for i in p.ingredients] == [0.5, 0.4]


def test_only_the_mass_fraction_basis_exists_in_schema_version_1():
    with pytest.raises(EvidenceError):
        propellant(basis="mole_fraction")


def test_an_ingredient_is_listed_once():
    twice = (IngredientReference("A", value(0.5, "mass fraction")),
             IngredientReference("A", value(0.5, "mass fraction")))
    with pytest.raises(EvidenceError):
        propellant(ingredients=twice)


# ---------------------------------------------------------------- records


def test_a_record_states_every_dimension():
    caps = capabilities()
    del caps[Dimension.VD]
    with pytest.raises(EvidenceError):
        record(capabilities=caps)
    with pytest.raises(EvidenceError):
        record(capabilities={**capabilities(), Dimension.VA: "GOLD"})


def test_regression_locked_needs_the_case_that_locks_it():
    locked = capabilities(EvidenceStatus.REGRESSION_LOCKED)
    record(capabilities=locked, comparison_case_ids=("some-case",))
    with pytest.raises(EvidenceError, match="names no comparison case"):
        record(capabilities=locked, comparison_case_ids=())


def test_every_value_cites_a_declared_source():
    stray = propellant(initial_temperature=value(298.15, "K", source_id="S-ELSEWHERE"))
    with pytest.raises(EvidenceError, match="does not declare"):
        record(propellant=stray)


def test_the_propellant_sources_are_declared_by_the_record():
    with pytest.raises(EvidenceError):
        record(propellant=propellant(source_ids=("S-OTHER",)))


def test_a_propellant_record_has_a_propellant_and_an_executable_key_has_one_too():
    with pytest.raises(EvidenceError):
        record(propellant=None)
    with pytest.raises(EvidenceError):
        record(kind=RecordKind.REFERENCE, propellant=None, executable_key="x")
    record(kind=RecordKind.REFERENCE, propellant=None)


def test_reported_values_walks_every_value_in_order():
    values = reported_values(record())
    assert [v.value for v in values] == [0.8, 0.2, 1.0, -100.0, 298.15, 298.15]
    assert reported_values(record(kind=RecordKind.REFERENCE, propellant=None)) == ()


# ------------------------------------------------------------ source registry


def test_a_record_resolves_against_its_registry():
    validate_against_sources(record(), {SRC: source()})
    with pytest.raises(EvidenceError, match="unknown sources"):
        validate_against_sources(record(), {})


@pytest.mark.parametrize("policy", [p for p in ShippingPolicy
                                    if p is not ShippingPolicy.VALUES_WITH_ATTRIBUTION])
def test_no_value_ships_from_a_source_that_does_not_permit_values(policy):
    with pytest.raises(EvidenceError, match="only metadata"):
        validate_against_sources(record(), {SRC: source(shipping=policy)})


@pytest.mark.parametrize("policy", list(ShippingPolicy))
def test_a_metadata_only_record_may_cite_any_source(policy):
    reference = record(kind=RecordKind.REFERENCE, propellant=None)
    validate_against_sources(reference, {SRC: source(shipping=policy)})


def test_a_source_refuses_an_unknown_tier_or_policy():
    with pytest.raises(EvidenceError):
        source(tier=4)
    with pytest.raises(EvidenceError):
        source(shipping="PUBLIC")
    with pytest.raises(EvidenceError):
        source(access_class="OPEN")
