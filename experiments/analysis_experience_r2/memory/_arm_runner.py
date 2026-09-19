"""One ablation arm, in its own process. Prints a JSON line."""
from __future__ import annotations
import gc, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QTimer
from lifecycle_lab import build, navigation, memory, delta, slope_mb_per_round

cfg = json.loads(sys.argv[1])
PAGES, ROUNDS = cfg["pages"], cfg["rounds"]

app, engine, window = build()
nav = navigation(engine)
st = {"round": 0, "step": 0, "warm": 5, "base": None, "series": []}


def tick():
    key = PAGES[st["step"] % len(PAGES)]
    if key == "__theme__":
        window.setProperty("themeMode",
                           "light" if st["step"] % 2 else "dark")
    elif key == "__resize__":
        window.setProperty("width", 1600 if st["step"] % 2 else 1920)
    else:
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
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
    if st["round"] >= ROUNDS:
        timer.stop()
        app.quit()


timer = QTimer(); timer.setInterval(8)
timer.timeout.connect(tick); timer.start()
app.exec()

s = st["series"]
half = len(s) // 2
print(json.dumps({
    "rounds": ROUNDS,
    "growth_mb": round(s[-1], 1),
    "slope_mb_per_round": round(slope_mb_per_round(s), 3),
    "slope_second_half": round(slope_mb_per_round(s[half:]), 3),
    "series": [round(v, 1) for v in s],
}))
