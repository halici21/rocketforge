"""The closed vocabularies of reference-engine evidence.

Every enumeration here exists because a real document needed the distinction
(DB-0.5, ``docs/research/engine_database/db05``). Each one has an explicit
"not stated" member where a source can fail to say: an unstated chamber-pressure
station is recorded as :attr:`PressureStation.UNKNOWN`, never guessed and never
left out.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "SourceAuthority", "TIER_FOR_AUTHORITY", "SourcePrimacy", "SourceAccess",
    "RightsReview", "ValueKind", "OPERATING_VALUE_KINDS", "Admissibility",
    "Environment", "PressureBasis", "PressureStation", "IspBasis",
    "MixtureRatioBasis", "MixtureRatioForm", "SubjectKind", "PropulsionUnitKind",
    "AliasKind", "LineageKind", "ConflictResolution", "ConflictCategory",
    "ComponentType", "Ownership", "EdgeKind", "FLUID_EDGE_KINDS", "MEDIUM_EDGE_KINDS",
    "TopologyEvidence",
    "SchematicProvenance", "ORIGINAL_PROVENANCES",
]


class SourceAuthority(StrEnum):
    """How close a source is to the hardware.

    Independent of redistribution rights and of whether the source was opened.
    """

    A = "A"
    """Agency or manufacturer document (NASA report, manufacturer data sheet)."""

    B = "B"
    """Peer-reviewed or professional-society paper, or a review committee compilation."""

    C = "C"
    """Textbook or reference handbook."""

    D = "D"
    """Encyclopaedia or curated web reference."""

    E = "E"
    """Forum, blog, news aggregator."""


#: The existing ``SourceReference.tier`` (1 primary, 2 strong secondary, 3
#: discovery only) that each authority corresponds to. An engine source must
#: carry the matching tier on its ``SourceReference``.
TIER_FOR_AUTHORITY: dict[SourceAuthority, int] = {
    SourceAuthority.A: 1, SourceAuthority.B: 1, SourceAuthority.C: 2,
    SourceAuthority.D: 3, SourceAuthority.E: 3,
}


class SourcePrimacy(StrEnum):
    """Whether the source is where the fact was first stated."""

    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TERTIARY = "TERTIARY"


class SourceAccess(StrEnum):
    """What was actually done with the document.

    Only :attr:`OPENED` makes a source's printed values evidence.
    """

    OPENED = "OPENED"
    """Fetched and read; values carry page, table or figure locators."""

    IDENTITY_VERIFIED_ONLY = "IDENTITY_VERIFIED_ONLY"
    """Its identity (title, report number) was checked; its content was not read."""

    FETCHED_NOT_READ = "FETCHED_NOT_READ"
    """Downloaded but not read."""

    SEARCH_RESULT_ONLY = "SEARCH_RESULT_ONLY"
    """Known only from a search-engine result or summary."""

    ACCESS_BLOCKED = "ACCESS_BLOCKED"
    """An attempt to open it failed (refused, not found, no URL)."""


class RightsReview(StrEnum):
    """Where the rights reading of a source stands."""

    NOT_REVIEWED = "NOT_REVIEWED"
    """Nobody has compared the statements yet."""

    CONSISTENT = "CONSISTENT"
    """The statements that exist agree."""

    CONFLICT_UNRESOLVED = "CONFLICT_UNRESOLVED"
    """The host and the page disagree, and no review has settled it."""

    CONFLICT_RESOLVED_BY_REVIEW = "CONFLICT_RESOLVED_BY_REVIEW"
    """They disagree; a recorded review decided which governs."""


class ValueKind(StrEnum):
    """What sort of number a source printed.

    A limit is not an operating value: the RS-25 high-pressure oxidizer turbine's
    "maximum allowable ... approximately 30,000 rpm" (JSC-19041 §1.5.2) is a
    shutdown overspeed limit, and an operating speed of that turbopump is a
    different fact.
    """

    NOMINAL = "NOMINAL"
    RATED = "RATED"
    MAXIMUM = "MAXIMUM"
    """The top of a stated operating envelope (e.g. "Maximum Thrust (109% Power Level)")."""
    MINIMUM = "MINIMUM"
    """The bottom of a stated operating envelope (e.g. a minimum throttle point)."""
    LIMIT = "LIMIT"
    """A boundary the hardware must not reach in operation (overspeed, burst, proof)."""
    AVERAGE = "AVERAGE"
    PREDICTION = "PREDICTION"
    TEST_RESULT = "TEST_RESULT"
    DESIGN_VALUE = "DESIGN_VALUE"
    """A requirement or design goal, not a demonstrated or rated value."""
    APPROXIMATE = "APPROXIMATE"
    """The source itself qualifies the number ("approximately", "about")."""
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


#: Kinds that describe the engine running. LIMIT, PREDICTION, DESIGN_VALUE,
#: OTHER and UNKNOWN are deliberately not here.
OPERATING_VALUE_KINDS = frozenset({
    ValueKind.NOMINAL, ValueKind.RATED, ValueKind.MAXIMUM, ValueKind.MINIMUM,
    ValueKind.AVERAGE, ValueKind.TEST_RESULT, ValueKind.APPROXIMATE,
})


class Admissibility(StrEnum):
    """Whether a transcribed assertion is evidence about its subject."""

    ADMITTED = "ADMITTED"
    REJECTED_STALE_TEXT = "REJECTED_STALE_TEXT"
    """Printed, but contradicted for this subject (e.g. a later revision reprinting a superseded value)."""
    REJECTED_MODEL_PARAMETER = "REJECTED_MODEL_PARAMETER"
    """A tuning constant of a computer model, not a fact about hardware."""
    REJECTED_OTHER = "REJECTED_OTHER"


class Environment(StrEnum):
    SEA_LEVEL = "SEA_LEVEL"
    VACUUM = "VACUUM"
    ALTITUDE = "ALTITUDE"
    UNKNOWN = "UNKNOWN"
    """The source does not say."""


class PressureBasis(StrEnum):
    ABSOLUTE = "ABSOLUTE"
    GAUGE = "GAUGE"
    UNKNOWN = "UNKNOWN"
    """Unstated: printed "psi" without "a" or "g" is this."""


class PressureStation(StrEnum):
    """Where a chamber pressure is referenced. Published Pc values are not interchangeable."""

    NOZZLE_STAGNATION = "NOZZLE_STAGNATION"
    INJECTOR_FACE = "INJECTOR_FACE"
    CHAMBER_TAP = "CHAMBER_TAP"
    THROAT = "THROAT"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class IspBasis(StrEnum):
    ENGINE = "ENGINE"
    THRUST_CHAMBER = "THRUST_CHAMBER"
    UNKNOWN = "UNKNOWN"


class MixtureRatioBasis(StrEnum):
    """Which flow a mixture ratio describes."""

    ENGINE = "ENGINE"
    THRUST_CHAMBER = "THRUST_CHAMBER"
    GAS_GENERATOR = "GAS_GENERATOR"
    PREBURNER = "PREBURNER"
    UNKNOWN = "UNKNOWN"


class MixtureRatioForm(StrEnum):
    """Which way up the ratio is printed (the H-1 GG is given fuel-to-LOX)."""

    OXIDIZER_TO_FUEL = "OXIDIZER_TO_FUEL"
    FUEL_TO_OXIDIZER = "FUEL_TO_OXIDIZER"


class SubjectKind(StrEnum):
    """What an assertion, alias or lineage edge is about."""

    FAMILY = "FAMILY"
    VARIANT = "VARIANT"
    CONFIGURATION = "CONFIGURATION"
    OPERATING_POINT = "OPERATING_POINT"
    PROPULSION_UNIT = "PROPULSION_UNIT"
    COMPONENT = "COMPONENT"


class PropulsionUnitKind(StrEnum):
    """Things with engine-like names that are not engine variants."""

    ENGINE_MODULE = "ENGINE_MODULE"
    """A packaged group of engines sold or flown as one (YF-21 = four YF-20)."""

    PROPULSION_SYSTEM = "PROPULSION_SYSTEM"
    """A designation for an assembly of different engines (RD-0212 = RD-0213 + RD-0214)."""

    STAGE_PROPULSION = "STAGE_PROPULSION"
    """A stage's propulsion: engines plus stage-owned tanks, pressurisation, feed."""


