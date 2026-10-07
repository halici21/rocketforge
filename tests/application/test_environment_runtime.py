"""ENV-1 in the running application: an altitude resolves, and nothing else runs.

The real shell is started in a subprocess with every public function of the
layers below ``application`` and every service and gateway entry point wrapped
in a counter, as in the LIQ-2 runtime test. Then:

1. **positive control** -- a real Isentropic solve registers calls;
2. **named pressures** -- open Engine Requirement and browse it at sea level:
   zero calls;
3. **altitude** -- choose the altitude source and type an altitude through the
   real controls. The only calls are ``physics.atmosphere`` state resolutions
   (closed-form, deterministic). No provider, gateway probe or service solve is
   reached, and the page shows the resolved state;
4. **out of range** -- an altitude above 1000 km shows the refusal and no state;
5. **downstream browsing** -- Propellant Trade and Thrust Chamber Sizing open on
   the altitude requirement; again only atmosphere resolutions, no solve;
6. **negative control** -- another real solve registers calls again.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
LOWER = ("rocketforge.physics", "rocketforge.engineering", "rocketforge.engine",
         "rocketforge.providers", "rocketforge.comparison")
EXCLUDED = ("rocketforge.engine.requirement", "rocketforge.engine.propellant_trade",
            "rocketforge.engine.chamber_sizing", "rocketforge.engine.chamber_geometry")
GATEWAY = "rocketforge.application.analysis.thermochemistry_provider"
GATEWAY_PROBES = ("availability", "chamber_provider", "_cea_module")
ATMOSPHERE = "rocketforge.physics.atmosphere"


def _drive() -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    import functools
    import importlib
    import inspect
    import pkgutil
    import re

    import rocketforge

    for info in pkgutil.walk_packages(rocketforge.__path__, "rocketforge."):
        try:
            importlib.import_module(info.name)
        except Exception:
            pass

    service_module = re.compile(r"^rocketforge\.application\.analysis\.\w+_(service|provider)$")
    entry = re.compile(r"^(solve|generate|run|evaluate|compute|calculate|reanalyse)")
    calls: dict[str, int] = {}

    def wrap(original, key):
        @functools.wraps(original)
        def counted(*args, **kwargs):
            calls[key] = calls.get(key, 0) + 1
            return original(*args, **kwargs)
        return counted

    wrappers: dict[int, object] = {}
    for name, module in list(sys.modules.items()):
        if module is None or name in EXCLUDED:
            continue
        lower, service = name.startswith(LOWER), bool(service_module.match(name))
        if not (lower or service):
            continue
        for attr, value in list(vars(module).items()):
            if inspect.isfunction(value) and value.__module__ == name:
                probe = name == GATEWAY and attr in GATEWAY_PROBES
                if service and not entry.search(attr) and not probe:
                    continue
                wrappers[id(value)] = wrap(value, f"{name}.{attr}")
            elif lower and inspect.isclass(value) and value.__module__ == name:
                for method, fn in list(vars(value).items()):
                    if inspect.isfunction(fn) and not method.startswith("__"):
                        setattr(value, method, wrap(fn, f"{name}.{attr}.{method}"))
    for name, module in list(sys.modules.items()):
        if module is None or not (name.startswith("rocketforge") or name == "main"):
            continue
        for attr, value in list(vars(module).items()):
            if inspect.isfunction(value) and id(value) in wrappers:
                setattr(module, attr, wrappers[id(value)])

    from PySide6.QtCore import (Q_ARG, QCoreApplication, QEvent, QMetaObject, QtMsgType,
                                QUrl, qInstallMessageHandler)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    warnings: list[str] = []
    qInstallMessageHandler(lambda kind, _c, message: warnings.append(str(message))
                           if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]
    window.setProperty("width", 1920); window.setProperty("height", 1080)
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport RocketForge 1.0\nimport "data" as D\n'
                  b'QtObject { property var nav: D.Navigation; property var iso: Isentropic;'
                  b' property var req: EngineRequirement }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_environment_runtime.qml")))
    holder = probe.create()
    nav, iso, req = (holder.property(n) for n in ("nav", "iso", "req"))

    def settle(seconds=0.3):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def plain(value):
        return value.toVariant() if hasattr(value, "toVariant") else value

    def items(root=None):
        out, stack = [], [root or window.contentItem()]
        while stack:
            node = stack.pop()
            for child in node.childItems():
                out.append(child)
                stack.append(child)
        return out

    def named(name):
        found = [i for i in items() if i.objectName() == name]
        return found[0] if found else None

    def type_into(name, text):
        field = named(name)
        field.setProperty("text", text)
        QMetaObject.invokeMethod(field, "edited"); settle()

    def activate(name, index):
        QMetaObject.invokeMethod(named(name), "activated", Q_ARG(int, index)); settle()

    def option_index(key):
        return [o["key"] for o in plain(req.property("ambientOptions"))].index(key)

    def not_atmosphere():
        return {k: n for k, n in calls.items() if not k.startswith(ATMOSPHERE)}

    def values():
        prefix = "requirementAtmosphereValue_"
        return {i.objectName()[len(prefix):]: i.property("text") for i in items()
                if i.objectName().startswith(prefix) and i.property("visible")}

    def capture(suffix):
        if os.environ.get("RF_ENVIRONMENT_CAPTURE"):
            target = pathlib.Path(os.environ["RF_ENVIRONMENT_CAPTURE"])
            window.grabWindow().save(str(target.with_stem(target.stem + suffix)))

    out: dict = {"wrapped": len(wrappers)}
    settle(0.8)
    calls.clear()
    iso.setMachAndSolve(2.5); settle()
    out["positive_control_calls"] = sum(calls.values())

    # 1. named pressures
    calls.clear()
    index = nav.indexOfKey("requirement")
    window.setProperty("currentPageIndex", index); settle(0.8)
    type_into("requirementThrust", "1000")
    type_into("requirementBurnTime", "200")
    out["named_calls"] = dict(calls)
    out["altitude_field_visible_at_sea_level"] = named("requirementAltitude").property("visible")

    # 2. altitude through the real controls
    calls.clear()
    activate("requirementAmbientMode", option_index("standard_atmosphere"))
    out["missing_issue"] = [i["code"] for i in plain(req.property("issues"))]
    type_into("requirementAltitude", "10")
    out["altitude_calls_other"] = not_atmosphere()
    out["altitude_calls_atmosphere"] = sum(calls.values())
    out["ambient_text"] = named("requirementAmbientPressure").property("text")
    out["ambient_read_only"] = named("requirementAmbientPressure").property("readOnly")
    out["state_values"] = values()
    out["state_visible"] = named("requirementAtmosphere").property("visible")
    out["record_environment"] = json.loads(req.property("stateJson"))["environment"]
    out["issues"] = [i["code"] for i in plain(req.property("issues"))]
    window.setProperty("themeMode", "light"); settle(0.4)
    capture("")
    window.setProperty("themeMode", "dark"); settle(0.4)
    capture("_dark")
    window.setProperty("themeMode", "light"); settle(0.3)

    # 3. out of range
    calls.clear()
    type_into("requirementAltitude", "1001")
    out["range_issues"] = [i["message"] for i in plain(req.property("issues"))
                           if i["code"] == "ALTITUDE_OUT_OF_RANGE"]
    out["range_state_visible"] = named("requirementAtmosphere").property("visible")
    out["range_ambient_text"] = named("requirementAmbientPressure").property("text")
    out["range_calls_other"] = not_atmosphere()
    capture("_out_of_range")

    # ENV-1B: the upper Standard, where speed of sound and viscosity are not defined
    calls.clear()
    type_into("requirementAltitude", "400")
    out["upper_values"] = values()
    out["upper_reasons"] = {i.objectName()[len("requirementAtmosphereReason_"):]:
                            i.property("text") for i in items()
                            if i.objectName().startswith("requirementAtmosphereReason_")
                            and i.property("visible")}
    out["upper_calls_other"] = not_atmosphere()
    capture("_upper")
    type_into("requirementAltitude", "10")

    # 4. downstream pages on the altitude requirement
    calls.clear()
    for key in ("propellanttrade", "chambersizing", "chambergeometry", "requirement"):
        window.setProperty("currentPageIndex", nav.indexOfKey(key)); settle(0.6)
    for w, h in ((1366, 768), (1920, 1080)):
        window.setProperty("width", w); window.setProperty("height", h); settle(0.3)
    out["downstream_calls_other"] = not_atmosphere()

    calls.clear()
    iso.setMachAndSolve(3.0); settle()
    out["negative_control_calls"] = sum(calls.values())
    out["warnings"] = warnings
    return out


def _run() -> dict:
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve())], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert completed.returncode == 0, completed.stderr[-3000:]
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    return json.loads(lines[-1][len("RESULT "):])


@pytest.fixture(scope="module")
def run():
    return _run()


def test_the_instrument_is_live(run):
    assert run["wrapped"] > 200
    assert run["positive_control_calls"] > 0 and run["negative_control_calls"] > 0


def test_named_pressures_reach_nothing(run):
    assert run["named_calls"] == {}, run["named_calls"]
    assert run["altitude_field_visible_at_sea_level"] is False


def test_an_altitude_resolves_through_the_atmosphere_only(run):
    assert run["missing_issue"].count("ALTITUDE_MISSING") == 1
    assert run["altitude_calls_other"] == {}, run["altitude_calls_other"]
    assert run["altitude_calls_atmosphere"] > 0
    assert run["record_environment"] == {"mode": "standard_atmosphere",
                                         "custom_pressure_Pa": 101325.0,
                                         "altitude_m": 10000.0, "atmosphere_model": "ussa1976"}
    assert "ALTITUDE_MISSING" not in run["issues"]


def test_the_page_shows_the_resolved_state(run):
    assert run["ambient_text"] == "26.4998981393" and run["ambient_read_only"] is True
    assert run["state_visible"] is True
    v = run["state_values"]
    assert v["temperature"] == "223.252 K" and v["geopotential_altitude"] == "9,984.3 m'"
    assert v["density"] == "0.41351 kg/m³" and v["speed_of_sound"] == "299.53 m/s"
    assert v["layer"] == "0" and v["pressure"] == "26.4999 kPa"


def test_out_of_range_is_shown_and_nothing_is_extrapolated(run):
    assert run["range_issues"] and "Nothing is extrapolated" in run["range_issues"][0]
    assert run["range_state_visible"] is False and run["range_ambient_text"] == ""
    assert run["range_calls_other"] == {}


def test_the_upper_standard_shows_what_it_does_not_define(run):
    v = run["upper_values"]
    assert v["temperature"] == "995.825 K"          # eq. 31; Sutton App. 2: 995.83
    assert v["speed_of_sound"] == "not defined" and v["dynamic_viscosity"] == "not defined"
    assert "1.3.10" in run["upper_reasons"]["speed_of_sound"]
    assert "1.3.11" in run["upper_reasons"]["dynamic_viscosity"]
    assert run["upper_calls_other"] == {}, run["upper_calls_other"]


def test_downstream_pages_solve_nothing(run):
    assert run["downstream_calls_other"] == {}, run["downstream_calls_other"]


def test_no_qml_warnings(run):
    assert run["warnings"] == [], run["warnings"]


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
