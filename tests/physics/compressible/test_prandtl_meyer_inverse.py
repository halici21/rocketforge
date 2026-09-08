"""The Prandtl-Meyer inverse and the expansion turn.

Two things are being checked here that a round-trip alone would not catch: that
the solver's *record* of what it did is honest (bracket, residual, iterations,
diagnostics), and that the expansion reuses the isentropic module rather than
growing its own static-ratio formulas.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError, SubsonicExpansionError
from rocketforge.core.result import Status
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import prandtl_meyer as pm

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]
AIR = PerfectGas(gamma=1.4)


# ---------------------------------------------------------------------------
# the inverse
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach", [1.0001, 1.01, 1.1, 1.5, 2.0, 3.0, 5.0, 10.0, 30.0])
def test_inverse_round_trips(gas, mach):
    solution = pm.mach_from_nu(float(pm.nu(mach, gas)), gas)
    assert solution.ok
    assert solution.unwrap() == pytest.approx(mach, rel=1e-9)


def test_reference_inversions_for_air():
    """Specification section 11.6: nu = 30 deg -> M, nu = 45 deg -> M."""
    assert pm.mach_from_nu(math.radians(30.0), AIR).unwrap() == pytest.approx(
        2.1339050332, abs=5e-10)
    assert pm.mach_from_nu(math.radians(45.0), AIR).unwrap() == pytest.approx(
        2.7644521940, abs=5e-10)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_zero_turning_is_answered_exactly_without_iterating(gas):
    """nu = 0 is the sonic point; iterating on a zero residual is theatre."""
    solution = pm.mach_from_nu(0.0, gas)
    assert solution.unwrap() == 1.0
    assert solution.convergence is None
    assert any(d.code == "SONIC_EXACT" for d in solution.diagnostics)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_turning_at_or_beyond_the_maximum_has_no_solution(gas):
    ceiling = pm.nu_max(gas)
    for value in (ceiling, ceiling * 1.001, ceiling + 0.5):
        solution = pm.mach_from_nu(value, gas)
        assert solution.status is Status.NO_SOLUTION
        assert solution.value is None
        assert any(d.code == "NU_EXCEEDS_MAX" for d in solution.diagnostics)


def test_the_refusal_at_the_ceiling_explains_itself():
    solution = pm.mach_from_nu(pm.nu_max(AIR) + 0.1, AIR)
    message = solution.diagnostics[-1].message
    assert "130.45" in message and "infinite" in message


@pytest.mark.parametrize("bad", [-1e-9, -0.5, -math.pi])
def test_negative_turning_is_refused(bad):
    with pytest.raises(DomainError, match="cannot be negative"):
        pm.mach_from_nu(bad, AIR)


@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_non_finite_turning_is_refused(bad):
    with pytest.raises(DomainError):
        pm.mach_from_nu(bad, AIR)


def test_the_scalar_inverse_refuses_an_array():
    with pytest.raises(DomainError, match="mach_from_nu_array"):
        pm.mach_from_nu(np.array([0.1, 0.2]), AIR)


# ---------------------------------------------------------------------------
# what the solver reports about itself
# ---------------------------------------------------------------------------


def test_the_inverse_reports_how_it_converged():
    solution = pm.mach_from_nu(math.radians(30.0), AIR)
    assert solution.status is Status.OK
    assert solution.convergence is not None
    assert solution.convergence.converged
    assert 0 < solution.convergence.iterations <= 100
    assert abs(solution.convergence.residual) <= 1e-9
    # The report's bracket is the *final* one, so it must still contain the
    # root; that the search started from an exact lower end of 1.0 is asserted
    # by the spy test below, where the initial call is visible.
    low, high = solution.convergence.bracket
    assert low <= solution.unwrap() <= high
    assert high - low <= 1e-9
    assert solution.inputs["gamma"] == pytest.approx(1.4)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach", [1.5, 3.0, 10.0])
def test_the_closed_form_bracket_seed_always_contains_the_root(gas, mach):
    """The seed must overestimate, or the bracket is invalid before Brent starts."""
    target = float(pm.nu(mach, gas))
    from rocketforge.core.tolerances import DEFAULT_TOLERANCES

    seed = pm._upper_bracket(target, gas, DEFAULT_TOLERANCES)
    assert seed > 1.0
    assert float(pm.nu(seed, gas)) >= target


def test_a_small_turn_warns_that_mach_is_less_determined_than_the_angle():
    solution = pm.mach_from_nu(float(pm.nu(1.0 + 1e-5, AIR)), AIR)
    assert solution.ok
    assert any(d.code == "NEAR_SONIC" for d in solution.diagnostics)
    assert "(3/2)" in "".join(d.message for d in solution.diagnostics) or "3/2" in "".join(
        d.message for d in solution.diagnostics)


def test_an_ordinary_turn_carries_no_near_sonic_warning():
    solution = pm.mach_from_nu(math.radians(20.0), AIR)
    assert not any(d.code == "NEAR_SONIC" for d in solution.diagnostics)


def test_the_inverse_uses_brent_rather_than_a_derivative_method(monkeypatch):
    """Newton is undefined at M = 1; the module must not have quietly adopted it."""
    from rocketforge.physics.compressible import prandtl_meyer as module

    calls = []
    original = module.brent

    def spy(*args, **kwargs):
        calls.append(args[1:3])
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "brent", spy)
    module.mach_from_nu(math.radians(30.0), AIR)
    assert calls, "the inverse must reach the project's own bracketed solver"
    assert calls[0][0] == 1.0, "the lower bracket end is exact and needs no margin"


# ---------------------------------------------------------------------------
# the array convenience
# ---------------------------------------------------------------------------


def test_array_inverse_matches_the_scalar_one():
    angles = np.radians(np.array([0.0, 5.0, 26.3797608134, 60.0, 100.0]))
    machs = pm.mach_from_nu_array(angles, AIR)
    for index, angle in enumerate(angles):
        assert machs[index] == pytest.approx(pm.mach_from_nu(float(angle), AIR).unwrap(),
                                             rel=1e-12)


def test_array_inverse_marks_unsolvable_angles_rather_than_failing():
    """A chart asking past the ceiling should see the curve stop, not crash."""
    angles = np.array([0.5, pm.nu_max(AIR) + 0.1])
    machs = pm.mach_from_nu_array(angles, AIR)
    assert math.isfinite(machs[0])
    assert math.isnan(machs[1])


# ---------------------------------------------------------------------------
# the expansion turn
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_zero_turn_leaves_the_flow_alone(gas):
    result = pm.expand(2.5, 0.0, gas).unwrap()
    assert result.mach2 == pytest.approx(2.5, rel=1e-12)
    assert result.pressure_ratio == pytest.approx(1.0, rel=1e-12)
    assert result.temperature_ratio == pytest.approx(1.0, rel=1e-12)
    assert result.density_ratio == pytest.approx(1.0, rel=1e-12)
    assert result.fan_angle == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", [1.0, 1.5, 2.0, 4.0])
@pytest.mark.parametrize("turn_deg", [1.0, 5.0, 15.0])
def test_expansion_accelerates_and_drops_every_static_property(gas, mach1, turn_deg):
    """The physical content of an expansion fan, asserted rather than assumed."""
    result = pm.expand(mach1, math.radians(turn_deg), gas).unwrap()
    assert result.mach2 > mach1
    assert result.pressure_ratio < 1.0
    assert result.temperature_ratio < 1.0
    assert result.density_ratio < 1.0
    assert result.mach_angle2 < result.mach_angle1


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_turn_is_exactly_the_change_in_nu(gas):
    for turn_deg in (0.5, 10.0, 30.0):
        turn = math.radians(turn_deg)
        result = pm.expand(2.0, turn, gas).unwrap()
        assert result.nu2 - result.nu1 == pytest.approx(turn, abs=1e-9)
        assert result.nu1 == pytest.approx(float(pm.nu(2.0, gas)), rel=1e-14)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_stagnation_state_is_untouched_by_an_expansion(gas):
    """Isentropic and adiabatic: p0 and T0 are the same on both sides.

    Checked through the isentropic relations rather than by asserting a stored
    1.0, so it is the physics being tested and not a literal.
    """
    result = pm.expand(2.0, math.radians(15.0), gas).unwrap()
    p01 = 1.0 / float(iso.pressure_ratio(result.mach1, gas))
    p02 = result.pressure_ratio / float(iso.pressure_ratio(result.mach2, gas))
    assert p02 == pytest.approx(p01, rel=1e-13)
    t01 = 1.0 / float(iso.temperature_ratio(result.mach1, gas))
    t02 = result.temperature_ratio / float(iso.temperature_ratio(result.mach2, gas))
    assert t02 == pytest.approx(t01, rel=1e-13)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_expansion_ratios_are_the_isentropic_quotients(gas):
    """The reuse requirement, asserted to machine precision.

    If an expansion-specific pressure formula ever appeared, it would agree to
    about 1e-12 and fail here at 1e-15, which is the point.
    """
    for mach1, turn_deg in ((1.5, 10.0), (2.0, 25.0), (4.0, 5.0)):
        result = pm.expand(mach1, math.radians(turn_deg), gas).unwrap()
        m1, m2 = result.mach1, result.mach2
        assert result.pressure_ratio == pytest.approx(
            float(iso.pressure_ratio(m2, gas)) / float(iso.pressure_ratio(m1, gas)), rel=1e-15)
        assert result.temperature_ratio == pytest.approx(
            float(iso.temperature_ratio(m2, gas)) / float(iso.temperature_ratio(m1, gas)),
            rel=1e-15)
        assert result.density_ratio == pytest.approx(
            float(iso.density_ratio(m2, gas)) / float(iso.density_ratio(m1, gas)), rel=1e-15)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_ideal_gas_law_holds_across_the_fan(gas):
    result = pm.expand(2.0, math.radians(20.0), gas).unwrap()
    assert result.pressure_ratio == pytest.approx(
        result.density_ratio * result.temperature_ratio, rel=1e-13)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_fan_angle_is_the_geometry_it_claims(gas):
    result = pm.expand(2.0, math.radians(15.0), gas).unwrap()
    assert result.fan_angle == pytest.approx(
        result.mach_angle1 - result.mach_angle2 + result.turn_angle, rel=1e-15)
    assert result.fan_angle > 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_a_turn_past_the_maximum_expansion_has_no_solution(gas):
    ceiling = pm.nu_max(gas)
    nu1 = float(pm.nu(2.0, gas))
    solution = pm.expand(2.0, ceiling - nu1 + 0.01, gas)
    assert solution.status is Status.NO_SOLUTION
    assert solution.value is None
    assert any(d.code == "NU_EXCEEDS_MAX" for d in solution.diagnostics)


def test_a_negative_turn_is_refused_rather_than_routed_into_a_compression():
    """expand() expands. A compression turn is a shock, and lives elsewhere."""
    with pytest.raises(DomainError, match="expand"):
        pm.expand(2.0, -math.radians(5.0), AIR)


def test_expansion_refuses_subsonic_upstream():
    with pytest.raises(SubsonicExpansionError):
        pm.expand(0.8, math.radians(5.0), AIR)


def test_expansion_describes_one_flow():
    with pytest.raises(SubsonicExpansionError):
        pm.expand(np.array([2.0, 3.0]), math.radians(5.0), AIR)


# ---------------------------------------------------------------------------
# the isentropic compression, and its honesty
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_isentropic_compression_reverses_an_expansion(gas):
    expanded = pm.expand(2.0, math.radians(12.0), gas).unwrap()
    recovered = pm.compress(expanded.mach2, math.radians(12.0), gas).unwrap()
    assert recovered.mach2 == pytest.approx(2.0, rel=1e-9)
    assert recovered.pressure_ratio == pytest.approx(1.0 / expanded.pressure_ratio, rel=1e-9)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_compression_decelerates_and_raises_every_static_property(gas):
    result = pm.compress(3.0, math.radians(10.0), gas).unwrap()
    assert result.mach2 < 3.0
    assert result.pressure_ratio > 1.0
    assert result.temperature_ratio > 1.0
    assert result.density_ratio > 1.0


def test_compression_says_it_is_an_idealisation():
    """A real concave turn shocks; the result must not let that pass unsaid."""
    solution = pm.compress(3.0, math.radians(10.0), AIR)
    codes = {d.code for d in solution.diagnostics}
    assert "ISENTROPIC_COMPRESSION" in codes
    message = next(d.message for d in solution.diagnostics
                   if d.code == "ISENTROPIC_COMPRESSION")
    assert "oblique shock" in message


def test_compression_below_sonic_has_no_solution():
    """Turning further than the flow has to give would take it below Mach 1."""
    nu1 = float(pm.nu(1.5, AIR))
    solution = pm.compress(1.5, nu1 + math.radians(5.0), AIR)
    assert solution.status is Status.NO_SOLUTION
    assert any(d.code == "NU_BELOW_ZERO" for d in solution.diagnostics)


def test_compressing_exactly_to_sonic_is_allowed():
    nu1 = float(pm.nu(1.5, AIR))
    result = pm.compress(1.5, nu1, AIR).unwrap()
    assert result.mach2 == pytest.approx(1.0, abs=1e-9)
