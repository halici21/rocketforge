"""Deterministic freeze manifests for stable scientific contracts.

A manifest records which files make up a frozen contract and what they
contained when it was frozen, in a form anyone can regenerate byte for byte.
That last part is the whole point, and it is where the Phase 4G manifest fell
short: its overall digest was produced by an algorithm the document did not
state, so the per-file hashes could be re-checked but the summary digest could
not be independently reconstructed.

What a digest protects: the **canonical source text** of each file, not the
bytes a particular working copy happens to hold. The repository stores text
with LF line endings (``.gitattributes``: ``* text=auto eol=lf``); a Windows
working copy may still hold CRLF, and a digest over those bytes would say a
file changed when nothing in it had. Algorithm 1 hashed raw bytes and did
exactly that: a fresh checkout disagreed with the working copy the manifests
were made from. Algorithm 2 hashes the canonical text.

The algorithm here is stated in full, implemented in one place, and verified by
a test that reimplements it from this docstring alone::

    1. Collect the files, each as a path relative to the repository root.
    2. Convert every path to POSIX form ("/" separators), so a manifest made on
       Windows and one made on Linux agree.
    3. Sort the relative paths lexicographically by their UTF-8 code points.
    4. For each, compute the SHA-256 of the file's canonical text: its bytes
       with every CRLF pair (0x0D 0x0A) replaced by LF (0x0A). Nothing else is
       changed -- no decoding, no trimming; a lone CR, trailing whitespace or a
       missing final newline all remain part of the content.
    5. Build the manifest text as, for each file in that order:

           "<64 lowercase hex digits><two spaces><relative posix path>\\n"

       That is the ``sha256sum`` line format, so ``sha256sum -c`` can check it
       against any checkout in the canonical form -- every fresh clone.
    6. Encode the manifest text as UTF-8.
    7. The overall digest is the SHA-256 of those bytes, lowercase hex.

Nothing else enters the digest: no timestamp, no machine name, no absolute
path, no file size, no ordering other than the sorted one. Two checkouts of the
same commit produce the same digest on any platform, whatever line endings the
working copy holds.

A manifest records the algorithm it was made with, and is verified with that
algorithm: a superseded algorithm-1 manifest stays a readable historical record.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

__all__ = [
    "MANIFEST_ALGORITHM",
    "RAW_BYTES_ALGORITHM",
    "ALGORITHM_DESCRIPTION",
    "FrozenFile",
    "FreezeManifest",
    "canonical_bytes",
    "file_digest",
    "manifest_text",
    "overall_digest",
    "build_manifest",
    "verify_manifest",
]

#: The identifier recorded in every manifest, so a change of algorithm is a
#: visible version change rather than a silent difference.
MANIFEST_ALGORITHM = "rocketforge-freeze-manifest/2"

#: The superseded algorithm: SHA-256 of a file's raw bytes. Kept so a manifest
#: made with it can still be read and checked for what it recorded.
RAW_BYTES_ALGORITHM = "rocketforge-freeze-manifest/1"

#: The algorithm in seven lines, as the combined freeze records state it. The
#: generators write it from here, so no record can describe a different rule.
ALGORITHM_DESCRIPTION = (
    "1. collect the files, each relative to the repository root",
    "2. convert each path to POSIX form",
    "3. sort the relative paths lexicographically by UTF-8 code point",
    "4. SHA-256 each file's canonical text: its bytes with every CRLF "
    "replaced by LF, nothing else changed",
    "5. one line per file: '<hex><two spaces><path>\\n'",
    "6. encode that text as UTF-8",
    "7. the overall digest is the SHA-256 of those bytes",
)


def canonical_bytes(data: bytes) -> bytes:
    """The canonical text of a file: every CRLF pair replaced by LF, nothing else."""
    return data.replace(b"\r\n", b"\n")


def file_digest(path: Path, algorithm: str = MANIFEST_ALGORITHM) -> str:
    """SHA-256 of a file's canonical text (algorithm 2), lowercase hex.

    Read as bytes, never decoded: the only transformation is the CRLF -> LF one
    the repository itself applies. ``RAW_BYTES_ALGORITHM`` hashes the raw bytes,
    for checking a manifest that was made that way.
    """
    data = path.read_bytes()
    if algorithm == MANIFEST_ALGORITHM:
        data = canonical_bytes(data)
    elif algorithm != RAW_BYTES_ALGORITHM:
        raise ValueError(f"unknown freeze-manifest algorithm {algorithm!r}")
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True, slots=True)
class FrozenFile:
    """One file in a frozen contract."""

    path: str          # relative, POSIX separators
    sha256: str

    def line(self) -> str:
        """The manifest line for this file, in ``sha256sum`` format."""
        return f"{self.sha256}  {self.path}\n"


def manifest_text(files: Sequence[FrozenFile]) -> str:
    """The canonical text whose SHA-256 is the overall digest.

    Sorted by relative path, one ``sha256sum``-format line each. This function
    is the single definition of that layout; every producer and checker goes
    through it, so they cannot drift apart.
    """
    return "".join(entry.line() for entry in
                   sorted(files, key=lambda entry: entry.path))


def overall_digest(files: Sequence[FrozenFile]) -> str:
    """SHA-256 of the UTF-8 encoded canonical manifest text."""
    return hashlib.sha256(manifest_text(files).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class FreezeManifest:
    """A frozen contract: what it covers, and what it contained."""

    contract: str
    version: str
    files: tuple[FrozenFile, ...]
    algorithm: str = MANIFEST_ALGORITHM
    note: str = ""

    @property
    def digest(self) -> str:
        return overall_digest(self.files)

    @property
    def text(self) -> str:
        return manifest_text(self.files)

    def to_dict(self) -> dict:
        """A JSON-shaped record. Free of absolute paths and timestamps.

        A timestamp would make two manifests of identical content differ, which
        would defeat the purpose; the commit that carries the manifest is the
        record of when it was made.
        """
        return {
            "contract": self.contract,
            "version": self.version,
            "algorithm": self.algorithm,
            "note": self.note,
            "file_count": len(self.files),
            "files": [{"path": entry.path, "sha256": entry.sha256}
                      for entry in sorted(self.files,
                                          key=lambda e: e.path)],
            "digest": self.digest,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "FreezeManifest":
        return cls(
            contract=payload["contract"],
            version=payload["version"],
            algorithm=payload.get("algorithm", RAW_BYTES_ALGORITHM),
            note=payload.get("note", ""),
            files=tuple(FrozenFile(path=entry["path"], sha256=entry["sha256"])
                        for entry in payload["files"]),
        )


def build_manifest(contract: str, version: str, root: Path,
                   paths: Iterable[Path], *, note: str = "") -> FreezeManifest:
    """Hash each file and assemble a manifest, with the current algorithm.

    ``paths`` may be absolute or relative; each is recorded relative to
    ``root`` in POSIX form, so the manifest carries no machine-specific text.
    """
    root = root.resolve()
    entries = []
    seen: set[str] = set()
    for path in paths:
        absolute = (path if path.is_absolute() else root / path).resolve()
        relative = PurePosixPath(absolute.relative_to(root).as_posix())
        if str(relative) in seen:
            raise ValueError(f"{relative} appears twice in the manifest")
        seen.add(str(relative))
        entries.append(FrozenFile(path=str(relative),
                                  sha256=file_digest(absolute)))
    return FreezeManifest(contract=contract, version=version,
                          files=tuple(entries), note=note)


def verify_manifest(manifest: FreezeManifest, root: Path) -> dict:
    """Re-hash every file, with the manifest's own algorithm, and report.

    Reports missing files and changed files separately: a file that was deleted
    and one that was edited are different problems with different answers.
    """
    root = root.resolve()
    missing, changed, present = [], [], []
    for entry in manifest.files:
        path = root / entry.path
        if not path.is_file():
            missing.append(entry.path)
            continue
        actual = file_digest(path, manifest.algorithm)
        present.append(FrozenFile(path=entry.path, sha256=actual))
        if actual != entry.sha256:
            changed.append({"path": entry.path,
                            "recorded": entry.sha256, "actual": actual})

    recomputed = overall_digest(present) if not missing else None
    return {
        "contract": manifest.contract,
        "version": manifest.version,
        "algorithm": manifest.algorithm,
        "files": len(manifest.files),
        "missing": missing,
        "changed": changed,
        "recorded_digest": manifest.digest,
        "recomputed_digest": recomputed,
        "digest_matches": (not missing and not changed
                           and recomputed == manifest.digest),
        "verdict": "PASS" if (not missing and not changed) else "FAIL",
    }


def write_manifest(manifest: FreezeManifest, directory: Path,
                   stem: str) -> tuple[Path, Path]:
    """Write the JSON record and the checkable ``sha256sum`` text beside it."""
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{stem}.json"
    text_path = directory / f"{stem}.sha256"
    json_path.write_text(json.dumps(manifest.to_dict(), indent=2),
                         encoding="utf-8")
    # newline="" so the exact bytes hashed are the exact bytes written.
    text_path.write_text(manifest.text, encoding="utf-8", newline="")
    return json_path, text_path
