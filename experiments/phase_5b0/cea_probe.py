"""Phase 5B-0 - NASA CEA v3 capability probe.

Experimental discovery script. NOT production code. Not importable by
rocketforge/. Uses provider-specific APIs freely, which is the point.

Run with the isolated CEA environment:
    %TEMP%\\rocketforge_phase5b0_cea\\Scripts\\python.exe cea_probe.py
"""
import hashlib
import json
import os
import sys

import numpy as np

import cea

OUT = {}


def section(name):
    print()
    print("=" * 72)
    print(name)
    print("=" * 72)


# ---------------------------------------------------------------------------
section("1. PROVENANCE")
# ---------------------------------------------------------------------------
pkg_dir = os.path.dirname(cea.__file__)
prov = {
    "package_version": cea.__version__,
    "lib_version": cea.lib_version(),
    "lib_version_tuple": [cea.lib_version_major(), cea.lib_version_minor(),
                          cea.lib_version_patch()],
    "python": sys.version.split()[0],
    "package_dir": pkg_dir,
    "R_constant": cea.R,
}
for fname in ("data/thermo.lib", "data/trans.lib"):
    p = os.path.join(pkg_dir, fname)
    if os.path.exists(p):
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        prov[fname] = {"bytes": os.path.getsize(p), "sha256": h}
for k, v in prov.items():
    print(f"  {k}: {v}")
OUT["provenance"] = prov

# ---------------------------------------------------------------------------
section("2. REACTANT SPECIES AVAILABILITY (cryogenic / condensed)")
# ---------------------------------------------------------------------------
candidates = [
    "O2", "O2(L)", "CH4", "CH4(L)", "H2", "H2(L)",
    "RP-1", "RP_1", "JP-10(L)", "Jet-A(L)", "C2H5OH(L)",
    "N2O4(L)", "CH6N2(L)", "N2H4(L)", "H2O2(L)", "Air",
    "AL2O3(a)", "AL2O3(L)", "C(gr)",
]
avail = {}
for name in candidates:
    try:
        m = cea.Mixture([name])
        avail[name] = True
    except Exception as exc:
        avail[name] = f"{type(exc).__name__}: {exc}"
for k, v in avail.items():
    print(f"  {k:14s} {'OK' if v is True else v}")
OUT["species_availability"] = avail

# ---------------------------------------------------------------------------
section("3. Reactant metadata + valid temperature range")
# ---------------------------------------------------------------------------
meta = {}
for name in ("O2", "O2(L)", "CH4", "CH4(L)", "RP-1"):
    if avail.get(name) is not True:
        continue
    try:
        r = cea.Reactant(name)
        meta[name] = {
            "formula": dict(r.formula) if r.formula else None,
            "molecular_weight": r.molecular_weight,
            "enthalpy": r.enthalpy,
            "enthalpy_units": r.enthalpy_units,
            "temperature": r.temperature,
            "valid_T_range": list(r.get_valid_temperature_range()),
        }
    except Exception as exc:
        meta[name] = f"{type(exc).__name__}: {exc}"
for k, v in meta.items():
    print(f"  {k}: {v}")
OUT["reactant_metadata"] = meta

# ---------------------------------------------------------------------------
section("4. UNITS DISCOVERY - chamber HP, gaseous CH4/O2")
# ---------------------------------------------------------------------------
reac = cea.Mixture(["CH4", "O2"])
prod = cea.Mixture(["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH", "CH4", "C(gr)"])
solver = cea.EqSolver(prod, reactants=reac)
soln = cea.EqSolution(solver)

fuel_w = np.array([100.0, 0.0])
oxid_w = np.array([0.0, 100.0])
of = 3.4
weights = reac.of_ratio_to_weights(oxid_w, fuel_w, of)
T_reac = 298.15
p_bar = 10.0e6 / 1.0e5           # 10 MPa expressed in bar

h0 = reac.calc_property(cea.ENTHALPY, weights, T_reac) / cea.R
solver.solve(soln, cea.HP, h0, p_bar, weights)

