"""Solve-call matrix for Engine Design. The component inventory found zero
Python backend wiring for this workspace at all (no ui/engine/**.qml file
imports RocketForge 1.0) -- this script measures that directly rather than
trusting the inventory's own static-analysis claim, by spying on every
real solve entry point in the application and driving a full interaction
battery through the real Engine Design UI.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler, QPoint
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent
    from PySide6.QtTest import QTest
    from PySide6.QtCore import Qt as QtNS

    import main as app_main
    from rocketforge.application.analysis import thermochemistry_service as thermo
    from rocketforge.application.analysis import performance_service as perf
    from rocketforge.application.analysis import line_service as line
    from rocketforge.engineering.chamber import handshake as chamber_handshake
    from rocketforge.engineering.nozzle import performance as nozzle_perf

    messages = []
    kinds = {QtMsgType.QtWarningMsg: "warning", QtMsgType.QtCriticalMsg: "critical",
             QtMsgType.QtFatalMsg: "fatal"}

    def handler(kind, context, message):
        if kind in kinds:
            messages.append((kinds[kind], message))

    qInstallMessageHandler(handler)

    counts = {"thermo": 0, "perf": 0, "line": 0, "chamber": 0, "nozzle": 0}
    real_thermo = thermo.solve_case
    real_perf = perf.solve_performance
    real_line = line.solve_case
    real_chamber = chamber_handshake.reduce_chamber_gas
    real_nozzle = nozzle_perf.solve_ideal_performance

    def spy(name, real):
        def wrapper(*a, **kw):
            counts[name] += 1
            return real(*a, **kw)
        return wrapper

    thermo.solve_case = spy("thermo", real_thermo)
    perf.solve_performance = spy("perf", real_perf)
    line.solve_case = spy("line", real_line)
    chamber_handshake.reduce_chamber_gas = spy("chamber", real_chamber)
    nozzle_perf.solve_ideal_performance = spy("nozzle", real_nozzle)

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
        b'import QtQuick\nimport RocketForge 1.0\nimport "engine/model"\n'
        b'QtObject { property var engineModel: EngineModel }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    engine_model = holder.property("engineModel")

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "engine")
    settle()

    def reset():
        for k in counts:
            counts[k] = 0

    def total():
        return sum(counts.values())

    results = []

    def record(label):
        results.append((label, dict(counts)))

    # Load demo (via the real button click, exercising fitAll()).
    reset()
    QTest.mouseClick(window, QtNS.MouseButton.LeftButton, QtNS.KeyboardModifier.NoModifier,
                      QPoint(929, 602))
    settle(rounds=15, pause=0.03)
    record("load demo engine (button click)")

    reset()
    engine_model.selectNode("n5", False)
    settle()
    record("select a component")

    reset()
    engine_model.setNodeEnabled("n5", False)
    settle()
    record("disable a component")
    engine_model.setNodeEnabled("n5", True)
    settle()

    reset()
    engine_model.clearSelection()
    settle()
    engine_model.selectConnection("c1")
    settle()
    record("select a connection")
    engine_model.clearSelection()
    settle()

    reset()
    engine_model.setProperty("detailLevel", "compact")
    settle()
    record("toggle compact detail level")
    engine_model.setProperty("detailLevel", "normal")
    settle()

    reset()
    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    settle()
    record("resize to 1366x768")
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()

    reset()
    window.setProperty("themeMode", "light")
    settle()
    record("theme change to light")
    window.setProperty("themeMode", "dark")
    settle()

    reset()
    engine_model.duplicateNode("n1")
    settle()
    record("duplicate a component")

    reset()
    engine_model.renameNode("n1", "Renamed Tank")
    settle()
    record("rename a component")

    reset()
    window.setProperty("appMode", "analysis")
    settle()
    window.setProperty("appMode", "engine")
    settle()
    record("switch to Analysis mode and back")

    print("\n--- Engine Design solve-call matrix ---")
    all_zero = True
    for label, c in results:
        bad = any(v != 0 for v in c.values())
        all_zero = all_zero and not bad
        flag = "FAIL" if bad else "ok"
        print(f"  [{flag}] {label}: {c}")

    warnings = messages
    print(f"\n{len(warnings)} Qt warnings/criticals")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")

    print("\nRESULT:", "PASS" if all_zero and not warnings else "FAIL")
    return 0 if all_zero and not warnings else 1


if __name__ == "__main__":
    sys.exit(main())
