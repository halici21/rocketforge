"""DB-2B Wave 3 (Japan, Europe, China): accounting, the frozen gates on the Wave 3 targets, and the boundaries.

Every DB-0.5 assertion of a Wave 3 engine is decided once. Each hazard below changes the manifest the way a
careless or motivated author might -- crossing variants, promoting a development figure, ignoring an epoch
conflict, laundering a restricted source, guessing a translated qualifier -- and checks that an existing gate
refuses it. No gate was added or loosened for Wave 3.
"""

from __future__ import annotations

import copy
import importlib
import json
import pathlib
import re
import sys
import types

import pytest

from rocketforge.evidence.engines import corpus_to_dict

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference_engines"))
import db2a_manifest  # noqa: E402
import db2b_wave3_manifest as wave3  # noqa: E402
import promote_db2a  # noqa: E402

P = db2a_manifest.P
LE7 = "CFG-LE7-H2-1990-REVIEW"
TARGETS = {"ENG-JP-LE-7", "ENG-JP-LE-7A", "ENG-JP-LE-9", "ENG-FR-VULCAIN", "ENG-FR-VULCAIN-2", "ENG-FR-VINCI",
           "ENG-CN-YF-75", "ENG-CN-YF-75D", "ENG-CN-YF-100", "ENG-CN-YF-77"}


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


def add_configuration(m, engine, cfg, variant, family=None):
    if family:
        m.FAMILIES = (*m.FAMILIES, (family, family, ""))
        m.VARIANTS = (*m.VARIANTS, (variant, family, variant, ""))
        m.SEED_SUBJECTS[engine] = (family, variant)
    m.SEED_SUBJECTS[engine] = (*m.SEED_SUBJECTS.get(engine, ()), cfg)
    m.CONFIGURATIONS = (*m.CONFIGURATIONS, (cfg, variant, cfg, ("MISSING", "NOT_AUDITED", "test"), ""))
    return m


# ------------------------------------------------------------------ accounting and boundaries


def test_wave3_seeds_are_exactly_the_target_groups_and_target_7():
    assert set(wave3.SEED_ENGINES) == TARGETS == set(wave3.ACCOUNTED_ENGINES)
    # target 7 is one existing DB-0 Chinese engine, not a substitute geography or a second pick
    extra = TARGETS - {"ENG-JP-LE-7", "ENG-JP-LE-7A", "ENG-JP-LE-9", "ENG-FR-VULCAIN", "ENG-FR-VULCAIN-2",
                       "ENG-FR-VINCI", "ENG-CN-YF-75", "ENG-CN-YF-75D", "ENG-CN-YF-100"}
    assert extra == {"ENG-CN-YF-77"}
    db0 = {e["id"] for e in json.loads((ROOT / "docs/research/engine_database/data/engines.json")
                                       .read_text(encoding="utf-8"))["engines"]}
    assert TARGETS <= db0


def test_every_wave3_research_assertion_is_decided_once(research):
    ids = {a for a, r in research.assertions.items() if r["engine_id"] in TARGETS}
    promoted = {e["db05_id"] for e in wave3.ASSERTIONS}
    assert ids == promoted | set(wave3.NOT_PROMOTED) and not (promoted & set(wave3.NOT_PROMOTED))
    assert len(ids) == 114


def test_only_existing_dispositions_are_used_and_no_owner_decision_releases_anything():
    assert not hasattr(wave3, "DISPOSITIONS")  # the Wave 1/2 vocabulary only
    earlier = set(promote_db2a.merge_manifests(*(importlib.import_module(n) for n in promote_db2a.MANIFESTS[:-1]))
                  .DISPOSITIONS)
    assert {why[0] for why in wave3.NOT_PROMOTED.values()} <= earlier
    assert wave3.OWNER_DECISIONS == {}
    assert not any("owner_accepted" in d or "owner_released" in d for d in wave3.RESEARCH_CONFLICTS.values())


#: The owner's decisions of 2026-10-12, word for word.
OWNER_TEXT = {
    "WAVE3-MEXT-NASDA-1997": "MEXT-hosted NASDA 1997 source: DO NOT CLEAR FOR SHIPPING.",
    "WAVE3-1990-TABLE-MATES": "Vulcain and LE-7 1990 review table-mate values: KEEP WITHHELD. Do not add owner_released.",
    "WAVE3-1990-SECONDARY-VALUES": "1990 secondary performance values: KEEP WITHHELD FROM PRODUCTION PERFORMANCE.",
    "WAVE3-NTRS-RIGHTS": "New NTRS source rights reading: ACCEPT as Owner-reviewed 2026-10-12.",
}


