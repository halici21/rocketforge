# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this
project does not yet follow strict Semantic Versioning (Engine Design mode
is not feature-complete, so a 1.0.0 would overstate it — see
[Known limitations](README.md#known-limitations)).

## [Unreleased]

### Added
- Build identity. Every package names the commit it was built from: in
  `rocketforge_build.json` beside the executable, in the executable's own
  version resource, and in Settings, which shows the build and offers **Copy
  build info**. A source run calls itself development (`[DEV <commit>]`); a
  package with no readable identity calls itself unknown, never current.
  `build_exe.bat` is the one build: it refuses a dirty or unpushed tree and
  any PySide6 other than the pin, and verifies the package by running it.
  See [docs/engineering/release/BUILD_AND_LAUNCH.md](docs/engineering/release/BUILD_AND_LAUNCH.md).
- Solid propellant thermochemistry: multi-component solid formulations
  solved to NASA CEA HP chamber equilibrium, with gas and condensed products
  and full provenance. Custom reactants require a formula, a heat of
  formation, a reference temperature and a source; no binder presets are
  shipped. NASA RP-1311 Example 5 is included as the reference case. See
  [docs/engineering/design/SOLID_PROPELLANT_PHASE1.md](docs/engineering/design/SOLID_PROPELLANT_PHASE1.md).
- CEA equilibrium characteristic velocity (c*) for solid formulations,
  shown with its limitations. It is not a motor Isp. Frozen c* is refused.
- Engine Requirement (LIQ-2): a page under **Liquid Engine** that records a
  liquid-engine requirement. It holds target thrust, the design environment
  as an ambient pressure, burn time, and preferences for the propellant pair
  (a LIQ-1 catalogue pair, or Auto), chamber pressure, O/F, feed architecture,
  power cycle (pump-fed only) and design priority. It is design intent only.
  Editing it solves nothing, and Auto choices stay open. Cycles, full-flow
  staged combustion included, are recorded as intent with no model behind
  them. The record round-trips as versioned JSON. See
  [docs/engineering/design/LIQ2_ENGINE_REQUIREMENT.md](docs/engineering/design/LIQ2_ENGINE_REQUIREMENT.md).
- Propellant Trade (LIQ-3): compares the liquid propellant catalogue pairs
  for the current engine requirement at a stated operating point. The
  comparison runs through the accepted NASA CEA chamber and RocketForge
  ideal-performance chain. It reports chamber temperature, molar mass, both
  gammas and c*. With a stated area ratio it also reports Cf, c_eff and Isp
  at the design ambient, plus total, oxidiser and fuel mass flow and the
  propellant consumed. Auto values in the requirement are never filled in,
  and nothing is scored. The user chooses a pair and can write it back to the
  requirement. Only Run trade solves. See
  [docs/engineering/design/LIQ3_PROPELLANT_TRADE.md](docs/engineering/design/LIQ3_PROPELLANT_TRADE.md).
- Thrust Chamber Sizing (LIQ-4): sizes the ideal thrust chamber and nozzle at
  the candidate selected in the propellant trade. The nozzle design input is
  an explicit Ae/At: the trade's own, or one stated for the sizing. It reports
  total, oxidiser and fuel mass flow; throat and exit area and diameter; c*,
  Cf (momentum and signed pressure terms), c_eff and Isp at the design
  ambient; the exit state; and momentum, pressure and total thrust with the
  closure against the target. The trade's chamber case is replayed through
  the accepted CEA path and must reproduce the trade's recorded numbers bit
  for bit. The ideal model's refusals and overexpansion notes pass through
  unchanged. Only Size solves. No chamber geometry, L*, injector, feed,
  cooling or cycle. See
  [docs/engineering/design/LIQ4_THRUST_CHAMBER_SIZING.md](docs/engineering/design/LIQ4_THRUST_CHAMBER_SIZING.md).
- Combustion Chamber Geometry (LIQ-5): extends an accepted sizing's throat
  upstream to a cylindrical chamber with a conical convergent, from a stated
  L*, contraction ratio Ac/At and converging half-angle. None of the three
  has a default. It reports chamber volume (L* · At, injector face to
  throat), chamber area and diameter, convergent length and volume, cylinder
  length and volume, injector-face-to-throat length, and the closures. The
  convergent uses the exact frustum volume: Sutton Eq. 8-8 is printed
  without its factor 1/3. A convergent larger than the chamber volume is
  refused, with the smallest L* that would fit. Ac/At below 3 and L*
  outside Sutton's typical range are advisories, not limits. Only Compute
  computes. No injector, pressure loss, cooling, structure or cycle. See
  [docs/engineering/design/LIQ5_COMBUSTION_CHAMBER_GEOMETRY.md](docs/engineering/design/LIQ5_COMBUSTION_CHAMBER_GEOMETRY.md).
- Injector & Feed Pressure (LIQ-6): takes an accepted sizing's oxidiser and
  fuel flows. For each branch it gives the total injector orifice area,
  A = ṁ/(Cd√(2ρΔp)), and the injection velocity, v = Cd√(2Δp/ρ) (Sutton
  §8.1, Eqs. 8-1, 8-2, 8-5). Optionally it splits the area into equal holes
  from a stated count or diameter, reporting the exact count, the whole-hole
  count and the Δp that whole count gives. Δp, Cd and density have no
  default. Density is stated, or taken from the validated CoolProp model for
  LOX, LCH4 and LH2 at the stream temperature and p1 + Δp. That model is
  liquid-phase only, so a supercritical inlet is refused with its reason. The
  pair closes O/F (Eq. 8-3) and total flow against LIQ-4. Each branch also
  has a pressure ledger (Sutton Eqs. 10-7, 11-6, 11-7). It holds chamber
  pressure, injector Δp, feed line, valves, cooling jacket, dynamic head ½ρv²
  (stated or from a line diameter), other losses and margin. Each term is
  stated, not applicable or unresolved, and unresolved is never zero. The
  ledger always gives the minimum known upstream pressure, and gives the
  required pressure only when it is complete. Δp/p1 is shown as
  stability-relevant; stability is not evaluated. Sutton's §8.9 worked example
  prints areas √2 larger than its own Eq. 8-2; the equations are followed and
  the discrepancy is recorded. Only Compute computes. No element design,
  atomization, efficiency, stability, pumps, tanks, cooling channels or cycle.
  See
  [docs/engineering/design/LIQ6_INJECTOR_FEED_PRESSURE.md](docs/engineering/design/LIQ6_INJECTOR_FEED_PRESSURE.md).
- Propellant Inventory (SYS-1): the first page of a new **Propulsion System**
  family, for the stage around the engine. It takes an accepted LIQ-4
  sizing's oxidiser and fuel flows and the LIQ-2 burn time, read through the
  trade that sizing extends. Per branch it keeps a mass budget: usable
  ṁ × t, available (usable plus stated transients, chill-down, other
  allowances and reserve), residual, and loaded (present plus boil-off). The
  residual comes from a stated expulsion efficiency η, with
  present = available/η, or from a stated tank residual and trapped-line mass
  (Sutton §6.2, §11.1, Example 11-1). The reserve is a stated mass or a stated
  fraction of the usable mass. No η, reserve, trapped-line mass, boil-off,
  transient or chill-down mass has a default. Unresolved is never zero: the
  loaded mass waits on it, and the minimum known load is given instead. No
  gas-generator or other cycle flow is added. Stale, refused or mismatched
  upstream results are refused. The record round-trips through versioned,
  fingerprint-checked JSON, and only Compute computes. See
  [docs/engineering/design/SYS1_PROPELLANT_INVENTORY.md](docs/engineering/design/SYS1_PROPELLANT_INVENTORY.md).
- Tank Geometry & Packaging (SYS-2), in **Propulsion System**: from a
  complete SYS-1 inventory, each branch's tank holds its loaded mass as
  liquid at a stated storage density, or the validated LOX/LCH4/LH2 liquid
  model at a stated storage temperature and pressure. With a stated ullage
  (a fraction of the tank, or a volume), V_tank = V_liquid/(1 − u) or
  V_liquid + V_u. The internal geometry is a sphere, or a cylinder with two
  hemispherical or ellipsoidal domes (half spheroids, k = h/R stated,
  0 < k ≤ 1). A cylinder is fixed by a stated diameter, which solves the
  barrel length, or a stated total length, which solves the radius by
  bracketed Brent on its monotonic range. The result gives the volumes,
  fill fraction, dimensions, dome volume and height, and analytic internal
  surface area, with mass, ullage and geometric closures. A geometry that
  cannot hold the volume, or that exceeds a stated envelope, is refused. No
  shape, diameter or optimum is chosen. Internal geometry only: no wall,
  MEOP, mass, insulation, common bulkhead or boil-off. See
  [docs/engineering/design/SYS2_TANK_GEOMETRY_PACKAGING.md](docs/engineering/design/SYS2_TANK_GEOMETRY_PACKAGING.md).
- Propellant Management (SYS-3): from the current SYS-1 inventory and the
  SYS-2 tanks built on it, each branch states its management mode (settled
  free surface, diaphragm, bladder, piston, bellows or surface-tension
  PMD), its acceleration environment and its settling intent. Outlet
  coverage is a declaration with its basis, never a demonstration (Sutton
  §6.2). A settled free surface in low gravity with no settling is
  refused; an unstated environment is unresolved; low-gravity feed is never
  claimed from geometry. The expulsion efficiency and residual stay SYS-1's
  and are never assigned from a device type (Table 6-2 is qualitative). The
  liquid and gas volumes from loading to the end of the burn are booked
  and closed. Full slosh dynamics are not modelled. See
  [docs/engineering/design/SYS3_PROPELLANT_MANAGEMENT.md](docs/engineering/design/SYS3_PROPELLANT_MANAGEMENT.md).
- Atmosphere foundation (ENV-1): `rocketforge/physics/atmosphere`, a
  reusable, Qt-free atmosphere state contract with manual-pressure, vacuum
  and U.S. Standard Atmosphere 1976 sources. The Standard runs from -5 km to
  1000 km geometric, from its own equations and constants, with geometric and
  geopotential altitude kept distinct. ENV-1B adds the 80-86 km transition
  (Table 8) and the diffusive upper atmosphere: N2, O, O2, Ar, He and H
  integrated from the Standard's equations, with P = NkT. Above 86 km the
  Standard defines no speed of sound or viscosity, and the state says so
  rather than inventing them. Everything is checked against the Standard's
  printed tables, including composition at 15 heights to 1000 km. The Engine Requirement can now state an altitude as the
  source of its design ambient pressure. The requirement records it as
  intent, and the application layer resolves it. Trade and sizing read the
  resolved pressure, and an altitude gives the same results as the same
  pressure stated manually. Requirements without an altitude are unchanged,
  byte for byte. NRLMSIS 2.1 (ENV-2) is deferred: NRL licenses it for
  academic, non-commercial use only. No weather, flight condition or
  trajectory. See
  [docs/engineering/design/ENV1_ATMOSPHERE_FOUNDATION.md](docs/engineering/design/ENV1_ATMOSPHERE_FOUNDATION.md).
- Flight environment foundation (ENV-3): `rocketforge/physics/flight`, a
  Qt-free point-state calculation. From an atmosphere state and explicit
  inputs (geometric altitude, air-relative speed and, for the Reynolds number
  only, a characteristic length), it gives four quantities. Gravity is
  g = GM/r², r = R + Z, with WGS 84 GM and semi-major axis; there is no J2,
  latitude or rotation term. It also gives Mach number V/a, dynamic pressure
  ½ρV² and Reynolds number ρVL/μ. A quantity whose atmosphere ingredient is
  not defined has no value and carries the atmosphere's own reason. Above
  86 km there is no Mach or Reynolds number. In vacuum q = 0, and there is no
  Mach or Reynolds number. A manual pressure gives gravity only. The speed is
  relative to the air, and no wind is assumed inside the physics. Results
  round-trip through versioned JSON with provenance. No trajectory, drag,
  lift, losses, winds or UI. See
  [docs/engineering/design/ENV3_FLIGHT_ENVIRONMENT.md](docs/engineering/design/ENV3_FLIGHT_ENVIRONMENT.md).
- `rocketforge/comparison`: comparison against reference cases. Direct CEA
  and NASA printouts get a verdict; independent codes (PROPEP, EXPLO5) and
  experiments get differences only.

### Not included
- Solid motor performance: Isp, thrust, thrust curve, Pc(t), nozzle
  expansion and internal ballistics. Rocket Performance refuses a solid
  chamber.

## [v0.1.0] — 2026-09-14

First downloadable build.

### Added
- Analysis mode: classic gas dynamics (Fanno, Rayleigh, isentropic,
  normal/oblique shock, Prandtl-Meyer, mass flow), NASA CEA-backed
  thermochemistry, CoolProp-backed fluid properties, line/transport, and a
  chamber+nozzle performance chain (c*, Cf, Isp) — all frozen, documented
  contracts (see [docs/README.md](docs/README.md)).
- Trade Study: design-space evaluation with Pareto-front visualization.
- Engine Design mode: an interactive canvas, component palette, and
  inspector — presentation-only, no component is solved end to end (see
  [Known limitations](README.md#known-limitations)).
- CI (GitHub Actions) running the full test suite, both with and without
  the NASA CEA provider installed.
- Prebuilt Windows executable, self-contained (NASA CEA and CoolProp
  bundled).

### Verified
- NASA CEA and Cantera thermochemistry providers, cross-checked against
  each other and against independent published references — see
  [docs/engineering/verification/CEA_CANTERA_VERIFICATION_R1.md](docs/engineering/verification/CEA_CANTERA_VERIFICATION_R1.md).

[v0.1.0]: https://github.com/halici21/rocketforge/releases/tag/v0.1.0
