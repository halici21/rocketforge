# Line API v1.0 — FROZEN

**Frozen on the transport-validation and line acceptance.**

| | |
| --- | --- |
| Package | `rocketforge.engineering.line` |
| Layer | L2, component. Depends on `core` and `physics.fluids` |
| Roadmap | `06_future_module_dependency_map.md` §8 **step 2** |
| Manifest | `tests/acceptance/freeze/transport_line/freeze_line_api_v1.json`, 7 files, digest `3de3a979b7ce7ea2…` |

The first hydraulic component in this project, and the first consumer of a
transport property. It exists only because
[METHANE_TRANSPORT_VALIDATION.md](METHANE_TRANSPORT_VALIDATION.md) closed the
viscosity gap the fluids foundation deliberately left open.

---

## Scope

**What it models.** Steady flow. Single-phase liquid. A straight circular pipe
of constant inner diameter. Fully developed flow. Constant properties taken
from one fluid state. Distributed wall friction only. Laminar and turbulent
branches with an explicit boundary between them.

**What it does not model, and must not be made to.**

No entrance length. No bends, elbows, tees or fittings. No valves. No orifices.
No minor losses of any kind. No elevation or head. No pumps. No heat transfer.
No compressible-gas piping. No two-phase flow. No cavitation or flashing. No
transients. No non-circular ducts. No variable-property integration along the
line. No network solver. No pipe structural sizing.

Several of those are the next roadmap steps. Hiding any of them inside a
straight-line friction number would make it quietly mean something else, so a
static test asserts that no minor-loss vocabulary appears in the package and
that no neighbouring component directory exists.

---

## The equations

```
A     = pi D^2 / 4                        m^2
Q     = mdot / rho                        m^3/s
V     = Q / A = mdot / (rho A)            m/s
Re    = rho V D / mu = 4 mdot / (pi D mu) dimensionless
eps/D = absolute roughness / D            dimensionless
q     = rho V^2 / 2                       Pa
dp    = f_D (L/D) rho V^2 / 2             Pa
```

The two Reynolds forms are written separately and **checked against each
other** on every result; the residual on the canonical case is exactly 0.

---

## Darcy, not Fanning

> **f_D = 4 f_F**

Every friction factor in this package is **Darcy**, Darcy-Weisbach requires
Darcy, and substituting Fanning underpredicts a pressure drop by exactly four.
The convention travels on every result in `friction_convention`, the interface
says "Darcy friction factor" in full, and a mutation test replaces `f_D` with
`f_D/4` and requires the pressure drop to move by 75 %.

---

## Flow regimes

| Regime | Range | Friction factor |
| --- | --- | --- |
| Laminar | Re < 2300 | `f_D = 64 / Re`, exact |
| **Transitional** | 2300 ≤ Re < 4000 | **none reported** |
| Turbulent | 4000 ≤ Re ≤ 1e8 | Colebrook-White, solved |

`REYNOLDS_LAMINAR_LIMIT = 2300` is the classical critical value for a circular
pipe. `REYNOLDS_TURBULENT_ONSET = 4000` and `COLEBROOK_REYNOLDS_MAX = 1e8` are
the edges of the turbulent zone of the Moody chart, and
`MAX_RELATIVE_ROUGHNESS = 0.05` is the largest relative roughness that chart
covers. Outside them the correlation is refused, not extrapolated.

### The transitional band

**No friction factor, no pressure drop, no outlet pressure.** Not zero, not
clamped, not interpolated. `64/Re` no longer holds there and Colebrook does not
yet apply, and a number between them would be a fabrication carrying the
authority of the two models it sits between.

The result object *enforces* this: constructing a transitional `LineResult`
with a friction factor raises. The velocity, Reynolds number, area and
geometry are still reported, because those are still valid.

---

## The turbulent correlation

```
1/sqrt(f_D) = -2 log10( eps/(3.7 D) + 2.51 / (Re sqrt(f_D)) )
```

Colebrook, J. Inst. Civ. Eng. **11** (1939) 133; domain from Moody, Trans. ASME
**66** (1944) 671.

**Solved, never approximated.** Haaland, Swamee-Jain and Blasius are explicit
approximations *to* this equation. They appear in the tests as sanity
comparisons and never as the production path, because an approximation
silently substituted for the model a result claims to use is a different model
wearing its name.

### How it is solved

Posed in `x = 1/sqrt(f_D)`, where the residual `g(x) = x + 2 log10(A + Bx)` has
derivative `1 + (2/ln10)·B/(A+Bx) > 0` — strictly increasing, so exactly one
root, which is what makes a fixed bracket safe rather than lucky.

