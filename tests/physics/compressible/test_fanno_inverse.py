"""Fanno flow: the branch-aware inverse, the duct problem, and the convention.

``docs/engineering/03_compressible_flow_specification.md`` section 8.6. The
inverse is bracketed per branch because ``4fL*/D`` falls to zero from both
sides of sonic: the whole range is not monotone and the equations cannot say
which duct the caller means.

The friction-convention tests in the last section are the ones that matter
most. A factor of four between Darcy and Fanning is the single most likely way
for this module to be silently wrong, and it would look entirely plausible on
screen.
"""

from __future__ import annotations

import numpy as np
import pytest

from rocketforge.core.errors import DomainError
from rocketforge.core.result import Status
from rocketforge.core.tolerances import DEFAULT_TOLERANCES
from rocketforge.physics.compressible import FlowBranch, PerfectGas
from rocketforge.physics.compressible import fanno

GAMMAS = (1.2, 1.3, 1.4, 1.66)


def gas(gamma: float) -> PerfectGas:
    return PerfectGas(gamma=gamma)


# ---------------------------------------------------------------------------
# the inverse
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", [0.05, 0.2, 0.5, 0.8, 0.95])
def test_subsonic_round_trip(gamma, mach):
    air = gas(gamma)
    parameter = float(fanno.friction_parameter(mach, air))
    solution = fanno.mach_from_friction_parameter(parameter, air, FlowBranch.SUBSONIC)
    assert solution.ok
    assert solution.unwrap() == pytest.approx(mach, rel=1e-9)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", [1.05, 1.5, 2.0, 3.5, 8.0])
def test_supersonic_round_trip(gamma, mach):
    air = gas(gamma)
    parameter = float(fanno.friction_parameter(mach, air))
    solution = fanno.mach_from_friction_parameter(parameter, air, FlowBranch.SUPERSONIC)
    assert solution.ok
    assert solution.unwrap() == pytest.approx(mach, rel=1e-8)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_two_branches_give_different_roots_for_the_same_parameter(gamma):
    """The reason a branch argument exists at all.

    One value of ``4fL*/D`` names two physically different ducts, and neither
    is more correct than the other.
    """
    air = gas(gamma)
    target = 0.2
    sub = fanno.mach_from_friction_parameter(target, air, FlowBranch.SUBSONIC)
    sup = fanno.mach_from_friction_parameter(target, air, FlowBranch.SUPERSONIC)
    assert sub.ok and sup.ok
    assert sub.unwrap() < 1.0 < sup.unwrap()
    assert float(fanno.friction_parameter(sub.unwrap(), air)) == pytest.approx(target, rel=1e-9)
    assert float(fanno.friction_parameter(sup.unwrap(), air)) == pytest.approx(target, rel=1e-9)


def test_branch_is_required_and_both_is_refused():
    air = gas(1.4)
    with pytest.raises(ValueError):
        fanno.mach_from_friction_parameter(0.5, air, "subsonic")
    with pytest.raises(ValueError):
        fanno.mach_from_friction_parameter(0.5, air, FlowBranch.BOTH)


@pytest.mark.parametrize("branch", [FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC])
def test_zero_parameter_is_the_sonic_state_on_either_branch(branch):
    solution = fanno.mach_from_friction_parameter(0.0, gas(1.4), branch)
    assert solution.ok
    assert solution.unwrap() == 1.0
    assert any(d.code == "SONIC_EXACT" for d in solution.diagnostics)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_a_supersonic_duct_longer_than_the_limit_has_no_solution(gamma):
    """Not a convergence failure -- a physical answer, and it says so."""
    air = gas(gamma)
    limit = fanno.friction_parameter_limit(air)
    solution = fanno.mach_from_friction_parameter(limit * 1.5, air, FlowBranch.SUPERSONIC)
    assert not solution.ok
    assert solution.status is Status.NO_SOLUTION
    assert any(d.code == "FANNO_LIMIT" for d in solution.diagnostics)
    detail = next(d.detail for d in solution.diagnostics if d.code == "FANNO_LIMIT")
    assert detail["limit"] == pytest.approx(limit)


def test_a_subsonic_duct_of_any_length_has_a_solution():
    """The subsonic branch runs to infinity, so nothing is out of range."""
    air = gas(1.4)
    for target in (1.0, 10.0, 100.0, 1e4):
        solution = fanno.mach_from_friction_parameter(target, air, FlowBranch.SUBSONIC)
        assert solution.ok, target
        assert 0.0 < solution.unwrap() < 1.0


def test_negative_parameter_is_refused():
    with pytest.raises(DomainError):
        fanno.mach_from_friction_parameter(-0.1, gas(1.4), FlowBranch.SUBSONIC)


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_nonfinite_parameter_is_refused(bad):
    with pytest.raises(DomainError):
        fanno.mach_from_friction_parameter(bad, gas(1.4), FlowBranch.SUBSONIC)


def test_inverse_refuses_an_array():
    with pytest.raises(DomainError):
        fanno.mach_from_friction_parameter(np.array([0.1, 0.2]), gas(1.4),
                                           FlowBranch.SUBSONIC)


