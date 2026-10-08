"""Propellant inventory of one branch: usable, available, residual, loaded.

Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed.:

* section 6.2 (p. 196): "The expulsion efficiency of a tank and/or propellant
  piping system is the amount of propellant that can be expelled or available
  for propulsion divided by the total amount of propellant initially present."
  The loss is "unavailable propellants left in tanks after rocket operation,
  trapped in grooves or corners of pipes, fittings, filters, and valves, or
  wetting the walls";
* section 11.1 (pp. 399-401), the propellant budget: the load is "always
  somewhat greater than the nominal amount of propellant needed", by residual
  propellant (item 6), loading uncertainty (7), off-nominal allowances (8, 9),
  evaporation and cool-down (10) and contingency (11). Example 11-1 forms the
  load as the nominal flow times the burn time times (1 + residual + reserve).

With the expulsion efficiency ``eta`` of the propellant present at the start
of the burn, the bookkeeping here is::

    m_usable    = mdot t                                  steady consumption
    m_available = m_usable + allowances + m_reserve       must be expellable
    m_present   = m_available / eta                       (eta stated), or
                = m_available + m_residual                (residual stated)
    m_residual  = m_present - m_available                 unavailable
    m_loaded    = m_present + m_boiloff                   lost before the burn

Allowances are propellant that leaves through the outlet without being part of
the steady burn: start and shutdown transients, chill-down through the engine,
others the user states. Boil-off evaporates from the tank before the burn, so
it is loaded but never present for expulsion and is not divided by ``eta``.

**Nothing is defaulted.** The expulsion efficiency, the residual, the reserve
and every allowance are stated, declared not applicable, or unresolved. An
unresolved term keeps the loaded mass unresolved; the minimum known loaded
mass, the sum of what is known, is always given. Every term is non-negative,
so the load is at least that.

SI: kg, kg/s, s.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from rocketforge.core.result import Diagnostic, Severity, Solution, Status

__all__ = [
    "BranchInventory",
    "MassTerm",
    "ResidualMode",
    "TermStatus",
    "branch_inventory",
    "expulsion_efficiency_from_residual",
    "present_from_expulsion_efficiency",
    "usable_mass",
]


class TermStatus(StrEnum):
    RESOLVED = "resolved"
    NOT_APPLICABLE = "not_applicable"
    UNRESOLVED = "unresolved"


class ResidualMode(StrEnum):
    EXPULSION_EFFICIENCY = "expulsion_efficiency"   # eta stated, of the propellant present
    RESIDUAL_MASS = "residual_mass"                 # the unavailable mass stated, kg
    UNRESOLVED = "unresolved"


def _finite(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _refuse(code: str, message: str, field: str) -> Solution:
    return Solution(value=None, status=Status.NO_SOLUTION,
                    diagnostics=(Diagnostic(code=code, severity=Severity.ERROR,
                                            message=message, field=field),))


@dataclass(frozen=True, slots=True)
class MassTerm:
    """One inventory term, kg. ``value`` exactly when resolved."""

    key: str
    label: str
    status: TermStatus
    value: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, TermStatus):
            raise ValueError("a term's status must be a TermStatus")
        if (self.value is not None) != (self.status is TermStatus.RESOLVED):
            raise ValueError(f"{self.key}: a value exists exactly when the term is resolved")
        if self.value is not None and not (_finite(self.value) and self.value >= 0.0):
            raise ValueError(f"{self.key}: a resolved mass is finite and at or above zero")

    @property
    def contribution(self) -> float:
        return self.value if self.value is not None else 0.0


def usable_mass(mass_flow: float, burn_time: float) -> float:
    """``mdot t``: the propellant the steady burn consumes."""
    if not (_finite(mass_flow) and mass_flow > 0.0):
        raise ValueError("the mass flow must be finite and above zero")
    if not (_finite(burn_time) and burn_time > 0.0):
        raise ValueError("the burn time must be finite and above zero")
    return float(mass_flow) * float(burn_time)


def present_from_expulsion_efficiency(available: float, efficiency: float) -> float:
    """``m_available / eta``: the propellant present for that much to be expellable."""
    if not (_finite(available) and available >= 0.0):
        raise ValueError("the available mass must be finite and at or above zero")
    if not (_finite(efficiency) and 0.0 < efficiency <= 1.0):
        raise ValueError("the expulsion efficiency must be above 0 and at most 1")
    return float(available) / float(efficiency)


def expulsion_efficiency_from_residual(available: float, residual: float) -> float:
    """``m_available / (m_available + m_residual)``, Sutton §6.2's definition."""
    if not (_finite(available) and available > 0.0):
        raise ValueError("the available mass must be finite and above zero")
    if not (_finite(residual) and residual >= 0.0):
        raise ValueError("the residual must be finite and at or above zero")
    return float(available) / (float(available) + float(residual))


