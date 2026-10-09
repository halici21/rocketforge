"""The engine-evidence corpus: every record, cross-checked, and what it can support.

:class:`EngineEvidenceCorpus` holds one consistent set of sources, identities,
components, schematics, topologies, assertions and conflicts. Constructing one
runs every cross-reference check; a corpus that exists is a corpus whose
references resolve.

What a record can support is answered per use, never as a score:

* :func:`regression_blockers` -- why a set of assertions cannot serve as a
  regression reference (empty when nothing blocks);
* :func:`original_topology_blockers` -- why a graph cannot count as an
  original drawing of the hardware.

Lookups return exactly what was recorded for a subject. There is no lookup
that walks the identity hierarchy, so no value is ever inherited from a
family or variant by a configuration, or the other way round.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from ..values import EvidenceError, Missing, MissingReason, ShippingPolicy, ValueStatus
from . import _checks as c
from .assertions import Assertion
from .conflicts import Conflict
from .identity import (
    Alias,
    EngineConfiguration,
    EngineFamily,
    EngineVariant,
    LineageEdge,
    OperatingPoint,
    PropulsionUnit,
    SubjectRef,
)
from .sources import EngineSource
from .topology import Component, Schematic, TopologyGraph
from .vocabulary import (
    OPERATING_VALUE_KINDS,
    ORIGINAL_PROVENANCES,
    Admissibility,
    ConflictResolution,
    SourceAccess,
    SourceAuthority,
    SubjectKind,
    TopologyEvidence,
)

__all__ = ["EngineEvidenceCorpus", "regression_blockers", "original_topology_blockers",
           "REGRESSION_AUTHORITIES", "BLOCKING_RESOLUTIONS"]

#: Only agency/manufacturer and peer-reviewed sources can anchor a regression.
REGRESSION_AUTHORITIES = frozenset({SourceAuthority.A, SourceAuthority.B})

#: Conflict states that block a regression on the assertions they involve.
BLOCKING_RESOLUTIONS = frozenset({ConflictResolution.UNRESOLVED,
                                  ConflictResolution.PARTIALLY_RESOLVED})

#: A value about hardware running belongs to a configuration, an operating
#: point, a component or a propulsion unit -- never to a family or a bare variant.
_SCOPED_SUBJECTS = frozenset({SubjectKind.CONFIGURATION, SubjectKind.OPERATING_POINT,
                              SubjectKind.COMPONENT, SubjectKind.PROPULSION_UNIT})

#: Access states from which a value (not a Missing) can be transcribed.
_VALUE_ACCESS = frozenset({SourceAccess.OPENED, SourceAccess.SEARCH_RESULT_ONLY})


def _index(items: Iterable, key: str, what: str) -> dict:
    out: dict = {}
    for item in items:
        k = getattr(item, key)
        if k in out:
            raise EvidenceError(f"duplicate {what} id {k!r}")
        out[k] = item
    return out


def _configuration_of(subjects: dict, ref: SubjectRef) -> str | None:
    if ref.kind is SubjectKind.CONFIGURATION:
        return ref.id
    if ref.kind is SubjectKind.OPERATING_POINT:
        return subjects[ref.kind][ref.id].configuration_id
    if ref.kind is SubjectKind.COMPONENT:
        scope = subjects[ref.kind][ref.id].scope
        return scope.id if scope.kind is SubjectKind.CONFIGURATION else None
    return None


_DASHES = re.compile(r"[\u2010-\u2015\u2212\s_]+")


def _name_key(name: str) -> str:
    """A name as compared for clashes: NFKC, case-folded, dashes/spaces/underscores folded to '-'."""
    return _DASHES.sub("-", unicodedata.normalize("NFKC", name).casefold()).strip("-")


def _unit_contents(units: dict) -> dict[str, set[SubjectRef]]:
    """Every configuration, variant and unit a propulsion unit contains, transitively."""
    out: dict[str, set[SubjectRef]] = {}

    def walk(unit_id: str) -> set[SubjectRef]:
        if unit_id not in out:
            out[unit_id] = set()
            for m in units[unit_id].members:
                out[unit_id].add(m.member)
                if m.member.kind is SubjectKind.PROPULSION_UNIT and m.member.id in units:
                    out[unit_id] |= walk(m.member.id)
        return out[unit_id]

    for unit_id in units:
        walk(unit_id)
    return out


def _acyclic(edges: dict[str, set[str]], what: str) -> None:
    state: dict[str, int] = {}

    def visit(node: str, path: list[str]) -> None:
        state[node] = 1
        for nxt in edges.get(node, ()):
            if state.get(nxt) == 1:
                raise EvidenceError(f"{what} forms a loop: {' -> '.join(path + [node, nxt])}")
            if state.get(nxt) is None:
                visit(nxt, path + [node])
        state[node] = 2

    for node in list(edges):
        if node not in state:
            visit(node, [])


@dataclass(frozen=True, slots=True)
class EngineEvidenceCorpus:
    """One cross-checked set of reference-engine evidence."""

    sources: tuple[EngineSource, ...]
    families: tuple[EngineFamily, ...]
    variants: tuple[EngineVariant, ...]
    configurations: tuple[EngineConfiguration, ...]
    operating_points: tuple[OperatingPoint, ...]
    units: tuple[PropulsionUnit, ...]
    aliases: tuple[Alias, ...]
    lineage: tuple[LineageEdge, ...]
    components: tuple[Component, ...]
    schematics: tuple[Schematic, ...]
    topologies: tuple[TopologyGraph, ...]
    assertions: tuple[Assertion, ...]
    conflicts: tuple[Conflict, ...]

    def __post_init__(self) -> None:
        for name, kind in (("sources", EngineSource), ("families", EngineFamily),
                           ("variants", EngineVariant), ("configurations", EngineConfiguration),
                           ("operating_points", OperatingPoint), ("units", PropulsionUnit),
                           ("aliases", Alias), ("lineage", LineageEdge), ("components", Component),
                           ("schematics", Schematic), ("topologies", TopologyGraph),
                           ("assertions", Assertion), ("conflicts", Conflict)):
            c.instances(getattr(self, name), kind, name)
        self._check()

    # ------------------------------------------------------------ indexes

    @property
    def source_map(self) -> dict[str, EngineSource]:
        return {s.source_id: s for s in self.sources}

    @property
    def assertion_map(self) -> dict[str, Assertion]:
        return {a.assertion_id: a for a in self.assertions}

    def _subjects(self) -> dict[SubjectKind, dict]:
        return {
            SubjectKind.FAMILY: {x.family_id: x for x in self.families},
            SubjectKind.VARIANT: {x.variant_id: x for x in self.variants},
            SubjectKind.CONFIGURATION: {x.configuration_id: x for x in self.configurations},
            SubjectKind.OPERATING_POINT: {x.operating_point_id: x for x in self.operating_points},
            SubjectKind.PROPULSION_UNIT: {x.unit_id: x for x in self.units},
            SubjectKind.COMPONENT: {x.component_id: x for x in self.components},
        }

    def resolves(self, ref: SubjectRef) -> bool:
        return ref.id in self._subjects()[ref.kind]

    def configuration_of(self, ref: SubjectRef) -> str | None:
        """The configuration a subject belongs to, or None above configuration level."""
        return _configuration_of(self._subjects(), ref)

    # ------------------------------------------------------------ queries

    def assertions_about(self, subject: SubjectRef) -> tuple[Assertion, ...]:
        """Exactly the assertions recorded for this subject. Nothing is inherited."""
        return tuple(a for a in self.assertions if a.subject == subject)

    def conflicts_involving(self, assertion_id: str) -> tuple[Conflict, ...]:
        return tuple(x for x in self.conflicts if assertion_id in x.assertion_ids)

    def is_intra_document(self, conflict: Conflict) -> bool:
        """Whether every competing claim was read in the same document."""
        amap = self.assertion_map
        return len({amap[i].source_id for i in conflict.assertion_ids}) == 1

    def duplicate_document_groups(self) -> tuple[tuple[str, ...], ...]:
        """Source ids sharing one content hash, by hash. Filenames are never compared."""
        groups: dict[str, list[str]] = defaultdict(list)
        for s in self.sources:
            if s.content_sha256 is not None:
                groups[s.content_sha256].append(s.source_id)
        return tuple(tuple(ids) for ids in groups.values() if len(ids) > 1)

    # ------------------------------------------------------------ checks

    def _check(self) -> None:
        sources = _index(self.sources, "source_id", "source")
        families = _index(self.families, "family_id", "family")
        variants = _index(self.variants, "variant_id", "variant")
        configs = _index(self.configurations, "configuration_id", "configuration")
        points = _index(self.operating_points, "operating_point_id", "operating point")
        units = _index(self.units, "unit_id", "propulsion unit")
        _index(self.aliases, "alias_id", "alias")
        _index(self.lineage, "lineage_id", "lineage edge")
        components = _index(self.components, "component_id", "component")
        schematics = _index(self.schematics, "schematic_id", "schematic")
        _index(self.topologies, "topology_id", "topology")
        assertions = _index(self.assertions, "assertion_id", "assertion")
        _index(self.conflicts, "conflict_id", "conflict")

        subjects = self._subjects()

        def need(table: dict, key: str, what: str, where: str) -> None:
            if key not in table:
                raise EvidenceError(f"{where}: unknown {what} {key!r}")

        def need_ref(ref: SubjectRef, where: str) -> None:
            if ref.id not in subjects[ref.kind]:
                raise EvidenceError(f"{where}: unknown {ref.kind.value.lower()} {ref.id!r}")

        # sources and duplicate documents
        for s in self.sources:
            if s.same_document_as is not None:
                need(sources, s.same_document_as, "source", f"{s.source_id}.same_document_as")
                other = sources[s.same_document_as]
                if s.content_sha256 is None or s.content_sha256 != other.content_sha256:
                    raise EvidenceError(
                        f"{s.source_id} says it is the same document as {other.source_id}, "
                        "but their content hashes differ or are not recorded")
                if other.same_document_as is not None:
                    raise EvidenceError(
                        f"{s.source_id}: name the canonical record, not another duplicate "
                        f"({other.source_id} is itself a duplicate)")
        for group in self.duplicate_document_groups():
            canonical = [sid for sid in group if sources[sid].same_document_as is None]
            if len(canonical) != 1:
                raise EvidenceError(
                    f"sources {list(group)} hold the same file; all but one must name the "
                    "canonical record in same_document_as")

        # identity hierarchy
        for v in self.variants:
            need(families, v.family_id, "family", v.variant_id)
        for x in self.configurations:
            need(variants, x.variant_id, "variant", x.configuration_id)
        for p in self.operating_points:
            need(configs, p.configuration_id, "configuration", p.operating_point_id)
        for comp in self.components:
            need_ref(comp.scope, comp.component_id)
        contains: dict[str, set[str]] = defaultdict(set)
        for u in self.units:
            for m in u.members:
                need_ref(m.member, f"{u.unit_id} member")
                if m.member.kind is SubjectKind.PROPULSION_UNIT:
                    contains[u.unit_id].add(m.member.id)
        _acyclic(contains, "propulsion-unit membership")
        contents = _unit_contents(units)

        # aliases: names point at identities; a shared name is flagged ambiguous
        names: dict[str, set[SubjectRef]] = defaultdict(set)
        for a in self.aliases:
            need_ref(a.target, a.alias_id)
            for sid in a.source_ids:
                need(sources, sid, "source", a.alias_id)
            names[_name_key(a.name)].add(a.target)
        for v in self.variants:
            names[_name_key(v.designation)].add(SubjectRef(SubjectKind.VARIANT, v.variant_id))
        for u in self.units:
            names[_name_key(u.designation)].add(SubjectRef(SubjectKind.PROPULSION_UNIT, u.unit_id))
        for f in self.families:
            names[_name_key(f.name)].add(SubjectRef(SubjectKind.FAMILY, f.family_id))
        for a in self.aliases:
            if len(names[_name_key(a.name)]) > 1 and not a.ambiguous:
                raise EvidenceError(
                    f"{a.alias_id}: the name {a.name!r} also names another identity; mark the "
                    "alias ambiguous")

        # lineage: resolvable and acyclic
        lineage_graph: dict[str, set[str]] = defaultdict(set)
        for edge in self.lineage:
            need_ref(edge.source, edge.lineage_id)
            need_ref(edge.target, edge.lineage_id)
            for sid in edge.source_ids:
                need(sources, sid, "source", edge.lineage_id)
            lineage_graph[f"{edge.source.kind}:{edge.source.id}"].add(
                f"{edge.target.kind}:{edge.target.id}")
        _acyclic(lineage_graph, "lineage")

        # schematics were viewed in opened documents
        for sch in self.schematics:
            need(sources, sch.source_id, "source", sch.schematic_id)
            if not sources[sch.source_id].opened:
                raise EvidenceError(f"{sch.schematic_id}: a schematic is recorded only from an opened document")

        # topologies
        for t in self.topologies:
            where = t.topology_id
            need_ref(t.scope, where)
            for sid in t.schematic_ids:
                need(schematics, sid, "schematic", where)
            for sid in t.text_source_ids:
                need(sources, sid, "source", where)
                if not sources[sid].opened:
                    raise EvidenceError(f"{where}: text source {sid} was not opened")
            for absence in t.completeness.absences:
                need(sources, absence.source_id, "source", f"{where} absence")
                if not sources[absence.source_id].opened:
                    raise EvidenceError(f"{where}: an absence statement needs an opened source")
            for node in t.nodes:
                if node.component_id is None:
                    continue
                need(components, node.component_id, "component", f"{where}.{node.node_id}")
                comp = components[node.component_id]
                inside = comp.scope == t.scope or (
                    t.scope.kind is SubjectKind.PROPULSION_UNIT
                    and comp.scope in contents.get(t.scope.id, set()))
                if not inside:
                    raise EvidenceError(
                        f"{where}.{node.node_id}: component {comp.component_id} belongs to "
                        f"{comp.scope.kind.value.lower()} {comp.scope.id}, outside this graph's scope")
                if comp.component_type is not node.component_type or comp.ownership is not node.ownership:
                    raise EvidenceError(
                        f"{where}.{node.node_id}: type/ownership disagree with component {comp.component_id}")

        # assertions
        derived_from: dict[str, set[str]] = defaultdict(set)
        for a in self.assertions:
            where = a.assertion_id
            need_ref(a.subject, where)
            need(sources, a.source_id, "source", where)
            source = sources[a.source_id]
            if a.access is not source.access:
                raise EvidenceError(
                    f"{where}: records access {a.access.value} but {source.source_id} is {source.access.value}")
            self._check_value_against_source(a, source)
            if a.first_stated_by is not None:
                need(sources, a.first_stated_by, "source", f"{where}.first_stated_by")
            if a.schematic_id is not None:
                need(schematics, a.schematic_id, "schematic", where)
                if schematics[a.schematic_id].source_id != a.source_id:
                    raise EvidenceError(f"{where}: read from a schematic in another document")
            if a.operating_point_id is not None:
                need(points, a.operating_point_id, "operating point", where)
                if a.subject.kind is SubjectKind.OPERATING_POINT:
                    raise EvidenceError(f"{where}: the subject is already an operating point")
                config = _configuration_of(subjects, a.subject)
                if config is None:
                    raise EvidenceError(
                        f"{where}: an operating point belongs to a configuration; a "
                        f"{a.subject.kind.value.lower()} subject cannot take one")
                if points[a.operating_point_id].configuration_id != config:
                    raise EvidenceError(f"{where}: operating point of another configuration")
            if a.derivation is not None:
                for i in a.derivation.input_assertion_ids:
                    need(assertions, i, "assertion", f"{where}.derivation")
                derived_from[where] |= set(a.derivation.input_assertion_ids)
        _acyclic(derived_from, "derivation")

        # conflicts
        for x in self.conflicts:
            for i in x.assertion_ids:
                need(assertions, i, "assertion", x.conflict_id)

    @staticmethod
    def _check_value_against_source(a: Assertion, source: EngineSource) -> None:
        where = a.assertion_id
        value = a.value
        if source.access is SourceAccess.ACCESS_BLOCKED and not (
                isinstance(value, Missing) and value.reason is MissingReason.ACCESS_BLOCKED):
            raise EvidenceError(
                f"{where}: {source.source_id} could not be opened; the only thing it can supply is "
                "Missing(ACCESS_BLOCKED)")
        if isinstance(value, Missing):
            if value.reason is MissingReason.ACCESS_BLOCKED and source.access is not SourceAccess.ACCESS_BLOCKED:
                raise EvidenceError(f"{where}: ACCESS_BLOCKED cites a source that was reached")
            if value.reason is MissingReason.NOT_REPORTED and source.access is not SourceAccess.OPENED:
                raise EvidenceError(f"{where}: 'not reported' can only be said of a document that was read")
            if value.reason is MissingReason.WITHHELD_RIGHTS and source.rights.values is ShippingPolicy.VALUES_WITH_ATTRIBUTION:
                raise EvidenceError(f"{where}: withheld for rights, but the source's values may ship")
            return
        if source.access not in _VALUE_ACCESS:
            raise EvidenceError(
                f"{where}: a value cannot be transcribed from {source.source_id}, whose access is "
                f"{source.access.value}")


def regression_blockers(corpus: EngineEvidenceCorpus, assertion_ids: Iterable[str]) -> tuple[str, ...]:
    """Why these assertions cannot together serve as a regression reference.

    Empty means nothing here blocks it; it does not make the set a locked
    regression -- that is a separate, deliberate decision with a comparison case.
    """
    amap, smap = corpus.assertion_map, corpus.source_map
    schematics = {s.schematic_id: s for s in corpus.schematics}
    out: list[str] = []
    for aid in dict.fromkeys(assertion_ids):
        if aid not in amap:
            raise EvidenceError(f"unknown assertion {aid!r}")
        a = amap[aid]
        s = smap[a.source_id]
        if a.admissibility is not Admissibility.ADMITTED:
            out.append(f"{aid}: not admitted ({a.admissibility.value})")
        if a.is_missing:
            out.append(f"{aid}: no value (Missing {a.value.reason.value})")  # type: ignore[union-attr]
        if a.status is ValueStatus.INFERRED:
            out.append(f"{aid}: INFERRED, never a basis for a verdict")
        if a.value_kind not in OPERATING_VALUE_KINDS:
            out.append(f"{aid}: value kind {a.value_kind.value} is not an operating value")
        if a.subject.kind not in _SCOPED_SUBJECTS:
            out.append(f"{aid}: stated for a {a.subject.kind.value.lower()}, not a configuration")
        if s.access is not SourceAccess.OPENED:
            out.append(f"{aid}: source {s.source_id} was not opened ({s.access.value})")
        if s.authority not in REGRESSION_AUTHORITIES:
            out.append(f"{aid}: source authority {s.authority.value}")
        if s.rights.values is not ShippingPolicy.VALUES_WITH_ATTRIBUTION:
            out.append(f"{aid}: values of {s.source_id} may not ship ({s.rights.values.value})")
        if s.rights.unresolved:
            out.append(f"{aid}: rights of {s.source_id} not settled ({s.rights.review.value})")
        if a.first_stated_by is not None:
            origin = smap[a.first_stated_by]
            if origin.authority not in REGRESSION_AUTHORITIES:
                out.append(f"{aid}: first stated by {origin.source_id}, authority {origin.authority.value}")
        if a.schematic_id is not None:
            drawn = schematics[a.schematic_id].provenance
            if drawn not in ORIGINAL_PROVENANCES:
                out.append(f"{aid}: read from schematic {a.schematic_id}, which is {drawn.value}")
        for x in corpus.conflicts_involving(aid):
            if x.resolution in BLOCKING_RESOLUTIONS:
                out.append(f"{aid}: in {x.resolution.value} conflict {x.conflict_id}")
            elif x.resolution is ConflictResolution.RESOLVED and x.preferred_assertion_id != aid:
                out.append(f"{aid}: not the claim that stands in {x.conflict_id}")
    return tuple(out)


def original_topology_blockers(corpus: EngineEvidenceCorpus, topology_id: str) -> tuple[str, ...]:
    """Why a graph cannot count as an original drawing of the hardware's topology."""
    graphs = {t.topology_id: t for t in corpus.topologies}
    if topology_id not in graphs:
        raise EvidenceError(f"unknown topology {topology_id!r}")
    graph = graphs[topology_id]
    sch = {s.schematic_id: s for s in corpus.schematics}
    out: list[str] = []
    if not graph.schematic_ids:
        out.append("rests on text only; no viewed schematic")
    for sid in graph.schematic_ids:
        if sch[sid].provenance not in ORIGINAL_PROVENANCES:
            out.append(f"schematic {sid} is {sch[sid].provenance.value}")
    inferred = [e for e in (*graph.nodes, *graph.edges) if e.evidence is TopologyEvidence.INFERRED]
    if inferred:
        out.append(f"{len(inferred)} element(s) are INFERRED")
    return tuple(out)
