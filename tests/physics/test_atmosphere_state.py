"""ENV-1: the atmosphere state contract, manual and vacuum semantics, records."""

from __future__ import annotations

import ast
import json
import math
import pathlib
from dataclasses import replace

import pytest

from rocketforge.core.result import Status
from rocketforge.physics import atmosphere
from rocketforge.physics.atmosphere import (
    ATMOSPHERE_MODELS,
    AtmosphereFormatError,
    AtmosphereState,
    manual_atmosphere,
    standard_atmosphere,
    ussa1976,
    vacuum_atmosphere,
)

PACKAGE = pathlib.Path(atmosphere.__file__).parent


def test_manual_keeps_the_pressure_and_invents_nothing():
    s = manual_atmosphere(26500.0).value
    assert s.model == "manual" and s.pressure == 26500.0 and s.model_version == ""
    for name in ("temperature", "density", "speed_of_sound", "dynamic_viscosity",
                 "geometric_altitude", "geopotential_altitude", "layer"):
        assert getattr(s, name) is None, name
    assert "no atmosphere model" in s.provenance.lower()
    assert manual_atmosphere(0.0).value.pressure == 0.0              # zero is allowed
    assert manual_atmosphere(101325.0, "Standard sea-level pressure").value.model == "manual"


@pytest.mark.parametrize("bad", [-1.0, math.nan, math.inf, -math.inf, None, "1", True])
def test_manual_refuses_what_is_not_a_pressure(bad):
    solution = manual_atmosphere(bad)
    assert solution.value is None and solution.status is Status.NO_SOLUTION
    assert solution.diagnostics[0].code == "AMBIENT_PRESSURE_INVALID"


def test_vacuum_is_explicit_not_a_high_altitude():
    s = vacuum_atmosphere().value
    assert s.is_vacuum and s.model == "vacuum"
    assert s.pressure == 0.0 and s.density == 0.0
    assert s.temperature is None and s.speed_of_sound is None and s.dynamic_viscosity is None
    assert s.geometric_altitude is None
    assert not ussa1976.state(80000.0).value.is_vacuum


def test_models_are_named_with_their_ranges():
    assert ATMOSPHERE_MODELS["ussa1976"] == ("U.S. Standard Atmosphere, 1976",
                                             (-5000.0, 1000000.0))
    assert standard_atmosphere("ussa1976", 1000.0).value == ussa1976.state(1000.0).value
    unknown = standard_atmosphere("nrlmsise00", 1000.0)
    assert unknown.value is None and unknown.diagnostics[0].code == "ATMOSPHERE_MODEL_UNKNOWN"


def test_unavailable_reasons_are_consistent():
    upper = ussa1976.state(300000.0).value
    assert upper.speed_of_sound is None and "speed_of_sound" in upper.unavailable
    with pytest.raises(ValueError, match="both defined and marked unavailable"):
        replace(upper, speed_of_sound=300.0)
    with pytest.raises(ValueError, match="unknown quantities"):
        replace(upper, unavailable={"wind_speed": "no"})
    with pytest.raises(ValueError):
        replace(upper, species_number_densities={"N2": -1.0})
    manual = manual_atmosphere(101325.0).value
    assert set(manual.unavailable) == {"temperature", "density", "speed_of_sound",
                                       "dynamic_viscosity"}


def test_a_version_1_record_still_reads():
    legacy = {"schema": "rocketforge.atmosphere-state", "version": 1, "model": "manual",
              "model_name": "Manual ambient pressure", "model_version": "",
              "pressure_Pa": 26500.0, "geometric_altitude_m": None,
              "geopotential_altitude_m": None, "temperature_K": None, "density_kg_m3": None,
              "speed_of_sound_m_s": None, "dynamic_viscosity_Pa_s": None, "layer": None,
              "inputs": {"pressure": 26500.0}, "provenance": "Stated directly."}
    state = AtmosphereState.from_dict(legacy)
    assert state.pressure == 26500.0 and state.species_number_densities == {}
    assert state.to_dict()["version"] == 2


def test_a_state_refuses_non_finite_or_negative_values():
    good = ussa1976.state(1000.0).value
    with pytest.raises(ValueError):
        replace(good, pressure=None)
    with pytest.raises(ValueError):
        replace(good, pressure=-1.0)
    with pytest.raises(ValueError):
        replace(good, pressure=math.nan)
    with pytest.raises(ValueError):
        replace(good, temperature=math.inf)


@pytest.mark.parametrize("state", [
    ussa1976.state(12345.6).value, ussa1976.state_at_geopotential(60000.0).value,
    ussa1976.state(83000.0).value, ussa1976.state(450000.0).value,
    manual_atmosphere(26500.0).value, vacuum_atmosphere().value])
def test_a_state_round_trips_with_its_identity_and_provenance(state):
    text = json.dumps(state.to_dict(), allow_nan=False)
    back = AtmosphereState.from_dict(json.loads(text))
    assert back == state
    assert json.dumps(back.to_dict(), allow_nan=False) == text
    payload = json.loads(text)
    assert payload["model"] == state.model and payload["model_version"] == state.model_version
    assert payload["provenance"] == state.provenance


def test_a_foreign_or_broken_state_record_is_refused():
    payload = ussa1976.state(1000.0).value.to_dict()
    for broken in ({**payload, "schema": "x"}, {**payload, "version": 3},
                   {k: v for k, v in payload.items() if k != "pressure_Pa"},
                   {**payload, "pressure_Pa": -5.0}, [], "text"):
        with pytest.raises(AtmosphereFormatError):
            AtmosphereState.from_dict(broken)


def test_the_package_is_pure_and_reaches_no_engine():
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [("." * node.level) + (node.module or "")]
            for name in names:
                assert not name.startswith(("PySide6", "rocketforge.engine",
                                            "rocketforge.engineering",
                                            "rocketforge.application",
                                            "rocketforge.providers", "requests",
                                            "urllib", "http", "socket")), (path.name, name)
                if name.startswith("rocketforge"):
                    assert name.startswith(("rocketforge.core", "rocketforge.physics")), name
