"""DB-1 schema stress tests: the hard architectures DB-0.5 found, held without flattening.

Two kinds of test:

* the five hand-built cases in ``engine_fixtures.py`` (RS-25, J-2, RL10A-3-3A,
  LMDE, RD-170), checked for the structures that broke simpler schemas;
* every verified DB-0.5 topology graph (``docs/research/engine_database/db05/
  topology``) converted into production graphs and validated -- research
  input used as a stress test, not ingested as data.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from rocketforge.evidence import AccessClass, Missing, MissingReason, ShippingPolicy, SourceReference
from rocketforge.evidence.engines import (
    Completeness,
    ComponentType,
    EdgeKind,
    EngineConfiguration,
    EngineEvidenceCorpus,
    EngineFamily,
    EngineSource,
    EngineVariant,
    EnumValue,
    RIGHTS_IN_RECORD,
    Ownership,
    RightsRecord,
    RightsReview,
    Schematic,
    SchematicProvenance,
    SourceAccess,
    SourceAuthority,
    SourcePrimacy,
    SubjectKind,
    SubjectRef,
    TopologyEdge,
    TopologyEvidence,
    TopologyGraph,
    TopologyNode,
    ValueKind,
    corpus_from_json,
    corpus_to_json,
    original_topology_blockers,
    regression_blockers,
)
from engine_fixtures import stress_corpus

DB05 = pathlib.Path(__file__).resolve().parents[2] / "docs" / "research" / "engine_database" / "db05"


@pytest.fixture(scope="module")
def corpus():
    return stress_corpus()


def graph(corpus, topology_id):
    return next(t for t in corpus.topologies if t.topology_id == topology_id)


def types(g):
    return [n.component_type for n in g.nodes]


# ------------------------------------------------------------------ RS-25


def test_rs25_block_iia_and_block_ii_are_separate_configurations(corpus):
    labels = {c.configuration_id: c.label for c in corpus.configurations if c.variant_id == "VAR-SSME"}
    assert set(labels) == {"CFG-SSME-PRE-LT", "CFG-SSME-IIA", "CFG-SSME-II"}
    pcs = {a.assertion_id: a for a in corpus.assertions if a.field_path == "performance.chamber_pressure"
           and a.subject.id.startswith("CFG-SSME")}
    assert pcs["RS25-PC-IIA-104"].subject.id == "CFG-SSME-IIA"
    assert pcs["RS25-PC-109"].subject.id == "CFG-SSME-II"
    assert pcs["RS25-PC-PRE-109"].subject.id == "CFG-SSME-PRE-LT"  # large-throat vs pre-large-throat


def test_rs25_several_operating_points_on_one_configuration(corpus):
    points = [p.label for p in corpus.operating_points if p.configuration_id == "CFG-SSME-II"]
    assert points == ["100% RPL", "109% RPL"]


def test_rs25_limit_is_kept_apart_from_operating_speed(corpus):
    a = corpus.assertion_map
    assert a["RS25-HPOT-LIMIT"].value_kind is ValueKind.LIMIT
    assert a["RS25-HPOTP-SPEED-IIA"].value_kind is ValueKind.NOMINAL
    assert a["RS25-HPOT-LIMIT"].subject != a["RS25-HPOTP-SPEED-IIA"].subject


def test_rs25_two_preburners_four_turbopumps_and_a_hydraulic_turbine(corpus):
    g = graph(corpus, "TOPO-RS25-IIA")
    assert types(g).count(ComponentType.PREBURNER) == 2
    assert types(g).count(ComponentType.TURBINE) == 3
    assert types(g).count(ComponentType.HYDRAULIC_TURBINE) == 1
    pumps = types(g).count(ComponentType.PUMP) + types(g).count(ComponentType.BOOSTER_PUMP)
    assert pumps == 5  # LPFTP, HPFTP, LPOTP, HPOTP main, HPOTP preburner boost
    rich = {a.subject.id: a.value for a in corpus.assertions if a.field_path == "combustion.rich_side"}
    assert rich == {"RS25IIA-FPB": EnumValue("FUEL_RICH"), "RS25IIA-OPB": EnumValue("FUEL_RICH")}
    shafts = g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT)
    assert ("RS25IIA-HPOT", "RS25IIA-HPOTP-BP") in {(e.source, e.target) for e in shafts}


def test_rs25_rights_disagreement_and_both_conflict_scopes(corpus):
    assert corpus.source_map["SRC-AIAA972687"].rights.review is RightsReview.CONFLICT_UNRESOLVED
    by_id = {x.conflict_id: x for x in corpus.conflicts}
    assert corpus.is_intra_document(by_id["CF-RS25-JSC-INTRA"])
    assert not corpus.is_intra_document(by_id["CF-RS25-EPS"])


def test_rs25_vehicle_owned_ports_stay_out_of_the_engine(corpus):
    g = graph(corpus, "TOPO-RS25-IIA")
    vehicle = {n.label for n in g.nodes if n.ownership is Ownership.VEHICLE}
    assert vehicle == {"ET fuel tank pressurization", "ET oxidizer tank pressurization"}


# ------------------------------------------------------------------ J-2


def test_j2_two_shafts_turbines_in_series_and_bypass(corpus):
    g = graph(corpus, "TOPO-J2")
    shafts = {(e.source, e.target) for e in g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT)}
    assert {("J2-FTP-T", "J2-FTP-P"), ("J2-OTP-T", "J2-OTP-P")} <= shafts
    flow = {(e.source, e.target): e for e in g.edges_of_kind(EdgeKind.FLUID_FLOW)}
    assert ("J2-GG", "J2-FTP-T") in flow and ("J2-FTP-T", "J2-OTP-T") in flow
    split = {e.target for e in g.edges if e.split_group == "H1"}
    assert split == {"J2-OTP-T", "J2-OTBV"}


def test_j2_mixture_ratio_states_start_tank_and_stage_interfaces(corpus):
    points = {p.label for p in corpus.operating_points if p.configuration_id == "CFG-J2-230K"}
    assert points == {"MR 5.5", "MR 4.5"}
    g = graph(corpus, "TOPO-J2")
    assert ComponentType.START_ENERGY_STORE in types(g)
    stage = {n.node_id for n in g.nodes if n.ownership is Ownership.STAGE}
    assert stage == {"J2-LOX-PRESS", "J2-LH2-PRESS"}
    assert {c.label for c in corpus.configurations if c.variant_id == "VAR-J2"} == {
        "225,000 lb version", "230,000 lb version"}


# ------------------------------------------------------------------ RL10A-3-3A


def test_rl10_expander_with_two_stage_fuel_pump_bypass_gear_and_vents(corpus):
    g = graph(corpus, "TOPO-RL10A33A")
    assert ComponentType.GAS_GENERATOR not in types(g) and ComponentType.PREBURNER not in types(g)
    assert not g.stated_absent(ComponentType.GAS_GENERATOR)  # omitted, not asserted absent
    shaft_targets = {e.target for e in g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT)}
    assert {"RL10-FP1", "RL10-FP2", "RL10-GEAR"} <= shaft_targets
    assert [(e.source, e.target) for e in g.edges_of_kind(EdgeKind.GEARED_DRIVE)] == [("RL10-GEAR", "RL10-LOXP")]
    assert {e.target for e in g.edges if e.split_group == "T1"} == {"RL10-TURB", "RL10-TCV"}
    vents = [e for e in g.edges if e.target == "RL10-OVBD"]
    assert len(vents) == 2
    assert original_topology_blockers(corpus, "TOPO-RL10A33A") == ()


# ------------------------------------------------------------------ LMDE


def test_lmde_pressure_fed_stage_and_engine_ownership(corpus):
    g = graph(corpus, "TOPO-LMDE")
    owners = {n.node_id.removeprefix("LMDE-"): n.ownership for n in g.nodes}
    assert {k for k, v in owners.items() if v is Ownership.STAGE} == {
        "SHE", "FHEX", "REG", "SOL", "QCV", "OXT", "FUT", "TRIM"}
    assert {"FCV", "SOV", "INJ", "TC"} <= {k for k, v in owners.items() if v is Ownership.ENGINE}
    assert ComponentType.PUMP not in types(g) and ComponentType.TURBINE not in types(g)
    links = {(e.source, e.target) for e in g.edges_of_kind(EdgeKind.MECHANICAL_LINKAGE)}
    assert links == {("LMDE-TCA", "LMDE-FCV"), ("LMDE-TCA", "LMDE-INJ")}


def test_lmde_throttle_minimum_two_configurations_and_blocked_source(corpus):
    a = corpus.assertion_map
    assert a["LMDE-MIN-THROTTLE"].value_kind is ValueKind.MINIMUM
    assert a["LMDE-ISP"].value_kind is ValueKind.DESIGN_VALUE
    assert a["LMDE-A14-PC"].value == Missing(MissingReason.ACCESS_BLOCKED)
    assert len([c for c in corpus.configurations if c.variant_id == "VAR-LMDE"]) == 2
    assert corpus.duplicate_document_groups() == (("SRC-TND7143", "SRC-AER-DPS"),)


# ------------------------------------------------------------------ RD-170


def test_rd170_multi_chamber_reconstruction_is_not_an_original(corpus):
    g = graph(corpus, "TOPO-RD170")
    assert types(g).count(ComponentType.THRUST_CHAMBER) == 4
    assert types(g).count(ComponentType.PREBURNER) == 2
    assert types(g).count(ComponentType.BOOSTER_PUMP) == 2
    assert types(g).count(ComponentType.TURBINE) == 1
    assert {e.target for e in g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT)} == {"RD170-HPOP", "RD170-HPFP"}
    schematic = next(s for s in corpus.schematics if s.schematic_id == "SCH-RD170-RKWL")
    assert schematic.provenance is SchematicProvenance.THIRD_PARTY_RECONSTRUCTION
    blockers = original_topology_blockers(corpus, "TOPO-RD170")
    assert any("THIRD_PARTY_RECONSTRUCTION" in b for b in blockers)
    assert any("INFERRED" in b for b in blockers)


def test_rd170_second_hand_values_and_intra_document_conflict(corpus):
    thrust = corpus.assertion_map["RD170-THRUST-SL"]
    assert thrust.first_stated_by == "SRC-PARIS-PLACARD-1989"
    assert corpus.source_map["SRC-PARIS-PLACARD-1989"].access is SourceAccess.SEARCH_RESULT_ONLY
    mr = next(x for x in corpus.conflicts if x.conflict_id == "CF-RD170-MR")
    assert corpus.is_intra_document(mr)
    assert any("UNRESOLVED" in b for b in regression_blockers(corpus, ["RD170-MR-258"]))


def test_the_whole_stress_corpus_round_trips(corpus):
    assert corpus_from_json(corpus_to_json(corpus)) == corpus


# ------------------------------------------------------------------ every DB-0.5 topology


_TYPE = {
    "accumulator": ComponentType.ACCUMULATOR, "actuator": ComponentType.ACTUATOR,
    "actuator_supply": ComponentType.ACTUATOR, "ambient": ComponentType.AMBIENT_SINK,
    "booster_pump": ComponentType.BOOSTER_PUMP, "check_valve": ComponentType.CHECK_VALVE,
    "combustion_chamber": ComponentType.COMBUSTION_CHAMBER, "cooling_jacket": ComponentType.COOLING_JACKET,
    "energy_store_start_tank": ComponentType.START_ENERGY_STORE, "engine_inlet": ComponentType.INTERFACE_PORT,
    "gas_generator": ComponentType.GAS_GENERATOR, "gearbox": ComponentType.GEARBOX,
    "heat_exchanger": ComponentType.HEAT_EXCHANGER, "hydraulic_pump": ComponentType.HYDRAULIC_PUMP,
    "igniter": ComponentType.IGNITER, "injector": ComponentType.INJECTOR, "junction": ComponentType.JUNCTION,
    "lubricant_blender": ComponentType.OTHER, "manifold": ComponentType.MANIFOLD, "nozzle": ComponentType.NOZZLE,
    "nozzle_extension": ComponentType.NOZZLE_EXTENSION, "nozzle_injection_port": ComponentType.MANIFOLD,
    "orifice": ComponentType.ORIFICE, "preburner_fuel_rich": ComponentType.PREBURNER,
    "preburner_ox_rich": ComponentType.PREBURNER, "pressurant_tank": ComponentType.PRESSURANT_TANK,
    "pump": ComponentType.PUMP, "regulator": ComponentType.REGULATOR,
    "start_cartridge": ComponentType.START_ENERGY_STORE, "tank": ComponentType.TANK,
    "tank_pressurization_port": ComponentType.INTERFACE_PORT, "thrust_chamber": ComponentType.THRUST_CHAMBER,
    "turbine": ComponentType.TURBINE, "turbine_hydraulic": ComponentType.HYDRAULIC_TURBINE,
    "valve": ComponentType.VALVE, "venturi": ComponentType.VENTURI,
}
_OWNER = {"engine": Ownership.ENGINE, "stage": Ownership.STAGE, "vehicle": Ownership.VEHICLE,
          "ambient": Ownership.AMBIENT}
_SCHEMATIC_PROVENANCE = {
    "SCH-DB05-RD170-RKWL-P19": SchematicProvenance.THIRD_PARTY_RECONSTRUCTION,
    "SCH-DB05-RS25IIA-BC9804-S19": SchematicProvenance.ORIGINAL_MANUFACTURER,
    "SCH-DB05-J2-COFFMAN-S4": SchematicProvenance.ORIGINAL_MANUFACTURER,
    "SCH-DB05-F1-BIGGS-SCHEM": SchematicProvenance.ORIGINAL_MANUFACTURER,
    "SCH-DB05-OMS-WB-F21": SchematicProvenance.ORIGINAL_CONTRACTOR,
    "SCH-DB05-OMS-WB-F210": SchematicProvenance.ORIGINAL_CONTRACTOR,
    "SCH-DB05-H1-SA10-F31": SchematicProvenance.ORIGINAL_CONTRACTOR,
}


def _edge_kind(fluid: str, role: str) -> tuple[EdgeKind, str | None]:
    role = role.lower()
    if "actuation" in role:
        return EdgeKind.CONTROL_ACTUATION, fluid
    if fluid == "none":
        if "gear" in role:
            return EdgeKind.GEARED_DRIVE, None
        if "linkage" in role:
            return EdgeKind.MECHANICAL_LINKAGE, None
        return EdgeKind.MECHANICAL_SHAFT, None
    return EdgeKind.FLUID_FLOW, fluid


def _group(role: str, kind: str) -> str | None:
    m = re.search(rf"{kind}_group (\w+)", role)
    return m.group(1) if m else None


def _rights() -> RightsRecord:
    p = ShippingPolicy.RIGHTS_REVIEW_REQUIRED
    return RightsRecord(Missing(MissingReason.NOT_AUDITED), Missing(MissingReason.NOT_AUDITED), p, p, p, p,
                        False, RightsReview.NOT_REVIEWED)


def _db05_hashes() -> dict[str, str]:
    docs = json.loads((DB05 / "documents_opened.json").read_text(encoding="utf-8"))["documents"]
    return {d["source_id"]: d["sha256"] for d in docs if d.get("sha256")}


def _source(sid: str) -> EngineSource:
    """A source with the SHA-256 DB-0.5 recorded for the file it opened."""
    return EngineSource(
        SourceReference(sid, "DB-0.5 research registry", (), sid, None, {}, "docs/research/engine_database",
                        "research document", AccessClass.PUBLIC_OPEN, RIGHTS_IN_RECORD,
                        ShippingPolicy.RIGHTS_REVIEW_REQUIRED, 1),
        SourceAuthority.A, SourcePrimacy.PRIMARY, SourceAccess.OPENED, _db05_hashes()[sid], None, _rights())


def _convert(path: pathlib.Path) -> EngineEvidenceCorpus:
    raw = json.loads(path.read_text(encoding="utf-8"))
    config = f"CFG-{raw['engine_id']}"
    viewed = {s["schematic_id"]: s for s in json.loads(
        (DB05 / "schematics_viewed.json").read_text(encoding="utf-8"))["schematics"]}
    source_ids = sorted({viewed[s]["source_id"] for s in raw["schematic_ids"]} | set(raw["text_sources"]))
    schematics = tuple(Schematic(sid, viewed[sid]["source_id"], viewed[sid]["locator"], viewed[sid]["title_as_printed"],
                                 _SCHEMATIC_PROVENANCE.get(sid, SchematicProvenance.ORIGINAL_AGENCY),
                                 "as recorded in DB-0.5", viewed[sid]["legibility"]) for sid in raw["schematic_ids"])
    nodes = tuple(TopologyNode(n["id"], _TYPE[n["component_type"]], n["label"], _OWNER[n["subsystem"]],
                               TopologyEvidence(n["evidence_status"]), n["locator"]) for n in raw["nodes"])
    edges = []
    for i, e in enumerate(raw["edges"]):
        kind, carrier = _edge_kind(e["fluid"], e["role"])
        edges.append(TopologyEdge(f"E{i:03d}", e["from"], e["to"], kind, carrier, e["role"],
                                  TopologyEvidence(e["evidence_status"]), e["locator"],
                                  _group(e["role"], "split"), _group(e["role"], "merge")))
    graph_ = TopologyGraph(f"TOPO-{raw['engine_id']}", SubjectRef(SubjectKind.CONFIGURATION, config), raw["configuration"],
                           SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH, tuple(raw["schematic_ids"]),
                           tuple(raw["text_sources"]),
                           Completeness(False, tuple(raw["completeness"]["known_omissions"])), nodes, tuple(edges))
    return EngineEvidenceCorpus(
        sources=tuple(_source(s) for s in source_ids), families=(EngineFamily("FAM-T", "test"),),
        variants=(EngineVariant("VAR-T", "FAM-T", raw["engine_id"]),),
        configurations=(EngineConfiguration(config, "VAR-T", raw["configuration"], Missing(MissingReason.NOT_AUDITED)),),
        operating_points=(), units=(), aliases=(), lineage=(), components=(), schematics=schematics,
        topologies=(graph_,), assertions=(), conflicts=())


DB05_GRAPHS = sorted((DB05 / "topology").glob("*.json"))


def test_all_ten_db05_topologies_are_found():
    assert len(DB05_GRAPHS) == 10  # DB-2B Wave 2 added the LR87AJ-11 graph


@pytest.mark.parametrize("path", DB05_GRAPHS, ids=lambda p: p.stem)
def test_every_db05_topology_fits_the_production_graph(path):
    raw = json.loads(path.read_text(encoding="utf-8"))
    corpus = _convert(path)
    g = corpus.topologies[0]
    assert len(g.nodes) == len(raw["nodes"]) and len(g.edges) == len(raw["edges"])
    assert corpus_from_json(corpus_to_json(corpus)) == corpus
    non_fluid = [e for e in g.edges if e.kind is not EdgeKind.FLUID_FLOW]
    assert all(e.carrier is None for e in non_fluid if e.kind is not EdgeKind.CONTROL_ACTUATION)
    if raw["engine_id"] == "ENG-SU-RD-170":
        assert original_topology_blockers(corpus, g.topology_id)


def test_db05_ownership_beyond_the_engine_survives_conversion():
    owners = {p.stem: {n.ownership for n in _convert(p).topologies[0].nodes} for p in DB05_GRAPHS}
    assert Ownership.VEHICLE in owners["ENG-US-AJ10-137"] and Ownership.VEHICLE in owners["ENG-US-AJ10-190"]
    assert Ownership.STAGE in owners["ENG-US-J-2"]
    pistons = [e for e in _convert(DB05 / "topology" / "ENG-US-AJ10-190.json").topologies[0].edges
               if e.kind is EdgeKind.CONTROL_ACTUATION]
    assert pistons and all(e.carrier == "GN2" for e in pistons)


# ------------------------------------------------------------------ stage / system-level topology


def _quad_corpus(*, foreign_node: bool = False, engine_graph_uses_tank: bool = False):
    """A pressure-fed RCS quad: four thrusters of one configuration on common, stage-owned tanks."""
    from rocketforge.evidence.engines import Component, PropulsionUnit, PropulsionUnitKind, UnitMember
    from engine_fixtures import source
    base = stress_corpus()
    cfg = SubjectRef(SubjectKind.CONFIGURATION, "CFG-R4D")
    unit = SubjectRef(SubjectKind.PROPULSION_UNIT, "UNIT-RCS-QUAD")
    comps = [Component("QUAD-HE", unit, ComponentType.PRESSURANT_TANK, "helium tank", Ownership.STAGE),
             Component("QUAD-OXT", unit, ComponentType.TANK, "oxidizer tank", Ownership.STAGE),
             Component("QUAD-FUT", unit, ComponentType.TANK, "fuel tank", Ownership.STAGE),
             Component("R4D-VALVE", cfg, ComponentType.VALVE, "thruster valve", Ownership.ENGINE),
             Component("R4D-TC", cfg, ComponentType.THRUST_CHAMBER, "thrust chamber", Ownership.ENGINE)]
    ev, loc = TopologyEvidence.REPORTED_IN_TEXT, "test text"
    nodes = [TopologyNode(c.component_id, c.component_type, c.label, c.ownership, ev, loc, c.component_id) for c in comps]
    if foreign_node:  # hardware of an engine that is not in the unit
        nodes.append(TopologyNode("J2-GG", ComponentType.GAS_GENERATOR, "GG", Ownership.ENGINE, ev, loc, "J2-GG"))
    F = EdgeKind.FLUID_FLOW
    edges = [TopologyEdge("q1", "QUAD-HE", "QUAD-OXT", F, "He", "ullage", ev, loc, split_group="P1"),
             TopologyEdge("q2", "QUAD-HE", "QUAD-FUT", F, "He", "ullage", ev, loc, split_group="P1"),
             TopologyEdge("q3", "QUAD-OXT", "R4D-VALVE", F, "N2O4", "common feed", ev, loc),
             TopologyEdge("q4", "QUAD-FUT", "R4D-VALVE", F, "MMH", "common feed", ev, loc),
             TopologyEdge("q5", "R4D-VALVE", "R4D-TC", F, "propellants", "injection", ev, loc)]
    unit_graph = TopologyGraph("TOPO-QUAD", unit, "RCS quad on common tanks", SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH,
                               (), ("SRC-QUAD",), Completeness(False, ("isolation valves",)), tuple(nodes), tuple(edges))
    graphs = [unit_graph]
    if engine_graph_uses_tank:
        graphs.append(TopologyGraph("TOPO-R4D", cfg, "thruster", SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH, (),
                                    ("SRC-QUAD",), Completeness(False, ("all",)),
                                    (nodes[1], nodes[3]), (edges[2],)))
    return stress_corpus(
        sources=base.sources + (source("SRC-QUAD"),),
        families=base.families + (EngineFamily("FAM-R4D", "R-4D"),),
        variants=base.variants + (EngineVariant("VAR-R4D", "FAM-R4D", "R-4D"),),
        configurations=base.configurations + (EngineConfiguration("CFG-R4D", "VAR-R4D", "thruster",
                                                                  Missing(MissingReason.NOT_AUDITED)),),
        units=base.units + (PropulsionUnit("UNIT-RCS-QUAD", PropulsionUnitKind.STAGE_PROPULSION, "RCS quad",
                                           (UnitMember(cfg, 4, "thrusters"),)),),
        components=base.components + tuple(comps),
        topologies=base.topologies + tuple(graphs))


def test_a_stage_level_graph_holds_shared_tanks_and_engine_hardware():
    corpus = _quad_corpus()
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-QUAD")
    assert g.scope.kind is SubjectKind.PROPULSION_UNIT
    scopes = {c.component_id: c.scope.kind for c in corpus.components
              if c.component_id.startswith(("QUAD", "R4D"))}
    assert scopes["QUAD-OXT"] is SubjectKind.PROPULSION_UNIT and scopes["R4D-TC"] is SubjectKind.CONFIGURATION
    assert corpus_from_json(corpus_to_json(corpus)) == corpus


def test_hardware_outside_a_graphs_scope_is_refused():
    from rocketforge.evidence import EvidenceError
    with pytest.raises(EvidenceError, match="outside this graph's scope"):
        _quad_corpus(foreign_node=True)
    with pytest.raises(EvidenceError, match="outside this graph's scope"):
        _quad_corpus(engine_graph_uses_tank=True)
