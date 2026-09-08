"""A non-interactive tour of the Rocket Performance workspace, runnable frozen.

Third of the diagnostics, and it exists for the same reason as the other two.
``selftest`` answers "can the packaged provider solve?"; ``uismoke`` answers
"does the packaged chemistry interface show the same numbers as the source
build?"; this answers the same question for the performance workspace, plus one
the others cannot ask:

**does changing a nozzle input in the packaged interface re-solve chemistry?**

The tour counts provider calls across the whole run. A frozen build that
quietly re-solved on every slider move would still look correct in a
screenshot, and the count is the only thing that catches it.

Invoked as::

    RocketForge.exe --selftest-rocket-performance <output directory>

It loads the real QML, drives the real controllers through the same slots the
interface's own controls call, writes one JSON report and a set of PNG
captures, and exits. **No synthetic desktop input**: nothing here can type into
whatever window happens to be in front, and it works under the offscreen
platform plugin.
"""

from __future__ import annotations

import json
import sys
import time

__all__ = ["PERF_SMOKE_FLAG", "run_performance_smoke", "RESOLUTIONS"]

#: The argument that triggers the performance tour.
PERF_SMOKE_FLAG = "--selftest-rocket-performance"

#: The window sizes the visual gate is judged at, unchanged since Phase 4G.
RESOLUTIONS = ((2560, 1440), (1920, 1080), (1366, 768))

PERFORMANCE, MODEL, ORACLE = 0, 1, 2



