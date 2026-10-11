"""The Reference Engines projection and controller (DB-3A) against the shipped corpus.

The projection is pure: it reads the admitted catalog and returns display rows.
These tests pin the honesty rules the workspace exists to keep -- values as
printed, unknown conditions kept unknown, context apart from the configuration,
design values and limits never among the operating values, missing data named
rather than zeroed, capabilities reported one by one, and a topology drawn from
its own nodes and edges only, with a deterministic, presentation-only layout.
"""
from __future__ import annotations

import os

import pytest

from rocketforge.application.analysis import reference_engine_view as view
from rocketforge.application.analysis.reference_engine_catalog import load_reference_engines
from rocketforge.evidence.engines.capabilities import Capability


@pytest.fixture(scope="module")
def catalog():
    return load_reference_engines()


def _all_facts(catalog, cfg):
    return [row for group in view.fact_groups(catalog, cfg) for row in group["rows"]]


# ------------------------------------------------------------------ library


def test_the_library_lists_every_configuration_in_a_fixed_order(catalog):
    rows = view.library_rows(catalog, view.visible_entries(catalog, view.EngineFilter()))
    assert len(rows) == len(catalog.entries()) == 16
    keys = [(r["section"].casefold(), r["title"].casefold()) for r in rows]
    assert keys == sorted(keys)
    assert sum(r["sectionStart"] for r in rows) == len({r["section"] for r in rows})
    again = view.library_rows(catalog, view.visible_entries(catalog, view.EngineFilter()))
    assert rows == again


@pytest.mark.parametrize("text,expected", [
    ("j-2", {"CFG-J2-230K", "CFG-J2S"}),
    ("RL10", {"CFG-RL10A-3-3A", "CFG-RL10B-2-DIV"}),
    ("rd-170", {"CFG-RD-170"}),
    ("  F-1 ", {"CFG-F1"}),
    ("CFG-RS-68A", {"CFG-RS-68A"}),
    ("no such engine", set()),
])
def test_search_matches_names_designations_families_aliases_and_ids(catalog, text, expected):
    found = {e.configuration_id for e in view.visible_entries(catalog, view.EngineFilter(search=text))}
    assert found == expected


def test_aliases_are_searchable(catalog):
    for alias in catalog.corpus.aliases:
        found = view.visible_entries(catalog, view.EngineFilter(search=alias.name))
        assert found, alias.name


def test_filters_use_the_backend_vocabulary_and_agree_with_it(catalog):
    options = view.filter_options(catalog)
    assert [o["key"] for o in options["capability"]] == [c.value for c in view.CAPABILITY_ORDER]
    assert {o["key"] for o in options["status"]} <= set(view.STATUS_WORDS)
    for cap in view.CAPABILITY_ORDER:
        for status in options["status"]:
            f = view.EngineFilter(capability=cap.value, status=status["key"])
            got = {e.configuration_id for e in view.visible_entries(catalog, f)}
            want = {e.configuration_id for e in catalog.entries()
                    if catalog.capability(e.configuration_id, cap).status.value == status["key"]}
            assert got == want
    # a capability alone narrows nothing: the pair is the filter
    alone = view.visible_entries(catalog, view.EngineFilter(capability="TOPOLOGY"))
    assert len(alone) == 16


def test_the_cycle_filter_offers_only_recorded_cycles_and_names_absence(catalog):
    options = [o["key"] for o in view.filter_options(catalog)["cycle"]]
    assert options[-1] == "NOT_RECORDED"
    none = {e.configuration_id for e in view.visible_entries(catalog, view.EngineFilter(cycle="NOT_RECORDED"))}
    some = set()
    for key in options[:-1]:
        some |= {e.configuration_id for e in view.visible_entries(catalog, view.EngineFilter(cycle=key))}
    assert none and some and not (none & some) and (none | some) == {e.configuration_id for e in catalog.entries()}


def test_library_capability_line_has_no_score(catalog):
    for row in view.library_rows(catalog, view.visible_entries(catalog, view.EngineFilter())):
        assert "%" not in row["capabilities"] and "/" not in row["capabilities"]


# ------------------------------------------------------------------ capabilities


def test_five_capabilities_are_reported_independently_in_backend_words(catalog):
    for entry in catalog.entries():
        rows = view.capability_rows(catalog, entry.configuration_id)
        assert [r["capability"] for r in rows] == [c.value for c in view.CAPABILITY_ORDER]
        for row, result in zip(rows, catalog.capabilities(entry.configuration_id)):
            assert row["status"] == result.status.value
            assert row["statusLabel"] == view.STATUS_WORDS[row["status"]]
            assert row["glyph"]                      # a shape, not only a colour