print(f"  converged: {soln.converged}")
raw = {
    "T": soln.T, "P": soln.P, "density": soln.density, "volume": soln.volume,
    "M": soln.M, "MW": soln.MW, "enthalpy": soln.enthalpy,
    "entropy": soln.entropy, "energy": soln.energy,
    "gamma_s": soln.gamma_s, "cp_eq": soln.cp_eq, "cp_fr": soln.cp_fr,
    "cv_eq": soln.cv_eq, "cv_fr": soln.cv_fr,
}
for k, v in raw.items():
    print(f"  {k:10s} = {v!r}")
OUT["units_probe_raw"] = raw
OUT["units_probe_inputs"] = {"of": of, "T_reac": T_reac, "p_bar": p_bar,
                             "h0_over_R": h0}

# ---------------------------------------------------------------------------
section("5. UNIT IDENTITY CHECKS")
# ---------------------------------------------------------------------------
Ru = 8.31446261815324             # J/(mol K)
checks = {}

# Hypothesis: M is kg/kmol (== g/mol). Then R_specific = Ru*1000/M  [J/(kg K)]
R_spec_from_M = Ru * 1000.0 / soln.M
checks["R_specific_from_M_J_per_kgK"] = R_spec_from_M

# cp_eq/cp_fr reported in kJ/(kg K) per the shipped sample labels
cp_fr_SI = soln.cp_fr * 1000.0
cv_fr_SI = soln.cv_fr * 1000.0
checks["cp_fr_SI"] = cp_fr_SI
checks["cv_fr_SI"] = cv_fr_SI
checks["cp_minus_cv_fr"] = cp_fr_SI - cv_fr_SI
checks["cp_minus_cv_vs_R"] = (cp_fr_SI - cv_fr_SI) / R_spec_from_M
checks["gamma_frozen_cp_over_cv"] = soln.cp_fr / soln.cv_fr
checks["gamma_s_reported"] = soln.gamma_s
checks["gamma_eq_cp_over_cv"] = soln.cp_eq / soln.cv_eq

# Ideal gas: p = rho R T. Test density unit hypotheses.
for label, rho in (("as_is", soln.density),
                   ("x1e-3", soln.density * 1e-3),
                   ("x1e3", soln.density * 1e3)):
    p_pred = rho * R_spec_from_M * soln.T          # Pa if rho in kg/m3
    checks[f"ideal_gas_p_Pa_{label}"] = p_pred
checks["P_reported"] = soln.P
checks["P_input_bar"] = p_bar

for k, v in checks.items():
    print(f"  {k:32s} = {v}")
OUT["identity_checks"] = checks

# ---------------------------------------------------------------------------
section("6. COMPOSITION + CONSERVATION")
# ---------------------------------------------------------------------------
X = soln.mole_fractions
Y = soln.mass_fractions
print(f"  n species returned: {len(X)}")
print(f"  sum(X) = {sum(X.values()):.15f}")
print(f"  sum(Y) = {sum(Y.values()):.15f}")
top = sorted(X.items(), key=lambda kv: -kv[1])[:8]
for name, x in top:
    print(f"    {name:10s} X={x:.6e}  Y={Y.get(name, float('nan')):.6e}")
OUT["composition"] = {
    "n_species": len(X),
    "sum_X": sum(X.values()),
    "sum_Y": sum(Y.values()),
    "mole_fractions": X,
    "mass_fractions": Y,
}
OUT["counts"] = {
    "num_gas": solver.num_gas, "num_condensed": solver.num_condensed,
    "num_elements": solver.num_elements, "num_products": solver.num_products,
    "num_reactants": solver.num_reactants,
}
print(f"  counts: {OUT['counts']}")

