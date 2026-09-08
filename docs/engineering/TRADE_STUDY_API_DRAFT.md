> **Superseded.** This draft was promoted to [TRADE_STUDY_API_V1.md](TRADE_STUDY_API_V1.md) by Phase 5G and frozen as TRADE STUDY API v1.0. It is kept for history; the v1 document is normative.

# Trade Study — API

Phase 5F. A generic design-space engine, and the RocketForge evaluator that
points it at thermochemistry and ideal rocket performance.

**This phase writes no physics.** It consumes the accepted Phase 5D and 5E
stack and adds the layer above it: design variables, constraints, feasibility,
objectives, Pareto analysis, an optional weighted score.

---

## Layer ownership

Doc 06 already assigned *"parametric studies, trades, sensitivity"* to
`engine.studies` at L3, and that is where the generic core went. It sits above
`engineering`, which doc 01 and doc 06 reserve for **the design of one physical
component** — a design-space engine is not a component, and putting it there
would have made `engineering` mean two things.

```
  ui/                     QML. No decision algorithm, no formula.
       ^
  application/            TradeStudyController -> trade_study_service
       ^                  the only layer that may wire a provider
       |
  engine/studies/         THE GENERIC CORE. No rockets, no Qt, no provider.
       ^
  engineering/nozzle      Phase 5E. Owns c*, Cf, thrust, c_eff, Isp.
  physics/thermochemistry Phase 5B/5C. Owns the chamber state.
```

L3 is a permission, not an obligation. The generic core imports **nothing**
from `physics`, `engineering`, `providers` or Qt — a test asserts it per module
— and the whole decision layer is exercised by synthetic evaluators with no
physics at all. That is what makes it possible to say the algorithms are
correct independently of what they will later be pointed at.

The arrow runs one way. `physics` and `engineering` import no study module; a
nozzle must be usable without a study around it.

---

## The chain, and why each link is separate

```
DESIGN VARIABLE -> PHYSICS -> RAW RESULT -> CONSTRAINT -> FEASIBILITY
                -> OBJECTIVE -> PARETO / OPTIONAL SCORE -> HUMAN DECISION
```

| Kind of statement | Owner | Example |
| --- | --- | --- |
| physics result | Phase 5D / 5E | T₀ = 3598 K, Isp = 348.7 s |
| constraint | the user | T₀ ≤ 3500 K |
| feasibility | the constraint applied to the result | infeasible |
| objective | the user | maximise Isp |
| Pareto membership | the objective vectors | efficient |
| score | the user's weights | 0.75 |
| decision | the user | — |

None of these becomes another. A score never reaches back into physics; a
constraint never becomes a penalty; a warning never becomes an infeasibility.

---

## `engine.studies` — the generic core

### Design variables

```python
LinearRangeVariable(key, label, stage, unit, domain, start, end, count)
ExplicitNumericVariable(key, label, stage, unit, domain, entries)
CategoricalVariable(key, label, stage, options)
```

Three kinds, deliberately no more. There is no expression language and no
user-supplied callable: a definition that could contain arbitrary code could
not be fingerprinted, serialised, or reasoned about, and "the study ran
something the user typed" is not a provenance record.

**`start`/`end`/`count`, never `step`.** The point count is then exact and
known before anything runs — which is what the workload preview needs — and
`linear_range` generates by index with both endpoints assigned literally.
Accumulating `value += step` forty times misses 1.0 by several ulp, and a study
whose top-of-range O/F is 4.499999999999998 has quietly stopped being the study
that was defined.

**Every variable declares a stage.** That is not documentation: the planner
reads it, and it is the entire basis of the solve-reuse guarantee.

### Metrics

```python
MetricDefinition(key, label, stage, unit, requires_scale, help, decimals_hint)
MetricRegistry(metrics)
```

`requires_scale` exists so a study asking for thrust with no engine size is
refused while it is still a form, rather than producing four hundred rows of
blanks. There is **no** `higher_is_better`: direction belongs to an explicit
objective, because "higher Isp is better" stops being true the moment it is
traded against chamber temperature.

### Study definition

```python
StudyDefinition(baseline, variables, stage_order, outputs, objectives,
                constraints, scoring, title)
```

`baseline` is a **snapshot**. Once a study exists it stops following the
workspace it was created from — otherwise editing the Thermochemistry tab would
relabel a completed study with conditions that did not produce it, the same
defect Phase 5D and 5E each had to design against.

`fingerprint` is a SHA-256 over the canonical form: sorted mappings, no title,
no display unit, no clock. Renaming a study does not change it; widening a
range does.

### Validation, before anything runs

