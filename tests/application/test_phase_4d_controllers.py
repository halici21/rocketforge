"""The Qt bridge for the Prandtl-Meyer and Oblique Shock pages.

These need a QGuiApplication but no window and no QML. What they check is that
the interface is handed correct, complete state -- and, just as importantly,
that nothing stale survives a change of mode, branch, gamma or range.

The state transitions at the bottom are the specification's own list. Each one
is a way a page can lie: showing a branch control where there is no branch,
keeping a detached request's previous wave angle, or leaving one Mach number's
reference comparison beside another Mach number's result.
"""

from __future__ import annotations

import math
import sys

import pytest
from PySide6.QtGui import QGuiApplication

from rocketforge.application.analysis.isentropic_controller import IsentropicController
from rocketforge.application.analysis.mass_flow_controller import MassFlowController
from rocketforge.application.analysis.normal_shock_controller import NormalShockController
from rocketforge.application.analysis.oblique_shock_controller import ObliqueShockController
from rocketforge.application.analysis.prandtl_meyer_controller import PrandtlMeyerController
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import normal_shock as ns
from rocketforge.physics.compressible import oblique_shock as obl
from rocketforge.physics.compressible import prandtl_meyer as pm

AIR = PerfectGas(gamma=1.4)


@pytest.fixture(scope="session")
def qt_app():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    yield app


@pytest.fixture()
def expansion(qt_app):
    return PrandtlMeyerController()


@pytest.fixture()
def oblique(qt_app):
    return ObliqueShockController()


def value_of(controller, key):
    for row in controller.results:
        if row["key"] == key:
            return row
    raise AssertionError(f"{key} not in the readout")


# ===========================================================================
# Prandtl-Meyer
# ===========================================================================


def test_prandtl_meyer_opens_computed(expansion):
    assert expansion.valid
    assert expansion.results
    assert expansion.tableRowCount > 0
    assert expansion.statusLabel == "Supersonic"


def test_prandtl_meyer_readout_is_in_degrees(expansion):
    expansion.setMachAndSolve(2.0)
    assert value_of(expansion, "nu")["raw"] == pytest.approx(26.3797608134, abs=1e-9)
    assert value_of(expansion, "mach_angle")["raw"] == pytest.approx(30.0, abs=1e-9)
    assert value_of(expansion, "nu")["unit"] == "°"


def test_prandtl_meyer_publishes_its_ceiling(expansion):
    assert expansion.nuMax == pytest.approx(130.4540768505, abs=5e-8)
    expansion.gamma = 1.2
    assert expansion.nuMax == pytest.approx(208.49623113, abs=5e-8)


def test_prandtl_meyer_hint_names_the_ceiling_for_the_angle_mode(expansion):
    expansion.mode = "nu"
    assert "130.45" in expansion.inputHint
    expansion.mode = "mach"
    assert "1 or greater" in expansion.inputHint


def test_prandtl_meyer_marks_the_sonic_row(expansion):
    assert expansion.sonicRow == 0
    assert expansion.tableModel.machAt(0) == pytest.approx(1.0)


def test_prandtl_meyer_compares_against_appendix_c(expansion):
    expansion.compareEnabled = True
    summary = expansion.comparisonSummary
    assert summary["rows"] > 0
    assert summary["review"] == 0
    assert summary["status"] == "PASS"
    assert "Appendix C" in summary["citation"]


def test_prandtl_meyer_reference_row_is_never_interpolated(expansion):
    expansion.compareEnabled = True
    expansion.tableStart = 1.005
    expansion.tableStep = 0.5
    expansion.regenerateTable()
    assert expansion.comparisonForRow(0) == []
    assert expansion.hasReferenceRow(0) is False


def test_prandtl_meyer_reference_switches_off_for_another_gamma(expansion):
    expansion.compareEnabled = True
    expansion.tableGamma = 1.3
    expansion.regenerateTable()
    assert expansion.referenceAvailable is False
    assert "1.3" in expansion.referenceMessage
    assert expansion.comparisonSummary == {}


def test_prandtl_meyer_reference_series_stays_inside_the_table_range(expansion):
    expansion.tableStart = 2.0
    expansion.tableEnd = 3.0
    expansion.regenerateTable()
    series = expansion.referenceSeries("nu")
    assert series
    assert all(2.0 <= point["x"] <= 3.0 for point in series)


