"""Propulsion evidence: what sources say, where they say it, and what it can support.

A pure-data layer, importing only ``core``. It holds sourced values and
explicit absences, source identity and shipping rights, propellant
formulations and burn-rate laws as sources print them, and per-dimension
evidence status. It
computes no physics, calls no provider, runs no solver and knows nothing of Qt;
``tests/test_architecture.py`` holds it to that.

Two things are deliberately elsewhere. Comparing a RocketForge result with a
reference is ``rocketforge.comparison``, which already owns verdict rules;
records here link to its cases by ``case_id``. Deciding whether a formulation
can be posed to NASA CEA needs the provider, and belongs to the application
layer's gateway, not to the data describing the formulation.

The layer's place in the architecture is ``docs/engineering/01_engineering_architecture.md``
section 2; the shipped data lives in ``rocketforge/data/evidence/``.
"""

from __future__ import annotations

from .burnlaw import BURN_LAW_FORM, BurnLawReference, BurnLawRegime
from .load import (
    BURN_LAW_SCHEMA_VERSION,
    RECORD_SCHEMA_VERSIONS,
    SCHEMA_VERSION,
    record_from_dict,
    record_from_json,
    record_to_dict,
    record_to_json,
    sources_from_json,
    sources_to_json,
)
from .records import (
    MASS_FRACTION_BASIS,
    CustomDefinition,
    EvidenceRecord,
    IngredientReference,
    PropellantReference,
    RecordKind,
    SourceReference,
    reported_values,
    validate_against_sources,
)
from .values import (
    AccessClass,
    Datum,
    Dimension,
    EvidenceError,
    EvidenceSchemaError,
    EvidenceStatus,
    Missing,
    MissingReason,
    ReportedValue,
    ShippingPolicy,
    ValueStatus,
)

__all__ = [
    "SCHEMA_VERSION", "BURN_LAW_SCHEMA_VERSION", "RECORD_SCHEMA_VERSIONS",
    "BURN_LAW_FORM", "BurnLawReference", "BurnLawRegime",
    "record_from_dict", "record_from_json", "record_to_dict",
    "record_to_json", "sources_from_json", "sources_to_json",
    "MASS_FRACTION_BASIS", "CustomDefinition", "EvidenceRecord",
    "IngredientReference", "PropellantReference", "RecordKind", "SourceReference",
    "reported_values", "validate_against_sources",
    "AccessClass", "Datum", "Dimension", "EvidenceError", "EvidenceSchemaError",
    "EvidenceStatus", "Missing", "MissingReason", "ReportedValue",
    "ShippingPolicy", "ValueStatus",
]
