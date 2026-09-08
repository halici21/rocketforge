"""Rayleigh flow: the one approved inverse, and the heat-addition duct problem.

``docs/engineering/03_compressible_flow_specification.md`` section 9.5 puts
exactly one inverse in v1 -- ``T0/T0* -> M``, branch given -- because that *is*
the heat-addition question. The ``T/T* -> M`` inverse is deliberately deferred:
it is not monotone on the subsonic branch, so a value below its maximum has two
subsonic roots either side of 1/sqrt(gamma), and inverting it honestly needs a
three-way interval selector rather than the two-way branch.

There is therefore no round-trip test for ``T/T*``. Its absence is the point,
and the test at the end of this file asserts that the function stays absent.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError, MissingGasConstantError
from rocketforge.core.result import Status
from rocketforge.core.tolerances import DEFAULT_TOLERANCES
from rocketforge.physics.compressible import FlowBranch, PerfectGas
from rocketforge.physics.compressible import rayleigh

GAMMAS = (1.2, 1.3, 1.4, 1.66)


def gas(gamma: float, with_r: bool = False) -> PerfectGas:
    return (PerfectGas(gamma=gamma, gas_constant=287.0528) if with_r
            else PerfectGas(gamma=gamma))


# ---------------------------------------------------------------------------
# the inverse
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", [0.05, 0.2, 0.5, 0.8, 0.95])
def test_subsonic_round_trip(gamma, mach):
    air = gas(gamma)
    ratio = float(rayleigh.stagnation_temperature_ratio(mach, air))
    solution = rayleigh.mach_from_stagnation_temperature_ratio(
        ratio, air, FlowBranch.SUBSONIC)
    assert solution.ok
    assert solution.unwrap() == pytest.approx(mach, rel=1e-8)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", [1.05, 1.5, 2.0, 3.5, 8.0])
def test_supersonic_round_trip(gamma, mach):
    air = gas(gamma)
    ratio = float(rayleigh.stagnation_temperature_ratio(mach, air))
    solution = rayleigh.mach_from_stagnation_temperature_ratio(
        ratio, air, FlowBranch.SUPERSONIC)
    assert solution.ok
    assert solution.unwrap() == pytest.approx(mach, rel=1e-8)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_one_ratio_has_a_root_on_each_branch(gamma):
    """Why the branch argument is not optional.

    T0/T0* rises to 1 from *both* sides, so every attainable value names two
    physically different ducts.
    """
    air = gas(gamma)
    target = 0.8
    sub = rayleigh.mach_from_stagnation_temperature_ratio(target, air, FlowBranch.SUBSONIC)
    sup = rayleigh.mach_from_stagnation_temperature_ratio(target, air,
                                                          FlowBranch.SUPERSONIC)
    assert sub.ok and sup.ok
    assert sub.unwrap() < 1.0 < sup.unwrap()
    for solution in (sub, sup):
        assert float(rayleigh.stagnation_temperature_ratio(solution.unwrap(), air)) \
            == pytest.approx(target, rel=1e-9)


def test_branch_is_required_and_both_is_refused():
    air = gas(1.4)
    with pytest.raises(ValueError):
        rayleigh.mach_from_stagnation_temperature_ratio(0.8, air, "subsonic")
    with pytest.raises(ValueError):
        rayleigh.mach_from_stagnation_temperature_ratio(0.8, air, FlowBranch.BOTH)


@pytest.mark.parametrize("branch", [FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC])
def test_a_ratio_of_one_is_the_sonic_state(branch):
    solution = rayleigh.mach_from_stagnation_temperature_ratio(1.0, gas(1.4), branch)
    assert solution.ok
    assert solution.unwrap() == 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
def test_a_ratio_above_one_is_thermally_choked_not_a_root_failure(gamma):
    """Above the sonic maximum there is no state, and the module says why."""
    solution = rayleigh.mach_from_stagnation_temperature_ratio(
        1.05, gas(gamma), FlowBranch.SUBSONIC)
    assert not solution.ok
    assert solution.status is Status.NO_SOLUTION
    assert any(d.code in ("THERMALLY_CHOKED", "RAYLEIGH_LIMIT")
               for d in solution.diagnostics)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_a_supersonic_ratio_below_the_finite_floor_has_no_solution(gamma):
    """The supersonic branch stops at (gamma^2-1)/gamma^2, so below it nothing
    exists however much the flow is cooled."""
    air = gas(gamma)
    floor = rayleigh.stagnation_temperature_ratio_limit(air)
    solution = rayleigh.mach_from_stagnation_temperature_ratio(
        floor * 0.5, air, FlowBranch.SUPERSONIC)
    assert not solution.ok
    assert solution.status is Status.NO_SOLUTION


@pytest.mark.parametrize("bad", [0.0, -0.2])
def test_nonpositive_ratio_is_refused(bad):
    with pytest.raises(DomainError):
        rayleigh.mach_from_stagnation_temperature_ratio(bad, gas(1.4), FlowBranch.SUBSONIC)


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_nonfinite_ratio_is_refused(bad):
    with pytest.raises(DomainError):
        rayleigh.mach_from_stagnation_temperature_ratio(bad, gas(1.4), FlowBranch.SUBSONIC)


def test_inverse_refuses_an_array():
    with pytest.raises(DomainError):
        rayleigh.mach_from_stagnation_temperature_ratio(
            np.array([0.7, 0.8]), gas(1.4), FlowBranch.SUBSONIC)


def test_near_sonic_solutions_are_flagged():
    """1 - T0/T0* goes as (M-1)^2, so half the digits survive the inversion."""
    solution = rayleigh.mach_from_stagnation_temperature_ratio(
        1.0 - 1e-10, gas(1.4), FlowBranch.SUBSONIC)
    assert solution.ok
    assert abs(solution.unwrap() - 1.0) < DEFAULT_TOLERANCES.near_sonic_mach
    assert any(d.code == "NEAR_SONIC" for d in solution.diagnostics)


def test_the_inverse_reports_its_convergence():
    solution = rayleigh.mach_from_stagnation_temperature_ratio(
        0.7, gas(1.4), FlowBranch.SUBSONIC)
    assert solution.ok
    assert solution.convergence is not None
    assert solution.convergence.converged
    assert solution.convergence.iterations >= 1


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_near_sonic_conditioning_follows_the_specified_quadratic(gamma):
    """``03`` section 9.2 and ``04``: 1 - T0/T0* ~ [4/(gamma+1)^2] (M-1)^2.

    The coefficient is what sets the achievable Mach precision near choking, so
    it is checked rather than assumed.
    """
    air = gas(gamma)
    coefficient = 4.0 / (gamma + 1.0) ** 2
    for epsilon in (1e-3, 1e-4, 1e-5):
        deficit = 1.0 - float(rayleigh.stagnation_temperature_ratio(1.0 + epsilon, air))
        assert deficit == pytest.approx(coefficient * epsilon * epsilon, rel=5e-3)


# ---------------------------------------------------------------------------
# the deferred inverse stays deferred
# ---------------------------------------------------------------------------


def test_the_static_temperature_inverse_is_not_offered():
    """``03`` section 9.5 defers it, with the reason recorded.

    T/T* has two subsonic roots either side of 1/sqrt(gamma). A two-way branch
    cannot name which one is wanted, so the honest options were a three-way
    interval selector or nothing; v1 chose nothing. This test exists so that a
    later implementer has to delete it deliberately rather than add an
    ambiguous inverse because a root finder happened to be available.
    """
    assert not hasattr(rayleigh, "mach_from_temperature_ratio")
    assert "mach_from_temperature_ratio" not in rayleigh.__all__


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_static_temperature_ratio_really_is_two_valued_subsonically(gamma):
    """The fact that justifies the deferral, demonstrated rather than asserted."""
    air = gas(gamma)
    peak = rayleigh.mach_at_maximum_temperature(air)
    # Strictly between the sonic value of 1 and the peak, so that a root exists
    # on each side of the peak. For gamma = 1.2 the peak is only 1.0083, so a
    # target chosen as a fraction of it can fall below 1 and have no upper root
    # at all -- which is a statement about the test, not about the physics.
    target = 0.5 * (1.0 + rayleigh.maximum_temperature_ratio(air))

    below = np.linspace(1e-3, peak, 4000)
    above = np.linspace(peak, 1.0, 4000)
    lower = below[np.argmin(np.abs(np.asarray(rayleigh.temperature_ratio(below, air))
                                   - target))]
    upper = above[np.argmin(np.abs(np.asarray(rayleigh.temperature_ratio(above, air))
                                   - target))]
    assert lower < peak < upper < 1.0
    assert float(rayleigh.temperature_ratio(lower, air)) == pytest.approx(target, rel=1e-3)
    assert float(rayleigh.temperature_ratio(upper, air)) == pytest.approx(target, rel=1e-3)


# ---------------------------------------------------------------------------
# the heat-addition duct problem
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_no_heat_leaves_the_flow_where_it_started(gamma):
    result = rayleigh.heat_addition(0.4, 1.0, gas(gamma)).unwrap()
    assert result.downstream.mach == pytest.approx(0.4, rel=1e-12)
    assert not result.thermally_choked


@pytest.mark.parametrize("gamma", GAMMAS)
def test_heating_a_subsonic_inlet_moves_it_towards_sonic(gamma):
    air = gas(gamma)
    result = rayleigh.heat_addition(0.3, 1.5, air).unwrap()
    assert 0.3 < result.downstream.mach < 1.0
    assert result.downstream.stagnation_temperature_ratio > \
        result.upstream.stagnation_temperature_ratio
    assert result.pressure_ratio_12 < 1.0                 # p falls with heating
    assert result.stagnation_pressure_ratio_12 < 1.0      # the Rayleigh loss


@pytest.mark.parametrize("gamma", GAMMAS)
def test_heating_a_supersonic_inlet_also_moves_it_towards_sonic(gamma):
    air = gas(gamma)
    result = rayleigh.heat_addition(3.0, 1.15, air).unwrap()
    assert 1.0 < result.downstream.mach < 3.0
    assert result.pressure_ratio_12 > 1.0                 # p rises on this branch
    assert result.stagnation_pressure_ratio_12 < 1.0      # still a loss


@pytest.mark.parametrize("gamma", GAMMAS)
def test_cooling_moves_a_subsonic_flow_away_from_sonic(gamma):
    """``03`` section 9.3: cooling a subsonic stream takes M towards 0."""
    result = rayleigh.heat_addition(0.6, 0.8, gas(gamma)).unwrap()
    assert result.downstream.mach < 0.6


@pytest.mark.parametrize("gamma", GAMMAS)
def test_cooling_moves_a_supersonic_flow_away_from_sonic(gamma):
    result = rayleigh.heat_addition(2.0, 0.9, gas(gamma)).unwrap()
    assert result.downstream.mach > 2.0


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("inlet", [0.2, 0.6, 0.9, 1.2, 2.0, 4.0])
def test_a_duct_never_crosses_the_sonic_point(gamma, inlet):
    """Checked at 99% of the available heat, where a solver that bracketed the
    whole range would be most tempted to return the root on the other side."""
    air = gas(gamma)
    at_inlet = float(rayleigh.stagnation_temperature_ratio(inlet, air))
    ratio = 1.0 + 0.99 * (1.0 / at_inlet - 1.0)
    result = rayleigh.heat_addition(inlet, ratio, air).unwrap()
    if inlet < 1.0:
        assert result.downstream.mach < 1.0
    else:
        assert result.downstream.mach > 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("inlet", [0.35, 2.5])
def test_exactly_the_choking_heat_ends_sonic(gamma, inlet):
    air = gas(gamma)
    at_inlet = float(rayleigh.stagnation_temperature_ratio(inlet, air))
    solution = rayleigh.heat_addition(inlet, 1.0 / at_inlet, air)
    assert solution.ok
    result = solution.unwrap()
    assert result.thermally_choked
    assert result.downstream.mach == 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("inlet", [0.35, 2.5])
def test_more_heat_than_the_line_can_take_is_refused_with_both_numbers(gamma, inlet):
    """No fabricated outlet Mach number, and the request is preserved.

    ``03`` section 9.5: the flow chokes and the upstream condition must change.
    That is an engineering answer, not a failure, and it is never silently
    clamped to the sonic value.
    """
    air = gas(gamma)
    at_inlet = float(rayleigh.stagnation_temperature_ratio(inlet, air))
    maximum = 1.0 / at_inlet
    requested = maximum * 1.2
    solution = rayleigh.heat_addition(inlet, requested, air)

    assert not solution.ok
    assert solution.status is Status.NO_SOLUTION
    assert solution.value is None
    diagnostic = next(d for d in solution.diagnostics if d.code == "THERMALLY_CHOKED")
    assert diagnostic.detail["requested"] == pytest.approx(requested)
    assert diagnostic.detail["maximum"] == pytest.approx(maximum)


def test_a_duct_cannot_start_at_the_sonic_point():
    with pytest.raises(DomainError):
        rayleigh.heat_addition(1.0, 1.1, gas(1.4))


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_a_nonpositive_temperature_ratio_is_refused(bad):
    with pytest.raises(DomainError):
        rayleigh.heat_addition(0.5, bad, gas(1.4))


# ---------------------------------------------------------------------------
# dimensional heat
# ---------------------------------------------------------------------------


def test_specific_heat_addition_uses_cp_from_the_gas_model():
    """``q = cp (T02 - T01)``, with cp taken from PerfectGas and not restated."""
    air = gas(1.4, with_r=True)
    t01 = 300.0
    mach1, mach2 = 0.3, 0.6
    q = rayleigh.specific_heat_addition(mach1, mach2, air, t01)

    first = float(rayleigh.stagnation_temperature_ratio(mach1, air))
    second = float(rayleigh.stagnation_temperature_ratio(mach2, air))
    expected = air.cp * (t01 * second / first - t01)
    assert q == pytest.approx(expected, rel=1e-14)
    assert q > 0.0                                   # accelerating means heating


def test_cooling_gives_a_negative_heat():
    air = gas(1.4, with_r=True)
    assert rayleigh.specific_heat_addition(0.6, 0.3, air, 300.0) < 0.0


def test_heat_needs_a_gas_constant_and_says_so():
    """cp needs R. Without one the module refuses rather than inventing air."""
    with pytest.raises(MissingGasConstantError):
        rayleigh.specific_heat_addition(0.3, 0.6, gas(1.4), 300.0)


@pytest.mark.parametrize("bad", [0.0, -50.0])
def test_heat_refuses_a_nonpositive_stagnation_temperature(bad):
    with pytest.raises(DomainError):
        rayleigh.specific_heat_addition(0.3, 0.6, gas(1.4, with_r=True), bad)
