"""DB-4A: the regression-acceptance review of the shipped reference-engine candidates.

Each hazard below changes one evidence record (through the frozen DB-1 types, never the shipped file) or one
call, and checks that the review refuses what it must: a delivered value as an ideal expected output, a design
value or a limit, an unknown environment or pressure station, a conflicted value, a family value standing in
for a configuration's, a tolerance read off the result. Nothing here runs a solver.
"""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import pathlib

import pytest

from rocketforge.application.analysis import reference_engine_regression as review
from rocketforge.application.analysis.reference_engine_catalog import ReferenceEngineCatalog, load_reference_engines
from rocketforge.evidence.engines import Conflict, RangeValue
from rocketforge.evidence.engines.capabilities import Capability, CapabilityStatus
from rocketforge.evidence.engines.identity import SubjectRef
from rocketforge.evidence.values import ShippingPolicy, ValueStatus
from rocketforge.evidence.engines.vocabulary import (
    Admissibility,
    ConflictCategory,
    ConflictResolution,
    Environment,
    IspBasis,
    MixtureRatioBasis,
    PressureStation,
    SubjectKind,
    ValueKind,
)
from rocketforge.evidence.engines.assertions import Qualifier

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHIPPED = ROOT / "rocketforge" / "data" / "evidence" / "engines" / "reference_engines.json"
#: The accepted corpus at 670e2c6. DB-4A changes no evidence.
SHIPPED_SHA256 = "18108af7e7524983665821133405f936e4ff8deb27d718f50607b244fdbada59"
J2, J2S = "CFG-J2-230K", "CFG-J2S"


@pytest.fixture(scope="module")
def catalog():
    return load_reference_engines()


def _edit(catalog, aid, **changes):
    """A catalog whose one assertion is changed through the frozen types (validation still runs)."""
    corpus = catalog.corpus
    assertions = tuple(dataclasses.replace(a, **changes) if a.assertion_id == aid else a for a in corpus.assertions)
    return ReferenceEngineCatalog(dataclasses.replace(corpus, assertions=assertions), catalog.fingerprint)


def _cond(catalog, aid, **changes):
    a = catalog.corpus.assertion_map[aid]
    return _edit(catalog, aid, conditions=dataclasses.replace(a.conditions, **changes))


def _q(catalog_or_review, cfg, quantity):
    r = review.review_candidate(catalog_or_review, cfg)
    return next(q for q in r.quantities if q.quantity == quantity)


# ------------------------------------------------------------------ the shipped candidates


def test_candidates_are_exactly_the_capability_supported_set(catalog):
    supported = {e.configuration_id for e in catalog.entries()
                 if catalog.capability(e.configuration_id, Capability.REGRESSION_CANDIDATE).status
                 is CapabilityStatus.SUPPORTED}
    assert set(review.regression_candidates(catalog)) == supported == {J2, J2S}
    assert {r.configuration_id for r in review.review_all(catalog)} == supported
    # research-only candidates (RS-25 SLS 109%, SPS Block I, RL10A-3-3A) are not production candidates
    assert not {"CFG-RS25-SLS", "CFG-SPS-BLOCK-I", "CFG-RL10A-3-3A"} & set(review.regression_candidates(catalog))


def test_eligibility_alone_accepts_nothing(catalog):
    """REGRESSION_CANDIDATE means eligible for review; the review accepts no hard regression today."""
    reviews = review.review_all(catalog)
    assert reviews and all(not r.hard_regressions for r in reviews)
    results = {(r.configuration_id, q.quantity): q.result for r in reviews for q in r.quantities}
    assert results == {
        (J2, "thrust"): review.BLOCKED_MISSING_INPUTS, (J2, "specific_impulse"): review.BLOCKED_SEMANTICS,
        (J2, "chamber_pressure"): review.INPUT_ELIGIBLE, (J2, "mixture_ratio"): review.BLOCKED_SEMANTICS,
        (J2, "area_ratio"): review.INPUT_ELIGIBLE,
        (J2S, "thrust"): review.BLOCKED_MISSING_INPUTS, (J2S, "specific_impulse"): review.BLOCKED_SEMANTICS,
        (J2S, "chamber_pressure"): review.INPUT_ELIGIBLE, (J2S, "mixture_ratio"): review.BLOCKED_SEMANTICS,
        (J2S, "area_ratio"): review.INPUT_ELIGIBLE,
    }


