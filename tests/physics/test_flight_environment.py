"""ENV-3: the point flight environment -- gravity, Mach, q and Reynolds number.

Oracles are independent of the implementation: gravity from the WGS 84
defining constants in exact rational arithmetic, and Mach, q and Re from the
U.S. Standard Atmosphere, 1976's printed Table I values.
"""

from __future__ import annotations

import ast
import json
import math
import pathlib
import subprocess
import sys
from fractions import Fraction

import pytest

from rocketforge.core.result import Status
from rocketforge.physics import flight
from rocketforge.physics.atmosphere import (
    manual_atmosphere,
    standard_atmosphere,
    ussa1976,
    vacuum_atmosphere,
)
from rocketforge.physics.flight import (
    MINIMUM_GEOMETRIC_ALTITUDE,
    WGS84_SPHERICAL,
    FlightEnvironment,
    FlightEnvironmentFormatError,
    SphericalGravity,
    flight_environment,
    standard_flight_environment,
)

PACKAGE = pathlib.Path(flight.__file__).parent
GM = Fraction("3.986004418e14")          # WGS 84, NGA.STND.0036_1.0.0, Table 3.1
A = Fraction(6378137)


def at(z: float, v: float, length: float | None = None) -> FlightEnvironment:
    solution = standard_flight_environment("ussa1976", z, v, characteristic_length=length)
    assert solution.status is Status.OK, solution.diagnostics
    return solution.value


# -- gravity ----------------------------------------------------------------


def test_sea_level_gravity_matches_an_exact_hand_calculation():
    exact = float(GM / A**2)
    assert at(0.0, 0.0).gravity == pytest.approx(exact, rel=1e-15)
    assert at(0.0, 0.0).gravity == pytest.approx(9.798285, abs=5e-7)
    # Not the Isp convention g0, and below it: pure attraction at the equatorial radius.
    assert at(0.0, 0.0).gravity < 9.80665


@pytest.mark.parametrize("z", [-5000.0, 0.0, 11000.0, 86000.0, 400000.0, 1000000.0])
def test_gravity_is_inverse_square_in_r_equals_a_plus_z(z):
    env = at(z, 0.0)
    r = A + Fraction(z)
    assert env.radius == float(r)
    assert env.gravity == pytest.approx(float(GM / r**2), rel=1e-15)
    assert env.gravity * env.radius**2 == pytest.approx(float(GM), rel=1e-15)


def test_gravity_falls_with_altitude_and_closes_the_inverse_square_ratio():
    heights = [-5000.0 + 2500.0 * i for i in range(403)]
    g = [at(z, 0.0).gravity for z in heights]
    assert all(b < a for a, b in zip(g, g[1:]))
    low, high = at(0.0, 0.0), at(1000000.0, 0.0)
    assert low.gravity / high.gravity == pytest.approx(
        float(((A + 1000000) / A) ** 2), rel=1e-14)


def test_gravity_model_records_its_constants_and_source():
    assert WGS84_SPHERICAL.gm == 3.986004418e14
    assert WGS84_SPHERICAL.reference_radius == 6378137.0
    assert "NGA.STND.0036" in WGS84_SPHERICAL.source
    assert "No J2" in WGS84_SPHERICAL.source
    for bad in (0.0, -1.0, math.nan, math.inf, True):
        with pytest.raises(ValueError):
            SphericalGravity("x", "x", bad, 1.0, "")
        with pytest.raises(ValueError):
            SphericalGravity("x", "x", 1.0, bad, "")


def test_another_gravity_model_is_used_as_given():
    model = SphericalGravity("test", "test", 4.0e14, 6.0e6, "test constants")
    env = standard_flight_environment("ussa1976", 0.0, 0.0, gravity_model=model).value
    assert env.gravity == 4.0e14 / 6.0e6**2 and env.gravity_model is model


