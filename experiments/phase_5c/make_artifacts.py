"""Phase 5C acceptance-artifact generation. Experimental, not production code.

Run in the CEA-enabled environment:

    .venv-cea\\Scripts\\python.exe experiments/phase_5c/make_artifacts.py
"""
from __future__ import annotations

import csv
import json
import pathlib
import statistics
import subprocess
import sys
import time

import numpy as np

# Run as a file path from anywhere: the project root is two levels up, and a
# script under experiments/ does not get it on sys.path for free.
_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    ExpansionMode,
    MixtureRatio,
    Phase,
    PropellantStream,
    to_jsonable,
)
from rocketforge.providers.cea import (
    GASEOUS_METHANE,
    GASEOUS_OXYGEN,
    LIQUID_METHANE,
    LOX,
    CEAThermochemistryProvider,
    check_availability,
)
import rocketforge.providers.cea.mapping as mp
from rocketforge.providers.cea.oracle import run_rocket_oracle
from rocketforge.providers.cea.species import CHO_PRODUCT_SPECIES, phase_of_cea_name

OUT = pathlib.Path("acceptance/phase_5c")
OUT.mkdir(parents=True, exist_ok=True)

provider = CEAThermochemistryProvider()
availability = check_availability()
resources = provider.resources()


def request(fuel, fuel_t, oxidiser, ox_t, of, pc,
            fuel_phase=Phase.LIQUID, ox_phase=Phase.LIQUID):
    return ChamberEquilibriumRequest(
        fuel=PropellantStream(fuel, fuel_t, phase=fuel_phase),
        oxidiser=PropellantStream(oxidiser, ox_t, phase=ox_phase),
        oxidiser_fuel_ratio=MixtureRatio(of), chamber_pressure=pc)


def write(name: str, payload) -> None:
    (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")


# --- capabilities ---------------------------------------------------------
write("cea_capabilities.json", {
    "provider_id": provider.provider_id,
    "provider_version": provider.version,
    "cea_version": availability.version,
    "cea_library_version": availability.library_version,
    "status": availability.status.value,
    "capabilities": to_jsonable(provider.capabilities),
    "thermo_lib": {"path": resources.thermo_path,
                   "bytes": resources.thermo_bytes,
                   "sha256": resources.thermo_sha256},
})

# --- the canonical production case ---------------------------------------
canonical = request(LIQUID_METHANE, 111.643, LOX, 90.17, 3.4, 10.0e6)
solution = provider.solve_chamber(canonical)
state = solution.value
write("cea_production_case.json", {
    "case": {"fuel": "LCH4 -> CH4(L)", "oxidiser": "LOX -> O2(L)",
             "of_mass": 3.4, "chamber_pressure_Pa": 10.0e6,
             "fuel_temperature_K": 111.643, "oxidiser_temperature_K": 90.17,
             "fuel_phase": "liquid", "oxidiser_phase": "liquid",
             "constraint": "HP", "chemistry_mode": "equilibrium"},
    "status": solution.status.value,
    "state": to_jsonable(state),
    "diagnostics": [to_jsonable(d) for d in solution.diagnostics],
})

# --- unit mapping ---------------------------------------------------------
with (OUT / "cea_unit_mapping.csv").open("w", newline="", encoding="utf-8") as fh:
    writer = csv.writer(fh)
    writer.writerow(["quantity", "cea_native_unit", "rocketforge_unit",
                     "conversion", "how_established"])
    for row in [
        ("pressure", "bar", "Pa", "x 1e5",
         "a solve given 100.0 reported P=100.0; the ideal-gas identity closed only at 1e7 Pa"),
        ("temperature", "K", "K", "none", "identical"),
        ("molar mass", "kg/kmol", "kg/mol", "/ 1e3",
         "p = rho R T closes only with M read as kg/kmol"),
        ("cp, cv", "kJ/(kg K)", "J/(kg K)", "x 1e3",
         "cp_fr - cv_fr = 0.38736 against a specific R of 387.36 J/(kg K)"),
        ("enthalpy", "kJ/kg", "J/kg", "x 1e3",
         "cross-checked against Cantera on the matched common case"),
        ("entropy", "kJ/(kg K)", "J/(kg K)", "x 1e3", "same"),
        ("density", "kg/m3", "kg/m3", "none",
         "p = rho R T closes with the raw value, unscaled"),
        ("gamma", "-", "-", "none", "dimensionless"),
        ("mole fraction", "-", "-", "none", "dimensionless"),
        ("c* (oracle)", "m/s", "m/s", "none", "Isp == Cf * c* exactly"),
        ("Isp (oracle)", "m/s", "m/s", "none",
         "Isp == Cf * c*; divide by g0 for seconds"),
    ]:
        writer.writerow(row)

# --- composition mapping --------------------------------------------------
chamber_input = mp.build_chamber_input(canonical)
raw = mp.solve_chamber_raw(provider._cea(), chamber_input)
with (OUT / "cea_composition_mapping.csv").open("w", newline="",
                                                encoding="utf-8") as fh:
    writer = csv.writer(fh)
    writer.writerow(["species", "cea_raw_mole_fraction",
                     "rocketforge_mole_fraction", "abs_difference", "phase"])
    for name in sorted(raw.mole_fractions, key=lambda k: -raw.mole_fractions[k]):
        a = raw.mole_fractions[name]
        b = state.composition.fraction_of(name)
        writer.writerow([name, repr(a), repr(b), repr(abs(a - b)),
                         phase_of_cea_name(name).value])

# --- operating matrix -----------------------------------------------------
matrix = []
for of in (2.5, 3.0, 3.4, 4.0, 4.5):
    for pc in (5.0e6, 10.0e6, 20.0e6):
        s = provider.solve_chamber(
            request(LIQUID_METHANE, 111.643, LOX, 90.17, of, pc))
        v = s.value
        residual = next((d.detail.get("residual") for d in s.diagnostics
                         if d.field == "element conservation" and d.detail), None)
        matrix.append({
            "of": of, "pc_Pa": pc, "status": s.status.value,
            "Tc_K": v.temperature if v else None,
            "M_kg_per_mol": v.molar_mass if v else None,
            "R_J_per_kgK": v.gas_constant if v else None,
            "gamma_s": v.gamma if v else None,
            "gamma_frozen": v.gamma_frozen if v else None,
            "density": v.density if v else None,
            "condensed_mass_fraction": v.condensed_mass_fraction if v else None,
            "element_residual": residual,
        })
write("cea_operating_matrix.json", matrix)

# --- rocket oracle --------------------------------------------------------
oracle = {}
for mode in (ExpansionMode.EQUILIBRIUM, ExpansionMode.FROZEN_AT_THROAT,
             ExpansionMode.FROZEN):
    result = run_rocket_oracle(
        provider._cea(), fuel_names=("CH4(L)",), oxidiser_names=("O2(L)",),
        fuel_weights=(1.0,), oxidiser_weights=(1.0,),
        reactant_temperatures=(111.643, 90.17), of_ratio=3.4,
        chamber_pressure=10.0e6, area_ratio=40.0,
        product_species=CHO_PRODUCT_SPECIES, expansion_mode=mode)
    oracle[mode.value] = to_jsonable(result)
write("cea_rocket_oracle.json", {
    "note": ("NASA CEA native rocket outputs. These are PROVIDER-NATIVE "
             "reference quantities, not RocketForge physics. RocketForge does "
             "not implement c*, Cf or Isp; ownership belongs to a future "
             "engineering.nozzle (ADR-15). Recorded with their full conditions "
             "so that Phase 5E can compare like for like."),
    "cases": oracle,
})

# --- matched common case, for the Cantera comparison ----------------------
common = request(GASEOUS_METHANE, 298.15, GASEOUS_OXYGEN, 298.15, 3.4, 10.0e6,
                 Phase.GAS, Phase.GAS)
common_state = provider.solve_chamber(common).unwrap()
write("cea_provider_common_case.json", {
    "case": {"reactants": "CH4 + O2 (gas)", "of_mass": 3.4,
             "T_reac_K": 298.15, "P_Pa": 10.0e6, "problem": "HP equilibrium",
             "species": list(common_state.provenance.species_set)},
    "provider": "RocketForge CEAThermochemistryProvider",
    "cea_version": availability.version,
    "thermo_sha256": resources.thermo_sha256,
    "Tc_K": common_state.temperature,
    "M_kg_per_mol": common_state.molar_mass,
    "R_J_per_kgK": common_state.gas_constant,
    "density": common_state.density,
    "gamma_s": common_state.gamma,
    "gamma_frozen": common_state.gamma_frozen,
    "cp_frozen": common_state.cp,
    "cv_frozen": common_state.cv,
    "X": dict(common_state.composition.fractions),
})


# --- benchmarks -----------------------------------------------------------
def median_of(fn, n):
    samples = []
    for _ in range(n):
        started = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - started)
    return statistics.median(samples)


