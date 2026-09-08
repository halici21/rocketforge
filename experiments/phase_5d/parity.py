"""Source against packaged: the same tour, compared state by state.

Both reports come from ``rocketforge.application.uismoke``, so the comparison
is between two runs of one program rather than between two descriptions of it.
Every scalar the interface displayed at every capture is compared, and the
worst relative difference is reported -- not a spot check.

Usage::

    .venv\\Scripts\\python.exe experiments\\phase_5d\\parity.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE = ROOT / "acceptance" / "phase_5d"


def _flatten(value, prefix=""):
    """Every leaf of a nested report, keyed by its path."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _flatten(item, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _flatten(item, f"{prefix}[{index}]")
    else:
        yield prefix, value


def main() -> int:
    source = json.loads((ACCEPTANCE / "ui_smoke_source.json").read_text(encoding="utf-8"))
    frozen = json.loads(
        (ACCEPTANCE / "packaged" / "ui_smoke_frozen.json").read_text(encoding="utf-8"))

    assert source["frozen"] is False, "the source report says it was frozen"
    assert frozen["frozen"] is True, "the packaged report says it was not frozen"

    by_name_source = {c["name"]: c["state"] for c in source["captures"]}
    by_name_frozen = {c["name"]: c["state"] for c in frozen["captures"]}

    report = {
        "source_python": source["python"],
        "frozen_python": frozen["python"],
        "source_provider": source["provider_headline"],
        "frozen_provider": frozen["provider_headline"],
        "captures_source": len(by_name_source),
        "captures_frozen": len(by_name_frozen),
        "capture_names_match": sorted(by_name_source) == sorted(by_name_frozen),
        "qt_messages_source": len(source["messages"]),
        "qt_messages_frozen": len(frozen["messages"]),
    }

    differences = []
    compared = 0
    worst = {"key": None, "relative": 0.0}

    for name in sorted(set(by_name_source) & set(by_name_frozen)):
        left = dict(_flatten(by_name_source[name]))
        right = dict(_flatten(by_name_frozen[name]))
        for key in sorted(set(left) | set(right)):
            a, b = left.get(key, "<missing>"), right.get(key, "<missing>")
            compared += 1
            if isinstance(a, float) and isinstance(b, float):
                if math.isnan(a) and math.isnan(b):
                    continue
                if a == b:
                    continue
                scale = max(abs(a), abs(b), 1e-30)
                relative = abs(a - b) / scale
                if relative > worst["relative"]:
                    worst = {"key": f"{name}.{key}", "relative": relative}
                differences.append({"capture": name, "field": key,
                                    "source": a, "frozen": b,
                                    "relative": relative})
            elif a != b:
                differences.append({"capture": name, "field": key,
                                    "source": a, "frozen": b})

    report["fields_compared"] = compared
    report["differences"] = differences
    report["difference_count"] = len(differences)
    report["worst_numeric_difference"] = worst
    report["bitwise_identical"] = not differences

    out = ACCEPTANCE / "ui_source_frozen_parity.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"captures: {report['captures_source']} source / "
          f"{report['captures_frozen']} frozen, "
          f"names match: {report['capture_names_match']}")
    print(f"fields compared: {compared}")
    print(f"differences: {len(differences)}")
    for entry in differences[:20]:
        print("   ", entry)
    print(f"bitwise identical: {report['bitwise_identical']}")
    return 0 if report["bitwise_identical"] and report["capture_names_match"] else 1


if __name__ == "__main__":
    sys.exit(main())
