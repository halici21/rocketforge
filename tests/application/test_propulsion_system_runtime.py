"""The propulsion-system pages (SYS gates) in the running application.

The real shell is started in a subprocess with every public function of the
layers below ``application`` and every service entry point wrapped in a
counter, plus both provider gateways' probes. The SYS relations live in
``rocketforge.engineering`` and are therefore counted. Then:

1. **positive control** -- a real Isentropic solve registers calls;
2. **setup** -- a requirement, a one-pair trade at Ae/At 40, a sizing and an
   injector study through their own controllers (needs NASA CEA);
3. **browsing** -- open each SYS page in turn, type, clear and retype inputs
   through the real fields, switch choices, change theme and size, leave and
   return: **zero** calls;
4. **Compute** -- each page's real button, in upstream order: its relations
   are reached and no provider is;
5. **after computing** -- theme and re-entry compute nothing; a change on the
   sizing page makes every SYS result stale without computing;
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
# The liquid-engine and propulsion-system data modules hold state the
# controllers compare (fingerprints); they are records, not solvers.
EXCLUDED_PREFIXES = ("rocketforge.engine.requirement", "rocketforge.engine.propellant_trade",
                     "rocketforge.engine.chamber_sizing", "rocketforge.engine.chamber_geometry",
                     "rocketforge.engine.injector", "rocketforge.engine.propulsion_system")
GATEWAYS = {"rocketforge.application.analysis.thermochemistry_provider":
            ("availability", "chamber_provider", "_cea_module"),
            "rocketforge.application.analysis.fluid_property_provider":
            ("availability", "property_provider")}
FORBIDDEN_TEXT = ("Best", "Optimal", "Optimum", "Recommended", "Score", "Feasible",
                  "guaranteed", "is available at the outlet")

#: Each SYS page, in upstream order: (nav key, objectName prefix, singleton,
#: relation module counted on Compute, [(field key, kind, value)]).
PAGES = [
    ("propellantinventory", "inventory", "PropellantInventory",
     "rocketforge.engineering.propulsion_system.inventory.branch_inventory",
     [(f"{b}.{k}", kind, v) for b in ("oxidiser", "fuel") for k, kind, v in (
         ("residual_mode", "choice", "expulsion_efficiency"),
         ("expulsion_efficiency", "number", "98"),
         ("reserve_mode", "choice", "stated_fraction"),
         ("reserve", "number", "2"),
         ("start_stop_mode", "choice", "not_applicable"),
         ("chilldown_mode", "choice", "not_applicable"),
         ("other_allowance_mode", "choice", "not_applicable"),
         ("boiloff_mode", "choice", "not_applicable"))]),
    ("tankgeometry", "tanks", "PropellantTanks",
     "rocketforge.engineering.propulsion_system.tank_geometry.solve_tank_geometry",
     [("oxidiser.density", "number", "1141"), ("oxidiser.ullage_mode", "choice", "fraction"),
      ("oxidiser.ullage", "number", "5"), ("oxidiser.shape", "choice", "sphere"),
      ("fuel.density", "number", "422.6"), ("fuel.ullage_mode", "choice", "fraction"),
      ("fuel.ullage", "number", "5"), ("fuel.shape", "choice", "cylinder_ellipsoidal"),
      ("fuel.sizing_mode", "choice", "stated_diameter"), ("fuel.diameter", "number", "4"),
      ("fuel.dome_ratio", "number", "0.7071")]),
    ("propellantmanagement", "management", "PropellantManagement",
     "rocketforge.engineering.propulsion_system.propellant_management.management_state",
     [("oxidiser.mode", "choice", "settled"), ("oxidiser.environment", "choice", "accelerated"),
      ("oxidiser.settling", "choice", "not_required"),
      ("fuel.mode", "choice", "diaphragm"), ("fuel.environment", "choice", "low_gravity"),
      ("fuel.settling", "choice", "not_required"),
      ("fuel.settling_acceleration", "number", "0.05")]),
]


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
        if module is None or name.startswith(EXCLUDED_PREFIXES):
            continue
        lower, service = name.startswith(LOWER), bool(service_module.match(name))
        if not (lower or service):
            continue
        for attr, value in list(vars(module).items()):
            if inspect.isfunction(value) and value.__module__ == name:
                probe = attr in GATEWAYS.get(name, ())
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
    singletons = ["Isentropic", "EngineRequirement", "PropellantTrade", "ChamberSizing",
                  "Injector"] + [p[2] for p in PAGES]
    source = ('import QtQuick\nimport RocketForge 1.0\nimport "data" as D\nQtObject { '
              'property var nav: D.Navigation; '
              + " ".join(f"property var s{i}: {n};" for i, n in enumerate(singletons)) + " }")
    probe = QQmlComponent(engine)
    probe.setData(source.encode(), QUrl.fromLocalFile(str(app_main.UI_DIR / "_sys_runtime.qml")))
    holder = probe.create()
    nav = holder.property("nav")
    ctl = {n: holder.property(f"s{i}") for i, n in enumerate(singletons)}
    iso, req, trade, sizing, inj = (ctl[n] for n in singletons[:5])

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
        if field is None:
            return False
        field.setProperty("text", text)
        QMetaObject.invokeMethod(field, "edited"); settle(0.1)
        return True

    def total():
        return sum(calls.values())

    def texts(prefix):
        return {i.objectName()[len(prefix):]: i.property("text") for i in items()
                if i.objectName().startswith(prefix)}

    out: dict = {"wrapped": len(wrappers), "pages": {}}
    settle(0.8)
    calls.clear()
    iso.setMachAndSolve(2.5); settle()
    out["positive_control_calls"] = total()

    # 1. setup through the upstream controllers
    req.setThrust("1000"); req.setBurnTime("200"); req.setPair("sutton-o2-ch4"); settle()
    trade.setStudyPressure("10"); trade.setRatioMode("catalogue")
    trade.setPerformanceBasis("ideal_area_ratio"); trade.setAreaRatio("40")
    trade.runTrade()
    deadline = time.perf_counter() + 120
    settle(0.2)
    while trade.property("busy") and time.perf_counter() < deadline:
        settle(0.1)
    trade.selectCandidate("sutton-o2-ch4"); settle()
    if sizing.property("canSize"):
        sizing.runSizing(); settle()
    out["sizing_ok"] = sizing.property("resultOk")
    # The injector, with a complete ledger, for the feed network's closure.
    for b, dp, cd, rho in (("oxidiser", "20", "0.8", "1141"), ("fuel", "15", "0.75", "422.6")):
        inj.setValue(b, "pressure_drop", dp); inj.setValue(b, "discharge_coefficient", cd)
        inj.setValue(b, "density", rho)
        for term, mode, value in (("feed_line_loss", "stated", "5"), ("valve_loss", "stated", "2"),
                                  ("cooling_jacket_loss", "not_applicable", ""),
                                  ("dynamic_head", "stated", "0.5"),
                                  ("other_loss", "not_applicable", ""),
                                  ("margin", "stated", "1")):
            inj.setLossMode(b, term, mode)
            if value:
                inj.setLossValue(b, term, value)
    settle()
    if inj.property("canCompute"):
        inj.computeInjector(); settle()
    out["injector_ok"] = inj.property("resultOk")

    families = nav.property("families")
    family = ([f["groups"][0]["items"] for f in families.toVariant()
               if f["key"] == "propulsionsystem"] if hasattr(families, "toVariant") else [])
    out["family"] = family

    # 2 and 3: per page, browse then Compute
    for key, prefix, singleton, relation, fields in PAGES:
        c = ctl[singleton]
        page: dict = {}
        calls.clear()
        index = nav.indexOfKey(key)
        page["nav_index"] = index
        window.setProperty("currentPageIndex", index); settle(0.8)
        page["status_before"] = named(prefix + "Status").property("text")
        page["issues_before"] = [i.property("text") for i in items()
                                 if i.objectName() == prefix + "Issue"]
        page["basis_rows"] = [i.property("text") for i in items()
                              if i.objectName() == prefix + "Basis"]
        typed = []
        for field, kind, value in fields:
            if kind == "number":
                typed.append(type_into(f"{prefix}_{field}", "123"))
                type_into(f"{prefix}_{field}", "")
                typed.append(type_into(f"{prefix}_{field}", value))
            elif kind == "text":
                typed.append(type_into(f"{prefix}_{field}", value))
            elif kind == "action":
                button = named(f"{prefix}_action_{field}_{value}")
                typed.append(button is not None)
                if button is not None:
                    QMetaObject.invokeMethod(button, "clicked"); settle(0.1)
            else:
                c.setChoice(field, value); settle(0.05)
        page["typed_all"] = all(typed)
        for theme in ("dark", "light"):
            window.setProperty("themeMode", theme); settle(0.3)
        for w, h in ((1366, 768), (1920, 1080)):
            window.setProperty("width", w); window.setProperty("height", h); settle(0.3)
        window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
        window.setProperty("currentPageIndex", index); settle(0.5)
        page["browse_calls"] = dict(calls)
        page["run_enabled"] = named(prefix + "Run").property("enabled")
        page["issues_after_typing"] = [i["message"] for i in c.property("issues")]

        calls.clear()
        if page["run_enabled"]:
            QMetaObject.invokeMethod(named(prefix + "Run"), "clicked"); settle(0.6)
        page["has_result"] = c.property("hasResult")
        page["status_after"] = named(prefix + "Status").property("text")
        page["message"] = c.property("message")
        page["relation_calls"] = calls.get(relation, 0)
        page["provider_calls"] = {k: n for k, n in calls.items()
                                  if k.startswith(("rocketforge.providers",) + tuple(GATEWAYS))}
        page["values"] = {b: texts(f"{prefix}_{b}_Value_") for b in ("oxidiser", "fuel")}
        page["totals"] = texts(prefix + "TotalValue_")
        page["labels"] = {b: texts(f"{prefix}_{b}_labelValue_") for b in ("oxidiser", "fuel")}
        page["ledger"] = {b: texts(f"{prefix}_{b}_ledgerValue_") for b in ("oxidiser", "fuel")}
        if page["has_result"] and c.result().ok:
            r = c.result()
            page["quantities"] = {"oxidiser": dict(r.oxidiser.quantities),
                                  "fuel": dict(r.fuel.quantities), "totals": dict(r.totals)}
        if os.environ.get("RF_SYS_CAPTURE"):
            target = pathlib.Path(os.environ["RF_SYS_CAPTURE"]) / f"{key}.png"
            for w, h, theme, suffix in ((1920, 1080, "light", ""), (1366, 768, "light", "_1366"),
                                        (1920, 1080, "dark", "_dark")):
                window.setProperty("themeMode", theme)
                window.setProperty("width", w); window.setProperty("height", h); settle(0.6)
                window.grabWindow().save(str(target.with_stem(target.stem + suffix)))
            scroll = named(prefix + "Scroll")
            scroll.setProperty("contentY", max(0.0, scroll.property("contentHeight")
                                               - scroll.property("height"))); settle(0.4)
            window.grabWindow().save(str(target.with_stem(target.stem + "_results")))
            scroll.setProperty("contentY", 0.0)
            window.setProperty("themeMode", "light")
            window.setProperty("width", 1920); window.setProperty("height", 1080); settle(0.3)
        roots = [i for i in items() if i.objectName() == prefix + "Status"]
        page["page_instances"] = len(roots)
        page_texts = [str(i.property("text")) for i in items() if i.property("text") is not None]
        page["forbidden_text"] = sorted({p for p in FORBIDDEN_TEXT for t in page_texts if p in t})
        out["pages"][key] = page

    # 5. after computing: re-entry computes nothing; a sizing change stales every SYS result
    calls.clear()
    for key, prefix, *_rest in PAGES:
        window.setProperty("currentPageIndex", nav.indexOfKey(key)); settle(0.4)
    out["stale_before_change"] = {p[2]: ctl[p[2]].property("resultStale") for p in PAGES}
    sizing.setAreaRatio("25"); settle()
    out["stale_after_change"] = {p[2]: ctl[p[2]].property("resultStale") for p in PAGES}
    out["status_after_change"] = named(PAGES[-1][1] + "Status").property("text")
    out["after_run_calls"] = dict(calls)

    calls.clear()
    iso.setMachAndSolve(3.0); settle()
    out["negative_control_calls"] = total()
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
    assert run["wrapped"] > 200
    assert run["positive_control_calls"] > 0 and run["negative_control_calls"] > 0


@pytest.mark.parametrize("key", [p[0] for p in PAGES])
def test_browsing_and_editing_compute_nothing(run, key):
    page = run["pages"][key]
    assert page["browse_calls"] == {}, page["browse_calls"]
    assert page["typed_all"], "a field was not found by its objectName"


def test_nothing_is_computed_after_the_run(run):
    assert run["after_run_calls"] == {}, run["after_run_calls"]


@pytest.mark.parametrize("key", [p[0] for p in PAGES])
def test_the_pages_sit_in_the_propulsion_system_family(run, key):
    index = run["pages"][key]["nav_index"]
    assert index >= 0
    if run["family"]:
        assert index in run["family"][0]


@pytest.mark.parametrize("key", [p[0] for p in PAGES])
def test_compute_is_the_only_computation(run, key):
    page = run["pages"][key]
    assert page["status_before"] == "Not computed"
    if not _cea_installed():
        assert not page["has_result"] and not page["run_enabled"]
        assert page["issues_before"], "a page without its upstream says why"
        return
    assert run["sizing_ok"] is True
    assert page["relation_calls"] >= 2, page
    assert page["provider_calls"] == {}, page["provider_calls"]
    assert page["has_result"] and page["status_after"].startswith("Computed"), page["message"]
    assert "incomplete" not in page["status_after"], page["message"]


def test_the_inventory_renders_its_closed_masses(run):
    if not _cea_installed():
        return
    page = run["pages"]["propellantinventory"]
    q = page["quantities"]
    for branch in ("oxidiser", "fuel"):
        b = q[branch]
        assert b["usable_mass"] == b["mass_flow"] * 200.0
        assert b["loaded_mass"] == pytest.approx(b["usable_mass"] * 1.02 / 0.98, rel=1e-14)
        assert page["values"][branch]["loaded_mass"] == f"{b['loaded_mass']:,.4f}"
        assert page["values"][branch]["expulsion_efficiency"] == "98.0000"
    assert page["totals"]["loaded_total"] == f"{q['totals']['loaded_total']:,.4f}"


def test_the_tanks_render_volumes_that_hold_the_inventory(run):
    if not _cea_installed():
        return
    inv = run["pages"]["propellantinventory"]["quantities"]
    page = run["pages"]["tankgeometry"]
    q = page["quantities"]
    ox, fu = q["oxidiser"], q["fuel"]
    assert ox["liquid_mass"] == inv["oxidiser"]["loaded_mass"]
    assert ox["tank_volume"] == pytest.approx(ox["liquid_mass"] / 1141.0 / 0.95, rel=1e-14)
    assert fu["diameter"] == 4.0 and fu["barrel_length"] > 0.0
    assert abs(fu["volume_closure"]) < 1e-14
    assert page["values"]["oxidiser"]["tank_volume"] == f"{ox['tank_volume']:,.6f}"


def test_management_declares_and_closes_its_volumes(run):
    if not _cea_installed():
        return
    page = run["pages"]["propellantmanagement"]
    for branch in ("oxidiser", "fuel"):
        b = page["quantities"][branch]
        assert b["gas_volume_end"] + b["residual_volume"] == pytest.approx(b["tank_volume"],
                                                                           rel=1e-14)
    labels = page["labels"]
    assert labels["oxidiser"]["outlet_availability"].startswith("Declared: settled")
    assert labels["fuel"]["outlet_availability"].startswith("Declared: positive-expulsion")
    assert page["quantities"]["fuel"]["settling_acceleration"] == 0.05


def test_a_change_upstream_makes_every_sys_result_stale(run):
    if not _cea_installed():
        return
    assert not any(run["stale_before_change"].values()), run["stale_before_change"]
    assert all(run["stale_after_change"].values()), run["stale_after_change"]
    assert run["status_after_change"].startswith("Stale")


def test_no_warning_no_verdict_text_and_no_accumulating_pages(run):
    assert run["warnings"] == [], run["warnings"]
    for key, page in run["pages"].items():
        assert page["forbidden_text"] == [], (key, page["forbidden_text"])
        assert page["page_instances"] == 1, key


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
