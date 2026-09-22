"""Render the Thermochemistry workspace in solid mode and save screenshots.

Captures are taken and then actually looked at -- a passing test suite is not a
visual pass, and this project has shipped a completely empty result rail that a
field-level parity check reported as clean.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "solid_propellant_r1" / "captures"


def find_with_property(obj, name, depth=0):
    if obj is None or depth > 14:
        return None
    try:
        idx = obj.metaObject().indexOfProperty(name)
    except Exception:
        idx = -1
    if idx >= 0:
        return obj
    for child in obj.children():
        hit = find_with_property(child, name, depth + 1)
        if hit is not None:
            return hit
    return None


def main() -> int:
    from PySide6.QtCore import QEvent, QCoreApplication, QUrl, QtMsgType
    from PySide6.QtCore import qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent
    from PySide6.QtQuick import QQuickWindow  # noqa: F401  (required for grabWindow)

    import main as app_main

    warnings: list[str] = []
    qInstallMessageHandler(
        lambda kind, ctx, msg: warnings.append(str(msg))
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=14):
        """Let Qt finish, including deferred deletes.

        ``processEvents`` alone does not deliver ``DeferredDelete``; Qt holds
        those until the loop unwinds to the level that posted them, which a
        scripted run never does. Dispatching them explicitly is what makes a
        scripted capture show the same thing an interactive session would.
        """
        for _ in range(rounds):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.02)
            app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data" as Data\n'
        b'QtObject { property var nav: Data.Navigation;'
        b' property var thermo: Thermochemistry }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_solid_probe.qml")))
    holder = probe.create()
    if holder is None:
        print("!! probe failed:", probe.errorString())
        return 1
    nav = holder.property("nav")
    thermo = holder.property("thermo")
    return capture(window, nav, thermo, settle, warnings)


def capture(window, nav, thermo, settle, warnings) -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    window.setProperty("appMode", "analysis")
    index = nav.indexOfKey("thermochem")
    if index is None or index < 0:
        print("!! thermochem page not found in navigation")
        return 1
    window.setProperty("currentPageIndex", index)
    settle()

    # The workspace is tabbed; land on the Calculator, which is where the
    # formulation editor lives.
    page = find_with_property(window, "section")
    if page is not None:
        page.setProperty("section", 0)     # Calculator: the formulation editor
        settle()
    print(f"page index {index}, section "
          f"{page.property('section') if page is not None else 'n/a'}")

    shots = []

    def shoot(name, w, h, theme):
        window.setProperty("width", w)
        window.setProperty("height", h)
        window.setProperty("themeMode", theme)
        settle()
        path = OUT / f"{name}_{theme}_{w}x{h}.png"
        window.grabWindow().save(str(path))
        shots.append(path)
        print(f"  {path.name}")

    # 1. bipropellant, untouched: the existing workspace must be unchanged.
    thermo.setProperty("formulationKind", "bipropellant")
    settle()
    call(thermo, "calculate")
    settle()
    print(f"bipropellant Tc row: {thermo.property('resultHeadline')}")
    shoot("bipropellant_solved", 1920, 1080, "dark")

    # 2. solid, the published case, before solving.
    thermo.setProperty("formulationKind", "solid")
    settle()
    print(f"solid formulation  : {thermo.property('solidFormulationLabel')}"
          f" | total {thermo.property('solidMassTotalText')}")
    shoot("solid_unsolved", 1920, 1080, "dark")

    # 3. solid, solved.
    call(thermo, "calculate")
    settle()
    print(f"solid headline     : {thermo.property('resultHeadline')}")
    shoot("solid_solved", 1920, 1080, "dark")
    shoot("solid_solved", 1366, 768, "dark")
    shoot("solid_solved", 1920, 1080, "light")

    # The composition tab: gas and condensed products, kept in separate states.
    if page is not None:
        page.setProperty("section", 1)
        settle()
        shoot("solid_composition", 1920, 1080, "dark")
        page.setProperty("section", 0)
        settle()

    # 4. section 27 stale fixture: solved Example 5, then AP edited and NOT
    #    recalculated. The result must stay, dimmed and labelled stale, and the
    #    condition rail must still show the solved 72.060 %.
    call(thermo, "setSolidMassPercent", 0, 73.06)
    settle()
    print(f"stale fixture      : stale={thermo.property('resultStale')}"
          f" form total {thermo.property('solidMassTotalText')}")
    shoot("solid_stale", 1920, 1080, "dark")

    # 5. solving the unbalanced grain: refused, not normalised.
    call(thermo, "calculate")
    settle()
    shoot("solid_refused", 1920, 1080, "dark")

    # 6. grain temperature the binder cannot follow: a warning, stated.
    call(thermo, "resetSolidFormulation")
    settle()
    thermo.setProperty("solidGrainTemperature", 320.0)
    settle()
    call(thermo, "calculate")
    settle()
    print(f"320 K status       : {thermo.property('statusKind')}")
    shoot("solid_assigned_enthalpy_warning", 1920, 1080, "dark")

    # 7. a refused c*, from CEA's real non-converged frozen solve: the
    #    chamber result stands, and c* says "Not available" with the reason.
    from rocketforge.application.analysis import thermochemistry_solid_service as svc
    original = svc.solve_solid_equilibrium_cstar
    svc.solve_solid_equilibrium_cstar = _refused_cstar
    try:
        call(thermo, "resetSolidFormulation")
        settle()
        call(thermo, "calculate")
        settle()
        print(f"refused c*         : available="
              f"{thermo.property('solidCStarAvailable')}")
        shoot("solid_cstar_refused", 1920, 1080, "dark")
    finally:
        svc.solve_solid_equilibrium_cstar = original

    # 8. an added ingredient, at 0 %.
    call(thermo, "resetSolidFormulation")
    settle()
    call(thermo, "addSolidIngredient", "B(b)")
    settle()
    shoot("solid_ingredient_added", 1920, 1080, "dark")
    call(thermo, "resetSolidFormulation")
    settle()

    interesting = [w for w in warnings
                   if "solid" in w.lower() or "Thermochemistry" in w
                   or "ThermoCalculator" in w]
    print(f"\nQt warnings total: {len(warnings)}"
          f"   relevant: {len(interesting)}")
    for w in interesting[:15]:
        print("   !", w)
    print(f"\n{len(shots)} captures -> {OUT}")
    return 0


def _refused_cstar(request, chamber):
    """The real refusal: CEA forced frozen from the chamber, which for this
    grain does not converge yet still returns a number."""
    import cea

    from rocketforge.providers.cea_solid import solve_solid_equilibrium_cstar

    class Frozen:
        def __init__(self, real):
            self.real = real

        def solve(self, *a, **kw):
            kw["n_frz"] = 1
            return self.real.solve(*a, **kw)

    class FreezingCEA:
        def __getattr__(self, name):
            return getattr(cea, name)

        def RocketSolver(self, *a, **kw):  # noqa: N802
            return Frozen(cea.RocketSolver(*a, **kw))

        def RocketSolution(self, solver):  # noqa: N802
            return cea.RocketSolution(solver.real)

    return solve_solid_equilibrium_cstar(FreezingCEA(), request, chamber)


def call(obj, name, *args):
    """Invoke a controller slot the way QML does, through the meta-object."""
    from PySide6.QtCore import Q_ARG, QMetaObject

    typed = []
    for value in args:
        kind = ("double" if isinstance(value, float)
                else "int" if isinstance(value, int) else "QString")
        typed.append(Q_ARG(kind, value))
    QMetaObject.invokeMethod(obj, name, *typed)


if __name__ == "__main__":
    raise SystemExit(main())
