"""Capture the Rocket Performance workspace across the canonical state matrix.

Runs unchanged before and after the visual pilot, so the two capture sets are
directly comparable and the scientific snapshot at each state can be diffed
field by field.

    python experiments/ui_visual_pilot/capture_matrix.py <before|after>

It also counts **provider solves**, wrapped around the gateway's own provider
so that what is counted is a real chemistry call reaching a real library. A
redesign that introduced a binding loop and re-solved the chamber on a nozzle
change would be caught here.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

LABEL = sys.argv[1] if len(sys.argv) > 1 else "before"
OUT = ROOT / "acceptance" / "ui_visual_pilot" / LABEL
OUT.mkdir(parents=True, exist_ok=True)

RESOLUTIONS = ((2560, 1440), (1920, 1080), (1366, 768))
PERFORMANCE, MODEL, ORACLE = 0, 1, 2


def main() -> int:
    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    messages: list[dict] = []
    kinds = {QtMsgType.QtDebugMsg: "debug", QtMsgType.QtInfoMsg: "info",
             QtMsgType.QtWarningMsg: "warning",
             QtMsgType.QtCriticalMsg: "critical",
             QtMsgType.QtFatalMsg: "fatal"}

    def handler(kind, context, message):
        messages.append({"kind": kinds.get(kind, str(kind)),
                         "message": message})

    qInstallMessageHandler(handler)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    ui_dir = app_main.UI_DIR
    engine.load(QUrl.fromLocalFile(str(ui_dir / "Main.qml")))
    roots = engine.rootObjects()
    if not roots:
        print("qml load failed")
        return 1
    window = roots[0]

    from rocketforge.application.analysis.performance_controller import (
        RocketPerformanceController,
    )
    from rocketforge.application.analysis.thermochemistry_controller import (
        ThermochemistryController,
    )

    performance = [c for c in engine.rootObjects()[0].findChildren(object)
                   if isinstance(c, RocketPerformanceController)]
    # The controllers are QML singletons; reach them through the engine.
    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject {\n'
        b'  property var perf: RocketPerformance\n'
        b'  property var thermo: Thermochemistry\n'
        b'  property int idx: Navigation.indexOfKey("performance")\n'
        b'}',
        QUrl.fromLocalFile(str(ui_dir / "_probe.qml")))
    holder = probe.create()
    if holder is None:
        print("probe failed:", probe.errorString())
        return 1
    controller = holder.property("perf")
    thermo = holder.property("thermo")
    window.setProperty("currentPageIndex", int(holder.property("idx")))

    # -- the provider-call counter ---------------------------------------
    solves = {"calls": 0}
    try:
        from rocketforge.application.analysis import (
            thermochemistry_provider as gateway,
        )

        if gateway.availability().usable:
            provider = gateway.chamber_provider()
            original = provider.solve_chamber

            def counting(request, _original=original):
                solves["calls"] += 1
                return _original(request)

            provider.solve_chamber = counting  # type: ignore[method-assign]
    except Exception as error:  # noqa: BLE001
        messages.append({"kind": "info", "message": f"counter: {error}"})

    def settle(rounds: int = 6, pause: float = 0.05) -> None:
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    from rocketforge.application.perfsmoke import _snapshot

    captures: list[dict] = []

    def capture(name: str, note: str) -> None:
        settle()
        image = window.grabWindow()
        image.save(str(OUT / f"{name}.png"))
        captures.append({"name": name, "note": note,
                         "width": image.width(), "height": image.height(),
                         "solveCalls": solves["calls"],
                         "state": _snapshot(controller)})

    report: dict = {"label": LABEL, "status": "ok",
                    "python": sys.version.split()[0]}

    # ---- empty: no chamber ----------------------------------------------
    for width, height in RESOLUTIONS:
        window.setProperty("width", width)
        window.setProperty("height", height)
        controller.showTab(PERFORMANCE)
        capture(f"empty_{width}x{height}", "no chamber state")

    if not thermo.property("providerAvailable"):
        report["captures"] = captures
        report["messages"] = messages
        report["note"] = "no chemistry provider; empty state only"
        (OUT / "capture_matrix.json").write_text(json.dumps(report, indent=2),
                                                 encoding="utf-8")
        return 0

    thermo.resetInputs()
    thermo.calculate()
    settle()
    after_chamber = solves["calls"]
    report["solvesAfterChamber"] = after_chamber

    # ---- the state matrix -----------------------------------------------
    STATES = [
        ("normalized_vacuum", dict(areaRatio=40.0, ambientMode="vacuum",
                                   scaleMode="normalized"),
         "normalized, vacuum: no engine size, so no thrust"),
        ("scaled_vacuum", dict(areaRatio=40.0, ambientMode="vacuum",
                               scaleMode="throat_area", scaleValue=0.02),
         "scaled by throat area: absolute thrust appears"),
        ("ambient_sea_level", dict(areaRatio=40.0, ambientMode="sea_level",
                                   scaleMode="throat_area", scaleValue=0.02),
         "sea level: overexpanded at this area ratio"),
        ("pressure_positive", dict(areaRatio=8.0, ambientMode="custom",
                                   ambientPressure=1000.0,
                                   scaleMode="throat_area", scaleValue=0.02),
         "pe > pa: positive pressure thrust"),
        ("pressure_near_zero", dict(areaRatio=40.0, ambientMode="custom",
                                    ambientPressure=21299.0,
                                    scaleMode="throat_area", scaleValue=0.02),
         "pe close to pa: the pressure term nearly vanishes"),
        ("pressure_negative", dict(areaRatio=120.0, ambientMode="sea_level",
                                   scaleMode="throat_area", scaleValue=0.02),
         "pe < pa: negative pressure thrust, not a failure"),
    ]

    for width, height in RESOLUTIONS:
        window.setProperty("width", width)
        window.setProperty("height", height)
        for name, settings, note in STATES:
            controller.resetInputs()
            for key, value in settings.items():
                controller.setProperty(key, value)
            controller.calculate()
            controller.showTab(PERFORMANCE)
            capture(f"{name}_{width}x{height}", note)

    # ---- model and provenance views -------------------------------------
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    controller.resetInputs()
    controller.calculate()
    controller.showTab(MODEL)
    capture("model_trace_1920x1080", "assumptions, reduction and provenance")
    controller.showTab(PERFORMANCE)

    # ---- stale: edit an input without recalculating ----------------------
    before_stale = solves["calls"]
    controller.setProperty("areaRatio", 60.0)
    settle()
    capture("stale_1920x1080", "an edited input marks the result stale")
    report["solvesFromStaleEdit"] = solves["calls"] - before_stale

    # ---- invalid: a nozzle regime this model refuses ---------------------
    controller.resetInputs()
    controller.setProperty("areaRatio", 2.0)
    controller.setProperty("ambientMode", "custom")
    controller.setProperty("ambientPressure", 5.0e6)
    controller.calculate()
    capture("invalid_1920x1080", "a regime outside the ideal model, refused")

    # ---- light theme -----------------------------------------------------
    window.setProperty("themeMode", "light")
    controller.resetInputs()
    controller.setProperty("scaleMode", "throat_area")
    controller.setProperty("scaleValue", 0.02)
    controller.calculate()
    for width, height in RESOLUTIONS:
        window.setProperty("width", width)
        window.setProperty("height", height)
        capture(f"light_{width}x{height}", "light theme, scaled vacuum")
    window.setProperty("themeMode", "dark")

    # ---- interaction spies ----------------------------------------------
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    controller.resetInputs()
    controller.calculate()
    settle()

    spies = {}
    for label, key, value in (("epsilon", "areaRatio", 55.0),
                              ("ambient", "ambientPressure", 50000.0),
                              ("scaleValue", "scaleValue", 0.03)):
        if label == "ambient":
            controller.setProperty("ambientMode", "custom")
        before = solves["calls"]
        controller.setProperty(key, value)
        controller.calculate()
        settle()
        spies[label] = solves["calls"] - before

    before = solves["calls"]
    controller.showTab(MODEL)
    controller.showTab(ORACLE)
    controller.showTab(PERFORMANCE)
    window.setProperty("themeMode", "light")
    window.setProperty("themeMode", "dark")
    window.setProperty("width", 1366)
    window.setProperty("width", 1920)
    settle()
    spies["view_theme_resize"] = solves["calls"] - before

    report["chemistrySolvesPerInteraction"] = spies
    report["totalSolves"] = solves["calls"]
    report["captures"] = captures
    report["messages"] = messages
    report["warnings"] = [m for m in messages
                          if m["kind"] in ("warning", "critical", "fatal")]
    (OUT / "capture_matrix.json").write_text(json.dumps(report, indent=2),
                                             encoding="utf-8")
    print(f"[{LABEL}] {len(captures)} captures, {len(report['warnings'])} "
          f"Qt warnings, chemistry solves per interaction: {spies}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
