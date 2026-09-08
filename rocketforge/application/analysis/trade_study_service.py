"""The RocketForge trade-study evaluator and service. Qt-free.

Where the generic engine meets the physics. The engine calls
:meth:`RocketForgeEvaluator.evaluate` once per stage key; this module turns
that into a chamber solve or a performance solve using the **canonical**
services from Phase 5D and 5E, and extracts the metrics the study asked for.

Two things it deliberately does not do:

**It does not compute anything.** No c*, no Cf, no Isp, no thrust. Every number
it returns was produced by ``performance_service`` over
``engineering.nozzle``, and a formula appearing here would be a second
implementation of a quantity RocketForge already owns.

**It does not run the CEA performance oracle.** A trade study's physics is
CEA for the chamber and RocketForge for the nozzle. The provider's own c*, Cf
and Isp remain a Phase 5E validation tool, invoked by hand for one case at a
time -- running them per study point would both cost a second chemistry pass
and put a second set of performance numbers where they could be mistaken for
these.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from rocketforge.engine.studies import (
    MetricRegistry,
    StageOutcome,
    StudyBaseline,
    StudyDefinition,
    StudyResult,
    StudyRunner,
    StudyValidationError,
    analyse,
    validate_definition,
)

from . import performance_service as perf
from . import thermochemistry_service as thermo
from .trade_study_domain import (
    STAGE_ORDER,
    STAGE_PERFORMANCE,
    STAGE_THERMOCHEMISTRY,
    metric_registry,
)

__all__ = [
    "TradeStudySetup",
    "RocketForgeEvaluator",
    "build_baseline",
    "build_definition",
    "make_runner",
    "run_trade_study",
    "reanalyse",
    "study_provenance",
    "metric_registry",
]


@dataclass(frozen=True, slots=True)
class TradeStudySetup:
    """The fixed half of a study: what is not varied.

    A snapshot. Once a study is built from one of these, editing the
    Thermochemistry or Rocket Performance workspace cannot reach it -- which is
    what stops a stored study from being relabelled with conditions that did
    not produce it.
    """

    chamber: thermo.ChamberCase
    performance: perf.PerformanceCase
    feed_pressure: float | None = None
    """Pa. The pressure the propellants are *stored and fed at*, which is a
    feed-system state and emphatically not the chamber pressure. ``None``
    means the user did not state one, and then the density metrics are simply
    absent -- never computed at a pressure nobody supplied."""

    @property
    def scale_available(self) -> bool:
        return self.performance.scale.is_scaled

    @property
    def density_metrics_available(self) -> bool:
        """Whether this setup can produce a density impulse at all."""
        if self.feed_pressure is None:
            return False
        from rocketforge.engineering.propellants import PRODUCTION_FLUID_MAPPING

        return (PRODUCTION_FLUID_MAPPING.has(self.chamber.fuel)
                and PRODUCTION_FLUID_MAPPING.has(self.chamber.oxidiser))

    def canonical(self) -> dict[str, Any]:
        case = self.chamber
        return {
            "fuel": case.fuel,
            "oxidiser": case.oxidiser,
            "oxidiser_fuel_ratio": float(case.oxidiser_fuel_ratio),
            "chamber_pressure": float(case.chamber_pressure),
            "fuel_temperature": float(case.fuel_temperature),
            "oxidiser_temperature": float(case.oxidiser_temperature),
            "gamma_strategy": self.performance.gamma_strategy.value,
            "gamma_basis": self.performance.gamma_basis.value,
            "area_ratio": float(self.performance.area_ratio),
            "ambient_pressure": float(self.performance.ambient.pressure),
            "scale_mode": self.performance.scale.mode.value,
            "scale_value": (None if self.performance.scale.value is None
                            else float(self.performance.scale.value)),
            "feed_pressure": (None if self.feed_pressure is None
                              else float(self.feed_pressure)),
        }


def build_baseline(setup: TradeStudySetup) -> StudyBaseline:
    """The immutable baseline the generic engine fingerprints.

    ``model`` is separated from ``conditions`` because they fail differently: a
    changed condition makes a different study, and a changed model makes a
    study whose numbers are not comparable with the previous one at all.
    """
    return StudyBaseline(
        conditions=setup.canonical(),
        model={
            "provider": thermo.PROVIDER_LABEL,
            "chemistry": thermo.MODEL_SUMMARY,
            "performance_model": "RocketForge ideal rocket, constant-property "
                                 "perfect gas, no efficiency factor",
            "gamma_strategy": setup.performance.gamma_strategy.value,
            "gamma_basis": setup.performance.gamma_basis.value,
        },
        label=thermo.case_headline(setup.chamber))


def build_definition(setup: TradeStudySetup, variables: Sequence[Any], *,
                     outputs: Sequence[str] = (),
                     objectives: Sequence[Any] = (),
                     constraints: Sequence[Any] = (),
                     scoring: Any = None,
                     title: str = "") -> StudyDefinition:
    """Assemble a definition. Does not validate -- the caller chooses when."""
    return StudyDefinition(
        baseline=build_baseline(setup),
        variables=tuple(variables),
        stage_order=STAGE_ORDER,
        outputs=tuple(outputs),
        objectives=tuple(objectives),
        constraints=tuple(constraints),
        scoring=scoring,
        title=title)


class RocketForgeEvaluator:
    """Evaluates one study stage for one point, using the canonical services.

    Holds no cache of its own. Reuse is the engine's job, driven by stage keys,
    and a second cache here would be a second place for a stale chamber state
    to hide.
    """

    __slots__ = ("_setup", "_solve_case", "_solve_performance", "_calls",
                 "_densities", "_density_calls")

    def __init__(self, setup: TradeStudySetup, *,
                 solve_case=None, solve_performance=None) -> None:
        self._setup = setup
        # Injected so a test can count calls without patching a module global.
        # Defaults are the canonical services; nothing else is ever used.
        self._solve_case = solve_case or thermo.solve_case
        self._solve_performance = solve_performance or perf.solve_performance
        self._calls: dict[str, int] = {STAGE_THERMOCHEMISTRY: 0,
                                       STAGE_PERFORMANCE: 0}
        # Stream states are fixed for a whole study: nothing a study varies
        # changes a propellant's tank temperature or its feed pressure. So the
        # densities are evaluated at most once each, whatever the point count,
        # and the counter below is what a test asserts that against.
        self._densities: tuple[Any, Any] | None = None
        self._density_calls = 0

    @property
    def calls(self) -> dict[str, int]:
        return dict(self._calls)

    @property
    def fluid_calls(self) -> int:
        """How many times a fluid property was actually evaluated."""
        return self._density_calls

    def stream_densities(self):
        """The two stream densities, evaluated once per study or not at all."""
        if self._densities is not None:
            return self._densities
        if not self._setup.density_metrics_available:
            self._densities = (None, None)
            return self._densities
        from rocketforge.application.analysis.fluid_property_provider import (
            availability,
            property_provider,
        )
        from rocketforge.engineering.propellants import (
            PRODUCTION_FLUID_MAPPING,
            stream_density,
        )

        if not availability().is_usable:
            self._densities = (None, None)
            return self._densities
        case = self._setup.chamber
        pressure = float(self._setup.feed_pressure)
        provider = property_provider()
        try:
            fuel = stream_density(provider,
                                  PRODUCTION_FLUID_MAPPING.require(case.fuel),
                                  float(case.fuel_temperature), pressure)
            oxidiser = stream_density(
                provider, PRODUCTION_FLUID_MAPPING.require(case.oxidiser),
                float(case.oxidiser_temperature), pressure)
        except Exception:  # noqa: BLE001 - an unusable state is an absent metric
            self._densities = (None, None)
            return self._densities
        self._density_calls += 2
        self._densities = (fuel, oxidiser)
        return self._densities

    # -- building the per-point cases -----------------------------------

    def chamber_case(self, values: Mapping[str, Any]) -> thermo.ChamberCase:
        """The baseline chamber case with this point's chemistry variables."""
        changes: dict[str, Any] = {}
        if "oxidiser_fuel_ratio" in values:
            changes["oxidiser_fuel_ratio"] = float(values["oxidiser_fuel_ratio"])
        if "chamber_pressure" in values:
            changes["chamber_pressure"] = float(values["chamber_pressure"])
        return (self._setup.chamber.replace(**changes) if changes
                else self._setup.chamber)

    def performance_case(self, values: Mapping[str, Any]) -> perf.PerformanceCase:
        """The baseline performance case with this point's nozzle variables."""
        case = self._setup.performance
        changes: dict[str, Any] = {}
        if "area_ratio" in values:
            changes["area_ratio"] = float(values["area_ratio"])
        if "ambient_pressure" in values:
            changes["ambient"] = perf.AmbientCondition(
                perf.AmbientMode.CUSTOM, float(values["ambient_pressure"]))
        if "throat_area" in values:
            from rocketforge.engineering.nozzle import (
                PerformanceScale,
                PerformanceScaleMode,
            )

            changes["scale"] = PerformanceScale(
                PerformanceScaleMode.THROAT_AREA, float(values["throat_area"]))
        return case.replace(**changes) if changes else case

    # -- the stage entry point -------------------------------------------

    def evaluate(self, stage: str, point, upstream) -> StageOutcome:
        if stage == STAGE_THERMOCHEMISTRY:
            return self._chamber(point)
        if stage == STAGE_PERFORMANCE:
            return self._performance(point, upstream)
        raise ValueError(f"unknown evaluation stage {stage!r}")

    def _chamber(self, point) -> StageOutcome:
        self._calls[STAGE_THERMOCHEMISTRY] += 1
        outcome = self._solve_case(self.chamber_case(point.values))
        diagnostics = _tagged(outcome.diagnostics, STAGE_THERMOCHEMISTRY)
        if outcome.state is None:
            return StageOutcome(
                ok=False, diagnostics=diagnostics,
                message=outcome.message or
                        f"the chamber equilibrium did not solve "
                        f"({outcome.status_label})")
        return StageOutcome(
            ok=True, value=outcome, metrics=chamber_metrics(outcome),
            diagnostics=diagnostics,
            warning=outcome.kind == thermo.OUTCOME_WARNING)

    def _performance(self, point, chamber) -> StageOutcome:
        self._calls[STAGE_PERFORMANCE] += 1
        outcome = self._solve_performance(chamber,
                                          self.performance_case(point.values))
        diagnostics = _tagged(outcome.diagnostics, STAGE_PERFORMANCE)
        if outcome.result is None:
            return StageOutcome(
                ok=False, diagnostics=diagnostics,
                message=outcome.message or
                        f"ideal performance is not defined here "
                        f"({outcome.status_label})")
        metrics = performance_metrics(outcome)
        metrics.update(self._density_metrics(point, outcome))
        return StageOutcome(
            ok=True, value=outcome, metrics=metrics,
            diagnostics=diagnostics,
            warning=outcome.kind == perf.OUTCOME_WARNING)

    def _density_metrics(self, point, outcome) -> dict[str, float | None]:
        """Validated densities and density impulse, or nothing at all.

        Nothing, rather than a fallback: a point with no validated density has
        no density impulse, and a study that *requires* it will mark that point
        NOT_EVALUABLE -- which is the honest verdict and is different from
        infeasible.
        """
        fuel, oxidiser = self.stream_densities()
        if fuel is None or oxidiser is None:
            return {}
        result = outcome.result
        if result is None:
            return {}
        from rocketforge.engineering.propellants import (
            density_impulse,
            mixture_bulk_density,
        )

        of = float(self.chamber_case(point.values).oxidiser_fuel_ratio)
        bulk = mixture_bulk_density(of, fuel, oxidiser)
        c_eff = _finite(result.effective_exhaust_velocity)
        isp = _finite(result.specific_impulse)
        metrics: dict[str, float | None] = {
            "fuel_density": fuel.density,
            "oxidiser_density": oxidiser.density,
            "bulk_propellant_density": bulk.density,
            "density_impulse": None,
        }
        if c_eff is not None and isp is not None:
            metrics["density_impulse"] = density_impulse(bulk, c_eff, isp).value
        return metrics