class AliasKind(StrEnum):
    NATIVE = "NATIVE"
    TRANSLITERATION = "TRANSLITERATION"
    INDEX = "INDEX"
    MANUFACTURER = "MANUFACTURER"
    MILITARY = "MILITARY"
    EXPORT = "EXPORT"
    FORMER_NAME = "FORMER_NAME"
    INFORMAL = "INFORMAL"


class LineageKind(StrEnum):
    """A directed relation ``from -> to``, read "from is <kind> to"."""

    DERIVED_FROM = "DERIVED_FROM"
    UPRATE_OF = "UPRATE_OF"
    RENAMED_FROM = "RENAMED_FROM"
    LICENSED_FROM = "LICENSED_FROM"
    SUCCESSOR_OF = "SUCCESSOR_OF"
    MODULE_OF = "MODULE_OF"


class ConflictResolution(StrEnum):
    UNRESOLVED = "UNRESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    EXPLAINED = "EXPLAINED"
    """The claims differ for a stated reason (different configuration, epoch, ...); all stand."""
    RESOLVED = "RESOLVED"
    """One claim is shown to be the reliable one for the subject; the others stay recorded."""


class ConflictCategory(StrEnum):
    DIFFERENT_VARIANT = "DIFFERENT_VARIANT"
    DIFFERENT_CONFIGURATION = "DIFFERENT_CONFIGURATION"
    DIFFERENT_OPERATING_POINT = "DIFFERENT_OPERATING_POINT"
    DIFFERENT_EPOCH = "DIFFERENT_EPOCH"
    DIFFERENT_DEFINITION = "DIFFERENT_DEFINITION"
    DIFFERENT_MEASUREMENT_STATION = "DIFFERENT_MEASUREMENT_STATION"
    ROUNDING = "ROUNDING"
    UNIT_CONVERSION = "UNIT_CONVERSION"
    PRINTED_TYPO = "PRINTED_TYPO"
    OTHER = "OTHER"


