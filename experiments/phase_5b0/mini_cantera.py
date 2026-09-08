"""Phase 5B-0 minimal frozen-executable probe - Cantera. Experimental."""
import sys
import numpy as np
import cantera as ct

def main():
    allsp = {s.name: s for s in ct.Species.list_from_file("nasa_gas.yaml")}
    names = ["CO","CO2","H","H2","H2O","O","O2","OH","HO2","H2O2","CH4"]
    gas = ct.Solution(thermo="ideal-gas", species=[allsp[n] for n in names if n in allsp])
    of = 3.4
    gas.TPY = 298.15, 1.0e7, f"CH4:{1/(1+of)}, O2:{of/(1+of)}"
    gas.equilibrate("HP")
    print("FROZEN_EXE_PROBE provider=cantera")
    print(f"  cantera_version={ct.__version__}")
    print(f"  frozen={getattr(sys,'frozen',False)} meipass={getattr(sys,'_MEIPASS','-')}")
    print(f"  data_dirs={ct.get_data_directories()}")
    print(f"  Tc_K={gas.T:.4f}")
    print(f"  M_kg_per_kmol={gas.mean_molecular_weight:.6f}")
    print(f"  gamma_frozen={gas.cp_mass/gas.cv_mass:.6f}")
    print(f"  sound_speed={gas.sound_speed:.4f}")
    print(f"  n_species={gas.n_species}")
    assert gas.T > 3000.0, "implausible chamber temperature"
    return 0

if __name__ == "__main__":
    sys.exit(main())
