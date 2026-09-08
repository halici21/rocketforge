# 04 — Numerical Methods and Domain Policy

Companion to `03`. Everything here is a decision an implementer would otherwise
have to invent: which root finder, which bracket, which tolerance, what happens
at the edges. No implementation.

---

## 1. Principles

1. **Analytic beats iterative.** If a closed form exists, it is the answer and
   the numerical method is demoted to a test oracle. This applies to three of
   the four isentropic inverses (`03` §3.3), θ_max (`03` §6.3) and β_sonic
   (`03` §6.4) — four places where a naive implementation would iterate.
2. **Bracketed beats unconstrained.** Every remaining inverse in v1 is a scalar,
   continuous, strictly monotone function on a physically bounded interval. That
   is exactly the case where Brent is unbeatable and Newton is a liability.
3. **A bracket must be derived, not guessed.** Every bracket below comes from
   the physics of the relation. Where an end point cannot be derived in closed
   form, an asymptotic seed is expanded geometrically until the sign changes,
   with a documented ceiling.
4. **Report, never fudge.** No clamping, no silent branch choice, no `nan`
   escaping into a result. If it did not converge, the status says so.

---

## 2. Root-finding method selection

Comparison, then the per-relation decision.

| Method | Robust without a good guess | Needs derivative | Converges | Fails how |
| --- | --- | --- | --- | --- |
| Bisection | yes (given a bracket) | no | linear, ~52 iterations for `float64` | never, if bracketed |
| **Brent (inverse quadratic + secant + bisection fallback)** | **yes (given a bracket)** | **no** | **superlinear, typically 6–12 iterations** | **never, if bracketed** |
| Newton | no | yes | quadratic near the root | diverges, or leaves the domain and returns `nan` |
| Secant | no | no | superlinear | diverges; no bracket to fall back on |

**Baseline: Brent, always, for every v1 inverse.** The functions cost ~10 flops;
6–12 evaluations is free at interactive rates, and the guaranteed-convergence
property removes a whole class of support problems. Newton is rejected outright
for the area-Mach inverse in particular: dA/dM = 0 at M = 1, so a Newton step
from anywhere near sonic divides by a near-zero derivative and throws the iterate
far outside the physical domain — often onto the *other* branch, which produces a
wrong answer rather than an error.

**Implementation: internal, in `core/numerics/roots.py` (ADR-09).**

```python
def brent(f, a, b, *, xtol, rtol, max_iter) -> tuple[float, RootReport]: ...
```

`RootReport` carries `converged`, `iterations`, `residual`, `bracket`, `method`,
and feeds `Convergence` (`02` §2.3) directly. The function must never raise on
non-convergence: it returns the best iterate with `converged=False`, and the
caller decides whether that becomes `NOT_CONVERGED` or an exception (the
`*_strict` variants).

Requirement on the implementation, since it is ours: `brent` must be tested
against analytic roots including a flat-derivative case, an
asymptotically-approached root, a root exactly at a bracket end, and a bracket
with no sign change (must raise `BracketError`, not loop).

---

## 3. Per-inverse decisions

### 3.1 Area-Mach inverse — `A/A* → M`

| | |
| --- | --- |
| Method | **Brent** |
| Monotonicity | strictly decreasing on (0,1), strictly increasing on (1,∞); minimum exactly 1 at M = 1 |
| Subsonic bracket | `[M_sub_seed, 1 − SONIC_MARGIN]` |
| Supersonic bracket | `[1 + SONIC_MARGIN, M_sup_seed]` |
| Tolerance | `xtol = MACH_ABS_TOL`, `rtol = MACH_REL_TOL` |
| Special cases | `AR < 1 − AREA_SONIC_TOL` → `AreaRatioError`; `|AR − 1| ≤ AREA_SONIC_TOL` → M = 1 exactly |

**Bracket seeds, derived rather than guessed.** In each limit A/A* has a clean
asymptotic form that inverts in closed form and gives a starting bound:

