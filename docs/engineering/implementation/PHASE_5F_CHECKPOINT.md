# Phase 5F — Checkpoint

Generic trade study / design space engine. Design variables, physics
evaluation, hard constraints, objectives, feasibility, Pareto analysis,
optional weighted scoring, dependency-aware solve reuse, and a Trade Study
workspace.

**Status:** COMPLETE

---

## Position

| Field | Value |
| --- | --- |
| CURRENT_SEGMENT | J — regressions, artifacts and documentation — **COMPLETE** |
| LAST_COMPLETED_STEP | STEP 143 — final verdict |
| NEXT_STEP | none; the phase is closed |
| NEXT_ACTION | Phase 5G, which is not started and not designed here |

---

## Opening gates

| Gate | Result | Accepted baseline | Match |
| --- | --- | --- | --- |
| Base (`.venv`) | **6108 passed, 113 skipped**, exit 0, 52.85 s | 6108 / 113 | ✅ |
| CEA-enabled (`.venv-cea`) | **6223 passed, 1 skipped**, exit 0, 59.39 s | 6223 / 1 | ✅ |
| Frozen Compressible | **22 / 22 byte-identical** | 22/22 | ✅ |

Digest `8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502`,
verified by recomputing each file's recorded `sha256[:16]` against the Phase 4G
manifest.

### Phase 5D corrective semantics

| | |
| --- | --- |
| Four condensed states | `unknown`, `none_reported`, `below_threshold`, `present` |
| `CONDENSED_REPORTING_THRESHOLD` | 1e-06, presentation-only, in `application.analysis.thermochemistry_service` |
| `SINGLE_PHASE_CONDENSED_LIMIT` | 1e-06, physics, in `engineering.chamber` |
| Separate constants in separate layers | ✅ (equal value, no shared identity) |
| O/F sweep optimizer language | none |

### Phase 5E identities

256 tests across the thermochemistry service, sweep, ideal performance and
performance service — all green.

---

## Phase 5E documentation normalization (STEP 2)

Wording only. No physics, no tolerances, no test changed.

| Item | Before | After |
| --- | --- | --- |
| §3.1 final verdict | `PASS` | **READY FOR PHASE 5F**, and the report header reads `COMPLETE — READY FOR PHASE 5F` |
| §3.2 c\* classification | `validation residual` | **closest cross-model difference** |
| §3.3 anchors warnings | `produced 1464 Qt warnings` | `produced 1464 Qt warnings in an intermediate run`, with the accepted 0 stated alongside |

§3.2 in full: RocketForge v1 is calorically perfect; CEA frozen-at-chamber is
calorically imperfect. Matching the *chemistry* assumption makes it the nearest
partner available, and nearest is not identical. The term *validation residual*
is now reserved for genuine same-model checks — c\* against the independent
perfect-gas analytic form, and the internal identities against frozen
Compressible.

Files touched: `PHASE_5E_CHECKPOINT.md`,
`PHASE_5E_IDEAL_ROCKET_PERFORMANCE.md`,
`acceptance/phase_5e/ACCEPTANCE_MANIFEST.md`,
`ROCKET_PERFORMANCE_UI_CONTRACT.md`, `experiments/phase_5e/oracle_compare.py`.
`acceptance/phase_5e/cea_oracle_comparison.json` regenerated so the artifact
carries the corrected classification rather than being hand-edited.

---

## SEGMENT A — package ownership and the generic core

### Ownership, resolved from the repository rather than from the brief

Doc 06 already assigns *"parametric studies, trades, sensitivity"* to
**`engine.studies`** at L3. That is where the generic core went. It is above
`engineering`, which doc 01 and doc 06 reserve for *the design of one physical
component* — a design-space engine is not a component, and putting it there
would have made `engineering` mean two different things.

L3 is a permission, not an obligation: the generic core imports **nothing**
from `physics`, `engineering`, `providers` or Qt, and is exercised entirely by
synthetic evaluators.

