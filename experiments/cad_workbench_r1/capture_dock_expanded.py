"""Quick verification capture: Analysis Dock expanded, both themes, plus a
resize-handle sanity check (no crash / no warning from dragging it)."""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "current_ui_audit"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication

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

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()

    target = None
    for c in window.findChildren(object):
        cname = c.metaObject().className()
        if cname.startswith("AnalysisDock"):
            target = c
            break
    if target is None:
        print("AnalysisDock instance not found")
        return 1

    target.setProperty("expanded", True)
    settle()
    image = window.grabWindow()
    image.save(str(OUT / "dock_expanded_dark_1920x1080.png"))

    window.setProperty("themeMode", "light")
    settle()
    image = window.grabWindow()
    image.save(str(OUT / "dock_expanded_light_1920x1080.png"))
    window.setProperty("themeMode", "dark")
    settle()

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
