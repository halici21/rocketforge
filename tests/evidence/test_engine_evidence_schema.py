"""Engine-evidence JSON, schema version 1: strict in, canonical out."""

from __future__ import annotations

import copy

import pytest

from rocketforge.evidence import EvidenceError, EvidenceSchemaError, Missing, MissingReason, record_from_dict
from rocketforge.evidence.engines import (
    ENGINE_EVIDENCE_FORMAT,
    ENGINE_EVIDENCE_SCHEMA_VERSION,
    PressureStation,
    SubjectKind,
    SubjectRef,
    corpus_fingerprint,
    corpus_from_dict,
    corpus_from_json,
    corpus_to_dict,
    corpus_to_json,
)
from engine_fixtures import stress_corpus


@pytest.fixture(scope="module")
def corpus():
    return stress_corpus()


@pytest.fixture()
def payload(corpus):
    return copy.deepcopy(corpus_to_dict(corpus))


def _assertion(payload, aid):
    return next(a for a in payload["assertions"] if a["assertion_id"] == aid)


def test_schema_version_and_format_marker(payload):
    assert ENGINE_EVIDENCE_SCHEMA_VERSION == 1
    assert payload["schema_version"] == 1 and payload["format"] == ENGINE_EVIDENCE_FORMAT


def test_round_trip_is_equal_and_byte_identical(corpus):
    text = corpus_to_json(corpus)
    again = corpus_from_json(text)
    assert again == corpus
    assert corpus_to_json(again) == text
    assert text.endswith("}\n") and "\r" not in text


def test_fingerprint_is_deterministic_and_content_sensitive(corpus, payload):
    assert corpus_fingerprint(corpus) == corpus_fingerprint(corpus_from_json(corpus_to_json(corpus)))
    _assertion(payload, "RS25-PC-109")["value"]["value"] = 2995
    assert corpus_fingerprint(corpus_from_dict(payload)) != corpus_fingerprint(corpus)


def test_scope_and_conditions_survive_the_round_trip(corpus):
    again = corpus_from_json(corpus_to_json(corpus)).assertion_map
    pc = again["J2-PC"]
    assert pc.operating_point_id == "OP-J2-MR55"
    assert pc.subject == SubjectRef(SubjectKind.CONFIGURATION, "CFG-J2-230K")
    assert pc.conditions.pressure_station is PressureStation.NOZZLE_STAGNATION
    assert pc.value_as_printed == "717" and pc.unit_as_printed == "psia"
    assert again["LMDE-PC"].value == Missing(MissingReason.NOT_REPORTED, "not printed in the pages read")
    assert again["RD170-THRUST-SL"].first_stated_by == "SRC-PARIS-PLACARD-1989"


def test_printed_value_and_unit_are_preserved_exactly(payload):
    a = _assertion(payload, "RD170-PC")
    assert a["value_as_printed"] == "250 kgs/cm2" and a["unit_as_printed"] == "kgs/cm2"


@pytest.mark.parametrize("mutate,match", [
    (lambda p: p.update(extra=1), "unknown field"),
    (lambda p: p.pop("conflicts"), "missing field"),
    (lambda p: p.update(schema_version=2), "not supported"),
    (lambda p: p.update(schema_version=True), "not supported"),
    (lambda p: p.update(format="rocketforge.evidence"), "not engine evidence"),
    (lambda p: _assertion(p, "RS25-PC-109").update(color="red"), "unknown field"),
    (lambda p: _assertion(p, "RS25-PC-109").pop("epoch"), "missing field"),
    (lambda p: _assertion(p, "RS25-PC-109").update(value_kind="TYPICAL"), "not one of"),
    (lambda p: _assertion(p, "RS25-PC-109")["conditions"].update(pressure_station="NOZZLE"), "not one of"),
    (lambda p: _assertion(p, "RS25-PC-109")["value"].update(type="float"), "not number, range"),
    (lambda p: _assertion(p, "RS25-PC-109")["value"].update(value="2994"), "must be a number"),
    (lambda p: p["topologies"][0]["edges"][0].update(kind="PIPE"), "not one of"),
    (lambda p: p["sources"][0]["rights"].pop("figures"), "missing field"),
])
def test_malformed_documents_are_refused(payload, mutate, match):
    mutate(payload)
    with pytest.raises(EvidenceSchemaError, match=match):
        corpus_from_dict(payload)


def test_semantic_errors_in_a_well_formed_file_are_refused(payload):
    _assertion(payload, "RS25-PC-109")["conditions"]["pressure_station"] = None
    with pytest.raises(EvidenceError, match="measurement station"):
        corpus_from_dict(payload)


def test_a_missing_optional_field_never_acquires_a_value(payload):
    a = _assertion(payload, "RS25-PC-109")
    assert a["epoch"] is None and a["normalized"] is None
    assert corpus_from_dict(payload).assertion_map["RS25-PC-109"].epoch is None
    del a["normalized"]
    with pytest.raises(EvidenceSchemaError, match="missing field"):
        corpus_from_dict(payload)


def test_duplicate_keys_and_nan_are_refused(corpus):
    text = corpus_to_json(corpus)
    with pytest.raises(EvidenceSchemaError, match="duplicate key"):
        corpus_from_json(text.replace('"format": ', '"format": "x", "format": ', 1))
    with pytest.raises(EvidenceSchemaError):
        corpus_from_json(text.replace('"value": 2994', '"value": NaN', 1))


def test_dangling_references_in_a_file_are_refused(payload):
    payload["conflicts"][0]["assertion_ids"][0] = "NOPE"
    with pytest.raises(EvidenceError, match="unknown assertion"):
        corpus_from_dict(payload)


def test_engine_evidence_and_solid_evidence_cannot_be_confused(payload):
    with pytest.raises(EvidenceSchemaError):
        record_from_dict(payload)
    with pytest.raises(EvidenceSchemaError, match="not engine evidence"):
        corpus_from_dict({"schema_version": 1, "record_id": "DS-X"})


def test_an_empty_corpus_is_valid_and_sparse_records_stay_valid():
    empty = {"format": ENGINE_EVIDENCE_FORMAT, "schema_version": 1, **{k: [] for k in (
        "sources", "families", "variants", "configurations", "operating_points", "units", "aliases",
        "lineage", "components", "schematics", "topologies", "assertions", "conflicts")}}
    assert corpus_to_dict(corpus_from_dict(empty)) == empty
    sparse = dict(empty, families=[{"family_id": "FAM-X", "name": "X", "notes": ""}],
                  variants=[{"variant_id": "VAR-X", "family_id": "FAM-X", "designation": "X-1", "notes": ""}])
    assert len(corpus_from_dict(sparse).variants) == 1
