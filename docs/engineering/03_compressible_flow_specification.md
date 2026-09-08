# 03 — Compressible Flow Module Specification

**Implementation-ready specification. No production code in this phase.**

Target module: `rocketforge/physics/compressible/`. Signatures are catalogued in
`02` §10–11; numerical methods, tolerances and brackets in `04`; tests in `05`.

---

## 1. Scope, model and conventions

### 1.1 The v1 physical model

| Property | v1 |
| --- | --- |
| Steadiness | steady |
| Dimensionality | one-dimensional, or quasi-one-dimensional for the nozzle |
| Gas | calorically perfect: γ constant, R constant, cp and cv constant |
| Equation of state | ideal, p = ρRT |
| Body forces | none |
| Work exchange | none (except where a relation says otherwise) |
| Chemistry | none. No dissociation, no finite rate, no variable γ |

Variable-γ chemistry is explicitly **not** admitted here (ADR-14). It arrives as
a separate model namespace with its own validation.

### 1.2 Notation

| Symbol | Meaning | Unit |
| --- | --- | --- |
| M | Mach number | – |
| γ | ratio of specific heats | – |
| R | specific gas constant | J/(kg·K) |
| p, T, ρ | static pressure, temperature, density | Pa, K, kg/m³ |
| p₀, T₀, ρ₀ | stagnation (total) properties | Pa, K, kg/m³ |
| p\*, T\*, ρ\* | properties at the sonic reference state of the process concerned | Pa, K, kg/m³ |
| A | cross-sectional area | m² |
| A\* | area at which M = 1 for the same mass flow and stagnation state | m² |
| a | speed of sound | m/s |
| V | velocity | m/s |
| ṁ | mass flow | kg/s |
| μ | Mach angle | rad |
| ν | Prandtl–Meyer angle | rad |
| θ | flow deflection angle | rad |
| β | oblique shock wave angle | rad |
| f | **Fanning** friction factor (see §8.2) | – |
| D | hydraulic diameter | m |
| L\* | duct length from the station to sonic choking | m |
| p_b | back pressure imposed on a nozzle exit | Pa |

Subscripts 1 and 2 mean upstream and downstream of a discontinuity; subscript e
means the nozzle exit plane; subscript s means the internal shock station.

**A recurring group.** Every isentropic relation is a power of

$$
\phi(M) \;=\; 1 + \frac{\gamma-1}{2}M^{2} \;=\; \frac{T_0}{T}
$$

Implementations compute `phi` once per call and raise it to the required powers,
which is both faster and better conditioned than repeating the bracket.

### 1.3 Convention decisions, fixed here

Where sources differ, RocketForge picks one and states it:

1. **Fanno friction parameter** is `4 f L*/D` with the **Fanning** factor f.
   See §8.2. Darcy is available only through explicit conversion helpers.
2. **Angles are radians** everywhere in the module (`01` §8).
3. **The sonic reference state is per-process.** The isentropic `A/A*`, the
   Fanno `p/p*` and the Rayleigh `p/p*` refer to three *different* sonic states,
   because the process that reaches them differs. Coincidences between them are
   listed in §8.4 and §9.4 and are used deliberately, never assumed.
4. **Positive θ is a turn into the flow** for shocks (compression) and a turn
   away from the flow for Prandtl–Meyer expansion; the two modules use separate
   function names (`expand`, `compress`) rather than a sign convention, because a
   sign convention here is a bug waiting to happen.
5. **Stagnation temperature is unchanged across an adiabatic shock**, exactly;
   `NormalShockResult.stagnation_temperature_ratio` is a literal `1.0`, not a
   computed value that could drift.

### 1.4 Sources and citation precision

Primary references for this specification:

* **J. D. Anderson, *Modern Compressible Flow: With Historical Perspective***,
  3rd ed. — isentropic relations and quasi-1D flow (ch. 3, 5), normal shocks
  (ch. 3), oblique shocks and expansion waves (ch. 4), Fanno/Rayleigh (ch. 3
  appendix material and the duct-flow treatment).
* **Ames Research Staff, *Equations, Tables, and Charts for Compressible
  Flow*, NACA Report 1135 (1953)** — the canonical equation set and tables;
  US Government work, freely reproducible, and the recommended cross-check
  source for the reference values in §11.
* **A. H. Shapiro, *The Dynamics and Thermodynamics of Compressible Fluid
  Flow*, Vol. I** — Fanno and Rayleigh line development, the friction-factor
  conventions, and the generalised one-dimensional treatment.
* **H. W. Liepmann and A. Roshko, *Elements of Gasdynamics*** — shock and
  expansion-wave physical interpretation.
* **G. P. Sutton and O. Biblarz, *Rocket Propulsion Elements*, 9th ed.** —
  nozzle operating regimes, choked mass flow in rocket form (ch. 3), and the
  boundary to rocket-specific performance which this module does **not** cross.
* **NASA Glenn Research Center, *Beginner's Guide to Aeronautics*** — the
  interactive compressible-flow relations, useful for informal cross-checks only.

**Citation precision, stated plainly.** Citations here are at chapter/report
level. Exact page and equation numbers vary between editions and printings and
are deliberately **not** invented: the implementer must fill in the precise
equation number from the physical edition on the shelf when writing each
module's docstring, and `05` §5 makes that a checklist item. The numeric values
in §11 were produced by evaluating the equations printed in this document at
`float64` — they are internally consistent by construction, and `05` §7 requires
an independent cross-check against NACA 1135 tables before any module is
accepted.

### 1.5 Module organisation

The flat layout of `02` §10 is recommended over one package per relation family:
nine modules, one concern each, no `__init__` re-export maze. Ownership:

| Module | Owns |
| --- | --- |
| `gas.py` | `PerfectGas` validation, speed of sound, cp/cv |
| `isentropic.py` | all γ-and-M ratios, area-Mach forward and inverse, mach angle |
| `mass_flow.py` | mass-flow parameter, choking, mass flux |
| `normal_shock.py` | all normal-shock jumps |
| `oblique_shock.py` | θ-β-M, θ_max, β_sonic, the wave geometry — *jumps come from `normal_shock`* |
| `prandtl_meyer.py` | ν, ν⁻¹, expansion/compression turns — *ratios come from `isentropic`* |
| `fanno.py` | adiabatic constant-area friction relations |
| `rayleigh.py` | frictionless constant-area heating relations |
| `nozzle.py` | quasi-1D C-D nozzle regimes and distributed solution |

---

## 2. Gas model

### 2.1 Relations

$$
c_p = \frac{\gamma R}{\gamma - 1}, \qquad
c_v = \frac{R}{\gamma - 1}, \qquad
a = \sqrt{\gamma R T}
$$

### 2.2 Domain

| Quantity | Rule | Behaviour outside |
| --- | --- | --- |
| γ | `gamma > 1` mathematically required | `InvalidGammaError` |
| γ | hard limits `1.001 <= gamma <= 3.0` | `InvalidGammaError` |
| γ | advisory band `1.05 <= gamma <= 1.9` | `EXTRAPOLATED_GAMMA` warning |
| R | `gas_constant > 0` when supplied | `InvalidGasConstantError` |
| R | `None` permitted | dimensional calls raise `MissingGasConstantError` |

**Why 1.001 and not "any γ > 1".** Several relations carry exponents
`γ/(γ−1)`, `1/(γ−1)` and `(γ+1)/(2(γ−1))`. At γ = 1.001 those are 1001, 1000 and
1000.5 — large but finite in `float64` for the Mach range of interest. Below
about γ = 1.0001 the exponent reaches 10⁴ and `φ^10⁴` overflows for modest Mach
numbers, producing `inf` where the physics is anyway meaningless (a calorically
perfect gas with γ → 1 has infinite specific heat). The limit is therefore where
the arithmetic stops being trustworthy, not an arbitrary round number, and the
advisory band is where the *model* stops being trustworthy. γ = 1.001 with
M = 5 is checked in the limit tests (`05` §11).

The upper bound 3.0 is generous: the monatomic ideal value is 5/3 ≈ 1.667, and
no physical gas exceeds it, but a user exploring the mathematics is not stopped.

---

## 3. Isentropic relations

**Assumptions:** steady, adiabatic, reversible, no work, calorically perfect gas.
**Domain:** M ≥ 0, γ > 1. A/A* additionally requires M > 0.

### 3.1 Forward relations

$$
\frac{T_0}{T} = 1 + \frac{\gamma-1}{2}M^2 \;=\; \phi
$$

$$
\frac{p_0}{p} = \phi^{\frac{\gamma}{\gamma-1}}, \qquad
\frac{\rho_0}{\rho} = \phi^{\frac{1}{\gamma-1}}
$$

The module returns the **static-over-stagnation** form (`T/T0`, `p/p0`,
`rho/rho0`), because those are bounded on (0, 1] and therefore numerically
better behaved and directly plottable; the reciprocal is the caller's business.

Sonic-reference (starred) forms, obtained by evaluating φ at M = 1:

$$
\frac{T}{T^{*}} = \frac{\gamma+1}{2 + (\gamma-1)M^{2}}, \qquad
\frac{p}{p^{*}} = \left[\frac{\gamma+1}{2+(\gamma-1)M^{2}}\right]^{\frac{\gamma}{\gamma-1}}, \qquad
\frac{\rho}{\rho^{*}} = \left[\frac{\gamma+1}{2+(\gamma-1)M^{2}}\right]^{\frac{1}{\gamma-1}}
$$

Area–Mach relation:

$$
\frac{A}{A^{*}} = \frac{1}{M}\left[\frac{2}{\gamma+1}\left(1+\frac{\gamma-1}{2}M^{2}\right)\right]^{\frac{\gamma+1}{2(\gamma-1)}}
$$

