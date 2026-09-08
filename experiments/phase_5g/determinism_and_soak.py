"""Determinism, state leakage, and a soak over ten thousand design points.

Four questions this answers, none of which a single-run test can:

1. Does the same input give the same output, repeatedly?
2. Does running B between two runs of A change A? (state leakage)
3. Does a long sequence drift?
4. Does memory accumulate across large studies?

Everything is float64 equality, not a tolerance. A provider that returned a
slightly different chamber on the second call would be a defect, and comparing
with a tolerance would hide exactly the thing being looked for.
"""

from __future__ import annotations

import gc
import json
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "acceptance" / "phase_5g"

from rocketforge.application.analysis import performance_service as perf  # noqa: E402
from rocketforge.application.analysis import thermochemistry_provider as gateway  # noqa: E402
from rocketforge.application.analysis import thermochemistry_service as thermo  # noqa: E402
from rocketforge.application.analysis import trade_study_service as ts  # noqa: E402
from rocketforge.application.analysis.trade_study_domain import (  # noqa: E402
    STAGE_PERFORMANCE,
    STAGE_THERMOCHEMISTRY,
    build_variable,
)
from rocketforge.engine.studies import (  # noqa: E402
    ExplicitNumericVariable,
    ObjectiveDefinition,
    ObjectiveDirection,
)

MAX_ISP = ObjectiveDefinition("specific_impulse", ObjectiveDirection.MAXIMIZE)
MIN_TC = ObjectiveDefinition("chamber_temperature", ObjectiveDirection.MINIMIZE)

CASE_A = thermo.DEFAULT_CASE
CASE_B = thermo.DEFAULT_CASE.replace(oxidiser_fuel_ratio=3.8,
                                     chamber_pressure=15.0e6)
PERFORMANCE = perf.DEFAULT_PERFORMANCE_CASE


def write(name: str, payload: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  -> {name}")


def chamber_signature(outcome) -> tuple:
    """Everything that must be identical between two solves of one case."""
    state = outcome.state
    return (
        outcome.kind,
        state.temperature, state.molar_mass, state.gas_constant,
        state.gamma_equilibrium, state.gamma_frozen,
        state.cp_frozen, state.cp_equilibrium,
        state.condensed_mass_fraction,
        tuple(state.composition.entries),           # ordering included
        tuple(d.code for d in outcome.diagnostics),
    )


def performance_signature(outcome) -> tuple:
    r = outcome.result
    return (
        outcome.kind, r.reduced.gamma,
        r.characteristic_velocity, r.thrust_coefficient_momentum,
        r.thrust_coefficient_pressure, r.thrust_coefficient,
        r.exit.mach, r.exit.pressure, r.exit.temperature, r.exit.velocity,
        r.effective_exhaust_velocity, r.specific_impulse, r.exit.regime,
    )


def study_signature(result) -> tuple:
    return (
        result.status.value,
        tuple(dict(result.counts.stage_solves).items()),
        tuple((p.index, tuple(sorted(p.values.items())),
               tuple(sorted((k, v) for k, v in p.metrics.items())),
               p.status.value, p.feasibility.value,
               p.is_pareto_efficient, p.score)
              for p in result.points),
        result.pareto_indices, result.ranking,
    )


# ===========================================================================
# repeats
# ===========================================================================


def deterministic_repeats(rounds: int = 5) -> dict:
    chamber = [chamber_signature(thermo.solve_case(CASE_A))
               for _ in range(rounds)]
    solved = thermo.solve_case(CASE_A)
    performance = [performance_signature(perf.solve_performance(solved, PERFORMANCE))
                   for _ in range(rounds)]

    setup = ts.TradeStudySetup(chamber=CASE_A, performance=PERFORMANCE)
    of = build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=6)
    eps = ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(20.0, 40.0, 80.0))
    definition = ts.build_definition(setup, [of, eps],
                                     outputs=("chamber_temperature",),
                                     objectives=(MAX_ISP, MIN_TC))
    studies = [study_signature(ts.run_trade_study(definition, setup))
               for _ in range(3)]

    return {
        "purpose": "the same input, repeatedly, compared by float64 equality",
        "rounds": rounds,
        "chamber_identical": len(set(chamber)) == 1,
        "performance_identical": len(set(performance)) == 1,
        "study_rounds": len(studies),
        "study_identical": len(set(studies)) == 1,
        "comparison": "exact float64 equality including composition ordering, "
                      "diagnostic codes, point ordering, feasibility, Pareto "
                      "membership and score",
        "fingerprint_stable": len({definition.fingerprint
                                   for _ in range(5)}) == 1,
        "verdict": "PASS" if (len(set(chamber)) == 1
                              and len(set(performance)) == 1
                              and len(set(studies)) == 1) else "FAIL",
    }


# ===========================================================================
# A / B / A
# ===========================================================================


