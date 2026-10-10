"""DB-2B Wave 1 promotion: exhaustive accounting, and every Wave-1 hazard refused by a gate.

Each test breaks the merged manifest or the DB-0.5 records one way and expects
the whole build to be refused with a named reason.
"""

from __future__ import annotations

import collections
import copy
import dataclasses
import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference_engines"))
import db2a_manifest  # noqa: E402
import db2b_wave1_manifest as wave1  # noqa: E402
import promote_db2a  # noqa: E402


@pytest.fixture(scope="module")
def research():
    return promote_db2a.load_research()


def manifest():
    return types.SimpleNamespace(**copy.deepcopy(vars(promote_db2a.load_manifest())))


def copy_of(research):
    return dataclasses.replace(research, **{f.name: copy.deepcopy(getattr(research, f.name))
                                            for f in dataclasses.fields(research)})


def refused(research, m, match):
    with pytest.raises(promote_db2a.PromotionError) as caught:
        promote_db2a.build_corpus(research, m)
    assert any(match in p for p in caught.value.problems), caught.value.problems


def entry(m, aid):
    return next(e for e in m.ASSERTIONS if e["db05_id"] == aid)


def topology(m, tid):
    return next(t for t in m.TOPOLOGIES if t["topology_id"] == tid)


def promote(m, *entries, from_not_promoted=True):
    for e in entries:
        if from_not_promoted:
            m.NOT_PROMOTED.pop(e["db05_id"], None)
    m.ASSERTIONS = (*m.ASSERTIONS, *entries)
    return m


# ------------------------------------------------------------------ accounting


def test_every_wave1_assertion_is_decided_once_with_a_disposition(research):
    seed = {a for a, r in research.assertions.items() if r["engine_id"] in wave1.SEED_ENGINES}
    promoted = {e["db05_id"] for e in wave1.ASSERTIONS}
    assert promoted | set(wave1.NOT_PROMOTED) == seed and not promoted & set(wave1.NOT_PROMOTED)
    assert all(isinstance(v, tuple) and v[0] in wave1.DISPOSITIONS for v in wave1.NOT_PROMOTED.values())


def test_accounting_totals(research):
    """The audit the design note reports, recomputed from the manifest."""
    totals = collections.Counter(v[0] for v in wave1.NOT_PROMOTED.values())
    assert len(wave1.ASSERTIONS) == 75
    assert dict(totals) == {"WITHHELD_RIGHTS": 46, "WITHHELD_CONFLICT": 15, "MISSING_REQUIRED_SEMANTICS": 10,
                            "NOT_NEEDED": 14, "SOURCE_SCOPE_TOO_BROAD": 10, "WRONG_CONFIGURATION": 5,
                            "WRONG_OPERATING_POINT": 1, "DUPLICATE": 1}
    assert len(wave1.ASSERTIONS) + sum(totals.values()) == sum(
        1 for r in research.assertions.values() if r["engine_id"] in wave1.SEED_ENGINES)


def test_wave1_records_exactly_the_owners_f1_decisions():
    assert {c for c, d in wave1.RESEARCH_CONFLICTS.items() if "owner_accepted" in d} == {
        "CF-DB05-F1-RATING", "CF-DB05-F1-PC"}
    assert set(wave1.OWNER_DECISIONS) == {"CF-DB05-F1-RATING", "CF-DB05-F1-PC"}
    assert wave1.OWNER_DECISIONS["CF-DB05-F1-PC"].startswith("owner (Cemil Eray), 2026-10-09")
    first, second = wave1.OWNER_DECISIONS["CF-DB05-F1-RATING"]
    assert first.startswith("owner (Cemil Eray), 2026-10-09") and second.startswith("owner (Cemil Eray), 2026-10-10")
    assert "ACCEPT F-1-010 for CFG-F1 only" in second and "Starts: 20; Duration: 2,250 seconds" in second
    assert set(wave1.OWNER_REVIEWS) == {"DB2A-RIGHTS", "WAVE1-RIGHTS", "DB2A-MANIFEST-METADATA",
                                        "DB2A-MANIFEST-AJ10-137-025"}
    assert "AJ10-137-025" in wave1.OWNER_REVIEWS["DB2A-MANIFEST-AJ10-137-025"]["decision"]
    assert "AS-DB05-US-AJ10-137-025" in db2a_manifest.NOT_PROMOTED
    assert set(wave1.OWNER_REVIEWS["WAVE1-RIGHTS"]["sources"]) == set(wave1.SOURCES)
    merged = promote_db2a.load_manifest().RESEARCH_CONFLICTS
    assert {c for c, d in merged.items() if "owner_accepted" in d} == {
        "CF-DB05-J2-THRUST", "CF-DB05-SPS-THRUST", "CF-DB05-F1-RATING", "CF-DB05-F1-PC"}
    # the sea-level rating stays withheld; the DB-0.5 conflicts are not rewritten
    assert set(wave1.RESEARCH_CONFLICTS["CF-DB05-F1-RATING"]["withhold"]) == {"AS-DB05-US-F-1-001", "AS-DB05-US-F-1-018"}


