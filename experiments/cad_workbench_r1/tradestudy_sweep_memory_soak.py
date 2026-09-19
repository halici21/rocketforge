"""Focused memory soak for the new parametric-sweep view specifically:
mode switch (Sweep <-> Design space), response-metric add/remove,
normalization toggle, point selection, and resize -- the new surface this
correction added, on top of the already-soaked Trade Study workspace.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))
import harness  # noqa: E402


def main() -> int:
    from PySide6.QtCore import (QCoreApplication, QEvent, QUrl, QtMsgType,
                                 qInstallMessageHandler)
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

    a = harness.control_a_known_allocation(40)
    b = harness.control_b_released_allocation(40)
    print("control A:", a["pass"], "control B:", b["pass"])
    if not (a["pass"] and b["pass"]):
        print("FAIL: harness controls did not pass")
        return 1

    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=5, pause=0.015):
        for _ in range(rounds):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(pause)

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
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    study.setVariableEnabled("area_ratio", False)
    study.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 21)
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

    ROUNDS = 40
    series = []
    base = harness.memory()

    for i in range(ROUNDS):
        study.setSweepMetricEnabled("characteristic_velocity", i % 2 == 0)
        study.setProperty("sweepScaledToPeak", i % 3 == 0)
        study.toggleSelection(i % 21)
        study.toggleSelection(i % 21)
        window.setProperty("width", 1700 + (i % 4) * 50)
        settle(rounds=2, pause=0.01)
        series.append(harness.delta(base, harness.memory())["private_mb"])

    window.setProperty("width", 1920)
    settle(rounds=8)

    slope = harness.slope_mb_per_round(series)
    first_half = harness.slope_mb_per_round(series[:ROUNDS // 2])
    second_half = harness.slope_mb_per_round(series[ROUNDS // 2:])
    print(f"\n{ROUNDS} rounds of sweep-mode/metric/normalize/select/resize:")
    print(f"  total growth: {series[-1]:.2f} MB")
    print(f"  first-half slope: {first_half:.4f} MB/round")
    print(f"  second-half slope: {second_half:.4f} MB/round")
    print(f"  decelerating: {abs(second_half) <= abs(first_half) + 0.05}")

    print(f"\n{len(messages)} Qt warnings/criticals")
    for msg in messages:
        print(" ", msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
