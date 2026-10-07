"""Thrust-chamber and nozzle sizing at one selected operating point.

LIQ-4. A sizing takes the candidate the user selected in a LIQ-3 propellant
trade -- its pair, O/F, chamber pressure, reactant temperatures and gamma basis,
copied verbatim -- plus the requirement's target thrust and design ambient, and
one explicit nozzle design input, the area ratio. It answers with the ideal
design point: propellant flow, throat and exit size, and the performance and
exit state those follow from. This module is the data; the evaluation lives in
the application layer, which alone can reach the chemistry provider.

Rules that shape it:

* **Ownership is kept.** LIQ-1 owns the chemistry, LIQ-2 the requirement and
  LIQ-3 the resolved operating point. :class:`OperatingPoint` is a copy of the
  selected LIQ-3 candidate and the trade it came from, including the numbers
  LIQ-3 recorded, so a sizing can prove it reproduced them. Nothing here
  re-decides a pair, an O/F or a chamber pressure.
* **The nozzle design input is stated.** The ideal model takes an area ratio.
  It is either the one the LIQ-3 trade was evaluated at or one the user states
  for the sizing, and :class:`AreaRatioSource` records which. No optimum
  expansion is assumed.
* **A refusal is a result.** A sizing the ideal model refuses (an internal
  shock at the design ambient, a nozzle with no net thrust there) keeps its
  definition and says why; it never carries a patched number.
* **Ideal.** No efficiency factor, divergence or other loss is applied. Chamber
  geometry, injectors, feed, cooling and cycle are not part of a sizing.

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
    "SIZING_QUANTITIES",
    "SIZING_SCHEMA",
    "SIZING_SCHEMA_VERSION",
    "AreaRatioSource",
    "OperatingPoint",
    "SizingDefinition",
    "SizingQuantity",
    "SizingResult",
    "SizingStatus",
    "quantity_named",
]

SIZING_SCHEMA: Final = "rocketforge.liquid-thrust-chamber-sizing"
SIZING_SCHEMA_VERSION: Final = 1


class AreaRatioSource(StrEnum):
    TRADE = "trade"                  # the Ae/At the selected LIQ-3 trade was evaluated at
    SIZING = "sizing"                # stated by the user for this sizing


class SizingStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"              # sized; the chain reported caveats
    REFUSED = "refused"              # the chamber, the check or the nozzle refused


@dataclass(frozen=True, slots=True)
class SizingQuantity:
    """One reported quantity, in SI. ``group`` is where it is shown."""

    key: str
    label: str
    unit: str
    group: str                       # "flow" | "geometry" | "performance" | "exit" | "thrust"
    note: str = ""


#: Everything a sizing reports, in display order. Each comes from the accepted
#: ideal-performance path (``solve_ideal_performance``) or is its definition
#: applied: ``mdot = F / c_eff``, the O/F split, and a circle's diameter.
SIZING_QUANTITIES: tuple[SizingQuantity, ...] = (
    SizingQuantity("mass_flow", "Propellant mass flow", "kg/s", "flow",
                   "Target thrust / c_eff at the design ambient"),
    SizingQuantity("oxidiser_mass_flow", "Oxidiser mass flow", "kg/s", "flow",
                   "mdot r / (1 + r)"),
    SizingQuantity("fuel_mass_flow", "Fuel mass flow", "kg/s", "flow", "mdot / (1 + r)"),
    SizingQuantity("throat_area", "Throat area At", "m²", "geometry",
                   "At = mdot c* / pc, from the ideal performance model"),
    SizingQuantity("throat_diameter", "Throat diameter Dt", "m", "geometry",
                   "Circular section: sqrt(4 At / pi)"),
    SizingQuantity("exit_area", "Exit area Ae", "m²", "geometry", "Ae = At · Ae/At"),
    SizingQuantity("exit_diameter", "Exit diameter De", "m", "geometry",
                   "Circular section: sqrt(4 Ae / pi)"),
    SizingQuantity("area_ratio", "Expansion ratio Ae/At", "", "geometry",
                   "The stated nozzle design input"),
    SizingQuantity("characteristic_velocity", "c*", "m/s", "performance",
                   "Chamber and throat quantity; independent of Ae/At and ambient"),
    SizingQuantity("thrust_coefficient", "Cf", "", "performance",
                   "At the design ambient: momentum + signed pressure term"),
    SizingQuantity("thrust_coefficient_momentum", "Cf, momentum term", "", "performance",
                   "Ve / c*"),
    SizingQuantity("thrust_coefficient_pressure", "Cf, pressure term", "", "performance",
                   "((pe - pa) / pc) Ae/At. Signed: negative when overexpanded"),
    SizingQuantity("effective_exhaust_velocity", "c_eff", "m/s", "performance",
                   "Cf c* = F / mdot at the design ambient"),
    SizingQuantity("specific_impulse", "Isp", "s", "performance",
                   "c_eff / g0 at the design ambient"),
    SizingQuantity("exit_mach", "Exit Mach number", "", "exit",
                   "Shock-free supersonic branch at Ae/At"),
    SizingQuantity("exit_pressure", "Exit pressure", "Pa", "exit", "Static, at the exit plane"),
    SizingQuantity("exit_pressure_ratio", "Exit pressure ratio pe/pc", "", "exit", ""),
    SizingQuantity("exit_temperature", "Exit temperature", "K", "exit",
                   "Static, frozen single-gamma expansion"),
    SizingQuantity("exit_velocity", "Exit velocity Ve", "m/s", "exit",
                   "Not the effective exhaust velocity"),
    SizingQuantity("momentum_thrust", "Momentum thrust", "N", "thrust", "mdot Ve"),
    SizingQuantity("pressure_thrust", "Pressure thrust", "N", "thrust",
                   "(pe - pa) Ae. Signed, not clamped"),
    SizingQuantity("thrust", "Calculated thrust", "N", "thrust",
                   "Momentum + pressure thrust of the sized engine"),
    SizingQuantity("thrust_closure", "Thrust closure", "", "thrust",
                   "Calculated thrust / target thrust - 1"),
)

_QUANTITY_KEYS = frozenset(q.key for q in SIZING_QUANTITIES)


def quantity_named(key: str) -> SizingQuantity | None:
    for quantity in SIZING_QUANTITIES:
        if quantity.key == key:
            return quantity
    return None


# ---------------------------------------------------------------------------
# the operating point, as LIQ-3 resolved it
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OperatingPoint:
    """The selected LIQ-3 candidate, copied, with the trade it came from.

    Attributes:
        trade_fingerprint: The LIQ-3 definition fingerprint. Identifies the
            question the candidate answered.
        trade_provenance: The chain LIQ-3 reported (CEA version, models).
        requirement_fingerprint: The LIQ-2 requirement snapshot the trade held.
        pair_key / pair_label / oxidiser / fuel: The LIQ-1 preset and its
            reactant keys, as evaluated.
        oxidiser_fuel_ratio / mixture_ratio_source: O/F by mass and where LIQ-3
            took it from.
        chamber_pressure / pressure_source: Pa, and where LIQ-3 took it from.
        oxidiser_temperature / fuel_temperature: K, as LIQ-3 evaluated them.
        gamma_basis: "frozen" or "equilibrium", the single-gamma reduction LIQ-3
            used for c* and the nozzle.
        ambient_pressure: The requirement's design ambient, Pa. Zero is vacuum.
        thrust: The requirement's target thrust, N.
        trade_area_ratio: The Ae/At LIQ-3 evaluated at, or ``None`` for a
            chamber-only trade.
        recorded: The candidate's LIQ-3 metrics, SI, as recorded.
    """

    trade_fingerprint: str
    trade_provenance: Mapping[str, str]
    requirement_fingerprint: str
    pair_key: str
    pair_label: str
    oxidiser: str
    fuel: str
    oxidiser_fuel_ratio: float
    mixture_ratio_source: str
    chamber_pressure: float
    pressure_source: str
    oxidiser_temperature: float
    fuel_temperature: float
    gamma_basis: str
    ambient_pressure: float
    thrust: float
    trade_area_ratio: float | None
    recorded: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("oxidiser_fuel_ratio", "chamber_pressure", "oxidiser_temperature",
                     "fuel_temperature", "thrust"):
            value = getattr(self, name)
            if not (math.isfinite(value) and value > 0.0):
                raise ValueError(f"{name} must be finite and positive")
        if not (math.isfinite(self.ambient_pressure) and self.ambient_pressure >= 0.0):
            raise ValueError("the design ambient pressure must be finite and at or above zero")
        if self.ambient_pressure >= self.chamber_pressure:
            raise ValueError("the chamber pressure must be above the design ambient pressure")
        if self.gamma_basis not in ("frozen", "equilibrium"):
            raise ValueError(f"unknown gamma basis {self.gamma_basis!r}")
        if self.trade_area_ratio is not None and not (
                math.isfinite(self.trade_area_ratio) and self.trade_area_ratio > 1.0):
            raise ValueError("a trade area ratio must be finite and above 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_fingerprint": self.trade_fingerprint,
            "trade_provenance": dict(self.trade_provenance),
            "requirement_fingerprint": self.requirement_fingerprint,
            "pair_key": self.pair_key, "pair_label": self.pair_label,
            "oxidiser": self.oxidiser, "fuel": self.fuel,
            "oxidiser_fuel_ratio": self.oxidiser_fuel_ratio,
            "mixture_ratio_source": self.mixture_ratio_source,
            "chamber_pressure_Pa": self.chamber_pressure,
            "pressure_source": self.pressure_source,
            "oxidiser_temperature_K": self.oxidiser_temperature,
            "fuel_temperature_K": self.fuel_temperature,
            "gamma_basis": self.gamma_basis,
            "ambient_pressure_Pa": self.ambient_pressure,
            "thrust_N": self.thrust,
            "trade_area_ratio": self.trade_area_ratio,
            "recorded": dict(self.recorded),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "OperatingPoint":
        ratio = payload.get("trade_area_ratio")
        return cls(
            trade_fingerprint=str(payload["trade_fingerprint"]),
            trade_provenance={str(k): str(v) for k, v in
                              dict(payload.get("trade_provenance", {})).items()},
            requirement_fingerprint=str(payload["requirement_fingerprint"]),
            pair_key=str(payload["pair_key"]), pair_label=str(payload["pair_label"]),
            oxidiser=str(payload["oxidiser"]), fuel=str(payload["fuel"]),
            oxidiser_fuel_ratio=float(payload["oxidiser_fuel_ratio"]),
            mixture_ratio_source=str(payload["mixture_ratio_source"]),
            chamber_pressure=float(payload["chamber_pressure_Pa"]),
            pressure_source=str(payload["pressure_source"]),
            oxidiser_temperature=float(payload["oxidiser_temperature_K"]),
            fuel_temperature=float(payload["fuel_temperature_K"]),
            gamma_basis=str(payload["gamma_basis"]),
            ambient_pressure=float(payload["ambient_pressure_Pa"]),
            thrust=float(payload["thrust_N"]),
            trade_area_ratio=None if ratio is None else float(ratio),
            recorded={str(k): float(v) for k, v in dict(payload.get("recorded", {})).items()},
        )


# ---------------------------------------------------------------------------
# the definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SizingDefinition:
    """Everything a sizing is, before it runs. Fully resolved by construction."""

    point: OperatingPoint
    area_ratio: float
    area_ratio_source: AreaRatioSource

    def __post_init__(self) -> None:
        if not (math.isfinite(self.area_ratio) and self.area_ratio > 1.0):
            raise ValueError("the area ratio must be finite and above 1")
        if (self.area_ratio_source is AreaRatioSource.TRADE
                and self.area_ratio != self.point.trade_area_ratio):
            raise ValueError("a trade area ratio must be the one the trade was evaluated at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "operating_point": self.point.to_dict(),
            "area_ratio": self.area_ratio,
            "area_ratio_source": self.area_ratio_source.value,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SizingDefinition":
        return cls(point=OperatingPoint.from_dict(payload["operating_point"]),
                   area_ratio=float(payload["area_ratio"]),
                   area_ratio_source=AreaRatioSource(payload["area_ratio_source"]))

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# the result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SizingResult:
    """A completed sizing, or its explicit refusal.

    Attributes:
        definition: What was asked.
        status: OK, WARNING or REFUSED.
        quantities: Every quantity of :data:`SIZING_QUANTITIES` with a value, SI.
        unresolved: Every quantity without one, mapped to the reason.
        regime: The nozzle regime the ideal model classified at the design
            ambient ("overexpanded", "ideally_expanded", "underexpanded"), or
            empty when it gave none.
        message: For a refusal, what refused and why.
        notes: Caveats and information the chain reported, as text.
        assumptions: The model's stated assumptions, attached to the numbers.
        provenance: Which chain produced the numbers.
    """

    definition: SizingDefinition
    status: SizingStatus
    quantities: Mapping[str, float] = field(default_factory=dict)
    unresolved: Mapping[str, str] = field(default_factory=dict)
    regime: str = ""
    message: str = ""
    notes: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = (set(self.quantities) | set(self.unresolved)) - _QUANTITY_KEYS
        if unknown:
            raise ValueError(f"unknown sizing quantities {sorted(unknown)}")
        overlap = set(self.quantities) & set(self.unresolved)
        if overlap:
            raise ValueError(f"quantities both valued and unresolved: {sorted(overlap)}")
        if self.status is SizingStatus.REFUSED and self.quantities:
            raise ValueError("a refused sizing carries no quantities")

    @property
    def ok(self) -> bool:
        return self.status is not SizingStatus.REFUSED

    def value(self, key: str) -> float | None:
        return self.quantities.get(key)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SIZING_SCHEMA,
            "version": SIZING_SCHEMA_VERSION,
            "definition": self.definition.to_dict(),
            "definition_fingerprint": self.definition.fingerprint,
            "status": self.status.value,
            "quantities": dict(self.quantities),
            "unresolved": dict(self.unresolved),
            "regime": self.regime,
            "message": self.message,
            "notes": list(self.notes),
            "assumptions": list(self.assumptions),
            "provenance": dict(self.provenance),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False,
                          allow_nan=False) + "\n"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SizingResult":
        if payload.get("schema") != SIZING_SCHEMA:
            raise RequirementFormatError(
                f"not a thrust-chamber sizing (schema {payload.get('schema')!r})")
        if payload.get("version") != SIZING_SCHEMA_VERSION:
            raise RequirementFormatError(
                f"sizing version {payload.get('version')!r} is not supported")
        try:
            return cls(
                definition=SizingDefinition.from_dict(payload["definition"]),
                status=SizingStatus(payload["status"]),
                quantities={str(k): float(v) for k, v in dict(payload["quantities"]).items()},
                unresolved={str(k): str(v) for k, v in dict(payload["unresolved"]).items()},
                regime=str(payload.get("regime", "")),
                message=str(payload.get("message", "")),
                notes=tuple(str(n) for n in payload.get("notes", ())),
                assumptions=tuple(str(a) for a in payload.get("assumptions", ())),
                provenance={str(k): str(v) for k, v in
                            dict(payload.get("provenance", {})).items()},
            )
        except KeyError as missing:
            raise RequirementFormatError(f"sizing record lacks {missing}") from None
        except (TypeError, ValueError) as error:
            if isinstance(error, RequirementFormatError):
                raise
            raise RequirementFormatError(str(error)) from None

    @classmethod
    def from_json(cls, text: str) -> "SizingResult":
        try:
            payload = json.loads(text)
        except (TypeError, ValueError) as error:
            raise RequirementFormatError(f"not valid JSON: {error}") from None
        if not isinstance(payload, Mapping):
            raise RequirementFormatError("a sizing record must be a mapping")
        return cls.from_dict(payload)
