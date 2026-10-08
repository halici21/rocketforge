# SYS-5 — Liquid propellant feed network foundation

For each branch, SYS-5 builds an explicit series of components from the tank
outlet to the LIQ-6 injector inlet. It computes the first-order hydraulic
pressure change of each component and closes the result on the injector's
pressure requirement and the SYS-4 tank pressure. Where a validated
component model exists, it replaces LIQ-6's opaque feed-line and valve
terms. Where none exists, the term stays explicit, either as an unresolved
component or a stated loss.

## Where it lives

| Part | Location |
| --- | --- |
| Component relations, series solve | `rocketforge/engineering/propulsion_system/feed_network.py` (reuses `engineering.line`) |
| Basis, definition, quantities | `rocketforge/engine/propulsion_system/feed_network.py` |
| Resolution, closure, computation | `rocketforge/application/analysis/feed_network_service.py` |
| QML singleton `FeedNetwork` | `rocketforge/application/analysis/feed_network_controller.py` |
| Page | `ui/pages/FeedNetworkPage.qml` |

## Components

Steady, single-phase and incompressible, at one density and viscosity. One
mass flow passes through every component in series, and continuity is
checked per component as ρvA/ṁ − 1.

| Kind | Inputs | Pressure change |
| --- | --- | --- |
| Pipe | L, D, ε | f (L/D) ρv²/2, with the Darcy f of `engineering.line`: 64/Re laminar, Colebrook–White turbulent, none in 2300 ≤ Re < 4000 |
| Local loss, valve, check valve | K, D | K ρv²/2, with K referred to the velocity at D |
| Filter, explicit loss | Δp | stated |
| Static head | Δz, a | ρ a Δz. Δz is the rise against the acceleration: positive is a loss, negative a gain (Sutton Eqs. 11-6, 11-7, *Laρ*) |
| Velocity head | D | ρv²/2 at the injector inlet: the liquid accelerated from rest in the tank. Last component only |
| Unresolved | — | unresolved, never zero |

**Inputs.**
- Only the resistance coefficient K is accepted. Flow coefficients (Cv, Kv)
  come in several unit conventions.
- No roughness, K, diameter, length or viscosity is defaulted. A pipe needs
  a stated viscosity.

**Fluid.**
- The density is LIQ-6's injector-inlet density, or stated.
- Viscosity has no validated feed-state source here, so it is stated.

**Topology.** A network must have at least one component, and the velocity
head may only be last. Otherwise the network is refused. Parallel branches
are not modelled.

## Closure with LIQ-6, without double counting

LIQ-6's ledger terms are assigned by where they lie relative to the network:

| LIQ-6 term | Here |
| --- | --- |
| chamber pressure, injector Δp, cooling jacket, margin | carried at the injector inlet |
| feed-line loss, valves | always **replaced**. Recorded as excluded, with their LIQ-6 value, and not counted |
| dynamic head, other losses | carried or replaced, **as stated**. No default |

Carrying the dynamic head while also modelling a velocity-head component
would count ρv²/2 twice, so that combination is refused (`DOUBLE_COUNTED`).

    p_inlet,req = Σ carried LIQ-6 terms
    p_tank,req  = p_inlet,req + Σ network
    margin      = p_tank − p_tank,req      (regulated; blowdown at start and end)

- **Closure.** ((p_tank − Σ network) − p_inlet,req − margin)/p_tank is
  reported. It sits at rounding level.
- **Comparison.** LIQ-6's own required pressure is shown beside the result,
  including the terms that are not counted here.
- **Unresolved inputs.** A carried term that is unresolved in LIQ-6, or an
  unresolved component, keeps the requirement and margins unresolved. The
  resolved network drop is still given.
- **Tank-outlet pressure.** The tank outlet's static pressure is the SYS-4
  tank pressure. The liquid column is credited only through a stated
  static-head component.
- **Blowdown.** A blowdown is checked at its start and end pressures at the
  design flow.

## Upstream

`feed_basis()` refuses:

| State | Code |
| --- | --- |
| no SYS-4 study | `NO_PRESSURIZATION` |
| SYS-4 stale | `PRESSURIZATION_STALE` |
| SYS-4 refused | `PRESSURIZATION_REFUSED` |
| no LIQ-6 study | `NO_INJECTOR` |
| LIQ-6 stale | `INJECTOR_STALE` |
| LIQ-6 refused | `INJECTOR_REFUSED` |
| LIQ-6 on another sizing | `INJECTOR_MISMATCH` |

## Verified

- **Laminar pipe.** Matches Hagen–Poiseuille.
- **Turbulent pipe.** Matches a separately iterated Colebrook–White to
  10⁻¹⁰.
- **Components by hand.** K ρv²/2 and the static-head sign, with series
  summation.
- **Unresolved and transitional components.** They propagate as unresolved.
- **Refusals.** Invalid topology and out-of-domain components.
- **Grid.** 243 cases (flow × diameter × roughness × K × rise): continuity
  ≤ 5 × 10⁻¹⁶, and the series sum is exact.
- **No double counting.** LIQ-6's feed terms are excluded, and the
  double-counted dynamic head is refused.
- **Branch closure.** Pressure closure ≤ 10⁻¹⁴.
- **Upstream.** Stale and mismatched upstream results are refused.
- **Records.** JSON round-trip with a fingerprint check.

## Not in SYS-5

- Two-phase flow, cavitation and NPSH closure.
- Water hammer and transients, valve dynamics, flexible-line dynamics.
- Thermal coupling.
- Turbopumps and cooling-channel hydraulics.
- Parallel networks, and Cv/Kv conventions.
