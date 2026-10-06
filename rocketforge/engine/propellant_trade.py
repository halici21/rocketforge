"""The liquid propellant trade: how candidate pairs compare for one requirement.

LIQ-3. A trade takes one LIQ-2 :class:`EngineRequirement` and a set of LIQ-1
propellant candidates, evaluates each at one **stated** operating point, and
records what came back. This module is the data: the definition (what was
asked, and where each operating assumption came from) and the result (what
each candidate gave, or why it gave nothing). The evaluation lives in the
application layer, which alone can reach the chemistry provider; this layer
only holds numbers and names.

Rules that shape it:

* **Every operating assumption carries its source.** A chamber pressure or an
  O/F is either the requirement's own value or one the user stated for this
  study. Nothing is filled in: an Auto chamber pressure, an upper limit or an
  Auto O/F leaves the definition unresolved until the user states a value.
* **The performance basis is explicit.** Ideal-performance quantities need a
  nozzle, and the requirement does not define one. Either the trade is
  chamber-only, and every quantity that needs a nozzle is reported as
  unresolved with that reason, or the user states the area ratio and gamma
  basis the comparison is made at, and the result carries them.
* **No score.** A result lists metrics. Ordering by one of them is a view; the
  data model has no ranking, no weighting and no "best".
* **A failed candidate is a row, not a hole.** It keeps its operating point and
  says what failed; the other candidates are untouched.

SI units throughout. Molar mass is kg/mol, as ``ChamberGas`` holds it.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Final

from .requirement import EngineRequirement, RequirementFormatError

__all__ = [
    "TRADE_SCHEMA",
    "TRADE_SCHEMA_VERSION",
    "CandidateResult",
    "CandidateStatus",
    "MixtureRatioSource",
    "PerformanceBasis",
    "PressureSource",
    "TRADE_METRICS",
    "TradeDefinition",
    "TradeMetric",
    "TradeResult",
    "metric_named",
]

TRADE_SCHEMA: Final = "rocketforge.liquid-propellant-trade"
TRADE_SCHEMA_VERSION: Final = 1


class PressureSource(StrEnum):
    REQUIREMENT = "requirement"      # the requirement's chamber-pressure target
    STUDY = "study"                  # stated for this study by the user


class MixtureRatioSource(StrEnum):
    REQUIREMENT = "requirement"      # the requirement's explicit O/F, every candidate
    CATALOGUE = "catalogue"          # each candidate's own LIQ-1 catalogue O/F
    STUDY = "study"                  # one O/F stated for this study, every candidate


class PerformanceBasis(StrEnum):
    CHAMBER_ONLY = "chamber_only"            # no nozzle stated: chamber metrics only
    IDEAL_AREA_RATIO = "ideal_area_ratio"    # ideal expansion through a stated Ae/At


class CandidateStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"              # solved; the chain reported caveats
    FAILED = "failed"                # the chamber or the performance step refused


@dataclass(frozen=True, slots=True)
class TradeMetric:
    """One reported quantity. ``tier`` says what it needs to exist."""

    key: str
    label: str
    unit: str
    tier: str                        # "chamber" | "performance" | "flow"
    note: str = ""


#: Everything a trade reports, in display order. Each is a quantity the
#: production chain already computes (or, for the flow tier, its definition
#: ``mdot = F / c_eff`` applied to the requirement's thrust).
TRADE_METRICS: tuple[TradeMetric, ...] = (
    TradeMetric("chamber_temperature", "Chamber temperature", "K", "chamber",
                "HP equilibrium, from the provider"),
    TradeMetric("molar_mass", "Molar mass", "kg/mol", "chamber",
                "Mean molar mass of the chamber products"),
    TradeMetric("gamma_frozen", "Gamma, frozen", "", "chamber", "cp/cv at the chamber"),
    TradeMetric("gamma_equilibrium", "Gamma, equilibrium", "", "chamber",
                "Isentropic exponent of the shifting-equilibrium state"),
    TradeMetric("characteristic_velocity", "c*", "m/s", "chamber",
                "Ideal c* of the reduced single-gamma gas, at the stated gamma basis"),
    TradeMetric("thrust_coefficient", "Cf", "", "performance",
                "Ideal, at the stated area ratio and the design ambient pressure"),
    TradeMetric("effective_exhaust_velocity", "c_eff", "m/s", "performance",
                "F / mdot at the design ambient pressure"),
    TradeMetric("specific_impulse", "Isp", "s", "performance",
                "c_eff / g0 at the design ambient pressure"),
    TradeMetric("exit_pressure", "Exit pressure", "Pa", "performance",
                "Ideal nozzle exit pressure at the stated area ratio"),
    TradeMetric("mass_flow", "Propellant mass flow", "kg/s", "flow",
                "Target thrust / c_eff"),
    TradeMetric("oxidiser_mass_flow", "Oxidiser mass flow", "kg/s", "flow",
                "mdot r / (1 + r)"),
    TradeMetric("fuel_mass_flow", "Fuel mass flow", "kg/s", "flow", "mdot / (1 + r)"),
    TradeMetric("propellant_mass", "Propellant consumed", "kg", "flow",
                "mdot × burn time; steady operation, no start or shutdown transients"),
)

_METRIC_KEYS = frozenset(metric.key for metric in TRADE_METRICS)


def metric_named(key: str) -> TradeMetric | None:
    for metric in TRADE_METRICS:
        if metric.key == key:
            return metric
    return None


# ---------------------------------------------------------------------------
# the definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TradeDefinition:
    """Everything a trade is, before it runs. Fully resolved by construction.

    Built by the application layer from a complete requirement and the user's
    study settings; a definition never holds an unresolved value. Candidate
    keys are LIQ-1 preset keys, in catalogue order.

    Attributes:
        requirement: The requirement snapshot. The trade does not follow later
            edits; a result says which requirement it answered.
        candidates: Preset keys evaluated.
        chamber_pressure / pressure_source: The operating chamber pressure, Pa,
            and whether the requirement or the study stated it.
        mixture_ratio_source / mixture_ratio: How O/F is set. ``mixture_ratio``
            is the one O/F every candidate uses, or ``None`` for ``CATALOGUE``.
        performance_basis / area_ratio / gamma_basis: The nozzle the ideal
            comparison is made at. ``area_ratio`` is ``None`` for chamber-only.
            ``gamma_basis`` ("frozen" or "equilibrium") reduces the chamber gas
            for c* -- and for the nozzle, when there is one.
    """

    requirement: EngineRequirement
    candidates: tuple[str, ...]
    chamber_pressure: float
    pressure_source: PressureSource
    mixture_ratio_source: MixtureRatioSource
    mixture_ratio: float | None
    performance_basis: PerformanceBasis
    area_ratio: float | None
    gamma_basis: str

    def __post_init__(self) -> None:
        if not self.candidates:
            raise ValueError("a trade needs at least one candidate")
        if not (math.isfinite(self.chamber_pressure) and self.chamber_pressure > 0.0):
            raise ValueError("the operating chamber pressure must be finite and positive")
        catalogue = self.mixture_ratio_source is MixtureRatioSource.CATALOGUE
        if catalogue != (self.mixture_ratio is None):
            raise ValueError("a catalogue O/F carries no number; any other source needs one")
        if self.mixture_ratio is not None and not (
                math.isfinite(self.mixture_ratio) and self.mixture_ratio > 0.0):
            raise ValueError("the O/F must be finite and positive")
        nozzle = self.performance_basis is PerformanceBasis.IDEAL_AREA_RATIO
        if nozzle != (self.area_ratio is not None):
            raise ValueError("an ideal basis needs an area ratio; chamber-only has none")
        if self.area_ratio is not None and not (
                math.isfinite(self.area_ratio) and self.area_ratio > 1.0):
            raise ValueError("the area ratio must be finite and above 1")
        if self.gamma_basis not in ("frozen", "equilibrium"):
            raise ValueError(f"unknown gamma basis {self.gamma_basis!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement": self.requirement.to_dict(),
            "candidates": list(self.candidates),
            "chamber_pressure_Pa": self.chamber_pressure,
            "pressure_source": self.pressure_source.value,
            "mixture_ratio_source": self.mixture_ratio_source.value,
            "mixture_ratio": self.mixture_ratio,
            "performance_basis": self.performance_basis.value,
            "area_ratio": self.area_ratio,
            "gamma_basis": self.gamma_basis,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TradeDefinition":
        try:
            return cls(
                requirement=EngineRequirement.from_dict(payload["requirement"]),
                candidates=tuple(str(key) for key in payload["candidates"]),
                chamber_pressure=float(payload["chamber_pressure_Pa"]),
                pressure_source=PressureSource(payload["pressure_source"]),
                mixture_ratio_source=MixtureRatioSource(payload["mixture_ratio_source"]),
                mixture_ratio=_optional(payload.get("mixture_ratio")),
                performance_basis=PerformanceBasis(payload["performance_basis"]),
                area_ratio=_optional(payload.get("area_ratio")),
                gamma_basis=str(payload["gamma_basis"]),
            )
        except KeyError as missing:
            raise RequirementFormatError(f"trade definition lacks {missing}") from None
        except (TypeError, ValueError) as error:
            if isinstance(error, RequirementFormatError):
                raise
            raise RequirementFormatError(str(error)) from None

    @property
    def fingerprint(self) -> str:
        record = self.to_dict()
        record["requirement"] = self.requirement.canonical()
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# the result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CandidateResult:
    """One candidate's answer, or its explicit failure.

    Attributes:
        key / label: The LIQ-1 preset.
        oxidiser / fuel: The preset's reactant keys, as evaluated.
        oxidiser_fuel_ratio / chamber_pressure: The operating point used.
        oxidiser_temperature / fuel_temperature: Stream temperatures, K -- each
            reactant's own reference temperature, exactly as the LIQ-1 preset
            sets them.
        status: OK, WARNING or FAILED.
        metrics: Every metric of :data:`TRADE_METRICS` with a value.
        unresolved: Every metric without one, mapped to the reason.
        message: For a failure, what failed and where.
        notes: Caveats the chain reported, as text.
    """

    key: str
    label: str
    oxidiser: str
    fuel: str
    oxidiser_fuel_ratio: float
    chamber_pressure: float
    oxidiser_temperature: float | None
    fuel_temperature: float | None
    status: CandidateStatus
    metrics: Mapping[str, float] = field(default_factory=dict)
    unresolved: Mapping[str, str] = field(default_factory=dict)
    message: str = ""
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        unknown = (set(self.metrics) | set(self.unresolved)) - _METRIC_KEYS
        if unknown:
            raise ValueError(f"unknown trade metrics {sorted(unknown)}")
        overlap = set(self.metrics) & set(self.unresolved)
        if overlap:
            raise ValueError(f"metrics both valued and unresolved: {sorted(overlap)}")

    @property
    def ok(self) -> bool:
        return self.status is not CandidateStatus.FAILED

    def value(self, key: str) -> float | None:
        return self.metrics.get(key)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key, "label": self.label,
            "oxidiser": self.oxidiser, "fuel": self.fuel,
            "oxidiser_fuel_ratio": self.oxidiser_fuel_ratio,
            "chamber_pressure_Pa": self.chamber_pressure,
            "oxidiser_temperature_K": self.oxidiser_temperature,
            "fuel_temperature_K": self.fuel_temperature,
            "status": self.status.value,
            "metrics": dict(self.metrics),
            "unresolved": dict(self.unresolved),
            "message": self.message,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CandidateResult":
        return cls(
            key=str(payload["key"]), label=str(payload["label"]),
            oxidiser=str(payload["oxidiser"]), fuel=str(payload["fuel"]),
            oxidiser_fuel_ratio=float(payload["oxidiser_fuel_ratio"]),
            chamber_pressure=float(payload["chamber_pressure_Pa"]),
            oxidiser_temperature=_optional(payload.get("oxidiser_temperature_K")),
            fuel_temperature=_optional(payload.get("fuel_temperature_K")),
            status=CandidateStatus(payload["status"]),
            metrics={str(k): float(v) for k, v in dict(payload["metrics"]).items()},
            unresolved={str(k): str(v) for k, v in dict(payload["unresolved"]).items()},
            message=str(payload.get("message", "")),
            notes=tuple(str(n) for n in payload.get("notes", ())),
        )


@dataclass(frozen=True, slots=True)
class TradeResult:
    """A completed trade: the definition, every candidate, and the provenance.

    ``selected`` is the candidate the user chose for the next design stage,
    or empty. Choosing is the user's act; nothing here sets it.
    """

    definition: TradeDefinition
    candidates: tuple[CandidateResult, ...]
    provenance: Mapping[str, str] = field(default_factory=dict)
    selected: str = ""

    def __post_init__(self) -> None:
        keys = tuple(candidate.key for candidate in self.candidates)
        if keys != self.definition.candidates:
            raise ValueError("a result must hold one row per defined candidate, in order")
        if self.selected and self.selected not in keys:
            raise ValueError(f"selected candidate {self.selected!r} is not in this trade")

    def candidate(self, key: str) -> CandidateResult | None:
        for candidate in self.candidates:
            if candidate.key == key:
                return candidate
        return None

    def with_selection(self, key: str) -> "TradeResult":
        """The same result with ``key`` chosen. A failed candidate cannot be."""
        if key:
            candidate = self.candidate(key)
            if candidate is None or not candidate.ok:
                raise ValueError(f"{key!r} is not a successful candidate of this trade")
        from dataclasses import replace

        return replace(self, selected=key)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": TRADE_SCHEMA,
            "version": TRADE_SCHEMA_VERSION,
            "definition": self.definition.to_dict(),
            "definition_fingerprint": self.definition.fingerprint,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "provenance": dict(self.provenance),
            "selected": self.selected,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False,
                          allow_nan=False) + "\n"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TradeResult":
        if payload.get("schema") != TRADE_SCHEMA:
            raise RequirementFormatError(
                f"not a propellant trade (schema {payload.get('schema')!r})")
        if payload.get("version") != TRADE_SCHEMA_VERSION:
            raise RequirementFormatError(
                f"trade version {payload.get('version')!r} is not supported")
        try:
            return cls(
                definition=TradeDefinition.from_dict(payload["definition"]),
                candidates=tuple(CandidateResult.from_dict(c)
                                 for c in payload["candidates"]),
                provenance={str(k): str(v) for k, v in
                            dict(payload.get("provenance", {})).items()},
                selected=str(payload.get("selected", "")),
            )
        except KeyError as missing:
            raise RequirementFormatError(f"trade record lacks {missing}") from None
        except (TypeError, ValueError) as error:
            if isinstance(error, RequirementFormatError):
                raise
            raise RequirementFormatError(str(error)) from None

    @classmethod
    def from_json(cls, text: str) -> "TradeResult":
        try:
            payload = json.loads(text)
        except (TypeError, ValueError) as error:
            raise RequirementFormatError(f"not valid JSON: {error}") from None
        if not isinstance(payload, Mapping):
            raise RequirementFormatError("a trade record must be a mapping")
        return cls.from_dict(payload)


def _optional(value: Any) -> float | None:
    return None if value is None else float(value)
