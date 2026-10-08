"""SYS-4 -- tank pressurization, per branch: regulated stored gas or blowdown.

A pressurization study takes a current SYS-3 management study (and through it
the SYS-2 tanks and SYS-1 inventory), copied verbatim, and per branch what the
user states: the mode, the pressurant's gas constant and the expansion
exponent, the tank and bottle states, and where the required tank pressure
comes from (stated, or the LIQ-6 injector ledger's required pressure). It
answers with the pressurant mass and bottle volume (regulated) or the pressure
evolution and end-of-burn pressure (blowdown), and the margin against the
required pressure. The relations are in
:mod:`rocketforge.engineering.propulsion_system.pressurization`.

* **No hidden defaults.** No gas, temperature, pressure or exponent is
  assumed. Isothermal is n = 1, stated like any other exponent.
* **Intent only** for autogenous and warm-gas (engine-gas) pressurization:
  recorded, not computed, until the thermal and cycle models exist.
* **Perfect gas.** No heat transfer, boil-off, regulator dynamics, line
  sizing or bottle structure.

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
    "PRESSURIZATION_BRANCH_QUANTITIES",
    "PRESSURIZATION_LABELS",
    "PRESSURIZATION_SCHEMA",
    "PRESSURIZATION_TOTALS",
    "BranchGasVolumes",
    "PressurantReserve",
    "PressurizationBasis",
    "PressurizationBranchDefinition",
    "PressurizationDefinition",
    "PressurizationMode",
    "RequiredSource",
    "TankGasTemperature",
    "UllageSource",
]

PRESSURIZATION_SCHEMA: Final = "rocketforge.tank-pressurization"
PRESSURIZATION_SCHEMA_VERSION: Final = 1


class PressurizationMode(StrEnum):
    REGULATED = "regulated"                  # stored gas through a regulator
    BLOWDOWN = "blowdown"                    # gas stored in the ullage
    AUTOGENOUS_INTENT = "autogenous_intent"  # recorded only
    WARM_GAS_INTENT = "warm_gas_intent"      # engine / gas-generator gas: recorded only

    @property
    def executable(self) -> bool:
        return self in (PressurizationMode.REGULATED, PressurizationMode.BLOWDOWN)


class RequiredSource(StrEnum):
    UNRESOLVED = "unresolved"
    STATED = "stated"
    INJECTOR = "injector"                    # the LIQ-6 ledger's required pressure


class TankGasTemperature(StrEnum):
    STATED = "stated"
    BOTTLE_INITIAL = "bottle_initial"        # Tp = T0: Sutton Eq. 6-7's isothermal end points
    BOTTLE_FINAL = "bottle_final"            # Tp = Tg: Example 6-2's single expanding mass


class UllageSource(StrEnum):
    GROUND = "ground"                        # pre-pressurized; the bottle fills only the expelled volume
    BOTTLE = "bottle"                        # the bottle also brings the start ullage to pp


class PressurantReserve(StrEnum):
    UNRESOLVED = "unresolved"
    NOT_APPLICABLE = "not_applicable"
    STATED_MASS = "stated_mass"              # kg
    STATED_FRACTION = "stated_fraction"      # of the initial bottle mass


def _finite_or_none(name: str, value: float | None) -> None:
    if value is not None and not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


@dataclass(frozen=True, slots=True)
class BranchGasVolumes:
    """One branch's gas volumes, copied from SYS-3. m^3."""

    tank_volume: float
    gas_volume_start: float
    expelled_volume: float
    gas_volume_end: float
    residual_volume: float

    def __post_init__(self) -> None:
        for name in ("tank_volume", "gas_volume_start", "expelled_volume", "gas_volume_end",
                     "residual_volume"):
            value = getattr(self, name)
            if not (math.isfinite(value) and value >= 0.0):
                raise ValueError(f"{name} must be finite and at or above zero")

    def to_dict(self) -> dict[str, float]:
        return {"tank_volume_m3": self.tank_volume,
                "gas_volume_start_m3": self.gas_volume_start,
                "expelled_volume_m3": self.expelled_volume,
                "gas_volume_end_m3": self.gas_volume_end,
                "residual_volume_m3": self.residual_volume}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BranchGasVolumes":
        return cls(float(payload["tank_volume_m3"]), float(payload["gas_volume_start_m3"]),
                   float(payload["expelled_volume_m3"]), float(payload["gas_volume_end_m3"]),
                   float(payload["residual_volume_m3"]))


