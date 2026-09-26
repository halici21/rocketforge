"""Workspace consolidation, on the real application scene.

The shared workspace grammar -- input drawer, inspector that pushes the
workspace, bottom drawer, focus overlay, interactive table, plot peek/focus --
and the migrated workspaces that use it, checked for what they must do and
for what they must never do:

* **Isentropic.** The calculator's input drawer names the case when closed;
  the Anderson summary counts a failing row as a failure (control: a failing
  row set is summarised as failing). The table's row is the chart's exact
  crosshair; a row range is an interval on the chart and never zooms it; the
  lens shows exactly the range and names it; visual zoom changes row height,
  never a value; a pinned table block holds the rows exactly as shown.
* **Nozzle Lab.** A distribution row that is a station lights that station;
  the two shock rows stay two readouts; a jump selects, opens the inspector
  and scrolls; nothing selected reads the operating point; playback of the
  cached shock-curve samples solves nothing and places the sample's own x_s.
* **Shell.** The open inspector pushes the workspace (no scrim).
* **Thermochemistry sweep and Trade Study** (with the CEA provider): a sweep
  point selected on a plot or the table is the one selection the inspector
  reads; focus rebuilds the same series and species isolation is
  presentation only; the Trade results table shows every visible row (the
  empty-table regression), a row selects its design point, the filter drawer
  counts what is visible, and a subset of another run is refused.
* **No view solves.** Every interaction above runs without one call to the
  nozzle, isentropic, sweep or study solve paths; a real input change (the
  control) does solve.

The scene runs in a fresh process (this file, run as a script), offscreen.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import subprocess
import sys
import time

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _drive() -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    from PySide6.QtCore import (Q_ARG, Q_RETURN_ARG, QCoreApplication, QEvent, QMetaObject,
                                QObject, QtMsgType, QUrl, qInstallMessageHandler)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main
    from rocketforge.application.analysis import (isentropic_controller, nozzle_controller,
                                                  thermochemistry_controller,
                                                  trade_study_controller)
    from rocketforge.application.analysis import thermochemistry_provider as gateway

    solves = {"nozzle": 0, "isentropic": 0, "shock_sweep": 0, "sweep": 0, "study": 0,
              "reanalyse": 0, "thermo": 0}

    def count(klass, name, key):
        original = getattr(klass, name)

        def counted(self, *a, _original=original, **k):
            solves[key] += 1
            return _original(self, *a, **k)
        setattr(klass, name, counted)

    count(nozzle_controller.NozzleController, "_recalculate", "nozzle")
    count(isentropic_controller.IsentropicController, "_recalculate", "isentropic")
    original_sweep = nozzle_controller.shock_position_sweep

    def counted_sweep(*a, **k):
        solves["shock_sweep"] += 1
        return original_sweep(*a, **k)
    nozzle_controller.shock_position_sweep = counted_sweep
    thermo_cls = thermochemistry_controller.ThermochemistryController
    original_run = thermo_cls.runSweep
    original_calc = thermo_cls.calculate
    trade_service = trade_study_controller.service
    original_reanalyse = trade_service.reanalyse

    def counted_reanalyse(*a, **k):
        solves["reanalyse"] += 1
        return original_reanalyse(*a, **k)
    trade_service.reanalyse = counted_reanalyse

    warnings: list[str] = []
    qInstallMessageHandler(lambda kind, _c, message: warnings.append(str(message))
                           if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg,
                                       QtMsgType.QtFatalMsg) else None)
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    if not engine.rootObjects():
        return {"loaded": False, "warnings": warnings}
    window = engine.rootObjects()[0]
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "analysis")
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport RocketForge 1.0\nimport "data" as D\nimport "theme"\n'
                  b'QtObject { property var nav: D.Navigation; property var shell: D.ShellContext;'
                  b' property var motion: Motion; property var nozzle: Nozzle;'
                  b' property var isentropic: Isentropic; property var session: AnalysisSession;'
                  b' property var thermo: Thermochemistry; property var trade: TradeStudy }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_workspace_consolidation.qml")))
    holder = probe.create()
    nav, shell, motion = (holder.property(k) for k in ("nav", "shell", "motion"))
    nozzle, isentropic, session = (holder.property(k) for k in ("nozzle", "isentropic", "session"))
    thermo, trade = holder.property("thermo"), holder.property("trade")

    def settle(seconds=0.4):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def objs(prefix):
        return [o for o in window.findChildren(QObject)
                if o.metaObject().className().startswith(prefix)]

    def named(name):
        found = window.findChildren(QObject, name)
        return found[0] if found else None

    def call(obj, name, *args):
        value = QMetaObject.invokeMethod(obj, name, Q_RETURN_ARG("QVariant"),
                                         *[Q_ARG("QVariant", a) for a in args])
        return value.toVariant() if hasattr(value, "toVariant") else value

    def call_void(obj, name, *args):
        QMetaObject.invokeMethod(obj, name, *[Q_ARG("QVariant", a) for a in args])

    def emit_row(obj, name, row):
        QMetaObject.invokeMethod(obj, name, Q_ARG("int", int(row)))

    def page(key, section, wait=0.8):
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle(0.6)
        for host in objs(""):
            name = host.metaObject().className().split("_QML")[0]
            if name.endswith("Page") and host.metaObject().indexOfProperty("section") >= 0:
                host.setProperty("section", section)
        settle(wait)

    # Repeater delegates have a visual parent but no QObject parent, so
    # findChildren misses them: walk the visual tree instead.
    def visual(item):
        out = []
        stack = [item]
        while stack:
            node = stack.pop()
            for child in node.childItems():
                out.append(child)
                stack.append(child)
        return out

    def table_rows(tbl, visible_only=True):
        return [o for o in visual(tbl) if o.property("isSelected") is not None
                and (o.isVisible() if visible_only else True)]

    def page_item(prefix):
        for o in objs(prefix):
            return o
        return None

    def layer_for(chart_name):
        for layer in objs("RFPlotInteraction"):
            chart = layer.property("chart")
            if chart is not None and chart.objectName() == chart_name:
                return layer, chart
        return None, None

    out: dict = {"loaded": True}
    baseline = dict(solves)

    # ================= Isentropic calculator ===============================
    page("isentropic", 1)
    drawer = named("isentropicInputDrawer")
    out["calc_drawer_summary"] = drawer.property("summary")
    drawer.setProperty("open", False)
    settle(0.3)
    handle = named("workspaceDrawerHandle")
    out["calc_drawer_handle_visible"] = bool(handle is not None and handle.property("visible"))
    drawer.setProperty("open", True)
    settle(0.3)
    calc = page_item("IsentropicCalculator")
    out["calc_check_summary"] = calc.property("checkSummary")
    out["calc_check_failing"] = call(calc, "summarizeCheck",
                                     [{"status": "PASS"}, {"status": "REVIEW"}, {"status": "PASS"}])
    out["calc_check_none"] = call(calc, "summarizeCheck", [])
    families = [o for o in visual(calc) if o.objectName().startswith("isentropicFamily_")]
    out["calc_families"] = sorted(o.objectName() for o in families)
    out["calc_other_rows"] = len(calc.property("otherRows").toVariant()
                                 if hasattr(calc.property("otherRows"), "toVariant")
                                 else calc.property("otherRows"))

    # ================= Isentropic table ====================================
    page("isentropic", 2)
    table = named("isentropicTable")
    model = isentropic.property("tableModel")
    mach = model.machAt
    emit_row(table, "rowClicked", 40)
    settle(0.3)
    sel = isentropic.property("selection")
    out["row_selection"] = [sel.property("kind"), sel.property("x"), mach(40)]
    page("isentropic", 0)
    layer, chart = layer_for("isentropicRelationChart")
    out["row_is_crosshair"] = layer is not None and layer.property("selectionX") == mach(40)
    page("isentropic", 2)
    table = named("isentropicTable")
    call_void(table, "selectRange", 80, 120)
    settle(0.3)
    out["range_selection"] = [sel.property("kind"), sel.property("x"), sel.property("x1"),
                              mach(80), mach(120)]
    page("isentropic", 0)
    layer, chart = layer_for("isentropicRelationChart")
    out["range_on_chart"] = {"h0": layer.property("highlightX0"), "h1": layer.property("highlightX1"),
                             "selectionX_nan": math.isnan(layer.property("selectionX")),
                             "zoomed": chart.property("zoomed")}
    page("isentropic", 2)
    table = named("isentropicTable")
    call_void(table, "selectRange", 80, 120)
    before_text = call(table, "cellText", 100, 1)
    call_void(table, "enterLens", 80, 120)
    settle(0.5)
    built_in_lens = table_rows(table)
    crumb = named("tableBreadcrumb")
    crumb_text = " ".join(str(t.property("text")) for t in crumb.findChildren(QObject)
                          if t.metaObject().indexOfProperty("text") >= 0) if crumb else ""
    # The table is virtualized: it shows `shownRows` and builds only the rows
    # in view, each one reading its own model row.
    out["lens"] = {"shown_rows": table.property("shownRows"), "breadcrumb": crumb_text,
                   "active": table.property("lensActive"),
                   "built": len(built_in_lens),
                   "built_rows": sorted(int(o.property("row")) for o in built_in_lens)}
    call_void(table, "setZoom", 1.4)
    settle(0.3)
    out["zoom"] = {"row_height": table.property("effRowHeight"), "zoom": table.property("zoom"),
                   "value_unchanged": call(table, "cellText", 100, 1) == before_text}
    call_void(table, "exitLens")
    call_void(table, "setZoom", 1.0)
    settle(0.3)
    out["lens_exit_rows"] = table.property("shownRows")
    out["built_full"] = len(table_rows(table))
    snap = isentropic.tableSnapshot(80, 82)
    sid = session.pin(snap)
    kept = session.snapshot(sid)
    out["table_snapshot"] = {"id": sid, "kind": kept.get("kind"), "rows": len(kept.get("rowKeys", [])),
                             "keys": kept.get("rowKeys"), "machs": [mach(80), mach(81), mach(82)],
                             "text0": kept.get("text", [[]])[0],
                             "shown0": [call(table, "cellText", 80, c) for c in range(len(kept["columns"]))]}

    # ================= Nozzle Lab ==========================================
    page("nozzlelab", 2)
    dist = page_item("NozzleDistribution")
    ntable = named("nozzleDistributionTable")
    throat, pre, post = (nozzle.property(k) for k in ("throatRow", "preShockRow", "postShockRow"))
    emit_row(ntable, "rowClicked", throat)
    settle(0.3)
    links = [o for o in objs("NozzleLinks")]
    out["nozzle_row_station"] = {
        "kind": nozzle.property("selection").property("kind"),
        "highlight": [l.property("highlightStation") for l in links],
        "title": (nozzle.property("selectionReadout") or {}).get("title", ""),
        "inspector": shell.property("inspectorOpen")}
    readouts = {}
    for label, row in (("pre", pre), ("post", post)):
        emit_row(ntable, "rowClicked", row)
        settle(0.2)
        r = nozzle.property("selectionReadout")
        readouts[label] = {"title": r.get("title"), "M": next((x["value"] for x in r["rows"] if x["label"] == "M"), None),
                           "highlight": [l.property("highlightStation") for l in objs("NozzleLinks")]}
    out["shock_rows"] = readouts
    shell.setProperty("inspectorOpen", False)
    settle(0.2)
    call_void(dist, "jumpTo", pre)
    settle(0.5)
    body = [o for o in ntable.findChildren(QObject)
            if o.metaObject().className().startswith("QQuickListView")][0]
    out["jump"] = {"key": nozzle.property("selection").property("key"),
                   "inspector": shell.property("inspectorOpen"), "contentY": body.property("contentY")}
    # the inspector pushes the workspace
    workspace_row = named("analysisWorkspaceRow")
    out["inspector_push"] = (workspace_row is not None and workspace_row.width()
                             < window.property("width") - 300)
    scrims = [o for o in objs("InspectorDrawer")[0].children()
              if o.metaObject().className().startswith("QQuickMouseArea")]
    out["inspector_scrims"] = len(scrims)
    nozzle.property("selection").clear()
    settle(0.2)
    out["operating_readout"] = (nozzle.property("selectionReadout") or {}).get("title", "")
    # playback: cached samples, no solve
    page("nozzlelab", 0)
    before = dict(solves)
    samples = nozzle.property("playbackSamples")
    sample_x = []
    for i in (0, 10, len(samples) - 1):
        nozzle.setProperty("playbackIndex", i)
        settle(0.15)
        vp = nozzle.property("playbackViewport")
        shock = [s for s in vp["stations"] if s["key"] == "shock"][0]
        sample_x.append([shock["x"], samples[i]["x"], "sample" in shock["title"]])
    regimes = page_item("NozzleRegimes")
    call_void(regimes, "play")
    settle(0.6)
    out["playback"] = {"samples": len(samples), "placed": sample_x,
                       "readout": (nozzle.property("selectionReadout") or {}).get("title", ""),
                       "advanced": nozzle.property("playbackIndex") > 0,
                       "solves": {k: solves[k] - before[k] for k in solves}}
    call_void(regimes, "stopPlayback")
    settle(0.2)
    out["playback_stopped"] = nozzle.property("playbackIndex")
    # 3D is not asserted offscreen (software renderer); the view switch exists
    out["view_switch"] = named("nozzleViewSwitch") is not None

    out["view_solves"] = {k: solves[k] - baseline[k] for k in solves}

    # ---- the control: a real input change solves -----------------------
    before = dict(solves)
    nozzle.setProperty("backPressureRatio", 0.72)
    settle(0.3)
    out["control_solves"] = solves["nozzle"] - before["nozzle"]
    out["row_selection_dropped_on_solve"] = nozzle.property("selection").property("kind")

    # ================= Thermochemistry sweep and Trade (CEA) ==============
    out["cea"] = bool(gateway.availability().usable)
    if out["cea"]:
        page("thermochem", 0)
        thermo.calculate()
        settle(0.8)
        page("thermochem", 2)
        thermo.runSweep()
        settle(1.2)
        view_before = dict(solves)
        runs_before = thermo.property("sweepSolvedCount")
        thermo.selectSweepPoint(12)
        settle(0.3)
        ssel = thermo.property("sweepSelection")
        out["sweep_selection"] = [ssel.property("kind"), ssel.property("key"),
                                  thermo.sweepPoint(12).get("of")]
        tchart = named("sweepChart_temperature")
        inner = [o for o in tchart.findChildren(QObject)
                 if o.metaObject().className().startswith("RFLineChart")][0]
        out["sweep_marker"] = {"markerX": inner.property("markerX"),
                               "regions": inner.property("markerRegions")}
        drawer = named("sweepDataDrawer")
        out["sweep_drawer_summary"] = drawer.property("summary")
        sweep_view = page_item("ThermoSweep")
        call_void(sweep_view, "openFocus", "Species vs O/F", "species")
        settle(0.8)
        fchart = named("sweepFocusChart")
        n_all = len(fchart.property("series").toVariant()) if hasattr(fchart.property("series"), "toVariant") else len(fchart.property("series"))
        focus_view = page_item("ThermoSweepFocus")
        names = [e["name"] for e in thermo.property("sweepSpeciesSeries")]
        call_void(focus_view, "toggleIsolation", names[0])
        settle(0.3)
        series_iso = fchart.property("series")
        series_iso = series_iso.toVariant() if hasattr(series_iso, "toVariant") else series_iso
        focus_view.setProperty("isolated", [])
        settle(0.3)
        series_back = fchart.property("series")
        series_back = series_back.toVariant() if hasattr(series_back, "toVariant") else series_back
        out["species_focus"] = {"all": n_all, "isolated": len(series_iso), "restored": len(series_back),
                                "result_species": len(thermo.property("sweepSpeciesSeries")),
                                "species_names": len(names)}
        overlay = named("sweepFocusOverlay")
        call_void(overlay, "hide")
        settle(0.5)
        out["sweep_view_solves"] = {"sweep_points": thermo.property("sweepSolvedCount") - runs_before}

        # ---- Trade ------------------------------------------------------
        page("tradestudy", 1)
        trade.runStudy()
        deadline = time.perf_counter() + 240
        settle(0.5)
        while time.perf_counter() < deadline and trade.property("busy"):
            settle(0.5)
        settle(0.8)
        page("tradestudy", 1)
        rtable = named("tradeResultsTable")
        built = table_rows(rtable)
        out["trade_rows"] = {"shown": rtable.property("shownRows"), "built": len(built),
                             "visible": trade.property("visibleRowCount"),
                             "total": trade.property("totalPointCount"),
                             "summary": named("tradeFilterDrawer").property("summary")}
        emit_row(rtable, "rowClicked", 14)
        settle(0.3)
        out["trade_row_select"] = {"selected": trade.property("selectedIndices"),
                                   "point": trade.pointAtRow(14),
                                   "inspector": shell.property("inspectorOpen")}
        subset = trade.subsetSnapshot([trade.pointAtRow(14), trade.pointAtRow(15)])
        sa = session.pin(subset)
        other = dict(subset, runIdentity="run 999")
        sb = session.pin(other)
        out["subset"] = {"a": sa, "b": sb, "kind": subset.get("kind"), "run": subset.get("runIdentity"),
                         "filter": subset.get("filter"), "compare": session.compare(sa, sb)}

    out["all_view_solves"] = {k: solves[k] - baseline[k] for k in solves}
    out["warnings"] = warnings
    return out


def _result() -> dict:
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve())], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    assert completed.returncode == 0, completed.stderr[-3000:]
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    result = json.loads(lines[-1][len("RESULT "):])
    assert result["loaded"], f"the application scene did not load: {result['warnings']}"
    return result


_CACHE: dict = {}


def result() -> dict:
    if not _CACHE:
        _CACHE.update(_result())
    return _CACHE


# ---------------------------------------------------------------- isentropic

def test_the_input_drawer_names_the_case_and_leaves_a_handle():
    r = result()
    assert "M = 2" in r["calc_drawer_summary"] and "γ 1.4" in r["calc_drawer_summary"]
    assert r["calc_drawer_handle_visible"]


def test_the_anderson_summary_names_a_failure_and_the_control_is_caught():
    r = result()
    assert r["calc_check_summary"] == "4/4 PASS"
    failing = r["calc_check_failing"]
    assert failing["allPass"] is False and "1 FAIL" in failing["text"], failing
    assert r["calc_check_none"]["text"] == "No exact reference row"


def test_every_ratio_family_is_shown_and_nothing_falls_to_other():
    r = result()
    assert r["calc_families"] == ["isentropicFamily_Density", "isentropicFamily_Pressure",
                                  "isentropicFamily_Temperature"]
    assert r["calc_other_rows"] == 0


def test_a_table_row_is_the_charts_exact_crosshair():
    r = result()
    kind, x, expected = r["row_selection"]
    assert kind == "tableRow" and x == expected
    assert r["row_is_crosshair"]


def test_a_row_range_is_an_interval_on_the_chart_and_never_zooms_it():
    r = result()
    kind, x0, x1, m0, m1 = r["range_selection"]
    assert kind == "tableRange" and (x0, x1) == (m0, m1)
    chart = r["range_on_chart"]
    assert (chart["h0"], chart["h1"]) == (m0, m1)
    assert chart["selectionX_nan"], "a range must not also draw a single-row crosshair"
    assert chart["zoomed"] is False, "the chart was zoomed to the range"


def test_the_lens_shows_exactly_the_range_and_names_it():
    r = result()
    lens = r["lens"]
    assert lens["active"] and lens["shown_rows"] == 41
    assert lens["built"] > 0 and all(80 <= row <= 120 for row in lens["built_rows"]), lens["built_rows"]
    assert "Full table" in lens["breadcrumb"] and "1.620" in lens["breadcrumb"]
    assert r["lens_exit_rows"] == 250
    # virtualized: far fewer rows built than the table holds
    assert 0 < r["built_full"] < 120, r["built_full"]


def test_visual_zoom_changes_the_rows_never_a_value():
    r = result()
    assert r["zoom"]["zoom"] == pytest.approx(1.4)
    assert r["zoom"]["row_height"] > 26
    assert r["zoom"]["value_unchanged"]


def test_a_pinned_table_block_holds_the_rows_exactly_as_shown():
    r = result()
    snap = r["table_snapshot"]
    assert snap["id"] and snap["kind"] == "table" and snap["rows"] == 3
    assert snap["keys"] == snap["machs"]
    assert snap["text0"] == snap["shown0"]


# ------------------------------------------------------------------ nozzle

def test_a_distribution_row_that_is_a_station_lights_that_station():
    r = result()
    n = r["nozzle_row_station"]
    assert n["kind"] == "tableRow" and "throat" in n["highlight"]
    assert "Throat" in n["title"] and n["inspector"]


def test_the_two_shock_rows_stay_two_readouts():
    r = result()
    pre, post = r["shock_rows"]["pre"], r["shock_rows"]["post"]
    assert "Pre Shock" in pre["title"] and "Post Shock" in post["title"]
    assert pre["M"] != post["M"] and float(pre["M"]) > 1.0 > float(post["M"])
    assert "shock" in pre["highlight"] and "shock" in post["highlight"]


def test_a_jump_selects_opens_the_inspector_and_scrolls():
    r = result()
    assert r["jump"]["key"].startswith("row:") and r["jump"]["inspector"]
    assert r["jump"]["contentY"] > 0


def test_the_inspector_pushes_the_workspace_without_a_scrim():
    r = result()
    assert r["inspector_push"]
    assert r["inspector_scrims"] == 0


def test_nothing_selected_reads_the_operating_point():
    assert result()["operating_readout"].startswith("Operating point")


def test_playback_places_the_cached_samples_and_solves_nothing():
    p = result()["playback"]
    assert p["samples"] > 10
    for placed, solver_x, says_sample in p["placed"]:
        assert placed == pytest.approx(solver_x, rel=0, abs=1e-12) and says_sample
    assert p["advanced"] and "sample" in p["readout"]
    assert all(v == 0 for v in p["solves"].values()), p["solves"]
    assert result()["playback_stopped"] == -1


def test_no_view_interaction_solves_and_the_control_does():
    r = result()
    assert all(v == 0 for v in r["view_solves"].values()), r["view_solves"]
    assert r["control_solves"] >= 1, "a real input change did not solve: the counter is blind"
    assert r["row_selection_dropped_on_solve"] == ""


def test_no_qml_warnings():
    assert result()["warnings"] == []


def test_the_chart_full_range_binding_shadows_no_function():
    """`readonly property var dataExtent` (the full-range binding) once shared
    its name with `function dataExtent()`. The property won, every call of the
    function threw, and the plain charts' hover readout (Mass Flow, Normal and
    Oblique Shock, Prandtl-Meyer, Fanno, Rayleigh) printed a TypeError per
    pointer move: 156 in one sweep of the pre-consolidation tree
    (acceptance/workspace_consolidation/audit/warnings_sweep_dark_PRE.json)."""
    import re
    source = (PROJECT_ROOT / "ui" / "components" / "RFLineChart.qml").read_text(encoding="utf-8")
    code = re.sub(r"//[^\n]*", "", source)
    properties = set(re.findall(r"property\s+\w+\s+(\w+)\s*:", code))
    functions = set(re.findall(r"function\s+(\w+)\s*\(", code))
    assert not properties & functions, properties & functions
    assert "dataExtent()" not in code


# ------------------------------------------------------------ sweep / trade

def _cea():
    if not result()["cea"]:
        pytest.skip("NASA CEA provider unavailable in this environment")


def test_a_sweep_point_is_the_one_selection_the_inspector_reads():
    _cea()
    r = result()
    kind, key, ratio = r["sweep_selection"]
    assert kind == "tableRow" and key == "12"
    assert r["sweep_marker"]["markerX"] == pytest.approx(ratio)
    assert r["sweep_marker"]["regions"] is False, "an O/F marker must not tint Mach regions"
    assert "41 rows" in r["sweep_drawer_summary"]


def test_species_isolation_is_presentation_only():
    _cea()
    s = result()["species_focus"]
    assert s["all"] >= s["species_names"] > 1
    assert 0 < s["isolated"] < s["all"]
    assert s["restored"] == s["all"]
    assert s["result_species"] == s["species_names"]
    assert result()["sweep_view_solves"]["sweep_points"] == 0


def test_the_trade_results_table_shows_every_visible_row():
    _cea()
    t = result()["trade_rows"]
    assert t["visible"] == t["total"] > 0
    assert t["shown"] == t["visible"], "the results table does not show every visible row"
    assert 0 < t["built"] < t["visible"], "the results table is empty (the rowCount regression) or not virtualized"
    assert f"{t['visible']} / {t['total']} visible" in t["summary"]


def test_a_trade_row_selects_its_design_point_without_evaluating():
    _cea()
    r = result()
    assert r["trade_row_select"]["point"] in r["trade_row_select"]["selected"]
    assert r["all_view_solves"]["reanalyse"] == 0


def test_a_subset_of_another_run_is_refused():
    _cea()
    s = result()["subset"]
    assert s["a"] and s["b"] and s["kind"] == "subset"
    assert s["run"].startswith("run ") and s["filter"]["mode"] == "all"
    assert s["compare"]["compatible"] is False and "different study runs" in s["compare"]["reason"]


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str))
