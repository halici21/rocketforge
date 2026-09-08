# Phase 5B — Provider-Independent Thermochemistry Core

The first production-code phase of the thermochemistry programme. Builds the
domain language every future provider will speak, and stops before any provider
solves anything.

**Date:** 2026-09-04.
**Type:** production implementation. 13 new modules, 257 new tests, zero new
runtime dependencies, zero changes outside the new package.

---

## 1. Baseline

| Gate | Result |
| --- | --- |
| Opening regression | **5285 passed, 1 skipped**, pytest exit 0, 60.55 s |
| Closing regression, run 1 | **5542 passed, 1 skipped**, pytest exit 0, 47.50 s |
| Closing regression, run 2 | **5542 passed, 1 skipped**, pytest exit 0, 47.77 s |
| Repeatability | identical across both runs |
| Architecture | **41 existing rules green and unmodified**, 18 additive rules added |
| Frozen Compressible | **UNCHANGED** — 22 files byte-identical, opening and closing |
| Frozen manifest digest | `8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502` |

Run directly as `.venv\Scripts\python.exe -m pytest -q`, no pipeline, exit code
recorded. 5542 − 5285 = **257 new tests**.

---

## 2. Phase 5B-0 decision integration

| Item | Status |
| --- | --- |
| ADR-20 (Cantera primary) | **SUPERSEDED**, original text preserved |
| ADR-21 (CEA developer-side) | **SUPERSEDED**, original text preserved |
| ADR-31 (new) | **NASA CEA v3 is the recommended first production provider; Cantera is an independent equilibrium oracle and the future kinetics/transport path** |
| `10_thermochemistry_provider_strategy.md` | superseding banner added at the top; body preserved unchanged |
| OQ-2 | resolved in **Phase 3's favour**; Phase 3 expected a CEA provider and was right |

The ADRs are **marked**, not deleted. They record what was believed and why:
the reasoning was sound, the factual premise about CEA's Python availability
was not. ADR-31 cites the measured evidence — cp313 wheel, Apache-2.0, no
Fortran toolchain, structured API without text parsing, native cryogenic
reactants worth 74.9 K of chamber temperature, native rocket outputs, 19×
faster on a matched workload, PyInstaller PASS with exact parity, and the RP-1311
reference corpus shipped in the package. "It is NASA" is explicitly not a reason.

**No provider dependency was added.** The compiled-dependency decision remains
a Phase 5C question, as the phase brief requires.

---

## 3. Files

### Created — production (13 modules, 4098 lines)

All under `rocketforge/physics/thermochemistry/`:

| Module | Lines | Holds |
| --- | --- | --- |
| `composition.py` | 662 | `Composition`, basis conversion, mean molar mass, elemental inventory, element balance |
| `propellants.py` | 573 | `PropellantDefinition`, `PropellantStream`, `MixtureRatio`, `PropellantPair`, `PropellantPairReferenceCase` |
| `validation.py` | 517 | `IdentityCheck`, `ValidationReport`, nine checks, two aggregates |
| `species.py` | 464 | `ElementalComposition`, `ThermoPolynomial`, `Species` |
| `states.py` | 316 | `ChamberGas`, `GasStation` |
| `protocols.py` | 266 | `ProviderCapability`, `ProviderCapabilities`, `ThermochemistryProvider` |
| `__init__.py` | 237 | the public surface, 70 exports |
| `types.py` | 220 | nine enumerations |
| `requests.py` | 213 | `ChamberEquilibriumRequest`, `ExpansionRequest` |
| `errors.py` | 197 | the error hierarchy |
| `provenance.py` | 166 | `ThermochemistryProvenance` |
| `serialization.py` | 142 | `to_jsonable` |
| `tolerances.py` | 125 | `ThermochemistryTolerances` |

### Created — tests (10 files, 3195 lines, 257 tests)

`tests/physics/thermochemistry/`: `conftest.py`, `test_composition.py` (55),
`test_propellants.py` (39), `test_states.py` (37), `test_species.py` (35),
`test_requests.py` (25), `test_provider_contract.py` (19),
`test_thermochemistry_architecture.py` (18), `test_contract_fitness.py` (15),
`test_serialization.py` (14).

### Created — documentation

* `docs/engineering/THERMOCHEMISTRY_CORE_API_DRAFT.md` — provisional API
* `docs/engineering/implementation/PHASE_5B_CHECKPOINT.md` — live checkpoint
* this report

