# Phase 4A — Core Numerical Foundation

Implementation note for the first production code in the RocketForge
engineering backend: the package skeleton, the bracketed root solver, and the
architecture enforcement test.

Date: 2026-08-30

---

# Verdict

**PASS**

---

## Phase 3 documents consumed

All eight, read before any code was written:

* `docs/engineering/01_engineering_architecture.md` — layer table and hard
  rules (§2), package layout (§3), the enforcement test (§4), the angle policy
  (§8), determinism (§9), ADR-09 (no SciPy at runtime).
* `docs/engineering/02_data_model_and_api_contracts.md` — the `Convergence`
  record (§2.3), the error taxonomy and the raise-versus-report policy (§5),
  immutability (ADR-08, §7).
* `docs/engineering/03_compressible_flow_specification.md` — the inverse
  problems this solver will serve; no physics implemented.
* `docs/engineering/04_numerical_methods_and_domain_policy.md` — the method
  choice and `brent` signature (§2), the per-inverse brackets (§3), near-sonic
  conditioning (§4), the tolerance set (§5), scalar/array policy (§9),
  performance budgets (§10).
* `docs/engineering/05_verification_and_validation_plan.md` — the test tree
  (§2), convergence tests (§13), the coverage philosophy (§15).
* `docs/engineering/06_future_module_dependency_map.md` — forbidden
  dependencies (§3).
* `docs/engineering/07_ui_integration_contracts.md` — confirmed no UI work is
  in scope.
* `docs/engineering/PHASE_3_SUMMARY.md` — the recommended first task, which is
  what this phase implements.

No contradictions between documents were found, so no `PHASE_3_SPEC_CONFLICT`
was raised. Points where Phase 3 was *silent* rather than contradictory are
recorded as decisions below.

---

## Files created

**Backend package**

    rocketforge/__init__.py                  package docstring, __version__; no eager imports
    rocketforge/core/__init__.py             layer 0 contract
    rocketforge/core/errors.py               exception hierarchy (5 classes)
    rocketforge/core/tolerances.py           ToleranceSet (Phase 4A subset), DEFAULT_TOLERANCES
    rocketforge/core/numerics/__init__.py     re-exports brent, RootReport, METHOD_BRENT
    rocketforge/core/numerics/roots.py       the Brent-Dekker solver and RootReport
    rocketforge/physics/__init__.py          layer contract, empty
    rocketforge/engineering/__init__.py      layer contract, empty
    rocketforge/engine/__init__.py           layer contract, empty
    rocketforge/providers/__init__.py        layer contract, empty
    rocketforge/application/__init__.py      layer contract, empty

**Tests**

    tests/test_architecture.py               41 tests
    tests/core/test_roots.py                 203 tests
    tests/core/test_tolerances.py            20 tests
    tests/core/test_roots_cross_validation.py 4 tests (skipped without SciPy)

**Other**

    requirements-dev.txt                     pytest; SciPy marked oracle-only
    docs/engineering/implementation/PHASE_4A_ROOT_FOUNDATION.md   this file

The five empty layer packages exist so the architecture test has real layers to
check and so the intended structure is visible. They contain a docstring
stating each layer's import rule and nothing else — no placeholder functions,
no stub APIs.

---

## Files modified

**None.** No existing file in the project was edited: not `ui/`, not `main.py`,
not `packaging/`, not `build_exe.bat`, `run.bat`, `requirements.txt` or
`README.md`. Verified by modification time after the phase.

`requirements.txt` was deliberately left alone. Phase 3 selected NumPy as a
runtime dependency for future vectorised physics, but nothing in Phase 4A
imports it — the scalar solver uses `math`, per the brief — so adding it now
would put an unused binary wheel into the frozen build. It joins
`requirements.txt` in the phase that first imports it.

`pytest` was installed into the existing `.venv` as a development tool. It is
pure Python, is not imported by any shipped module, and does not affect the
PyInstaller bundle.

---

## Public API

```python
from rocketforge.core.numerics.roots import brent, RootReport, METHOD_BRENT

def brent(
    f: Callable[[float], float],
    a: float,
    b: float,
    *,
    xtol: float,
    rtol: float,
    max_iter: int,
) -> tuple[float, RootReport]: ...
```

Exactly the signature specified in `04` §2. Tolerances are keyword-only and
have **no defaults**: every call site states the accuracy it needs, which is
what keeps a physics module's tolerance choice visible in review rather than
inherited from a global.

Internal helpers (`_interpolate`, `_acceptable`, `_window`, `_straddles`,
`_same_sign`, `_ordered`, `_finite_argument`, `_report`) are private and tested
only through the public function.

