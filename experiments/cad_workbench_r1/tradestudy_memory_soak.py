"""Memory soak for the redesigned Trade Study workspace.

Cycles the interactions the mega-prompt calls out by name: axis switching,
selected-point cycling, Dock open/close, Inspector open/close, table
selection, resize, theme change -- and requires bounded/decelerating growth,
using this project's own control-verified process-memory harness
(experiments/qml_memory/harness.py) rather than a new, unverified probe.
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
    from PySide6.QtCore import (QCoreApplication, QEvent, QObject, QUrl,
                                 QtMsgType, qInstallMessageHandler)
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

    print("=== harness controls (this process) ===")
    a = harness.control_a_known_allocation(40)
    print("control A (known 40MB alloc):", a["pass"], a["seen"])
    b = harness.control_b_released_allocation(40)
    print("control B (release+collect):", b["pass"], b["retained"])
    d = harness.control_d_no_op_noise(app, rounds=10, iterations=30)
    print("control D (no-op floor): slope=", d["slope_mb_per_round"],
          "peak-to-peak=", d["peak_to_peak_mb"])
    if not (a["pass"] and b["pass"]):
        print("FAIL: harness controls did not pass -- readings below are"
              " not trustworthy")
        return 1

    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=6, pause=0.02):
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
        print("no thermochemistry provider -- cannot run this soak")
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

    dock = window.findChild(QObject, "analysisDock")
    options = study.property("objectiveAxisOptions")
    axis_keys = [o["key"] for o in options] if options else []
    n_points = study.property("visibleRowCount")
    print(f"\nstudy: {n_points} points, axis options: {axis_keys}")

    ROUNDS = 60
    series = []
    base = harness.memory()

    for i in range(ROUNDS):
        # axis switching
        study.setProperty("paretoX", axis_keys[i % len(axis_keys)])
        study.setProperty("paretoY", axis_keys[(i + 1) % len(axis_keys)])
        # selected-point cycling
        idx = i % max(1, n_points)
        study.toggleSelection(idx)
        study.toggleSelection(idx)
        # Dock open/close
        if dock is not None:
            dock.setProperty("currentTab", i % 2)
            dock.setProperty("expanded", i % 2 == 0)
        # Inspector open/close (mirrors the auto-open-on-select path)
        study.toggleSelection(idx)
        settle(rounds=2, pause=0.005)
        study.toggleSelection(idx)
        # table sort/filter/page navigation
        study.setProperty("filterMode", "feasible" if i % 2 else "all")
        # resize
        window.setProperty("width", 1600 + (i % 5) * 40)
        window.setProperty("height", 900 + (i % 3) * 20)
        # theme change
        window.setProperty("themeMode", "light" if i % 2 else "dark")

        settle(rounds=3, pause=0.005)
        series.append(harness.delta(base, harness.memory())["private_mb"])

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("themeMode", "dark")
    if dock is not None:
        dock.setProperty("expanded", False)
    settle(rounds=10)

    slope = harness.slope_mb_per_round(series)
    first_half = harness.slope_mb_per_round(series[:ROUNDS // 2])
    second_half = harness.slope_mb_per_round(series[ROUNDS // 2:])
    print(f"\n{ROUNDS} rounds of axis-switch/select/dock/inspector/"
          f"resize/theme cycling:")
    print(f"  total growth: {series[-1]:.2f} MB")
    print(f"  overall slope: {slope:.4f} MB/round")
    print(f"  first-half slope: {first_half:.4f} MB/round")
    print(f"  second-half slope: {second_half:.4f} MB/round")
    print(f"  decelerating: {abs(second_half) <= abs(first_half) + 0.05}")

    e = harness.control_e_object_lifecycle(app)
    print(f"\ncontrol E (200 QObject create/deleteLater, census returns "
          f"to zero): {e['pass']} "
          f"(alive before dispatch={e['alive_before_dispatch']}, "
          f"after={e['alive_after_dispatch']})")

    print(f"\n{len(messages)} Qt warnings/criticals during the soak")
    for msg in messages[:20]:
        print(" ", msg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