def test_a_missing_or_unknown_disposition_is_refused(research):
    m = manifest()
    m.NOT_PROMOTED["AS-DB05-US-F-1-009"] = "not needed"
    refused(research, m, "needs a (disposition, reason) pair")
    m = manifest()
    m.NOT_PROMOTED["AS-DB05-US-F-1-009"] = ("BORING", "x")
    refused(research, m, "needs a (disposition, reason) pair")


def test_dispositions_are_checked_against_what_they_claim(research):
    m = manifest()
    m.NOT_PROMOTED["AS-DB05-US-F-1-009"] = ("WITHHELD_CONFLICT", "no such conflict")
    refused(research, m, "no research-conflict decision withholds it")
    m = manifest()
    m.NOT_PROMOTED["AS-DB05-US-H-1-188K-009"] = ("WITHHELD_RIGHTS", "the source is fine")
    refused(research, m, "passes the rights gate")
    m = manifest()
    m.NOT_PROMOTED["AS-DB05-US-H-1-188K-009"] = ("SOURCE_NOT_OPENED", "it was")
    refused(research, m, "SOURCE_NOT_OPENED, but SRC-NTRS-19650013470 was read")


def test_manifests_cannot_redefine_each_others_keys():
    other = types.SimpleNamespace(SOURCES={"SRC-NASA-TND7375": {"host": "different"}})
    with pytest.raises(promote_db2a.PromotionError, match="defined twice"):
        promote_db2a.merge_manifests(db2a_manifest, other)


# ------------------------------------------------------------------ J-2S


def test_a_j2_graph_cannot_be_filed_under_the_j2s(research):
    m = manifest()
    spec = copy.deepcopy(topology(m, "TOPO-J2-230K"))
    spec.update(topology_id="TOPO-J2S", scope=("CONFIGURATION", "CFG-J2S"))
    m.TOPOLOGIES = (*m.TOPOLOGIES, spec)
    refused(research, m, "scope CFG-J2S is not an identity of ENG-US-J-2")
    m = manifest()
    spec = dict(copy.deepcopy(topology(m, "TOPO-J2-230K")), engine="ENG-US-J-2S", topology_id="TOPO-J2S",
                scope=("CONFIGURATION", "CFG-J2S"))
    m.TOPOLOGIES = (*m.TOPOLOGIES, spec)
    refused(research, m, "no DB-0.5 topology for ENG-US-J-2S")


def test_a_j2_value_cannot_be_filed_under_the_j2s(research):
    m = manifest()
    entry(m, "AS-DB05-US-J-2-004")["subject"] = "CFG-J2S"
    entry(m, "AS-DB05-US-J-2-004")["operating_point"] = "OP-J2S-MR55"
    refused(research, m, "is not an identity of ENG-US-J-2")


# ------------------------------------------------------------------ F-1


def test_the_f1_rating_conflict_blocks_its_thrust(research):
    m = promote(manifest(), db2a_manifest.P("AS-DB05-US-F-1-001", "CFG-F1", "performance.thrust_sl", ("number", 1522000),
                                            "NOMINAL", cond=dict(environment="SEA_LEVEL")))
    refused(research, m, "withholds AS-DB05-US-F-1-001, which is promoted")


def test_the_f1_viewgraph_values_need_the_owners_decision(research):
    m = manifest()
    del m.RESEARCH_CONFLICTS["CF-DB05-F1-RATING"]["owner_accepted"]
    refused(research, m, "owner_released needs the owner's recorded decision")
    m = manifest()
    m.RESEARCH_CONFLICTS["CF-DB05-F1-RATING"]["owner_accepted"] = "owner, today: accept"
    refused(research, m, "owner_accepted is not the decision recorded in OWNER_DECISIONS")


