# 05 — Verification and Validation Plan

The gate between "the module exists" and "the UI may use it".

**UI screenshots are not validation.** A number rendered beautifully in a panel
is exactly as wrong as the same number printed to a terminal. Every physics
claim in this specification is validated in Python, headless, before any QML
binds to it (task §27, §143).

---

## 1. The hierarchy

```
   Equation, with a named source            <- 03, section 1.4 and per-relation
        |
   Implementation with a stated domain      <- 04, section 7
        |
   Unit tests (does it compute the formula)
        |
   Reference cases (does it match authority)
        |
   Property / invariant tests (does it behave like physics)
        |
   Round-trip and limit tests (is the inverse consistent, are the edges sane)
        |
   Cross-validation (does an independent source agree)
        |
   UI integration (only now)
```

A module that stops before "cross-validation" is not finished; a module that
skips to "UI integration" is a liability, because a plausible-looking curve hides
a wrong constant far better than a failing assertion does.

---

## 2. Test tree

```
tests/
  test_architecture.py                 # import allow-list, no-PySide6, no _deg below application
  core/
    test_roots.py                      # Brent itself: analytic roots, flat derivative,
                                       #   root at a bracket end, no sign change -> BracketError,
                                       #   max_iter behaviour, determinism
    test_units.py                      # every registered unit round-trips; offsets (K/degC, gauge)
    test_result.py                     # Solution semantics, unwrap, to_jsonable round-trip
    test_tolerances.py                 # ToleranceSet is frozen; overrides propagate
  physics/
    compressible/
      test_gas.py
      test_isentropic.py
      test_mass_flow.py
      test_normal_shock.py
      test_oblique_shock.py
      test_prandtl_meyer.py
      test_fanno.py
      test_rayleigh.py
      test_nozzle.py
      test_reuse.py                    # the duplication audit, executable (section 9)
      test_equations_registry.py       # every relation has a record; identifiers unique
  reference_data/
    isentropic_gamma_1.40.json
    area_mach_gamma_1.40.json
    mass_flow.json
    normal_shock_gamma_1.40.json
    oblique_shock_gamma_1.40.json
    prandtl_meyer_gamma_1.40.json
    fanno_gamma_1.40.json
    rayleigh_gamma_1.40.json
    nozzle_ar2.0_gamma_1.40.json
    SOURCES.md
```

Runner: pytest. No network, no Qt, no external solver in the suite. The whole
physics suite must run in a process where `import PySide6` fails — that is
asserted, not assumed.

---

## 3. Reference-data storage

Expected values live in JSON, not scattered through assertions (task §103).
Reason: a table of 200 numbers embedded in 200 test functions cannot be reviewed,
re-sourced, or regenerated; a data file can be diffed, and its provenance can be
recorded per row.

```json
{
  "schema_version": 1,
  "relation": "isentropic",
  "model": "perfect_gas_isentropic_v1",
  "gamma": 1.4,
  "generated": "2026-08-30",
  "provenance": "values evaluated from the closed forms in docs/engineering/03 at float64",
  "cross_checked_against": "NACA 1135 Table I (to be confirmed at implementation)",
  "default_rtol": 1e-10,
  "cases": [
    {
      "mach": 2.0,
      "temperature_ratio": 0.5555555556,
      "pressure_ratio": 0.1278045255,
      "density_ratio": 0.2300481458,
      "area_ratio": 1.6875,
      "rtol": 1e-9,
      "source": "exact rational: T/T0 = 5/9, A/A* = 27/16",
      "confirmed": "pending"
    }
  ]
}
```

Rules:

* Every case carries `source` and a `confirmed` field. `confirmed` starts at
  `"pending"` and becomes a citation (`"NACA 1135 Table I, M=2.00"`) once a human
  has checked it against the printed table. **A module is not accepted while any
  starred case in `03` §11 is still `"pending"`** (§7 below).