@dataclass(frozen=True, slots=True)
class PressurizationBasis:
    """The SYS-3 study a pressurization study reads, with its chain."""

    management: Upstream
    sizing_fingerprint: str
    pair_label: str
    oxidiser: str
    fuel: str
    oxidiser_gas: BranchGasVolumes
    fuel_gas: BranchGasVolumes

    def gas_of(self, branch: Branch) -> BranchGasVolumes:
        return self.oxidiser_gas if branch is Branch.OXIDISER else self.fuel_gas

    def propellant_of(self, branch: Branch) -> str:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"management": self.management.to_dict(),
                "sizing_fingerprint": self.sizing_fingerprint, "pair_label": self.pair_label,
                "oxidiser": self.oxidiser, "fuel": self.fuel,
                "oxidiser_gas": self.oxidiser_gas.to_dict(),
                "fuel_gas": self.fuel_gas.to_dict()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PressurizationBasis":
        return cls(management=Upstream.from_dict(payload["management"]),
                   sizing_fingerprint=str(payload["sizing_fingerprint"]),
                   pair_label=str(payload["pair_label"]), oxidiser=str(payload["oxidiser"]),
                   fuel=str(payload["fuel"]),
                   oxidiser_gas=BranchGasVolumes.from_dict(payload["oxidiser_gas"]),
                   fuel_gas=BranchGasVolumes.from_dict(payload["fuel_gas"]))


_NUMBERS = ("gas_constant", "exponent", "required_pressure", "tank_pressure",
            "tank_gas_temperature", "bottle_initial_pressure", "bottle_initial_temperature",
            "bottle_final_pressure", "reserve_value", "initial_pressure",
            "initial_temperature")


