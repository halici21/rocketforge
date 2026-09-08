"""Running a study: the dependency planner, the study-local cache, the runner.

This is where the phase's central optimisation lives. A study point count is
not a solve count::

    41 O/F values × 10 area ratios  =  410 design points
                                    =   41 chamber solves
                                    =  410 performance evaluations

Not 410 chamber solves. The mechanism is deliberately simple: each stage is
evaluated once per distinct **stage key**, and a stage key contains only the
variables at or before that stage. An area ratio declared at the performance
stage therefore cannot appear in the chemistry key, and the reuse follows
structurally rather than from a cache that happens to hit.

Failures are cached too. If one chamber state will not converge and ten area
ratios depend on it, that is one refused solve and ten downstream points that
name the same upstream failure -- not ten more attempts at something already
known not to work.

The cache is **study-local**. A process-global scientific cache would outlive
the provenance that makes its entries meaningful, and would make two studies
silently share a result whose model assumptions might differ.

The runner is a generator so the application can drive it in chunks between Qt
event-loop turns. Provider calls stay serial: Phase 5B-0 measured threading and
found no gain, and concurrent chemistry would trade a proven property for an
unproven one.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from .constraints import evaluate_constraints
from .definition import StudyDefinition
from .enumeration import DesignPoint, stage_key
from .metrics import MetricRegistry
from .results import (
    EvaluationCounts,
    EvaluationStatus,
    Feasibility,
    StudyDiagnostic,
    StudyPointResult,
    StudyResult,
    StudyStatus,
)
from .analysis import analyse

__all__ = [
    "StageOutcome",
    "StudyEvaluator",
    "StudyProgress",
    "StudyRunner",
    "run_study",
]


@dataclass(frozen=True, slots=True)
class StageOutcome:
    """What one evaluation stage produced for one stage key.

    ``value`` is opaque to this package and is handed to the next stage
    untouched -- for RocketForge it is a chamber outcome, then a performance
    outcome, and this module never looks inside either.
    """

    ok: bool
    value: Any = None
    metrics: Mapping[str, float | None] = field(default_factory=dict)
    diagnostics: tuple[Any, ...] = ()
    message: str = ""
    warning: bool = False

    @classmethod
    def failure(cls, message: str, diagnostics: Sequence[Any] = ()) -> "StageOutcome":
        return cls(ok=False, message=message, diagnostics=tuple(diagnostics))


class StudyEvaluator(Protocol):
    """What a domain must supply to be studied.

    One method. Everything domain-specific -- which provider, which services,
    what a metric means -- lives behind it, which is what keeps this package
    free of any dependency on rockets.
    """

    def evaluate(self, stage: str, point: DesignPoint,
                 upstream: Any) -> StageOutcome:
        """Evaluate one stage for one point, given the previous stage's value."""
        ...


@dataclass(frozen=True, slots=True)
class StudyProgress:
    """Where a run has got to.

    Reports real work, not a synthesised percentage. ``stage_solves`` counts
    distinct evaluations actually performed, so a progress line can say "41 of
    41 chamber states, 300 of 410 points" and both halves mean something.
    """

    points_total: int
    points_done: int
    stage: str = ""
    stage_solves_total: Mapping[str, int] = field(default_factory=dict)
    stage_solves_done: Mapping[str, int] = field(default_factory=dict)
    cancelled: bool = False

    @property
    def fraction(self) -> float:
        if self.points_total <= 0:
            return 0.0
        return min(1.0, self.points_done / self.points_total)