* As M → 0: `A/A* → (1/M)·(2/(γ+1))^{(γ+1)/(2(γ−1))}`, so
  `M_sub_seed ≈ (2/(γ+1))^{(γ+1)/(2(γ−1))} / AR`. Take half of it to guarantee
  the sign, then halve again while `F(lo) < 0`, floored at `MACH_FLOOR`.
* As M → ∞: `A/A* → M^{(γ+1)/(γ−1)} · ((γ−1)/(γ+1))^{(γ+1)/(2(γ−1))}`, so
  `M_sup_seed ≈ [AR · ((γ+1)/(γ−1))^{(γ+1)/(2(γ−1))}]^{(γ−1)/(γ+1)}`. Double it,
  then double while `F(hi) < 0`, capped at `MACH_CEILING`.

> **ERRATUM-4B-01 (recorded 2026-08-30, Phase 4B implementation).** The
> supersonic asymptote printed above is wrong. With `k = (γ+1)/(2(γ−1))` the
> correct limit and its inversion are
>
> ```
> A/A*        ->  M^(2/(γ−1)) · ((γ−1)/(γ+1))^k
> M_sup_seed  ~=  [ (A/A*) · ((γ+1)/(γ−1))^k ] ^ ((γ−1)/2)
> ```
>
> The exponent on M is `2/(γ−1)`, not `(γ+1)/(γ−1)`, and the inversion exponent
> is `(γ−1)/2`, not `(γ−1)/(γ+1)`.
>
> *Derivation:* `A/A* -> (1/M)·((γ−1)/(γ+1)·M²)^k = M^(2k−1)·((γ−1)/(γ+1))^k`,
> and `2k − 1 = (γ+1)/(γ−1) − 1 = 2/(γ−1)`.
>
> *Evidence:* at γ = 1.4 and M = 100 the true area ratio is 4.6366×10⁷. The
> corrected form gives `100⁵/216 = 4.63×10⁷`; the printed form gives
> `100⁶/216 = 4.63×10⁹`, a factor of 100 out.
>
> The corrected form is what `rocketforge/physics/compressible/isentropic.py`
> implements. The original text is left above so the correction is traceable.
> Note the printed form would still have produced a working solve — the bracket
> is expanded until the sign changes — but from a systematically poor seed, so
> this was a latent inefficiency rather than a latent wrong answer.

Both seeds are exact in the limit and conservative in between, so the expansion
loop almost never runs. This is what task §77 asks for instead of an arbitrary
`M_max = 1000`.

Sanity of the ceiling: at M = 100, γ = 1.4, A/A* = 4.64×10⁷ and p/p₀ = 2.8×10⁻¹².
`MACH_CEILING = 100` therefore covers every area ratio a real device has by
several orders of magnitude, while staying inside the range where a calorically
perfect gas is even arguably meaningful. Beyond it the answer is a modelling
error, not a numerical one, and the module says so rather than iterating into
nonsense.

### 3.2 Prandtl–Meyer inverse — `ν → M`

| | |
| --- | --- |
| Method | **Brent** |
| Monotonicity | strictly increasing on M ≥ 1; dν/dM = √(M²−1)/(M·φ) ≥ 0, zero only at M = 1 |
| Bracket | `[1.0, hi]` — the lower end is exact and needs no margin, since ν(1) = 0 < ν_target |
| `hi` seed | closed form from the large-M asymptote, below — no expansion loop needed |
| Tolerance | `xtol = MACH_ABS_TOL`, `rtol = MACH_REL_TOL` |
| Special cases | `ν ≤ NU_TOL` → M = 1 exactly; `ν ≥ ν_max − NU_TOL` → `NO_SOLUTION` |

**Upper bracket end, derived.** Using `arctan x → π/2 − 1/x` for large x in the
two arctangents of ν gives

$$
\nu_{\max} - \nu(M) \;\approx\; \frac{2}{(\gamma-1)M}
\qquad\Longrightarrow\qquad
M_{\text{seed}} \;=\; \frac{2}{(\gamma-1)\left(\nu_{\max}-\nu_{\text{target}}\right)}
$$

