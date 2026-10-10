"""DB-2B Wave 2: accounting, the frozen gates on the Wave 2 targets, and the boundaries.

Every DB-0.5 assertion of a Wave 2 engine is decided once. Each test below changes the
manifest the way a careless or motivated author might and checks that a gate refuses it.
"""

from __future__ import annotations

import collections
import copy
import json
import pathlib
import re
import sys
import types

import pytest

from rocketforge.evidence.engines import corpus_to_dict

ROOT =pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference_engines"))
import db2a_manifest  # noqa: E402
import db2b_wave2_manifest as wave2  # noqa: E402
import promote_db2a  # noqa: E402

P = db2a_manifest.P


@pytest.fixture(scope="module")
def research():
    return promote_db2a.load_research()


def manifest():
    return types.SimpleNamespace(**copy.deepcopy(vars(promote_db2a.load_manifest())))


def refused(research, m, match):
    with pytest.raises(promote_db2a.PromotionError) as caught:
        promote_db2a.build_corpus(research, m)
    assert any(match in p for p in caught.value.problems), caught.value.problems


def entry(m, aid):
    return next(e for e in m.ASSERTIONS if e["db05_id"] == aid)


def promote(m, *entries):
    for e in entries:
        m.NOT_PROMOTED.pop(e["db05_id"], None)
    m.ASSERTIONS = (*m.ASSERTIONS, *entries)
    return m


def add_configuration(m, engine, cfg, variant):
    m.SEED_SUBJECTS[engine] = (*m.SEED_SUBJECTS.get(engine, ()), cfg)
    m.CONFIGURATIONS = (*m.CONFIGURATIONS, (cfg, variant, cfg, ("MISSING", "NOT_AUDITED", "test"), ""))
    return m


# ------------------------------------------------------------------ accounting


def test_every_wave2_assertion_is_decided_once(research):
    seed = {a for a, r in research.assertions.items() if r["engine_id"] in wave2.SEED_ENGINES}
    promoted = {e["db05_id"] for e in wave2.ASSERTIONS}
    assert promoted | set(wave2.NOT_PROMOTED) == seed and not promoted & set(wave2.NOT_PROMOTED)


def test_accounting_totals(research):
    totals = collections.Counter(v[0] for v in wave2.NOT_PROMOTED.values())
    assert len(wave2.ASSERTIONS) == 34
    assert dict(totals) == {"WITHHELD_RIGHTS": 33, "WITHHELD_CONFLICT": 5, "SECONDHAND_MANUFACTURER_VALUE": 4,
                            "MISSING_REQUIRED_SEMANTICS": 4, "DUPLICATE": 3, "WRONG_CONFIGURATION": 2,
                            "INFERRED_ONLY": 1, "NOT_NEEDED": 1, "DISCOVERY_ONLY_SOURCE": 1}
    assert len(wave2.ASSERTIONS) + sum(totals.values()) == 88


def test_rights_refused_targets_ship_nothing():
    """RL10A-4-2 and Rutherford: every opened document carries a copyright notice."""
    for prefix in ("AS-DB05-US-RL10A-4-2-", "AS-DB05-NZ-RUTHERFORD-"):
        assert not [e for e in wave2.ASSERTIONS if e["db05_id"].startswith(prefix)]
        assert all(v[0] in ("WITHHELD_RIGHTS",) for k, v in wave2.NOT_PROMOTED.items() if k.startswith(prefix))
    for engine in ("ENG-US-RL10A-4-2", "ENG-NZ-RUTHERFORD", "ENG-NZ-RUTHERFORD-VACUUM"):
        assert wave2.SEED_SUBJECTS[engine] == ()


# ------------------------------------------------------------------ no owner decision


