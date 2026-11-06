"""DB-2B Wave 4 (US design and test documents): accounting, the frozen gates on the Wave 4 targets, and the boundaries.

Every DB-0.5 assertion of a Wave 4 engine is decided once. Each hazard below changes the manifest the way a careless
or motivated author might and checks that an existing gate refuses it. No gate was added or loosened for Wave 4.
"""

from __future__ import annotations

import copy
import importlib
import json
import pathlib
import sys
import types

import pytest

from rocketforge.evidence.engines import corpus_to_dict
from rocketforge.evidence.engines.capabilities import Capability, configuration_assertions, evaluate_capability

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference_engines"))
import db2a_manifest  # noqa: E402
import db2b_wave4_manifest as wave4  # noqa: E402
import promote_db2a  # noqa: E402

P = db2a_manifest.P
RL, RLOP = "CFG-RL10A-3-3-FR1769", "OP-RL10A-3-3-FR1769-OF5"
LR, H200, F1A = "CFG-LR91-AJ-11-T3E", "CFG-H1-200K-S-IB-4", "CFG-F1A-MSFC-2013"
TARGETS = {"ENG-US-RL10A-3-3", "ENG-US-LR91-AJ-11", "ENG-US-H-1-200K", "ENG-US-F-1A"}


@pytest.fixture(scope="module")
def research():
    return promote_db2a.load_research()


@pytest.fixture(scope="module")
def corpus(research):
    return promote_db2a.build_corpus(research)


def manifest():
    return types.SimpleNamespace(**copy.deepcopy(vars(promote_db2a.load_manifest())))


def refused(research, m, match):
    with pytest.raises(promote_db2a.PromotionError) as caught:
        promote_db2a.build_corpus(research, m)
    assert any(match in p for p in caught.value.problems), caught.value.problems


def promote(m, *entries):
    for e in entries:
        m.NOT_PROMOTED.pop(e["db05_id"], None)
    m.ASSERTIONS = (*m.ASSERTIONS, *entries)
    return m


def numbers(corpus, cfg):
    return {a.field_path: a.value.value for a in configuration_assertions(corpus, cfg) if hasattr(a.value, "value")}


# ------------------------------------------------------------------ accounting


def test_every_wave4_assertion_is_decided_once(research):
    ids = {i for i, r in research.assertions.items() if r["engine_id"] in TARGETS}
    promoted = {e["db05_id"] for e in wave4.ASSERTIONS}
    held = set(wave4.NOT_PROMOTED)
    assert promoted | held == ids and not promoted & held
    assert (len(promoted), len(held)) == (29, 9)


def test_wave4_adds_only_its_records_and_changes_nothing_shipped(research):
    names = promote_db2a.MANIFESTS
    upto = names.index("db2b_wave4_manifest")
    earlier = promote_db2a.merge_manifests(*(importlib.import_module(n) for n in names[:upto]))
    before = corpus_to_dict(promote_db2a.build_corpus(research, earlier))
    after = corpus_to_dict(promote_db2a.build_corpus(research, manifest()))
    for kind, items in before.items():
        if isinstance(items, list):
            new = {json.dumps(x, sort_keys=True) for x in after[kind]}
            assert all(json.dumps(x, sort_keys=True) in new for x in items), kind
    added = {a["assertion_id"] for a in after["assertions"]} - {a["assertion_id"] for a in before["assertions"]}
    assert added == {e["db05_id"] for e in wave4.ASSERTIONS}
    assert {c["configuration_id"] for c in after["configurations"]} - {
        c["configuration_id"] for c in before["configurations"]} == {RL, LR, H200, F1A}
    assert len(after["topologies"]) == len(before["topologies"])


def test_the_owner_review_covers_rights_only_and_releases_nothing():
    assert wave4.OWNER_DECISIONS == {} and set(wave4.OWNER_REVIEWS) == {"WAVE4-NTRS-RIGHTS"}
    review = wave4.OWNER_REVIEWS["WAVE4-NTRS-RIGHTS"]
    assert review["decision"].startswith("owner (Cemil Eray), 2026-11-06: ")
    assert set(review["sources"]) == set(wave4.SOURCES)
    for spec in wave4.SOURCES.values():
        assert spec["review_note"].endswith(
            "Owner-reviewed 2026-11-06 (a RocketForge shipping-policy review, not a legal determination).")
    assert wave4.SOURCES["SRC-DB05-NTRS-20140011656"]["primacy"] == "SECONDARY"
    assert not any("owner_accepted" in d or "owner_released" in d for d in wave4.RESEARCH_CONFLICTS.values())


