"""Large-study performance measurement for the redesigned Trade Study Pareto view.

Mega-prompt item 25: measure, don't assume, at >= 1000 points and several
thousand if the architecture supports it. `area_ratio` is a nozzle-stage
variable (TRADE_STUDY_API_V1.md) -- widening its count multiplies points
without multiplying chemistry solves, so a several-thousand-point study
stays cheap to actually run here.

Each existing StudyPareto.qml marker is a real QML Item (Rectangle +
HoverHandler + TapHandler + RFTooltip) inside a nested Repeater, one per
evaluated point -- exactly the pattern rf-scientific-visualization's own
"large studies stay responsive" section warns about. This script measures
wall-clock time for publication, an axis switch and a selection change at
that scale, and RSS growth, rather than assuming it is fine or broken.
"""
from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))

# The project's own established, control-verified process-memory probe
# (rf-qml-architecture Rule 2: a naive ctypes/psapi probe here has silently
# returned 0 before). Reused rather than reimplemented.
import harness as memharness  # noqa: E402


def rss_mb() -> float:
    return memharness.memory()["working_set_mb"]


def main() -> int:
    from PySide6.QtCore import QCoreApplication, QEvent, QUrl, QtMsgType, qInstallMessageHandler
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

    def settle(rounds=6, pause=0.02):
        for _ in range(rounds):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(pause)

    # Positive control: prove the RSS probe actually sees allocation before
    # trusting a "no growth" reading later (rf-qml-architecture Rule 2).
    before = rss_mb()
    _ballast = bytearray(150 * 1024 * 1024)
    after = rss_mb()
    del _ballast
    print(f"positive control: {before:.1f} MB -> {after:.1f} MB "
          f"(delta {after - before:.1f} MB)")
    if after - before < 50:
        print("FAIL: RSS probe did not detect a 150MB allocation -- "
              "do not trust readings below")
        return 1

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
        print("no thermochemistry provider -- cannot run this measurement")
        return 0

    thermoC.calculate()
    settle()
    perfC.calculate()
    settle()
    window.setProperty("currentPageIndex", int(holder.property("idx")))
    settle()

    study.addObjective("chamber_temperature", "minimize")
    # Global closeout section 10: reproduce one representative NEAR-CAP case
    # (the documented ~16k-point dense-column legibility limit), not a new
    # binning algorithm -- 164 O/F values x 100 area-ratio values = 16400
    # points, matching the Trade Study integration report's own recorded
    # 16400-row near-cap run.
    study.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 164)
    study.setVariableRange("area_ratio", 10.0, 80.0, 100)
    settle()
    print("planned points:", study.property("pointCount"),
          "planned chemistry solves:", study.property("chemistrySolveCount"))

    t0 = time.perf_counter()
    study.runStudy()
    guard = 0
    while study.property("busy") and guard < 400_000:
        app.processEvents()
        guard += 1
    t_run = time.perf_counter() - t0
    settle()
    n_points = study.property("visibleRowCount")
    print(f"\nEvaluate {n_points} points: {t_run:.2f} s wall clock "
          f"({1000 * t_run / max(1, n_points):.2f} ms/point)")

    rss_after_run = rss_mb()
    print(f"RSS after publication: {rss_after_run:.1f} MB")

    # Force Pareto tab visible -- StudyPareto.qml's nested-Repeater markers
    # only exist while that tab is the current StackLayout page.
    study.showTab(2)
    settle(rounds=20, pause=0.03)
    rss_after_pareto = rss_mb()
    print(f"RSS after Pareto tab render "
          f"({n_points} marker Items instantiated): {rss_after_pareto:.1f} MB "
          f"(delta {rss_after_pareto - rss_after_run:.1f} MB)")

    options = study.property("objectiveAxisOptions")
    keys = [o["key"] for o in options] if options else []

    t0 = time.perf_counter()
    study.setProperty("paretoX", keys[0] if keys else "")
    settle(rounds=10, pause=0.02)
    t_axis = time.perf_counter() - t0
    print(f"\nAxis switch (X -> {keys[0] if keys else '?'}): "
          f"{1000 * t_axis:.1f} ms")

    t0 = time.perf_counter()
    study.toggleSelection(0)
    settle(rounds=10, pause=0.02)
    t_select = time.perf_counter() - t0
    print(f"Point selection: {1000 * t_select:.1f} ms")
    study.toggleSelection(0)
    settle()

    t0 = time.perf_counter()
    window.setProperty("width", 1366)
    window.setProperty("height", 768)
    settle(rounds=10, pause=0.02)
    t_resize = time.perf_counter() - t0
    print(f"Resize with {n_points} points on screen: {1000 * t_resize:.1f} ms")
    window.setProperty("width", 1920)
    window.setProperty("height", 1080)
    settle()

    # Idle CPU proxy: pump the event loop with nothing changing and time it.
    t0 = time.perf_counter()
    for _ in range(60):
        app.processEvents()
        time.sleep(0.01)
    t_idle = time.perf_counter() - t0
    print(f"\n60 idle event-loop turns: {t_idle:.2f} s "
          f"(no repaint should be forced by this)")

    rss_final = rss_mb()
    print(f"\nFinal RSS: {rss_final:.1f} MB")

    print(f"\n{len(messages)} Qt warnings/criticals")
    for msg in messages[:20]:
        print(" ", msg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
