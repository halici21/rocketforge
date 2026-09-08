"""Optional weighted scoring.

Off unless a user turns it on. A score is a way of collapsing several
objectives into one number so a list can be sorted, and collapsing is a
decision -- doing it automatically because a study happens to have two
objectives would be making that decision on the user's behalf and then hiding
it behind a column heading.

Three properties this module is careful about:

**A score is study-relative.** Min-max normalisation is taken over the feasible
evaluated points of *this* study, so the same physical design scores
differently in a different population. That is a real property of the method,
not an implementation detail, and it is stated wherever a score is shown.

**A score never touches Pareto.** Dominance is computed from the objective
vectors and knows nothing about weights. Changing every weight leaves the front
byte-identical, and a test asserts it.

**A score never touches feasibility.** An infeasible point does not receive a
penalised score; it remains infeasible and is not scored at all.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from .objectives import ObjectiveDefinition, ObjectiveDirection

__all__ = [
    "NormalizationMethod",
    "WeightedScoreDefinition",
    "normalize_objective",
    "score_points",
    "ZERO_SPAN_COMPONENT",
]

#: What a normalised component becomes when an objective has no spread.
#:
#: If every feasible point shares one chamber temperature, that objective
#: cannot discriminate between them, and any constant leaves the ranking
#: decided entirely by the other objectives. One is chosen over zero so a
#: single-objective zero-span study scores 1.0 rather than 0.0 -- "all equally
#: good" reads better than "all worthless", and neither changes an order.
ZERO_SPAN_COMPONENT = 1.0


class NormalizationMethod(StrEnum):
    """How raw objective values are made comparable.

    One method in v1, named explicitly rather than left implicit, so that
    adding a second later is a visible change to every stored study rather
    than a silent change of meaning.
    """

    MIN_MAX_OVER_FEASIBLE = "min_max_over_feasible"

    @property
    def label(self) -> str:
        return "Min–max over the feasible evaluated points"


@dataclass(frozen=True, slots=True)
class WeightedScoreDefinition:
    """Weights over objectives, plus the normalisation they are applied to.

    Weights are validated but **not** rewritten: the user's numbers are stored
    as given, and the normalised weights actually used are exposed separately
    so both are visible. Silently rescaling the input would make the form and
    the result disagree.
    """

    weights: Mapping[str, float]
    method: NormalizationMethod = NormalizationMethod.MIN_MAX_OVER_FEASIBLE

    def __post_init__(self) -> None:
        if not self.weights:
            raise ValueError("a weighted score needs at least one weight")
        total = 0.0
        for metric, weight in self.weights.items():
            number = float(weight)
            if not math.isfinite(number):
                raise ValueError(
                    f"weight for {metric!r} must be finite, got {weight!r}")
            if number < 0.0:
                raise ValueError(
                    f"weight for {metric!r} must be at or above zero, got "
                    f"{weight!r}. A negative weight is a reversed objective "
                    "direction wearing a disguise; set the direction instead.")
            total += number
        if total <= 0.0:
            raise ValueError(
                "at least one weight must be above zero, or the score is the "
                "same number for every design")

    @property
    def total_weight(self) -> float:
        return sum(float(weight) for weight in self.weights.values())

    @property
    def effective_weights(self) -> dict[str, float]:
        """The weights actually applied, normalised to sum to one.

        Exposed rather than kept internal: a user who typed 3 and 1 should be
        able to see that the score used 0.75 and 0.25.
        """
        total = self.total_weight
        return {metric: float(weight) / total
                for metric, weight in self.weights.items()}

    def canonical(self) -> dict[str, object]:
        return {"method": self.method.value,
                "weights": {key: float(value)
                            for key, value in sorted(self.weights.items())}}


def normalize_objective(values: Sequence[float],
                        objective: ObjectiveDefinition) -> tuple[float, ...]:
    """Map raw values onto [0, 1], with 1 always meaning better.

    For MAXIMIZE: ``(x − min) / (max − min)``.
    For MINIMIZE: ``(max − x) / (max − min)``.

    Both directions therefore produce "1 is the best of this population", which
    is what lets a weighted sum add them together without a sign convention
    nobody remembers.
    """
    numbers = [float(value) for value in values]
    if not numbers:
        return ()
    low, high = min(numbers), max(numbers)
    span = high - low
    if span == 0.0:
        return tuple(ZERO_SPAN_COMPONENT for _ in numbers)
    if objective.direction is ObjectiveDirection.MAXIMIZE:
        return tuple((value - low) / span for value in numbers)
    return tuple((high - value) / span for value in numbers)


def score_points(entries: Sequence[tuple[int, Mapping[str, float | None]]],
                 objectives: Sequence[ObjectiveDefinition],
                 definition: WeightedScoreDefinition) -> dict[int, float]:
    """Weighted scores for the scorable points.

    ``entries`` is ``(index, metrics)`` for the **feasible evaluated** points;
    the caller has already excluded the rest, because only the caller knows
    what failed and what violated a constraint.

    A point missing any objective value is not scored -- it is absent from the
    result rather than scored as zero, which would rank an unevaluable design
    above a merely poor one.
    """
    if not objectives:
        return {}

    usable: list[int] = []
    columns: dict[str, list[float]] = {objective.metric: []
                                       for objective in objectives}
    for index, metrics in entries:
        values = []
        for objective in objectives:
            value = metrics.get(objective.metric)
            if value is None or not math.isfinite(float(value)):
                values = []
                break
            values.append(float(value))
        if not values:
            continue
        usable.append(index)
        for objective, value in zip(objectives, values, strict=True):
            columns[objective.metric].append(value)

    if not usable:
        return {}

    weights = definition.effective_weights
    normalised = {objective.metric: normalize_objective(
                      columns[objective.metric], objective)
                  for objective in objectives}

    scores: dict[int, float] = {}
    for position, index in enumerate(usable):
        total = 0.0
        for objective in objectives:
            weight = weights.get(objective.metric, 0.0)
            total += weight * normalised[objective.metric][position]
        scores[index] = total
    return scores
