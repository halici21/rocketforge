"""The Prandtl-Meyer function, its Mach angle companion, and the ceiling.

Angles are radians throughout the physics layer, so every assertion here is in
radians too; where a degree value from the specification is quoted it is
converted at the point of comparison rather than by a second implementation.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError, SubsonicExpansionError
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import prandtl_meyer as pm

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]
AIR = PerfectGas(gamma=1.4)


# ---------------------------------------------------------------------------
# the relation itself
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_nu_matches_its_closed_form(gas):
    gamma = gas.gamma
    ratio = math.sqrt((gamma + 1.0) / (gamma - 1.0))
    for mach in (1.0, 1.01, 1.5, 2.0, 3.0, 5.0, 10.0, 40.0):
        excess = mach * mach - 1.0
        expected = (ratio * math.atan(math.sqrt(excess) / ratio)
                    - math.atan(math.sqrt(excess)))
        assert pm.nu(mach, gas) == pytest.approx(expected, rel=1e-14, abs=1e-16)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_sonic_turning_is_exactly_zero(gas):
    """The one value in the whole relation that must be exact, not approximate."""
    assert pm.nu(1.0, gas) == 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_nu_increases_strictly_with_mach(gas):
    grid = np.linspace(1.0, 60.0, 20001)
    values = np.asarray(pm.nu(grid, gas))
    assert np.all(np.diff(values) > 0.0)
    assert values[0] == 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_nu_stays_below_its_supremum(gas):
    ceiling = pm.nu_max(gas)
    grid = np.linspace(1.0, 500.0, 5000)
    assert np.all(pm.nu(grid, gas) < ceiling)
    # ...and reaches it in the limit.
    assert pm.nu(1e7, gas) == pytest.approx(ceiling, rel=1e-6)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_nu_max_matches_its_closed_form(gas):
    gamma = gas.gamma
    expected = 0.5 * math.pi * (math.sqrt((gamma + 1.0) / (gamma - 1.0)) - 1.0)
    assert pm.nu_max(gas) == pytest.approx(expected, rel=1e-15)


def test_nu_max_reference_values():
    """The published maxima, in degrees, from the specification section 11.6."""
    for gamma, expected in ((1.2, 208.49623113), (1.3, 159.19871589),
                            (1.4, 130.4540768505), (1.66, 90.68053173)):
        assert math.degrees(pm.nu_max(PerfectGas(gamma=gamma))) == pytest.approx(
            expected, abs=5e-8)


@pytest.mark.parametrize("mach,expected_nu,expected_mu", [
    (1.0, 0.0000000000, 90.0000000000),
    (1.5, 11.9052088267, 41.8103148958),
    (2.0, 26.3797608134, 30.0000000000),
    (3.0, 49.7573467443, 19.4712206345),
    (5.0, 76.9202155085, 11.5369590328),
    (10.0, 102.3162531732, 5.7391704773),
])
def test_reference_values_for_air(mach, expected_nu, expected_mu):
    """Specification section 11.6, to every digit it prints."""
    assert math.degrees(pm.nu(mach, AIR)) == pytest.approx(expected_nu, abs=5e-10)
    assert math.degrees(pm.mach_angle(mach)) == pytest.approx(expected_mu, abs=5e-10)


def test_gamma_changes_the_answer():
    """Proof that gamma is used rather than air being assumed."""
    assert pm.nu(2.0, PerfectGas(gamma=1.2)) != pm.nu(2.0, PerfectGas(gamma=1.4))


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_nu_is_a_lower_gamma_larger_relation(gas):
    """A lower gamma turns further to reach the same Mach number.

    Physically: less energy goes into internal modes, so the flow accelerates
    less readily and more turning is needed. Worth asserting because it fixes
    the direction of the gamma dependence, which is easy to invert by mistake.
    """
    for mach in (1.5, 2.0, 5.0):
        assert pm.nu(mach, PerfectGas(gamma=1.2)) > pm.nu(mach, PerfectGas(gamma=1.66))


# ---------------------------------------------------------------------------
# the Mach angle is reused, not reimplemented
# ---------------------------------------------------------------------------


def test_mach_angle_is_the_isentropic_one():
    """Not a copy: the same function object, re-exported.

    The Mach angle is geometry and it already exists, verified, in the
    isentropic module. If this ever stopped being true there would be two
    definitions of asin(1/M) in the package, which is one too many.
    """
    assert pm.mach_angle is iso.mach_angle


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_mach_angle_decreases_from_a_right_angle(gas):
    assert pm.mach_angle(1.0) == pytest.approx(0.5 * math.pi, rel=1e-15)
    grid = np.linspace(1.0, 40.0, 5000)
    angles = np.asarray(pm.mach_angle(grid))
    assert np.all(np.diff(angles) < 0.0)
    assert angles[-1] > 0.0


def test_mach_angle_needs_no_gas():
    """Geometry, not gas dynamics: it takes no gamma and must not acquire one."""
    assert pm.mach_angle(2.0) == pytest.approx(math.asin(0.5), rel=1e-15)


# ---------------------------------------------------------------------------
# domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0.999999999, 0.5, 0.0, -2.0])
def test_subsonic_is_refused_with_its_own_error(bad):
    with pytest.raises(SubsonicExpansionError):
        pm.nu(bad, AIR)


def test_the_refusal_says_why():
    with pytest.raises(SubsonicExpansionError, match="supersonic"):
        pm.nu(0.5, AIR)


def test_subsonic_expansion_error_is_a_domain_error():
    assert issubclass(SubsonicExpansionError, DomainError)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_mach_rejected(bad):
    with pytest.raises(DomainError):
        pm.nu(bad, AIR)


def test_array_with_one_subsonic_element_raises_and_names_the_index():
    with pytest.raises(SubsonicExpansionError) as excinfo:
        pm.nu(np.array([2.0, 3.0, 0.5]), AIR)
    assert "index 2" in str(excinfo.value)


# ---------------------------------------------------------------------------
# scalar / array policy
# ---------------------------------------------------------------------------


def test_scalar_returns_float_and_array_returns_array():
    assert isinstance(pm.nu(2.0, AIR), float)
    result = pm.nu(np.array([1.0, 2.0, 3.0]), AIR)
    assert isinstance(result, np.ndarray) and result.dtype == np.float64


def test_array_and_scalar_paths_agree():
    grid = np.array([1.0, 1.5, 2.0, 7.0])
    vector = pm.nu(grid, AIR)
    for index, mach in enumerate(grid):
        assert vector[index] == pytest.approx(float(pm.nu(float(mach), AIR)), rel=1e-15)


# ---------------------------------------------------------------------------
# the derivative, and what it says about the inverse
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_derivative_matches_a_numerical_one(gas):
    for mach in (1.2, 2.0, 5.0):
        step = 1e-6
        numerical = (float(pm.nu(mach + step, gas)) - float(pm.nu(mach - step, gas))) / (2 * step)
        assert pm._derivative(mach, gas) == pytest.approx(numerical, rel=1e-8)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_derivative_vanishes_at_sonic(gas):
    """Why Brent and not Newton: a first Newton step from M = 1 is undefined."""
    assert pm._derivative(1.0, gas) == 0.0
    assert pm._derivative(1.0 + 1e-9, gas) > 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_near_sonic_follows_the_three_halves_power_law(gas):
    """nu ~ [4 sqrt(2) / (3(gamma+1))] (M-1)^(3/2) as M -> 1.

    The conditioning statement of the specification, asserted rather than
    quoted: it is what says how many digits of Mach survive an inversion from a
    small angle.
    """
    coefficient = 4.0 * math.sqrt(2.0) / (3.0 * (gas.gamma + 1.0))
    for excess in (1e-3, 1e-4, 1e-5, 1e-6):
        value = float(pm.nu(1.0 + excess, gas))
        expected = coefficient * excess ** 1.5
        assert value == pytest.approx(expected, rel=2.0 * math.sqrt(excess) + 1e-6)
