"""Section 40: capture every Qt/QML warning across a heavy navigation session.

Nothing is suppressed; the handler records everything at warning level or
above and the categories are reported verbatim.
"""
from __future__ import annotations
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QtMsgType, qInstallMessageHandler, QTimer
MESSAGES = []


def handler(kind, ctx, msg):
    if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg,
                QtMsgType.QtFatalMsg):
        MESSAGES.append({"level": str(kind).split(".")[-1], "text": str(msg)})


qInstallMessageHandler(handler)

from rig import build, navigation, ROOT  # noqa: E402

OUT = ROOT / "acceptance" / "analysis_r2_closure" / "memory"
PAGES = ["isentropic", "obliqueshock", "nozzlelab", "thermochem",
         "performance", "tradestudy", "fluidproperties", "line", "equations"]

app, engine, window = build()
nav = navigation(engine)
st = {"i": 0}


def tick():
    window.setProperty("currentPageIndex", nav.indexOfKey(PAGES[st["i"] % len(PAGES)]))
    if st["i"] % 9 == 0:
        window.setProperty("themeMode", "light" if st["i"] % 18 else "dark")
    if st["i"] % 11 == 0:
        window.setProperty("width", 1366 if st["i"] % 22 else 1920)
        window.setProperty("height", 768 if st["i"] % 22 else 1080)
    st["i"] += 1
    if st["i"] >= 180:
        timer.stop(); app.quit()


timer = QTimer(); timer.setInterval(4)
timer.timeout.connect(tick); timer.start()
app.exec()

unique = {}
for m in MESSAGES:
    unique[m["text"]] = unique.get(m["text"], 0) + 1
print("navigation events driven: 180")
print("total warnings:", len(MESSAGES), " unique:", len(unique))
for text, n in list(unique.items())[:20]:
    print("  x%-4d %s" % (n, text[:150]))

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "qt_warnings.json").write_text(json.dumps(
    {"navigation_events": 180, "total": len(MESSAGES),
     "unique": len(unique),
     "messages": [{"count": n, "text": t} for t, n in unique.items()],
     "suppression": "none -- handler records all warning/critical/fatal"},
    indent=2) + "\n", encoding="utf-8")
sys.exit(0 if not MESSAGES else 1)
