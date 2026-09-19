"""Verify whether Engine Design's demo-engine clipping at 1366x768, flagged
by the independent design review, is a NEW regression or the already-
investigated/accepted "resize after wide load, no auto-refit" condition
from the Engine Design phase's own audit -- by loading natively AT 1366,
not resizing into it after a wider-resolution load."""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "global_closeout" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickWindow  # noqa: F401
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=10, pause=0.02):
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

    # Native load: size set FIRST, then switch to engine mode and load demo.
    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    window.setProperty("appMode", "engine")
    settle()
    engine_model.loadDemo()
    settle()
    window.grabWindow().save(str(OUT / "engine_native_1366_after_load.png"))
    print("native 1366 load captured")

    return 0


if __name__ == "__main__":
    sys.exit(main())
