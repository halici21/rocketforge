"""What one engine configuration's evidence can support, asked one use at a time.

Five questions, each answered for one configuration with a status, the
assertions and graphs the answer rests on, what is missing (``gaps``) and what
a reader must keep in mind (``caveats``). Never a score, never a rank, and
never a combination of the five.

* ``IDENTITY`` -- the configuration is a named build of a named variant and
  family, and at least one shipped statement is about it.
* ``ARCHITECTURE`` -- both propellants, and the power cycle or the feed
  system, are stated *for this configuration*.
* ``PERFORMANCE_REFERENCE`` -- thrust, specific impulse, chamber pressure,
  mixture ratio and nozzle area ratio are stated for it as operating values.
* ``TOPOLOGY`` -- a graph of it (or of a propulsion unit that contains it)
  exists; SUPPORTED only when nothing stops it counting as an original
  drawing of the hardware. Every graph says what it leaves out.
* ``REGRESSION_CANDIDATE`` -- those five quantities, the running ones at one
  operating point, with a stated environment for thrust and specific impulse
  and none printed as an average or an approximation, pass
  :func:`~.corpus.regression_blockers`. SUPPORTED means *eligible to be
  proposed* as a regression reference. No regression is accepted, locked or
  run here: that is a separate, deliberate decision with a comparison case.

What counts: an assertion whose subject is the configuration, one of its
operating points, or a component of it -- never its variant or family. A
statement printed for "the J-2" or "the AJ10-137" is reported as context (a
caveat naming it) and supports nothing about a particular configuration. Only
admitted, REPORTED or DIGITISED values count; an INFERRED one never does.
Nothing here solves, converts or recommends.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from ..values import EvidenceError
from .admission import SHIPPED_STATUSES
from .assertions import Assertion
from .corpus import EngineEvidenceCorpus, original_topology_blockers, regression_blockers
from .identity import SubjectRef
from .topology import TopologyGraph
from .vocabulary import (
    OPERATING_VALUE_KINDS,
    Admissibility,
    Environment,
    IspBasis,
    MixtureRatioBasis,
    PressureBasis,
    PressureStation,
    SubjectKind,
)

__all__ = [
    "Capability", "CapabilityStatus", "CapabilityResult", "PERFORMANCE_QUANTITIES",
    "ARCHITECTURE_FIELDS", "evaluate_capability", "configuration_capabilities",
    "configuration_assertions", "context_assertions", "configuration_topologies",
]


class Capability(StrEnum):
    IDENTITY = "IDENTITY"
    ARCHITECTURE = "ARCHITECTURE"
    PERFORMANCE_REFERENCE = "PERFORMANCE_REFERENCE"
    TOPOLOGY = "TOPOLOGY"
    REGRESSION_CANDIDATE = "REGRESSION_CANDIDATE"


class CapabilityStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    NOT_SUPPORTED = "NOT_SUPPORTED"


#: The quantities a performance reference needs, by the field paths that hold them.
PERFORMANCE_QUANTITIES: dict[str, tuple[str, ...]] = {
    "thrust": ("performance.thrust", "performance.thrust_vac", "performance.thrust_sl"),
    "specific_impulse": ("performance.specific_impulse", "performance.specific_impulse_vac",
                         "performance.specific_impulse_sl"),
    "chamber_pressure": ("performance.chamber_pressure",),
    "mixture_ratio": ("propellants.mixture_ratio",),
    "area_ratio": ("nozzle.area_ratio",),
}

#: Quantities stated at an operating point; the area ratio is geometry.
_RUNNING = ("thrust", "specific_impulse", "chamber_pressure", "mixture_ratio")

#: The architecture statements, by field path.
ARCHITECTURE_FIELDS: dict[str, str] = {
    "oxidizer": "propellants.oxidizer",
    "fuel": "propellants.fuel",
    "cycle": "architecture.cycle",
    "feed": "architecture.feed",
}


@dataclass(frozen=True, slots=True)
class CapabilityResult:
    """One answer: a status, what it rests on, what is missing, and what to keep in mind."""

    capability: Capability
    configuration_id: str
    status: CapabilityStatus
    assertion_ids: tuple[str, ...]
    topology_ids: tuple[str, ...]
    gaps: tuple[str, ...]
    caveats: tuple[str, ...]


# ------------------------------------------------------------------ scoping


def _require(corpus: EngineEvidenceCorpus, configuration_id: str) -> None:
    if not corpus.resolves(SubjectRef(SubjectKind.CONFIGURATION, configuration_id)):
        raise EvidenceError(f"unknown configuration {configuration_id!r}")


def configuration_assertions(corpus: EngineEvidenceCorpus, configuration_id: str) -> tuple[Assertion, ...]:
    """Assertions about this configuration, its operating points or its components. Nothing inherited."""
    _require(corpus, configuration_id)
    return tuple(a for a in corpus.assertions if corpus.configuration_of(a.subject) == configuration_id)


def context_assertions(corpus: EngineEvidenceCorpus, configuration_id: str) -> tuple[Assertion, ...]:
    """Statements about the configuration's variant or family: context, never its values."""
    _require(corpus, configuration_id)
    config = next(c for c in corpus.configurations if c.configuration_id == configuration_id)
    variant = next(v for v in corpus.variants if v.variant_id == config.variant_id)
    above = {SubjectRef(SubjectKind.VARIANT, variant.variant_id),
             SubjectRef(SubjectKind.FAMILY, variant.family_id)}
    return tuple(a for a in corpus.assertions if a.subject in above)