* `rtol` is per case, defaulting to the file's `default_rtol`, because a value of
  0.0018900384 and a value of 29.0 do not deserve the same absolute treatment.
* Regenerating the file requires a deliberate script run and shows up as a data
  diff in review — never as a silent test update.
* `SOURCES.md` in the same directory records, per file, which reference edition
  and table was used and by whom.

---

## 4. Unit-test matrix

Per module, what must exist. "Cases" refers to `03` §11.

| Module | Forward | Inverse | Branch | Limits | Invalid | Reference |
| --- | --- | --- | --- | --- | --- | --- |
| `gas` | cp, cv, a | — | — | γ → 1.001 | γ ≤ 1, R ≤ 0 | cp/cv for air |
| `isentropic` | 4 ratios + 3 starred + μ | 3 analytic + area-Mach | sub/sup/both | M = 0, 1, large | M < 0, ratio > 1, A/A* < 1 | §11.1, §11.2 |
| `mass_flow` | MFP, Γ, ṁ, flux, p*/p₀ | — | — | M = 0, 1, large | A ≤ 0, missing R | §11.3 |
| `normal_shock` | 6 ratios + entropy + A* ratio | M₁ from p₂/p₁ | — | M₁ = 1, large | M₁ < 1 | §11.4 |
| `oblique_shock` | θ(β), θ_max, β_sonic, full solve | β(θ) | weak/strong/both | θ → 0, θ → θ_max | M₁ ≤ 1, θ > θ_max | §11.5 |
| `prandtl_meyer` | ν, ν_max, μ | M(ν), expand, compress | — | M = 1, ν → ν_max | M < 1, ν < 0, ν ≥ ν_max | §11.6 |
| `fanno` | 6 relations | M(4fL*/D), duct | sub/sup | M = 1, M → 0, M → ∞ | L < 0, over-length | §11.7 |
| `rayleigh` | 5 relations | M(T₀/T₀*), heat addition | sub/sup | M = 1, 1/√γ, M → ∞ | r > 1, r < limit | §11.8 |
| `nozzle` | criticals, classify, distributed solve | shock location | all 7 regimes | boundaries | p_b/p₀ ≥ 1, bad geometry | §11.9 |

---

## 5. Per-relation acceptance checklist

Applied to every public relation before it is considered done. This is the
checklist a reviewer works through, not a suggestion.

1. The docstring states the equation, the assumptions, the domain, the units of
   every argument and the unit of the return.
2. The docstring cites the source **with the edition's own equation or table
   number** — filled in from the physical book, not from this specification
   (`03` §1.4).
3. There is an `EquationRecord` in the registry with a matching identifier.
4. Domain violations raise the exception named in `04` §7 — with a test.
5. At least two reference cases pass at the stated tolerance.
6. The invariants in §9 that apply to it pass.
7. If it has an inverse: the round-trip test in §10 passes on both branches.
8. If it iterates: the convergence tests in §12 pass.
9. Scalar and array calls agree (`04` §9) — tested by comparing element-wise.

---

## 6. Reference cases — the required minimum

Starred rows in `03` §11 are the mandatory set. Restated as a checklist:

**Isentropic (γ = 1.4):** M = 0, 1, 2, 3 for all four ratios, plus the exact
rational identities (T/T₀ = 5/9 at M = 2; A/A* = 27/16 at M = 2; A/A* = 25 at
M = 5), which are checked at `rtol = 1e-14` because they are exact.

**Area-Mach (γ = 1.4):** A/A* = 1 → M = 1 on both branches; A/A* = 2.0 →
(0.3059038342, 2.1971981217); A/A* = 4.0 → (0.1465482140, 2.9401791693).

**Normal shock (γ = 1.4):** M₁ = 2 and M₁ = 3 for all six outputs, plus the exact
rationals (p₂/p₁ = 9/2 and 31/3; ρ₂/ρ₁ = 8/3 and 27/7; M₂ = 1/√3 at M₁ = 2).

