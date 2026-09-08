"""The oblique shock: both roots, the detachment limit, the normal shock inside.

Angles are radians below the application layer. Public API only, no Qt.

Run from the project root, so that the package is importable:

    .venv\Scripts\python.exe -m examples.compressible.oblique_shock_example

"""

import math

from rocketforge.physics.compressible import (
    PerfectGas,
    ShockBranch,
    normal_shock,
    oblique_shock,
)


def main() -> None:
    air = PerfectGas(gamma=1.4, gas_constant=287.05)
    mach1, theta = 3.0, math.radians(20.0)

    print("M1 = 3 turned through 20 degrees: two shocks satisfy that turn")
    pair = oblique_shock.solve_both(mach1, theta, air).unwrap()
    for label, result in (("weak", pair.weak), ("strong", pair.strong)):
        print(f"  {label:<7} beta = {math.degrees(result.beta):7.4f} deg"
              f"  M2 = {result.mach2:.6f}"
              f"  p2/p1 = {result.pressure_ratio:8.6f}"
              f"  p02/p01 = {result.stagnation_pressure_ratio:.6f}")

    print()
    print("An oblique shock IS a normal shock, at the normal component:")
    weak = pair.weak
    print(f"  Mn1 = M1 sin(beta) = {weak.mach_normal1:.10f}")
    independent = normal_shock.solve(weak.mach_normal1, air)
    print(f"  normal_shock.solve(Mn1).p2/p1 = {independent.pressure_ratio:.10f}")
    print(f"  the oblique result's  p2/p1   = {weak.pressure_ratio:.10f}")
    print(f"  identical: {independent.pressure_ratio == weak.pressure_ratio}")

    print()
    limit = oblique_shock.theta_max(mach1, air).unwrap()
    print("The maximum attached turn at M1 = 3 is "
          f"{math.degrees(limit.theta_max):.6f} deg")
    print("Beyond it no attached solution exists, and none is invented:")
    detached = oblique_shock.solve(mach1, limit.theta_max * 1.05, air, ShockBranch.WEAK)
    print(f"  status {detached.status.value}")
    for diagnostic in detached.diagnostics:
        print(f"  [{diagnostic.code}] {diagnostic.message[:70]}...")


if __name__ == "__main__":
    main()
