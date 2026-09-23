"""Which RocketForge is this? One answer, captured once, read everywhere.

A packaged build carries a manifest, ``rocketforge_build.json``, written by
the build (``packaging/build_release.py``) before the application is packaged
and placed beside ``RocketForge.exe``. The executable reads its identity from
that file and nothing else: it never looks for git or a repository, so it
cannot be mistaken for whatever source happens to sit next to it.

A source run has no manifest. It asks git, if git and the repository are there,
and calls itself a development run -- never production, whatever the tree is.

Nothing else in RocketForge parses git or the manifest. The build writes the
manifest with :func:`capture`; the application reads it with
:func:`identity_for_process`; the package verifier reads it with
:func:`read_manifest`.

Vocabulary, as ``docs/engineering/release/BUILD_AND_LAUNCH.md`` defines it:

    production    packaged by the canonical build from a clean, committed tree
    development   a source run, or a package built from a tree that was not
    unknown       a package whose manifest is missing or unreadable: it is
                  never presented as current
"""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

__all__ = [
    "MANIFEST_NAME", "MANIFEST_SCHEMA", "PRODUCTION", "DEVELOPMENT", "UNKNOWN",
    "APPLICATION_PATHS", "BuildIdentity", "git_facts", "runtime_versions",
    "capture", "read_manifest", "identity_for_process",
]

MANIFEST_NAME = "rocketforge_build.json"
MANIFEST_SCHEMA = "rocketforge-build/1"

PRODUCTION = "production"
DEVELOPMENT = "development"
UNKNOWN = "unknown"

#: What the application is made of. A change here, committed or not, changes
#: what runs; a change anywhere else (tests, docs, experiments) does not, so it
#: does not make a build dirty.
APPLICATION_PATHS = ("main.py", "rocketforge", "ui", "assets", "packaging",
                     "build_exe.bat", "requirements.txt",
                     "requirements-thermochemistry.txt",
                     "requirements-fluids.txt")

#: Every key a manifest must carry.
MANIFEST_KEYS = ("schema", "product", "version", "commit", "describe", "branch",
                 "channel", "dirty", "build_timestamp_utc", "python", "pyside6",
                 "qt", "cea", "coolprop", "pyinstaller")


@dataclass(frozen=True)
class BuildIdentity:
    """The facts a user, a screenshot or a bug report can name a build by."""

    product: str
    version: str                 # the product version (main.APP_VERSION)
    commit: str                  # full SHA; "" when it cannot be established
    describe: str                # git describe, e.g. v0.1.0-25-g7cb6cd4
    branch: str
    channel: str                 # production | development | unknown
    packaged: bool
    dirty: bool | None           # None when it cannot be established
    build_timestamp_utc: str     # "" for a source run
    python: str
    pyside6: str
    qt: str
    cea: str
    coolprop: str

    @property
    def short_commit(self) -> str:
        return self.commit[:7]

    @property
    def build_id(self) -> str:
        """The one token to ask a user for: ``7cb6cd4``, ``7cb6cd4-dev``, ..."""
        if not self.commit or self.channel == UNKNOWN:
            return "unknown"
        token = self.short_commit
        if self.channel != PRODUCTION:
            token += "-dev"
        if self.dirty:
            token += "-dirty"
        return token

    @property
    def mode(self) -> str:
        return "packaged" if self.packaged else "source run"

    @property
    def is_current_candidate(self) -> bool:
        """Only a production package with a known, clean commit can be current."""
        return (self.packaged and self.channel == PRODUCTION
                and bool(self.commit) and self.dirty is False)

    def window_title(self, name: str) -> str:
        """A production package is just its name; anything else says what it is."""
        if self.is_current_candidate:
            return name
        if self.build_id == "unknown":
            return f"{name} [UNKNOWN BUILD]"
        return f"{name} [DEV {self.short_commit}{'-dirty' if self.dirty else ''}]"

    def summary(self) -> str:
        """The text the About panel shows and "Copy build info" copies."""
        lines = [
            f"{self.product} {self.version}",
            f"Build {self.build_id} · {self.channel} · {self.mode}",
            f"Commit {self.commit or 'unknown'}"
            + (f" ({self.describe})" if self.describe else ""),
        ]
        if self.build_timestamp_utc:
            lines.append(f"Built {self.build_timestamp_utc}")
        lines.append(f"Qt {self.qt} · PySide6 {self.pyside6} · Python {self.python}")
        providers = [f"NASA CEA {self.cea}" if self.cea else "NASA CEA not present",
                     f"CoolProp {self.coolprop}" if self.coolprop else "CoolProp not present"]
        lines.append(" · ".join(providers))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        data = asdict(self)
        data.update(build_id=self.build_id, mode=self.mode,
                    short_commit=self.short_commit)
        return data


