"""Thrust-chamber and nozzle sizing (LIQ-4): resolve, size, present. Qt-free.

The input is the candidate selected in a LIQ-3 propellant trade, read as LIQ-3
resolved it. The chain is the production chain, called, not copied::

    selected LIQ-3 candidate  --(exact ChamberCase)-->  thermochemistry_service.solve_case
        consistency check       Tc, molar mass and c* must equal the LIQ-3 record
        performance_service.solve_performance   ideal nozzle at the stated Ae/At and
                                                the design ambient -> c_eff
        mdot = F / c_eff
        performance_service.solve_performance   the same, scaled to that mdot ->
                                                At = mdot c*/pc, Ae, thrust breakdown
        Dt, De                                  circular sections

**Why the chamber is solved again.** A LIQ-3 record holds numbers, not the
chamber state the ideal nozzle needs (gamma, R, T0). Sizing replays the exact
case LIQ-3 solved -- same reactant keys, O/F, chamber pressure and stream
temperatures -- and then requires the replay to reproduce LIQ-3's recorded
chamber temperature, molar mass and c* bit for bit. A difference means the
chain is no longer the one that produced the trade, and the sizing is refused
rather than mixing the two.

**Nothing is resolved silently.** :func:`operating_point` refuses a missing,
stale or unselected trade. :func:`build_definition` refuses a sizing without a
stated area ratio: the trade's when it had one, or one the user states. No
optimum expansion is assumed.

Feed architecture and cycle are not read: the ideal chamber and nozzle design
point is the same whatever the cycle, and no cycle, injector, feed, cooling or
chamber-geometry model exists in this build.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from rocketforge.engine.chamber_sizing import (
    SIZING_QUANTITIES,
    AreaRatioSource,
    OperatingPoint,
    SizingDefinition,
    SizingResult,
    SizingStatus,
)
from rocketforge.engine.propellant_trade import TradeResult

__all__ = [
    "DISPLAY",
    "GROUPS",
    "SizingIssue",
    "SizingSettings",
    "build_definition",
    "display_value",
    "operating_point",
    "provenance",
    "quantity_groups",
    "solve_sizing",
]

#: The checks the replayed chamber must pass: LIQ-3 metric key, ChamberGas
#: attribute, label.
_REPRODUCED = (("chamber_temperature", "temperature", "chamber temperature"),
               ("molar_mass", "molar_mass", "molar mass"))


@dataclass(frozen=True, slots=True)
class SizingSettings:
    """What the user states for the sizing. ``area_ratio`` None: use the trade's."""

    area_ratio: float | None = None


@dataclass(frozen=True, slots=True)
class SizingIssue:
    code: str
    field: str
    message: str


def operating_point(result: TradeResult | None, stale: bool
                    ) -> tuple[OperatingPoint | None, tuple[SizingIssue, ...]]:
    """The selected LIQ-3 candidate as an operating point, or why there is none."""
    if result is None:
        return None, (SizingIssue("NO_TRADE", "trade",
                                  "No propellant trade has been run. Run one on the "
                                  "Propellant Trade page and select a candidate."),)
    if stale:
        return None, (SizingIssue("TRADE_STALE", "trade",
                                  "The propellant trade is stale: the requirement or its "
                                  "settings changed since it ran. Run it again."),)
    if not result.selected:
        return None, (SizingIssue("NO_SELECTION", "trade",
                                  "No candidate is selected in the propellant trade. "
                                  "Nothing is chosen for you."),)
    candidate = result.candidate(result.selected)
    if candidate is None or not candidate.ok:
        return None, (SizingIssue("SELECTION_FAILED", "trade",
                                  "The selected candidate did not solve in the trade."),)
    if candidate.oxidiser_temperature is None or candidate.fuel_temperature is None:
        return None, (SizingIssue("SELECTION_INCOMPLETE", "trade",
                                  "The selected candidate carries no stream temperatures."),)
    d = result.definition
    requirement = d.requirement
    return OperatingPoint(
        trade_fingerprint=d.fingerprint,
        trade_provenance=dict(result.provenance),
        requirement_fingerprint=requirement.fingerprint,
        pair_key=candidate.key, pair_label=candidate.label,
        oxidiser=candidate.oxidiser, fuel=candidate.fuel,
        oxidiser_fuel_ratio=candidate.oxidiser_fuel_ratio,
        mixture_ratio_source=d.mixture_ratio_source.value,
        chamber_pressure=candidate.chamber_pressure,
        pressure_source=d.pressure_source.value,
        oxidiser_temperature=candidate.oxidiser_temperature,
        fuel_temperature=candidate.fuel_temperature,
        gamma_basis=d.gamma_basis,
        ambient_pressure=requirement.environment.ambient_pressure,
        thrust=float(requirement.thrust),
        trade_area_ratio=d.area_ratio,
        recorded=dict(candidate.metrics),
    ), ()


