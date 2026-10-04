"""EV-5: burn-rate laws as evidence -- the model, its strict JSON, and its rights.

Every law here is synthetic and test-only (source ``S-TEST-LAW``); no published
coefficient appears in this file. The shipped corpus is only ever read.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from rocketforge.evidence import (
    BURN_LAW_FORM,
    BURN_LAW_SCHEMA_VERSION,
    SCHEMA_VERSION,
    AccessClass,
    BurnLawReference,
    BurnLawRegime,
    Dimension,
    EvidenceError,
    EvidenceRecord,
    EvidenceSchemaError,
    EvidenceStatus,
    Missing,
    MissingReason,
    RecordKind,
    ReportedValue,
    ShippingPolicy,
    SourceReference,
    ValueStatus,
    record_from_json,
    record_to_json,
    reported_values,
    validate_against_sources,
)

SID, HELD = "S-TEST-LAW", "S-TEST-HELD"
ROOT = pathlib.Path(__file__).resolve().parents[2]
RECORDS = ROOT / "rocketforge" / "data" / "evidence" / "records"


def _source(sid, shipping):
    return SourceReference(source_id=sid, organization="Test", authors=(), title=sid, year=None,
                           identifiers={}, locator=f"https://example.invalid/{sid}",
                           source_type="test", access_class=AccessClass.PUBLIC_OPEN,
                           rights_statement="test", shipping=shipping, tier=2)


SOURCES = {SID: _source(SID, ShippingPolicy.VALUES_WITH_ATTRIBUTION),
           HELD: _source(HELD, ShippingPolicy.RIGHTS_REVIEW_REQUIRED)}


def v(value, unit, decimals=2, sid=SID):
    return ReportedValue(value, unit, sid, "Table 9 (test)", ValueStatus.REPORTED, decimals=decimals)


def regime(lo, hi, a, n, sid=SID):
    return BurnLawRegime(v(lo, "MPa", sid=sid), v(hi, "MPa", sid=sid), v(a, "mm/s", sid=sid),
                         v(n, "1", 3, sid=sid))


def law(regimes=None, sid=SID, **kw):
    base = dict(law_id="L-TEST", source_ids=(sid,), propellant_name="test propellant",
                form=BURN_LAW_FORM, pressure_unit="MPa", rate_unit="mm/s",
                regimes=regimes if regimes is not None else (
                    regime(0.1, 1.0, 5.0, 0.4, sid), regime(1.0, 2.0, 7.5, -0.25, sid),
                    regime(2.0, 4.0, 3.0, 0.6, sid)),
                temperature=Missing(MissingReason.NOT_REPORTED, "the source says 'ambient'"),
                uncertainty=Missing(MissingReason.NOT_REPORTED, "none given"))
    base.update(kw)
    return BurnLawReference(**base)


def record(burn=None, sid=SID, kind=RecordKind.BURN_LAW):
    return EvidenceRecord(
        record_id="DS-TEST-LAW", title="test law", kind=kind, source_ids=(sid,),
        capabilities={Dimension.VA: EvidenceStatus.REFERENCE_ONLY,
                      Dimension.VB: EvidenceStatus.SOURCE_COMPLETE_CANDIDATE,
                      Dimension.VC: EvidenceStatus.NOT_APPLICABLE,
                      Dimension.VD: EvidenceStatus.NOT_APPLICABLE},
        capability_notes={}, propellant=None, comparison_case_ids=(), executable_key=None,
        blockers=(), notes="", burn_law=law(sid=sid) if burn is None else burn)


# ---------------------------------------------------------------- the model


def test_a_piecewise_law_holds_its_regimes_units_and_explicit_absences():
    item = law()
    assert len(item.regimes) == 3 and item.regimes[1].n.value == -0.25
    assert isinstance(item.temperature, Missing) and isinstance(item.uncertainty, Missing)
    assert len(tuple(item.reported_values())) == 12


@pytest.mark.parametrize("bad, message", [
    (lambda: regime(1.0, 1.0, 5.0, 0.4), "p_min < p_max"),
    (lambda: regime(2.0, 1.0, 5.0, 0.4), "p_min < p_max"),
    (lambda: regime(-0.1, 1.0, 5.0, 0.4), "negative"),
    (lambda: regime(0.1, 1.0, 0.0, 0.4), "positive"),
    (lambda: BurnLawRegime(v(0.1, "MPa"), v(1.0, "psia"), v(5.0, "mm/s"), v(0.4, "1")), "one unit"),
    (lambda: BurnLawRegime(v(0.1, "MPa"), v(1.0, "MPa"), v(5.0, "mm/s"), v(0.4, "MPa")),
     "dimensionless"),
    (lambda: BurnLawRegime(v(0.1, "MPa"), Missing(MissingReason.NOT_REPORTED), v(5.0, "mm/s"),
                           v(0.4, "1")), "reported value"),
])
def test_a_regime_that_is_not_a_law_is_refused(bad, message):
    with pytest.raises(EvidenceError, match=message):
        bad()


@pytest.mark.parametrize("bad, message", [
    (lambda: law(regimes=()), "at least one regime"),
    (lambda: law(regimes=(regime(0.1, 2.0, 5.0, 0.4), regime(1.0, 3.0, 5.0, 0.4))), "overlap"),
    (lambda: law(regimes=(regime(2.0, 3.0, 5.0, 0.4), regime(0.1, 1.0, 5.0, 0.4))), "overlap"),
    (lambda: law(form="r = a + b*p"), "law form"),
    (lambda: law(pressure_unit="psia"), "nothing is converted"),
    (lambda: law(rate_unit="in/s"), "nothing is converted"),
    (lambda: law(temperature=20.0), "Missing"),
])
def test_a_law_that_would_need_repair_is_refused_not_repaired(bad, message):
    with pytest.raises(EvidenceError, match=message):
        bad()


def test_a_gap_between_regimes_is_kept_as_a_gap():
    item = law(regimes=(regime(0.1, 1.0, 5.0, 0.4), regime(2.0, 3.0, 5.0, 0.4)))
    assert [r.pressure_max.value for r in item.regimes] == [1.0, 3.0]


def test_only_a_burn_law_record_carries_a_law():
    with pytest.raises(EvidenceError, match="burn-law record"):
        record(kind=RecordKind.REFERENCE)
    with pytest.raises(EvidenceError, match="burn-law record"):
        EvidenceRecord(record_id="X", title="x", kind=RecordKind.BURN_LAW, source_ids=(SID,),
                       capabilities=record().capabilities, capability_notes={}, propellant=None,
                       comparison_case_ids=(), executable_key=None, blockers=(), notes="")


def test_the_law_must_cite_a_declared_source():
    with pytest.raises(EvidenceError, match="does not declare"):
        record(burn=law(sid=HELD))


# ---------------------------------------------------------------- JSON, versioned


def test_a_law_round_trips_byte_for_byte_as_schema_version_2():
    text = record_to_json(record())
    payload = json.loads(text)
    assert payload["schema_version"] == BURN_LAW_SCHEMA_VERSION == 2
    assert list(payload)[-1] == "burn_law" and payload["burn_law"]["form"] == BURN_LAW_FORM
    again = record_from_json(text, SOURCES)
    assert again == record() and record_to_json(again) == text


def test_every_shipped_record_is_still_version_1_byte_for_byte():
    assert SCHEMA_VERSION == 1
    for path in RECORDS.glob("*.json"):
        assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1, path.name


def _payload():
    return json.loads(record_to_json(record()))


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d.update(schema_version=1), "unknown field"),                  # v1 has no law
    (lambda d: d.update(burn_law=None), "carries a burn law"),
    (lambda d: d["burn_law"].update(extra=1), "unknown field"),
    (lambda d: d["burn_law"]["regimes"][0].update(extra=1), "unknown field"),
    (lambda d: d["burn_law"]["regimes"][0].pop("n"), "missing field"),
    (lambda d: d["burn_law"]["regimes"][0].update(a={"missing": "NOT_REPORTED"}), "never missing"),
    (lambda d: d["burn_law"].update(regimes={}), "must be a list"),
    (lambda d: d.update(schema_version=3), "not supported"),
])
def test_a_malformed_law_is_refused(mutate, message):
    data = _payload()
    mutate(data)
    with pytest.raises(EvidenceSchemaError, match=message):
        record_from_json(json.dumps(data), SOURCES)


# ---------------------------------------------------------------- rights


def test_a_law_from_a_source_under_rights_review_cannot_ship():
    held = record(burn=law(regimes=(regime(0.1, 1.0, 5.0, 0.4, HELD),), sid=HELD), sid=HELD)
    assert len(reported_values(held)) == 4
    with pytest.raises(EvidenceError, match="RIGHTS_REVIEW_REQUIRED"):
        validate_against_sources(held, SOURCES)
    with pytest.raises(EvidenceError, match="RIGHTS_REVIEW_REQUIRED"):
        record_from_json(record_to_json(held), SOURCES)


def test_no_shipped_record_carries_a_burn_law_yet():
    """The Nakka law's redistribution is still under review (R1): nothing ships."""
    for path in RECORDS.glob("*.json"):
        assert "burn_law" not in json.loads(path.read_text(encoding="utf-8")), path.name
