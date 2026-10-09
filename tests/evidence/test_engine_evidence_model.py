"""Reference-engine evidence (DB-1): the model and its validators.

Every check here is a refusal the schema must make, or a distinction it must
keep. Fixtures are test-only (``engine_fixtures.py``); nothing ships.
"""

from __future__ import annotations

import dataclasses

import pytest

from rocketforge.evidence import EvidenceError, Missing, MissingReason, ShippingPolicy, ValueStatus
from rocketforge.evidence.engines import (
    OPERATING_VALUE_KINDS,
    TIER_FOR_AUTHORITY,
    AbsenceStatement,
    Admissibility,
    Alias,
    AliasKind,
    Assertion,
    Completeness,
    ComponentType,
    Conditions,
    Conflict,
    ConflictCategory,
    ConflictResolution,
    EdgeKind,
    EngineConfiguration,
    EngineVariant,
    EnumValue,
    Environment,
    LineageEdge,
    LineageKind,
    NormalizedQuantity,
    NumberValue,
    OperatingPoint,
    Ownership,
    PressureBasis,
    PressureStation,
    PropulsionUnit,
    PropulsionUnitKind,
    RangeValue,
    RightsNotice,
    RightsRecord,
    RightsReview,
    Schematic,
    SchematicProvenance,
    SourceAccess,
    SourceAuthority,
    SubjectKind,
    SubjectRef,
    TopologyEdge,
    TopologyEvidence,
    TopologyGraph,
    TopologyNode,
    UnitMember,
    ValueKind,
    original_topology_blockers,
    regression_blockers,
)
from engine_fixtures import CFG, OPENED, num, pc, rights, source, stress_corpus

P = SubjectRef


def corpus_with(**changes):
    return stress_corpus(**changes)


def base():
    return stress_corpus()


def replace_assertion(corpus, aid, **changes):
    return tuple(dataclasses.replace(a, **changes) if a.assertion_id == aid else a for a in corpus.assertions)


# ------------------------------------------------------------------ the shared evidence layer


def test_missing_reason_gains_access_blocked_and_keeps_one_rights_meaning():
    assert MissingReason.ACCESS_BLOCKED.value == "ACCESS_BLOCKED"
    assert MissingReason.WITHHELD_RIGHTS.value == "WITHHELD_RIGHTS"
    assert not hasattr(MissingReason, "RIGHTS_RESTRICTED")  # DB-0's spelling of WITHHELD_RIGHTS


def test_authority_maps_onto_the_existing_source_tier():
    assert TIER_FOR_AUTHORITY == {SourceAuthority.A: 1, SourceAuthority.B: 1, SourceAuthority.C: 2,
                                  SourceAuthority.D: 3, SourceAuthority.E: 3}
    good = source("SRC-X", SourceAuthority.C)
    with pytest.raises(EvidenceError, match="tier"):
        dataclasses.replace(good, authority=SourceAuthority.A)


def test_the_source_reference_and_rights_record_carry_one_values_decision():
    good = source("SRC-X")
    with pytest.raises(EvidenceError, match="one decision"):
        dataclasses.replace(good, rights=rights(ShippingPolicy.METADATA_ONLY))


# ------------------------------------------------------------------ identity and scope


def test_the_stress_corpus_validates():
    corpus = base()
    assert len(corpus.assertions) == 40 and len(corpus.topologies) == 5


def test_numeric_values_are_never_inherited_across_identity_levels():
    corpus = base()
    variant = corpus.assertions_about(P(SubjectKind.VARIANT, "VAR-SSME"))
    family = corpus.assertions_about(P(SubjectKind.FAMILY, "FAM-RS25"))
    block_ii = corpus.assertions_about(P(CFG, "CFG-SSME-II"))
    block_iia = corpus.assertions_about(P(CFG, "CFG-SSME-IIA"))
    assert variant == () and family == ()
    assert {a.assertion_id for a in block_ii}.isdisjoint({a.assertion_id for a in block_iia})
    assert "RS25-PC-IIA-104" in {a.assertion_id for a in block_iia}
    assert "RS25-PC-IIA-104" not in {a.assertion_id for a in block_ii}


