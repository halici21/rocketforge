# LIQ-5 — Combustion-chamber geometry and L*

LIQ-5 extends an accepted LIQ-4 sizing from the throat upstream to the
injector face. Given the sized throat and three stated design inputs, it
answers: what chamber volume, chamber diameter and injector-face-to-throat
geometry result? It does not design the injector, the feed system, the cooling
or the cycle, and it says nothing about combustion efficiency or stability.

## Where it lives

| Part | Location |
| --- | --- |
| The relations, once | `rocketforge/engineering/chamber_geometry/relations.py` |
| Throat basis, definition, result, JSON record | `rocketforge/engine/chamber_geometry.py` |
| Resolution, computation, presentation | `rocketforge/application/analysis/chamber_geometry_service.py` |
| QML singleton `ChamberGeometry` | `rocketforge/application/analysis/chamber_geometry_controller.py` |
| Page (Liquid Engine family, after Thrust Chamber Sizing) | `ui/pages/ChamberGeometryPage.qml` |

`06` section 2 assigns "L*, contraction ratio, residence time, chamber
volume" to `engineering.chamber`. That package is frozen as part of the
Rocket Performance API v1, so the geometry is its own package,
`engineering.chamber_geometry`, beside it (as `engineering.line` and
`engineering.propellants` are). The frozen package is unchanged. Residence
time is not implemented.

## Source

Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed., section 8.2,
"Volume and Shape" (pp. 285–287):

- Chamber volume is "the volume from injector face up to nozzle throat
  section so as to include the cylindrical chamber and the converging cone
  frustum of the nozzle", corner radii neglected.
- `L* ≡ Vc / At` (Eq. 8-9).
- Pressure losses ahead of the nozzle inlet "may become appreciable when the
  chamber area is less than three times the throat area" (item 6).
- "Typical values for L* are between 0.8 and 3.0 m … for several
  bipropellants", and chamber volume and shape are in practice chosen from
  prior successful chambers with the same propellants.

### Eq. 8-8 and the factor 1/3

Eq. 8-8 is printed as `Vc = A1 L1 + A1 Lc (1 + √(At/A1) + At/A1)`. The second
term is the frustum, and as printed it lacks the factor 1/3 of a frustum's
volume. The printed form contradicts itself. At `At = A1` the frustum is a
cylinder of length `Lc`, of volume `A1 Lc`, and the printed term gives
`3 A1 Lc`. LIQ-5 uses the geometric frustum volume, which is Eq. 8-8 with the
1/3 restored:

    V_conv = (π/3) L_conv (Rc² + Rc Rt + Rt²) = (A1 L_conv / 3)(1 + √(At/A1) + At/A1)

Huzel & Huang give the same volume in another closed form,
`(1/3) At Rt cot θ (εc^{3/2} − 1)`, and the tests use it as an independent
oracle. The 9th-edition worked example (section 8.9) does not use Eq. 8-8, so
it neither confirms nor contradicts the printed form.

## Inputs

| Input | Source | Domain | Default |
| --- | --- | --- | --- |
| At, Dt | the accepted LIQ-4 sizing, verbatim | — | — |
| L* | stated | > 0, finite | none |
| Ac/At | stated | > 1, finite | none |
| Converging half-angle θ | stated, from the axis | 0° < θ < 90° | none |

`throat_basis()` refuses each of these LIQ-4 states with a reason:

| LIQ-4 state | Code |
| --- | --- |
| nothing sized | `NO_SIZING` |
| the trade selection, the trade or the nozzle changed since sizing | `SIZING_STALE` |
| the sizing was refused (shock, no net thrust, …) | `SIZING_REFUSED` |
| no throat in the record | `SIZING_INCOMPLETE` |

An unstated input is `…_UNRESOLVED` and an out-of-domain one is `…_INVALID`.
Neither is clamped or replaced. The service and the relation check the same
domains, and a test checks that the two agree at every boundary.

## The geometry

A flat injector face, a cylinder of area `Ac`, and a straight cone to the
throat. All sections are circular and corner radii are neglected.

    Vc     = L* At
    Ac     = εc At,      Rc = √(Ac/π),     Rt = √(At/π)
    L_conv = (Rc − Rt) / tan θ
    V_conv = (π/3) L_conv (Rc² + Rc Rt + Rt²)
    V_cyl  = Vc − V_conv,       L_cyl = V_cyl / Ac
    L_inj  = L_cyl + L_conv

Reported closures are `((Ac L_cyl + V_conv)/At)/L* − 1` and
`π Rc² / (εc At) − 1`. Both are at rounding level.

**Refusal.** If `V_conv > Vc`, the convergent alone does not fit in the stated
volume. The geometry is refused, and the message gives both volumes and the
smallest L* this εc and θ admit, `V_conv / At`. Inputs are never adjusted. A
negative `V_cyl` within `1e-12 Vc` of zero is rounding at the exact boundary,
and is reported as a zero-length cylinder with a note.

## Advisories, not limits

| Condition | Severity | Basis |
| --- | --- | --- |
| Ac/At < 3 | warning: result shown, status "with advisories" | Sutton §8.2 item 6. The LIQ-4 ideal sizing neglects this loss. |
| L* outside 0.8–3.0 m | information | Sutton §8.2 typical bipropellant range. Not a validity limit. |

L* fixes a volume. LIQ-5 does not infer combustion completeness, efficiency
or stability from it, and it offers no default or optimum L*.

## Execution and state

Only **Compute** computes. It is pure algebra and does not reach the
provider. Opening the page, typing, clearing or retyping the inputs, theme,
size and re-entry compute nothing. Neither do changes upstream: a change in
the requirement, the trade or the sizing only re-announces the controller's
state. A result whose definition fingerprint no longer matches reads as
**stale**. The definition includes the LIQ-4 sizing's fingerprint and throat,
so re-sizing the same question keeps the geometry current, and a different
sizing makes it stale.

A result is immutable and round-trips through versioned JSON
(`schema: rocketforge.liquid-chamber-geometry`). Loading checks the recorded
definition fingerprint, so a hand-edited record is refused. The record holds
the throat basis with the sizing and trade identities and provenance, the
three stated inputs (the half-angle in radians, like every angle below the
application layer; the page states and shows degrees), every quantity in SI,
the unresolved reasons, the advisories, the model assumptions and the
provenance.

## Not in LIQ-5

- Injector and orifice design, atomization, combustion efficiency, combustion
  stability, residence (stay) time.
- Chamber pressure-loss correction (advised on, not modelled).
- Corner radii, contoured or tapered chambers, nozzle contour.
- Wall thickness, structures, materials, heat transfer, cooling.
- Feed pressure budget, pumps, turbines, preburners, and the GG, expander,
  staged or FFSC cycles.
- Tanks.
