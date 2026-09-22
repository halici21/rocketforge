"""The comparison layer's own rules, with no provider present.

What these pin down is what a comparison is *allowed to conclude*: a verdict
against direct CEA or a NASA printout, and differences only -- no verdict, no
ranking -- against an independent code or an experiment.
"""

from __future__ import annotations

import pytest

import rocketforge.comparison as comparison
from rocketforge.comparison import (
    AGREES,
    COMPARED,
    DIFFERS,
    INCOMPLETE,
    ObservedQuantity,
    ReferenceCase,
    ReferenceCaseError,
    ReferenceQuantity,
    SourceKind,
    UnitError,
    case_from_mapping,
    compare,
    to_canonical,
)


def a_case(kind=SourceKind.NASA_PUBLISHED, quantities=None, **overrides):
    base = dict(
        case_id="fixture", title="fixture", source_kind=kind,
        benchmark_class="A", source="test fixture", code="NASA CEA",
        code_version="not stated", inputs={},
        quantities=quantities or (
            ReferenceQuantity("chamber_temperature", 2723.021, "K", decimals=3),),
        tolerance_rel=0.0 if kind is SourceKind.CEA_DIRECT else None)
    base.update(overrides)
    return ReferenceCase(**base)


def seen(key, value, unit):
    return {key: ObservedQuantity(key, value, unit)}


# ---------------------------------------------------------------------------
# units: exact, and refused when unknown
# ---------------------------------------------------------------------------


def test_conversion_factors_are_the_exact_definitions():
    assert to_canonical(1.0, "ft/s")[0] == 0.3048
    assert to_canonical(1.0, "atm")[0] == 101325.0
    assert to_canonical(1.0, "cal/g")[0] == 4184.0          # thermochemical cal
    assert to_canonical(1.0, "psia")[0] == pytest.approx(6894.757293168361,
                                                        rel=1e-15)


def test_an_unknown_unit_is_refused_not_guessed():
    with pytest.raises(UnitError):
        to_canonical(1.0, "furlongs/fortnight")


def test_no_basis_conversion_exists():
    """Mole and mass fractions are different quantities, not different units."""
    with pytest.raises(UnitError):
        to_canonical(0.5, "mole")


# ---------------------------------------------------------------------------
# printed precision
# ---------------------------------------------------------------------------


def test_half_unit_from_decimals_and_from_significant_figures():
    assert ReferenceQuantity("t", 2723.021, "K", decimals=3).printed_half_unit \
        == pytest.approx(5e-4)
    # %10.5g printed 0.3215 (a trailing zero dropped): five figures, 5e-6.
    assert ReferenceQuantity("x", 0.3215, "1", significant_figures=5) \
        .printed_half_unit == pytest.approx(5e-6)
    assert ReferenceQuantity("x", 7.2172e-07, "1", significant_figures=5) \
        .printed_half_unit == pytest.approx(5e-12)


def test_both_precision_kinds_at_once_are_refused():
    with pytest.raises(ReferenceCaseError):
        ReferenceQuantity("t", 1.0, "K", decimals=3, significant_figures=5)


# ---------------------------------------------------------------------------
# what a case must carry
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field,value", [
    ("source", ""), ("code", ""), ("code_version", ""), ("benchmark_class", "C")])
def test_an_incomplete_case_is_refused(field, value):
    with pytest.raises(ReferenceCaseError):
        a_case(**{field: value})


def test_a_direct_cea_case_must_state_its_tolerance():
    with pytest.raises(ReferenceCaseError):
        a_case(SourceKind.CEA_DIRECT, tolerance_rel=None)


@pytest.mark.parametrize("kind", [SourceKind.NASA_PUBLISHED,
                                  SourceKind.INDEPENDENT_CODE,
                                  SourceKind.EXPERIMENT])
def test_only_direct_cea_may_carry_a_tolerance(kind):
    """A printout is held to its print; an independent code to nothing."""
    with pytest.raises(ReferenceCaseError):
        a_case(kind, tolerance_rel=1e-3)


def test_a_printout_without_its_precision_is_refused():
    with pytest.raises(ReferenceCaseError):
        a_case(quantities=(ReferenceQuantity("chamber_temperature", 2723.0, "K"),))


# ---------------------------------------------------------------------------
# verdicts -- and where there are none
# ---------------------------------------------------------------------------


def test_a_printout_agrees_within_half_its_last_digit():
    case = a_case()
    assert compare(case, seen("chamber_temperature", 2723.0214, "K")).verdict == AGREES


def test_a_printout_differs_just_outside_half_its_last_digit():
    """The negative control: the bound must be able to fail."""
    case = a_case()
    assert compare(case, seen("chamber_temperature", 2723.0216, "K")).verdict == DIFFERS