*Verified:* this seed **over**estimates M at every point tested (M = 1.5, 2, 3, 5,
10, 30 at γ = 1.2, 1.4 and 1.66), by a factor between 1.001 and 1.96 — closest at
high Mach, most conservative at low Mach where the bracket is cheap anyway. It is
therefore always a valid upper end, and the expansion loop in the pseudocode of
`03` §12.3 is a safety net that never runs in practice. It is also always > 1, so
the bracket is never degenerate. Cap at `MACH_CEILING` regardless.

Newton is tempting here because dν/dM is available in closed form, but it fails
at exactly the point users start from: at M = 1 the derivative is 0, so a first
Newton step from M = 1 is undefined. Brent from `[1, hi]` has no such problem.

### 3.3 Oblique shock β from θ

| | |
| --- | --- |
| Method | **Brent on each side of β_θmax** |
| θ_max | **closed form** (`03` §6.3) — no iteration at all |
| β_sonic | **closed form** (`03` §6.4) — no iteration |
| Weak bracket | `[μ + ANGLE_MARGIN, β_θmax]` |
| Strong bracket | `[β_θmax, π/2 − ANGLE_MARGIN]` |
| Tolerance | `xtol = ANGLE_ABS_TOL` (radians) |
| Special cases | θ ≤ `ANGLE_TOL` → β = μ; θ > θ_max + `ANGLE_TOL` → `NO_SOLUTION`/`DETACHED_SHOCK`; `|θ − θ_max| ≤ ANGLE_TOL` → the merged root β_θmax |

Splitting at the closed-form maximum is what makes each half strictly monotone,
so each bracket has exactly one root. Any implementation that searches the whole
[μ, π/2] interval at once is relying on luck about which root Brent lands on.

The conditioning caveat: near θ_max the two roots are close and θ(β) is flat, so
β is poorly determined. The bracket end points differ by less than
`ANGLE_ABS_TOL` in that regime, which is precisely when the merged-root branch
fires. A `NEAR_THETA_MAX` warning is emitted when
`θ_max − θ < 0.01 · θ_max`, telling the user that β is sensitive there.

### 3.4 Fanno inverse — `4fL*/D → M`

| | |
| --- | --- |
| Method | **Brent** |
| Subsonic | strictly decreasing from +∞ (M → 0) to 0 (M = 1) |
| Supersonic | strictly increasing from 0 (M = 1) to the finite limit `L_∞ = −1/γ + (γ+1)/(2γ)·ln((γ+1)/(γ−1))` (0.8215081165 at γ = 1.4) |
| Subsonic bracket | `[lo, 1 − SONIC_MARGIN]`, `lo` seeded from the small-M asymptote `4fL*/D ≈ 1/(γM²)` → `lo ≈ 1/√(γL)`, then halved while needed, floored at `MACH_FLOOR` |
| Supersonic bracket | `[1 + SONIC_MARGIN, MACH_CEILING]` — a fixed ceiling is legitimate here because the function is bounded and the target is checked against `L_∞` first |
| Special cases | `L ≤ FANNO_TOL` → M = 1 exactly; supersonic with `L > L_∞ − FANNO_TOL` → `NO_SOLUTION`/`FANNO_LIMIT` |

The supersonic branch is the one that catches implementers out: because the
function is bounded, an unguarded bracket expansion runs to the ceiling and then
reports a spurious non-convergence. Checking against `L_∞` **before** bracketing
turns that into a correct physical answer.

### 3.5 Rayleigh inverse — `T₀/T₀* → M`