@dataclass(frozen=True, slots=True)
class PressurizationBranchDefinition:
    """One branch's stated pressurization. Complete by construction for its
    mode; the relations check domains.

    Attributes:
        mode: Regulated, blowdown, or a recorded intent.
        gas_name / gas_constant: The pressurant as stated, R in J/(kg K).
        exponent: n of p V^n = const; 1 is isothermal.
        required_source / required_pressure / required_reason: Where the
            required tank pressure comes from; the value (Pa) when resolved,
            otherwise why not. A LIQ-6 value is copied with ``required_upstream``.
        tank_pressure / tank_gas_temperature_mode / tank_gas_temperature /
        bottle_* / ullage_source / reserve_*: Regulated mode.
        initial_pressure / initial_temperature: Blowdown mode.
    """

    branch: Branch
    mode: PressurizationMode
    gas_name: str
    gas_constant: float | None
    exponent: float | None
    required_source: RequiredSource
    required_pressure: float | None
    required_reason: str
    required_upstream: Upstream | None
    tank_pressure: float | None = None
    tank_gas_temperature_mode: TankGasTemperature | None = None
    tank_gas_temperature: float | None = None
    bottle_initial_pressure: float | None = None
    bottle_initial_temperature: float | None = None
    bottle_final_pressure: float | None = None
    ullage_source: UllageSource | None = None
    reserve_mode: PressurantReserve = PressurantReserve.UNRESOLVED
    reserve_value: float | None = None
    initial_pressure: float | None = None
    initial_temperature: float | None = None
    intent_note: str = ""

    def __post_init__(self) -> None:
        for name in _NUMBERS:
            _finite_or_none(name, getattr(self, name))
        regulated = self.mode is PressurizationMode.REGULATED
        blowdown = self.mode is PressurizationMode.BLOWDOWN
        if self.mode.executable and (self.gas_constant is None or self.exponent is None):
            raise ValueError("an executable mode states its gas constant and exponent")
        if regulated != all(v is not None for v in (
                self.tank_pressure, self.tank_gas_temperature_mode,
                self.bottle_initial_pressure, self.bottle_initial_temperature,
                self.bottle_final_pressure, self.ullage_source)):
            raise ValueError("the regulated inputs are stated exactly in regulated mode")
        if blowdown != (self.initial_pressure is not None and self.initial_temperature
                        is not None):
            raise ValueError("the blowdown inputs are stated exactly in blowdown mode")
        stated_temperature = self.tank_gas_temperature_mode is TankGasTemperature.STATED
        if stated_temperature != (self.tank_gas_temperature is not None):
            raise ValueError("a stated tank-gas temperature carries its value")
        stated_reserve = self.reserve_mode in (PressurantReserve.STATED_MASS,
                                               PressurantReserve.STATED_FRACTION)
        if stated_reserve != (self.reserve_value is not None):
            raise ValueError("a stated reserve carries its value")
        if self.required_pressure is None and not self.required_reason.strip():
            raise ValueError("an unresolved required pressure says why")
        if (self.required_source is RequiredSource.INJECTOR) != (self.required_upstream
                                                                is not None):
            raise ValueError("a LIQ-6 required pressure names its upstream")

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "branch": self.branch.value, "mode": self.mode.value, "gas_name": self.gas_name,
            "required_source": self.required_source.value,
            "required_reason": self.required_reason,
            "required_upstream": (None if self.required_upstream is None
                                  else self.required_upstream.to_dict()),
            "tank_gas_temperature_mode": (None if self.tank_gas_temperature_mode is None
                                          else self.tank_gas_temperature_mode.value),
            "ullage_source": None if self.ullage_source is None else self.ullage_source.value,
            "reserve_mode": self.reserve_mode.value,
            "intent_note": self.intent_note,
        }
        out.update({name: getattr(self, name) for name in _NUMBERS})
        return out

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PressurizationBranchDefinition":
        def number(name: str) -> float | None:
            value = payload.get(name)
            return None if value is None else float(value)

        upstream = payload.get("required_upstream")
        temperature_mode = payload.get("tank_gas_temperature_mode")
        ullage = payload.get("ullage_source")
        return cls(
            branch=Branch(payload["branch"]), mode=PressurizationMode(payload["mode"]),
            gas_name=str(payload["gas_name"]),
            required_source=RequiredSource(payload["required_source"]),
            required_reason=str(payload.get("required_reason", "")),
            required_upstream=None if upstream is None else Upstream.from_dict(upstream),
            tank_gas_temperature_mode=(None if temperature_mode is None
                                       else TankGasTemperature(temperature_mode)),
            ullage_source=None if ullage is None else UllageSource(ullage),
            reserve_mode=PressurantReserve(payload["reserve_mode"]),
            intent_note=str(payload.get("intent_note", "")),
            **{name: number(name) for name in _NUMBERS})


@dataclass(frozen=True, slots=True)
class PressurizationDefinition:
    basis: PressurizationBasis
    oxidiser: PressurizationBranchDefinition
    fuel: PressurizationBranchDefinition

    def __post_init__(self) -> None:
        if self.oxidiser.branch is not Branch.OXIDISER or self.fuel.branch is not Branch.FUEL:
            raise ValueError("the oxidiser and fuel branches are each in their own place")

    def branch(self, branch: Branch) -> PressurizationBranchDefinition:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"basis": self.basis.to_dict(), "oxidiser": self.oxidiser.to_dict(),
                "fuel": self.fuel.to_dict()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PressurizationDefinition":
        return cls(basis=PressurizationBasis.from_dict(payload["basis"]),
                   oxidiser=PressurizationBranchDefinition.from_dict(payload["oxidiser"]),
                   fuel=PressurizationBranchDefinition.from_dict(payload["fuel"]))

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


