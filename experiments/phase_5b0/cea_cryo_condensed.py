"""Phase 5B-0 - CEA cryogenic reactants, condensed phases, Isp units, RP-1.

Experimental. NOT production code.
"""
import json
import sys

import numpy as np

import cea

OUT = {}
FUEL_W = np.array([100.0, 0.0])
OXID_W = np.array([0.0, 100.0])
PROD = ["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH", "HO2", "H2O2",
        "CH4", "C(gr)"]


def sec(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


def rocket(reac_names, prod_names, of, pc_bar, T_reac, supar=40.0, n_frz=None):
    reac = cea.Mixture(reac_names)
    prod = cea.Mixture(prod_names)
    solver = cea.RocketSolver(prod, reactants=reac)
    soln = cea.RocketSolution(solver)
    w = reac.of_ratio_to_weights(OXID_W, FUEL_W, of)
    hc = reac.calc_property(cea.ENTHALPY, w, T_reac) / cea.R
    kw = {"supar": supar, "hc": hc}
    if n_frz is not None:
        kw["n_frz"] = n_frz
    solver.solve(soln, w, pc_bar, **kw)
    return solver, soln, hc


# ---------------------------------------------------------------------------
sec("1. CRYOGENIC LIQUID REACTANTS - per-reactant temperatures")
# ---------------------------------------------------------------------------
cryo = {}
# CH4(L) at 111.643 K (normal boiling point), O2(L) at 90.17 K
for label, names, temps in (
    ("gas_298", ["CH4", "O2"], 298.15),
    ("liquid_nbp", ["CH4(L)", "O2(L)"], [111.643, 90.17]),
):
    try:
        solver, soln, hc = rocket(names, PROD, 3.4, 100.0, temps)
        cryo[label] = {
            "reactants": names, "T_reac": temps, "hc_over_R": hc,
            "converged": bool(soln.converged),
            "Tc": soln.T[0], "T_throat": soln.T[1], "T_exit": soln.T[2],
            "c_star": soln.c_star[0], "Isp_exit": soln.Isp[-1],
            "Isp_vac_exit": soln.Isp_vacuum[-1],
            "gamma_s_c": soln.gamma_s[0], "M_c": soln.M[0],
            "cf_exit": soln.coefficient_of_thrust[-1],
        }
        print(f"  {label:12s} Tc={soln.T[0]:8.2f} K  c*={soln.c_star[0]:8.2f}  "
              f"Isp_exit={soln.Isp[-1]:8.2f}  hc/R={hc:.4f}")
    except Exception as exc:
        cryo[label] = f"{type(exc).__name__}: {exc}"
        print(f"  {label:12s} FAILED: {cryo[label]}")

if isinstance(cryo.get("gas_298"), dict) and isinstance(cryo.get("liquid_nbp"), dict):
    dT = cryo["gas_298"]["Tc"] - cryo["liquid_nbp"]["Tc"]
    dI = cryo["gas_298"]["Isp_exit"] - cryo["liquid_nbp"]["Isp_exit"]
    cryo["delta_gas_minus_liquid"] = {"Tc_K": dT, "Isp_exit": dI}
    print(f"  gaseous-minus-liquid: dTc = {dT:.2f} K, dIsp_exit = {dI:.2f}")
    print("  -> a nonzero delta proves the phase enthalpy is actually applied")
OUT["cryogenic"] = cryo

# ---------------------------------------------------------------------------
sec("2. Isp UNITS")
# ---------------------------------------------------------------------------
u = {}
if isinstance(cryo.get("liquid_nbp"), dict):
    isp = cryo["liquid_nbp"]["Isp_exit"]
    u["Isp_raw"] = isp
    u["as_seconds_if_m_per_s"] = isp / 9.80665
    u["cf_times_cstar"] = (cryo["liquid_nbp"]["cf_exit"]
                           * cryo["liquid_nbp"]["c_star"])
    u["identity_Isp_eq_cf_cstar"] = abs(
        u["cf_times_cstar"] - isp) / max(abs(isp), 1e-30)
    print(f"  Isp raw            = {u['Isp_raw']:.4f}")
    print(f"  /g0 (if m/s)       = {u['as_seconds_if_m_per_s']:.4f} s")
    print(f"  Cf * c*            = {u['cf_times_cstar']:.4f}")
    print(f"  rel diff Isp vs Cf*c* = {u['identity_Isp_eq_cf_cstar']:.3e}")
    print("  -> Isp == Cf*c* confirms Isp is an effective exhaust velocity [m/s]")
OUT["isp_units"] = u

# ---------------------------------------------------------------------------
sec("3. CONDENSED PHASES - is C(gr) actually present?")
# ---------------------------------------------------------------------------
cond = {}
for label, of in (("stoich_rich_3.4", 3.4), ("very_fuel_rich_1.0", 1.0),
                  ("extremely_rich_0.5", 0.5)):
    try:
        solver, soln, _ = rocket(["CH4", "O2"], PROD, of, 100.0, 298.15)
        X = {k: float(v[0]) for k, v in soln.mole_fractions.items()}
        Y = {k: float(v[0]) for k, v in soln.mass_fractions.items()}
        cgr_X = X.get("C(gr)", 0.0)
        cgr_Y = Y.get("C(gr)", 0.0)
        cond[label] = {
            "of": of, "Tc": soln.T[0], "num_condensed": solver.num_condensed,
            "C(gr)_X": cgr_X, "C(gr)_Y": cgr_Y,
            "sum_X": sum(X.values()), "sum_Y": sum(Y.values()),
        }
        print(f"  O/F={of:<5} Tc={soln.T[0]:8.2f}  num_condensed={solver.num_condensed}"
              f"  X[C(gr)]={cgr_X:.6e}  Y[C(gr)]={cgr_Y:.6e}")
    except Exception as exc:
        cond[label] = f"{type(exc).__name__}: {exc}"
        print(f"  O/F={of} FAILED: {cond[label]}")
print("  NOTE: num_condensed counts condensed species PRESENT IN THE PRODUCT LIST,")
print("        not necessarily species with a nonzero amount at the solution.")
OUT["condensed"] = cond

# ---------------------------------------------------------------------------
sec("4. ALUMINISED CASE - a real condensed-phase producer")
# ---------------------------------------------------------------------------
alu = {}
try:
    names_r = ["AL", "O2"]
    names_p = ["AL", "ALO", "ALO2", "AL2O", "AL2O2", "AL2O3(a)", "AL2O3(L)",
               "O", "O2"]
    solver, soln, _ = rocket(names_r, names_p, 1.0, 100.0, 298.15)
    X = {k: float(v[0]) for k, v in soln.mole_fractions.items()}
    Y = {k: float(v[0]) for k, v in soln.mass_fractions.items()}
    condensed_Y = sum(v for k, v in Y.items() if "(a)" in k or "(L)" in k)
    alu = {"Tc": soln.T[0], "num_condensed": solver.num_condensed,
           "condensed_mass_fraction": condensed_Y,
           "top": sorted(X.items(), key=lambda kv: -kv[1])[:6]}
    print(f"  Al/O2 O/F=1.0  Tc={soln.T[0]:.2f}  num_condensed={solver.num_condensed}")
    print(f"  condensed mass fraction = {condensed_Y:.6f}")
    for k, v in alu["top"]:
        print(f"    {k:12s} X={v:.6e}  Y={Y.get(k, 0.0):.6e}")
except Exception as exc:
    alu = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", alu)
OUT["aluminised"] = alu

# ---------------------------------------------------------------------------
sec("5. RP-1 AND OTHER PROPELLANT NAMES")
# ---------------------------------------------------------------------------
names = {}
probe = ["RP-1", "CH6N2(L)", "MMH", "N2H4(L)", "N2O4(L)", "H2O2(L)",
         "Jet-A(L)", "JP-10(L)", "C2H5OH(L)", "H2(L)", "C12H26,n-dodecane"]
for n in probe:
    try:
        cea.Mixture([n])
        try:
            r = cea.Reactant(n)
            rng = r.get_valid_temperature_range()
        except Exception:
            rng = None
        names[n] = {"in_thermo_db": True, "reactant_T_range": list(rng) if rng else None}
        print(f"  {n:22s} OK   T_range={names[n]['reactant_T_range']}")
    except Exception as exc:
        names[n] = {"in_thermo_db": False, "error": str(exc)[:110]}
        print(f"  {n:22s} NOT FOUND")
OUT["propellant_names"] = names

# ---------------------------------------------------------------------------
sec("6. LOX/RP-1 ROCKET CASE")
# ---------------------------------------------------------------------------
rp1 = {}
try:
    p = ["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH", "HO2", "C(gr)"]
    solver, soln, _ = rocket(["RP-1", "O2(L)"], p, 2.56, 100.0, [298.15, 90.17])
    rp1 = {"Tc": soln.T[0], "c_star": soln.c_star[0],
           "Isp_exit": soln.Isp[-1], "gamma_s_c": soln.gamma_s[0],
           "M_c": soln.M[0], "converged": bool(soln.converged)}
    print(f"  LOX/RP-1 O/F=2.56 Pc=100bar: Tc={soln.T[0]:.2f} K  "
          f"c*={soln.c_star[0]:.2f} m/s  M={soln.M[0]:.4f}  gamma_s={soln.gamma_s[0]:.4f}")
except Exception as exc:
    rp1 = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", rp1)
OUT["lox_rp1"] = rp1

# ---------------------------------------------------------------------------
sec("7. ELEMENT CONSERVATION (independent check)")
# ---------------------------------------------------------------------------
# Reactant elemental content per kg vs product elemental content per kg.
el = {}
try:
    reac = cea.Mixture(["CH4", "O2"])
    prod = cea.Mixture(PROD)
    solver = cea.EqSolver(prod, reactants=reac)
    soln = cea.EqSolution(solver)
    of = 3.4
    w = reac.of_ratio_to_weights(OXID_W, FUEL_W, of)
    h0 = reac.calc_property(cea.ENTHALPY, w, 298.15) / cea.R
    solver.solve(soln, cea.HP, h0, 100.0, w)

    # reactant side, per kg of mixture: CH4 and O2 mass fractions
    wsum = float(np.sum(w))
    y_ch4, y_o2 = float(w[0]) / wsum, float(w[1]) / wsum
    M_CH4, M_O2 = 16.04246, 31.9988          # kg/kmol
    reac_el = {
        "C": y_ch4 / M_CH4 * 1.0,
        "H": y_ch4 / M_CH4 * 4.0,
        "O": y_o2 / M_O2 * 2.0,
    }
    ATOMS = {
        "CO": {"C": 1, "O": 1}, "CO2": {"C": 1, "O": 2}, "H": {"H": 1},
        "H2": {"H": 2}, "H2O": {"H": 2, "O": 1}, "O": {"O": 1},
        "O2": {"O": 2}, "OH": {"O": 1, "H": 1}, "HO2": {"H": 1, "O": 2},
        "H2O2": {"H": 2, "O": 2}, "CH4": {"C": 1, "H": 4}, "C(gr)": {"C": 1},
    }
    MW = {"CO": 28.0101, "CO2": 44.0095, "H": 1.00794, "H2": 2.01588,
          "H2O": 18.01528, "O": 15.9994, "O2": 31.9988, "OH": 17.00734,
          "HO2": 33.00674, "H2O2": 34.01468, "CH4": 16.04246, "C(gr)": 12.0107}
    Y = soln.mass_fractions
    prod_el = {"C": 0.0, "H": 0.0, "O": 0.0}
    for sp, y in Y.items():
        for elem, cnt in ATOMS[sp].items():
            prod_el[elem] += y / MW[sp] * cnt
    el = {"reactant_kmol_per_kg": reac_el, "product_kmol_per_kg": prod_el,
          "rel_imbalance": {k: abs(prod_el[k] - reac_el[k]) / max(abs(reac_el[k]), 1e-30)
                            for k in reac_el}}
    for k in ("C", "H", "O"):
        print(f"  {k}: reactant={reac_el[k]:.9e}  product={prod_el[k]:.9e}  "
              f"rel={el['rel_imbalance'][k]:.3e}")
    el["max_rel_imbalance"] = max(el["rel_imbalance"].values())
    print(f"  max relative elemental imbalance = {el['max_rel_imbalance']:.3e}")
except Exception as exc:
    el = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", el)
OUT["element_balance"] = el

out_path = sys.argv[1] if len(sys.argv) > 1 else "cea_cryo_condensed.json"
with open(out_path, "w") as fh:
    json.dump(OUT, fh, indent=2, default=str)
print("\nwritten:", out_path)
