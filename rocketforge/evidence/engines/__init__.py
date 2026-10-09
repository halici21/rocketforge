"""Reference-engine evidence: the production schema for what sources say about liquid rocket engines.

DB-1 of the reference engine database. A data model and its validators only:
no records ship with it (that is DB-2), nothing here is shown in the UI, and
nothing here is solved. It sits in the ``evidence`` layer and imports only
``core`` and the rest of ``evidence``.

What it reuses from :mod:`rocketforge.evidence`: :class:`~rocketforge.evidence.Missing`
and :class:`~rocketforge.evidence.MissingReason` for explicit absence,
:class:`~rocketforge.evidence.ValueStatus` for how a value entered the record,
:class:`~rocketforge.evidence.SourceReference` (wrapped by :class:`EngineSource`)
for source identity and the values shipping decision,
:class:`~rocketforge.evidence.ShippingPolicy` for every rights policy, and the
strict JSON conventions of :mod:`rocketforge.evidence.load`.

What it adds: an identity hierarchy (family, variant, configuration,
operating point) with no value inheritance; propulsion units, aliases and
lineage; typed assertions with value kinds and structured conditions;
multi-statement rights records; conflicts that reference claims; components,
schematics with provenance, and topology graphs with typed edges and explicit
completeness. Design: ``docs/engineering/design/DB1_REFERENCE_ENGINE_EVIDENCE_SCHEMA.md``.
"""

from __future__ import annotations

from .assertions import (
    FIELD_PATH_PATTERN,
    Assertion,
    AssertionValue,
    Conditions,
    Derivation,
    EnumValue,
    NormalizedQuantity,
    NumberValue,
    Qualifier,
    RangeValue,
    Setting,
    TextValue,
)
from .conflicts import Conflict
from .corpus import (
    BLOCKING_RESOLUTIONS,
    REGRESSION_AUTHORITIES,
    EngineEvidenceCorpus,
    original_topology_blockers,
    regression_blockers,
)
from .identity import (
    Alias,
    EngineConfiguration,
    EngineFamily,
    EngineVariant,
    LineageEdge,
    OperatingPoint,
    PropulsionUnit,
    SubjectRef,
    UnitMember,
)
from .load import (
    ENGINE_EVIDENCE_FORMAT,
    ENGINE_EVIDENCE_SCHEMA_VERSION,
    corpus_fingerprint,
    corpus_from_dict,
    corpus_from_json,
    corpus_to_dict,
    corpus_to_json,
)
from .sources import RIGHTS_IN_RECORD, EngineSource, RightsNotice, RightsRecord
from .topology import (
    HARDWARE_SCOPES,
    AbsenceStatement,
    Completeness,
    Component,
    Schematic,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)
from .vocabulary import (
    FLUID_EDGE_KINDS,
    MEDIUM_EDGE_KINDS,
    OPERATING_VALUE_KINDS,
    ORIGINAL_PROVENANCES,
    TIER_FOR_AUTHORITY,
    Admissibility,
    AliasKind,
    ComponentType,
    ConflictCategory,
    ConflictResolution,
    EdgeKind,
    Environment,
    IspBasis,
    LineageKind,
    MixtureRatioBasis,
    MixtureRatioForm,
    Ownership,
    PressureBasis,
    PressureStation,
    PropulsionUnitKind,
    RightsReview,
    SchematicProvenance,
    SourceAccess,
    SourceAuthority,
    SourcePrimacy,
    SubjectKind,
    TopologyEvidence,
    ValueKind,
)

__all__ = [
    "FIELD_PATH_PATTERN", "Assertion", "AssertionValue", "Conditions", "Derivation", "EnumValue",
    "NormalizedQuantity", "NumberValue", "Qualifier", "RangeValue", "Setting", "TextValue",
    "Conflict",
    "BLOCKING_RESOLUTIONS", "REGRESSION_AUTHORITIES", "EngineEvidenceCorpus",
    "original_topology_blockers", "regression_blockers",
    "Alias", "EngineConfiguration", "EngineFamily", "EngineVariant", "LineageEdge",
    "OperatingPoint", "PropulsionUnit", "SubjectRef", "UnitMember",
    "ENGINE_EVIDENCE_FORMAT", "ENGINE_EVIDENCE_SCHEMA_VERSION", "corpus_fingerprint",
    "corpus_from_dict", "corpus_from_json", "corpus_to_dict", "corpus_to_json",
    "EngineSource", "RightsNotice", "RightsRecord", "RIGHTS_IN_RECORD", "HARDWARE_SCOPES",
    "AbsenceStatement", "Completeness", "Component", "Schematic", "TopologyEdge",
    "TopologyGraph", "TopologyNode",
    "FLUID_EDGE_KINDS", "MEDIUM_EDGE_KINDS", "OPERATING_VALUE_KINDS", "ORIGINAL_PROVENANCES", "TIER_FOR_AUTHORITY",
    "Admissibility", "AliasKind", "ComponentType", "ConflictCategory", "ConflictResolution",
    "EdgeKind", "Environment", "IspBasis", "LineageKind", "MixtureRatioBasis",
    "MixtureRatioForm", "Ownership", "PressureBasis", "PressureStation", "PropulsionUnitKind",
    "RightsReview", "SchematicProvenance", "SourceAccess", "SourceAuthority", "SourcePrimacy",
    "SubjectKind", "TopologyEvidence", "ValueKind",
]