def test_minimum_altitude_is_the_lowest_any_atmosphere_reaches():
    assert MINIMUM_GEOMETRIC_ALTITUDE == ussa1976.GEOMETRIC_ALTITUDE_RANGE[0]
    vac = vacuum_atmosphere().value
    assert flight_environment(vac, 0.0, geometric_altitude=-5000.0).ok
    refused = flight_environment(vac, 0.0, geometric_altitude=-5000.001)
    assert refused.value is None and refused.diagnostics[0].code == "ALTITUDE_OUT_OF_RANGE"


# -- Mach, q, Re against printed Table I -------------------------------------

#: Table I (geometric): Z, Cs (m/s), rho (kg/m^3), mu (Pa s), as printed.
TABLE_I = [
    (0.0, 340.294, 1.2250, 1.7894e-5),
    (11000.0, 295.154, 3.6480e-1, 1.4223e-5),
    (20000.0, 295.070, 8.8910e-2, 1.4216e-5),
]


@pytest.mark.parametrize("z, cs, rho, mu", TABLE_I)
@pytest.mark.parametrize("v", [0.0, 50.0, 340.0, 1000.0, 7800.0])
def test_mach_q_reynolds_against_printed_table(z, cs, rho, mu, v):
    env = at(z, v, length=2.5)
    assert env.mach == pytest.approx(v / cs, rel=2e-6, abs=0.0)
    assert env.dynamic_pressure == pytest.approx(0.5 * rho * v * v, rel=1e-4, abs=0.0)
    assert env.reynolds_number == pytest.approx(rho * v * 2.5 / mu, rel=1.5e-4, abs=0.0)


def test_closures_are_exact_against_the_state_it_was_built_on():
    for z in (0.0, 30000.0, 80000.0, 83000.0, 86000.0):
        s = ussa1976.state(z).value
        env = flight_environment(s, 123.4, characteristic_length=0.7).value
        assert env.mach == 123.4 / s.speed_of_sound
        assert env.dynamic_pressure == 0.5 * s.density * 123.4 * 123.4
        assert env.reynolds_number == s.density * 123.4 * 0.7 / s.dynamic_viscosity


def test_scaling_with_speed_and_length_at_fixed_atmosphere():
    base = at(5000.0, 100.0, 1.0)
    for k in (0.5, 2.0, 3.0, 10.0):
        scaled = at(5000.0, 100.0 * k, 1.0)
        assert scaled.mach == pytest.approx(k * base.mach, rel=1e-14)
        assert scaled.dynamic_pressure == pytest.approx(k * k * base.dynamic_pressure, rel=1e-14)
        assert scaled.reynolds_number == pytest.approx(k * base.reynolds_number, rel=1e-14)
        longer = at(5000.0, 100.0, k)
        assert longer.reynolds_number == pytest.approx(k * base.reynolds_number, rel=1e-14)
        assert longer.mach == base.mach and longer.dynamic_pressure == base.dynamic_pressure


def test_zero_speed_is_defined_as_zero():
    env = at(0.0, 0.0, 1.0)
    assert env.mach == 0.0 and env.dynamic_pressure == 0.0 and env.reynolds_number == 0.0


# -- refusals ---------------------------------------------------------------

BAD_NUMBERS = [math.nan, math.inf, -math.inf, None, "1", True]


@pytest.mark.parametrize("bad", [-1.0, -1e-300, *BAD_NUMBERS])
def test_air_speed_is_a_finite_non_negative_magnitude(bad):
    solution = flight_environment(vacuum_atmosphere().value, bad)
    assert solution.value is None and solution.status is Status.NO_SOLUTION
    assert solution.diagnostics[0].code == "AIR_SPEED_INVALID"
    assert solution.diagnostics[0].field == "air_speed"


@pytest.mark.parametrize("bad", [0.0, -0.1, math.nan, math.inf, "1", True])
def test_characteristic_length_must_be_positive_and_finite(bad):
    solution = standard_flight_environment("ussa1976", 0.0, 10.0, characteristic_length=bad)
    assert solution.value is None
    assert solution.diagnostics[0].code == "CHARACTERISTIC_LENGTH_INVALID"


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, "1", True])
def test_geometric_altitude_must_be_finite(bad):
    solution = flight_environment(vacuum_atmosphere().value, 0.0, geometric_altitude=bad)
    assert solution.value is None and solution.diagnostics[0].code == "ALTITUDE_INVALID"


