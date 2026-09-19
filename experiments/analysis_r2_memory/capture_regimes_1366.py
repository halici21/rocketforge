"""Section 34: Nozzle Lab at 1366x768 across real regimes, both themes."""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent
from rig import build, navigation, settle, find_prop, ROOT
import main as app_main

OUT = ROOT / "acceptance" / "analysis_r2_closure" / "nozzle_1366" / "after"
# (label, p_b/p0) -- chosen from the regime thresholds the page itself reports:
# choking onset 0.9372, shock at exit 0.5134, ideal expansion 0.0939.
REGIMES = [("internal_shock", 0.70), ("overexpanded", 0.30),
           ("underexpanded", 0.05), ("unchoked", 0.98)]

for theme in (__import__("sys").argv[1],):
    app, engine, window = build(width=1366, height=768, theme=theme)
    nav = navigation(engine)
    probe = QQmlComponent(engine)
    probe.setData(b'import QtQuick\nimport RocketForge 1.0\n'
                  b'QtObject { property var nozzle: Nozzle }',
                  QUrl.fromLocalFile(str(app_main.UI_DIR / "_nz.qml")))
    nozzle = probe.create().property("nozzle")

    window.setProperty("currentPageIndex", nav.indexOfKey("nozzlelab"))
    settle(app, 10)
    page = find_prop(window, "section")
    page.setProperty("section", 1)
    settle(app, 8)

    for label, pb in REGIMES:
        nozzle.setProperty("backPressureRatio", pb)
        settle(app, 12)
        OUT.mkdir(parents=True, exist_ok=True)
        window.grabWindow().save(str(OUT / ("regime_%s_%s.png" % (label, theme))))
        print("captured %-16s p_b/p0=%.2f  %s" % (label, pb, theme))
    app.quit()
