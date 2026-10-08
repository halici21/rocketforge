"""The DB-0 engine research package is internally consistent.

DB-0 (docs/research/engine_database) is research data, not a runtime asset:
nothing under rocketforge/ reads it. These checks keep it honest as it is
edited by hand or regenerated: every id is unique, every citation resolves,
every evidence status and missing-value reason is one the package defines, and
no value claims REPORTED status on the strength of an encyclopedic or forum
source.
"""
from __future__ import annotations

import collections
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs" / "research" / "engine_database"
DATA = PACKAGE / "data"

VALUE_STATUS = {"REPORTED", "DERIVED", "DIGITISED", "INFERRED", "SECONDARY_CLAIM"}
MISSING_REASON = {"NOT_REPORTED", "NOT_AUDITED", "UNKNOWN", "ACCESS_BLOCKED", "RIGHTS_RESTRICTED"}
TIERS = {"A", "B", "C", "D", "E"}
RIGHTS = {"PUBLIC_DOMAIN_GOV", "OPEN_LICENSE", "VALUES_WITH_ATTRIBUTION", "METADATA_ONLY",
          "RESTRICTED_REFERENCE", "RIGHTS_REVIEW_REQUIRED", "UNKNOWN"}
ACCESS = {"fetched", "search_result_only", "dead_link", "paywalled", "not_retrieved"}
ENGINE_STATUS = {"operational", "retired", "cancelled", "experimental", "development", "proposed", "unknown"}
FEED = {"pressure_fed_regulated", "pressure_fed_blowdown", "pressure_fed_unspecified", "pump_fed_turbopump",
        "pump_fed_electric", "pump_fed_positive_displacement", "other", "UNKNOWN"}
CYCLE = {"none_pressure_fed", "gas_generator", "expander_closed", "expander_bleed", "staged_combustion_fuel_rich",
         "staged_combustion_ox_rich", "full_flow_staged_combustion", "tap_off", "separate_turbine_working_fluid",
         "electric_pump", "combustion_tap", "other", "UNKNOWN"}
TOPOLOGY_EVIDENCE = {"SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "DERIVED_FROM_BOTH", "INFERRED", "UNKNOWN"}
DOCUMENTS = ["DB0_RESEARCH_OVERVIEW.md", "ENGINE_ARCHITECTURE_TAXONOMY.md", "ENGINE_FAMILY_MASTER_LIST.md",
             "ANCHOR_ENGINE_CORPUS.md", "FLOW_SCHEMATIC_INDEX.md", "SOURCE_REGISTRY.md", "CONFLICT_LEDGER.md",
             "RIGHTS_MATRIX.md", "SCHEMA_PROPOSAL.md", "COVERAGE_GAPS.md"]


def load(name: str, key: str) -> list[dict]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))[key]


@pytest.fixture(scope="module")
def engines():
    return load("engines.json", "engines")


@pytest.fixture(scope="module")
def sources():
    return {s["source_id"]: s for s in load("sources.json", "sources")}


@pytest.fixture(scope="module")
def anchors():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA / "anchors").glob("*.json"))]


def test_every_deliverable_document_exists():
    missing = [d for d in DOCUMENTS if not (PACKAGE / d).is_file()]
    assert missing == []


def test_ids_are_unique(engines):
    for name, key, field in [("engines.json", "engines", "id"), ("sources.json", "sources", "source_id"),
                             ("schematics.json", "schematics", "schematic_id"),
                             ("conflicts.json", "conflicts", "conflict_id"), ("families.json", "families", "family_id")]:
        ids = [item[field] for item in load(name, key)]
        dupes = [i for i, n in collections.Counter(ids).items() if n > 1]
        assert dupes == [], f"{name}: duplicate {field} {dupes}"


def test_engine_records_use_the_defined_vocabulary(engines):
    for e in engines:
        assert e["id"].startswith("ENG-"), e["id"]
        assert e["family_id"].startswith("FAM-"), e["id"]
        assert e["status"] in ENGINE_STATUS, (e["id"], e["status"])
        assert e["feed"] in FEED, (e["id"], e["feed"])
        assert e["cycle"] in CYCLE, (e["id"], e["cycle"])
        assert e["cycle_status"] in VALUE_STATUS | {"UNKNOWN"}, (e["id"], e["cycle_status"])
        assert e["identity_evidence"] in {"SOURCED", "UNSOURCED_PLACEHOLDER"}, e["id"]
        for v in e["key_values"]:
            assert v["status"] in VALUE_STATUS, (e["id"], v)
            assert v.get("source_id"), (e["id"], v)


