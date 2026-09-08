# Phase 5G — Integrated propulsion analysis acceptance / freeze

# Verdict

**PROPULSION ANALYSIS v1.0 — ACCEPTED / FROZEN**

Thermochemistry, Ideal Rocket Performance and Trade Study are frozen as v1.0
over frozen Compressible v1, with the NASA CEA v3 provider frozen separately at
its own v1.0. Every gate below passed; no tolerance was widened, no test was
removed, no case was skipped, and the two product defects found during the
phase were fixed rather than documented around.

Not a feature phase: no new physics, no new design variable, no new optimiser,
no UI redesign. The one API change is a hardening — three public reference
tables became read-only.

---

## Opening baseline

| Gate | Result | Accepted baseline | Match |
| --- | --- | --- | --- |
| Base (`.venv`) | 6390 passed, 118 skipped, exit 0, 58.99 s | 6390 / 118 | ✅ |
| CEA (`.venv-cea`) | 6510 passed, 1 skipped, exit 0, 59.26 s | 6510 / 1 | ✅ |
| Frozen Compressible | 22 / 22 byte-identical | 22 / 22 | ✅ |

Compressible digest
`8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502`, verified by
recomputing each file's recorded hash against the Phase 4G manifest. The tree
was clean before any freeze work began, so nothing in this report is measured
against a moved baseline.

---

## Files created

**Production — 2**

| File | Purpose |
| --- | --- |
| `rocketforge/core/freeze.py` | `FrozenFile`, `manifest_text`, `overall_digest`; the manifest algorithm, stated in full in prose |
| `rocketforge/application/shellsmoke.py` | `--selftest-workspaces`: walks the navigation model and renders every workspace at three resolutions in both themes |

**Tests — 1**

`tests/acceptance/test_propulsion_freeze.py` — 61 tests: an independent
reimplementation of the digest, a mutation proof, the freeze boundary, the
public contract (enum members, dataclass field names and order, immutability),
the accidental-export policy, the lazy CEA import, and the reporting-threshold
boundary.

**Harnesses — 7**, under `experiments/phase_5g/`: `api_surface_audit.py`,
`contract_audit.py`, `integrated_acceptance.py`, `determinism_and_soak.py`,
`generate_freeze_manifests.py`, `package_audit.py`,
`architecture_and_benchmarks.py`.

**Documents — 7**: `THERMOCHEMISTRY_API_V1.md`, `ROCKET_PERFORMANCE_API_V1.md`,
`TRADE_STUDY_API_V1.md`, `PROPULSION_ANALYSIS_API_V1.md`,
`PROPULSION_ANALYSIS_LIMITATIONS.md`, `PHASE_5G_CHECKPOINT.md`, and this report.

**Artifacts** — 26 JSON files and 8 capture directories under
`acceptance/phase_5g/`, including `ACCEPTANCE_MANIFEST.md`.

## Files modified

| File | Change | Behaviour |
| --- | --- | --- |
| `rocketforge/providers/cea/propellants.py` | `PRODUCTION_PROPELLANTS`, `CEA_REACTANT_TEMPERATURE_RANGES` → `MappingProxyType` | every read identical; mutation now raises |
| `rocketforge/providers/cea/species.py` | `CEA_FORMULAS` → `MappingProxyType` | as above |
| `ui/components/RFEngineeringTable.qml` | header `Text` anchored both sides, `elide: Text.ElideRight`, alignment from the column's `align` | a label that already fitted renders identically; a long one elides instead of overprinting |
| `main.py` | `--selftest-workspaces` dispatch | new diagnostic only |
| three API drafts | superseded banners pointing at the v1 documents | documentation only |

---

## Defects discovered during Phase 5G

**1 — Public mutable reference tables (product, fixed).**
`PRODUCTION_PROPELLANTS`, `CEA_REACTANT_TEMPERATURE_RANGES` and `CEA_FORMULAS`
were plain public `dict`s holding data that validation depends on: which
reactant names exist, which temperature range refuses a stream, which element
formulas the balance check uses. Nothing in the codebase wrote to them, but a
public mutable dict is a public mutation point on the far side of a freeze, and
a wrong answer produced through a mutated table would carry full provenance
saying it was right. Now `MappingProxyType`, with the full CEA suite green
afterwards. The only API change of the phase, and it makes the contract
stricter rather than different.