| Code | Refused because |
| --- | --- |
| `NO_STAGE_ORDER` | a study needs at least one evaluation stage |
| `DUPLICATE_DESIGN_VARIABLE` | the same variable appears twice |
| `UNKNOWN_VARIABLE_STAGE` | a stage the study does not declare |
| `EMPTY_DESIGN_VARIABLE` | no values to study |
| `NO_REQUESTED_METRICS` | it would evaluate points and report nothing |
| `UNKNOWN_METRIC` | names what is available |
| `METRIC_REQUIRES_SCALE` | thrust with no engine size |
| `DUPLICATE_OBJECTIVE` | two directions on one metric contradict |
| `SCORING_WITHOUT_OBJECTIVES` | nothing to combine |
| `SCORE_WEIGHT_WITHOUT_OBJECTIVE` | a weight on something not being optimised |
| `OBJECTIVE_WITHOUT_SCORE_WEIGHT` | an omitted weight is an invisible zero |
| `STUDY_TOO_LARGE` | above `MAX_STUDY_POINTS`, and says by how much |
| `INEFFECTIVE_DESIGN_VARIABLE` | the variable cannot affect anything requested |

The last one is worth its own note. Varying an area ratio in a study whose only
output is chamber temperature produces N identical rows. That is not a null
result, it is a misunderstanding of the model, and generating the rows anyway
would confirm it — a flat line reads as "area ratio barely matters" rather than
"area ratio was never in this calculation".

### The point cap

`MAX_STUDY_POINTS = 20 000`, chosen from measurement
(`acceptance/phase_5f/study_performance.json`):

| points | total s | decision s | pareto s | peak MB |
| --- | --- | --- | --- | --- |
| 1 000 | 0.080 | 0.010 | 0.006 | 1.6 |
| 10 000 | 1.53 | 0.227 | 0.263 | 16.5 |
| **20 000** | **4.73** | **0.682** | **0.456** | **33.1** |
| 40 000 | 14.44 | 2.274 | 1.878 | 66.6 |

Doubling to 40 000 triples the total: the quadratic Pareto term turning. A
repeat at the cap peaks at the same 33.08 MB, so nothing accumulates. Exceeding
the cap refuses the definition; it never silently samples a subset.

---

## The dependency planner

The central optimisation of the phase:

```
41 O/F values × 10 area ratios  =  410 design points
                                =   41 chamber solves
                                =  410 performance evaluations
```

A **stage key** holds the values of every variable at or before that stage, and
nothing else. An area ratio declared at the performance stage therefore cannot
appear in the chemistry key, and the reuse follows structurally rather than
from a cache that happens to hit.

Measured (`acceptance/phase_5f/chemistry_cache_proof.json`):

| Case | Points | Expected | Actual | Reduction |
| --- | --- | --- | --- | --- |
| 41 O/F × 4 ε | 164 | 41 | **41** | 4.0× |
| 41 O/F × 10 ε | 410 | 41 | **41** | 10.0× |
| fixed chamber, 10 ε × 5 p_a | 50 | 1 | **1** | 50.0× |
| 5 O/F × 4 p_c × 3 ε | 60 | 20 | **20** | 3.0× |
| chamber temperature only, 41 O/F | 41 | 41 | **41** | 1.0× |

**Failures are cached too.** One refused chamber with ten dependants costs one
call, not ten, and the ten downstream points are never attempted
(`failure_caching.json`: 4 upstream calls, 20 downstream, 20 failed points
kept).

The cache is **study-local**. A process-global scientific cache would outlive
the provenance that makes its entries meaningful, and would let two studies
silently share a result whose model assumptions might differ.

### Required-stage planning

A study is evaluated only as deep as its requested metrics need. A
chamber-temperature study never runs the performance stage: no c*, no Cf, no
Isp is computed for a study that asked for none.

---

## The decision layer

Runs once, over a complete population, on raw results that already exist.

```
constraints -> feasibility -> Pareto -> ranking -> optional score
```

### Constraints

`<=`, `<`, `>=`, `>`, `==`. Plain float comparison, **no hidden tolerance** — a
margin belongs in the limit, where it is visible. A missing metric produces a
third answer (`None`), not a violation: a model limitation is not an
engineering verdict.

There is no penalty function. Turning "exceeds 3500 K" into "score minus 0.3"
produces a ranking in which a design that cannot be built outranks one that
can, and no coefficient fixes that.

### Two status fields

| `EvaluationStatus` | |
| --- | --- |
| `SUCCESS` | the model produced the required metrics |
| `WARNING` | evaluated, with a scientific caveat attached |
| `FAILED` | a stage refused or errored |
| `NOT_EVALUABLE` | every stage succeeded and a required metric is still absent |

| `Feasibility` | |
| --- | --- |
| `FEASIBLE` | satisfies every constraint |
| `INFEASIBLE` | violates one |
| `NOT_EVALUATED` | no verdict is possible |

