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
- Tank Pressurization (SYS-4): regulated stored gas and blowdown per
  branch, with a perfect gas (Sutton §6.4, §6.5). The regulated mode applies
  Eq. 6-5 with explicit temperatures: mp = pp Vp/(R Tp),
  Tg = T0 (pg/p0)^((n−1)/n), V0 = mp R/(p0/T0 − pg/Tg). It reproduces
  Eq. 6-7 and Example 6-2 exactly under their conventions and reports the
  bottle mass, the residual gas, the end-of-burn regulator drop and an
  optional stated reserve. Blowdown evolves the SYS-3 ullage as pV^n =
  const, with the end-of-burn pressure and the margins. No gas, gas
  constant, exponent, temperature or pressure has a default. The required
  tank pressure is stated, or taken from the LIQ-6 ledger, and stays
  unresolved when that ledger is incomplete. Autogenous and warm-gas
  pressurization are recorded as intent only. Sutton's helium isentropic
  line in Example 6-2 prints 1.334 V0 where its equation gives 1.322; the
  equation is followed and the discrepancy pinned. Real-gas
  compressibility, heat transfer, boil-off, regulator dynamics and
  pressurant lines are not modelled. See
  [docs/engineering/design/SYS4_TANK_PRESSURIZATION.md](docs/engineering/design/SYS4_TANK_PRESSURIZATION.md).
- Feed Network (SYS-5): each branch's liquid line from the tank outlet to
  the injector inlet is an explicit series of components. Pipes use the
  Darcy friction factor of `engineering.line` (none in the transition band);
  local losses, valves and check valves use K ρv²/2 with K stated (no Cv
  conventions); filters and explicit losses take a stated Δp; static head is
  ρ a Δz with a stated sign convention; the velocity head ρv²/2 is the
  injector-inlet boundary; unknown components stay unresolved. The
  injector inlet needs the LIQ-6 terms downstream of it. LIQ-6's feed-line
  and valve terms are always replaced and recorded as excluded, the dynamic
  head and other terms are carried or replaced as stated, and carrying the
  dynamic head beside a velocity-head component is refused, so no loss is
  counted twice. The tank-outlet requirement is closed against each SYS-4
  tank pressure. Two-phase flow, cavitation and NPSH, transients, valve
  dynamics, pumps and cooling channels are not modelled. See
  [docs/engineering/design/SYS5_FEED_NETWORK.md](docs/engineering/design/SYS5_FEED_NETWORK.md).
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
- `rocketforge/evidence/engines` (DB-1): the production schema for reference
  liquid-engine evidence. It is internal infrastructure, with no engine
  records, no UI and no solver use. It holds:
  - family, variant, configuration and operating point, with no value
    inheritance between levels;
  - typed assertions with value kinds (a limit is not an operating value) and
    structured conditions, including chamber-pressure basis and measurement
    station;
  - sources with an access state and a content hash;
  - rights records that keep a host's statement and a printed notice when
    they disagree;
  - conflicts that reference claims and never average them;
  - topology graphs with typed edges (flow, shaft, gear, linkage, actuation,
    electrical), explicit completeness, and schematic provenance (an original
    drawing or a third-party reconstruction).

  Strict versioned JSON, schema version 1. Adds `MissingReason.ACCESS_BLOCKED`.
  See
  [docs/engineering/design/DB1_REFERENCE_ENGINE_EVIDENCE_SCHEMA.md](docs/engineering/design/DB1_REFERENCE_ENGINE_EVIDENCE_SCHEMA.md).
- Reference engine seed corpus (DB-2A): the initial verified seed corpus of
  three engine configurations, shipped as data in
  `rocketforge/data/evidence/engines/reference_engines.json`. The three are
  the J-2 at the 230,000 lb rating (MR 5.5 calibration point), the
  RL10A-3-3A at 475 psia and O/F 5.0, and the Apollo SPS engine (AJ10-137)
  in its Block I configuration. It is not a complete engine database. The
  J-2 thrust and the SPS Block I chamber pressure, thrust and specific impulse
  ship by recorded owner decision for their own configuration only, while the
  research conflicts behind them stay open.
  - Every value, graph element and source was promoted one by one from the
    DB-0.5 research through a reviewable manifest
    (`tools/reference_engines/db2a_manifest.py`) and gates that refuse
    unopened sources, unsettled rights, open conflicts, inferred values and
    filled-in conditions. The application reads only the shipped file.
  - `rocketforge.evidence.engines.admission` states what a shipped corpus
    must satisfy beyond the schema. `rocketforge.evidence.engines.capabilities`
    answers five questions per configuration: identity, architecture,
    performance reference, topology and regression candidate. A regression
    candidate is eligibility only; no regression is accepted.
  - `rocketforge.application.analysis.reference_engine_catalog` is a
    read-only backend over the corpus, with no UI, no provider and no solve.
    The package verifier also loads the packaged corpus.

  See
  [docs/engineering/design/DB2A_VERIFIED_REFERENCE_ENGINE_SEED_CORPUS.md](docs/engineering/design/DB2A_VERIFIED_REFERENCE_ENGINE_SEED_CORPUS.md).
- Reference engine corpus, DB-2B Wave 1: the curated, verified reference
  corpus grows from 3 to 11 engine configurations: J-2S, F-1, H-1 188K
  (Saturn I SA-10), the LM descent engine (final design), the Space Shuttle
  OMS engine, and three RS-25 builds (original-throat baseline, Block II as of
  2003, SLS-adapted). It is not comprehensive coverage, and most new records
  are deliberately sparse: values in open research conflicts, values from
  documents with restrictive notices (Boeing-proprietary, copyrighted
  workbooks and spec sheets) and values a source states for another build are
  not shipped, and nothing missing is filled in. RS-25 Block IIA ships no
  configuration (rights). The promotion tool merges the DB-2A and Wave 1
  manifests into one corpus and adds gates: field-level conflict coverage,
  per-configuration sources, disposition accounting, graph scope and
  provenance, recorded text bases for restated graph elements, owner decisions
  limited to the recorded ones, and notice reading that recognises an explicit
  "no copyright notice". See
  [docs/engineering/design/DB2B_WAVE1_VERIFIED_HISTORICAL_CORPUS.md](docs/engineering/design/DB2B_WAVE1_VERIFIED_HISTORICAL_CORPUS.md).

### Research
- DB-0 liquid engine research map (documentation and research data only; no
  application feature, nothing shipped). A best-effort, source-traceable map
  of publicly documented liquid rocket engines: 576 variant records in 227
  families, an architecture taxonomy, 46 anchor audits with topology graphs,
  a flow-schematic index, a source registry with rights classes, a conflict
  ledger and a proposed DB-1 schema. Values were read from web-search
  summaries only, so none is regression-grade; DB-0 is recorded as partial.
  See
  [docs/research/engine_database/DB0_RESEARCH_OVERVIEW.md](docs/research/engine_database/DB0_RESEARCH_OVERVIEW.md).

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
