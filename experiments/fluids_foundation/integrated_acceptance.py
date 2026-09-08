"""Integrated acceptance: density studies, determinism, state, soak, memory.

Everything here runs against the real providers. Comparisons are by exact
float64 equality, not a tolerance: a provider that returned a slightly
different answer on a second identical call is the defect being looked for, and
a tolerance would hide it.
"""
from __future__ import annotations

import gc
import json
import pathlib
import sys
import time
import tracemalloc

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rocketforge.application.analysis import performance_service as perf  # noqa: E402
from rocketforge.application.analysis import thermochemistry_service as thermo  # noqa: E402
from rocketforge.application.analysis import trade_study_service as svc  # noqa: E402
from rocketforge.engine.studies import (  # noqa: E402
    LinearRangeVariable,
    ObjectiveDefinition,
    ObjectiveDirection,
    VariableDomain,
)
from rocketforge.engineering.propellants import (  # noqa: E402
    PRODUCTION_FLUID_MAPPING,
    density_impulse,
    mixture_bulk_density,
    stream_density,
)
from rocketforge.physics.fluids import (  # noqa: E402
    METHANE,
    OXYGEN,
    FluidPhase,
    FluidProperty,
    FluidStateRequest,
)
from rocketforge.providers.fluid_properties import coolprop_provider  # noqa: E402

OUT = ROOT / "acceptance" / "fluids_foundation"
OUT.mkdir(parents=True, exist_ok=True)

FEED = 3.0e5
fluids = coolprop_provider()


def base_case():
    return thermo.ChamberCase(fuel="LCH4", oxidiser="LOX",
                              oxidiser_fuel_ratio=3.4, chamber_pressure=1.0e7,
                              fuel_temperature=111.643,
                              oxidiser_temperature=90.17)


def setup(feed=FEED):
    return svc.TradeStudySetup(chamber=base_case(),
                               performance=perf.PerformanceCase(),
                               feed_pressure=feed)