A single overloaded enum would make it impossible to tell a chamber that would
not converge from one that converged at 3610 K when the limit was 3500.

### Pareto

One front, not a ranked series. `dominates` requires no-worse on every
objective and strictly-better on at least one, after respecting each
direction. Excluded: failed points (no vector), infeasible points (letting one
dominate would remove a buildable design in favour of an unbuildable one), and
non-finite values (a NaN compares false against everything and would look
unbeatable).

Identical vectors do not dominate each other, so ties all stay — the honest
answer, since picking one duplicate would hide that the study found several
equally good designs.

**The score never enters.** Dominance is a property of the objective vectors.

O(N²), measured rather than assumed: 0.456 s at the 20 000-point cap.

### Optional weighted score

Off unless explicitly enabled. Min–max over the feasible evaluated set, with 1
always meaning better in both directions, so a weighted sum needs no sign
convention. A zero-span objective contributes a constant to every point and
cannot decide an order; nothing divides by zero.

A score is **study-relative**: the same design scores differently in a
different population. That is a property of the method, and it is stated
wherever a score is shown.

### Re-analysis

`reanalyse(result, definition)` re-runs the decision layer on existing raw
results. Measured (`reanalysis_zero_resolve.json`): flipping an objective,
changing a constraint limit three times and reweighting a score each cost **0**
chemistry solves and **0** performance solves, with the raw metrics identical
before and after.

---

## `application.analysis.trade_study_service` — the RocketForge evaluator

```python
TradeStudySetup(chamber: ChamberCase, performance: PerformanceCase)
RocketForgeEvaluator(setup).evaluate(stage, point, upstream) -> StageOutcome
run_trade_study(definition, setup, ...) -> StudyResult
reanalyse(result, definition) -> StudyResult
```

**It computes nothing.** No c*, no Cf, no Isp, no thrust. Every number comes
from `performance_service` over `engineering.nozzle`, and a test asserts that
no Phase 5F module defines a function with one of those names or references
`sqrt`, `STANDARD_GRAVITY` or `vandenkerckhove`.

Direct-solve parity (`direct_solve_parity.json`): every one of 164 cached
points compared against invoking the canonical services directly for that exact
point — **1148 field comparisons, 0 differences**, by exact float equality.

### Variables

| Key | Stage | Effect |
| --- | --- | --- |
| `oxidiser_fuel_ratio` | chemistry | each value is a separate chamber solve |
| `chamber_pressure` | chemistry | multiplies the chamber solve count |
| `area_ratio` | performance | costs no chamber solves |
| `ambient_pressure` | performance | an operating condition; pressure term only |
| `throat_area` | performance | sizes the engine; no scale-free quantity moves |

### Deliberately not variables

| | Why |
| --- | --- |
| liquid reactant temperature | CEA models the shipped liquid reactants with an assigned enthalpy, so the requested stream temperature does not enter the solve. A temperature study would draw a sensitivity curve for something not modelled — a flat line read as "temperature barely matters". Deferred until reactant enthalpy / fluid-property coupling exists. |
| gamma strategy and basis | a model assumption. Two reductions in one front compare models, not designs. |
| provider, chemistry mode, database | study provenance. Ranking designs computed by different providers ranks the providers. |
| propellant pair | the registry supports a categorical variable, but a pair study also changes the product element set. Left for a later phase rather than fabricated from display strings. |

### Metrics

Sixteen, spanning both stages. **None is called plain `gamma`** — a chamber
state carries two isentropic exponents several per cent apart, and one column
so headed would be uninterpretable. `gamma_equilibrium` and `gamma_frozen`
are separate metrics.

### The oracle is not study physics

A trade study's physics is the provider for the chamber and RocketForge for the
nozzle. `CEARocketOracle` is a Phase 5E validation tool and is **not** evaluated
per study point — the provenance record says so in a field, and a test asserts
the service does not import it.

### Density impulse — out of scope

Not implemented, and `density_hint` is untouched. It is display-only reference
metadata by Phase 5A/5B contract, and `rho·Isp·g0` computed from it would be a
physical claim resting on a number never validated as a physical property, at a
temperature, pressure and phase it does not record. An AST audit over every
Phase 5F module asserts no identifier, attribute or non-docstring string
contains "density", with a two-way negative control.

Deferred until a validated fluid-property source exists.

---

## What is not here

No gradient optimisation, no genetic algorithm, no Bayesian or surrogate
optimisation, no trajectory or engine-cycle optimisation, no arbitrary user
formulas, no new physics of any kind.

A trade study evaluates a **finite sampled grid**. Nothing in this phase
searches, and nothing in it claims a global optimum.
