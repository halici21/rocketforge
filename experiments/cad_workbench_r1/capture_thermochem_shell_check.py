"""Basic shell-wrap verification for Thermochemistry (NOT a redesign check --
just: does the existing, unmodified page load and solve correctly through
the new shell, the same mechanical question asked of Rocket Performance).
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "thermochemistry"
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

    def settle(rounds=6, pause=0.05):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject { property var thermo: Thermochemistry\n'
        b'  property int idx: Navigation.indexOfKey("thermochem") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    thermo = holder.property("thermo")
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    if not thermo.property("providerAvailable"):
        print("no chemistry provider -- capturing the provider-unavailable state only")
        for width, height in ((1920, 1080), (1366, 768)):
            window.setProperty("width", width)
            window.setProperty("height", height)
            settle()
            window.grabWindow().save(str(OUT / f"no_provider_{width}x{height}.png"))
        warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
        print(f"{len(warnings)} Qt warnings")
        return 0

    solves = {"n": 0}
    from rocketforge.application.analysis import thermochemistry_provider as gw
    if gw.availability().usable:
        provider = gw.chamber_provider()
        original = provider.solve_chamber

        def counting(request, _o=original):
            solves["n"] += 1
            return _o(request)
        provider.solve_chamber = counting

    thermo.resetInputs()
    thermo.calculate()
    settle()
    after_calc = solves["n"]

    for width, height in ((2560, 1440), (1920, 1080), (1366, 768)):
        window.setProperty("width", width)
        window.setProperty("height", height)
        settle()
        window.grabWindow().save(str(OUT / f"calculator_{width}x{height}.png"))

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("themeMode", "light")
    settle()
    window.grabWindow().save(str(OUT / "calculator_light_1920x1080.png"))
    window.setProperty("themeMode", "dark")
    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    settle()
    window.grabWindow().save(str(OUT / "calculator_1366x768.png"))
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)

    # ---- stale-vs-solved mismatch fixture (rf-visual-qa's required check) --
    before_stale_edit = solves["n"]
    thermo.setProperty("mixtureRatio", 4.2)
    settle()
    window.grabWindow().save(str(OUT / "calculator_stale_1920x1080.png"))
    solves_from_stale_edit = solves["n"] - before_stale_edit
    thermo.resetInputs()
    thermo.calculate()
    settle()

    # Browser/Dock interaction must not re-solve
    before = solves["n"]
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()
    dock = None
    for c in window.findChildren(object):
        if c.metaObject().className().startswith("AnalysisDock"):
            dock = c
            break
    if dock is not None:
        dock.setProperty("expanded", True)
        settle()
        dock.setProperty("expanded", False)
        settle()
    after_interaction = solves["n"]

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"solves: after calculate={after_calc}, after tab/dock interaction "
          f"delta={after_interaction - before}, after stale-edit "
          f"delta={solves_from_stale_edit} (expect 0 -- editing must mark "
          f"stale, never silently re-solve)")
    print(f"{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
