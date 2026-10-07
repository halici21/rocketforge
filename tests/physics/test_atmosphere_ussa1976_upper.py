"""ENV-1B: the U.S. Standard Atmosphere, 1976, from 80 km to 1000 km.

**References, not the implementation.** Every reference below was read from
the Standard's printed tables (NTRS 19770009539): Table VIII (composition,
pp. 225-230 of the scan), Table I (T, P, rho; pp. 83-88), Table II (N, M;
pp. 107-112), Table 9 and Appendix A. A few rows come from Sutton &
Biblarz, Appendix 2, which cites the Standard. None was produced by this code.

Tolerances follow the printing. Four-figure values are checked to within one
unit of the last printed digit: the tables round in some columns and truncate
in others, and the 1976 program's own integration differs from an exact one
by a fraction of that unit. Table I pressures (five figures) are checked to
1e-4 relative: above 86 km pressure is N k T, summed from species that agree
to four figures. Temperatures are checked to their printed rounding.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.physics.atmosphere import ussa1976 as u
from rocketforge.physics.atmosphere import ussa1976_upper as up
from rocketforge.physics.atmosphere._dopri5 import integrate
from rocketforge.physics.atmosphere._ussa1976_constants import (
    AVOGADRO,
    BOLTZMANN,
    M0,
    R_STAR,
)

SPECIES = ("N2", "O", "O2", "Ar", "He", "H")

#: Table VIII, number densities (m^-3), as printed. None: not tabulated.
TABLE_VIII = {
    86: ("1.130e20", "8.600e16", "3.031e19", "1.351e18", "7.582e14", None),
    90: ("5.547e19", "2.443e17", "1.479e19", "6.574e17", "3.976e14", None),
    95: ("2.268e19", "4.365e17", "5.830e18", "2.583e17", "1.973e14", None),
    100: ("9.210e18", "4.298e17", "2.151e18", "9.501e16", "1.133e14", None),
    110: ("1.641e18", "2.303e17", "2.621e17", "1.046e16", "5.821e13", None),
    115: ("7.254e17", "1.428e17", "9.646e16", "3.386e15", "4.648e13", None),
    120: ("3.726e17", "9.275e16", "4.395e16", "1.366e15", "3.888e13", None),
    130: ("1.326e17", "4.625e16", "1.375e16", "3.458e14", "2.972e13", None),
    140: ("6.009e16", "2.729e16", "5.702e15", "1.205e14", "2.449e13", None),
    150: ("3.124e16", "1.780e16", "2.750e15", "5.000e13", "2.106e13", "3.767e11"),
    200: ("2.925e15", "4.050e15", "1.918e14", "1.938e12", "1.310e13", "1.630e11"),
    300: ("9.593e13", "5.433e14", "3.942e12", "1.568e10", "7.566e12", "1.049e11"),
    500: ("2.592e11", "1.836e13", "4.607e9", "3.445e6", "3.215e12", "8.000e10"),
    750: ("2.741e8", "3.666e11", "1.838e6", "1.967e2", "1.208e12", "6.249e10"),
    1000: ("4.626e5", "9.562e9", "1.251e3", "2.188e-2", "4.850e11", "4.967e10"),
}

#: Table I (geometric): km -> (T K, P mb, rho kg/m^3), as printed.
TABLE_I = {
    86: ("186.87", 3.7338e-3, "6.958e-6"), 90: ("186.87", 1.8359e-3, "3.416e-6"),
    95: ("188.42", 7.5966e-4, "1.393e-6"), 100: ("195.08", 3.2011e-4, "5.604e-7"),
    110: ("240.00", 7.1042e-5, "9.708e-8"), 120: ("360.00", 2.5382e-5, "2.222e-8"),
    130: ("469.27", 1.2505e-5, "8.152e-9"), 140: ("559.63", 7.2028e-6, "3.831e-9"),
    150: ("634.39", 4.5422e-6, "2.076e-9"), 200: ("854.56", 8.4736e-7, "2.541e-10"),
    300: ("976.01", 8.7704e-8, "1.916e-11"), 500: ("999.24", 3.0236e-9, "5.215e-13"),
    600: ("999.85", 8.2130e-10, "1.137e-13"),
    750: ("999.99", 2.2599e-10, "1.788e-14"), 1000: ("1000.00", 7.5138e-11, "3.561e-15"),
}

#: Table II (geometric): km -> (N m^-3, M kg/kmol), as printed.
TABLE_II = {86: ("1.447e20", "28.95"), 120: ("5.107e17", "26.20"),
            150: ("5.186e16", "24.10"), 200: ("7.182e15", "21.30"),
            230: ("3.106e15", "19.95"), 500: ("2.192e13", "14.33"),
            850: ("9.717e11", "4.85")}

#: Sutton Appendix 2 rows not read from Table I: km -> (T, P/P0, rho). At
#: 600 km Sutton prints rho 2.137e-13; Table I prints 1.137e-13 (a misprint,
#: tested below), so that value is not used.
SUTTON = {160: ("696.29", "2.9997e-9", "1.233e-9"), 400: ("995.83", "1.4328e-11", "2.803e-12"),
          600: ("999.85", "8.1056e-13", None)}


def unit(printed: str) -> float:
    mantissa, _, exponent = printed.lower().partition("e")
    decimals = len(mantissa.split(".")[1]) if "." in mantissa else 0
    return 10.0 ** ((int(exponent) if exponent else 0) - decimals)


def within_one_unit(value: float, printed: str) -> bool:
    return abs(value - float(printed)) <= unit(printed) * (1 + 1e-9)


def rounds_to(value: float, printed: str) -> bool:
    return abs(value - float(printed)) <= 0.5 * unit(printed) * (1 + 1e-9)


def at_km(z_km: float):
    solution = u.state(z_km * 1000.0)
    assert solution.value is not None, solution.diagnostics
    return solution.value


# ===========================================================================
# the Standard's tables
# ===========================================================================


@pytest.mark.parametrize("z", sorted(TABLE_VIII))
def test_table_viii_composition(z):
    s = at_km(z)
    for name, printed in zip(SPECIES, TABLE_VIII[z]):
        if printed is None:
            assert name not in s.species_number_densities
        else:
            value = s.species_number_densities[name]
            assert within_one_unit(value, printed), (z, name, value, printed)


@pytest.mark.parametrize("z", sorted(TABLE_I))
def test_table_i_temperature_pressure_density(z):
    t, p_mb, rho = TABLE_I[z]
    s = at_km(z)
    assert rounds_to(s.temperature, t), s.temperature
    assert s.pressure == pytest.approx(p_mb * 100.0, rel=1e-4)
    assert within_one_unit(s.density, rho), s.density


@pytest.mark.parametrize("z", sorted(TABLE_II))
def test_table_ii_number_density_and_molecular_weight(z):
    n, m = TABLE_II[z]
    s = at_km(z)
    assert within_one_unit(s.number_density, n), s.number_density
    assert within_one_unit(s.mean_molar_mass, m), s.mean_molar_mass


@pytest.mark.parametrize("z", sorted(SUTTON))
def test_sutton_appendix_2_upper_rows(z):
    t, ratio, rho = SUTTON[z]
    s = at_km(z)
    assert rounds_to(s.temperature, t)
    assert s.pressure / u.P0 == pytest.approx(float(ratio), rel=1e-4)
    if rho is not None:
        assert within_one_unit(s.density, rho)


def test_sutton_upper_misprints():
    """Sutton prints 845.56 K at 200 km (Table I: 854.56) and rho 2.137e-13 at
    600 km (Table I: 1.137e-13)."""
    assert rounds_to(at_km(200).temperature, "854.56")
    assert not rounds_to(at_km(200).temperature, "845.56")
    assert within_one_unit(at_km(600).density, "1.137e-13")
    assert not within_one_unit(at_km(600).density, "2.137e-13")


def test_table_9_and_appendix_a_at_86_km():
    s = at_km(86)
    assert s.species_number_densities == {k: pytest.approx(v, rel=1e-13)
                                          for k, v in up.N_7.items()}
    assert s.number_density == pytest.approx(1.447265163e20, rel=2e-7)      # Table 26
    assert s.mean_molar_mass == pytest.approx(28.9522082, rel=2e-8)          # Table 26
    assert s.density == pytest.approx(6.957880e-6, rel=2e-7)                 # Appendix A


# ===========================================================================
# temperature (eqs. 25-32) and Appendix B
# ===========================================================================


def test_temperature_segments_meet_with_the_standards_slopes():
    assert up.temperature(86.0) == up.temperature(90.999) == up.T7
    assert up.temperature(91.0) == pytest.approx(up.T7, abs=1e-12)
    assert up.dtemperature_dz(91.0) == 0.0
    for z, t, slope in ((110.0, 240.0, 12.0), (120.0, 360.0, 12.0)):
        assert up.temperature(z - 1e-9) == pytest.approx(t, abs=1e-6)
        assert up.temperature(z) == pytest.approx(t, abs=1e-12)
        assert up.dtemperature_dz(z - 1e-9) == pytest.approx(slope, rel=1e-6)
        assert up.dtemperature_dz(z) == pytest.approx(slope, rel=1e-12)
    assert up.temperature(500.0) == pytest.approx(999.2356, abs=5e-5)        # T11, p. 14
    assert 999.9 < up.temperature(1000.0) < up.T_INF


def test_the_ellipse_constants_are_appendix_bs():
    """The module derives Tc, A and a from the defining conditions; rounded to
    four decimals they are the printed 263.1905 K, -76.3232 K, -19.9429 km."""
    assert round(up.TC, 4) == 263.1905
    assert round(up.A_ELLIPSE, 4) == -76.3232
    assert round(up.A_AXIS, 4) == -19.9429
    # The defining conditions, checked directly on the ellipse:
    x = (110.0 - 91.0) / up.A_AXIS
    assert up.TC + up.A_ELLIPSE * math.sqrt(1 - x * x) == pytest.approx(240.0, abs=1e-10)
    assert up.dtemperature_dz(110.0 - 1e-12) == pytest.approx(12.0, rel=1e-8)
    # Rounded constants would miss T9 by 2.7e-4 K:
    xr = 19.0 / -19.9429
    assert 263.1905 - 76.3232 * math.sqrt(1 - xr * xr) == pytest.approx(239.99973, abs=1e-5)


def test_temperature_derivative_is_the_derivative():
    for z in (92.0, 100.0, 109.0, 115.0, 130.0, 300.0, 800.0):
        h = 1e-5
        numeric = (up.temperature(z + h) - up.temperature(z - h)) / (2 * h)
        assert up.dtemperature_dz(z) == pytest.approx(numeric, rel=1e-6)


# ===========================================================================
# hydrogen
# ===========================================================================


def test_hydrogen_exists_from_150_km_only():
    assert "H" not in at_km(149.999).species_number_densities
    assert "H" in at_km(150.0).species_number_densities
    assert at_km(500.0).species_number_densities["H"] == pytest.approx(8.0e10, rel=1e-12)


def test_the_150_km_step_is_exactly_the_hydrogen_the_standard_adds():
    below, at150 = at_km(149.9999999), at_km(150.0)
    added = at150.species_number_densities["H"]
    assert at150.number_density - below.number_density == pytest.approx(added, rel=1e-3)
    assert added / at150.number_density == pytest.approx(7.26e-6, rel=1e-2)


def test_above_500_km_hydrogen_is_in_diffusive_equilibrium():
    """With the flux integral neglected (p. 14), n(H) T^0.75 e^tau is constant."""
    nodes = up._nodes()
    tau500 = nodes[500][5]
    for z in (600, 750, 1000):
        t = up.temperature(float(z))
        expected = up.N_H_11 * (up._T11 / t) ** 0.75 * math.exp(-(nodes[z][5] - tau500))
        assert at_km(z).species_number_densities["H"] == pytest.approx(expected, rel=1e-13)


def test_keeping_the_flux_above_500_km_would_miss_table_viii():
    """The term the Standard neglects would lower n(H) by ~0.3 % at 1000 km,
    three units of Table VIII's last digit."""
    nodes = up._nodes()
    tau500, g500 = nodes[500][5], nodes[500][6]
    z = 1000
    t = up.temperature(float(z))
    with_flux = ((up.N_H_11 - math.exp(-tau500) * (nodes[z][6] - g500))
                 * (up._T11 / t) ** 0.75 * math.exp(-(nodes[z][5] - tau500)))
    assert not within_one_unit(with_flux, "4.967e10")
    assert within_one_unit(at_km(z).species_number_densities["H"], "4.967e10")


