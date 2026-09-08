# Phase 5E — Checkpoint

Ideal Rocket Performance: RocketForge-owned c\*, Cf, thrust, c_eff and Isp.

**Status:** COMPLETE

---

## Position

| Field | Value |
| --- | --- |
| CURRENT_SEGMENT | J — regressions, artifacts and documentation — **COMPLETE** |
| LAST_COMPLETED_STEP | STEP 114 — final verdict |
| NEXT_STEP | none; the phase is closed |
| NEXT_ACTION | Phase 5F, which is not started and not designed here |

---

## Opening gates

| Gate | Result | Accepted baseline | Match |
| --- | --- | --- | --- |
| Base (`.venv`) | **5799 passed, 106 skipped**, exit 0, 72.62 s | 5799 / 106 | ✅ |
| CEA-enabled (`.venv-cea`) | **5907 passed, 1 skipped**, exit 0, 70.97 s | 5907 / 1 | ✅ |
| Frozen Compressible | **22 / 22 byte-identical** | 22/22 | ✅ |

Frozen manifest verified by recomputing each file's recorded `sha256[:16]`
against the Phase 4G manifest. Digest
`8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502` therefore
still stands.

Phase 5D corrective tests are inside those totals and pass.

---

## STEP 11 — package ownership, resolved from the repository

The brief suggested `rocketforge.engineering.rocket_performance` while stating
that repository conventions win. They do, and they are unambiguous:

| Source | Statement |
| --- | --- |
| ADR-15 (`01` §ADR-15) | "thrust, Cf, c\*, Isp … belong in `engineering/nozzle/`" |
| `06` §2 module table | `engineering.nozzle` owns **thrust, Cf, c\*, Isp** |
| `12` §7 | "`engineering.nozzle` turns that into thrust, Cf, c\* and Isp (ADR-15)" |
| `12` §8 | the γ reduction adapter lives in `engineering/chamber/handshake.py` |
| `CEA_PROVIDER_CONTRACT.md` §13 | "ownership belongs to `engineering.nozzle` (ADR-15)" |
| `THERMOCHEMISTRY_CORE_API_DRAFT.md` | "c\*, Cf, Isp, thrust → `engineering.nozzle` (ADR-15)" |

**Decision:**

* `rocketforge/engineering/chamber/` — the `ChamberGas` → single-γ reduction and
  its eight preconditions;
* `rocketforge/engineering/nozzle/` — c\*, Cf, thrust decomposition, c_eff, Isp.

Both are new; `rocketforge/engineering/` was empty before this phase.

---

## STEP 13 — the handshake contract, read rather than invented

`12` §4 fixes eight preconditions. All are refusals with diagnostics, never
silent corrections:

| # | Precondition |
| --- | --- |
| P1 | provenance present and states the chemistry mode |
| P2 | `gamma > 1`, finite |
| P3 | `gas_constant > 0`, finite |
| P4 | `R == Ru / M̄` within tolerance |
| P5 | `temperature > 0`, finite |
| P6 | `condensed_mass_fraction` present **and** below the declared limit |
| P7 | `condensed_mass_fraction is None` **rejects** — unknown is not absent |
| P8 | the γ strategy is explicitly chosen |

`11` §7.3 states the refusal threshold must be *declared*, is *not zero*, and
that "trace condensed fractions at the 1e-6 level are numerical noise in a
provider's species list, not a two-phase flow". It points at `13` §4 for the
value; `13` §4 is a tolerance-policy table and **does not fix it**. Phase 5E
therefore declares it, in the engineering layer, with its own name, its own
justification and its own tests:

    engineering.chamber.SINGLE_PHASE_CONDENSED_LIMIT

It is numerically 1e-6 because `11` §7.3 argues that level is provider noise —
the same physical argument that set Phase 5D's presentation threshold, reached
independently. The two constants are **separate objects in separate layers**,
and a test asserts the engineering layer never imports
`CONDENSED_REPORTING_THRESHOLD` (brief §57).

