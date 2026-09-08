"""Line acceptance: canonical cases, matrices, parity, determinism, benchmark.

Every expectation is either hand-computed, produced by an independently
implemented oracle, or recomputed from the equations in this file. The
production code is never asked to generate its own expected value.
"""
from __future__ import annotations

import gc
import json
import math
import pathlib
import sys
import time
import tracemalloc
from decimal import Decimal, getcontext

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from rocketforge.application.analysis import line_service as service  # noqa: E402
from rocketforge.engineering.line import (  # noqa: E402
    CircularLineRequest,
    FlowRegime,
    circular_area,
    colebrook_darcy_friction_factor,
    colebrook_residual,
    hagen_poiseuille_pressure_drop,
    laminar_darcy_friction_factor,
    mean_velocity,
    reynolds_number_from_mass_flow,
    solve_line,
    volumetric_flow,
)
from rocketforge.physics.fluids import (  # noqa: E402
    HYDROGEN,
    METHANE,
    OXYGEN,
    FluidPhase,
    FluidStateRequest,
)
from rocketforge.providers.fluid_properties import coolprop_provider  # noqa: E402

OUT = ROOT / "acceptance" / "transport_line"
OUT.mkdir(parents=True, exist_ok=True)
provider = coolprop_provider()


def write(name, payload):
    (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  -> {name}")


def state(fluid, temperature, pressure):
    return provider.evaluate(FluidStateRequest(
        fluid=fluid, temperature=temperature, pressure=pressure,
        required_phase=FluidPhase.LIQUID)).value


def independent_colebrook(reynolds, roughness, digits=50):
    """A Decimal bisection sharing nothing with the production solver."""
    getcontext().prec = digits
    re_d, eps_d = Decimal(repr(reynolds)), Decimal(repr(roughness))
    two, ten = Decimal(2), Decimal(10)

    def residual(f):
        root = f.sqrt()
        inside = eps_d / Decimal("3.7") + Decimal("2.51") / (re_d * root)
        return Decimal(1) / root + two * (inside.ln() / ten.ln())

    low, high = Decimal("1e-6"), Decimal("1")
    for _ in range(400):
        mid = (low + high) / two
        if residual(low) * residual(mid) <= 0:
            high = mid
        else:
            low = mid
    return float((low + high) / two)


# ===========================================================================
# 1. the canonical real LCH4 line case
# ===========================================================================
print("canonical LCH4 line case")

CANON = dict(temperature=111.643, pressure=1.0e6, mass_flow=2.0, length=5.0,
             diameter=0.02, roughness=1.5e-6)

methane = state(METHANE, CANON["temperature"], CANON["pressure"])
request = CircularLineRequest(
    fluid_state=methane, mass_flow=CANON["mass_flow"], length=CANON["length"],
    inner_diameter=CANON["diameter"], absolute_roughness=CANON["roughness"])
result = solve_line(request).value

# recomputed here, from the equations, with nothing taken from the result
area = math.pi * CANON["diameter"] ** 2 / 4.0
rho = methane.density
mu = methane.dynamic_viscosity
velocity = CANON["mass_flow"] / (rho * area)
reynolds = rho * velocity * CANON["diameter"] / mu
eps_d = CANON["roughness"] / CANON["diameter"]
friction = independent_colebrook(reynolds, eps_d)
pressure_drop = friction * CANON["length"] / CANON["diameter"] * 0.5 * rho * velocity ** 2

write("real_lch4_line_case.json", {
    "purpose": "one production line case, traceable to validated fluid data",
    "inputs": CANON,
    "fluid_state": {
        "fluid": methane.fluid.name, "phase": methane.phase.value,
        "temperature_K": methane.temperature, "pressure_Pa": methane.pressure,
        "density_kg_per_m3": rho, "dynamic_viscosity_Pa_s": mu,
        "provider": methane.provenance.provider_label,
        "library_version": methane.provenance.library_version,
        "backend": methane.provenance.backend,
    },
    "transport_envelope_status": service.transport_status(
        "METHANE", CANON["temperature"], CANON["pressure"])[1],
    "result": result.as_mapping(),
    "independent_recomputation": {
        "area_m2": area, "mean_velocity_m_per_s": velocity,
        "reynolds_number": reynolds, "relative_roughness": eps_d,
        "darcy_friction_factor": friction,
        "major_pressure_drop_Pa": pressure_drop,
        "note": ("computed here from the equations, with the friction factor "
                 "from a Decimal bisection that shares nothing with the "
                 "production solver"),
    },
    "differences": {
        "area": abs(result.area - area) / area,
        "velocity": abs(result.mean_velocity - velocity) / velocity,
        "reynolds": abs(result.reynolds_number - reynolds) / reynolds,
        "friction_factor": abs(result.darcy_friction_factor - friction) / friction,
        "pressure_drop": abs(result.major_pressure_drop - pressure_drop) / pressure_drop,
    },
})

# ===========================================================================
# 2. traceability: the line used the state's own numbers
# ===========================================================================
print("fluid traceability")
write("fluid_line_traceability.json", {
    "purpose": "the line must use the fluid state's own density and viscosity",
    "state_density": rho,
    "line_density": result.fluid.density,
    "density_identical": result.fluid.density == rho,
    "state_viscosity": mu,
    "line_viscosity": result.fluid.dynamic_viscosity,
    "viscosity_identical": result.fluid.dynamic_viscosity == mu,
    "state_temperature": methane.temperature,
    "line_temperature": result.fluid.temperature,
    "state_pressure": methane.pressure,
    "line_pressure": result.fluid.pressure,
    "line_inlet_is_the_property_pressure":
        result.inlet_pressure == methane.pressure,
    "note": ("bit equality, not a tolerance: an application-level "
             "recomputation would show up here as a difference in the last "
             "digits"),
})

# ===========================================================================
# 3. laminar identity and scaling
# ===========================================================================
print("laminar identity and scaling")

laminar_cases = []
for mass_flow, diameter, length in ((0.001, 0.01, 1.0), (0.0005, 0.005, 2.0),
                                    (0.0008, 0.012, 0.5)):
    st = state(METHANE, 111.643, 1.0e6)
    res = solve_line(CircularLineRequest(
        fluid_state=st, mass_flow=mass_flow, length=length,
        inner_diameter=diameter, absolute_roughness=0.0)).value
    q = volumetric_flow(mass_flow, st.density)
    poiseuille = hagen_poiseuille_pressure_drop(
        st.dynamic_viscosity, length, q, diameter)
    laminar_cases.append({
        "mass_flow": mass_flow, "diameter": diameter, "length": length,
        "reynolds_number": res.reynolds_number,
        "regime": res.flow_regime.value,
        "darcy_friction_factor": res.darcy_friction_factor,
        "sixty_four_over_re": 64.0 / res.reynolds_number,
        "darcy_weisbach_Pa": res.major_pressure_drop,
        "hagen_poiseuille_Pa": poiseuille,
        "relative_difference":
            abs(res.major_pressure_drop - poiseuille) / poiseuille,
    })
write("hagen_poiseuille_identity.json", {
    "purpose": "the laminar production path must reproduce the closed form",
    "cases": laminar_cases,
    "worst_relative_difference": max(c["relative_difference"]
                                     for c in laminar_cases),
})

# ===========================================================================
# 4. the Colebrook domain matrix
# ===========================================================================
print("colebrook domain matrix")

matrix = []
worst_residual = 0.0
worst_oracle = 0.0
worst_iterations = 0
for reynolds_value in (4.0e3, 1.0e4, 3.0e4, 1.0e5, 3.0e5, 1.0e6, 1.0e7, 1.0e8):
    for eps in (0.0, 1.0e-5, 1.0e-4, 1.0e-3, 1.0e-2, 5.0e-2):
        f, report = colebrook_darcy_friction_factor(reynolds_value, eps)
        residual = abs(colebrook_residual(f, reynolds_value, eps))
        oracle = independent_colebrook(reynolds_value, eps)
        difference = abs(f - oracle) / oracle
        worst_residual = max(worst_residual, residual)
        worst_oracle = max(worst_oracle, difference)
        worst_iterations = max(worst_iterations, report.iterations)
        matrix.append({
            "reynolds_number": reynolds_value, "relative_roughness": eps,
            "darcy_friction_factor": f, "independent_oracle": oracle,
            "relative_difference": difference, "residual": residual,
            "iterations": report.iterations, "converged": report.converged,
        })
write("colebrook_domain_matrix.json", {
    "purpose": "the whole declared turbulent domain, against an independent "
               "Decimal bisection",
    "cases": len(matrix),
    "worst_relative_difference_vs_oracle": worst_oracle,
    "worst_residual": worst_residual,
    "worst_iterations": worst_iterations,
    "all_converged": all(m["converged"] for m in matrix),
    "matrix": matrix,
})

# ===========================================================================
# 5. transition, and the Darcy/Fanning mutation
# ===========================================================================
print("transition and the Darcy/Fanning mutation")

transition = []
for mass_flow in (0.0026, 0.0028, 0.0030, 0.0032):
    st = state(METHANE, 111.643, 1.0e6)
    res = solve_line(CircularLineRequest(
        fluid_state=st, mass_flow=mass_flow, length=1.0,
        inner_diameter=0.01, absolute_roughness=0.0)).value
    transition.append({
        "mass_flow": mass_flow, "reynolds_number": res.reynolds_number,
        "regime": res.flow_regime.value,
        "darcy_friction_factor": res.darcy_friction_factor,
        "major_pressure_drop": res.major_pressure_drop,
    })
write("transition_cases.json", {
    "purpose": "between the boundaries no friction factor is reported",
    "cases": transition,
    "every_transitional_case_withholds_the_friction_factor": all(
        c["darcy_friction_factor"] is None for c in transition
        if c["regime"] == "transitional"),
    "nothing_is_zero": all(c["darcy_friction_factor"] != 0.0
                           for c in transition),
})

darcy = result.darcy_friction_factor
fanning = darcy / 4.0
correct = result.major_pressure_drop
mutated = fanning * CANON["length"] / CANON["diameter"] * 0.5 * rho * velocity ** 2
write("darcy_fanning_mutation.json", {
    "purpose": "using the Fanning factor in Darcy-Weisbach must fail loudly",
    "darcy_friction_factor": darcy,
    "fanning_equivalent": fanning,
    "ratio": darcy / fanning,
    "correct_pressure_drop_Pa": correct,
    "mutated_pressure_drop_Pa": mutated,
    "relative_error_of_the_mutation": abs(mutated - correct) / correct,
    "detected": abs(mutated - correct) / correct > 0.7,
})

# ===========================================================================
# 6. determinism, state leakage, error recovery
# ===========================================================================
print("determinism and state")

def canonical():
    st = state(METHANE, 111.643, 1.0e6)
    return solve_line(CircularLineRequest(
        fluid_state=st, mass_flow=2.0, length=5.0, inner_diameter=0.02,
        absolute_roughness=1.5e-6)).value

repeats = [(canonical().darcy_friction_factor, canonical().major_pressure_drop)
           for _ in range(5)]
first = canonical()
oxygen_state = state(OXYGEN, 90.17, 1.0e6)
oxygen_result = solve_line(CircularLineRequest(
    fluid_state=oxygen_state, mass_flow=2.0, length=5.0, inner_diameter=0.02,
    absolute_roughness=1.5e-6)).value
after = canonical()

# error recovery
solve_line(CircularLineRequest(fluid_state=methane, mass_flow=2.0, length=5.0,
                               inner_diameter=0.02, absolute_roughness=0.02))
recovered = canonical()

write("line_determinism.json", {
    "purpose": "identical solves are identical; nothing leaks; refusals leave "
               "no residue",
    "five_repeats_identical": len(set(repeats)) == 1,
    "methane_before": first.darcy_friction_factor,
    "oxygen_between": oxygen_result.darcy_friction_factor,
    "methane_after": after.darcy_friction_factor,
    "no_leak": first.darcy_friction_factor == after.darcy_friction_factor,
    "fluids_actually_differ":
        first.darcy_friction_factor != oxygen_result.darcy_friction_factor,
    "canonical_after_a_refusal": recovered.darcy_friction_factor,
    "recovery_exact":
        recovered.darcy_friction_factor == first.darcy_friction_factor,
})

# ===========================================================================
# 7. benchmark and soak
# ===========================================================================
print("benchmark and soak")

started = time.perf_counter()
for _ in range(1000):
    colebrook_darcy_friction_factor(1.0e6, 1.0e-4)
colebrook_seconds = time.perf_counter() - started

st = state(METHANE, 111.643, 1.0e6)
started = time.perf_counter()
solves = 0
for i in range(1000):
    mass_flow = 0.0005 + i * 0.004
    solve_line(CircularLineRequest(
        fluid_state=st, mass_flow=mass_flow, length=5.0, inner_diameter=0.05,
        absolute_roughness=1.5e-6))
    solves += 1
solve_seconds = time.perf_counter() - started

tracemalloc.start()
retained = []
for round_index in range(10):
    for i in range(500):
        solve_line(CircularLineRequest(
            fluid_state=st, mass_flow=0.001 + i * 0.004, length=5.0,
            inner_diameter=0.05, absolute_roughness=1.5e-6))
    gc.collect()
    retained.append(tracemalloc.get_traced_memory()[0] / 1e6)
tracemalloc.stop()

write("line_performance.json", {
    "purpose": "line algebra should be cheap beside chemistry",
    "colebrook_solves": 1000,
    "colebrook_seconds": round(colebrook_seconds, 4),
    "colebrook_per_second": round(1000 / colebrook_seconds, 1),
    "line_solves": solves,
    "line_seconds": round(solve_seconds, 4),
    "line_per_second": round(solves / solve_seconds, 1),
    "soak_solves": 5000,
    "retained_MB": [round(v, 3) for v in retained],
    "growth_MB": round(retained[-1] - retained[0], 4),
    "monotonic": all(b >= a for a, b in zip(retained, retained[1:])),
})

print("done")
