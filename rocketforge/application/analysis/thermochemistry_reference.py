"""Comparison against an accepted external thermochemistry reference. Qt-free.

The direction is the same one the compressible reference module states, and it
matters more here, not less:

    published value  --compare-->  RocketForge + provider value

never

    published value  --lookup-->   answer

Nothing in RocketForge reads a published number to produce a result. The
reference exists to check the pipeline, and a check that could feed the thing it
checks is not a check.

**Tolerance comes from the source's own printed precision**, computed here from
the significant-figure count the dataset records, before any comparison runs. A
value printed to six figures stands for anything within half a unit of its last
digit; requiring more would be requiring the source to be more precise than it
is, and widening it afterwards to make a value pass would be tuning
RocketForge to a rounded number -- the one thing this project never does.

**Performance quantities are absent by construction.** The published source
carries c*, Isp and an exit gamma. This module does not load their values at
all: the dataset records that they exist and why Phase 5D does not compare
them, and carries no number for them. A quantity whose value is never read
cannot leak into a display (Phase 5D §84, §129, §171).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache

from .reference_comparison import reference_root
from .thermochemistry_service import ChamberCase, ChamberOutcome, solve_case

__all__ = [
    "ReferenceQuantity",
    "ReferenceComparison",
    "ReferenceCase",
    "THERMOCHEMISTRY_REFERENCE",
    "load_reference",
    "reference_case",
    "run_reference",
    "compare",
    "rounding_box",
]

#: The dataset this workspace ships. One, deliberately: Phase 5C validated one
#: external case end to end, and a References page listing three when one was
#: checked would be padding.
THERMOCHEMISTRY_REFERENCE = "thermochemistry_nasa_cea_2002_lox_lh2.json"


def rounding_box(value: float, significant_figures: int) -> float:
    """Relative half-width of the box a printed value could have come from.

    A number printed to N significant figures stands for anything within half a
    unit of its last digit. That, and not a chosen constant, is what sets the
    tolerance for comparing against it.
    """
    if value == 0.0:
        return 0.0
    exponent = math.floor(math.log10(abs(value)))
    half_ulp = 0.5 * 10.0 ** (exponent - significant_figures + 1)
    return half_ulp / abs(value)


@lru_cache(maxsize=4)
def load_reference(name: str = THERMOCHEMISTRY_REFERENCE) -> dict:
    """The shipped reference dataset, read once.

    Resolved through :func:`reference_root`, which knows about ``sys._MEIPASS``,
    so the packaged application reads the bundled copy rather than a path that
    exists only in a source checkout.
    """
    payload = json.loads((reference_root() / name).read_text(encoding="utf-8"))
    if payload.get("kind") != "thermochemistry_chamber":
        raise ValueError(
            f"{name} is not a thermochemistry chamber reference; it declares "
            f"kind {payload.get('kind')!r}")
    return payload


@dataclass(frozen=True, slots=True)
class ReferenceQuantity:
    """One published value, with everything needed to compare against it."""

    key: str
    label: str
    state_field: str
    value: float
    unit: str
    significant_figures: int
    to_si: float
    si_unit: str

    @property
    def si_value(self) -> float:
        """The published value in RocketForge's units."""
        return self.value * self.to_si

    @property
    def tolerance(self) -> float:
        """The source's own rounding box, as a relative half-width."""
        return rounding_box(self.value, self.significant_figures)


