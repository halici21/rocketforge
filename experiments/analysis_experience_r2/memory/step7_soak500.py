"""Step 9: the long soak. 500 rounds on the heaviest chart path.

20-round arms in step6 scattered between -0.6 and +2.3 MB/round with no
feature attribution, which is the signature of allocator noise rather than a
leak. The way to tell them apart is to run long enough that noise averages out
and a leak does not: a leak keeps its slope, a high-water mark flattens.

Real event loop, no manual processEvents, no forced collection between
rounds, no census (step5 proved the census is a wrapper factory).
"""
from __future__ import annotations
import gc, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QTimer
from lifecycle_lab import (build, navigation, memory, delta,
                           slope_mb_per_round, ROOT)

OUT = ROOT / "acceptance" / "analysis_experience_r2_implementation" / "memory"
PAGES = ["nozzlelab", "tradestudy", "isentropic", "obliqueshock"]
ROUNDS = 500

app, engine, window = build()
nav = navigation(engine)
st = {"round": 0, "step": 0, "warm": 6, "base": None, "series": []}


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
    st["series"].append(delta(st["base"], memory())["private_mb"])
    if st["round"] % 100 == 0:
        print("  round %4d   %+8.1f MB" % (st["round"], st["series"][-1]),
              flush=True)
    if st["round"] >= ROUNDS:
        timer.stop()
        app.quit()


timer = QTimer(); timer.setInterval(4)
timer.timeout.connect(tick); timer.start()
app.exec()

s = st["series"]


def seg(a, b):
    part = s[a:b]
    return round(slope_mb_per_round(part), 4) if len(part) > 2 else 0.0


quarters = [seg(0, 125), seg(125, 250), seg(250, 375), seg(375, 500)]
overall = round(slope_mb_per_round(s), 4)
peak = round(max(s), 1)
final = round(s[-1], 1)

result = {
    "driver": "QTimer inside app.exec()", "rounds": ROUNDS,
    "pages_per_round": len(PAGES),
    "page_loads": ROUNDS * len(PAGES),
    "peak_growth_mb": peak, "final_growth_mb": final,
    "overall_slope_mb_per_round": overall,
    "quarter_slopes": quarters,
    "decelerating": quarters[3] < quarters[0],
    "final_quarter_slope": quarters[3],
    "projected_mb_per_1000_page_loads": round(quarters[3] * 250, 1),
    "series_every_25": [round(v, 1) for v in s[::25]],
}

print()
print("500 rounds x %d pages = %d page loads" % (len(PAGES), ROUNDS * len(PAGES)))
print("  peak growth        : %.1f MB" % peak)
print("  final growth       : %.1f MB" % final)
print("  overall slope      : %.4f MB/round" % overall)
print("  quarter slopes     : %s" % quarters)
print("  final-quarter slope: %.4f MB/round" % quarters[3])
print("  decelerating       : %s" % result["decelerating"])

bounded = quarters[3] <= 0.10
print()
print("VERDICT:", "BOUNDED" if bounded else "UNBOUNDED GROWTH")

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "step7_soak500.json").write_text(json.dumps(result, indent=2) + "\n",
                                        encoding="utf-8")
sys.exit(0 if bounded else 1)
