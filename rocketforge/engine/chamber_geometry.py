"""Combustion-chamber geometry at one accepted thrust-chamber sizing.

LIQ-5. A geometry takes the throat of a LIQ-4 sizing -- its area, diameter and
the sizing it came from, copied verbatim -- plus three stated design inputs:
the characteristic length L*, the contraction area ratio Ac/At and the
converging half-angle. It answers with the chamber that holds ``L* At`` from
the injector face to the throat: volume, diameter, the converging and
cylindrical lengths and volumes, and the injector-face-to-throat length. This
module is the data; the relations are in
:mod:`rocketforge.engineering.chamber_geometry`.

Rules that shape it:

* **Ownership is kept.** LIQ-4 owns the throat. :class:`ThroatBasis` is a copy
  of it and of the sizing's identity, so a geometry is traceable to the exact
  sizing and trade it extends. Nothing here re-sizes a throat.
* **The design inputs are stated.** L*, Ac/At and the angle have no default and
  no optimum. A value out of its domain is refused, not clamped.
* **A refusal is a result.** A converging section larger than the chamber
  volume keeps its definition and says why; it never carries a patched number.

SI units throughout. The half-angle is in radians, as is every angle below the
application layer (``01`` section 8); the page states it in degrees.
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
    "GEOMETRY_QUANTITIES",
    "GEOMETRY_SCHEMA",
    "GEOMETRY_SCHEMA_VERSION",
    "GeometryDefinition",
    "GeometryQuantity",
    "GeometryResult",
    "GeometryStatus",
    "ThroatBasis",
]

GEOMETRY_SCHEMA: Final = "rocketforge.liquid-chamber-geometry"
GEOMETRY_SCHEMA_VERSION: Final = 1


class GeometryStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"              # computed; an advisory applies
    REFUSED = "refused"              # the geometry does not exist for these inputs


@dataclass(frozen=True, slots=True)
class GeometryQuantity:
    """One reported quantity, in SI. ``group`` is where it is shown."""

    key: str
    label: str
    group: str                       # "inputs" | "chamber" | "converging" | "lengths" | "closure"
    note: str = ""


#: Everything a geometry reports, in display order.
GEOMETRY_QUANTITIES: tuple[GeometryQuantity, ...] = (
    GeometryQuantity("throat_area", "Throat area At", "inputs", "From the LIQ-4 sizing"),
    GeometryQuantity("throat_diameter", "Throat diameter Dt", "inputs", "From the LIQ-4 sizing"),
    GeometryQuantity("characteristic_length", "Characteristic length L*", "inputs",
                     "Stated. L* = Vc / At (Sutton Eq. 8-9)"),
    GeometryQuantity("contraction_ratio", "Contraction ratio Ac/At", "inputs", "Stated"),
    GeometryQuantity("converging_half_angle", "Converging half-angle", "inputs",
                     "Stated, from the axis"),
    GeometryQuantity("chamber_volume", "Chamber volume Vc", "chamber",
                     "L* · At, injector face to throat"),
    GeometryQuantity("chamber_area", "Chamber area Ac", "chamber", "Ac/At · At"),
    GeometryQuantity("chamber_diameter", "Chamber diameter Dc", "chamber",
                     "Circular section: sqrt(4 Ac / pi)"),
    GeometryQuantity("converging_length", "Converging length", "converging",
                     "(Rc - Rt) / tan(half-angle)"),
    GeometryQuantity("converging_volume", "Converging volume", "converging",
                     "Conical frustum: (pi/3) L (Rc² + Rc Rt + Rt²)"),
    GeometryQuantity("converging_volume_fraction", "Converging share of Vc", "converging",
                     "Converging volume / Vc"),
    GeometryQuantity("cylinder_length", "Cylindrical length", "lengths",
                     "(Vc - converging volume) / Ac"),
    GeometryQuantity("cylinder_volume", "Cylindrical volume", "lengths",
                     "Vc - converging volume"),
    GeometryQuantity("injector_to_throat_length", "Injector face to throat", "lengths",
                     "Cylindrical + converging length, axial"),
    GeometryQuantity("characteristic_length_closure", "L* closure", "closure",
                     "((Ac · cylindrical length + converging volume) / At) / L* - 1"),
    GeometryQuantity("contraction_closure", "Ac/At closure", "closure",
                     "(pi Rc²) / (Ac/At · At) - 1"),
)

_QUANTITY_KEYS = frozenset(q.key for q in GEOMETRY_QUANTITIES)


def _positive(value: float) -> bool:
    return math.isfinite(value) and value > 0.0


# ---------------------------------------------------------------------------
# the throat, as LIQ-4 sized it
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ThroatBasis:
    """The throat of an accepted LIQ-4 sizing, copied, with what it came from.

    Attributes:
        sizing_fingerprint: The LIQ-4 definition fingerprint.
        sizing_status: The LIQ-4 status ("ok" or "warning").
        sizing_provenance: The chain LIQ-4 reported.
        trade_fingerprint: The LIQ-3 trade the sizing extends.
        pair_key / pair_label: The propellant pair, as LIQ-3 selected it.
        chamber_pressure: Pa, as LIQ-3 resolved it.
        thrust: N, the LIQ-2 target the throat was sized for.
        area_ratio: The LIQ-4 nozzle Ae/At.
        throat_area: m^2, LIQ-4's At.
        throat_diameter: m, LIQ-4's Dt.
    """

    sizing_fingerprint: str
    sizing_status: str
    sizing_provenance: Mapping[str, str]
    trade_fingerprint: str
    pair_key: str
    pair_label: str
    chamber_pressure: float
    thrust: float
    area_ratio: float
    throat_area: float
    throat_diameter: float

    def __post_init__(self) -> None:
        for name in ("chamber_pressure", "thrust", "throat_area", "throat_diameter"):
            if not _positive(getattr(self, name)):
                raise ValueError(f"{name} must be finite and positive")
        if not (math.isfinite(self.area_ratio) and self.area_ratio > 1.0):
            raise ValueError("the nozzle area ratio must be finite and above 1")
        if self.sizing_status not in ("ok", "warning"):
            raise ValueError("a throat basis comes from an accepted sizing only")

    def to_dict(self) -> dict[str, Any]:
        return {
            "sizing_fingerprint": self.sizing_fingerprint,
            "sizing_status": self.sizing_status,
            "sizing_provenance": dict(self.sizing_provenance),
            "trade_fingerprint": self.trade_fingerprint,
            "pair_key": self.pair_key, "pair_label": self.pair_label,
            "chamber_pressure_Pa": self.chamber_pressure,
            "thrust_N": self.thrust,
            "area_ratio": self.area_ratio,
            "throat_area_m2": self.throat_area,
            "throat_diameter_m": self.throat_diameter,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ThroatBasis":
        return cls(
            sizing_fingerprint=str(payload["sizing_fingerprint"]),
            sizing_status=str(payload["sizing_status"]),
            sizing_provenance={str(k): str(v) for k, v in
                               dict(payload.get("sizing_provenance", {})).items()},
            trade_fingerprint=str(payload["trade_fingerprint"]),
            pair_key=str(payload["pair_key"]), pair_label=str(payload["pair_label"]),
            chamber_pressure=float(payload["chamber_pressure_Pa"]),
            thrust=float(payload["thrust_N"]),
            area_ratio=float(payload["area_ratio"]),
            throat_area=float(payload["throat_area_m2"]),
            throat_diameter=float(payload["throat_diameter_m"]),
        )


# ---------------------------------------------------------------------------
# the definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GeometryDefinition:
    """Everything a geometry is, before it is computed. Fully stated by construction.

    Domain checks belong to the relations; this only refuses a value that is
    not a number, so a record that reaches it is complete.
    """

    basis: ThroatBasis
    characteristic_length: float              # m
    contraction_ratio: float
    converging_half_angle: float              # rad, from the axis

    def __post_init__(self) -> None:
        for name in ("characteristic_length", "contraction_ratio",
                     "converging_half_angle"):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")

    def to_dict(self) -> dict[str, Any]:
        return {
            "throat_basis": self.basis.to_dict(),
            "characteristic_length_m": self.characteristic_length,
            "contraction_ratio": self.contraction_ratio,
            "converging_half_angle_rad": self.converging_half_angle,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GeometryDefinition":
        return cls(basis=ThroatBasis.from_dict(payload["throat_basis"]),
                   characteristic_length=float(payload["characteristic_length_m"]),
                   contraction_ratio=float(payload["contraction_ratio"]),
                   converging_half_angle=float(payload["converging_half_angle_rad"]))

    @property
    def fingerprint(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# the result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GeometryResult:
    """A computed chamber geometry, or its explicit refusal.

    ``quantities`` are SI; ``converging_half_angle`` is in radians.
    ``notes`` are the relations' advisories and information, as text.
    """

    definition: GeometryDefinition
    status: GeometryStatus
    quantities: Mapping[str, float] = field(default_factory=dict)
    unresolved: Mapping[str, str] = field(default_factory=dict)
    message: str = ""
    notes: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = (set(self.quantities) | set(self.unresolved)) - _QUANTITY_KEYS
        if unknown:
            raise ValueError(f"unknown geometry quantities {sorted(unknown)}")
        overlap = set(self.quantities) & set(self.unresolved)
        if overlap:
            raise ValueError(f"quantities both valued and unresolved: {sorted(overlap)}")
        if self.status is GeometryStatus.REFUSED and self.quantities:
            raise ValueError("a refused geometry carries no quantities")

    @property
    def ok(self) -> bool:
        return self.status is not GeometryStatus.REFUSED

    def value(self, key: str) -> float | None:
        return self.quantities.get(key)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": GEOMETRY_SCHEMA,
            "version": GEOMETRY_SCHEMA_VERSION,
            "definition": self.definition.to_dict(),
            "definition_fingerprint": self.definition.fingerprint,
            "status": self.status.value,
            "quantities": dict(self.quantities),
            "unresolved": dict(self.unresolved),
            "message": self.message,
            "notes": list(self.notes),
            "assumptions": list(self.assumptions),
            "provenance": dict(self.provenance),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False,
                          allow_nan=False) + "\n"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "GeometryResult":
        if payload.get("schema") != GEOMETRY_SCHEMA:
            raise RequirementFormatError(
                f"not a chamber geometry (schema {payload.get('schema')!r})")
        if payload.get("version") != GEOMETRY_SCHEMA_VERSION:
            raise RequirementFormatError(
                f"geometry version {payload.get('version')!r} is not supported")
        try:
            result = cls(
                definition=GeometryDefinition.from_dict(payload["definition"]),
                status=GeometryStatus(payload["status"]),
                quantities={str(k): float(v) for k, v in dict(payload["quantities"]).items()},
                unresolved={str(k): str(v) for k, v in dict(payload["unresolved"]).items()},
                message=str(payload.get("message", "")),
                notes=tuple(str(n) for n in payload.get("notes", ())),
                assumptions=tuple(str(a) for a in payload.get("assumptions", ())),
                provenance={str(k): str(v) for k, v in
                            dict(payload.get("provenance", {})).items()},
            )
        except KeyError as missing:
            raise RequirementFormatError(f"geometry record lacks {missing}") from None
        except (TypeError, ValueError) as error:
            if isinstance(error, RequirementFormatError):
                raise
            raise RequirementFormatError(str(error)) from None
        recorded = payload.get("definition_fingerprint")
        if recorded is not None and recorded != result.definition.fingerprint:
            raise RequirementFormatError(
                "the record's definition does not match its fingerprint")
        return result

    @classmethod
    def from_json(cls, text: str) -> "GeometryResult":
        try:
            payload = json.loads(text)
        except (TypeError, ValueError) as error:
            raise RequirementFormatError(f"not valid JSON: {error}") from None
        if not isinstance(payload, Mapping):
            raise RequirementFormatError("a geometry record must be a mapping")
        return cls.from_dict(payload)