def test_atmosphere_refusals_pass_through():
    assert standard_flight_environment("ussa1976", 1.0e6 + 1, 0.0).diagnostics[0].code \
        == "ALTITUDE_OUT_OF_RANGE"
    assert standard_flight_environment("nrlmsis", 0.0, 0.0).diagnostics[0].code \
        == "ATMOSPHERE_MODEL_UNKNOWN"
    assert standard_flight_environment("ussa1976", math.nan, 0.0).value is None
    assert flight_environment({"pressure": 1.0}, 0.0).diagnostics[0].code == "ATMOSPHERE_INVALID"
    assert flight_environment(vacuum_atmosphere().value, 0.0, gravity_model="wgs84"
                              ).diagnostics[0].code == "GRAVITY_MODEL_INVALID"


def test_stated_altitude_must_be_the_atmosphere_altitude():
    s = ussa1976.state(10000.0).value
    mismatch = flight_environment(s, 0.0, geometric_altitude=10001.0)
    assert mismatch.value is None and mismatch.diagnostics[0].code == "ALTITUDE_MISMATCH"
    stated = flight_environment(s, 0.0, geometric_altitude=10000.0).value
    implied = flight_environment(s, 0.0).value
    assert stated.altitude_source == "stated" and implied.altitude_source == "atmosphere"
    assert stated.gravity == implied.gravity


# -- unavailable propagates --------------------------------------------------


@pytest.mark.parametrize("z", [86000.001, 90000.0, 150000.0, 600000.0, 1000000.0])
def test_above_86_km_mach_and_reynolds_are_unavailable_with_the_standards_reason(z):
    env = at(z, 7000.0, 1.0)
    s = env.atmosphere
    assert s.speed_of_sound is None and s.dynamic_viscosity is None
    assert env.mach is None and env.reynolds_number is None
    assert s.unavailable["speed_of_sound"] in env.unavailable["mach"]
    assert s.unavailable["dynamic_viscosity"] in env.unavailable["reynolds_number"]
    # Density is defined, so q is: a momentum flux, not a continuum property.
    assert env.dynamic_pressure == pytest.approx(0.5 * s.density * 7000.0**2, rel=1e-15)
    assert env.dynamic_pressure > 0.0
    assert env.gravity is not None


def test_the_86_km_boundary_follows_the_atmosphere_exactly():
    inside, base, above = at(85999.999, 300.0, 1.0), at(86000.0, 300.0, 1.0), \
        at(86000.0001, 300.0, 1.0)
    assert inside.mach is not None and base.mach is not None and above.mach is None
    assert base.mach == pytest.approx(inside.mach, rel=1e-5)
    assert base.reynolds_number == pytest.approx(inside.reynolds_number, rel=1e-4)


def test_reynolds_is_unavailable_without_a_length_only_for_that_reason():
    env = at(0.0, 100.0)
    assert env.reynolds_number is None and env.mach is not None
    assert "characteristic length" in env.unavailable["reynolds_number"]
    assert "viscosity" not in env.unavailable["reynolds_number"].split(". ", 1)[1]


def test_vacuum_has_zero_q_and_no_mach_or_reynolds():
    env = flight_environment(vacuum_atmosphere().value, 7800.0, geometric_altitude=400000.0,
                             characteristic_length=3.0).value
    assert env.dynamic_pressure == 0.0
    assert env.mach is None and env.reynolds_number is None
    assert "no gas" in env.unavailable["mach"] and "no gas" in env.unavailable["reynolds_number"]
    assert env.gravity == pytest.approx(float(GM / (A + 400000) ** 2), rel=1e-15)
    no_altitude = flight_environment(vacuum_atmosphere().value, 0.0).value
    assert no_altitude.gravity is None and no_altitude.radius is None
    assert "geometric altitude" in no_altitude.unavailable["gravity"]


