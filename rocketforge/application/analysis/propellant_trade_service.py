"""Liquid propellant trade (LIQ-3): resolve, evaluate, present. Qt-free.

The chain for one candidate is the production chain, called, not copied::

    LIQ-1 preset  --(reactant keys, reference temperatures)-->  ChamberCase
        thermochemistry_service.solve_case         NASA CEA, HP equilibrium
        reduce_chamber_gas + characteristic_velocity   c*, at the stated gamma basis
        performance_service.solve_performance      ideal nozzle, only if one is stated
        mdot = F / c_eff, split by O/F, x burn time    only with a valid c_eff

**Nothing is resolved silently.** :func:`build_definition` turns a LIQ-2
requirement plus the user's study settings into a :class:`TradeDefinition`, or
into the list of what is still missing. An Auto chamber pressure or an upper
limit needs a study chamber pressure stated by the user; an Auto O/F needs the
user to choose either each candidate's catalogue O/F or one stated O/F; the
ideal-performance quantities need a stated area ratio. Until then the trade
does not run, and the reason is shown.

Feed architecture and cycle are carried in the requirement snapshot as intent.
Nothing here reads them: no cycle loss, feasibility or power balance exists in
this build, and the ideal chamber + nozzle figures are the same whatever the
cycle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from rocketforge.engine.propellant_trade import (
    TRADE_METRICS,
    CandidateResult,
    CandidateStatus,
    MixtureRatioSource,
    PerformanceBasis,
    PressureSource,
    TradeDefinition,
    TradeResult,
    metric_named,
)
from rocketforge.engine.requirement import (
    ChamberPressureMode,
    EngineRequirement,
    MixtureRatioMode,
)

from . import engine_requirement_service as requirement_service
from . import environment_service
from . import thermochemistry_presets as presets

__all__ = [
    "DISPLAY",
    "TradeIssue",
    "TradeSettings",
    "assemble_result",
    "build_definition",
    "candidate_keys",
    "evaluate_candidate",
    "operating_needs",
    "provenance",
    "table_rows",
]

#: Gamma bases offered, the same two the Rocket Performance workspace offers.
GAMMA_BASES = ("frozen", "equilibrium")


@dataclass(frozen=True, slots=True)
class TradeSettings:
    """What the user states for this study, beyond the requirement.

    Every value starts unset. A value is read only where the requirement
    leaves that decision open; it never overrides a stated requirement value.
    """

    chamber_pressure: float | None = None          # Pa
    mixture_ratio_mode: str = ""                   # "" | "catalogue" | "explicit"
    mixture_ratio: float | None = None
    performance_basis: PerformanceBasis = PerformanceBasis.CHAMBER_ONLY
    area_ratio: float | None = None
    gamma_basis: str = "frozen"

    def replace(self, **changes: Any) -> "TradeSettings":
        from dataclasses import replace as _replace

        return _replace(self, **changes)


@dataclass(frozen=True, slots=True)
class TradeIssue:
    code: str
    field: str
    message: str


def operating_needs(requirement: EngineRequirement) -> dict[str, bool]:
    """Which study inputs this requirement leaves to the user."""
    return {
        "chamber_pressure": requirement.chamber_pressure.mode is not ChamberPressureMode.TARGET,
        "mixture_ratio": requirement.mixture_ratio.mode is MixtureRatioMode.AUTO,
    }


def candidate_keys(requirement: EngineRequirement) -> tuple[str, ...]:
    """The preset keys a trade evaluates: the chosen pair, or every executable one.

    Blocked catalogue pairs are never candidates and nothing is substituted
    for them.
    """
    if requirement.propellant.is_explicit:
        preset = presets.preset_named(requirement.propellant.pair_key)
        return (preset.key,) if preset is not None and preset.executable else ()
    return tuple(preset.key for preset in presets.executable_presets())


def _positive(value: float | None) -> bool:
    return value is not None and math.isfinite(value) and value > 0.0


def build_definition(requirement: EngineRequirement, settings: TradeSettings
                     ) -> tuple[TradeDefinition | None, tuple[TradeIssue, ...]]:
    """The resolved definition, or ``None`` and every reason it cannot be built."""
    issues: list[TradeIssue] = []

    def add(code: str, field: str, message: str) -> None:
        issues.append(TradeIssue(code, field, message))

    for issue in requirement_service.requirement_issues(requirement):
        add("REQUIREMENT_INCOMPLETE", issue.field,
            f"Engine Requirement: {issue.message}")

    candidates = candidate_keys(requirement)
    if not candidates and not issues:
        add("NO_CANDIDATES", "propellant", "No executable propellant pair to evaluate.")

    ambient = environment_service.ambient_pressure(requirement.environment)
    chamber = requirement.chamber_pressure
    pressure: float | None = None
    pressure_source = PressureSource.REQUIREMENT
    if chamber.mode is ChamberPressureMode.TARGET:
        pressure = chamber.value
    else:
        pressure_source = PressureSource.STUDY
        stated = settings.chamber_pressure
        if stated is None:
            word = ("is Auto" if chamber.mode is ChamberPressureMode.AUTO
                    else "is an upper limit, not an operating point")
            add("CHAMBER_PRESSURE_UNRESOLVED", "chamber_pressure",
                f"The requirement's chamber pressure {word}. State the chamber "
                "pressure this study compares at.")
        elif not _positive(stated):
            add("CHAMBER_PRESSURE_INVALID", "chamber_pressure",
                "The study chamber pressure must be finite and above zero.")
        elif stated <= ambient:
            add("CHAMBER_PRESSURE_NOT_ABOVE_AMBIENT", "chamber_pressure",
                "The study chamber pressure is not above the design ambient pressure.")
        elif (chamber.mode is ChamberPressureMode.UPPER_LIMIT and chamber.value is not None
              and stated > chamber.value):
            add("CHAMBER_PRESSURE_ABOVE_LIMIT", "chamber_pressure",
                "The study chamber pressure exceeds the requirement's upper limit.")
        else:
            pressure = stated

    ratio = requirement.mixture_ratio
    ratio_value: float | None = None
    if ratio.mode is MixtureRatioMode.EXPLICIT:
        ratio_source = MixtureRatioSource.REQUIREMENT
        ratio_value = ratio.value
    elif ratio.mode is MixtureRatioMode.PAIR_REFERENCE:
        ratio_source = MixtureRatioSource.CATALOGUE
    elif settings.mixture_ratio_mode == "catalogue":
        ratio_source = MixtureRatioSource.CATALOGUE
    elif settings.mixture_ratio_mode == "explicit":
        ratio_source = MixtureRatioSource.STUDY
        ratio_value = settings.mixture_ratio
        if not _positive(ratio_value):
            add("MIXTURE_RATIO_INVALID", "mixture_ratio",
                "State the O/F this study uses for every candidate, above zero.")
    else:
        ratio_source = MixtureRatioSource.STUDY
        add("MIXTURE_RATIO_UNRESOLVED", "mixture_ratio",
            "The requirement's O/F is Auto. Choose each candidate's catalogue O/F "
            "or state one O/F for the study. No O/F is optimised.")

    area_ratio: float | None = None
    if settings.performance_basis is PerformanceBasis.IDEAL_AREA_RATIO:
        area_ratio = settings.area_ratio
        if not (area_ratio is not None and math.isfinite(area_ratio) and area_ratio > 1.0):
            add("AREA_RATIO_UNRESOLVED", "area_ratio",
                "An ideal performance comparison needs a stated area ratio above 1.")
    if settings.gamma_basis not in GAMMA_BASES:
        add("GAMMA_BASIS_INVALID", "gamma_basis", "Choose the frozen or equilibrium gamma basis.")

    if issues:
        return None, tuple(issues)
    return TradeDefinition(
        requirement=requirement, candidates=candidates,
        chamber_pressure=float(pressure), pressure_source=pressure_source,
        mixture_ratio_source=ratio_source, mixture_ratio=ratio_value,
        performance_basis=settings.performance_basis, area_ratio=area_ratio,
        gamma_basis=settings.gamma_basis), ()


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------

_NO_NOZZLE = ("No performance basis stated: choose an ideal area ratio to compare "
              "nozzle quantities. None is assumed.")


def _failed(definition: TradeDefinition, key: str, label: str, ox: str, fuel: str,
            ratio: float, temps: tuple[float | None, float | None], message: str
            ) -> CandidateResult:
    return CandidateResult(
        key=key, label=label, oxidiser=ox, fuel=fuel, oxidiser_fuel_ratio=ratio,
        chamber_pressure=definition.chamber_pressure,
        oxidiser_temperature=temps[0], fuel_temperature=temps[1],
        status=CandidateStatus.FAILED,
        unresolved={metric.key: message for metric in TRADE_METRICS},
        message=message)


def evaluate_candidate(definition: TradeDefinition, key: str) -> CandidateResult:
    """Evaluate one candidate through the production chain. Never raises.

    A failure is returned as a FAILED row carrying its operating point and the
    reason; it touches nothing else.
    """
    from rocketforge.engineering.chamber import ChamberGammaBasis, reduce_chamber_gas
    from rocketforge.engineering.nozzle import characteristic_velocity
    from rocketforge.physics.thermochemistry import GammaStrategy

    from . import performance_service as performance
    from .thermochemistry_provider import propellant_named
    from .thermochemistry_service import ChamberCase, solve_case

    preset = presets.preset_named(key)
    if preset is None or not preset.executable:
        return _failed(definition, key, key, "", "", definition.mixture_ratio or 0.0,
                       (None, None), "Not an executable catalogue pair.")
    ratio = (preset.oxidiser_fuel_ratio if definition.mixture_ratio is None
             else definition.mixture_ratio)
    oxidiser, fuel = propellant_named(preset.oxidiser), propellant_named(preset.fuel)
    temps = (oxidiser.reference_temperature if oxidiser else None,
             fuel.reference_temperature if fuel else None)
    if oxidiser is None or fuel is None:
        return _failed(definition, key, preset.label, preset.oxidiser, preset.fuel,
                       ratio, temps, "A reactant of this pair is not available in "
                                     "this build's propellant catalogue.")

    case = ChamberCase(fuel=fuel.key, oxidiser=oxidiser.key,
                       oxidiser_fuel_ratio=float(ratio),
                       chamber_pressure=definition.chamber_pressure,
                       fuel_temperature=fuel.reference_temperature,
                       oxidiser_temperature=oxidiser.reference_temperature)
    chamber = solve_case(case)
    if chamber.state is None:
        return _failed(definition, key, preset.label, preset.oxidiser, preset.fuel,
                       ratio, temps, f"Chamber equilibrium: {chamber.status_label}. "
                                     f"{chamber.message}".strip())

    notes: list[str] = [str(d.message) for d in chamber.diagnostics
                        if str(getattr(d, "severity", "")) == "warning"]
    state = chamber.state
    metrics: dict[str, float] = {
        "chamber_temperature": float(state.temperature),
        "molar_mass": float(state.molar_mass),
    }
    unresolved: dict[str, str] = {}
    for name, attr in (("gamma_frozen", "gamma_frozen"),
                       ("gamma_equilibrium", "gamma_equilibrium")):
        value = getattr(state, attr, None)
        if value is None:
            unresolved[name] = "Not reported by the provider for this state."
        else:
            metrics[name] = float(value)

    basis = ChamberGammaBasis(definition.gamma_basis)
    warned = chamber.has_warnings
    performance_reason = _NO_NOZZLE
    result = None
    if definition.performance_basis is PerformanceBasis.IDEAL_AREA_RATIO:
        outcome = performance.solve_performance(chamber, performance.PerformanceCase(
            gamma_strategy=GammaStrategy.CHAMBER, gamma_basis=basis,
            area_ratio=float(definition.area_ratio),
            ambient=performance.AmbientCondition(
                performance.AmbientMode.CUSTOM,
                environment_service.ambient_pressure(definition.requirement.environment))))
        result = outcome.result
        notes += [str(d.message) for d in outcome.diagnostics
                  if str(getattr(d, "severity", "")) == "warning"]
        if result is None:
            performance_reason = f"Ideal performance refused: {outcome.message}"
            warned = True
        warned = warned or outcome.has_warnings

    if result is not None:
        metrics["characteristic_velocity"] = float(result.characteristic_velocity)
        metrics["thrust_coefficient"] = float(result.thrust_coefficient)
        metrics["effective_exhaust_velocity"] = float(result.effective_exhaust_velocity)
        metrics["specific_impulse"] = float(result.specific_impulse)
        metrics["exit_pressure"] = float(result.exit.pressure)
    else:
        reduction = reduce_chamber_gas(state, GammaStrategy.CHAMBER, basis,
                                       chamber_pressure=definition.chamber_pressure)
        if reduction.value is None:
            first = reduction.diagnostics[0].message if reduction.diagnostics else ""
            unresolved["characteristic_velocity"] = (
                f"Single-gamma reduction refused: {first}".strip())
            warned = True
        else:
            metrics["characteristic_velocity"] = float(characteristic_velocity(
                reduction.value.gas, reduction.value.stagnation_temperature))
        for metric in TRADE_METRICS:
            if metric.tier == "performance":
                unresolved[metric.key] = performance_reason

    flow_reason = performance_reason
    c_eff = metrics.get("effective_exhaust_velocity")
    if c_eff is not None and not c_eff > 0.0:
        flow_reason = ("c_eff is not positive at the design ambient pressure: the "
                       "stated nozzle gives no net thrust there.")
        c_eff = None
    requirement = definition.requirement
    if c_eff is not None:
        mass_flow = requirement.thrust / c_eff
        metrics["mass_flow"] = mass_flow
        metrics["oxidiser_mass_flow"] = mass_flow * ratio / (1.0 + ratio)
        metrics["fuel_mass_flow"] = mass_flow / (1.0 + ratio)
        metrics["propellant_mass"] = mass_flow * requirement.burn_time
    else:
        for metric in TRADE_METRICS:
            if metric.tier == "flow":
                unresolved[metric.key] = flow_reason

    return CandidateResult(
        key=key, label=preset.label, oxidiser=preset.oxidiser, fuel=preset.fuel,
        oxidiser_fuel_ratio=float(ratio), chamber_pressure=definition.chamber_pressure,
        oxidiser_temperature=temps[0], fuel_temperature=temps[1],
        status=CandidateStatus.WARNING if warned else CandidateStatus.OK,
        metrics=metrics, unresolved=unresolved,
        notes=tuple(dict.fromkeys(notes)))


def provenance() -> dict[str, str]:
    """Which chain produced the numbers. Read only after a run has used it."""
    from .thermochemistry_provider import PROVIDER_LABEL, availability

    state = availability()
    return {
        "chamber": f"{PROVIDER_LABEL} {state.library_version}".strip(),
        "chamber_model": "HP equilibrium, reactants at their reference temperatures",
        "performance": "RocketForge ideal rocket model (single gamma, chamber strategy)",
        "catalogue": presets.SUTTON_SOURCE,
    }


def assemble_result(definition: TradeDefinition,
                    candidates: tuple[CandidateResult, ...]) -> TradeResult:
    return TradeResult(definition=definition, candidates=candidates,
                       provenance=provenance())


# ---------------------------------------------------------------------------
# presentation
# ---------------------------------------------------------------------------

#: Display unit and scale per metric. Conversion happens here and nowhere else.
DISPLAY: dict[str, tuple[str, float, int]] = {
    "chamber_temperature": ("K", 1.0, 0),
    "molar_mass": ("g/mol", 1.0e3, 2),
    "gamma_frozen": ("", 1.0, 4),
    "gamma_equilibrium": ("", 1.0, 4),
    "characteristic_velocity": ("m/s", 1.0, 0),
    "thrust_coefficient": ("", 1.0, 4),
    "effective_exhaust_velocity": ("m/s", 1.0, 0),
    "specific_impulse": ("s", 1.0, 1),
    "exit_pressure": ("kPa", 1.0e-3, 2),
    "mass_flow": ("kg/s", 1.0, 2),
    "oxidiser_mass_flow": ("kg/s", 1.0, 2),
    "fuel_mass_flow": ("kg/s", 1.0, 2),
    "propellant_mass": ("kg", 1.0, 0),
}


def display_value(key: str, value: float | None) -> str:
    if value is None:
        return "—"
    unit, scale, decimals = DISPLAY[key]
    return f"{value * scale:,.{decimals}f}"


def table_rows(result: TradeResult, sort_key: str = "", descending: bool = True
               ) -> list[dict[str, Any]]:
    """One row per candidate, ordered by one displayed metric or catalogue order.

    Ordering is a view of the numbers shown, never a verdict: rows without
    that metric (failed or unresolved) follow in catalogue order, and ties
    keep catalogue order.
    """
    order = list(range(len(result.candidates)))
    if sort_key and metric_named(sort_key) is not None:
        valued = [i for i in order if result.candidates[i].value(sort_key) is not None]
        missing = [i for i in order if i not in valued]
        valued.sort(key=lambda i: result.candidates[i].value(sort_key),
                    reverse=descending)
        order = valued + missing
    rows = []
    for rank, index in enumerate(order):
        candidate = result.candidates[index]
        rows.append({
            "key": candidate.key, "label": candidate.label,
            "status": candidate.status.value, "ok": candidate.ok,
            "selected": candidate.key == result.selected,
            "ratio": f"{candidate.oxidiser_fuel_ratio:g}",
            "message": candidate.message,
            "notes": list(candidate.notes),
            "values": {metric.key: display_value(metric.key, candidate.value(metric.key))
                       for metric in TRADE_METRICS},
            "unresolved": dict(candidate.unresolved),
            "position": rank,
        })
    return rows
