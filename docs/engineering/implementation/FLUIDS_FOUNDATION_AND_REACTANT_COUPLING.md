# Fluids foundation and reactant enthalpy coupling

# Verdict

**FLUID PROPERTIES & REACTANT STATE COUPLING v1.0 — ACCEPTED**

`physics.fluids` exists as a frozen L1 contract; CoolProp 8.0.0 is validated
and bundled as its production provider; the assigned-enthalpy limitation is
**closed** by a chemically safe sensible-enthalpy correction that NASA CEA
demonstrably consumes; liquid density now comes from the real stream state; and
density impulse is computed from it and available as a trade-study objective.

`06_future_module_dependency_map.md` §8 **step 1**. **No phase number is
assigned** — the authoritative roadmap orders modules, not phases.

---

## Opening baseline

| Gate | Result |
| --- | --- |
| Base (`.venv`) | **6451 passed, 118 skipped**, exit 0 |
| CEA (`.venv-cea`) | **6571 passed, 1 skipped**, exit 0 |
| Frozen Compressible | 22 / 22 byte-identical |
| Thermochemistry / Performance / Trade Study / CEA Provider v1.0 | all four digests reproduced exactly |

Matched the accepted Phase 5G baseline exactly. The tree was clean before any
work began.

---

## Files created

**Production — 15**

| Package | Files |
| --- | --- |
| `rocketforge/physics/fluids/` | `__init__`, `types`, `identity`, `requests`, `states`, `protocols`, `provenance`, `errors` (8) |
| `rocketforge/providers/fluid_properties/` | `__init__`, `constant`, `coolprop` (3) |
| `rocketforge/engineering/propellants/` | `__init__`, `mapping`, `density` (3) |
| `rocketforge/providers/cea/` | `enthalpy_coupling.py` (1) |

Plus `rocketforge/application/analysis/fluid_property_provider.py`,
`fluid_property_service.py`, `fluid_property_controller.py`, and
`rocketforge/application/fluidsmoke.py`.

**Interface** — `ui/pages/FluidPropertiesPage.qml`.

**Tests — 5 files**: `tests/physics/fluids/test_fluid_domain.py`,
`tests/providers/fluid_properties/test_constant_provider.py` and
`test_coolprop_provider.py`,
`tests/providers/cea/test_reactant_enthalpy_coupling.py`,
`tests/engineering/propellants/test_density_and_impulse.py`,
`tests/test_fluids_architecture.py`.

**Documents — 5**: `FLUID_PROPERTIES_API_V1.md`,
`FLUID_PROPERTY_PROVIDER_CONTRACT.md`,
`REACTANT_ENTHALPY_COUPLING_CONTRACT.md`, `DENSITY_IMPULSE_CONTRACT.md`, and
this report, plus `FLUIDS_FOUNDATION_CHECKPOINT.md`.

**Dependency profile** — `requirements-fluids.txt`.

**Artifacts** — `acceptance/fluids_foundation/`, 15 JSON files, 4 freeze
manifests with `.sha256` companions, and `ACCEPTANCE_MANIFEST.md`.

## Files modified

| File | Change |
| --- | --- |
| `rocketforge/providers/cea/mapping.py` | `CEAChamberInput.enthalpy_correction` appended; applied in `solve_chamber_raw`; `build_chamber_input` keyword |
| `rocketforge/providers/cea/provider.py` | `solve_chamber` policy keywords; `_apply_enthalpy_correction`; superseding diagnostic; policy in provenance |
| `rocketforge/application/analysis/trade_study_domain.py` | 4 metrics registered |
| `rocketforge/application/analysis/trade_study_service.py` | `feed_pressure`, stream densities, density metrics |
| `packaging/RocketForge.spec` | conditional CoolProp collection |
| `main.py`, `ui/data/Navigation.qml`, `ui/shell/SideNav.qml` | the new workspace |
| `tests/acceptance/test_propulsion_freeze.py` | v1.1 as current, v1.0 as history, 4 new supersession tests |
| `tests/application/test_trade_study_service.py` | the density rule narrowed — see corrections |
| `docs/engineering/PROPULSION_ANALYSIS_LIMITATIONS.md` | two limitations closed |

---

## Frozen-contract evolution

**Compressible v1.0** — untouched, 22/22 byte-identical.

**Thermochemistry API v1.0** — untouched. `PropellantStream` already carried an
optional `pressure`, so the pressure blocker needed no version bump: it needed
the fluids boundary to *demand* a pressure rather than invent one.

**Ideal Rocket Performance v1.0** — untouched.

**Trade Study API v1.0 — untouched.** This is the §65 preferred outcome and it
was achievable: `engine.studies` is a generic engine that takes metrics from
whatever the evaluator returns, and its metric *table* lives in
`application/analysis`, which no freeze manifest covers. Density impulse
therefore needed no v1.1.