def _units_containing(corpus: EngineEvidenceCorpus, configuration_id: str) -> set[str]:
    target = SubjectRef(SubjectKind.CONFIGURATION, configuration_id)
    members = {u.unit_id: {m.member for m in u.members} for u in corpus.units}
    found: set[str] = set()
    changed = True
    while changed:
        changed = False
        for unit_id, refs in members.items():
            if unit_id in found:
                continue
            if target in refs or any(SubjectRef(SubjectKind.PROPULSION_UNIT, u) in refs for u in found):
                found.add(unit_id)
                changed = True
    return found


def configuration_topologies(corpus: EngineEvidenceCorpus, configuration_id: str) -> tuple[TopologyGraph, ...]:
    """Graphs of this configuration, and of propulsion units that contain it."""
    _require(corpus, configuration_id)
    units = _units_containing(corpus, configuration_id)
    return tuple(t for t in corpus.topologies
                 if (t.scope.kind is SubjectKind.CONFIGURATION and t.scope.id == configuration_id)
                 or (t.scope.kind is SubjectKind.PROPULSION_UNIT and t.scope.id in units))


def _counts(a: Assertion) -> bool:
    return (a.admissibility is Admissibility.ADMITTED and not a.is_missing
            and a.status in SHIPPED_STATUSES)


def _result(capability, configuration_id, status, ids=(), topologies=(), gaps=(), caveats=()):
    return CapabilityResult(capability, configuration_id, status, tuple(ids), tuple(topologies),
                            tuple(gaps), tuple(dict.fromkeys(caveats)))


#: Context fields that speak to an architecture field (a propellant pair printed together).
_RELATED = {"propellants.oxidizer": ("propellants.combination",),
            "propellants.fuel": ("propellants.combination",)}


def _context_note(context: tuple[Assertion, ...], field_path: str) -> list[str]:
    paths = (field_path, *_RELATED.get(field_path, ()))
    return [f"{a.assertion_id} states {a.field_path} for {a.subject.kind.value.lower()} {a.subject.id}; "
            "not applied to this configuration" for a in context if a.field_path in paths]


# ------------------------------------------------------------------ the five questions


def _identity(corpus, cfg) -> CapabilityResult:
    config = next(c for c in corpus.configurations if c.configuration_id == cfg)
    own = [a for a in configuration_assertions(corpus, cfg) if _counts(a)]
    caveats = []
    if not isinstance(config.effective, str):
        caveats.append(f"when this configuration applies is not stated ({config.effective.reason.value})")
    status = CapabilityStatus.SUPPORTED if own else CapabilityStatus.NOT_SUPPORTED
    gaps = [] if own else ["no shipped statement is about this configuration"]
    return _result(Capability.IDENTITY, cfg, status, [a.assertion_id for a in own], gaps=gaps, caveats=caveats)


