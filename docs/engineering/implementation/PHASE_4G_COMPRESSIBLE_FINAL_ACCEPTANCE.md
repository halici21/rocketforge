# Phase 4G — Compressible Flow Final Acceptance and API Freeze

# Verdict

**COMPRESSIBLE FLOW v1.0 — ACCEPTED / FROZEN**

Every automated gate passes, and the manual packaged-UI gate is closed. The
project owner worked through
`acceptance/phase_4g/MANUAL_EXE_RELEASE_CHECKLIST.md` in the shipped executable
on 2026-09-02: 56 of 56 items PASS, including all seven blocking honesty
checks.

    5 285 passed, 1 skipped        (4 494 at the start of the phase)
    41 architecture tests green, unchanged and not weakened
    0 QML warnings across 12 pages, 3 sections, 2 themes, plus Engine Design
    2 320 published values compared: 2 316 PASS, 4 explained REVIEW, 0 pending
    593 cross-module identity tests
    51 of 51 source ↔ frozen-resource values identical
    56 of 56 manual packaged-UI checks PASS, 7 of 7 blocking
    1 API defect found and fixed

---

## Baseline

    4 494 passed, 1 skipped
    41 architecture tests green
    all eight analysis pages plus Engine Design open with 0 QML warnings

---

## 1. What this phase added, and what it did not

Phase 4G wrote no new physics. It wrote tests, contracts and documents, and it
fixed one genuine API defect. The one production change to `rocketforge/` is
listed in section 3.

