"""Compressible mass flow: the parameter, the choked limit, and a real passage.

Public API only, no Qt.

Run from the project root, so that the package is importable:

    .venv\Scripts\python.exe -m examples.compressible.mass_flow_example

"""

from rocketforge.physics.compressible import FlowBranch, PerfectGas, mass_flow


def main() -> None:
    air = PerfectGas(gamma=1.4, gas_constant=287.05)
    area, p0, t0 = 0.01, 1.0e6, 3000.0

    print("A 0.01 m^2 throat at p0 = 1 MPa, T0 = 3000 K")
    choked = mass_flow.choked_mass_flow(air, area, p0, t0)
    print(f"  choked mass flow  {choked:.6f} kg/s")
    print(f"  choked mass flux  {mass_flow.choked_mass_flux(air, p0, t0):.4f} kg/(s m^2)")
    print(f"  Gamma(gamma)      {mass_flow.choked_mass_flow_coefficient(air):.10f}")

    print()
    print("The same passage below the choking condition:")
    for mach in (0.2, 0.5, 0.8, 1.0):
        flow = float(mass_flow.mass_flow(mach, air, area, p0, t0))
        print(f"  M = {mach:4.2f}  mdot = {flow:9.6f} kg/s"
              f"  ({flow / choked * 100:5.1f}% of choked)")

    print()
    print("Choking is decided by the pressure ratio, not by assumption:")
    critical = mass_flow.critical_pressure_ratio(air)
    print(f"  p*/p0 = {critical:.10f}")
    for ratio in (0.9, critical, 0.2):
        print(f"  p/p0 = {ratio:.6f} -> choked: {mass_flow.is_choked(ratio, air)}")

    print()
    print("The inverse needs a branch, because a mass-flow ratio has two roots:")
    for branch in (FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC):
        mach = mass_flow.mach_from_mass_flow_ratio(0.6, air, branch).unwrap()
        print(f"  mdot/mdot_choked = 0.6 on {branch.value:<10} -> M = {mach:.10f}")


if __name__ == "__main__":
    main()