### Modified

* `docs/engineering/PHASE_5A_SUMMARY.md` — ADR-20/21 superseded, ADR-31 added
* `docs/engineering/10_thermochemistry_provider_strategy.md` — superseding banner

**No production file outside `physics/thermochemistry/` was touched.** No QML
file changed. No requirements file changed. No `.spec` changed.

---

## 4. Domain model

### Species

Identity is `(name, phase)`, exposed as `canonical_id` → `"H2O:gas"`. `H2O(g)`
and `H2O(l)` never compare equal and never share a hash. `Phase` has **no**
`UNKNOWN` member; where a phase may be unknown the field is `Phase | None` and
nothing defaults it to `GAS`.

`display_name` is separate from `name`, so a presentation choice can never
change a machine identity.

Elemental formulae use `float` atom counts (a surrogate formula is fractional)
and arbitrary element symbols — F, Cl, metals, `e-` all work with no change to
the balance algorithm.

Molar mass is **kg/mol**, stored and never recomputed: different databases use
different atomic weights, and `formula_molar_mass(weights)` cross-checks against
*caller-supplied* weights rather than a shipped periodic table. The admissible
range `[1e-6, 1.0]` kg/mol catches the kg/kmol provider unit by three orders of
magnitude.

A surrogate must name its source, because two RP-1 fits are two species.
Species names are **not** length-limited: NASA CEA's 15-character cap is a
provider constraint and lives in the adapter's name map.

`ThermoPolynomial` implements NASA-7 and NASA-9 evaluation on **caller-supplied**
coefficients — it knows no species and can invent no data. Out-of-range
evaluation raises. Range joins are tested for value continuity and deliberately
**not** for slope continuity, which the published fits do not guarantee.

### Composition

| Decision | Value |
| --- | --- |
| Canonical basis | mole fraction |
| Alternate basis | mass fraction, explicit |
| Basis implied anywhere | **never** — no constructor omits it |
| Sum policy | exact 1 accepted; within 1e-9 canonicalised **and recorded**; outside refused |
| Arbitrary rescaling | **refused** in `from_fractions`; `from_weights` normalises because the caller declared weights |
| Negative fractions | refused; `fraction_negative_tol` is 0, so nothing is clamped |
| Zero components | preserved |
| Trace species | preserved, no storage cutoff |
| Ordering | sorted, so equality and encoding are order-independent |

`mole_to_mass_fractions` and `mass_to_mole_fractions` are pure functions that
accept molar masses in any consistent unit, so an adapter can use them before
converting. Round trips close to 1e-12 or better, and hand-computed references
(10 / 90 g/mol, giving mass fractions of exactly 0.1 and 0.9) are checked
independently rather than by inverting the production call.

**Naming deviation, recorded:** Phase 5A `09` §5.1 called this `Mixture` with an
implicit mole basis. It is `Composition` with an explicit basis — strictly
stronger, and consistent with `09` §4.3's ban on implicit bases.

### Mean molar mass and gas constant

`M = Σ X_i M_i` on a mole basis, `1/M = Σ Y_i / M_i` on a mass basis, and a
validator that the two agree. `R = Ru / M` uses
`core.constants.UNIVERSAL_GAS_CONSTANT` — **reused, not redefined**. The
constant lives in a frozen file, which was read and not modified, so no
`FROZEN_CORE_EXTENSION_DECISION_REQUIRED` arose.

### Element conservation

`ElementalInventory` always carries an explicit basis —
`PER_MOLE_OF_MIXTURE` or `PER_KILOGRAM_OF_MIXTURE` — and inventories on
different bases refuse to be compared. The residual is scale-aware and cannot
divide by zero for an element absent from both sides. Tolerance:
`element_balance_rel_tol = 1e-8`, chosen with an order of magnitude of margin
over the 1.04e-09 Phase 5B-0 measured on a real solve.

### Propellants

`PropellantDefinition` (the substance, at its **reference** condition) is kept
strictly apart from `PropellantStream` (the **actual** operating condition).
That separation is load-bearing: Phase 5B-0 measured 74.9 K of chamber
temperature between LOX at 90.17 K and notional LOX at 298 K.

`density_hint` is display-only, and a test greps the package to prove no code
path reads it. `provider_names` is a generic `{provider_id: name}` mapping,
replacing Phase 5A's `cea_name` so no public field names one vendor.