**2 — Table headers could overprint their neighbours (product, fixed).**
`RFEngineeringTable`'s header `Text` was anchored on one side only, so it had
no width, and a header longer than its column printed across the next one. Two
Trade Study headers were illegible at 1920×1080. Found by reading a capture,
not by a test — worth recording, because 134 captures passed a zero-Qt-message
gate while showing it.

**3–5 — Three defects in my own audit code (harness, fixed).** The parity
comparator counted 35 `nan` / `nan` pairs as differences, because Python
reports `nan != nan`; two recorded NaNs are the same recorded value, while a
NaN against a number still differs, and the rule is now checked both ways. The
solve-count comparison was reading wall-clock timing fields alongside the
counts. The dependency scan counted relative imports as third-party, because
`from .analysis import x` puts `analysis` in `node.module`; corrected, the real
answer is `PySide6` and `numpy`.

None of the three was resolved by relaxing a tolerance, and each correction was
re-run against a negative control that must fail.

---

## API audit

`acceptance/phase_5g/api_surface_audit.json`, over the five Phase 5 packages.

| | |
| --- | --- |
| Declared exports (`__all__`) | 160 |
| Accidental exports | **0** |
| Reachable beyond `__all__` | submodule names and the `annotations` `__future__` flag only |
| Mutable module-level containers | **0** (was 3) |
| Unfrozen public dataclasses | **0** |
| Exports defined outside `rocketforge` | **0** |
| Undocumented exports | **0** |

The reachable-but-undeclared residue is asserted rather than assumed, by
`test_only_all_is_public_and_the_rest_is_a_submodule_or_a_future_flag`: every
name reachable on a package and absent from `__all__` must be either a
submodule of that package or the `__future__` flag. Anything else fails.

## Thermochemistry API v1

`THERMOCHEMISTRY_API_V1.md`. Owns `ChamberGas`, `GasStation`, the composition
types, the request types and the provider protocol. Owns no provider, no
nozzle, no performance quantity and no chamber sizing.

The public state carries **two** isentropic exponents and never a bare `gamma`.
Frozen: 13 files, digest
`44312c23c71cfd527f8ac621e62c69e50d7c63354fbb4b3b8de2096fd2e93453`.

## CEA provider contract

`CEA_PROVIDER_CONTRACT.md`, versioned separately from the domain it implements
so that a provider fix does not reopen the Thermochemistry API. NASA CEA 3.3.4;
`thermo.lib` SHA-256
`8e5df1cca92d4a48663d1ee5a1372e6508c59cddc2247ceeca32f041a03ec52a` — identical
to the hash accepted at Phase 5C and to the hash inside the packaged build.

The provider is an optional dependency: `import cea` happens lazily inside the
adapter, and a subprocess test asserts the whole performance chain runs in a
clean interpreter with no `cea`, `cantera` or `CoolProp` entry in `sys.modules`.
Frozen: 11 files, digest
`0a46b5f089a9cc7a47278eecd0868b8d68730aa1abbf9c5775e35cb70eb9285a`.

## Rocket Performance API v1

`ROCKET_PERFORMANCE_API_V1.md`. Owns c\*, Cf, momentum thrust, pressure thrust,
total thrust, c_eff and Isp — RocketForge's own, computed over frozen
Compressible and never restating it. Owns no chemistry and no second copy of
the gas dynamics.

A static test asserts that no module outside
`engineering/nozzle/performance.py` defines a function named
`characteristic_velocity`, `thrust_coefficient`, `specific_impulse` or
`effective_exhaust_velocity`. Frozen: 6 files, digest
`d07f4ff9017efdfe0340bfb5514dea9774498500262e3212aa68d51a22756787`.

## Trade Study API v1

`TRADE_STUDY_API_V1.md`. Owns design variables, enumeration and stage keys,
hard constraints, feasibility, objectives, Pareto dominance, optional weighted
scoring, comparison and the run lifecycle. Owns no physics, no provider and no
Qt — the engine is tested against a synthetic evaluator with no rocket behind
it. Frozen: 12 files, digest
`912065266fccc6d54776de3ebcac33f83ea7c209378b4a87e3e900061b8c409d`.

---

## Dependency architecture

`acceptance/phase_5g/architecture_audit.json`. The import graph is read from
the syntax tree, so a function-local import counts exactly as a top-level one.

| | |
| --- | --- |
| Layer-order violations (`core → physics → engineering → engine → providers → application → ui`) | **none** |
| Cycles between layers | **none** |
| Python files under `ui/` | **none** |
| Modules importing `rocketforge.providers` outside `application/` | **none** |
| Third-party runtime imports | `PySide6`, `numpy` |
| scipy, pandas, scikit-learn, pymoo, DEAP, Optuna, Cantera, RocketCEA, CoolProp | **absent** |

