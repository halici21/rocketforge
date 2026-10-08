"""SYS-1 -- the propellant inventory of a stage, per branch.

An inventory takes an accepted LIQ-4 sizing's oxidiser and fuel flows and the
LIQ-2 requirement's burn time, copied verbatim, and per branch what the user
states about the budget: how the unavailable propellant is given (an
expulsion efficiency or a residual mass), a reserve, and allowances. It answers
with the usable, available, residual and loaded masses of each branch and the
totals. The relations are in
:mod:`rocketforge.engineering.propulsion_system.inventory`.

Rules that shape it:

* **Upstream is truth.** LIQ-4 owns the flows and LIQ-2 the burn time.
  :class:`InventoryBasis` is a copy with the identities it came from.
* **Nothing is invented.** No expulsion efficiency, reserve, trapped-line mass,
  boil-off, transient or chill-down allowance has a default. Each is stated,
  declared not applicable, or unresolved, and unresolved is never zero.
* **No cycle flows.** Only the thrust-chamber flows exist upstream; no gas
  generator, pressurization bleed or auxiliary flow is added or implied.

SI units throughout.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Final

from .records import Branch, Quantity, Upstream, fingerprint, register_schema

__all__ = [
    "ALLOWANCE_TERMS",
    "INVENTORY_BRANCH_QUANTITIES",
    "INVENTORY_SCHEMA",
    "INVENTORY_TOTALS",
    "InventoryBasis",
    "InventoryBranchDefinition",
    "InventoryDefinition",
    "ReserveMode",
    "ResidualMode",
    "TermMode",
    "TermSetting",
]

INVENTORY_SCHEMA: Final = "rocketforge.propellant-inventory"
INVENTORY_SCHEMA_VERSION: Final = 1


class TermMode(StrEnum):
    UNRESOLVED = "unresolved"
    STATED = "stated"                    # value: kg
    NOT_APPLICABLE = "not_applicable"


class ReserveMode(StrEnum):
    UNRESOLVED = "unresolved"
    NOT_APPLICABLE = "not_applicable"
    STATED_MASS = "stated_mass"          # value: kg
    STATED_FRACTION = "stated_fraction"  # value: fraction of the usable mass


class ResidualMode(StrEnum):
    UNRESOLVED = "unresolved"
    EXPULSION_EFFICIENCY = "expulsion_efficiency"
    RESIDUAL_MASS = "residual_mass"


#: Propellant that leaves through the outlet besides the steady burn, in ledger
#: order: (key, label, Sutton basis). The reserve is its own setting.
ALLOWANCE_TERMS: tuple[tuple[str, str, str], ...] = (
    ("start_stop", "Start and shutdown transients", "Sutton §11.1; Example 6-1 allows them"),
    ("chilldown", "Chill-down through the engine", "Sutton §11.1 item 10"),
    ("other_allowance", "Other stated allowance", "Sutton §11.1 items 7-9, 11; stated"),
)


@dataclass(frozen=True, slots=True)
class TermSetting:
    """One stated term. ``value`` exactly when the mode carries one."""

    mode: TermMode = TermMode.UNRESOLVED
    value: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, TermMode):
            raise ValueError("a term mode must be a TermMode")
        if (self.mode is TermMode.STATED) != (self.value is not None):
            raise ValueError("a stated term carries its value; no other term does")
        if self.value is not None and not (math.isfinite(self.value) and self.value >= 0.0):
            raise ValueError("a stated mass is finite and at or above zero")

    def to_dict(self) -> dict[str, Any]:
        return {"mode": self.mode.value, "value": self.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TermSetting":
        value = payload.get("value")
        return cls(TermMode(payload["mode"]), None if value is None else float(value))


@dataclass(frozen=True, slots=True)
class InventoryBasis:
    """The flows of an accepted LIQ-4 sizing and the LIQ-2 burn time, copied.

    Attributes:
        sizing: The LIQ-4 sizing's identity.
        trade_fingerprint / requirement_fingerprint: What it extends.
        pair_key / pair_label / oxidiser / fuel: The propellants.
        oxidiser_fuel_ratio: O/F by mass, as LIQ-4 used it.
        chamber_pressure: Pa, as LIQ-4 used it.
        oxidiser_temperature / fuel_temperature: K, the LIQ-3 stream temperatures.
        mass_flow / oxidiser_mass_flow / fuel_mass_flow: kg/s, LIQ-4's.
        burn_time: s, the LIQ-2 requirement's.
    """

    sizing: Upstream
    trade_fingerprint: str
    requirement_fingerprint: str
    pair_key: str
    pair_label: str
    oxidiser: str
    fuel: str
    oxidiser_fuel_ratio: float
    chamber_pressure: float
    oxidiser_temperature: float
    fuel_temperature: float
    mass_flow: float
    oxidiser_mass_flow: float
    fuel_mass_flow: float
    burn_time: float

    def __post_init__(self) -> None:
        for name in ("oxidiser_fuel_ratio", "chamber_pressure", "oxidiser_temperature",
                     "fuel_temperature", "mass_flow", "oxidiser_mass_flow", "fuel_mass_flow",
                     "burn_time"):
            value = getattr(self, name)
            if not (isinstance(value, (int, float)) and math.isfinite(value) and value > 0.0):
                raise ValueError(f"{name} must be finite and positive")
        if self.sizing.status not in ("ok", "warning"):
            raise ValueError("an inventory basis comes from an accepted sizing only")

    def mass_flow_of(self, branch: Branch) -> float:
        return self.oxidiser_mass_flow if branch is Branch.OXIDISER else self.fuel_mass_flow

    def propellant_of(self, branch: Branch) -> str:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def temperature_of(self, branch: Branch) -> float:
        return self.oxidiser_temperature if branch is Branch.OXIDISER else self.fuel_temperature

    def to_dict(self) -> dict[str, Any]:
        return {
            "sizing": self.sizing.to_dict(),
            "trade_fingerprint": self.trade_fingerprint,
            "requirement_fingerprint": self.requirement_fingerprint,
            "pair_key": self.pair_key, "pair_label": self.pair_label,
            "oxidiser": self.oxidiser, "fuel": self.fuel,
            "oxidiser_fuel_ratio": self.oxidiser_fuel_ratio,
            "chamber_pressure_Pa": self.chamber_pressure,
            "oxidiser_temperature_K": self.oxidiser_temperature,
            "fuel_temperature_K": self.fuel_temperature,
            "mass_flow_kg_s": self.mass_flow,
            "oxidiser_mass_flow_kg_s": self.oxidiser_mass_flow,
            "fuel_mass_flow_kg_s": self.fuel_mass_flow,
            "burn_time_s": self.burn_time,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InventoryBasis":
        return cls(
            sizing=Upstream.from_dict(payload["sizing"]),
            trade_fingerprint=str(payload["trade_fingerprint"]),
            requirement_fingerprint=str(payload["requirement_fingerprint"]),
            pair_key=str(payload["pair_key"]), pair_label=str(payload["pair_label"]),
            oxidiser=str(payload["oxidiser"]), fuel=str(payload["fuel"]),
            oxidiser_fuel_ratio=float(payload["oxidiser_fuel_ratio"]),
            chamber_pressure=float(payload["chamber_pressure_Pa"]),
            oxidiser_temperature=float(payload["oxidiser_temperature_K"]),
            fuel_temperature=float(payload["fuel_temperature_K"]),
            mass_flow=float(payload["mass_flow_kg_s"]),
            oxidiser_mass_flow=float(payload["oxidiser_mass_flow_kg_s"]),
            fuel_mass_flow=float(payload["fuel_mass_flow_kg_s"]),
            burn_time=float(payload["burn_time_s"]),
        )


@dataclass(frozen=True, slots=True)
class InventoryBranchDefinition:
    """One branch's stated budget. Complete by construction.

    Attributes:
        residual_mode: How the unavailable propellant is stated.
        expulsion_efficiency: eta, in EXPULSION_EFFICIENCY mode only.
        tank_residual / trapped_line: The residual's parts, in RESIDUAL_MASS
            mode; otherwise unresolved and unused.
        reserve_mode / reserve_value: kg, or a fraction of the usable mass.
        allowances: Every term of :data:`ALLOWANCE_TERMS`, by key.
        boiloff: Lost from the tank before the burn.
    """

    branch: Branch
    residual_mode: ResidualMode
    expulsion_efficiency: float | None
    tank_residual: TermSetting
    trapped_line: TermSetting
    reserve_mode: ReserveMode
    reserve_value: float | None
    allowances: Mapping[str, TermSetting]
    boiloff: TermSetting

    def __post_init__(self) -> None:
        efficiency = self.residual_mode is ResidualMode.EXPULSION_EFFICIENCY
        if efficiency != (self.expulsion_efficiency is not None):
            raise ValueError("an expulsion efficiency is stated exactly in its own mode")
        if self.expulsion_efficiency is not None and not (
                math.isfinite(self.expulsion_efficiency)
                and 0.0 < self.expulsion_efficiency <= 1.0):
            raise ValueError("the expulsion efficiency must be above 0 and at most 1")
        if self.residual_mode is not ResidualMode.RESIDUAL_MASS and (
                self.tank_residual.mode is not TermMode.UNRESOLVED
                or self.trapped_line.mode is not TermMode.UNRESOLVED):
            raise ValueError("the residual's parts are stated only in residual-mass mode")
        stated = self.reserve_mode in (ReserveMode.STATED_MASS, ReserveMode.STATED_FRACTION)
        if stated != (self.reserve_value is not None):
            raise ValueError("a stated reserve carries its value; no other reserve does")
        if self.reserve_value is not None and not (
                math.isfinite(self.reserve_value) and self.reserve_value >= 0.0):
            raise ValueError("a reserve is finite and at or above zero")
        if set(self.allowances) != {key for key, _l, _b in ALLOWANCE_TERMS}:
            raise ValueError("the allowances are exactly "
                             f"{[key for key, _l, _b in ALLOWANCE_TERMS]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch.value,
            "residual_mode": self.residual_mode.value,
            "expulsion_efficiency": self.expulsion_efficiency,
            "tank_residual_kg": self.tank_residual.to_dict(),
            "trapped_line_kg": self.trapped_line.to_dict(),
            "reserve_mode": self.reserve_mode.value,
            "reserve_value": self.reserve_value,
            "allowances_kg": {key: self.allowances[key].to_dict()
                              for key, _l, _b in ALLOWANCE_TERMS},
            "boiloff_kg": self.boiloff.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InventoryBranchDefinition":
        eta = payload.get("expulsion_efficiency")
        reserve = payload.get("reserve_value")
        return cls(
            branch=Branch(payload["branch"]),
            residual_mode=ResidualMode(payload["residual_mode"]),
            expulsion_efficiency=None if eta is None else float(eta),
            tank_residual=TermSetting.from_dict(payload["tank_residual_kg"]),
            trapped_line=TermSetting.from_dict(payload["trapped_line_kg"]),
            reserve_mode=ReserveMode(payload["reserve_mode"]),
            reserve_value=None if reserve is None else float(reserve),
            allowances={str(k): TermSetting.from_dict(v)
                        for k, v in dict(payload["allowances_kg"]).items()},
            boiloff=TermSetting.from_dict(payload["boiloff_kg"]),
        )


@dataclass(frozen=True, slots=True)
class InventoryDefinition:
    """Everything an inventory is, before it is computed."""

    basis: InventoryBasis
    oxidiser: InventoryBranchDefinition
    fuel: InventoryBranchDefinition

    def __post_init__(self) -> None:
        if self.oxidiser.branch is not Branch.OXIDISER or self.fuel.branch is not Branch.FUEL:
            raise ValueError("the oxidiser and fuel branches are each in their own place")

    def branch(self, branch: Branch) -> InventoryBranchDefinition:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"basis": self.basis.to_dict(), "oxidiser": self.oxidiser.to_dict(),
                "fuel": self.fuel.to_dict()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InventoryDefinition":
        return cls(basis=InventoryBasis.from_dict(payload["basis"]),
                   oxidiser=InventoryBranchDefinition.from_dict(payload["oxidiser"]),
                   fuel=InventoryBranchDefinition.from_dict(payload["fuel"]))

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


#: Everything a branch reports, in display order. SI.
INVENTORY_BRANCH_QUANTITIES: tuple[Quantity, ...] = (
    Quantity("mass_flow", "Mass flow", "burn", "kg/s", "From the LIQ-4 sizing"),
    Quantity("burn_time", "Burn time", "burn", "s", "From the LIQ-2 requirement"),
    Quantity("usable_mass", "Usable propellant", "burn", "kg",
             "ṁ × burn time: the steady burn's consumption"),
    Quantity("start_stop", "Start and shutdown transients", "budget", "kg", "Stated"),
    Quantity("chilldown", "Chill-down through the engine", "budget", "kg", "Stated"),
    Quantity("other_allowance", "Other stated allowance", "budget", "kg", "Stated"),
    Quantity("reserve_mass", "Reserve", "budget", "kg",
             "Stated, or a stated fraction of the usable propellant"),
    Quantity("available_mass", "Available propellant", "budget", "kg",
             "Usable + allowances + reserve: must be expellable"),
    Quantity("expulsion_efficiency", "Expulsion efficiency", "residual", "",
             "Stated, or available / present (Sutton §6.2)"),
    Quantity("tank_residual", "Tank residual", "residual", "kg", "Stated"),
    Quantity("trapped_line", "Trapped in lines and valves", "residual", "kg", "Stated"),
    Quantity("residual_mass", "Residual (unavailable) propellant", "residual", "kg",
             "Present − available"),
    Quantity("present_mass", "Present at the start of the burn", "residual", "kg",
             "Available / η, or available + residual"),
    Quantity("boiloff_mass", "Boil-off before the burn", "load", "kg", "Stated"),
    Quantity("loaded_mass", "Loaded propellant", "load", "kg",
             "Present + boil-off; only when every term is resolved"),
    Quantity("minimum_known_loaded", "Minimum known load", "load", "kg",
             "Sum of the resolved terms; the load is at least this"),
    Quantity("unavailable_fraction", "Residual / present", "load", "", "1 − η"),
    Quantity("balance_closure", "Balance closure", "closure", "",
             "(available + residual + boil-off) / loaded − 1"),
    Quantity("efficiency_closure", "Efficiency closure", "closure", "",
             "(present − residual) / present / η − 1"),
)

INVENTORY_TOTALS: tuple[Quantity, ...] = (
    Quantity("usable_total", "Usable propellant", "total", "kg", "Oxidiser + fuel"),
    Quantity("loaded_total", "Loaded propellant", "total", "kg", "Oxidiser + fuel"),
    Quantity("minimum_known_loaded_total", "Minimum known load", "total", "kg",
             "Oxidiser + fuel, resolved terms only"),
    Quantity("residual_total", "Residual propellant", "total", "kg", "Oxidiser + fuel"),
    Quantity("usable_oxidiser_fuel_ratio", "Usable O/F", "total", "",
             "Equals the LIQ-4 O/F by construction"),
    Quantity("loaded_oxidiser_fuel_ratio", "Loaded O/F", "total", "",
             "Differs from the engine O/F when the budgets differ"),
    Quantity("usable_ratio_closure", "Usable O/F closure", "total", "",
             "Usable O/F / LIQ-4 O/F − 1"),
    Quantity("usable_total_closure", "Usable total closure", "total", "",
             "Usable total / (ṁ × burn time) − 1"),
)

register_schema(INVENTORY_SCHEMA, INVENTORY_SCHEMA_VERSION, InventoryDefinition,
                INVENTORY_BRANCH_QUANTITIES, INVENTORY_TOTALS)
