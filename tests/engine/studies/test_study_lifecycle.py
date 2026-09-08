"""Study definitions, validation, re-analysis, cancellation and determinism.

The re-analysis tests are the ones that matter most here: they are how the
phase's second efficiency claim is checked. Changing an objective, a constraint
or a weight must cost **zero** evaluator calls, and the raw physics values must
come out the other side unchanged.
"""

from __future__ import annotations

import pytest

from rocketforge.engine.studies import (
    ComparisonOperator,
    ConstraintDefinition,
    EvaluationStatus,
    ExplicitNumericVariable,
    Feasibility,
    LinearRangeVariable,
    MAX_STUDY_POINTS,
    ObjectiveDefinition,
    ObjectiveDirection,
    StudyRunner,
    StudyStatus,
    StudyValidationError,
    WeightedScoreDefinition,
    analyse,
    run_study,
    validate_definition,
)


# ===========================================================================
# definition validation
# ===========================================================================


def test_a_valid_study_passes(make_study, registry, upstream_variable):
    validate_definition(make_study([upstream_variable], outputs=("alpha",)),
                        registry)


def test_a_duplicate_variable_is_refused(make_study, registry):
    a = ExplicitNumericVariable(key="x", label="X", stage="upstream",
                                entries=(1.0,))
    b = ExplicitNumericVariable(key="x", label="X again", stage="upstream",
                                entries=(2.0,))
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study([a, b], outputs=("alpha",)), registry)
    assert info.value.code == "DUPLICATE_DESIGN_VARIABLE"


def test_a_variable_with_an_unknown_stage_is_refused(make_study, registry):
    bad = ExplicitNumericVariable(key="z", label="Z", stage="nowhere",
                                  entries=(1.0,))
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study([bad], outputs=("alpha",)), registry)
    assert info.value.code == "UNKNOWN_VARIABLE_STAGE"


def test_a_study_that_reports_nothing_is_refused(make_study, registry,
                                                 upstream_variable):
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study([upstream_variable], outputs=()),
                            registry)
    assert info.value.code == "NO_REQUESTED_METRICS"


def test_an_unknown_metric_is_refused_by_name(make_study, registry,
                                              upstream_variable):
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study([upstream_variable],
                                       outputs=("invented",)), registry)
    assert info.value.code == "UNKNOWN_METRIC"
    assert "alpha" in info.value.message          # says what is available


def test_a_scaled_metric_without_a_scale_is_refused_before_running(
        make_study, registry, upstream_variable):
    """400 rows of blanks is not an answer, and this is where it is prevented."""
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study([upstream_variable], outputs=("sized",)),
                            registry, scale_available=False)
    assert info.value.code == "METRIC_REQUIRES_SCALE"


def test_the_same_metric_twice_as_an_objective_is_refused(
        make_study, registry, upstream_variable):
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study(
            [upstream_variable], outputs=("alpha",),
            objectives=(ObjectiveDefinition("alpha", ObjectiveDirection.MAXIMIZE),
                        ObjectiveDefinition("alpha", ObjectiveDirection.MINIMIZE))),
            registry)
    assert info.value.code == "DUPLICATE_OBJECTIVE"


def test_scoring_without_objectives_is_refused(make_study, registry,
                                               upstream_variable):
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study(
            [upstream_variable], outputs=("alpha",),
            scoring=WeightedScoreDefinition(weights={"alpha": 1.0})), registry)
    assert info.value.code == "SCORING_WITHOUT_OBJECTIVES"


def test_an_objective_without_a_weight_is_refused(make_study, registry,
                                                  upstream_variable,
                                                  maximise_beta):
    """An omitted weight is an invisible zero; the study must state it."""
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study(
            [upstream_variable],
            objectives=(maximise_beta,
                        ObjectiveDefinition("alpha", ObjectiveDirection.MINIMIZE)),
            scoring=WeightedScoreDefinition(weights={"beta": 1.0})), registry)
    assert info.value.code == "OBJECTIVE_WITHOUT_SCORE_WEIGHT"


