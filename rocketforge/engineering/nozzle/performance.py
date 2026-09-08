"""Ideal rocket performance: c*, Cf, thrust, effective exhaust velocity, Isp.

RocketForge owns these equations. NASA CEA returns all three of c*, Cf and Isp
natively and **none of those values appears here**: the provider sits beside
this chain as an oracle, not inside it. This module imports no provider, no Qt
and no application code, and it computes from a reduced chamber gas alone -- so
it works on a machine with no chemistry library installed at all.

The chain, and the direction of every arrow::

    ReducedChamberGas                (an explicit gamma strategy, already chosen)
        |
        +--> c*        = sqrt(R T0) / Gamma(gamma)      frozen choked flow
        |
        +--> exit      = area ratio + gamma             frozen nozzle physics
        |
        +--> Cf        = Ve/c*  +  ((pe - pa)/pc) eps
        |
        +--> F         = mdot Ve  +  (pe - pa) Ae       when a size is given
        |
        +--> c_eff     = Cf c*   ==   F / mdot
        |
        +--> Isp       = c_eff / g0

**No relation is restated.** The mass-flow parameter, the area-Mach relation
and the nozzle's critical pressure ratios all come from frozen Compressible
v1.0. What this module adds is the rocket layer ADR-15 assigns to it: turning
gas dynamics into propulsion performance.

Three things the equations here are careful about, because each is a way a
plausible number can be wrong:

* **c* does not depend on ambient pressure or area ratio.** It is set at the
  throat. A c* that moved with altitude would mean the chamber and the nozzle
  had been confused for each other.
* **The pressure thrust is signed.** An overexpanded nozzle has ``pe < pa`` and
  its pressure term *reduces* thrust. Clamping that to zero would turn a real
  performance loss into a silent gain.
* **c_eff is not the exit velocity.** They differ by exactly the pressure term
  divided by the mass flow, and coincide only at ideal expansion.
"""

from __future__ import annotations

import math

from rocketforge.core.constants import STANDARD_GRAVITY
from rocketforge.core.result import Diagnostic, Severity, Solution, Status
from rocketforge.physics.compressible import isentropic, mass_flow, nozzle
from rocketforge.physics.compressible.types import NozzleRegime

from .types import (
    IdealPerformanceRequest,
    IdealRocketPerformance,
    NozzleExitState,
    PerformanceScale,
    PerformanceScaleMode,
    ThrustBreakdown,
)

__all__ = [
    "characteristic_velocity",
    "solve_ideal_performance",
    "STANDARD_GRAVITY",
    "SUPPORTED_NOZZLE_REGIMES",
]

#: The three regimes that share the shock-free, fully supersonic internal
#: solution this model is defined for. See ``types.SUPPORTED_REGIMES``.
SUPPORTED_NOZZLE_REGIMES = frozenset({
    NozzleRegime.OVEREXPANDED,
    NozzleRegime.IDEALLY_EXPANDED,
    NozzleRegime.UNDEREXPANDED,
})


# ---------------------------------------------------------------------------
# characteristic velocity
# ---------------------------------------------------------------------------


def characteristic_velocity(gas, stagnation_temperature: float) -> float:
    """c* [m/s], the chamber and choked-throat performance quantity.

    Defined as ``c* = p_c A_t / mdot``: the chamber pressure and throat area
    needed to pass a given mass flow. It measures how much thrust-producing
    mass flow a chamber of a given pressure can generate -- how good the
    *propellant and its combustion* are -- and says nothing about the nozzle.

    **It is not the exhaust velocity.** For a typical LOX/CH₄ chamber c* is
    around 1800 m/s while the exhaust leaves at over 3000 m/s. Reading one as
    the other is a 70 % error.

    Derived from the frozen mass-flow parameter rather than from a second
    closed form. Phase 4 defines ``MFP = mdot sqrt(R T0) / (A p0)`` and
    ``Gamma(gamma)`` as its value at Mach 1, so::

        mdot = Gamma A_t p_c / sqrt(R T0)
        c*   = p_c A_t / mdot = sqrt(R T0) / Gamma(gamma)

    which is one substitution away from the definition and reuses the choking
    physics that was already validated, instead of restating the vandenkerckhove
    function here.

    Args:
        gas: A ``PerfectGas`` carrying gamma and a gas constant.
        stagnation_temperature: T0 [K], the chamber stagnation temperature.

    Returns:
        c* [m/s].
    """
    temperature = float(stagnation_temperature)
    if not math.isfinite(temperature) or temperature <= 0.0:
        raise ValueError(
            f"the stagnation temperature must be finite and positive, got "
            f"{stagnation_temperature!r}")
    gas_constant = gas.gas_constant
    if gas_constant is None or gas_constant <= 0.0:
        raise ValueError(
            "c* is a dimensional quantity and needs a gas constant; this gas "
            "was constructed without one")
    return math.sqrt(gas_constant * temperature) / mass_flow.choked_mass_flow_coefficient(gas)


