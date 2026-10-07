"""Atmosphere (ENV-1): one resolved-state contract and the models behind it.

A consumer asks for an :class:`AtmosphereState` from an explicit source --
a manual pressure, vacuum, or a named standard model at an altitude -- and
reads the pressure (and, where the source defines them, temperature, density,
speed of sound and viscosity). Engine, trajectory or flight code consumes the
state; it does not reimplement any of this.

Models in this build:

* ``"ussa1976"`` -- U.S. Standard Atmosphere, 1976, -5 km to 1000 km geometric.

Pure, Qt-free, SI.
"""

from __future__ import annotations

from typing import Final

from rocketforge.core.result import Solution

from . import ussa1976
from .state import (
    ATMOSPHERE_STATE_SCHEMA,
    MANUAL,
    VACUUM,
    AtmosphereFormatError,
    AtmosphereState,
    manual_atmosphere,
    refuse,
    vacuum_atmosphere,
)

__all__ = [
    "ATMOSPHERE_MODELS",
    "ATMOSPHERE_STATE_SCHEMA",
    "MANUAL",
    "VACUUM",
    "AtmosphereFormatError",
    "AtmosphereState",
    "manual_atmosphere",
    "standard_atmosphere",
    "ussa1976",
    "vacuum_atmosphere",
]

#: Standard atmosphere models by key: (name, geometric altitude range in m).
ATMOSPHERE_MODELS: Final = {
    ussa1976.MODEL: (ussa1976.MODEL_NAME, ussa1976.GEOMETRIC_ALTITUDE_RANGE),
}


def standard_atmosphere(model: str, geometric_altitude: float) -> Solution[AtmosphereState]:
    """The named model's state at a geometric altitude (m), or its refusal."""
    if model == ussa1976.MODEL:
        return ussa1976.state(geometric_altitude)
    return refuse("ATMOSPHERE_MODEL_UNKNOWN",
                  f"No atmosphere model {model!r} exists in this build.", "model")
