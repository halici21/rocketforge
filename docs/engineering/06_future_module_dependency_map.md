# 06 — Future Module Dependency Map

What each future module owns, what it may depend on, what data it hands
onward, and — most importantly — what it must **never** own. Documentation only;
none of this is built in Phase 4 except the compressible module.

---

## 1. The map at a glance

```
                         +-------------------------+
                         |     ENGINE SYSTEM       |   L3
                         |  cycles, balances,      |
                         |  network, studies       |
                         +-----------+-------------+
                                     | uses
        +--------------+-------------+-------------+---------------+
        |              |             |             |               |
   +----v----+   +-----v----+  +-----v-----+  +----v-----+   +-----v----+
   | injector|   | chamber  |  |  nozzle   |  | cooling  |   |  pump /  |   L2
   |         |   |          |  | (rocket)  |  |          |   | turbine  |
   +----+----+   +-----+----+  +-----+-----+  +----+-----+   +-----+----+
        |              |             |             |               |
        |              |        uses |             |               |
        |              |     +-------v--------+    |               |
        |              +---->| COMPRESSIBLE   |<---+               |
        |                    | (this phase)   |                    |   L1
        |                    +-------+--------+                    |
        |                            |                             |
   +----v---------+   +--------------v-----+   +------------+   +--v-------------+
   | fluids       |   | thermochemistry    |   | heat       |   | combustion     |   L1
   | (interfaces) |   | (interfaces)       |   | transfer   |   |                |
   +----+---------+   +----------+---------+   +-----+------+   +----------------+
        |                        |                   |
        | implemented by         | implemented by    |
   +----v---------+   +----------v---------+         |
   | CoolProp     |   | CEA / RocketCEA /  |         |                              L4
   | provider     |   | Cantera provider   |         |
   +--------------+   +--------------------+         |
                                                     |
                    +--------------------------------v--------+
                    |             CORE                        |   L0
                    | units, errors, result, numerics, prov.  |
                    +-----------------------------------------+
```

Arrows point *from* the dependent module *to* what it depends on. There is no
arrow from any L1 box upwards — that is the invariant the architecture test
enforces (`01` §4).

---

## 2. Module table

