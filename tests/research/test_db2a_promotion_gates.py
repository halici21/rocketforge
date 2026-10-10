"""DB-2A promotion: the manifest rebuilds the shipped file exactly, and every gate refuses what it must.

The promotion tool reads DB-0.5 research; these tests run it on the real
records and on copies broken one way at a time. A refused build writes nothing
and names the entry and the rule.
"""

from __future__ import annotations

import copy
import dataclasses
import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "reference_engines"))
import db2a_manifest  # noqa: E402
import promote_db2a  # noqa: E402

from rocketforge.evidence.engines import corpus_to_json  # noqa: E402

J2_PC = "AS-DB05-US-J-2-003"
COFFMAN = "SRC-NTRS-20100027318"
#: SHA-256 of the J-2 graph's free text, reviewed 2026-10-09 for wording only MSFC-MAN-503 supports.
J2_WORDING = "4e9361c55251b53e5834e71876f5a4b4a3f26c1eafce4ced866f9bcd125b6def"


@pytest.fixture(scope="module")
def research():
    return promote_db2a.load_research()


def manifest(**changes):
    """The merged DB-2A + DB-2B Wave 1 manifest the shipped file is built from, deep-copied."""
    m = types.SimpleNamespace(**copy.deepcopy(vars(promote_db2a.load_manifest())))
    for k, v in changes.items():
        setattr(m, k, v)
    return m


def refused(research, m, match):
    with pytest.raises(promote_db2a.PromotionError) as caught:
        promote_db2a.build_corpus(research, m)
    assert any(match in p for p in caught.value.problems), caught.value.problems


def copy_of(research):
    return dataclasses.replace(research, **{f.name: copy.deepcopy(getattr(research, f.name))
                                            for f in dataclasses.fields(research)})


def entry(m, aid):
    return next(e for e in m.ASSERTIONS if e["db05_id"] == aid)


# ------------------------------------------------------------------ the real build


def test_the_manifest_rebuilds_the_shipped_file_byte_for_byte(research):
    text = corpus_to_json(promote_db2a.build_corpus(research, manifest()))
    assert promote_db2a.OUTPUT.read_text(encoding="utf-8") == text
    assert promote_db2a.main(["--check"]) == 0


def test_every_seed_assertion_is_decided_once(research):
    m = manifest()
    seed = {a for a, r in research.assertions.items() if r["engine_id"] in m.SEED_ENGINES}
    promoted = {e["db05_id"] for e in m.ASSERTIONS}
    assert promoted | set(m.NOT_PROMOTED) == seed and not promoted & set(m.NOT_PROMOTED)


def test_nothing_is_promoted_by_rule(research):
    """The source-verified DB-0.5 assertions of the seeds are far more than what ships."""
    m = manifest()
    verified = [a for a, r in research.assertions.items()
                if r["engine_id"] in m.SEED_ENGINES and r["evidence_status"] == "SOURCE_VERIFIED"]
    assert len(m.ASSERTIONS) < len(verified)


def test_a_missing_decision_is_refused(research):
    m = manifest()
    del m.NOT_PROMOTED["AS-DB05-US-J-2-013"]
    refused(research, m, "neither promoted nor listed")


# ------------------------------------------------------------------ source gates


def test_a_search_result_is_never_evidence(research):
    r = copy_of(research)
    r.assertions[J2_PC]["source_id"] = "SRC-WIKI-J2"
    refused(r, manifest(), "never opened")


def test_an_access_blocked_source_is_not_used_as_fetched(research):
    r = copy_of(research)
    r.documents[COFFMAN]["read_level"] = "ACCESS_BLOCKED"
    refused(r, manifest(), "not READ_AND_MINED")


def test_unreviewed_rights_ship_nothing(research):
    m = manifest()
    m.SOURCES[COFFMAN]["review"] = "NOT_REVIEWED"
    refused(research, m, "rights review is NOT_REVIEWED")


def test_a_restrictive_printed_notice_blocks_the_source(research):
    r = copy_of(research)
    r.documents[COFFMAN]["rights_statement_checked"] = "p.ii: Reproduction is not permitted"
    refused(r, manifest(), "restrictive printed notice")