`engine.studies` imports nothing from `physics`, `engineering` or `providers`:
the evaluator is a protocol that the application implements.

## Compressible v1 dependency

22 / 22 files byte-identical to the Phase 4G freeze, digest unchanged. Phase 5
consumes `physics.compressible` only through public symbols — `PerfectGas`,
`isentropic`, `mass_flow`, `nozzle` — and an AST audit with a negative control
asserts that no Phase 5 module names a private symbol from it. c\* is derived
by one substitution from the frozen choked-flow relation rather than written
out again, and Γ(γ) is the vandenkerckhove function already living in
`mass_flow`.

## Units

Canonical SI everywhere below the application boundary; conversion happens at
that boundary and nowhere else. All 18 published metrics were compared against
the canonical unit for their quantity: **no disagreements**. Isp is in
**seconds** and c_eff in **m/s**, and they are separate published fields rather
than one number with a unit switch.

## O/F semantics

Oxidiser mass / fuel mass, everywhere, with no second convention anywhere in
the stack. The audit collected all six public names carrying the quantity and
confirmed that each states the orientation in its own docstring, so the meaning
never depends on having read a different file.

## Gamma semantics

Two exponents, never merged and never defaulted:

| | |
| --- | --- |
| γ_s | the isentropic exponent of the **shifting** expansion |
| γ_fr = cp/cv | the **frozen** exponent |

They differ by 5.56 % on the canonical case — larger than every model
difference in this report. **No bare public `gamma` exists**; the audit
searched for one and found none. The fields are `gamma_equilibrium` and
`gamma_frozen`.

Reducing a two-gamma `ChamberGas` to a one-gamma `PerfectGas` requires both a
`GammaStrategy` (where along the flow) and a `ChamberGammaBasis` (which of the
two), **neither with a default**. Omitting either is a `TypeError`, not a quiet
choice.

## Tolerance inventory

`acceptance/phase_5g/tolerance_inventory.json` — every threshold with its
value, its owning module and its stated reason. Four scalars, plus the named
tolerance sets:

| Constant | Value | Owner | Kind |
| --- | --- | --- | --- |
| `IDENTITY_TOLERANCE` | 1e-12 | `engineering/nozzle/validation.py` | verification |
| `GAS_CONSTANT_IDENTITY_TOLERANCE` | 1e-08 | `engineering/chamber/handshake.py` | physics precondition |
| `SINGLE_PHASE_CONDENSED_LIMIT` | 1e-06 | `engineering/chamber/handshake.py` | **physics** |
| `CONDENSED_REPORTING_THRESHOLD` | 1e-06 | `application/analysis/thermochemistry_service.py` | **presentation** |

