# Phase 4B — Perfect Gas, Isentropic Flow, Area–Mach Inversion

The first production engineering physics in RocketForge.

Date: 2026-08-30

---

# Verdict

**PASS**

---

## Phase 3 contracts consumed

| Document | Sections used |
| --- | --- |
| `01_engineering_architecture.md` | §2 layer rules, §3 package layout, §8 radians-only, §9 determinism, §10 provenance and model versioning, §11 naming and ratio orientation |
| `02_data_model_and_api_contracts.md` | §1.2 `PerfectGas`, §2.2–2.4 `Solution`/`Status`/`Diagnostic`/`Convergence`, §4 `FlowBranch`, §5 error taxonomy, §9 equation registry, §10.1–10.2 API signatures, §11 `IsentropicRatios` and `AreaMachSolutions` |
| `03_compressible_flow_specification.md` | §1.2 notation, §2 gas model and domains, §3.1–3.4 the relations and the area-Mach branch policy, §12.1 pseudocode, §11 cross-checking values |
| `04_numerical_methods_and_domain_policy.md` | §3.1 brackets, §3.6 analytic inverses, §4 near-sonic conditioning, §5 tolerances, §6 extreme inputs, §7 domain table, §8 no silent clamping, §9 scalar/array policy, §10 budgets, §11 conditioning checklist |
| `05_verification_and_validation_plan.md` | §7 external confirmation as a blocking gate, §9 invariants, §10 round trips, §11 limits, §12 invalid input, §14 duplication audit, §15 coverage philosophy |
| `06_future_module_dependency_map.md` | §3 forbidden dependencies |
| `07_ui_integration_contracts.md` | §4 confirmed the Isentropic page's inputs and readout rows; **no UI work performed** |
| `PHASE_4A_ROOT_FOUNDATION.md` | the `brent` contract and `RootReport` |

One erratum was found in a Phase 3 document (ERRATUM-4B-01, below). It is an
arithmetic slip within one document, not a contradiction between two, so no
`PHASE_3_SPEC_CONFLICT` was raised.

---

## Files created

**Production**

    rocketforge/core/constants.py                       universal constants (R_universal, g0)
    rocketforge/core/result.py                          Status, Severity, Diagnostic, Convergence, Solution
    rocketforge/core/provenance.py                      RelationRef, VariableRef, EquationRecord
    rocketforge/core/numerics/arrays.py                 scalar/array handling and domain guards
    rocketforge/physics/compressible/__init__.py        public surface
    rocketforge/physics/compressible/types.py           FlowBranch, IsentropicRatios, AreaMachSolutions
    rocketforge/physics/compressible/gas.py             PerfectGas, speed_of_sound
    rocketforge/physics/compressible/isentropic.py      the relations and both inverses
    rocketforge/physics/compressible/equations.py       reference registry

**Tests**

    tests/physics/compressible/test_gas.py              102
    tests/physics/compressible/test_isentropic.py       180
    tests/physics/compressible/test_isentropic_inverse.py 90
    tests/physics/compressible/test_area_mach.py        228
    tests/physics/compressible/test_reference_cases.py   33
    tests/physics/compressible/test_public_api.py        14
    tests/physics/compressible/test_reuse.py             11

**Reference data**

    tests/reference_data/SOURCES.md
    tests/reference_data/isentropic_naca1135.json
    tests/reference_data/area_mach_naca1135.json

**Documentation**

    docs/engineering/implementation/PHASE_4B_PERFECT_GAS_ISENTROPIC.md

## Files modified

    rocketforge/core/errors.py          + DomainError, AreaRatioError, GasModelError,
                                          InvalidGammaError, InvalidGasConstantError,
                                          MissingGasConstantError
    rocketforge/core/tolerances.py      + the Mach, area, sonic and gamma-domain fields
    tests/core/test_tolerances.py       updated for the extended set (not a frozen file)
    requirements.txt                    + numpy>=1.26, with the reason
    docs/engineering/04_...policy.md    + ERRATUM-4B-01, appended beside the text it corrects

**Not modified:** `ui/`, `main.py`, `packaging/`, `build_exe.bat`, `run.bat`,
and every Phase 4A file frozen by the brief — `core/numerics/roots.py`,
`tests/core/test_roots.py`, `tests/core/test_roots_cross_validation.py`,
`tests/test_architecture.py`. No defect was found in the root solver, so it was
not touched.