def test_an_operating_point_must_belong_to_the_subjects_configuration():
    corpus = base()
    bad = replace_assertion(corpus, "RS25-PC-109", operating_point_id="OP-IIA-104.5")
    with pytest.raises(EvidenceError, match="operating point of another configuration"):
        corpus_with(assertions=bad)


def test_a_family_or_variant_cannot_take_an_operating_point():
    corpus = base()
    bad = replace_assertion(corpus, "RS25-PC-109", subject=P(SubjectKind.VARIANT, "VAR-SSME"))
    with pytest.raises(EvidenceError, match="cannot take one"):
        corpus_with(assertions=bad)


@pytest.mark.parametrize("field,target", [
    ("variants", EngineVariant("VAR-ORPHAN", "FAM-NONE", "X")),
    ("configurations", EngineConfiguration("CFG-ORPHAN", "VAR-NONE", "X", Missing(MissingReason.UNKNOWN))),
    ("operating_points", OperatingPoint("OP-ORPHAN", "CFG-NONE", "X")),
])
def test_dangling_identity_references_are_refused(field, target):
    corpus = base()
    with pytest.raises(EvidenceError, match="unknown"):
        corpus_with(**{field: getattr(corpus, field) + (target,)})


def test_duplicate_ids_are_refused():
    corpus = base()
    with pytest.raises(EvidenceError, match="duplicate assertion id"):
        corpus_with(assertions=corpus.assertions + (corpus.assertions[0],))


def test_dangling_subject_and_source_references_are_refused():
    corpus = base()
    with pytest.raises(EvidenceError, match="unknown configuration"):
        corpus_with(assertions=replace_assertion(corpus, "RS25-PC-109", subject=P(CFG, "CFG-NONE")))
    with pytest.raises(EvidenceError, match="unknown source"):
        corpus_with(assertions=replace_assertion(corpus, "RS25-PC-109", source_id="SRC-NONE"))


def test_propulsion_units_are_not_engine_variants_and_cannot_contain_themselves():
    unit = PropulsionUnit("UNIT-A", PropulsionUnitKind.PROPULSION_SYSTEM, "RD-0212",
                          (UnitMember(P(CFG, "CFG-J2-230K"), Missing(MissingReason.NOT_REPORTED)),))
    assert unit.kind is PropulsionUnitKind.PROPULSION_SYSTEM
    with pytest.raises(EvidenceError, match="contain itself"):
        PropulsionUnit("UNIT-A", PropulsionUnitKind.ENGINE_MODULE, "x",
                       (UnitMember(P(SubjectKind.PROPULSION_UNIT, "UNIT-A"), 4),))
    corpus = base()
    loop = (PropulsionUnit("UNIT-B", PropulsionUnitKind.ENGINE_MODULE, "b",
                           (UnitMember(P(SubjectKind.PROPULSION_UNIT, "UNIT-C"), 1),)),
            PropulsionUnit("UNIT-C", PropulsionUnitKind.ENGINE_MODULE, "c",
                           (UnitMember(P(SubjectKind.PROPULSION_UNIT, "UNIT-B"), 1),)))
    with pytest.raises(EvidenceError, match="loop"):
        corpus_with(units=corpus.units + loop)


def test_an_alias_names_an_identity_and_a_shared_name_must_be_marked_ambiguous():
    with pytest.raises(EvidenceError, match="names a family"):
        Alias("AL-1", "x", AliasKind.INFORMAL, P(SubjectKind.COMPONENT, "RS25IIA-MFV"), ("SRC-L3H-RS25",))
    corpus = base()
    clash = Alias("AL-2", "RD-180", AliasKind.INFORMAL, P(SubjectKind.VARIANT, "VAR-RD170"), ("SRC-RKWL-1990",))
    with pytest.raises(EvidenceError, match="ambiguous"):
        corpus_with(aliases=(clash,))
    corpus_with(aliases=(dataclasses.replace(clash, ambiguous=True),))


