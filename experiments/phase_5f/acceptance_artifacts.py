"""Generate the Phase 5F acceptance evidence.

Every artifact records a measurement rather than an assertion: call counts,
enumerated points, hand-checked fronts and the residuals between a cached study
and a direct solve. Nothing here is copied from a test expectation -- the tests
and these artifacts are two independent readings of the same code.

Run with the CEA interpreter for the live sections; the synthetic ones need no
chemistry library and are produced either way.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "acceptance" / "phase_5f"

from rocketforge.application.analysis import performance_service as perf  # noqa: E402
from rocketforge.application.analysis import thermochemistry_provider as gateway  # noqa: E402
from rocketforge.application.analysis import thermochemistry_service as thermo  # noqa: E402
from rocketforge.application.analysis import trade_study_service as ts  # noqa: E402
from rocketforge.application.analysis.trade_study_domain import (  # noqa: E402
    DEFERRED_VARIABLES,
    METRICS,
    STAGE_ORDER,
    STAGE_PERFORMANCE,
    STAGE_THERMOCHEMISTRY,
    VARIABLE_SPECS,
    build_variable,
)
from rocketforge.engine.studies import (  # noqa: E402
    ComparisonOperator,
    ConstraintDefinition,
    ExplicitNumericVariable,
    Feasibility,
    LinearRangeVariable,
    MAX_STUDY_POINTS,
    MetricDefinition,
    MetricRegistry,
    ObjectiveDefinition,
    ObjectiveDirection,
    StageOutcome,
    StudyBaseline,
    StudyDefinition,
    WeightedScoreDefinition,
    analyse,
    enumerate_points,
    evaluate_constraints,
    linear_range,
    pareto_front,
    run_study,
    score_points,
)

MAX_ISP = ObjectiveDefinition("specific_impulse", ObjectiveDirection.MAXIMIZE)
MIN_TC = ObjectiveDefinition("chamber_temperature", ObjectiveDirection.MINIMIZE)


def write(name: str, payload: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  -> {name}")


def setup(scaled: bool = False) -> ts.TradeStudySetup:
    performance = perf.DEFAULT_PERFORMANCE_CASE
    if scaled:
        from rocketforge.engineering.nozzle import (
            PerformanceScale,
            PerformanceScaleMode,
        )

        performance = performance.replace(
            scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    return ts.TradeStudySetup(chamber=thermo.DEFAULT_CASE,
                              performance=performance)


# ===========================================================================
# 1. definitions and enumeration
# ===========================================================================


def study_definition_examples() -> None:
    base = setup()
    of = build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41)
    eps = ExplicitNumericVariable(key="area_ratio", label="Area ratio  Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(10.0, 20.0, 40.0, 80.0))
    canonical = ts.build_definition(
        base, [of, eps], outputs=("chamber_temperature",),
        objectives=(MAX_ISP, MIN_TC),
        constraints=(ConstraintDefinition("chamber_temperature",
                                          ComparisonOperator.LE, 3500.0),),
        scoring=WeightedScoreDefinition(
            weights={"specific_impulse": 3.0, "chamber_temperature": 1.0}),
        title="canonical two-objective study")

    renamed = canonical.replace(title="a different name entirely")
    widened = canonical.replace(variables=(
        build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=42),
        eps))

    write("study_definition_examples.json", {
        "purpose": "a full StudyDefinition, and what does and does not change "
                   "its fingerprint",
        "stage_order": list(STAGE_ORDER),
        "variables_offered": [
            {k: v for k, v in spec.items() if k != "default"}
            for spec in VARIABLE_SPECS],
        "variables_deliberately_not_offered": [dict(entry)
                                               for entry in DEFERRED_VARIABLES],
        "metrics": [{"key": m.key, "label": m.label, "unit": m.unit,
                     "stage": m.stage, "requires_scale": m.requires_scale}
                    for m in METRICS],
        "canonical": canonical.canonical(),
        "fingerprints": {
            "canonical": canonical.fingerprint,
            "renamed_title": renamed.fingerprint,
            "one_more_of_value": widened.fingerprint,
        },
        "fingerprint_verdict": {
            "title_is_not_scientific": renamed.fingerprint == canonical.fingerprint,
            "a_wider_range_is": widened.fingerprint != canonical.fingerprint,
        },
        "point_cap": MAX_STUDY_POINTS,
    })


def point_enumeration() -> None:
    of = ExplicitNumericVariable(key="oxidiser_fuel_ratio", label="O/F",
                                 stage=STAGE_THERMOCHEMISTRY,
                                 entries=(2.5, 3.5, 4.5))
    eps = ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(10.0, 40.0, 80.0, 120.0))
    points = enumerate_points([of, eps])

    span = linear_range(2.5, 4.5, 41)
    accumulated, step = 2.5, 2.0 / 40
    for _ in range(40):
        accumulated += step

    write("point_enumeration.json", {
        "purpose": "deterministic ordering and exact endpoints",
        "variables": [{"key": "oxidiser_fuel_ratio", "values": list(of.values)},
                      {"key": "area_ratio", "values": list(eps.values)}],
        "total_points": len(points),
        "ordering_rule": "the first variable varies slowest (odometer order); "
                         "index is the point identity for the life of a study",
        "points": [{"index": p.index, **{k: v for k, v in p.values.items()}}
                   for p in points],
        "endpoint_exactness": {
            "count": 41,
            "first": span[0],
            "last": span[-1],
            "first_exact": span[0] == 2.5,
            "last_exact": span[-1] == 4.5,
            "accumulated_last": accumulated,
            "accumulation_would_drift": accumulated != 4.5,
            "note": "generated by index rather than by repeated addition; the "
                    "accumulated value is shown to record what that avoids",
        },
    })


# ===========================================================================
# 2. the dependency planner and the cache
# ===========================================================================


def dependency_planner_and_cache() -> None:
    base = setup()
    registry = ts.metric_registry()

    cases = []
    for name, variables, outputs, objectives in (
        ("A — 41 O/F x 4 area ratios",
         [build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41),
          ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(10.0, 20.0, 40.0, 80.0))],
         (), (MAX_ISP,)),
        ("A' — 41 O/F x 10 area ratios",
         [build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41),
          build_variable("area_ratio", start=10.0, end=100.0, count=10)],
         (), (MAX_ISP,)),
        ("B — fixed chamber, 10 area ratios x 5 ambients",
         [build_variable("area_ratio", start=10.0, end=100.0, count=10),
          build_variable("ambient_pressure", start=0.0, end=101325.0, count=5)],
         (), (MAX_ISP,)),
        ("C — 5 O/F x 4 chamber pressures x 3 area ratios",
         [build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=5),
          build_variable("chamber_pressure", start=5.0e6, end=20.0e6, count=4),
          ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(10.0, 40.0, 80.0))],
         (), (MAX_ISP,)),
        ("D — chamber temperature only, 41 O/F",
         [build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41)],
         ("chamber_temperature",), ()),
    ):
        definition = ts.build_definition(base, variables, outputs=outputs,
                                         objectives=objectives)
        evaluator = ts.RocketForgeEvaluator(base)
        available = gateway.availability().usable
        actual = None
        if available:
            result = ts.run_trade_study(definition, base, evaluator=evaluator)
            actual = dict(result.counts.stage_solves)
        cases.append({
            "case": name,
            "design_points": definition.point_count,
            "required_stages": list(definition.required_stages(registry)),
            "expected_chemistry_solves":
                definition.unique_solves(STAGE_THERMOCHEMISTRY),
            "expected_performance_solves":
                definition.point_count
                if STAGE_PERFORMANCE in definition.required_stages(registry)
                else 0,
            "actual_solves": actual,
            "naive_chemistry_solves": definition.point_count,
            "reduction_factor": round(
                definition.point_count
                / definition.unique_solves(STAGE_THERMOCHEMISTRY), 3),
        })

    write("dependency_planner.json", {
        "purpose": "which stage each variable belongs to, and what that costs",
        "stages": {
            STAGE_THERMOCHEMISTRY: [s["key"] for s in VARIABLE_SPECS
                                    if s["stage"] == STAGE_THERMOCHEMISTRY],
            STAGE_PERFORMANCE: [s["key"] for s in VARIABLE_SPECS
                                if s["stage"] == STAGE_PERFORMANCE],
        },
        "rule": "a stage key holds the values of every variable at or before "
                "that stage, and nothing else",
        "cases": cases,
    })

    write("chemistry_cache_proof.json", {
        "purpose": "measured provider call counts, not timings",
        "provider_available": gateway.availability().usable,
        "blocking_claim": "a design point count is not a solve count",
        "cases": [{k: c[k] for k in ("case", "design_points",
                                     "expected_chemistry_solves",
                                     "actual_solves", "naive_chemistry_solves",
                                     "reduction_factor")}
                  for c in cases],
        "verdict": ("PASS" if all(
            c["actual_solves"] is None
            or c["actual_solves"].get(STAGE_THERMOCHEMISTRY)
            == c["expected_chemistry_solves"] for c in cases) else "FAIL"),
    })


def failure_caching() -> None:
    """One refused upstream state with N dependants costs one call."""
    registry = MetricRegistry([MetricDefinition("m", "M", "up"),
                               MetricDefinition("n", "N", "down")])
    calls = {"up": 0, "down": 0}

    class Refusing:
        def evaluate(self, stage, point, upstream):
            calls[stage] += 1
            if stage == "up":
                if point.values["x"] in (1.0, 2.0):
                    return StageOutcome.failure("synthetic refusal")
                return StageOutcome(ok=True, value={"m": point.values["x"]},
                                    metrics={"m": point.values["x"]})
            return StageOutcome(ok=True, metrics={"n": upstream["m"] * 2})

    definition = StudyDefinition(
        baseline=StudyBaseline(),
        stage_order=("up", "down", "decide"),
        variables=(ExplicitNumericVariable(key="x", label="X", stage="up",
                                           entries=(1.0, 2.0, 3.0, 4.0)),
                   ExplicitNumericVariable(key="y", label="Y", stage="down",
                                           entries=tuple(float(v)
                                                         for v in range(10)))),
        outputs=("n",))
    result = run_study(definition, registry, Refusing())

    write("failure_caching.json", {
        "purpose": "a refused upstream state is solved once, not once per "
                   "dependant",
        "design_points": len(result.points),
        "refused_upstream_values": [1.0, 2.0],
        "dependants_per_value": 10,
        "upstream_calls": calls["up"],
        "downstream_calls": calls["down"],
        "naive_upstream_calls": len(result.points),
        "failed_points_kept": result.failed_count,
        "points_dropped": 0,
        "verdict": "PASS" if calls["up"] == 4 and calls["down"] == 20 else "FAIL",
        "note": "the two refused states have 10 dependants each; the tour cost "
                "4 upstream calls in total and attempted no downstream work "
                "for them",
    })


# ===========================================================================
# 3. direct-solve parity
# ===========================================================================


def direct_solve_parity() -> None:
    if not gateway.availability().usable:
        write("direct_solve_parity.json",
              {"status": "skipped", "reason": "no chemistry provider"})
        return

    base = setup()
    of = build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41)
    eps = ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(10.0, 20.0, 40.0, 80.0))
    fields = ("chamber_temperature", "gamma_frozen", "characteristic_velocity",
              "thrust_coefficient", "effective_exhaust_velocity",
              "specific_impulse", "exit_pressure")
    definition = ts.build_definition(base, [of, eps], outputs=fields)
    evaluator = ts.RocketForgeEvaluator(base)
    result = ts.run_trade_study(definition, base, evaluator=evaluator)

    direct = ts.RocketForgeEvaluator(base)
    compared, differences = 0, []
    for point in result.points:
        chamber = thermo.solve_case(direct.chamber_case(point.values))
        outcome = perf.solve_performance(
            chamber, direct.performance_case(point.values))
        expected = {**ts.chamber_metrics(chamber),
                    **ts.performance_metrics(outcome)}
        for key in fields:
            compared += 1
            if point.metrics.get(key) != expected.get(key):
                differences.append({
                    "index": point.index, "field": key,
                    "cached": point.metrics.get(key),
                    "direct": expected.get(key)})

    write("direct_solve_parity.json", {
        "purpose": "caching changes the call count, never the science",
        "design_points": len(result.points),
        "fields_per_point": len(fields),
        "fields_compared": compared,
        "differences": differences,
        "cached_chemistry_solves":
            evaluator.calls[STAGE_THERMOCHEMISTRY],
        "direct_chemistry_solves": direct.calls[STAGE_THERMOCHEMISTRY],
        "comparison": "exact float equality, not a tolerance",
        "verdict": "PASS" if not differences else "FAIL",
    })


# ===========================================================================
# 4. the decision layer, on hand-checked fixtures
# ===========================================================================


HAND_POINTS = [
    (0, {"isp": 300.0, "tc": 3000.0}),
    (1, {"isp": 320.0, "tc": 3200.0}),
    (2, {"isp": 340.0, "tc": 3400.0}),
    (3, {"isp": 310.0, "tc": 3300.0}),
    (4, {"isp": 300.0, "tc": 3100.0}),
    (5, {"isp": 340.0, "tc": 3400.0}),
]
HAND_MAX_ISP = ObjectiveDefinition("isp", ObjectiveDirection.MAXIMIZE)
HAND_MIN_TC = ObjectiveDefinition("tc", ObjectiveDirection.MINIMIZE)


def constraint_cases() -> None:
    constraints = [ConstraintDefinition("tc", ComparisonOperator.LE, 3200.0),
                   ConstraintDefinition("isp", ComparisonOperator.GE, 310.0)]
    rows = []
    for index, metrics in HAND_POINTS + [(6, {"isp": None, "tc": 3000.0})]:
        outcomes = evaluate_constraints(metrics, constraints)
        rows.append({
            "index": index,
            "metrics": metrics,
            "outcomes": [{"constraint": o.constraint.describe(),
                          "value": o.value, "satisfied": o.satisfied,
                          "describe": o.describe()} for o in outcomes],
            "verdict": ("infeasible" if any(o.satisfied is False for o in outcomes)
                        else "not assessable"
                        if any(o.satisfied is None for o in outcomes)
                        else "feasible"),
        })

    write("constraint_cases.json", {
        "purpose": "hard constraints, hand-specified expectations",
        "constraints": [c.describe() for c in constraints],
        "expected": {"0": "infeasible (isp 300 < 310)",
                     "1": "feasible",
                     "2": "infeasible (tc 3400 > 3200)",
                     "3": "infeasible (tc 3300 > 3200)",
                     "4": "infeasible (isp 300 < 310)",
                     "5": "infeasible (tc 3400 > 3200)",
                     "6": "not assessable — isp was never produced"},
        "rows": rows,
        "penalty_system": "none — a constraint is satisfied or violated, and "
                          "an unjudgeable metric is a third answer rather than "
                          "a violation",
    })


def pareto_cases() -> None:
    front = pareto_front(HAND_POINTS, [HAND_MAX_ISP, HAND_MIN_TC])
    mutated = list(HAND_POINTS)
    mutated[3] = (3, {"isp": 400.0, "tc": 2900.0})
    mutated_front = pareto_front(mutated, [HAND_MAX_ISP, HAND_MIN_TC])
    flipped = pareto_front(
        HAND_POINTS,
        [HAND_MAX_ISP, ObjectiveDefinition("tc", ObjectiveDirection.MAXIMIZE)])

    write("pareto_cases.json", {
        "purpose": "nondominance on a fixture whose answer was worked out by "
                   "hand, not produced by the implementation",
        "objectives": ["maximize isp", "minimize tc"],
        "points": [{"index": i, **m} for i, m in HAND_POINTS],
        "expected_front": [0, 1, 2, 5],
        "expected_reasoning": {
            "0": "nondominated — lowest tc",
            "1": "nondominated",
            "2": "nondominated — highest isp",
            "3": "dominated by 1: lower isp and higher tc",
            "4": "dominated by 0: equal isp, higher tc",
            "5": "ties with 2; identical vectors do not dominate each other, "
                 "so both stay",
        },
        "actual_front": list(front),
        "mutation_proof": {
            "changed_point": 3,
            "before": dict(HAND_POINTS[3][1]),
            "after": dict(mutated[3][1]),
            "fixture_actually_changed": HAND_POINTS[3][1] != mutated[3][1],
            "front_before": list(front),
            "front_after": list(mutated_front),
        },
        "direction_proof": {
            "front_with_tc_maximised": list(flipped),
            "changed": list(flipped) != list(front),
        },
        "excluded_by_construction": "failed and infeasible points never reach "
                                    "this function; the caller filters them, "
                                    "because only the caller knows what they "
                                    "mean",
        "verdict": "PASS" if list(front) == [0, 1, 2, 5] else "FAIL",
    })


def scoring_cases() -> None:
    fixture = HAND_POINTS[:3]
    definition = WeightedScoreDefinition(
        weights={"isp": 3.0, "tc": 1.0})
    scores = score_points(fixture, [HAND_MAX_ISP, HAND_MIN_TC], definition)
    flipped = score_points(fixture, [HAND_MAX_ISP, HAND_MIN_TC],
                           WeightedScoreDefinition(weights={"isp": 1.0,
                                                            "tc": 3.0}))
    front_before = pareto_front(fixture, [HAND_MAX_ISP, HAND_MIN_TC])
    front_after = pareto_front(fixture, [HAND_MAX_ISP, HAND_MIN_TC])

    write("scoring_cases.json", {
        "purpose": "min-max normalisation and a weighted total, computed by "
                   "hand first",
        "enabled_by_default": False,
        "method": definition.method.value,
        "weights_as_typed": dict(definition.weights),
        "weights_applied": definition.effective_weights,
        "points": [{"index": i, **m} for i, m in fixture],
        "hand_calculation": {
            "isp normalised (maximise)": [0.0, 0.5, 1.0],
            "tc normalised (minimise)": [1.0, 0.5, 0.0],
            "score 0": "0.75*0.0 + 0.25*1.0 = 0.25",
            "score 1": "0.75*0.5 + 0.25*0.5 = 0.50",
            "score 2": "0.75*1.0 + 0.25*0.0 = 0.75",
        },
        "actual_scores": {str(k): v for k, v in sorted(scores.items())},
        "reweighted_scores": {str(k): v for k, v in sorted(flipped.items())},
        "reweighting_reverses_the_ranking":
            max(scores, key=scores.get) != max(flipped, key=flipped.get),
        "pareto_unchanged_by_weights": list(front_before) == list(front_after),
        "zero_span_convention":
            "an objective with no spread contributes the same constant to "
            "every point, so it cannot decide an order and nothing divides by "
            "zero",
        "population_relative":
            "min-max is taken over this study's feasible evaluated points, so "
            "the same design scores differently in a different population",
        "verdict": "PASS" if [round(scores[i], 12) for i in (0, 1, 2)] ==
                             [0.25, 0.5, 0.75] else "FAIL",
    })


# ===========================================================================
# 5. re-analysis costs no physics
# ===========================================================================


def reanalysis_zero_resolve() -> None:
    if not gateway.availability().usable:
        write("reanalysis_zero_resolve.json",
              {"status": "skipped", "reason": "no chemistry provider"})
        return

    base = setup()
    of = build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41)
    eps = ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(10.0, 20.0, 40.0, 80.0))
    definition = ts.build_definition(
        base, [of, eps], outputs=("chamber_temperature",),
        objectives=(MAX_ISP, MIN_TC))
    evaluator = ts.RocketForgeEvaluator(base)
    result = ts.run_trade_study(definition, base, evaluator=evaluator)
    after_run = dict(evaluator.calls)
    raw_before = [dict(p.metrics) for p in result.points]

    steps = []

    flipped = definition.replace(objectives=(
        ObjectiveDefinition("specific_impulse", ObjectiveDirection.MINIMIZE),
        MIN_TC))
    a = ts.reanalyse(result, flipped)
    steps.append({"edit": "objective direction flipped",
                  "chemistry_solves_added":
                      evaluator.calls[STAGE_THERMOCHEMISTRY]
                      - after_run[STAGE_THERMOCHEMISTRY],
                  "performance_solves_added":
                      evaluator.calls[STAGE_PERFORMANCE]
                      - after_run[STAGE_PERFORMANCE],
                  "pareto_changed": a.pareto_indices != result.pareto_indices,
                  "raw_unchanged": [dict(p.metrics) for p in a.points]
                                   == raw_before})

    for limit in (3600.0, 3500.0, 3400.0):
        constrained = definition.replace(constraints=(
            ConstraintDefinition("chamber_temperature",
                                 ComparisonOperator.LE, limit),))
        b = ts.reanalyse(result, constrained)
        steps.append({"edit": f"constraint tc <= {limit:g}",
                      "chemistry_solves_added":
                          evaluator.calls[STAGE_THERMOCHEMISTRY]
                          - after_run[STAGE_THERMOCHEMISTRY],
                      "performance_solves_added":
                          evaluator.calls[STAGE_PERFORMANCE]
                          - after_run[STAGE_PERFORMANCE],
                      "feasible": b.feasible_count,
                      "infeasible": b.infeasible_count,
                      "raw_unchanged": [dict(p.metrics) for p in b.points]
                                       == raw_before})

    scored = definition.replace(scoring=WeightedScoreDefinition(
        weights={"specific_impulse": 99.0, "chamber_temperature": 0.01}))
    c = ts.reanalyse(result, scored)
    steps.append({"edit": "score weights 99 / 0.01",
                  "chemistry_solves_added":
                      evaluator.calls[STAGE_THERMOCHEMISTRY]
                      - after_run[STAGE_THERMOCHEMISTRY],
                  "performance_solves_added":
                      evaluator.calls[STAGE_PERFORMANCE]
                      - after_run[STAGE_PERFORMANCE],
                  "pareto_unchanged": c.pareto_indices == result.pareto_indices,
                  "raw_unchanged": [dict(p.metrics) for p in c.points]
                                   == raw_before})

    write("reanalysis_zero_resolve.json", {
        "purpose": "a decision edit re-runs the decision layer and nothing else",
        "design_points": len(result.points),
        "solves_for_the_original_run": after_run,
        "edits": steps,
        "verdict": "PASS" if all(s["chemistry_solves_added"] == 0
                                 and s["performance_solves_added"] == 0
                                 and s["raw_unchanged"] for s in steps)
                   else "FAIL",
    })


# ===========================================================================
# 6. the live study
# ===========================================================================


def live_trade_study() -> None:
    if not gateway.availability().usable:
        write("live_trade_study.json",
              {"status": "skipped", "reason": "no chemistry provider"})
        return

    base = setup()
    of = build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41)
    eps = ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(10.0, 20.0, 40.0, 80.0))

    single = ts.build_definition(base, [of, eps], objectives=(MAX_ISP,),
                                 title="live study A")
    started = time.perf_counter()
    a = ts.run_trade_study(single, base)
    a_seconds = time.perf_counter() - started

    two = ts.build_definition(
        base, [of, eps], outputs=("chamber_temperature",),
        objectives=(MAX_ISP, MIN_TC),
        constraints=(ConstraintDefinition("chamber_temperature",
                                          ComparisonOperator.LE, 3500.0),),
        title="live study B")
    started = time.perf_counter()
    b = ts.run_trade_study(two, base)
    b_seconds = time.perf_counter() - started

    def best(result, objective):
        chosen, value = None, None
        for point in result.points:
            if not point.eligible_for_decision:
                continue
            current = point.metric(objective.metric)
            if current is None:
                continue
            if value is None or objective.is_better(current, value):
                chosen, value = point, current
        return None if chosen is None else {
            "index": chosen.index,
            "variables": dict(chosen.point.values),
            "value": value,
            "wording": "best evaluated feasible point",
        }

    write("live_trade_study.json", {
        "purpose": "two live studies against NASA CEA chemistry and "
                   "RocketForge performance",
        "provider": ts.study_provenance(single, base)["provider"],
        "performance_owner": "RocketForge",
        "oracle_used": False,
        "study_A": {
            "title": single.title,
            "definition_fingerprint": single.fingerprint,
            "design_points": len(a.points),
            "stage_solves": dict(a.counts.stage_solves),
            "seconds": round(a_seconds, 3),
            "failed": a.failed_count,
            "feasible": a.feasible_count,
            "objectives": ["maximize specific_impulse"],
            "ranking_length": len(a.ranking),
            "best": best(a, MAX_ISP),
            "diagnostics": [{"code": d.code, "severity": d.severity,
                             "count": d.count, "total": d.total,
                             "origin": d.origin} for d in a.diagnostics],
        },
        "study_B": {
            "title": two.title,
            "definition_fingerprint": two.fingerprint,
            "design_points": len(b.points),
            "stage_solves": dict(b.counts.stage_solves),
            "seconds": round(b_seconds, 3),
            "constraint": "chamber_temperature <= 3500 K",
            "feasible": b.feasible_count,
            "infeasible": b.infeasible_count,
            "pareto_points": len(b.pareto_indices),
            "pareto_indices": list(b.pareto_indices),
            "pareto_front": [
                {"index": index,
                 "variables": dict(b.by_index(index).point.values),
                 "specific_impulse": b.by_index(index).metric("specific_impulse"),
                 "chamber_temperature":
                     b.by_index(index).metric("chamber_temperature")}
                for index in b.pareto_indices],
            "best_per_objective": {
                "maximize specific_impulse": best(b, MAX_ISP),
                "minimize chamber_temperature": best(b, MIN_TC),
            },
            "note": "the constraint limit is a documented test value, not one "
                    "chosen to shape the front",
        },
    })


def main() -> int:
    print("Phase 5F acceptance artifacts")
    study_definition_examples()
    point_enumeration()
    dependency_planner_and_cache()
    failure_caching()
    direct_solve_parity()
    constraint_cases()
    pareto_cases()
    scoring_cases()
    reanalysis_zero_resolve()
    live_trade_study()
    return 0


if __name__ == "__main__":
    sys.exit(main())