| Module | Layer | Owns | Depends on | Outgoing data | Must NOT own |
| --- | --- | --- | --- | --- | --- |
| `core` | L0 | units, constants, `Solution`, errors, tolerances, Brent, provenance | — | typed infrastructure | any physical relation |
| `physics.compressible` | L1 | γ-based isentropic, mass flow, shocks, PM, Fanno, Rayleigh, quasi-1D nozzle | `core` | ratios, Mach, regimes, distributed arrays | thrust, Isp, c\*, Cf, chemistry, contours, geometry generation, fluid properties |
| `physics.fluids` | L1 | `FluidState`, `FluidPropertyProvider` protocol, constant-property model | `core` | ρ, μ, k, h, s, cp, phase | any device correlation; any external library import |
| `physics.thermochemistry` | L1 | `ChamberGas`, `GasStation`, provider protocol | `core` | T₀, γ, R, M̄, composition | chamber sizing, nozzle geometry, performance |
| `physics.heat_transfer` | L1 | Nusselt/Prandtl/Reynolds correlations, conduction, radiation kernels | `core`, `physics.fluids` | h, q″, wall temperatures | channel geometry, jacket layout |
| `physics.combustion` | L1 | flame speed, characteristic times, stability parameters | `core`, `physics.thermochemistry` | timescales, stability numbers | injector element design |
| `engineering.injector` | L2 | orifice sizing, ΔP, Cd application, element patterns, momentum ratio | `physics.fluids`, `core` | ṁ per element, ΔP, spray parameters | fluid property equations, chamber pressure determination |
| `engineering.chamber` | L2 | L\*, contraction ratio, residence time, chamber volume | `physics.thermochemistry`, `physics.compressible` | chamber gas state, throat conditions | equilibrium chemistry, nozzle expansion |
| `engineering.nozzle` | L2 | **thrust, Cf, c\*, Isp**, contour generation (conical, bell, Rao), divergence loss, efficiency factors, separation correlations | `physics.compressible`, `physics.thermochemistry` | F, Isp, Cf, contour, exit state | quasi-1D area-Mach or shock physics |
| `engineering.cooling` | L2 | channel sizing, coolant ΔP and ΔT, wall temperature, jacket layout | `physics.heat_transfer`, `physics.fluids` | coolant outlet state, wall temperatures | fluid property equations, hot-gas state determination |
| `engineering.pump` | L2 | head, efficiency, NPSH, specific speed, power | `physics.fluids` | Δp, power, outlet state | shaft speed balancing across the cycle |
| `engineering.turbine` | L2 | expansion ratio, efficiency, power extracted | `physics.fluids`, `physics.thermochemistry` | power, outlet state | shaft power balance |
| `engineering.valve` | L2 | Cv/Kv, ΔP, authority | `physics.fluids` | ΔP, ṁ | feed-network solution |
| `engineering.line` | L2 | pipe ΔP, friction factor correlation, hydraulic diameter | `physics.fluids`, `physics.compressible.fanno` | ΔP, outlet state | network topology |
| `engineering.tank` | L2 | ullage, pressurant demand, outflow, blowdown | `physics.fluids` | outlet state, pressurant ṁ | feed-system iteration |
| `engineering.gas_generator` / `preburner` | L2 | off-stoichiometric combustion sizing, turbine inlet conditioning | `physics.thermochemistry`, `engineering.chamber` | turbine inlet gas state | turbine performance |
| `engineering.heat_exchanger` | L2 | effectiveness, NTU, area | `physics.heat_transfer`, `physics.fluids` | outlet states | fluid properties |
| `engine.network` | L3 | graph topology, port typing, connectivity validation | `engineering.*` | resolved network | component equations |
| `engine.balances` | L3 | mass, pressure, power and energy balances | `engineering.*` | residual vector | component equations |
| `engine.cycles` | L3 | pressure-fed, GG, expander, staged, FFSC topologies | `engine.network`, `engine.balances` | cycle definition | component equations |
| `engine.solver` | L3 | multivariate iteration, convergence, damping, continuation | `engine.balances`, `core.numerics` | converged engine state | any physics |
| `engine.studies` | L3 | parametric studies, trades, sensitivity | `engine.solver` | study results | physics |
| `providers.*` | L4 | adapters onto CoolProp / CEA / Cantera / tables | `physics.*` interfaces | `FluidState`, `ChamberGas` | any device or system logic |
| `application.*` | L5 | composition, controllers, view models, formatting | everything | QML-ready state | any relation |

---

## 3. Forbidden dependencies — explicitly

| Forbidden | Why |
| --- | --- |
| `physics.*` → `engineering.*` | inverts the layering; the day `compressible` imports `nozzle` for a contour helper, the fundamental layer stops being fundamental |
| `physics.*` → `providers.*` | the interface belongs to physics; the implementation must not |
| `physics.*` → `PySide6` | acceptance criterion (task §89) |
| `engineering.*` → `engine.*` | a component must be usable without an engine around it |
| any layer → `application.*` | the composition root is a leaf, not a library |
| `engineering.nozzle` → its own quasi-1D relations | duplication; it must call `physics.compressible.nozzle` |
| `engineering.cooling` → its own fluid property equations | duplication; it must call a `FluidPropertyProvider` |
| `engineering.pump` / `turbine` / `injector` → `import CoolProp` | library leakage (task §15) |
| `compressible` → chamber/thrust/Isp concepts | ADR-15, the fundamental/rocket split |
| `ui` → any Python module directly | QML talks only to registered controllers |

---

## 4. Boundary contracts in detail

### 4.1 Thermochemistry → compressible (task §117)

**Compressible v1 receives γ, R, p₀ and T₀ as inputs and computes no chemistry.**

```
fuel + oxidiser + MR + pc
        |
        v   ThermochemistryProvider.equilibrium_chamber()
   ChamberGas { T0, gamma, gas_constant, molar_mass, composition, provenance }
        |
        v   engineering.chamber  (adapts to the station of interest)
   PerfectGas(gamma, R) + p0 + T0
        |
        v   physics.compressible.nozzle.solve()
   NozzleSolution { regime, M(x), p(x), T(x), ... }
        |
        v   engineering.nozzle
   F, Cf, c*, Isp
```