def test_lineage_cannot_form_a_loop():
    corpus = base()
    back = LineageEdge("LIN-BACK", LineageKind.DERIVED_FROM, P(SubjectKind.VARIANT, "VAR-RD170"),
                       P(SubjectKind.VARIANT, "VAR-RD180"), ("SRC-RKWL-1990",))
    with pytest.raises(EvidenceError, match="loop"):
        corpus_with(lineage=corpus.lineage + (back,))


# ------------------------------------------------------------------ assertion values and kinds


def test_value_types_are_typed_not_float_plus_string():
    corpus = base()
    kinds = {type(a.value).__name__ for a in corpus.assertions}
    assert {"NumberValue", "RangeValue", "EnumValue", "TextValue", "Missing"} <= kinds


def test_a_range_runs_low_to_high_and_tokens_are_upper_snake_case():
    with pytest.raises(EvidenceError):
        RangeValue(109, 67)
    with pytest.raises(EvidenceError):
        EnumValue("fuel-rich")


def test_limit_is_not_an_operating_value():
    assert ValueKind.LIMIT not in OPERATING_VALUE_KINDS
    corpus = base()
    limit = corpus.assertion_map["RS25-HPOT-LIMIT"]
    assert limit.value_kind is ValueKind.LIMIT
    assert any("not an operating value" in b for b in regression_blockers(corpus, ["RS25-HPOT-LIMIT"]))


def test_chamber_pressure_must_state_basis_and_station():
    with pytest.raises(EvidenceError, match="measurement station"):
        num("X", P(CFG, "C"), "performance.chamber_pressure", "717", 717, "psia", "S", "p.1",
            cond=Conditions(pressure_basis=PressureBasis.ABSOLUTE))
    ok = num("X", P(CFG, "C"), "performance.chamber_pressure", "717", 717, "psia", "S", "p.1",
             cond=pc(station=PressureStation.NOZZLE_STAGNATION))
    assert ok.conditions.pressure_station is PressureStation.NOZZLE_STAGNATION


def test_thrust_states_its_environment_unknown_allowed_omission_not():
    with pytest.raises(EvidenceError, match="environment"):
        num("X", P(CFG, "C"), "performance.thrust", "1", 1, "lb", "S", "p.1")
    num("X", P(CFG, "C"), "performance.thrust", "1", 1, "lb", "S", "p.1",
        cond=Conditions(environment=Environment.UNKNOWN))


def test_mixture_ratio_states_form_and_basis():
    with pytest.raises(EvidenceError, match="which way up"):
        num("X", P(CFG, "C"), "propellants.mixture_ratio", "5.5", 5.5, ":1", "S", "p.1")


def test_missing_is_never_a_zero_or_false():
    corpus = base()
    a = corpus.assertion_map["LMDE-PC"]
    assert a.is_missing and not a.is_quantity and a.status is None
    assert a.value == Missing(MissingReason.NOT_REPORTED, "not printed in the pages read")
    assert a.value != NumberValue(0)
    with pytest.raises(EvidenceError, match="nothing printed"):
        dataclasses.replace(a, value_as_printed="0")
    assert any("no value" in b for b in regression_blockers(corpus, ["LMDE-PC"]))