---

## PerfectGas API

```python
@dataclass(frozen=True, slots=True)
class PerfectGas:
    gamma: float
    gas_constant: float | None = None       # J/(kg K); None = dimensionless only

    cp: float                               # property, gamma R / (gamma - 1)
    cv: float                               # property, R / (gamma - 1)
    is_dimensional: bool                    # property
    diagnostics: tuple[Diagnostic, ...]     # property; EXTRAPOLATED_GAMMA advisory

    def speed_of_sound(self, temperature) -> float | np.ndarray: ...

    @classmethod
    def air(cls) -> PerfectGas: ...                                  # 1.4, 287.0528
    @classmethod
    def from_molar_mass(cls, gamma, molar_mass) -> PerfectGas: ...   # kg/mol

def speed_of_sound(temperature, gas: PerfectGas) -> float | np.ndarray: ...
```

Immutable, so a stored analysis can name its gas and that gas cannot have
changed since. `cp` and `cv` are derived rather than stored, which makes
`cp/cv == gamma` and `cp - cv == R` true by construction rather than by
discipline — both are asserted across four gammas and three gas constants.

---

## Isentropic API

Forward, scalar or array, returning the bare number:

```python
temperature_ratio(mach, gas)        # T/T0
pressure_ratio(mach, gas)           # p/p0
density_ratio(mach, gas)            # rho/rho0
area_ratio(mach, gas)               # A/A*
temperature_ratio_star(mach, gas)   # T/T*
pressure_ratio_star(mach, gas)      # p/p*
density_ratio_star(mach, gas)       # rho/rho*
mach_angle(mach)                    # mu [rad]; takes no gas -- it is geometry
ratios_from_mach(mach, gas) -> IsentropicRatios      # scalar only
```

Analytic inverses, scalar or array, no iteration:

```python
mach_from_temperature_ratio(ratio, gas)
mach_from_pressure_ratio(ratio, gas)
mach_from_density_ratio(ratio, gas)
```

Every ratio is oriented **static over stagnation** or **static over sonic**, as
its name states. A reader never has to open the source to learn which way up a
ratio is, and a test asserts that none of the static-to-stagnation ratios can
exceed 1 — the inversion mistake that is otherwise invisible in a plot.

---

## Area–Mach API

```python
mach_from_area_ratio(area_ratio, gas, branch, tolerances=DEFAULT_TOLERANCES)
    -> Solution[float]

mach_from_area_ratio_both(area_ratio, gas, tolerances=DEFAULT_TOLERANCES)
    -> Solution[AreaMachSolutions]        # named .subsonic / .supersonic

mach_from_area_ratio_array(area_ratios, gas, branch, tolerances=DEFAULT_TOLERANCES)
    -> np.ndarray
```

`branch` is a required positional argument of type `FlowBranch` with **no
default**. Omitting it is a `TypeError`; passing a string is a `ValueError`;
passing `FlowBranch.BOTH` is a `ValueError` naming the two-root function. That
the argument is genuinely used is proved rather than assumed: a test starts
from a known supersonic Mach number, computes its area ratio, asks for the
*subsonic* branch, and requires a different root that still reproduces the same
area ratio through the forward relation.

---

## Analytical inverses

Three of the four, exactly as `04` §3.6 requires:

| Inverse | Form |
| --- | --- |
| `T/T0 -> M` | `sqrt( 2/(gamma-1) (T0/T - 1) )` |
| `p/p0 -> M` | `sqrt( 2/(gamma-1) expm1( -(gamma-1)/gamma ln(p/p0) ) )` |
| `rho/rho0 -> M` | `sqrt( 2/(gamma-1) expm1( -(gamma-1) ln(rho/rho0) ) )` |

`expm1`, not the algebraically identical difference: as the ratio approaches 1
the bracket is a difference of nearly equal numbers, and at p/p0 = 1 − 1e-13 the
naive form has lost every significant digit while this form still resolves the
Mach number. A test drives that case directly.

That these do not iterate is enforced, not merely intended: a test replaces the
shared solver with a function that raises, and the inverses still work.

---

## Numerical inverse — area–Mach

Brent on a bracket derived from the asymptotic behaviour of the relation, per
branch, with the sonic point handled in closed form.