@dataclass(frozen=True, slots=True)
class _TaggedDiagnostic:
    """A diagnostic that remembers which stage raised it."""

    code: str
    severity: str
    message: str
    origin: str
    field: str = ""


def _tagged(diagnostics: Sequence[Any], origin: str) -> tuple[Any, ...]:
    """Attach a stage to each diagnostic, so aggregation can say where.

    A warning that reached a study from the chamber solve and one raised by the
    nozzle model mean different things to a reader, and the study summary is
    the only place the distinction survives.
    """
    return tuple(
        _TaggedDiagnostic(
            code=getattr(d, "code", str(d)),
            severity=str(getattr(d, "severity", "info")),
            message=getattr(d, "message", ""),
            origin=origin,
            field=str(getattr(d, "field", "") or ""))
        for d in diagnostics)


# ---------------------------------------------------------------------------
# metric extraction -- reading, never computing
# ---------------------------------------------------------------------------


def _finite(value: Any) -> float | None:
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def chamber_metrics(outcome: thermo.ChamberOutcome) -> dict[str, float | None]:
    """Chamber-stage metrics, read straight off the solved state.

    Note what is absent: no density, and nothing derived from a propellant's
    ``density_hint``. That field is display-only reference metadata by Phase
    5A/5B contract, and a density impulse computed from it would be a physical
    claim resting on a number never validated as a physical property.
    """
    state = outcome.state
    if state is None:
        return {}
    return {
        "chamber_temperature": _finite(state.temperature),
        "mean_molar_mass": _finite(state.molar_mass),
        "gas_constant": _finite(state.gas_constant),
        "gamma_equilibrium": _finite(state.gamma_equilibrium),
        "gamma_frozen": _finite(state.gamma_frozen),
        "condensed_mass_fraction": _finite(state.condensed_mass_fraction),
    }


