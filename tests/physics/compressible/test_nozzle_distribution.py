"""The distributed solution: stations, branches, discontinuity and conservation.

``03`` sections 10.7, 10.8 and 10.10. The arrays are the caller's own grid --
no resampling, no smoothing -- plus one duplicated station when a shock exists.
Everything a reviewer would want to check about a nozzle solution is checkable
on those arrays, which is the point of returning them.
"""

from __future__ import annotations

import numpy as np
import pytest

from rocketforge.core.errors import GeometryError, InputError
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import mass_flow as mf
from rocketforge.physics.compressible import nozzle
from rocketforge.physics.compressible.geometry import AreaDistribution
from rocketforge.physics.compressible.types import NozzleOperating, NozzleRegime

P0 = 1.0e6
T0 = 3000.0
AREA_RATIO = 2.0


def gas(gamma: float = 1.4) -> PerfectGas:
    return PerfectGas(gamma=gamma, gas_constant=287.05)


def geometry(n: int = 101, area_ratio: float = AREA_RATIO) -> AreaDistribution:
    return AreaDistribution.conical(throat_area=0.01, area_ratio=area_ratio, n=n)


def solve_at(back_ratio: float, n: int = 101, gamma: float = 1.4,
             temperature: float | None = T0):
    return nozzle.solve(geometry(n), NozzleOperating(P0, back_ratio * P0, temperature),
                        gas(gamma)).unwrap()


def criticals(gamma: float = 1.4, area_ratio: float = AREA_RATIO):
    return nozzle.critical_pressure_ratios(area_ratio, gas(gamma)).unwrap()


BACKS = {
    "unchoked": 0.99,
    "choking_onset": None,     # filled below
    "internal_shock": None,
    "shock_at_exit": None,
    "overexpanded": None,
    "ideal": None,
    "underexpanded": None,
}
_c = criticals()
BACKS["choking_onset"] = _c.first_critical
BACKS["internal_shock"] = 0.5 * (_c.first_critical + _c.second_critical)
BACKS["shock_at_exit"] = _c.second_critical
BACKS["overexpanded"] = 0.5 * (_c.second_critical + _c.third_critical)
BACKS["ideal"] = _c.third_critical
BACKS["underexpanded"] = 0.5 * _c.third_critical
ALL_BACKS = tuple(BACKS.values())


# ---------------------------------------------------------------------------
# the grid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("back", ALL_BACKS)
def test_every_array_has_the_same_length(back):
    solution = solve_at(back)
    lengths = {len(solution.x), len(solution.area), len(solution.mach),
               len(solution.pressure), len(solution.temperature),
               len(solution.density), len(solution.velocity),
               len(solution.speed_of_sound), len(solution.stagnation_pressure),
               len(solution.stagnation_temperature), len(solution.area_ratio),
               len(solution.pressure_ratio), len(solution.stagnation_pressure_ratio)}
    assert len(lengths) == 1


@pytest.mark.parametrize("back", ALL_BACKS)
def test_the_supplied_grid_is_returned_unchanged_apart_from_the_shock(back):
    """No resampling: the caller chose the resolution and gets it back."""
    grid = geometry(101)
    solution = solve_at(back)
    extra = solution.x.size - grid.x.size
    assert extra in (0, 1, 2)
    assert np.all(np.isin(np.round(grid.x, 12), np.round(solution.x, 12)))


@pytest.mark.parametrize("back", ALL_BACKS)
def test_the_throat_is_an_explicit_station(back):
    solution = solve_at(back)
    assert solution.area[solution.throat_index] == pytest.approx(
        geometry().throat_area, rel=1e-12)
    assert solution.throat.mach == solution.mach[solution.throat_index]


@pytest.mark.parametrize("back", ALL_BACKS)
def test_the_exit_is_an_explicit_station(back):
    solution = solve_at(back)
    assert solution.area[-1] == pytest.approx(geometry().exit_area, rel=1e-12)
    assert solution.exit.mach == solution.mach[-1]


@pytest.mark.parametrize("resolution", [11, 51, 201, 1001])
def test_the_solution_survives_any_reasonable_resolution(resolution):
    solution = solve_at(BACKS["internal_shock"], n=resolution)
    assert solution.regime is NozzleRegime.INTERNAL_NORMAL_SHOCK
    assert solution.shock_index is not None
    assert solution.x.size >= resolution


