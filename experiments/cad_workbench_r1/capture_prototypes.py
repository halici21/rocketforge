"""Capture ONE shell prototype (A/B/C) headlessly. Run once per process --
loading multiple QQmlApplicationEngine instances against ApplicationWindow
roots in one process is unstable (segfaults on the second load), so this
takes a single prototype name and is invoked three times, once per process,
by run_prototype_captures.bat / the orchestrating shell command.

    QT_QPA_PLATFORM=offscreen QT_QPA_FONTDIR="C:/Windows/Fonts" \\
        .venv-cea/Scripts/python.exe experiments/cad_workbench_r1/capture_prototypes.py ProtoA

Requires the temporary Obsidian/Champagne dark-palette values already in
place in ui/theme/Theme.qml -- all three prototypes read the same Theme
singleton, so the palette is identical across A/B/C by construction.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "acceptance" / "cad_workbench_r1"
UI_DIR = ROOT / "ui"

RESOLUTIONS = ((2560, 1440), (1920, 1080), (1366, 768))


def main() -> int:
    proto = sys.argv[1] if len(sys.argv) > 1 else "ProtoA"

    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication

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
    engine.warnings.connect(
        lambda errs: messages.extend(
            {"kind": "qml-error", "message": str(e)} for e in errs))
    engine.load(QUrl.fromLocalFile(str(UI_DIR / "_prototypes" / f"{proto}.qml")))
    roots = engine.rootObjects()
    if not roots:
        print(f"[{proto}] qml load failed")
        for m in messages:
            print("   ", m["kind"], m["message"])
        return 1
    window = roots[0]

    proto_out = OUT / f"shell_prototype_{proto[-1].lower()}"
    proto_out.mkdir(parents=True, exist_ok=True)

    def settle(rounds: int = 6, pause: float = 0.05) -> None:
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    captures: list[dict] = []

    def capture(name: str, note: str) -> None:
        settle()
        image = window.grabWindow()
        image.save(str(proto_out / f"{name}.png"))
        captures.append({"name": name, "note": note,
                         "width": image.width(), "height": image.height()})

    for width, height in RESOLUTIONS:
        window.setProperty("width", width)
        window.setProperty("height", height)
        capture(f"{proto.lower()}_default_{width}x{height}",
                "Isentropic Flow (default landing), dark theme")

    window.setProperty("currentPageIndex", 13)  # Rocket Performance
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    capture(f"{proto.lower()}_performance_1920x1080",
            "navigated to Rocket Performance, dark theme")
    window.setProperty("currentPageIndex", 0)

    report = {
        "prototype": proto,
        "captures": captures,
        "messages": messages,
        "warnings": [m for m in messages if m["kind"] in ("warning", "critical", "fatal", "qml-error")],
    }
    (proto_out / "capture_report.json").write_text(json.dumps(report, indent=2),
                                                    encoding="utf-8")
    print(f"[{proto}] {len(captures)} captures, {len(report['warnings'])} Qt warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
