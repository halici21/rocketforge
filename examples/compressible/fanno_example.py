"""Fanno flow: adiabatic duct friction, its choking length, and both conventions.

The duct group is 4 f_Fanning L/D. Public API only, no Qt.

Run from the project root, so that the package is importable:

    .venv\Scripts\python.exe -m examples.compressible.fanno_example

"""

from rocketforge.physics.compressible import FlowBranch, PerfectGas, fanno


def main() -> None:
    air = PerfectGas(gamma=1.4, gas_constant=287.05)

    print("Fanno state at M = 0.5, gamma = 1.4")
    state = fanno.state(0.5, air)
    print(f"  T/T*        {state.temperature_ratio:.10f}")
    print(f"  p/p*        {state.pressure_ratio:.10f}")
    print(f"  p0/p0*      {state.stagnation_pressure_ratio:.10f}")
    print(f"  V/V*        {state.velocity_ratio:.10f}")
    print(f"  4 f_F L*/D  {state.friction_parameter:.10f}  (duct left before choking)")

    print()
    print("The supersonic branch is bounded; the subsonic one is not:")
    print("  4 f_F L*/D limit as M -> infinity: "
          f"{fanno.friction_parameter_limit(air):.10f}")
    for mach in (0.1, 0.5, 1.0, 2.0, 5.0):
        print(f"  M = {mach:4.1f}  4 f_F L*/D = "
              f"{float(fanno.friction_parameter(mach, air)):.10f}")

    print()
    print("Both friction conventions describe the same wall:")
    fanning = 0.005
    darcy = fanno.fanning_to_darcy(fanning)
    print(f"  f_Fanning = {fanning}  <->  f_Darcy = {darcy}  (f_D = 4 f_F)")
    length, diameter = 5.0, 0.1
    group = fanno.duct_parameter_from_geometry(fanning, length, diameter)
    print(f"  L = {length} m, D_h = {diameter} m  ->  4 f_F L/D = {group}")

    print()
    print("A real duct: M1 = 0.3 through that geometry")
    result = fanno.downstream_mach(0.3, group, air).unwrap()
    print(f"  M2                   {result.downstream.mach:.10f}")
    print(f"  p2/p1                {result.pressure_ratio_12:.10f}")
    print(f"  p02/p01              {result.stagnation_pressure_ratio_12:.10f}")
    print(f"  duct left to choking {result.remaining_to_choking:.10f}")

    print()
    print("Ask for more duct than the flow can sustain and it says so:")
    over = fanno.downstream_mach(0.3, 10.0, air)
    print(f"  status {over.status.value}")
    for diagnostic in over.diagnostics:
        print(f"  [{diagnostic.code}] {diagnostic.message[:70]}...")

    print()
    print("The inverse needs a branch, because both branches reach M = 1:")
    for branch in (FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC):
        mach = fanno.mach_from_friction_parameter(0.3, air, branch).unwrap()
        print(f"  4 f_F L*/D = 0.3 on {branch.value:<10} -> M = {mach:.10f}")


if __name__ == "__main__":
    main()