def test_manual_pressure_gives_gravity_only_when_an_altitude_is_stated():
    s = manual_atmosphere(26500.0).value
    env = flight_environment(s, 200.0, geometric_altitude=10000.0,
                             characteristic_length=1.0).value
    assert env.gravity is not None and env.altitude_source == "stated"
    assert env.mach is None and env.dynamic_pressure is None and env.reynolds_number is None
    assert "pressure only" in env.unavailable["dynamic_pressure"]


# -- records, provenance, determinism -----------------------------------------


@pytest.mark.parametrize("make", [
    lambda: at(0.0, 250.0, 1.5),
    lambda: at(84000.0, 250.0),
    lambda: at(300000.0, 7700.0, 2.0),
    lambda: flight_environment(vacuum_atmosphere().value, 10.0).value,
    lambda: flight_environment(manual_atmosphere(1.0e4).value, 10.0,
                               geometric_altitude=0.0).value,
])
def test_records_round_trip_through_json(make):
    env = make()
    record = json.loads(json.dumps(env.to_dict()))
    assert record["schema"] == "rocketforge.flight-environment" and record["version"] == 1
    assert FlightEnvironment.from_dict(record) == env
    assert make() == env                                            # deterministic


def test_record_names_units_and_provenance():
    record = at(1000.0, 100.0, 1.0).to_dict()
    for key in ("air_speed_m_s", "geometric_altitude_m", "characteristic_length_m",
                "radius_m", "gravity_m_s2", "mach", "dynamic_pressure_Pa",
                "reynolds_number", "gravity_model", "atmosphere"):
        assert key in record, key
    assert record["gravity_model"]["gm_m3_s2"] == 3.986004418e14
    assert record["atmosphere"]["model"] == "ussa1976"
    p = record["provenance"]
    assert "GM / r^2" in p["gravity"] and "V_air / a" in p["mach"]
    assert "rho V_air^2 / 2" in p["dynamic_pressure"] and "rho V_air L / mu" in p["reynolds_number"]
    assert "no wind" in p["scope"]


@pytest.mark.parametrize("mutate", [
    lambda r: r.update(schema="other"),
    lambda r: r.update(version=2),
    lambda r: r.update(air_speed_m_s=-1.0),
    lambda r: r.update(air_speed_m_s=None),
    lambda r: r.update(mach="1"),
    lambda r: r.update(mach=None),                 # neither defined nor unavailable
    lambda r: r.update(unavailable={**r["unavailable"], "mach": "x"}),  # both
    lambda r: r.pop("atmosphere"),
    lambda r: r["gravity_model"].update(gm_m3_s2=-1.0),
])
def test_bad_records_are_refused(mutate):
    record = json.loads(json.dumps(at(0.0, 100.0, 1.0).to_dict()))
    mutate(record)
    with pytest.raises(FlightEnvironmentFormatError):
        FlightEnvironment.from_dict(record)


# -- boundaries of the package ------------------------------------------------


def test_package_imports_only_core_and_the_atmosphere():
    allowed = {"__future__", "math", "collections", "dataclasses", "typing"}
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    continue                                   # within the package
                names = [node.module]
            else:
                continue
            for name in names:
                assert (name.split(".")[0] in allowed
                        or name.startswith(("rocketforge.core", "rocketforge.physics.atmosphere"))
                        ), f"{path.name} imports {name}"


def test_no_provider_engine_or_qt_is_loaded_by_a_calculation():
    code = (
        "import sys\n"
        "from rocketforge.physics.flight import standard_flight_environment\n"
        "for z in (0.0, 84000.0, 500000.0):\n"
        "    assert standard_flight_environment('ussa1976', z, 300.0, characteristic_length=1.0).ok\n"
        "bad = [m for m in sys.modules if m.startswith(('rocketforge.providers', "
        "'rocketforge.engine', 'rocketforge.engineering', 'rocketforge.application', "
        "'PySide6', 'CoolProp', 'cea', 'rocketcea', 'cantera', 'scipy'))]\n"
        "assert not bad, bad\n")
    subprocess.run([sys.executable, "-c", code], check=True, cwd=PACKAGE.parents[2])