| File | What it owns |
| --- | --- |
| `rocketforge/engine/studies/variables.py` | `LinearRangeVariable`, `ExplicitNumericVariable`, `CategoricalVariable`, `VariableDomain`, `linear_range` |
| `rocketforge/engine/studies/metrics.py` | `MetricDefinition`, `MetricRegistry` |
| `rocketforge/engine/studies/enumeration.py` | `DesignPoint`, `enumerate_points`, `point_count`, `stage_key`, `unique_stage_keys` |
| `rocketforge/engine/studies/definition.py` | `StudyBaseline`, `StudyDefinition`, fingerprint, `validate_definition`, `MAX_STUDY_POINTS` |
| `rocketforge/engine/studies/constraints.py` | `ComparisonOperator`, `ConstraintDefinition`, `ConstraintOutcome` |
| `rocketforge/engine/studies/objectives.py` | `ObjectiveDirection`, `ObjectiveDefinition`, `rank_by_objective` |
| `rocketforge/engine/studies/pareto.py` | `dominates`, `pareto_membership`, `pareto_front` |
| `rocketforge/engine/studies/scoring.py` | `WeightedScoreDefinition`, `normalize_objective`, `score_points` |
| `rocketforge/engine/studies/results.py` | `EvaluationStatus`, `Feasibility`, `StudyStatus`, `StudyPointResult`, `StudyResult` |
| `rocketforge/engine/studies/execution.py` | `StageOutcome`, `StudyRunner`, `run_study`, diagnostic aggregation |
| `rocketforge/engine/studies/analysis.py` | `analyse` — the whole decision pass |

### Exact endpoints

`linear_range` generates by index, `start + i·span/(n−1)`, with both endpoints
assigned literally. Accumulating `value += step` 40 times misses 1.0; the test
asserts both the exact endpoint and that the accumulation it replaces does not.

---

## SEGMENT B — dependency planner and study-local cache

A stage key contains the values of every variable **at or before** that stage,
and nothing else. An area ratio declared at the performance stage therefore
cannot appear in the chemistry key, and reuse follows structurally rather than
from a cache that happens to hit.

### The three mandatory cases

| Case | Points | Chemistry solves | |
| --- | --- | --- | --- |
| A — 41 O/F × 10 ε | 410 | **41** | ✅ |
| B — fixed chamber, 10 ε × 5 p_a | 50 | **1** | ✅ |
| C — 5 O/F × 4 p_c × 3 ε | 60 | **20** | ✅ |

Negative controls: adding an upstream value adds exactly one solve; adding ten
downstream values adds none. The recorded call log is also checked directly —
the 41 upstream calls carry 41 distinct O/F values.

### Failure caching

One refused chamber with ten dependants costs **one** call, not ten, and the
ten downstream points are never attempted. Failed points keep their variable
values, their index and their reason: a hole in a design space is information,
and deleting the rows that show it leaves a chart implying the space is
continuous.

The cache is **study-local**. A second study re-solves; it does not inherit the
first one's cache.

---

## SEGMENT C — the RocketForge evaluator

| File | What it owns |
| --- | --- |
| `rocketforge/application/analysis/trade_study_domain.py` | stages, `VARIABLE_SPECS`, `METRICS`, `DEFERRED_VARIABLES` |
| `rocketforge/application/analysis/trade_study_service.py` | `TradeStudySetup`, `RocketForgeEvaluator`, `run_trade_study`, `reanalyse`, `study_provenance` |

Five variables: O/F and chamber pressure at the chemistry stage; area ratio,
ambient pressure and throat area at the performance stage. Sixteen metrics, of
which **none** is called plain `gamma` — `gamma_equilibrium` and `gamma_frozen`
are several per cent apart and a single column would be uninterpretable.

Deliberately not design variables, each with its reason recorded in
`DEFERRED_VARIABLES`: liquid reactant temperature (CEA's assigned enthalpy
means the study would draw a sensitivity curve for something not modelled),
gamma strategy and basis (a model assumption), provider and database (study
provenance), propellant pair (needs an element-set decision, left for later
rather than fabricated).

### Direct-solve parity

Every one of 164 cached points was compared against invoking `solve_case` and
`solve_performance` directly for that exact point: **492 field comparisons, 0
differences**. The same grid solved naively costs 164 provider calls against
the cached 41 — a measured 4.0× reduction, reported as a call count rather than
as a timing.

### Live, against NASA CEA

164 points, **41 chemistry solves**, 164 performance evaluations, 0.12 s,
0 failures. Best evaluated feasible Isp 363.29 s at O/F 2.85, Ae/At 80.

---

## SEGMENT D — the decision layer

