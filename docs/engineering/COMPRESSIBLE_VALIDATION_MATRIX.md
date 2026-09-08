# Compressible Flow — Validation Matrix

What kind of evidence backs each public capability. The point of the matrix is
the *shape* of the coverage: no important capability rests on one kind of test
alone.

Legend: **U** unit · **P** property/sweep · **L** limit/boundary · **R**
round-trip · **X** cross-module · **REF** published reference · **UI** exercised
on a page · **PKG** verified from the packaged bundle.

---

## Capabilities

| Capability | U | P | L | R | X | REF | UI | PKG |
| --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| PerfectGas: gamma, R, cp, cv | Y | Y | Y | - | Y | - | Y | Y |
| Speed of sound | Y | Y | Y | - | Y | - | Y | Y |
| Isentropic T/T0, p/p0, rho/rho0 | Y | Y | Y | Y | Y | Y | Y | Y |
| Starred ratios T/T*, p/p*, rho/rho* | Y | Y | Y | - | Y | - | Y | Y |
| Mach angle | Y | Y | Y | - | Y | Y | Y | Y |
| Closed-form isentropic inverses | Y | Y | Y | Y | Y | - | Y | Y |
| Area-Mach forward A/A* | Y | Y | Y | Y | Y | Y | Y | Y |
| Area-Mach inverse, both branches | Y | Y | Y | Y | Y | Y | Y | Y |
| Mass-flow parameter, Gamma | Y | Y | Y | - | Y | - | Y | Y |
| Dimensional mass flow, mass flux | Y | Y | Y | - | Y | - | Y | Y |
| Choked mass flow, critical ratios | Y | Y | Y | - | Y | - | Y | Y |
| Mass-flow inverse, both branches | Y | Y | Y | Y | Y | - | Y | Y |
| Normal-shock jump relations | Y | Y | Y | - | Y | Y | Y | Y |
| Pitot ratio | Y | Y | Y | - | Y | Y | Y | Y |
| Normal-shock inverses | Y | Y | Y | Y | Y | Y | Y | Y |
| Prandtl-Meyer nu, nu_max | Y | Y | Y | - | Y | Y | Y | Y |
| Prandtl-Meyer inverse | Y | Y | Y | Y | Y | Y | Y | Y |
| Expansion and compression turns | Y | Y | Y | Y | Y | - | Y | Y |
| theta-beta-M relation | Y | Y | Y | - | Y | - | Y | Y |
| theta_max, detachment | Y | Y | Y | - | Y | - | Y | Y |
| Oblique weak and strong roots | Y | Y | Y | Y | Y | Y | Y | Y |
| theta-beta-M curve | Y | Y | Y | - | Y | - | Y | Y |
| Fanno starred ratios | Y | Y | Y | - | Y | Y | Y | Y |
| Fanno 4 f_F L*/D and its limit | Y | Y | Y | - | Y | Y | Y | Y |
| Fanno inverses, both branches | Y | Y | Y | Y | Y | Y | Y | Y |
| Fanno duct segment, choking | Y | Y | Y | - | Y | Y | Y | Y |
| Darcy / Fanning equivalence | Y | Y | - | Y | Y | Y | Y | Y |
| Rayleigh starred ratios | Y | Y | Y | - | Y | Y | Y | Y |
| Rayleigh critical points (both) | Y | Y | Y | - | Y | Y | Y | Y |
| Rayleigh T0 inverse, both branches | Y | Y | Y | Y | Y | Y | Y | Y |
| Rayleigh heat transition, choking | Y | Y | Y | - | Y | Y | Y | Y |
| AreaDistribution validation | Y | Y | Y | - | - | - | Y | Y |
| Monotone cubic interpolation | Y | Y | Y | Y | - | - | Y | Y |
| Nozzle three criticals | Y | Y | Y | - | Y | Y | Y | Y |
| Nozzle regime classification (7) | Y | Y | Y | - | Y | Y | Y | Y |
| Internal shock location | Y | Y | Y | Y | Y | Y | Y | Y |
| Nozzle distributed solution | Y | Y | Y | - | Y | Y | Y | Y |
| Shock discontinuity representation | Y | Y | Y | - | Y | - | Y | Y |
| Nozzle mass / energy / p0 conservation | Y | Y | Y | - | Y | - | Y | Y |

Blank cells are deliberate, not gaps: geometry has no published table to
compare against, and `PerfectGas` has no round trip to make.

## Cross-cutting guarantees

| Guarantee | How it is checked |
| --- | --- |
| Public API surface | contract snapshot + 84 tests in `tests/contracts/` |
| Branch never guessed | a test asserts no ambiguous inverse has a default |
| No hidden gas default | a test walks every public function's `gas` parameter |
| Immutable results | every public dataclass asserted frozen |
| JSON serializable | success, warning and no-solution payloads round-tripped |
| Qt isolation | all thirteen representative calls in a PySide6-blocked subprocess |
| No global state | the subsystem walked for mutable module attributes |
| Non-finite input | NaN / +inf / -inf into ten entry points |
| Scalar/array shape | eight forward relations, scalar, 1-D and 2-D |
| Reference engine works | mutation self-test: 1% corruption must be detected |
| Reference data untouched | SHA-256 digests before and after the mutation tests |
| Examples do not rot | nine examples executed with Qt blocked |
| Determinism | the same call twice, and the suite run twice |
| Cache correctness | cold cache vs warm cache asserted identical |

## Test counts

    tests/physics        4 366
    tests/application      447
    tests/core             233   (1 skipped: the SciPy oracle)
    tests/contracts        198
    test_architecture.py    41
    ----------------------------
    total                5 285 passed, 1 skipped

## The one skip

`tests/core/test_roots_cross_validation.py` skips when SciPy is absent. SciPy
is a development-only cross-validation oracle listed in `requirements-dev.txt`;
it is deliberately not a runtime dependency, and the skip hides no production
functionality. It is the only skip in the suite.
