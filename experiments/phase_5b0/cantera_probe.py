"""Phase 5B-0 - Cantera capability probe.

Experimental discovery script. NOT production code.
"""
import hashlib
import json
import os
import sys

import numpy as np

import cantera as ct

OUT = {}


def sec(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


# ---------------------------------------------------------------------------
sec("1. PROVENANCE")
# ---------------------------------------------------------------------------
data_dir = os.path.join(os.path.dirname(ct.__file__), "data")
prov = {
    "version": ct.__version__,
    "git_commit": getattr(ct, "__git_commit__", None),
    "python": sys.version.split()[0],
    "data_dir": data_dir,
    "data_directories": list(ct.get_data_directories()),
}
for mech in ("gri30.yaml", "nasa_gas.yaml", "nasa_condensed.yaml"):
    p = os.path.join(data_dir, mech)
    if os.path.exists(p):
        prov[mech] = {
            "bytes": os.path.getsize(p),
            "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
        }
for k, v in prov.items():
    print(f"  {k}: {v}")
OUT["provenance"] = prov

# ---------------------------------------------------------------------------
sec("2. AVAILABLE DATABASES")
# ---------------------------------------------------------------------------
dbs = {}
for mech in ("gri30.yaml", "nasa_gas.yaml", "nasa_condensed.yaml"):
    try:
        sp = ct.Species.list_from_file(mech)
        dbs[mech] = {"n_species": len(sp),
                     "sample": [s.name for s in sp[:12]]}
        print(f"  {mech:22s} {len(sp):5d} species")
    except Exception as exc:
        dbs[mech] = f"{type(exc).__name__}: {exc}"
        print(f"  {mech:22s} FAILED {dbs[mech]}")
# does nasa_gas contain the CEA-style names we need?
try:
    names = {s.name for s in ct.Species.list_from_file("nasa_gas.yaml")}
    want = ["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH", "HO2", "H2O2", "CH4"]
    dbs["nasa_gas_has_target_species"] = {w: (w in names) for w in want}
    print(f"  nasa_gas has target species: {dbs['nasa_gas_has_target_species']}")
    cond = {s.name for s in ct.Species.list_from_file("nasa_condensed.yaml")}
    dbs["nasa_condensed_sample"] = sorted(cond)[:20]
    dbs["nasa_condensed_n"] = len(cond)
    print(f"  nasa_condensed: {len(cond)} species, sample {sorted(cond)[:8]}")
except Exception as exc:
    print("  species listing failed:", exc)
OUT["databases"] = dbs

# ---------------------------------------------------------------------------
sec("3. HP EQUILIBRIUM - CH4/O2, matched species set to CEA")
# ---------------------------------------------------------------------------
CEA_PRODUCTS = ["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH", "CH4"]
OF = 3.4
T_REAC = 298.15
P_PA = 10.0e6

M_CH4, M_O2 = 16.04246, 31.9988


def matched_solution():
    """Ideal-gas phase restricted to the CEA product species, NASA data."""
    allsp = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
    chosen = [allsp[n] for n in CEA_PRODUCTS if n in allsp]
    return ct.Solution(thermo="ideal-gas", species=chosen), [s.name for s in chosen]


hp = {}
try:
    gas, chosen = matched_solution()
    hp["species_used"] = chosen
    # reactant mass fractions from O/F
    y_f = 1.0 / (1.0 + OF)
    y_o = OF / (1.0 + OF)
    gas.TPY = T_REAC, P_PA, f"CH4:{y_f}, O2:{y_o}"
    h_reac = gas.enthalpy_mass
    s_reac = gas.entropy_mass
    gas.equilibrate("HP")
    hp.update({
        "converged": True,
        "T": gas.T, "P": gas.P, "density": gas.density,
        "mean_molecular_weight": gas.mean_molecular_weight,
        "cp_mass": gas.cp_mass, "cv_mass": gas.cv_mass,
        "cp_over_cv": gas.cp_mass / gas.cv_mass,
        "enthalpy_mass": gas.enthalpy_mass, "entropy_mass": gas.entropy_mass,
        "sound_speed": gas.sound_speed,
        "h_reactant": h_reac, "s_reactant": s_reac,
        "h_conserved_abs": abs(gas.enthalpy_mass - h_reac),
        "X": {n: float(x) for n, x in zip(gas.species_names, gas.X) if x > 0},
        "Y": {n: float(y) for n, y in zip(gas.species_names, gas.Y) if y > 0},
        "sum_X": float(np.sum(gas.X)), "sum_Y": float(np.sum(gas.Y)),
    })
    print(f"  species used: {chosen}")
    print(f"  Tc  = {gas.T:.4f} K")
    print(f"  Mbar= {gas.mean_molecular_weight:.6f}  (Cantera unit?)")
    print(f"  cp  = {gas.cp_mass:.4f}   cv = {gas.cv_mass:.4f}   cp/cv = {gas.cp_mass/gas.cv_mass:.6f}")
    print(f"  rho = {gas.density:.6f}   a = {gas.sound_speed:.4f}")
    print(f"  h_reac = {h_reac:.6e}  h_prod = {gas.enthalpy_mass:.6e}  |dh| = {hp['h_conserved_abs']:.3e}")
    print(f"  sum X = {hp['sum_X']:.15f}   sum Y = {hp['sum_Y']:.15f}")
    for n, x in sorted(hp["X"].items(), key=lambda kv: -kv[1])[:8]:
        print(f"    {n:8s} X={x:.6e}  Y={hp['Y'].get(n, 0):.6e}")
except Exception as exc:
    hp = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", hp)
OUT["hp_equilibrium"] = hp

# ---------------------------------------------------------------------------
sec("4. UNIT IDENTITY CHECKS")
# ---------------------------------------------------------------------------
idc = {}
if isinstance(hp, dict) and hp.get("converged"):
    Ru = 8.31446261815324
    gas, _ = matched_solution()
    gas.TPY = T_REAC, P_PA, f"CH4:{1/(1+OF)}, O2:{OF/(1+OF)}"
    gas.equilibrate("HP")
    Mbar = gas.mean_molecular_weight
    idc["mean_molecular_weight_raw"] = Mbar
    # hypothesis: kg/kmol
    R_spec = Ru * 1000.0 / Mbar
    idc["R_specific_if_kg_per_kmol"] = R_spec
    idc["cp_minus_cv"] = gas.cp_mass - gas.cv_mass
    idc["cp_minus_cv_over_R"] = (gas.cp_mass - gas.cv_mass) / R_spec
    idc["ideal_gas_p"] = gas.density * R_spec * gas.T
    idc["P_reported"] = gas.P
    idc["ideal_gas_rel_err"] = abs(idc["ideal_gas_p"] - gas.P) / gas.P
    idc["gamma_cp_cv"] = gas.cp_mass / gas.cv_mass
    idc["sound_speed"] = gas.sound_speed
    idc["a_from_gamma_R_T"] = float(np.sqrt(idc["gamma_cp_cv"] * R_spec * gas.T))
    idc["a_rel_diff"] = abs(idc["a_from_gamma_R_T"] - gas.sound_speed) / gas.sound_speed
    idc["cantera_gas_constant"] = ct.gas_constant
    for k, v in idc.items():
        print(f"  {k:32s} = {v}")
OUT["identity_checks"] = idc

# ---------------------------------------------------------------------------
sec("5. WHICH GAMMA DOES CANTERA GIVE?")
# ---------------------------------------------------------------------------
gam = {}
try:
    gas, _ = matched_solution()
    gas.TPY = T_REAC, P_PA, f"CH4:{1/(1+OF)}, O2:{OF/(1+OF)}"
    gas.equilibrate("HP")
    gam["cp_over_cv_frozen"] = gas.cp_mass / gas.cv_mass
    gam["sound_speed_frozen"] = gas.sound_speed
    # numerical equilibrium isentropic exponent: -dln p/dln v at constant s
    s0, T0, P0, rho0 = gas.entropy_mass, gas.T, gas.P, gas.density
    lo, hi = P0 * 0.999, P0 * 1.001
    gas.SP = s0, lo
    gas.equilibrate("SP")
    rlo = gas.density
    gas.SP = s0, hi
    gas.equilibrate("SP")
    rhi = gas.density
    gam["gamma_s_equilibrium_numeric"] = float(
        (np.log(hi) - np.log(lo)) / (np.log(rhi) - np.log(rlo)))
    gam["note"] = ("cp_mass/cv_mass is the FROZEN ratio at fixed composition; "
                   "the equilibrium isentropic exponent must be computed by "
                   "finite difference along an SP path")
    for k, v in gam.items():
        print(f"  {k}: {v}")
except Exception as exc:
    gam = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", gam)
OUT["gamma"] = gam

# ---------------------------------------------------------------------------
sec("6. SP EXPANSION - equilibrium vs frozen")
# ---------------------------------------------------------------------------
exp = {}
try:
    P_EXIT = P_PA / 100.0
    # equilibrium (shifting)
    gas, _ = matched_solution()
    gas.TPY = T_REAC, P_PA, f"CH4:{1/(1+OF)}, O2:{OF/(1+OF)}"
    gas.equilibrate("HP")
    h0, s0 = gas.enthalpy_mass, gas.entropy_mass
    gas.SP = s0, P_EXIT
    gas.equilibrate("SP")
    v_eq = float(np.sqrt(max(2.0 * (h0 - gas.enthalpy_mass), 0.0)))
    exp["equilibrium"] = {"T_exit": gas.T, "M_exit": gas.mean_molecular_weight,
                          "v_exit": v_eq}
    # frozen: same composition, isentropic to exit pressure
    gas2, _ = matched_solution()
    gas2.TPY = T_REAC, P_PA, f"CH4:{1/(1+OF)}, O2:{OF/(1+OF)}"
    gas2.equilibrate("HP")
    X_frozen = gas2.X.copy()
    gas2.SPX = s0, P_EXIT, X_frozen
    v_fr = float(np.sqrt(max(2.0 * (h0 - gas2.enthalpy_mass), 0.0)))
    exp["frozen"] = {"T_exit": gas2.T, "M_exit": gas2.mean_molecular_weight,
                     "v_exit": v_fr}
    exp["delta_v_eq_minus_frozen"] = v_eq - v_fr
    exp["T_eq_gt_T_frozen"] = exp["equilibrium"]["T_exit"] > exp["frozen"]["T_exit"]
    exp["M_rises_in_equilibrium"] = (exp["equilibrium"]["M_exit"]
                                     > OUT["hp_equilibrium"]["mean_molecular_weight"])
    print(f"  equilibrium exit: T={exp['equilibrium']['T_exit']:.2f} "
          f"M={exp['equilibrium']['M_exit']:.4f} v={v_eq:.2f}")
    print(f"  frozen      exit: T={exp['frozen']['T_exit']:.2f} "
          f"M={exp['frozen']['M_exit']:.4f} v={v_fr:.2f}")
    print(f"  dV(eq-frozen) = {exp['delta_v_eq_minus_frozen']:.2f} m/s")
    print(f"  T_eq > T_frozen: {exp['T_eq_gt_T_frozen']}   "
          f"M rises in equilibrium: {exp['M_rises_in_equilibrium']}")
except Exception as exc:
    exp = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", exp)
OUT["sp_expansion"] = exp

# ---------------------------------------------------------------------------
sec("7. ROCKET PERFORMANCE - native?")
# ---------------------------------------------------------------------------
rocket = {
    "c_star": "UNSUPPORTED - no such attribute/function in the Cantera API",
    "coefficient_of_thrust": "UNSUPPORTED",
    "Isp": "UNSUPPORTED",
    "area_ratio_expansion": "UNSUPPORTED - no area-ratio driven solver",
    "throat_sonic_search": "DERIVABLE - must be found by the caller "
                           "(equilibrium sound speed vs velocity)",
    "found_attrs": [a for a in dir(ct) if any(k in a.lower() for k in
                                              ("rocket", "isp", "cstar", "thrust", "nozzle"))],
}
print(f"  rocket-specific names in cantera namespace: {rocket['found_attrs']}")
for k, v in rocket.items():
    if k != "found_attrs":
        print(f"  {k:26s} {v}")
OUT["rocket"] = rocket

# ---------------------------------------------------------------------------
sec("8. CRYOGENIC REACTANTS")
# ---------------------------------------------------------------------------
cryo = {}
try:
    allsp = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
    cryo["gas_db_has_O2(L)"] = "O2(L)" in allsp
    cryo["gas_db_has_CH4(L)"] = "CH4(L)" in allsp
    condsp = {s.name for s in ct.Species.list_from_file("nasa_condensed.yaml")}
    cryo["condensed_db_has_O2(L)"] = "O2(L)" in condsp
    cryo["condensed_db_has_CH4(L)"] = "CH4(L)" in condsp
    cryo["condensed_names_sample"] = sorted(condsp)[:25]
    print(f"  nasa_gas has O2(L): {cryo['gas_db_has_O2(L)']}, CH4(L): {cryo['gas_db_has_CH4(L)']}")
    print(f"  nasa_condensed has O2(L): {cryo['condensed_db_has_O2(L)']}, "
          f"CH4(L): {cryo['condensed_db_has_CH4(L)']}")

    # What happens if you simply set T below the boiling point in a gas phase?
    gas, _ = matched_solution()
    gas.TPY = 111.643, P_PA, "CH4:1.0"
    cryo["gas_phase_at_111K"] = {
        "T": gas.T, "phase_of_matter": gas.phase_of_matter,
        "enthalpy_mass": gas.enthalpy_mass,
        "warning": "treated as an IDEAL GAS at 111 K - no condensation, "
                   "no latent heat; silently wrong as a liquid reactant",
    }
    print(f"  ideal-gas CH4 forced to 111.643 K: phase='{gas.phase_of_matter}', "
          f"h={gas.enthalpy_mass:.4e} J/kg  <-- NOT liquid methane")

    # PureFluid route
    try:
        w = ct.Methane()
        w.TP = 111.643, 101325.0
        cryo["purefluid_methane"] = {
            "available": True, "T": w.T, "P": w.P,
            "enthalpy_mass": w.enthalpy_mass,
            "phase_of_matter": w.phase_of_matter,
            "note": "PureFluid gives a real liquid enthalpy, but on its OWN "
                    "datum - not the reacting-mixture datum",
        }
        print(f"  ct.Methane() at 111.643 K, 1 atm: phase='{w.phase_of_matter}', "
              f"h={w.enthalpy_mass:.4e} J/kg")
        print("    -> different enthalpy datum from the ideal-gas mechanism; "
              "cannot be mixed directly")
    except Exception as exc:
        cryo["purefluid_methane"] = f"{type(exc).__name__}: {exc}"
        print("  PureFluid methane failed:", cryo["purefluid_methane"])
except Exception as exc:
    cryo["error"] = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", cryo["error"])
OUT["cryogenic"] = cryo

# ---------------------------------------------------------------------------
sec("9. ERROR BEHAVIOUR")
# ---------------------------------------------------------------------------
errs = {}


def try_case(label, fn):
    try:
        fn()
        errs[label] = "NO ERROR RAISED"
    except Exception as exc:
        errs[label] = f"{type(exc).__name__}: {str(exc)[:150].replace(chr(10), ' ')}"
    print(f"  {label:26s} -> {errs[label]}")


g0, _ = matched_solution()


def _neg_T():
    g0.TP = -50.0, P_PA


def _bad_species():
    g0.TPY = 300.0, P_PA, "NOTASPECIES:1.0"


def _bad_mech():
    ct.Solution("no_such_mechanism.yaml")


def _neg_P():
    g0.TP = 300.0, -1.0


try_case("negative temperature", _neg_T)
try_case("negative pressure", _neg_P)
try_case("invalid species", _bad_species)
try_case("invalid mechanism", _bad_mech)
OUT["errors"] = errs

# ---------------------------------------------------------------------------
sec("10. STATE / MUTABILITY / REPEATABILITY")
# ---------------------------------------------------------------------------


def solve_of(of_val):
    g, _ = matched_solution()
    g.TPY = T_REAC, P_PA, f"CH4:{1/(1+of_val)}, O2:{of_val/(1+of_val)}"
    g.equilibrate("HP")
    return g.T


rep = [solve_of(OF) for _ in range(10)]
OUT["repeatability"] = {"n": len(rep), "unique": len(set(rep)),
                        "bitwise_identical": len(set(rep)) == 1,
                        "first": rep[0], "last": rep[-1],
                        "spread": max(rep) - min(rep)}
print(f"  10 identical solves bitwise identical: {OUT['repeatability']['bitwise_identical']} "
      f"(spread {OUT['repeatability']['spread']:.3e})")

# reusing ONE object (the realistic fast path) - does history matter?
gshared, _ = matched_solution()


def solve_shared(of_val):
    gshared.TPY = T_REAC, P_PA, f"CH4:{1/(1+of_val)}, O2:{of_val/(1+of_val)}"
    gshared.equilibrate("HP")
    return gshared.T


a1 = solve_shared(OF)
b1 = solve_shared(2.6)
a2 = solve_shared(OF)
b2 = solve_shared(2.6)
a3 = solve_shared(OF)
OUT["state_leakage"] = {"A": [a1, a2, a3], "B": [b1, b2],
                        "A_stable": a1 == a2 == a3, "B_stable": b1 == b2,
                        "A_differs_from_B": a1 != b1,
                        "note": "shared mutable Solution object reused across solves"}
print(f"  shared-object A/B/A/B/A: A_stable={OUT['state_leakage']['A_stable']} "
      f"B_stable={OUT['state_leakage']['B_stable']}")

gm, _ = matched_solution()
gm.TP = 300.0, 101325.0
before = gm.T
gm.TP = 400.0, 101325.0
OUT["mutability"] = (f"MUTABLE: the Solution object is a mutable state container "
                     f"(T {before} -> {gm.T}); raw objects must not escape an adapter")
print(f"  {OUT['mutability']}")

out_path = sys.argv[1] if len(sys.argv) > 1 else "cantera_probe.json"
with open(out_path, "w") as fh:
    json.dump(OUT, fh, indent=2, default=str)
print("\nwritten:", out_path)
