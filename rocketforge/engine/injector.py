"""Injector hydraulics and branch pressure budgets at one accepted sizing.

LIQ-6. An injector study takes the flows of a LIQ-4 sizing -- the oxidiser and
fuel mass flows, O/F, chamber pressure, stream temperatures and the sizing's
identity, copied verbatim -- and, per propellant branch, stated hydraulic
inputs (injector pressure drop, discharge coefficient, liquid density or its
validated source, and optionally a hole count or diameter) and stated pressure
terms. It answers, per branch, with the total injector orifice area and
injection velocity, and a pressure ledger with the minimum known and, when
complete, the required upstream pressure. This module is the data; the
relations are in :mod:`rocketforge.engineering.injector`.

Rules that shape it:

* **Ownership is kept.** LIQ-4 owns the flows, O/F and chamber pressure.
  :class:`FlowBasis` is a copy, so a result is traceable to the exact sizing.
* **Nothing hydraulic is defaulted.** Cd, density, dp and the hole count or
  diameter are stated; a density from a fluid model says which model, at
  which state.
* **An unknown loss stays unknown.** A pressure term is stated, declared not
  applicable, or unresolved. Unresolved never becomes zero.
* **No verdicts.** Nothing here says an injector is stable, efficient, or
  that a pressure is achievable.

SI units throughout.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Final

from .requirement import RequirementFormatError

__all__ = [
    "BRANCH_QUANTITIES",
    "INJECTOR_SCHEMA",
    "INJECTOR_SCHEMA_VERSION",
    "LOSS_TERMS",
    "PAIR_QUANTITIES",
    "Branch",
    "BranchDefinition",
    "BranchQuantity",
    "BranchResult",
    "DensitySource",
    "FlowBasis",
    "HoleMode",
    "InjectorDefinition",
    "InjectorResult",
    "InjectorStatus",
    "LedgerLine",
    "LossMode",
    "LossSetting",
]

INJECTOR_SCHEMA: Final = "rocketforge.liquid-injector"
INJECTOR_SCHEMA_VERSION: Final = 1


class Branch(StrEnum):
    OXIDISER = "oxidiser"
    FUEL = "fuel"


class DensitySource(StrEnum):
    STATED = "stated"                # the user's number
    FLUID_MODEL = "fluid_model"      # a validated fluid-property model, at a recorded state


class HoleMode(StrEnum):
    AREA = "area"                    # total flow area only
    HOLE_COUNT = "hole_count"        # N stated -> equal-hole diameter
    HOLE_DIAMETER = "hole_diameter"  # d stated -> equivalent count


class LossMode(StrEnum):
    UNRESOLVED = "unresolved"
    STATED = "stated"                # value: Pa
    NOT_APPLICABLE = "not_applicable"
    LINE_DIAMETER = "line_diameter"  # dynamic head only; value: line diameter, m


class InjectorStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"              # computed; an advisory applies
    REFUSED = "refused"              # a branch could not be computed


#: The stated pressure terms after chamber pressure and injector drop, in ledger
#: order: (key, label, Sutton basis). Chamber pressure and the injector drop are
#: always resolved from the basis and the hydraulic inputs.
LOSS_TERMS: tuple[tuple[str, str, str], ...] = (
    ("feed_line_loss", "Feed-line loss", "Sutton Eq. 11-6: piping"),
    ("valve_loss", "Valves and components", "Sutton Eqs. 10-7, 11-6: valves"),
    ("cooling_jacket_loss", "Cooling-jacket loss", "Sutton Eqs. 10-7, 11-6: dp_j"),
    ("dynamic_head", "Dynamic flow head ½ρv²", "Sutton Eq. 11-6: 1/2 rho v^2"),
    ("other_loss", "Other stated losses", "Stated by the user"),
    ("margin", "Design / calibration margin", "Sutton §11.5: extra pressure-drop margin"),
)
_LOSS_KEYS = tuple(key for key, _label, _basis in LOSS_TERMS)


@dataclass(frozen=True, slots=True)
class BranchQuantity:
    key: str
    label: str
    group: str               # "flow" | "orifice" | "holes" | "budget" | "closure"
    note: str = ""


#: Everything a branch reports, in display order. SI.
BRANCH_QUANTITIES: tuple[BranchQuantity, ...] = (
    BranchQuantity("mass_flow", "Mass flow", "flow", "From the LIQ-4 sizing"),
    BranchQuantity("density", "Liquid density ρ", "flow", "Stated, or the validated fluid model"),
    BranchQuantity("volumetric_flow", "Volumetric flow Q", "flow", "mdot / ρ (Sutton Eq. 8-2)"),
    BranchQuantity("pressure_drop", "Injector pressure drop Δp", "orifice", "Stated"),
    BranchQuantity("pressure_drop_ratio", "Δp / chamber pressure", "orifice",
                   "Stability-relevant; stability is not evaluated"),
    BranchQuantity("discharge_coefficient", "Discharge coefficient Cd", "orifice", "Stated"),
    BranchQuantity("flow_area", "Total orifice area A", "orifice",
                   "mdot / (Cd √(2ρΔp)) (Sutton Eq. 8-2)"),
    BranchQuantity("effective_area", "Effective area Cd·A", "orifice", ""),
    BranchQuantity("injection_velocity", "Injection velocity v", "orifice",
                   "Cd √(2Δp/ρ) (Sutton Eq. 8-5)"),
    BranchQuantity("hole_count", "Hole count N", "holes",
                   "Stated, or A / hole area (exact, may be fractional)"),
    BranchQuantity("hole_diameter", "Hole diameter d", "holes",
                   "Stated, or √(4A / (πN))"),
    BranchQuantity("hole_area", "Area per hole", "holes", "πd²/4"),
    BranchQuantity("whole_hole_count", "Whole holes", "holes", "N rounded up"),
    BranchQuantity("whole_hole_flow_area", "Area with whole holes", "holes", ""),
    BranchQuantity("whole_hole_pressure_drop", "Δp with whole holes", "holes",
                   "Same mass flow: Δp (A / A_whole)² (Sutton Eq. 8-2)"),
    BranchQuantity("line_velocity", "Feed-line velocity", "budget",
                   "mdot / (ρ πD²/4), for the dynamic head"),
    BranchQuantity("minimum_known_pressure", "Minimum known upstream pressure", "budget",
                   "Sum of the resolved terms; the requirement is at least this"),
    BranchQuantity("required_pressure", "Required upstream pressure", "budget",
                   "Only when every term is resolved"),
    BranchQuantity("mass_flow_closure", "Mass-flow closure", "closure",
                   "Cd A √(2ρΔp) / mdot − 1"),
    BranchQuantity("velocity_closure", "Velocity closure", "closure", "ρ v A / mdot − 1"),
    BranchQuantity("hole_area_closure", "Hole-area closure", "closure",
                   "N πd²/4 / A − 1"),
)
_BRANCH_KEYS = frozenset(q.key for q in BRANCH_QUANTITIES)

#: The pair's closures, from the two branches' Eq. 8-2 flows.
PAIR_QUANTITIES: tuple[BranchQuantity, ...] = (
    BranchQuantity("total_mass_flow", "Total mass flow", "pair",
                   "Sum of the two branches' Eq. 8-2 flows"),
    BranchQuantity("oxidiser_fuel_ratio", "O/F from the orifices", "pair",
                   "(Cd A √(2ρΔp))_o / (…)_f (Sutton Eq. 8-3)"),
    BranchQuantity("oxidiser_fuel_ratio_closure", "O/F closure", "pair",
                   "O/F from the orifices / LIQ-4 O/F − 1"),
    BranchQuantity("total_mass_flow_closure", "Total-flow closure", "pair",
                   "Total from the orifices / LIQ-4 mass flow − 1"),
)
_PAIR_KEYS = frozenset(q.key for q in PAIR_QUANTITIES)


def _positive(value: float) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0.0


def _fingerprint(payload: Mapping[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# the flows, as LIQ-4 sized them
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FlowBasis:
    """The flows of an accepted LIQ-4 sizing, copied, with what they came from.

    Attributes:
        sizing_fingerprint / sizing_status / sizing_provenance: The LIQ-4 sizing.
        trade_fingerprint: The LIQ-3 trade the sizing extends.
        pair_key / pair_label / oxidiser / fuel: The propellants, as evaluated.
        oxidiser_fuel_ratio: O/F by mass, as LIQ-4 used it.
        chamber_pressure: Pa, as LIQ-4 used it (LIQ-3's resolved p1).
        oxidiser_temperature / fuel_temperature: K, as LIQ-3 evaluated them.
        mass_flow / oxidiser_mass_flow / fuel_mass_flow: kg/s, LIQ-4's.
        thrust: N, the LIQ-2 target.
    """

    sizing_fingerprint: str
    sizing_status: str
    sizing_provenance: Mapping[str, str]
    trade_fingerprint: str
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
    thrust: float

    def __post_init__(self) -> None:
        for name in ("oxidiser_fuel_ratio", "chamber_pressure", "oxidiser_temperature",
                     "fuel_temperature", "mass_flow", "oxidiser_mass_flow", "fuel_mass_flow",
                     "thrust"):
            if not _positive(getattr(self, name)):
                raise ValueError(f"{name} must be finite and positive")
        if self.sizing_status not in ("ok", "warning"):
            raise ValueError("a flow basis comes from an accepted sizing only")

    def mass_flow_of(self, branch: Branch) -> float:
        return self.oxidiser_mass_flow if branch is Branch.OXIDISER else self.fuel_mass_flow

    def temperature_of(self, branch: Branch) -> float:
        return self.oxidiser_temperature if branch is Branch.OXIDISER else self.fuel_temperature

    def propellant_of(self, branch: Branch) -> str:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {
            "sizing_fingerprint": self.sizing_fingerprint,
            "sizing_status": self.sizing_status,
            "sizing_provenance": dict(self.sizing_provenance),
            "trade_fingerprint": self.trade_fingerprint,
            "pair_key": self.pair_key, "pair_label": self.pair_label,
            "oxidiser": self.oxidiser, "fuel": self.fuel,
            "oxidiser_fuel_ratio": self.oxidiser_fuel_ratio,
            "chamber_pressure_Pa": self.chamber_pressure,
            "oxidiser_temperature_K": self.oxidiser_temperature,
            "fuel_temperature_K": self.fuel_temperature,
            "mass_flow_kg_s": self.mass_flow,
            "oxidiser_mass_flow_kg_s": self.oxidiser_mass_flow,
            "fuel_mass_flow_kg_s": self.fuel_mass_flow,
            "thrust_N": self.thrust,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FlowBasis":
        return cls(
            sizing_fingerprint=str(payload["sizing_fingerprint"]),
            sizing_status=str(payload["sizing_status"]),
            sizing_provenance={str(k): str(v) for k, v in
                               dict(payload.get("sizing_provenance", {})).items()},
            trade_fingerprint=str(payload["trade_fingerprint"]),
            pair_key=str(payload["pair_key"]), pair_label=str(payload["pair_label"]),
            oxidiser=str(payload["oxidiser"]), fuel=str(payload["fuel"]),
            oxidiser_fuel_ratio=float(payload["oxidiser_fuel_ratio"]),
            chamber_pressure=float(payload["chamber_pressure_Pa"]),
            oxidiser_temperature=float(payload["oxidiser_temperature_K"]),
            fuel_temperature=float(payload["fuel_temperature_K"]),
            mass_flow=float(payload["mass_flow_kg_s"]),
            oxidiser_mass_flow=float(payload["oxidiser_mass_flow_kg_s"]),
            fuel_mass_flow=float(payload["fuel_mass_flow_kg_s"]),
            thrust=float(payload["thrust_N"]),
        )


# ---------------------------------------------------------------------------
# the definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LossSetting:
    """One stated pressure term. ``value`` is Pa when STATED, the line diameter
    in m when LINE_DIAMETER, and absent otherwise."""

    mode: LossMode = LossMode.UNRESOLVED
    value: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mode, LossMode):
            raise ValueError("a loss mode must be a LossMode")
        needs_value = self.mode in (LossMode.STATED, LossMode.LINE_DIAMETER)
        if needs_value != (self.value is not None):
            raise ValueError(f"a {self.mode.value} term "
                             + ("needs" if needs_value else "carries no") + " value")
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError("a term's value must be finite")

    def to_dict(self) -> dict[str, Any]:
        return {"mode": self.mode.value, "value": self.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LossSetting":
        value = payload.get("value")
        return cls(LossMode(payload["mode"]), None if value is None else float(value))


@dataclass(frozen=True, slots=True)
class BranchDefinition:
    """One branch's stated inputs. Complete by construction; domains are the
    relations' to check.

    Attributes:
        branch: Oxidiser or fuel.
        pressure_drop: Injector Δp, Pa.
        discharge_coefficient: Cd.
        density_source: Stated, or the validated fluid model.
        density: kg/m^3 when stated; absent for the fluid model.
        density_pressure: Pa, the state a fluid-model density is evaluated at
            (chamber pressure + Δp, the injector inlet); absent when stated.
        hole_mode / hole_count / hole_diameter: How the area is split, if at all.
        losses: Every term of :data:`LOSS_TERMS`, by key.
    """

    branch: Branch
    pressure_drop: float
    discharge_coefficient: float
    density_source: DensitySource
    density: float | None
    density_pressure: float | None
    hole_mode: HoleMode
    hole_count: int | None
    hole_diameter: float | None
    losses: Mapping[str, LossSetting]

    def __post_init__(self) -> None:
        for name in ("pressure_drop", "discharge_coefficient"):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")
        stated = self.density_source is DensitySource.STATED
        if stated != (self.density is not None) or stated == (self.density_pressure is not None):
            raise ValueError("a stated density carries its value; a fluid-model density "
                             "carries the pressure it is evaluated at")
        if (self.hole_mode is HoleMode.HOLE_COUNT) != (self.hole_count is not None):
            raise ValueError("a hole count is stated exactly in hole-count mode")
        if (self.hole_mode is HoleMode.HOLE_DIAMETER) != (self.hole_diameter is not None):
            raise ValueError("a hole diameter is stated exactly in hole-diameter mode")
        if set(self.losses) != set(_LOSS_KEYS):
            raise ValueError(f"the ledger states exactly {list(_LOSS_KEYS)}")
        for key, setting in self.losses.items():
            if setting.mode is LossMode.LINE_DIAMETER and key != "dynamic_head":
                raise ValueError("only the dynamic head is computed from a line diameter")

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch.value,
            "pressure_drop_Pa": self.pressure_drop,
            "discharge_coefficient": self.discharge_coefficient,
            "density_source": self.density_source.value,
            "density_kg_m3": self.density,
            "density_pressure_Pa": self.density_pressure,
            "hole_mode": self.hole_mode.value,
            "hole_count": self.hole_count,
            "hole_diameter_m": self.hole_diameter,
            "losses": {key: self.losses[key].to_dict() for key in _LOSS_KEYS},
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BranchDefinition":
        def optional(key: str) -> float | None:
            value = payload.get(key)
            return None if value is None else float(value)

        count = payload.get("hole_count")
        if count is not None and (isinstance(count, bool) or int(count) != count):
            raise ValueError("a hole count is a whole number")
        return cls(
            branch=Branch(payload["branch"]),
            pressure_drop=float(payload["pressure_drop_Pa"]),
            discharge_coefficient=float(payload["discharge_coefficient"]),
            density_source=DensitySource(payload["density_source"]),
            density=optional("density_kg_m3"),
            density_pressure=optional("density_pressure_Pa"),
            hole_mode=HoleMode(payload["hole_mode"]),
            hole_count=None if count is None else int(count),
            hole_diameter=optional("hole_diameter_m"),
            losses={str(k): LossSetting.from_dict(v)
                    for k, v in dict(payload["losses"]).items()},
        )


@dataclass(frozen=True, slots=True)
class InjectorDefinition:
    """Everything an injector study is, before it is computed."""

    basis: FlowBasis
    oxidiser: BranchDefinition
    fuel: BranchDefinition

    def __post_init__(self) -> None:
        if self.oxidiser.branch is not Branch.OXIDISER or self.fuel.branch is not Branch.FUEL:
            raise ValueError("the oxidiser and fuel branches are each in their own place")

    def branch(self, branch: Branch) -> BranchDefinition:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {"flow_basis": self.basis.to_dict(), "oxidiser": self.oxidiser.to_dict(),
                "fuel": self.fuel.to_dict()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InjectorDefinition":
        return cls(basis=FlowBasis.from_dict(payload["flow_basis"]),
                   oxidiser=BranchDefinition.from_dict(payload["oxidiser"]),
                   fuel=BranchDefinition.from_dict(payload["fuel"]))

    @property
    def fingerprint(self) -> str:
        return _fingerprint(self.to_dict())


# ---------------------------------------------------------------------------
# the result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LedgerLine:
    """One pressure term as computed. ``status`` is "resolved",
    "not_applicable" or "unresolved"; ``value`` (Pa) only when resolved."""

    key: str
    label: str
    status: str
    value: float | None
    source: str
    reason: str

    def __post_init__(self) -> None:
        if self.status not in ("resolved", "not_applicable", "unresolved"):
            raise ValueError(f"unknown term status {self.status!r}")
        if (self.value is not None) != (self.status == "resolved"):
            raise ValueError(f"{self.key}: a value exists exactly when the term is resolved")
        if self.value is not None and not (math.isfinite(self.value) and self.value >= 0.0):
            raise ValueError(f"{self.key}: a resolved term is finite and at or above zero")

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "label": self.label, "status": self.status,
                "value_Pa": self.value, "source": self.source, "reason": self.reason}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LedgerLine":
        value = payload.get("value_Pa")
        return cls(key=str(payload["key"]), label=str(payload["label"]),
                   status=str(payload["status"]), value=None if value is None else float(value),
                   source=str(payload.get("source", "")), reason=str(payload.get("reason", "")))


@dataclass(frozen=True, slots=True)
class BranchResult:
    """One branch, computed or refused.

    ``quantities`` are SI; ``unresolved`` maps each quantity without a value to
    why. ``ledger`` is the pressure budget, in order. ``density_provenance``
    says where the density came from.
    """

    branch: Branch
    status: InjectorStatus
    quantities: Mapping[str, float] = field(default_factory=dict)
    unresolved: Mapping[str, str] = field(default_factory=dict)
    ledger: tuple[LedgerLine, ...] = ()
    density_provenance: Mapping[str, str] = field(default_factory=dict)
    message: str = ""
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        unknown = (set(self.quantities) | set(self.unresolved)) - _BRANCH_KEYS
        if unknown:
            raise ValueError(f"unknown branch quantities {sorted(unknown)}")
        if set(self.quantities) & set(self.unresolved):
            raise ValueError("a quantity is both valued and unresolved")
        if self.status is InjectorStatus.REFUSED and (self.quantities or self.ledger):
            raise ValueError("a refused branch carries no quantities and no ledger")
        for key, value in self.quantities.items():
            if not math.isfinite(value):
                raise ValueError(f"{key} must be finite")

    @property
    def ok(self) -> bool:
        return self.status is not InjectorStatus.REFUSED

    def value(self, key: str) -> float | None:
        return self.quantities.get(key)

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch.value, "status": self.status.value,
            "quantities": dict(self.quantities), "unresolved": dict(self.unresolved),
            "ledger": [line.to_dict() for line in self.ledger],
            "density_provenance": dict(self.density_provenance),
            "message": self.message, "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BranchResult":
        return cls(
            branch=Branch(payload["branch"]), status=InjectorStatus(payload["status"]),
            quantities={str(k): float(v) for k, v in dict(payload["quantities"]).items()},
            unresolved={str(k): str(v) for k, v in dict(payload["unresolved"]).items()},
            ledger=tuple(LedgerLine.from_dict(line) for line in payload.get("ledger", ())),
            density_provenance={str(k): str(v) for k, v in
                                dict(payload.get("density_provenance", {})).items()},
            message=str(payload.get("message", "")),
            notes=tuple(str(n) for n in payload.get("notes", ())),
        )


@dataclass(frozen=True, slots=True)
class InjectorResult:
    """Both branches and the pair's closures, or why not."""

    definition: InjectorDefinition
    status: InjectorStatus
    oxidiser: BranchResult
    fuel: BranchResult
    pair: Mapping[str, float] = field(default_factory=dict)
    pair_unresolved: Mapping[str, str] = field(default_factory=dict)
    message: str = ""
    assumptions: tuple[str, ...] = ()
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.oxidiser.branch is not Branch.OXIDISER or self.fuel.branch is not Branch.FUEL:
            raise ValueError("the oxidiser and fuel results are each in their own place")
        unknown = (set(self.pair) | set(self.pair_unresolved)) - _PAIR_KEYS
        if unknown:
            raise ValueError(f"unknown pair quantities {sorted(unknown)}")
        refused = not (self.oxidiser.ok and self.fuel.ok)
        if refused != (self.status is InjectorStatus.REFUSED):
            raise ValueError("the study is refused exactly when a branch is")
        if refused and self.pair:
            raise ValueError("a refused study carries no pair closure")

    @property
    def ok(self) -> bool:
        return self.status is not InjectorStatus.REFUSED

    def branch(self, branch: Branch) -> BranchResult:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": INJECTOR_SCHEMA,
            "version": INJECTOR_SCHEMA_VERSION,
            "definition": self.definition.to_dict(),
            "definition_fingerprint": self.definition.fingerprint,
            "status": self.status.value,
            "oxidiser": self.oxidiser.to_dict(),
            "fuel": self.fuel.to_dict(),
            "pair": dict(self.pair),
            "pair_unresolved": dict(self.pair_unresolved),
            "message": self.message,
            "assumptions": list(self.assumptions),
            "provenance": dict(self.provenance),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False,
                          allow_nan=False) + "\n"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InjectorResult":
        if not isinstance(payload, Mapping):
            raise RequirementFormatError("an injector record must be a mapping")
        if payload.get("schema") != INJECTOR_SCHEMA:
            raise RequirementFormatError(
                f"not an injector record (schema {payload.get('schema')!r})")
        if payload.get("version") != INJECTOR_SCHEMA_VERSION:
            raise RequirementFormatError(
                f"injector record version {payload.get('version')!r} is not supported")
        try:
            result = cls(
                definition=InjectorDefinition.from_dict(payload["definition"]),
                status=InjectorStatus(payload["status"]),
                oxidiser=BranchResult.from_dict(payload["oxidiser"]),
                fuel=BranchResult.from_dict(payload["fuel"]),
                pair={str(k): float(v) for k, v in dict(payload.get("pair", {})).items()},
                pair_unresolved={str(k): str(v) for k, v in
                                 dict(payload.get("pair_unresolved", {})).items()},
                message=str(payload.get("message", "")),
                assumptions=tuple(str(a) for a in payload.get("assumptions", ())),
                provenance={str(k): str(v) for k, v in
                            dict(payload.get("provenance", {})).items()},
            )
        except KeyError as missing:
            raise RequirementFormatError(f"injector record lacks {missing}") from None
        except (TypeError, ValueError) as error:
            if isinstance(error, RequirementFormatError):
                raise
            raise RequirementFormatError(str(error)) from None
        if payload.get("definition_fingerprint") != result.definition.fingerprint:
            raise RequirementFormatError(
                "the record's definition does not match its fingerprint")
        return result

    @classmethod
    def from_json(cls, text: str) -> "InjectorResult":
        try:
            payload = json.loads(text)
        except (TypeError, ValueError) as error:
            raise RequirementFormatError(f"not valid JSON: {error}") from None
        return cls.from_dict(payload)
