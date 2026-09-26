"""Drive the real shell through a navigation route, under a real event loop.

The route that once crashed in Qt6Qml -- Nozzle Lab (Operating point) into
Thermochemistry -- only failed under ``app.exec()``: a real event loop, no
``processEvents()`` pumping, no forced ``DeferredDelete``. This module drives
exactly that, one step per timer tick, and records every Qt warning on the way.

It serves two callers with one implementation:

* ``RocketForge.exe --selftest-navigation <out.json> <route>`` checks a
  packaged build (packaging/verify_package.py, the canonical build);
* ``tests/application/shell_navigation_driver.py`` runs the same routes from
  source in CI, and adds its negative controls around them.

A route is a comma-separated list of steps:

    page:<key>      navigate to that Navigation key
    section:<n>     switch the current page to section n
    mode:<name>     application mode, "analysis" or "engine"
    solve           Thermochemistry and Rocket Performance calculate()
    solid:<key>     solid mode, load that formulation, calculate()
    biprop          bipropellant mode, reset the inputs, calculate()
    theme:<mode>    "light" or "dark"
    size:<w>x<h>    resize the window, e.g. size:1366x768
    capture:<name>  save the window as <name>.png beside the report
    settings:<open|close>  the Settings menu, which shows the build identity
    view:<2d|3d>    the current page's 2D / 3D view switch, as a click on it
    expect3d:<yes|no>  a Qt Quick 3D scene exists (yes) or none does (no)
    backpressure:<r>   Nozzle Lab's back pressure p_b/p0, as typed in its field
    expectshock:<yes|no>  the 3D shock plane is shown (yes) or absent (no)
    sweep           Thermochemistry runSweep()
    peekfocus       the first plot peek on screen opens, then asks for Focus
    expectfocus:<yes|no>  a Focus overlay is open (yes) or none is (no)

A solid or biprop step fails the run unless it ends in the mode it names with a
result -- or, with no chemistry provider, at least in that mode.
"""

from __future__ import annotations

import json
import sys

__all__ = ["NAVIGATION_SMOKE_FLAG", "Route", "run_navigation_smoke"]

NAVIGATION_SMOKE_FLAG = "--selftest-navigation"


def _section_page(obj, depth=0):
    if obj is None or depth > 14:
        return None
    if obj.metaObject().indexOfProperty("section") >= 0:
        return obj
    for child in obj.children():
        found = _section_page(child, depth + 1)
        if found is not None:
            return found
    return None