class StudyRunner:
    """Evaluates a study, one point at a time, with per-stage reuse.

    Drive it with :meth:`run` when nothing else needs the thread, or step it
    with :meth:`steps` to keep an event loop responsive. Both produce the same
    result: the generator is the only implementation, and ``run`` exhausts it.
    """

    __slots__ = ("_definition", "_registry", "_evaluator", "_stages",
                 "_points", "_cache", "_counts", "_results", "_started",
                 "_cancelled", "_scale_available")

    def __init__(self, definition: StudyDefinition, registry: MetricRegistry,
                 evaluator: StudyEvaluator, *,
                 scale_available: bool = True) -> None:
        self._definition = definition
        self._registry = registry
        self._evaluator = evaluator
        self._scale_available = scale_available
        self._stages = definition.required_stages(registry)
        self._points = definition.enumerate()
        self._cache: dict[tuple[str, tuple], StageOutcome] = {}
        self._counts: dict[str, int] = {stage: 0 for stage in self._stages}
        self._results: list[StudyPointResult] = []
        self._started = 0.0
        self._cancelled = False

    # -- introspection, available before running -------------------------

    @property
    def points_total(self) -> int:
        return len(self._points)

    @property
    def stages(self) -> tuple[str, ...]:
        return self._stages

    def expected_solves(self) -> dict[str, int]:
        """How many evaluations each required stage will need.

        Computed from variable cardinalities, so the workload preview costs
        nothing even for a study far too large to enumerate.
        """
        return {stage: self._definition.unique_solves(stage)
                for stage in self._stages}

    def cancel(self) -> None:
        self._cancelled = True

    # -- the run ---------------------------------------------------------

    def steps(self) -> Iterator[StudyProgress]:
        """Evaluate one point per iteration, yielding progress.

        Physics only. No constraint is checked, no front is computed and no
        score is assigned here -- decision analysis is a population-level
        question and is answered once, after every point exists, by
        :func:`analyse`. Recomputing a front after each point would be both
        wasteful and misleading, since an intermediate front is a front over a
        subset nobody chose.
        """
        self._started = time.perf_counter()
        expected = self.expected_solves()
        for point in self._points:
            if self._cancelled:
                yield StudyProgress(
                    points_total=len(self._points),
                    points_done=len(self._results),
                    stage_solves_total=expected,
                    stage_solves_done=dict(self._counts),
                    cancelled=True)
                return
            self._results.append(self._evaluate_point(point))
            yield StudyProgress(
                points_total=len(self._points),
                points_done=len(self._results),
                stage=self._stages[-1] if self._stages else "",
                stage_solves_total=expected,
                stage_solves_done=dict(self._counts))

    def _evaluate_point(self, point: DesignPoint) -> StudyPointResult:
        """Walk the required stages for one point, reusing what it can."""
        metrics: dict[str, float | None] = {}
        diagnostics: list[Any] = []
        upstream: Any = None
        warned = False
        reached = ""

        for stage in self._stages:
            key = (stage, stage_key(point, self._definition.variables,
                                    self._definition.stage_order, stage))
            outcome = self._cache.get(key)
            if outcome is None:
                outcome = self._evaluator.evaluate(stage, point, upstream)
                self._cache[key] = outcome
                self._counts[stage] = self._counts.get(stage, 0) + 1
            # A cached failure is reused exactly like a cached success. Ten
            # area ratios over one chamber that would not converge is one
            # refused solve, not ten.
            diagnostics.extend(outcome.diagnostics)
            if outcome.warning:
                warned = True
            if not outcome.ok:
                return StudyPointResult(
                    point=point,
                    status=EvaluationStatus.FAILED,
                    metrics=metrics,
                    diagnostics=tuple(diagnostics),
                    message=outcome.message,
                    stage_reached=reached)
            metrics.update(outcome.metrics)
            upstream = outcome.value
            reached = stage

        missing = [key for key in self._definition.required_metrics
                   if metrics.get(key) is None]
        if missing:
            # Every stage succeeded and a required metric still is not there.
            # Distinct from a failure: the upstream numbers this point did
            # produce are valid and worth keeping.
            return StudyPointResult(
                point=point,
                status=EvaluationStatus.NOT_EVALUABLE,
                metrics=metrics,
                diagnostics=tuple(diagnostics),
                message=("this point produced no value for "
                         f"{', '.join(sorted(missing))}, which this study "
                         "requires"),
                stage_reached=reached)

        return StudyPointResult(
            point=point,
            status=(EvaluationStatus.WARNING if warned
                    else EvaluationStatus.SUCCESS),
            metrics=metrics,
            diagnostics=tuple(diagnostics),
            stage_reached=reached)

    def run(self, *, on_progress: Callable[[StudyProgress], None] | None = None,
            should_cancel: Callable[[], bool] | None = None) -> StudyResult:
        """Evaluate everything, then analyse. Serial, and never parallel."""
        last: StudyProgress | None = None
        for progress in self.steps():
            last = progress
            if on_progress is not None:
                on_progress(progress)
            if should_cancel is not None and should_cancel():
                self.cancel()
        return self.finish(cancelled=bool(last and last.cancelled)
                           or self._cancelled)

    def finish(self, *, cancelled: bool = False) -> StudyResult:
        """Package what has been evaluated, and analyse it if it is complete."""
        elapsed = (time.perf_counter() - self._started) if self._started else 0.0
        counts = EvaluationCounts(
            points=len(self._points),
            evaluated=len(self._results),
            stage_solves=dict(self._counts),
            elapsed_seconds=elapsed)
        status = (StudyStatus.CANCELLED
                  if cancelled or len(self._results) < len(self._points)
                  else StudyStatus.COMPLETE)

        raw = StudyResult(
            definition=self._definition,
            points=tuple(self._results),
            status=status,
            counts=counts,
            diagnostics=aggregate_diagnostics(self._results),
            message=("The study was cancelled. The points below were evaluated; "
                     "no front, ranking or score is shown, because they would "
                     "describe a design space that was only partly explored."
                     if status is StudyStatus.CANCELLED else ""))
        if status is not StudyStatus.COMPLETE:
            return raw
        return analyse(raw, self._definition)


