"""Freeze manifests for the fluids foundation, and the CEA provider's v1.1.

Same algorithm as Phase 5G -- ``rocketforge-freeze-manifest/1``, unchanged and
restated in every file it writes. Production ``.py`` only: no test, no
harness, no artifact, no QML.

**The CEA provider is versioned, not overwritten.** Its v1.0 manifest stays
exactly where it is, as the historical record of what was accepted at the Phase
5G freeze. This writes a *new* v1.1 manifest beside it. Nothing here rewrites
a digest that was published.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rocketforge.core.freeze import (  # noqa: E402
    MANIFEST_ALGORITHM,
    FrozenFile,
    manifest_text,
    overall_digest,
)

OUT_DIR = ROOT / "acceptance" / "fluids_foundation"

CONTRACTS = {
    "freeze_fluid_properties_api_v1": {
        "contract": "FLUID PROPERTIES API",
        "version": "1.0",
        "roots": ["rocketforge/physics/fluids"],
        "note": "the fluid-property domain: identity, phase, request, state, "
                "capabilities, provenance, provider protocol",
    },
    "freeze_coolprop_provider_v1": {
        "contract": "COOLPROP FLUID PROVIDER",
        "version": "1.0",
        "roots": ["rocketforge/providers/fluid_properties"],
        "note": "the constant-property and CoolProp implementations of that "
                "domain, versioned separately from it",
    },
    "freeze_propellant_metrics_api_v1": {
        "contract": "PROPELLANT METRICS API",
        "version": "1.0",
        "roots": ["rocketforge/engineering/propellants"],
        "note": "propellant-to-fluid binding, validated stream density, "
                "additive-volume bulk density, density impulse",
    },
    "freeze_cea_provider_v1_1": {
        "contract": "NASA CEA PROVIDER",
        "version": "1.1",
        "roots": ["rocketforge/providers/cea"],
        "note": "v1.0 plus the reactant sensible-enthalpy correction. "
                "Additive: the v1.0 native policy is the default and "
                "reproduces every v1.0 result bit for bit.",
        "supersedes": "freeze_cea_provider_v1",
        "change": [
            "added rocketforge/providers/cea/enthalpy_coupling.py",
            "CEAChamberInput gained a defaulted `enthalpy_correction` field, "
            "appended last so v1.0 field order is unchanged",
            "solve_chamber_raw adds that correction to CEA's own mixture "
            "enthalpy before the HP constraint is formed",
            "build_chamber_input gained a defaulted keyword argument",
            "solve_chamber gained three defaulted keyword arguments",
            "provenance always records the reactant enthalpy policy",
        ],
    },
}


def collect(roots: list[str]) -> list[FrozenFile]:
    import hashlib

    files: list[FrozenFile] = []
    for root in roots:
        for path in sorted((ROOT / root).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append(FrozenFile(path=path.relative_to(ROOT).as_posix(),
                                    sha256=digest))
    return files


OUT_DIR.mkdir(parents=True, exist_ok=True)
combined = {
    "purpose": "the fluids-foundation freeze boundary",
    "algorithm": MANIFEST_ALGORITHM,
    "algorithm_description": [
        "1. collect the files, each relative to the repository root",
        "2. convert each path to POSIX form",
        "3. sort the relative paths lexicographically by UTF-8 code point",
        "4. SHA-256 each file's exact bytes",
        "5. one line per file: '<hex><two spaces><path>\\n'",
        "6. encode that text as UTF-8",
        "7. the overall digest is the SHA-256 of those bytes",
    ],
    "reproducible_without_this_code": True,
    "checkable_with": "sha256sum -c <stem>.sha256",
    "python": f"{sys.version_info.major}.{sys.version_info.minor}."
              f"{sys.version_info.micro}",
    "excluded_from_every_manifest": [
        "acceptance harnesses and experiment scripts",
        "tests and fixtures",
        "QML and other interface files",
        "screenshots and generated artifacts",
        "__pycache__",
    ],
    "contracts": {},
}

print("Fluids-foundation freeze manifests")
for stem, spec in CONTRACTS.items():
    files = collect(spec["roots"])
    digest = overall_digest(files)
    record = {
        "contract": spec["contract"],
        "version": spec["version"],
        "algorithm": MANIFEST_ALGORITHM,
        "roots": spec["roots"],
        "note": spec["note"],
        "file_count": len(files),
        "digest": digest,
        "files": [{"path": f.path, "sha256": f.sha256} for f in files],
    }
    for key in ("supersedes", "change"):
        if key in spec:
            record[key] = spec[key]
    (OUT_DIR / f"{stem}.json").write_text(json.dumps(record, indent=2),
                                          encoding="utf-8")
    (OUT_DIR / f"{stem}.sha256").write_text(manifest_text(files),
                                            encoding="utf-8")
    combined["contracts"][stem] = {
        "contract": spec["contract"], "version": spec["version"],
        "file_count": len(files), "digest": digest}
    print(f"  {spec['contract']} v{spec['version']}: {len(files)} files, "
          f"digest {digest[:16]}...")

(OUT_DIR / "freeze_manifest.json").write_text(json.dumps(combined, indent=2),
                                              encoding="utf-8")
print(f"\n-> {OUT_DIR / 'freeze_manifest.json'}")
