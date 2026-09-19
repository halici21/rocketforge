"""Verify the Engine Design 1366 clipping finding by driving the REAL
"Load demo engine" button (QTest.mouseClick), not calling
EngineModel.loadDemo() directly from Python -- the direct-call bypasses the
button's own onClicked handler, which (confirmed by reading source) always
calls canvas.fitAll() right after loading. If the clipping disappears when
driven through the real button, the independent review's BLOCKING finding
was a test-harness artifact, not a reachable product defect."""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "global_closeout" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QUrl, Qt, QPoint
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickWindow  # noqa: F401
    from PySide6.QtTest import QTest

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

    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    window.setProperty("appMode", "engine")
    settle()
    window.grabWindow().save(str(OUT / "engine_native_1366_empty_before_click.png"))

    # The empty-state "Load demo engine" button, centered in the canvas.
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(652, 446))
    settle(rounds=15, pause=0.03)
    window.grabWindow().save(str(OUT / "engine_native_1366_after_real_button.png"))
    print("captured via real button click")

    return 0


if __name__ == "__main__":
    sys.exit(main())
