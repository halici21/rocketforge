"""LIQ-3 in the running application: only Run trade solves.

The real shell is started in a subprocess with every public function of the
layers below ``application`` and every service solve entry point wrapped in a
counter, plus the provider gateway's availability probe (as in the Propulsion
Database runtime test). Then:

1. **positive control** -- a real Isentropic solve registers calls;
2. **browsing** -- open the Propellant Trade page and set every study input
   through the real QML controls, sort, change theme and size, leave and
   return: **zero** calls, and not even an availability probe;
3. **Run trade** -- the real button. With NASA CEA installed it solves exactly
   one chamber per candidate and fills the table; without it, it reports the
   missing provider and solves nothing;
4. **after the run** -- sorting, selecting a row, theme, size and re-entry
   solve nothing; "Use for Engine Requirement" writes the chosen pair into the
   requirement without a solve;
5. **negative control** -- another real solve registers calls again.
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
EXCLUDED = ("rocketforge.engine.requirement", "rocketforge.engine.propellant_trade")
GATEWAY = "rocketforge.application.analysis.thermochemistry_provider"
GATEWAY_PROBES = ("availability", "chamber_provider", "_cea_module")
PROBE_NAMES = frozenset(GATEWAY_PROBES) | {"check_availability", "_installed", "load_cea"}
FORBIDDEN_TEXT = ("Best", "Optimal", "Recommended", "Score", "Feasible")


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
                  b' property var req: EngineRequirement; property var trade: PropellantTrade }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_trade_runtime.qml")))
    holder = probe.create()
    nav, iso, req, trade = (holder.property(n) for n in ("nav", "iso", "req", "trade"))

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

    def select(name, index):
        QMetaObject.invokeMethod(named(name), "selected", Q_ARG(int, index)); settle()

    def total():
        return sum(calls.values())

    def solves():
        """Calls that are not availability probes. Run checks availability
        first -- in the gateway and in the provider package below it."""
        return {k: n for k, n in calls.items() if k.rsplit(".", 1)[-1] not in PROBE_NAMES}

    out: dict = {"wrapped": len(wrappers)}
    settle(0.8)
    calls.clear()
    iso.setMachAndSolve(2.5); settle()
    out["positive_control_calls"] = total()

    # 0. a requirement for the trade to answer (through its own controller)
    req.setThrust("1000"); req.setBurnTime("200"); settle()

    # 1. browsing
    calls.clear()
    index = nav.indexOfKey("propellanttrade")
    out["nav_index"] = index
    window.setProperty("currentPageIndex", index); settle(0.8)
    out["status_before"] = named("tradeStatus").property("text")
    out["run_enabled_before"] = named("tradeRun").property("enabled")
    out["issues_before"] = len([i for i in items() if i.objectName() == "tradeIssue"])
    type_into("tradeStudyPressure", "10")
    select("tradeRatioMode", 1)                                   # Catalogue
    select("tradeBasis", 1)                                       # Ideal, stated Ae/At
    type_into("tradeAreaRatio", "40")
    select("tradeGamma", 1); select("tradeGamma", 0)
    trade.sortBy("specific_impulse"); settle()
    out["run_enabled_after_setup"] = named("tradeRun").property("enabled")
    out["candidates_text"] = named("tradeCandidates").property("text")
    for theme in ("dark", "light"):
        window.setProperty("themeMode", theme); settle(0.3)
    for w, h in ((1366, 768), (1920, 1080)):
        window.setProperty("width", w); window.setProperty("height", h); settle(0.3)
    window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
    window.setProperty("currentPageIndex", index); settle(0.5)
    out["browse_calls"] = dict(calls)

    # 2. Run trade, the real button
    calls.clear()
    QMetaObject.invokeMethod(named("tradeRun"), "clicked")
    deadline = time.perf_counter() + 120
    settle(0.2)
    while trade.property("busy") and time.perf_counter() < deadline:
        settle(0.1)
    settle(0.5)
    out["has_result"] = trade.property("hasResult")
    out["message"] = trade.property("message")
    out["solve_case_calls"] = calls.get(
        "rocketforge.application.analysis.thermochemistry_service.solve_case", 0)
    out["run_solves"] = sum(solves().values())
    out["run_call_names"] = sorted(calls)
    rows = trade.property("rows")
    rows = rows.toVariant() if hasattr(rows, "toVariant") else rows
    out["row_keys"] = [r["key"] for r in rows]
    out["rendered_rows"] = sorted(i.objectName() for i in items()
                                  if i.objectName().startswith("tradeRow_"))
    out["assumptions"] = [i.property("text") for i in items()
                          if i.objectName() == "tradeAssumption"]

    # 3. after the run: browse, select and apply solve nothing
    calls.clear()
    trade.sortBy("chamber_temperature"); trade.sortBy("chamber_temperature"); settle()
    if rows:
        first_ok = next((r["key"] for r in rows if r["ok"]), "")
        trade.selectCandidate(first_ok); settle()
        out["selected"] = trade.property("selectedKey")
        QMetaObject.invokeMethod(named("tradeApply"), "clicked"); settle()
        state = json.loads(req.property("stateJson"))
        out["requirement_pair"] = state["propellant"]
        out["stale_after_apply"] = trade.property("resultStale")
    for theme in ("dark", "light"):
        window.setProperty("themeMode", theme); settle(0.3)
    window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
    window.setProperty("currentPageIndex", index); settle(0.5)
    out["after_run_calls"] = dict(calls)
    out["page_instances"] = sum(1 for i in items() if i.objectName() == "tradeStatus")

    roots = [i for i in items() if i.metaObject().className().startswith("PropellantTradePage")]
    texts = [str(i.property("text")) for r in roots for i in items(r)
             if i.property("text") is not None]
    out["forbidden_text"] = sorted({p for p in FORBIDDEN_TEXT for t in texts if p in t})

    if os.environ.get("RF_TRADE_CAPTURE"):
        window.setProperty("width", 1920); window.setProperty("height", 1080)
        settle(0.6)
        window.grabWindow().save(os.environ["RF_TRADE_CAPTURE"])

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


def test_the_study_waits_for_stated_inputs(run):
    assert run["status_before"] == "Not run"
    assert run["run_enabled_before"] is False and run["issues_before"] == 2
    assert run["run_enabled_after_setup"] is True
    assert run["candidates_text"].startswith("12 candidates")
    assert "Red fuming" not in run["candidates_text"]


def test_run_trade_is_the_only_solve(run):
    if not _cea_installed():
        assert run["run_solves"] == 0 and not run["has_result"]
        assert "No thermochemistry provider" in run["message"]
        return
    assert run["solve_case_calls"] == 12, run["solve_case_calls"]
    assert run["has_result"] and len(run["row_keys"]) == 12
    assert sorted(f"tradeRow_{k}" for k in run["row_keys"]) == run["rendered_rows"]
    assert any("stated for this study" in text for text in run["assumptions"])
    assert any("Ae/At 40" in text for text in run["assumptions"])


def test_selection_reaches_the_requirement(run):
    if not _cea_installed():
        return
    assert run["selected"] and run["requirement_pair"] == {
        "mode": "explicit", "pair_key": run["selected"]}
    assert run["stale_after_apply"] is True


def test_no_warning_no_verdict_text_and_no_accumulating_pages(run):
    assert run["warnings"] == [], run["warnings"]
    assert run["forbidden_text"] == []
    assert run["page_instances"] == 1


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