def test_the_regime_does_not_depend_on_the_resolution():
    """Classification is a threshold decision, not a sampling artefact."""
    regimes = {solve_at(BACKS["internal_shock"], n=n).regime for n in (11, 51, 501)}
    assert len(regimes) == 1


# ---------------------------------------------------------------------------
# branch assignment
# ---------------------------------------------------------------------------


def test_the_unchoked_nozzle_is_subsonic_everywhere():
    solution = solve_at(0.99)
    assert solution.regime is NozzleRegime.UNCHOKED_SUBSONIC
    assert np.all(solution.mach < 1.0)
    assert solution.throat.mach < 1.0
    assert not solution.choked


def test_the_choked_subsonic_exit_is_sonic_only_at_the_throat():
    solution = solve_at(BACKS["choking_onset"])
    assert solution.mach[solution.throat_index] == 1.0
    assert np.all(solution.mach[:solution.throat_index] < 1.0)
    assert np.all(solution.mach[solution.throat_index + 1:] < 1.0)


def test_the_shock_free_supersonic_nozzle_crosses_the_sonic_point_once():
    solution = solve_at(BACKS["ideal"])
    assert solution.mach[solution.throat_index] == 1.0
    assert np.all(solution.mach[:solution.throat_index] < 1.0)
    assert np.all(solution.mach[solution.throat_index + 1:] > 1.0)


def test_the_internal_shock_topology_is_subsonic_sonic_supersonic_subsonic():
    """``69``: the branch sequence is explicit, and this is where it is asserted."""
    solution = solve_at(BACKS["internal_shock"])
    throat, index = solution.throat_index, solution.shock_index
    assert np.all(solution.mach[:throat] < 1.0)
    assert solution.mach[throat] == 1.0
    assert np.all(solution.mach[throat + 1:index + 1] > 1.0)
    assert np.all(solution.mach[index + 1:] < 1.0)


@pytest.mark.parametrize("back", ALL_BACKS)
def test_every_station_reproduces_its_own_area_relation(back):
    """Each Mach number must be the area relation's root for its own sonic area."""
    air = gas()
    solution = solve_at(back)
    if solution.choked:
        sonic_area = geometry().throat_area
    else:
        sonic_area = geometry().exit_area / iso.area_ratio(solution.exit.mach, air)

    for i, (area, mach) in enumerate(zip(solution.area, solution.mach)):
        if solution.shock_index is not None and i > solution.shock_index:
            # Downstream of a shock the sonic area is the *new* one, and
            # comparing to the throat here would be the classic error.
            local = sonic_area * solution.shock.area_star_downstream_ratio
        else:
            local = sonic_area
        assert iso.area_ratio(mach, air) == pytest.approx(area / local, rel=1e-8)


# ---------------------------------------------------------------------------
# the shock discontinuity
# ---------------------------------------------------------------------------


def test_the_shock_station_appears_twice_at_the_same_position():
    solution = solve_at(BACKS["internal_shock"])
    index = solution.shock_index
    assert solution.x[index] == solution.x[index + 1]
    assert solution.area[index] == solution.area[index + 1]


def test_the_two_shock_rows_carry_the_two_different_states():
    solution = solve_at(BACKS["internal_shock"])
    index = solution.shock_index
    assert solution.mach[index] == solution.shock.mach_upstream
    assert solution.mach[index + 1] == solution.shock.mach_downstream
    assert solution.mach[index] > 1.0 > solution.mach[index + 1]


def test_the_jump_is_not_smoothed():
    """Pressure and temperature step up; the model's only irreversibility."""
    solution = solve_at(BACKS["internal_shock"])
    index = solution.shock_index
    assert solution.pressure[index + 1] > solution.pressure[index]
    assert solution.temperature[index + 1] > solution.temperature[index]
    assert solution.pressure[index + 1] / solution.pressure[index] == pytest.approx(
        solution.shock.pressure_ratio, rel=1e-9)


def test_the_shock_position_is_where_the_geometry_puts_that_area():
    solution = solve_at(BACKS["internal_shock"])
    grid = geometry()
    expected_area = solution.shock.area_ratio_shock * grid.throat_area
    assert solution.shock.x == pytest.approx(
        grid.x_at_area(expected_area, side="diverging"), rel=1e-12)
    assert solution.shock.x > grid.throat_x


@pytest.mark.parametrize("back_key", ["unchoked", "choking_onset", "overexpanded",
                                      "ideal", "underexpanded"])
def test_the_shock_free_regimes_carry_no_shock_at_all(back_key):
    solution = solve_at(BACKS[back_key])
    assert solution.shock is None
    assert solution.shock_index is None


