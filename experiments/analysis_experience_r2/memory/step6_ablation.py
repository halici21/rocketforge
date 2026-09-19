"""Step 4: ablation across the real chart-page path, real event loop.

Every arm drives the same navigation under app.exec() and measures only the
allocator. No census is taken inside a run -- step5 proved findChildren is
itself a wrapper factory, so an instrument that walks the tree cannot be used
to judge the tree.

Arms marked (patched) temporarily edit product QML, measure, and restore. The
restore is verified by checksum, not by assumption.
"""
from __future__ import annotations
import gc, hashlib, json, shutil, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "acceptance" / "analysis_experience_r2_implementation" / "memory"
CHART = ROOT / "ui" / "components" / "RFLineChart.qml"
PY = ROOT / ".venv-cea" / "Scripts" / "python.exe"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def run_arm(pages, rounds=20):
    """Each arm runs in its own process: one QGuiApplication per run, and no
    state carried between arms."""
    res = subprocess.run(
        [str(PY), str(HERE / "_arm_runner.py"), json.dumps(
            {"pages": pages, "rounds": rounds})],
        capture_output=True, text=True, cwd=str(ROOT),
        env={**__import__("os").environ,
             "QT_QPA_PLATFORM": "offscreen",
             "QT_QPA_FONTDIR": "C:/Windows/Fonts"})
    if res.returncode != 0:
        print(res.stdout[-2000:]); print(res.stderr[-2000:])
        raise SystemExit("arm failed")
    return json.loads(res.stdout.strip().splitlines()[-1])


PATCHES = {
    "hover/crosshair disabled": (
        "        renderStrategy: Canvas.Cooperative",
        "        visible: false  // ablation"),
    "annotations disabled": (
        "            // the simple vertical reference (M = 1, usually)",
        "            if (true) { ctx.restore ? 0 : 0 } else\n"
        "            // the simple vertical reference (M = 1, usually)"),
    "Canvas paint disabled": (
        "        onPaint: {\n            var ctx = getContext(\"2d\")\n"
        "            ctx.reset()\n            ctx.clearRect(0, 0, width, height)\n"
        "\n            var all = root.allSeries",
        "        onPaint: {\n            if (true) return\n"
        "            var ctx = getContext(\"2d\")\n"
        "            ctx.reset()\n            ctx.clearRect(0, 0, width, height)\n"
        "\n            var all = root.allSeries"),
}


def main():
    original = CHART.read_text(encoding="utf-8")
    before_digest = digest(CHART)
    arms = {}

    plain = [
        ("full chart pages (isentropic+fanno)", ["isentropic", "fanno"]),
        ("chart removed (non-chart pages)", ["equations", "fluidproperties"]),
        ("page kept alive (same page)", ["isentropic", "isentropic"]),
        ("Nozzle Lab (NozzleObject canvas)", ["nozzlelab", "isentropic"]),
        ("Trade Study (RFPlotSurface)", ["tradestudy", "isentropic"]),
        ("Oblique Shock (two charts)", ["obliqueshock", "isentropic"]),
        ("theme flip only", ["__theme__", "__theme__"]),
        ("resize only", ["__resize__", "__resize__"]),
    ]
    print("== unpatched arms ==")
    for label, pages in plain:
        arms[label] = run_arm(pages)
        print("  %-38s slope %7.3f  2nd-half %7.3f  growth %6.1f MB"
              % (label, arms[label]["slope_mb_per_round"],
                 arms[label]["slope_second_half"], arms[label]["growth_mb"]))

    print("== patched arms (product QML temporarily edited) ==")
    for label, (old, new) in PATCHES.items():
        if old not in original:
            print("  %-38s SKIPPED (anchor not found)" % label)
            continue
        CHART.write_text(original.replace(old, new, 1), encoding="utf-8")
        try:
            arms[label] = run_arm(["isentropic", "fanno"])
            print("  %-38s slope %7.3f  2nd-half %7.3f  growth %6.1f MB"
                  % (label, arms[label]["slope_mb_per_round"],
                     arms[label]["slope_second_half"], arms[label]["growth_mb"]))
        finally:
            CHART.write_text(original, encoding="utf-8")

    after_digest = digest(CHART)
    restored = before_digest == after_digest
    print()
    print("RFLineChart.qml restored exactly:", restored,
          "(%s -> %s)" % (before_digest, after_digest))

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step6_ablation.json").write_text(
        json.dumps({"arms": arms, "source_restored": restored,
                    "digest_before": before_digest,
                    "digest_after": after_digest}, indent=2) + "\n",
        encoding="utf-8")
    return 0 if restored else 1


if __name__ == "__main__":
    sys.exit(main())
