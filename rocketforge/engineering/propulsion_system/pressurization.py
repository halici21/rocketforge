"""Tank pressurization with a perfect gas: regulated stored gas and blowdown.

Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed.:

* section 6.4 (pp. 205-207, Table 6-3): a **regulated** system feeds gas from
  a high-pressure tank through a regulator, so the propellant tank stays at an
  essentially constant pressure; in a **blowdown** system the gas is stored in
  the propellant tank's ullage and "gas temperatures, pressures and the
  resulting thrust all steadily decrease as propellants are consumed";
* section 6.5 (pp. 215-217), "Simplified Analysis for the Mass of Pressurizing
  Gas": perfect gas, no propellant evaporation, an inert gas that does not
  dissolve, no sloshing. With subscript 0 the gas tank initially, g the gas
  tank at the end, p the gas in the propellant tank::

      m0 = mg + mp,   pV = mRT                                   (Eq. 6-5)
      isothermal:  V0 = pp Vp / (p0 - pg),
                   m0 = (pp Vp / (R T0)) / (1 - pg/p0)           (Eqs. 6-6, 6-7)

  "In real pressurizations, end conditions should fall somewhere between
  isothermal and adiabatic ... a reversible polytropic expansion of a perfect
  gas, where the polytropic exponent lies between 1.0 and k." Example 6-2
  treats the isentropic limit as one gas mass expanding from (p0, V0) to
  (pp, V0 + Vp): p0 V0^k = pp (V0 + Vp)^k.

**Regulated stored gas, here.** Eq. 6-5 is applied as written, with each
state's temperature explicit::

    mp = pp Vp / (R Tp)                       gas delivered to the propellant tank
    Tg = T0 (pg/p0)^((n-1)/n)                 bottle gas after a polytropic expansion
    V0 = mp R / (p0/T0 - pg/Tg)               from m0 = mg + mp
    m0 = p0 V0 / (R T0),   mg = pg V0 / (R Tg)

The bottle expansion exponent ``n`` (1 isothermal, up to k) and the tank-gas
temperature ``Tp`` are stated, never chosen. With n = 1 and Tp = T0 this is
Eq. 6-7 exactly; with n = k, pg = pp and Tp = Tg it is Example 6-2 exactly.
``pg`` is the bottle pressure at the end, which must stay at or above the
regulated tank pressure (Sutton: "pg >= pp to account for valve, piping, and
regulator pressure drops").

**Blowdown, here.** The ullage gas expands polytropically from (pi, Vi) to
(pf, Vf) as liquid leaves::

    pf = pi (Vi/Vf)^n,   Tf = Ti (Vi/Vf)^(n-1),   m = pi Vi / (R Ti)

**Perfect gas only.** No real-gas compressibility, no heat transfer to the
gas, no propellant evaporation or gas solubility, no regulator dynamics, no
line sizing. Sutton calls these "theoretical (i.e., minimum) mass estimates".

SI: Pa, K, m^3, kg, J/(kg K).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from rocketforge.core.result import Diagnostic, Severity, Solution, Status

__all__ = [
    "BlowdownState",
    "Blowdown",
    "RegulatedPressurization",
    "blowdown",
    "ideal_gas_mass",
    "polytropic_temperature",
    "regulated_stored_gas",
]


def _finite(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _refuse(code: str, message: str, field: str) -> Solution:
    return Solution(value=None, status=Status.NO_SOLUTION,
                    diagnostics=(Diagnostic(code=code, severity=Severity.ERROR,
                                            message=message, field=field),))


def _positive(**values: float) -> Solution | None:
    for name, value in values.items():
        if not (_finite(value) and value > 0.0):
            return _refuse(f"{name.upper()}_INVALID",
                           f"The {name.replace('_', ' ')} must be finite and above zero.", name)
    return None


def _exponent(n: float) -> Solution | None:
    if not (_finite(n) and n >= 1.0):
        return _refuse("EXPONENT_INVALID", "The polytropic exponent must be finite and at "
                       "least 1 (1 is isothermal; Sutton §6.5 bounds it by k).", "exponent")
    return None


def ideal_gas_mass(pressure: float, volume: float, gas_constant: float,
                   temperature: float) -> float:
    """``p V / (R T)``, Sutton Eq. 6-5."""
    return pressure * volume / (gas_constant * temperature)


def polytropic_temperature(temperature: float, pressure_from: float, pressure_to: float,
                           exponent: float) -> float:
    """``T (p_to/p_from)^((n-1)/n)`` along p V^n = const of a perfect gas."""
    return temperature * (pressure_to / pressure_from) ** ((exponent - 1.0) / exponent)


@dataclass(frozen=True, slots=True)
class RegulatedPressurization:
    """One branch's stored-gas pressurization. SI.

    Attributes:
        tank_pressure / tank_gas_temperature / fill_volume: pp, Tp, Vp.
        delivered_mass: mp.
        bottle_initial_pressure / bottle_initial_temperature: p0, T0.
        bottle_final_pressure / bottle_final_temperature: pg, Tg.
        bottle_volume: V0.
        initial_mass / residual_mass: m0 and mg (left in the bottle).
        regulator_drop_end: pg - pp, the smallest regulator inlet-outlet
            difference, at the end of the burn.
        mass_closure: (mg + mp) / m0 - 1.
    """

    tank_pressure: float
    tank_gas_temperature: float
    fill_volume: float
    delivered_mass: float
    bottle_initial_pressure: float
    bottle_initial_temperature: float
    bottle_final_pressure: float
    bottle_final_temperature: float
    exponent: float
    gas_constant: float
    bottle_volume: float
    initial_mass: float
    residual_mass: float
    regulator_drop_end: float
    mass_closure: float


def regulated_stored_gas(tank_pressure: float, fill_volume: float,
                         tank_gas_temperature: float, bottle_initial_pressure: float,
                         bottle_initial_temperature: float, bottle_final_pressure: float,
                         gas_constant: float, exponent: float
                         ) -> Solution[RegulatedPressurization]:
    """Gas mass and bottle volume to hold ``tank_pressure`` over ``fill_volume``."""
    refused = (_positive(tank_pressure=tank_pressure, fill_volume=fill_volume,
                         tank_gas_temperature=tank_gas_temperature,
                         bottle_initial_pressure=bottle_initial_pressure,
                         bottle_initial_temperature=bottle_initial_temperature,
                         bottle_final_pressure=bottle_final_pressure,
                         gas_constant=gas_constant) or _exponent(exponent))
    if refused is not None:
        return refused
    pp, vp, tp = float(tank_pressure), float(fill_volume), float(tank_gas_temperature)
    p0, t0, pg = (float(bottle_initial_pressure), float(bottle_initial_temperature),
                  float(bottle_final_pressure))
    r, n = float(gas_constant), float(exponent)
    if pg < pp:
        return _refuse("BOTTLE_BELOW_TANK_PRESSURE",
                       f"The bottle's final pressure ({pg:g} Pa) is below the regulated tank "
                       f"pressure ({pp:g} Pa): the regulator cannot deliver it (Sutton §6.5: "
                       "pg ≥ pp).", "bottle_final_pressure")
    if pg >= p0:
        return _refuse("BOTTLE_PRESSURE_ORDER",
                       "The bottle's final pressure must be below its initial pressure: no gas "
                       "would leave it.", "bottle_final_pressure")
    tg = polytropic_temperature(t0, p0, pg, n)
    mp = ideal_gas_mass(pp, vp, r, tp)
    v0 = mp * r / (p0 / t0 - pg / tg)
    m0 = ideal_gas_mass(p0, v0, r, t0)
    mg = ideal_gas_mass(pg, v0, r, tg)
    return Solution(
        value=RegulatedPressurization(
            tank_pressure=pp, tank_gas_temperature=tp, fill_volume=vp, delivered_mass=mp,
            bottle_initial_pressure=p0, bottle_initial_temperature=t0,
            bottle_final_pressure=pg, bottle_final_temperature=tg, exponent=n,
            gas_constant=r, bottle_volume=v0, initial_mass=m0, residual_mass=mg,
            regulator_drop_end=pg - pp, mass_closure=(mg + mp) / m0 - 1.0),
        status=Status.OK,
        provenance=("Sutton & Biblarz 9th ed. §6.5, Eqs. 6-5, 6-6, 6-7, Example 6-2",))


@dataclass(frozen=True, slots=True)
class BlowdownState:
    expelled_fraction: float       # of the liquid expelled
    gas_volume: float
    pressure: float
    temperature: float


@dataclass(frozen=True, slots=True)
class Blowdown:
    """One branch's blowdown. SI."""

    initial_pressure: float
    initial_temperature: float
    initial_volume: float
    final_volume: float
    exponent: float
    gas_constant: float
    gas_mass: float
    final_pressure: float
    final_temperature: float
    blowdown_ratio: float          # Vf / Vi
    pressure_ratio: float          # pf / pi
    mass_closure: float            # pf Vf / (R Tf) / m - 1
    evolution: tuple[BlowdownState, ...]