---

## RootReport

```python
@dataclass(frozen=True, slots=True)
class RootReport:
    converged: bool
    iterations: int
    residual: float                      # |f(root)|
    tolerance: float                     # window actually applied at the root
    bracket: tuple[float, float]         # final maintained interval, ordered
    method: str                          # "brent"
    function_calls: int
    initial_bracket: tuple[float, float]
```

The first six fields are the physics layer's `Convergence` record (`02` §2.3)
in the same order, so the mapping is a field-for-field copy. `function_calls`
and `initial_bracket` are the two additions the Phase 4A brief permits; both
are exact and testable, and neither costs an extra evaluation of `f`.

Frozen and built only from floats, ints, strings and tuples, so it can be
compared, stored, serialised to JSON, or handed to another thread.

---

## Error behaviour

```
RocketForgeError
├── InputError                   non-finite endpoint or tolerance, a >= b,
│                                xtol <= 0, rtol < 0, max_iter < 1
└── NumericalError
    ├── BracketError             f(a), f(b) share a sign and neither is a root
    └── NonFiniteEvaluationError f returned NaN or an infinity
```

`TypeError` is raised for a non-callable `f`, a non-numeric argument, or
tolerances passed positionally — those are Python-level misuse, not domain
questions, and Phase 3 (`05` §12) already uses native errors for that class of
mistake.

Running out of iterations is **not** an error: the solver returns its best
estimate with `converged=False`, per `04` §2.

---

## Numerical algorithm

Brent-Dekker: inverse quadratic interpolation where three distinct abscissae
are available, the secant rule where only two are, and bisection whenever
interpolation cannot be shown to be safe. Written from the published
description of the method; no SciPy source was consulted or copied, and the
architecture test forbids SciPy anywhere under `rocketforge/`.

Invariants maintained every pass:

* `f(b)` and `f(c)` have opposite signs, so `[b, c]` brackets a root;
* `|f(b)| <= |f(c)|`, so `b` is the better of the two estimates.

An interpolated step is accepted only if it satisfies both classical
conditions: it stays within `1.5 * half_width - 0.5 * tol` of `b` — three
quarters of the way across the bracket at most, so the sign change can never be
stepped over — and it is no larger than half the step before last, which stops
interpolation from stalling. Failing either, the step is a bisection.

Division safety: every interpolation denominator is checked, and any
non-finite intermediate returns `None` from `_interpolate`, which the caller
turns into a bisection. No NaN can enter the iteration.

Sign tests compare signs directly rather than forming the product `fa * fb`,
which can overflow or underflow when the two magnitudes are extreme and would
then answer the wrong question.

---

## Termination policy

Iteration stops when the maintained bracket half-width is within
`0.5 * (xtol + rtol * |b|)`, or when `f(b)` is exactly zero. On convergence the
true root lies within `report.tolerance` of the returned value.

The applied window is never narrower than `4 * eps * |root|`. A request tighter
than the floating-point grid can resolve would otherwise exhaust the budget and
report a failure that is really an impossible demand; `tolerance` reports what
was actually applied, so the number stays truthful.

Endpoint roots short-circuit before the sign test: `f(a) == 0` returns `a` after
a single evaluation, and `f(b) == 0` returns `b` after two. Signed zero needs no
special case since `-0.0 == 0.0`.

---

## Decisions and additions

Phase 3 was silent on each of these. None contradicts it; all are recorded here
rather than resolved silently, and none required editing a Phase 3 document.

**DECISION-4A-01 — the residual is reported, not used as a stopping rule.**
`04` §5 defines `residual_tol` as "|f(x)| accepted as a converged root", and
`05` §13.2 asserts `|f(root)| <= residual_tol` for the physics inverses. Those
are *acceptance* criteria for well-scaled physics residuals; making `|f|` the
termination criterion inside `brent` would be wrong in both directions. On a
flat function such as `(x-1)**3`, `|f| <= 1e-10` is already satisfied at
`|x-1| = 4.6e-4`, so stopping there would return four correct digits while
claiming ten; on a steep function such as `1e8 * (x - 0.3)`, an essentially
exact root still carries a residual far above `1e-10`, so the criterion could
never be met. Termination is therefore on the root, both numbers are reported,
and the caller applies whichever its problem needs. Covered by
`test_small_residual_does_not_imply_an_accurate_root`.

**DECISION-4A-02 — `a < b` is required; the solver does not reorder.**
A reversed bracket almost always means the caller derived it incorrectly, and
silently swapping would hide that. `InputError`, with a message saying so.

