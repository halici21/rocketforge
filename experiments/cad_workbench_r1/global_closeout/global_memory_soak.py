"""Global closeout section 29-30: mixed-session global memory soak.

Reuses the project's own control-verified process-memory harness
(experiments/qml_memory/harness.py) directly, following the exact pattern
established for every prior per-workspace soak in this program. This one is
deliberately MIXED across all six workspaces plus Home plus Engine Design in
a single long-running session, because that is what a real user session
looks like and is the condition most likely to reveal cross-workspace
accumulation that six isolated soaks would miss.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
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

    def settle(rounds=5, pause=0.01):
        for _ in range(rounds):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(pause)

    probe_lines = [
        'import QtQuick', 'import RocketForge 1.0', 'import "data" as Data',
        'import "engine/model"', 'QtObject {',
        '  property var thermoC: Thermochemistry',
        '  property var perfC: RocketPerformance',
        '  property var study: TradeStudy',
        '  property var fluidC: FluidProperties',
        '  property var lineC: Line',
        '  property var engineM: EngineModel',
        '  property var nav: Data.Navigation',
        '  property var shell: Data.ShellContext',
        '}', '',
    ]
    probe = QQmlComponent(engine)
    probe.setData("\n".join(probe_lines).encode("utf-8"),
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    if holder is None:
        print("probe errors:", probe.errors())
        return 1

    thermoC = holder.property("thermoC")
    perfC = holder.property("perfC")
    study = holder.property("study")
    fluidC = holder.property("fluidC")
    lineC = holder.property("lineC")
    engineM = holder.property("engineM")
    nav = holder.property("nav")
    shell = holder.property("shell")

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "analysis")
    settle()

    if thermoC.property("providerAvailable"):
        thermoC.calculate()
        settle()
    perfC.calculate()
    settle()
    fluidC.calculate()
    settle()
    lineC.calculate()
    settle()
    study.setVariableEnabled("area_ratio", False)
    study.setVariableRange("oxidiser_fuel_ratio", 2.6, 4.2, 6)
    study.runStudy()
    for _ in range(400):
        app.processEvents()
        time.sleep(0.01)
        if not study.property("busy"):
            break
    settle()
    engineM.loadDemo()
    settle()

    pages = ["home", "thermochem", "performance", "tradestudy",
             "fluidproperties", "line"]

    ROUNDS = 500
    series = []
    base = harness.memory()

    for i in range(ROUNDS):
        key = pages[i % len(pages)]
        window.setProperty("appMode", "analysis")
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        window.setProperty("themeMode", "light" if i % 5 == 0 else "dark")
        window.setProperty("width", 1700 + (i % 4) * 50)
        if shell is not None:
            shell.setProperty("inspectorOpen", i % 7 == 0)
        if key == "tradestudy":
            study.requestTab.emit(i % 4)
            try:
                if study.property("pointCount"):
                    study.toggleSelection(0)
                    study.toggleSelection(0)
            except Exception:
                pass
        # Engine Design round-trip every 8th round.
        if i % 8 == 0:
            window.setProperty("appMode", "engine")
            settle(rounds=2, pause=0.005)
            nid = "n%d" % (1 + (i % 7))
            try:
                engineM.selectNode(nid, False)
                engineM.clearSelection()
            except Exception:
                pass
            window.setProperty("appMode", "analysis")
        settle(rounds=2, pause=0.005)
        series.append(harness.delta(base, harness.memory())["private_mb"])

    window.setProperty("width", 1920)
    window.setProperty("themeMode", "dark")
    window.setProperty("appMode", "analysis")
    window.setProperty("currentPageIndex", nav.indexOfKey("home"))
    settle(rounds=8)

    slope = harness.slope_mb_per_round(series)
    first_half = harness.slope_mb_per_round(series[:ROUNDS // 2])
    second_half = harness.slope_mb_per_round(series[ROUNDS // 2:])
    print(f"\n{ROUNDS} mixed cross-workspace rounds "
          f"(navigate/theme/resize/Inspector/Trade-tab/Engine-select):")
    print(f"  total growth: {series[-1]:.2f} MB")
    print(f"  overall slope: {slope:.4f} MB/round")
    print(f"  first-half slope: {first_half:.4f} MB/round")
    print(f"  second-half slope: {second_half:.4f} MB/round")
    print(f"  decelerating: {abs(second_half) <= abs(first_half) + 0.05}")

    e = harness.control_e_object_lifecycle(app)
    print(f"\ncontrol E (200 QObject create/deleteLater, census returns "
          f"to zero): {e['pass']}")

    print(f"\n{len(messages)} Qt warnings/criticals")
    for msg in messages[:20]:
        print(" ", msg)

    ok = (abs(second_half) <= abs(first_half) + 0.05 and e["pass"] and not messages)
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
