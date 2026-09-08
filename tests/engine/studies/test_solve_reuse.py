"""Solve reuse — the blocking property of Phase 5F.

A study point count is not a solve count. The three mandatory cases from the
brief are here, plus the negative controls that stop them being vacuous, plus
the failure-caching case that is easy to get wrong because it only shows up
when something refuses.

Every count is measured by a recording evaluator. There is no timing, no cache
statistic and no proxy: the claim is "the upstream stage ran 41 times", so the
test counts the times it ran.
"""

from __future__ import annotations

import pytest

from rocketforge.engine.studies import (
    EvaluationStatus,
    ExplicitNumericVariable,
    LinearRangeVariable,
    StudyRunner,
    run_study,
)


# ===========================================================================
# CASE A — 41 upstream × 10 downstream = 410 points, 41 upstream solves
# ===========================================================================


def test_case_a_410_points_cost_41_upstream_solves(
        make_study, registry, evaluator, upstream_variable, downstream_variable):
    """The canonical proof. 410 design points, 41 chemistry states."""
    study = make_study([upstream_variable, downstream_variable])
    assert study.point_count == 410
    assert study.unique_solves("upstream") == 41

    result = run_study(study, registry, evaluator)

    assert len(result.points) == 410
    assert evaluator.upstream_calls == 41
    assert evaluator.downstream_calls == 410
    assert result.counts.stage_solves == {"upstream": 41, "downstream": 410}


def test_case_a_every_point_still_got_an_answer(
        make_study, registry, evaluator, upstream_variable, downstream_variable):
    """Reuse must not cost coverage."""
    study = make_study([upstream_variable, downstream_variable])
    result = run_study(study, registry, evaluator)
    assert all(point.ok for point in result.points)
    assert all(point.metrics["beta"] is not None for point in result.points)


# ===========================================================================
# CASE B — fixed upstream, two downstream variables = 1 upstream solve
# ===========================================================================


def test_case_b_fifty_points_cost_one_upstream_solve(
        make_study, registry, evaluator):
    """Nothing upstream varies, so the upstream stage runs exactly once."""
    y = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                entries=(1.0, 2.0, 3.0, 4.0, 5.0,
                                         6.0, 7.0, 8.0, 9.0, 10.0))
    z = ExplicitNumericVariable(key="z", label="Z", stage="downstream",
                                entries=(0.0, 0.25, 0.5, 0.75, 1.0))
    study = make_study([y, z])

    assert study.point_count == 50
    assert study.unique_solves("upstream") == 1

    result = run_study(study, registry, evaluator)
    assert len(result.points) == 50
    assert evaluator.upstream_calls == 1
    assert evaluator.downstream_calls == 50


# ===========================================================================
# CASE C — two upstream variables multiply
# ===========================================================================


def test_case_c_upstream_variables_multiply(make_study, registry, evaluator):
    """5 × 4 upstream values × 3 downstream = 60 points, 20 upstream solves."""
    x = ExplicitNumericVariable(key="x", label="X", stage="upstream",
                                entries=(1.0, 2.0, 3.0, 4.0, 5.0))
    w = ExplicitNumericVariable(key="w", label="W", stage="upstream",
                                entries=(10.0, 20.0, 30.0, 40.0))
    y = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                entries=(1.0, 2.0, 3.0))
    study = make_study([x, w, y])

    assert study.point_count == 60
    assert study.unique_solves("upstream") == 20

    result = run_study(study, registry, evaluator)
    assert evaluator.upstream_calls == 20
    assert evaluator.downstream_calls == 60


# ===========================================================================
# negative controls -- the counter is not vacuously constant
# ===========================================================================


def test_adding_an_upstream_value_adds_an_upstream_solve(
        make_study, registry, downstream_variable, evaluator_class):
    """An upstream variable genuinely drives the expensive stage."""
    small = evaluator_class()
    large = evaluator_class()
    x_small = LinearRangeVariable(key="x", label="X", stage="upstream",
                                  start=2.5, end=4.5, count=5)
    x_large = LinearRangeVariable(key="x", label="X", stage="upstream",
                                  start=2.5, end=4.5, count=6)

    run_study(make_study([x_small, downstream_variable]), registry, small)
    run_study(make_study([x_large, downstream_variable]), registry, large)

    assert small.upstream_calls == 5
    assert large.upstream_calls == 6


def test_adding_a_downstream_value_adds_no_upstream_solve(
        make_study, registry, upstream_variable, evaluator_class):
    """The property the whole planner exists for, stated as a difference."""
    few = evaluator_class()
    many = evaluator_class()
    y_few = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                    entries=(1.0, 2.0))
    y_many = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                     entries=tuple(float(v) for v in range(1, 21)))

    run_study(make_study([upstream_variable, y_few]), registry, few)
    run_study(make_study([upstream_variable, y_many]), registry, many)

    assert few.upstream_calls == 41
    assert many.upstream_calls == 41           # ten times the points
    assert few.downstream_calls == 82
    assert many.downstream_calls == 820


