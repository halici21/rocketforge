# SYS-1 — Propellant inventory

SYS-1 answers, for each propellant branch: *how much propellant must be loaded
to support this engine's burn?* It takes the accepted LIQ-4 sizing's oxidiser
and fuel flows and the LIQ-2 requirement's burn time, and keeps a mass budget
per branch: usable, available, residual and loaded propellant.

It is a mass budget. It has no density, volume, ullage, tank geometry,
pressurization or cycle flow.

## Where it lives

SYS-1 is the first propulsion-system (stage-level) gate. It sits beside the
liquid-engine records rather than inside them.

| Part | Location |
| --- | --- |
| Inventory relations | `rocketforge/engineering/propulsion_system/inventory.py` |
| Shared study, branch and ledger records | `rocketforge/engine/propulsion_system/records.py` |
| Basis, definition, quantities | `rocketforge/engine/propulsion_system/inventory.py` |
| Resolution, computation, presentation | `rocketforge/application/analysis/propellant_inventory_service.py` |
| QML singleton `PropellantInventory` | `rocketforge/application/analysis/propellant_inventory_controller.py` |
| Shared SYS controller and display rows | `system_study_controller.py`, `system_presentation.py` |
| Page (new **Propulsion System** family) | `ui/pages/PropellantInventoryPage.qml` over `ui/components/RFSystemWorkspace.qml` |

## Sources

All from Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed.

**§6.2, p. 196.** "The expulsion efficiency of a tank and/or propellant piping
system is the amount of propellant that can be expelled or available for
propulsion divided by the total amount of propellant initially present." The
loss is "unavailable propellants left in tanks after rocket operation, trapped
in grooves or corners of pipes, fittings, filters, and valves, or wetting the
walls". Sutton quotes typical values of 97 to 99.7 %. SYS-1 does not use them.

**§11.1, pp. 399–401, the propellant budget.** The load is "always somewhat
greater than the nominal amount of propellant needed". The extra covers
residual propellant (item 6, typically 0.5–2 % of the load), loading
uncertainty (7), off-nominal allowances (8, 9), evaporation and cool-down (10)
and contingency (11). **Example 11-1** forms the load as the nominal flow ×
burn time × (1.00 + 0.01 + 0.06), for a 1 % residual and a 6 % reserve.

**Example 6-1, p. 196** allows "two additional seconds for start and stop
transients and unavailable residual propellant". This is where the
start/shutdown allowance comes from.

## Inputs

**From upstream, verbatim (`InventoryBasis`):**
- LIQ-4: ṁo, ṁf, ṁ, O/F, chamber pressure, stream temperatures, the
  sizing's identity;
- LIQ-2, through the LIQ-3 trade that the sizing extends: the burn time.

`inventory_basis()` refuses these states:

| Upstream state | Code |
| --- | --- |
| nothing sized | `NO_SIZING` |
| sizing stale | `SIZING_STALE` |
| sizing refused | `SIZING_REFUSED` |
| no flows in the record | `SIZING_INCOMPLETE` |
| trade missing, stale, or not the one the sizing extends | `TRADE_MISMATCH` |
| trade's requirement is not the sizing's | `REQUIREMENT_MISMATCH` |

LIQ-3 already refuses a requirement without a burn time, so no inventory can
exist without one. None is assumed.

**Stated per branch.** None has a default; everything starts unresolved.

| Input | Modes |
| --- | --- |
| Unavailable propellant | expulsion efficiency η (0 < η ≤ 1) · residual mass (tank residual + trapped-line mass, each stated / n.a. / unresolved) · unresolved |
| Reserve | stated mass · stated fraction of the usable mass · not applicable · unresolved |
| Start and shutdown transients | stated kg · n.a. · unresolved |
| Chill-down through the engine | stated kg · n.a. · unresolved |
| Other stated allowance | stated kg · n.a. · unresolved |
| Boil-off before the burn | stated kg · n.a. · unresolved |

## Bookkeeping

    m_usable    = ṁ t
    m_available = m_usable + transients + chill-down + other + reserve
    m_present   = m_available / η              (η stated)
                = m_available + m_residual     (residual stated)
    m_residual  = m_present − m_available
    m_loaded    = m_present + m_boiloff

- **η covers tank and piping.** This follows Sutton's definition. In η mode
  no separate trapped-line mass is added; the record says it is covered.
- **η derived.** In residual-mass mode, η = m_available / m_present.
- **Boil-off is not divided by η.** It leaves the tank before the burn and
  is never present for expulsion.
- **Unresolved is never zero.** Each loaded total is given only when every
  term is resolved. The minimum known load, the sum of the resolved terms, is
  always given. In η mode it is the known available mass divided by η. Every
  term is non-negative, so the load is at least this.
- **No cycle flows.** Only the thrust-chamber flows exist upstream. No
  gas-generator, tank-pressurization bleed or auxiliary flow is added. When a
  cycle exists, its flows will come from that gate and will not be counted
  here twice.

## Closures

- Balance: (available + residual + boil-off)/loaded − 1.
- Efficiency: (present − residual)/present/η − 1.
- Usable O/F against the LIQ-4 O/F.
- Usable total against ṁ t.

All of these are at rounding level.

## Execution and state

- **Only Compute computes.** Opening the page, editing, and changes upstream
  compute nothing. A change upstream re-announces the state, and the result
  then reads as stale.
- **The record** round-trips through versioned JSON
  (`schema: rocketforge.propellant-inventory`) and is fingerprint-checked.

## Verified

- **Relations.** ṁ t exactly; η inversion over a grid; Example 11-1's
  1.07 ṁ t; balance and efficiency closures ≤ 5 × 10⁻¹⁶ over a
  216-case grid; unresolved terms give a lower bound, not a zero.
- **Service.** The stale, refused and mismatched upstream states above;
  every invalid input refused, not clamped; branches distinct, with different
  budgets; unresolved terms propagate to the totals.
- **Runtime.** In the running application, browsing computes nothing;
  Compute reaches the inventory relation and no provider; a new nozzle on the
  sizing page makes the result stale.

## Not in SYS-1

- Density, volume, ullage, tanks (SYS-2).
- Propellant management (SYS-3).
- Pressurant (SYS-4).
- Feed lines (SYS-5).
- Gas-generator and other cycle flows; mission Δv and attitude-control
  budgets; mixture-ratio-variation allowances derived from engine data. Any of
  these can be entered as a stated allowance.
