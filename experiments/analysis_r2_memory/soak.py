"""Sections 21-23: acceptance soaks under a real Qt event loop.

Driven by a QTimer inside app.exec(). No manual processEvents, no hand
dispatch of DeferredDelete, no forced collection between rounds -- Qt's own
loop does whatever it really does, which is the only faithful model of what a
user's session does.

Object counts are sampled sparsely and only at the ends, because findChildren
creates a Python wrapper per object and would otherwise be measuring itself.
"""
from __future__ import annotations
import gc, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QTimer, QCoreApplication, QEvent
from rig import (build, navigation, memory, delta, slope_mb_per_round,
                 census, find_prop, ROOT)

#: Censuses are taken from here, always. A count taken while a chart page is
#: resident includes that page's own items, so comparing a baseline taken on
#: one page with a final taken on another measures which page is loaded rather
#: than what was retained. Parking on a fixed, chart-free page first removes
#: that confound entirely.
CENSUS_PAGE = "equations"

OUT = ROOT / "acceptance" / "analysis_r2_closure" / "memory"

PROFILES = {
    "focused_100": {
        "rounds": 100,
        "pages": ["isentropic", "fanno"],
        "interact": True,
        "note": "focused chart-page create/destroy with interaction"},
    "focused_500": {
        "rounds": 500,
        "pages": ["isentropic", "fanno"],
        "interact": True,
        "note": "same reproducer, long run"},
    "mixed_session": {
        "rounds": 100,
        "pages": ["isentropic", "obliqueshock", "nozzlelab", "thermochem",
                  "performance", "tradestudy", "fluidproperties", "line"],
        "interact": True, "theme": True, "resize": True,
        "note": "representative Analysis session across all eight workspaces"},
}


def census_from_parking(window, nav, app):
    """Park on CENSUS_PAGE, let deletions finish, then count."""
    window.setProperty("currentPageIndex", nav.indexOfKey(CENSUS_PAGE))
    for _ in range(20):
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    gc.collect()
    return census(window)


def main() -> int:
    name = sys.argv[1]
    cfg = PROFILES[name]
    app, engine, window = build()
    nav = navigation(engine)

    st = {"round": 0, "step": 0, "warm": 8, "base": None, "series": [],
          "census_base": None, "census_final": None}

    def tick():
        pages = cfg["pages"]
        key = pages[st["step"] % len(pages)]
        window.setProperty("currentPageIndex", nav.indexOfKey(key))

        if cfg.get("interact"):
            # Real interaction on the page we just entered: change the
            # displayed mode, and move the chart's hover state.
            page = find_prop(window, "section")
            if page is not None:
                page.setProperty("section",
                                 (st["step"] // len(pages)) % 2)
            chart = find_prop(window, "hoverActive")
            if chart is not None:
                chart.setProperty("hoverActive", st["step"] % 2 == 0)
        st["step"] += 1
        if st["step"] % len(pages):
            return

        if cfg.get("theme") and st["round"] % 5 == 0:
            window.setProperty("themeMode",
                               "light" if st["round"] % 10 else "dark")
        if cfg.get("resize") and st["round"] % 7 == 0:
            window.setProperty("width", 1366 if st["round"] % 14 else 1920)
            window.setProperty("height", 768 if st["round"] % 14 else 1080)

        if st["warm"] > 0:
            st["warm"] -= 1
            if st["warm"] == 0:
                gc.collect()
                st["base"] = memory()
                st["census_base"] = census_from_parking(window, nav, app)
            return

        st["round"] += 1
        st["series"].append(round(delta(st["base"], memory())["private_mb"], 1))
        if st["round"] % 50 == 0:
            print("    round %4d  %+8.1f MB" % (st["round"], st["series"][-1]),
                  flush=True)
        if st["round"] >= cfg["rounds"]:
            st["census_final"] = census_from_parking(window, nav, app)
            timer.stop()
            app.quit()

    timer = QTimer(); timer.setInterval(4)
    timer.timeout.connect(tick); timer.start()
    app.exec()

    s = st["series"]
    half = len(s) // 2
    growth = {k: st["census_final"][k] - st["census_base"][k]
              for k in st["census_base"]}
    watched = ("workspace_pages", "RFLineChart", "RFPlotSurface", "Canvas",
               "HoverHandler", "TapHandler", "Connections", "Loader",
               "all_quick_items")
    bounded_objects = all(growth[k] <= 0 for k in watched)

    res = {
        "profile": name, "note": cfg["note"],
        "driver": "QTimer inside app.exec() (real event loop)",
        "rounds": cfg["rounds"], "pages": cfg["pages"],
        "page_loads": cfg["rounds"] * len(cfg["pages"]),
        "interaction": bool(cfg.get("interact")),
        "theme_cycled": bool(cfg.get("theme")),
        "resize_cycled": bool(cfg.get("resize")),
        "baseline_mb": 0.0,
        "peak_mb": round(max(s), 1), "final_mb": round(s[-1], 1),
        "first_half_slope": round(slope_mb_per_round(s[:half]), 4),
        "second_half_slope": round(slope_mb_per_round(s[half:]), 4),
        "overall_slope": round(slope_mb_per_round(s), 4),
        "object_growth": {k: growth[k] for k in watched},
        "object_counts_bounded": bounded_objects,
        "series_sampled": [round(v, 1) for v in s[::max(1, len(s) // 20)]],
    }
    res["bounded"] = bounded_objects and res["second_half_slope"] <= 0.5

    print("  %s: peak %.1f MB, final %.1f MB" % (name, res["peak_mb"], res["final_mb"]))
    print("  slopes: first half %.4f, second half %.4f"
          % (res["first_half_slope"], res["second_half_slope"]))
    print("  object growth:", {k: v for k, v in res["object_growth"].items() if v})
    print("  BOUNDED:", res["bounded"])

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / (name + ".json")).write_text(json.dumps(res, indent=2) + "\n",
                                        encoding="utf-8")
    return 0 if res["bounded"] else 1


if __name__ == "__main__":
    sys.exit(main())