def test_the_upstream_key_ignores_downstream_values(
        make_study, registry, evaluator, upstream_variable):
    """Structural check on the recorded calls, not just on the total."""
    y = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                entries=(1.0, 2.0, 3.0))
    run_study(make_study([upstream_variable, y]), registry, evaluator)
    upstream_x = [values["x"] for stage, values in evaluator.calls
                  if stage == "upstream"]
    assert len(upstream_x) == len(set(upstream_x)) == 41


# ===========================================================================
# failure caching
# ===========================================================================


def test_a_failed_upstream_state_is_solved_once_not_once_per_dependent(
        make_study, registry, upstream_variable, downstream_variable,
        evaluator_class):
    """Ten dependents of one refusal cost one call, not ten."""
    evaluator = evaluator_class(fail_upstream_at=(2.5, 3.0))
    study = make_study([upstream_variable, downstream_variable])
    result = run_study(study, registry, evaluator)

    assert evaluator.upstream_calls == 41       # still one per state
    failed = [p for p in result.points if p.status is EvaluationStatus.FAILED]
    assert len(failed) == 20                    # 2 states × 10 downstream
    assert all(p.metrics.get("beta") is None for p in failed)


def test_a_failed_upstream_state_costs_no_downstream_calls(
        make_study, registry, upstream_variable, downstream_variable,
        evaluator_class):
    """Nothing downstream is attempted on a chamber that did not solve."""
    evaluator = evaluator_class(fail_upstream_at=(2.5,))
    run_study(make_study([upstream_variable, downstream_variable]),
              registry, evaluator)
    assert evaluator.downstream_calls == 400    # 410 minus the ten dependents


def test_failed_points_are_kept_with_their_variable_values(
        make_study, registry, upstream_variable, downstream_variable,
        evaluator_class):
    """A hole in the design space is information, not a row to delete."""
    evaluator = evaluator_class(fail_upstream_at=(2.5,))
    result = run_study(make_study([upstream_variable, downstream_variable]),
                       registry, evaluator)

    assert len(result.points) == 410            # nothing dropped
    failed = [p for p in result.points if p.status is EvaluationStatus.FAILED]
    assert len(failed) == 10
    for point in failed:
        assert point.values["x"] == 2.5
        assert point.values["y"] is not None
        assert point.message


def test_a_downstream_failure_does_not_poison_its_upstream_state(
        make_study, registry, upstream_variable, evaluator_class):
    """One bad area ratio must not invalidate the chamber it shares."""
    y = ExplicitNumericVariable(key="y", label="Y", stage="downstream",
                                entries=(1.0, 2.0, 3.0))
    evaluator = evaluator_class(fail_downstream_at=(2.0,))
    result = run_study(make_study([upstream_variable, y]), registry, evaluator)

    failed = [p for p in result.points if p.status is EvaluationStatus.FAILED]
    assert len(failed) == 41
    assert all(p.values["y"] == 2.0 for p in failed)
    assert evaluator.upstream_calls == 41


# ===========================================================================
# stage planning
# ===========================================================================


def test_an_upstream_only_study_never_runs_the_downstream_stage(
        make_study, registry, evaluator, upstream_variable):
    """A chamber-temperature study must not compute an Isp nobody asked for."""
    study = make_study([upstream_variable], outputs=("alpha",))
    assert study.required_stages(registry) == ("upstream",)

    result = run_study(study, registry, evaluator)
    assert evaluator.upstream_calls == 41
    assert evaluator.downstream_calls == 0
    assert all(p.metrics.get("alpha") is not None for p in result.points)


def test_a_downstream_metric_pulls_in_both_stages(
        make_study, registry, evaluator, upstream_variable):
    study = make_study([upstream_variable], outputs=("beta",))
    assert study.required_stages(registry) == ("upstream", "downstream")
    run_study(study, registry, evaluator)
    assert evaluator.downstream_calls == 41


def test_the_expected_solve_preview_matches_what_actually_ran(
        make_study, registry, evaluator, upstream_variable, downstream_variable):
    """The number shown before Run must be the number that happens."""
    study = make_study([upstream_variable, downstream_variable])
    runner = StudyRunner(study, registry, evaluator)
    expected = runner.expected_solves()

    result = runner.run()
    assert expected == {"upstream": 41, "downstream": 410}
    assert dict(result.counts.stage_solves) == expected


def test_the_cache_is_study_local(make_study, registry, upstream_variable,
                                  downstream_variable, evaluator_class):
    """A second study re-solves; it does not inherit the first one's cache.

    Sharing across studies would make a result depend on what happened to have
    been run before it, which is the opposite of reproducible.
    """
    study = make_study([upstream_variable, downstream_variable])
    first = evaluator_class()
    second = evaluator_class()
    run_study(study, registry, first)
    run_study(study, registry, second)
    assert first.upstream_calls == 41
    assert second.upstream_calls == 41