The compressible module never learns where γ came from. That is what makes the
same module serve a γ = 1.4 air textbook problem and a γ = 1.22 combustion-gas
analysis without a branch anywhere in its code.

The known limitation of that handshake (a single γ across a large expansion) is
recorded in `03` §10.11; the fix is a *separate* equilibrium/frozen nozzle model,
not a mutation of v1.

### 4.2 Injector boundary (task §118)

`engineering.injector` obtains density, viscosity and thermophysical data from a
`FluidPropertyProvider` — never by importing CoolProp, and never by carrying its
own property correlations.

It must **not** import compressible nozzle logic. The temptation exists because
an injector orifice can choke, but a choked *liquid* orifice is cavitation
(a fluid-property phenomenon) and a choked *gas* orifice is
`physics.compressible.mass_flow` with a device discharge coefficient — the
generic relation, not the nozzle module.

```
FluidPropertyProvider -> FluidState (rho, mu, p_sat)
                            |
                            v
                    engineering.injector
                       - orifice sizing from mdot, dP, Cd
                       - element momentum ratio
                       - cavitation margin from p_sat
                            |
                            v
                    mdot per element, dP, spray parameters
```

### 4.3 Cooling boundary (task §119)

```
physics.compressible.nozzle  ->  hot-gas state along the wall (T, p, M, V)
AreaDistribution / contour   ->  wall geometry
FluidPropertyProvider        ->  coolant properties
physics.heat_transfer        ->  correlations (Bartz-type hot side, channel side)
                                   |
                                   v
                         engineering.cooling
                           - channel sizing
                           - coolant dP and dT
                           - wall temperature
                                   |
                                   v
                    coolant outlet state -> back into the feed system
```

`engineering.cooling` owns the *jacket*, not the fluid and not the correlation.
It never restates a property equation, and it never computes the hot-gas state
itself — it asks the nozzle solution for it.

### 4.4 Turbomachinery boundary (task §120)

Pump and turbine depend on fluid properties, thermodynamics and rotational
mechanics, and stay entirely outside the compressible module. A turbine
expanding a real gas is *not* the quasi-1D nozzle problem, and modelling it with
`compressible.nozzle` would be a category error.

The one legitimate overlap: a turbine's ideal expansion may use isentropic
relations for a perfect gas. That is `physics.compressible.isentropic` used as
the fundamental relation it is — the correct direction, L2 → L1.

---

## 5. Engine cycle dependency graphs (task §121)

**Propellant path**

```
Fluid properties -> Tank -> (Valve) -> Pump -> (Line, Cooling jacket) -> Injector -> Chamber
```

**Expansion path**

```
Thermochemistry -> Chamber -> Nozzle (compressible) -> Nozzle (rocket) -> Performance
```

**Power loop (gas generator / staged combustion)**

```
Gas Generator / Preburner -> Turbine -> Shaft -> Pump
                                   ^                |
                                   +----------------+
                                     power balance
```

**Thermal loop (regenerative cooling)**

```
Chamber + Nozzle -> hot-gas state -> Cooling jacket -> coolant outlet state -> Feed system
        ^                                                                          |
        +--------------------------------------------------------------------------+
                          coolant is the fuel; its enthalpy returns to the chamber
```

The last two are *loops*, which is exactly why `engine.solver` exists as its own
module: they cannot be resolved by evaluating components in a fixed order.

---

## 6. Which subsystems require iteration (task §122)

| Coupling | Why it iterates | Owner |
| --- | --- | --- |
| Pump / turbine power balance | turbine power depends on flow split, which depends on pump ΔP, which depends on turbine power | `engine.balances` |
| Regenerative cooling | coolant temperature rise changes fluid properties, which change ΔP and h, which change the temperature rise | `engine.solver` + `engineering.cooling` |
| Injector / chamber pressure compatibility | injector ΔP depends on p_c; p_c depends on ṁ through the throat; ṁ depends on injector ΔP | `engine.balances` |
| Cycle flow split (GG, staged) | the fraction sent to the power loop changes both the turbine inlet state and the main chamber MR | `engine.solver` |
| Turbine inlet conditioning | preburner MR sets turbine inlet T, which sets power, which sets required flow, which sets MR | `engine.solver` |
| Expander cycle | turbine power comes entirely from the cooling jacket heat pickup, which depends on chamber conditions set by that same flow | `engine.solver` (the most strongly coupled of the cycles) |
| Tank blowdown | pressurant demand changes ullage state, which changes outflow | `engineering.tank` + `engine.studies` |