def test_every_blocked_quantity_says_why(catalog):
    for r in review.review_all(catalog):
        for q in r.quantities:
            assert (q.result == review.INPUT_ELIGIBLE) == (q.blockers == ()), q


# ------------------------------------------------------------------ adversarial hazards


def test_1_delivered_isp_never_becomes_a_hard_expected_value(catalog):
    """Make every input complete and the Isp's basis known: still delivered against ideal, so efficiency only."""
    c = _cond(catalog, "AS-DB05-US-J-2-004", mixture_ratio_basis=MixtureRatioBasis.THRUST_CHAMBER)
    c = _cond(c, "AS-DB05-US-J-2-002", isp_basis=IspBasis.THRUST_CHAMBER)
    isp = _q(c, J2, "specific_impulse")
    assert isp.result == review.EFFICIENCY_COMPARISON_ONLY != review.HARD_REGRESSION_ELIGIBLE
    assert any("delivered" in b for b in isp.blockers)
    assert any("owner decision" in b for b in isp.blockers)      # no accepted efficiency class exists


def test_1b_even_an_ideal_source_value_does_not_lock_the_model_without_its_model_choices(catalog):
    c = _cond(catalog, "AS-DB05-US-J-2-004", mixture_ratio_basis=MixtureRatioBasis.THRUST_CHAMBER)
    a = c.corpus.assertion_map["AS-DB05-US-J-2-002"]
    c = _cond(c, "AS-DB05-US-J-2-002", isp_basis=IspBasis.THRUST_CHAMBER,
              qualifiers=(*a.conditions.qualifiers, Qualifier("performance_basis", "ideal")))
    isp = _q(c, J2, "specific_impulse")
    assert isp.result == review.BLOCKED_SEMANTICS
    assert any("gamma basis" in b for b in isp.blockers)


@pytest.mark.parametrize("kind", [ValueKind.DESIGN_VALUE, ValueKind.LIMIT, ValueKind.MINIMUM, ValueKind.MAXIMUM,
                                  ValueKind.PREDICTION, ValueKind.APPROXIMATE])
def test_2_3_design_values_limits_and_bounds_are_never_expected_outputs(catalog, kind):
    c = _edit(catalog, "AS-DB05-US-J-2-002", value_kind=kind)
    isp = _q(c, J2, "specific_impulse")
    assert isp.result == review.BLOCKED_SEMANTICS
    assert any(f"value kind {kind.value} is not a point value" in b for b in isp.blockers)


@pytest.mark.parametrize("aid,cfg,quantity", [("AS-DB05-US-J-2-002", J2, "specific_impulse"),
                                              ("AS-DB05-US-J-2-003", J2, "chamber_pressure")])
def test_an_average_is_never_taken_as_the_operating_point_value(catalog, aid, cfg, quantity):
    """Average-to-nominal laundering: an average, as an output or an input, is refused by the review itself."""
    c = _edit(catalog, aid, value_kind=ValueKind.AVERAGE)
    q = _q(c, cfg, quantity)
    assert q.result == review.BLOCKED_SEMANTICS
    assert any("value kind AVERAGE is not a point value" in b for b in q.blockers)


def test_an_average_output_stays_blocked_with_every_other_input_complete(catalog):
    c = _cond(catalog, "AS-DB05-US-J-2-004", mixture_ratio_basis=MixtureRatioBasis.THRUST_CHAMBER)
    c = _cond(c, "AS-DB05-US-J-2-002", isp_basis=IspBasis.THRUST_CHAMBER)
    c = _edit(c, "AS-DB05-US-J-2-002", value_kind=ValueKind.AVERAGE)
    assert _q(c, J2, "specific_impulse").result == review.BLOCKED_SEMANTICS


@pytest.mark.parametrize("changes,reason", [
    ({"admissibility": Admissibility.REJECTED_OTHER}, "not admitted"),
    ({"status": ValueStatus.INFERRED}, "INFERRED"),
])
def test_the_review_keeps_every_evidence_regression_blocker(catalog, changes, reason):
    """The review is called directly here, so it must not rely on the capability having filtered first."""
    c = _edit(catalog, "AS-DB05-US-J-2-003", **changes)
    pc = _q(c, J2, "chamber_pressure")
    assert pc.result == review.BLOCKED_SEMANTICS
    assert any(reason in b for b in pc.blockers)


