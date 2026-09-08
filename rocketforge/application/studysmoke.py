"""A non-interactive tour of the Trade Study workspace, runnable frozen.

Fourth of the diagnostics, and it exists for the reason the other three do:
claims about the *packaged* application cannot be checked by inspecting
``dist/``. It answers the questions a screenshot cannot:

* does the packaged interface run a real study against the bundled provider?
* **does the packaged dependency planner still reuse chamber solves?**
* does changing an objective, a constraint or a weight re-solve anything?

The middle one is the blocking measurement. A frozen build that solved
chemistry once per design point instead of once per chemistry state would look
identical in every capture, and only a call count catches it.

Invoked as::

    RocketForge.exe --selftest-trade-study <output directory>

It loads the real QML, drives the real controllers through the same slots the
interface's own controls call, writes one JSON report and a set of PNG
captures, and exits. **No synthetic desktop input**, so it cannot type into
whatever window happens to be in front, and it runs under the offscreen
platform plugin.
"""

from __future__ import annotations

import json
import sys
import time

__all__ = ["STUDY_SMOKE_FLAG", "run_study_smoke", "RESOLUTIONS"]

#: The argument that triggers the trade-study tour.
STUDY_SMOKE_FLAG = "--selftest-trade-study"

#: The window sizes the visual gate is judged at, unchanged since Phase 4G.
RESOLUTIONS = ((2560, 1440), (1920, 1080), (1366, 768))

SETUP, RESULTS, PARETO, COMPARE = 0, 1, 2, 3



