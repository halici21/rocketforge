"""Reference Engines (DB-3A) in the running application: zero solves, real QML.

A subprocess starts the real shell (main.configure_application and
main.build_engine, as the product does) with every public function of
``physics``, ``engineering``, ``engine``, ``providers`` and ``comparison`` --
and every solve/generate/run/evaluate entry point of the application's
services and provider gateways, plus the gateway's availability and probe
functions -- wrapped in a counter, each alias re-bound, before QML is loaded.

Then, in order:

1. **positive control** -- a real Isentropic solve must register calls, or the
   instrument is proven blind;
2. **the DB-3A view sequence** -- open the page; search; every filter through
   the real QML controls; a zero match and its Clear button; every configuration
   selected in turn; the capability, assertion, source, graph, node and edge
   inspector; zoom, fit and reset; the data drawer with both tables and a row of
   each; the library drawer; both themes; three window sizes; and leaving and
   returning -- must register **zero** calls and **zero** probes;
3. **negative control** -- another real solve must register calls again.

The same run checks that the route renders what the controller holds, shows
the honesty statements the contract asks for (unknown station, third-party
reconstruction, layout disclaimer, no-topology state, eligibility-only
regression), prints no Qt/QML warning, offers no edit or solve action, and does
not accumulate page instances when left and re-entered.
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
#: Words that would offer an action this read-only workspace must not have, or a
#: claim it must not make. Matched against whole button/tool labels and page text.
FORBIDDEN_ACTIONS = ("Edit", "Save", "Delete", "Create", "Import", "Promote", "Override", "Calculate",
                     "Run", "Solve", "Accept", "Lock")
FORBIDDEN_CLAIMS = ("Validated", "validated reference", "Score", "★", "stars")
GATEWAY_PROBES = ("availability", "chamber_provider", "provider_provenance", "_cea_module",
                  "probe_solid_library_species", "solid_ingredient_catalogue")
CONFIGS = ("CFG-J2-230K", "CFG-F1", "CFG-H1-188K-SA10", "CFG-LMDE-FINAL", "CFG-J2S", "CFG-IPD",
           "CFG-RD-170", "CFG-RS-68A", "CFG-LR87-AJ-11-T3E", "CFG-RL10B-2-DIV")


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

    # The workspace must not reach the network or the research tree at runtime.
    # builtins.open and io.open are both watched: pathlib reads go through io.open.
    import builtins
    import io
    import socket
    opened: list[str] = []
    real_open = io.open

    def watched_open(file, *args, **kwargs):
        opened.append(str(file))
        return real_open(file, *args, **kwargs)

    def watch(on: bool) -> None:
        builtins.open = io.open = watched_open if on else real_open
        socket.socket = NoSocket if on else NoSocket.__mro__[1]

    sockets: list[str] = []

    class NoSocket(socket.socket):
        def connect(self, address):          # noqa: D401 - a counter, not an API
            sockets.append(str(address))
            raise OSError("network disabled in this test")

    from PySide6.QtCore import (Q_ARG, QCoreApplication, QEvent, QMetaObject, QtMsgType, QUrl,
                                qInstallMessageHandler)
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
                  b' property var re: ReferenceEngines; property var shell: D.ShellContext }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_engines_runtime.qml")))
    holder = probe.create()
    nav, iso, rex, shell = (holder.property(n) for n in ("nav", "iso", "re", "shell"))

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

    def emit(obj, signal, *args):
        QMetaObject.invokeMethod(obj, signal, *args)
        settle()

    def texts(root):
        return [str(i.property("text")) for i in [root] + items(root)
                if i.metaObject().className().startswith(("QQuickText", "RFButton", "RFToolButton",
                                                          "RFStatusChip", "RFSectionLabel"))
                and i.property("text") is not None]

    def total():
        return sum(calls.values())

    out: dict = {"wrapped": len(wrappers), "bindings": bindings, "gc_limit": gc_limit}
    settle(0.8)

    # 1. positive control
    calls.clear()
    iso.setMachAndSolve(2.5); settle()
    out["positive_control_calls"] = total()

    # The file and socket watchers' own positive controls: each must see a read
    # and a connection made on purpose, through the same paths the code would use.
    watch(True)
    (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    try:
        socket.create_connection(("127.0.0.1", 9), timeout=0.2)
    except OSError:
        pass
    out["watch_control"] = {"read_seen": any(p.endswith("README.md") for p in opened),
                            "socket_seen": bool(sockets)}
    opened.clear(); sockets.clear()

    # 2. the DB-3A view sequence
    calls.clear()
    # a fresh controller, built under the instrument: loading and admitting the
    # corpus reads the shipped engine files only, and solves nothing
    from rocketforge.application.analysis.reference_engine_controller import ReferenceEngineController
    fresh = ReferenceEngineController()
    out["construction"] = {"calls": total(), "configurations": fresh.configurationCount,
                           "opened": sorted({p.replace("\\", "/") for p in opened})}
    del fresh
    opened.clear()
    steps: list[tuple[str, int]] = []

    def step(label):
        steps.append((label, total()))

    index = nav.indexOfKey("engines")
    out["nav_index"] = index
    out["nav_evidence"] = nav.indexOfKey("evidence")
    out["reference_family_items"] = [f["groups"][0]["items"] for f in plain(nav.property("families"))
                                     if f["key"] == "reference"][0]
    window.setProperty("currentPageIndex", index); settle(0.8); step("enter page")
    out["initial_selected"] = rex.property("selectedConfigurationId")
    out["first_library_row"] = plain(rex.property("library").rows())[0]["configurationId"]
    lst = named("engineLibraryList")
    out["library_rows"] = lst.property("count") if lst else -1
    out["controller_rows"] = rex.property("visibleCount")
    title = named("engineRecordTitle")
    out["title_matches"] = title is not None and title.property("text") == rex.property("recordTitle") != ""
    step("read library and record")

    search = named("engineSearch")
    search.setProperty("text", "rl10"); settle()
    out["search_rl10"] = [r["configurationId"] for r in plain(rex.property("library").rows())]
    search.setProperty("text", "lm descent"); settle()
    out["search_lm"] = [r["configurationId"] for r in plain(rex.property("library").rows())]
    search.setProperty("text", ""); settle()
    cap, status, cycle = named("engineCapabilityFilter"), named("engineStatusFilter"), named("engineCycleFilter")
    options = plain(rex.property("filterOptions"))
    out["status_enabled_without_capability"] = bool(status.property("enabled"))
    emit(cap, "activated", Q_ARG(int, 4))                              # Topology
    out["status_enabled_with_capability"] = bool(status.property("enabled"))
    emit(status, "activated", Q_ARG(int, 2))                           # Partial
    out["topology_partial"] = [r["configurationId"] for r in plain(rex.property("library").rows())]
    for i in range(1, len(options["status"]) + 1):
        emit(status, "activated", Q_ARG(int, i))
    emit(cap, "activated", Q_ARG(int, 0))
    for i in range(1, len(options["cycle"]) + 1):
        emit(cycle, "activated", Q_ARG(int, i))
    step("search and filters through the QML controls")
    rex.clearFilters(); settle()
    rex.setSearch("no such engine zz"); settle()
    empty = named("engineEmptyState")
    out["no_match_state"] = rex.property("emptyState")
    out["no_match_visible"] = bool(empty and empty.property("visible"))
    out["no_match_selection"] = rex.property("selectedConfigurationId")
    emit(named("engineClearFilters"), "clicked")
    out["after_clear"] = [rex.property("emptyState"), rex.property("selectedConfigurationId"),
                          rex.property("hasActiveFilter"), search.property("text")]
    step("zero match and Clear filters")

    seen: dict = {}
    # every configuration is visited; the representative ones are read in detail
    everything = [r["configurationId"] for r in plain(rex.property("library").rows())]
    out["visited"] = len(everything)
    for cfg in everything:
        rex.selectConfiguration(cfg); settle(0.2)
    for cfg in CONFIGS:
        rex.selectConfiguration(cfg); settle(0.35)
        page_root = [i for i in items() if i.metaObject().className().startswith("ReferenceEnginesPage")][0]
        words = texts(page_root)
        seen[cfg] = {
            "title": rex.property("recordTitle"),
            "graphs": rex.property("graphCount"),
            "nodes": sum(1 for i in items() if i.objectName().startswith("node_")),
            "edges": sum(1 for i in items() if i.objectName().startswith("edgeHandle_")),
            "no_topology_visible": bool(named("engineNoTopology") and named("engineNoTopology").property("visible")),
            "recon_visible": bool(named("topologyReconstructionBanner")
                                  and named("topologyReconstructionBanner").property("visible")),
            "layout_note": any("Connectivity is evidence; position is not" in w for w in words),
            "capabilities": [named("capabilityStatus_" + c).property("text") for c in
                             ("IDENTITY", "ARCHITECTURE", "PERFORMANCE_REFERENCE", "TOPOLOGY",
                              "REGRESSION_CANDIDATE")],
            "words": words,
        }
    step("every representative configuration")

    rex.selectConfiguration("CFG-RS25-BLOCK-II"); settle()
    page_root = [i for i in items() if i.metaObject().className().startswith("ReferenceEnginesPage")][0]
    out["rs25_words"] = texts(page_root)
    pc = [a for a in plain(rex.property("facts").rows()) if "2,870" in a["valueText"] or "1,125" in a["valueText"]]
    out["pc_rows"] = pc
    if pc:
        rex.inspectAssertion(pc[0]["assertionId"]); settle()
    shell.setProperty("inspectorOpen", True); settle(0.4)
    out["pc_inspector"] = [i.property("text") for i in items() if i.objectName() == "engineInspectorValue"]

    rex.selectConfiguration("CFG-F1"); settle()
    rex.inspectCapability("REGRESSION_CANDIDATE"); settle()
    out["capability_inspector_title"] = named("engineInspectorTitle").property("text")
    rex.inspectSource(plain(rex.property("sources").rows())[0]["sourceId"]); settle()
    out["source_inspector"] = [i.property("text") for i in items() if i.objectName() == "engineInspectorValue"]
    rex.inspectGraph(); settle()
    out["graph_inspector"] = [i.property("text") for i in items() if i.objectName() == "engineInspectorValue"]
    node = [i for i in items() if i.objectName().startswith("node_")][0]
    QMetaObject.invokeMethod(node, "forceActiveFocus"); settle()
    rex.inspectNode(node.objectName()[len("node_"):]); settle()
    out["node_kind"] = rex.property("inspectionKind")
    handle = [i for i in items() if i.objectName().startswith("edgeHandle_")][0]
    rex.inspectEdge(handle.objectName()[len("edgeHandle_"):]); settle()
    out["edge_kind"] = rex.property("inspectionKind")
    out["edge_inspector"] = [i.property("text") for i in items() if i.objectName() == "engineInspectorValue"]
    for name in ("topologyZoomIn", "topologyZoomOut", "topologyFit", "topologyReset"):
        emit(named(name), "clicked")
    emit(named("engineInspectRecord"), "clicked")
    out["back_to_record"] = rex.property("inspectionKind") == ""
    step("inspector: capability, assertion, source, graph, node, edge; zoom")

    drawer = named("engineDataDrawer")
    drawer.setProperty("open", True); settle(0.5)
    emit(named("engineAssertionTable"), "rowClicked", Q_ARG(int, 1))
    out["table_row_kind"] = [rex.property("inspectionKind"), rex.property("selectedTableRow")]
    emit(named("engineTableSwitch"), "selected", Q_ARG(int, 1))
    emit(named("engineConnectionTable"), "rowClicked", Q_ARG(int, 2))
    out["connection_row_kind"] = [rex.property("inspectionKind"), rex.property("selectedConnectionRow")]
    drawer.setProperty("open", False); shell.setProperty("inspectorOpen", False); settle()
    step("data drawer: both tables")
    library = named("engineLibraryDrawer")
    QMetaObject.invokeMethod(library, "setOpenByUser", Q_ARG("QVariant", False)); settle()
    QMetaObject.invokeMethod(library, "setOpenByUser", Q_ARG("QVariant", True)); settle()
    step("library drawer")
    for theme in ("light", "dark"):
        window.setProperty("themeMode", theme); settle(0.35)
    for w, h in ((1366, 768), (2560, 1440), (1920, 1080)):
        window.setProperty("width", w); window.setProperty("height", h); settle(0.35)
    step("theme and size")

    shell.setProperty("inspectorOpen", True); settle(0.4)
    page_root = [i for i in items() if i.metaObject().className().startswith("ReferenceEnginesPage")][0]
    inspector = named("engineInspector")
    page_texts = texts(page_root) + (texts(inspector) if inspector else [])
    out["page_text_count"] = len(page_texts)
    buttons = [str(i.property("text")) for r in [page_root] + ([inspector] if inspector else [])
               for i in [r] + items(r) if i.metaObject().className().startswith(("RFButton", "RFToolButton"))]
    out["buttons"] = sorted(set(buttons))
    out["forbidden_actions"] = sorted({b for b in buttons for w in FORBIDDEN_ACTIONS
                                       if b == w or b.startswith(w + " ")})
    out["forbidden_claims"] = sorted({w for t in page_texts for w in FORBIDDEN_CLAIMS if w in t})
    shell.setProperty("inspectorOpen", False); settle(0.3)
    counts = []
    for _ in range(3):
        window.setProperty("currentPageIndex", nav.indexOfKey("home")); settle(0.45)
        window.setProperty("currentPageIndex", index); settle(0.6)
        counts.append(sum(1 for i in items() if i.objectName() == "engineRecordTitle"))
    out["page_instances"] = counts
    out["selection_after_reentry"] = rex.property("selectedConfigurationId")
    step("leave and return x3")
    out["view_calls"] = total()
    out["view_call_names"] = sorted(calls)
    out["steps"] = steps
    watch(False)
    out["opened"] = sorted({p.replace("\\", "/") for p in opened})
    # matched on the path inside the repository (the checkout's own folder name is not evidence)
    root = PROJECT_ROOT.as_posix().lower() + "/"
    research = ("docs/", "research", "db05", "manifest", "renders", "acceptance/")
    out["opened_research"] = [p for p in out["opened"] + out["construction"]["opened"]
                              if any(r in p.lower().removeprefix(root) for r in research)
                              or p.lower().endswith((".pdf", ".png", ".jpg"))]
    out["sockets"] = sockets
    out["seen"] = seen

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
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=400)
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


def test_browsing_reference_engines_solves_and_probes_nothing(run):
    assert run["view_calls"] == 0, (run["view_call_names"], run["steps"])
    assert [label for label, _ in run["steps"]] == [
        "enter page", "read library and record", "search and filters through the QML controls",
        "zero match and Clear filters", "every representative configuration",
        "inspector: capability, assertion, source, graph, node, edge; zoom",
        "data drawer: both tables", "library drawer", "theme and size", "leave and return x3"]


def test_nothing_is_read_from_research_or_the_network_at_runtime(run):
    # the watchers are live: each saw its own deliberate read and connection
    assert run["watch_control"] == {"read_seen": True, "socket_seen": True}
    assert run["opened_research"] == [], run["opened_research"]
    assert run["sockets"] == []
    # building the controller reads only the shipped engine corpus, and solves nothing
    assert run["construction"]["calls"] == 0 and run["construction"]["configurations"] == 16
    assert run["construction"]["opened"]
    assert all("rocketforge/data/evidence/engines" in p for p in run["construction"]["opened"]), \
        run["construction"]["opened"]
    # browsing reads no file at all
    assert run["opened"] == [], run["opened"]
    assert run["visited"] == 16


def test_the_route_sits_in_the_reference_family_and_renders_the_controller(run):
    assert run["nav_index"] >= 0
    assert run["reference_family_items"] == [11, run["nav_evidence"], run["nav_index"]]
    assert run["title_matches"]
    assert run["initial_selected"] == run["first_library_row"]      # deterministic
    assert run["library_rows"] == run["controller_rows"] == 16


def test_search_and_filters_come_from_the_corpus(run):
    assert set(run["search_rl10"]) == {"CFG-RL10A-3-3A", "CFG-RL10B-2-DIV"}
    assert run["search_lm"] == ["CFG-LMDE-FINAL"]
    assert not run["status_enabled_without_capability"] and run["status_enabled_with_capability"]
    assert run["topology_partial"] == ["CFG-RD-170"]


def test_zero_match_is_stated_and_recoverable(run):
    assert run["no_match_state"] == "no-match" and run["no_match_visible"]
    assert run["no_match_selection"] == ""
    assert run["after_clear"][0] == "" and run["after_clear"][1] and not run["after_clear"][2]
    assert run["after_clear"][3] == ""


def test_topology_honesty_on_the_real_records(run):
    seen = run["seen"]
    rd = seen["CFG-RD-170"]
    assert rd["recon_visible"] and rd["layout_note"] and rd["nodes"] > 0 and rd["edges"] > 0
    for cfg in ("CFG-F1", "CFG-J2-230K", "CFG-LMDE-FINAL", "CFG-LR87-AJ-11-T3E", "CFG-H1-188K-SA10"):
        assert seen[cfg]["graphs"] == 1 and not seen[cfg]["recon_visible"], cfg
        assert seen[cfg]["nodes"] > 0 and seen[cfg]["edges"] > 0 and seen[cfg]["layout_note"], cfg
    for cfg in ("CFG-J2S", "CFG-IPD", "CFG-RS-68A", "CFG-RL10B-2-DIV"):
        assert seen[cfg]["graphs"] == 0 and seen[cfg]["no_topology_visible"], cfg
        assert seen[cfg]["nodes"] == 0, cfg


def test_capabilities_are_independent_words(run):
    words = {"Supported", "Partial", "Not supported"}
    for cfg, data in run["seen"].items():
        assert len(data["capabilities"]) == 5 and set(data["capabilities"]) <= words, cfg
    assert run["seen"]["CFG-RD-170"]["capabilities"][3] == "Partial"
    assert run["seen"]["CFG-J2-230K"]["capabilities"][4] == "Supported"
    assert any("eligibility only" in w for w in run["seen"]["CFG-J2-230K"]["words"])


def test_an_unknown_condition_stays_unknown(run):
    assert any("Pressure station: Unknown" in w for w in run["rs25_words"]), run["pc_rows"]
    assert "Unknown (not stated by the source)" in run["pc_inspector"]


def test_the_inspector_reads_every_subject(run):
    assert run["capability_inspector_title"] == "Regression candidate"
    assert any("not a legal determination" in v for v in run["source_inspector"])
    assert any("position" in v and "not" in v for v in run["graph_inspector"])
    assert run["node_kind"] == "node" and run["edge_kind"] == "edge" and run["edge_inspector"]
    assert run["back_to_record"]
    assert run["table_row_kind"] == ["assertion", 1]
    assert run["connection_row_kind"] == ["edge", 2]


def test_no_warning_no_action_and_no_accumulating_pages(run):
    assert run["warnings"] == [], run["warnings"]
    assert run["page_text_count"] > 60
    assert run["forbidden_actions"] == [], run["buttons"]
    assert run["forbidden_claims"] == []
    assert run["page_instances"] == [1, 1, 1]
    assert run["selection_after_reentry"]
    assert run["gc_limit"] == "0"


if __name__ == "__main__":
    print("RESULT " + json.dumps(_drive(), default=str), flush=True)
