"""Table and design-point subset snapshots, and row-range selection.

The consolidation extends the one session and the one selection rather than
building parallel ones: a table block and a design-point subset are frozen,
bounded and compared by the same rules as a plot snapshot, and a comparison
across kinds -- or across study runs -- is refused with a reason.
"""
from __future__ import annotations

import math

import pytest

from rocketforge.application.visualization import plot
from rocketforge.application.visualization.selection import AnalysisSelection
from rocketforge.application.visualization.session import AnalysisSession

COLUMNS = [{"key": "mach", "label": "M", "unit": ""},
           {"key": "p0_over_p", "label": "p₀/p", "unit": ""}]


def _table(keys=(1.8, 1.9, 2.0), values=None, identity=1, columns=None, source="isentropic.table"):
    values = values or [[k, 1.0 + k] for k in keys]
    return {"kind": "table", "source": source, "identity": identity,
            "columns": columns or COLUMNS, "rowKeys": list(keys), "values": values,
            "text": [[f"{v:.4f}" for v in row] for row in values],
            "rangeLabel": f"M {keys[0]:.2f}–{keys[-1]:.2f}", "stale": False}


def _subset(indices=(3, 7), run=11, filter_mode="all", columns=None):
    return {"kind": "subset", "source": "tradestudy", "identity": run, "runIdentity": run,
            "indices": list(indices), "filter": {"mode": filter_mode, "visible": 328, "total": 328},
            "columns": columns or [{"key": "isp", "label": "Isp", "unit": "s"}],
            "rows": [[str(i)] for i in indices], "stale": False}


def _plot():
    return {"source": "isentropic", "identity": 1, "quantity": "p0_over_p",
            "quantityLabel": "p_0/p", "unit": "", "xQuantity": "mach", "xLabel": "Mach number",
            "xUnit": "", "xRange": [1.6, 2.4], "yRange": [1.0, 8.0], "axisMode": "log",
            "series": [{"label": "p_0/p", "points": [{"x": 2.0, "y": 7.8}]}], "stale": False}


@pytest.fixture()
def session(qt_app):
    return AnalysisSession()


def test_a_table_block_is_frozen_and_complete(session):
    live = _table()
    sid = session.pin(live)
    assert sid
    live["values"][0][1] = -5.0
    kept = session.snapshot(sid)
    assert kept["kind"] == "table" and kept["values"][0][1] == 2.8
    assert kept["rangeLabel"] == "M 1.80–2.00"


@pytest.mark.parametrize("broken", [
    {"rowKeys": []},
    {"values": [[1.8, 2.8]]},                          # fewer value rows than keys
    {"rowKeys": [1.8, float("nan"), 2.0]},
    {"values": [[1.8, 2.8], [1.9], [2.0, 3.0]]},       # ragged row
])
def test_a_broken_table_block_is_refused_with_a_reason(session, broken):
    snap = _table(); snap.update(broken)
    assert session.pin(snap) == "" and session.lastError


def test_a_missing_table_field_is_refused(session):
    snap = _table(); del snap["rangeLabel"]
    assert session.pin(snap) == "" and "rangeLabel" in session.lastError


def test_an_unknown_kind_is_refused(session):
    snap = _table(); snap["kind"] = "movie"
    assert session.pin(snap) == "" and "kind" in session.lastError


def test_table_delta_aligns_rows_by_engineering_key_not_position(session):
    a = session.pin(_table(keys=(1.8, 1.9, 2.0), values=[[1.8, 2.0], [1.9, 3.0], [2.0, 4.0]]))
    # B starts one row later: position 0 of B is M 1.9, not M 1.8
    b = session.pin(_table(keys=(1.9, 2.0, 2.1), values=[[1.9, 3.5], [2.0, 4.25], [2.1, 5.0]],
                           identity=2))
    d = session.tableDelta(a, b)
    assert d["compatible"] and d["matched"] == 2
    assert d["unmatchedA"] == 1 and d["unmatchedB"] == 1
    assert [r["key"] for r in d["rows"]] == [1.9, 2.0]
    assert math.isclose(d["rows"][0]["deltas"][1], 0.5)
    assert math.isclose(d["rows"][1]["deltas"][1], 0.25)


