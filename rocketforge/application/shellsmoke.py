"""Render every accepted workspace, at every supported size, in both themes.

The three existing tours each drive one workspace deeply. This one goes wide:
it visits every entry in the navigation model plus the Engine Design mode,
captures each, and reports the Qt messages. Its job is to catch the thing a
deep tour cannot -- a page that broke because something *else* changed.

Because it walks the navigation model rather than a hand-written list, a page
added later is covered automatically, and a page removed is noticed.

It also exercises a several-thousand-point trade study, which is where a table
model that retained a delegate per row would show.

**No synthetic desktop input.** Navigation goes through the same property the
shell's own side-nav sets.
"""

from __future__ import annotations

import json
import sys
import time

__all__ = ["SHELL_SMOKE_FLAG", "run_shell_smoke", "RESOLUTIONS"]

SHELL_SMOKE_FLAG = "--selftest-workspaces"

RESOLUTIONS = ((2560, 1440), (1920, 1080), (1366, 768))



def _complete_deletions() -> None:
    # DeferredDelete is not dispatched by processEvents(); it is
    # delivered when the loop unwinds to the exec() that posted it. A
    # tour driven only by processEvents() therefore never completes a
    # single deleteLater(), so objects Qt has correctly destroyed stay
    # committed and the tour's memory profile is not the application's.
    # See docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md.
    from PySide6.QtCore import QCoreApplication, QEvent

    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def run_shell_smoke(argv, configure, build_engine, ui_dir) -> int:
    """Visit every workspace and report. Returns 0 clean, 2 with warnings."""
    from pathlib import Path

    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    ui_dir = Path(ui_dir)
    outdir = Path(argv[0]) if argv else Path.cwd() / "shell_smoke"
    outdir.mkdir(parents=True, exist_ok=True)

    messages: list[dict] = []
    kinds = {QtMsgType.QtDebugMsg: "debug", QtMsgType.QtInfoMsg: "info",
             QtMsgType.QtWarningMsg: "warning",
             QtMsgType.QtCriticalMsg: "critical",
             QtMsgType.QtFatalMsg: "fatal"}

    def handler(kind, context, message):
        messages.append({"kind": kinds.get(kind, str(kind)),
                         "message": message})

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

    # Read the navigation model itself, so this cannot drift from the product.
    probe_component = QQmlComponent(engine)
    probe_component.setData(
        b'import QtQuick\nimport "data"\n'
        b'QtObject {\n'
        b'  property var keys: Navigation.items.map(function (i) { return i.key })\n'
        b'  property var labels: Navigation.items.map(function (i) { return i.label })\n'
        b'}',
        QUrl.fromLocalFile(str(ui_dir / "_probe.qml")))
    probe = probe_component.create()
    if probe is None:
        _write(outdir, {"status": "navigation_probe_failed",
                        "detail": probe_component.errorString(),
                        "messages": messages})
        return 1
    # A QML array arrives as a QJSValue; toVariant() gives the Python list.
    def read_list(name: str) -> list:
        value = probe.property(name)
        converted = value.toVariant() if hasattr(value, "toVariant") else value
        return list(converted or [])

    keys = read_list("keys")
    labels = read_list("labels")
    if not keys:
        _write(outdir, {"status": "navigation_model_empty",
                        "messages": messages})
        return 1

    def settle(rounds: int = 4, pause: float = 0.04) -> None:
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
                         "messages_so_far": len(messages)})

    report: dict = {
        "status": "ok",
        "frozen": bool(getattr(sys, "frozen", False)),
        "python": sys.version.split()[0],
        "navigation_keys": keys,
        "navigation_labels": labels,
        "workspace_count": len(keys),
    }

    # ---- populate the pages that render nothing until they are solved ---
    #
    # Added because two pages shipped bindings to a singleton that does not
    # exist and nothing noticed: their delegates only exist once there is a
    # result, and a tour that visits an empty page evaluates none of them. A
    # visual gate that cannot see the rows is not a visual gate.
    populated: list[str] = []
    for singleton, label in (("FluidProperties", "Fluid Properties"),
                             ("Line", "Line")):
        solver = QQmlComponent(engine)
        source = (f"import QtQuick\nimport RocketForge 1.0\n"
                  f"QtObject {{ Component.onCompleted: "
                  f"{singleton}.calculate() }}")
        solver.setData(source.encode("utf-8"),
                       QUrl.fromLocalFile(str(ui_dir / "_solve.qml")))
        instance = solver.create()
        if instance is not None:
            populated.append(label)
        else:
            messages.append({"kind": "warning",
                             "message": f"could not populate {label}: "
                                        f"{solver.errorString()}"})
    report_populated = populated

    # ---- every workspace, at every resolution -------------------------
    per_page: list[dict] = []
    for width, height in RESOLUTIONS:
        window.setProperty("width", width)
        window.setProperty("height", height)
        window.setProperty("appMode", "analysis")
        for index, key in enumerate(keys):
            before = len(messages)
            window.setProperty("currentPageIndex", index)
            capture(f"{key}_{width}x{height}", f"{labels[index]} workspace")
            per_page.append({"key": key, "label": labels[index],
                             "resolution": f"{width}x{height}",
                             "new_messages": len(messages) - before})

    # ---- engine design mode -------------------------------------------
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    before = len(messages)
    window.setProperty("appMode", "engine")
    capture("engine_design_1920x1080", "Engine Design workspace")
    per_page.append({"key": "engine_design", "label": "Engine Design",
                     "resolution": "1920x1080",
                     "new_messages": len(messages) - before})
    window.setProperty("appMode", "analysis")

    # ---- both themes ---------------------------------------------------
    for theme in ("light", "dark"):
        window.setProperty("themeMode", theme)
        for key in ("isentropic", "thermochem", "performance", "tradestudy"):
            if key in keys:
                window.setProperty("currentPageIndex", keys.index(key))
                capture(f"{key}_{theme}_1920x1080", f"{theme} theme")
    window.setProperty("themeMode", "dark")

    report["per_page"] = per_page
    report["pages_with_messages"] = [p for p in per_page
                                     if p["new_messages"] > 0]

    # ---- a large trade study through the real controller ---------------
    large = _large_study(app, settle, window, keys, capture)
    if large is not None:
        report["large_study"] = large

    report["populated_before_capture"] = report_populated
    report["captures"] = captures
    report["messages"] = messages
    _write(outdir, report)
    return 0 if not _warnings(messages) else 2


