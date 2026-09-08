"""The mass-flow service: the adapter, not the physics.

What is worth testing here is precisely what the service adds -- mode
dispatch, the dimensional/dimensionless split, error handling that returns a
message instead of raising, and table assembly. The gas dynamics itself is
verified in ``tests/physics``; where a value is checked below it is checked
against the physics layer, never against a number typed into this file.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.application.analysis import mass_flow_service as svc
from rocketforge.physics.compressible import FlowBranch, PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import mass_flow as mf

AIR = PerfectGas(gamma=1.4)


def value_of(result, key):
    return result.value_of(key)


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


def test_mach_mode_reports_the_physics_value():
    result = svc.solve(svc.SolveMode.MACH, 0.5, 1.4)
    assert result.ok
    assert result.mach == pytest.approx(0.5)
    assert value_of(result, "mass_flow_parameter") == pytest.approx(
        float(mf.mass_flow_parameter(0.5, AIR)), rel=1e-15)
    assert value_of(result, "flow_fraction") == pytest.approx(
        float(mf.mass_flow_over_choked(0.5, AIR)), rel=1e-15)
    assert value_of(result, "choked_coefficient") == pytest.approx(
        mf.choked_mass_flow_coefficient(AIR), rel=1e-15)


def test_pressure_ratio_mode_uses_the_isentropic_inverse():
    result = svc.solve(svc.SolveMode.PRESSURE_RATIO, 0.5, 1.4)
    assert result.ok
    assert result.mach == pytest.approx(float(iso.mach_from_pressure_ratio(0.5, AIR)), rel=1e-12)


@pytest.mark.parametrize("branch,expected_side", [
    (FlowBranch.SUBSONIC, "below"),
    (FlowBranch.SUPERSONIC, "above"),
])
def test_flow_ratio_mode_honours_the_branch(branch, expected_side):
    result = svc.solve(svc.SolveMode.FLOW_RATIO, 0.6, 1.4, branch=branch)
    assert result.ok
    assert (result.mach < 1.0) is (expected_side == "below")
    assert result.branch_used == branch.value
    assert value_of(result, "flow_fraction") == pytest.approx(0.6, abs=1e-9)


def test_flow_ratio_mode_can_return_both_roots():
    result = svc.solve(svc.SolveMode.FLOW_RATIO, 0.6, 1.4, branch=FlowBranch.BOTH)
    assert result.ok
    assert result.branch_used == "both"
    subsonic, supersonic = result.both
    assert subsonic < 1.0 < supersonic
    for mach in (subsonic, supersonic):
        assert mf.mass_flow_over_choked(mach, AIR) == pytest.approx(0.6, abs=1e-9)


def test_mass_flow_mode_inverts_a_flow_in_kilograms_per_second():
    state = svc.FlowState(area=0.01, stagnation_pressure=1e6,
                          stagnation_temperature=300.0, gas_constant=287.0528)
    result = svc.solve(svc.SolveMode.MASS_FLOW, 20.0, 1.4, state,
                       branch=FlowBranch.SUBSONIC)
    assert result.ok
    assert value_of(result, "mass_flow") == pytest.approx(20.0, rel=1e-8)
    assert result.mach < 1.0


def test_mass_flow_above_the_choked_value_is_refused_with_a_reason():
    state = svc.FlowState()
    ceiling = mf.choked_mass_flow(
        PerfectGas(gamma=1.4, gas_constant=state.gas_constant),
        state.area, state.stagnation_pressure, state.stagnation_temperature)
    result = svc.solve(svc.SolveMode.MASS_FLOW, ceiling * 1.5, 1.4, state)
    assert not result.ok
    assert "cannot exceed" in result.message


# ---------------------------------------------------------------------------
# the dimensional / dimensionless split
# ---------------------------------------------------------------------------


def test_dimensional_rows_are_filled_when_the_state_supports_them():
    state = svc.FlowState(area=0.02, stagnation_pressure=2e6,
                          stagnation_temperature=1200.0, gas_constant=320.0)
    result = svc.solve(svc.SolveMode.MACH, 0.4, 1.25, state)
    sized = PerfectGas(gamma=1.25, gas_constant=320.0)
    assert value_of(result, "mass_flow") == pytest.approx(
        float(mf.mass_flow(0.4, sized, 0.02, 2e6, 1200.0)), rel=1e-14)
    assert value_of(result, "mass_flux") == pytest.approx(
        float(mf.mass_flux(0.4, sized, 2e6, 1200.0)), rel=1e-14)
    assert value_of(result, "choked_mass_flow") == pytest.approx(
        mf.choked_mass_flow(sized, 0.02, 2e6, 1200.0), rel=1e-14)


@pytest.mark.parametrize("field", ["area", "stagnation_pressure",
                                   "stagnation_temperature", "gas_constant"])
def test_an_incomplete_state_leaves_dimensional_rows_empty_rather_than_guessing(field):
    """The service must not invent a gas constant to fill a blank field."""
    state = svc.FlowState(**{field: 0.0})
    assert not state.complete
    result = svc.solve(svc.SolveMode.MACH, 0.5, 1.4, state)
    assert result.ok, "the dimensionless answer is still perfectly available"
    for key in ("mass_flow", "mass_flux", "choked_mass_flow", "throat_area"):
        assert value_of(result, key) is None
    # ...while the dimensionless block is complete.
    for key in ("mass_flow_parameter", "flow_fraction", "choked_coefficient"):
        assert value_of(result, key) is not None


def test_a_dimensional_mode_with_an_incomplete_state_says_what_is_missing():
    result = svc.solve(svc.SolveMode.MASS_FLOW, 5.0, 1.4, svc.FlowState(area=0.0))
    assert not result.ok
    assert "area" in result.message


def test_throat_area_is_the_area_that_would_choke_this_flow():
    state = svc.FlowState(area=0.05)
    result = svc.solve(svc.SolveMode.MACH, 0.3, 1.4, state)
    assert value_of(result, "throat_area") == pytest.approx(
        0.05 / float(iso.area_ratio(0.3, AIR)), rel=1e-12)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mach,expected", [
    (0.3, "Subsonic"), (1.0, "Choked"), (2.0, "Supersonic"),
])
def test_status_names_the_flow_regime(mach, expected):
    assert svc.solve(svc.SolveMode.MACH, mach, 1.4).status == expected


def test_the_choked_status_explains_what_choking_means():
    result = svc.solve(svc.SolveMode.MACH, 1.0, 1.4)
    assert "most mass it can" in result.message


# ---------------------------------------------------------------------------
# invalid input returns a message, never an exception
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode,value", [
    (svc.SolveMode.MACH, -1.0),
    (svc.SolveMode.MACH, math.nan),
    (svc.SolveMode.FLOW_RATIO, 1.5),
    (svc.SolveMode.FLOW_RATIO, 0.0),
    (svc.SolveMode.PRESSURE_RATIO, 1.5),
    (svc.SolveMode.PRESSURE_RATIO, 0.0),
    (svc.SolveMode.MASS_FLOW, -3.0),
])
def test_invalid_input_is_reported_not_raised(mode, value):
    result = svc.solve(mode, value, 1.4)
    assert not result.ok
    assert result.rows == ()
    assert result.message


@pytest.mark.parametrize("gamma", [0.9, 1.0, 3.5, -1.0, math.nan])
def test_an_impossible_gamma_is_reported_not_raised(gamma):
    result = svc.solve(svc.SolveMode.MACH, 0.5, gamma)
    assert not result.ok
    assert result.message


def test_an_advisory_gamma_still_computes_but_says_so():
    result = svc.solve(svc.SolveMode.MACH, 0.5, 1.02)
    assert result.ok
    assert any(d.code == "EXTRAPOLATED_GAMMA" for d in result.diagnostics)


# ---------------------------------------------------------------------------
# choking report
# ---------------------------------------------------------------------------


def test_choking_report_agrees_with_the_physics_predicate():
    for ratio in (0.1, 0.4, 0.5283, 0.6, 0.99, 1.0):
        choked, message = svc.choking_report(ratio, 1.4)
        assert choked is mf.is_choked(ratio, AIR)
        assert "0.5283" in message
        assert ("Choked" in message) is choked


def test_choking_report_uses_the_gas_it_is_given():
    _, message = svc.choking_report(0.5, 1.2)
    assert f"{mf.critical_pressure_ratio(PerfectGas(gamma=1.2)):.4f}" in message


def test_choking_report_does_not_claim_to_classify_a_nozzle():
    """Scope guard: the wording must stay about a convergent passage."""
    _, message = svc.choking_report(0.3, 1.4)
    assert "nozzle" not in message.lower()


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------


def test_dimensionless_table_columns_are_computed_from_the_physics():
    table = svc.generate_table(1.4, 0.1, 3.0, 0.1)
    keys = [c.key for c in table.columns]
    assert keys[0] == "mach"
    for index, mach in enumerate(table.values[:, 0]):
        assert table.values[index, keys.index("mass_flow_parameter")] == pytest.approx(
            float(mf.mass_flow_parameter(mach, AIR)), rel=1e-14)
        assert table.values[index, keys.index("area_ratio")] == pytest.approx(
            float(iso.area_ratio(mach, AIR)), rel=1e-14)


def test_a_table_may_start_at_rest_where_the_area_ratio_is_unbounded():
    """Mass flow is zero at M = 0 and perfectly defined; A/A* is not.

    The row is kept and the unbounded entry reported as infinity, rather than
    the whole row being dropped because one column has no finite value.
    """
    table = svc.generate_table(1.4, 0.0, 1.0, 0.5)
    keys = [c.key for c in table.columns]
    assert table.values[0, 0] == 0.0
    assert table.values[0, keys.index("mass_flow_parameter")] == 0.0
    assert math.isinf(table.values[0, keys.index("area_ratio")])
    assert np.isfinite(table.values[1:, keys.index("area_ratio")]).all()


def test_the_sonic_row_is_inserted_and_located():
    table = svc.generate_table(1.4, 0.3, 2.0, 0.4)
    assert table.sonic_row is not None
    assert table.values[table.sonic_row, 0] == pytest.approx(1.0)
    keys = [c.key for c in table.columns]
    assert table.values[table.sonic_row, keys.index("flow_fraction")] == pytest.approx(1.0)


def test_the_dimensional_table_applies_the_state():
    state = svc.FlowState(area=0.03, stagnation_pressure=5e5,
                          stagnation_temperature=800.0, gas_constant=300.0)
    table = svc.generate_table(1.4, 0.2, 2.0, 0.2,
                               svc.TableConvention.DIMENSIONAL, state)
    keys = [c.key for c in table.columns]
    sized = PerfectGas(gamma=1.4, gas_constant=300.0)
    for index, mach in enumerate(table.values[:, 0]):
        assert table.values[index, keys.index("mass_flow")] == pytest.approx(
            float(mf.mass_flow(mach, sized, 0.03, 5e5, 800.0)), rel=1e-14)
    assert table.metadata["area"] == 0.03


def test_a_dimensional_table_without_a_state_is_refused():
    with pytest.raises(ValueError, match="area"):
        svc.generate_table(1.4, 0.2, 2.0, 0.2,
                           svc.TableConvention.DIMENSIONAL, svc.FlowState(area=0.0))


def test_table_metadata_records_how_it_was_made():
    table = svc.generate_table(1.35, 0.1, 2.0, 0.1)
    assert table.gamma == pytest.approx(1.35)
    assert table.metadata["model"] == "perfect_gas_mass_flow_v1"
    assert table.metadata["rows"] == table.row_count
    assert table.metadata["choked_coefficient"] == pytest.approx(
        mf.choked_mass_flow_coefficient(PerfectGas(gamma=1.35)))


@pytest.mark.parametrize("start,end,step,fragment", [
    (0.1, 2.0, 0.0, "Step"),
    (0.1, 2.0, -0.1, "Step"),
    (2.0, 1.0, 0.1, "greater than start"),
    (-0.5, 2.0, 0.1, "negative"),
    (0.1, 2.0, 1e-9, "row limit"),
])
def test_an_impossible_range_is_refused_with_a_reason(start, end, step, fragment):
    with pytest.raises(ValueError, match=fragment):
        svc.generate_table(1.4, start, end, step)


def test_the_row_limit_is_enforced_before_allocating():
    with pytest.raises(ValueError, match="row limit"):
        svc.mach_grid(0.0, 50.0, 1e-9)


def test_gamma_changes_the_whole_table():
    a = svc.generate_table(1.2, 0.1, 2.0, 0.1)
    b = svc.generate_table(1.4, 0.1, 2.0, 0.1)
    assert not np.allclose(a.values[:, 1], b.values[:, 1])
