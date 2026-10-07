# LIQ-6 — Injector hydraulics and feed pressure budget

LIQ-6 takes an accepted LIQ-4 sizing's oxidiser and fuel flows and answers two
questions for each propellant branch:
1. What total injector flow area, and what injection velocity, does the branch
   need?
2. What upstream pressure must the branch supply to sustain the chamber?

It sizes hydraulics and keeps a pressure ledger. It does not design injector
elements, a feed system or a cycle. It says nothing about atomization,
combustion efficiency or combustion stability.

## Where it lives

| Part | Location |
| --- | --- |
| Orifice, hole and dynamic-head relations | `rocketforge/engineering/injector/hydraulics.py` |
| Branch pressure ledger | `rocketforge/engineering/injector/pressure_budget.py` |
| Flow basis, definition, result, JSON record | `rocketforge/engine/injector.py` |
| Resolution, density source, computation, presentation | `rocketforge/application/analysis/injector_service.py` |
| QML singleton `Injector` | `rocketforge/application/analysis/injector_controller.py` |
| Page (Liquid Engine family, after Chamber Geometry) | `ui/pages/InjectorPage.qml` |

## Sources

All from Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed.

**§8.1, "Injector Flow Characteristics" (pp. 280–282).** Incompressible flow
through hydraulic orifices:

    Q    = Cd A √(2Δp/ρ)          (Eq. 8-1)
    ṁ    = Q ρ = Cd A √(2ρΔp)     (Eq. 8-2)
    r    = ṁo/ṁf                  (Eq. 8-3, from Eq. 8-2 per branch)
    v    = Q/A = Cd √(2Δp/ρ)      (Eq. 8-5)

A is "the cross-sectional area of the orifice", and Δp is "the pressure drop
across the injector elements". Solved for A, it is the cumulative orifice area
of one propellant, which is how §8.9 uses it.

**§10.4, Eq. 10-7 (p. 377).** The pressure a branch supplies "has to equal the
chamber pressure p1 modified by all the pressure drops" downstream of it. The
text names those drops: "cooling jacket, injector, piping, and … open fuel
valve".

**§11.5, Eqs. 11-6 and 11-7 (p. 423).** For a pressurized branch:

    p_gas − Δp_gas = p1 + Δp(piping, valves) + Δp_inj + Δp_j + ½ρv² − Laρ

The text adds: "a good design should provide extra pressure drop margins"
for calibration orifices.

### The §8.9 worked example is √2 off its own Eq. 8-2

The example takes 10.749 kg/s LOX and 4.387 kg/s RP-1, Δp = 0.965 MPa,
Cd = 0.80, and Table 7-1's specific gravities of 1.14 and 0.807.

| Branch | Sutton prints | Eq. 8-2 gives | Ratio |
| --- | --- | --- | --- |
| Oxidiser | 4.098 cm² | 2.865 cm² | 1.431 |
| Fuel | 1.98 cm² | 1.390 cm² | 1.425 |

Both ratios are √2 (1.414) within the rounding of the densities. The example
evidently computed ṁ/(Cd√(ρΔp)). Its hole counts (130 oxidiser holes of
2.00 mm, 100 fuel holes of 1.5 mm) follow from its own areas.

LIQ-6 follows Eqs. 8-1, 8-2 and 8-5 as printed. They agree with each other and
with Bernoulli for the ideal jet, ½ρ(v/Cd)² = Δp. A test records the example's
discrepancy. This is the same treatment LIQ-5 gave Eq. 8-8's missing 1/3: the
equations are kept, and the inconsistent arithmetic is documented.

## Inputs

**From the accepted LIQ-4 sizing, verbatim (`FlowBasis`):**
- ṁo, ṁf and ṁ;
- O/F;
- chamber pressure p1;
- the LIQ-3 stream temperatures;
- the propellant names;
- the sizing and trade identities.

`flow_basis()` refuses these states:

| LIQ-4 state | Code |
| --- | --- |
| nothing sized | `NO_SIZING` |
| stale | `SIZING_STALE` |
| refused | `SIZING_REFUSED` |
| no flows in the record | `SIZING_INCOMPLETE` |

**Stated per branch.** None has a default.

| Input | Domain |
| --- | --- |
| Injector pressure drop Δp | > 0 |
| Discharge coefficient Cd | 0 < Cd ≤ 1. Not inferred from an element type: Table 8-2's ranges depend on the particular hole. |
| Density | stated, > 0, or the validated fluid model (below) |
| Orifice split | total area only; or a hole count N (whole, ≥ 1) giving the equal-hole diameter; or a hole diameter d (> 0) giving the equivalent count |
| Pressure terms | each one stated (≥ 0), not applicable, or unresolved |

An unstated hydraulic input is `…_UNRESOLVED`, and an out-of-domain one is
`…_INVALID`. Both block Compute. Nothing is clamped.

### Liquid density

Density is never read from the CEA chamber state. There are two sources:
- **Stated.**
- **Validated fluid model.** It is available only for propellants with a
  validated binding (`engineering.propellants.PRODUCTION_FLUID_MAPPING`: LOX,
  LCH4, LH2). It goes through `stream_density()` and CoolProp. The state is
  the LIQ-3 stream temperature at the injector inlet, p1 + Δp. Provider,
  version, state and phase are recorded with the result.