# ===========================================================================
# boundaries: 80 km, 86 km
# ===========================================================================

QUANTITIES = ("pressure", "density", "temperature", "number_density", "mean_molar_mass",
              "molecular_scale_temperature")


def test_80_km_is_continuous():
    lo, at, hi = (u.state(80000.0 + d).value for d in (-1e-6, 0.0, 1e-6))
    for name in QUANTITIES:
        assert getattr(lo, name) == pytest.approx(getattr(at, name), rel=1e-9)
        assert getattr(hi, name) == pytest.approx(getattr(at, name), rel=1e-9)
    assert at.regime.startswith("lower") and hi.regime.startswith("transition")


def test_the_86_km_step_is_the_standards_own_and_is_explained():
    """The hydrostatic 80-86 km form and the species form at 86 km differ by
    ~1e-5. Both are the Standard's definitions; the step is not tolerated
    blindly but decomposed:

    * Table 9 / Appendix A take Z7 = 86 km as H7 = 84.8520 km' (Table 4), but
      eq. 18 maps 86 km to 84.85205 km'. At H = 84 852.0 m' the hydrostatic
      density is Appendix A's 6.957880e-6; at 84 852.05 m' it is 8.1e-6 lower.
    * In pressure, k = 1.380622e-23 exceeds R*/N_A by 2.29e-6 (p. 3).
    """
    below, above = u.state(86000.0 - 1e-6).value, u.state(86000.0).value
    rho_step = below.density / above.density - 1.0
    p_step = below.pressure / above.pressure - 1.0
    assert u.geopotential_altitude(86000.0) == pytest.approx(84852.0458, abs=1e-4)
    _, tm, p = u._hydrostatic(84852.0)
    assert p * M0 / (R_STAR * tm) == pytest.approx(6.957880e-6, rel=3e-7)
    _, tm86, p86 = u._hydrostatic(u.geopotential_altitude(86000.0))
    offset = (p86 * M0 / (R_STAR * tm86)) / (p * M0 / (R_STAR * tm)) - 1.0
    k_mismatch = BOLTZMANN / (R_STAR / AVOGADRO) - 1.0
    assert offset == pytest.approx(-7.89e-6, rel=1e-2)
    assert k_mismatch == pytest.approx(2.29e-6, rel=1e-2)
    # T7 = 186.8673 K is itself rounded: TM(86 km) M7/M0 (Appendix A's M7) is
    # 186.86722 K, 4.3e-7 lower.
    t_term = tm86 * (28.952208 / M0) / up.T7 - 1.0
    assert t_term == pytest.approx(-4.3e-7, rel=0.1)
    assert rho_step == pytest.approx(offset, abs=3e-7)
    assert p_step == pytest.approx(rho_step - k_mismatch + t_term, abs=5e-8)
    assert abs(p_step) < 1.2e-5 and abs(rho_step) < 1e-5
    assert below.temperature == pytest.approx(above.temperature, rel=1e-6)


