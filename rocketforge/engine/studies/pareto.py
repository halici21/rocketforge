"""Pareto nondominance over evaluated, feasible points.

One front, not a ranked series of them. The first nondominated set answers the
question a trade study actually asks -- "which of these designs is not beaten
outright by another" -- and NSGA-style ranks would be machinery for an
optimiser this phase deliberately does not contain.

Three exclusions, each for a different reason:

* **failed points** have no objective vector to compare;
* **infeasible points** are not designs anyone may choose, so letting one
  dominate a feasible design would remove a buildable option in favour of an
  unbuildable one;
* **non-finite values** compare false against everything, and a NaN silently
  becomes nondominated because nothing can beat it.

The score never enters. Dominance is a property of the objective vectors, and
a weighted sum is a different question asked later with different information.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .objectives import ObjectiveDefinition

__all__ = ["pareto_membership", "pareto_front", "dominates"]


def _vector(metrics: Mapping[str, float | None],
            objectives: Sequence[ObjectiveDefinition]) -> tuple[float, ...] | None:
    """The objective values for one point, or None if any is unusable."""
    values: list[float] = []
    for objective in objectives:
        value = metrics.get(objective.metric)
        if value is None:
            return None
        number = float(value)
        if not math.isfinite(number):
            return None
        values.append(number)
    return tuple(values)


def dominates(first: Sequence[float], second: Sequence[float],
              objectives: Sequence[ObjectiveDefinition]) -> bool:
    """Whether ``first`` dominates ``second``.

    No worse on every objective, and strictly better on at least one, after
    respecting each objective's own direction. The "strictly better on at least
    one" is what stops two identical vectors from dominating each other, which
    would empty the front of every duplicated design.
    """
    strictly_better = False
    for objective, a, b in zip(objectives, first, second, strict=True):
        if not objective.is_at_least_as_good(a, b):
            return False
        if objective.is_better(a, b):
            strictly_better = True
    return strictly_better


def pareto_membership(entries: Sequence[tuple[int, Mapping[str, float | None]]],
                      objectives: Sequence[ObjectiveDefinition]
                      ) -> dict[int, bool]:
    """Which of the given points are nondominated.

    ``entries`` is ``(index, metrics)`` for the points **eligible** to be on the
    front -- the caller has already excluded failed and infeasible ones, since
    only the caller knows what those mean.

    Every eligible index appears in the result, so a caller cannot silently
    lose a point by looking up a key that is absent. A point whose objective
    vector is unusable is present and False.

    Ties: identical vectors do not dominate each other, so all of them are on
    the front. Deterministic, and the honest answer -- picking one duplicate to
    keep would hide that the study found several equally good designs.
    """
    if not objectives:
        return {index: False for index, _ in entries}

    vectors: dict[int, tuple[float, ...]] = {}
    membership: dict[int, bool] = {}
    for index, metrics in entries:
        vector = _vector(metrics, objectives)
        membership[index] = False
        if vector is not None:
            vectors[index] = vector

    # O(N^2). Measured rather than assumed: at the study sizes this phase
    # permits it costs milliseconds, and a smarter algorithm would be more code
    # to get wrong for no observable gain.
    items = list(vectors.items())
    for index, vector in items:
        if not any(dominates(other, vector, objectives)
                   for other_index, other in items if other_index != index):
            membership[index] = True
    return membership


def pareto_front(entries: Sequence[tuple[int, Mapping[str, float | None]]],
                 objectives: Sequence[ObjectiveDefinition]) -> tuple[int, ...]:
    """The indices of the nondominated points, in enumeration order."""
    membership = pareto_membership(entries, objectives)
    return tuple(index for index, _ in entries if membership.get(index))