def test_tables_with_different_columns_do_not_compare(session):
    a = session.pin(_table())
    other = [{"key": "mach", "label": "M", "unit": ""}, {"key": "T0_over_T", "label": "T₀/T", "unit": ""}]
    b = session.pin(_table(columns=other, identity=2))
    verdict = session.compare(a, b)
    assert verdict["compatible"] is False and "columns" in verdict["reason"]
    assert session.tableDelta(a, b)["compatible"] is False


def test_kinds_never_compare(session):
    t = session.pin(_table())
    p = session.pin(_plot())
    s = session.pin(_subset())
    assert session.compare(t, p) == {"compatible": False, "reason": "different snapshot kinds"}
    assert session.compare(s, t)["compatible"] is False
    assert session.compareAt(t, t, 1.9)["compatible"] is False     # not a plot
    assert session.tableDelta(p, p)["compatible"] is False


def test_a_subset_records_run_filter_and_columns(session):
    sid = session.pin(_subset(filter_mode="feasible"))
    kept = session.snapshot(sid)
    assert kept["indices"] == [3, 7] and kept["runIdentity"] == 11
    assert kept["filter"]["mode"] == "feasible" and kept["columns"][0]["unit"] == "s"


def test_a_subset_from_another_run_is_refused(session):
    a = session.pin(_subset(run=11))
    b = session.pin(_subset(run=12))
    c = session.pin(_subset(run=11, indices=(1,)))
    verdict = session.compare(a, b)
    assert verdict["compatible"] is False and "different study runs" in verdict["reason"]
    assert session.compare(a, c)["compatible"] is True


@pytest.mark.parametrize("broken", [
    {"indices": []}, {"indices": [3, 3]}, {"indices": [-1, 2]}, {"rows": [["3"]]},
])
def test_a_broken_subset_is_refused(session, broken):
    snap = _subset(); snap.update(broken)
    assert session.pin(snap) == ""


def test_a_plot_snapshot_without_a_kind_is_still_a_plot(session):
    sid = session.pin(_plot())
    assert plot.snapshot_kind(session.snapshot(sid)) == "plot"


def test_a_row_range_is_one_selection_with_two_ends(qt_app):
    sel = AnalysisSelection()
    seen = []
    sel.changed.connect(lambda: seen.append(sel.kind))
    sel.selectRange("tableRange", "rows:80-120", 2.2, 1.8, "M 1.80–2.20", "table")
    assert (sel.kind, sel.x, sel.x1) == ("tableRange", 1.8, 2.2) and seen == ["tableRange"]
    sel.select("tableRow", "3", 1.9, "row 4", "table")
    assert math.isnan(sel.x1)                          # a single row carries no far end
    sel.clear()
    assert math.isnan(sel.x) and math.isnan(sel.x1)
    with pytest.raises(ValueError):
        sel.selectRange("tableRange", "k", math.nan, 1.0, "", "")


def test_rows_sharing_a_key_stay_distinct_in_a_comparison(session):
    """The pre- and post-shock rows of a distribution share x; they are matched
    occurrence by occurrence, never merged into one."""
    keys = (0.04, 0.0482, 0.0482, 0.05)
    a = session.pin(_table(keys=keys, values=[[k, v] for k, v in zip(keys, (1.0, 1.8, 0.6, 0.55))],
                           source="nozzle.distribution"))
    b = session.pin(_table(keys=keys, values=[[k, v] for k, v in zip(keys, (1.0, 1.9, 0.5, 0.55))],
                           source="nozzle.distribution", identity=2))
    d = session.tableDelta(a, b)
    assert d["matched"] == 4
    shock_rows = [r for r in d["rows"] if r["key"] == 0.0482]
    assert len(shock_rows) == 2
    assert math.isclose(shock_rows[0]["deltas"][1], 0.1) and math.isclose(shock_rows[1]["deltas"][1], -0.1)
    assert math.isclose(d["maxAbs"][1], 0.1) and d["maxAbs"][0] is None
