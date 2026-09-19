"""Follow-up captures from the rf-visual-qa pass: things a static before/after
screenshot set cannot prove on its own.

1. Selection persistence across an axis switch -- select a point, switch X,
   confirm the same logical point (by index) still carries the gold ring at
   its new projected position, not silently dropped or stuck at the old
   pixel location.
2. The hover tooltip actually renders real content (never captured live).
3. Legibility at a count close to MAX_STUDY_POINTS (20000), not just 2460.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "tradestudy" / "after"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

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

    def settle(rounds=8, pause=0.02):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject { property var thermoC: Thermochemistry\n'
        b'  property var perfC: RocketPerformance\n'
        b'  property var study: TradeStudy\n'
        b'  property int idx: Navigation.indexOfKey("tradestudy") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    thermoC = holder.property("thermoC")
    perfC = holder.property("perfC")
    study = holder.property("study")

    if not thermoC.property("providerAvailable"):
        print("no thermochemistry provider")
        return 0

    thermoC.calculate(); settle()
    perfC.calculate(); settle()
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    study.addObjective("chamber_temperature", "minimize")
    settle()
    study.runStudy()
    for _ in range(400):
        app.processEvents()
        time.sleep(0.01)
        if not study.property("busy"):
            break
    settle()
    study.showTab(2)
    settle()

    # -- 1. selection persists across an axis switch -----------------------
    study.toggleSelection(3)
    settle(rounds=10, pause=0.02)
    window.grabWindow().save(str(OUT / "state_selection_before_axis_switch.png"))
    options = study.property("objectiveAxisOptions")
    keys = [o["key"] for o in options] if options else []
    other_key = next((k for k in keys if k != study.property("paretoX")), None)
    print("switching X from", study.property("paretoX"), "to", other_key)
    study.setProperty("paretoX", other_key)
    settle(rounds=10, pause=0.02)
    window.grabWindow().save(str(OUT / "state_selection_after_axis_switch.png"))
    selected_now = study.property("selectedIndices")
    print("selectedIndices after axis switch:", list(selected_now))
    study.toggleSelection(3)
    settle()

    # -- 2. hover tooltip actually renders ----------------------------------
    # QTest drives real pointer events through Qt Quick's scene graph (a
    # raw QMouseEvent posted to the window does not reliably reach a
    # PointerHandler); RFTooltip also has a 420ms show delay, so the settle
    # after moving the mouse must exceed that.
    from PySide6.QtTest import QTest
    from PySide6.QtCore import QPoint

    target = QPoint(627, 507)  # a marker's approximate screen position
    QTest.mouseMove(window, target)
    for _ in range(20):
        app.processEvents()
        time.sleep(0.03)
    window.grabWindow().save(str(OUT / "state_hover_tooltip.png"))

    # -- 3. legibility near MAX_STUDY_POINTS --------------------------------
    study.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 41)
    study.setVariableRange("area_ratio", 10.0, 80.0, 400)
    settle()
    planned = study.property("pointCount")
    print("planned points near cap:", planned)
    study.runStudy()
    for _ in range(4000):
        app.processEvents()
        time.sleep(0.005)
        if not study.property("busy"):
            break
    settle(rounds=20, pause=0.03)
    study.showTab(2)
    settle(rounds=20, pause=0.03)
    window.grabWindow().save(str(OUT / "state_near_cap_dataset_dark_1920x1080.png"))
    print("actual points near cap:", study.property("visibleRowCount"))

    print(f"\n{len(messages)} Qt warnings/criticals")
    for msg in messages:
        print(" ", msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
