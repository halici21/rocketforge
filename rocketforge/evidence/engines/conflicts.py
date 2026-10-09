"""Conflicts: published claims that disagree, kept as claims.

A :class:`Conflict` references the competing assertions; it never copies,
averages or replaces them. Even a resolved conflict leaves every claim in the
corpus, and a preferred claim is named only when the resolution says one is
the reliable statement for the subject.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..values import EvidenceError
from . import _checks as c
from .vocabulary import ConflictCategory, ConflictResolution

__all__ = ["Conflict"]


@dataclass(frozen=True, slots=True)
class Conflict:
    """Two or more assertions that cannot all be taken at face value.

    Attributes:
        conflict_id: Stable identifier.
        field_path: What disagrees, in words or as a field path.
        assertion_ids: The competing assertions (at least two, distinct). They
            may come from one document (an intra-document conflict: a table
            and its own text) or several; the corpus reports which.
        resolution: Where the conflict stands.
        categories: Why the claims differ, when known. At least one for any
            resolution other than UNRESOLVED.
        explanation: The argument, citing what it rests on.
        preferred_assertion_id: For RESOLVED only, the claim shown to be the
            reliable one. The others are kept.
    """

    conflict_id: str
    field_path: str
    assertion_ids: tuple[str, ...]
    resolution: ConflictResolution
    categories: tuple[ConflictCategory, ...]
    explanation: str
    preferred_assertion_id: str | None = None

    def __post_init__(self) -> None:
        c.ident(self.conflict_id, "conflict_id")
        c.text(self.field_path, "conflict field_path")
        c.idents(self.assertion_ids, "conflict assertion_ids", allow_empty=False)
        if len(self.assertion_ids) < 2:
            raise EvidenceError(f"{self.conflict_id}: a conflict is between at least two assertions")
        c.member(ConflictResolution, self.resolution, "resolution")
        c.instances(self.categories, ConflictCategory, "categories")
        if len(set(self.categories)) != len(self.categories):
            raise EvidenceError(f"{self.conflict_id}: a category is listed twice")
        c.plain(self.explanation, "explanation")
        if self.resolution is not ConflictResolution.UNRESOLVED:
            if not self.categories:
                raise EvidenceError(f"{self.conflict_id}: a {self.resolution.value} conflict says why the claims differ")
            c.text(self.explanation, f"{self.conflict_id}: explanation")
        if self.preferred_assertion_id is not None:
            if self.resolution is not ConflictResolution.RESOLVED:
                raise EvidenceError(f"{self.conflict_id}: only a RESOLVED conflict names a preferred claim")
            if self.preferred_assertion_id not in self.assertion_ids:
                raise EvidenceError(f"{self.conflict_id}: the preferred claim must be one of the competing assertions")
        elif self.resolution is ConflictResolution.RESOLVED:
            raise EvidenceError(f"{self.conflict_id}: a RESOLVED conflict names the claim that stands")