@dataclass(frozen=True, slots=True)
class ReferenceComparison:
    """One published quantity against what the pipeline produced."""

    key: str
    label: str
    published: float
    published_unit: str
    computed: float | None
    unit: str
    relative_difference: float
    tolerance: float
    passed: bool

    @property
    def verdict(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass(frozen=True, slots=True)
class ReferenceCase:
    """A reference dataset, unpacked into the pieces a page needs."""

    dataset: str
    title: str
    level: str
    level_name: str
    source: dict
    conditions: dict
    case: ChamberCase
    case_notes: dict
    quantities: tuple[ReferenceQuantity, ...]
    not_compared: tuple[dict, ...]

    @property
    def citation(self) -> str:
        source = self.source
        return (f"{source.get('program', '')}, {source.get('header_date', '')} "
                f"— {source.get('authors', '')}").strip(" —,")


def reference_case(payload: dict | None = None) -> ReferenceCase:
    """Unpack a dataset into a runnable, displayable reference case.

    Takes the payload rather than only a filename so that a test can hand in a
    deliberately altered copy and prove the comparison actually reads it.
    """
    payload = payload if payload is not None else load_reference()
    spec = payload["case"]
    case = ChamberCase(
        fuel=spec["fuel"],
        oxidiser=spec["oxidiser"],
        oxidiser_fuel_ratio=float(spec["oxidiser_fuel_ratio"]),
        chamber_pressure=float(spec["chamber_pressure_Pa"]),
        fuel_temperature=float(spec["fuel_temperature_K"]),
        oxidiser_temperature=float(spec["oxidiser_temperature_K"]),
    )
    quantities = tuple(
        ReferenceQuantity(
            key=entry["key"], label=entry["label"],
            state_field=entry["state_field"], value=float(entry["value"]),
            unit=entry["unit"],
            significant_figures=int(entry["significant_figures"]),
            to_si=float(entry["to_si"]), si_unit=entry["si_unit"])
        for entry in payload["published"]
    )
    return ReferenceCase(
        dataset=payload["dataset"],
        title=payload["title"],
        level=payload.get("level", ""),
        level_name=payload.get("level_name", ""),
        source=dict(payload.get("source", {})),
        conditions=dict(payload.get("conditions", {})),
        case=case,
        case_notes={k: v for k, v in spec.items() if k.endswith("note")},
        quantities=quantities,
        not_compared=tuple(dict(entry) for entry in payload.get("not_compared", ())),
    )


def run_reference(case: ReferenceCase) -> ChamberOutcome:
    """Solve the reference case exactly as stored.

    The conditions come from the dataset, never from whatever happens to be in
    the Calculator form. A reference case that could be edited would stop being
    a reference (Phase 5D §87, §88).
    """
    return solve_case(case.case)


def compare(case: ReferenceCase,
            outcome: ChamberOutcome) -> tuple[ReferenceComparison, ...]:
    """Published values against the pipeline's, with the source's own tolerance.

    A quantity the result does not carry is reported with ``computed=None`` and
    a failed verdict rather than being dropped: silently omitting a row would
    turn a missing answer into a passing comparison.
    """
    state = outcome.state
    rows: list[ReferenceComparison] = []
    for quantity in case.quantities:
        computed: float | None = None
        if state is not None:
            raw = getattr(state, quantity.state_field, None)
            computed = None if raw is None else float(raw)
        published_si = quantity.si_value
        if computed is None or published_si == 0.0:
            relative = float("inf")
            passed = False
        else:
            relative = abs(computed - published_si) / abs(published_si)
            passed = relative <= quantity.tolerance
        rows.append(ReferenceComparison(
            key=quantity.key, label=quantity.label,
            published=published_si, published_unit=quantity.si_unit,
            computed=computed, unit=quantity.si_unit,
            relative_difference=relative, tolerance=quantity.tolerance,
            passed=passed))
    return tuple(rows)


def overall_verdict(rows: tuple[ReferenceComparison, ...]) -> str:
    """PASS only when every compared quantity passed. No partial credit."""
    if not rows:
        return "NOT RUN"
    return "PASS" if all(row.passed for row in rows) else "FAIL"


def source_rows(case: ReferenceCase) -> tuple[dict[str, str], ...]:
    """The source's identity and the conditions it was produced under.

    Shown instead of a bare "PASS", because a verdict with no visible source is
    an assertion rather than evidence (Phase 5D §85).
    """
    rows = [{"label": key.replace("_", " ").title(), "value": str(value)}
            for key, value in case.source.items()]
    rows.extend({"label": key.replace("_", " ").title(), "value": str(value)}
                for key, value in case.conditions.items())
    return tuple(rows)