def test_regression_candidate_is_eligibility_only(catalog):
    row = view.capability_rows(catalog, "CFG-J2-230K")[4]
    assert row["status"] == "SUPPORTED"
    assert "Eligible only" in row["summary"] and "validated" not in row["summary"].casefold()
    readout = view.capability_readout(catalog, "CFG-J2-230K", "REGRESSION_CANDIDATE")
    assert "Eligibility only" in readout["sections"][0]["rows"][0]["value"]


# ------------------------------------------------------------------ values


def test_values_are_shown_as_printed(catalog):
    for entry in catalog.entries():
        for a in catalog.assertions(entry.configuration_id):
            text = view.reading(a)
            assert text.startswith(a.value_as_printed.rstrip())


def test_a_printed_unit_is_not_repeated(catalog):
    a = next(x for x in catalog.corpus.assertions if x.assertion_id == "AS-DB05-US-F-1-011")
    assert view.reading(a) == "16:1"
    thrust = next(x for x in catalog.assertions("CFG-F1") if x.field_path == "performance.thrust_vac")
    assert view.reading(thrust) == thrust.value_as_printed + " " + thrust.unit_as_printed
    # a sentence keeps its own words: no unit is glued onto it (visual QA finding)
    for a in catalog.corpus.assertions:
        if any(ch.isalpha() for ch in a.value_as_printed):
            assert view.reading(a) == a.value_as_printed.rstrip(), a.assertion_id


def test_an_unknown_station_stays_unknown(catalog):
    rows = [r for r in _all_facts(catalog, "CFG-RS25-BLOCK-II") if r["field"] == "performance.chamber_pressure"]
    assert rows and all("Pressure station: Unknown" in r["conditions"] for r in rows)
    readout = view.assertion_readout(catalog, "CFG-RS25-BLOCK-II", rows[0]["assertionId"])
    conditions = next(s for s in readout["sections"] if s["title"] == "Conditions")["rows"]
    assert {"label": "Pressure station", "value": "Unknown (not stated by the source)"} in conditions


def test_a_condition_the_record_does_not_carry_is_not_invented(catalog):
    for entry in catalog.entries():
        for a in catalog.assertions(entry.configuration_id):
            labels = [label for label, _ in view.condition_items(a)]
            carried = sum(getattr(a.conditions, attr) is not None for attr, _ in view._CONDITION_LABELS)
            assert len(labels) == carried + len(a.conditions.qualifiers)


def test_design_values_limits_and_qualification_life_are_not_operating_values(catalog):
    for entry in catalog.entries():
        cfg = entry.configuration_id
        operating = {r["assertionId"] for g in view.fact_groups(catalog, cfg) if g["key"] == "performance"
                     for r in g["rows"]}
        assert operating == set(catalog.capability(cfg, Capability.PERFORMANCE_REFERENCE).assertion_ids) & \
            {a.assertion_id for a in catalog.assertions(cfg)}
        for a in (*catalog.assertions(cfg), *view.context_assertions(catalog, cfg)):
            if a.value_kind.value in ("DESIGN_VALUE", "LIMIT") or "qualification" in a.field_path:
                assert a.assertion_id not in operating, a.assertion_id
    # the corpus does hold design values (LMDE, IPD) and a qualification life (F-1): the check bites
    kinds = {a.value_kind.value for e in catalog.entries()
             for a in (*catalog.assertions(e.configuration_id), *view.context_assertions(catalog, e.configuration_id))}
    assert "DESIGN_VALUE" in kinds
    assert any("qualification" in a.field_path for a in catalog.assertions("CFG-F1"))


def test_context_is_kept_apart_from_the_configuration(catalog):
    for entry in catalog.entries():
        cfg = entry.configuration_id
        own = {r["assertionId"] for r in _all_facts(catalog, cfg)}
        ctx = {r["assertionId"] for r in view.context_rows(catalog, cfg)}
        assert not (own & ctx)
        for row in view.context_rows(catalog, cfg):
            assert row["level"] in ("Variant", "Family", "Propulsion unit")
    for row in view.context_rows(catalog, "CFG-LMDE-FINAL"):
        readout = view.assertion_readout(catalog, "CFG-LMDE-FINAL", row["assertionId"])
        scope = next(s for s in readout["sections"] if s["title"] == "Scope")["rows"]
        assert any("not a value of this configuration" in r["value"] for r in scope), row["assertionId"]