| | |
| --- | --- |
| Method | **Brent** |
| Subsonic | strictly increasing from 0 (M → 0) to 1 (M = 1) |
| Supersonic | strictly decreasing from 1 (M = 1) to `(γ²−1)/γ²` (0.4897959184 at γ = 1.4) as M → ∞ |
| Subsonic bracket | `[MACH_FLOOR, 1 − SONIC_MARGIN]` — both ends are exact bounds; no expansion needed |
| Supersonic bracket | `[1 + SONIC_MARGIN, MACH_CEILING]`, after checking the target against the limit |
| Special cases | `r > 1 + RAYLEIGH_TOL` → `THERMALLY_CHOKED`; `|r − 1| ≤ RAYLEIGH_TOL` → M = 1; supersonic with `r < (γ²−1)/γ² − RAYLEIGH_TOL` → `NO_SOLUTION`/`RAYLEIGH_LIMIT` |

The two bounded limits (1 above, `(γ²−1)/γ²` below on the supersonic branch) mean
this inverse never needs a bracket search at all — both brackets are closed-form.

### 3.6 Other analytic inverses

`p/p₀ → M`, `T/T₀ → M`, `ρ/ρ₀ → M` are closed form (`03` §3.3). **They must not
be implemented with a root finder.** A test asserts they return exactly (to
`REL_TOL`) the same value as a Brent solve of the forward relation, which both
validates the closed form and documents the equivalence.

Numerical care: use `expm1(((γ−1)/γ)·log(p0/p))` rather than
`(p0/p)^((γ−1)/γ) − 1`. At p/p₀ = 0.999 the naive form loses about three
significant digits in the subtraction; `expm1` loses none.

### 3.7 Nozzle internal shock location

| | |
| --- | --- |
| Method | **Brent on `A_s/A*`** (not on x, and not on M) |
| Monotonicity | `F(A_s)` is strictly decreasing (argued in `03` §10.6) |
| Bracket | `[1 + SONIC_MARGIN, A_exit/A*]` — closed form, because the two ends evaluate to the first and second criticals |
| Tolerance | `xtol = AREA_ABS_TOL`, `rtol = AREA_REL_TOL` |
| Cost | each residual evaluation runs two nested area-Mach inversions, so ~10 outer × ~10 inner ≈ 100 relation evaluations — still well under a millisecond |

**Why the shock position is solved in area, not in x.** Area is the variable the
physics depends on; x enters only through the geometry. Solving in A_s keeps the
residual smooth even when A(x) is supplied on a coarse or unevenly spaced grid,
and it makes the dimensionless API (`shock_area_ratio`) possible without any
geometry at all. The conversion A_s → x_s is a monotone interpolation on the
diverging side afterwards, and is the only place the geometry resolution matters.

Nested-solve tolerance rule: the inner area-Mach inversions must be solved at
least two orders tighter than the outer residual tolerance, or the outer Brent
sees a noisy function and stalls. This is stated as a hard requirement, not
advice.

---

## 4. Near-sonic conditioning — quantified

The sonic point is where every relation in this module is flat, and the flatness
is not a numerical artefact but a property of the equations. Writing M = 1 + ε
and expanding:

| Relation | Near-sonic behaviour | Coefficient at γ = 1.4 |
| --- | --- | --- |
| A/A* − 1 | `≈ [2/(γ+1)]·ε²` | 0.8333333 |
| 4fL*/D | `≈ [4/(γ(γ+1))]·ε²` | 1.1904762 |
| 1 − T₀/T₀* (Rayleigh) | `≈ [4/(γ+1)²]·ε²` | 0.6944444 |
| ν | `≈ [4√2/(3(γ+1))]·ε^{3/2}` | 0.7856742 |

*These four coefficients were derived analytically and then confirmed
numerically at γ = 1.15, 1.2, 1.3, 1.4 and 1.66; agreement is to six significant
figures (the residual being the finite-difference error of the check, not of the
formula).*

**The consequence, stated plainly.** Three of the four relations are *quadratic*
at the sonic point, so inverting them loses half the available precision:

$$
|M - 1| \;\approx\; \sqrt{\frac{\gamma+1}{2}\,\delta}
\qquad\text{where }\delta = \left|\frac{A}{A^{*}}-1\right|
$$

