"""Compare Rocket Performance's original accepted-pilot captures against its
capture through the new CAD/CAE Workbench R1 production shell.

Adapted from experiments/ui_visual_pilot/scientific_parity.py (same method,
same strictness -- no normalisation, no tolerance) rather than reusing that
script directly, because it hardcodes "before"/"after" and writes to
acceptance/ui_visual_pilot/scientific_parity.json -- overwriting the
original accepted pilot's own evidence would destroy history this program
must not touch.

    python experiments/cad_workbench_r1/rocket_performance_parity.py
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PILOT_BASE = ROOT / "acceptance" / "ui_visual_pilot"
OUT_DIR = ROOT / "acceptance" / "cad_workbench_r1" / "rocket_performance"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def leaves(value, prefix: str):
    if isinstance(value, dict):
        for key in sorted(value):
            yield from leaves(value[key], f"{prefix}.{key}")
    elif isinstance(value, list):
        yield f"{prefix}.length", len(value)
        for index, item in enumerate(value):
            yield from leaves(item, f"{prefix}[{index}]")
    else:
        yield prefix, value


def load(label: str) -> dict:
    path = PILOT_BASE / label / "capture_matrix.json"
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    before, after = load("before"), load("after_r1_shell")

    by_name = {c["name"]: c for c in before["captures"]}
    after_by_name = {c["name"]: c for c in after["captures"]}

    only_before = sorted(set(by_name) - set(after_by_name))
    only_after = sorted(set(after_by_name) - set(by_name))

    differences: list[dict] = []
    fields = 0
    for name in sorted(set(by_name) & set(after_by_name)):
        a = dict(leaves(by_name[name]["state"], "state"))
        b = dict(leaves(after_by_name[name]["state"], "state"))
        for key in sorted(set(a) | set(b)):
            fields += 1
            if a.get(key, "<missing>") != b.get(key, "<missing>"):
                differences.append({"capture": name, "field": key,
                                    "before": a.get(key, "<missing>"),
                                    "after": b.get(key, "<missing>")})

    report = {
        "purpose": "Rocket Performance, accepted pilot vs. the new CAD/CAE "
                   "Workbench R1 production shell -- must not change one "
                   "scientific result",
        "before_label": "before (original accepted pilot baseline)",
        "after_label": "after_r1_shell (new Browser/Dock/palette shell, "
                       "page itself unmodified)",
        "captures_compared": len(set(by_name) & set(after_by_name)),
        "fields_compared": fields,
        "differences": differences,
        "only_before": only_before,
        "only_after": only_after,
        "chemistry_solves_before": before.get("chemistrySolvesPerInteraction"),
        "chemistry_solves_after": after.get("chemistrySolvesPerInteraction"),
        "total_solves_before": before.get("totalSolves"),
        "total_solves_after": after.get("totalSolves"),
        "qt_warnings_before": len(before.get("warnings", [])),
        "qt_warnings_after": len(after.get("warnings", [])),
    }
    passed = (not differences and not only_before and not only_after
              and report["chemistry_solves_after"]
              == report["chemistry_solves_before"]
              and report["total_solves_after"] == report["total_solves_before"]
              and report["qt_warnings_after"] <= report["qt_warnings_before"])
    report["verdict"] = "PASS" if passed else "FAIL"

    (OUT_DIR / "scientific_parity.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    print(f"{report['captures_compared']} captures, {fields} fields, "
          f"{len(differences)} differences")
    print(f"solves {report['total_solves_before']} -> {report['total_solves_after']}")
    print(f"chemistry solves per interaction: before={report['chemistry_solves_before']} "
          f"after={report['chemistry_solves_after']}")
    print(f"Qt warnings: before={report['qt_warnings_before']} "
          f"after={report['qt_warnings_after']}")
    print(f"verdict: {report['verdict']}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
