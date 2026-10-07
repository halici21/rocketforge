"""LIQ-5 in the running application: only Compute computes.

The real shell is started in a subprocess with every public function of the
layers below ``application`` and every service entry point wrapped in a
counter, plus the provider gateway's availability probe (as in the LIQ-4
runtime test). The geometry relation lives in ``rocketforge.engineering`` and
is therefore counted. Then:

1. **positive control** -- a real Isentropic solve registers calls;
2. **setup** -- a requirement, a one-pair trade at Ae/At 40 and a sizing,
   through their own controllers (needs NASA CEA);
3. **browsing** -- open Combustion Chamber Geometry, type, clear and retype
   the three inputs through the real fields, change theme and size, leave and
   return: **zero** calls;
4. **Compute** -- the real button: exactly one call of the geometry relation
   and no provider call;
5. **refusal** -- an L* below the convergent's volume, computed: refused, no
   numbers rendered;
6. **after computing** -- theme, re-entry and a new nozzle stated on the sizing
   page compute nothing, and the result reads as stale;
7. **negative control** -- another real solve registers calls again.
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
# The liquid-engine data modules hold state the controllers compare
# (fingerprints); they are records, not solvers.
EXCLUDED = ("rocketforge.engine.requirement", "rocketforge.engine.propellant_trade",
            "rocketforge.engine.chamber_sizing", "rocketforge.engine.chamber_geometry")
GATEWAY = "rocketforge.application.analysis.thermochemistry_provider"
GATEWAY_PROBES = ("availability", "chamber_provider", "_cea_module")
GEOMETRY = "rocketforge.engineering.chamber_geometry.relations.cylindrical_conical_chamber"
FORBIDDEN_TEXT = ("Best", "Optimal", "Optimum", "Recommended", "Score", "Feasible",
                  "complete combustion", "stable")


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
                  b' property var sizing: ChamberSizing; property var geo: ChamberGeometry }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_geometry_runtime.qml")))
    holder = probe.create()
    nav, iso, req, trade, sizing, geo = (holder.property(n) for n in
                                         ("nav", "iso", "req", "trade", "sizing", "geo"))

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

    def texts(prefix):
        return {i.objectName()[len(prefix):]: i.property("text") for i in items()
                if i.objectName().startswith(prefix)}

    out: dict = {"wrapped": len(wrappers)}
    settle(0.8)
    calls.clear()
    iso.setMachAndSolve(2.5); settle()
    out["positive_control_calls"] = total()

    # 1. setup: requirement, trade, sizing through their own controllers
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

    # 2. browsing
    calls.clear()
    index = nav.indexOfKey("chambergeometry")
    out["nav_index"] = index
    families = nav.property("families")
    out["family"] = [f["groups"][0]["items"] for f in families.toVariant()
                     if f["key"] == "liquidengine"] if hasattr(families, "toVariant") else []
    window.setProperty("currentPageIndex", index); settle(0.8)
    out["status_before"] = named("geometryStatus").property("text")
    out["issues_before"] = [i.property("text") for i in items()
                            if i.objectName() == "geometryIssue"]
    out["basis_before"] = [i.property("text") for i in items()
                           if i.objectName() == "geometryBasis"]
    out["run_enabled_empty"] = named("geometryRun").property("enabled")
    type_into("geometryLStar", "2"); type_into("geometryLStar", "")
    type_into("geometryLStar", "1"); type_into("geometryContraction", "3")
    type_into("geometryHalfAngle", "25")
    out["stated"] = [geo.property(n) for n in ("characteristicLengthText",
                                               "contractionRatioText", "halfAngleText")]
    out["run_enabled_stated"] = named("geometryRun").property("enabled")
    for theme in ("dark", "light"):
        window.setProperty("themeMode", theme); settle(0.3)
    for w, h in ((1366, 768), (1920, 1080)):
        window.setProperty("width", w); window.setProperty("height", h); settle(0.3)
    window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
    window.setProperty("currentPageIndex", index); settle(0.5)
    out["browse_calls"] = dict(calls)

    # 3. Compute, the real button
    calls.clear()
    if named("geometryRun").property("enabled"):
        QMetaObject.invokeMethod(named("geometryRun"), "clicked"); settle(0.6)
    out["has_result"] = geo.property("hasResult")
    out["status_after"] = named("geometryStatus").property("text")
    out["message"] = geo.property("message")
    out["geometry_calls"] = calls.get(GEOMETRY, 0)
    out["provider_calls"] = {k: n for k, n in calls.items()
                             if k.startswith(("rocketforge.providers", GATEWAY))}
    out["rendered_rows"] = sorted(i.objectName() for i in items()
                                  if i.objectName().startswith("geometryRow_"))
    out["values"] = texts("geometryValue_")
    out["sizing_throat"] = [sizing.result().value("throat_area"),
                            sizing.result().value("throat_diameter")] if out["sizing_ok"] else []
    out["result_quantities"] = (dict(geo.result().quantities)
                                if geo.property("hasResult") and geo.result().ok else {})
    out["sketch_visible"] = bool(named("geometrySketch") and named("geometrySketch").property("visible"))

    if os.environ.get("RF_GEOMETRY_CAPTURE"):
        target = pathlib.Path(os.environ["RF_GEOMETRY_CAPTURE"])
        for w, h, theme, suffix in ((1920, 1080, "light", ""), (1366, 768, "light", "_1366"),
                                    (1920, 1080, "dark", "_dark")):
            window.setProperty("themeMode", theme)
            window.setProperty("width", w); window.setProperty("height", h); settle(0.6)
            window.grabWindow().save(str(target.with_stem(target.stem + suffix)))
        window.setProperty("themeMode", "light")
        window.setProperty("width", 1920); window.setProperty("height", 1080); settle(0.3)

    # 4. refusal through the real field and button
    type_into("geometryLStar", "0.2")
    out["stale_on_edit"] = geo.property("resultStale")
    calls.clear()
    QMetaObject.invokeMethod(named("geometryRun"), "clicked"); settle(0.5)
    out["refused_status"] = named("geometryStatus").property("text")
    out["refused_message"] = geo.property("message")
    out["refused_values"] = texts("geometryValue_")
    out["refused_sketch_visible"] = bool(named("geometrySketch")
                                         and named("geometrySketch").property("visible"))
    if os.environ.get("RF_GEOMETRY_CAPTURE"):
        target = pathlib.Path(os.environ["RF_GEOMETRY_CAPTURE"])
        window.grabWindow().save(str(target.with_stem(target.stem + "_refused")))
    type_into("geometryLStar", "1")
    QMetaObject.invokeMethod(named("geometryRun"), "clicked"); settle(0.5)

    # 5. after computing: theme, re-entry and a change on the sizing page compute nothing
    calls.clear()
    for theme in ("dark", "light"):
        window.setProperty("themeMode", theme); settle(0.3)
    window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
    window.setProperty("currentPageIndex", index); settle(0.5)
    out["stale_before_change"] = geo.property("resultStale")
    sizing.setAreaRatio("25"); settle()
    out["stale_after_change"] = geo.property("resultStale")
    out["status_after_change"] = named("geometryStatus").property("text")
    out["issues_after_change"] = [i.property("text") for i in items()
                                  if i.objectName() == "geometryIssue"]
    out["after_run_calls"] = dict(calls)
    out["page_instances"] = sum(1 for i in items() if i.objectName() == "geometryStatus")

    roots = [i for i in items()
             if i.metaObject().className().startswith("ChamberGeometryPage")]
    page_texts = [str(i.property("text")) for r in roots for i in items(r)
                  if i.property("text") is not None]
    out["forbidden_text"] = sorted({p for p in FORBIDDEN_TEXT for t in page_texts if p in t})

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


def test_browsing_and_editing_compute_nothing(run):
    assert run["browse_calls"] == {}, run["browse_calls"]
    assert run["after_run_calls"] == {}, run["after_run_calls"]


def test_the_page_sits_in_the_liquid_engine_family(run):
    assert run["nav_index"] >= 0
    if run["family"]:
        assert run["nav_index"] in run["family"][0]


def test_the_inputs_are_read_through_the_real_fields(run):
    assert run["status_before"] == "Not computed"
    assert run["stated"] == ["1", "3", "25"]
    if not _cea_installed():
        assert run["run_enabled_stated"] is False
        assert any("No thrust-chamber sizing" in t for t in run["issues_before"])
        return
    assert run["sizing_ok"] is True
    assert run["run_enabled_empty"] is False
    assert any("State the characteristic length" in t for t in run["issues_before"])
    assert run["run_enabled_stated"] is True
    assert any(t.endswith("cm² · sizing") for t in run["basis_before"])


def test_compute_is_the_only_computation(run):
    if not _cea_installed():
        assert not run["has_result"]
        return
    assert run["geometry_calls"] == 1, run["geometry_calls"]
    assert run["provider_calls"] == {}, run["provider_calls"]
    assert run["has_result"] and run["status_after"] == "Computed", run["message"]
    assert len(run["rendered_rows"]) == 16
    assert all(v != "—" for v in run["values"].values()), run["values"]
    assert run["sketch_visible"] is True


def test_the_rendered_geometry_closes_on_the_liq4_throat(run):
    if not _cea_installed():
        return
    q = run["result_quantities"]
    at, dt = run["sizing_throat"]
    assert q["throat_area"] == at and q["throat_diameter"] == dt
    assert q["chamber_volume"] == pytest.approx(1.0 * at, rel=1e-15)
    assert abs(q["characteristic_length_closure"]) < 1e-13
    assert run["values"]["chamber_volume"] == f"{at * 1e6:,.1f}"
    assert run["values"]["characteristic_length"] == "1.0000"


def test_a_refusal_renders_no_numbers(run):
    if not _cea_installed():
        return
    assert run["stale_on_edit"] is True
    assert run["refused_status"] == "Refused"
    assert "smallest L*" in run["refused_message"]
    assert all(v == "—" for v in run["refused_values"].values())
    assert run["refused_sketch_visible"] is False


def test_a_change_upstream_makes_the_geometry_stale(run):
    if not _cea_installed():
        return
    assert run["stale_before_change"] is False
    assert run["stale_after_change"] is True
    assert run["status_after_change"].startswith("Stale")
    assert any("sizing is stale" in t for t in run["issues_after_change"])


def test_no_warning_no_verdict_text_and_no_accumulating_pages(run):
    assert run["warnings"] == [], run["warnings"]
    assert run["forbidden_text"] == []
    assert run["page_instances"] == 1


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