**NASA CEA Provider v1.0 → v1.1.** The correction has to reach the HP
constraint, which is inside the frozen package; no extension point outside it
could do that without reimplementing the chamber solve. So the version was
bumped, additively, and the v1.0 manifest was **kept unmodified** as the record
of what Phase 5G accepted — enforced by four tests.

---

## physics.fluids

8 files, digest `306ec275df25f850…`. Imports `rocketforge.core` and nothing
else in the project; no Qt, no CEA, no CoolProp — asserted per module.

**Public API**: `FluidDefinition`, `OXYGEN`/`METHANE`/`HYDROGEN`, `FluidPhase`,
`FluidProperty`, `PropertyStatus`, `FluidStateRequest`, `FluidState`,
`FluidPropertyProvenance`, `FluidPropertyProvider`,
`FluidPropertyCapabilities`, `FluidPropertyCapability`, and nine errors.
23 declared exports.

**Fluid identity** is `OXYGEN`, upper case, carrying only name, formula, molar
mass and source. A definition with a density would be a second source of truth
competing with the provider. Molar mass is kg/mol; a value above 1 is refused
by name because 31.9988 is g/mol.

**Phase**: `LIQUID`, `GAS`, `SUPERCRITICAL`, `SOLID`, `TWO_PHASE`. **No
`UNKNOWN` member** — a documented departure from the brief's suggested list, and
a deliberate match to `physics.thermochemistry.Phase`: unknown is `None`, and
`None` is never read as GAS. `TWO_PHASE` *is* a member because a saturated
state is an answer, not an absence.

**Properties**: density, specific enthalpy, cp, dynamic viscosity, thermal
conductivity. Canonical SI, and the adapter performs **no unit conversion at
all**, which is the safest possible answer to the unit question.

---

## ConstantPropertyProvider

In-tree, dependency-free, deterministic. Declares neither
`TEMPERATURE_DEPENDENCE` nor `PRESSURE_DEPENDENCE`, carries
`CONSTANT_PROPERTY_APPROXIMATION` in every provenance, and warns on every
result that the requested state did not change the numbers.

A production definition must state a source **and** an envelope: a constant
that claims validity everywhere is claiming to be an equation of state. A
synthetic test model may declare no envelope and must say so.

**The reactant coupling refuses it by name.** A constant-property model returns
the same enthalpy at both states, so the increment would be exactly zero and
indistinguishable from a correct reference-state result — the most dangerous
failure available in that coupling.

---

## Real property provider

| | |
| --- | --- |
| Provider | CoolProp |
| Version | **8.0.0**, pinned in `requirements-fluids.txt` |
| Licence | MIT — redistributable |
| Python | `cp312-abi3` wheel, runs on CPython 3.13.2 |
| Backend | `HEOS` |
| Import | lazy, asserted statically and in a clean subprocess |
| Packaging | 118 files bundled; a real query runs in the packaged build |

---

## Production fluids

| Propellant | Fluid | Status |
| --- | --- | --- |
| LOX | `OXYGEN` | validated, liquid at 90.17 K / 1 atm |
| LCH4 | `METHANE` | validated, liquid at 111.643 K / 1 atm |
| LH2 | `HYDROGEN` | validated, liquid at 20.27 K / 1 atm |
| GOX, GCH4 | — | no bulk-liquid binding; their CEA entries are already temperature-dependent |
| **RP-1** | **none** | **unsupported.** Not a pure fluid and not in the production catalogue; asking raises `UnmappedPropellantError`. No surrogate is substituted |

---

## External property validation

NIST Chemistry WebBook isobaric tables, retrieved 2026-09-06. **An
independent-implementation check, not an independent-model check** — NIST and
CoolProp implement the same reference equations of state here, and saying
otherwise would overstate what this proves.

| Property | Result |
| --- | --- |
| Density | inside box, all three fluids, liquid and vapour |
| **Enthalpy difference** | O₂ 3392.5 vs 3390; CH₄ 6924.4 vs 6930; H₂ 18096.8 vs 18096 J/kg — inside box |
| cp | inside box |
| Viscosity | O₂ and H₂ inside box; **CH₄ not validated** |
| Conductivity | inside box |

42 validated comparisons, all inside boxes derived from printed precision
before comparing.

**Methane viscosity is not validated.** CoolProp uses Quiñones-Cisneros (2006)
friction theory and NIST does not, so the 0.4–1.4 % gap is a model difference
between two correlations rather than evidence about either. Nothing here
consumes viscosity; it blocks the hydraulic components.

---

## Phase validation

| State | Result |
| --- | --- |
| Liquid | all three cryogens at their reference states |
| Gas | O₂ at 95 K, 1 atm |
| Near saturation | O₂ at 95 K, 3 bar — subcooled liquid |
| Two-phase | at exactly `p_sat`: `TWO_PHASE`, every property `TWO_PHASE_AMBIGUOUS`, no value stored |
| Below triple point | refused, range named |

