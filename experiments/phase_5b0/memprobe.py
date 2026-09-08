"""Phase 5B-0 - order-of-magnitude process memory. Experimental, not production."""
import ctypes, json, sys
from ctypes import wintypes

class PMC(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_k32.GetCurrentProcess.restype = wintypes.HANDLE
_k32.K32GetProcessMemoryInfo.restype = wintypes.BOOL
_k32.K32GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]

def rss():
    c = PMC(); c.cb = ctypes.sizeof(c)
    ok = _k32.K32GetProcessMemoryInfo(_k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
    if not ok:
        return None
    return c.WorkingSetSize / 1e6

import numpy as np
R = {"baseline_mb": rss()}
try:
    import cea
    R["provider"] = "cea"; R["after_import_mb"] = rss()
    reac = cea.Mixture(["CH4","O2"]); prod = cea.Mixture(["CO","CO2","H","H2","H2O","O","O2","OH","HO2","H2O2","CH4"])
    sv = cea.EqSolver(prod, reactants=reac); R["after_setup_mb"] = rss()
    fw, ow = np.array([100.,0.]), np.array([0.,100.])
    for o in np.linspace(2.5,4.5,1000):
        w = reac.of_ratio_to_weights(ow, fw, float(o))
        h = reac.calc_property(cea.ENTHALPY, w, 298.15)/cea.R
        s = cea.EqSolution(sv); sv.solve(s, cea.HP, h, 100.0, w); s.T
    R["after_1000_sweep_mb"] = rss()
except ImportError:
    import cantera as ct
    R["provider"] = "cantera"; R["after_import_mb"] = rss()
    allsp = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
    chosen = [allsp[n] for n in ["CO","CO2","H","H2","H2O","O","O2","OH","HO2","H2O2","CH4"] if n in allsp]
    g = ct.Solution(thermo="ideal-gas", species=chosen); R["after_setup_mb"] = rss()
    for o in np.linspace(2.5,4.5,1000):
        g.TPY = 298.15, 1e7, f"CH4:{1/(1+o)}, O2:{o/(1+o)}"; g.equilibrate("HP"); g.T
    R["after_1000_sweep_mb"] = rss()
print(json.dumps(R, indent=2))
open(sys.argv[1],"w").write(json.dumps(R, indent=2))
