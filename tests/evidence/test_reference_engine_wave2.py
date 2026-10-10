"""DB-2B Wave 2 in the shipped corpus: what each difficult target carries, and what it must not.

These read the production file only. Capability results are evaluated, never set here.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from rocketforge.evidence.engines import EdgeKind, NumberValue, corpus_from_json, corpus_to_dict
from rocketforge.evidence.engines.capabilities import Capability, configuration_assertions, evaluate_capability
from rocketforge.evidence.engines.vocabulary import SchematicProvenance

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHIPPED = ROOT / "rocketforge" / "data" / "evidence" / "engines" / "reference_engines.json"
WAVE2 = ("CFG-RL10B-2-DIV", "CFG-RD-170", "CFG-IPD", "CFG-RS-68A", "CFG-LR87-AJ-11-T3E")


@pytest.fixture(scope="module")
def corpus():
    return corpus_from_json(SHIPPED.read_text(encoding="utf-8"))


def own(corpus, cfg):
    return {a.assertion_id: a for a in configuration_assertions(corpus, cfg)}


def text(corpus, cfg):
    d = corpus_to_dict(corpus)
    return json.dumps([a for a in d["assertions"] if a["subject"]["id"] == cfg]
                      + [c for c in d["configurations"] if c["configuration_id"] == cfg]
                      + [t for t in d["topologies"] if t["scope"]["id"] == cfg])


#: What each Wave 2 configuration's evidence supports, as evaluated.
EXPECTED = {
    "CFG-RL10B-2-DIV": dict(IDENTITY="SUPPORTED", ARCHITECTURE="PARTIAL", PERFORMANCE_REFERENCE="PARTIAL",
                            TOPOLOGY="NOT_SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-RD-170": dict(IDENTITY="SUPPORTED", ARCHITECTURE="PARTIAL", PERFORMANCE_REFERENCE="NOT_SUPPORTED",
                       TOPOLOGY="PARTIAL", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-IPD": dict(IDENTITY="SUPPORTED", ARCHITECTURE="SUPPORTED", PERFORMANCE_REFERENCE="NOT_SUPPORTED",
                    TOPOLOGY="NOT_SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-RS-68A": dict(IDENTITY="SUPPORTED", ARCHITECTURE="NOT_SUPPORTED", PERFORMANCE_REFERENCE="NOT_SUPPORTED",
                            TOPOLOGY="NOT_SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
    "CFG-LR87-AJ-11-T3E": dict(IDENTITY="SUPPORTED", ARCHITECTURE="SUPPORTED", PERFORMANCE_REFERENCE="PARTIAL",
                               TOPOLOGY="SUPPORTED", REGRESSION_CANDIDATE="NOT_SUPPORTED"),
}


@pytest.mark.parametrize("cfg", WAVE2)
def test_wave2_capabilities_are_what_the_evidence_supports(corpus, cfg):
    got = {cap.name: evaluate_capability(corpus, cfg, cap).status.value for cap in Capability}
    assert got == EXPECTED[cfg]


def test_no_wave2_configuration_is_a_regression_candidate(corpus):
    assert all(evaluate_capability(corpus, cfg, Capability.REGRESSION_CANDIDATE).status.value == "NOT_SUPPORTED"
               for cfg in WAVE2)


def test_rights_refused_targets_and_sources_ship_nothing(corpus):
    ids = {a.assertion_id for a in corpus.assertions}
    assert not [i for i in ids if i.startswith(("AS-DB05-US-RL10A-4-2-", "AS-DB05-NZ-"))]
    sources = {s.reference.source_id for s in corpus.sources}
    assert not sources & {"SRC-NAP-11780", "SRC-ULA-DIV-GPSIIISV02", "SRC-ULA-CENTAUR-ICLT4", "SRC-RL-PRESSKIT-2017",
                          "SRC-RL-500-TESTS", "SRC-RKLB-PAYLOAD-INCREASE", "SRC-RL-ELECTRON-PAGE",
                          "SRC-NASA-PSP-BLOG-WORKHORSE"}  # the last: a blog, discovery only
    names = json.dumps([[v.designation, v.notes] for v in corpus.variants] + [[c.label] for c in corpus.configurations])
    assert "rutherford" not in names.lower() and "rl10a-4-2" not in names.lower()


def test_wave2_rights_readings_record_the_owner_review(corpus):
    """Owner decision 2026-10-10: a shipping-policy review, not a legal determination; nothing upgraded."""
    wave2_sources = {"SRC-ULA-DIV-INAUGURAL", "SRC-NTRS-19910018906", "SRC-DB05-NTRS-19950002748", "SRC-NTRS-IPD-WPB",
                     "SRC-DB05-NTRS-20050243602", "SRC-DB05-NTRS-20090014109", "SRC-DB05-NTRS-19750004937"}
    for s in corpus.sources:
        if s.reference.source_id in wave2_sources:
            assert s.rights.review_note.endswith(
                "Owner-reviewed 2026-10-10 (a RocketForge shipping-policy review, not a legal determination).")
            assert s.rights.values.value == "VALUES_WITH_ATTRIBUTION"


# ------------------------------------------------------------------ RL10B-2


def test_rl10b2_ships_no_pc_or_isp_and_an_unstated_thrust_environment(corpus):
    a = own(corpus, "CFG-RL10B-2-DIV")
    assert not any(x.field_path.startswith(("performance.chamber_pressure", "performance.specific_impulse")) for x in a.values())
    thrust = [x for x in a.values() if x.field_path == "performance.thrust"]
    assert [x.value.value for x in thrust] == [24750] and thrust[0].conditions.environment.value == "UNKNOWN"
    assert {x.source_id for x in a.values()} == {"SRC-ULA-DIV-INAUGURAL"}
    assert not any(n in text(corpus, "CFG-RL10B-2-DIV") for n in ("644", "633", "466.5", "465.5"))


# ------------------------------------------------------------------ RD-170


def test_rd170_topology_stays_a_third_party_reconstruction(corpus):
    sch = next(s for s in corpus.schematics if s.schematic_id == "SCH-DB05-RD170-RKWL-P19")
    assert sch.provenance is SchematicProvenance.THIRD_PARTY_RECONSTRUCTION
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-RD-170")
    assert g.scope.id == "CFG-RD-170" and len(g.nodes) == 9 and len(g.edges) == 12
    r = evaluate_capability(corpus, "CFG-RD-170", Capability.TOPOLOGY)
    assert r.status.value == "PARTIAL" and r.gaps


def test_rd170_graph_is_what_rockwell_drew(corpus):
    """Review findings: the fuel line is labelled FUEL (no source prints RP-1); the LP fuel pump's return line
    rises from the kick pump; no line joins the HP fuel pump and the kick pump; 'turbine drive' is not printed."""
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-RD-170")
    assert {e.carrier for e in g.edges if e.carrier} == {"LOX", "fuel", "ox-rich gas"}
    pairs = {(e.source, e.target) for e in g.edges}
    assert ("N-KICK", "N-LPFP") in pairs and ("N-HPFP", "N-LPFP") not in pairs and ("N-HPFP", "N-KICK") not in pairs
    assert not any("turbine drive" in e.role and e.target in ("N-LPOP", "N-LPFP") for e in g.edges)
    assert len(g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT)) == 2
    assert "RP-1" not in json.dumps([x for x in corpus_to_dict(corpus)["topologies"] if x["topology_id"] == "TOPO-RD-170"])


def test_rd170_ships_no_placard_value_and_no_mixture_ratio(corpus):
    a = own(corpus, "CFG-RD-170")
    assert not any(x.field_path.startswith(("performance.", "propellants.mixture_ratio")) for x in a.values())
    assert {x.source_id for x in a.values()} == {"SRC-DB05-NTRS-19950002748", "SRC-NTRS-19910018906"}
    layout = a["AS-DB05-SU-RD-170-006"]
    assert "CONFIRMED_SECONDARY" in layout.note and "secondary" in layout.note
    body = text(corpus, "CFG-RD-170")
    assert not any(n in body for n in ("740 t", "806 t", "2.58", "2.47", "kgs/cm2", "3,556"))
    fuel = next(x for x in a.values() if x.field_path == "propellants.fuel")
    assert fuel.value.token == "KEROSENE"  # printed 'Kerosene', not RP-1


# ------------------------------------------------------------------ IPD


def test_ipd_has_no_graph_from_its_cycle_name(corpus):
    assert not [t for t in corpus.topologies if t.scope.id == "CFG-IPD"]
    assert evaluate_capability(corpus, "CFG-IPD", Capability.TOPOLOGY).status.value == "NOT_SUPPORTED"
    cycle = [x for x in own(corpus, "CFG-IPD").values() if x.field_path == "architecture.cycle"]
    assert [x.value.token for x in cycle] == ["FULL_FLOW_STAGED_COMBUSTION"]


def test_ipd_design_class_is_a_variant_design_value_not_a_tested_value(corpus):
    thrust = [a for a in corpus.assertions if a.assertion_id == "AS-DB05-US-IPD-013"]
    assert thrust[0].subject.id == "VAR-IPD" and thrust[0].value_kind.value == "DESIGN_VALUE"
    assert "goal of designing" in thrust[0].value_as_printed and thrust[0].source_id == "SRC-DB05-NTRS-20050243602"
    assert "AS-DB05-US-IPD-001" not in corpus.assertion_map
    assert not any(x.field_path.startswith("performance.") for x in own(corpus, "CFG-IPD").values())


def test_ipd_test_articles_are_not_the_engine(corpus):
    ids = {a.assertion_id for a in corpus.assertions}
    assert not {"AS-DB05-US-IPD-003", "AS-DB05-US-IPD-005"} & ids


# ------------------------------------------------------------------ RS-68A


def test_rs68a_carries_no_rs68_value_and_no_thrust(corpus):
    assert not any(x.field_path.startswith("performance.") for x in own(corpus, "CFG-RS-68A").values())
    body = json.dumps(corpus_to_dict(corpus)["assertions"])
    assert "650,000" not in body and "702,000" not in body and "705," not in body
    changes = own(corpus, "CFG-RS-68A")
    assert changes and all(not isinstance(a.value, NumberValue) for a in changes.values())
    assert {a.source_id for a in changes.values()} == {"SRC-DB05-NTRS-20090014109"}


# ------------------------------------------------------------------ LR87


def test_lr87_values_stay_on_the_lr87aj11(corpus):
    lr = [a for a in corpus.assertions if a.assertion_id.startswith("AS-DB05-US-LR87-")]
    assert lr and {a.subject.id for a in lr} == {"CFG-LR87-AJ-11-T3E"}
    assert [c.configuration_id for c in corpus.configurations if "LR87" in c.configuration_id] == ["CFG-LR87-AJ-11-T3E"]
    a = own(corpus, "CFG-LR87-AJ-11-T3E")
    tokens = {x.field_path: x.value.token for x in a.values() if hasattr(x.value, "token")}
    assert tokens["propellants.fuel"] == "AEROZINE_50" and tokens["propellants.oxidizer"] == "NITROGEN_TETROXIDE"
    assert not any(x.field_path in ("propellants.mixture_ratio", "performance.chamber_pressure") for x in a.values())


def test_lr87_graph_is_the_contractor_schematic_with_its_omissions(corpus):
    g = next(t for t in corpus.topologies if t.topology_id == "TOPO-LR87-AJ-11")
    assert len(g.nodes) == 16 and len(g.edges) == 18
    sch = next(s for s in corpus.schematics if s.schematic_id == "SCH-DB05-LR87AJ11-GD-F620")
    assert sch.provenance is SchematicProvenance.ORIGINAL_CONTRACTOR
    assert "subassembly 2 (identical, per the text)" in g.completeness.known_omissions
    assert not g.completeness.declared_complete
    assert len(g.edges_of_kind(EdgeKind.GEARED_DRIVE)) == 2  # report p.6-23: 'through a gear train'
    assert not g.edges_of_kind(EdgeKind.MECHANICAL_SHAFT)
    assert {e.carrier for e in g.edges if e.carrier} == {"fuel", "oxidizer", "hot gas"}
