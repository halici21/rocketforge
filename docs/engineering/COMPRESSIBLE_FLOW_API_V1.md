# Fundamental Compressible Flow API v1.0

**Status:** frozen for the public surface described here.
**Namespace:** `rocketforge.physics.compressible`
**Machine-readable contract:** `tests/contracts/compressible_api_v1.json`, enforced by
`tests/contracts/test_compressible_api_v1.py`.

This is the contract a future engineering module may build on. Everything in it
is checked by a test; nothing in it is aspirational.

---

## 1. What "frozen" means

Code written against this document may rely on:

* **public symbol names** — what is exported, from where;
* **argument meaning and order** — including which arguments are mandatory;
* **branch semantics** — which enum member selects which physical root;
* **units** — SI below the application layer, radians for every angle;
* **result-field meaning and order** — the fields of each frozen record;
* **ratio orientation** — what is divided by what, stated per field;
* **status meaning** — what `ok`, `warning`, `not_converged` and `no_solution`
  imply about the value.

Internal implementation may still change: a faster inverse, a different
bracket, a new cache. What may not change silently is anything in the list
above, or in the contract file.

**A breaking change requires a version bump or a recorded erratum**, made in
the same commit that updates `compressible_api_v1.json`, so it appears in
review rather than in a downstream module's failure.

---

## 2. Recommended imports

Everything needed for normal use is reachable from the package root. No caller
should ever have to import a private module path.

```python
from rocketforge.physics.compressible import (
    PerfectGas, FlowBranch, ShockBranch, NozzleRegime,
    AreaDistribution, NozzleOperating,
    isentropic, mass_flow, normal_shock, prandtl_meyer,
    oblique_shock, fanno, rayleigh, nozzle,
)
```

The package exports 36 names: eleven submodules and twenty-five types. A test
asserts that every submodule is both importable from the package and listed in
`__all__`.

---

## 3. Conventions that hold everywhere

### 3.1 Units

| Quantity | Unit |
| --- | --- |
| pressure | Pa |
| temperature | K |
| area | m² |
| length, position | m |
| velocity, speed of sound | m/s |
| density | kg/m³ |
| mass flow | kg/s |
| specific heat, gas constant | J/(kg K) |
| specific heat addition | J/kg |
| **angles** | **radians** |

There is no unit library in the physics layer and no implicit conversion. A
name ending in `_deg` is forbidden below `application`, and the architecture
suite enforces it. Degrees exist only above that boundary, where a user types
them.

### 3.2 Ratio orientation

Every ratio names both of its parts. The rule is mechanical:

| Form | Meaning | Example |
| --- | --- | --- |
| `pressure_ratio` on a *state* relation | static over stagnation, `p/p0` | `isentropic.pressure_ratio(M, gas)` |
| `pressure_ratio` on a *jump* record | downstream over upstream, `p2/p1` | `NormalShockResult.pressure_ratio` |
| `*_ratio_star` | static over the sonic reference, `p/p*` | `isentropic.pressure_ratio_star` |
| `*_ratio` on a Fanno/Rayleigh state | the same, `p/p*` | `FannoState.pressure_ratio` |
| `stagnation_pressure_ratio` on a jump | `p02/p01` | `NormalShockResult` |
| `stagnation_pressure_ratio` on a Fanno/Rayleigh state | `p0/p0*` | `FannoState` |
| `*_12` suffix | explicitly outlet over inlet | `FannoDuctResult.pressure_ratio_12` |

Where a UI shows the reciprocal because a textbook does — `p0/p` on the
Isentropic page — that inversion happens in the application layer, never in
the physics.

### 3.3 Static, stagnation, total

RocketForge uses **stagnation** in field names and treats *total* as its
synonym in prose. There is no field named `total_*`; a reader who sees "total
pressure" in an interface is looking at `stagnation_pressure`.

### 3.4 What the star means, per module

`*` is a sonic reference state, but **not the same one in every module**, and
conflating them is a real error:

| Module | `*` is | Shares stagnation state with the flow? |
| --- | --- | --- |
| isentropic, area–Mach, mass flow, nozzle | the sonic state reached **isentropically** from the same stagnation condition | yes: same p0, same T0 |
| fanno | the sonic state reached **by friction** along the same Fanno line | T0 yes, p0 **no** |
| rayleigh | the sonic state reached **by heat exchange** along the same Rayleigh line | neither |