def test_feed_and_cycle_agree(engines):
    # LIQ-2: a pressure-fed engine has no power cycle, and an electric pump is a pump feed.
    for e in engines:
        if e["feed"].startswith("pressure_fed"):
            assert e["cycle"] in {"none_pressure_fed", "UNKNOWN"}, e["id"]
        if e["feed"].startswith("pump_fed"):
            assert e["cycle"] != "none_pressure_fed", e["id"]
        if e["cycle"] == "electric_pump":
            assert e["feed"] == "pump_fed_electric", e["id"]


def test_every_citation_resolves(engines, sources, anchors):
    for e in engines:
        for sid in e["source_ids"]:
            assert sid in sources, (e["id"], sid)
        for v in e["key_values"]:
            assert v["source_id"] in sources, (e["id"], v["source_id"])
        for a in e["aliases"]:
            for sid in a.get("source_ids") or []:
                assert sid in sources, (e["id"], a["name"], sid)
    for s in load("schematics.json", "schematics"):
        assert s["source_id"] in sources, s["schematic_id"]
    for c in load("conflicts.json", "conflicts"):
        for claim in c["claims"]:
            # A claim without a registered source must say where it came from instead.
            assert claim.get("source_id") in sources or claim.get("origin"), (c["conflict_id"], claim)
    for a in anchors:
        for x in a.get("assertions") or []:
            assert x.get("source_id") in sources, (a["engine_id"], x.get("field_path"))


def test_engine_references_resolve(engines, anchors):
    ids = {e["id"] for e in engines}
    for a in anchors:
        assert a["engine_id"] in ids, a["engine_id"]
    families = {f["family_id"] for f in load("families.json", "families")}
    for s in load("schematics.json", "schematics"):
        for eid in s["engine_ids"]:
            assert eid in ids, (s["schematic_id"], eid)
        for fid in s.get("family_ids") or []:
            assert fid in families, (s["schematic_id"], fid)
        assert not s.get("unresolved_engine_refs"), s["schematic_id"]
    for a in load("aliases.json", "aliases"):
        assert a["engine_id"] in ids, a
    for f in load("families.json", "families"):
        for eid in f["variant_ids"]:
            assert eid in ids, (f["family_id"], eid)


def test_sources_use_the_defined_vocabulary(sources):
    for sid, s in sources.items():
        assert s["tier"] in TIERS, (sid, s["tier"])
        assert s["rights"] in RIGHTS, (sid, s["rights"])
        assert s["access"] in ACCESS, (sid, s["access"])


def test_a_source_is_claimed_as_opened_only_with_a_db05_access_record(sources):
    # DB-0 could not open any document. DB-0.5 records every document it opened in
    # db05/documents_opened.json; no other source may claim access "fetched".
    opened = json.loads((PACKAGE / "db05" / "documents_opened.json").read_text(encoding="utf-8"))["documents"]
    read = {d["source_id"] for d in opened if d["read_level"] in {"READ_AND_MINED", "IDENTITY_VERIFIED_ONLY"}}
    assert {sid for sid, s in sources.items() if s["access"] == "fetched"} == read


def test_a_value_is_reported_only_by_a_tier_a_to_c_source(engines, sources, anchors):
    for e in engines:
        for v in e["key_values"]:
            if v["status"] == "REPORTED":
                assert sources[v["source_id"]]["tier"] in {"A", "B", "C"}, (e["id"], v)
    for a in anchors:
        for x in a.get("assertions") or []:
            if x.get("status") == "REPORTED":
                assert sources[x["source_id"]]["tier"] in {"A", "B", "C"}, (a["engine_id"], x.get("field_path"))


def test_anchor_missing_values_and_topology_use_the_defined_vocabulary(anchors):
    for a in anchors:
        for x in a.get("assertions") or []:
            assert x.get("status") in VALUE_STATUS, (a["engine_id"], x)
        for m in a.get("missing") or []:
            assert m.get("reason") in MISSING_REASON, (a["engine_id"], m)
        topology = a.get("topology") or {}
        nodes = {n["id"] for n in topology.get("nodes") or []}
        for item in (topology.get("nodes") or []) + (topology.get("edges") or []):
            assert item.get("evidence_status") in TOPOLOGY_EVIDENCE, (a["engine_id"], item)
        for edge in topology.get("edges") or []:
            assert edge["from"] in nodes and edge["to"] in nodes, (a["engine_id"], edge)
