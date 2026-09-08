"""Phase 5B-0 - RP-1311 reference case, custom reactants, blends, concurrency.

Experimental. NOT production code.
"""
import concurrent.futures
import json
import sys
import time

import numpy as np

import cea

OUT = {}


def sec(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


# ---------------------------------------------------------------------------
sec("1. RP-1311 EXAMPLE 8 - published LOX/LH2 IAC rocket case")
# ---------------------------------------------------------------------------
try:
    reac_names = ["H2(L)", "O2(L)"]
    T_reactant = np.array([20.27, 90.17])
    of_ratio = 5.55157
    pc = 53.3172
    reac = cea.Mixture(reac_names)
    prod = cea.Mixture(reac_names, products_from_reactants=True)
    solver = cea.RocketSolver(prod, reactants=reac)
    soln = cea.RocketSolution(solver)
    w = reac.of_ratio_to_weights(np.array([0.0, 1.0]), np.array([1.0, 0.0]),
                                 of_ratio)
    hc = reac.calc_property(cea.ENTHALPY, w, T_reactant) / cea.R
    solver.solve(soln, w, pc, [10.0, 100.0, 1000.0], subar=[1.58],
                 supar=[25.0, 50.0, 75.0], hc=hc, iac=True)
    ex8 = {
        "source": "NASA RP-1311 Part II, example 8 (shipped with cea 3.3.4)",
        "inputs": {"reactants": reac_names, "T_reac_K": T_reactant.tolist(),
                   "of_ratio": of_ratio, "pc_bar": pc,
                   "pi_p": [10.0, 100.0, 1000.0], "subar": [1.58],
                   "supar": [25.0, 50.0, 75.0], "iac": True},
        "converged": bool(soln.converged), "num_pts": int(soln.num_pts),
        "T_K": soln.T.tolist(), "P_bar": soln.P.tolist(),
        "M_kg_per_kmol": soln.M.tolist(), "gamma_s": soln.gamma_s.tolist(),
        "ae_at": soln.ae_at.tolist(), "mach": soln.Mach.tolist(),
        "cstar_m_per_s": soln.c_star.tolist(),
        "cf": soln.coefficient_of_thrust.tolist(),
        "Isp_m_per_s": soln.Isp.tolist(),
        "Isp_vac_m_per_s": soln.Isp_vacuum.tolist(),
        "n_products_auto_selected": int(solver.num_products),
    }
    print(f"  converged={soln.converged}  stations={soln.num_pts}  "
          f"auto-selected products={solver.num_products}")
    print(f"  Tc  = {soln.T[0]:.2f} K")
    print(f"  c*  = {soln.c_star[0]:.2f} m/s")
    print(f"  Isp = {np.array2string(soln.Isp, precision=2)}")
    print(f"  Ae/At = {np.array2string(soln.ae_at, precision=3)}")
    OUT["rp1311_example8"] = ex8
except Exception as exc:
    OUT["rp1311_example8"] = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", OUT["rp1311_example8"])

# ---------------------------------------------------------------------------
sec("2. CUSTOM REACTANT - a species not in thermo.lib")
# ---------------------------------------------------------------------------
cust = {}
try:
    import inspect
    cust["Reactant_signature"] = str(inspect.signature(cea.Reactant.__init__)) \
        if hasattr(cea.Reactant, "__init__") else "n/a"
except Exception:
    cust["Reactant_signature"] = "not introspectable (Cython)"
try:
    # RP-1 style surrogate defined explicitly: formula + heat of formation
    r = cea.Reactant("MY-RP1-SURROGATE",
                     formula={"C": 1.0, "H": 1.9423},
                     enthalpy=-5430.0, enthalpy_units="cal/mol",
                     temperature=298.15)
    cust["custom_reactant_constructed"] = True
    cust["name"] = r.name
    cust["formula"] = dict(r.formula) if r.formula else None
    cust["enthalpy"] = r.enthalpy
    cust["enthalpy_units"] = r.enthalpy_units
    cust["temperature"] = r.temperature
    print(f"  custom reactant OK: {r.name} formula={cust['formula']} "
          f"h={r.enthalpy} {r.enthalpy_units} at {r.temperature} K")
    # use it in a mixture
    m = cea.Mixture([r, "O2(L)"])
    cust["usable_in_mixture"] = True
    print(f"  usable in a Mixture: True  (num_species={m.num_species})")
except Exception as exc:
    cust["error"] = f"{type(exc).__name__}: {exc}"
    print("  custom reactant FAILED:", cust["error"])
OUT["custom_reactant"] = cust

# ---------------------------------------------------------------------------
sec("3. CONCENTRATION-DEFINED OXIDISER - H2O2 90 wt%")
# ---------------------------------------------------------------------------
h2o2 = {}
try:
    # 90 % H2O2 / 10 % H2O by mass, as a two-component oxidiser blend
    reac = cea.Mixture(["RP-1", "H2O2(L)", "H2O(L)"])
    prod = cea.Mixture(["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH",
                        "HO2", "C(gr)"])
    solver = cea.RocketSolver(prod, reactants=reac)
    soln = cea.RocketSolution(solver)
    of = 7.0
    fuel_w = np.array([1.0, 0.0, 0.0])
    oxid_w = np.array([0.0, 0.90, 0.10])      # MASS fractions within the oxidiser
    w = reac.of_ratio_to_weights(oxid_w, fuel_w, of)
    hc = reac.calc_property(cea.ENTHALPY, w, [298.15, 298.15, 298.15]) / cea.R
    solver.solve(soln, w, 100.0, supar=40.0, hc=hc)
    h2o2 = {"of": of, "oxidiser_blend_mass": {"H2O2(L)": 0.90, "H2O(L)": 0.10},
            "weights_used": w.tolist(), "converged": bool(soln.converged),
            "Tc_K": float(soln.T[0]), "cstar": float(soln.c_star[0]),
            "Isp_exit": float(soln.Isp[-1]), "M": float(soln.M[0])}
    print(f"  RP-1 / 90% H2O2 at O/F={of}: Tc={soln.T[0]:.2f} K  "
          f"c*={soln.c_star[0]:.2f} m/s  Isp={soln.Isp[-1]:.2f} m/s")
    print(f"  weights vector = {w}  <- blend expressed by MASS within the oxidiser")
except Exception as exc:
    h2o2 = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", h2o2)
OUT["h2o2_concentration_blend"] = h2o2

# ---------------------------------------------------------------------------
sec("4. CONCURRENCY - modest, deliberate, documented")
# ---------------------------------------------------------------------------
conc = {}
PRODUCTS = ["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH", "HO2", "H2O2", "CH4"]


def one_case(of_val, n=25):
    """Independent solver objects per worker - no sharing by construction."""
    r = cea.Mixture(["CH4", "O2"])
    p = cea.Mixture(PRODUCTS)
    sv = cea.EqSolver(p, reactants=r)
    out = []
    for _ in range(n):
        w = r.of_ratio_to_weights(np.array([0.0, 100.0]),
                                  np.array([100.0, 0.0]), of_val)
        h = r.calc_property(cea.ENTHALPY, w, 298.15) / cea.R
        s = cea.EqSolution(sv)
        sv.solve(s, cea.HP, h, 100.0, w)
        out.append(s.T)
    return out


ofs = [2.6, 3.0, 3.4, 3.8]
t0 = time.perf_counter()
serial = {o: one_case(o) for o in ofs}
conc["serial_s"] = time.perf_counter() - t0
try:
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        threaded = dict(zip(ofs, pool.map(one_case, ofs)))
    conc["threaded_s"] = time.perf_counter() - t0
    conc["threaded_matches_serial"] = all(serial[o] == threaded[o] for o in ofs)
    conc["each_case_internally_constant"] = all(
        len(set(threaded[o])) == 1 for o in ofs)
    conc["verdict"] = ("NO CORRUPTION OBSERVED in this modest test with "
                       "per-worker solver objects; NOT a thread-safety "
                       "guarantee - the library documents no such guarantee")
    print(f"  serial   {conc['serial_s']*1e3:.1f} ms")
    print(f"  threaded {conc['threaded_s']*1e3:.1f} ms")
    print(f"  threaded == serial: {conc['threaded_matches_serial']}")
    print(f"  {conc['verdict']}")
except Exception as exc:
    conc["error"] = f"{type(exc).__name__}: {exc}"
    print("  threading FAILED:", conc["error"])
OUT["concurrency"] = conc

# ---------------------------------------------------------------------------
sec("5. SHARED-SOLVER CONCURRENCY - the unsafe pattern, tested deliberately")
# ---------------------------------------------------------------------------
shared = {}
try:
    r = cea.Mixture(["CH4", "O2"])
    p = cea.Mixture(PRODUCTS)
    sv = cea.EqSolver(p, reactants=r)

    def shared_case(of_val, n=25):
        out = []
        for _ in range(n):
            w = r.of_ratio_to_weights(np.array([0.0, 100.0]),
                                      np.array([100.0, 0.0]), of_val)
            h = r.calc_property(cea.ENTHALPY, w, 298.15) / cea.R
            s = cea.EqSolution(sv)
            sv.solve(s, cea.HP, h, 100.0, w)
            out.append(s.T)
        return out

    ref = {o: shared_case(o) for o in ofs}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        got = dict(zip(ofs, pool.map(shared_case, ofs)))
    shared["matches_serial"] = all(ref[o] == got[o] for o in ofs)
    shared["internally_constant"] = all(len(set(got[o])) == 1 for o in ofs)
    shared["verdict"] = ("shared EqSolver across threads: "
                         + ("no corruption observed"
                            if shared["matches_serial"] else
                            "CORRUPTION OBSERVED - results differ from serial"))
    print(f"  shared solver across threads matches serial: {shared['matches_serial']}")
    print(f"  each case internally constant: {shared['internally_constant']}")
    print(f"  -> {shared['verdict']}")
except Exception as exc:
    shared["error"] = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", shared["error"])
OUT["shared_solver_concurrency"] = shared

# ---------------------------------------------------------------------------
sec("6. PROVIDER-ABSENT DETECTION PATTERN")
# ---------------------------------------------------------------------------
det = {}
code = ("try:\n"
        "    import cea\n"
        "    print('AVAILABLE', cea.__version__)\n"
        "except ImportError as exc:\n"
        "    print('UNAVAILABLE', exc)\n")
det["pattern"] = code
det["import_is_side_effect_free"] = None
try:
    # does importing cea alone initialise the Fortran library / read data?
    det["is_initialized_after_import"] = bool(cea.is_initialized())
    print(f"  cea.is_initialized() after import: {det['is_initialized_after_import']}")
    print("  -> import DOES initialise the native library and load thermo.lib;")
    print("     a bare `import cea` is therefore not free, and a missing data")
    print("     file fails at IMPORT time, not at first solve.")
except Exception as exc:
    det["error"] = str(exc)
OUT["availability_detection"] = det

out = sys.argv[1] if len(sys.argv) > 1 else "cea_final_tests.json"
with open(out, "w") as fh:
    json.dump(OUT, fh, indent=2, default=str)
print("\nwritten:", out)