def test_a_shock_at_the_exit_needs_no_inserted_station():
    solution = solve_at(BACKS["shock_at_exit"])
    assert solution.shock_index == solution.x.size - 2
    assert solution.x[-1] == solution.x[-2]
    assert solution.mach[-2] == pytest.approx(criticals().mach_exit_supersonic)


# ---------------------------------------------------------------------------
# conservation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("back", ALL_BACKS)
def test_mass_is_conserved_at_every_station(back):
    solution = solve_at(back)
    local = solution.density * solution.area * solution.velocity
    assert np.allclose(local, solution.mass_flow, rtol=1e-8)


@pytest.mark.parametrize("back", ALL_BACKS)
def test_stagnation_temperature_is_constant_everywhere(back):
    """Adiabatic, so T0 does not change -- across the shock included."""
    air = gas()
    solution = solve_at(back)
    local = solution.temperature + solution.velocity ** 2 / (2.0 * air.cp)
    assert np.allclose(local, T0, rtol=1e-12)
    assert np.all(solution.stagnation_temperature == T0)


@pytest.mark.parametrize("back_key", ["unchoked", "choking_onset", "overexpanded",
                                      "ideal", "underexpanded"])
def test_stagnation_pressure_is_constant_without_a_shock(back_key):
    solution = solve_at(BACKS[back_key])
    assert np.allclose(solution.stagnation_pressure, P0, rtol=1e-12)


def test_stagnation_pressure_falls_once_and_only_at_the_shock():
    """No gradual loss: this model is isentropic apart from one discontinuity."""
    solution = solve_at(BACKS["internal_shock"])
    index = solution.shock_index
    upstream = solution.stagnation_pressure[:index + 1]
    downstream = solution.stagnation_pressure[index + 1:]
    assert np.allclose(upstream, P0, rtol=1e-12)
    assert np.allclose(downstream, P0 * solution.shock.stagnation_pressure_ratio,
                       rtol=1e-12)
    assert downstream[0] < upstream[-1]


@pytest.mark.parametrize("back", ALL_BACKS)
def test_the_local_stagnation_pressure_matches_the_local_state(back):
    """p0(x) is not an annotation; it is the state's own stagnation pressure."""
    air = gas()
    solution = solve_at(back)
    recomputed = solution.pressure / np.asarray(iso.pressure_ratio(solution.mach, air))
    assert np.allclose(recomputed, solution.stagnation_pressure, rtol=1e-8)


# ---------------------------------------------------------------------------
# mass flow
# ---------------------------------------------------------------------------


def test_the_choked_mass_flow_is_the_mass_flow_module_at_the_throat():
    air = gas()
    solution = solve_at(BACKS["ideal"])
    assert solution.mass_flow == mf.choked_mass_flow(
        air, geometry().throat_area, P0, T0)


def test_the_unchoked_mass_flow_comes_from_the_actual_throat_mach():
    air = gas()
    solution = solve_at(0.99)
    assert solution.mass_flow == pytest.approx(
        float(mf.mass_flow(solution.throat.mach, air, geometry().throat_area, P0, T0)),
        rel=1e-12)
    assert solution.mass_flow < mf.choked_mass_flow(air, geometry().throat_area, P0, T0)


def test_every_choked_regime_passes_exactly_the_same_mass():
    """Back pressure stops mattering the moment the throat goes sonic."""
    flows = {solve_at(BACKS[key]).mass_flow for key in
             ("choking_onset", "internal_shock", "shock_at_exit",
              "overexpanded", "ideal", "underexpanded")}
    assert len(flows) == 1


def test_the_mass_flow_climbs_to_the_choked_value_and_then_stops():
    critical = criticals()
    choked = mf.choked_mass_flow(gas(), geometry().throat_area, P0, T0)
    rising = [solve_at(b).mass_flow for b in
              (0.99, 0.98, 0.96, critical.first_critical + 1e-4)]
    assert np.all(np.diff(rising) > 0.0)
    assert rising[-1] < choked
    assert solve_at(critical.first_critical).mass_flow == choked


