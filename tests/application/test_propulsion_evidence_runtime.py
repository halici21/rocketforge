"""The Propulsion Database in the running application: zero solves, real QML.

A subprocess starts the real shell (main.configure_application and
main.build_engine, as the product does) with every public function of
``physics``, ``engineering``, ``engine``, ``providers`` and ``comparison`` --
and every solve/generate/run/evaluate entry point of the application's
services and provider gateways -- wrapped in a counter, each alias to it in
every loaded module re-bound to the wrapper, before QML is loaded.

Then, in order:

1. **positive control** -- a real Isentropic solve through its controller must
   register calls, or the instrument is proven blind;
2. **the EV-2 view sequence** -- open the page, load and browse the library,
   every filter (through the real QML controls), a zero match and its Clear
   button, the record and field inspector, the data drawer and a table row,
   the library drawer, both themes, three window sizes, and leaving and
   returning -- must register **zero** calls;
3. **the EV-3 sequence** -- the record opens "Not checked"; a click on the real
   "Check CEA compatibility" control is the only thing that probes the library
   (probes > 0, solves = 0), the state the page shows is the controller's, and
   theme, size and re-entry afterwards probe nothing again. Where a
   Thermochemistry workspace is wired to the Propulsion Database and the record
   is executable, the real "Open in Thermochemistry" control reaches that
   workspace with the published case loaded and nothing solved;
4. **negative control** -- another real solve must register calls again.

The provider gateway's availability, provider-construction and library-probe
functions are wrapped as well, so the EV-2 sequence also proves browsing never
touches the gateway. The same run checks that the route renders what the
controller holds, prints no Qt/QML warning, offers no solve or execution action
before a check, and does not accumulate page instances when left and re-entered.
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
FORBIDDEN_TEXT = ("Open in Thermochemistry", "CEA compatible", "CEA ready", "Validated",
                  "Run study", "Calculate")

#: Gateway functions that ask about, construct or probe the provider. Wrapped so
#: that a probe is visible to the instrument; a probe is not a solve.
GATEWAY_PROBES = ("availability", "chamber_provider", "provider_provenance", "_cea_module",
                  "probe_solid_library_species", "solid_ingredient_catalogue")
PROBE_NAMES = frozenset(GATEWAY_PROBES) | {"library_species_available", "check_availability",
                                           "load_cea", "discover_resources"}
SOLVE_PREFIXES = ("solve", "_solve", "calculate", "run", "evaluate", "compute", "generate",
                  "reanalyse")


def probe_calls(calls: dict) -> int:
    return sum(n for key, n in calls.items() if key.rsplit(".", 1)[-1] in PROBE_NAMES)


def solve_calls(calls: dict) -> dict:
    return {key: n for key, n in calls.items()
            if key.rsplit(".", 1)[-1].startswith(SOLVE_PREFIXES) or "solve" in key.rsplit(".", 1)[-1]}


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
        if module is None:
            continue
        lower, service = name.startswith(LOWER), bool(service_module.match(name))
        if not (lower or service):
            continue
        for attr, value in list(vars(module).items()):
            if inspect.isfunction(value) and value.__module__ == name:
                gateway_probe = (name == "rocketforge.application.analysis.thermochemistry_provider"
                                 and attr in GATEWAY_PROBES)
                if service and not entry.search(attr) and not gateway_probe:
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

    from PySide6.QtCore import (Q_ARG, QCoreApplication, QEvent, QMetaObject, QObject,
                                QtMsgType, QUrl, qInstallMessageHandler)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main

    warnings: list[str] = []
    qInstallMessageHandler(lambda kind, _c, message: warnings.append(str(message))
                           if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)
    app_main.configure_application()
    gc_limit = os.environ.get("QV4_GC_TIMELIMIT")
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]
    window.setProperty("width", 1920); window.setProperty("height", 1080)
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport RocketForge 1.0\nimport "data" as D\n'
                  b'QtObject { property var nav: D.Navigation; property var iso: Isentropic;'
                  b' property var ev: PropulsionEvidence; property var shell: D.ShellContext;'
                  b' property var thermo: Thermochemistry }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_evidence_runtime.qml")))
    holder = probe.create()
    nav, iso, ev, shell, thermo = (holder.property(n)
                                   for n in ("nav", "iso", "ev", "shell", "thermo"))

    def settle(seconds=0.35):
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

    def emit(obj, signal, *args):
        QMetaObject.invokeMethod(obj, signal, *args)
        settle()

    def total():
        return sum(calls.values())

    out: dict = {"wrapped": len(wrappers), "bindings": bindings, "gc_limit": gc_limit}
    settle(0.8)

    # 1. positive control
    calls.clear()
    iso.setMachAndSolve(2.5); settle()
    out["positive_control_calls"] = total()

    # 2. the EV-2 view sequence
    calls.clear()
    steps: list[tuple[str, int]] = []

    def step(label):
        steps.append((label, total()))

    index = nav.indexOfKey("evidence")
    out["nav_index"] = index
    out["reference_family_items"] = [f["groups"][0]["items"] for f in plain(nav.property("families"))
                                     if f["key"] == "reference"][0]
    window.setProperty("currentPageIndex", index); settle(0.8); step("enter page")
    title = named("evidenceRecordTitle")
    out["title_matches"] = title is not None and title.property("text") == ev.property("recordTitle") != ""
    lst = named("evidenceLibraryList")
    out["library_rows"] = lst.property("count") if lst else -1
    out["controller_rows"] = ev.property("visibleCount")
    out["selected"] = ev.property("selectedRecordId")
    va = named("capabilityStatus_VA"); vb = named("capabilityStatus_VB")
    out["capability_text"] = [va.property("text") if va else None, vb.property("text") if vb else None]
    step("read library and record")

    status = named("evidenceStatusFilter"); dim = named("evidenceDimensionFilter")
    ship = named("evidenceShippingFilter")
    statuses = [o["key"] for o in plain(ev.property("filterOptions"))["status"]]
    out["status_options"] = statuses
    for i in range(1, len(statuses) + 1):
        emit(status, "activated", Q_ARG(int, i))
    emit(dim, "activated", Q_ARG(int, 2))                 # VB
    emit(ship, "activated", Q_ARG(int, 1))
    step("filters through the QML controls")
    ev.setFilterShipping(""); ev.setFilterStatus("REGRESSION_LOCKED"); ev.setFilterDimension("VB"); settle()
    empty = named("evidenceEmptyState")
    out["no_match_state"] = ev.property("emptyState")
    out["no_match_visible"] = bool(empty and empty.property("visible"))
    out["no_match_selection"] = ev.property("selectedRecordId")
    emit(named("evidenceClearFilters"), "clicked")
    out["after_clear"] = [ev.property("emptyState"), ev.property("selectedRecordId"), ev.property("hasActiveFilter")]
    step("zero match and Clear filters")

    emit(named("evidenceProvenanceButton"), "clicked")
    inspector = named("evidenceInspector")
    out["inspector_open"] = bool(shell.property("inspectorOpen")) and inspector is not None
    ititle = named("evidenceInspectorTitle")
    out["inspector_title_is_record"] = bool(ititle and ititle.property("text") == ev.property("recordTitle"))
    step("record inspector")
    drawer = named("evidenceDataDrawer")
    drawer.setProperty("open", True); settle(0.5)
    emit(named("evidenceTable"), "rowClicked", Q_ARG(int, 3))
    out["row_inspection_key"] = ev.property("inspectionKey")
    ititle = named("evidenceInspectorTitle")
    out["inspector_title_row"] = ititle.property("text") if ititle else None
    values = [i.property("text") for i in items() if i.objectName() == "evidenceInspectorValue"]
    out["inspector_values"] = values
    ev.inspectDatum("density"); settle()
    out["missing_values"] = [i.property("text") for i in items() if i.objectName() == "evidenceInspectorValue"]
    emit(named("evidenceInspectRecord"), "clicked")
    out["back_to_record"] = ev.property("inspectionKey") == ""
    drawer.setProperty("open", False); shell.setProperty("inspectorOpen", False); settle()
    step("table row, missing field, inspector and drawer")
    library = named("evidenceLibraryDrawer")
    QMetaObject.invokeMethod(library, "setOpenByUser", Q_ARG("QVariant", False)); settle()
    QMetaObject.invokeMethod(library, "setOpenByUser", Q_ARG("QVariant", True)); settle()
    step("library drawer")
    for theme in ("light", "dark"):
        window.setProperty("themeMode", theme); settle(0.4)
    for w, h in ((1366, 768), (2560, 1440), (1920, 1080)):
        window.setProperty("width", w); window.setProperty("height", h); settle(0.4)
    step("theme and size")

    # the page and its inspector only: other shell text is not this page's claim
    shell.setProperty("inspectorOpen", True); settle(0.4)
    roots = [i for i in items() if i.metaObject().className().startswith("PropulsionEvidencePage")]
    roots += [i for i in items() if i.objectName() == "evidenceInspector"]
    page_texts = [str(i.property("text")) for r in roots for i in [r] + items(r)
                  if i.metaObject().className().startswith(("QQuickText", "RFButton", "RFToolButton"))
                  and i.property("text") is not None]
    out["page_text_count"] = len(page_texts)
    shell.setProperty("inspectorOpen", False); settle(0.3)
    out["forbidden_text"] = sorted({phrase for phrase in FORBIDDEN_TEXT
                                    for text in page_texts if phrase in text})
    counts = []
    for _ in range(3):
        window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.5)
        window.setProperty("currentPageIndex", index); settle(0.6)
        counts.append(sum(1 for i in items() if i.objectName() == "evidenceRecordTitle"))
    out["page_instances"] = counts
    step("leave and return x3")
    out["view_calls"] = total()
    out["view_call_names"] = sorted(calls)
    out["steps"] = steps

    # 3. the EV-3 sequence: only the explicit check probes; nothing solves
    calls.clear()
    window.setProperty("currentPageIndex", index); settle(0.6)
    ev.selectRecord("DS-RP1311-E5"); settle()
    chip = named("evidenceCompatibilityState")
    check = named("evidenceCompatibilityCheck")
    out["ev3_before"] = {
        "state": ev.property("compatibilityState"),
        "chip": chip.property("text") if chip else None,
        "check_visible": bool(check and check.property("visible")),
        "open_control": named("evidenceOpenThermochemistry") is not None,
        "calls": total()}
    emit(check, "clicked"); settle(0.6)
    chip = named("evidenceCompatibilityState")
    meaning = named("evidenceCompatibilityMeaning")
    open_control = named("evidenceOpenThermochemistry")
    out["ev3_after"] = {
        "state": ev.property("compatibilityState"),
        "label": ev.property("compatibilityLabel"),
        "chip": chip.property("text") if chip else None,
        "identity": ev.property("compatibilityIdentity"),
        "meaning_shows_identity": bool(meaning) and ev.property("compatibilityIdentity") != ""
                                  and ev.property("compatibilityIdentity") in meaning.property("text"),
        "blockers": ev.property("compatibilityBlockerCount"),
        "can_open": ev.property("canOpenInThermochemistry"),
        "open_reason": ev.property("openUnavailableReason"),
        "open_control": bool(open_control and open_control.property("visible")),
        "probes": probe_calls(calls), "solves": solve_calls(calls),
        "call_names": sorted(calls)}
    shell.setProperty("inspectorOpen", True); settle(0.4)
    out["ev3_inspector"] = [i.property("text") for i in items() if i.objectName() == "evidenceInspectorValue"]
    shell.setProperty("inspectorOpen", False); settle(0.3)
    calls.clear()
    for theme in ("dark", "light"):
        window.setProperty("themeMode", theme); settle(0.3)
    for w, h in ((1366, 768), (2560, 1440), (1920, 1080)):
        window.setProperty("width", w); window.setProperty("height", h); settle(0.3)
    window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.4)
    window.setProperty("currentPageIndex", index); settle(0.6)
    out["ev3_after_view_calls"] = total()
    out["ev3_state_after_reentry"] = ev.property("compatibilityState")
    out["ev3_opened"] = None
    open_control = named("evidenceOpenThermochemistry")
    if ev.property("canOpenInThermochemistry") and open_control is not None:
        calls.clear()
        emit(open_control, "clicked"); settle(0.8)
        out["ev3_opened"] = {
            "on_thermochem": int(window.property("currentPageIndex")) == nav.indexOfKey("thermochem"),
            "kind": thermo.property("formulationKind"),
            "reference_case": bool(thermo.property("solidIsReferenceCase")),
            "has_result": bool(thermo.property("hasResult")),
            "solves": solve_calls(calls)}
        window.setProperty("currentPageIndex", index); settle(0.6)

    # 4. negative control
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


def test_browsing_evidence_solves_nothing(run):
    assert run["view_calls"] == 0, (run["view_call_names"], run["steps"])
    assert [label for label, _ in run["steps"]] == [
        "enter page", "read library and record", "filters through the QML controls",
        "zero match and Clear filters", "record inspector",
        "table row, missing field, inspector and drawer", "library drawer",
        "theme and size", "leave and return x3"]


def test_the_route_renders_the_controller_state(run):
    assert run["nav_index"] >= 0 and run["title_matches"]
    assert run["reference_family_items"] == [11, run["nav_index"]]    # beside Equation Library
    assert run["status_options"] == ["REGRESSION_LOCKED", "NOT_APPLICABLE"]
    assert run["library_rows"] == run["controller_rows"] >= 1 and run["selected"]
    assert run["capability_text"] == ["Regression locked", "Not applicable"]


def test_zero_match_is_stated_and_recoverable(run):
    assert run["no_match_state"] == "no-match" and run["no_match_visible"]
    assert run["no_match_selection"] == ""
    assert run["after_clear"][0] == "" and run["after_clear"][1] and not run["after_clear"][2]


def test_the_inspector_reads_records_rows_and_missing_fields(run):
    assert run["inspector_open"] and run["inspector_title_is_record"]
    assert run["row_inspection_key"] == "ingredients[1].custom.formula.H"
    assert run["inspector_title_row"] == "CHOS-Binder · atoms of H"
    assert "1.86955" in run["inspector_values"] and "REPORTED" in run["inspector_values"]
    assert "cea 3.3.4 samples/rp1311/example5.py, line 44" in run["inspector_values"]
    assert "NOT_REPORTED" in run["missing_values"] and run["back_to_record"]


def test_the_compatibility_check_is_explicit_and_solves_nothing(run):
    before, after = run["ev3_before"], run["ev3_after"]
    assert before == {"state": "NOT_CHECKED", "chip": "Not checked", "check_visible": True,
                      "open_control": False, "calls": 0}
    assert after["probes"] > 0, after["call_names"]
    assert after["solves"] == {}, after["solves"]
    assert after["chip"] == after["label"] != "Not checked"
    if after["state"] == "EXECUTABLE_VERIFIED":                    # NASA CEA installed
        assert "8e5df1cca92d4a48663d1ee5a1372e6508c59cddc2247ceeca32f041a03ec52a" in after["identity"]
    else:
        assert after["state"] == "PROVIDER_UNAVAILABLE" and "unavailable" in after["identity"]
    assert after["meaning_shows_identity"] and after["blockers"] == 0
    assert "Executable · verified" in run["ev3_inspector"] or \
        "Provider unavailable" in run["ev3_inspector"]
    # the answer stays with its record; theme, size and re-entry probe nothing
    assert run["ev3_after_view_calls"] == 0
    assert run["ev3_state_after_reentry"] == after["state"]


def test_open_in_thermochemistry_loads_and_does_not_solve(run):
    after = run["ev3_after"]
    if after["state"] != "EXECUTABLE_VERIFIED":
        assert not after["can_open"] and not after["open_control"]
        return
    # main.py hands the Thermochemistry controller to the Propulsion Database,
    # so a verified record must be openable: losing that wiring fails here.
    assert after["can_open"], after["open_reason"]
    assert after["open_control"] and after["open_reason"] == ""
    opened = run["ev3_opened"]
    assert opened["on_thermochem"], opened
    assert opened["kind"] == "solid" and opened["reference_case"] and not opened["has_result"]
    assert opened["solves"] == {}, opened["solves"]


def test_no_warning_no_action_and_no_accumulating_pages(run):
    assert run["warnings"] == [], run["warnings"]
    assert run["page_text_count"] > 40 and run["forbidden_text"] == []
    assert run["page_instances"] == [1, 1, 1]
    assert run["gc_limit"] == "0"                       # the shipped one-pass collector


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
