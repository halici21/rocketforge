"""Isentropic flow: the ratios, the two area-Mach roots, and a small table.

Public API only, no Qt.

Run from the project root, so that the package is importable:

    .venv\Scripts\python.exe -m examples.compressible.isentropic_example

"""

from rocketforge.physics.compressible import FlowBranch, PerfectGas, isentropic


def main() -> None:
    air = PerfectGas(gamma=1.4, gas_constant=287.05)

    print("Isentropic relations at M = 2, gamma = 1.4")
    ratios = isentropic.ratios_from_mach(2.0, air)
    print(f"  T/T0     {ratios.temperature_ratio:.6f}")
    print(f"  p/p0     {ratios.pressure_ratio:.6f}")
    print(f"  rho/rho0 {ratios.density_ratio:.6f}")
    print(f"  A/A*     {float(isentropic.area_ratio(2.0, air)):.6f}")
    print(f"  mu       {float(isentropic.mach_angle(2.0)):.6f} rad")

    print()
    print("The area relation has two roots, and the caller chooses which:")
    for branch in (FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC):
        mach = isentropic.mach_from_area_ratio(2.0, air, branch).unwrap()
        print(f"  A/A* = 2 on the {branch.value:<10} branch -> M = {mach:.10f}")

    print()
    print("A short table, computed rather than looked up:")
    print(f"  {'M':>6} {'T/T0':>10} {'p/p0':>12} {'A/A*':>10}")
    for mach in (0.5, 1.0, 1.5, 2.0, 3.0):
        print(f"  {mach:6.2f} {float(isentropic.temperature_ratio(mach, air)):10.6f}"
              f" {float(isentropic.pressure_ratio(mach, air)):12.6f}"
              f" {float(isentropic.area_ratio(mach, air)):10.6f}")

    print()
    print("Any gas, not just air -- combustion products at gamma = 1.22:")
    products = PerfectGas(gamma=1.22, gas_constant=320.0)
    exit_mach = isentropic.mach_from_area_ratio(
        12.4, products, FlowBranch.SUPERSONIC).unwrap()
    print(f"  A_e/A* = 12.4 -> M_e = {exit_mach:.6f}")


if __name__ == "__main__":
    main()
