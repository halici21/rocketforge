"""Combustion-chamber geometry from L*, contraction ratio and convergent angle.

The geometry is the one Sutton & Biblarz, *Rocket Propulsion Elements*, 9th
ed., section 8.2 ("Volume and Shape") describes: a flat injector face, a
cylindrical chamber, and a converging conical frustum down to the nozzle
throat, corner radii neglected. Two definitions from that section fix it:

* **Chamber volume** is the volume from the injector face to the throat. It
  includes the cylinder and the converging frustum (p. 285).
* **Characteristic length** ``L* = Vc / At`` (Eq. 8-9).

With the throat area ``At``, ``L*``, the contraction area ratio
``eps_c = Ac / At`` and the converging half-angle ``theta``, all stated::

    Vc     = L* At
    Ac     = eps_c At,               Rc = sqrt(Ac / pi),   Rt = sqrt(At / pi)
    L_conv = (Rc - Rt) / tan(theta)
    V_conv = (pi / 3) L_conv (Rc^2 + Rc Rt + Rt^2)
    V_cyl  = Vc - V_conv,            L_cyl = V_cyl / Ac
    L_inj  = L_cyl + L_conv          injector face to throat, axially

**The frustum volume carries a factor 1/3.** Sutton's Eq. 8-8 is printed as
``Vc = A1 L1 + A1 Lc (1 + sqrt(At/A1) + At/A1)``, without it. The printed form
contradicts itself: at ``At = A1`` the frustum is a cylinder of length ``Lc``
whose volume is ``A1 Lc``, and the printed form gives ``3 A1 Lc``. The
geometric volume of a frustum, used here, is ``(Lc/3)(A1 + sqrt(A1 At) + At)``,
which is Eq. 8-8 with the 1/3 restored.

Nothing is chosen here. L*, the contraction ratio and the angle are inputs
with no default; one that is out of its domain is refused, never clamped. A
converging section that alone needs more volume than ``L* At`` is refused,
with the smallest L* that this contraction ratio and angle admit.

**Rules of thumb are advisories.** Section 8.2 notes that chamber pressure
losses "may become appreciable when the chamber area is less than three times
the throat area", and gives 0.8-3.0 m as typical L* for several
bipropellants. Neither is a validity boundary of the geometry; both are
reported, neither refuses. L* fixes a volume. It does not establish
combustion completeness or stability, and nothing here says it does.

SI units: m, m^2, m^3, radians.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rocketforge.core.result import Diagnostic, Severity, Solution, Status

__all__ = [
    "CONTRACTION_PRESSURE_LOSS_ADVISORY",
    "CYLINDER_VOLUME_TOLERANCE",
    "TYPICAL_BIPROPELLANT_L_STAR",
    "ChamberGeometry",
    "conical_frustum_volume",
    "converging_length",
    "cylindrical_conical_chamber",
]

#: Sutton section 8.2, item 6: pressure losses ahead of the nozzle inlet "may
#: become appreciable when the chamber area is less than three times the throat
#: area". An advisory: the ideal performance upstream neglects that loss.
CONTRACTION_PRESSURE_LOSS_ADVISORY = 3.0

#: Sutton section 8.2, after Eq. 8-9: "Typical values for L* are between 0.8
#: and 3.0 m ... for several bipropellants". Information only: not a default,
#: not a validity range, not a combustion-completeness criterion.
TYPICAL_BIPROPELLANT_L_STAR = (0.8, 3.0)

#: A cylinder volume within this fraction of Vc below zero is rounding in
#: ``Vc - V_conv`` at the exact boundary, not a converging section that is too
#: large. It is reported as a cylinder of zero length, with a note.
CYLINDER_VOLUME_TOLERANCE = 1.0e-12


@dataclass(frozen=True, slots=True)
class ChamberGeometry:
    """A cylindrical chamber with a conical convergent to the throat. SI."""

    throat_area: float
    throat_radius: float
    characteristic_length: float
    contraction_ratio: float
    converging_half_angle: float     # rad, from the axis
    chamber_volume: float
    chamber_area: float
    chamber_radius: float
    converging_length: float
    converging_volume: float
    cylinder_length: float
    cylinder_volume: float
    injector_to_throat_length: float

    @property
    def characteristic_length_closure(self) -> float:
        """``((Ac L_cyl + V_conv) / At) / L* - 1``: the parts rebuilt into L*."""
        rebuilt = (self.chamber_area * self.cylinder_length + self.converging_volume)
        return rebuilt / self.throat_area / self.characteristic_length - 1.0

    @property
    def contraction_closure(self) -> float:
        """``(pi Rc^2) / (eps_c At) - 1``: the chamber radius rebuilt into Ac/At."""
        return (math.pi * self.chamber_radius ** 2
                / (self.contraction_ratio * self.throat_area) - 1.0)


def conical_frustum_volume(length: float, radius_a: float, radius_b: float) -> float:
    """Volume of a right circular conical frustum: ``(pi/3) h (a^2 + a b + b^2)``."""
    return math.pi / 3.0 * length * (radius_a * radius_a + radius_a * radius_b
                                     + radius_b * radius_b)


def converging_length(chamber_radius: float, throat_radius: float,
                      half_angle: float) -> float:
    """Axial length of a straight cone from ``chamber_radius`` to ``throat_radius``."""
    return (chamber_radius - throat_radius) / math.tan(half_angle)


def _refuse(code: str, message: str, field: str,
            detail: dict[str, float] | None = None) -> Solution[ChamberGeometry]:
    return Solution(value=None, status=Status.NO_SOLUTION,
                    diagnostics=(Diagnostic(code=code, severity=Severity.ERROR,
                                            message=message, field=field, detail=detail),))


def _finite_above(value: float, floor: float) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value > floor


def cylindrical_conical_chamber(throat_area: float, characteristic_length: float,
                                contraction_ratio: float, converging_half_angle: float
                                ) -> Solution[ChamberGeometry]:
    """The chamber that holds ``L* At`` from injector face to throat.

    Args:
        throat_area: At, m^2.
        characteristic_length: L*, m.
        contraction_ratio: Ac / At, above 1.
        converging_half_angle: The cone's half-angle from the axis, rad, in
            (0, pi/2).

    Returns a refusal, with a diagnostic naming the input, for an input out of
    its domain or for a converging section larger than the chamber volume.
    """
    if not _finite_above(throat_area, 0.0):
        return _refuse("THROAT_AREA_INVALID", "The throat area must be finite and above zero.",
                       "throat_area")
    if not _finite_above(characteristic_length, 0.0):
        return _refuse("CHARACTERISTIC_LENGTH_INVALID",
                       "L* must be finite and above zero.", "characteristic_length")
    if not _finite_above(contraction_ratio, 1.0):
        return _refuse("CONTRACTION_RATIO_INVALID",
                       "The contraction ratio Ac/At must be finite and above 1: the chamber "
                       "must be wider than the throat for a converging section to exist.",
                       "contraction_ratio")
    if not (_finite_above(converging_half_angle, 0.0)
            and converging_half_angle < math.pi / 2.0):
        return _refuse("CONVERGING_HALF_ANGLE_INVALID",
                       "The converging half-angle must be above 0 and below 90 degrees.",
                       "converging_half_angle")

    throat_radius = math.sqrt(throat_area / math.pi)
    chamber_volume = characteristic_length * throat_area
    chamber_area = contraction_ratio * throat_area
    chamber_radius = math.sqrt(chamber_area / math.pi)
    l_conv = converging_length(chamber_radius, throat_radius, converging_half_angle)
    v_conv = conical_frustum_volume(l_conv, chamber_radius, throat_radius)
    v_cyl = chamber_volume - v_conv

    diagnostics: list[Diagnostic] = []
    if v_cyl < 0.0:
        if v_cyl < -CYLINDER_VOLUME_TOLERANCE * chamber_volume:
            minimum = v_conv / throat_area
            return _refuse(
                "CONVERGING_SECTION_EXCEEDS_CHAMBER_VOLUME",
                f"The converging section alone needs {v_conv:.6g} m³, but L* · At allows "
                f"{chamber_volume:.6g} m³. At this contraction ratio and half-angle the "
                f"smallest L* that leaves a cylinder is {minimum:.6g} m. No input is "
                "changed to make the geometry fit.",
                "characteristic_length",
                {"converging_volume": v_conv, "chamber_volume": chamber_volume,
                 "minimum_characteristic_length": minimum})
        diagnostics.append(Diagnostic(
            "CYLINDER_ZERO_AT_BOUNDARY", Severity.INFO,
            "The converging section takes the whole chamber volume to within rounding: "
            "the cylinder has zero length and the chamber is the frustum alone.",
            "cylinder_length", {"rounding_residual": v_cyl}))
        v_cyl = 0.0

    if contraction_ratio < CONTRACTION_PRESSURE_LOSS_ADVISORY:
        diagnostics.append(Diagnostic(
            "CONTRACTION_BELOW_PRESSURE_LOSS_ADVISORY", Severity.WARNING,
            f"Ac/At {contraction_ratio:g} is below {CONTRACTION_PRESSURE_LOSS_ADVISORY:g}. "
            "Sutton §8.2: pressure losses ahead of the nozzle inlet may become appreciable "
            "when the chamber area is less than three times the throat area. The ideal "
            "sizing upstream does not include that loss. An advisory, not a limit.",
            "contraction_ratio", {"contraction_ratio": contraction_ratio}))
    low, high = TYPICAL_BIPROPELLANT_L_STAR
    if not low <= characteristic_length <= high:
        diagnostics.append(Diagnostic(
            "CHARACTERISTIC_LENGTH_OUTSIDE_TYPICAL", Severity.INFO,
            f"L* {characteristic_length:g} m is outside the {low:g}-{high:g} m Sutton §8.2 "
            "gives as typical for several bipropellants. Information only: that range is "
            "not a validity limit, and L* alone says nothing about combustion completeness "
            "or stability.",
            "characteristic_length", {"characteristic_length": characteristic_length}))

    geometry = ChamberGeometry(
        throat_area=throat_area, throat_radius=throat_radius,
        characteristic_length=characteristic_length, contraction_ratio=contraction_ratio,
        converging_half_angle=converging_half_angle,
        chamber_volume=chamber_volume, chamber_area=chamber_area,
        chamber_radius=chamber_radius, converging_length=l_conv,
        converging_volume=v_conv, cylinder_length=v_cyl / chamber_area,
        cylinder_volume=v_cyl, injector_to_throat_length=v_cyl / chamber_area + l_conv)
    status = (Status.OK_WITH_WARNINGS
              if any(d.severity is Severity.WARNING for d in diagnostics) else Status.OK)
    return Solution(value=geometry, status=status, diagnostics=tuple(diagnostics))