---

## Frozen physics being consumed

| Need | Frozen v1 API |
| --- | --- |
| c\* | `mass_flow.choked_mass_flow_coefficient(gas)` — Γ(γ), the MFP at M = 1 |
| mass flow | `mass_flow.choked_mass_flow(gas, At, p0, T0)` |
| exit Mach, regime, pe/p0 | `nozzle.classify(area_ratio, pb/p0, gas)` → `NozzleRegimeResult` |
| exit temperature | `isentropic.temperature_ratio(Me, gas)` |
| speed of sound | `gas.speed_of_sound(...)` / `PerfectGas` |

`c* = sqrt(R T0) / Γ(γ)` follows directly from the frozen MFP definition
`mdot sqrt(R T0) / (A p0)` evaluated at M = 1, so the production path reuses
frozen physics rather than restating a second mass-flow formula.

---

## Files created

_none yet_

## Files modified

_none yet_

## Tests

| Suite | Result |
| --- | --- |
| Focused physics | not run |
| Application | not run |
| UI | not run |
| Oracle | not run |
| Base regression | 5799 / 106 (opening) |
| CEA regression | 5907 / 1 (opening) |

## Packaged state

Not rebuilt in this phase yet. Phase 5D bundle: 203.9 MB, 2107 files.

## QML warnings

Not yet measured in this phase.

## Blockers

None.


---

# Progress — segments A to E (partial)

## Files created

**Engineering, Qt-free and provider-free**

| File | Contents |
| --- | --- |
| `rocketforge/engineering/chamber/__init__.py` | package |
| `rocketforge/engineering/chamber/handshake.py` | `ChamberGammaBasis`, `ReducedChamberGas`, `reduce_chamber_gas`, `SINGLE_PHASE_CONDENSED_LIMIT` |
| `rocketforge/engineering/nozzle/__init__.py` | package |
| `rocketforge/engineering/nozzle/types.py` | request/result records, `PerformanceScale`, `IDEAL_MODEL_ASSUMPTIONS` |
| `rocketforge/engineering/nozzle/performance.py` | `characteristic_velocity`, `solve_ideal_performance` |
| `rocketforge/engineering/nozzle/validation.py` | the 15-relation identity matrix |

**Tests**

| File | Count |
| --- | --- |
| `tests/engineering/conftest.py` | provider-independent `ChamberGas` factory |
| `tests/engineering/test_chamber_handshake.py` | 39 |
| `tests/engineering/test_ideal_performance.py` | 98 |
| **total** | **137, all passing in the base environment** |

**Experiments / acceptance**

* `experiments/phase_5e/oracle_compare.py`
* `acceptance/phase_5e/cea_oracle_comparison.json`

## Files modified

_none yet_ — no existing production file has been touched.

---

## The two decisions this phase had to make

### 1. Package ownership — resolved from ADR-15, not from the brief

The brief suggested `engineering.rocket_performance` while stating repository
conventions win. ADR-15, `06` §2, `12` §7/§8, the CEA provider contract and the
thermochemistry API draft all say `engineering.nozzle` for performance and
`engineering/chamber/handshake.py` for the reduction. Those are the locations
used.

### 2. `GammaStrategy` alone is ambiguous — `ChamberGammaBasis` added

A `ChamberGas` carries **two** gammas and Phase 5A's `GammaStrategy` says only
*where* along the expansion to take one, never *which*:

| | canonical LOX/CH₄ chamber |
| --- | --- |
| `gamma_equilibrium` = γ_s | 1.132592 |
| `gamma_frozen` = cp/cv | 1.195567 |
| apart | **5.56 %** |
| worth | 2 % of c\*, 11 % of Isp |

So the engineering layer adds a second explicit axis, `ChamberGammaBasis`
(`EQUILIBRIUM` / `FROZEN`), required exactly as the strategy is. **No
thermochemistry domain type was changed.** The frozen basis is the one this
model actually performs — cp/cv is the exponent of a constant-composition
isentropic process — and it is what makes the CEA comparison meaningful.

