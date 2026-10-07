"""The resolved atmosphere: one state, whatever produced it.

An :class:`AtmosphereState` is what a consumer reads -- a nozzle design point,
and later a trajectory or an orbit -- and it says where it came from. The
sources in this build:

* **Manual** -- an explicitly supplied ambient pressure and nothing else.
* **Vacuum** -- zero pressure and zero density, stated as vacuum rather than
  reached through some high altitude.
* **The U.S. Standard Atmosphere, 1976** (:mod:`.ussa1976`) -- a deterministic
  reference atmosphere from -5 km to 1000 km.

An empirical, time- and space-weather-dependent model (NRLMSIS 2.1, ENV-2) is
deferred: NRL licenses it for academic, non-commercial use only, which an MIT
distribution cannot carry.

**A quantity a source does not define is absent, and says why.** Every
optional field is ``None`` unless the source defines it, and ``unavailable``
maps each field that is ``None`` *for a scientific reason* to that reason (for
example, the Standard does not define a speed of sound above 86 km). Nothing
is filled in to make sources look alike. Pressure is always defined.

Resolution returns a :class:`~rocketforge.core.result.Solution`: a refusal
carries no state and a diagnostic that names the input that failed. Nothing is
clamped.

SI units, except where the Standard's own unit is kept and named: mean molar
mass in kg/kmol (numerically g/mol).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final

from rocketforge.core.result import Diagnostic, Severity, Solution, Status

__all__ = [
    "ATMOSPHERE_STATE_SCHEMA",
    "ATMOSPHERE_STATE_VERSION",
    "AtmosphereFormatError",
    "AtmosphereState",
    "MANUAL",
    "OPTIONAL_QUANTITIES",
    "VACUUM",
    "manual_atmosphere",
    "vacuum_atmosphere",
]

ATMOSPHERE_STATE_SCHEMA: Final = "rocketforge.atmosphere-state"
#: 2 adds composition, number density, mean molar mass, molecular-scale
#: temperature, regime and the ``unavailable`` reasons (ENV-1B). Version 1
#: records still read.
ATMOSPHERE_STATE_VERSION: Final = 2

#: Model identities of the two sources that are not atmosphere models.
MANUAL: Final = "manual"
VACUUM: Final = "vacuum"

#: The optional scalar quantities, with their record keys. Pressure is listed
#: with them for its record key and checks, but every state defines it.
OPTIONAL_QUANTITIES: Final = (
    ("pressure", "pressure_Pa"),
    ("geometric_altitude", "geometric_altitude_m"),
    ("geopotential_altitude", "geopotential_altitude_m"),
    ("temperature", "temperature_K"),
    ("molecular_scale_temperature", "molecular_scale_temperature_K"),
    ("density", "density_kg_m3"),
    ("number_density", "number_density_m3"),
    ("mean_molar_mass", "mean_molar_mass_kg_kmol"),
    ("speed_of_sound", "speed_of_sound_m_s"),
    ("dynamic_viscosity", "dynamic_viscosity_Pa_s"),
)
_NAMES = frozenset(name for name, _key in OPTIONAL_QUANTITIES) | {"species_number_densities"}
_NON_NEGATIVE = ("pressure", "density", "number_density")
_POSITIVE = ("temperature", "molecular_scale_temperature", "mean_molar_mass",
             "speed_of_sound", "dynamic_viscosity")


class AtmosphereFormatError(ValueError):
    """A serialised atmosphere state that cannot be read as one."""


@dataclass(frozen=True, slots=True)
class AtmosphereState:
    """The ambient atmosphere at one point, and what it came from.

    Attributes:
        model: Identity: ``"manual"``, ``"vacuum"`` or ``"ussa1976"``.
        model_name: Human-readable name of the source.
        model_version: The model's version or edition; empty when not a model.
        pressure: Static pressure, Pa. Always defined.
        geometric_altitude: m above mean sea level, when an altitude was an input.
        geopotential_altitude: m' (standard geopotential metres), when the model
            uses one.
        temperature: Kinetic (neutral) temperature, K.
        molecular_scale_temperature: TM = T M0 / M, K (U.S. Standard Atmosphere).
        density: Total mass density, kg/m^3.
        number_density: Total number density of the species counted, m^-3.
        mean_molar_mass: Mean molecular weight, kg/kmol.
        species_number_densities: Number density per species, m^-3, keyed by
            formula ("N2", "O", "O2", "Ar", "He", "H").
        speed_of_sound: m/s, when defined.
        dynamic_viscosity: Pa s, when defined.
        layer: The model's layer or segment index (USSA 1976 Tables 4 and 5).
        regime: Which of a model's formulations produced the state.
        unavailable: Field name -> why the source does not define it.
        inputs: What the state was resolved from (JSON values).
        provenance: Where the numbers come from, as text.
    """

    model: str
    model_name: str
    model_version: str
    pressure: float
    geometric_altitude: float | None = None
    geopotential_altitude: float | None = None
    temperature: float | None = None
    density: float | None = None
    speed_of_sound: float | None = None
    dynamic_viscosity: float | None = None
    layer: int | None = None
    inputs: Mapping[str, Any] = field(default_factory=dict)
    provenance: str = ""
    molecular_scale_temperature: float | None = None
    number_density: float | None = None
    mean_molar_mass: float | None = None
    species_number_densities: Mapping[str, float] = field(default_factory=dict)
    regime: str = ""
    unavailable: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.pressure is None:
            raise ValueError("an atmosphere state always has a pressure")
        for name, _key in OPTIONAL_QUANTITIES:
            value = getattr(self, name)
            if value is None:
                continue
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite when it is defined")
            if name in _NON_NEGATIVE and value < 0.0:
                raise ValueError(f"{name} must be at or above zero")
            if name in _POSITIVE and value <= 0.0:
                raise ValueError(f"{name} must be above zero")
        for species, value in self.species_number_densities.items():
            if not (isinstance(value, (int, float)) and math.isfinite(value) and value >= 0.0):
                raise ValueError(f"the number density of {species} must be finite and >= 0")
        unknown = set(self.unavailable) - _NAMES
        if unknown:
            raise ValueError(f"unavailable names unknown quantities {sorted(unknown)}")
        for name in self.unavailable:
            value = getattr(self, name)
            defined = bool(value) if name == "species_number_densities" else value is not None
            if defined:
                raise ValueError(f"{name} is both defined and marked unavailable")

    @property
    def is_vacuum(self) -> bool:
        return self.model == VACUUM

    def to_dict(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "schema": ATMOSPHERE_STATE_SCHEMA,
            "version": ATMOSPHERE_STATE_VERSION,
            "model": self.model, "model_name": self.model_name,
            "model_version": self.model_version,
        }
        for name, key in OPTIONAL_QUANTITIES:
            record[key] = getattr(self, name)
        record.update({
            "species_number_densities_m3": dict(self.species_number_densities),
            "layer": self.layer,
            "regime": self.regime,
            "unavailable": dict(self.unavailable),
            "inputs": dict(self.inputs),
            "provenance": self.provenance,
        })
        return record

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AtmosphereState":
        if not isinstance(payload, Mapping):
            raise AtmosphereFormatError("an atmosphere state must be a mapping")
        if payload.get("schema") != ATMOSPHERE_STATE_SCHEMA:
            raise AtmosphereFormatError(
                f"not an atmosphere state (schema {payload.get('schema')!r})")
        version = payload.get("version")
        if version not in (1, ATMOSPHERE_STATE_VERSION):
            raise AtmosphereFormatError(f"atmosphere state version {version!r} is not supported")
        if "pressure_Pa" not in payload:
            raise AtmosphereFormatError("atmosphere state lacks 'pressure_Pa'")

        def optional(key: str) -> float | None:
            value = payload.get(key)
            if value is not None and (isinstance(value, bool)
                                      or not isinstance(value, (int, float))):
                raise AtmosphereFormatError(f"{key} must be a number or null")
            return None if value is None else float(value)

        try:
            layer = payload.get("layer")
            scalars = {name: optional(key) for name, key in OPTIONAL_QUANTITIES}
            if scalars["pressure"] is None:
                raise AtmosphereFormatError("an atmosphere state always has a pressure")
            return cls(
                model=str(payload["model"]), model_name=str(payload["model_name"]),
                model_version=str(payload["model_version"]),
                layer=None if layer is None else int(layer),
                species_number_densities={
                    str(k): float(v) for k, v in
                    dict(payload.get("species_number_densities_m3", {})).items()},
                regime=str(payload.get("regime", "")),
                unavailable={str(k): str(v) for k, v in
                             dict(payload.get("unavailable", {})).items()},
                inputs=dict(payload.get("inputs", {})),
                provenance=str(payload.get("provenance", "")),
                **scalars,
            )
        except KeyError as missing:
            raise AtmosphereFormatError(f"atmosphere state lacks {missing}") from None
        except (TypeError, ValueError) as error:
            if isinstance(error, AtmosphereFormatError):
                raise
            raise AtmosphereFormatError(str(error)) from None


def refuse(code: str, message: str, field: str,
           detail: Mapping[str, float] | None = None) -> Solution[AtmosphereState]:
    """A refusal: no state, one diagnostic naming the input that failed."""
    return Solution(value=None, status=Status.NO_SOLUTION,
                    diagnostics=(Diagnostic(code=code, severity=Severity.ERROR,
                                            message=message, field=field,
                                            detail=dict(detail) if detail else None),))


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


_NOT_AN_ATMOSPHERE = "A manual ambient pressure is a pressure only; it defines no {}."


def manual_atmosphere(pressure: float, label: str = "Manual ambient pressure"
                      ) -> Solution[AtmosphereState]:
    """An explicitly supplied ambient pressure, and nothing more.

    ``label`` names the pressure (for example the standard sea-level value). It
    does not make the state a standard atmosphere: no temperature, density,
    speed of sound or viscosity is attached.
    """
    if not (is_number(pressure) and math.isfinite(pressure) and pressure >= 0.0):
        return refuse("AMBIENT_PRESSURE_INVALID",
                      "A manual ambient pressure must be finite and at or above zero.",
                      "pressure")
    return Solution(
        value=AtmosphereState(
            model=MANUAL, model_name=label, model_version="", pressure=float(pressure),
            inputs={"pressure": float(pressure)},
            provenance="Stated directly; no atmosphere model is used.",
            unavailable={name: _NOT_AN_ATMOSPHERE.format(name.replace("_", " "))
                         for name in ("temperature", "density", "speed_of_sound",
                                      "dynamic_viscosity")}),
        status=Status.OK)


def vacuum_atmosphere() -> Solution[AtmosphereState]:
    """Vacuum, stated as such: zero pressure, zero density."""
    reason = "Not defined for vacuum: there is no gas."
    return Solution(
        value=AtmosphereState(
            model=VACUUM, model_name="Vacuum", model_version="", pressure=0.0, density=0.0,
            number_density=0.0,
            provenance="Stated vacuum; not a high altitude of any model.",
            unavailable={name: reason for name in ("temperature", "speed_of_sound",
                                                   "dynamic_viscosity",
                                                   "mean_molar_mass")}),
        status=Status.OK)
