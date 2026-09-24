"""Nozzle Lab views follow every solve -- checked on the rendered page.

The defect this guards against was found by looking: the drawing, its shock
station, the shock-position curve and the Charts guides were bound to slot
calls, which a QML binding never re-makes, so each kept an earlier solve on
screen -- once a shock drawn inside a shock-free nozzle. The controller-level
tests (test_analysis_experience_phase2.py) hold the properties to the slots;
this one holds the page to the controller, through the transitions that broke
it: shock -> no shock, no shock -> shock, a different shock station, a
different back pressure, a different nozzle.

The scene runs in a fresh process (this file, run as a script). In a shared
pytest process the full application scene and the directory-imported theme
probes of the notation tests break each other depending on their order, and a
scene that silently fails to load would turn this test into a skip.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]

TRANSITIONS = [
    ("default operating point", {}),
    ("shock -> no shock", {"backPressureRatio": 0.05}),
    ("no shock -> shock", {"backPressureRatio": 0.7}),
    ("a different shock station", {"backPressureRatio": 0.6}),
    ("a different back pressure, still shock-free", {"backPressureRatio": 0.3}),
    ("a different nozzle", {"areaRatio": 3.0, "backPressureRatio": 0.5}),
]


def _drive() -> dict:
    """Load the real scene, open Nozzle Lab, walk the transitions."""
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        # As in shell_navigation_driver.py: the offscreen platform looks for
        # fonts beside Qt, finds none, and warns; use the system fonts.
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    from PySide6.QtCore import (QCoreApplication, QEvent, QObject, QtMsgType, QUrl,
                                qInstallMessageHandler)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    warnings: list[str] = []
    qInstallMessageHandler(lambda kind, _context, message: warnings.append(str(message))
                           if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg,
                                       QtMsgType.QtFatalMsg) else None)
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    roots = engine.rootObjects()
    if not roots:
        return {"loaded": False, "warnings": warnings}
    window = roots[0]
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "analysis")
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport RocketForge 1.0\nimport "data" as Data\n'
                  b'QtObject { property var nav: Data.Navigation; property var nozzle: Nozzle }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_nozzle_refresh.qml")))
    holder = probe.create()
    nav, nozzle = holder.property("nav"), holder.property("nozzle")

    def settle():
        for _ in range(8):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            app.processEvents()

    def variant(value):
        return value.toVariant() if hasattr(value, "toVariant") else value

    def with_property(name, predicate=lambda value: True):
        return [child for child in window.findChildren(QObject)
                if child.metaObject().indexOfProperty(name) >= 0
                and predicate(child.property(name))]

    def shock(stations):
        return [round(s["value"], 12) for s in variant(stations) if s["label"] == "shock"]

    def mismatches():
        found = []
        want = shock(nozzle.markers())
        fresh_wall = [p for s in nozzle.contourSeries() if s["label"] == "wall"
                      for p in s["points"]]
        drawings = [o for o in with_property("stations")
                    if o.metaObject().className().startswith("NozzleObject")]
        if not drawings:
            found.append("no nozzle drawing is loaded")
        for drawing in drawings:
            if shock(drawing.property("stations")) != want:
                found.append(f"drawing shock {shock(drawing.property('stations'))} != {want}")
            if variant(drawing.property("wall")) != fresh_wall:
                found.append("drawing wall differs from the solved contour")

        curve = nozzle.shockPositionSeries()
        regime_charts = with_property("xLabel", lambda v: "back pressure" in str(v))
        if not regime_charts:
            found.append("no shock-position chart is loaded")
        for chart in regime_charts:
            if variant(chart.property("series"))[0]["points"] != curve:
                found.append("shock-position curve differs from a fresh sweep")

        axial = with_property("xLabel", lambda v: "axial" in str(v))
        for chart in axial:
            if shock(chart.property("guides")) != want:
                found.append(f"{chart.property('yLabel')}: guide shock differs")
        distribution = [c for c in axial if "radius" not in str(c.property("yLabel"))]
        if not distribution:
            found.append("no distribution chart is loaded")
        else:
            shown = variant(distribution[0].property("series"))
            if [s["points"] for s in shown] != [s["points"] for s in nozzle.series("mach")]:
                found.append("distribution chart differs from series('mach')")
        return found

    window.setProperty("currentPageIndex", nav.indexOfKey("nozzlelab"))
    settle()
    failures, crossed = [], []
    for name, changes in TRANSITIONS:
        for key, value in changes.items():
            nozzle.setProperty(key, value)
        settle()
        crossed.append(bool(nozzle.property("hasShock")))
        failures += [f"{name}: {message}" for message in mismatches()]
    return {"loaded": True, "failures": failures, "has_shock": crossed, "warnings": warnings}


def test_every_nozzle_view_shows_the_current_solve():
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve())], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    assert completed.returncode == 0, completed.stderr[-2000:]
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    result = json.loads(lines[-1][len("RESULT "):])
    assert result["loaded"], f"the application scene did not load: {result['warnings']}"
    assert result["failures"] == [], "\n".join(result["failures"])
    assert result["warnings"] == [], result["warnings"]
    # the walk really crossed the shock boundary both ways
    has_shock = dict(zip([name for name, _ in TRANSITIONS], result["has_shock"]))
    assert has_shock["shock -> no shock"] is False
    assert has_shock["no shock -> shock"] is True


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive()), flush=True)