**The compressible module itself remains direct and non-iterative at the system
level.** Its internal inverses iterate (`04` §3), but it exposes no coupling that
the engine solver must resolve: given γ, R, p₀, T₀, geometry and back pressure,
it returns an answer in one call. That property is worth protecting — it is what
lets the engine solver treat the nozzle as a cheap, deterministic function inside
its own iteration.

---

## 7. UI component types → future modules

The 16 component types already defined in `ui/engine/model/ComponentRegistry.qml`,
mapped to the engineering module that will eventually give each one behaviour.
**No QML changes; this is the attachment plan.**

| `type` | Category | Future module | Primary physics dependency |
| --- | --- | --- | --- |
| `tank` | fluid | `engineering.tank` | `physics.fluids` |
| `pump` | fluid | `engineering.pump` | `physics.fluids` |
| `valve` | fluid | `engineering.valve` | `physics.fluids` |
| `regulator` | fluid | `engineering.valve` (regulator mode) | `physics.fluids` |
| `orifice` | fluid | `engineering.injector` (orifice primitive) | `physics.fluids`, `physics.compressible.mass_flow` |
| `injector` | combustion | `engineering.injector` | `physics.fluids` |
| `chamber` | combustion | `engineering.chamber` | `physics.thermochemistry`, `physics.compressible` |
| `igniter` | combustion | `engineering.chamber` (ignition sub-model) | `physics.combustion` |
| `nozzle` | expansion | `engineering.nozzle` | **`physics.compressible.nozzle`** |
| `turbine` | power | `engineering.turbine` | `physics.fluids`, `physics.compressible.isentropic` |
| `shaft` | power | `engine.balances` (not a physics component — a constraint) | — |
| `gasgenerator` | power | `engineering.gas_generator` | `physics.thermochemistry` |
| `preburner` | power | `engineering.preburner` | `physics.thermochemistry` |
| `coolingjacket` | thermal | `engineering.cooling` | `physics.heat_transfer` |
| `heatexchanger` | thermal | `engineering.heat_exchanger` | `physics.heat_transfer` |
| `filmcooling` | thermal | `engineering.cooling` (film sub-model) | `physics.heat_transfer` |

Note `shaft`: it is a component in the *editor* because the user draws it, but it
is a **constraint** in the solver (equal speed, power balance), not a device with
its own equations. Recording that now prevents someone writing an
`engineering/shaft.py` full of nothing.

The port `subtype` values already in the registry (`propellant`, `pressurant`,
`fuel`, `oxidiser`, `mixture`, `hot gas`, `shaft`, `wall`) map directly onto the
stream types the network layer will carry, so the graph the user draws is
already, structurally, the graph the solver will need.

---

## 8. Implementation order for the layers above compressible

Not part of Phase 4, but the sequence follows from the dependency map:

1. `physics.fluids` interfaces + a constant-property in-tree provider (unblocks
   every L2 hydraulic module without any external dependency).
2. `engineering.line`, `valve`, `orifice` — the simplest L2 components, and a
   real test of the provider boundary.
3. `physics.thermochemistry` interfaces + a CEA provider.
4. `engineering.chamber` and `engineering.nozzle` (rocket) — the first modules
   that turn compressible results into performance.
5. `engineering.injector`, `tank`, `pump`, `turbine`.
6. `engine.network` + `engine.balances` — with a pressure-fed cycle only.
7. `engine.solver` — and only then the coupled cycles.
8. `physics.heat_transfer` + `engineering.cooling` — deliberately late, because
   it is the most correlation-heavy and the hardest to validate.

Each step is gated by `05` §16 in the same way the compressible module is.