`mass_flow` is **optional** on a stream — a chamber equilibrium needs the ratio,
not the absolute rate — and `mixture_ratio_from_streams` requires it and says so.

### O/F

**O/F = oxidiser mass ÷ fuel mass, always.** `MixtureRatio` refuses 0, negatives,
NaN and infinity, and clamps nothing. A monopropellant is **not** `O/F = 0`; the
refusal message says so. `equivalence_ratio(stoich)` requires the stoichiometric
value explicitly — no hidden constant. `fuel_oxidiser_ratio()` is named so it
cannot be mistaken for O/F.

`mixture_ratio_from_streams(fuel, oxidiser)` takes fuel first and returns
oxidiser-over-fuel, **checking the roles**: swapped arguments raise rather than
inverting silently. The orientation test uses asymmetric flows (1.0 and 3.4
kg/s) so an inversion cannot hide.

### Pairs and reference cases

`PropellantPair` carries **no performance and no `optimal_of`**. Phase 5B-0
measured c\*, Tc and Isp peaking at O/F 2.85, 3.75 and 3.30 for LOX/CH₄ — three
different maxima — so "optimum O/F" is undefined without an objective.
`stoichiometric_of_mass` *is* allowed, because it does not depend on an
operating point.

`PropellantPairReferenceCase` binds every observation to its conditions and
requires a unit for each. Observations live in a mapping rather than as typed
attributes, so the record cannot be mistaken for a computed result. No
historical table was transcribed; that is a later reference-data task.

---

## 5. State contracts

Phase 5A's canonical names and mandatory field sets, unchanged.

| | `ChamberGas` | `GasStation` |
| --- | --- | --- |
| Mandatory | `temperature` (**T0**), `gamma`, `gas_constant`, `molar_mass`, `composition` | `pressure`, `temperature` (static), `gamma` |
| Optional | pressure, density, enthalpy, entropy, cp, cv, cp_frozen, cp_equilibrium, gamma_frozen, gamma_equilibrium, speed_of_sound, condensed_mass_fraction, request, provenance | composition, molar_mass, gas_constant, density, enthalpy, entropy, cp, cv, cp_frozen, cp_equilibrium, gamma_frozen, gamma_equilibrium, speed_of_sound, velocity, mach, area_ratio, condensed_mass_fraction, provenance |

**Additions Phase 5B-0 forced:** `gamma_frozen`/`gamma_equilibrium` and
`cp_frozen`/`cp_equilibrium`. The spike measured γ_s = 1.1336 against a frozen
cp/cv of 1.1985 on the same real state — 5.7 % apart. One field could not carry
both.

`ChamberGas.temperature` is a **stagnation** temperature and says so.
`GasStation.composition is None` **means the chamber's composition** (frozen
flow), a documented convention rather than missing data.
`condensed_mass_fraction is None` means **unknown**, never zero.

Neither record carries `c_star`, `cf`, `isp`, `thrust`, `l_star`, `throat_area`
or any chamber dimension, and an AST-based architecture test enforces it.

### State identities

| Identity | Result |
| --- | --- |
| `R = Ru / M` | **PASS** |
| `cp - cv = R` | **PASS**, conditional on the fields being present |
| `gamma = cp / cv` | **PASS**, applied to the **frozen** gamma only |
| `p = rho R T` | **PASS**, conditional |
| `state M = composition M` | **PASS** when a species table is supplied |

`check_gamma_definition` deliberately does **not** apply to the equilibrium
exponent: it is a different quantity, and applying the identity would fail a
correct provider.

A check that could not run is `applicable=False` and is **never counted as a
pass**. `ValidationReport.skipped` reports them separately.

---

## 6. Request contract

`ChamberEquilibriumRequest(fuel, oxidiser, oxidiser_fuel_ratio,
chamber_pressure, chemistry_mode=EQUILIBRIUM, equilibrium_constraint=HP,
product_species=None, trace_threshold=None)`.

Validates on construction, so malformed input is refused **before a provider is
consulted**. That guard exists because Phase 5B-0 measured NASA CEA silently
accepting a negative temperature and a negative pressure and returning without
raising.

Absent by design: total mass flow, nozzle geometry, chamber dimensions, and
every provider-specific flag — no `n_frz`, no `iac`, no `ac_at`, no `**kwargs`.
Tests assert each of those names is not a field.

