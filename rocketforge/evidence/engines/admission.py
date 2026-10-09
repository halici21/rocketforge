"""What a shipped reference-engine corpus satisfies beyond the schema.

The DB-1 schema accepts research-grade evidence: search results, inferred
values, unsettled rights, open conflicts, all honestly labelled. A corpus that
RocketForge *ships* as reference data holds a stricter subset, and
:func:`admission_violations` states the difference:

* every source was opened, its values may ship with attribution, and its
  rights reading is settled (consistent, or a conflict resolved by a recorded
  review) -- a source nobody reviewed ships nothing;
* every assertion is admitted, and is REPORTED or DIGITISED (a digitised value
  read from an original drawing); an INFERRED or DERIVED value is not shipped
  reference data, and a Missing value is only "the source does not give it";
* no shipped assertion is in an UNRESOLVED or PARTIALLY_RESOLVED conflict;
* no graph claims to be complete.

The function only reports. It never repairs, never drops a record, and never
reaches past the corpus it is given.
"""

from __future__ import annotations

from ..values import MissingReason, ShippingPolicy, ValueStatus
from .corpus import BLOCKING_RESOLUTIONS, EngineEvidenceCorpus
from .vocabulary import ORIGINAL_PROVENANCES, Admissibility, RightsReview, SourceAccess

__all__ = ["admission_violations", "SHIPPED_STATUSES", "SETTLED_RIGHTS"]

#: How a shipped value may have entered the record.
SHIPPED_STATUSES = frozenset({ValueStatus.REPORTED, ValueStatus.DIGITISED})

#: Rights readings under which a source's values may ship.
SETTLED_RIGHTS = frozenset({RightsReview.CONSISTENT, RightsReview.CONFLICT_RESOLVED_BY_REVIEW})


def admission_violations(corpus: EngineEvidenceCorpus) -> tuple[str, ...]:
    """Why this corpus may not ship as reference data. Empty means it may."""
    out: list[str] = []
    schematics = {s.schematic_id: s for s in corpus.schematics}
    for s in corpus.sources:
        sid = s.source_id
        if s.access is not SourceAccess.OPENED:
            out.append(f"source {sid}: {s.access.value}; only a document that was opened is shipped")
        if s.rights.values is not ShippingPolicy.VALUES_WITH_ATTRIBUTION:
            out.append(f"source {sid}: values policy {s.rights.values.value}")
        if s.rights.review not in SETTLED_RIGHTS:
            out.append(f"source {sid}: rights review {s.rights.review.value}")
    for a in corpus.assertions:
        aid = a.assertion_id
        if a.admissibility is not Admissibility.ADMITTED:
            out.append(f"{aid}: {a.admissibility.value}")
        if a.is_missing:
            if a.value.reason is not MissingReason.NOT_REPORTED:  # type: ignore[union-attr]
                out.append(f"{aid}: a shipped Missing value says only that the source does not give it")
            continue
        if a.status not in SHIPPED_STATUSES:
            out.append(f"{aid}: status {a.status.value}; only REPORTED or DIGITISED values ship")  # type: ignore[union-attr]
        if a.status is ValueStatus.DIGITISED:
            drawn = schematics.get(a.schematic_id) if a.schematic_id else None
            if drawn is None or drawn.provenance not in ORIGINAL_PROVENANCES:
                out.append(f"{aid}: a digitised value is read from an original drawing it names")
    for x in corpus.conflicts:
        if x.resolution in BLOCKING_RESOLUTIONS:
            out.append(f"conflict {x.conflict_id}: {x.resolution.value} on shipped assertions "
                       f"{', '.join(x.assertion_ids)}")
    for t in corpus.topologies:
        if t.completeness.declared_complete:
            out.append(f"{t.topology_id}: a shipped graph does not claim completeness")
    return tuple(out)