def test_wave2_records_no_owner_decision():
    assert not hasattr(wave2, "OWNER_DECISIONS") and not hasattr(wave2, "OWNER_REVIEWS")
    assert not [c for c, d in wave2.RESEARCH_CONFLICTS.items() if {"owner_accepted", "owner_released", "owner_scope"} & set(d)]
    merged = promote_db2a.load_manifest()
    assert set(merged.OWNER_DECISIONS) == {"CF-DB05-J2-THRUST", "CF-DB05-SPS-THRUST", "CF-DB05-F1-RATING", "CF-DB05-F1-PC"}
    for sid, spec in wave2.SOURCES.items():
        assert not promote_db2a._OWNER_REVIEW_WORDS.search(spec["review_note"]), sid
        assert not any(sid in r["sources"] for r in merged.OWNER_REVIEWS.values()), sid


def test_a_wave2_value_cannot_be_owner_released_without_a_recorded_decision(research):
    m = manifest()
    m.RESEARCH_CONFLICTS["CF-DB05-RS68A-THRUST"]["owner_released"] = ("AS-DB05-US-RS-68A-002",)
    refused(research, m, "owner_released needs the owner's recorded decision")


# ------------------------------------------------------------------ RL10A-4-2


def test_an_rl10a42_value_cannot_pick_a_side_of_the_a41_a42_columns(research):
    m = add_configuration(manifest(), "ENG-US-RL10A-4-2", "CFG-RL10A-4-2", "VAR-RL10A-3-3A")
    m = promote(m, P("AS-DB05-US-RL10A-4-2-001", "CFG-RL10A-4-2", "performance.thrust_vac", ("number", 22300),
                     "NOMINAL", cond=dict(environment="VACUUM")))
    refused(research, m, "withholds AS-DB05-US-RL10A-4-2-001, which is promoted")
    refused(research, m, "SRC-NAP-11780: withheld")


def test_rl10a33a_values_cannot_be_filed_under_another_rl10(research):
    m = promote(manifest(), P("AS-DB05-US-RL10A-3-3A-007", "CFG-RL10B-2-DIV", "performance.thrust", ("text",), "OTHER"))
    refused(research, m, "is not an identity of ENG-US-RL10A-3-3A")


# ------------------------------------------------------------------ RL10B-2


@pytest.mark.parametrize("aid,field,value", [("AS-DB05-US-RL10B-2-002", "performance.chamber_pressure", 644),
                                             ("AS-DB05-US-RL10B-2-005", "performance.specific_impulse_vac", 465.5)])
def test_the_unresolved_rl10b2_pc_isp_pair_cannot_ship(research, aid, field, value):
    cond = (dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN") if "pressure" in field
            else dict(environment="VACUUM", isp_basis="UNKNOWN"))
    m = promote(manifest(), P(aid, "CFG-RL10B-2-DIV", field, ("number", value), "NOMINAL", cond=cond))
    refused(research, m, f"withholds {aid}, which is promoted")


def test_rl10b2_architecture_ships_without_its_performance(research):
    corpus = promote_db2a.build_corpus(research, manifest())
    fields = {a.field_path for a in corpus.assertions if a.subject.id == "CFG-RL10B-2-DIV"}
    assert {"propellants.oxidizer", "propellants.fuel"} <= fields
    assert not {"performance.chamber_pressure", "performance.specific_impulse_vac"} & fields


# ------------------------------------------------------------------ RD-170


def test_the_rockwell_reconstruction_cannot_be_relabelled_original(research):
    for provenance in ("ORIGINAL_MANUFACTURER", "ORIGINAL_CONTRACTOR", "ORIGINAL_AGENCY"):
        m = manifest()
        m.SCHEMATICS["SCH-DB05-RD170-RKWL-P19"]["provenance"] = provenance
        refused(research, m, f"is a third-party reconstruction in DB-0.5, not {provenance}")


@pytest.mark.parametrize("aid,value", [("AS-DB05-SU-RD-170-008", 2.58), ("AS-DB05-SU-RD-170-009", 2.47)])
def test_the_rd170_mixture_ratio_conflict_cannot_be_normalised_away(research, aid, value):
    m = promote(manifest(), P(aid, "CFG-RD-170", "propellants.mixture_ratio", ("number", value), "NOMINAL"))
    refused(research, m, f"withholds {aid}, which is promoted")
    m = manifest()
    m.RESEARCH_CONFLICTS["CF-DB05-RD170-MR"]["withhold"] = ()
    m = promote(m, P(aid, "CFG-RD-170", "propellants.mixture_ratio", ("number", value), "NOMINAL"))
    refused(research, m, f"claim assertion {aid} is not listed as withheld")


