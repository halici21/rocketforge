"""ENV-1: the U.S. Standard Atmosphere, 1976, against the Standard itself.

**References, not the implementation.** Every reference value here was read
from the Standard's own printed tables (NASA-TM-X-74335 / NOAA-S/T 76-1562,
NTRS 19770009539) or from Sutton & Biblarz, *Rocket Propulsion Elements*, 9th
ed., Appendix 2, which cites the Standard as its source. None was produced by
this code.

* **Table I** (geometric altitude): T, P and rho. Its pressure column is
  printed **truncated**, not rounded: in every row read, the model's pressure
  cut to the printed digits gives the printed value. The rows' own P, T and rho
  disagree with rho = P M0 / (R* T) by up to 5e-5 for the same reason. So
  pressure is checked against the truncation interval,
  ``printed <= P < printed + 1 unit``, and T and rho against rounding
  (+-0.5 unit).
* **Table II** (geopotential altitude): one row, for the H-indexed path.
* **Table III** (geometric altitude): speed of sound and dynamic viscosity.
* **Sutton Appendix 2.** Its rows up to 50 km are geometric. Its 75 km row is
  the Standard's value at *geopotential* 75 km, not geometric (Table I at
  Z = 75 000 m reads 208.399 K, not 206.650 K). The test pins that, so no
  one "fixes" the model to Sutton's row.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.constants import STANDARD_GRAVITY, UNIVERSAL_GAS_CONSTANT
from rocketforge.core.result import Status
from rocketforge.physics.atmosphere import ussa1976 as u

# ===========================================================================
# the Standard's printed tables
# ===========================================================================

#: Table I: Z (m), H (m', as printed), T (K), P (mb, truncated), rho (kg/m^3).
TABLE_I = [
    (-5000, -5004, "320.676", "1.7776e3", "1.9311"),
    (11000, 10981, "216.774", "2.2699e2", "3.6480e-1"),
    (11100, 11081, "216.650", "2.2346e2", "3.5932e-1"),
    (11200, 11180, "216.650", "2.1997e2", "3.5372e-1"),
    (19000, 18943, "216.650", "6.4674e1", "1.0400e-1"),
    (38000, 37774, "244.818", "3.7713", "5.3666e-3"),
    (60000, 59439, "247.021", "2.1958e-1", "3.0968e-4"),
    (75000, 74125, "208.399", "2.3881e-2", "3.9921e-5"),
    (80000, 79006, "198.639", "1.0524e-2", "1.8458e-5"),
]

#: Table II (geopotential altitude): H (m'), Z (m, as printed), T, P (mb,
#: truncated), rho. H = 11 000 and 20 000 m' are Table 4 layer bases.
TABLE_II = [
    (11000, 11019, "216.650", "2.2632e2", "3.6392e-1"),
    (20000, 20063, "216.650", "5.4748e1", "8.8035e-2"),
    (60000, 60572, "245.450", "2.0314e-1", "2.8832e-4"),
    (75000, 75896, "206.650", "2.0679e-2", "3.4861e-5"),
]

#: Table III: Z (m), speed of sound (m/s), dynamic viscosity (N s/m^2).
TABLE_III = [(-1000, "344.11", "1.8206e-5"), (3000, "328.58", "1.6938e-5"),
             (27000, "299.72", "1.4592e-5")]

#: Sutton Appendix 2 rows, by what each one actually is. Labelled "altitude",
#: its rows mix geometric and geopotential readings of the Standard and carry
#: digit transpositions; each value is listed under the reading it matches.
#: (kind, altitude, T, P/P0, rho); None where the printed value is a misprint.
SUTTON = [
    ("geometric", 0, "288.150", "1.0000", "1.2250"),
    ("geometric", 1000, "281.651", "8.8700e-1", "1.1117"),
    ("geopotential", 3000, "268.650", None, "9.0912e-1"),       # P/P0 printed 6.6919e-1
    ("geopotential", 5000, "255.650", "5.3313e-1", None),       # rho printed 7.6312e-1
    ("geometric", 10000, "223.252", None, "4.1351e-1"),         # P/P0 printed 2.6151e-1
    ("geometric", 25000, "221.552", "2.5158e-2", "4.0084e-2"),
    ("geometric", 50000, "270.650", "7.8735e-4", "1.0269e-3"),
    ("geopotential", 75000, "206.650", "2.0408e-5", "3.4861e-5"),
]

#: The misprints, against the Standard read the same way as the row's other
#: values: (kind, altitude, quantity, printed, the Standard's value).
SUTTON_MISPRINTS = [
    ("geopotential", 3000, "pressure_ratio", 6.6919e-1, 6.9191e-1),
    ("geopotential", 5000, "density", 7.6312e-1, 7.3612e-1),
    ("geometric", 10000, "pressure_ratio", 2.6151e-1, 2.6153e-1),
]


def unit(printed: str) -> float:
    """One unit in the last printed digit."""
    mantissa = printed.lower().split("e")[0]
    exponent = int(printed.lower().split("e")[1]) if "e" in printed.lower() else 0
    decimals = len(mantissa.split(".")[1]) if "." in mantissa else 0
    return 10.0 ** (exponent - decimals)


def rounds_to(value: float, printed: str) -> bool:
    return abs(value - float(printed)) <= 0.5 * unit(printed) * (1 + 1e-9)


def truncates_to(value: float, printed: str) -> bool:
    return float(printed) <= value < float(printed) + unit(printed)


def at(z):
    solution = u.state(z)
    assert solution.status is Status.OK, solution.diagnostics
    return solution.value


@pytest.mark.parametrize("z,h,t,p_mb,rho", TABLE_I)
def test_table_i(z, h, t, p_mb, rho):
    s = at(z)
    assert round(s.geopotential_altitude) == h
    assert rounds_to(s.temperature, t), s.temperature
    assert truncates_to(s.pressure / 100.0, p_mb), s.pressure
    assert rounds_to(s.density, rho), s.density


@pytest.mark.parametrize("h,z,t,p_mb,rho", TABLE_II)
def test_table_ii(h, z, t, p_mb, rho):
    s = u.state_at_geopotential(float(h)).value
    # Z is printed to the metre. Eq. (19) gives 11 019.07, 20 063.12 and
    # 60 571.73 (rounded as printed) but 75 895.45 against a printed 75 896,
    # while its neighbours (76 408, 76 920) round correctly. So: within 1 m.
    assert abs(s.geometric_altitude - z) < 1.0
    assert rounds_to(s.temperature, t)
    assert truncates_to(s.pressure / 100.0, p_mb), s.pressure
    assert rounds_to(s.density, rho)


@pytest.mark.parametrize("z,a,mu", TABLE_III)
def test_table_iii_speed_of_sound_and_viscosity(z, a, mu):
    s = at(z)
    assert rounds_to(s.speed_of_sound, a), s.speed_of_sound
    assert rounds_to(s.dynamic_viscosity, mu), s.dynamic_viscosity


def _read(kind: str, altitude: float):
    return at(altitude) if kind == "geometric" else u.state_at_geopotential(altitude).value


@pytest.mark.parametrize("kind,altitude,t,ratio,rho", SUTTON)
def test_sutton_appendix_2_rows_match_the_standard_read_as_labelled(kind, altitude, t,
                                                                    ratio, rho):
    s = _read(kind, float(altitude))
    assert rounds_to(s.temperature, t)
    if ratio is not None:
        assert abs(s.pressure / u.P0 - float(ratio)) <= unit(ratio)
    if rho is not None:
        assert abs(s.density - float(rho)) <= unit(rho)


def test_sutton_mixes_geometric_and_geopotential_rows():
    """The 3 000, 5 000 and 75 000 m rows are the Standard at geopotential
    altitude; read as geometric (what the model takes) they are off by far more
    than their digits. Table I at Z = 75 000 m is 208.399 K, not 206.650 K."""
    for altitude, t in ((3000, "268.650"), (5000, "255.650"), (75000, "206.650")):
        assert not rounds_to(at(float(altitude)).temperature, t)
    assert rounds_to(at(75000.0).temperature, "208.399")


@pytest.mark.parametrize("kind,altitude,quantity,printed,standard", SUTTON_MISPRINTS)
def test_sutton_misprints_are_misprints(kind, altitude, quantity, printed, standard):
    s = _read(kind, float(altitude))
    value = s.pressure / u.P0 if quantity == "pressure_ratio" else s.density
    assert abs(value - standard) <= 1e-5 * standard * 2                 # the Standard
    assert abs(value - printed) > 5e-5 * standard                        # not Sutton's


def test_sea_level_reference_state():
    s = at(0.0)
    assert s.pressure == 101325.0 and s.temperature == 288.15
    assert s.geopotential_altitude == 0.0 and s.layer == 0
    assert rounds_to(s.density, "1.2250")
    assert rounds_to(s.speed_of_sound, "340.29")
    assert rounds_to(s.dynamic_viscosity, "1.7894e-5")


# ===========================================================================
# constants: the Standard's, from its text (not Table 2's misprints)
# ===========================================================================


def test_constants_are_the_standards():
    assert u.R_STAR == 8314.32 and u.M0 == 28.9644 and u.R0 == 6356766.0
    assert u.P0 == 101325.0 and u.T0 == 288.15 and u.GAMMA == 1.4
    assert u.BETA == 1.458e-6 and u.SUTHERLAND_S == 110.4
    assert u.G0 == u.G0_PRIME == STANDARD_GRAVITY == 9.80665
    # Deliberately not CODATA: the Standard's R* reproduces its tables.
    assert u.R_STAR != UNIVERSAL_GAS_CONSTANT * 1000.0
    assert abs(u.R_STAR / (UNIVERSAL_GAS_CONSTANT * 1000.0) - 1.0) < 2e-5
    assert [h for h, _ in u.LAYERS] == [0, 11000, 20000, 32000, 47000, 51000, 71000]
    assert [g * 1000 for _, g in u.LAYERS] == pytest.approx([-6.5, 0, 1, 2.8, 0, -2.8, -2])


def test_sutherland_s_is_110_4_not_110():
    """Table III's mu/mu0 at -1 000 m is 1.0174 with mu = 1.8206e-5, so
    mu0 = 1.7895e-5, which S = 110 K (p. 4's misprint) cannot give."""
    t = 288.15
    assert rounds_to(1.458e-6 * t ** 1.5 / (t + 110.4), "1.7894e-5")
    assert not rounds_to(1.458e-6 * t ** 1.5 / (t + 110.0), "1.7894e-5")


# ===========================================================================
# altitude conventions
# ===========================================================================


def test_geometric_and_geopotential_are_distinct_and_inverse():
    assert u.geopotential_altitude(11000.0) == pytest.approx(10980.998, abs=1e-3)
    assert u.geopotential_altitude(0.0) == 0.0
    for z in np.linspace(-5000.0, 80000.0, 101):
        assert u.geometric_altitude(u.geopotential_altitude(z)) == pytest.approx(z, abs=1e-8)
        if z > 0:
            assert u.geopotential_altitude(z) < z
        elif z < 0:
            assert u.geopotential_altitude(z) < z          # deeper below, too


def test_eleven_kilometres_geometric_is_still_the_troposphere():
    """Z = 11 000 m is H = 10 981 m': layer 0, T = 216.774 K (Table I), not the
    216.650 K a model that confused the two would give."""
    s = at(11000.0)
    assert s.layer == 0 and s.temperature > 216.65
    assert at(u.geometric_altitude(11000.0)).temperature == pytest.approx(216.65, abs=1e-9)


def test_the_two_entry_points_agree():
    for z in (-4000.0, 0.0, 8000.0, 15000.0, 33333.0, 49000.0, 66000.0, 79999.0):
        a, b = at(z), u.state_at_geopotential(u.geopotential_altitude(z)).value
        for name in ("temperature", "pressure", "density", "speed_of_sound",
                     "dynamic_viscosity"):
            assert getattr(a, name) == pytest.approx(getattr(b, name), rel=1e-13)


# ===========================================================================
# layer boundaries and continuity
# ===========================================================================

BOUNDARIES = [h for h, _ in u.LAYERS[1:]]


@pytest.mark.parametrize("h", BOUNDARIES)
def test_each_layer_boundary_is_continuous(h):
    """At each Hb, both sides agree; just above and below differ by the gradient."""
    eps = 1e-6                                         # m'
    below = u.state_at_geopotential(h - eps).value
    exact = u.state_at_geopotential(h).value
    above = u.state_at_geopotential(h + eps).value
    assert below.layer + 1 == exact.layer == above.layer
    for name in ("temperature", "pressure", "density", "speed_of_sound",
                 "dynamic_viscosity"):
        a, b, c = getattr(below, name), getattr(exact, name), getattr(above, name)
        assert a == pytest.approx(b, rel=1e-9) and c == pytest.approx(b, rel=1e-9), name


def test_base_temperatures_are_table_4s():
    """TM,b from eq. (23): 288.15, 216.65, 216.65, 228.65, 270.65, 270.65, 214.65."""
    expected = [288.15, 216.65, 216.65, 228.65, 270.65, 270.65, 214.65]
    got = [u.state_at_geopotential(h).value.temperature for h, _ in u.LAYERS]
    assert got == pytest.approx(expected, abs=1e-9)


def test_layer_pressures_chain_through_every_base():
    """Each base pressure is the layer below evaluated at the base (33a/33b),
    so walking up base by base and evaluating directly agree. The Standard's
    printed values at H = 11 000 and 20 000 m' are in TABLE_II above."""
    for (h0, g0), (h1, _g1) in zip(u.LAYERS, u.LAYERS[1:]):
        base = u.state_at_geopotential(h0).value
        top = u.state_at_geopotential(h1).value
        if g0 == 0.0:
            expected = base.pressure * math.exp(
                -u.G0_PRIME * u.M0 * (h1 - h0) / (u.R_STAR * base.temperature))
        else:
            expected = base.pressure * (base.temperature / top.temperature) ** (
                u.G0_PRIME * u.M0 / (u.R_STAR * g0))
        assert top.pressure == pytest.approx(expected, rel=1e-13)


# ===========================================================================
# physics consistency and a dense grid
# ===========================================================================

GRID = np.concatenate([np.linspace(-5000.0, 80000.0, 4251),
                       [u.geometric_altitude(h) + d for h in BOUNDARIES
                        for d in (-1e-3, 0.0, 1e-3)]])


def test_dense_grid_is_physical_and_consistent():
    previous = None
    for z in np.sort(GRID):
        s = at(float(z))
        assert s.pressure > 0 and s.density > 0 and s.temperature > 0
        assert 180.0 < s.temperature < 330.0
        assert s.density == pytest.approx(s.pressure * u.M0 / (u.R_STAR * s.temperature),
                                          rel=1e-14)
        assert s.speed_of_sound == pytest.approx(
            math.sqrt(u.GAMMA * u.R_STAR * s.temperature / u.M0), rel=1e-14)
        assert s.dynamic_viscosity == pytest.approx(
            u.BETA * s.temperature ** 1.5 / (s.temperature + u.SUTHERLAND_S), rel=1e-14)
        if previous is not None and z > previous[0]:
            assert s.pressure < previous[1].pressure          # strictly falls with height
            assert s.density < previous[1].density
            jump = abs(s.temperature - previous[1].temperature)
            assert jump <= 6.6e-3 * (z - previous[0]) + 1e-9  # |dT/dZ| within Table 4
        previous = (z, s)


def test_hydrostatic_balance_holds_locally():
    """dP/dH = -g0' rho (eq. 16 in H): a centred difference over 1 m'."""
    for h in (500.0, 15000.0, 25000.0, 40000.0, 49000.0, 60000.0, 75000.0):
        lo, mid, hi = (u.state_at_geopotential(h + d).value for d in (-0.5, 0.0, 0.5))
        assert (hi.pressure - lo.pressure) == pytest.approx(
            -u.G0_PRIME * mid.density, rel=1e-6)


# ===========================================================================
# range and refusals
# ===========================================================================


def test_the_exact_range_is_supported_and_nothing_beyond():
    """ENV-1B extends the range from 80 km to the Standard's 1000 km; the
    values below 80 km are unchanged (every test above)."""
    low, high = u.GEOMETRIC_ALTITUDE_RANGE
    assert (low, high) == (-5000.0, 1000000.0)
    assert at(low).layer == 0 and at(80000.0).layer == 6 and at(high).layer == 10
    for z in (low - 1e-6, high + 1e-6, -1e9, 1000001.0, 1e12):
        solution = u.state(z)
        assert solution.value is None and solution.status is Status.NO_SOLUTION
        assert solution.diagnostics[0].code == "ALTITUDE_OUT_OF_RANGE"
        assert "Nothing is extrapolated" in solution.diagnostics[0].message


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, None, "1000", True])
def test_invalid_inputs_are_refused(bad):
    for solution in (u.state(bad), u.state_at_geopotential(bad)):
        assert solution.value is None
        assert solution.diagnostics[0].code == "ALTITUDE_INVALID"


def test_geopotential_entry_has_the_same_range():
    low, high = (u.geopotential_altitude(z) for z in u.GEOMETRIC_ALTITUDE_RANGE)
    assert u.state_at_geopotential(low).value is not None
    assert u.state_at_geopotential(high).value is not None
    assert u.state_at_geopotential(high + 1e-6).value is None
    assert u.state_at_geopotential(84852.0).value is not None   # Table 4's top, now in range
