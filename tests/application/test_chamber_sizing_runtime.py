"""LIQ-4 in the running application: only Size solves.

The real shell is started in a subprocess with every public function of the
layers below ``application`` and every service solve entry point wrapped in a
counter, plus the provider gateway's availability probe (as in the Propellant
Trade runtime test). Then:

1. **positive control** -- a real Isentropic solve registers calls;
2. **setup** -- a requirement and a one-pair trade at Ae/At 40, run and
   selected through their own controllers;
3. **browsing** -- open Thrust Chamber Sizing, type and clear an area ratio
   through the real field, change theme and size, leave and return: **zero**
   calls, and not even an availability probe;
4. **Size** -- the real button. With NASA CEA installed it solves exactly one
   chamber and shows every quantity; without it there is no trade, so Size is
   disabled and nothing is solved;
5. **after sizing** -- theme, re-entry and a change of trade selection solve
   nothing, and the result reads as stale;
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
# The three liquid-engine data modules hold state the controllers compare
# (fingerprints); they are records, not solvers.
EXCLUDED = ("rocketforge.engine.requirement", "rocketforge.engine.propellant_trade",
            "rocketforge.engine.chamber_sizing")
GATEWAY = "rocketforge.application.analysis.thermochemistry_provider"
GATEWAY_PROBES = ("availability", "chamber_provider", "_cea_module")
PROBE_NAMES = frozenset(GATEWAY_PROBES) | {"check_availability", "_installed", "load_cea"}
FORBIDDEN_TEXT = ("Best", "Optimal", "Optimum Ae", "Recommended", "Score", "Feasible")


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

    from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QtMsgType, QUrl
    from PySide6.QtCore import qInstallMessageHandler
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
                  b' property var req: EngineRequirement; property var trade: PropellantTrade;'
                  b' property var sizing: ChamberSizing }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_sizing_runtime.qml")))
    holder = probe.create()
    nav, iso, req, trade, sizing = (holder.property(n)
                                    for n in ("nav", "iso", "req", "trade", "sizing"))

    def settle(seconds=0.3):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

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

    def total():
        return sum(calls.values())

    def solves():
        return {k: n for k, n in calls.items() if k.rsplit(".", 1)[-1] not in PROBE_NAMES}

    out: dict = {"wrapped": len(wrappers)}
    settle(0.8)
    calls.clear()
    iso.setMachAndSolve(2.5); settle()
    out["positive_control_calls"] = total()

    # 1. setup: a requirement and a one-pair trade, through their controllers
    req.setThrust("1000"); req.setBurnTime("200"); req.setPair("sutton-o2-ch4"); settle()
    trade.setStudyPressure("10"); trade.setRatioMode("catalogue")
    trade.setPerformanceBasis("ideal_area_ratio"); trade.setAreaRatio("40")
    trade.runTrade()
    deadline = time.perf_counter() + 120
    settle(0.2)
    while trade.property("busy") and time.perf_counter() < deadline:
        settle(0.1)
    trade.selectCandidate("sutton-o2-ch4"); settle()
    out["trade_selected"] = trade.property("selectedKey")

    # 2. browsing
    calls.clear()
    index = nav.indexOfKey("chambersizing")
    out["nav_index"] = index
    out["family"] = [f["groups"][0]["items"] for f in nav.property("families").toVariant()
                     if f["key"] == "liquidengine"] if hasattr(
                         nav.property("families"), "toVariant") else []
    window.setProperty("currentPageIndex", index); settle(0.8)
    out["status_before"] = named("sizingStatus").property("text")
    out["run_enabled_before"] = named("sizingRun").property("enabled")
    out["issues_before"] = [i.property("text") for i in items()
                            if i.objectName() == "sizingIssue"]
    out["operating_before"] = [i.property("text") for i in items()
                               if i.objectName() == "sizingOperating"]
    type_into("sizingAreaRatio", "25")
    out["stated_ratio"] = sizing.property("areaRatioText")
    type_into("sizingAreaRatio", "")
    for theme in ("dark", "light"):
        window.setProperty("themeMode", theme); settle(0.3)
    for w, h in ((1366, 768), (1920, 1080)):
        window.setProperty("width", w); window.setProperty("height", h); settle(0.3)
    window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
    window.setProperty("currentPageIndex", index); settle(0.5)
    out["browse_calls"] = dict(calls)

    # 3. Size, the real button
    calls.clear()
    if named("sizingRun").property("enabled"):
        QMetaObject.invokeMethod(named("sizingRun"), "clicked"); settle(0.6)
    out["has_result"] = sizing.property("hasResult")
    out["status_after"] = named("sizingStatus").property("text")
    out["message"] = sizing.property("message")
    out["solve_case_calls"] = calls.get(
        "rocketforge.application.analysis.thermochemistry_service.solve_case", 0)
    out["run_solves"] = sum(solves().values())
    out["rendered_rows"] = sorted(i.objectName() for i in items()
                                  if i.objectName().startswith("sizingRow_"))
    out["values"] = {i.objectName()[len("sizingValue_"):]: i.property("text") for i in items()
                     if i.objectName().startswith("sizingValue_")}
    out["assumptions"] = [i.property("text") for i in items()
                          if i.objectName() == "sizingAssumption"]
    out["regime"] = (named("sizingRegime").property("text")
                     if named("sizingRegime") is not None else "")

    if os.environ.get("RF_SIZING_CAPTURE"):
        for w, h, suffix in ((1920, 1080, ""), (1366, 768, "_1366")):
            window.setProperty("width", w); window.setProperty("height", h); settle(0.6)
            target = pathlib.Path(os.environ["RF_SIZING_CAPTURE"])
            window.grabWindow().save(str(target.with_stem(target.stem + suffix)))
        window.setProperty("width", 1920); window.setProperty("height", 1080); settle(0.3)

    # 4. after sizing: theme, re-entry and a new trade selection solve nothing
    calls.clear()
    for theme in ("dark", "light"):
        window.setProperty("themeMode", theme); settle(0.3)
    window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
    window.setProperty("currentPageIndex", index); settle(0.5)
    out["stale_before_change"] = sizing.property("resultStale")
    trade.selectCandidate(""); settle()
    out["stale_after_change"] = sizing.property("resultStale")
    out["status_after_change"] = named("sizingStatus").property("text")
    out["after_run_calls"] = dict(calls)
    out["page_instances"] = sum(1 for i in items() if i.objectName() == "sizingStatus")

    roots = [i for i in items() if i.metaObject().className().startswith("ChamberSizingPage")]
    texts = [str(i.property("text")) for r in roots for i in items(r)
             if i.property("text") is not None]
    out["forbidden_text"] = sorted({p for p in FORBIDDEN_TEXT for t in texts if p in t})

    calls.clear()
    iso.setMachAndSolve(3.0); settle()
    out["negative_control_calls"] = total()
    out["warnings"] = warnings
    return out


def _run() -> dict:
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve())], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=400)
    assert completed.returncode == 0, completed.stderr[-3000:]
    lines = [line for line in completed.stdout.splitlines() if line.startswith("RESULT ")]
    assert lines, completed.stdout[-2000:] + completed.stderr[-2000:]
    return json.loads(lines[-1][len("RESULT "):])


@pytest.fixture(scope="module")
def run():
    return _run()


def _cea_installed() -> bool:
    from rocketforge.application.analysis.thermochemistry_provider import availability

    return availability().usable


def test_the_instrument_is_live(run):
    assert run["wrapped"] > 200
    assert run["positive_control_calls"] > 0 and run["negative_control_calls"] > 0


def test_browsing_neither_solves_nor_probes(run):
    assert run["browse_calls"] == {}, run["browse_calls"]
    assert run["after_run_calls"] == {}, run["after_run_calls"]


def test_the_page_sits_in_the_liquid_engine_family(run):
    assert run["nav_index"] >= 0
    if run["family"]:
        assert run["nav_index"] in run["family"][0]


def test_the_page_reads_the_trade_and_the_stated_ratio(run):
    assert run["status_before"] == "Not sized"
    assert run["stated_ratio"] == "25"
    if not _cea_installed():
        assert run["run_enabled_before"] is False
        assert any("No propellant trade" in text for text in run["issues_before"])
        return
    assert run["trade_selected"] == "sutton-o2-ch4"
    assert run["run_enabled_before"] is True and run["issues_before"] == []
    assert any("selected in the trade" in text for text in run["operating_before"])


def test_size_is_the_only_solve(run):
    if not _cea_installed():
        assert run["run_solves"] == 0 and not run["has_result"]
        return
    assert run["solve_case_calls"] == 1, run["solve_case_calls"]
    assert run["has_result"] and run["status_after"].startswith("Sized"), run["message"]
    assert len(run["rendered_rows"]) == 23
    assert all(value != "—" for value in run["values"].values()), run["values"]
    assert run["values"]["thrust"] == "1,000.0000"
    assert any("Ae/At 40 · the trade's nozzle" in text for text in run["assumptions"])
    assert run["regime"].startswith("overexpanded")


def test_a_new_trade_selection_makes_the_sizing_stale(run):
    if not _cea_installed():
        return
    assert run["stale_before_change"] is False
    assert run["stale_after_change"] is True
    assert run["status_after_change"].startswith("Stale")


def test_no_warning_no_verdict_text_and_no_accumulating_pages(run):
    assert run["warnings"] == [], run["warnings"]
    assert run["forbidden_text"] == []
    assert run["page_instances"] == 1


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
