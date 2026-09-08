"""Phase 5B-0 - provider benchmarks.

Experimental. NOT production code.

Fairness rule (spike spec section 50): a CEA full rocket calculation and a
Cantera chamber-only equilibrium are DIFFERENT workloads. Both providers are
therefore benchmarked on a matched chamber-only HP workload, and CEA's rocket
workload is reported separately and labelled.

    <env>\\Scripts\\python.exe benchmark.py <out.json>
"""
import json
import os
import statistics
import subprocess
import sys
import time

import numpy as np

PC_BAR, PC_PA = 100.0, 100.0e5
T_GAS = 298.15
OF = 3.4
PRODUCTS_GAS = ["CO", "CO2", "H", "H2", "H2O", "O", "O2", "OH", "HO2",
                "H2O2", "CH4"]


def median_of(fn, n):
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t)
    return {"median_s": statistics.median(ts), "min_s": min(ts),
            "max_s": max(ts), "n": n}


def rss_mb():
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD),
                        ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]
        c = PMC()
        c.cb = ctypes.sizeof(c)
        ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
        return c.WorkingSetSize / 1e6
    except Exception:
        return None


def import_cost(module):
    """Cold import cost, measured in a fresh subprocess."""
    code = (f"import time;t=time.perf_counter();import {module};"
            f"print(time.perf_counter()-t)")
    ts = []
    for _ in range(5):
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True)
        out = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
        if out:
            try:
                ts.append(float(out[-1]))
            except ValueError:
                pass
    return {"median_s": statistics.median(ts) if ts else None, "samples": ts}


RES = {"python": sys.version.split()[0], "mem_baseline_mb": rss_mb()}

# ---------------------------------------------------------------------------
try:
    import cea
    RES["provider"] = "cea"
    RES["version"] = cea.__version__
    RES["import_cost"] = import_cost("cea")
    RES["mem_after_import_mb"] = rss_mb()

    fuel_w = np.array([100.0, 0.0])
    oxid_w = np.array([0.0, 100.0])

    # --- matched workload: chamber-only HP, gaseous reactants -------------
    reac = cea.Mixture(["CH4", "O2"])
    prod = cea.Mixture(PRODUCTS_GAS)
    solver = cea.EqSolver(prod, reactants=reac)
    w = reac.of_ratio_to_weights(oxid_w, fuel_w, OF)
    h0 = reac.calc_property(cea.ENTHALPY, w, T_GAS) / cea.R

    def chamber_only():
        s = cea.EqSolution(solver)
        solver.solve(s, cea.HP, h0, PC_BAR, w)
        return s.T

    t = time.perf_counter()
    chamber_only()
    RES["first_solve_after_setup_s"] = time.perf_counter() - t
    RES["warm_chamber_only"] = median_of(chamber_only, 200)

    # --- construction cost (solver + mixtures), i.e. per-request setup ----
    def full_setup_and_solve():
        r = cea.Mixture(["CH4", "O2"])
        p = cea.Mixture(PRODUCTS_GAS)
        sv = cea.EqSolver(p, reactants=r)
        ww = r.of_ratio_to_weights(oxid_w, fuel_w, OF)
        hh = r.calc_property(cea.ENTHALPY, ww, T_GAS) / cea.R
        s = cea.EqSolution(sv)
        sv.solve(s, cea.HP, hh, PC_BAR, ww)
        return s.T

    RES["cold_setup_plus_solve"] = median_of(full_setup_and_solve, 50)

    # --- sweeps, matched chamber-only workload ---------------------------
    for n in (100, 1000):
        ofs = np.linspace(2.5, 4.5, n)

        def sweep():
            out = []
            for o in ofs:
                ww = reac.of_ratio_to_weights(oxid_w, fuel_w, float(o))
                hh = reac.calc_property(cea.ENTHALPY, ww, T_GAS) / cea.R
                s = cea.EqSolution(solver)
                solver.solve(s, cea.HP, hh, PC_BAR, ww)
                out.append(s.T)
            return out

        RES[f"sweep_{n}_chamber_only"] = median_of(sweep, 5)
        RES[f"sweep_{n}_chamber_only"]["per_point_ms"] = (
            RES[f"sweep_{n}_chamber_only"]["median_s"] / n * 1e3)

    # --- CEA-ONLY workload: full rocket, labelled separately -------------
    rprod = cea.Mixture(PRODUCTS_GAS + ["C(gr)"])
    rsolver = cea.RocketSolver(rprod, reactants=reac)
    hc = reac.calc_property(cea.ENTHALPY, w, T_GAS) / cea.R

    def rocket_full():
        s = cea.RocketSolution(rsolver)
        rsolver.solve(s, w, PC_BAR, supar=40.0, hc=hc)
        return s.Isp[-1]

    rocket_full()
    RES["warm_rocket_full_CEA_ONLY"] = median_of(rocket_full, 100)
    for n in (100, 1000):
        ofs = np.linspace(2.5, 4.5, n)

        def rsweep():
            out = []
            for o in ofs:
                ww = reac.of_ratio_to_weights(oxid_w, fuel_w, float(o))
                hh = reac.calc_property(cea.ENTHALPY, ww, T_GAS) / cea.R
                s = cea.RocketSolution(rsolver)
                rsolver.solve(s, ww, PC_BAR, supar=40.0, hc=hh)
                out.append(s.Isp[-1])
            return out

        RES[f"sweep_{n}_rocket_full_CEA_ONLY"] = median_of(rsweep, 3)
        RES[f"sweep_{n}_rocket_full_CEA_ONLY"]["per_point_ms"] = (
            RES[f"sweep_{n}_rocket_full_CEA_ONLY"]["median_s"] / n * 1e3)
        if n == 1000:
            RES["mem_after_1000_sweep_mb"] = rss_mb()