@dataclass(frozen=True, slots=True)
class BranchInventory:
    """One branch's inventory. Totals are ``None`` while a term they need is
    unresolved; ``minimum_known_loaded`` is always set.

    Attributes:
        usable: mdot t.
        available: usable + allowances + reserve, when all are resolved.
        minimum_known_available: the same sum over the resolved terms.
        residual: unavailable propellant, kg.
        expulsion_efficiency: stated, or available / present.
        present: propellant present at the start of the burn.
        boiloff: lost before the burn, kg, when resolved.
        loaded: present + boil-off.
        minimum_known_loaded: the load is at least this.
        unresolved: keys of the unresolved terms, in order.
        balance_closure: (available + residual + boiloff) / loaded - 1.
        efficiency_closure: (present - residual) / present / eta - 1.
    """

    usable: float
    available: float | None
    minimum_known_available: float
    residual: float | None
    expulsion_efficiency: float | None
    present: float | None
    boiloff: float | None
    loaded: float | None
    minimum_known_loaded: float
    unresolved: tuple[str, ...]
    balance_closure: float | None
    efficiency_closure: float | None


def branch_inventory(mass_flow: float, burn_time: float, allowances: Sequence[MassTerm],
                     residual_mode: ResidualMode, residual_value: float | None,
                     residual_terms: Sequence[MassTerm], boiloff: MassTerm
                     ) -> Solution[BranchInventory]:
    """One branch's inventory.

    Args:
        mass_flow / burn_time: The steady burn, kg/s and s.
        allowances: Terms that leave through the outlet besides the steady
            burn, including the reserve, each resolved, n/a or unresolved.
        residual_mode: How the unavailable propellant is stated.
        residual_value: eta for EXPULSION_EFFICIENCY; absent otherwise.
        residual_terms: For RESIDUAL_MASS, the stated parts of the residual
            (tank residual, trapped line); empty otherwise.
        boiloff: Lost from the tank before the burn.
    """
    if not (_finite(mass_flow) and mass_flow > 0.0):
        return _refuse("MASS_FLOW_INVALID", "The branch mass flow must be finite and above "
                       "zero.", "mass_flow")
    if not (_finite(burn_time) and burn_time > 0.0):
        return _refuse("BURN_TIME_INVALID", "The burn time must be finite and above zero.",
                       "burn_time")
    if not isinstance(residual_mode, ResidualMode):
        raise ValueError("residual_mode must be a ResidualMode")
    eta = None
    if residual_mode is ResidualMode.EXPULSION_EFFICIENCY:
        if not (_finite(residual_value) and 0.0 < residual_value <= 1.0):
            return _refuse("EXPULSION_EFFICIENCY_INVALID", "The expulsion efficiency must be "
                           "above 0 and at most 1.", "expulsion_efficiency")
        if residual_terms:
            raise ValueError("an expulsion efficiency covers the residual; no parts are stated")
        eta = float(residual_value)
    elif residual_value is not None:
        raise ValueError("only an expulsion efficiency carries a residual value")
    if residual_mode is not ResidualMode.RESIDUAL_MASS and residual_terms:
        raise ValueError("residual parts are stated only in residual-mass mode")
    keys = [t.key for t in (*allowances, *residual_terms, boiloff)]
    if len(set(keys)) != len(keys):
        raise ValueError(f"duplicate inventory terms in {keys}")

    usable = usable_mass(mass_flow, burn_time)
    unresolved = [t.key for t in allowances if t.status is TermStatus.UNRESOLVED]
    known_available = math.fsum([usable, *(t.contribution for t in allowances)])
    available = None if unresolved else known_available

    residual: float | None = None
    present: float | None = None
    known_residual = 0.0
    if residual_mode is ResidualMode.EXPULSION_EFFICIENCY:
        known_residual = present_from_expulsion_efficiency(known_available, eta) - known_available
        if available is not None:
            present = present_from_expulsion_efficiency(available, eta)
            residual = present - available
    elif residual_mode is ResidualMode.RESIDUAL_MASS:
        parts_unresolved = [t.key for t in residual_terms if t.status is TermStatus.UNRESOLVED]
        known_residual = math.fsum(t.contribution for t in residual_terms)
        unresolved += parts_unresolved
        if not parts_unresolved and not residual_terms:
            unresolved.append("residual")
        elif not parts_unresolved:
            residual = known_residual
            if available is not None:
                present = available + residual
                eta = expulsion_efficiency_from_residual(available, residual)
    else:
        unresolved.append("residual")

    boiloff_value = boiloff.value if boiloff.status is TermStatus.RESOLVED else (
        0.0 if boiloff.status is TermStatus.NOT_APPLICABLE else None)
    if boiloff.status is TermStatus.UNRESOLVED:
        unresolved.append(boiloff.key)
    loaded = None if present is None or boiloff_value is None else present + boiloff_value
    minimum = math.fsum([known_available, known_residual, boiloff.contribution])
    return Solution(
        value=BranchInventory(
            usable=usable, available=available, minimum_known_available=known_available,
            residual=residual, expulsion_efficiency=eta, present=present,
            boiloff=boiloff_value, loaded=loaded, minimum_known_loaded=minimum,
            unresolved=tuple(unresolved),
            balance_closure=(None if loaded is None or loaded == 0.0 else
                             math.fsum([available, residual, boiloff_value]) / loaded - 1.0),
            efficiency_closure=(None if present is None or eta is None else
                                (present - residual) / present / eta - 1.0)),
        status=Status.OK,
        provenance=("Sutton & Biblarz 9th ed. §6.2 (expulsion efficiency), §11.1 "
                    "(propellant budget, Example 11-1)",),
        inputs={"mass_flow": float(mass_flow), "burn_time": float(burn_time)})
