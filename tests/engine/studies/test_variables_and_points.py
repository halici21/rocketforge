"""Design variables, point enumeration, and the stage keys reuse depends on."""

from __future__ import annotations

import math

import pytest

from rocketforge.engine.studies import (
    CategoricalVariable,
    ExplicitNumericVariable,
    LinearRangeVariable,
    VariableDomain,
    enumerate_points,
    linear_range,
    point_count,
)
from rocketforge.engine.studies.enumeration import stage_key, unique_stage_keys

STAGES = ("upstream", "downstream", "decision")


# ===========================================================================
# linear ranges
# ===========================================================================


def test_a_linear_range_has_exact_endpoints():
    """The two values a user is most likely to have chosen deliberately."""
    values = linear_range(2.5, 4.5, 41)
    assert values[0] == 2.5
    assert values[-1] == 4.5
    assert len(values) == 41


def test_a_linear_range_does_not_drift_like_accumulation():
    """``value += step`` 40 times lands short; generating by index does not."""
    values = linear_range(0.0, 1.0, 41)
    accumulated = 0.0
    step = 1.0 / 40
    for _ in range(40):
        accumulated += step
    assert values[-1] == 1.0
    assert accumulated != 1.0            # the failure mode this avoids
    assert values[20] == pytest.approx(0.5, abs=0.0)


def test_a_single_point_range_is_the_start_value():
    assert linear_range(3.4, 9.9, 1) == (3.4,)


def test_a_linear_range_is_evenly_spaced():
    values = linear_range(10.0, 20.0, 6)
    gaps = [b - a for a, b in zip(values, values[1:])]
    for gap in gaps:
        assert gap == pytest.approx(2.0, rel=1e-12)


@pytest.mark.parametrize("count", [0, -1, -100])
def test_a_range_needs_at_least_one_point(count):
    with pytest.raises(ValueError):
        linear_range(1.0, 2.0, count)


def test_a_range_count_must_be_an_integer():
    with pytest.raises(TypeError):
        linear_range(1.0, 2.0, 4.0)      # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_a_range_endpoint_must_be_finite(bad):
    with pytest.raises(ValueError):
        linear_range(bad, 2.0, 5)


def test_a_descending_range_is_allowed():
    """Nothing here decides which direction is meaningful."""
    values = linear_range(10.0, 2.0, 5)
    assert values[0] == 10.0
    assert values[-1] == 2.0


# ===========================================================================
# variable kinds
# ===========================================================================


def test_a_variable_needs_a_key_and_a_stage():
    with pytest.raises(ValueError):
        LinearRangeVariable(key="", label="X", stage="upstream")
    with pytest.raises(ValueError):
        LinearRangeVariable(key="x", label="X", stage="")


def test_a_domain_refuses_a_value_outside_it():
    with pytest.raises(ValueError, match="outside its allowed domain"):
        LinearRangeVariable(key="of", label="O/F", stage="upstream",
                            start=-1.0, end=4.0, count=5,
                            domain=VariableDomain(minimum=0.0,
                                                  exclusive_minimum=True))


def test_a_domain_accepts_a_value_inside_it():
    variable = LinearRangeVariable(
        key="of", label="O/F", stage="upstream", start=0.5, end=4.0, count=5,
        domain=VariableDomain(minimum=0.0, exclusive_minimum=True))
    assert variable.count == 5


def test_explicit_values_are_kept_in_the_order_given():
    variable = ExplicitNumericVariable(key="eps", label="Ae/At",
                                       stage="downstream",
                                       entries=(80.0, 10.0, 40.0))
    assert variable.values == (80.0, 10.0, 40.0)


def test_explicit_values_refuse_a_duplicate():
    """A repeated value would be evaluated twice and ranked twice."""
    with pytest.raises(ValueError, match="repeats a value"):
        ExplicitNumericVariable(key="eps", label="Ae/At", stage="downstream",
                                entries=(10.0, 20.0, 10.0))


def test_explicit_values_refuse_a_non_finite_entry():
    with pytest.raises(ValueError, match="non-finite"):
        ExplicitNumericVariable(key="eps", label="Ae/At", stage="downstream",
                                entries=(10.0, float("nan")))


def test_a_categorical_variable_is_not_numeric():
    variable = CategoricalVariable(key="pair", label="Propellants",
                                   stage="upstream",
                                   options=("LOX/LCH4", "LOX/LH2"))
    assert not variable.is_numeric
    assert variable.count == 2


def test_a_categorical_variable_refuses_duplicates_and_emptiness():
    with pytest.raises(ValueError):
        CategoricalVariable(key="p", label="P", stage="upstream", options=())
    with pytest.raises(ValueError):
        CategoricalVariable(key="p", label="P", stage="upstream",
                            options=("a", "a"))


def test_a_variable_canonical_form_excludes_the_label():
    """A renamed variable is the same variable, and must fingerprint the same."""
    first = LinearRangeVariable(key="x", label="Ex", stage="upstream",
                                start=1.0, end=2.0, count=3)
    second = LinearRangeVariable(key="x", label="Completely different",
                                 stage="upstream", start=1.0, end=2.0, count=3)
    assert first.canonical() == second.canonical()


# ===========================================================================
# enumeration
# ===========================================================================