CoolProp does not answer "twophase" for a `(T, p)` pair on the saturation line;
it declines, because the pair does not determine the state. The adapter detects
that case against CoolProp's **own** 1e-4 % band and reports `TWO_PHASE`.

---

## Reactant enthalpy coupling

**CEA explicit h accepted: YES**, through the official
`EqSolver.solve(solution, HP, constraint, p, weights)` path the adapter already
used. No text parsing, no `thermo.lib` edit, no hidden global state.

**CEA chemical reference**: retained entirely. Only a difference crosses.

**Equation**

```
h_corrected = h_CEA_ref + [ h_fluid(T,p) − h_fluid(T_ref,p_ref) ]
```

applied at the mixture as `Δh_mix = Σ wᵢ·Δhᵢ` in J/kg, added to CEA's own
mixture enthalpy before the constraint is formed. Legitimate because
`calc_property(ENTHALPY, …)` is linear in the mass fractions — verified, not
assumed: it reproduces the mass-weighted sum to 0.025 J/kg in 1.58 × 10⁶.

Gate: only reactants whose CEA entry is measurably assigned-enthalpy.
`p_ref = 101325 Pa`, declared once.

## Reference-state identity

| | |
| --- | --- |
| Δh | **exactly 0.0**, both reactants |
| Native chamber | 3598.2854205339845 K |
| Corrected chamber | 3598.2854205339845 K |
| Difference | **0.0** — bit-identical on T, R, M̄, γ_fr, γ_eq |

## Temperature response

| Oxidiser T | Native T | Corrected T | Δh (O₂) |
| --- | --- | --- | --- |
| 86.0 K | 3598.2854205339845 | 3597.50 | −6955 J/kg |
| 88.0 K | 3598.2854205339845 | 3597.88 | −3574 J/kg |
| 90.17 K | 3598.2854205339845 | 3598.31 | +106 J/kg (pressure term) |
| 98.0 K | 3598.2854205339845 | 3599.84 | positive |

Native is identical at every temperature — the limitation, reproduced.
Corrected is strictly monotone. Composition responds because the chamber
temperature does; 28 species on both sides.

## Double-counting

| Control | Result |
| --- | --- |
| GOX/GCH4 with bindings supplied *and* the corrected policy active | **0 corrections applied**, chamber bit-identical |
| Already-temperature-sensitive reactants | never corrected; the gate is the measured behaviour, not a name list |

## Energy / element validation

The provider's own post-validation ran on every corrected solve and passed,
including the element balance. The correction enters reactant enthalpy only;
elemental inventory is untouched.

---

## Stream pressure semantics

| | |
| --- | --- |
| Fuel property pressure | explicit, from the binding / setup |
| Oxidiser property pressure | explicit, from the binding / setup |
| **Chamber pressure reused silently** | **NO** — asserted by an AST audit with a negative control that fires on the substitution |

Not theoretical: at 1 atm a LOX stream requested at 95 K is a **gas**, and the
correction is refused by name rather than computed on the wrong branch.

---

## Liquid density, bulk density, density impulse

| | |
| --- | --- |
| Fuel (LCH4, 111.643 K, 3 bar) | 422.579 kg/m³ |
| Oxidiser (LOX, 90.17 K, 3 bar) | 1141.705 kg/m³ |
| Formula | `ρ_mix = (1 + O/F) / (1/ρ_f + (O/F)/ρ_ox)` |
| Assumptions | separate volumes, additive tanks, no mixing, no ullage, no structure, no stratification — carried on every result |
| Density impulse | `ρ_mix·c_eff`, unit **kg/(m² s)** = N·s/m³ |
| Identity | `ρ_mix·Isp·g₀`, residual **0.0** on every case |
| Hand-checks | ρ_mix 800.0 and I_d 2 400 000.0 exactly, written down before running |

**`density_hint`**: used in physics — **NO**. Used in density impulse — **NO**.
AST audit over every module of this phase, with a two-way negative control.

---

## Trade Study integration

| | |
| --- | --- |
| Implemented | yes |
| API version | **v1.0, unchanged** |
| Objective | `maximize density_impulse` |
| Points | 410 |
| Chemistry solves | **41** |
| Performance solves | 410 |
| **Fluid property evaluations** | **2** |
| Direct-solve parity | **160 comparisons, 0 differences**, exact equality |

A point without a validated density gets `NOT_EVALUABLE`, not `INFEASIBLE` —
Phase 5F semantics, unchanged.

---

## Determinism, state leakage, performance, soak

