# Phase 5F — Generic Trade Study / Design Space Engine

Design variables, physics evaluation, hard constraints, objectives,
feasibility, Pareto analysis, optional explicit weighted scoring, design
comparison, dependency-aware solve reuse, and a user-facing Trade Study
workspace.

**Verdict: READY FOR PHASE 5G.**

---

## 1. What this phase is, and is not

It writes **no physics**. It consumes the accepted Phase 5D thermochemistry and
Phase 5E ideal-performance stack and adds the layer above them: a design space,
the constraints that make part of it unavailable, the objectives that order
what remains, and the analysis that helps a person choose.

The distinction it exists to preserve, one way only:

```
DESIGN VARIABLE -> PHYSICS -> RAW RESULT -> CONSTRAINT -> FEASIBILITY
                -> OBJECTIVE -> PARETO / OPTIONAL SCORE -> HUMAN DECISION
```

A score never reaches back into physics. A constraint never becomes a penalty.
A warning never becomes an infeasibility. A failed point is never deleted.

---

## 2. Phase 5E documentation normalization

Wording only. No physics, no tolerance and no test changed.

| Item | Before | After |
| --- | --- | --- |
| Final verdict | `PASS` | **READY FOR PHASE 5F**; the report header reads `COMPLETE — READY FOR PHASE 5F` |
| c\* classification | `validation residual` | **closest cross-model difference** |
| Anchors warnings | `produced 1464 Qt warnings` | `…in an intermediate run`, with the accepted **0** stated alongside |

The second is the substantive one. RocketForge v1 is calorically perfect; CEA
frozen-at-chamber is calorically imperfect. Matching the *chemistry* assumption
makes it the nearest partner available, and nearest is not identical. The term
*validation residual* is now reserved for genuine same-model checks — c\*
against the independent perfect-gas analytic form, and the internal identities
against frozen Compressible.

`acceptance/phase_5e/cea_oracle_comparison.json` was **regenerated** rather than
hand-edited, so the artifact carries the corrected classification from the code
that produces it.

---

## 3. Layer ownership, resolved from the repository

Doc 06 already assigns *"parametric studies, trades, sensitivity"* to
**`engine.studies`** at L3. That is where the generic core went — above
`engineering`, which docs 01 and 06 reserve for **the design of one physical
component**. A design-space engine is not a component, and putting it there
would have made `engineering` mean two things.

L3 is a permission, not an obligation. The generic core imports nothing from
`physics`, `engineering`, `providers` or Qt — asserted per module — and a
clean-interpreter subprocess runs a whole study with no `cea`, `cantera` or
`PySide6` entry in `sys.modules`.

### Files created

| File | Owns |
| --- | --- |
| `rocketforge/engine/studies/variables.py` | the three variable kinds, `linear_range` |
| `rocketforge/engine/studies/metrics.py` | `MetricDefinition`, `MetricRegistry` |
| `rocketforge/engine/studies/enumeration.py` | `DesignPoint`, enumeration, **`stage_key`** |
| `rocketforge/engine/studies/definition.py` | `StudyBaseline`, `StudyDefinition`, fingerprint, validation, the point cap |
| `rocketforge/engine/studies/constraints.py` | operators, `ConstraintDefinition`, `ConstraintOutcome` |
| `rocketforge/engine/studies/objectives.py` | direction, `ObjectiveDefinition`, ranking |
| `rocketforge/engine/studies/pareto.py` | `dominates`, `pareto_membership`, `pareto_front` |
| `rocketforge/engine/studies/scoring.py` | `WeightedScoreDefinition`, normalisation, scoring |
| `rocketforge/engine/studies/results.py` | the two status enums, point and study results |
| `rocketforge/engine/studies/execution.py` | `StudyRunner`, the cache, diagnostic aggregation |
| `rocketforge/engine/studies/analysis.py` | `analyse` — the whole decision pass |
| `rocketforge/application/analysis/trade_study_domain.py` | stages, variables, metrics, deferrals |
| `rocketforge/application/analysis/trade_study_service.py` | `TradeStudySetup`, `RocketForgeEvaluator`, run, re-analyse, provenance |
| `rocketforge/application/analysis/trade_study_controller.py` | the Qt facade |
| `rocketforge/application/studysmoke.py` | `--selftest-trade-study` |
| `ui/pages/TradeStudyPage.qml` + 5 in `ui/pages/tradestudy/` | the workspace |

### Files modified

`main.py` (a fifth singleton and a fourth diagnostic), `ui/data/Navigation.qml`,
`ui/shell/SideNav.qml`, `ui/components/RFComboBox.qml` (an added `activated`
signal — purely additive), and `current_case()` accessors added to the
thermochemistry and performance controllers. Two architecture tests gained the
third analysis domain in their exclusion lists.

