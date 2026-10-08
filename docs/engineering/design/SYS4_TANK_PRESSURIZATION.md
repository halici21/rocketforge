# SYS-4 — Tank pressurization foundation

SYS-4 answers, for each branch: *what pressurant state, mass and volume
maintain or evolve the tank pressure?* It reads a current SYS-3 study, and
through it the SYS-2 tanks and the SYS-1 inventory. The required tank
pressure is stated or taken from the LIQ-6 injector ledger.

There are two executable modes:
- **regulated stored gas**;
- **blowdown**.

**Autogenous** and **warm-gas (engine-gas)** pressurization are recorded as
intent and computed nowhere, until their thermal and cycle models exist.

## Where it lives

| Part | Location |
| --- | --- |
| Perfect-gas relations | `rocketforge/engineering/propulsion_system/pressurization.py` |
| Basis, definition, quantities | `rocketforge/engine/propulsion_system/pressurization.py` |
| Resolution, computation | `rocketforge/application/analysis/tank_pressurization_service.py` |
| QML singleton `TankPressurization` | `rocketforge/application/analysis/tank_pressurization_controller.py` |
| Page | `ui/pages/TankPressurizationPage.qml` |

## Sources

Sutton & Biblarz, 9th ed.

**§6.4 and Table 6-3.** In a regulated system the tank stays at an
essentially constant pressure. In a blowdown system "gas temperatures,
pressures and the resulting thrust all steadily decrease".

**§6.5, "Simplified Analysis for the Mass of Pressurizing Gas"** assumes a
perfect gas, no evaporation, no solubility and no sloshing:

    m0 = mg + mp,  pV = mRT                                         (6-5)
    isothermal: V0 = pp Vp/(p0 − pg),  m0 = (pp Vp/(R T0))/(1 − pg/p0)   (6-6, 6-7)

Sutton adds: "the polytropic exponent lies between 1.0 and k".
**Example 6-2** treats the isentropic limit as one gas mass:
p0 V0^k = pp (V0 + Vp)^k.

## Regulated stored gas

Eq. 6-5 is applied as written, with every state's temperature explicit:

    mp = pp Vp / (R Tp)
    Tg = T0 (pg/p0)^((n−1)/n)          bottle after a polytropic expansion
    V0 = mp R / (p0/T0 − pg/Tg)
    m0 = p0 V0/(R T0),   mg = pg V0/(R Tg)

- **Exponent.** n is stated: 1 is isothermal, and the polytropic limit is
  at most k.
- **Tank-gas temperature Tp** is stated, or one of Sutton's two
  conventions, chosen explicitly:
  - Tp = T0 reproduces Eq. 6-7 exactly when n = 1;
  - Tp = Tg reproduces Example 6-2 exactly when n = k and pg = pp.
- **Regulator.** The bottle's final pressure pg is stated, and must stay at
  or above pp (Sutton: pg ≥ pp). pg − pp is reported as the end-of-burn
  regulator drop.
- **Gas volume filled.** Vp is the expelled liquid (SYS-3). It also
  includes the start ullage if the bottle fills that, starting from no
  pressurant; the user states which.
- **Reserve.** An optional pressurant reserve is a stated mass or a stated
  fraction of m0, stored at the bottle's initial state.

## Blowdown

The ullage gas expands from the SYS-3 start volume Vi to the end volume
Vf = Vi + V_expelled:

    pf = pi (Vi/Vf)^n,   Tf = Ti (Vi/Vf)^(n−1),   m = pi Vi/(R Ti)

The evolution is tabulated at 0, 25, 50, 75 and 100 % expelled. The margins
over the required pressure are reported at the start and at the end. A
negative margin is a **warning** with its number. The engine's flow decay as
the pressure falls is not modelled.

## No hidden defaults

- **Not assumed:** the gas, its R, the exponent, any temperature or any
  pressure.
- **Gas.** The pressurant is named and its R stated. No gas library is
  used: RocketForge has no validated gas-property path for pressurants.
- **Required pressure.** If LIQ-6's ledger is incomplete, the required
  pressure stays unresolved with LIQ-6's reason, and so do the margins.
- **Stale or mismatched LIQ-6.** A LIQ-6 study that is stale, refused or for
  another sizing is refused as a source.

## The model's limits

- **Perfect gas.** Sutton calls these "theoretical (i.e., minimum) mass
  estimates".
- **Real gas.** Compressibility at high bottle pressure is **not**
  modelled. It can be material: helium departs from the perfect gas by
  several percent at tens of MPa. The results are therefore the perfect-gas
  answer and are labelled as such.
- **Not included:** heat transfer to the gas, propellant evaporation and gas
  solubility, regulator dynamics, pressurant lines, and bottle structure.

## Sutton's helium arithmetic in Example 6-2

For helium (k = 1.68), Sutton prints 1.334 V0 = 0.180 and V0 = 0.135 m³.
The correct factor is 4.118^(1/1.68) − 1 = 1.322, which gives
V0 = 0.1362 m³, 0.9 % larger. The nitrogen line (1.748, 0.103 m³) is
consistent. SYS-4 follows the equation, and a test pins the discrepancy.
This is the same treatment LIQ-5 and LIQ-6 gave their sources' arithmetic.

## Verified

- **Example 6-2.** Isothermal for helium and nitrogen, and isentropic for
  nitrogen. The helium isentropic value is pinned as above.
- **Regulated mass closure.** m0 = mg + mp to 10⁻¹⁵ over a range of stated
  temperatures and exponents.
- **Blowdown.** pVⁿ is constant along the evolution, isothermal and
  polytropic; mass closes.
- **Refusals.** Invalid gas states, a regulator that cannot deliver, and a
  stale SYS-3.
- **Mixed modes.** A regulated and a blowdown branch run in one study.
- **Propagation.** Unresolved requirements propagate; intent modes reach no
  relation.
- **Records.** JSON round-trip with a fingerprint check.

## Not in SYS-4

- Autogenous heat-exchanger closure, warm-gas chemistry and cryogenic
  boil-off.
- Tank heat transfer and regulator transients.
- Pressurant line sizing, bottle and tank structure, and real-gas
  properties.
