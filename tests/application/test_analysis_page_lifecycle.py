"""Analysis pages are destroyed when you navigate away from them.

This exists because the claim was once made, loudly and with numbers, that
they are not. A soak reported ~28 MB retained per chart-page load and ~2.8 GB
over twelve rounds. All of it was an artifact of the measuring script driving
the loop with ``processEvents()`` alone: Qt delivers ``DeferredDelete`` when
the event loop unwinds to the level that posted it, so a scripted loop that
never unwinds never lets ``deleteLater()`` finish, and every object correctly
scheduled for destruction is still there to be counted.

``experiments/qml_memory/harness.settle`` already documented exactly this trap.
The soak did not use it. So the lesson is encoded here instead of in a comment:
a test fails if pages stop being destroyed, and -- just as importantly -- the
negative control below fails if this test ever stops being able to tell.
"""

from __future__ import annotations

import pathlib
import sys

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QUrl

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

#: Perfect-gas workspaces only, so this runs in the base environment with no
#: chemistry provider installed.
CHART_PAGES = ["isentropic", "fanno", "nozzlelab", "obliqueshock"]


def _turn(app, *, deferred: bool, rounds: int = 6) -> None:
    """Turn the event loop, optionally completing deferred deletions."""
    for _ in range(rounds):
        app.processEvents()
        if deferred:
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()


def _page_items(window) -> int:
    """Live QQuickItems under the window, as a proxy for page instances.

    findChildren only walks the QObject tree, so an item still parented into
    the scene is counted and one that has been destroyed is not -- which is
    precisely the distinction under test.
    """
    return sum(1 for child in window.findChildren(QObject)
               if "QQuickItem" in child.metaObject().className()
               or "Canvas" in child.metaObject().className())


@pytest.fixture(scope="module")
def analysis_window(qt_app):
    from PySide6.QtQuick import QQuickWindow  # noqa: F401  (registers the type)
    import main as app_main

    app_main.configure_application()
    engine, _env = app_main.build_engine(qt_app)
    engine.load(QUrl.fromLocalFile(str(app_main.UI_DIR / "Main.qml")))
    roots = engine.rootObjects()
    if not roots:
        pytest.skip("the QML scene did not load in this environment")
    window = roots[0]
    window.setProperty("width", 1600)
    window.setProperty("height", 900)
    window.setProperty("appMode", "analysis")
    _turn(qt_app, deferred=True)

    from PySide6.QtQml import QQmlComponent
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport "data" as Data\n'
                  b'QtObject { property var nav: Data.Navigation }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_lifecycle.qml")))
    nav = probe.create().property("nav")
    yield qt_app, window, nav


def _cycle(app, window, nav, *, deferred: bool, rounds: int) -> int:
    """Navigate `rounds` times through the chart pages; return item growth."""
    for key in CHART_PAGES:                       # warm every page once
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        _turn(app, deferred=True)

    baseline = _page_items(window)
    for _ in range(rounds):
        for key in CHART_PAGES:
            window.setProperty("currentPageIndex", nav.indexOfKey(key))
            _turn(app, deferred=deferred)
    _turn(app, deferred=True)                     # always settle before counting
    return _page_items(window) - baseline


def test_navigating_away_destroys_the_page(analysis_window):
    """The invariant: repeated navigation does not accumulate page instances."""
    app, window, nav = analysis_window
    growth = _cycle(app, window, nav, deferred=True, rounds=6)
    assert growth <= 0, (
        f"{growth} live items accumulated over 6 rounds through "
        f"{len(CHART_PAGES)} chart pages; pages are not being destroyed"
    )


def test_the_check_can_actually_detect_retention(analysis_window):
    """Negative control: without DeferredDelete, retention must be visible.

    If this ever stops failing to reclaim, the assertion above has become
    vacuous -- it would be passing because nothing is ever counted, not
    because nothing is ever retained.
    """
    app, window, nav = analysis_window

    for key in CHART_PAGES:
        window.setProperty("currentPageIndex", nav.indexOfKey(key))
        _turn(app, deferred=True)
    baseline = _page_items(window)

    for _ in range(3):
        for key in CHART_PAGES:
            window.setProperty("currentPageIndex", nav.indexOfKey(key))
            _turn(app, deferred=False)
    undispatched = _page_items(window) - baseline

    assert undispatched > 0, (
        "processEvents() alone left nothing pending, so this test can no "
        "longer distinguish a destroyed page from a retained one"
    )

    _turn(app, deferred=True, rounds=12)
    assert _page_items(window) - baseline <= 0, (
        "the objects pending above were never reclaimed once DeferredDelete "
        "was dispatched -- that would be a real leak"
    )
