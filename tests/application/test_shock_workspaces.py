"""The Normal and Oblique Shock workspaces, on the real application scene.

Both workspaces now speak the Isentropic grammar: an honest header chip, a
section transition, an input drawer that names the case, a table section with
the shared toolbar, row and range selection, the lens and pinned blocks, and a
relation/sweep chart that shows the table's selection. Checked on the running
shell, each with what it must never do:

* **Honest header.** "Calculated" only for a valid result; a refused or
  detached request shows its status (control: the detached request flips it).
* **Linked selection.** A table row is the chart's crosshair at that row's
  exact key; a range is a band and never zooms the chart; the lens shows
  exactly the range.
* **No view solves.** Route entry, section switches, drawer open/close, row
  and range selection, the lens, a table scroll, a theme switch, a resize and
  navigating away and back call none of the normal- or oblique-shock service
  entry points -- solve, generate_table, limits_for, curve_data -- nor the
  reference comparison; a real input change and Generate (the controls) do.
* **No warnings** on the way.

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

OBJECT_NAMES = {
    "normalshock": ["sectionStack", "normalShockHeaderStatus", "normalShockInputDrawer",
                    "normalShockResults", "normalShockReferenceCheck", "normalShockTable",
                    "normalShockTableSettings", "normalShockTableSnapshots",
                    "normalShockTableStatus", "normalShockRelationChart"],
    "obliqueshock": ["sectionStack", "obliqueShockHeaderStatus", "obliqueShockInputDrawer",
                     "obliqueShockResults", "obliqueShockCalculatorDiagram",
                     "obliqueShockStudyDiagram", "obliqueShockSweepChart", "obliqueShockTable",
                     "obliqueShockTableSettings", "obliqueShockTableSnapshots",
                     "obliqueShockTableStatus"],
}


def _drive() -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    from PySide6.QtCore import (Q_ARG, QCoreApplication, QEvent, QMetaObject, QObject,
                                QtMsgType, QUrl, qInstallMessageHandler)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main
    from rocketforge.application.analysis import normal_shock_controller as ns_module
    from rocketforge.application.analysis import oblique_shock_controller as obl_module
    from rocketforge.application.analysis import reference_comparison

    solves: dict[str, int] = {}

    def count(module, name, key):
        original = getattr(module, name)
        solves[key] = 0

        def counted(*a, _original=original, **k):
            solves[key] += 1
            return _original(*a, **k)
        setattr(module, name, counted)

    for name in ("solve", "generate_table", "limits_for"):
        count(ns_module, name, f"normal.{name}")
    for name in ("solve", "generate_table", "limits_for", "curve_data"):
        count(obl_module, name, f"oblique.{name}")
    count(reference_comparison, "compare_row", "reference.compare_row")

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
    probe.setData(b'import QtQuick\nimport RocketForge 1.0\nimport "data" as D\n'
                  b'QtObject { property var nav: D.Navigation;'
                  b' property var normal: NormalShock; property var oblique: ObliqueShock }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_shock_workspaces.qml")))
    holder = probe.create()
    nav, normal, oblique = (holder.property(k) for k in ("nav", "normal", "oblique"))

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
        found = [o for o in window.findChildren(QObject, name)]
        visible = [o for o in found if o.property("visible") is not False]
        return (visible or found or [None])[0]

    def host():
        for o in objs(""):
            cls = o.metaObject().className().split("_QML")[0]
            if cls.endswith("ShockPage") and o.metaObject().indexOfProperty("section") >= 0:
                return o
        return None

    def page(key, section=None, wait=0.8):
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle(0.6)
        if section is not None:
            host().setProperty("section", section)
        settle(wait)

    def section(n, wait=0.5):
        host().setProperty("section", n)
        settle(wait)

    def call_void(obj, name, *args):
        QMetaObject.invokeMethod(obj, name, *[Q_ARG("QVariant", a) for a in args])

    def emit_row(obj, name, row):
        QMetaObject.invokeMethod(obj, name, Q_ARG("int", int(row)))

    def layer_for(chart_name):
        for layer in objs("RFPlotInteraction"):
            chart = layer.property("chart")
            if chart is not None and chart.objectName() == chart_name:
                return layer, chart
        return None, None

    def chip(name):
        c = named(name)
        return None if c is None else [c.property("text"), c.property("tone")]

    def scroll(table):
        views = [o for o in table.findChildren(QObject)
                 if o.metaObject().className().startswith("QQuickListView")]
        if views:
            views[0].setProperty("contentY", 400.0)
            settle(0.2)
            views[0].setProperty("contentY", 0.0)

    out: dict = {"loaded": True}
    settle(0.6)
    baseline = dict(solves)

    workspaces = (
        ("normalshock", normal, "normalShockTable", "normalShockRelationChart", 0,
         "normalShockInputDrawer", "normalShockTableSettings", "normalShockHeaderStatus"),
        ("obliqueshock", oblique, "obliqueShockTable", "obliqueShockSweepChart", 1,
         "obliqueShockInputDrawer", "obliqueShockTableSettings", "obliqueShockHeaderStatus"),
    )
    for key, ctrl, table_name, chart_name, chart_section, drawer_name, settings_name, header in workspaces:
        view: dict = {}
        page(key, 0)
        view["header"] = chip(header)
        missing = []
        for s in (0, 1, 2):
            section(s, 0.4)
            missing += [n for n in OBJECT_NAMES[key] if not window.findChildren(QObject, n)]
        view["missing_names"] = sorted(set(n for n in missing
                                           if not window.findChildren(QObject, n)))
        # the input drawer: closed over a valid result, and the reader's choice
        section(1 if key == "normalshock" else 0)
        drawer = named(drawer_name)
        view["drawer_default_open"] = drawer.property("open")
        call_void(drawer, "setOpenByUser", True)
        settle(0.3)
        view["drawer_user_open"] = drawer.property("open")
        call_void(drawer, "setOpenByUser", False)
        settle(0.3)
        # the table: a row, a range, the lens, a scroll, the settings drawer
        section(2)
        table = named(table_name)
        model = ctrl.property("tableModel")
        emit_row(table, "rowClicked", 12)
        settle(0.3)
        sel = ctrl.property("selection")
        view["row"] = [sel.property("kind"), sel.property("x"), model.machAt(12),
                       table.property("selectedRow")]
        section(chart_section)
        layer, chart = layer_for(chart_name)
        view["row_crosshair"] = layer is not None and layer.property("selectionX") == model.machAt(12)
        section(2)
        table = named(table_name)
        call_void(table, "selectRange", 5, 15)
        settle(0.3)
        view["range"] = [sel.property("kind"), sel.property("x"), sel.property("x1"),
                         model.machAt(5), model.machAt(15)]
        section(chart_section)
        layer, chart = layer_for(chart_name)
        view["range_band"] = {"h0": layer.property("highlightX0"), "h1": layer.property("highlightX1"),
                              "crosshair_nan": math.isnan(layer.property("selectionX")),
                              "zoomed": chart.property("zoomed")}
        section(2)
        table = named(table_name)
        call_void(table, "selectRange", 5, 15)
        call_void(table, "enterLens", 5, 15)
        settle(0.4)
        view["lens"] = {"active": table.property("lensActive"), "shown": table.property("shownRows")}
        scroll(table)
        call_void(table, "exitLens")
        settle(0.3)
        view["lens_exit_rows"] = [table.property("shownRows"), ctrl.property("tableRowCount")]
        settings = named(settings_name)
        settings.setProperty("open", False)
        settle(0.2)
        settings.setProperty("open", True)
        settle(0.2)
        view["readout_title"] = (ctrl.property("selectionReadout") or {}).get("title", "")
        # theme, resize, away and back
        for theme in ("light", "dark"):
            window.setProperty("themeMode", theme)
            settle(0.3)
        for w, h in ((1366, 768), (2560, 1440), (1920, 1080)):
            window.setProperty("width", w)
            window.setProperty("height", h)
            settle(0.3)
        page("home", wait=0.4)
        page(key, 2)
        table = named(table_name)
        view["after_return"] = [host() is not None, ctrl.property("selection").property("kind"),
                                table.property("rangeFirst"), table.property("rangeLast")]
        out[key] = view

    out["view_solves"] = {k: solves[k] - baseline[k] for k in solves}

    # ---- the controls: real input changes and Generate do solve ------------------
    before = dict(solves)
    page("normalshock", 1)
    normal.setProperty("inputValue", 2.5)
    settle(0.3)
    normal.regenerateTable()
    settle(0.3)
    page("obliqueshock", 0)
    oblique.setProperty("mach1", 2.5)
    settle(0.4)
    out["control_solves"] = {k: solves[k] - before[k] for k in solves}

    # ---- header honesty, with its control ----------------------------------------
    oblique.setProperty("mach1", 2.0)
    oblique.setProperty("inputValue", 30.0)
    settle(0.4)
    out["detached"] = {"header": chip("obliqueShockHeaderStatus"),
                       "drawer_open": named("obliqueShockInputDrawer").property("open"),
                       "results": len(oblique.property("results"))}
    oblique.setProperty("inputValue", 10.0)
    settle(0.4)
    out["attached_header"] = chip("obliqueShockHeaderStatus")
    page("normalshock", 1)
    normal.setProperty("inputValue", 0.5)
    settle(0.4)
    out["refused_header"] = chip("normalShockHeaderStatus")
    normal.setProperty("inputValue", 2.0)
    settle(0.3)

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


@pytest.mark.parametrize("key", ["normalshock", "obliqueshock"])
def test_the_workspace_names_its_parts_for_automation(key):
    assert result()[key]["missing_names"] == []


@pytest.mark.parametrize("key", ["normalshock", "obliqueshock"])
def test_the_header_claims_a_calculated_state_only_for_a_valid_result(key):
    assert result()[key]["header"] == ["Calculated", "success"]


def test_a_detached_or_refused_request_is_what_the_header_says():
    r = result()
    assert r["detached"]["header"] == ["Detached", "warning"]
    assert r["detached"]["results"] == 0, "a detached request kept a solution on screen"
    assert r["attached_header"] == ["Calculated", "success"]
    assert r["refused_header"][1] == "warning" and r["refused_header"][0] != "Calculated"


@pytest.mark.parametrize("key", ["normalshock", "obliqueshock"])
def test_the_input_drawer_follows_the_result_until_the_reader_chooses(key):
    v = result()[key]
    assert v["drawer_default_open"] is False, "closed over a valid result"
    assert v["drawer_user_open"] is True


def test_a_detached_request_opens_the_inputs():
    assert result()["detached"]["drawer_open"] is True


@pytest.mark.parametrize("key", ["normalshock", "obliqueshock"])
def test_a_table_row_is_the_charts_exact_crosshair(key):
    v = result()[key]
    kind, x, expected, selected = v["row"]
    assert kind == "tableRow" and x == expected and selected == 12
    assert v["row_crosshair"]


@pytest.mark.parametrize("key", ["normalshock", "obliqueshock"])
def test_a_row_range_is_a_band_and_never_zooms_the_chart(key):
    v = result()[key]
    kind, x0, x1, k0, k1 = v["range"]
    assert kind == "tableRange" and (x0, x1) == (k0, k1)
    band = v["range_band"]
    assert (band["h0"], band["h1"]) == (k0, k1)
    assert band["crosshair_nan"] and band["zoomed"] is False


@pytest.mark.parametrize("key", ["normalshock", "obliqueshock"])
def test_the_lens_shows_exactly_the_range(key):
    v = result()[key]
    assert v["lens"] == {"active": True, "shown": 11}
    shown, rows = v["lens_exit_rows"]
    assert shown == rows > 11


def test_no_view_interaction_solves():
    solves = result()["view_solves"]
    assert all(n == 0 for n in solves.values()), solves


def test_the_controls_do_solve_so_the_counter_is_not_blind():
    c = result()["control_solves"]
    assert c["normal.solve"] >= 1 and c["normal.generate_table"] == 1
    assert c["reference.compare_row"] >= 1
    assert c["oblique.solve"] >= 1 and c["oblique.curve_data"] >= 1 and c["oblique.limits_for"] >= 1


@pytest.mark.parametrize("key", ["normalshock", "obliqueshock"])
def test_coming_back_shows_the_selection_the_workspace_holds(key):
    rebuilt, kind, first, last = result()[key]["after_return"]
    assert rebuilt is True and kind == "tableRange"
    assert (first, last) == (5, 15), "the rebuilt table lost the range the chart still shows"


def test_no_qml_warnings():
    assert result()["warnings"] == []


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str))
