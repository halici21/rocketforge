"""Verifies the new parametric-sweep controller properties with a real
single-swept-variable study, before writing any QML for it."""
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

    messages = []

    def handler(kind, context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            messages.append(message)

    qInstallMessageHandler(handler)

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(rounds=8, pause=0.02):
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
        print("no thermochemistry provider")
        return 0

    thermoC.calculate(); settle()
    perfC.calculate(); settle()
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    # Single swept variable (O/F only) -- disable area_ratio which is
    # enabled by default.
    study.setVariableEnabled("area_ratio", False)
    study.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 21)
    settle()
    print("isParametricSweep (before run):", study.property("isParametricSweep"))

    study.runStudy()
    for _ in range(400):
        app.processEvents()
        time.sleep(0.01)
        if not study.property("busy"):
            break
    settle()

    print("isParametricSweep:", study.property("isParametricSweep"))
    print("sweepVariableKey:", study.property("sweepVariableKey"))
    print("sweepVariableTitle:", study.property("sweepVariableTitle"))
    options = study.property("responseMetricOptions")
    print("responseMetricOptions:", [(o["key"], o["label"]) for o in options] if options else options)

    metrics = study.property("sweepMetrics")
    print("default sweepMetrics:", list(metrics) if metrics else metrics)

    study.setSweepMetricEnabled("density_impulse", True)
    settle()
    metrics = study.property("sweepMetrics")
    print("after adding density_impulse:", list(metrics) if metrics else metrics)

    series = study.property("sweepSeries")
    print("\nsweepSeries: ", len(series) if series else 0, "series")
    for s in (series or []):
        pts = s["points"]
        xs = [p["x"] for p in pts]
        print(f"  {s['key']}: {len(pts)} points, x sorted: {xs == sorted(xs)}, "
              f"peak={s['peak']:.4g}, first={pts[0]}, last={pts[-1]}")

    # select a design in the middle of the sweep
    mid_index = series[0]["points"][len(series[0]["points"]) // 2]["index"]
    study.toggleSelection(mid_index)
    settle()
    rows = study.property("sweepComparisonRows")
    print(f"\nsweepComparisonRows for selected point {mid_index}:")
    for r in (rows or []):
        print("  ", r)

    # normalized view
    study.setProperty("sweepScaledToPeak", True)
    settle()
    series_norm = study.property("sweepSeries")
    print("\nnormalized note:", study.property("sweepScalingNote"))
    for s in (series_norm or []):
        ys = [p["y"] for p in s["points"] if p["hasValue"]]
        print(f"  {s['key']}: normalized y range [{min(ys):.4f}, {max(ys):.4f}]"
              f" (expect max == 1.0)")
        raw_ys = [p["rawY"] for p in s["points"] if p["hasValue"]]
        print(f"    rawY range [{min(raw_ys):.4g}, {max(raw_ys):.4g}] (unchanged)")

    print(f"\n{len(messages)} Qt warnings/criticals")
    for msg in messages:
        print(" ", msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
