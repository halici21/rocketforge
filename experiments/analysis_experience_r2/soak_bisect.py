"""SUPERSEDED — this file measured with a broken settle().

It defined its own event-loop turn from processEvents() alone, which never
dispatches DeferredDelete, so every page Qt had correctly scheduled for
destruction was still counted as live. That is where the reported
~171-227 MB/round came from. It was an artifact of this file, not a property
of the product.

The authoritative measurements live in experiments/analysis_experience_r2/
memory/, which drive navigation from a QTimer inside app.exec(). Kept only so
the false result has a traceable origin; do not cite its numbers.
"""
from __future__ import annotations
import pathlib, sys, time
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow  # noqa: F401
from PySide6.QtQml import QQmlComponent
import main as app_main
from harness import memory, slope_mb_per_round


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


app_main.configure_application()
app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
engine, _env = app_main.build_engine(app)
engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
window = engine.rootObjects()[0]


def settle(n=6):
    # Corrected: harness.settle dispatches DeferredDelete.
    from harness import settle as _settle
    _settle(app, n)


probe = QQmlComponent(engine)
probe.setData(b'import QtQuick\nimport "data" as Data\n'
              b'QtObject { property var nav: Data.Navigation }',
              QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe_bis.qml")))
nav = probe.create().property("nav")
window.setProperty("width", 1920); window.setProperty("height", 1080)
window.setProperty("themeMode", "dark"); window.setProperty("appMode", "analysis")
settle()

PAGES = ["isentropic", "massflow", "normalshock", "prandtlmeyer", "fanno",
         "rayleigh", "nozzlelab", "obliqueshock", "tradestudy"]


def goto(key):
    window.setProperty("currentPageIndex", nav.indexOfKey(key))
    settle(4)


def drive_pages():
    for key in PAGES:
        goto(key)


def drive_sections():
    goto("isentropic")
    page = find_with_property(window, "section")
    for s in (0, 1, 2, 0):
        page.setProperty("section", s); settle(3)


def drive_quantity():
    goto("isentropic")
    q = find_with_property(window, "quantityIndex")
    for i in (0, 1, 2, 3, 0):
        q.setProperty("quantityIndex", i); settle(3)


def drive_theme():
    window.setProperty("themeMode", "light"); settle(4)
    window.setProperty("themeMode", "dark"); settle(4)


def drive_idle():
    settle(12)


SCENARIOS = [("idle (control)", drive_idle), ("page switching", drive_pages),
             ("section switching", drive_sections),
             ("chart quantity", drive_quantity), ("theme flip", drive_theme)]

for label, fn in SCENARIOS:
    for _ in range(2):
        fn()
    series = []
    for _ in range(6):
        fn()
        series.append(memory()["private_mb"])
    print("%-20s slope %8.2f MB/round   (end %.0f MB)"
          % (label, slope_mb_per_round(series), series[-1]))
