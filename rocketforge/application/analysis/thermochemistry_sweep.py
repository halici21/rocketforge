"""An O/F sweep over chamber equilibrium. Qt-free.

What this is: the same scalar chamber calculation the Calculator runs, repeated
over a range of mixture ratios, with every point kept and every point
traceable.

What this is **not**: an optimiser. Nothing here reports a best, optimal or
recommended O/F. A maximum found in a sampled interval is a maximum in that
sampled interval and is labelled as one -- Phase 5B-0 measured different
quantities peaking at different mixture ratios, so "the peak" is not a single
place, and choosing between them is a decision layer this phase does not build
(Phase 5D §12, §55, §77).

Three implementation choices worth stating:

* **Scalar solves, in order, in this process.** No batch provider API was added
  for the sweep, and no threads were used: Phase 5B-0 measured four threads at
  roughly 0.85x of serial for CEA, so parallelising would cost performance and
  buy a shared native library's concurrency risk (Phase 5D §57, §61).
* **A failed point is a point.** It keeps its place in the sequence and its own
  message. Charts break their line across it rather than joining the
  neighbours, because a straight segment across a failure asserts physics that
  was never solved (§63, §123).
* **Repeated provider warnings are aggregated, not repeated.** An
  assigned-enthalpy caveat is a property of the reactant, so it is true at
  every point; forty-one identical rows would bury the point-specific ones
  (§78).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any

from .thermochemistry_service import (
    OUTCOME_OK,
    OUTCOME_WARNING,
    ChamberCase,
    ChamberOutcome,
    solve_case,
)

__all__ = [
    "SweepRange",
    "SweepPoint",
    "SweepResult",
    "SweepRangeError",
    "MAX_SWEEP_POINTS",
    "DEFAULT_SWEEP_RANGE",
    "validate_range",
    "sweep_cases",
    "run_sweep",
    "series_for",
    "species_series_for",
    "SWEEP_QUANTITIES",
    "sweep_columns",
    "aggregated_warnings",
    "maximum_in_range",
]

#: The application-level guard on how many solves one sweep may request.
#:
#: Chosen from measurement, not caution. Phase 5C benchmarked the full
#: RocketForge pipeline -- mapping, solve, element balance, four state
#: identities, composition validation and provenance -- at 0.568 ms per point,
#: so 1000 points is about 0.57 s of solving. That is a wait, but a bounded and
#: honest one, and it is the largest sweep Phase 5C actually measured. A larger
#: request is refused with the limit named rather than silently truncated.
MAX_SWEEP_POINTS = 1000


class SweepRangeError(ValueError):
    """A sweep range that cannot be run, with the reason in the message."""


@dataclass(frozen=True, slots=True)
class SweepRange:
    """The O/F interval and how densely it is sampled.

    Expressed as endpoints plus a point count rather than a step, because a
    step does not divide an interval exactly and the resulting endpoint drift
    is exactly the kind of quiet inaccuracy this project refuses. The step is
    derived and reported.
    """

    start: float
    end: float
    points: int

    def __post_init__(self) -> None:
        validate_range(self.start, self.end, self.points)

    @property
    def step(self) -> float:
        """The spacing actually used. Exact for the endpoints by construction."""
        if self.points < 2:
            return 0.0
        return (self.end - self.start) / (self.points - 1)

    def values(self) -> tuple[float, ...]:
        """The sampled O/F values, ascending, endpoints included exactly.

        The last value is set to ``end`` rather than accumulated, so the
        interval a user asked for is the interval that gets solved.
        """
        if self.points == 1:
            return (self.start,)
        step = self.step
        out = [self.start + step * i for i in range(self.points - 1)]
        out.append(self.end)
        return tuple(out)


def validate_range(start: float, end: float, points: int) -> None:
    """Refuse a sweep that cannot mean anything, naming what is wrong.

    Endpoints are never silently reordered: a user who typed them backwards
    asked a different question from the one that would be answered, and
    swapping them quietly is how a plotted axis ends up disagreeing with the
    form above it (Phase 5D §58).
    """
    for name, value in (("O/F start", start), ("O/F end", end)):
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise SweepRangeError(f"{name} must be a number.") from exc
        if not math.isfinite(number):
            raise SweepRangeError(f"{name} must be finite.")
        if number <= 0.0:
            raise SweepRangeError(
                f"{name} must be greater than zero; O/F is a mass ratio.")
    if float(end) <= float(start):
        raise SweepRangeError(
            "O/F end must be greater than O/F start. The endpoints are not "
            "reordered automatically, because the range you asked for is the "
            "range that gets solved.")
    try:
        count = int(points)
    except (TypeError, ValueError) as exc:
        raise SweepRangeError("Point count must be a whole number.") from exc
    if count < 2:
        raise SweepRangeError("A sweep needs at least 2 points.")
    if count > MAX_SWEEP_POINTS:
        raise SweepRangeError(
            f"{count} points exceeds the {MAX_SWEEP_POINTS}-point limit for a "
            f"single sweep. At the measured 0.57 ms per solve that limit is "
            f"about 0.6 s of chemistry; a larger study belongs to a batch "
            f"workflow, not to an interactive sweep.")


#: The Phase 5D acceptance sweep: O/F 2.5 to 4.5 in steps of 0.05.
DEFAULT_SWEEP_RANGE = SweepRange(start=2.5, end=4.5, points=41)


# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SweepPoint:
    """One solved -- or refused -- operating point of a sweep."""

    oxidiser_fuel_ratio: float
    outcome: ChamberOutcome

    @property
    def ok(self) -> bool:
        return self.outcome.state is not None

    @property
    def kind(self) -> str:
        return self.outcome.kind

    @property
    def warned(self) -> bool:
        return self.outcome.kind == OUTCOME_WARNING

    def value_of(self, key: str) -> float:
        """One quantity of this point's state, or NaN when it has none.

        NaN rather than zero, and NaN rather than an exception: a failed point
        must be representable in a numeric table without pretending it has a
        value.
        """
        state = self.outcome.state
        if state is None:
            return float("nan")
        value = getattr(state, key, None)
        return float("nan") if value is None else float(value)


@dataclass(frozen=True, slots=True)
class SweepResult:
    """A completed sweep: what was fixed, what was varied, what came back."""

    case: ChamberCase
    sweep: SweepRange
    points: tuple[SweepPoint, ...]
    elapsed_seconds: float = 0.0

    @property
    def solved(self) -> tuple[SweepPoint, ...]:
        return tuple(point for point in self.points if point.ok)

    @property
    def failed(self) -> tuple[SweepPoint, ...]:
        return tuple(point for point in self.points if not point.ok)

    @property
    def solved_count(self) -> int:
        return len(self.solved)

    @property
    def failed_count(self) -> int:
        return len(self.failed)

    @property
    def provenance(self) -> Any:
        """Provenance shared by the sweep, taken from its first solved point."""
        for point in self.points:
            if point.outcome.provenance is not None:
                return point.outcome.provenance
        return None


def sweep_cases(case: ChamberCase, sweep: SweepRange) -> tuple[ChamberCase, ...]:
    """The individual scalar cases a sweep will run, in ascending O/F.

    Pure, so a test can assert exactly which requests a sweep would make
    without a provider installed, and without confirming the sweep against
    itself.
    """
    return tuple(case.replace(oxidiser_fuel_ratio=value)
                 for value in sweep.values())


def run_sweep(case: ChamberCase, sweep: SweepRange) -> SweepResult:
    """Solve every point of the sweep, keeping failures in place."""
    started = time.perf_counter()
    points = tuple(
        SweepPoint(oxidiser_fuel_ratio=point_case.oxidiser_fuel_ratio,
                   outcome=solve_case(point_case))
        for point_case in sweep_cases(case, sweep)
    )
    return SweepResult(case=case, sweep=sweep, points=points,
                       elapsed_seconds=time.perf_counter() - started)


# ---------------------------------------------------------------------------
# chart and table data
# ---------------------------------------------------------------------------

#: The quantities a sweep can chart, with the label and unit each must carry.
#:
#: ``gamma`` is the same field the Calculator labels "Isentropic exponent γ_s",
#: with the same qualifier, so the two views cannot disagree about which of the
#: state's two gammas is being drawn (Phase 5D §66, §126).
SWEEP_QUANTITIES: tuple[dict[str, str], ...] = (
    {"key": "temperature", "label": "Chamber temperature  T₀", "unit": "K",
     "qualifier": "Adiabatic · HP equilibrium"},
    {"key": "molar_mass", "label": "Mean molar mass  M̄", "unit": "kg/mol",
     "qualifier": ""},
    {"key": "gamma", "label": "Isentropic exponent  γ_s", "unit": "",
     "qualifier": "equilibrium"},
    {"key": "density", "label": "Density  ρ", "unit": "kg/m³", "qualifier": ""},
    {"key": "gas_constant", "label": "Specific gas constant  R",
     "unit": "J/(kg·K)", "qualifier": ""},
    {"key": "cp", "label": "Specific heat  c_p", "unit": "J/(kg·K)",
     "qualifier": "frozen"},
    {"key": "cv", "label": "Specific heat  c_v", "unit": "J/(kg·K)",
     "qualifier": "frozen"},
)


def quantity_meta(key: str) -> dict[str, str]:
    """Label, unit and qualifier for a chartable quantity."""
    for entry in SWEEP_QUANTITIES:
        if entry["key"] == key:
            return dict(entry)
    return {"key": key, "label": key, "unit": "", "qualifier": ""}


def series_for(result: SweepResult, key: str) -> tuple[tuple[dict, ...], ...]:
    """A quantity against O/F, split into runs of consecutive solved points.

    Returned as a tuple of segments rather than one list of points. A chart
    draws each segment as its own polyline, so a failed point becomes a gap
    instead of a straight line joining the values on either side of it -- which
    would draw physics nobody solved (Phase 5D §63, §73, §123).
    """
    segments: list[tuple[dict, ...]] = []
    current: list[dict] = []
    for point in result.points:
        value = point.value_of(key)
        if point.ok and math.isfinite(value):
            current.append({"x": float(point.oxidiser_fuel_ratio), "y": value})
        elif current:
            segments.append(tuple(current))
            current = []
    if current:
        segments.append(tuple(current))
    return tuple(segments)


def species_series_for(result: SweepResult, name: str,
                       basis: str = "mole") -> tuple[tuple[dict, ...], ...]:
    """One species' fraction against O/F, on the stated basis.

    A species absent from a converged point's composition is a genuine zero for
    that point -- the equilibrium contains none of it -- and is plotted as zero
    rather than dropped. A *failed* point still breaks the line.
    """
    from rocketforge.physics.thermochemistry import CompositionBasis
    from .thermochemistry_service import species_table

    target = (CompositionBasis.MASS_FRACTION if basis == "mass"
              else CompositionBasis.MOLE_FRACTION)
    segments: list[tuple[dict, ...]] = []
    current: list[dict] = []
    species: dict[str, Any] = {}
    for point in result.points:
        state = point.outcome.state
        if state is None:
            if current:
                segments.append(tuple(current))
                current = []
            continue
        if not species:
            species = species_table(point.outcome)
        composition = state.composition.to_basis(target, species)
        fraction = float(dict(composition.fractions).get(name, 0.0))
        current.append({"x": float(point.oxidiser_fuel_ratio), "y": fraction})
    if current:
        segments.append(tuple(current))
    return tuple(segments)


def species_in_sweep(result: SweepResult) -> tuple[str, ...]:
    """Every species name any solved point of the sweep contains.

    Ordered by the largest mole fraction the species reaches anywhere in the
    sweep, so the selectable list starts with the species that actually matter
    for this propellant pair rather than in alphabetical order.
    """
    peak: dict[str, float] = {}
    for point in result.points:
        state = point.outcome.state
        if state is None:
            continue
        for name, fraction in state.composition.fractions.items():
            value = float(fraction)
            if value > peak.get(name, 0.0):
                peak[name] = value
    return tuple(name for name, _ in
                 sorted(peak.items(), key=lambda item: (-item[1], item[0])))


#: The sweep table's columns. ``status`` is text; everything else is numeric
#: and is stored as a number, so a copied or exported table carries values
#: rather than rendered strings.
def sweep_columns() -> tuple[dict, ...]:
    return (
        {"key": "of", "label": "O/F", "unit": "", "kind": "number",
         "decimals_hint": 4},
        {"key": "temperature", "label": "T₀ [K]", "unit": "K", "kind": "number",
         "decimals_hint": 6},
        {"key": "molar_mass", "label": "M̄ [kg/mol]", "unit": "kg/mol",
         "kind": "number", "decimals_hint": 6},
        {"key": "gamma", "label": "γ_s", "unit": "", "kind": "number",
         "decimals_hint": 6},
        {"key": "density", "label": "ρ [kg/m³]", "unit": "kg/m³",
         "kind": "number", "decimals_hint": 6},
        {"key": "gas_constant", "label": "R [J/(kg·K)]", "unit": "J/(kg·K)",
         "kind": "number", "decimals_hint": 6},
        {"key": "cp", "label": "c_p [J/(kg·K)]", "unit": "J/(kg·K)",
         "kind": "number", "decimals_hint": 6},
        {"key": "cv", "label": "c_v [J/(kg·K)]", "unit": "J/(kg·K)",
         "kind": "number", "decimals_hint": 6},
        {"key": "status", "label": "Status", "unit": "", "kind": "text",
         "align": "left"},
    )


_STATUS_TEXT = {
    OUTCOME_OK: "solved",
    OUTCOME_WARNING: "warning",
}


def sweep_rows(result: SweepResult) -> tuple[tuple, ...]:
    """The sweep as table rows, ascending in O/F, failures included.

    A failed point contributes a row of NaN with its status text, which the
    table renders as em dashes. It is never dropped, and never filled with a
    neighbouring value.
    """
    rows: list[tuple] = []
    for point in result.points:
        rows.append((
            float(point.oxidiser_fuel_ratio),
            point.value_of("temperature"),
            point.value_of("molar_mass"),
            point.value_of("gamma"),
            point.value_of("density"),
            point.value_of("gas_constant"),
            point.value_of("cp"),
            point.value_of("cv"),
            _STATUS_TEXT.get(point.kind, point.outcome.status_label.lower()),
        ))
    return tuple(rows)


# ---------------------------------------------------------------------------
# warnings and extrema
# ---------------------------------------------------------------------------


def aggregated_warnings(result: SweepResult) -> tuple[dict, ...]:
    """Repeated provider warnings, collapsed to one row each.

    Each row names the diagnostic, how many points carried it, and the O/F
    range over which it applied, and keeps one representative message. The
    per-point diagnostics are untouched and remain reachable from the point
    itself.
    """
    from rocketforge.core.result import Severity

    buckets: dict[str, dict] = {}
    for point in result.points:
        for diagnostic in point.outcome.diagnostics:
            if diagnostic.severity is Severity.INFO:
                continue
            bucket = buckets.setdefault(diagnostic.code, {
                "code": diagnostic.code,
                "severity": str(diagnostic.severity),
                "message": diagnostic.message,
                "count": 0,
                "first": point.oxidiser_fuel_ratio,
                "last": point.oxidiser_fuel_ratio,
            })
            bucket["count"] += 1
            bucket["last"] = point.oxidiser_fuel_ratio
    total = len(result.points)
    for bucket in buckets.values():
        bucket["applies_to_all"] = bucket["count"] == total
        bucket["range_text"] = (
            f"all {total} points" if bucket["count"] == total
            else f"{bucket['count']} of {total} points, "
                 f"O/F {bucket['first']:g} to {bucket['last']:g}")
    return tuple(sorted(buckets.values(), key=lambda b: b["code"]))


def maximum_in_range(result: SweepResult, key: str) -> dict | None:
    """The largest sampled value of a quantity, and where it occurred.

    Deliberately named for what it is. This is the maximum **in the sampled
    interval**, on this grid, for this quantity -- not an optimum, not a
    recommendation, and not necessarily where any other quantity peaks
    (Phase 5D §12, §77).
    """
    best: dict | None = None
    for point in result.points:
        value = point.value_of(key)
        if not point.ok or not math.isfinite(value):
            continue
        if best is None or value > best["value"]:
            best = {"of": float(point.oxidiser_fuel_ratio), "value": value,
                    "key": key}
    return best
