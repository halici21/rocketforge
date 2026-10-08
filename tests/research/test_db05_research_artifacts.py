"""The DB-0.5 opened-source evidence layer is internally consistent.

DB-0.5 (docs/research/engine_database/db05) holds only evidence read from
documents that were actually opened. These checks keep that promise
mechanical: every assertion, schematic and topology cites an opened document
with a locator, every topology edge joins declared nodes, and nothing is
promoted from a document whose access was blocked.
"""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs" / "research" / "engine_database"
DB05 = PACKAGE / "db05"

READ_LEVELS = {"READ_AND_MINED", "IDENTITY_VERIFIED_ONLY", "FETCHED_NOT_READ", "FETCHED_NOT_EVIDENCE", "ACCESS_BLOCKED"}
VALUE_STATUS = {"REPORTED", "DERIVED", "DIGITISED", "INFERRED"}
DISPOSITIONS = {"PROMOTED", "REJECTED_FOR_VARIANT", "NOT_PROMOTED_MODEL_PARAMETER"}
TOPOLOGY_EVIDENCE = {"SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH", "INFERRED"}
RESOLUTIONS = {"RESOLVED", "EXPLAINED", "PARTIALLY_RESOLVED", "UNRESOLVED", "CONFIRMED_SECONDARY"}
DB0_OUTCOMES = {"CONFIRMED", "CONFIRMED_OTHER_SOURCE", "CORRECTED", "RECLASSIFIED", "UNSUPPORTED", "WRONG_VARIANT", "ACCESS_BLOCKED"}
TIERS = {"A", "B", "C", "D", "E"}


def load(name: str, key: str) -> list[dict]:
    return json.loads((DB05 / name).read_text(encoding="utf-8"))[key]


@pytest.fixture(scope="module")
def opened():
    docs = load("documents_opened.json", "documents")
    return {d["source_id"]: d for d in docs if d["read_level"] in {"READ_AND_MINED", "IDENTITY_VERIFIED_ONLY"}}


@pytest.fixture(scope="module")
def engines():
    return {e["id"] for e in json.loads((PACKAGE / "data" / "engines.json").read_text(encoding="utf-8"))["engines"]}


@pytest.fixture(scope="module")
def sources():
    return {s["source_id"] for s in json.loads((PACKAGE / "data" / "sources.json").read_text(encoding="utf-8"))["sources"]}


def test_every_document_record_is_well_formed(sources):
    docs = load("documents_opened.json", "documents")
    assert len({d["source_id"] for d in docs}) == len(docs)
    for d in docs:
        assert d["read_level"] in READ_LEVELS, d["source_id"]
        assert d["source_id"] in sources, d["source_id"]
        if d["read_level"] in {"READ_AND_MINED", "IDENTITY_VERIFIED_ONLY"}:
            assert d["sha256"] and d["bytes"], d["source_id"]
            assert d["identifier_verified"] and d["title_as_printed"], d["source_id"]
            assert d["tier"] in TIERS, d["source_id"]
            assert d["rights_statement_checked"], d["source_id"]
        if d["read_level"] == "ACCESS_BLOCKED":
            assert d["status_note"], d["source_id"]


def test_every_assertion_cites_an_opened_document_with_a_locator(opened, engines):
    ids = set()
    for a in load("assertions.json", "assertions"):
        assert a["assertion_id"] not in ids
        ids.add(a["assertion_id"])
        assert a["engine_id"] in engines, a["assertion_id"]
        assert a["source_id"] in opened, a["assertion_id"]
        assert opened[a["source_id"]]["read_level"] == "READ_AND_MINED", a["assertion_id"]
        assert a["locator"].strip(), a["assertion_id"]
        assert a["status"] in VALUE_STATUS, a["assertion_id"]
        assert a["disposition"] in DISPOSITIONS, a["assertion_id"]
        assert a["access"] == "fetched", a["assertion_id"]
        assert a["value_as_printed"] not in (None, ""), a["assertion_id"]


def test_schematics_were_viewed_in_opened_documents(opened, engines):
    for s in load("schematics_viewed.json", "schematics"):
        assert s["verification"] == "VERIFIED_VIEWED", s["schematic_id"]
        assert s["source_id"] in opened, s["schematic_id"]
        assert s["locator"] and s["viewed_how"] and s["legibility"], s["schematic_id"]
        assert set(s["engine_ids"]) <= engines, s["schematic_id"]


def test_topology_graphs_are_closed_and_cite_viewed_schematics(engines):
    viewed = {s["schematic_id"] for s in load("schematics_viewed.json", "schematics")}
    paths = sorted((DB05 / "topology").glob("*.json"))
    assert paths
    for p in paths:
        t = json.loads(p.read_text(encoding="utf-8"))
        assert t["engine_id"] == p.stem and t["engine_id"] in engines
        assert t["schematic_ids"] and set(t["schematic_ids"]) <= viewed, p.name
        assert t["completeness"]["declared_complete"] is False, p.name  # absence is never asserted by omission
        nodes = {n["id"] for n in t["nodes"]}
        assert len(nodes) == len(t["nodes"]), p.name
        for item in t["nodes"] + t["edges"]:
            assert item["evidence_status"] in TOPOLOGY_EVIDENCE, (p.name, item)
            assert item["locator"], (p.name, item)
        for e in t["edges"]:
            assert e["from"] in nodes and e["to"] in nodes, (p.name, e)


def test_conflicts_and_db0_dispositions_use_the_defined_vocabulary(sources, opened):
    for c in load("conflicts.json", "conflicts"):
        assert c["resolution"] in RESOLUTIONS, c["conflict_id"]
        assert len(c["claims"]) >= 1, c["conflict_id"]
        for _value, sid, locator in c["claims"]:
            assert sid in sources, (c["conflict_id"], sid)
            assert locator, c["conflict_id"]
        if c["resolution"] in {"RESOLVED", "EXPLAINED"}:
            assert c["explanation"], c["conflict_id"]
            assert any(sid in opened for _v, sid, _l in c["claims"]), c["conflict_id"]
    seen = set()
    for x in load("db0_dispositions.json", "dispositions"):
        assert x["outcome"] in DB0_OUTCOMES, x
        key = (x["engine_id"], x["db0_assertion_index"])
        assert key not in seen
        seen.add(key)
        anchor = json.loads((PACKAGE / "data" / "anchors" / f"{x['engine_id']}.json").read_text(encoding="utf-8"))
        assert anchor["assertions"][x["db0_assertion_index"]]["field_path"] == x["db0_field_path"], x