def test_the_owner_decisions_are_recorded_literally_and_release_nothing(research):
    assert set(wave3.OWNER_REVIEWS) == set(OWNER_TEXT)
    for key, text in OWNER_TEXT.items():
        decision = wave3.OWNER_REVIEWS[key]["decision"]
        assert decision.startswith("owner (Cemil Eray), 2026-10-12: ") and text in decision, key
    # only the rights review names a source, and that source was already shipping
    assert {k: r["sources"] for k, r in wave3.OWNER_REVIEWS.items() if r["sources"]} == {
        "WAVE3-NTRS-RIGHTS": ("SRC-DB05-NTRS-19910018905",)}
    note = wave3.SOURCES["SRC-DB05-NTRS-19910018905"]["review_note"]
    assert note.endswith("Owner-reviewed 2026-10-12 (a RocketForge shipping-policy review, not a legal determination).")
    # tier and authority are preserved: secondary, not upgraded
    spec = wave3.SOURCES["SRC-DB05-NTRS-19910018905"]
    assert (spec["authority"], spec["primacy"]) == ("B", "SECONDARY")
    # nothing more ships than before the decisions: the same three assertions
    assert {e["db05_id"] for e in wave3.ASSERTIONS} == {
        "AS-DB05-JP-LE-7-001", "AS-DB05-JP-LE-7-002", "AS-DB05-JP-LE-7-003"}
    assert "SRC-MEXT-SAC-1997" in wave3.WITHHELD_SOURCES
    held = {i for d in wave3.RESEARCH_CONFLICTS.values() for i in d.get("withhold", ())}
    table_mates = {a for a, why in wave3.NOT_PROMOTED.items() if why[0] == "OWNER_DECISION_REQUIRED"}
    assert table_mates and table_mates <= held


def test_an_owner_review_cannot_cover_a_withheld_source(research):
    m = manifest()
    m.OWNER_REVIEWS["WAVE3-MEXT-NASDA-1997"] = dict(m.OWNER_REVIEWS["WAVE3-MEXT-NASDA-1997"],
                                                    sources=("SRC-MEXT-SAC-1997",))
    refused(research, m, "OWNER_REVIEWS WAVE3-MEXT-NASDA-1997: SRC-MEXT-SAC-1997 is not a shipped source")


def test_wave3_adds_only_its_records_and_changes_nothing_shipped(research):
    names = promote_db2a.MANIFESTS
    upto = names.index("db2b_wave3_manifest")
    earlier = promote_db2a.merge_manifests(*(importlib.import_module(n) for n in names[:upto]))
    before = corpus_to_dict(promote_db2a.build_corpus(research, earlier))
    after = corpus_to_dict(promote_db2a.build_corpus(research, manifest()))
    for kind, items in before.items():
        if isinstance(items, list):
            new = {json.dumps(x, sort_keys=True) for x in after[kind]}
            assert all(json.dumps(x, sort_keys=True) in new for x in items), kind
    added = {a["assertion_id"] for a in after["assertions"]} - {a["assertion_id"] for a in before["assertions"]}
    assert added == {e["db05_id"] for e in wave3.ASSERTIONS} == {
        "AS-DB05-JP-LE-7-001", "AS-DB05-JP-LE-7-002", "AS-DB05-JP-LE-7-003"}
    assert {c["configuration_id"] for c in after["configurations"]} - {c["configuration_id"] for c in
                                                                       before["configurations"]} == {LE7}
    assert len(after["topologies"]) == len(before["topologies"]) == 8
    assert len(after["schematics"]) == len(before["schematics"])


def test_promotion_is_deterministic(research):
    a = corpus_to_dict(promote_db2a.build_corpus(research, manifest()))
    b = corpus_to_dict(promote_db2a.build_corpus(research, manifest()))
    assert a == b


# ------------------------------------------------------------------ LE-7 / LE-7A


def test_le7_ships_architecture_only_from_its_own_review(corpus):
    shipped = [a for a in corpus.assertions if a.subject.id == LE7]
    assert {a.field_path for a in shipped} == {"propellants.oxidizer", "propellants.fuel", "architecture.cycle"}
    assert {a.source_id for a in shipped} == {"SRC-DB05-NTRS-19910018905"}
    assert {a.locator for a in shipped} == {wave3_locator("AS-DB05-JP-LE-7-001")}
    cycle = next(a for a in shipped if a.field_path == "architecture.cycle")
    assert cycle.value.token == "STAGED_COMBUSTION"  # no rich side inferred from 'Staged Combustion'


def wave3_locator(aid):
    return promote_db2a.load_research().assertions[aid]["locator"]


def test_no_le7a_value_crosses_into_the_le7(corpus, research):
    assert not any(a.assertion_id.startswith("AS-DB05-JP-LE-7A-") for a in corpus.assertions)
    m = manifest()
    promote(m, P("AS-DB05-JP-LE-7A-013", LE7, "performance.thrust_vac", ("number", 1100), "NOMINAL",
                 cond=dict(environment="VACUUM")))
    refused(research, m, "is not an identity of ENG-JP-LE-7A")


