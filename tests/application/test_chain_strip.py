"""R3-F: the design-chain strip shows each step's state and only navigates.

In a subprocess running the real shell, with every service entry point counted:

1. on each of the ten chain pages the strip lists its chain's five steps in order, the page's own
   step is the current one, and the states follow the controllers (nothing solved: the
   requirement is "incomplete", every other step "none");
2. a click on another step, and Enter on a focused one, open that step's page and solve nothing;
3. stating the requirement turns its step "stated"; with NASA CEA installed, running the trade
   turns that step "done", and changing the requirement afterwards turns it "stale";
4. with NASA CEA installed, a step says what its page says about an unusable result: a refused
   sizing and an incomplete propellant inventory are an "issue" showing the page's own label,
   a trade in which no candidate solved is an "issue" ("No usable candidate"), and a usable
   sizing is "done".
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import time

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
LIQUID = ["requirement", "propellanttrade", "chambersizing", "chambergeometry", "injector"]
SYSTEM = ["propellantinventory", "tankgeometry", "propellantmanagement", "tankpressurization",
          "feednetwork"]


def _drive() -> dict:
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if sys.platform == "win32":
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
    import functools
    import importlib
    import inspect
    import pkgutil

    import rocketforge

    for info in pkgutil.walk_packages(rocketforge.__path__, "rocketforge."):
        try:
            importlib.import_module(info.name)
        except Exception:
            pass

    service_module = re.compile(r"^rocketforge\.application\.analysis\.\w+_service$")
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
        if module is None or not service_module.match(name):
            continue
        for attr, value in list(vars(module).items()):
            if inspect.isfunction(value) and value.__module__ == name and entry.search(attr):
                wrappers[id(value)] = wrap(value, f"{name}.{attr}")
    for name, module in list(sys.modules.items()):
        if module is None or not (name.startswith("rocketforge") or name == "main"):
            continue
        for attr, value in list(vars(module).items()):
            if inspect.isfunction(value) and id(value) in wrappers:
                setattr(module, attr, wrappers[id(value)])

    from PySide6.QtCore import QCoreApplication, QEvent, QPointF, Qt, QtMsgType, QUrl
    from PySide6.QtCore import qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent
    from PySide6.QtTest import QTest

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
                  b'QtObject { property var nav: D.Navigation; property var req: EngineRequirement;'
                  b' property var trade: PropellantTrade; property var sizing: ChamberSizing;'
                  b' property var inventory: PropellantInventory }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_chain_strip_runtime.qml")))
    holder = probe.create()
    nav, req, trade, sizing, inventory = (holder.property(n)
                                          for n in ("nav", "req", "trade", "sizing", "inventory"))
    keys = [item["key"] for item in nav.property("items").toVariant()]

    def settle(seconds=0.3):
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def items():
        out, stack = [], [window.contentItem()]
        while stack:
            node = stack.pop()
            for child in node.childItems():
                out.append(child)
                stack.append(child)
        return out

    def strip():
        steps = {}
        for item in items():
            name = item.objectName()
            if name.startswith("chainStep_") and item.isVisible():
                steps[name[len("chainStep_"):]] = (item.property("stepState"), item.property("current"),
                                                   item.mapToScene(QPointF(0, 0)).x())
        order = sorted(steps, key=lambda k: steps[k][2])
        return {"order": order, "state": {k: steps[k][0] for k in order},
                "current": [k for k in order if steps[k][1]]}

    def named(prefix):
        return next(i for i in items() if i.objectName() == prefix and i.isVisible())

    def total():
        return sum(calls.values())

    out: dict = {"wrapped": len(wrappers)}
    pages = {}
    for key in LIQUID + SYSTEM:
        window.setProperty("currentPageIndex", nav.indexOfKey(key)); settle(0.8)
        pages[key] = strip()
    out["pages"] = pages

    # a click on another step opens it, and solves nothing
    window.setProperty("currentPageIndex", nav.indexOfKey("chambersizing")); settle(0.8)
    start = total()
    target = named("chainStep_propellanttrade")
    centre = target.mapToScene(QPointF(target.width() / 2, target.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, centre); settle(0.8)
    out["clicked"] = keys[window.property("currentPageIndex")]
    # Enter on a focused step
    target = named("chainStep_injector")
    target.forceActiveFocus(); settle(0.2)
    QTest.keyClick(window, Qt.Key_Return); settle(0.8)
    out["entered"] = keys[window.property("currentPageIndex")]
    # a click on the current step does nothing
    current = named("chainStep_injector")
    centre = current.mapToScene(QPointF(current.width() / 2, current.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, centre); settle(0.5)
    out["current_click"] = keys[window.property("currentPageIndex")]
    out["navigation_calls"] = total() - start

    # the requirement's step follows the requirement
    req.setThrust("1000"); req.setBurnTime("200"); req.setPair("sutton-o2-ch4"); settle(0.5)
    out["stated"] = strip()["state"].get("requirement")

    # with CEA, a trade's step turns done, then stale when the requirement changes
    trade.setStudyPressure("10"); trade.setRatioMode("catalogue")
    trade.setPerformanceBasis("ideal_area_ratio"); trade.setAreaRatio("40")
    out["can_run"] = bool(trade.property("canRun"))
    if out["can_run"]:
        trade.runTrade()
        deadline = time.perf_counter() + 300
        while trade.property("busy") and time.perf_counter() < deadline:
            settle(0.2)
        settle(0.5)
        out["after_trade"] = strip()["state"].get("propellanttrade")
        req.setThrust("1200"); settle(0.5)
        out["after_change"] = strip()["state"].get("propellanttrade")

        # sizing: the strip says what the sizing controller says, usable or not
        trade.runTrade()
        deadline = time.perf_counter() + 300
        while trade.property("busy") and time.perf_counter() < deadline:
            settle(0.2)
        trade.selectCandidate("sutton-o2-ch4"); settle(0.5)
        sizing_cases = []
        for ratio in ("100000", ""):      # far past any expansion (refused), then the trade's nozzle
            sizing.setAreaRatio(ratio); settle(0.2)
            sizing.runSizing(); settle(0.8)
            window.setProperty("currentPageIndex", nav.indexOfKey("chambergeometry")); settle(0.8)
            labels = {i.objectName(): i.property("stateLabel") for i in items()
                      if i.objectName().startswith("chainStep_")}
            sizing_cases.append({"ratio": ratio, "ok": bool(sizing.property("resultOk")),
                                 "has": bool(sizing.property("hasResult")),
                                 "status": sizing.property("statusLabel"),
                                 "state": strip()["state"].get("chambersizing"),
                                 "label": labels.get("chainStep_chambersizing")})
        out["sizing"] = sizing_cases

        # an inventory with its terms left unresolved is computed but incomplete
        inventory.compute(); settle(0.8)
        window.setProperty("currentPageIndex", nav.indexOfKey("tankgeometry")); settle(0.8)
        labels = {i.objectName(): i.property("stateLabel") for i in items()
                  if i.objectName().startswith("chainStep_")}
        out["inventory"] = {"status": inventory.property("resultStatus"),
                            "ok": bool(inventory.property("resultOk")),
                            "label_page": inventory.property("statusLabel"),
                            "state": strip()["state"].get("propellantinventory"),
                            "label": labels.get("chainStep_propellantinventory")}

        # a trade in which no candidate solves: an O/F far outside any combustion
        trade.setRatioMode("explicit"); trade.setStudyRatio("500")
        trade.runTrade()
        deadline = time.perf_counter() + 300
        while trade.property("busy") and time.perf_counter() < deadline:
            settle(0.2)
        settle(0.5)
        window.setProperty("currentPageIndex", nav.indexOfKey("chambersizing")); settle(0.8)
        labels = {i.objectName(): i.property("stateLabel") for i in items()
                  if i.objectName().startswith("chainStep_")}
        out["failed_trade"] = {"ok": bool(trade.property("resultOk")),
                               "has": bool(trade.property("hasResult")),
                               "page": trade.property("statusLabel"),
                               "state": strip()["state"].get("propellanttrade"),
                               "label": labels.get("chainStep_propellanttrade")}
    out["warnings"] = warnings
    return out


def _run() -> dict:
    completed = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve())], cwd=PROJECT_ROOT,
        env=dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONUNBUFFERED="1"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
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
    assert run["wrapped"] > 20


@pytest.mark.parametrize("key", LIQUID + SYSTEM)
def test_each_chain_page_shows_its_chain_in_order_with_itself_current(run, key):
    page = run["pages"][key]
    chain = LIQUID if key in LIQUID else SYSTEM
    assert page["order"] == chain
    assert page["current"] == [key]
    expected = {k: ("incomplete" if k == "requirement" else "none") for k in chain}
    assert page["state"] == expected


def test_a_step_only_navigates(run):
    assert run["clicked"] == "propellanttrade"
    assert run["entered"] == "injector"
    assert run["current_click"] == "injector"          # the current step is not a link
    assert run["navigation_calls"] == 0


def test_the_requirement_step_follows_the_requirement(run):
    assert run["stated"] == "stated"


def test_a_result_step_is_done_and_then_stale(run):
    if not _cea_installed():
        pytest.skip("NASA CEA is not installed; the trade cannot run")
    assert run["can_run"]
    assert run["after_trade"] == "done"
    assert run["after_change"] == "stale"


def test_a_result_step_says_what_its_page_says(run):
    """A refused or incomplete result is never "done": it shows the page's own status label."""
    if not _cea_installed():
        pytest.skip("NASA CEA is not installed; nothing can be sized")
    cases = run["sizing"]
    assert all(c["has"] for c in cases), cases
    for c in cases:
        if c["ok"]:
            assert (c["state"], c["label"]) == ("done", "Done"), c
        else:
            assert (c["state"], c["label"]) == ("issue", c["status"]), c
    assert any(not c["ok"] for c in cases), ("no refused case was produced", cases)
    assert any(c["ok"] for c in cases), ("no usable case was produced", cases)


def test_an_incomplete_study_is_never_done(run):
    """An incomplete inventory is ok (not refused) yet the next step refuses it."""
    if not _cea_installed():
        pytest.skip("NASA CEA is not installed; nothing can be sized")
    inv = run["inventory"]
    assert inv["status"] == "incomplete" and inv["ok"], inv
    assert (inv["state"], inv["label"]) == ("issue", inv["label_page"]), inv


def test_a_trade_with_no_usable_candidate_is_never_done(run):
    """Every candidate failed: the page still says "Evaluated", but nothing can be selected."""
    if not _cea_installed():
        pytest.skip("NASA CEA is not installed; the trade cannot run")
    t = run["failed_trade"]
    assert t["has"] and not t["ok"], t
    assert (t["state"], t["label"]) == ("issue", "No usable candidate"), t


def test_no_qml_warning(run):
    assert run["warnings"] == [], run["warnings"]


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
