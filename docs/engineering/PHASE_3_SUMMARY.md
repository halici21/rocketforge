# Phase 3 Summary — Engineering Architecture and Compressible Flow Specification

Date: 2026-08-30
Project: `C:\Users\erayh\Documents\Python\rocket`
UI status: **ROCKETFORGE UI FOUNDATION v1.0 — ACCEPTED / FROZEN** (untouched)

---

# Verdict

**READY FOR PHASE 4**

Every acceptance criterion of task §146–§150 is met. The architecture is
unambiguous, all public APIs are proposed with signatures, all data models are
specified, every equation is written out, every inverse problem is specified with
its branch behaviour and root-finding method, all domains are tabulated, the test
matrix is defined with authoritative reference values, and the nozzle regimes and
internal-shock algorithm are fully specified. No production code was written.

---

## Architecture

Seven layers, with the dependency direction enforced by a test rather than by
convention:

```
ui  ->  application  ->  providers
             |               (implement interfaces declared in physics)
             +->  engine  ->  engineering  ->  physics  ->  core
```

A new pure-Python package `rocketforge/` sits beside the frozen `ui/`. It imports
no Qt, requires no `QGuiApplication`, and is usable from a notebook, a script or
an optimiser. `physics` may never import `engineering`, `providers`,
`application` or PySide6; external libraries (CoolProp, CEA, Cantera) are
confined to `providers/`, which satisfy protocols declared in `physics` —
dependency inversion, so the physics layer stays importable with none of them
installed.

QML receives prepared, formatted state from per-page controllers. It never
computes a ratio, a Mach number, a unit conversion or an angle conversion.

---

## Compressible Scope

`rocketforge/physics/compressible/` — nine modules, one concern each:

| Module | Contents |
| --- | --- |
| `gas` | `PerfectGas`, cp/cv, speed of sound, γ and R domains |
| `isentropic` | all γ-and-M ratios, starred ratios, area-Mach forward and both inverse branches, Mach angle, dimensional state |
| `mass_flow` | mass-flow parameter, Γ(γ), choked flow, mass flux, critical pressure ratio |
| `normal_shock` | M₂, p, ρ, T, p₀ jumps, entropy, A₂\*/A₁\* |
| `oblique_shock` | θ-β-M, closed-form θ_max and β_sonic, weak/strong branches, detachment, θ-β-M curve data |
| `prandtl_meyer` | ν, ν_max, numerical inverse, expansion and compression turns |
| `fanno` | adiabatic constant-area friction relations, **Fanning convention fixed**, both-branch inverse, duct problem |
| `rayleigh` | frictionless constant-area heating relations, T₀-ratio inverse, heat-addition problem, the non-trivial extrema |
| `nozzle` | quasi-1D C-D nozzle: three criticals, seven regimes, internal shock location, distributed arrays |

Model: steady, one-dimensional (quasi-1D for the nozzle), calorically perfect,
constant γ and R. No chemistry, no variable γ, no back door for one.

---

## Critical Decisions

* **SI floats internally; units converted only at the application boundary.**
  Pint is not a dependency of the physics core — unit algebra inside a
  2000-point interactive sweep costs more than the boundary converter it would
  replace.
* **Radians internally, degrees on screen.** Names ending `_deg` are forbidden
  below `application/` and the architecture test enforces it.
* **Two-tier API.** Algebraic total relations return bare floats/arrays;
  anything branched, iterative or classified returns `Solution[T]` carrying
  status, diagnostics, convergence data and provenance.
* **Branches are enums and are never guessed.** `mach_from_area_ratio` has no
  default branch at all — the argument is required.
* **Raise for invalid input; report for unattainable physics.** `ν(0.5)` raises;
  a detached shock returns `NO_SOLUTION` with a diagnostic. Nothing is ever
  silently clamped.
* **NumPy yes, SciPy no (for v1), Pandas no.** Every v1 inverse is a scalar
  bracketed monotone root; an internal Brent avoids adding a large binary wheel
  to a frozen build whose packaging is only just proven stable, and returns the
  diagnostics `Solution` needs.
* **Frozen dataclasses everywhere**, JSON-serialisable by construction, so
  results can cross a thread, be cached, be stored and be regression-recorded.
* **Fundamental gas dynamics and rocket nozzle design are different layers.**
  Thrust, Cf, c\*, Isp and contour generation are absent from `physics` by
  design and belong to `engineering/nozzle/`.
* **Model identifiers are versioned from day one** (`perfect_gas_isentropic_v1`).
* **Solver diagnostics reuse the existing `EngineModel.problems` record shape**,
  so the first engine solver needs no QML change to report a warning.