def unwithhold(m, cid, aid):
    """Take an id off the manifest's own withhold list, so the refusal must come from a frozen gate."""
    d = m.RESEARCH_CONFLICTS[cid]
    d["withhold"] = tuple(i for i in d["withhold"] if i != aid)
    return m


def test_development_figures_do_not_become_configuration_ratings(research):
    # the 1990 review's 265,000 lbf is a claim of the open epoch conflict: the claim gate refuses it
    m = unwithhold(manifest(), "CF-DB05-LE7-EPOCH", "AS-DB05-JP-LE-7-007")
    promote(m, P("AS-DB05-JP-LE-7-007", LE7, "performance.thrust_vac", ("number", 265000), "NOMINAL",
                 cond=dict(environment="VACUUM")))
    refused(research, m, "claim assertion AS-DB05-JP-LE-7-007 is not listed as withheld")


def test_a_table_mate_of_an_open_epoch_needs_the_owner(research):
    m = unwithhold(manifest(), "CF-DB05-LE7-EPOCH", "AS-DB05-JP-LE-7-011")
    promote(m, P("AS-DB05-JP-LE-7-011", LE7, "nozzle.area_ratio", ("number", 60), "NOMINAL"))
    refused(research, m, "promoted AS-DB05-JP-LE-7-011 is printed in the same table as a withheld rating claim")


def test_p18_architecture_is_a_table_mate_but_p16_is_independent(research):
    """The decisive distinction: the same cycle from the p.18 rating table is refused; from p.16 it ships."""
    m = manifest()
    m.ASSERTIONS = tuple(e for e in m.ASSERTIONS if e["db05_id"] != "AS-DB05-JP-LE-7-003")
    m.NOT_PROMOTED["AS-DB05-JP-LE-7-003"] = ("DUPLICATE", "test")
    promote(m, P("AS-DB05-JP-LE-7-004", LE7, "architecture.cycle", ("enum", "STAGED_COMBUSTION"), "NOMINAL"))
    refused(research, m, "promoted AS-DB05-JP-LE-7-004 is printed in the same table as a withheld rating claim")
    promote_db2a.build_corpus(research, manifest())  # the p.16 statement passes every gate


def test_the_nasda_table_is_withheld_until_its_rights_are_reviewed(research):
    m = manifest()
    promote(m, P("AS-DB05-JP-LE-7-021", LE7, "mechanical.length", ("number", 3243), "NOMINAL"))
    refused(research, m, "SRC-MEXT-SAC-1997: withheld")


# ------------------------------------------------------------------ LE-9


def test_le9_development_data_cannot_populate_a_flight_configuration(research):
    m = add_configuration(manifest(), "ENG-JP-LE-9", "CFG-LE9-TEST", "VAR-LE-9", family="FAM-LE9")
    promote(m, P("AS-DB05-JP-LE-9-002", "CFG-LE9-TEST", "performance.thrust_vac", ("number", 1471), "NOMINAL",
                 cond=dict(environment="VACUUM")))
    refused(research, m, "SRC-JAXA-PRESS-LE9-2017: withheld")


def test_a_cycle_label_generates_no_topology(corpus):
    assert not [t for t in corpus.topologies if t.scope.id == LE7]
    assert not wave3.TOPOLOGIES and not wave3.SCHEMATICS
    from rocketforge.evidence.engines.capabilities import Capability, evaluate_capability
    assert evaluate_capability(corpus, LE7, Capability.TOPOLOGY).status.value == "NOT_SUPPORTED"


# ------------------------------------------------------------------ Vulcain / Vulcain 2


def test_vulcain_briefing_table_waits_for_the_owner(research):
    m = add_configuration(manifest(), "ENG-FR-VULCAIN", "CFG-VULCAIN-TEST", "VAR-VULCAIN", family="FAM-VULCAIN")
    unwithhold(m, "CF-DB05-VULCAIN-THRUST", "AS-DB05-FR-VULCAIN-002")
    m.CONFIGURATION_SOURCES["CFG-VULCAIN-TEST"] = ("SRC-NTRS-19910018907",)
    m.SOURCES["SRC-NTRS-19910018907"] = dict(wave3.SOURCES["SRC-DB05-NTRS-19910018905"],
                                             organization="Orbital Technologies Corp.")
    promote(m, P("AS-DB05-FR-VULCAIN-002", "CFG-VULCAIN-TEST", "architecture.cycle", ("enum", "GAS_GENERATOR"),
                 "NOMINAL"))
    refused(research, m, "promoted AS-DB05-FR-VULCAIN-002 is printed in the same table as a withheld rating claim")


