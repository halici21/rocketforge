"""SYS-3 -- propellant management: intent and first-order bookkeeping, per branch.

A management study takes a current, complete SYS-1 inventory and the current
SYS-2 tanks built on it, copied verbatim, and per branch what the user
states: the management mode (settled free surface, a positive-expulsion
device or a surface-tension PMD), the acceleration environment and whether a
settling acceleration is intended. It answers with the liquid and gas volumes
from loading to the end of the burn and the outlet-availability *declaration*
with its basis. The relations are in
:mod:`rocketforge.engineering.propulsion_system.propellant_management`.

* **The expulsion efficiency is SYS-1's.** It is never assigned from a device
  type.
* **No dynamics.** No slosh modes, damping, frequency, control coupling,
  CFD, screen pore sizing or diaphragm stress.
* **No false availability.** An availability state is a declaration with its
  basis; low-gravity feed is never claimed from geometry.

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
    "MANAGEMENT_BRANCH_QUANTITIES",
    "MANAGEMENT_LABELS",
    "MANAGEMENT_SCHEMA",
    "BranchStorage",
    "Environment",
    "ManagementBasis",
    "ManagementBranchDefinition",
    "ManagementDefinition",
    "ManagementMode",
    "SettlingIntent",
]

MANAGEMENT_SCHEMA: Final = "rocketforge.propellant-management"
MANAGEMENT_SCHEMA_VERSION: Final = 1


class ManagementMode(StrEnum):
    SETTLED = "settled"
    DIAPHRAGM = "diaphragm"
    BLADDER = "bladder"
    PISTON = "piston"
    BELLOWS = "bellows"
    SURFACE_TENSION = "surface_tension"


class Environment(StrEnum):
    ACCELERATED = "accelerated"
    LOW_GRAVITY = "low_gravity"
    UNRESOLVED = "unresolved"


class SettlingIntent(StrEnum):
    REQUIRED = "required"
    NOT_REQUIRED = "not_required"
    UNRESOLVED = "unresolved"


def _positive(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0.0


@dataclass(frozen=True, slots=True)
class BranchStorage:
    """One branch's inventory and tank, copied from SYS-1 and SYS-2. SI."""

    loaded_mass: float
    present_mass: float
    available_mass: float
    residual_mass: float
    boiloff_mass: float
    expulsion_efficiency: float
    expulsion_source: str            # "stated" | "derived from the stated residual"
    density: float
    tank_volume: float
    liquid_volume: float
    ullage_volume: float
    ullage_fraction: float
    fill_fraction: float

    def __post_init__(self) -> None:
        for name in ("loaded_mass", "present_mass", "available_mass", "density", "tank_volume",
                     "liquid_volume", "fill_fraction", "expulsion_efficiency"):
            if not _positive(getattr(self, name)):
                raise ValueError(f"{name} must be finite and positive")
        for name in ("residual_mass", "boiloff_mass", "ullage_volume", "ullage_fraction"):
            value = getattr(self, name)
            if not (math.isfinite(value) and value >= 0.0):
                raise ValueError(f"{name} must be finite and at or above zero")

    def to_dict(self) -> dict[str, Any]:
        return {"loaded_mass_kg": self.loaded_mass, "present_mass_kg": self.present_mass,
                "available_mass_kg": self.available_mass, "residual_mass_kg": self.residual_mass,
                "boiloff_mass_kg": self.boiloff_mass,
                "expulsion_efficiency": self.expulsion_efficiency,
                "expulsion_source": self.expulsion_source, "density_kg_m3": self.density,
                "tank_volume_m3": self.tank_volume, "liquid_volume_m3": self.liquid_volume,
                "ullage_volume_m3": self.ullage_volume, "ullage_fraction": self.ullage_fraction,
                "fill_fraction": self.fill_fraction}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BranchStorage":
        return cls(
            loaded_mass=float(payload["loaded_mass_kg"]),
            present_mass=float(payload["present_mass_kg"]),
            available_mass=float(payload["available_mass_kg"]),
            residual_mass=float(payload["residual_mass_kg"]),
            boiloff_mass=float(payload["boiloff_mass_kg"]),
            expulsion_efficiency=float(payload["expulsion_efficiency"]),
            expulsion_source=str(payload["expulsion_source"]),
            density=float(payload["density_kg_m3"]), tank_volume=float(payload["tank_volume_m3"]),
            liquid_volume=float(payload["liquid_volume_m3"]),
            ullage_volume=float(payload["ullage_volume_m3"]),
            ullage_fraction=float(payload["ullage_fraction"]),
            fill_fraction=float(payload["fill_fraction"]))


