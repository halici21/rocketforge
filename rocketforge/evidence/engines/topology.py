"""Hardware identities, schematics and topology graphs.

A :class:`Component` is a piece of hardware of one configuration (or of a
propulsion unit, for hardware several engines share), typed and owned (engine, stage, vehicle, ambient, external). Facts about it -- stage
count, rich side, speed -- are assertions whose subject is the component, so
a component never carries an unsourced attribute.

A :class:`TopologyGraph` is first-class -- an engine graph or a stage/system
graph -- with nodes, typed edges (fluid flow,
common shaft, geared drive, mechanical linkage, electrical power, control
actuation), per-element evidence and locators, the schematics and texts it
rests on, and an explicit completeness statement. **Omission is never
absence**: a graph says what it knows it leaves out; that a component is not
there is stated only by an :class:`AbsenceStatement` citing a source that
says so.

A :class:`Schematic` records who drew it. A third-party reconstruction (the
Rockwell RD-170 drawing from 1989 display photographs) is recorded as one and
never qualifies a graph as an original drawing of the hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..values import EvidenceError
from . import _checks as c
from .identity import SubjectRef
from .vocabulary import (
    FLUID_EDGE_KINDS,
    MEDIUM_EDGE_KINDS,
    ComponentType,
    EdgeKind,
    Ownership,
    SchematicProvenance,
    SubjectKind,
    TopologyEvidence,
)

__all__ = [
    "Component", "Schematic", "TopologyNode", "TopologyEdge", "AbsenceStatement",
    "Completeness", "TopologyGraph", "HARDWARE_SCOPES",
]

#: What hardware and graphs can belong to: one engine configuration, or a
#: propulsion unit (a stage's propulsion, a module, a multi-engine system)
#: whose shared tanks, pressurisation and feed serve several engines.
HARDWARE_SCOPES = frozenset({SubjectKind.CONFIGURATION, SubjectKind.PROPULSION_UNIT})


def _scope(value: object, where: str) -> None:
    if not isinstance(value, SubjectRef) or value.kind not in HARDWARE_SCOPES:
        raise EvidenceError(
            f"{where}: scope is an engine configuration or a propulsion unit, got {value!r}")


@dataclass(frozen=True, slots=True)
class Component:
    """A piece of hardware of one configuration or one propulsion unit.

    Attributes:
        scope: The configuration it belongs to, or the propulsion unit for
            hardware shared by several engines (a stage's common tanks).
        part_ids: Identifiers the documents use for it (finding numbers such
            as ``B19``, part numbers), when they name it that way.
    """

    component_id: str
    scope: SubjectRef
    component_type: ComponentType
    label: str
    ownership: Ownership
    part_ids: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.component_id, "component_id")
        _scope(self.scope, self.component_id)
        c.member(ComponentType, self.component_type, "component_type")
        c.text(self.label, "component label")
        c.member(Ownership, self.ownership, "ownership")
        c.texts(self.part_ids, "part_ids")
        c.plain(self.notes, "notes")
        _ownership_fits(self.component_type, self.ownership, self.component_id)


def _ownership_fits(kind: ComponentType, owner: Ownership, where: str) -> None:
    if (kind is ComponentType.AMBIENT_SINK) != (owner is Ownership.AMBIENT):
        raise EvidenceError(
            f"{where}: the ambient sink, and only it, is owned by AMBIENT "
            f"(got {kind.value} owned by {owner.value})")


@dataclass(frozen=True, slots=True)
class Schematic:
    """A figure that was viewed, and who drew it.

    Attributes:
        provenance: Who drew it (:class:`~.vocabulary.SchematicProvenance`).
            ROCKETFORGE_DERIVED_GRAPH describes graphs, not printed figures,
            and is refused here.
        drawn_by: The organisation that drew it, as far as the document says.
        legibility: What could and could not be read at the resolution viewed.
    """

    schematic_id: str
    source_id: str
    locator: str
    title_as_printed: str
    provenance: SchematicProvenance
    drawn_by: str
    legibility: str
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.schematic_id, "schematic_id")
        c.ident(self.source_id, "schematic source_id")
        c.text(self.locator, "schematic locator")
        c.text(self.title_as_printed, "schematic title")
        c.member(SchematicProvenance, self.provenance, "schematic provenance")
        if self.provenance is SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH:
            raise EvidenceError(
                f"{self.schematic_id}: a printed schematic is drawn by its author; "
                "ROCKETFORGE_DERIVED_GRAPH describes a graph, not a figure")
        c.text(self.drawn_by, "drawn_by")
        c.text(self.legibility, "legibility")
        c.plain(self.notes, "notes")


@dataclass(frozen=True, slots=True)
class TopologyNode:
    """One element of a graph.

    ``component_id`` links to a :class:`Component` when the element is
    identified hardware; a node without one is still typed and owned (a
    junction, a port) and its type and ownership must match the component when
    one is named.
    """

    node_id: str
    component_type: ComponentType
    label: str
    ownership: Ownership
    evidence: TopologyEvidence
    locator: str
    component_id: str | None = None

    def __post_init__(self) -> None:
        c.ident(self.node_id, "node_id")
        c.member(ComponentType, self.component_type, "node component_type")
        c.text(self.label, "node label")
        c.member(Ownership, self.ownership, "node ownership")
        c.member(TopologyEvidence, self.evidence, "node evidence")
        c.text(self.locator, f"node {self.node_id} locator")
        if self.component_id is not None:
            c.ident(self.component_id, "node component_id")
        _ownership_fits(self.component_type, self.ownership, self.node_id)


@dataclass(frozen=True, slots=True)
class TopologyEdge:
    """A directed relation between two nodes.

    Attributes:
        kind: What the edge carries (:class:`~.vocabulary.EdgeKind`).
        carrier: The fluid, for a fluid-flow edge ("LH2", "H2-rich gas"),
            where it is required; the medium, optionally, for control
            actuation or electrical power ("GN2" to valve pistons); ``None``
            for shaft, gear and linkage edges -- a shaft carries no fluid.
        role: What the edge is for, in words ("turbine drive", "nozzle bypass").
        split_group, merge_group: Edges leaving one node as parallel branches
            share a split group; edges joining share a merge group.
    """

    edge_id: str
    source: str
    target: str
    kind: EdgeKind
    carrier: str | None
    role: str
    evidence: TopologyEvidence
    locator: str
    split_group: str | None = None
    merge_group: str | None = None

    def __post_init__(self) -> None:
        c.ident(self.edge_id, "edge_id")
        c.ident(self.source, "edge source")
        c.ident(self.target, "edge target")
        if self.source == self.target:
            raise EvidenceError(f"{self.edge_id}: an edge joins two different nodes")
        c.member(EdgeKind, self.kind, "edge kind")
        if self.kind in FLUID_EDGE_KINDS:
            c.text(self.carrier, f"{self.edge_id}: the fluid a flow edge carries")
        elif self.kind in MEDIUM_EDGE_KINDS:
            c.optional_text(self.carrier, f"{self.edge_id}: the medium")
        elif self.carrier is not None:
            raise EvidenceError(f"{self.edge_id}: a {self.kind.value} edge carries no fluid")
        c.text(self.role, "edge role")
        c.member(TopologyEvidence, self.evidence, "edge evidence")
        c.text(self.locator, f"edge {self.edge_id} locator")
        for name in ("split_group", "merge_group"):
            value = getattr(self, name)
            if value is not None:
                c.ident(value, name)


@dataclass(frozen=True, slots=True)
class AbsenceStatement:
    """A source saying a component is not there. The only way a graph asserts absence."""

    component_type: ComponentType
    statement: str
    source_id: str
    locator: str

    def __post_init__(self) -> None:
        c.member(ComponentType, self.component_type, "absent component_type")
        c.text(self.statement, "absence statement (as printed)")
        c.ident(self.source_id, "absence source_id")
        c.text(self.locator, "absence locator")


@dataclass(frozen=True, slots=True)
class Completeness:
    """What a graph claims about its own completeness.

    ``declared_complete`` is a claim that needs a source; without one, a graph
    is incomplete and ``known_omissions`` lists what it is known to leave out.
    """

    declared_complete: bool
    known_omissions: tuple[str, ...]
    absences: tuple[AbsenceStatement, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.declared_complete, bool):
            raise EvidenceError("declared_complete must be true or false")
        c.texts(self.known_omissions, "known_omissions")
        c.instances(self.absences, AbsenceStatement, "absences")
        if self.declared_complete and self.known_omissions:
            raise EvidenceError("a graph declared complete lists no omissions")


@dataclass(frozen=True, slots=True)
class TopologyGraph:
    """A flow / mechanical / electrical topology of one configuration or propulsion unit.

    Attributes:
        scope: The configuration, or the propulsion unit for a stage- or
            system-level graph. A unit graph may use components of the unit and
            of the engine configurations it contains.
        provenance: How this graph was produced. A graph RocketForge builds
            from documents is ROCKETFORGE_DERIVED_GRAPH; the drawings it rests
            on carry their own provenance (see ``schematic_ids``).
        schematic_ids: Viewed schematics the graph rests on.
        text_source_ids: Sources whose text the graph rests on.
    """

    topology_id: str
    scope: SubjectRef
    label: str
    provenance: SchematicProvenance
    schematic_ids: tuple[str, ...]
    text_source_ids: tuple[str, ...]
    completeness: Completeness
    nodes: tuple[TopologyNode, ...]
    edges: tuple[TopologyEdge, ...]
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.topology_id, "topology_id")
        _scope(self.scope, self.topology_id)
        c.text(self.label, "topology label")
        c.member(SchematicProvenance, self.provenance, "topology provenance")
        c.idents(self.schematic_ids, "schematic_ids")
        c.idents(self.text_source_ids, "text_source_ids")
        if not self.schematic_ids and not self.text_source_ids:
            raise EvidenceError(f"{self.topology_id}: a graph rests on at least one schematic or text")
        if not isinstance(self.completeness, Completeness):
            raise EvidenceError("completeness must be a Completeness")
        c.instances(self.nodes, TopologyNode, "nodes")
        c.instances(self.edges, TopologyEdge, "edges")
        c.plain(self.notes, "notes")
        where = self.topology_id
        node_ids = [n.node_id for n in self.nodes]
        if len(set(node_ids)) != len(node_ids):
            raise EvidenceError(f"{where}: a node id is used twice")
        edge_ids = [e.edge_id for e in self.edges]
        if len(set(edge_ids)) != len(edge_ids):
            raise EvidenceError(f"{where}: an edge id is used twice")
        known = set(node_ids)
        for edge in self.edges:
            for end in (edge.source, edge.target):
                if end not in known:
                    raise EvidenceError(f"{where}: edge {edge.edge_id} references unknown node {end!r}")
        drawn = (TopologyEvidence.SHOWN_IN_SCHEMATIC, TopologyEvidence.DERIVED_FROM_BOTH)
        texted = (TopologyEvidence.REPORTED_IN_TEXT, TopologyEvidence.DERIVED_FROM_BOTH)
        for element in (*self.nodes, *self.edges):
            name = getattr(element, "node_id", None) or getattr(element, "edge_id")
            if element.evidence in drawn and not self.schematic_ids:
                raise EvidenceError(f"{where}: {name} is {element.evidence.value} but the graph cites no schematic")
            if element.evidence in texted and not self.text_source_ids:
                raise EvidenceError(f"{where}: {name} is {element.evidence.value} but the graph cites no text")

    def node(self, node_id: str) -> TopologyNode:
        for item in self.nodes:
            if item.node_id == node_id:
                return item
        raise KeyError(node_id)

    def edges_of_kind(self, kind: EdgeKind) -> tuple[TopologyEdge, ...]:
        return tuple(e for e in self.edges if e.kind is kind)

    def stated_absent(self, component_type: ComponentType) -> bool:
        """Whether a cited source says this component is not there.

        False does not mean present, and a type missing from ``nodes`` does
        not make this True: omission from a drawing is never absence.
        """
        return any(a.component_type is component_type for a in self.completeness.absences)