Mach angle (M ≥ 1): μ = arcsin(1/M).

Speed of sound and velocity, when the state is dimensional:

$$
a = \sqrt{\gamma R T}, \qquad V = M a
$$

### 3.2 Limiting behaviour

| Limit | T/T₀ | p/p₀ | ρ/ρ₀ | A/A* |
| --- | --- | --- | --- | --- |
| M → 0 | 1 | 1 | 1 | → ∞ |
| M = 1 | 2/(γ+1) | (2/(γ+1))^{γ/(γ−1)} | (2/(γ+1))^{1/(γ−1)} | 1 (exact minimum) |
| M → ∞ | → 0 like M⁻² | → 0 like M^{−2γ/(γ−1)} | → 0 like M^{−2/(γ−1)} | → ∞ like M^{(γ+1)/(γ−1)} |

At M = 0 exactly, `area_ratio` returns `None` in `IsentropicRatios` and raises
`DomainError` from the bare function: A/A* is genuinely infinite, and returning
`inf` would silently propagate into a plot axis.

### 3.3 Inverse relations — analytic

Three of the four inverses are closed-form and must **not** be solved
numerically:

$$
M = \sqrt{\frac{2}{\gamma-1}\left[\left(\frac{p_0}{p}\right)^{\frac{\gamma-1}{\gamma}} - 1\right]}
\qquad
M = \sqrt{\frac{2}{\gamma-1}\left[\frac{T_0}{T} - 1\right]}
\qquad
M = \sqrt{\frac{2}{\gamma-1}\left[\left(\frac{\rho_0}{\rho}\right)^{\gamma-1} - 1\right]}
$$

Domains: `0 < p/p0 <= 1`, `0 < T/T0 <= 1`, `0 < rho/rho0 <= 1`. A ratio of
exactly 1 returns M = 0. A ratio above 1 or at/below 0 raises `DomainError` —
never clamped (task §81).

Numerical note: for p/p₀ very close to 1 the bracket `(p0/p)^((γ−1)/γ) − 1`
suffers cancellation. Use `expm1`/`log1p`:
`M = sqrt(2/(γ−1) · expm1(((γ−1)/γ)·log(p0/p)))`, which is accurate to full
precision as p/p₀ → 1⁻ where the naive form loses digits.

### 3.4 Inverse relation — area-Mach (§34, critical)

A/A*(M) is not invertible in closed form. It has a single minimum of exactly 1
at M = 1, decreasing on (0,1) and increasing on (1,∞). Therefore:

| Input | Required behaviour |
| --- | --- |
| `A/A* < 1 − area_sonic_tol` | `raise AreaRatioError`. **Not** clamped to 1 |
| `|A/A* − 1| <= area_sonic_tol` | return **M = 1 exactly** for either branch, `Status.OK`, diagnostic `SONIC_EXACT` |
| `A/A* > 1 + area_sonic_tol` | **two** solutions exist. Return the requested branch |
| branch omitted | **API forbids it.** `branch` is a required positional-or-keyword argument with no default |

The last row is the rule task §34 demands: the API never picks a branch on the
caller's behalf. `mach_from_area_ratio_both()` exists for callers who want both,
and returns the named-field `AreaMachSolutions`, not a tuple whose order must be
remembered.

Solution method, brackets and the near-sonic conditioning limit: `04` §3.1 and
§4. Pseudocode: §12.1.

---

## 4. Mass flow and choking

**Assumptions:** as §3, plus one-dimensional flow through a known area.

### 4.1 Relations

Dimensionless mass-flow parameter (the form the module owns, because it is
γ-and-M only):

$$
\mathrm{MFP}(M,\gamma) \;=\; \frac{\dot m \sqrt{R T_0}}{A\,p_0}
\;=\; \sqrt{\gamma}\; M \left(1+\frac{\gamma-1}{2}M^{2}\right)^{-\frac{\gamma+1}{2(\gamma-1)}}
$$

Dimensional mass flow:

$$
\dot m \;=\; \frac{p_0 A}{\sqrt{T_0}}\sqrt{\frac{\gamma}{R}}\;M\left(1+\frac{\gamma-1}{2}M^{2}\right)^{-\frac{\gamma+1}{2(\gamma-1)}}
$$

Choked flow. MFP is maximised at M = 1, where it equals the vandenkerckhove
function

$$
\Gamma(\gamma) = \sqrt{\gamma}\left(\frac{2}{\gamma+1}\right)^{\frac{\gamma+1}{2(\gamma-1)}}
\qquad\Rightarrow\qquad
\dot m_{\max} = \frac{\Gamma(\gamma)\, p_0 A^{*}}{\sqrt{R T_0}}
$$

Critical pressure ratio:

$$
\frac{p^{*}}{p_0} = \left(\frac{2}{\gamma+1}\right)^{\frac{\gamma}{\gamma-1}}
$$

Mass flux ρV = ṁ/A follows from the same expression divided by A.

### 4.2 Proof obligation

That MFP is maximum at M = 1 is not asserted in code — it is a property test
(`05` §9): `argmax(MFP)` over a fine Mach grid must fall at M = 1, and
`dMFP/dM` must change sign there.

### 4.3 What "choked" means here (§38)

In this module, *choked* means exactly one thing: **the local Mach number at the
minimum-area station is 1, so the mass-flow parameter is at its maximum and
further reduction of downstream pressure cannot increase ṁ.**

* `is_choked(pressure_ratio, gas)` answers `p_receiver/p_0 <= p*/p_0` for a
  simple convergent passage, and nothing more.
* No discharge coefficient, no boundary-layer displacement, no two-phase
  behaviour, no injector or valve semantics enter this module. A discharge
  coefficient is a *device* correction and belongs to `engineering/injector` or
  `engineering/valve`, which multiply this module's ideal result.
* The nozzle module decides choking from its own regime analysis (§10.5) and
  reports the same fact; it does not redefine it.

---

## 5. Normal shock

**Assumptions:** steady, adiabatic, one-dimensional, no work, calorically
perfect gas, discontinuity of zero thickness.
**Domain:** M₁ ≥ 1, γ > 1.

### 5.1 Relations

$$
M_2^{2} = \frac{1 + \frac{\gamma-1}{2}M_1^{2}}{\gamma M_1^{2} - \frac{\gamma-1}{2}}
$$

$$
\frac{p_2}{p_1} = 1 + \frac{2\gamma}{\gamma+1}\left(M_1^{2}-1\right)
\qquad
\frac{\rho_2}{\rho_1} = \frac{(\gamma+1)M_1^{2}}{2+(\gamma-1)M_1^{2}}
\qquad
\frac{T_2}{T_1} = \frac{p_2}{p_1}\cdot\frac{\rho_1}{\rho_2}
$$

$$
\frac{p_{0,2}}{p_{0,1}} =
\left[\frac{(\gamma+1)M_1^{2}}{2+(\gamma-1)M_1^{2}}\right]^{\frac{\gamma}{\gamma-1}}
\left[\frac{\gamma+1}{2\gamma M_1^{2}-(\gamma-1)}\right]^{\frac{1}{\gamma-1}}
$$

$$
\frac{T_{0,2}}{T_{0,1}} = 1 \quad\text{(exactly, adiabatic)}
\qquad
\frac{s_2-s_1}{R} = -\ln\!\frac{p_{0,2}}{p_{0,1}}
$$

$$
\frac{A_2^{*}}{A_1^{*}} = \frac{p_{0,1}}{p_{0,2}}
$$

The last relation is what makes the nozzle internal-shock algorithm work
(§10.6): a shock does not change ṁ or T₀, so the sonic area downstream grows in
exactly the proportion that p₀ falls.

`T2/T1` is computed as the ratio of the two other ratios rather than from an
independent closed form. That is deliberate: it guarantees
`p2/p1 = (ρ2/ρ1)(T2/T1)` to machine precision, so the returned state is
self-consistent under the ideal gas law, which a separately-coded formula would
satisfy only to round-off.

### 5.2 Domain behaviour (§40)

| Input | Behaviour |
| --- | --- |
| M₁ > 1 | normal solution |
| M₁ = 1 (within `sonic_tol`) | all ratios exactly 1, M₂ = 1, `Status.OK`, diagnostic `SONIC_EXACT`. This is the degenerate zero-strength shock and is physically correct |
| M₁ < 1 | **`raise SubsonicShockError`.** No silent extrapolation. The relations formally return values for M₁ < 1, but those describe an entropy-decreasing expansion shock, which violates the second law |

The M₁ < 1 case is the one every implementer is tempted to let through because
the algebra does not complain. `05` §12 has an explicit test.

### 5.3 Physical interpretation (metadata, feeds the UI later)

Across an adiabatic normal shock with M₁ > 1: M drops below 1; p, T, ρ all
increase; p₀ decreases (entropy rises); T₀ is unchanged; the shock is
irreversible and the loss grows steeply with M₁ (p₀₂/p₀₁ ≈ 0.72 at M₁ = 2 but
0.33 at M₁ = 3 and 0.06 at M₁ = 5 for γ = 1.4).

### 5.4 Plots (§42)

`M2`, `p2/p1`, `T2/T1`, `ρ2/ρ1`, `p02/p01` versus M₁ over [1, 5] by default, one
`Series` per γ in the case set. The steep p₀ loss is the curve the page exists to
show, so the default y-scale for `p02/p01` is linear on [0, 1] and the module
provides the data for a log option without deciding it.

---

## 6. Oblique shock