# ---------------------------------------------------------------------------
section("7. ROCKET MODE - equilibrium and frozen")
# ---------------------------------------------------------------------------
rocket = {}
try:
    rprod = cea.Mixture(["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH",
                         "HO2", "H2O2", "CH4", "C(gr)"])
    rreac = cea.Mixture(["CH4", "O2"])
    rsolver = cea.RocketSolver(rprod, reactants=rreac)
    rsoln = cea.RocketSolution(rsolver)
    w = rreac.of_ratio_to_weights(np.array([0.0, 100.0]),
                                  np.array([100.0, 0.0]), of)
    hc = rreac.calc_property(cea.ENTHALPY, w, T_reac) / cea.R
    rsolver.solve(rsoln, w, p_bar, supar=40.0, hc=hc)
    print(f"  converged: {rsoln.converged}  num_pts: {rsoln.num_pts}")
    rocket["equilibrium"] = {
        "num_pts": rsoln.num_pts,
        "T": rsoln.T.tolist(), "P": rsoln.P.tolist(),
        "gamma_s": rsoln.gamma_s.tolist(), "M": rsoln.M.tolist(),
        "MW": rsoln.MW.tolist(), "Mach": rsoln.Mach.tolist(),
        "ae_at": rsoln.ae_at.tolist(), "c_star": rsoln.c_star.tolist(),
        "cf": rsoln.coefficient_of_thrust.tolist(),
        "Isp": rsoln.Isp.tolist(), "Isp_vacuum": rsoln.Isp_vacuum.tolist(),
        "cp_eq": rsoln.cp_eq.tolist(), "cp_fr": rsoln.cp_fr.tolist(),
        "sonic_velocity": rsoln.sonic_velocity.tolist(),
    }
    for k in ("T", "P", "gamma_s", "M", "Mach", "ae_at", "c_star", "cf",
              "Isp", "Isp_vacuum"):
        print(f"    {k:14s} {np.array2string(getattr(rsoln, {'cf': 'coefficient_of_thrust'}.get(k, k)), precision=4)}")
except Exception as exc:
    rocket["equilibrium"] = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", rocket["equilibrium"])

# frozen: n_frz selects the freeze station index
for label, nfrz in (("frozen_at_chamber", 1), ("frozen_at_throat", 2)):
    try:
        rsoln2 = cea.RocketSolution(rsolver)
        rsolver.solve(rsoln2, w, p_bar, supar=40.0, hc=hc, n_frz=nfrz)
        rocket[label] = {
            "num_pts": rsoln2.num_pts, "T": rsoln2.T.tolist(),
            "Isp": rsoln2.Isp.tolist(), "c_star": rsoln2.c_star.tolist(),
            "cf": rsoln2.coefficient_of_thrust.tolist(),
            "gamma_s": rsoln2.gamma_s.tolist(),
            "Mach": rsoln2.Mach.tolist(),
        }
        print(f"  {label}: converged={rsoln2.converged} "
              f"T={np.array2string(rsoln2.T, precision=2)} "
              f"Isp={np.array2string(rsoln2.Isp, precision=3)}")
    except Exception as exc:
        rocket[label] = f"{type(exc).__name__}: {exc}"
        print(f"  {label} FAILED: {rocket[label]}")

OUT["rocket"] = rocket

# ---------------------------------------------------------------------------
section("8. CRYOGENIC LIQUID REACTANTS")
# ---------------------------------------------------------------------------
cryo = {}
try:
    creac = cea.Mixture(["CH4(L)", "O2(L)"])
    cprod = cea.Mixture(["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH",
                         "HO2", "H2O2", "CH4", "C(gr)"])
    csolver = cea.RocketSolver(cprod, reactants=creac)
    csoln = cea.RocketSolution(csolver)
    cw = creac.of_ratio_to_weights(np.array([0.0, 100.0]),
                                   np.array([100.0, 0.0]), of)
    chc = creac.calc_property(cea.ENTHALPY, cw, None) / cea.R
    csolver.solve(csoln, cw, p_bar, supar=40.0, hc=chc)
    cryo["rocket_liquid"] = {
        "converged": csoln.converged, "T": csoln.T.tolist(),
        "Isp": csoln.Isp.tolist(), "c_star": csoln.c_star.tolist(),
        "gamma_s": csoln.gamma_s.tolist(), "M": csoln.M.tolist(),
    }
    print(f"  CH4(L)/O2(L) converged={csoln.converged}")
    print(f"    Tc={csoln.T[0]:.2f} K  c*={csoln.c_star[0]:.2f}  "
          f"Isp={np.array2string(csoln.Isp, precision=2)}")
