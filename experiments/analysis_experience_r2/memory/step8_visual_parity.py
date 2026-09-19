"""Visual-preservation gate: re-capture, then compare pixels with the
user-approved images.

No product file was edited in this investigation -- the one file that was
temporarily patched for ablation (RFLineChart.qml) was restored and its
checksum verified. But "I did not change it" is an assertion, and the gate the
user asked for is evidence. So the approved captures are re-rendered from the
current tree and compared pixel by pixel with QImage.
"""
from __future__ import annotations
import json, sys, pathlib, subprocess, os

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ACC = ROOT / "acceptance" / "analysis_experience_r2_implementation"
APPROVED = ACC / "user_review"
FRESH = ACC / "memory" / "revalidation"
PY = ROOT / ".venv-cea" / "Scripts" / "python.exe"

# approved image -> (capture script config)
TARGETS = {
    "01_isentropic_relation_dark.png": ("capture_impl.py",
        {"targets": ["isentropic"], "outdir": "memory/revalidation"}),
    "03_nozzlelab_regime_map_dark.png": ("capture_impl.py",
        {"targets": ["nozzlelab"], "outdir": "memory/revalidation"}),
    "04_obliqueshock_calculator_dark.png": ("capture_impl.py",
        {"targets": ["obliqueshock"], "outdir": "memory/revalidation"}),
    "08_fluidproperties_dark.png": ("capture_impl.py",
        {"targets": ["fluidproperties"], "outdir": "memory/revalidation"}),
}
RENAME = {
    "01_isentropic_relation_dark.png": "isentropic_dark_1920x1080.png",
    "03_nozzlelab_regime_map_dark.png": "nozzlelab_dark_1920x1080.png",
    "04_obliqueshock_calculator_dark.png": "obliqueshock_dark_1920x1080.png",
    "08_fluidproperties_dark.png": "fluidproperties_dark_1920x1080.png",
}


def compare(a: pathlib.Path, b: pathlib.Path):
    """Pixel comparison via QImage, in a throwaway process."""
    code = (
        "import sys;from PySide6.QtGui import QImage, QGuiApplication;"
        "app=QGuiApplication(sys.argv[:1]);"
        "a=QImage(sys.argv[1]);b=QImage(sys.argv[2]);"
        "print('SIZE_MISMATCH') if a.size()!=b.size() else None;"
        "d=sum(1 for y in range(a.height()) for x in range(a.width())"
        " if a.pixel(x,y)!=b.pixel(x,y));"
        "print('DIFF', d, a.width()*a.height())"
    )
    res = subprocess.run([str(PY), "-c", code, str(a), str(b)],
                         capture_output=True, text=True, cwd=str(ROOT),
                         env={**os.environ, "QT_QPA_PLATFORM": "offscreen"})
    out = res.stdout.strip()
    if "DIFF" not in out:
        return None, res.stderr[-400:]
    line = [l for l in out.splitlines() if l.startswith("DIFF")][0]
    _, differing, total = line.split()
    return (int(differing), int(total)), None


def main() -> int:
    FRESH.mkdir(parents=True, exist_ok=True)
    for approved_name, (script, cfg) in TARGETS.items():
        subprocess.run(
            [str(PY), str(ROOT / "experiments/analysis_experience_r2" / script),
             json.dumps(cfg)],
            capture_output=True, text=True, cwd=str(ROOT),
            env={**os.environ, "QT_QPA_PLATFORM": "offscreen",
                 "QT_QPA_FONTDIR": "C:/Windows/Fonts"})

    report = {}
    worst = 0.0
    for approved_name, fresh_name in RENAME.items():
        a, b = APPROVED / approved_name, FRESH / fresh_name
        if not b.exists():
            report[approved_name] = {"error": "fresh capture missing"}
            worst = 100.0
            continue
        result, err = compare(a, b)
        if result is None:
            report[approved_name] = {"error": err}
            worst = 100.0
            continue
        differing, total = result
        pct = 100.0 * differing / total
        worst = max(worst, pct)
        report[approved_name] = {"differing_pixels": differing,
                                 "total_pixels": total,
                                 "percent": round(pct, 4),
                                 "identical": differing == 0}
        print("  %-42s %8d / %d differing  (%.4f%%)"
              % (approved_name, differing, total, pct))

    (ACC / "memory" / "step8_visual_parity.json").write_text(
        json.dumps({"worst_percent": round(worst, 4), "images": report},
                   indent=2) + "\n", encoding="utf-8")
    print()
    print("VERDICT:", "PIXEL-IDENTICAL to the approved captures" if worst == 0
          else "worst difference %.4f%%" % worst)
    return 0 if worst == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
