"""Identity: what an assertion can be about.

::

    EngineFamily -> EngineVariant -> EngineConfiguration -> OperatingPoint

plus :class:`PropulsionUnit` for things with engine-like names that are not
engine variants (an engine module, a multi-engine propulsion system, a stage's
propulsion), :class:`Alias` for other names, and :class:`LineageEdge` for
derivation, uprating and renaming.

The hierarchy carries **no values**. Nothing here or in the corpus resolves a
number "up" or "down" it: a chamber pressure stated for a configuration is not
a chamber pressure of its variant, and a value printed for "the RL10" stays a
family-level statement. That is what lets one variant hold several rated
configurations (SSME Block IIA and Block II; J-2 225K and 230K) without any of
them inheriting another's numbers.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..values import EvidenceError, Missing
from . import _checks as c
from .vocabulary import AliasKind, LineageKind, PropulsionUnitKind, SubjectKind

__all__ = [
    "SubjectRef", "EngineFamily", "EngineVariant", "EngineConfiguration",
    "OperatingPoint", "UnitMember", "PropulsionUnit", "Alias", "LineageEdge",
]


@dataclass(frozen=True, slots=True)
class SubjectRef:
    """A typed reference to an identity or a component."""

    kind: SubjectKind
    id: str

    def __post_init__(self) -> None:
        c.member(SubjectKind, self.kind, "subject kind")
        c.ident(self.id, "subject id")


@dataclass(frozen=True, slots=True)
class EngineFamily:
    family_id: str
    name: str
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.family_id, "family_id")
        c.text(self.name, "family name")
        c.plain(self.notes, "notes")


@dataclass(frozen=True, slots=True)
class EngineVariant:
    """A designated engine (RS-25D, J-2S, RL10A-3-3A)."""

    variant_id: str
    family_id: str
    designation: str
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.variant_id, "variant_id")
        c.ident(self.family_id, "family_id")
        c.text(self.designation, "designation")
        c.plain(self.notes, "notes")


@dataclass(frozen=True, slots=True)
class EngineConfiguration:
    """A build standard or rating of a variant (Block IIA; the 230,000 lb J-2; Apollo SPS Block I).

    Attributes:
        label: The configuration as sources name it.
        effective: When it applies, in words or as a date ("first flight STS-104,
            July 2001"), or Missing when no source says.
    """

    configuration_id: str
    variant_id: str
    label: str
    effective: str | Missing
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.configuration_id, "configuration_id")
        c.ident(self.variant_id, "variant_id")
        c.text(self.label, "configuration label")
        if not isinstance(self.effective, Missing):
            c.text(self.effective, "effective")
        c.plain(self.notes, "notes")


@dataclass(frozen=True, slots=True)
class OperatingPoint:
    """A named running condition of one configuration ("104.5% RPL", "MR 4.5", "idle mode").

    Its defining settings are not restated here; an assertion made at this point
    references it and carries its own conditions.
    """

    operating_point_id: str
    configuration_id: str
    label: str
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.operating_point_id, "operating_point_id")
        c.ident(self.configuration_id, "configuration_id")
        c.text(self.label, "operating point label")
        c.plain(self.notes, "notes")


@dataclass(frozen=True, slots=True)
class UnitMember:
    """One member of a propulsion unit: an engine configuration or another unit.

    ``count`` is how many; Missing when no source states it.
    """

    member: SubjectRef
    count: int | Missing
    role: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.member, SubjectRef):
            raise EvidenceError(f"member must be a SubjectRef, got {self.member!r}")
        if self.member.kind not in (SubjectKind.CONFIGURATION, SubjectKind.VARIANT,
                                    SubjectKind.PROPULSION_UNIT):
            raise EvidenceError(
                f"a unit member is an engine variant or configuration or another unit, "
                f"not a {self.member.kind.value}")
        if isinstance(self.count, bool) or not isinstance(self.count, (int, Missing)):
            raise EvidenceError(f"count must be an integer or Missing, got {self.count!r}")
        if isinstance(self.count, int) and self.count < 1:
            raise EvidenceError(f"count must be at least 1, got {self.count}")
        c.plain(self.role, "role")


@dataclass(frozen=True, slots=True)
class PropulsionUnit:
    """A module, a propulsion system, or a stage's propulsion: not an engine variant."""

    unit_id: str
    kind: PropulsionUnitKind
    designation: str
    members: tuple[UnitMember, ...]
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.unit_id, "unit_id")
        c.member(PropulsionUnitKind, self.kind, "propulsion unit kind")
        c.text(self.designation, "designation")
        c.instances(self.members, UnitMember, "members")
        refs = [m.member for m in self.members]
        if len(set(refs)) != len(refs):
            raise EvidenceError(f"{self.unit_id}: a member is listed twice")
        if SubjectRef(SubjectKind.PROPULSION_UNIT, self.unit_id) in refs:
            raise EvidenceError(f"{self.unit_id} cannot contain itself")
        c.plain(self.notes, "notes")


_ALIAS_TARGETS = frozenset({SubjectKind.FAMILY, SubjectKind.VARIANT,
                            SubjectKind.CONFIGURATION, SubjectKind.PROPULSION_UNIT})


@dataclass(frozen=True, slots=True)
class Alias:
    """Another name for an identity. An alias names an identity, never another alias."""

    alias_id: str
    name: str
    kind: AliasKind
    target: SubjectRef
    source_ids: tuple[str, ...]
    ambiguous: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.alias_id, "alias_id")
        c.text(self.name, "alias name")
        c.member(AliasKind, self.kind, "alias kind")
        if not isinstance(self.target, SubjectRef) or self.target.kind not in _ALIAS_TARGETS:
            raise EvidenceError(
                f"an alias names a family, variant, configuration or propulsion unit, "
                f"got {self.target!r}")
        c.idents(self.source_ids, "alias source_ids", allow_empty=False)
        if not isinstance(self.ambiguous, bool):
            raise EvidenceError("ambiguous must be true or false")
        c.plain(self.notes, "notes")


@dataclass(frozen=True, slots=True)
class LineageEdge:
    """``source`` is ``kind`` to ``target`` (the RD-180 is DERIVED_FROM the RD-170)."""

    lineage_id: str
    kind: LineageKind
    source: SubjectRef
    target: SubjectRef
    source_ids: tuple[str, ...]
    notes: str = ""

    def __post_init__(self) -> None:
        c.ident(self.lineage_id, "lineage_id")
        c.member(LineageKind, self.kind, "lineage kind")
        for name in ("source", "target"):
            ref = getattr(self, name)
            if not isinstance(ref, SubjectRef) or ref.kind not in _ALIAS_TARGETS:
                raise EvidenceError(f"lineage {name} must reference an identity, got {ref!r}")
        if self.source == self.target:
            raise EvidenceError(f"{self.lineage_id}: an identity cannot be {self.kind.value} itself")
        c.idents(self.source_ids, "lineage source_ids", allow_empty=False)
        c.plain(self.notes, "notes")
