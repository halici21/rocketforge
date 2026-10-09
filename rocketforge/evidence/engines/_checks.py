"""Construction-time checks shared by the engine-evidence types."""

from __future__ import annotations

import math
import re
from enum import StrEnum
from typing import Any, TypeVar

from ..values import EvidenceError

E = TypeVar("E", bound=StrEnum)

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]*$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def text(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{what} must be a non-empty string, got {value!r}")
    return value


def plain(value: object, what: str) -> str:
    """A string that may be empty (notes)."""
    if not isinstance(value, str):
        raise EvidenceError(f"{what} must be a string, got {value!r}")
    return value


def optional_text(value: object, what: str) -> str | None:
    return None if value is None else text(value, what)


def ident(value: object, what: str) -> str:
    text(value, what)
    if not _ID.match(value):  # type: ignore[arg-type]
        raise EvidenceError(f"{what} {value!r} is not a valid identifier "
                            "(letters, digits and . _ : / + - only, no spaces)")
    return value  # type: ignore[return-value]


def idents(values: object, what: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise EvidenceError(f"{what} must be a tuple, got {type(values).__name__}")
    for item in values:
        ident(item, f"each entry of {what}")
    if not allow_empty and not values:
        raise EvidenceError(f"{what} must not be empty")
    if len(set(values)) != len(values):
        raise EvidenceError(f"{what} contains a duplicate")
    return values


def texts(values: object, what: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise EvidenceError(f"{what} must be a tuple, got {type(values).__name__}")
    for item in values:
        text(item, f"each entry of {what}")
    if len(set(values)) != len(values):
        raise EvidenceError(f"{what} contains a duplicate")
    return values


def member(kind: type[E], value: object, what: str) -> E:
    if not isinstance(value, kind):
        raise EvidenceError(f"{what} must be a {kind.__name__}, got {value!r}")
    return value


def optional_member(kind: type[E], value: object, what: str) -> E | None:
    return None if value is None else member(kind, value, what)


def number(value: object, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceError(f"{what} must be a real number, got {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise EvidenceError(f"{what} must be finite, got {result!r}")
    return result


def sha256_hex(value: object, what: str) -> str:
    if not isinstance(value, str) or not _HEX64.match(value):
        raise EvidenceError(f"{what} must be 64 lowercase hexadecimal digits, got {value!r}")
    return value


def instances(values: object, kind: type, what: str) -> tuple[Any, ...]:
    if not isinstance(values, tuple):
        raise EvidenceError(f"{what} must be a tuple, got {type(values).__name__}")
    for item in values:
        if not isinstance(item, kind):
            raise EvidenceError(f"every entry of {what} must be a {kind.__name__}, got {item!r}")
    return values
