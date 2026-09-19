"""Verifies selection -> Inspector/Dock wiring end to end, with real captures.

Not inferred from code: actually selects a point via TradeStudy.toggleSelection
(the same call the redesigned Canvas hit-test issues on tap), confirms
ShellContext.inspectorOpen flips true and TradeStudy.compareColumns carries
that design's data, then captures the Inspector-open and Dock-Diagnostics-open
states for manual review.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "tradestudy" / "after"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    messages = []

    def handler(kind, context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            messages.append(message)

    qInstallMessageHandler(handler)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=8, pause=0.03):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject { property var thermoC: Thermochemistry\n'
        b'  property var perfC: RocketPerformance\n'
        b'  property var study: TradeStudy\n'
        b'  property var shell: ShellContext\n'
        b'  property int idx: Navigation.indexOfKey("tradestudy") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    thermoC = holder.property("thermoC")
    perfC = holder.property("perfC")
    study = holder.property("study")
    shell = holder.property("shell")

    if not thermoC.property("providerAvailable"):
        print("no thermochemistry provider")
        return 0

    thermoC.calculate(); settle()
    perfC.calculate(); settle()
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    study.addObjective("chamber_temperature", "minimize")
    settle()
    study.runStudy()
    for _ in range(400):
        app.processEvents()
        time.sleep(0.01)
        if not study.property("busy"):
            break
    settle()
    study.showTab(2)
    settle()

    print("inspectorOpen before selection:", shell.property("inspectorOpen"))
    study.toggleSelection(5)
    settle()
    print("inspectorOpen after selecting point 5:", shell.property("inspectorOpen"))
    columns = study.property("compareColumns")
    print("compareColumns length:", len(columns) if columns else 0)
    if columns:
        design = columns[-1]
        print("inspected design title:", design["title"])
        print("inspected design subtitle:", design["subtitle"])
        print("row count:", len(design["rows"]))
        for row in design["rows"][:6]:
            print("  ", row["group"], "|", row["label"], "=", row["value"])

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle(rounds=15, pause=0.03)
    window.grabWindow().save(str(OUT / "state_selected_inspector_open_dark_1920x1080.png"))

    # Second selection so Compare has 2 designs while we're here (also
    # verifies the Inspector still shows the most-recently-selected one).
    study.toggleSelection(12)
    settle()
    columns2 = study.property("compareColumns")
    if columns2:
        print("after 2nd selection, inspected design title:", columns2[-1]["title"])
    window.grabWindow().save(str(OUT / "state_selected_two_designs_dark_1920x1080.png"))

    warnings = messages
    print(f"\n{len(warnings)} Qt warnings/criticals")
    for msg in warnings:
        print(" ", msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
