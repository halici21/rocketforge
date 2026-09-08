"""JSON-safe encoding for the thermochemistry domain records.

Encoding only. The backend has no DTO *decoding* framework today, and inventing
one here would be a second architecture for a problem nobody has yet; Phase 5B
spec section 122 permits encoding-only on exactly that condition. When a
decoding contract arrives, it decodes these shapes.

Two rules the encoder keeps:

* **No rounding.** Floats are emitted at full ``float64`` precision. Display
  precision is the interface's decision and is applied where a human reads the
  number, never where a machine stores it (Phase 5B spec section 123).
* **Nothing is invented.** A field that is ``None`` encodes as ``null``. The
  encoder never substitutes a default for missing data.

Negative zero is normalised to ``0.0``. It is the same value, it renders as
``-0.0`` in a report, and no physical quantity in this domain distinguishes the
two (Phase 5B spec section 128). Genuine negative values are untouched.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

from .composition import (
    Composition,
    ElementalInventory,
    ElementBalanceReport,
)
from .propellants import (
    MixtureRatio,
    PropellantDefinition,
    PropellantPair,
    PropellantPairReferenceCase,
    PropellantStream,
)
from .protocols import ProviderCapabilities, ProviderCapability
from .provenance import ThermochemistryProvenance
from .requests import ChamberEquilibriumRequest, ExpansionRequest
from .species import ElementalComposition, Species, ThermoPolynomial
from .states import ChamberGas, GasStation
from .validation import IdentityCheck, ValidationReport

__all__ = ["to_jsonable", "SERIALISABLE_TYPES"]

#: Every public record this module knows how to encode. Used by the
#: serialization tests to prove the coverage claim rather than assert it.
SERIALISABLE_TYPES: tuple[type, ...] = (
    ElementalComposition,
    ThermoPolynomial,
    Species,
    Composition,
    ElementalInventory,
    ElementBalanceReport,
    PropellantDefinition,
    PropellantStream,
    MixtureRatio,
    PropellantPair,
    PropellantPairReferenceCase,
    ChamberEquilibriumRequest,
    ExpansionRequest,
    ThermochemistryProvenance,
    ProviderCapabilities,
    ChamberGas,
    GasStation,
    IdentityCheck,
    ValidationReport,
)


def _number(value: float) -> float:
    """A JSON-safe float, with negative zero normalised and NaN refused."""
    number = float(value)
    if math.isnan(number) or math.isinf(number):
        raise ValueError(
            f"{number!r} is not representable in JSON; a non-finite value should "
            "never have reached a validated record")
    return 0.0 if number == 0.0 else number


def to_jsonable(value: Any) -> Any:
    """Convert a thermochemistry record into JSON-safe primitives.

    Handles the domain records, the enums, dataclasses generally, mappings,
    sequences and scalars. Sets become sorted lists so that encoding is
    deterministic -- an unordered set would produce a different document on
    every run and make two identical results look different.
    """
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return _number(value)

    # ElementalComposition and Composition store (key, value) pairs; emitting
    # them as objects reads far better than as arrays of two-element arrays.
    if isinstance(value, ElementalComposition):
        return {"atoms": {symbol: _number(count) for symbol, count in value.entries}}
    if isinstance(value, Composition):
        payload: dict[str, Any] = {
            "fractions": {name: _number(x) for name, x in value.entries},
            "basis": value.basis.value,
        }
        if value.database:
            payload["database"] = value.database
        if value.database_version:
            payload["database_version"] = value.database_version
        if value.canonicalised_from_sum is not None:
            payload["canonicalised_from_sum"] = _number(value.canonicalised_from_sum)
        return payload
    if isinstance(value, ProviderCapabilities):
        return {
            "supported": sorted(c.value for c in value.supported),
            "pressure_range": (None if value.pressure_range is None
                               else [_number(v) for v in value.pressure_range]),
            "mixture_ratio_range": (None if value.mixture_ratio_range is None
                                    else [_number(v) for v in value.mixture_ratio_range]),
            "temperature_ceiling": (None if value.temperature_ceiling is None
                                    else _number(value.temperature_ceiling)),
        }

    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(to_jsonable(v) for v in value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, ProviderCapability):
        return value.value

    raise TypeError(
        f"{type(value).__name__} has no JSON-safe encoding; add one deliberately "
        "rather than falling back on repr()")