def test_the_withheld_saturn_manual_cannot_be_promoted(research):
    m = manifest()
    m.NOT_PROMOTED.pop("AS-DB05-US-J-2-018")
    m.ASSERTIONS = (*m.ASSERTIONS, db2a_manifest.P("AS-DB05-US-J-2-018", "VAR-J2", "turbines.drive", ("text",), "OTHER"))
    refused(research, m, "withheld")


# ------------------------------------------------------------------ assertion gates


def test_inferred_is_never_promoted_as_reported(research):
    r = copy_of(research)
    r.assertions[J2_PC]["status"] = "INFERRED"
    refused(r, manifest(), "INFERRED")


def test_a_value_must_be_the_printed_value(research):
    m = manifest()
    entry(m, J2_PC)["value"] = ("number", 763)
    refused(research, m, "is not DB-0.5's")


def test_an_unknown_pc_station_is_never_filled_in(research):
    m = manifest()
    entry(m, "AS-DB05-US-RL10A-3-3A-006")["conditions"]["pressure_station"] = "NOZZLE_STAGNATION"
    refused(research, m, "must be UNKNOWN")


def test_an_unstated_environment_is_never_filled_in(research):
    m = manifest()
    entry(m, "AS-DB05-US-RL10A-3-3A-010")["conditions"]["environment"] = "VACUUM"
    refused(research, m, "must be UNKNOWN")


@pytest.mark.parametrize("aid,field,value,match", [
    ("AS-DB05-US-RL10A-3-3A-010", "isp_basis", "ENGINE", "stays UNKNOWN"),
    ("AS-DB05-US-RL10A-3-3A-012", "mixture_ratio_basis", "ENGINE", "stays UNKNOWN"),
    ("AS-DB05-US-AJ10-137-010", "mixture_ratio_basis", "THRUST_CHAMBER", "stays UNKNOWN"),
])
def test_unstated_conditions_are_never_filled_in(research, aid, field, value, match):
    m = manifest()
    entry(m, aid)["conditions"][field] = value
    refused(research, m, match)


def test_a_mixture_ratio_direction_needs_print_or_a_reading(research):
    m = manifest()
    e = entry(m, "AS-DB05-US-RL10A-3-3A-012")
    e["reading"] = "trust me"
    refused(research, m, "is not printed (O/F) nor in a DB-0.5 record the reading cites or quotes")
    m = manifest()
    entry(m, "AS-DB05-US-RL10A-3-3A-012")["conditions"]["mixture_ratio_form"] = "FUEL_TO_OXIDIZER"
    refused(research, m, "is not printed (F/O)")
    m = manifest()
    entry(m, "AS-DB05-US-J-2-004")["conditions"]["mixture_ratio_form"] = "FUEL_TO_OXIDIZER"
    refused(research, m, "is not printed (F/O)")


def test_a_value_kind_must_be_what_is_printed(research):
    m = manifest()
    entry(m, J2_PC)["value_kind"] = "MAXIMUM"
    refused(research, m, "value kind MAXIMUM is not what the source prints")


def test_an_operating_point_the_source_does_not_state_needs_a_basis(research):
    m = manifest()
    entry(m, "AS-DB05-US-RL10A-3-3A-009")["op_basis"] = ""
    refused(research, m, "needs a basis (op_basis)")
    m = manifest()
    entry(m, "AS-DB05-US-RL10A-3-3A-009")["op_basis"] = "x"
    refused(research, m, "needs a basis (op_basis)")
    m = manifest()
    entry(m, "AS-DB05-US-RL10A-3-3A-009")["op_basis"] = "AS-DB05-US-RL10A-3-3A-013 (area ratio)"
    refused(research, m, "op_basis cites no assertion that places it")


def test_a_limit_is_never_promoted_as_an_operating_value(research):
    r = copy_of(research)
    r.assertions["AS-DB05-US-RL10A-3-3A-004"]["value_as_printed"] = "overspeed limit 32000 rpm"
    refused(r, manifest(), "printed as a limit")


