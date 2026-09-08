"""Compare the before and after capture matrices field by field.

The pilot's governing rule is that a visual redesign must not change one
scientific result. That is not a claim to be made by reading a diff of QML: it
is decided here, by comparing the scientific snapshot taken at each of the
canonical states in both runs.

    python experiments/ui_visual_pilot/scientific_parity.py

Exit status is 0 only when every field at every state agrees exactly. Values
are compared as they were captured -- formatted strings and numbers -- so a
changed rounding, a dropped unit or a relabelled quantity all count as a
difference. Nothing is normalised, and no tolerance is applied: a tolerance
here would be a way of not noticing.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / "acceptance" / "ui_visual_pilot"


def leaves(value, prefix: str):
    """Flatten to scalars, so a report names the exact row that moved.

    Comparing the nested structures whole would be just as strict -- Python
    compares them deeply -- but it would say only that ``resultGroups``
    differs, and the count of what was checked would be 27 fields per state
    rather than the couple of hundred values a reader actually sees.
    """
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
    path = BASE / label / "capture_matrix.json"
    if not path.is_file():
        raise SystemExit(f"missing {path}; run capture_matrix.py {label}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    before, after = load("before"), load("after")

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
        "purpose": "the visual pilot must not change one scientific result",
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

    (BASE / "scientific_parity.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    print(f"{report['captures_compared']} captures, {fields} fields, "
          f"{len(differences)} differences")
    print(f"solves {report['total_solves_before']} -> "
          f"{report['total_solves_after']}, "
          f"warnings {report['qt_warnings_before']} -> "
          f"{report['qt_warnings_after']}")
    for d in differences[:20]:
        print(f"  {d['capture']}.{d['field']}: "
              f"{d['before']!r} -> {d['after']!r}")
    print(report["verdict"])
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
