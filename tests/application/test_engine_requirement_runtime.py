"""LIQ-2 in the running application: the Engine Requirement page solves nothing.

A subprocess starts the real shell (``main.configure_application`` and
``main.build_engine``, as the product does) with every public function of
``physics``, ``engineering``, ``engine``, ``providers`` and ``comparison`` --
and every solve/generate/run/evaluate entry point of the application services
and provider gateways -- wrapped in a counter before QML is loaded. The
requirement domain module itself is excluded from the count: it is the state
being edited, not a calculation.

Then:

1. **positive control** -- a real Isentropic solve must register calls;
2. **the edit sequence** -- open the page and change every requirement field
   through the real QML controls (text fields, combo boxes, segmented
   controls), move feed from pump-fed to pressure-fed, choose full-flow staged
   combustion, copy and paste the record, switch theme and window size, leave
   and return -- must register **zero** calls, and the page must show what the
   controller holds;
3. **negative control** -- another real solve must register calls again.
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
#: The state under edit. Its methods (validation, serialisation) are what an
#: edit is *expected* to call, and none of them is a calculation.
EXCLUDED = ("rocketforge.engine.requirement",)
FORBIDDEN_TEXT = ("Calculate", "Run study", "Solve", "Recommended", "Optimal")


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
        except Exception:            # an optional provider absent in this environment
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
                if service and not entry.search(attr):
                    continue
                wrappers[id(value)] = wrap(value, f"{name}.{attr}")
            elif lower and inspect.isclass(value) and value.__module__ == name:
                for method, fn in list(vars(value).items()):
                    if inspect.isfunction(fn) and not method.startswith("__"):
                        setattr(value, method, wrap(fn, f"{name}.{attr}.{method}"))
    bindings = 0
    for name, module in list(sys.modules.items()):
        if module is None or not (name.startswith("rocketforge") or name == "main"):
            continue
        for attr, value in list(vars(module).items()):
            if inspect.isfunction(value) and id(value) in wrappers:
                setattr(module, attr, wrappers[id(value)])
                bindings += 1

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
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_requirement_runtime.qml")))
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
        """Set a field's text and finish editing, as a person's Enter does."""
        field = named(name)
        field.setProperty("text", text)
        QMetaObject.invokeMethod(field, "edited")
        settle()

    def activate(name, index):
        QMetaObject.invokeMethod(named(name), "activated", Q_ARG(int, index)); settle()

    def select(name, index):
        QMetaObject.invokeMethod(named(name), "selected", Q_ARG(int, index)); settle()

    def option_index(options, key):
        return [o["key"] for o in plain(req.property(options))].index(key)

    def total():
        return sum(calls.values())

    out: dict = {"wrapped": len(wrappers), "bindings": bindings}
    settle(0.8)

    # 1. positive control
    calls.clear()
    iso.setMachAndSolve(2.5); settle()
    out["positive_control_calls"] = total()

    # 2. the edit sequence
    calls.clear()
    index = nav.indexOfKey("requirement")
    out["nav_index"] = index
    out["family"] = [f["groups"][0]["items"] for f in plain(nav.property("families"))
                     if f["key"] == "liquidengine"]
    window.setProperty("currentPageIndex", index); settle(0.8)
    out["status_before"] = named("requirementStatus").property("text")

    type_into("requirementName", "Upper stage")
    type_into("requirementThrust", "1000")
    type_into("requirementBurnTime", "380")
    activate("requirementAmbientMode", option_index("ambientOptions", "custom"))
    type_into("requirementAmbientPressure", "2.5")
    pairs = [o["key"] for o in plain(req.property("pairOptions"))]
    activate("requirementPair", 1 + pairs.index("sutton-o2-ch4"))       # 0 is Auto
    select("requirementChamberMode", option_index("chamberPressureOptions", "target"))
    type_into("requirementChamberPressure", "30")
    select("requirementRatioMode", option_index("mixtureRatioOptions", "pair_reference"))
    out["reference_ratio_text"] = named("requirementReferenceRatio").property("text")
    select("requirementFeed", option_index("feedOptions", "pump_fed"))
    activate("requirementCycle", option_index("cycleOptions", "full_flow_staged_combustion"))
    out["cycle_note"] = named("requirementCycleNote").property("text")
    activate("requirementPriority", option_index("priorityOptions", "specific_impulse"))
    out["after_edits"] = json.loads(req.property("stateJson"))
    out["complete"] = req.property("isComplete")
    out["status_after"] = named("requirementStatus").property("text")
    out["summary_cycle"] = named("requirementSummary_cycle").property("text")
    out["summary_pair"] = named("requirementSummary_propellant").property("text")
    out["open_decisions"] = named("requirementOpenDecisions").property("text")

    select("requirementFeed", option_index("feedOptions", "pressure_fed"))
    cycle_box = named("requirementCycle")
    out["pressure_fed"] = {"cycle": req.property("cycle"),
                           "cycle_enabled": cycle_box.property("enabled"),
                           "summary": named("requirementSummary_cycle").property("text"),
                           "note": named("requirementCycleNote").property("text")}
    select("requirementFeed", option_index("feedOptions", "pump_fed"))
    activate("requirementCycle", option_index("cycleOptions", "full_flow_staged_combustion"))

    saved = req.property("stateJson")
    QMetaObject.invokeMethod(named("requirementCopy"), "clicked"); settle()
    QMetaObject.invokeMethod(named("requirementReset"), "clicked"); settle()
    out["after_reset_thrust"] = named("requirementThrust").property("text")
    QMetaObject.invokeMethod(named("requirementPaste"), "clicked"); settle()
    out["restored"] = req.property("stateJson") == saved
    out["restored_field"] = named("requirementThrust").property("text")

    for theme in ("dark", "light"):
        window.setProperty("themeMode", theme); settle(0.3)
    for w, h in ((1366, 768), (2560, 1440), (1920, 1080)):
        window.setProperty("width", w); window.setProperty("height", h); settle(0.3)
    counts = []
    for _ in range(3):
        window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
        window.setProperty("currentPageIndex", index); settle(0.5)
        counts.append(sum(1 for i in items() if i.objectName() == "requirementStatus"))
    out["page_instances"] = counts
    out["state_after_reentry"] = req.property("stateJson") == saved

    roots = [i for i in items() if i.metaObject().className().startswith("EngineRequirementPage")]
    texts = [str(i.property("text")) for r in roots for i in items(r)
             if i.property("text") is not None]
    out["page_text_count"] = len(texts)
    out["forbidden_text"] = sorted({p for p in FORBIDDEN_TEXT for t in texts if p in t})
    out["edit_calls"] = total()
    out["edit_call_names"] = sorted(calls)

    if os.environ.get("RF_REQUIREMENT_CAPTURE"):
        window.setProperty("currentPageIndex", index); settle(0.6)
        window.grabWindow().save(os.environ["RF_REQUIREMENT_CAPTURE"])

    # 3. negative control
    calls.clear()
    iso.setMachAndSolve(3.0); settle()
    out["negative_control_calls"] = total()
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


def test_the_instrument_is_live_before_and_after(run):
    assert run["wrapped"] > 200 and run["bindings"] > 0
    assert run["positive_control_calls"] > 0, "the instrument cannot see a real solve"
    assert run["negative_control_calls"] > 0, "the instrument went blind during the sequence"


def test_editing_the_requirement_solves_nothing(run):
    assert run["edit_calls"] == 0, run["edit_call_names"]


def test_the_page_is_its_own_rail_family(run):
    assert run["nav_index"] >= 0 and run["family"] == [[run["nav_index"]]]


def test_the_qml_controls_write_the_controller_requirement(run):
    state = run["after_edits"]
    assert state["name"] == "Upper stage"
    assert state["thrust_N"] == 1.0e6 and state["burn_time_s"] == 380.0
    assert state["environment"] == {"mode": "custom", "custom_pressure_Pa": 2500.0}
    assert state["propellant"] == {"mode": "explicit", "pair_key": "sutton-o2-ch4"}
    assert state["chamber_pressure"] == {"mode": "target", "value_Pa": 30.0e6}
    assert state["mixture_ratio"] == {"mode": "pair_reference", "value": None}
    assert state["feed"] == "pump_fed"
    assert state["cycle"] == "full_flow_staged_combustion"
    assert state["priority"] == "specific_impulse"
    assert run["complete"] is True
    assert run["status_before"] == "2 items to resolve"
    assert run["status_after"] == "Requirement complete"


def test_the_page_renders_what_the_controller_holds(run):
    assert run["reference_ratio_text"].startswith("O/F 3 ")         # Sutton LOX/CH4
    assert run["summary_pair"] == "Oxygen / Methane"
    assert run["summary_cycle"] == "Full-flow staged combustion"
    assert "future-modelled intent" in run["cycle_note"]
    assert run["open_decisions"] == "None"


def test_pressure_fed_has_no_cycle(run):
    assert run["pressure_fed"] == {
        "cycle": "", "cycle_enabled": False, "summary": "Not applicable",
        "note": "Only a pump-fed engine has a power cycle."}


def test_the_record_survives_copy_reset_and_paste(run):
    assert run["after_reset_thrust"] == ""
    assert run["restored"] and run["restored_field"] == "1000"
    assert run["state_after_reentry"]


def test_no_warning_no_solve_action_and_no_accumulating_pages(run):
    assert run["warnings"] == [], run["warnings"]
    assert run["page_text_count"] > 30 and run["forbidden_text"] == []
    assert run["page_instances"] == [1, 1, 1]


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
