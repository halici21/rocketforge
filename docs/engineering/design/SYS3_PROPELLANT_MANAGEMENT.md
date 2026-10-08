# SYS-3 — Propellant management foundation

SYS-3 records, for each branch, what keeps liquid propellant at the tank
outlet, and keeps first-order books on the liquid and gas volumes from
loading to the end of the burn. It reads a complete SYS-1 inventory and the
current SYS-2 tanks built from it.

**It states intent and checks it for consistency; it proves nothing.** No
device performance, settling time, capillary retention or slosh dynamics is
computed. Full slosh dynamics are left to a future vehicle-dynamics gate.

## Where it lives

| Part | Location |
| --- | --- |
| Semantics and volumes | `rocketforge/engineering/propulsion_system/propellant_management.py` |
| Basis, definition, quantities | `rocketforge/engine/propulsion_system/management.py` |
| Resolution, computation | `rocketforge/application/analysis/propellant_management_service.py` |
| QML singleton `PropellantManagement` | `rocketforge/application/analysis/propellant_management_controller.py` |
| Page | `ui/pages/PropellantManagementPage.qml` |

## Sources

Sutton & Biblarz, 9th ed., §6.2, pp. 199–203, and Table 6-2:

- In zero g, liquids "may not always cover the tank outlet".
- Positive-expulsion devices are "movable pistons, inflatable flexible
  bladders, or thin movable and flexible metal diaphragms".
- Surface-tension devices "work best in relatively low-acceleration
  environments".
- "a small acceleration may be applied ... to orient the liquid".

Table 6-2 rates the devices qualitatively ("Excellent" … "Poor") for
hydrazine spacecraft tanks. It is not used numerically, and **no expulsion
efficiency is assigned from a device type**.

## Inputs

**From upstream, verbatim (`BranchStorage`).**
- SYS-1: loaded, present, available, residual and boil-off masses, and η
  with its source (stated or derived).
- SYS-2: storage density, tank volume, ullage and fill.
- The chain's sizing identity.

`management_basis()` refuses these states:

| Upstream state | Code |
| --- | --- |
| inventory missing or incomplete | `INVENTORY_INCOMPLETE` |
| inventory stale | `INVENTORY_STALE` |
| no tanks | `NO_TANKS` |
| tanks stale | `TANKS_STALE` |
| tanks refused | `TANKS_REFUSED` |
| tanks not from this inventory | `TANKS_MISMATCH` |

**Stated per branch.**

| Input | Values |
| --- | --- |
| Management mode | settled free surface · diaphragm · bladder · piston · bellows · surface-tension device (PMD). No default. |
| Acceleration environment | accelerated throughout · low-gravity phases · unresolved |
| Settling acceleration | required · not required · unresolved; optionally a stated value in m/s², recorded only |

## Outlet coverage: declarations, not demonstrations

| Mode | Environment | Settling | Declaration |
| --- | --- | --- | --- |
| any | unresolved | any | **UNRESOLVED** |
| settled | accelerated | any | settled by the stated acceleration (slosh and vortexing not modelled) |
| settled | low gravity | required | only while settling acts (magnitude and duration not evaluated) |
| settled | low gravity | unresolved | **UNRESOLVED** |
| settled | low gravity | not required | **refused**: nothing keeps the outlet covered |
| diaphragm, bladder, piston, bellows | stated | any | positive-expulsion device (performance, stress, fatigue not evaluated) |
| surface tension | stated | any | capillary retention declared (not evaluated; low-gravity feed not claimed); an advisory in an accelerated environment |

Every declaration names what it rests on and what is not evaluated. An
unresolved branch makes the study incomplete.

## Volumes

    V_present  = m_present / ρ              liquid at the start of the burn
    V_gas,0    = V_tank − V_present          ullage plus the space boil-off left
    V_expelled = m_available / ρ
    V_gas,end  = V_gas,0 + V_expelled = V_tank − m_residual / ρ

The residual is held in the tank for these books. Residual held in the lines
would leave the tank and enlarge the final gas volume by up to m_residual/ρ.

The closures are:
- fill + ullage = 1;
- (V_gas,end + V_residual)/V_tank − 1;
- (available + residual + boil-off)/loaded − 1.

All are at rounding level.

## Verified

- **Combinations.** Every mode × environment × settling combination is
  either a declaration with a basis or the one explicit refusal. All five
  availability states occur, and no wording claims availability.
- **Volumes.** Checked by hand.
- **Consistency.** η and the residual equal SYS-1's exactly.
- **Upstream.** Every stale and mismatched upstream state is refused.
- **Records.** Every mode round-trips through JSON with a fingerprint check.

## Not in SYS-3

- Slosh dynamics, pendulum or mode models, damping, frequency and control
  coupling.
- Free-surface CFD and vortexing.
- Settling time and propellant-acquisition analysis.
- Screen pore and bubble-point sizing, galleries.
- Diaphragm or bladder stress and fatigue.
- Expulsion efficiency by device.
