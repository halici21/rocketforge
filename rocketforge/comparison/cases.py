"""Reference cases: what an external source says, and what it may be used for.

A reference is only as useful as what it is allowed to prove, and that depends
on where it came from. So the kind of source is part of the data, and it
decides what a comparison may conclude:

* :attr:`SourceKind.CEA_DIRECT` -- the same code RocketForge wraps, run
  directly. Agreement is expected to a stated tolerance (usually exactly), and
  a verdict is meaningful: a difference is a RocketForge defect.
* :attr:`SourceKind.NASA_PUBLISHED` -- a NASA-published or NASA-shipped
  printout. Agreement is expected within the printed precision, and a verdict
  is meaningful at that precision.
* :attr:`SourceKind.INDEPENDENT_CODE` -- another program (PROPEP, EXPLO5, ...).
  Different thermodynamic data and different models. Differences are reported
  and **no verdict is drawn**: neither side is ground truth, and nothing here
  ranks one code above another.
* :attr:`SourceKind.EXPERIMENT` -- a measurement. Reserved for future work;
  differences only, with the measurement's own uncertainty carried alongside.

Separately, :attr:`ReferenceCase.benchmark_class` records *what* a case
validates: ``"A"`` for a solid-propellant end-to-end benchmark, ``"B"`` for a
mechanism check that is not itself a solid propellant.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any

from rocketforge.core.errors import InputError

from .units import to_canonical

__all__ = [
    "SourceKind",
    "ReferenceQuantity",
    "ReferenceCase",
    "ReferenceCaseError",
    "VERDICT_KINDS",
    "REQUIRED_CASE_FIELDS",
    "case_from_mapping",
]


class ReferenceCaseError(InputError):
    """A reference case is incomplete or self-contradictory."""


class SourceKind(Enum):
    CEA_DIRECT = "cea_direct"
    NASA_PUBLISHED = "nasa_published"
    INDEPENDENT_CODE = "independent_code"
    EXPERIMENT = "experiment"


#: The only kinds a pass/fail verdict may be drawn against.
VERDICT_KINDS = frozenset({SourceKind.CEA_DIRECT, SourceKind.NASA_PUBLISHED})


@dataclass(frozen=True, slots=True)
class ReferenceQuantity:
    """One value a source states.

    Attributes:
        key: The quantity, as RocketForge names it -- ``chamber_temperature``,
            ``molar_mass``, ``gamma``, ``characteristic_velocity``, or
            ``mole_fraction:<species>`` / ``mass_fraction:<species>``. The basis
            of a fraction is part of its key, so a mole fraction can never be
            compared with a mass fraction.
        value: As the source states it, in :attr:`unit`.
        unit: One :mod:`.units` knows.
        decimals: Printed decimal places, when the source printed fixed-point.
        significant_figures: Printed significant figures, when it printed that
            way. At most one of the two; with neither, the value is taken as
            exact (appropriate for a direct run, not for a printout).
        uncertainty: Absolute, in :attr:`unit`, for a measurement. Carried and
            reported; not turned into a verdict.
        note: Anything a reader needs to interpret the number.
    """

    key: str
    value: float
    unit: str
    decimals: int | None = None
    significant_figures: int | None = None
    uncertainty: float | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key.strip():
            raise ReferenceCaseError("a reference quantity needs a key")
        value = float(self.value)
        if not math.isfinite(value):
            raise ReferenceCaseError(f"{self.key}: value must be finite")
        object.__setattr__(self, "value", value)
        to_canonical(value, self.unit)            # refuses an unknown unit
        if self.decimals is not None and self.significant_figures is not None:
            raise ReferenceCaseError(
                f"{self.key}: give printed decimals or significant figures, "
                "not both")

    @property
    def printed_half_unit(self) -> float | None:
        """Half the last printed digit, in :attr:`unit`; ``None`` if exact.

        A printed 0.3215 at five significant figures means the true value lies
        within 0.000005 of it -- and that, not the looser reading of the
        string, is the bound a printout supports.
        """
        if self.decimals is not None:
            return 0.5 * 10.0 ** (-self.decimals)
        if self.significant_figures is not None:
            if self.value == 0.0:
                return 0.0
            exponent = math.floor(math.log10(abs(self.value)))
            return 0.5 * 10.0 ** (exponent - self.significant_figures + 1)
        return None


@dataclass(frozen=True, slots=True)
class ReferenceCase:
    """Everything a source states about one case, and where it comes from.

    Attributes:
        case_id: Stable identifier.
        title: Human-facing name.
        source_kind: What kind of source -- decides whether a verdict is
            allowed at all.
        benchmark_class: ``"A"`` (solid end-to-end) or ``"B"`` (mechanism
            check, not a solid propellant).
        source: The citation. Required: a reference that cannot say where it
            came from is not a reference.
        code: The program that produced the numbers (``"NASA CEA"``,
            ``"PROPEP"``, ``"EXPLO5"``); empty for an experiment.
        code_version: As stated by the source, or ``"not stated"`` -- never
            left blank, so an unknown version reads as unknown.
        inputs: What was solved, as the source states it.
        quantities: The values it reports.
        missing: What the source does *not* give that a full reproduction would
            need. Recorded, never filled in.
        tolerance_rel: For :attr:`SourceKind.CEA_DIRECT` only: the relative
            agreement required. ``0.0`` means bit-identical.
    """

    case_id: str
    title: str
    source_kind: SourceKind
    benchmark_class: str
    source: str
    code: str
    code_version: str
    inputs: Mapping[str, Any]
    quantities: tuple[ReferenceQuantity, ...]
    missing: tuple[str, ...] = ()
    tolerance_rel: float | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        for name in ("case_id", "title", "source"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ReferenceCaseError(f"a reference case needs a {name}")
        if not isinstance(self.source_kind, SourceKind):
            raise ReferenceCaseError(
                f"source_kind must be a SourceKind, got {self.source_kind!r}")
        if self.benchmark_class not in ("A", "B"):
            raise ReferenceCaseError(
                f"benchmark_class must be 'A' (solid end-to-end) or 'B' "
                f"(mechanism), got {self.benchmark_class!r}")
        if self.source_kind is not SourceKind.EXPERIMENT and not self.code.strip():
            raise ReferenceCaseError(
                f"{self.case_id}: a code-produced reference must name its code")
        if not self.code_version.strip():
            raise ReferenceCaseError(
                f"{self.case_id}: state the code version, or 'not stated'")
        if self.source_kind is SourceKind.CEA_DIRECT:
            if self.tolerance_rel is None or self.tolerance_rel < 0.0:
                raise ReferenceCaseError(
                    f"{self.case_id}: a direct-CEA case needs a tolerance_rel "
                    "(0.0 for bit-identical)")
        elif self.tolerance_rel is not None:
            raise ReferenceCaseError(
                f"{self.case_id}: tolerance_rel applies only to direct-CEA "
                "cases. A printout is held to its printed precision, and an "
                "independent code or an experiment to no tolerance at all.")
        if self.source_kind is SourceKind.NASA_PUBLISHED:
            for q in self.quantities:
                if q.printed_half_unit is None:
                    raise ReferenceCaseError(
                        f"{self.case_id}: {q.key} needs its printed precision; "
                        "a printout is not exact")
        keys = [q.key for q in self.quantities]
        if len(keys) != len(set(keys)):
            raise ReferenceCaseError(f"{self.case_id}: duplicate quantity keys")
        object.__setattr__(self, "inputs", MappingProxyType(dict(self.inputs)))
        object.__setattr__(self, "quantities", tuple(self.quantities))
        object.__setattr__(self, "missing", tuple(self.missing))

    @property
    def allows_verdict(self) -> bool:
        return self.source_kind in VERDICT_KINDS


#: The fields an imported case must carry. Everything else defaults.
REQUIRED_CASE_FIELDS = ("case_id", "title", "source_kind", "benchmark_class",
                        "source", "code", "code_version", "inputs",
                        "quantities")


def case_from_mapping(data: Mapping[str, Any]) -> ReferenceCase:
    """Build a case from plain data -- the import path for a PROPEP or EXPLO5
    run, or a measurement, without writing code.

    Strict on purpose: a missing field is refused, not defaulted, because a
    reference with a silently assumed code version or source kind is worse
    than no reference. ``quantities`` is a list of mappings with the
    :class:`ReferenceQuantity` fields.
    """
    absent = [name for name in REQUIRED_CASE_FIELDS if name not in data]
    if absent:
        raise ReferenceCaseError(f"reference case is missing {absent}")
    try:
        kind = SourceKind(data["source_kind"])
    except ValueError:
        raise ReferenceCaseError(
            f"unknown source_kind {data['source_kind']!r}; one of "
            f"{[k.value for k in SourceKind]}") from None
    quantities = []
    for item in data["quantities"]:
        unknown = set(item) - {"key", "value", "unit", "decimals",
                               "significant_figures", "uncertainty", "note"}
        if unknown:
            raise ReferenceCaseError(f"unknown quantity fields {sorted(unknown)}")
        quantities.append(ReferenceQuantity(**item))
    return ReferenceCase(
        case_id=data["case_id"], title=data["title"], source_kind=kind,
        benchmark_class=data["benchmark_class"], source=data["source"],
        code=data["code"], code_version=data["code_version"],
        inputs=data["inputs"], quantities=tuple(quantities),
        missing=tuple(data.get("missing", ())),
        tolerance_rel=data.get("tolerance_rel"),
        notes=data.get("notes", ""))