Constraints → feasibility → Pareto → ranking → optional score, in that order,
each depending only on what precedes it.

| Separation | Enforced by |
| --- | --- |
| physics failure ≠ infeasibility | two enums, `EvaluationStatus` and `Feasibility`, and a third value `NOT_EVALUATED` for "no verdict possible" |
| warning ≠ failure ≠ infeasibility | a warning point evaluates, stays feasible, ranks and scores |
| constraint ≠ penalty | a `ConstraintOutcome` has no penalty field, and a test asserts it |
| score ≠ Pareto | dominance never sees a weight; changing every weight leaves the front byte-identical |
| score ≠ feasibility | asserted directly |

Pareto is checked against a **hand-computed six-point fixture** with the
expected front written down, not produced by the implementation. It covers
dominated points, a tie, mixed directions, and — via the study tests — the
exclusion of infeasible and failed points that would otherwise dominate. The
mutation proof asserts the fixture actually changed before requiring the front
to follow.

Scoring is checked against hand-computed normalised values and weighted totals
(0.25 / 0.50 / 0.75 for weights 3 and 1).

### The point cap, chosen from measurement

`MAX_STUDY_POINTS = 20 000`, from `experiments/phase_5f/point_cap_benchmark.py`
(`acceptance/phase_5f/study_performance.json`):

| points | total s | decision s | pareto s | peak MB |
| --- | --- | --- | --- | --- |
| 1 000 | 0.080 | 0.010 | 0.006 | 1.6 |
| 10 000 | 1.53 | 0.227 | 0.263 | 16.5 |
| **20 000** | **4.73** | **0.682** | **0.456** | **33.1** |
| 40 000 | 14.44 | 2.274 | 1.878 | 66.6 |

Doubling to 40 000 triples the total — the quadratic Pareto term turning. A
repeat run at the cap peaks at the same 33.08 MB, so nothing accumulates.

---

## Test counts

| Module | Tests |
| --- | --- |
| `tests/engine/studies/test_variables_and_points.py` | 35 |
| `tests/engine/studies/test_solve_reuse.py` | 21 |
| `tests/engine/studies/test_decision_layer.py` | 44 |
| `tests/engine/studies/test_study_lifecycle.py` | 30 |
| `tests/application/test_trade_study_service.py` | 34 + 4 CEA-only |

**164 passing** in the CEA environment.

## Regressions

| | |
| --- | --- |
| Base opening | 6108 / 113, exit 0 |
| CEA opening | 6223 / 1, exit 0 |
| Closing | pending Segment J |

## Solve counts

| | |
| --- | --- |
| CHEMISTRY_SOLVE_COUNT | 41 for the canonical 164-point grid, at both the evaluator and the provider |
| PERFORMANCE_SOLVE_COUNT | 164 |
| Re-analysis (objective / constraint / weight) | **0** and **0** |

## Interface

| | |
| --- | --- |
| CURRENT_QML_WARNINGS | not yet built |
| Packaged state | Phase 5E build in `dist/`; Phase 5F rebuild pending |

## Frozen manifest

22 / 22 byte-identical.

---

## SEGMENT E — cancellation and chunked execution

Serial and chunked: eight design points per event-loop turn on a zero-interval
`QTimer`. No thread pool and no concurrent provider call — a test bans
`QThread`, `QThreadPool`, `ThreadPoolExecutor`, `ProcessPoolExecutor`,
`multiprocessing` and `QRunnable` from the controller. Phase 5B-0 measured CEA
threading and found no gain.

A cancelled study keeps its evaluated points and presents **no** front, ranking
or score, and says why.

Progress reports real work — "300 of 410 points · 41 of 41 chamber solves" —
rather than a synthesised percentage.

---

## SEGMENT F — service, controller and Setup

| File | Owns |
| --- | --- |
| `rocketforge/application/analysis/trade_study_controller.py` | the Qt facade |
| `ui/pages/TradeStudyPage.qml` | header, view selector, stack |
| `ui/pages/tradestudy/StudySetup.qml` | baseline, variables, outputs, objectives, constraints, scoring, run |
| `ui/pages/tradestudy/StudyVariableRow.qml` | one variable and what varying it costs |