---

## Measured: what CEA's Cf and Isp are referenced to

Established rather than assumed, on all three modes:

    Cf_reported + (pe/pc) * epsilon  ==  Ivac / c*      residual 6e-09 … 4e-07

So CEA's `thrust_coefficient` and `specific_impulse` are the
**optimum-expansion** values, and `specific_impulse_vacuum` carries the vacuum
pressure term. Comparing RocketForge's vacuum Cf against CEA's reported Cf
would have produced a 5.6 % "error" that is entirely a difference of reference
condition.

## Measured: the oracle comparison

LOX/LCH₄, O/F 3.4, Pc 10 MPa, Ae/At 40, throat 0.01 m².

| | c\* [m/s] | Cf opt | Cf vac | Isp opt [s] | Isp vac [s] | Me | Te [K] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CEA equilibrium | 1846.892 | 1.85966 | 1.96046 | 350.230 | 369.215 | 3.9285 | 1809.18 |
| CEA frozen at throat | 1846.892 | 1.78566 | 1.86297 | 336.295 | 350.854 | 4.3038 | 1248.65 |
| CEA frozen at chamber | 1809.226 | 1.79502 | 1.87091 | 331.162 | 345.164 | 4.3389 | 1167.58 |
| **RF frozen basis** | **1810.013** | 1.80406 | 1.88903 | 332.975 | 348.658 | 4.2142 | 1314.87 |
| **RF equilibrium basis** | **1845.820** | 1.85457 | 1.96351 | 349.069 | 369.574 | 3.8770 | 1802.30 |

### Classification — `PHASE_5E_MODEL_MATCH_NOTE`

**No CEA mode is exactly like-for-like.** RocketForge v1 is *calorically*
perfect (cp constant); every CEA mode is calorically imperfect (cp from the
NASA polynomials at the local temperature). No chemistry mode removes that.

What *can* be matched is the chemistry assumption, which makes
**frozen basis ↔ frozen-at-chamber** the nearest partner: both hold the chamber
composition fixed and both use the specific-heat ratio of that composition.

| Quantity | RF frozen − CEA frozen-at-chamber | Classification |
| --- | --- | --- |
| c\* | **4.35e-04** | closest cross-model difference — the throat is a short expansion from the chamber, so the caloric mismatch has barely accumulated |
| Cf optimum | 5.04e-03 | model difference |
| Isp optimum | 5.48e-03 | model difference |
| Exit temperature | 1.26e-01 | model difference — the caloric assumption over the whole expansion |

The equilibrium basis agrees with CEA equilibrium to 3.3e-03 on Isp, and that
is **not** validation: γ_s is *defined* as the isentropic exponent of the
shifting expansion, so a constant-γ_s model approximates it by construction.
Close agreement between different models is recorded as a model difference.

---

## Verified so far

| Check | Result |
| --- | --- |
| c\* vs the independent analytic form | 4e-16 relative, across 5 gases |
| identity matrix, 15 relations | worst 3.7e-16, both scale modes, three ambients |
| c\* invariance under ε, pa, At | exact equality |
| pressure-thrust sign, all three cases | positive / zero / negative |
| optimum-expansion identity c_eff = Ve at pe = pa | 1e-12 |
| scale doubling | normalized unchanged, absolutes ×2 to 1e-13 |
| mass-flow scale round trip | throat area recovered to 1e-13 |
| shock-inside-nozzle refusal | `NOZZLE_REGIME_UNSUPPORTED`, named |
| CEA-free operation | full solve, `sys.modules` free of `cea` |
| mutation proofs | 16, each asserting the fixture changed first |

---

## SEGMENT F — application service and controller

### Files

