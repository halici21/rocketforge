# Compressible Flow — Numerical Limits in float64

What the subsystem can and cannot resolve, and what it promises when it cannot.
Every figure here was measured, not estimated from theory alone.

The theme is one property of the equations, not a defect in the code: **most of
these relations are flat at the sonic point**, so inverting them near M = 1
loses roughly half the available digits. `04` section 4 derives the
coefficients; this document records the practical consequences.

---

## 1. The conditioning of each relation near sonic

Writing M = 1 + eps:

| Relation | Behaviour | Coefficient at gamma = 1.4 |
| --- | --- | --- |
| `A/A* - 1` | quadratic in eps | 0.8333333 |
| `4 f_F L*/D` | quadratic in eps | 1.1904762 |
| `1 - T0/T0*` (Rayleigh) | quadratic in eps | 0.6944444 |
| `nu` | eps^(3/2) | 0.7856742 |

A quadratic relation inverted in double precision resolves a Mach number to
about `sqrt(eps_machine)` — roughly 1e-8 in the best case, and in practice
1e-6 to 1e-7 once the relation's own coefficient is included.

## 2. What that means, module by module

### Area-Mach inverse

* **Near sonic.** `|A/A* - 1| <= area_sonic_tol` (1e-11) returns exactly M = 1
  with `SONIC_EXACT`, because inside that window returning 1 is *more* accurate
  than any root finder could be. That window corresponds to |M - 1| ~ 3.5e-6.
* **Round trip.** M -> A/A* -> M reproduces M to about 1e-9 away from sonic and
  about 1e-6 within 5% of it. Both are asserted in the cross-module suite.
* **Large area ratios.** The residual runs the other way as well: at
  A/A* = 50 the subsonic root sits at M = 0.012, where dA/dM is enormous, so a
  Mach number converged to 1e-10 leaves the area ratio good to about 1e-8.

### Prandtl-Meyer inverse

nu is eps^(3/2) near sonic — the *best* conditioned of the four, but still
sublinear. The inverse reproduces M to about 1e-5 at M = 1.001 and 1e-9 by
M = 1.5.

### Oblique shock near theta_max

The two roots merge at theta_max. Within `near_theta_max` (1% of theta_max)
they are poorly separated and the result carries `NEAR_THETA_MAX`. The
solution is still returned; the diagnostic is an honesty flag about resolution,
not an error.

### Weak oblique shocks near M1 sin(beta) = 1

The stagnation-pressure loss across a very weak shock is third order in
(Mn1 - 1), so `p02/p01` is 1 to within round-off long before the shock is
geometrically negligible. RocketForge reports the computed value; it does not
pretend to resolve a loss below 1e-16.

### Fanno near sonic

`4 f_F L*/D` is quadratic at M = 1 and reaches exactly 0 there. Two
consequences: a value below `fanno_tol` (1e-12) returns M = 1 exactly, and a
**log axis cannot be applied** to that column — the interface says
"not applied" rather than silently drawing a linear one.

### Rayleigh near sonic

`T0/T0*` is quadratic at M = 1 with maximum 1. The inverse resolves M to about
1e-5 at `T0/T0* = 0.9999`. The supersonic branch has a floor of
(gamma^2 - 1)/gamma^2 = 0.4897959184 at gamma = 1.4, below which no supersonic
solution exists; the request is refused with `RAYLEIGH_LIMIT`.

### Nozzle regime boundaries

The three criticals are computed to about 1e-15. `pressure_tol` is 1e-9,
applied **relatively** to each threshold, which makes the three measure-zero
regimes reachable by a user typing a rounded number without swallowing a
genuinely different operating point.

A back pressure assembled from four-significant-figure published values misses
an exact threshold by roughly 1e-4 — far outside that window, and correctly so.
The interface's preset buttons exist for this reason: they set the back
pressure to the *computed* threshold, which lands exactly.

### Nozzle shock near the throat

As pb approaches the first critical the shock area ratio approaches 1, where
the supersonic area-Mach inversion is at its flattest. Measured at
gamma = 1.4, Ae/At = 2:

```
    pb offset below first critical     As/At        M1          p02/p01
        1e-3                           1.0072       1.0952      0.99907
        1e-4                           1.0015       1.0428      0.99991
        1e-5                           1.0003       1.0196      0.99999
        1e-6                           1.0001       1.0090      1.00000
```

The shock strength goes to zero smoothly. No finite shock is claimed at the
onset itself: at exactly the first critical the module returns
`NO_INTERNAL_SHOCK`, because the supersonic pocket has zero extent.

### Nozzle shock near the exit

Approaching the second critical from above, As/At -> Ae/At and M1 -> Me_sup to
about 1e-6. At the threshold itself the shock-at-exit path is taken exactly,
with no root solve, and the result is `normal_shock.solve(Me_sup)` verbatim.

## 3. What is promised, and what is not

**Promised.**

* No NaN and no infinity escapes a public function. A non-finite input either
  raises a domain error or returns `no_solution`.
* No silent clamping of a physical quantity into range.
* Determinism: the same float64 inputs give the same result, every time,
  independent of batch size, sampling resolution or cache state.
* A sonic window that is *documented* rather than discovered, with
  `SONIC_EXACT` when it is used.

**Not promised.**

* Mach numbers resolved below about 1e-6 near M = 1 from an area ratio, a
  friction length or a Rayleigh stagnation-temperature ratio.
* Separation of the two oblique roots within 1% of theta_max.
* Stagnation-pressure losses below double-precision round-off for vanishingly
  weak shocks.
* Distinguishing back pressures closer than `pressure_tol` times a threshold.

## 4. Deliberately not used in production

`Decimal`, `Fraction` and `mpmath` appear **only** in test oracles and in the
scripts that generated reference datasets. Introducing arbitrary precision into
the runtime to paper over float64 conditioning would hide the limits above
rather than state them. SciPy is likewise a development-only cross-validation
oracle, and its single test skips when it is absent.