def test_transition_uses_table_8_and_leaves_p_rho_cs_exact():
    for z, ratio in u.MOLECULAR_WEIGHT_RATIO[1:-1]:
        s = u.state(z).value
        assert s.mean_molar_mass == pytest.approx(M0 * ratio, rel=1e-15)
        assert s.temperature == pytest.approx(s.molecular_scale_temperature * ratio,
                                              rel=1e-15)
        assert s.density == pytest.approx(
            s.pressure * M0 / (R_STAR * s.molecular_scale_temperature), rel=1e-15)
        assert s.speed_of_sound == pytest.approx(
            math.sqrt(1.4 * R_STAR * s.molecular_scale_temperature / M0), rel=1e-15)
    # Table I prints the uncorrected TM-based T in 80-86 km (section 1.2.4);
    # Table 8 then gives T = 186.87 K at 86 km against TM 186.95 K.
    s = u.state(85999.0).value
    assert s.molecular_scale_temperature - s.temperature == pytest.approx(0.0787, abs=2e-3)


# ===========================================================================
# what is and is not defined
# ===========================================================================


def test_speed_of_sound_and_viscosity_end_at_86_km():
    at86 = at_km(86.0)
    assert at86.speed_of_sound is not None and at86.dynamic_viscosity is not None
    assert at86.speed_of_sound == pytest.approx(
        math.sqrt(1.4 * R_STAR * at86.temperature / at86.mean_molar_mass), rel=1e-15)
    for z in (86.001, 100.0, 500.0, 1000.0):
        s = at_km(z)
        assert s.speed_of_sound is None and s.dynamic_viscosity is None
        assert "1.3.10" in s.unavailable["speed_of_sound"]
        assert "1.3.11" in s.unavailable["dynamic_viscosity"]
    assert at_km(85.0).speed_of_sound is not None


