# 08 — Thermochemistry Architecture

Where combustion chemistry lives in RocketForge, what it owns, what it is
forbidden to own, and why the boundaries are drawn where they are.

**Status:** specification. Nothing in this document is implemented. Phase 5A
designs; Phase 5B builds.

**Phase 3 precedence.** Documents `01`–`07` already fixed several boundaries for
this layer. Where they did, this document elaborates and never redesigns. The
canonical type names are Phase 3's: `ChamberGas` and `GasStation`, not any new
coinage. One internal tension inside Phase 3 itself is recorded in §5.3.

---

## 1. The one-sentence version

`physics.thermochemistry` turns *propellants and a chamber pressure* into *a gas
with properties*, and hands that gas to the frozen compressible subsystem, which
has never heard of chemistry and never will.

---

## 2. Where it sits

Phase 3 (`01` §3, `06` §2) already placed this layer. Phase 5A does not move it.

```
    L0  core                    units, Solution, errors, tolerances, Brent, provenance
         |
    L1  physics.compressible    FROZEN v1.0 -- gamma-based gas dynamics
        physics.fluids          single-species thermophysical properties
        physics.thermochemistry <-- THIS LAYER: reacting mixtures
         |
    L2  engineering.chamber     L*, contraction, residence time
        engineering.nozzle      thrust, Cf, c*, Isp, contours
         |
    L3  engine.*                network, balances, cycles, solver
         |
    L4  providers.*             Cantera / CEA / CoolProp adapters
         |
    L5  application.*           controllers, view models
```

`physics.thermochemistry` depends on `core` and nothing else (`06` §2). It does
**not** import `physics.compressible`, even though its output feeds it: the
handshake is a data contract, not a call. That direction is what lets the
compressible module stay frozen while this layer evolves.

The layer numbering is a dependency ordering, not a runtime call stack.
`providers` sits at L4 because it depends on the L1 protocols; at runtime it is
`application` (L5) that constructs a provider and injects it downward.

---

## 3. What this layer owns

`06` §2 grants this layer `ChamberGas`, `GasStation` and the provider protocol,
and lists its outputs as T₀, γ, R, M̄ and composition. The table below is that
grant, itemised.

| Owns | Not this layer |
| --- | --- |
| `Species` — a chemical species and its thermodynamic data | fluid transport correlations (`physics.fluids`) |
| `PropellantDefinition` — a substance usable as a reactant | tank sizing, feed pressure (`engineering.tank`) |
| `PropellantStream` — a flowing quantity of one propellant at a state | injector element design (`engineering.injector`) |
| `Mixture` — composition of a reacting or product mixture | chamber geometry (`engineering.chamber`) |
| `MixtureRatio` — the canonical O/F definition and its conversions | mixture-ratio *optimisation* (`engine.studies`) |
| `ChamberGas` — the equilibrium product gas (Phase 3 name) | L\*, residence time (`engineering.chamber`) |
| `GasStation` — a thermochemical state at an expansion station | nozzle geometry, contours (`engineering.nozzle`) |
| `ThermochemistryProvider` — the protocol | the CEA or Cantera *implementation* (`providers.*`) |
| `ChemistryMode` / `ExpansionMode` — equilibrium, frozen, frozen-at-throat | which mode a study should use (`application`) |
| provenance for every computed state | citation formatting (`application`) |

## 4. What this layer must never own

Stated as prohibitions because each is a temptation with a plausible excuse.

| Prohibition | The excuse it defeats |
| --- | --- |
| **No thrust, Cf, c\*, Isp** | "c\* is just a chamber property" — it is not; it is a performance figure, and `06` §2 assigns performance to `engineering` (ADR-15) |
| **No geometry objects** — no `AreaDistribution`, no contour, no station list | "equilibrium expansion needs a nozzle" — it needs a scalar; see §5.3 |
| **No chamber dimensions, L\*, residence time** | "residence time decides whether equilibrium is reached" — true, and that judgement belongs to `engineering.chamber`, which may then *choose* a chemistry mode |
| **No external library imports** | "Cantera is pure Python now" — the protocol belongs to physics, the implementation to `providers` (`06` §3) |
| **No Qt** | the same acceptance criterion the compressible layer passes |
| **No fluid transport properties** | "I need LOX density at the injector" — that is `physics.fluids`; see §6 |
| **No kinetics in v1** | "finite-rate would be more accurate" — it would also be a different validation problem; see `11` §9 |
| **No mutation of `physics.compressible`** | "variable γ would be easy to add" — ADR-14 and the v1.0 freeze both forbid it |