def test_missing_reasons_must_match_the_sources_access():
    corpus = base()
    with pytest.raises(EvidenceError, match="ACCESS_BLOCKED cites a source that was reached"):
        corpus_with(assertions=replace_assertion(
            corpus, "LMDE-PC", value=Missing(MissingReason.ACCESS_BLOCKED)))
    with pytest.raises(EvidenceError, match="was read"):
        corpus_with(assertions=replace_assertion(
            corpus, "RS25-HPOTP-SPEED-WIKI", value=Missing(MissingReason.NOT_REPORTED), value_as_printed="",
            unit_as_printed="", status=None))
    for reason in (MissingReason.NOT_REPORTED, MissingReason.UNKNOWN, MissingReason.WITHHELD_RIGHTS):
        with pytest.raises(EvidenceError, match="could not be opened"):
            corpus_with(assertions=replace_assertion(corpus, "LMDE-A14-PC", value=Missing(reason)))


def test_no_value_can_come_from_a_blocked_source():
    corpus = base()
    bad = replace_assertion(corpus, "LMDE-A14-PC", value=NumberValue(1), value_as_printed="1",
                            unit_as_printed="psia", status=ValueStatus.REPORTED)
    with pytest.raises(EvidenceError, match="could not be opened"):
        corpus_with(assertions=bad)


def test_assertion_access_must_agree_with_its_source():
    corpus = base()
    with pytest.raises(EvidenceError, match="records access"):
        corpus_with(assertions=replace_assertion(corpus, "RS25-PC-109", access=SourceAccess.SEARCH_RESULT_ONLY))


def test_derived_values_carry_their_derivation_and_rejected_ones_a_reason():
    with pytest.raises(EvidenceError, match="DERIVED"):
        num("X", P(CFG, "C"), "nozzle.area_ratio", "1", 1, ":1", "S", "p.1", status=ValueStatus.DERIVED)
    with pytest.raises(EvidenceError, match="says why"):
        num("X", P(CFG, "C"), "nozzle.area_ratio", "1", 1, ":1", "S", "p.1", adm=Admissibility.REJECTED_OTHER)


def test_a_normalised_value_sits_beside_the_printed_one():
    a = num("X", P(CFG, "C"), "performance.thrust", "418,000 lb", 418000, "lb", "S", "p.1",
            cond=Conditions(environment=Environment.SEA_LEVEL),
            normalized=NormalizedQuantity(NumberValue(1859341.6), "N", "lbf x 4.4482216152605"))
    assert a.value == NumberValue(418000) and a.unit_as_printed == "lb"
    with pytest.raises(EvidenceError, match="shape"):
        dataclasses.replace(a, normalized=NormalizedQuantity(RangeValue(1, 2), "N", "x"))


def test_first_stated_by_must_resolve_and_differ_from_the_reader():
    corpus = base()
    a = corpus.assertion_map["RD170-THRUST-SL"]
    assert a.first_stated_by == "SRC-PARIS-PLACARD-1989" and a.source_id == "SRC-RKWL-1990"
    with pytest.raises(EvidenceError, match="unknown source"):
        corpus_with(assertions=replace_assertion(corpus, "RD170-THRUST-SL", first_stated_by="SRC-NOPE"))


# ------------------------------------------------------------------ sources, duplicates, rights


def test_duplicate_documents_are_found_by_hash_and_must_be_linked():
    corpus = base()
    assert corpus.duplicate_document_groups() == (("SRC-TND7143", "SRC-AER-DPS"),)
    unlinked = tuple(dataclasses.replace(s, same_document_as=None) if s.source_id == "SRC-AER-DPS" else s
                     for s in corpus.sources)
    with pytest.raises(EvidenceError, match="same file"):
        corpus_with(sources=unlinked)


def test_a_same_document_claim_needs_equal_hashes():
    corpus = base()
    wrong = tuple(dataclasses.replace(s, content_sha256="f" * 64) if s.source_id == "SRC-AER-DPS" else s
                  for s in corpus.sources)
    with pytest.raises(EvidenceError, match="hashes differ"):
        corpus_with(sources=wrong)


