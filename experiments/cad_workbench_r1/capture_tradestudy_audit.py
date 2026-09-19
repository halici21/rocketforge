"""Current-state audit capture for Trade Study, before any redesign.

Drives Thermochemistry -> Rocket Performance -> Trade Study to a real,
populated, completed study (not just the empty/configure state), then
captures the required resolution/theme matrix.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "tradestudy"
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

    def settle(rounds=8, pause=0.05):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject { property var thermo: Thermochemistry\n'
        b'  property var perf: RocketPerformance\n'
        b'  property var study: TradeStudy\n'
        b'  property int idx: Navigation.indexOfKey("tradestudy") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    thermo = holder.property("thermo")
    perf = holder.property("perf")
    study = holder.property("study")

    if not thermo.property("providerAvailable"):
        print("no thermochemistry provider -- cannot populate a study")
        return 0

    thermo.calculate()
    settle()
    perf.calculate()
    settle()

    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    print("baselineAvailable:", study.property("baselineAvailable"))

    # Second objective, so a Pareto front exists (>= 2 objectives required).
    study.addObjective("chamber_temperature", "minimize")
    settle()
    print("definitionValid:", study.property("definitionValid"),
          study.property("definitionMessage"))
    print("pointCount:", study.property("pointCount"),
          "chemistrySolveCount:", study.property("chemistrySolveCount"))

    study.runStudy()
    # Chunked on a zero-interval QTimer (8 points/turn) -- pump until done.
    for _ in range(400):
        app.processEvents()
        time.sleep(0.01)
        if not study.property("busy"):
            break
    settle()
    print("hasResult:", study.property("hasResult"),
          "resultComplete:", study.property("resultComplete"),
          "visibleRowCount:", study.property("visibleRowCount"))
    print("paretoAvailable:", study.property("paretoAvailable"))

    for width, height in ((2560, 1440), (1920, 1080), (1366, 768)):
        window.setProperty("width", width)
        window.setProperty("height", height)
        settle()
        for section, name in ((0, "setup"), (1, "results"), (2, "pareto"),
                              (3, "compare")):
            study.showTab(section)
            settle()
            window.grabWindow().save(
                str(OUT / f"audit_{name}_dark_{width}x{height}.png"))

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("themeMode", "light")
    settle()
    for section, name in ((0, "setup"), (1, "results"), (2, "pareto"),
                          (3, "compare")):
        study.showTab(section)
        settle()
        window.grabWindow().save(
            str(OUT / f"audit_{name}_light_1920x1080.png"))
    window.setProperty("themeMode", "dark")

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"\n{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