@pytest.mark.parametrize("aid,field,value,cond", [
    ("AS-DB05-US-F-1-002", "performance.thrust_vac", 1748200, dict(environment="VACUUM")),
    ("AS-DB05-US-F-1-003", "performance.specific_impulse_sl", 265.4, dict(environment="SEA_LEVEL", isp_basis="UNKNOWN")),
    ("AS-DB05-US-F-1-005", "performance.chamber_pressure", 1125, dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN")),
])
@pytest.mark.parametrize("subject", ["VAR-F1", "FAM-F1"])
def test_the_admitted_f1_values_are_not_inherited(research, aid, field, value, cond, subject):
    m = manifest()
    entry(m, aid).update(subject=subject)
    refused(research, m, f"not filed on {'variant' if subject.startswith('VAR') else 'family'} {subject}")


def test_the_f1_sea_level_rating_cannot_be_released(research):
    m = manifest()
    d = m.RESEARCH_CONFLICTS["CF-DB05-F1-RATING"]
    d["owner_released"] = (*d["owner_released"], "AS-DB05-US-F-1-001")
    refused(research, m, "owner_released AS-DB05-US-F-1-001 is a claim of the conflict")


def test_a_release_is_only_for_a_value_printed_with_a_withheld_claim(research):
    m = manifest()
    d = m.RESEARCH_CONFLICTS["CF-DB05-F1-RATING"]
    d["owner_released"] = (*d["owner_released"], "AS-DB05-US-F-1-011")  # area ratio, another slide
    refused(research, m, "owner_released AS-DB05-US-F-1-011 is not a promoted assertion printed with a withheld claim")


def test_the_f1_chamber_pressure_keeps_its_unknown_station_and_needs_the_owner(research):
    m = manifest()
    entry(m, "AS-DB05-US-F-1-005")["conditions"]["pressure_station"] = "NOZZLE_STAGNATION"
    refused(research, m, "must be UNKNOWN")
    m = manifest()
    del m.RESEARCH_CONFLICTS["CF-DB05-F1-PC"]["owner_accepted"]
    refused(research, m, "not carrying it needs the owner's recorded decision")


def test_an_unused_owner_decision_is_refused(research):
    m = manifest()
    m.OWNER_DECISIONS["CF-DB05-F1-MASS"] = "owner (Cemil Eray), 2026-10-09: accept the mass"
    refused(research, m, "CF-DB05-F1-MASS: OWNER_DECISIONS records a decision its conflict does not use")
    m = manifest()  # the same words, recorded under a conflict that does not carry them
    m.OWNER_DECISIONS["CF-DB05-F1-MASS"] = m.OWNER_DECISIONS["CF-DB05-F1-PC"]
    refused(research, m, "CF-DB05-F1-MASS: OWNER_DECISIONS records a decision its conflict does not use")


def test_an_owner_review_must_be_recorded_for_its_source(research):
    m = manifest()
    m.OWNER_REVIEWS["WAVE1-RIGHTS"] = dict(m.OWNER_REVIEWS["WAVE1-RIGHTS"], sources=tuple(
        s for s in m.OWNER_REVIEWS["WAVE1-RIGHTS"]["sources"] if s != "SRC-JSC-19950"))
    refused(research, m, "SRC-JSC-19950: the rights note says owner-reviewed, but no OWNER_REVIEWS entry lists the source")
    m = manifest()
    m.SOURCES["SRC-JSC-19950"]["review_note"] = "government work."
    refused(research, m, "SRC-JSC-19950: listed by OWNER_REVIEWS WAVE1-RIGHTS, but its rights note does not record the review")


def test_an_owner_review_does_not_upgrade_a_withheld_source(research):
    m = manifest()
    m.OWNER_REVIEWS["WAVE1-RIGHTS"]["sources"] += ("SRC-USA-OMS21002",)
    refused(research, m, "OWNER_REVIEWS WAVE1-RIGHTS: SRC-USA-OMS21002 is not a shipped source")


def test_the_f1_mixture_ratio_direction_is_not_guessed(research):
    m = promote(manifest(), db2a_manifest.P("AS-DB05-US-F-1-006", "CFG-F1", "propellants.mixture_ratio", ("number", 2.27),
                                            "NOMINAL",
                                            cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="ENGINE")))
    refused(research, m, "is not printed (O/F)")


def test_withheld_manual_wording_cannot_return_to_the_f1_graph(research):
    m = manifest()
    del topology(m, "TOPO-F1")["restate_omissions"]["helium supply to the heat exchanger (stage)"]
    refused(research, m, "carries withheld wording 'helium'")
    m = manifest()
    topology(m, "TOPO-F1")["restate_omissions"]["4-way control valve and checkout valve"] = "4-way cont"
    refused(research, m, "can only be cut at a word boundary")
    m = manifest()
    topology(m, "TOPO-F1")["restate_omissions"]["4-way control valve and checkout valve"] = "a control valve"
    refused(research, m, "can only be cut at a word boundary")


# ------------------------------------------------------------------ H-1


def test_h1_callouts_cannot_return_in_a_role(research):
    m = manifest()
    topology(m, "TOPO-H1-188K-SA10")["restate_edges"][0]["role"] = "fuel discharge (968 psia)"
    refused(research, m, "deleting the withheld wording")
    m = manifest()
    del topology(m, "TOPO-H1-188K-SA10")["restate_edges"][11]
    refused(research, m, "carries withheld wording 'callout'")


def test_a_digitised_h1_callout_is_not_an_operating_value(research):
    m = promote(manifest(), db2a_manifest.P("AS-DB05-US-H-1-188K-019", "CFG-H1-188K-SA10", "feed.lox_discharge",
                                            ("number", 880), "NOMINAL"))
    refused(research, m, "DIGITISED without the schematic it was read from")