def test_an_opened_document_records_its_hash_and_a_search_result_has_none():
    with pytest.raises(EvidenceError, match="hash of the file"):
        dataclasses.replace(source("SRC-X"), content_sha256=None)
    with pytest.raises(EvidenceError, match="never fetched"):
        dataclasses.replace(source("SRC-X", access=SourceAccess.SEARCH_RESULT_ONLY), content_sha256="a" * 64)


def test_host_metadata_and_printed_notice_may_disagree_and_stay_unresolved():
    corpus = base()
    aiaa = corpus.source_map["SRC-AIAA972687"]
    assert aiaa.rights.notices_disagree and aiaa.rights.review is RightsReview.CONFLICT_UNRESOLVED
    assert aiaa.rights.host_metadata.statement == "GOV_PUBLIC_USE_PERMITTED"
    assert "AIAA" in aiaa.rights.printed_notice.statement
    assert aiaa.authority is SourceAuthority.A  # scientific authority is a separate dimension


def test_a_rights_disagreement_cannot_be_marked_consistent_or_ship_values():
    host = RightsNotice("public use", "NTRS")
    page = RightsNotice("All rights reserved", "p.1")
    with pytest.raises(EvidenceError, match="must be CONFLICT_UNRESOLVED"):
        RightsRecord(host, page, *(ShippingPolicy.RIGHTS_REVIEW_REQUIRED,) * 4, True, RightsReview.CONSISTENT)
    with pytest.raises(EvidenceError, match="stricter reading governs"):
        RightsRecord(host, page, ShippingPolicy.VALUES_WITH_ATTRIBUTION, *(ShippingPolicy.METADATA_ONLY,) * 3,
                     True, RightsReview.CONFLICT_UNRESOLVED)
    with pytest.raises(EvidenceError, match="review_note"):
        RightsRecord(host, page, *(ShippingPolicy.METADATA_ONLY,) * 4, True, RightsReview.CONFLICT_RESOLVED_BY_REVIEW)
    resolved = RightsRecord(host, page, *(ShippingPolicy.VALUES_WITH_ATTRIBUTION,) * 4, True,
                            RightsReview.CONFLICT_RESOLVED_BY_REVIEW, "counsel review 2026-10: page notice governs figures only")
    assert not resolved.unresolved


def test_rights_policies_are_per_content_kind():
    corpus = base()
    coffman = corpus.source_map["SRC-COFFMAN-J2"].rights
    assert coffman.values is ShippingPolicy.VALUES_WITH_ATTRIBUTION
    assert coffman.figures is ShippingPolicy.RIGHTS_REVIEW_REQUIRED


# ------------------------------------------------------------------ conflicts


def test_conflicts_reference_claims_and_never_average_them():
    corpus = base()
    x = next(c for c in corpus.conflicts if c.conflict_id == "CF-RS25-PUMPPOWER")
    values = [corpus.assertion_map[i].value.value for i in x.assertion_ids]
    assert sorted(values) == [69000.0, 71140.0]
    assert not hasattr(x, "value") and x.preferred_assertion_id is None


def test_intra_and_inter_document_conflicts_are_told_apart():
    corpus = base()
    by_id = {c.conflict_id: c for c in corpus.conflicts}
    assert corpus.is_intra_document(by_id["CF-RS25-JSC-INTRA"])
    assert corpus.is_intra_document(by_id["CF-RD170-MR"])
    assert not corpus.is_intra_document(by_id["CF-RS25-PUMPPOWER"])


def test_conflict_rules():
    with pytest.raises(EvidenceError, match="at least two"):
        Conflict("C", "f", ("A",), ConflictResolution.UNRESOLVED, (), "")
    with pytest.raises(EvidenceError, match="says why"):
        Conflict("C", "f", ("A", "B"), ConflictResolution.EXPLAINED, (), "because")
    with pytest.raises(EvidenceError, match="names the claim that stands"):
        Conflict("C", "f", ("A", "B"), ConflictResolution.RESOLVED, (ConflictCategory.PRINTED_TYPO,), "typo")
    with pytest.raises(EvidenceError, match="only a RESOLVED"):
        Conflict("C", "f", ("A", "B"), ConflictResolution.EXPLAINED, (ConflictCategory.ROUNDING,), "r", "A")
    corpus = base()
    with pytest.raises(EvidenceError, match="unknown assertion"):
        corpus_with(conflicts=corpus.conflicts + (
            Conflict("C-X", "f", ("RS25-PC-109", "NOPE"), ConflictResolution.UNRESOLVED, (), ""),))