def _complete_deletions() -> None:
    # DeferredDelete is not dispatched by processEvents(); it is
    # delivered when the loop unwinds to the exec() that posted it. A
    # tour driven only by processEvents() therefore never completes a
    # single deleteLater(), so objects Qt has correctly destroyed stay
    # committed and the tour's memory profile is not the application's.
    # See docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md.
    from PySide6.QtCore import QCoreApplication, QEvent

    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def run_study_smoke(argv, configure, build_engine, ui_dir) -> int:
    """Load the interface, run studies, and report what they cost.

    Returns 0 when the tour completed with no Qt warning and the solve counts
    were correct, 2 when it completed with warnings, and 1 when it could not
    run or a solve count was wrong.
    """
    from pathlib import Path

    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    ui_dir = Path(ui_dir)
    outdir = Path(argv[0]) if argv else Path.cwd() / "study_smoke"
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

    from rocketforge.application.analysis.thermochemistry_controller import (
        ThermochemistryController,
    )
    from rocketforge.application.analysis.trade_study_controller import (
        TradeStudyController,
    )

    studies = app.findChildren(TradeStudyController)
    chemistry = app.findChildren(ThermochemistryController)
    if not studies or not chemistry:
        _write(outdir, {"status": "controller_missing", "messages": messages})
        return 1
    controller = studies[0]
    thermo = chemistry[0]

    probe_component = QQmlComponent(engine)
    probe_component.setData(
        b'import QtQuick\nimport "data"\n'
        b'QtObject { property int idx: Navigation.indexOfKey("tradestudy") }',
        QUrl.fromLocalFile(str(ui_dir / "_probe.qml")))
    probe = probe_component.create()
    if probe is None or int(probe.property("idx")) < 0:
        _write(outdir, {"status": "navigation_entry_missing",
                        "messages": messages})
        return 1
    page_index = int(probe.property("idx"))
    window.setProperty("currentPageIndex", page_index)

    # ---- the provider-call counter -------------------------------------
    #
    # Wrapped around the gateway's own provider, so what is counted is a real
    # solve reaching the bundled library rather than a service call that might
    # have been served from somewhere else.
    counter = {"calls": 0}
    installed = False
    try:
        from rocketforge.application.analysis import thermochemistry_provider as gw

        if gw.availability().usable:
            provider = gw.chamber_provider()
            original = provider.solve_chamber

            def counting_solve(request, _original=original):
                counter["calls"] += 1
                return _original(request)

            provider.solve_chamber = counting_solve  # type: ignore[method-assign]
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

    def run_and_wait(timeout: float = 240.0) -> None:
        """Drive the chunked runner from here, exactly as the event loop would."""
        controller.runStudy()
        deadline = time.perf_counter() + timeout
        while controller.busy and time.perf_counter() < deadline:
            app.processEvents()
            _complete_deletions()
            time.sleep(0.005)
        settle()

    captures: list[dict] = []

    def capture(name: str, note: str) -> None:
        settle()
        image = window.grabWindow()
        path = outdir / f"{name}.png"
        image.save(str(path))
        captures.append({"name": name, "file": path.name, "note": note,
                         "width": image.width(), "height": image.height(),
                         "providerCalls": counter["calls"],
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

    # ---- the empty state ------------------------------------------------
    for width, height in RESOLUTIONS:
        window.setProperty("width", width)
        window.setProperty("height", height)
        show(SETUP)
        capture(f"setup_{width}x{height}",
                "study definition before anything has been run")

    if not thermo.providerAvailable:
        show(RESULTS)
        capture("no_provider_1920x1080",
                "no chemistry provider installed; the workspace states it "
                "rather than substituting a gas")
        report["captures"] = captures
        report["messages"] = messages
        report["note"] = ("no chemistry provider installed, so no study could "
                          "be run; the workspace was toured in its refusing "
                          "state only")
        _write(outdir, report)
        return 0 if not _warnings(messages) else 2

    # ---- the canonical grid ---------------------------------------------
    controller.setVariableEnabled("oxidiser_fuel_ratio", True)
    controller.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 41)
    controller.setVariableEnabled("area_ratio", True)
    controller.setVariableRange("area_ratio", 10.0, 80.0, 4)
    controller.setVariableEnabled("chamber_pressure", False)
    controller.setVariableEnabled("ambient_pressure", False)
    controller.setVariableEnabled("throat_area", False)
    settle()

    preview = {
        "points": int(controller.pointCount),
        "chemistrySolves": int(controller.chemistrySolveCount),
        "performanceSolves": int(controller.performanceSolveCount),
        "note": controller.workloadNote,
    }

    before = counter["calls"]
    run_and_wait()
    canonical_calls = counter["calls"] - before

    for width, height in RESOLUTIONS:
        tag = f"{width}x{height}"
        window.setProperty("width", width)
        window.setProperty("height", height)
        show(RESULTS)
        capture(f"results_{tag}",
                "164 design points from 41 chamber solves; failed, infeasible "
                "and successful rows all present")

    # ---- a second objective, so a front exists ---------------------------
    controller.addObjective("chamber_temperature", "minimize")
    settle()
    after_objective = counter["calls"]

    for width, height in RESOLUTIONS:
        tag = f"{width}x{height}"
        window.setProperty("width", width)
        window.setProperty("height", height)
        show(PARETO)
        capture(f"pareto_{tag}",
                "two objectives; efficient, dominated and excluded points are "
                "distinguished by marker shape as well as colour")

    # ---- a constraint, then a score --------------------------------------
    controller.addConstraint("chamber_temperature", "<=", 3500.0)
    settle()
    after_constraint = counter["calls"]
    show(RESULTS)
    capture("results_constrained_1920x1080",
            "a hard constraint: infeasible points keep every number they "
            "produced and are excluded from the front")

    controller.setProperty("scoringEnabled", True)
    settle()
    after_score = counter["calls"]
    show(PARETO)
    capture("pareto_scored_1920x1080",
            "scoring enabled; the front is unchanged, because a weight cannot "
            "move a dominance verdict")
    front_with_score = list(controller.property("selectedIndices") or [])

    # ---- compare ---------------------------------------------------------
    for row in controller.bestRows:
        controller.toggleSelection(int(row["index"]))
    settle()
    show(COMPARE)
    capture("compare_1920x1080",
            "up to four designs side by side, raw physics above the score")

    # ---- light theme ------------------------------------------------------
    window.setProperty("themeMode", "light")
    show(SETUP)
    capture("setup_light_1920x1080", "light theme")
    show(RESULTS)
    capture("results_light_1920x1080", "light theme")
    window.setProperty("themeMode", "dark")

    # ---- the blocking measurement ----------------------------------------
    report["preview"] = preview
    report["solveCounts"] = {
        "designPoints": preview["points"],
        "expectedChemistrySolves": preview["chemistrySolves"],
        "actualChemistrySolves": canonical_calls,
        "addedByObjective": after_objective - canonical_calls - before,
        "addedByConstraint": after_constraint - after_objective,
        "addedByScore": after_score - after_constraint,
    }
    counts = report["solveCounts"]
    reuse_ok = counts["actualChemistrySolves"] == counts["expectedChemistrySolves"]
    decision_free = (counts["addedByObjective"] == 0
                     and counts["addedByConstraint"] == 0
                     and counts["addedByScore"] == 0)
    counts["verdict"] = (
        "PASS — solve reuse correct and the decision layer re-solved nothing"
        if reuse_ok and decision_free else
        "FAIL — " + ("chemistry solve count wrong" if not reuse_ok
                     else "a decision edit re-solved physics"))

    report["captures"] = captures
    report["messages"] = messages
    _write(outdir, report)
    if not (reuse_ok and decision_free):
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
        "baselineAvailable": bool(controller.baselineAvailable),
        "baselineHeadline": controller.baselineHeadline,
        "pointCount": int(controller.pointCount),
        "chemistrySolveCount": int(controller.chemistrySolveCount),
        "performanceSolveCount": int(controller.performanceSolveCount),
        "workloadNote": controller.workloadNote,
        "definitionValid": bool(controller.definitionValid),
        "definitionMessage": controller.definitionMessage,
        "definitionFingerprint": controller.definitionFingerprint,
        "variableRows": [dict(row) for row in controller.variableRows],
        "objectiveRows": [dict(row) for row in controller.objectiveRows],
        "constraintRows": [dict(row) for row in controller.constraintRows],
        "scoringEnabled": bool(controller.scoringEnabled),
        "weightRows": [dict(row) for row in controller.weightRows],
        "hasResult": bool(controller.hasResult),
        "resultComplete": bool(controller.resultComplete),
        "studyStatus": controller.studyStatus,
        "summaryRows": [dict(row) for row in controller.summaryRows],
        "solveReuseNote": controller.solveReuseNote,
        "visibleRowCount": int(controller.visibleRowCount),
        "resultColumns": [dict(column) for column in controller.resultColumns],
        "diagnosticRows": [dict(row) for row in controller.diagnosticRows],
        "provenanceRows": [dict(row) for row in controller.provenanceRows],
        "paretoAvailable": bool(controller.paretoAvailable),
        "paretoNote": controller.paretoNote,
        "paretoSeries": [
            {"key": series["key"], "label": series["label"],
             "count": len(series["points"]),
             "points": [dict(point) for point in series["points"]]}
            for series in controller.paretoSeries],
        "bestRows": [dict(row) for row in controller.bestRows],
        "compareColumns": [dict(column) for column in controller.compareColumns],
        "selectedIndices": list(controller.selectedIndices),
    }


def _write(outdir, report) -> None:
    label = "frozen" if getattr(sys, "frozen", False) else "source"
    path = outdir / f"study_smoke_{label}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    warnings = _warnings(report.get("messages", []))
    counts = report.get("solveCounts", {})
    print(f"[study-smoke] {label}: {len(report.get('captures', []))} captures, "
          f"{len(report.get('messages', []))} Qt messages "
          f"({len(warnings)} warning or worse) -> {path}")
    if counts:
        print(f"[study-smoke] {counts['designPoints']} design points, "
              f"{counts['actualChemistrySolves']} chamber solves "
              f"(expected {counts['expectedChemistrySolves']}); "
              f"decision edits added "
              f"{counts['addedByObjective'] + counts['addedByConstraint'] + counts['addedByScore']} "
              f"solves — {counts['verdict']}")
    for entry in warnings[:20]:
        print(f"  [{entry['kind']}] {entry['message']}")
