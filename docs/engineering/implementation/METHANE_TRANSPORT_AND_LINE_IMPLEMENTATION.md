# Methane transport validation and engineering.line

# Verdict

**METHANE TRANSPORT VALIDATED — ENGINEERING.LINE v1.0 ACCEPTED / FROZEN**

Both gates passed, in order. Methane dynamic viscosity is validated against
primary and evaluated-reference evidence over an explicit liquid envelope, and
`engineering.line` is built on it — the first hydraulic component in this
project and the first consumer of a transport property.

`06_future_module_dependency_map.md` §8 **step 2**. **No phase number
assigned.**

---

## Opening baseline

| Gate | Result |
| --- | --- |
| Base (`.venv`) | **6648 passed, 154 skipped**, exit 0, 50.93 s |
| Production (`.venv-cea`) | **6803 total**, exit 0 once the incident below was repaired |
| Frozen Compressible | 22 / 22 byte-identical |
| Freeze | all eight prior contracts reproduce |

**Authoritative production interpreter: `.venv-cea`**, established from
`build_exe.bat` and the fluids acceptance manifest rather than assumed.

### An incident in the opening gates, and its repair

Running the Phase 5G manifest generator regenerated `freeze_cea_provider_v1.json`
from the current v1.1 tree, writing 12 files under a "1.0" label and destroying
the historical record. **The supersession tests written in the previous phase
caught it within seconds** — the only reason it was recoverable rather than a
silent falsification.

Restored by inverting the exact v1.1 edits and accepted **only** because the
reconstruction reproduced the digest
`0a46b5f089a9cc7a47278eecd0868b8d68730aa1abbf9c5775e35cb70eb9285a`, published
in four documents that were not overwritten. The first attempt did not match —
two edits were missing — and nothing was written until it did. The generator
now refuses to regenerate a superseded contract.

---

## Gate A — methane viscosity

| | |
| --- | --- |
| Provider | CoolProp 8.0.0, `HEOS` |
| Exact transport model | **friction theory (f-theory)**, `QuinonesCisneros-JPCB-2006`, dilute-gas term plus an EOS-coupled residual, no critical enhancement, no state-dependent switching — read from CoolProp's own fluid JSON |
| Primary model reference | Quiñones-Cisneros & Deiters, J. Phys. Chem. B **110** (2006) 12820, DOI 10.1021/jp0618577 |
| Independent references | Sotiriadou, Antoniadis, Assael, Martinek & Huber (NIST), Int. J. Thermophys. **47** (2025) 18, DOI 10.1007/s10765-025-03690-7; Diller, Physica **104A** (1980) 417; NIST Chemistry WebBook |
| Validation envelope | **T 100–125 K, p 0.5–3.0 MPa, liquid**, p ≥ 1.5·p_sat |
| Reference points | **24** states, 4 T × 6 p, all `liquid`, plus saturated check values |
| Worst comparison | **2.885 %** at 100 K, 0.5 MPa |
| Reference uncertainty | **3 % (k=2)** liquid (2025 correlation); 2 % Diller; 1 % Boon |
| Acceptance criterion | **3 %**, the published expanded uncertainty — derived before comparing, never widened |
| NIST comparison classification | **cross-model difference**, not an implementation residual: friction theory vs a different correlation, on an identical EOS |
| Unit validation | ×1000, ÷1000, ×10⁶ all detected; no conversion in the adapter |
| Phase validation | 6/6 agree; two-phase withholds viscosity entirely |
| Determinism | identical repeats; A/B/A with oxygen clean |

### Why the worst case is acceptable, and how that was established

2.885 % against a 3 % criterion is too close to wave through, so the third leg
was measured. At 100 K saturated liquid:

| Source | μ (µPa·s) | vs the 2025 evaluated correlation |
| --- | --- | --- |
| Sotiriadou 2025 | 154.500 | — |
| **CoolProp** | 155.635 | **+0.734 %** |
| NIST WebBook | 150.956 | **−2.294 %** |

The provider is about three times closer to the current evaluated reference
than the older implementation is. The 2.885 % is a spread *between references*,
not a provider error — which is exactly what a 3 % (k=2) uncertainty means in
practice, and exactly what judging against one of two disagreeing references
would have got wrong.

The **density agrees to 0.00000 %** at every state, because both implement
Setzmann–Wagner. That isolates every viscosity difference to the transport
correlation, and is what makes the argument clean.

## Gate A verdict

**PASS.**

---

## engineering.line architecture

| | |
| --- | --- |
| Package | `rocketforge.engineering.line`, 7 modules |
| Dependencies | `rocketforge.core`, `rocketforge.physics.fluids` — **nothing else in the project**, asserted per module |
| Forbidden and asserted absent | provider imports, CEA, CoolProp, Qt, application |
| Fluid handshake | consumes a `FluidState`; requires an identified `LIQUID` phase and an **available** density and viscosity |

