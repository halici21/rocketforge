"""Capture the CURRENT (pre-R1) shell headlessly, as "before" evidence for
the CAD/CAE Workbench R1 current-UI audit.

Mirrors experiments/ui_visual_pilot/capture_matrix.py's pattern: real running
application, offscreen QPA, window.grabWindow(), Qt message capture.

    QT_QPA_PLATFORM=offscreen python experiments/cad_workbench_r1/capture_current_shell.py
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "acceptance" / "cad_workbench_r1" / "current_ui_audit"
OUT.mkdir(parents=True, exist_ok=True)

RESOLUTIONS = ((1920, 1080), (1366, 768))


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
        messages.append({"kind": kinds.get(kind, str(kind)), "message": message})

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

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport "model"\n'
        b'QtObject { property var engineModel: EngineModel }',
        QUrl.fromLocalFile(str((ui_dir / "engine" / "_probe.qml"))))
    holder = probe.create()
    engine_model = holder.property("engineModel") if holder is not None else None
    if holder is None:
        messages.append({"kind": "info", "message": f"engine probe failed: {probe.errorString()}"})

    def settle(rounds: int = 6, pause: float = 0.05) -> None:
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    captures: list[dict] = []

    def capture(name: str, note: str) -> None:
        settle()
        image = window.grabWindow()
        image.save(str(OUT / f"{name}.png"))
        captures.append({"name": name, "note": note,
                         "width": image.width(), "height": image.height()})

    # ---- analysis mode, default landing page, both themes -----------------
    window.setProperty("appMode", "analysis")
    window.setProperty("currentPageIndex", 0)
    for width, height in RESOLUTIONS:
        window.setProperty("width", width)
        window.setProperty("height", height)
        capture(f"analysis_default_dark_{width}x{height}",
                "default analysis landing page (index 0), dark theme")

    window.setProperty("themeMode", "light")
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    capture("analysis_default_light_1920x1080",
            "default analysis landing page, light theme")
    window.setProperty("themeMode", "dark")

    # ---- engine design mode, empty canvas ----------------------------------
    window.setProperty("appMode", "engine")
    for width, height in RESOLUTIONS:
        window.setProperty("width", width)
        window.setProperty("height", height)
        capture(f"engine_empty_dark_{width}x{height}",
                "Engine Design, empty canvas, dark theme")

    window.setProperty("themeMode", "light")
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    capture("engine_empty_light_1920x1080", "Engine Design, empty canvas, light theme")
    window.setProperty("themeMode", "dark")

    # ---- engine design mode, demo engine loaded ----------------------------
    if engine_model is not None:
        try:
            engine_model.loadDemo()
        except Exception as error:  # noqa: BLE001
            messages.append({"kind": "info", "message": f"loadDemo failed: {error}"})
        settle()
        for width, height in RESOLUTIONS:
            window.setProperty("width", width)
            window.setProperty("height", height)
            capture(f"engine_demo_dark_{width}x{height}",
                    "Engine Design, demo gas-generator architecture loaded, dark theme")

    report = {
        "purpose": "current (pre-R1) shell capture -- CAD/CAE Workbench R1 "
                   "current-UI audit evidence",
        "python": sys.version.split()[0],
        "captures": captures,
        "messages": messages,
        "warnings": [m for m in messages if m["kind"] in ("warning", "critical", "fatal")],
    }
    (OUT / "capture_report.json").write_text(json.dumps(report, indent=2),
                                             encoding="utf-8")
    print(f"{len(captures)} captures, {len(report['warnings'])} Qt warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
