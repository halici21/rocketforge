"""The Normal and Oblique Shock workspaces' view state: presentation only.

The two controllers gained the Isentropic workspace's selection and table
grammar -- one shared selection, row and range readouts, table snapshots and
their restore, the settings a table was generated with -- and hold the view
data a page reads (the reference check of the solved M1, the strong-shock
limits, the attachment limits, the theta-beta-M curve and its overlays) with
the inputs it was made from. Checked here, each against what it must never do:

* a readout or a snapshot is the generated row as shown, never a recomputed
  or interpolated value; a weak-versus-strong row keeps both branches in
  their own columns, and a block is never restored onto a sweep of another
  branch, Mach number or gas;
* reading any of it solves nothing -- every test that could solve counts the
  service entry points, and each has a control proving the counter sees a
  real input change.
"""
from __future__ import annotations

import math

import pytest

from rocketforge.application.analysis import normal_shock_controller as ns_module
from rocketforge.application.analysis import oblique_shock_controller as obl_module
from rocketforge.application.analysis import reference_comparison
from rocketforge.application.analysis.normal_shock_controller import NormalShockController
from rocketforge.application.analysis.oblique_shock_controller import ObliqueShockController
from rocketforge.application.visualization.session import AnalysisSession


def _count(monkeypatch, module, names, calls: dict | None = None) -> dict:
    """Wrap ``module.<name>`` for each name; the live call counts, in ``calls`` if given."""
    calls = {} if calls is None else calls
    calls.update({name: 0 for name in names})
    for name in names:
        original = getattr(module, name)

        def counted(*a, _name=name, _original=original, **k):
            calls[_name] += 1
            return _original(*a, **k)
        monkeypatch.setattr(module, name, counted)
    return calls


def _shown(model, row):
    return [str(model.data(model.index(row, c))) for c in range(model.columnCount())]


# ============================================================== normal shock

@pytest.fixture()
def ns(qt_app):
    return NormalShockController()


def test_a_row_range_is_one_selection_read_as_shown(ns):
    model = ns.tableModel
    ns.selectTableRange(60, 20)
    sel = ns.selection
    assert sel.kind == "tableRange" and (sel.x, sel.x1) == (model.machAt(20), model.machAt(60))
    readout = ns.selectionReadout
    assert readout["title"].startswith("Rows 21–61") and readout["identity"] == ns.tableIdentity
    first, last = _shown(model, 20), _shown(model, 60)
    assert [r["value"] for r in readout["rows"]] == [f"{a}  →  {b}" for a, b in zip(first, last)]
    ns.selectTableRange(7, 7)                          # a one-row range is a row
    assert ns.selection.kind == "tableRow"


def test_a_row_readout_keeps_the_whole_shock_together(ns):
    model = ns.tableModel
    ns.selectTableRow(50)
    readout = ns.selectionReadout
    labels = [r["label"] for r in readout["rows"]]
    assert labels == [c["label"] for c in model.columns]      # M1 and every jump, in order
    assert [r["value"] for r in readout["rows"]] == _shown(model, 50)
    assert readout["stale"] is False and "γ = 1.4" in readout["note"]
    ns.selectTableRow(0)                                        # the M1 = 1 row
    assert "vanishing shock" in ns.selectionReadout["note"]


def test_a_point_off_the_generated_samples_reads_nothing(ns):
    """A chart point is read back only at an exact generated M1: no nearest-row guess."""
    mach = ns.tableModel.machAt(40)
    ns.selection.selectPoint("plotPoint", "p2_over_p1", mach, 1.0, "p2/p1", "chart")
    assert ns.selectionReadout["key"] == "40"
    ns.selection.selectPoint("plotPoint", "p2_over_p1", mach + 1e-7, 1.0, "p2/p1", "chart")
    assert ns.selectionReadout == {}
    assert ns.rowExactly(mach) == 40 and ns.rowExactly(mach + 1e-7) == -1


def test_a_snapshot_is_the_rows_as_shown_and_restores_only_onto_the_same_gas(ns):
    model = ns.tableModel
    snap = ns.tableSnapshot(80, 82)
    assert snap["kind"] == "table" and snap["source"] == "normal_shock.table"
    assert snap["rowKeys"] == [model.machAt(r) for r in (80, 81, 82)]
    assert snap["text"][0] == _shown(model, 80)
    assert snap["gamma"] == 1.4 and snap["convention"] == "anderson" and snap["stale"] is False
    assert AnalysisSession().pin(snap)
    assert ns.restorableRange(snap) == [80, 82]                 # the same table
    ns.regenerateTable()                                        # same settings, new table
    assert ns.tableIdentity != snap["identity"]
    assert ns.restorableRange(snap) == [80, 82]                 # rows at exactly its keys
    ns.tableGamma = 1.3
    ns.regenerateTable()
    assert ns.restorableRange(snap) == [], "restored onto a table of another gas"


