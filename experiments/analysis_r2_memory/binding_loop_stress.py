"""A binding loop always warns. Cross the compact breakpoint hard and listen."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from PySide6.QtCore import QtMsgType, qInstallMessageHandler
MSGS = []
qInstallMessageHandler(lambda k, c, m: MSGS.append(str(m))
                       if k in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)
from rig import build, navigation, settle, find_prop  # noqa: E402

app, engine, window = build(width=1920, height=1080)
nav = navigation(engine)
window.setProperty("currentPageIndex", nav.indexOfKey("nozzlelab"))
settle(app, 10)
find_prop(window, "section").setProperty("section", 1)
settle(app, 10)

for i in range(60):
    h = 768 if i % 2 else 1080
    window.setProperty("width", 1366 if i % 2 else 1920)
    window.setProperty("height", h)
    settle(app, 4)
# And straddle the 620 boundary one pixel at a time.
for h in range(612, 630):
    window.setProperty("height", h)
    settle(app, 3)

loops = [m for m in MSGS if "binding loop" in m.lower()]
print("resize cycles: 60 + 18 single-pixel steps across the 620 breakpoint")
print("total Qt warnings :", len(MSGS))
print("binding loops     :", len(loops))
for m in MSGS[:6]:
    print("   ", m[:140])
sys.exit(1 if loops else 0)