class Route:
    """A parsed route over a loaded shell, run step by step on a timer."""

    def __init__(self, engine, window, ui_dir, specs, capture_dir=None):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent

        self.window = window
        self.capture_dir = capture_dir
        self._probe = QQmlComponent(engine)
        self._probe.setData(
            b'import QtQuick\nimport RocketForge 1.0\nimport "data" as Data\n'
            b'QtObject { property var nav: Data.Navigation;'
            b' property var thermo: Thermochemistry; property var perf: RocketPerformance;'
            b' property var nozzle: Nozzle }',
            QUrl.fromLocalFile(str(ui_dir / "_navigation_smoke_probe.qml")))
        self._holder = self._probe.create()
        self.nav, self.thermo, self.perf, self.nozzle = (
            self._holder.property(name) for name in ("nav", "thermo", "perf", "nozzle"))
        self.specs = [spec for spec in specs if spec]
        self.steps = [(spec, self._step(spec)) for spec in self.specs]

    def _step(self, spec):
        from PySide6.QtCore import QMetaObject

        window, thermo, perf = self.window, self.thermo, self.perf
        kind, _, arg = spec.partition(":")
        if kind == "page":
            index = int(self.nav.indexOfKey(arg))
            if index < 0:
                raise ValueError(f"unknown navigation key {arg!r}")
            return lambda: window.setProperty("currentPageIndex", index)
        if kind == "section":
            def select(n=int(arg)):
                page = _section_page(window)
                if page is None:
                    raise RuntimeError(f"no page with sections at step {spec!r}")
                page.setProperty("section", n)
            return select
        if kind == "mode":
            return lambda: window.setProperty("appMode", arg)
        if kind == "theme":
            return lambda: window.setProperty("themeMode", arg)
        if kind == "size":
            width, height = (int(value) for value in arg.lower().split("x"))
            return lambda: (window.setProperty("width", width),
                            window.setProperty("height", height))
        if kind == "settings":
            if arg not in ("open", "close"):
                raise ValueError(f"settings:{arg} -- use settings:open or settings:close")

            def settings(action=arg):
                from PySide6.QtCore import QMetaObject, QObject
                menus = [child for child in window.findChildren(QObject)
                         if child.metaObject().className().startswith("SettingsPanel")]
                if not menus:
                    raise RuntimeError("no Settings menu in the shell")
                QMetaObject.invokeMethod(menus[0], action)
            return settings
        if kind == "capture":
            if self.capture_dir is None:
                raise ValueError("capture steps need a report directory")

            def capture(name=arg):
                image = window.grabWindow()
                if image.isNull() or not image.save(str(self.capture_dir / f"{name}.png")):
                    raise RuntimeError(f"capture {name!r} could not be saved")
            return capture
        if kind == "solve":
            return lambda: (QMetaObject.invokeMethod(thermo, "calculate"),
                            QMetaObject.invokeMethod(perf, "calculate"))
        if kind == "solid":
            known = [option["key"] for option in thermo.property("solidFormulationOptions")]
            if arg not in known:
                raise ValueError(f"unknown solid formulation {arg!r}; known: {known}")

            def solid(key=arg):
                # Loading a formulation does not change the mode: without this the
                # step would solve the bipropellant case and report nothing wrong.
                thermo.setProperty("formulationKind", "solid")
                thermo.loadSolidFormulation(key)
                QMetaObject.invokeMethod(thermo, "calculate")
                self._require_result("solid")
            return solid
        if kind == "view":
            if arg not in ("2d", "3d"):
                raise ValueError(f"view:{arg} -- use view:2d or view:3d")

            def view(mode=arg):
                from PySide6.QtCore import Q_ARG, QMetaObject, QObject
                switches = [child for child in window.findChildren(QObject)
                            if child.metaObject().indexOfSignal("modeRequested(QString)") >= 0
                            and child.metaObject().indexOfProperty("show3D") >= 0]
                # More than one page has a switch (Rocket Performance, Nozzle
                # Lab): the one on screen is the one a click would reach.
                shown = [s for s in switches if hasattr(s, "isVisible") and s.isVisible()]
                switches = shown or switches
                if not switches:
                    raise RuntimeError("no 2D / 3D view switch on this page")
                if mode == "3d" and not switches[0].property("threeDAvailable"):
                    raise RuntimeError("the 3D view is unavailable: "
                                       + str(switches[0].property("unavailableReason")))
                QMetaObject.invokeMethod(switches[0], "modeRequested", Q_ARG(str, mode))
            return view
        if kind == "expect3d":
            if arg not in ("yes", "no"):
                raise ValueError(f"expect3d:{arg} -- use expect3d:yes or expect3d:no")

            def expect3d(wanted=arg == "yes"):
                from PySide6.QtCore import QObject
                scenes = [child for child in window.findChildren(QObject)
                          if child.metaObject().className().startswith("QQuick3DViewport")]
                if bool(scenes) != wanted:
                    raise RuntimeError(f"{len(scenes)} Qt Quick 3D scene(s); expected "
                                       f"{'one' if wanted else 'none'}")
            return expect3d
        if kind == "backpressure":
            ratio = float(arg)
            return lambda: self.nozzle.setProperty("backPressureRatio", ratio)
        if kind == "expectshock":
            if arg not in ("yes", "no"):
                raise ValueError(f"expectshock:{arg} -- use expectshock:yes or expectshock:no")

            def expectshock(wanted=arg == "yes"):
                from PySide6.QtCore import QObject
                planes = [child for child in window.findChildren(QObject)
                          if child.objectName() == "station:shock-plane"]
                if not planes:
                    raise RuntimeError("no 3D view with a shock plane is loaded")
                shown = any(bool(plane.property("visible")) for plane in planes)
                if shown != wanted:
                    raise RuntimeError(f"shock plane shown={shown}; expected "
                                       f"{'shown' if wanted else 'absent'}")
            return expectshock
        if kind == "sweep":
            return lambda: QMetaObject.invokeMethod(thermo, "runSweep")
        if kind == "peekfocus":
            def peekfocus():
                from PySide6.QtCore import QObject
                peeks = [child for child in window.findChildren(QObject)
                         if child.metaObject().className().startswith("RFPlotPeek")
                         and child.isVisible()]
                if not peeks:
                    raise RuntimeError("no plot peek on screen")
                QMetaObject.invokeMethod(peeks[0], "startPeek")
                if not peeks[0].property("peeking"):
                    raise RuntimeError("the plot peek did not open")
                QMetaObject.invokeMethod(peeks[0], "requestFocus")
            return peekfocus
        if kind == "expectfocus":
            if arg not in ("yes", "no"):
                raise ValueError(f"expectfocus:{arg} -- use expectfocus:yes or expectfocus:no")

            def expectfocus(wanted=arg == "yes"):
                from PySide6.QtCore import QObject
                opened = [child for child in window.findChildren(QObject)
                          if child.metaObject().className().startswith("RFFocusOverlay")
                          and child.property("opened")]
                if bool(opened) != wanted:
                    raise RuntimeError(f"{len(opened)} Focus overlay(s) open; expected "
                                       f"{'one' if wanted else 'none'}")
            return expectfocus
        if kind == "biprop":
            def biprop():
                thermo.setProperty("formulationKind", "bipropellant")
                QMetaObject.invokeMethod(thermo, "resetInputs")
                QMetaObject.invokeMethod(thermo, "calculate")
                self._require_result("bipropellant")
            return biprop
        raise ValueError(f"unknown step {spec!r}")

    def _require_result(self, kind):
        """The step is in the mode it names and, given a provider, solved it."""
        thermo = self.thermo
        if thermo.property("formulationKind") != kind:
            raise RuntimeError(f"Thermochemistry is in {thermo.property('formulationKind')!r} "
                               f"mode, not {kind!r}")
        if thermo.property("providerAvailable") and not thermo.property("hasResult"):
            raise RuntimeError(f"{kind} calculate() produced no result: "
                               f"{thermo.property('statusMessage')}")

    def run(self, app, step_ms, warnings, *, before_step=None, on_step=None) -> dict:
        """Run under ``app.exec()``; return the result record."""
        from PySide6.QtCore import QTimer

        state = {"done": 0, "result": None}

        def finish(code, **result):
            state["result"] = {"steps": state["done"], "warnings": list(warnings),
                               **result}
            app.exit(code)

        def tick():
            if before_step is not None:
                before_step(state["done"])
            if state["done"] >= len(self.steps):
                finish(0, status="ok")
                return
            spec, action = self.steps[state["done"]]
            try:
                action()
            except Exception as error:      # a step that did not do what it names
                finish(4, status="step-failed", step=spec, error=str(error))
                return
            state["done"] += 1
            if on_step is not None:
                on_step(state["done"], spec)
            QTimer.singleShot(step_ms, tick)

        QTimer.singleShot(step_ms, tick)
        app.exec()
        return state["result"] or {"status": "no-result", "steps": state["done"],
                                   "warnings": list(warnings)}


