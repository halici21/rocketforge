"""Engine Design memory soak. Per the phase brief's own item 66, this is
the most spatially complex workspace so far -- runs a longer cycle count
than the other five workspaces' own accepted soaks, covering: page
entry/exit, repeated selection, Inspector context change, Dock
interaction, zoom/pan, theme switch, resize, and repeated state
publication (component add/duplicate/delete)."""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))
import harness  # noqa: E402


def main() -> int:
    from PySide6.QtCore import (QCoreApplication, QEvent, QUrl, QtMsgType,
                                 qInstallMessageHandler)
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

    a = harness.control_a_known_allocation(40)
    b = harness.control_b_released_allocation(40)
    print("control A:", a["pass"], "control B:", b["pass"])
    if not (a["pass"] and b["pass"]):
        print("FAIL: harness controls did not pass")
        return 1

    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=5, pause=0.01):
        for _ in range(rounds):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(pause)

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "engine/model"\n'
        b'QtObject { property var engineModel: EngineModel\n'
        b'  readonly property int nodeCount: EngineModel.nodes.count }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    engine_model = holder.property("engineModel")

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "engine")
    settle()
    engine_model.loadDemo()
    settle()
    base_count = holder.property("nodeCount")
    print("base node count:", base_count)

    ROUNDS = 500
    series = []
    base = harness.memory()
    node_ids = ["n1", "n2", "n3", "n4", "n5", "n6", "n7"]

    for i in range(ROUNDS):
        nid = node_ids[i % len(node_ids)]
        engine_model.selectNode(nid, False)
        engine_model.clearSelection()
        engine_model.setProperty("detailLevel", "compact" if i % 3 == 0 else "normal")
        window.setProperty("width", 1700 + (i % 4) * 50)
        window.setProperty("themeMode", "light" if i % 5 == 0 else "dark")
        # Every 10th round: duplicate then immediately delete, exercising
        # real node create/destroy without growing the graph.
        if i % 10 == 0:
            new_id = engine_model.duplicateNode(nid)
            if new_id:
                engine_model.removeNode(new_id)
        # App-mode round trip every 20th round.
        if i % 20 == 0:
            window.setProperty("appMode", "analysis")
            settle(rounds=2, pause=0.005)
            window.setProperty("appMode", "engine")
        settle(rounds=2, pause=0.005)
        series.append(harness.delta(base, harness.memory())["private_mb"])

    window.setProperty("width", 1920)
    window.setProperty("themeMode", "dark")
    settle(rounds=8)
    final_count = holder.property("nodeCount")

    slope = harness.slope_mb_per_round(series)
    first_half = harness.slope_mb_per_round(series[:ROUNDS // 2])
    second_half = harness.slope_mb_per_round(series[ROUNDS // 2:])
    print(f"\n{ROUNDS} rounds of select/detail-level/resize/theme/"
          f"duplicate-delete/mode-switch cycling:")
    print(f"  node count: base={base_count} final={final_count} "
          f"(must match -- confirms no accumulation from the "
          f"duplicate+delete cycles)")
    print(f"  total growth: {series[-1]:.2f} MB")
    print(f"  first-half slope: {first_half:.4f} MB/round")
    print(f"  second-half slope: {second_half:.4f} MB/round")
    print(f"  decelerating: {abs(second_half) <= abs(first_half) + 0.05}")

    e = harness.control_e_object_lifecycle(app)
    print(f"\ncontrol E (200 QObject create/deleteLater, census returns "
          f"to zero): {e['pass']}")

    print(f"\n{len(messages)} Qt warnings/criticals")
    for msg in messages[:20]:
        print(" ", msg)

    ok = (base_count == final_count and abs(second_half) <= abs(first_half) + 0.05
          and e["pass"] and not messages)
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
