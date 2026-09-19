"""Section 26: reproduce and MEASURE the 1366x768 Solution clip.

No eyeballing. The real geometry of every participant is read off the live
scene so the fix is designed against numbers.
"""
from __future__ import annotations
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QObject
from rig import build, navigation, settle, find_prop, ROOT

OUT = ROOT / "acceptance" / "analysis_r2_closure" / "nozzle_1366"


def walk(obj, depth=0, acc=None, maxdepth=22):
    acc = [] if acc is None else acc
    if obj is None or depth > maxdepth:
        return acc
    cls = obj.metaObject().className()
    try:
        h = obj.property("height"); w = obj.property("width")
        y = obj.property("y"); vis = obj.property("visible")
    except Exception:
        h = w = y = vis = None
    if h is not None:
        acc.append({"depth": depth, "class": cls, "w": w, "h": h, "y": y,
                    "visible": vis})
    for c in obj.children():
        walk(c, depth + 1, acc, maxdepth)
    return acc


def main() -> int:
    app, engine, window = build(width=1366, height=768)
    nav = navigation(engine)
    window.setProperty("currentPageIndex", nav.indexOfKey("nozzlelab"))
    settle(app, 10)
    page = find_prop(window, "section")
    page.setProperty("section", 1)          # Operating point
    settle(app, 12)

    items = walk(window)
    # The Solution panel and its immediate content.
    panels = [i for i in items if "RFPanel" in i["class"] and i["visible"]]
    grids = [i for i in items if "RowLayout" in i["class"] or "GridLayout" in i["class"]]
    columns = [i for i in items if "ColumnLayout" in i["class"] and i["visible"]]

    report = {
        "viewport": {"width": 1366, "height": 768},
        "page": "Nozzle Lab / Operating point",
        "visible_panels": sorted(
            [{"class": p["class"], "w": round(p["w"] or 0),
              "h": round(p["h"] or 0), "y": round(p["y"] or 0)}
             for p in panels], key=lambda d: d["y"])[:12],
        "tallest_columns": sorted(
            [{"class": c["class"], "h": round(c["h"] or 0)} for c in columns],
            key=lambda d: -d["h"])[:8],
        "total_items_measured": len(items),
    }

    print("viewport 1366x768, Nozzle Lab / Operating point")
    print("  visible panels (top to bottom):")
    for p in report["visible_panels"]:
        print("    y=%-5d h=%-5d w=%-5d %s" % (p["y"], p["h"], p["w"], p["class"][:44]))
    print("  tallest columns:")
    for c in report["tallest_columns"]:
        print("    h=%-5d %s" % (c["h"], c["class"][:50]))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "layout_measurements.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
