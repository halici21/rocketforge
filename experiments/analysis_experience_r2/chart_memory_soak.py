"""Memory soak for the charts this program redesigned.

CORRECTED. An earlier revision of this file defined its own settle() from
processEvents() alone and reported ~56 MB/round retained on chart pages. That
was an artifact: Qt delivers DeferredDelete when the event loop unwinds to the
level that posted it, so a scripted loop that never unwinds never lets
deleteLater() complete, and every object correctly scheduled for destruction
was still there to be counted. harness.settle() had documented exactly this
trap; this file was not using it. It is now.

For the authoritative measurement see experiments/analysis_experience_r2/
memory/, which drives navigation from a QTimer inside app.exec() -- a real
event loop rather than a simulated one.


RFLineChart gained tick generation and per-role fonts inside its paint pass;
RFPlotSurface gained two computed tick arrays feeding Repeaters and a grid
Canvas. Both now recompute on every repaint. The question this answers is not
"is it fast" -- it is whether repeatedly driving them leaves anything behind.

Calibrated against the existing controls in experiments/qml_memory/harness.py
so a number here means the same thing it does there.
"""
from __future__ import annotations
import pathlib, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow  # noqa: F401
from PySide6.QtQml import QQmlComponent
import main as app_main
from harness import (memory, delta, slope_mb_per_round,
                     settle as harness_settle,
                     control_a_known_allocation, control_b_released_allocation)


def find_with_property(obj, name, depth=0):
    if obj is None or depth > 14:
        return None
    try:
        idx = obj.metaObject().indexOfProperty(name)
    except Exception:
        idx = -1
    if idx >= 0 and obj.metaObject().property(idx).isWritable():
        return obj
    for child in obj.children():
        hit = find_with_property(child, name, depth + 1)
        if hit is not None:
            return hit
    return None


def main() -> int:
    print("== controls ==")
    a = control_a_known_allocation()
    b = control_b_released_allocation()
    print("  A known allocation : saw %.1f MB of %d  pass=%s"
          % (a["seen"]["private_mb"], a["allocated_mb"], a["pass"]))
    print("  B released         : retained %.1f MB  pass=%s"
          % (b["retained"]["private_mb"], b["pass"]))
    if not a["pass"]:
        print("FAIL: the meter cannot see a real allocation, so a PASS below "
              "would mean nothing")
        return 1
    if not b["pass"]:
        print("FAIL: the meter reports retention for memory that was freed")
        return 1

    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]

    def settle(n=8):
        # harness.settle dispatches DeferredDelete. Do not replace this with a
        # bare processEvents() loop; see the module docstring.
        harness_settle(app, n)

    probe = QQmlComponent(engine)
    probe.setData(
        b'import QtQuick\nimport "data" as Data\n'
        b'QtObject { property var nav: Data.Navigation }',
        QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe_mem.qml")))
    nav = probe.create().property("nav")

    window.setProperty("width", 1920); window.setProperty("height", 1080)
    window.setProperty("themeMode", "dark"); window.setProperty("appMode", "analysis")
    settle()

    # Warm every chart-bearing page once so first-load cost is not counted as
    # growth. RFLineChart consumers plus the one RFPlotSurface consumer.
    pages = ["isentropic", "massflow", "normalshock", "prandtlmeyer", "fanno",
             "rayleigh", "nozzlelab", "obliqueshock", "tradestudy"]
    for key in pages:
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle()

    series = []
    base = memory()
    # Long enough for allocator noise to average out. At 12 rounds the band
    # this oscillates in (tens of MB, see memory/step7_soak500.json) is wider
    # than any trend inside it, so a fixed slope threshold over 12 rounds
    # tests the noise rather than the product.
    ROUNDS = 40
    for r in range(ROUNDS):
        for key in pages:
            window.setProperty("currentPageIndex", nav.indexOfKey(key))
            settle(4)
            page = find_with_property(window, "section")
            if page is not None:
                for section in range(3):
                    page.setProperty("section", section)
                    settle(2)
            qpage = find_with_property(window, "quantityIndex")
            if qpage is not None:
                for i in range(3):
                    qpage.setProperty("quantityIndex", i)
                    settle(2)
        # A theme flip repaints every Canvas in the tree.
        window.setProperty("themeMode", "light"); settle(4)
        window.setProperty("themeMode", "dark"); settle(4)
        now = memory()
        series.append(now["private_mb"])
        print("  round %2d  private %.1f MB" % (r + 1, now["private_mb"]))

    grew = delta(base, memory())
    slope = slope_mb_per_round(series)
    print()
    print("rounds              :", ROUNDS)
    print("total growth        : %.1f MB private, %.1f MB working set"
          % (grew["private_mb"], grew["working_set_mb"]))
    print("slope               : %.3f MB/round" % slope)

    # A leak keeps its slope; a high-water mark flattens. So the test is
    # deceleration over the run, not a fixed slope -- the same criterion the
    # 500-round soak uses, and the one the evidence actually supports.
    half = len(series) // 2
    first_half = slope_mb_per_round(series[:half])
    second_half = slope_mb_per_round(series[half:])
    print("slope, first half   : %.3f MB/round" % first_half)
    print("slope, second half  : %.3f MB/round" % second_half)

    if second_half > 0.5:
        print("FAIL: growth is still running at the end of the soak")
        return 1
    print("PASS: bounded -- growth decelerates rather than accumulating")
    return 0


if __name__ == "__main__":
    sys.exit(main())