def write(name, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  -> {name}")


# ===========================================================================
# 1. determinism and state leakage
# ===========================================================================
print("determinism and state")


def evaluate(fluid, temperature, pressure):
    return fluids.evaluate(FluidStateRequest(
        fluid=fluid, temperature=temperature, pressure=pressure)).value


def snapshot(state):
    return {p.value: state.value_of(p) for p in FluidProperty if state.has(p)}


repeats = [snapshot(evaluate(OXYGEN, 90.17, FEED)) for _ in range(5)]
determinism = {
    "purpose": "identical queries must be identical, by exact float equality",
    "repeats": 5,
    "all_identical": all(r == repeats[0] for r in repeats),
    "values": repeats[0],
}

a1 = snapshot(evaluate(OXYGEN, 90.17, FEED))
b1 = snapshot(evaluate(METHANE, 111.643, FEED))
a2 = snapshot(evaluate(OXYGEN, 90.17, FEED))
b2 = snapshot(evaluate(METHANE, 111.643, FEED))
a3 = snapshot(evaluate(OXYGEN, 90.17, FEED))
for temperature in range(80, 100):
    evaluate(OXYGEN, float(temperature), FEED)
a4 = snapshot(evaluate(OXYGEN, 90.17, FEED))
determinism["state_leak"] = {
    "pattern": "A/B/A/B/A then 20 other states then A",
    "a_identical": a1 == a2 == a3 == a4,
    "b_identical": b1 == b2,
    "a_differs_from_b": a1 != b1,
    "note": ("the last clause matters: three equal answers would also be "
             "produced by a stuck cache"),
}
write("determinism.json", determinism)


# ===========================================================================
# 2. density impulse canonical cases
# ===========================================================================
print("density impulse cases")

cases = []
for label, ox_t, fuel_t in (("reference", 90.17, 111.643),
                            ("colder oxidiser", 86.0, 111.643),
                            ("warmer oxidiser", 98.0, 111.643)):
    fuel = stream_density(fluids, PRODUCTION_FLUID_MAPPING.require("LCH4"),
                          fuel_t, FEED)
    oxidiser = stream_density(fluids, PRODUCTION_FLUID_MAPPING.require("LOX"),
                              ox_t, FEED)
    bulk = mixture_bulk_density(3.4, fuel, oxidiser)
    metric = density_impulse(bulk, 3400.0, 3400.0 / 9.80665)
    cases.append({"case": label, "oxidiser_temperature_K": ox_t,
                  "fuel_temperature_K": fuel_t,
                  **metric.as_mapping(),
                  "fuel_density": fuel.density,
                  "oxidiser_density": oxidiser.density})

densities = [c["oxidiser_density"] for c in cases]
write("density_impulse_cases.json", {
    "purpose": "validated stream densities, bulk density and density impulse",
    "feed_pressure_Pa": FEED,
    "cases": cases,
    "density_responds_to_temperature": len(set(densities)) == len(densities),
    "warmer_oxidiser_is_less_dense": densities[1] > densities[0] > densities[2],
    "every_identity_residual_zero": all(c["identity_residual"] == 0.0
                                        for c in cases),
})


# ===========================================================================
# 3. a trade study with density impulse as an objective
# ===========================================================================
print("trade study with density impulse")

variables = (
    LinearRangeVariable(key="oxidiser_fuel_ratio", label="O/F", unit="",
                        stage="thermochemistry",
                        domain=VariableDomain(minimum=0.0,
                                             exclusive_minimum=True),
                        start=2.5, end=4.5, count=41),
    LinearRangeVariable(key="area_ratio", label="Ae/At", unit="",
                        stage="performance",
                        domain=VariableDomain(minimum=1.0),
                        start=10.0, end=100.0, count=10),
)
study_setup = setup()
definition = svc.build_definition(
    study_setup, variables,
    objectives=(ObjectiveDefinition(metric="density_impulse",
                                    direction=ObjectiveDirection.MAXIMIZE),))
evaluator = svc.RocketForgeEvaluator(study_setup)
started = time.perf_counter()
result = svc.run_trade_study(definition, study_setup, evaluator=evaluator)
elapsed = time.perf_counter() - started

points = result.points
with_metric = [p for p in points if p.metrics.get("density_impulse") is not None]
best = max(with_metric, key=lambda p: p.metrics["density_impulse"])
study_report = {
    "purpose": "density impulse as a first-class trade-study objective",
    "points": len(points),
    "chemistry_solves": evaluator.calls["thermochemistry"],
    "performance_solves": evaluator.calls["performance"],
    "fluid_property_evaluations": evaluator.fluid_calls,
    "seconds": elapsed,
    "points_with_density_impulse": len(with_metric),
    "best_evaluated_feasible": {
        "values": dict(best.point.values),
        "density_impulse": best.metrics["density_impulse"],
        "specific_impulse": best.metrics["specific_impulse"],
        "bulk_propellant_density": best.metrics["bulk_propellant_density"],
    },
    "note": ("410 design points, 41 chemistry states and exactly two fluid "
             "evaluations: a study varies no quantity that changes a stream "
             "state, so the densities are computed once each"),
}
write("integrated_density_study.json", study_report)


# ===========================================================================
# 4. direct-solve parity for the density metrics
# ===========================================================================
print("direct-solve parity")

differences = []
compared = 0
for entry in points[:40]:
    of = float(entry.point.values["oxidiser_fuel_ratio"])
    fuel = stream_density(fluids, PRODUCTION_FLUID_MAPPING.require("LCH4"),
                          111.643, FEED)
    oxidiser = stream_density(fluids, PRODUCTION_FLUID_MAPPING.require("LOX"),
                              90.17, FEED)
    bulk = mixture_bulk_density(of, fuel, oxidiser)
    c_eff = entry.metrics["effective_exhaust_velocity"]
    isp = entry.metrics["specific_impulse"]
    if c_eff is None or isp is None:
        continue
    direct = density_impulse(bulk, c_eff, isp).value
    for name, cached, recomputed in (
            ("bulk_propellant_density", entry.metrics["bulk_propellant_density"],
             bulk.density),
            ("fuel_density", entry.metrics["fuel_density"], fuel.density),
            ("oxidiser_density", entry.metrics["oxidiser_density"],
             oxidiser.density),
            ("density_impulse", entry.metrics["density_impulse"], direct)):
        compared += 1
        if cached != recomputed:
            differences.append({"point": dict(entry.point.values),
                                "metric": name, "cached": cached,
                                "recomputed": recomputed})
write("direct_solve_parity.json", {
    "purpose": "cached study metrics against a direct recomputation",
    "comparisons": compared,
    "differences": len(differences),
    "detail": differences[:5],
    "note": "exact float equality, not a tolerance",
})


# ===========================================================================
# 5. state snapshot consistency
# ===========================================================================
print("state snapshot consistency")

case = base_case()
fuel = stream_density(fluids, PRODUCTION_FLUID_MAPPING.require("LCH4"),
                      case.fuel_temperature, FEED)
oxidiser = stream_density(fluids, PRODUCTION_FLUID_MAPPING.require("LOX"),
                          case.oxidiser_temperature, FEED)
write("state_snapshot_consistency.json", {
    "purpose": ("density and chemistry must read the same requested state; "
                "density at T1 with chemistry at T2 would be undetectable "
                "in the numbers"),
    "chamber_case": {"fuel_temperature_K": case.fuel_temperature,
                     "oxidiser_temperature_K": case.oxidiser_temperature},
    "fuel_density_state": {"temperature_K": fuel.temperature,
                           "pressure_Pa": fuel.pressure, "phase": fuel.phase},
    "oxidiser_density_state": {"temperature_K": oxidiser.temperature,
                               "pressure_Pa": oxidiser.pressure,
                               "phase": oxidiser.phase},
    "fuel_temperature_agrees": fuel.temperature == case.fuel_temperature,
    "oxidiser_temperature_agrees":
        oxidiser.temperature == case.oxidiser_temperature,
    "both_pressures_are_the_feed_pressure":
        fuel.pressure == FEED and oxidiser.pressure == FEED,
    "feed_pressure_is_not_the_chamber_pressure":
        FEED != case.chamber_pressure,
})


# ===========================================================================
# 6. soak and memory
# ===========================================================================
print("soak and memory")

tracemalloc.start()
started = time.perf_counter()
count = 0
for round_index in range(10):
    for temperature in range(80, 100):
        evaluate(OXYGEN, float(temperature), FEED)
        count += 1
    for temperature in range(105, 125):
        evaluate(METHANE, float(temperature), FEED)
        count += 1
    for temperature in range(15, 30):
        from rocketforge.physics.fluids import HYDROGEN

        evaluate(HYDROGEN, float(temperature), 5.0e5)
        count += 1
soak_seconds = time.perf_counter() - started
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

retained = []
tracemalloc.start()
for round_index in range(10):
    for temperature in range(80, 100):
        evaluate(OXYGEN, float(temperature), FEED)
    gc.collect()
    retained.append(tracemalloc.get_traced_memory()[0] / 1e6)
tracemalloc.stop()

write("soak_results.json", {
    "purpose": "sustained property evaluation",
    "evaluations": count,
    "seconds": soak_seconds,
    "evaluations_per_second": count / soak_seconds,
    "peak_MB": peak / 1e6,
})
write("memory_results.json", {
    "purpose": "does anything accumulate across repeated identical work?",
    "rounds": len(retained),
    "evaluations_per_round": 20,
    "retained_MB": [round(value, 3) for value in retained],
    "growth_MB": round(retained[-1] - retained[0], 4),
    "monotonic": all(b >= a for a, b in zip(retained, retained[1:])),
})

print("done")
