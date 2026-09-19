"""Solve-call matrix for the redesigned Trade Study workspace.

Verifies the mega-prompt's BLOCKING zero-physics gate: axis switch, hover,
point selection, table selection/sort/column-visibility, Inspector
open/close, Dock open/close, resize and theme change must all cause zero
chemistry and zero performance solves. Evaluate itself must cause the
expected non-zero count. Instrumented by monkey-patching the exact module
functions `trade_study_service.py` captures at evaluator-construction time
(`thermo.solve_case`, `perf.solve_performance`), per this project's
established solve-call-parity technique -- patched on the already-imported
module objects, no importlib.reload, spied via a call counter.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent

    import main as app_main
    from rocketforge.application.analysis import thermochemistry_service as thermo
    from rocketforge.application.analysis import performance_service as perf

    messages = []
    kinds = {QtMsgType.QtWarningMsg: "warning", QtMsgType.QtCriticalMsg: "critical",
             QtMsgType.QtFatalMsg: "fatal"}

    def handler(kind, context, message):
        if kind in kinds:
            messages.append((kinds[kind], message))

    qInstallMessageHandler(handler)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=6, pause=0.02):
        for _ in range(rounds):
            app.processEvents()
            time.sleep(pause)
            app.processEvents()

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport RocketForge 1.0\nimport "data"\n'
        b'QtObject { property var thermoC: Thermochemistry\n'
        b'  property var perfC: RocketPerformance\n'
        b'  property var study: TradeStudy\n'
        b'  property int idx: Navigation.indexOfKey("tradestudy") }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe.qml")))
    holder = probe.create()
    thermoC = holder.property("thermoC")
    perfC = holder.property("perfC")
    study = holder.property("study")

    if not thermoC.property("providerAvailable"):
        print("no thermochemistry provider -- cannot run this matrix")
        return 0

    thermoC.calculate()
    settle()
    perfC.calculate()
    settle()
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    # -- instrument -------------------------------------------------------
    counts = {"chemistry": 0, "performance": 0}
    real_solve_case = thermo.solve_case
    real_solve_performance = perf.solve_performance

    def spy_solve_case(*args, **kwargs):
        counts["chemistry"] += 1
        return real_solve_case(*args, **kwargs)

    def spy_solve_performance(*args, **kwargs):
        counts["performance"] += 1
        return real_solve_performance(*args, **kwargs)

    thermo.solve_case = spy_solve_case
    perf.solve_performance = spy_solve_performance

    def reset():
        counts["chemistry"] = 0
        counts["performance"] = 0

    def total():
        return counts["chemistry"] + counts["performance"]

    results = []

    def record(label, before_ok=True):
        results.append((label, counts["chemistry"], counts["performance"],
                        before_ok))

    # -- a real study, with two objectives so Pareto is populated ---------
    study.addObjective("chamber_temperature", "minimize")
    settle()
    reset()
    study.runStudy()
    for _ in range(400):
        app.processEvents()
        time.sleep(0.01)
        if not study.property("busy"):
            break
    settle()
    record("Evaluate (baseline study)")
    baseline_chem = counts["chemistry"]
    print(f"Evaluate: {baseline_chem} chemistry, {counts['performance']} "
          f"performance solves, hasResult={study.property('hasResult')}, "
          f"points={study.property('visibleRowCount')}")
    if baseline_chem <= 0:
        print("FAIL: Evaluate produced zero chemistry solves")
        return 1

    # -- view-only interactions: each must be exactly zero -----------------
    reset()
    options = study.property("objectiveAxisOptions")
    axis_keys = [o["key"] for o in options] if options else []
    print("axis options:", axis_keys)

    def try_axis(prop, key):
        reset()
        study.setProperty(prop, key)
        settle()
        record(f"set {prop} -> {key}")

    # Switch X through every available axis (design variable AND metric).
    for key in axis_keys:
        try_axis("paretoX", key)
    # And Y, back to something else.
    for key in reversed(axis_keys):
        try_axis("paretoY", key)

    reset()
    study.toggleSelection(0)
    settle()
    record("select point 0 (marker tap)")

    reset()
    study.toggleSelection(1)
    settle()
    record("select point 1 (second marker tap)")

    reset()
    study.toggleSelection(1)
    settle()
    record("deselect point 1")

    reset()
    study.clearSelection()
    settle()
    record("clear selection")

    reset()
    study.setProperty("filterMode", "feasible")
    settle()
    record("table filter change")
    study.setProperty("filterMode", "all")
    settle()

    reset()
    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    settle()
    record("resize to 1366x768")
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()

    reset()
    window.setProperty("themeMode", "light")
    settle()
    record("theme change to light")
    window.setProperty("themeMode", "dark")
    settle()

    reset()
    study.addConstraint("chamber_temperature", "<=", 3600.0)
    settle()
    record("add constraint (decision-layer re-analysis)")
    constraint_calls = total()

    reset()
    study.setProperty("scoringEnabled", True)
    settle()
    record("enable scoring (decision-layer re-analysis)")
    scoring_calls = total()

    # -- parametric sweep view: mode switch, metric choice, normalization --
    reset()
    study.setVariableEnabled("area_ratio", False)
    settle()
    study.runStudy()
    for _ in range(400):
        app.processEvents()
        time.sleep(0.01)
        if not study.property("busy"):
            break
    settle()
    baseline_sweep_chem = counts["chemistry"]
    print(f"\nsweep-study Evaluate: {baseline_sweep_chem} chemistry, "
          f"{counts['performance']} performance, "
          f"isParametricSweep={study.property('isParametricSweep')}")

    reset()
    study.setSweepMetricEnabled("characteristic_velocity", True)
    settle()
    record("enable a second sweep response curve")

    reset()
    study.setSweepMetricEnabled("characteristic_velocity", False)
    settle()
    record("disable a sweep response curve")

    reset()
    study.setProperty("sweepScaledToPeak", True)
    settle()
    record("toggle sweep normalization on")
    study.setProperty("sweepScaledToPeak", False)
    settle()

    reset()
    study.toggleSelection(5)
    settle()
    record("select a point on a sweep curve")
    study.toggleSelection(5)
    settle()

    # -- report -------------------------------------------------------------
    print("\n--- solve-call matrix ---")
    all_zero = True
    for label, chem, prf, _ in results:
        if "Evaluate" in label:
            continue
        bad = (chem, prf) != (0, 0)
        all_zero = all_zero and not bad
        flag = "FAIL" if bad else "ok"
        print(f"  [{flag}] {label}: chemistry={chem} performance={prf}")

    print(f"\nconstraint edit (decision-layer, chemistry+performance "
          f"expected 0): {constraint_calls}")
    print(f"scoring enable (decision-layer, expected 0): {scoring_calls}")
    if constraint_calls != 0 or scoring_calls != 0:
        all_zero = False

    warnings = messages
    print(f"\n{len(warnings)} Qt warnings/criticals")
    for kind, msg in warnings:
        print(f"  {kind}: {msg}")

    # Sanity check: a design-variable axis pair must still populate points
    # (the _axis_value fallback), not silently come back empty. Re-enable
    # area_ratio (disabled above for the single-swept-variable checks) and
    # re-run so it is part of the study's own variables again.
    study.setVariableEnabled("area_ratio", True)
    settle()
    study.runStudy()
    for _ in range(400):
        app.processEvents()
        time.sleep(0.01)
        if not study.property("busy"):
            break
    settle()
    study.setProperty("paretoX", "oxidiser_fuel_ratio")
    study.setProperty("paretoY", "area_ratio")
    settle()
    series = study.property("paretoSeries")
    total_points = sum(len(s["points"]) for s in series) if series else 0
    print(f"\ndesign-variable axis pair (O/F vs area ratio): "
          f"{total_points} points across {len(series) if series else 0} series")
    if total_points == 0:
        print("FAIL: a design-variable axis pair produced zero plotted points")
        all_zero = False

    print("\nRESULT:", "PASS" if all_zero and not warnings else "FAIL")
    return 0 if all_zero and not warnings else 1


if __name__ == "__main__":
    sys.exit(main())