def test_composition_is_reported_from_86_km():
    for z in (0.0, 50.0, 85.9):
        s = at_km(z)
        assert s.species_number_densities == {}
        assert "Table VIII" in s.unavailable["species_number_densities"]
    assert set(at_km(86.0).species_number_densities) == {"N2", "O", "O2", "Ar", "He"}
    assert set(at_km(200.0).species_number_densities) == set(SPECIES)


def test_upper_totals_are_their_definitions():
    for z in (90.0, 140.0, 333.3, 999.0):
        s = at_km(z)
        n = sum(s.species_number_densities.values())
        mass = sum(v * up.MOLAR_MASS[k] for k, v in s.species_number_densities.items())
        assert s.number_density == pytest.approx(n, rel=1e-15)
        assert s.pressure == pytest.approx(n * BOLTZMANN * s.temperature, rel=1e-15)
        assert s.density == pytest.approx(mass / AVOGADRO, rel=1e-15)
        assert s.mean_molar_mass == pytest.approx(mass / n, rel=1e-15)
        assert s.molecular_scale_temperature == pytest.approx(
            s.temperature * M0 / s.mean_molar_mass, rel=1e-15)
        # The Standard's k and R*/N_A differ by 2.29e-6 (p. 3), and it shows.
        assert s.density * R_STAR * s.temperature / (s.pressure * s.mean_molar_mass) == \
            pytest.approx(1 - 2.29e-6, abs=1e-8)


