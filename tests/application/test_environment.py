"""ENV-1 in LIQ-2 and downstream: altitude as a source of ambient pressure.

* **Compatibility.** A requirement without an altitude writes the same record,
  byte for byte, that it wrote before ENV-1, so its fingerprint is unchanged,
  and the record of an earlier build reads back as it was.
* **Ownership.** The requirement records intent and computes nothing; its
  module still imports only the standard library. The application layer's
  ``environment_service`` resolves an altitude through
  ``physics.atmosphere``, and LIQ-3/4 read the pressure through it.
* **Parity.** An altitude, and a manual ambient pressure equal to what that
  altitude resolves to, give identical trade, sizing and chamber-geometry
  numbers.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import pathlib
from dataclasses import replace

import pytest

from rocketforge.application.analysis import chamber_geometry_service as geometry_service
from rocketforge.application.analysis import chamber_sizing_service as sizing_service
from rocketforge.application.analysis import engine_requirement_service as requirement_service
from rocketforge.application.analysis import environment_service
from rocketforge.application.analysis import propellant_trade_service as trade_service
from rocketforge.application.analysis import thermochemistry_provider as gateway_module
from rocketforge.application.analysis.engine_requirement_controller import (
    EngineRequirementController,
)
from rocketforge.engine.propellant_trade import PerformanceBasis
from rocketforge.engine.requirement import (
    DEFAULT_ATMOSPHERE_MODEL,
    AmbientMode,
    AmbientNotResolvedHere,
    ChamberPressureMode,
    ChamberPressurePreference,
    DesignEnvironment,
    EngineRequirement,
    validate_requirement,
)
from rocketforge.physics import atmosphere
from rocketforge.physics.atmosphere import ussa1976

ROOT = pathlib.Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "rocketforge" / "application" / "analysis"
BASE = EngineRequirement(thrust=1.0e6, burn_time=200.0)
ALTITUDE = DesignEnvironment(AmbientMode.STANDARD_ATMOSPHERE, altitude=10000.0)
IDEAL = trade_service.TradeSettings(
    chamber_pressure=10e6, mixture_ratio_mode="catalogue",
    performance_basis=PerformanceBasis.IDEAL_AREA_RATIO, area_ratio=40.0)

_STATUS = gateway_module.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable, reason=f"NASA CEA provider unavailable ({_STATUS.status})")


def codes(requirement):
    return [i.code for i in requirement_service.requirement_issues(requirement)]


# ===========================================================================
# compatibility
# ===========================================================================

#: The record EngineRequirement(thrust=1e6, burn_time=200) wrote before ENV-1,
#: written out by hand from the LIQ-2 schema.
PRE_ENV1 = {
    "schema": "rocketforge.liquid-engine-requirement", "version": 1, "name": "",
    "thrust_N": 1000000.0,
    "environment": {"mode": "sea_level", "custom_pressure_Pa": 101325.0},
    "burn_time_s": 200.0,
    "propellant": {"mode": "auto", "pair_key": ""},
    "chamber_pressure": {"mode": "auto", "value_Pa": None},
    "mixture_ratio": {"mode": "auto", "value": None},
    "feed": "auto", "cycle": None, "priority": "unstated",
}


def test_a_requirement_without_altitude_writes_the_pre_env1_record():
    assert BASE.to_dict() == PRE_ENV1
    canonical = {k: v for k, v in PRE_ENV1.items() if k != "name"}
    expected = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False).encode("utf-8")).hexdigest()
    assert BASE.fingerprint == expected
    for mode in (AmbientMode.VACUUM, AmbientMode.CUSTOM, AmbientMode.SEA_LEVEL):
        env = BASE.replace(environment=DesignEnvironment(mode, 26500.0)).to_dict()["environment"]
        assert set(env) == {"mode", "custom_pressure_Pa"}


def test_a_pre_env1_record_reads_back_unchanged():
    loaded = EngineRequirement.from_dict(PRE_ENV1)
    assert loaded == BASE and loaded.environment.altitude is None
    assert loaded.environment.atmosphere_model == DEFAULT_ATMOSPHERE_MODEL == ussa1976.MODEL


def test_an_altitude_requirement_round_trips_with_its_model():
    requirement = BASE.replace(environment=ALTITUDE)
    record = requirement.to_dict()["environment"]
    assert record == {"mode": "standard_atmosphere", "custom_pressure_Pa": 101325.0,
                      "altitude_m": 10000.0, "atmosphere_model": "ussa1976"}
    assert EngineRequirement.from_json(requirement.to_json()) == requirement
    kept = requirement.replace(environment=replace(ALTITUDE, mode=AmbientMode.VACUUM))
    assert kept.to_dict()["environment"]["altitude_m"] == 10000.0          # kept, as typed
    assert EngineRequirement.from_json(kept.to_json()) == kept


def test_named_pressures_are_unchanged_and_reach_no_physics(monkeypatch):
    def forbidden(*_a, **_k):
        raise AssertionError("a named pressure reached the atmosphere package")

    for name in ("manual_atmosphere", "vacuum_atmosphere", "standard_atmosphere"):
        monkeypatch.setattr(atmosphere, name, forbidden)
    monkeypatch.setattr(ussa1976, "state", forbidden)
    for env, pressure in ((DesignEnvironment(AmbientMode.VACUUM), 0.0),
                          (DesignEnvironment(AmbientMode.SEA_LEVEL), 101325.0),
                          (DesignEnvironment(AmbientMode.CUSTOM, 26500.0), 26500.0)):
        assert env.ambient_pressure == pressure
        assert environment_service.ambient_pressure(env) == pressure
        assert codes(BASE.replace(environment=env)) == []


# ===========================================================================
# ownership: intent in the requirement, resolution in the application layer
# ===========================================================================


def test_the_requirement_does_not_resolve_an_altitude():
    with pytest.raises(AmbientNotResolvedHere):
        _ = ALTITUDE.ambient_pressure
    assert validate_requirement(BASE.replace(environment=ALTITUDE)) == ()


def test_the_resolver_is_the_atmosphere_package():
    state = environment_service.resolve(ALTITUDE).value
    assert state == ussa1976.state(10000.0).value
    assert environment_service.ambient_pressure(ALTITUDE) == state.pressure
    assert environment_service.resolve(DesignEnvironment(AmbientMode.VACUUM)).value.is_vacuum
    sea = environment_service.resolve(DesignEnvironment(AmbientMode.SEA_LEVEL)).value
    assert sea.model == "manual" and sea.temperature is None and sea.pressure == 101325.0


def test_altitude_issues():
    def at(**changes):
        return BASE.replace(environment=replace(ALTITUDE, **changes))

    assert codes(at(altitude=None)) == ["ALTITUDE_MISSING"]
    assert codes(at(altitude=math.nan)) == ["ALTITUDE_INVALID"]
    assert codes(at(altitude=math.inf)) == ["ALTITUDE_INVALID"]
    assert codes(at(altitude=1000000.1)) == ["ALTITUDE_OUT_OF_RANGE"]
    assert codes(at(altitude=-5000.1)) == ["ALTITUDE_OUT_OF_RANGE"]
    assert codes(at(atmosphere_model="msis")) == ["ATMOSPHERE_MODEL_UNKNOWN"]
    assert codes(at(atmosphere_model=" ")) == ["ATMOSPHERE_MODEL_MISSING"]
    assert codes(at(altitude=1000000.0)) == [] and codes(at(altitude=-5000.0)) == []
    assert codes(at(altitude=90000.0)) == []                         # ENV-1B: upper Standard
    for bad in (at(altitude=None), at(altitude=1.1e6)):
        assert math.isnan(environment_service.ambient_pressure(bad.environment))


def test_the_chamber_is_checked_against_the_resolved_ambient():
    """At Z = -5 km the ambient is 177.8 kPa: a 0.15 MPa chamber is below it."""
    low = BASE.replace(environment=replace(ALTITUDE, altitude=-5000.0),
                       chamber_pressure=ChamberPressurePreference(ChamberPressureMode.TARGET,
                                                                 150e3))
    assert codes(low) == ["CHAMBER_PRESSURE_NOT_ABOVE_AMBIENT"]
    assert codes(low.replace(environment=replace(ALTITUDE, altitude=1000.0))) == []


def test_the_summary_shows_the_altitude_and_its_pressure():
    rows = {r["key"]: r["value"] for r in
            requirement_service.summary_rows(BASE.replace(environment=ALTITUDE))}
    assert "Z = 10 km" in rows["environment"] and "p_a = 26.4999 kPa" in rows["environment"]


def _imports(path):
    """(rocketforge/absolute modules, sibling modules) a file imports."""
    absolute, siblings = set(), set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            absolute.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if node.module is None:
                    siblings.update(a.name for a in node.names)
                else:
                    siblings.add(node.module)
            else:
                absolute.add(node.module)
    return absolute, siblings


def test_environment_service_reaches_only_the_atmosphere_and_the_requirement():
    absolute, siblings = _imports(ANALYSIS / "environment_service.py")
    assert siblings == set()
    assert {n for n in absolute if n.startswith("rocketforge")} == {
        "rocketforge.core.result", "rocketforge.engine.requirement",
        "rocketforge.physics", "rocketforge.physics.atmosphere"}


def test_liq2_modules_add_only_the_environment_service():
    for name in ("engine_requirement_service.py", "engine_requirement_controller.py"):
        absolute, siblings = _imports(ANALYSIS / name)
        assert siblings <= {"engine_requirement_service", "environment_service",
                            "thermochemistry_presets"}, (name, siblings)
        assert {n for n in absolute if n.startswith("rocketforge")} == {
            "rocketforge.engine.requirement"}, name


#: The one place outside the atmosphere package that states a USSA 1976
#: constant, before ENV-1: the frozen compressible ``PerfectGas.air()``, whose
#: R = 287.0528 J/(kg K) is documented as 8314.32 / 28.9644.
PRE_EXISTING = {ROOT / "rocketforge" / "physics" / "compressible" / "gas.py"}


def test_no_atmosphere_constant_is_restated_outside_the_package():
    for path in (ROOT / "rocketforge").rglob("*.py"):
        if "atmosphere" in path.parts or path in PRE_EXISTING:
            continue
        text = path.read_text(encoding="utf-8")
        for constant in ("8.31432", "8314.32", "28.9644", "6356766", "6.356766"):
            assert constant not in text, (path, constant)


def test_the_compressible_air_constant_agrees_with_the_standard():
    """``PerfectGas.air()`` (frozen, pre-ENV-1) uses 287.0528 J/(kg K) and cites
    8314.32 / 28.9644, which is 287.05307. They differ by 9.5e-7 relative. That
    is recorded here, not changed: the compressible package is frozen and the
    atmosphere package does not use it."""
    from rocketforge.physics.compressible import PerfectGas

    standard = ussa1976.R_STAR / ussa1976.M0
    assert standard == pytest.approx(287.05307, abs=5e-6)
    assert PerfectGas.air().gas_constant == pytest.approx(standard, rel=1e-6)
    assert PerfectGas.air().gas_constant != pytest.approx(standard, rel=1e-7)
    assert PerfectGas.air().gamma == ussa1976.GAMMA


# ===========================================================================
# parity: altitude == the same manual pressure, downstream
# ===========================================================================


def _chain(requirement):
    definition, issues = trade_service.build_definition(requirement, IDEAL)
    assert definition is not None, issues
    rows = tuple(trade_service.evaluate_candidate(definition, k) for k in definition.candidates)
    trade = trade_service.assemble_result(definition, rows).with_selection("sutton-o2-ch4")
    point, issues = sizing_service.operating_point(trade, stale=False)
    assert point is not None, issues
    sized_def, _ = sizing_service.build_definition(point, sizing_service.SizingSettings())
    sized = sizing_service.solve_sizing(sized_def)
    basis, _ = geometry_service.throat_basis(sized, stale=False)
    geo_def, _ = geometry_service.build_definition(basis, geometry_service.GeometrySettings(
        characteristic_length=1.0, contraction_ratio=3.0, converging_half_angle_deg=25.0))
    return trade, point, sized, geometry_service.solve_geometry(geo_def)


def _assert_parity(altitude_m):
    by_altitude = BASE.replace(environment=replace(ALTITUDE, altitude=altitude_m))
    pressure = environment_service.ambient_pressure(by_altitude.environment)
    manual = BASE.replace(environment=DesignEnvironment(AmbientMode.CUSTOM, pressure))
    a, b = _chain(by_altitude), _chain(manual)
    assert a[1].ambient_pressure == b[1].ambient_pressure == pressure
    for ca, cb in zip(a[0].candidates, b[0].candidates):
        assert (ca.key, ca.status, dict(ca.metrics)) == (cb.key, cb.status, dict(cb.metrics))
    assert a[2].quantities == b[2].quantities and a[2].status == b[2].status
    assert a[2].regime == b[2].regime and a[2].notes == b[2].notes
    assert a[3].quantities == b[3].quantities
    assert a[0].definition.fingerprint != b[0].definition.fingerprint   # different intent
    return a


def test_altitude_and_its_manual_pressure_size_identically(stub_gateway):
    for z in (0.0, 10000.0, 25000.0):
        trade, point, sized, geometry = _assert_parity(z)
        assert sized.ok and geometry.ok
        assert abs(sized.quantities["thrust_closure"]) <= 1e-12


def test_sea_level_altitude_equals_the_named_sea_level(stub_gateway):
    """Z = 0 resolves to P0 = 101 325 Pa exactly, the named sea-level pressure."""
    zero = _chain(BASE.replace(environment=replace(ALTITUDE, altitude=0.0)))
    named = _chain(BASE)
    assert zero[2].quantities == named[2].quantities


@requires_cea
def test_parity_holds_through_nasa_cea():
    trade, point, sized, geometry = _assert_parity(10000.0)
    assert point.ambient_pressure == pytest.approx(26499.9, rel=1e-5)
    assert sized.ok and abs(sized.quantities["thrust_closure"]) <= 1e-12


# ===========================================================================
# the controller
# ===========================================================================


@pytest.fixture()
def controller(qt_app):
    return EngineRequirementController()


def test_altitude_through_the_form(controller):
    controller.setAmbientMode("standard_atmosphere")
    assert [i["code"] for i in controller.property("issues")
            if i["field"] == "environment"] == ["ALTITUDE_MISSING"]
    assert controller.property("ambientPressureText") == ""
    assert controller.property("atmosphereRows") == []
    controller.setAltitude("10")                                     # km
    assert controller.requirement().environment.altitude == 10000.0
    assert controller.property("altitudeText") == "10"
    assert controller.property("ambientPressureText") == "26.4998981393"
    rows = {r["key"]: r for r in controller.property("atmosphereRows")}
    assert rows["temperature"]["value"] == "223.252" and rows["layer"]["value"] == "0"
    assert rows["geopotential_altitude"]["unit"] == "m'"
    assert "U.S. Standard Atmosphere, 1976" in controller.property("atmosphereSource")


def test_switching_modes_keeps_what_was_typed(controller):
    controller.setAmbientMode("standard_atmosphere")
    controller.setAltitude("12")
    controller.setAmbientMode("vacuum")
    assert controller.property("ambientPressureText") == "0"
    assert controller.property("atmosphereRows") == []
    controller.setAmbientPressure("40")                              # becomes custom
    env = controller.requirement().environment
    assert (env.mode, env.custom_pressure, env.altitude) == (AmbientMode.CUSTOM, 40e3, 12e3)
    controller.setAmbientMode("standard_atmosphere")
    assert controller.requirement().environment.altitude == 12000.0


def test_invalid_altitude_text_is_ignored_and_out_of_range_is_reported(controller):
    controller.setAmbientMode("standard_atmosphere")
    controller.setAltitude("10")
    for text in ("abc", "nan", "inf"):
        controller.setAltitude(text)
        assert controller.requirement().environment.altitude == 10000.0
    controller.setAltitude("1001")
    assert "ALTITUDE_OUT_OF_RANGE" in [i["code"] for i in controller.property("issues")]
    assert controller.property("ambientPressureText") == ""
    controller.setAltitude("")
    assert controller.requirement().environment.altitude is None