def _architecture(corpus, cfg) -> CapabilityResult:
    own = [a for a in configuration_assertions(corpus, cfg) if _counts(a)]
    context = context_assertions(corpus, cfg)
    found = {name: [a for a in own if a.field_path == path] for name, path in ARCHITECTURE_FIELDS.items()}
    gaps, caveats = [], []
    for name in ("oxidizer", "fuel"):
        if not found[name]:
            gaps.append(f"{ARCHITECTURE_FIELDS[name]} is not stated for this configuration")
            caveats += _context_note(context, ARCHITECTURE_FIELDS[name])
    if not found["cycle"] and not found["feed"]:
        gaps.append("neither architecture.cycle nor architecture.feed is stated for this configuration")
    for name in ("cycle", "feed"):
        if not found[name]:
            caveats += _context_note(context, ARCHITECTURE_FIELDS[name])
    ids = [a.assertion_id for name in ARCHITECTURE_FIELDS for a in found[name]]
    if not gaps:
        status = CapabilityStatus.SUPPORTED
    else:
        status = CapabilityStatus.PARTIAL if ids else CapabilityStatus.NOT_SUPPORTED
    return _result(Capability.ARCHITECTURE, cfg, status, ids, gaps=gaps, caveats=caveats)


def _performance(corpus, cfg):
    """Operating-value assertions per quantity, plus the caveats about them."""
    own = [a for a in configuration_assertions(corpus, cfg) if _counts(a)]
    by_quantity: dict[str, list[Assertion]] = defaultdict(list)
    caveats: list[str] = []
    for a in own:
        quantity = next((q for q, paths in PERFORMANCE_QUANTITIES.items() if a.field_path in paths), None)
        if quantity is None or not a.is_quantity:
            continue
        if a.value_kind not in OPERATING_VALUE_KINDS:
            caveats.append(f"{a.assertion_id}: value kind {a.value_kind.value} is not an operating value; not used")
            continue
        by_quantity[quantity].append(a)
    for quantity, claims in by_quantity.items():
        for a in claims:
            caveats += _condition_caveats(a)
        if len({_magnitude(a) for a in claims}) > 1:
            caveats.append(f"{quantity}: the claims differ ({', '.join(a.assertion_id for a in claims)})")
    return by_quantity, caveats


def _magnitude(a: Assertion):
    v = a.value
    return (v.low, v.high) if hasattr(v, "low") else (v.value, a.unit_as_printed)  # type: ignore[union-attr]


def _condition_caveats(a: Assertion) -> list[str]:
    c, aid, out = a.conditions, a.assertion_id, []
    if c.pressure_station is PressureStation.UNKNOWN:
        out.append(f"{aid}: chamber-pressure measurement station not stated by the source")
    if c.pressure_basis is PressureBasis.UNKNOWN:
        out.append(f"{aid}: pressure basis (absolute or gauge) not stated by the source")
    if c.environment is Environment.UNKNOWN:
        out.append(f"{aid}: environment (vacuum or sea level) not stated by the source")
    if c.isp_basis is IspBasis.UNKNOWN:
        out.append(f"{aid}: specific-impulse basis (engine or thrust chamber) not stated by the source")
    if c.mixture_ratio_basis is MixtureRatioBasis.UNKNOWN:
        out.append(f"{aid}: which flow the mixture ratio describes is not stated by the source")
    if a.value_kind.value in ("AVERAGE", "APPROXIMATE"):
        out.append(f"{aid}: printed as {a.value_kind.value.lower()}")
    return out


def _performance_reference(corpus, cfg) -> CapabilityResult:
    by_quantity, caveats = _performance(corpus, cfg)
    gaps = [f"{q}: no shipped operating value for this configuration"
            for q in PERFORMANCE_QUANTITIES if not by_quantity.get(q)]
    ids = [a.assertion_id for q in PERFORMANCE_QUANTITIES for a in by_quantity.get(q, ())]
    if not gaps:
        status = CapabilityStatus.SUPPORTED
    else:
        status = CapabilityStatus.PARTIAL if ids else CapabilityStatus.NOT_SUPPORTED
    return _result(Capability.PERFORMANCE_REFERENCE, cfg, status, ids, gaps=gaps, caveats=caveats)


