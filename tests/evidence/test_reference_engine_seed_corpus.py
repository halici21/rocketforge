"""DB-2A: the shipped seed corpus holds exactly three verified configurations, faithfully.

Reads the shipped file the way the application does, and checks it against the
DB-0.5 research records it was promoted from (the research files are read by
this test only; nothing at run time reads them).
"""

from __future__ import annotations

import copy
import json
import pathlib

import pytest

from rocketforge.evidence import EvidenceError, Missing, MissingReason, ShippingPolicy, ValueStatus
from rocketforge.evidence.engines import (
    ComponentType,
    Conflict,
    ConflictCategory,
    ConflictResolution,
    EdgeKind,
    Environment,
    MixtureRatioBasis,
    MixtureRatioForm,
    NumberValue,
    Ownership,
    PressureBasis,
    PressureStation,
    RightsReview,
    SchematicProvenance,
    SourceAccess,
    SubjectKind,
    TopologyEvidence,
    ValueKind,
    corpus_fingerprint,
    corpus_from_dict,
    corpus_from_json,
    corpus_to_dict,
    corpus_to_json,
    original_topology_blockers,
)
from rocketforge.evidence.engines.admission import admission_violations
from rocketforge.evidence.engines.capabilities import (
    Capability,
    CapabilityStatus,
    configuration_assertions,
    context_assertions,
    evaluate_capability,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHIPPED = ROOT / "rocketforge" / "data" / "evidence" / "engines" / "reference_engines.json"
DB05 = ROOT / "docs" / "research" / "engine_database" / "db05"
SEEDS = {"CFG-J2-230K", "CFG-RL10A-3-3A", "CFG-SPS-BLOCK-I"}
DB05_ENGINE = {"TOPO-J2-230K": "ENG-US-J-2", "TOPO-RL10A-3-3A": "ENG-US-RL10A-3-3A",
               "TOPO-SPS-BLOCK-I": "ENG-US-AJ10-137"}


@pytest.fixture(scope="module")
def corpus():
    return corpus_from_json(SHIPPED.read_text(encoding="utf-8"))


@pytest.fixture()
def payload(corpus):
    return copy.deepcopy(corpus_to_dict(corpus))


@pytest.fixture(scope="module")
def db05():
    read = lambda name: json.loads((DB05 / name).read_text(encoding="utf-8"))  # noqa: E731
    return {"assertions": {a["assertion_id"]: a for a in read("assertions.json")["assertions"]},
            "documents": {d["source_id"]: d for d in read("documents_opened.json")["documents"]}}


def a(corpus, aid):
    return corpus.assertion_map[aid]


def status(corpus, cfg, capability):
    return evaluate_capability(corpus, cfg, capability).status


# ------------------------------------------------------------------ the boundary


def test_exactly_the_three_seed_configurations_ship(corpus):
    assert {c.configuration_id for c in corpus.configurations} == SEEDS
    assert {v.designation for v in corpus.variants} == {"J-2", "RL10A-3-3A", "AJ10-137"}
    assert len(corpus.families) == 3 and len(corpus.operating_points) == 3


@pytest.mark.parametrize("name", ["RS-25", "SSME", "F-1", "H-1", "J-2S", "OMS", "AJ10-190", "LMDE", "RD-170",
                                  "RL10A-4-2", "RL10B-2", "Rutherford", "LR87", "RS-68"])
def test_no_other_engine_is_migrated(corpus, name):
    names = [v.designation for v in corpus.variants] + [x.label for x in corpus.configurations]
    names += [x.name for x in corpus.families] + [x.name for x in corpus.aliases]
    assert not any(name.lower() == n.lower() or n.lower().startswith(name.lower() + " ") for n in names)
    assert not any(name.replace("-", "").upper() in aid.replace("-", "") for aid in corpus.assertion_map
                   if not aid.startswith(("AS-DB05-US-J-2-", "AS-DB05-US-RL10A-3-3A-", "AS-DB05-US-AJ10-137-")))


def test_the_shipped_file_is_canonical(corpus):
    text = SHIPPED.read_text(encoding="utf-8")
    assert corpus_to_json(corpus) == text and "\r" not in text


def test_the_fingerprint_is_stable_across_loads(corpus):
    again = corpus_from_json(SHIPPED.read_text(encoding="utf-8"))
    assert again == corpus and corpus_fingerprint(again) == corpus_fingerprint(corpus)


def test_the_shipped_corpus_passes_admission(corpus):
    assert admission_violations(corpus) == ()


# ------------------------------------------------------------------ promotion is faithful


def test_every_assertion_is_its_db05_assertion_verbatim(corpus, db05):
    for x in corpus.assertions:
        r = db05["assertions"][x.assertion_id]
        assert r["disposition"] == "PROMOTED" and r["status"] in ("REPORTED", "DIGITISED"), x.assertion_id
        assert x.status is ValueStatus(r["status"]), x.assertion_id
        assert (x.value_as_printed, x.locator, x.source_id) == (r["value_as_printed"], r["locator"], r["source_id"])
        if x.is_quantity:
            assert x.unit_as_printed == r["unit_as_printed"]


def test_sources_are_opened_rights_settled_and_hash_matched(corpus, db05):
    assert {s.source_id for s in corpus.sources} == {
        "SRC-NTRS-20100027318", "SRC-NTRS-19950022693", "SRC-NTRS-19910018888",
        "SRC-NASA-TND7375", "SRC-NTRS-20100027319"}
    for s in corpus.sources:
        doc = db05["documents"][s.source_id]
        assert s.access is SourceAccess.OPENED and s.content_sha256 == doc["sha256"]
        assert s.rights.values is ShippingPolicy.VALUES_WITH_ATTRIBUTION
        assert s.rights.review is RightsReview.CONSISTENT and not s.rights.notices_disagree
        assert s.rights.host_metadata.statement.endswith(doc["ntrs_copyright_determination"])
        assert s.rights.printed_notice.reason is MissingReason.NOT_REPORTED


def test_the_rights_blocked_saturn_manual_contributes_nothing(corpus):
    text = SHIPPED.read_text(encoding="utf-8")
    assert "19750063889" not in text and "SRC-NTRS-20120016414" not in text
    # it is named only to say what was left out because of it
    cited = [x.locator for x in corpus.assertions] + [s.locator for s in corpus.schematics]
    cited += [x.locator for t in corpus.topologies for x in (*t.nodes, *t.edges)]
    assert not any("MSFC" in c for c in cited)
    assert all(s.source_id != "SRC-DB05-NTRS-19750063889" for s in corpus.sources)


def test_nothing_shipped_is_inferred_and_no_conflict_is_open(corpus):
    assert all(x.status is not ValueStatus.INFERRED for x in corpus.assertions)
    for t in corpus.topologies:
        assert all(e.evidence is not TopologyEvidence.INFERRED for e in (*t.nodes, *t.edges))
    assert corpus.conflicts == ()


# ------------------------------------------------------------------ the three records


def test_j2_230k_mr55_reads_as_the_rocketdyne_viewgraph(corpus):
    op = "OP-J2-230K-MR55"
    thrust, isp, pc, mr = (a(corpus, f"AS-DB05-US-J-2-00{i}") for i in (1, 2, 3, 4))
    assert thrust.value == NumberValue(230000) and thrust.conditions.environment is Environment.VACUUM
    assert "owner decision" in thrust.note
    assert isp.value == NumberValue(425) and isp.conditions.environment is Environment.VACUUM
    assert pc.value == NumberValue(717) and pc.conditions.pressure_station is PressureStation.NOZZLE_STAGNATION
    assert pc.conditions.pressure_basis is PressureBasis.ABSOLUTE
    assert mr.value == NumberValue(5.5) and mr.conditions.mixture_ratio_form is MixtureRatioForm.OXIDIZER_TO_FUEL
    assert mr.conditions.mixture_ratio_basis is MixtureRatioBasis.ENGINE
    assert {x.operating_point_id for x in (thrust, isp, pc, mr)} == {op}
    numbers = {x.value.value for x in corpus.assertions if isinstance(x.value, NumberValue)}
    # the owner accepted the 230,000 lb thrust for this configuration only; the competing claims
    # (225,000 lb rating, J-2X paper, search-result figure) stay out
    assert not {225000, 232250} & numbers
    assert "AS-DB05-US-J-2-014" not in corpus.assertion_map and "AS-DB05-US-J-2-015" not in corpus.assertion_map
    cfg = next(c for c in corpus.configurations if c.configuration_id == "CFG-J2-230K")
    assert cfg.effective.reason is MissingReason.UNKNOWN


def test_rl10a33a_keeps_the_unknown_pc_station_and_isp_environment(corpus):
    for aid in ("AS-DB05-US-RL10A-3-3A-006", "AS-DB05-US-RL10A-3-3A-017"):
        assert a(corpus, aid).value == NumberValue(475)
        assert a(corpus, aid).conditions.pressure_station is PressureStation.UNKNOWN
    isp = a(corpus, "AS-DB05-US-RL10A-3-3A-010")
    assert isp.field_path == "performance.specific_impulse" and isp.conditions.environment is Environment.UNKNOWN
    assert a(corpus, "AS-DB05-US-RL10A-3-3A-012").value == NumberValue(5.0)
    assert "AS-DB05-US-RL10A-3-3A-008" not in corpus.assertion_map  # the rejected model parameter
    assert "AS-DB05-US-RL10A-3-3A-007" not in corpus.assertion_map  # 'all models': family level


def test_sps_is_block_i_only(corpus):
    pc, thrust, isp = (a(corpus, f"AS-DB05-US-AJ10-137-00{i}") for i in (1, 2, 3))
    assert (pc.value, thrust.value, isp.value) == (NumberValue(102), NumberValue(21500), NumberValue(309))
    assert isp.value_kind is ValueKind.AVERAGE and isp.conditions.environment is Environment.UNKNOWN
    for x in (pc, thrust, isp):  # owner-accepted for Block I only
        assert x.subject.id == "CFG-SPS-BLOCK-I" and x.operating_point_id == "OP-SPS-BLOCK-I-OF2"
        assert "Block I only" in x.note
    assert a(corpus, "AS-DB05-US-AJ10-137-010").value == NumberValue(2.0)
    for block_ii in ("AS-DB05-US-AJ10-137-009", "AS-DB05-US-AJ10-137-013"):
        assert block_ii not in corpus.assertion_map
    for aerojet in ("014", "015", "016", "017", "019", "020", "021", "022"):
        assert f"AS-DB05-US-AJ10-137-{aerojet}" not in corpus.assertion_map
    assert "AS-DB05-US-AJ10-137-011" not in corpus.assertion_map  # in an UNRESOLVED conflict


def test_variant_statements_stay_with_the_variant(corpus):
    sps = configuration_assertions(corpus, "CFG-SPS-BLOCK-I")
    assert "AS-DB05-US-AJ10-137-018" not in {x.assertion_id for x in sps}
    assert [x.assertion_id for x in context_assertions(corpus, "CFG-SPS-BLOCK-I")] == ["AS-DB05-US-AJ10-137-018"]
    j2_context = {x.assertion_id for x in context_assertions(corpus, "CFG-J2-230K")}
    assert j2_context == {"AS-DB05-US-J-2-009", "AS-DB05-US-J-2-010", "AS-DB05-US-J-2-011", "AS-DB05-US-J-2-012"}
    assert all(x.subject.kind is SubjectKind.VARIANT for x in context_assertions(corpus, "CFG-J2-230K"))


# ------------------------------------------------------------------ topology


def _db05_graph(topology_id):
    return json.loads((DB05 / "topology" / f"{DB05_ENGINE[topology_id]}.json").read_text(encoding="utf-8"))


#: What each seed graph leaves out of its DB-0.5 graph (nodes; edge indices), each one a listed omission.
LEFT_OUT = {"TOPO-J2-230K": ({"N-HYD-PUMP"}, {5, 6, 25, 26, 27}),
            "TOPO-RL10A-3-3A": (set(), {18}),
            "TOPO-SPS-BLOCK-I": (set(), set())}
_TYPES = {"pump": ComponentType.PUMP, "turbine": ComponentType.TURBINE, "valve": ComponentType.VALVE,
          "gearbox": ComponentType.GEARBOX, "tank": ComponentType.TANK, "injector": ComponentType.INJECTOR,
          "ambient": ComponentType.AMBIENT_SINK, "gas_generator": ComponentType.GAS_GENERATOR,
          "energy_store_start_tank": ComponentType.START_ENERGY_STORE}


@pytest.mark.parametrize("topology_id", sorted(DB05_ENGINE))
def test_graphs_keep_db05_ids_types_ownership_and_edges(corpus, topology_id):
    g = next(t for t in corpus.topologies if t.topology_id == topology_id)
    raw = _db05_graph(topology_id)
    owners = {"engine": Ownership.ENGINE, "stage": Ownership.STAGE, "vehicle": Ownership.VEHICLE,
              "ambient": Ownership.AMBIENT}
    raw_nodes = {n["id"]: n for n in raw["nodes"]}
    for n in g.nodes:
        assert n.ownership is owners[raw_nodes[n.node_id]["subsystem"]], n.node_id
        if raw_nodes[n.node_id]["component_type"] in _TYPES:
            assert n.component_type is _TYPES[raw_nodes[n.node_id]["component_type"]], n.node_id
    for e in g.edges:
        r = raw["edges"][int(e.edge_id[1:])]
        assert (e.source, e.target) == (r["from"], r["to"]), e.edge_id
        if e.kind is EdgeKind.FLUID_FLOW and e.carrier != r["fluid"]:
            assert topology_id == "TOPO-SPS-BLOCK-I" and "A-50" in r["fluid"], e.edge_id
    nodes_out, edges_out = LEFT_OUT[topology_id]
    assert set(raw_nodes) - {n.node_id for n in g.nodes} == nodes_out
    assert set(range(len(raw["edges"]))) - {int(e.edge_id[1:]) for e in g.edges} == edges_out
    assert set(raw["completeness"]["known_omissions"]) <= set(g.completeness.known_omissions)
    assert len(g.completeness.known_omissions) > len(raw["completeness"]["known_omissions"]) or not edges_out
    assert not g.completeness.declared_complete and g.completeness.absences == ()
    assert original_topology_blockers(corpus, topology_id) == ()


def test_j2_drives_withheld_with_the_saturn_manual_are_omissions_not_absences(corpus):
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-J2-230K")
    assert g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT) == () and g.edges_of_kind(EdgeKind.GEARED_DRIVE) == ()
    omissions = " ".join(g.completeness.known_omissions)
    assert "turbine-to-pump drive of each turbopump" in omissions and "rights-withheld source" in omissions
    text = " ".join([omissions, g.notes, *(n.label for n in g.nodes), *(e.role for e in g.edges)]).lower()
    for withheld_wording in ("hydraulic", "direct drive", "pu valve", "stdv", "fuel manifold", "exhaust duct"):
        assert withheld_wording not in text, withheld_wording
    assert not g.stated_absent(ComponentType.HYDRAULIC_PUMP) and not g.stated_absent(ComponentType.SHAFT)
    assert all("MSFC" not in x.locator for x in (*g.nodes, *g.edges))
    assert {n.node_id for n in g.nodes if n.ownership is Ownership.STAGE} == {"N-LOX-TANK-PRESS", "N-LH2-TANK-PRESS"}


