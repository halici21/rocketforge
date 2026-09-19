"""Global closeout section 14: cross-workspace screenshot matrix.

Not a re-capture of every per-state screenshot each workspace already has
from its own accepted phase (those remain valid -- no source in those
workspaces changed except the documented Engine Design/Trade Study fixes,
already captured separately). This is the GLOBAL consistency pass: every
page, populated with real data where straightforward, at the blocking
1366x768 resolution, plus Home across the full resolution/theme set.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "global_closeout" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickWindow  # noqa: F401
    from PySide6.QtQml import QQmlComponent

    import main as app_main

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

    def settle(rounds=10, pause=0.02):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    probe_lines = [
        'import QtQuick',
        'import RocketForge 1.0',
        'import "data"',
        'import "engine/model"',
        'QtObject {',
        '  property var thermoC: Thermochemistry',
        '  property var perfC: RocketPerformance',
        '  property var study: TradeStudy',
        '  property var fluidC: FluidProperties',
        '  property var lineC: Line',
        '  property var engineM: EngineModel',
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

    nav_probe_lines = [
        'import QtQuick',
        'import "data" as Data',
        'QtObject {',
        '  property var nav: Data.Navigation',
        '}',
        '',
    ]
    nav_probe_src = "\n".join(nav_probe_lines)
    nav_probe = QQmlComponent(engine)
    nav_probe.setData(nav_probe_src.encode("utf-8"),
                      QUrl.fromLocalFile(str(app_main.UI_DIR / "_navprobe2.qml")))
    nav_holder = nav_probe.create()
    nav = nav_holder.property("nav")

    thermoC = holder.property("thermoC")
    perfC = holder.property("perfC")
    study = holder.property("study")
    fluidC = holder.property("fluidC")
    lineC = holder.property("lineC")
    engineM = holder.property("engineM")

    window.setProperty("appMode", "analysis")
    settle()

    # -- populate each workspace with real data -----------------------------
    if thermoC is not None and thermoC.property("providerAvailable"):
        thermoC.calculate()
        settle()
    if perfC is not None:
        try:
            perfC.calculate()
            settle()
        except Exception as exc:  # noqa: BLE001
            print("perfC.calculate failed:", exc)
    if fluidC is not None:
        try:
            fluidC.calculate()
            settle()
        except Exception as exc:  # noqa: BLE001
            print("fluidC.calculate failed:", exc)
    if lineC is not None:
        try:
            lineC.calculate()
            settle()
        except Exception as exc:  # noqa: BLE001
            print("lineC.calculate failed:", exc)
    if study is not None:
        study.setVariableEnabled("area_ratio", False)
        study.setVariableRange("oxidiser_fuel_ratio", 2.6, 4.2, 6)
        study.runStudy()
        for _ in range(400):
            app.processEvents()
            time.sleep(0.01)
            if not study.property("busy"):
                break
        settle()
    if engineM is not None:
        try:
            engineM.loadDemo()
            settle()
        except Exception as exc:  # noqa: BLE001
            print("engineM.loadDemo failed:", exc)

    pages = ["home", "thermochem", "performance", "tradestudy",
             "fluidproperties", "line"]

    # -- 1366x768 dark pass across every analysis page + engine -------------
    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    window.setProperty("themeMode", "dark")
    for key in pages:
        page_idx = nav.indexOfKey(key)
        window.setProperty("appMode", "analysis")
        window.setProperty("currentPageIndex", page_idx)
        settle()
        window.grabWindow().save(str(OUT / f"global_1366_dark_{key}.png"))
        print(key, "-> index", page_idx, "captured")

    window.setProperty("appMode", "engine")
    settle()
    window.grabWindow().save(str(OUT / "global_1366_dark_engine.png"))
    print("engine -> captured")

    # -- Home across the full resolution/theme set ---------------------------
    window.setProperty("appMode", "analysis")
    window.setProperty("currentPageIndex", nav.indexOfKey("home"))
    for width, height in ((2560, 1440), (1920, 1080), (1366, 768)):
        window.setProperty("width", width)
        window.setProperty("height", height)
        window.setProperty("themeMode", "dark")
        settle()
        window.grabWindow().save(str(OUT / f"global_home_dark_{width}x{height}.png"))
    for width, height in ((1920, 1080), (1366, 768)):
        window.setProperty("width", width)
        window.setProperty("height", height)
        window.setProperty("themeMode", "light")
        settle()
        window.grabWindow().save(str(OUT / f"global_home_light_{width}x{height}.png"))
    window.setProperty("themeMode", "dark")

    warnings = list(messages)
    print(f"\n{len(warnings)} Qt warnings/criticals during global capture")
    for m in warnings[:30]:
        print(" ", m)

    return 0


if __name__ == "__main__":
    sys.exit(main())
