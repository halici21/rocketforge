"""Propellant tank internal volume and geometry: sphere, cylinder with domes.

Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed., section 6.2
(pp. 196-197): "Any gas volume above the propellant in sealed tanks is called
the ullage"; an "optimum shape for propellant tanks ... is spherical", and
larger tanks are "Most ... cylindrical with half ellipses at the ends".

**Volumes.** With the liquid mass m at storage density rho::

    V_liquid = m / rho
    V_tank   = V_liquid / (1 - u)        ullage stated as a fraction u of the tank
             = V_liquid + V_ullage       ullage stated as a volume
    fill     = V_liquid / V_tank

**Shapes** (all internal; no wall). R is the radius of the sphere or of the
cylinder::

    sphere                 V = 4/3 pi R^3            A = 4 pi R^2
    cylinder + 2 domes     V = pi R^2 L + 2 V_dome   A = 2 pi R L + 2 A_dome

A dome is half a spheroid of equatorial radius R and polar height h = k R,
with the ratio ``k`` stated, 0 < k <= 1. ``k = 1`` is the hemisphere. For
k < 1 the dome is half an oblate spheroid, with eccentricity
e = sqrt(1 - k^2)::

    V_dome = 2/3 pi R^2 h
    A_dome = pi R^2 + pi h^2 artanh(e) / e        (-> 2 pi R^2 as k -> 1)

**Two ways to fix a cylinder**, both well posed:

* the diameter is stated: the barrel length is L = (V - 2 V_dome) / (pi R^2).
  If the domes alone hold more than V, no barrel length exists and the
  request is refused. L = 0 is accepted exactly;
* the total length L_t = L + 2h is stated. Then
  V(R) = pi R^2 L_t - 2/3 pi k R^3 rises monotonically on 0 < R <= L_t/(2k).
  Its largest value, pi L_t^3 / (6 k^2), is two domes with no barrel. A larger
  V is refused; otherwise R is the one root, found by bracketed Brent.

Nothing is chosen: neither a shape, nor a diameter, nor an optimum. A stated
envelope (a maximum diameter or length) that the result exceeds is refused,
never stretched.

SI: kg, kg/m^3, m, m^2, m^3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from rocketforge.core.numerics import brent
from rocketforge.core.result import Diagnostic, Severity, Solution, Status

__all__ = [
    "SizingMode",
    "TankShape",
    "TankGeometry",
    "TankVolumes",
    "dome_area",
    "dome_volume",
    "solve_tank_geometry",
    "tank_volumes",
]


class TankShape(StrEnum):
    SPHERE = "sphere"
    CYLINDER_HEMISPHERICAL = "cylinder_hemispherical"
    CYLINDER_ELLIPSOIDAL = "cylinder_ellipsoidal"


class SizingMode(StrEnum):
    VOLUME = "volume"                    # sphere: the volume fixes the radius
    STATED_DIAMETER = "stated_diameter"  # cylinder: solve the barrel length
    STATED_LENGTH = "stated_length"      # cylinder: solve the diameter


def _finite(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _refuse(code: str, message: str, field: str) -> Solution:
    return Solution(value=None, status=Status.NO_SOLUTION,
                    diagnostics=(Diagnostic(code=code, severity=Severity.ERROR,
                                            message=message, field=field),))


@dataclass(frozen=True, slots=True)
class TankVolumes:
    liquid_mass: float
    density: float
    liquid_volume: float
    ullage_volume: float
    tank_volume: float
    ullage_fraction: float
    fill_fraction: float
    mass_closure: float            # rho V_liquid / m - 1
    ullage_closure: float          # (V_liquid + V_ullage) / V_tank - 1


def tank_volumes(liquid_mass: float, density: float, ullage_fraction: float | None = None,
                 ullage_volume: float | None = None) -> Solution[TankVolumes]:
    """Liquid, ullage and tank volume. Exactly one ullage statement."""
    if not (_finite(liquid_mass) and liquid_mass > 0.0):
        return _refuse("LIQUID_MASS_INVALID", "The liquid mass must be finite and above zero.",
                       "liquid_mass")
    if not (_finite(density) and density > 0.0):
        return _refuse("DENSITY_INVALID", "The storage density must be finite and above zero.",
                       "density")
    if (ullage_fraction is None) == (ullage_volume is None):
        raise ValueError("state the ullage exactly once: a fraction or a volume")
    m, rho = float(liquid_mass), float(density)
    liquid = m / rho
    if ullage_fraction is not None:
        if not (_finite(ullage_fraction) and 0.0 <= ullage_fraction < 1.0):
            return _refuse("ULLAGE_FRACTION_INVALID", "The ullage fraction must be at or above "
                           "0 and below 1 of the tank volume.", "ullage_fraction")
        u = float(ullage_fraction)
        tank = liquid / (1.0 - u)
        ullage = tank - liquid
    else:
        if not (_finite(ullage_volume) and ullage_volume >= 0.0):
            return _refuse("ULLAGE_VOLUME_INVALID", "The ullage volume must be finite and at "
                           "or above zero.", "ullage_volume")
        ullage = float(ullage_volume)
        tank = liquid + ullage
        u = ullage / tank
    return Solution(
        value=TankVolumes(liquid_mass=m, density=rho, liquid_volume=liquid,
                          ullage_volume=ullage, tank_volume=tank, ullage_fraction=u,
                          fill_fraction=liquid / tank,
                          mass_closure=rho * liquid / m - 1.0,
                          ullage_closure=(liquid + ullage) / tank - 1.0),
        status=Status.OK, provenance=("Sutton & Biblarz 9th ed. §6.2 (ullage)",))


def dome_volume(radius: float, ratio: float) -> float:
    """Half a spheroid of equatorial radius R and height k R: 2/3 pi R^2 (k R)."""
    return 2.0 / 3.0 * math.pi * radius * radius * (ratio * radius)


def _artanh_over_e(e: float) -> float:
    """artanh(e)/e, with its series near e = 0 where the quotient cancels."""
    if e < 1.0e-4:
        e2 = e * e
        return 1.0 + e2 / 3.0 + e2 * e2 / 5.0
    return math.atanh(e) / e


def dome_area(radius: float, ratio: float) -> float:
    """Internal surface of half a spheroid, 0 < k <= 1: pi R^2 + pi h^2 artanh(e)/e."""
    if not (0.0 < ratio <= 1.0):
        raise ValueError("the dome height ratio must be above 0 and at most 1")
    h = ratio * radius
    e = math.sqrt(max(0.0, 1.0 - ratio * ratio))
    return math.pi * radius * radius + math.pi * h * h * _artanh_over_e(e)


@dataclass(frozen=True, slots=True)
class TankGeometry:
    """One tank's internal geometry. SI. A sphere has no barrel and no dome."""

    shape: TankShape
    mode: SizingMode
    volume: float                  # the internal volume asked for
    radius: float
    diameter: float
    dome_ratio: float | None       # k = h/R
    dome_height: float | None
    dome_volume: float | None      # each
    barrel_length: float | None
    total_length: float            # along the axis; the diameter for a sphere
    surface_area: float            # internal wetted area of the whole tank
    geometric_volume: float        # recomputed from the dimensions
    volume_closure: float          # geometric / asked - 1
    convergence_iterations: int | None