def test_the_mass_flow_vanishes_as_the_back_pressure_approaches_the_reservoir():
    """The zero-flow limit, approached rather than special-cased.

    Every back pressure here is above the first critical, so every one of them
    is genuinely unchoked -- 0.9 would already be an internal-shock case at
    this area ratio, and would pass the choked mass flow instead.
    """
    choked = mf.choked_mass_flow(gas(), geometry().throat_area, P0, T0)
    flows = [solve_at(b).mass_flow for b in (0.95, 0.99, 0.999, 0.9999, 0.999999)]
    assert np.all(np.diff(flows) < 0.0)
    assert flows[-1] < 0.005 * choked
    # Each decade closer to the reservoir costs about a factor of ten in flow,
    # which is the square-root behaviour of the mass-flow parameter near rest.
    assert flows[-1] == pytest.approx(flows[-2] / 10.0, rel=0.05)


# ---------------------------------------------------------------------------
# the internal solution the last three regimes share
# ---------------------------------------------------------------------------


def test_overexpanded_ideal_and_underexpanded_share_one_internal_solution():
    """``50``, ``134``: only the label and the external context differ."""
    solutions = [solve_at(BACKS[key]) for key in
                 ("overexpanded", "ideal", "underexpanded")]
    reference = solutions[0]
    for other in solutions[1:]:
        assert np.array_equal(reference.mach, other.mach)
        assert np.array_equal(reference.pressure, other.pressure)
        assert np.array_equal(reference.temperature, other.temperature)
        assert np.array_equal(reference.density, other.density)
        assert np.array_equal(reference.velocity, other.velocity)
        assert np.array_equal(reference.stagnation_pressure, other.stagnation_pressure)
        assert reference.mass_flow == other.mass_flow
    assert len({s.regime for s in solutions}) == 3


# ---------------------------------------------------------------------------
# the unchoked sonic reference
# ---------------------------------------------------------------------------


def test_the_unchoked_sonic_area_is_virtual_and_smaller_than_the_throat():
    """``03`` section 10.10: the step implementations usually get wrong."""
    air = gas()
    solution = solve_at(0.99)
    virtual = geometry().exit_area / iso.area_ratio(solution.exit.mach, air)
    assert virtual < geometry().throat_area
    assert solution.throat.mach < 1.0


def test_the_unchoked_exit_pressure_is_the_back_pressure():
    for back in (0.99, 0.97, 0.95):
        solution = solve_at(back)
        assert solution.pressure[-1] == pytest.approx(back * P0, rel=1e-9)


def test_the_throat_mach_rises_to_one_as_choking_is_approached():
    critical = criticals()
    machs = [solve_at(b).throat.mach for b in
             (0.99, 0.97, critical.first_critical + 1e-3, critical.first_critical + 1e-6)]
    assert np.all(np.diff(machs) > 0.0)
    assert machs[-1] == pytest.approx(1.0, abs=1e-2)


def test_the_throat_mach_falls_to_zero_as_the_flow_stops():
    machs = [solve_at(b).throat.mach for b in (0.9, 0.99, 0.999, 0.99999)]
    assert np.all(np.diff(machs) < 0.0)
    assert machs[-1] < 1e-2


# ---------------------------------------------------------------------------
# refusals and the dimensionless path
# ---------------------------------------------------------------------------


def test_a_monotone_duct_is_refused_by_the_solver():
    duct = AreaDistribution(x=np.array([0.0, 1.0, 2.0]), area=np.array([3.0, 2.0, 1.0]))
    with pytest.raises(GeometryError):
        nozzle.solve(duct, NozzleOperating(P0, 0.5 * P0, T0), gas())


def test_a_back_pressure_above_the_reservoir_is_refused():
    with pytest.raises(InputError):
        nozzle.solve(geometry(), NozzleOperating(P0, 1.2 * P0, T0), gas())


def test_a_negative_pressure_is_refused():
    with pytest.raises(InputError):
        nozzle.solve(geometry(), NozzleOperating(P0, -1.0, T0), gas())


def test_without_a_reservoir_temperature_the_ratios_still_come_back():
    solution = nozzle.solve(geometry(), NozzleOperating(P0, 0.3 * P0), gas())
    record = solution.unwrap()
    assert record.temperature is None
    assert record.density is None
    assert record.velocity is None
    assert record.mass_flow is None
    assert record.mach is not None
    assert record.pressure_ratio is not None
    assert any(d.code == "DIMENSIONLESS_ONLY" for d in solution.diagnostics)


def test_a_gas_without_a_constant_gets_the_same_treatment():
    solution = nozzle.solve(geometry(), NozzleOperating(P0, 0.3 * P0, T0),
                            PerfectGas(gamma=1.4))
    assert solution.unwrap().mass_flow is None
    assert any(d.code == "DIMENSIONLESS_ONLY" for d in solution.diagnostics)