**Assumptions:** as §5, plus a straight, attached, two-dimensional planar wave
(a wedge, not a cone — conical flow is Taylor–Maccoll and is **not** in v1).
**Domain:** M₁ > 1, γ > 1, 0 ≤ θ < π/2.

### 6.1 The θ-β-M relation

$$
\tan\theta = 2\cot\beta\;\frac{M_1^{2}\sin^{2}\beta - 1}{M_1^{2}\left(\gamma+\cos 2\beta\right)+2}
$$

valid for μ = arcsin(1/M₁) ≤ β ≤ π/2. At β = μ the shock is a Mach wave (θ = 0);
at β = π/2 it is a normal shock (θ = 0). Between them θ rises to a maximum and
falls back — hence two β roots for every attainable θ.

### 6.2 v1 solution modes

| Mode | Status | Note |
| --- | --- | --- |
| given M₁, θ, γ, branch → β and the full downstream state | **v1** | the primary mode; drives the Oblique Shock page |
| given M₁, β, γ → θ and downstream state | **v1** | closed-form, no iteration; cheap and useful for the diagram |
| θ_max(M₁, γ) and β at θ_max | **v1** | closed form, §6.3 |
| β_sonic(M₁, γ) — the wave angle at which M₂ = 1 | **v1** | closed form, §6.4 |
| θ-β-M curve data for plotting | **v1** | §6.7 |
| given θ, β → M₁ | **FUTURE** | invertible in closed form for M₁², but of narrow use and easy to misuse; deferred rather than half-specified |
| conical (Taylor–Maccoll) shocks | **FUTURE** | different physics, different module |
| detached bow-shock shape | **not planned** | requires a numerical field solution |

### 6.3 θ_max — closed form (§44)

The maximum-deflection wave angle has an analytic solution; it does **not**
require a maximisation. Solving dθ/dβ = 0:

$$
\sin^{2}\beta_{\theta\max} = \frac{1}{\gamma M_1^{2}}\left[\frac{(\gamma+1)M_1^{2}}{4} - 1
+ \sqrt{(\gamma+1)\left(\frac{(\gamma+1)M_1^{4}}{16} + \frac{(\gamma-1)M_1^{2}}{2} + 1\right)}\;\right]
$$

then θ_max = θ(β_θmax, M₁, γ) from §6.1.

*Verification.* Evaluated against an independent golden-section maximisation of
θ(β) at M₁ = 1.5, 2, 3, 5, 10 (γ = 1.4): agreement to 7–8 significant figures
(e.g. M₁ = 2: closed form 64.66897983°, search 64.66897995°). The implementation
must keep the closed form as the answer and the search as a *test*, not the
reverse — the search is 400 iterations, the closed form is one square root.

### 6.4 β_sonic — closed form

The wave angle at which the downstream flow is exactly sonic:

$$
\sin^{2}\beta_{\text{sonic}} = \frac{1}{\gamma M_1^{2}}\left[\frac{(\gamma+1)M_1^{2}}{4} - \frac{3-\gamma}{4}
+ \sqrt{(\gamma+1)\left(\frac{(\gamma+1)M_1^{4}}{16} + \frac{(\gamma-3)M_1^{2}}{8} + \frac{\gamma+9}{16}\right)}\;\right]
$$

*Verification.* Substituting this β into the full solution chain gives
M₂ = 1.00000000 at M₁ = 1.5, 2, 3, 5, 10 (γ = 1.4).

Why it matters: β_sonic sits *just below* β at θ_max, so a narrow band of weak
solutions near θ_max already has subsonic downstream flow. The result carries
`downstream_supersonic` so the UI can say so rather than implying that "weak"
means "supersonic behind".

### 6.5 Branch policy (§45)

* `branch` is an explicit `ShockBranch` argument.
* Default is `ShockBranch.WEAK`, and when the default is used the solution
  carries an informational `BRANCH_ASSUMED` diagnostic naming it. A default is
  acceptable here (unlike area-Mach) because the weak branch is what physically
  occurs in essentially all external aerodynamic situations, and because the
  result object states which branch it is; the diagnostic keeps it honest.
* `ShockBranch.STRONG` returns the strong solution with an informational
  `STRONG_BRANCH_UNSTABLE` diagnostic: the strong shock is a valid solution of
  the equations, but is realised only when downstream conditions force it.
* `ShockBranch.BOTH` returns `ObliqueShockPair`.

### 6.6 Detachment (§44)

If θ > θ_max + `angle_tol`:

```
Solution(value=None,
         status=Status.NO_SOLUTION,
         diagnostics=[Diagnostic("DETACHED_SHOCK", ERROR,
             "No attached oblique shock exists: the requested deflection "
             "exceeds the maximum for this Mach number.",
             detail={"theta": theta, "theta_max": theta_max, "mach1": mach1})])
```

The result must **never** be a fabricated attached solution, and must never be
the θ_max solution silently substituted. If `|θ − θ_max| <= angle_tol` the two
roots have merged: return the single β = β_θmax solution with
`BRANCH_ASSUMED`-style diagnostic noting the branches coincide.

### 6.7 Downstream state — by reuse, not by restating (§46)

```
Mn1 = M1 * sin(beta)
(Mn2, p2/p1, rho2/rho1, T2/T1, p02/p01) = normal_shock.<relations>(Mn1, gas)
M2  = Mn2 / sin(beta - theta)
```

`oblique_shock.py` contains **no** pressure, temperature, density or stagnation
formula of its own. That is asserted by the duplication test (`05` §9), which
compares oblique results at (M₁, β) against `normal_shock` results at
`M₁ sin β` to machine precision.

### 6.8 θ-β-M diagram data

`theta_beta_curve(mach1, gas, n)` returns β on a grid clustered towards both
ends (where the curve turns sharply), the matching θ, plus the three markers
θ_max, β at θ_max, and β_sonic. It returns data only — no colours, no axes, no
Qt (task §72). The UI decides which curves to overlay for which Mach numbers.

---

## 7. Prandtl–Meyer expansion

**Assumptions:** steady, two-dimensional, isentropic, centred expansion around a
convex corner, calorically perfect gas.
**Domain:** M ≥ 1, γ > 1.

### 7.1 The Prandtl–Meyer function

$$
\nu(M) = \sqrt{\frac{\gamma+1}{\gamma-1}}\;\arctan\sqrt{\frac{\gamma-1}{\gamma+1}\left(M^{2}-1\right)}
\;-\;\arctan\sqrt{M^{2}-1}
$$

ν(1) = 0 exactly. ν is strictly increasing on M ≥ 1, with

$$
\frac{d\nu}{dM} = \frac{\sqrt{M^{2}-1}}{M\left(1+\frac{\gamma-1}{2}M^{2}\right)} \;\ge\; 0
$$

and the finite supremum

$$
\nu_{\max} = \frac{\pi}{2}\left(\sqrt{\frac{\gamma+1}{\gamma-1}} - 1\right)
$$

which is 130.4540768505° for γ = 1.4. This is the total turning available to
expand to M → ∞ and is a hard ceiling on the inverse.

### 7.2 Domain behaviour

| Input | Behaviour |
| --- | --- |
| M < 1 | `raise SubsonicExpansionError`. The expression is complex-valued there |
| M = 1 | ν = 0 exactly, μ = π/2 |
| ν requested ≥ ν_max | `Status.NO_SOLUTION`, diagnostic explaining that the turn exceeds the maximum for this γ |
| ν < 0 | `raise DomainError` |

### 7.3 Inverse

ν(M) is not invertible in closed form; solve numerically (`04` §3.2). The
inverse is *better* conditioned near M = 1 than the area-Mach inverse: from
§4 of `04`, ν ≈ [4√2 / (3(γ+1))]·(M−1)^{3/2}, so a relative error ε in ν gives
ε^{2/3} in (M−1) rather than ε^{1/2}.

### 7.4 Expansion turn (§49)

Given M₁ ≥ 1, a turn angle Δθ > 0, and γ:

```
nu1 = nu(M1)
nu2 = nu1 + turn_angle            # expansion: nu increases
if nu2 >= nu_max:  -> NO_SOLUTION ("turn exceeds maximum expansion")
M2  = mach_from_nu(nu2)
```

Downstream ratios come **from the isentropic module**, because the expansion is
isentropic and p₀, T₀ are therefore unchanged:

$$
\frac{p_2}{p_1} = \frac{p(M_2)/p_0}{p(M_1)/p_0},\qquad
\frac{T_2}{T_1} = \frac{T(M_2)/T_0}{T(M_1)/T_0},\qquad
\frac{\rho_2}{\rho_1} = \frac{\rho(M_2)/\rho_0}{\rho(M_1)/\rho_0}
$$

No expansion-specific pressure formula is written (task §49, §138).

The fan geometry: the leading Mach line lies at μ₁ = arcsin(1/M₁) from the
upstream flow direction, the trailing line at μ₂ = arcsin(1/M₂) from the
downstream direction, and the total fan angle is
`mach_angle1 − mach_angle2 + turn_angle`. This is returned as `fan_angle` for
the visualisation and is geometry, not new physics.

`compress()` is the same machinery with `nu2 = nu1 − turn_angle`, valid only for
an isentropic compression (ν₂ ≥ 0 required); it carries a diagnostic noting that
a real finite compression turn coalesces into a shock, and that the isentropic
result is an idealisation.

---

## 8. Fanno flow

**Assumptions:** steady, one-dimensional, **constant area**, adiabatic, wall
friction, no shaft work, calorically perfect gas.
**Domain:** M > 0, M ≠ ∞, γ > 1.

### 8.1 The sonic reference

