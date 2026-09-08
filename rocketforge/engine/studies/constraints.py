"""Hard constraints, and what makes them hard.

A constraint is satisfied or violated. It is never converted into a penalty
term, never softened by a tolerance the user did not ask for, and never allowed
to change a raw physics value. A point that violates one is **infeasible** --
still evaluated, still shown, still carrying every number it produced.

The penalty-function approach is deliberately absent. Turning "chamber
temperature exceeds 3500 K" into "score minus 0.3" produces a ranking in which
a design that cannot be built outranks one that can, and no amount of tuning
the coefficient fixes that: the two are different kinds of statement.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

__all__ = [
    "ComparisonOperator",
    "ConstraintDefinition",
    "ConstraintOutcome",
    "evaluate_constraints",
]


class ComparisonOperator(StrEnum):
    """The comparisons a hard constraint may make.

    ``EQ`` exists because a study may legitimately pin a categorical or an
    exactly-representable value, but it is not offered prominently: floating
    engineering quantities are almost never equal, and a user who reaches for
    it on a chamber temperature has usually meant ``<=``.
    """

    LE = "<="
    LT = "<"
    GE = ">="
    GT = ">"
    EQ = "=="

    def compare(self, value: float, limit: float) -> bool:
        """Plain float comparison. No hidden tolerance.

        A tolerance here would move a constraint the user typed. If a design
        needs a margin, the margin belongs in the limit, where it is visible.
        """
        if self is ComparisonOperator.LE:
            return value <= limit
        if self is ComparisonOperator.LT:
            return value < limit
        if self is ComparisonOperator.GE:
            return value >= limit
        if self is ComparisonOperator.GT:
            return value > limit
        return value == limit

    @property
    def label(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ConstraintDefinition:
    """One hard limit on one metric.

    ``limit`` is in the metric's canonical unit. Display units are converted at
    the application boundary; a constraint that stored "3500" without knowing
    whether that was kelvin or rankine would be a constraint nobody could
    reproduce.
    """

    metric: str
    operator: ComparisonOperator
    limit: float

    def __post_init__(self) -> None:
        if not self.metric or not self.metric.strip():
            raise ValueError("a constraint needs a metric key")
        if not isinstance(self.operator, ComparisonOperator):
            raise TypeError(
                f"constraint operator must be a ComparisonOperator, got "
                f"{self.operator!r}")
        if not math.isfinite(float(self.limit)):
            raise ValueError(
                f"constraint limit must be finite, got {self.limit!r}")

    def satisfied_by(self, value: float | None) -> bool | None:
        """Whether a value satisfies this. ``None`` when it cannot be judged.

        ``None`` is a third answer, not a failure: a metric that was never
        produced has not violated anything, and reporting it as violated would
        turn a model limitation into an engineering verdict.
        """
        if value is None:
            return None
        number = float(value)
        if not math.isfinite(number):
            return None
        return self.operator.compare(number, float(self.limit))

    def canonical(self) -> dict[str, object]:
        return {"metric": self.metric, "operator": self.operator.value,
                "limit": float(self.limit)}

    def describe(self) -> str:
        return f"{self.metric} {self.operator.value} {self.limit:g}"


@dataclass(frozen=True, slots=True)
class ConstraintOutcome:
    """One constraint checked against one point.

    Carries the actual value alongside the verdict, so an infeasible point can
    say *how* infeasible rather than only that it is. "3610 K > 3500 K limit"
    is actionable; "infeasible" is not.
    """

    constraint: ConstraintDefinition
    value: float | None
    satisfied: bool | None

    @property
    def judged(self) -> bool:
        return self.satisfied is not None

    @property
    def violated(self) -> bool:
        return self.satisfied is False

    def describe(self) -> str:
        if self.value is None or self.satisfied is None:
            return f"{self.constraint.metric}: not available"
        verb = "satisfies" if self.satisfied else "violates"
        return (f"{self.constraint.metric}: {self.value:g} {verb} "
                f"{self.constraint.operator.value} {self.constraint.limit:g}")


def evaluate_constraints(metrics: Mapping[str, float | None],
                         constraints: Sequence[ConstraintDefinition]
                         ) -> tuple[ConstraintOutcome, ...]:
    """Check every constraint against one point's metrics.

    Every constraint produces an outcome, including the ones whose metric is
    missing. Dropping those would make an unjudgeable point look feasible.
    """
    return tuple(
        ConstraintOutcome(constraint=constraint,
                          value=(None if metrics.get(constraint.metric) is None
                                 else float(metrics[constraint.metric])),
                          satisfied=constraint.satisfied_by(
                              metrics.get(constraint.metric)))
        for constraint in constraints)