**Oblique shock (γ = 1.4):** M₁ = 2, θ = 10° → β_weak = 39.31393184°,
β_strong = 83.70008038°; M₁ = 3, θ = 20° → β_weak = 37.76363415°;
θ_max(M₁ = 2) = 22.97353176°; θ_max(M₁ = 3) = 34.07343978°.

**Prandtl–Meyer (γ = 1.4):** ν(2) = 26.3797608134°, ν(3) = 49.7573467443°,
ν_max = 130.4540768505°, and the inverse ν = 30° → M = 2.1339050332.

**Fanno (γ = 1.4, Fanning):** M = 0.3 → 4fL*/D = 5.2992531051; M = 0.5 →
1.0690603127; M = 2 → 0.3049965026; M = 3 → 0.5221594082; supersonic limit
0.8215081165. **The M = 0.5 case is the friction-convention guard** (`03` §8.2).

**Rayleigh (γ = 1.4):** M = 0.2, 0.5, 2, 3 for all five ratios; the T/T\* maximum
(γ+1)²/(4γ) = 36/35 at M = 1/√γ; the supersonic T₀/T₀\* limit (γ²−1)/γ².

**Nozzle (γ = 1.4, Ae/A\* = 2):** the three criticals 0.9371625024, 0.5134007280,
0.0939326457; the internal shock at A_s/A\* = 1.5 giving p_b/p₀ = 0.7584257377.

---

## 7. Cross-validation (task §96, §102)

**Requirement, not a suggestion: every starred reference case must be confirmed
against an independent authority before the module is accepted.**

Priority order:

1. **NACA Report 1135 tables** — the canonical tabulation, US Government work,
   covering isentropic, normal shock, oblique shock and Prandtl–Meyer.
2. **Anderson's appendices** — isentropic, normal shock, PM, θ-β-M.
3. **Shapiro Vol. I tables** — Fanno and Rayleigh, and the friction-factor
   convention in particular.
4. **NASA Glenn's interactive calculators** — informal spot checks only.

Rules that keep this honest:

* Confirmation is recorded per case in the reference-data file (`confirmed`
  field) and summarised in `SOURCES.md`. "It matched the calculator I found" is
  not a citation.
* **No external calculator or library becomes a runtime dependency.**
  Cross-validation is a one-time human activity whose *result* is stored, not a
  test that calls out to something.
* Where a published table is rounded to 4 decimals and our value carries 10, the
  test asserts against the published digits at the published precision, and the
  extra digits are ours to keep — but the file records both.
* If an authoritative source disagrees beyond rounding, the module stops. That
  is a specification bug, not a test to be loosened.

---

## 8. What "done" means for a coefficient

A subtle failure mode worth naming: an implementation can pass every reference
case and still be wrong for another γ, because the reference set is γ = 1.4. Two
guards:

* Every relation is additionally tested at γ = 1.2, 1.3 and 1.66 against the
  *γ-general* identities that must hold at any γ (§9), not against tabulated
  numbers.
* Where a γ-dependent closed form is claimed in this specification (Γ(γ), p*/p₀,
  ν_max, the Fanno supersonic limit, the Rayleigh supersonic limit, the four
  near-sonic coefficients of `04` §4, θ_max), the test evaluates it at four γ
  values against an independent numerical determination.

---

## 9. Property and invariant tests (task §97)

These are what catch a wrong sign or a transposed exponent that happens to agree
at one Mach number.

**Isentropic**

* p/p₀, T/T₀ and ρ/ρ₀ are strictly decreasing for M > 0.
* All three equal 1 at M = 0, and all lie in (0, 1] for M ≥ 0.
* `(p/p0) == (rho/rho0) * (T/T0)` to `rel_tol` — the ideal gas law, satisfied by
  the ratios.
* `(p/p0) == (T/T0)**(γ/(γ−1))` to `rel_tol`.
* A/A* has its minimum at M = 1, and that minimum equals exactly 1.
* A/A* is strictly decreasing on (0,1) and strictly increasing on (1,∞).
* μ decreases monotonically from π/2 at M = 1.