def test_near_sonic_solutions_are_flagged_rather_than_overclaimed():
    """Half the digits carry over, and the result says so instead of pretending."""
    air = gas(1.4)
    tiny = 1e-8
    solution = fanno.mach_from_friction_parameter(tiny, air, FlowBranch.SUBSONIC)
    assert solution.ok
    assert abs(solution.unwrap() - 1.0) < DEFAULT_TOLERANCES.near_sonic_mach
    assert any(d.code == "NEAR_SONIC" for d in solution.diagnostics)


def test_the_inverse_reports_its_convergence():
    """A root report, not just a number: iterations, residual and bracket."""
    solution = fanno.mach_from_friction_parameter(1.0, gas(1.4), FlowBranch.SUBSONIC)
    assert solution.ok
    assert solution.convergence is not None
    assert solution.convergence.converged
    assert solution.convergence.iterations >= 1
    assert abs(solution.convergence.residual) <= 1e-9


# ---------------------------------------------------------------------------
# the duct problem
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_a_zero_length_duct_leaves_the_flow_where_it_started(gamma):
    air = gas(gamma)
    solution = fanno.downstream_mach(0.4, 0.0, air)
    assert solution.ok
    result = solution.unwrap()
    assert result.downstream.mach == pytest.approx(0.4, rel=1e-12)
    assert not result.choked


@pytest.mark.parametrize("gamma", GAMMAS)
def test_friction_pushes_a_subsonic_inlet_up_towards_sonic(gamma):
    air = gas(gamma)
    result = fanno.downstream_mach(0.3, 1.0, air).unwrap()
    assert 0.3 < result.downstream.mach < 1.0
    assert result.downstream.friction_parameter < result.upstream.friction_parameter
    # The static trends that go with acceleration.
    assert result.pressure_ratio_12 < 1.0
    assert result.temperature_ratio_12 < 1.0
    assert result.stagnation_pressure_ratio_12 < 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
def test_friction_pulls_a_supersonic_inlet_down_towards_sonic(gamma):
    air = gas(gamma)
    result = fanno.downstream_mach(3.0, 0.2, air).unwrap()
    assert 1.0 < result.downstream.mach < 3.0
    assert result.downstream.friction_parameter < result.upstream.friction_parameter
    assert result.pressure_ratio_12 > 1.0
    assert result.temperature_ratio_12 > 1.0
    # Still a loss: friction is irreversible on this branch too.
    assert result.stagnation_pressure_ratio_12 < 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("inlet", [0.2, 0.6, 0.9, 1.2, 2.0, 4.0])
def test_a_duct_never_crosses_the_sonic_point(gamma, inlet):
    """A subsonic inlet stays subsonic and a supersonic inlet stays supersonic.

    Checked at 90% of the available length, which is where a solver that
    bracketed the whole range instead of one branch would be most tempted to
    return the root on the other side.
    """
    air = gas(gamma)
    available = float(fanno.friction_parameter(inlet, air))
    result = fanno.downstream_mach(inlet, 0.9 * available, air).unwrap()
    if inlet < 1.0:
        assert result.downstream.mach < 1.0
    else:
        assert result.downstream.mach > 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("inlet", [0.35, 2.5])
def test_a_duct_of_exactly_the_choking_length_ends_sonic(gamma, inlet):
    air = gas(gamma)
    available = float(fanno.friction_parameter(inlet, air))
    solution = fanno.downstream_mach(inlet, available, air)
    assert solution.ok
    result = solution.unwrap()
    assert result.choked
    assert result.downstream.mach == 1.0
    assert result.remaining_to_choking == 0.0


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("inlet", [0.35, 2.5])
def test_a_duct_longer_than_the_choking_length_is_refused_with_both_numbers(gamma, inlet):
    """No fabricated outlet, and the requested length is preserved.

    ``03`` section 8.6: the over-length case is a genuine engineering answer --
    the flow chokes and the upstream condition must change -- so it is reported
    rather than silently truncated to the sonic length.
    """
    air = gas(gamma)
    available = float(fanno.friction_parameter(inlet, air))
    requested = available * 1.5
    solution = fanno.downstream_mach(inlet, requested, air)

    assert not solution.ok
    assert solution.status is Status.NO_SOLUTION
    assert solution.value is None
    diagnostic = next(d for d in solution.diagnostics if d.code == "FRICTION_CHOKED")
    assert diagnostic.detail["duct_parameter"] == pytest.approx(requested)
    assert diagnostic.detail["available"] == pytest.approx(available)


def test_a_duct_cannot_start_at_the_sonic_point():
    with pytest.raises(DomainError):
        fanno.downstream_mach(1.0, 0.1, gas(1.4))


def test_a_negative_duct_length_is_refused():
    with pytest.raises(DomainError):
        fanno.downstream_mach(0.5, -0.1, gas(1.4))


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("pair", [(0.3, 0.7), (0.9, 0.95), (4.0, 1.5), (2.0, 1.2)])
def test_required_duct_parameter_is_the_inverse_of_the_duct_problem(gamma, pair):
    """Ask for the length between two stations, then walk it and arrive."""
    air = gas(gamma)
    mach1, mach2 = pair
    length = fanno.required_duct_parameter(mach1, mach2, air)
    assert length > 0.0
    result = fanno.downstream_mach(mach1, length, air).unwrap()
    assert result.downstream.mach == pytest.approx(mach2, rel=1e-8)


