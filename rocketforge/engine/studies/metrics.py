"""The metric registry: what a study can output, constrain or optimise.

A metric is a name a study definition may refer to. The registry says what that
name means -- its unit, which evaluation stage produces it, and what has to
have succeeded for it to exist -- so that a study asking for something the
model cannot produce is refused while it is still a definition, rather than
producing several hundred points with a column of em dashes.

This layer registers no metric of its own. It is the domain's business what
"specific_impulse" is; this module only guarantees that the name resolves, that
its stage is known, and that nothing asks for it without the stage that
produces it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

__all__ = ["MetricDefinition", "MetricRegistry"]


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """One quantity a study can report on.

    Attributes:
        key: The stable identifier a study definition refers to.
        label: What a person reads.
        unit: The canonical unit. Empty for dimensionless.
        stage: Which evaluation stage produces it. A study requesting this
            metric must run at least that far.
        requires_scale: Whether the metric needs an absolute engine size.
            Thrust and mass flow do; c*, Cf and Isp do not. A study asking for
            one of these without a size is refused at definition time rather
            than filled with nulls.
        help: One sentence for a tooltip. Prose lives with the definition so
            two views cannot describe the same metric differently.
        higher_is_better: Deliberately absent. Direction belongs to an explicit
            ObjectiveDefinition, never to the metric -- "higher Isp is better"
            is false the moment a study is trading it against chamber
            temperature.
    """

    key: str
    label: str
    stage: str
    unit: str = ""
    requires_scale: bool = False
    help: str = ""
    decimals_hint: int = 6

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise ValueError("a metric needs a non-empty key")
        if not self.stage or not self.stage.strip():
            raise ValueError(f"metric {self.key!r} needs a stage")


class MetricRegistry:
    """The set of metrics one domain offers, keyed by identifier.

    Immutable once built. A study holds the keys it uses and the registry
    resolves them, so a metric that is renamed breaks loudly at definition
    validation instead of silently producing an empty column.
    """

    __slots__ = ("_metrics",)

    def __init__(self, metrics: Iterable[MetricDefinition] = ()) -> None:
        table: dict[str, MetricDefinition] = {}
        for metric in metrics:
            if metric.key in table:
                raise ValueError(f"metric {metric.key!r} registered twice")
            table[metric.key] = metric
        self._metrics = table

    def __contains__(self, key: object) -> bool:
        return key in self._metrics

    def __iter__(self) -> Iterator[MetricDefinition]:
        return iter(self._metrics.values())

    def __len__(self) -> int:
        return len(self._metrics)

    def __getitem__(self, key: str) -> MetricDefinition:
        try:
            return self._metrics[key]
        except KeyError:
            raise KeyError(
                f"no metric named {key!r}. Known metrics: "
                f"{', '.join(sorted(self._metrics))}") from None

    def get(self, key: str) -> MetricDefinition | None:
        return self._metrics.get(key)

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(self._metrics)

    def for_stage(self, stage: str) -> tuple[MetricDefinition, ...]:
        return tuple(m for m in self._metrics.values() if m.stage == stage)

    def stages_required(self, keys: Iterable[str]) -> set[str]:
        """The stages that must run to produce these metrics.

        This is what lets a chamber-temperature-only study skip the
        performance solve entirely rather than computing an Isp nobody asked
        for.
        """
        return {self[key].stage for key in keys}

    def with_metrics(self, metrics: Iterable[MetricDefinition]) -> "MetricRegistry":
        """A new registry with more metrics. The original is unchanged."""
        return MetricRegistry(list(self._metrics.values()) + list(metrics))