---

## 5. The handshake with frozen Compressible v1

### 5.1 The chain

Fixed by `06` §4.1 and unchanged here:

```
    fuel + oxidiser + O/F + p_c
            |
            v   ThermochemistryProvider.equilibrium_chamber()
    ChamberGas { temperature, gamma, gas_constant, molar_mass, cp,
                 composition, provenance }
            |
            v   engineering.chamber  (reduces to a single-gamma model)
    PerfectGas(gamma, R) + p0 + T0
            |
            v   physics.compressible.nozzle.solve()      <-- FROZEN, untouched
    NozzleSolution { regime, M(x), p(x), T(x), ... }
            |
            v   engineering.nozzle
    F, Cf, c*, Isp
```

### 5.2 Two things about this that matter more than they look

**The adapter is in L2, not L1.** `engineering.chamber` performs the
`ChamberGas → PerfectGas` reduction, because choosing *which* γ to freeze is an
engineering judgement about a particular analysis, not a fact about the
chemistry. `12` §5 specifies the named strategies. `physics.thermochemistry`
never constructs a `PerfectGas`, which is also what keeps it from importing
`physics.compressible`.

**The reduction is lossy, and the loss is quantified, not hidden.** A single γ
across a large expansion is wrong by a knowable amount; `12` §6 requires every
such result to carry the strategy used and a stated error character. The fix is
a separate equilibrium-expansion path (`11` §6), never a γ(x) hook bolted into
the frozen module (ADR-14).

### 5.3 An internal Phase 3 tension, recorded

Two Phase 3 statements pull in opposite directions:

* `01` §5 specifies `expand(self, chamber: ChamberGas, area_ratio: float,
  mode: ExpansionMode) -> GasStation` — an **area ratio** crosses into this
  layer.
* `06` §2 says `physics.thermochemistry` never owns **nozzle geometry**, and
  `02` §1.5 says the same of `GasStation`.

This is not a Phase 5A deviation to report as `PHASE_3_SPEC_CONFLICT` against a
Phase 5A design; it is an ambiguity *within* Phase 3, and it is resolved here in
the way that keeps both statements true:

> A dimensionless scalar area ratio is a **boundary condition**, not geometry.
> The layer accepts the number, never an `AreaDistribution`, never a contour,
> never an axial station list, and it stores no area in any returned state.

The resolution is forced by the physics, not by taste. An equilibrium expansion
has a varying γ, so the area–Mach relation the frozen module implements does not
apply to it; only the provider, which knows the composition at every pressure,
can close an area-ratio condition. Refusing the scalar would make equilibrium
expansion unimplementable. `09` §9 therefore keeps Phase 3's `expand()`
signature verbatim and **adds** a pressure-driven sibling, because extension is
not contradiction — and because `expand_to_pressure()` is the primitive that the
area-ratio form is built on.

---

## 6. The boundary with `physics.fluids`

These two L1 modules are easy to confuse and must not be merged.

| Question | Module | Why |
| --- | --- | --- |
| What is the density of liquid oxygen at 90 K, 3 MPa? | `physics.fluids` | single species, no reaction |
| What is the viscosity of RP-1 at 300 K? | `physics.fluids` | single species, transport property |
| What is the saturation pressure of methane at 110 K? | `physics.fluids` | single species, phase equilibrium |
| What is the enthalpy of liquid methane *as a reactant* at 111 K? | **`physics.thermochemistry`** | a formation enthalpy plus a sensible term, on the species' own thermodynamic basis |
| What is the equilibrium temperature of LOX/CH₄ at O/F 3.4, 10 MPa? | **`physics.thermochemistry`** | reacting mixture |
| What is γ of the combustion products? | **`physics.thermochemistry`** | reacting mixture |

**The rule.** `physics.fluids` answers questions about *a substance*.
`physics.thermochemistry` answers questions about *a reaction and its products*.
A propellant appears in both, wearing different hats: as a fluid it has a
density the injector needs; as a reactant it has a formation enthalpy the
chamber needs. `09` §4 keeps those two faces in one type without letting either
module compute the other's answer.

