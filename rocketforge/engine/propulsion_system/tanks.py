"""SYS-2 -- propellant tank volume, geometry and packaging, per branch.

A tank study takes an accepted, complete SYS-1 inventory's loaded masses,
copied verbatim, and per branch what the user states: the storage density or
the state a validated fluid model evaluates it at, the ullage, the shape and
the one dimension that fixes it. It answers with the liquid, ullage and tank
volumes and the internal geometry. The relations are in
:mod:`rocketforge.engineering.propulsion_system.tank_geometry`.

* **No structure.** Internal geometry only: no wall thickness, stress, MEOP,
  dry mass, insulation, common bulkhead or boil-off.
* **Nothing is chosen.** No shape, diameter, ullage or density has a default,
  and no optimum is searched for. A requested geometry that cannot hold the
  volume is refused.

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
    "TANK_BRANCH_QUANTITIES",
    "TANK_SCHEMA",
    "TANK_TOTALS",
    "DensitySource",
    "TankBranchDefinition",
    "TankDefinition",
    "TanksBasis",
    "TankShape",
    "SizingMode",
    "UllageMode",
]

TANK_SCHEMA: Final = "rocketforge.propellant-tanks"
TANK_SCHEMA_VERSION: Final = 1


class DensitySource(StrEnum):
    STATED = "stated"
    FLUID_MODEL = "fluid_model"          # validated liquid binding, at a stated storage state


class UllageMode(StrEnum):
    FRACTION = "fraction"                # of the tank volume
    VOLUME = "volume"                    # m^3


class TankShape(StrEnum):
    SPHERE = "sphere"
    CYLINDER_HEMISPHERICAL = "cylinder_hemispherical"
    CYLINDER_ELLIPSOIDAL = "cylinder_ellipsoidal"


class SizingMode(StrEnum):
    VOLUME = "volume"
    STATED_DIAMETER = "stated_diameter"
    STATED_LENGTH = "stated_length"


def _positive(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0.0


@dataclass(frozen=True, slots=True)
class TanksBasis:
    """The loaded masses of an accepted, complete SYS-1 inventory, copied."""

    inventory: Upstream
    sizing_fingerprint: str
    pair_label: str
    oxidiser: str
    fuel: str
    oxidiser_loaded_mass: float
    fuel_loaded_mass: float

    def __post_init__(self) -> None:
        if not (_positive(self.oxidiser_loaded_mass) and _positive(self.fuel_loaded_mass)):
            raise ValueError("the loaded masses must be finite and positive")
        if self.inventory.status != "ok":
            raise ValueError("a tank basis comes from a complete inventory only")

    def loaded_mass_of(self, branch: Branch) -> float:
        return self.oxidiser_loaded_mass if branch is Branch.OXIDISER else self.fuel_loaded_mass

    def propellant_of(self, branch: Branch) -> str:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"inventory": self.inventory.to_dict(),
                "sizing_fingerprint": self.sizing_fingerprint, "pair_label": self.pair_label,
                "oxidiser": self.oxidiser, "fuel": self.fuel,
                "oxidiser_loaded_mass_kg": self.oxidiser_loaded_mass,
                "fuel_loaded_mass_kg": self.fuel_loaded_mass}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TanksBasis":
        return cls(inventory=Upstream.from_dict(payload["inventory"]),
                   sizing_fingerprint=str(payload["sizing_fingerprint"]),
                   pair_label=str(payload["pair_label"]), oxidiser=str(payload["oxidiser"]),
                   fuel=str(payload["fuel"]),
                   oxidiser_loaded_mass=float(payload["oxidiser_loaded_mass_kg"]),
                   fuel_loaded_mass=float(payload["fuel_loaded_mass_kg"]))


def _optional(payload: Mapping[str, Any], key: str) -> float | None:
    value = payload.get(key)
    return None if value is None else float(value)


@dataclass(frozen=True, slots=True)
class TankBranchDefinition:
    """One tank's stated inputs. Complete by construction; domains are the
    relations' to check.

    Attributes:
        density_source / density: kg/m^3 when stated.
        storage_temperature / storage_pressure: K and Pa, the state a
            fluid-model density is evaluated at; absent when stated.
        ullage_mode / ullage_value: a fraction of the tank, or m^3.
        shape / sizing_mode: the geometry family and what fixes it.
        diameter / total_length: m, the stated dimension of the mode.
        dome_ratio: k = h/R, for ellipsoidal domes only.
        envelope_diameter / envelope_length: m, optional limits.
    """

    branch: Branch
    density_source: DensitySource
    density: float | None
    storage_temperature: float | None
    storage_pressure: float | None
    ullage_mode: UllageMode
    ullage_value: float
    shape: TankShape
    sizing_mode: SizingMode
    diameter: float | None
    total_length: float | None
    dome_ratio: float | None
    envelope_diameter: float | None
    envelope_length: float | None

    def __post_init__(self) -> None:
        stated = self.density_source is DensitySource.STATED
        if stated != (self.density is not None):
            raise ValueError("a stated density carries its value")
        if stated == (self.storage_temperature is not None and self.storage_pressure is not None) \
                or (self.storage_temperature is None) != (self.storage_pressure is None):
            raise ValueError("a fluid-model density carries its storage temperature and "
                             "pressure; a stated one carries neither")
        sphere = self.shape is TankShape.SPHERE
        if sphere != (self.sizing_mode is SizingMode.VOLUME):
            raise ValueError("a sphere, and only a sphere, is fixed by its volume")
        if (self.sizing_mode is SizingMode.STATED_DIAMETER) != (self.diameter is not None):
            raise ValueError("a diameter is stated exactly in stated-diameter mode")
        if (self.sizing_mode is SizingMode.STATED_LENGTH) != (self.total_length is not None):
            raise ValueError("a length is stated exactly in stated-length mode")
        if (self.shape is TankShape.CYLINDER_ELLIPSOIDAL) != (self.dome_ratio is not None):
            raise ValueError("a dome ratio is stated exactly for ellipsoidal domes")
        for name in ("density", "storage_temperature", "storage_pressure", "ullage_value",
                     "diameter", "total_length", "dome_ratio", "envelope_diameter",
                     "envelope_length"):
            value = getattr(self, name)
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite")

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch.value,
            "density_source": self.density_source.value,
            "density_kg_m3": self.density,
            "storage_temperature_K": self.storage_temperature,
            "storage_pressure_Pa": self.storage_pressure,
            "ullage_mode": self.ullage_mode.value,
            "ullage_value": self.ullage_value,
            "shape": self.shape.value,
            "sizing_mode": self.sizing_mode.value,
            "diameter_m": self.diameter,
            "total_length_m": self.total_length,
            "dome_ratio": self.dome_ratio,
            "envelope_diameter_m": self.envelope_diameter,
            "envelope_length_m": self.envelope_length,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TankBranchDefinition":
        return cls(
            branch=Branch(payload["branch"]),
            density_source=DensitySource(payload["density_source"]),
            density=_optional(payload, "density_kg_m3"),
            storage_temperature=_optional(payload, "storage_temperature_K"),
            storage_pressure=_optional(payload, "storage_pressure_Pa"),
            ullage_mode=UllageMode(payload["ullage_mode"]),
            ullage_value=float(payload["ullage_value"]),
            shape=TankShape(payload["shape"]),
            sizing_mode=SizingMode(payload["sizing_mode"]),
            diameter=_optional(payload, "diameter_m"),
            total_length=_optional(payload, "total_length_m"),
            dome_ratio=_optional(payload, "dome_ratio"),
            envelope_diameter=_optional(payload, "envelope_diameter_m"),
            envelope_length=_optional(payload, "envelope_length_m"),
        )


@dataclass(frozen=True, slots=True)
class TankDefinition:
    """Everything a tank study is, before it is computed."""

    basis: TanksBasis
    oxidiser: TankBranchDefinition
    fuel: TankBranchDefinition

    def __post_init__(self) -> None:
        if self.oxidiser.branch is not Branch.OXIDISER or self.fuel.branch is not Branch.FUEL:
            raise ValueError("the oxidiser and fuel tanks are each in their own place")

    def branch(self, branch: Branch) -> TankBranchDefinition:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"basis": self.basis.to_dict(), "oxidiser": self.oxidiser.to_dict(),
                "fuel": self.fuel.to_dict()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TankDefinition":
        return cls(basis=TanksBasis.from_dict(payload["basis"]),
                   oxidiser=TankBranchDefinition.from_dict(payload["oxidiser"]),
                   fuel=TankBranchDefinition.from_dict(payload["fuel"]))

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


TANK_BRANCH_QUANTITIES: tuple[Quantity, ...] = (
    Quantity("liquid_mass", "Loaded liquid mass", "volume", "kg", "From the SYS-1 inventory"),
    Quantity("density", "Storage density ρ", "volume", "kg/m3",
             "Stated, or the validated fluid model at the storage state"),
    Quantity("liquid_volume", "Liquid volume", "volume", "m3", "m / ρ"),
    Quantity("ullage_fraction", "Ullage / tank volume", "volume", "", "Stated, or V_u / V_tank"),
    Quantity("ullage_volume", "Ullage volume", "volume", "m3", "Stated, or V_tank − V_liquid"),
    Quantity("tank_volume", "Tank internal volume", "volume", "m3",
             "V_liquid / (1 − u), or V_liquid + V_u"),
    Quantity("fill_fraction", "Fill fraction", "volume", "", "V_liquid / V_tank"),
    Quantity("diameter", "Internal diameter", "geometry", "m",
             "Stated, or solved from the volume"),
    Quantity("barrel_length", "Cylindrical barrel length", "geometry", "m",
             "Solved, or from the stated length"),
    Quantity("dome_ratio", "Dome height / radius k", "geometry", "", "1 for a hemisphere"),
    Quantity("dome_height", "Dome height", "geometry", "m", "k R"),
    Quantity("dome_volume", "Volume of one dome", "geometry", "m3", "2/3 π R² h"),
    Quantity("total_length", "Total internal length", "geometry", "m",
             "Barrel + 2 domes; the diameter for a sphere"),
    Quantity("surface_area", "Internal surface area", "geometry", "m2",
             "Analytic: sphere, cylinder and half-spheroid areas"),
    Quantity("geometric_volume", "Volume from the dimensions", "closure", "m3", ""),
    Quantity("volume_closure", "Geometric closure", "closure", "",
             "Volume from the dimensions / tank volume − 1"),
    Quantity("mass_closure", "Mass closure", "closure", "", "ρ V_liquid / m − 1"),
    Quantity("ullage_closure", "Ullage closure", "closure", "",
             "(V_liquid + V_ullage) / V_tank − 1"),
)

TANK_TOTALS: tuple[Quantity, ...] = (
    Quantity("tank_volume_total", "Tank internal volume", "total", "m3", "Oxidiser + fuel"),
    Quantity("liquid_volume_total", "Liquid volume", "total", "m3", "Oxidiser + fuel"),
    Quantity("ullage_volume_total", "Ullage volume", "total", "m3", "Oxidiser + fuel"),
    Quantity("surface_area_total", "Internal surface area", "total", "m2", "Oxidiser + fuel"),
)

TANK_LABELS = ("shape", "density_source")

register_schema(TANK_SCHEMA, TANK_SCHEMA_VERSION, TankDefinition, TANK_BRANCH_QUANTITIES,
                TANK_TOTALS, TANK_LABELS)