def test_required_duct_parameter_refuses_to_cross_sonic():
    """No length of constant-area duct connects a subsonic and a supersonic state."""
    with pytest.raises(DomainError):
        fanno.required_duct_parameter(0.5, 2.0, gas(1.4))


# ---------------------------------------------------------------------------
# the friction convention -- the factor-of-four guard
# ---------------------------------------------------------------------------


def test_darcy_and_fanning_convert_by_exactly_four():
    assert fanno.fanning_to_darcy(0.005) == pytest.approx(0.02, rel=1e-15)
    assert fanno.darcy_to_fanning(0.02) == pytest.approx(0.005, rel=1e-15)
    assert fanno.darcy_to_fanning(fanno.fanning_to_darcy(0.0123)) == pytest.approx(0.0123)


def test_the_same_physical_duct_gives_the_same_answer_in_either_convention():
    """The permanent guard on ``03`` section 8.2.

    One duct, described twice. The Darcy description quotes f_D = 0.02; the
    Fanning description quotes f_F = 0.005. They are the same wall, so every
    number that comes out must be identical -- not close, identical, because
    the conversion is an exact division by four.
    """
    air = gas(1.4)
    length, diameter = 3.0, 0.1
    darcy, fanning = 0.02, 0.005

    from_darcy = fanno.duct_parameter_from_geometry(
        fanno.darcy_to_fanning(darcy), length, diameter)
    from_fanning = fanno.duct_parameter_from_geometry(fanning, length, diameter)
    assert from_darcy == from_fanning

    a = fanno.downstream_mach(0.3, from_darcy, air).unwrap()
    b = fanno.downstream_mach(0.3, from_fanning, air).unwrap()
    assert a.downstream.mach == b.downstream.mach
    assert a.pressure_ratio_12 == b.pressure_ratio_12
    assert a.stagnation_pressure_ratio_12 == b.stagnation_pressure_ratio_12


def test_reading_a_fanning_number_as_darcy_would_be_caught():
    """The error this convention decision exists to prevent, made deliberately.

    Feeding a Darcy factor straight in where a Fanning one is expected models a
    duct four times too long. The point is that the mistake is never subtle: it
    moves the outlet Mach number by a wide margin, and for a duct of any
    reasonable length it turns an attached solution into a choked one. A
    convention error cannot hide inside a rounding difference.
    """
    air = gas(1.4)
    correct = fanno.duct_parameter_from_geometry(0.005, 3.0, 0.1)
    mistaken = fanno.duct_parameter_from_geometry(0.02, 3.0, 0.1)
    assert mistaken == pytest.approx(4.0 * correct)

    right = fanno.downstream_mach(0.3, correct, air).unwrap().downstream.mach
    wrong = fanno.downstream_mach(0.3, mistaken, air).unwrap().downstream.mach
    assert right < 1.0 and wrong < 1.0
    # Not a near miss. For this duct the outlet Mach number is out by 18 per
    # cent -- far outside anything a tolerance or a rounding could explain.
    assert abs(wrong - right) / right > 0.15

    # Lengthen the same duct and the mistake stops being a wrong number and
    # becomes a wrong answer: the flow is reported as choked when it is not.
    available = float(fanno.friction_parameter(0.3, air))
    honest = 0.9 * available
    assert fanno.downstream_mach(0.3, honest, air).ok
    assert not fanno.downstream_mach(0.3, 4.0 * honest, air).ok


def test_the_specification_value_pins_the_convention():
    """``4fL*/D`` at M = 0.5, gamma = 1.4 is 1.0690603127 in the Fanning group.

    Under a Darcy reading the same duct reads 0.2672650782. ``03`` section 8.2
    names both numbers precisely so this test can tell them apart.
    """
    value = float(fanno.friction_parameter(0.5, gas(1.4)))
    assert value == pytest.approx(1.0690603127, abs=5e-11)
    assert value / 4.0 == pytest.approx(0.2672650782, abs=5e-11)


@pytest.mark.parametrize("scale", [0.5, 2.0, 10.0])
def test_only_the_group_matters_not_the_individual_lengths(scale):
    """f L / D is one number: doubling L and D together changes nothing."""
    base = fanno.duct_parameter_from_geometry(0.005, 3.0, 0.1)
    scaled = fanno.duct_parameter_from_geometry(0.005, 3.0 * scale, 0.1 * scale)
    assert scaled == pytest.approx(base, rel=1e-14)


def test_geometry_helper_refuses_nonpositive_dimensions():
    for args in ((0.0, 1.0, 0.1), (0.005, 0.0, 0.1), (0.005, 1.0, 0.0),
                 (-0.005, 1.0, 0.1)):
        with pytest.raises(DomainError):
            fanno.duct_parameter_from_geometry(*args)
