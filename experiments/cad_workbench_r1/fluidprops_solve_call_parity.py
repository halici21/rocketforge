"""Fluid Properties solve-call parity: Evaluate -> exactly 1 provider
evaluation; every other interaction (Browser, Dock, selection, theme,
resize, stale-edit) -> 0.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "fluidproperties"
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
        b'QtObject { property var fp: FluidProperties\n'
        b'  property int idx: Navigation.indexOfKey("fluidproperties")\n'
        b'  property int perfIdx: Navigation.indexOfKey("performance") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    fp = holder.property("fp")
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()

    # Patch the one function FluidPropertyController.calculate() actually
    # calls -- no module reload, just a direct attribute swap on the
    # already-imported module object the running controller holds a
    # reference to (same technique as line_solve_call_parity.py).
    evals = {"n": 0}
    import rocketforge.application.analysis.fluid_property_service as fp_service
    original_evaluate_case = fp_service.evaluate_case

    def counting(case, _o=original_evaluate_case):
        evals["n"] += 1
        return _o(case)
    fp_service.evaluate_case = counting

    spies = {}

    def spy(label, action):
        before = evals["n"]
        action()
        settle()
        spies[label] = evals["n"] - before

    spy("evaluate", lambda: fp.calculate())

    dock = None
    for c in window.findChildren(object):
        if c.metaObject().className().startswith("AnalysisDock"):
            dock = c
            break

    spy("dock_expand_collapse", lambda: (dock.setProperty("expanded", True),
                                         dock.setProperty("expanded", False)))
    spy("selection_navigate_away_and_back", lambda: (
        window.setProperty("currentPageIndex", int(holder.property("perfIdx"))),
        settle(3),
        window.setProperty("currentPageIndex", int(holder.property("idx")))))
    spy("theme_toggle", lambda: (window.setProperty("themeMode", "light"),
                                 settle(3),
                                 window.setProperty("themeMode", "dark")))
    spy("resize", lambda: (window.setProperty("width", 1366),
                           settle(3),
                           window.setProperty("width", 1920)))
    spy("stale_edit_no_recalculate", lambda: fp.setTemperature(120.0))

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    report = {"spies": spies, "warnings": len(warnings)}
    (OUT / "solve_call_parity.json").write_text(json.dumps(report, indent=2),
                                                encoding="utf-8")
    print(json.dumps(spies, indent=2))
    print(f"{len(warnings)} Qt warnings")
    ok = spies.get("evaluate") == 1 and all(
        v == 0 for k, v in spies.items() if k != "evaluate")
    print("PASS" if ok and not warnings else "FAIL")
    return 0 if ok and not warnings else 1


if __name__ == "__main__":
    sys.exit(main())
