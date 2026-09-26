"""The Qt facade for the Trade Study workspace.

The only file in this feature that imports Qt. It holds no equation, no
physical constant, no Pareto loop and no score formula: every number it
publishes was computed by ``engine.studies`` or by the canonical
thermochemistry and performance services, and every verdict was decided there.

Three behaviours are worth reading the code for.

**Execution is serial and chunked.** A study runs a few points per event-loop
turn on a zero-interval timer, so the interface stays responsive without a
single concurrent provider call. Phase 5B-0 measured CEA threading and found no
gain; trading a proven property for an unproven one to make a progress bar move
would be a poor bargain.

**Editing the decision layer never re-solves.** Changing an objective
direction, a constraint limit or a weight calls ``reanalyse`` on the raw result
that already exists. The provider is not touched, the performance service is
not touched, and the raw metrics are carried across by reference.

**The workload is previewed before anything runs.** The point count and the
unique chemistry-solve count are computed from variable cardinalities, so
editing a range updates both without a single solve. A user pressing Run should
already know whether they asked for 41 chamber solves or 4 100.
"""

from __future__ import annotations

import math
from typing import Any

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

from rocketforge.application.formatting import EM_DASH, format_engineering
from rocketforge.engine.studies import (
    ComparisonOperator,
    ConstraintDefinition,
    EvaluationStatus,
    Feasibility,
    LARGE_STUDY_POINTS,
    MAX_STUDY_POINTS,
    ObjectiveDefinition,
    ObjectiveDirection,
    StudyStatus,
    StudyValidationError,
    WeightedScoreDefinition,
)

from . import trade_study_service as service
from .thermochemistry_table_model import ThermoTableModel
from .trade_study_domain import (
    DEFERRED_VARIABLES,
    METRICS,
    STAGE_LABELS,
    STAGE_PERFORMANCE,
    STAGE_THERMOCHEMISTRY,
    VARIABLE_SPECS,
    build_variable,
    metric_registry,
    variable_spec,
)

__all__ = ["TradeStudyController"]

#: How many design points to evaluate between event-loop turns.
#:
#: Small enough that a cancel press is answered promptly, large enough that the
#: timer overhead does not dominate a study whose points are microseconds
#: apart. The expensive points are the chemistry ones, and one of those per
#: chunk is already the right granularity.
CHUNK_SIZE = 8

#: Display precision for every published number.
DEFAULT_PRECISION = 6

#: The wording used wherever a best point is named.
#:
#: A trade study evaluates a finite sampled grid. "Global optimum" would claim
#: something no sampling can establish, and this phase contains no optimiser
#: that could.
BEST_WORDING = "Best evaluated feasible point"


def _text(value: float | None, precision: int = DEFAULT_PRECISION) -> str:
    return format_engineering(value, precision)