def test_a_study_larger_than_the_cap_is_refused_not_sampled(
        make_study, registry):
    big = [LinearRangeVariable(key=f"v{i}", label=f"V{i}", stage="upstream",
                               start=0.0, end=1.0, count=40) for i in range(3)]
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study(big, outputs=("alpha",)), registry)
    assert info.value.code == "STUDY_TOO_LARGE"
    assert f"{MAX_STUDY_POINTS:,}" in info.value.message


def test_a_variable_that_cannot_affect_anything_is_refused(
        make_study, registry, upstream_variable, downstream_variable):
    """N identical rows would read as 'this barely matters', not 'unused'."""
    with pytest.raises(StudyValidationError) as info:
        validate_definition(make_study([upstream_variable, downstream_variable],
                                       outputs=("alpha",)), registry)
    assert info.value.code == "INEFFECTIVE_DESIGN_VARIABLE"
    assert "identical rows" in info.value.message


def test_a_single_valued_downstream_variable_is_not_ineffective(
        make_study, registry, upstream_variable):
    """One value produces one row, which is a fixed condition, not a flat line."""
    pinned = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                     entries=(4.0,))
    validate_definition(make_study([upstream_variable, pinned],
                                   outputs=("alpha",)), registry)


# ===========================================================================
# fingerprint
# ===========================================================================


def test_the_fingerprint_ignores_the_title(make_study, registry,
                                           upstream_variable):
    a = make_study([upstream_variable], outputs=("alpha",), title="First")
    b = make_study([upstream_variable], outputs=("alpha",), title="Second")
    assert a.fingerprint == b.fingerprint


def test_the_fingerprint_changes_with_a_range(make_study, upstream_variable):
    other = LinearRangeVariable(key="x", label="X", stage="upstream",
                                start=2.5, end=4.5, count=42)
    assert (make_study([upstream_variable], outputs=("alpha",)).fingerprint
            != make_study([other], outputs=("alpha",)).fingerprint)


def test_the_fingerprint_changes_with_an_objective_direction(
        make_study, upstream_variable):
    up = ObjectiveDefinition("alpha", ObjectiveDirection.MAXIMIZE)
    down = ObjectiveDefinition("alpha", ObjectiveDirection.MINIMIZE)
    assert (make_study([upstream_variable], objectives=(up,)).fingerprint
            != make_study([upstream_variable], objectives=(down,)).fingerprint)


def test_the_fingerprint_is_stable_across_calls(make_study, upstream_variable):
    study = make_study([upstream_variable], outputs=("alpha",))
    assert study.fingerprint == study.fingerprint


def test_constraint_order_does_not_change_the_fingerprint(
        make_study, upstream_variable):
    a = ConstraintDefinition("alpha", ComparisonOperator.LE, 200.0)
    b = ConstraintDefinition("beta", ComparisonOperator.GE, 10.0)
    forward = make_study([upstream_variable], constraints=(a, b))
    backward = make_study([upstream_variable], constraints=(b, a))
    assert forward.fingerprint == backward.fingerprint


# ===========================================================================
# statuses
# ===========================================================================


def test_a_point_missing_a_required_metric_is_not_evaluable_not_infeasible(
        make_study, registry, upstream_variable, evaluator_class):
    """A model limitation and a violated limit are different verdicts."""
    y = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                entries=(1.0, 2.0, 3.0))
    evaluator = evaluator_class(missing_downstream_at=(2.0,))
    result = run_study(make_study([upstream_variable, y]), registry, evaluator)

    affected = [p for p in result.points if p.values["y"] == 2.0]
    assert len(affected) == 41
    for point in affected:
        assert point.status is EvaluationStatus.NOT_EVALUABLE
        assert point.feasibility is Feasibility.NOT_EVALUATED
        assert point.metrics.get("alpha") is not None     # upstream survived


def test_a_warning_point_is_evaluated_feasible_and_eligible(
        make_study, registry, upstream_variable, evaluator_class,
        maximise_beta):
    """A caveat is not a failure and not an infeasibility."""
    evaluator = evaluator_class(warn_upstream=True)
    result = run_study(make_study([upstream_variable],
                                  objectives=(maximise_beta,)),
                       registry, evaluator)
    assert all(p.status is EvaluationStatus.WARNING for p in result.points)
    assert all(p.feasibility is Feasibility.FEASIBLE for p in result.points)
    assert result.ranking                       # warning points still rank