def _large_study(app, settle, window, keys, capture) -> dict | None:
    """A several-thousand-point study, to exercise the results table."""
    from rocketforge.application.analysis import thermochemistry_provider as gw
    from rocketforge.application.analysis.trade_study_controller import (
        TradeStudyController,
    )

    if not gw.availability().usable:
        return {"status": "skipped", "reason": "no chemistry provider"}

    found = app.findChildren(TradeStudyController)
    if not found:
        return None
    controller = found[0]

    if "tradestudy" in keys:
        window.setProperty("currentPageIndex", keys.index("tradestudy"))
    settle()

    controller.setVariableEnabled("oxidiser_fuel_ratio", True)
    controller.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 61)
    controller.setVariableEnabled("area_ratio", True)
    controller.setVariableRange("area_ratio", 10.0, 120.0, 50)
    controller.addObjective("chamber_temperature", "minimize")
    settle()

    expected_points = int(controller.pointCount)
    expected_solves = int(controller.chemistrySolveCount)

    started = time.perf_counter()
    controller.runStudy()
    while controller.busy and time.perf_counter() - started < 600.0:
        app.processEvents()
        _complete_deletions()
        time.sleep(0.002)
    run_seconds = time.perf_counter() - started
    settle()

    controller.showTab(1)
    published = time.perf_counter()
    capture("large_study_results_1920x1080",
            f"{expected_points} design points in the results table")
    table_seconds = time.perf_counter() - published

    rows = int(controller.visibleRowCount)
    controller.filterMode = "pareto"
    settle()
    pareto_rows = int(controller.visibleRowCount)
    controller.filterMode = "feasible"
    settle()
    feasible_rows = int(controller.visibleRowCount)
    controller.filterMode = "all"
    settle()

    controller.showTab(2)
    plotted = time.perf_counter()
    capture("large_study_pareto_1920x1080", "the front over a large grid")
    plot_seconds = time.perf_counter() - plotted

    summary = {row["label"]: row["value"] for row in controller.summaryRows}
    return {
        "design_points": expected_points,
        "expected_chemistry_solves": expected_solves,
        "reported_chemistry_solves": summary.get("Chamber solves"),
        "run_seconds": round(run_seconds, 2),
        "results_publication_seconds": round(table_seconds, 3),
        "pareto_publication_seconds": round(plot_seconds, 3),
        "table_rows": rows,
        "pareto_rows": pareto_rows,
        "feasible_rows": feasible_rows,
        "filters_work": pareto_rows <= feasible_rows <= rows,
        "status": controller.studyStatus,
    }


def _warnings(messages: list[dict]) -> list[dict]:
    return [entry for entry in messages
            if entry["kind"] in ("warning", "critical", "fatal")]


def _write(outdir, report) -> None:
    label = "frozen" if getattr(sys, "frozen", False) else "source"
    path = outdir / f"shell_smoke_{label}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    warnings = _warnings(report.get("messages", []))
    print(f"[shell-smoke] {label}: {report.get('workspace_count', 0)} "
          f"workspaces, {len(report.get('captures', []))} captures, "
          f"{len(report.get('messages', []))} Qt messages "
          f"({len(warnings)} warning or worse) -> {path}")
    large = report.get("large_study") or {}
    if large.get("design_points"):
        print(f"[shell-smoke] large study: {large['design_points']} points, "
              f"{large['reported_chemistry_solves']} chamber solves, "
              f"run {large['run_seconds']}s, table "
              f"{large['results_publication_seconds']}s, plot "
              f"{large['pareto_publication_seconds']}s")
    for entry in warnings[:20]:
        print(f"  [{entry['kind']}] {entry['message']}")
