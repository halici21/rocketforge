"""Spherical Earth gravity (ENV-3): g = GM / r^2, r = R + Z.

One baseline, stated with its constants: a point mass (equivalently, a
spherically symmetric Earth) of gravitational parameter GM, with altitude
measured from a sphere of reference radius R. No latitude, oblateness (J2),
Earth rotation or centrifugal term is applied.

**The constants are WGS 84's** (NGA.STND.0036_1.0.0_WGS84, 2014, Table 3.1,
the four defining parameters): GM = 3.986004418 x 10^14 m^3/s^2, the value that
includes the mass of the atmosphere, and the semi-major axis
a = 6 378 137 m as the reference radius. With these, g at Z = 0 is
9.798 m/s^2: the pure attraction at the equatorial radius.

Two values that look similar are deliberately *not* used:

* g0 = 9.80665 m/s^2 (:data:`rocketforge.core.constants.STANDARD_GRAVITY`) is a
  defined convention for weight and specific impulse, not local gravity.
* The U.S. Standard Atmosphere's r0 = 6 356 766 m is an *effective* radius
  chosen, with g0, for the Standard's own hydrostatics at 45.5425 deg latitude
  (eq. 17). It belongs to the atmosphere model and is not a radius of the
  Earth.

Real surface gravity, rotation included, runs from about 9.780 m/s^2 at the
equator to 9.832 m/s^2 at the poles. A spherical baseline is within that band's
width, not inside it at every latitude, and says so.

Pure, Qt-free, SI.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

__all__ = [
    "WGS84_GM",
    "WGS84_SEMI_MAJOR_AXIS",
    "WGS84_SPHERICAL",
    "GravityFormatError",
    "SphericalGravity",
]

#: GM, m^3/s^2, including the atmosphere (WGS 84, NGA.STND.0036_1.0.0, Table 3.1).
WGS84_GM: Final = 3.986004418e14
#: a, m: semi-major axis of the WGS 84 ellipsoid (NGA.STND.0036_1.0.0, Table 3.1).
WGS84_SEMI_MAJOR_AXIS: Final = 6378137.0


class GravityFormatError(ValueError):
    """A serialised gravity model that cannot be read as one."""


@dataclass(frozen=True, slots=True)
class SphericalGravity:
    """A spherical (point-mass) gravity model and the source of its constants.

    Attributes:
        key: Identity, for records.
        name: Human-readable name.
        gm: Gravitational parameter GM, m^3/s^2.
        reference_radius: R, m. Geometric altitude is measured from it.
        source: Where GM and R come from.
    """

    key: str
    name: str
    gm: float
    reference_radius: float
    source: str

    def __post_init__(self) -> None:
        for label, value in (("gm", self.gm), ("reference_radius", self.reference_radius)):
            if not (isinstance(value, (int, float)) and not isinstance(value, bool)
                    and math.isfinite(value) and value > 0.0):
                raise ValueError(f"{label} must be finite and above zero")

    def radius(self, geometric_altitude: float) -> float:
        """r = R + Z, m."""
        return self.reference_radius + geometric_altitude

    def acceleration(self, geometric_altitude: float) -> float:
        """g = GM / (R + Z)^2, m/s^2. The caller keeps R + Z above zero."""
        return self.gm / self.radius(geometric_altitude) ** 2

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "name": self.name, "gm_m3_s2": self.gm,
                "reference_radius_m": self.reference_radius, "source": self.source}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SphericalGravity":
        try:
            return cls(key=str(payload["key"]), name=str(payload["name"]),
                       gm=float(payload["gm_m3_s2"]),
                       reference_radius=float(payload["reference_radius_m"]),
                       source=str(payload["source"]))
        except KeyError as missing:
            raise GravityFormatError(f"gravity model lacks {missing}") from None
        except (TypeError, ValueError) as error:
            raise GravityFormatError(str(error)) from None


#: The baseline: WGS 84 GM about a sphere of the WGS 84 semi-major axis.
WGS84_SPHERICAL: Final = SphericalGravity(
    key="spherical_wgs84",
    name="Spherical Earth, WGS 84 GM and semi-major axis",
    gm=WGS84_GM,
    reference_radius=WGS84_SEMI_MAJOR_AXIS,
    source=("NGA.STND.0036_1.0.0_WGS84 (2014), Table 3.1: GM = 3.986004418e14 m^3/s^2 "
            "(atmosphere included), a = 6378137 m. No J2, latitude or rotation term."),
)
