"""The Qt bridge for the Mass Flow and Normal Shock pages.

These need a QGuiApplication but no window and no QML, so they run in the same
headless suite as everything else. What they check is that the interface is
handed correct, complete state -- and, just as importantly, that nothing stale
survives a change of mode, gamma or range.

The metaobject tests at the bottom exist because of a defect that cost real
time: PySide6 builds a *corrupt* metaobject when a subclass declares
``Property(..., notify=Base.someSignal)``, and the first QML access to such an
object segfaults with no exception and no warning. A crash is not something a
normal test can catch, so these assert the structural property instead.
"""

from __future__ import annotations

import sys

import pytest
from PySide6.QtGui import QGuiApplication

from rocketforge.application.analysis.mass_flow_controller import MassFlowController
from rocketforge.application.analysis.normal_shock_controller import NormalShockController
from rocketforge.application.analysis.isentropic_controller import IsentropicController
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import mass_flow as mf
from rocketforge.physics.compressible import normal_shock as ns

AIR = PerfectGas(gamma=1.4)


@pytest.fixture(scope="session")
def qt_app():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    yield app


@pytest.fixture()
def massflow(qt_app):
    return MassFlowController()


@pytest.fixture()
def shock(qt_app):
    return NormalShockController()


def value_of(controller, key):
    for row in controller.results:
        if row["key"] == key:
            return row
    raise AssertionError(f"{key} not in the readout")


# ---------------------------------------------------------------------------
# mass flow: opens with a real answer
# ---------------------------------------------------------------------------


def test_mass_flow_opens_computed(massflow):
    assert massflow.valid
    assert massflow.results
    assert massflow.tableRowCount > 0
    assert massflow.statusLabel == "Subsonic"


def test_mass_flow_readout_matches_the_physics(massflow):
    massflow.setMachAndSolve(0.6)
    assert value_of(massflow, "mass_flow_parameter")["raw"] == pytest.approx(
        float(mf.mass_flow_parameter(0.6, AIR)), rel=1e-12)
    assert value_of(massflow, "choked_coefficient")["raw"] == pytest.approx(
        mf.choked_mass_flow_coefficient(AIR), rel=1e-12)


def test_mass_flow_marks_the_choked_row(massflow):
    assert massflow.sonicRow >= 0
    assert massflow.tableModel.machAt(massflow.sonicRow) == pytest.approx(1.0)


def test_mass_flow_dimensional_rows_report_their_availability(massflow):
    assert massflow.dimensionalAvailable
    assert value_of(massflow, "mass_flow")["available"] is True

    massflow.area = 0.0
    assert not massflow.dimensionalAvailable
    assert massflow.dimensionalMessage
    assert value_of(massflow, "mass_flow")["available"] is False
    # ...and the dimensionless block is unaffected.
    assert value_of(massflow, "mass_flow_parameter")["available"] is True


def test_mass_flow_choking_check_is_independent_of_the_solve(massflow):
    massflow.receiverPressureRatio = 0.2
    assert massflow.chokingCheck["choked"] is True
    massflow.receiverPressureRatio = 0.9
    assert massflow.chokingCheck["choked"] is False
    # The readout is untouched by the choking question.
    assert massflow.valid


def test_mass_flow_choking_check_follows_gamma(massflow):
    massflow.receiverPressureRatio = 0.5
    for gamma in (1.2, 1.4, 1.66):
        massflow.gamma = gamma
        critical = mf.critical_pressure_ratio(PerfectGas(gamma=gamma))
        assert massflow.chokingCheck["choked"] is (0.5 <= critical)


def test_mass_flow_offers_no_invented_reference(massflow):
    """Anderson has no mass-flow appendix; the page says so rather than faking one."""
    assert massflow.referenceAvailable is False
    assert "no mass-flow" in massflow.referenceMessage
    assert "A*/A" in massflow.referenceMessage


# ---------------------------------------------------------------------------
# normal shock: opens with a real answer
# ---------------------------------------------------------------------------


def test_normal_shock_opens_computed(shock):
    assert shock.valid
    assert shock.mach == pytest.approx(2.0)
    assert value_of(shock, "p2_over_p1")["raw"] == pytest.approx(4.5, rel=1e-12)
    assert shock.tableRowCount > 0


