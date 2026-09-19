"""The curated README screenshot set, from the current tree with real data.

Ten captures, each driven into a genuine solved or populated state. No mock
results are substituted anywhere: every number on these images comes from the
same solvers the application ships with, and the chemistry-backed workspaces
require the production profile (.venv-cea) to render their real values.
"""
from __future__ import annotations
import pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "images" / "screenshots"

from PySide6.QtCore import (QUrl, QtMsgType, qInstallMessageHandler,
                            QCoreApplication, QEvent)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow  # noqa: F401
from PySide6.QtQml import QQmlComponent
import main as app_main

WARNINGS = []
qInstallMessageHandler(lambda k, c, m: WARNINGS.append(str(m))
                       if k in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg)
                       else None)


def find_prop(obj, name, depth=0):
    if obj is None or depth > 16:
        return None
    try:
        idx = obj.metaObject().indexOfProperty(name)
    except Exception:
        idx = -1
    if idx >= 0 and obj.metaObject().property(idx).isWritable():
        return obj
    for c in obj.children():
        hit = find_prop(c, name, depth + 1)
        if hit is not None:
            return hit
    return None


def main() -> int:
    theme = sys.argv[1] if len(sys.argv) > 1 else "dark"
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 1920
    height = int(sys.argv[3]) if len(sys.argv) > 3 else 1080
    suffix = "" if (theme == "dark" and width == 1920) else "-%s%s" % (
        theme if theme != "dark" else "", "" if width == 1920 else "-1366")
    suffix = suffix.strip("-")
    suffix = ("-" + suffix) if suffix else ""

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(n=14):
        # DeferredDelete must be dispatched or the PREVIOUS page stays in the
        # object tree, and find_prop() then resolves `section` on the page we
        # just navigated away from -- which produced a "Study" capture showing
        # the Calculator tab.
        for _ in range(n):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.02)
            app.processEvents()

    probe = QQmlComponent(engine)
    probe.loadUrl(QUrl.fromLocalFile(
        str(ROOT / 'experiments' / 'analysis_experience_r2' / '_readme_probe.qml')))
    for err in probe.errors():
        print('probe error:', err.toString())
    h = probe.create()
    nav = h.property("nav")

    window.setProperty("width", width); window.setProperty("height", height)
    window.setProperty("themeMode", theme)
    window.setProperty("appMode", "analysis")
    settle()

    # ---- real data everywhere -----------------------------------------
    thermo = h.property("thermo")
    if thermo.property("providerAvailable"):
        thermo.calculate(); settle()
    else:
        print("!! no chemistry provider — run under .venv-cea"); return 2
    h.property("perf").calculate(); settle()
    h.property("fluid").calculate(); settle()
    h.property("line").calculate(); settle()
    h.property("oblique").setDeflectionAndSolve(10.0); settle()

    study = h.property("study")

    def run_study():
        study.runStudy()
        for _ in range(1500):
            app.processEvents(); time.sleep(0.01)
            if not study.property("busy"):
                break
        settle()

    # The Sweep view answers "how does the system respond as ONE variable
    # changes", and correctly refuses when more than one varies. So the two
    # Trade Study captures need two different studies, not two tabs of one.
    def configure_sweep():
        study.setVariableEnabled("area_ratio", False)
        study.setVariableRange("oxidiser_fuel_ratio", 2.6, 4.2, 9)
        run_study()

    def configure_design_space():
        study.addObjective("thrust_coefficient", "maximize")
        study.setVariableEnabled("area_ratio", True)
        study.setVariableRange("area_ratio", 20.0, 80.0, 5)
        study.setVariableRange("oxidiser_fuel_ratio", 2.6, 4.2, 6)
        run_study()

    configure_sweep()
    h.property("em").loadDemo(); settle()

    OUT.mkdir(parents=True, exist_ok=True)

    def shot(name, key, section=None, mode="analysis", extra=None):
        window.setProperty("appMode", mode)
        if key:
            window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle()
        if section is not None:
            page = find_prop(window, "section")
            if page is not None:
                page.setProperty("section", section)
                settle()
        if extra is not None:
            extra()
            settle()
        path = OUT / ("%s%s.png" % (name, suffix))
        window.grabWindow().save(str(path))
        print("  %-30s %s" % (name + suffix, path.name))

    def study_sub(index):
        # StudyTrade exposes its Sweep / Design space choice as `mode`.
        def go():
            sub = find_prop(window, "mode")
            if sub is not None:
                sub.setProperty("mode", index)
        return go

    shot("analysis-overview", "home")
    shot("isentropic-flow", "isentropic", 0)          # Relation
    shot("oblique-shock-study", "obliqueshock", 1)    # Study
    shot("nozzle-lab", "nozzlelab", 1)                # Operating point
    shot("thermochemistry", "thermochem")
    shot("rocket-performance", "performance")
    shot("trade-study", "tradestudy", 2, extra=study_sub(0))          # Sweep
    configure_design_space()
    shot("trade-study-design-space", "tradestudy", 2, extra=study_sub(1))
    shot("fluid-properties", "fluidproperties")
    shot("engine-design", None, mode="engine",
         extra=lambda: print("     selected:", h.selectRepresentativeNode()))

    print("Qt warnings:", len(WARNINGS))
    for w in WARNINGS[:5]:
        print("   ", w[:140])
    return 0


if __name__ == "__main__":
    sys.exit(main())