Two exact coincidences are real and tested: `fanno.temperature_ratio` equals
`isentropic.temperature_ratio_star`, and `fanno.stagnation_pressure_ratio`
equals `isentropic.area_ratio` — the latter because `p0 A*` is fixed for a
given mass flow and T0. `p/p*`, `rho/rho*` and `V/V*` do **not** coincide, and
a test asserts the difference so a future tidy-up cannot merge the families.

### 3.5 Errors versus solutions

| Situation | Behaviour |
| --- | --- |
| malformed or out-of-domain input | **raises** `DomainError`, `InputError`, `GeometryError`, … |
| a physically unattainable request | returns `Solution` with `status=no_solution`, `value=None`, and a diagnostic |
| an iterative result | returns `Solution` with a `Convergence` report |
| a closed-form result | returns the value, or a `Solution` with `convergence=None` |

Nothing is ever silently clamped into range. A duct longer than the flow can
sustain, heat beyond the choking limit, a turn past ν_max, a deflection past
θ_max and a nozzle back pressure outside `(0, 1)` are all *reported*, never
adjusted.

### 3.6 Branches are never guessed

Four inverses have two physical roots. Each takes a **mandatory** branch:

```python
isentropic.mach_from_area_ratio(area_ratio, gas, branch)
mass_flow.mach_from_mass_flow_ratio(ratio, gas, branch)
fanno.mach_from_friction_parameter(parameter, gas, branch)
rayleigh.mach_from_stagnation_temperature_ratio(ratio, gas, branch)
oblique_shock.solve(mach1, theta, gas, branch)      # weak or strong
```

A test asserts none of them ever acquires a default. `FlowBranch.BOTH` and
`ShockBranch.BOTH` are **requests only** — they select the paired entry points
(`mach_from_area_ratio_both`, `solve_both`) and never appear in a result.

`rayleigh` deliberately offers **no** `T/T*` inverse: that relation is not
monotone on the subsonic branch, so a branch flag could not separate its two
roots. Offering an ambiguous inversion would be worse than not offering one.

### 3.7 No hidden gas

Every relation takes its `gas` explicitly. There is no default γ, no "current
gas", no module-level mutable state, and no singleton. A test walks the whole
subsystem asserting this.

---

## 4. Modules

### 4.1 `gas` — `PerfectGas`

```python
PerfectGas(gamma: float, gas_constant: float | None = None)
```

Frozen. `gamma` is validated against the hard limits (1.001 … 3.0) with an
advisory band (1.05 … 1.9). `gas_constant` is optional: the dimensionless half
of the subsystem needs only γ, and asking a gas without R for `cp`, `cv` or a
speed of sound raises `MissingGasConstantError` rather than inventing one.

Properties: `cp`, `cv`, `gas_constant`, `gamma`; method `speed_of_sound(T)`.

### 4.2 `isentropic`

Forward, vectorised, scalar-in-scalar-out:
`temperature_ratio`, `pressure_ratio`, `density_ratio` (all static/stagnation),
`area_ratio` (A/A*), `temperature_ratio_star`, `pressure_ratio_star`,
`density_ratio_star`, `mach_angle` (radians).

Closed-form inverses: `mach_from_temperature_ratio`, `mach_from_pressure_ratio`,
`mach_from_density_ratio`.

Bracketed inverse: `mach_from_area_ratio(ratio, gas, branch)` →
`Solution[float]`; `mach_from_area_ratio_both` → `Solution[AreaMachSolutions]`;
`mach_from_area_ratio_array` for a batch.

Aggregate: `ratios_from_mach` → `IsentropicRatios`.

### 4.3 `mass_flow`

`mass_flow_parameter` (MFP), `choked_mass_flow_coefficient` (Γ),
`mass_flow_over_choked`, `mass_flow`, `mass_flux`, `choked_mass_flow`,
`choked_mass_flux`, `critical_pressure_ratio`, `critical_temperature_ratio`,
`is_choked`, `mach_from_mass_flow_ratio(ratio, gas, branch)`.

The identity `mdot/mdot_choked = MFP/Γ = A*/A` links this module to the area
relation and is tested at four γ across the whole Mach grid.

### 4.4 `normal_shock`

