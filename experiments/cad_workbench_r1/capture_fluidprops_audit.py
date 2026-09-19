"""Current-state audit capture for Fluid Properties, before any redesign."""
from __future__ import annotations

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
        b'  property int idx: Navigation.indexOfKey("fluidproperties") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    fp = holder.property("fp")
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    if not fp.property("providerAvailable"):
        print("no fluid-properties provider -- capturing unavailable state only")
        window.setProperty("width", 1920)
        window.setProperty("height", 1080)
        settle()
        window.grabWindow().save(str(OUT / "audit_no_provider_1920x1080.png"))
        return 0

    fp.calculate()
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
    for row in fp.property("resultRows"):
        print(f"  {row['label']:25s} {row['value']:>15s} {row['unit']:12s} "
              f"available={row['available']} status={row['status']!r}")
    print("phase:", fp.property("phase"))
    print("statusLabel:", fp.property("statusLabel"))
    print("statusTone:", fp.property("statusTone"))
    print("provenance rows:")
    for row in fp.property("provenanceRows"):
        print(f"  {row['label']:35s} {row['value']}")
    print("diagnostic rows:")
    for row in fp.property("diagnosticRows"):
        print(f"  {row['severity']:8s} {row['code']:35s} {row['message']}")

    warnings = [m for m in messages if m[0] in ("warning", "critical", "fatal")]
    print(f"{len(warnings)} Qt warnings")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
