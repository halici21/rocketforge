"""Rayleigh flow: heat exchange, thermal choking, and two different maxima.

Public API only, no Qt.

Run from the project root, so that the package is importable:

    .venv\Scripts\python.exe -m examples.compressible.rayleigh_example

"""

from rocketforge.physics.compressible import FlowBranch, PerfectGas, rayleigh


def main() -> None:
    air = PerfectGas(gamma=1.4, gas_constant=287.05)

    print("Rayleigh state at M = 0.5, gamma = 1.4")
    state = rayleigh.state(0.5, air)
    print(f"  T/T*    {state.temperature_ratio:.10f}")
    print(f"  p/p*    {state.pressure_ratio:.10f}")
    print(f"  T0/T0*  {state.stagnation_temperature_ratio:.10f}")
    print(f"  p0/p0*  {state.stagnation_pressure_ratio:.10f}")

    print()
    print("Two maxima, at two different Mach numbers -- this is the trap:")
    peak = rayleigh.mach_at_maximum_temperature(air)
    print(f"  static T is greatest at M = 1/sqrt(gamma) = {peak:.10f}")
    print(f"    with T/T* = {rayleigh.maximum_temperature_ratio(air):.10f}")
    print("  stagnation T is greatest at M = 1 exactly, with T0/T0* = 1")
    print("  Between them the static temperature FALLS while heat is still added.")

    print()
    print("Heating a subsonic flow: M1 = 0.2 with T02/T01 = 2")
    result = rayleigh.heat_addition(0.2, 2.0, air).unwrap()
    print(f"  M2      {result.downstream.mach:.10f}")
    print(f"  p2/p1   {result.pressure_ratio_12:.10f}")
    print(f"  T2/T1   {result.temperature_ratio_12:.10f}")
    print(f"  p02/p01 {result.stagnation_pressure_ratio_12:.10f}  (the Rayleigh loss)")

    print()
    print("In dimensional terms, for that same heating:")
    heat = rayleigh.specific_heat_addition(0.2, 2.0, air, 300.0)
    print(f"  T01 = 300 K  ->  q = {float(heat):,.1f} J/kg")

    print()
    print("More heat than the flow can absorb has no solution on the same line:")
    over = rayleigh.heat_addition(0.2, 10.0, air)
    print(f"  status {over.status.value}")
    for diagnostic in over.diagnostics:
        print(f"  [{diagnostic.code}] {diagnostic.message[:70]}...")

    print()
    print("The T0/T0* inverse needs a branch. The T/T* inverse is not offered")
    print("at all, because T/T* is not monotone on the subsonic branch.")
    for branch in (FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC):
        mach = rayleigh.mach_from_stagnation_temperature_ratio(
            0.85, air, branch).unwrap()
        print(f"  T0/T0* = 0.85 on {branch.value:<10} -> M = {mach:.10f}")


if __name__ == "__main__":
    main()