---

## 4. Solve reuse — the blocking property

A design point count is not a solve count. A **stage key** holds the values of
every variable at or before that stage and nothing else, so an area ratio
declared at the performance stage cannot appear in the chemistry key.

| Case | Points | Expected | Actual | Reduction |
| --- | --- | --- | --- | --- |
| 41 O/F × 4 ε | 164 | 41 | **41** | 4.0× |
| 41 O/F × 10 ε | 410 | 41 | **41** | 10.0× |
| fixed chamber, 10 ε × 5 p_a | 50 | 1 | **1** | 50.0× |
| 5 O/F × 4 p_c × 3 ε | 60 | 20 | **20** | 3.0× |
| chamber temperature only, 41 O/F | 41 | 41 | **41** | 1.0× |

Counted at the evaluator **and** at the provider, and again in the packaged
executable. Negative controls: one more upstream value adds exactly one solve;
ten more downstream values add none.

**Failure caching.** One refused chamber with ten dependants costs one call,
not ten, and the ten downstream points are never attempted. Failed points keep
their variable values, their index and their reason — 20 kept, 0 dropped.

The cache is **study-local**. A second study re-solves; it does not inherit the
first one's cache.

**Required-stage planning.** A chamber-temperature study never runs the
performance stage: no c\*, no Cf, no Isp is computed for a study that asked for
none.

---

## 5. Direct-solve parity

Caching may change a call count. It may not change a number.

Every one of 164 cached points was compared against invoking `solve_case` and
`solve_performance` directly for that exact point, across seven fields:
**1148 comparisons, 0 differences**, by exact float equality rather than a
tolerance. The same grid solved naively costs 164 provider calls against the
cached 41 — a measured 4.0× reduction, reported as a call count.

---

## 6. The decision layer

| Separation | Enforced by |
| --- | --- |
| physics failure ≠ infeasibility | two enums plus a third `NOT_EVALUATED` value |
| warning ≠ failure ≠ infeasibility | a warning point evaluates, stays feasible, ranks and scores |
| constraint ≠ penalty | `ConstraintOutcome` has no penalty field, asserted |
| score ≠ Pareto | dominance never sees a weight; the front is byte-identical after reweighting |
| score ≠ feasibility | asserted directly |
| required metric missing ≠ infeasible | `NOT_EVALUABLE`, with the upstream numbers kept |

Pareto is checked against a **hand-computed six-point fixture** whose expected
front was written down, not produced by the implementation — covering dominated
points, a tie, mixed directions, and a mutation proof that asserts the fixture
changed before requiring the front to follow.

Scoring is checked against hand-computed normalised values and weighted totals
(0.25 / 0.50 / 0.75 for weights 3 and 1).

### Re-analysis

Flipping an objective, changing a constraint limit three times, and reweighting
a score: **0 chemistry solves and 0 performance solves each**, with the raw
metrics identical before and after. Measured through the functions, through the
Qt controller, and in the packaged build.

---

## 7. The point cap, chosen from measurement

`MAX_STUDY_POINTS = 20 000`.

| points | total s | decision s | pareto s | peak MB |
| --- | --- | --- | --- | --- |
| 1 000 | 0.080 | 0.010 | 0.006 | 1.6 |
| 10 000 | 1.53 | 0.227 | 0.263 | 16.5 |
| **20 000** | **4.73** | **0.682** | **0.456** | **33.1** |
| 40 000 | 14.44 | 2.274 | 1.878 | 66.6 |

Doubling to 40 000 triples the total — the quadratic Pareto term turning. A
repeat at the cap peaks at the same 33.08 MB, so nothing accumulates. Exceeding
it refuses the definition and says by how much; it never samples a subset.

---

## 8. Live studies

LOX/LCH4, 100 bar, frozen gamma basis, vacuum.

**Study A** — 41 O/F × 4 area ratios, maximise Isp. 164 points, **41 chamber
solves**, 164 performance evaluations. Best evaluated feasible Isp 363.29 s at
O/F 2.85, Ae/At 80.

**Study B** — the same grid, maximise Isp and minimise chamber temperature,
with T₀ ≤ 3500 K. 40 feasible, 124 infeasible, **8 Pareto-efficient**. The
limit is a documented test value, not one chosen to shape the front.

The provider's own c\*, Cf and Isp are **not** evaluated per study point. A
trade study's physics is CEA for the chamber and RocketForge for the nozzle;
the provenance record states it in a field, and a test asserts the service does
not import the oracle module.

---

## 9. The workspace

