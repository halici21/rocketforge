"""One ablation variant, in its own process. Prints one JSON line."""
from __future__ import annotations
import gc, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from rig import (build, navigation, settle, memory, delta, slope_mb_per_round,
                 census, find_prop)

cfg = json.loads(sys.argv[1])
PAGES, ROUNDS = cfg["pages"], cfg.get("rounds", 12)
MODE = cfg.get("mode", "destroy")

app, engine, window = build()
nav = navigation(engine)

for key in PAGES:
    window.setProperty("currentPageIndex", nav.indexOfKey(key))
    settle(app, 5)
gc.collect()

base_mem, base_census = memory(), census(window)
series = []
for _ in range(ROUNDS):
    for key in PAGES:
        if MODE == "hide":
            # Page stays alive; only its visibility changes.
            item = find_prop(window, "visible")
            window.setProperty("currentPageIndex", nav.indexOfKey(PAGES[0]))
        else:
            window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle(app, 5)
    series.append(round(delta(base_mem, memory())["private_mb"], 1))

final = census(window)
growth = {k: final[k] - base_census[k] for k in base_census}
half = len(series) // 2
print(json.dumps({
    "rounds": ROUNDS, "page_loads": ROUNDS * len(PAGES),
    "growth_mb": series[-1],
    "slope_mb_per_round": round(slope_mb_per_round(series), 3),
    "early_slope": round(slope_mb_per_round(series[:half]), 3),
    "late_slope": round(slope_mb_per_round(series[half:]), 3),
    "obj_pages": growth["workspace_pages"],
    "obj_charts": growth["RFLineChart"] + growth["RFPlotSurface"],
    "obj_canvas": growth["Canvas"],
    "obj_hover": growth["HoverHandler"],
    "obj_connections": growth["Connections"],
    "obj_items": growth["all_quick_items"],
}))
