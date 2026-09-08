"""Constraints, feasibility, Pareto and scoring, on hand-computable fixtures.

The expected answers here are worked out by hand and written down, never
produced by calling the function under test. A Pareto test whose expectation
comes from the Pareto implementation checks that the code agrees with itself.

The fixtures are deliberately tiny -- six points, two objectives -- because a
front you can verify by eye is a front you can be sure about.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.engine.studies import (
    ComparisonOperator,
    ConstraintDefinition,
    Feasibility,
    NormalizationMethod,
    ObjectiveDefinition,
    ObjectiveDirection,
    WeightedScoreDefinition,
    evaluate_constraints,
    normalize_objective,
    pareto_front,
    pareto_membership,
    rank_by_objective,
    score_points,
)
from rocketforge.engine.studies.pareto import dominates
from rocketforge.engine.studies.scoring import ZERO_SPAN_COMPONENT

MAX_ISP = ObjectiveDefinition("isp", ObjectiveDirection.MAXIMIZE)
MIN_TC = ObjectiveDefinition("tc", ObjectiveDirection.MINIMIZE)


# ===========================================================================
# constraints
# ===========================================================================


@pytest.mark.parametrize("operator,value,limit,expected", [
    (ComparisonOperator.LE, 3500.0, 3500.0, True),
    (ComparisonOperator.LE, 3500.1, 3500.0, False),
    (ComparisonOperator.LT, 3500.0, 3500.0, False),
    (ComparisonOperator.GE, 340.0, 340.0, True),
    (ComparisonOperator.GE, 339.9, 340.0, False),
    (ComparisonOperator.GT, 340.0, 340.0, False),
    (ComparisonOperator.EQ, 2.0, 2.0, True),
])
def test_each_operator_compares_as_written(operator, value, limit, expected):
    constraint = ConstraintDefinition("m", operator, limit)
    assert constraint.satisfied_by(value) is expected


def test_a_constraint_uses_no_hidden_tolerance():
    """A margin belongs in the limit, where the user can see it."""
    constraint = ConstraintDefinition("tc", ComparisonOperator.LE, 3500.0)
    assert constraint.satisfied_by(3500.0 + 1e-9) is False
    assert constraint.satisfied_by(3500.0) is True


def test_a_missing_metric_is_unjudged_rather_than_violated():
    """A model limitation is not an engineering verdict."""
    constraint = ConstraintDefinition("tc", ComparisonOperator.LE, 3500.0)
    assert constraint.satisfied_by(None) is None


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_a_non_finite_value_is_unjudged(bad):
    constraint = ConstraintDefinition("tc", ComparisonOperator.LE, 3500.0)
    assert constraint.satisfied_by(bad) is None


def test_a_constraint_limit_must_be_finite():
    with pytest.raises(ValueError):
        ConstraintDefinition("tc", ComparisonOperator.LE, float("nan"))


def test_every_constraint_produces_an_outcome_including_unjudgeable_ones():
    """Dropping the unjudgeable ones would make a point look feasible."""
    outcomes = evaluate_constraints(
        {"tc": 3400.0, "isp": None},
        [ConstraintDefinition("tc", ComparisonOperator.LE, 3500.0),
         ConstraintDefinition("isp", ComparisonOperator.GE, 340.0)])
    assert len(outcomes) == 2
    assert outcomes[0].satisfied is True
    assert outcomes[1].satisfied is None


def test_a_violated_outcome_says_by_how_much():
    """'3610 K violates <= 3500' is actionable; 'infeasible' is not."""
    outcome = evaluate_constraints(
        {"tc": 3610.0},
        [ConstraintDefinition("tc", ComparisonOperator.LE, 3500.0)])[0]
    assert outcome.violated
    assert "3610" in outcome.describe()
    assert "3500" in outcome.describe()


# ===========================================================================
# Pareto — an independent, hand-checked fixture
# ===========================================================================

#: Six designs. Maximise isp, minimise tc. Worked out by hand:
#:
#:   0: isp 300, tc 3000
#:   1: isp 320, tc 3200
#:   2: isp 340, tc 3400
#:   3: isp 310, tc 3300   dominated by 1 (lower isp, higher tc)
#:   4: isp 300, tc 3100   dominated by 0 (same isp, higher tc)
#:   5: isp 340, tc 3400   a tie with 2
#:
#: Nondominated: 0, 1, 2, 5.
HAND_FIXTURE = [
    (0, {"isp": 300.0, "tc": 3000.0}),
    (1, {"isp": 320.0, "tc": 3200.0}),
    (2, {"isp": 340.0, "tc": 3400.0}),
    (3, {"isp": 310.0, "tc": 3300.0}),
    (4, {"isp": 300.0, "tc": 3100.0}),
    (5, {"isp": 340.0, "tc": 3400.0}),
]
HAND_EXPECTED_FRONT = (0, 1, 2, 5)


def test_the_hand_computed_front_is_reproduced():
    assert pareto_front(HAND_FIXTURE, [MAX_ISP, MIN_TC]) == HAND_EXPECTED_FRONT


def test_a_dominated_point_is_excluded_for_the_stated_reason():
    membership = pareto_membership(HAND_FIXTURE, [MAX_ISP, MIN_TC])
    assert membership[3] is False       # beaten by 1 on both
    assert membership[4] is False       # equal isp, worse tc than 0
    assert membership[1] is True


def test_identical_vectors_do_not_dominate_each_other():
    """Both duplicates stay. Keeping one would hide that there are two."""
    membership = pareto_membership(HAND_FIXTURE, [MAX_ISP, MIN_TC])
    assert membership[2] is True and membership[5] is True


def test_dominance_respects_each_direction_separately():
    assert dominates((340.0, 3000.0), (300.0, 3400.0), [MAX_ISP, MIN_TC])
    assert not dominates((300.0, 3400.0), (340.0, 3000.0), [MAX_ISP, MIN_TC])
    # better isp but worse tc: neither dominates
    assert not dominates((340.0, 3400.0), (300.0, 3000.0), [MAX_ISP, MIN_TC])
    assert not dominates((300.0, 3000.0), (340.0, 3400.0), [MAX_ISP, MIN_TC])


def test_two_maximise_objectives_work_too():
    entries = [(0, {"a": 1.0, "b": 5.0}), (1, {"a": 5.0, "b": 1.0}),
               (2, {"a": 2.0, "b": 2.0}), (3, {"a": 5.0, "b": 5.0})]
    objectives = [ObjectiveDefinition("a", ObjectiveDirection.MAXIMIZE),
                  ObjectiveDefinition("b", ObjectiveDirection.MAXIMIZE)]
    assert pareto_front(entries, objectives) == (3,)


def test_three_objectives_are_all_used():
    """Membership uses every objective, not the two a chart happens to plot."""
    entries = [(0, {"a": 1.0, "b": 1.0, "c": 9.0}),
               (1, {"a": 2.0, "b": 2.0, "c": 1.0})]
    two = [ObjectiveDefinition("a", ObjectiveDirection.MAXIMIZE),
           ObjectiveDefinition("b", ObjectiveDirection.MAXIMIZE)]
    three = two + [ObjectiveDefinition("c", ObjectiveDirection.MAXIMIZE)]
    assert pareto_front(entries, two) == (1,)          # 1 beats 0 on a and b
    assert pareto_front(entries, three) == (0, 1)      # c rescues 0


def test_a_point_with_a_missing_objective_value_is_not_on_the_front():
    entries = HAND_FIXTURE + [(6, {"isp": None, "tc": 1.0})]
    membership = pareto_membership(entries, [MAX_ISP, MIN_TC])
    assert membership[6] is False
    assert 6 in membership              # present, not silently dropped


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_a_non_finite_objective_value_is_not_on_the_front(bad):
    """A NaN compares false against everything and would look unbeatable."""
    entries = HAND_FIXTURE + [(6, {"isp": bad, "tc": 0.0})]
    membership = pareto_membership(entries, [MAX_ISP, MIN_TC])
    assert membership[6] is False


def test_no_objectives_means_no_front():
    membership = pareto_membership(HAND_FIXTURE, [])
    assert set(membership.values()) == {False}


def test_the_front_is_returned_in_enumeration_order():
    shuffled = [HAND_FIXTURE[i] for i in (5, 2, 0, 3, 1, 4)]
    assert pareto_front(shuffled, [MAX_ISP, MIN_TC]) == (5, 2, 0, 1)


# ===========================================================================
# Pareto mutation proof
# ===========================================================================


def test_mutating_an_objective_value_changes_membership():
    """The fixture must actually change, and the answer must follow it."""
    mutated = list(HAND_FIXTURE)
    before = dict(mutated[3][1])
    mutated[3] = (3, {"isp": 400.0, "tc": 2900.0})   # now beats everything
    assert mutated[3][1] != before                   # the fixture moved

    front_before = pareto_front(HAND_FIXTURE, [MAX_ISP, MIN_TC])
    front_after = pareto_front(mutated, [MAX_ISP, MIN_TC])
    assert 3 not in front_before
    assert front_after == (3,)                       # it dominates all others


def test_mutating_a_direction_changes_membership():
    flipped = ObjectiveDefinition("tc", ObjectiveDirection.MAXIMIZE)
    assert (pareto_front(HAND_FIXTURE, [MAX_ISP, MIN_TC])
            != pareto_front(HAND_FIXTURE, [MAX_ISP, flipped]))


# ===========================================================================
# single-objective ranking
# ===========================================================================


def test_a_single_objective_ranks_rather_than_fronts():
    values = [(index, metrics["isp"]) for index, metrics in HAND_FIXTURE]
    ranked = rank_by_objective(values, MAX_ISP)
    assert [index for index, _ in ranked][:2] == [2, 5]     # both at 340
    assert ranked[-1][0] in (0, 4)                          # both at 300


def test_ranking_respects_minimise():
    values = [(index, metrics["tc"]) for index, metrics in HAND_FIXTURE]
    ranked = rank_by_objective(values, MIN_TC)
    assert ranked[0][0] == 0                                # tc 3000
    assert ranked[0][1] == 3000.0


def test_ranking_drops_non_finite_values():
    ranked = rank_by_objective([(0, 1.0), (1, float("nan")), (2, 3.0)], MAX_ISP)
    assert [index for index, _ in ranked] == [2, 0]


# ===========================================================================
# scoring — hand-computed
# ===========================================================================


def test_min_max_normalisation_maps_best_to_one_in_both_directions():
    assert normalize_objective([10.0, 20.0, 30.0], MAX_ISP) == (0.0, 0.5, 1.0)
    assert normalize_objective([10.0, 20.0, 30.0], MIN_TC) == (1.0, 0.5, 0.0)


def test_a_zero_span_objective_gives_every_point_the_same_component():
    """No discriminatory power, so it must not decide the order."""
    assert normalize_objective([7.0, 7.0, 7.0], MAX_ISP) == (
        ZERO_SPAN_COMPONENT,) * 3


def test_a_zero_span_objective_does_not_divide_by_zero():
    values = normalize_objective([7.0, 7.0], MIN_TC)
    assert all(math.isfinite(value) for value in values)


#: Three points, two objectives, weights 3 and 1 → effective 0.75 and 0.25.
#:
#:   isp: 300, 320, 340  → maximise → 0.0, 0.5, 1.0
#:   tc: 3000, 3200, 3400 → minimise → 1.0, 0.5, 0.0
#:
#:   score 0 = 0.75·0.0 + 0.25·1.0 = 0.25
#:   score 1 = 0.75·0.5 + 0.25·0.5 = 0.50
#:   score 2 = 0.75·1.0 + 0.25·0.0 = 0.75
SCORE_FIXTURE = [
    (0, {"isp": 300.0, "tc": 3000.0}),
    (1, {"isp": 320.0, "tc": 3200.0}),
    (2, {"isp": 340.0, "tc": 3400.0}),
]


def test_the_hand_computed_scores_are_reproduced():
    definition = WeightedScoreDefinition(weights={"isp": 3.0, "tc": 1.0})
    scores = score_points(SCORE_FIXTURE, [MAX_ISP, MIN_TC], definition)
    assert scores[0] == pytest.approx(0.25, abs=1e-12)
    assert scores[1] == pytest.approx(0.50, abs=1e-12)
    assert scores[2] == pytest.approx(0.75, abs=1e-12)


def test_the_effective_weights_are_exposed_and_the_raw_ones_kept():
    definition = WeightedScoreDefinition(weights={"isp": 3.0, "tc": 1.0})
    assert definition.weights == {"isp": 3.0, "tc": 1.0}      # as typed
    assert definition.effective_weights == {"isp": 0.75, "tc": 0.25}


def test_flipping_the_weights_reverses_the_ranking():
    isp_heavy = WeightedScoreDefinition(weights={"isp": 3.0, "tc": 1.0})
    tc_heavy = WeightedScoreDefinition(weights={"isp": 1.0, "tc": 3.0})
    a = score_points(SCORE_FIXTURE, [MAX_ISP, MIN_TC], isp_heavy)
    b = score_points(SCORE_FIXTURE, [MAX_ISP, MIN_TC], tc_heavy)
    assert max(a, key=a.get) == 2
    assert max(b, key=b.get) == 0


def test_weights_must_be_non_negative_and_not_all_zero():
    with pytest.raises(ValueError, match="at or above zero"):
        WeightedScoreDefinition(weights={"isp": -1.0})
    with pytest.raises(ValueError, match="above zero"):
        WeightedScoreDefinition(weights={"isp": 0.0, "tc": 0.0})
    with pytest.raises(ValueError):
        WeightedScoreDefinition(weights={})


def test_a_point_missing_an_objective_value_is_not_scored():
    """Absent, not zero -- a zero would rank it above a merely poor design."""
    entries = SCORE_FIXTURE + [(3, {"isp": None, "tc": 3000.0})]
    definition = WeightedScoreDefinition(weights={"isp": 1.0, "tc": 1.0})
    scores = score_points(entries, [MAX_ISP, MIN_TC], definition)
    assert 3 not in scores
    assert set(scores) == {0, 1, 2}


def test_the_normalisation_method_is_named_explicitly():
    definition = WeightedScoreDefinition(weights={"isp": 1.0})
    assert definition.method is NormalizationMethod.MIN_MAX_OVER_FEASIBLE
    assert "feasible" in definition.method.label.lower()


def test_a_score_is_relative_to_its_population():
    """The same design scores differently in a different study. Stated, not hidden."""
    definition = WeightedScoreDefinition(weights={"isp": 1.0})
    narrow = score_points([(0, {"isp": 300.0}), (1, {"isp": 320.0})],
                          [MAX_ISP], definition)
    wide = score_points([(0, {"isp": 300.0}), (1, {"isp": 320.0}),
                         (2, {"isp": 400.0})], [MAX_ISP], definition)
    assert narrow[1] == 1.0
    assert wide[1] < 1.0            # the same design, a different population


# ===========================================================================
# the separations that matter
# ===========================================================================


def test_scoring_does_not_change_pareto_membership():
    """Mandatory regression. Dominance never sees a weight."""
    before = pareto_front(SCORE_FIXTURE, [MAX_ISP, MIN_TC])
    for weights in ({"isp": 1.0, "tc": 1.0}, {"isp": 1000.0, "tc": 0.001},
                    {"isp": 0.0, "tc": 1.0}):
        score_points(SCORE_FIXTURE, [MAX_ISP, MIN_TC],
                     WeightedScoreDefinition(weights=weights))
        assert pareto_front(SCORE_FIXTURE, [MAX_ISP, MIN_TC]) == before


def test_scoring_does_not_change_a_constraint_verdict():
    constraint = ConstraintDefinition("tc", ComparisonOperator.LE, 3100.0)
    before = [constraint.satisfied_by(metrics["tc"])
              for _, metrics in SCORE_FIXTURE]
    score_points(SCORE_FIXTURE, [MAX_ISP, MIN_TC],
                 WeightedScoreDefinition(weights={"isp": 5.0, "tc": 0.1}))
    after = [constraint.satisfied_by(metrics["tc"])
             for _, metrics in SCORE_FIXTURE]
    assert before == after == [True, False, False]


def test_a_constraint_is_never_turned_into_a_score_penalty():
    """An infeasible point is infeasible, not 'scored lower'."""
    outcome = evaluate_constraints(
        {"tc": 3610.0},
        [ConstraintDefinition("tc", ComparisonOperator.LE, 3500.0)])[0]
    assert outcome.satisfied is False
    assert not hasattr(outcome, "penalty")
    assert not hasattr(outcome, "deduction")
