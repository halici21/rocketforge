"""Point enumeration and stage keys.

The Cartesian product, in a documented order, plus the one thing the whole
solve-reuse guarantee rests on: a **stage key** that contains exactly the
variables an evaluation stage depends on, and nothing else.

If an area ratio ever appeared in the chemistry stage key, 410 design points
would become 410 chamber solves instead of 41. So the key is built from the
variables' declared stages rather than from a list someone maintains by hand,
and a test asserts that changing a downstream variable leaves the upstream key
identical.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from typing import Any

from .variables import DesignVariable

__all__ = ["DesignPoint", "enumerate_points", "point_count", "stage_key"]


@dataclass(frozen=True, slots=True)
class DesignPoint:
    """One combination of design-variable values.

    ``index`` is the point's identity for the whole life of a study: it is
    stable, it is the default display order, and a sorted table still refers
    back to it. ``values`` is keyed by variable key, never by position.
    """

    index: int
    values: Mapping[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def describe(self, variables: Sequence[DesignVariable]) -> str:
        parts = []
        for variable in variables:
            value = self.values.get(variable.key)
            if value is None:
                continue
            unit = f" {variable.unit}" if variable.unit else ""
            shown = f"{value:g}" if isinstance(value, (int, float)) else str(value)
            parts.append(f"{variable.label} {shown}{unit}")
        return " · ".join(parts)


def point_count(variables: Sequence[DesignVariable]) -> int:
    """How many points the product will contain. Computed without building it.

    Needed before anything runs: the preview has to be able to say "412 000
    points" without enumerating 412 000 points to find out.
    """
    total = 1
    for variable in variables:
        total *= variable.count
    return total


def enumerate_points(variables: Sequence[DesignVariable]) -> tuple[DesignPoint, ...]:
    """The Cartesian product, in a stable documented order.

    **Order.** The first variable in the definition varies slowest and the last
    varies fastest -- odometer order, the same as ``itertools.product``. Chosen
    because it puts the upstream variables outermost when they are declared
    first, so a table read top to bottom walks the chemistry states in order
    rather than interleaving them.

    Ordering is part of the contract: a study re-run must produce the same
    point at the same index, or a stored index refers to a different design.
    """
    if not variables:
        return (DesignPoint(index=0, values={}),)
    keys = [variable.key for variable in variables]
    value_lists = [variable.values for variable in variables]
    points = []
    for index, combination in enumerate(product(*value_lists)):
        points.append(DesignPoint(
            index=index,
            values=dict(zip(keys, combination, strict=True))))
    return tuple(points)


def stage_key(point: DesignPoint,
              variables: Sequence[DesignVariable],
              stage_order: Sequence[str],
              stage: str) -> tuple[tuple[str, Any], ...]:
    """The identity of one evaluation stage for one point.

    Contains the values of every variable at or before ``stage``, and nothing
    else. That "and nothing else" is the whole optimisation: an area ratio
    declared at the performance stage cannot appear in the chemistry key, so
    ten area ratios over one chamber state are one chamber solve.

    Sorted by variable key so the key is order-independent, and returned as a
    tuple of pairs so it is hashable and reads legibly in a failure message.
    """
    try:
        limit = list(stage_order).index(stage)
    except ValueError:
        raise ValueError(
            f"stage {stage!r} is not in the study's stage order "
            f"{tuple(stage_order)}") from None
    order = {name: position for position, name in enumerate(stage_order)}
    included = []
    for variable in variables:
        position = order.get(variable.stage)
        if position is None:
            raise ValueError(
                f"variable {variable.key!r} declares stage {variable.stage!r}, "
                f"which is not in the study's stage order {tuple(stage_order)}")
        if position <= limit:
            included.append((variable.key, point.values[variable.key]))
    included.sort(key=lambda entry: entry[0])
    return tuple(included)


def unique_stage_keys(points: Sequence[DesignPoint],
                      variables: Sequence[DesignVariable],
                      stage_order: Sequence[str],
                      stage: str) -> tuple[tuple[tuple[str, Any], ...], ...]:
    """Every distinct stage key, in first-appearance order.

    First-appearance rather than sorted, so the expensive stage runs in the
    same order the points do and a progress report advances monotonically
    through the table the user is looking at.
    """
    seen: dict[tuple, None] = {}
    for point in points:
        seen.setdefault(stage_key(point, variables, stage_order, stage), None)
    return tuple(seen)
