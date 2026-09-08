"""A non-interactive tour of the Thermochemistry workspace, runnable frozen.

Sibling of :mod:`rocketforge.application.selftest`, and it exists for the same
reason. That module answers "can the packaged provider solve?"; this one
answers "does the packaged **interface** load, navigate, calculate, and show
the same numbers the source build shows?" Neither question can be answered by
inspecting ``dist/``.

Invoked as::

    RocketForge.exe --selftest-thermochemistry-ui <output directory>

It loads the real QML, drives the real controller, writes one JSON report and
a set of PNG captures, and exits. There is no menu entry, no window that
outlives it and no user-facing surface: this is a diagnostic.

**It sends no synthetic desktop input.** Navigation goes through the same slots
the interface's own controls call, so it cannot type into whatever window
happens to be in front, and it works under the offscreen platform plugin.

``application`` is the composition root, so this is the layer allowed to reach
a provider. As with the other self-test, every import that could pull in a
chemistry library is function-local, so a normal launch pays nothing for it.
"""

from __future__ import annotations

import json
import sys
import time

__all__ = ["UI_SMOKE_FLAG", "run_ui_smoke", "RESOLUTIONS"]

#: The argument that triggers the workspace tour.
UI_SMOKE_FLAG = "--selftest-thermochemistry-ui"

#: The window sizes the visual gate is judged at, unchanged since Phase 4G.
RESOLUTIONS = ((2560, 1440), (1920, 1080), (1366, 768))

CALCULATOR, COMPOSITION, SWEEP, REFERENCES = 0, 1, 2, 3