def test_direct_cea_at_zero_tolerance_means_identical():
    case = a_case(SourceKind.CEA_DIRECT, quantities=(
        ReferenceQuantity("chamber_temperature", 2723.0209993067942, "K"),))
    assert compare(case, seen("chamber_temperature", 2723.0209993067942, "K")
                   ).verdict == AGREES
    one_ulp = 2723.0209993067947
    assert compare(case, seen("chamber_temperature", one_ulp, "K")).verdict == DIFFERS


@pytest.mark.parametrize("kind", [SourceKind.INDEPENDENT_CODE, SourceKind.EXPERIMENT])
def test_an_independent_source_gets_differences_and_never_a_verdict(kind):
    """However far apart the two numbers are, nothing here says who is right."""
    case = a_case(kind, code="PROPEP", quantities=(
        ReferenceQuantity("chamber_temperature", 3000.0, "K", uncertainty=5.0),))
    result = compare(case, seen("chamber_temperature", 2723.0, "K"))
    assert result.verdict == COMPARED
    row = result.rows[0]
    assert row.verdict == COMPARED and row.bound is None
    assert row.abs_diff == pytest.approx(-277.0)
    assert row.uncertainty == 5.0


def test_a_verdict_case_missing_a_quantity_is_incomplete_not_agreeing():
    case = a_case(quantities=(
        ReferenceQuantity("chamber_temperature", 2723.021, "K", decimals=3),
        ReferenceQuantity("characteristic_velocity", 1525.68, "m/s", decimals=2)))
    result = compare(case, seen("chamber_temperature", 2723.021, "K"))
    assert result.verdict == INCOMPLETE
    assert result.not_observed == ("characteristic_velocity",)


def test_units_are_reconciled_before_comparing():
    case = a_case(quantities=(
        ReferenceQuantity("characteristic_velocity", 6386.75, "ft/s", decimals=2),))
    result = compare(case, seen("characteristic_velocity", 6386.75 * 0.3048, "m/s"))
    assert result.verdict == AGREES and result.rows[0].unit == "m/s"


def test_a_dimension_mismatch_is_an_error_not_a_difference():
    case = a_case()
    with pytest.raises(ValueError):
        compare(case, seen("chamber_temperature", 2723.0, "m/s"))


def test_a_mole_fraction_is_never_compared_with_a_mass_fraction():
    case = a_case(quantities=(
        ReferenceQuantity("mole_fraction:H2", 0.3215, "1", significant_figures=5),))
    result = compare(case, seen("mass_fraction:H2", 0.3215, "1"))
    assert result.rows == () and result.verdict == INCOMPLETE


def test_nothing_in_the_layer_ranks_references():
    """No "best", "closest" or ranking helper -- by design, and by test."""
    names = " ".join(comparison.__all__).lower()
    for word in ("rank", "best", "closest", "winner", "score"):
        assert word not in names


# ---------------------------------------------------------------------------
# importing an external case as data
# ---------------------------------------------------------------------------


def an_import(**overrides):
    data = {
        "case_id": "propep-example", "title": "an imported run",
        "source_kind": "independent_code", "benchmark_class": "A",
        "source": "a user-supplied PROPEP run", "code": "PROPEP",
        "code_version": "not stated", "inputs": {"note": "fixture"},
        "quantities": [{"key": "chamber_temperature", "value": 3000.0,
                        "unit": "K"}],
        "missing": ["binder heat of formation not published"],
    }
    data.update(overrides)
    return data


def test_an_independent_code_run_imports_as_data():
    case = case_from_mapping(an_import())
    assert case.source_kind is SourceKind.INDEPENDENT_CODE
    assert case.allows_verdict is False
    assert case.missing == ("binder heat of formation not published",)


@pytest.mark.parametrize("field", ["code_version", "source", "source_kind", "code"])
def test_an_import_missing_a_required_field_is_refused(field):
    data = an_import()
    del data[field]
    with pytest.raises(ReferenceCaseError):
        case_from_mapping(data)


def test_an_import_cannot_claim_a_verdict_kind_without_precision():
    """Relabelling a PROPEP number as a NASA printout does not get it a verdict:
    a printout must state its printed precision, and this one does not."""
    with pytest.raises(ReferenceCaseError):
        case_from_mapping(an_import(source_kind="nasa_published"))


def test_an_unknown_quantity_field_is_refused():
    with pytest.raises(ReferenceCaseError):
        case_from_mapping(an_import(quantities=[
            {"key": "chamber_temperature", "value": 1.0, "unit": "K",
             "confidence": "high"}]))
