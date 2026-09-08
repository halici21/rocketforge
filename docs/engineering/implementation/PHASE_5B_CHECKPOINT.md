# Phase 5B — Execution Checkpoint

**PHASE 5B COMPLETE.** This file recorded progress for checkpointed
continuation; the continuation was never needed. The final report is
`PHASE_5B_THERMOCHEMISTRY_CORE.md`.

---

## Status

```
PHASE                = 5B  (provider-independent thermochemistry core)
SEGMENT              = COMPLETE
LAST_COMPLETED_STEP  = 54
NEXT_STEP            = none -- Phase 5B is finished
NEXT_ACTION          = none. Phase 5C is NASA CEA v3 production provider; see
                       PHASE_5B_THERMOCHEMISTRY_CORE.md section 16.
CURRENT_TEST_RESULT  = 5542 passed / 1 skipped / exit 0 (twice, identical)
CURRENT_FAILING      = none
FROZEN_MANIFEST      = PASS (22 files byte-identical, opening and closing)
VERDICT              = READY FOR PHASE 5C
```

---

## Baseline

| Gate | Result |
| --- | --- |
| Opening regression | **5285 passed, 1 skipped**, exit 0, 60.55 s |
| Frozen manifest, opening | **PASS** — 22 files byte-identical |
| Digest | `8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502` |

---

## Step log

| Step | Description | Status |
| --- | --- | --- |
| 1 | Read Phase 5A, 5B-0, core architecture docs | **done** |
| 2 | Opening regression via `.venv\Scripts\python.exe` | **done** |
| 3 | Verify frozen Compressible manifest | **done — PASS** |
| 4 | Create this checkpoint | **done** |
| 5 | Supersede provider ADRs with 5B-0 evidence | **done** |
| 6 | Inspect core constants / Solution / errors / tolerances | **done** |
| 7 | Define Phase 5B package layout | **done** |
| 8 | Foundational enums | **done** |
| 9 | Species identity + elemental representation | **done** |
| 10 | Species validation / immutability tests (35 tests) | **done** |
| 11 | Composition domain | **done** |
| 12 | Sum / canonicalization policy | **done** |
| 13 | mole↔mass conversion | **done** |
| 14 | Mean molar mass | **done** |
| 15 | Specific gas constant relation | **done** |
| 16 | Elemental inventory | **done** |
| 17 | Element-balance validator | **done** |
| 18 | Composition/element mutation proofs (5 proofs) | **done** |
| 19 | PropellantDefinition | **done** |
| 20 | PropellantStream | **done** |
| 21 | Blend representation | **done** |
| 22 | PropellantPairDefinition | **done** |
| 23 | Canonical O/F type/validation | **done** |
| 24 | PropellantPairReferenceCase schema | **done** |
| 25 | Propellant/stream/pair tests | **done** |
| 26 | Thermodynamic-state DTOs | **done** |
| 27 | State property consistency validation | **done** |
| 28 | R/Mbar mutation proof | **done** |
| 29 | cp/cv/gamma mutation proof | **done** |
| 30 | Ideal-gas mutation proof | **done** |
| 31 | Chamber thermochemical state DTO | **done** |
| 32 | Equilibrium/combustion request DTO | **done** |
| 33 | Equilibrium/chemistry mode contracts | **done** |
| 34 | Provider capabilities | **done** |
| 35 | Provider provenance | **done** |
| 36 | ThermochemistryProvider protocol | **done** |
| 37 | Fake provider + contract tests | **done** |
| 38 | JSON serialization tests | **done** |
| 39 | Public-import tests | **done** |
| 40 | Architecture/static source tests | **done** |
| 41 | Run full new thermochemistry test set | **done** |
| 42 | Contract fitness vs real CEA API evidence | **done** |
| 43 | Contract fitness vs Cantera evidence | **done** |
| 44 | Resolve contract deficiencies | **done** |
| 45 | Provisional API document | **done** |
| 46 | Source/dependency/formula audit | **done** |
| 47 | Headless PySide-blocked test | **done** |
| 48 | Full RocketForge regression | **done** |
| 49 | Repeat full suite | **done** |
| 50 | Recompute frozen manifest | **done** |
| 51 | Verify `.venv` provider-free | **done** |
| 52 | Write Phase 5B report | **done** |
| 53 | Mark checkpoint COMPLETE | **done** |
| 54 | Final verdict | **done** |

---

## Findings from step 6 — core infrastructure inspection

Decisions these facts settle, so they are not re-derived on a later context:

| Fact | Consequence |
| --- | --- |
| **`UNIVERSAL_GAS_CONSTANT = 8.31446261815324` J/(mol·K) already exists** in `rocketforge/core/constants.py` (CODATA, exact since the 2019 SI redefinition) | §46 satisfied by **reuse**. No `FROZEN_CORE_EXTENSION_DECISION_REQUIRED`. That file is frozen and is only read. |
| `STANDARD_GRAVITY = 9.80665` also present | Available later for Isp; not used in 5B |
| `core.result` provides `Status` (OK / OK_WITH_WARNINGS / NOT_CONVERGED / NO_SOLUTION), `Severity` (INFO/WARNING/ERROR), `Diagnostic(code, severity, message, field, detail)`, `Convergence`, `Solution[T]` with `value/status/diagnostics/provenance/convergence/inputs`, `.ok`, `.unwrap()`, `.with_diagnostics()` | Reuse directly (§113). No new result framework. |
| `core.errors` hierarchy: `RocketForgeError → InputError → DomainError`, plus `GasModelError`, `NumericalError` branches. Policy: **raise for invalid input, report for unattainable physics** | Thermochemistry errors subclass these; only genuinely new ones added (§183) |
| `core.provenance` holds `RelationRef`/`EquationRecord` — *equation* traceability, a different concept from *provider* provenance | `ThermochemistryProvenance` is new and lives in the thermochemistry package |
| `core.tolerances.ToleranceSet` is one frozen dataclass of named tolerances with `DEFAULT_TOLERANCES` | Follow the same pattern for a separate thermochemistry tolerance set (§164) |
| `physics/__init__.py` exports nothing (`__all__ = []`); `physics/compressible/__init__.py` owns its API | Same convention for `physics/thermochemistry/__init__.py`. Avoids the Phase 4F package-root export defect (§242) |
| **`tests/test_architecture.py` already bans `cea`, `cantera`, `rocketcea`, `CoolProp`, `pyCEA` outside `providers`** via `EXTERNAL_LIBRARY_ROOTS` | §16/§150 largely satisfied by existing rules — **no weakening needed, and no new rule required for provider imports** |
| Existing rules also cover Qt below `application`, scipy anywhere, `_deg` naming, and the layer matrix (`physics` → `core`, `physics` only) | Thermochemistry importing application/engineering/engine already fails today |
| **Gap:** `compressible` and `thermochemistry` are both in the `physics` layer, so the layer matrix permits `compressible → thermochemistry` | **New additive rule needed** at step 40 (§152) |

---

## Decisions made

| # | Decision | Rationale |
| --- | --- | --- |
| D1 | Reuse `core.constants.UNIVERSAL_GAS_CONSTANT`; do not define a second Ru | §46/§47; the frozen file is read, never modified |
| D2 | Reuse `Solution`/`Diagnostic`/`Status`; no parallel result type | §113 |
| D3 | `physics/thermochemistry/__init__.py` is the public surface; `physics/__init__.py` stays empty | matches the compressible convention |
| D4 | Provider-import architecture rules already exist — add only the intra-physics rule | do not duplicate or weaken existing rules |

---

## Files created

Production, all under `rocketforge/physics/thermochemistry/`:
`__init__.py`, `types.py`, `errors.py`, `tolerances.py`, `species.py`,
`composition.py`, `propellants.py`, `provenance.py`, `requests.py`,
`states.py`, `protocols.py`, `validation.py`, `serialization.py` — 13 modules.

Tests, under `tests/physics/thermochemistry/`:
`conftest.py`, `test_species.py`, `test_composition.py`.

## Files modified

* `docs/engineering/PHASE_5A_SUMMARY.md` — ADR-20/21 marked SUPERSEDED with
  their original text preserved; ADR-31 added.
* `docs/engineering/10_thermochemistry_provider_strategy.md` — superseding
  banner at the top; body preserved.

No production file outside `physics/thermochemistry/` has been touched.

---

## Deviations from Phase 5A, recorded not silent

| # | Deviation | Justification |
| --- | --- | --- |
| V1 | `Mixture` (09 s.5.1) implemented as **`Composition`** with an explicit `basis` field | An implicit basis is the ambiguity 09 s.4.3 forbids for `SpeciesAmount`; forbidding it there and relying on it here would be inconsistent. Strictly stronger contract. |
| V2 | `PropellantDefinition.cea_name` implemented as **`provider_names: Mapping[str, str]`** | Phase 5B spec s.206 forbids a public field named after one vendor. Same intent, extends to Cantera and beyond. |
| V3 | Protocol takes a **`ChamberEquilibriumRequest`** rather than names + scalars (09 s.9.1) | Phase 5B-0 proved reactant temperature and phase are first-class inputs (74.9 K of Tc); a name plus a scalar cannot carry a stream's actual condition. |
| V4 | Protocol returns **`Solution[ChamberGas]`**, not a bare value (09 s.9.4 / ADR-30) | `core/errors.py` policy: non-convergence is reported, never raised. Phase 5B-0 found CEA exposing exactly such a `converged` flag; a bare return has nowhere to put it. Adapters stay thin; no provider type crosses the boundary. |
| V5 | `PropellantStream.mass_flow` is **optional**, not mandatory (09 s.10) | A chamber equilibrium needs the ratio, not the absolute rate (spec s.192). `mixture_ratio_from_streams` still requires it and says so. |

## Unresolved issues

None. No blocking defect, no `PHASE_5A_SPEC_CONFLICT`, no
`FROZEN_CORE_EXTENSION_DECISION_REQUIRED` — `UNIVERSAL_GAS_CONSTANT` already
existed in the frozen `core/constants.py` and is reused read-only.


---

## Closing record

| Gate | Result |
| --- | --- |
| Opening regression | 5285 passed, 1 skipped, exit 0, 60.55 s |
| Closing run 1 | **5542 passed, 1 skipped**, exit 0, 47.50 s |
| Closing run 2 | **5542 passed, 1 skipped**, exit 0, 47.77 s — identical |
| New tests | **257** |
| Existing architecture rules | 41, green, unmodified |
| Additive architecture rules | 18 |
| Frozen manifest | 22 files byte-identical |
| Main `.venv` | provider-free |
| Requirements / QML / spec | unchanged |

**One defect the full gate caught that the subset runs did not:** the new
architecture test was first named `test_architecture.py` and collided with
`tests/test_architecture.py`. With no `__init__.py` files pytest could not
import both and the entire suite errored during collection. Renamed to
`test_thermochemistry_architecture.py`. A green subset is not a green suite.

**Status: COMPLETE.**
