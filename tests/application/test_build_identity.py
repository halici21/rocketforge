"""Which RocketForge is running must always have one answer.

A source run names its commit and calls itself development; a package names
the commit in its manifest and nothing else; a package with no readable
manifest is an unknown build and is never presented as current.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from rocketforge.application import build_identity as bi

ROOT = Path(__file__).resolve().parents[2]
COMMIT_A = "a" * 40


def git_available() -> bool:
    return shutil.which("git") is not None and (ROOT / ".git").exists()


def manifest(**overrides) -> dict:
    data = {"schema": bi.MANIFEST_SCHEMA, "product": "RocketForge", "version": "0.1.0",
            "commit": COMMIT_A, "describe": "v0.1.0-3-gaaaaaaa", "branch": "master",
            "channel": bi.PRODUCTION, "dirty": False,
            "build_timestamp_utc": "2026-09-24T00:00:00Z", "python": "3.13.2",
            "pyside6": "6.10.2", "qt": "6.10.2", "cea": "3.3.4", "coolprop": "8.0.0",
            "pyinstaller": "6.22.2"}
    data.update(overrides)
    return data


def packaged(folder: Path, data=None) -> bi.BuildIdentity:
    folder.mkdir(parents=True, exist_ok=True)
    if data is not None:
        (folder / bi.MANIFEST_NAME).write_text(
            data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return bi.identity_for_process(product="RocketForge", version="0.1.0", frozen=True,
                                   executable_dir=folder, source_root=ROOT)


# ---------------------------------------------------------------------------
# the identity a process reports
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not git_available(), reason="needs git and the repository")
def test_a_source_run_names_the_checkout_commit_and_is_development():
    identity = bi.identity_for_process(product="RocketForge", version="0.1.0",
                                       frozen=False, executable_dir=ROOT, source_root=ROOT)
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    assert identity.commit == head
    assert identity.channel == bi.DEVELOPMENT and not identity.packaged
    assert identity.build_id.startswith(head[:7] + "-dev")
    assert identity.window_title("RocketForge").startswith("RocketForge [DEV ")
    assert not identity.is_current_candidate
    assert "source run" in identity.summary()


def test_a_package_reads_its_manifest_and_not_the_repository(tmp_path):
    identity = packaged(tmp_path, manifest())
    # the repository beside it is at another commit; the package does not care
    assert identity.commit == COMMIT_A and identity.packaged
    assert identity.channel == bi.PRODUCTION and identity.build_id == "aaaaaaa"
    assert identity.window_title("RocketForge") == "RocketForge"
    assert identity.is_current_candidate
    assert identity.cea == "3.3.4" and identity.coolprop == "8.0.0"   # from the manifest


def test_a_package_without_a_manifest_is_unknown_and_never_current(tmp_path):
    identity = packaged(tmp_path)
    assert identity.build_id == "unknown" and identity.channel == bi.UNKNOWN
    assert identity.window_title("RocketForge") == "RocketForge [UNKNOWN BUILD]"
    assert not identity.is_current_candidate


@pytest.mark.parametrize("broken", [
    "not json",
    json.dumps({"schema": "something-else"}),
    json.dumps(manifest(commit="abc123")),
    json.dumps(manifest(channel="nightly")),
    json.dumps({k: v for k, v in manifest().items() if k != "dirty"}),
])
def test_a_malformed_manifest_is_refused_and_the_package_is_unknown(tmp_path, broken):
    with pytest.raises(ValueError):
        (tmp_path / bi.MANIFEST_NAME).write_text(broken, encoding="utf-8")
        bi.read_manifest(tmp_path / bi.MANIFEST_NAME)
    assert packaged(tmp_path / "pkg", broken).build_id == "unknown"


def test_a_development_or_dirty_package_says_so(tmp_path):
    development = packaged(tmp_path / "dev", manifest(channel=bi.DEVELOPMENT))
    assert development.window_title("RocketForge") == "RocketForge [DEV aaaaaaa]"
    assert development.build_id == "aaaaaaa-dev"
    dirty = packaged(tmp_path / "dirty", manifest(channel=bi.DEVELOPMENT, dirty=True))
    assert dirty.build_id == "aaaaaaa-dev-dirty" and not dirty.is_current_candidate
    assert dirty.window_title("RocketForge") == "RocketForge [DEV aaaaaaa-dirty]"


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_dirty_means_the_application_changed_not_the_docs(tmp_path):
    def run(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True,
                       capture_output=True)

    run("init", "-q")
    run("config", "user.email", "t@example.invalid")
    run("config", "user.name", "t")
    (tmp_path / "main.py").write_text("print(1)\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("a\n", encoding="utf-8")
    run("add", ".")
    run("commit", "-q", "-m", "one")
    assert bi.git_facts(tmp_path)["dirty"] is False
    (tmp_path / "docs" / "a.md").write_text("b\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("scratch\n", encoding="utf-8")
    assert bi.git_facts(tmp_path)["dirty"] is False          # not the application
    (tmp_path / "ui").mkdir()
    (tmp_path / "ui" / "New.qml").write_text("Item {}\n", encoding="utf-8")
    assert bi.git_facts(tmp_path)["dirty"] is True           # an untracked view counts
    (tmp_path / "ui" / "New.qml").unlink()
    (tmp_path / "main.py").write_text("print(2)\n", encoding="utf-8")
    assert bi.git_facts(tmp_path)["dirty"] is True


@pytest.mark.skipif(not git_available(), reason="needs git and the repository")
def test_a_captured_manifest_is_one_the_package_can_read(tmp_path):
    data = bi.capture(ROOT, product="RocketForge", version="0.1.0", channel=bi.PRODUCTION)
    (tmp_path / bi.MANIFEST_NAME).write_text(json.dumps(data), encoding="utf-8")
    assert bi.read_manifest(tmp_path / bi.MANIFEST_NAME)["commit"] == data["commit"]
