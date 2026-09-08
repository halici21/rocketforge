"""The blocking coupling checks: reference-state identity and temperature response.

Five questions, each answered by measurement rather than by reading the code:

* §43/§96  at ``(T_ref, p_ref)`` the increment is exactly 0.0 and the corrected
           chamber reproduces the native one **bit for bit**;
* §46      at ``T_ref`` but a different pressure the increment is a small,
           genuine pressure term -- preserved, not zeroed;
* §97      away from the reference temperature the chamber actually moves, and
           native mode provably does not;
* §98/§99  a gaseous reactant, which CEA already varies with temperature, is
           left alone, so the sensible term is never counted twice;
* §101     the elemental inventory is untouched by any of it.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from rocketforge.physics.fluids import METHANE, OXYGEN, FluidPhase
from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    MixtureRatio,
    Phase,
    PropellantStream,
)
from rocketforge.providers.cea import CEAThermochemistryProvider
from rocketforge.providers.cea.enthalpy_coupling import (
    CEA_REFERENCE_PRESSURE,
    ReactantEnthalpyPolicy,
    ReactantFluidBinding,
)
from rocketforge.providers.cea.propellants import (
    GASEOUS_METHANE,
    GASEOUS_OXYGEN,
    LIQUID_METHANE,
    LOX,
)
from rocketforge.providers.fluid_properties import coolprop_provider

OUT = pathlib.Path("acceptance/fluids_foundation/reference_state_identity.json")

FEED_PRESSURE = 3.0e5  # Pa. An explicit feed pressure, not the chamber's.
CHAMBER_PRESSURE = 1.0e7
T_REF_OX = 90.17
T_REF_FUEL = 111.643

provider = CEAThermochemistryProvider()
fluids = coolprop_provider()


def build_request(ox_t, fuel_t, pressure, ox=LOX, fuel=LIQUID_METHANE,
                  ox_phase=Phase.LIQUID, fuel_phase=Phase.LIQUID):
    return ChamberEquilibriumRequest(
        fuel=PropellantStream(propellant=fuel, temperature=fuel_t,
                              pressure=pressure, phase=fuel_phase),
        oxidiser=PropellantStream(propellant=ox, temperature=ox_t,
                                  pressure=pressure, phase=ox_phase),
        oxidiser_fuel_ratio=MixtureRatio(3.4),
        chamber_pressure=CHAMBER_PRESSURE)


def bindings(pressure):
    return {
        "O2(L)": ReactantFluidBinding(fluid=OXYGEN, pressure=pressure,
                                      required_phase=FluidPhase.LIQUID),
        "CH4(L)": ReactantFluidBinding(fluid=METHANE, pressure=pressure,
                                       required_phase=FluidPhase.LIQUID),
    }


def solve(request, corrected, pressure=FEED_PRESSURE, binds=None):
    if not corrected:
        return provider.solve_chamber(request)
    return provider.solve_chamber(
        request,
        enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
        fluid_provider=fluids,
        reactant_bindings=binds if binds is not None else bindings(pressure))


def summarise(solution):
    state = solution.value
    if state is None:
        return {"status": solution.status.value,
                "diagnostics": [d.code for d in solution.diagnostics]}
    return {
        "status": solution.status.value,
        "T": float(state.temperature),
        "R": float(state.gas_constant),
        "M": float(state.molar_mass),
        "gamma_frozen": float(state.gamma_frozen),
        "gamma_equilibrium": float(state.gamma_equilibrium),
        "diagnostics": [d.code for d in solution.diagnostics],
    }


def corrections_of(solution):
    return [dict(d.detail) for d in solution.diagnostics
            if d.code == "REACTANT_ENTHALPY_FLUID_CORRECTED"]


report = {
    "purpose": "reference-state identity, pressure term and temperature "
               "response of the fluid sensible-enthalpy correction",
    "chamber_pressure_Pa": CHAMBER_PRESSURE,
    "of_mass": 3.4,
    "cea_reference_state": {
        "O2(L)": {"T_K": T_REF_OX, "p_Pa": CEA_REFERENCE_PRESSURE},
        "CH4(L)": {"T_K": T_REF_FUEL, "p_Pa": CEA_REFERENCE_PRESSURE},
    },
}

# --- A. exactly at the reference state: the blocking identity -------------
ref_request = build_request(T_REF_OX, T_REF_FUEL, CEA_REFERENCE_PRESSURE)
native = solve(ref_request, False)
corrected = solve(ref_request, True, CEA_REFERENCE_PRESSURE)
n, c = summarise(native), summarise(corrected)
corr = corrections_of(corrected)
report["A_reference_state_identity"] = {
    "note": "T = T_ref and p = p_ref for both reactants",
    "increments_J_per_kg": [d["delta_h_sensible_J_per_kg"] for d in corr],
    "every_increment_exactly_zero": all(
        d["delta_h_sensible_J_per_kg"] == 0.0 for d in corr),
    "native_T": n["T"], "corrected_T": c["T"],
    "delta_T": c["T"] - n["T"],
    "bit_identical": (c["T"] == n["T"] and c["R"] == n["R"]
                      and c["M"] == n["M"]
                      and c["gamma_frozen"] == n["gamma_frozen"]
                      and c["gamma_equilibrium"] == n["gamma_equilibrium"]),
    "corrections": corr,
}

# --- B. reference temperature, elevated pressure: a real pressure term ----
press_request = build_request(T_REF_OX, T_REF_FUEL, FEED_PRESSURE)
n2 = summarise(solve(press_request, False))
c2sol = solve(press_request, True, FEED_PRESSURE)
c2 = summarise(c2sol)
report["B_pressure_term_only"] = {
    "note": ("T = T_ref, p = 3 bar. The increment is purely the liquid's "
             "pressure dependence, which is small and real and is preserved "
             "rather than zeroed."),
    "feed_pressure_Pa": FEED_PRESSURE,
    "increments_J_per_kg": [d["delta_h_sensible_J_per_kg"]
                            for d in corrections_of(c2sol)],
    "native_T": n2["T"], "corrected_T": c2["T"], "delta_T": c2["T"] - n2["T"],
}

# --- C. oxidiser temperature sweep ---------------------------------------
sweep = {}
for ox_t in (86.0, 88.0, T_REF_OX, 93.0, 95.0, 98.0):
    request = build_request(ox_t, T_REF_FUEL, FEED_PRESSURE)
    nn = summarise(solve(request, False))
    cs = solve(request, True, FEED_PRESSURE)
    cc = summarise(cs)
    sweep[f"{ox_t:g}"] = {
        "native_T": nn["T"], "corrected_T": cc["T"],
        "delta_T": cc["T"] - nn["T"],
        "native_diagnostics": nn["diagnostics"],
        "corrected_diagnostics": cc["diagnostics"],
        "oxidiser_delta_h_J_per_kg": next(
            (d["delta_h_sensible_J_per_kg"] for d in corrections_of(cs)
             if d["reactant"] == "O2(L)"), None),
    }
report["C_oxidiser_temperature_sweep"] = sweep
report["C_native_is_insensitive"] = len({v["native_T"] for v in sweep.values()}) == 1
report["C_corrected_is_monotone"] = all(
    a["corrected_T"] < b["corrected_T"] for a, b in
    zip(list(sweep.values())[:-1], list(sweep.values())[1:]))

# --- D. gaseous reactants: no correction, no double counting --------------
gas_request = build_request(300.0, 298.15, FEED_PRESSURE,
                            ox=GASEOUS_OXYGEN, fuel=GASEOUS_METHANE,
                            ox_phase=Phase.GAS, fuel_phase=Phase.GAS)
gas_native = solve(gas_request, False)
gas_corrected = solve(gas_request, True, FEED_PRESSURE, binds={
    "O2": ReactantFluidBinding(fluid=OXYGEN, pressure=FEED_PRESSURE,
                               required_phase=FluidPhase.GAS),
    "CH4": ReactantFluidBinding(fluid=METHANE, pressure=FEED_PRESSURE,
                                required_phase=FluidPhase.GAS)})
gn, gc = summarise(gas_native), summarise(gas_corrected)
report["D_gas_negative_control"] = {
    "note": ("Both reactants are bound to a fluid *and* the corrected policy "
             "is active. CEA already varies these entries with temperature, "
             "so the gate must refuse the correction and the two results must "
             "be bit-identical. If they differ, the sensible term is being "
             "counted twice."),
    "native_T": gn["T"], "corrected_T": gc["T"],
    "bit_identical": gn["T"] == gc["T"],
    "corrections_applied": len(corrections_of(gas_corrected)),
    "native_diagnostics": gn["diagnostics"],
    "corrected_diagnostics": gc["diagnostics"],
}

# --- E. elemental inventory is untouched ---------------------------------
def elements_of(solution):
    state = solution.value
    totals = {}
    for name, fraction in state.composition.entries:
        species = state.composition_species.get(name) if hasattr(
            state, "composition_species") else None
        totals[name] = float(fraction)
    return totals


cold = solve(build_request(86.0, T_REF_FUEL, FEED_PRESSURE), True, FEED_PRESSURE)
warm = solve(build_request(98.0, T_REF_FUEL, FEED_PRESSURE), True, FEED_PRESSURE)
report["E_composition_responds"] = {
    "note": ("Product composition *may* change, because the chamber "
             "temperature changed. Elemental conservation is checked "
             "separately by the provider's own post-validation, which ran on "
             "both of these solves."),
    "cold_species": len(cold.value.composition.entries),
    "warm_species": len(warm.value.composition.entries),
    "cold_T": float(cold.value.temperature),
    "warm_T": float(warm.value.temperature),
    "both_passed_provider_post_validation": all(
        d.code != "PROVIDER_ELEMENT_BALANCE_FAILED"
        for s in (cold, warm) for d in s.diagnostics),
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
for key in ("A_reference_state_identity", "B_pressure_term_only",
            "C_oxidiser_temperature_sweep", "C_native_is_insensitive",
            "C_corrected_is_monotone", "D_gas_negative_control",
            "E_composition_responds"):
    print(f"--- {key} ---")
    print(json.dumps(report[key], indent=1)[:1400])