def build_definition(point: OperatingPoint | None, settings: SizingSettings
                     ) -> tuple[SizingDefinition | None, tuple[SizingIssue, ...]]:
    """The resolved sizing, or ``None`` and every reason it cannot be built."""
    if point is None:
        return None, ()
    stated = settings.area_ratio
    if stated is not None:
        if not (math.isfinite(stated) and stated > 1.0):
            return None, (SizingIssue("AREA_RATIO_INVALID", "area_ratio",
                                      "The stated area ratio must be finite and above 1."),)
        return SizingDefinition(point, float(stated), AreaRatioSource.SIZING), ()
    if point.trade_area_ratio is not None:
        return SizingDefinition(point, point.trade_area_ratio, AreaRatioSource.TRADE), ()
    return None, (SizingIssue(
        "AREA_RATIO_UNRESOLVED", "area_ratio",
        "The trade was chamber-only, so no nozzle is defined. State the expansion "
        "ratio Ae/At to size at. No optimum expansion is assumed."),)


# ---------------------------------------------------------------------------
# sizing
# ---------------------------------------------------------------------------


def _refused(definition: SizingDefinition, message: str, notes=(), regime: str = ""
             ) -> SizingResult:
    return SizingResult(
        definition=definition, status=SizingStatus.REFUSED,
        unresolved={q.key: message for q in SIZING_QUANTITIES},
        regime=regime, message=message, notes=tuple(dict.fromkeys(notes)),
        provenance=provenance(definition))


def _messages(diagnostics, severities=("warning", "info")) -> list[str]:
    return [str(d.message) for d in diagnostics
            if str(getattr(d, "severity", "")) in severities]


def _diameter(area: float) -> float:
    return math.sqrt(4.0 * area / math.pi)