The Fanno star state is the state the flow would reach at the end of a duct of
length L\* — reached *by friction*, not isentropically. It is a different state
from the isentropic A/A* reference, and mixing them is a known implementation
trap. See §8.4 for the two genuine coincidences.

### 8.2 Friction factor convention — FIXED (§52)

**RocketForge uses the Fanning friction factor f, and the duct parameter
`4 f L / D`.**

$$
f_{\text{Fanning}} = \frac{\tau_w}{\tfrac{1}{2}\rho V^{2}}
\qquad\qquad
f_{\text{Darcy}} = 4 f_{\text{Fanning}}
$$

Rules that make the convention impossible to get wrong in use:

1. The public function is named `friction_parameter` and its docstring states
   `4 f_Fanning L*/D` in the first line.
2. Conversion helpers `darcy_to_fanning` and `fanning_to_darcy` exist and are
   the only sanctioned way to move between conventions.
3. Any UI label showing a friction factor **must** name the convention
   ("Fanning f", "Darcy f_D"); the ambiguous bare "f" is banned in labels
   (`07` §6).
4. A reference test pins `4fL*/D` at M = 0.5, γ = 1.4 to **1.0690603127**. Under
   the Darcy reading the same duct would read 0.2672650782 — a factor of four,
   which is exactly the error this convention decision prevents, and the test
   catches it immediately.

### 8.3 Relations

With φ = 2 + (γ−1)M²:

$$
\frac{T}{T^{*}} = \frac{\gamma+1}{\varphi}, \qquad
\frac{p}{p^{*}} = \frac{1}{M}\sqrt{\frac{\gamma+1}{\varphi}}, \qquad
\frac{\rho}{\rho^{*}} = \frac{1}{M}\sqrt{\frac{\varphi}{\gamma+1}}, \qquad
\frac{V}{V^{*}} = M\sqrt{\frac{\gamma+1}{\varphi}}
$$

$$
\frac{p_0}{p_0^{*}} = \frac{1}{M}\left[\frac{\varphi}{\gamma+1}\right]^{\frac{\gamma+1}{2(\gamma-1)}}
$$

$$
\frac{4 f L^{*}}{D} = \frac{1-M^{2}}{\gamma M^{2}}
+ \frac{\gamma+1}{2\gamma}\ln\!\left[\frac{(\gamma+1)M^{2}}{\varphi}\right]
$$

T₀/T₀\* = 1 identically: the flow is adiabatic, so stagnation temperature is
constant along the duct.

### 8.4 The two genuine coincidences

Both are consequences of the flow being adiabatic with fixed mass flow, and both
should be *documented and tested*, not assumed by accident:

* `fanno.temperature_ratio(M) == isentropic.temperature_ratio_star(M)` exactly —
  both equal (γ+1)/(2+(γ−1)M²), because T₀ is constant in each case.
* `fanno.stagnation_pressure_ratio(M) == isentropic.area_ratio(M)` exactly —
  because p₀A\* is constant for a given ṁ and T₀, so p₀/p₀\* = A/A\*.

`p/p*`, `ρ/ρ*` and `V/V*` do **not** coincide with their isentropic
counterparts. `05` §9 tests both the equalities and the inequalities, so a
future refactor cannot quietly merge the two families.

### 8.5 Physical direction (§53)

Friction drives **both** branches towards M = 1:

* subsonic (M < 1): M increases, p falls, T falls, p₀ falls, V rises;
* supersonic (M > 1): M decreases, p rises, T rises, p₀ falls, V falls;
* p₀ always falls — friction is irreversible in both branches.

`4fL*/D` is the *remaining* duct length to choking, so it decreases monotonically
along the duct in both branches. It is 0 at M = 1 and:

* → ∞ as M → 0 (an infinitely long subsonic duct);
* → a finite limit as M → ∞:
  `−1/γ + (γ+1)/(2γ)·ln((γ+1)/(γ−1))` = **0.8215081165** for γ = 1.4.

That finite supersonic limit is a real physical statement — no supersonic Fanno
duct longer than that ratio can be run without a shock — and it is the natural
upper end of the supersonic bracket (`04` §3.4).

### 8.6 Inverse problems (§54)

| Problem | v1 | Method |
| --- | --- | --- |
| `M → 4fL*/D` | yes | closed form |
| `4fL*/D → M`, branch given | yes | bracketed root, `04` §3.4 |
| `M1 + 4fL/D of the actual duct → M2` | yes | subtract, then invert on the same branch |
| `M1, M2 → required 4fL/D` | yes | difference of the closed forms |
| `p2/p1 → M2` given M1 | FUTURE | expressible but rarely how a duct problem is posed |

The `M1 + duct → M2` case is where the branch awareness matters:

```
L_available  = duct_parameter                   # 4 f L / D of the real duct
L_max        = friction_parameter(M1)           # 4 f L*/D at the inlet
if L_available > L_max + tol:      -> FRICTION_CHOKED, NO_SOLUTION
if |L_available - L_max| <= tol:   -> M2 = 1 exactly, choked=True
else: M2 = mach_from_friction_parameter(L_max - L_available, branch=branch_of(M1))
```

A subsonic inlet stays subsonic and a supersonic inlet stays supersonic: **the
Fanno solution never crosses M = 1 within a continuous duct.** The over-length
case is a genuine engineering answer — the flow chokes and the upstream
condition must change — and is reported as `FRICTION_CHOKED`, never as a
silently truncated duct.

### 8.7 Plots (§55)

`T/T*`, `p/p*`, `ρ/ρ*`, `p0/p0*`, `4fL*/D` versus M. The subsonic and supersonic
branches must be delivered as **separate `Series`** rather than one array
containing M = 1, because `p/p*` and `4fL*/D` have very different scales on the
two sides and a single series invites a misleading autoscale. Suggested default
ranges: M ∈ [0.05, 1] and M ∈ [1, 5].

---

## 9. Rayleigh flow

**Assumptions:** steady, one-dimensional, **constant area**, frictionless, heat
exchange with the surroundings, no shaft work, calorically perfect gas.
**Domain:** M > 0, γ > 1.

### 9.1 Relations

$$
\frac{p}{p^{*}} = \frac{\gamma+1}{1+\gamma M^{2}}, \qquad
\frac{T}{T^{*}} = M^{2}\left(\frac{\gamma+1}{1+\gamma M^{2}}\right)^{2}, \qquad
\frac{\rho}{\rho^{*}} = \frac{1}{M^{2}}\cdot\frac{1+\gamma M^{2}}{\gamma+1}
$$

$$
\frac{T_0}{T_0^{*}} = \frac{(\gamma+1)M^{2}\left[2+(\gamma-1)M^{2}\right]}{\left(1+\gamma M^{2}\right)^{2}}
$$

$$
\frac{p_0}{p_0^{*}} = \frac{\gamma+1}{1+\gamma M^{2}}\left[\frac{2+(\gamma-1)M^{2}}{\gamma+1}\right]^{\frac{\gamma}{\gamma-1}}
$$

Heat added between two stations, when dimensional:

$$
q = c_p\left(T_{0,2}-T_{0,1}\right)
$$

### 9.2 The non-trivial extrema (§57 — "do not oversimplify")

Rayleigh flow is the one family in this module whose qualitative behaviour is
genuinely counter-intuitive, and the specification is explicit about it:

* **T₀/T₀\* has its maximum of exactly 1 at M = 1.** Heat addition therefore
  drives *both* branches towards M = 1, and the sonic state is the thermal
  choking limit.
* **T/T\* has its maximum at M = 1/√γ, not at M = 1.** The value there is
  (γ+1)²/(4γ), which is 1.0285714286 for γ = 1.4 (at M = 0.8451542547).
* Consequently, **between M = 1/√γ and M = 1 the static temperature falls while
  heat is being added.** This is correct, not a bug: in that band the flow is
  accelerating fast enough that the kinetic-energy rise exceeds the added heat.
  A test pins this behaviour (`05` §9) precisely because a future "tidy-up"
  might otherwise be tempted to make T/T\* monotone.
* As M → ∞, T₀/T₀\* → (γ² − 1)/γ², which is 0.4897959184 for γ = 1.4 — a finite
  limit, so a supersonic Rayleigh flow can only be *cooled* so far.
* p₀/p₀\* > 1 on both sides of sonic with a minimum of 1 at M = 1: heat addition
  always destroys stagnation pressure, in both branches. This is the Rayleigh
  loss and is worth surfacing in the UI interpretation panel.

### 9.3 Physical direction

| Branch | Heating | Cooling |
| --- | --- | --- |
| M < 1 | M → 1, p falls, p₀ falls, T rises then (above M = 1/√γ) falls | M → 0 |
| M > 1 | M → 1, p rises, p₀ falls, T rises | M → ∞ |

### 9.4 Coincidence with the isentropic family

None. Every Rayleigh starred ratio differs from its isentropic counterpart —
including T/T\*, which for Rayleigh is `M²[(γ+1)/(1+γM²)]²` and for the
isentropic/Fanno family is `(γ+1)/(2+(γ−1)M²)`. A test asserts they differ at
M = 0.5 and M = 2, guarding against a copy-paste between the two modules.

### 9.5 Inverse problems (§58)

| Problem | v1 | Rationale |
| --- | --- | --- |
| `M → all ratios` | yes | closed form |
| `T0/T0* → M`, branch given | **yes** | this *is* the heat-addition problem; without it the module cannot answer "how much can I heat this flow" |
| `M1 + T02/T01 → M2` | **yes** | the standard duct question; built on the above |
| `p/p* → M`, branch given | FUTURE | monotone and easy, but not how a Rayleigh problem is posed in practice |
| `T/T* → M` | **FUTURE, and flagged** | T/T\* is **not monotone** on the subsonic branch: it has two subsonic roots either side of M = 1/√γ. Any implementation must therefore expose a three-way branch, which is more UI complexity than the question earns in v1 |

