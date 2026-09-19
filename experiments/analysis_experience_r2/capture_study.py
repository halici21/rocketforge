"""Capture Trade Study tabs with a completed study."""
from __future__ import annotations
import json, pathlib, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
BASE = ROOT / "acceptance" / "analysis_experience_r2_implementation"

from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow  # noqa: F401
from PySide6.QtQml import QQmlComponent
import main as app_main

msgs = []
qInstallMessageHandler(lambda k, c, m: msgs.append(str(m))
                       if k in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg) else None)

app_main.configure_application()
app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
engine, _env = app_main.build_engine(app)
engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
window = engine.rootObjects()[0]


def settle(n=12):
    for _ in range(n):
        app.processEvents(); time.sleep(0.02); app.processEvents()


def find_with_property(obj, name, depth=0):
    if obj is None or depth > 14:
        return None
    try:
        idx = obj.metaObject().indexOfProperty(name)
    except Exception:
        idx = -1
    if idx >= 0 and obj.metaObject().property(idx).isWritable():
        return obj
    for child in obj.children():
        hit = find_with_property(child, name, depth + 1)
        if hit is not None:
            return hit
    return None


probe = QQmlComponent(engine)
probe.setData(
    b'import QtQuick\nimport RocketForge 1.0\nimport "data" as Data\n'
    b'QtObject { property var nav: Data.Navigation; property var study: TradeStudy }',
    QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe3.qml")))
holder = probe.create()
nav = holder.property("nav")
study = holder.property("study")

cfg = json.loads(sys.argv[1])
window.setProperty("width", cfg.get("w", 1920))
window.setProperty("height", cfg.get("h", 1080))
window.setProperty("themeMode", cfg.get("theme", "dark"))
window.setProperty("appMode", "analysis")
settle()

study.addObjective("thrust_coefficient", "maximize")
study.setVariableEnabled("area_ratio", True)
study.setVariableRange("area_ratio", 20.0, 80.0, 5)
study.setVariableRange("oxidiser_fuel_ratio", 2.6, 4.2, 6)
study.runStudy()
for _ in range(900):
    app.processEvents(); time.sleep(0.01)
    if not study.property("busy"):
        break
settle()
print("study complete:", study.property("statusLabel"))

window.setProperty("currentPageIndex", nav.indexOfKey("tradestudy"))
settle()
out = BASE / cfg["outdir"]; out.mkdir(parents=True, exist_ok=True)
page = find_with_property(window, "section")
for shot in cfg["shots"]:
    page.setProperty("section", shot["section"])
    settle()
    window.grabWindow().save(str(out / (shot["name"] + "_" + cfg.get("theme", "dark") + ".png")))
    print("captured", shot["name"])

print(len(msgs), "Qt warnings")
for m in msgs[:8]:
    print("  ", m)