def test_gate_refuses_an_owner_review_word_no_review_lists(research):
    m = manifest()
    m.OWNER_REVIEWS = {k: v for k, v in m.OWNER_REVIEWS.items() if k != "WAVE4-NTRS-RIGHTS"}
    refused(research, m, "the rights note says owner-reviewed, but no OWNER_REVIEWS entry lists the source")


# ------------------------------------------------------------------ what ships


def test_rl10a33_ships_design_estimates_without_a_chamber_pressure(corpus):
    got = numbers(corpus, RL)
    assert got["performance.thrust_vac"] == 15000 and got["performance.specific_impulse"] == 444
    assert got["chamber.throat_diameter"] == 5.14 and got["performance.cstar"] == 7626
    assert "performance.chamber_pressure" not in got
    assert not {a.assertion_id for a in configuration_assertions(corpus, RL)} & {
        "AS-DB05-US-RL10A-3-3-004", "AS-DB05-US-RL10A-3-3-013", "AS-DB05-US-RL10A-3-3-014"}


def test_h1_200k_is_an_average_not_a_rating(corpus):
    thrust = next(a for a in configuration_assertions(corpus, H200) if a.field_path == "performance.thrust_sl")
    assert thrust.value_kind.value == "AVERAGE" and thrust.value.value == 200.53 and thrust.unit_as_printed == "Kips"
    assert "AS-DB05-US-H-1-200K-001" not in corpus.assertion_map


def test_no_mixture_ratio_ships_without_a_printed_direction(corpus):
    for i in ("AS-DB05-US-LR91-AJ-11-002", "AS-DB05-US-H-1-200K-004", "AS-DB05-US-F-1A-004"):
        assert i not in corpus.assertion_map


@pytest.mark.parametrize("cfg", [RL, LR, H200, F1A])
def test_no_wave4_configuration_is_a_regression_candidate_or_has_a_graph(corpus, cfg):
    assert evaluate_capability(corpus, cfg, Capability.REGRESSION_CANDIDATE).status.value == "NOT_SUPPORTED"
    assert evaluate_capability(corpus, cfg, Capability.TOPOLOGY).status.value == "NOT_SUPPORTED"


# ------------------------------------------------------------------ the gates still refuse


def test_gate_refuses_a_chamber_pressure_held_by_the_open_conflict(research):
    m = promote(manifest(), P("AS-DB05-US-RL10A-3-3-013", RL, "performance.chamber_pressure", ("number", 385.2),
                              "DESIGN_VALUE", op=RLOP, op_basis="AS-DB05-US-RL10A-3-3-015",
                              cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN"),
                              reading="Table V-1 is headed 'Estimated'"))
    refused(research, m, "withholds AS-DB05-US-RL10A-3-3-013, which is promoted")


def test_gate_refuses_a_guessed_mixture_ratio_direction(research):
    m = promote(manifest(), P("AS-DB05-US-F-1A-004", F1A, "propellants.mixture_ratio", ("number", 2.27), "NOMINAL",
                              cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="UNKNOWN")))
    refused(research, m, "mixture ratio form OXIDIZER_TO_FUEL is not printed")


def test_gate_refuses_an_f1a_value_on_the_f1(research):
    m = manifest()
    m.ASSERTIONS = tuple(dict(e, subject="CFG-F1") if e["db05_id"] == "AS-DB05-US-F-1A-002" else e
                         for e in m.ASSERTIONS)
    refused(research, m, "subject CFG-F1 is not an identity of ENG-US-F-1A")


def test_gate_refuses_the_purdue_table_for_the_titan_configuration(research):
    m = promote(manifest(), P("AS-DB05-US-LR91-AJ-11-001", LR, "propellants.mixture_ratio", ("number", 1.78), "NOMINAL",
                              cond=dict(mixture_ratio_basis="UNKNOWN")))
    refused(research, m, "SRC-PURDUE-LR91AJ11: not in the manifest's source list")


def test_gate_refuses_a_value_the_source_does_not_print(research):
    m = manifest()
    m.ASSERTIONS = tuple(dict(e, value=("number", 200530)) if e["db05_id"] == "AS-DB05-US-H-1-200K-002" else e
                         for e in m.ASSERTIONS)
    refused(research, m, "value 200530.0 is not DB-0.5's 200.53")


def test_the_shipped_file_is_what_the_manifests_build():
    assert promote_db2a.main(["--check"]) == 0