except ImportError:
    import cantera as ct
    RES["provider"] = "cantera"
    RES["version"] = ct.__version__
    RES["import_cost"] = import_cost("cantera")
    RES["mem_after_import_mb"] = rss_mb()

    allsp = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
    chosen = [allsp[n] for n in PRODUCTS_GAS if n in allsp]
    RES["species_list_load_s"] = None
    t = time.perf_counter()
    _ = ct.Species.list_from_file("nasa_gas.yaml")
    RES["species_list_load_s"] = time.perf_counter() - t

    gas = ct.Solution(thermo="ideal-gas", species=chosen)
    yf, yo = 1.0 / (1.0 + OF), OF / (1.0 + OF)

    def chamber_only():
        gas.TPY = T_GAS, PC_PA, f"CH4:{yf}, O2:{yo}"
        gas.equilibrate("HP")
        return gas.T

    t = time.perf_counter()
    chamber_only()
    RES["first_solve_after_setup_s"] = time.perf_counter() - t
    RES["warm_chamber_only"] = median_of(chamber_only, 200)

    def full_setup_and_solve():
        g = ct.Solution(thermo="ideal-gas", species=chosen)
        g.TPY = T_GAS, PC_PA, f"CH4:{yf}, O2:{yo}"
        g.equilibrate("HP")
        return g.T

    RES["cold_setup_plus_solve"] = median_of(full_setup_and_solve, 50)

    # object construction alone, the cost an adapter would pay per request
    RES["solution_construction"] = median_of(
        lambda: ct.Solution(thermo="ideal-gas", species=chosen), 50)

    for n in (100, 1000):
        ofs = np.linspace(2.5, 4.5, n)

        def sweep():
            out = []
            for o in ofs:
                f = 1.0 / (1.0 + float(o))
                x = float(o) / (1.0 + float(o))
                gas.TPY = T_GAS, PC_PA, f"CH4:{f}, O2:{x}"
                gas.equilibrate("HP")
                out.append(gas.T)
            return out

        RES[f"sweep_{n}_chamber_only"] = median_of(sweep, 5)
        RES[f"sweep_{n}_chamber_only"]["per_point_ms"] = (
            RES[f"sweep_{n}_chamber_only"]["median_s"] / n * 1e3)
        if n == 1000:
            RES["mem_after_1000_sweep_mb"] = rss_mb()

out = sys.argv[1] if len(sys.argv) > 1 else "benchmark.json"
with open(out, "w") as fh:
    json.dump(RES, fh, indent=2, default=str)

print(f"provider: {RES['provider']} {RES['version']}")
print(f"  cold import (subprocess median): {RES['import_cost']['median_s']*1e3:.1f} ms")
print(f"  first solve after setup:         {RES['first_solve_after_setup_s']*1e3:.3f} ms")
print(f"  warm chamber-only solve:         {RES['warm_chamber_only']['median_s']*1e6:.1f} us")
print(f"  cold setup + solve:              {RES['cold_setup_plus_solve']['median_s']*1e3:.3f} ms")
for k in sorted(RES):
    if k.startswith("sweep_"):
        print(f"  {k:34s} {RES[k]['median_s']*1e3:9.2f} ms  "
              f"({RES[k]['per_point_ms']:.4f} ms/point)")
if "warm_rocket_full_CEA_ONLY" in RES:
    print(f"  warm rocket full (CEA only):     "
          f"{RES['warm_rocket_full_CEA_ONLY']['median_s']*1e6:.1f} us")
print(f"  memory: baseline {RES['mem_baseline_mb']:.1f} MB -> "
      f"import {RES['mem_after_import_mb']:.1f} MB -> "
      f"after 1000 sweep {RES.get('mem_after_1000_sweep_mb', float('nan')):.1f} MB")
print("written:", out)