def test_a_block_ii_value_never_becomes_block_i(research):
    m = manifest()
    m.NOT_PROMOTED.pop("AS-DB05-US-AJ10-137-009")
    m.ASSERTIONS = (*m.ASSERTIONS, db2a_manifest.P(
        "AS-DB05-US-AJ10-137-009", "CFG-SPS-BLOCK-I", "propellants.mixture_ratio", ("number", 1.6), "NOMINAL",
        op="OP-SPS-BLOCK-I-OF2", cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="UNKNOWN")))
    refused(research, m, "printed for configuration 'Block II'")


def test_a_statement_cannot_move_to_another_engine(research):
    m = manifest()
    entry(m, J2_PC)["subject"] = "CFG-RL10A-3-3A"
    refused(research, m, "is not an identity of ENG-US-J-2")


# ------------------------------------------------------------------ conflict gates


def test_an_unresolved_research_conflict_can_only_withhold(research):
    r = copy_of(research)
    r.conflicts["CF-DB05-J2-MASS"]["resolution"] = "UNRESOLVED"
    refused(r, manifest(), "can only be withheld")


def test_a_partially_resolved_conflict_ships_only_with_the_owners_decision(research):
    corpus = promote_db2a.build_corpus(research, manifest())
    assert "AS-DB05-US-AJ10-137-002" in corpus.assertion_map and "AS-DB05-US-J-2-001" in corpus.assertion_map
    for cid in ("CF-DB05-SPS-THRUST", "CF-DB05-J2-THRUST"):
        m = manifest()
        del m.RESEARCH_CONFLICTS[cid]["owner_accepted"]
        refused(research, m, "needs the owner's recorded decision")
        m = manifest()
        m.RESEARCH_CONFLICTS[cid]["owner_accepted"] = "  "
        refused(research, m, "needs the owner's recorded decision")
    m = manifest()
    del m.RESEARCH_CONFLICTS["CF-DB05-SPS-THRUST"]
    refused(research, m, "has no decision")


def test_owner_acceptance_never_reaches_an_unresolved_conflict(research):
    r = copy_of(research)
    r.conflicts["CF-DB05-SPS-THRUST"]["resolution"] = "UNRESOLVED"
    refused(r, manifest(), "can only be withheld")


def test_a_conflict_decision_must_cover_every_claim_it_matches(research):
    m = manifest()
    m.RESEARCH_CONFLICTS["CF-DB05-SPS-THRUST"]["touches"] = ("AS-DB05-US-AJ10-137-002",)
    refused(research, m, "promoted claim assertion AS-DB05-US-AJ10-137-001 is not listed in touches")
    m = manifest()
    m.RESEARCH_CONFLICTS["CF-DB05-SPS-REG"]["withhold"] = ()
    refused(research, m, "claim assertion AS-DB05-US-AJ10-137-011 is not listed as withheld")


def test_claims_are_matched_to_their_assertions(research):
    claims = promote_db2a.claim_matches(research.conflicts["CF-DB05-SPS-THRUST"], research)
    assert claims[0] == {"AS-DB05-US-AJ10-137-001", "AS-DB05-US-AJ10-137-002", "AS-DB05-US-AJ10-137-003"}
    assert claims[1] == {"AS-DB05-US-AJ10-137-014", "AS-DB05-US-AJ10-137-015", "AS-DB05-US-AJ10-137-016"}


def test_a_withheld_claim_cannot_be_promoted(research):
    m = manifest()
    m.NOT_PROMOTED.pop("AS-DB05-US-AJ10-137-011")
    m.ASSERTIONS = (*m.ASSERTIONS, db2a_manifest.P(
        "AS-DB05-US-AJ10-137-011", "UNIT-SPS-BLOCK-I", "pressurization.helium", ("text",), "OTHER"))
    refused(research, m, "withholds AS-DB05-US-AJ10-137-011")