---

## Numerical Strategy

* **Analytic wherever a closed form exists** — three of the four isentropic
  inverses, θ_max, and β_sonic. Two of those (θ_max, β_sonic) are commonly
  implemented as searches; both closed forms were verified numerically to 7–8
  significant figures and reduce an iteration to one square root.
* **Brent on a derived bracket** for every remaining inverse: area-Mach,
  Prandtl–Meyer, oblique β, Fanno, Rayleigh, nozzle shock position. Newton is
  rejected — dA/dM = 0 and dν/dM = 0 at M = 1, so a Newton step near sonic
  leaves the domain or lands on the wrong branch.
* **Brackets derived from asymptotics, not guessed.** `M_max = 100` is justified
  (A/A* ≈ 4.6 × 10⁷ there), not arbitrary.
* **Near-sonic conditioning quantified rather than hidden.** A/A* − 1 ≈
  [2/(γ+1)]ε², 4fL\*/D ≈ [4/(γ(γ+1))]ε², 1 − T₀/T₀\* ≈ [4/(γ+1)²]ε², and
  ν ≈ [4√2/(3(γ+1))]ε^{3/2} — all four derived and confirmed across γ. The
  consequence: Mach near sonic cannot be resolved better than ~10⁻⁸ in float64,
  so the policy is a sonic tolerance plus an honest `NEAR_SONIC` warning, not
  tighter tolerances.
* **Named tolerance categories**, not one epsilon: comparison, root, sonic,
  branch, angle, pressure and domain limits, gathered in a frozen `ToleranceSet`
  passed explicitly so determinism survives.
* **Scalar-or-array for algebraic relations; scalar-only for solvers**, with
  explicit `*_array` variants where a vector inverse is genuinely needed.
* `float64` throughout. Deterministic: same inputs plus same model version give
  bit-identical results.

---

## Verification Strategy

Equation → implementation → unit tests → reference cases → property tests →
round-trip and limit tests → cross-validation → **only then** UI integration.

* **Reference values are stored as data**, in `tests/reference_data/*.json`, one
  row per case with its own tolerance, source and a `confirmed` field.
* The reference values in this specification were generated by evaluating the
  documented equations at `float64` and are internally consistent by
  construction. Each starred case must additionally be **confirmed against NACA
  1135 / Anderson / Shapiro by a human** before its module is accepted — no
  module ships with `"pending"` rows.
* **Property tests carry the physics**: MFP maximised at M = 1; A/A* minimised at
  exactly 1; p₀₂/p₀₁ < 1 and Δs ≥ 0 across every shock; ρ₂/ρ₁ bounded by
  (γ+1)/(γ−1); ν monotone; friction driving both branches to sonic; T/T\*
  peaking at M = 1/√γ in Rayleigh flow (and therefore *falling* while heat is
  added between 1/√γ and 1); the three nozzle criticals strictly ordered; mass
  flow identical across every choked regime.
* **The duplication audit is executable.** Oblique shock results must equal
  normal-shock results at M₁ sin β to machine precision; PM ratios must equal
  quotients of isentropic values; nozzle stations must equal direct isentropic
  and normal-shock calls. Machine precision, so a re-derivation cannot pass.
* Every module is additionally tested at γ = 1.2, 1.3 and 1.66, because a
  reference set at γ = 1.4 alone cannot catch a γ-dependent error.
* Coverage percentage is reported but is never the acceptance criterion.

---

## Files Created

```
rocket/docs/engineering/
  01_engineering_architecture.md              layers, providers, units, angles,
                                              determinism, provenance, 16 ADRs
  02_data_model_and_api_contracts.md          state objects, Solution model, errors,
                                              branches, sweeps, registry, full API
                                              signatures and result dataclasses
  03_compressible_flow_specification.md       every equation, domain, limit, branch,
                                              nozzle regimes and shock algorithm,
                                              reference values, mandatory pseudocode
  04_numerical_methods_and_domain_policy.md   root methods, brackets, tolerances,
                                              near-sonic conditioning, domain table,
                                              extreme inputs, scalar/array policy
  05_verification_and_validation_plan.md      test tree, reference-data format,
                                              property/round-trip/limit/invalid/
                                              convergence tests, UI integration gate
  06_future_module_dependency_map.md          module table, forbidden dependencies,
                                              boundary contracts, cycle graphs,
                                              component-type mapping
  07_ui_integration_contracts.md              per-page input/output contracts against
                                              the frozen QML, plus recorded future
                                              UI requirements
  PHASE_3_SUMMARY.md                          this file
```

---

## Source Changes

**No application source files modified.**

