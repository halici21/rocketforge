"""EV-4: the Gate-4 records, as the R1 audit defines them, and nothing more.

The shipped corpus now holds RP-1311 Example 5 plus the Gate-4 manifest of the
R1 integration blueprint (section 11, gate 4): the NASA reports TN D-7133,
JPL 79-29 (BATES), CR-2478 and CR-183944 (RSRM-9), with values their NTRS
rights allow, and rights-limited reference records -- Fraunhofer 2015 and
2022, the JANNAF databases, and three operational motors -- with none.

Checked here: each record's identity and four independent capability states;
that every shipped number is a reported value from a value-shipping source
with a precise locator and its printed precision; that the rights-limited
records carry no number at all; that printed inconsistencies stay printed;
that the comparison cases the records name exist; and that the EV-3 check
answers honestly for each record and solves nothing.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

import rocketforge.comparison.rp1311 as rp1311
import rocketforge.comparison.rp1311_historical as rp1311_historical
import rocketforge.comparison.solid_reports as solid_reports
from rocketforge.application.analysis import evidence_cea_bridge as bridge
from rocketforge.application.analysis import propulsion_evidence_service as service
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.comparison import CaseOrigin, ReferenceCase, SourceKind
from rocketforge.evidence import (
    Dimension,
    EvidenceStatus as S,
    Missing,
    MissingReason,
    RecordKind,
    ReportedValue,
    ShippingPolicy,
    ValueStatus,
    reported_values,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
RECORDS = ROOT / "rocketforge" / "data" / "evidence" / "records"
R1 = ROOT / "acceptance" / "propulsion_evidence_research_r1" / "dataset_registry.json"
VA, VB, VC, VD = Dimension.VA, Dimension.VB, Dimension.VC, Dimension.VD
NA = S.NOT_APPLICABLE

#: R1 matrices section 1, one row per record: (VA, VB, VC, VD).
CAPABILITIES = {
    "DS-RP1311-E5": (S.REGRESSION_LOCKED, NA, NA, NA),
    "DS-TND7133": (S.REFERENCE_ONLY, S.VALIDATION_CANDIDATE, S.UNDERDEFINED, S.REFERENCE_ONLY),
    "DS-JPL-ALTPROP-BATES": (S.REFERENCE_ONLY, S.VALIDATION_CANDIDATE, S.UNDERDEFINED,
                             S.VALIDATION_CANDIDATE),
    "DS-CR2478-STERILIZABLE": (NA, S.REFERENCE_ONLY, S.VALIDATION_CANDIDATE,
                               S.VALIDATION_CANDIDATE),
    "DS-RSRM9": (S.UNDERDEFINED, S.REFERENCE_ONLY, S.REFERENCE_ONLY, S.REFERENCE_ONLY),
    "DS-FHG-2015-ADNGAP-MOTOR": (S.REFERENCE_ONLY, S.VALIDATION_CANDIDATE, S.UNDERDEFINED,
                                 S.VALIDATION_CANDIDATE),
    "DS-FHG-2022-ADN-FIBRES": (NA, S.VALIDATION_CANDIDATE, S.UNDERDEFINED, S.REFERENCE_ONLY),
    "DS-JANNAF-DATABASES-REF": (S.ACCESS_BLOCKED,) * 4,
    "DS-OPERATIONAL-JAXA-SRB3": (NA, NA, S.REFERENCE_ONLY, S.REFERENCE_ONLY),
    "DS-OPERATIONAL-ESA-P120C": (NA, NA, S.REFERENCE_ONLY, S.REFERENCE_ONLY),
    "DS-OPERATIONAL-ISRO-S200": (NA, NA, S.REFERENCE_ONLY, S.REFERENCE_ONLY),
}
NASA_VALUE_RECORDS = ("DS-TND7133", "DS-JPL-ALTPROP-BATES", "DS-CR2478-STERILIZABLE", "DS-RSRM9")
RIGHTS_LIMITED = ("DS-FHG-2015-ADNGAP-MOTOR", "DS-FHG-2022-ADN-FIBRES", "DS-JANNAF-DATABASES-REF",
                  "DS-OPERATIONAL-JAXA-SRB3", "DS-OPERATIONAL-ESA-P120C",
                  "DS-OPERATIONAL-ISRO-S200")
ALL_CASES = (*(getattr(rp1311, n) for n in rp1311.__all__),
             rp1311_historical.RP1311_EXAMPLE5_PRINT_1996, *solid_reports.SOLID_REPORT_CASES)


@pytest.fixture(scope="module")
def corpus():
    return service.load_corpus()


def test_the_corpus_is_rp1311_plus_the_gate4_manifest(corpus):
    assert {r.record_id for r in corpus.records} == set(CAPABILITIES)


@pytest.mark.parametrize("rid", sorted(CAPABILITIES))
def test_each_record_carries_its_four_r1_capability_states(corpus, rid):
    record = corpus.record(rid)
    assert tuple(record.capabilities[d] for d in (VA, VB, VC, VD)) == CAPABILITIES[rid]


def test_no_record_is_gold_and_only_rp1311_is_locked_or_executable(corpus):
    for record in corpus.records:
        if record.record_id == "DS-RP1311-E5":
            continue
        assert S.REGRESSION_LOCKED not in record.capabilities.values(), record.record_id
        assert S.VERIFIED_NUMERICAL_REFERENCE not in record.capabilities.values()
        assert record.executable_key is None
        assert "gold" not in record.title.lower()


# ---------------------------------------------------------------- provenance


@pytest.mark.parametrize("rid", NASA_VALUE_RECORDS)
def test_every_shipped_number_is_reported_located_and_printed_as_is(corpus, rid):
    record = corpus.record(rid)
    for value in reported_values(record):
        source = corpus.sources[value.source_id]
        assert value.source_id in record.source_ids
        assert source.shipping is ShippingPolicy.VALUES_WITH_ATTRIBUTION
        assert value.status is ValueStatus.REPORTED
        assert re.search(r"(Table|p\.|PDF|Figure)", value.locator), value.locator
        assert value.locator.split(",")[0].strip()        # names the report it is in
        assert value.decimals is not None, value           # printed precision is carried


@pytest.mark.parametrize("rid", RIGHTS_LIMITED)
def test_a_rights_limited_record_ships_no_number(corpus, rid):
    record = corpus.record(rid)
    assert record.kind is RecordKind.REFERENCE and record.propellant is None
    assert reported_values(record) == ()
    assert all(not corpus.sources[sid].values_may_ship for sid in record.source_ids)
    assert record.blockers                                  # says why, in words


def test_withheld_numbers_do_not_leak_into_rights_limited_text():
    """The R1 audit's numbers for the rights-limited datasets appear nowhere in
    their shipped files -- not in a note, a title or a blocker."""
    if not R1.is_file():
        pytest.skip("the R1 research registry (developer-machine evidence) is absent")
    registry = {d["dataset_id"]: d for d in json.loads(R1.read_text(encoding="utf-8"))["datasets"]}

    def numbers(node):
        if isinstance(node, bool):
            return
        if isinstance(node, (int, float)):
            yield node
        elif isinstance(node, dict):
            for key, value in node.items():
                if key not in ("loc", "st", "sources"):
                    yield from numbers(value)
        elif isinstance(node, list):
            for value in node:
                yield from numbers(value)
    for rid in RIGHTS_LIMITED:
        if rid not in registry:
            continue
        text = (RECORDS / f"{rid}.json").read_text(encoding="utf-8")
        tokens = set(re.findall(r"\d+(?:\.\d+)?", text))
        withheld = {repr(float(n)).removesuffix(".0") for n in numbers(registry[rid])
                    if n not in (0, 1)}
        leaked = {w for w in withheld if len(w) >= 3 and w in tokens}
        assert not leaked, (rid, leaked)


def test_the_nasa_records_do_not_invent_what_the_reports_leave_out(corpus):
    tnd = corpus.record("DS-TND7133").propellant
    assert not tnd.exact_formulation
    binder = [i for i in tnd.ingredients if "Binder" in i.source_name]
    assert len(binder) == 1 and binder[0].custom is None and binder[0].provider_name is None
    jpl = corpus.record("DS-JPL-ALTPROP-BATES").propellant
    assert not jpl.exact_formulation
    assert [i.custom for i in jpl.ingredients] == [None] * len(jpl.ingredients)
    rsrm = corpus.record("DS-RSRM9").propellant
    assert all(isinstance(i.fraction, Missing) and i.fraction.reason is MissingReason.NOT_REPORTED
               for i in rsrm.ingredients)                  # the 1979 baseline is not borrowed
    assert "reconstructed" in corpus.record("DS-RSRM9").notes
    assert "ignition" in corpus.record("DS-RSRM9").notes
    cr = corpus.record("DS-CR2478-STERILIZABLE").propellant
    assert all(isinstance(i.fraction, Missing) and i.fraction.reason is MissingReason.NOT_AUDITED
               for i in cr.ingredients)


def test_the_fractions_stay_as_printed_and_are_not_normalised(corpus):
    printed = {i.source_name: (i.fraction.value, i.fraction.unit)
               for i in corpus.record("DS-JPL-ALTPROP-BATES").propellant.ingredients}
    assert printed == {"AP": (69.6, "wt%"), "Al": (16.0, "wt%"), "Fe2O3": (0.4, "wt%"),
                       "PBAN": (14.0, "wt%")}
    tnd = [i.fraction.value for i in corpus.record("DS-TND7133").propellant.ingredients]
    assert tnd == [46.0, 13.0, 6.0, 19.0, 16.0]


# ---------------------------------------------------------------- comparison cases


def test_every_named_comparison_case_exists(corpus):
    known = {case.case_id for case in ALL_CASES}
    for record in corpus.records:
        assert set(record.comparison_case_ids) <= known, record.record_id


def test_every_case_states_its_database_and_origin():
    for case in ALL_CASES:
        assert isinstance(case, ReferenceCase) and case.database_version.strip()
        assert case.origin is CaseOrigin.IMPORTED            # all are held as data


def test_the_report_cases_are_independent_code_without_a_verdict():
    for case in solid_reports.SOLID_REPORT_CASES:
        assert case.source_kind is SourceKind.INDEPENDENT_CODE and not case.allows_verdict
        assert case.code_version == "not stated" and case.database_version == "not stated"


def test_the_jpl_cstar_inconsistency_is_recorded_as_printed_not_resolved():
    case = solid_reports.JPL_79_29_TP_H1148_THEORETICAL
    assert "characteristic_velocity" not in {q.key for q in case.quantities}
    entry = [m for m in case.missing if m.startswith("characteristic_velocity")]
    assert len(entry) == 1 and "'1371 (5155)'" in entry[0]


def test_the_rp1311_cases_keep_their_values():
    """Provenance was added; not one number moved."""
    ex5 = rp1311.RP1311_EXAMPLE5_PUBLISHED
    temps = {q.key: q.value for q in ex5.quantities}
    assert temps["chamber_temperature"] == 2723.021 and temps["molar_mass"] == 22.290
    assert "8e5df1cc" in ex5.database_version
    assert rp1311_historical.RP1311_EXAMPLE5_PRINT_1996.database_version.startswith("not stated")


# ---------------------------------------------------------------- EV-3, honest per record


@pytest.fixture()
def no_solve(monkeypatch):
    """Library names all present (stub); every solve path counts."""
    calls = {"solve": 0}

    def probe(names):
        asked = tuple(dict.fromkeys(names))
        return gateway.LibrarySpeciesProbe(usable=True, names=asked, present=asked,
                                           status="stub", library_version="stub",
                                           database="thermo.lib", database_sha256="f" * 64,
                                           probed=asked)
    monkeypatch.setattr(gateway, "probe_solid_library_species", probe)

    def counted(*_args, **_kwargs):
        calls["solve"] += 1
        raise AssertionError("an assessment must not solve")
    for name in ("solve_solid_chamber_state", "solve_solid_equilibrium_cstar"):
        monkeypatch.setattr(gateway, name, counted)
    return calls


EXPECTED_STATES = {
    "DS-TND7133": bridge.CompatibilityState.UNDERDEFINED,
    "DS-JPL-ALTPROP-BATES": bridge.CompatibilityState.UNDERDEFINED,
    "DS-RSRM9": bridge.CompatibilityState.UNDERDEFINED,
    "DS-CR2478-STERILIZABLE": bridge.CompatibilityState.NOT_A_CEA_TARGET,
    **{rid: bridge.CompatibilityState.NOT_A_CEA_TARGET for rid in RIGHTS_LIMITED},
}


@pytest.mark.parametrize("rid", sorted(EXPECTED_STATES))
def test_the_explicit_check_answers_each_gate4_record_honestly(corpus, no_solve, rid):
    record = corpus.record(rid)
    result = bridge.assess(record, corpus.sources)
    assert result.state is EXPECTED_STATES[rid]
    assert not result.executable and result.formulation is None
    assert no_solve["solve"] == 0
    if result.state is bridge.CompatibilityState.UNDERDEFINED:
        codes = {b.code for b in result.blockers}
        assert codes and bridge.WITHHELD_RIGHTS not in codes


def test_rp1311_answer_is_unchanged(corpus, no_solve):
    result = bridge.assess(corpus.record("DS-RP1311-E5"), corpus.sources)
    assert result.state is bridge.CompatibilityState.EXECUTABLE_VERIFIED
    assert result.thermochemistry_key == "rp1311-example5"
    assert no_solve["solve"] == 0