def test_the_rd170_secondary_sources_stay_secondary(research):
    corpus = promote_db2a.build_corpus(research, manifest())
    src = {s.reference.source_id: s for s in corpus.sources}
    for sid in ("SRC-NTRS-19910018906", "SRC-DB05-NTRS-19950002748"):
        assert src[sid].primacy.value == "SECONDARY" and src[sid].authority.value == "B"


# ------------------------------------------------------------------ IPD


def test_a_cycle_label_cannot_make_a_graph(research):
    for engine, cfg in (("ENG-US-IPD", "CFG-IPD"), ("ENG-NZ-RUTHERFORD", "CFG-IPD")):
        m = manifest()
        m.TOPOLOGIES = (*m.TOPOLOGIES, dict(
            engine=engine, topology_id="TOPO-X", scope=("CONFIGURATION", cfg), label="x", schematic_ids=(),
            text_source_ids=(), withhold_nodes={}, withhold_edges={}, restate_nodes={}, restate_edges={},
            restate_omissions={}, extra_omissions=(), notes=""))
        refused(research, m, f"no DB-0.5 topology for {engine}")


def test_a_blocked_source_is_not_evidence(research):
    m = manifest()
    m.SOURCES["SRC-DTIC-ADA397910"] = dict(m.SOURCES["SRC-NTRS-IPD-WPB"])
    problems = promote_db2a.source_problems("SRC-DTIC-ADA397910", research, m)
    assert any("ACCESS_BLOCKED" in p for p in problems), problems


def test_the_ipd_design_goal_comes_from_the_document_that_prints_it(research):
    """Review finding: the value came from one document and its kind from another. Without a reading the
    kind gate refuses it. With a reading the frozen kind gate accepts any written reading, so the
    manifest's choice (IPD-013 from the document that prints the goal) is held by the corpus-level test
    in tests/evidence/test_reference_engine_wave2.py, which pins IPD-001 out of production."""
    m = promote(manifest(), P("AS-DB05-US-IPD-001", "VAR-IPD", "performance.thrust", ("number", 250000), "DESIGN_VALUE",
                              cond=dict(environment="UNKNOWN")))
    refused(research, m, "AS-DB05-US-IPD-001: value kind DESIGN_VALUE is not what the source prints")


def test_the_ipd_design_goal_is_not_a_tested_engine_value(research):
    """Filing the programme goal on the tested configuration is refused. The refusal comes from the
    same-place rule (the goal shares its page with the variant-level programme statements); the frozen kind
    gate does not read 'designing' as a design word, so it would not refuse NOMINAL on its own."""
    m = manifest()
    entry(m, "AS-DB05-US-IPD-013").update(subject="CFG-IPD", value_kind="NOMINAL", reading="")
    refused(research, m, "printed in the same place as configuration statements (AS-DB05-US-IPD-013)")


# ------------------------------------------------------------------ RS-68A


def test_rs68_baseline_wording_cannot_reach_the_rs68a(research):
    m = manifest()
    m.CONFIGURATIONS = tuple((c[:4] + ("RS-68: more than 650,000 lb of thrust (sea level).",)) if c[0] == "CFG-RS-68A"
                             else c for c in m.CONFIGURATIONS)
    refused(research, m, "carries withheld wording")


def test_a_discovery_only_blog_cannot_speak_for_the_rs68a(research):
    """Review finding: a launch-day blog shipped with authority A. DB-1 calls a blog E: discovery only."""
    assert "SRC-NASA-PSP-BLOG-WORKHORSE" not in wave2.SOURCES
    m = promote(manifest(), P("AS-DB05-US-RS-68A-001", "CFG-RS-68A", "identity.vehicle", ("text",), "OTHER"))
    refused(research, m, "CFG-RS-68A takes values from SRC-DB05-NTRS-20090014109 only")


