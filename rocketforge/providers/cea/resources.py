"""Locating and identifying the thermodynamic database CEA actually used.

One owner for resource discovery, so that ``thermo.lib`` is never searched for
in two places with two answers (5C brief §153).

The requirement this serves: a chemistry result is reproducible only if the
data behind it is identified. Phase 5B's ``ThermochemistryProvenance`` has a
``database_sha256`` field; this module is what fills it, and it must fill it
with the file the solve **actually used**, not a convenient copy found
elsewhere on the machine.

Frozen builds are the case that makes this non-trivial. Under PyInstaller the
package is unpacked beneath ``sys._MEIPASS``, so a path derived from the source
tree would be wrong -- and wrong only in the shipped executable, which is the
worst place to find out. The discovery here derives the path from the imported
``cea`` module itself, which is correct in both worlds by construction, and
records which world it was.
"""

from __future__ import annotations

import hashlib
import pathlib
import sys
from dataclasses import dataclass
from types import ModuleType

__all__ = ["CEAResources", "discover_resources"]

#: Read in blocks rather than whole: thermo.lib is only ~600 kB today, but a
#: hashing helper that assumes a small file is a trap for the day it is not.
_BLOCK = 1 << 20


@dataclass(frozen=True, slots=True)
class CEAResources:
    """Where CEA's data lives, and what it contains.

    Attributes:
        package_dir: The imported package's directory.
        thermo_path: The thermodynamic database actually loaded.
        thermo_sha256: Its content hash, or ``""`` if the file is unreadable.
        thermo_bytes: Its size.
        trans_path: The transport database, when present.
        trans_sha256: Its hash.
        frozen: Whether this is a PyInstaller bundle.
        meipass: The bundle root, when frozen.
    """

    package_dir: str
    thermo_path: str
    thermo_sha256: str
    thermo_bytes: int
    trans_path: str = ""
    trans_sha256: str = ""
    frozen: bool = False
    meipass: str = ""

    @property
    def thermo_short(self) -> str:
        """First 16 hex characters of the database hash, for display."""
        return self.thermo_sha256[:16]

    @property
    def is_identified(self) -> bool:
        """Whether the database was found and hashed."""
        return bool(self.thermo_sha256)


def _sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(_BLOCK):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def discover_resources(cea_module: ModuleType) -> CEAResources:
    """Find the data files belonging to an imported ``cea`` module.

    Derived from ``cea.__file__`` rather than from any RocketForge path. The
    provider does not tell CEA where its data is, and it does not guess: it
    asks the module where *it* lives and looks beside it. That is the same
    answer in a source tree and in a frozen bundle, which is why this works in
    both without a branch on ``sys.frozen``.
    """
    package_dir = pathlib.Path(cea_module.__file__).resolve().parent
    frozen = bool(getattr(sys, "frozen", False))
    meipass = str(getattr(sys, "_MEIPASS", "") or "")

    thermo = package_dir / "data" / "thermo.lib"
    trans = package_dir / "data" / "trans.lib"

    thermo_sha = _sha256(thermo) if thermo.is_file() else ""
    thermo_size = thermo.stat().st_size if thermo.is_file() else 0
    trans_sha = _sha256(trans) if trans.is_file() else ""

    return CEAResources(
        package_dir=str(package_dir),
        thermo_path=str(thermo),
        thermo_sha256=thermo_sha,
        thermo_bytes=thermo_size,
        trans_path=str(trans) if trans.is_file() else "",
        trans_sha256=trans_sha,
        frozen=frozen,
        meipass=meipass,
    )
