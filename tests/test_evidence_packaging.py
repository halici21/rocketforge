"""The package carries the shipped evidence corpus exactly, and the verifier can tell.

Checked on a made-up package tree: the real ``rocketforge/data/evidence`` and
the Propulsion Database pages copied under ``_internal``, then broken one way
at a time -- a fixture slipped in, a file edited, a record missing, a value its
source withholds, an execution action added to a page, a tests folder packaged.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packaging"))
import verify_package  # noqa: E402

SOURCE = ROOT / "rocketforge" / "data" / "evidence"


@pytest.fixture()
def package(tmp_path):
    internal = tmp_path / "RocketForge" / "_internal"
    shutil.copytree(SOURCE, internal / "rocketforge" / "data" / "evidence")
    pages = internal / "ui" / "pages"
    pages.mkdir(parents=True)
    shutil.copy(ROOT / "ui" / "pages" / "PropulsionEvidencePage.qml", pages)
    shutil.copytree(ROOT / "ui" / "pages" / "propulsionevidence", pages / "propulsionevidence")
    return tmp_path / "RocketForge"


def evidence(package):
    return package / "_internal" / "rocketforge" / "data" / "evidence"


def test_an_exact_copy_passes(package):
    assert verify_package.check_evidence(package, ROOT) == []


def test_a_packaged_fixture_is_named(package):
    (evidence(package) / "records" / "DS-TEST.json").write_text("{}", encoding="utf-8")
    failures = verify_package.check_evidence(package, ROOT)
    assert any("DS-TEST.json is packaged but is not shipped evidence" in f for f in failures)


def test_an_edited_or_missing_file_is_named(package):
    record = evidence(package) / "records" / "DS-RP1311-E5.json"
    record.write_text(record.read_text(encoding="utf-8").replace("0.7206", "0.7207"), encoding="utf-8")
    assert any("differs from the source tree" in f
               for f in verify_package.check_evidence(package, ROOT))
    record.unlink()
    failures = verify_package.check_evidence(package, ROOT)
    assert any("records/DS-RP1311-E5.json is missing" in f for f in failures)
    assert any("required record DS-RP1311-E5" in f for f in failures)


def test_a_value_its_source_withholds_fails_to_load(package):
    registry = evidence(package) / "sources.json"
    data = json.loads(registry.read_text(encoding="utf-8"))
    for source in data["sources"]:
        source["shipping"] = "METADATA_ONLY"
    registry.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    failures = verify_package.check_evidence(package, ROOT)
    assert any("does not load" in f and "METADATA_ONLY" in f for f in failures)


def test_the_reference_engine_seed_corpus_is_packaged_and_must_load(package):
    corpus = evidence(package) / "engines" / "reference_engines.json"
    assert corpus.is_file() and verify_package.check_evidence(package, ROOT) == []
    data = json.loads(corpus.read_text(encoding="utf-8"))
    data["assertions"][0]["status"] = "INFERRED"
    corpus.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    failures = verify_package.check_evidence(package, ROOT)
    assert any("engines/reference_engines.json differs from the source tree" in f for f in failures)
    assert any("reference-engine corpus does not load" in f and "INFERRED" in f for f in failures)
    corpus.unlink()
    failures = verify_package.check_evidence(package, ROOT)
    assert any("engines/reference_engines.json is missing" in f for f in failures)


def test_an_execution_action_on_the_pages_is_named(package):
    folder = package / "_internal" / "ui" / "pages" / "propulsionevidence"
    inspector = folder / "EvidenceInspector.qml"
    inspector.write_text(inspector.read_text(encoding="utf-8") + "\n// calculate(\n",
                         encoding="utf-8")
    assert any("EvidenceInspector.qml carries 'calculate('" in f
               for f in verify_package.check_evidence(package, ROOT))


def test_open_in_thermochemistry_is_named_outside_its_post_check_gate(package):
    """EV-3's action lives in the record view behind canOpenInThermochemistry;
    anywhere else, or ungated, the package is refused."""
    folder = package / "_internal" / "ui" / "pages" / "propulsionevidence"
    inspector = folder / "EvidenceInspector.qml"
    inspector.write_text(inspector.read_text(encoding="utf-8") + "\n// Open in Thermochemistry\n",
                         encoding="utf-8")
    assert any("EvidenceInspector.qml carries 'Open in Thermochemistry'" in f
               for f in verify_package.check_evidence(package, ROOT))
    record = folder / "EvidenceRecord.qml"
    record.write_text(record.read_text(encoding="utf-8").replace(
        "active: PropulsionEvidence.canOpenInThermochemistry", "active: true"), encoding="utf-8")
    assert any("EvidenceRecord.qml carries 'Open in Thermochemistry' outside" in f
               for f in verify_package.check_evidence(package, ROOT))


def test_a_packaged_tests_folder_is_named(package):
    (package / "_internal" / "tests").mkdir()
    assert any("tests/ folder" in f for f in verify_package.check_evidence(package, ROOT))


def test_the_spec_packages_the_evidence_folder_and_nothing_under_tests():
    spec = (ROOT / "packaging" / "RocketForge.spec").read_text(encoding="utf-8")
    assert 'EVIDENCE_DIR = os.path.join(ROOT, "rocketforge", "data", "evidence")' in spec
    assert '(EVIDENCE_DIR, os.path.join("rocketforge", "data", "evidence"))' in spec
    assert "tests" not in [part for line in spec.splitlines() if "datas" in line
                           for part in line.replace('"', " ").split()]


def test_the_package_smoke_opens_the_propulsion_database():
    assert "page:evidence" in verify_package.EVIDENCE_ROUTE
    assert "DS-RP1311-E5" in verify_package.EVIDENCE_REQUIRED
    shipped = {p.stem for p in (SOURCE / "records").glob("*.json")}
    assert set(verify_package.EVIDENCE_REQUIRED) == shipped

def test_the_package_smoke_runs_the_explicit_cea_check_without_solving():
    route = verify_package.EVIDENCE_CEA_ROUTE.split(",")
    assert route.index("evselect:DS-RP1311-E5") < route.index("evcheck") < route.index("evopen")
    assert route[route.index("evopen") + 1] == "expectthermo:unsolved"


def test_the_package_smoke_visits_every_shock_section():
    route = verify_package.SHOCK_ROUTE
    for page in ("page:normalshock", "page:obliqueshock"):
        section = route.split(page, 1)[1].split("page:", 1)[0]
        assert all(f"section:{n}" in section for n in range(3)), page
