"""DB-2A catalog: a read-only, deterministic, solver-free view of the shipped seed corpus."""

from __future__ import annotations

import ast
import dataclasses
import json
import pathlib
import shutil
import socket
import subprocess
import sys

import pytest

from rocketforge.application.analysis import reference_engine_catalog as catalog_module
from rocketforge.application.analysis.reference_engine_catalog import (
    load_reference_engines,
    reference_engine_path,
)
from rocketforge.evidence import EvidenceError, Missing
from rocketforge.evidence.engines import SubjectKind
from rocketforge.evidence.engines.capabilities import Capability, CapabilityStatus

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE = ROOT / "rocketforge" / "application" / "analysis" / "reference_engine_catalog.py"


@pytest.fixture(scope="module")
def catalog():
    return load_reference_engines()


def test_the_catalog_lists_every_shipped_configuration(catalog):
    entries = catalog.entries()
    assert [e.configuration_id for e in entries] == sorted(c.configuration_id for c in catalog.corpus.configurations)
    assert {"CFG-J2-230K", "CFG-RL10A-3-3A", "CFG-SPS-BLOCK-I"} <= {e.configuration_id for e in entries}
    j2 = catalog.entry("CFG-J2-230K")
    assert (j2.designation, j2.family_name) == ("J-2", "J-2")
    assert [p.operating_point_id for p in j2.operating_points] == ["OP-J2-230K-MR55"]
    assert isinstance(j2.effective, Missing)


def test_names_find_exactly_what_is_recorded(catalog):
    assert [e.configuration_id for e in catalog.find("J-2")] == ["CFG-J2-230K", "CFG-J2S"]  # the J-2 family
    assert [e.configuration_id for e in catalog.find("J-2S")] == ["CFG-J2S"]
    assert [e.configuration_id for e in catalog.find("sps engine")] == ["CFG-SPS-BLOCK-I"]
    assert [e.configuration_id for e in catalog.find("RL10")] == ["CFG-RL10A-3-3A", "CFG-RL10B-2-DIV"]
    assert [e.configuration_id for e in catalog.find("RD-170")] == ["CFG-RD-170"]
    assert catalog.find("RL10A-4-2") == () and catalog.find("Rutherford") == ()  # Wave 2: rights, nothing shipped
    assert catalog.find("J2") == () and catalog.find("AJ10-190") == ()
    assert [e.configuration_id for e in catalog.find("SSME")] == [
        "CFG-RS25-BLOCK-II", "CFG-RS25-SLS", "CFG-RS25-SMALL-THROAT"]


def test_own_statements_and_context_are_kept_apart(catalog):
    own = catalog.assertions("CFG-SPS-BLOCK-I")
    context = catalog.context("CFG-SPS-BLOCK-I")
    assert own and context and not {a.assertion_id for a in own} & {a.assertion_id for a in context}
    assert all(a.subject.kind is not SubjectKind.VARIANT for a in own)
    assert all(a.subject.kind is SubjectKind.VARIANT for a in context)


def test_sources_are_only_what_the_record_cites(catalog):
    assert [s.source_id for s in catalog.sources("CFG-J2-230K")] == ["SRC-NTRS-20100027318"]
    assert {s.source_id for s in catalog.sources("CFG-SPS-BLOCK-I")} == {"SRC-NASA-TND7375", "SRC-NTRS-20100027319"}


def test_capabilities_are_five_separate_answers(catalog):
    results = catalog.capabilities("CFG-SPS-BLOCK-I")
    assert [r.capability for r in results] == list(Capability)
    assert catalog.capability("CFG-SPS-BLOCK-I", Capability.ARCHITECTURE).status is CapabilityStatus.PARTIAL
    assert not hasattr(results[0], "score")


def test_answers_are_frozen_tuples(catalog):
    with pytest.raises(dataclasses.FrozenInstanceError):
        catalog.fingerprint = "x"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        catalog.entries()[0].label = "x"  # type: ignore[misc]
    for answer in (catalog.entries(), catalog.assertions("CFG-J2-230K"), catalog.topologies("CFG-J2-230K"),
                   catalog.capabilities("CFG-J2-230K"), catalog.sources("CFG-J2-230K")):
        assert isinstance(answer, tuple)


def test_loading_is_deterministic(catalog):
    again = load_reference_engines()
    assert again == catalog and again.fingerprint == catalog.fingerprint
    assert [r for r in again.capabilities("CFG-RL10A-3-3A")] == list(catalog.capabilities("CFG-RL10A-3-3A"))


def _code_strings(path: pathlib.Path) -> list[str]:
    """String literals a module's code can use: every constant except bare string statements (docstrings)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bare = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr)}
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in bare]


def test_the_catalog_reads_one_file_and_never_research(tmp_path, monkeypatch):
    elsewhere = tmp_path / "copy.json"
    shutil.copy(reference_engine_path(), elsewhere)
    assert load_reference_engines(elsewhere).fingerprint == load_reference_engines().fingerprint
    for path in (ROOT / "rocketforge").rglob("*.py"):
        code = [s for s in _code_strings(path)
                if any(w in s.replace("\\", "/") for w in ("docs/research", "engine_database", "db05"))]
        assert not code, (path, code)
    assert reference_engine_path() == ROOT / "rocketforge" / "data" / "evidence" / "engines" / "reference_engines.json"


def test_a_frozen_build_finds_the_corpus_beside_the_other_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert reference_engine_path() == tmp_path / "rocketforge" / "data" / "evidence" / "engines" / "reference_engines.json"
    with pytest.raises(EvidenceError, match="no reference-engine corpus"):
        load_reference_engines()


def test_loading_needs_no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("the catalog opened a network connection")
    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    assert len(load_reference_engines().entries()) == 16


def test_a_file_that_breaks_a_shipping_rule_is_refused_not_trimmed(tmp_path):
    payload = json.loads(reference_engine_path().read_text(encoding="utf-8"))
    payload["assertions"][0]["status"] = "INFERRED"
    path = tmp_path / "reference_engines.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(EvidenceError, match="may not ship as reference data"):
        load_reference_engines(path)


# ------------------------------------------------------------------ no solver can be reached


FORBIDDEN = ("rocketforge.physics", "rocketforge.engineering", "rocketforge.engine", "rocketforge.providers",
             "rocketforge.comparison", "rocketforge.ui", "cea", "cantera", "CoolProp", "PySide6", "PyQt5")


def test_the_catalog_imports_no_solver_ui_or_provider():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(("rocketforge.application." if node.level else "") + (node.module or ""))
    assert not [m for m in imported if m.startswith(FORBIDDEN)]
    assert {m for m in imported if m.startswith("rocketforge.application")} == {"rocketforge.application.data_paths"}


def test_importing_and_using_the_catalog_loads_no_solver():
    code = ("import sys\n"
            "from rocketforge.application.analysis.reference_engine_catalog import load_reference_engines\n"
            "c = load_reference_engines()\n"
            "[c.capabilities(e.configuration_id) for e in c.entries()]\n"
            f"bad = sorted(m for m in sys.modules if m.startswith({FORBIDDEN!r}))\n"
            "print(bad)\n")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "[]", out.stdout + out.stderr


def test_the_catalog_has_no_design_entry_point():
    public = [n for n in dir(catalog_module) if not n.startswith("_")]
    assert not [n for n in public if any(w in n.lower() for w in ("design", "recommend", "solve", "size"))]