The workload preview is the centrepiece: point count and unique chamber-solve
count, updated as a range is edited, with **zero** solves. `current_case()`
accessors were added to the thermochemistry and performance controllers —
plain Python methods, so no domain record reaches QML.

---

## SEGMENT G — Results, Pareto and Compare

Three series distinguished by marker **shape** as well as colour. Two notes a
reader would otherwise get wrong: the markers are samples rather than a curve,
and with more than two objectives the plot is a projection of a front decided
on all of them.

Compare shows at most four designs, grouped variables → physics → constraints →
decision, with the weighted score as the last row of the last group.

---

## SEGMENT H — architecture rules

85 rules in `tests/application/test_trade_study_architecture.py`. Per-module
assertions that no `engine.studies` file imports Qt, a provider, the
application, `physics` or `engineering`; a clean-interpreter subprocess that
runs a whole study with no `cea`, `cantera` or `PySide6` in `sys.modules`; no
decision algorithm, physical constant or score formula in QML; no second
performance implementation; and a wording audit over both the QML and every
published controller property.

---

## SEGMENT I — packaged build and parity

Clean rebuild from `.venv-cea`. All four diagnostics pass:

| Diagnostic | Result |
| --- | --- |
| `--selftest-thermochemistry` | exit 0 |
| `--selftest-thermochemistry-ui` | 35 captures, 0 Qt messages |
| `--selftest-rocket-performance` | 29 captures, 0 Qt messages, 0 chamber solves from input changes |
| `--selftest-trade-study` | 14 captures, 0 Qt messages, 41 chamber solves for 164 points, 0 added by decision edits |

**Parity: 6936 fields compared, 0 differing, 0 present in only one build.**

---

## SEGMENT J — regressions, artifacts, documentation

### Closing gates

| Gate | Accepted baseline | Result | |
| --- | --- | --- | --- |
| Base (`.venv`) | 6108 / 113 | **6390 passed, 118 skipped**, exit 0 | ✅ |
| CEA-enabled (`.venv-cea`) | 6223 / 1 | **6510 passed, 1 skipped**, exit 0 | ✅ |
| CEA repeat | identical | **6510 / 1** | ✅ |
| Frozen Compressible | 22 / 22 | **22 / 22 byte-identical** | ✅ |

Phase 5F adds **287 tests** and **85 architecture rules**.

### Artifacts — `acceptance/phase_5f/`

`ACCEPTANCE_MANIFEST.md`, `study_definition_examples.json`,
`point_enumeration.json`, `dependency_planner.json`,
`chemistry_cache_proof.json`, `failure_caching.json`,
`direct_solve_parity.json`, `constraint_cases.json`, `pareto_cases.json`,
`scoring_cases.json`, `reanalysis_zero_resolve.json`, `live_trade_study.json`,
`study_performance.json`, `source_frozen_parity.json`,
`existing_ui_regression.json`, plus `ui_source/`, `ui_packaged/`,
`regression_5d/` and `regression_5e/`.

### Documents

`docs/engineering/TRADE_STUDY_API_DRAFT.md`,
`docs/engineering/TRADE_STUDY_UI_CONTRACT.md`,
`docs/engineering/implementation/PHASE_5F_TRADE_STUDY_ENGINE.md`.

---

## Final solve counts

| | |
| --- | --- |
| CHEMISTRY_SOLVE_COUNT | 41 for the canonical 164-point grid; 41 for 410 points; 1 for a fixed chamber; 20 for a 5 × 4 upstream grid |
| PERFORMANCE_SOLVE_COUNT | one per design point, when the stage is required; **0** for a chamber-temperature-only study |
| Re-analysis (objective / constraint / weight) | **0** and **0**, at every level including packaged |

## Interface

| | |
| --- | --- |
| CURRENT_QML_WARNINGS | **0**, source and packaged |
| Packaged state | clean rebuild from `.venv-cea`; all four diagnostics green |

## Frozen manifest

22 / 22 byte-identical.

## Blockers

None.

## Verdict

**READY FOR PHASE 5G.**

Nothing was hidden through a widened tolerance, a removed test, an unexplained
skip, a clamp, a hidden penalty, a silent fallback or a score manipulation.
Every correction — three QML binding loops, two Pareto display defects, four
audits of my own that were reading the wrong thing, and one architecture rule
that needed the third analysis domain — is recorded in full in the acceptance
manifest.
