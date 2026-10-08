"""The shapes every propulsion-system study shares: branches, ledgers, results.

A study has two branches, oxidiser and fuel, each computed on its own and kept
in its own place, plus a few totals across both. Each branch carries:

* ``quantities`` -- SI numbers, each one valued or, in ``unresolved``, absent
  with the reason;
* ``labels`` -- named states that are words, not numbers (a management mode,
  an availability status);
* ``ledger`` -- the terms a total is built from, each resolved, not
  applicable, unresolved or excluded. Unresolved is never zero;
* ``series`` -- a short table where a quantity evolves (blowdown pressure).

A result is immutable and round-trips through versioned JSON. Loading checks
the definition against its fingerprint, so a hand-edited record is refused.
Each gate registers its schema here with the definition class and the keys
its branches and totals may carry.

SI units throughout.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from ..injector import Branch
from ..requirement import RequirementFormatError

__all__ = [
    "Branch",
    "BranchOutcome",
    "LedgerLine",
    "Quantity",
    "StudyResult",
    "StudyStatus",
    "Upstream",
    "fingerprint",
    "register_schema",
]


class StudyStatus(StrEnum):
    OK = "ok"                    # computed and complete
    INCOMPLETE = "incomplete"    # computed; a total waits on an unresolved term
    WARNING = "warning"          # computed; an advisory applies (a negative margin, ...)
    REFUSED = "refused"          # a branch could not be computed


LINE_STATUSES = ("resolved", "not_applicable", "unresolved", "excluded")


@dataclass(frozen=True, slots=True)
class Quantity:
    """One reported quantity. ``unit`` is the SI unit of the stored value."""

    key: str
    label: str
    group: str
    unit: str = ""
    note: str = ""


def fingerprint(payload: Mapping[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class Upstream:
    """The identity of one upstream result a basis was copied from."""

    gate: str                    # "LIQ-4", "SYS-1", ...
    fingerprint: str             # its definition fingerprint
    status: str                  # its status when copied

    def to_dict(self) -> dict[str, str]:
        return {"gate": self.gate, "fingerprint": self.fingerprint, "status": self.status}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Upstream":
        return cls(str(payload["gate"]), str(payload["fingerprint"]), str(payload["status"]))


@dataclass(frozen=True, slots=True)
class LedgerLine:
    """One term of a total as computed.

    ``status`` is "resolved" (``value`` set, in ``unit``), "not_applicable"
    (declared absent, adds nothing), "unresolved" (not known; the total waits
    on it) or "excluded" (deliberately not counted here, with the reason --
    for example a term another gate already counts). A resolved value may be
    signed when the term is a gain.
    """

    key: str
    label: str
    status: str
    value: float | None
    unit: str = ""
    source: str = ""
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status not in LINE_STATUSES:
            raise ValueError(f"unknown term status {self.status!r}")
        if (self.value is not None) != (self.status == "resolved"):
            raise ValueError(f"{self.key}: a value exists exactly when the term is resolved")
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError(f"{self.key}: a resolved term is finite")
        if self.status != "resolved" and not self.reason.strip():
            raise ValueError(f"{self.key}: a term that is not resolved says why")

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "label": self.label, "status": self.status,
                "value": self.value, "unit": self.unit, "source": self.source,
                "reason": self.reason}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "LedgerLine":
        value = payload.get("value")
        return cls(key=str(payload["key"]), label=str(payload["label"]),
                   status=str(payload["status"]),
                   value=None if value is None else float(value),
                   unit=str(payload.get("unit", "")), source=str(payload.get("source", "")),
                   reason=str(payload.get("reason", "")))


def _numbers(payload: Mapping[str, Any]) -> dict[str, float]:
    return {str(k): float(v) for k, v in dict(payload).items()}


def _texts(payload: Mapping[str, Any]) -> dict[str, str]:
    return {str(k): str(v) for k, v in dict(payload).items()}


@dataclass(frozen=True, slots=True)
class BranchOutcome:
    """One branch of one study, computed or refused."""

    branch: Branch
    status: StudyStatus
    quantities: Mapping[str, float] = field(default_factory=dict)
    unresolved: Mapping[str, str] = field(default_factory=dict)
    labels: Mapping[str, str] = field(default_factory=dict)
    ledger: tuple[LedgerLine, ...] = ()
    series: tuple[Mapping[str, float], ...] = ()
    provenance: Mapping[str, str] = field(default_factory=dict)
    message: str = ""
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.branch, Branch) or not isinstance(self.status, StudyStatus):
            raise ValueError("a branch outcome names its branch and status")
        if set(self.quantities) & set(self.unresolved):
            raise ValueError("a quantity is both valued and unresolved")
        if self.status is StudyStatus.REFUSED and (self.quantities or self.ledger
                                                   or self.series):
            raise ValueError("a refused branch carries no quantities, ledger or series")
        for key, value in self.quantities.items():
            if not math.isfinite(value):
                raise ValueError(f"{key} must be finite")
        for row in self.series:
            if not all(math.isfinite(v) for v in row.values()):
                raise ValueError("a series value must be finite")

    @property
    def ok(self) -> bool:
        return self.status is not StudyStatus.REFUSED

    def value(self, key: str) -> float | None:
        return self.quantities.get(key)

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch.value, "status": self.status.value,
            "quantities": dict(self.quantities), "unresolved": dict(self.unresolved),
            "labels": dict(self.labels),
            "ledger": [line.to_dict() for line in self.ledger],
            "series": [dict(row) for row in self.series],
            "provenance": dict(self.provenance), "message": self.message,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BranchOutcome":
        return cls(
            branch=Branch(payload["branch"]), status=StudyStatus(payload["status"]),
            quantities=_numbers(payload["quantities"]),
            unresolved=_texts(payload["unresolved"]),
            labels=_texts(payload.get("labels", {})),
            ledger=tuple(LedgerLine.from_dict(line) for line in payload.get("ledger", ())),
            series=tuple(_numbers(row) for row in payload.get("series", ())),
            provenance=_texts(payload.get("provenance", {})),
            message=str(payload.get("message", "")),
            notes=tuple(str(n) for n in payload.get("notes", ())),
        )


class Definition(Protocol):
    @property
    def fingerprint(self) -> str: ...

    def to_dict(self) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class _Schema:
    version: int
    definition: Any                     # the definition class, with from_dict
    branch_keys: frozenset[str]
    total_keys: frozenset[str]
    label_keys: frozenset[str]


_SCHEMAS: dict[str, _Schema] = {}


def register_schema(schema: str, version: int, definition: Any,
                    branch_quantities: tuple[Quantity, ...],
                    total_quantities: tuple[Quantity, ...] = (),
                    branch_labels: tuple[str, ...] = ()) -> None:
    """Declare a gate's record: its definition class and the keys it may carry."""
    _SCHEMAS[schema] = _Schema(version, definition,
                               frozenset(q.key for q in branch_quantities),
                               frozenset(q.key for q in total_quantities),
                               frozenset(branch_labels))