**Why the reactant enthalpy is thermochemistry's and not fluids'.** A
`FluidState` enthalpy is referenced to whatever datum its library uses — CoolProp
sets its own zero per fluid. Reaction energetics require every reactant and
product on **one** absolute datum: elements in their reference state at 298.15 K.
Mixing the two is the classic way to get a flame temperature that is confidently
wrong, so the datum is a property of this layer and is stated in `09` §3.4.

The overlap is real and is resolved by ownership, not by cleverness: the
reactant enthalpy at injection temperature is thermochemistry's, and it may
*consume* a temperature or a phase that came from a fluid calculation upstream.

---

## 7. Directory layout

`01` §3 reserves `physics/thermochemistry/interfaces.py` and the four
`providers/` packages. Filled in here.

```
    rocketforge/physics/thermochemistry/
        __init__.py             public namespace, __all__, no external imports
        interfaces.py           ThermochemistryProvider protocol, capabilities
                                (the file Phase 3 named)
        species.py              Species, SpeciesDatabase protocol
        propellants.py          PropellantDefinition, PropellantStream, blends
        mixture.py              Mixture, MixtureRatio, composition conversions
        states.py               ChamberGas, GasStation
        modes.py                ChemistryMode, ExpansionMode enums
        provenance.py           ThermochemistryProvenance record

    rocketforge/providers/
        cantera/                CanteraProvider          (optional dependency)
        cea/                    RocketCEAProvider        (optional dependency)
        tabulated/              TabulatedProvider        (in-tree data)
```

Note what is **absent**: no `equilibrium.py` solving Gibbs minimisation inside
`physics`. Phase 5A's position is that RocketForge does not write its own
equilibrium solver in v1 — see `10` §3 and ADR-19. The physics layer owns the
*contract*; a provider owns the *solution*.

Errors reuse `core`'s hierarchy plus the three provider errors Phase 3 already
named in `01` §5 (`ProviderUnavailableError`, `ProviderDomainError`,
`ProviderFluidUnknownError`); this layer adds no parallel error module.

---

## 8. Import rules, restated for this layer

| From | To | Allowed |
| --- | --- | --- |
| `physics.thermochemistry` | `core` | yes |
| `physics.thermochemistry` | `physics.compressible` | **no** — data contract only |
| `physics.thermochemistry` | `physics.fluids` | **no** in v1; see §6 and OQ-4 |
| `physics.thermochemistry` | `providers.*` | **no** |
| `physics.thermochemistry` | Cantera / CEA / CoolProp | **no** |
| `physics.thermochemistry` | PySide6 | **no** |
| `providers.cantera` | `physics.thermochemistry` | yes — that is the direction |
| `engineering.chamber` | `physics.thermochemistry` | yes |
| `application.*` | both | yes — it chooses and injects the provider |

The architecture suite (41 rules, unchanged through Phase 4G) needs additions in
Phase 5B to enforce the new rows. Those are **additive**; no existing rule is
weakened or relaxed. See `13` §8.

---

## 9. Why a protocol and not a base class

Same reasoning as `physics.fluids` (`01` §5): a `Protocol` lets a provider be
any object with the right shape — a Cantera adapter, a CEA wrapper, a lookup
table, a stub in a test — without inheriting from a physics type. It also keeps
the physics layer importable with none of them installed, which is the property
that makes `pytest` run on a clean checkout.

---

## 10. Failure philosophy, inherited

The compressible subsystem's rules apply here unchanged, because they are what
made it trustworthy:

* malformed input **raises**; a physically unattainable request returns a
  `Solution` with `no_solution` and a diagnostic;
* nothing is silently clamped — not a mixture ratio, not a temperature, not a
  condensed-phase fraction;
* every returned state carries provenance naming the provider, its version and
  its options;
* no result implies more precision than the underlying data supports;
* an unsupported propellant is an explicit refusal, never a substitution.

`11` §8 adds one rule specific to this layer: **a state that the downstream
model cannot represent is refused, not approximated.** The concrete case is
condensed-phase products entering a single-phase quasi-1D nozzle.

One inherited rule deserves restating in chemical terms, because this is the
layer where it will be tempting to break it: **a published CEA output table is
never the solver.** A stored table may be a *reference case* in a test, or a
declared `tabulated` provider that says so in its provenance and refuses to
extrapolate. What must never appear is a code path where a user's input is
interpolated in a shipped results table and returned as if it had been computed.
RocketForge already holds this line for compressible flow and holds it here for
the same reason.