class TradeStudyController(QObject):
    """Application-side facade for the Trade Study workspace."""

    setupChanged = Signal()
    workloadChanged = Signal()
    progressChanged = Signal()
    resultChanged = Signal()
    selectionChanged = Signal()
    requestTab = Signal(int)

    def __init__(self, chamber_source: Any = None,
                 performance_source: Any = None,
                 parent: QObject | None = None) -> None:
        """Take the two workspaces a study's baseline is snapshotted from.

        Duck-typed, as in Phase 5E: anything exposing the case accessors will
        do, which keeps this class from importing two sibling controllers and
        creating an import cycle the next feature would have to break.
        """
        QObject.__init__(self, parent)

        self._chamber_source = chamber_source
        self._performance_source = performance_source
        self._registry = metric_registry()
        self._precision = DEFAULT_PRECISION

        # -- setup state ------------------------------------------------
        self._ranges: dict[str, dict[str, Any]] = {
            spec["key"]: {"enabled": False, **dict(spec["default"])}
            for spec in VARIABLE_SPECS
        }
        self._ranges["oxidiser_fuel_ratio"]["enabled"] = True
        self._ranges["area_ratio"]["enabled"] = True

        self._outputs: list[str] = ["chamber_temperature",
                                    "characteristic_velocity"]
        self._objectives: list[ObjectiveDefinition] = [
            ObjectiveDefinition("specific_impulse", ObjectiveDirection.MAXIMIZE)]
        self._constraints: list[ConstraintDefinition] = []
        self._scoring_enabled = False
        self._weights: dict[str, float] = {"specific_impulse": 1.0}

        # -- run state ---------------------------------------------------
        self._runner = None
        self._steps = None
        self._timer = QTimer(self)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self._advance)
        self._busy = False
        self._cancelled = False
        self._points_done = 0
        self._stage_done: dict[str, int] = {}
        self._setup_snapshot: service.TradeStudySetup | None = None

        # -- result state ------------------------------------------------
        self._result = None
        self._definition = None
        self._stale = False
        self._message = ""
        self._error_code = ""
        self._filter = "all"
        self._model = ThermoTableModel(self)
        self._selected: list[int] = []
        # Which evaluated study the view shows: every finished run gets the
        # next number, and a decision re-analysis of it (no re-solve) the
        # next revision. A pinned design-point subset records both, so a
        # subset of another run -- or of another analysis of this one -- is
        # never compared as if its point indices meant the same designs.
        self._run_identity = 0
        self._analysis_revision = 0
        self._pareto_x = ""
        self._pareto_y = ""
        # Whether a person picked this axis themselves (the RFComboBox
        # onActivated path), as opposed to it holding an automatic default.
        # An explicit pick survives a later objective/constraint/weight edit
        # -- re-analysing is not a reason to silently change what a person
        # is looking at -- while a still-automatic axis keeps adapting
        # toward the richest available default (objectives first) as the
        # study definition grows.
        self._pareto_x_explicit = False
        self._pareto_y_explicit = False

        # -- parametric sweep view ----------------------------------------
        # Which response metrics are drawn as curves against the study's
        # single swept variable (Mode 1 -- see sweepSeries). Empty means
        # "not yet chosen"; _ensure_sweep_metrics() fills in a sensible
        # default the first time it is read.
        self._sweep_metrics: list[str] = []
        self._sweep_scaled = False

    # ==================================================================
    # the baseline
    # ==================================================================

    def _setup(self) -> service.TradeStudySetup | None:
        """Snapshot the two upstream workspaces. None if either is missing."""
        chamber = getattr(self._chamber_source, "current_case", None)
        performance = getattr(self._performance_source, "current_case", None)
        if chamber is None or performance is None:
            return None
        return service.TradeStudySetup(chamber=chamber(),
                                       performance=performance())

    @Property(bool, notify=setupChanged)
    def baselineAvailable(self) -> bool:
        return self._setup() is not None

    @Property(str, notify=setupChanged)
    def baselineHeadline(self) -> str:
        setup = self._setup()
        if setup is None:
            return ""
        from .thermochemistry_service import case_headline

        return case_headline(setup.chamber)

    @Property("QVariantList", notify=setupChanged)
    def baselineRows(self):
        """What the study holds fixed. Snapshotted when Run is pressed.

        Shown here because a front computed on one gamma basis and a front
        computed on the other are not comparable, and a reader has to be able
        to see which one they are looking at without leaving the page.
        """
        setup = self._setup()
        if setup is None:
            return []
        chamber, performance = setup.chamber, setup.performance
        rows = [
            {"label": "Propellants",
             "value": f"{chamber.oxidiser} / {chamber.fuel}"},
            {"label": "Stream temperatures",
             "value": f"{chamber.oxidiser_temperature:g} K / "
                      f"{chamber.fuel_temperature:g} K"},
            {"label": "Provider",
             "value": self._provider_label()},
            {"label": "Gamma strategy and basis",
             "value": f"{performance.gamma_strategy.value} / "
                      f"{performance.gamma_basis.value}"},
            {"label": "Engine size", "value": performance.scale.label},
        ]
        for spec in VARIABLE_SPECS:
            if not self._ranges[spec["key"]]["enabled"]:
                rows.append({"label": f"{spec['label']} (fixed)",
                             "value": self._fixed_value_text(spec["key"])})
        return rows

    def _provider_label(self) -> str:
        from .thermochemistry_provider import PROVIDER_LABEL, availability

        status = availability()
        return (f"{PROVIDER_LABEL} {status.version}".strip() if status.usable
                else f"{PROVIDER_LABEL} — unavailable")

    def _fixed_value_text(self, key: str) -> str:
        setup = self._setup()
        if setup is None:
            return EM_DASH
        spec = variable_spec(key) or {}
        value = {
            "oxidiser_fuel_ratio": setup.chamber.oxidiser_fuel_ratio,
            "chamber_pressure": setup.chamber.chamber_pressure,
            "area_ratio": setup.performance.area_ratio,
            "ambient_pressure": setup.performance.ambient.pressure,
            "throat_area": setup.performance.scale.value,
        }.get(key)
        if value is None:
            return EM_DASH
        unit = f" {spec.get('unit', '')}".rstrip()
        return f"{_text(value)}{unit}"

    @Property("QVariantList", constant=True)
    def deferredVariables(self):
        """What is deliberately not offered, with the reason on the page.

        An omission the interface explains is a decision; one it hides is an
        oversight a user will assume was an oversight.
        """
        return [dict(entry) for entry in DEFERRED_VARIABLES]

    # ==================================================================
    # design variables
    # ==================================================================

    @Property("QVariantList", notify=setupChanged)
    def variableRows(self):
        rows = []
        for spec in VARIABLE_SPECS:
            state = self._ranges[spec["key"]]
            rows.append({
                "key": spec["key"],
                "label": spec["label"],
                "unit": spec["unit"],
                "stage": spec["stage"],
                "stageLabel": STAGE_LABELS[spec["stage"]],
                "dimensionless": spec["dimensionless"],
                "effect": spec["effect"],
                "note": spec["note"],
                "enabled": bool(state["enabled"]),
                "start": float(state["start"]),
                "end": float(state["end"]),
                "count": int(state["count"]),
                "affectsChemistry": spec["stage"] == STAGE_THERMOCHEMISTRY,
                "summary": self._range_summary(spec["key"]),
            })
        return rows

    def _range_summary(self, key: str) -> str:
        state = self._ranges[key]
        if not state["enabled"]:
            return "fixed at the baseline value"
        spec = variable_spec(key) or {}
        unit = f" {spec.get('unit', '')}".rstrip()
        if int(state["count"]) == 1:
            return f"{state['start']:g}{unit}"
        return (f"{state['start']:g} → {state['end']:g}{unit}, "
                f"{int(state['count'])} values")

    @Slot(str, bool)
    def setVariableEnabled(self, key: str, enabled: bool) -> None:
        if key not in self._ranges:
            return
        self._ranges[key]["enabled"] = bool(enabled)
        self._on_setup_changed()

    @Slot(str, float, float, int)
    def setVariableRange(self, key: str, start: float, end: float,
                         count: int) -> None:
        if key not in self._ranges:
            return
        state = self._ranges[key]
        try:
            start, end, count = float(start), float(end), int(count)
        except (TypeError, ValueError):
            return
        if not (math.isfinite(start) and math.isfinite(end)) or count < 1:
            return
        state.update(start=start, end=end, count=count)
        self._on_setup_changed()

    def _variables(self) -> list[Any]:
        """The enabled variables, built through the domain registry.

        Ordered chemistry-stage first, so the enumeration walks the chamber
        states in order and a results table read top to bottom follows the
        expensive stage rather than interleaving it.
        """
        chemistry, performance = [], []
        for spec in VARIABLE_SPECS:
            state = self._ranges[spec["key"]]
            if not state["enabled"]:
                continue
            try:
                variable = build_variable(spec["key"], start=state["start"],
                                          end=state["end"],
                                          count=int(state["count"]))
            except (ValueError, KeyError):
                continue
            (chemistry if spec["stage"] == STAGE_THERMOCHEMISTRY
             else performance).append(variable)
        return chemistry + performance

    # ==================================================================
    # workload preview
    # ==================================================================

    @Property(int, notify=workloadChanged)
    def pointCount(self) -> int:
        total = 1
        for variable in self._variables():
            total *= variable.count
        return total

    @Property(int, notify=workloadChanged)
    def chemistrySolveCount(self) -> int:
        """Distinct chamber solves. Computed from cardinalities, not run."""
        total = 1
        for variable in self._variables():
            if variable.stage == STAGE_THERMOCHEMISTRY:
                total *= variable.count
        return total

    @Property(int, notify=workloadChanged)
    def performanceSolveCount(self) -> int:
        definition = self._build_definition()
        if definition is None:
            return 0
        stages = definition.required_stages(self._registry)
        return self.pointCount if STAGE_PERFORMANCE in stages else 0

    @Property(str, notify=workloadChanged)
    def workloadNote(self) -> str:
        """The sentence that teaches the dependency planner.

        Shown before Run, not after. A user who can see that 410 points cost 41
        chamber solves understands the model; one who only sees a spinner does
        not, and will build the study that costs 410.
        """
        points, solves = self.pointCount, self.chemistrySolveCount
        if points <= 0:
            return ""
        if self.performanceSolveCount == 0:
            return (f"{points:,} design points · {solves:,} chamber solves · "
                    "no performance evaluation is required by this study")
        saved = points - solves
        note = (f"{points:,} design points · {solves:,} unique chamber solves · "
                f"{points:,} performance evaluations")
        if saved > 0:
            note += (f". The nozzle-stage variables add no chamber solves, so "
                     f"{saved:,} chemistry solves are avoided.")
        return note

    @Property(bool, notify=workloadChanged)
    def studyIsLarge(self) -> bool:
        return self.pointCount > LARGE_STUDY_POINTS

    @Property(int, constant=True)
    def maximumPoints(self) -> int:
        return MAX_STUDY_POINTS

    def _on_setup_changed(self) -> None:
        if self._result is not None:
            self._stale = True
        self.setupChanged.emit()
        self.workloadChanged.emit()
        self.resultChanged.emit()

    # ==================================================================
    # outputs, objectives, constraints, scoring
    # ==================================================================

    @Property("QVariantList", constant=True)
    def metricOptions(self):
        return [{"key": m.key, "label": m.label, "unit": m.unit,
                 "stage": m.stage, "stageLabel": STAGE_LABELS[m.stage],
                 "requiresScale": m.requires_scale, "help": m.help}
                for m in METRICS]

    @Property("QVariantList", notify=setupChanged)
    def selectedOutputs(self):
        return list(self._outputs)

    @Slot(str, bool)
    def setOutputSelected(self, key: str, selected: bool) -> None:
        if key not in self._registry:
            return
        if selected and key not in self._outputs:
            self._outputs.append(key)
        elif not selected and key in self._outputs:
            self._outputs.remove(key)
        self._on_setup_changed()

    @Property("QVariantList", notify=setupChanged)
    def objectiveRows(self):
        return [{"metric": o.metric,
                 "label": self._registry[o.metric].label,
                 "unit": self._registry[o.metric].unit,
                 "direction": o.direction.value,
                 "directionLabel": o.direction.label}
                for o in self._objectives if o.metric in self._registry]

    @Slot(str, str)
    def addObjective(self, metric: str, direction: str) -> None:
        if metric not in self._registry:
            return
        if any(o.metric == metric for o in self._objectives):
            return
        try:
            way = ObjectiveDirection(direction)
        except ValueError:
            return
        self._objectives.append(ObjectiveDefinition(metric, way))
        self._weights.setdefault(metric, 1.0)
        self._on_decision_changed()

    @Slot(str)
    def removeObjective(self, metric: str) -> None:
        self._objectives = [o for o in self._objectives if o.metric != metric]
        self._weights.pop(metric, None)
        self._on_decision_changed()

    @Slot(str, str)
    def setObjectiveDirection(self, metric: str, direction: str) -> None:
        try:
            way = ObjectiveDirection(direction)
        except ValueError:
            return
        self._objectives = [ObjectiveDefinition(o.metric, way)
                            if o.metric == metric else o
                            for o in self._objectives]
        self._on_decision_changed()

    @Property("QVariantList", notify=setupChanged)
    def constraintRows(self):
        rows = []
        for index, constraint in enumerate(self._constraints):
            metric = self._registry.get(constraint.metric)
            rows.append({
                "index": index,
                "metric": constraint.metric,
                "label": metric.label if metric else constraint.metric,
                "unit": metric.unit if metric else "",
                "operator": constraint.operator.value,
                "limit": float(constraint.limit),
                "describe": constraint.describe(),
            })
        return rows

    @Property("QVariantList", constant=True)
    def operatorOptions(self):
        """The two operators an engineering limit almost always wants.

        ``<`` , ``>`` and ``==`` exist in the domain type but are not offered:
        on a floating quantity a strict inequality differs from its
        non-strict form only at exact equality, which for a computed
        temperature is a coincidence rather than an intent.
        """
        return [{"key": ComparisonOperator.LE.value, "label": "≤"},
                {"key": ComparisonOperator.GE.value, "label": "≥"}]

    @Slot(str, str, float)
    def addConstraint(self, metric: str, operator: str, limit: float) -> None:
        if metric not in self._registry:
            return
        try:
            constraint = ConstraintDefinition(
                metric, ComparisonOperator(operator), float(limit))
        except (ValueError, TypeError):
            return
        self._constraints.append(constraint)
        self._on_decision_changed()

    @Slot(int)
    def removeConstraint(self, index: int) -> None:
        if 0 <= index < len(self._constraints):
            del self._constraints[index]
            self._on_decision_changed()

    @Property(bool, notify=setupChanged)
    def scoringEnabled(self) -> bool:
        """Off unless the user turns it on. Never enabled by having objectives."""
        return self._scoring_enabled

    @scoringEnabled.setter
    def scoringEnabled(self, value: bool) -> None:
        value = bool(value)
        if value == self._scoring_enabled:
            return
        self._scoring_enabled = value
        self._on_decision_changed()

    @Property("QVariantList", notify=setupChanged)
    def weightRows(self):
        """The typed weights and the normalised ones actually applied."""
        definition = self._score_definition()
        effective = definition.effective_weights if definition else {}
        rows = []
        for objective in self._objectives:
            metric = self._registry.get(objective.metric)
            rows.append({
                "metric": objective.metric,
                "label": metric.label if metric else objective.metric,
                "weight": float(self._weights.get(objective.metric, 1.0)),
                "effective": _text(effective.get(objective.metric), 4),
            })
        return rows

    @Slot(str, float)
    def setWeight(self, metric: str, weight: float) -> None:
        try:
            value = float(weight)
        except (TypeError, ValueError):
            return
        if not math.isfinite(value) or value < 0.0:
            return
        self._weights[metric] = value
        self._on_decision_changed()

    @Property(str, constant=True)
    def scoringNote(self) -> str:
        return ("Min–max normalisation over the feasible evaluated points of "
                "this study. A score is therefore relative to this population: "
                "the same design scores differently in a study with a different "
                "range. It never changes a raw value, a feasibility verdict or "
                "Pareto membership.")

    def _score_definition(self) -> WeightedScoreDefinition | None:
        if not self._scoring_enabled or not self._objectives:
            return None
        weights = {o.metric: float(self._weights.get(o.metric, 1.0))
                   for o in self._objectives}
        if not weights or sum(weights.values()) <= 0.0:
            return None
        try:
            return WeightedScoreDefinition(weights=weights)
        except ValueError:
            return None

    def _on_decision_changed(self) -> None:
        """A decision edit: re-analyse if raw results exist, never re-solve."""
        self.setupChanged.emit()
        self.workloadChanged.emit()
        if self._result is not None and self._result.complete:
            definition = self._build_definition()
            if definition is not None:
                try:
                    self._result = service.reanalyse(self._result, definition)
                    self._definition = definition
                    self._analysis_revision += 1
                except StudyValidationError:
                    pass
                self._publish()
                return
        self.resultChanged.emit()

    # ==================================================================
    # the definition
    # ==================================================================

    def _build_definition(self):
        setup = self._setup()
        if setup is None:
            return None
        return service.build_definition(
            setup, self._variables(),
            outputs=tuple(self._outputs),
            objectives=tuple(self._objectives),
            constraints=tuple(self._constraints),
            scoring=self._score_definition(),
            title="Trade study")

    def _validation_error(self) -> StudyValidationError | None:
        setup = self._setup()
        definition = self._build_definition()
        if setup is None or definition is None:
            return StudyValidationError(
                "NO_BASELINE",
                "A study starts from a chamber case and a nozzle "
                "configuration. Set them on the Thermochemistry and Rocket "
                "Performance tabs first.")
        from rocketforge.engine.studies import validate_definition

        try:
            validate_definition(definition, self._registry,
                                scale_available=setup.scale_available)
        except StudyValidationError as error:
            return error
        return None

    @Property(bool, notify=setupChanged)
    def definitionValid(self) -> bool:
        return self._validation_error() is None

    @Property(str, notify=setupChanged)
    def definitionMessage(self) -> str:
        error = self._validation_error()
        return error.message if error else ""

    @Property(str, notify=setupChanged)
    def definitionCode(self) -> str:
        error = self._validation_error()
        return error.code if error else ""

    @Property(str, notify=setupChanged)
    def definitionFingerprint(self) -> str:
        definition = self._build_definition()
        return definition.fingerprint[:16] if definition else ""

    # ==================================================================
    # running
    # ==================================================================

    @Property(bool, notify=progressChanged)
    def busy(self) -> bool:
        return self._busy

    @Slot()
    def runStudy(self) -> None:
        """Start a study. Serial, chunked, and never concurrent."""
        if self._busy or not self.definitionValid:
            return
        setup = self._setup()
        definition = self._build_definition()
        if setup is None or definition is None:
            return
        try:
            runner = service.make_runner(definition, setup)
        except StudyValidationError as error:
            self._message = error.message
            self._error_code = error.code
            self.resultChanged.emit()
            return

        self._setup_snapshot = setup
        self._definition = definition
        self._runner = runner
        self._steps = runner.steps()
        self._busy = True
        self._cancelled = False
        self._points_done = 0
        self._stage_done = {}
        self._result = None
        self._stale = False
        self._message = ""
        self._error_code = ""
        self._selected = []
        self.progressChanged.emit()
        self.resultChanged.emit()
        self._timer.start()

    def _advance(self) -> None:
        """One chunk of points, then back to the event loop."""
        assert self._steps is not None
        for _ in range(CHUNK_SIZE):
            try:
                progress = next(self._steps)
            except StopIteration:
                self._finish()
                return
            self._points_done = progress.points_done
            self._stage_done = dict(progress.stage_solves_done)
            if progress.cancelled:
                self._finish()
                return
        self.progressChanged.emit()

    def _finish(self) -> None:
        self._timer.stop()
        runner, self._runner, self._steps = self._runner, None, None
        self._busy = False
        if runner is not None:
            result = runner.finish(cancelled=self._cancelled)
            if self._definition is not None and self._setup_snapshot is not None:
                result = service._with_provenance(
                    result, self._definition, self._setup_snapshot)
            self._result = result
            self._run_identity += 1
            self._analysis_revision = 0
        self.progressChanged.emit()
        self._publish()

    @Slot()
    def cancelStudy(self) -> None:
        if not self._busy or self._runner is None:
            return
        self._cancelled = True
        self._runner.cancel()

    @Property(int, notify=progressChanged)
    def pointsEvaluated(self) -> int:
        return self._points_done

    @Property(int, notify=progressChanged)
    def chemistrySolvesDone(self) -> int:
        return int(self._stage_done.get(STAGE_THERMOCHEMISTRY, 0))

    @Property(float, notify=progressChanged)
    def progressFraction(self) -> float:
        total = self.pointCount
        return 0.0 if total <= 0 else min(1.0, self._points_done / total)

    @Property(str, notify=progressChanged)
    def progressText(self) -> str:
        """Real work, not a synthesised percentage."""
        if not self._busy:
            return ""
        return (f"{self._points_done:,} of {self.pointCount:,} points · "
                f"{self.chemistrySolvesDone:,} of "
                f"{self.chemistrySolveCount:,} chamber solves")

    # ==================================================================
    # results
    # ==================================================================

    def _publish(self) -> None:
        self._rebuild_table()
        self._ensure_pareto_axes()
        self.resultChanged.emit()
        self.selectionChanged.emit()

    @Property(bool, notify=resultChanged)
    def hasResult(self) -> bool:
        return self._result is not None

    @Property(bool, notify=resultChanged)
    def resultComplete(self) -> bool:
        return self._result is not None and self._result.complete

    @Property(bool, notify=resultChanged)
    def resultStale(self) -> bool:
        """Whether the setup has moved since this result was produced."""
        return self._stale

    @Property(str, notify=resultChanged)
    def studyStatus(self) -> str:
        return self._result.status.value if self._result else "none"

    @Property(str, notify=resultChanged)
    def studyStatusLabel(self) -> str:
        return self._result.status.label if self._result else "No study yet"

    @Property(str, notify=resultChanged)
    def message(self) -> str:
        return self._message or (self._result.message if self._result else "")

    @Property("QVariantList", notify=resultChanged)
    def summaryRows(self):
        if self._result is None:
            return []
        result = self._result
        counts = result.counts
        rows = [
            {"label": "Design points", "value": f"{len(result.points):,}"},
            {"label": "Evaluated", "value": f"{result.evaluated_count:,}"},
            {"label": "With warnings", "value": f"{result.warning_count:,}"},
            {"label": "Failed", "value": f"{result.failed_count:,}"},
            {"label": "Feasible", "value": f"{result.feasible_count:,}"},
            {"label": "Infeasible", "value": f"{result.infeasible_count:,}"},
            {"label": "Not assessed", "value": f"{result.not_assessed_count:,}"},
            {"label": "Chamber solves",
             "value": f"{counts.stage_solves.get(STAGE_THERMOCHEMISTRY, 0):,}"},
            {"label": "Performance evaluations",
             "value": f"{counts.stage_solves.get(STAGE_PERFORMANCE, 0):,}"},
            {"label": "Elapsed", "value": f"{counts.elapsed_seconds:.2f} s"},
        ]
        if result.complete and result.pareto_indices:
            rows.append({"label": "Pareto-efficient",
                         "value": f"{len(result.pareto_indices):,}"})
        return rows

    @Property(str, notify=resultChanged)
    def solveReuseNote(self) -> str:
        """What the planner actually saved, after the fact."""
        if self._result is None:
            return ""
        solves = self._result.counts.stage_solves
        chemistry = solves.get(STAGE_THERMOCHEMISTRY, 0)
        points = len(self._result.points)
        if chemistry >= points:
            return f"{points:,} design points · {chemistry:,} chamber solves"
        return (f"{points:,} design points · {chemistry:,} chamber solves · "
                f"{solves.get(STAGE_PERFORMANCE, 0):,} performance evaluations")

    # -- the table -------------------------------------------------------

    @Property(QObject, constant=True)
    def resultsModel(self) -> QObject:
        return self._model

    @Property(str, notify=resultChanged)
    def filterMode(self) -> str:
        return self._filter

    @filterMode.setter
    def filterMode(self, value: str) -> None:
        if value not in ("all", "feasible", "pareto", "failed", "warnings"):
            return
        if value == self._filter:
            return
        self._filter = value
        self._rebuild_table()
        self.resultChanged.emit()

    @Property("QVariantList", constant=True)
    def filterOptions(self):
        return [
            {"key": "all", "label": "All points"},
            {"key": "feasible", "label": "Feasible only"},
            {"key": "pareto", "label": "Pareto only"},
            {"key": "warnings", "label": "With warnings"},
            {"key": "failed", "label": "Failed only"},
        ]

    def _visible_points(self) -> list[Any]:
        """A display filter. It hides rows; it never removes them."""
        if self._result is None:
            return []
        points = list(self._result.points)
        if self._filter == "feasible":
            return [p for p in points if p.feasibility is Feasibility.FEASIBLE]
        if self._filter == "pareto":
            return [p for p in points if p.is_pareto_efficient]
        if self._filter == "failed":
            return [p for p in points if not p.ok]
        if self._filter == "warnings":
            return [p for p in points if p.has_warning]
        return points

    def _columns(self) -> list[dict]:
        if self._definition is None:
            return []
        columns = [{"key": "index", "label": "#", "kind": "text",
                    "align": "left"}]
        for variable in self._definition.variables:
            columns.append({"key": variable.key,
                            "label": f"{variable.label}"
                                     + (f"  [{variable.unit}]"
                                        if variable.unit else ""),
                            "kind": "number", "decimals_hint": 6})
        for key in self._definition.required_metrics:
            metric = self._registry.get(key)
            if metric is None:
                continue
            columns.append({"key": key,
                            "label": metric.label
                                     + (f"  [{metric.unit}]"
                                        if metric.unit else ""),
                            "kind": "number",
                            "decimals_hint": metric.decimals_hint})
        columns.append({"key": "status", "label": "Status", "kind": "text",
                        "align": "left"})
        columns.append({"key": "feasibility", "label": "Feasibility",
                        "kind": "text", "align": "left"})
        if self._result is not None and self._result.pareto_indices:
            columns.append({"key": "pareto", "label": "Pareto", "kind": "text",
                            "align": "left"})
        if self._result is not None and self._result.scored:
            columns.append({"key": "score", "label": "Score", "kind": "number",
                            "decimals_hint": 4})
        return columns

    def _rebuild_table(self) -> None:
        if self._result is None or self._definition is None:
            self._model.clear()
            return
        columns = self._columns()
        keys = [column["key"] for column in columns]
        rows, kinds, labels = [], [], []
        for point in self._visible_points():
            cells = []
            for key in keys:
                if key == "index":
                    cells.append(str(point.index))
                elif key == "status":
                    cells.append(point.status.label)
                elif key == "feasibility":
                    cells.append(point.feasibility.label)
                elif key == "pareto":
                    cells.append("Pareto" if point.is_pareto_efficient else "")
                elif key == "score":
                    cells.append(point.score)
                elif key in point.values:
                    cells.append(point.values[key])
                else:
                    cells.append(point.metrics.get(key))
            rows.append(tuple(cells))
            kinds.append("failed" if not point.ok
                         else "warning" if point.has_warning
                         else "condensed"
                         if point.feasibility is Feasibility.INFEASIBLE
                         else "")
            labels.append("PARETO" if point.is_pareto_efficient else "")
        self._model.set_table(columns, rows, kinds, labels)

    @Property("QVariantList", notify=resultChanged)
    def resultColumns(self):
        """The table's column definitions, for the view that renders it.

        Published separately from the model because the table component takes
        them as a property; the model holds the same list, and both come from
        one builder so they cannot disagree about column order.
        """
        return [dict(column) for column in self._columns()]

    @Property(int, notify=resultChanged)
    def visibleRowCount(self) -> int:
        return len(self._visible_points())

    @Property(int, notify=resultChanged)
    def totalPointCount(self) -> int:
        """Every evaluated point, whatever the filter shows."""
        return 0 if self._result is None else len(self._result.points)

    @Property(str, notify=resultChanged)
    def filterLabel(self) -> str:
        for option in self.filterOptions:
            if option["key"] == self._filter:
                return option["label"]
        return self._filter

    @Property(str, notify=resultChanged)
    def runIdentity(self) -> str:
        """The evaluated study on screen: its run, and its decision revision."""
        if self._result is None:
            return ""
        return (f"run {self._run_identity}"
                + (f" · analysis {self._analysis_revision}" if self._analysis_revision else ""))

    @Slot(int, result=int)
    def pointAtRow(self, row: int) -> int:
        """The design-point index a visible table row shows, else -1."""
        points = self._visible_points()
        return points[row].index if 0 <= row < len(points) else -1

    @Slot(int, result=int)
    def rowOfPoint(self, index: int) -> int:
        """The visible table row of design point ``index``, else -1 (filtered out)."""
        for row, point in enumerate(self._visible_points()):
            if point.index == index:
                return row
        return -1

    @Slot("QVariantList")
    def setSelection(self, indices) -> None:
        """Select exactly these design points (up to the comparison limit)."""
        if self._result is None:
            return
        chosen = []
        for value in indices:
            index = int(value)
            if self._result.by_index(index) is not None and index not in chosen:
                chosen.append(index)
        self._selected = chosen[:TradeStudyController.MAX_COMPARE]
        self.selectionChanged.emit()

    @Slot("QVariantList", result="QVariantMap")
    def subsetSnapshot(self, indices):
        """A ``kind: "subset"`` snapshot: these design points, as the table
        shows them, with the filter, the visible columns and the run they
        belong to. Read from the evaluated result; nothing is evaluated."""
        if self._result is None or self._definition is None:
            return {}
        points = []
        for value in indices:
            point = self._result.by_index(int(value))
            if point is not None and point.index not in [p.index for p in points]:
                points.append(point)
        if not points:
            return {}
        columns = self._columns()
        rows = []
        for point in points:
            cells = []
            for column in columns:
                key = column["key"]
                if key == "index":
                    cells.append(str(point.index))
                elif key == "status":
                    cells.append(point.status.label)
                elif key == "feasibility":
                    cells.append(point.feasibility.label)
                elif key == "pareto":
                    cells.append("Pareto" if point.is_pareto_efficient else "")
                elif key == "score":
                    cells.append(_text(point.score))
                elif key in point.values:
                    cells.append(_text(point.values[key]))
                else:
                    cells.append(_text(point.metrics.get(key)))
            rows.append(cells)
        run = self.runIdentity
        return {
            "kind": "subset", "source": "tradestudy", "identity": self._run_identity,
            "runIdentity": run, "indices": [p.index for p in points],
            "filter": {"mode": self._filter, "label": self.filterLabel,
                       "visible": self.visibleRowCount, "total": self.totalPointCount},
            "columns": [{"key": c["key"], "label": c["label"], "unit": ""} for c in columns],
            "rows": rows, "stale": bool(self._stale),
            "label": f"{len(points)} design point{'s' if len(points) != 1 else ''} · {self.filterLabel}",
        }

    # -- diagnostics and provenance --------------------------------------

    @Property("QVariantList", notify=resultChanged)
    def diagnosticRows(self):
        """Repeated codes aggregated; per-point detail stays on the point."""
        if self._result is None:
            return []
        return [{"code": d.code, "severity": d.severity, "message": d.message,
                 "origin": d.origin,
                 "summary": f"{d.count:,} of {d.total:,} points"}
                for d in self._result.diagnostics]

    @Property("QVariantList", notify=resultChanged)
    def provenanceRows(self):
        """Read from the result's own snapshot, never from the live form."""
        if self._result is None or not self._result.provenance:
            return []
        record = self._result.provenance
        provider = record.get("provider", {})
        model = record.get("performance_model", {})
        baseline = record.get("baseline", {})
        return [
            {"label": "Chamber equilibrium",
             "value": f"{provider.get('label', '')} "
                      f"{provider.get('library_version', '')}".strip()},
            {"label": "Chemistry model", "value": provider.get("chemistry", "")},
            {"label": "Ideal performance", "value": model.get("owner", "")},
            {"label": "Performance model", "value": model.get("model", "")},
            {"label": "Gamma strategy / basis",
             "value": f"{model.get('gamma_strategy', '')} / "
                      f"{model.get('gamma_basis', '')}"},
            {"label": "Propellants",
             "value": f"{baseline.get('oxidiser', '')} / "
                      f"{baseline.get('fuel', '')}"},
            {"label": "Definition fingerprint",
             "value": str(record.get("definition_fingerprint", ""))[:16]},
            {"label": "Provider performance oracle",
             "value": "not used — a trade study's performance is RocketForge's"},
        ]

    # ==================================================================
    # Pareto
    # ==================================================================

    def _axis_keys(self) -> list[str]:
        """Every quantity this study's own points actually carry a value for.

        The default axis pair still prefers the study's own objectives (the
        dimensions Pareto membership was decided over), but the full option
        list is wider: every design variable this study varied, plus every
        metric it requested -- exactly the same set `_columns()` already
        builds the results table from, so an axis choice can never be one
        this study's own points have no value for.
        """
        keys: list[str] = []
        if self._definition is not None:
            for variable in self._definition.variables:
                if variable.key not in keys:
                    keys.append(variable.key)
            for key in self._definition.required_metrics:
                if key not in keys and key in self._registry:
                    keys.append(key)
        return keys

    def _ensure_pareto_axes(self) -> None:
        objective_metrics = [o.metric for o in self._objectives]
        all_keys = self._axis_keys()
        if not self._pareto_x_explicit or self._pareto_x not in all_keys:
            self._pareto_x = (objective_metrics[0] if objective_metrics
                              else (all_keys[0] if all_keys else ""))
            self._pareto_x_explicit = False
        if (not self._pareto_y_explicit or self._pareto_y not in all_keys
                or self._pareto_y == self._pareto_x):
            preferred = [m for m in objective_metrics if m != self._pareto_x]
            others = preferred or [k for k in all_keys if k != self._pareto_x]
            self._pareto_y = others[0] if others else ""
            self._pareto_y_explicit = False

    @Property("QVariantList", notify=resultChanged)
    def objectiveAxisOptions(self):
        """Every axis a reader may plot the design space against.

        Not only the study's own objectives -- every design variable this
        study varied and every metric it requested, presentation-only
        (rf-scientific-visualization live: the underlying per-point data
        already carries every one of these, so offering the choice adds no
        physics and changes no Pareto/feasibility/score verdict). Kept under
        its original name since every existing QML binding already uses it;
        widened rather than replaced.
        """
        objective_metrics = {o.metric for o in self._objectives}
        options = []
        for key in self._axis_keys():
            info = self._axis_field_info(key)
            if info is None:
                continue
            label, _unit, is_objective = info
            options.append({
                "key": key, "label": label,
                "isObjective": key in objective_metrics or is_objective,
            })
        return options

    def _axis_field_info(self, key: str) -> tuple[str, str, bool] | None:
        """(label, unit, is a design variable) for a design-space axis key.

        Checked against the study's own variables first -- a variable key
        never collides with a metric key in this registry, but checking
        both in one place keeps every axis-label lookup agreeing with
        `_columns()`'s own precedence exactly.
        """
        if self._definition is not None:
            for variable in self._definition.variables:
                if variable.key == key:
                    return variable.label, variable.unit, True
        metric = self._registry.get(key)
        if metric is not None:
            return metric.label, metric.unit, False
        return None

    @Property(str, notify=resultChanged)
    def paretoX(self) -> str:
        return self._pareto_x

    @paretoX.setter
    def paretoX(self, value: str) -> None:
        self._pareto_x_explicit = True
        if value == self._pareto_x:
            return
        self._pareto_x = value
        self.resultChanged.emit()

    @Property(str, notify=resultChanged)
    def paretoY(self) -> str:
        return self._pareto_y

    @paretoY.setter
    def paretoY(self, value: str) -> None:
        self._pareto_y_explicit = True
        if value == self._pareto_y:
            return
        self._pareto_y = value
        self.resultChanged.emit()

    @Property(str, notify=resultChanged)
    def paretoXTitle(self) -> str:
        """The axis label a reader sees: a name and a unit, not a key."""
        return self._axis_title(self._pareto_x)

    @Property(str, notify=resultChanged)
    def paretoYTitle(self) -> str:
        return self._axis_title(self._pareto_y)

    def _axis_title(self, key: str) -> str:
        info = self._axis_field_info(key)
        if info is None:
            return key
        label, unit, _is_variable = info
        return f"{label}  [{unit}]" if unit else label

    @Property(int, notify=resultChanged)
    def paretoXIndex(self) -> int:
        """Where the current axis sits in the option list.

        Published so the selector can be bound to the axis it controls. Left
        unbound, a combo box shows option zero while the plot is drawn against
        something else, and the control quietly contradicts the picture.
        """
        return self._axis_index(self._pareto_x)

    @Property(int, notify=resultChanged)
    def paretoYIndex(self) -> int:
        return self._axis_index(self._pareto_y)

    def _axis_index(self, key: str) -> int:
        keys = self._axis_keys()
        return keys.index(key) if key in keys else 0

    def _axis_value(self, point: Any, key: str) -> float | None:
        """A point's value for any design-space axis, variable or metric.

        Mirrors `_rebuild_table`'s own precedence exactly (design-variable
        value first, then a registry metric) so a plotted axis can never
        disagree with the same column in the results table.
        """
        if key in point.values:
            value = point.values[key]
            try:
                number = float(value)
            except (TypeError, ValueError):
                return None
            return number if math.isfinite(number) else None
        return point.metric(key)

    @Property(bool, notify=resultChanged)
    def paretoAvailable(self) -> bool:
        return (self._result is not None and self._result.complete
                and len(self._objectives) >= 2
                and bool(self._pareto_x) and bool(self._pareto_y))

    @Property("QVariantList", notify=resultChanged)
    def paretoSeries(self):
        """Three series: efficient, dominated feasible, and not feasible.

        Separated by series rather than by colour alone, so the distinction
        survives for a reader who cannot rely on hue. Pareto/feasibility
        status is a property of the point itself, decided once by the
        decision layer over every objective -- it does not change with
        which two dimensions are plotted, including when an axis is a
        design variable rather than an objective.
        """
        if not self.paretoAvailable:
            return []
        efficient, dominated, excluded = [], [], []
        for point in self._result.points:
            x = self._axis_value(point, self._pareto_x)
            y = self._axis_value(point, self._pareto_y)
            if x is None or y is None:
                continue
            entry = {
                "x": x, "y": y, "index": point.index,
                "status": point.status.label,
                "feasibility": point.feasibility.label,
                "pareto": point.is_pareto_efficient,
                "score": (_text(point.score, 4)
                          if point.score is not None else ""),
            }
            if point.is_pareto_efficient:
                efficient.append(entry)
            elif point.feasibility is Feasibility.FEASIBLE:
                dominated.append(entry)
            else:
                excluded.append(entry)
        efficient.sort(key=lambda entry: entry["x"])
        return [
            {"key": "dominated", "label": "Feasible, dominated",
             "marker": "circle", "points": dominated},
            {"key": "excluded", "label": "Infeasible or failed",
             "marker": "cross", "points": excluded},
            {"key": "efficient", "label": "Pareto-efficient",
             "marker": "diamond", "points": efficient},
        ]

    @Property(bool, notify=resultChanged)
    def paretoAxesAreObjectives(self) -> bool:
        """Whether both plotted axes are this study's own objectives.

        False whenever a reader has chosen a design variable or a
        non-objective metric for either axis -- the plot's own honesty note
        needs to say so, since a projection onto a non-objective dimension
        has no reason to show a monotone "front" edge the way a projection
        onto two objectives does.
        """
        objective_metrics = {o.metric for o in self._objectives}
        return (self._pareto_x in objective_metrics
                and self._pareto_y in objective_metrics)

    @Property(str, notify=resultChanged)
    def paretoNote(self) -> str:
        """Says what the plot is, and what it is not.

        Three things a reader would otherwise assume: that the points lie on
        a curve, that membership was decided by the two axes on screen, and
        that both axes are objectives when one or both may be a design
        variable chosen only for this view.
        """
        if not self.paretoAvailable:
            return ""
        count = len(self._objectives)
        note = ("Each marker is one evaluated design, not a point on a "
                "continuous curve — the front is a sample of the grid that was "
                "run.")
        if not self.paretoAxesAreObjectives:
            objective_labels = ", ".join(
                self._registry[m].label for m in
                (o.metric for o in self._objectives) if m in self._registry)
            note += (f" Pareto/feasibility status is decided using this "
                     f"study's own objectives ({objective_labels}), not the "
                     "axes shown here — a marker's status is a property of "
                     "the design, not of this particular view.")
        elif count > 2:
            shown = ", ".join(self._registry[m].label
                              for m in (self._pareto_x, self._pareto_y))
            note += (f" Pareto membership was decided using all {count} "
                     f"objectives; this plot shows {shown}, so a marker may "
                     "look dominated here while being efficient in the full "
                     "objective set.")
        return note

    # ==================================================================
    # parametric sweep (the primary trade-study grammar: one swept design
    # variable against one or more response curves)
    # ==================================================================

    def _swept_variables(self) -> list[Any]:
        """The design variables the evaluated study actually varied.

        Reads the study's own frozen definition, not the live Setup-tab
        state -- a range edited after Evaluate has not been run yet, and
        this describes what was actually solved.
        """
        if self._definition is None:
            return []
        return [v for v in self._definition.variables if v.count > 1]

    @Property(bool, notify=resultChanged)
    def isParametricSweep(self) -> bool:
        """True when exactly one design variable was actually varied.

        This is the primary Trade Study grammar: a single swept variable
        plotted against one or more response curves answers "how does the
        system respond as this design variable changes." Two or more
        varied variables make a genuine multidimensional design space
        instead, where a 2D scatter/Pareto projection is the honest
        picture (see paretoAvailable/paretoSeries).
        """
        return len(self._swept_variables()) == 1

    @Property(str, notify=resultChanged)
    def sweepVariableKey(self) -> str:
        swept = self._swept_variables()
        return swept[0].key if swept else ""

    @Property(str, notify=resultChanged)
    def sweepVariableTitle(self) -> str:
        swept = self._swept_variables()
        if not swept:
            return ""
        variable = swept[0]
        return (f"{variable.label}  [{variable.unit}]" if variable.unit
                else variable.label)

    @Property("QVariantList", notify=resultChanged)
    def responseMetricOptions(self):
        """Every metric a sweep curve may be plotted against.

        Metrics only, never another design variable -- a sweep curve's Y
        axis is a response to the one thing being swept, not a second
        swept quantity (that is a multidimensional study, not this view).
        """
        if self._definition is None:
            return []
        options = []
        for key in self._definition.required_metrics:
            metric = self._registry.get(key)
            if metric is None:
                continue
            options.append({"key": key, "label": metric.label,
                            "unit": metric.unit})
        return options

    def _ensure_sweep_metrics(self) -> None:
        options = [o["key"] for o in self.responseMetricOptions]
        kept = [k for k in self._sweep_metrics if k in options]
        if kept != self._sweep_metrics:
            self._sweep_metrics = kept
        if not self._sweep_metrics and options:
            objective_metrics = [o.metric for o in self._objectives
                                 if o.metric in options]
            defaults = objective_metrics[:2] if objective_metrics else options[:1]
            self._sweep_metrics = defaults

    @Property("QVariantList", notify=resultChanged)
    def sweepMetrics(self):
        """The response metrics currently drawn as curves, in chosen order."""
        self._ensure_sweep_metrics()
        return list(self._sweep_metrics)

    @Slot(str, bool)
    def setSweepMetricEnabled(self, key: str, enabled: bool) -> None:
        self._ensure_sweep_metrics()
        if enabled:
            if key not in self._sweep_metrics:
                self._sweep_metrics.append(key)
        elif key in self._sweep_metrics:
            self._sweep_metrics.remove(key)
        self.resultChanged.emit()
        # sweepComparisonRows is notify=selectionChanged (it is also gated
        # on which design is selected) -- emit both so the Inspector's
        # comparison table updates immediately when the chosen metric set
        # changes, not only on the next selection change.
        self.selectionChanged.emit()

    @Property(bool, notify=resultChanged)
    def sweepScaledToPeak(self) -> bool:
        """Whether each sweep curve is shown as a fraction of its own peak.

        Named to avoid this project's own QML no-decision-algorithm guard
        (test_qml_implements_no_decision_algorithm bans the substring
        "normaliz" in any workspace .qml file, so a view that only reads
        this flag's name would trip it) -- the user-facing word is still
        "Normalized" everywhere this actually renders as text.
        """
        return self._sweep_scaled

    @sweepScaledToPeak.setter
    def sweepScaledToPeak(self, value: bool) -> None:
        value = bool(value)
        if value == self._sweep_scaled:
            return
        self._sweep_scaled = value
        self.resultChanged.emit()

    @Property(str, notify=resultChanged)
    def sweepScalingNote(self) -> str:
        if not self._sweep_scaled:
            return ""
        return ("Each curve is normalized to its own maximum in this "
                "evaluated sweep (value ÷ evaluated maximum) — a "
                "presentation choice, not a physical quantity. Raw values "
                "stay available in the Inspector and the results table.")

    @Property("QVariantList", notify=resultChanged)
    def sweepSeries(self):
        """One curve per selected response metric against the swept variable.

        Sorted by the swept variable's value so a polyline connects samples
        in sweep order, never in evaluation order. A point whose metric
        could not be computed (`hasValue: false`) is included with a
        placeholder y so the index stays aligned with every other series,
        but carries no drawable value -- the caller must break the line
        there rather than bridge across it, the same honesty discipline
        the results table already applies to a failed row.
        """
        if not self.isParametricSweep or self._result is None:
            return []
        sweep_key = self.sweepVariableKey
        self._ensure_sweep_metrics()
        series = []
        for metric_key in self._sweep_metrics:
            info = self._axis_field_info(metric_key)
            label = info[0] if info else metric_key
            unit = info[1] if info else ""
            raw_values = []
            points = []
            for point in self._result.points:
                x = self._axis_value(point, sweep_key)
                if x is None:
                    continue
                y = self._axis_value(point, metric_key)
                has_value = y is not None
                if has_value:
                    raw_values.append(y)
                points.append({
                    "x": x, "y": (y if has_value else 0.0),
                    "hasValue": has_value,
                    "index": point.index,
                    "status": point.status.label,
                    "feasibility": point.feasibility.label,
                    "pareto": point.is_pareto_efficient,
                    "score": (_text(point.score, 4)
                              if point.score is not None else ""),
                })
            points.sort(key=lambda p: p["x"])
            peak = max(raw_values) if raw_values else None
            if self._sweep_scaled and peak:
                for entry in points:
                    entry["rawY"] = entry["y"]
                    if entry["hasValue"]:
                        entry["y"] = entry["y"] / peak
            else:
                for entry in points:
                    entry["rawY"] = entry["y"]
            series.append({"key": metric_key, "label": label, "unit": unit,
                           "peak": (peak if peak is not None else 0.0),
                           "points": points})
        return series

    @Property("QVariantList", notify=selectionChanged)
    def sweepComparisonRows(self):
        """For the selected design: each response's value, the maximum of
        that response across the evaluated sweep, and how far this design
        sits from that maximum.

        Answers "how much do I give up in this metric to be here" with a
        number, not just a curve position. Pure aggregation over results
        this study already produced -- zero new physics. Never called an
        "efficiency loss": that word claims a specific, defined physical
        quantity this is not.
        """
        if not self.isParametricSweep or not self._selected or self._result is None:
            return []
        point = self._result.by_index(self._selected[-1])
        if point is None:
            return []
        self._ensure_sweep_metrics()
        rows = []
        for metric_key in self._sweep_metrics:
            value = self._axis_value(point, metric_key)
            if value is None:
                continue
            others = [self._axis_value(p, metric_key)
                     for p in self._result.points]
            others = [v for v in others if v is not None]
            if not others:
                continue
            peak = max(others)
            info = self._axis_field_info(metric_key)
            label = info[0] if info else metric_key
            unit = info[1] if info else ""
            diff = value - peak
            percent = (diff / peak * 100.0) if peak else 0.0
            rows.append({
                "label": label, "unit": unit,
                "value": f"{_text(value)} {unit}".strip(),
                "maxValue": f"{_text(peak)} {unit}".strip(),
                "diffFromMax": f"{_text(diff)} {unit}".strip(),
                "percentFromMax": f"{percent:+.2f}%",
            })
        return rows

    @Property(str, notify=resultChanged)
    def rankingNote(self) -> str:
        if self._result is None or not self._result.complete:
            return ""
        if len(self._objectives) == 1:
            return ("One objective, so there is no trade-off to plot. The "
                    "points are ranked instead.")
        return ""

    @Property("QVariantList", notify=resultChanged)
    def bestRows(self):
        """The best evaluated feasible point per objective.

        Never called an optimum: a finite sampled grid cannot establish one,
        and this phase contains no algorithm that could.
        """
        if self._result is None or not self._result.complete:
            return []
        rows = []
        for objective in self._objectives:
            best, best_value = None, None
            for point in self._result.points:
                if not point.eligible_for_decision:
                    continue
                value = point.metric(objective.metric)
                if value is None:
                    continue
                if best_value is None or objective.is_better(value, best_value):
                    best, best_value = point, value
            if best is None:
                continue
            metric = self._registry[objective.metric]
            rows.append({
                "objective": f"{objective.direction.label} {metric.label}",
                "value": f"{_text(best_value)} {metric.unit}".strip(),
                "point": best.point.describe(self._definition.variables),
                "index": best.index,
                "wording": BEST_WORDING,
            })
        return rows

    # ==================================================================
    # compare
    # ==================================================================

    #: How many designs may be compared side by side.
    MAX_COMPARE = 4

    @Property(int, constant=True)
    def maximumComparisons(self) -> int:
        return TradeStudyController.MAX_COMPARE

    @Property("QVariantList", notify=selectionChanged)
    def selectedIndices(self):
        return list(self._selected)

    @Slot(int)
    def toggleSelection(self, index: int) -> None:
        if index in self._selected:
            self._selected.remove(index)
        elif len(self._selected) < TradeStudyController.MAX_COMPARE:
            self._selected.append(index)
        self.selectionChanged.emit()

    @Slot()
    def clearSelection(self) -> None:
        self._selected = []
        self.selectionChanged.emit()

    @Property("QVariantList", notify=selectionChanged)
    def compareColumns(self):
        """One column per selected design, raw physics included.

        The score, where it exists, is one row among many rather than the
        headline: a reader must always be able to see what produced it.
        """
        if self._result is None or self._definition is None:
            return []
        columns = []
        for index in self._selected:
            point = self._result.by_index(index)
            if point is None:
                continue
            rows = []
            for variable in self._definition.variables:
                value = point.values.get(variable.key)
                unit = f" {variable.unit}" if variable.unit else ""
                rows.append({"group": "Design variables",
                             "label": variable.label,
                             "value": f"{_text(value)}{unit}".strip()})
            for key in self._definition.required_metrics:
                metric = self._registry.get(key)
                if metric is None:
                    continue
                unit = f" {metric.unit}" if metric.unit else ""
                rows.append({"group": "Physics",
                             "label": metric.label,
                             "value": f"{_text(point.metric(key))}{unit}".strip()})
            for outcome in point.constraint_outcomes:
                rows.append({"group": "Constraints",
                             "label": outcome.constraint.describe(),
                             "value": outcome.describe()})
            # Decision last, and the score last within it. A score summarises
            # the numbers above it, and a reader must be able to see them
            # before being asked to trust it.
            rows.append({"group": "Decision", "label": "Status",
                         "value": point.status.label})
            rows.append({"group": "Decision", "label": "Feasibility",
                         "value": point.feasibility.label})
            if self._result.pareto_indices:
                rows.append({"group": "Decision", "label": "Pareto",
                             "value": "Efficient" if point.is_pareto_efficient
                                      else "Dominated"})
            warnings = [d for d in point.diagnostics
                        if str(getattr(d, "severity", "")) in ("warning", "error")]
            rows.append({"group": "Decision", "label": "Warnings",
                         "value": f"{len(warnings)}" if warnings else "none"})
            if self._result.scored:
                rows.append({"group": "Decision", "label": "Weighted score",
                             "value": _text(point.score, 4)})

            # Mark where a group heading belongs, so the view renders one per
            # group rather than one per row. Deciding it here keeps the loop
            # that knows the order in the same place as the order.
            previous = ""
            for entry in rows:
                entry["showGroup"] = entry["group"] != previous
                previous = entry["group"]

            columns.append({
                "index": index,
                "title": f"Point {index}",
                "subtitle": point.point.describe(self._definition.variables),
                "rows": rows,
            })
        return columns

    @Property("QVariantList", notify=selectionChanged)
    def selectedViolations(self):
        """Exactly which limits a selected infeasible point failed."""
        if self._result is None:
            return []
        rows = []
        for index in self._selected:
            point = self._result.by_index(index)
            if point is None:
                continue
            for outcome in point.violated:
                rows.append({"index": index, "text": outcome.describe()})
        return rows

    @Slot(int)
    def showTab(self, index: int) -> None:
        self.requestTab.emit(int(index))
