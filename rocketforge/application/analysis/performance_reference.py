"""The external performance reference, and what it does and does not validate.

Phase 5D's thermochemistry dataset deliberately carried **no** value for c* or
Isp, because RocketForge did not own those quantities. Phase 5E does, so this
is a **separate** dataset rather than an extension of that one -- the Phase 5D
contract that its reference is thermochemistry-only stays intact.

Two things this module is careful about, and they are the whole reason it is
not a copy of the thermochemistry reference:

**It validates the oracle, not RocketForge.** The published numbers came from a
shifting-equilibrium, calorically imperfect calculation. RocketForge v1 is a
constant-property, calorically perfect model. So the source is compared against
the **CEA oracle** -- two implementations of the same method, which is a real
check -- and RocketForge is then compared against the oracle under its own
stated assumptions, as a *model difference*.

**The reference condition is stated.** CEA's printed Cf and Isp are the
optimum-expansion values, established by measurement rather than assumed; the
dataset records it and the comparison honours it. Comparing a vacuum figure
against them would be wrong by the entire pressure term.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache

from .reference_comparison import reference_root
from .thermochemistry_reference import rounding_box

__all__ = [
    "PERFORMANCE_REFERENCE",
    "PublishedPerformance",
    "PerformanceReferenceCase",
    "PerformanceComparison",
    "load_performance_reference",
    "performance_reference_case",
    "compare_published",
    "overall_verdict",
    "source_rows",
]

#: The one external performance case this phase validates end to end.
PERFORMANCE_REFERENCE = "performance_nasa_cea_2002_lox_lh2.json"


@dataclass(frozen=True, slots=True)
class PublishedPerformance:
    """One published performance value, with everything needed to compare."""

    key: str
    label: str
    oracle_field: str
    value: float
    unit: str
    significant_figures: int
    to_si: float
    si_unit: str
    conversion_note: str = ""

    @property
    def si_value(self) -> float:
        return self.value * self.to_si

    @property
    def tolerance(self) -> float:
        """The source's own rounding box, from its printed precision."""
        return rounding_box(self.value, self.significant_figures)


@dataclass(frozen=True, slots=True)
class PerformanceReferenceCase:
    """A performance reference, unpacked."""

    dataset: str
    title: str
    level: str
    level_name: str
    source: dict
    conditions: dict
    case: dict
    published: tuple[PublishedPerformance, ...]
    validates: dict
    reference_condition_note: str

    @property
    def citation(self) -> str:
        source = self.source
        return (f"{source.get('program', '')}, {source.get('header_date', '')} "
                f"— {source.get('authors', '')}").strip(" —,")


@dataclass(frozen=True, slots=True)
class PerformanceComparison:
    """One published value against one computed value, honestly labelled.

    ``role`` is what makes this different from a compressible-table comparison:
    the same published number is a *validation* of the oracle and a *model
    comparison* against RocketForge, and the verdict wording follows the role
    rather than the number.
    """

    key: str
    label: str
    published: float
    computed: float | None
    unit: str
    relative_difference: float
    tolerance: float
    passed: bool
    role: str                  # "validation" | "model comparison"
    source_of_computed: str

    @property
    def verdict(self) -> str:
        if self.computed is None:
            return "NOT RUN"
        if self.role == "validation":
            return "PASS" if self.passed else "FAIL"
        return "WITHIN BOX" if self.passed else "MODEL DIFFERENCE"


@lru_cache(maxsize=4)
def load_performance_reference(name: str = PERFORMANCE_REFERENCE) -> dict:
    """The shipped dataset, read once, through the bundle-aware root."""
    payload = json.loads((reference_root() / name).read_text(encoding="utf-8"))
    if payload.get("kind") != "rocket_performance":
        raise ValueError(
            f"{name} is not a rocket performance reference; it declares kind "
            f"{payload.get('kind')!r}")
    return payload


def performance_reference_case(payload: dict | None = None) -> PerformanceReferenceCase:
    """Unpack a dataset. Takes the payload so a test can alter it."""
    payload = payload if payload is not None else load_performance_reference()
    return PerformanceReferenceCase(
        dataset=payload["dataset"],
        title=payload["title"],
        level=payload.get("level", ""),
        level_name=payload.get("level_name", ""),
        source=dict(payload.get("source", {})),
        conditions=dict(payload.get("conditions", {})),
        case=dict(payload["case"]),
        published=tuple(
            PublishedPerformance(
                key=entry["key"], label=entry["label"],
                oracle_field=entry["oracle_field"], value=float(entry["value"]),
                unit=entry["unit"],
                significant_figures=int(entry["significant_figures"]),
                to_si=float(entry["to_si"]), si_unit=entry["si_unit"],
                conversion_note=entry.get("conversion_note", ""))
            for entry in payload["published"]),
        validates=dict(payload.get("validates", {})),
        reference_condition_note=payload.get("reference_condition_note", ""),
    )


def compare_published(case: PerformanceReferenceCase,
                      computed: dict[str, float | None],
                      *, role: str, source_of_computed: str
                      ) -> tuple[PerformanceComparison, ...]:
    """Published values against computed ones, at the source's own precision.

    ``computed`` is keyed by the dataset's ``key`` fields. A missing value is
    reported with ``computed=None`` and a failed verdict rather than dropped:
    omitting a row would turn a missing answer into a passing comparison.
    """
    if role not in ("validation", "model comparison"):
        raise ValueError(
            "role must be 'validation' or 'model comparison'. A comparison "
            "whose role is unstated cannot say whether a residual is an error "
            "or a modelling choice.")
    rows: list[PerformanceComparison] = []
    for published in case.published:
        value = computed.get(published.key)
        expected = published.si_value
        if value is None or expected == 0.0 or not math.isfinite(float(value)):
            relative, passed, value = float("inf"), False, None
        else:
            relative = abs(float(value) - expected) / abs(expected)
            passed = relative <= published.tolerance
        rows.append(PerformanceComparison(
            key=published.key, label=published.label, published=expected,
            computed=value, unit=published.si_unit,
            relative_difference=relative, tolerance=published.tolerance,
            passed=passed, role=role, source_of_computed=source_of_computed))
    return tuple(rows)


def overall_verdict(rows: tuple[PerformanceComparison, ...]) -> str:
    """PASS only when every row passed. No partial credit."""
    if not rows:
        return "NOT RUN"
    if all(row.passed for row in rows):
        return "PASS" if rows[0].role == "validation" else "WITHIN BOX"
    return "FAIL" if rows[0].role == "validation" else "MODEL DIFFERENCE"


def source_rows(case: PerformanceReferenceCase) -> tuple[dict[str, str], ...]:
    """Source identity and conditions, so a verdict is never shown alone."""
    rows = [{"label": key.replace("_", " ").title(), "value": str(value)}
            for key, value in case.source.items()]
    rows.extend({"label": key.replace("_", " ").title(), "value": str(value)}
                for key, value in case.conditions.items())
    return tuple(rows)
