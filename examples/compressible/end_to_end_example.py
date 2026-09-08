"""One script, five modules, no Qt: gas -> isentropic -> mass flow -> shock -> nozzle.

The point of this file is that a user can do real work with the public API
alone, from a plain Python prompt or a notebook, with no interface running.

Run from the project root, so that the package is importable:

    .venv\Scripts\python.exe -m examples.compressible.end_to_end_example

"""

from rocketforge.physics.compressible import (
    AreaDistribution,
    FlowBranch,
    NozzleOperating,
    PerfectGas,
    isentropic,
    mass_flow,
    normal_shock,
    nozzle,
)


def main() -> None:
    # 1. State the gas. Nothing is assumed about it.
    products = PerfectGas(gamma=1.22, gas_constant=320.0)
    print(f"Gas: gamma = {products.gamma}, R = {products.gas_constant} J/(kg K)")
    print(f"     cp = {products.cp:.2f}, cv = {products.cv:.2f} J/(kg K)")

    # 2. Isentropic: where does a given area ratio put the exit?
    area_ratio = 12.4
    exit_mach = isentropic.mach_from_area_ratio(
        area_ratio, products, FlowBranch.SUPERSONIC).unwrap()
    print()
    print(f"A_e/A* = {area_ratio} -> M_e = {exit_mach:.6f}")
    print(f"     p_e/p0 = {float(isentropic.pressure_ratio(exit_mach, products)):.8f}")

    # 3. Mass flow through the throat.
    throat_area, p0, t0 = 0.02, 6.0e6, 3400.0
    flow = mass_flow.choked_mass_flow(products, throat_area, p0, t0)
    print()
    print(f"A_t = {throat_area} m^2 at {p0 / 1e6:.1f} MPa, {t0:.0f} K")
    print(f"     choked mass flow = {flow:.4f} kg/s")

    # 4. What a normal shock at that exit Mach number would cost.
    shock = normal_shock.solve(exit_mach, products)
    print()
    print(f"A normal shock at M = {exit_mach:.4f} would give")
    print(f"     M2 = {shock.mach2:.6f}, p02/p01 = {shock.stagnation_pressure_ratio:.6f}")

    # 5. The nozzle itself, which composes all of the above.
    geometry = AreaDistribution.conical(throat_area=throat_area,
                                        area_ratio=area_ratio, n=121)
    solution = nozzle.solve(geometry, NozzleOperating(p0, 101_325.0, t0),
                            products).unwrap()
    print()
    print(f"At sea-level back pressure the nozzle is {solution.regime.value}")
    print(f"     mass flow  {solution.mass_flow:.4f} kg/s"
          f"  (matches the throat calculation: {abs(solution.mass_flow - flow) < 1e-9})")
    print(f"     exit M     {solution.exit.mach:.6f}")
    print(f"     exit p     {solution.exit.pressure:,.1f} Pa")
    print(f"     exit V     {solution.exit.velocity:,.2f} m/s")
    print()
    print("No thrust, no Isp: those belong to the engineering layer, which will"
          " call this one.")


if __name__ == "__main__":
    main()
