"""Load the demo engine while the window is ALREADY at 1366x768 -- the more
realistic case for whether the 1366 floor is usable, versus resizing after
loading at a wider size."""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "engine_design" / "before"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler, QPoint
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent
    from PySide6.QtTest import QTest
    from PySide6.QtCore import Qt as QtNS

    import main as app_main

    messages = []
    kinds = {QtMsgType.QtWarningMsg: "warning", QtMsgType.QtCriticalMsg: "critical",
             QtMsgType.QtFatalMsg: "fatal"}

    def handler(kind, context, message):
        if kind in kinds:
            messages.append((kinds[kind], message))

    qInstallMessageHandler(handler)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=10, pause=0.03):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    window.setProperty("appMode", "engine")
    settle()
    window.grabWindow().save(str(OUT / "audit_empty_dark_1366x768.png"))

    # Click "Load demo engine" -- the button position at 1366x768 (centered
    # in the canvas region, which is narrower here than at 1920).
    QTest.mouseClick(window, QtNS.MouseButton.LeftButton, QtNS.KeyboardModifier.NoModifier,
                      QPoint(652, 446))
    settle(rounds=15, pause=0.03)
    window.grabWindow().save(str(OUT / "audit_populated_native_1366x768.png"))

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"\n{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
