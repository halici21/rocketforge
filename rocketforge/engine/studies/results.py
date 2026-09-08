"""What a study produced: per point, and in aggregate.

Two status fields, deliberately not one.

``EvaluationStatus`` answers "did the model produce an answer here?" and
``Feasibility`` answers "is that answer a design anyone may choose?". They are
different questions with different owners -- the first belongs to the physics,
the second to the user's constraints -- and a single overloaded enum makes it
impossible to tell a chamber that would not converge from a chamber that
converged at 3610 K when the limit was 3500.

Failed points are kept. A design space with holes in it is information: the
holes are where the model stops working, and deleting the rows that show that
leaves a chart implying the space is continuous.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .constraints import ConstraintOutcome
from .enumeration import DesignPoint

__all__ = [
    "EvaluationStatus",
    "Feasibility",
    "StudyStatus",
    "StudyPointResult",
    "StudyDiagnostic",
    "StudyResult",
    "EvaluationCounts",
]


class EvaluationStatus(StrEnum):
    """Whether the model produced the metrics this study required."""

    SUCCESS = "success"
    WARNING = "warning"
    """Evaluated, with a scientific caveat attached. **Not** a failure, and not
    an infeasibility -- an assigned-enthalpy reactant produces a usable chamber
    state that a reader should know something about."""

    FAILED = "failed"
    """A stage refused or errored. No usable metrics for the required set."""

    NOT_EVALUABLE = "not_evaluable"
    """Every stage that ran succeeded, but a metric the study *requires* is not
    available -- a performance refusal in a study whose objective is Isp. Kept
    distinct from FAILED because the point may still carry valid upstream
    numbers."""

    @property
    def produced_metrics(self) -> bool:
        return self in (EvaluationStatus.SUCCESS, EvaluationStatus.WARNING)

    @property
    def label(self) -> str:
        return {
            EvaluationStatus.SUCCESS: "Evaluated",
            EvaluationStatus.WARNING: "Evaluated with warnings",
            EvaluationStatus.FAILED: "Evaluation failed",
            EvaluationStatus.NOT_EVALUABLE: "Required metric unavailable",
        }[self]


class Feasibility(StrEnum):
    """Whether the point satisfies the user's hard constraints."""

    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    NOT_EVALUATED = "not_evaluated"
    """No verdict is possible -- the point did not produce the metrics the
    constraints refer to. Not the same as infeasible, and never displayed as
    such: a model limitation is not an engineering verdict."""

    @property
    def label(self) -> str:
        return {
            Feasibility.FEASIBLE: "Feasible",
            Feasibility.INFEASIBLE: "Infeasible",
            Feasibility.NOT_EVALUATED: "Not assessed",
        }[self]


class StudyStatus(StrEnum):
    """How far a study got."""

    COMPLETE = "complete"
    CANCELLED = "cancelled"
    FAILED = "failed"

    @property
    def label(self) -> str:
        return {
            StudyStatus.COMPLETE: "Complete",
            StudyStatus.CANCELLED: "Cancelled",
            StudyStatus.FAILED: "Failed",
        }[self]

    @property
    def decision_analysis_valid(self) -> bool:
        """Whether a final Pareto front or ranking may be presented.

        Only for a complete study. A front over half a design space is not a
        front over the design space, and presenting one from a cancelled run
        would let a user choose a design because its competitor had not been
        evaluated yet.
        """
        return self is StudyStatus.COMPLETE


@dataclass(frozen=True, slots=True)
class StudyDiagnostic:
    """One aggregated message across a study.

    Repeated codes are counted rather than repeated: 410 identical
    assigned-enthalpy warnings are one fact about the study, and rendering 410
    cards buries the one that only occurred twice.
    """

    code: str
    severity: str
    message: str
    count: int
    total: int
    origin: str = ""

    @property
    def describe(self) -> str:
        return f"{self.code} — {self.count} of {self.total} points"


