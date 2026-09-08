"""A converging-diverging nozzle across its whole back-pressure range.

Public API only, no Qt. This is the module that composes all the others.

Run from the project root, so that the package is importable:

    .venv\Scripts\python.exe -m examples.compressible.cd_nozzle_example

"""

import numpy as np

from rocketforge.physics.compressible import (
    AreaDistribution,
    NozzleOperating,
    PerfectGas,
    nozzle,
)


def main() -> None:
    air = PerfectGas(gamma=1.4, gas_constant=287.05)
    area_ratio = 2.0
    p0, t0 = 1.0e6, 3000.0

    print("A nozzle with A_e/A_t = 2, gamma = 1.4, has three thresholds:")
    critical = nozzle.critical_pressure_ratios(area_ratio, air).unwrap()
    print(f"  choking onset    p_b/p0 = {critical.first_critical:.10f}")
    print(f"  shock at exit    p_b/p0 = {critical.second_critical:.10f}")
    print(f"  ideal expansion  p_b/p0 = {critical.third_critical:.10f}")
    print(f"  exit Mach, subsonic branch   {critical.mach_exit_subsonic:.10f}")
    print(f"  exit Mach, supersonic branch {critical.mach_exit_supersonic:.10f}")

    print()
    print("Every regime, classified from those thresholds alone:")
    cases = [
        ("just below the reservoir", 0.98),
        ("choking onset", critical.first_critical),
        ("a shock inside the nozzle", 0.70),
        ("the shock at the exit", critical.second_critical),
        ("overexpanded", 0.30),
        ("ideal expansion", critical.third_critical),
        ("underexpanded", 0.03),
    ]
    for _label, back in cases:
        result = nozzle.classify(area_ratio, back, air).unwrap()
        shock = ("" if result.shock is None
                 else f"  shock at A_s/A_t = {result.shock.area_ratio_shock:.6f}")
        print(f"  p_b/p0 = {back:.6f}  {result.regime.value:<22}"
              f" M_e = {result.mach_exit:.6f}{shock}")

    print()
    print("The distributed solution needs a contour, which the caller supplies:")
    geometry = AreaDistribution.conical(throat_area=0.01, area_ratio=area_ratio, n=81)
    solution = nozzle.solve(geometry, NozzleOperating(p0, 0.70 * p0, t0), air).unwrap()
    print(f"  regime     {solution.regime.value}")
    print(f"  mass flow  {solution.mass_flow:.6f} kg/s")
    print(f"  throat M   {solution.throat.mach:.6f}")
    print(f"  exit M     {solution.exit.mach:.6f}")
    print(f"  stations   {solution.mach.size}"
          "  (the shock station appears twice, at the same x)")

    index = solution.shock_index
    print()
    print(f"Across the shock, at x = {solution.x[index]:.6f} m:")
    print(f"  M   {solution.mach[index]:.6f} -> {solution.mach[index + 1]:.6f}")
    print(f"  p   {solution.pressure[index]:,.1f} -> "
          f"{solution.pressure[index + 1]:,.1f} Pa")
    print(f"  T   {solution.temperature[index]:,.1f} -> "
          f"{solution.temperature[index + 1]:,.1f} K")
    print(f"  p0  {solution.stagnation_pressure[index]:,.1f} -> "
          f"{solution.stagnation_pressure[index + 1]:,.1f} Pa")

    print()
    print("What is conserved, checked on the arrays the solver returned:")
    local = solution.density * solution.area * solution.velocity
    total = solution.temperature + solution.velocity ** 2 / (2.0 * air.cp)
    levels = np.unique(np.round(solution.stagnation_pressure, 6)).size
    print(f"  mass flow spread  {np.ptp(local) / local.mean():.2e}  (should be ~0)")
    print(f"  T0 spread         {np.ptp(total):.2e} K  (adiabatic)")
    print(f"  p0 levels         {levels}  (one before the shock, one after)")


if __name__ == "__main__":
    main()
