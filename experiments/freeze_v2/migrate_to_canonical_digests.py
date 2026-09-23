"""Migrate the freeze manifests from algorithm 1 (raw bytes) to 2 (canonical text).

One-off, and kept so the migration can be audited and re-run. It reads the
algorithm-1 manifests from the local, untracked ``acceptance/`` evidence and
writes algorithm-2 manifests to the tracked ``tests/acceptance/freeze/``.

Nothing is re-frozen. For every file of every current manifest it proves two
things before writing anything, and stops if either fails:

  1. the recorded algorithm-1 digest is the SHA-256 of the file's bytes on
     disk now -- so the manifest describes this working copy exactly;
  2. those bytes with CRLF -> LF are identical to the committed git blob at
     HEAD -- so this working copy holds exactly the committed content.

Together they say the algorithm-2 digest describes the same content the
algorithm-1 digest froze, and that a fresh checkout will reproduce it.

The superseded ``freeze_cea_provider_v1`` is copied byte for byte and keeps
algorithm 1: it is history, and it is only ever checked for internal
consistency. The Phase 4G compressible record -- 16-hex raw-byte prefixes in a
Markdown table -- becomes a full algorithm-2 manifest, proven the same way.

usage: python experiments/freeze_v2/migrate_to_canonical_digests.py
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rocketforge.core.freeze import (MANIFEST_ALGORITHM, RAW_BYTES_ALGORITHM,  # noqa: E402
                                     FrozenFile, canonical_bytes, manifest_text,
                                     overall_digest)

SOURCE = ROOT / "acceptance"
TARGET = ROOT / "tests" / "acceptance" / "freeze"
GROUPS = ("phase_5g", "fluids_foundation", "transport_line")
HISTORICAL = {"freeze_cea_provider_v1"}
DESCRIPTION_STEP_4 = ("4. SHA-256 each file's canonical text: its bytes with every "
                      "CRLF replaced by LF, nothing else changed")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def committed(relative: str) -> bytes:
    done = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{relative}"],
                          capture_output=True, check=True)
    return done.stdout


def prove(relative: str, recorded: str, width: int = 64) -> dict:
    raw = (ROOT / relative).read_bytes()
    if sha(raw)[:width] != recorded:
        raise SystemExit(f"{relative}: the recorded digest does not describe the bytes on disk")
    canonical = canonical_bytes(raw)
    if canonical != committed(relative):
        raise SystemExit(f"{relative}: the canonical text differs from the committed blob")
    return {"path": relative, "algorithm_1": recorded, "algorithm_2": sha(canonical),
            "crlf_on_disk": b"\r\n" in raw}


def write_pair(directory: Path, stem: str, payload: dict, files: list[FrozenFile]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{stem}.json").write_text(json.dumps(payload, indent=2) + "\n",
                                            encoding="utf-8", newline="\n")
    (directory / f"{stem}.sha256").write_text(manifest_text(files), encoding="utf-8",
                                              newline="")


record = {"from": RAW_BYTES_ALGORITHM, "to": MANIFEST_ALGORITHM, "manifests": []}
new_digests: dict[str, str] = {}

for group in GROUPS:
    for source in sorted((SOURCE / group).glob("freeze_*.json")):
        stem = source.stem
        if stem == "freeze_manifest":
            continue
        out = TARGET / group
        if stem in HISTORICAL:
            out.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, out / source.name)
            shutil.copyfile(source.with_suffix(".sha256"), out / f"{stem}.sha256")
            record["manifests"].append({"stem": stem, "kept": RAW_BYTES_ALGORITHM,
                                        "reason": "superseded history, copied unmodified"})
            continue
        old = json.loads(source.read_text(encoding="utf-8"))
        proofs = [prove(e["path"], e["sha256"]) for e in old["files"]]
        files = [FrozenFile(path=p["path"], sha256=p["algorithm_2"]) for p in proofs]
        new = dict(old)
        new["algorithm"] = MANIFEST_ALGORITHM
        new["files"] = [{"path": f.path, "sha256": f.sha256}
                        for f in sorted(files, key=lambda f: f.path)]
        new["digest"] = overall_digest(files)
        new["migrated_from"] = {"algorithm": RAW_BYTES_ALGORITHM, "digest": old["digest"]}
        write_pair(out, stem, new, files)
        new_digests[stem] = new["digest"]
        record["manifests"].append({"stem": stem, "algorithm_1_digest": old["digest"],
                                    "algorithm_2_digest": new["digest"], "files": proofs})

# Phase 4G: Compressible v1 as a full manifest.
table = (SOURCE / "phase_4g" / "ACCEPTANCE_MANIFEST.md").read_text(encoding="utf-8")
rows = re.findall(r"^\| `(rocketforge/[^`]+\.py)` \| `([0-9a-f]{16})` \|", table, re.M)
if len(rows) != 22:
    raise SystemExit(f"expected the 22 Phase 4G rows, found {len(rows)}")
proofs = [prove(path, prefix, width=16) for path, prefix in rows]
files = [FrozenFile(path=p["path"], sha256=p["algorithm_2"]) for p in proofs]
compressible = {
    "contract": "COMPRESSIBLE FLOW API",
    "version": "1.0",
    "algorithm": MANIFEST_ALGORITHM,
    "roots": ["rocketforge/physics/compressible", "rocketforge/core"],
    "note": ("Compressible v1 as frozen by Phase 4G. That record held 16-hex prefixes of "
             "raw-byte SHA-256 in a Markdown table; each was proven against the file "
             "before this full manifest replaced it."),
    "file_count": len(files),
    "files": [{"path": f.path, "sha256": f.sha256} for f in sorted(files, key=lambda f: f.path)],
    "digest": overall_digest(files),
    "migrated_from": {"record": "acceptance/phase_4g/ACCEPTANCE_MANIFEST.md",
                      "algorithm": "first 16 hex digits of SHA-256 over raw bytes"},
}
write_pair(TARGET / "phase_4g", "freeze_compressible_api_v1", compressible, files)
new_digests["freeze_compressible_api_v1"] = compressible["digest"]
record["manifests"].append({"stem": "freeze_compressible_api_v1",
                            "algorithm_1_digest": None,
                            "algorithm_2_digest": compressible["digest"], "files": proofs})

# The combined documents: algorithm, description, tracked paths, new digests.
for group in GROUPS:
    combined = json.loads((SOURCE / group / "freeze_manifest.json").read_text(encoding="utf-8"))
    combined["algorithm"] = MANIFEST_ALGORITHM
    if "algorithm_description" in combined:
        combined["algorithm_description"] = [
            DESCRIPTION_STEP_4 if line.startswith("4.") else line
            for line in combined["algorithm_description"]]
    combined["algorithm_history"] = (
        f"{RAW_BYTES_ALGORITHM} hashed raw bytes, so a CRLF working copy and a fresh "
        f"LF checkout disagreed; replaced by {MANIFEST_ALGORITHM} without re-freezing "
        f"anything (tests/acceptance/freeze/MIGRATION_V1_TO_V2.json)")
    contracts = combined["contracts"]
    items = contracts.values() if isinstance(contracts, dict) else contracts
    keys = list(contracts) if isinstance(contracts, dict) else [None] * len(contracts)
    for key, entry in zip(keys, items):
        stem = key or Path(entry.get("json", "")).stem or "freeze_line_api_v1"
        if stem in HISTORICAL:
            entry["algorithm"] = RAW_BYTES_ALGORITHM
        elif stem in new_digests:
            entry["digest"] = new_digests[stem]
        for field in ("json", "sha256_text"):
            if field in entry:
                entry[field] = entry[field].replace("acceptance/", "tests/acceptance/freeze/", 1)
    (TARGET / group / "freeze_manifest.json").write_text(
        json.dumps(combined, indent=2) + "\n", encoding="utf-8", newline="\n")

(TARGET / "MIGRATION_V1_TO_V2.json").write_text(json.dumps(record, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
proven = sum(len(m.get("files", [])) for m in record["manifests"])
print(f"migrated {len(new_digests)} manifests; {proven} files proven; "
      f"history kept: {sorted(HISTORICAL)}")
for stem, digest in sorted(new_digests.items()):
    print(f"  {stem}: {digest}")
