"""Design environment -> resolved atmosphere (ENV-1). Qt-free.

The one place a LIQ-2 :class:`DesignEnvironment` becomes an
:class:`AtmosphereState` and an ambient pressure. The requirement records
intent (a manual pressure, vacuum, sea level, or an altitude in a named model)
and computes nothing; the physics is :mod:`rocketforge.physics.atmosphere`. This
module only connects them. It reaches no provider and solves nothing; resolving
an altitude is a handful of closed-form expressions.

Named pressures stay named: vacuum, sea level and a custom pressure return
their pressure directly, without calling the atmosphere package, exactly as
before ENV-1. Only an altitude is resolved through a model.
"""

from __future__ import annotations

import math
from typing import Any

from rocketforge.core.result import Solution
from rocketforge.engine.requirement import (
    STANDARD_SEA_LEVEL_PRESSURE,
    AmbientMode,
    ChamberPressureMode,
    DesignEnvironment,
    EngineRequirement,
    RequirementIssue,
)
from rocketforge.physics import atmosphere
from rocketforge.physics.atmosphere import AtmosphereState

__all__ = [
    "ambient_pressure",
    "environment_issues",
    "model_options",
    "resolve",
    "state_rows",
]


def resolve(environment: DesignEnvironment) -> Solution[AtmosphereState]:
    """The resolved atmosphere for an environment, or why there is none."""
    if environment.mode is AmbientMode.VACUUM:
        return atmosphere.vacuum_atmosphere()
    if environment.mode is AmbientMode.SEA_LEVEL:
        return atmosphere.manual_atmosphere(STANDARD_SEA_LEVEL_PRESSURE,
                                            "Standard sea-level pressure")
    if environment.mode is AmbientMode.CUSTOM:
        return atmosphere.manual_atmosphere(environment.custom_pressure)
    if environment.altitude is None:
        return atmosphere.state.refuse("ALTITUDE_MISSING", "State the design altitude.",
                                       "altitude")
    return atmosphere.standard_atmosphere(environment.atmosphere_model, environment.altitude)


def ambient_pressure(environment: DesignEnvironment) -> float:
    """The design ambient pressure, Pa; NaN when an altitude does not resolve.

    Named pressures are returned as the requirement states them, without the
    atmosphere package: their numbers are unchanged by ENV-1. An unresolved
    altitude is reported by :func:`environment_issues`, which stops every
    downstream stage before it reads this.
    """
    if not environment.is_altitude:
        return environment.ambient_pressure
    resolved = resolve(environment).value
    return math.nan if resolved is None else resolved.pressure


def environment_issues(requirement: EngineRequirement) -> list[RequirementIssue]:
    """The checks that need the resolved altitude: model range, and the
    chamber pressure against the resolved ambient. The requirement checks the
    rest (stated, finite) and these are not repeated for a missing altitude."""
    environment = requirement.environment
    if not environment.is_altitude or environment.altitude is None \
            or not math.isfinite(environment.altitude) \
            or not environment.atmosphere_model.strip():
        return []
    resolved = resolve(environment)
    if resolved.value is None:
        diagnostic = resolved.diagnostics[0]
        return [RequirementIssue(diagnostic.code, "environment", diagnostic.message)]
    chamber = requirement.chamber_pressure
    if (chamber.mode is not ChamberPressureMode.AUTO and chamber.value is not None
            and math.isfinite(chamber.value) and chamber.value > 0.0
            and chamber.value <= resolved.value.pressure):
        word = "target" if chamber.mode is ChamberPressureMode.TARGET else "limit"
        return [RequirementIssue(
            "CHAMBER_PRESSURE_NOT_ABOVE_AMBIENT", "chamber_pressure",
            f"The chamber-pressure {word} is not above the design ambient pressure; "
            "a chamber at or below ambient cannot expel its flow.")]
    return []


def model_options() -> list[dict[str, Any]]:
    """The atmosphere models an altitude can be read in, with their ranges."""
    return [{"key": key, "label": name, "minimum": low, "maximum": high}
            for key, (name, (low, high)) in atmosphere.ATMOSPHERE_MODELS.items()]


#: Display unit, scale and format per state quantity.
_ROWS = (
    ("geometric_altitude", "Geometric altitude Z", "m", 1.0, ",.1f"),
    ("geopotential_altitude", "Geopotential altitude H", "m'", 1.0, ",.1f"),
    ("pressure", "Static pressure", "kPa", 1.0e-3, ",.6g"),
    ("temperature", "Temperature", "K", 1.0, ",.3f"),
    ("density", "Density", "kg/m³", 1.0, ".5g"),
    ("number_density", "Number density", "m⁻³", 1.0, ".5g"),
    ("mean_molar_mass", "Mean molar mass", "kg/kmol", 1.0, ".6g"),
    ("speed_of_sound", "Speed of sound", "m/s", 1.0, ",.2f"),
    ("dynamic_viscosity", "Dynamic viscosity", "Pa·s", 1.0, ".5g"),
)


def state_rows(state: AtmosphereState) -> list[dict[str, str]]:
    """The quantities of a state, as display rows. One the source does not
    define is shown as "not defined" with the source's reason, never as a
    number; one it simply does not carry is left out."""
    rows = []
    for key, label, unit, scale, spec in _ROWS:
        value = getattr(state, key)
        if value is not None:
            rows.append({"key": key, "label": label, "unit": unit, "reason": "",
                         "value": format(value * scale, spec)})
        elif key in state.unavailable:
            rows.append({"key": key, "label": label, "unit": "", "value": "not defined",
                         "reason": state.unavailable[key]})
    if state.layer is not None:
        rows.append({"key": "layer", "label": "Layer (Tables 4, 5)", "unit": "",
                     "value": str(state.layer), "reason": ""})
    return rows
