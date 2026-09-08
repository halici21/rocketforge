"""The theta-beta-M relation, its two closed forms, and the downstream state.

Branch behaviour and the reuse audit have files of their own; this one covers
the forward relation, the analytic maximum, the sonic wave angle, and the
physical invariants of an attached shock.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError, SubsonicShockError
from rocketforge.physics.compressible import PerfectGas, ShockBranch
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import normal_shock as ns
from rocketforge.physics.compressible import oblique_shock as obl

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]
AIR = PerfectGas(gamma=1.4)
MACHS = (1.2, 1.5, 2.0, 3.0, 5.0, 10.0)


def wave_angles(mach1, gas, count=400, margin=1e-6):
    """A grid of admissible wave angles for one Mach number."""
    mu = float(iso.mach_angle(mach1))
    return np.linspace(mu + margin, 0.5 * math.pi - margin, count)


# ---------------------------------------------------------------------------
# the forward relation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_theta_matches_its_closed_form(gas, mach1):
    gamma = gas.gamma
    for beta in wave_angles(mach1, gas, count=25):
        numerator = mach1**2 * math.sin(beta) ** 2 - 1.0
        denominator = mach1**2 * (gamma + math.cos(2.0 * beta)) + 2.0
        expected = math.atan(2.0 / math.tan(beta) * numerator / denominator)
        assert obl.theta_from_beta(beta, mach1, gas) == pytest.approx(expected, abs=1e-14)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_both_ends_of_the_range_turn_the_flow_through_nothing(gas, mach1):
    """A Mach wave at the Mach angle, a normal shock at a right angle."""
    mu = float(iso.mach_angle(mach1))
    assert obl.theta_from_beta(mu, mach1, gas) == 0.0
    assert obl.theta_from_beta(0.5 * math.pi, mach1, gas) == 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_theta_rises_to_a_single_maximum_and_falls_back(gas, mach1):
    """The shape the whole branch structure depends on, checked numerically.

    Not "the chart looks right": the deflection is sampled densely, required to
    be positive in the interior, and its derivative required to change sign
    exactly once.
    """
    grid = wave_angles(mach1, gas, count=4001)
    theta = np.asarray(obl.theta_from_beta(grid, mach1, gas))
    assert np.all(theta > 0.0)

    slope = np.diff(theta)
    assert slope[0] > 0.0 and slope[-1] < 0.0
    sign_changes = np.count_nonzero(np.diff(np.sign(slope)) != 0)
    assert sign_changes == 1, "the deflection must have exactly one maximum"


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_theta_accepts_arrays_and_broadcasts_against_mach(gas):
    betas = np.linspace(0.6, 1.4, 9)
    result = obl.theta_from_beta(betas, 3.0, gas)
    assert isinstance(result, np.ndarray) and result.shape == betas.shape
    for index, beta in enumerate(betas):
        assert result[index] == pytest.approx(float(obl.theta_from_beta(float(beta), 3.0, gas)),
                                              rel=1e-14, abs=1e-16)


# ---------------------------------------------------------------------------
# domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [1.0, 0.999, 0.5, 0.0, -1.0])
def test_subsonic_upstream_is_refused(bad):
    with pytest.raises(SubsonicShockError):
        obl.theta_from_beta(0.8, bad, AIR)


@pytest.mark.parametrize("mach1", MACHS)
def test_a_wave_angle_below_the_mach_angle_is_refused(mach1):
    mu = float(iso.mach_angle(mach1))
    with pytest.raises(DomainError, match="Mach angle"):
        obl.theta_from_beta(mu - 1e-3, mach1, AIR)


def test_a_wave_angle_past_a_right_angle_is_refused():
    with pytest.raises(DomainError):
        obl.theta_from_beta(0.5 * math.pi + 1e-3, 3.0, AIR)


@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_non_finite_angles_rejected(bad):
    with pytest.raises(DomainError):
        obl.theta_from_beta(bad, 3.0, AIR)


# ---------------------------------------------------------------------------
# theta_max, in closed form
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_theta_max_agrees_with_an_independent_maximisation(gas, mach1):
    """The closed form is the answer; the search is only the oracle.

    A golden-section search over the admissible range, written here and nowhere
    in production, must find the same maximum. Four hundred iterations against
    one square root.
    """
    result = obl.theta_max(mach1, gas).unwrap()

    def negative(beta):
        return -float(obl.theta_from_beta(beta, mach1, gas))

    low = float(iso.mach_angle(mach1)) + 1e-9
    high = 0.5 * math.pi - 1e-9
    ratio = 0.5 * (math.sqrt(5.0) - 1.0)
    a, b = low, high
    c, d = b - ratio * (b - a), a + ratio * (b - a)
    for _ in range(400):
        if negative(c) < negative(d):
            b, d = d, c
            c = b - ratio * (b - a)
        else:
            a, c = c, d
            d = a + ratio * (b - a)
    searched = 0.5 * (a + b)

    assert result.beta_at_theta_max == pytest.approx(searched, abs=1e-7)
    assert result.theta_max == pytest.approx(-negative(searched), rel=1e-9)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_no_wave_angle_turns_the_flow_further_than_theta_max(gas, mach1):
    limit = obl.theta_max(mach1, gas).unwrap().theta_max
    grid = wave_angles(mach1, gas, count=8001)
    assert np.max(obl.theta_from_beta(grid, mach1, gas)) <= limit + 1e-12


@pytest.mark.parametrize("mach1,theta_max_deg,beta_deg,mu_deg", [
    (1.2, 3.94418698, 71.97654795, 56.44269),
    (1.5, 12.11266889, 66.58887589, 41.81031),
    (2.0, 22.97353176, 64.66897983, 30.00000),
    (3.0, 34.07343978, 65.24084545, 19.47122),
    (5.0, 41.11766310, 66.58424395, 11.53696),
    (10.0, 44.42901938, 67.45435106, 5.73917),
])
def test_theta_max_reference_values_for_air(mach1, theta_max_deg, beta_deg, mu_deg):
    """Specification section 11.5, to every digit it prints."""
    result = obl.theta_max(mach1, AIR).unwrap()
    assert math.degrees(result.theta_max) == pytest.approx(theta_max_deg, abs=5e-9)
    assert math.degrees(result.beta_at_theta_max) == pytest.approx(beta_deg, abs=5e-9)
    assert math.degrees(result.mach_angle) == pytest.approx(mu_deg, abs=5e-6)


def test_theta_max_reference_values_for_other_gammas():
    """Section 11.5: the gamma dependence at M1 = 2 is strong and is checked."""
    for gamma, expected in ((1.2, 26.79177125), (1.3, 24.72935680), (1.66, 19.42123489)):
        result = obl.theta_max(2.0, PerfectGas(gamma=gamma)).unwrap()
        assert math.degrees(result.theta_max) == pytest.approx(expected, abs=5e-9)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_theta_max_grows_with_mach_and_saturates(gas):
    limits = [obl.theta_max(m, gas).unwrap().theta_max for m in (1.5, 2.0, 3.0, 5.0, 10.0, 40.0)]
    assert all(b > a for a, b in zip(limits, limits[1:]))
    assert limits[-1] - limits[-2] < limits[1] - limits[0]


def test_theta_max_needs_no_iteration(monkeypatch):
    """Closed form means closed form: nothing here may reach the root solver."""
    from rocketforge.physics.compressible import oblique_shock as module

    def forbidden(*args, **kwargs):  # pragma: no cover - only on failure
        raise AssertionError("theta_max must not iterate")

    monkeypatch.setattr(module, "brent", forbidden)
    assert obl.theta_max(3.0, AIR).unwrap().theta_max > 0.0
    assert obl.beta_sonic(3.0, AIR).unwrap() > 0.0
    assert obl.solve_from_beta(3.0, 0.9, AIR).ok


# ---------------------------------------------------------------------------
# beta_sonic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_the_sonic_wave_angle_really_gives_sonic_flow_behind(gas, mach1):
    """The definition, put through the whole solution chain."""
    beta = obl.beta_sonic(mach1, gas).unwrap()
    result = obl.solve_from_beta(mach1, beta, gas).unwrap()
    assert result.mach2 == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_the_sonic_wave_angle_sits_below_the_maximum_deflection_angle(gas, mach1):
    """Which is why "weak" does not mean "supersonic behind"."""
    sonic = obl.beta_sonic(mach1, gas).unwrap()
    peak = obl.theta_max(mach1, gas).unwrap().beta_at_theta_max
    assert sonic < peak


@pytest.mark.parametrize("mach1,expected_deg", [
    (1.2, 68.07572881), (1.5, 62.25682634), (2.0, 61.48537164),
    (3.0, 63.76660294), (5.0, 66.08399728), (10.0, 67.33509986),
])
def test_beta_sonic_reference_values_for_air(mach1, expected_deg):
    assert math.degrees(obl.beta_sonic(mach1, AIR).unwrap()) == pytest.approx(
        expected_deg, abs=5e-9)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_downstream_supersonic_flag_matches_the_sonic_wave_angle(gas, mach1):
    """The flag is computed, not inferred from the branch name."""
    sonic = obl.beta_sonic(mach1, gas).unwrap()
    below = obl.solve_from_beta(mach1, sonic * 0.98, gas).unwrap()
    above = obl.solve_from_beta(mach1, min(sonic * 1.02, 0.5 * math.pi), gas).unwrap()
    assert below.downstream_supersonic is True
    assert above.downstream_supersonic is False


# ---------------------------------------------------------------------------
# the two limits
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_a_right_angle_reproduces_the_normal_shock_exactly(gas, mach1):
    """The blocking cross-module check: beta = 90 degrees IS a normal shock."""
    oblique = obl.solve_from_beta(mach1, 0.5 * math.pi, gas).unwrap()
    normal = ns.solve(mach1, gas)

    assert oblique.theta == 0.0
    assert oblique.mach_normal1 == pytest.approx(mach1, rel=1e-15)
    assert oblique.mach2 == pytest.approx(normal.mach2, rel=1e-15)
    assert oblique.pressure_ratio == pytest.approx(normal.pressure_ratio, rel=1e-15)
    assert oblique.density_ratio == pytest.approx(normal.density_ratio, rel=1e-15)
    assert oblique.temperature_ratio == pytest.approx(normal.temperature_ratio, rel=1e-15)
    assert oblique.stagnation_pressure_ratio == pytest.approx(
        normal.stagnation_pressure_ratio, rel=1e-15)
    assert oblique.entropy_change == pytest.approx(normal.entropy_change, rel=1e-15)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
@pytest.mark.parametrize("epsilon", [1e-3, 1e-5, 1e-7])
def test_the_mach_angle_limit_is_a_wave_of_no_strength(gas, mach1, epsilon):
    """As beta -> mu the shock vanishes: every ratio tends to 1 and M2 to M1."""
    mu = float(iso.mach_angle(mach1))
    result = obl.solve_from_beta(mach1, mu + epsilon, gas).unwrap()
    tolerance = max(200.0 * epsilon, 1e-9)
    assert result.theta == pytest.approx(0.0, abs=tolerance)
    assert result.pressure_ratio == pytest.approx(1.0, abs=tolerance)
    assert result.density_ratio == pytest.approx(1.0, abs=tolerance)
    assert result.temperature_ratio == pytest.approx(1.0, abs=tolerance)
    assert result.stagnation_pressure_ratio == pytest.approx(1.0, abs=tolerance)
    assert result.mach2 == pytest.approx(mach1, abs=tolerance * mach1)


# ---------------------------------------------------------------------------
# physical invariants of an attached shock
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_every_attached_shock_compresses_and_costs_stagnation_pressure(gas, mach1):
    for beta in wave_angles(mach1, gas, count=60, margin=1e-3):
        result = obl.solve_from_beta(mach1, float(beta), gas).unwrap()
        assert result.mach_normal1 > 1.0
        assert result.mach_normal2 < 1.0
        assert result.pressure_ratio > 1.0
        assert result.density_ratio > 1.0
        assert result.temperature_ratio > 1.0
        assert 0.0 < result.stagnation_pressure_ratio < 1.0
        assert result.stagnation_temperature_ratio == 1.0
        assert result.entropy_change > 0.0
        assert result.mach2 > 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_the_downstream_mach_is_the_normal_component_over_the_turned_sine(gas, mach1):
    """M2 = Mn2 / sin(beta - theta): the geometry that closes the solution."""
    for beta in wave_angles(mach1, gas, count=30, margin=1e-3):
        result = obl.solve_from_beta(mach1, float(beta), gas).unwrap()
        assert result.mach2 == pytest.approx(
            result.mach_normal2 / math.sin(result.beta - result.theta), rel=1e-14)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_the_normal_component_is_the_upstream_mach_times_the_sine(gas, mach1):
    for beta in wave_angles(mach1, gas, count=30, margin=1e-3):
        result = obl.solve_from_beta(mach1, float(beta), gas).unwrap()
        assert result.mach_normal1 == pytest.approx(mach1 * math.sin(float(beta)), rel=1e-14)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_downstream_flow_angle_is_the_deflection_not_the_wave_angle(gas):
    """A confusion worth a test: the flow turns by theta, not by beta."""
    result = obl.solve_from_beta(3.0, 0.7, gas).unwrap()
    assert result.downstream_flow_angle == result.theta
    assert result.downstream_flow_angle != result.beta


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_ideal_gas_law_holds_across_the_shock(gas):
    for beta in (0.6, 0.9, 1.2, 1.5):
        result = obl.solve_from_beta(4.0, beta, gas).unwrap()
        assert result.pressure_ratio == pytest.approx(
            result.density_ratio * result.temperature_ratio, rel=1e-14)


def test_solve_from_beta_reports_the_branch_rather_than_choosing_it():
    peak = obl.theta_max(3.0, AIR).unwrap().beta_at_theta_max
    assert obl.solve_from_beta(3.0, peak * 0.8, AIR).unwrap().branch is ShockBranch.WEAK
    assert obl.solve_from_beta(3.0, peak * 1.1, AIR).unwrap().branch is ShockBranch.STRONG


def test_solve_from_beta_describes_one_shock():
    with pytest.raises(DomainError):
        obl.solve_from_beta(3.0, np.array([0.7, 0.9]), AIR)
