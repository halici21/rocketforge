"""Flight environment (ENV-3): the point state between the atmosphere and flight.

From a resolved :class:`~rocketforge.physics.atmosphere.AtmosphereState` and
explicit conditions -- geometric altitude, air-relative speed and, for the
Reynolds number only, a characteristic length -- :func:`flight_environment`
gives local gravity, Mach number, dynamic pressure and Reynolds number, each
with its relation or the reason it is not defined.

Later trajectory and aerodynamics code consumes this state; it computes no
trajectory, wind, force, coefficient or loss itself.

Pure, Qt-free, SI.
"""

from __future__ import annotations

from .environment import (
    FLIGHT_ENVIRONMENT_SCHEMA,
    FLIGHT_ENVIRONMENT_VERSION,
    MINIMUM_GEOMETRIC_ALTITUDE,
    FlightEnvironment,
    FlightEnvironmentFormatError,
    flight_environment,
    standard_flight_environment,
)
from .gravity import (
    WGS84_GM,
    WGS84_SEMI_MAJOR_AXIS,
    WGS84_SPHERICAL,
    GravityFormatError,
    SphericalGravity,
)

__all__ = [
    "FLIGHT_ENVIRONMENT_SCHEMA",
    "FLIGHT_ENVIRONMENT_VERSION",
    "MINIMUM_GEOMETRIC_ALTITUDE",
    "WGS84_GM",
    "WGS84_SEMI_MAJOR_AXIS",
    "WGS84_SPHERICAL",
    "FlightEnvironment",
    "FlightEnvironmentFormatError",
    "GravityFormatError",
    "SphericalGravity",
    "flight_environment",
    "standard_flight_environment",
]