def test_repeated_warnings_are_aggregated_but_kept_per_point(
        make_study, registry, upstream_variable, evaluator_class):
    evaluator = evaluator_class(warn_upstream=True)
    result = run_study(make_study([upstream_variable]), registry, evaluator)

    codes = {d.code: d for d in result.diagnostics}
    assert "SYNTHETIC_CAVEAT" in codes
    assert codes["SYNTHETIC_CAVEAT"].count == 41
    assert codes["SYNTHETIC_CAVEAT"].total == 41
    assert all(p.diagnostics for p in result.points)      # still inspectable


def test_an_infeasible_point_keeps_every_raw_number(
        make_study, registry, evaluator, upstream_variable):
    """A violated constraint changes a verdict, never a measurement."""
    study = make_study([upstream_variable], outputs=("alpha",),
                       constraints=(ConstraintDefinition(
                           "alpha", ComparisonOperator.LE, 130.0),))
    result = run_study(study, registry, evaluator)

    infeasible = [p for p in result.points
                  if p.feasibility is Feasibility.INFEASIBLE]
    assert infeasible
    for point in infeasible:
        assert point.status is EvaluationStatus.SUCCESS   # the physics worked
        assert point.metrics["alpha"] is not None
        assert point.violated                             # says which limit


def test_an_infeasible_point_is_excluded_from_the_front_but_not_the_table(
        make_study, registry, evaluator, upstream_variable, maximise_beta,
        minimise_alpha):
    """Letting one dominate would remove a buildable design for an unbuildable."""
    study = make_study([upstream_variable],
                       objectives=(maximise_beta, minimise_alpha),
                       constraints=(ConstraintDefinition(
                           "alpha", ComparisonOperator.LE, 130.0),))
    result = run_study(study, registry, evaluator)

    assert len(result.points) == 41                       # nothing removed
    assert result.infeasible_count > 0
    for index in result.pareto_indices:
        assert result.by_index(index).feasibility is Feasibility.FEASIBLE


def test_a_failed_point_is_excluded_from_the_front_but_not_the_table(
        make_study, registry, upstream_variable, evaluator_class,
        maximise_beta, minimise_alpha):
    evaluator = evaluator_class(fail_upstream_at=(2.5, 4.5))
    study = make_study([upstream_variable],
                       objectives=(maximise_beta, minimise_alpha))
    result = run_study(study, registry, evaluator)

    assert len(result.points) == 41
    assert result.failed_count == 2
    for index in result.pareto_indices:
        assert result.by_index(index).ok


# ===========================================================================
# re-analysis — zero evaluator calls
# ===========================================================================


def test_changing_an_objective_direction_costs_no_evaluator_calls(
        make_study, registry, evaluator, upstream_variable, maximise_beta):
    study = make_study([upstream_variable], objectives=(maximise_beta,))
    result = run_study(study, registry, evaluator)
    before = len(evaluator.calls)

    flipped = study.replace(objectives=(
        ObjectiveDefinition("beta", ObjectiveDirection.MINIMIZE),))
    reanalysed = analyse(result, flipped)

    assert len(evaluator.calls) == before
    assert reanalysed.ranking[0] != result.ranking[0]     # the order moved
    assert [p.metrics for p in reanalysed.points] == [p.metrics
                                                      for p in result.points]


def test_changing_a_constraint_costs_no_evaluator_calls(
        make_study, registry, evaluator, upstream_variable):
    study = make_study([upstream_variable], outputs=("alpha",))
    result = run_study(study, registry, evaluator)
    before = len(evaluator.calls)

    loose = analyse(result, study.replace(constraints=(
        ConstraintDefinition("alpha", ComparisonOperator.LE, 200.0),)))
    tight = analyse(result, study.replace(constraints=(
        ConstraintDefinition("alpha", ComparisonOperator.LE, 130.0),)))

    assert len(evaluator.calls) == before
    assert loose.feasible_count > tight.feasible_count
    assert loose.infeasible_count < tight.infeasible_count