# ---------------------------------------------------------------------------
# the solve
# ---------------------------------------------------------------------------


def solve_ideal_performance(
    request: IdealPerformanceRequest,
) -> Solution[IdealRocketPerformance]:
    """Ideal rocket performance for one operating point.

    Returns a ``Solution``. The value is ``None`` and the status is
    ``NO_SOLUTION`` when the nozzle is not in a regime this model is defined
    for -- an internal shock, a shock at the exit plane, a choked subsonic
    diverging section or an unchoked nozzle are all *different internal
    solutions*, and reporting an ideal supersonic figure for one of them would
    lend this model's authority to a flow it did not solve.

    Malformed input raises; the request validates itself on construction.
    """
    reduced = request.reduced
    gas = reduced.gas
    chamber_pressure = float(request.chamber_pressure)
    ambient_pressure = float(request.ambient_pressure)
    area_ratio = float(request.area_ratio)

    diagnostics: list[Diagnostic] = []

    # ---- the exit plane, from frozen nozzle physics ----------------------
    #
    # The internal solution of an ideal rocket nozzle is the shock-free
    # supersonic branch, fixed by the area ratio and gamma alone. Ambient
    # pressure does not enter it -- it enters the pressure-thrust term. So the
    # exit state comes from the critical-ratio calculation, which needs no back
    # pressure and therefore also works in a vacuum, where a back-pressure
    # ratio of zero is outside the classifier's domain.
    criticals = nozzle.critical_pressure_ratios(area_ratio, gas)
    if criticals.value is None:
        return Solution(value=None, status=Status.NO_SOLUTION,
                        diagnostics=criticals.diagnostics)
    critical = criticals.value
    diagnostics.extend(criticals.diagnostics)

    exit_mach = float(critical.mach_exit_supersonic)
    exit_pressure_ratio = float(critical.third_critical)
    exit_pressure = exit_pressure_ratio * chamber_pressure

    regime, regime_diagnostics = _classify(area_ratio, chamber_pressure,
                                           ambient_pressure, gas, critical)
    diagnostics.extend(regime_diagnostics)
    if regime not in SUPPORTED_NOZZLE_REGIMES:
        return Solution(
            value=None, status=Status.NO_SOLUTION,
            diagnostics=tuple(diagnostics) + (Diagnostic(
                code="NOZZLE_REGIME_UNSUPPORTED", severity=Severity.ERROR,
                message=(
                    f"The nozzle is {regime.value!r} at this ambient pressure, "
                    "which is a different internal solution from the "
                    "shock-free supersonic expansion this ideal model "
                    "computes. Ideal performance is not reported for it; "
                    f"lower the ambient pressure below "
                    f"{critical.second_critical * chamber_pressure:.6g} Pa, or "
                    "reduce the area ratio."),
                field="nozzle_regime",
                detail={"second_critical_pressure":
                        critical.second_critical * chamber_pressure,
                        "third_critical_pressure": exit_pressure}),))

    exit_temperature = float(
        isentropic.temperature_ratio(exit_mach, gas)) * reduced.stagnation_temperature
    exit_velocity = exit_mach * float(gas.speed_of_sound(exit_temperature))

    exit_state = NozzleExitState(
        mach=exit_mach,
        pressure=exit_pressure,
        temperature=exit_temperature,
        velocity=exit_velocity,
        pressure_ratio=exit_pressure_ratio,
        area_ratio=area_ratio,
        regime=str(regime.value),
        ambient_pressure=ambient_pressure,
    )

    # ---- the scale-free performance --------------------------------------
    c_star = characteristic_velocity(gas, reduced.stagnation_temperature)

    # Cf = Ve/c*  +  ((pe - pa)/pc) * epsilon
    #
    # The pressure term is signed on purpose. pe < pa is an overexpanded
    # nozzle: the term is negative and thrust really is lower.
    cf_momentum = exit_velocity / c_star
    cf_pressure = ((exit_pressure - ambient_pressure) / chamber_pressure) * area_ratio
    cf_total = cf_momentum + cf_pressure

    effective_exhaust_velocity = cf_total * c_star
    specific_impulse = effective_exhaust_velocity / STANDARD_GRAVITY

    if cf_pressure < 0.0:
        diagnostics.append(Diagnostic(
            code="OVEREXPANDED_PRESSURE_THRUST", severity=Severity.INFO,
            message=(
                f"The exit pressure {exit_pressure:.6g} Pa is below the ambient "
                f"{ambient_pressure:.6g} Pa, so the pressure term reduces "
                "thrust in this ideal model. The value is negative because the "
                "physics is, not because anything failed."),
            field="thrust_coefficient_pressure",
            detail={"exit_pressure": exit_pressure,
                    "ambient_pressure": ambient_pressure}))

    # ---- the absolute engine, if a size was given -------------------------
    throat_area, exit_area, mdot, thrust = _apply_scale(
        request.scale, gas, reduced, chamber_pressure, c_star, area_ratio,
        exit_velocity, exit_pressure, ambient_pressure)

    result = IdealRocketPerformance(
        characteristic_velocity=c_star,
        thrust_coefficient_momentum=cf_momentum,
        thrust_coefficient_pressure=cf_pressure,
        thrust_coefficient=cf_total,
        effective_exhaust_velocity=effective_exhaust_velocity,
        specific_impulse=specific_impulse,
        exit=exit_state,
        chamber_pressure=chamber_pressure,
        ambient_pressure=ambient_pressure,
        scale=request.scale,
        reduced=reduced,
        thrust=thrust,
        throat_area=throat_area,
        exit_area=exit_area,
        mass_flow=mdot,
        diagnostics=tuple(diagnostics),
    )
    status = (Status.OK_WITH_WARNINGS
              if any(d.severity is Severity.WARNING for d in diagnostics)
              else Status.OK)
    return Solution(value=result, status=status, diagnostics=tuple(diagnostics))


