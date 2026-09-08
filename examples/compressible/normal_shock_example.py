"""The normal shock: the jump, what it costs, and the inverse.

Public API only, no Qt.

Run from the project root, so that the package is importable:

    .venv\Scripts\python.exe -m examples.compressible.normal_shock_example

"""

from rocketforge.physics.compressible import PerfectGas, normal_shock


def main() -> None:
    air = PerfectGas(gamma=1.4, gas_constant=287.05)

    print("Normal shock at M1 = 2, gamma = 1.4")
    shock = normal_shock.solve(2.0, air)
    print(f"  M2        {shock.mach2:.10f}")
    print(f"  p2/p1     {shock.pressure_ratio:.10f}")
    print(f"  rho2/rho1 {shock.density_ratio:.10f}")
    print(f"  T2/T1     {shock.temperature_ratio:.10f}")
    print(f"  p02/p01   {shock.stagnation_pressure_ratio:.10f}")
    print(f"  p02/p1    {shock.stagnation_pressure_over_upstream_static:.10f}")
    print(f"  T02/T01   {shock.stagnation_temperature_ratio:.1f}  (adiabatic, exactly 1)")
    print(f"  ds/R      {shock.entropy_change:.10f}  (>= 0, the second law)")
    print(f"  A2*/A1*   {shock.area_star_ratio:.10f}")

    print()
    print("Stronger shocks lose more stagnation pressure:")
    for mach in (1.0, 1.5, 2.0, 3.0, 5.0, 10.0):
        result = normal_shock.solve(mach, air)
        print(f"  M1 = {mach:5.1f}  M2 = {result.mach2:.6f}"
              f"  p02/p01 = {result.stagnation_pressure_ratio:.6f}")

    print()
    print("And the limits as M1 -> infinity:")
    print(f"  M2 floor        {normal_shock.mach_downstream_limit(air):.10f}")
    print(f"  density ceiling {normal_shock.density_ratio_limit(air):.10f}")

    print()
    print("Inverses: from a measured pressure ratio back to the upstream Mach")
    upstream = normal_shock.mach_upstream_from_pressure_ratio(4.5, air)
    print(f"  p2/p1 = 4.5 -> M1 = {float(upstream):.10f}")


if __name__ == "__main__":
    main()