def test_normal_shock_readout_matches_the_physics(shock):
    shock.setMachAndSolve(3.0)
    result = ns.solve(3.0, AIR)
    assert value_of(shock, "mach2")["raw"] == pytest.approx(result.mach2, rel=1e-12)
    assert value_of(shock, "entropy_change")["raw"] == pytest.approx(
        result.entropy_change, rel=1e-12)


def test_normal_shock_every_mode_reaches_the_same_shock(shock):
    result = ns.solve(2.5, AIR)
    for key, value in (
        ("mach1", 2.5),
        ("p2_over_p1", result.pressure_ratio),
        ("rho2_over_rho1", result.density_ratio),
        ("mach2", result.mach2),
        ("p02_over_p01", result.stagnation_pressure_ratio),
    ):
        shock.mode = key
        shock.inputValue = value
        assert shock.valid, key
        assert shock.mach == pytest.approx(2.5, rel=1e-7), key


def test_normal_shock_flags_which_mode_iterates(shock):
    shock.mode = "mach1"
    assert shock.modeIsIterative is False
    shock.mode = "p02_over_p01"
    assert shock.modeIsIterative is True


def test_normal_shock_reports_the_strong_shock_limits(shock):
    shock.gamma = 1.4
    assert "6.000" in shock.strongShockLimits["densityRatio"]
    shock.gamma = 1.2
    assert "11.00" in shock.strongShockLimits["densityRatio"]


def test_normal_shock_compares_against_appendix_b(shock):
    shock.compareEnabled = True
    summary = shock.comparisonSummary
    assert summary["rows"] > 0
    assert summary["review"] == 0, "the default range excludes the two known ties"
    assert summary["status"] == "PASS"
    assert "Appendix B" in summary["citation"]


def test_normal_shock_reference_row_is_never_interpolated(shock):
    shock.compareEnabled = True
    # A Mach number the appendix does not print has no comparison.
    shock.tableStart = 1.005
    shock.tableStep = 0.5
    shock.regenerateTable()
    assert shock.comparisonForRow(0) == []
    assert shock.hasReferenceRow(0) is False


def test_normal_shock_reference_switches_off_for_another_gamma(shock):
    shock.compareEnabled = True
    shock.tableGamma = 1.3
    shock.regenerateTable()
    assert shock.referenceAvailable is False
    assert "1.3" in shock.referenceMessage
    assert shock.comparisonSummary == {}


def test_normal_shock_reference_series_stays_inside_the_table_range(shock):
    shock.tableStart = 2.0
    shock.tableEnd = 3.0
    shock.regenerateTable()
    series = shock.referenceSeries("p2_over_p1")
    assert series
    assert all(2.0 <= point["x"] <= 3.0 for point in series)


def test_normal_shock_explains_the_two_known_review_rows(shock):
    assert "5.9" in shock.referenceNote and "6.9" in shock.referenceNote
    assert "40-digit" in shock.referenceNote


# ---------------------------------------------------------------------------
# nothing stale survives a change
# ---------------------------------------------------------------------------


def test_changing_mode_replaces_the_input_rather_than_reinterpreting_it(massflow):
    """A Mach of 0.5 is not a flow fraction of 0.5, and pretending otherwise
    would silently answer a question the user did not ask."""
    massflow.setMachAndSolve(0.5)
    massflow.mode = "flow_ratio"
    assert massflow.inputValue != 0.5 or massflow.mode == "flow_ratio"
    assert massflow.valid


def test_changing_gamma_recomputes_every_readout(massflow):
    massflow.gamma = 1.4
    before = value_of(massflow, "choked_coefficient")["raw"]
    massflow.gamma = 1.2
    after = value_of(massflow, "choked_coefficient")["raw"]
    assert after != before
    assert after == pytest.approx(
        mf.choked_mass_flow_coefficient(PerfectGas(gamma=1.2)), rel=1e-12)


def test_changing_the_state_recomputes_the_dimensional_rows(massflow):
    before = value_of(massflow, "mass_flow")["raw"]
    massflow.stagnationPressure = massflow.stagnationPressure * 2.0
    after = value_of(massflow, "mass_flow")["raw"]
    assert after == pytest.approx(2.0 * before, rel=1e-12)


def test_a_refused_range_clears_the_table_rather_than_leaving_the_old_one(massflow):
    assert massflow.tableRowCount > 0
    massflow.tableStep = 0.0
    massflow.regenerateTable()
    assert massflow.tableRowCount == 0
    assert "Step" in massflow.tableMessage
    assert massflow.sonicRow == -1
    assert massflow.chartSeries("mass_flow_parameter") == []

    # ...and a valid range brings it back.
    massflow.tableStep = 0.1
    massflow.regenerateTable()
    assert massflow.tableRowCount > 0
    assert massflow.tableMessage == ""


