"""Section 29: launch the real application and walk every workspace.

Driven by a QTimer inside app.exec() -- a real event loop, the same one a user
gets. Every Qt warning is recorded; nothing is suppressed.
"""
from __future__ import annotations
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QUrl, QTimer, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow  # noqa: F401
from PySide6.QtQml import QQmlComponent
import main as app_main

MSGS = []
qInstallMessageHandler(lambda k, c, m: MSGS.append((str(k).split(".")[-1], str(m)))
                       if k in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg,
                                QtMsgType.QtFatalMsg) else None)

app_main.configure_application()
app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
engine, _env = app_main.build_engine(app)
engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
roots = engine.rootObjects()
if not roots:
    print("FAIL: the application did not load"); sys.exit(1)
window = roots[0]

probe = QQmlComponent(engine)
probe.setData(b'import QtQuick\nimport "data" as Data\n'
              b'QtObject { property var nav: Data.Navigation }',
              QUrl.fromLocalFile(str(app_main.UI_DIR / "_smoke.qml")))
nav = probe.create().property("nav")

WALK = ["home", "isentropic", "massflow", "normalshock", "obliqueshock",
        "prandtlmeyer", "fanno", "rayleigh", "nozzlelab", "thermochem",
        "performance", "tradestudy", "fluidproperties", "line", "equations"]
state = {"i": 0, "visited": [], "pages": 0}


def tick():
    i = state["i"]
    if i < len(WALK):
        key = WALK[i]
        idx = nav.indexOfKey(key)
        if idx < 0:
            print("  !! unreachable route:", key)
        else:
            window.setProperty("appMode", "analysis")
            window.setProperty("currentPageIndex", idx)
            state["visited"].append(key)
            state["pages"] += 1
    elif i == len(WALK):
        window.setProperty("appMode", "engine")       # Engine Design
    elif i == len(WALK) + 1:
        window.setProperty("themeMode", "light")
    elif i == len(WALK) + 2:
        window.setProperty("themeMode", "dark")
    elif i == len(WALK) + 3:
        window.setProperty("width", 1366); window.setProperty("height", 768)
    elif i == len(WALK) + 4:
        window.setProperty("width", 1920); window.setProperty("height", 1080)
    else:
        timer.stop(); app.quit(); return
    state["i"] += 1


timer = QTimer(); timer.setInterval(120)
timer.timeout.connect(tick); timer.start()
app.exec()

print("workspaces visited :", state["pages"], "/", len(WALK))
print("  ", ", ".join(state["visited"]))
print("engine mode, theme cycle, 1366/1920 resize: exercised")
print("Qt warnings:", len(MSGS))
for level, m in MSGS[:10]:
    print("   [%s] %s" % (level, m[:150]))
sys.exit(1 if MSGS or state["pages"] != len(WALK) else 0)