# ------------------------------------------------------------------ LMDE


def test_the_development_lmde_cannot_join_the_final_graph(research):
    m = manifest()
    spec = topology(m, "TOPO-LM-DPS-FINAL")
    spec["schematic_ids"] = (*spec["schematic_ids"], "SCH-DB05-LMDE-TND7143-F6")
    refused(research, m, "schematic SCH-DB05-LMDE-TND7143-F6 is not one the DB-0.5 graph rests on")
    m = manifest()
    topology(m, "TOPO-LM-DPS-FINAL")["notes"] += " Also the helium injection engine."
    refused(research, m, "carries withheld wording 'helium injection'")


def test_a_programme_requirement_cannot_become_a_final_design_value(research):
    m = manifest()
    entry(m, "AS-DB05-US-LMDE-002").update(subject="CFG-LMDE-FINAL", value_kind="NOMINAL", reading="")
    refused(research, m, "printed as a design requirement; promoted as NOMINAL")


# ------------------------------------------------------------------ OMS


def test_the_rights_withheld_oms_workbook_ships_nothing(research):
    m = promote(manifest(), db2a_manifest.P("AS-DB05-US-AJ10-190-002", "CFG-OMS", "performance.specific_impulse",
                                            ("number", 313), "NOMINAL", cond=dict(environment="UNKNOWN", isp_basis="UNKNOWN")))
    refused(research, m, "SRC-USA-OMS21002: withheld")
    m = manifest()
    m.TOPOLOGIES = (*m.TOPOLOGIES, dict(
        engine="ENG-US-AJ10-190", topology_id="TOPO-OMS", scope=("CONFIGURATION", "CFG-OMS"), label="OMS",
        schematic_ids=("SCH-DB05-OMS-WB-F21",), text_source_ids=("SRC-DB05-NTRS-19850008634",),
        withhold_nodes={}, withhold_edges={}, restate_nodes={}, restate_edges={}, restate_omissions={},
        extra_omissions=(), notes=""))
    refused(research, m, "SRC-USA-OMS21002: withheld")


def test_an_unstated_oms_environment_is_not_filled(research):
    m = manifest()
    entry(m, "AS-DB05-US-AJ10-190-004")["conditions"]["environment"] = "VACUUM"
    refused(research, m, "must be UNKNOWN")


def test_a_mirror_host_cannot_claim_an_ntrs_statement(research):
    m = manifest()
    m.SOURCES["SRC-JSC-19950"]["host"] = "GOV_PUBLIC_USE_PERMITTED"
    refused(research, m, "is not what NTRS returned (None)")


# ------------------------------------------------------------------ RS-25


def test_a_block_iia_value_cannot_reach_block_ii(research):
    m = promote(manifest(), db2a_manifest.P("AS-DB05-US-SSME-BLOCK-IIA-004", "CFG-RS25-BLOCK-II", "pumps.HPOTP.speed_rpm",
                                            ("number", 22250), "NOMINAL"))
    refused(research, m, "is not an identity of ENG-US-SSME-BLOCK-IIA")
    refused(research, m, "SRC-ENGINEHISTORY-SSMEORIENT-1998: withheld")


def test_one_rs25_build_cannot_borrow_anothers_source(research):
    m = manifest()
    entry(m, "AS-DB05-US-SSME-BLOCK-II-034").update(subject="CFG-RS25-SLS", operating_point=None)
    refused(research, m, "CFG-RS25-SLS takes values from")


def test_the_boeing_schematic_cannot_become_shipped_topology(research):
    m = manifest()
    m.TOPOLOGIES = (*m.TOPOLOGIES, dict(
        engine="ENG-US-SSME-BLOCK-IIA", topology_id="TOPO-RS25-IIA", scope=("CONFIGURATION", "CFG-RS25-BLOCK-II"),
        label="Block IIA", schematic_ids=("SCH-DB05-RS25IIA-BC9804-S19",),
        text_source_ids=("SRC-ENGINEHISTORY-SSMEORIENT-1998",), withhold_nodes={}, withhold_edges={},
        restate_nodes={}, restate_edges={}, restate_omissions={}, extra_omissions=(), notes=""))
    refused(research, m, "figures are RESTRICTED_REFERENCE")
    refused(research, m, "scope CFG-RS25-BLOCK-II is not an identity of ENG-US-SSME-BLOCK-IIA")
    refused(research, m, "SRC-ENGINEHISTORY-SSMEORIENT-1998: withheld")


def test_an_open_rs25_conflict_blocks_a_value_on_its_field(research):
    m = promote(manifest(), db2a_manifest.P("AS-DB05-US-SSME-BLOCK-II-017", "CFG-RS25-SLS", "performance.thrust_sl",
                                            ("number", 418000), "NOMINAL", op="OP-RS25-SLS-109",
                                            cond=dict(environment="SEA_LEVEL")))
    refused(research, m, "withholds AS-DB05-US-SSME-BLOCK-II-017, which is promoted")


