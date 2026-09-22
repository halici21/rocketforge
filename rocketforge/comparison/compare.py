"""Compare RocketForge's reported values with a reference case.

Every comparison reports the same things -- both values in the same unit, the
absolute and relative difference -- and then, *only where the source kind
permits*, a verdict:

* direct CEA: ``agrees`` within the case's stated tolerance, else ``differs``;
* a NASA printout: ``agrees`` within half its last printed digit, else
  ``differs``;
* an independent code or an experiment: ``compared``, and nothing more.

That last rule is the point of this module. PROPEP and EXPLO5 use their own
thermodynamic data and their own models; a difference from either is
information about two codes, not evidence that either is wrong. There is no
function here that ranks, sorts by closeness, or picks a "best" reference, and
none should be added.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from .cases import ReferenceCase, SourceKind
from .units import to_canonical

__all__ = [
    "ObservedQuantity",
    "QuantityComparison",
    "CaseComparison",
    "compare",
    "AGREES",
    "DIFFERS",
    "COMPARED",
    "INCOMPLETE",
]

AGREES = "agrees"
DIFFERS = "differs"
COMPARED = "compared"          # a difference, reported without a verdict
INCOMPLETE = "incomplete"      # the reference states something RocketForge did not


@dataclass(frozen=True, slots=True)
class ObservedQuantity:
    """A value RocketForge reported, keyed as :class:`ReferenceQuantity` is."""

    key: str
    value: float
    unit: str


@dataclass(frozen=True, slots=True)
class QuantityComparison:
    """One quantity, both sides, in the canonical unit.

    Attributes:
        bound: What agreement means for this row, absolute: half the printed
            digit, or the tolerance times the reference. ``None`` where no
            verdict is drawn.
        uncertainty: A measurement's stated uncertainty, carried for the
            reader; never turned into a verdict.
    """

    key: str
    unit: str
    reference: float
    observed: float
    abs_diff: float
    rel_diff: float | None
    bound: float | None
    verdict: str
    uncertainty: float | None = None


@dataclass(frozen=True, slots=True)
class CaseComparison:
    """A whole case compared.

    Attributes:
        rows: One per reference quantity RocketForge also reported.
        not_observed: Reference quantities RocketForge did not report. A
            verdict case with any of these cannot ``agree``: agreement with
            part of a reference is not agreement with the reference.
    """

    case: ReferenceCase
    rows: tuple[QuantityComparison, ...]
    not_observed: tuple[str, ...]

    @property
    def verdict(self) -> str:
        if not self.case.allows_verdict:
            return COMPARED
        if self.not_observed:
            return INCOMPLETE
        if any(row.verdict == DIFFERS for row in self.rows):
            return DIFFERS
        return AGREES

    def as_records(self) -> list[dict]:
        """Plain dictionaries, for an archive or a report."""
        return [{
            "key": r.key, "unit": r.unit, "reference": r.reference,
            "observed": r.observed, "abs_diff": r.abs_diff,
            "rel_diff": r.rel_diff, "bound": r.bound, "verdict": r.verdict,
            "uncertainty": r.uncertainty,
        } for r in self.rows]


#: Floating-point slack on a printed-precision bound: a value exactly half a
#: digit away is inside the bound, and conversion must not push it out.
_BOUND_EPS_REL = 1e-12


def compare(case: ReferenceCase,
            observed: Mapping[str, ObservedQuantity]) -> CaseComparison:
    """Compare one reference case with what RocketForge reported."""
    rows: list[QuantityComparison] = []
    missing: list[str] = []
    for ref in case.quantities:
        seen = observed.get(ref.key)
        if seen is None:
            missing.append(ref.key)
            continue
        reference, unit, dimension = to_canonical(ref.value, ref.unit)
        value, seen_unit, seen_dimension = to_canonical(seen.value, seen.unit)
        if seen_dimension != dimension:
            raise ValueError(
                f"{ref.key}: reference is a {dimension}, RocketForge reported "
                f"a {seen_dimension}")
        abs_diff = value - reference
        rel_diff = abs_diff / reference if reference != 0.0 else None

        bound = None
        if case.source_kind is SourceKind.CEA_DIRECT:
            bound = case.tolerance_rel * abs(reference)
        elif case.source_kind is SourceKind.NASA_PUBLISHED:
            half_unit = ref.printed_half_unit
            bound = to_canonical(half_unit, ref.unit)[0] * (1.0 + _BOUND_EPS_REL)

        if bound is None:
            verdict = COMPARED
        else:
            verdict = AGREES if abs(abs_diff) <= bound else DIFFERS

        uncertainty = (None if ref.uncertainty is None
                       else to_canonical(ref.uncertainty, ref.unit)[0])
        if not math.isfinite(value):
            verdict = DIFFERS if bound is not None else COMPARED
        rows.append(QuantityComparison(
            key=ref.key, unit=unit, reference=reference, observed=value,
            abs_diff=abs_diff, rel_diff=rel_diff, bound=bound,
            verdict=verdict, uncertainty=uncertainty))
    return CaseComparison(case=case, rows=tuple(rows), not_observed=tuple(missing))
