"""Current-state audit capture for Line, before any redesign."""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "line"
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
        b'QtObject { property var line: Line\n'
        b'  property int idx: Navigation.indexOfKey("line") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    line = holder.property("line")
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    if not line.property("providerAvailable"):
        print("no fluid-properties provider -- capturing unavailable state only")
        window.setProperty("width", 1920)
        window.setProperty("height", 1080)
        settle()
        window.grabWindow().save(str(OUT / "audit_no_provider_1920x1080.png"))
        return 0

    line.calculate()
    settle()
    for width, height in ((2560, 1440), (1920, 1080), (1366, 768)):
        window.setProperty("width", width)
        window.setProperty("height", height)
        settle()
        window.grabWindow().save(str(OUT / f"audit_default_{width}x{height}.png"))

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("themeMode", "light")
    settle()
    window.grabWindow().save(str(OUT / "audit_default_light_1920x1080.png"))
    window.setProperty("themeMode", "dark")

    print("default case rows:")
    for row in line.property("resultRows"):
        print(f"  {row['label']:35s} {row['value']:>15s} {row['unit']}")
    print("flow regime:", line.property("flowRegime"))

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
