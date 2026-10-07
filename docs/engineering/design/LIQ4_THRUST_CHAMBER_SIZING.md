# LIQ-4 — Thrust-chamber and nozzle sizing

LIQ-4 turns the operating point selected in a LIQ-3 propellant trade into an
ideal thrust-chamber design point: propellant flow, throat size and nozzle
exit size, with the performance and exit state they follow from. It sizes the
ideal throat and exit. It does not design the combustion chamber, the
injector, the feed system, the cooling or the cycle.

## Where it lives

| Part | Location |
| --- | --- |
| Operating point, definition, result, JSON record | `rocketforge/engine/chamber_sizing.py` |
| Resolution, sizing, presentation | `rocketforge/application/analysis/chamber_sizing_service.py` |
| QML singleton `ChamberSizing` | `rocketforge/application/analysis/chamber_sizing_controller.py` |
| Page (Liquid Engine family, after Propellant Trade) | `ui/pages/ChamberSizingPage.qml` |

## Who owns what

| Stage | Owns | LIQ-4 reads |
| --- | --- | --- |
| LIQ-1 | chemistry (CEA chamber) | through the same `solve_case` |
| LIQ-2 | requirement | target thrust, design ambient, from the trade's snapshot |
| LIQ-3 | the resolved operating point | the selected candidate, verbatim |
| LIQ-4 | sizing derived from that point | — |

`OperatingPoint` copies the selected candidate as LIQ-3 recorded it. That
covers the pair and its reactant keys, the O/F, the chamber pressure, the
stream temperatures, the gamma basis and the source of each. It also keeps
the requirement's thrust and ambient as the trade held them, the trade's
fingerprint and provenance, and every metric LIQ-3 recorded. LIQ-4 does not
re-decide any of these.

## The input it accepts

`operating_point()` refuses with a stated reason in each of these cases:

| State of the trade | Code |
| --- | --- |
| no trade run | `NO_TRADE` |
| the requirement or trade settings changed since it ran | `TRADE_STALE` |
| no candidate selected | `NO_SELECTION` |
| the selection did not solve | `SELECTION_FAILED` |

The nozzle design input is an explicit **area ratio Ae/At**, the input the
accepted ideal model takes. It comes from one of two places:

- **The trade's nozzle.** If the trade was evaluated with a stated Ae/At, that
  value is used and the source is recorded as `trade`.
- **Stated for the sizing.** If the user types a value, it is used and the
  source is recorded as `sizing`. A chamber-only trade requires one
  (`AREA_RATIO_UNRESOLVED`).

No optimum expansion (`pe = pa`) is assumed. A stated exit-pressure design
basis is not offered; see the limitations below.

## The chain, called rather than copied

1. **Replay.** `thermochemistry_service.solve_case` runs the selected
   candidate's exact `ChamberCase`: the same reactant keys, O/F, chamber
   pressure and stream temperatures. A LIQ-3 record holds numbers, not the
   chamber state (gamma, R, T0) the ideal nozzle needs, so the chamber is solved
   once more, and only on the explicit Size action.
2. **Check.** The replay must reproduce LIQ-3's recorded chamber temperature,
   molar mass and c* **bit for bit**. When sizing at the trade's own nozzle, Cf,
   c_eff, Isp and mass flow must match too. Any difference refuses the
   sizing: the chain is no longer the one that produced the trade, and the two
   are not mixed.
3. **Unit nozzle.** `performance_service.solve_performance`, unscaled, at the
   stated Ae/At and the design ambient, with a single gamma (chamber strategy)
   at the trade's basis. This gives c_eff.
4. **Flow.** `mdot = F / c_eff`, split by O/F.
5. **Scaled nozzle.** `solve_performance` again with `PerformanceScale(MASS_FLOW,
   mdot)`. The accepted model gives `At = mdot c*/pc`, `Ae = At · Ae/At`, the
   exit state, and the momentum and signed pressure thrust.
6. **Diameters.** `D = sqrt(4A/π)` for circular sections.

No compressible-flow or rocket relation is restated. Steps 3 and 5 are pure
algebra on the solved chamber; neither touches the provider.

## Thrust closure

The calculated thrust is the momentum thrust plus the pressure thrust of the
sized engine. `thrust_closure = F_calc / F_target − 1` is reported. Tests
require `|closure| ≤ 1e-12`, sea level and vacuum. They also check that
`F = mdot · c_eff = Cf · pc · At`.

## The solver's behaviour is kept

- **Internal shock.** A nozzle that holds an internal shock at the design
  ambient is refused by `solve_ideal_performance`. Its message, which names the
  regime, becomes the reason on every quantity, and the sizing is `REFUSED`
  with no numbers.
- **Overexpansion.** An overexpanded nozzle keeps its negative pressure thrust
  and pressure-term Cf. The model's own notes come through unchanged: the
  oblique-shock and separation flags and the signed pressure-term note. The
  regime is shown.
- **No net thrust.** A nozzle with `c_eff ≤ 0` at the design ambient is refused:
  no mass flow meets the target there.

## Execution and state

Only **Size** solves, and it costs one chamber solve. Opening the page, typing
or clearing the area ratio, theme, size and re-entry neither solve nor probe
the provider. Neither do changes in the trade or the requirement. A change
upstream only re-announces the controller's state. A result whose definition
fingerprint no longer matches the current trade selection and area ratio reads
as **stale**. The runtime test counts every function below `application` and
the gateway probe across that sequence, and finds zero.

A result is immutable and round-trips through versioned JSON
(`schema: rocketforge.liquid-thrust-chamber-sizing`). The record holds the
operating point with the trade fingerprint and provenance, the area ratio and
its source, every quantity in SI, the unresolved reasons, the regime, the
solver notes, the model assumptions and the provenance.

A typical flow is: run the trade, select a candidate, then size. Applying the
selection to the Engine Requirement (LIQ-3) changes the requirement, which
makes the trade stale. Run the trade again before sizing. With the pair now
explicit, that is one chamber solve.

## Carried, not evaluated

Feed architecture and cycle are not read. The ideal design point is the same
for every cycle, and the service and controller are tested to contain no
reference to them.

## Not in LIQ-4

- Combustion-chamber diameter, volume, contraction ratio or geometry, and L*
  (LIQ-5).
- Injector sizing or pressure drop, feed pressure budget, pumps, turbines and
  preburners.
- Gas-generator, expander, staged or full-flow staged-combustion feasibility,
  and power balance.
- Cooling and heat transfer, tanks, structural sizing.
- Nozzle contour, length, or optimisation of any kind.
- Efficiency factors (c*, Cf, divergence). The ideal model applies none.
- Design-exit-pressure basis. Sizing for a stated pe (including `pe = pa`)
  would need the area ratio derived from a pressure ratio. That is not offered
  in this stage, so the area ratio must be stated.