**Mass flow**

* MFP is maximised at M = 1 (`argmax` over a fine grid lands on the sonic
  sample), and dMFP/dM changes sign there.
* `MFP(1, γ) == Γ(γ)` to `rel_tol`.
* `p*/p0 == pressure_ratio(1, γ)` to `rel_tol`.
* ṁ scales exactly linearly with A and with p₀, and as T₀^(−1/2).

**Normal shock**

* M₂ < 1 for every M₁ > 1, and M₂ → √((γ−1)/2γ) as M₁ → ∞ (0.3779645 at γ = 1.4).
* p₂/p₁, T₂/T₁, ρ₂/ρ₁ all > 1 for M₁ > 1 and strictly increasing in M₁.
* p₀₂/p₀₁ < 1 for M₁ > 1, strictly decreasing, and → 1 as M₁ → 1⁺.
* Entropy change ≥ 0 always, = 0 only at M₁ = 1 (second law).
* T₀₂/T₀₁ is exactly 1.0 (identity, not a computation).
* ρ₂/ρ₁ is bounded above by (γ+1)/(γ−1) = 6 at γ = 1.4 — a strong check that the
  density formula is not inverted.
* `A2*/A1* == p01/p02` to `rel_tol`.

**Oblique shock**

* θ(μ) = 0 and θ(π/2) = 0 for every M₁ > 1.
* θ(β) has exactly one interior maximum, at the closed-form β_θmax.
* The weak root is always < β_θmax; the strong root always >.
* M₂ < M₁ always; M₂ < 1 for the strong branch always.
* At β = π/2, every ratio equals the normal-shock value at M₁ — to machine
  precision, since it is the same code path.
* θ_max increases monotonically with M₁ and approaches its hypersonic limit.

**Prandtl–Meyer**

* ν is strictly increasing on M ≥ 1; ν(1) = 0 exactly.
* ν < ν_max for every finite M; ν → ν_max as M → ∞.
* An expansion always gives M₂ > M₁, p₂ < p₁, T₂ < T₁, ρ₂ < ρ₁.
* p₀ and T₀ are unchanged across the fan (isentropic) — tested by comparing the
  stagnation values computed at stations 1 and 2.

**Fanno**

* Both branches move towards M = 1 as the duct lengthens (subsonic M rises,
  supersonic M falls).
* 4fL*/D ≥ 0 always, = 0 only at M = 1, strictly decreasing along the duct.
* p₀/p₀\* > 1 on both sides with its minimum of 1 at M = 1 — friction always
  destroys stagnation pressure.
* T₀ is constant (adiabatic): `T0/T0* == 1` identically.
* The two coincidences of `03` §8.4 hold **exactly**:
  `fanno.temperature_ratio == isentropic.temperature_ratio_star` and
  `fanno.stagnation_pressure_ratio == isentropic.area_ratio`.
* The non-coincidence holds: `fanno.pressure_ratio != isentropic.pressure_ratio_star`
  at M = 0.5 and M = 2 (guards against a copy-paste).

**Rayleigh**

* T₀/T₀\* ≤ 1 everywhere, = 1 only at M = 1 (thermal choking is the ceiling).
* T/T\* has its maximum at M = 1/√γ with value (γ+1)²/(4γ) — **and T/T\* is
  therefore decreasing on (1/√γ, 1) while heat is being added.** This test exists
  specifically so that a future "simplification" cannot make T/T\* monotone.
* p₀/p₀\* ≥ 1 on both sides, minimum 1 at M = 1.
* p/p\* is strictly decreasing in M over the whole range.
* T₀/T₀\* → (γ²−1)/γ² as M → ∞.
* No Rayleigh starred ratio equals its isentropic counterpart (§9.4 of `03`).

**Nozzle**