def performance_metrics(outcome: perf.PerformanceOutcome) -> dict[str, float | None]:
    """Performance-stage metrics, read off the ``IdealRocketPerformance``.

    Every value comes from the Phase 5E result object. Nothing is recomputed,
    rescaled or rounded here: a trade study reporting a different Isp from the
    Rocket Performance workspace for the same case would mean one of them is
    wrong, and there is only one implementation so that cannot happen.

    Scaled metrics are ``None`` when no engine size was given -- never zero.
    """
    result = outcome.result
    if result is None:
        return {}
    thrust = result.thrust
    return {
        "characteristic_velocity": _finite(result.characteristic_velocity),
        "thrust_coefficient": _finite(result.thrust_coefficient),
        "effective_exhaust_velocity": _finite(result.effective_exhaust_velocity),
        "specific_impulse": _finite(result.specific_impulse),
        "exit_mach": _finite(result.exit.mach),
        "exit_pressure": _finite(result.exit.pressure),
        "exit_temperature": _finite(result.exit.temperature),
        "exit_velocity": _finite(result.exit.velocity),
        "total_thrust": _finite(thrust.total) if thrust else None,
        "momentum_thrust": _finite(thrust.momentum) if thrust else None,
        "pressure_thrust": _finite(thrust.pressure) if thrust else None,
        "mass_flow": _finite(result.mass_flow),
    }