| δ = \|A/A* − 1\| | best achievable \|M − 1\| (γ = 1.4) |
| --- | --- |
| 10⁻⁶ | 1.1 × 10⁻³ |
| 10⁻⁹ | 3.5 × 10⁻⁵ |
| 10⁻¹¹ | 3.5 × 10⁻⁶ |
| 2.2 × 10⁻¹⁶ (machine epsilon) | 1.6 × 10⁻⁸ |

So even with a *perfect* root finder and an exact input, Mach number near sonic
cannot be resolved better than about 10⁻⁸ in `float64`. Chasing `xtol = 1e-12`
on M there is meaningless. This is the analysis behind ADR-11, and it is why the
policy is a sonic tolerance plus an honest warning rather than tighter
tolerances.

Prandtl–Meyer is the exception: its 3/2-power behaviour loses only a third of
the digits, so `ν → M` is genuinely better conditioned near M = 1 than
`A/A* → M`. Worth knowing when the two are used together.

**Policy that follows:**

* `AREA_SONIC_TOL = 1e-11` on the area ratio → M is pinned to exactly 1 whenever
  the true M is within ~3.5 × 10⁻⁶ of sonic. Inside that window, returning 1 is
  more accurate than anything the root finder could produce.
* `NEAR_SONIC_MACH = 1e-3`: when the *solved* M lands within this of 1, attach
  the `NEAR_SONIC` warning quoting the resolution limit. This is a wide window
  on purpose — it is an honesty flag, not an error.
* The same treatment, with the module's own tolerance name, for Fanno
  (`FANNO_TOL`) and Rayleigh (`RAYLEIGH_TOL`).

---

## 5. Tolerance categories

One epsilon for everything is forbidden (task §78). Named categories, each with
a rationale, gathered in a frozen `ToleranceSet` that every solver accepts as a
defaulted argument.

```python
@dataclass(frozen=True, slots=True)
class ToleranceSet:
    # --- generic comparison ---
    rel_tol: float = 1e-12          # relative comparison of two computed values
    abs_tol: float = 1e-14          # absolute floor for near-zero comparisons

    # --- root finding ---
    mach_abs_tol: float = 1e-10     # absolute xtol on Mach
    mach_rel_tol: float = 1e-12     # relative xtol on Mach
    angle_abs_tol: float = 1e-10    # radians
    area_abs_tol: float = 1e-10
    area_rel_tol: float = 1e-12
    residual_tol: float = 1e-10     # |f(x)| accepted as a converged root
    max_iter: int = 100

    # --- sonic / branch handling ---
    area_sonic_tol: float = 1e-11   # |A/A* - 1| treated as sonic
    sonic_tol: float = 1e-9         # |M - 1| treated as sonic
    sonic_margin: float = 1e-9      # bracket offset from M = 1
    near_sonic_mach: float = 1e-3   # window for the NEAR_SONIC warning
    fanno_tol: float = 1e-12        # |4fL*/D| treated as choked
    rayleigh_tol: float = 1e-12     # |T0/T0* - 1| treated as choked
    angle_tol: float = 1e-9         # radians; zero-deflection / theta_max merge
    nu_tol: float = 1e-12           # radians
    pressure_tol: float = 1e-9      # relative, on pb/p0 regime boundaries

    # --- domain limits ---
    mach_floor: float = 1e-6        # smallest Mach a bracket will reach
    mach_ceiling: float = 100.0     # largest Mach a bracket will reach
    gamma_min: float = 1.001
    gamma_max: float = 3.0
```

Why these numbers:

* `mach_abs_tol = 1e-10` sits comfortably above the 10⁻⁸ near-sonic resolution
  floor and far above the ~10⁻¹⁶ machine limit away from sonic, so it is
  achievable everywhere and never the binding constraint.
* `rel_tol = 1e-12` is roughly 4500 × machine epsilon — loose enough that a
  legitimately different evaluation order does not fail a comparison, tight
  enough to catch a real formula error.
