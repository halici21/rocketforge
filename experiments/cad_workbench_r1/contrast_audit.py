"""WCAG contrast audit of ui/theme/Theme.qml's current semantic token pairs.

Same relative-luminance/contrast-ratio math Sunumatik's own
validate-palette-library.mjs uses (WCAG 2.x). Read-only: parses the QML
literally rather than importing Qt, so it runs in plain Python with no
PySide6 dependency.

    python experiments/cad_workbench_r1/contrast_audit.py
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
THEME = ROOT / "ui" / "theme" / "Theme.qml"
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "contrast_audit.json"


def luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
              for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def parse_palette(text: str, block_name: str) -> dict[str, str]:
    start = text.index(f"readonly property QtObject {block_name}:")
    # crude brace-matched slice, sufficient for this file's regular structure
    depth = 0
    i = text.index("{", start)
    j = i
    while True:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    body = text[i:j]
    tokens = {}
    for match in re.finditer(r'readonly property color (\w+): "(#[0-9A-Fa-f]{6})"', body):
        tokens[match.group(1)] = match.group(2)
    return tokens


PAIRS = [
    ("text", "background", "primary text on window", 4.5),
    ("text", "surface", "primary text on panel", 4.5),
    ("text", "surfaceElevated", "primary text on popup", 4.5),
    ("textSecondary", "background", "secondary text on window", 4.5),
    ("textSecondary", "surface", "secondary text on panel", 4.5),
    ("textMuted", "background", "muted text on window", 4.5),
    ("textMuted", "surface", "muted text on panel", 4.5),
    ("textDisabled", "surface", "disabled text on panel (informational only, no floor)", None),
    ("accentContrast", "accent", "accent-contrast ink on accent fill", 4.5),
    ("success", "background", "success token as text-sized mark", 3.0),
    ("warning", "background", "warning token as text-sized mark", 3.0),
    ("error", "background", "error token as text-sized mark", 3.0),
]


def main() -> int:
    text = THEME.read_text(encoding="utf-8")
    results = {"dark": {}, "light": {}}
    for scheme, block in (("dark", "darkPalette"), ("light", "lightPalette")):
        tokens = parse_palette(text, block)
        rows = []
        for fg, bg, role, minimum in PAIRS:
            if fg not in tokens or bg not in tokens:
                continue
            ratio = contrast(tokens[fg], tokens[bg])
            verdict = "INFO" if minimum is None else ("PASS" if ratio >= minimum else "FAIL")
            rows.append({"role": role, "foreground": fg, "fg_hex": tokens[fg],
                        "background": bg, "bg_hex": tokens[bg],
                        "ratio": round(ratio, 2), "target": minimum,
                        "verdict": verdict})
        results[scheme] = rows

    fails = [r for scheme in results.values() for r in scheme if r["verdict"] == "FAIL"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for scheme, rows in results.items():
        print(f"-- {scheme} --")
        for r in rows:
            print(f"  {r['verdict']:5} {r['ratio']:5.2f}  {r['role']}"
                  f" ({r['foreground']} {r['fg_hex']} on {r['background']} {r['bg_hex']}"
                  f", target {r['target']})")
    print(f"\n{len(fails)} FAIL out of {sum(len(v) for v in results.values())} pairs checked")
    return 0


if __name__ == "__main__":
    exit(main())