# ------------------------------------------------------------------ regression capability


def test_search_result_only_evidence_never_qualifies():
    corpus = base()
    blockers = regression_blockers(corpus, ["RS25-HPOTP-SPEED-WIKI"])
    assert any("was not opened (SEARCH_RESULT_ONLY)" in b for b in blockers)
    assert any("authority D" in b for b in blockers)


def test_unresolved_conflicts_block_regression_on_the_fields_involved():
    corpus = base()
    assert any("UNRESOLVED conflict CF-RS25-PUMPPOWER" in b
               for b in regression_blockers(corpus, ["RS25-HPFTP-POWER-L3H"]))
    clean = regression_blockers(corpus, ["RS25-PC-109", "RS25-THRUST-VAC-109", "RS25-ISP-VAC"])
    assert clean == ()


def test_rejected_stale_text_and_restricted_rights_block():
    corpus = base()
    assert any("not admitted" in b for b in regression_blockers(corpus, ["RS25-EPS-STALE"]))
    assert any("may not ship" in b for b in regression_blockers(corpus, ["RS25-PC-IIA-104"]))


def test_regression_needs_a_configuration_scoped_value():
    corpus = base()
    moved = replace_assertion(corpus, "RS25-EPS-L3H", subject=P(SubjectKind.VARIANT, "VAR-SSME"))
    shifted = corpus_with(assertions=moved)
    assert any("not a configuration" in b for b in regression_blockers(shifted, ["RS25-EPS-L3H"]))


def test_there_is_no_overall_quality_score():
    import rocketforge.evidence.engines as engines
    assert not [n for n in engines.__all__ if "score" in n.lower() or "quality" in n.lower()]


# ------------------------------------------------------------------ topology


def _graph(**changes):
    nodes = (TopologyNode("A", ComponentType.PUMP, "pump", Ownership.ENGINE, TopologyEvidence.SHOWN_IN_SCHEMATIC, "fig 1"),
             TopologyNode("B", ComponentType.TURBINE, "turbine", Ownership.ENGINE, TopologyEvidence.SHOWN_IN_SCHEMATIC, "fig 1"))
    edges = (TopologyEdge("e1", "B", "A", EdgeKind.MECHANICAL_SHAFT, None, "shaft",
                          TopologyEvidence.SHOWN_IN_SCHEMATIC, "fig 1"),)
    args = dict(topology_id="TG", scope=SubjectRef(CFG, "CFG-J2-230K"), label="g",
                provenance=SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH, schematic_ids=("SCH-J2-S4",),
                text_source_ids=(), completeness=Completeness(False, ("valves",)), nodes=nodes, edges=edges)
    args.update(changes)
    return TopologyGraph(**args)


def test_a_shaft_carries_no_fluid_and_a_flow_names_its_fluid():
    with pytest.raises(EvidenceError, match="carries no fluid"):
        TopologyEdge("e", "A", "B", EdgeKind.MECHANICAL_SHAFT, "none", "shaft", TopologyEvidence.INFERRED, "x")
    with pytest.raises(EvidenceError, match="fluid a flow edge carries"):
        TopologyEdge("e", "A", "B", EdgeKind.FLUID_FLOW, None, "feed", TopologyEvidence.INFERRED, "x")


