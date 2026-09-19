"""Section 5: reproduce the reported leak on the approved tree, instrumented.

Two arms that differ ONLY in whether DeferredDelete is dispatched between
navigations. Everything else -- tree, pages, meter, round count -- is
identical, so any difference is attributable to that one variable.
"""
from __future__ import annotations
import gc, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from rig import (build, navigation, settle, memory, delta, slope_mb_per_round,
                 census, ROOT)

OUT = ROOT / "acceptance" / "analysis_r2_closure" / "memory"
PAGES = ["isentropic", "fanno"]
ROUNDS = 10


def arm(app, window, nav, deferred, label):
    for key in PAGES:                      # warm
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        settle(app, 5, deferred=True)
    gc.collect()

    base_mem = memory()
    base_census = census(window)
    series, counts = [], []
    for _ in range(ROUNDS):
        for key in PAGES:
            window.setProperty("currentPageIndex", nav.indexOfKey(key))
            settle(app, 5, deferred=deferred)
        series.append(round(delta(base_mem, memory())["private_mb"], 1))
        counts.append(census(window))

    final = counts[-1]
    growth = {k: final[k] - base_census[k] for k in base_census}
    res = {
        "label": label, "deferred_delete_dispatched": deferred,
        "pages": PAGES, "rounds": ROUNDS,
        "page_loads": ROUNDS * len(PAGES),
        "private_mb_growth": series[-1],
        "slope_mb_per_round": round(slope_mb_per_round(series), 3),
        "mb_per_page_load": round(series[-1] / (ROUNDS * len(PAGES)), 2),
        "series_mb": series,
        "census_baseline": base_census,
        "census_final": final,
        "census_growth": growth,
    }
    print("  %-34s  %7.1f MB  (%5.2f MB/load)  slope %7.3f"
          % (label, series[-1], res["mb_per_page_load"],
             res["slope_mb_per_round"]))
    for k in ("workspace_pages", "RFLineChart", "Canvas", "HoverHandler",
              "Connections", "all_quick_items", "_total_qobjects"):
        if growth.get(k):
            print("        %-20s %+d" % (k, growth[k]))
    return res


def main() -> int:
    app, engine, window = build()
    nav = navigation(engine)

    print("== section 5: reproduction, %d rounds x %d pages ==" % (ROUNDS, len(PAGES)))
    broken = arm(app, window, nav, False, "processEvents only (as filed)")
    fixed = arm(app, window, nav, True, "+ DeferredDelete dispatched")

    reproduced = broken["mb_per_page_load"] > 5
    explained = (fixed["mb_per_page_load"] < broken["mb_per_page_load"] * 0.2
                 and fixed["census_growth"]["all_quick_items"] <= 0)

    report = {
        "tree": "approved Analysis R2 working tree, unmodified",
        "prior_claim": {"per_round_mb": 171, "per_chart_page_destroy_mb": 28},
        "arms": {"without_deferred_delete": broken,
                 "with_deferred_delete": fixed},
        "leak_reproduced_with_original_method": reproduced,
        "difference_explained_by_deferred_delete": explained,
        "lifecycle_paths_exercised": {
            "navigation": "Main.qml currentPageIndex -> WorkspaceHost Loader.source",
            "creation": "Loader instantiates pages/<Page>.qml",
            "destruction": "Loader.source change destroys the previous item",
            "chart_primitive": "RFLineChart (Canvas) / RFPlotSurface",
            "model_publication": "controller QVariantList properties read by QML",
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reproduction.json").write_text(json.dumps(report, indent=2) + "\n",
                                           encoding="utf-8")
    (OUT / "object_counts.json").write_text(json.dumps(
        {"without_deferred_delete": broken["census_growth"],
         "with_deferred_delete": fixed["census_growth"],
         "baseline": fixed["census_baseline"],
         "note": "growth is final minus baseline over the run"},
        indent=2) + "\n", encoding="utf-8")

    print()
    print("reproduced with the original method :", reproduced)
    print("explained by DeferredDelete         :", explained)
    return 0


if __name__ == "__main__":
    sys.exit(main())