PRESSURIZATION_BRANCH_QUANTITIES: tuple[Quantity, ...] = (
    Quantity("required_pressure", "Required tank pressure", "requirement", "Pa",
             "Stated, or the LIQ-6 ledger's required pressure"),
    Quantity("tank_pressure", "Regulated tank pressure pp", "requirement", "Pa", "Stated"),
    Quantity("pressure_margin", "Margin: pp − required", "requirement", "Pa", ""),
    Quantity("gas_constant", "Gas constant R", "gas", "J/(kg K)", "Stated with the gas"),
    Quantity("exponent", "Expansion exponent n", "gas", "", "Stated; 1 is isothermal"),
    Quantity("gas_volume_start", "Gas volume at the start", "ullage", "m3", "SYS-3"),
    Quantity("gas_volume_end", "Gas volume at the end", "ullage", "m3", "SYS-3"),
    Quantity("fill_volume", "Volume the bottle fills", "regulated", "m3",
             "Expelled liquid, plus the start ullage if the bottle fills it"),
    Quantity("tank_gas_temperature", "Tank gas temperature Tp", "regulated", "K",
             "Stated, T0 (Eq. 6-7) or Tg (Example 6-2)"),
    Quantity("delivered_mass", "Gas delivered to the tank mp", "regulated", "kg",
             "pp Vp / (R Tp)"),
    Quantity("bottle_initial_pressure", "Bottle pressure p0", "regulated", "Pa", "Stated"),
    Quantity("bottle_initial_temperature", "Bottle temperature T0", "regulated", "K", "Stated"),
    Quantity("bottle_final_pressure", "Bottle pressure at the end pg", "regulated", "Pa",
             "Stated; the regulator's lowest inlet pressure"),
    Quantity("bottle_final_temperature", "Bottle temperature at the end Tg", "regulated", "K",
             "T0 (pg/p0)^((n−1)/n)"),
    Quantity("regulator_drop_end", "Regulator inlet − outlet at the end", "regulated", "Pa",
             "pg − pp"),
    Quantity("bottle_volume", "Bottle volume V0", "regulated", "m3",
             "mp R / (p0/T0 − pg/Tg), Sutton Eq. 6-5"),
    Quantity("initial_mass", "Pressurant in the bottle m0", "regulated", "kg", "p0 V0 / (R T0)"),
    Quantity("bottle_residual_mass", "Left in the bottle mg", "regulated", "kg",
             "pg V0 / (R Tg)"),
    Quantity("reserve_mass", "Pressurant reserve", "regulated", "kg",
             "Stated mass, or a stated fraction of m0"),
    Quantity("loaded_pressurant", "Pressurant loaded", "regulated", "kg", "m0 + reserve"),
    Quantity("bottle_volume_with_reserve", "Bottle volume with the reserve", "regulated", "m3",
             "Reserve stored at p0 and T0"),
    Quantity("initial_pressure", "Initial tank pressure", "blowdown", "Pa", "Stated"),
    Quantity("initial_temperature", "Initial gas temperature", "blowdown", "K", "Stated"),
    Quantity("gas_mass", "Ullage gas mass", "blowdown", "kg", "pi Vi / (R Ti)"),
    Quantity("blowdown_ratio", "Blowdown ratio Vf/Vi", "blowdown", "", ""),
    Quantity("final_pressure", "End-of-burn pressure", "blowdown", "Pa", "pi (Vi/Vf)^n"),
    Quantity("final_temperature", "End-of-burn gas temperature", "blowdown", "K",
             "Ti (Vi/Vf)^(n−1)"),
    Quantity("margin_start", "Margin at the start", "blowdown", "Pa", "pi − required"),
    Quantity("margin_end", "Margin at the end", "blowdown", "Pa", "pf − required"),
    Quantity("mass_closure", "Mass closure", "closure", "",
             "(mg + mp)/m0 − 1, or pf Vf/(R Tf)/m − 1"),
)

PRESSURIZATION_TOTALS: tuple[Quantity, ...] = (
    Quantity("pressurant_total", "Pressurant, both branches", "total", "kg",
             "Loaded regulated pressurant and blowdown ullage gas"),
    Quantity("bottle_volume_total", "Bottle volume, both branches", "total", "m3",
             "Regulated branches, with reserve"),
)

PRESSURIZATION_LABELS = ("mode", "gas", "expansion", "tank_gas_temperature_basis",
                         "required_source", "feed_check", "intent")

register_schema(PRESSURIZATION_SCHEMA, PRESSURIZATION_SCHEMA_VERSION, PressurizationDefinition,
                PRESSURIZATION_BRANCH_QUANTITIES, PRESSURIZATION_TOTALS,
                PRESSURIZATION_LABELS)
