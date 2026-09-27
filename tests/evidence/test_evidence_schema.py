"""Evidence JSON schema version 1: strict in, canonical out.

The loader is exercised on a record built in-test (not on the shipped data, which
``test_evidence_rp1311.py`` covers), so a failure here is a schema failure.
"""

from __future__ import annotations

import copy
import json

import pytest

from rocketforge.evidence import (
    SCHEMA_VERSION,
    EvidenceError,
    EvidenceSchemaError,
    Missing,
    MissingReason,
    record_from_dict,
    record_from_json,
    record_to_dict,
    record_to_json,
    sources_from_json,
    sources_to_json,
)
from evidence_fixtures import SRC, record, source


def payload():
    return record_to_dict(record())


def load(data):
    return record_from_json(json.dumps(data), {SRC: source()})


def test_the_schema_version_is_1():
    assert SCHEMA_VERSION == 1
    assert payload()["schema_version"] == 1


def test_a_record_round_trips_to_an_equal_record_and_identical_text():
    original = record()
    text = record_to_json(original)
    again = record_from_json(text, {SRC: source()})
    assert again == original
    assert record_to_json(again) == text


def test_the_canonical_text_is_stable_and_newline_terminated():
    text = record_to_json(record())
    assert text.endswith("}\n") and "\r" not in text
    assert text == record_to_json(record())


def test_missing_values_survive_the_round_trip_unchanged():
    again = load(payload())
    assert again.propellant.density == Missing(MissingReason.NOT_REPORTED, "not stated")
    assert again.propellant.ingredients[1].custom.molecular_weight == Missing(
        MissingReason.NOT_REPORTED)


def test_a_whole_formula_can_be_missing_and_round_trip():
    data = payload()
    data["propellant"]["ingredients"][1]["custom"]["formula"] = {"missing": "NOT_REPORTED"}
    again = load(data)
    assert again.propellant.ingredients[1].custom.formula == Missing(MissingReason.NOT_REPORTED)
    assert record_to_dict(again) == data


@pytest.mark.parametrize("version", [0, 2, "1", 1.0, True, None])
def test_an_unsupported_schema_version_is_refused(version):
    data = payload()
    data["schema_version"] = version
    with pytest.raises(EvidenceSchemaError, match="schema_version"):
        load(data)


def test_a_missing_schema_version_is_refused():
    data = payload()
    del data["schema_version"]
    with pytest.raises(EvidenceSchemaError, match="schema_version is required"):
        load(data)


def _paths(data, prefix=()):
    """Every object key in the payload, as a path, to remove or extend."""
    if isinstance(data, dict):
        for key, item in data.items():
            yield prefix + (key,)
            yield from _paths(item, prefix + (key,))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            yield from _paths(item, prefix + (i,))


def _at(data, path):
    for step in path:
        data = data[step]
    return data


OPTIONAL = {"decimals", "significant_figures", "note"}


@pytest.mark.parametrize("path", [
    p for p in _paths(record_to_dict(record()))
    if p[-1] not in OPTIONAL and p != ("schema_version",)
    and not (len(p) > 1 and p[-2] in ("formula", "capabilities", "capability_notes"))
], ids=lambda p: ".".join(map(str, p)))
def test_every_required_field_is_required(path):
    data = payload()
    del _at(data, path[:-1])[path[-1]]
    with pytest.raises(EvidenceError):
        load(data)


@pytest.mark.parametrize("path", [
    (), ("propellant",), ("propellant", "ingredients", 0),
    ("propellant", "ingredients", 0, "fraction"), ("propellant", "density"),
    ("propellant", "ingredients", 1, "custom"),
], ids=lambda p: ".".join(map(str, p)) or "record")
def test_an_unknown_field_is_refused_at_every_level(path):
    data = payload()
    _at(data, path)["uncertainty_pct"] = 5
    with pytest.raises(EvidenceSchemaError, match="unknown field"):
        load(data)


