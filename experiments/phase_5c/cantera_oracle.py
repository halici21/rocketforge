"""Phase 5C Level-C oracle: Cantera on the matched common case.

Experimental, not production. Run in a Cantera environment -- deliberately NOT
``.venv-cea``, because the official executable is built from that environment
and Cantera must not be bundled:

    %TEMP%\\rocketforge_phase5b0_cantera\\Scripts\\python.exe \\
        experiments/phase_5c/cantera_oracle.py

Reads the CEA side from ``acceptance/phase_5c/cea_provider_common_case.json``
and writes the comparison beside it. Nothing in RocketForge is imported: this
script needs only Cantera and the recorded JSON, which is what keeps the two
providers genuinely independent.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import cantera as ct
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "acceptance" / "phase_5c"
CEA_FILE = ARTIFACTS / "cea_provider_common_case.json"

if not CEA_FILE.exists():
    sys.exit(f"run make_artifacts.py first; {CEA_FILE} is missing")

cea_case = json.loads(CEA_FILE.read_text(encoding="utf-8"))
case = cea_case["case"]
of = float(case["of_mass"])
t_reac = float(case["T_reac_K"])
pressure = float(case["P_Pa"])

# Match the species set exactly. Cantera's NASA data and CEA's thermo.lib are
# independent transcriptions of the same lineage, so matching the species is
# the most that can be matched; the thermodynamic data still differs.
wanted = [s for s in case["species"] if not s.endswith(")")]
available = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
species = [available[n] for n in wanted if n in available]
missing = [n for n in wanted if n not in available]

gas = ct.Solution(thermo="ideal-gas", species=species)
y_fuel = 1.0 / (1.0 + of)
y_ox = of / (1.0 + of)
gas.TPY = t_reac, pressure, f"CH4:{y_fuel}, O2:{y_ox}"
gas.equilibrate("HP")

entropy = gas.entropy_mass
molar_mass = gas.mean_molecular_weight / 1000.0        # kg/kmol -> kg/mol

# Cantera exposes no equilibrium isentropic exponent; compute it the way
# Phase 5B-0 did, by finite difference along an isentrope.
low, high = pressure * 0.999, pressure * 1.001
probe = ct.Solution(thermo="ideal-gas", species=species)
probe.TPX = gas.T, gas.P, gas.X
probe.SP = entropy, low
probe.equilibrate("SP")
rho_low = probe.density
probe.SP = entropy, high
probe.equilibrate("SP")
rho_high = probe.density
gamma_s = float((math.log(high) - math.log(low))
                / (math.log(rho_high) - math.log(rho_low)))

cantera_result = {
    "provider": "Cantera",
    "version": ct.__version__,
    "mechanism": "nasa_gas.yaml",
    "species_requested": wanted,
    "species_missing": missing,
    "gas_constant_used_by_provider": ct.gas_constant,
    "Tc_K": gas.T,
    "M_kg_per_mol": molar_mass,
    "R_J_per_kgK": ct.gas_constant / gas.mean_molecular_weight,
    "density": gas.density,
    "gamma_s": gamma_s,
    "gamma_frozen": gas.cp_mass / gas.cv_mass,
    "cp_frozen": gas.cp_mass,
    "cv_frozen": gas.cv_mass,
    "X": {n: float(x) for n, x in zip(gas.species_names, gas.X)},
}

(ARTIFACTS / "cantera_oracle_common_case.json").write_text(
    json.dumps(cantera_result, indent=2), encoding="utf-8")


def relative(a: float, b: float) -> float:
    scale = max(abs(a), abs(b))
    return 0.0 if scale == 0.0 else abs(a - b) / scale


bulk = {}
for key in ("Tc_K", "M_kg_per_mol", "R_J_per_kgK", "density", "gamma_s",
            "gamma_frozen", "cp_frozen", "cv_frozen"):
    bulk[key] = {
        "cea": cea_case[key],
        "cantera": cantera_result[key],
        "relative_difference": relative(cea_case[key], cantera_result[key]),
    }

species_rows = {}
for name in sorted(set(cea_case["X"]) | set(cantera_result["X"])):
    a = cea_case["X"].get(name, 0.0)
    b = cantera_result["X"].get(name, 0.0)
    if max(a, b) < 1.0e-6:
        continue
    species_rows[name] = {"cea": a, "cantera": b,
                          "relative_difference": relative(a, b)}

comparison = {
    "parity_tier": 2,
    "parity_tier_note": (
        "Tier 2. The two providers use INDEPENDENT thermodynamic databases -- "
        "NASA CEA's thermo.lib and Cantera's nasa_gas.yaml -- so exact "
        "agreement is neither expected nor required. Neither is treated as "
        "ground truth. Agreement on bulk properties with larger differences in "
        "trace radicals is the expected signature of independent data, not a "
        "defect in either provider."),
    "case": case,
    "cea_version": cea_case["cea_version"],
    "cea_thermo_sha256": cea_case.get("thermo_sha256", ""),
    "cantera_version": cantera_result["version"],
    "cantera_mechanism": cantera_result["mechanism"],
    "species_missing_from_cantera": missing,
    "bulk_properties": bulk,
    "major_species": species_rows,
    "max_bulk_relative_difference": max(v["relative_difference"]
                                        for v in bulk.values()),
    "max_species_relative_difference": (
        max(v["relative_difference"] for v in species_rows.values())
        if species_rows else 0.0),
}
(ARTIFACTS / "cantera_oracle_comparison.json").write_text(
    json.dumps(comparison, indent=2), encoding="utf-8")

print(f"Cantera {ct.__version__} vs NASA CEA {cea_case['cea_version']}, "
      f"matched species set, Tier 2")
print(f"  species requested {len(wanted)}, missing from Cantera: {missing or 'none'}")
print()
print(f"{'quantity':18s} {'CEA':>16s} {'Cantera':>16s} {'rel diff':>10s}")
for key, row in bulk.items():
    print(f"{key:18s} {row['cea']:16.8g} {row['cantera']:16.8g} "
          f"{row['relative_difference']:10.2e}")
print()
print(f"{'species':10s} {'CEA':>14s} {'Cantera':>14s} {'rel diff':>10s}")
for name, row in sorted(species_rows.items(),
                        key=lambda kv: -kv[1]["cea"]):
    print(f"{name:10s} {row['cea']:14.6e} {row['cantera']:14.6e} "
          f"{row['relative_difference']:10.2e}")
print()
print(f"max bulk difference    {comparison['max_bulk_relative_difference']:.3e}")
print(f"max species difference {comparison['max_species_relative_difference']:.3e}")
