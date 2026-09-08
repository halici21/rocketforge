"""Verification of the area-Mach inverse.

The first production caller of the shared root solver, and the first relation
with two physical answers. Contracts under test come from
``docs/engineering/03_compressible_flow_specification.md`` section 3.4 (branch
policy, the sonic window, rejection below unity) and ``04`` sections 3.1 and 4
(brackets, tolerances, near-sonic conditioning).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import AreaRatioError, DomainError
from rocketforge.core.numerics import roots
from rocketforge.core.result import Severity, Status, UnusableSolutionError
from rocketforge.core.tolerances import DEFAULT_TOLERANCES, ToleranceSet
from rocketforge.physics.compressible import FlowBranch, PerfectGas
from rocketforge.physics.compressible import isentropic as iso

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]

AREA_RATIOS = (1.0001, 1.01, 1.1, 1.5, 2.0, 4.0, 10.0, 50.0, 100.0, 1000.0)


# ---------------------------------------------------------------------------
# branch is mandatory and is actually used
# ---------------------------------------------------------------------------


def test_branch_argument_is_required():
    """The relation has two roots; the API must never choose one silently."""
    with pytest.raises(TypeError):
        iso.mach_from_area_ratio(2.0, PerfectGas(gamma=1.4))  # type: ignore[call-arg]


@pytest.mark.parametrize("bad", ["subsonic", "sub", 0, None, True])
def test_branch_must_be_the_enum(bad):
    with pytest.raises(ValueError):
        iso.mach_from_area_ratio(2.0, PerfectGas(gamma=1.4), bad)  # type: ignore[arg-type]


def test_both_branch_is_refused_by_the_single_root_api():
    with pytest.raises(ValueError) as excinfo:
        iso.mach_from_area_ratio(2.0, PerfectGas(gamma=1.4), FlowBranch.BOTH)
    assert "mach_from_area_ratio_both" in str(excinfo.value)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_the_two_branches_give_different_answers(gas, area_ratio):
    subsonic = iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUBSONIC).unwrap()
    supersonic = iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUPERSONIC).unwrap()
    assert subsonic < 1.0 < supersonic


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach", [1.2, 2.0, 3.5, 6.0])
def test_asking_for_the_other_branch_returns_the_other_root(gas, mach):
    """Start supersonic, ask for subsonic, and get the alternate solution.

    This is what proves the branch argument does something: the same area ratio
    must come back as a different, genuinely subsonic Mach number, and that
    number must reproduce the area ratio through the forward relation.
    """
    area_ratio = float(iso.area_ratio(mach, gas))

    same = iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUPERSONIC).unwrap()
    assert same == pytest.approx(mach, rel=1e-9)

    other = iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUBSONIC).unwrap()
    assert other < 1.0
    assert other != pytest.approx(mach, rel=1e-3)
    # The alternate root must reproduce the same area ratio. The tolerance is
    # set by what the solver was asked for, not by the relation: near M -> 0,
    # A/A* ~ C/M, so an *absolute* Mach tolerance of 1e-10 on a root of order
    # 1e-3 is only about 1e-7 in relative area. Asserting tighter than that
    # would be asserting a tolerance nobody requested.
    allowed = 10.0 * DEFAULT_TOLERANCES.mach_abs_tol / other
    assert float(iso.area_ratio(other, gas)) == pytest.approx(area_ratio, rel=allowed)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach", [0.05, 0.2, 0.5, 0.9])
def test_starting_subsonic_the_supersonic_branch_returns_the_alternate(gas, mach):
    area_ratio = float(iso.area_ratio(mach, gas))
    same = iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUBSONIC).unwrap()
    other = iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUPERSONIC).unwrap()
    assert same == pytest.approx(mach, rel=1e-9)
    assert other > 1.0
    assert float(iso.area_ratio(other, gas)) == pytest.approx(area_ratio, rel=1e-9)


# ---------------------------------------------------------------------------
# round trips
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_subsonic_round_trip(gas):
    for mach in (1e-3, 0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99):
        area_ratio = float(iso.area_ratio(mach, gas))
        recovered = iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUBSONIC).unwrap()
        assert recovered == pytest.approx(mach, rel=1e-8, abs=1e-10)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_supersonic_round_trip(gas):
    for mach in (1.01, 1.1, 1.5, 2.0, 3.0, 5.0, 10.0, 25.0):
        area_ratio = float(iso.area_ratio(mach, gas))
        recovered = iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUPERSONIC).unwrap()
        assert recovered == pytest.approx(mach, rel=1e-8)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_round_trip_never_crosses_the_sonic_point(gas):
    """A subsonic request must never return a supersonic root, or vice versa."""
    for mach in np.linspace(0.02, 0.98, 40):
        recovered = iso.mach_from_area_ratio(
            float(iso.area_ratio(mach, gas)), gas, FlowBranch.SUBSONIC
        ).unwrap()
        assert recovered < 1.0
    for mach in np.linspace(1.02, 12.0, 40):
        recovered = iso.mach_from_area_ratio(
            float(iso.area_ratio(mach, gas)), gas, FlowBranch.SUPERSONIC
        ).unwrap()
        assert recovered > 1.0


# ---------------------------------------------------------------------------
# the sonic point
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("branch", [FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC])
def test_unit_area_ratio_returns_exactly_sonic_on_either_branch(gas, branch):
    solution = iso.mach_from_area_ratio(1.0, gas, branch)
    assert solution.value == 1.0
    assert solution.status is Status.OK
    assert any(d.code == "SONIC_EXACT" for d in solution.diagnostics)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_sonic_window_returns_one_without_iterating(gas):
    """Inside the window, exactly 1 is the most accurate answer available.

    Handing this to the root finder would be asking it to resolve a minimum
    where the derivative vanishes; the closed-form answer is both exact and
    free, and the convergence record says "analytic" rather than "brent".
    """
    tolerance = DEFAULT_TOLERANCES.area_sonic_tol
    # Strictly inside the window. 1.0 + tolerance is not usable here: the sum
    # rounds to a double whose distance from unity is 1.0000000827e-11, which
    # is outside the window by about 8e-19, so it correctly goes to the solver.
    for offset in (0.0, tolerance / 2, -tolerance / 2, tolerance / 10):
        solution = iso.mach_from_area_ratio(1.0 + offset, gas, FlowBranch.SUBSONIC)
        assert solution.value == 1.0
        assert solution.convergence is not None
        assert solution.convergence.method == "analytic"
        assert solution.convergence.iterations == 0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_just_outside_the_sonic_window_the_solver_runs(gas):
    solution = iso.mach_from_area_ratio(1.0 + 1e-6, gas, FlowBranch.SUPERSONIC)
    assert solution.ok
    assert solution.convergence is not None
    assert solution.convergence.method == "brent"
    assert solution.value > 1.0


def sonic_window_mach(gas) -> float:
    """How far from M = 1 the sonic area-ratio window reaches.

    A/A* - 1 = [2/(gamma+1)] (M-1)^2, so an area window of ``area_sonic_tol``
    corresponds to a Mach window of ``sqrt(area_sonic_tol (gamma+1)/2)`` --
    about 3.5e-6 at gamma = 1.4. Offsets inside that are answered with exactly
    1 by design; only offsets outside it resolve to a branch.
    """
    return math.sqrt(DEFAULT_TOLERANCES.area_sonic_tol * (gas.gamma + 1.0) / 2.0)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("epsilon", [1e-2, 1e-3, 1e-4, 1e-5])
def test_near_sonic_offsets_resolve_on_the_correct_side(gas, epsilon):
    """Symmetric offsets either side of sonic must not swap branches."""
    assert epsilon > sonic_window_mach(gas), "this test is about offsets outside the sonic window"
    for sign, branch in ((-1.0, FlowBranch.SUBSONIC), (1.0, FlowBranch.SUPERSONIC)):
        mach = 1.0 + sign * epsilon
        area_ratio = float(iso.area_ratio(mach, gas))
        recovered = iso.mach_from_area_ratio(area_ratio, gas, branch).unwrap()
        assert (recovered < 1.0) == (sign < 0.0)
        # Conditioning: A/A* - 1 goes as (M-1)^2, so a relative error d in the
        # area ratio becomes sqrt(d) in the Mach number. Allow for that rather
        # than demanding precision the relation cannot carry.
        assert recovered == pytest.approx(mach, rel=max(1e-6, 1e-8 / epsilon))


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("epsilon", [1e-6, 1e-7, 1e-9])
def test_offsets_inside_the_sonic_window_return_exactly_one(gas, epsilon):
    """Inside the window both branches answer 1 -- the documented behaviour.

    Not a limitation being tolerated: at these offsets the area ratio differs
    from unity by less than 1e-11, and 1 is the most accurate Mach number the
    relation can support.
    """
    assert epsilon < sonic_window_mach(gas)
    for sign, branch in ((-1.0, FlowBranch.SUBSONIC), (1.0, FlowBranch.SUPERSONIC)):
        area_ratio = float(iso.area_ratio(1.0 + sign * epsilon, gas))
        solution = iso.mach_from_area_ratio(area_ratio, gas, branch)
        assert solution.value == 1.0
        assert any(d.code == "SONIC_EXACT" for d in solution.diagnostics)


def test_near_sonic_solution_carries_the_advisory():
    gas = PerfectGas(gamma=1.4)
    area_ratio = float(iso.area_ratio(1.0 + 1e-5, gas))
    solution = iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUPERSONIC)
    assert solution.status is Status.OK_WITH_WARNINGS
    near = [d for d in solution.diagnostics if d.code == "NEAR_SONIC"]
    assert near and near[0].severity is Severity.WARNING


def test_far_from_sonic_there_is_no_advisory():
    gas = PerfectGas(gamma=1.4)
    solution = iso.mach_from_area_ratio(4.0, gas, FlowBranch.SUPERSONIC)
    assert solution.status is Status.OK
    assert not [d for d in solution.diagnostics if d.code == "NEAR_SONIC"]


# ---------------------------------------------------------------------------
# domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0.999, 0.8, 0.5, 0.0])
@pytest.mark.parametrize("branch", [FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC])
def test_area_ratio_below_one_is_rejected(bad, branch):
    """Never clamped to 1: A/A* < 1 is not a flow state."""
    with pytest.raises(AreaRatioError):
        iso.mach_from_area_ratio(bad, PerfectGas(gamma=1.4), branch)


@pytest.mark.parametrize("bad", [-1.0, -0.001])
def test_negative_area_ratio_is_rejected(bad):
    with pytest.raises(AreaRatioError):
        iso.mach_from_area_ratio(bad, PerfectGas(gamma=1.4), FlowBranch.SUBSONIC)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_area_ratio_is_rejected(bad):
    with pytest.raises(DomainError):
        iso.mach_from_area_ratio(bad, PerfectGas(gamma=1.4), FlowBranch.SUBSONIC)


def test_scalar_api_rejects_an_array():
    with pytest.raises(DomainError) as excinfo:
        iso.mach_from_area_ratio(np.array([2.0, 3.0]), PerfectGas(gamma=1.4), FlowBranch.SUBSONIC)
    assert "mach_from_area_ratio_array" in str(excinfo.value)


def test_area_ratio_error_is_a_domain_error():
    assert issubclass(AreaRatioError, DomainError)


# ---------------------------------------------------------------------------
# the Solution wrapper
# ---------------------------------------------------------------------------


def test_solution_carries_convergence_detail():
    gas = PerfectGas(gamma=1.4)
    solution = iso.mach_from_area_ratio(4.0, gas, FlowBranch.SUPERSONIC)
    convergence = solution.convergence
    assert convergence is not None
    assert convergence.converged is True
    assert convergence.method == "brent"
    assert 0 < convergence.iterations <= 60
    assert convergence.bracket is not None
    low, high = convergence.bracket
    assert low <= solution.value <= high
    assert convergence.residual < 1e-8


def test_solution_carries_provenance():
    solution = iso.mach_from_area_ratio(4.0, PerfectGas(gamma=1.4), FlowBranch.SUPERSONIC)
    assert solution.provenance
    reference = solution.provenance[0]
    assert reference.identifier == "isentropic.area_ratio.v1"
    assert reference.model == "perfect_gas_isentropic_v1"
    assert reference.source
    assert reference.assumptions


def test_solution_echoes_its_inputs():
    solution = iso.mach_from_area_ratio(4.0, PerfectGas(gamma=1.3), FlowBranch.SUBSONIC)
    assert solution.inputs == {"area_ratio": 4.0, "gamma": 1.3}


def test_solution_is_immutable():
    solution = iso.mach_from_area_ratio(4.0, PerfectGas(gamma=1.4), FlowBranch.SUBSONIC)
    with pytest.raises(Exception):
        solution.value = 0.0  # type: ignore[misc]


def test_extrapolated_gamma_advisory_reaches_the_solution():
    """A questionable gas model must be visible wherever it is used."""
    gas = PerfectGas(gamma=2.5)
    solution = iso.mach_from_area_ratio(3.0, gas, FlowBranch.SUPERSONIC)
    assert solution.ok
    assert solution.status is Status.OK_WITH_WARNINGS
    assert any(d.code == "EXTRAPOLATED_GAMMA" for d in solution.diagnostics)


def test_unwrap_returns_the_value_when_usable():
    solution = iso.mach_from_area_ratio(2.0, PerfectGas(gamma=1.4), FlowBranch.SUBSONIC)
    assert solution.unwrap() == solution.value


# ---------------------------------------------------------------------------
# non-convergence is surfaced, never hidden
# ---------------------------------------------------------------------------


def test_non_convergence_is_reported_and_not_silently_retried():
    """With a budget of one iteration the answer cannot be trusted, and says so.

    No automatic retry at a looser tolerance, and no exception either: the
    caller is handed the best estimate together with the fact that it did not
    converge.
    """
    tight = ToleranceSet(max_iter=1)
    solution = iso.mach_from_area_ratio(50.0, PerfectGas(gamma=1.4), FlowBranch.SUPERSONIC, tight)
    assert solution.status is Status.NOT_CONVERGED
    assert solution.ok is False
    assert solution.value is not None and math.isfinite(solution.value)
    assert solution.convergence is not None and solution.convergence.converged is False
    assert any(d.code == "NOT_CONVERGED" and d.severity is Severity.ERROR
               for d in solution.diagnostics)


def test_unwrap_raises_on_a_non_converged_solution():
    tight = ToleranceSet(max_iter=1)
    solution = iso.mach_from_area_ratio(50.0, PerfectGas(gamma=1.4), FlowBranch.SUPERSONIC, tight)
    with pytest.raises(UnusableSolutionError):
        solution.unwrap()


# ---------------------------------------------------------------------------
# solver reuse
# ---------------------------------------------------------------------------


def test_the_inverse_uses_the_shared_root_solver(monkeypatch):
    """No private bisection hidden inside the physics module."""
    calls = []
    original = roots.brent

    def spy(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(iso, "brent", spy)
    iso.mach_from_area_ratio(4.0, PerfectGas(gamma=1.4), FlowBranch.SUPERSONIC)
    assert len(calls) == 1
    assert calls[0]["xtol"] == DEFAULT_TOLERANCES.mach_abs_tol
    assert calls[0]["rtol"] == DEFAULT_TOLERANCES.mach_rel_tol
    assert calls[0]["max_iter"] == DEFAULT_TOLERANCES.max_iter


def test_tolerances_are_taken_from_the_supplied_set(monkeypatch):
    calls = []
    original = roots.brent

    def spy(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(iso, "brent", spy)
    custom = ToleranceSet(mach_abs_tol=1e-8, mach_rel_tol=1e-10, max_iter=57)
    iso.mach_from_area_ratio(4.0, PerfectGas(gamma=1.4), FlowBranch.SUPERSONIC, custom)
    assert calls[0]["xtol"] == 1e-8
    assert calls[0]["rtol"] == 1e-10
    assert calls[0]["max_iter"] == 57


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_brackets_hold_the_root_and_the_solve_is_cheap(gas, area_ratio):
    """The derived brackets must contain the root without a long search."""
    for branch in (FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC):
        solution = iso.mach_from_area_ratio(area_ratio, gas, branch)
        assert solution.ok
        convergence = solution.convergence
        assert convergence is not None and convergence.iterations <= 60
        low, high = convergence.bracket
        assert low <= solution.value <= high


def test_extreme_area_ratio_still_converges():
    """A/A* = 1e6 is past any real nozzle but must not misbehave."""
    solution = iso.mach_from_area_ratio(1.0e6, PerfectGas(gamma=1.4), FlowBranch.SUPERSONIC)
    assert solution.ok
    assert solution.value > 10.0
    assert solution.value <= DEFAULT_TOLERANCES.mach_ceiling


# ---------------------------------------------------------------------------
# both-branch API
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("area_ratio", [1.5, 2.0, 4.0, 10.0])
def test_both_returns_named_fields_matching_the_single_branch_calls(gas, area_ratio):
    pair = iso.mach_from_area_ratio_both(area_ratio, gas).unwrap()
    assert pair.area_ratio == area_ratio
    assert pair.sonic is False
    assert pair.subsonic == pytest.approx(
        iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUBSONIC).unwrap(), rel=1e-15
    )
    assert pair.supersonic == pytest.approx(
        iso.mach_from_area_ratio(area_ratio, gas, FlowBranch.SUPERSONIC).unwrap(), rel=1e-15
    )
    assert pair.subsonic < 1.0 < pair.supersonic


def test_both_at_the_sonic_point():
    pair = iso.mach_from_area_ratio_both(1.0, PerfectGas(gamma=1.4)).unwrap()
    assert pair.subsonic == 1.0
    assert pair.supersonic == 1.0
    assert pair.sonic is True


def test_both_does_not_repeat_the_same_diagnostic():
    solution = iso.mach_from_area_ratio_both(1.0, PerfectGas(gamma=2.5))
    codes = [d.code for d in solution.diagnostics]
    assert len(codes) == len(set(codes)), f"duplicated diagnostics: {codes}"


def test_both_result_is_immutable():
    pair = iso.mach_from_area_ratio_both(2.0, PerfectGas(gamma=1.4)).unwrap()
    with pytest.raises(Exception):
        pair.subsonic = 0.5  # type: ignore[misc]


# ---------------------------------------------------------------------------
# array API
# ---------------------------------------------------------------------------


def test_array_inverse_matches_the_scalar_calls():
    gas = PerfectGas(gamma=1.4)
    ratios = np.array([1.2, 2.0, 5.0, 20.0])
    result = iso.mach_from_area_ratio_array(ratios, gas, FlowBranch.SUPERSONIC)
    assert isinstance(result, np.ndarray) and result.shape == ratios.shape
    for index, ratio in enumerate(ratios):
        assert result[index] == pytest.approx(
            iso.mach_from_area_ratio(float(ratio), gas, FlowBranch.SUPERSONIC).unwrap(), rel=1e-15
        )


def test_array_inverse_preserves_shape():
    gas = PerfectGas(gamma=1.4)
    ratios = np.array([[1.5, 2.0], [3.0, 4.0]])
    assert iso.mach_from_area_ratio_array(ratios, gas, FlowBranch.SUBSONIC).shape == (2, 2)


def test_array_inverse_rejects_a_bad_element_rather_than_returning_nan():
    """A NaN in a plotted series is a silent hole; the call fails instead."""
    gas = PerfectGas(gamma=1.4)
    with pytest.raises(AreaRatioError):
        iso.mach_from_area_ratio_array(np.array([2.0, 0.5, 3.0]), gas, FlowBranch.SUBSONIC)


def test_array_inverse_round_trips():
    gas = PerfectGas(gamma=1.3)
    machs = np.array([1.1, 1.5, 2.5, 4.0, 8.0])
    ratios = iso.area_ratio(machs, gas)
    recovered = iso.mach_from_area_ratio_array(ratios, gas, FlowBranch.SUPERSONIC)
    assert np.allclose(recovered, machs, rtol=1e-8)


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------


def test_repeated_solves_are_bitwise_identical():
    gas = PerfectGas(gamma=1.4)
    first = iso.mach_from_area_ratio(4.0, gas, FlowBranch.SUPERSONIC)
    for _ in range(5):
        again = iso.mach_from_area_ratio(4.0, gas, FlowBranch.SUPERSONIC)
        assert again.value.hex() == first.value.hex()
        assert again.convergence == first.convergence


def test_interleaved_solves_do_not_disturb_each_other():
    gas = PerfectGas(gamma=1.4)
    a1 = iso.mach_from_area_ratio(2.0, gas, FlowBranch.SUBSONIC).unwrap()
    b1 = iso.mach_from_area_ratio(9.0, gas, FlowBranch.SUPERSONIC).unwrap()
    a2 = iso.mach_from_area_ratio(2.0, gas, FlowBranch.SUBSONIC).unwrap()
    b2 = iso.mach_from_area_ratio(9.0, gas, FlowBranch.SUPERSONIC).unwrap()
    assert a1.hex() == a2.hex()
    assert b1.hex() == b2.hex()