def test_the_expansion_turn_is_off_until_asked_for(expansion):
    assert expansion.expansionEnabled is False
    assert expansion.expansionResults == []
    expansion.expansionEnabled = True
    assert expansion.expansionValid
    assert expansion.expansionResults


def test_the_expansion_turn_follows_the_shared_gamma(expansion):
    expansion.expansionEnabled = True
    expansion.expansionMach = 2.0
    expansion.expansionTurn = 10.0
    before = next(r["raw"] for r in expansion.expansionResults if r["key"] == "mach2")
    expansion.gamma = 1.2
    after = next(r["raw"] for r in expansion.expansionResults if r["key"] == "mach2")
    assert after != before


def test_a_turn_past_the_maximum_clears_the_expansion_readout(expansion):
    expansion.expansionEnabled = True
    expansion.expansionTurn = 200.0
    assert expansion.expansionValid is False
    assert expansion.expansionResults == []
    assert "maximum expansion" in expansion.expansionMessage


# ===========================================================================
# Oblique shock
# ===========================================================================


def test_oblique_opens_computed(oblique):
    assert oblique.valid
    assert oblique.results
    assert oblique.tableRowCount > 0
    assert oblique.statusLabel == "Attached"


def test_oblique_readout_matches_the_physics(oblique):
    physics = obl.solve(2.0, math.radians(10.0), AIR).unwrap()
    assert value_of(oblique, "beta")["raw"] == pytest.approx(
        math.degrees(physics.beta), rel=1e-13)
    assert value_of(oblique, "mach2")["raw"] == pytest.approx(physics.mach2, rel=1e-15)
    assert value_of(oblique, "pressure_ratio")["raw"] == pytest.approx(
        physics.pressure_ratio, rel=1e-15)


def test_oblique_reports_the_normal_component_so_the_reuse_is_visible(oblique):
    beta = math.radians(value_of(oblique, "beta")["raw"])
    assert value_of(oblique, "mach_normal1")["raw"] == pytest.approx(
        2.0 * math.sin(beta), rel=1e-12)


def test_oblique_publishes_the_three_limiting_angles(oblique):
    limits = oblique.limits
    assert limits["machAngle"] == pytest.approx(30.0, abs=1e-9)
    assert limits["thetaMax"] == pytest.approx(22.97353176, abs=5e-8)
    assert limits["betaSonic"] < limits["betaAtThetaMax"]


def test_the_diagram_comes_from_the_same_controller(oblique):
    curve = oblique.curve()
    assert curve["weak"] and curve["strong"]
    assert curve["thetaMax"] == pytest.approx(oblique.limits["thetaMax"], rel=1e-12)
    assert curve["mach1"] == pytest.approx(oblique.mach1)


def test_the_operating_point_sits_on_the_solved_branch(oblique):
    point = oblique.operatingPoint
    assert point["both"] is False
    assert point["theta"] == pytest.approx(10.0, abs=1e-9)
    assert point["beta"] == pytest.approx(value_of(oblique, "beta")["raw"], rel=1e-15)
    assert point["beta"] < oblique.curve()["betaAtThetaMax"], "on the weak branch"


def test_the_strong_branch_moves_the_operating_point(oblique):
    weak = oblique.operatingPoint["beta"]
    oblique.branch = "strong"
    strong = oblique.operatingPoint["beta"]
    assert strong > oblique.curve()["betaAtThetaMax"] > weak


def test_both_branches_mark_two_points(oblique):
    oblique.branch = "both"
    point = oblique.operatingPoint
    assert point["both"] is True
    assert point["betaWeak"] < point["betaStrong"]


def test_oblique_offers_no_invented_reference(oblique):
    """Anderson has no oblique-shock appendix; the page says so."""
    assert oblique.referenceAvailable is False
    assert "no oblique-shock table" in oblique.referenceMessage
    assert "β = 90°" in oblique.referenceMessage


def test_the_study_is_capped_and_says_so(oblique):
    oblique.tableEnd = 40.0
    oblique.regenerateTable()
    assert oblique.tableCapped is True
    assert "capped at θ_max" in oblique.tableFooter
    assert oblique.sonicRow == oblique.tableRowCount - 1