@dataclass(frozen=True, slots=True)
class StudyResult:
    """Both branches of one study and its totals, or why not."""

    schema: str
    definition: Any
    status: StudyStatus
    oxidiser: BranchOutcome
    fuel: BranchOutcome
    totals: Mapping[str, float] = field(default_factory=dict)
    totals_unresolved: Mapping[str, str] = field(default_factory=dict)
    message: str = ""
    assumptions: tuple[str, ...] = ()
    provenance: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        spec = _SCHEMAS.get(self.schema)
        if spec is None:
            raise ValueError(f"unknown study schema {self.schema!r}")
        if not isinstance(self.definition, spec.definition):
            raise ValueError("the definition is not this study's")
        if self.oxidiser.branch is not Branch.OXIDISER or self.fuel.branch is not Branch.FUEL:
            raise ValueError("the oxidiser and fuel results are each in their own place")
        for outcome in (self.oxidiser, self.fuel):
            unknown = (set(outcome.quantities) | set(outcome.unresolved)) - spec.branch_keys
            if unknown:
                raise ValueError(f"unknown branch quantities {sorted(unknown)}")
            if set(outcome.labels) - spec.label_keys:
                raise ValueError(f"unknown branch labels {sorted(set(outcome.labels) - spec.label_keys)}")
        unknown = (set(self.totals) | set(self.totals_unresolved)) - spec.total_keys
        if unknown:
            raise ValueError(f"unknown totals {sorted(unknown)}")
        if set(self.totals) & set(self.totals_unresolved):
            raise ValueError("a total is both valued and unresolved")
        for key, value in self.totals.items():
            if not math.isfinite(value):
                raise ValueError(f"{key} must be finite")
        refused = not (self.oxidiser.ok and self.fuel.ok)
        if refused != (self.status is StudyStatus.REFUSED):
            raise ValueError("the study is refused exactly when a branch is")
        if refused and self.totals:
            raise ValueError("a refused study carries no totals")

    @property
    def ok(self) -> bool:
        return self.status is not StudyStatus.REFUSED

    def branch(self, branch: Branch) -> BranchOutcome:
        return self.oxidiser if branch is Branch.OXIDISER else self.fuel

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": _SCHEMAS[self.schema].version,
            "definition": self.definition.to_dict(),
            "definition_fingerprint": self.definition.fingerprint,
            "status": self.status.value,
            "oxidiser": self.oxidiser.to_dict(),
            "fuel": self.fuel.to_dict(),
            "totals": dict(self.totals),
            "totals_unresolved": dict(self.totals_unresolved),
            "message": self.message,
            "assumptions": list(self.assumptions),
            "provenance": dict(self.provenance),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False, allow_nan=False) + "\n"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], schema: str) -> "StudyResult":
        """Load a record of ``schema``. Anything else, or a record whose
        definition does not match its fingerprint, is refused."""
        if not isinstance(payload, Mapping):
            raise RequirementFormatError("a study record must be a mapping")
        spec = _SCHEMAS.get(schema)
        if spec is None or payload.get("schema") != schema:
            raise RequirementFormatError(
                f"not a {schema} record (schema {payload.get('schema')!r})")
        if payload.get("version") != spec.version:
            raise RequirementFormatError(
                f"{schema} record version {payload.get('version')!r} is not supported")
        try:
            result = cls(
                schema=schema,
                definition=spec.definition.from_dict(payload["definition"]),
                status=StudyStatus(payload["status"]),
                oxidiser=BranchOutcome.from_dict(payload["oxidiser"]),
                fuel=BranchOutcome.from_dict(payload["fuel"]),
                totals=_numbers(payload.get("totals", {})),
                totals_unresolved=_texts(payload.get("totals_unresolved", {})),
                message=str(payload.get("message", "")),
                assumptions=tuple(str(a) for a in payload.get("assumptions", ())),
                provenance=_texts(payload.get("provenance", {})),
            )
        except KeyError as missing:
            raise RequirementFormatError(f"{schema} record lacks {missing}") from None
        except (TypeError, ValueError) as error:
            if isinstance(error, RequirementFormatError):
                raise
            raise RequirementFormatError(str(error)) from None
        if payload.get("definition_fingerprint") != result.definition.fingerprint:
            raise RequirementFormatError(
                "the record's definition does not match its fingerprint")
        return result

    @classmethod
    def from_json(cls, text: str, schema: str) -> "StudyResult":
        try:
            payload = json.loads(text)
        except (TypeError, ValueError) as error:
            raise RequirementFormatError(f"not valid JSON: {error}") from None
        return cls.from_dict(payload, schema)
