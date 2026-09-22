"""Solve NASA RP-1311 Example 5 with CEA directly, and record it in full.

The middle term of the three-way validation. The official sample prints values
rounded to the published table's width; this records what CEA actually returned,
at full precision, so the RocketForge provider can be compared against CEA
rather than against a rounded printout.

Nothing in RocketForge is imported for the solve itself -- that is the point.
The only RocketForge import is the phase classifier, used to report how the
product set divides into gas and condensed, and it is applied *after* the solve.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

import cea

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from rocketforge.providers.cea.species import (  # noqa: E402
    CEA_FORMULAS,
    phase_of_cea_name,
)
from rocketforge.providers.cea_solid import (  # noqa: E402
    RP1311_EXAMPLE5,
    RP1311_EXAMPLE5_OMIT,
    RP1311_EXAMPLE5_PRESSURES_BAR,
)

PRESSURE_BAR = RP1311_EXAMPLE5_PRESSURES_BAR[0]


def build_reactants() -> list[object]:
    """The reactant list, with the custom binder materialised per call."""
    out: list[object] = []
    for item in RP1311_EXAMPLE5.ingredients:
        if item.custom is None:
            out.append(item.name)
        else:
            out.append(cea.Reactant(
                name=item.name,
                formula=dict(item.custom.formula),
                molecular_weight=item.custom.molecular_weight,
                enthalpy=item.custom.heat_of_formation,
                enthalpy_units=item.custom.heat_of_formation_units,
                temperature=item.custom.reference_temperature,
            ))
    return out


def solve() -> dict:
    reactants = build_reactants()
    weights = np.asarray(RP1311_EXAMPLE5.mass_fractions, dtype=np.float64)
    temps = np.asarray([RP1311_EXAMPLE5.initial_temperature] * len(weights),
                       dtype=np.float64)

    reac = cea.Mixture(reactants)
    prod = cea.Mixture(reactants, products_from_reactants=True,
                       omit=list(RP1311_EXAMPLE5_OMIT))
    solver = cea.EqSolver(prod, reactants=reac)
    solution = cea.EqSolution(solver)

    h0 = reac.calc_property(cea.ENTHALPY, weights, temps)
    solver.solve(solution, cea.HP, h0 / cea.R, PRESSURE_BAR, weights)

    mole = {str(k): float(v) for k, v in solution.mole_fractions.items()}
    mass = {str(k): float(v) for k, v in solution.mass_fractions.items()}
    return {
        "pressure_bar": PRESSURE_BAR,
        "converged": bool(solution.converged),
        "temperature_k": float(solution.T),
        "pressure_out_bar": float(solution.P),
        "density": float(solution.density),
        "molar_mass_MW": float(solution.MW),
        "molar_mass_M": float(solution.M),
        "enthalpy_kj_per_kg": float(solution.enthalpy),
        "entropy_kj_per_kg_k": float(solution.entropy),
        "gamma_s": float(solution.gamma_s),
        "cp_fr": float(solution.cp_fr),
        "cv_fr": float(solution.cv_fr),
        "cp_eq": float(solution.cp_eq),
        "cv_eq": float(solution.cv_eq),
        "num_condensed_candidates": int(solver.num_condensed),
        "num_gas": int(solver.num_gas),
        "num_products": int(solver.num_products),
        "num_elements": int(solver.num_elements),
        "cea_R": float(cea.R),
        "h0_over_R": float(h0 / cea.R),
        "mole_fractions": mole,
        "mass_fractions": mass,
    }


def classify(names: list[str]) -> dict:
    """Split the product set by phase, and report curated-formula coverage."""
    gas, condensed, unclassified = [], [], []
    for name in names:
        try:
            phase = phase_of_cea_name(name)
        except Exception as exc:  # noqa: BLE001
            unclassified.append({"name": name, "error": str(exc)})
            continue
        (condensed if phase.is_condensed else gas).append(name)
    return {
        "gas": sorted(gas),
        "condensed": sorted(condensed),
        "unclassified": unclassified,
        "with_curated_formula": sorted(n for n in names if n in CEA_FORMULAS),
        "without_curated_formula": sorted(n for n in names if n not in CEA_FORMULAS),
    }


def main() -> None:
    result = solve()
    names = sorted(result["mass_fractions"])
    result["phase_report"] = classify(names)

    out = pathlib.Path(__file__).with_name("example5_direct.json")
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")

    pr = result["phase_report"]
    print(f"converged      : {result['converged']}")
    print(f"T              : {result['temperature_k']!r} K")
    print(f"MW             : {result['molar_mass_MW']!r}")
    print(f"gamma_s        : {result['gamma_s']!r}")
    print(f"products       : {len(names)}"
          f"  (gas {len(pr['gas'])}, condensed {len(pr['condensed'])},"
          f" unclassified {len(pr['unclassified'])})")
    print(f"condensed      : {pr['condensed']}")
    for name in pr["condensed"]:
        print(f"   {name:12s} mass {result['mass_fractions'][name]!r}")
    print(f"curated formula: {len(pr['with_curated_formula'])} of {len(names)}")
    if pr["unclassified"]:
        print("UNCLASSIFIED   :")
        for item in pr["unclassified"]:
            print(f"   {item['name']}: {item['error']}")
    print(f"\nwritten -> {out}")


if __name__ == "__main__":
    main()
