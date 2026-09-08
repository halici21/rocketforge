"""Verification of the Qt bridge: the table model and the page controller.

These need a QGuiApplication but no window and no QML, so they run in the same
headless suite as everything else. What they check is that the interface is
handed correct, complete state -- not how it looks.
"""

from __future__ import annotations

import sys

import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication

from rocketforge.application.analysis.engineering_table_model import EngineeringTableModel
from rocketforge.application.analysis.isentropic_controller import IsentropicController
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso


@pytest.fixture(scope="session")
def qt_app():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    yield app


@pytest.fixture()
def controller(qt_app):
    return IsentropicController()


# ---------------------------------------------------------------------------
# the generic table model
# ---------------------------------------------------------------------------


def test_model_reports_its_shape(qt_app):
    model = EngineeringTableModel()
    model.set_table(
        [{"key": "a", "label": "A"}, {"key": "b", "label": "B"}],
        np.array([[1.0, 2.0], [3.0, 4.0]]),
    )
    assert model.rowCount() == 2
    assert model.columnCount() == 2
    assert model.headerData(1, Qt.Horizontal, Qt.DisplayRole) == "B"


def test_model_keeps_values_numeric_and_formats_only_for_display(qt_app):
    model = EngineeringTableModel()
    model.set_table([{"key": "a", "label": "A"}], np.array([[1.23456789]]))
    index = model.index(0, 0)
    assert model.data(index, EngineeringTableModel.ValueRole) == 1.23456789
    assert model.data(index, Qt.DisplayRole) == "1.23457"
    # The stored number is untouched by the display precision.
    model.setPrecision(3)
    assert model.data(index, EngineeringTableModel.ValueRole) == 1.23456789
    assert model.data(index, Qt.DisplayRole) == "1.23"


def test_model_marks_the_special_row_and_the_regions(qt_app):
    model = EngineeringTableModel()
    model.set_table([{"key": "m", "label": "M"}],
                    np.array([[0.5], [1.0], [2.0]]),
                    marker_row=1, marker_text="SONIC")
    assert model.data(model.index(1, 0), EngineeringTableModel.MarkerRole) == "SONIC"
    assert model.data(model.index(0, 0), EngineeringTableModel.MarkerRole) == ""
    assert model.data(model.index(0, 0), EngineeringTableModel.RegionRole) == "subsonic"
    assert model.data(model.index(1, 0), EngineeringTableModel.RegionRole) == "sonic"
    assert model.data(model.index(2, 0), EngineeringTableModel.RegionRole) == "supersonic"


def test_model_out_of_range_access_is_safe(qt_app):
    model = EngineeringTableModel()
    model.set_table([{"key": "a", "label": "A"}], np.array([[1.0]]))
    assert model.data(model.index(5, 0), Qt.DisplayRole) is None
    assert np.isnan(model.machAt(5))


def test_model_row_text_is_tab_separated(qt_app):
    model = EngineeringTableModel()
    model.set_table([{"key": "a", "label": "A"}, {"key": "b", "label": "B"}],
                    np.array([[1.0, 2.0]]))
    assert model.rowAsText(0).count("\t") == 1
    assert model.headerAsText() == "A\tB"
    assert model.tableAsText().splitlines()[0] == "A\tB"


def test_model_csv_export_is_full_precision(qt_app):
    """A number rounded for the screen must not become the exported number."""
    model = EngineeringTableModel()
    model.set_table([{"key": "a", "label": "A"}], np.array([[1.234567890123456]]))
    model.setPrecision(4)
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "1.235"
    assert "1.234567890123456" in model.to_csv()


def test_model_finds_the_nearest_row(qt_app):
    model = EngineeringTableModel()
    model.set_table([{"key": "m", "label": "M"}], np.array([[0.5], [1.0], [2.0]]))
    assert model.rowNearest(0.9) == 1
    assert model.rowNearest(1.9) == 2