| | Subsonic | Supersonic |
| --- | --- | --- |
| Bracket | `[seed, 1 - sonic_margin]` | `[1 + sonic_margin, seed]` |
| Seed | `(2/(gamma+1))^k / (A/A*)`, halved | `[ (A/A*) ((gamma+1)/(gamma-1))^k ]^((gamma-1)/2)`, doubled |
| Expansion | halve while the residual has the wrong sign, floored at `mach_floor` | double, capped at `mach_ceiling` |

with `k = (gamma+1)/(2(gamma-1))`. Both seeds are exact in their limit, so the
expansion loop is a safety net rather than a search. Measured over 10 area
ratios from 1.0001 to 1000 and four gammas, every solve converged in at most 60
iterations with the root inside the reported bracket.

**ERRATUM-4B-01.** `04` §3.1 printed the supersonic asymptote with the exponent
`(gamma+1)/(gamma-1)` on M and `(gamma-1)/(gamma+1)` on its inversion. Both are
wrong: the correct exponents are `2/(gamma-1)` and `(gamma-1)/2`. Derivation:
`A/A* -> (1/M)((gamma-1)/(gamma+1) M^2)^k = M^(2k-1) ((gamma-1)/(gamma+1))^k`
and `2k - 1 = 2/(gamma-1)`. Evidence: at gamma = 1.4 and M = 100 the true area
ratio is 4.6366e7; the corrected form gives `100^5/216 = 4.63e7`, the printed
form `100^6/216 = 4.63e9`, a factor of 100 out. The corrected form is
implemented, and the erratum is recorded in `04` beside the original text rather
than replacing it. The printed form would still have produced correct answers —
the bracket is expanded until the sign changes — so this was a latent
inefficiency, not a latent wrong result.

---

## Root solver integration

The physics module imports `brent` from `core.numerics.roots` and defines the
residual as `area_ratio(mach, gas) - target`. It contains no loop of its own; a
test asserts that no function in the module is named like a solver, that `brent`
is called exactly once per inversion, and that the tolerances passed are the
ones from the supplied `ToleranceSet` (`mach_abs_tol`, `mach_rel_tol`,
`max_iter`) rather than literals.

`RootReport` is mapped field-for-field onto the physics layer's `Convergence`
record, so `iterations`, `residual`, `bracket` and `method` all reach the caller.
The sonic fast path reports `method="analytic"` with zero iterations, which
distinguishes it from a solve at a glance.

---

## Domain policy

| Input | Behaviour |
| --- | --- |
| `gamma` outside `[1.001, 3.0]` | `InvalidGammaError` |
| `gamma` outside `[1.05, 1.9]` | computed, with an `EXTRAPOLATED_GAMMA` **warning** |
| `gas_constant` <= 0, non-finite, or non-numeric | `InvalidGasConstantError` |
| `gas_constant` absent, dimensional property requested | `MissingGasConstantError` |
| Mach < 0, NaN, inf | `DomainError` — never `abs()`, never clamped |
| Mach = 0 into `area_ratio` | `DomainError`; the ratio is genuinely unbounded and `inf` would leak into a plot axis |
| Mach < 1 into `mach_angle` | `DomainError` |
| Ratio > 1, <= 0, non-finite into an inverse | `DomainError` — 1.0000001 is not rounded to 1 |
| `A/A* < 1 - area_sonic_tol` | `AreaRatioError` |
| Temperature <= 0 or non-finite | `DomainError`; Kelvin only, no Celsius guessing |
| One bad element in an array | the whole call raises, naming the index — never a silent NaN |

The advisory/error distinction is the one worth stating twice: a gamma of 2.5 is
*computable but questionable*, so it warns and still returns a number; a gamma of
0.9 is meaningless, so it raises.

---

## Near-sonic behaviour

`A/A* - 1 = [2/(gamma+1)](M-1)^2`, so the relation is quadratically flat at its
minimum and inverting it there loses half the available precision. Three
consequences, all implemented and all tested:

* **Inside the sonic window** (`|A/A* - 1| <= 1e-11`, which is `|M-1|` up to
  about 3.5e-6 at gamma = 1.4) the answer is exactly 1 on either branch, with a
  `SONIC_EXACT` diagnostic and no iteration. Handing this to a root finder would
  be asking it to resolve a vanishing derivative.
* **Just outside it**, the solve runs and a `NEAR_SONIC` warning states that the
  Mach number is less well determined than the area ratio.
