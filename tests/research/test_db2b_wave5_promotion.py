"""DB-2B Wave 5 (the rest of the backlog): accounting, what ships, and the frozen gates on the Wave 5 targets.

Every DB-0.5 assertion of a Wave 5 engine is decided once, and with this wave no research assertion stays undecided.
Each hazard below changes the manifest the way a careless or motivated author might and checks that an existing gate
refuses it. No gate was added or loosened for Wave 5.
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
import db2b_wave5_manifest as wave5  # noqa: E402
import promote_db2a  # noqa: E402

P = db2a_manifest.P
R68, R68OP = "CFG-RS68-1999-BASELINE", "OP-RS68-1999-RATED"


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


# ------------------------------------------------------------------ accounting


def test_every_wave5_assertion_is_decided_once(research):
    ids = {i for i, r in research.assertions.items() if r["engine_id"] in wave5.SEED_ENGINES}
    promoted = {e["db05_id"] for e in wave5.ASSERTIONS}
    held = set(wave5.NOT_PROMOTED)
    assert promoted | held == ids and not promoted & held
    assert (len(promoted), len(held)) == (6, 56)


def test_no_research_assertion_stays_undecided(research):
    m = promote_db2a.load_manifest()
    decided = {e["db05_id"] for e in m.ASSERTIONS} | set(m.NOT_PROMOTED)
    assert set(research.assertions) <= decided


def test_wave5_adds_only_its_records_and_changes_nothing_shipped(research):
    names = promote_db2a.MANIFESTS
    upto = names.index("db2b_wave5_manifest")
    earlier = promote_db2a.merge_manifests(*(importlib.import_module(n) for n in names[:upto]))
    through = promote_db2a.merge_manifests(*(importlib.import_module(n) for n in names[:upto + 1]))
    before = corpus_to_dict(promote_db2a.build_corpus(research, earlier))
    after = corpus_to_dict(promote_db2a.build_corpus(research, through))
    for kind, items in before.items():
        if isinstance(items, list):
            new = {json.dumps(x, sort_keys=True) for x in after[kind]}
            assert all(json.dumps(x, sort_keys=True) in new for x in items), kind
    assert {a["assertion_id"] for a in after["assertions"]} - {a["assertion_id"] for a in before["assertions"]} == {
        e["db05_id"] for e in wave5.ASSERTIONS}
    assert {c["configuration_id"] for c in after["configurations"]} - {
        c["configuration_id"] for c in before["configurations"]} == {R68}
    assert len(after["topologies"]) == len(before["topologies"])


def test_the_owner_decisions_are_recorded_and_scoped():
    assert set(wave5.OWNER_DECISIONS) == {"CF-DB05-E-US_HIST-04"}
    assert set(wave5.OWNER_REVIEWS) == {"WAVE5-RS68-RIGHTS", "2026-11-06-NK33-RIGHTS"}
    assert all(r["decision"].startswith("owner (Cemil Eray), 2026-11-06: ") for r in wave5.OWNER_REVIEWS.values())
    assert wave5.OWNER_REVIEWS["WAVE5-RS68-RIGHTS"]["sources"] == ("SRC-DB05-NTRS-20000025317",)
    assert wave5.OWNER_REVIEWS["2026-11-06-NK33-RIGHTS"]["sources"] == ()
    assert set(wave5.SOURCES) == {"SRC-DB05-NTRS-20000025317"}
    note = wave5.SOURCES["SRC-DB05-NTRS-20000025317"]["review_note"]
    assert note.endswith("Owner-reviewed 2026-11-06 (a RocketForge shipping-policy review, not a legal determination).")


# ------------------------------------------------------------------ what ships


def test_rs68_ships_the_1999_baseline_and_no_mixture_ratio(corpus):
    got = {a.field_path: a for a in configuration_assertions(corpus, R68)}
    assert {k: v.value.value for k, v in got.items() if k.startswith(("performance.", "nozzle."))} == {
        "performance.thrust_vac": 745, "performance.thrust_sl": 650, "performance.chamber_pressure": 1410,
        "performance.specific_impulse_vac": 410, "nozzle.area_ratio": 21.5}
    assert got["performance.specific_impulse_vac"].value_kind.value == "AVERAGE"
    assert got["performance.chamber_pressure"].conditions.pressure_station.value == "UNKNOWN"
    assert got["mechanical.mass"].value.text == "Weight, lb < 15,000"
    assert got["mechanical.mass"].value_kind.value == "OTHER"
    assert "propellants.mixture_ratio" not in got


def test_rs68_is_not_a_regression_candidate(corpus):
    result = evaluate_capability(corpus, R68, Capability.REGRESSION_CANDIDATE)
    assert result.status.value == "NOT_SUPPORTED"
    assert any("average" in g for g in result.gaps) and any("mixture_ratio" in g for g in result.gaps)


@pytest.mark.parametrize("prefix", ["AS-DB05-RU-RD-180-", "AS-DB05-RU-RD-171M-", "AS-DB05-SU-NK-33-",
                                    "AS-DB05-SU-RD-0120-", "AS-DB05-US-H-1-0", "AS-DB05-US-LR87-AJ-5-",
                                    "AS-DB05-US-LR87-AJ-7-", "AS-DB05-US-LR91-AJ-5-",
                                    "AS-DB05-US-SSME-FPL-PHASE-I-"])
def test_the_other_nine_engines_ship_nothing(corpus, prefix):
    assert not [i for i in corpus.assertion_map if i.startswith(prefix)]


# ------------------------------------------------------------------ the gates still refuse


def test_gate_refuses_a_guessed_rs68_mixture_ratio_direction(research):
    m = promote(manifest(), P("AS-DB05-US-RS-68-004", R68, "propellants.mixture_ratio", ("number", 6.0), "RATED",
                              op=R68OP, op_basis="AS-DB05-US-RS-68-001 (the slide's 'Rated' column)",
                              cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="ENGINE")))
    refused(research, m, "mixture ratio form OXIDIZER_TO_FUEL is not printed")


def test_gate_refuses_the_nk33_slides(research):
    m = promote(manifest(), P("AS-DB05-SU-NK-33-008", R68, "nozzle.area_ratio", ("number", 27.7), "NOMINAL"))
    refused(research, m, "SRC-NAS-DEPS-068011: not in the manifest's source list")


def test_gate_refuses_the_proposed_rd180_on_the_rs68(research):
    m = promote(manifest(), P("AS-DB05-RU-RD-180-006", R68, "propellants.mixture_ratio", ("number", 2.6), "NOMINAL",
                              cond=dict(mixture_ratio_basis="UNKNOWN")))
    refused(research, m, f"subject {R68} is not an identity of ENG-RU-RD-180")


def test_gate_refuses_a_conflict_value_without_the_owners_decision(research):
    m = manifest()
    del m.OWNER_DECISIONS["CF-DB05-E-US_HIST-04"]
    del m.RESEARCH_CONFLICTS["CF-DB05-E-US_HIST-04"]["owner_accepted"]
    refused(research, m, "not carrying it needs the owner's recorded decision")


def test_gate_refuses_the_rights_note_without_the_review(research):
    m = manifest()
    del m.OWNER_REVIEWS["WAVE5-RS68-RIGHTS"]
    refused(research, m, "the rights note says owner-reviewed, but no OWNER_REVIEWS entry lists the source")


def test_the_shipped_file_is_what_the_manifests_build():
    assert promote_db2a.main(["--check"]) == 0