@dataclass(frozen=True, slots=True)
class ManagementBasis:
    """The SYS-1 inventory and SYS-2 tanks a management study reads."""

    inventory: Upstream
    tanks: Upstream
    sizing_fingerprint: str
    pair_label: str
    oxidiser: str
    fuel: str
    oxidiser_storage: BranchStorage
    fuel_storage: BranchStorage

    def storage_of(self, branch: Branch) -> BranchStorage:
        return self.oxidiser_storage if branch is Branch.OXIDISER else self.fuel_storage

    def propellant_of(self, branch: Branch) -> str:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"inventory": self.inventory.to_dict(), "tanks": self.tanks.to_dict(),
                "sizing_fingerprint": self.sizing_fingerprint,
                "pair_label": self.pair_label, "oxidiser": self.oxidiser, "fuel": self.fuel,
                "oxidiser_storage": self.oxidiser_storage.to_dict(),
                "fuel_storage": self.fuel_storage.to_dict()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ManagementBasis":
        return cls(inventory=Upstream.from_dict(payload["inventory"]),
                   tanks=Upstream.from_dict(payload["tanks"]),
                   sizing_fingerprint=str(payload["sizing_fingerprint"]),
                   pair_label=str(payload["pair_label"]), oxidiser=str(payload["oxidiser"]),
                   fuel=str(payload["fuel"]),
                   oxidiser_storage=BranchStorage.from_dict(payload["oxidiser_storage"]),
                   fuel_storage=BranchStorage.from_dict(payload["fuel_storage"]))


@dataclass(frozen=True, slots=True)
class ManagementBranchDefinition:
    """One branch's stated management intent."""

    branch: Branch
    mode: ManagementMode
    environment: Environment
    settling: SettlingIntent
    settling_acceleration: float | None      # m/s^2, recorded intent only

    def __post_init__(self) -> None:
        if self.settling_acceleration is not None and not _positive(self.settling_acceleration):
            raise ValueError("a stated settling acceleration is finite and above zero")

    def to_dict(self) -> dict[str, Any]:
        return {"branch": self.branch.value, "mode": self.mode.value,
                "environment": self.environment.value, "settling": self.settling.value,
                "settling_acceleration_m_s2": self.settling_acceleration}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ManagementBranchDefinition":
        a = payload.get("settling_acceleration_m_s2")
        return cls(branch=Branch(payload["branch"]), mode=ManagementMode(payload["mode"]),
                   environment=Environment(payload["environment"]),
                   settling=SettlingIntent(payload["settling"]),
                   settling_acceleration=None if a is None else float(a))


@dataclass(frozen=True, slots=True)
class ManagementDefinition:
    basis: ManagementBasis
    oxidiser: ManagementBranchDefinition
    fuel: ManagementBranchDefinition

    def __post_init__(self) -> None:
        if self.oxidiser.branch is not Branch.OXIDISER or self.fuel.branch is not Branch.FUEL:
            raise ValueError("the oxidiser and fuel branches are each in their own place")

    def branch(self, branch: Branch) -> ManagementBranchDefinition:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"basis": self.basis.to_dict(), "oxidiser": self.oxidiser.to_dict(),
                "fuel": self.fuel.to_dict()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ManagementDefinition":
        return cls(basis=ManagementBasis.from_dict(payload["basis"]),
                   oxidiser=ManagementBranchDefinition.from_dict(payload["oxidiser"]),
                   fuel=ManagementBranchDefinition.from_dict(payload["fuel"]))

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


MANAGEMENT_BRANCH_QUANTITIES: tuple[Quantity, ...] = (
    Quantity("tank_volume", "Tank internal volume", "loading", "m3", "SYS-2"),
    Quantity("density", "Storage density ρ", "loading", "kg/m3", "SYS-2"),
    Quantity("fill_fraction", "Fill fraction at loading", "loading", "", "SYS-2"),
    Quantity("ullage_fraction", "Ullage fraction at loading", "loading", "", "SYS-2"),
    Quantity("ullage_volume", "Ullage volume at loading", "loading", "m3", "SYS-2"),
    Quantity("liquid_volume_present", "Liquid at the start of the burn", "burn", "m3",
             "Present mass / ρ (loaded less boil-off)"),
    Quantity("gas_volume_start", "Gas volume at the start of the burn", "burn", "m3",
             "V_tank − liquid present"),
    Quantity("ullage_fraction_start", "Gas fraction at the start", "burn", "", ""),
    Quantity("expelled_volume", "Liquid expelled", "burn", "m3", "Available mass / ρ"),
    Quantity("gas_volume_end", "Gas volume at the end of expulsion", "burn", "m3",
             "Start gas + expelled; residual held in the tank"),
    Quantity("ullage_fraction_end", "Gas fraction at the end", "burn", "", ""),
    Quantity("expulsion_efficiency", "Expulsion efficiency", "residual", "",
             "SYS-1; never assigned from the device type"),
    Quantity("residual_mass", "Expected residual", "residual", "kg", "SYS-1"),
    Quantity("residual_volume", "Residual volume", "residual", "m3", "Residual / ρ"),
    Quantity("settling_acceleration", "Stated settling acceleration", "intent", "m/s2",
             "Recorded intent; settling is not evaluated"),
    Quantity("fill_ullage_closure", "Fill + ullage closure", "closure", "",
             "Fill + ullage fraction − 1"),
    Quantity("volume_closure", "Volume closure", "closure", "",
             "(gas at end + residual volume) / V_tank − 1"),
    Quantity("inventory_closure", "Inventory closure", "closure", "",
             "(available + residual + boil-off) / loaded − 1"),
)

MANAGEMENT_LABELS = ("management_mode", "environment", "settling", "outlet_availability",
                     "availability_basis", "expulsion_source")

register_schema(MANAGEMENT_SCHEMA, MANAGEMENT_SCHEMA_VERSION, ManagementDefinition,
                MANAGEMENT_BRANCH_QUANTITIES, (), MANAGEMENT_LABELS)