* `sonic_margin = 1e-9` keeps a bracket end 10⁻⁹ away from M = 1, where by §4 the
  area ratio differs from 1 by ~8 × 10⁻¹⁹ — below machine epsilon. That is *fine*
  because the sonic-tolerance branch has already caught anything that close; the
  margin exists only to keep the bracket open, not to resolve anything.
* `mach_floor = 1e-6`: at M = 10⁻⁶, A/A* ≈ 5.8 × 10⁵ and the flow is
  indistinguishable from stagnant. Lower is arithmetic, not physics.
* `pressure_tol = 1e-9` relative on the regime boundaries: the criticals are
  computed to ~10⁻¹⁵, so 10⁻⁹ makes the boundary regimes (`SHOCK_AT_EXIT`,
  `IDEALLY_EXPANDED`, `CHOKED_SUBSONIC_EXIT`) reachable in practice by a user
  typing a rounded number, without swallowing a genuinely different case.

`ToleranceSet` is frozen and passed explicitly, so a study can be re-run at
tighter tolerances without a global switch and without breaking determinism
(`01` §9).

---

## 6. Extreme-input policy

No `nan`, no `inf`, no silent overflow escapes a public function (task §79).

| Input | Behaviour |
| --- | --- |
| M = 0 | valid for the ratios (all → 1); `area_ratio` raises `DomainError` (genuinely infinite); ν and μ raise `SubsonicExpansionError` |
| M → 0⁺ | valid; A/A* grows as 1/M and is returned as a large finite number until `mach_floor` |
| M = 1 exactly | every relation must return its exact sonic value; no branch may divide by (M − 1) or by √(M²−1) without guarding |
| M large | valid to `mach_ceiling = 100`; above that, `DomainError` with a message stating that the perfect-gas model is not meaningful there, rather than an overflow |
| M < 0 | `DomainError`. **Never** taken as \|M\| and never clamped to 0 |
| M = nan / inf | `DomainError`, checked first, before any arithmetic |
| γ ≤ 1 | `InvalidGammaError` |
| γ → 1⁺ | permitted down to 1.001; a limit test at γ = 1.001, M = 5 must produce finite values (`03` §2.2) |
| γ outside [1.05, 1.9] | computed, with an `EXTRAPOLATED_GAMMA` warning |
| p/p₀ → 0 | valid; M grows; returns a large finite Mach until the ceiling |
| p/p₀ = 0 | `DomainError` — the implied Mach is infinite |
| p/p₀ > 1 | `DomainError` — a static pressure above stagnation is not a flow state |
| A/A* < 1 | `AreaRatioError` — **never** clamped to 1 |
| Negative p, T, ρ, A | `DomainError` at the state constructor, before any relation sees them |
| p_b/p₀ ≥ 1 | `InputError` from the nozzle: no forward flow |

**Input validation happens once, at the public boundary**, and internal helpers
assume validated input. That keeps the hot vectorised paths clean while making
the guarantee total from outside.

---

## 7. Complete domain table

Every public relation, its domain, and the exception raised outside it.

