"""Properties that must hold for every gas, every geometry and every regime.

The individual regime files check named cases. This file sweeps: four gammas,
several area ratios and a dense back-pressure grid, asserting the invariants
that make a nozzle solution a nozzle solution rather than a plausible set of
numbers.
"""

from __future__ import annotations

import numpy as np
import pytest

from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import mass_flow as mf
from rocketforge.physics.compressible import nozzle
from rocketforge.physics.compressible.geometry import AreaDistribution
from rocketforge.physics.compressible.types import NozzleOperating, NozzleRegime

GAMMAS = (1.2, 1.3, 1.4, 1.66)
AREA_RATIOS = (1.5, 2.0, 4.0, 10.0)
P0, T0 = 2.0e6, 2800.0


def gas(gamma: float) -> PerfectGas:
    return PerfectGas(gamma=gamma, gas_constant=320.0)


def geometry(area_ratio: float, n: int = 61) -> AreaDistribution:
    return AreaDistribution.conical(throat_area=0.005, area_ratio=area_ratio, n=n)


def back_pressure_grid(gamma: float, area_ratio: float, n: int = 24):
    """A grid that visits every regime, built from the criticals themselves."""
    critical = nozzle.critical_pressure_ratios(area_ratio, gas(gamma)).unwrap()
    return np.concatenate([
        np.linspace(0.999, critical.first_critical, 5),
        np.linspace(critical.first_critical, critical.second_critical, n // 2)[1:-1],
        [critical.second_critical],
        np.linspace(critical.second_critical, critical.third_critical, 6)[1:-1],
        [critical.third_critical],
        np.linspace(critical.third_critical, 1e-3, 4)[1:],
    ])


def solutions(gamma: float, area_ratio: float):
    duct = geometry(area_ratio)
    air = gas(gamma)
    for back in back_pressure_grid(gamma, area_ratio):
        yield float(back), nozzle.solve(
            duct, NozzleOperating(P0, float(back) * P0, T0), air).unwrap()


# ---------------------------------------------------------------------------
# conservation, everywhere
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_mass_is_conserved_in_every_regime(gamma, area_ratio):
    for back, solution in solutions(gamma, area_ratio):
        local = solution.density * solution.area * solution.velocity
        assert np.allclose(local, solution.mass_flow, rtol=1e-7), (back, solution.regime)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_stagnation_temperature_is_conserved_in_every_regime(gamma, area_ratio):
    air = gas(gamma)
    for back, solution in solutions(gamma, area_ratio):
        local = solution.temperature + solution.velocity ** 2 / (2.0 * air.cp)
        assert np.allclose(local, T0, rtol=1e-10), (back, solution.regime)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_stagnation_pressure_only_ever_falls_at_a_shock(gamma, area_ratio):
    for back, solution in solutions(gamma, area_ratio):
        levels = np.unique(np.round(solution.stagnation_pressure, 6))
        expected = 2 if solution.shock is not None else 1
        assert levels.size == expected, (back, solution.regime, levels)
        assert np.all(np.diff(solution.stagnation_pressure) <= 1e-9)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_every_choked_regime_passes_the_critical_mass_flow(gamma, area_ratio):
    air = gas(gamma)
    duct = geometry(area_ratio)
    expected = mf.choked_mass_flow(air, duct.throat_area, P0, T0)
    for back, solution in solutions(gamma, area_ratio):
        if solution.choked:
            assert solution.mass_flow == expected, (back, solution.regime)
        else:
            assert solution.mass_flow < expected


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_pressure_and_temperature_stay_physical(gamma, area_ratio):
    for back, solution in solutions(gamma, area_ratio):
        assert np.all(solution.pressure > 0.0)
        assert np.all(solution.temperature > 0.0)
        assert np.all(solution.density > 0.0)
        assert np.all(np.isfinite(solution.mach))
        assert np.all(solution.pressure <= P0 * (1.0 + 1e-12))
        assert np.all(solution.temperature <= T0 * (1.0 + 1e-12))


# ---------------------------------------------------------------------------
# continuity across the regime boundaries
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_solution_is_continuous_through_choking_onset(gamma):
    """Approached from both sides, the throat Mach and mass flow agree."""
    air = gas(gamma)
    duct = geometry(2.0)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    below = nozzle.solve(duct, NozzleOperating(
        P0, (critical.first_critical - 1e-7) * P0, T0), air).unwrap()
    above = nozzle.solve(duct, NozzleOperating(
        P0, (critical.first_critical + 1e-7) * P0, T0), air).unwrap()
    assert above.regime is NozzleRegime.UNCHOKED_SUBSONIC
    assert below.regime is NozzleRegime.INTERNAL_NORMAL_SHOCK
    assert above.throat.mach == pytest.approx(1.0, abs=2e-3)
    assert below.throat.mach == 1.0
    assert above.mass_flow == pytest.approx(below.mass_flow, rel=1e-5)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_solution_is_continuous_through_shock_at_exit(gamma):
    """The shock leaves the nozzle rather than disappearing discontinuously."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    # Just outside the boundary window, which is relative: pressure_tol times
    # the threshold. Inside it the answer is SHOCK_AT_EXIT, and correctly so.
    inside = nozzle.classify(2.0, critical.second_critical * (1 + 1e-7), air).unwrap()
    outside = nozzle.classify(2.0, critical.second_critical * (1 - 1e-7), air).unwrap()
    assert inside.regime is NozzleRegime.INTERNAL_NORMAL_SHOCK
    assert outside.regime is NozzleRegime.OVEREXPANDED
    assert inside.shock.area_ratio_shock == pytest.approx(2.0, rel=1e-4)
    assert outside.shock is None
    # The internal flow either side is the same right up to the exit plane.
    assert inside.shock.mach_upstream == pytest.approx(
        critical.mach_exit_supersonic, rel=1e-4)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_exit_state_is_continuous_through_ideal_expansion(gamma):
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    for offset in (-1e-6, 0.0, 1e-6):
        result = nozzle.classify(2.0, critical.third_critical + offset, air).unwrap()
        assert result.mach_exit == critical.mach_exit_supersonic
        assert result.pressure_ratio_exit == critical.third_critical


# ---------------------------------------------------------------------------
# monotone trends
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("area_ratio", AREA_RATIOS)
def test_the_shock_marches_downstream_as_the_back_pressure_falls(gamma, area_ratio):
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
    backs = np.linspace(critical.first_critical * 0.999,
                        critical.second_critical * 1.001, 30)
    positions = [nozzle.shock_area_ratio(area_ratio, float(b), air).unwrap()
                 .area_ratio_shock for b in backs]
    assert np.all(np.diff(positions) > 0.0)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_shock_position_in_x_moves_with_it(gamma):
    air = gas(gamma)
    duct = geometry(2.0, n=201)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    backs = np.linspace(critical.first_critical * 0.999,
                        critical.second_critical * 1.001, 15)
    positions = [nozzle.solve(duct, NozzleOperating(P0, float(b) * P0, T0), air)
                 .unwrap().shock.x for b in backs]
    assert np.all(np.diff(positions) > 0.0)
    assert positions[0] > duct.throat_x
    assert positions[-1] <= duct.x[-1] + 1e-12


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_exit_mach_rises_as_the_back_pressure_falls(gamma):
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    backs = np.concatenate([
        np.linspace(0.999, critical.first_critical, 6),
        np.linspace(critical.first_critical, critical.second_critical, 10)[1:],
    ])
    machs = [nozzle.classify(2.0, float(b), air).unwrap().mach_exit for b in backs]
    assert np.all(np.diff(machs) > 0.0)


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------


def test_solving_twice_gives_identical_arrays():
    """``172``: no flakiness, no unseeded anything."""
    air = gas(1.4)
    duct = geometry(2.0)
    operating = NozzleOperating(P0, 0.7 * P0, T0)
    first = nozzle.solve(duct, operating, air).unwrap()
    second = nozzle.solve(duct, operating, air).unwrap()
    assert np.array_equal(first.mach, second.mach)
    assert np.array_equal(first.pressure, second.pressure)
    assert first.shock.area_ratio_shock == second.shock.area_ratio_shock


def test_the_dimensionless_and_distributed_paths_agree():
    """classify() and solve() must never disagree about the same nozzle."""
    air = gas(1.4)
    duct = geometry(2.0)
    for back in back_pressure_grid(1.4, 2.0):
        cheap = nozzle.classify(2.0, float(back), air).unwrap()
        full = nozzle.solve(duct, NozzleOperating(P0, float(back) * P0, T0),
                            air).unwrap()
        assert cheap.regime is full.regime
        assert cheap.mach_exit == pytest.approx(full.exit.mach, rel=1e-9)
        if cheap.shock is not None:
            # Not bit-identical: solve() recovers pb/p0 as (pb*p0)/p0, which can
            # differ from the literal ratio by an ulp, and the root moves with it.
            assert cheap.shock.area_ratio_shock == pytest.approx(
                full.shock.area_ratio_shock, rel=1e-12)


@pytest.mark.parametrize("area_ratio", [1.05, 1.5, 3.0, 8.0, 25.0, 100.0])
def test_a_wide_range_of_nozzles_is_solvable(area_ratio):
    """``165``: high area ratios stay finite and consistent."""
    air = gas(1.4)
    critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
    middle = 0.5 * (critical.first_critical + critical.second_critical)
    result = nozzle.classify(area_ratio, middle, air).unwrap()
    assert 1.0 < result.shock.area_ratio_shock < area_ratio
    assert np.isfinite(result.mach_exit)
    assert 0.0 < result.pressure_ratio_exit < 1.0