def test_vulcain_values_cannot_cross_into_vulcain_2(research):
    m = add_configuration(manifest(), "ENG-FR-VULCAIN-2", "CFG-V2-TEST", "VAR-VULCAIN-2", family="FAM-VULCAIN")
    promote(m, P("AS-DB05-FR-VULCAIN-016", "CFG-V2-TEST", "performance.thrust_vac", ("number", 115), "NOMINAL",
                 cond=dict(environment="VACUUM")))
    refused(research, m, "is not an identity of ENG-FR-VULCAIN")


# ------------------------------------------------------------------ Vinci


def test_vinci_epochs_are_not_collapsed(research):
    decision = wave3.RESEARCH_CONFLICTS["CF-DB05-VINCI-EPOCH"]
    assert decision["decision"] == "WITHHOLD"
    assert set(decision["withhold"]) == {"AS-DB05-FR-VINCI-002", "AS-DB05-FR-VINCI-004"}
    conflict = research.conflicts["CF-DB05-VINCI-EPOCH"]
    # NASA's 2011 table placed 180 kN in vacuum (PARTIALLY_RESOLVED); the two ESA epochs still stay apart.
    assert conflict["resolution"] in ("UNRESOLVED", "PARTIALLY_RESOLVED") and conflict["kind"] == "different_epoch"
    target = research.assertions["AS-DB05-FR-VINCI-002"]
    assert "programme target" in target["conditions"]["kind"]


# ------------------------------------------------------------------ YF-75 / YF-75D / YF-100 / YF-77


def test_yf75d_cannot_fill_a_yf75_configuration(research):
    m = add_configuration(manifest(), "ENG-CN-YF-75", "CFG-YF75-TEST", "VAR-YF-75", family="FAM-YF75")
    promote(m, P("AS-DB05-CN-YF-75D-001", "CFG-YF75-TEST", "identity.summary", ("text",), "OTHER"))
    refused(research, m, "is not an identity of ENG-CN-YF-75D")


def test_yf100_derivative_is_not_aliased_into_the_baseline(corpus, research):
    assert not [a for a in corpus.aliases if "YF" in a.name.upper()]
    assert "post-pump swing" in research.assertions["AS-DB05-CN-YF-100-003"]["value_as_printed"]
    assert wave3.NOT_PROMOTED["AS-DB05-CN-YF-100-003"][0] == "WITHHELD_RIGHTS"


def test_china_ships_nothing_because_every_source_is_restricted(corpus):
    assert not any(a.assertion_id.startswith("AS-DB05-CN-") for a in corpus.assertions)
    reasons = {wave3.NOT_PROMOTED[a][0] for a in wave3.NOT_PROMOTED if a.startswith("AS-DB05-CN-")}
    assert reasons == {"WITHHELD_RIGHTS"}


# ------------------------------------------------------------------ multilingual


def test_an_untranslated_direction_is_never_supplied(research):
    """混合比 5.9 prints no direction; a translator's 'O/F' cannot be added."""
    m = manifest()
    m.WITHHELD_SOURCES.pop("SRC-JAXA-PRESS-LE9-2017")  # isolate the semantic gate from the rights gate
    m = add_configuration(m, "ENG-JP-LE-7A", "CFG-LE7A-TEST", "VAR-LE-7A", family="FAM-LE7A")
    promote(m, P("AS-DB05-JP-LE-7A-017", "CFG-LE7A-TEST", "propellants.mixture_ratio", ("number", 5.9), "NOMINAL",
                 cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL")))
    refused(research, m, "mixture ratio form OXIDIZER_TO_FUEL is not printed")


def test_original_language_and_gloss_are_kept_apart(research):
    jp = [r for r in research.assertions.values() if r["source_id"] == "SRC-MEXT-SAC-1997"]
    assert jp and all(re.search(r"[぀-ヿ一-鿿]", r["value_as_printed"]) for r in jp)
    assert all("not a translation source" in r["note"] for r in jp)
    thrust = research.assertions["AS-DB05-JP-LE-7-015"]
    assert thrust["unit_as_printed"] == "tonf" and thrust["value"] == 110
    # no source is a translation, and no gloss is cited as a source
    assert not [d for d in research.documents.values() if re.search(r"(?i)\btranslat", d.get("title_as_printed") or "")]


def test_every_restricted_source_is_named_and_none_ships(corpus):
    shipped = {s.reference.source_id for s in corpus.sources}
    assert not set(wave3.WITHHELD_SOURCES) & shipped
    assert "SRC-DB05-NTRS-19910018905" in shipped


def test_production_never_reads_the_wave3_research_files():
    package = ROOT / "rocketforge"
    for path in package.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "ledger_wave3" not in text and "db2b_wave3_manifest" not in text, path
