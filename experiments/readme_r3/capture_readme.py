"""The README screenshot set after R3, from the current tree with real solves.

    .venv-cea\\Scripts\\python.exe experiments/readme_r3/capture_readme.py [out_dir] [name ...]

Ten captures at 1920x1080, each driven into a genuine solved or populated
state; every number on them comes from the solvers the application ships
with. The chemistry-backed workspaces need the production profile
(.venv-cea). It runs in a real, frameless window rather than offscreen, so
the Qt Quick 3D views render; the pointer is parked over the page header
before each capture, except for the hover peek, which places it on purpose.
`out_dir` defaults to docs/images/screenshots; names limit the run to those
captures.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "docs" / "images" / "screenshots"
ONLY = set(sys.argv[2:])

from PySide6.QtCore import (Q_ARG, QCoreApplication, QEvent, QMetaObject, QPoint, QPointF, Qt,
                            QtMsgType, QUrl, qInstallMessageHandler)
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtQml import QQmlComponent

import main as app_main

WARNINGS: list[str] = []
qInstallMessageHandler(lambda k, c, m: WARNINGS.append(str(m))
                       if k in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)

PROBE = """
import QtQuick
import RocketForge 1.0
import "%(ui)s/data" as Data
import "%(ui)s/engine/model"
QtObject {
    property var nav: Data.Navigation
    property var thermo: Thermochemistry
    property var perf: RocketPerformance
    property var nozzle: Nozzle
    property var isen: Isentropic
    property var study: TradeStudy
    property var em: EngineModel
    property var req: EngineRequirement
    property var trade: PropellantTrade
    property var sizing: ChamberSizing
    property var engines: ReferenceEngines
    // Selects the chamber by type: node ids are generated at load time.
    function selectRepresentativeNode() {
        for (var i = 0; i < EngineModel.nodes.count; ++i) {
            var n = EngineModel.nodes.get(i)
            if (n.type === "chamber") { EngineModel.selectNode(n.nodeId, false); return n.name }
        }
        return ""
    }
}
"""

# Where the pointer sits for the hover peek: on the chamber temperature plot,
# at O/F 3.000 once the plot has enlarged.
PEEK_POINT = (713, 420)


def main() -> int:
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(seconds=0.4):
        # DeferredDelete must be dispatched, or the previous page stays in the
        # item tree and a property lookup can land on it.
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.01)

    probe = QQmlComponent(engine)
    probe.setData((PROBE % {"ui": QUrl.fromLocalFile(str(app_main.UI_DIR)).toString()}).encode(),
                  QUrl.fromLocalFile(str(pathlib.Path(__file__).with_name("_probe.qml"))))
    for err in probe.errors():
        print("probe error:", err.toString())
    h = probe.create()
    nav = h.property("nav")

    # Frameless at the origin, so a 1080-high window is not clipped by the
    # title bar on a 1080p screen.
    window.setFlag(Qt.FramelessWindowHint, True)
    window.setPosition(0, 0)
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("themeMode", "dark")
    window.setProperty("appMode", "analysis")
    settle(1.0)

    def items():
        stack = [window.contentItem()]
        while stack:
            item = stack.pop()
            yield item
            stack.extend(item.childItems())

    def visible(item):
        return item.isVisible() and item.width() > 0 and item.height() > 0

    def by_class(prefix):
        return [i for i in items() if i.metaObject().className().startswith(prefix) and visible(i)]

    def item_with(prop):
        for item in items():
            meta = item.metaObject()
            index = meta.indexOfProperty(prop)
            if index >= 0 and meta.property(index).isWritable() and visible(item):
                return item
        return None

    def go(key, section=None, mode="analysis"):
        window.setProperty("appMode", mode)
        if key:
            window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle(1.0)
        if section is not None:
            item_with("section").setProperty("section", section)
            settle(1.0)

    def to_3d():
        # The switch's own signal: a synthesized click on it never returns
        # once the 3D view starts rendering.
        for switch in by_class("RFViewSwitch"):
            QMetaObject.invokeMethod(switch, "modeRequested", Q_ARG(str, "3d"))
        settle(3.0)

    def wait_busy(obj, limit=600):
        end = time.perf_counter() + limit
        settle(0.3)
        while obj.property("busy") and time.perf_counter() < end:
            settle(0.2)
        settle(0.5)

    def point_at(x, y):
        QCursor.setPos(window.mapToGlobal(QPoint(x, y)))
        settle(0.6)

    def want(name):
        return not ONLY or name in ONLY

    def shot(name, keep_pointer=False):
        if not keep_pointer:
            point_at(700, 60)
        settle(1.2)
        window.grabWindow().save(str(OUT / f"{name}.png"))
        print(f"  {name}")

    OUT.mkdir(parents=True, exist_ok=True)

    # ---- chamber and performance: LOX/LCH4, defaults, in vacuum ----------
    thermo, perf = h.property("thermo"), h.property("perf")
    if not thermo.property("providerAvailable"):
        print("!! no chemistry provider: run under .venv-cea")
        return 2
    thermo.calculate(); settle(1.0)
    perf.setProperty("ambientMode", "vacuum")
    perf.calculate(); settle(1.0)
    if want("rocket-performance-3d"):
        go("performance", 0); to_3d(); shot("rocket-performance-3d")

    # ---- Nozzle Lab: an internal normal shock ------------------------------
    h.property("nozzle").setProperty("backPressureRatio", 0.70); settle(0.5)
    if want("nozzle-lab-3d"):
        go("nozzlelab", 0); to_3d(); shot("nozzle-lab-3d")
    if want("nozzle-distribution-lens"):
        go("nozzlelab", 2)
        table = by_class("RFEngineeringTable")[0]
        QMetaObject.invokeMethod(table, "enterLens", Q_ARG("QVariant", 121), Q_ARG("QVariant", 134))
        settle(1.0)
        shot("nozzle-distribution-lens")

    # ---- Isentropic Flow at M = 2 -------------------------------------------
    h.property("isen").setMachAndSolve(2.0); settle(0.5)
    if want("isentropic-flow"):
        go("isentropic", 0); shot("isentropic-flow")

    # ---- Thermochemistry: the default 41-point O/F sweep --------------------
    if want("thermochemistry-sweep-peek") or want("thermochemistry-sweep-light"):
        thermo.runSweep(); wait_busy(thermo)
    if want("thermochemistry-sweep-peek"):
        go("thermochem", 2)
        point_at(*PEEK_POINT); settle(2.0)
        shot("thermochemistry-sweep-peek", keep_pointer=True)
    if want("thermochemistry-sweep-light"):
        window.setProperty("themeMode", "light"); settle(0.8)
        go("thermochem", 2); shot("thermochemistry-sweep-light")
        window.setProperty("themeMode", "dark"); settle(0.8)

    # ---- Trade Study: a second objective gives a Pareto front ---------------
    if want("trade-study-design-space"):
        study = h.property("study")
        study.addObjective("chamber_temperature", "minimize")
        study.runStudy(); wait_busy(study)
        print("     evaluated designs:", study.property("pointsEvaluated"))
        go("tradestudy", 2)
        item_with("mode").setProperty("mode", 1)      # Design space
        shot("trade-study-design-space")

    # ---- Liquid Engine: a 100 kN vacuum LOX/LCH4 chamber, sized -------------
    if want("thrust-chamber-sizing"):
        req, trade, sizing = h.property("req"), h.property("trade"), h.property("sizing")
        req.setThrust("100"); req.setBurnTime("400"); req.setPair("sutton-o2-ch4")
        req.setAmbientMode("vacuum")
        trade.setStudyPressure("10"); trade.setRatioMode("catalogue")
        trade.setPerformanceBasis("ideal_area_ratio"); trade.setAreaRatio("40")
        settle(0.5)
        trade.runTrade(); wait_busy(trade)
        trade.selectCandidate("sutton-o2-ch4"); settle(0.5)
        sizing.setAreaRatio(""); sizing.runSizing(); settle(1.5)
        go("chambersizing"); shot("thrust-chamber-sizing")

    # ---- Reference Engines: the J-2 at its 230,000 lb rating ----------------
    if want("reference-engines"):
        h.property("engines").selectConfiguration("CFG-J2-230K"); settle(0.8)
        go("engines"); shot("reference-engines")

    # ---- Engine Design: the demo topology, chamber selected -----------------
    if want("engine-design"):
        h.property("em").loadDemo(); settle(0.8)
        go(None, mode="engine")
        print("     selected:", h.selectRepresentativeNode())
        shot("engine-design")

    print("Qt warnings:", len(WARNINGS))
    for warning in WARNINGS[:12]:
        print("   ", warning[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