`mach_downstream`, `pressure_ratio`, `density_ratio`, `temperature_ratio`,
`stagnation_pressure_ratio`, `stagnation_pressure_over_upstream_static` (the
pitot ratio), `entropy_change`, `area_star_ratio`, the two limits
(`density_ratio_limit`, `mach_downstream_limit`), four inverses, and
`solve(mach1, gas)` → `NormalShockResult`.

`stagnation_temperature_ratio` is the literal `1.0`: the model is adiabatic and
a computed `0.9999999` would invite doubt about what was lost.

### 4.5 `prandtl_meyer`

`nu`, `nu_max`, `mach_angle` (**re-exported from `isentropic`, not a second
implementation** — a test asserts identity), `mach_from_nu`,
`mach_from_nu_array`, `expand`, `compress` → `Solution[PrandtlMeyerResult]`.

`nu2` in the record is recomputed from the Mach number actually returned, so
the record is self-consistent; it therefore differs from `nu1 + turn` by the
inversion tolerance carried through dν/dM.

### 4.6 `oblique_shock`

`theta_from_beta`, `theta_max`, `beta_sonic`, `beta_from_theta`,
`solve(mach1, theta, gas, branch)`, `solve_from_beta`, `solve_both`,
`theta_beta_curve`.

Every jump quantity in an `ObliqueShockResult` is `normal_shock` evaluated at
`mach_normal1 = M1 sin β` — asserted identical, not merely close. A deflection
beyond θ_max returns `no_solution` with `DETACHED_SHOCK`; no attached answer is
fabricated.

### 4.7 `fanno`

Adiabatic, constant area, wall friction. Five starred ratios plus
`friction_parameter` — **the Fanning group `4 f_F L*/D`**, with
`f_D = 4 f_F`. `darcy_to_fanning` and `fanning_to_darcy` are the only sanctioned
conversion; `duct_parameter_from_geometry(fanning, length, hydraulic_diameter)`
takes the Fanning factor.

`state`, `friction_parameter_limit` (0.8215081165 at γ = 1.4),
`mach_from_friction_parameter(value, gas, branch)`, `downstream_mach`,
`required_duct_parameter`.

### 4.8 `rayleigh`

Frictionless, constant area, heat exchange through the state relation only.
Five starred ratios, `mach_at_maximum_temperature` (1/√γ),
`maximum_temperature_ratio` ((γ+1)²/4γ), `stagnation_temperature_ratio_limit`,
`state`, `mach_from_stagnation_temperature_ratio(ratio, gas, branch)`,
`heat_addition`, `specific_heat_addition`.

The two maxima are different states at different Mach numbers and are exposed
separately. See §3.6 for why there is no `T/T*` inverse.

### 4.9 `geometry` — `AreaDistribution`

```python
AreaDistribution(x, area)
AreaDistribution.from_area_ratios(x, area_ratio, throat_area=1.0)
AreaDistribution.conical(throat_area, area_ratio, converging_ratio=4.0,
                         half_angle=pi/12, converging_half_angle=pi/6, n=201)
```

Geometry only. The constructor accepts any physically meaningful duct;
`require_converging_diverging()` adds what the C-D solver needs. Interpolation
is Fritsch–Carlson monotone cubic, so it cannot invent an extremum the supplied
data does not have. `area_at(x)` and `x_at_area(area, side)` — the side is
mandatory, because a C-D duct reaches almost every area twice.

### 4.10 `nozzle`

```python
critical_pressure_ratios(area_ratio_exit, gas, tolerances) -> Solution[CriticalPressureRatios]
classify(area_ratio_exit, pressure_ratio_back, gas, tolerances) -> Solution[NozzleRegimeResult]
shock_area_ratio(area_ratio_exit, pressure_ratio_back, gas, tolerances) -> Solution[ShockLocation]
solve(geometry, operating, gas, tolerances) -> Solution[NozzleSolution]
```

The first three are dimensionless and need no contour. Only `solve` returns a
physical shock position; `ShockLocation.x` is `None` from the dimensionless
path, which is the type saying that an area ratio cannot know where that area
occurs.

Restates nothing: area–Mach, the isentropic ratios, the normal shock and the
mass flow are all *called*. An audit reads the source for the formulas that
must not appear in it.

---

## 5. Enums

