"""Comparison of RocketForge results with reference cases.

A layer of its own, importing only ``core`` and ``physics``: it compares
results it is handed and cannot run a solver itself, so a comparison can never
quietly produce the number it is checking.

What a comparison may conclude depends on the source (see :mod:`.cases`):
a verdict against direct CEA or a NASA printout; differences only, and no
verdict and no ranking, against an independent code such as PROPEP or EXPLO5
or against an experiment.

Named ``comparison`` rather than ``validation`` because "validation" already
means input guarding in this codebase
(``rocketforge/physics/thermochemistry/validation.py``).
"""

from __future__ import annotations

from .cases import (
    REQUIRED_CASE_FIELDS,
    VERDICT_KINDS,
    ReferenceCase,
    ReferenceCaseError,
    ReferenceQuantity,
    SourceKind,
    case_from_mapping,
)
from .compare import (
    AGREES,
    COMPARED,
    DIFFERS,
    INCOMPLETE,
    CaseComparison,
    ObservedQuantity,
    QuantityComparison,
    compare,
)
from .extract import observed_from_chamber
from .units import CANONICAL_UNIT, UnitError, to_canonical

__all__ = [
    "SourceKind", "ReferenceQuantity", "ReferenceCase", "ReferenceCaseError",
    "VERDICT_KINDS", "REQUIRED_CASE_FIELDS", "case_from_mapping",
    "ObservedQuantity", "QuantityComparison",
    "CaseComparison", "compare", "AGREES", "DIFFERS", "COMPARED",
    "INCOMPLETE", "observed_from_chamber", "CANONICAL_UNIT", "UnitError",
    "to_canonical",
]
