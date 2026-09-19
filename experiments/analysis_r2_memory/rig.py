"""Shared rig for the closure investigation: app, settle, per-class census."""
from __future__ import annotations
import gc, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))

from PySide6.QtCore import QUrl, QCoreApplication, QEvent, QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow  # noqa: F401
from PySide6.QtQml import QQmlComponent
import main as app_main
from harness import memory, delta, slope_mb_per_round  # noqa: F401

#: The object classes section 9 asks to be counted, by metaobject name
#: fragment. QML-defined types report as e.g. RFLineChart_QMLTYPE_42.
TRACKED = {
    "workspace_pages":   ("Page_QMLTYPE", "PageQMLTYPE"),
    "RFLineChart":       ("RFLineChart",),
    "RFPlotSurface":     ("RFPlotSurface",),
    "Canvas":            ("QQuickCanvasItem",),
    "HoverHandler":      ("QQuickHoverHandler",),
    "TapHandler":        ("QQuickTapHandler",),
    "Connections":       ("QQmlConnections",),
    "Loader":            ("QQuickLoader",),
    "Repeater":          ("QQuickRepeater",),
    "ListView":          ("QQuickListView",),
    "all_quick_items":   ("QQuickItem",),
}


def settle(app, rounds: int = 8, deferred: bool = True, collect: bool = False):
    """Turn the loop. `deferred=False` reproduces the original broken method."""
    for _ in range(rounds):
        app.processEvents()
        if deferred:
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        time.sleep(0.005)
        app.processEvents()
    if collect:
        gc.collect()


def build(width=1920, height=1080, theme="dark"):
    app_main.configure_application()
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    engine, _env = app_main.build_engine(app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    window = engine.rootObjects()[0]
    window.setProperty("width", width)
    window.setProperty("height", height)
    window.setProperty("themeMode", theme)
    window.setProperty("appMode", "analysis")
    settle(app)
    return app, engine, window


def navigation(engine):
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport "data" as Data\n'
                  b'QtObject { property var nav: Data.Navigation }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_rig_nav.qml")))
    return probe.create().property("nav")


def census(window):
    """Per-class live counts under the window.

    NOTE: findChildren creates a Python wrapper per returned object, so this
    must never be called inside a run whose purpose is to measure Python-side
    wrapper growth. It is for object-lifetime questions only.
    """
    raw = {}
    for child in window.findChildren(QObject):
        name = child.metaObject().className()
        raw[name] = raw.get(name, 0) + 1
    out = {}
    for label, needles in TRACKED.items():
        out[label] = sum(n for cls, n in raw.items()
                         if any(needle in cls for needle in needles))
    out["_distinct_classes"] = len(raw)
    out["_total_qobjects"] = sum(raw.values())
    return out


def find_prop(obj, name, depth=0):
    if obj is None or depth > 16:
        return None
    try:
        idx = obj.metaObject().indexOfProperty(name)
    except Exception:
        idx = -1
    if idx >= 0 and obj.metaObject().property(idx).isWritable():
        return obj
    for c in obj.children():
        hit = find_prop(c, name, depth + 1)
        if hit is not None:
            return hit
    return None
