"""Analysis Experience R2 implementation captures."""
from __future__ import annotations
import pathlib, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
BASE = ROOT / "acceptance" / "analysis_experience_r2_implementation"

def run(targets, outdir, w=1920, h=1080, theme="dark", populate=True):
    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQuick import QQuickWindow  # noqa: F401
    from PySide6.QtQml import QQmlComponent
    import main as app_main

    msgs = []
    def handler(kind, ctx, m):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            msgs.append(str(m))
    qInstallMessageHandler(handler)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=10, pause=0.02):
        for _ in range(rounds):
            app.processEvents(); time.sleep(pause); app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data" as Data\n'
        b'import "engine/model"\n'
        b'QtObject { property var nav: Data.Navigation\n'
        b'  property var obliqueC: ObliqueShock\n  property var thermoC: Thermochemistry\n'
        b'  property var perfC: RocketPerformance\n  property var fluidC: FluidProperties\n'
        b'  property var lineC: Line\n  property var study: TradeStudy\n'
        b'  property var engineM: EngineModel }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    nav = holder.property("nav")

    window.setProperty("appMode", "analysis")
    window.setProperty("width", w); window.setProperty("height", h)
    window.setProperty("themeMode", theme)
    settle()

    if populate:
        t = holder.property("thermoC")
        if t.property("providerAvailable"):
            t.calculate(); settle()
        holder.property("perfC").calculate(); settle()
        holder.property("fluidC").calculate(); settle()
        holder.property("lineC").calculate(); settle()
        holder.property("obliqueC").setDeflectionAndSolve(10.0); settle()
        s = holder.property("study")
        s.setVariableEnabled("area_ratio", False)
        s.setVariableRange("oxidiser_fuel_ratio", 2.6, 4.2, 6)
        s.runStudy()
        for _ in range(400):
            app.processEvents(); time.sleep(0.01)
            if not s.property("busy"): break
        settle()
        holder.property("engineM").loadDemo(); settle()

    out = BASE / outdir
    out.mkdir(parents=True, exist_ok=True)
    for key in targets:
        window.setProperty("appMode", "analysis")
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle()
        window.grabWindow().save(str(out / f"{key}_{theme}_{w}x{h}.png"))
        print("captured", key, theme, w, h)

    print(f"{len(msgs)} Qt warnings")
    for m in msgs[:10]:
        print("  ", m)
    return 0

if __name__ == "__main__":
    import json
    cfg = json.loads(sys.argv[1])
    sys.exit(run(cfg["targets"], cfg["outdir"],
                 cfg.get("w", 1920), cfg.get("h", 1080),
                 cfg.get("theme", "dark"), cfg.get("populate", True)))