class ComponentType(StrEnum):
    """Hardware identities a topology or an assertion can name.

    Typing only; facts about a component (stages, rich side, speed) are
    assertions about it, so a component never carries an unsourced attribute.
    """

    THRUST_CHAMBER = "THRUST_CHAMBER"
    COMBUSTION_CHAMBER = "COMBUSTION_CHAMBER"
    INJECTOR = "INJECTOR"
    NOZZLE = "NOZZLE"
    NOZZLE_EXTENSION = "NOZZLE_EXTENSION"
    COOLING_JACKET = "COOLING_JACKET"
    PUMP = "PUMP"
    BOOSTER_PUMP = "BOOSTER_PUMP"
    TURBINE = "TURBINE"
    HYDRAULIC_TURBINE = "HYDRAULIC_TURBINE"
    TURBOPUMP_ASSEMBLY = "TURBOPUMP_ASSEMBLY"
    SHAFT = "SHAFT"
    GEARBOX = "GEARBOX"
    GAS_GENERATOR = "GAS_GENERATOR"
    PREBURNER = "PREBURNER"
    HEAT_EXCHANGER = "HEAT_EXCHANGER"
    VALVE = "VALVE"
    REGULATOR = "REGULATOR"
    CHECK_VALVE = "CHECK_VALVE"
    ORIFICE = "ORIFICE"
    VENTURI = "VENTURI"
    MANIFOLD = "MANIFOLD"
    JUNCTION = "JUNCTION"
    IGNITER = "IGNITER"
    START_ENERGY_STORE = "START_ENERGY_STORE"
    TANK = "TANK"
    PRESSURANT_TANK = "PRESSURANT_TANK"
    ACCUMULATOR = "ACCUMULATOR"
    ACTUATOR = "ACTUATOR"
    HYDRAULIC_PUMP = "HYDRAULIC_PUMP"
    ELECTRIC_MOTOR = "ELECTRIC_MOTOR"
    ELECTRICAL_SOURCE = "ELECTRICAL_SOURCE"
    AMBIENT_SINK = "AMBIENT_SINK"
    INTERFACE_PORT = "INTERFACE_PORT"
    OTHER = "OTHER"