def test_a_promoted_value_on_an_open_conflicts_field_is_refused_even_if_unlisted(research):
    m = manifest()
    m.RESEARCH_CONFLICTS["CF-DB05-RS25-SLTHRUST"]["withhold"] = tuple(
        i for i in m.RESEARCH_CONFLICTS["CF-DB05-RS25-SLTHRUST"]["withhold"] if i != "AS-DB05-US-SSME-BLOCK-II-017")
    promote(m, db2a_manifest.P("AS-DB05-US-SSME-BLOCK-II-017", "CFG-RS25-SLS", "performance.thrust_sl",
                               ("number", 418000), "NOMINAL", op="OP-RS25-SLS-109", cond=dict(environment="SEA_LEVEL")))
    refused(research, m, "states the conflict's field")


# ------------------------------------------------------------------ rights notices


@pytest.mark.parametrize("statement,restrictive", [
    ("NASA JSC training manual; no copyright notice on cover", False),
    ("NASA publication (US Government work); no copyright notice", False),
    ("NTRS GOV_PUBLIC_USE_PERMITTED", False),
    ("p.1: 'Copyright (c) 2004 by United Space Alliance ... All other rights are reserved'", True),
    ("Every page stamped 'BOEING PROPRIETARY'", True),
    ("p.2: '(c) 2002 AIAA ... No copyright is asserted under Title 17, U.S. Code'", True),
    ("(c) 2024 L3Harris Technologies", True),
    ("Reproduction for non-government use ... is not permitted", True),
    ("no copyright notice on the cover, but p.3 prints 'All rights reserved'", True),
])
def test_restrictive_notices_are_recognised(statement, restrictive):
    assert promote_db2a.restrictive_notice(statement) is restrictive


# ------------------------------------------------------------------ review findings (each a confirmed bypass)


@pytest.mark.parametrize("tid,key,kind", [
    ("TOPO-F1", 7, "restate_edges"), ("TOPO-F1", "N-HYP", "restate_nodes"),
    ("TOPO-J2-230K", 15, "restate_edges"), ("TOPO-J2-230K", "N-ASI", "restate_nodes"),
    ("TOPO-SPS-BLOCK-I", "N-INJ", "restate_nodes"),
])
def test_a_restated_text_basis_must_be_recorded_text(research, tid, key, kind):
    m = manifest()
    del topology(m, tid)[kind][key]["text_basis"]
    refused(research, m, "names the DB-0.5 assertions that record that text")
    m = manifest()
    topology(m, tid)[kind][key]["text_basis"] = ("AS-DB05-US-J-2-018",)  # MSFC-MAN-503, not a graph text source
    refused(research, m, "is not a DB-0.5 assertion from one of the graph's text sources")


@pytest.mark.parametrize("kind", ["MAXIMUM", "RATED"])
def test_a_word_in_a_compound_modifier_does_not_justify_a_kind(research, kind):
    m = manifest()
    entry(m, "AS-DB05-US-LMDE-008")["value_kind"] = kind
    refused(research, m, f"value kind {kind} is not what the source prints")


@pytest.mark.parametrize("aid,subject,field,value,cond", [
    ("AS-DB05-US-J-2S-001", "FAM-J2", "performance.thrust_vac", 265000, dict(environment="VACUUM")),
    ("AS-DB05-US-J-2S-008", "VAR-J2S", "nozzle.area_ratio", 40, {}),
    ("AS-DB05-US-H-1-188K-001", "VAR-H1", "performance.thrust_sl", 188000, dict(environment="SEA_LEVEL")),
    ("AS-DB05-US-SSME-BLOCK-I-001", "VAR-RS25", "nozzle.area_ratio", 77.5, {}),
])
def test_a_build_value_is_not_filed_on_a_family_or_variant(research, aid, subject, field, value, cond):
    m = manifest()
    entry(m, aid).update(subject=subject, operating_point=None, cond=cond)
    refused(research, m, "not filed on")


def test_a_requirement_is_not_filed_on_a_propulsion_unit(research):
    m = manifest()
    entry(m, "AS-DB05-US-LMDE-004")["subject"] = "UNIT-LM-DPS-FINAL"
    refused(research, m, "a propulsion unit carries pressurization, feed or tank statements")


def test_withheld_rs25_and_lmde_wording_cannot_ride_in_a_note(research):
    m = manifest()
    entry(m, "AS-DB05-US-SSME-BLOCK-II-034")["note"] = "Block IIA HPFTP 34,311 rpm, MR 6.032 (BC98-04)."
    refused(research, m, "carries withheld wording")
    m = manifest()
    entry(m, "AS-DB05-US-LMDE-013")["note"] = "As on the fixed-area helium injection engine of Fig. 6."
    refused(research, m, "carries withheld wording")