The recommendation is one inverse pair in v1 (T₀ ratio, both branches) plus the
duct problem built on it. The T/T\* inverse is explicitly deferred **with its
reason recorded**, so a later implementer does not add it casually and pick a
root at random.

The heat-addition problem:

```
r1 = stagnation_temperature_ratio(M1)                # T01/T0*
r2 = r1 * (T02/T01)                                  # T02/T0*
if r2 > 1 + tol:  -> THERMALLY_CHOKED, NO_SOLUTION
if |r2 - 1| <= tol: -> M2 = 1 exactly, thermally_choked = True
else: M2 = mach_from_stagnation_temperature_ratio(r2, branch = branch_of(M1))
```

As with Fanno, the solution never crosses M = 1 inside a continuous duct.

### 9.6 Plots (§59)

`T/T*`, `T0/T0*`, `p/p*`, `p0/p0*` versus M, subsonic and supersonic as separate
series. The T/T\* curve **must** be sampled finely enough near M = 1/√γ to show
its maximum — a coarse grid hides the single most instructive feature of the
Rayleigh line. `mach_grid(..., cluster="sonic")` plus an explicit sample at
1/√γ is specified for this page.

---

## 10. Converging–diverging nozzle

The integrating module. It restates no relation: everything comes from
`isentropic`, `normal_shock` and `mass_flow`.

**Assumptions:** steady, quasi-one-dimensional, adiabatic, calorically perfect,
isentropic except across an infinitely thin normal shock, area varying slowly
enough that the flow is locally one-dimensional.

### 10.1 What this module is not

It is **fundamental gas dynamics**, not rocket nozzle design (ADR-15). Thrust,
Cf, c\*, Isp, contour generation, divergence loss, efficiency factors, film
cooling and wall heat transfer are **absent by design** and belong to
`engineering/nozzle/`, which will call this module.

### 10.2 Geometry contract (§61)

Input is an `AreaDistribution` (`02` §1.6): x and A(x) supplied to the solver.
The solver never generates a contour. Two access levels:

* **Dimensionless / analysis level** — `classify()`, `critical_pressure_ratios()`
  and `shock_area_ratio()` need only `Ae/A*` and `pb/p0`. This is what the
  frozen Nozzle Lab page can call today, since it exposes an area ratio and a
  back-pressure fraction.
* **Distributed level** — `solve()` needs the full A(x) and returns arrays.

Validation: strictly increasing x; strictly positive A; exactly one interior
minimum (otherwise `GeometryError`); at least three points; the throat must not
be the first or last station for a C-D solve.

### 10.3 Operating inputs (§62)

`NozzleOperating(stagnation_pressure, back_pressure, stagnation_temperature=None)`
plus a `PerfectGas`. T₀ and R are needed only for T, ρ, a, V and ṁ; without them
the solution is returned with those arrays as `None` and a diagnostic saying so,
rather than fabricated.

### 10.4 The three critical pressure ratios

All expressed as p_b/p₀ and computed from `Ae/A*` alone:

| Name | Definition | How computed |
| --- | --- | --- |
| **first critical** | highest back pressure at which the throat is exactly sonic; flow subsonic everywhere else | `isentropic.pressure_ratio(M_e_sub)` where `M_e_sub = mach_from_area_ratio(Ae/A*, SUBSONIC)` |
| **second critical** | normal shock standing exactly in the exit plane | `isentropic.pressure_ratio(M_e_sup) × normal_shock.pressure_ratio(M_e_sup)` |
| **third critical** | ideal (design) expansion, shock-free, p_e = p_b | `isentropic.pressure_ratio(M_e_sup)` where `M_e_sup = mach_from_area_ratio(Ae/A*, SUPERSONIC)` |

Ordering, always: `third < second < first < 1`.

Worked example, γ = 1.4, Ae/A\* = 2.0 — the numbers a reviewer can check by hand:

| | Value |
| --- | --- |
| M_e subsonic | 0.3059038342 |
| M_e supersonic | 2.1971981217 |
| first critical p_b/p₀ | 0.9371625024 |
| second critical p_b/p₀ | 0.5134007280 |
| third critical p_b/p₀ | 0.0939326457 |

### 10.5 Regime classification (§63, §64)

Given r = p_b/p₀ and the three criticals, with `pressure_tol` as the comparison
tolerance:

| Condition | Regime | Meaning |
| --- | --- | --- |
| `r >= 1` | `InputError` | back pressure at or above the stagnation pressure: no flow, or reversed flow. Not a regime |
| `first < r < 1` | `UNCHOKED_SUBSONIC` | venturi behaviour; throat subsonic; ṁ set by the pressure ratio |
| `\|r − first\| <= tol` | `CHOKED_SUBSONIC_EXIT` | choking onset: M = 1 at the throat, subsonic diverging section, shock-free |
| `second < r < first` | `INTERNAL_NORMAL_SHOCK` | choked; a normal shock stands in the diverging section; solve for its position (§10.6) |
| `\|r − second\| <= tol` | `SHOCK_AT_EXIT` | the shock has reached the exit plane |
| `third < r < second` | `OVEREXPANDED` | shock-free internally; the exit flow is supersonic with p_e < p_b; adjustment happens **outside** the nozzle |
| `\|r − third\| <= tol` | `IDEALLY_EXPANDED` | p_e = p_b |
| `r < third` | `UNDEREXPANDED` | p_e > p_b; expansion fans stand off the exit plane |

Notes that keep this from being "vague hard-coded rules":

* Every threshold is *computed* from the area ratio and γ. There is no
  hard-coded pressure number anywhere in the classifier.
* `CHOKING_ONSET` from the task's list is named `CHOKED_SUBSONIC_EXIT` here,
  because the same regime covers the whole (measure-zero) matched condition and
  reads correctly in a UI chip.
* Internally the flow is identical across `OVEREXPANDED`, `IDEALLY_EXPANDED` and
  `UNDEREXPANDED` — the same shock-free supersonic solution. The three differ
  only in what happens downstream of the exit plane, which this quasi-1D model
  does not compute. The regime is reported; the external wave pattern is not
  claimed.

### 10.6 Internal shock location (§65, §66) — algorithm

The physical chain, each step naming the module it comes from:

1. The throat is choked, so A₁\* = A_throat and ṁ is fixed.
2. Upstream of the shock the flow is isentropic on the supersonic branch:
   at area A_s, `M_s1 = isentropic.mach_from_area_ratio(A_s/A₁*, SUPERSONIC)`.
3. Across the shock: `normal_shock.solve(M_s1)` gives M_s2 and p₀₂/p₀₁.
4. Downstream the flow is again isentropic but with a **new sonic area**,
   `A₂* = A₁* · p₀₁/p₀₂` (§5.1). Since the duct area now exceeds A₂\* and the
   flow is subsonic, the branch is subsonic from here to the exit.
5. At the exit, `M_e = isentropic.mach_from_area_ratio(A_e/A₂*, SUBSONIC)`.
6. Exit static pressure: `p_e/p₀₁ = (p_e/p₀₂)·(p₀₂/p₀₁)`.
7. A steady solution requires `p_e = p_b`, so define the residual
   `F(A_s/A₁*) = p_e(A_s)/p₀₁ − p_b/p₀₁` and solve `F = 0`.

**Monotonicity — why this is well-posed.** Moving the shock downstream means it
sits at a higher area ratio, so M_s1 is larger, the shock is stronger, p₀₂/p₀₁ is
smaller, A₂\* is larger, A_e/A₂\* is smaller, M_e is larger and p_e is *lower*.
F is therefore strictly decreasing in A_s/A₁\* over (1, A_e/A₁\*], which makes a
bracketed root both unique and safe. The bracket end points evaluate exactly to
the first and second criticals, so `F(1⁺) > 0 > F(A_e/A*)` for any r strictly
between them — no bracket search is ever needed.

Verification example (γ = 1.4, Ae/A\* = 2.0, shock placed at A_s/A\* = 1.5):
M_s1 = 1.8541235267, M_s2 = 0.6048430465, p₀₂/p₀₁ = 0.7883594291,
A₂\*/A₁\* = 1.2684569539, M_e = 0.2358088692, and the back pressure that puts the
shock there is p_b/p₀ = 0.7584257377 — which duly lies between the second
(0.5134) and first (0.9372) criticals.

Pseudocode: §12.4. Root method and tolerances: `04` §3.7.

### 10.7 Distributed output (§67)

`NozzleSolution` returns, on a common grid, `x`, `area`, `mach`, `pressure`,
`temperature`, `density`, `speed_of_sound`, `velocity`, `stagnation_pressure`,
`stagnation_temperature`.

Construction rules:

* The output grid is the input `x` grid, **plus** the two duplicated shock
  stations when a shock exists (§10.8). No resampling, no smoothing: the caller
  chose the resolution and gets it back.
* `stagnation_temperature` is constant everywhere (adiabatic), including across
  the shock. It is filled with the input value, not recomputed per station.
* `stagnation_pressure` is constant at p₀₁ before the shock and constant at p₀₂
  after it — a single step. In shock-free regimes it is constant throughout.
* Branch selection per station: subsonic everywhere upstream of the throat;
  downstream of the throat, supersonic until the shock and subsonic after it;
  in `UNCHOKED_SUBSONIC`, subsonic throughout with the sonic reference derived
  from the *exit* condition rather than the throat (§10.10).