def test_topology_nodes_are_unique_and_edges_resolve():
    g = _graph()
    with pytest.raises(EvidenceError, match="used twice"):
        _graph(nodes=g.nodes + (g.nodes[0],))
    with pytest.raises(EvidenceError, match="unknown node"):
        _graph(edges=(TopologyEdge("e9", "A", "Z", EdgeKind.FLUID_FLOW, "LOX", "feed",
                                   TopologyEvidence.INFERRED, "x"),))
    with pytest.raises(EvidenceError, match="two different nodes"):
        TopologyEdge("e", "A", "A", EdgeKind.FLUID_FLOW, "LOX", "loop", TopologyEvidence.INFERRED, "x")


def test_schematic_evidence_needs_a_schematic_and_text_evidence_a_text():
    with pytest.raises(EvidenceError, match="cites no schematic"):
        _graph(schematic_ids=(), text_source_ids=("SRC-COFFMAN-J2",))
    with pytest.raises(EvidenceError, match="cites no text"):
        _graph(nodes=_graph().nodes + (TopologyNode("C", ComponentType.VALVE, "v", Ownership.ENGINE,
                                                     TopologyEvidence.REPORTED_IN_TEXT, "p.2"),))


def test_omission_is_never_absence():
    g = _graph()
    assert ComponentType.GAS_GENERATOR not in {n.component_type for n in g.nodes}
    assert g.stated_absent(ComponentType.GAS_GENERATOR) is False
    stated = _graph(completeness=Completeness(False, ("valves",), (
        AbsenceStatement(ComponentType.GAS_GENERATOR, "The engine cycle was changed to a tap-off cycle to eliminate the gas generator",
                         "SRC-COFFMAN-J2", "p.8"),)))
    assert stated.stated_absent(ComponentType.GAS_GENERATOR) is True
    with pytest.raises(EvidenceError, match="lists no omissions"):
        Completeness(True, ("valves",))


def test_ambient_ownership_is_reserved_for_the_exhaust_sink():
    with pytest.raises(EvidenceError, match="ambient sink"):
        TopologyNode("N", ComponentType.TANK, "tank", Ownership.AMBIENT, TopologyEvidence.INFERRED, "x")


def test_a_node_must_agree_with_the_component_it_names():
    corpus = base()
    graph = corpus.topologies[0]
    bad_node = dataclasses.replace(graph.nodes[0], ownership=Ownership.VEHICLE)
    bad = dataclasses.replace(graph, nodes=(bad_node,) + graph.nodes[1:])
    with pytest.raises(EvidenceError, match="disagree with component"):
        corpus_with(topologies=(bad,) + corpus.topologies[1:])


def test_a_printed_schematic_is_never_a_rocketforge_graph():
    with pytest.raises(EvidenceError, match="describes a graph"):
        Schematic("S", "SRC", "fig 1", "t", SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH, "x", "legible")


def test_a_schematic_must_come_from_an_opened_document():
    corpus = base()
    bad = corpus.schematics + (Schematic("SCH-WIKI", "SRC-WIKI-RS25", "infobox", "t",
                                         SchematicProvenance.UNKNOWN, "unknown", "legible"),)
    with pytest.raises(EvidenceError, match="opened document"):
        corpus_with(schematics=bad)


def test_third_party_reconstruction_never_qualifies_as_original_topology():
    corpus = base()
    blockers = original_topology_blockers(corpus, "TOPO-RD170")
    assert any("THIRD_PARTY_RECONSTRUCTION" in b for b in blockers)
    assert original_topology_blockers(corpus, "TOPO-RL10A33A") == ()


def test_edge_kinds_cover_more_than_plumbing():
    corpus = base()
    kinds = {e.kind for t in corpus.topologies for e in t.edges}
    assert {EdgeKind.FLUID_FLOW, EdgeKind.MECHANICAL_SHAFT, EdgeKind.GEARED_DRIVE,
            EdgeKind.MECHANICAL_LINKAGE} <= kinds


# ------------------------------------------------------------------ review findings (DB-1 independent review)