def test_rl10_keeps_its_shaft_and_gear_relations(corpus):
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-RL10A-3-3A")
    assert ("N-GEAR", "N-LOXP") in {(e.source, e.target) for e in g.edges_of_kind(EdgeKind.GEARED_DRIVE)}
    shafts = {(e.source, e.target) for e in g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT)}
    assert {("N-TURB", "N-FP1"), ("N-TURB", "N-FP2"), ("N-TURB", "N-GEAR")} <= shafts
    assert all(e.carrier is None for e in (*g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT),
                                           *g.edges_of_kind(EdgeKind.GEARED_DRIVE)))


def test_sps_graph_is_the_service_module_unit_with_engine_and_vehicle_owners(corpus):
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-SPS-BLOCK-I")
    assert g.scope.kind is SubjectKind.PROPULSION_UNIT
    engine = {n.node_id for n in g.nodes if n.ownership is Ownership.ENGINE}
    assert engine == {"N-BIPROP", "N-INJ", "N-TC", "N-NOZ"}
    assert len([n for n in g.nodes if n.ownership is Ownership.VEHICLE]) == 11
    assert not any("A-50" in (e.carrier or "") for e in g.edges)
    assert "4400" not in g.node("N-HE-TANK").label  # the withheld regulator-conflict value


def test_the_rl10_drawing_is_a_contractors_not_the_manufacturers(corpus):
    sch = next(s for s in corpus.schematics if s.schematic_id == "SCH-DB05-RL10A33A-CR195478-F1")
    assert sch.provenance is SchematicProvenance.ORIGINAL_CONTRACTOR
    assert "not ORIGINAL_MANUFACTURER" in sch.notes