def test_a_value_that_is_not_one_number_is_never_an_expected_output(catalog):
    a = catalog.corpus.assertion_map["AS-DB05-US-J-2-002"]
    c = _cond(catalog, "AS-DB05-US-J-2-004", mixture_ratio_basis=MixtureRatioBasis.THRUST_CHAMBER)
    c = _cond(c, "AS-DB05-US-J-2-002", isp_basis=IspBasis.THRUST_CHAMBER)
    c = _edit(c, "AS-DB05-US-J-2-002", value=RangeValue(a.value.value, a.value.value + 5.0))
    isp = _q(c, J2, "specific_impulse")
    assert isp.result == review.BLOCKED_SEMANTICS and any("not a single number" in b for b in isp.blockers)


def test_a_propulsion_unit_value_never_stands_for_the_engine(catalog, monkeypatch):
    """A cluster's thrust is not the engine's. No unit ships today, so a catalog is made to hand one over."""
    original = catalog.corpus.assertion_map["AS-DB05-US-J-2-001"]
    cluster = dataclasses.replace(original, subject=SubjectRef(SubjectKind.PROPULSION_UNIT, "PU-TEST-CLUSTER"),
                                  operating_point_id=None)
    real = ReferenceEngineCatalog.assertions
    monkeypatch.setattr(ReferenceEngineCatalog, "assertions",
                        lambda self, cfg: tuple(cluster if a.assertion_id == original.assertion_id else a
                                                for a in real(self, cfg)))
    thrust = _q(catalog, J2, "thrust")
    assert thrust.result == review.BLOCKED_SEMANTICS
    assert any("propulsion unit" in b for b in thrust.blockers)


def test_values_a_source_may_not_ship_block_with_rights(catalog):
    corpus = catalog.corpus
    sid = corpus.assertion_map["AS-DB05-US-J-2-002"].source_id
    policy = ShippingPolicy.METADATA_ONLY
    sources = tuple(dataclasses.replace(s, rights=dataclasses.replace(s.rights, values=policy),
                                        reference=dataclasses.replace(s.reference, shipping=policy))
                    if s.source_id == sid else s for s in corpus.sources)
    c = ReferenceEngineCatalog(dataclasses.replace(corpus, sources=sources), catalog.fingerprint)
    isp = _q(c, J2, "specific_impulse")
    assert isp.result == review.BLOCKED_RIGHTS and any("may not ship" in b for b in isp.blockers)


def test_4_unknown_environment_blocks_an_environment_dependent_comparison(catalog):
    c = _cond(catalog, "AS-DB05-US-J-2S-002", environment=Environment.UNKNOWN)
    isp = _q(c, J2S, "specific_impulse")
    assert isp.result == review.BLOCKED_SEMANTICS
    assert any("environment not stated" in b for b in isp.blockers)


def test_4b_altitude_without_an_ambient_pressure_is_an_unknown_environment(catalog):
    c = _cond(catalog, "AS-DB05-US-J-2-004", mixture_ratio_basis=MixtureRatioBasis.THRUST_CHAMBER)
    c = _cond(c, "AS-DB05-US-J-2-002", isp_basis=IspBasis.THRUST_CHAMBER, environment=Environment.ALTITUDE)
    isp = _q(c, J2, "specific_impulse")
    assert isp.result == review.BLOCKED_SEMANTICS
    assert any("environment not stated (ALTITUDE" in b for b in isp.blockers)


def test_5_unknown_pressure_station_blocks_the_chamber_pressure_input(catalog):
    c = _cond(catalog, "AS-DB05-US-J-2S-003", pressure_station=PressureStation.UNKNOWN)
    pc = _q(c, J2S, "chamber_pressure")
    assert pc.result == review.BLOCKED_SEMANTICS
    assert any("pressure station UNKNOWN" in b for b in pc.blockers)
    assert any("input chamber_pressure: BLOCKED_SEMANTICS" in b for b in _q(c, J2S, "specific_impulse").blockers)


@pytest.mark.parametrize("resolution", [ConflictResolution.UNRESOLVED, ConflictResolution.PARTIALLY_RESOLVED])
def test_6_an_open_conflict_blocks_the_affected_value(catalog, resolution):
    corpus = catalog.corpus
    conflict = Conflict("CF-TEST-J2-ISP", "performance.specific_impulse_vac",
                        ("AS-DB05-US-J-2-002", "AS-DB05-US-J-2S-002"), resolution,
                        () if resolution is ConflictResolution.UNRESOLVED else (ConflictCategory.DIFFERENT_VARIANT,),
                        "test: two Isp claims nobody has reconciled")
    c = ReferenceEngineCatalog(dataclasses.replace(corpus, conflicts=(conflict,)), catalog.fingerprint)
    isp = _q(c, J2, "specific_impulse")
    assert isp.result == review.BLOCKED_CONFLICT
    assert any(f"{resolution.value} conflict CF-TEST-J2-ISP" in b for b in isp.blockers)