def run_navigation_smoke(argv, configure, build_engine, ui_dir) -> int:
    """``<out.json> <route> [--step-ms MS] [--window WxH]``. 0 clean; 2 with warnings; else failed.

    ``--window`` sizes the window before it is shown (default 1920x1080). A run
    on a real platform -- the 3D view needs one -- uses a size that fits the
    screen, so the window manager has no geometry to correct and warn about.
    """
    from pathlib import Path

    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication

    if len(argv) < 2:
        return 64
    out, specs = Path(argv[0]), argv[1].split(",")
    step_ms = int(argv[argv.index("--step-ms") + 1]) if "--step-ms" in argv else 600
    width, height = 1920, 1080
    if "--window" in argv:
        width, height = (int(v) for v in argv[argv.index("--window") + 1].lower().split("x"))

    warnings: list[str] = []

    def on_message(kind, _context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            warnings.append(str(message))

    qInstallMessageHandler(on_message)
    configure()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _environment = build_engine(app)
    engine.load(QUrl.fromLocalFile(str(Path(ui_dir) / "Main.qml")))
    if not engine.rootObjects():
        out.write_text(json.dumps({"status": "load-failed", "warnings": warnings}),
                       encoding="utf-8")
        return 3
    window = engine.rootObjects()[0]
    window.setProperty("width", width)
    window.setProperty("height", height)
    window.setProperty("appMode", "analysis")
    try:
        route = Route(engine, window, Path(ui_dir), specs, capture_dir=out.parent)
    except ValueError as error:
        out.write_text(json.dumps({"status": "bad-route", "error": str(error)}),
                       encoding="utf-8")
        return 64
    result = route.run(app, step_ms, warnings)
    result["route"] = ",".join(route.specs)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if result["status"] != "ok":
        return 4
    return 2 if result["warnings"] else 0
