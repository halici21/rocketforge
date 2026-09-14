"""CEA <-> Cantera cross-provider matrix -- gaseous reactants only.

Diagnostic, not production. Section 31 of the verification campaign is
explicit: liquid-reactant reference-state complications must not be the first
CEA-vs-Cantera test. Every state here is gaseous CH4/O2 or gaseous H2/O2 at a
controlled initial temperature, matching the pattern already established and
accepted in Phase 5C's single CH4/O2 common case
(``experiments/phase_5c/cantera_oracle.py``) -- this script generalises that
pattern to a real matrix rather than one point.

Two passes, because the two providers cannot share a Python environment
(Cantera is deliberately not installed alongside CEA -- see
``experiments/phase_5c/cantera_oracle.py``'s own docstring):

    .venv-cea\\Scripts\\python.exe  experiments/cea_cantera_verification/cross_provider_matrix.py cea
    <a Cantera-only venv>\\Scripts\\python.exe experiments/cea_cantera_verification/cross_provider_matrix.py cantera
    .venv\\Scripts\\python.exe      experiments/cea_cantera_verification/cross_provider_matrix.py compare

The `cea` pass writes ``acceptance/cea_cantera_verification/matrix_cea.json``;
the `cantera` pass reads the case list from that file and writes
``matrix_cantera.json``; `compare` reads both and writes
``cross_provider_matrix.json``, with no RocketForge or Cantera import needed
for the comparison itself.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "acceptance" / "cea_cantera_verification"
OUT.mkdir(parents=True, exist_ok=True)

#: (fuel, of_mass, pressure_Pa) x 2 fuels x 3 mixture points x 2 pressures = 12
CASES = []
for pressure in (5.0e6, 10.0e6):
    for of in (2.5, 3.4, 4.5):          # rich, near-peak, lean -- CH4/O2
        CASES.append({"fuel": "CH4", "of_mass": of, "pressure_Pa": pressure})
    for of in (4.0, 7.94, 12.0):        # rich, ~stoichiometric, lean -- H2/O2
        CASES.append({"fuel": "H2", "of_mass": of, "pressure_Pa": pressure})

T_REAC = 298.15  # K, gaseous reactants, standard reference temperature


def run_cea() -> None:
    sys.path.insert(0, str(ROOT))
    from rocketforge.physics.thermochemistry import (
        ChamberEquilibriumRequest, MixtureRatio, Phase, PropellantStream,
    )
    from rocketforge.providers.cea import (
        GASEOUS_METHANE, GASEOUS_OXYGEN, CEAThermochemistryProvider,
        check_availability,
    )
    from rocketforge.physics.thermochemistry.propellants import PropellantDefinition
    from rocketforge.physics.thermochemistry.composition import Composition
    from rocketforge.physics.thermochemistry.types import PropellantRole
    from rocketforge.providers.cea.species import CHO_PRODUCT_SPECIES, HO_PRODUCT_SPECIES

    # No production GASEOUS_HYDROGEN exists (RocketForge's production
    # propellant set only defines liquid H2 -- see propellants.py). Built here,
    # locally, for this diagnostic only: it is never imported by production
    # code and is not registered in PRODUCTION_PROPELLANTS.
    GASEOUS_HYDROGEN = PropellantDefinition(
        name="GH2", role=PropellantRole.FUEL,
        composition=Composition.pure("H2"),
        reference_temperature=298.15, reference_phase=Phase.GAS,
        provider_names={"cea": "H2"},
        source="cross_provider_matrix.py diagnostic only, not production",
    )

    provider = CEAThermochemistryProvider()
    availability = check_availability()
    if not availability.is_usable:
        sys.exit(f"CEA unavailable: {availability.status.value} "
                 f"{availability.detail}")

    results = []
    for case in CASES:
        fuel_def = GASEOUS_METHANE if case["fuel"] == "CH4" else GASEOUS_HYDROGEN
        species = (CHO_PRODUCT_SPECIES if case["fuel"] == "CH4"
                  else HO_PRODUCT_SPECIES)
        request = ChamberEquilibriumRequest(
            fuel=PropellantStream(fuel_def, T_REAC, phase=Phase.GAS),
            oxidiser=PropellantStream(GASEOUS_OXYGEN, T_REAC, phase=Phase.GAS),
            oxidiser_fuel_ratio=MixtureRatio(case["of_mass"]),
            chamber_pressure=case["pressure_Pa"])
        state = provider.solve_chamber(request).unwrap()
        results.append({
            **case,
            "species_requested": list(species),
            "Tc_K": state.temperature,
            "M_kg_per_mol": state.molar_mass,
            "R_J_per_kgK": state.gas_constant,
            "gamma_s": state.gamma,
            "gamma_frozen": state.gamma_frozen,
            "cp_frozen": state.cp,
            "cv_frozen": state.cv,
            "X": dict(state.composition.fractions),
        })

    (OUT / "matrix_cea.json").write_text(json.dumps({
        "provider": "RocketForge CEAThermochemistryProvider",
        "cea_version": availability.version,
        "reactant_temperature_K": T_REAC,
        "cases": results,
    }, indent=2), encoding="utf-8")
    print(f"CEA: {len(results)} cases written to matrix_cea.json")


def run_cantera() -> None:
    import cantera as ct

    cea_data = json.loads((OUT / "matrix_cea.json").read_text(encoding="utf-8"))
    available = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}

    results = []
    for row in cea_data["cases"]:
        wanted = [s for s in row["species_requested"] if not s.endswith(")")]
        species = [available[n] for n in wanted if n in available]
        missing = [n for n in wanted if n not in available]

        gas = ct.Solution(thermo="ideal-gas", species=species)
        of = row["of_mass"]
        y_fuel = 1.0 / (1.0 + of)
        y_ox = of / (1.0 + of)
        t_reac = cea_data["reactant_temperature_K"]
        gas.TPY = t_reac, row["pressure_Pa"], f"{row['fuel']}:{y_fuel}, O2:{y_ox}"
        gas.equilibrate("HP")

        entropy = gas.entropy_mass
        molar_mass = gas.mean_molecular_weight / 1000.0
        low, high = row["pressure_Pa"] * 0.999, row["pressure_Pa"] * 1.001
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

        results.append({
            "fuel": row["fuel"], "of_mass": of, "pressure_Pa": row["pressure_Pa"],
            "species_missing": missing,
            "Tc_K": gas.T,
            "M_kg_per_mol": molar_mass,
            "R_J_per_kgK": ct.gas_constant / gas.mean_molecular_weight,
            "gamma_s": gamma_s,
            "gamma_frozen": gas.cp_mass / gas.cv_mass,
            "cp_frozen": gas.cp_mass,
            "cv_frozen": gas.cv_mass,
            "X": {n: float(x) for n, x in zip(gas.species_names, gas.X)},
        })

    (OUT / "matrix_cantera.json").write_text(json.dumps({
        "provider": "Cantera", "version": ct.__version__,
        "mechanism": "nasa_gas.yaml", "cases": results,
    }, indent=2), encoding="utf-8")
    print(f"Cantera: {len(results)} cases written to matrix_cantera.json")


def relative(a: float, b: float) -> float:
    scale = max(abs(a), abs(b))
    return 0.0 if scale == 0.0 else abs(a - b) / scale


def run_compare() -> None:
    cea = json.loads((OUT / "matrix_cea.json").read_text(encoding="utf-8"))
    cantera = json.loads((OUT / "matrix_cantera.json").read_text(encoding="utf-8"))

    rows = []
    for a, b in zip(cea["cases"], cantera["cases"]):
        assert a["fuel"] == b["fuel"] and a["of_mass"] == b["of_mass"] \
            and a["pressure_Pa"] == b["pressure_Pa"], "case order mismatch"
        bulk = {k: {"cea": a[k], "cantera": b[k],
                    "relative_difference": relative(a[k], b[k])}
                for k in ("Tc_K", "M_kg_per_mol", "gamma_s", "gamma_frozen",
                          "cp_frozen", "cv_frozen")}
        species_rows = {}
        for name in sorted(set(a["X"]) | set(b["X"])):
            xa, xb = a["X"].get(name, 0.0), b["X"].get(name, 0.0)
            if max(xa, xb) < 1.0e-6:
                continue
            species_rows[name] = {"cea": xa, "cantera": xb,
                                  "relative_difference": relative(xa, xb)}
        rows.append({
            "fuel": a["fuel"], "of_mass": a["of_mass"],
            "pressure_Pa": a["pressure_Pa"],
            "bulk_properties": bulk,
            "max_bulk_relative_difference": max(v["relative_difference"]
                                                for v in bulk.values()),
            "species": species_rows,
            "max_species_relative_difference": (
                max(v["relative_difference"] for v in species_rows.values())
                if species_rows else 0.0),
        })

    result = {
        "parity_tier": 2,
        "parity_tier_note": (
            "Tier 2, as established in Phase 5C. Independent thermodynamic "
            "databases (CEA thermo.lib vs Cantera nasa_gas.yaml); exact "
            "agreement is neither expected nor required; neither is ground "
            "truth. This is a generalisation of the accepted single CH4/O2 "
            "point to a 12-state matrix across two fuels, three mixture "
            "points each, and two pressures -- all gaseous reactants, per the "
            "campaign's explicit instruction to start cross-provider "
            "comparison with gaseous reactants before any liquid case."),
        "cea_version": cea["cea_version"], "cantera_version": cantera["version"],
        "cases": rows,
        "worst_bulk_relative_difference": max(r["max_bulk_relative_difference"]
                                              for r in rows),
        "worst_species_relative_difference": max(
            r["max_species_relative_difference"] for r in rows),
        "worst_bulk_case": max(rows, key=lambda r: r["max_bulk_relative_difference"]),
    }
    (OUT / "cross_provider_matrix.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")

    print(f"{len(rows)} states compared")
    print(f"{'fuel':4s} {'O/F':>6s} {'P[MPa]':>7s} {'Tc rel':>10s} "
          f"{'M rel':>10s} {'max species rel':>16s}")
    for r in rows:
        print(f"{r['fuel']:4s} {r['of_mass']:6.2f} "
              f"{r['pressure_Pa']/1e6:7.1f} "
              f"{r['bulk_properties']['Tc_K']['relative_difference']:10.2e} "
              f"{r['bulk_properties']['M_kg_per_mol']['relative_difference']:10.2e} "
              f"{r['max_species_relative_difference']:16.2e}")
    print()
    print(f"worst bulk difference:    {result['worst_bulk_relative_difference']:.2e}")
    print(f"worst species difference: {result['worst_species_relative_difference']:.2e}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "cea":
        run_cea()
    elif mode == "cantera":
        run_cantera()
    elif mode == "compare":
        run_compare()
    else:
        sys.exit("usage: cross_provider_matrix.py cea|cantera|compare")