* `third < second < first < 1` for every Ae/A\* > 1 and every γ.
* All three criticals → 1 as Ae/A\* → 1⁺ (a straight duct has no room for any of
  the regimes).
* The shock position moves monotonically downstream as p_b falls.
* At the second critical, the solved shock position equals the exit exactly.
* ṁ is identical across every choked regime for a given p₀, T₀, A_throat — the
  physical signature of choking, and a strong end-to-end check.
* p₀ is constant along the duct except for exactly one downward step at a shock;
  T₀ is constant everywhere.
* M(x) is continuous except at the shock, and M = 1 exactly at the throat
  whenever `choked` is true.
* Mass flow computed at every station from ρVA agrees to `rel_tol` — the
  continuity check, which catches a wrong branch selection anywhere in the array.

---

## 10. Round-trip tests (task §98)

For every invertible relation, forward then inverse must recover the input.

| Round trip | Grid | Tolerance |
| --- | --- | --- |
| `M → p/p0 → M` | M ∈ {0.01 … 10}, 40 points, log-spaced | `rtol = 1e-10` |
| `M → T/T0 → M` | same | `rtol = 1e-10` |
| `M → ρ/ρ0 → M` | same | `rtol = 1e-10` |
| `M → A/A* → M` (SUBSONIC) | M ∈ (0.01, 0.999) | `rtol = 1e-8` |
| `M → A/A* → M` (SUPERSONIC) | M ∈ (1.001, 20) | `rtol = 1e-8` |
| `M → ν → M` | M ∈ [1.001, 20] | `rtol = 1e-9` |
| `M₁, θ → β → θ` (both branches) | M₁ ∈ {1.5, 2, 3, 5}, θ ∈ (0, θ_max) | `atol = 1e-9` rad |
| `M → 4fL*/D → M` (both branches) | M ∈ (0.05, 0.99) ∪ (1.01, 5) | `rtol = 1e-8` |
| `M → T0/T0* → M` (both branches) | same | `rtol = 1e-8` |
| `A_s → p_b → A_s` (nozzle shock) | A_s/A* ∈ (1.05, 0.95·AR) | `rtol = 1e-7` |

The looser tolerances on the area-Mach, Fanno and Rayleigh round trips near their
brackets' ends are not slack — they are the conditioning limit derived in `04`
§4. Each of those tests is additionally run *excluding* the near-sonic band to
demonstrate that `rtol = 1e-12` is achieved away from M = 1, which proves the
looseness is physical rather than a weak implementation.

Round trips must also be run at γ = 1.2, 1.3 and 1.66.

---

## 11. Limit tests (task §99)

| Limit | Assertion |
| --- | --- |
| M → 0 | all isentropic ratios → 1; MFP → 0; A/A* → ∞ (raises); no `nan` anywhere |
| M = 1 exactly | every relation returns its exact sonic value; A/A* = 1; 4fL*/D = 0; T₀/T₀\* = 1; ν = 0; p₀₂/p₀₁ = 1; no division by zero |
| M → large (100) | every value finite; A/A* ≈ 4.64 × 10⁷ (γ = 1.4); p/p₀ ≈ 2.8 × 10⁻¹²; no overflow |
| M > `mach_ceiling` | `DomainError`, not `inf` |
| γ → 1.001 | finite results at M = 5 for every relation; exponents ≈ 1000 do not overflow |
| γ = 3.0 | finite results; ν_max, Γ, p*/p₀ all sane |
| θ → 0 (oblique) | β → μ; every ratio → 1; M₂ → M₁ |
| θ → θ_max | weak and strong roots converge to β_θmax; the merged-root branch fires |
| Shock strength → 0 (M₁ → 1⁺) | every normal-shock ratio → 1; entropy change → 0 from above, never negative |
| A/A* → 1⁺ | both branches → 1; the sonic-tolerance branch returns exactly 1 |
| Fanno → star | 4fL*/D → 0 from above on both branches; never negative |
| Rayleigh → star | T₀/T₀\* → 1 from below on both branches; never above 1 |
| Fanno supersonic L → L_∞ | `NO_SOLUTION`/`FANNO_LIMIT`, not a runaway bracket |
| Rayleigh supersonic r → (γ²−1)/γ² | `NO_SOLUTION`/`RAYLEIGH_LIMIT` |
| Nozzle Ae/A* → 1⁺ | all three criticals → 1; classification still well-ordered |

