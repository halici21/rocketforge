"""Synthetic fixtures for the generic design-space engine.

Everything here is deliberately **not** a rocket. The decision algorithms --
enumeration, constraints, feasibility, Pareto, scoring, solve reuse -- are
domain-agnostic, and testing them against a closed-form synthetic evaluator is
what makes it possible to say they are correct independently of the physics
they will later be pointed at.

A synthetic test proves nothing about thermochemistry or nozzle performance,
and none of these fixtures may appear in an artifact that claims otherwise.
The live studies against NASA CEA and RocketForge performance are separate and
are the only place a physical claim is made.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from rocketforge.engine.studies import (
    LinearRangeVariable,
    MetricDefinition,
    MetricRegistry,
    ObjectiveDefinition,
    ObjectiveDirection,
    StageOutcome,
    StudyBaseline,
    StudyDefinition,
)

#: Three stages, named as the RocketForge domain names them, so the generic
#: tests exercise the same shape the real evaluator will.
STAGES = ("upstream", "downstream", "decision")


@pytest.fixture()
def registry() -> MetricRegistry:
    """A small metric set spanning both evaluation stages."""
    return MetricRegistry([
        MetricDefinition("alpha", "Alpha", "upstream", "A",
                         help="Produced by the upstream stage only."),
        MetricDefinition("beta", "Beta", "downstream", "B",
                         help="Needs both stages."),
        MetricDefinition("gamma_out", "Gamma out", "downstream", "",
                         help="Also downstream."),
        MetricDefinition("sized", "Sized quantity", "downstream", "N",
                         requires_scale=True),
    ])


@dataclass
class CountingEvaluator:
    """A deterministic evaluator that records every call it receives.

    The call log is the point. Solve reuse is a claim about *how many times a
    stage ran*, and the only honest way to check it is to count, so this
    fixture counts per stage and keeps the arguments it was given.

    ``fail_upstream_at`` injects a refusal at chosen upstream values, which is
    the only practical way to exercise failure caching: a synthetic evaluator
    that always succeeds can never show that ten dependents of one failure cost
    one call rather than ten.
    """

    fail_upstream_at: tuple[float, ...] = ()
    fail_downstream_at: tuple[float, ...] = ()
    warn_upstream: bool = False
    missing_downstream_at: tuple[float, ...] = ()
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def count(self, stage: str) -> int:
        return sum(1 for name, _ in self.calls if name == stage)

    @property
    def upstream_calls(self) -> int:
        return self.count("upstream")

    @property
    def downstream_calls(self) -> int:
        return self.count("downstream")

    def evaluate(self, stage: str, point, upstream) -> StageOutcome:
        self.calls.append((stage, dict(point.values)))
        x = float(point.values.get("x", 0.0))
        y = float(point.values.get("y", 0.0))

        if stage == "upstream":
            if x in self.fail_upstream_at:
                return StageOutcome.failure(
                    f"synthetic upstream refusal at x={x:g}",
                    diagnostics=(_Diagnostic("UPSTREAM_REFUSED", "error",
                                             "synthetic upstream refusal"),))
            diagnostics = ()
            if self.warn_upstream:
                diagnostics = (_Diagnostic("SYNTHETIC_CAVEAT", "warning",
                                           "a synthetic scientific caveat"),)
            # alpha rises with x; deliberately monotone so a hand-checked
            # expectation is easy to write.
            return StageOutcome(ok=True, value={"alpha": 100.0 + 10.0 * x},
                                metrics={"alpha": 100.0 + 10.0 * x},
                                diagnostics=diagnostics,
                                warning=self.warn_upstream)

        if stage == "downstream":
            if y in self.fail_downstream_at:
                return StageOutcome.failure(
                    f"synthetic downstream refusal at y={y:g}")
            alpha = float(upstream["alpha"])
            if y in self.missing_downstream_at:
                # Every stage succeeded, but the metric the study needs is
                # absent. A different situation from a refusal, and the study
                # must classify it differently.
                return StageOutcome(ok=True, value={},
                                    metrics={"beta": None, "gamma_out": None})
            return StageOutcome(ok=True, value={},
                                metrics={"beta": alpha - 2.0 * y,
                                         "gamma_out": alpha * y,
                                         "sized": alpha * y * 10.0})

        raise AssertionError(f"unexpected stage {stage!r}")


@dataclass(frozen=True, slots=True)
class _Diagnostic:
    code: str
    severity: str
    message: str


@pytest.fixture()
def evaluator() -> CountingEvaluator:
    return CountingEvaluator()


@pytest.fixture()
def evaluator_class():
    """The class itself, for a test that needs to build several.

    Handed over as a fixture rather than imported. ``tests/`` carries no
    ``__init__.py``, so a relative import from a test module fails and a plain
    ``import conftest`` resolves to whichever conftest pytest loaded first --
    a trap this project has now been caught by three times.
    """
    return CountingEvaluator


@pytest.fixture()
def baseline() -> StudyBaseline:
    return StudyBaseline(conditions={"fixed": 1.0},
                         model={"provider": "synthetic", "version": "0"})


@pytest.fixture()
def upstream_variable() -> LinearRangeVariable:
    """41 upstream values, the canonical cache-proof cardinality."""
    return LinearRangeVariable(key="x", label="X", stage="upstream",
                               start=2.5, end=4.5, count=41)


@pytest.fixture()
def downstream_variable() -> LinearRangeVariable:
    """10 downstream values, which must cost no upstream solves."""
    return LinearRangeVariable(key="y", label="Y", stage="downstream",
                               start=1.0, end=10.0, count=10)


@pytest.fixture()
def make_study(baseline, registry):
    """Build a definition without repeating the boilerplate every time."""

    def _make(variables, *, outputs=("beta",), objectives=(), constraints=(),
              scoring=None, stages=STAGES, title="synthetic"):
        return StudyDefinition(
            baseline=baseline,
            variables=tuple(variables),
            stage_order=tuple(stages),
            outputs=tuple(outputs),
            objectives=tuple(objectives),
            constraints=tuple(constraints),
            scoring=scoring,
            title=title)

    return _make


@pytest.fixture()
def maximise_beta() -> ObjectiveDefinition:
    return ObjectiveDefinition("beta", ObjectiveDirection.MAXIMIZE)


@pytest.fixture()
def minimise_alpha() -> ObjectiveDefinition:
    return ObjectiveDefinition("alpha", ObjectiveDirection.MINIMIZE)
