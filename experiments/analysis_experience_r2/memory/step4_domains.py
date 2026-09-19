"""Step 3: which domain is growing, and is it reclaimable?

Step 3's real-event-loop run showed +2.27 MB/round with live QObject counts
going DOWN. So objects die correctly and something else accumulates. The
candidates separate cleanly if they are asked separately:

  Python heap          gc object count
  PySide wrappers      Python-side QObject wrapper count
  QML/JS heap          what QQmlEngine.collectGarbage() gives back
  component cache      what QQmlEngine.trimComponentCache() gives back
  QObject lifetime     the census (already flat)
  allocator high-water the SHAPE of the curve, and whether a reclaim helps

The distinction that matters: memory the process can still hand back on
request is a high-water mark, not a leak. Memory nothing reclaims is a leak.
"""
from __future__ import annotations
import gc, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QTimer, QObject
from lifecycle_lab import (build, navigation, memory, delta,
                           slope_mb_per_round, census, matching, ROOT)

OUT = ROOT / "acceptance" / "analysis_experience_r2_implementation" / "memory"
PAGES = ["isentropic", "fanno", "nozzlelab", "obliqueshock", "tradestudy"]
ROUNDS = 100


def python_objects():
    return len(gc.get_objects())


def qobject_wrappers():
    return sum(1 for o in gc.get_objects() if isinstance(o, QObject))


def main() -> int:
    app, engine, window = build()
    nav = navigation(engine)

    st = {"round": 0, "step": 0, "warm": 6, "base": None, "samples": []}

    def tick():
        window.setProperty("currentPageIndex",
                           nav.indexOfKey(PAGES[st["step"] % len(PAGES)]))
        st["step"] += 1
        if st["step"] % len(PAGES):
            return
        if st["warm"] > 0:
            st["warm"] -= 1
            if st["warm"] == 0:
                gc.collect()
                st["base"] = memory()
            return

        st["round"] += 1
        if st["round"] % 10 == 0 or st["round"] <= 3:
            st["samples"].append({
                "round": st["round"],
                "private_mb": round(delta(st["base"], memory())["private_mb"], 1),
                "py_objects": python_objects(),
                "py_qobject_wrappers": qobject_wrappers(),
                "live_items": matching(census(window), "QQuickItem", "Canvas",
                                       "RFLineChart", "Page"),
            })
        if st["round"] >= ROUNDS:
            timer.stop()
            app.quit()

    timer = QTimer(); timer.setInterval(8)
    timer.timeout.connect(tick); timer.start()
    app.exec()

    peak = delta(st["base"], memory())["private_mb"]

    # Ask each reclaimer in turn how much it can hand back.
    reclaim = {}
    engine.collectGarbage()
    reclaim["after_qml_js_gc_mb"] = round(delta(st["base"], memory())["private_mb"], 1)
    engine.trimComponentCache()
    reclaim["after_trim_component_cache_mb"] = round(
        delta(st["base"], memory())["private_mb"], 1)
    gc.collect()
    reclaim["after_python_gc_mb"] = round(delta(st["base"], memory())["private_mb"], 1)

    series = [s["private_mb"] for s in st["samples"]]
    first_half = [s for s in st["samples"] if s["round"] <= ROUNDS // 2]
    second_half = [s for s in st["samples"] if s["round"] > ROUNDS // 2]

    def slope_of(samples):
        if len(samples) < 2:
            return 0.0
        rounds = [s["round"] for s in samples]
        vals = [s["private_mb"] for s in samples]
        span = rounds[-1] - rounds[0]
        return (vals[-1] - vals[0]) / span if span else 0.0

    result = {
        "rounds": ROUNDS, "pages_per_round": len(PAGES),
        "peak_growth_mb": round(peak, 1),
        "slope_first_half_mb_per_round": round(slope_of(first_half), 3),
        "slope_second_half_mb_per_round": round(slope_of(second_half), 3),
        "decelerating": slope_of(second_half) < slope_of(first_half),
        "reclaim": reclaim,
        "reclaimed_mb": round(peak - reclaim["after_python_gc_mb"], 1),
        "samples": st["samples"],
    }

    print("100 rounds x %d pages, real event loop" % len(PAGES))
    print("  peak growth                : %.1f MB" % result["peak_growth_mb"])
    print("  slope, first half          : %.3f MB/round"
          % result["slope_first_half_mb_per_round"])
    print("  slope, second half         : %.3f MB/round"
          % result["slope_second_half_mb_per_round"])
    print("  decelerating               :", result["decelerating"])
    print("  after QML JS gc            : %.1f MB" % reclaim["after_qml_js_gc_mb"])
    print("  after trimComponentCache   : %.1f MB" % reclaim["after_trim_component_cache_mb"])
    print("  after python gc            : %.1f MB" % reclaim["after_python_gc_mb"])
    print("  reclaimed by asking        : %.1f MB" % result["reclaimed_mb"])
    print()
    print("  round  privateMB  pyObjects  pyQObjWrappers  liveItems")
    for s in st["samples"]:
        print("  %5d  %9.1f  %9d  %14d  %9d"
              % (s["round"], s["private_mb"], s["py_objects"],
                 s["py_qobject_wrappers"], s["live_items"]))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step4_domains.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
