"""The package verifier must be able to fail.

packaging/verify_package.py decides whether dist/RocketForge is the canonical
build of a commit. A check that cannot fail proves nothing, so each failure it
exists for is produced here on purpose: a stale commit, a development or dirty
package, a parallel build beside the canonical one, an extra executable, a
PySide6 other than the pin, a missing manifest.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from rocketforge.application import build_identity as bi

ROOT = Path(__file__).resolve().parents[1]
COMMIT_A = "a" * 40
COMMIT_B = "b" * 40


def manifest(**overrides) -> dict:
    data = {"schema": bi.MANIFEST_SCHEMA, "product": "RocketForge", "version": "0.1.0",
            "commit": COMMIT_A, "describe": "v0.1.0-3-gaaaaaaa", "branch": "master",
            "channel": bi.PRODUCTION, "dirty": False,
            "build_timestamp_utc": "2026-09-24T00:00:00Z", "python": "3.13.2",
            "pyside6": "6.10.2", "qt": "6.10.2", "cea": "3.3.4", "coolprop": "8.0.0",
            "pyinstaller": "6.22.2"}
    data.update(overrides)
    return data


def verifier():
    path = ROOT / "packaging" / "verify_package.py"
    spec = importlib.util.spec_from_file_location("verify_package", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_package(dist: Path, data: dict) -> Path:
    package = dist / "RocketForge"
    (package / "_internal").mkdir(parents=True)
    (package / "RocketForge.exe").write_bytes(b"MZ not a real executable")
    (package / bi.MANIFEST_NAME).write_text(json.dumps(data), encoding="utf-8")
    return package


def test_the_verifier_accepts_the_commit_it_was_built_from(tmp_path):
    vp = verifier()
    package = fake_package(tmp_path / "dist", manifest())
    assert vp.check_layout(package) == []
    failures, loaded = vp.check_manifest(package, COMMIT_A)
    assert failures == [] and loaded["commit"] == COMMIT_A


def test_the_verifier_calls_a_package_of_another_commit_stale(tmp_path):
    vp = verifier()
    package = fake_package(tmp_path / "dist", manifest())
    failures, _ = vp.check_manifest(package, COMMIT_B)
    assert any("stale" in failure for failure in failures), failures


def test_the_verifier_refuses_a_development_or_dirty_package_as_canonical(tmp_path):
    vp = verifier()
    package = fake_package(tmp_path / "dist", manifest(channel=bi.DEVELOPMENT, dirty=True))
    failures, _ = vp.check_manifest(package, COMMIT_A)
    assert len(failures) == 2, failures
    assert vp.check_manifest(package, COMMIT_A, allow_development=True)[0] == []


def test_the_verifier_refuses_parallel_builds_and_extra_executables(tmp_path):
    vp = verifier()
    package = fake_package(tmp_path / "dist", manifest())
    (tmp_path / "dist" / "RocketForge_old").mkdir()
    (package / "RocketForge_final.exe").write_bytes(b"MZ")
    failures = vp.check_layout(package)
    assert any("other RocketForge builds" in f for f in failures), failures
    assert any("only RocketForge.exe" in f for f in failures), failures


def test_the_verifier_refuses_a_pyside6_other_than_the_pin(tmp_path):
    vp = verifier()
    assert vp.pinned(ROOT / "requirements.txt", "PySide6-Essentials") == "6.10.2"
    pins = {"pyside6": vp.pinned(ROOT / "requirements.txt", "PySide6-Essentials"),
            "cea": vp.pinned(ROOT / "requirements-thermochemistry.txt", "cea"),
            "coolprop": vp.pinned(ROOT / "requirements-fluids.txt", "CoolProp")}
    assert vp.check_pins(manifest(**pins), ROOT) == []
    failures = vp.check_pins(manifest(**{**pins, "pyside6": "6.11.2"}), ROOT)
    assert len(failures) == 1 and "6.11.2" in failures[0]


def test_the_verifier_reports_a_missing_manifest(tmp_path):
    vp = verifier()
    package = fake_package(tmp_path / "dist", manifest())
    (package / bi.MANIFEST_NAME).unlink()
    failures, loaded = vp.check_manifest(package, COMMIT_A)
    assert loaded is None and failures