| File | What it owns |
| --- | --- |
| `rocketforge/application/analysis/performance_service.py` | `PerformanceCase`, `AmbientCondition`, `PerformanceOutcome`, the seven outcome kinds, `solve_performance`, the display rows, `reference_condition_results` |
| `rocketforge/application/analysis/performance_oracle.py` | `OracleOutcome`, `run_oracle`, `oracle_comparison_rows`. The **only** module here that reaches a provider |
| `rocketforge/application/analysis/performance_controller.py` | `RocketPerformanceController`, the Qt facade |
| `rocketforge/providers/cea/provider.py` | `rocket_oracle()` — additive, public, mirrors the Phase 5D `species_table()` decision |
| `rocketforge/application/analysis/thermochemistry_controller.py` | `chamber_outcome()` — additive, a plain Python method, deliberately **not** a Qt property |

### ZERO CHEMISTRY RE-SOLVE — § 80, blocking

Proved twice, behaviourally and structurally.

**Behaviourally**, by call count. The stub provider records every
`solve_chamber` it receives. Starting from one solved chamber (baseline = 1
call), each of these was changed and performance recomputed — first through
`solve_performance` directly, then again through the real Qt controller:

| Input changed | Chamber solves |
| --- | --- |
| area ratio (small, large, five times each) | **0** |
| ambient pressure (vacuum / sea level / custom) | **0** |
| scale (throat area, mass flow) | **0** |
| gamma basis, gamma strategy | **0** |
| 15 combined changes in sequence | **0** |
| reference-condition re-evaluation for the oracle table | **0** |
| reading every Qt property on the controller | **0** |

Negative control: solving a *different* chamber case raises the count by
exactly 1, so the counter is not vacuously constant.

**Structurally**, by import. `performance_service` imports neither
`rocketforge.providers` nor the provider gateway, so no expression in it can
start a chemistry solve. It also does not import `performance_oracle`, so a
provider's c\*, Cf or Isp cannot reach a RocketForge performance field even by
accident. Negative control: the oracle module *does* import the gateway.

### Upstream-change invalidation — § 81

When the Thermochemistry workspace produces or clears a chamber state, the
performance result is **marked**, never recomputed and never relabelled:

| Property | Behaviour |
| --- | --- |
| `chamberSuperseded` | compares by **identity** — two chambers with equal numbers are still two different answers |
| result rows | unchanged; nothing is silently recomputed |
| `resultHeadline` | unchanged; it is built from the case the result carries |
| `hasResult` | still true; the old answer is kept and flagged, not discarded |
| `resultStale` | separate flag, for the *inputs* moving rather than the chamber |

### The oracle, and what keeps it an oracle

`rocket_oracle()` is a **separate** CEA run, invoked only by an explicit user
action. Nothing on the performance path reads it, and it returns an
`OracleOutcome` — plain floats under their own names, not an
`IdealRocketPerformance` — so a substitution would have to be written
deliberately.

Measured on LOX/LCH4, O/F 3.4, 100 bar, Ae/At 40, frozen chamber basis:

| Quantity | RocketForge | CEA frozen-at-chamber | Difference | Classification |
| --- | --- | --- | --- | --- |
| c\* | 1810.01 | 1809.23 | +0.04 % | model difference |
| Cf, optimum expansion | 1.80406 | 1.79502 | +0.50 % | model difference |
| Isp, optimum expansion | 332.975 | 331.162 | +0.55 % | model difference |
| Isp, vacuum | 348.658 | 345.164 | +1.01 % | model difference |

### Defect found and fixed during this segment

The first version of the comparison table placed RocketForge's figure **at the
user's chosen ambient** beside CEA's, which is quoted at optimum expansion.
That is the error the Segment E dataset was written to warn about, and on this
case it produced a spurious −4.93 % where the honest figure is +0.55 %.

Fixed by `reference_condition_results()`: the nozzle — not the chemistry — is
re-solved at each reference condition the provider quotes, and every row
compares like with like. The gas reduction object is reused by identity, which
a test asserts.

### Second defect: an order-dependent test of my own

