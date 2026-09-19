"""Shared rig for the Analysis R2 memory investigation.

Nothing here decides anything. It provides the app, a settle() with an
explicit and honest definition, and a census of live objects, so every
experiment in this directory measures the same way.
"""
from __future__ import annotations
import gc, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))

from PySide6.QtCore import QUrl, QCoreApplication, QEvent, QObject
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow, QQuickItem  # noqa: F401
from PySide6.QtQml import QQmlComponent
import main as app_main
from harness import memory, delta, slope_mb_per_round  # noqa: F401


def settle(app, rounds: int = 8, deferred: bool = True, collect: bool = True):
    """Turn the event loop.

    `deferred` is the whole point of this function existing. processEvents()
    alone does NOT dispatch DeferredDelete: Qt holds those until the event
    loop unwinds to the level the deleteLater() was issued from, which in a
    scripted harness never happens. A soak that omits this measures objects
    that are already condemned and simply have not been collected yet, and
    reports it as a leak. harness.control_e exists because this project has
    already been caught by exactly that.
    """
    for _ in range(rounds):
        app.processEvents()
        if deferred:
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        time.sleep(0.01)
        app.processEvents()
    if collect:
        gc.collect()


def build(width: int = 1920, height: int = 1080, theme: str = "dark"):
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
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_nav_probe.qml")))
    return probe.create().property("nav")


def census(root, wanted=None):
    """Live QObject counts by metaobject class name, under `root`.

    findChildren walks the QObject tree, so anything still parented is seen.
    An object whose parent was destroyed but which is itself still referenced
    will NOT appear here -- that is deliberate: the two together (census plus
    the allocator) distinguish "still in the tree" from "orphaned but alive".
    """
    counts = {}
    for child in root.findChildren(QObject):
        name = child.metaObject().className()
        counts[name] = counts.get(name, 0) + 1
    if wanted is not None:
        return {k: counts.get(k, 0) for k in wanted}
    return counts


def matching(counts, *needles):
    """Total of every class whose name contains any of `needles`."""
    total = 0
    for name, n in counts.items():
        if any(needle.lower() in name.lower() for needle in needles):
            total += n
    return total
