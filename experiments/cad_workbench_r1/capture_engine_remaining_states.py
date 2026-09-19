"""Captures the two states rf-visual-qa's own canonical matrix names for
Engine Design that were not yet captured: a disabled ("unavailable")
component, and a NOT_IMPLEMENTED component's placeholder workspace opened
for real (not just read from source)."""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "engine_design" / "before"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

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

    probe_src = (
        'import QtQuick\n'
        'import RocketForge 1.0\n'
        'import "engine/model"\n'
        'QtObject {\n'
        '    property var engineModel: EngineModel\n'
        '}\n'
    )
    probe = QQmlComponent(engine)
    probe.setData(probe_src.encode("utf-8"),
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    engine_model = holder.property("engineModel")

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "engine")
    settle()
    engine_model.loadDemo()
    settle()

    # -- disabled ("unavailable") component ---------------------------------
    engine_model.setNodeEnabled("n2", False)  # Fuel Pump
    settle()
    window.grabWindow().save(str(OUT / "state_disabled_component_dark_1920x1080.png"))
    print("disabled component captured")

    # -- open a NOT_IMPLEMENTED component's placeholder workspace ----------
    # n1 = Fuel Tank (type "tank", workspace "placeholder").
    engine_model.selectNode("n1", False)
    settle()
    # Double-click equivalent: call the same function EngineCanvas.qml's
    # own double-tap handler calls.
    engine_model.selectNode("n1", False)
    settle()
    # Use the Inspector's own "Open <type> workspace" action path by
    # invoking the workspace-open function the canvas exposes indirectly
    # through EngineWorkspace -- simplest reliable route here is calling
    # the same requestNodeMenu-independent path: EngineModel has no direct
    # "open workspace" function (that lives on EngineWorkspace/EngineCanvas
    # QML, not the singleton), so drive it via a real double-click at n1's
    # known canvas position instead.
    from PySide6.QtTest import QTest
    from PySide6.QtCore import QPoint, Qt as QtNS
    QTest.mouseDClick(window, QtNS.MouseButton.LeftButton, QtNS.KeyboardModifier.NoModifier,
                       QPoint(133, 178))
    settle(rounds=15, pause=0.03)
    window.grabWindow().save(str(OUT / "state_placeholder_workspace_dark_1920x1080.png"))
    print("placeholder workspace captured")

    engine_model.setNodeEnabled("n2", True)
    settle()

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"\n{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
