"""Sustained load: fluid states, corrected chamber solves, repeated studies.

Long enough to matter. A leak that shows at ten evaluations is a bug anyone
would find; the ones worth a soak test show at ten thousand.
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
from rocketforge.physics.fluids import (  # noqa: E402
    HYDROGEN,
    METHANE,
    OXYGEN,
    FluidPhase,
    FluidStateRequest,
)
from rocketforge.providers.cea import CEAThermochemistryProvider  # noqa: E402
from rocketforge.providers.cea.enthalpy_coupling import (  # noqa: E402
    ReactantEnthalpyPolicy,
    ReactantFluidBinding,
)
from rocketforge.providers.cea.propellants import LIQUID_METHANE, LOX  # noqa: E402
from rocketforge.physics.thermochemistry import (  # noqa: E402
    ChamberEquilibriumRequest,
    MixtureRatio,
    Phase,
    PropellantStream,
)
from rocketforge.providers.fluid_properties import coolprop_provider  # noqa: E402

OUT = ROOT / "acceptance" / "fluids_foundation"
FEED = 3.0e5
fluids = coolprop_provider()
chemistry = CEAThermochemistryProvider()

SWEEPS = (
    (OXYGEN, 81.0, 99.0, FEED),
    (METHANE, 102.0, 120.0, FEED),
    (HYDROGEN, 15.0, 30.0, 5.0e5),
)


def evaluate(fluid, temperature, pressure):
    return fluids.evaluate(FluidStateRequest(
        fluid=fluid, temperature=temperature, pressure=pressure)).value


# --- 1. ten thousand fluid states ---------------------------------------
print("fluid soak")
tracemalloc.start()
started = time.perf_counter()
evaluations = 0
first: dict = {}
last: dict = {}
for round_index in range(120):
    for fluid, low, high, pressure in SWEEPS:
        for step in range(30):
            temperature = low + (high - low) * step / 29.0
            state = evaluate(fluid, temperature, pressure)
            evaluations += 1
            if state is not None and step == 0:
                key = fluid.name
                if key not in first:
                    first[key] = state.density
                last[key] = state.density
fluid_seconds = time.perf_counter() - started
_current, fluid_peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

report = {
    "purpose": "sustained fluid, coupling and study load",
    "fluid_states": {
        "evaluations": evaluations,
        "seconds": round(fluid_seconds, 3),
        "per_second": round(evaluations / fluid_seconds, 1),
        "peak_MB": round(fluid_peak / 1e6, 3),
        "first_and_last_agree": first == last,
        "note": ("the same state at the start and the end of ten thousand "
                 "evaluations must give the same density, or something is "
                 "accumulating in the provider"),
    },
}
print(f"  {evaluations} evaluations in {fluid_seconds:.2f}s")


# --- 2. hundreds of corrected chamber solves ----------------------------
print("coupling soak")


def bindings():
    return {"O2(L)": ReactantFluidBinding(fluid=OXYGEN, pressure=FEED,
                                          required_phase=FluidPhase.LIQUID),
            "CH4(L)": ReactantFluidBinding(fluid=METHANE, pressure=FEED,
                                           required_phase=FluidPhase.LIQUID)}


def request(ox_t, of):
    return ChamberEquilibriumRequest(
        fuel=PropellantStream(propellant=LIQUID_METHANE, temperature=111.643,
                              pressure=FEED, phase=Phase.LIQUID),
        oxidiser=PropellantStream(propellant=LOX, temperature=ox_t,
                                  pressure=FEED, phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(of),
        chamber_pressure=1.0e7)


tracemalloc.start()
started = time.perf_counter()
solves = 0
temperatures: list[float] = []
canonical_first = chemistry.solve_chamber(
    request(90.17, 3.4),
    enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
    fluid_provider=fluids, reactant_bindings=bindings()).value.temperature
for round_index in range(20):
    for step in range(20):
        ox_t = 86.0 + 12.0 * step / 19.0
        of = 2.8 + 1.2 * (step % 7) / 6.0
        result = chemistry.solve_chamber(
            request(ox_t, of),
            enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
            fluid_provider=fluids, reactant_bindings=bindings())
        solves += 1
        if result.value is not None:
            temperatures.append(float(result.value.temperature))
canonical_last = chemistry.solve_chamber(
    request(90.17, 3.4),
    enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
    fluid_provider=fluids, reactant_bindings=bindings()).value.temperature
coupling_seconds = time.perf_counter() - started
_current, coupling_peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

report["corrected_chamber_solves"] = {
    "solves": solves,
    "seconds": round(coupling_seconds, 3),
    "per_second": round(solves / coupling_seconds, 2),
    "peak_MB": round(coupling_peak / 1e6, 3),
    "canonical_before": canonical_first,
    "canonical_after": canonical_last,
    "canonical_unchanged": canonical_first == canonical_last,
    "distinct_chamber_temperatures": len(set(temperatures)),
}
print(f"  {solves} corrected solves in {coupling_seconds:.2f}s")


# --- 3. repeated identical studies --------------------------------------
print("study repeats")

case = thermo.ChamberCase(fuel="LCH4", oxidiser="LOX",
                          oxidiser_fuel_ratio=3.4, chamber_pressure=1.0e7,
                          fuel_temperature=111.643, oxidiser_temperature=90.17)
study_setup = svc.TradeStudySetup(chamber=case,
                                  performance=perf.PerformanceCase(),
                                  feed_pressure=FEED)
variables = (
    LinearRangeVariable(key="oxidiser_fuel_ratio", label="O/F", unit="",
                        stage="thermochemistry",
                        domain=VariableDomain(minimum=0.0,
                                              exclusive_minimum=True),
                        start=2.5, end=4.5, count=21),
    LinearRangeVariable(key="area_ratio", label="Ae/At", unit="",
                        stage="performance", domain=VariableDomain(minimum=1.0),
                        start=10.0, end=100.0, count=10),
)
definition = svc.build_definition(
    study_setup, variables,
    objectives=(ObjectiveDefinition(metric="density_impulse",
                                    direction=ObjectiveDirection.MAXIMIZE),))

retained: list[float] = []
signatures: list[int] = []
tracemalloc.start()
for round_index in range(10):
    evaluator = svc.RocketForgeEvaluator(study_setup)
    result = svc.run_trade_study(definition, study_setup, evaluator=evaluator)
    # A hash, not the data. Retaining ten full 210-point signatures is ~19 kB
    # per round of *harness* memory, which reads as a perfectly linear leak in
    # the product and is nothing of the kind. Measured that way first, then
    # corrected: the growth below is what the code under test actually keeps.
    signatures.append(hash(tuple(
        (p.metrics.get("density_impulse"), p.is_pareto_efficient)
        for p in result.points)))
    del result
    gc.collect()
    retained.append(tracemalloc.get_traced_memory()[0] / 1e6)
tracemalloc.stop()

report["repeated_studies"] = {
    "rounds": len(retained),
    "points_each": 210,
    "all_results_identical": all(s == signatures[0] for s in signatures),
    "retained_MB": [round(value, 3) for value in retained],
    "growth_MB": round(retained[-1] - retained[0], 4),
    "monotonic": all(b >= a for a, b in zip(retained, retained[1:])),
    "fluid_evaluations_per_study": evaluator.fluid_calls,
    "chemistry_solves_per_study": evaluator.calls["thermochemistry"],
}
print(f"  {len(retained)} studies, growth "
      f"{report['repeated_studies']['growth_MB']} MB")

(OUT / "soak_results.json").write_text(json.dumps(report, indent=2),
                                       encoding="utf-8")
print(f"-> {OUT / 'soak_results.json'}")
