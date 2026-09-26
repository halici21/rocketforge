"""The controller side of the workspace consolidation: presentation only.

Table blocks and range selections read the generated table; the Nozzle Lab
playback reads the shock-curve samples the regime map already solved; the
inspector's operating-point reading copies the published rows; a sweep point
and a Trade design point are read from their results. None of it solves --
every test that could solve counts the solve entry points.
"""
from __future__ import annotations

import math

import pytest

from rocketforge.application.analysis import nozzle_controller as nozzle_module
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.isentropic_controller import IsentropicController
from rocketforge.application.analysis.nozzle_controller import NozzleController
from rocketforge.application.visualization import table as table_module
from rocketforge.application.visualization.session import AnalysisSession
from rocketforge.application.visualization.viewport import SAMPLE_NOTE, with_sample_shock

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(not _STATUS.usable,
                                  reason=f"NASA CEA provider unavailable ({_STATUS.status})")


# ------------------------------------------------------------ table blocks

def test_clamp_block_orders_and_bounds():
    assert table_module.clamp_block(5, 2, 10) == (2, 5)
    assert table_module.clamp_block(-3, 20, 10) == (0, 9)
    assert table_module.clamp_block(0, 0, 0) is None


def test_a_table_block_reads_values_and_text_as_given():
    values = [[1.0, 10.0], [2.0, float("nan")], [3.0, 30.0]]
    block = table_module.table_block(
        source="s", identity=4, columns=[{"key": "a", "label": "A"}, {"key": "b", "label": "B", "unit": "Pa"}],
        values=values, text_at=lambda r, c: f"t{r}{c}", first=0, last=1, key_symbol="A")
    assert block["rowKeys"] == [1.0, 2.0]
    assert block["values"] == [[1.0, 10.0], [2.0, None]]          # NaN is no value, not a number
    assert block["text"] == [["t00", "t01"], ["t10", "t11"]]
    assert block["rangeLabel"] == "A t00–t10" and block["columns"][1]["unit"] == "Pa"
    with pytest.raises(ValueError):
        table_module.table_block(source="s", identity=0, columns=[], values=[], text_at=str,
                                 first=0, last=1)


def test_block_text_is_tab_separated_with_its_header():
    text = table_module.block_text(["A", "B"], lambda r, c: f"{r}{c}", 1, 2, 2)
    assert text == "A\tB\n10\t11\n20\t21"


# ------------------------------------------------------------ isentropic

@pytest.fixture()
def iso(qt_app):
    controller = IsentropicController()
    controller.regenerateTable()
    return controller


def test_a_row_range_is_one_selection_with_both_machs(iso):
    model = iso.tableModel
    iso.selectTableRange(120, 80)
    sel = iso.selection
    assert sel.kind == "tableRange" and (sel.x, sel.x1) == (model.machAt(80), model.machAt(120))
    readout = iso.selectionReadout
    assert readout["title"].startswith("Rows 81–121")
    assert all("→" in row["value"] for row in readout["rows"])
    iso.selectTableRange(7, 7)                      # a one-row range is a row
    assert iso.selection.kind == "tableRow"


def test_a_table_snapshot_is_the_rows_as_shown_and_pins(iso):
    snap = iso.tableSnapshot(80, 82)
    assert snap["kind"] == "table" and snap["source"] == "isentropic.table"
    assert snap["rowKeys"] == [iso.tableModel.machAt(r) for r in (80, 81, 82)]
    shown = [str(iso.tableModel.data(iso.tableModel.index(80, c))) for c in range(len(snap["columns"]))]
    assert snap["text"][0] == shown
    assert AnalysisSession().pin(snap)


def test_row_exactly_never_guesses_a_nearest_row(iso):
    mach = iso.tableModel.machAt(40)
    assert iso.rowExactly(mach) == 40
    assert iso.rowExactly(mach + 1e-7) == -1


def test_a_new_table_drops_a_range(iso):
    iso.selectTableRange(10, 20)
    iso.tableGamma = 1.3
    iso.regenerateTable()
    assert iso.selection.kind == ""


# ------------------------------------------------------------ nozzle

@pytest.fixture()
def noz(qt_app, monkeypatch):
    calls = {"sweep": 0}
    original = nozzle_module.shock_position_sweep

    def counted(*a, **k):
        calls["sweep"] += 1
        return original(*a, **k)
    monkeypatch.setattr(nozzle_module, "shock_position_sweep", counted)
    controller = NozzleController()
    controller.backPressureRatio = 0.7
    controller.calls = calls
    return controller


