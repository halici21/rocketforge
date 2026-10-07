"""The flight environment at one point (ENV-3).

Given a resolved :class:`~rocketforge.physics.atmosphere.AtmosphereState` and
explicit flight conditions, :func:`flight_environment` returns the local
gravity, Mach number, dynamic pressure and Reynolds number, each with its
relation, or the reason it is not defined. It is a point-state calculation:
no trajectory, wind, force, coefficient or loss is computed here.

**Inputs, each one explicit.**

* ``atmosphere`` -- the state; its model owns every gas property. Nothing
  here restates an atmosphere equation.
* ``air_speed`` -- the speed of the vehicle *relative to the local air*, m/s,
  a magnitude (>= 0). It is not an inertial or ground speed. Winds are not
  modelled; a caller that has only a ground or inertial speed and assumes
  still air must say so at its own boundary. This module cannot tell the
  difference and does not guess.
* ``geometric_altitude`` -- m above mean sea level, for gravity. A state
  resolved at an altitude carries it, and a stated altitude must equal it.
  Manual and vacuum states carry none.
* ``characteristic_length`` -- m, > 0, only for the Reynolds number.

**Relations.**

* g = GM / r^2, r = R + Z (:mod:`.gravity`, spherical WGS 84 baseline);
* M = V_air / a;
* q = rho V_air^2 / 2;
* Re = rho V_air L / mu.

**What is not defined stays undefined.** A quantity whose ingredient the
atmosphere state does not define -- a speed of sound or viscosity above
86 km in the Standard, anything but pressure in a manual state, a speed of
sound or viscosity in vacuum -- is ``None``, and ``unavailable`` carries the
atmosphere's own reason. Vacuum has zero density, so q is zero, which is
physically true; its Mach and Reynolds numbers are not defined, because there
is no gas, and zero density does not make a ratio with an undefined viscosity
zero.

Invalid input is refused (a :class:`~rocketforge.core.result.Solution` with
no value and a diagnostic naming the input); nothing is clamped.

Mean free path and Knudsen number are not given: the Standard's collision
diameter is among the known misprints of its Table 2, and a continuum
criterion is a judgement for the aerodynamics that will use it. See
``docs/engineering/design/ENV3_FLIGHT_ENVIRONMENT.md``.

Pure, Qt-free, SI.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final

from rocketforge.core.result import Diagnostic, Severity, Solution, Status
from rocketforge.physics.atmosphere import AtmosphereFormatError, AtmosphereState
from rocketforge.physics.atmosphere import standard_atmosphere as _standard_atmosphere

from .gravity import WGS84_SPHERICAL, GravityFormatError, SphericalGravity

__all__ = [
    "FLIGHT_ENVIRONMENT_SCHEMA",
    "FLIGHT_ENVIRONMENT_VERSION",
    "MINIMUM_GEOMETRIC_ALTITUDE",
    "FlightEnvironment",
    "FlightEnvironmentFormatError",
    "flight_environment",
    "standard_flight_environment",
]

FLIGHT_ENVIRONMENT_SCHEMA: Final = "rocketforge.flight-environment"
FLIGHT_ENVIRONMENT_VERSION: Final = 1

#: m. The lowest geometric altitude gravity is evaluated at. Below it is not a
#: flight condition: no atmosphere in this build reaches it (the Standard
#: starts at -5 km), and the point-mass law does not hold inside the Earth.
MINIMUM_GEOMETRIC_ALTITUDE: Final = -5000.0

#: The derived scalars, with their record keys.
QUANTITIES: Final = (
    ("radius", "radius_m"),
    ("gravity", "gravity_m_s2"),
    ("mach", "mach"),
    ("dynamic_pressure", "dynamic_pressure_Pa"),
    ("reynolds_number", "reynolds_number"),
)
_NAMES = frozenset(name for name, _key in QUANTITIES)

_NO_ALTITUDE = ("No geometric altitude is stated, and the atmosphere state "
                "({}) carries none; gravity needs one.")
_NO_LENGTH = "No characteristic length is stated; a Reynolds number needs one."
_SCOPE = ("ENV-3 point flight environment. Air-relative speed as stated; no wind, "
          "trajectory, force or loss model.")


class FlightEnvironmentFormatError(ValueError):
    """A serialised flight environment that cannot be read as one."""


@dataclass(frozen=True, slots=True)
class FlightEnvironment:
    """The flight environment at one point, and what it came from.

    Attributes:
        atmosphere: The atmosphere state every gas property is read from.
        gravity_model: The gravity model and the source of its constants.
        air_speed: Speed relative to the local air, m/s (>= 0).
        geometric_altitude: m above mean sea level, when known.
        altitude_source: ``"stated"``, ``"atmosphere"`` or ``""`` (none).
        characteristic_length: m, when stated.
        radius: r = R + Z, m.
        gravity: m/s^2.
        mach: Mach number.
        dynamic_pressure: q, Pa.
        reynolds_number: Re based on ``characteristic_length``.
        unavailable: Quantity name -> why it is not defined.
        provenance: Quantity name -> the relation and where its inputs came from.
    """

    atmosphere: AtmosphereState
    gravity_model: SphericalGravity
    air_speed: float
    geometric_altitude: float | None = None
    altitude_source: str = ""
    characteristic_length: float | None = None
    radius: float | None = None
    gravity: float | None = None
    mach: float | None = None
    dynamic_pressure: float | None = None
    reynolds_number: float | None = None
    unavailable: Mapping[str, str] = field(default_factory=dict)
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (_finite(self.air_speed) and self.air_speed >= 0.0):
            raise ValueError("air_speed must be finite and at or above zero")
        if self.characteristic_length is not None and not (
                _finite(self.characteristic_length) and self.characteristic_length > 0.0):
            raise ValueError("characteristic_length must be finite and above zero")
        if self.geometric_altitude is not None and not _finite(self.geometric_altitude):
            raise ValueError("geometric_altitude must be finite")
        if self.altitude_source not in ("stated", "atmosphere", ""):
            raise ValueError(f"unknown altitude_source {self.altitude_source!r}")
        if (self.altitude_source == "") != (self.geometric_altitude is None):
            raise ValueError("an altitude has a source, and only an altitude has one")
        for name, _key in QUANTITIES:
            value = getattr(self, name)
            if value is None:
                continue
            if not _finite(value):
                raise ValueError(f"{name} must be finite when it is defined")
            if value < 0.0 or (name in ("radius", "gravity") and value == 0.0):
                raise ValueError(f"{name} is out of its physical range")
        unknown = set(self.unavailable) - _NAMES
        if unknown:
            raise ValueError(f"unavailable names unknown quantities {sorted(unknown)}")
        for name, _key in QUANTITIES:
            if (getattr(self, name) is None) != (name in self.unavailable):
                raise ValueError(f"{name} must be either defined or unavailable, not both "
                                 "or neither")

    def to_dict(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "schema": FLIGHT_ENVIRONMENT_SCHEMA,
            "version": FLIGHT_ENVIRONMENT_VERSION,
            "air_speed_m_s": self.air_speed,
            "geometric_altitude_m": self.geometric_altitude,
            "altitude_source": self.altitude_source,
            "characteristic_length_m": self.characteristic_length,
        }
        for name, key in QUANTITIES:
            record[key] = getattr(self, name)
        record.update({
            "unavailable": dict(self.unavailable),
            "provenance": dict(self.provenance),
            "gravity_model": self.gravity_model.to_dict(),
            "atmosphere": self.atmosphere.to_dict(),
        })
        return record

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FlightEnvironment":
        if not isinstance(payload, Mapping):
            raise FlightEnvironmentFormatError("a flight environment must be a mapping")
        if payload.get("schema") != FLIGHT_ENVIRONMENT_SCHEMA:
            raise FlightEnvironmentFormatError(
                f"not a flight environment (schema {payload.get('schema')!r})")
        if payload.get("version") != FLIGHT_ENVIRONMENT_VERSION:
            raise FlightEnvironmentFormatError(
                f"flight environment version {payload.get('version')!r} is not supported")

        def number(key: str, optional: bool = True) -> float | None:
            value = payload.get(key)
            if value is None and optional:
                return None
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise FlightEnvironmentFormatError(f"{key} must be a number"
                                                   + (" or null" if optional else ""))
            return float(value)

        try:
            return cls(
                atmosphere=AtmosphereState.from_dict(payload["atmosphere"]),
                gravity_model=SphericalGravity.from_dict(payload["gravity_model"]),
                air_speed=number("air_speed_m_s", optional=False),
                geometric_altitude=number("geometric_altitude_m"),
                altitude_source=str(payload.get("altitude_source", "")),
                characteristic_length=number("characteristic_length_m"),
                unavailable={str(k): str(v) for k, v in
                             dict(payload.get("unavailable", {})).items()},
                provenance={str(k): str(v) for k, v in
                            dict(payload.get("provenance", {})).items()},
                **{name: number(key) for name, key in QUANTITIES},
            )
        except KeyError as missing:
            raise FlightEnvironmentFormatError(f"flight environment lacks {missing}") from None
        except (AtmosphereFormatError, GravityFormatError) as error:
            raise FlightEnvironmentFormatError(str(error)) from None
        except (TypeError, ValueError) as error:
            if isinstance(error, FlightEnvironmentFormatError):
                raise
            raise FlightEnvironmentFormatError(str(error)) from None


def _finite(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _refuse(code: str, message: str, field_name: str) -> Solution[FlightEnvironment]:
    return Solution(value=None, status=Status.NO_SOLUTION,
                    diagnostics=(Diagnostic(code=code, severity=Severity.ERROR,
                                            message=message, field=field_name),))


def _absent(state: AtmosphereState, name: str, what: str) -> str:
    """The atmosphere's own reason a quantity is absent, or a plain statement."""
    return state.unavailable.get(name) or f"The atmosphere state ({state.model_name}) " \
                                          f"does not define {what}."


