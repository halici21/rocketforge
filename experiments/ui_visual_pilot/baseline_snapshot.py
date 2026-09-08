"""Preserve the current visual source before anything destructive runs.

The previous program lost its only copy of the pre-pilot interface because
dist/ was deleted for a clean rebuild and dist/ was where that copy lived. This
writes an immutable snapshot into the acceptance tree instead, with a SHA-256
manifest so a later claim about "what the source looked like" is checkable.

    python experiments/ui_visual_pilot/baseline_snapshot.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "acceptance" / "ui_rollout" / "baseline_snapshot"

# every QML tree under ui/. The first version listed four of the seven
# and the snapshot would not even load.
TREES = ("ui/pages", "ui/components", "ui/theme", "ui/data",
         "ui/engine", "ui/shell", "ui/visuals")
EXTRA = ("ui/Main.qml",)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    # Extend rather than refuse: the first snapshot was incomplete (it listed
    # four of the seven QML trees and would not load). Files already captured
    # are never overwritten, so nothing recorded before this run can change.
    OUT.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for tree in TREES:
        source = ROOT / tree
        if not source.is_dir():
            continue
        for path in sorted(source.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            rel = path.relative_to(ROOT)
            target = OUT / "source" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(path, target)
            manifest.append({"path": rel.as_posix(),
                             "sha256": sha256(target)})
    for name in EXTRA:
        path = ROOT / name
        if path.is_file():
            rel = path.relative_to(ROOT)
            target = OUT / "source" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(path, target)
            manifest.append({"path": rel.as_posix(),
                             "sha256": sha256(target)})

    # the accepted pilot's own evidence, so it survives any later rebuild
    pilot = ROOT / "acceptance" / "ui_visual_pilot"
    for name in ("scientific_parity.json", "accessibility.json",
                 "performance_after.json", "performance_before.json",
                 "source_packaged_parity.json", "ACCEPTANCE_MANIFEST.md"):
        path = pilot / name
        if path.is_file():
            shutil.copy2(path, OUT / f"pilot_{name}")
    captures = OUT / "pilot_captures"
    captures.mkdir(exist_ok=True)
    for label in ("before", "after"):
        source = pilot / label
        if source.is_dir():
            shutil.copytree(source, captures / label, dirs_exist_ok=True)

    # frozen contract identities, so a later verification has something to
    # compare against that does not depend on the manifests themselves
    freezes = []
    for path in sorted((ROOT / "acceptance").rglob("freeze_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not data.get("files"):
            continue
        freezes.append({"manifest": path.relative_to(ROOT).as_posix(),
                        "contract": data.get("contract"),
                        "version": data.get("version"),
                        "digest": data.get("digest"),
                        "file_count": data.get("file_count")})

    text = "".join(f"{row['sha256']}  {row['path']}\n" for row in manifest)
    report = {
        "purpose": "immutable pre-rollout snapshot of the visual source",
        "algorithm": "rocketforge-freeze-manifest/1",
        "file_count": len(manifest),
        "digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "files": manifest,
        "frozen_contracts": freezes,
    }
    (OUT / "manifest.json").write_text(json.dumps(report, indent=2),
                                       encoding="utf-8")
    print(f"snapshot: {len(manifest)} files, digest {report['digest'][:16]}..., "
          f"{len(freezes)} frozen contracts recorded")
    print(f"          {len(list(captures.rglob('*.png')))} pilot captures kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