```python
FlowBranch    = subsonic | supersonic | both      # `both` is a request only
ShockBranch   = weak | strong | both              # `both` is a request only
NozzleRegime  = unchoked_subsonic | choked_subsonic_exit | internal_normal_shock
              | shock_at_exit | overexpanded | ideally_expanded | underexpanded
Status        = ok | warning | not_converged | no_solution
Severity      = info | warning | error
```

The string values are part of the contract: they are what a serialized result
carries, and renaming one would silently invalidate stored data.

---

## 6. Diagnostics

Diagnostics are data — never printed, never raised through `warnings`. Each has
a stable `code`, a `severity`, one user-facing sentence, and optional numeric
detail.

| Code | Severity | Result is | Meaning |
| --- | --- | --- | --- |
| `SONIC_EXACT` | info | exact | the input was within the sonic window; M = 1 returned exactly |
| `NEAR_SONIC` | info | valid | close enough to sonic that resolution is limited |
| `EXTRAPOLATED_GAMMA` | info | valid | γ outside the advisory band, inside the hard limits |
| `NOT_CONVERGED` | warning | best iterate | the iteration ceiling was reached |
| `NU_EXCEEDS_MAX` | error | none | the requested turn exceeds ν_max |
| `NU_BELOW_ZERO` | error | none | a compression turn below the sonic limit |
| `DETACHED_SHOCK` | error | none | deflection beyond θ_max: no attached solution |
| `NEAR_THETA_MAX` | info | valid | the two oblique roots are close and poorly separated |
| `STRONG_BRANCH_UNSTABLE` | info | valid | the strong root is rarely realised in practice |
| `FRICTION_CHOKED` | error | none | the requested duct exceeds the length to sonic |
| `FANNO_LIMIT` | error | none | beyond the supersonic branch's bounded ceiling |
| `THERMALLY_CHOKED` | error | none | the requested heat exceeds the sonic limit |
| `RAYLEIGH_LIMIT` | error | none | below the supersonic `T0/T0*` floor |
| `NOT_CHOKED` | info | valid | nozzle: the throat is not sonic |
| `NO_INTERNAL_SHOCK` | info/error | none | no shock exists at this back pressure |
| `SHOCK_AT_EXIT` | info | valid | the shock stands exactly in the exit plane |
| `EXTERNAL_COMPRESSION` | info | valid | overexpanded: adjustment happens outside |
| `EXTERNAL_EXPANSION` | info | valid | underexpanded: adjustment happens outside |
| `MODEL_LIMIT_SEPARATION` | warning | valid | strongly overexpanded; a flag, not a prediction |
| `NEAR_REGIME_BOUNDARY` | info | valid | within a factor of 1000 of a threshold |
| `CRITICAL_ORDER` | error | none | the three criticals came out unordered |
| `DIMENSIONLESS_ONLY` | info | partial | no T0 or R, so no dimensional arrays |
| `ISENTROPIC_COMPRESSION` | info | valid | a compression turn treated isentropically |
| `BRANCH_ASSUMED` | info | valid | a paired request resolved to one branch |

**Terminology, deliberately distinct.** *Choked* means different mechanisms in
different modules — a fixed maximum mass flow (mass flow, nozzle), the maximum
friction length (Fanno), the heat-addition sonic limit (Rayleigh) — so each
carries its own code rather than one generic status. *Detached* belongs to the
oblique shock alone and is never reused for the absence of a nozzle shock.

---

## 7. Numerical policy

All tolerances come from the frozen `ToleranceSet` in `rocketforge.core.tolerances`,
passed explicitly, with no module-level configuration. The set is complete as of
Phase 4F: `pressure_tol` was the last field to arrive.

Every bracketed inverse in the subsystem uses one root finder — the Phase 4A
Brent–Dekker implementation in `rocketforge.core.numerics.roots`. There is no
Newton path, no secant fallback, no local bisection and no SciPy. Brackets are
derived from the physics, never searched for.

Conditioning limits are documented in `COMPRESSIBLE_NUMERICAL_LIMITS.md`.

---

## 8. What v1 does not model

Variable γ · real-gas behaviour · reacting or equilibrium chemistry · viscous
losses · boundary layers · finite shock thickness · flow separation ·
shock–boundary-layer interaction · turbulence · multidimensional flow · the
external plume · combustion · and every rocket performance quantity: thrust,
Cf, c\*, Isp, nozzle efficiency, discharge coefficient.

Those belong above this layer, in modules that will *call* it.