def blowdown(initial_pressure: float, initial_temperature: float, initial_volume: float,
             expelled_volume: float, gas_constant: float, exponent: float,
             fractions: Sequence[float] = (0.0, 0.25, 0.5, 0.75, 1.0)) -> Solution[Blowdown]:
    """The ullage gas expanding as ``expelled_volume`` of liquid leaves."""
    refused = (_positive(initial_pressure=initial_pressure,
                         initial_temperature=initial_temperature,
                         initial_volume=initial_volume, expelled_volume=expelled_volume,
                         gas_constant=gas_constant) or _exponent(exponent))
    if refused is not None:
        return refused
    p_i, t_i, v_i = float(initial_pressure), float(initial_temperature), float(initial_volume)
    dv, r, n = float(expelled_volume), float(gas_constant), float(exponent)

    def state(fraction: float) -> BlowdownState:
        v = v_i + fraction * dv
        ratio = v_i / v
        return BlowdownState(fraction, v, p_i * ratio ** n, t_i * ratio ** (n - 1.0))

    end = state(1.0)
    mass = ideal_gas_mass(p_i, v_i, r, t_i)
    return Solution(
        value=Blowdown(
            initial_pressure=p_i, initial_temperature=t_i, initial_volume=v_i,
            final_volume=end.gas_volume, exponent=n, gas_constant=r, gas_mass=mass,
            final_pressure=end.pressure, final_temperature=end.temperature,
            blowdown_ratio=end.gas_volume / v_i, pressure_ratio=end.pressure / p_i,
            mass_closure=ideal_gas_mass(end.pressure, end.gas_volume, r, end.temperature)
            / mass - 1.0,
            evolution=tuple(state(float(f)) for f in fractions)),
        status=Status.OK,
        provenance=("Sutton & Biblarz 9th ed. §6.4 (Table 6-3), §6.5 (polytropic perfect "
                    "gas)",))