The binding is validated for the **liquid** phase, and a state in any other
phase is refused, not converted. At typical injector inlet pressures this
matters. For example, LOX at 90 K and 12 MPa is above oxygen's critical
pressure (5.04 MPa), and CoolProp classes it as supercritical. In that case
the fluid model refuses the branch, gives the provider's reason, and asks for
a stated density. Below the critical pressure it evaluates.

A branch heated before the injector, such as a regenerative coolant, is not at
the LIQ-3 temperature, so its density should be stated. The provider is
reached only when Compute is pressed. It is absent in the base environment,
where the branch is refused with the install remedy.

## Hydraulics

For each branch:

    A        = ṁ / (Cd √(2ρΔp))
    v        = Cd √(2Δp/ρ)
    Q        = ṁ/ρ,     Cd·A,     Δp/p1
    N stated : d = √(4A/(πN))
    d stated : N = A/(πd²/4)  (exact, may be fractional)

**Whole holes.** With N rounded up, the area is A_whole = N_whole·πd²/4, and
at the same flow Eq. 8-2 gives Δp_whole = Δp(A/A_whole)². Both the exact and
the whole-hole values are reported, and neither replaces the other. A hole
larger than the whole required area is a warning.

**Closures**, all at rounding level:
- Cd·A·√(2ρΔp)/ṁ − 1;
- ρvA/ṁ − 1;
- N·πd²/4/A − 1.

**Pair closures.** From each branch's own orifice, ṁ' = Cd·A·√(2ρΔp). Then
O/F' = ṁo'/ṁf' (Eq. 8-3) is closed against the LIQ-4 O/F, and ṁo' + ṁf' is
closed against the LIQ-4 ṁ.

**Δp/p1** is reported because it is stability-relevant. Stability is not
evaluated. Sutton §8.9 quotes 15–25 % of p1 as usual practice; LIQ-6 neither
applies that nor checks against it.

## Pressure ledger

Each branch's ledger, in order:

| Term | Source |
| --- | --- |
| Chamber pressure p1 | LIQ-4, always resolved |
| Injector pressure drop | stated, always resolved |
| Feed-line loss | stated / n.a. / unresolved |
| Valves and components | stated / n.a. / unresolved |
| Cooling-jacket loss | stated / n.a. / unresolved |
| Dynamic flow head ½ρv² | stated / from a line diameter D (v = ṁ/(ρπD²/4)) / n.a. / unresolved |
| Other stated losses | stated / n.a. / unresolved |
| Design / calibration margin | stated / n.a. / unresolved |

- **Minimum known upstream pressure** is the sum of the resolved terms. Every
  term is non-negative, so the requirement is at least this.
- **Required upstream pressure** is the same sum, reported only when no term
  is unresolved. Otherwise it is absent, and the reason lists the unresolved
  terms.
- **Unresolved is never zero.** A term the user does not know stays visible
  as UNRESOLVED. "Not applicable" is a separate, explicit declaration.
- **Static head is not credited.** Laρ needs a liquid level and a flight
  acceleration, which are not known here. The required pressure is at the
  branch's own reference point, a pump discharge or tank outlet, as the user's
  terms define it.

## Execution and state

Only **Compute** computes. Opening the page, editing, switching density
source, hole mode or term status, theme, size and re-entry compute nothing.
Changes upstream only re-announce the controller's state. A runtime test wraps
every lower-layer function and both provider gateways, and shows:
- zero calls while browsing;
- exactly two orifice relations and no provider call on Compute with stated
  densities;
- staleness after a change in the sizing.

A result is immutable and round-trips through versioned JSON
(`schema: rocketforge.liquid-injector`). Loading checks the definition
fingerprint, so a hand-edited record is refused. The record holds the flow
basis, every stated input in SI, every quantity, the full ledger with each
term's status, source and reason, the density provenance, the assumptions and
the provenance chain.

## Verified

- **Hand calculations.** Area, velocity, hole diameter and count, whole-hole
  Δp, and dynamic head. Bernoulli as an independent oracle. The §8.9 example's
  √2 discrepancy is pinned.
- **Scaling.** A ∝ ṁ, A ∝ Δp^−½, A ∝ ρ^−½, v ∝ Δp^½, and v independent of ṁ.
- **A 3 072-case grid** through the service: 4 chamber pressures × 4 O/F ×
  3 flows × 64 hydraulic combinations, with randomised ledgers and hole modes.
  Area, velocity, hole, ledger, O/F and total-flow closures are all ≤ 6 × 10⁻¹⁶.
  The ledger is complete exactly when no term is unresolved.

## Not in LIQ-6

- Injector element design (impinging, coaxial, swirl, pintle), patterns,
  manifolds, element counts per element type.
- Atomization and SMD, mixing, combustion efficiency, combustion stability.
- Cavitation and NPSH, feed-line friction models, valve models.
- Pumps, turbines, preburners, tanks, pressurant; the GG, expander, staged and
  FFSC power balances.
- Cooling-channel design; regenerative heating of the coolant.
- Injector thermal and structural design.
- Transients and throttling.
