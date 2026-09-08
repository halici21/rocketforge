"""Compare rendered captures against the accepted pilot, pixel by pixel.

Scientific parity reads controller *properties*. It cannot see the rendered
page at all, which is exactly how a change that silently emptied the entire
headline readout -- Isp, Cf, c*, c_eff and thrust, gone -- passed 5688 fields
with 0 differences. Only looking at the picture caught it.

This compares each capture against the same capture from the accepted visual
pilot, preserved in acceptance/ui_rollout/baseline_snapshot/pilot_captures/.

    python experiments/ui_visual_pilot/visual_parity.py

Pixel identity is not required and is not the gate: anti-aliasing and text
layout can move a pixel without meaning anything. What is a gate is CONTENT
DISAPPEARING -- a region that used to carry ink and now carries none. So two
numbers are reported per capture:

  changed_fraction  how much of the image differs at all
  ink_ratio         non-background pixels now, over non-background pixels then

An ink_ratio well below 1 means the page is rendering less than it used to,
which is the failure this exists to catch.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CURRENT = ROOT / "acceptance" / "ui_visual_pilot" / "after"
ACCEPTED = (ROOT / "acceptance" / "ui_rollout" / "baseline_snapshot"
            / "pilot_captures" / "after")
OUT = ROOT / "acceptance" / "ui_rollout"

#: below this, the page is drawing materially less than the accepted pilot
INK_FLOOR = 0.90
#: above this, too much of the image moved to be anti-aliasing
CHANGED_CEILING = 0.02


def load(path: pathlib.Path):
    from PySide6.QtGui import QImage

    image = QImage(str(path))
    if image.isNull():
        raise SystemExit(f"cannot read {path}")
    return image.convertToFormat(QImage.Format.Format_RGB32)


def stats(image) -> tuple[int, list[int]]:
    """Non-background pixel count, and a coarse row profile."""
    width, height = image.width(), image.height()
    # the background is whatever the corner is: dark in dark theme, light in
    # light theme, so this works without knowing which was captured
    background = image.pixel(2, height - 2) & 0xFFFFFF
    ink = 0
    profile = []
    step = 4
    for y in range(0, height, step):
        row = 0
        for x in range(0, width, step):
            if (image.pixel(x, y) & 0xFFFFFF) != background:
                row += 1
        profile.append(row)
        ink += row
    return ink, profile


def compare(a, b) -> float:
    if a.size() != b.size():
        return 1.0
    width, height = a.width(), a.height()
    step = 4
    differing = total = 0
    for y in range(0, height, step):
        for x in range(0, width, step):
            total += 1
            if (a.pixel(x, y) & 0xFFFFFF) != (b.pixel(x, y) & 0xFFFFFF):
                differing += 1
    return differing / total if total else 0.0


def main() -> int:
    from PySide6.QtGui import QGuiApplication

    QGuiApplication.instance() or QGuiApplication(sys.argv[:1])

    if not ACCEPTED.is_dir():
        print(f"no accepted captures at {ACCEPTED}")
        return 1

    rows = []
    failures = []
    for path in sorted(ACCEPTED.glob("*.png")):
        current = CURRENT / path.name
        if not current.is_file():
            failures.append(f"{path.name}: missing from the current run")
            continue
        before, after = load(path), load(current)
        ink_before, _ = stats(before)
        ink_after, _ = stats(after)
        ratio = (ink_after / ink_before) if ink_before else 1.0
        changed = compare(before, after)
        ok_ink = ratio >= INK_FLOOR
        ok_changed = changed <= CHANGED_CEILING
        rows.append({"capture": path.name,
                     "ink_before": ink_before, "ink_after": ink_after,
                     "ink_ratio": round(ratio, 4),
                     "changed_fraction": round(changed, 5),
                     "pass": ok_ink and ok_changed})
        if not ok_ink:
            failures.append(f"{path.name}: ink ratio {ratio:.3f} < {INK_FLOOR} "
                            "-- the page renders less than the accepted pilot")
        elif not ok_changed:
            failures.append(f"{path.name}: {changed:.3%} of pixels moved "
                            f"(> {CHANGED_CEILING:.0%})")

    report = {
        "purpose": "the memory fix must not change what the page draws",
        "accepted_from": str(ACCEPTED.relative_to(ROOT).as_posix()),
        "ink_floor": INK_FLOOR, "changed_ceiling": CHANGED_CEILING,
        "captures": rows, "failures": failures,
        "verdict": "PASS" if not failures else "FAIL",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "visual_parity.json").write_text(json.dumps(report, indent=2),
                                            encoding="utf-8")

    worst = sorted(rows, key=lambda r: r["ink_ratio"])[:5]
    print(f"{len(rows)} captures compared against the accepted pilot")
    for row in worst:
        print(f"  ink {row['ink_ratio']:.4f}  changed "
              f"{row['changed_fraction']:.4%}  {row['capture']}")
    for failure in failures:
        print(f"  FAIL {failure}")
    print(report["verdict"])
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