Every one is documented at its definition. `GAS_CONSTANT_IDENTITY_TOLERANCE`
exists for a measured reason: CEA uses a pre-2019 universal gas constant
(8314.51 against CODATA's 8314.46261815324, 5.7e-06 apart), so an exact
identity would refuse a correct provider.

## Presentation-vs-physics thresholds

The two 1e-06 constants are numerically equal and semantically unrelated, which
is exactly the confusion worth guarding against.

`SINGLE_PHASE_CONDENSED_LIMIT` decides what the model **refuses**.
`CONDENSED_REPORTING_THRESHOLD` decides which sentence the interface
**prints**: it changes no composition, deletes no species, alters no
`ChamberGas` field, touches no element balance and never reaches a provider.

Enforced structurally — the presentation constant is defined in the application
layer, and a test asserts that no module in `core`, `physics`, `engineering`,
`engine` or `providers` references it. The exact fraction is displayed beside
the sentence in every case, so the threshold never hides a number.

## Assigned-enthalpy limitation

Preserved end to end, and deliberately not solved here.
`acceptance/phase_5g/assigned_enthalpy_chain.json`:

| Stage | Behaviour |
| --- | --- |
| Provider | warns `PROVIDER_ASSIGNED_ENTHALPY_REACTANT`, carrying both the requested and the assigned temperature |
| Performance | inherits the warning; the result is a `warning` outcome, not a failure |
| Trade study | aggregates it across **5 / 5** points |
| Feasibility | still **feasible** — a caveat does not withhold a number |

Liquid reactant temperature is therefore not offered as a design variable: a
sensitivity curve for a quantity the provider is not modelling would read as
"temperature barely matters". Deferred to reactant-enthalpy / fluid-property
coupling.

## Condensed-phase semantics

`acceptance/phase_5g/condensed_chain.json`, one chain per side of the boundary:

| Condensed fraction | Thermochemistry | Performance | Study |
| --- | --- | --- | --- |
| below the limit | reported with its exact value, `CONDENSED_TRACE_ACCEPTED` | solves normally | succeeds |
| present (1.65e-02) | valid state, condensed products reported | reduction **refused**, `CONDENSED_PHASE_PRESENT` | a chamber-temperature study still succeeds; an Isp study fails at that point |

Refused, never averaged into the gas. A mixed-phase chamber still yields valid
thermochemistry; only a study requiring a *performance* metric is unevaluable
there, and it says so by name rather than returning a number.

---

## Thermochemistry validation

Carried forward from Phase 5C and unchanged: Level A adapter regression,
Level B external published NASA CEA case, Level C Cantera cross-check — three
levels that are never merged into one number. Every Level B value falls inside
its source's rounding box, and those boxes were derived from printed precision
before the comparison ran.

Provider identity is re-verified here: version 3.3.4, `thermo.lib` hash
matching the accepted one in source and in the bundle.

## Performance validation

Two kinds, kept apart by name.

**Same-model validation residuals.** c\* against an independent analytic
perfect-gas form: **4e-16** across five gases. The internal identities against
frozen Compressible: worst residual **0.0** across the Phase 5G acceptance
matrix (3.7e-16 across the wider Phase 5E matrix).

**Cross-model differences.** RocketForge frozen basis against CEA
frozen-at-chamber, LOX/LCH4, O/F 3.4, 100 bar, Ae/At 40 — c\* 4.35e-04,
Cf 5.04e-03, Isp 5.48e-03, exit temperature 1.26e-01. No CEA mode is
like-for-like, because RocketForge v1 is calorically perfect and every CEA mode
is calorically imperfect. These are model differences, labelled as such
everywhere they appear, including in the interface.

## Performance identity matrix

`check_identities` recomputes 6 scale-free and 9 scaled relations on every
result at `IDENTITY_TOLERANCE = 1e-12`:

```
c*    = sqrt(R T0)/Γ(γ) = p_c·A_t/ṁ
Cf    = Cf_momentum + Cf_pressure = F/(p_c·A_t)
F     = ṁ·V_e + (p_e − p_a)·A_e = Cf·p_c·A_t
c_eff = F/ṁ = Cf·c*
Isp   = c_eff/g₀
```

Worst residual across the acceptance matrix: **0.0**. Scale-free quantities are
identical across three engine scales; absolutes double exactly when the throat
area doubles; the `THROAT_AREA` ↔ `MASS_FLOW` round trip closes to 1.7e-16.

The interface states, on the same panel that shows them, that internal
consistency is not validation.

## Ambient matrix

`acceptance/phase_5g/ambient_matrix.json`, one nozzle across five ambient
pressures:

| Property | Result |
| --- | --- |
| c\* | invariant — chamber and throat, no ambient term |
| Exit Mach, pressure, temperature, velocity | invariant, by exact equality |
| Isp | monotone decreasing with ambient pressure |

Ambient pressure does not enter the internal solution; it enters exactly one
term. The exit state comes from `critical_pressure_ratios`, which needs no back
pressure and therefore works at p_a = 0, where a back-pressure ratio would fall
outside the classifier's domain.

## Pressure-thrust sign matrix

`Cf_pressure = ((p_e − p_a)/p_c)·ε`, signed, never clamped:

| Ambient | Regime | Sign |
| --- | --- | --- |
| vacuum | underexpanded by definition | **positive** |
| below p_e | underexpanded | **positive** |
| p_a = p_e | ideally expanded | **zero** |
| above p_e | overexpanded | **negative** |
| far above p_e | overexpanded | **negative** |

Recorded as `positive / positive / zero / negative / negative`. A clamp at zero
would make an overexpanded engine look as good as an ideally expanded one; a
test asserts the negative value survives all the way to the published field.

## CEA oracle boundary

The provider's own c\*, Cf and Isp exist and are reachable, and they are an
oracle. Four properties hold them there:

1. **Different types.** `OracleOutcome` carries plain floats under their own
   names; it is not an `IdealRocketPerformance`, and the two do not interchange.
2. **No import path.** `performance_service` does not import
   `performance_oracle`, and `trade_study_service` does not either — asserted.
3. **Explicit invocation.** It runs only from a user action; no nozzle input
   reaches it.
4. **A separate CEA run.** A chamber state carries no performance figure, so
   none can be derived from one.

A trade study's physics is CEA for the chamber and RocketForge for the nozzle,
and every study's provenance record states that in a field.

## External NASA references

`performance_nasa_cea_2002_lox_lh2.json` — NASA-GLENN CEA, 18 October 2002,
McBride and Gordon; LOX/LH2, O/F 6.0, 1000 psia, Ae/At 40. Produced by the 2002
Fortran implementation, while the provider under test is the v3
re-implementation, so neither number produced the other.

| Comparison | c\* | Isp | Verdict |
| --- | --- | --- | --- |
| published vs the CEA oracle | 3.82e-06 in a 6.61e-06 box | 1.32e-05 in 1.16e-04 | **PASS — validation** |
| published vs RF, frozen basis | 1.70e-02 | 3.36e-02 | model difference |
| published vs RF, equilibrium basis | 4.99e-06 | 7.13e-03 | model difference |

The dataset records which claim it supports in its own `validates` field, so
the distinction cannot be lost by someone reading only the numbers. The
equilibrium-basis agreement is **not** counted as validation: γ_s is defined as
the isentropic exponent of the shifting expansion, so a constant-γ_s model
approximates it by construction.

## Trade Study cache

A stage key holds the values of every variable at or before that stage and
nothing else. That is the whole mechanism, and it is why reuse is exact rather
than approximate.

| Grid | Points | Chemistry solves |
| --- | --- | --- |
| 41 O/F × 10 ε | 410 | **41** |
| fixed chamber, 10 ε × 5 p_a | 50 | **1** |
| 5 O/F × 4 p_c × 3 ε | 60 | **20** |
| soak, five studies | 14 865 | **405** (36.7×) |

Reported as a measured call count from a counting provider stub, never as an
estimate.

## Direct-solve parity

Caching may change a call count; it may not change a number. Every one of 164
cached points was compared against invoking `solve_case` and
`solve_performance` directly for that exact point, across seven fields:
**1148 comparisons, 0 differences**, by exact float equality rather than a
tolerance.

## Decision-layer independence

| Separation | Enforced by |
| --- | --- |
| physics failure ≠ infeasibility | `EvaluationStatus` and `Feasibility` are two enums |
| warning ≠ failure ≠ infeasibility | a warning point evaluates, stays feasible, ranks and scores |
| constraint ≠ penalty | `ConstraintOutcome` has no penalty field, asserted |
| score ≠ Pareto | dominance never reads a weight |
| score ≠ feasibility | asserted directly |
| missing required metric ≠ infeasible | `NOT_EVALUABLE`, with the upstream numbers kept |

Editing an objective, a constraint limit or a weight costs **0 chemistry and 0
performance solves**, with the raw metrics identical before and after —
measured through the functions, through the Qt controller, and in the packaged
build.

## Pareto validation

Dominance: no worse on every objective, strictly better on at least one.
Checked against a **hand-computed six-point fixture** whose expected front was
written down rather than produced by the implementation — covering dominated
points, a tie, mixed directions, and a mutation proof that requires the fixture
to change before the front is allowed to follow.

Failed, infeasible and non-finite points are excluded from the front and remain
in the result set. Reweighting the score leaves the front byte-identical.
Study B: 164 points, 40 feasible, 124 infeasible, **8 Pareto-efficient**.

## Score validation

Optional, off by default, and study-relative. Min–max normalisation over the
feasible evaluated set; a zero-span component contributes
`ZERO_SPAN_COMPONENT = 1.0` rather than dividing by zero. Checked against
hand-computed normalised values and weighted totals (0.25 / 0.50 / 0.75 for
weights 3 and 1).

A score never enters dominance, never enters feasibility and never enters
physics. Wherever a score appears, the interface says that the same design
scores differently in a study with a different range.

## Density impulse exclusion

Not implemented. `density_hint` is display-only reference metadata by the Phase
5A/5B contract, and an AST audit — with a two-way negative control, because the
first version of this scan flagged its own disclaimer text — asserts that no
Phase 5F or 5G module references it in any expression.

`ρ·Isp·g₀` computed from it would be a physical claim resting on a number never
validated as a physical property, at a temperature, pressure and phase it does
not record. Deferred until a validated fluid-property source exists.

---

## Integrated canonical cases

| Case | Result |
| --- | --- |
| LOX/LCH4 canonical | T₀ 3598.2854 K, c\* 1810.0129 m/s, Cf 1.889026, Isp 348.6575 s; identity chain recomputed independently, worst residual **0.0** |
| Scaled | scale-free quantities identical across three scales; absolutes exact; round trip 1.7e-16 |
| Ambient sweep | c\* and exit state invariant, Isp monotone, signs as tabulated |
| Assigned enthalpy | warning propagated provider → performance → study, still feasible |
| Condensed | below-threshold solves; present refuses the reduction by name |
| Integrated studies | 164 points, 41 chamber solves, 8 Pareto points |

## Provenance chain

`acceptance/phase_5g/provenance_chain.json` — **PASS**. One trade-study point
(O/F 3.5, ε 40) was rebuilt from nothing but its recorded provenance: study
fingerprint → design point → thermochemistry request → provider and version →
database SHA-256 → chamber state → gamma strategy and basis → performance model
→ nozzle and ambient condition → raw metrics → the decision definition that
judged them.

The reconstruction matches on chamber temperature (3607.1756631152743 K) and
Isp (347.1604931607501 s) exactly.

Provenance is read from the result's **own** snapshot, so editing the interface
cannot relabel a stored result.

## Determinism

Exact float64 equality, not a tolerance — a provider returning a slightly
different chamber on a second call is precisely the defect being looked for,
and a tolerance would hide it.

| Check | Result |
| --- | --- |
| Five identical chamber solves | identical, including composition ordering |
| Five identical performance solves | identical |
| Three identical trade studies | identical, including point order, feasibility, Pareto and score |
| Study definition fingerprint | stable across runs |

## State leakage

A/B/A/B/A at the chamber: `a1 == a2 == a3`, `b1 == b2`, and `a ≠ b` — the last
clause matters, because three equal results would also be produced by a stuck
cache. A/B/A at performance and at the study level: identical. Case A after 50
unrelated cases: unchanged.

## Soak tests

| | |
| --- | --- |
| Design points | **14 865** across five studies |
| Chamber solves | **405** |
| Reduction against naive | **36.7×** |
| Wall clock | 29.06 s |
| Peak memory | 21.1 MB |

No degradation across the run, and the last study's results match the first
study's on the overlapping grid.

## Memory

Ten identical 820-point studies in one process, each followed by an explicit
collection:

```
retained MB: 1.391 1.417 1.418 1.418 1.420 1.420 1.420 1.420 1.420 1.421
```

**+0.030 MB over ten rounds**, plateauing from round two and not monotonic; all
ten results identical. That is allocator noise, not a leak. A repeat at the
20 000-point cap peaks at the same 33.08 MB as the first run.

## Cancellation/recovery

`acceptance/phase_5g/error_recovery.json` — **PASS**. After a refused chamber
(a reactant outside CEA's stated temperature range), a refused nozzle regime
(an internal normal shock), and a study in which all 4 points failed, the
canonical case re-solves byte-identically to before. A refusal leaves no
residue.

The trade study runs chunked on a `QTimer` with no worker thread, so a
cancellation is a state transition rather than a killed thread.

## Performance benchmarks

| Operation | Time |
| --- | --- |
| Thermochemistry, cold | 3.31 ms |
| Thermochemistry, warm (median of 20) | 0.55 ms |
| Ideal performance (median of 200) | 0.027 ms |
| Trade study, 100 points | 0.047 s |
| Trade study, 1 000 points | 0.358 s |
| Trade study, 4 040 points | 1.435 s |

Recorded as a change detector, not as a pass/fail gate: a microbenchmark
threshold fails on a busy machine and teaches people to ignore the suite.
`MAX_STUDY_POINTS = 20 000` was chosen from this curve — 4.73 s and 33.1 MB at
the cap, tripling at 40 000 as the quadratic Pareto term turns.

---

## Source UI acceptance

| | |
| --- | --- |
| Workspaces rendered | 15, plus Engine Design |
| Captures | 78 workspace tours + 56 shell = **134** |
| Qt messages | **0** |
| Resolutions | 2560×1440, 1920×1080, 1366×768 |
| Themes | light and dark |
| Large study | 3050 points, 61 chamber solves, table 0.46 s, plot 0.83 s |

No unguarded synthetic desktop input was used anywhere; the tours drive
controllers and the QML object tree directly.

## Existing UI regression

Every pre-Phase-5 workspace was walked at all three resolutions in both themes.
The compressible pages are unchanged, and a Phase 5D architecture rule — now
naming the analysis domains explicitly rather than excluding them — asserts
that no compressible page was modified by this phase.

The one interface change is `RFEngineeringTable`'s header, which affects every
engineering table: a header that already fitted renders identically, and one
that did not now elides instead of overprinting.

## Packaging

Clean PyInstaller directory build from `.venv-cea`, the only environment that
may build the official executable. All five diagnostics pass on the built
application, each exit 0:

`--selftest-thermochemistry`, `--selftest-thermochemistry-ui`,
`--selftest-rocket-performance`, `--selftest-trade-study`,
`--selftest-workspaces`.

## Package-content audit

| | |
| --- | --- |
| Files | 2 117 |
| Size | 192.9 MB |
| `thermo.lib` hash matches the accepted one | **YES** |
| Cantera, RocketCEA, CoolProp | **absent** |
| pytest, SciPy, pandas, scikit-learn, pymoo, DEAP, Optuna | **absent** |
| `tests/`, `experiments/` | **not bundled** |

**Caveat, stated rather than glossed:** this audit inspects the bundle's
contents and runs the bundle's own diagnostics. No machine without the
development environment was used, so the claim is **self-containment of the
bundle**, not verified clean-machine operation.

## Source ↔ packaged parity

| Tour | Fields | Differences |
| --- | --- | --- |
| Thermochemistry UI | 4 253 | **0** |
| Rocket Performance | 5 013 | **0** |
| Trade Study | 6 936 | **0** |
| Workspaces | 448 | **0** |
| **Total** | **16 650** | **0** |

Compared by exact equality, with two NaNs treated as the same recorded value
and a NaN against a number treated as a real difference. Solve counts match:
**PASS**. Provenance matches: **PASS**.

## Public API contract tests

`tests/acceptance/test_propulsion_freeze.py`, 61 tests. What they pin:

* every enum's exact member set — `Status`, `Severity`, `GammaStrategy`,
  `ChamberGammaBasis`, `PerformanceScaleMode`, `EvaluationStatus`,
  `Feasibility`, `ObjectiveDirection`, `ConstraintOperator`
* every public dataclass's field **names and order**, so a reordering is a
  breaking change and is caught as one
* immutability — frozen dataclasses reject assignment; the three reference
  tables reject mutation
* the accidental-export policy
* the lazy CEA import, in a clean subprocess
* the reporting threshold's boundary behaviour, and its absence below the
  application layer

---

## Freeze boundaries

Frozen: the four production packages, source only.

Not frozen, deliberately: tests, acceptance harnesses, experiment scripts, QML,
screenshots, generated artifacts, `__pycache__`. A test asserts that no
manifest contains a test, harness, artifact or QML path — freezing the tests
would make fixing a test a contract change, and freezing QML would make a label
edit one.

## Freeze manifest algorithm

`rocketforge-freeze-manifest/1`, stated in full in `rocketforge/core/freeze.py`
and repeated inside every manifest file:

1. collect the files, each path relative to the repository root
2. convert to POSIX form
3. sort lexicographically by UTF-8 code point
4. SHA-256 each file's exact bytes
5. one line per file: `<hex><two spaces><path>` and a newline
6. encode that text as UTF-8
7. the overall digest is the SHA-256 of those bytes

| Check | Result |
| --- | --- |
| Reimplemented independently from the prose, agrees | **PASS**, all four |
| `.sha256` companion checkable with `sha256sum -c` | **PASS**, all four |
| A one-byte mutation changes the file hash **and** the digest | **PASS** |
| No absolute path, timestamp or user name in any manifest | **PASS** |

This closes the Phase 4G gap, where per-file hashes were checkable but the
overall digest was not reconstructible without the code that produced it.

## Frozen manifests

| Contract | Version | Files | Digest |
| --- | --- | --- | --- |
| THERMOCHEMISTRY API | 1.0 | 13 | `44312c23c71cfd527f8ac621e62c69e50d7c63354fbb4b3b8de2096fd2e93453` |
| IDEAL ROCKET PERFORMANCE API | 1.0 | 6 | `d07f4ff9017efdfe0340bfb5514dea9774498500262e3212aa68d51a22756787` |
| TRADE STUDY API | 1.0 | 12 | `912065266fccc6d54776de3ebcac33f83ea7c209378b4a87e3e900061b8c409d` |
| NASA CEA PROVIDER | 1.0 | 11 | `0a46b5f089a9cc7a47278eecd0868b8d68730aa1abbf9c5775e35cb70eb9285a` |
| COMPRESSIBLE FLOW (Phase 4G) | 1.0 | 22 | `8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502` |

Regenerated at the close of the phase, with unchanged digests.

## Final test counts

| Suite | Result |
| --- | --- |
| Base (`.venv`) | **6451 passed, 118 skipped**, exit 0 |
| CEA (`.venv-cea`) | **6571 passed, 1 skipped**, exit 0 |
| CEA, repeat run | **6571 passed, 1 skipped** — identical |
| Phase 5G additions | **+61** |

No tolerance widened, no test removed, no case skipped, no provider
substituted. The 118 base-environment skips are the CEA-requiring tests, which
the CEA environment runs.

## Architecture-rule counts

**305 architecture and freeze tests pass** across `tests/test_architecture.py`,
the three UI architecture suites, the thermochemistry and CEA architecture
suites, and `tests/acceptance/test_propulsion_freeze.py`.

Each is a static or AST assertion rather than a naming convention: layer order,
absence of cycles, no Python under `ui/`, no provider import outside
`application`, no private Compressible symbol, one owner per equation, no
`density_hint` in physics or decision code, no presentation threshold below the
application layer, no global-optimum wording, and no provider name in a
RocketForge-computed provenance row.

---

## Known limitations

Full list with reasons in `PROPULSION_ANALYSIS_LIMITATIONS.md`. In brief:
assigned-enthalpy liquid reactants; one production provider; five propellants;
equilibrium chamber only; **ideal means ideal** — no efficiency, loss,
divergence or separation model, so every figure is an upper bound on a real
engine; the constant-property reduction, which makes no CEA mode like-for-like;
three nozzle regimes, with everything else refused by name; mixed-phase
chambers refused rather than averaged; a sampled design space rather than an
optimiser, so nothing claims a global optimum; a study-relative score; a
20 000-point cap; no density impulse; and model assumptions that are not design
variables.

Every one is stated on the screen where a user could walk into it.

## Deferred work

| | |
| --- | --- |
| Reactant enthalpy / fluid-property coupling | unblocks liquid-temperature sensitivity and, with it, density impulse |
| Validated liquid density / density impulse | needs the above |
| Delivered-performance efficiency and loss models | c\* and Cf efficiency, divergence, viscous, boundary-layer |
| Real nozzle separation | the current flag is a rule of thumb, not a prediction |
| Finite-rate chemistry | between the frozen and equilibrium brackets |
| Additional production providers | the protocol exists; a second implementation does not |
| Expanded propellant catalogue | a data-curation effort with its own provenance requirements |
| Engine component design integration | injector, chamber geometry, cooling |
| Cycle analysis | pumps, turbines, feed system, balances |

## Recommended next development phase

**`physics.fluids` — `FluidState`, the `FluidPropertyProvider` protocol, and a
constant-property in-tree provider.**

This is not a fresh proposal. It is **step 1** of the implementation order in
`06_future_module_dependency_map.md` §8, and the only remaining unimplemented
L1 physics module. Steps 3 and 4 of that list — `physics.thermochemistry` with
a CEA provider, then `engineering.chamber` and `engineering.nozzle` — are what
Phases 5B through 5F delivered and this phase freezes. Step 1 was passed over
to reach a complete rocket-performance chain first; taking it now restores the
roadmap's own order.

Three independent reasons converge on it:

1. **The roadmap says so**, and states there that it unblocks every L2
   hydraulic module without any external dependency.
2. **It is what the deferred limitations are waiting on.** Both open items —
   reactant enthalpy coupling and validated liquid density — need exactly one
   thing: a validated fluid-property source behind a protocol. Neither can be
   closed before it exists, and both are currently the honest reason a user
   cannot vary liquid reactant temperature or see density impulse.
3. **It is a shape this codebase has already proven twice.** Domain protocol in
   `physics`, adapter in `providers`, wiring in `application` — the same
   structure as thermochemistry, except that the constant-property model is a
   real in-tree provider, so the boundary is exercised from day one without
   adding a dependency.

Scope it as a physics-and-contract phase: no device correlations, no external
library, no new UI beyond what property inspection needs. `engineering.line`,
`valve` and `orifice` — step 2, and the first genuine test of that provider
boundary — follow it.

**Not recommended next.** Anything needing a converged engine (`engine.solver`
and the cycles) is several roadmap steps away and would require components that
do not exist. `physics.heat_transfer` and `engineering.cooling` are deliberately
last in §8, being the most correlation-heavy and the hardest to validate. And
delivered-performance efficiency models would reopen a contract frozen today,
which deserves a better reason than proximity.

**Phase numbering is not assigned here.** The authoritative roadmap orders
modules, not phase numbers; naming the next phase is the owner's call.
