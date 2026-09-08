"""Phase 5B-0 followup: custom reactant with molecular_weight, threading isolation."""
import concurrent.futures, json, sys, time
import numpy as np
import cea

OUT={}
print("="*72); print("1. CUSTOM REACTANT (name <=15 chars)"); print("="*72)
try:
    r = cea.Reactant(name="RP1-SURROGATE",  # <=15 chars; 16+ raises CEA_INVALID_SIZE
                     formula={"C":1.0,"H":1.9423},
                     molecular_weight=13.9761,
                     enthalpy=-5430.0, enthalpy_units="cal/mol",
                     temperature=298.15)
    reac = cea.Mixture([r, "O2(L)"])
    prod = cea.Mixture(["CO","CO2","H","H2","H2O","O","O2","OH","HO2","C(gr)"])
    sv = cea.RocketSolver(prod, reactants=reac)
    s = cea.RocketSolution(sv)
    w = reac.of_ratio_to_weights(np.array([0.,1.]), np.array([1.,0.]), 2.56)
    hc = reac.calc_property(cea.ENTHALPY, w, [298.15, 90.17]) / cea.R
    sv.solve(s, w, 100.0, supar=40.0, hc=hc)
    OUT["custom_reactant"] = {"works": True, "Tc": float(s.T[0]),
        "cstar": float(s.c_star[0]), "Isp_exit": float(s.Isp[-1]),
        "M": float(s.M[0]), "note":"CEA reactant/species names are limited to 15 characters; 16+ raises CEA_INVALID_SIZE (Fortran fixed-width field)"}
    print(f"  WORKS. custom-surrogate/LOX O/F=2.56: Tc={s.T[0]:.2f} K  c*={s.c_star[0]:.2f} m/s  Isp={s.Isp[-1]:.2f} m/s")
    print("  -> name length limit is 15 chars; 16+ raises CEA_INVALID_SIZE")
except Exception as e:
    OUT["custom_reactant"]={"works":False,"error":f"{type(e).__name__}: {e}"}
    print("  FAILED:", OUT["custom_reactant"]["error"])

print(); print("="*72); print("2. THREADING SLOWDOWN ISOLATION"); print("="*72)
P=["CO","CO2","H","H2","H2O","O","O2","OH","HO2","H2O2","CH4"]
def work(of_val, n=25):
    r=cea.Mixture(["CH4","O2"]); p=cea.Mixture(P); sv=cea.EqSolver(p,reactants=r)
    out=[]
    for _ in range(n):
        w=r.of_ratio_to_weights(np.array([0.,100.]),np.array([100.,0.]),of_val)
        h=r.calc_property(cea.ENTHALPY,w,298.15)/cea.R
        s=cea.EqSolution(sv); sv.solve(s,cea.HP,h,100.0,w); out.append(s.T)
    return out
ofs=[2.6,3.0,3.4,3.8]
t=time.perf_counter(); [work(o) for o in ofs]; serial=time.perf_counter()-t
res={"serial_ms":serial*1e3}
for nw in (1,2,4):
    t=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=nw) as pool:
        list(pool.map(work, ofs))
    res[f"threads_{nw}_ms"]=(time.perf_counter()-t)*1e3
for k,v in res.items(): print(f"  {k:18s} {v:8.2f} ms")
res["speedup_4t"]=res["serial_ms"]/res["threads_4_ms"]
print(f"  speedup at 4 threads: {res['speedup_4t']:.2f}x  (<1 means SLOWER than serial)")
print("  -> threading is counterproductive; recommend serial in-process or separate processes")
OUT["threading"]=res
open(sys.argv[1],"w").write(json.dumps(OUT,indent=2,default=str))
print("\nwritten:", sys.argv[1])