# ---------------------------------------------------------------------------
# running
# ---------------------------------------------------------------------------


def make_runner(definition: StudyDefinition, setup: TradeStudySetup, *,
                registry: MetricRegistry | None = None,
                evaluator: Any = None) -> StudyRunner:
    """A runner for this study, validated first.

    Validation happens here rather than inside the runner so that a refusal
    arrives before any chemistry does.
    """
    registry = registry or metric_registry()
    validate_definition(definition, registry,
                        scale_available=setup.scale_available)
    return StudyRunner(definition, registry,
                       evaluator or RocketForgeEvaluator(setup),
                       scale_available=setup.scale_available)


def run_trade_study(definition: StudyDefinition, setup: TradeStudySetup, *,
                    registry: MetricRegistry | None = None,
                    evaluator: Any = None,
                    on_progress=None, should_cancel=None) -> StudyResult:
    """Run one study to completion. The headless entry point."""
    runner = make_runner(definition, setup, registry=registry,
                         evaluator=evaluator)
    result = runner.run(on_progress=on_progress, should_cancel=should_cancel)
    return _with_provenance(result, definition, setup)


def reanalyse(result: StudyResult, definition: StudyDefinition) -> StudyResult:
    """Re-run the decision layer on existing raw results.

    Calls no provider and no performance service. Changing an objective, a
    constraint or a weight goes through here, and the raw metrics are carried
    across by reference so nothing can drift.
    """
    if not result.complete:
        return result
    updated = analyse(result, definition)
    return StudyResult(
        definition=definition,
        points=updated.points,
        status=updated.status,
        counts=updated.counts,
        provenance=result.provenance,
        diagnostics=updated.diagnostics,
        pareto_indices=updated.pareto_indices,
        ranking=updated.ranking,
        scored=updated.scored,
        message=updated.message)