def aggregate_diagnostics(results: Sequence[StudyPointResult]
                          ) -> tuple[StudyDiagnostic, ...]:
    """Collapse repeated per-point diagnostics into one row each.

    410 identical assigned-enthalpy warnings are one fact about the study. The
    per-point diagnostics stay on their points and remain inspectable; this is
    the summary, and it exists so the one warning that occurred twice is not
    buried under the one that occurred everywhere.
    """
    table: dict[str, dict[str, Any]] = {}
    total = len(results)
    for result in results:
        seen_here: set[str] = set()
        for diagnostic in result.diagnostics:
            code = getattr(diagnostic, "code", None) or str(diagnostic)
            if code in seen_here:
                continue
            seen_here.add(code)
            entry = table.setdefault(code, {
                "code": code,
                "severity": str(getattr(diagnostic, "severity", "info")),
                "message": getattr(diagnostic, "message", ""),
                "origin": str(getattr(diagnostic, "origin", "")),
                "count": 0,
            })
            entry["count"] += 1
    order = {"error": 0, "warning": 1, "info": 2}
    rows = [StudyDiagnostic(code=entry["code"], severity=entry["severity"],
                            message=entry["message"], count=entry["count"],
                            total=total, origin=entry["origin"])
            for entry in table.values()]
    rows.sort(key=lambda row: (order.get(row.severity, 3), -row.count, row.code))
    return tuple(rows)


def run_study(definition: StudyDefinition, registry: MetricRegistry,
              evaluator: StudyEvaluator, *,
              scale_available: bool = True,
              on_progress: Callable[[StudyProgress], None] | None = None,
              should_cancel: Callable[[], bool] | None = None) -> StudyResult:
    """Run one study to completion. The headless entry point."""
    runner = StudyRunner(definition, registry, evaluator,
                         scale_available=scale_available)
    return runner.run(on_progress=on_progress, should_cancel=should_cancel)
