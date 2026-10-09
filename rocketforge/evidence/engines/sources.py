"""Engine sources: what was done with a document, and what may be done with it.

An :class:`EngineSource` wraps the existing :class:`~rocketforge.evidence.SourceReference`
(bibliographic identity, how a reader obtains it, the values shipping policy and
the 1-3 tier) and adds what reference-engine evidence needs beside it:

* the A-E authority scale, tied to the existing tier by
  :data:`~.vocabulary.TIER_FOR_AUTHORITY`;
* the access state -- only an :attr:`~.vocabulary.SourceAccess.OPENED` document
  can make a value evidence;
* the content hash, so two registry entries for one file are one document;
* a :class:`RightsRecord` that keeps the repository's statement and the printed
  notice side by side, with a policy per content kind.

Scientific authority and redistribution rights are separate: a Tier A NASA
report can carry a restrictive printed notice, and that is recorded, not
resolved.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..records import SourceReference
from ..values import EvidenceError, Missing, MissingReason, ShippingPolicy
from . import _checks as c
from .vocabulary import (
    TIER_FOR_AUTHORITY,
    RightsReview,
    SourceAccess,
    SourceAuthority,
    SourcePrimacy,
)

__all__ = ["RightsNotice", "RightsRecord", "EngineSource", "RIGHTS_IN_RECORD"]

#: The ``SourceReference.rights_statement`` of every engine source. The statements
#: themselves live in the structured :class:`RightsRecord`; one place, so they
#: cannot drift apart.
RIGHTS_IN_RECORD = "See the engine source rights record."

#: Missing reasons a rights statement can carry: nobody looked, or nothing is stated.
_NOTICE_ABSENCE = frozenset({MissingReason.NOT_AUDITED, MissingReason.NOT_REPORTED,
                             MissingReason.ACCESS_BLOCKED})


@dataclass(frozen=True, slots=True)
class RightsNotice:
    """One rights statement, as found.

    Attributes:
        statement: The statement verbatim, or a faithful excerpt.
        where: Where it was read: the repository record ("NTRS citation API,
            copyright.determinationType") or the page ("PDF p.3, page A").
    """

    statement: str
    where: str

    def __post_init__(self) -> None:
        c.text(self.statement, "rights statement")
        c.text(self.where, "where the rights statement was read")


def _notice(value: object, what: str) -> None:
    if isinstance(value, Missing):
        if value.reason not in _NOTICE_ABSENCE:
            raise EvidenceError(
                f"{what}: a rights statement is absent because it was not audited, is "
                f"not printed, or the page could not be reached; got {value.reason.value}")
    elif not isinstance(value, RightsNotice):
        raise EvidenceError(f"{what} must be a RightsNotice or Missing, got {value!r}")


@dataclass(frozen=True, slots=True)
class RightsRecord:
    """What a source's rights statements say and what follows for each kind of content.

    The host's metadata and the printed page are separate statements and may
    disagree (NTRS "public use permitted" over a page printing an AIAA
    copyright). A disagreement is recorded with ``notices_disagree`` and stays
    :attr:`~.vocabulary.RightsReview.CONFLICT_UNRESOLVED` until a review with
    a written ``review_note`` settles it. While unresolved, no content kind may
    be shipped with values.

    Attributes:
        host_metadata: The repository's or host's statement, or Missing.
        printed_notice: The notice printed in the document, or Missing
            (``NOT_REPORTED`` when the page carries none).
        values, figures, tables, text: What RocketForge may distribute of each
            kind of content, in the existing shipping vocabulary.
        notices_disagree: A reviewer's finding that the two statements conflict.
            It is the reviewer's call, not computed from the text: wording
            differs in ways a string comparison cannot judge.
        review: Where the rights reading stands.
        review_note: Why the policies are what they are; required when a
            conflict was resolved by review.
    """

    host_metadata: RightsNotice | Missing
    printed_notice: RightsNotice | Missing
    values: ShippingPolicy
    figures: ShippingPolicy
    tables: ShippingPolicy
    text: ShippingPolicy
    notices_disagree: bool
    review: RightsReview
    review_note: str = ""

    def __post_init__(self) -> None:
        _notice(self.host_metadata, "host_metadata")
        _notice(self.printed_notice, "printed_notice")
        for kind in ("values", "figures", "tables", "text"):
            c.member(ShippingPolicy, getattr(self, kind), f"{kind} policy")
        if not isinstance(self.notices_disagree, bool):
            raise EvidenceError("notices_disagree must be true or false")
        c.member(RightsReview, self.review, "review")
        c.plain(self.review_note, "review_note")
        conflict_states = (RightsReview.CONFLICT_UNRESOLVED,
                           RightsReview.CONFLICT_RESOLVED_BY_REVIEW)
        if self.notices_disagree and self.review not in conflict_states:
            raise EvidenceError(
                "the host statement and the printed notice disagree; the rights review "
                "must be CONFLICT_UNRESOLVED (or CONFLICT_RESOLVED_BY_REVIEW with a note), "
                f"not {self.review.value}")
        if self.review in conflict_states and not self.notices_disagree:
            raise EvidenceError(f"review {self.review.value} needs notices_disagree=true")
        if self.notices_disagree and (isinstance(self.host_metadata, Missing)
                                      or isinstance(self.printed_notice, Missing)):
            raise EvidenceError("a disagreement needs both statements recorded")
        if self.review is RightsReview.CONFLICT_RESOLVED_BY_REVIEW and not self.review_note.strip():
            raise EvidenceError("a conflict resolved by review records the review in review_note")
        if self.review is RightsReview.CONFLICT_UNRESOLVED:
            shipped = [kind for kind in ("values", "figures", "tables", "text")
                       if getattr(self, kind) is ShippingPolicy.VALUES_WITH_ATTRIBUTION]
            if shipped:
                raise EvidenceError(
                    f"rights are in unresolved conflict, yet {shipped} would ship content; "
                    "the stricter reading governs until a review decides")

    @property
    def unresolved(self) -> bool:
        return self.review in (RightsReview.CONFLICT_UNRESOLVED, RightsReview.NOT_REVIEWED)


@dataclass(frozen=True, slots=True)
class EngineSource:
    """A source of reference-engine evidence.

    Attributes:
        reference: The existing source record. Its ``shipping`` must equal
            ``rights.values``, its ``tier`` must match ``authority``, and its
            ``rights_statement`` is :data:`RIGHTS_IN_RECORD`.
        authority: A-E (:class:`~.vocabulary.SourceAuthority`).
        primacy: Whether the source first stated what it says.
        access: What was done with the document.
        content_sha256: SHA-256 of the file that was opened, when one was;
            required for an opened document.
        same_document_as: Another source id holding the same file. Two
            sources with one hash must say so; filenames are never compared.
        rights: The rights reading.
        access_note: How access was attempted, and why it failed if it did.
    """

    reference: SourceReference
    authority: SourceAuthority
    primacy: SourcePrimacy
    access: SourceAccess
    content_sha256: str | None
    same_document_as: str | None
    rights: RightsRecord
    access_note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.reference, SourceReference):
            raise EvidenceError(f"reference must be a SourceReference, got {self.reference!r}")
        c.ident(self.reference.source_id, "source_id")
        c.member(SourceAuthority, self.authority, "authority")
        c.member(SourcePrimacy, self.primacy, "primacy")
        c.member(SourceAccess, self.access, "access")
        if self.content_sha256 is not None:
            c.sha256_hex(self.content_sha256, "content_sha256")
        if self.access in (SourceAccess.OPENED, SourceAccess.FETCHED_NOT_READ) \
                and self.content_sha256 is None:
            raise EvidenceError(
                f"{self.source_id}: a fetched document records the hash of the file read")
        if self.access in (SourceAccess.SEARCH_RESULT_ONLY, SourceAccess.ACCESS_BLOCKED) \
                and self.content_sha256 is not None:
            raise EvidenceError(f"{self.source_id}: a document that was never fetched has no hash")
        if self.same_document_as is not None:
            c.ident(self.same_document_as, "same_document_as")
            if self.same_document_as == self.source_id:
                raise EvidenceError(f"{self.source_id} cannot be a duplicate of itself")
        if not isinstance(self.rights, RightsRecord):
            raise EvidenceError(f"rights must be a RightsRecord, got {self.rights!r}")
        if self.reference.rights_statement != RIGHTS_IN_RECORD:
            raise EvidenceError(
                f"{self.source_id}: rights statements are recorded in the rights record; the "
                f"source reference's rights_statement must read {RIGHTS_IN_RECORD!r}")
        if self.reference.shipping is not self.rights.values:
            raise EvidenceError(
                f"{self.source_id}: the source reference ships "
                f"{self.reference.shipping.value} but the rights record's values policy is "
                f"{self.rights.values.value}; they are one decision")
        expected = TIER_FOR_AUTHORITY[self.authority]
        if self.reference.tier != expected:
            raise EvidenceError(
                f"{self.source_id}: authority {self.authority.value} corresponds to tier "
                f"{expected}, but the source reference says tier {self.reference.tier}")
        c.plain(self.access_note, "access_note")

    @property
    def source_id(self) -> str:
        return self.reference.source_id

    @property
    def opened(self) -> bool:
        return self.access is SourceAccess.OPENED