## Model scope

Steady, single-phase liquid, straight circular pipe of constant diameter, fully
developed, constant properties from one fluid state, distributed wall friction
only.

Excluded and asserted: entrance length, bends, fittings, valves, orifices,
minor losses, elevation, pumps, heat transfer, compressible-gas piping,
two-phase, cavitation, transients, non-circular ducts, variable-property
integration, network solving.

## Equations

```
A     = pi D^2 / 4
Q     = mdot / rho
V     = Q / A
Re    = rho V D / mu = 4 mdot / (pi D mu)
dp    = f_D (L/D) rho V^2 / 2
```

## Friction convention

**Darcy.** `f_D = 4 f_F`. The convention rides on every result, the interface
says "Darcy friction factor" in full, and the factor-of-four mutation is
asserted: replacing `f_D` with `f_D/4` moves the pressure drop by **75 %** and
the check fails loudly.

## Flow regimes

| Regime | Range | Source |
| --- | --- | --- |
| Laminar | Re < 2300 | classical critical value; `64/Re` is exact |
| **Transitional** | 2300 ≤ Re < 4000 | **no friction factor reported** |
| Turbulent | 4000 ≤ Re ≤ 1e8, ε/D ≤ 0.05 | Moody chart turbulent zone |

The transitional band reports no friction factor, no pressure drop and no
outlet pressure — not zero, not clamped, not interpolated. The result type
*enforces* it: constructing a transitional result with a friction factor raises.

## Laminar validation

| | |
| --- | --- |
| `f_D = 64/Re` | exact |
| Darcy-Weisbach vs Hagen-Poiseuille | worst **3.9e-16** |
| dp ∝ L, ∝ ṁ, ∝ D⁻⁴ | exact to 1e-12 |
| Roughness independence | bit-identical |

## Turbulent model

| | |
| --- | --- |
| Correlation | Colebrook-White |
| Source | Colebrook, J. Inst. Civ. Eng. 11 (1939) 133; Moody, Trans. ASME 66 (1944) 671 |
| Solve variable | `x = 1/sqrt(f_D)`, where the residual is provably monotone |
| Root solver | the project's own `brent` — no SciPy |
| Bracket | x ∈ [1, 30] |
| Tolerances | xtol 1e-13, rtol 1e-14, max_iter 100 |
| Worst iterations | **15** |
| Worst residual | **4.4e-14** |

## Turbulent validation

| | |
| --- | --- |
| Independent oracle | a **Decimal bisection** at 50 digits, sharing no code with production: 48 cases, worst **1.3e-14** |
| Fully-rough limit | von Kármán closed form, within 2e-3 |
| Smooth pipe | the exact Prandtl reduction, to 1e-12 (the textbook 0.8 is a rounding of 2·log₁₀2.51 = 0.79934, checked separately) |
| Blasius | a **sanity comparison only**, never the oracle |
| Roughness trend | monotone increasing at fixed Re |

## Fluid provenance

Density and viscosity come from the `FluidState` and are recorded on the
result. Against the state's own values: **bit-identical**. The provider, its
version and its backend travel into the result and onto the screen.

## Real LCH4 line case

| | |
| --- | --- |
| T, p | 111.643 K, 1.0 MPa — inside the validated envelope |
| ρ, μ | 423.233 kg/m³, 1.182187e-04 Pa·s |
| ṁ, L, D, ε | 2.0 kg/s, 5 m, 0.02 m, 1.5 µm |
| V, Re | 15.0418 m/s, 1.077020e+06 |
| Regime, f_D | turbulent, **0.0129718** |
| Δp | **155 271 Pa** |

Independent recomputation, with the friction factor from the Decimal oracle:
worst difference across every field **2.7e-16**.

## Pressure semantics

The fluid state's pressure **is** the line inlet pressure — a feed-system
state. Chamber pressure reused implicitly: **NO**, asserted by an AST audit
with a negative control that fires on the substitution. The field is labelled
"Line inlet pressure". A loss exceeding the inlet pressure returns
`LINE_INSUFFICIENT_INLET_PRESSURE`, never a clamped or negative pressure.

## `density_hint`

Read by the line: **NO.** AST audit with a negative control.

## Determinism, recovery, performance

| | |
| --- | --- |
| Five identical solves | identical |
| Methane / oxygen / methane | no leak; the fluids genuinely differ |
| Canonical case after a refusal | **exact** |
| Colebrook | ~118 000 solves/s |
| Full line | ~44 000 solves/s |
| 5 000-solve soak | **+0.0003 MB** |

## Application and workspace