# ---------------------------------------------------------------------------
# internals
# ---------------------------------------------------------------------------


def _classify(area_ratio: float, chamber_pressure: float,
              ambient_pressure: float, gas, critical):
    """Which regime the nozzle is in at this ambient pressure.

    A vacuum is handled by definition rather than by calling the classifier: a
    back-pressure ratio of zero is outside its declared domain of (0, 1), and
    zero is unambiguously below the third critical, which is where
    ``UNDEREXPANDED`` begins. Everything else goes to the frozen classifier so
    the boundary tolerances are its, not a second set invented here.
    """
    if ambient_pressure == 0.0:
        return NozzleRegime.UNDEREXPANDED, ()
    ratio = ambient_pressure / chamber_pressure
    if ratio >= 1.0:
        return NozzleRegime.UNCHOKED_SUBSONIC, ()
    classified = nozzle.classify(area_ratio, ratio, gas)
    if classified.value is None:
        return NozzleRegime.UNCHOKED_SUBSONIC, classified.diagnostics
    return classified.value.regime, classified.diagnostics


def _apply_scale(scale: PerformanceScale, gas, reduced, chamber_pressure: float,
                 c_star: float, area_ratio: float, exit_velocity: float,
                 exit_pressure: float, ambient_pressure: float):
    """Absolute mass flow, areas and thrust -- or four ``None``.

    ``None`` rather than zero. An unscaled request did not ask about an engine
    of a particular size, and reporting 0 N of thrust would answer a question
    nobody asked with a claim that is false for every real engine.
    """
    if scale.mode is PerformanceScaleMode.NORMALIZED:
        return None, None, None, None

    if scale.mode is PerformanceScaleMode.THROAT_AREA:
        throat_area = float(scale.value)
        # mdot from the frozen choked-flow relation rather than from
        # pc*At/c*: the same physics that defined c* in the first place, used
        # in the direction it was written.
        mdot = mass_flow.choked_mass_flow(
            gas, throat_area, chamber_pressure, reduced.stagnation_temperature)
    else:
        mdot = float(scale.value)
        # The inverse of c* = pc At / mdot. There is no second mass-flow
        # formula here -- this is the same relation solved for the other
        # unknown.
        throat_area = mdot * c_star / chamber_pressure

    exit_area = area_ratio * throat_area
    momentum = mdot * exit_velocity
    pressure = (exit_pressure - ambient_pressure) * exit_area
    return (throat_area, exit_area, mdot,
            ThrustBreakdown(momentum=momentum, pressure=pressure,
                            total=momentum + pressure))