def test_playback_samples_are_the_maps_own_sweep_and_place_its_x(noz):
    samples = noz.playbackSamples
    assert len(samples) > 10 and all(set(s) >= {"pb", "areaRatio", "x"} for s in samples)
    before = noz.calls["sweep"]
    for index in (0, len(samples) // 2, len(samples) - 1):
        noz.playbackIndex = index
        shock = [s for s in noz.playbackViewport["stations"] if s["key"] == "shock"][0]
        assert shock["x"] == samples[index]["x"]            # the solver's own x_s
        assert shock["note"] == SAMPLE_NOTE and "sample" in shock["title"]
        assert noz.selectionReadout["key"] == "playback"
    assert noz.calls["sweep"] == before, "stepping the playback re-solved the curve"
    noz.playbackIndex = 10_000
    assert noz.playbackIndex == -1 and noz.playbackViewport == noz.viewport


def test_the_operating_point_reads_with_nothing_selected(noz):
    noz.selection.clear()
    readout = noz.selectionReadout
    assert readout["title"] == f"Operating point · {noz.regimeLabel}"
    labels = {row["label"] for row in readout["rows"]}
    published = {row["label"]: row["value"] for row in noz.results}
    assert labels <= set(published)
    assert all(row["value"] == published[row["label"]] for row in readout["rows"])
    assert noz.regimeNote in readout["note"]


def test_distribution_rows_map_to_stations_and_keep_both_shock_sides(noz):
    assert noz.stationForRow(noz.throatRow) == "throat"
    assert noz.stationForRow(noz.preShockRow) == noz.stationForRow(noz.postShockRow) == "shock"
    assert noz.stationForRow(noz.exitRow) == "exit"
    assert noz.stationForRow(3) == ""
    noz.selectTableRow(noz.preShockRow)
    pre = noz.selectionReadout
    noz.selectTableRow(noz.postShockRow)
    post = noz.selectionReadout
    assert "Pre Shock" in pre["title"] and "Post Shock" in post["title"]
    assert pre["rows"] != post["rows"]
    assert noz.rowForX(noz.selection.x) == noz.preShockRow      # the shared x reads the first row


def test_a_range_across_the_shock_says_so(noz):
    noz.selectTableRange(noz.preShockRow - 3, noz.postShockRow + 3)
    readout = noz.selectionReadout
    assert readout["kind"] == "tableRange" and "crosses the shock" in readout["note"]


def test_a_new_solve_drops_a_row_but_keeps_a_station(noz):
    noz.selectTableRow(5)
    noz.backPressureRatio = 0.69
    assert noz.selection.kind == ""
    throat = [s for s in noz.viewport["stations"] if s["key"] == "throat"][0]
    noz.selection.select("station", "throat", throat["x"], "Throat", "test")
    noz.backPressureRatio = 0.68
    assert noz.selection.kind == "station"


def test_with_sample_shock_leaves_an_invalid_viewport_alone():
    invalid = {"valid": False, "stations": []}
    assert with_sample_shock(invalid, {"x": 0.1}, 0, 1) is invalid


def test_a_distribution_snapshot_keeps_both_shock_rows(noz):
    snap = noz.tableSnapshot(noz.preShockRow, noz.postShockRow)
    assert len(snap["rowKeys"]) == 2 and snap["rowKeys"][0] == snap["rowKeys"][1]
    assert snap["values"][0] != snap["values"][1]


# ------------------------------------------------------------ sweep / trade (CEA)

@requires_cea
def test_a_sweep_point_selection_is_dropped_by_any_sweep_change(qt_app):
    from rocketforge.application.analysis.thermochemistry_controller import ThermochemistryController
    thermo = ThermochemistryController()
    thermo.calculate()
    thermo.runSweep()
    thermo.selectSweepPoint(12)
    sel = thermo.sweepSelection
    assert sel.kind == "tableRow" and sel.key == "12"
    assert math.isclose(sel.x, thermo.sweepPoint(12)["of"])
    thermo.selectSweepNear(sel.x + 1e-6)
    assert thermo.sweepSelection.key == "12"            # the nearest real sample
    thermo.sweepStart = thermo.sweepStart + 0.1           # an edited input
    assert thermo.sweepSelection.kind == ""


@requires_cea
def test_a_subset_names_its_run_and_another_run_is_refused(qt_app):
    from rocketforge.application.analysis.performance_controller import RocketPerformanceController
    from rocketforge.application.analysis.thermochemistry_controller import ThermochemistryController
    from rocketforge.application.analysis.trade_study_controller import TradeStudyController
    thermo = ThermochemistryController()
    trade = TradeStudyController(thermo, RocketPerformanceController(thermo))
    trade.setVariableEnabled("oxidiser_fuel_ratio", True)
    trade.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 5)
    trade.setVariableEnabled("area_ratio", True)
    trade.setVariableRange("area_ratio", 10.0, 80.0, 2)

    def run():
        # the chunked runner, driven as the event loop would drive it
        trade.runStudy()
        guard = 0
        while trade.busy and guard < 100_000:
            trade._advance()
            guard += 1

    run()
    first = trade.subsetSnapshot([trade.pointAtRow(0), trade.pointAtRow(1)])
    assert first["kind"] == "subset" and first["runIdentity"] == "run 1"
    assert first["filter"] == {"mode": "all", "label": "All points",
                               "visible": trade.visibleRowCount, "total": trade.totalPointCount}
    assert trade.rowOfPoint(first["indices"][1]) == 1
    run()
    second = trade.subsetSnapshot([trade.pointAtRow(0)])
    assert second["runIdentity"] == "run 2"
    session = AnalysisSession()
    a, b = session.pin(first), session.pin(second)
    verdict = session.compare(a, b)
    assert verdict["compatible"] is False and "different study runs" in verdict["reason"]
    trade.setSelection([first["indices"][0], first["indices"][1], 99999])
    assert trade.selectedIndices == first["indices"]