def test_a_rights_withheld_value_cannot_be_relabelled(research):
    m = manifest()
    m.NOT_PROMOTED["AS-DB05-US-AJ10-190-005"] = ("NOT_NEEDED", "a chamber pressure we do not need")
    refused(research, m, "is refused for rights or access; the disposition must say so")


def test_an_invented_owner_decision_is_refused(research):
    m = manifest()
    m.RESEARCH_CONFLICTS["CF-DB05-F1-PC"] = dict(decision="CARRIED_NOT", touches=(), competing={}, argument="x",
                                                 owner_accepted="owner, today: accept")
    refused(research, m, "owner_accepted is not the decision recorded in OWNER_DECISIONS")
    m = manifest()
    m.RESEARCH_CONFLICTS["CF-DB05-J2-THRUST"]["owner_accepted"] += " and more"
    refused(research, m, "owner_accepted is not the decision recorded in OWNER_DECISIONS")


@pytest.mark.parametrize("statement", [
    "no copyright notice on the cover but all rights reserved by Boeing",
    "no copyright notice, although stamped BOEING PROPRIETARY on p.3",
    "no copyright notice except (c) 2024 L3Harris",
])
def test_an_exception_after_no_notice_is_restrictive(statement):
    assert promote_db2a.restrictive_notice(statement) is True


# ------------------------------------------------------------------ second review findings


def test_a_text_basis_must_be_from_the_page_the_locator_adds(research):
    m = manifest()
    topology(m, "TOPO-J2-230K")["restate_nodes"]["N-GG"]["text_basis"] = ("AS-DB05-US-J-2-032",)  # text p.4
    refused(research, m, "but no text basis is from that page")


def test_a_withheld_assertion_is_not_a_text_basis(research):
    m = manifest()
    topology(m, "TOPO-F1")["restate_nodes"]["N-HYP"]["text_basis"] = ("AS-DB05-US-F-1-001",)
    refused(research, m, "is withheld or not shippable")


def test_a_quoted_passage_must_be_in_the_text_basis(research):
    m = manifest()
    topology(m, "TOPO-J2-230K")["restate_nodes"]["N-GG"]["reason"] = (
        "text basis restated: Coffman text p.2 'the gas generator was fed from the start tank'")
    refused(research, m, "none of the passages the reason quotes is in its text basis")


def test_a_reading_does_not_excuse_a_requirement_kind(research):
    m = manifest()
    entry(m, "AS-DB05-US-LMDE-007")["value_kind"] = "NOMINAL"
    refused(research, m, "printed as a design requirement")


def test_a_reading_does_not_excuse_a_build_value_on_a_family(research):
    m = manifest()
    entry(m, "AS-DB05-US-J-2S-001").update(subject="FAM-J2", operating_point=None,
                                           cond=dict(environment="VACUUM"), reading="read as the family's")
    refused(research, m, "not filed on family FAM-J2")


def test_a_requirement_is_not_a_configuration_value(research):
    m = manifest()
    entry(m, "AS-DB05-US-LMDE-007")["subject"] = "CFG-LMDE-FINAL"
    refused(research, m, "a design requirement is not a value of configuration")


def test_a_statement_beside_a_build_is_not_generalised_to_the_variant(research):
    m = promote(manifest(), db2a_manifest.P("AS-DB05-US-SSME-BLOCK-II-026", "VAR-RS25", "identity.block_iia_change",
                                            ("text",), "OTHER"))
    refused(research, m, "printed in the same place as configuration statements")


def test_owner_decisions_are_recorded_text_not_derived():
    assert set(db2a_manifest.OWNER_DECISIONS) == {"CF-DB05-J2-THRUST", "CF-DB05-SPS-THRUST"}
    assert all(isinstance(v, str) and v.startswith("owner (Cemil Eray), 2026-10-09")
               for v in db2a_manifest.OWNER_DECISIONS.values())
    m = manifest()
    m.RESEARCH_CONFLICTS["CF-DB05-SPS-THRUST"]["owner_accepted"] = "owner (Cemil Eray), 2026-10-09: accept all"
    assert m.OWNER_DECISIONS["CF-DB05-SPS-THRUST"] != "owner (Cemil Eray), 2026-10-09: accept all"


def test_a_restricted_source_cannot_be_withheld_as_out_of_scope(research):
    m = manifest()
    m.WITHHELD_SOURCES["SRC-USA-OMS21002"] = dict(m.WITHHELD_SOURCES["SRC-USA-OMS21002"], rights=False)
    refused(research, m, "withheld with rights=False, but its rights record is restrictive")