def flight_environment(atmosphere: AtmosphereState, air_speed: float, *,
                       geometric_altitude: float | None = None,
                       characteristic_length: float | None = None,
                       gravity_model: SphericalGravity = WGS84_SPHERICAL
                       ) -> Solution[FlightEnvironment]:
    """The flight environment for an atmosphere state and explicit conditions.

    Args:
        atmosphere: A resolved atmosphere state (manual, vacuum or a model).
        air_speed: Speed relative to the local air, m/s; a magnitude, >= 0.
        geometric_altitude: m above mean sea level, for gravity. Optional when
            the state carries one, and then it must equal it.
        characteristic_length: m, > 0; only the Reynolds number uses it.
        gravity_model: The gravity model; the WGS 84 spherical baseline by default.

    Returns:
        The environment, or a refusal naming the input that failed. A quantity
        whose ingredients are not defined is ``None`` with its reason; that is
        not a refusal.
    """
    if not isinstance(atmosphere, AtmosphereState):
        return _refuse("ATMOSPHERE_INVALID", "A resolved atmosphere state is required.",
                       "atmosphere")
    if not isinstance(gravity_model, SphericalGravity):
        return _refuse("GRAVITY_MODEL_INVALID", "A spherical gravity model is required.",
                       "gravity_model")
    if not (_finite(air_speed) and air_speed >= 0.0):
        return _refuse("AIR_SPEED_INVALID",
                       "The air-relative speed must be a finite magnitude at or above zero; "
                       "direction is not part of a speed.", "air_speed")
    if characteristic_length is not None and not (
            _finite(characteristic_length) and characteristic_length > 0.0):
        return _refuse("CHARACTERISTIC_LENGTH_INVALID",
                       "The characteristic length must be finite and above zero.",
                       "characteristic_length")
    if geometric_altitude is not None and not _finite(geometric_altitude):
        return _refuse("ALTITUDE_INVALID", "The geometric altitude must be finite.",
                       "geometric_altitude")

    state_altitude = atmosphere.geometric_altitude
    if geometric_altitude is not None and state_altitude is not None \
            and float(geometric_altitude) != state_altitude:
        return _refuse("ALTITUDE_MISMATCH",
                       f"The stated geometric altitude ({float(geometric_altitude):g} m) is not "
                       f"the altitude the atmosphere state was resolved at "
                       f"({state_altitude:g} m).", "geometric_altitude")
    if geometric_altitude is not None:
        altitude, source = float(geometric_altitude), "stated"
    elif state_altitude is not None:
        altitude, source = state_altitude, "atmosphere"
    else:
        altitude, source = None, ""
    if altitude is not None and altitude < MINIMUM_GEOMETRIC_ALTITUDE:
        return _refuse("ALTITUDE_OUT_OF_RANGE",
                       f"Gravity is evaluated from {MINIMUM_GEOMETRIC_ALTITUDE:g} m geometric "
                       "altitude up; below that is not a flight condition. Nothing is "
                       "extrapolated.", "geometric_altitude")

    speed = float(air_speed)
    length = None if characteristic_length is None else float(characteristic_length)
    values: dict[str, float] = {}
    unavailable: dict[str, str] = {}
    provenance: dict[str, str] = {}
    source_name = atmosphere.model_name

    if altitude is None:
        unavailable["radius"] = unavailable["gravity"] = _NO_ALTITUDE.format(source_name)
    else:
        values["radius"] = gravity_model.radius(altitude)
        values["gravity"] = gravity_model.acceleration(altitude)
        provenance["radius"] = f"r = R + Z; R from {gravity_model.name}"
        provenance["gravity"] = f"g = GM / r^2; {gravity_model.source}"

    a = atmosphere.speed_of_sound
    if a is None:
        unavailable["mach"] = "Mach number needs a speed of sound. " + _absent(
            atmosphere, "speed_of_sound", "a speed of sound")
    else:
        values["mach"] = speed / a
        provenance["mach"] = f"M = V_air / a; a from {source_name}"

    rho = atmosphere.density
    if rho is None:
        unavailable["dynamic_pressure"] = "Dynamic pressure needs a density. " + _absent(
            atmosphere, "density", "a density")
    else:
        values["dynamic_pressure"] = 0.5 * rho * speed * speed
        provenance["dynamic_pressure"] = f"q = rho V_air^2 / 2; rho from {source_name}"

    mu = atmosphere.dynamic_viscosity
    missing = []
    if rho is None:
        missing.append(_absent(atmosphere, "density", "a density"))
    if mu is None:
        missing.append(_absent(atmosphere, "dynamic_viscosity", "a dynamic viscosity"))
    if length is None:
        missing.append(_NO_LENGTH)
    if missing:
        unavailable["reynolds_number"] = ("Reynolds number needs a density, a viscosity "
                                          "and a characteristic length. " + " ".join(missing))
    else:
        values["reynolds_number"] = rho * speed * length / mu
        provenance["reynolds_number"] = (f"Re = rho V_air L / mu; rho and mu from "
                                         f"{source_name}, L as stated")
    provenance["scope"] = _SCOPE

    return Solution(
        value=FlightEnvironment(
            atmosphere=atmosphere, gravity_model=gravity_model, air_speed=speed,
            geometric_altitude=altitude, altitude_source=source,
            characteristic_length=length, unavailable=unavailable, provenance=provenance,
            **values),
        status=Status.OK,
        inputs={"air_speed": speed}
        | ({} if geometric_altitude is None else {"geometric_altitude": float(geometric_altitude)})
        | ({} if length is None else {"characteristic_length": length}),
    )


def standard_flight_environment(model: str, geometric_altitude: float, air_speed: float, *,
                                characteristic_length: float | None = None,
                                gravity_model: SphericalGravity = WGS84_SPHERICAL
                                ) -> Solution[FlightEnvironment]:
    """The flight environment at a geometric altitude in a named atmosphere model.

    Resolves the atmosphere, then :func:`flight_environment` with the same
    altitude. An atmosphere refusal (unknown model, altitude out of range) is
    returned as it is.
    """
    resolved = _standard_atmosphere(model, geometric_altitude)
    if resolved.value is None:
        return Solution(value=None, status=resolved.status, diagnostics=resolved.diagnostics)
    return flight_environment(resolved.value, air_speed,
                              geometric_altitude=geometric_altitude,
                              characteristic_length=characteristic_length,
                              gravity_model=gravity_model)
