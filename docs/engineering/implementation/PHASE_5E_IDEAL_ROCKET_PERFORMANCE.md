# Phase 5E — Ideal Rocket Performance

RocketForge-owned characteristic velocity, thrust coefficient, momentum and
pressure thrust, total thrust, effective exhaust velocity and specific impulse,
with explicit ambient-pressure and nozzle-expansion semantics, a constant-property
perfect-gas reduction, a CEA native performance oracle, external reference
validation, and a Rocket Performance application and interface.

**Status: COMPLETE — READY FOR PHASE 5F.**

---

## 1. What this phase owns

Before it, RocketForge could compute a chamber equilibrium and a quasi-1D
nozzle flow, and could not say what an engine would do with them. Phase 5D
deliberately shipped no c\*, no Cf and no Isp, because RocketForge owned none
of them.

It owns all of them now, and computes every one from its own equations over the
frozen Phase 4 gas dynamics.

The provider's own c\*, Cf and Isp are also reachable, and are an **oracle** —
something to compare against, never the implementation. Section 6 lists the
four properties that keep that true rather than intended.

---

## 2. The single-gamma handshake

`ChamberGas` carries two isentropic exponents, γ_s (equilibrium) and
γ_fr = cp/cv (frozen), **5.56 % apart** on the demonstration case. `PerfectGas`
carries one. Reducing the first to the second is the modelling decision the
whole phase rests on, so it is an explicit call in a new package,
`engineering.chamber`, with no default.

`GammaStrategy` alone was not enough: it says *where along the flow* to take
gamma, not *which of the two*. `ChamberGammaBasis` was added in the engineering
layer, leaving every thermochemistry domain type untouched.

Doc 12 §4 preconditions P1–P8 are enforced, each with its own refusal code and
its own mutation proof — 16 in total, every one asserting the fixture actually
changed before checking that the rule fired.

The single-phase limit here (`SINGLE_PHASE_CONDENSED_LIMIT`) is a **physics**
threshold and is unrelated to Phase 5D's presentation-only
`CONDENSED_REPORTING_THRESHOLD`. They are separate constants in separate
layers, and the Phase 5D corrective patch's guarantee is untouched.

---

## 3. The equations

`c* = sqrt(R T0) / Gamma(gamma)` — derived from the frozen choked-flow physics,
one substitution from `c* = p_c A_t / mdot`, rather than restated.

Checked against an independent implementation written from the textbook
relations with nothing but `math`, including its own bisection for the
area–Mach inverse:

| Check | Result |
| --- | --- |
| c\* vs the independent analytic form | **4e-16** relative, 5 gases |
| identity matrix, 15 relations | worst **3.7e-16**, both scale modes, three ambients |
| c\* invariance under ε, p_a, A_t | exact equality |
| exit state invariance under p_a | exact equality |
| pressure-thrust sign | positive / zero / negative, as the case requires |
| optimum-expansion identity c_eff = V_e at p_e = p_a | 1e-12 |
| scale doubling | normalized unchanged, absolutes ×2 to 1e-13 |
| mass-flow scale round trip | throat area recovered to 1e-13 |

### Semantics that are stated, not assumed

**Ambient pressure is zero in vacuum**, not a missing value, and needs no
separate equation. It never touches c\*, and never touches the internal nozzle
solution; it enters `(p_e − p_a)A_e` alone.

**The pressure term is signed.** Negative for an overexpanded nozzle, and never
clamped — a clamp would make an overexpanded engine look as good as an ideally
expanded one.

**Isp is in seconds.** `c_eff` is in m/s. Nothing in this codebase labels a
value in m/s as an Isp.

**`NORMALIZED` is not a degraded mode.** With no engine size, thrust, mass flow
and the areas are `None` — never zero, because zero thrust is a claim about an
engine rather than the absence of one.

**Three regimes are supported**: overexpanded, ideally expanded, underexpanded.
They share one internal solution. Everything else — an internal shock, a shock
at the exit plane, a choked subsonic diverging section, an unchoked nozzle — is
a *different internal solution*, and is refused by name with
`NOZZLE_REGIME_UNSUPPORTED` rather than reported with this model's authority
attached.

---

## 4. Running with no chemistry library

The whole chain runs in the base environment. Proved two ways, both
order-independent:

* **in process, as a delta** — solving imports no chemistry module that was not
  already loaded; and
* **in a clean interpreter** — a subprocess imports the chain, reduces a
  chamber state, solves, verifies the identities, and asserts `sys.modules`
  holds no `cea`, `cantera` or `CoolProp` entry at all.

The second is the claim the phase actually makes. The first version of this
test read `sys.modules` absolutely in process, which asserted "nothing anywhere
in this pytest session has imported a chemistry library" — a property of
collection order, not of this code. It had been passing by luck, and started
failing as soon as an application test that legitimately exercises the provider
ran before it. Replacing it was a correction, and the replacement is stronger.

---

## 5. Zero chemistry re-solve — the blocking requirement

Ideal performance is algebra over an already-solved chamber state, so changing
a nozzle input must cost **zero** chamber solves.

**Structurally**: `performance_service` imports neither `rocketforge.providers`
nor the provider gateway, so no expression in it can start a solve. It also
does not import `performance_oracle`.

**Behaviourally**, by call count, at three levels:

| Level | Inputs changed | Chamber solves |
| --- | --- | --- |
| service function | ε, p_a, scale, gamma basis, gamma strategy — 5× each | **0** |
| service function | 15 combined changes in sequence | **0** |
| Qt controller | each of the six inputs, then a 15-step session | **0** |
| Qt controller | reading every published property | **0** |
| **packaged executable** | 9 input changes across the tour | **0** |