`EquilibriumConstraint` exposes **HP and SP only**. Providers support TP, UV, TV
and SV; exposing all of them would make the enum a description of CEA.

**Frozen chemistry is not constant gamma**, and `ExpansionMode`'s docstring says
so: a frozen mixture still has a temperature-dependent cp. `FreezeLocation` is
explicit — `CHAMBER` or `THROAT` — because a boolean cannot express a difference
that changes the exit state.

---

## 7. Provider contract

```python
class ThermochemistryProvider(Protocol):
    provider_id: str
    version: str
    capabilities: ProviderCapabilities
    def provenance(self) -> ThermochemistryProvenance: ...
    def solve_chamber(self, request) -> Solution[ChamberGas]: ...
```

`ProviderCapability` has 21 members, shaped so both candidates can be honest:
CEA declares `LIQUID_REACTANTS`, `ROCKET_PERFORMANCE`, `AREA_RATIO_EXPANSION`
and `NATIVE_EQUILIBRIUM_GAMMA`; Cantera declares `KINETICS` and none of those.
A test asserts exactly that asymmetry.

Declaring `ROCKET_PERFORMANCE` says a provider can supply oracle values. It does
**not** move ownership of performance out of `engineering.nozzle`, and a test
asserts `ChamberGas` still has no such fields.

Capabilities are **declared, never discovered**. `require()` raises
`UnsupportedCapabilityError` naming the missing capability. An undeclared range
is treated as an absence of information, not as a claim of validity.

`ThermochemistryProvenance` carries provider id, versions, database name,
version and SHA-256, chemistry mode, constraint, species set, reactant
conditions, options and warnings — and **no timestamp**, so two identical
calculations produce equal provenance.

### Error and status policy

| Outcome | Mechanism |
| --- | --- |
| Malformed input | `InputError` subclass, **raised**, before any provider runs |
| Physical no-solution / not converged | a `Solution` whose status says so — **not** an exception |
| Provider unavailable | `ProviderUnavailableError`, raised |
| Unsupported capability | `UnsupportedCapabilityError`, raised immediately |

`ProviderUnavailableError` documents that a guarded import must catch
`ValueError` as well as `ImportError`, because NASA CEA loads its thermodynamic
database at **import** time.

**Two refinements of Phase 5A, documented not silent:** the protocol takes a
request object rather than names plus scalars (5B-0 proved reactant temperature
and phase are first-class), and it returns `Solution[ChamberGas]` rather than a
bare value (this project's own policy reports non-convergence rather than
raising it, and CEA exposes exactly such a flag). Neither weakens ADR-30's
intent: adapters stay thin and no provider type crosses the boundary.

---

## 8. Validation and mutation proofs

Every critical validator has a mutation proof that **asserts the fixture
actually changed** before asserting the validator notices. This is the direct
answer to the Phase 4G defect where a self-test mutated a bound method, silently
changed nothing, and reported success.

| Mutation | Proof |
| --- | --- |
| Composition sum perturbed beyond tolerance | **PASS** |
| Product species dropped | **PASS** |
| Molar mass scaled ×2 | **PASS** |
| Atom count altered (CO₂ → CO₃) | **PASS**, and names `O` as the worst element |
| `R` scaled ×1.001 | **PASS** |
| `M` scaled ×1000 (the kg/kmol slip) | **PASS** |
| `cv` scaled ×1.01 | **PASS** |
| `gamma_frozen` set to 1.4 | **PASS** |
| Density scaled ×1.02 | **PASS**, residual matches 0.02/1.02 analytically |
| State `M` against its own composition | **PASS** |
| Nothing is silently repaired | **PASS** |

**Vacuous mutation checks: none.** Every proof includes an explicit
`assert mutated != original, "the mutation must bite"`.

One mutation proof reports an honest **limit** rather than a success: swapping
two molar masses leaves the round trip closing, because the conversion remains
self-consistent. The test says so and checks the mass fractions differ instead.

Two of my own fixtures were caught by these validators during development — an
arbitrary `M_BAR` that did not match its composition, and an inconsistent `R`/`M`
pair in the headless script. Both are recorded in the test files as small
evidence that the checks work.

---

## 9. Contract fitness against the real providers

`test_contract_fitness.py` maps the **recorded output of NASA CEA 3.3.4 and
Cantera 3.2.0** — the `acceptance/phase_5b0/` artifacts — into these records,
through one mapping function with **no provider branch**.