def _with_provenance(result: StudyResult, definition: StudyDefinition,
                     setup: TradeStudySetup) -> StudyResult:
    return StudyResult(
        definition=result.definition,
        points=result.points,
        status=result.status,
        counts=result.counts,
        provenance=study_provenance(definition, setup, result),
        diagnostics=result.diagnostics,
        pareto_indices=result.pareto_indices,
        ranking=result.ranking,
        scored=result.scored,
        message=result.message)


def study_provenance(definition: StudyDefinition, setup: TradeStudySetup,
                     result: StudyResult | None = None) -> dict[str, Any]:
    """Who computed this study, with what, under which assumptions.

    Shared across every point rather than copied onto each: ten thousand
    identical database digests are one fact, and storing it once keeps a large
    result small without losing a word of traceability.
    """
    from .thermochemistry_provider import availability

    status = availability()
    provider: dict[str, Any] = {
        "label": thermo.PROVIDER_LABEL,
        "available": bool(status.usable),
        "version": status.version or "",
        "library_version": status.library_version or "",
        "chemistry": thermo.MODEL_SUMMARY,
    }
    return {
        "provider": provider,
        "performance_model": {
            "owner": "RocketForge",
            "model": "ideal rocket, constant-property perfect gas, isentropic "
                     "shock-free expansion, no efficiency factor of any kind",
            "gamma_strategy": setup.performance.gamma_strategy.value,
            "gamma_basis": setup.performance.gamma_basis.value,
        },
        "baseline": setup.canonical(),
        "definition_fingerprint": definition.fingerprint,
        "stage_order": list(definition.stage_order),
        "variables": [variable.canonical() for variable in definition.variables],
        "objectives": [objective.canonical()
                       for objective in definition.objectives],
        "constraints": [constraint.canonical()
                        for constraint in definition.constraints],
        "scoring": (definition.scoring.canonical()
                    if definition.scoring else None),
        "oracle_used": False,
        "oracle_note": "A trade study's physics is the provider for the chamber "
                       "and RocketForge for the nozzle. The provider's own c*, "
                       "Cf and Isp are a Phase 5E validation tool and are not "
                       "evaluated per study point.",
    }