Negative control at every level: solving a *different* chamber case raises the
count by exactly 1.

---

## 6. The oracle, and what keeps it one

`CEAThermochemistryProvider.rocket_oracle()` returns CEA's own c\*, Cf and Isp.

1. **Different types.** `OracleOutcome` carries plain floats under their own
   names; it is not an `IdealRocketPerformance`, and the two do not
   interchange.
2. **No import path.** The module computing RocketForge's performance fields
   cannot see the provider's.
3. **Explicit invocation.** It runs only from a user action, which is also why
   the zero-re-solve property survives having an oracle in the workspace.
4. **A separate CEA run.** A chamber state carries no performance figure, and
   this cannot be derived from one.

### What the comparison found

**No CEA mode is exactly like-for-like.** RocketForge v1 is *calorically*
perfect — cp constant. Every CEA mode is calorically imperfect, evaluating cp
from the NASA polynomials at the local temperature. No chemistry mode removes
that difference.

What *can* be matched is the chemistry assumption, which makes **frozen basis ↔
frozen-at-chamber** the nearest partner available. Nearest is not identical, so
every figure below is a **cross-model difference**; the term *validation
residual* is reserved for same-model checks — c\* against the independent
perfect-gas analytic form, and the internal identities against frozen
Compressible. LOX/LCH4, O/F 3.4, 100 bar, Ae/At 40:

| Quantity | RF frozen − CEA frozen-at-chamber | Classification |
| --- | --- | --- |
| c\* | **4.35e-04** | closest cross-model difference — the throat is a short expansion from the chamber, so the caloric mismatch has barely accumulated |
| Cf, optimum | 5.04e-03 | model difference |
| Isp, optimum | 5.48e-03 | model difference |
| Exit temperature | 1.26e-01 | model difference — the caloric assumption over the whole expansion |

The equilibrium basis agrees with CEA equilibrium to 3.3e-03 on Isp, and that
is **not** validation: γ_s is *defined* as the isentropic exponent of the
shifting expansion, so a constant-γ_s model approximates it by construction.
Close agreement between different models is recorded as a model difference.

### The reference condition, measured rather than assumed

CEA's printed Cf and Isp are the **optimum-expansion** values. Established by
measurement on the v3 provider: across all three chemistry modes,
`Cf + (p_e/p_c)·ε` reproduces `I_vac/c*` to between 6e-09 and 4e-07.

Comparing a vacuum figure against them is wrong by the whole pressure term —
**5.6 %** on a LOX/LH2 case at Ae/At 40, larger than every model difference the
comparison exists to show. The first version of the interface's comparison
table did exactly that, producing a spurious −4.93 % where the honest figure is
+0.55 %. Fixed by re-solving the **nozzle** at each reference condition the
provider quotes, reusing the gas reduction by identity.

---

## 7. External reference

`performance_nasa_cea_2002_lox_lh2.json` — NASA-GLENN CEA, October 18 2002,
McBride and Gordon; LOX/LH2 at O/F 6.0, 1000 psia, Ae/At 40. Produced by the
2002 Fortran implementation, while the provider under test is the v3
re-implementation, so neither number produced the other.

It validates the **oracle**, and compares RocketForge as a model comparison:

| Comparison | c\* | Isp | Verdict |
| --- | --- | --- | --- |
| published vs the CEA oracle | 3.82e-06 in a 6.61e-06 box | 1.32e-05 in 1.16e-04 | **PASS** |
| published vs RF, frozen basis | 1.70e-02 | 3.36e-02 | model difference |
| published vs RF, equilibrium basis | 4.99e-06 (within box) | 7.13e-03 | model difference |

The dataset records the reason in its own `validates` field, so the
distinction cannot be lost by someone reading the numbers alone.

---

## 8. The workspace

Third analysis domain, its own sidebar section, three views of one calculation.
The full contract is in `ROCKET_PERFORMANCE_UI_CONTRACT.md`; the rules it
enforces are: no equations or constants in QML, no provider import or provider
name in QML, no chamber state means no numbers, no engine size means no thrust,
a result is never relabelled, an upstream chamber change invalidates rather
than recomputes, and the oracle lives behind its own panel and its own button.

| | Source | Packaged |
| --- | --- | --- |
| Captures | 29 | 29 |
| Qt messages | **0** | **0** |
| Chamber solves from input changes | **0** | **0** |

**Parity: 5013 fields compared, 0 differing.**

---

## 9. Gates

| Gate | Opening | Closing |
| --- | --- | --- |
| Base (`.venv`) | 5799 passed, 106 skipped | **6108 passed, 113 skipped**, exit 0 |
| CEA-enabled (`.venv-cea`) | 5907 passed, 1 skipped | **6223 passed, 1 skipped**, exit 0 |
| Frozen Compressible | 22 / 22 byte-identical | **22 / 22 byte-identical** |

`rocketforge.physics.compressible` was not modified. Verified by recomputing
each file's recorded `sha256[:16]` against the Phase 4G manifest.

---

## 10. What this phase does not do

No combustion efficiency, no c\* or Cf efficiency, no divergence, viscous,
boundary-layer, separation or two-phase correction, no finite-rate chemistry,
no composition shift through the nozzle, no chamber geometry, no injector, no
cooling, no trade studies, no Pareto fronts, **no optimisation**.

Phase 5D's O/F sweep remains analysis-only. Nothing in this phase turned it
into an optimiser, and nothing here is a Trade Study Engine.

The assigned-enthalpy limitation is unchanged: still not solved, still warned
about, and the warning now travels downstream and is shown on the performance
result with its origin marked.

An ideal figure is an **upper bound** on a real engine. Every result carries
the assumption list that says so, and the interface shows it as a first-class
panel rather than a footnote.
