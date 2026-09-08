"""The study definition: everything a study is, before it runs.

Immutable, fingerprintable, and validated up front. "Up front" is the design
decision: a study that would produce 400 rows of em dashes because its
objective refers to a metric the model cannot produce should be refused while
it is still a form, not discovered after several minutes of chemistry.

The baseline is a snapshot. Once a study exists it stops following the
workspace it was created from -- otherwise editing the Thermochemistry tab
would silently relabel a completed study with conditions that did not produce
it, which is the same defect Phase 5D and 5E each had to design against.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .constraints import ConstraintDefinition
from .enumeration import DesignPoint, enumerate_points, point_count, unique_stage_keys
from .metrics import MetricRegistry
from .objectives import ObjectiveDefinition
from .scoring import WeightedScoreDefinition
from .variables import DesignVariable

__all__ = [
    "MAX_STUDY_POINTS",
    "LARGE_STUDY_POINTS",
    "StudyBaseline",
    "StudyDefinition",
    "StudyValidationError",
    "validate_definition",
]

#: The hard ceiling on design points in one study.
#:
#: Chosen from measurement, not taste. ``experiments/phase_5f/
#: point_cap_benchmark.py`` times the generic layer alone -- enumeration,
#: constraints, the O(N^2) Pareto pass and scoring -- against an arithmetic
#: evaluator, so no provider time is mixed in
#: (``acceptance/phase_5f/study_performance.json``):
#:
#: ===========  =========  ============  ==========  =========
#: points       total s    decision s    pareto s    peak MB
#: ===========  =========  ============  ==========  =========
#: 1 000        0.080      0.010         0.006       1.6
#: 10 000       1.53       0.227         0.263       16.5
#: **20 000**   **4.73**   **0.682**     **0.456**   **33.1**
#: 40 000       14.44      2.274         1.878       66.6
#: ===========  =========  ============  ==========  =========
#:
#: Doubling from 20 000 to 40 000 triples the total: that is the quadratic
#: Pareto term turning, and it is what sets the ceiling. At 20 000 the whole
#: decision pass is under a second and memory is 33 MB, which a table model
#: publishes without stalling. A repeat run at the cap peaks at the same
#: 33.08 MB, so nothing accumulates between studies.
#:
#: A study larger than this is better expressed as several with a narrower
#: question each. The cap is a guard, not an optimisation: exceeding it refuses
#: the definition and says by how much, rather than silently sampling a subset.
MAX_STUDY_POINTS = 20_000

#: Above this, the workspace warns before running. Non-blocking.
#:
#: Set where the unique-solve preview starts to matter: a thousand points may
#: be a hundred chamber solves or a thousand, and those are very different
#: waits. The warning shows both numbers rather than a spinner.
LARGE_STUDY_POINTS = 1_000


class StudyValidationError(ValueError):
    """A study definition that cannot be run, with the reason and its code."""

    def __init__(self, code: str, message: str, *, field: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.code}: {self.message}"


@dataclass(frozen=True, slots=True)
class StudyBaseline:
    """Everything held fixed for the whole study.

    Opaque to this layer: a mapping of canonical values plus a model record.
    The generic engine never interprets it, it only fingerprints it and passes
    it to the evaluator, which is what keeps this package free of any idea of
    what a propellant is.

    ``model`` is separated from ``conditions`` because the two fail differently.
    Changing a condition makes a different study; changing the model makes a
    study whose numbers are not comparable with the previous one at all.
    """

    conditions: Mapping[str, Any] = field(default_factory=dict)
    model: Mapping[str, Any] = field(default_factory=dict)
    label: str = ""

    def canonical(self) -> dict[str, Any]:
        return {"conditions": _canonical(self.conditions),
                "model": _canonical(self.model)}


def _canonical(value: Any) -> Any:
    """A JSON-shaped, order-independent form of a value.

    Mappings are sorted by key so that two definitions built in different
    orders fingerprint identically -- the order a form's fields were populated
    in is not a scientific difference.
    """
    if isinstance(value, Mapping):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        return float(value)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


@dataclass(frozen=True, slots=True)
class StudyDefinition:
    """One trade study, fully specified and independent of any interface.

    Attributes:
        baseline: What is held fixed, snapshotted at creation.
        variables: What varies. Order is the enumeration order.
        stage_order: The evaluation stages, cheapest-dependency first. The
            generic layer only knows they are ordered; the domain names them.
        outputs: Metric keys to report. Objectives and constraints add their
            own, so this is what the user wants *in addition*.
        objectives: What the study is trying to do. May be empty -- a purely
            exploratory study is a valid study.
        constraints: Hard limits. May be empty.
        scoring: Optional, and off unless explicitly supplied.
    """

    baseline: StudyBaseline
    variables: tuple[DesignVariable, ...]
    stage_order: tuple[str, ...]
    outputs: tuple[str, ...] = ()
    objectives: tuple[ObjectiveDefinition, ...] = ()
    constraints: tuple[ConstraintDefinition, ...] = ()
    scoring: WeightedScoreDefinition | None = None
    title: str = ""

    @property
    def point_count(self) -> int:
        return point_count(self.variables)

    @property
    def required_metrics(self) -> tuple[str, ...]:
        """Every metric the study must produce, deduplicated, in a stable order.

        Outputs first, then objectives, then constraints -- so the display
        order of a results table follows what the user asked to see rather
        than what the machinery happened to need.
        """
        seen: dict[str, None] = {}
        for key in self.outputs:
            seen.setdefault(key, None)
        for objective in self.objectives:
            seen.setdefault(objective.metric, None)
        for constraint in self.constraints:
            seen.setdefault(constraint.metric, None)
        return tuple(seen)

    def required_stages(self, registry: MetricRegistry) -> tuple[str, ...]:
        """The stages that must run, in study order.

        A chamber-temperature study stops after the chemistry stage: no
        performance evaluation runs at all, because nothing asked for a number
        that stage produces.
        """
        needed = {registry[key].stage for key in self.required_metrics
                  if key in registry}
        if not needed:
            return (self.stage_order[0],) if self.stage_order else ()
        deepest = max(self.stage_order.index(stage) for stage in needed
                      if stage in self.stage_order)
        return tuple(self.stage_order[: deepest + 1])

    def variables_at(self, stage: str) -> tuple[DesignVariable, ...]:
        return tuple(v for v in self.variables if v.stage == stage)

    def enumerate(self) -> tuple[DesignPoint, ...]:
        return enumerate_points(self.variables)

    def unique_solves(self, stage: str) -> int:
        """How many distinct evaluations that stage will need.

        The number the workload preview shows beside the point count, and the
        number the whole dependency planner exists to keep small. Computed by
        multiplying the cardinalities of the variables at or before this stage
        -- no enumeration, so a 400 000-point preview costs nothing.
        """
        try:
            limit = self.stage_order.index(stage)
        except ValueError:
            raise ValueError(
                f"stage {stage!r} is not in {self.stage_order}") from None
        order = {name: position for position, name in enumerate(self.stage_order)}
        total = 1
        for variable in self.variables:
            if order.get(variable.stage, len(order)) <= limit:
                total *= variable.count
        return total

    def unique_stage_keys(self, stage: str):
        return unique_stage_keys(self.enumerate(), self.variables,
                                 self.stage_order, stage)

    def canonical(self) -> dict[str, Any]:
        """The scientifically meaningful content, in a deterministic shape.

        Excludes the title and every display concern: renaming a study does not
        make it a different study, and the fingerprint must agree.
        """
        return {
            "baseline": self.baseline.canonical(),
            "stage_order": list(self.stage_order),
            "variables": [variable.canonical() for variable in self.variables],
            "outputs": sorted(self.outputs),
            "objectives": [objective.canonical() for objective in self.objectives],
            "constraints": sorted(
                (constraint.canonical() for constraint in self.constraints),
                key=lambda entry: (entry["metric"], entry["operator"],
                                   entry["limit"])),
            "scoring": self.scoring.canonical() if self.scoring else None,
        }

    @property
    def fingerprint(self) -> str:
        """A stable digest of the scientific definition.

        Changes when the study changes; does not change when the title, the
        clock or a display unit does. Used to tell a re-run from a new study,
        and to label an artifact with the definition that produced it.
        """
        payload = json.dumps(self.canonical(), sort_keys=True,
                             separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def replace(self, **changes: Any) -> "StudyDefinition":
        from dataclasses import replace as _replace

        return _replace(self, **changes)


def validate_definition(definition: StudyDefinition,
                        registry: MetricRegistry,
                        *, scale_available: bool = True,
                        max_points: int = MAX_STUDY_POINTS) -> None:
    """Refuse a study that cannot produce a meaningful answer.

    Raises ``StudyValidationError`` with a stable code. Every check here exists
    because the alternative is discovering the problem after the chemistry has
    run.
    """
    if not definition.stage_order:
        raise StudyValidationError(
            "NO_STAGE_ORDER", "a study needs at least one evaluation stage")

    keys = [variable.key for variable in definition.variables]
    if len(set(keys)) != len(keys):
        duplicated = sorted({key for key in keys if keys.count(key) > 1})
        raise StudyValidationError(
            "DUPLICATE_DESIGN_VARIABLE",
            f"the same variable appears more than once: {', '.join(duplicated)}")

    for variable in definition.variables:
        if variable.stage not in definition.stage_order:
            raise StudyValidationError(
                "UNKNOWN_VARIABLE_STAGE",
                f"variable {variable.key!r} declares stage {variable.stage!r}, "
                f"which is not one of {definition.stage_order}",
                field=variable.key)
        if variable.count == 0:
            raise StudyValidationError(
                "EMPTY_DESIGN_VARIABLE",
                f"variable {variable.key!r} has no values to study",
                field=variable.key)

    if not definition.required_metrics:
        raise StudyValidationError(
            "NO_REQUESTED_METRICS",
            "a study must request at least one output, objective or constraint; "
            "otherwise it evaluates points and reports nothing about them")

    for key in definition.required_metrics:
        metric = registry.get(key)
        if metric is None:
            raise StudyValidationError(
                "UNKNOWN_METRIC",
                f"no metric named {key!r}. Known metrics: "
                f"{', '.join(sorted(registry.keys))}", field=key)
        if metric.requires_scale and not scale_available:
            raise StudyValidationError(
                "METRIC_REQUIRES_SCALE",
                f"{metric.label} needs an absolute engine size, and this "
                "study's baseline has none. Set a throat area or mass flow, or "
                "remove it — a column of blanks is not an answer.", field=key)

    objective_metrics = [objective.metric for objective in definition.objectives]
    if len(set(objective_metrics)) != len(objective_metrics):
        raise StudyValidationError(
            "DUPLICATE_OBJECTIVE",
            "the same metric appears as an objective more than once; if two "
            "directions were intended, they contradict each other")

    if definition.scoring is not None:
        if not definition.objectives:
            raise StudyValidationError(
                "SCORING_WITHOUT_OBJECTIVES",
                "a weighted score combines objectives, and this study has none")
        unknown = sorted(set(definition.scoring.weights) - set(objective_metrics))
        if unknown:
            raise StudyValidationError(
                "SCORE_WEIGHT_WITHOUT_OBJECTIVE",
                f"weights refer to metrics that are not objectives: "
                f"{', '.join(unknown)}")
        missing = sorted(set(objective_metrics) - set(definition.scoring.weights))
        if missing:
            raise StudyValidationError(
                "OBJECTIVE_WITHOUT_SCORE_WEIGHT",
                f"objectives with no weight: {', '.join(missing)}. An omitted "
                "weight is an invisible zero; state it.")

    total = definition.point_count
    if total > max_points:
        raise StudyValidationError(
            "STUDY_TOO_LARGE",
            f"{total:,} design points exceeds the {max_points:,}-point limit. "
            "Narrow a range or reduce a count — the study is not sampled down "
            "silently.")

    _validate_effective_variables(definition, registry)


def _validate_effective_variables(definition: StudyDefinition,
                                  registry: MetricRegistry) -> None:
    """Refuse a variable that cannot affect anything the study reports.

    Varying an area ratio in a study whose only output is chamber temperature
    produces N identical rows. That is not a null result, it is a
    misunderstanding of the model, and generating the rows anyway would confirm
    it -- the flat line reads as "area ratio does not matter much" rather than
    "area ratio was never in this calculation".
    """
    required_stages = set(definition.required_stages(registry))
    if not required_stages:
        return
    order = {name: position for position, name in enumerate(definition.stage_order)}
    deepest = max(order[stage] for stage in required_stages if stage in order)

    for variable in definition.variables:
        position = order.get(variable.stage)
        if position is None or variable.count <= 1:
            continue
        if position > deepest:
            produced = sorted(definition.required_metrics)
            raise StudyValidationError(
                "INEFFECTIVE_DESIGN_VARIABLE",
                f"{variable.label} is evaluated at the {variable.stage!r} "
                f"stage, but this study only requires results up to the "
                f"{definition.stage_order[deepest]!r} stage "
                f"({', '.join(produced)}). Varying it would produce "
                f"{variable.count} identical rows. Add a metric it affects, or "
                "remove it.",
                field=variable.key)
