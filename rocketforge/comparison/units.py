"""Unit conversion for reference values, to the units RocketForge reports.

References arrive in whatever units their source printed -- NASA's shipped
examples print c* in ft/s for one case and m/s for another, pressure in atm
or bar, energy in cal/g. Every factor here is **exact by definition**, not
measured, so a conversion can never be the source of a difference a
comparison reports.

Deliberately absent: any conversion between a mole basis and a mass basis.
That needs a composition, and doing it silently inside a comparison would let
a mole fraction be compared with a mass fraction. Basis is part of a
quantity's key instead (``mole_fraction:H2`` is a different quantity from
``mass_fraction:H2``).
"""

from __future__ import annotations

from rocketforge.core.errors import InputError

__all__ = ["CANONICAL_UNIT", "to_canonical", "UnitError"]


class UnitError(InputError):
    """A unit this module does not know, or one for the wrong dimension."""


#: dimension -> the unit RocketForge reports it in.
CANONICAL_UNIT = {
    "temperature": "K",
    "pressure": "Pa",
    "velocity": "m/s",
    "molar_mass": "kg/kmol",
    "specific_energy": "J/kg",
    "specific_entropy": "J/(kg*K)",
    "density": "kg/m^3",
    "dimensionless": "1",
}

#: unit -> (dimension, factor to the canonical unit). Sources of the exact
#: values: the international foot (0.3048 m, 1959); the standard atmosphere
#: (101325 Pa); the avoirdupois pound and standard gravity defining psi; the
#: thermochemical calorie (4.184 J), which is the one NASA CEA uses.
_FACTORS: dict[str, tuple[str, float]] = {
    "K": ("temperature", 1.0),
    "Pa": ("pressure", 1.0),
    "kPa": ("pressure", 1.0e3),
    "MPa": ("pressure", 1.0e6),
    "bar": ("pressure", 1.0e5),
    "atm": ("pressure", 101325.0),
    "psia": ("pressure", 0.45359237 * 9.80665 / 0.0254 ** 2),
    "m/s": ("velocity", 1.0),
    "ft/s": ("velocity", 0.3048),
    "kg/kmol": ("molar_mass", 1.0),
    "g/mol": ("molar_mass", 1.0),
    "kg/mol": ("molar_mass", 1.0e3),
    "J/kg": ("specific_energy", 1.0),
    "kJ/kg": ("specific_energy", 1.0e3),
    "cal/g": ("specific_energy", 4184.0),
    "J/(kg*K)": ("specific_entropy", 1.0),
    "kJ/(kg*K)": ("specific_entropy", 1.0e3),
    "cal/(g*K)": ("specific_entropy", 4184.0),
    "kg/m^3": ("density", 1.0),
    "g/cm^3": ("density", 1.0e3),
    "1": ("dimensionless", 1.0),
}


def to_canonical(value: float, unit: str) -> tuple[float, str, str]:
    """``(value in the canonical unit, canonical unit, dimension)``."""
    try:
        dimension, factor = _FACTORS[unit]
    except KeyError:
        raise UnitError(
            f"unknown unit {unit!r}; known units are {sorted(_FACTORS)}. "
            "Refused rather than guessed.") from None
    return float(value) * factor, CANONICAL_UNIT[dimension], dimension
