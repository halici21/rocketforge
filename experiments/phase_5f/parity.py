"""Compare the source and packaged Trade Study tours, field by field.

A screenshot proves something was drawn. This proves the packaged workspace
held the *same numbers and the same verdicts* as the source one, by walking
both reports and comparing every leaf of every captured controller snapshot --
raw metrics, feasibility, Pareto membership, scores, provenance and the solve
counts.

Fields expected to differ are named and excluded rather than filtered by a
pattern, so a newly differing field fails the comparison instead of slipping
through a wildcard.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: Keys whose values legitimately differ between the two builds.
#:
#: ``elapsed`` is wall-clock and ``Elapsed`` is its display row; both are
#: timings rather than results. Everything else here identifies the build.
EXPECTED_TO_DIFFER = {"frozen", "meipass", "python", "messages", "file",
                      "callCounterInstalled", "elapsed_seconds"}

#: Summary rows whose value is a timing rather than a result.
TIMING_ROWS = {"Elapsed"}


def leaves(value, prefix: str = "") -> dict[str, object]:
    """Flatten a report into ``path -> scalar``."""
    out: dict[str, object] = {}
    if isinstance(value, dict):
        if value.get("label") in TIMING_ROWS:
            return out
        for key, item in value.items():
            if key in EXPECTED_TO_DIFFER:
                continue
            out.update(leaves(item, f"{prefix}.{key}" if prefix else key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            out.update(leaves(item, f"{prefix}[{index}]"))
    else:
        out[prefix] = value
    return out


def main() -> int:
    source_path = ROOT / "acceptance" / "phase_5f" / "ui_source" / "study_smoke_source.json"
    frozen_path = ROOT / "acceptance" / "phase_5f" / "ui_packaged" / "study_smoke_frozen.json"
    if not source_path.exists() or not frozen_path.exists():
        print("both tours must have been run first")
        return 1

    source = json.loads(source_path.read_text(encoding="utf-8"))
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))

    a, b = leaves(source), leaves(frozen)
    only_source = sorted(set(a) - set(b))
    only_frozen = sorted(set(b) - set(a))
    differing = sorted(key for key in set(a) & set(b) if a[key] != b[key])

    report = {
        "source": str(source_path.relative_to(ROOT)),
        "packaged": str(frozen_path.relative_to(ROOT)),
        "sourceCaptures": len(source.get("captures", [])),
        "packagedCaptures": len(frozen.get("captures", [])),
        "comparedFields": len(set(a) & set(b)),
        "onlyInSource": only_source,
        "onlyInPackaged": only_frozen,
        "differing": [{"field": key, "source": a[key], "packaged": b[key]}
                      for key in differing],
        "sourceQtMessages": len(source.get("messages", [])),
        "packagedQtMessages": len(frozen.get("messages", [])),
        "sourceSolveCounts": source.get("solveCounts"),
        "packagedSolveCounts": frozen.get("solveCounts"),
        "excludedFields": sorted(EXPECTED_TO_DIFFER),
        "excludedRows": sorted(TIMING_ROWS),
    }
    report["verdict"] = ("PASS" if not (only_source or only_frozen or differing)
                         else "MISMATCH")

    out = ROOT / "acceptance" / "phase_5f" / "source_frozen_parity.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"compared {report['comparedFields']} fields across "
          f"{report['sourceCaptures']} captures")
    print(f"  only in source:   {len(only_source)}")
    print(f"  only in packaged: {len(only_frozen)}")
    print(f"  differing:        {len(differing)}")
    for entry in report["differing"][:20]:
        print(f"    {entry['field']}: {entry['source']!r} vs {entry['packaged']!r}")
    for key in only_source[:10]:
        print(f"    source only: {key}")
    for key in only_frozen[:10]:
        print(f"    packaged only: {key}")
    print(f"  Qt messages: source {report['sourceQtMessages']}, "
          f"packaged {report['packagedQtMessages']}")
    source_counts = source.get("solveCounts", {})
    frozen_counts = frozen.get("solveCounts", {})
    print(f"  chamber solves: source {source_counts.get('actualChemistrySolves')}, "
          f"packaged {frozen_counts.get('actualChemistrySolves')} "
          f"(expected {source_counts.get('expectedChemistrySolves')})")
    print(f"VERDICT: {report['verdict']} -> {out.relative_to(ROOT)}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
