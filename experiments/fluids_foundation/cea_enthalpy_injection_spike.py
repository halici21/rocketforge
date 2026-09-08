"""SEGMENT E spike: can NASA CEA be given an explicit corrected reactant enthalpy?

Blocking question. Answered by measurement, never by reading the API surface.

Four things must be established before any coupling is written:

1. what ``Mixture.calc_property(ENTHALPY, weights, temperatures)`` actually
   returns -- its basis and its unit;
2. that perturbing the HP constraint moves the chamber (positive control);
3. that moving an assigned-enthalpy reactant's temperature does *not* move it
   (negative control, and the reason a correction is needed at all);
4. that a gaseous reactant *does* respond to temperature natively, so applying
   a correction there would double-count.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import cea  # noqa: E402

from rocketforge.providers.cea.units import enthalpy_argument  # noqa: E402

OUT = pathlib.Path("acceptance/fluids_foundation/cea_enthalpy_injection_spike.json")

PRODUCTS = ["CO2", "CO", "H2O", "OH", "H2", "O2", "H", "O", "CH4", "C(gr)"]


def solve(reactant_names, ox_w, fuel_w, of_ratio, temperatures, pressure_bar,
          enthalpy_delta_over_r=0.0):
    """One HP chamber solve, optionally with the constraint shifted."""
    reactants = cea.Mixture(list(reactant_names))
    products = cea.Mixture(PRODUCTS)
    solver = cea.EqSolver(products, reactants=reactants)
    solution = cea.EqSolution(solver)
    weights = reactants.of_ratio_to_weights(
        np.asarray(ox_w, dtype=float), np.asarray(fuel_w, dtype=float),
        float(of_ratio))
    mixture_enthalpy = reactants.calc_property(
        cea.ENTHALPY, weights, list(temperatures))
    constraint = enthalpy_argument(mixture_enthalpy, cea.R) + enthalpy_delta_over_r
    solver.solve(solution, cea.HP, constraint, float(pressure_bar), weights)
    return {
        "mixture_enthalpy_raw": float(mixture_enthalpy),
        "constraint_h_over_r": float(constraint),
        "converged": bool(solution.converged),
        "T": float(solution.T),
        "MW": float(solution.MW),
        "enthalpy_kj_per_kg": float(solution.enthalpy),
        "weights": [float(w) for w in weights],
    }


report: dict = {
    "purpose": "does NASA CEA consume an explicitly supplied reactant enthalpy?",
    "cea_version": cea.__version__ if hasattr(cea, "__version__") else "3.3.4",
    "cea_R": float(cea.R),
}

# --- 1. what does calc_property(ENTHALPY, ...) return? --------------------
# One pure reactant at unit weight: the returned number can then be compared
# against its own molar mass to decide mass- vs mole-basis.
for name in ("O2(L)", "CH4(L)", "O2", "CH4"):
    mix = cea.Mixture([name])
    w = np.array([1.0], dtype=float)
    r = cea.Reactant(name)
    try:
        lo, hi = r.get_valid_temperature_range()
    except Exception:  # noqa: BLE001
        lo, hi = float("nan"), float("nan")
    t_mid = 0.5 * (lo + hi) if lo == lo else 298.15
    h_mid = float(mix.calc_property(cea.ENTHALPY, w, [t_mid]))
    h_lo = float(mix.calc_property(cea.ENTHALPY, w, [lo + 0.25 * (hi - lo)]))
    h_hi = float(mix.calc_property(cea.ENTHALPY, w, [lo + 0.75 * (hi - lo)]))
    report.setdefault("reactant_probe", {})[name] = {
        "valid_range_K": [lo, hi],
        "h_at_mid": h_mid,
        "h_at_25pct": h_lo,
        "h_at_75pct": h_hi,
        "temperature_sensitive": h_lo != h_hi,
        "molar_mass_kg_per_kmol": float(r.MW) if hasattr(r, "MW") else None,
    }

# --- 2. positive control: shift the constraint ---------------------------
LOX_CH4 = dict(reactant_names=["O2(L)", "CH4(L)"], ox_w=[1.0, 0.0],
               fuel_w=[0.0, 1.0], of_ratio=3.4,
               temperatures=[90.17, 111.643], pressure_bar=100.0)

base = solve(**LOX_CH4)
report["baseline"] = base

shifts = {}
for delta in (-50.0, -5.0, 5.0, 50.0):
    shifts[str(delta)] = solve(**LOX_CH4, enthalpy_delta_over_r=delta)
report["constraint_shift"] = shifts
report["constraint_shift_moves_chamber"] = all(
    abs(v["T"] - base["T"]) > 1e-9 for v in shifts.values())

# --- 3. negative control: move an assigned-enthalpy reactant's T ----------
warm = dict(LOX_CH4)
warm["temperatures"] = [95.0, 111.643]
warm_result = solve(**warm)
report["assigned_liquid_temperature_change"] = {
    "from_K": 90.17, "to_K": 95.0,
    "T_before": base["T"], "T_after": warm_result["T"],
    "mixture_enthalpy_before": base["mixture_enthalpy_raw"],
    "mixture_enthalpy_after": warm_result["mixture_enthalpy_raw"],
    "chamber_moved": warm_result["T"] != base["T"],
}

# --- 4. gaseous reactants must respond natively ---------------------------
GOX_GCH4 = dict(reactant_names=["O2", "CH4"], ox_w=[1.0, 0.0],
                fuel_w=[0.0, 1.0], of_ratio=3.4,
                temperatures=[298.15, 298.15], pressure_bar=100.0)
gas_base = solve(**GOX_GCH4)
gas_warm = dict(GOX_GCH4)
gas_warm["temperatures"] = [320.0, 298.15]
gas_warm_result = solve(**gas_warm)
report["gas_temperature_change"] = {
    "from_K": 298.15, "to_K": 320.0,
    "T_before": gas_base["T"], "T_after": gas_warm_result["T"],
    "mixture_enthalpy_before": gas_base["mixture_enthalpy_raw"],
    "mixture_enthalpy_after": gas_warm_result["mixture_enthalpy_raw"],
    "chamber_moved": gas_warm_result["T"] != gas_base["T"],
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2)[:4000])