def _complete_deletions() -> None:
    # DeferredDelete is not dispatched by processEvents(); it is
    # delivered when the loop unwinds to the exec() that posted it. A
    # tour driven only by processEvents() therefore never completes a
    # single deleteLater(), so objects Qt has correctly destroyed stay
    # committed and the tour's memory profile is not the application's.
    # See docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md.
    from PySide6.QtCore import QCoreApplication, QEvent

    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def run_performance_smoke(argv, configure, build_engine, ui_dir) -> int:
    """Load the interface, tour the workspace, and report what it held.

    The bootstrap is handed in rather than imported, for the reason
    ``uismoke`` gives: a frozen build runs ``main.py`` as ``__main__``, so
    importing it there would load a second copy.

    Returns 0 when the tour completed with no Qt warning, 2 when it completed
    with warnings, and 1 when it could not run at all.
    """
    from pathlib import Path

    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    ui_dir = Path(ui_dir)
    outdir = Path(argv[0]) if argv else Path.cwd() / "perf_smoke"
    outdir.mkdir(parents=True, exist_ok=True)

    messages: list[dict] = []
    kinds = {
        QtMsgType.QtDebugMsg: "debug",
        QtMsgType.QtInfoMsg: "info",
        QtMsgType.QtWarningMsg: "warning",
        QtMsgType.QtCriticalMsg: "critical",
        QtMsgType.QtFatalMsg: "fatal",
    }

    def handler(kind, context, message):
        messages.append({"kind": kinds.get(kind, str(kind)), "message": message})

    qInstallMessageHandler(handler)

    configure()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _environment = build_engine(app)
    engine.load(QUrl.fromLocalFile(str(ui_dir / "Main.qml")))
    roots = engine.rootObjects()
    if not roots:
        _write(outdir, {"status": "qml_load_failed", "messages": messages})
        return 1
    window = roots[0]

    from rocketforge.application.analysis.performance_controller import (
        RocketPerformanceController,
    )
    from rocketforge.application.analysis.thermochemistry_controller import (
        ThermochemistryController,
    )

    performance = app.findChildren(RocketPerformanceController)
    chemistry = app.findChildren(ThermochemistryController)
    if not performance or not chemistry:
        _write(outdir, {"status": "controller_missing", "messages": messages})
        return 1
    controller = performance[0]
    thermo = chemistry[0]

    # Ask the navigation model where the workspace is, rather than assuming an
    # index that a later page would silently shift.
    probe_component = QQmlComponent(engine)
    probe_component.setData(
        b'import QtQuick\nimport "data"\n'
        b'QtObject { property int idx: Navigation.indexOfKey("performance") }',
        QUrl.fromLocalFile(str(ui_dir / "_probe.qml")))
    probe = probe_component.create()
    if probe is None:
        _write(outdir, {"status": "navigation_probe_failed",
                        "detail": probe_component.errorString(),
                        "messages": messages})
        return 1
    page_index = int(probe.property("idx"))
    if page_index < 0:
        _write(outdir, {"status": "navigation_entry_missing",
                        "messages": messages})
        return 1
    window.setProperty("currentPageIndex", page_index)

    # ---- the provider-call counter -------------------------------------
    #
    # Wrapped around the gateway's own provider rather than around the service,
    # so what is counted is a real solve reaching a real library. A frozen
    # build that re-solved chemistry on a nozzle change would be caught here
    # and nowhere else in this tour.
    solve_counter = {"calls": 0}
    installed = False
    try:
        from rocketforge.application.analysis import thermochemistry_provider as gw

        if gw.availability().usable:
            provider = gw.chamber_provider()
            original = provider.solve_chamber

            def counting_solve(request, _original=original):
                solve_counter["calls"] += 1
                return _original(request)

            provider.solve_chamber = counting_solve      # type: ignore[method-assign]
            installed = True
    except Exception as error:  # noqa: BLE001 - the tour reports, never crashes
        messages.append({"kind": "info",
                         "message": f"call counter not installed: {error}"})

    def settle(rounds: int = 6, pause: float = 0.05) -> None:
        for _ in range(rounds):
            app.processEvents()
            _complete_deletions()
            time.sleep(pause)
            app.processEvents()
            _complete_deletions()

    captures: list[dict] = []

    def capture(name: str, note: str) -> None:
        settle()
        image = window.grabWindow()
        path = outdir / f"{name}.png"
        image.save(str(path))
        captures.append({"name": name, "file": path.name, "note": note,
                         "width": image.width(), "height": image.height(),
                         "solveCalls": solve_counter["calls"],
                         "state": _snapshot(controller)})

    def show(section: int) -> None:
        controller.showTab(section)
        settle()

    settle()
    report: dict = {
        "status": "ok",
        "frozen": bool(getattr(sys, "frozen", False)),
        "meipass": str(getattr(sys, "_MEIPASS", "") or ""),
        "python": sys.version.split()[0],
        "pageIndex": page_index,
        "providerAvailable": bool(thermo.providerAvailable),
        "callCounterInstalled": installed,
    }

    # ---- with no chamber state at all ----------------------------------
    for width, height in RESOLUTIONS:
        window.setProperty("width", width)
        window.setProperty("height", height)
        show(PERFORMANCE)
        capture(f"no_chamber_{width}x{height}",
                "no chamber equilibrium solved yet: the workspace refuses "
                "rather than estimating one")

    if not thermo.providerAvailable:
        # A chamber state is what this workspace needs, and on a build with no
        # chemistry library there is no way to obtain one. That is a supported
        # configuration, not an error, and the tour records it honestly rather
        # than reporting a performance figure computed from nothing.
        report["captures"] = captures
        report["messages"] = messages
        report["note"] = ("no chemistry provider installed, so no chamber "
                          "state could be produced; the performance workspace "
                          "was toured in its refusing state only")
        _write(outdir, report)
        return 0 if not _warnings(messages) else 2

    thermo.resetInputs()
    thermo.calculate()
    settle()
    report["chamberHeadline"] = controller.chamberHeadline
    baseline_after_chamber = solve_counter["calls"]

    for width, height in RESOLUTIONS:
        tag = f"{width}x{height}"
        window.setProperty("width", width)
        window.setProperty("height", height)

        controller.resetInputs()
        show(PERFORMANCE)
        capture(f"ready_{tag}",
                "a chamber state is available; nothing computed yet")

        controller.calculate()
        capture(f"vacuum_{tag}",
                "Ae/At 40 in vacuum, frozen gamma basis, no engine size: "
                "thrust is withheld rather than defaulted")

        controller.ambientMode = "sea_level"
        controller.calculate()
        capture(f"sea_level_{tag}",
                "the same nozzle at sea level: overexpanded, and the pressure "
                "term is negative rather than clamped")

        controller.scaleMode = "throat_area"
        controller.scaleValue = 0.01
        controller.calculate()
        capture(f"scaled_{tag}",
                "sized by a 0.01 m2 throat: the engine group appears")

        controller.ambientMode = "custom"
        controller.ambientPressure = 5.0e6
        controller.calculate()
        capture(f"refused_{tag}",
                "ambient at 5 MPa drives a shock inside the nozzle: outside "
                "the ideal model, refused by name")

        controller.resetInputs()
        controller.calculate()
        show(MODEL)
        capture(f"model_{tag}",
                "assumptions, gas reduction, internal identities, provenance")

        show(ORACLE)
        capture(f"oracle_before_{tag}",
                "the provider has not been asked; this panel runs only on "
                "request")
        controller.runOracle()
        capture(f"oracle_{tag}",
                "the provider's own c*, Cf and Isp, compared at matched "
                "reference conditions")

    # ---- the blocking measurement --------------------------------------
    #
    # Every nozzle input moved, repeatedly, through the same slots the controls
    # call. The count must not move.
    show(PERFORMANCE)
    controller.resetInputs()
    controller.calculate()
    before_inputs = solve_counter["calls"]
    for ratio in (5.0, 15.0, 40.0, 90.0):
        for ambient in ("vacuum", "sea_level"):
            controller.areaRatio = ratio
            controller.ambientMode = ambient
            controller.calculate()
    controller.scaleMode = "mass_flow"
    controller.scaleValue = 25.0
    controller.calculate()
    controller.gammaBasis = "equilibrium"
    controller.calculate()
    controller.gammaBasis = "frozen"
    controller.calculate()
    after_inputs = solve_counter["calls"]

    report["chamberSolves"] = {
        "afterChamberSolve": baseline_after_chamber,
        "beforeInputSweep": before_inputs,
        "afterInputSweep": after_inputs,
        "causedByInputChanges": after_inputs - before_inputs,
        "verdict": ("PASS — no chemistry re-solve"
                    if after_inputs == before_inputs
                    else "FAIL — a nozzle input re-solved chemistry"),
    }

    controller.resetInputs()
    controller.calculate()
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("themeMode", "light")
    show(PERFORMANCE)
    capture("performance_light_1920x1080", "light theme")
    show(MODEL)
    capture("model_light_1920x1080", "light theme")
    window.setProperty("themeMode", "dark")

    report["captures"] = captures
    report["messages"] = messages
    _write(outdir, report)
    if after_inputs != before_inputs:
        return 1
    return 0 if not _warnings(messages) else 2


