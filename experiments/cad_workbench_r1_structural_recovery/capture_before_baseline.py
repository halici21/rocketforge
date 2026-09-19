"""Immutable BEFORE baseline for the structural redesign recovery.

Captures the CURRENT production shell (as of the four-workspace-accepted
checkpoint) at the required resolution/theme matrix, before any recovery
code changes. Never re-run this against changed code -- these are the
reference images the recovery is measured against.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1_structural_recovery" / "before"
OUT.mkdir(parents=True, exist_ok=True)

# key, default calculate-slot (or None), out-name
PAGES = [
    ("isentropic", None, "home_landing"),  # no dedicated Home exists yet --
                                            # the default landing page today
    ("performance", "Performance", "rocket_performance"),
    ("thermochem", "Thermochemistry", "thermochemistry"),
    ("line", "Line", "line"),
    ("fluidproperties", "FluidProperties", "fluid_properties"),
]


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
        b'QtObject {\n'
        b'  property var performance: RocketPerformance\n'
        b'  property var thermochemistry: Thermochemistry\n'
        b'  property var line: Line\n'
        b'  property var fluidProperties: FluidProperties\n'
        b'  property int idxIsentropic: Navigation.indexOfKey("isentropic")\n'
        b'  property int idxPerformance: Navigation.indexOfKey("performance")\n'
        b'  property int idxThermochem: Navigation.indexOfKey("thermochem")\n'
        b'  property int idxLine: Navigation.indexOfKey("line")\n'
        b'  property int idxFluid: Navigation.indexOfKey("fluidproperties")\n'
        b'}',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()

    idx_for_key = {
        "isentropic": int(holder.property("idxIsentropic")),
        "performance": int(holder.property("idxPerformance")),
        "thermochem": int(holder.property("idxThermochem")),
        "line": int(holder.property("idxLine")),
        "fluidproperties": int(holder.property("idxFluid")),
    }
    controller_for_key = {
        "performance": holder.property("performance"),
        "thermochem": holder.property("thermochemistry"),
        "line": holder.property("line"),
        "fluidproperties": holder.property("fluidProperties"),
    }

    for key, _label, out_name in PAGES:
        window.setProperty("currentPageIndex", idx_for_key[key])
        settle()
        ctrl = controller_for_key.get(key)
        if ctrl is not None:
            available = ctrl.property("providerAvailable")
            if available is None or bool(available):
                ctrl.calculate()
                settle()

        for width, height in ((2560, 1440), (1920, 1080), (1366, 768)):
            window.setProperty("width", width)
            window.setProperty("height", height)
            settle()
            window.grabWindow().save(
                str(OUT / f"{out_name}_dark_{width}x{height}.png"))

        window.setProperty("width", 1920)
        window.setProperty("height", 1080)
        window.setProperty("themeMode", "light")
        settle()
        window.grabWindow().save(str(OUT / f"{out_name}_light_1920x1080.png"))
        window.setProperty("themeMode", "dark")
        settle()

        print(f"[{out_name}] captured")

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"\n{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
