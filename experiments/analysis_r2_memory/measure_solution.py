"""Exact heights inside the Solution panel at 1366x768."""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from PySide6.QtCore import QObject
from rig import build, navigation, settle, find_prop

app, engine, window = build(width=1366, height=768)
nav = navigation(engine)
window.setProperty("currentPageIndex", nav.indexOfKey("nozzlelab"))
settle(app, 10)
find_prop(window, "section").setProperty("section", 1)
settle(app, 12)


def find_solution_panel(root):
    for c in root.findChildren(QObject):
        if "RFPanel" in c.metaObject().className():
            if str(c.property("title")) == "Solution":
                return c
    return None


panel = find_solution_panel(window)
print("Solution panel : h=%.0f w=%.0f" % (panel.property("height"),
                                          panel.property("width")))

# Its direct content: the hero ColumnLayout and the groups RowLayout.
for child in panel.findChildren(QObject):
    cls = child.metaObject().className()
    h = child.property("height")
    if h is None:
        continue
    if "ColumnLayout" in cls or "RowLayout" in cls or "GridLayout" in cls:
        depth_marker = ""
        print("  %-22s h=%-7.1f w=%-7.1f y=%-6.1f"
              % (cls[:22], h, child.property("width") or 0,
                 child.property("y") or 0))
