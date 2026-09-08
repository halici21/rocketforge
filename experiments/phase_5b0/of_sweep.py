"""Phase 5B-0 - LOX/CH4 O/F sweep, trade-study data path proof.

Experimental. NOT production code. Runs under whichever isolated provider
environment invokes it; the provider is detected, never guessed.

    <env>\\Scripts\\python.exe of_sweep.py <out.csv>

Case (one transparent representative condition, NOT claimed as an optimum):
    LOX / CH4
    Pc     = 100 bar = 10 MPa
    O/F    = 2.5 .. 4.5 step 0.05   (41 points)
    supar  = 40   (CEA rocket mode only)
    reactants at their normal boiling points:
        O2(L)  90.170 K
        CH4(L) 111.643 K
    Cantera cannot represent liquid reactants (no O2(L)/CH4(L) in its
    databases), so its sweep uses GASEOUS reactants at 298.15 K and is
    therefore a DIFFERENT physical case. It is recorded as such and must not
    be compared to the CEA liquid case as if it were the same problem.
"""
import csv
import sys
import time

import numpy as np

OF_MIN, OF_MAX, OF_STEP = 2.5, 4.5, 0.05
PC_BAR = 100.0
PC_PA = 100.0e5
SUPAR = 40.0
T_O2L, T_CH4L = 90.170, 111.643
T_GAS = 298.15

PRODUCTS = ["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH", "HO2", "H2O2",
            "CH4", "C(gr)"]
PRODUCTS_GAS = [s for s in PRODUCTS if s != "C(gr)"]

of_values = np.round(np.arange(OF_MIN, OF_MAX + 1e-9, OF_STEP), 10)


def run_cea():
    import cea
    rows = []
    reac = cea.Mixture(["CH4(L)", "O2(L)"])
    prod = cea.Mixture(PRODUCTS)
    solver = cea.RocketSolver(prod, reactants=reac)
    fuel_w = np.array([100.0, 0.0])
    oxid_w = np.array([0.0, 100.0])
    t0 = time.perf_counter()
    for of in of_values:
        w = reac.of_ratio_to_weights(oxid_w, fuel_w, float(of))
        hc = reac.calc_property(cea.ENTHALPY, w, [T_CH4L, T_O2L]) / cea.R
        row = {"of": float(of), "provider": "cea", "pc_bar": PC_BAR,
               "supar": SUPAR, "reactant_phase": "liquid",
               "T_fuel_K": T_CH4L, "T_ox_K": T_O2L}
        try:
            s = cea.RocketSolution(solver)
            solver.solve(s, w, PC_BAR, supar=SUPAR, hc=hc)
            X = {k: float(v[0]) for k, v in s.mole_fractions.items()}
            Yc = {k: float(v[0]) for k, v in s.mass_fractions.items()}
            row.update({
                "converged": bool(s.converged),
                "Tc_K": float(s.T[0]),
                "T_throat_K": float(s.T[1]),
                "T_exit_K": float(s.T[2]),
                "M_kg_per_kmol": float(s.M[0]),
                "R_J_per_kgK": 8314.51 / float(s.M[0]),
                "gamma_s": float(s.gamma_s[0]),
                "cp_eq_kJ_per_kgK": float(s.cp_eq[0]),
                "cp_fr_kJ_per_kgK": float(s.cp_fr[0]),
                "cstar_m_per_s": float(s.c_star[0]),
                "cf_exit": float(s.coefficient_of_thrust[-1]),
                "Isp_eq_m_per_s": float(s.Isp[-1]),
                "Isp_vac_eq_m_per_s": float(s.Isp_vacuum[-1]),
                "mach_exit": float(s.Mach[-1]),
                "X_H2O": X.get("H2O", 0.0), "X_CO": X.get("CO", 0.0),
                "X_CO2": X.get("CO2", 0.0), "X_H2": X.get("H2", 0.0),
                "X_OH": X.get("OH", 0.0), "X_O2": X.get("O2", 0.0),
                "X_H": X.get("H", 0.0), "X_O": X.get("O", 0.0),
                "Y_condensed": sum(v for k, v in Yc.items()
                                   if "(" in k and k != "C(gr)" or k == "C(gr)"),
                "sum_X": sum(X.values()),
            })
            # frozen at throat
            s2 = cea.RocketSolution(solver)
            solver.solve(s2, w, PC_BAR, supar=SUPAR, hc=hc, n_frz=2)
            row["Isp_frozen_throat_m_per_s"] = float(s2.Isp[-1])
            row["T_exit_frozen_throat_K"] = float(s2.T[-1])
            # frozen at chamber
            s3 = cea.RocketSolution(solver)
            solver.solve(s3, w, PC_BAR, supar=SUPAR, hc=hc, n_frz=1)
            row["Isp_frozen_chamber_m_per_s"] = float(s3.Isp[-1])
            row["T_exit_frozen_chamber_K"] = float(s3.T[-1])
            row["dIsp_eq_minus_frozen_throat"] = (
                row["Isp_eq_m_per_s"] - row["Isp_frozen_throat_m_per_s"])
            row["dIsp_rel"] = (row["dIsp_eq_minus_frozen_throat"]
                               / row["Isp_eq_m_per_s"])
        except Exception as exc:
            row["converged"] = False
            row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    print(f"  cea sweep: {len(rows)} points in {time.perf_counter()-t0:.2f} s")
    return rows