def solve_sizing(definition: SizingDefinition) -> SizingResult:
    """Size the ideal thrust chamber and nozzle. Never raises.

    The only function here that reaches a provider (one chamber solve). Every
    refusal of the chain comes back as a REFUSED result carrying its reason.
    """
    from rocketforge.engineering.chamber import ChamberGammaBasis
    from rocketforge.engineering.nozzle import (
        IDEAL_MODEL_ASSUMPTIONS,
        PerformanceScale,
        PerformanceScaleMode,
    )
    from rocketforge.physics.thermochemistry import GammaStrategy

    from . import performance_service as performance
    from .thermochemistry_service import ChamberCase, solve_case

    point = definition.point
    chamber = solve_case(ChamberCase(
        fuel=point.fuel, oxidiser=point.oxidiser,
        oxidiser_fuel_ratio=point.oxidiser_fuel_ratio,
        chamber_pressure=point.chamber_pressure,
        fuel_temperature=point.fuel_temperature,
        oxidiser_temperature=point.oxidiser_temperature))
    if chamber.state is None:
        return _refused(definition, f"Chamber equilibrium: {chamber.status_label}. "
                                    f"{chamber.message}".strip())
    notes = _messages(chamber.diagnostics, ("warning",))
    state = chamber.state
    for key, attribute, label in _REPRODUCED:
        recorded, replayed = point.recorded.get(key), float(getattr(state, attribute))
        if recorded is not None and replayed != recorded:
            return _refused(definition, (
                f"The chamber solve does not reproduce the propellant trade: {label} "
                f"{replayed!r} here, {recorded!r} in the trade. The chain has changed "
                "since the trade ran; run the trade again."), notes)

    def solve(scale: PerformanceScale):
        return performance.solve_performance(chamber, performance.PerformanceCase(
            gamma_strategy=GammaStrategy.CHAMBER,
            gamma_basis=ChamberGammaBasis(point.gamma_basis),
            area_ratio=definition.area_ratio,
            ambient=performance.AmbientCondition(performance.AmbientMode.CUSTOM,
                                                 point.ambient_pressure),
            scale=scale))

    unit = solve(PerformanceScale())
    if unit.result is None:
        return _refused(definition, f"Ideal performance refused: {unit.message}",
                        notes + _messages(unit.diagnostics))
    recorded_c_star = point.recorded.get("characteristic_velocity")
    if (recorded_c_star is not None
            and unit.result.characteristic_velocity != recorded_c_star):
        return _refused(definition, (
            f"The chamber solve does not reproduce the propellant trade: c* "
            f"{unit.result.characteristic_velocity!r} here, {recorded_c_star!r} in the "
            "trade. Run the trade again."), notes, unit.result.exit.regime)
    c_eff = unit.result.effective_exhaust_velocity
    if not c_eff > 0.0:
        return _refused(definition, (
            "c_eff is not positive at the design ambient pressure: this nozzle gives no "
            "net thrust there, so no mass flow can meet the target thrust."),
            notes + _messages(unit.diagnostics), unit.result.exit.regime)

    mass_flow = point.thrust / c_eff
    sized = solve(PerformanceScale(PerformanceScaleMode.MASS_FLOW, mass_flow))
    if sized.result is None:                     # same algebra as above; kept explicit
        return _refused(definition, f"Ideal performance refused: {sized.message}",
                        notes + _messages(sized.diagnostics))
    r = sized.result
    if definition.area_ratio_source is AreaRatioSource.TRADE:
        # Sized at the trade's own nozzle: the trade's performance and flow
        # figures are the same numbers, and must be.
        for key, value in (("thrust_coefficient", r.thrust_coefficient),
                           ("effective_exhaust_velocity", r.effective_exhaust_velocity),
                           ("specific_impulse", r.specific_impulse),
                           ("mass_flow", r.mass_flow)):
            recorded = point.recorded.get(key)
            if recorded is not None and float(value) != recorded:
                return _refused(definition, (
                    f"The sizing does not reproduce the propellant trade: {key} "
                    f"{float(value)!r} here, {recorded!r} in the trade. Run the trade "
                    "again."), notes, r.exit.regime)
    ratio = point.oxidiser_fuel_ratio
    quantities: dict[str, float] = {
        "mass_flow": float(r.mass_flow),
        "oxidiser_mass_flow": float(r.mass_flow) * ratio / (1.0 + ratio),
        "fuel_mass_flow": float(r.mass_flow) / (1.0 + ratio),
        "throat_area": float(r.throat_area),
        "throat_diameter": _diameter(float(r.throat_area)),
        "exit_area": float(r.exit_area),
        "exit_diameter": _diameter(float(r.exit_area)),
        "area_ratio": float(r.exit.area_ratio),
        "characteristic_velocity": float(r.characteristic_velocity),
        "thrust_coefficient": float(r.thrust_coefficient),
        "thrust_coefficient_momentum": float(r.thrust_coefficient_momentum),
        "thrust_coefficient_pressure": float(r.thrust_coefficient_pressure),
        "effective_exhaust_velocity": float(r.effective_exhaust_velocity),
        "specific_impulse": float(r.specific_impulse),
        "exit_mach": float(r.exit.mach),
        "exit_pressure": float(r.exit.pressure),
        "exit_pressure_ratio": float(r.exit.pressure_ratio),
        "exit_temperature": float(r.exit.temperature),
        "exit_velocity": float(r.exit.velocity),
        "momentum_thrust": float(r.thrust.momentum),
        "pressure_thrust": float(r.thrust.pressure),
        "thrust": float(r.thrust.total),
        "thrust_closure": float(r.thrust.total) / point.thrust - 1.0,
    }
    notes += _messages(sized.diagnostics)
    return SizingResult(
        definition=definition,
        status=SizingStatus.WARNING if sized.has_warnings else SizingStatus.OK,
        quantities=quantities, regime=str(r.exit.regime),
        notes=tuple(dict.fromkeys(notes)),
        assumptions=tuple(IDEAL_MODEL_ASSUMPTIONS) + (
            "Circular throat and exit sections.",
            "Steady operation at the target thrust and design ambient; no throttling, "
            "start or shutdown.",
            f"Single gamma at the chamber, {point.gamma_basis} basis, as in the trade.",
        ),
        provenance=provenance(definition))


