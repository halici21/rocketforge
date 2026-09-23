"""Generate the Phase 5 freeze manifests.

The boundary is drawn around **scientific contracts and the code that
implements them**, not around everything that exists. Acceptance harnesses,
screenshots, test fixtures and QML layout files are deliberately outside it:
freezing a view file would make a layout fix a contract break, and freezing a
test would make improving a test a contract break.

Four contracts, each versioned independently so a future provider fix does not
have to bump the domain API it implements:

    THERMOCHEMISTRY API v1.0        the provider-independent domain
    IDEAL ROCKET PERFORMANCE v1.0   the chamber handshake and the nozzle model
    TRADE STUDY API v1.0            the generic design-space engine
    NASA CEA PROVIDER v1.0          the adapter and its scientific mapping

The CEA provider is manifested as well as its contract, and the reason is
recorded in the manifest note: its *mapping* decisions -- which CEA name a
propellant becomes, which temperature range refuses a stream, which product set
a case is solved over -- are scientific claims, not implementation detail. A
future provider bug fix bumps that manifest's version and re-runs the provider
validation; it does not touch the three API manifests.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rocketforge.core.freeze import (  # noqa: E402
    ALGORITHM_DESCRIPTION,
    MANIFEST_ALGORITHM,
    build_manifest,
    verify_manifest,
    write_manifest,
)

#: Tracked beside the tests that verify it (it was the untracked acceptance/).
OUT = ROOT / "tests" / "acceptance" / "freeze" / "phase_5g"

CONTRACTS = [
    {
        "contract": "THERMOCHEMISTRY API",
        "version": "1.0",
        "stem": "freeze_thermochemistry_api_v1",
        "roots": ["rocketforge/physics/thermochemistry"],
        "note": "The provider-independent thermochemistry domain: the chamber "
                "state record, the provider protocol, composition and species "
                "semantics, propellant records, requests, provenance, "
                "validation and tolerances. No provider is named here; the "
                "arrow points from an adapter down to this contract and never "
                "back.",
    },
    {
        "contract": "IDEAL ROCKET PERFORMANCE API",
        "version": "1.0",
        "stem": "freeze_rocket_performance_api_v1",
        "roots": ["rocketforge/engineering/chamber",
                  "rocketforge/engineering/nozzle"],
        "note": "The single-gamma chamber handshake and RocketForge's own "
                "ideal rocket model: c*, Cf, thrust, c_eff and Isp, computed "
                "over frozen Compressible v1. A provider's own performance "
                "values are an oracle and are not part of this contract.",
    },
    {
        "contract": "TRADE STUDY API",
        "version": "1.0",
        "stem": "freeze_trade_study_api_v1",
        "roots": ["rocketforge/engine/studies"],
        "note": "The generic design-space engine: design variables, metric "
                "registry, point enumeration and stage keys, study definition "
                "and validation, constraints, objectives, Pareto, optional "
                "weighted scoring, results and execution. It imports no "
                "physics, no provider and no Qt, and is exercised by synthetic "
                "evaluators.",
    },
    {
        "contract": "NASA CEA PROVIDER",
        "version": "1.0",
        "stem": "freeze_cea_provider_v1",
        "roots": ["rocketforge/providers/cea"],
        "note": "The NASA CEA v3 adapter. Manifested because its mapping "
                "decisions are scientific claims -- which CEA reactant name a "
                "propellant becomes, which declared temperature range refuses "
                "a stream, which product species set a case is solved over. "
                "Versioned separately from the three API contracts so a "
                "provider fix can be released without reopening them.",
    },
]

#: Excluded from every manifest wherever they appear.
EXCLUDE_NAMES = {"__pycache__"}


def collect(roots: list[str]) -> list[Path]:
    paths: list[Path] = []
    for relative in roots:
        base = ROOT / relative
        for path in sorted(base.rglob("*.py")):
            if any(part in EXCLUDE_NAMES for part in path.parts):
                continue
            paths.append(path)
    return paths


def main() -> int:
    # Superseded contracts must not be regenerated from a moved tree.
    #
    # Learned the hard way: run during the transport/line work, this script
    # rewrote freeze_cea_provider_v1.json from a v1.1 tree, producing twelve
    # files under a "1.0" label. The record was recovered only because the
    # digest is published elsewhere and the fluids-foundation supersession
    # tests fired within seconds.
    #
    # A generator that can silently rewrite history is the wrong shape. This
    # one refuses: a superseded manifest is evidence, not output.
    superseded = [spec for spec in CONTRACTS
                  if (spec["contract"], spec["version"])
                  == ("NASA CEA PROVIDER", "1.0")]
    for spec in superseded:
        print(f"  SKIPPING {spec['contract']} v{spec['version']}: superseded "
              "by v1.1 in the fluids foundation. Its manifest records the "
              "source as accepted at the Phase 5G freeze and is not "
              "regenerated. Use experiments/fluids_foundation/"
              "generate_freeze_manifests.py for v1.1.")
        CONTRACTS.remove(spec)

    print("Phase 5G freeze manifests")
    records = []
    for spec in CONTRACTS:
        paths = collect(spec["roots"])
        manifest = build_manifest(spec["contract"], spec["version"], ROOT,
                                  paths, note=spec["note"])
        json_path, text_path = write_manifest(manifest, OUT, spec["stem"])
        check = verify_manifest(manifest, ROOT)
        records.append({
            "contract": manifest.contract,
            "version": manifest.version,
            "roots": spec["roots"],
            "file_count": len(manifest.files),
            "digest": manifest.digest,
            "json": str(json_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256_text": str(text_path.relative_to(ROOT)).replace("\\", "/"),
            "self_verification": check["verdict"],
        })
        print(f"  {manifest.contract} v{manifest.version}: "
              f"{len(manifest.files)} files, digest {manifest.digest[:16]}… "
              f"[{check['verdict']}]")

    combined = {
        "purpose": "the Phase 5 propulsion-analysis freeze boundary",
        "algorithm": MANIFEST_ALGORITHM,
        "algorithm_description": list(ALGORITHM_DESCRIPTION),
        "reproducible_without_this_code": True,
        "checkable_with": "sha256sum -c <stem>.sha256",
        "python": sys.version.split()[0],
        "excluded_from_every_manifest": [
            "acceptance harnesses and experiment scripts",
            "tests and fixtures",
            "QML and other interface files",
            "screenshots and generated artifacts",
            "__pycache__",
        ],
        "exclusion_reason": "the freeze protects scientific contracts. "
                            "Freezing a view file would make a layout fix a "
                            "contract break; freezing a test would make "
                            "improving a test one.",
        "contracts": records,
    }
    (OUT / "freeze_manifest.json").write_text(
        json.dumps(combined, indent=2), encoding="utf-8")
    print(f"\n-> {(OUT / 'freeze_manifest.json').relative_to(ROOT)}")
    return 0 if all(r["self_verification"] == "PASS" for r in records) else 1


if __name__ == "__main__":
    sys.exit(main())