def test_the_point_count_is_the_product_of_the_cardinalities():
    a = LinearRangeVariable(key="x", label="X", stage="upstream",
                            start=0.0, end=1.0, count=41)
    b = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                entries=(1.0, 2.0, 3.0, 4.0))
    assert point_count([a, b]) == 164
    assert len(enumerate_points([a, b])) == 164


def test_the_point_count_needs_no_enumeration():
    """A preview must be cheap even for a study too large to run."""
    huge = [LinearRangeVariable(key=f"v{i}", label=f"V{i}", stage="upstream",
                                start=0.0, end=1.0, count=50)
            for i in range(6)]
    assert point_count(huge) == 50 ** 6      # returns instantly


def test_the_first_variable_varies_slowest():
    """Odometer order, documented, and part of the contract."""
    a = ExplicitNumericVariable(key="x", label="X", stage="upstream",
                                entries=(1.0, 2.0))
    b = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                entries=(10.0, 20.0, 30.0))
    points = enumerate_points([a, b])
    assert [(p["x"], p["y"]) for p in points] == [
        (1.0, 10.0), (1.0, 20.0), (1.0, 30.0),
        (2.0, 10.0), (2.0, 20.0), (2.0, 30.0)]


def test_point_indices_are_stable_and_contiguous():
    a = ExplicitNumericVariable(key="x", label="X", stage="upstream",
                                entries=(1.0, 2.0, 3.0))
    points = enumerate_points([a])
    assert [p.index for p in points] == [0, 1, 2]


def test_enumeration_is_deterministic_across_calls():
    a = LinearRangeVariable(key="x", label="X", stage="upstream",
                            start=2.5, end=4.5, count=41)
    b = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                entries=(10.0, 20.0, 40.0, 80.0))
    first = enumerate_points([a, b])
    second = enumerate_points([a, b])
    assert [dict(p.values) for p in first] == [dict(p.values) for p in second]


def test_no_variables_still_produces_one_point():
    """A single-point study is a valid study: everything fixed, one answer."""
    points = enumerate_points([])
    assert len(points) == 1
    assert dict(points[0].values) == {}


# ===========================================================================
# stage keys -- the basis of every solve-reuse claim
# ===========================================================================


@pytest.fixture()
def two_stage_variables():
    return [
        LinearRangeVariable(key="x", label="X", stage="upstream",
                            start=2.5, end=4.5, count=41),
        ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                entries=(10.0, 20.0, 40.0, 80.0)),
    ]


def test_an_upstream_key_excludes_downstream_variables(two_stage_variables):
    """The one property the 410-to-41 reduction rests on."""
    points = enumerate_points(two_stage_variables)
    key = stage_key(points[0], two_stage_variables, STAGES, "upstream")
    assert key == (("x", 2.5),)
    assert "y" not in dict(key)


def test_a_downstream_key_includes_both_stages(two_stage_variables):
    points = enumerate_points(two_stage_variables)
    key = stage_key(points[0], two_stage_variables, STAGES, "downstream")
    assert dict(key) == {"x": 2.5, "y": 10.0}


def test_points_sharing_an_upstream_value_share_an_upstream_key(two_stage_variables):
    points = enumerate_points(two_stage_variables)
    first_four = [stage_key(p, two_stage_variables, STAGES, "upstream")
                  for p in points[:4]]
    assert len(set(first_four)) == 1     # four area ratios, one chamber


def test_the_unique_upstream_key_count_is_the_upstream_cardinality(
        two_stage_variables):
    points = enumerate_points(two_stage_variables)
    keys = unique_stage_keys(points, two_stage_variables, STAGES, "upstream")
    assert len(points) == 164
    assert len(keys) == 41


def test_unique_downstream_keys_are_every_point(two_stage_variables):
    points = enumerate_points(two_stage_variables)
    keys = unique_stage_keys(points, two_stage_variables, STAGES, "downstream")
    assert len(keys) == 164


def test_the_stage_key_is_order_independent():
    """Declaring variables in a different order must not change the key."""
    a = ExplicitNumericVariable(key="x", label="X", stage="upstream",
                                entries=(1.0,))
    b = ExplicitNumericVariable(key="w", label="W", stage="upstream",
                                entries=(5.0,))
    forward = enumerate_points([a, b])[0]
    backward = enumerate_points([b, a])[0]
    assert (stage_key(forward, [a, b], STAGES, "upstream")
            == stage_key(backward, [b, a], STAGES, "upstream"))


def test_a_variable_with_an_unknown_stage_is_refused(two_stage_variables):
    bad = ExplicitNumericVariable(key="z", label="Z", stage="nowhere",
                                  entries=(1.0,))
    points = enumerate_points(two_stage_variables + [bad])
    with pytest.raises(ValueError, match="not in the study's stage order"):
        stage_key(points[0], two_stage_variables + [bad], STAGES, "upstream")


def test_asking_for_an_unknown_stage_is_refused(two_stage_variables):
    points = enumerate_points(two_stage_variables)
    with pytest.raises(ValueError, match="not in the study's stage order"):
        stage_key(points[0], two_stage_variables, STAGES, "invented")


def test_unique_keys_are_in_first_appearance_order(two_stage_variables):
    """So the expensive stage runs in the order the table is read."""
    points = enumerate_points(two_stage_variables)
    keys = unique_stage_keys(points, two_stage_variables, STAGES, "upstream")
    assert keys[0] == (("x", 2.5),)
    assert keys[-1] == (("x", 4.5),)