def _complete_deletions() -> None:
    # DeferredDelete is not dispatched by processEvents(); it is
    # delivered when the loop unwinds to the exec() that posted it. A
    # tour driven only by processEvents() therefore never completes a
    # single deleteLater(), so objects Qt has correctly destroyed stay
    # committed and the tour's memory profile is not the application's.
    # See docs/engineering/implementation/QML_MEMORY_ROOT_CAUSE.md.
    from PySide6.QtCore import QCoreApplication, QEvent

    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def run_ui_smoke(argv, configure, build_engine, ui_dir) -> int:
    """Load the interface, tour the workspace, and report what it held.

    The bootstrap is handed in rather than imported. A frozen build runs
    ``main.py`` as ``__main__``, so ``import main`` there would either fail or
    load a second copy of it; taking the three pieces this needs as arguments
    means the same code runs identically from source and from the bundle.

    Returns 0 when the tour completed with no Qt warning, 2 when it completed
    with warnings, and 1 when it could not run at all.
    """
    from pathlib import Path

    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    ui_dir = Path(ui_dir)
    outdir = Path(argv[0]) if argv else Path.cwd() / "ui_smoke"
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

    found = app.findChildren(ThermochemistryController)
    if not found:
        _write(outdir, {"status": "controller_missing", "messages": messages})
        return 1
    controller = found[0]

    # Ask the navigation model where the workspace is, rather than assuming an
    # index that a later page would silently shift.
    probe_component = QQmlComponent(engine)
    probe_component.setData(
        b'import QtQuick\nimport "data"\n'
        b'QtObject { property int idx: Navigation.indexOfKey("thermochem") }',
        QUrl.fromLocalFile(str(ui_dir / "_probe.qml")))
    probe = probe_component.create()
    if probe is None:
        _write(outdir, {"status": "navigation_probe_failed",
                        "detail": probe_component.errorString(),
                        "messages": messages})
        return 1
    window.setProperty("currentPageIndex", int(probe.property("idx")))

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
        "provider_available": bool(controller.providerAvailable),
        "provider_headline": controller.providerHeadline,
    }

    if not controller.providerAvailable:
        for width, height in RESOLUTIONS:
            window.setProperty("width", width)
            window.setProperty("height", height)
            capture(f"no_provider_{width}x{height}",
                    "no chemistry provider installed")
        report["captures"] = captures
        report["messages"] = messages
        _write(outdir, report)
        return 0 if not _warnings(messages) else 2

    for width, height in RESOLUTIONS:
        tag = f"{width}x{height}"
        window.setProperty("width", width)
        window.setProperty("height", height)

        controller.resetInputs()
        show(CALCULATOR)
        capture(f"calculator_empty_{tag}",
                "before any calculation: no numbers, intentional empty state")

        controller.calculate()
        capture(f"calculator_result_{tag}",
                "the validated demonstration case, LOX/LCH4 at O/F 3.4, 10 MPa")

        controller.oxidiserTemperature = 95.0
        controller.calculate()
        capture(f"calculator_warning_{tag}",
                "LOX requested at 95 K; the provider uses its assigned enthalpy")

        controller.oxidiserTemperature = 200.0
        controller.calculate()
        capture(f"calculator_refused_{tag}",
                "stream temperature outside the provider's declared range")

        controller.resetInputs()
        controller.calculate()
        show(COMPOSITION)
        capture(f"composition_{tag}", "full product composition")

        controller.traceThresholdIndex = 3
        capture(f"composition_filtered_{tag}",
                "display threshold applied; hidden species stated, not removed")
        controller.traceThresholdIndex = 0

        controller.mixtureRatio = 0.5
        controller.calculate()
        capture(f"composition_condensed_{tag}",
                "fuel-rich O/F 0.5: real condensed carbon")
        controller.resetInputs()
        controller.calculate()

        show(SWEEP)
        capture(f"sweep_empty_{tag}", "sweep setup before running")
        controller.runSweep()
        capture(f"sweep_{tag}", "41 points, O/F 2.5 to 4.5")

        show(REFERENCES)
        capture(f"references_before_{tag}", "reference case not yet run")
        controller.runReference()
        capture(f"references_{tag}", "published NASA CEA case, compared")

    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    window.setProperty("themeMode", "light")
    show(CALCULATOR)
    capture("calculator_light_1920x1080", "light theme")
    show(COMPOSITION)
    capture("composition_light_1920x1080", "light theme")
    window.setProperty("themeMode", "dark")

    report["captures"] = captures
    report["messages"] = messages
    _write(outdir, report)
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
        "providerAvailable": bool(controller.providerAvailable),
        "providerHeadline": controller.providerHeadline,
        "statusKind": controller.statusKind,
        "statusLabel": controller.statusLabel,
        "statusMessage": controller.statusMessage,
        "resultHeadline": controller.resultHeadline,
        "resultStale": bool(controller.resultStale),
        "warningCount": int(controller.warningCount),
        "assignedEnthalpy": [dict(note) for note in controller.assignedEnthalpyNotes],
        "provenance": dict(controller.provenanceSummary),
        "speciesSet": list(controller.speciesSet),
        "speciesTotal": int(controller.speciesTotal),
        "speciesShown": int(controller.speciesShown),
        "condensed": dict(controller.condensed),
        "hasSweep": bool(controller.hasSweep),
        "sweepSolved": int(controller.sweepSolvedCount),
        "sweepFailed": int(controller.sweepFailedCount),
        "referenceVerdict": controller.referenceVerdict,
        "referenceRows": [dict(row) for row in controller.referenceRows],
        "resultRows": [{"key": row["key"], "value": row["value"],
                        "raw": row["raw"], "unit": row["unit"],
                        "qualifier": row["qualifier"]}
                       for row in controller.resultRows],
        "advancedRows": [{"key": row["key"], "value": row["value"],
                          "raw": row["raw"], "unit": row["unit"]}
                         for row in controller.advancedRows],
    }


def _write(outdir, report) -> None:
    label = "frozen" if getattr(sys, "frozen", False) else "source"
    path = outdir / f"ui_smoke_{label}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    warnings = _warnings(report.get("messages", []))
    print(f"[ui-smoke] {label}: {len(report.get('captures', []))} captures, "
          f"{len(report.get('messages', []))} Qt messages "
          f"({len(warnings)} warning or worse) -> {path}")
    for entry in warnings[:20]:
        print(f"  [{entry['kind']}] {entry['message']}")
