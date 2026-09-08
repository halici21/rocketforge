"""Layer 3 -- the generic design-space / trade-study engine.

Doc 06 assigns "parametric studies, trades, sensitivity" to ``engine.studies``,
and this is that module. It sits above ``engineering`` because a study is not
the design of one physical component: it is a decision layer over results that
components produced.

**Nothing here knows what a rocket is.** No thermochemistry, no nozzle, no c*,
no Isp -- not even an import of them. A study is a set of design variables, an
evaluator that turns a point into metrics, and the decision analysis that
follows: constraints, feasibility, objectives, Pareto, an optional score. The
whole package is exercised in tests by synthetic evaluators with no physics at
all, which is what makes the decision algorithms checkable independently of the
physics they will be pointed at.

Consequently it imports no provider, no Qt, and no physics module. The
RocketForge evaluator that wires this to thermochemistry and ideal performance
lives in ``application`` -- the only layer allowed to touch a provider.

The distinction the whole package exists to preserve::

    DESIGN VARIABLE -> PHYSICS -> RAW RESULT -> CONSTRAINT -> FEASIBILITY
                    -> OBJECTIVE -> PARETO / OPTIONAL SCORE -> HUMAN DECISION

Each arrow is one-way. A score never reaches back into physics; a constraint
never becomes a penalty; a warning never becomes an infeasibility.
"""

from __future__ import annotations

from .variables import (
    CategoricalVariable,
    DesignVariable,
    ExplicitNumericVariable,
    LinearRangeVariable,
    VariableDomain,
    linear_range,
)
from .metrics import MetricDefinition, MetricRegistry
from .enumeration import DesignPoint, enumerate_points, point_count
from .definition import (
    MAX_STUDY_POINTS,
    LARGE_STUDY_POINTS,
    StudyBaseline,
    StudyDefinition,
    StudyValidationError,
    validate_definition,
)
from .constraints import (
    ComparisonOperator,
    ConstraintDefinition,
    ConstraintOutcome,
    evaluate_constraints,
)
from .objectives import ObjectiveDefinition, ObjectiveDirection, rank_by_objective
from .pareto import pareto_front, pareto_membership
from .scoring import (
    NormalizationMethod,
    WeightedScoreDefinition,
    normalize_objective,
    score_points,
)
from .results import (
    EvaluationCounts,
    EvaluationStatus,
    Feasibility,
    StudyDiagnostic,
    StudyPointResult,
    StudyResult,
    StudyStatus,
)
from .analysis import analyse, apply_constraints, decide_feasibility
from .execution import (
    StageOutcome,
    StudyEvaluator,
    StudyProgress,
    StudyRunner,
    run_study,
)

__all__ = [
    "CategoricalVariable",
    "DesignVariable",
    "ExplicitNumericVariable",
    "LinearRangeVariable",
    "VariableDomain",
    "linear_range",
    "MetricDefinition",
    "MetricRegistry",
    "DesignPoint",
    "enumerate_points",
    "point_count",
    "MAX_STUDY_POINTS",
    "LARGE_STUDY_POINTS",
    "StudyBaseline",
    "StudyDefinition",
    "StudyValidationError",
    "validate_definition",
    "ComparisonOperator",
    "ConstraintDefinition",
    "ConstraintOutcome",
    "evaluate_constraints",
    "ObjectiveDefinition",
    "ObjectiveDirection",
    "rank_by_objective",
    "pareto_front",
    "pareto_membership",
    "NormalizationMethod",
    "WeightedScoreDefinition",
    "normalize_objective",
    "score_points",
    "EvaluationStatus",
    "Feasibility",
    "StudyPointResult",
    "StudyResult",
    "StudyStatus",
    "EvaluationCounts",
    "StudyDiagnostic",
    "analyse",
    "apply_constraints",
    "decide_feasibility",
    "StageOutcome",
    "StudyEvaluator",
    "StudyProgress",
    "StudyRunner",
    "run_study",
]
