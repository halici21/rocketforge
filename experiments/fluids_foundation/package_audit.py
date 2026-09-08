"""Source against packaged, field by field, plus what the bundle contains.

Same comparator discipline as Phase 5G, including the two corrections that
phase's own audit needed: two NaNs are the same recorded value while a NaN
against a number is a real difference, and wall-clock timings are excluded from
a comparison of *numbers* because they are not numbers under test.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "acceptance" / "fluids_foundation"
OUT.mkdir(parents=True, exist_ok=True)

SOURCE_DIR = OUT / "parity_source"
PACKAGED_DIR = OUT / "parity_packaged"
EXE = ROOT / "dist" / "RocketForge" / "RocketForge.exe"
PYTHON = ROOT / ".venv-cea" / "Scripts" / "python.exe"

#: Fields that legitimately differ between a source run and a frozen one.
EXPECTED_TO_DIFFER = {"frozen"}

#: Wall-clock measurements. Compared for plausibility elsewhere; excluded here,
#: because a run that took 1.7 s instead of 1.8 s has not produced a different
#: number, and letting timings into a numeric comparison is how Phase 5G's own
#: solve-count parity first reported a false failure.
TIMING_KEYS = {"seconds", "elapsed", "run_seconds", "table_seconds",
               "plot_seconds", "per_second"}


def leaves(value, prefix: str = "") -> dict[str, object]:
    """Flatten a JSON document to dotted leaf paths."""
    out: dict[str, object] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            out.update(leaves(item, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            out.update(leaves(item, f"{prefix}[{index}]"))
    else:
        out[prefix] = value
    return out


def same(left, right) -> bool:
    """Exact equality, with two NaNs counted as the same recorded value.

    Python reports ``nan != nan``, which is correct arithmetic and wrong here:
    two runs that both recorded "not a number" recorded the same thing. A NaN
    against a real number is still a difference, and is still reported.
    """
    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True
    return left == right


def excluded(key: str) -> bool:
    tail = key.split(".")[-1].split("[")[0]
    return tail in EXPECTED_TO_DIFFER or tail in TIMING_KEYS


def run(command, cwd) -> int:
    import os

    environment = dict(os.environ)
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["QT_QPA_FONTDIR"] = "C:/Windows/Fonts"
    completed = subprocess.run(command, cwd=str(cwd), env=environment,
                               capture_output=True, text=True)
    return completed.returncode


def compare(label: str, relative: str) -> dict:
    source_path = SOURCE_DIR / relative
    packaged_path = PACKAGED_DIR / relative
    if not source_path.is_file() or not packaged_path.is_file():
        return {"tour": label, "status": "missing",
                "source_present": source_path.is_file(),
                "packaged_present": packaged_path.is_file()}
    a = leaves(json.loads(source_path.read_text(encoding="utf-8")))
    b = leaves(json.loads(packaged_path.read_text(encoding="utf-8")))
    keys = {k for k in set(a) & set(b) if not excluded(k)}
    only_source = sorted(k for k in set(a) - set(b) if not excluded(k))
    only_packaged = sorted(k for k in set(b) - set(a) if not excluded(k))
    differing = sorted(k for k in keys if not same(a[k], b[k]))
    return {
        "tour": label,
        "compared_fields": len(keys),
        "only_in_source": only_source,
        "only_in_packaged": only_packaged,
        "differing": [{"field": k, "source": a[k], "packaged": b[k]}
                      for k in differing],
        "verdict": ("PASS" if not (only_source or only_packaged or differing)
                    else "MISMATCH"),
    }


def package_contents() -> dict:
    root = ROOT / "dist" / "RocketForge"
    if not root.is_dir():
        return {"status": "no bundle"}
    files = [p for p in root.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    names = {p.name.lower() for p in files}
    parts = {part.lower() for p in files for part in p.parts}

    thermo = next((p for p in files if p.name == "thermo.lib"), None)
    accepted = ("8e5df1cca92d4a48663d1ee5a1372e6508c59cddc2247ceeca32f041a03"
                "ec52a")
    thermo_hash = (hashlib.sha256(thermo.read_bytes()).hexdigest()
                   if thermo else "")

    forbidden = {
        "cantera": any("cantera" in n for n in parts),
        "rocketcea": any("rocketcea" in n for n in parts),
        "pytest": any(n == "pytest" for n in parts),
        "scipy": any(n == "scipy" for n in parts),
        "pandas": any(n == "pandas" for n in parts),
        "sklearn": any(n == "sklearn" for n in parts),
        "pymoo": any(n == "pymoo" for n in parts),
        "tests": any(n == "tests" for n in parts),
        "experiments": any(n == "experiments" for n in parts),
    }
    coolprop_files = [p.relative_to(root).as_posix() for p in files
                      if "coolprop" in p.name.lower()
                      or "CoolProp" in p.parts]
    return {
        "file_count": len(files),
        "total_MB": round(total / 1e6, 1),
        "thermo_lib_present": thermo is not None,
        "thermo_lib_sha256": thermo_hash,
        "thermo_lib_matches_accepted": thermo_hash == accepted,
        "coolprop_present": bool(coolprop_files),
        "coolprop_files": sorted(coolprop_files)[:10],
        "coolprop_file_count": len(coolprop_files),
        "forbidden_present": {k: v for k, v in forbidden.items() if v},
        "nothing_forbidden": not any(forbidden.values()),
    }


def main() -> int:
    print("Fluids-foundation package audit")
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGED_DIR.mkdir(parents=True, exist_ok=True)

    tours = [
        ("Fluid properties", "--selftest-fluid-properties",
         "fluid_smoke.json"),
        ("Reactant coupling", "--selftest-reactant-enthalpy-coupling",
         "coupling_smoke.json"),
    ]

    for label, flag, _name in tours:
        code = run([str(PYTHON), str(ROOT / "main.py"), flag,
                    str(SOURCE_DIR)], ROOT)
        print(f"  source   {label}: exit {code}")
        code = run([str(EXE), flag, str(PACKAGED_DIR)], ROOT)
        print(f"  packaged {label}: exit {code}")

    results = [compare(label, name) for label, _flag, name in tours]
    report = {
        "purpose": "source versus packaged, field by field",
        "tours": results,
        "total_fields_compared": sum(t.get("compared_fields", 0)
                                     for t in results),
        "total_differences": sum(len(t.get("differing", [])) for t in results),
        "excluded_fields": sorted(EXPECTED_TO_DIFFER),
        "excluded_timing_keys": sorted(TIMING_KEYS),
        "verdict": "PASS" if all(t.get("verdict") == "PASS" for t in results)
                   else "MISMATCH",
    }
    (OUT / "source_packaged_parity.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    contents = package_contents()
    (OUT / "package_contents.json").write_text(json.dumps(contents, indent=2),
                                               encoding="utf-8")

    for tour in results:
        print(f"  {tour['tour']:20s} {tour.get('compared_fields', 0):>5} fields, "
              f"{len(tour.get('differing', []))} differing "
              f"[{tour.get('verdict')}]")
        for entry in tour.get("differing", [])[:5]:
            print(f"      {entry['field']}: {entry['source']!r} vs "
                  f"{entry['packaged']!r}")
    print(f"  total: {report['total_fields_compared']} fields, "
          f"{report['total_differences']} differences -> {report['verdict']}")
    print(f"  bundle: {contents['file_count']} files, {contents['total_MB']} MB")
    print(f"  CoolProp files bundled: {contents['coolprop_file_count']}")
    print(f"  thermo.lib matches accepted: "
          f"{contents['thermo_lib_matches_accepted']}")
    print(f"  nothing forbidden bundled: {contents['nothing_forbidden']}")
    return 0 if report["verdict"] == "PASS" and contents["nothing_forbidden"] else 1


if __name__ == "__main__":
    sys.exit(main())