def _topology(corpus, cfg) -> CapabilityResult:
    graphs = configuration_topologies(corpus, cfg)
    if not graphs:
        return _result(Capability.TOPOLOGY, cfg, CapabilityStatus.NOT_SUPPORTED,
                       gaps=["no topology graph of this configuration"])
    gaps, caveats, original = [], [], False
    for g in graphs:
        blockers = original_topology_blockers(corpus, g.topology_id)
        gaps += [f"{g.topology_id}: {b}" for b in blockers]
        original = original or not blockers
        if not g.completeness.declared_complete:
            omitted = "; ".join(g.completeness.known_omissions) or "none listed"
            caveats.append(f"{g.topology_id} is incomplete by its own account; known omissions: {omitted}")
        if g.scope.kind is SubjectKind.PROPULSION_UNIT:
            caveats.append(f"{g.topology_id} is a graph of propulsion unit {g.scope.id}, which contains this configuration")
    status = CapabilityStatus.SUPPORTED if original else CapabilityStatus.PARTIAL
    return _result(Capability.TOPOLOGY, cfg, status, topologies=[g.topology_id for g in graphs],
                   gaps=gaps, caveats=caveats)


def _regression_candidate(corpus, cfg) -> CapabilityResult:
    by_quantity, caveats = _performance(corpus, cfg)
    gaps = [f"{q}: no shipped operating value for this configuration"
            for q in PERFORMANCE_QUANTITIES if not by_quantity.get(q)]
    ids = [a.assertion_id for q in PERFORMANCE_QUANTITIES for a in by_quantity.get(q, ())]
    for q in PERFORMANCE_QUANTITIES:
        claims = by_quantity.get(q, ())
        if len({_magnitude(a) for a in claims}) > 1:
            gaps.append(f"{q}: the claims differ, so there is no single reference value")
    points = {a.operating_point_id for q in _RUNNING for a in by_quantity.get(q, ())}
    if points and (len(points) != 1 or None in points):
        gaps.append("thrust, specific impulse, chamber pressure and mixture ratio are not all "
                    "stated at one operating point")
    for q in ("thrust", "specific_impulse"):
        for a in by_quantity.get(q, ()):
            if a.conditions.environment is Environment.UNKNOWN:
                gaps.append(f"{a.assertion_id}: {q} with no stated environment cannot be compared "
                            "with an ideal-performance case")
    for q in _RUNNING:
        for a in by_quantity.get(q, ()):
            if a.value_kind.value in ("AVERAGE", "APPROXIMATE"):
                gaps.append(f"{a.assertion_id}: {q} is printed as {a.value_kind.value.lower()}, "
                            "not as one operating value")
    if ids:
        gaps += list(regression_blockers(corpus, ids))
    status = CapabilityStatus.NOT_SUPPORTED if gaps else CapabilityStatus.SUPPORTED
    caveats = caveats + ["eligibility only: no regression is accepted, locked or run from this record"]
    return _result(Capability.REGRESSION_CANDIDATE, cfg, status, ids, gaps=gaps, caveats=caveats)


_EVALUATORS = {
    Capability.IDENTITY: _identity,
    Capability.ARCHITECTURE: _architecture,
    Capability.PERFORMANCE_REFERENCE: _performance_reference,
    Capability.TOPOLOGY: _topology,
    Capability.REGRESSION_CANDIDATE: _regression_candidate,
}


def evaluate_capability(corpus: EngineEvidenceCorpus, configuration_id: str,
                        capability: Capability) -> CapabilityResult:
    """Answer one question about one configuration."""
    _require(corpus, configuration_id)
    return _EVALUATORS[Capability(capability)](corpus, configuration_id)


def configuration_capabilities(corpus: EngineEvidenceCorpus,
                               configuration_id: str) -> tuple[CapabilityResult, ...]:
    """All five answers for one configuration, in a fixed order."""
    return tuple(evaluate_capability(corpus, configuration_id, c) for c in Capability)