@pytest.mark.parametrize("kind", [SubjectKind.VARIANT, SubjectKind.FAMILY])
def test_7_a_variant_or_family_value_never_supplies_a_configuration_expected_output(catalog, kind, monkeypatch):
    entry = catalog.entry(J2)
    subject = SubjectRef(kind, entry.variant_id if kind is SubjectKind.VARIANT else entry.family_id)
    c = _edit(catalog, "AS-DB05-US-J-2-002", subject=subject, operating_point_id=None)
    # through the catalog: the value is the configuration's context, never its own
    assert _q(c, J2, "specific_impulse").result == review.BLOCKED_MISSING_INPUTS
    # and the review's own filter, even if a catalog handed it the family/variant record as the configuration's
    moved = c.corpus.assertion_map["AS-DB05-US-J-2-002"]
    real = ReferenceEngineCatalog.assertions
    monkeypatch.setattr(ReferenceEngineCatalog, "assertions", lambda self, cfg: (*real(self, cfg), moved))
    isp = _q(c, J2, "specific_impulse")
    assert isp.assertion_ids == () and isp.result == review.BLOCKED_MISSING_INPUTS


def test_8_a_source_input_is_not_mislabelled_as_an_expected_output(catalog):
    r = review.review_candidate(catalog, J2)
    inputs = {aid for q in r.quantities if q.role == "input" for aid in q.assertion_ids}
    outputs = {aid for q in r.quantities if q.role == "expected_output" for aid in q.assertion_ids}
    assert "AS-DB05-US-J-2-003" in inputs and not inputs & outputs
    assert {q.quantity for q in r.quantities if q.role == "expected_output"} == {"thrust", "specific_impulse"}


def test_9_a_tolerance_cannot_be_read_off_the_result():
    assert review.tolerance_problems("OBSERVED_DIFFERENCE", derived_after_comparison=True)
    assert review.tolerance_problems("STATED_UNCERTAINTY", derived_after_comparison=True)
    assert review.tolerance_problems("WIDENED_UNTIL_IT_PASSES", derived_after_comparison=False)
    # printed precision is a reading bound, not an uncertainty: not a basis on its own
    assert review.tolerance_problems("PRINTED_PRECISION", derived_after_comparison=False)
    assert review.tolerance_problems("STATED_UNCERTAINTY", derived_after_comparison=False) == ()


def test_engine_mixture_ratio_is_not_taken_as_the_thrust_chambers(catalog):
    mr = _q(catalog, J2, "mixture_ratio")
    assert mr.result == review.BLOCKED_SEMANTICS and any("ENGINE mixture ratio" in b for b in mr.blockers)


def test_thrust_needs_a_size_no_source_records(catalog):
    c = _cond(catalog, "AS-DB05-US-J-2-004", mixture_ratio_basis=MixtureRatioBasis.THRUST_CHAMBER)
    thrust = _q(c, J2, "thrust")
    assert thrust.result == review.BLOCKED_MISSING_INPUTS
    assert any("throat area or mass flow" in b for b in thrust.blockers)


# ------------------------------------------------------------------ no write path, no solver, no corpus change


def test_11_the_review_has_no_write_path_and_no_solver(catalog):
    source = inspect.getsource(review)
    for forbidden in ("open(", "write_text", "write_bytes", "json.dump", "unlink", "shutil"):
        assert forbidden not in source, forbidden
    for layer in ("rocketforge.providers", "rocketforge.physics", "rocketforge.engineering", "rocketforge.engine.",
                  "PySide6"):
        assert layer not in source, layer
    before = catalog.corpus
    review.review_all(catalog)
    assert catalog.corpus is before
    assert hashlib.sha256(SHIPPED.read_bytes()).hexdigest() == SHIPPED_SHA256


def test_12_the_production_corpus_is_byte_for_byte_the_accepted_one():
    assert hashlib.sha256(SHIPPED.read_bytes()).hexdigest() == SHIPPED_SHA256