def test_owner_rights_acceptance_upgrades_no_policy(corpus):
    for s in corpus.sources:
        assert "Owner-reviewed 2026-10-09" in s.rights.review_note
        assert s.rights.values is ShippingPolicy.VALUES_WITH_ATTRIBUTION
        assert s.rights.tables is ShippingPolicy.RIGHTS_REVIEW_REQUIRED
        assert s.rights.text is ShippingPolicy.RIGHTS_REVIEW_REQUIRED
    coffman = next(s for s in corpus.sources if s.source_id == "SRC-NTRS-20100027318")
    assert coffman.rights.figures is ShippingPolicy.RIGHTS_REVIEW_REQUIRED


def test_schematics_are_original_drawings_of_named_provenance(corpus):
    assert {s.schematic_id: s.provenance for s in corpus.schematics} == {
        "SCH-DB05-J2-COFFMAN-S4": SchematicProvenance.ORIGINAL_MANUFACTURER,
        "SCH-DB05-RL10A33A-CR195478-F1": SchematicProvenance.ORIGINAL_CONTRACTOR,
        "SCH-DB05-SPS-TND7375-F2": SchematicProvenance.ORIGINAL_AGENCY}


# ------------------------------------------------------------------ capabilities

EXPECTED = {
    "CFG-J2-230K": dict(IDENTITY="SUPPORTED", ARCHITECTURE="SUPPORTED", PERFORMANCE_REFERENCE="SUPPORTED",
                        TOPOLOGY="SUPPORTED", REGRESSION_CANDIDATE="SUPPORTED"),
    "CFG-RL10A-3-3A": dict(IDENTITY="SUPPORTED", ARCHITECTURE="SUPPORTED", PERFORMANCE_REFERENCE="SUPPORTED",
                           TOPOLOGY="SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-SPS-BLOCK-I": dict(IDENTITY="SUPPORTED", ARCHITECTURE="PARTIAL", PERFORMANCE_REFERENCE="SUPPORTED",
                            TOPOLOGY="SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
}


@pytest.mark.parametrize("cfg", sorted(SEEDS))
@pytest.mark.parametrize("capability", list(Capability))
def test_capabilities_are_what_the_evidence_supports(corpus, cfg, capability):
    assert status(corpus, cfg, capability).value == EXPECTED[cfg][capability.value]


def test_a_regression_candidate_is_eligibility_only(corpus):
    r = evaluate_capability(corpus, "CFG-J2-230K", Capability.REGRESSION_CANDIDATE)
    assert any("no regression is accepted" in c for c in r.caveats)
    assert r.status is CapabilityStatus.SUPPORTED and r.gaps == ()
    assert set(r.assertion_ids) == {f"AS-DB05-US-J-2-00{i}" for i in (1, 2, 3, 4, 7)}


def test_an_average_isp_is_no_regression_reference(corpus):
    r = evaluate_capability(corpus, "CFG-SPS-BLOCK-I", Capability.REGRESSION_CANDIDATE)
    assert r.status is CapabilityStatus.NOT_SUPPORTED
    assert any("printed as average" in g for g in r.gaps) and any("no stated environment" in g for g in r.gaps)


def test_an_isp_with_no_stated_environment_is_no_regression_reference(corpus):
    r = evaluate_capability(corpus, "CFG-RL10A-3-3A", Capability.REGRESSION_CANDIDATE)
    assert r.gaps == ("AS-DB05-US-RL10A-3-3A-010: specific_impulse with no stated environment cannot be "
                      "compared with an ideal-performance case",)
    performance = evaluate_capability(corpus, "CFG-RL10A-3-3A", Capability.PERFORMANCE_REFERENCE)
    assert performance.status is CapabilityStatus.SUPPORTED


def test_sps_propellants_are_not_inherited_from_the_variant(corpus):
    r = evaluate_capability(corpus, "CFG-SPS-BLOCK-I", Capability.ARCHITECTURE)
    assert r.assertion_ids == ("AS-DB05-US-AJ10-137-023",)
    assert any("AS-DB05-US-AJ10-137-018" in c and "not applied" in c for c in r.caveats)


# ------------------------------------------------------------------ negatives on the shipped record


def _with(payload, aid, **fields):
    x = next(i for i in payload["assertions"] if i["assertion_id"] == aid)
    x.update(fields)
    return corpus_from_dict(payload)


def test_a_limit_is_never_an_operating_value(payload):
    corpus = _with(payload, "AS-DB05-US-RL10A-3-3A-009", value_kind="LIMIT")
    r = evaluate_capability(corpus, "CFG-RL10A-3-3A", Capability.PERFORMANCE_REFERENCE)
    assert r.status is CapabilityStatus.PARTIAL
    assert any(g.startswith("thrust:") for g in r.gaps) and any("LIMIT" in c for c in r.caveats)


def test_inferred_relabelled_or_kept_is_refused_and_supports_nothing(payload):
    corpus = _with(payload, "AS-DB05-US-RL10A-3-3A-009", status="INFERRED")
    assert any("INFERRED" in v for v in admission_violations(corpus))
    assert status(corpus, "CFG-RL10A-3-3A", Capability.PERFORMANCE_REFERENCE) is CapabilityStatus.PARTIAL


@pytest.mark.parametrize("resolution", ["UNRESOLVED", "PARTIALLY_RESOLVED"])
def test_an_open_conflict_on_a_shipped_value_is_refused(corpus, resolution):
    open_ = Conflict("CF-TEST", "performance.chamber_pressure",
                     ("AS-DB05-US-RL10A-3-3A-006", "AS-DB05-US-RL10A-3-3A-017"), ConflictResolution(resolution),
                     () if resolution == "UNRESOLVED" else (ConflictCategory.OTHER,), "test")
    payload = corpus_to_dict(corpus)
    payload["conflicts"] = [{"conflict_id": open_.conflict_id, "field_path": open_.field_path,
                             "assertion_ids": list(open_.assertion_ids), "resolution": resolution,
                             "categories": [c.value for c in open_.categories], "explanation": "test",
                             "preferred_assertion_id": None}]
    broken = corpus_from_dict(payload)
    assert any(resolution in v for v in admission_violations(broken))
    r = evaluate_capability(broken, "CFG-RL10A-3-3A", Capability.REGRESSION_CANDIDATE)
    assert r.status is CapabilityStatus.NOT_SUPPORTED and any(resolution in g for g in r.gaps)


def test_unreviewed_rights_are_refused(payload):
    src = next(s for s in payload["sources"] if s["reference"]["source_id"] == "SRC-NASA-TND7375")
    src["rights"]["review"] = "NOT_REVIEWED"
    assert any("NOT_REVIEWED" in v for v in admission_violations(corpus_from_dict(payload)))


def test_a_family_statement_supports_no_configuration(payload):
    fam = copy.deepcopy(next(i for i in payload["assertions"] if i["assertion_id"] == "AS-DB05-US-AJ10-137-023"))
    fam.update(assertion_id="TEST-FAMILY-FUEL", subject={"kind": "FAMILY", "id": "FAM-AJ10"},
               field_path="propellants.fuel", value={"type": "enum", "token": "AEROZINE_50"})
    payload["assertions"].append(fam)
    corpus = corpus_from_dict(payload)
    r = evaluate_capability(corpus, "CFG-SPS-BLOCK-I", Capability.ARCHITECTURE)
    assert r.status is CapabilityStatus.PARTIAL and "TEST-FAMILY-FUEL" not in r.assertion_ids


def test_block_i_values_never_reach_another_sps_configuration(payload):
    payload["configurations"].append({"configuration_id": "CFG-SPS-BLOCK-II", "variant_id": "VAR-AJ10-137",
                                      "label": "Block II", "effective": {"missing": "NOT_AUDITED", "note": ""},
                                      "notes": ""})
    corpus = corpus_from_dict(payload)
    assert configuration_assertions(corpus, "CFG-SPS-BLOCK-II") == ()
    for capability in (Capability.PERFORMANCE_REFERENCE, Capability.ARCHITECTURE, Capability.IDENTITY):
        assert status(corpus, "CFG-SPS-BLOCK-II", capability) is CapabilityStatus.NOT_SUPPORTED
    moved = next(i for i in payload["assertions"] if i["assertion_id"] == "AS-DB05-US-AJ10-137-010")
    moved["subject"] = {"kind": "CONFIGURATION", "id": "CFG-SPS-BLOCK-II"}
    with pytest.raises(EvidenceError, match="operating point of another configuration"):
        corpus_from_dict(payload)


def test_an_edge_needs_both_endpoints_and_a_locator(payload):
    graph = next(t for t in payload["topologies"] if t["topology_id"] == "TOPO-RL10A-3-3A")
    broken = copy.deepcopy(payload)
    next(t for t in broken["topologies"] if t["topology_id"] == "TOPO-RL10A-3-3A")["edges"][0]["target"] = "N-NOPE"
    with pytest.raises(EvidenceError, match="unknown node"):
        corpus_from_dict(broken)
    graph["edges"][0]["locator"] = " "
    with pytest.raises(EvidenceError, match="locator"):
        corpus_from_dict(payload)


def test_a_third_party_drawing_cannot_pass_as_original(payload):
    sch = next(s for s in payload["schematics"] if s["schematic_id"] == "SCH-DB05-J2-COFFMAN-S4")
    sch["provenance"] = "THIRD_PARTY_RECONSTRUCTION"
    corpus = corpus_from_dict(payload)
    assert original_topology_blockers(corpus, "TOPO-J2-230K")
    assert status(corpus, "CFG-J2-230K", Capability.TOPOLOGY) is CapabilityStatus.PARTIAL


def test_an_unknown_configuration_is_an_error_not_an_empty_answer(corpus):
    with pytest.raises(EvidenceError, match="unknown configuration"):
        evaluate_capability(corpus, "CFG-RS25", Capability.IDENTITY)
    assert isinstance(next(c for c in corpus.configurations if c.configuration_id == "CFG-RL10A-3-3A").effective,
                      Missing)