def test_the_generated_settings_name_the_table_and_an_edit_marks_it_stale(ns):
    assert ns.tableGenerated["gamma"] == 1.4 and ns.tableStale is False
    ns.tableGamma = 1.3                                         # edited, not generated
    assert ns.tableStale is True
    assert ns.tableGenerated["gamma"] == 1.4 and ns.plottedGamma == 1.4
    assert "γ = 1.4" in ns.generatedCaption
    ns.selectTableRow(10)
    assert ns.selectionReadout["stale"] is True
    assert ns.tableSnapshot(10, 12)["stale"] is True
    ns.regenerateTable()
    assert ns.tableStale is False and ns.plottedGamma == 1.3
    assert ns.selection.kind == "", "a row of the previous table survived a new one"


def test_a_refused_table_clears_its_view_state(ns):
    ns.selectTableRow(5)
    ns.tableStart = 0.5                                         # below M1 = 1: refused
    ns.regenerateTable()
    assert ns.tableRowCount == 0 and ns.tableMessage
    assert ns.tableGenerated == {} and math.isnan(ns.plottedGamma)
    assert ns.tableStale is False and ns.generatedCaption == ""
    assert ns.selection.kind == "" and ns.tableSnapshot(0, 0) == {}


def test_the_chart_data_is_the_generated_block(ns):
    data = ns.chartData
    assert set(data) == {c["key"] for c in ns.tableModel.columns[1:]}
    assert data["p2_over_p1"] == ns.chartSeries("p2_over_p1")


def test_the_held_reference_check_is_the_slot_result(ns):
    assert ns.currentMachComparison == ns.comparisonForCurrentMach()
    assert ns.currentMachComparison and all(q["status"] == "PASS" for q in ns.currentMachComparison)
    ns.inputValue = 2.03                                        # not printed in Appendix B
    assert ns.currentMachComparison == [] == ns.comparisonForCurrentMach()


def test_row_comparisons_made_with_the_table_equal_a_fresh_comparison(ns):
    ns.compareEnabled = True
    rows = [ns.rowExactly(2.0), ns.rowExactly(3.0), ns.rowExactly(2.02)]
    assert all(r >= 0 for r in rows)
    for row in rows:
        assert ns.comparisonForRow(row) == ns._compare_row(row)
    assert ns.comparisonForRow(rows[0]) and ns.comparisonForRow(rows[2]) == []


def test_reading_the_normal_shock_view_state_solves_nothing(ns, monkeypatch):
    calls = _count(monkeypatch, ns_module, ["solve", "generate_table", "limits_for"])
    _count(monkeypatch, reference_comparison, ["compare_row"], calls)
    ns.compareEnabled = True                                    # made with the table, once
    made = dict(calls)
    for _ in range(3):
        for name in ("results", "valid", "statusLabel", "strongShockLimits",
                     "currentMachComparison", "chartData", "tableGenerated", "tableStale",
                     "plottedGamma", "generatedCaption", "selectionReadout", "tableIdentity",
                     "resultIdentity", "comparisonSummary"):
            ns.property(name)
        for row in (0, 50, 100):
            ns.comparisonForRow(row)
            ns.selectTableRow(row)
            ns.selectionReadout
        ns.selectTableRange(10, 30)
        ns.selectionReadout
        ns.tableSnapshot(10, 30)
        ns.selection.clear()
    assert calls == made, f"a view read solved: {calls} vs {made}"
    # the control: a real input change is a solve and a check
    ns.inputValue = 3.0
    assert calls["solve"] == made["solve"] + 1
    assert calls["compare_row"] == made["compare_row"] + 1
    ns.gamma = 1.3
    ns.strongShockLimits
    assert calls["limits_for"] == made["limits_for"] + 1
    ns.regenerateTable()
    assert calls["generate_table"] == made["generate_table"] + 1


def test_strong_shock_limits_still_refuse_a_bad_gamma(ns):
    """Held per gamma, but a refused gamma is not held: reading it raises as before."""
    ns.gamma = 1.0
    assert ns.valid is False
    with pytest.raises(Exception):
        ns._strong_shock_limits()
    ns.gamma = 1.4
    assert "6.000" in ns.strongShockLimits["caption"]


# ============================================================= oblique shock

@pytest.fixture()
def obl(qt_app):
    return ObliqueShockController()


def test_a_sweep_row_is_read_with_the_branch_it_was_generated_on(obl):
    model = obl.tableModel
    obl.selectTableRow(10)
    readout = obl.selectionReadout
    assert [r["value"] for r in readout["rows"]] == _shown(model, 10)
    assert "M₁ = 2" in readout["note"] and "weak branch" in readout["note"]
    obl.selectTableRow(obl.sonicRow)
    assert "merge" in obl.selectionReadout["note"]
    obl.tableBranch = "strong"
    obl.regenerateTable()
    obl.selectTableRow(10)
    assert "strong branch" in obl.selectionReadout["note"]


