"""Phase 5B-0 - the fair common case (Tier A).

One problem both providers can represent WITHOUT inventing liquid-property
support, solved with a MATCHED species set so the comparison is about the
solvers and their thermodynamic data, not about who was allowed more species.

    CH4 + O2, GASEOUS reactants at 298.15 K
    O/F = 3.4 by mass
    P   = 10 MPa (100 bar)
    HP equilibrium
    species: CO CO2 H H2 H2O O O2 OH CH4     (9, gas only, no condensed)

Emits one JSON per provider; merge_common_case.py builds the comparison CSV.
"""
import json
import sys

import numpy as np

SPECIES = ["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH", "CH4"]
OF = 3.4
T_REAC = 298.15
P_PA = 10.0e6
P_BAR = 100.0
Ru_2019 = 8.31446261815324

res = {"case": {"reactants": "CH4 + O2 (gas)", "of_mass": OF,
                "T_reac_K": T_REAC, "P_Pa": P_PA,
                "species": SPECIES, "problem": "HP equilibrium"}}

try:
    import cea
    res["provider"] = "NASA CEA"
    res["version"] = cea.__version__
    res["gas_constant_used_by_provider"] = cea.R
    reac = cea.Mixture(["CH4", "O2"])
    prod = cea.Mixture(SPECIES)
    solver = cea.EqSolver(prod, reactants=reac)
    soln = cea.EqSolution(solver)
    w = reac.of_ratio_to_weights(np.array([0.0, 100.0]),
                                 np.array([100.0, 0.0]), OF)
    h0 = reac.calc_property(cea.ENTHALPY, w, T_REAC) / cea.R
    solver.solve(soln, cea.HP, h0, P_BAR, w)
    res.update({
        "converged": bool(soln.converged),
        "Tc_K": soln.T,
        "P_Pa": soln.P * 1e5,
        "M_kg_per_kmol": soln.M,
        "density_kg_per_m3": soln.density,
        "gamma_s_equilibrium": soln.gamma_s,
        "cp_frozen_J_per_kgK": soln.cp_fr * 1e3,
        "cp_equilibrium_J_per_kgK": soln.cp_eq * 1e3,
        "cv_frozen_J_per_kgK": soln.cv_fr * 1e3,
        "gamma_frozen_cp_over_cv": soln.cp_fr / soln.cv_fr,
        "entropy_J_per_kgK": soln.entropy * 1e3,
        "enthalpy_J_per_kg": soln.enthalpy * 1e3,
        "X": dict(soln.mole_fractions),
        "Y": dict(soln.mass_fractions),
        "sum_X": sum(soln.mole_fractions.values()),
        "native_units": {"P": "bar", "cp": "kJ/(kg K)", "M": "kg/kmol",
                         "density": "kg/m3", "h": "kJ/kg", "s": "kJ/(kg K)"},
    })
except ImportError:
    import cantera as ct
    res["provider"] = "Cantera"
    res["version"] = ct.__version__
    res["gas_constant_used_by_provider"] = ct.gas_constant
    allsp = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
    gas = ct.Solution(thermo="ideal-gas",
                      species=[allsp[n] for n in SPECIES if n in allsp])
    gas.TPY = T_REAC, P_PA, f"CH4:{1/(1+OF)}, O2:{OF/(1+OF)}"
    gas.equilibrate("HP")
    s0 = gas.entropy_mass
    # equilibrium isentropic exponent by central finite difference on an SP path
    lo, hi = P_PA * 0.999, P_PA * 1.001
    g2 = ct.Solution(thermo="ideal-gas",
                     species=[allsp[n] for n in SPECIES if n in allsp])
    g2.TPX = gas.T, gas.P, gas.X
    g2.SP = s0, lo
    g2.equilibrate("SP")
    rlo = g2.density
    g2.SP = s0, hi
    g2.equilibrate("SP")
    rhi = g2.density
    gamma_s = float((np.log(hi) - np.log(lo)) / (np.log(rhi) - np.log(rlo)))
    res.update({
        "converged": True,
        "Tc_K": gas.T,
        "P_Pa": gas.P,
        "M_kg_per_kmol": gas.mean_molecular_weight,
        "density_kg_per_m3": gas.density,
        "gamma_s_equilibrium": gamma_s,
        "cp_frozen_J_per_kgK": gas.cp_mass,
        "cp_equilibrium_J_per_kgK": None,
        "cv_frozen_J_per_kgK": gas.cv_mass,
        "gamma_frozen_cp_over_cv": gas.cp_mass / gas.cv_mass,
        "entropy_J_per_kgK": gas.entropy_mass,
        "enthalpy_J_per_kg": gas.enthalpy_mass,
        "X": {n: float(x) for n, x in zip(gas.species_names, gas.X)},
        "Y": {n: float(y) for n, y in zip(gas.species_names, gas.Y)},
        "sum_X": float(np.sum(gas.X)),
        "native_units": {"P": "Pa", "cp": "J/(kg K)", "M": "kg/kmol",
                         "density": "kg/m3", "h": "J/kg", "s": "J/(kg K)"},
        "gamma_s_note": "NOT native - computed by finite difference on an SP path",
        "cp_equilibrium_note": "NOT native - Cantera exposes only frozen cp",
    })

res["R_specific_J_per_kgK"] = Ru_2019 * 1000.0 / res["M_kg_per_kmol"]

out = sys.argv[1]
with open(out, "w") as fh:
    json.dump(res, fh, indent=2, default=str)
print(f"{res['provider']} {res['version']}: Tc={res['Tc_K']:.4f} K  "
      f"M={res['M_kg_per_kmol']:.6f}  gamma_s={res['gamma_s_equilibrium']:.6f}")
print("written:", out)
