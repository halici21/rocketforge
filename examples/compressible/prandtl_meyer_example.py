"""Prandtl-Meyer: the function, its maximum, and an expansion turn.

Angles are radians below the application layer. Public API only, no Qt.

Run from the project root, so that the package is importable:

    .venv\Scripts\python.exe -m examples.compressible.prandtl_meyer_example

"""

import math

from rocketforge.physics.compressible import PerfectGas, prandtl_meyer


def main() -> None:
    air = PerfectGas(gamma=1.4, gas_constant=287.05)

    print("The Prandtl-Meyer function, gamma = 1.4")
    for mach in (1.0, 1.5, 2.0, 3.0, 5.0):
        angle = float(prandtl_meyer.nu(mach, air))
        print(f"  M = {mach:4.1f}  nu = {angle:.10f} rad = {math.degrees(angle):8.4f} deg")

    maximum = prandtl_meyer.nu_max(air)
    print(f"  nu_max = {maximum:.10f} rad = {math.degrees(maximum):.6f} deg"
          "  (the limit as M -> infinity)")

    print()
    print("A 10 degree expansion from M = 2:")
    result = prandtl_meyer.expand(2.0, math.radians(10.0), air).unwrap()
    print(f"  M2         {result.mach2:.10f}")
    print(f"  nu1 -> nu2 {result.nu1:.6f} -> {result.nu2:.6f} rad")
    print(f"  p2/p1      {result.pressure_ratio:.10f}")
    print(f"  T2/T1      {result.temperature_ratio:.10f}")
    print(f"  fan angle  {result.fan_angle:.10f} rad")

    print()
    print("Compression is the same relation with the turn reversed:")
    back = prandtl_meyer.compress(result.mach2, math.radians(10.0), air).unwrap()
    print(f"  M back to {back.mach2:.10f}  (started at 2.0)")

    print()
    print("Turning further than nu_max has no solution, and the module says so:")
    beyond = prandtl_meyer.expand(2.0, maximum, air)
    print(f"  status {beyond.status.value}")
    for diagnostic in beyond.diagnostics:
        print(f"  [{diagnostic.code}] {diagnostic.message[:70]}...")


if __name__ == "__main__":
    main()