`test_a_full_performance_solve_runs_with_no_chemistry_library_loaded` read
`sys.modules` after solving and required no `cea` entry. `sys.modules` is
process-global, so the assertion was really "nothing anywhere in this pytest
session has imported a chemistry library" — a property of collection order, and
false as soon as an application test that legitimately exercises the provider
ran first. It had been passing by luck.

Replaced by two tests that are each order-independent, and together stronger:

* a **delta** check in process — solving imports no chemistry module that was
  not already loaded; and
* a **clean-interpreter** check — a subprocess imports the chain, reduces a
  chamber state, solves, verifies the identities, and asserts `sys.modules`
  holds no `cea`, `cantera` or `CoolProp` entry at all.

The second is the claim the phase actually makes: a build with no chemistry
library installed can still compute ideal rocket performance.

### Tests

| Module | Tests |
| --- | --- |
| `tests/application/test_performance_service.py` | 65 |
| `tests/application/test_performance_controller.py` | 58 + 4 CEA-only |

### Gates after SEGMENT F

| Gate | Result |
| --- | --- |
| Base (`.venv`) | **6075 passed, 113 skipped**, exit 0, 57.88 s |
| CEA-enabled (`.venv-cea`) | **6190 passed, 1 skipped**, exit 0, 64.68 s |
| Frozen Compressible | **22 / 22 byte-identical** |

---

## SEGMENT G — the Rocket Performance workspace

Third analysis domain, its own sidebar section, three views of one calculation:
**Performance**, **Model**, **Provider comparison**.

| File | Role |
| --- | --- |
| `ui/pages/RocketPerformancePage.qml` | header, view selector, stack |
| `ui/pages/rocketperformance/PerfCalculator.qml` | inputs and results |
| `ui/pages/rocketperformance/PerfResultHeader.qml` | what the result is for, and its caveats |
| `ui/pages/rocketperformance/PerfResultGroup.qml` | one physics group of quantities |
| `ui/pages/rocketperformance/PerfModel.qml` | assumptions, reduction, identities, provenance |
| `ui/pages/rocketperformance/PerfOracle.qml` | the provider's own answer, in its own panel |

Wired in `main.py` (a fourth singleton, `RocketPerformance`, constructed with
the chemistry controller it reads), `ui/data/Navigation.qml` (a new
`performanceDomain`) and `ui/shell/SideNav.qml`. `"Performance"` was removed
from the planned-modules list: it exists now, so advertising it as planned
would be false.

**No shared component was changed.** A test asserts none of them mentions this
workspace.

### Two layout defects, both caught by reading the captures

**Nested layouts default `Layout.fillHeight` to true**, unlike plain items. The
result header competed with the results Flickable for the panel's height and
won, leaving the performance numbers with none. Not caught by any test — which
is what the visual gate is for.

**`anchors.verticalCenter` inside a `RowLayout`** produced 1464 Qt warnings
in an intermediate run. Replaced with `Layout.alignment`; every accepted run
afterwards, source and packaged, reported **0** Qt warnings.

### One wording defect

The assumption panel concatenated the ideal model's list with the reduction's,
and the two overlap — both say the gas is single-phase and constant-property,
in slightly different words. A list that appears to repeat itself undermines
the panel it is trying to make authoritative. Split into two attributed groups.

---

## SEGMENT H — architecture rules

`tests/application/test_performance_ui_architecture.py`, 32 rules. The Phase 5D
boundary re-checked on the new files, plus a second boundary running the other
way: the provider's performance quantities must not be presented as
RocketForge's, in a workspace where both appear.

| Rule | |
| --- | --- |
| only the controller imports Qt | the other three modules run headless |
| no QML imports a provider or a physics module | |
| no QML names a chemistry library as code | |
| **no QML names a provider even as a label** | the name is data, read from the result; a hard-coded one would survive a provider change and start lying |
| `Math` restricted to layout arithmetic | with a negative control |
| no physical constant in QML | with a negative control |
| no unit conversion in QML | with a negative control |
| the calculator view never reads an oracle property | |
| no QML computes a difference between two answers | |
| no string promises real-engine performance | negation-aware, with a two-way negative control |
| no compressible page mentions this workspace | and the chemistry workspace does not reach into it |

