"""SYS-5 -- the liquid feed network from tank outlet to injector inlet, per branch.

A feed-network study takes a current SYS-4 pressurization study (the tank
pressures it provides) and the current LIQ-6 injector study on the same
sizing (the flows, the liquid density at the injector inlet and the pressure
ledger), copied verbatim, and per branch an ordered series of components the
user states. It answers with each component's pressure change, the network's
total, the pressure the injector inlet needs and the margin of each tank
pressure over the requirement. The relations are in
:mod:`rocketforge.engineering.propulsion_system.feed_network`.

**No loss is counted twice.** The LIQ-6 ledger's feed-line and valve terms are
the span this network models: they are always replaced, and recorded as
excluded with their LIQ-6 value. Chamber pressure, injector drop,
cooling-jacket loss and margin lie downstream of the injector-inlet boundary
and are carried. The dynamic head and "other" terms are carried or replaced
as the user states; neither has a default.

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
    "CARRIED_TERMS",
    "CHOSEN_TERMS",
    "FEED_BRANCH_QUANTITIES",
    "FEED_SCHEMA",
    "REPLACED_TERMS",
    "ComponentSpec",
    "DensitySource",
    "FeedBasis",
    "FeedBranchBasis",
    "FeedBranchDefinition",
    "FeedDefinition",
    "LedgerTerm",
    "TermAssignment",
]

FEED_SCHEMA: Final = "rocketforge.feed-network"
FEED_SCHEMA_VERSION: Final = 1

#: LIQ-6 ledger terms by where they lie against this network.
CARRIED_TERMS = ("chamber_pressure", "injector_pressure_drop", "cooling_jacket_loss", "margin")
REPLACED_TERMS = ("feed_line_loss", "valve_loss")
CHOSEN_TERMS = ("dynamic_head", "other_loss")


class TermAssignment(StrEnum):
    CARRIED = "carried"          # counted at the injector-inlet boundary
    REPLACED = "replaced"        # the network models this span; LIQ-6's value is not counted


class DensitySource(StrEnum):
    INJECTOR = "injector"        # LIQ-6's liquid density at the injector inlet
    STATED = "stated"


@dataclass(frozen=True, slots=True)
class LedgerTerm:
    """One LIQ-6 ledger line, copied. ``value`` in Pa when resolved."""

    key: str
    label: str
    status: str
    value: float | None

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "label": self.label, "status": self.status,
                "value_Pa": self.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LedgerTerm":
        value = payload.get("value_Pa")
        return cls(str(payload["key"]), str(payload["label"]), str(payload["status"]),
                   None if value is None else float(value))


@dataclass(frozen=True, slots=True)
class FeedBranchBasis:
    """One branch's upstream state. SI.

    Attributes:
        mass_flow: LIQ-4's, through LIQ-6.
        injector_density: LIQ-6's liquid density at the injector inlet.
        ledger: LIQ-6's pressure ledger, in order.
        tank_pressures: SYS-4's tank pressures, by name ("regulated", or
            "start" and "end" of a blowdown); empty for an intent-only branch.
        pressurization_mode: SYS-4's mode, as a word.
    """

    mass_flow: float
    injector_density: float
    ledger: tuple[LedgerTerm, ...]
    tank_pressures: Mapping[str, float]
    pressurization_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {"mass_flow_kg_s": self.mass_flow, "injector_density_kg_m3": self.injector_density,
                "ledger": [t.to_dict() for t in self.ledger],
                "tank_pressures_Pa": dict(self.tank_pressures),
                "pressurization_mode": self.pressurization_mode}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FeedBranchBasis":
        return cls(float(payload["mass_flow_kg_s"]), float(payload["injector_density_kg_m3"]),
                   tuple(LedgerTerm.from_dict(t) for t in payload["ledger"]),
                   {str(k): float(v) for k, v in dict(payload["tank_pressures_Pa"]).items()},
                   str(payload["pressurization_mode"]))


@dataclass(frozen=True, slots=True)
class FeedBasis:
    pressurization: Upstream
    injector: Upstream
    sizing_fingerprint: str
    pair_label: str
    oxidiser: str
    fuel: str
    oxidiser_basis: FeedBranchBasis
    fuel_basis: FeedBranchBasis

    def of(self, branch: Branch) -> FeedBranchBasis:
        return self.oxidiser_basis if branch is Branch.OXIDISER else self.fuel_basis

    def propellant_of(self, branch: Branch) -> str:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"pressurization": self.pressurization.to_dict(),
                "injector": self.injector.to_dict(),
                "sizing_fingerprint": self.sizing_fingerprint, "pair_label": self.pair_label,
                "oxidiser": self.oxidiser, "fuel": self.fuel,
                "oxidiser_basis": self.oxidiser_basis.to_dict(),
                "fuel_basis": self.fuel_basis.to_dict()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FeedBasis":
        return cls(Upstream.from_dict(payload["pressurization"]),
                   Upstream.from_dict(payload["injector"]), str(payload["sizing_fingerprint"]),
                   str(payload["pair_label"]), str(payload["oxidiser"]), str(payload["fuel"]),
                   FeedBranchBasis.from_dict(payload["oxidiser_basis"]),
                   FeedBranchBasis.from_dict(payload["fuel_basis"]))


_SPEC_FIELDS = ("length", "diameter", "roughness", "loss_coefficient", "pressure_drop", "rise",
                "acceleration")


@dataclass(frozen=True, slots=True)
class ComponentSpec:
    """One stated component: its kind (``engineering...ComponentKind`` value)
    and the inputs that kind states, SI."""

    kind: str
    label: str = ""
    length: float | None = None
    diameter: float | None = None
    roughness: float | None = None
    loss_coefficient: float | None = None
    pressure_drop: float | None = None
    rise: float | None = None
    acceleration: float | None = None

    def __post_init__(self) -> None:
        for name in _SPEC_FIELDS:
            value = getattr(self, name)
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite")

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "label": self.label,
                **{name: getattr(self, name) for name in _SPEC_FIELDS}}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ComponentSpec":
        def number(name: str) -> float | None:
            value = payload.get(name)
            return None if value is None else float(value)

        return cls(str(payload["kind"]), str(payload.get("label", "")),
                   **{name: number(name) for name in _SPEC_FIELDS})


@dataclass(frozen=True, slots=True)
class FeedBranchDefinition:
    branch: Branch
    density_source: DensitySource
    density: float
    viscosity: float | None
    components: tuple[ComponentSpec, ...]
    assignments: Mapping[str, TermAssignment]

    def __post_init__(self) -> None:
        if not (math.isfinite(self.density) and self.density > 0.0):
            raise ValueError("the density is finite and above zero")
        if self.viscosity is not None and not (math.isfinite(self.viscosity)
                                               and self.viscosity > 0.0):
            raise ValueError("a stated viscosity is finite and above zero")
        if set(self.assignments) != set(CHOSEN_TERMS):
            raise ValueError(f"the assignments are exactly {list(CHOSEN_TERMS)}")

    def to_dict(self) -> dict[str, Any]:
        return {"branch": self.branch.value, "density_source": self.density_source.value,
                "density_kg_m3": self.density, "viscosity_Pa_s": self.viscosity,
                "components": [c.to_dict() for c in self.components],
                "assignments": {k: self.assignments[k].value for k in CHOSEN_TERMS}}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FeedBranchDefinition":
        mu = payload.get("viscosity_Pa_s")
        return cls(Branch(payload["branch"]), DensitySource(payload["density_source"]),
                   float(payload["density_kg_m3"]), None if mu is None else float(mu),
                   tuple(ComponentSpec.from_dict(c) for c in payload["components"]),
                   {str(k): TermAssignment(v) for k, v in dict(payload["assignments"]).items()})


@dataclass(frozen=True, slots=True)
class FeedDefinition:
    basis: FeedBasis
    oxidiser: FeedBranchDefinition
    fuel: FeedBranchDefinition

    def __post_init__(self) -> None:
        if self.oxidiser.branch is not Branch.OXIDISER or self.fuel.branch is not Branch.FUEL:
            raise ValueError("the oxidiser and fuel branches are each in their own place")

    def branch(self, branch: Branch) -> FeedBranchDefinition:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"basis": self.basis.to_dict(), "oxidiser": self.oxidiser.to_dict(),
                "fuel": self.fuel.to_dict()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FeedDefinition":
        return cls(FeedBasis.from_dict(payload["basis"]),
                   FeedBranchDefinition.from_dict(payload["oxidiser"]),
                   FeedBranchDefinition.from_dict(payload["fuel"]))

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


FEED_BRANCH_QUANTITIES: tuple[Quantity, ...] = (
    Quantity("mass_flow", "Mass flow", "flow", "kg/s", "LIQ-4, through LIQ-6"),
    Quantity("density", "Liquid density ρ", "flow", "kg/m3", "LIQ-6 injector inlet, or stated"),
    Quantity("viscosity", "Dynamic viscosity μ", "flow", "Pa s", "Stated"),
    Quantity("component_count", "Components in series", "network", "", ""),
    Quantity("network_known_drop", "Resolved network drop", "network", "Pa",
             "Sum of the resolved components"),
    Quantity("network_drop", "Network drop, tank outlet → injector inlet", "network", "Pa",
             "Only when every component is resolved"),
    Quantity("max_continuity_closure", "Largest continuity closure", "network", "",
             "max |ρ v A / ṁ − 1| over the components"),
    Quantity("inlet_required", "Required injector-inlet pressure", "closure", "Pa",
             "Carried LIQ-6 terms: p1 + Δp_inj + jacket + margin (+ chosen)"),
    Quantity("tank_required", "Required tank-outlet pressure", "closure", "Pa",
             "Injector-inlet requirement + network drop"),
    Quantity("liq6_required", "LIQ-6 required pressure, as LIQ-6 gave it", "closure", "Pa",
             "For comparison; its replaced terms are not counted here"),
    Quantity("tank_pressure_regulated", "Tank pressure (regulated)", "closure", "Pa", "SYS-4"),
    Quantity("margin_regulated", "Margin (regulated)", "closure", "Pa",
             "Tank pressure − required tank-outlet pressure"),
    Quantity("tank_pressure_start", "Tank pressure at the start (blowdown)", "closure", "Pa",
             "SYS-4"),
    Quantity("margin_start", "Margin at the start (blowdown)", "closure", "Pa", ""),
    Quantity("tank_pressure_end", "Tank pressure at the end (blowdown)", "closure", "Pa",
             "SYS-4"),
    Quantity("margin_end", "Margin at the end (blowdown)", "closure", "Pa", ""),
    Quantity("pressure_closure", "Pressure closure", "closure", "",
             "((p_tank − network) − inlet requirement − margin) / p_tank"),
)

FEED_TOTALS: tuple[Quantity, ...] = ()
FEED_LABELS = ("pressurization", "density_source", "feed_check")

register_schema(FEED_SCHEMA, FEED_SCHEMA_VERSION, FeedDefinition, FEED_BRANCH_QUANTITIES,
                FEED_TOTALS, FEED_LABELS)
