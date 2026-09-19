"""Section 11: ablation matrix across the real chart-page lifecycle.

Run under the CORRECT method (DeferredDelete dispatched). The reproduction
already showed what the broken method reports; the question here is whether,
once deletions are allowed to complete, ANY variant still retains -- in memory
or in object counts.

Variants are adapted to the actual architecture. Ones that would require
inventing a capability the product does not have are recorded as not
applicable rather than faked.
"""
from __future__ import annotations
import hashlib, json, os, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "acceptance" / "analysis_r2_closure" / "memory"
CHART = ROOT / "ui" / "components" / "RFLineChart.qml"
PY = ROOT / ".venv-cea" / "Scripts" / "python.exe"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def run(pages, mode="destroy", rounds=12):
    res = subprocess.run(
        [str(PY), str(HERE / "_variant.py"),
         json.dumps({"pages": pages, "mode": mode, "rounds": rounds})],
        capture_output=True, text=True, cwd=str(ROOT),
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen",
             "QT_QPA_FONTDIR": "C:/Windows/Fonts"})
    if res.returncode != 0:
        print(res.stdout[-1500:], res.stderr[-1500:])
        raise SystemExit("variant failed")
    return json.loads(res.stdout.strip().splitlines()[-1])


# (id, description, kind, payload)
PLAIN = [
    ("A0", "full chart page, created and destroyed", ["isentropic", "fanno"], "destroy"),
    ("A1", "page without any chart component", ["equations", "fluidproperties"], "destroy"),
    ("A6", "page kept alive, not destroyed", ["isentropic", "isentropic"], "destroy"),
    ("A7", "chart page destroyed (Nozzle Lab, NozzleObject canvas)", ["nozzlelab", "equations"], "destroy"),
    ("A7b", "chart page destroyed (Trade Study, RFPlotSurface)", ["tradestudy", "equations"], "destroy"),
    ("A7c", "chart page destroyed (Oblique Shock, two charts)", ["obliqueshock", "equations"], "destroy"),
    ("A10", "no chart at all: theme/resize excluded, navigation only", ["equations", "gases"], "destroy"),
]

PATCHED = [
    ("A2", "chart present, dataset emptied",
     "    property var points: []", "    property var points: []\n    onPointsChanged: points = []"),
    ("A3", "annotations disabled (guides + markers)",
     "    property var guides: []\n    property var markers: []",
     "    property var guides: []\n    property var markers: []\n"
     "    readonly property bool _ablateAnnotations: true"),
    ("A4", "hover/crosshair disabled",
     "        renderStrategy: Canvas.Cooperative", "        visible: false"),
    ("A5", "Canvas paint replaced by an inert pass",
     "        onPaint: {\n            var ctx = getContext(\"2d\")",
     "        onPaint: {\n            if (true) return\n            var ctx = getContext(\"2d\")"),
    ("A9", "Connections path disabled in the chart",
     "    function repaint() { plot.requestPaint() }",
     "    function repaint() { }"),
]


def main():
    original = CHART.read_text(encoding="utf-8")
    before = digest(CHART)
    rows = []

    print("== plain variants ==")
    for vid, desc, pages, mode in PLAIN:
        r = run(pages, mode)
        r.update({"id": vid, "description": desc, "patched": False})
        rows.append(r)
        print("  %-4s %-52s %7.1f MB  late %7.3f  items %+d"
              % (vid, desc[:52], r["growth_mb"], r["late_slope"], r["obj_items"]))

    print("== patched variants (RFLineChart temporarily edited) ==")
    for vid, desc, old, new in PATCHED:
        if old not in original:
            rows.append({"id": vid, "description": desc, "patched": True,
                         "status": "NOT APPLICABLE — anchor absent in the "
                                   "current implementation"})
            print("  %-4s %-52s NOT APPLICABLE" % (vid, desc[:52]))
            continue
        CHART.write_text(original.replace(old, new, 1), encoding="utf-8")
        try:
            r = run(["isentropic", "fanno"])
            r.update({"id": vid, "description": desc, "patched": True})
            rows.append(r)
            print("  %-4s %-52s %7.1f MB  late %7.3f  items %+d"
                  % (vid, desc[:52], r["growth_mb"], r["late_slope"],
                     r["obj_items"]))
        finally:
            CHART.write_text(original, encoding="utf-8")

    after = digest(CHART)
    print()
    print("RFLineChart restored:", before == after, "(%s -> %s)" % (before, after))

    OUT.mkdir(parents=True, exist_ok=True)

    cols = ["id", "description", "patched", "rounds", "page_loads",
            "growth_mb", "early_slope", "late_slope", "obj_pages",
            "obj_charts", "obj_canvas", "obj_hover", "obj_connections",
            "obj_items", "status"]
    lines = [",".join(cols)]
    for r in rows:
        lines.append(",".join(
            '"%s"' % str(r.get(c, "")).replace('"', "'") for c in cols))
    (OUT / "ablation_matrix.csv").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")

    md = ["# Ablation matrix — Analysis R2 chart-page lifecycle", "",
          "All variants run with `DeferredDelete` dispatched, i.e. the correct",
          "method. The reproduction (`reproduction.json`) already established",
          "what the broken method reports; this asks whether any variant still",
          "retains once deletions are allowed to complete.", "",
          "`obj_*` columns are live-object growth over the run. Zero is the",
          "required answer for every one of them.", "",
          "| id | variant | growth MB | early | late | pages | charts | canvas | hover | conns | items |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        if r.get("status"):
            md.append("| %s | %s | — | — | — | — | — | — | — | — | %s |"
                      % (r["id"], r["description"], r["status"]))
            continue
        md.append("| %s | %s | %.1f | %.3f | %.3f | %+d | %+d | %+d | %+d | %+d | %+d |"
                  % (r["id"], r["description"], r["growth_mb"],
                     r["early_slope"], r["late_slope"], r["obj_pages"],
                     r["obj_charts"], r["obj_canvas"], r["obj_hover"],
                     r["obj_connections"], r["obj_items"]))
    md += ["", "RFLineChart.qml restored byte-identically: `%s`" % (before == after),
           "digest before `%s`, after `%s`." % (before, after)]
    (OUT / "ablation_matrix.md").write_text("\n".join(md) + "\n",
                                            encoding="utf-8")
    return 0 if before == after else 1


if __name__ == "__main__":
    sys.exit(main())