def test_model_is_reusable_for_any_quantity(qt_app):
    """It must carry no compressible-flow knowledge at all."""
    model = EngineeringTableModel()
    model.set_table(
        [{"key": "mach1", "label": "M₁"}, {"key": "p2_over_p1", "label": "p₂/p₁"}],
        np.array([[2.0, 4.5], [3.0, 10.333]]),
    )
    assert model.headerData(1, Qt.Horizontal, Qt.DisplayRole) == "p₂/p₁"
    assert model.rowCount() == 2


# ---------------------------------------------------------------------------
# the controller
# ---------------------------------------------------------------------------


def test_controller_publishes_computed_results(controller):
    controller.mode = "mach"
    controller.inputValue = 2.0
    controller.gamma = 1.4
    assert controller.valid
    rows = {r["key"]: r for r in controller.results}
    assert rows["mach"]["value"] == "2.00000"
    assert rows["area_ratio"]["value"] == "1.68750"
    assert rows["p0_over_p"]["raw"] == pytest.approx(7.824449, rel=1e-6)


def test_controller_offers_only_implemented_modes(controller):
    keys = {m["key"] for m in controller.solveModes}
    assert keys == {
        "mach", "p_over_p0", "p0_over_p", "T_over_T0", "T0_over_T",
        "rho_over_rho0", "rho0_over_rho", "area_ratio",
    }


def test_branch_control_appears_only_for_the_area_ratio(controller):
    controller.mode = "mach"
    assert controller.branchRequired is False
    controller.mode = "area_ratio"
    assert controller.branchRequired is True
    controller.mode = "p0_over_p"
    assert controller.branchRequired is False


def test_changing_mode_offers_a_valid_starting_value(controller):
    """Reinterpreting the previous number in the new quantity would usually be
    out of domain, so a sensible default is substituted instead."""
    controller.mode = "mach"
    controller.inputValue = 3.0
    controller.mode = "p_over_p0"
    assert 0.0 < controller.inputValue <= 1.0
    assert controller.valid


def test_invalid_input_is_reported_without_crashing(controller):
    controller.mode = "mach"
    controller.inputValue = -1.0
    assert controller.valid is False
    assert controller.results == []
    assert controller.statusLabel == "Invalid input"
    assert controller.statusMessage


def test_invalid_input_never_shows_nan(controller):
    controller.mode = "area_ratio"
    controller.branch = "subsonic"
    controller.inputValue = 0.5
    assert controller.valid is False
    assert all("nan" not in r["value"].lower() for r in controller.results)


def test_diagnostics_reach_the_interface(controller):
    controller.gamma = 2.5
    controller.mode = "mach"
    controller.inputValue = 2.0
    codes = {d["code"] for d in controller.diagnostics}
    assert "EXTRAPOLATED_GAMMA" in codes
    assert controller.valid, "an unusual gamma is a warning, not a refusal"


def test_table_is_generated_and_marks_the_sonic_row(controller):
    controller.tableGamma = 1.4
    controller.tableStart = 0.02
    controller.tableEnd = 5.0
    controller.tableStep = 0.02
    controller.regenerateTable()
    assert controller.tableRowCount == 250
    assert controller.sonicRow >= 0
    assert controller.tableModel.machAt(controller.sonicRow) == pytest.approx(1.0)


def test_table_columns_follow_the_convention(controller):
    controller.tableConvention = "anderson"
    controller.regenerateTable()
    assert [c["key"] for c in controller.tableColumns] == [
        "mach", "p0_over_p", "rho0_over_rho", "T0_over_T", "area_ratio"]
    controller.tableConvention = "standard"
    controller.regenerateTable()
    assert [c["key"] for c in controller.tableColumns] == [
        "mach", "p_over_p0", "rho_over_rho0", "T_over_T0", "area_ratio"]


def test_table_cells_match_the_physics(controller):
    controller.tableGamma = 1.3
    controller.tableStart = 0.5
    controller.tableEnd = 3.0
    controller.tableStep = 0.5
    controller.tableConvention = "anderson"
    controller.regenerateTable()
    gas = PerfectGas(gamma=1.3)
    model = controller.tableModel
    for row in range(model.rowCount()):
        mach = model.machAt(row)
        computed = model.data(model.index(row, 1), EngineeringTableModel.ValueRole)
        assert computed == pytest.approx(1.0 / float(iso.pressure_ratio(mach, gas)), rel=1e-14)