def subprocess_median(code, n=5):
    samples = []
    for _ in range(n):
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True)
        lines = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
        if lines:
            try:
                samples.append(float(lines[-1]))
            except ValueError:
                pass
    return statistics.median(samples) if samples else None


package_import = subprocess_median(
    "import time;t=time.perf_counter();"
    "import rocketforge.providers.cea as p;print(time.perf_counter()-t)")
first_check = subprocess_median(
    "import rocketforge.providers.cea as p;import time;"
    "t=time.perf_counter();p.check_availability();print(time.perf_counter()-t)")

fresh = CEAThermochemistryProvider()
started = time.perf_counter()
fresh.solve_chamber(canonical)
first_solve = time.perf_counter() - started

warm = median_of(lambda: provider.solve_chamber(canonical), 200)
raw_only = median_of(lambda: mp.solve_chamber_raw(provider._cea(), chamber_input), 200)


def sweep(n):
    for value in np.linspace(2.5, 4.5, n):
        provider.solve_chamber(
            request(LIQUID_METHANE, 111.643, LOX, 90.17, float(value), 10.0e6))


sweep_100 = median_of(lambda: sweep(100), 3)
sweep_1000 = median_of(lambda: sweep(1000), 3)

write("cea_performance_benchmark.json", {
    "python": sys.version.split()[0],
    "cea_version": availability.version,
    "provider_package_import_s": package_import,
    "first_availability_check_s": first_check,
    "first_solve_cold_provider_s": first_solve,
    "warm_full_pipeline_s": warm,
    "warm_raw_cea_solve_only_s": raw_only,
    "rocketforge_overhead_s": warm - raw_only,
    "rocketforge_overhead_fraction": (warm - raw_only) / warm,
    "sweep_100_s": sweep_100,
    "sweep_100_per_point_ms": sweep_100 / 100.0 * 1e3,
    "sweep_1000_s": sweep_1000,
    "sweep_1000_per_point_ms": sweep_1000 / 1000.0 * 1e3,
    "note": ("warm_full_pipeline includes mapping, unit conversion, element "
             "conservation, the state identities and provenance; "
             "warm_raw_cea_solve_only is the library call alone, so the "
             "difference is RocketForge's validation cost."),
})

print("artifacts written to", OUT)
for path in sorted(OUT.glob("*")):
    print(f"  {path.name:38s} {path.stat().st_size:>9d} bytes")