def provenance(definition: SizingDefinition) -> dict[str, str]:
    """Which chain produced the numbers, and the trade they came from."""
    from .thermochemistry_provider import PROVIDER_LABEL, availability

    point = definition.point
    return {
        "chamber": f"{PROVIDER_LABEL} {availability().library_version}".strip(),
        "chamber_model": "HP equilibrium, the trade's exact case replayed and checked",
        "performance": "RocketForge ideal rocket model (single gamma, chamber strategy)",
        "sizing": "mdot = F / c_eff; At = mdot c* / pc; circular sections",
        "trade": f"LIQ-3 trade {point.trade_fingerprint[:12]}, candidate {point.pair_key}",
        "trade_chamber": point.trade_provenance.get("chamber", ""),
    }


# ---------------------------------------------------------------------------
# presentation
# ---------------------------------------------------------------------------

#: Display unit, scale and decimals per quantity. Conversion happens here only.
DISPLAY: dict[str, tuple[str, float, str]] = {
    "mass_flow": ("kg/s", 1.0, ",.3f"),
    "oxidiser_mass_flow": ("kg/s", 1.0, ",.3f"),
    "fuel_mass_flow": ("kg/s", 1.0, ",.3f"),
    "throat_area": ("cm²", 1.0e4, ",.3f"),
    "throat_diameter": ("mm", 1.0e3, ",.2f"),
    "exit_area": ("cm²", 1.0e4, ",.2f"),
    "exit_diameter": ("mm", 1.0e3, ",.1f"),
    "area_ratio": ("", 1.0, ".6g"),
    "characteristic_velocity": ("m/s", 1.0, ",.1f"),
    "thrust_coefficient": ("", 1.0, ".5f"),
    "thrust_coefficient_momentum": ("", 1.0, ".5f"),
    "thrust_coefficient_pressure": ("", 1.0, "+.5f"),
    "effective_exhaust_velocity": ("m/s", 1.0, ",.1f"),
    "specific_impulse": ("s", 1.0, ",.2f"),
    "exit_mach": ("", 1.0, ".4f"),
    "exit_pressure": ("kPa", 1.0e-3, ",.3f"),
    "exit_pressure_ratio": ("", 1.0, ".5g"),
    "exit_temperature": ("K", 1.0, ",.1f"),
    "exit_velocity": ("m/s", 1.0, ",.1f"),
    "momentum_thrust": ("kN", 1.0e-3, ",.4f"),
    "pressure_thrust": ("kN", 1.0e-3, "+,.4f"),
    "thrust": ("kN", 1.0e-3, ",.4f"),
    "thrust_closure": ("", 1.0, ".1e"),
}

GROUPS: tuple[tuple[str, str], ...] = (
    ("flow", "Propellant flow"),
    ("geometry", "Throat and exit"),
    ("performance", "Performance at the design ambient"),
    ("exit", "Exit state"),
    ("thrust", "Thrust closure"),
)


def display_value(key: str, value: float | None) -> str:
    if value is None:
        return "—"
    _unit, scale, spec = DISPLAY[key]
    return format(value * scale, spec)


def quantity_groups(result: SizingResult) -> list[dict[str, Any]]:
    """Every quantity, grouped for display, with its unit, note and reason."""
    groups = []
    for key, title in GROUPS:
        rows = [{"key": q.key, "label": q.label, "unit": DISPLAY[q.key][0],
                 "note": q.note, "value": display_value(q.key, result.value(q.key)),
                 "reason": result.unresolved.get(q.key, "")}
                for q in SIZING_QUANTITIES if q.group == key]
        groups.append({"key": key, "title": title, "rows": rows})
    return groups