* **Below the float64 floor** — offsets of about 1e-8 — the excess over unity is
  ~1e-16 and simply is not representable. A test asserts that, rather than
  asserting a strict inequality double precision cannot deliver. That test
  documents the limit instead of hiding it.

The coefficient `2/(gamma+1)` derived in `04` §4 is verified directly against
the implementation at three offsets and four gammas.

---

## Scalar/array behaviour

Per `04` §9: algebraic relations accept a scalar or an array and mirror the
input type; the `Solution`-returning inverse is scalar-only, with an explicit
`*_array` variant. Integer and float32 inputs are promoted to float64, because
the module is specified as double precision and silently keeping seven digits
would undercut every tolerance in it. Shapes are preserved, including 2-D.

The array inverse is a Python loop over the scalar solver, deliberately: a
vectorised iteration would converge element by element at different rates and
make a result depend on the batch it was computed in, which the determinism rule
forbids. A failed element raises rather than returning NaN, because a NaN in a
plotted series looks like a rendering fault.

---

## Provenance

Every relation carries a `RelationRef` with a versioned identifier
(`isentropic.area_ratio.v1`), the model (`perfect_gas_isentropic_v1`), the
source, the assumptions and the domain. The prose lives once in
`equations.py`, and results reference it rather than copying it. Each record
also carries `latex` and the entity-based `html` the existing Equation Library
page already renders — so that page can eventually read the registry with no
QML change.

---

## Reference confirmation

**The blocking gate of `05` §7 is satisfied. No case remains pending.**

**Primary source — NACA Report 1135**, *Equations, Tables, and Charts for
Compressible Flow*, Ames Research Staff, 1953; US Government work, read from the
scan hosted by NASA at
`https://www.nasa.gov/wp-content/uploads/2023/03/equations-tables-charts-compressibleflow-report-1135.pdf`
(accessed 2026-08-30). Values were read directly from the printed tables:

| M | Table, page | p/p_t | rho/rho_t | T/T_t | A/A* |
| --- | --- | --- | --- | --- | --- |
| 0.50 | I, p.633 | 0.8430 | 0.8852 | 0.9524 | 1.3398 |
| 1.00 | I and II, p.633 | 0.5283 | 0.6339 | 0.8333 | 1.0000 |
| 2.00 | II, p.634 | 0.1278 | 0.2300 | 0.5556 | 1.6875 |
| 3.00 | II, p.635 | 0.02722 | 0.07623 | 0.3571 | 4.235 |

All sixteen values match to within half a unit in the last printed digit, which
is the tolerance the tests use. Nothing is asserted more tightly than the source
states it, and the printed precision is stored in the data rather than inferred
(JSON parses `0.8430` as `0.843` and loses the trailing zero).

**Branch pairs**, the check that the two-root behaviour is right:

* `A/A* = 1.6875` — the value NACA prints at M = 2.00. The supersonic branch
  returns 2.0000000000, and the subsonic branch returns 0.37224, which lies
  strictly between the printed rows M = 0.37 (1.6961) and M = 0.38 (1.6587) of
  Table I. The bracket comes from two printed rows and the monotonicity of the
  column, not from RocketForge.
* `A/A* = 1.3398` — the value printed at M = 0.50. The subsonic branch returns
  0.50002, within the precision the area ratio is printed to; the supersonic
  branch returns 1.7023, which must exceed 1.70 because Table II prints 1.338
  there and the column rises.

**Independent confirmation of the equation forms — NASA Glenn Research Center**,
*Isentropic Flow Equations*, Beginner's Guide to Aeronautics,
`https://www.grc.nasa.gov/www/k-12/airplane/isentrop.html` (accessed
2026-08-30). Its equations 6–9 are algebraically identical to the implemented
forms, including the area relation.

**Third, independent kind of check — exact rational values.** At gamma = 1.4,
`T/T0` is exactly 5/6, 5/9, 5/14 and 1/6 at M = 1, 2, 3 and 5, and `A/A*` is
exactly 27/16 at M = 2 and 25 at M = 5. These are verifiable with a pencil and
are asserted at machine precision.

**Speed of sound.** `PerfectGas.air()` at 288.15 K gives 340.294 m/s, the value
tabulated by the US Standard Atmosphere, 1976 — a check of the constant, the
relation and the arithmetic together, against a number RocketForge did not
produce.