# ---------------------------------------------------------------------------
# nothing stale survives a change
# ---------------------------------------------------------------------------


def test_switching_from_deflection_to_wave_angle_removes_the_branch_control(oblique):
    """Given a wave angle there is no branch to choose, so no control appears."""
    assert oblique.branchRequired is True
    oblique.mode = "beta"
    assert oblique.branchRequired is False
    assert oblique.branchUsed == ""
    assert oblique.valid


def test_switching_mode_replaces_the_input_rather_than_reinterpreting_it(oblique):
    """A deflection of 10 degrees is not a wave angle of 10 degrees.

    Reusing the number would silently answer a different question -- and 10
    degrees is below the Mach angle, so it is not even a legal wave angle.
    """
    oblique.inputValue = 10.0
    oblique.mode = "beta"
    assert oblique.inputValue != 10.0
    assert oblique.valid


def test_a_detached_request_clears_the_previous_solution(oblique):
    """The specification's own case: no stale wave angle, no stale ratios."""
    assert oblique.valid
    previous_beta = value_of(oblique, "beta")["raw"]
    assert previous_beta > 0.0

    oblique.inputValue = 30.0
    assert oblique.detached is True
    assert oblique.valid is False
    assert oblique.results == [], "no row may survive a request with no solution"
    assert oblique.operatingPoint == {}, "and no marker may stay on the diagram"
    assert oblique.statusLabel == "Detached"
    assert "22.9735" in oblique.statusMessage

    # ...and a legal deflection brings the solution back.
    oblique.inputValue = 15.0
    assert oblique.detached is False
    assert oblique.valid
    assert value_of(oblique, "beta")["raw"] != previous_beta


def test_switching_from_both_back_to_one_branch_drops_the_other(oblique):
    oblique.branch = "both"
    assert {row["group"] for row in oblique.results} == {"Weak solution", "Strong solution"}
    oblique.branch = "weak"
    groups = {row["group"] for row in oblique.results}
    assert "Strong solution" not in groups
    assert groups == {"Geometry", "Flow", "Shock jump", "Total"}
    assert oblique.operatingPoint["both"] is False


def test_changing_the_upstream_mach_moves_the_limits_and_the_curve(oblique):
    before = oblique.limits["thetaMax"]
    before_curve = oblique.curve()["thetaMax"]
    oblique.mach1 = 4.0
    assert oblique.limits["thetaMax"] != before
    assert oblique.curve()["thetaMax"] == pytest.approx(oblique.limits["thetaMax"], rel=1e-12)
    assert oblique.curve()["thetaMax"] != before_curve


def test_changing_gamma_recomputes_the_whole_result(oblique):
    before = value_of(oblique, "beta")["raw"]
    oblique.gamma = 1.2
    assert value_of(oblique, "beta")["raw"] != before
    assert oblique.limits["thetaMax"] == pytest.approx(26.79177125, abs=5e-8)


def test_a_refused_study_range_clears_the_table(oblique):
    assert oblique.tableRowCount > 0
    oblique.tableStep = 0.0
    oblique.regenerateTable()
    assert oblique.tableRowCount == 0
    assert "Step" in oblique.tableMessage
    assert oblique.chartSeries("beta") == []

    oblique.tableStep = 1.0
    oblique.regenerateTable()
    assert oblique.tableRowCount > 0
    assert oblique.tableMessage == ""


def test_regenerating_the_study_drops_the_previous_selection(oblique):
    oblique.selectRow(3)
    assert oblique.selectedRow == 3
    oblique.regenerateTable()
    assert oblique.selectedRow == -1


def test_switching_the_pm_mode_replaces_the_input(expansion):
    expansion.setMachAndSolve(3.0)
    assert expansion.inputValue == 3.0
    expansion.mode = "nu"
    assert expansion.inputValue != 3.0
    assert expansion.valid


def test_an_invalid_pm_input_keeps_the_reading_but_marks_it_stale(expansion):
    expansion.setMachAndSolve(2.0)
    assert expansion.valid and not expansion.stale
    expansion.inputValue = 0.5
    assert not expansion.valid
    assert expansion.stale
    assert expansion.results == []
    assert "supersonic" in expansion.statusMessage


