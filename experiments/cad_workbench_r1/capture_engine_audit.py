"""Current-state audit capture for Engine Design, before any redesign.

Drives the real EngineModel (no fabrication): empty state, the demo engine
loaded, a selected component, a selected connection, and captures the
required resolution/theme matrix.
"""
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
        '    readonly property int nodeCount: EngineModel.nodes.count\n'
        '    readonly property int connectionCount: EngineModel.connections.count\n'
        '}\n'
    )
    probe = QQmlComponent(engine)
    probe.setData(probe_src.encode("utf-8"),
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    if holder is None:
        print("probe errors:", probe.errors())
        return 1
    engine_model = holder.property("engineModel")

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "engine")
    settle()
    window.grabWindow().save(str(OUT / "audit_empty_dark_1920x1080.png"))
    print("empty state: nodes =", holder.property("nodeCount"))

    engine_model.loadDemo()
    settle()
    for width, height in ((2560, 1440), (1920, 1080), (1366, 768)):
        window.setProperty("width", width)
        window.setProperty("height", height)
        settle()
        window.grabWindow().save(str(OUT / f"audit_populated_dark_{width}x{height}.png"))
    print("populated: nodes =", holder.property("nodeCount"),
          "connections =", holder.property("connectionCount"))

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("themeMode", "light")
    settle()
    window.grabWindow().save(str(OUT / "audit_populated_light_1920x1080.png"))
    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    settle()
    window.grabWindow().save(str(OUT / "audit_populated_light_1366x768.png"))
    window.setProperty("themeMode", "dark")
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()

    engine_model.selectNode("n5", False)
    settle()
    window.grabWindow().save(str(OUT / "audit_selected_component_dark_1920x1080.png"))

    engine_model.clearSelection()
    settle()
    engine_model.selectConnection("c1")
    settle()
    window.grabWindow().save(str(OUT / "audit_selected_connection_dark_1920x1080.png"))
    engine_model.clearSelection()
    settle()

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"\n{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
