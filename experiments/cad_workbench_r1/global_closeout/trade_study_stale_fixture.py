"""Global closeout section 9: Trade Study stale-state fixture, driven live.

Evaluate a study, preserve the result, change a chemistry-affecting design
variable WITHOUT re-evaluating, and confirm: old result stays tied to the
old definition, resultStale becomes explicit, and (this is the point of the
fixture) the Trade tab (Sweep/Design-space) and the Selected Design
Inspector -- which previously had zero resultStale wiring -- now show the
"Setup changed" chip too. Then recalculate and confirm it clears.
"""
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
    from PySide6.QtQuick import QQuickWindow  # noqa: F401  (wakes up window type resolution)
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

    probe_lines = [
        'import QtQuick',
        'import RocketForge 1.0',
        'import "data" as Data',
        'QtObject {',
        '    property var study: TradeStudy',
        '    property int tradeStudyIndex: Data.Navigation.indexOfKey("tradestudy")',
        '}',
        '',
    ]
    probe_src = "\n".join(probe_lines)
    probe = QQmlComponent(engine)
    probe.setData(probe_src.encode("utf-8"),
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    if holder is None:
        print("probe errors:", probe.errors())
        return 1
    study = holder.property("study")
    trade_study_index = holder.property("tradeStudyIndex")
    print("tradeStudyIndex =", trade_study_index)

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("appMode", "analysis")
    settle()

    # Only oxidiser_fuel_ratio enabled (chemistry-affecting), small point count.
    study.setVariableEnabled("area_ratio", False)
    study.setVariableRange("oxidiser_fuel_ratio", 2.6, 4.2, 6)
    settle()

    def run_and_wait(label):
        study.runStudy()
        for _ in range(400):
            app.processEvents()
            time.sleep(0.01)
            if not study.property("busy"):
                break
        settle()
        print(label, "busy=", study.property("busy"),
              "hasResult=", study.property("hasResult"),
              "resultStale=", study.property("resultStale"),
              "pointCount=", study.property("pointCount"))

    run_and_wait("after first run")

    window.setProperty("currentPageIndex", trade_study_index)
    settle()
    study.requestTab.emit(2)
    settle()
    try:
        study.toggleSelection(0)
    except Exception as exc:  # noqa: BLE001
        print("toggleSelection(0) failed:", exc)
    settle()

    window.grabWindow().save(str(OUT / "tradestudy_trade_fresh_dark_1920x1080.png"))

    # Now change a chemistry-affecting variable WITHOUT re-running.
    study.setVariableRange("oxidiser_fuel_ratio", 2.8, 4.4, 6)
    settle()
    print("after edit, before rerun: resultStale=", study.property("resultStale"),
          "pointCount(old)=", study.property("pointCount"))

    # Force a relayout pass (RowLayout can lag a visibility flip by one polish
    # cycle in the offscreen backend) before trusting the grab.
    window.setProperty("width", 1921)
    settle(20, 0.03)
    window.setProperty("width", 1920)
    settle(20, 0.03)

    from PySide6.QtCore import QObject as _QO
    chip = window.findChild(_QO, "tradeStaleChip")
    if chip is not None:
        # Walk up mapToItem against the window root to get an absolute position.
        try:
            abs_pos = chip.mapToItem(window, 0, 0)
            print("chip abs pos:", abs_pos)
        except Exception as exc:
            print("mapToItem failed:", exc)
        print("chip found: visible=", chip.property("visible"),
              "width=", chip.property("width"),
              "x=", chip.property("x"), "y=", chip.property("y"),
              "opacity=", chip.property("opacity"),
              "text=", chip.property("text"))
        parent_item = chip.parent()
        depth = 0
        while parent_item is not None and depth < 8:
            try:
                w = parent_item.property("width")
                x = parent_item.property("x")
                oname = parent_item.objectName()
            except Exception:
                w = x = oname = None
            print("  parent[%d]" % depth, type(parent_item).__name__, "objectName=", oname, "x=", x, "width=", w)
            parent_item = parent_item.parent()
            depth += 1
    else:
        print("chip NOT FOUND by objectName")
    inspector_drawer = window.findChild(_QO, "inspectorDrawerRoot")
    print("inspectorOpen probe via findChild inspectorDrawerRoot:", inspector_drawer)
    print("window width=", window.property("width"), "height=", window.property("height"))

    window.grabWindow().save(str(OUT / "tradestudy_trade_stale_dark_1920x1080.png"))

    # Recalculate and confirm stale clears.
    run_and_wait("after second run")
    window.grabWindow().save(str(OUT / "tradestudy_trade_recalculated_dark_1920x1080.png"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