| Question | Answer |
| --- | --- |
| Composition preserved? | yes, all 9 species, values to full precision |
| Phase preserved? | yes |
| Provenance preserved? | yes, including species set and reactant conditions |
| Units unambiguous? | yes; kg/kmol→kg/mol and bar→Pa happen once, visibly |
| Both gammas survive? | yes, and the test asserts they are >5 % apart |
| Both cp values survive? | yes; Cantera's absent equilibrium cp maps to `None`, not a fabricated number |
| Provider-specific dumping ground needed? | **no** |
| Contract biased toward one provider? | **no** — both map through the same function |

**A real finding came out of this.** Mapped CEA output *fails* the strict
`state_identity_rel_tol` of 1e-9 on `cp − cv = R` and `p = ρRT`, because CEA
computes them with its own pre-2019 universal gas constant while RocketForge
recomputes R from CODATA — a 5.7e-06 discrepancy. The response was **not** to
loosen the strict tolerance. A separate named category was added,
`provider_identity_rel_tol = 1e-5`, with the measurement behind it, and a test
proves it is still tight enough to catch a 1 % density error. Cantera, which
uses the CODATA value, passes even the strict tolerance — the contrast is the
evidence that the category is about a specific provider's constants rather than
about sloppiness.

---

## 10. Architecture

| Rule | Result |
| --- | --- |
| 41 existing rules | **green and unmodified** |
| Thermochemistry imports only `core` and itself | **PASS** |
| Thermochemistry → compressible | **absent** |
| **Compressible → thermochemistry** | **absent** (new additive rule; the layer matrix could not express it, since both are in `physics`) |
| No `cea`/`cantera`/`rocketcea`/`CoolProp`/SciPy/Qt imports | **PASS** |
| No NumPy import | **PASS** — not needed, so not taken |
| No equilibrium solver defined | **PASS** (AST check on definitions) |
| No c\*/Cf/Isp/thrust defined | **PASS** (AST check) |
| No chamber-geometry fields | **PASS** |
| No public field named after a vendor | **PASS** |
| No test fixture imported by production | **PASS** |
| Headless with Qt blocked | **PASS**, in a subprocess |
| Compressible still works without thermochemistry | **PASS**, in a subprocess |
| External-consumer import | **PASS** |
| `__all__` complete and honest | **PASS**, 70 names, nothing leaked |
| API documented as provisional | **PASS** |

**One collection defect found and fixed by the full gate.** The new
architecture test was first named `test_architecture.py`, colliding with
`tests/test_architecture.py`; with no `__init__.py` files pytest could not
import both and the whole suite errored during collection. The subset runs had
passed. Renamed to `test_thermochemistry_architecture.py`. Worth recording: a
green subset is not a green suite.

---

## 11. Dependencies and environment

| Check | Result |
| --- | --- |
| `requirements.txt` changed | **NO** |
| `requirements-dev.txt` changed | **NO** |
| Main `.venv` gained `cea` | **NO** |
| Main `.venv` gained `cantera` | **NO** |
| Main `.venv` gained `rocketcea` / CoolProp | **NO** |
| New runtime dependencies | **NONE** |
| QML files changed | **NONE** |
| Application layer changed | **NONE** |
| Engine Design changed | **NONE** |
| Executable rebuilt | **NO** — no UI path consumes this package yet, and a headless import test covers the real risk |

---

## 12. Deliberately not implemented

NASA CEA adapter · Cantera adapter · RocketCEA · CoolProp · equilibrium solver ·
Gibbs minimisation · kinetics · transport properties · fluid-property provider ·
c\* · Cf · Isp · thrust · chamber geometry · L\* · injector · cooling · pump ·
turbine · engine cycle · trade-study engine · Pareto scoring · thermochemistry
UI · production propellant catalogue.

`GammaStrategy` exists as a **data contract only**; no gamma reduction is
implemented and none may be selected implicitly.

---

## 13. Self-review

**Scientific.** H₂O(g) and H₂O(l) stay distinct: yes. RP-1 representable as a
sourced surrogate: yes. Propellant as a blend: yes. Every composition states its
basis: yes. Mole/mass round trip: yes. Both mean-molar-mass paths agree: yes.
Elemental inventory without a provider: yes. A future provider checkable for
element conservation: yes. O/F unambiguously oxidiser/fuel by mass: yes. LOX at
90 K separate from its reference state: yes. Chamber state carrying Tc, M̄, R,
cp, cv, γ, composition and provenance without Isp: yes. Frozen chemistry
representable without implying constant γ: yes. Condensed species representable
and detectable: yes.

