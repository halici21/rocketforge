"""Opens a NOT_IMPLEMENTED component's placeholder workspace via the real
Inspector 'Open <type> workspace' button click."""
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

    def handler(kind, context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            messages.append(message)

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

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "engine/model"\n'
        b'QtObject { property var engineModel: EngineModel }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    engine_model = holder.property("engineModel")

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "engine")
    settle()
    engine_model.loadDemo()
    settle()
    engine_model.selectNode("n1", False)
    settle()
    window.grabWindow().save(str(OUT / "_tmp_before_click.png"))

    # Click the Inspector's "Open tank workspace" button.
    QTest.mouseClick(window, QtNS.MouseButton.LeftButton, QtNS.KeyboardModifier.NoModifier,
                      QPoint(1748, 368))
    settle(rounds=15, pause=0.03)
    window.grabWindow().save(str(OUT / "state_placeholder_workspace_dark_1920x1080.png"))
    print("saved")

    warnings = messages
    print(f"\n{len(warnings)} Qt warnings")
    for m in warnings:
        print(" ", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