@dataclass(frozen=True, slots=True)
class StudyPointResult:
    """One design point, evaluated.

    ``metrics`` holds only what the study asked for, in canonical units, as
    plain floats. A metric that could not be produced is ``None`` -- never
    zero, because a zero thrust is a claim about an engine.
    """

    point: DesignPoint
    status: EvaluationStatus
    metrics: Mapping[str, float | None] = field(default_factory=dict)
    diagnostics: tuple[Any, ...] = ()
    message: str = ""
    feasibility: Feasibility = Feasibility.NOT_EVALUATED
    constraint_outcomes: tuple[ConstraintOutcome, ...] = ()
    is_pareto_efficient: bool = False
    score: float | None = None
    stage_reached: str = ""

    @property
    def index(self) -> int:
        return self.point.index

    @property
    def values(self) -> Mapping[str, Any]:
        return self.point.values

    @property
    def ok(self) -> bool:
        return self.status.produced_metrics

    @property
    def has_warning(self) -> bool:
        return self.status is EvaluationStatus.WARNING

    @property
    def violated(self) -> tuple[ConstraintOutcome, ...]:
        return tuple(outcome for outcome in self.constraint_outcomes
                     if outcome.violated)

    @property
    def eligible_for_decision(self) -> bool:
        """Whether this point may appear on a front or in a ranking.

        Evaluated **and** feasible. Both halves are required, and each excludes
        a different thing: a failed point has nothing to compare, and an
        infeasible one is not a design anyone may choose.
        """
        return (self.status.produced_metrics
                and self.feasibility is Feasibility.FEASIBLE)

    def metric(self, key: str) -> float | None:
        value = self.metrics.get(key)
        if value is None:
            return None
        number = float(value)
        return number if math.isfinite(number) else None

    def with_decision(self, *, feasibility: Feasibility,
                      constraint_outcomes: Sequence[ConstraintOutcome],
                      is_pareto_efficient: bool = False,
                      score: float | None = None) -> "StudyPointResult":
        """A copy carrying new decision data, with the raw values untouched.

        Re-analysis goes through here. ``metrics``, ``status``, ``diagnostics``
        and ``point`` are passed through by reference, so no re-analysis can
        alter a number the physics produced.
        """
        return StudyPointResult(
            point=self.point,
            status=self.status,
            metrics=self.metrics,
            diagnostics=self.diagnostics,
            message=self.message,
            feasibility=feasibility,
            constraint_outcomes=tuple(constraint_outcomes),
            is_pareto_efficient=is_pareto_efficient,
            score=score,
            stage_reached=self.stage_reached)


@dataclass(frozen=True, slots=True)
class EvaluationCounts:
    """What the run actually cost.

    ``stage_solves`` is the number the whole dependency planner exists to keep
    small, and it is reported rather than inferred: a study that quietly solved
    chemistry once per design point would look identical in every other field.
    """

    points: int = 0
    evaluated: int = 0
    stage_solves: Mapping[str, int] = field(default_factory=dict)
    elapsed_seconds: float = 0.0

    def describe(self) -> str:
        solves = ", ".join(f"{stage}: {count}"
                           for stage, count in sorted(self.stage_solves.items()))
        return f"{self.evaluated}/{self.points} points ({solves})"


@dataclass(frozen=True, slots=True)
class StudyResult:
    """A completed -- or cancelled -- study.

    Holds the definition it came from, so a stored result is readable without
    the form that produced it and cannot be relabelled by a later edit.
    """

    definition: Any
    points: tuple[StudyPointResult, ...]
    status: StudyStatus
    counts: EvaluationCounts
    provenance: Mapping[str, Any] = field(default_factory=dict)
    diagnostics: tuple[StudyDiagnostic, ...] = ()
    pareto_indices: tuple[int, ...] = ()
    ranking: tuple[int, ...] = ()
    scored: bool = False
    message: str = ""

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self):
        return iter(self.points)

    def by_index(self, index: int) -> StudyPointResult | None:
        for result in self.points:
            if result.index == index:
                return result
        return None

    @property
    def complete(self) -> bool:
        return self.status is StudyStatus.COMPLETE

    @property
    def decision_analysis_valid(self) -> bool:
        return self.status.decision_analysis_valid

    @property
    def evaluated_count(self) -> int:
        return sum(1 for result in self.points if result.ok)

    @property
    def warning_count(self) -> int:
        return sum(1 for result in self.points if result.has_warning)

    @property
    def failed_count(self) -> int:
        return sum(1 for result in self.points if not result.ok)

    @property
    def feasible_count(self) -> int:
        return sum(1 for result in self.points
                   if result.feasibility is Feasibility.FEASIBLE)

    @property
    def infeasible_count(self) -> int:
        return sum(1 for result in self.points
                   if result.feasibility is Feasibility.INFEASIBLE)

    @property
    def not_assessed_count(self) -> int:
        return sum(1 for result in self.points
                   if result.feasibility is Feasibility.NOT_EVALUATED)

    @property
    def pareto_count(self) -> int:
        return len(self.pareto_indices)

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "points": len(self.points),
            "evaluated": self.evaluated_count,
            "warnings": self.warning_count,
            "failed": self.failed_count,
            "feasible": self.feasible_count,
            "infeasible": self.infeasible_count,
            "not_assessed": self.not_assessed_count,
            "pareto": self.pareto_count,
            "scored": self.scored,
            "stage_solves": dict(self.counts.stage_solves),
            "elapsed_seconds": self.counts.elapsed_seconds,
        }