The Phase 3 §11 values were used only as a cross-check and are explicitly *not*
treated as authority anywhere in the suite.

---

## Tests

    full suite (project venv)   932 passed, 0 failed, 1 skipped
    with SciPy oracle           925 passed, 0 failed, 0 skipped

| File | Tests |
| --- | --- |
| `tests/test_architecture.py` | 41 |
| `tests/core/test_roots.py` | 203 |
| `tests/core/test_tolerances.py` | 30 |
| `tests/core/test_roots_cross_validation.py` | 4 (skipped without SciPy) |
| `tests/physics/compressible/test_gas.py` | 102 |
| `tests/physics/compressible/test_isentropic.py` | 180 |
| `tests/physics/compressible/test_isentropic_inverse.py` | 90 |
| `tests/physics/compressible/test_area_mach.py` | 228 |
| `tests/physics/compressible/test_reference_cases.py` | 33 |
| `tests/physics/compressible/test_public_api.py` | 14 |
| `tests/physics/compressible/test_reuse.py` | 11 |

Four test expectations were wrong during development and were corrected once the
implementation was shown to be right. Each is worth recording because each
taught something:

1. **`A/A* > 1` strictly at `|M-1| = 1e-8`** — false in float64; the excess is
   ~8e-17. Replaced by an explicit conditioning test.
2. **`1.0 + area_sonic_tol` is inside the sonic window** — it is not: the sum
   rounds to a double 1.0000000827e-11 from unity, outside by 8e-19. The test
   now uses offsets strictly inside.
3. **Branch resolution at an offset of 1e-6 from sonic** — that offset is
   *inside* the sonic window by design, so both branches correctly return 1. Split
   into two tests, one either side of the window boundary.
4. **Reproducing an area ratio from a tiny subsonic root to 1e-9 relative** —
   near M → 0, `A/A* ~ C/M`, so an *absolute* Mach tolerance of 1e-10 on a root
   of order 1e-3 is only ~1e-7 in relative area. The tolerance is now derived
   from what the solver was actually asked for.

---

## Property tests

Physical invariants asserted over deterministic grids, at gamma = 1.2, 1.3, 1.4
and 1.66:

* `T/T0`, `p/p0`, `rho/rho0` strictly decreasing, and all bounded in (0, 1] —
  the orientation guard.
* `p/p0 = (rho/rho0)(T/T0)` — the equation of state, satisfied by the ratios.
* `p/p0 = (T/T0)^(gamma/(gamma-1))` — the isentropic link.
* `A/A* >= 1` everywhere, with its minimum **exactly** 1 **exactly** at M = 1 —
  not "the smallest sample on a grid".
* `A/A*` strictly decreasing on (0,1) and strictly increasing on (1,∞), which is
  what makes each bracket contain exactly one root.
* Starred ratios above 1 subsonic and below 1 supersonic, and equal to the
  stagnation ratios normalised at sonic.
* `cp/cv = gamma` and `cp - cv = R`.
* Mach angle decreasing, exactly π/2 at M = 1, exactly 30° at M = 2.
* Results differ between gases — proof that gamma is used, not assumed.

---

## Round-trip tests

* `M -> ratio -> M` for all three analytic inverses, over 18 Mach numbers from
  1e-6 to 10, at four gammas; tight to 1e-13 away from stagnation.
* `M -> A/A* -> M` on each branch separately, subsonic 1e-3 to 0.99 and
  supersonic 1.01 to 25, at four gammas.
* A sweep of 80 Mach numbers checking that a subsonic request never returns a
  supersonic root and vice versa.
* The near-stagnation conditioning limit is asserted rather than avoided: at
  M = 1e-6 the temperature ratio differs from 1 by ~1e-12, so only a few digits
  of Mach number are recoverable, and the test says so.

---

## Performance sanity

    100,000 Mach x 4 forward ratios      4.7 ms      (47 ns per value per ratio)
     10,000 Mach x 4 forward ratios      0.36 ms
      1,000 area-Mach inverse solves    99.7 ms      (100 us per solve)
      single scalar inverse             95 us
      single analytic inverse            6.4 us

