"""Every view-state change this program introduced must cost zero solves.

The phases moved default tabs, added a sweep drawer, added a nozzle object,
promoted heroes and changed table widths. All of those are presentation. If
any of them re-enters a solver, the workspace is no longer showing the result
the user asked for -- it is showing a new one computed as a side effect of
looking at it.
"""
from __future__ import annotations
import pathlib, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow  # noqa: F401
from PySide6.QtQml import QQmlComponent
import main as app_main

CALLS = {}


def instrument():
    """Count calls into the real solve entry points, then call through."""
    import rocketforge.application.analysis.nozzle_service as nozzle_service
    import rocketforge.application.analysis.thermochemistry_service as thermo
    import rocketforge.application.analysis.performance_service as perf
    import rocketforge.application.analysis.line_service as line
    import rocketforge.application.analysis.fluid_property_service as fluid

    targets = [
        # Nozzle Lab is where this program changed the most, so all four of
        # its entry points are watched, not just the calculator's: the object
        # added in Phase 5 reads contourSeries/markers, and a sweep re-entered
        # by a tab switch would be exactly the defect this gate exists for.
        (nozzle_service, "solve"),
        (nozzle_service, "solve_record"),
        (nozzle_service, "back_pressure_sweep"),
        (nozzle_service, "shock_position_sweep"),
        (thermo, "solve_case"),
        (perf, "solve_performance"),
        (line, "solve_case"),
        (fluid, "evaluate_case"),
    ]
    missing = [n for m, n in targets if getattr(m, n, None) is None]
    if missing:
        raise SystemExit("solve entry points not found, so this gate would "
                         "silently watch nothing: " + ", ".join(missing))
    for module, name in targets:
        original = getattr(module, name)
        key = module.__name__.split(".")[-1] + "." + name

        def wrapper(*a, _o=original, _k=key, **kw):
            CALLS[_k] = CALLS.get(_k, 0) + 1
            return _o(*a, **kw)

        setattr(module, name, wrapper)
        CALLS.setdefault(key, 0)


def find_with_property(obj, name, depth=0):
    if obj is None or depth > 14:
        return None
    try:
        idx = obj.metaObject().indexOfProperty(name)
    except Exception:
        idx = -1
    if idx >= 0 and obj.metaObject().property(idx).isWritable():
        return obj
    for child in obj.children():
        hit = find_with_property(child, name, depth + 1)
        if hit is not None:
            return hit
    return None


def main() -> int:
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(n=12):
        for _ in range(n):
            app.processEvents(); time.sleep(0.02); app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data" as Data\n'
        b'QtObject { property var nav: Data.Navigation\n'
        b'  property var nozzle: Nozzle; property var oblique: ObliqueShock\n'
        b'  property var isen: Isentropic; property var fluid: FluidProperties }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe_parity.qml")))
    holder = probe.create()
    nav = holder.property("nav")

    window.setProperty("width", 1920); window.setProperty("height", 1080)
    window.setProperty("themeMode", "dark"); window.setProperty("appMode", "analysis")
    settle()

    # Solve everything FIRST, then start counting: the baseline state is a
    # solved workspace, exactly as a reader would leave it.
    holder.property("fluid").calculate(); settle()
    holder.property("oblique").setDeflectionAndSolve(10.0); settle()
    for key in ("nozzlelab", "isentropic", "fluidproperties", "obliqueshock"):
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle()

    instrument()
    before = dict(CALLS)
    actions = []

    def act(label, fn):
        fn()
        settle()
        actions.append(label)

    # --- Phase 1: the default-view inversion and every tab it reordered ---
    for key in ("isentropic", "massflow", "normalshock", "prandtlmeyer",
                "fanno", "rayleigh", "nozzlelab", "obliqueshock"):
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle()
        page = find_with_property(window, "section")
        if page is None:
            continue
        for section in range(4):
            act("%s section=%d" % (key, section),
                lambda p=page, s=section: p.setProperty("section", s))

    # --- Phase 1: the Oblique Shock sweep drawer ---
    window.setProperty("currentPageIndex", nav.indexOfKey("obliqueshock"))
    settle()
    page = find_with_property(window, "section")
    page.setProperty("section", 1); settle()
    drawer = find_with_property(window, "tableOpen")
    if drawer is not None:
        act("oblique drawer open", lambda: drawer.setProperty("tableOpen", True))
        act("oblique drawer close", lambda: drawer.setProperty("tableOpen", False))

    # --- Phase 2: the chart quantity selector ---
    window.setProperty("currentPageIndex", nav.indexOfKey("isentropic"))
    settle()
    qpage = find_with_property(window, "quantityIndex")
    if qpage is not None:
        for i in range(4):
            act("isentropic quantity=%d" % i,
                lambda n=i: qpage.setProperty("quantityIndex", n))
    lpage = find_with_property(window, "logScale")
    if lpage is not None:
        act("isentropic log off", lambda: lpage.setProperty("logScale", False))
        act("isentropic log on", lambda: lpage.setProperty("logScale", True))

    # --- Phase 6: theme, which repaints every chart ---
    act("theme light", lambda: window.setProperty("themeMode", "light"))
    act("theme dark", lambda: window.setProperty("themeMode", "dark"))

    # --- Closure: the responsive transition across the compact breakpoint.
    # Nozzle Lab rebuilds its whole Solution grammar here -- four groups
    # abreast, stacked cells, an inlined hero -- so if any of that reached a
    # solver, this is where it would show.
    window.setProperty("currentPageIndex", nav.indexOfKey("nozzlelab"))
    settle()
    page = find_with_property(window, "section")
    if page is not None:
        page.setProperty("section", 1)
        settle()
    for w, h, label in ((1366, 768, "compact"), (1920, 1080, "roomy"),
                        (1366, 768, "compact again"), (2560, 1440, "large")):
        act("resize to %s (%dx%d)" % (label, w, h),
            lambda ww=w, hh=h: (window.setProperty("width", ww),
                                window.setProperty("height", hh)))

    after = dict(CALLS)
    delta = {k: after.get(k, 0) - before.get(k, 0) for k in after}
    total = sum(delta.values())

    print("view-state actions driven:", len(actions))
    for name, count in sorted(delta.items()):
        print("  %-42s %d" % (name, count))
    print("total solve calls during view-state changes:", total)

    if total != 0:
        print("FAIL: a presentation change re-entered a solver")
        return 1

    # Negative control: the counter must be able to see a real solve.
    holder.property("fluid").calculate()
    settle()
    control = sum(CALLS.values()) - sum(after.values())
    print("negative control (one real evaluate):", control, "call(s)")
    if control < 1:
        print("FAIL: the counter cannot detect a solve, so zero proves nothing")
        return 1

    print("PASS: zero solves from view state, and the counter is live")
    return 0


if __name__ == "__main__":
    sys.exit(main())