def test_changing_a_weight_costs_no_evaluator_calls_and_no_pareto_change(
        make_study, registry, evaluator, upstream_variable, maximise_beta,
        minimise_alpha):
    study = make_study([upstream_variable],
                       objectives=(maximise_beta, minimise_alpha),
                       scoring=WeightedScoreDefinition(
                           weights={"beta": 1.0, "alpha": 1.0}))
    result = run_study(study, registry, evaluator)
    before = len(evaluator.calls)

    reweighted = analyse(result, study.replace(
        scoring=WeightedScoreDefinition(weights={"beta": 99.0, "alpha": 0.01})))

    assert len(evaluator.calls) == before
    assert reweighted.pareto_indices == result.pareto_indices
    assert reweighted.scored and result.scored


def test_re_analysis_never_alters_a_raw_value(
        make_study, registry, evaluator, upstream_variable, maximise_beta):
    study = make_study([upstream_variable], objectives=(maximise_beta,))
    result = run_study(study, registry, evaluator)
    snapshot = [dict(p.metrics) for p in result.points]

    for limit in (0.0, 100.0, 1e9):
        analyse(result, study.replace(constraints=(
            ConstraintDefinition("beta", ComparisonOperator.GE, limit),)))

    assert [dict(p.metrics) for p in result.points] == snapshot


def test_re_analysis_returns_a_new_result_and_leaves_the_old_one_alone(
        make_study, registry, evaluator, upstream_variable, maximise_beta):
    study = make_study([upstream_variable], objectives=(maximise_beta,))
    result = run_study(study, registry, evaluator)
    original_feasible = result.feasible_count

    analyse(result, study.replace(constraints=(
        ConstraintDefinition("beta", ComparisonOperator.GE, 1e9),)))

    assert result.feasible_count == original_feasible


# ===========================================================================
# cancellation
# ===========================================================================


def test_a_cancelled_study_keeps_what_it_evaluated(
        make_study, registry, evaluator, upstream_variable, maximise_beta):
    study = make_study([upstream_variable], objectives=(maximise_beta,))
    runner = StudyRunner(study, registry, evaluator)
    for index, _ in enumerate(runner.steps()):
        if index >= 9:
            runner.cancel()
    result = runner.finish(cancelled=True)

    assert result.status is StudyStatus.CANCELLED
    assert 0 < len(result.points) < 41


def test_a_cancelled_study_presents_no_front_ranking_or_score(
        make_study, registry, evaluator, upstream_variable, maximise_beta,
        minimise_alpha):
    study = make_study([upstream_variable],
                       objectives=(maximise_beta, minimise_alpha),
                       scoring=WeightedScoreDefinition(
                           weights={"beta": 1.0, "alpha": 1.0}))
    runner = StudyRunner(study, registry, evaluator)
    for index, _ in enumerate(runner.steps()):
        if index >= 4:
            runner.cancel()
    result = runner.finish(cancelled=True)

    assert not result.decision_analysis_valid
    assert result.pareto_indices == ()
    assert result.ranking == ()
    assert not result.scored
    assert "cancelled" in result.message.lower()


def test_a_complete_study_does_present_decision_analysis(
        make_study, registry, evaluator, upstream_variable, maximise_beta,
        minimise_alpha):
    study = make_study([upstream_variable],
                       objectives=(maximise_beta, minimise_alpha))
    result = run_study(study, registry, evaluator)
    assert result.decision_analysis_valid
    assert result.pareto_indices


# ===========================================================================
# determinism
# ===========================================================================


def test_the_same_study_run_twice_produces_identical_results(
        make_study, registry, upstream_variable, downstream_variable,
        evaluator_class, maximise_beta, minimise_alpha):
    study = make_study([upstream_variable, downstream_variable],
                       objectives=(maximise_beta, minimise_alpha),
                       scoring=WeightedScoreDefinition(
                           weights={"beta": 2.0, "alpha": 1.0}))
    first = run_study(study, registry, evaluator_class())
    second = run_study(study, registry, evaluator_class())

    assert [dict(p.values) for p in first.points] == [dict(p.values)
                                                      for p in second.points]
    assert [dict(p.metrics) for p in first.points] == [dict(p.metrics)
                                                       for p in second.points]
    assert first.pareto_indices == second.pareto_indices
    assert first.ranking == second.ranking
    assert [p.score for p in first.points] == [p.score for p in second.points]