def test_every_shipped_assertion_is_shown_somewhere(catalog):
    """Review minor 6: the propulsion-unit assertions were shown nowhere."""
    shown = set()
    for entry in catalog.entries():
        cfg = entry.configuration_id
        shown |= {r["assertionId"] for r in _all_facts(catalog, cfg)}
        shown |= {r["assertionId"] for r in view.context_rows(catalog, cfg)}
    assert {a.assertion_id for a in catalog.corpus.assertions} == shown
    levels = {r["assertionId"]: r["level"] for r in view.context_rows(catalog, "CFG-LMDE-FINAL")}
    assert levels["AS-DB05-US-LMDE-013"] == levels["AS-DB05-US-LMDE-014"] == "Propulsion unit"


def test_a_value_whose_excerpt_lacks_its_unit_says_the_unit(catalog):
    rows = {r["assertionId"]: r for r in _all_facts(catalog, "CFG-RS25-SMALL-THROAT")}
    pc = rows["AS-DB05-US-SSME-BLOCK-I-002"]
    assert pc["valueText"] == "3285 (109% power level)" and pc["unitNote"] == "Unit as printed: psia"
    f1 = {r["field"]: r for r in _all_facts(catalog, "CFG-F1")}
    assert f1["performance.thrust_vac"]["unitNote"] == ""      # '1,748,200 lb' already says it


def test_the_table_prints_the_excerpt_and_says_how_it_is_recorded(catalog):
    keys, rows = view.assertion_table(catalog, "CFG-J2-230K")
    columns = [c["key"] for c in view.TABLE_COLUMNS]
    by_id = {a.assertion_id: a for a in catalog.assertions("CFG-J2-230K")}
    for key, row in zip(keys, rows):
        assert row[columns.index("value")] == by_id[key].value_as_printed
    cycle = next(row for key, row in zip(keys, rows) if by_id[key].field_path == "architecture.cycle")
    assert cycle[columns.index("recorded")] == "Gas generator"


def test_missing_performance_is_named_not_zeroed(catalog):
    rows = view.missing_rows(catalog, "CFG-RD-170")
    assert {r["quantity"] for r in rows} >= {"Thrust", "Specific impulse", "Chamber pressure", "Mixture ratio"}
    assert all(r["reason"] for r in rows)
    assert view.missing_rows(catalog, "CFG-J2-230K") == []


def test_no_table_cell_is_empty_or_a_dash(catalog):
    for entry in catalog.entries():
        cfg = entry.configuration_id
        for table in (view.assertion_table(catalog, cfg)[1], view.connection_table(catalog, cfg)[1]):
            for row in table:
                for cell in row:
                    assert str(cell).strip() not in ("", "-", "—", "0"), (cfg, row)


def test_readouts_never_show_an_empty_heading(catalog):
    for entry in catalog.entries():
        cfg = entry.configuration_id
        readouts = [view.configuration_readout(catalog, cfg)]
        readouts += [view.capability_readout(catalog, cfg, c.value) for c in view.CAPABILITY_ORDER]
        readouts += [view.assertion_readout(catalog, cfg, a.assertion_id)
                     for a in (*catalog.assertions(cfg), *view.context_assertions(catalog, cfg))]
        readouts += [view.source_readout(catalog, s.reference.source_id) for s in catalog.sources(cfg)]
        for r in readouts:
            assert all(section["rows"] for section in r["sections"]), r["title"]


def test_sources_keep_authority_and_rights_apart(catalog):
    readout = view.source_readout(catalog, "SRC-NTRS-19910018906")
    titles = [s["title"] for s in readout["sections"]]
    assert "Technical authority" in titles and "Rights and shipping" in titles
    text = " ".join(r["value"] for s in readout["sections"] for r in s["rows"])
    assert "not a legal determination" in text


# ------------------------------------------------------------------ topology


def test_a_graph_draws_exactly_its_own_nodes_and_edges(catalog):
    for entry in catalog.entries():
        cfg = entry.configuration_id
        graphs = {g.topology_id: g for g in catalog.topologies(cfg)}
        for v in view.graph_views(catalog, cfg):
            g = graphs[v["topologyId"]]
            assert [n["nodeId"] for n in v["nodes"]] == [n.node_id for n in g.nodes]
            assert [(e["edgeId"], e["source"], e["target"]) for e in v["edges"]] == \
                [(e.edge_id, e.source, e.target) for e in g.edges]
            assert [n["ownership"] for n in v["nodes"]] == [n.ownership.value for n in g.nodes]