def test_promoting_a_competing_claim_is_refused(research):
    m = manifest()
    m.NOT_PROMOTED.pop("AS-DB05-US-AJ10-137-015")
    m.ASSERTIONS = (*m.ASSERTIONS, db2a_manifest.P(
        "AS-DB05-US-AJ10-137-015", "VAR-AJ10-137", "performance.chamber_pressure", ("number", 100), "NOMINAL",
        cond=dict(pressure_basis="UNKNOWN", pressure_station="UNKNOWN")))
    refused(research, m, "promoted claim assertion AS-DB05-US-AJ10-137-015 is not listed in touches")


# ------------------------------------------------------------------ topology gates


def _j2(m):
    return next(t for t in m.TOPOLOGIES if t["topology_id"] == "TOPO-J2-230K")


def test_an_edge_without_an_endpoint_is_refused(research):
    r = copy_of(research)
    r.topologies["ENG-US-J-2"]["edges"][0]["to"] = "N-NOPE"
    refused(r, manifest(), "is not a node")


def test_withholding_a_node_withholds_its_edges(research):
    m = manifest()
    _j2(m)["withhold_nodes"]["N-GG"] = "test"
    refused(research, m, "keeps withheld node N-GG")


def test_an_edge_without_provenance_is_refused(research):
    r = copy_of(research)
    r.topologies["ENG-US-AJ10-137"]["edges"][3]["locator"] = ""
    refused(r, manifest(), "no evidence status or locator")


def test_a_rights_withheld_locator_cannot_slip_through(research):
    m = manifest()
    del _j2(m)["restate_nodes"]["N-ASI"]
    refused(research, m, "locator cites a withheld source")


def test_withheld_wording_cannot_slip_through_a_label(research):
    m = manifest()
    del _j2(m)["restate_nodes"]["N-MRCV"]["label"]
    refused(research, m, "carries withheld wording 'pu valve'")


def _sps(m):
    return next(t for t in m.TOPOLOGIES if t["topology_id"] == "TOPO-SPS-BLOCK-I")


def _rl10(m):
    return next(t for t in m.TOPOLOGIES if t["topology_id"] == "TOPO-RL10A-3-3A")


@pytest.mark.parametrize("change,match", [
    (lambda m: _rl10(m)["restate_edges"].update({0: dict(carrier="RP-1", reason="x")}), "not a listed generalisation"),
    (lambda m: _j2(m)["restate_nodes"].update({"N-GG": dict(label="Preburner", reason="x")}), "can only be cut"),
    (lambda m: _j2(m)["restate_nodes"].update({"N-INJ": dict(evidence="REPORTED_IN_TEXT", reason="x")}),
     "can only keep or lower its evidence"),
    (lambda m: _sps(m)["restate_nodes"].update({"N-OX-SUMP": dict(locator="somewhere else", reason="x")}),
     "are neither whole parts"),
    (lambda m: _j2(m)["restate_nodes"].update({"N-GG": dict(locator="NTRS 20100027318 p.999 invented", reason="x")}),
     "are neither whole parts"),
    (lambda m: _j2(m)["restate_nodes"].update({"N-GG": dict(locator="2", reason="x")}), "are neither whole parts"),
    (lambda m: _j2(m)["restate_nodes"].update({"N-GG": dict(locator="Saturn V Flight Manual p.5-5", reason="x")}),
     "are neither whole parts"),
    (lambda m: _j2(m)["restate_edges"].update({0: dict(role="anything", reason="x")}), "deleting the withheld wording"),
    (lambda m: _j2(m)["restate_edges"][15].update(role="preburner bleed to ambient"), "deleting the withheld wording"),
    (lambda m: _j2(m)["restate_edges"].update({14: dict(role="LOX dump", removes=("refill",), reason="x")}),
     "deleting the withheld wording"),
    (lambda m: _j2(m)["restate_nodes"].update({"N-OTP-P": dict(label="L", reason="x")}), "can only be cut"),
    (lambda m: _j2(m)["restate_nodes"].update({"N-INJ": dict(component_type="valve", reason="x")}), "cannot be restated"),
    (lambda m: _j2(m)["restate_nodes"]["N-GG"].update(reason=""), "gives no reason"),
])
def test_a_restatement_can_only_narrow(research, change, match):
    m = manifest()
    change(m)
    refused(research, m, match)