**Provider.** CEA results map in: yes, demonstrated on recorded output. Cantera
results map in: yes, same function. CEA can expose extra capabilities without
forcing Cantera to lie: yes. Database SHA preserved: yes. Unsupported capability
representable: yes. Provider failure distinct from invalid input: yes. Raw
provider objects stay behind the adapter: yes, and a test walks every field.
Phase 5B imports neither provider: yes.

**Architecture.** Compressible byte-identical: yes. Dependency direction
preserved: yes. Qt-free: yes. No global provider state: yes. Records immutable:
yes. Public import intentional: yes. Works from a script without the GUI: yes.
Phase 5C can add CEA without redesigning this layer: yes — the fitness tests
are the evidence.

**Trade-study readiness.** Future sweeps over O/F, Pc, propellant pairs and
reactant temperatures: all expressible. Provider/model provenance preserved:
yes. Reference cases condition-bound: yes. No universal "optimal O/F" defined:
correct, and asserted by a test.

---

## 14. Deviations from Phase 5A, recorded

| # | Deviation | Justification |
| --- | --- | --- |
| V1 | `Mixture` → **`Composition`** with an explicit basis | An implicit basis is the ambiguity `09` §4.3 forbids elsewhere; strictly stronger contract |
| V2 | `cea_name` → **`provider_names` mapping** | Phase 5B spec §206 forbids a public field named after one vendor; same intent, generalises |
| V3 | Protocol takes a **request object** | 5B-0 proved reactant temperature and phase are first-class inputs |
| V4 | Protocol returns **`Solution[ChamberGas]`** | `core/errors.py` policy reports non-convergence; CEA exposes such a flag |
| V5 | `PropellantStream.mass_flow` **optional** | A chamber equilibrium needs the ratio, not the rate (spec §192) |
| V6 | Added `provider_identity_rel_tol` | Measured: CEA's pre-2019 Ru puts a 5.7e-06 floor under provider identity checks |

No `PHASE_5A_SPEC_CONFLICT`, no `FROZEN_CORE_EXTENSION_DECISION_REQUIRED`, no
`DATA_MODEL_BLOCKER`, no `PROVIDER_CONTRACT_BLOCKER`.

---

## 15. Open issues

None.

---

## 16. Recommended Phase 5C

**NASA CEA v3 Production Thermochemistry Provider.**

| Item | Detail |
| --- | --- |
| Package | `rocketforge/providers/cea/` |
| Dependency decision | **first**: whether `cea` may enter `requirements.txt`, given the deliberately minimal runtime. Owner's call; everything below assumes yes |
| Core | `solve_chamber(request) -> Solution[ChamberGas]`, HP equilibrium |
| Cryogenic reactants | per-reactant temperature vectors; `O2(L)`, `CH4(L)`, `H2(L)`, `RP-1` |
| Composition mapping | `dict[str, float]` → `Composition`, complete, mole basis |
| Unit conversion | bar→Pa, kg/kmol→kg/mol, kJ→J, once and visibly |
| Pre-provider validation | already done by the request; the adapter adds range checks against declared capabilities |
| Provenance | `cea.__version__`, `lib_version()`, `thermo.lib` SHA-256, species set, mode |
| Condensed phases | compute the fraction from the **composition**, never from `num_condensed` |
| Name mapping | `provider_names["cea"]`, enforcing the **15-character** limit at the adapter |
| Constants | recompute R from RocketForge's Ru; use `provider_identity_rel_tol` for identity checks |
| Error mapping | `ImportError`/`ValueError` → `ProviderUnavailableError`; out-of-range → `ProviderDomainError`; `converged=False` → `Status.NOT_CONVERGED` |
| Input guards | validate T and P before the call — CEA accepts negatives silently |
| Execution | serial in-process; no thread pool (5B-0 measured 0.85× at four threads) |
| Caching | cache the initialised solver: 0.216 ms cold-setup versus 44 µs warm |
| Conformance | reuse the contract tests; point them at the real adapter |
| Reference validation | transcribe RP-1311 cases with rounding boxes |
| Cantera oracle | optional, dev-only, skipped when absent |

No UI in Phase 5C.
