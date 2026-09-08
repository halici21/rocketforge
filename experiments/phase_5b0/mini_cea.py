"""Phase 5B-0 minimal frozen-executable probe - NASA CEA. Experimental."""
import sys
import numpy as np
import cea

def main():
    reac = cea.Mixture(["CH4(L)", "O2(L)"])
    prod = cea.Mixture(["CO","CO2","H","H2","H2O","O","O2","OH","HO2","H2O2","CH4","C(gr)"])
    solver = cea.RocketSolver(prod, reactants=reac)
    soln = cea.RocketSolution(solver)
    w = reac.of_ratio_to_weights(np.array([0.,100.]), np.array([100.,0.]), 3.4)
    hc = reac.calc_property(cea.ENTHALPY, w, [111.643, 90.170]) / cea.R
    solver.solve(soln, w, 100.0, supar=40.0, hc=hc)
    print("FROZEN_EXE_PROBE provider=cea")
    print(f"  cea_version={cea.__version__} lib={cea.lib_version()}")
    print(f"  frozen={getattr(sys,'frozen',False)} meipass={getattr(sys,'_MEIPASS','-')}")
    print(f"  converged={soln.converged}")
    print(f"  Tc_K={soln.T[0]:.4f}")
    print(f"  cstar_m_per_s={soln.c_star[0]:.4f}")
    print(f"  gamma_s={soln.gamma_s[0]:.6f}")
    print(f"  M_kg_per_kmol={soln.M[0]:.6f}")
    print(f"  Isp_exit_m_per_s={soln.Isp[-1]:.4f}")
    assert soln.converged, "did not converge"
    return 0

if __name__ == "__main__":
    sys.exit(main())