@pytest.mark.parametrize("path,bad", [
    (("kind",), "EXPERIMENTAL"),
    (("capabilities", "VA"), "GOLD"),
    (("propellant", "ingredients", 0, "fraction", "status"), "MEASURED"),
    (("propellant", "density", "missing"), "ABSENT"),
], ids=lambda x: str(x))
def test_an_unknown_enumeration_value_is_refused(path, bad):
    data = payload()
    _at(data, path[:-1])[path[-1]] = bad
    with pytest.raises(EvidenceSchemaError, match="is not one of"):
        load(data)


def test_an_unknown_dimension_is_refused():
    data = payload()
    data["capabilities"]["VE"] = "NOT_APPLICABLE"
    with pytest.raises(EvidenceSchemaError):
        load(data)


@pytest.mark.parametrize("path,bad", [
    (("propellant", "ingredients", 0, "fraction", "value"), "0.8"),
    (("propellant", "ingredients", 0, "fraction", "value"), True),
    (("propellant", "ingredients", 0, "fraction", "value"), None),
    (("propellant", "exact_formulation"), "yes"),
    (("source_ids",), "S-TEST-A"),
    (("propellant", "ingredients"), {}),
    (("propellant",), []),
    (("propellant", "density"), 1.2),
    (("capabilities",), ["VA"]),
])
def test_a_malformed_structure_is_refused(path, bad):
    data = payload()
    _at(data, path[:-1])[path[-1]] = bad
    with pytest.raises(EvidenceError):
        load(data)


def test_an_atom_count_cannot_be_missing_on_its_own():
    data = payload()
    data["propellant"]["ingredients"][1]["custom"]["formula"]["C"] = {"missing": "UNKNOWN"}
    with pytest.raises(EvidenceSchemaError, match="whole formula"):
        load(data)


def test_a_duplicated_key_is_refused_rather_than_overwritten():
    text = record_to_json(record()).replace(
        '"title": "Test record",', '"title": "Test record",\n  "title": "Other",', 1)
    with pytest.raises(EvidenceSchemaError, match="duplicate key"):
        record_from_json(text, {SRC: source()})


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_json_constants_are_refused(constant):
    text = record_to_json(record()).replace('"value": 0.8', f'"value": {constant}', 1)
    with pytest.raises(EvidenceSchemaError):
        record_from_json(text, {SRC: source()})


@pytest.mark.parametrize("text", ["", "{", "[]", "null", "42"])
def test_text_that_is_not_a_record_object_is_refused(text):
    with pytest.raises(EvidenceSchemaError):
        record_from_json(text, {SRC: source()})


def test_malformed_input_fails_the_same_way_every_time():
    data = payload()
    del data["propellant"]["family"]
    messages = set()
    for _ in range(3):
        with pytest.raises(EvidenceSchemaError) as caught:
            load(copy.deepcopy(data))
        messages.add(str(caught.value))
    assert len(messages) == 1


def test_record_from_json_checks_the_registry_but_record_from_dict_does_not():
    data = payload()
    record_from_dict(data)                              # schema only
    with pytest.raises(EvidenceError, match="unknown sources"):
        record_from_json(json.dumps(data), {})


# ---------------------------------------------------------------- registry


def test_a_source_registry_round_trips():
    sources = [source(), source("S-TEST-B", year=None, authors=())]
    text = sources_to_json(sources)
    loaded = sources_from_json(text)
    assert list(loaded) == ["S-TEST-A", "S-TEST-B"]
    assert list(loaded.values()) == sources
    assert sources_to_json(loaded.values()) == text


def test_a_registry_needs_its_version_and_refuses_duplicates_and_unknowns():
    good = json.loads(sources_to_json([source()]))
    for mutate, match in [
        (lambda d: d.pop("schema_version"), "schema_version is required"),
        (lambda d: d.update(schema_version=2), "not supported"),
        (lambda d: d["sources"].append(copy.deepcopy(d["sources"][0])), "listed twice"),
        (lambda d: d["sources"][0].update(licence="x"), "unknown field"),
        (lambda d: d["sources"][0].pop("shipping"), "missing field"),
        (lambda d: d["sources"][0].update(shipping="FREE"), "is not one of"),
    ]:
        data = copy.deepcopy(good)
        mutate(data)
        with pytest.raises(EvidenceSchemaError, match=match):
            sources_from_json(json.dumps(data))