def _sphere(volume: float) -> TankGeometry:
    radius = (3.0 * volume / (4.0 * math.pi)) ** (1.0 / 3.0)
    geometric = 4.0 / 3.0 * math.pi * radius ** 3
    return TankGeometry(
        shape=TankShape.SPHERE, mode=SizingMode.VOLUME, volume=volume, radius=radius,
        diameter=2.0 * radius, dome_ratio=None, dome_height=None, dome_volume=None,
        barrel_length=None, total_length=2.0 * radius,
        surface_area=4.0 * math.pi * radius * radius, geometric_volume=geometric,
        volume_closure=geometric / volume - 1.0, convergence_iterations=None)


def _capsule(shape: TankShape, mode: SizingMode, volume: float, radius: float, ratio: float,
             barrel: float, iterations: int | None) -> TankGeometry:
    dome_v = dome_volume(radius, ratio)
    geometric = math.pi * radius * radius * barrel + 2.0 * dome_v
    return TankGeometry(
        shape=shape, mode=mode, volume=volume, radius=radius, diameter=2.0 * radius,
        dome_ratio=ratio, dome_height=ratio * radius, dome_volume=dome_v,
        barrel_length=barrel, total_length=barrel + 2.0 * ratio * radius,
        surface_area=2.0 * math.pi * radius * barrel + 2.0 * dome_area(radius, ratio),
        geometric_volume=geometric, volume_closure=geometric / volume - 1.0,
        convergence_iterations=iterations)