def test_weak_and_strong_side_by_side_stay_two_columns(obl):
    obl.tableConvention = "comparison"
    obl.regenerateTable()
    obl.selectTableRow(5)
    readout = obl.selectionReadout
    labels = [r["label"] for r in readout["rows"]]
    assert "β weak" in labels and "β strong" in labels
    values = {r["label"]: r["value"] for r in readout["rows"]}
    assert values["β weak"] != values["β strong"]
    assert "weak and strong side by side" in readout["note"]
    assert "weak and strong side by side" in obl.generatedCaption
    snap = obl.tableSnapshot(5, 6)
    assert snap["convention"] == "comparison" and "side by side" in snap["regime"]


def test_a_sweep_block_is_never_restored_onto_another_shock(obl):
    snap = obl.tableSnapshot(4, 8)
    assert snap["source"] == "oblique_shock.table" and snap["branch"] == "weak"
    assert snap["mach1"] == 2.0 and snap["regime"] == "M₁ 2 · weak branch"
    assert obl.restorableRange(snap) == [4, 8]
    obl.tableBranch = "strong"
    obl.regenerateTable()
    assert obl.restorableRange(snap) == [], "the same θ on the strong branch is another shock"
    obl.tableBranch = "weak"
    obl.tableMach1 = 3.0
    obl.regenerateTable()
    assert obl.restorableRange(snap) == [], "the same θ at another M1 is another shock"
    obl.tableMach1 = 2.0
    obl.regenerateTable()
    assert obl.restorableRange(snap) == [4, 8]


def test_the_sweep_names_its_generated_settings_and_edits_are_stale(obl):
    gen = obl.tableGenerated
    assert (gen["mach1"], gen["branch"], gen["convention"], gen["capped"]) == (2.0, "weak", "branch", True)
    obl.tableMach1 = 2.5
    assert obl.tableStale is True and obl.tableGenerated["mach1"] == 2.0
    assert "M₁ = 2 " in obl.generatedCaption
    obl.regenerateTable()
    assert obl.tableStale is False and "M₁ = 2.5" in obl.generatedCaption


def test_a_detached_request_reads_no_state(obl):
    obl.inputValue = 30.0
    assert obl.detached and obl.results == []
    obl.selection.select("state", "state", math.nan, "state", "calculator")
    assert obl.selectionReadout == {}, "a detached request was given a readout"


def test_the_held_curve_is_the_curve_and_a_refused_state_draws_nothing(obl):
    assert obl.curveData == obl.curve()
    obl.mach1 = 0.8
    assert obl.curveData == {} and obl.limits == {}
    with pytest.raises(Exception):
        obl.curve()                                             # the slot is unchanged
    obl.mach1 = 3.0
    assert obl.curveData == obl.curve() and obl.curveData["mach1"] == 3.0


def test_reading_the_oblique_shock_view_state_solves_nothing(obl, monkeypatch):
    calls = _count(monkeypatch, obl_module, ["solve", "generate_table", "limits_for", "curve_data"])
    overlays = obl.comparisonCurves                             # asked for: made once
    assert [c["mach1"] for c in overlays] == [1.5, 2.0, 3.0, 5.0]
    assert calls["curve_data"] == 4
    made = dict(calls)
    for _ in range(3):
        for name in ("results", "valid", "limits", "inputHint", "curveData", "comparisonCurves",
                     "operatingPoint", "chartData", "tableGenerated", "tableStale",
                     "generatedCaption", "selectionReadout", "resultGroups"):
            obl.property(name)
        for row in (0, 10, obl.sonicRow):
            obl.selectTableRow(row)
            obl.selectionReadout
        obl.selectTableRange(3, 9)
        obl.selectionReadout
        obl.tableSnapshot(3, 9)
        obl.selection.clear()
    assert calls == made, f"a view read solved: {calls} vs {made}"
    # the control: M1 is a real input -- one solve, one curve, one set of limits
    obl.mach1 = 2.5
    obl.curveData, obl.limits, obl.inputHint, obl.comparisonCurves
    assert calls["solve"] == made["solve"] + 1
    assert calls["curve_data"] == made["curve_data"] + 1       # overlays keep their gamma
    assert calls["limits_for"] == made["limits_for"] + 1
    obl.gamma = 1.3
    obl.comparisonCurves
    assert calls["curve_data"] == made["curve_data"] + 1 + 4    # overlays follow gamma
    obl.regenerateTable()
    assert calls["generate_table"] == made["generate_table"] + 1
