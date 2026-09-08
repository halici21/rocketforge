"""Objectives: which metric, and which direction.

The direction is always explicit. Nothing here infers that a higher specific
impulse is better, because that is false the moment the same study is trading
it against chamber temperature or against a mass the model does not carry. A
metric is a number; wanting more of it is a decision, and decisions are
recorded rather than assumed.

An objective changes no physics. Flipping MAXIMIZE to MINIMIZE re-sorts a
column and nothing else -- a property this package guarantees structurally, by
never giving the decision layer a way to reach an evaluator.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

__all__ = ["ObjectiveDirection", "ObjectiveDefinition", "rank_by_objective"]


class ObjectiveDirection(StrEnum):
    """Which way is better. Stated, never inferred from the metric name."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"

    @property
    def label(self) -> str:
        return "Maximize" if self is ObjectiveDirection.MAXIMIZE else "Minimize"


@dataclass(frozen=True, slots=True)
class ObjectiveDefinition:
    """One thing a study is trying to do more, or less, of."""

    metric: str
    direction: ObjectiveDirection

    def __post_init__(self) -> None:
        if not self.metric or not self.metric.strip():
            raise ValueError("an objective needs a metric key")
        if not isinstance(self.direction, ObjectiveDirection):
            raise TypeError(
                f"objective direction must be an ObjectiveDirection, got "
                f"{self.direction!r}. It is never inferred from the metric.")

    def is_better(self, candidate: float, incumbent: float) -> bool:
        """Whether ``candidate`` is strictly preferable to ``incumbent``."""
        if self.direction is ObjectiveDirection.MAXIMIZE:
            return candidate > incumbent
        return candidate < incumbent

    def is_at_least_as_good(self, candidate: float, incumbent: float) -> bool:
        if self.direction is ObjectiveDirection.MAXIMIZE:
            return candidate >= incumbent
        return candidate <= incumbent

    def canonical(self) -> dict[str, str]:
        return {"metric": self.metric, "direction": self.direction.value}

    def describe(self) -> str:
        return f"{self.direction.label} {self.metric}"


def rank_by_objective(values: Sequence[tuple[int, float]],
                      objective: ObjectiveDefinition
                      ) -> tuple[tuple[int, float], ...]:
    """Rank ``(index, value)`` pairs best-first for one objective.

    Used when a study has exactly one objective, where a Pareto front would be
    a misleading name for "the single best point". Ties keep enumeration order,
    so a re-run ranks identical designs identically.

    Non-finite values are dropped rather than sorted: a NaN compares false
    against everything and would land wherever the sort happened to put it.
    """
    finite = [(index, float(value)) for index, value in values
              if value is not None and math.isfinite(float(value))]
    reverse = objective.direction is ObjectiveDirection.MAXIMIZE
    finite.sort(key=lambda entry: (entry[1], -entry[0]), reverse=reverse)
    return tuple(finite)
