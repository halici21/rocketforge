"""Ideal rocket performance, prepared for display. Qt-free.

The chain, and the one thing it must never do::

    ChamberOutcome (Phase 5D, already solved)
        |
        +--> reduce_chamber_gas       an explicit gamma strategy and basis
        |
        +--> solve_ideal_performance  RocketForge's own equations
        |
        v
    PerformanceOutcome                an immutable display snapshot

**No chemistry is re-solved here.** The chamber state arrives already computed.
Changing an area ratio, an ambient pressure or an engine size re-runs algebra
that costs microseconds and touches no provider, and a spy test asserts zero
additional chamber solves for each of those three. That is not an optimisation:
a chemistry re-solve on every input change would let the two workspaces
silently disagree about which chamber a number came from.

The other thing this module owns is the **dual provenance**. RocketForge
computed the performance; a provider computed the chamber state it started
from. Those are two different claims, and merging them into a single
"Provider: NASA CEA" line would attribute RocketForge's equations to a library
that did not run them.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from rocketforge.engineering.chamber import ChamberGammaBasis, reduce_chamber_gas
from rocketforge.engineering.nozzle import (
    IDEAL_MODEL_ASSUMPTIONS,
    IdealPerformanceRequest,
    IdealRocketPerformance,
    PerformanceScale,
    PerformanceScaleMode,
    check_identities,
    solve_ideal_performance,
)
from rocketforge.physics.thermochemistry import GammaStrategy

from .thermochemistry_service import ChamberOutcome, case_headline

__all__ = [
    "AmbientMode",
    "AmbientCondition",
    "PerformanceCase",
    "PerformanceOutcome",
    "PerformanceRow",
    "STANDARD_SEA_LEVEL_PRESSURE",
    "DEFAULT_PERFORMANCE_CASE",
    "EMPTY_OUTCOME",
    "OUTCOME_EMPTY",
    "OUTCOME_OK",
    "OUTCOME_WARNING",
    "OUTCOME_NO_CHAMBER",
    "OUTCOME_REDUCTION_REFUSED",
    "OUTCOME_NOZZLE_REFUSED",
    "OUTCOME_INVALID_INPUT",
    "GROUP_CHAMBER",
    "GROUP_NOZZLE",
    "GROUP_TOTAL",
    "GROUP_ENGINE",
    "PERFORMANCE_GROUPS",
    "solve_performance",
    "performance_rows",
    "thrust_rows",
    "reduction_rows",
    "assumption_rows",
    "assumption_groups",
    "inherited_diagnostics",
    "own_diagnostics",
    "reference_condition_results",
    "REFERENCE_CONDITIONS",
    "identity_rows",
    "performance_provenance",
    "GAMMA_STRATEGY_OPTIONS",
    "GAMMA_BASIS_OPTIONS",
    "AMBIENT_OPTIONS",
    "SCALE_OPTIONS",
]

#: The ISA sea-level static pressure, in pascals.
#:
#: An **input preset**, not a physical constant of this model: it is one value
#: a user might otherwise type into the ambient field, and no equation reads
#: it. It lives at the application boundary for that reason -- the engineering
#: layer takes a pascal value and does not know that one of them has a name.
STANDARD_SEA_LEVEL_PRESSURE = 101325.0


class AmbientMode(StrEnum):
    """How the ambient pressure was chosen.

    Three ways of naming one number, and **not** three physics paths:
    ``F_pressure = (p_e - p_a) A_e`` is the same equation in all of them, and
    vacuum is simply ``p_a = 0`` rather than a special case with its own
    formula.
    """

    VACUUM = "vacuum"
    SEA_LEVEL = "sea_level"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class AmbientCondition:
    """An ambient pressure, and the name the user gave it."""

    mode: AmbientMode = AmbientMode.VACUUM
    custom_pressure: float = STANDARD_SEA_LEVEL_PRESSURE

    def __post_init__(self) -> None:
        if not isinstance(self.mode, AmbientMode):
            raise TypeError(
                f"ambient mode must be an AmbientMode, got {self.mode!r}")
        if self.mode is AmbientMode.CUSTOM:
            value = float(self.custom_pressure)
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(
                    f"a custom ambient pressure must be finite and at or above "
                    f"zero, got {self.custom_pressure!r}. Zero is vacuum.")

    @property
    def pressure(self) -> float:
        if self.mode is AmbientMode.VACUUM:
            return 0.0
        if self.mode is AmbientMode.SEA_LEVEL:
            return STANDARD_SEA_LEVEL_PRESSURE
        return float(self.custom_pressure)

    @property
    def label(self) -> str:
        if self.mode is AmbientMode.VACUUM:
            return "vacuum, p_a = 0"
        if self.mode is AmbientMode.SEA_LEVEL:
            return f"sea level, p_a = {STANDARD_SEA_LEVEL_PRESSURE:g} Pa"
        return f"p_a = {self.pressure:g} Pa"


@dataclass(frozen=True, slots=True)
class PerformanceCase:
    """Everything the user chose here, beside the chamber they chose earlier.

    Five decisions, none of them defaulted anywhere downstream: which gamma to
    reduce to, on which basis, what area ratio to expand through, what ambient
    pressure to fly at, and what size of engine -- if any -- to scale to.
    """

    gamma_strategy: GammaStrategy = GammaStrategy.CHAMBER
    gamma_basis: ChamberGammaBasis = ChamberGammaBasis.FROZEN
    area_ratio: float = 40.0
    ambient: AmbientCondition = field(default_factory=AmbientCondition)
    scale: PerformanceScale = field(default_factory=PerformanceScale)

    def replace(self, **changes: Any) -> "PerformanceCase":
        from dataclasses import replace as _replace

        return _replace(self, **changes)

    @property
    def headline(self) -> str:
        return (f"Ae/At {self.area_ratio:g} · {self.ambient.label} · "
                f"gamma {self.gamma_strategy.value}/{self.gamma_basis.value}")


#: The demonstration case: the frozen basis, because a constant-composition
#: expansion is what this model actually computes; vacuum, because it is the
#: unambiguous reference condition; normalized, because no engine has been
#: sized yet and inventing a throat area would produce a thrust figure that
#: looks like an answer.
DEFAULT_PERFORMANCE_CASE = PerformanceCase()

OUTCOME_EMPTY = "empty"
OUTCOME_OK = "ok"
OUTCOME_WARNING = "warning"
OUTCOME_NO_CHAMBER = "no_chamber"
OUTCOME_REDUCTION_REFUSED = "reduction_refused"
OUTCOME_NOZZLE_REFUSED = "nozzle_refused"
OUTCOME_INVALID_INPUT = "invalid_input"

_STATUS_LABELS = {
    OUTCOME_EMPTY: "No result yet",
    OUTCOME_OK: "Solved",
    OUTCOME_WARNING: "Solved with warnings",
    OUTCOME_NO_CHAMBER: "No chamber state",
    OUTCOME_REDUCTION_REFUSED: "Gas reduction refused",
    OUTCOME_NOZZLE_REFUSED: "Outside the ideal model",
    OUTCOME_INVALID_INPUT: "Input refused",
}

_STATUS_TONES = {
    OUTCOME_EMPTY: "neutral",
    OUTCOME_OK: "success",
    OUTCOME_WARNING: "warning",
    OUTCOME_NO_CHAMBER: "neutral",
    OUTCOME_REDUCTION_REFUSED: "warning",
    OUTCOME_NOZZLE_REFUSED: "warning",
    OUTCOME_INVALID_INPUT: "warning",
}

#: The gamma strategies offered, with the meaning of each stated.
#:
#: Only the two the model can evaluate from a chamber state alone appear here.
#: The others need an expansion that has not been solved yet, and offering a
#: control that always refuses is worse than not offering it -- the handshake
#: still refuses them by name if one arrives from anywhere else.
GAMMA_STRATEGY_OPTIONS: tuple[dict[str, str], ...] = (
    {"key": GammaStrategy.CHAMBER.value, "label": "Chamber",
     "note": "Gamma taken at the chamber state."},
    {"key": GammaStrategy.THROAT.value, "label": "Throat",
     "note": "Gamma at the sonic condition. Under a constant-composition "
             "model this is the same chemical state as the chamber, so it is "
             "the same number - stated explicitly rather than assumed."},
)

#: Which of the two exponents in a chamber state to reduce to. They differ by
#: several per cent on a real case, so the choice is a visible input.
GAMMA_BASIS_OPTIONS: tuple[dict[str, str], ...] = (
    {"key": ChamberGammaBasis.FROZEN.value, "label": "Frozen  cp/cv",
     "note": "The exponent of a constant-composition isentropic process - "
             "which is the process this model computes. Like-for-like with a "
             "provider's frozen-at-chamber expansion."},
    {"key": ChamberGammaBasis.EQUILIBRIUM.value, "label": "Equilibrium  gamma_s",
     "note": "The isentropic exponent of a shifting-equilibrium expansion. "
             "Held constant it approximates that expansion - closely near the "
             "throat, less so far downstream."},
)

AMBIENT_OPTIONS: tuple[dict[str, str], ...] = (
    {"key": AmbientMode.VACUUM.value, "label": "Vacuum",
     "note": "p_a = 0, so the pressure term is p_e·A_e and is always "
             "positive."},
    {"key": AmbientMode.SEA_LEVEL.value, "label": "Sea level",
     "note": f"p_a = {STANDARD_SEA_LEVEL_PRESSURE:g} Pa, the ISA sea-level "
             "static pressure."},
    {"key": AmbientMode.CUSTOM.value, "label": "Custom",
     "note": "Any ambient pressure at or above zero, in pascals."},
)

SCALE_OPTIONS: tuple[dict[str, str], ...] = (
    {"key": PerformanceScaleMode.NORMALIZED.value, "label": "None",
     "note": "No engine size. c*, Cf, c_eff and Isp need none; thrust, mass "
             "flow and areas are withheld rather than defaulted."},
    {"key": PerformanceScaleMode.THROAT_AREA.value, "label": "Throat area",
     "note": "A_t in m². Mass flow follows from the choked-flow relation."},
    {"key": PerformanceScaleMode.MASS_FLOW.value, "label": "Mass flow",
     "note": "mdot in kg/s. The throat area follows from "
             "A_t = mdot·c*/p_c."},
)


@dataclass(frozen=True, slots=True)
class PerformanceOutcome:
    """One completed performance calculation, or one completed refusal.

    ``chamber`` is the exact ``ChamberOutcome`` this was computed from, held by
    identity so a result can still say which chamber it belongs to after the
    Thermochemistry workspace has moved on to another one.
    """

    kind: str
    case: PerformanceCase | None = None
    chamber: ChamberOutcome | None = None
    result: IdealRocketPerformance | None = None
    diagnostics: tuple[Any, ...] = ()
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.result is not None

    @property
    def status_label(self) -> str:
        return _STATUS_LABELS.get(self.kind, "Unknown")

    @property
    def status_tone(self) -> str:
        return _STATUS_TONES.get(self.kind, "neutral")

    @property
    def has_warnings(self) -> bool:
        return self.kind == OUTCOME_WARNING

    @property
    def is_scaled(self) -> bool:
        return self.result is not None and self.result.is_scaled

    @property
    def chamber_headline(self) -> str:
        return case_headline(self.chamber.case) if self.chamber else ""

    @property
    def headline(self) -> str:
        """What this result is for, built from the case it carries.

        Never from the live input form: that is how a result gets relabelled
        with conditions that did not produce it (Phase 5D section 133).
        """
        if self.case is None:
            return ""
        chamber = self.chamber_headline
        if chamber:
            return f"{chamber} · {self.case.headline}"
        return self.case.headline


EMPTY_OUTCOME = PerformanceOutcome(kind=OUTCOME_EMPTY)


def solve_performance(chamber: ChamberOutcome | None,
                      case: PerformanceCase) -> PerformanceOutcome:
    """Reduce the chamber state, then solve the ideal nozzle. Never raises.

    Refuses rather than substituting at each of the three places it can: no
    accepted chamber state, a reduction the single-gamma preconditions
    rejected, or a nozzle regime the ideal model is not defined for.

    Calls no provider. The chamber state is an input to this function, and
    that is the whole of the zero-re-solve guarantee.
    """
    if chamber is None or chamber.state is None:
        return PerformanceOutcome(
            kind=OUTCOME_NO_CHAMBER, case=case, chamber=chamber,
            message="Ideal performance starts from an accepted chamber "
                    "equilibrium. Solve one on the Thermochemistry tab first "
                    "- nothing here is estimated in its place.")

    if getattr(chamber.case, "propellant_kind", "") == "solid":
        # A solid formulation's chamber state. Refused here, explicitly, and not
        # left to the reduction's condensed-phase gate: that gate stops an
        # aluminised grain, but a non-metalised one arrives with no condensed
        # mass at all and would otherwise pass straight through and publish an
        # ideal-rocket result for a solid propellant. Solid reference
        # performance is deferred to R1.1, pending an authoritative solid
        # expansion benchmark; until then there is no validated claim to make.
        return PerformanceOutcome(
            kind=OUTCOME_NOZZLE_REFUSED, case=case, chamber=chamber,
            message="The current chamber state is a solid-propellant "
                    "formulation. Solid rocket performance is not part of "
                    "this build: only its chamber thermochemistry is "
                    "validated. Nothing is estimated in its place.")

    reduction = reduce_chamber_gas(
        chamber.state, case.gamma_strategy, case.gamma_basis,
        chamber_pressure=chamber.case.chamber_pressure if chamber.case else None)
    if reduction.value is None:
        first = reduction.diagnostics[0] if reduction.diagnostics else None
        return PerformanceOutcome(
            kind=OUTCOME_REDUCTION_REFUSED, case=case, chamber=chamber,
            diagnostics=tuple(reduction.diagnostics),
            message=first.message if first else
                    "This chamber state cannot be reduced to a single-gamma "
                    "perfect gas.")

    try:
        request = IdealPerformanceRequest(
            reduced=reduction.value,
            chamber_pressure=chamber.case.chamber_pressure,
            area_ratio=case.area_ratio,
            ambient_pressure=case.ambient.pressure,
            scale=case.scale)
    except (ValueError, TypeError) as error:
        return PerformanceOutcome(
            kind=OUTCOME_INVALID_INPUT, case=case, chamber=chamber,
            diagnostics=tuple(reduction.diagnostics), message=str(error))

    solution = solve_ideal_performance(request)
    diagnostics = tuple(reduction.diagnostics) + tuple(solution.diagnostics)
    if solution.value is None:
        refusal = next((d for d in solution.diagnostics
                        if str(d.severity) == "error"), None)
        return PerformanceOutcome(
            kind=OUTCOME_NOZZLE_REFUSED, case=case, chamber=chamber,
            diagnostics=diagnostics,
            message=refusal.message if refusal else
                    "No ideal performance figure is defined for this "
                    "operating point.")

    warned = (any(str(d.severity) == "warning" for d in diagnostics)
              or chamber.has_warnings)
    return PerformanceOutcome(
        kind=OUTCOME_WARNING if warned else OUTCOME_OK,
        case=case, chamber=chamber, result=solution.value,
        diagnostics=diagnostics)


# ---------------------------------------------------------------------------
# display rows -- numeric, never formatted here
# ---------------------------------------------------------------------------


GROUP_CHAMBER = "Chamber / choked flow"
GROUP_NOZZLE = "Nozzle expansion"
GROUP_TOTAL = "Total propulsive performance"
GROUP_ENGINE = "Scaled engine"

#: The display order. The grouping is the physics grouping: c* belongs to the
#: chamber and the throat, Cf to the nozzle, c_eff and Isp to the two together.
#: A flat list of eight numbers would let a reader take c* for an exhaust
#: velocity, which is the most common misreading of these quantities.
PERFORMANCE_GROUPS: tuple[dict[str, str], ...] = (
    {"key": GROUP_CHAMBER, "title": GROUP_CHAMBER,
     "note": "Fixed by the gas and the chamber alone. Independent of the area "
             "ratio and of the ambient pressure."},
    {"key": GROUP_NOZZLE, "title": GROUP_NOZZLE,
     "note": "Fixed by the area ratio and the gas; the ambient pressure "
             "enters the pressure term only."},
    {"key": GROUP_TOTAL, "title": GROUP_TOTAL,
     "note": "The product of the two above: c_eff = Cf · c*, and "
             "Isp = c_eff / g0."},
    {"key": GROUP_ENGINE, "title": GROUP_ENGINE,
     "note": "Needs an engine size. Withheld entirely when none was given."},
)


@dataclass(frozen=True, slots=True)
class PerformanceRow:
    """One displayed quantity, still numeric.

    Formatting belongs to the view. ``value`` stays a float here so a test can
    assert on the number rather than on a rendering of it.
    """

    key: str
    label: str
    unit: str
    value: float | None
    group: str
    qualifier: str = ""
    emphasis: bool = False
    help: str = ""

    @property
    def available(self) -> bool:
        return self.value is not None and math.isfinite(self.value)


_HELP = {
    "c_star": (
        "Characteristic velocity, c* = p_c*A_t / mdot. A chamber and "
        "choked-throat quantity: how effectively the combustion products turn "
        "chamber conditions into mass flow. It is NOT the exhaust velocity, "
        "and it does not change with ambient pressure or area ratio."),
    "cf": (
        "Thrust coefficient, Cf = F / (p_c*A_t). Dimensionless. It measures "
        "how much the nozzle amplifies the thrust the chamber would produce "
        "through a bare throat."),
    "cf_momentum": (
        "The momentum half of Cf, equal to V_e / c*. Independent of ambient "
        "pressure."),
    "cf_pressure": (
        "The pressure half of Cf, ((p_e - p_a)/p_c) * Ae/At. Negative when "
        "the exit pressure is below ambient: an overexpanded nozzle really "
        "does produce less thrust, and the sign is kept."),
    "c_eff": (
        "Effective exhaust velocity, c_eff = F / mdot = Cf * c*. It includes "
        "both the momentum and the pressure contribution, so it equals the "
        "exit velocity only when the nozzle is ideally expanded."),
    "isp": (
        "Specific impulse, Isp = c_eff / g0, in SECONDS. Impulse delivered "
        "per unit weight of propellant. It is not a burn duration, and a "
        "value in m/s is c_eff, not this."),
    "exit_velocity": (
        "The physical velocity of the gas crossing the exit plane. Distinct "
        "from the effective exhaust velocity."),
    "exit_mach": (
        "Exit Mach number. Fixed by the area ratio and gamma alone - ambient "
        "pressure does not enter it."),
    "exit_pressure": "Static pressure at the exit plane.",
    "exit_temperature": "Static temperature at the exit plane.",
    "exit_pressure_ratio": "p_e / p_c.",
    "mass_flow": "mdot = p_c*A_t / c*, the choked flow this throat passes.",
    "throat_area": "A_t, the sonic area.",
    "exit_area": "A_e = A_t * Ae/At.",
    "momentum_thrust": "mdot*V_e, the momentum contribution.",
    "pressure_thrust": (
        "(p_e - p_a)*A_e, the pressure contribution. Signed: negative for an "
        "overexpanded nozzle, and not clamped to zero."),
    "total_thrust": "F, the sum of the two contributions above.",
}


def performance_rows(outcome: PerformanceOutcome) -> tuple[PerformanceRow, ...]:
    """The scale-free performance, grouped as the physics groups it."""
    result = outcome.result
    if result is None:
        return ()
    exit_state = result.exit
    return (
        PerformanceRow("c_star", "Characteristic velocity  c*", "m/s",
                       result.characteristic_velocity, GROUP_CHAMBER,
                       qualifier="chamber and throat only", emphasis=True,
                       help=_HELP["c_star"]),

        PerformanceRow("exit_mach", "Exit Mach number  M_e", "",
                       exit_state.mach, GROUP_NOZZLE,
                       help=_HELP["exit_mach"]),
        PerformanceRow("exit_pressure", "Exit pressure  p_e", "Pa",
                       exit_state.pressure, GROUP_NOZZLE,
                       help=_HELP["exit_pressure"]),
        PerformanceRow("exit_pressure_ratio", "Exit pressure ratio  p_e/p_c",
                       "", exit_state.pressure_ratio, GROUP_NOZZLE,
                       help=_HELP["exit_pressure_ratio"]),
        PerformanceRow("exit_temperature", "Exit temperature  T_e", "K",
                       exit_state.temperature, GROUP_NOZZLE,
                       help=_HELP["exit_temperature"]),
        PerformanceRow("exit_velocity", "Exit velocity  V_e", "m/s",
                       exit_state.velocity, GROUP_NOZZLE,
                       qualifier="not the effective exhaust velocity",
                       help=_HELP["exit_velocity"]),
        PerformanceRow("cf_momentum", "Thrust coefficient, momentum term", "",
                       result.thrust_coefficient_momentum, GROUP_NOZZLE,
                       qualifier="V_e / c*", help=_HELP["cf_momentum"]),
        PerformanceRow("cf_pressure", "Thrust coefficient, pressure term", "",
                       result.thrust_coefficient_pressure, GROUP_NOZZLE,
                       qualifier="signed", help=_HELP["cf_pressure"]),
        PerformanceRow("cf", "Thrust coefficient  Cf", "",
                       result.thrust_coefficient, GROUP_NOZZLE,
                       qualifier="dimensionless", emphasis=True,
                       help=_HELP["cf"]),

        PerformanceRow("c_eff", "Effective exhaust velocity  c_eff", "m/s",
                       result.effective_exhaust_velocity, GROUP_TOTAL,
                       qualifier="Cf * c*", emphasis=True, help=_HELP["c_eff"]),
        PerformanceRow("isp", "Specific impulse  Isp", "s",
                       result.specific_impulse, GROUP_TOTAL,
                       qualifier="c_eff / g0", emphasis=True,
                       help=_HELP["isp"]),
    )


def thrust_rows(outcome: PerformanceOutcome) -> tuple[PerformanceRow, ...]:
    """The absolute engine.

    Empty when no size was given -- never a row of zeros. Zero thrust is a
    physical claim about an engine, not the absence of one.
    """
    result = outcome.result
    if result is None or not result.is_scaled:
        return ()
    thrust = result.thrust
    return (
        PerformanceRow("throat_area", "Throat area  A_t", "m²",
                       result.throat_area, GROUP_ENGINE,
                       help=_HELP["throat_area"]),
        PerformanceRow("exit_area", "Exit area  A_e", "m²",
                       result.exit_area, GROUP_ENGINE,
                       help=_HELP["exit_area"]),
        PerformanceRow("mass_flow", "Mass flow  mdot", "kg/s",
                       result.mass_flow, GROUP_ENGINE,
                       help=_HELP["mass_flow"]),
        PerformanceRow("momentum_thrust", "Momentum thrust  mdot*V_e", "N",
                       thrust.momentum, GROUP_ENGINE,
                       help=_HELP["momentum_thrust"]),
        PerformanceRow("pressure_thrust", "Pressure thrust  (p_e - p_a)*A_e",
                       "N", thrust.pressure, GROUP_ENGINE, qualifier="signed",
                       help=_HELP["pressure_thrust"]),
        PerformanceRow("total_thrust", "Total thrust  F", "N", thrust.total,
                       GROUP_ENGINE, emphasis=True,
                       help=_HELP["total_thrust"]),
    )


def reduction_rows(outcome: PerformanceOutcome) -> tuple[dict[str, str], ...]:
    """The gas reduction, in full.

    Shown because it is a modelling decision rather than a detail: the gamma
    that was used, where it came from, and the condensed fraction that was
    accepted are the three facts that decide whether the numbers above are
    comparable with anyone else's.
    """
    result = outcome.result
    if result is None:
        return ()
    reduced = result.reduced
    condensed = reduced.condensed_mass_fraction
    return (
        {"label": "Gamma strategy", "value": reduced.strategy.value},
        {"label": "Gamma basis", "value": reduced.basis.value},
        {"label": "Gamma used", "value": f"{reduced.gamma:.6f}"},
        {"label": "Gamma taken from", "value": reduced.gamma_source},
        {"label": "Specific gas constant  R",
         "value": f"{reduced.gas_constant:.4f} J/(kg K)"},
        {"label": "Stagnation temperature  T_0",
         "value": f"{reduced.stagnation_temperature:.2f} K"},
        {"label": "Chamber pressure  p_c",
         "value": f"{result.chamber_pressure:.6g} Pa"},
        {"label": "Ambient pressure  p_a",
         "value": f"{result.ambient_pressure:.6g} Pa"},
        {"label": "Area ratio  Ae/At",
         "value": f"{result.exit.area_ratio:g}"},
        {"label": "Nozzle regime", "value": result.exit.regime},
        {"label": "Engine size", "value": result.scale.label},
        {"label": "Condensed mass fraction accepted",
         "value": (f"{condensed:.3e}" if condensed is not None
                   else "not reported by the provider")},
    )


def assumption_rows(outcome: PerformanceOutcome) -> tuple[str, ...]:
    """What the ideal model claims, plus what the reduction committed to.

    Available before any result exists, so the panel is never empty: a reader
    should be able to find out what the model would assume before running it.
    """
    result = outcome.result
    if result is None:
        return IDEAL_MODEL_ASSUMPTIONS
    return tuple(result.assumptions) + tuple(result.reduced.assumptions)


def assumption_groups(outcome: PerformanceOutcome) -> tuple[dict[str, Any], ...]:
    """The same assumptions, attributed to whichever layer made them.

    Shown grouped rather than merged because the two lists overlap: both say
    the gas is single-phase and constant-property, in slightly different words.
    Concatenated, that reads as a list with duplicates in it and quietly
    undermines the panel. Separated, it reads as what it is -- the model states
    a requirement, and the reduction reports having met it.
    """
    result = outcome.result
    return (
        {"title": "The ideal rocket model",
         "note": "True of every result this workspace produces.",
         "items": list(result.assumptions if result is not None
                       else IDEAL_MODEL_ASSUMPTIONS)},
        {"title": "This gas reduction",
         "note": "What the chosen gamma strategy and basis committed to for "
                 "this particular chamber state.",
         "items": list(result.reduced.assumptions) if result is not None else []},
    )


#: The two reference conditions a provider quotes performance at.
#:
#: ``optimum`` is p_a = p_e, where the pressure term vanishes by construction.
#: It is an identity evaluated at a known exit pressure, not a search for a
#: best case, and no code here calls it optimal in the sense of preferable.
REFERENCE_CONDITIONS: tuple[dict[str, str], ...] = (
    {"key": "vacuum", "label": "vacuum",
     "note": "p_a = 0. The pressure term is at its largest."},
    {"key": "optimum", "label": "optimum expansion",
     "note": "p_a = p_e, so the pressure term is zero and Cf is the momentum "
             "term alone. An identity at this nozzle's own exit pressure."},
)


def reference_condition_results(outcome: PerformanceOutcome
                                ) -> dict[str, IdealRocketPerformance | None]:
    """This case re-evaluated at each reference condition a provider quotes.

    Needed because the user's ambient pressure is generally neither of them,
    and a comparison across different reference conditions measures the
    pressure term rather than the model difference it claims to measure.

    Re-solves the **nozzle** only. The gas reduction is reused exactly as it
    is, so no chemistry is touched and the two runs are demonstrably the same
    gas as the result on screen.
    """
    result = outcome.result
    if result is None:
        return {"vacuum": None, "optimum": None}

    def at(ambient: float) -> IdealRocketPerformance | None:
        solution = solve_ideal_performance(IdealPerformanceRequest(
            reduced=result.reduced,
            chamber_pressure=result.chamber_pressure,
            area_ratio=result.exit.area_ratio,
            ambient_pressure=ambient,
            scale=result.scale))
        return solution.value

    return {"vacuum": at(0.0), "optimum": at(result.exit.pressure)}


def own_diagnostics(outcome: PerformanceOutcome) -> tuple[dict[str, str], ...]:
    """Diagnostics raised by the reduction and by the nozzle solve."""
    return tuple(
        {"code": d.code, "severity": str(d.severity), "message": d.message,
         "field": d.field or "", "origin": "performance"}
        for d in outcome.diagnostics)


def inherited_diagnostics(outcome: PerformanceOutcome
                          ) -> tuple[dict[str, str], ...]:
    """Caveats that came from the chamber state, kept attached downstream.

    An assigned-enthalpy warning does not stop the performance algebra, and it
    does not stop applying either: the chamber state it describes is the one
    every number here was computed from. Dropping it at the layer boundary is
    how a caveat gets lost between two correct calculations.
    """
    chamber = outcome.chamber
    if chamber is None:
        return ()
    from .thermochemistry_service import diagnostic_rows

    return tuple(
        {"code": row.code, "severity": row.severity, "title": row.title,
         "message": row.message, "origin": "thermochemistry"}
        for row in diagnostic_rows(chamber, include_info=False))


def identity_rows(outcome: PerformanceOutcome) -> tuple[dict[str, Any], ...]:
    """Every internal identity, recomputed, for the validation panel."""
    if outcome.result is None:
        return ()
    report = check_identities(outcome.result)
    return tuple(
        {"name": check.name, "residual": check.residual,
         "tolerance": check.tolerance, "passed": check.passed,
         "scaled": check.scaled}
        for check in report.checks)


def performance_provenance(outcome: PerformanceOutcome
                           ) -> tuple[dict[str, str], ...]:
    """Who computed what. Two entries, never merged into one.

    The chamber row is read from the result's own chamber outcome rather than
    from whatever provider happens to be installed now, so a result keeps the
    identity of the provider that made it (Phase 5D section 180).
    """
    from .thermochemistry_service import provenance_summary

    rows = [{
        "role": "Ideal performance  (c*, Cf, c_eff, Isp, thrust)",
        "computed_by": "RocketForge",
        "model": "Ideal rocket: constant-property perfect gas, isentropic "
                 "shock-free expansion, no efficiency factor of any kind.",
        "detail": "rocketforge.engineering.nozzle over "
                  "rocketforge.physics.compressible",
    }]
    chamber = outcome.chamber
    if chamber is not None and chamber.provenance is not None:
        summary = provenance_summary(chamber)
        rows.append({
            "role": "Chamber equilibrium  (T_0, R, gamma, composition)",
            "computed_by": summary["provider"],
            "model": summary["model"],
            "detail": f"{summary['database']} {summary['sha']}".strip(),
        })
    else:
        rows.append({
            "role": "Chamber equilibrium  (T_0, R, gamma, composition)",
            "computed_by": "no chamber state",
            "model": "",
            "detail": "",
        })
    return tuple(rows)
