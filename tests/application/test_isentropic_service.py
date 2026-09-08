"""Verification of the isentropic analysis adapter.

The adapter's job is to prepare, not to compute. These tests check that every
number it publishes came from the physics layer, that the reciprocal display
conventions are the right way up, and that the table is generated rather than
looked up.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.application.analysis import isentropic_service as svc
from rocketforge.physics.compressible import FlowBranch, PerfectGas
from rocketforge.physics.compressible import isentropic as iso

AIR = PerfectGas(gamma=1.4)


def value_of(result: svc.CalculatorResult, key: str) -> float:
    for row in result.rows:
        if row.key == key:
            return row.value
    raise AssertionError(f"no row {key!r} in result")


# ---------------------------------------------------------------------------
# every solve mode
# ---------------------------------------------------------------------------


def test_solve_from_mach():
    result = svc.solve(svc.SolveMode.MACH, 2.0, 1.4)
    assert result.ok
    assert result.mach == 2.0
    assert value_of(result, "p_over_p0") == pytest.approx(0.1278045255, rel=1e-9)
    assert value_of(result, "area_ratio") == pytest.approx(1.6875, rel=1e-12)


@pytest.mark.parametrize("mode,value,expected_mach", [
    (svc.SolveMode.PRESSURE_RATIO, 0.1278045255, 2.0),
    (svc.SolveMode.TEMPERATURE_RATIO, 0.5555555556, 2.0),
    (svc.SolveMode.DENSITY_RATIO, 0.2300481458, 2.0),
])
def test_solve_from_canonical_ratios(mode, value, expected_mach):
    result = svc.solve(mode, value, 1.4)
    assert result.ok
    assert result.mach == pytest.approx(expected_mach, rel=1e-7)


@pytest.mark.parametrize("mode,canonical", [
    (svc.SolveMode.PRESSURE_RATIO_INVERSE, svc.SolveMode.PRESSURE_RATIO),
    (svc.SolveMode.TEMPERATURE_RATIO_INVERSE, svc.SolveMode.TEMPERATURE_RATIO),
    (svc.SolveMode.DENSITY_RATIO_INVERSE, svc.SolveMode.DENSITY_RATIO),
])
@pytest.mark.parametrize("mach", [0.3, 0.8, 1.0, 2.0, 4.0])
def test_reciprocal_mode_is_the_inverse_of_the_canonical_mode(mode, canonical, mach):
    """Entering p0/p must give the same Mach as entering p/p0 of its reciprocal.

    This is the test that catches an orientation mistake in the adapter, which
    is the single easiest error to make in this file.
    """
    relation = {
        svc.SolveMode.PRESSURE_RATIO: iso.pressure_ratio,
        svc.SolveMode.TEMPERATURE_RATIO: iso.temperature_ratio,
        svc.SolveMode.DENSITY_RATIO: iso.density_ratio,
    }[canonical]
    ratio = float(relation(mach, AIR))

    direct = svc.solve(canonical, ratio, 1.4)
    reciprocal = svc.solve(mode, 1.0 / ratio, 1.4)

    assert direct.ok and reciprocal.ok
    assert reciprocal.mach == pytest.approx(direct.mach, rel=1e-9)
    assert reciprocal.mach == pytest.approx(mach, rel=1e-7)


def test_solve_from_area_ratio_requires_and_uses_the_branch():
    subsonic = svc.solve(svc.SolveMode.AREA_RATIO, 2.0, 1.4, FlowBranch.SUBSONIC)
    supersonic = svc.solve(svc.SolveMode.AREA_RATIO, 2.0, 1.4, FlowBranch.SUPERSONIC)
    assert subsonic.mach == pytest.approx(0.30590383, rel=1e-6)
    assert supersonic.mach == pytest.approx(2.19719812, rel=1e-6)
    assert subsonic.mach < 1.0 < supersonic.mach


def test_solve_from_area_ratio_both_returns_two_roots():
    result = svc.solve(svc.SolveMode.AREA_RATIO, 2.0, 1.4, FlowBranch.BOTH)
    assert result.ok
    assert result.both is not None
    subsonic, supersonic = result.both
    assert subsonic < 1.0 < supersonic


def test_area_ratio_of_one_is_sonic():
    result = svc.solve(svc.SolveMode.AREA_RATIO, 1.0, 1.4, FlowBranch.SUBSONIC)
    assert result.ok
    assert result.mach == 1.0
    assert result.status == "Sonic"


def test_every_declared_mode_can_be_solved():
    """No mode is offered that the physics layer cannot answer."""
    for info in svc.SOLVE_MODES:
        result = svc.solve(info.mode, info.default_value, 1.4, FlowBranch.SUPERSONIC)
        assert result.ok, f"{info.mode} failed with its own default value: {result.message}"


# ---------------------------------------------------------------------------
# results come from the physics layer
# ---------------------------------------------------------------------------


def test_every_displayed_ratio_matches_a_physics_call():
    result = svc.solve(svc.SolveMode.MACH, 2.5, 1.3)
    gas = PerfectGas(gamma=1.3)
    assert value_of(result, "T_over_T0") == pytest.approx(float(iso.temperature_ratio(2.5, gas)), rel=1e-15)
    assert value_of(result, "p_over_p0") == pytest.approx(float(iso.pressure_ratio(2.5, gas)), rel=1e-15)
    assert value_of(result, "rho_over_rho0") == pytest.approx(float(iso.density_ratio(2.5, gas)), rel=1e-15)
    assert value_of(result, "area_ratio") == pytest.approx(float(iso.area_ratio(2.5, gas)), rel=1e-15)


def test_reciprocal_rows_are_exact_reciprocals():
    result = svc.solve(svc.SolveMode.MACH, 2.0, 1.4)
    for canonical, inverse in (("p_over_p0", "p0_over_p"),
                               ("T_over_T0", "T0_over_T"),
                               ("rho_over_rho0", "rho0_over_rho")):
        assert value_of(result, inverse) == pytest.approx(1.0 / value_of(result, canonical), rel=1e-15)


def test_mach_angle_is_reported_in_degrees_for_display():
    """Radians below the application layer, degrees at the boundary."""
    result = svc.solve(svc.SolveMode.MACH, 2.0, 1.4)
    assert value_of(result, "mach_angle") == pytest.approx(30.0, abs=1e-9)


def test_mach_angle_absent_below_sonic():
    result = svc.solve(svc.SolveMode.MACH, 0.5, 1.4)
    assert value_of(result, "mach_angle") is None


def test_area_ratio_absent_at_rest():
    result = svc.solve(svc.SolveMode.MACH, 0.0, 1.4)
    assert result.ok
    assert value_of(result, "area_ratio") is None
    assert value_of(result, "p_over_p0") == 1.0


# ---------------------------------------------------------------------------
# invalid input is reported, never crashed on
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode,value", [
    (svc.SolveMode.MACH, -1.0),
    (svc.SolveMode.MACH, math.nan),
    (svc.SolveMode.PRESSURE_RATIO, 1.5),
    (svc.SolveMode.PRESSURE_RATIO, 0.0),
    (svc.SolveMode.PRESSURE_RATIO_INVERSE, 0.5),
    (svc.SolveMode.TEMPERATURE_RATIO, -0.2),
    (svc.SolveMode.AREA_RATIO, 0.8),
])
def test_invalid_input_reports_rather_than_raises(mode, value):
    result = svc.solve(mode, value, 1.4, FlowBranch.SUBSONIC)
    assert result.ok is False
    assert result.message, "an invalid input must explain itself"
    assert result.rows == ()


@pytest.mark.parametrize("gamma", [0.9, 1.0, 5.0, math.nan])
def test_invalid_gamma_reports(gamma):
    result = svc.solve(svc.SolveMode.MACH, 2.0, gamma)
    assert result.ok is False
    assert "gamma" in result.message.lower()


def test_reciprocal_of_zero_is_reported_not_a_division_error():
    result = svc.solve(svc.SolveMode.PRESSURE_RATIO_INVERSE, 0.0, 1.4)
    assert result.ok is False
    assert result.message


def test_extrapolated_gamma_reaches_the_result_as_a_diagnostic():
    result = svc.solve(svc.SolveMode.MACH, 2.0, 2.5)
    assert result.ok, "an unusual gamma is computable, not an error"
    assert any(d.code == "EXTRAPOLATED_GAMMA" for d in result.diagnostics)


def test_near_sonic_status_is_surfaced():
    gas = PerfectGas(gamma=1.4)
    area = float(iso.area_ratio(1.0002, gas))
    result = svc.solve(svc.SolveMode.AREA_RATIO, area, 1.4, FlowBranch.SUPERSONIC)
    assert result.ok
    assert result.status in ("Near sonic", "Sonic")


# ---------------------------------------------------------------------------
# table generation
# ---------------------------------------------------------------------------


def test_table_is_computed_not_looked_up():
    """Every cell must equal a direct physics call at that Mach number."""
    data = svc.generate_table(1.4, 0.5, 3.0, 0.5)
    gas = PerfectGas(gamma=1.4)
    keys = [c.key for c in data.columns]
    for row in data.values:
        mach = row[0]
        assert row[keys.index("p0_over_p")] == pytest.approx(
            1.0 / float(iso.pressure_ratio(mach, gas)), rel=1e-14)
        assert row[keys.index("area_ratio")] == pytest.approx(
            float(iso.area_ratio(mach, gas)), rel=1e-14)


def test_table_respects_range_and_step():
    data = svc.generate_table(1.4, 0.1, 1.0, 0.1, include_sonic=False)
    assert data.values[0, 0] == pytest.approx(0.1)
    assert data.values[-1, 0] == pytest.approx(1.0)
    spacing = np.diff(data.values[:, 0])
    assert np.allclose(spacing, 0.1, atol=1e-12)


def test_default_table_contains_the_sonic_row_exactly():
    data = svc.generate_table(1.4, 0.02, 5.0, 0.02)
    assert data.sonic_row is not None
    assert data.values[data.sonic_row, 0] == pytest.approx(1.0, abs=1e-12)
    assert data.values[data.sonic_row, -1] == pytest.approx(1.0, rel=1e-12), "A/A* = 1 at sonic"


def test_sonic_row_is_inserted_when_the_step_would_step_over_it():
    """M = 1 is the row every reader looks for; a 0.03 grid from 0.03 misses it."""
    data = svc.generate_table(1.4, 0.03, 2.0, 0.03, include_sonic=True)
    assert data.sonic_row is not None
    assert data.values[data.sonic_row, 0] == 1.0
    assert data.metadata["sonic_inserted"] is True


def test_sonic_insertion_can_be_switched_off():
    data = svc.generate_table(1.4, 0.03, 2.0, 0.03, include_sonic=False)
    assert data.sonic_row is None


def test_gamma_changes_the_table():
    air = svc.generate_table(1.4, 1.0, 3.0, 1.0)
    exhaust = svc.generate_table(1.22, 1.0, 3.0, 1.0)
    assert not np.allclose(air.values[:, 1], exhaust.values[:, 1])
    assert air.values[0, 4] == pytest.approx(1.0)      # A/A* = 1 at sonic, any gamma
    assert exhaust.values[0, 4] == pytest.approx(1.0)


def test_anderson_convention_is_the_reciprocal_of_the_standard_one():
    """The two conventions must be the same physics, printed the other way up."""
    anderson = svc.generate_table(1.4, 0.5, 3.0, 0.5, svc.TableConvention.ANDERSON)
    standard = svc.generate_table(1.4, 0.5, 3.0, 0.5, svc.TableConvention.STANDARD)
    assert np.allclose(anderson.values[:, 0], standard.values[:, 0])
    for column in (1, 2, 3):
        assert np.allclose(anderson.values[:, column], 1.0 / standard.values[:, column], rtol=1e-14)
    assert np.allclose(anderson.values[:, 4], standard.values[:, 4]), "A/A* is not a ratio pair"


def test_anderson_columns_are_the_classical_ones():
    data = svc.generate_table(1.4, 0.5, 2.0, 0.5, svc.TableConvention.ANDERSON)
    assert [c.key for c in data.columns] == [
        "mach", "p0_over_p", "rho0_over_rho", "T0_over_T", "area_ratio"]


@pytest.mark.parametrize("start,end,step,fragment", [
    (0.0, 5.0, 0.02, "greater than zero"),
    (-1.0, 5.0, 0.02, "greater than zero"),
    (2.0, 1.0, 0.02, "greater than start"),
    (0.1, 5.0, 0.0, "greater than zero"),
    (0.1, 5.0, -0.1, "greater than zero"),
])
def test_invalid_ranges_are_rejected_with_a_reason(start, end, step, fragment):
    with pytest.raises(ValueError) as excinfo:
        svc.generate_table(1.4, start, end, step)
    assert fragment in str(excinfo.value)


def test_row_limit_guards_against_an_accidental_tiny_step():
    with pytest.raises(ValueError) as excinfo:
        svc.generate_table(1.4, 0.01, 5.0, 1e-9)
    message = str(excinfo.value)
    assert "row limit" in message or "rows" in message
    assert f"{svc.MAX_TABLE_ROWS:,}" in message


def test_table_generation_is_deterministic():
    first = svc.generate_table(1.4, 0.02, 5.0, 0.02)
    second = svc.generate_table(1.4, 0.02, 5.0, 0.02)
    assert np.array_equal(first.values, second.values)


def test_table_and_scalar_agree_at_the_same_mach():
    """The table path and the calculator path must not diverge."""
    data = svc.generate_table(1.4, 0.5, 3.0, 0.5, svc.TableConvention.ANDERSON)
    for row in data.values:
        mach = float(row[0])
        result = svc.solve(svc.SolveMode.MACH, mach, 1.4)
        assert row[1] == pytest.approx(value_of(result, "p0_over_p"), rel=1e-14)
        assert row[4] == pytest.approx(value_of(result, "area_ratio"), rel=1e-14)


def test_large_table_uses_vectorised_physics_and_stays_quick():
    import time
    start = time.perf_counter()
    data = svc.generate_table(1.4, 0.01, 25.0, 0.005)
    elapsed = time.perf_counter() - start
    assert data.row_count > 4900
    assert elapsed < 1.0, f"{data.row_count} rows took {elapsed:.2f}s; a Python loop has crept in"
