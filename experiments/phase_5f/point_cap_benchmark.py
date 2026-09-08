"""Measure the generic layer, so the study point cap is chosen from evidence.

The cap exists to stop a study becoming unusable, not to stop it being large.
Picking a round number without measuring would either refuse studies that run
fine or admit studies that stall the interface, so this measures the four costs
that scale with point count and reports where each one turns:

    enumeration        linear
    evaluation         linear in the evaluator, which is not this layer's cost
    constraints        linear
    Pareto             O(N^2) -- the term that decides the cap
    scoring            linear

The evaluator here is a trivial arithmetic stub. That is deliberate: the cap is
a limit on the *generic* machinery, and mixing in chemistry time would measure
the provider instead.
"""

from __future__ import annotations

import json
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rocketforge.engine.studies import (  # noqa: E402
    ExplicitNumericVariable,
    LinearRangeVariable,
    MetricDefinition,
    MetricRegistry,
    ObjectiveDefinition,
    ObjectiveDirection,
    StageOutcome,
    StudyBaseline,
    StudyDefinition,
    WeightedScoreDefinition,
    analyse,
    run_study,
)
from rocketforge.engine.studies.pareto import pareto_membership  # noqa: E402

STAGES = ("upstream", "downstream", "decision")

REGISTRY = MetricRegistry([
    MetricDefinition("alpha", "Alpha", "upstream", "A"),
    MetricDefinition("beta", "Beta", "downstream", "B"),
])


class ArithmeticEvaluator:
    """As cheap as an evaluator can be, so the measurement is of this layer."""

    def __init__(self) -> None:
        self.calls = {"upstream": 0, "downstream": 0}

    def evaluate(self, stage, point, upstream):
        self.calls[stage] += 1
        x = float(point.values.get("x", 1.0))
        y = float(point.values.get("y", 1.0))
        if stage == "upstream":
            return StageOutcome(ok=True, value={"alpha": 100.0 + x},
                                metrics={"alpha": 100.0 + x})
        return StageOutcome(ok=True, value={},
                            metrics={"beta": upstream["alpha"] * y - x * y})


def build(upstream_count: int, downstream_count: int) -> StudyDefinition:
    return StudyDefinition(
        baseline=StudyBaseline(conditions={"fixed": 1.0},
                               model={"provider": "arithmetic"}),
        variables=(
            LinearRangeVariable(key="x", label="X", stage="upstream",
                                start=1.0, end=5.0, count=upstream_count),
            LinearRangeVariable(key="y", label="Y", stage="downstream",
                                start=1.0, end=9.0, count=downstream_count),
        ),
        stage_order=STAGES,
        outputs=("alpha", "beta"),
        objectives=(ObjectiveDefinition("beta", ObjectiveDirection.MAXIMIZE),
                    ObjectiveDefinition("alpha", ObjectiveDirection.MINIMIZE)),
        scoring=WeightedScoreDefinition(weights={"beta": 2.0, "alpha": 1.0}),
    )


def measure(upstream_count: int, downstream_count: int) -> dict:
    definition = build(upstream_count, downstream_count)
    evaluator = ArithmeticEvaluator()

    tracemalloc.start()
    started = time.perf_counter()
    result = run_study(definition, REGISTRY, evaluator)
    total = time.perf_counter() - started
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # The decision layer alone, re-run over the finished raw result.
    started = time.perf_counter()
    analyse(result, definition)
    decision = time.perf_counter() - started

    eligible = [(p.index, p.metrics) for p in result.points
                if p.eligible_for_decision]
    started = time.perf_counter()
    pareto_membership(eligible, definition.objectives)
    pareto = time.perf_counter() - started

    return {
        "points": definition.point_count,
        "upstream_values": upstream_count,
        "downstream_values": downstream_count,
        "upstream_solves": evaluator.calls["upstream"],
        "downstream_solves": evaluator.calls["downstream"],
        "total_seconds": round(total, 4),
        "decision_seconds": round(decision, 4),
        "pareto_seconds": round(pareto, 4),
        "peak_memory_mb": round(peak / 1024 / 1024, 2),
        "retained_memory_mb": round(current / 1024 / 1024, 2),
        "pareto_points": len(result.pareto_indices),
        "feasible": result.feasible_count,
    }


def main() -> int:
    sizes = [
        (10, 10),        # 100
        (25, 20),        # 500
        (40, 25),        # 1 000
        (50, 50),        # 2 500
        (100, 50),       # 5 000
        (100, 100),      # 10 000
        (200, 100),      # 20 000 -- the proposed cap
        (200, 200),      # 40 000 -- twice the cap, to see the turn
    ]
    rows = [measure(a, b) for a, b in sizes]

    print(f"{'points':>8} {'up':>5} {'down':>7} {'total s':>9} "
          f"{'decision s':>11} {'pareto s':>9} {'peak MB':>8}")
    for row in rows:
        print(f"{row['points']:>8} {row['upstream_solves']:>5} "
              f"{row['downstream_solves']:>7} {row['total_seconds']:>9.4f} "
              f"{row['decision_seconds']:>11.4f} {row['pareto_seconds']:>9.4f} "
              f"{row['peak_memory_mb']:>8.2f}")

    # A second run at the largest size, to show nothing accumulates.
    repeat = measure(200, 100)

    report = {
        "purpose": ("evidence for MAX_STUDY_POINTS; the generic layer only, "
                    "with an arithmetic evaluator, so no provider time is "
                    "included"),
        "interpreter": sys.version.split()[0],
        "rows": rows,
        "repeat_at_20000": repeat,
        "notes": [
            "Pareto is O(N^2) and is the term that decides the cap.",
            "Evaluation time is the evaluator's, not this layer's; a real "
            "study is dominated by chemistry, which solve reuse is what "
            "reduces.",
            "The repeat at the cap shows peak memory does not grow between "
            "runs.",
        ],
    }
    out = ROOT / "acceptance" / "phase_5f" / "study_performance.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nrepeat at 20 000 points: {repeat['total_seconds']:.4f} s, "
          f"peak {repeat['peak_memory_mb']:.2f} MB")
    print(f"-> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
