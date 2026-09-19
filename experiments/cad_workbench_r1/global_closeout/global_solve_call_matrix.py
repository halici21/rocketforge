"""Global closeout section 27: consolidated cross-workspace solve-call matrix.

Reuses the established technique from every prior phase: monkeypatch the
real solve entry point directly on its already-imported module object, then
drive real UI interactions and assert zero calls. This run is deliberately a
MIXED session touching all six workspaces in one process, not six separate
runs, because the risk this section exists to catch is cross-workspace
leakage (e.g. switching to Engine Design after Line was solved triggering a
stray Line/Thermochemistry recompute) that six isolated runs cannot see.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "global_closeout"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickWindow  # noqa: F401
    from PySide6.QtQml import QQmlComponent

    import main as app_main
    from rocketforge.application.analysis import thermochemistry_service
    from rocketforge.application.analysis import performance_service
    from rocketforge.application.analysis import line_service
    from rocketforge.application.analysis import fluid_property_service
    from rocketforge.engineering.chamber import handshake as chamber_handshake
    from rocketforge.engineering.nozzle import performance as nozzle_performance

    messages = []

    def handler(kind, context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            messages.append(str(message))

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

    probe_lines = [
        'import QtQuick',
        'import RocketForge 1.0',
        'import "data" as Data',
        'import "engine/model"',
        'QtObject {',
        '  property var thermoC: Thermochemistry',
        '  property var perfC: RocketPerformance',
        '  property var study: TradeStudy',
        '  property var fluidC: FluidProperties',
        '  property var lineC: Line',
        '  property var engineM: EngineModel',
        '  property var nav: Data.Navigation',
        '}',
        '',
    ]
    probe_src = "\n".join(probe_lines)
    probe = QQmlComponent(engine)
    probe.setData(probe_src.encode("utf-8"),
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

    window.setProperty("appMode", "analysis")
    settle()

    # -- intentional solves to populate every workspace, BEFORE the spy ----
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

    # -- install the spy ----------------------------------------------------
    calls = {"thermo": 0, "perf": 0, "line": 0, "fluid": 0,
             "chamber": 0, "nozzle": 0}

    real_thermo = thermochemistry_service.solve_case
    real_perf = performance_service.solve_performance
    real_line = line_service.solve_case
    real_fluid = fluid_property_service.evaluate_case
    real_chamber = chamber_handshake.reduce_chamber_gas
    real_nozzle = nozzle_performance.solve_ideal_performance

    def spy_thermo(*a, **k):
        calls["thermo"] += 1
        return real_thermo(*a, **k)

    def spy_perf(*a, **k):
        calls["perf"] += 1
        return real_perf(*a, **k)

    def spy_line(*a, **k):
        calls["line"] += 1
        return real_line(*a, **k)

    def spy_fluid(*a, **k):
        calls["fluid"] += 1
        return real_fluid(*a, **k)

    def spy_chamber(*a, **k):
        calls["chamber"] += 1
        return real_chamber(*a, **k)

    def spy_nozzle(*a, **k):
        calls["nozzle"] += 1
        return real_nozzle(*a, **k)

    thermochemistry_service.solve_case = spy_thermo
    performance_service.solve_performance = spy_perf
    line_service.solve_case = spy_line
    fluid_property_service.evaluate_case = spy_fluid
    chamber_handshake.reduce_chamber_gas = spy_chamber
    nozzle_performance.solve_ideal_performance = spy_nozzle

    interactions = []

    def record(label):
        interactions.append((label, dict(calls)))

    # navigation across every workspace
    for key in ["home", "thermochem", "performance", "tradestudy",
                "fluidproperties", "line"]:
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle()
        record(f"navigate:{key}")

    # theme + resize
    window.setProperty("themeMode", "light")
    settle()
    record("theme:light")
    window.setProperty("themeMode", "dark")
    settle()
    record("theme:dark")
    for w, h in ((1366, 768), (1920, 1080), (2560, 1440)):
        window.setProperty("width", w)
        window.setProperty("height", h)
        settle()
        record(f"resize:{w}x{h}")

    # Trade Study: tab switches, axis-ish property touches, selection
    window.setProperty("currentPageIndex", nav.indexOfKey("tradestudy"))
    settle()
    study.requestTab.emit(2)
    settle()
    record("tradestudy:tab-trade")
    try:
        study.toggleSelection(0)
        settle()
        record("tradestudy:select-point")
        study.toggleSelection(0)
        settle()
        record("tradestudy:deselect-point")
    except Exception as exc:  # noqa: BLE001
        print("trade study selection interaction failed:", exc)
    study.requestTab.emit(1)
    settle()
    record("tradestudy:tab-results")
    study.requestTab.emit(0)
    settle()
    record("tradestudy:tab-setup")

    # Inspector / Dock open-close via ShellContext
    shell_probe = QQmlComponent(engine)
    shell_probe.setData(
        b'import QtQuick\nimport "data" as Data\n'
        b'QtObject { property var shell: Data.ShellContext }\n',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_shellprobe.qml")))
    shell_holder = shell_probe.create()
    shell = shell_holder.property("shell")
    if shell is not None:
        shell.setProperty("inspectorOpen", True)
        settle()
        record("inspector:open")
        shell.setProperty("inspectorOpen", False)
        settle()
        record("inspector:close")

    # Engine Design: pan/zoom/fit, selection, connection selection
    window.setProperty("appMode", "engine")
    settle()
    record("engine:enter")
    try:
        engineM.selectNode("n5", False)
        settle()
        record("engine:select-node")
        engineM.clearSelection()
        settle()
        engineM.selectConnection("c1")
        settle()
        record("engine:select-connection")
        engineM.clearSelection()
        settle()
        record("engine:clear-selection")
    except Exception as exc:  # noqa: BLE001
        print("engine selection interaction failed:", exc)
    window.setProperty("appMode", "analysis")
    settle()
    record("engine:exit-to-analysis")

    # restore real functions
    thermochemistry_service.solve_case = real_thermo
    performance_service.solve_performance = real_perf
    line_service.solve_case = real_line
    fluid_property_service.evaluate_case = real_fluid
    chamber_handshake.reduce_chamber_gas = real_chamber
    nozzle_performance.solve_ideal_performance = real_nozzle

    total = sum(calls.values())
    print("\nfinal call counts:", calls)
    print("TOTAL solve calls during view-only interactions:", total)

    report = {
        "final_counts": calls,
        "total": total,
        "interactions": [{"label": lbl, "cumulative_counts": c} for lbl, c in interactions],
        "qt_warnings": messages,
    }
    with open(OUT / "global_solve_call_matrix.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"{len(messages)} Qt warnings/criticals")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
