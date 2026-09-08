"""Phase 5B-0 - merge the two common-case JSONs into a comparison CSV."""
import csv, json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2])); out = sys.argv[3]
FIELDS = [("Tc_K","Chamber temperature","K"),("M_kg_per_kmol","Mean molar mass","kg/kmol"),
          ("R_specific_J_per_kgK","Specific gas constant (CODATA 2019 / Mbar)","J/(kg K)"),
          ("density_kg_per_m3","Density","kg/m3"),
          ("gamma_s_equilibrium","Equilibrium isentropic exponent","-"),
          ("gamma_frozen_cp_over_cv","Frozen cp/cv","-"),
          ("cp_frozen_J_per_kgK","Frozen cp","J/(kg K)"),
          ("cp_equilibrium_J_per_kgK","Equilibrium cp","J/(kg K)"),
          ("cv_frozen_J_per_kgK","Frozen cv","J/(kg K)"),
          ("entropy_J_per_kgK","Entropy","J/(kg K)"),
          ("sum_X","Sum of mole fractions","-"),
          ("gas_constant_used_by_provider","Universal gas constant used","J/(kmol K)")]
rows=[]
def num(v):
    try: return float(v)
    except (TypeError, ValueError): return None
for key,label,unit in FIELDS:
    va, vb = num(a.get(key)), num(b.get(key))
    rel = ""
    if va is not None and vb is not None and abs(va) > 1e-30:
        rel = f"{abs(vb-va)/abs(va):.6e}"
    rows.append({"quantity":label,"key":key,"unit":unit,
                 "cea":"" if va is None else f"{va:.10g}",
                 "cantera":"" if vb is None else f"{vb:.10g}",
                 "abs_diff":"" if (va is None or vb is None) else f"{vb-va:.6e}",
                 "rel_diff":rel,
                 "note":("Cantera: not native" if vb is None else
                         ("Cantera: finite-difference, not native" if key=="gamma_s_equilibrium" else ""))})
species=sorted(set(a["X"])|set(b["X"]), key=lambda s:-max(num(a["X"].get(s,0)) or 0, num(b["X"].get(s,0)) or 0))
for s in species:
    xa, xb = num(a["X"].get(s,0.0)) or 0.0, num(b["X"].get(s,0.0)) or 0.0
    rel = f"{abs(xb-xa)/abs(xa):.6e}" if abs(xa)>1e-14 else ""
    rows.append({"quantity":f"mole fraction {s}","key":f"X[{s}]","unit":"-",
                 "cea":f"{xa:.10g}","cantera":f"{xb:.10g}",
                 "abs_diff":f"{xb-xa:.6e}","rel_diff":rel,"note":""})
with open(out,"w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=["quantity","key","unit","cea","cantera","abs_diff","rel_diff","note"])
    w.writeheader(); w.writerows(rows)
print(f"{'quantity':<44}{'CEA':>16}{'Cantera':>16}{'rel diff':>13}")
for r in rows:
    print(f"  {r['quantity']:<42}{r['cea']:>16}{r['cantera']:>16}{r['rel_diff']:>13}")
print("\nwritten:", out)