@pytest.mark.parametrize("field", ["performance.isp", "performance.pc", "performance.isp_vac",
                                   "performance.vacuum_thrust", "chamber.main_chamber_pressure"])
def test_synonyms_cannot_dodge_the_field_obligations(field):
    with pytest.raises(EvidenceError, match="canonical name"):
        num("X", P(CFG, "C"), field, "1", 1, "u", "S", "p.1")


def test_suffixed_canonical_names_keep_their_obligations():
    with pytest.raises(EvidenceError, match="measurement station"):
        num("X", P(CFG, "C"), "performance.chamber_pressure_max", "1", 1, "psia", "S", "p.1")
    with pytest.raises(EvidenceError, match="environment"):
        num("X", P(CFG, "C"), "performance.thrust_vac", "1", 1, "lb", "S", "p.1")


def test_thrust_chamber_fields_are_not_thrust():
    a = num("X", P(CFG, "C"), "architecture.thrust_chamber_count", "4", 4, "chambers", "S", "p.1")
    assert a.conditions == Conditions()


def test_a_missing_value_needs_no_printed_conditions():
    a = Assertion("X", P(CFG, "C"), "performance.chamber_pressure", Missing(MissingReason.NOT_AUDITED), "", "",
                  Conditions(), ValueKind.UNKNOWN, None, Admissibility.ADMITTED, "S", "pp.1-10", OPENED)
    assert a.is_missing


def test_a_mixture_ratio_setting_states_form_and_basis():
    from rocketforge.evidence.engines import MixtureRatioForm, Setting
    with pytest.raises(EvidenceError, match="mixture_ratio_basis"):
        Conditions(mixture_ratio=Setting(5.5, ":1"), mixture_ratio_form=MixtureRatioForm.OXIDIZER_TO_FUEL)


def test_alias_clashes_are_found_across_units_families_and_unicode_dashes():
    corpus = base()
    dash = Alias("AL-3", "RD‑180", AliasKind.INFORMAL, P(SubjectKind.VARIANT, "VAR-RD170"), ("SRC-RKWL-1990",))
    with pytest.raises(EvidenceError, match="ambiguous"):
        corpus_with(aliases=(dash,))
    unit_name = Alias("AL-4", "S-II stage propulsion", AliasKind.INFORMAL, P(SubjectKind.VARIANT, "VAR-J2"),
                      ("SRC-COFFMAN-J2",))
    with pytest.raises(EvidenceError, match="ambiguous"):
        corpus_with(aliases=(unit_name,))


def test_the_source_reference_rights_text_points_at_the_rights_record():
    from rocketforge.evidence.engines import RIGHTS_IN_RECORD
    good = source("SRC-X")
    assert good.reference.rights_statement == RIGHTS_IN_RECORD
    with pytest.raises(EvidenceError, match="rights record"):
        dataclasses.replace(good, reference=dataclasses.replace(good.reference, rights_statement="public domain"))


def test_regression_checks_the_first_stated_source_and_the_schematic_drawer():
    corpus = base()
    wiki_origin = replace_assertion(corpus, "RS25-PC-109", first_stated_by="SRC-WIKI-RS25")
    assert any("first stated by SRC-WIKI-RS25" in b
               for b in regression_blockers(corpus_with(assertions=wiki_origin), ["RS25-PC-109"]))
    sch = tuple(dataclasses.replace(s, provenance=SchematicProvenance.THIRD_PARTY_RECONSTRUCTION)
                if s.schematic_id == "SCH-BC9804-S19" else s for s in corpus.schematics)
    assert any("THIRD_PARTY_RECONSTRUCTION" in b
               for b in regression_blockers(corpus_with(schematics=sch), ["RS25-PC-IIA-104"]))
    assert len(regression_blockers(corpus, ["RS25-EPS-STALE", "RS25-EPS-STALE"])) == len(
        regression_blockers(corpus, ["RS25-EPS-STALE"]))
