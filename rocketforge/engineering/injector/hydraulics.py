"""Injector orifice hydraulics: incompressible flow through a total orifice area.

Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed., section 8.1,
"Injector Flow Characteristics" (pp. 280-282). For an incompressible liquid
through hydraulic orifices::

    Q    = Cd A sqrt(2 dp / rho)                (Eq. 8-1)
    mdot = Q rho = Cd A sqrt(2 rho dp)          (Eq. 8-2)
    v    = Q / A = Cd sqrt(2 dp / rho)          (Eq. 8-5)

with Cd the discharge coefficient, rho the liquid density, A the orifice
cross-sectional area and dp the pressure drop across the injector elements.
Solving Eq. 8-2 for the area that passes a required mass flow::

    A = mdot / (Cd sqrt(2 rho dp))

``A`` is the *total* geometric orifice area of one propellant branch. Split
into ``N`` equal round holes of diameter ``d``, ``A = N pi d^2 / 4``.

**Nothing is chosen here.** Cd, rho and dp are inputs with no default, and the
discharge coefficient is not inferred from an orifice type: Sutton's Table 8-2
gives ranges that depend on the entrance, length and diameter of a particular
hole, and on Reynolds number. A value out of its domain is refused, never
clamped.

**Rounding to whole holes changes the pressure drop.** A hole diameter that
does not divide ``A`` into a whole number of holes gives an exact, fractional
equivalent count; built with the next whole number, the area grows and, at the
same mass flow, Eq. 8-2 gives ``dp_whole = dp (A / A_whole)^2``. Both are
reported; neither is substituted for the other.

The relations are hydraulic only. Atomization, mixing, combustion efficiency
and combustion stability are not computed and not implied.

SI units: kg/s, kg/m^3, Pa, m, m^2, m^3/s, m/s.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rocketforge.core.result import Diagnostic, Severity, Solution, Status

__all__ = [
    "WHOLE_COUNT_TOLERANCE",
    "DynamicHead",
    "HoleSplit",
    "OrificeSizing",
    "dynamic_head",
    "holes_from_count",
    "holes_from_diameter",
    "orifice_sizing",
]

#: A fractional hole count within this relative distance of a whole number is
#: that whole number: the fraction is rounding in A / a_hole, not a hole.
WHOLE_COUNT_TOLERANCE = 1.0e-9


def _finite(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _refuse(code: str, message: str, field: str) -> Solution:
    return Solution(value=None, status=Status.NO_SOLUTION,
                    diagnostics=(Diagnostic(code=code, severity=Severity.ERROR,
                                            message=message, field=field),))


def _check(mass_flow, density, pressure_drop, discharge_coefficient) -> Solution | None:
    if not (_finite(mass_flow) and mass_flow > 0.0):
        return _refuse("MASS_FLOW_INVALID", "The branch mass flow must be finite and above zero.",
                       "mass_flow")
    if not (_finite(density) and density > 0.0):
        return _refuse("DENSITY_INVALID", "The liquid density must be finite and above zero.",
                       "density")
    if not (_finite(pressure_drop) and pressure_drop > 0.0):
        return _refuse("PRESSURE_DROP_INVALID",
                       "The injector pressure drop must be finite and above zero.",
                       "pressure_drop")
    if not (_finite(discharge_coefficient) and 0.0 < discharge_coefficient <= 1.0):
        return _refuse("DISCHARGE_COEFFICIENT_INVALID",
                       "The discharge coefficient must be above 0 and at most 1.",
                       "discharge_coefficient")
    return None


@dataclass(frozen=True, slots=True)
class OrificeSizing:
    """One branch's total injector orifice, sized for its mass flow. SI.

    Attributes:
        mass_flow / density / pressure_drop / discharge_coefficient: The inputs.
        flow_area: A, the total geometric orifice area (Eq. 8-2 solved for A).
        effective_area: Cd A.
        volumetric_flow: Q = mdot / rho (Eq. 8-2).
        injection_velocity: v = Cd sqrt(2 dp / rho) (Eq. 8-5).
        mass_flow_closure: Cd A sqrt(2 rho dp) / mdot - 1 (Eq. 8-2 forward).
        velocity_closure: rho v A / mdot - 1 (Eq. 8-5 with Q = v A).
    """

    mass_flow: float
    density: float
    pressure_drop: float
    discharge_coefficient: float
    flow_area: float
    effective_area: float
    volumetric_flow: float
    injection_velocity: float
    mass_flow_closure: float
    velocity_closure: float


def orifice_sizing(mass_flow: float, density: float, pressure_drop: float,
                   discharge_coefficient: float) -> Solution[OrificeSizing]:
    """The total orifice area and injection velocity for one branch."""
    refused = _check(mass_flow, density, pressure_drop, discharge_coefficient)
    if refused is not None:
        return refused
    mdot, rho, dp, cd = (float(mass_flow), float(density), float(pressure_drop),
                         float(discharge_coefficient))
    area = mdot / (cd * math.sqrt(2.0 * rho * dp))
    velocity = cd * math.sqrt(2.0 * dp / rho)
    return Solution(
        value=OrificeSizing(
            mass_flow=mdot, density=rho, pressure_drop=dp, discharge_coefficient=cd,
            flow_area=area, effective_area=cd * area, volumetric_flow=mdot / rho,
            injection_velocity=velocity,
            mass_flow_closure=cd * area * math.sqrt(2.0 * rho * dp) / mdot - 1.0,
            velocity_closure=rho * velocity * area / mdot - 1.0),
        status=Status.OK,
        provenance=("Sutton & Biblarz 9th ed. §8.1, Eqs. 8-1, 8-2, 8-5",),
        inputs={"mass_flow": mdot, "density": rho, "pressure_drop": dp,
                "discharge_coefficient": cd})


@dataclass(frozen=True, slots=True)
class HoleSplit:
    """The total area as equal round holes. SI.

    ``hole_count`` is exact: whole when the count was stated, fractional when
    it follows from a stated diameter. ``whole_hole_count`` is the next whole
    number at or above it, with the area and, at the same mass flow, the
    pressure drop that whole number of holes gives.
    """

    flow_area: float
    hole_count: float
    hole_diameter: float
    hole_area: float
    whole_hole_count: int
    whole_hole_flow_area: float
    whole_hole_pressure_drop: float
    hole_area_closure: float        # N a_hole / A - 1, at the exact count


def _whole(count: float) -> int:
    nearest = round(count)
    if nearest >= 1 and abs(count - nearest) <= WHOLE_COUNT_TOLERANCE * count:
        return int(nearest)
    return math.ceil(count)


def _split(sizing: OrificeSizing, count: float, diameter: float) -> HoleSplit:
    hole_area = math.pi * diameter * diameter / 4.0
    whole = _whole(count)
    whole_area = whole * hole_area
    return HoleSplit(
        flow_area=sizing.flow_area, hole_count=count, hole_diameter=diameter,
        hole_area=hole_area, whole_hole_count=whole, whole_hole_flow_area=whole_area,
        whole_hole_pressure_drop=sizing.pressure_drop * (sizing.flow_area / whole_area) ** 2,
        hole_area_closure=count * hole_area / sizing.flow_area - 1.0)


def holes_from_count(sizing: OrificeSizing, hole_count: int) -> Solution[HoleSplit]:
    """N stated: the equal-hole diameter d = sqrt(4 A / (pi N))."""
    if isinstance(hole_count, bool) or not isinstance(hole_count, int) or hole_count < 1:
        return _refuse("HOLE_COUNT_INVALID", "The hole count must be a whole number of at "
                       "least 1.", "hole_count")
    diameter = math.sqrt(4.0 * sizing.flow_area / (math.pi * hole_count))
    return Solution(value=_split(sizing, float(hole_count), diameter), status=Status.OK)


def holes_from_diameter(sizing: OrificeSizing, hole_diameter: float) -> Solution[HoleSplit]:
    """d stated: the equivalent count N = A / (pi d^2 / 4), exact and whole."""
    if not (_finite(hole_diameter) and hole_diameter > 0.0):
        return _refuse("HOLE_DIAMETER_INVALID",
                       "The hole diameter must be finite and above zero.", "hole_diameter")
    d = float(hole_diameter)
    count = sizing.flow_area / (math.pi * d * d / 4.0)
    diagnostics = ()
    if count < 1.0:
        diagnostics = (Diagnostic(
            code="HOLE_LARGER_THAN_REQUIRED_AREA", severity=Severity.WARNING,
            message=(f"One hole of this diameter is {1.0 / count:.4g} times the required "
                     "area; the equivalent count is below one. One whole hole lowers the "
                     "pressure drop accordingly."),
            field="hole_diameter"),)
    return Solution(value=_split(sizing, count, d),
                    status=Status.OK_WITH_WARNINGS if diagnostics else Status.OK,
                    diagnostics=diagnostics)


@dataclass(frozen=True, slots=True)
class DynamicHead:
    """The dynamic flow head 1/2 rho v^2 at a stated line diameter. SI."""

    line_diameter: float
    line_area: float
    line_velocity: float
    dynamic_head: float


def dynamic_head(mass_flow: float, density: float, line_diameter: float
                 ) -> Solution[DynamicHead]:
    """Sutton Eq. 11-6/11-7's dynamic flow head, 1/2 rho v^2, with
    v = mdot / (rho pi D^2 / 4) in a round line of diameter D."""
    if not (_finite(mass_flow) and mass_flow > 0.0):
        return _refuse("MASS_FLOW_INVALID", "The branch mass flow must be finite and above "
                       "zero.", "mass_flow")
    if not (_finite(density) and density > 0.0):
        return _refuse("DENSITY_INVALID", "The liquid density must be finite and above zero.",
                       "density")
    if not (_finite(line_diameter) and line_diameter > 0.0):
        return _refuse("LINE_DIAMETER_INVALID",
                       "The feed-line diameter must be finite and above zero.", "line_diameter")
    area = math.pi * float(line_diameter) ** 2 / 4.0
    velocity = float(mass_flow) / (float(density) * area)
    return Solution(value=DynamicHead(line_diameter=float(line_diameter), line_area=area,
                                      line_velocity=velocity,
                                      dynamic_head=0.5 * float(density) * velocity * velocity),
                    status=Status.OK,
                    provenance=("Sutton & Biblarz 9th ed. §11.5, Eqs. 11-6, 11-7",))