| | |
| --- | --- |
| Bracket | `x` in [1, 30], i.e. `f_D` from 1.0 down to 1.1e-3 |
| Solver | `rocketforge.core.numerics.roots.brent` — the project's own, no SciPy |
| Tolerances | `xtol = 1e-13`, `rtol = 1e-14`, `max_iter = 100` |
| Worst observed | **15 iterations**, residual **4.4e-14** across 48 domain cases |

A non-converged solve returns `LINE_FRICTION_FACTOR_NOT_CONVERGED`. **No
approximation is substituted and the last iterate is not returned**: an
unconverged friction factor would carry the authority of a converged one.

---

## The fluid handshake

The request carries a `FluidState`. The package imports `core` and
`physics.fluids` and **nothing else in the project** — no provider, no CEA, no
CoolProp, no Qt, asserted per module.

It requires:

* an identified phase — `None` is refused and never assumed to be liquid;
* `LIQUID` — a gas is a compressible problem with different equations and a
  two-phase state has no single density at all;
* an **available** density and dynamic viscosity — neither is defaulted or
  estimated.

**`density_hint` is never read.** AST audit with a negative control.

---

## Pressure semantics

The fluid state's pressure **is** the line inlet / property-evaluation
pressure. It is a feed-system state.

**It is never a chamber pressure.** A static audit asserts no module in the
package reads `chamber_pressure`, with a negative control that fires on the
substitution, and the interface labels the field "Line inlet pressure".

```
p_out = p_in - dp
```

If `dp >= p_in` the result is `LINE_INSUFFICIENT_INLET_PRESSURE`, not a
negative or clamped pressure. That is not a hydraulic solution; it is the
statement that this flow cannot be driven through this line.

---

## Statuses

| Code | Meaning |
| --- | --- |
| — (OK) | solved |
| `LINE_TRANSITIONAL_REGIME_UNSUPPORTED` | warning; result present without a friction factor |
| `LINE_FLUID_STATE_UNUSABLE` | wrong phase, unknown phase, or a missing property |
| `LINE_OUTSIDE_MODEL_DOMAIN` | Re or ε/D beyond the correlation's declared range |
| `LINE_INSUFFICIENT_INLET_PRESSURE` | the loss exceeds the inlet pressure |
| `LINE_FRICTION_FACTOR_NOT_CONVERGED` | the Colebrook solve failed |

Malformed input — a zero or negative flow, length, diameter, a negative
roughness, a NaN — **raises**. Nothing is clamped and nothing is made absolute.
Zero flow and zero length are not solved as degenerate cases: the friction
relations are undefined there, and a zero pressure drop would be an answer to a
question nobody asked.

---

## The constant-property limitation

One density and one viscosity are used along the whole line. The model does
**not** integrate ρ(p) or μ(p) down the pipe.

Correct wording for what this is: a **steady single-phase constant-property
straight-line model**. Not a high-fidelity line solver, and not a
pressure-coupled hydraulic solver. The limitation is in the API docs, in the
result's `assumptions`, and on the screen.

---

## What is validated

| Check | Result |
| --- | --- |
| Reynolds identity, the two forms | residual **0.0** on the canonical case |
| Laminar Darcy-Weisbach vs Hagen-Poiseuille | worst **3.9e-16** |
| dp ∝ L, dp ∝ ṁ, dp ∝ D⁻⁴ | exact to 1e-12 |
| Laminar friction factor vs roughness | independent, bit-identical |
| Colebrook vs an independent Decimal bisection | 48 cases, worst **1.3e-14** |
| Colebrook residual | worst **4.4e-14** |
| Fully-rough limit vs the von Kármán law | within 2e-3 |
| Smooth-pipe case vs the Prandtl reduction | exact to 1e-12 |
| Fanning-instead-of-Darcy mutation | detected, 75 % error |
| Canonical LCH4 case vs independent recomputation | all fields ≤ **2.7e-16** |
| Line ρ and μ vs the fluid state's own | **bit-identical** |
| Determinism, A/B/A, recovery after refusal | exact |

Artifacts in `acceptance/transport_line/`.

---

## Performance

| | |
| --- | --- |
| Colebrook solves | ~118 000 / s |
| Full line solves | ~44 000 / s |
| 5 000-solve soak | +0.0003 MB retained |

Line algebra is far cheaper than chemistry, as it should be.

---

## Production fluids

A line result is offered only where the fluid's **density and viscosity are
both validated** at that state. Methane's envelope is 100–125 K and
0.5–3.0 MPa; oxygen and hydrogen carry their own. Outside it the workspace
reports `outside_transport_envelope` and presents no production result, even
though the provider would happily answer.

That gate lives in the application layer, not here: the line model is generic
and will solve any valid state. **What RocketForge is willing to claim is a
product decision, and product decisions belong to the composition root.**
