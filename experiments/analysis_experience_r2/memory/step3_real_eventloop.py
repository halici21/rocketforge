"""Does the SHIPPING application retain pages? Driven by a real event loop.

Step 1 showed a scripted processEvents() soak reports a leak that a
DeferredDelete-dispatching soak does not. That distinguishes two harnesses.
It does not yet distinguish the PRODUCT: if RocketForge itself never let the
event loop unwind, the retention would be real for users regardless of how a
script measures it.

So this drives navigation from a QTimer inside app.exec(). Nothing here calls
processEvents, nothing forces a collection between rounds, and nothing
dispatches DeferredDelete by hand. Qt's own loop does whatever it really does.
"""
from __future__ import annotations
import gc, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QTimer, QObject
from lifecycle_lab import (build, navigation, memory, delta,
                           slope_mb_per_round, census, matching, ROOT)

OUT = ROOT / "acceptance" / "analysis_experience_r2_implementation" / "memory"
PAGES = ["isentropic", "fanno", "nozzlelab", "obliqueshock", "tradestudy"]
ROUNDS = 40


def main() -> int:
    app, engine, window = build()
    nav = navigation(engine)

    state = {"round": 0, "step": 0, "warm": 6, "base": None,
             "series": [], "items": []}

    def tick():
        # One page change per timer fire, so the loop fully unwinds between
        # each one -- exactly as it does when a person clicks the rail.
        key = PAGES[state["step"] % len(PAGES)]
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        state["step"] += 1

        if state["step"] % len(PAGES):
            return
        if state["warm"] > 0:
            state["warm"] -= 1
            if state["warm"] == 0:
                gc.collect()
                state["base"] = memory()
            return

        state["round"] += 1
        state["series"].append(delta(state["base"], memory())["private_mb"])
        state["items"].append(matching(census(window), "QQuickItem", "Canvas",
                                       "RFLineChart", "Page"))
        if state["round"] >= ROUNDS:
            timer.stop()
            app.quit()

    timer = QTimer()
    timer.setInterval(16)
    timer.timeout.connect(tick)
    timer.start()
    app.exec()

    series, items = state["series"], state["items"]
    slope = slope_mb_per_round(series)
    result = {
        "driver": "QTimer inside app.exec() -- a real Qt event loop",
        "no_manual_processEvents": True,
        "no_manual_deferred_delete_dispatch": True,
        "no_forced_gc_between_rounds": True,
        "pages_per_round": len(PAGES),
        "rounds": ROUNDS,
        "growth_mb": round(series[-1], 1),
        "slope_mb_per_round": round(slope, 4),
        "live_items_first": items[0],
        "live_items_last": items[-1],
        "live_item_growth": items[-1] - items[0],
        "series_mb": [round(v, 1) for v in series],
    }
    print("real event loop, %d rounds x %d pages" % (ROUNDS, len(PAGES)))
    print("  growth            : %.1f MB" % result["growth_mb"])
    print("  slope             : %.4f MB/round" % result["slope_mb_per_round"])
    print("  live items        : %d -> %d  (%+d)"
          % (items[0], items[-1], result["live_item_growth"]))
    print("  first 8 rounds    :", result["series_mb"][:8])
    print("  last 8 rounds     :", result["series_mb"][-8:])

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step3_real_eventloop.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")

    bounded = slope <= 0.5 and result["live_item_growth"] == 0
    print()
    print("VERDICT:", "BOUNDED -- the shipping app does not retain pages"
          if bounded else "GROWTH PRESENT under a real event loop")
    return 0 if bounded else 1


if __name__ == "__main__":
    sys.exit(main())
