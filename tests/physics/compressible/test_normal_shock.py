"""Verification of the normal-shock relations.

Covers the jump relations, the domain rule that keeps the second law intact,
the weak- and strong-shock limits, the physical invariants of ``05`` section 9,
and a cross-module reconstruction of the stagnation-pressure ratio from the
isentropic relations -- which is what proves the two modules agree rather than
merely coexisting.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError, SubsonicShockError
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import normal_shock as ns

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]
AIR = PerfectGas(gamma=1.4)

# Deterministic upstream grid: just above sonic, the working range, and strong.
MACH_GRID = np.array([
    1.0, 1.0001, 1.001, 1.01, 1.05, 1.2, 1.5, 2.0, 2.5, 3.0,
    4.0, 5.0, 8.0, 12.0, 20.0, 50.0,
])

#: Smallest shock strength whose stagnation-pressure loss is resolvable in
#: double precision. The loss goes as (M1^2-1)^3, so at M1 - 1 = 1e-4 it is
#: about 1.3e-12 -- four orders above eps -- while at 1e-6 it is 1e-18 and
#: vanishes into rounding. See the module docstring of ``normal_shock``.
RESOLVABLE_SHOCK = 1e-4


# ---------------------------------------------------------------------------
# the relations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_relations_match_their_closed_forms(gas):
    gamma = gas.gamma
    for mach in MACH_GRID:
        squared = mach * mach
        half = 0.5 * (gamma - 1.0)

        expected_m2 = math.sqrt((1.0 + half * squared) / (gamma * squared - half))
        assert ns.mach_downstream(mach, gas) == pytest.approx(expected_m2, rel=1e-14)

        expected_p = 1.0 + 2.0 * gamma / (gamma + 1.0) * (squared - 1.0)
        assert ns.pressure_ratio(mach, gas) == pytest.approx(expected_p, rel=1e-14)

        expected_rho = (gamma + 1.0) * squared / (2.0 + (gamma - 1.0) * squared)
        assert ns.density_ratio(mach, gas) == pytest.approx(expected_rho, rel=1e-14)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_ideal_gas_law_holds_across_the_shock(gas):
    """p2/p1 = (rho2/rho1)(T2/T1) exactly, because T2/T1 is derived from them."""
    for mach in MACH_GRID:
        p = float(ns.pressure_ratio(mach, gas))
        rho = float(ns.density_ratio(mach, gas))
        t = float(ns.temperature_ratio(mach, gas))
        assert p == pytest.approx(rho * t, rel=1e-15)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_entropy_change_is_minus_log_of_the_stagnation_ratio(gas):
    for mach in MACH_GRID:
        expected = -math.log(float(ns.stagnation_pressure_ratio(mach, gas)))
        assert ns.entropy_change(mach, gas) == pytest.approx(expected, rel=1e-14)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_area_star_ratio_is_the_reciprocal_stagnation_ratio(gas):
    for mach in MACH_GRID:
        assert ns.area_star_ratio(mach, gas) == pytest.approx(
            1.0 / float(ns.stagnation_pressure_ratio(mach, gas)), rel=1e-15
        )


# ---------------------------------------------------------------------------
# cross-module reconstruction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_stagnation_pressure_ratio_reconstructed_from_isentropic_relations(gas):
    """Rebuild p02/p01 from a different route and require agreement.

        p02/p01 = (p02/p2) * (p2/p1) * (p1/p01)

    The middle term is the shock's static jump; the outer two are isentropic
    stagnation relations at the downstream and upstream Mach numbers. If the
    two modules ever disagreed, this is where it would show.
    """
    for mach1 in MACH_GRID:
        mach2 = float(ns.mach_downstream(mach1, gas))
        downstream_stagnation = 1.0 / float(iso.pressure_ratio(mach2, gas))   # p02/p2
        static_jump = float(ns.pressure_ratio(mach1, gas))                    # p2/p1
        upstream_static = float(iso.pressure_ratio(mach1, gas))               # p1/p01
        reconstructed = downstream_stagnation * static_jump * upstream_static
        assert reconstructed == pytest.approx(
            float(ns.stagnation_pressure_ratio(mach1, gas)), rel=1e-12
        ), f"routes disagree at M1 = {mach1}, gamma = {gas.gamma}"


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_pitot_ratio_is_the_composition_it_claims_to_be(gas):
    for mach in MACH_GRID:
        expected = (float(ns.stagnation_pressure_ratio(mach, gas))
                    / float(iso.pressure_ratio(mach, gas)))
        assert ns.stagnation_pressure_over_upstream_static(mach, gas) == pytest.approx(
            expected, rel=1e-15
        )


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_stagnation_temperature_is_conserved(gas):
    """Adiabatic: T02 = T01 exactly, and the result says so as a literal."""
    for mach in (1.0, 2.0, 5.0):
        assert ns.solve(mach, gas).stagnation_temperature_ratio == 1.0


# ---------------------------------------------------------------------------
# physical invariants over a grid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_downstream_flow_is_always_subsonic(gas):
    grid = np.linspace(1.0 + 1e-6, 40.0, 4000)
    downstream = ns.mach_downstream(grid, gas)
    assert np.all(downstream < 1.0)
    assert np.all(downstream > 0.0)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_static_properties_all_increase(gas):
    grid = np.linspace(1.0 + 1e-6, 40.0, 4000)
    assert np.all(ns.pressure_ratio(grid, gas) > 1.0)
    assert np.all(ns.density_ratio(grid, gas) > 1.0)
    assert np.all(ns.temperature_ratio(grid, gas) > 1.0)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_stagnation_pressure_falls_and_stays_positive(gas):
    grid = np.linspace(1.0 + RESOLVABLE_SHOCK, 40.0, 4000)
    ratio = ns.stagnation_pressure_ratio(grid, gas)
    assert np.all(ratio < 1.0)
    assert np.all(ratio > 0.0)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_stagnation_pressure_loss_grows_monotonically(gas):
    """A stronger shock always costs more stagnation pressure."""
    grid = np.linspace(1.0 + RESOLVABLE_SHOCK, 30.0, 5000)
    assert np.all(np.diff(ns.stagnation_pressure_ratio(grid, gas)) < 0.0)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_entropy_increases_for_every_real_shock(gas):
    """The second law, made arithmetic."""
    grid = np.linspace(1.0 + RESOLVABLE_SHOCK, 30.0, 3000)
    change = ns.entropy_change(grid, gas)
    assert np.all(change > 0.0)
    assert np.all(np.diff(change) > 0.0)
    assert ns.entropy_change(1.0, gas) == pytest.approx(0.0, abs=1e-15)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_weak_shock_loss_follows_the_cubic_law(gas):
    """Where the loss is resolvable, it must follow the analytic weak-shock law.

        1 - p02/p01  ->  [2 gamma / (3 (gamma+1)^2)] (M1^2 - 1)^3

    This is the assertion that makes the unresolvable band below it a
    numerical statement rather than an excuse: the relation demonstrably has
    the right cubic behaviour right down to where doubles run out.
    """
    coefficient = 2.0 * gas.gamma / (3.0 * (gas.gamma + 1.0) ** 2)
    for excess in (1e-4, 1e-3, 1e-2):
        mach = 1.0 + excess
        loss = 1.0 - float(ns.stagnation_pressure_ratio(mach, gas))
        expected = coefficient * (mach * mach - 1.0) ** 3
        assert loss == pytest.approx(expected, rel=6.0 * excess + 1e-6)
        assert loss > 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_unresolvable_weak_shocks_stay_within_an_ulp_of_no_shock(gas):
    """Below the resolvable band the loss is smaller than double precision.

    Documented in the module docstring: 1 - p02/p01 goes as (M1^2-1)^3, which
    for M1 - 1 < 1e-5 is below the spacing of doubles near 1. Nothing is
    clamped to hide that, so the honest assertion is "indistinguishable from
    no shock", not "strictly less than one".
    """
    floor = 8.0 * float(np.finfo(float).eps)
    for excess in (0.0, 1e-9, 1e-7, 1e-6):
        mach = 1.0 + excess
        assert abs(float(ns.stagnation_pressure_ratio(mach, gas)) - 1.0) <= floor
        assert abs(float(ns.entropy_change(mach, gas))) <= floor
        assert abs(float(ns.area_star_ratio(mach, gas)) - 1.0) <= floor


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_density_ratio_stays_below_its_strong_shock_limit(gas):
    """A calorically perfect gas cannot be compressed past (gamma+1)/(gamma-1)."""
    limit = ns.density_ratio_limit(gas)
    assert limit == pytest.approx((gas.gamma + 1.0) / (gas.gamma - 1.0), rel=1e-15)
    grid = np.linspace(1.0, 200.0, 5000)
    assert np.all(ns.density_ratio(grid, gas) < limit)

    # The approach is not merely "close for a big number": the shortfall is
    # 2 / (2 + (gamma-1) M1^2) exactly, so assert that instead of guessing a
    # tolerance. A wrong exponent anywhere in the relation breaks this.
    for mach in (10.0, 50.0, 500.0):
        shortfall = 1.0 - float(ns.density_ratio(mach, gas)) / limit
        expected = 2.0 / (2.0 + (gas.gamma - 1.0) * mach * mach)
        assert shortfall == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_downstream_mach_approaches_its_strong_shock_limit(gas):
    limit = ns.mach_downstream_limit(gas)
    assert limit == pytest.approx(math.sqrt((gas.gamma - 1.0) / (2.0 * gas.gamma)), rel=1e-15)

    # M2 falls towards the limit from above and never crosses it.
    grid = np.linspace(1.0, 200.0, 3000)
    downstream = ns.mach_downstream(grid, gas)
    assert np.all(downstream >= limit)
    assert np.all(np.diff(downstream) < 0.0)

    # Convergence is O(1/M1^2), so each tenfold rise in M1 must cut the
    # remaining excess by about a hundred.
    excess = [float(ns.mach_downstream(m, gas)) - limit for m in (10.0, 100.0, 1000.0)]
    assert excess[0] > excess[1] > excess[2] > 0.0
    assert excess[0] / excess[1] == pytest.approx(100.0, rel=0.03)
    assert excess[1] / excess[2] == pytest.approx(100.0, rel=1e-3)


def test_air_strong_shock_limits_are_the_familiar_numbers():
    assert ns.density_ratio_limit(AIR) == pytest.approx(6.0, rel=1e-15)
    assert ns.mach_downstream_limit(AIR) == pytest.approx(0.37796, abs=1e-5)


# ---------------------------------------------------------------------------
# limits
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("epsilon", [1e-2, 1e-4, 1e-6, 1e-8])
def test_weak_shock_approaches_the_identity(gas, epsilon):
    """As M1 -> 1 the shock vanishes and every ratio tends to 1."""
    mach = 1.0 + epsilon
    tolerance = max(50.0 * epsilon, 1e-12)
    assert ns.mach_downstream(mach, gas) == pytest.approx(1.0, abs=tolerance)
    assert ns.pressure_ratio(mach, gas) == pytest.approx(1.0, abs=tolerance)
    assert ns.density_ratio(mach, gas) == pytest.approx(1.0, abs=tolerance)
    assert ns.temperature_ratio(mach, gas) == pytest.approx(1.0, abs=tolerance)
    assert ns.stagnation_pressure_ratio(mach, gas) == pytest.approx(1.0, abs=tolerance)
    # Entropy production goes as (M1-1)^3, so it vanishes far faster.
    assert ns.entropy_change(mach, gas) == pytest.approx(0.0, abs=tolerance)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_sonic_input_is_the_degenerate_zero_strength_shock(gas):
    """M1 = 1 is a limit, not a shock: every ratio is exactly 1."""
    result = ns.solve(1.0, gas)
    assert result.mach2 == pytest.approx(1.0, rel=1e-14)
    assert result.pressure_ratio == pytest.approx(1.0, rel=1e-14)
    assert result.density_ratio == pytest.approx(1.0, rel=1e-14)
    assert result.temperature_ratio == pytest.approx(1.0, rel=1e-14)
    assert result.stagnation_pressure_ratio == pytest.approx(1.0, rel=1e-14)
    assert result.entropy_change == pytest.approx(0.0, abs=1e-14)
    assert result.sonic_limit is True


def test_sonic_pitot_ratio_is_the_isentropic_stagnation_ratio():
    """With no shock, p02/p1 is just p0/p at Mach 1."""
    assert ns.stagnation_pressure_over_upstream_static(1.0, AIR) == pytest.approx(
        1.0 / float(iso.pressure_ratio(1.0, AIR)), rel=1e-14
    )


# ---------------------------------------------------------------------------
# domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relation", [
    ns.mach_downstream, ns.pressure_ratio, ns.density_ratio, ns.temperature_ratio,
    ns.stagnation_pressure_ratio, ns.entropy_change, ns.area_star_ratio,
    ns.stagnation_pressure_over_upstream_static,
])
@pytest.mark.parametrize("bad", [0.999999, 0.5, 0.0, -2.0])
def test_subsonic_upstream_is_refused(relation, bad):
    """Algebraically defined, thermodynamically forbidden, so refused."""
    with pytest.raises(SubsonicShockError):
        relation(bad, AIR)


def test_subsonic_shock_error_is_a_domain_error():
    assert issubclass(SubsonicShockError, DomainError)


def test_refusal_explains_why():
    with pytest.raises(SubsonicShockError) as excinfo:
        ns.pressure_ratio(0.5, AIR)
    assert "supersonic" in str(excinfo.value)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_upstream_mach_rejected(bad):
    with pytest.raises(DomainError):
        ns.pressure_ratio(bad, AIR)


def test_array_with_one_subsonic_element_raises():
    with pytest.raises(SubsonicShockError):
        ns.pressure_ratio(np.array([2.0, 3.0, 0.5]), AIR)


def test_solve_rejects_an_array():
    with pytest.raises(SubsonicShockError):
        ns.solve(np.array([2.0, 3.0]), AIR)


# ---------------------------------------------------------------------------
# inverse
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_upstream_mach_from_pressure_ratio_round_trips(gas):
    """Closed form, so it must invert the forward relation exactly."""
    for mach in (1.0, 1.5, 2.0, 5.0, 12.0):
        ratio = float(ns.pressure_ratio(mach, gas))
        assert ns.mach_upstream_from_pressure_ratio(ratio, gas) == pytest.approx(mach, rel=1e-12)


def test_pressure_inverse_uses_no_root_solver(monkeypatch):
    """The shock relations are algebraic; nothing here may iterate."""
    from rocketforge.core.numerics import roots

    def forbidden(*args, **kwargs):  # pragma: no cover - only on failure
        raise AssertionError("normal shock must not call the root solver")

    monkeypatch.setattr(roots, "brent", forbidden)
    assert ns.mach_upstream_from_pressure_ratio(4.5, AIR) == pytest.approx(2.0, rel=1e-12)
    assert ns.solve(3.0, AIR).mach2 > 0.0


@pytest.mark.parametrize("bad", [0.5, 0.0, -1.0])
def test_pressure_inverse_rejects_a_ratio_below_one(bad):
    with pytest.raises(DomainError):
        ns.mach_upstream_from_pressure_ratio(bad, AIR)


# ---------------------------------------------------------------------------
# grouped result and array policy
# ---------------------------------------------------------------------------


def test_result_is_immutable_and_complete():
    result = ns.solve(2.0, AIR)
    with pytest.raises(Exception):
        result.mach1 = 3.0  # type: ignore[misc]
    for field in ("mach1", "mach2", "pressure_ratio", "density_ratio", "temperature_ratio",
                  "stagnation_pressure_ratio", "stagnation_pressure_over_upstream_static",
                  "stagnation_temperature_ratio", "entropy_change", "area_star_ratio"):
        assert math.isfinite(getattr(result, field))


def test_result_agrees_with_the_individual_relations():
    gas = PerfectGas(gamma=1.3)
    result = ns.solve(2.5, gas)
    assert result.mach2 == pytest.approx(float(ns.mach_downstream(2.5, gas)), rel=1e-15)
    assert result.pressure_ratio == pytest.approx(float(ns.pressure_ratio(2.5, gas)), rel=1e-15)
    assert result.entropy_change == pytest.approx(float(ns.entropy_change(2.5, gas)), rel=1e-15)


def test_scalar_returns_float_and_array_returns_array():
    assert isinstance(ns.pressure_ratio(2.0, AIR), float)
    result = ns.pressure_ratio(np.array([1.5, 2.0, 3.0]), AIR)
    assert isinstance(result, np.ndarray) and result.dtype == np.float64


def test_array_and_scalar_paths_agree():
    grid = np.array([1.0, 1.5, 2.0, 5.0])
    vector = ns.stagnation_pressure_ratio(grid, AIR)
    for index, mach in enumerate(grid):
        assert vector[index] == pytest.approx(
            float(ns.stagnation_pressure_ratio(float(mach), AIR)), rel=1e-15
        )


def test_relations_require_an_explicit_gas():
    with pytest.raises(TypeError):
        ns.pressure_ratio(2.0)  # type: ignore[call-arg]
