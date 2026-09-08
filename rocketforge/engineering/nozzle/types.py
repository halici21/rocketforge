"""What an ideal rocket performance calculation is asked, and what it answers.

Records only. Every relation lives in :mod:`performance`; nothing here
computes anything, so a result can be constructed in a test without running the
solver, and mutated to prove a validator actually looks at it.

The split between *normalised* and *scaled* quantities is the one that shapes
these types. c*, Cf, the effective exhaust velocity and Isp are properties of
a gas, an area ratio and an ambient pressure; a throat area is not needed to
know any of them. Mass flow, areas and thrust are properties of an engine of a
particular size. So the second group is ``None`` when no scale was given --
never zero, because zero thrust is a physical claim about an engine rather than
an absence of one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum

from rocketforge.core.result import Diagnostic
from rocketforge.engineering.chamber import ReducedChamberGas

__all__ = [
    "PerformanceScaleMode",
    "PerformanceScale",
    "IdealPerformanceRequest",
    "NozzleExitState",
    "ThrustBreakdown",
    "IdealRocketPerformance",
    "IDEAL_MODEL_ASSUMPTIONS",
    "SUPPORTED_REGIMES",
]

#: What this model claims, stated once and attached to every result.
#:
#: Read as a list of what is **absent**: there is no combustion efficiency, no
#: c* or Cf efficiency, no divergence, viscous or boundary-layer loss, no
#: separation correction and no two-phase term. An ideal figure is an upper
#: bound on a real engine, and a user who reads one as a prediction is out by
#: several per cent -- which is exactly the number they would copy into a
#: spreadsheet.
IDEAL_MODEL_ASSUMPTIONS: tuple[str, ...] = (
    "Ideal: no efficiency factor of any kind is applied.",
    "Steady, one-dimensional flow.",
    "Inviscid: no boundary layer, no wall friction.",
    "Adiabatic nozzle: no heat loss through the wall.",
    "Isentropic expansion, shock-free and fully supersonic.",
    "Constant-property gas: gamma and R fixed at the reduced chamber values.",
    "Single phase: condensed products refuse the reduction rather than being "
    "averaged into the gas.",
    "No divergence, viscous, boundary-layer or separation correction.",
    "No finite-rate chemistry and no composition shift through the nozzle.",
)


class PerformanceScaleMode(StrEnum):
    """How, or whether, an absolute engine size is supplied.

    ``NORMALIZED`` is not a smaller version of the others: it is the honest
    statement that no engine size was given, and it returns every quantity that
    does not need one. Nothing here invents a default throat area -- a made-up
    size would produce a thrust figure that looks like an answer.
    """

    NORMALIZED = "normalized"
    THROAT_AREA = "throat_area"
    MASS_FLOW = "mass_flow"


@dataclass(frozen=True, slots=True)
class PerformanceScale:
    """The engine size, or the absence of one.

    ``value`` is the throat area in m² for ``THROAT_AREA`` and the mass flow in
    kg/s for ``MASS_FLOW``. It must be ``None`` for ``NORMALIZED`` and present
    otherwise: a mode and a value that disagree is how an engine ends up sized
    by a number nobody meant as a size.
    """

    mode: PerformanceScaleMode = PerformanceScaleMode.NORMALIZED
    value: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, PerformanceScaleMode):
            raise TypeError(
                f"scale mode must be a PerformanceScaleMode, got {self.mode!r}")
        if self.mode is PerformanceScaleMode.NORMALIZED:
            if self.value is not None:
                raise ValueError(
                    "a normalized request carries no engine size; pass "
                    "PerformanceScale() with no value, or choose a scale mode")
            return
        if self.value is None:
            raise ValueError(
                f"scale mode {self.mode.value!r} needs a value: a throat area "
                "in m² or a mass flow in kg/s")
        number = float(self.value)
        if not math.isfinite(number) or number <= 0.0:
            raise ValueError(
                f"the scale value must be finite and strictly positive, got "
                f"{self.value!r}")

    @property
    def is_scaled(self) -> bool:
        return self.mode is not PerformanceScaleMode.NORMALIZED

    @property
    def label(self) -> str:
        if self.mode is PerformanceScaleMode.NORMALIZED:
            return "Normalized — no engine size"
        unit = "m²" if self.mode is PerformanceScaleMode.THROAT_AREA else "kg/s"
        what = ("throat area At" if self.mode is PerformanceScaleMode.THROAT_AREA
                else "mass flow ṁ")
        return f"{what} = {self.value:g} {unit}"


#: The nozzle regimes an ideal performance figure is defined for.
#:
#: All three share one internal solution: shock-free, fully supersonic, exit
#: state fixed by the area ratio alone. They differ only in how the exit
#: pressure compares with ambient, which is precisely what the pressure-thrust
#: term expresses.
#:
#: Everything below the second critical -- a shock standing at or inside the
#: exit plane, a choked subsonic diverging section, an unchoked nozzle -- is a
#: *different internal solution*, and reporting an ideal supersonic figure for
#: it would attach this model's authority to a flow it did not solve.
SUPPORTED_REGIMES = ("overexpanded", "ideally_expanded", "underexpanded")


@dataclass(frozen=True, slots=True)
class IdealPerformanceRequest:
    """One ideal performance question, fully specified.

    Nothing is inferred. The gas reduction was already an explicit decision
    (:class:`ReducedChamberGas`); the area ratio, the ambient pressure and the
    engine size are the three remaining ones, and each is stated here rather
    than defaulted somewhere downstream.

    Attributes:
        reduced: The single-gamma gas the chamber state was reduced to, with
            the strategy that produced it.
        chamber_pressure: p_c [Pa]. The nozzle's stagnation pressure.
        area_ratio: Ae/At [-], above 1. Validated by the frozen nozzle module.
        ambient_pressure: p_a [Pa], zero or above. **Zero is vacuum**, not a
            missing value, and it needs no separate equation.
        scale: The engine size, or the absence of one.
    """

    reduced: ReducedChamberGas
    chamber_pressure: float
    area_ratio: float
    ambient_pressure: float
    scale: PerformanceScale = field(default_factory=PerformanceScale)

    def __post_init__(self) -> None:
        if not isinstance(self.reduced, ReducedChamberGas):
            raise TypeError(
                "a performance request needs a ReducedChamberGas -- the "
                "explicit gas reduction -- not a raw chamber state")
        for name, value, floor in (
                ("chamber pressure", self.chamber_pressure, 0.0),
                ("area ratio", self.area_ratio, 1.0),
        ):
            number = float(value)
            if not math.isfinite(number) or number <= floor:
                raise ValueError(
                    f"{name} must be finite and above {floor:g}, got {value!r}")
        ambient = float(self.ambient_pressure)
        if not math.isfinite(ambient) or ambient < 0.0:
            raise ValueError(
                f"ambient pressure must be finite and at or above zero, got "
                f"{self.ambient_pressure!r}. Zero is vacuum.")
        if not isinstance(self.scale, PerformanceScale):
            raise TypeError(
                f"scale must be a PerformanceScale, got {type(self.scale).__name__}")


@dataclass(frozen=True, slots=True)
class NozzleExitState:
    """The exit plane, as the frozen compressible module reported it.

    Kept rather than recomputed, and kept small: this is what the performance
    result needs to be traceable, not a copy of the whole nozzle solution.
    """

    mach: float
    pressure: float                 # p_e [Pa]
    temperature: float              # T_e [K]
    velocity: float                 # V_e [m/s]
    pressure_ratio: float           # p_e / p_c [-]
    area_ratio: float               # Ae/At [-]
    regime: str
    ambient_pressure: float         # p_a [Pa], the regime was classified at


@dataclass(frozen=True, slots=True)
class ThrustBreakdown:
    """Thrust, kept in its two physically distinct parts.

    They are separate outputs because they behave differently: the momentum
    term is fixed by the gas and the area ratio, while the pressure term
    changes sign with altitude. Collapsing them into one number hides the only
    part of the answer that depends on where the engine is flying.

    ``pressure`` is negative for an overexpanded nozzle and that is correct,
    not an error to be clipped away.
    """

    momentum: float                 # [N]
    pressure: float                 # [N], signed
    total: float                    # [N]


@dataclass(frozen=True, slots=True)
class IdealRocketPerformance:
    """Ideal rocket performance, computed by RocketForge.

    Attributes:
        characteristic_velocity: c* [m/s]. ``p_c A_t / mdot`` -- a chamber and
            choked-throat quantity. **It is not the exhaust velocity** and it
            does not change with ambient pressure or area ratio.
        thrust_coefficient_momentum: Cf from the momentum term, ``V_e / c*``.
        thrust_coefficient_pressure: Cf from the pressure term,
            ``((p_e - p_a) / p_c) * epsilon``. Signed.
        thrust_coefficient: The sum. Dimensionless.
        effective_exhaust_velocity: c_eff [m/s], ``F / mdot`` and equally
            ``Cf * c*``. **Not the same as the exit velocity** unless the
            nozzle is ideally expanded.
        specific_impulse: Isp [s], ``c_eff / g0``. Seconds of impulse per unit
            weight of propellant -- not a burn duration.
        exit: The exit plane state.
        thrust: Absolute thrust, or ``None`` when no engine size was given.
        throat_area / exit_area / mass_flow: Likewise ``None`` when unscaled.
        reduced: The gas reduction this was computed from, carrying the gamma
            strategy and the chamber state behind it.
        assumptions: What the ideal model claims. Attached to the result so it
            travels with the numbers.
        diagnostics: Anything a reader should know, including caveats inherited
            from the chamber state.
    """

    characteristic_velocity: float
    thrust_coefficient_momentum: float
    thrust_coefficient_pressure: float
    thrust_coefficient: float
    effective_exhaust_velocity: float
    specific_impulse: float
    exit: NozzleExitState
    chamber_pressure: float
    ambient_pressure: float
    scale: PerformanceScale
    reduced: ReducedChamberGas
    thrust: ThrustBreakdown | None = None
    throat_area: float | None = None        # [m²]
    exit_area: float | None = None          # [m²]
    mass_flow: float | None = None          # [kg/s]
    assumptions: tuple[str, ...] = IDEAL_MODEL_ASSUMPTIONS
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def is_scaled(self) -> bool:
        """Whether absolute quantities are available."""
        return self.thrust is not None

    @property
    def exit_velocity(self) -> float:
        """V_e [m/s]. Distinct from :attr:`effective_exhaust_velocity`."""
        return self.exit.velocity

    @property
    def is_ideally_expanded(self) -> bool:
        """Whether p_e equals p_a, so the pressure term vanishes."""
        return self.thrust_coefficient_pressure == 0.0
