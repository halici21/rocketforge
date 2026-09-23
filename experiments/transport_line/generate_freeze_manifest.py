"""Freeze manifest for LINE API v1.0.

Same algorithm as every other contract in this repository,
``rocketforge.core.freeze``'s current one (``rocketforge-freeze-manifest/2``).
Production ``.py`` only: no test, no harness, no artifact, no QML.

This script freezes exactly one contract and touches no other, which is the
lesson from the transport/line opening gates, where running an older
generator against a moved tree overwrote a superseded manifest.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rocketforge.core.freeze import (  # noqa: E402
    MANIFEST_ALGORITHM,
    FrozenFile,
    file_digest,
    manifest_text,
    overall_digest,
)

#: Tracked beside the tests that verify it (it was the untracked acceptance/).
OUT = ROOT / "tests" / "acceptance" / "freeze" / "transport_line"
OUT.mkdir(parents=True, exist_ok=True)
ROOTS = ["rocketforge/engineering/line"]

files = []
for relative in ROOTS:
    for path in sorted((ROOT / relative).rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        files.append(FrozenFile(
            path=path.relative_to(ROOT).as_posix(),
            sha256=file_digest(path)))      # the one implementation of the rule

digest = overall_digest(files)
record = {
    "contract": "LINE API",
    "version": "1.0",
    "algorithm": MANIFEST_ALGORITHM,
    "roots": ROOTS,
    "note": ("straight circular single-phase liquid line: Darcy friction "
             "factor and distributed wall friction. Gated on the methane "
             "transport validation."),
    "excluded": ["tests", "acceptance harnesses", "QML", "artifacts",
                 "__pycache__"],
    "file_count": len(files),
    "digest": digest,
    "files": [{"path": f.path, "sha256": f.sha256} for f in files],
}
(OUT / "freeze_line_api_v1.json").write_text(json.dumps(record, indent=2),
                                             encoding="utf-8")
(OUT / "freeze_line_api_v1.sha256").write_text(manifest_text(files),
                                               encoding="utf-8", newline="")
(OUT / "freeze_manifest.json").write_text(json.dumps({
    "purpose": "the line freeze boundary",
    "algorithm": MANIFEST_ALGORITHM,
    "reproducible_without_this_code": True,
    "checkable_with": "sha256sum -c freeze_line_api_v1.sha256",
    "python": f"{sys.version_info.major}.{sys.version_info.minor}."
              f"{sys.version_info.micro}",
    "contracts": [{"contract": "LINE API", "version": "1.0",
                   "file_count": len(files), "digest": digest}],
}, indent=2), encoding="utf-8")

print(f"LINE API v1.0: {len(files)} files, digest {digest}")

# mutation proof: one byte changes the file hash and the overall digest
probe = list(files)
probe[0] = FrozenFile(path=probe[0].path,
                      sha256=hashlib.sha256(b"x").hexdigest())
mutated = overall_digest(probe)
print(f"one-byte mutation changes the digest: {mutated != digest}")