### A Phase 5D rule, rescoped rather than weakened

`test_no_compressible_page_was_modified_by_this_phase` was written as an
exclusion — "every page that is not thermochemistry must not mention
Thermochemistry". That was the same claim only while this was the last
workspace in the product. It silently began asserting that the *new* workspace
may not name the tab a user must visit to get a chamber state, which it must.

Rescoped to name the analysis domains explicitly, with an added test that the
exclusion covers only those, so it cannot be widened later to make a failure go
away. Its force on the 30+ compressible pages is unchanged.

### One audit that had to learn about negation

The wording audit bans "recommended design". This workspace's own honest
tooltip says "an example, **not** a recommended design". Flagging that would
push the disclaimer out of the interface — the same class of false positive as
reading "isp" out of `chamberPressureDisplay`, which cost three separate fixes
in Phase 5D. The audit now skips a banned phrase preceded by a negation, and
its negative control fires on the claim while staying silent on the disclaimer.

---

## SEGMENT I — the packaged build

`--selftest-rocket-performance <directory>`, in
`rocketforge/application/perfsmoke.py`. Sibling of the Phase 5D UI smoke, with
one thing neither of the other diagnostics can do: **it counts provider calls
across the tour.** A frozen build that quietly re-solved chemistry on every
input change would still look correct in a screenshot.

| | Source | Packaged |
| --- | --- | --- |
| Captures | 29 | 29 |
| Qt messages | **0** | **0** |
| Chamber solves from input changes | **0** | **0** |
| Resolutions | 2560×1440, 1920×1080, 1366×768, + light theme | same |

**Parity: 5013 fields compared, 0 differing, 0 present in only one build.**

Built from `.venv-cea` so the bundled provider is present. No synthetic desktop
input: a test bans `QTest`, `sendEvent`, `postEvent`, `pyautogui` and the rest
from the diagnostic.

---

## SEGMENT J — regressions, artifacts, documentation

### Closing gates

| Gate | Accepted baseline | Result | |
| --- | --- | --- | --- |
| Base (`.venv`) | 5799 / 106 | **6108 passed, 113 skipped**, exit 0 | ✅ |
| CEA-enabled (`.venv-cea`) | 5907 / 1 | **6223 passed, 1 skipped**, exit 0 | ✅ |
| Frozen Compressible | 22 / 22 | **22 / 22 byte-identical** | ✅ |

Phase 5E adds **308 tests, 7 skipped without a provider**.

### Artifacts

| Path | |
| --- | --- |
| `acceptance/phase_5e/ACCEPTANCE_MANIFEST.md` | the manifest |
| `acceptance/phase_5e/cea_oracle_comparison.json` | three CEA modes against two RocketForge bases |
| `acceptance/phase_5e/nasa_performance_reference.json` | the external NASA case |
| `acceptance/phase_5e/ui_source/` | 29 captures + report |
| `acceptance/phase_5e/ui_packaged/` | 29 captures + report |
| `acceptance/phase_5e/ui_parity.json` | 5013 fields, 0 differing |

### Documents

| Path | |
| --- | --- |
| `docs/engineering/ROCKET_PERFORMANCE_API_DRAFT.md` | the API |
| `docs/engineering/ROCKET_PERFORMANCE_UI_CONTRACT.md` | the interface contract |
| `docs/engineering/implementation/PHASE_5E_IDEAL_ROCKET_PERFORMANCE.md` | the phase report |

---

## Blockers

None.

## Verdict

**READY FOR PHASE 5F.**

Nothing was hidden through a widened tolerance, a removed test, an unexplained
skip, a clamp or a provider substitution. Three corrections are recorded in
full in the acceptance manifest, one of them to a test of my own that had been
passing by luck.
