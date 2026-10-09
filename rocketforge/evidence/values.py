"""Sourced values and explicit absence: the atoms every evidence record is built from.

A number in an evidence record is only as useful as the answer to "where does
it say that?". So a value here never stands alone: :class:`ReportedValue`
carries the value *as the source printed it*, the unit the source printed, the
source it came from, where in that source, and how it got into the record --
read directly, derived by arithmetic, digitised from a plot, or inferred.

The other half is just as important. A source that does not state a density has
not stated a density of zero, and it has not stated one somewhere else either.
:class:`Missing` records that, with the reason, so a field can never silently
disappear from a record and a reader can never mistake "not reported" for "not
looked for".

Deliberately absent: unit conversion. Evidence stores what the source says;
converting happens at the point of use, through the one validated unit table
(``rocketforge.comparison.units``), where a conversion error would show up as a
comparison difference instead of being baked into the record.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from rocketforge.core.errors import InputError

__all__ = [
    "EvidenceError",
    "EvidenceSchemaError",
    "ValueStatus",
    "MissingReason",
    "Dimension",
    "EvidenceStatus",
    "ShippingPolicy",
    "AccessClass",
    "ReportedValue",
    "Missing",
    "Datum",
]


class EvidenceError(InputError):
    """An evidence record, or a value in one, is incomplete or self-contradictory."""


class EvidenceSchemaError(EvidenceError):
    """Serialised evidence does not match the schema this build understands.

    Raised for an unsupported ``schema_version``, an unknown or missing field,
    a value of the wrong JSON type, or an unknown enumeration value. Refused
    rather than read leniently: a record that parses "mostly" is a record whose
    missing part nobody noticed.
    """


class ValueStatus(StrEnum):
    """How a value entered the record."""

    REPORTED = "REPORTED"
    """Printed by the source, transcribed as printed."""

    DERIVED = "DERIVED"
    """Computed from reported values by stated arithmetic (unit conversion, a ratio)."""

    DIGITISED = "DIGITISED"
    """Read off a plot. Carries the digitiser's uncertainty, never a printed precision."""

    INFERRED = "INFERRED"
    """Reasoned from context rather than stated. Never a basis for a verdict."""


class MissingReason(StrEnum):
    """Why a field has no value."""

    NOT_REPORTED = "NOT_REPORTED"
    """The source does not give it."""

    UNKNOWN = "UNKNOWN"
    """It could not be determined."""

    NOT_AUDITED = "NOT_AUDITED"
    """The source was not examined for it."""

    WITHHELD_RIGHTS = "WITHHELD_RIGHTS"
    """The source gives it, but the value may not be shipped.

    The engine research package (DB-0) called this ``RIGHTS_RESTRICTED``; it is
    the same meaning and has this one spelling."""

    ACCESS_BLOCKED = "ACCESS_BLOCKED"
    """The source that would give it could not be opened (refused, not found).

    Added for reference-engine evidence. It says nothing about whether the
    source gives the value, only that nobody could look."""


class Dimension(StrEnum):
    """The four independent validation dimensions. A record is judged on each separately."""

    VA = "VA"   # thermochemistry
    VB = "VB"   # burn rate
    VC = "VC"   # internal ballistics
    VD = "VD"   # motor performance


class EvidenceStatus(StrEnum):
    """What a record can support in one dimension.

    There is no ``GOLD`` and no overall score: a dataset can be strong in one
    dimension and unusable in another, and a single label would hide that.
    """

    REGRESSION_LOCKED = "REGRESSION_LOCKED"
    VERIFIED_NUMERICAL_REFERENCE = "VERIFIED_NUMERICAL_REFERENCE"
    SOURCE_COMPLETE_CANDIDATE = "SOURCE_COMPLETE_CANDIDATE"
    VALIDATION_CANDIDATE = "VALIDATION_CANDIDATE"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    UNDERDEFINED = "UNDERDEFINED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ACCESS_BLOCKED = "ACCESS_BLOCKED"


class ShippingPolicy(StrEnum):
    """What of a source may be distributed inside RocketForge.

    Public is not the same as redistributable. Only
    :attr:`VALUES_WITH_ATTRIBUTION` permits a shipped record to carry values
    taken from the source; every other policy permits metadata only.
    """

    VALUES_WITH_ATTRIBUTION = "VALUES_WITH_ATTRIBUTION"
    METADATA_ONLY = "METADATA_ONLY"
    RESTRICTED_REFERENCE = "RESTRICTED_REFERENCE"
    LICENSED_PROVIDER = "LICENSED_PROVIDER"
    RIGHTS_REVIEW_REQUIRED = "RIGHTS_REVIEW_REQUIRED"


class AccessClass(StrEnum):
    """How a reader can obtain the source."""

    PUBLIC_OPEN = "PUBLIC_OPEN"
    PUBLIC_WEB_PAGE = "PUBLIC_WEB_PAGE"
    PAYWALLED = "PAYWALLED"
    ACCOUNT_RESTRICTED = "ACCOUNT_RESTRICTED"
    COMMERCIAL_PRODUCT = "COMMERCIAL_PRODUCT"
    NOT_RETRIEVED = "NOT_RETRIEVED"


def _text(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{what} must be a non-empty string, got {value!r}")
    return value


def _precision(value: object, what: str, minimum: int) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise EvidenceError(f"{what} must be an integer >= {minimum} or None, got {value!r}")
    return value


@dataclass(frozen=True, slots=True)
class ReportedValue:
    """One value a source states, with everything needed to find it again.

    Attributes:
        value: As the source states it, in :attr:`unit`. Never converted,
            rounded or corrected here -- a printed typo stays a printed typo,
            and is flagged in :attr:`note`.
        unit: As the source prints it (``"cal/mol"``, ``"mass fraction"``).
        source_id: The ``SourceReference.source_id`` it comes from.
        locator: Where in that source: page, table, figure, line.
        status: How it entered the record (:class:`ValueStatus`).
        decimals: Printed decimal places, when the source printed fixed-point.
        significant_figures: Printed significant figures, when it printed that
            way. At most one of the two; with neither, no printed precision is
            claimed.
        note: Anything a reader needs to interpret the number.
    """

    value: float
    unit: str
    source_id: str
    locator: str
    status: ValueStatus
    decimals: int | None = None
    significant_figures: int | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise EvidenceError(f"a reported value must be a real number, got {self.value!r}")
        number = float(self.value)
        if not math.isfinite(number):
            raise EvidenceError(f"a reported value must be finite, got {number!r}")
        object.__setattr__(self, "value", number)
        _text(self.unit, "unit")
        _text(self.source_id, "source_id")
        _text(self.locator, "locator (page, table or figure in the source)")
        if not isinstance(self.status, ValueStatus):
            raise EvidenceError(f"status must be a ValueStatus, got {self.status!r}")
        _precision(self.decimals, "decimals", 0)
        _precision(self.significant_figures, "significant_figures", 1)
        if self.decimals is not None and self.significant_figures is not None:
            raise EvidenceError("give printed decimals or significant figures, not both")
        if not isinstance(self.note, str):
            raise EvidenceError(f"note must be a string, got {self.note!r}")


@dataclass(frozen=True, slots=True)
class Missing:
    """A field the record deliberately has no value for, and why."""

    reason: MissingReason
    note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.reason, MissingReason):
            raise EvidenceError(f"reason must be a MissingReason, got {self.reason!r}")
        if not isinstance(self.note, str):
            raise EvidenceError(f"note must be a string, got {self.note!r}")


#: A scientific field is always one of these, never absent.
Datum = ReportedValue | Missing
