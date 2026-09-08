"""The weak and strong branches, their ordering, their merge, and detachment.

This is where a root-interval mistake would show. Splitting the wave-angle
range at the closed-form maximum is what makes each half monotone, so a solver
that searched the whole interval would return whichever root Brent happened to
land on -- and would sometimes swap them. The ordering test below is the one
that catches that.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.core.errors import DomainError, SubsonicShockError
from rocketforge.core.result import Status
from rocketforge.physics.compressible import PerfectGas, ShockBranch
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import oblique_shock as obl

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]
AIR = PerfectGas(gamma=1.4)
MACHS = (1.5, 2.0, 3.0, 5.0, 10.0)


def interior_deflections(mach1, gas, count=9):
    """Deflections strictly inside (0, theta_max)."""
    limit = obl.theta_max(mach1, gas).unwrap().theta_max
    return [limit * fraction for fraction in
            [(index + 1) / (count + 1) for index in range(count)]]


# ---------------------------------------------------------------------------
# both roots exist, and in the right order
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_the_branches_are_ordered_around_the_maximum(gas, mach1):
    """mu < beta_weak < beta_at_theta_max < beta_strong < pi/2.

    The single assertion that a root-interval error cannot survive.
    """
    mu = float(iso.mach_angle(mach1))
    peak = obl.theta_max(mach1, gas).unwrap().beta_at_theta_max
    for theta in interior_deflections(mach1, gas):
        weak = obl.beta_from_theta(mach1, theta, gas, ShockBranch.WEAK).unwrap()
        strong = obl.beta_from_theta(mach1, theta, gas, ShockBranch.STRONG).unwrap()
        assert mu < weak < peak < strong < 0.5 * math.pi, (mach1, math.degrees(theta))


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_both_roots_actually_produce_the_requested_deflection(gas, mach1):
    """Not "beta looks about right": the residual is checked on both branches."""
    for theta in interior_deflections(mach1, gas):
        for branch in (ShockBranch.WEAK, ShockBranch.STRONG):
            beta = obl.beta_from_theta(mach1, theta, gas, branch).unwrap()
            residual = float(obl.theta_from_beta(beta, mach1, gas)) - theta
            assert abs(residual) < 1e-9, (mach1, branch, math.degrees(theta), residual)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_each_root_lands_inside_its_own_bracket(gas, mach1):
    mu = float(iso.mach_angle(mach1))
    peak = obl.theta_max(mach1, gas).unwrap().beta_at_theta_max
    for theta in interior_deflections(mach1, gas, count=5):
        weak = obl.beta_from_theta(mach1, theta, gas, ShockBranch.WEAK)
        strong = obl.beta_from_theta(mach1, theta, gas, ShockBranch.STRONG)
        assert mu <= weak.unwrap() <= peak
        assert peak <= strong.unwrap() <= 0.5 * math.pi
        for solution in (weak, strong):
            assert solution.convergence is not None
            assert solution.convergence.converged
            assert abs(solution.convergence.residual) <= 1e-9


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_the_strong_branch_costs_more_stagnation_pressure(gas, mach1):
    """The physical distinction between the branches, on an interior grid."""
    for theta in interior_deflections(mach1, gas):
        pair = obl.solve_both(mach1, theta, gas).unwrap()
        assert pair.strong.stagnation_pressure_ratio < pair.weak.stagnation_pressure_ratio
        assert pair.strong.pressure_ratio > pair.weak.pressure_ratio
        assert pair.strong.mach2 < pair.weak.mach2
        assert pair.strong.entropy_change > pair.weak.entropy_change


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_the_strong_branch_is_always_subsonic_behind(gas, mach1):
    """True as a computed fact here, and still not what defines the branch."""
    for theta in interior_deflections(mach1, gas):
        pair = obl.solve_both(mach1, theta, gas).unwrap()
        assert pair.strong.downstream_supersonic is False
        assert pair.strong.mach2 < 1.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_the_weak_branch_is_not_always_supersonic_behind(gas, mach1):
    """The trap this module refuses to fall into.

    Near the maximum deflection a weak solution is already subsonic behind,
    because the sonic wave angle sits below the angle of maximum deflection. A
    module that hard-coded "weak = supersonic" would be wrong here.
    """
    # The subsonic band is bounded by two computed angles, so it is located by
    # them rather than by a fraction of theta_max: at M1 = 10 the band is only
    # a thousandth of a degree wide and any fixed fraction would miss it.
    sonic = obl.beta_sonic(mach1, gas).unwrap()
    peak = obl.theta_max(mach1, gas).unwrap().beta_at_theta_max
    assert sonic < peak
    inside = 0.5 * (sonic + peak)
    theta = float(obl.theta_from_beta(inside, mach1, gas))

    near = obl.solve(mach1, theta, gas, ShockBranch.WEAK).unwrap()
    assert near.branch is ShockBranch.WEAK
    assert near.beta < peak, "still the weak root"
    assert near.downstream_supersonic is False

    limit = obl.theta_max(mach1, gas).unwrap().theta_max
    modest = obl.solve(mach1, limit * 0.3, gas, ShockBranch.WEAK).unwrap()
    assert modest.downstream_supersonic is True


# ---------------------------------------------------------------------------
# the reference cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mach1,theta_deg,beta_weak,beta_strong,mach2_weak,p_weak,mach2_strong,p_strong", [
        (2.0, 10, 39.31393184, 83.70008038, 1.64052223, 1.70657860, 0.60369764, 4.44380721),
        (2.0, 20, 53.42294053, 74.27013704, 1.21021840, 2.84286271, 0.72778855, 4.15701686),
        (3.0, 20, 37.76363415, 82.14667102, 1.99413167, 3.77125746, 0.53936286, 10.13729988),
        (5.0, 30, 42.34426480, 80.64342348, 2.13564125, 13.06668858, 0.53827016, 28.22907617),
    ])
def test_solved_reference_cases_for_air(mach1, theta_deg, beta_weak, beta_strong,
                                        mach2_weak, p_weak, mach2_strong, p_strong):
    """Specification section 11.5, to every digit it prints, on both branches."""
    pair = obl.solve_both(mach1, math.radians(theta_deg), AIR).unwrap()
    assert math.degrees(pair.weak.beta) == pytest.approx(beta_weak, abs=5e-9)
    assert math.degrees(pair.strong.beta) == pytest.approx(beta_strong, abs=5e-9)
    assert pair.weak.mach2 == pytest.approx(mach2_weak, abs=5e-9)
    assert pair.weak.pressure_ratio == pytest.approx(p_weak, abs=5e-9)
    assert pair.strong.mach2 == pytest.approx(mach2_strong, abs=5e-9)
    assert pair.strong.pressure_ratio == pytest.approx(p_strong, abs=5e-9)


# ---------------------------------------------------------------------------
# zero deflection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_zero_deflection_gives_the_mach_wave_or_the_normal_shock(gas, mach1):
    """Both are real solutions; the branch says which, and neither is invented."""
    mu = float(iso.mach_angle(mach1))
    weak = obl.beta_from_theta(mach1, 0.0, gas, ShockBranch.WEAK)
    strong = obl.beta_from_theta(mach1, 0.0, gas, ShockBranch.STRONG)
    assert weak.unwrap() == pytest.approx(mu, rel=1e-15)
    assert strong.unwrap() == pytest.approx(0.5 * math.pi, rel=1e-15)
    assert any(d.code == "SONIC_EXACT" for d in weak.diagnostics)


def test_zero_deflection_does_not_iterate(monkeypatch):
    from rocketforge.physics.compressible import oblique_shock as module

    def forbidden(*args, **kwargs):  # pragma: no cover - only on failure
        raise AssertionError("a zero-deflection wave needs no root solve")

    monkeypatch.setattr(module, "brent", forbidden)
    assert obl.beta_from_theta(3.0, 0.0, AIR, ShockBranch.WEAK).ok
    assert obl.beta_from_theta(3.0, 0.0, AIR, ShockBranch.STRONG).ok


# ---------------------------------------------------------------------------
# the merge at theta_max
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
def test_at_the_maximum_the_two_branches_are_one(gas, mach1):
    limit = obl.theta_max(mach1, gas).unwrap()
    for branch in (ShockBranch.WEAK, ShockBranch.STRONG):
        solution = obl.beta_from_theta(mach1, limit.theta_max, gas, branch)
        assert solution.unwrap() == pytest.approx(limit.beta_at_theta_max, rel=1e-12)
        assert any(d.code == "BRANCH_ASSUMED" for d in solution.diagnostics)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
@pytest.mark.parametrize("epsilon", [1e-2, 1e-4, 1e-6, 1e-8])
def test_the_roots_approach_the_maximum_from_opposite_sides_and_never_cross(gas, mach1, epsilon):
    """The conditioning test. As the deflection nears its maximum the two wave
    angles coalesce, and the one thing that must never happen is that they swap."""
    limit = obl.theta_max(mach1, gas).unwrap()
    theta = limit.theta_max * (1.0 - epsilon)
    weak = obl.beta_from_theta(mach1, theta, gas, ShockBranch.WEAK).unwrap()
    strong = obl.beta_from_theta(mach1, theta, gas, ShockBranch.STRONG).unwrap()
    assert weak <= limit.beta_at_theta_max <= strong
    assert weak < strong


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_gap_between_the_roots_shrinks_as_the_maximum_is_approached(gas):
    limit = obl.theta_max(3.0, gas).unwrap()
    gaps = []
    for epsilon in (1e-2, 1e-4, 1e-6):
        theta = limit.theta_max * (1.0 - epsilon)
        weak = obl.beta_from_theta(3.0, theta, gas, ShockBranch.WEAK).unwrap()
        strong = obl.beta_from_theta(3.0, theta, gas, ShockBranch.STRONG).unwrap()
        gaps.append(strong - weak)
    assert gaps[0] > gaps[1] > gaps[2] > 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_approaching_the_maximum_warns_that_the_wave_angle_is_ill_determined(gas):
    limit = obl.theta_max(3.0, gas).unwrap().theta_max
    near = obl.beta_from_theta(3.0, limit * 0.9995, gas, ShockBranch.WEAK)
    assert any(d.code == "NEAR_THETA_MAX" for d in near.diagnostics)
    ordinary = obl.beta_from_theta(3.0, limit * 0.5, gas, ShockBranch.WEAK)
    assert not any(d.code == "NEAR_THETA_MAX" for d in ordinary.diagnostics)


# ---------------------------------------------------------------------------
# detachment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", MACHS)
@pytest.mark.parametrize("excess", [1e-6, 1e-3, 0.05, 0.5])
def test_beyond_the_maximum_there_is_no_attached_shock(gas, mach1, excess):
    """A physical classification, never a numerical failure.

    The status is NO_SOLUTION with a DETACHED_SHOCK diagnostic -- not a
    BracketError, not NOT_CONVERGED, not a NaN, and above all not a fabricated
    attached solution.
    """
    limit = obl.theta_max(mach1, gas).unwrap().theta_max
    theta = limit * (1.0 + excess) + 1e-9
    for branch in (ShockBranch.WEAK, ShockBranch.STRONG):
        solution = obl.beta_from_theta(mach1, theta, gas, branch)
        assert solution.status is Status.NO_SOLUTION
        assert solution.value is None
        codes = {d.code for d in solution.diagnostics}
        assert codes == {"DETACHED_SHOCK"} or "DETACHED_SHOCK" in codes
        assert "NOT_CONVERGED" not in codes


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_full_solve_also_detaches_rather_than_substituting_theta_max(gas):
    limit = obl.theta_max(2.0, gas).unwrap().theta_max
    solution = obl.solve(2.0, limit + math.radians(2.0), gas)
    assert solution.status is Status.NO_SOLUTION
    assert solution.value is None
    detail = next(d for d in solution.diagnostics if d.code == "DETACHED_SHOCK").detail
    assert detail["theta_max"] == pytest.approx(limit, rel=1e-12)


def test_the_detachment_message_says_what_the_limit_was():
    solution = obl.solve(2.0, math.radians(30.0), AIR)
    message = next(d for d in solution.diagnostics if d.code == "DETACHED_SHOCK").message
    assert "30.0000" in message and "22.9735" in message
    assert "detached bow shock" in message


def test_solve_both_reports_detachment_once_rather_than_twice():
    solution = obl.solve_both(2.0, math.radians(30.0), AIR)
    assert solution.status is Status.NO_SOLUTION
    assert solution.value is None
    assert sum(d.code == "DETACHED_SHOCK" for d in solution.diagnostics) == 1


# ---------------------------------------------------------------------------
# the branch contract
# ---------------------------------------------------------------------------


def test_the_default_branch_is_weak_and_says_so():
    default = obl.solve(3.0, math.radians(15.0), AIR)
    explicit = obl.solve(3.0, math.radians(15.0), AIR, ShockBranch.WEAK)
    assert default.unwrap().branch is ShockBranch.WEAK
    assert default.unwrap().beta == pytest.approx(explicit.unwrap().beta, rel=1e-15)


def test_the_strong_branch_carries_its_own_advisory():
    solution = obl.solve(3.0, math.radians(15.0), AIR, ShockBranch.STRONG)
    assert any(d.code == "STRONG_BRANCH_UNSTABLE" for d in solution.diagnostics)
    message = next(d.message for d in solution.diagnostics
                   if d.code == "STRONG_BRANCH_UNSTABLE")
    assert "downstream conditions" in message


def test_both_is_a_request_and_never_a_result():
    pair = obl.solve_both(3.0, math.radians(15.0), AIR).unwrap()
    assert pair.weak.branch is ShockBranch.WEAK
    assert pair.strong.branch is ShockBranch.STRONG
    with pytest.raises(ValueError, match="solve_both"):
        obl.solve(3.0, math.radians(15.0), AIR, ShockBranch.BOTH)
    with pytest.raises(ValueError, match="solve_both"):
        obl.beta_from_theta(3.0, math.radians(15.0), AIR, ShockBranch.BOTH)


def test_a_branch_must_be_a_branch():
    with pytest.raises(ValueError, match="ShockBranch"):
        obl.beta_from_theta(3.0, math.radians(15.0), AIR, "weak")


# ---------------------------------------------------------------------------
# domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [1.0, 0.9, 0.0, -2.0])
def test_the_inverse_refuses_subsonic_upstream(bad):
    with pytest.raises(SubsonicShockError):
        obl.beta_from_theta(bad, math.radians(5.0), AIR, ShockBranch.WEAK)


@pytest.mark.parametrize("bad", [-1e-9, -0.2])
def test_a_negative_deflection_is_refused(bad):
    with pytest.raises(DomainError, match=">= 0"):
        obl.beta_from_theta(3.0, bad, AIR, ShockBranch.WEAK)


@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_a_non_finite_deflection_is_refused(bad):
    with pytest.raises(DomainError):
        obl.beta_from_theta(3.0, bad, AIR, ShockBranch.WEAK)


def test_the_inverse_describes_one_shock():
    import numpy as np

    with pytest.raises(DomainError, match="scalar"):
        obl.beta_from_theta(3.0, np.array([0.1, 0.2]), AIR, ShockBranch.WEAK)