Plus the conditioning checklist of `04` §11, one test per row.

---

## 12. Invalid-input tests (task §100)

Each asserts the **specific** exception type from `04` §7, not merely that
something was raised.

| Input | Expected |
| --- | --- |
| `PerfectGas(gamma=1.0)` / `0.9` / `-1` | `InvalidGammaError` |
| `PerfectGas(gamma=1.4, gas_constant=0)` / negative | `InvalidGasConstantError` |
| `mass_flow(...)` with `gas_constant=None` | `MissingGasConstantError` |
| `isentropic.pressure_ratio(mach=-2)` | `DomainError` (never 0, never 2) |
| `isentropic.area_ratio(mach=0)` | `DomainError` |
| `mach_from_pressure_ratio(1.2)` / `(0.0)` / `(-0.1)` | `DomainError` |
| `mach_from_area_ratio(0.8, ...)` | `AreaRatioError` (never clamped to 1) |
| `mach_from_area_ratio(2.0, gas)` without `branch` | `TypeError` (the argument is required) |
| `mach_from_area_ratio(2.0, gas, FlowBranch.BOTH)` | `ValueError` naming `*_both` |
| `normal_shock.solve(0.8)` | `SubsonicShockError` |
| `prandtl_meyer.nu(0.9)` | `SubsonicExpansionError` |
| `mach_from_nu(-0.1)` | `DomainError` |
| `mach_from_nu(ν_max + 0.1)` | `Solution` with `NO_SOLUTION` (not an exception — it is a meaningful question) |
| `oblique_shock.solve(2.0, radians(40))` | `Solution` with `NO_SOLUTION` + `DETACHED_SHOCK` |
| `oblique_shock.solve(0.9, ...)` | `SubsonicShockError` |
| `fanno.mach_from_friction_parameter(-1, ...)` | `DomainError` |
| `rayleigh.mach_from_stagnation_temperature_ratio(1.5, ...)` | `Solution` with `THERMALLY_CHOKED` |
| `nozzle.classify(AR, 1.0, gas)` / `1.5` | `InputError` |
| `nozzle.classify(0.8, ...)` | `GeometryError` |
| `AreaDistribution` with non-monotone x | `GeometryError` |
| `AreaDistribution` with a negative area | `GeometryError` |
| `AreaDistribution` with two interior minima | `GeometryError` from the C-D solver |
| `FlowState(pressure=-1, ...)` | `DomainError` |
| Array input with one bad element | raises, and the message names the index |
| `nan` / `inf` Mach | `DomainError`, checked before arithmetic |

The exception-versus-`Solution` split is itself under test: a reviewer changing
one to the other breaks a test on purpose.

---

## 13. Convergence tests (task §101)

For every iterative solver, six tests — not just "the number looks right":

1. **Converges** — `Convergence.converged is True` and `iterations <= 60` on a
   representative grid.
2. **Residual** — `|f(root)| <= residual_tol` on the same grid.
3. **Correct branch** — the returned root lies inside the requested branch's
   interval, on every grid point. This is what catches a bracket that silently
   spans the sonic point.
4. **Bracket integrity** — `Convergence.bracket` end points genuinely straddle
   the root (opposite signs), asserted by re-evaluating the residual.
5. **Max-iteration behaviour** — with `max_iter = 2`, the solver returns
   `NOT_CONVERGED` with the best iterate and does not raise, does not loop, and
   does not return `nan`.
6. **Near-singular input** — inputs within `near_sonic_mach` of the sonic point
   return the sonic result or a converged root carrying `NEAR_SONIC`, never a
   failure.

