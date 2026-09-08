> **Superseded.** This draft was promoted to [ROCKET_PERFORMANCE_API_V1.md](ROCKET_PERFORMANCE_API_V1.md) by Phase 5G and frozen as IDEAL ROCKET PERFORMANCE API v1.0. It is kept for history; the v1 document is normative.

# Rocket Performance — API

Phase 5E. The ideal rocket model: characteristic velocity, thrust coefficient,
momentum and pressure thrust, effective exhaust velocity, and specific impulse.

**RocketForge computes all of these itself.** A provider's own c\*, Cf and Isp
exist in this codebase and are reachable, but only as an oracle — see
[The oracle](#the-oracle-and-what-keeps-it-one) for what enforces that.

---

## Layers

```
physics.compressible        FROZEN. Quasi-1D gas dynamics.
        ^                   mass_flow, nozzle, isentropic — imported, never restated.
        |
engineering.chamber         The single-gamma handshake.
        |                   ChamberGas (two gammas, a composition) -> PerfectGas.
        v
engineering.nozzle          The performance equations.
        |                   c*, Cf, thrust, c_eff, Isp. No Qt, no provider, no chemistry.
        v
application.analysis        Case, outcome, display rows, provenance.
        |                   performance_service.py — Qt-free.
        v
application.analysis        The Qt facade.
                            performance_controller.py — the only file importing Qt.
```

`engineering.nozzle` runs with **no chemistry library installed**. A
subprocess test asserts this in a clean interpreter: import the chain, reduce a
chamber state, solve, verify the identities, and find no `cea`, `cantera` or
`CoolProp` entry in `sys.modules`.

---

## `engineering.chamber` — the handshake

A `ChamberGas` carries two isentropic exponents that differ by several per cent
on a real case, plus a composition and possibly a condensed fraction. A
`PerfectGas` carries one gamma and one R. Reducing the first to the second is a
modelling decision, so it is an explicit call with no default.

```python
reduce_chamber_gas(state, strategy, basis, *, chamber_pressure=None,
                   condensed_limit=SINGLE_PHASE_CONDENSED_LIMIT
                   ) -> Solution[ReducedChamberGas]
```

| Argument | Meaning |
| --- | --- |
| `strategy` | `GammaStrategy` — where along the flow gamma is taken |
| `basis` | `ChamberGammaBasis.FROZEN` (cp/cv) or `EQUILIBRIUM` (γ_s) |
| `condensed_limit` | The single-phase precondition. **A physics threshold**, unrelated to Phase 5D's presentation-only `CONDENSED_REPORTING_THRESHOLD`. |

`ChamberGammaBasis` exists because `GammaStrategy` alone is ambiguous: it says
*where* to take gamma, not *which of the two* to take. Adding it in the
engineering layer left every thermochemistry domain type untouched.

### Refusals

| Code | Cause |
| --- | --- |
| `CHAMBER_MODE_NOT_RECORDED` | the state does not say what chemistry produced it |
| `CHAMBER_STATE_NOT_PHYSICAL` | a non-positive temperature, gamma or gas constant |
| `CHAMBER_GAMMA_OUTSIDE_GAS_MODEL` | gamma outside `DEFAULT_TOLERANCES`, checked **before** `PerfectGas` so the caller gets a named refusal rather than an exception |
| `CHAMBER_GAS_CONSTANT_INCONSISTENT` | R and R_u/M disagree beyond `GAS_CONSTANT_IDENTITY_TOLERANCE` |
| `CONDENSED_FRACTION_UNKNOWN` | not reported, so single-phase cannot be established |
| `CONDENSED_PHASE_PRESENT` | above the limit; refused rather than averaged into the gas |
| `GAMMA_STRATEGY_UNAVAILABLE` | a strategy needing an expansion that has not been solved |

Info: `CONDENSED_TRACE_ACCEPTED` — a nonzero fraction below the limit, reported
with its exact value.

---

## `engineering.nozzle` — the equations

```python
characteristic_velocity(gas, stagnation_temperature) -> float
solve_ideal_performance(request: IdealPerformanceRequest
                        ) -> Solution[IdealRocketPerformance]
check_identities(result) -> IdentityReport
```

### c\*

```
c* = sqrt(R T0) / Gamma(gamma)
```

Derived from the frozen Phase 4 choked-flow physics — one substitution from
`c* = p_c A_t / mdot` — rather than written out again. `Gamma` is the
vandenkerckhove function already in `physics.compressible.mass_flow`.

Checked against an independent analytic form to **4e-16** across five gases.

### The exit state

From `nozzle.critical_pressure_ratios`, which needs no back pressure and
therefore works in a vacuum, where a back-pressure ratio of zero is outside the
classifier's domain. **Ambient pressure does not enter the internal solution**;
it enters the pressure-thrust term. Tests assert exact equality of the exit
Mach, pressure and velocity across ambient pressures.

### Regimes

Supported: `overexpanded`, `ideally_expanded`, `underexpanded` — one internal
solution, differing only in how p_e compares with p_a. At `p_a = 0` the regime
is `underexpanded` by definition rather than by classification.

Everything else — an internal normal shock, a shock at the exit plane, a choked
subsonic diverging section, an unchoked nozzle — is a **different internal
solution** and is refused with `NOZZLE_REGIME_UNSUPPORTED`, named.

### Thrust coefficient

```
Cf_momentum = V_e / c*
Cf_pressure = ((p_e - p_a) / p_c) * epsilon        signed, never clamped
Cf          = Cf_momentum + Cf_pressure
c_eff       = Cf * c*
Isp         = c_eff / g0                            SECONDS
```

`Cf_pressure` is negative for an overexpanded nozzle and stays negative. A
clamp would make an overexpanded engine look as good as an ideally expanded
one.

### Scale

| `PerformanceScaleMode` | Given | Derived |
| --- | --- | --- |
| `NORMALIZED` | nothing | c\*, Cf, c_eff, Isp only |
| `THROAT_AREA` | A_t [m²] | mdot from the choked-flow relation |
| `MASS_FLOW` | mdot [kg/s] | A_t = mdot·c\*/p_c |

`NORMALIZED` is not a degraded mode. It is the statement that no engine size
was given, and thrust, mass flow and the areas are `None` — **never zero**,
because zero thrust is a claim about an engine rather than the absence of one.

The two sized modes are round-trip consistent to 1e-12.

### Identities

`check_identities` recomputes 6 scale-free and 9 scaled relations at
`IDENTITY_TOLERANCE = 1e-12`. Worst observed residual across the test matrix:
**3.7e-16**.

Internal consistency is not validation, and the interface says so on the panel
that shows it.

---

## `application.analysis.performance_service` — Qt-free

```python
solve_performance(chamber: ChamberOutcome | None,
                  case: PerformanceCase) -> PerformanceOutcome
```

Never raises. Seven outcome kinds: `ok`, `warning`, `no_chamber`,
`reduction_refused`, `nozzle_refused`, `invalid_input`, `empty`.

### Zero chemistry re-solve — blocking

The chamber state is an **argument**. This module imports neither
`rocketforge.providers` nor the provider gateway, so no expression in it can
start a chemistry solve. Changing an area ratio, an ambient pressure, an engine
size, a gamma basis or a gamma strategy costs **0** provider calls, measured by
a call-counting stub in the service tests, again through the Qt controller, and
again in the packaged executable.

### Reference conditions

```python
reference_condition_results(outcome) -> {"vacuum": ..., "optimum": ...}
```

Re-solves the **nozzle** at each reference condition a provider quotes,
reusing the gas reduction object by identity. Needed because CEA quotes Cf and
Isp at optimum expansion: comparing a vacuum figure against one of those is
wrong by the whole pressure term — 5.6 % on a LOX/LH2 case at Ae/At 40, larger
than any model difference such a table exists to show.

### Provenance

`performance_provenance` returns exactly **two** rows and never merges them:

| Role | Computed by |
| --- | --- |
| Ideal performance (c\*, Cf, c_eff, Isp, thrust) | RocketForge |
| Chamber equilibrium (T₀, R, gamma, composition) | the provider named on the result |

A test asserts the RocketForge row names no chemistry library, in any field.

---

## The oracle, and what keeps it one

`CEAThermochemistryProvider.rocket_oracle(request, *, area_ratio,
expansion_mode)` returns CEA's own c\*, Cf and Isp.
`application.analysis.performance_oracle.run_oracle` wraps it for display.

Four properties keep it from becoming the implementation:

1. **Different types.** `OracleOutcome` carries plain floats under their own
   names. It is not an `IdealRocketPerformance` and the two do not interchange.
2. **No import path.** `performance_service` does not import
   `performance_oracle`. The module computing RocketForge's fields cannot see
   the provider's.
3. **Explicit invocation.** It runs only from a user action. No nozzle input
   reaches it — which is also why the zero-re-solve property survives having an
   oracle in the workspace.
4. **Separate CEA run.** A chamber state carries no performance figure, and
   this cannot be derived from one.

---

## What is not here

No combustion efficiency, no c\* or Cf efficiency, no divergence, viscous,
boundary-layer or separation correction, no two-phase term, no finite-rate
chemistry, no composition shift through the nozzle, no chamber geometry, no
injector, no cooling, no optimisation.

An ideal figure is an **upper bound** on a real engine, and every result
carries `IDEAL_MODEL_ASSUMPTIONS` saying so.
