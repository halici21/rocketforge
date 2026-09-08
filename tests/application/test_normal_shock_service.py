"""The normal-shock service: the adapter, not the physics.

Mode dispatch, the optional dimensional state, error handling that returns a
message instead of raising, and table assembly. Values are checked against the
physics layer rather than against numbers typed into this file, except where a
published value is quoted deliberately and labelled as such.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.application.analysis import normal_shock_service as svc
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import normal_shock as ns

AIR = PerfectGas(gamma=1.4)


# ---------------------------------------------------------------------------
# modes
# ---------------------------------------------------------------------------


def test_every_mode_has_a_descriptor_and_a_workable_default():
    assert len(svc.SOLVE_MODES) == len(svc.SolveMode)
    for info in svc.SOLVE_MODES:
        assert svc.mode_info(info.mode) is info
        assert info.label and info.symbol and info.hint
        result = svc.solve(info.mode, info.default_value, 1.4)
        assert result.ok, (info.mode, result.message)


def test_every_mode_describes_the_same_shock():
    """Five ways in, one flow out. This is the service-level statement of the
    physics-level test that the inverses agree."""
    shock = ns.solve(2.0, AIR)
    inputs = {
        svc.SolveMode.MACH_UPSTREAM: 2.0,
        svc.SolveMode.PRESSURE_RATIO: shock.pressure_ratio,
        svc.SolveMode.DENSITY_RATIO: shock.density_ratio,
        svc.SolveMode.MACH_DOWNSTREAM: shock.mach2,
        svc.SolveMode.STAGNATION_PRESSURE_RATIO: shock.stagnation_pressure_ratio,
    }
    for mode, value in inputs.items():
        result = svc.solve(mode, value, 1.4)
        assert result.ok, mode
        assert result.mach == pytest.approx(2.0, rel=1e-8), mode
        assert result.value_of("mach2") == pytest.approx(shock.mach2, rel=1e-8), mode


def test_only_the_stagnation_pressure_mode_is_marked_iterative():
    iterative = [i.mode for i in svc.SOLVE_MODES if i.iterative]
    assert iterative == [svc.SolveMode.STAGNATION_PRESSURE_RATIO]


def test_readouts_come_from_the_physics_result():
    result = svc.solve(svc.SolveMode.MACH_UPSTREAM, 3.0, 1.4)
    shock = ns.solve(3.0, AIR)
    for key, expected in (
        ("mach2", shock.mach2),
        ("p2_over_p1", shock.pressure_ratio),
        ("rho2_over_rho1", shock.density_ratio),
        ("T2_over_T1", shock.temperature_ratio),
        ("p02_over_p01", shock.stagnation_pressure_ratio),
        ("p02_over_p1", shock.stagnation_pressure_over_upstream_static),
        ("area_star_ratio", shock.area_star_ratio),
        ("entropy_change", shock.entropy_change),
    ):
        assert result.value_of(key) == pytest.approx(expected, rel=1e-15), key


def test_stagnation_temperature_is_reported_as_exactly_unchanged():
    assert svc.solve(svc.SolveMode.MACH_UPSTREAM, 4.0, 1.4).value_of("T02_over_T01") == 1.0


# ---------------------------------------------------------------------------
# the optional dimensional state
# ---------------------------------------------------------------------------


def test_upstream_conditions_turn_ratios_into_pressures_and_temperatures():
    upstream = svc.UpstreamState(pressure=50_000.0, temperature=250.0)
    result = svc.solve(svc.SolveMode.MACH_UPSTREAM, 2.0, 1.4, upstream)
    shock = ns.solve(2.0, AIR)
    assert result.value_of("p2") == pytest.approx(50_000.0 * shock.pressure_ratio, rel=1e-15)
    assert result.value_of("T2") == pytest.approx(250.0 * shock.temperature_ratio, rel=1e-15)
    assert result.value_of("p01") == pytest.approx(
        50_000.0 / float(iso.pressure_ratio(2.0, AIR)), rel=1e-15)
    assert result.value_of("p02") == pytest.approx(
        result.value_of("p01") * shock.stagnation_pressure_ratio, rel=1e-15)


def test_the_stagnation_temperature_is_the_same_on_both_sides():
    """T0 is one number, not two, because the shock is adiabatic."""
    upstream = svc.UpstreamState(pressure=101325.0, temperature=300.0)
    result = svc.solve(svc.SolveMode.MACH_UPSTREAM, 2.5, 1.4, upstream)
    assert result.value_of("T0") == pytest.approx(
        300.0 / float(iso.temperature_ratio(2.5, AIR)), rel=1e-15)


@pytest.mark.parametrize("field", ["pressure", "temperature"])
def test_an_incomplete_upstream_state_leaves_those_rows_empty(field):
    upstream = svc.UpstreamState(**{field: 0.0})
    assert not upstream.complete
    result = svc.solve(svc.SolveMode.MACH_UPSTREAM, 2.0, 1.4, upstream)
    assert result.ok, "the ratios are complete without a dimensional state"
    for key in ("p2", "T2", "p01", "p02", "T0"):
        assert result.value_of(key) is None
    assert result.value_of("p2_over_p1") == pytest.approx(4.5)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


def test_the_sonic_limit_is_named_and_explained():
    result = svc.solve(svc.SolveMode.MACH_UPSTREAM, 1.0, 1.4)
    assert result.status == "Sonic limit"
    assert "vanishing shock" in result.message


def test_a_strong_shock_warns_about_the_gas_model_not_the_arithmetic():
    result = svc.solve(svc.SolveMode.MACH_UPSTREAM, 15.0, 1.4)
    assert result.status == "Strong shock"
    assert "perfect-gas" in result.message
    assert result.ok, "the warning is about applicability; the numbers are still produced"


def test_an_ordinary_shock_is_simply_valid():
    result = svc.solve(svc.SolveMode.MACH_UPSTREAM, 2.0, 1.4)
    assert result.status == "Valid"
    assert result.message == ""


# ---------------------------------------------------------------------------
# invalid input returns a message, never an exception
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode,value,fragment", [
    (svc.SolveMode.MACH_UPSTREAM, 0.5, "supersonic"),
    (svc.SolveMode.MACH_UPSTREAM, -1.0, "supersonic"),
    (svc.SolveMode.MACH_UPSTREAM, math.nan, "finite"),
    (svc.SolveMode.PRESSURE_RATIO, 0.5, "compresses"),
    (svc.SolveMode.DENSITY_RATIO, 0.5, "compresses"),
    (svc.SolveMode.DENSITY_RATIO, 6.0, "strong-shock limit"),
    (svc.SolveMode.DENSITY_RATIO, 7.0, "strong-shock limit"),
    (svc.SolveMode.MACH_DOWNSTREAM, 1.5, "subsonic"),
    (svc.SolveMode.MACH_DOWNSTREAM, 0.2, "strong-shock limit"),
    (svc.SolveMode.STAGNATION_PRESSURE_RATIO, 1.5, "never creates it"),
    (svc.SolveMode.STAGNATION_PRESSURE_RATIO, 0.0, "> 0"),
])
def test_an_impossible_input_is_reported_with_the_reason(mode, value, fragment):
    result = svc.solve(mode, value, 1.4)
    assert not result.ok
    assert result.rows == ()
    assert fragment in result.message, result.message


@pytest.mark.parametrize("gamma", [0.9, 1.0, 3.5, math.nan])
def test_an_impossible_gamma_is_reported_not_raised(gamma):
    result = svc.solve(svc.SolveMode.MACH_UPSTREAM, 2.0, gamma)
    assert not result.ok and result.message


def test_the_density_limit_moves_with_gamma():
    """rho2/rho1 = 6.5 is impossible for air and ordinary for gamma = 1.2."""
    assert not svc.solve(svc.SolveMode.DENSITY_RATIO, 6.5, 1.4).ok
    assert svc.solve(svc.SolveMode.DENSITY_RATIO, 6.5, 1.2).ok


def test_limits_are_reported_for_the_caption():
    density, mach = svc.limits_for(1.4)
    assert density == pytest.approx(6.0)
    assert mach == pytest.approx(0.37796, abs=1e-5)
    assert svc.limits_for(1.2)[0] == pytest.approx(11.0)


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------


def test_the_anderson_convention_prints_the_appendix_columns_in_order():
    table = svc.generate_table(1.4, 1.0, 5.0, 0.1)
    assert [c.key for c in table.columns] == [
        "mach1", "p2_over_p1", "rho2_over_rho1", "T2_over_T1",
        "p02_over_p01", "p02_over_p1", "mach2",
    ]


def test_every_table_value_matches_the_physics():
    table = svc.generate_table(1.3, 1.0, 6.0, 0.25)
    gas = PerfectGas(gamma=1.3)
    keys = [c.key for c in table.columns]
    for index, mach1 in enumerate(table.values[:, 0]):
        shock = ns.solve(mach1, gas)
        assert table.values[index, keys.index("p2_over_p1")] == pytest.approx(
            shock.pressure_ratio, rel=1e-14)
        assert table.values[index, keys.index("mach2")] == pytest.approx(
            shock.mach2, rel=1e-14)
        assert table.values[index, keys.index("p02_over_p1")] == pytest.approx(
            shock.stagnation_pressure_over_upstream_static, rel=1e-14)


def test_the_extended_convention_adds_what_the_appendix_omits():
    table = svc.generate_table(1.4, 1.0, 4.0, 0.5, svc.TableConvention.EXTENDED)
    keys = [c.key for c in table.columns]
    assert "entropy_change" in keys and "area_star_ratio" in keys
    for index, mach1 in enumerate(table.values[:, 0]):
        assert table.values[index, keys.index("entropy_change")] == pytest.approx(
            float(ns.entropy_change(mach1, AIR)), rel=1e-14)


def test_a_table_cannot_start_below_mach_one():
    with pytest.raises(ValueError, match="supersonic"):
        svc.generate_table(1.4, 0.5, 3.0, 0.1)


@pytest.mark.parametrize("start,end,step,fragment", [
    (1.0, 5.0, 0.0, "Step"),
    (1.0, 5.0, -0.5, "Step"),
    (3.0, 2.0, 0.1, "greater than start"),
    (1.0, 5.0, 1e-9, "row limit"),
])
def test_an_impossible_range_is_refused_with_a_reason(start, end, step, fragment):
    with pytest.raises(ValueError, match=fragment):
        svc.generate_table(1.4, start, end, step)


def test_table_metadata_records_how_it_was_made():
    table = svc.generate_table(1.4, 1.0, 5.0, 0.1)
    assert table.metadata["model"] == "perfect_gas_normal_shock_v1"
    assert table.metadata["rows"] == table.row_count
    assert table.metadata["density_ratio_limit"] == pytest.approx(6.0)
    assert table.sonic_row == 0


def test_a_table_starting_above_sonic_has_no_sonic_row():
    assert svc.generate_table(1.4, 1.5, 5.0, 0.1).sonic_row is None


def test_table_columns_stay_physically_ordered():
    """A quick invariant sweep over a generated table, not a sampled row."""
    table = svc.generate_table(1.4, 1.0, 20.0, 0.05)
    keys = [c.key for c in table.columns]
    assert np.all(table.values[:, keys.index("mach2")] <= 1.0)
    assert np.all(table.values[:, keys.index("p02_over_p01")] <= 1.0)
    assert np.all(np.diff(table.values[:, keys.index("p2_over_p1")]) > 0.0)
    assert np.all(table.values[:, keys.index("rho2_over_rho1")] < 6.0)