**DECISION-4A-03 — "best iterate" means the endpoint with the smaller `|f|`.**
Brent maintains `|f(b)| <= |f(c)|`, so `b` is both the smaller-residual
candidate and an endpoint of the reported bracket. Returning an earlier iterate
with a smaller residual was rejected: it could lie outside the final bracket,
making the returned root and the returned interval mutually inconsistent.
Asserted by `test_max_iter_exhaustion_returns_the_better_of_the_two_candidates`.

**DECISION-4A-04 — `if TYPE_CHECKING:` imports count against the layer rules.**
The Phase 4A brief left this to the architecture policy and recommended
counting them. A physics module that needs an engineering type to describe its
own signature has an engineering dependency whether or not the interpreter
follows it.

**DECISION-4A-05 — a two-tier halving safeguard.**
Discovered during testing rather than anticipated: on a root of multiplicity
greater than one, interpolation converges on the root from one side while the
far endpoint never moves. The *estimate* improves but the *bracket* does not,
and since termination is a statement about the bracket, the solve runs out of
budget with a residual of 1e-23 and `converged=False`. Textbook Brent behaves
the same way — multiplicity greater than one degrades it from superlinear to
linear.

Tier one requires the interval to halve every second pass; tier two, armed once
tier one has fired twice, requires it every pass. Measured over the analytic
cases, tier one never fires on a simple root, so smooth problems are unaffected.
Both tiers only ever *force a bisection*, so neither can affect correctness —
only cost. Measured on fourteen cases:

| variant | smooth cases | `(x-r)**3` | `(x-r)**5` | `(x-r)**7` |
| --- | --- | --- | --- | --- |
| no safeguard | 1–33 iterations | did not converge | did not converge | did not converge |
| halve every 2 passes | 1–33 (unchanged) | 85–88 | did not converge | did not converge |
| halve every pass | 1–43 (up to 2.6x worse) | 55–62 | 63 | 65 |
| **two-tier (chosen)** | **1–33 (unchanged)** | **64–66** | **70** | **70** |

**DECISION-4A-06 — the tolerance window has a machine-precision floor.**
See the termination policy above.

**DECISION-4A-07 — NumPy is not added to `requirements.txt` yet.**
See "Files modified".

**ADDITION-4A-01 — `NonFiniteEvaluationError`.**
`02` §5 lists `BracketError` and `ConvergenceError` under `NumericalError` but
does not cover a function returning NaN or an infinity. The Phase 4A brief
names this class as a likely need, so it is added under `NumericalError` rather
than overloading `BracketError`, whose meaning is specifically "no sign change".
`ConvergenceError` is not implemented in this phase because nothing raises it
yet — it belongs with the physics layer's `*_strict()` variants.

---

## Determinism

Bitwise identical across repeated runs, asserted with `float.hex()` on the root
and equality on the whole report, over all 13 analytic cases and five repeats
each. Interleaving different problems does not perturb any of them
(`test_no_global_state_between_solves`), and three consecutive full-suite runs
produced identical results.

There is no randomness, no module-level mutable state, no caching, and no
time-dependence anywhere in the solver.

---

## Tests

    project .venv    264 passed, 1 skipped   (cross-validation skips: no SciPy)
    oracle env       268 passed, 0 skipped   (SciPy 1.18.1 present)

Per file: architecture 41, root solver 203, tolerances 20, cross-validation 4.

Required matrix from the Phase 4A brief §93, all covered and passing: linear,
polynomial and `cos(x) - x` roots; flat-derivative odd roots; roots at the left
and right endpoints; no sign change; non-finite endpoints and non-finite
function values; invalid tolerances and `max_iter`; narrow brackets; large and
small root magnitudes; iteration exhaustion; converged and non-converged report
correctness; residual correctness; bracket consistency; repeated-run
determinism; absence of global state.

The optional high-value cases of §94 are also covered: exponentially scaled
functions, asymmetric brackets, a root adjacent to an endpoint, magnitudes
spanning twenty decades, and a kinked function where interpolation is rejected
repeatedly and bisection has to carry the solve.

Two defects were found by these tests during development, both in the tests'
own inputs rather than the solver, and both fixed: a level-4 relative import in
the architecture fixtures that Python itself would reject, and a
cross-validation function written as `exp(k*d) - 1`, whose cancellation near the
root leaves it unable to locate its own zero (now `expm1`). The architecture
checker's self-tests also caught two real parser holes before the checker was
trusted — see below.

---

## Cross-validation