Verified: no file under `ui/`, and none of `main.py`, `packaging/`,
`build_exe.bat`, `run.bat`, `requirements.txt` or `README.md`, has a modification
time later than the start of this phase. The only files written are the eight
documents above, all under `docs/engineering/`.

---

## UI Changes

**None.** No QML file was opened for writing, no theme, component, page,
workspace or engine-model file was altered. Seven future UI requirements are
*recorded* in `07` §9 — including the two that block a specific capability (a
branch selector for the `A/A*` input mode, and a friction-convention label on the
Fanno page) — but none is actioned, and both fall on pages that are currently
placeholders anyway.

---

## Physics Code

**None.** No solver, no relation, no root finder, no unit conversion and no
`rocketforge/` package was created. Reference values in `03` §11 were produced by
a throwaway script in the session scratchpad, outside the project, purely so the
specification's expected values are consistent with the equations it states
rather than quoted from memory. Nothing from that script is part of the project.

---

## Open Questions

Three, none of which blocks Phase 4.

1. **Sweep transport to QML.** Whether a 2000-point series should cross the
   boundary as a `QVariantList` or via a buffer is a measurement, not a design
   decision. Start with lists; optimise only if a frame budget is actually
   missed.
2. **Rayleigh inverse scope.** One inverse (T₀ ratio → M) plus the duct problem
   is recommended for v1; the T/T\* inverse is deferred *with its reason
   recorded* (T/T\* is not monotone on the subsonic branch, so it needs a
   three-way branch). Worth a second opinion from whoever will teach with it.
3. **Nozzle geometry input.** The frozen Nozzle Lab exposes an area ratio, not an
   arbitrary A(x). The solver contract accepts both; whether the page ever gains
   an A(x) import is a later UI question.

---

## Recommended Phase 4 Sequence

Ordered by dependency, with each step usable and testable before the next
begins.

1. **`core`** — errors, `Solution`/`Diagnostic`/`Convergence`, `ToleranceSet`,
   `RelationRef`, units, and **`numerics/roots.py` (Brent) with its own full test
   suite**. Nothing physical, and everything downstream depends on it.
2. **`test_architecture.py`** — the import allow-list and the no-PySide6 proof.
   Written *before* the physics, so the boundary is never accidentally crossed.
3. **`gas`** — `PerfectGas` with its validation and domains.
4. **`isentropic`** — forward relations, the three analytic inverses, then the
   area-Mach inverse with both branches. The largest single step, and the one
   that establishes the house style for every module after it.
5. **`mass_flow`** — small, and it exercises the dimensional half of the API for
   the first time.
6. **`normal_shock`** — self-contained, and a prerequisite for two later modules.
7. **`prandtl_meyer`** — first use of a numerical inverse against a closed-form
   ceiling; reuses `isentropic` for its ratios.
8. **`oblique_shock`** — reuses `normal_shock` entirely; adds the closed-form
   θ_max/β_sonic and the branch/detachment logic.
9. **`fanno`** — independent of 6–8; fixes the friction convention and its guard
   test early.
10. **`rayleigh`** — independent; the extrema tests matter more here than
    anywhere else.
11. **`nozzle`** — last, because it integrates 4, 5 and 6. Criticals and
    classification first, then the internal shock solve, then the distributed
    output with the duplicated shock station.
12. **Sweep APIs** (`Series`, `SweepResult`, `Case`, sampling helpers) across all
    modules.
13. **Equation registry** populated for every relation implemented above.
14. **Reference data confirmed** against NACA 1135 / Anderson / Shapiro, and the
    `"pending"` fields cleared.
15. **UI integration**, page by page, each gated on `05` §16. Order:
    Equation Library (cheapest, no numerical risk) → Isentropic (proves the whole
    chain) → Normal Shock → Mass Flow → Prandtl–Meyer → Oblique Shock → Fanno →
    Rayleigh → Nozzle Lab (the integration test) → Compare and Charts.

**The exact first task:** create `rocketforge/core/` and implement
`core/numerics/roots.py` — a Brent solver returning `(root, RootReport)` with
`converged`, `iterations`, `residual`, `bracket` and `method` — together with
`tests/core/test_roots.py` covering analytic roots, a flat-derivative root, a
root sitting exactly on a bracket end, a bracket with no sign change (must raise
`BracketError`), `max_iter` exhaustion (must return the best iterate with
`converged=False`, never raise and never loop), and bit-level determinism across
repeated runs.

Everything numerical in Phase 4 rests on that one function, and it is the only
piece of the plan where we are replacing a well-tested library with our own code
— so it is the piece that must be proven first.
