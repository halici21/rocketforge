"""Captures the Option B (2.5D node rendering) spike, dark and light, for a
fair blind comparison against Option A (the accepted, improved 2D
EngineNode rendering, already captured with identical demo data)."""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "engine_design" / "comparison"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QtMsgType, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow

    messages = []

    def handler(kind, context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            messages.append(message)

    qInstallMessageHandler(handler)

    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    harness_path = pathlib.Path(__file__).parent / "Harness25D.qml"

    for theme in ("dark", "light"):
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("initialTheme", theme)
        engine.load(QUrl.fromLocalFile(str(harness_path)))
        roots = engine.rootObjects()
        if not roots:
            print("FAILED to load harness")
            for m in messages:
                print(" ", m)
            return 1
        window = roots[0]
        if not isinstance(window, QQuickWindow):
            print('root object type:', type(window))

        for _ in range(10):
            app.processEvents()
            time.sleep(0.02)

        window.grabWindow().save(str(OUT / f"option_b_2_5d_{theme}_1920x1080.png"))
        engine.deleteLater()

    print(f"\n{len(messages)} Qt warnings")
    for m in messages:
        print(" ", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