**Files created**

    tests/physics/compressible/test_cross_module_consistency.py   593 tests
    tests/contracts/compressible_api_v1.json                      the contract
    tests/contracts/test_compressible_api_v1.py                    84 tests
    tests/contracts/test_subsystem_guarantees.py                   64 tests
    tests/contracts/test_reference_engine_selftest.py              22 tests
    tests/contracts/test_examples_run.py                           28 tests
    examples/compressible/*.py                                      9 examples
    docs/engineering/COMPRESSIBLE_FLOW_API_V1.md
    docs/engineering/COMPRESSIBLE_FLOW_THEORY_MAP.md
    docs/engineering/COMPRESSIBLE_REFERENCE_INDEX.md
    docs/engineering/COMPRESSIBLE_VALIDATION_MATRIX.md
    docs/engineering/COMPRESSIBLE_NUMERICAL_LIMITS.md
    docs/engineering/COMPRESSIBLE_PERFORMANCE_BASELINE.md
    docs/engineering/COMPRESSIBLE_FLOW_V1_RELEASE.md
    acceptance/phase_4g/ACCEPTANCE_MANIFEST.md
    acceptance/phase_4g/MANUAL_EXE_RELEASE_CHECKLIST.md
    acceptance/phase_4g/  (13 screenshots)

**Files modified**

    rocketforge/physics/compressible/__init__.py   the nozzle namespace defect

Nothing else under `rocketforge/` changed. No equation was touched.

---

## 2. The audit, and what it found

Nine mechanical audits ran over the subsystem. Eight found nothing, which is
the point of running them; the ninth found a real defect.

| Audit | Result |
| --- | --- |
| SciPy / pandas / numba in production | 0 |
| Qt below the application layer | 0 (one docstring mention) |
| `_deg` names below application | 0 (two occurrences, both prose *forbidding* it) |
| `TODO` / `FIXME` / `HACK` in compressible code | 0 |
| debug output in production | 0 (one `stderr` message in the bootstrap) |
| mutable module-level state | 0 |
| silent physics clamping | 0 — three `clip`/`min` uses, all bracket seeds or post-validation tidying |
| duplicate Mach-angle implementation | 0 — `prandtl_meyer.mach_angle is isentropic.mach_angle` |
| **package namespace** | **defect: see section 3** |

---

## 3. The defect: Phase 4F's nozzle was unreachable

`rocketforge/physics/compressible/__init__.py` had not been updated when the
nozzle arrived. The consequence:

```python
>>> from rocketforge.physics.compressible import nozzle
ImportError
```

Everything worked *inside* the project, because the application layer imports
the private module path directly. But a future engineering module — the exact
consumer this freeze exists to serve — would have had to write
`from rocketforge.physics.compressible.nozzle import solve`, which section 118
of the task specification forbids.

Eleven symbols were unreachable: the `nozzle` and `geometry` submodules,
`AreaDistribution`, `NozzleRegime`, `NozzleSolution`, `NozzleOperating`,
`CriticalPressureRatios`, `ShockLocation`, `NozzleRegimeResult`, `FlowState`
and `StagnationState`.

**Fix:** exported them. The package now exports 36 names, and a contract test
asserts that every submodule is both importable from the package and listed in
`__all__`, so this cannot recur silently.

This is the whole justification for the phase: five phases of green tests did
not reveal it, because nothing inside the project imported the way an outside
consumer would.

---

## 4. Naming, units, angles and ratios

**Ratio orientation** is unambiguous throughout. The convention is mechanical
and documented in `COMPRESSIBLE_FLOW_API_V1.md` §3.2: a state relation's
`pressure_ratio` is static over stagnation, a jump record's is downstream over
upstream, `*_star` is over the sonic reference, and a `_12` suffix means outlet
over inlet explicitly. The Isentropic page publishes *both* orientations as
separately named rows (`T_over_T0` and `T0_over_T`), which is the right way to
serve a textbook convention without ambiguity.

**Static / stagnation / total**: the codebase says *stagnation* in every field
name and treats *total* as prose synonym. There is no `total_*` field anywhere.

**The star** means three different states in three families, and that is now
documented in one table rather than left to be inferred. Two exact coincidences
between Fanno and isentropic are asserted; three deliberate non-coincidences are
asserted too, so a later tidy-up cannot merge the families.

**Angles** are radians below `application`, enforced by the architecture suite.
**Units** are SI throughout, with no unit library and no implicit conversion.

**One inconsistency found, recorded rather than changed.** The application-layer
readout accessors differ between pages: `resultValue(key)` on the Phase 4B-4D
controllers, `rawValue(key)` on 4E-4F, and readout keys differ too — Normal
Shock publishes `p02_over_p01` where Oblique Shock publishes
`stagnation_pressure_ratio` for the same physical quantity. Both are displayed
with explicit labels, so nothing is misleading to a user. This is the
*application* layer, not the frozen physics contract, and renaming a QML-facing
slot is not a Phase 4G change. It is a Phase 5 cleanup candidate.

---

## 5. Branch semantics

Four inverses have two physical roots; all four take a mandatory branch, and a
contract test asserts none acquires a default:

    isentropic.mach_from_area_ratio(ratio, gas, branch)
    mass_flow.mach_from_mass_flow_ratio(ratio, gas, branch)
    fanno.mach_from_friction_parameter(value, gas, branch)
    rayleigh.mach_from_stagnation_temperature_ratio(ratio, gas, branch)

`oblique_shock.solve` takes a `ShockBranch`. `BOTH` in either enum is a
*request* that selects a paired entry point and never appears in a result.

Rayleigh deliberately offers no `T/T*` inverse: the relation is not monotone on
the subsonic branch, so a branch flag could not separate its roots. Not offering
an inversion is better than offering an ambiguous one.

---

## 6. Cross-module validation

The phase's central deliverable: 593 tests asking whether the ten modules agree
with *each other*, over four gammas and one shared Mach grid.

| Identity | Result |
| --- | --- |
| Isentropic ratios satisfy the ideal gas law | PASS |
| Starred ratios are the stagnation ratios referred to sonic | PASS |
| Area-Mach round trip, both branches | PASS |
| The two area-Mach roots stay apart | PASS |
| `mdot/mdot_choked = MFP/Γ = A*/A` | PASS |
| `choked_mass_flow = mass_flow(M=1)` | PASS |
| Mass-flow inverse inherits the area-Mach branch | PASS |
| `T2/T1 = (p2/p1)/(ρ2/ρ1)` across a shock | PASS |
| `p02/p01` rebuilt from the isentropic ratios | PASS |
| `A2*/A1* = p01/p02` | PASS |
| The two shock states share one Fanno line | PASS |
| The two shock states share one Rayleigh line | PASS |
| Fanno's two coincidences with isentropic, and three non-coincidences | PASS |
| An expansion's ratios are the isentropic ratios | PASS |
| One Mach-angle implementation, shared by identity | PASS |
| Oblique = normal shock at `M1 sin β` | PASS |
| β = 90° reduces oblique to normal exactly | PASS |
| β → μ gives no jump | PASS |
| Weak root is always shallower, with less p₀ loss | PASS |
| Darcy ↔ Fanning describe one duct | PASS |
| The remaining Fanno length lands exactly on M = 1 | PASS |
| Available Rayleigh heat lands exactly on M = 1 | PASS |
| Rayleigh's two maxima at 1/√γ and 1 | PASS |
| Every nozzle station satisfies its own area relation | PASS |
| Nozzle mass flow is the mass-flow module | PASS |
| Nozzle T₀ constant across the shock | PASS |
| Nozzle p₀ loses exactly once, at the shock | PASS |
| The nozzle shock is `normal_shock.solve` | PASS |
| The three criticals are isentropic + shock relations | PASS |
| Over/ideal/under share one internal solution | PASS |
| The regime does not depend on station count | PASS |
| **Every module agrees about M = 1** | PASS |

Four failures during development were all wrong assumptions in the *test* about
signatures — `expand()` returns a `Solution`, `duct_parameter_from_geometry`
takes the Fanning factor — plus two conditioning tolerances that were too tight
and are now documented. No production code was changed to make a test pass.

---

## 7. API contract

`tests/contracts/compressible_api_v1.json` records the deliberate public
surface: 36 package exports, 89 function signatures, 34 result records with
their field order, 5 enums with their values. 23.4 kB, human-reviewable, with
the default `ToleranceSet` elided to a constant name so an unrelated tolerance
addition does not churn every diff.

84 tests enforce it, and they check more than equality: no private name is
exported, every public record is frozen, no ambiguous inverse has a default
branch, no relation has a default gas.

---

## 8. Subsystem guarantees

64 further tests cover what a consumer will assume without checking:

* **Qt isolation** — all thirteen representative calls in a subprocess with
  PySide6 made unimportable, `PySide6 not in sys.modules` asserted, and the
  results compared against the ordinary environment.
* **Serialization** — eight record types plus a full nozzle solution round-trip
  through JSON, including success, warning and no-solution payloads. No QObject
  leakage, no `object at 0x...` in any payload.
* **Immutability** — every public dataclass asserted frozen.
* **No global state** — the subsystem walked for mutable module attributes.
* **Non-finite input** — NaN, +inf and -inf into ten entry points: each either
  raises a domain error or returns an explicit no-solution. Never a NaN answer.
* **Shape** — eight forward relations: scalar in, scalar out; array in, array
  out with dtype and shape preserved, including 2-D.
* **The cache** — Phase 4F's memoised nozzle thresholds: keyed on everything
  that changes the answer, cold and warm caches asserted identical, and the
  cached record immutable.

---

## 9. Reference closure

**2 320 published values, 2 316 PASS, 4 REVIEW, 0 pending.** Full index in
`COMPRESSIBLE_REFERENCE_INDEX.md`.

The comparison engine is now self-tested. Corrupting one published column by 1%
in an in-memory copy must produce REVIEW; perturbing by 1e-9 must not. A
SHA-256 digest check asserts the shipped files were never touched by those
tests.

The first version of that self-test was **vacuous**: its mutation helper wrote
`row.values`, which on a dict is the bound method, so it silently changed
nothing and the "detection" test passed against unmodified data. It is fixed,
and it now asserts that the mutation actually altered rows before comparing —
which is precisely the failure mode section 60 of the task exists to prevent.

The four REVIEW cases are one suspected misprint (Appendix A, M = 16, `T0/T`
printed 52.29 where the exactly-linear relation gives 52.20) and three
last-digit rounding edges. All are pinned, evidenced and preserved as printed.

---

## 10. Numerical limits

`COMPRESSIBLE_NUMERICAL_LIMITS.md` states what float64 can resolve here and
what it cannot: near-sonic inversion to about 1e-6 rather than 1e-15, the
oblique roots merging within 1% of θ_max, nozzle thresholds separated by no
less than `pressure_tol` times their value, and the measured near-throat shock
behaviour. It also states what is *promised*: no NaN escapes, no silent
clamping, and determinism independent of batch size or cache state.

No arbitrary-precision library was introduced into production to hide any of
it. `Decimal`, `Fraction`, `mpmath` and SciPy remain test-and-oracle tools.

---

## 11. Examples

Nine Qt-free scripts under `examples/compressible/`, one per module plus an
end-to-end script that takes a gas through isentropic, mass-flow, shock and
nozzle calculations. Each is executed by the test suite in a subprocess with
PySide6 blocked, and each is checked for importing only from the package root.

A reproducibility finding came out of writing them: run as a bare path
(`python examples/compressible/fanno_example.py`) they fail, because the
project is not installed as a package and the script's own directory goes on
`sys.path` instead of the root. They are therefore documented and tested as
`python -m examples.compressible.fanno_example` from the project root, which
works with no boilerplate in the files.

---

## 12. Performance

Full table in `COMPRESSIBLE_PERFORMANCE_BASELINE.md`. Highlights, measured:

    isentropic, all four ratios, 100 000 samples      4.61 ms
    normal shock, all ratios, 100 000                 5.96 ms
    one area-Mach inverse                             0.104 ms
    one oblique solve                                 0.448 ms
    one nozzle internal-shock solve                   3.01 ms
    one nozzle classification                         0.013 ms
    100 000 nozzle classifications                     867 ms
    nozzle distribution, 1 000 stations                123 ms

No timing assertion is written as a unit test: those are brittle across
machines. The baseline exists so an order-of-magnitude regression is visible.

---

## 13. UI acceptance

Every page opens, in both themes, with **zero QML warnings**.

**Value parity**: for all eight modules, what the controller publishes was
compared against a direct backend call. All agree.

**Stale state**: eight transitions exercised — isentropic both→single, the
mass-flow dimensional gate, a printed shock row → an unprinted Mach number,
Prandtl-Meyer inverse→direct, oblique attached→detached→attached, Fanno
valid→choked, Rayleigh valid→choked, and all five nozzle regime transitions.
Nothing stale survived any of them.

Nine flags raised during that sweep were all **wrong assumptions in the sweep**,
not defects: wrong readout keys, a `theta` property that does not exist (so
`setProperty` created a dynamic one that drove nothing), a `dimensional` toggle
that is actually a read-only gate, and a sequencing error where the shock page
was left on an unprinted Mach number. Each was checked against the page's actual
behaviour before being dismissed; the oblique page, for instance, correctly
reports "Near detachment" at θ = 34.0°, flips to Detached with **zero available
rows** at 34.1°, and recovers cleanly.

The one genuine per-Mach honesty question — what a page shows when the Mach
number has no printed reference row — is already handled: the page says
"This M₁ is not one of them, and no value is interpolated."

**Engine Design** opens unchanged: canvas, palette and inspector intact,
performance rows still showing em dashes with the note that they await a solver.
No fundamental nozzle result is wired into it, as required.

---

## 14. Packaging

    build          clean rebuild, exit 0
    path           C:\\Users\\erayh\\Documents\\Python\\rocket\\dist\\RocketForge\\RocketForge.exe
    size           191.9 MB, 2 072 files
    numpy          present
    forbidden      scipy, pandas, numba, sympy, mpmath, tests, PDFs — all absent
    references     all 6 datasets present
    QML            39 pages
    launch         starts and stays alive

**Source ↔ frozen parity: 51 of 51 values identical**, covering every module
and every nozzle regime, with `sys._MEIPASS` pointed at the packaged bundle.

**Bundle provenance:** 47 `rocketforge` modules compiled into `PYZ-00.pyz`, 13
of them `physics.compressible`, every one traced to a file in this project tree.

**Limitation, stated plainly.** PyInstaller compiles Python modules into the PYZ
archive, so the packaged *code* cannot be imported from `_internal` and re-run
in isolation — only the data directory survives on disk. What was verified is
that no result depends on which copy of the reference data is loaded, and that
the code in the bundle is the code that was tested. Earlier phases' claims of
"frozen path verification" were of this same kind, and this report names it.

---

## 15. The manual gate, and why it mattered

Section 101 of the task is explicit, and it is right: a final UI freeze may not
rest on offscreen renders, a bundled-backend matrix and a landing-page
screenshot. A human has to open the shipped application.

Driving a packaged Qt process requires synthetic desktop input, which the
harness refuses to send — a refusal earlier phases got right and this phase did
not undermine. So the gate was prepared as a checklist rather than faked as
automation: 56 items across nine sections, seven of them blocking.

**The gate is now closed.** The project owner worked through it in
`dist\RocketForge\RocketForge.exe` on 2026-09-02 and reported 56 of 56 PASS,
with the seven blocking honesty checks confirmed individually:

| # | Blocking check | Result |
| --- | --- | :-: |
| 4.4 | a turn beyond nu_max is refused with an explanation | PASS |
| 5.4 | a detached oblique shock leaves no attached numbers on screen | PASS |
| 6.3 | a choked Fanno duct shows no outlet Mach | PASS |
| 7.3 | Rayleigh heat past the limit shows no outlet Mach | PASS |
| 8.6 | an overexpanded nozzle has no shock card | PASS |
| 8.12 | the shock marker leaves the charts with the shock | PASS |
| 9.5 | no error dialog, blank page or visible QML warning | PASS |

Those seven are the ones that matter, because each asks the same question: can a
stale or invented number reach a user? In the shipped build, none can.

**Build identity.** The executable that was checked was built at
2026-09-02 16:04:36, which postdates every bundled source file — the newest is
`rocketforge/physics/compressible/__init__.py` at 15:21:49, carrying this
phase's namespace fix. The build exercised by hand is the same clean Phase 4G
build the automated gates ran against, and it was not rebuilt afterwards.

**Provenance.** These results were performed and reported by the project owner
and transcribed into the acceptance record. That is the nature of a manual gate,
and it is stated rather than blurred into the automated evidence above.

---

## 16. Physics files modified

**None.** No equation, tolerance or solver was changed. The single production
edit was the package `__init__.py` namespace fix in section 3.

## 17. API changes

One, additive: eleven previously unreachable symbols are now exported. No
signature, field, enum value or behaviour changed, so nothing that already
worked can break.

## 18. Remaining limitations

* Application-layer readout accessors and keys are inconsistent between pages
  (section 4). Cosmetic, outside the frozen contract, a Phase 5 candidate.
* Packaged *code* cannot be executed in isolation for parity testing
  (section 14).
* Everything in `COMPRESSIBLE_NUMERICAL_LIMITS.md` and the v1 non-goals in
  `COMPRESSIBLE_FLOW_V1_RELEASE.md`.

## 19. What the freeze means from here

`rocketforge.physics.compressible` is frozen at the public surface described in
`COMPRESSIBLE_FLOW_API_V1.md`, as of 2026-09-02, at manifest digest
`8f0d1cf5685e0c52b6083b9a5f77196b25a1f987b85acadb4d7094ba385a3502`.

Future modules **consume** this subsystem. They do not reopen its scientific
foundations, and they do not edit its public surface casually. A breaking change
now requires a version bump or a recorded erratum, made in the same commit that
updates `tests/contracts/compressible_api_v1.json`, so it appears in review
rather than in a downstream failure.

Internal implementation may still change — a faster inverse, a different
bracket, another cache — provided the contract tests stay green.

## 20. Recommended next program

    Phase 5 — Thermochemistry / combustion foundations and propellant /
    chamber state providers: the layer that supplies a ChamberGas to this
    subsystem rather than modifying it.

Not implemented.
