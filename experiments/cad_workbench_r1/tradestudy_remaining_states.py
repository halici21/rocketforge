"""Captures the remaining required Trade Study states not already covered:
empty/configure (before any evaluation), light theme at 1366x768, and a
several-thousand-point dense dataset on the Pareto tab.
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

    def settle(rounds=8, pause=0.02):
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
        b'  property int idx: Navigation.indexOfKey("tradestudy") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    thermoC = holder.property("thermoC")
    perfC = holder.property("perfC")
    study = holder.property("study")

    if not thermoC.property("providerAvailable"):
        print("no thermochemistry provider")
        return 0

    thermoC.calculate(); settle()
    perfC.calculate(); settle()
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    # -- empty / configure state (before any evaluation) -------------------
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()
    study.showTab(2)
    settle()
    window.grabWindow().save(str(OUT / "state_empty_pareto_dark_1920x1080.png"))
    print("captured: empty/configure Pareto state, hasResult =",
          study.property("hasResult"))

    # -- light theme at 1366x768 (risk check) -------------------------------
    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    window.setProperty("themeMode", "light")
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
    window.grabWindow().save(str(OUT / "state_pareto_light_1366x768.png"))
    print("captured: light 1366x768 Pareto, points =",
          study.property("visibleRowCount"))
    window.setProperty("themeMode", "dark")
    settle()

    # -- dense dataset (several thousand points) on screen ------------------
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    study.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 41)
    study.setVariableRange("area_ratio", 10.0, 80.0, 60)
    settle()
    print("planned dense points:", study.property("pointCount"))
    study.runStudy()
    for _ in range(400):
        app.processEvents()
        time.sleep(0.01)
        if not study.property("busy"):
            break
    settle(rounds=15, pause=0.03)
    study.showTab(2)
    settle(rounds=15, pause=0.03)
    window.grabWindow().save(str(OUT / "state_dense_dataset_dark_1920x1080.png"))
    print("captured: dense dataset Pareto, points =",
          study.property("visibleRowCount"))

    print(f"\n{len(messages)} Qt warnings/criticals")
    for msg in messages:
        print(" ", msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
