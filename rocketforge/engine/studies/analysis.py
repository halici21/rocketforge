"""Decision analysis: constraints, feasibility, Pareto, optional score.

Runs once, over a complete population, on raw results that already exist. That
is the whole reason re-analysis is cheap: changing an objective direction, a
constraint limit or a weight re-runs *this* module and nothing else. No
provider is called, no physics is recomputed, and the raw metrics are passed
through by reference so they cannot be altered by anything here.

The order is fixed and each step depends only on the ones before it:

    constraints  ->  feasibility  ->  Pareto  ->  ranking  ->  optional score

Score is last and feeds back into nothing. A weight cannot move a front, and a
front cannot move a feasibility verdict.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .constraints import evaluate_constraints
from .objectives import rank_by_objective
from .pareto import pareto_membership
from .results import Feasibility, StudyPointResult, StudyResult
from .scoring import score_points

__all__ = ["analyse", "apply_constraints", "decide_feasibility"]


def decide_feasibility(result: StudyPointResult,
                       outcomes: Sequence[Any]) -> Feasibility:
    """Feasible, infeasible, or not assessable. Three answers, not two.

    A point whose metrics were never produced has not violated anything.
    Reporting it as infeasible would turn a limitation of the model into a
    verdict about the design, which is the single most misleading thing this
    layer could do.
    """
    if not result.status.produced_metrics:
        return Feasibility.NOT_EVALUATED
    if not outcomes:
        return Feasibility.FEASIBLE
    if any(outcome.satisfied is False for outcome in outcomes):
        return Feasibility.INFEASIBLE
    if any(outcome.satisfied is None for outcome in outcomes):
        return Feasibility.NOT_EVALUATED
    return Feasibility.FEASIBLE


def apply_constraints(results: Sequence[StudyPointResult],
                      constraints: Sequence[Any]
                      ) -> list[StudyPointResult]:
    """Attach constraint outcomes and a feasibility verdict to each point."""
    updated = []
    for result in results:
        outcomes = evaluate_constraints(result.metrics, constraints)
        updated.append(result.with_decision(
            feasibility=decide_feasibility(result, outcomes),
            constraint_outcomes=outcomes))
    return updated


def analyse(raw: StudyResult, definition: Any) -> StudyResult:
    """Produce the decision layer for a complete study.

    Takes a result and returns a new one. The input is never mutated: raw
    metrics, diagnostics and point identities are carried across by reference,
    so re-analysing a study a dozen times cannot drift a single number.
    """
    points = apply_constraints(raw.points, definition.constraints)

    eligible = [(result.index, result.metrics) for result in points
                if result.eligible_for_decision]

    objectives = definition.objectives
    membership = (pareto_membership(eligible, objectives)
                  if len(objectives) >= 2 else {})

    ranking: tuple[int, ...] = ()
    if len(objectives) == 1:
        # One objective. A "Pareto front" here is just the best point wearing a
        # grander name, so the study reports a ranking instead and says so.
        objective = objectives[0]
        ordered = rank_by_objective(
            [(index, metrics.get(objective.metric))
             for index, metrics in eligible
             if metrics.get(objective.metric) is not None],
            objective)
        ranking = tuple(index for index, _ in ordered)

    scores: dict[int, float] = {}
    if definition.scoring is not None and objectives:
        scores = score_points(eligible, objectives, definition.scoring)

    decided = [
        result.with_decision(
            feasibility=result.feasibility,
            constraint_outcomes=result.constraint_outcomes,
            is_pareto_efficient=membership.get(result.index, False),
            score=scores.get(result.index))
        for result in points
    ]

    pareto_indices = tuple(result.index for result in decided
                           if result.is_pareto_efficient)

    if not ranking and scores:
        # With a score and two or more objectives, the ranking is by score.
        # Pareto membership is untouched by it -- the two answer different
        # questions and are shown as separate columns.
        ranking = tuple(index for index, _ in
                        sorted(scores.items(),
                               key=lambda entry: (-entry[1], entry[0])))

    return StudyResult(
        definition=raw.definition,
        points=tuple(decided),
        status=raw.status,
        counts=raw.counts,
        provenance=raw.provenance,
        diagnostics=raw.diagnostics,
        pareto_indices=pareto_indices,
        ranking=ranking,
        scored=bool(scores),
        message=raw.message)
