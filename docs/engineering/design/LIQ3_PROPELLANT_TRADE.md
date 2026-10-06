# LIQ-3 — Propellant and operating-point trade

LIQ-3 answers one question for the current LIQ-2 engine requirement: how do the
available LIQ-1 propellant pairs compare at a stated operating point? It
evaluates each candidate through the accepted production chain, shows the
engineering quantities side by side, and lets the user choose one for the next
design stage. It compares concepts. It does not size an engine.

## Where it lives

| Part | Location |
| --- | --- |
| Definition, candidate result, trade result, JSON record | `rocketforge/engine/propellant_trade.py` |
| Resolution, evaluation, presentation | `rocketforge/application/analysis/propellant_trade_service.py` |
| QML singleton `PropellantTrade` | `rocketforge/application/analysis/propellant_trade_controller.py` |
| Page (Liquid Engine family, beside Engine Requirement) | `ui/pages/PropellantTradePage.qml` |

## The chain, called rather than copied

For each candidate:

1. The LIQ-1 preset gives the reactant keys. Each stream sits at its
   reactant's reference temperature, exactly as applying the preset does.
2. `thermochemistry_service.solve_case` runs the NASA CEA HP chamber
   equilibrium.
3. `reduce_chamber_gas` + `characteristic_velocity` give c*, at the stated
   gamma basis. These are the same two calls `solve_ideal_performance` makes,
   and a test asserts the two paths give the same c* bit for bit.
4. `performance_service.solve_performance` runs the ideal nozzle, only when
   the user has stated an area ratio. The ambient pressure is the
   requirement's design environment.
5. `mdot = F / c_eff`, split by O/F, multiplied by the burn time. This step
   runs only when `c_eff` is valid.

Under CEA, every candidate's chamber temperature, molar mass, c*, Isp and mass
flow are tested to be bit-identical to that chain run by hand.

## Nothing is resolved silently

| Requirement says | The trade |
| --- | --- |
| Chamber pressure target | uses it (`requirement target`) |
| Chamber pressure Auto | waits for a **study** chamber pressure from the user |
| Chamber pressure upper limit | waits for a study chamber pressure at or below the limit. The limit is not an operating point |
| O/F explicit | uses it for every candidate |
| O/F pair reference | uses the catalogue O/F of the chosen pair |
| O/F Auto | waits for the user to choose each candidate's catalogue O/F or one stated O/F. No O/F is optimised |
| Propellant Auto | every executable catalogue pair (12). The RFNA pairs are never candidates and nothing is substituted for them |
| Propellant explicit | that pair only: one chamber solve |

Requirement issues (LIQ-2) block the trade and are listed. A stated
requirement value always wins over a study value.

## The performance basis is stated

The requirement defines no nozzle, so none is assumed. The default basis is
**chamber only**. Cf, c_eff, Isp, exit pressure and every mass flow are then
shown as "—", each with the reason "No performance basis stated". With
**Ideal, stated Ae/At**, the user gives the area ratio. The comparison runs at
that ratio and the design ambient, with a single gamma (chamber strategy) at
the chosen frozen or equilibrium basis. The operating-assumptions panel and
the saved record carry all of it.

The ideal model's own refusals pass through. An area ratio that holds an
internal shock at the design ambient is refused by `solve_ideal_performance`,
and its message becomes the reason on every nozzle and flow quantity. The
chamber quantities still stand. Overexpansion warnings are kept as row notes.

## No score

The table has no ranking column, weight or "best". Sorting orders the rows by
one displayed column. Rows without that value follow in catalogue order, and
ties keep catalogue order. Choosing a pair is a click on a row. "Use for
Engine Requirement" then writes it back:

- the pair becomes the requirement's explicit pair;
- a catalogue O/F becomes *pair reference* if the requirement's O/F was Auto;
  a stated study O/F becomes the explicit O/F;
- a study chamber pressure becomes the target if the requirement's was Auto.
  An upper limit is kept as written.

A stale result (the requirement or the settings moved since the run) cannot
be applied.

## Execution and state

Only **Run trade** solves. It runs one candidate per event-loop turn, the
Trade Study pattern. Opening the page, editing a setting, sorting, selecting,
theme, size and re-entry neither solve nor probe the provider. The runtime
test counts every function below `application` and the gateway's
availability probe across that sequence and finds zero.

A result is immutable and round-trips through versioned JSON
(`schema: rocketforge.liquid-propellant-trade`). The record holds the
definition fingerprint and the provenance (CEA version, performance model,
catalogue source).

## Carried, not evaluated

Feed architecture and cycle preference travel in the requirement snapshot and
are shown as intent. Nothing reads them: the ideal chamber and nozzle figures
are the same for every cycle, and no cycle loss, feasibility check or power
balance exists. The service is tested to contain no reference to them.

## Not in LIQ-3

- Thrust-chamber and nozzle sizing: throat or exit dimensions, expansion-ratio
  design, chamber geometry, L*.
- Cycle feasibility, cycle losses, gas-generator or preburner flows, and
  pump/turbine power balance.
- Injectors, feed systems, cooling and tanks.
- Bulk density and density impulse are not reported. LIQ-2 records density
  impulse as a priority label only.