Fourth analysis domain, four views, full contract in
`TRADE_STUDY_UI_CONTRACT.md`. The rules: the workload is previewed before
anything runs; no equations, constants or decision algorithms in QML; every
point keeps its row; execution is serial and chunked; a cancelled study shows
no front; scoring is off by default; the Pareto plot says its markers are
samples and that it is a projection; and nothing anywhere claims a global
optimum.

| | Source | Packaged |
| --- | --- | --- |
| Captures | 14 | 14 |
| Qt messages | **0** | **0** |
| Chamber solves (expected 41) | **41** | **41** |
| Solves added by decision edits | **0** | **0** |

**Parity: 6936 fields compared, 0 differing.**

---

## 10. Gates

| Gate | Accepted baseline | Result | |
| --- | --- | --- | --- |
| Base (`.venv`) | 6108 / 113 | **6390 passed, 118 skipped**, exit 0 | ✅ |
| CEA-enabled (`.venv-cea`) | 6223 / 1 | **6510 passed, 1 skipped**, exit 0 | ✅ |
| Frozen Compressible | 22 / 22 | **22 / 22 byte-identical** | ✅ |

Phase 5F adds **287 tests**. Architecture rules: 41 original + 18 (5B) + 18
(5C) + 50 (5D) + 32 (5E) + **85 (5F)**, all green.

All three earlier self-tests pass unchanged on the new build: the Phase 5C
provider diagnostic (exit 0), the Phase 5D interface tour (35 captures, 0 Qt
messages), and the Phase 5E performance tour (29 captures, 0 Qt messages, 0
chamber solves from nozzle input changes).

---

## 11. Defects found and fixed

**Three QML binding loops.** Selectors bound to a controller property that also
wrote back from `onCurrentIndexChanged` looped through their own bindings.
Comparing values first did not help — Qt reports the loop on the binding.
Fixed by writing back from `activated`, which fires only on user selection;
`RFComboBox` now forwards it.

**The Pareto axis selectors were unbound**: both read "Specific impulse" while
the plot was drawn against chamber temperature. Caught by reading the capture.

**The axis titles showed raw metric keys** rather than labels and units.

**Four audits of my own were wrong about what they were reading**, each in the
same family the project has met before:

* `_imports` missed relative imports, so a module importing six siblings looked
  as though it imported nothing;
* the decision-algorithm scan read display labels — "Feasible, dominated" is a
  legend entry, not a dominance loop;
* the density-hint scan and the global-optimum scan each flagged the very
  docstring and disclaimer that exist to prevent the thing being audited.

All four were rewritten to read the syntax tree, to blank string literals, or
to skip negated phrases, and each gained a **two-way negative control** that
fires on the violation and stays silent on the explanation.

**A Phase 5D architecture rule needed the third analysis domain** added to its
exclusion list — exactly the maintenance the Phase 5E rescoping was designed to
require, with the companion test still refusing any widening beyond named
domains.

---

## 12. Deliberately not implemented

density impulse · liquid density physics · reactant enthalpy / fluid-property
coupling · reactant-temperature optimisation · provider comparison inside one
Pareto study · gamma-strategy comparison inside one Pareto study · combustion
efficiency · nozzle losses · actual or delivered performance · gradient
optimisation · genetic algorithms · Bayesian optimisation · surrogate
optimisation · arbitrary user equations · trajectory optimisation ·
engine-cycle optimisation · automatic application of a selected study point to
Engine Design.

`density_hint` is untouched. An AST audit over every Phase 5F module asserts no
identifier, attribute or non-docstring string contains "density".

---

## 13. Known limitations

* **The propellant pair is not a design variable.** The registry supports a
  categorical variable and the catalogue is provenance-bearing, but a pair
  study also changes the product element set. Left for a later phase rather
  than fabricated from display strings.
* **One reduction per study.** Comparing gamma bases means running two studies;
  mixing them in one front would compare models rather than designs.
* **A score is study-relative.** Stated in the interface and in this document,
  but it remains a property a reader has to hold in mind.
* **The Pareto pass is O(N²).** Measured at 0.456 s at the 20 000-point cap,
  which is why it is not something else.

---

## 14. Recommended Phase 5G

**INTEGRATED PROPULSION ANALYSIS ACCEPTANCE / FREEZE.**

System-wide acceptance of Thermochemistry, Rocket Performance and Trade Study,
and of their interfaces with frozen Compressible v1: audit the public APIs,
audit the dependency boundaries, freeze the stable interfaces, verify the
scientific provenance end to end, verify full source/package parity, run
canonical multi-layer validation cases and long regression or soak tests,
document the known limitations, and produce the integrated acceptance manifest.