except Exception as exc:
    cryo["rocket_liquid"] = f"{type(exc).__name__}: {exc}"
    print("  FAILED:", cryo["rocket_liquid"])

# explicit reactant temperature override
try:
    r = cea.Reactant("O2(L)")
    cryo["O2L_default_T"] = r.temperature
    cryo["O2L_valid_range"] = list(r.get_valid_temperature_range())
    print(f"  O2(L) default T={r.temperature} valid={cryo['O2L_valid_range']}")
except Exception as exc:
    cryo["O2L_meta"] = f"{type(exc).__name__}: {exc}"

OUT["cryogenic"] = cryo

# ---------------------------------------------------------------------------
section("9. ERROR BEHAVIOUR")
# ---------------------------------------------------------------------------
errs = {}


def try_case(label, fn):
    try:
        fn()
        errs[label] = "NO ERROR RAISED"
    except Exception as exc:
        errs[label] = f"{type(exc).__name__}: {str(exc)[:160]}"
    print(f"  {label:26s} -> {errs[label]}")


try_case("invalid species", lambda: cea.Mixture(["NOT_A_SPECIES_XYZ"]))
try_case("negative temperature",
         lambda: reac.calc_property(cea.ENTHALPY, weights, -50.0))
try_case("negative pressure",
         lambda: solver.solve(cea.EqSolution(solver), cea.HP, h0, -1.0, weights))
try_case("invalid eq_type",
         lambda: solver.solve(cea.EqSolution(solver), 99999, h0, p_bar, weights))
OUT["errors"] = errs

# ---------------------------------------------------------------------------
section("10. STATE / MUTABILITY / REPEATABILITY")
# ---------------------------------------------------------------------------
rep = []
for _ in range(10):
    s = cea.EqSolution(solver)
    solver.solve(s, cea.HP, h0, p_bar, weights)
    rep.append((s.T, s.gamma_s, s.M))
OUT["repeatability"] = {
    "n": len(rep),
    "unique_T": len(set(r[0] for r in rep)),
    "T_first": rep[0][0], "T_last": rep[-1][0],
    "bitwise_identical": len(set(rep)) == 1,
}
print(f"  10 identical solves bitwise identical: {OUT['repeatability']['bitwise_identical']}")

# A/B/A state leakage
of_b = 2.6
w_b = reac.of_ratio_to_weights(oxid_w, fuel_w, of_b)
h0_b = reac.calc_property(cea.ENTHALPY, w_b, T_reac) / cea.R


def solve_of(h, w):
    s = cea.EqSolution(solver)
    solver.solve(s, cea.HP, h, p_bar, w)
    return s.T


a1 = solve_of(h0, weights)
b1 = solve_of(h0_b, w_b)
a2 = solve_of(h0, weights)
b2 = solve_of(h0_b, w_b)
a3 = solve_of(h0, weights)
OUT["state_leakage"] = {
    "A": [a1, a2, a3], "B": [b1, b2],
    "A_stable": a1 == a2 == a3, "B_stable": b1 == b2,
    "A_differs_from_B": a1 != b1,
}
print(f"  A/B/A/B/A leakage: A_stable={OUT['state_leakage']['A_stable']} "
      f"B_stable={OUT['state_leakage']['B_stable']}")

# mutability of the solution object
try:
    s = cea.EqSolution(solver)
    solver.solve(s, cea.HP, h0, p_bar, weights)
    before = s.T
    s.T = 1.0
    OUT["mutability"] = f"MUTABLE: T changed {before} -> {s.T}"
except Exception as exc:
    OUT["mutability"] = f"read-only property ({type(exc).__name__})"
print(f"  solution.T assignment: {OUT['mutability']}")
print(f"  solver reused across solves: solution object is the mutated carrier")

# ---------------------------------------------------------------------------
with open(sys.argv[1] if len(sys.argv) > 1 else "cea_probe.json", "w") as fh:
    json.dump(OUT, fh, indent=2, default=str)
print()
print("written:", sys.argv[1] if len(sys.argv) > 1 else "cea_probe.json")