def test_invalid_table_range_clears_and_explains(controller):
    controller.tableStart = 5.0
    controller.tableEnd = 1.0
    controller.regenerateTable()
    assert controller.tableRowCount == 0
    assert controller.tableMessage


def test_row_limit_is_reported_to_the_interface(controller):
    controller.tableStart = 0.01
    controller.tableEnd = 5.0
    controller.tableStep = 1e-7
    controller.regenerateTable()
    assert controller.tableRowCount == 0
    assert "row limit" in controller.tableMessage or "rows" in controller.tableMessage


def test_reference_availability_follows_gamma(controller):
    controller.tableGamma = 1.4
    controller.regenerateTable()
    assert controller.referenceAvailable is True
    assert controller.referenceMessage == ""

    controller.tableGamma = 1.22
    controller.regenerateTable()
    assert controller.referenceAvailable is False
    assert "1.4" in controller.referenceMessage


def test_comparison_summary_is_computed_not_hardcoded(controller):
    controller.tableGamma = 1.4
    controller.tableStart = 0.02
    controller.tableEnd = 5.0
    controller.tableStep = 0.02
    controller.regenerateTable()
    controller.compareEnabled = True
    summary = controller.comparisonSummary
    assert summary["rows"] > 0
    assert summary["values"] == 4 * summary["rows"]
    assert summary["pass"] + summary["review"] == summary["values"]
    assert summary["status"] in ("PASS", "REVIEW")


def test_comparison_is_absent_until_enabled(controller):
    controller.compareEnabled = False
    assert controller.comparisonSummary == {}


def test_row_comparison_returns_nothing_for_an_untabulated_mach(controller):
    controller.tableGamma = 1.4
    controller.tableStart = 0.015
    controller.tableEnd = 0.05
    controller.tableStep = 0.007
    controller.regenerateTable()
    # 0.015, 0.022, ... none of which Anderson prints.
    assert controller.comparisonForRow(0) == []
    assert controller.hasReferenceRow(0) is False


def test_row_comparison_at_a_tabulated_mach(controller):
    controller.tableGamma = 1.4
    controller.regenerateTable()
    detail = controller.comparisonForRow(controller.sonicRow)
    assert len(detail) == 4
    assert {d["label"] for d in detail} == {"p₀/p", "ρ₀/ρ", "T₀/T", "A/A*"}
    assert all(d["status"] == "PASS" for d in detail)


def test_table_row_opens_in_the_calculator(controller):
    controller.regenerateTable()
    controller.setMachAndSolve(controller.tableModel.machAt(controller.sonicRow))
    assert controller.mode == "mach"
    assert controller.mach == pytest.approx(1.0)


def test_chart_series_comes_from_the_same_block_as_the_table(controller):
    controller.tableGamma = 1.4
    controller.tableStart = 0.5
    controller.tableEnd = 3.0
    controller.tableStep = 0.5
    controller.regenerateTable()
    series = controller.chartSeries("area_ratio")
    model = controller.tableModel
    assert len(series) == model.rowCount()
    for row, point in enumerate(series):
        assert point["x"] == pytest.approx(model.machAt(row))
        assert point["y"] == pytest.approx(
            model.data(model.index(row, 4), EngineeringTableModel.ValueRole))


def test_chart_series_for_an_unknown_quantity_is_empty(controller):
    controller.regenerateTable()
    assert controller.chartSeries("not_a_column") == []


def test_csv_export_writes_a_file(controller, tmp_path):
    controller.tableStart = 0.5
    controller.tableEnd = 2.0
    controller.tableStep = 0.5
    controller.regenerateTable()
    path = controller.exportCsv(str(tmp_path))
    assert path
    text = (tmp_path / path.split("\\")[-1]).read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("mach,")
    assert len(text.splitlines()) == controller.tableRowCount + 1


def test_assumptions_come_from_the_equation_registry(controller):
    assumptions = controller.assumptions
    assert assumptions
    assert any("perfect gas" in a.lower() for a in assumptions)