def state_leak_sequence() -> dict:
    a1 = chamber_signature(thermo.solve_case(CASE_A))
    b1 = chamber_signature(thermo.solve_case(CASE_B))
    a2 = chamber_signature(thermo.solve_case(CASE_A))
    b2 = chamber_signature(thermo.solve_case(CASE_B))
    a3 = chamber_signature(thermo.solve_case(CASE_A))

    solved_a = thermo.solve_case(CASE_A)
    solved_b = thermo.solve_case(CASE_B)
    pa1 = performance_signature(perf.solve_performance(solved_a, PERFORMANCE))
    _ = perf.solve_performance(solved_b, PERFORMANCE)
    pa2 = performance_signature(perf.solve_performance(solved_a, PERFORMANCE))

    setup_a = ts.TradeStudySetup(chamber=CASE_A, performance=PERFORMANCE)
    setup_b = ts.TradeStudySetup(chamber=CASE_B, performance=PERFORMANCE)
    of = build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=4)
    da = ts.build_definition(setup_a, [of], objectives=(MAX_ISP,))
    db = ts.build_definition(setup_b, [of], objectives=(MAX_ISP,))
    sa1 = study_signature(ts.run_trade_study(da, setup_a))
    _ = ts.run_trade_study(db, setup_b)
    sa2 = study_signature(ts.run_trade_study(da, setup_a))

    # A long alternating sequence, then A again.
    long_cases = []
    for index in range(50):
        case = CASE_A.replace(
            oxidiser_fuel_ratio=2.6 + 0.04 * (index % 25),
            chamber_pressure=(8.0 + 0.5 * (index % 10)) * 1.0e6)
        long_cases.append(chamber_signature(thermo.solve_case(case)))
    a_after_long = chamber_signature(thermo.solve_case(CASE_A))

    return {
        "purpose": "running another case in between must not change this one",
        "chamber_ABABA": {
            "a1_equals_a2": a1 == a2,
            "a1_equals_a3": a1 == a3,
            "b1_equals_b2": b1 == b2,
            "a_differs_from_b": a1 != b1,
        },
        "performance_ABA": {"a1_equals_a2": pa1 == pa2},
        "trade_study_ABA": {"a1_equals_a2": sa1 == sa2},
        "long_sequence": {
            "cases_run": len(long_cases),
            "distinct_results": len(set(long_cases)),
            "a_unchanged_after_50_other_cases": a1 == a_after_long,
        },
        "verdict": "PASS" if (a1 == a2 == a3 == a_after_long and b1 == b2
                              and a1 != b1 and pa1 == pa2 and sa1 == sa2)
                   else "FAIL",
    }


# ===========================================================================
# soak
# ===========================================================================