**Performed.** SciPy 1.18.1, in an isolated environment outside the project so
the application's own `.venv` is unchanged.

    distinct cases        1421
    families              8 (linear, cubic+linear, exponential offset, arctangent,
                             hyperbolic tangent, trigonometric, logarithmic, rational)
    grid                  14 roots x 5 parameters x 3 bracket shapes, deterministic
    mismatches            0
    bit-identical roots   1235 / 1421
    max |ours - SciPy|    4.09e-12  (root 2048, where the tolerance window is 2.15e-11)
    function calls        ours 9982, SciPy 8268  (ratio 1.207)
    max iterations        23

No disagreement on convergence, on the root, or against the analytic root of
each generated case. The 21% higher evaluation count is the price of the
halving safeguard and is well inside the 0.5–2.0 band the test asserts.

Cases are generated from deterministic grids — no randomness, seeded or
otherwise — and are deduplicated by the problem they actually pose, so a
clamped bracket or a saturated parameter cannot inflate the count. Every case
has a simple analytic root inside a sign-changing bracket, so "which root" is
never ambiguous.

There is no fallback onto SciPy anywhere, and `tests/test_architecture.py` fails
the build if any module under `rocketforge/` imports it.

---

## Architecture test

**PASS**, 41 tests.

Enforced, by parsing each module's AST rather than importing it:

| Rule | Status |
| --- | --- |
| `core` may import only `core` | enforced |
| `physics` may import `core` | enforced |
| `engineering` may import `physics`, `core` | enforced |
| `engine` may import `engineering`, `physics`, `core` | enforced |
| `providers` may import `physics`, `core` | enforced |
| `application` may import everything below | enforced |
| Qt only in `application` | enforced |
| CoolProp / RocketCEA / Cantera only in `providers` | enforced |
| SciPy nowhere under `rocketforge/` | enforced |
| no `_deg` names below `application` (angles are radians) | enforced |
| backend never imports `ui` or `main` | enforced |

Failure messages name the importing module, the line, the forbidden target, the
rule that was violated and the section of `01` that states it.

**The checker is tested against itself.** Eight synthetic forbidden edges must
be rejected and six legitimate ones accepted; relative imports of every depth
must resolve; `TYPE_CHECKING` imports must be seen; the standard library and
NumPy must be ignored. Those self-tests found two real holes before the checker
was trusted: `from .. import physics` resolved only to `rocketforge` and so
missed the layer entirely, and a relative import walking past the package root
returned a bare tail that looked like an external package. Both fixed.

Known limitation, documented in the test module: static analysis sees `import`
statements, so a dynamic `importlib` import would not be detected. Nothing in
RocketForge uses one.

---

## Qt isolation

**PASS.** Two independent checks, both run as subprocesses:

* `import rocketforge` loads no Qt, no SciPy, no NumPy, and no `rocketforge`
  submodules — the top-level package stays empty and cheap.
* With a meta path finder making PySide6 unimportable, every backend module
  below `application` is imported via `pkgutil.walk_packages` and the solver is
  exercised. `application` is excluded from that sweep because it is the one
  layer permitted to hold Qt adapters.

---

## Performance sanity

    10,000 solves of cos(x) = t     0.104 s total, 10.4 us per solve
                                    10.2 function evaluations per solve
    single sqrt(2) solve            8.3 us

Against the `04` §10 budget of under 100 µs for a bracketed inverse, with an
order of magnitude to spare. The 10.2 evaluations per solve matches the "6–12"
Phase 3 expected. No optimisation was attempted and none is warranted.

---

## Existing UI smoke test

**PASS.** `python main.py` launches and stays up, before and after the backend
was added. No QML file, theme, component, workspace or engine model was touched.

The Windows executable was **not** rebuilt. The UI does not consume the backend
yet, `packaging/RocketForge.spec` needed no change, and the accepted build in
`dist/RocketForge/` remains the accepted UI build.

---

## Physics implemented

**None.** No gas model, no relation, no constant with physical meaning. The
only occurrences of physical vocabulary anywhere in `rocketforge/` are in
docstrings that explain which future inverse each layer will serve.

---

## Ready for Phase 4B

**YES.**

The recommended next task, from `PHASE_3_SUMMARY.md` step 3, is
`rocketforge/physics/compressible/gas.py`: the `PerfectGas` model with its
`gamma` and `gas_constant` validation, `cp`/`cv` as computed properties,
`speed_of_sound`, and the domain rules of `03` §2.2 — including the reasoning
behind the hard limit `1.001 <= gamma <= 3.0` and the `EXTRAPOLATED_GAMMA`
advisory band. It needs `InvalidGammaError`, `InvalidGasConstantError` and
`MissingGasConstantError` added to `core/errors.py`, and it is gated by
`05` §16 before anything binds to QML.
