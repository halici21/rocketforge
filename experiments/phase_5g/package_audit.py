"""Source versus packaged, and what the bundle actually contains.

Two jobs:

**Parity.** Compare every deterministic field of every tour, source against
packaged -- numbers, statuses, feasibility, Pareto membership, scores,
provenance and solve counts. Fields that legitimately differ are named, not
matched by a pattern, so a newly differing field fails rather than slipping
through a wildcard.

**Contents.** Walk the bundle and report what is in it: the provider, its
database and hash, and whether anything development-only came along. A grep of
one directory would not do -- this walks every file.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "acceptance" / "phase_5g"
BUNDLE = ROOT / "dist" / "RocketForge"

#: Keys whose values legitimately differ between a source run and a frozen one.
EXPECTED_TO_DIFFER = {
    "frozen", "meipass", "python", "messages", "file",
    "callCounterInstalled", "elapsed_seconds", "seconds",
    "run_seconds", "results_publication_seconds",
    "pareto_publication_seconds", "messages_so_far",
}

#: Display rows whose value is a timing rather than a result.
TIMING_ROWS = {"Elapsed"}

TOURS = [
    ("thermochemistry_ui", "ui_source_5d/ui_smoke_source.json",
     "ui_packaged_5d/ui_smoke_frozen.json"),
    ("rocket_performance", "ui_source_5e/perf_smoke_source.json",
     "ui_packaged_5e/perf_smoke_frozen.json"),
    ("trade_study", "ui_source_5f/study_smoke_source.json",
     "ui_packaged_5f/study_smoke_frozen.json"),
    ("workspaces", "ui_source_shell/shell_smoke_source.json",
     "ui_packaged_shell/shell_smoke_frozen.json"),
]


def leaves(value, prefix: str = "") -> dict[str, object]:
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


def same(left, right) -> bool:
    """Whether two recorded values are the same value.

    ``NaN`` is how a row records "this was never produced", and Python reports
    ``nan != nan``. Two NaNs are the same recorded value and must compare
    equal; a NaN against a number is still a difference, which is the case that
    matters.
    """
    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True
    return left == right


def compare(label: str, source_rel: str, frozen_rel: str) -> dict:
    source_path, frozen_path = OUT / source_rel, OUT / frozen_rel
    if not source_path.is_file() or not frozen_path.is_file():
        return {"tour": label, "status": "missing"}
    source = json.loads(source_path.read_text(encoding="utf-8"))
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    a, b = leaves(source), leaves(frozen)
    only_source = sorted(set(a) - set(b))
    only_frozen = sorted(set(b) - set(a))
    differing = sorted(k for k in set(a) & set(b)
                       if not same(a[k], b[k]))
    return {
        "tour": label,
        "compared_fields": len(set(a) & set(b)),
        "only_in_source": only_source,
        "only_in_packaged": only_frozen,
        "differing": [{"field": k, "source": a[k], "packaged": b[k]}
                      for k in differing],
        "source_qt_messages": len(source.get("messages", [])),
        "packaged_qt_messages": len(frozen.get("messages", [])),
        "verdict": ("PASS" if not (only_source or only_frozen or differing)
                    else "MISMATCH"),
    }


def solve_count_parity() -> dict:
    """The counts a packaging change could plausibly break."""
    rows = []
    for label, source_rel, frozen_rel in TOURS:
        source_path, frozen_path = OUT / source_rel, OUT / frozen_rel
        if not (source_path.is_file() and frozen_path.is_file()):
            continue
        source = json.loads(source_path.read_text(encoding="utf-8"))
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        for key in ("solveCounts", "chamberSolves", "large_study"):
            if key not in source and key not in frozen:
                continue
            left = dict(source.get(key) or {})
            right = dict(frozen.get(key) or {})
            # The block carries wall-clock timings beside the counts. A
            # packaged run is not expected to take the same number of
            # milliseconds; it is expected to solve the same number of times.
            for timing in ("run_seconds", "results_publication_seconds",
                           "pareto_publication_seconds", "seconds",
                           "elapsed_seconds"):
                left.pop(timing, None)
                right.pop(timing, None)
            rows.append({"tour": label, "field": key,
                         "compared": sorted(set(left) | set(right)),
                         "source": left, "packaged": right,
                         "identical": left == right})
    return {
        "purpose": "packaging must not change how many times anything is solved",
        "rows": rows,
        "verdict": "PASS" if all(r["identical"] for r in rows) else "FAIL",
    }


def provenance_parity() -> dict:
    """Provider identity, database hash and model, source against packaged."""
    rows = []
    for label, source_rel, frozen_rel in TOURS:
        source_path, frozen_path = OUT / source_rel, OUT / frozen_rel
        if not (source_path.is_file() and frozen_path.is_file()):
            continue
        source = json.loads(source_path.read_text(encoding="utf-8"))
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))

        def provenance(report):
            found = []
            for capture in report.get("captures", []):
                state = capture.get("state", {})
                for key in ("provenance", "provenanceRows"):
                    if state.get(key):
                        found.append(state[key])
            return found

        a, b = provenance(source), provenance(frozen)
        rows.append({"tour": label, "records_compared": min(len(a), len(b)),
                     "identical": a == b})
    return {
        "purpose": "a packaged result must carry the same provenance",
        "rows": rows,
        "verdict": "PASS" if all(r["identical"] for r in rows) else "FAIL",
    }


def package_contents() -> dict:
    """Walk the bundle: what is in it, and what must not be."""
    if not BUNDLE.is_dir():
        return {"status": "missing", "path": str(BUNDLE)}

    files = [p for p in BUNDLE.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)

    forbidden = {
        "cantera": [], "rocketcea": [], "coolprop": [], "pytest": [],
        "_pytest": [], "scipy": [], "pandas": [], "sklearn": [],
        "pymoo": [], "deap": [], "optuna": [],
    }
    tests, experiments = [], []
    cea_files, thermo_lib = [], None

    for path in files:
        relative = path.relative_to(BUNDLE).as_posix()
        lowered = relative.lower()
        parts = [p.lower() for p in path.relative_to(BUNDLE).parts]
        for name in forbidden:
            # match a path segment, so "coolprop" does not match a substring
            # inside an unrelated file name
            if any(part == name or part.startswith(f"{name}.")
                   or part.startswith(f"{name}-") for part in parts):
                forbidden[name].append(relative)
        if any(part == "tests" for part in parts):
            tests.append(relative)
        if any(part == "experiments" for part in parts):
            experiments.append(relative)
        if any(part == "cea" for part in parts):
            cea_files.append(relative)
        if path.name == "thermo.lib":
            thermo_lib = path

    accepted_hash = ("8e5df1cca92d4a48663d1ee5a1372e6508c59cddc"
                     "2247ceeca32f041a03ec52a")
    bundled_hash = (hashlib.sha256(thermo_lib.read_bytes()).hexdigest()
                    if thermo_lib else None)

    return {
        "path": str(BUNDLE.relative_to(ROOT)).replace("\\", "/"),
        "file_count": len(files),
        "total_bytes": total,
        "total_MB": round(total / 1024 / 1024, 1),
        "executable_present": (BUNDLE / "RocketForge.exe").is_file(),
        "cea_files": len(cea_files),
        "thermo_lib_present": thermo_lib is not None,
        "thermo_lib_relative": (thermo_lib.relative_to(BUNDLE).as_posix()
                                if thermo_lib else None),
        "thermo_lib_sha256": bundled_hash,
        "thermo_lib_matches_accepted": bundled_hash == accepted_hash,
        "accepted_thermo_lib_sha256": accepted_hash,
        "forbidden_present": {k: v for k, v in forbidden.items() if v},
        "tests_bundled": tests,
        "experiments_bundled": experiments,
        "verdict": "PASS" if (not any(forbidden.values()) and not tests
                              and not experiments
                              and bundled_hash == accepted_hash) else "FAIL",
        "clean_machine_note":
            "this audit inspects the bundle's contents; it is not a "
            "clean-machine installation test. No machine without the "
            "development environment was used, so the claim here is "
            "self-containment of the bundle, not verified clean-machine "
            "operation.",
    }


def main() -> int:
    print("Phase 5G package audit")
    tours = [compare(*entry) for entry in TOURS]
    report = {
        "purpose": "source versus packaged, field by field",
        "tours": tours,
        "total_fields_compared": sum(t.get("compared_fields", 0)
                                     for t in tours),
        "total_differences": sum(len(t.get("differing", [])) for t in tours),
        "excluded_fields": sorted(EXPECTED_TO_DIFFER),
        "excluded_rows": sorted(TIMING_ROWS),
        "solve_counts": solve_count_parity(),
        "provenance": provenance_parity(),
        "verdict": "PASS" if all(t.get("verdict") == "PASS" for t in tours)
                   else "MISMATCH",
    }
    (OUT / "source_packaged_parity.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    contents = package_contents()
    (OUT / "package_contents.json").write_text(
        json.dumps(contents, indent=2), encoding="utf-8")

    for tour in tours:
        print(f"  {tour['tour']:22s} {tour.get('compared_fields', 0):>6} fields, "
              f"{len(tour.get('differing', []))} differing, "
              f"{len(tour.get('only_in_source', []))}/"
              f"{len(tour.get('only_in_packaged', []))} one-sided "
              f"[{tour.get('verdict')}]")
        for entry in tour.get("differing", [])[:5]:
            print(f"      {entry['field']}: {entry['source']!r} vs "
                  f"{entry['packaged']!r}")
    print(f"  total: {report['total_fields_compared']} fields, "
          f"{report['total_differences']} differences -> {report['verdict']}")
    print(f"  solve counts: {report['solve_counts']['verdict']}")
    print(f"  provenance:   {report['provenance']['verdict']}")
    print()
    print(f"  bundle: {contents['file_count']} files, {contents['total_MB']} MB")
    print(f"  thermo.lib hash matches accepted: "
          f"{contents['thermo_lib_matches_accepted']}")
    print(f"  forbidden present: {contents['forbidden_present'] or 'none'}")
    print(f"  tests bundled: {len(contents['tests_bundled'])}, "
          f"experiments bundled: {len(contents['experiments_bundled'])}")
    print(f"  contents verdict: {contents['verdict']}")
    return 0 if (report["verdict"] == "PASS"
                 and contents["verdict"] == "PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