def _git(repo: Path, *args: str) -> str | None:
    # A source run started through pythonw has no console; without this flag
    # each git call would flash one open.
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                              text=True, timeout=15, creationflags=flags)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def git_facts(repo: Path) -> dict:
    """Commit, describe, branch and dirty state of a checkout; blanks without git.

    Dirty means the application's own files (``APPLICATION_PATHS``) differ from
    the commit: modified, staged, deleted, or present but untracked. A change to
    the tests or the documentation does not change what runs, so it does not
    count.
    """
    commit = _git(repo, "rev-parse", "HEAD")
    if not commit:
        return {"commit": "", "describe": "", "branch": "", "dirty": None}
    status = _git(repo, "status", "--porcelain", "--untracked-files=all", "--",
                  *APPLICATION_PATHS)
    return {
        "commit": commit,
        "describe": _git(repo, "describe", "--tags", "--long", "--always") or "",
        "branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD") or "",
        "dirty": None if status is None else bool(status),
    }


def _distribution_version(*names: str) -> str:
    for name in names:
        try:
            return metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return ""


def runtime_versions() -> dict:
    """What this process runs on. Qt is asked, not assumed.

    The providers are read from their installed metadata, never imported: both
    are loaded lazily on purpose, so that RocketForge starts without them, and
    asking for a version must not change that.
    """
    try:
        import PySide6
        from PySide6.QtCore import qVersion
        pyside6, qt = PySide6.__version__, qVersion()
    except ImportError:
        pyside6, qt = "", ""
    return {"python": platform.python_version(), "pyside6": pyside6, "qt": qt,
            "cea": _distribution_version("cea"),
            "coolprop": _distribution_version("CoolProp", "coolprop")}


def capture(repo: Path, *, product: str, version: str, channel: str) -> dict:
    """The manifest for a build made now, from ``repo``, in this environment."""
    facts = git_facts(repo)
    return {
        "schema": MANIFEST_SCHEMA,
        "product": product,
        "version": version,
        **facts,
        "channel": channel,
        "build_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **runtime_versions(),
        "pyinstaller": _distribution_version("pyinstaller"),
    }


def read_manifest(path: Path) -> dict:
    """A manifest, validated. Raises ``ValueError`` rather than guessing."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"unreadable build manifest {path}: {error}") from error
    if not isinstance(data, dict) or data.get("schema") != MANIFEST_SCHEMA:
        raise ValueError(f"{path} is not a {MANIFEST_SCHEMA} manifest")
    missing = [key for key in MANIFEST_KEYS if key not in data]
    if missing:
        raise ValueError(f"{path} lacks {missing}")
    if data["channel"] not in (PRODUCTION, DEVELOPMENT):
        raise ValueError(f"{path} names an unknown channel {data['channel']!r}")
    if len(str(data["commit"])) != 40:
        raise ValueError(f"{path} does not name a full commit")
    return data


def identity_for_process(*, product: str, version: str, frozen: bool,
                         executable_dir: Path, source_root: Path) -> BuildIdentity:
    """This process's identity: from the manifest if packaged, else from git."""
    runtime = runtime_versions()
    if frozen:
        try:
            manifest = read_manifest(Path(executable_dir) / MANIFEST_NAME)
        except ValueError:
            runtime.update(cea="", coolprop="")
            return BuildIdentity(product=product, version=version, commit="",
                                 describe="", branch="", channel=UNKNOWN,
                                 packaged=True, dirty=None, build_timestamp_utc="",
                                 **runtime)
        # A package carries no provider metadata; the manifest records what the
        # build bundled. Python, PySide6 and Qt are the running ones.
        runtime.update(cea=manifest["cea"], coolprop=manifest["coolprop"])
        return BuildIdentity(
            product=product, version=version, commit=manifest["commit"],
            describe=manifest["describe"], branch=manifest["branch"],
            channel=manifest["channel"], packaged=True, dirty=manifest["dirty"],
            build_timestamp_utc=manifest["build_timestamp_utc"], **runtime)
    facts = git_facts(Path(source_root))
    return BuildIdentity(product=product, version=version, channel=DEVELOPMENT,
                         packaged=False, build_timestamp_utc="", **facts, **runtime)
