"""The three critical pressure ratios, and the ordering everything rests on.

``03`` section 10.4. Each critical is the exit pressure of a *different*
internal solution, and every one is computed from Ae/A* and gamma -- there is
no hard-coded pressure anywhere in the classifier, which is what these tests
exist to keep true.
"""

from __future__ import annotations

import pytest

from rocketforge.core.errors import GeometryError
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import normal_shock as shock
from rocketforge.physics.compressible import nozzle
from rocketforge.physics.compressible.types import FlowBranch

GAMMAS = (1.2, 1.3, 1.4, 1.66)
AREA_RATIOS = (1.05, 1.5, 2.0, 4.0, 10.0, 50.0)


def gas(gamma: float = 1.4) -> PerfectGas:
    return PerfectGas(gamma=gamma, gas_constant=287.05)


# ---------------------------------------------------------------------------
# the worked example from the specification
# ---------------------------------------------------------------------------


def test_the_phase_3_worked_example_is_reproduced_exactly():
    """``03`` section 10.4, gamma = 1.4, Ae/A* = 2 -- the hand-checkable case."""
    critical = nozzle.critical_pressure_ratios(2.0, gas()).unwrap()
    assert critical.mach_exit_subsonic == pytest.approx(0.3059038342, abs=5e-10)
    assert critical.mach_exit_supersonic == pytest.approx(2.1971981217, abs=5e-10)
    assert critical.first_critical == pytest.approx(0.9371625024, abs=5e-10)
    assert critical.second_critical == pytest.approx(0.5134007280, abs=5e-10)
    assert critical.third_critical == pytest.approx(0.0939326457, abs=5e-10)


# ---------------------------------------------------------------------------
# definitions, checked against the modules they are supposed to come from
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_the_exit_machs_are_the_two_area_mach_roots(gamma, area_ratio):
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
    subsonic = iso.mach_from_area_ratio(area_ratio, air, FlowBranch.SUBSONIC).unwrap()
    supersonic = iso.mach_from_area_ratio(area_ratio, air, FlowBranch.SUPERSONIC).unwrap()
    assert critical.mach_exit_subsonic == subsonic
    assert critical.mach_exit_supersonic == supersonic


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_the_first_critical_is_the_subsonic_branch_exit_pressure(gamma, area_ratio):
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
    assert critical.first_critical == iso.pressure_ratio(critical.mach_exit_subsonic, air)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_the_third_critical_is_the_supersonic_branch_exit_pressure(gamma, area_ratio):
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
    assert critical.third_critical == iso.pressure_ratio(critical.mach_exit_supersonic, air)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_the_second_critical_is_the_third_through_a_normal_shock(gamma, area_ratio):
    """``05`` section 10 requires this identity to machine precision."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
    expected = (critical.third_critical
                * shock.pressure_ratio(critical.mach_exit_supersonic, air))
    assert critical.second_critical == pytest.approx(expected, rel=1e-15)


def test_the_phase_3_shock_at_exit_identity():
    """``03`` section 11.9: 0.0939326457 x 5.4656261834 = 0.5134007280."""
    air = gas()
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    jump = shock.solve(critical.mach_exit_supersonic, air)
    assert jump.mach2 == pytest.approx(0.5474316548, abs=5e-10)
    assert jump.pressure_ratio == pytest.approx(5.4656261834, abs=5e-10)
    assert jump.stagnation_pressure_ratio == pytest.approx(0.6294128957, abs=5e-10)
    assert critical.third_critical * jump.pressure_ratio == pytest.approx(
        critical.second_critical, rel=1e-15)


# ---------------------------------------------------------------------------
# ordering, the invariant everything else rests on
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_the_thresholds_are_always_ordered(gamma, area_ratio):
    critical = nozzle.critical_pressure_ratios(area_ratio, gas(gamma)).unwrap()
    assert 0.0 < critical.third_critical < critical.second_critical
    assert critical.second_critical < critical.first_critical < 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_thresholds_move_the_right_way_with_area_ratio(gamma):
    """A longer diverging section lowers all three, and separates them."""
    air = gas(gamma)
    previous = None
    for area_ratio in AREA_RATIOS:
        critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
        if previous is not None:
            assert critical.first_critical > previous.first_critical
            assert critical.second_critical < previous.second_critical
            assert critical.third_critical < previous.third_critical
        previous = critical


@pytest.mark.parametrize("gamma", GAMMAS)
def test_all_three_thresholds_converge_on_the_sonic_ratio_as_the_nozzle_degenerates(gamma):
    """As Ae/A* -> 1 the exit becomes the throat, so all three criticals meet.

    ``05`` says "all three criticals -> 1" for this limit, which reads as
    "converge on one value" rather than "converge on unity": at Ae/A* = 1 the
    exit *is* the throat, both branches give M = 1, and every critical is the
    sonic pressure ratio p*/p0 -- 0.5283 at gamma = 1.4, never 1. The
    well-ordering the same line requires is what is checked here, together with
    the limit the physics actually has.
    """
    air = gas(gamma)
    sonic = iso.pressure_ratio(1.0, air)
    previous_spread = None
    for area_ratio in (1.1, 1.01, 1.001, 1.0001):
        critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
        assert critical.third_critical < critical.second_critical < critical.first_critical
        spread = critical.first_critical - critical.third_critical
        if previous_spread is not None:
            assert spread < previous_spread
        previous_spread = spread
    tightest = nozzle.critical_pressure_ratios(1.0001, air).unwrap()
    assert tightest.first_critical == pytest.approx(sonic, rel=2e-2)
    assert tightest.third_critical == pytest.approx(sonic, rel=2e-2)
    assert tightest.second_critical == pytest.approx(sonic, rel=2e-2)


# ---------------------------------------------------------------------------
# refusals
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("area_ratio", [0.8, 1.0])
def test_a_non_diverging_area_ratio_is_refused(area_ratio):
    with pytest.raises(GeometryError):
        nozzle.critical_pressure_ratios(area_ratio, gas())


def test_a_non_finite_area_ratio_is_refused():
    with pytest.raises(GeometryError):
        nozzle.critical_pressure_ratios(float("nan"), gas())


def test_the_thresholds_need_no_gas_constant():
    """Ratios are what gamma alone supplies, so a dimensionless gas is enough."""
    critical = nozzle.critical_pressure_ratios(
        2.0, PerfectGas(gamma=1.4)).unwrap()
    assert critical.first_critical == pytest.approx(0.9371625024, abs=5e-10)
