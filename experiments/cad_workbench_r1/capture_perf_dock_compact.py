"""Rocket Performance, at the 1366x768 floor, WITH the Analysis Dock
expanded -- the one state combination experiments/ui_visual_pilot/
capture_matrix.py structurally cannot exercise (it never touches Dock
state, because Dock state did not exist when it was written). Raised as a
real gap by rf-visual-qa during the CAD/CAE Workbench R1 shell-integration
review of Rocket Performance.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "rocket_performance"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    messages = []
    kinds = {QtMsgType.QtDebugMsg: "debug", QtMsgType.QtInfoMsg: "info",
             QtMsgType.QtWarningMsg: "warning",
             QtMsgType.QtCriticalMsg: "critical", QtMsgType.QtFatalMsg: "fatal"}

    def handler(kind, context, message):
        messages.append((kinds.get(kind, str(kind)), message))

    qInstallMessageHandler(handler)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=6, pause=0.05):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject { property var perf: RocketPerformance\n'
        b'  property var thermo: Thermochemistry\n'
        b'  property int idx: Navigation.indexOfKey("performance") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    controller = holder.property("perf")
    thermo = holder.property("thermo")
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    if not thermo.property("providerAvailable"):
        print("no chemistry provider -- cannot solve a chamber for this capture")
        return 1
    thermo.resetInputs()
    thermo.calculate()
    settle()
    controller.resetInputs()
    controller.calculate()
    settle()

    dock = None
    for c in window.findChildren(object):
        if c.metaObject().className().startswith("AnalysisDock"):
            dock = c
            break
    if dock is None:
        print("AnalysisDock not found")
        return 1

    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    settle()
    image = window.grabWindow()
    image.save(str(OUT / "performance_1366x768_dock_collapsed.png"))

    dock.setProperty("expanded", True)
    settle()
    image = window.grabWindow()
    image.save(str(OUT / "performance_1366x768_dock_expanded.png"))

    # the dock dragged to its actual, computed maximum at this window
    # height (window.height * 0.5, capped at 420 -- see AnalysisDock.qml)
    # -- the realistic worst case a real drag gesture could ever reach,
    # since the DragHandler itself clamps to maxExpandedHeight
    max_height = dock.property("maxExpandedHeight")
    dock.setProperty("expandedHeight", max_height)
    settle()
    image = window.grabWindow()
    image.save(str(OUT / "performance_1366x768_dock_expanded_tall.png"))
    print(f"dock dragged to its computed max at 1366x768: {max_height}px")

    # resize-while-open re-clamp: shrink the window further with the dock
    # still open at its (now too-large) previous maximum
    window.setProperty("height", 700)
    settle()
    reclamped = dock.property("expandedHeight")
    new_max = dock.property("maxExpandedHeight")
    print(f"after shrinking to 700px tall: expandedHeight={reclamped} "
          f"(new max {new_max}) -- {'OK, reclamped' if reclamped <= new_max + 0.01 else 'BUG: not reclamped'}")

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"3 captures, {len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