def test_the_layout_is_deterministic_and_never_overlaps(catalog):
    for entry in catalog.entries():
        cfg = entry.configuration_id
        first, second = view.graph_views(catalog, cfg), view.graph_views(catalog, cfg)
        assert first == second
        for v in first:
            boxes = {(n["x"], n["y"]) for n in v["nodes"]}
            assert len(boxes) == len(v["nodes"])
            assert all(n["x"] + n["w"] <= v["width"] and n["y"] + n["h"] <= v["height"] for n in v["nodes"])


def test_the_rd170_reconstruction_is_flagged_and_originals_are_not(catalog):
    rd = view.graph_views(catalog, "CFG-RD-170")[0]
    assert rd["reconstruction"] and "Third-party reconstruction" in rd["provenanceText"]
    assert not rd["declaredComplete"] and rd["omissions"]
    for cfg in ("CFG-F1", "CFG-J2-230K", "CFG-LMDE-FINAL", "CFG-LR87-AJ-11-T3E", "CFG-H1-188K-SA10"):
        g = view.graph_views(catalog, cfg)[0]
        assert not g["reconstruction"] and "original drawing" in g["provenanceText"], cfg


def test_a_record_without_topology_gets_none(catalog):
    for cfg in ("CFG-J2S", "CFG-IPD", "CFG-RS-68A", "CFG-RL10B-2-DIV"):
        assert view.graph_views(catalog, cfg) == []
        assert view.connection_table(catalog, cfg) == ([], [])


def test_the_graph_readout_says_position_is_not_evidence(catalog):
    readout = view.graph_readout(catalog, "CFG-RD-170", "TOPO-RD-170")
    text = " ".join(r["value"] for s in readout["sections"] for r in s["rows"])
    assert "where a node sits on screen is not" in text and "not a copy of the figure" in text


def test_non_engine_components_are_marked(catalog):
    lmde = view.graph_views(catalog, "CFG-LMDE-FINAL")[0]
    vehicle = [n for n in lmde["nodes"] if n["ownership"] == "VEHICLE"]
    assert vehicle and not any(n["engineOwned"] for n in vehicle)
    assert all(n["ownershipWord"] == "Vehicle" for n in vehicle)
    assert lmde["hasNonEngine"]
    f1 = view.graph_views(catalog, "CFG-F1")[0]
    assert any(n["ownership"] == "AMBIENT" and not n["engineOwned"] for n in f1["nodes"])


def _graphs(catalog):
    seen = {}
    for entry in catalog.entries():
        for v in view.graph_views(catalog, entry.configuration_id):
            seen.setdefault(v["topologyId"], v)
    return list(seen.values())


def test_no_wire_passes_under_a_component_it_does_not_connect(catalog):
    """A wire drawn under a box reads as a connection the graph does not hold (review M1)."""
    for v in _graphs(catalog):
        boxes = {n["nodeId"]: (n["x"], n["y"], n["x"] + n["w"], n["y"] + n["h"]) for n in v["nodes"]}
        for e in v["edges"]:
            points = e["points"]
            for p, q in zip(points, points[1:]):
                assert p[0] == q[0] or p[1] == q[1], (e["edgeId"], p, q)       # orthogonal
                for nid, (x0, y0, x1, y1) in boxes.items():
                    for k in range(41):
                        x = p[0] + (q[0] - p[0]) * k / 40
                        y = p[1] + (q[1] - p[1]) * k / 40
                        assert not (x0 + 0.5 < x < x1 - 0.5 and y0 + 0.5 < y < y1 - 0.5), \
                            (v["topologyId"], e["edgeId"], nid)
            # it starts on its source's right side and ends on its target's left side
            sx0, sy0, sx1, sy1 = boxes[e["source"]]
            tx0, ty0, tx1, ty1 = boxes[e["target"]]
            assert points[0][0] == sx1 and sy0 < points[0][1] < sy1
            assert points[-1][0] == tx0 and ty0 < points[-1][1] < ty1
            # the handle sits on the wire, outside every box
            hx, hy = e["mx"], e["my"]
            assert not any(x0 < hx < x1 and y0 < hy < y1 for x0, y0, x1, y1 in boxes.values()), e["edgeId"]