def _warnings(messages: list[dict]) -> list[dict]:
    return [entry for entry in messages
            if entry["kind"] in ("warning", "critical", "fatal")]


def _snapshot(controller) -> dict:
    """Exactly what the controller held at the moment of a capture.

    This is what makes source and frozen comparable field by field: a
    screenshot shows that something was drawn, and this says what.
    """
    return {
        "hasChamber": bool(controller.hasChamber),
        "chamberHeadline": controller.chamberHeadline,
        "chamberRows": [dict(row) for row in controller.chamberRows],
        "chamberSuperseded": bool(controller.chamberSuperseded),
        "statusKind": controller.statusKind,
        "statusLabel": controller.statusLabel,
        "statusTone": controller.statusTone,
        "message": controller.message,
        "resultHeadline": controller.resultHeadline,
        "resultStale": bool(controller.resultStale),
        "caseHeadline": controller.caseHeadline,
        "scaled": bool(controller.scaled),
        "unscaledNote": controller.unscaledNote,
        "warningCount": int(controller.warningCount),
        "identitiesPassed": bool(controller.identitiesPassed),
        "identitySummary": controller.identitySummary,
        "identityRows": [dict(row) for row in controller.identityRows],
        "resultGroups": [{"title": group["title"],
                          "rows": [{"key": row["key"], "value": row["value"],
                                    "unit": row["unit"],
                                    "qualifier": row["qualifier"]}
                                   for row in group["rows"]]}
                         for group in controller.resultGroups],
        "reductionRows": [dict(row) for row in controller.reductionRows],
        "assumptions": list(controller.assumptions),
        "diagnostics": [dict(row) for row in controller.diagnostics],
        "provenanceRows": [dict(row) for row in controller.provenanceRows],
        "oracleStatus": controller.oracleStatus,
        "oracleMode": controller.oracleMode,
        "oracleRows": [dict(row) for row in controller.oracleRows],
        "oracleComparisonRows": [dict(row)
                                 for row in controller.oracleComparisonRows],
        "oracleStale": bool(controller.oracleStale),
    }


def _write(outdir, report) -> None:
    label = "frozen" if getattr(sys, "frozen", False) else "source"
    path = outdir / f"perf_smoke_{label}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    warnings = _warnings(report.get("messages", []))
    solves = report.get("chamberSolves", {})
    print(f"[perf-smoke] {label}: {len(report.get('captures', []))} captures, "
          f"{len(report.get('messages', []))} Qt messages "
          f"({len(warnings)} warning or worse) -> {path}")
    if solves:
        print(f"[perf-smoke] chamber solves caused by nozzle input changes: "
              f"{solves['causedByInputChanges']} — {solves['verdict']}")
    for entry in warnings[:20]:
        print(f"  [{entry['kind']}] {entry['message']}")
