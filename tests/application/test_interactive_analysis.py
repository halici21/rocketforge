"""The interactive analysis layer, on the real application scene.

Four things are checked here, each with a control that proves the check can
fail:

* **Linked selection.** A chart click near the throat selects the throat
  station: the drawing highlights it, the chart draws its crosshair at the
  solved throat x, and the inspector reads the solved station values -- the
  known values of the default case, digit for digit. The control offsets the
  click beyond the station tolerance and the same checker reports the
  mismatch. A table row selected on Isentropic's Table tab is the chart's
  crosshair, at that row's Mach number.
* **The analysis lens.** Entering the lens sets exactly the selected x and y
  range on the chart, the plotted data are the same objects before and after,
  the breadcrumb names the range, and reset returns to the full range. A
  pinned snapshot keeps its range when the view moves on.
* **Motion modes.** Full, Reduced and Off run the same interaction sequence --
  with a section switch interrupted by another -- and end in exactly the same
  logical state. Full animates a section switch; Off does not.
* **No solve.** Nothing above calls the nozzle or isentropic solve; a real
  input change (the control) does.

The scene runs in a fresh process (this file, run as a script), offscreen, as
in test_nozzle_view_refresh.py.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: The default Nozzle Lab case (gamma 1.4, A_e/A_t 2, p_b/p_0 0.7): its shock
#: station as the inspector must read it.
EXPECTED_SHOCK = {"A_s/A_t": "1.51009", "M_1": "1.86271", "M_2": "0.603072",
                  "p_2/p_1": "3.88131", "p_02/p_01": "0.784450"}


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
    from rocketforge.application.analysis import isentropic_controller, nozzle_controller

    solves = {"nozzle": 0, "isentropic": 0}
    for module, cls, key in ((nozzle_controller, "NozzleController", "nozzle"),
                             (isentropic_controller, "IsentropicController", "isentropic")):
        klass = getattr(module, cls)
        original = klass._recalculate

        def counted(self, _original=original, _key=key):
            solves[_key] += 1
            return _original(self)
        klass._recalculate = counted

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
                  b' property var isentropic: Isentropic; property var session: AnalysisSession }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_interactive_analysis.qml")))
    holder = probe.create()
    nav, shell, motion = (holder.property(k) for k in ("nav", "shell", "motion"))
    nozzle, isentropic, session = (holder.property(k) for k in ("nozzle", "isentropic", "session"))

    def settle(seconds=0.5):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def objs(prefix):
        return [o for o in window.findChildren(QObject)
                if o.metaObject().className().startswith(prefix)]

    def plain(value):
        return value.toVariant() if hasattr(value, "toVariant") else value

    def call(obj, name, *args):
        value = QMetaObject.invokeMethod(obj, name, Q_RETURN_ARG("QVariant"),
                                         *[Q_ARG("QVariant", a) for a in args])
        return value.toVariant() if hasattr(value, "toVariant") else value

    def layer_for(chart_name):
        for layer in objs("RFPlotInteraction"):
            chart = layer.property("chart")
            if chart is not None and chart.objectName() == chart_name:
                return layer, chart
        return None, None

    def page(key, section, wait=0.8):
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle(0.6)
        for host in objs(""):
            name = host.metaObject().className().split("_QML")[0]
            if name.endswith("Page") and host.metaObject().indexOfProperty("section") >= 0:
                host.setProperty("section", section)
        settle(wait)

    out = {"loaded": True}
    baseline = dict(solves)

    # ---- linked selection: chart -> station -> drawing, chart, inspector ----
    page("nozzlelab", 3)
    stations = {s["key"]: s for s in nozzle.property("viewport")["stations"]}
    extent = nozzle.property("viewport")["extent"]
    tolerance = 0.012 * (extent["xMax"] - extent["xMin"])
    layer, chart = layer_for("nozzleDistributionChart")

    def linked_state():
        drawing = objs("NozzleObject")
        readout = nozzle.property("selectionReadout")
        return {"kind": nozzle.property("selection").property("kind"),
                "key": nozzle.property("selection").property("key"),
                "drawing": drawing[0].property("selectedKey") if drawing else None,
                "crosshair": layer.property("selectionX"),
                "rows": {r["label"]: r["value"] for r in readout.get("rows", [])}}

    def mismatches(state, key):
        found = []
        if state["kind"] != "station" or state["key"] != key:
            found.append(f"selection is {state['kind']}:{state['key']}, not station:{key}")
        if state["drawing"] != key:
            found.append(f"the drawing highlights {state['drawing']!r}, not {key!r}")
        if state["crosshair"] != stations[key]["x"]:
            found.append(f"crosshair at {state['crosshair']}, {key} at {stations[key]['x']}")
        return found

    throat_x = stations["throat"]["x"]
    QMetaObject.invokeMethod(layer, "pointSelected", Q_ARG(float, throat_x + 0.4 * tolerance),
                             Q_ARG(float, 1.0), Q_ARG(int, 0), Q_ARG(str, "M"))
    settle(0.3)
    out["chart_to_station"] = mismatches(linked_state(), "throat")
    # control: the same click, offset past the station tolerance
    QMetaObject.invokeMethod(layer, "pointSelected", Q_ARG(float, throat_x + 3.0 * tolerance),
                             Q_ARG(float, 1.0), Q_ARG(int, 0), Q_ARG(str, "M"))
    settle(0.3)
    out["offset_control"] = mismatches(linked_state(), "throat")
    # the drawing's own click path: shock, then the inspector values
    drawing = objs("NozzleObject")[0]
    QMetaObject.invokeMethod(drawing, "stationClicked", Q_ARG(str, "shock"),
                             Q_ARG(float, stations["shock"]["x"]))
    settle(0.3)
    shock_state = linked_state()
    out["drawing_to_station"] = mismatches(shock_state, "shock")
    out["shock_rows"] = shock_state["rows"]
    out["inspector_opened"] = bool(shell.property("inspectorOpen"))
    shell.setProperty("inspectorOpen", False)
    nozzle.property("selection").clear()
    settle(0.3)

    # ---- table -> chart (Isentropic) ------------------------------------------
    page("isentropic", 2)
    isentropic.selectTableRow(7)
    settle(0.3)
    row_x = isentropic.property("selection").property("x")
    page("isentropic", 0)
    ilayer, ichart = layer_for("isentropicRelationChart")
    out["table_row"] = {"kind": isentropic.property("selection").property("kind"),
                        "x": row_x, "crosshair": ilayer.property("selectionX"),
                        "title": isentropic.property("selectionReadout").get("title")}
    isentropic.property("selection").clear()
    settle(0.2)

    # ---- the analysis lens -----------------------------------------------------
    points_before = plain(ichart.property("points"))
    full = call(ichart, "fullExtent")
    x0 = full["xmin"] + 0.30 * (full["xmax"] - full["xmin"])
    x1 = full["xmin"] + 0.55 * (full["xmax"] - full["xmin"])
    y0, y1 = full["ymin"] * 1.5, full["ymax"] * 0.5
    call(ilayer, "enterLens", x0, x1, y0, y1)
    settle(0.6)
    view = [ichart.property(k) for k in ("viewXMin", "viewXMax", "viewYMin", "viewYMax")]
    crumb = [o for o in window.findChildren(QObject, "lensBreadcrumb")
             if o.property("visible")]
    crumb_text = ""
    if crumb:
        crumb_text = " ".join(str(c.property("text")) for c in crumb[0].children()
                              if c.metaObject().indexOfProperty("text") >= 0)
    charts = objs("IsentropicCharts")[0]
    pinned = call(charts, "pinSnapshot")
    snap_before = json.dumps(session.snapshot(pinned), sort_keys=True)
    call(ilayer, "panBy", 60, 0)
    call(ilayer, "zoomAt", 400, 200, 0.6)
    settle(0.2)
    snap_after = json.dumps(session.snapshot(pinned), sort_keys=True)
    call(ilayer, "resetView", False)
    settle(0.3)
    out["lens"] = {
        "requested": [x0, x1, y0, y1], "view": view,
        "data_unchanged": plain(ichart.property("points")) == points_before
                          and len(points_before) > 10,
        "breadcrumb": crumb_text,
        "snapshot_range": json.loads(snap_before)["xRange"],
        "snapshot_unchanged": snap_before == snap_after,
        "reset_zoomed": ichart.property("zoomed"),
        "reset_lens": ilayer.property("lensActive"),
    }
    # probes: two real samples and their delta
    for fx in (0.3, 0.6):
        sample = call(ilayer, "nearestSample", ichart.property("width") * fx,
                      ichart.property("height") * 0.5)
        call(ilayer, "addProbe", sample)
    probes = ilayer.property("probes")
    probes = probes.toVariant() if hasattr(probes, "toVariant") else probes
    delta = ilayer.property("probeDelta")
    delta = delta.toVariant() if hasattr(delta, "toVariant") else delta
    out["probes"] = {"count": len(probes), "delta": delta,
                     "expected_dy": probes[1]["y"] - probes[0]["y"] if len(probes) == 2 else None}
    call(ilayer, "clearProbes")
    session.clear()
    settle(0.2)
    out["interaction_solves"] = {k: solves[k] - baseline[k] for k in solves}

    # ---- motion modes: the same sequence ends in the same state ---------------
    finals = {}
    arriving = {}
    for mode in ("full", "reduced", "off"):
        motion.setProperty("mode", mode)
        page("isentropic", 0, wait=0.5)
        host = [o for o in objs("") if o.metaObject().className().split("_QML")[0] == "IsentropicPage"][0]
        stack = [s for s in window.findChildren(QObject, "sectionStack") if s.property("visible")][0]
        host.setProperty("section", 1)
        arriving[mode] = stack.childItems()[1].opacity()      # right after the switch
        host.setProperty("section", 2)                        # interrupted by another
        settle(0.05)
        host.setProperty("section", 0)
        charts = objs("IsentropicCharts")[0]
        charts.setProperty("focusMode", True)
        ilayer, ichart = layer_for("isentropicRelationChart")
        call(ilayer, "enterLens", x0, x1, y0, y1)
        call(ilayer, "resetView", True)                       # reset during the ease
        call(ilayer, "enterLens", x0, x1, y0, y1)
        shell.setProperty("inspectorOpen", True)
        shell.setProperty("inspectorOpen", False)
        charts.setProperty("focusMode", False)
        settle(0.9)
        transitions = objs("RFSectionTransition")
        finals[mode] = {
            "section": host.property("section"),
            "sections": [round(item.opacity(), 6) for item in stack.childItems()],
            "transition_settled": all(t.property("arriving") is None and not t.property("shifted")
                                      and not t.property("running") for t in transitions),
            "view": [ichart.property(k) for k in ("viewXMin", "viewXMax", "viewYMin", "viewYMax")],
            "lens": ilayer.property("lensActive"),
            "focus": charts.property("focusMode"),
            "inspector": shell.property("inspectorOpen"),
        }
        call(ilayer, "resetView", False)
        settle(0.2)
    motion.setProperty("mode", "full")
    out["motion"] = {"finals": finals, "arriving_opacity": arriving}
    out["all_solves"] = {k: solves[k] - baseline[k] for k in solves}

    # ---- control: a real input change is a solve ------------------------------
    isentropic.setProperty("inputValue", 2.3)
    settle(0.3)
    out["control_solves"] = solves["isentropic"] - baseline["isentropic"] - out["all_solves"]["isentropic"]
    out["warnings"] = warnings
    return out


def _result() -> dict:
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve())], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
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


def test_linked_selection_maps_by_station_and_the_offset_control_is_caught():
    r = result()
    assert r["chart_to_station"] == [], r["chart_to_station"]
    assert r["offset_control"], "an offset click still read as the throat: the check is blind"
    assert r["drawing_to_station"] == [], r["drawing_to_station"]
    assert r["inspector_opened"] is True


def test_the_inspector_reads_the_known_shock_station_values():
    rows = result()["shock_rows"]
    for label, value in EXPECTED_SHOCK.items():
        assert rows.get(label) == value, (label, rows)


def test_a_table_row_is_the_charts_crosshair():
    t = result()["table_row"]
    assert t["kind"] == "tableRow" and t["crosshair"] == t["x"], t
    assert t["title"].startswith("Table row"), t


def test_the_lens_shows_exactly_the_selected_range_and_changes_no_data():
    lens = result()["lens"]
    assert lens["view"] == lens["requested"]
    assert lens["data_unchanged"] is True
    assert "(lens)" in lens["breadcrumb"] and "–" in lens["breadcrumb"], lens["breadcrumb"]
    assert lens["reset_zoomed"] is False and lens["reset_lens"] is False


def test_a_pinned_snapshot_keeps_its_range_when_the_view_moves_on():
    lens = result()["lens"]
    assert lens["snapshot_unchanged"] is True
    assert lens["snapshot_range"][0] >= lens["requested"][0] - 1e-12
    assert lens["snapshot_range"][1] <= lens["requested"][1] + 1e-12


def test_two_probes_give_the_delta_of_their_real_samples():
    p = result()["probes"]
    assert p["count"] == 2
    assert p["delta"]["dy"] == p["expected_dy"]


def test_every_motion_mode_ends_in_the_same_state_and_only_full_animates():
    m = result()["motion"]
    finals = m["finals"]
    assert finals["full"] == finals["reduced"] == finals["off"], finals
    state = finals["full"]
    assert state["section"] == 0 and state["lens"] is True and state["focus"] is False
    assert all(opacity == 1 for opacity in state["sections"]) and state["transition_settled"]
    assert m["arriving_opacity"]["full"] < 1          # a switch fades in...
    assert m["arriving_opacity"]["off"] == 1          # ...unless motion is off


def test_no_interaction_solves_and_the_control_does():
    r = result()
    assert r["interaction_solves"] == {"nozzle": 0, "isentropic": 0}
    assert r["all_solves"] == {"nozzle": 0, "isentropic": 0}
    assert r["control_solves"] >= 1
    assert r["warnings"] == [], r["warnings"]


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