def soak(target_points: int = 10_000) -> dict:
    """Several studies totalling at least ``target_points`` design points."""
    plans = [
        ("41 x 20",
         build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41),
         build_variable("area_ratio", start=10.0, end=100.0, count=20)),
        ("61 x 25",
         build_variable("oxidiser_fuel_ratio", start=2.4, end=4.6, count=61),
         build_variable("area_ratio", start=8.0, end=120.0, count=25)),
        ("81 x 30",
         build_variable("oxidiser_fuel_ratio", start=2.2, end=4.8, count=81),
         build_variable("area_ratio", start=5.0, end=150.0, count=30)),
        ("101 x 40",
         build_variable("oxidiser_fuel_ratio", start=2.0, end=5.0, count=101),
         build_variable("area_ratio", start=5.0, end=200.0, count=40)),
        ("121 x 50",
         build_variable("oxidiser_fuel_ratio", start=2.0, end=5.0, count=121),
         build_variable("area_ratio", start=5.0, end=250.0, count=50)),
    ]
    setup = ts.TradeStudySetup(chamber=CASE_A, performance=PERFORMANCE)

    gc.collect()
    tracemalloc.start()
    baseline_current, _ = tracemalloc.get_traced_memory()

    rows, totals = [], {"points": 0, "chemistry": 0, "performance": 0}
    started_all = time.perf_counter()
    for label, of, eps in plans:
        definition = ts.build_definition(setup, [of, eps],
                                         outputs=("chamber_temperature",),
                                         objectives=(MAX_ISP, MIN_TC))
        started = time.perf_counter()
        result = ts.run_trade_study(definition, setup)
        seconds = time.perf_counter() - started
        current, peak = tracemalloc.get_traced_memory()
        solves = dict(result.counts.stage_solves)
        rows.append({
            "study": label,
            "design_points": len(result.points),
            "chemistry_solves": solves.get(STAGE_THERMOCHEMISTRY, 0),
            "performance_solves": solves.get(STAGE_PERFORMANCE, 0),
            "naive_chemistry_solves": len(result.points),
            "seconds": round(seconds, 3),
            "feasible": result.feasible_count,
            "failed": result.failed_count,
            "pareto": len(result.pareto_indices),
            "peak_MB": round(peak / 1024 / 1024, 2),
            "retained_MB": round((current - baseline_current) / 1024 / 1024, 2),
        })
        totals["points"] += len(result.points)
        totals["chemistry"] += solves.get(STAGE_THERMOCHEMISTRY, 0)
        totals["performance"] += solves.get(STAGE_PERFORMANCE, 0)
        del result
        gc.collect()

    total_seconds = time.perf_counter() - started_all

    # The first plan again, to see whether anything accumulated.
    label, of, eps = plans[0]
    definition = ts.build_definition(setup, [of, eps],
                                     outputs=("chamber_temperature",),
                                     objectives=(MAX_ISP, MIN_TC))
    first_signature = None
    repeats = []
    for round_index in range(4):
        started = time.perf_counter()
        result = ts.run_trade_study(definition, setup)
        seconds = time.perf_counter() - started
        current, peak = tracemalloc.get_traced_memory()
        signature = study_signature(result)
        if first_signature is None:
            first_signature = signature
        repeats.append({
            "round": round_index + 1,
            "seconds": round(seconds, 3),
            "peak_MB": round(peak / 1024 / 1024, 2),
            "retained_MB": round((current - baseline_current) / 1024 / 1024, 2),
            "identical_to_first": signature == first_signature,
        })
        del result
        gc.collect()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    retained = [row["retained_MB"] for row in rows]
    return {
        "purpose": "many studies in one process; drift, growth and reuse",
        "studies": rows,
        "totals": totals,
        "total_seconds": round(total_seconds, 2),
        "target_points": target_points,
        "target_met": totals["points"] >= target_points,
        "naive_chemistry_solves": totals["points"],
        "actual_chemistry_solves": totals["chemistry"],
        "reduction_factor": round(totals["points"] / totals["chemistry"], 2),
        "repeat_of_first_study": repeats,
        "final_peak_MB": round(peak / 1024 / 1024, 2),
        "final_retained_MB": round((current - baseline_current) / 1024 / 1024, 2),
        "retained_series_MB": retained,
        "monotonic_growth": all(a <= b for a, b in zip(retained, retained[1:])),
        "note": "peak grows with the largest study held in memory, which is "
                "expected; the repeat rounds show whether anything is retained "
                "between studies",
        "verdict": "PASS" if (totals["points"] >= target_points
                              and all(r["identical_to_first"] for r in repeats))
                   else "FAIL",
    }


# ===========================================================================
# recovery
# ===========================================================================


def error_recovery() -> dict:
    """A refusal must not leave the provider or the services unusable."""
    good = chamber_signature(thermo.solve_case(CASE_A))

    # A stream temperature outside the range CEA declares: a refusal, by design.
    refused = thermo.solve_case(CASE_A.replace(oxidiser_temperature=250.0))

    # A nozzle regime the ideal model is not defined for.
    solved = thermo.solve_case(CASE_A)
    bad_nozzle = perf.solve_performance(
        solved, PERFORMANCE.replace(
            ambient=perf.AmbientCondition(perf.AmbientMode.CUSTOM, 5.0e6)))

    # A study whose upstream states mostly refuse.
    setup = ts.TradeStudySetup(
        chamber=CASE_A.replace(oxidiser_temperature=250.0),
        performance=PERFORMANCE)
    of = build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=4)
    failing = ts.run_trade_study(
        ts.build_definition(setup, [of], objectives=(MAX_ISP,)), setup)

    after = chamber_signature(thermo.solve_case(CASE_A))

    return {
        "purpose": "after every failure mode, the canonical case is unchanged",
        "refused_chamber": {
            "status": refused.kind,
            "produced_a_state": refused.state is not None,
            "message": refused.message[:160],
        },
        "refused_performance": {
            "status": bad_nozzle.kind,
            "produced_a_result": bad_nozzle.result is not None,
            "message": bad_nozzle.message[:160],
        },
        "failing_study": {
            "points": len(failing.points),
            "failed": failing.failed_count,
            "chemistry_solves":
                dict(failing.counts.stage_solves).get(STAGE_THERMOCHEMISTRY),
        },
        "canonical_case_unchanged_afterwards": good == after,
        "verdict": "PASS" if (good == after and refused.state is None
                              and bad_nozzle.result is None) else "FAIL",
    }


def main() -> int:
    if not gateway.availability().usable:
        write("determinism.json", {"status": "skipped",
                                   "reason": "no chemistry provider"})
        return 1

    print("Phase 5G determinism, state leakage, soak and recovery")
    write("deterministic_repeats.json", deterministic_repeats())
    write("state_leak_sequence.json", state_leak_sequence())
    write("soak_results.json", soak())
    write("error_recovery.json", error_recovery())
    return 0


if __name__ == "__main__":
    sys.exit(main())
