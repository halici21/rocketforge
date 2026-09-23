"""Drive the real application shell through a navigation route. Not a test.

Run as a separate process by ``test_shell_navigation_smoke.py``, so that a
crash or a hang ends this process and not the test session. Navigation is
driven by a QTimer inside ``app.exec()``: a real event loop, with no
``processEvents()`` pumping and no forced ``DeferredDelete`` -- the conditions
under which a Nozzle Lab -> Thermochemistry switch once crashed in Qt6Qml.

usage: shell_navigation_driver.py <route> [--step-ms MS] [--inject warning|crash|hang]

<route> is a comma-separated list of steps:
    page:<key>      navigate to that Navigation key
    section:<n>     switch the current page to section n
    mode:<name>     application mode, "analysis" or "engine"
    solve           Thermochemistry and Rocket Performance calculate()
    solid:<key>     solid mode, load that formulation, calculate()
    biprop          bipropellant mode, reset the inputs, calculate()

A solid or biprop step fails the run unless it ends in the mode it names with
a result -- or, with no chemistry provider, at least in that mode.

Prints ``RESULT <json>`` on success: steps completed and every Qt warning seen.
"""
from __future__ import annotations

import faulthandler
import json
import os
import pathlib
import sys

faulthandler.enable()
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

args = sys.argv[1:]
ROUTE = [step for step in args[0].split(",") if step]
STEP_MS = int(args[args.index("--step-ms") + 1]) if "--step-ms" in args else 600
INJECT = args[args.index("--inject") + 1] if "--inject" in args else ""

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if sys.platform == "win32":
    # The offscreen platform looks for fonts beside Qt, finds none, and says
    # so on every run; point it at the system fonts the real platform uses.
    os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from PySide6.QtCore import (QMetaObject, QTimer, QUrl, QtMsgType,  # noqa: E402
                            qInstallMessageHandler)
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlComponent  # noqa: E402

import main as app_main  # noqa: E402

warnings: list[str] = []


def _on_message(kind, _context, message):
    if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
        warnings.append(str(message))


qInstallMessageHandler(_on_message)
app_main.configure_application()
app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
engine, _env = app_main.build_engine(app)
engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
if not engine.rootObjects():
    print("RESULT " + json.dumps({"status": "load-failed", "warnings": warnings}), flush=True)
    sys.exit(3)
window = engine.rootObjects()[0]
window.setProperty("width", 1920)
window.setProperty("height", 1080)
window.setProperty("appMode", "analysis")

probe = QQmlComponent(engine)
probe.setData(b'import QtQuick\nimport RocketForge 1.0\nimport "data" as Data\n'
              b'QtObject { property var nav: Data.Navigation;'
              b' property var thermo: Thermochemistry; property var perf: RocketPerformance }',
              QUrl.fromLocalFile(str(app_main.UI_DIR / "_shell_navigation_probe.qml")))
holder = probe.create()
nav, thermo, perf = (holder.property(name) for name in ("nav", "thermo", "perf"))


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


def _step(spec):
    kind, _, arg = spec.partition(":")
    if kind == "page":
        index = int(nav.indexOfKey(arg))
        if index < 0:
            raise SystemExit(f"unknown navigation key {arg!r}")
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
    if kind == "solve":
        return lambda: (QMetaObject.invokeMethod(thermo, "calculate"),
                        QMetaObject.invokeMethod(perf, "calculate"))
    if kind == "solid":
        known = [option["key"] for option in thermo.property("solidFormulationOptions")]
        if arg not in known:
            raise SystemExit(f"unknown solid formulation {arg!r}; known: {known}")

        def solid(key=arg):
            # Loading a formulation does not change the mode: without this the
            # step would solve the bipropellant case and report nothing wrong.
            thermo.setProperty("formulationKind", "solid")
            thermo.loadSolidFormulation(key)
            QMetaObject.invokeMethod(thermo, "calculate")
            _require_result("solid")
        return solid
    if kind == "biprop":
        def biprop():
            thermo.setProperty("formulationKind", "bipropellant")
            QMetaObject.invokeMethod(thermo, "resetInputs")
            QMetaObject.invokeMethod(thermo, "calculate")
            _require_result("bipropellant")
        return biprop
    raise SystemExit(f"unknown step {spec!r}")


def _require_result(kind):
    """The step is in the mode it names and, given a provider, solved it."""
    if thermo.property("formulationKind") != kind:
        raise RuntimeError(f"Thermochemistry is in {thermo.property('formulationKind')!r} "
                           f"mode, not {kind!r}")
    if thermo.property("providerAvailable") and not thermo.property("hasResult"):
        raise RuntimeError(f"{kind} calculate() produced no result: "
                           f"{thermo.property('statusMessage')}")


def _inject():
    """Negative controls: prove the test can see each failure it guards against."""
    if INJECT == "warning":
        broken = QQmlComponent(engine)
        broken.setData(b"import QtQuick\nItem { Component.onCompleted: undefinedThing.call() }",
                       QUrl.fromLocalFile(str(app_main.UI_DIR / "_shell_navigation_broken.qml")))
        _keep.append(broken.create())
    elif INJECT == "crash":
        # A real native fault, like the Qt6Qml one. Not ctypes: on Windows it
        # catches the access violation and raises OSError instead.
        faulthandler._read_null()
    elif INJECT == "hang":
        import time
        time.sleep(3600)


_keep: list = []
steps = [(spec, _step(spec)) for spec in ROUTE]
state = {"done": 0}


def _tick():
    if state["done"] == 1 and INJECT:
        _inject()
    if state["done"] >= len(steps):
        print("RESULT " + json.dumps({"status": "ok", "steps": state["done"],
                                      "warnings": warnings}), flush=True)
        app.quit()
        return
    spec, action = steps[state["done"]]
    try:
        action()
    except Exception as error:      # a step that did not do what it names
        print("RESULT " + json.dumps({"status": "step-failed", "step": spec,
                                      "error": str(error), "steps": state["done"],
                                      "warnings": warnings}), flush=True)
        app.exit(4)
        return
    state["done"] += 1
    print(f"STEP {state['done']} {spec}", flush=True)
    QTimer.singleShot(STEP_MS, _tick)


QTimer.singleShot(STEP_MS, _tick)
sys.exit(app.exec())