@pytest.mark.parametrize("words", ["Vacuum Isp 452.3 s", "6,276 lbm/s", "rated 7,268 lb", "7,774 lb"])
def test_l3harris_wording_cannot_ride_in_an_rs25_note(research, words):
    m = manifest()
    entry(m, "AS-DB05-US-SSME-BLOCK-II-034")["note"] = words
    refused(research, m, "carries withheld wording")


def test_withheld_wording_cannot_ride_in_a_variant_note(research):
    m = manifest()
    m.VARIANTS = tuple((v[:3] + ("The SSME; Block IIA HPFTP 34,311 rpm.",)) if v[0] == "VAR-RS25" else v
                       for v in m.VARIANTS)
    refused(research, m, "carries withheld wording")


# ------------------------------------------------------------------ post-change review of the owner gates (2026-10-10)


def _rating(m):
    return m.RESEARCH_CONFLICTS["CF-DB05-F1-RATING"]


def test_a_table_mate_of_a_withheld_rating_cannot_ship_without_the_owner(research):
    """Confirmed bypass: with every owner record removed, the F-1 table values still shipped."""
    m = manifest()
    d = _rating(m)
    del d["owner_released"], d["owner_accepted"], d["owner_scope"]
    del m.OWNER_DECISIONS["CF-DB05-F1-RATING"]
    refused(research, m, "AS-DB05-US-F-1-002 is printed in the same table as a withheld rating claim")


def test_a_release_names_only_values_the_owner_names(research):
    """Confirmed bypass (post-change review): an id added to owner_released, with the owner's words
    unchanged, shipped. Here: the whole qualification-life cell, whose mission duration the owner
    did not admit."""
    m = manifest()
    entry(m, "AS-DB05-US-F-1-010")["value"] = ("text",)
    refused(research, m, "AS-DB05-US-F-1-010 ('Starts 20; Duration 2,250 seconds; mission duration 165 seconds') "
                         "is not a value the owner's recorded decision names")
    m = manifest()
    entry(m, "AS-DB05-US-F-1-010")["value"] = ("text", "Starts 20; Duration 2,250 seconds; mission duration 165 seconds")
    refused(research, m, "is not a value the owner's recorded decision names")


def test_the_f1_qualification_life_needs_its_own_owner_decision(research):
    m = manifest()
    _rating(m)["owner_accepted"] = m.OWNER_DECISIONS["CF-DB05-F1-RATING"][0]
    m.OWNER_DECISIONS["CF-DB05-F1-RATING"] = m.OWNER_DECISIONS["CF-DB05-F1-RATING"][0]
    refused(research, m, "AS-DB05-US-F-1-010 ('Starts 20; Duration 2,250 seconds') is not a value the owner's "
                         "recorded decision names")
    m = manifest()
    d = _rating(m)
    d["owner_released"] = tuple(i for i in d["owner_released"] if i != "AS-DB05-US-F-1-010")
    refused(research, m, "AS-DB05-US-F-1-010 is printed in the same table as a withheld rating claim")


def test_admitted_text_is_only_what_the_source_prints(research):
    m = manifest()
    entry(m, "AS-DB05-US-F-1-010")["value"] = ("text", "Starts 20; Duration 3,000 seconds")
    refused(research, m, "admitted text ['Duration 3,000 seconds'] is not printed in")
    m = manifest()
    entry(m, "AS-DB05-US-F-1-010")["value"] = ("text", " ; ")
    refused(research, m, "AS-DB05-US-F-1-010: admitted text [] is not printed in")


@pytest.mark.parametrize("subject", ["VAR-F1", "FAM-F1"])
def test_the_f1_qualification_life_is_not_inherited(research, subject):
    m = manifest()
    entry(m, "AS-DB05-US-F-1-010")["subject"] = subject
    refused(research, m, f"AS-DB05-US-F-1-010 is authorised by the owner for CFG-F1, but is filed on {subject}")


def test_an_owner_decision_is_scoped_to_the_configuration_it_names(research):
    m = manifest()
    _rating(m)["owner_scope"] = "CFG-H1-188K-SA10"
    refused(research, m, "owner_scope 'CFG-H1-188K-SA10' is not the configuration the owner's decision names (CFG-F1)")
    m = manifest()
    del m.RESEARCH_CONFLICTS["CF-DB05-F1-PC"]["owner_scope"]
    refused(research, m, "CF-DB05-F1-PC: owner_scope None is not the configuration the owner's decision names")