`LineService` (Qt-free) → `LineController` → `Analysis → Line`. The transport
envelope gate lives in the **application**, not in `engineering.line`: the line
model is generic and will solve any valid state, while what RocketForge is
willing to *claim* is a product decision belonging to the composition root.

The page shows density, viscosity, area, velocity, Reynolds number, regime,
relative roughness, the Darcy friction factor, dynamic pressure, the friction
pressure drop, the inlet and predicted outlet pressures, full provenance and
all twelve model assumptions. The "Viscosity validated" chip is never true
merely because a provider answered.

## Visual acceptance

17 workspaces at 2560×1440, 1920×1080 and 1366×768 in both themes, **62
captures, 0 Qt messages**. Reviewed by looking at them.

## Packaged executable

| | |
| --- | --- |
| Build | clean rebuild from `.venv-cea` |
| Files / size | 2 240 / 245.1 MB |
| Self-tests | **8 / 8 exit 0** |
| `--selftest-line` | solves a real turbulent and a real laminar line, withholds the friction factor in the transition, refuses a state outside the validated envelope |
| **Source ↔ packaged parity** | **149 fields, 0 differences** |
| `thermo.lib` matches accepted | YES |
| Forbidden dependencies | absent |

**Clean-machine caveat**, unchanged: self-containment of the bundle, not
verified clean-machine operation.

## Tests

| Suite | Result |
| --- | --- |
| Base (`.venv`) | **6831 passed, 154 skipped**, exit 0 |
| Production (`.venv-cea`) | **6986 passed, 2 skipped**, exit 0 |
| Repeat | **6986 / 2 — identical** |
| Added | **+183** in each environment |

## Frozen contracts

| Contract | State |
| --- | --- |
| Compressible v1.0 | 22 / 22 byte-identical |
| Thermochemistry, Performance, Trade Study v1.0 | unchanged |
| CEA Provider v1.0 | superseded; **restored and digest-verified** |
| CEA Provider v1.1, Fluid Properties, CoolProp Provider, Propellant Metrics | unchanged |
| **LINE API v1.0** | **7 files, `3de3a979b7ce7ea2acd37a20e1a028671411506bbea5d3f97bb290713c5cca4d`** |

---

## Corrections made during this work

**1 — The manifest overwrite.** Mine; caught by the previous phase's tests;
repaired by digest-verified reconstruction; cause fixed in the generator.

**2 — Two pages bound to a singleton that does not exist.**
`Palette.textMuted` — the theme singleton is `Theme`. The Fluid Properties page
shipped with this in the previous phase and nothing noticed, because the
workspace tour renders those pages **empty** and an unevaluated binding is
silent. Both pages fixed; the tour now populates them before capturing; a new
rule rejects any page naming a singleton that does not exist, with the
component inventory derived from the tree rather than hand-listed.

**3 — Three defects in my own audits.** The QML physics scan flagged four
innocents — three drawing primitives using `Math.PI *`, and the Fanno page's
`frictionFactor` *binding*. The Colebrook-constant scan flagged the Line page's
own explanatory comment. The singleton allowlist went stale immediately. All
rewritten: comments stripped, scope narrowed to the file each rule governs,
inventory derived structurally.

**4 — My own fixtures were wrong twice.** Five "laminar" test cases were
turbulent; three mutation cases exceeded the inlet pressure and were correctly
refused. The production code was right both times.

**5 — A fluids-foundation scope rule narrowed.** It asserted `engineering.line`
did not exist. This work is the roadmap step that creates it, so `line` — and
only `line` — was removed from that list, with a counterpart test asserting the
package now exists.

---

## Known limitations

* Straight circular line only; single-phase liquid only.
* **Constant properties**: one ρ and one μ along the whole line. This is a
  steady single-phase constant-property straight-line model, not a
  pressure-coupled hydraulic solver, and it is not described as one anywhere.
* Distributed wall friction only — no minor losses, fittings, valves, orifices,
  elevation, heat transfer, cavitation, two-phase pressure drop or transients.
* **No transition correlation.** Between Re 2300 and 4000 nothing is reported.
* Methane viscosity carries a **3 % (k=2)** uncertainty from the reference
  correlation, and every pressure drop computed from it inherits that floor.
* Line results are offered only inside each fluid's validated transport
  envelope; outside it the provider still answers but RocketForge does not
  present a production result.
* No hydraulic network solver.

---

## Deferred roadmap

Per `06_future_module_dependency_map.md` §8 step 2, the remaining components in
this family:

    engineering.valve
    engineering.orifice

**Not implemented here**, and asserted absent. Both will need their own
discharge-coefficient and flow-coefficient contracts, and neither should be
folded into the line: the line owns distributed straight-pipe friction and
nothing else.