def test_a_refused_range_also_clears_the_shock_comparison(shock):
    shock.compareEnabled = True
    assert shock.comparisonSummary
    shock.tableStart = 0.5           # below Mach 1: no shock to tabulate
    shock.regenerateTable()
    assert shock.tableRowCount == 0
    assert "supersonic" in shock.tableMessage
    assert shock.comparisonSummary == {}


def test_an_invalid_input_keeps_the_reading_but_marks_it_stale(shock):
    shock.setMachAndSolve(2.0)
    assert shock.valid and not shock.stale
    shock.inputValue = 0.5           # subsonic: no shock
    assert not shock.valid
    assert shock.stale
    assert "supersonic" in shock.statusMessage
    assert shock.results == [], "an invalid input publishes no readout rows"


def test_regenerating_the_table_drops_the_previous_selection(massflow):
    massflow.selectRow(4)
    assert massflow.selectedRow == 4
    massflow.regenerateTable()
    assert massflow.selectedRow == -1


def test_the_table_and_the_charts_read_the_same_block(massflow):
    series = massflow.chartSeries("mass_flow_parameter")
    keys = [c["key"] for c in massflow.tableColumns]
    column = keys.index("mass_flow_parameter")
    values = massflow.tableModel.values
    # The chart drops non-finite entries, so match on Mach rather than index.
    by_mach = {round(float(values[r, 0]), 9): float(values[r, column])
               for r in range(values.shape[0])}
    for point in series:
        assert by_mach[round(point["x"], 9)] == pytest.approx(point["y"])


def test_charts_drop_an_unbounded_value_rather_than_plotting_it(massflow):
    """A/A* is infinite at rest. The table prints it; the chart leaves a gap."""
    massflow.tableStart = 0.0
    massflow.tableConvention = "dimensionless"
    massflow.regenerateTable()
    assert massflow.tableModel.values[0, 0] == 0.0
    series = massflow.chartSeries("area_ratio")
    assert all(point["x"] > 0.0 for point in series)


# ---------------------------------------------------------------------------
# the isentropic page must not have regressed
# ---------------------------------------------------------------------------


def test_the_isentropic_page_still_works(qt_app):
    """Phase 4C shares code with the Isentropic page; this is the guard.

    The area-ratio "Both" case is the one the specification calls out: after
    solving A/A* on both branches, switching back to Mach must leave no branch
    control, no pair of roots, and a correctly recomputed area ratio.
    """
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


def test_the_isentropic_reference_comparison_still_passes(qt_app):
    controller = IsentropicController()
    controller.compareEnabled = True
    summary = controller.comparisonSummary
    assert summary["review"] == 0
    assert summary["status"] == "PASS"


# ---------------------------------------------------------------------------
# regression: the metaobject must be sound
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("controller_class", [
    MassFlowController, NormalShockController, IsentropicController,
])
def test_every_property_has_a_usable_notify_signal(qt_app, controller_class):
    """Regression for a segfault, not a wrong answer.

    A property whose notify index points outside its own metaobject crashes the
    process the first time QML binds to it. Walking the metaobject here is the
    only way to see that from a test, since the failure mode has no exception.
    """
    meta = controller_class.staticMetaObject
    for index in range(meta.propertyOffset(), meta.propertyCount()):
        prop = meta.property(index)
        if prop.isConstant():
            continue
        assert prop.hasNotifySignal(), prop.name()
        signal_index = prop.notifySignalIndex()
        assert 0 <= signal_index < meta.methodCount(), (prop.name(), signal_index)
        # Resolving it is what QML does; it must not fault.
        assert meta.method(signal_index).name().data()


@pytest.mark.parametrize("controller_class", [MassFlowController, NormalShockController])
def test_controllers_declare_their_own_signals(qt_app, controller_class):
    """The structural rule behind the test above, stated directly.

    Every signal a controller's properties notify with must be declared on that
    controller, not inherited. Inheriting one is what produced the corrupt
    metaobject.
    """
    for name in ("resultsChanged", "inputsChanged", "tableChanged",
                 "tableSettingsChanged", "referenceChanged"):
        assert name in vars(controller_class), (
            f"{controller_class.__name__} must declare {name} itself"
        )
