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
            b' property var thermo: Thermochemistry; property var perf: RocketPerformance }',
            QUrl.fromLocalFile(str(ui_dir / "_navigation_smoke_probe.qml")))
        self._holder = self._probe.create()
        self.nav, self.thermo, self.perf = (self._holder.property(name)
                                            for name in ("nav", "thermo", "perf"))
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
    """``<out.json> <route> [--step-ms MS]``. 0 clean; 2 with warnings; else failed."""
    from pathlib import Path

    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication

    if len(argv) < 2:
        return 64
    out, specs = Path(argv[0]), argv[1].split(",")
    step_ms = int(argv[argv.index("--step-ms") + 1]) if "--step-ms" in argv else 600

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
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
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