def test_an_inferred_element_cannot_be_restated_as_evidenced(research):
    r = copy_of(research)
    nodes = {n["id"]: n for n in r.topologies["ENG-US-J-2"]["nodes"]}
    nodes["N-MRCV"]["evidence_status"] = "INFERRED"  # the manifest restates it as SHOWN_IN_SCHEMATIC
    refused(r, manifest(), "can only keep or lower its evidence")


def test_an_inferred_element_stays_inferred_and_distinguishable(research):
    from rocketforge.evidence.engines import TopologyEvidence, original_topology_blockers
    r = copy_of(research)
    nodes = {n["id"]: n for n in r.topologies["ENG-US-J-2"]["nodes"]}
    nodes["N-OTP-P"]["evidence_status"] = "INFERRED"  # restated for its locator only
    nodes["N-INJ"]["evidence_status"] = "INFERRED"  # not restated at all
    corpus = promote_db2a.build_corpus(r, manifest())
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-J2-230K")
    assert g.node("N-OTP-P").evidence is TopologyEvidence.INFERRED
    assert g.node("N-INJ").evidence is TopologyEvidence.INFERRED
    assert "2 element(s) are INFERRED" in original_topology_blockers(corpus, "TOPO-J2-230K")


def test_a_third_party_reconstruction_is_never_reclassified_as_original(research):
    r = copy_of(research)
    r.schematics["SCH-DB05-J2-COFFMAN-S4"]["kind"] = "THIRD_PARTY_RECONSTRUCTION line schematic"
    refused(r, manifest(), "third-party reconstruction")


def test_left_out_elements_become_omissions_never_absences(research):
    corpus = promote_db2a.build_corpus(research, manifest())
    for t in corpus.topologies:
        assert t.completeness.absences == () and not t.completeness.declared_complete
    j2 = next(t for t in corpus.topologies if t.topology_id == "TOPO-J2-230K")
    assert "one component known only from a rights-withheld source (not recorded)" in j2.completeness.known_omissions


def test_owner_decisions_are_exactly_the_recorded_ones():
    """``owner_accepted`` unblocks a PARTIALLY_RESOLVED conflict and is the owner's act alone. The two
    entries are the owner's DB-2A decisions of 2026-10-09; any other change must change this test
    in the same commit."""
    recorded = {cid: d["owner_accepted"] for cid, d in db2a_manifest.RESEARCH_CONFLICTS.items()
                if "owner_accepted" in d}
    assert set(recorded) == {"CF-DB05-J2-THRUST", "CF-DB05-SPS-THRUST"}
    assert all(v.startswith("owner (Cemil Eray), 2026-10-09: accept") for v in recorded.values())
    assert db2a_manifest.RESEARCH_CONFLICTS["CF-DB05-J2-THRUST"]["touches"] == ("AS-DB05-US-J-2-001",)
    assert db2a_manifest.RESEARCH_CONFLICTS["CF-DB05-SPS-THRUST"]["touches"] == (
        "AS-DB05-US-AJ10-137-001", "AS-DB05-US-AJ10-137-002", "AS-DB05-US-AJ10-137-003")


def test_owner_decisions_leave_the_research_conflicts_as_recorded(research):
    for cid in ("CF-DB05-J2-THRUST", "CF-DB05-SPS-THRUST"):
        assert research.conflicts[cid]["resolution"] == "PARTIALLY_RESOLVED"


def test_the_j2_graph_wording_is_pinned(research):
    """The withheld-wording check is a word list, so it is best effort. Pin every free-text string of
    the J-2 graph: any change to its labels, roles, omissions or notes must be reviewed here."""
    import hashlib
    corpus = promote_db2a.build_corpus(research, manifest())
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-J2-230K")
    text = "\n".join([g.label, g.notes, *g.completeness.known_omissions, *(f"{n.node_id}={n.label}" for n in g.nodes),
                      *(f"{e.edge_id}={e.role}|{e.carrier}" for e in g.edges)])
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == J2_WORDING