def test_an_owner_decision_does_not_carry_to_a_later_configuration(research):
    m = manifest()
    m.SEED_SUBJECTS["ENG-US-F-1"] = (*m.SEED_SUBJECTS["ENG-US-F-1"], "CFG-F1-LATER")
    m.CONFIGURATIONS = (*m.CONFIGURATIONS, ("CFG-F1-LATER",) + next(c for c in m.CONFIGURATIONS if c[0] == "CFG-F1")[1:])
    entry(m, "AS-DB05-US-F-1-002")["subject"] = "CFG-F1-LATER"
    refused(research, m, "AS-DB05-US-F-1-002 is authorised by the owner for CFG-F1, but is filed on CFG-F1-LATER")
    m = manifest()
    m.SEED_SUBJECTS["ENG-US-F-1"] = (*m.SEED_SUBJECTS["ENG-US-F-1"], "CFG-F1-LATER")
    m.CONFIGURATIONS = (*m.CONFIGURATIONS, ("CFG-F1-LATER",) + next(c for c in m.CONFIGURATIONS if c[0] == "CFG-F1")[1:])
    entry(m, "AS-DB05-US-F-1-005")["subject"] = "CFG-F1-LATER"
    refused(research, m, "AS-DB05-US-F-1-005 is authorised by the owner for CFG-F1, but is filed on CFG-F1-LATER")


def test_another_engines_owner_decision_cannot_authorise_the_f1(research):
    m = manifest()
    _rating(m)["owner_accepted"] = m.OWNER_DECISIONS["CF-DB05-J2-THRUST"]
    refused(research, m, "CF-DB05-F1-RATING: owner_accepted is not the decision recorded in OWNER_DECISIONS")


def test_a_released_value_keeps_its_own_conflict(research):
    m = manifest()
    m = promote(m, db2a_manifest.P("AS-DB05-US-F-1-007", "CFG-F1", "mechanical.mass", ("number", 18616), "NOMINAL"))
    _rating(m)["owner_released"] += ("AS-DB05-US-F-1-007",)
    refused(research, m, "CF-DB05-F1-MASS: withholds AS-DB05-US-F-1-007, which is promoted")


def test_a_mixture_ratio_direction_is_not_supplied_by_the_reading_alone(research):
    """Confirmed bypass (since DB-2A): a reading saying 'O/F' shipped the F-1 2.27 with a direction
    no record prints."""
    m = manifest()
    m = promote(m, db2a_manifest.P("AS-DB05-US-F-1-006", "CFG-F1", "propellants.mixture_ratio", ("number", 2.27),
                                   "NOMINAL", reading="read as O/F",
                                   cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="ENGINE")))
    _rating(m)["owner_released"] += ("AS-DB05-US-F-1-006",)
    refused(research, m, "AS-DB05-US-F-1-006: mixture ratio form OXIDIZER_TO_FUEL is not printed (O/F) nor in a "
                         "DB-0.5 record the reading cites or quotes")


def test_the_db2a_mixture_ratio_readings_rest_on_records(research):
    """The two DB-2A readings that state a direction are backed by DB-0.5 records: the RL10 one
    cites AS-DB05-US-RL10A-3-3A-006 ('O/F = 5.0'); the SPS one quotes TN D-7375 p.3, transcribed
    as AS-DB05-US-AJ10-137-025."""
    assert "oxidizer-to-fuel weight ratio" in research.assertions["AS-DB05-US-AJ10-137-025"]["value_as_printed"]
    m = manifest()
    entry(m, "AS-DB05-US-AJ10-137-010")["reading"] = "the same paragraph defines it as the 'oxidizer-to-fuel ratio' (O/F)"
    refused(research, m, "AS-DB05-US-AJ10-137-010: mixture ratio form OXIDIZER_TO_FUEL is not printed")
    m = manifest()
    entry(m, "AS-DB05-US-RL10A-3-3A-012")["reading"] = "CR-195478 prints the same point as 'O/F = 5.0'"
    refused(research, m, "AS-DB05-US-RL10A-3-3A-012: mixture ratio form OXIDIZER_TO_FUEL is not printed")


@pytest.mark.parametrize("note", ["Reviewed and approved by the owner.", "Owner-approved 2026-10-09.",
                                  "owner accepted this reading"])
def test_any_owner_review_wording_needs_a_recorded_review(research, note):
    m = manifest()
    m.SOURCES["SRC-NTRS-19860012108"]["review_note"] = note
    m.OWNER_REVIEWS["WAVE1-RIGHTS"] = dict(m.OWNER_REVIEWS["WAVE1-RIGHTS"], sources=tuple(
        s for s in m.OWNER_REVIEWS["WAVE1-RIGHTS"]["sources"] if s != "SRC-NTRS-19860012108"))
    refused(research, m, "SRC-NTRS-19860012108: the rights note says owner-reviewed")


def test_an_owner_review_lists_only_known_shipped_sources(research):
    m = manifest()
    m.OWNER_REVIEWS["WAVE1-RIGHTS"]["sources"] += ("SRC-NTRS-99999999",)
    refused(research, m, "OWNER_REVIEWS WAVE1-RIGHTS: SRC-NTRS-99999999 is not a shipped source")


def test_db2a_rights_review_is_the_five_seed_sources():
    assert set(wave1.OWNER_REVIEWS["DB2A-RIGHTS"]["sources"]) == set(db2a_manifest.SOURCES)