def test_the_pm_reference_panel_follows_the_current_mach(expansion):
    """The stale-reference bug from an earlier phase, guarded here.

    The comparison must belong to the Mach number on screen, not to whichever
    one was last looked up.
    """
    expansion.setMachAndSolve(2.0)
    first = expansion.comparisonForCurrentMach()
    assert first and first[0]["reference"].startswith("26.38")

    expansion.setMachAndSolve(3.0)
    second = expansion.comparisonForCurrentMach()
    assert second and second[0]["reference"].startswith("49.76")

    expansion.setMachAndSolve(2.005)      # not a printed row
    assert expansion.comparisonForCurrentMach() == []


def test_the_pm_table_and_charts_read_the_same_block(expansion):
    series = expansion.chartSeries("nu")
    keys = [c["key"] for c in expansion.tableColumns]
    column = keys.index("nu")
    values = expansion.tableModel.values
    by_mach = {round(float(values[r, 0]), 9): float(values[r, column])
               for r in range(values.shape[0])}
    for point in series:
        assert by_mach[round(point["x"], 9)] == pytest.approx(point["y"])


# ---------------------------------------------------------------------------
# the earlier modules must not have regressed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("controller_class", [
    PrandtlMeyerController, ObliqueShockController,
    IsentropicController, MassFlowController, NormalShockController,
])
def test_every_property_has_a_usable_notify_signal(qt_app, controller_class):
    """Regression for a segfault, not a wrong answer.

    A property whose notify index points outside its own metaobject crashes
    the process the first time QML binds to it.
    """
    meta = controller_class.staticMetaObject
    for index in range(meta.propertyOffset(), meta.propertyCount()):
        prop = meta.property(index)
        if prop.isConstant():
            continue
        assert prop.hasNotifySignal(), prop.name()
        signal_index = prop.notifySignalIndex()
        assert 0 <= signal_index < meta.methodCount(), (prop.name(), signal_index)
        assert meta.method(signal_index).name().data()


@pytest.mark.parametrize("controller_class", [PrandtlMeyerController, ObliqueShockController])
def test_controllers_declare_their_own_signals(qt_app, controller_class):
    for name in ("resultsChanged", "inputsChanged", "tableChanged",
                 "tableSettingsChanged", "referenceChanged"):
        assert name in vars(controller_class), (
            f"{controller_class.__name__} must declare {name} itself")


def test_the_isentropic_page_still_works(qt_app):
    controller = IsentropicController()
    controller.mode = "area_ratio"
    controller.branch = "both"
    controller.inputValue = 2.0
    assert controller.valid
    assert controller.branchRequired is True
    assert len(controller.bothBranches) == 2

    controller.setMachAndSolve(2.0)
    assert controller.branchRequired is False
    assert controller.bothBranches == []
    for row in controller.results:
        if row["key"] == "area_ratio":
            assert row["raw"] == pytest.approx(1.6875, rel=1e-9)
            break
    else:
        raise AssertionError("A/A* missing from the isentropic readout")


def test_the_mass_flow_page_still_works(qt_app):
    controller = MassFlowController()
    assert controller.valid
    assert controller.tableRowCount > 0
    assert controller.chokingCheck["choked"] is True


def test_the_normal_shock_page_still_works(qt_app):
    controller = NormalShockController()
    assert controller.valid
    controller.compareEnabled = True
    assert controller.comparisonSummary["review"] == 0


def test_the_oblique_shock_reproduces_the_published_normal_shock(qt_app):
    """The cross-module claim the Oblique page makes about itself, checked.

    Its reference message says that at beta = 90 degrees RocketForge
    reproduces the published normal-shock values. This asserts it end to end,
    through the controller, against the Appendix B dataset.
    """
    from rocketforge.application.analysis import reference_comparison as rc

    controller = ObliqueShockController()
    controller.mach1 = 2.0
    controller.mode = "beta"
    controller.inputValue = 90.0

    normal = ns.solve(2.0, AIR)
    assert value_of(controller, "mach2")["raw"] == pytest.approx(normal.mach2, rel=1e-14)
    assert value_of(controller, "theta")["raw"] == pytest.approx(0.0, abs=1e-9)

    published = rc.compare_row(2.0, 1.4, rc.load_normal_shock_reference())
    for quantity in published.quantities:
        assert quantity.passed, quantity.key