def test_the_conflicted_rs68a_thrust_cannot_ship(research):
    m = promote(manifest(), P("AS-DB05-US-RS-68A-002", "CFG-RS-68A", "performance.thrust", ("number", 702000),
                              "NOMINAL", cond=dict(environment="UNKNOWN")))
    refused(research, m, "withholds AS-DB05-US-RS-68A-002, which is promoted")


# ------------------------------------------------------------------ LR87


def test_lr87_values_cannot_cross_to_another_variant_or_the_family(research):
    m = manifest()
    entry(m, "AS-DB05-US-LR87-AJ-11-001")["subject"] = "CFG-LR87-AJ-5"
    refused(research, m, "is not an identity of ENG-US-LR87-AJ-11")
    m = manifest()
    entry(m, "AS-DB05-US-LR87-AJ-11-001")["subject"] = "FAM-LR87"
    refused(research, m, "not filed on family FAM-LR87")


def test_the_lr87_mixture_ratio_direction_is_not_guessed(research):
    m = promote(manifest(), P("AS-DB05-US-LR87-AJ-11-017", "CFG-LR87-AJ-11-T3E", "propellants.mixture_ratio",
                              ("number", 1.915), "NOMINAL", reading="O/F from the flows 1,135 / 592",
                              cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL")))
    refused(research, m, "mixture ratio form OXIDIZER_TO_FUEL is not printed")


# ------------------------------------------------------------------ Rutherford


def test_rutherford_values_cannot_cross_sea_level_and_vacuum(research):
    m = add_configuration(manifest(), "ENG-NZ-RUTHERFORD", "CFG-RUTHERFORD-SL", "VAR-RL10B-2")
    m = promote(m, P("AS-DB05-NZ-RUTHERFORD-VACUUM-003", "CFG-RUTHERFORD-SL", "performance.thrust_vac",
                     ("number", 5800), "NOMINAL", cond=dict(environment="VACUUM")))
    refused(research, m, "is not an identity of ENG-NZ-RUTHERFORD-VACUUM")


def test_rutherford_copyright_refuses_its_values(research):
    m = add_configuration(manifest(), "ENG-NZ-RUTHERFORD", "CFG-RUTHERFORD-SL", "VAR-RL10B-2")
    m = promote(m, P("AS-DB05-NZ-RUTHERFORD-008", "CFG-RUTHERFORD-SL", "performance.thrust_sl", ("number", 5600),
                     "NOMINAL", cond=dict(environment="SEA_LEVEL")))
    refused(research, m, "SRC-RKLB-PAYLOAD-INCREASE: withheld")


# ------------------------------------------------------------------ global


def test_the_build_is_deterministic(research):
    one = promote_db2a.corpus_to_json(promote_db2a.build_corpus(research, manifest()))
    two = promote_db2a.corpus_to_json(promote_db2a.build_corpus(research, manifest()))
    assert one == two == promote_db2a.OUTPUT.read_text(encoding="utf-8")


def test_wave2_adds_only_its_targets(research):
    """The corpus without the Wave 2 manifest is exactly the shipped corpus minus Wave 2's records."""
    import importlib
    earlier = promote_db2a.merge_manifests(*(importlib.import_module(n) for n in promote_db2a.MANIFESTS[:-1]))
    before = corpus_to_dict(promote_db2a.build_corpus(research, earlier))
    after = corpus_to_dict(promote_db2a.build_corpus(research, manifest()))
    for kind, items in before.items():
        if isinstance(items, list):
            new = {json.dumps(x, sort_keys=True) for x in after[kind]}
            assert all(json.dumps(x, sort_keys=True) in new for x in items), kind
    added = {a["assertion_id"] for a in after["assertions"]} - {a["assertion_id"] for a in before["assertions"]}
    assert added == {e["db05_id"] for e in wave2.ASSERTIONS}


def test_production_code_never_reads_research_files():
    """No executable string in the package names the research tree (docstrings may cite it)."""
    import ast
    for path in (ROOT / "rocketforge").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                      if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                      and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                assert not re.search(r"engine_database|db05|docs/research", node.value), (path, node.value[:80])