| Check | Result |
| --- | --- |
| Five identical queries | identical, exact float64 |
| A/B/A/B/A + 20 others + A | `a1==a2==a3==a4`, `b1==b2`, `a≠b` |
| Fluid query, warm | ~0.7 ms (1497/s) |
| 10 800 fluid states | 7.2 s, peak 0.45 MB, same state identical before and after |
| 400 corrected chamber solves | 1.8 s, canonical case unchanged after |
| Corrected chamber solve | ~4.4 ms (225/s) |
| 10 repeated identical studies | all results identical; **+0.0059 MB, non-monotonic** |

---

## Interface

| | |
| --- | --- |
| Fluid Properties workspace | 16th workspace, its own sidebar domain |
| Qt messages | **0**, source and packaged |
| Resolutions / themes | 2560×1440, 1920×1080, 1366×768 · light and dark |
| Thermochemistry corrected mode | policy and correction in provenance |
| Density impulse | available as a Trade Study metric with its ingredients |

---

## Packaged executable

| | |
| --- | --- |
| Files / size | 2 239 / 245.0 MB |
| CoolProp bundled | 118 files |
| `thermo.lib` hash matches accepted | **YES** |
| Real fluid query in the bundle | **YES** |
| Corrected chamber in the bundle | **YES**, bit-identical at reference |
| Density metric in the bundle | **YES**, residual 0 |
| Self-tests | **7 / 7 exit 0**, 0 Qt messages |
| **Source ↔ packaged parity** | **363 fields, 0 differences** |

**Clean-machine caveat**, unchanged from Phase 5G: this establishes
self-containment of the bundle, not verified clean-machine operation.

---

## Tests

| Suite | Result |
| --- | --- |
| Base (`.venv`) | **6648 passed, 154 skipped**, exit 0 |
| CEA + fluids (`.venv-cea`) | **6803 passed, 2 skipped**, exit 0 |
| Repeat | **6803 / 2 — identical** |
| New tests | **+197** base, **+232** in the fluid-enabled environment |

The 154 base skips are the CoolProp- and CEA-requiring tests, which the
fluid-enabled environment runs. No tolerance widened, no test removed, no
unexplained skip.

---

## Architecture

165 acceptance and fluids-architecture tests pass. Every scan has a negative
control beside it, because a scan that passes by looking in the wrong place is
worse than no scan — Phase 5G found four of those in its own audit code.

`physics.fluids` reaches no further than `core`; no provider imports
`application`; CoolProp is never imported at module scope; `density_hint` is
never read; no chamber pressure becomes a fluid pressure; no line, valve,
orifice, injector, pump, turbine, cooling or tank module exists; no device
correlation vocabulary appears.

---

## Corrections made during this work

**1 — Interface defects, found by looking.** The new page shipped three Qt
warnings, then printed its pressure as `300000.000000000`, then turned out to
have **no sidebar entry at all** — it rendered in the smoke test and was
unreachable to a user. All three found by reading a capture.

**2 — Two harness defects of my own.** The reference-state check first
evaluated the fluid at the *feed* pressure while comparing against a reference
at 1 atm, reporting a 0.0218 K "failure" that was a real pressure term measured
against the wrong reference; split into the blocking identity and a separately
recorded pressure result. The study memory measurement retained a 210-entry
signature per round, producing a perfectly linear 0.18 MB "leak" that was
entirely the harness; re-measured at +0.0059 MB, non-monotonic.

**3 — A Phase 5F architecture rule narrowed, deliberately.** That phase banned
*every identifier containing "density"* from trade-study code, because density
then had no validated source and could only have come from `density_hint`. The
blanket form would now forbid correct work. The invariant is asserted directly
instead, the negative control is strengthened to fire on a `density_hint` read
inside a module full of legitimate density code, and a positive assertion was
added that density must arrive through the propellant-metrics layer. The
protection is the same; the overreach is gone.

---

## Known limitations

* **Methane viscosity is not validated** — different correlations, 0.4–1.4 %.
  Blocking for the hydraulic components.
* Three fluids, five properties, no mixture model.
* Single-phase evaluation only; two-phase states are refused, not interpolated.
* The correction is a sensible-enthalpy term: no phase change, no heat of
  solution, no ortho/para hydrogen conversion.
* RP-1 unsupported.
* Bulk density is an additive-volume tank figure, not a stage mass model.
* Liquid reactant temperature is still not a trade-study design variable: the
  physics is now correct, but exposing it as a swept variable is a separate
  decision with its own UI and cache implications.
* CoolProp and NASA CEA remain two independent models; the coupling makes the
  reactant *state* right within CEA's chemistry and reconciles nothing else.

---

## Deferred next work

Per `06_future_module_dependency_map.md` §8 **step 2**:

    engineering.line
    engineering.valve
    engineering.orifice

the simplest L2 components and the first real test of the fluid-property
provider boundary. **Not implemented here**, and blocked first on validating
methane viscosity, which they would be the first to consume.