class Ownership(StrEnum):
    """Which assembly a component belongs to. Appearing in an engine schematic does not make it the engine's."""

    ENGINE = "ENGINE"
    STAGE = "STAGE"
    VEHICLE = "VEHICLE"
    AMBIENT = "AMBIENT"
    EXTERNAL = "EXTERNAL"
    """Installation or facility (test stand, ground support)."""
    UNKNOWN = "UNKNOWN"


class EdgeKind(StrEnum):
    """What a topology edge carries. Not every relation is plumbing."""

    FLUID_FLOW = "FLUID_FLOW"
    MECHANICAL_SHAFT = "MECHANICAL_SHAFT"
    """Common shaft (turbine to pump on the same shaft)."""
    GEARED_DRIVE = "GEARED_DRIVE"
    MECHANICAL_LINKAGE = "MECHANICAL_LINKAGE"
    """Valves ganged together, an actuator driving an injector sleeve."""
    ELECTRICAL_POWER = "ELECTRICAL_POWER"
    CONTROL_ACTUATION = "CONTROL_ACTUATION"
    """A control or actuation medium acting on a component (pneumatic, hydraulic signal)."""


#: Edges that carry a fluid must name it.
FLUID_EDGE_KINDS = frozenset({EdgeKind.FLUID_FLOW})

#: Edges that may name the medium they act through (GN2 to valve pistons on
#: the Shuttle OMS; RP-1 as hydraulic fluid on the F-1; a bus voltage).
#: Mechanical edges carry nothing and may not name a carrier.
MEDIUM_EDGE_KINDS = frozenset({EdgeKind.CONTROL_ACTUATION, EdgeKind.ELECTRICAL_POWER})


class TopologyEvidence(StrEnum):
    SHOWN_IN_SCHEMATIC = "SHOWN_IN_SCHEMATIC"
    REPORTED_IN_TEXT = "REPORTED_IN_TEXT"
    DERIVED_FROM_BOTH = "DERIVED_FROM_BOTH"
    INFERRED = "INFERRED"


class SchematicProvenance(StrEnum):
    """Who drew a schematic (or built a graph)."""

    ORIGINAL_MANUFACTURER = "ORIGINAL_MANUFACTURER"
    ORIGINAL_AGENCY = "ORIGINAL_AGENCY"
    ORIGINAL_CONTRACTOR = "ORIGINAL_CONTRACTOR"
    THIRD_PARTY_RECONSTRUCTION = "THIRD_PARTY_RECONSTRUCTION"
    """Drawn by someone outside the programme from indirect evidence (photographs, displays)."""
    ROCKETFORGE_DERIVED_GRAPH = "ROCKETFORGE_DERIVED_GRAPH"
    """A graph RocketForge built from schematics and text; its basis is the schematics' provenance."""
    UNKNOWN = "UNKNOWN"


#: Provenances that count as an original drawing of the hardware.
ORIGINAL_PROVENANCES = frozenset({
    SchematicProvenance.ORIGINAL_MANUFACTURER, SchematicProvenance.ORIGINAL_AGENCY,
    SchematicProvenance.ORIGINAL_CONTRACTOR,
})
