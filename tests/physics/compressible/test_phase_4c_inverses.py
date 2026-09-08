"""The Phase 4C inverse relations.

Three of the four are closed form and must invert their forward relation
exactly. The fourth -- upstream Mach from a stagnation-pressure loss -- is the
only place this phase iterates, and it is held to the same round-trip
standard rather than to a looser "close enough".

The mass-flow inverse gets the most attention, because it is not a new solve
at all: it is the area-Mach inversion wearing different units, and the tests
below assert that identity rather than taking it on trust from a docstring.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError
from rocketforge.core.result import Status
from rocketforge.physics.compressible import FlowBranch, PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import mass_flow as mf
from rocketforge.physics.compressible import normal_shock as ns

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]
AIR = PerfectGas(gamma=1.4)


# ---------------------------------------------------------------------------
# mass flow: the identity that makes the inverse free
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_mass_flow_ratio_is_the_reciprocal_area_ratio(gas):
    """MFP(M)/Gamma = A*/A, for every Mach number.

    The identity the inverse is built on. If it ever failed, the inverse would
    be solving the wrong curve -- so it is asserted directly, on a dense grid,
    before anything is inverted.
    """
    grid = np.concatenate([np.linspace(0.01, 0.99, 300), np.linspace(1.01, 12.0, 300)])
    ratio = np.asarray(mf.mass_flow_parameter(grid, gas)) / mf.choked_mass_flow_coefficient(gas)
    area = np.asarray(iso.area_ratio(grid, gas))
    np.testing.assert_allclose(ratio, 1.0 / area, rtol=1e-13)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_sonic_flow_is_the_full_choked_flow(gas):
    assert mf.mass_flow_over_choked(1.0, gas) == pytest.approx(1.0, rel=1e-15)
    assert iso.area_ratio(1.0, gas) == pytest.approx(1.0, rel=1e-15)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach", [0.05, 0.3, 0.8, 0.99])
def test_subsonic_mass_flow_inverse_round_trips(gas, mach):
    ratio = float(mf.mass_flow_over_choked(mach, gas))
    solution = mf.mach_from_mass_flow_ratio(ratio, gas, FlowBranch.SUBSONIC)
    assert solution.ok
    assert solution.unwrap() == pytest.approx(mach, abs=1e-9)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach", [1.05, 2.0, 4.0, 9.0])
def test_supersonic_mass_flow_inverse_round_trips(gas, mach):
    ratio = float(mf.mass_flow_over_choked(mach, gas))
    solution = mf.mach_from_mass_flow_ratio(ratio, gas, FlowBranch.SUPERSONIC)
    assert solution.ok
    assert solution.unwrap() == pytest.approx(mach, rel=1e-9)


def test_the_two_branches_are_different_answers_to_the_same_question():
    """Half the choked flow is passed by one subsonic and one supersonic state."""
    subsonic = mf.mach_from_mass_flow_ratio(0.5, AIR, FlowBranch.SUBSONIC).unwrap()
    supersonic = mf.mach_from_mass_flow_ratio(0.5, AIR, FlowBranch.SUPERSONIC).unwrap()
    assert subsonic < 1.0 < supersonic
    assert mf.mass_flow_over_choked(subsonic, AIR) == pytest.approx(0.5, abs=1e-9)
    assert mf.mass_flow_over_choked(supersonic, AIR) == pytest.approx(0.5, abs=1e-9)


def test_full_flow_returns_the_sonic_state_on_either_branch():
    for branch in (FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC):
        assert mf.mach_from_mass_flow_ratio(1.0, AIR, branch).unwrap() == pytest.approx(1.0)


def test_inverse_delegates_rather_than_re_solving(monkeypatch):
    """The identity must be *used*, not merely documented.

    If a second bespoke solve were ever added, this fails -- which is the point.
    """
    calls = []
    original = iso.mach_from_area_ratio

    def spy(area_ratio_value, gas, branch, tolerances=None):
        calls.append(area_ratio_value)
        return original(area_ratio_value, gas, branch) if tolerances is None else original(
            area_ratio_value, gas, branch, tolerances)

    monkeypatch.setattr(iso, "mach_from_area_ratio", spy)
    mf.mach_from_mass_flow_ratio(0.25, AIR, FlowBranch.SUBSONIC)
    assert calls == [pytest.approx(4.0)]


@pytest.mark.parametrize("bad", [1.5, 2.0])
def test_flow_above_choked_is_refused(bad):
    with pytest.raises(DomainError, match="cannot exceed 1"):
        mf.mach_from_mass_flow_ratio(bad, AIR, FlowBranch.SUBSONIC)


@pytest.mark.parametrize("bad", [0.0, -0.5, math.nan, math.inf])
def test_non_positive_or_non_finite_flow_ratio_refused(bad):
    with pytest.raises(DomainError):
        mf.mach_from_mass_flow_ratio(bad, AIR, FlowBranch.SUBSONIC)


def test_mass_flow_inverse_requires_an_explicit_branch():
    with pytest.raises(ValueError, match="branch"):
        mf.mach_from_mass_flow_ratio(0.5, AIR, FlowBranch.BOTH)


# ---------------------------------------------------------------------------
# normal shock: the closed-form inverses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", [1.0, 1.2, 2.0, 3.5, 8.0, 20.0])
def test_density_inverse_round_trips(gas, mach1):
    ratio = float(ns.density_ratio(mach1, gas))
    assert ns.mach_upstream_from_density_ratio(ratio, gas) == pytest.approx(mach1, rel=1e-11)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_density_inverse_refuses_the_unreachable_compression(gas):
    limit = ns.density_ratio_limit(gas)
    with pytest.raises(DomainError, match="strong-shock limit"):
        ns.mach_upstream_from_density_ratio(limit, gas)
    with pytest.raises(DomainError):
        ns.mach_upstream_from_density_ratio(limit * 1.01, gas)
    # Just inside the limit is legal, and gives a very strong shock.
    assert ns.mach_upstream_from_density_ratio(limit * (1.0 - 1e-6), gas) > 100.0


@pytest.mark.parametrize("bad", [0.99, 0.5, 0.0])
def test_density_inverse_refuses_an_expansion(bad):
    with pytest.raises(DomainError, match="compresses"):
        ns.mach_upstream_from_density_ratio(bad, AIR)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", [1.0, 1.5, 2.0, 5.0, 15.0])
def test_downstream_mach_inverse_round_trips(gas, mach1):
    mach2 = float(ns.mach_downstream(mach1, gas))
    assert ns.mach_upstream_from_downstream_mach(mach2, gas) == pytest.approx(mach1, rel=1e-10)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_relation_really_is_an_involution(gas):
    """Applying it twice returns the input, which is what makes it its own inverse."""
    for mach1 in (1.0, 1.3, 2.4, 6.0):
        once = float(ns.mach_downstream(mach1, gas))
        twice = float(ns.mach_downstream(once, gas)) if once == 1.0 else float(
            ns.mach_upstream_from_downstream_mach(once, gas)
        )
        assert twice == pytest.approx(mach1, rel=1e-10)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_downstream_inverse_refuses_values_off_the_curve(gas):
    limit = ns.mach_downstream_limit(gas)
    with pytest.raises(DomainError, match="strong-shock limit"):
        ns.mach_upstream_from_downstream_mach(limit, gas)
    with pytest.raises(DomainError, match="strong-shock limit"):
        ns.mach_upstream_from_downstream_mach(limit * 0.5, gas)
    with pytest.raises(DomainError, match="subsonic"):
        ns.mach_upstream_from_downstream_mach(1.2, gas)


# ---------------------------------------------------------------------------
# normal shock: the one relation that iterates
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", [1.05, 1.5, 2.0, 3.0, 6.0, 15.0, 40.0])
def test_stagnation_pressure_inverse_round_trips(gas, mach1):
    ratio = float(ns.stagnation_pressure_ratio(mach1, gas))
    solution = ns.mach_upstream_from_stagnation_pressure_ratio(ratio, gas)
    assert solution.ok
    assert solution.unwrap() == pytest.approx(mach1, rel=1e-8)


def test_stagnation_pressure_inverse_reports_how_it_converged():
    solution = ns.mach_upstream_from_stagnation_pressure_ratio(0.7209, AIR)
    assert solution.status is Status.OK
    assert solution.convergence is not None
    assert solution.convergence.converged
    assert solution.convergence.iterations > 0
    assert abs(solution.convergence.residual) <= 1e-9
    assert solution.convergence.bracket is not None
    assert solution.inputs["gamma"] == pytest.approx(1.4)


def test_no_loss_is_answered_exactly_without_iterating():
    """p02/p01 = 1 is the zero-strength shock; iterating on it would be theatre."""
    solution = ns.mach_upstream_from_stagnation_pressure_ratio(1.0, AIR)
    assert solution.unwrap() == 1.0
    assert solution.convergence is None


def test_a_severe_loss_widens_the_bracket_rather_than_failing():
    """A ratio of 1e-9 lies past the default Mach ceiling and must still solve."""
    solution = ns.mach_upstream_from_stagnation_pressure_ratio(1e-9, AIR)
    assert solution.ok
    mach = solution.unwrap()
    assert mach > 100.0
    assert ns.stagnation_pressure_ratio(mach, AIR) == pytest.approx(1e-9, rel=1e-6)


@pytest.mark.parametrize("bad", [1.0 + 1e-12, 1.5, 10.0])
def test_a_stagnation_pressure_gain_is_refused(bad):
    with pytest.raises(DomainError, match="never creates it"):
        ns.mach_upstream_from_stagnation_pressure_ratio(bad, AIR)


@pytest.mark.parametrize("bad", [0.0, -0.2, math.nan, math.inf])
def test_impossible_stagnation_ratios_refused(bad):
    with pytest.raises(DomainError):
        ns.mach_upstream_from_stagnation_pressure_ratio(bad, AIR)


def test_provenance_names_the_relation_behind_the_answer():
    solution = ns.mach_upstream_from_stagnation_pressure_ratio(0.5, AIR)
    assert solution.provenance, "an iterative result must say which relation it inverted"


# ---------------------------------------------------------------------------
# the inverses agree with each other
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", [1.4, 2.6, 5.0, 11.0])
def test_all_four_shock_inverses_recover_the_same_upstream_mach(gas, mach1):
    """Four measurements of one shock must name one flow.

    Pressure jump, density jump, downstream Mach and stagnation-pressure loss
    are what an experiment actually reads. If they disagreed, one of the
    forward relations would be wrong -- and this is the test that would say so.
    """
    result = ns.solve(mach1, gas)
    assert ns.mach_upstream_from_pressure_ratio(result.pressure_ratio, gas) == pytest.approx(
        mach1, rel=1e-11)
    assert ns.mach_upstream_from_density_ratio(result.density_ratio, gas) == pytest.approx(
        mach1, rel=1e-11)
    assert ns.mach_upstream_from_downstream_mach(result.mach2, gas) == pytest.approx(
        mach1, rel=1e-10)
    assert ns.mach_upstream_from_stagnation_pressure_ratio(
        result.stagnation_pressure_ratio, gas).unwrap() == pytest.approx(mach1, rel=1e-8)


# ---------------------------------------------------------------------------
# regression: the limit's own round-off
# ---------------------------------------------------------------------------


def test_the_textbook_limit_typed_exactly_is_refused():
    """Regression. rho2/rho1 = 6 is the number every text prints for air.

    ``(gamma+1)/(gamma-1)`` evaluates to 6.000000000000001 in float64, so a
    ``>= limit`` guard let a typed 6.0 through and the inverse answered
    M1 = 1.6e8 -- an entirely fictitious number wearing a valid result's
    clothes. The guard now tests the denominator against its own round-off.
    """
    with pytest.raises(DomainError, match="strong-shock limit"):
        ns.mach_upstream_from_density_ratio(6.0, AIR)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_the_computed_limit_and_its_neighbours_are_all_refused(gas):
    """Whichever side the limit's own rounding falls, none of it is answerable."""
    limit = ns.density_ratio_limit(gas)
    for ratio in (limit, math.nextafter(limit, 0.0), math.nextafter(limit, math.inf)):
        with pytest.raises(DomainError):
            ns.mach_upstream_from_density_ratio(ratio, gas)

    floor = ns.mach_downstream_limit(gas)
    for mach2 in (floor, math.nextafter(floor, 0.0), math.nextafter(floor, 1.0)):
        with pytest.raises(DomainError):
            ns.mach_upstream_from_downstream_mach(mach2, gas)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_a_refused_input_is_always_one_whose_answer_was_worthless(gas):
    """The guard must not refuse anything an engineer could have wanted.

    Every ratio that maps to a Mach number below 1000 -- far past anything the
    perfect-gas model applies to -- must still be answered.
    """
    for mach1 in (2.0, 10.0, 50.0, 200.0, 1000.0):
        ratio = float(ns.density_ratio(mach1, gas))
        assert ns.mach_upstream_from_density_ratio(ratio, gas) == pytest.approx(
            mach1, rel=1e-6)
        downstream = float(ns.mach_downstream(mach1, gas))
        assert ns.mach_upstream_from_downstream_mach(downstream, gas) == pytest.approx(
            mach1, rel=1e-5)
