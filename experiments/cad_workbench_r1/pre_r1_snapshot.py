"""Preserve the current visual source before the CAD/CAE Workbench R1 program
runs anything destructive.

Mirrors experiments/ui_visual_pilot/baseline_snapshot.py's pattern (never
overwrite a file already captured) so a later claim about "what the shell
looked like before R1" is checkable against a SHA-256 manifest rather than
memory.

    python experiments/cad_workbench_r1/pre_r1_snapshot.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "acceptance" / "cad_workbench_r1" / "pre_r1"

TREES = ("ui/pages", "ui/components", "ui/theme", "ui/data",
         "ui/engine", "ui/shell", "ui/visuals")
EXTRA = ("ui/Main.qml",)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
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
            manifest.append({"path": rel.as_posix(), "sha256": sha256(target)})
    for name in EXTRA:
        path = ROOT / name
        if path.is_file():
            rel = path.relative_to(ROOT)
            target = OUT / "source" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(path, target)
            manifest.append({"path": rel.as_posix(), "sha256": sha256(target)})

    # frozen contract identities, recorded independently of the manifests
    # themselves so a later verification has something fixed to compare to
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

    # the component inventory this program depends on, recorded by digest so
    # a later step cannot silently redefine what "implemented" means
    inventory_path = ROOT / "acceptance" / "cad_workbench_r1" / "engine_component_inventory.json"
    inventory = None
    if inventory_path.is_file():
        inventory = {"path": inventory_path.relative_to(ROOT).as_posix(),
                     "sha256": sha256(inventory_path)}

    text = "".join(f"{row['sha256']}  {row['path']}\n" for row in manifest)
    report = {
        "purpose": "immutable pre-R1 snapshot of the UI source, before the "
                   "CAD/CAE Workbench R1 shell/theme/workspace redesign",
        "algorithm": "rocketforge-freeze-manifest/1",
        "file_count": len(manifest),
        "digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "files": manifest,
        "frozen_contracts": freezes,
        "component_inventory": inventory,
    }
    (OUT / "manifest.json").write_text(json.dumps(report, indent=2),
                                       encoding="utf-8")
    print(f"snapshot: {len(manifest)} files, digest {report['digest'][:16]}..., "
          f"{len(freezes)} frozen contracts recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