def test_no_two_wires_share_a_run_unless_they_share_an_end(catalog):
    """Two wires on the same line would read as a merge the graph does not record."""
    for v in _graphs(catalog):
        segments = []
        for e in v["edges"]:
            pts = e["points"]
            last = len(pts) - 2
            segments += [(e, i, last, p, q) for i, (p, q) in enumerate(zip(pts, pts[1:]))]
        for i, (e1, i1, l1, p1, q1) in enumerate(segments):
            for e2, i2, l2, p2, q2 in segments[i + 1:]:
                if e1 is e2:
                    continue
                for axis in (0, 1):
                    other = 1 - axis
                    if p1[other] == q1[other] and p2[other] == q2[other] and abs(p1[other] - p2[other]) < 0.5:
                        lo = max(min(p1[axis], q1[axis]), min(p2[axis], q2[axis]))
                        hi = min(max(p1[axis], q1[axis]), max(p2[axis], q2[axis]))
                        if hi - lo > 1:
                            shared_source = i1 == i2 == 0 and e1["source"] == e2["source"]
                            shared_target = i1 == l1 and i2 == l2 and e1["target"] == e2["target"]
                            assert shared_source or shared_target, (v["topologyId"], e1["edgeId"], e2["edgeId"])


def test_every_arrowhead_points_into_its_target(catalog):
    for v in _graphs(catalog):
        boxes = {n["nodeId"]: n for n in v["nodes"]}
        for e in v["edges"]:
            target = boxes[e["target"]]
            assert e["x3"] == target["x"] and e["ax"] < e["x3"] and e["bx"] < e["x3"]


# ------------------------------------------------------------------ controller


@pytest.fixture(scope="module")
def controller():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QCoreApplication

    from rocketforge.application.analysis.reference_engine_controller import ReferenceEngineController
    _app = QCoreApplication.instance() or QCoreApplication([])
    return ReferenceEngineController()


def test_the_controller_selects_deterministically_and_follows_filters(controller):
    controller.clearFilters()
    first = controller.library.rows()[0]["configurationId"]
    assert controller.selectedConfigurationId == first
    controller.setSearch("rd-170")
    assert controller.selectedConfigurationId == "CFG-RD-170" and controller.visibleCount == 1
    controller.setSearch("zz no match")
    assert controller.emptyState == "no-match" and controller.selectedConfigurationId == ""
    controller.clearFilters()
    assert controller.emptyState == "" and controller.visibleCount == 16


def test_the_controller_refuses_what_it_does_not_offer(controller):
    controller.clearFilters()
    controller.setFilterStatus("BOGUS")
    controller.setFilterCycle("BOGUS")
    controller.setFilterCapability("BOGUS")
    assert not controller.hasActiveFilter
    controller.selectConfiguration("CFG-DOES-NOT-EXIST")
    assert controller.selectedConfigurationId
    controller.inspectAssertion("AS-NOT-HERE")
    controller.inspectNode("N-NOT-HERE")
    assert controller.inspectionKind == ""


def test_the_controller_inspects_and_switches_graph_state(controller):
    controller.clearFilters()
    controller.selectConfiguration("CFG-RD-170")
    assert controller.graphCount == 1 and controller.graphReconstruction
    node = controller.graphNodes.rows()[0]["nodeId"]
    controller.inspectNode(node)
    assert controller.inspectionKind == "node" and controller.selectedNodeId == node
    controller.inspectConnectionRow(0)
    assert controller.inspectionKind == "edge" and controller.selectedConnectionRow == 0
    controller.inspectTableRow(0)
    assert controller.inspectionKind == "assertion" and controller.selectedTableRow == 0
    controller.selectConfiguration("CFG-J2S")
    assert controller.inspectionKind == "" and controller.graphCount == 0 and controller.graphNodes.count() == 0
    assert controller.inspectionReadout["kind"] == "configuration"


def test_the_controller_holds_no_mutating_slot(controller):
    from PySide6.QtCore import QMetaMethod
    meta = controller.metaObject()
    names = {bytes(meta.method(i).name()).decode() for i in range(meta.methodOffset(), meta.methodCount())
             if meta.method(i).methodType() == QMetaMethod.MethodType.Slot}
    banned = ("edit", "save", "delete", "create", "import", "promote", "override", "solve", "run", "write")
    assert not [n for n in names if n.casefold().startswith(banned)], names


def test_a_recorded_number_is_never_rounded(catalog):
    """'%g' would round past six significant digits; the recorded value is shown exactly."""
    assert view._exact(1748215.0) == "1748215" and view._exact(2.924) == "2.924"
    columns = [c["key"] for c in view.TABLE_COLUMNS]
    for entry in catalog.entries():
        keys, rows = view.assertion_table(catalog, entry.configuration_id)
        by_id = {a.assertion_id: a for a in catalog.assertions(entry.configuration_id)}
        for key, row in zip(keys, rows):
            value = by_id[key].value
            if hasattr(value, "value") and isinstance(value.value, float):
                assert float(row[columns.index("recorded")]) == value.value, key
