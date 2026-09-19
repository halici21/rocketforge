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
              QUrl.fromLocalFile(str(app_main.UI_DIR / "_probe_pk.qml")))
nav = probe.create().property("nav")
window.setProperty("width", 1920); window.setProperty("height", 1080)
window.setProperty("themeMode", "dark"); window.setProperty("appMode", "analysis")
settle()


def cycle(keys):
    def run():
        for k in keys:
            window.setProperty("currentPageIndex", nav.indexOfKey(k))
            settle(4)
    return run


CASES = [
    # Two chart-bearing workspaces, landing on their relation charts.
    ("chart pages", cycle(["isentropic", "fanno"])),
    # Two pages with no RFLineChart at all.
    ("non-chart pages", cycle(["equations", "fluidproperties"])),
    # A single page re-selected: the Loader source does not change, so
    # nothing is created or destroyed. The control for the control.
    ("same page repeatedly", cycle(["isentropic", "isentropic"])),
]

for label, fn in CASES:
    for _ in range(3):
        fn()
    series = []
    for _ in range(8):
        fn()
        series.append(memory()["private_mb"])
    print("%-24s slope %8.2f MB/round   (end %.0f MB)"
          % (label, slope_mb_per_round(series), series[-1]))