| Relation | Domain | Outside → |
| --- | --- | --- |
| `PerfectGas(gamma, R)` | 1.001 ≤ γ ≤ 3.0; R > 0 or None | `InvalidGammaError` / `InvalidGasConstantError` |
| `isentropic.temperature_ratio` | M ≥ 0 | `DomainError` |
| `isentropic.pressure_ratio` | M ≥ 0 | `DomainError` |
| `isentropic.density_ratio` | M ≥ 0 | `DomainError` |
| `isentropic.area_ratio` | M > 0 | `DomainError` (M = 0 → infinite) |
| `isentropic.*_ratio_star` | M ≥ 0 | `DomainError` |
| `isentropic.mach_angle` | M ≥ 1 | `DomainError` |
| `isentropic.mach_from_pressure_ratio` | 0 < p/p₀ ≤ 1 | `DomainError` |
| `isentropic.mach_from_temperature_ratio` | 0 < T/T₀ ≤ 1 | `DomainError` |
| `isentropic.mach_from_density_ratio` | 0 < ρ/ρ₀ ≤ 1 | `DomainError` |
| `isentropic.mach_from_area_ratio` | A/A* ≥ 1; branch required | `AreaRatioError` / `ValueError` |
| `mass_flow.mass_flow_parameter` | M ≥ 0 | `DomainError` |
| `mass_flow.mass_flow` | M ≥ 0, A > 0, p₀ > 0, T₀ > 0, R present | `DomainError` / `MissingGasConstantError` |
| `normal_shock.*` | M₁ ≥ 1 | `SubsonicShockError` |
| `oblique_shock.theta_from_beta` | M₁ > 1, μ ≤ β ≤ π/2 | `SubsonicShockError` / `DomainError` |
| `oblique_shock.beta_from_theta` | M₁ > 1, 0 ≤ θ ≤ θ_max | `SubsonicShockError` / `NO_SOLUTION` |
| `oblique_shock.theta_max`, `beta_sonic` | M₁ > 1 | `SubsonicShockError` |
| `prandtl_meyer.nu` | M ≥ 1 | `SubsonicExpansionError` |
| `prandtl_meyer.mach_from_nu` | 0 ≤ ν < ν_max | `DomainError` / `NO_SOLUTION` |
| `prandtl_meyer.expand` | M₁ ≥ 1, Δθ ≥ 0, ν₁ + Δθ < ν_max | `SubsonicExpansionError` / `NO_SOLUTION` |
| `fanno.*` (forward) | M > 0 | `DomainError` |
| `fanno.mach_from_friction_parameter` | L ≥ 0; supersonic branch also L < L_∞ | `DomainError` / `NO_SOLUTION` |
| `rayleigh.*` (forward) | M > 0 | `DomainError` |
| `rayleigh.mach_from_stagnation_temperature_ratio` | 0 < r ≤ 1; supersonic also r ≥ (γ²−1)/γ² | `DomainError` / `NO_SOLUTION` |
| `nozzle.classify` | Ae/A* ≥ 1, 0 < p_b/p₀ < 1 | `GeometryError` / `InputError` |
| `nozzle.shock_area_ratio` | second < p_b/p₀ < first | `InputError` (wrong regime) |
| `nozzle.solve` | valid `AreaDistribution` with one interior minimum | `GeometryError` |

---

## 8. No silent clamping (task §81)

Stated as a rule with teeth:

* `mach = -2` → `DomainError`, never 0, never 2.
* `A/A* = 0.8` → `AreaRatioError`, never 1.
* `gamma = 0.9` → `InvalidGammaError`, never 1.4.
* `p/p0 = 1.2` → `DomainError`, never 1.
* A vectorised call with **any** invalid element raises for the whole array,
  naming the first offending index. It does not return `nan` for that element:
  a `nan` in a plot series is a silent hole, and the caller cannot tell it from
  a rendering bug.

The UI may prevent such inputs (`07` §3), but the physics layer stays safe
independently, because it is also called from notebooks, scripts, sweeps and
future optimisers that have no UI validation in front of them.

---

## 9. Scalar and array API policy (task §75)

**Decision: Tier-1 relations accept scalar or array and mirror the input type.
Tier-2 solvers are scalar-only, with an explicit `*_array` variant where a
vectorised inverse is genuinely useful.**

Rules:

| | Tier 1 (algebraic) | Tier 2 (`Solution`) |
| --- | --- | --- |
| Input | `float`, list, tuple, or `np.ndarray` | `float` only |
| Output | `float` for scalar input; `np.ndarray` for array input | `Solution[...]` |
| Broadcasting | standard NumPy against `gas` scalars | n/a |
| Validation | vectorised; raises on the first invalid element with its index | scalar |

