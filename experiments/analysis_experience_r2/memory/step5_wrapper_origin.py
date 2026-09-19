"""Is the PySide wrapper growth the product, or my own instrument?

step4 sampled with census(), which calls findChildren(QObject) -- and that
call CREATES a Python wrapper for every QObject it returns. 13 samples over a
tree of ~2000 objects is ~26000 wrappers, against the ~29700 observed. That is
close enough that the instrument has to be ruled out before the product is
accused.

Three arms, identical navigation, differing only in what is measured:
  A  no census at any point
  B  census every sample (what step4 did)
  C  census every sample, then explicitly drop the references and collect
"""
from __future__ import annotations
import gc, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QTimer, QObject
from lifecycle_lab import build, navigation, memory, delta, ROOT

OUT = ROOT / "acceptance" / "analysis_experience_r2_implementation" / "memory"
PAGES = ["isentropic", "fanno", "nozzlelab", "obliqueshock", "tradestudy"]
ROUNDS = 40


def wrappers():
    return sum(1 for o in gc.get_objects() if isinstance(o, QObject))


def run(arm, window, nav, app):
    st = {"round": 0, "step": 0, "warm": 4, "first": None, "last": None}

    def tick():
        window.setProperty("currentPageIndex",
                           nav.indexOfKey(PAGES[st["step"] % len(PAGES)]))
        st["step"] += 1
        if st["step"] % len(PAGES):
            return
        if st["warm"] > 0:
            st["warm"] -= 1
            return
        st["round"] += 1

        if arm in ("B", "C"):
            found = window.findChildren(QObject)
            n = len(found)
            if arm == "C":
                del found
                gc.collect()
            else:
                del n
        if st["round"] in (1, ROUNDS):
            gc.collect()
            value = wrappers()
            if st["round"] == 1:
                st["first"] = value
            else:
                st["last"] = value
        if st["round"] >= ROUNDS:
            timer.stop()
            app.quit()

    timer = QTimer(); timer.setInterval(8)
    timer.timeout.connect(tick); timer.start()
    app.exec()
    return st


def main() -> int:
    app, engine, window = build()
    nav = navigation(engine)

    arms = {}
    for arm, label in (("A", "no census at all"),
                       ("B", "census, references dropped implicitly"),
                       ("C", "census, references dropped + gc.collect()")):
        gc.collect()
        st = run(arm, window, nav, app)
        grew = st["last"] - st["first"]
        arms[arm] = {"label": label, "first": st["first"], "last": st["last"],
                     "growth": grew,
                     "per_page_load": round(grew / (ROUNDS * len(PAGES)), 2)}
        print("  %s  %-44s %6d -> %6d   %+7d  (%.2f/page load)"
              % (arm, label, st["first"], st["last"], grew,
                 arms[arm]["per_page_load"]))

    instrument_driven = arms["A"]["growth"] < arms["B"]["growth"] * 0.2
    print()
    print("VERDICT:", "the wrapper growth is the INSTRUMENT (census), not the "
          "product" if instrument_driven
          else "wrapper growth persists WITHOUT census -- product-side")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step5_wrapper_origin.json").write_text(
        json.dumps({"rounds": ROUNDS, "pages_per_round": len(PAGES),
                    "arms": arms,
                    "instrument_driven": instrument_driven}, indent=2) + "\n",
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