* The throat station is set to exactly M = 1 when the nozzle is choked, rather
  than inverted from an area ratio of 1 ± round-off, which is where a naive
  implementation produces `nan`.

### 10.8 Discontinuity representation (§68)

**Recommended: duplicate the shock station in the arrays.**

The shock is placed at x_s, and the output contains two consecutive samples with
`x[i] == x[i+1] == x_s`, the first carrying the pre-shock state and the second
the post-shock state. `NozzleSolution.shock_index` is `i`.

Why this over the alternatives:

* A structured `Discontinuity` object with two separate arrays forces every
  consumer — plot, table, export, test — to reassemble the profile, and the
  frozen `MockLineSeries`/`NozzleVisualization` consume flat point lists.
* Smoothing the jump is forbidden: it would be a false result and would hide the
  p₀ loss the page exists to display (task §68).
* Duplicated abscissae are drawn correctly as a vertical jump by any polyline
  renderer, including the existing QML canvas drawing, with no special case.

The cost is that a consumer computing dp/dx must skip the duplicated pair;
`shock_index` makes that a one-line guard, and the field is mandatory rather than
optional so it cannot be overlooked.

### 10.9 Model limitations — to be stated in the UI, not buried (§69, §70)

This model does **not** capture, and must never be presented as capturing:

* multidimensional flow, radial velocity components, or contour-shape effects;
* boundary layers, viscous losses, or displacement thickness;
* **flow separation** — see below;
* shock–boundary-layer interaction, lambda feet, or asymmetric separation;
* the external shock or expansion structure downstream of the exit plane;
* chemical non-equilibrium, frozen or equilibrium chemistry, or variable γ;
* heat transfer to the wall, film or regenerative cooling;
* transient start-up and shut-down (a real nozzle's most demanding moments).

**Separation, specifically.** v1 classifies `OVEREXPANDED` from `p_e < p_b`, and
that is *all* it does. It does not predict whether, or where, the flow separates
from the wall. Real overexpanded nozzles separate — and the classic engineering
criteria for it (Summerfield's rule of thumb, Schmucker, Kalt–Bendall and the
rest) are **empirical correlations**, not consequences of quasi-1D theory. They
belong in `engineering/nozzle/separation.py` when someone implements and
validates them against test data.

The module therefore emits `MODEL_LIMIT_SEPARATION` when the flow is
substantially overexpanded, with a message stating that real nozzles may
separate and that this model does not predict it. The trigger threshold is a
*presentation* choice, not a physical claim: p_e/p_b < 0.4 is suggested because
it is the region where separation is commonly observed, and the diagnostic
message says explicitly that the threshold is a rule of thumb for flagging, not
a prediction.

### 10.10 The unchoked case

When `r > first critical` the throat is not sonic, A\* is not the throat area,
and the whole solution is subsonic. Procedure:

1. `M_e = isentropic.mach_from_pressure_ratio(p_b/p0)` — the exit is matched
   directly to the back pressure because a subsonic exit can communicate with
   the downstream reservoir.
2. `A* = A_e / isentropic.area_ratio(M_e)` — a *virtual* sonic area, smaller than
   the throat, that is never physically reached.
3. Every station: `M(x) = mach_from_area_ratio(A(x)/A*, SUBSONIC)`.
4. `choked = False`, `mass_flow` computed from the actual throat Mach number
   rather than from Γ; diagnostic `NOT_CHOKED`.

Step 2 is the step implementations usually get wrong by continuing to use the
throat as A\*, which produces a nonsense throat Mach number of exactly 1 in a
regime where the throat is not sonic.

### 10.11 Perfect-gas limitation and the future path (§71)

Constant γ is appropriate for teaching, verification and preliminary analysis. It
is *not* adequate for real combustion products across a large expansion, where γ
falls significantly from chamber to exit and dissociation/recombination matters.

The future path, specified but not built:

```
ThermochemistryProvider (CEA / Cantera)
        -> ChamberGas (T0, gamma, R, composition)
        -> station-dependent gas properties along the expansion
        -> an equilibrium/frozen nozzle model in a separate namespace
```

v1 stays isolated: no γ(x) hook, no partially-wired variable-γ path (ADR-14).

---

## 11. Reference values

**Provenance of these numbers.** They were produced by evaluating the equations
printed in this document at `float64`, in an independent scratch script written
for this specification. They are therefore internally consistent with the stated
equations by construction, and they agree with the classical published tables at
the precision those tables are printed to. They are **not** transcriptions of a
table. Before any module is accepted, `05` §7 requires an independent
cross-check of at least the starred rows against NACA 1135 (or Anderson's
appendices), and the reference-data files record which source confirmed each
value.

Digits given here exceed what the tests should assert; tolerances are in `05`.

### 11.1 Isentropic, γ = 1.4

| M | T/T₀ | p/p₀ | ρ/ρ₀ | A/A\* |
| --- | --- | --- | --- | --- |
| 0 | 1 | 1 | 1 | ∞ (DomainError) |
| 0.2 | 0.9920634921 | 0.9724967030 | 0.9802766766 | 2.9635200000 |
| 0.5 | 0.9523809524 | 0.8430191754 | 0.8851701342 | 1.3398437500 |
| 0.8 | 0.8865248227 | 0.6560216184 | 0.7399923855 | 1.0382300000 |
| 1.0 \* | 0.8333333333 | 0.5282817877 | 0.6339381453 | 1.0000000000 |
| 1.5 | 0.6896551724 | 0.2724030665 | 0.3949844464 | 1.1761670525 |
| 2.0 \* | 0.5555555556 | 0.1278045255 | 0.2300481458 | 1.6875000000 |
| 3.0 \* | 0.3571428571 | 0.0272236837 | 0.0762263144 | 4.2345679012 |
| 5.0 | 0.1666666667 | 0.0018900384 | 0.0113402303 | 25.0000000000 |

Exact rational checks a reviewer can verify by hand at γ = 1.4: T/T₀ = 5/6 at
M = 1, 5/9 at M = 2, 5/14 at M = 3, 1/6 at M = 5; A/A\* = 25 exactly at M = 5 and
27/16 exactly at M = 2.

### 11.2 Area-Mach inverse, γ = 1.4

| A/A\* | M subsonic | M supersonic |
| --- | --- | --- |
| 1.0 | 1 (exact, both branches) | 1 (exact) |
| 1.5 | 0.4302617321 | 1.8541235267 |
| 2.0 \* | 0.3059038342 | 2.1971981217 |
| 2.4 | 0.2503049138 | 2.3985993045 |
| 4.0 | 0.1465482140 | 2.9401791693 |
| 10.0 | 0.0579872029 | 3.9225518209 |
| 100.0 | 0.0057871533 | 6.9362903898 |

### 11.3 Mass flow

| γ | p\*/p₀ | Γ(γ) |
| --- | --- | --- |
| 1.10 | 0.5846792891 | 0.6283602479 |
| 1.20 | 0.5644739301 | 0.6485311707 |
| 1.22 | 0.5606134091 | 0.6523863806 |
| 1.30 | 0.5457277338 | 0.6672623512 |
| 1.40 \* | 0.5282817877 | 0.6847314564 |
| 1.66 | 0.4880837599 | 0.7252274303 |

MFP at γ = 1.4: 0.2310534285 (M = 0.2), 0.5110532153 (M = 0.5),
**0.6847314564 (M = 1, the maximum, equal to Γ)**, 0.4057667890 (M = 2),
0.1617004314 (M = 3).

### 11.4 Normal shock, γ = 1.4

| M₁ | M₂ | p₂/p₁ | ρ₂/ρ₁ | T₂/T₁ | p₀₂/p₀₁ |
| --- | --- | --- | --- | --- | --- |
| 1.0 | 1.0000000000 | 1.0000000000 | 1.0000000000 | 1.0000000000 | 1.0000000000 |
| 1.5 | 0.7010887417 | 2.4583333333 | 1.8620689655 | 1.3202160494 | 0.9297865123 |
| 2.0 \* | 0.5773502692 | 4.5000000000 | 2.6666666667 | 1.6875000000 | 0.7208738615 |
| 3.0 \* | 0.4751909633 | 10.3333333333 | 3.8571428571 | 2.6790123457 | 0.3283438882 |
| 5.0 | 0.4152273993 | 29.0000000000 | 5.0000000000 | 5.8000000000 | 0.0617163197 |

Exact at γ = 1.4: p₂/p₁ = 9/2 at M₁ = 2, 31/3 at M₁ = 3, 29 at M₁ = 5;
ρ₂/ρ₁ = 8/3 at M₁ = 2 and 27/7 at M₁ = 3; M₂ = 1/√3 at M₁ = 2.

### 11.5 Oblique shock, γ = 1.4

θ_max and the sonic wave angle:

| M₁ | θ_max [°] | β at θ_max [°] | θ at M₂ = 1 [°] | β_sonic [°] | μ [°] |
| --- | --- | --- | --- | --- | --- |
| 1.2 | 3.94418698 | 71.97654795 | 3.70077175 | 68.07572881 | 56.44269 |
| 1.5 | 12.11266889 | 66.58887589 | 11.69333282 | 62.25682634 | 41.81031 |
| 2.0 \* | 22.97353176 | 64.66897983 | 22.70598675 | 61.48537164 | 30.00000 |
| 3.0 \* | 34.07343978 | 65.24084545 | 34.00834530 | 63.76660294 | 19.47122 |
| 5.0 | 41.11766310 | 66.58424395 | 41.10940077 | 66.08399728 | 11.53696 |
| 10.0 | 44.42901938 | 67.45435106 | 44.42852324 | 67.33509986 | 5.73917 |

Solved cases:

| M₁ | θ [°] | β weak [°] | β strong [°] | M₂ weak | p₂/p₁ weak | M₂ strong | p₂/p₁ strong |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2.0 \* | 10 | 39.31393184 | 83.70008038 | 1.64052223 | 1.70657860 | 0.60369764 | 4.44380721 |
| 2.0 | 20 | 53.42294053 | 74.27013704 | 1.21021840 | 2.84286271 | 0.72778855 | 4.15701686 |
| 3.0 \* | 20 | 37.76363415 | 82.14667102 | 1.99413167 | 3.77125746 | 0.53936286 | 10.13729988 |
| 5.0 | 30 | 42.34426480 | 80.64342348 | 2.13564125 | 13.06668858 | 0.53827016 | 28.22907617 |

θ_max at M₁ = 2 for other γ: 26.79177125° (1.2), 24.72935680° (1.3),
19.42123489° (1.66) — the γ-dependence is strong and worth a comparison plot.

### 11.6 Prandtl–Meyer, γ = 1.4

| M | ν [°] | μ [°] |
| --- | --- | --- |
| 1.0 | 0.0000000000 | 90.0000000000 |
| 1.5 | 11.9052088267 | 41.8103148958 |
| 2.0 \* | 26.3797608134 | 30.0000000000 |
| 3.0 \* | 49.7573467443 | 19.4712206345 |
| 5.0 | 76.9202155085 | 11.5369590328 |
| 10.0 | 102.3162531732 | 5.7391704773 |

ν_max: 130.4540768505° (γ = 1.4), 208.49623113° (1.2), 159.19871589° (1.3),
90.68053173° (1.66).

Inverse: ν = 30° → M = 2.1339050332; ν = 45° → M = 2.7644521940.

### 11.7 Fanno, γ = 1.4, Fanning, `4fL*/D`

| M | T/T\* | p/p\* | ρ/ρ\* | p₀/p₀\* | 4fL\*/D |
| --- | --- | --- | --- | --- | --- |
| 0.1 | 1.1976047904 | 10.9435131033 | 9.1378334412 | 5.8218287500 | 66.9215600298 |
| 0.2 | 1.1904761905 | 5.4554472559 | 4.5825756950 | 2.9635200000 | 14.5332664820 |
| 0.3 \* | 1.1787819253 | 3.6190574668 | 3.0701670844 | 2.0350652623 | 5.2992531051 |
| 0.5 \* | 1.1428571429 | 2.1380899353 | 1.8708286934 | 1.3398437500 | 1.0690603127 |
| 0.8 | 1.0638297872 | 1.2892765578 | 1.2119199644 | 1.0382300000 | 0.0722899724 |
| 1.0 | 1.0000000000 | 1.0000000000 | 1.0000000000 | 1.0000000000 | 0.0000000000 |
| 1.5 | 0.8275862069 | 0.6064784349 | 0.7328281088 | 1.1761670525 | 0.1360502174 |
| 2.0 \* | 0.6666666667 | 0.4082482905 | 0.6123724357 | 1.6875000000 | 0.3049965026 |
| 3.0 \* | 0.4285714286 | 0.2182178902 | 0.5091750772 | 4.2345679012 | 0.5221594082 |
| 5.0 | 0.2000000000 | 0.0894427191 | 0.4472135955 | 25.0000000000 | 0.6938039249 |

Supersonic limit `4fL*/D → 0.8215081165`. Note the p₀/p₀\* column reproducing the
A/A\* column of §11.1 exactly, as §8.4 states.

Duct problems: M₁ = 0.3 with `4fL/D = 3.0` → M₂ = 0.4005096605 (choking length
5.2992531051, so the duct is short enough); M₁ = 3.0 with `4fL/D = 0.3` →
M₂ = 1.7415765823.

### 11.8 Rayleigh, γ = 1.4

| M | T/T\* | p/p\* | ρ/ρ\* | T₀/T₀\* | p₀/p₀\* |
| --- | --- | --- | --- | --- | --- |
| 0.1 | 0.0560204475 | 2.3668639053 | 42.2500000000 | 0.0467770736 | 1.2591455962 |
| 0.2 \* | 0.2066115702 | 2.2727272727 | 11.0000000000 | 0.1735537190 | 1.2345958840 |
| 0.3 | 0.4088727920 | 2.1314387211 | 5.2129629630 | 0.3468604185 | 1.1985487768 |
| 0.5 \* | 0.7901234568 | 1.7777777778 | 2.2500000000 | 0.6913580247 | 1.1140525032 |
| 0.8451542547 | 1.0285714286 | 1.2000000000 | 1.1666666667 | 0.9795918367 | 1.0116230105 |
| 1.0 | 1.0000000000 | 1.0000000000 | 1.0000000000 | 1.0000000000 | 1.0000000000 |
| 1.5 | 0.7525039919 | 0.5783132530 | 0.7685185185 | 0.9092756568 | 1.1215452275 |
| 2.0 \* | 0.5289256198 | 0.3636363636 | 0.6875000000 | 0.7933884298 | 1.5030959785 |
| 3.0 \* | 0.2802768166 | 0.1764705882 | 0.6296296296 | 0.6539792388 | 3.4244519899 |
| 5.0 | 0.1111111111 | 0.0666666667 | 0.6000000000 | 0.5555555556 | 18.6338998125 |

The row at M = 0.8451542547 = 1/√1.4 is the T/T\* maximum, value
(γ+1)²/(4γ) = 1.0285714286 exactly (= 36/35).

Heat addition: M₁ = 0.2 (T₀/T₀\* = 0.1735537190) with T₀₂/T₀₁ = 2 →
M₂ = 0.3001345550; with T₀₂/T₀₁ = 4 → M₂ = 0.5019571678.

### 11.9 Nozzle, γ = 1.4, Ae/A\* = 2.0

Criticals as in §10.4. Internal shock at A_s/A\* = 1.5 as in §10.6.

Additional check — shock exactly at the exit: M₁ = 2.1971981217 gives
M₂ = 0.5474316548, p₂/p₁ = 5.4656261834, p₀₂/p₀₁ = 0.6294128957, and
p_b/p₀ = 0.0939326457 × 5.4656261834 = 0.5134007280, which must equal the second
critical to machine precision. That identity is a required test (`05` §10).

---

## 12. Mandatory pseudocode

Not runnable Python. Tolerances named here are defined in `04` §5.

### 12.1 Area-Mach inverse

```
function mach_from_area_ratio(AR, gas, branch):
    require gas.gamma > 1
    if AR is nan or AR <= 0:            raise DomainError
    if AR < 1 - AREA_SONIC_TOL:         raise AreaRatioError(AR)      # NO clamping

    if |AR - 1| <= AREA_SONIC_TOL:
        return Solution(1.0, OK, [Diagnostic(SONIC_EXACT, INFO, ...)],
                        convergence = Convergence(True, 0, |AR-1|, AREA_SONIC_TOL,
                                                  None, "analytic"))

    define F(M) = isentropic.area_ratio(M, gas) - AR       # continuous, monotone on each branch

    if branch is SUBSONIC:
        lo = M_SUB_FLOOR(AR, gamma)          # 04 section 3.1: asymptotic seed, not a magic number
        hi = 1 - SONIC_MARGIN
    else if branch is SUPERSONIC:
        lo = 1 + SONIC_MARGIN
        hi = M_SUP_CEILING(AR, gamma)        # asymptotic seed, expanded until F(hi) > 0
    else:
        raise ValueError("branch must be SUBSONIC or SUPERSONIC; use *_both for a pair")

    assert F(lo) and F(hi) have opposite signs        # else BracketError

    (M, report) = brent(F, lo, hi, xtol = MACH_ABS_TOL, rtol = MACH_REL_TOL,
                        max_iter = MAX_ITER)

    diagnostics = []
    if |M - 1| <= NEAR_SONIC_MACH:
        diagnostics.append(Diagnostic(NEAR_SONIC, WARNING,
            "Area ratio is within {d} of unity; Mach resolution near sonic is "
            "limited to about sqrt((gamma+1)/2 * d).", ...))

    return Solution(M, OK if report.converged else NOT_CONVERGED,
                    diagnostics, provenance = (REL_AREA_MACH,),
                    convergence = report)
```

### 12.2 Oblique shock: β from θ

```
function beta_from_theta(M1, theta, gas, branch):
    if M1 <= 1:            raise SubsonicShockError
    if theta < 0:          raise DomainError
    mu = asin(1 / M1)

    if theta <= ANGLE_TOL:                     # Mach wave
        return Solution(mu, OK, [Diagnostic(SONIC_EXACT, INFO, "zero-deflection Mach wave")])

    beta_max   = closed_form_beta_at_theta_max(M1, gamma)      # section 6.3, one sqrt
    theta_lim  = theta_from_beta(beta_max, M1, gamma)

    if theta > theta_lim + ANGLE_TOL:
        return Solution(None, NO_SOLUTION, [Diagnostic(DETACHED_SHOCK, ERROR, ...,
                        detail = {theta, theta_lim, M1})])

    if |theta - theta_lim| <= ANGLE_TOL:       # the two roots have merged
        return Solution(beta_max, OK, [Diagnostic(BRANCH_ASSUMED, INFO,
                        "weak and strong solutions coincide at theta_max")])

    define G(b) = theta_from_beta(b, M1, gamma) - theta
    # G is single-signed-crossing on each side of beta_max, by construction

    if branch is WEAK:     lo, hi = mu + ANGLE_MARGIN, beta_max
    else:                  lo, hi = beta_max, pi/2 - ANGLE_MARGIN

    (beta, report) = brent(G, lo, hi, xtol = ANGLE_ABS_TOL, max_iter = MAX_ITER)
    return Solution(beta, OK if report.converged else NOT_CONVERGED, ...,
                    convergence = report)
```

`theta_max` itself needs **no** iteration (§6.3) — the closed form is the answer.
A numerical maximisation is kept only as a test oracle.

### 12.3 Prandtl–Meyer inverse

```
function mach_from_nu(nu_target, gas):
    if nu_target < 0:                       raise DomainError
    if nu_target <= NU_TOL:                 return Solution(1.0, OK, [SONIC_EXACT])
    nu_ceiling = nu_max(gas)                # (pi/2)(sqrt((g+1)/(g-1)) - 1)
    if nu_target >= nu_ceiling - NU_TOL:
        return Solution(None, NO_SOLUTION, [Diagnostic("NU_EXCEEDS_MAX", ERROR,
            "Requested turning exceeds the maximum expansion for this gamma.", ...)])

    define H(M) = nu(M, gas) - nu_target    # strictly increasing on M >= 1

    lo = 1.0
    hi = seed_from_asymptote(nu_target, gamma)      # 04 section 3.2
    while H(hi) < 0 and hi < MACH_CEILING:  hi = min(2*hi, MACH_CEILING)
    if H(hi) < 0:                           return Solution(None, NOT_CONVERGED, ...)

    (M, report) = brent(H, lo, hi, xtol = MACH_ABS_TOL, rtol = MACH_REL_TOL)
    return Solution(M, OK if report.converged else NOT_CONVERGED, ..., convergence = report)
```

### 12.4 Nozzle regime classifier and internal shock

```
function classify(AR_exit, r, gas):                 # r = pb/p0
    if AR_exit < 1:                       raise GeometryError
    if r <= 0 or r >= 1:                  raise InputError("back pressure must satisfy 0 < pb/p0 < 1")

    Me_sub = mach_from_area_ratio(AR_exit, gas, SUBSONIC).unwrap()
    Me_sup = mach_from_area_ratio(AR_exit, gas, SUPERSONIC).unwrap()

    first  = isentropic.pressure_ratio(Me_sub, gas)
    third  = isentropic.pressure_ratio(Me_sup, gas)
    second = third * normal_shock.pressure_ratio(Me_sup, gas)
    assert third < second < first < 1

    if r > first + PRESSURE_TOL:            regime = UNCHOKED_SUBSONIC
    elif |r - first|  <= PRESSURE_TOL:      regime = CHOKED_SUBSONIC_EXIT
    elif r > second + PRESSURE_TOL:         regime = INTERNAL_NORMAL_SHOCK
    elif |r - second| <= PRESSURE_TOL:      regime = SHOCK_AT_EXIT
    elif r > third + PRESSURE_TOL:          regime = OVEREXPANDED
    elif |r - third|  <= PRESSURE_TOL:      regime = IDEALLY_EXPANDED
    else:                                   regime = UNDEREXPANDED
    return regime, CriticalPressureRatios(...)


function shock_area_ratio(AR_exit, r, gas):         # only for INTERNAL_NORMAL_SHOCK
    define F(As):                                   # As = A_shock / A1*   in (1, AR_exit)
        Ms1   = mach_from_area_ratio(As, gas, SUPERSONIC).unwrap()
        shock = normal_shock.solve(Ms1, gas)
        A2_star_ratio = 1 / shock.stagnation_pressure_ratio          # A2*/A1*
        Me    = mach_from_area_ratio(AR_exit / A2_star_ratio, gas, SUBSONIC).unwrap()
        pe_over_p01 = isentropic.pressure_ratio(Me, gas) * shock.stagnation_pressure_ratio
        return pe_over_p01 - r

    # F is strictly decreasing in As (section 10.6), and the ends are the criticals:
    #   F(1+)      -> first  - r   > 0
    #   F(AR_exit) -> second - r   < 0
    (As, report) = brent(F, 1 + SONIC_MARGIN, AR_exit, xtol = AREA_ABS_TOL,
                         rtol = AREA_REL_TOL, max_iter = MAX_ITER)
    return ShockLocation(As, x = geometry.x_at_area(As) if geometry else None, ...)
```

### 12.5 Fanno inverse on a branch

```
function mach_from_friction_parameter(L, gas, branch):
    if L < 0:                        raise DomainError
    if L <= FANNO_TOL:               return Solution(1.0, OK, [SONIC_EXACT])

    define K(M) = friction_parameter(M, gas) - L      # decreasing on (0,1), increasing... see note

    if branch is SUBSONIC:
        # 4fL*/D decreases monotonically from +inf at M -> 0 to 0 at M = 1
        lo = subsonic_seed(L, gamma)                  # 04 section 3.4
        while K(lo) < 0 and lo > MACH_FLOOR:  lo = lo / 2
        hi = 1 - SONIC_MARGIN
    else:
        # on the supersonic branch it rises from 0 at M = 1 to a finite limit
        L_limit = -1/gamma + (gamma+1)/(2*gamma) * ln((gamma+1)/(gamma-1))
        if L > L_limit - FANNO_TOL:
            return Solution(None, NO_SOLUTION, [Diagnostic("FANNO_LIMIT", ERROR,
                "Requested friction parameter exceeds the supersonic maximum "
                "{L_limit} for this gamma.", ...)])
        lo = 1 + SONIC_MARGIN
        hi = supersonic_seed(L, gamma)
        while K(hi) < 0 and hi < MACH_CEILING:  hi = min(2*hi, MACH_CEILING)

    (M, report) = brent(K, lo, hi, ...)
    return Solution(M, ..., convergence = report)
```

### 12.6 Rayleigh inverse on a branch

```
function mach_from_stagnation_temperature_ratio(r, gas, branch):
    if r <= 0:                raise DomainError
    if r > 1 + RAYLEIGH_TOL:
        return Solution(None, NO_SOLUTION, [Diagnostic(THERMALLY_CHOKED, ERROR,
            "T0/T0* cannot exceed 1: the requested heating drives the flow past "
            "the sonic condition.", ...)])
    if |r - 1| <= RAYLEIGH_TOL:   return Solution(1.0, OK, [SONIC_EXACT])

    define P(M) = stagnation_temperature_ratio(M, gas) - r
    # T0/T0* increases monotonically from 0 at M -> 0 to 1 at M = 1,
    # then decreases from 1 to (gamma^2 - 1)/gamma^2 as M -> infinity

    if branch is SUBSONIC:
        lo, hi = MACH_FLOOR, 1 - SONIC_MARGIN
    else:
        limit = (gamma^2 - 1) / gamma^2
        if r < limit - RAYLEIGH_TOL:
            return Solution(None, NO_SOLUTION, [Diagnostic("RAYLEIGH_LIMIT", ERROR,
                "T0/T0* below {limit} is unreachable on the supersonic branch.", ...)])
        lo, hi = 1 + SONIC_MARGIN, MACH_CEILING

    (M, report) = brent(P, lo, hi, ...)
    return Solution(M, ..., convergence = report)
```

### 12.7 Full nozzle distributed solve

```
function solve(geometry, operating, gas):
    validate geometry (section 10.2); AR_exit = geometry.exit_area / geometry.throat_area
    r = operating.back_pressure / operating.stagnation_pressure
    regime, criticals = classify(AR_exit, r, gas)

    switch regime:
      UNCHOKED_SUBSONIC:
          Me      = isentropic.mach_from_pressure_ratio(r, gas)
          A_star  = geometry.exit_area / isentropic.area_ratio(Me, gas)   # virtual
          M(x)    = mach_from_area_ratio(A(x)/A_star, gas, SUBSONIC)      # every station
          p0(x)   = p0 everywhere;  choked = False;  shock = None

      CHOKED_SUBSONIC_EXIT:
          A_star  = geometry.throat_area
          M(x)    = SUBSONIC branch everywhere;  M(throat) = 1 exactly
          shock = None

      INTERNAL_NORMAL_SHOCK, SHOCK_AT_EXIT:
          A_star  = geometry.throat_area
          As      = shock_area_ratio(AR_exit, r, gas)            # section 12.4
          x_s     = geometry.x_at_area(As * A_star, side = "diverging")
          upstream of throat:      SUBSONIC branch
          throat -> x_s:           SUPERSONIC branch, p0 = p01
          duplicate the station at x_s (section 10.8)
          x_s -> exit:             SUBSONIC branch on A/A2*, p0 = p02
          choked = True

      OVEREXPANDED, IDEALLY_EXPANDED, UNDEREXPANDED:
          A_star  = geometry.throat_area
          upstream of throat: SUBSONIC;  throat: M = 1;  downstream: SUPERSONIC
          p0(x) = p01 everywhere;  shock = None;  choked = True
          if regime is OVEREXPANDED and pe / pb < 0.4:
              emit MODEL_LIMIT_SEPARATION (a flag, not a prediction - section 10.9)

    # dimensional fill-in, only if T0 and R are available
    T(x)   = T0 * isentropic.temperature_ratio(M(x), gas)
    p(x)   = p0(x) * isentropic.pressure_ratio(M(x), gas)
    rho(x) = p(x) / (R * T(x))
    a(x)   = sqrt(gamma * R * T(x));    V(x) = M(x) * a(x)
    mdot   = choked ? mass_flow.choked_mass_flow(gas, A_throat, p0, T0)
                    : mass_flow.mass_flow(M(throat), gas, A_throat, p0, T0)

    return Solution(NozzleSolution(...), OK | OK_WITH_WARNINGS, diagnostics,
                    provenance = (REL_AREA_MACH, REL_ISENTROPIC, REL_NORMAL_SHOCK, ...))
```
