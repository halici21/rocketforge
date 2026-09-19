"""Step 1-2: revalidate the harness, then reproduce the leak two ways.

The two ways differ only in whether DeferredDelete is dispatched between
rounds. If the reported leak is an artifact of the earlier soak never
dispatching it, that difference is the whole story and the rest of the
investigation is about something else.
"""
from __future__ import annotations
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from lifecycle_lab import (build, navigation, settle, memory, delta,
                           slope_mb_per_round, census, matching, ROOT)
from harness import run_calibration

PAGES = ["isentropic", "fanno"]
OUT = ROOT / "acceptance" / "analysis_experience_r2_implementation" / "memory"


def soak(app, window, nav, rounds, deferred, label):
    for _ in range(3):                      # warm
        for key in PAGES:
            window.setProperty("currentPageIndex", nav.indexOfKey(key))
            settle(app, 4, deferred=deferred)

    base = memory()
    series, items = [], []
    for _ in range(rounds):
        for key in PAGES:
            window.setProperty("currentPageIndex", nav.indexOfKey(key))
            settle(app, 4, deferred=deferred)
        series.append(delta(base, memory())["private_mb"])
        items.append(matching(census(window), "QQuickItem", "Canvas",
                              "RFLineChart", "Page"))
    result = {
        "label": label, "rounds": rounds, "deferred_delete_dispatched": deferred,
        "growth_mb": round(series[-1], 1),
        "slope_mb_per_round": round(slope_mb_per_round(series), 3),
        "live_items_first_round": items[0],
        "live_items_last_round": items[-1],
        "live_item_growth": items[-1] - items[0],
        "series": [round(v, 1) for v in series],
    }
    print("%-34s slope %8.3f MB/round   growth %7.1f MB   items %+d"
          % (label, result["slope_mb_per_round"], result["growth_mb"],
             result["live_item_growth"]))
    return result


def main() -> int:
    app, engine, window = build()

    print("== step 2: harness calibration (all five controls) ==")
    cal = run_calibration(app)
    for key in ("control_a_known_allocation", "control_b_released_allocation",
                "control_c_intentional_leak", "control_e_object_lifecycle"):
        print("  %-32s pass=%s" % (key.replace("control_", ""),
                                   cal[key].get("pass")))
    d = cal["control_d_no_op_noise"]
    print("  %-32s slope %.4f MB/round, p2p %.4f MB"
          % ("d_no_op_noise (the floor)", d["slope_mb_per_round"],
             d["peak_to_peak_mb"]))
    print("  CALIBRATION VERDICT:", cal["verdict"])
    if cal["verdict"] != "PASS":
        print("STOP: the meter is not trustworthy; nothing below would mean "
              "anything")
        return 1
    print("  control_e note:", cal["control_e_object_lifecycle"]
          .get("alive_before_dispatch"), "objects alive before dispatch,",
          cal["control_e_object_lifecycle"].get("alive_after_dispatch"),
          "after")

    nav = navigation(engine)
    print()
    print("== step 1: reproduce, with and without DeferredDelete dispatch ==")
    without = soak(app, window, nav, 8, False, "processEvents only (as filed)")
    with_dd = soak(app, window, nav, 8, True, "+ DeferredDelete dispatched")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step1_reproduce.json").write_text(
        json.dumps({"calibration_verdict": cal["verdict"],
                    "control_d_floor_slope": d["slope_mb_per_round"],
                    "control_e": cal["control_e_object_lifecycle"],
                    "without_deferred_delete": without,
                    "with_deferred_delete": with_dd}, indent=2) + "\n",
        encoding="utf-8")
    print()
    print("written:", OUT / "step1_reproduce.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
