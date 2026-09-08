"""The Prandtl-Meyer and Oblique Shock services: the adapters, not the physics.

What is worth testing here is what the services add -- mode dispatch, the
degree/radian boundary, branch handling, detachment reporting, and table
assembly. Values are checked against the physics layer rather than against
numbers typed into this file.

The degree boundary gets particular attention. It is the one place in the
project where a unit error is both easy to make and invisible in the result:
a Mach number is a Mach number either way, and only the angles would be wrong.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.application.analysis import oblique_shock_service as oss
from rocketforge.application.analysis import prandtl_meyer_service as pms
from rocketforge.physics.compressible import PerfectGas, ShockBranch
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import oblique_shock as obl
from rocketforge.physics.compressible import prandtl_meyer as pm

AIR = PerfectGas(gamma=1.4)


def value_of(result, key):
    return result.value_of(key)


# ===========================================================================
# Prandtl-Meyer
# ===========================================================================


def test_every_pm_mode_has_a_descriptor_and_a_workable_default():
    assert len(pms.SOLVE_MODES) == len(pms.SolveMode)
    for info in pms.SOLVE_MODES:
        assert pms.mode_info(info.mode) is info
        assert info.label and info.symbol and info.hint
        assert pms.solve(info.mode, info.default_value, 1.4).ok, info.mode


def test_only_the_angle_mode_iterates():
    assert [i.mode for i in pms.SOLVE_MODES if i.iterative] == [pms.SolveMode.NU]


def test_pm_readout_is_in_degrees_and_matches_the_radian_physics():
    """The boundary test: the service converts, and converts correctly."""
    result = pms.solve(pms.SolveMode.MACH, 2.0, 1.4)
    assert value_of(result, "nu") == pytest.approx(
        math.degrees(float(pm.nu(2.0, AIR))), rel=1e-14)
    assert value_of(result, "mach_angle") == pytest.approx(
        math.degrees(float(iso.mach_angle(2.0))), rel=1e-14)
    # ...and the numbers are the familiar degrees, not radians.
    assert value_of(result, "nu") == pytest.approx(26.3797608134, abs=1e-9)
    assert value_of(result, "mach_angle") == pytest.approx(30.0, abs=1e-9)


def test_solving_from_an_angle_takes_degrees_in():
    result = pms.solve(pms.SolveMode.NU, 26.3797608134, 1.4)
    assert result.ok
    assert result.mach == pytest.approx(2.0, abs=1e-9)


def test_the_two_pm_modes_are_inverses_of_each_other():
    for mach in (1.0, 1.5, 3.0, 8.0):
        forward = pms.solve(pms.SolveMode.MACH, mach, 1.4)
        backward = pms.solve(pms.SolveMode.NU, value_of(forward, "nu"), 1.4)
        assert backward.mach == pytest.approx(mach, rel=1e-8)


def test_the_remaining_turn_is_what_is_left_of_the_maximum():
    result = pms.solve(pms.SolveMode.MACH, 3.0, 1.4)
    assert (value_of(result, "nu") + value_of(result, "nu_remaining")
            == pytest.approx(value_of(result, "nu_max"), rel=1e-12))
    assert value_of(result, "nu_max") == pytest.approx(pms.nu_max_degrees(1.4), rel=1e-15)


def test_nu_max_in_degrees_is_the_published_number():
    assert pms.nu_max_degrees(1.4) == pytest.approx(130.4540768505, abs=5e-8)
    assert pms.nu_max_degrees(1.2) == pytest.approx(208.49623113, abs=5e-8)


@pytest.mark.parametrize("mach,expected", [(1.0, "Sonic"), (2.0, "Supersonic")])
def test_pm_status_names_the_regime(mach, expected):
    assert pms.solve(pms.SolveMode.MACH, mach, 1.4).status == expected


@pytest.mark.parametrize("mode,value,fragment", [
    (pms.SolveMode.MACH, 0.5, "supersonic"),
    (pms.SolveMode.MACH, math.nan, "finite"),
    (pms.SolveMode.NU, -5.0, "negative"),
    (pms.SolveMode.NU, 131.0, "maximum expansion"),
    (pms.SolveMode.NU, 200.0, "maximum expansion"),
])
def test_pm_invalid_input_is_reported_not_raised(mode, value, fragment):
    result = pms.solve(mode, value, 1.4)
    assert not result.ok
    assert result.rows == ()
    assert fragment in result.message, result.message


def test_the_pm_ceiling_moves_with_gamma():
    """131 degrees is impossible for air and ordinary for gamma = 1.2."""
    assert not pms.solve(pms.SolveMode.NU, 131.0, 1.4).ok
    assert pms.solve(pms.SolveMode.NU, 131.0, 1.2).ok


@pytest.mark.parametrize("gamma", [0.9, 1.0, 3.5, math.nan])
def test_pm_impossible_gamma_is_reported_not_raised(gamma):
    assert not pms.solve(pms.SolveMode.MACH, 2.0, gamma).ok


# ---------------------------------------------------------------------------
# the expansion turn
# ---------------------------------------------------------------------------


def test_the_expansion_turn_reports_the_downstream_mach_as_its_headline():
    result = pms.expansion_turn(2.0, 10.0, 1.4)
    assert result.ok
    assert result.mach == pytest.approx(value_of(result, "mach2"), rel=1e-15)
    assert result.mach > 2.0


def test_the_expansion_turn_matches_the_physics_in_degrees():
    physics = pm.expand(2.0, math.radians(10.0), AIR).unwrap()
    result = pms.expansion_turn(2.0, 10.0, 1.4)
    assert value_of(result, "nu1") == pytest.approx(math.degrees(physics.nu1), rel=1e-14)
    assert value_of(result, "nu2") == pytest.approx(math.degrees(physics.nu2), rel=1e-14)
    assert value_of(result, "fan_angle") == pytest.approx(
        math.degrees(physics.fan_angle), rel=1e-14)
    assert value_of(result, "pressure_ratio") == pytest.approx(
        physics.pressure_ratio, rel=1e-15)


def test_the_turn_adds_to_nu_in_the_units_the_user_typed():
    result = pms.expansion_turn(2.0, 15.0, 1.4)
    assert value_of(result, "nu2") - value_of(result, "nu1") == pytest.approx(15.0, abs=1e-9)


def test_the_expansion_says_the_stagnation_state_is_untouched():
    result = pms.expansion_turn(2.0, 10.0, 1.4)
    assert value_of(result, "stagnation_pressure_ratio") == 1.0
    assert value_of(result, "stagnation_temperature_ratio") == 1.0
    assert "no loss" in result.message.lower() or "unchanged" in result.message


def test_a_turn_past_the_maximum_is_reported_not_raised():
    result = pms.expansion_turn(2.0, 120.0, 1.4)
    assert not result.ok
    assert result.status == "No solution"
    assert "maximum expansion" in result.message


def test_a_negative_turn_is_refused_by_the_service_too():
    result = pms.expansion_turn(2.0, -5.0, 1.4)
    assert not result.ok
    assert result.message


# ---------------------------------------------------------------------------
# the PM table
# ---------------------------------------------------------------------------


def test_the_pm_table_prints_the_appendix_columns_by_default():
    table = pms.generate_table(1.4, 1.0, 5.0, 0.02)
    assert [c.key for c in table.columns] == ["mach", "nu", "mach_angle"]
    assert table.metadata["angle_units"] == "degrees"


def test_every_pm_table_value_matches_the_physics():
    table = pms.generate_table(1.3, 1.0, 6.0, 0.25)
    gas = PerfectGas(gamma=1.3)
    for row in table.values:
        mach = row[0]
        assert row[1] == pytest.approx(math.degrees(float(pm.nu(mach, gas))), rel=1e-13)
        assert row[2] == pytest.approx(math.degrees(float(iso.mach_angle(mach))), rel=1e-13)


def test_the_pm_table_starts_at_sonic_and_marks_it():
    table = pms.generate_table(1.4, 1.0, 3.0, 0.1)
    assert table.sonic_row == 0
    assert table.values[0, 1] == 0.0
    assert table.values[0, 2] == pytest.approx(90.0)


def test_the_pm_table_cannot_start_below_sonic():
    with pytest.raises(ValueError, match="1 or greater"):
        pms.generate_table(1.4, 0.5, 3.0, 0.1)


def test_the_extended_pm_table_adds_the_isentropic_ratios():
    table = pms.generate_table(1.4, 1.0, 4.0, 0.5, pms.TableConvention.EXTENDED)
    keys = [c.key for c in table.columns]
    assert "p_over_p0" in keys and "area_ratio" in keys
    for row in table.values:
        assert row[keys.index("p_over_p0")] == pytest.approx(
            float(iso.pressure_ratio(row[0], AIR)), rel=1e-14)


@pytest.mark.parametrize("start,end,step,fragment", [
    (1.0, 5.0, 0.0, "Step"),
    (1.0, 5.0, -0.1, "Step"),
    (3.0, 2.0, 0.1, "greater than start"),
    (1.0, 5.0, 1e-9, "row limit"),
])
def test_an_impossible_pm_range_is_refused_with_a_reason(start, end, step, fragment):
    with pytest.raises(ValueError, match=fragment):
        pms.generate_table(1.4, start, end, step)


def test_the_pm_table_columns_move_in_the_right_directions():
    table = pms.generate_table(1.4, 1.0, 20.0, 0.05)
    assert np.all(np.diff(table.values[:, 1]) > 0.0), "nu increases"
    assert np.all(np.diff(table.values[:, 2]) < 0.0), "mu decreases"
    assert np.all(table.values[:, 1] < pms.nu_max_degrees(1.4))
    assert table.values[0, 2] == pytest.approx(90.0)


# ===========================================================================
# Oblique shock
# ===========================================================================


def test_every_oblique_mode_has_a_descriptor_and_a_workable_default():
    assert len(oss.SOLVE_MODES) == len(oss.SolveMode)
    for info in oss.SOLVE_MODES:
        assert oss.mode_info(info.mode) is info
        assert oss.solve(info.mode, info.default_value, 2.0, 1.4).ok, info.mode


def test_only_the_deflection_mode_needs_a_branch_and_iterates():
    assert [i.mode for i in oss.SOLVE_MODES if i.needs_branch] == [oss.SolveMode.THETA]
    assert [i.mode for i in oss.SOLVE_MODES if i.iterative] == [oss.SolveMode.THETA]


def test_the_two_oblique_modes_agree_on_the_same_shock():
    from_theta = oss.solve(oss.SolveMode.THETA, 10.0, 2.0, 1.4, ShockBranch.WEAK)
    from_beta = oss.solve(oss.SolveMode.BETA, value_of(from_theta, "beta"), 2.0, 1.4)
    assert value_of(from_beta, "theta") == pytest.approx(10.0, abs=1e-7)
    assert value_of(from_beta, "mach2") == pytest.approx(value_of(from_theta, "mach2"),
                                                         rel=1e-9)


def test_oblique_readout_is_in_degrees_and_matches_the_radian_physics():
    physics = obl.solve(2.0, math.radians(10.0), AIR, ShockBranch.WEAK).unwrap()
    result = oss.solve(oss.SolveMode.THETA, 10.0, 2.0, 1.4, ShockBranch.WEAK)
    assert value_of(result, "beta") == pytest.approx(math.degrees(physics.beta), rel=1e-14)
    assert value_of(result, "theta") == pytest.approx(10.0, abs=1e-9)
    assert value_of(result, "mach_angle") == pytest.approx(30.0, abs=1e-9)
    assert value_of(result, "theta_max") == pytest.approx(22.97353176, abs=5e-8)
    assert value_of(result, "mach2") == pytest.approx(physics.mach2, rel=1e-15)
    assert value_of(result, "pressure_ratio") == pytest.approx(physics.pressure_ratio,
                                                               rel=1e-15)


def test_the_total_pressure_loss_is_the_percentage_it_says():
    result = oss.solve(oss.SolveMode.THETA, 20.0, 3.0, 1.4, ShockBranch.WEAK)
    ratio = value_of(result, "stagnation_pressure_ratio")
    assert value_of(result, "stagnation_pressure_loss") == pytest.approx(
        100.0 * (1.0 - ratio), rel=1e-12)


def test_the_normal_component_is_reported_so_the_reuse_is_visible():
    result = oss.solve(oss.SolveMode.THETA, 10.0, 2.0, 1.4, ShockBranch.WEAK)
    assert value_of(result, "mach_normal1") == pytest.approx(
        2.0 * math.sin(math.radians(value_of(result, "beta"))), rel=1e-12)
    assert value_of(result, "mach_normal1") > 1.0
    assert value_of(result, "mach_normal2") < 1.0


def test_the_branch_changes_the_answer_and_is_reported():
    weak = oss.solve(oss.SolveMode.THETA, 10.0, 2.0, 1.4, ShockBranch.WEAK)
    strong = oss.solve(oss.SolveMode.THETA, 10.0, 2.0, 1.4, ShockBranch.STRONG)
    assert weak.branch_used == "weak" and strong.branch_used == "strong"
    assert value_of(strong, "beta") > value_of(weak, "beta")
    assert (value_of(strong, "stagnation_pressure_ratio")
            < value_of(weak, "stagnation_pressure_ratio"))
    assert strong.status == "Strong branch"


def test_both_branches_are_kept_in_separate_groups():
    result = oss.solve(oss.SolveMode.THETA, 10.0, 2.0, 1.4, ShockBranch.BOTH)
    assert result.ok
    assert result.branch_used == "both"
    groups = {row.group for row in result.rows}
    assert groups == {"Weak solution", "Strong solution"}
    weak_beta = value_of(result, "weak_beta")
    strong_beta = value_of(result, "strong_beta")
    assert weak_beta < strong_beta
    assert result.both == pytest.approx((math.radians(weak_beta), math.radians(strong_beta)),
                                        rel=1e-12)


def test_the_beta_mode_offers_no_branch_because_there_is_nothing_to_choose():
    result = oss.solve(oss.SolveMode.BETA, 39.31393184, 2.0, 1.4)
    assert result.ok
    assert result.branch_used == ""
    assert oss.mode_info(oss.SolveMode.BETA).needs_branch is False


# ---------------------------------------------------------------------------
# detachment
# ---------------------------------------------------------------------------


def test_a_deflection_past_the_limit_produces_no_result_at_all():
    """Not a substituted solution, and not a numerical failure."""
    result = oss.solve(oss.SolveMode.THETA, 30.0, 2.0, 1.4, ShockBranch.WEAK)
    assert not result.ok
    assert result.mach is None
    assert result.rows == ()
    assert result.status == "Detached"
    assert "22.9735" in result.message and "30.0000" in result.message
    assert "detached bow shock" in result.message


def test_detachment_is_reported_on_every_branch_including_both():
    for branch in (ShockBranch.WEAK, ShockBranch.STRONG, ShockBranch.BOTH):
        result = oss.solve(oss.SolveMode.THETA, 30.0, 2.0, 1.4, branch)
        assert result.status == "Detached"
        assert result.rows == ()


def test_the_limits_are_available_for_a_caption():
    limits = oss.limits_for(2.0, 1.4)
    assert limits["machAngle"] == pytest.approx(30.0, abs=1e-9)
    assert limits["thetaMax"] == pytest.approx(22.97353176, abs=5e-8)
    assert limits["betaAtThetaMax"] == pytest.approx(64.66897983, abs=5e-8)
    assert limits["betaSonic"] == pytest.approx(61.48537164, abs=5e-8)
    assert limits["betaSonic"] < limits["betaAtThetaMax"]


def test_the_limits_are_empty_rather_than_wrong_for_a_subsonic_stream():
    assert oss.limits_for(0.8, 1.4) == {}


@pytest.mark.parametrize("mach1,fragment", [(1.0, "greater than 1"), (0.5, "greater than 1")])
def test_a_subsonic_upstream_is_reported_not_raised(mach1, fragment):
    result = oss.solve(oss.SolveMode.THETA, 10.0, mach1, 1.4)
    assert not result.ok
    assert fragment in result.message


def test_a_wave_angle_outside_the_admissible_range_is_reported_not_raised():
    result = oss.solve(oss.SolveMode.BETA, 10.0, 2.0, 1.4)   # below the Mach angle
    assert not result.ok
    assert "Mach angle" in result.message


# ---------------------------------------------------------------------------
# the parameter study
# ---------------------------------------------------------------------------


def test_the_study_sweeps_the_deflection_on_one_branch():
    table = oss.generate_table(2.0, 1.4, 0.0, 20.0, 2.0)
    assert [c.key for c in table.columns][0] == "theta"
    for row in table.values:
        theta, beta = row[0], row[1]
        physics = obl.solve(2.0, math.radians(theta), AIR, ShockBranch.WEAK).unwrap()
        assert beta == pytest.approx(math.degrees(physics.beta), rel=1e-12)
        assert row[2] == pytest.approx(physics.mach2, rel=1e-12)


def test_the_study_is_capped_at_the_attachment_limit():
    """Past theta_max there is no attached shock, and no row is invented."""
    table = oss.generate_table(2.0, 1.4, 0.0, 40.0, 2.0)
    assert table.metadata["capped_at_theta_max"] is True
    assert table.metadata["requested_end"] == 40.0
    assert table.values[:, 0].max() <= table.metadata["theta_max"] + 1e-9


def test_the_last_row_is_the_maximum_deflection_and_is_marked():
    table = oss.generate_table(3.0, 1.4, 0.0, 40.0, 5.0)
    assert table.sonic_row == table.values.shape[0] - 1
    assert table.values[-1, 0] == pytest.approx(table.metadata["theta_max"], rel=1e-12)


def test_an_uncapped_range_says_so():
    table = oss.generate_table(3.0, 1.4, 0.0, 10.0, 2.0)
    assert table.metadata["capped_at_theta_max"] is False


def test_the_comparison_convention_puts_the_branches_side_by_side():
    table = oss.generate_table(2.0, 1.4, 2.0, 20.0, 4.0, oss.TableConvention.COMPARISON)
    keys = [c.key for c in table.columns]
    assert "beta_weak" in keys and "beta_strong" in keys
    # Every row but the last: two distinct wave angles, the strong one costing
    # more. The last row is theta_max itself, where the branches merge into one
    # -- so it is asserted as an equality rather than excused.
    for row in table.values[:-1]:
        assert row[keys.index("beta_strong")] > row[keys.index("beta_weak")]
        assert row[keys.index("p02_strong")] < row[keys.index("p02_weak")]

    merged = table.values[-1]
    assert merged[0] == pytest.approx(table.metadata["theta_max"], rel=1e-12)
    assert merged[keys.index("beta_strong")] == pytest.approx(
        merged[keys.index("beta_weak")], rel=1e-12)
    assert merged[keys.index("p02_strong")] == pytest.approx(
        merged[keys.index("p02_weak")], rel=1e-12)


def test_the_study_can_sweep_the_strong_branch():
    table = oss.generate_table(2.0, 1.4, 2.0, 20.0, 4.0, oss.TableConvention.BRANCH,
                              ShockBranch.STRONG)
    assert table.metadata["branch"] == "strong"
    for row in table.values:
        physics = obl.solve(2.0, math.radians(row[0]), AIR, ShockBranch.STRONG).unwrap()
        assert row[1] == pytest.approx(math.degrees(physics.beta), rel=1e-12)


def test_a_study_starting_past_the_limit_is_refused_with_a_reason():
    with pytest.raises(ValueError, match="No attached shock"):
        oss.generate_table(2.0, 1.4, 30.0, 40.0, 1.0)


@pytest.mark.parametrize("start,end,step,fragment", [
    (0.0, 20.0, 0.0, "Step"),
    (20.0, 10.0, 1.0, "greater than the start"),
    (-1.0, 20.0, 1.0, "negative"),
    (0.0, 20.0, 1e-9, "row limit"),
])
def test_an_impossible_study_range_is_refused_with_a_reason(start, end, step, fragment):
    with pytest.raises(ValueError, match=fragment):
        oss.generate_table(2.0, 1.4, start, end, step)


def test_the_study_records_how_it_was_made():
    table = oss.generate_table(3.0, 1.4, 0.0, 30.0, 1.0)
    assert table.metadata["model"] == "perfect_gas_oblique_shock_v1"
    assert table.metadata["mach1"] == 3.0
    assert table.metadata["angle_units"] == "degrees"
    assert table.metadata["theta_max"] == pytest.approx(34.07343978, abs=5e-8)


# ---------------------------------------------------------------------------
# the diagram data
# ---------------------------------------------------------------------------


def test_the_curve_is_split_into_the_two_branches_at_the_maximum():
    curve = oss.curve_data(2.0, 1.4, 200)
    assert curve["weak"] and curve["strong"]
    assert all(point["y"] <= curve["betaAtThetaMax"] + 1e-9 for point in curve["weak"])
    assert all(point["y"] >= curve["betaAtThetaMax"] - 1e-9 for point in curve["strong"])


def test_the_curve_starts_and_ends_at_zero_deflection():
    curve = oss.curve_data(3.0, 1.4, 200)
    assert curve["weak"][0]["x"] == pytest.approx(0.0, abs=1e-9)
    assert curve["weak"][0]["y"] == pytest.approx(curve["machAngle"], rel=1e-12)
    assert curve["strong"][-1]["x"] == pytest.approx(0.0, abs=1e-9)
    assert curve["strong"][-1]["y"] == pytest.approx(90.0, abs=1e-6)


def test_the_curve_peaks_at_the_marked_maximum():
    curve = oss.curve_data(2.0, 1.4, 800)
    peak = max(point["x"] for point in curve["weak"] + curve["strong"])
    assert peak == pytest.approx(curve["thetaMax"], rel=1e-3)
    assert curve["thetaMax"] == pytest.approx(22.97353176, abs=5e-8)


def test_the_curve_carries_the_three_markers_a_reader_needs():
    curve = oss.curve_data(3.0, 1.4, 100)
    assert curve["machAngle"] < curve["betaSonic"] < curve["betaAtThetaMax"] < 90.0


def test_the_curve_comes_from_the_same_solver_the_calculator_uses():
    """A chart drawn from a second implementation would be a second answer."""
    curve = oss.curve_data(2.0, 1.4, 400)
    for point in curve["weak"][5:60:10]:
        solved = oss.solve(oss.SolveMode.BETA, point["y"], 2.0, 1.4)
        assert value_of(solved, "theta") == pytest.approx(point["x"], abs=1e-9)