# ===========================================================================
# numerics, determinism, and a dense audit
# ===========================================================================


BREAKPOINTS = (91.0, 95.0, 97.0, 100.0, 110.0, 115.0, 120.0)


def _reference(z):
    """Straight from 86 km at a tighter tolerance, stopping only at the
    Standard's breakpoints (where coefficients change form), not at nodes."""
    y = [math.log(up.N_7[k] * up.T7) for k in ("N2", "O", "O2", "Ar", "He")]
    start = 86.0
    for stop in [b for b in BREAKPOINTS if b < z] + [z]:
        y = integrate(up._rates, start, y, stop, rtol=1e-15, atol=1e-15, first_step=0.01)
        start = stop
    return y


def test_node_continuation_equals_direct_integration():
    """A query between nodes continues the ODE from the node below; it must
    agree with an independent pass that ignores the node grid."""
    for z in (93.37, 117.5, 142.0):
        direct = _reference(z)
        t = up.temperature(z)
        for i, name in enumerate(("N2", "O", "O2", "Ar", "He")):
            assert at_km(z).species_number_densities[name] == pytest.approx(
                math.exp(direct[i]) / t, rel=1e-9)


def test_results_are_deterministic_and_order_independent():
    first = [at_km(z) for z in (700.0, 88.0, 150.5, 999.9)]
    up._nodes.cache_clear()
    second = [at_km(z) for z in (999.9, 150.5, 88.0, 700.0)][::-1]
    assert first == second


GRID = np.concatenate([np.linspace(80.0, 1000.0, 3681),
                       [b + d for b in (86.0, 91.0, 95.0, 97.0, 100.0, 110.0, 115.0,
                                        120.0, 150.0, 500.0) for d in (-1e-6, 1e-6)]])


def test_dense_audit_from_80_to_1000_km():
    previous = None
    for z in np.sort(GRID):
        s = at_km(float(z))
        assert 180.0 < s.temperature <= 1000.0
        for name in ("pressure", "density", "number_density", "mean_molar_mass"):
            assert math.isfinite(getattr(s, name)) and getattr(s, name) > 0.0
        if previous is not None:
            p = previous
            crosses_86 = p.geometric_altitude < 86000.0 <= s.geometric_altitude
            crosses_150 = p.geometric_altitude < 150000.0 <= s.geometric_altitude
            if crosses_150:
                # The Standard's second step: H joins at 150 km. Upward jumps,
                # bounded here; their exact size (the hydrogen added) is
                # test_the_150_km_step_is_exactly_the_hydrogen_the_standard_adds.
                assert 0 < s.number_density / p.number_density - 1 < 1e-5
                assert 0 < s.pressure / p.pressure - 1 < 1e-5
                assert 0 < s.density / p.density - 1 < 1e-6
                assert s.mean_molar_mass < p.mean_molar_mass
                previous = s
                continue
            if crosses_86:
                # The one non-monotonic point: the Standard's own 86 km step,
                # decomposed in test_the_86_km_step_is_the_standards_own_...
                for name in ("pressure", "density", "number_density"):
                    assert abs(getattr(s, name) / getattr(p, name) - 1) < 1.2e-5, name
                # Table 8's 0.999579 against Appendix A's M7/M0 = 0.99957908.
                assert abs(s.mean_molar_mass / p.mean_molar_mass - 1) < 1e-7
            else:
                assert s.pressure < p.pressure and s.density < p.density, z
                assert s.mean_molar_mass <= p.mean_molar_mass * (1 + 1e-12), z
            if not crosses_86 and not (z >= 150.0 > p.geometric_altitude / 1000.0):
                assert s.number_density < p.number_density, z      # H joins at 150 km
            for name, value in s.species_number_densities.items():
                assert value > 0.0, (z, name)
        previous = s
