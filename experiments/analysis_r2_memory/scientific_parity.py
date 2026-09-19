"""Section 37: field-level scientific parity across the responsive change.

The risk this closure actually introduces is that restructuring the Solution
for compact height changes what it says. So the same solved state is read at
1366 (compact grammar) and 1920 (roomy grammar) and compared field by field.
Any difference would be the defect.

Also compares every other workspace's published results across the same
resize, because the breakpoint is global.
"""
from __future__ import annotations
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent
from rig import build, navigation, settle, find_prop, ROOT
import main as app_main

OUT = ROOT / "acceptance" / "analysis_r2_closure" / "parity"

app, engine, window = build(width=1920, height=1080)
nav = navigation(engine)
probe = QQmlComponent(engine)
probe.setData(
    b'import QtQuick\nimport RocketForge 1.0\n'
    b'QtObject {\n'
    b'  property var nozzle: Nozzle\n  property var isen: Isentropic\n'
    b'  property var oblique: ObliqueShock\n  property var fluid: FluidProperties\n'
    b'  property var line: Line\n  property var study: TradeStudy\n'
    b'  property var perf: RocketPerformance\n}',
    QUrl.fromLocalFile(str(app_main.UI_DIR / "_sci.qml")))
h = probe.create()

h.property("fluid").calculate()
h.property("line").calculate()
h.property("perf").calculate()
h.property("oblique").setDeflectionAndSolve(10.0)
settle(app, 14)


def snapshot():
    """Every published result row, from every workspace, as text."""
    out = {}
    # Controllers expose their rows under different names; ask for each in
    # turn rather than silently skipping a workspace whose name differs and
    # then claiming it was covered.
    CANDIDATES = ("results", "resultRows", "resultGroups")
    for name in ("nozzle", "isen", "oblique", "fluid", "line", "perf"):
        ctrl = h.property(name)
        rows = None
        for prop in CANDIDATES:
            rows = ctrl.property(prop)
            if rows:
                break
        if not rows:
            out[name] = {"_unavailable": "no result rows under " + str(CANDIDATES)}
            continue
        if rows and isinstance(rows[0], dict) and "rows" in rows[0]:
            rows = [r for g in rows for r in (g.get("rows") or [])]
        out[name] = [
            {"key": r.get("key"), "label": r.get("label"),
             "value": r.get("value"), "unit": r.get("unit"),
             "available": r.get("available")}
            for r in rows]
    # Chart series for the pages whose charts were restructured.
    isen = h.property("isen")
    cols = [c["key"] for c in isen.property("tableColumns") if c["key"] != "mach"]
    out["_isentropic_series"] = {
        k: [[round(p["x"], 12), round(p["y"], 12)]
            for p in isen.chartSeries(k)[:40]] for k in cols}
    nz = h.property("nozzle")
    out["_nozzle_contour"] = [
        {"label": part["label"],
         "points": [[round(p["x"], 12), round(p["y"], 12)]
                    for p in part["points"][:40]]}
        for part in nz.contourSeries()]
    out["_nozzle_markers"] = [dict(m) for m in nz.markers()]
    study = h.property("study")
    if study.property("hasResult"):
        out["_study_pareto"] = [
            {"index": r.get("index"), "pareto": r.get("pareto"),
             "feasible": r.get("feasible"), "score": r.get("score")}
            for r in (study.property("pointRows") or [])]
    return out


# Roomy, then compact, then back -- the resize is what this tests.
window.setProperty("currentPageIndex", nav.indexOfKey("nozzlelab"))
settle(app, 10)
page = find_prop(window, "section")
page.setProperty("section", 1)
settle(app, 10)

roomy = snapshot()
window.setProperty("width", 1366); window.setProperty("height", 768)
settle(app, 14)
compact = snapshot()
window.setProperty("width", 1920); window.setProperty("height", 1080)
settle(app, 14)
back = snapshot()

def diff(a, b, path="", acc=None):
    acc = [] if acc is None else acc
    if type(a) is not type(b):
        acc.append({"path": path, "roomy": str(a)[:80], "compact": str(b)[:80]})
        return acc
    if isinstance(a, dict):
        for k in set(a) | set(b):
            diff(a.get(k), b.get(k), path + "/" + str(k), acc)
    elif isinstance(a, list):
        if len(a) != len(b):
            acc.append({"path": path, "roomy": "len %d" % len(a),
                        "compact": "len %d" % len(b)})
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                diff(x, y, path + "[%d]" % i, acc)
    elif a != b:
        acc.append({"path": path, "roomy": str(a)[:80], "compact": str(b)[:80]})
    return acc


d1 = diff(roomy, compact)
d2 = diff(roomy, back)
fields = sum(len(v) if isinstance(v, list) else 1 for v in roomy.values())

# Negative control: the comparison must be able to see a change.
control = json.loads(json.dumps(roomy))
control["nozzle"][0]["value"] = "CHANGED"
control_diffs = diff(roomy, control)

report = {
    "question": "does the responsive restructure change any published value",
    "workspaces": sorted(k for k in roomy if not k.startswith("_")),
    "top_level_fields_compared": fields,
    "roomy_vs_compact_differences": d1,
    "roomy_vs_restored_differences": d2,
    "negative_control_differences_detected": len(control_diffs),
    "verdict": "PASS" if not d1 and not d2 and control_diffs else "FAIL",
}
print("workspaces compared      :", ", ".join(report["workspaces"]))
print("roomy vs compact diffs   :", len(d1))
print("roomy vs restored diffs  :", len(d2))
print("negative control         :", len(control_diffs), "difference(s) detected")
print("VERDICT:", report["verdict"])
for x in d1[:8]:
    print("   ", x)

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "scientific_parity.json").write_text(json.dumps(report, indent=2) + "\n",
                                            encoding="utf-8")
sys.exit(0 if report["verdict"] == "PASS" else 1)