Additionally: `Convergence is None` for every closed-form relation, and
`Convergence is not None` for every iterative one — a structural test over the
whole module, so a future closed-form optimisation cannot silently pretend to
have iterated (or vice versa).

---

## 14. The duplication audit, executable (task §138)

`test_reuse.py` turns the audit table of `02` §12 into assertions:

* **Oblique ⊃ normal shock:** for M₁ ∈ {1.5, 2, 3, 5} and β spanning
  [μ, π/2], `oblique.solve_from_beta(M₁, β)` ratios equal
  `normal_shock.<same>(M₁·sin β)` to machine precision (`rtol = 1e-15`). Machine
  precision, not `1e-10` — anything looser would permit a re-derivation.
* **PM ⊃ isentropic:** `expand()` ratios equal the quotient of
  `isentropic` values at M₁ and M₂ to `rtol = 1e-15`.
* **Nozzle ⊃ isentropic + normal shock:** the shock-station values in a
  distributed solution equal direct `normal_shock` calls at the same M to
  machine precision; every non-shock station equals a direct `isentropic` call.
* **Fanno/isentropic coincidences and non-coincidences** as listed in §9.
* **Static AST check:** `oblique_shock.py` and `prandtl_meyer.py` contain no
  `**` exponentiation with the exponent `gamma/(gamma-1)` or
  `(gamma+1)/(2*(gamma-1))` — a crude but effective grep for a re-implemented
  isentropic or shock formula. Reviewed as a heuristic, with a documented
  allow-list if a legitimate exception appears.

---

## 15. Coverage philosophy (task §105)

Line coverage is not the target. A module can reach 100% by calling every
function once with γ = 1.4 and M = 2, and still be wrong everywhere else.

What is actually required before a module is accepted:

| Requirement | Measure |
| --- | --- |
| Every public relation has ≥ 2 reference cases | checklist §5 |
| Every documented domain boundary has an invalid-input test | §12, one row each |
| Every branch of every branched relation is exercised | §13.3 |
| Every inverse has a round trip on every branch | §10 |
| Every physical invariant in §9 is asserted | §9 |
| Every limit in §11 is asserted | §11 |
| Every iterative solver has all six convergence tests | §13 |
| The reuse audit passes | §14 |

Line coverage is *reported* (and will land near 100% as a by-product), but it is
never the acceptance criterion, and a coverage number is never accepted in place
of a missing invariant test.

---

## 16. The UI integration gate (task §143)

**A submodule may not be bound to QML until all of the following are true.** This
is a hard rule, and the checklist belongs in the Phase 4 pull request.

1. Unit tests pass.
2. Reference cases pass, and every starred case is `confirmed` against an
   external authority (§7) — no `"pending"` rows remain.
3. Round-trip tests pass on every branch.
4. Invariant and limit tests pass.
5. Invalid-input tests pass with the specific exception types.
6. Convergence tests pass, including the max-iteration and near-singular cases.
7. The reuse audit passes.
8. Tests pass at γ = 1.2, 1.3, 1.4 and 1.66.
9. The physics package imports and runs with PySide6 absent from the process.
10. The relation appears in the equation registry with a source citation
    carrying a real equation/table number.

Only then does the controller get written, and even then the controller has its
own (small) tests: input validation, formatting, em dash for `None`, diagnostic
mapping. The QML itself remains frozen; if a page genuinely cannot express a
result, that is a UI requirement recorded in `07` §9 and scheduled as its own
phase — not a change smuggled into a physics commit.

---

## 17. Regression policy

* Reference-data files are the regression baseline. A change in any stored value
  requires a new `model` identifier (`01` §10) and an explicit review of why the
  number moved.
* A bug fix that changes a number gets a test named for the bug, added to the
  reference file with `source: "bug fix #NNN, verified against <authority>"`.
* Performance budgets (`04` §10) are measured but not asserted in CI; a
  regression there is a discussion, not a build break.