Why not wrap arrays in `Solution` too: a 2000-element sweep would need either
2000 `Solution` objects (absurd) or one `Solution` whose diagnostics cannot say
which element they refer to (useless). `SweepResult` (`02` §6) is the array-level
answer, carrying whole-sweep diagnostics.

Why the explicit `*_array` variants (`mach_from_area_ratio_array`,
`mach_from_nu_array`) rather than overloading: they are the *only* Tier-2
functions where a vector inverse is a real use case (a nozzle station sweep, a
ν-fan sweep). Making them separate names keeps the return type honest — array in,
array out, raising on failure rather than returning a `Solution` — and avoids
the surprise polymorphism task §75 warns about.

Implementation note for the array inverses: they are a Python-level loop over
Brent, not a vectorised Newton. At a few thousand points that is a few
milliseconds — acceptable, measured, and far safer than a vectorised iteration
whose convergence differs element by element. If profiling later shows it
matters, the fix is a monotone-interpolation seed followed by a fixed small
number of Newton polish steps, with the bracketed method retained as the
fallback — and that change must not alter results beyond `mach_abs_tol`.

---

## 10. Determinism, precision and performance

**Determinism.** Brent's iteration is deterministic given (f, bracket,
tolerances). No randomness, no time-dependence, no ordering dependence. Same
inputs and same `ToleranceSet` → identical bits.

**Precision.** `float64` throughout. Justified in ADR-11 and quantified in §4:
the binding limit near sonic is algebraic conditioning, not representation, so
extended precision would buy a factor of ~10⁸ in δ to gain 10⁴ in M — a poor
trade for a large dependency. Away from sonic, `float64` delivers ~14 significant
figures, which exceeds every reference value in `03` §11 and every engineering
requirement by many orders.

**Performance targets** (qualitative, per task §93):

| Operation | Budget | Rationale |
| --- | --- | --- |
| One Tier-1 scalar relation | < 5 µs | pure arithmetic |
| One bracketed inverse | < 100 µs | ~10 Brent iterations |
| 2000-point vectorised sweep, one quantity | < 5 ms | one NumPy expression |
| 2000-point array inverse | < 200 ms | Python loop over Brent |
| Full nozzle solve, 400 stations, with a shock | < 50 ms | two array inversions plus one outer root |

These are budgets to *measure against*, not optimisation targets to design for.
The order of preference is: correct formula → stable formula → NumPy
vectorisation → only then micro-optimisation. No caching of cheap relations
(task §92); caching is reserved for genuinely expensive future operations such
as a CEA equilibrium call, where it will be explicit and keyed on the full input
tuple.

---

## 11. Numerical conditioning checklist

Places where the naive expression loses precision, and what to write instead.

| Situation | Naive | Use instead |
| --- | --- | --- |
| p/p₀ → 1 in the Mach inverse | `(p0/p)**((γ−1)/γ) − 1` | `expm1(((γ−1)/γ) * log(p0/p))` |
| M → 0 in φ − 1 | `φ − 1` | `(γ−1)/2 * M²` directly |
| A/A* near 1 | inverting numerically | the sonic-tolerance branch (§4) |
| Normal shock as M₁ → 1 | `p₂/p₁ − 1` cancelling | `2γ/(γ+1) * (M₁²−1)`, already in that form |
| ν near M = 1 | `atan(√(M²−1))` with M² − 1 cancelling | `√((M−1)(M+1))` for the inner term |
| Oblique shock near θ_max | either bracket | the merged-root branch plus `NEAR_THETA_MAX` |
| Fanno as M → 1 | `(1−M²)/(γM²)` and the log both → 0 | keep as written; the two terms cancel *correctly* to ε² — but assert the result is ≥ 0 and clip exact zeros at the sonic tolerance |
| Very large area ratio | `M^((γ+1)/(γ−1))` overflow check | bracket ceiling at `mach_ceiling`, checked before evaluation |
| ρ from p and T | `p/(R*T)` with T → 0 | guarded by the T > 0 domain check |

Each row is a test in `05` §11.
