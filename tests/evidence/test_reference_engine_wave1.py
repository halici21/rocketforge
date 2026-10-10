"""DB-2B Wave 1: six historical targets in the shipped corpus, each exactly as far as its evidence goes.

Checks the shipped file against the boundary (only the planned engines), and
per target the things that would go wrong first: a J-2 graph under the J-2S, a
canonical F-1 thrust, H-1 family values on the SA-10 engine, the development
LMDE in the final design, a guessed OMS mixture ratio, and RS-25 Block IIA
values (rights-withheld) under Block II.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from rocketforge.evidence import MissingReason, ShippingPolicy
from rocketforge.evidence.engines import (
    ComponentType,
    EdgeKind,
    Environment,
    NumberValue,
    Ownership,
    PressureStation,
    SchematicProvenance,
    SubjectKind,
    ValueKind,
    corpus_from_json,
    corpus_to_dict,
    corpus_to_json,
)
from rocketforge.evidence.engines.admission import admission_violations
from rocketforge.evidence.engines.capabilities import (
    Capability,
    CapabilityStatus,
    configuration_assertions,
    configuration_topologies,
    context_assertions,
    evaluate_capability,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHIPPED = ROOT / "rocketforge" / "data" / "evidence" / "engines" / "reference_engines.json"

SEEDS = {"CFG-J2-230K", "CFG-RL10A-3-3A", "CFG-SPS-BLOCK-I"}
WAVE1 = {"CFG-J2S", "CFG-F1", "CFG-H1-188K-SA10", "CFG-LMDE-FINAL", "CFG-OMS",
         "CFG-RS25-SMALL-THROAT", "CFG-RS25-BLOCK-II", "CFG-RS25-SLS"}
#: The DB-0.5 engines whose assertions may appear in production.
ALLOWED_ENGINES = ("J-2-", "RL10A-3-3A-", "AJ10-137-", "J-2S-", "F-1-", "H-1-188K-", "LMDE-", "AJ10-190-",
                   "SSME-BLOCK-I-", "SSME-BLOCK-IIA-", "SSME-BLOCK-II-")


@pytest.fixture(scope="module")
def corpus():
    return corpus_from_json(SHIPPED.read_text(encoding="utf-8"))


def own(corpus, cfg):
    return {a.assertion_id: a for a in configuration_assertions(corpus, cfg)}


def status(corpus, cfg, capability):
    return evaluate_capability(corpus, cfg, capability).status.value


def numbers(assertions):
    return {a.value.value for a in assertions if isinstance(a.value, NumberValue)}


# ------------------------------------------------------------------ boundary


def test_only_the_seeds_and_the_wave1_configurations_ship(corpus):
    assert {c.configuration_id for c in corpus.configurations} == SEEDS | WAVE1
    assert {v.designation for v in corpus.variants} == {
        "J-2", "RL10A-3-3A", "AJ10-137", "J-2S", "F-1", "H-1", "LM descent engine", "OMS engine", "RS-25"}


@pytest.mark.parametrize("name", ["RD-170", "RL10A-4-2", "RL10B-2", "IPD", "Rutherford", "LR87", "RS-68",
                                  "LE-7", "LE-9", "Vulcain", "Vinci", "YF-"])
def test_no_later_target_is_migrated(corpus, name):
    text = json.dumps([[v.designation, v.notes] for v in corpus.variants]
                      + [[c.label, c.notes] for c in corpus.configurations]
                      + [[f.name] for f in corpus.families] + [[a.name] for a in corpus.aliases])
    assert name.lower() not in text.lower()


def test_every_assertion_comes_from_an_allowed_engine(corpus):
    for aid in corpus.assertion_map:
        assert aid.removeprefix("AS-DB05-US-").startswith(ALLOWED_ENGINES), aid
    assert not any(aid.startswith("AS-DB05-US-SSME-BLOCK-IIA-") for aid in corpus.assertion_map)


def test_the_corpus_is_admitted_canonical_and_conflict_free(corpus):
    assert admission_violations(corpus) == ()
    assert corpus_to_json(corpus) == SHIPPED.read_text(encoding="utf-8")
    assert corpus.conflicts == ()


#: What each Wave-1 configuration's evidence supports, as evaluated (not set here).
EXPECTED = {
    "CFG-J2S": dict(IDENTITY="SUPPORTED", ARCHITECTURE="SUPPORTED", PERFORMANCE_REFERENCE="SUPPORTED",
                    TOPOLOGY="NOT_SUPPORTED", REGRESSION_CANDIDATE="SUPPORTED"),
    "CFG-F1": dict(IDENTITY="SUPPORTED", ARCHITECTURE="SUPPORTED", PERFORMANCE_REFERENCE="PARTIAL",
                   TOPOLOGY="SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-H1-188K-SA10": dict(IDENTITY="SUPPORTED", ARCHITECTURE="SUPPORTED", PERFORMANCE_REFERENCE="PARTIAL",
                             TOPOLOGY="SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-LMDE-FINAL": dict(IDENTITY="SUPPORTED", ARCHITECTURE="NOT_SUPPORTED", PERFORMANCE_REFERENCE="NOT_SUPPORTED",
                           TOPOLOGY="SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-OMS": dict(IDENTITY="SUPPORTED", ARCHITECTURE="PARTIAL", PERFORMANCE_REFERENCE="PARTIAL",
                    TOPOLOGY="NOT_SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-RS25-SMALL-THROAT": dict(IDENTITY="SUPPORTED", ARCHITECTURE="NOT_SUPPORTED",
                                  PERFORMANCE_REFERENCE="PARTIAL", TOPOLOGY="NOT_SUPPORTED",
                                  REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-RS25-BLOCK-II": dict(IDENTITY="SUPPORTED", ARCHITECTURE="NOT_SUPPORTED", PERFORMANCE_REFERENCE="PARTIAL",
                              TOPOLOGY="NOT_SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-RS25-SLS": dict(IDENTITY="SUPPORTED", ARCHITECTURE="NOT_SUPPORTED", PERFORMANCE_REFERENCE="PARTIAL",
                         TOPOLOGY="NOT_SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
}


@pytest.mark.parametrize("cfg", sorted(WAVE1))
@pytest.mark.parametrize("capability", list(Capability))
def test_capabilities_follow_the_admitted_evidence(corpus, cfg, capability):
    assert status(corpus, cfg, capability) == EXPECTED[cfg][capability.value]


# ------------------------------------------------------------------ J-2S


def test_j2s_architecture_ships_without_a_graph(corpus):
    a = own(corpus, "CFG-J2S")
    assert a["AS-DB05-US-J-2S-007"].value.token == "TAP_OFF"
    assert a["AS-DB05-US-J-2S-003"].conditions.pressure_station is PressureStation.NOZZLE_STAGNATION
    assert configuration_topologies(corpus, "CFG-J2S") == ()
    r = evaluate_capability(corpus, "CFG-J2S", Capability.TOPOLOGY)
    assert r.gaps == ("no topology graph of this configuration",)


def test_no_j2_graph_or_value_leaks_into_the_j2s(corpus):
    assert all(t.scope.id != "CFG-J2S" for t in corpus.topologies)
    assert not any(aid.startswith("AS-DB05-US-J-2-") for aid in own(corpus, "CFG-J2S"))
    j2 = next(t for t in corpus.topologies if t.topology_id == "TOPO-J2-230K")
    assert j2.scope.id == "CFG-J2-230K"
    assert numbers(own(corpus, "CFG-J2S").values()).isdisjoint({230000, 425, 717, 27.5})


def test_j2s_is_a_candidate_only(corpus):
    r = evaluate_capability(corpus, "CFG-J2S", Capability.REGRESSION_CANDIDATE)
    assert any("no regression is accepted" in c for c in r.caveats)


# ------------------------------------------------------------------ F-1


#: The five DB-2A seed sources (their rights notes are DB-2A's own).
SEED_SOURCES = {"SRC-NTRS-20100027318", "SRC-NTRS-19950022693", "SRC-NTRS-19910018888", "SRC-NASA-TND7375",
                "SRC-NTRS-20100027319"}


def test_f1_ships_the_owner_admitted_table_values_and_no_rating(corpus):
    a = own(corpus, "CFG-F1")
    shipped = {x.field_path: x.value.value for x in a.values() if x.field_path.startswith("performance.")}
    assert shipped == {"performance.thrust_vac": 1748200, "performance.specific_impulse_sl": 265.4,
                       "performance.specific_impulse_vac": 304.1, "performance.chamber_pressure": 1125}
    assert all("owner decision (2026-10-09)" in x.note or "by owner decision" in x.note
               for x in a.values() if x.field_path.startswith("performance."))
    pc = next(x for x in a.values() if x.field_path == "performance.chamber_pressure")
    assert pc.conditions.pressure_station.value == "UNKNOWN"
    # no sea-level thrust, no canonical rating, no F-1A, no mass
    assert numbers(corpus.assertions).isdisjoint({1522000, 1530000, 1500000, 1800000, 18616})
    assert not any(x.field_path == "performance.thrust_sl" for x in a.values())
    # the rest of the table waits for the owner (mass, mixture ratio)
    assert not any(x.field_path.startswith(("mechanical.mass", "propellants.mixture_ratio")) for x in a.values())
    # admitted for CFG-F1 only, never inherited by the variant or family
    for subject in ("VAR-F1", "FAM-F1"):
        assert not [x for x in corpus.assertions if x.subject.id == subject and x.field_path.startswith("performance.")]
    r = evaluate_capability(corpus, "CFG-F1", Capability.PERFORMANCE_REFERENCE)
    assert {g.split(":")[0] for g in r.gaps} == {"mixture_ratio"}
    assert not [p for p in corpus.operating_points if p.configuration_id == "CFG-F1"]


def test_f1_qualification_life_ships_as_qualification_information_only(corpus):
    """Owner decision of 2026-10-10: Starts 20 and Duration 2,250 seconds, for CFG-F1 only; the
    printed mission duration is not admitted; the verbatim cell stays as provenance."""
    a = corpus.assertion_map["AS-DB05-US-F-1-010"]
    assert a.subject.id == "CFG-F1" and a.field_path == "test_history.qualification_life"
    assert a.value.text == "Starts 20; Duration 2,250 seconds"
    assert a.value_as_printed == "Starts 20; Duration 2,250 seconds; mission duration 165 seconds"
    assert a.operating_point_id is None and a.value_kind.value == "OTHER"
    for words in ("nominal operating life", "demonstrated flight life", "operating-point performance datum",
                  "regression quantity", "mission duration is not admitted"):
        assert words in a.note
    assert not [x for x in corpus.assertions if x.subject.id in ("VAR-F1", "FAM-F1")
                and x.field_path.startswith("test_history.")]
    # it raises neither performance nor regression
    for cap, status in ((Capability.PERFORMANCE_REFERENCE, "PARTIAL"), (Capability.REGRESSION_CANDIDATE, "NOT_SUPPORTED")):
        assert evaluate_capability(corpus, "CFG-F1", cap).status.value == status


def test_wave1_rights_readings_record_the_owner_review(corpus):
    wave1_sources = {s.reference.source_id for s in corpus.sources} - SEED_SOURCES
    assert len(wave1_sources) == 9
    for s in corpus.sources:
        if s.reference.source_id in wave1_sources:
            assert s.rights.review_note.endswith(
                "Owner-reviewed 2026-10-09 (a RocketForge shipping-policy review, not a legal determination).")


def test_f1_mixture_ratio_without_a_printed_direction_is_not_guessed(corpus):
    assert "AS-DB05-US-F-1-006" not in corpus.assertion_map
    assert not any(x.field_path == "propellants.mixture_ratio" for x in own(corpus, "CFG-F1").values())


def test_f1_topology_ships_without_the_withheld_manual(corpus):
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-F1")
    assert g.scope.id == "CFG-F1" and len(g.nodes) == 15 and len(g.edges) == 19
    shafts = {(e.source, e.target) for e in g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT)}
    assert shafts == {("N-TP-TURB", "N-TP-LOX"), ("N-TP-TURB", "N-TP-FUEL")}
    assert all("MSFC" not in x.locator for x in (*g.nodes, *g.edges))
    text = " ".join([g.notes, *g.completeness.known_omissions, *(n.label for n in g.nodes), *(e.role for e in g.edges)])
    for term in ("checkout", "helium", "dual ball valve", "on turbine exhaust"):
        assert term not in text.lower()
    assert "N-STAGE-PRESS" not in {n.node_id for n in g.nodes}
    assert g.completeness.absences == () and not g.stated_absent(ComponentType.TANK)


# ------------------------------------------------------------------ H-1


def test_h1_sparse_performance_does_not_block_the_rest(corpus):
    for capability in ("IDENTITY", "ARCHITECTURE", "TOPOLOGY"):
        assert status(corpus, "CFG-H1-188K-SA10", Capability(capability)) == "SUPPORTED"
    r = evaluate_capability(corpus, "CFG-H1-188K-SA10", Capability.PERFORMANCE_REFERENCE)
    assert {g.split(":")[0] for g in r.gaps} == {"specific_impulse", "chamber_pressure", "mixture_ratio", "area_ratio"}


def test_h1_missing_values_stay_missing_and_no_family_value_is_used(corpus):
    a = own(corpus, "CFG-H1-188K-SA10")
    fields = {x.field_path for x in a.values()}
    assert not fields & {"performance.chamber_pressure", "performance.specific_impulse",
                         "performance.specific_impulse_sl", "propellants.mixture_ratio"}
    assert all(x.source_id == "SRC-NTRS-19650013470" for x in a.values())
    assert a["AS-DB05-US-H-1-188K-001"].value == NumberValue(188000)
    assert a["AS-DB05-US-H-1-188K-011"].conditions.mixture_ratio_basis.value == "GAS_GENERATOR"
    assert [c.configuration_id for c in corpus.configurations if c.variant_id == "VAR-H1"] == ["CFG-H1-188K-SA10"]


def test_h1_schematic_callouts_do_not_ship(corpus):
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-H1-188K-SA10")
    roles = " ".join(e.role for e in g.edges)
    assert "callout" not in roles and not re.search(r"\b(968|930|880|830|728|893|812|785|790)\b", roles)
    assert len(g.edges_of_kind(EdgeKind.GEARED_DRIVE)) == 2


# ------------------------------------------------------------------ LMDE


def test_lmde_final_design_only(corpus):
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-LM-DPS-FINAL")
    assert set(g.schematic_ids) == {"SCH-DB05-LMDE-TND7143-F3", "SCH-DB05-LMDE-TND7143-F7"}
    assert "SCH-DB05-LMDE-TND7143-F6" not in {s.schematic_id for s in corpus.schematics}
    text = json.dumps(corpus_to_dict(corpus)["topologies"]) + json.dumps(
        [c.notes for c in corpus.configurations if c.configuration_id == "CFG-LMDE-FINAL"])
    for term in ("helium injection", "helium-injection", "fixed-area", "Fig. 6", "Figure 6"):
        assert term.lower() not in text.lower()


def test_lmde_stage_equipment_stays_outside_the_engine(corpus):
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-LM-DPS-FINAL")
    assert g.scope.kind is SubjectKind.PROPULSION_UNIT
    engine = {n.node_id for n in g.nodes if n.ownership is Ownership.ENGINE}
    assert engine == {"N-FCV", "N-TCA", "N-SOV", "N-INJ", "N-FILM", "N-TC", "N-NOZ"}
    vehicle = {n.node_id for n in g.nodes if n.ownership is Ownership.VEHICLE}
    assert {"N-SHE", "N-REG", "N-OX-TANKS", "N-FU-TANKS"} <= vehicle
    unit_level = [a for a in corpus.assertions if a.subject.id == "UNIT-LM-DPS-FINAL"]
    assert {a.field_path for a in unit_level} == {"pressurization.she", "pressurization.regulation"}


def test_lmde_fixed_throttle_point_is_shipped_as_printed(corpus):
    ftp = own(corpus, "CFG-LMDE-FINAL")["AS-DB05-US-LMDE-008"]
    assert ftp.value_kind is ValueKind.NOMINAL and ftp.value == NumberValue(92.5)
    assert "maximum operational" not in ftp.note


def test_lmde_requirements_stay_with_the_variant(corpus):
    context = context_assertions(corpus, "CFG-LMDE-FINAL")
    assert all(a.value_kind in (ValueKind.DESIGN_VALUE, ValueKind.OTHER) for a in context)
    assert all(a.value_kind is not ValueKind.DESIGN_VALUE for a in own(corpus, "CFG-LMDE-FINAL").values())


# ------------------------------------------------------------------ OMS


def test_oms_keeps_313_and_never_316(corpus):
    a = own(corpus, "CFG-OMS")
    assert a["AS-DB05-US-AJ10-190-004"].value == NumberValue(313)
    assert a["AS-DB05-US-AJ10-190-004"].conditions.environment is Environment.UNKNOWN
    assert 316 not in numbers(corpus.assertions)


def test_oms_mixture_ratio_and_chamber_pressure_are_not_guessed(corpus):
    fields = {x.field_path for x in own(corpus, "CFG-OMS").values()}
    assert "propellants.mixture_ratio" not in fields and "performance.chamber_pressure" not in fields
    r = evaluate_capability(corpus, "CFG-OMS", Capability.PERFORMANCE_REFERENCE)
    assert {g.split(":")[0] for g in r.gaps} == {"chamber_pressure", "mixture_ratio"}


def test_oms_rights_limited_record(corpus):
    assert "SRC-USA-OMS21002" not in {s.source_id for s in corpus.sources}
    assert configuration_topologies(corpus, "CFG-OMS") == ()
    assert {x.value.token for x in own(corpus, "CFG-OMS").values() if x.field_path.startswith("propellants.")} == {
        "NITROGEN_TETROXIDE", "MONOMETHYLHYDRAZINE"}


# ------------------------------------------------------------------ RS-25


def test_rs25_configurations_stay_distinct_through_a_round_trip(corpus):
    again = corpus_from_json(corpus_to_json(corpus))
    configs = {c.configuration_id: c.label for c in again.configurations if c.variant_id == "VAR-RS25"}
    assert set(configs) == {"CFG-RS25-SMALL-THROAT", "CFG-RS25-BLOCK-II", "CFG-RS25-SLS"}
    assert own(again, "CFG-RS25-SMALL-THROAT")["AS-DB05-US-SSME-BLOCK-I-001"].value == NumberValue(77.5)
    assert numbers(own(again, "CFG-RS25-BLOCK-II").values()) == {2870, 2747, 470000}
    assert numbers(own(again, "CFG-RS25-SLS").values()) == {512300}
    assert "Operational Thrust 109%" not in own(again, "CFG-RS25-SLS")["AS-DB05-US-SSME-BLOCK-II-016"].note


def test_rs25_block_iia_values_never_reach_block_ii(corpus):
    block_iia_values = {15519, 34311, 5018, 22250, 2871, 6.032}
    for cfg in ("CFG-RS25-BLOCK-II", "CFG-RS25-SLS", "CFG-RS25-SMALL-THROAT"):
        assert numbers(own(corpus, cfg).values()).isdisjoint(block_iia_values), cfg
        assert not any(x.field_path.startswith("pumps.") for x in own(corpus, cfg).values())
    assert "Block IIA" not in [c.label for c in corpus.configurations]


def test_rs25_rights_restricted_sources_and_figures_do_not_ship(corpus):
    shipped = {s.source_id for s in corpus.sources}
    for withheld in ("SRC-ENGINEHISTORY-SSMEORIENT-1998", "SRC-L3HARRIS-RS25-SPEC", "SRC-AIAA-97-2687",
                     "SRC-NTRS-20030005845"):
        assert withheld not in shipped
    assert "SCH-DB05-RS25IIA-BC9804-S19" not in {s.schematic_id for s in corpus.schematics}
    for cfg in ("CFG-RS25-SMALL-THROAT", "CFG-RS25-BLOCK-II", "CFG-RS25-SLS"):
        assert configuration_topologies(corpus, cfg) == ()


def test_rs25_open_conflicts_block_only_their_fields(corpus):
    sls = own(corpus, "CFG-RS25-SLS")
    assert any(x.field_path == "performance.thrust_vac" for x in sls.values())  # unaffected
    assert not any(x.field_path.startswith(("performance.thrust_sl", "mechanical.mass")) for x in sls.values())
    block_ii = own(corpus, "CFG-RS25-BLOCK-II")
    assert not any(x.field_path == "performance.thrust_sl" for x in block_ii.values())
    assert {x.operating_point_id for x in block_ii.values() if x.is_quantity} == {"OP-RS25-BII-RPL", "OP-RS25-BII-104"}


# ------------------------------------------------------------------ sources and rights


def test_wave1_sources_keep_their_rights_record(corpus):
    sources = {s.source_id: s for s in corpus.sources}
    mirror = sources["SRC-JSC-19950"]
    assert mirror.rights.host_metadata.reason is MissingReason.NOT_REPORTED
    assert "ibiblio" in mirror.reference.locator
    biggs = sources["SRC-DB05-NTRS-20100027316"]
    assert biggs.rights.values is ShippingPolicy.VALUES_WITH_ATTRIBUTION
    assert biggs.rights.figures is ShippingPolicy.RIGHTS_REVIEW_REQUIRED
    for s in corpus.sources:
        assert s.rights.tables is ShippingPolicy.RIGHTS_REVIEW_REQUIRED and s.rights.text is ShippingPolicy.RIGHTS_REVIEW_REQUIRED


def test_wave1_schematics_are_original_drawings(corpus):
    provenance = {s.schematic_id: s.provenance for s in corpus.schematics}
    assert provenance["SCH-DB05-F1-BIGGS-SCHEM"] is SchematicProvenance.ORIGINAL_MANUFACTURER
    assert provenance["SCH-DB05-H1-SA10-F31"] is SchematicProvenance.ORIGINAL_CONTRACTOR
    assert provenance["SCH-DB05-LMDE-TND7143-F7"] is SchematicProvenance.ORIGINAL_AGENCY