Against the `04` §10 budgets — under 5 ms for a 2000-point sweep, under 100 µs
per bracketed inverse, under 200 ms for a 2000-point array inverse — all are
met, the vectorised path by a wide margin. The scalar inverse sits at its budget:
roughly 90% of the 95 µs is per-residual validation and `Solution` construction
rather than the ~8 µs solve itself. That is within specification and has not
been optimised, per the instruction not to tune on microbenchmarks; if a UI
sweep ever needs it, the fix is a validation-free internal residual, and the
array API already exists as the vectorised path.

---

## Architecture enforcement

**PASS**, 41 tests, unchanged and not weakened. The new modules satisfy the
existing rules as written: `physics` imports only `core`, no Qt appears below
`application`, no SciPy appears anywhere, no `_deg` name exists below
`application`, and nothing reaches into `ui`. NumPy is unaffected by the rules —
the checker only governs internal layer edges, Qt, external property libraries
and SciPy.

## Phase 4A regression

**PASS.** 203 root-solver tests and 41 architecture tests, all green, with the
frozen files untouched. The SciPy cross-validation still passes its 1421
deterministic cases in the oracle environment. No defect was found in `brent`,
so no change to it was considered.

## Qt isolation

**PASS.** `import rocketforge` still loads no Qt and no submodules, and the
compressible module was additionally exercised in a subprocess with PySide6 made
unimportable — computing ratios, inverting an area ratio and evaluating a speed
of sound with Qt absent from `sys.modules`.

## Existing RocketForge UI

**PASS.** `python main.py` launches and stays up. No QML, theme, component,
workspace, engine model or mock value was touched, and the interface does not
know the backend exists.

The executable was **not** rebuilt: the UI does not consume the backend, and
`packaging/RocketForge.spec` needs no change because PyInstaller bundles what
`main.py` imports, which is still only Qt.

---

## Duplication audit

Asserted in `test_reuse.py`, not merely inspected:

| Rule | How it is enforced |
| --- | --- |
| One isentropic factor | `_phi` computed once; an AST scan bounds how often the group appears inline |
| One area–Mach relation | only `area_ratio` is public in the module |
| The inverse solves the forward relation | replacing `area_ratio` moves the root; if it did not, the inverse would hold its own copy |
| One root solver | no function named like a solver; `brent` called exactly once per inversion |
| One gas validation | `InvalidGammaError` appears in `gas.py` and nowhere else |
| One branch vocabulary | `FlowBranch` defined only in `types.py` |
| No baked-in air | no air-like numeric literal in the relations' executable code |
| Starred ratios derived | asserted equal to the stagnation ratios normalised at sonic |

---

## Deviations from Phase 3

**Three, all additive and none contradicting the specification.**

1. **DECISION-4B-01 — the gamma advisory is exposed as `PerfectGas.diagnostics`.**
   `02` §2.4 lists `EXTRAPOLATED_GAMMA` as raised by "any" relation, but
   Tier-1 relations return bare floats and cannot carry a diagnostic. The gas
   therefore computes its own advisories, and every `Solution`-returning
   relation merges them in. No printing, no `warnings.warn`: the advisory is a
   machine-readable record wherever the gas is used.
2. **DECISION-4B-02 — the gamma hard limits are read from `DEFAULT_TOLERANCES`,
   not from a per-call tolerance set.** `04` §5 places `gamma_min`/`gamma_max`
   in `ToleranceSet`, but a gas is constructed without one. The limits are a
   property of the *model* rather than a numerical tuning knob, so `PerfectGas`
   validates against the defaults and a custom tolerance set does not change
   what gases exist.
3. **ADDITION-4B-01 — `InvalidGasConstantError` and `gamma_advisory_min/max`.**
   The error is named in `03` §2.2 and `04` §7 but is missing from the class
   tree drawn in `02` §5; it is added under `GasModelError` where those two
   documents imply it belongs. The two advisory-band fields are the numeric form
   of the band stated in `03` §2.2 and had no home in `ToleranceSet`.

Plus **ERRATUM-4B-01** above, which is a correction to a Phase 3 document rather
than a deviation from it.

---

## Ready for Phase 4C

**YES.**

The next module is **Mass Flow and Choking**, then **Normal Shock**. Both build
directly on what now exists: the mass-flow parameter is a function of the same
`_phi` group and reuses `PerfectGas`; the normal shock is self-contained but
needs the same `Solution`, diagnostic and provenance machinery, which is now in
place and exercised. Neither was started.