def solve_tank_geometry(volume: float, shape: TankShape, mode: SizingMode,
                        diameter: float | None = None, total_length: float | None = None,
                        dome_ratio: float | None = None,
                        envelope_diameter: float | None = None,
                        envelope_length: float | None = None) -> Solution[TankGeometry]:
    """The internal geometry holding ``volume`` in the stated shape and mode.

    Args:
        volume: Internal tank volume, m^3.
        shape / mode: As stated; a sphere takes VOLUME only, a cylinder
            STATED_DIAMETER or STATED_LENGTH.
        diameter / total_length: The stated dimension of the mode.
        dome_ratio: k for ellipsoidal domes; 1 for hemispherical; absent for a
            sphere.
        envelope_diameter / envelope_length: Optional limits the result must
            not exceed.
    """
    if not (_finite(volume) and volume > 0.0):
        return _refuse("VOLUME_INVALID", "The tank volume must be finite and above zero.",
                       "volume")
    for name, value in (("envelope_diameter", envelope_diameter),
                        ("envelope_length", envelope_length)):
        if value is not None and not (_finite(value) and value > 0.0):
            return _refuse(f"{name.upper()}_INVALID",
                           f"The {name.replace('_', ' ')} must be finite and above zero.", name)
    v = float(volume)
    if shape is TankShape.SPHERE:
        if mode is not SizingMode.VOLUME:
            raise ValueError("a sphere is fixed by its volume")
        geometry = _sphere(v)
    else:
        if shape is TankShape.CYLINDER_HEMISPHERICAL:
            if dome_ratio not in (None, 1.0):
                raise ValueError("hemispherical domes have k = 1")
            k = 1.0
        else:
            if not (_finite(dome_ratio) and 0.0 < dome_ratio <= 1.0):
                return _refuse("DOME_RATIO_INVALID", "The dome height-to-radius ratio k must "
                               "be above 0 and at most 1 (k = 1 is a hemisphere).",
                               "dome_ratio")
            k = float(dome_ratio)
        if mode is SizingMode.STATED_DIAMETER:
            if not (_finite(diameter) and diameter > 0.0):
                return _refuse("DIAMETER_INVALID", "The tank diameter must be finite and above "
                               "zero.", "diameter")
            radius = float(diameter) / 2.0
            domes = 2.0 * dome_volume(radius, k)
            if domes > v:
                return _refuse(
                    "DIAMETER_TOO_LARGE",
                    f"At {float(diameter):g} m the two domes alone hold {domes:.6g} m³, more "
                    f"than the {v:.6g} m³ required, so no barrel length exists. State a "
                    "smaller diameter or a sphere.", "diameter")
            barrel = (v - domes) / (math.pi * radius * radius)
            geometry = _capsule(shape, mode, v, radius, k, barrel, None)
        elif mode is SizingMode.STATED_LENGTH:
            if not (_finite(total_length) and total_length > 0.0):
                return _refuse("LENGTH_INVALID", "The tank length must be finite and above "
                               "zero.", "total_length")
            lt = float(total_length)
            r_max = lt / (2.0 * k)
            v_max = math.pi * lt ** 3 / (6.0 * k * k)
            if v > v_max:
                return _refuse(
                    "LENGTH_TOO_SHORT",
                    f"A {lt:g} m tank of this dome shape holds at most {v_max:.6g} m³ (two "
                    f"domes, no barrel), less than the {v:.6g} m³ required. State a longer "
                    "tank.", "total_length")
            if v == v_max:
                radius, iterations = r_max, 0
            else:
                def residual(r: float) -> float:
                    return math.pi * r * r * lt - 2.0 / 3.0 * math.pi * k * r ** 3 - v

                radius, report = brent(residual, 0.0, r_max, xtol=1e-15 * r_max,
                                       rtol=4.0 * 2.2e-16, max_iter=200)
                if not report.converged:
                    return _refuse("RADIUS_NOT_CONVERGED", "The radius solve did not converge; "
                                   "no unconverged value is returned.", "diameter")
                iterations = report.iterations
            # R <= L_t/(2k) on the bracket, so a negative barrel is rounding only.
            barrel = max(0.0, lt - 2.0 * k * radius)
            geometry = _capsule(shape, mode, v, radius, k, barrel, iterations)
        else:
            raise ValueError("a cylinder is fixed by a stated diameter or length")
    if envelope_diameter is not None and geometry.diameter > envelope_diameter:
        return _refuse("ENVELOPE_DIAMETER_EXCEEDED",
                       f"The tank needs a {geometry.diameter:.6g} m diameter; the envelope "
                       f"allows {float(envelope_diameter):g} m.", "envelope_diameter")
    if envelope_length is not None and geometry.total_length > envelope_length:
        return _refuse("ENVELOPE_LENGTH_EXCEEDED",
                       f"The tank needs a {geometry.total_length:.6g} m length; the envelope "
                       f"allows {float(envelope_length):g} m.", "envelope_length")
    return Solution(value=geometry, status=Status.OK,
                    provenance=("Sutton & Biblarz 9th ed. §6.2 (tank shapes); analytic "
                                "sphere and spheroid volume and area",))