def run_cantera():
    import cantera as ct
    allsp = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
    chosen = [allsp[n] for n in PRODUCTS_GAS if n in allsp]
    rows = []
    t0 = time.perf_counter()
    for of in of_values:
        gas = ct.Solution(thermo="ideal-gas", species=chosen)
        row = {"of": float(of), "provider": "cantera", "pc_bar": PC_BAR,
               "supar": "", "reactant_phase": "gas",
               "T_fuel_K": T_GAS, "T_ox_K": T_GAS}
        try:
            yf = 1.0 / (1.0 + float(of))
            yo = float(of) / (1.0 + float(of))
            gas.TPY = T_GAS, PC_PA, f"CH4:{yf}, O2:{yo}"
            gas.equilibrate("HP")
            h0, s0 = gas.enthalpy_mass, gas.entropy_mass
            X = {n: float(x) for n, x in zip(gas.species_names, gas.X)}
            Mbar = gas.mean_molecular_weight
            # equilibrium isentropic exponent by finite difference on an SP path
            lo, hi = PC_PA * 0.999, PC_PA * 1.001
            g2 = ct.Solution(thermo="ideal-gas", species=chosen)
            g2.TPX = gas.T, gas.P, gas.X
            g2.SP = s0, lo
            g2.equilibrate("SP")
            rlo = g2.density
            g2.SP = s0, hi
            g2.equilibrate("SP")
            rhi = g2.density
            gamma_s = float((np.log(hi) - np.log(lo))
                            / (np.log(rhi) - np.log(rlo)))
            # equilibrium expansion to the CEA exit pressure is not known here,
            # so expand to a fixed pressure ratio of 100 for a comparable trend
            g3 = ct.Solution(thermo="ideal-gas", species=chosen)
            g3.TPX = gas.T, gas.P, gas.X
            g3.SP = s0, PC_PA / 100.0
            g3.equilibrate("SP")
            v_eq = float(np.sqrt(max(2.0 * (h0 - g3.enthalpy_mass), 0.0)))
            g4 = ct.Solution(thermo="ideal-gas", species=chosen)
            g4.TPX = gas.T, gas.P, gas.X
            g4.SPX = s0, PC_PA / 100.0, gas.X
            v_fr = float(np.sqrt(max(2.0 * (h0 - g4.enthalpy_mass), 0.0)))
            row.update({
                "converged": True,
                "Tc_K": gas.T, "T_throat_K": "", "T_exit_K": g3.T,
                "M_kg_per_kmol": Mbar,
                "R_J_per_kgK": ct.gas_constant / Mbar,
                "gamma_s": gamma_s,
                "gamma_frozen_cp_cv": gas.cp_mass / gas.cv_mass,
                "cp_eq_kJ_per_kgK": "", "cp_fr_kJ_per_kgK": gas.cp_mass / 1000.0,
                "cstar_m_per_s": "", "cf_exit": "",
                "Isp_eq_m_per_s": "", "Isp_vac_eq_m_per_s": "",
                "v_exit_eq_pr100_m_per_s": v_eq,
                "v_exit_frozen_pr100_m_per_s": v_fr,
                "dv_eq_minus_frozen": v_eq - v_fr,
                "mach_exit": "",
                "X_H2O": X.get("H2O", 0.0), "X_CO": X.get("CO", 0.0),
                "X_CO2": X.get("CO2", 0.0), "X_H2": X.get("H2", 0.0),
                "X_OH": X.get("OH", 0.0), "X_O2": X.get("O2", 0.0),
                "X_H": X.get("H", 0.0), "X_O": X.get("O", 0.0),
                "sum_X": float(np.sum(gas.X)),
                "sound_speed_frozen": gas.sound_speed,
            })
        except Exception as exc:
            row["converged"] = False
            row["error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    print(f"  cantera sweep: {len(rows)} points in {time.perf_counter()-t0:.2f} s")
    return rows


def main():
    try:
        import cea  # noqa: F401
        rows = run_cea()
    except ImportError:
        import cantera  # noqa: F401
        rows = run_cantera()

    out = sys.argv[1] if len(sys.argv) > 1 else "of_sweep.csv"
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("written:", out, f"({len(rows)} rows, {len(keys)} columns)")


if __name__ == "__main__":
    main()
