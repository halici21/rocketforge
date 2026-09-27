"""Evidence records: sources, propellant formulations as a source states them, and
what each record can support.

These types describe the world; they compute nothing. A
:class:`PropellantReference` says what a source printed about a grain -- it is
not a :class:`~rocketforge.physics.solid_propellant.SolidFormulation`, and
nothing here builds one. Turning evidence into something a provider can solve
is a separate, later step with its own checks, and keeping it out of this
package is what lets evidence be browsed without anything being solved.

Two rules are enforced on construction because a record that breaks them is not
evidence:

* every :class:`~.values.ReportedValue` names a source the record declares;
* a record that is regression-locked in any dimension names the comparison case
  that locks it.

A third, the shipping rule, needs the source registry and is checked by
:func:`validate_against_sources`.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from .values import (
    AccessClass,
    Datum,
    Dimension,
    EvidenceError,
    EvidenceStatus,
    Missing,
    ReportedValue,
    ShippingPolicy,
)

__all__ = [
    "RecordKind",
    "SourceReference",
    "CustomDefinition",
    "IngredientReference",
    "PropellantReference",
    "EvidenceRecord",
    "MASS_FRACTION_BASIS",
    "reported_values",
    "validate_against_sources",
]

#: The only formulation basis schema version 1 records. Mass fraction is what
#: the solid chamber path consumes; a percent is a presentation of it.
MASS_FRACTION_BASIS = "mass_fraction"


class RecordKind(StrEnum):
    """What a record is about."""

    PROPELLANT = "PROPELLANT"
    """A propellant formulation as a source states it."""

    REFERENCE = "REFERENCE"
    """A source-level reference with no formulation (e.g. an operational motor)."""


def _text(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(f"{what} must be a non-empty string, got {value!r}")
    return value


def _texts(values: object, what: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise EvidenceError(f"{what} must be a tuple of strings, got {type(values).__name__}")
    for item in values:
        _text(item, f"each entry of {what}")
    if not allow_empty and not values:
        raise EvidenceError(f"{what} must not be empty")
    if len(set(values)) != len(values):
        raise EvidenceError(f"{what} contains a duplicate")
    return values


def _datum(value: object, what: str) -> None:
    if not isinstance(value, (ReportedValue, Missing)):
        raise EvidenceError(
            f"{what} must be a ReportedValue or an explicit Missing, got {value!r}. "
            "A field with no value states why; it is never simply left out.")


@dataclass(frozen=True, slots=True)
class SourceReference:
    """A document, program or page that evidence is taken from.

    Attributes:
        source_id: Stable identifier (``"S-NASA-RP1311-P2-1996"``). Values cite it.
        organization, authors, title, year: Bibliographic identity. ``year`` is
            ``None`` when the source does not state one.
        identifiers: Report numbers, DOIs, accession numbers, keyed by kind.
        locator: A canonical URL or equivalent.
        source_type: What kind of document it is, in words.
        access_class: How a reader can obtain it.
        rights_statement: Rights as the source or its repository states them.
            Not inferred: an unstated right is recorded as unstated.
        shipping: What RocketForge may distribute from it.
        tier: 1 primary, 2 strong secondary (e.g. an author's own test page),
            3 discovery only.
    """

    source_id: str
    organization: str
    authors: tuple[str, ...]
    title: str
    year: int | None
    identifiers: Mapping[str, str]
    locator: str
    source_type: str
    access_class: AccessClass
    rights_statement: str
    shipping: ShippingPolicy
    tier: int

    def __post_init__(self) -> None:
        for name in ("source_id", "organization", "title", "locator",
                     "source_type", "rights_statement"):
            _text(getattr(self, name), name)
        _texts(self.authors, "authors")
        if self.year is not None and (isinstance(self.year, bool)
                                      or not isinstance(self.year, int)):
            raise EvidenceError(f"year must be an integer or None, got {self.year!r}")
        if not isinstance(self.identifiers, Mapping):
            raise EvidenceError("identifiers must be a mapping of strings")
        for key, value in self.identifiers.items():
            _text(key, "identifier kind")
            _text(value, f"identifier {key!r}")
        object.__setattr__(self, "identifiers", MappingProxyType(dict(self.identifiers)))
        if not isinstance(self.access_class, AccessClass):
            raise EvidenceError(f"access_class must be an AccessClass, got {self.access_class!r}")
        if not isinstance(self.shipping, ShippingPolicy):
            raise EvidenceError(f"shipping must be a ShippingPolicy, got {self.shipping!r}")
        if self.tier not in (1, 2, 3) or isinstance(self.tier, bool):
            raise EvidenceError(f"tier must be 1, 2 or 3, got {self.tier!r}")

    @property
    def values_may_ship(self) -> bool:
        """Whether a shipped record may carry values taken from this source."""
        return self.shipping is ShippingPolicy.VALUES_WITH_ATTRIBUTION


@dataclass(frozen=True, slots=True)
class CustomDefinition:
    """What a source states to define an ingredient that is not a library species.

    Mirrors what an assigned-enthalpy reactant needs -- formula, enthalpy with
    its units, reference temperature, and a molecular weight when the source
    gives one -- but each part is a sourced datum, so a definition the source
    leaves incomplete stays visibly incomplete instead of being filled in.

    Attributes:
        formula: Element -> atoms per formula unit, each a reported value; or
            :class:`~.values.Missing` when the source gives no formula.
        enthalpy: The assigned enthalpy (heat of formation), with its unit as
            printed on the value.
        reference_temperature: The temperature that enthalpy belongs to.
        molecular_weight: Per formula unit, when stated.
    """

    formula: Mapping[str, ReportedValue] | Missing
    enthalpy: Datum
    reference_temperature: Datum
    molecular_weight: Datum

    def __post_init__(self) -> None:
        if isinstance(self.formula, Mapping):
            if not self.formula:
                raise EvidenceError(
                    "a stated formula must name at least one element; use Missing "
                    "when the source gives none")
            for element, count in self.formula.items():
                _text(element, "element symbol")
                if not isinstance(count, ReportedValue):
                    raise EvidenceError(
                        f"atom count for {element!r} must be a ReportedValue, got {count!r}")
            object.__setattr__(self, "formula", MappingProxyType(dict(self.formula)))
        elif not isinstance(self.formula, Missing):
            raise EvidenceError(
                "formula must be a mapping of reported atom counts or Missing, "
                f"got {self.formula!r}")
        _datum(self.enthalpy, "enthalpy")
        _datum(self.reference_temperature, "reference_temperature")
        _datum(self.molecular_weight, "molecular_weight")

    def reported_values(self) -> Iterator[ReportedValue]:
        if isinstance(self.formula, Mapping):
            yield from self.formula.values()
        for datum in (self.enthalpy, self.reference_temperature, self.molecular_weight):
            if isinstance(datum, ReportedValue):
                yield datum


@dataclass(frozen=True, slots=True)
class IngredientReference:
    """One ingredient as a source names it.

    Attributes:
        source_name: The name exactly as the source prints it.
        fraction: Its share of the formulation on the propellant's basis.
        provider_name: The provider's spelling of the same ingredient
            (``"NH4CLO4(I)"``), when it has been reviewed and recorded. Data,
            not a lookup: no synonym or phase is ever chosen automatically.
        custom: The source's definition, for an ingredient that is not a
            library species.
    """

    source_name: str
    fraction: Datum
    provider_name: str | None = None
    custom: CustomDefinition | None = None

    def __post_init__(self) -> None:
        _text(self.source_name, "source_name")
        _datum(self.fraction, f"fraction of {self.source_name!r}")
        if self.provider_name is not None:
            _text(self.provider_name, "provider_name")
        if self.custom is not None and not isinstance(self.custom, CustomDefinition):
            raise EvidenceError(f"custom must be a CustomDefinition or None, got {self.custom!r}")

    def reported_values(self) -> Iterator[ReportedValue]:
        if isinstance(self.fraction, ReportedValue):
            yield self.fraction
        if self.custom is not None:
            yield from self.custom.reported_values()


@dataclass(frozen=True, slots=True)
class PropellantReference:
    """A propellant formulation exactly as its sources state it.

    Fractions are held as printed. Whether they close, and whether the
    formulation can be posed to a provider, is judged later and elsewhere;
    nothing here normalises, completes or substitutes.

    Attributes:
        propellant_id: Stable identifier.
        source_ids: The sources the formulation is taken from.
        family: A short descriptive family (``"AP / custom binder / Al"``).
        source_name: What the source calls the propellant.
        exact_formulation: True only when the source gives every ingredient's
            fraction; then every fraction must be a reported value.
        basis: The fraction basis; ``"mass_fraction"`` in schema version 1.
        ingredients: In the source's order.
        density: As stated, or Missing.
        initial_temperature: The grain/reactant temperature the source states.
    """

    propellant_id: str
    source_ids: tuple[str, ...]
    family: str
    source_name: str
    exact_formulation: bool
    basis: str
    ingredients: tuple[IngredientReference, ...]
    density: Datum
    initial_temperature: Datum

    def __post_init__(self) -> None:
        for name in ("propellant_id", "family", "source_name"):
            _text(getattr(self, name), name)
        _texts(self.source_ids, "source_ids", allow_empty=False)
        if not isinstance(self.exact_formulation, bool):
            raise EvidenceError("exact_formulation must be a bool")
        if self.basis != MASS_FRACTION_BASIS:
            raise EvidenceError(
                f"basis must be {MASS_FRACTION_BASIS!r} in schema version 1, got {self.basis!r}")
        if not isinstance(self.ingredients, tuple) or not self.ingredients:
            raise EvidenceError("ingredients must be a non-empty tuple")
        names = []
        for item in self.ingredients:
            if not isinstance(item, IngredientReference):
                raise EvidenceError(
                    f"every ingredient must be an IngredientReference, got {item!r}")
            names.append(item.source_name)
        if len(set(names)) != len(names):
            raise EvidenceError("an ingredient is listed twice")
        if self.exact_formulation and any(
                not isinstance(item.fraction, ReportedValue) for item in self.ingredients):
            raise EvidenceError(
                "an exact formulation needs every ingredient fraction reported; an "
                "ingredient with a Missing fraction makes it inexact")
        _datum(self.density, "density")
        _datum(self.initial_temperature, "initial_temperature")

    def reported_values(self) -> Iterator[ReportedValue]:
        for item in self.ingredients:
            yield from item.reported_values()
        for datum in (self.density, self.initial_temperature):
            if isinstance(datum, ReportedValue):
                yield datum


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """One dataset: what its sources say, and what it can support per dimension.

    Attributes:
        record_id: Stable identifier (``"DS-RP1311-E5"``).
        title: Human-facing name.
        kind: :class:`RecordKind`.
        source_ids: Every source the record draws on.
        capabilities: Status in each of VA, VB, VC and VD -- all four, always.
        capability_notes: Why, per dimension, where a reason helps.
        propellant: The formulation, for a propellant record.
        comparison_case_ids: ``ReferenceCase.case_id`` values in
            ``rocketforge.comparison`` that compare against this record.
        executable_key: The key of an executable formulation this record
            documents (``"rp1311-example5"``), when one exists. The executable
            formulation stays the authority for execution.
        blockers: What prevents further use, in words.
        notes: Anything else a reader needs.
    """

    record_id: str
    title: str
    kind: RecordKind
    source_ids: tuple[str, ...]
    capabilities: Mapping[Dimension, EvidenceStatus]
    capability_notes: Mapping[Dimension, str]
    propellant: PropellantReference | None
    comparison_case_ids: tuple[str, ...]
    executable_key: str | None
    blockers: tuple[str, ...]
    notes: str

    def __post_init__(self) -> None:
        _text(self.record_id, "record_id")
        _text(self.title, "title")
        if not isinstance(self.kind, RecordKind):
            raise EvidenceError(f"kind must be a RecordKind, got {self.kind!r}")
        _texts(self.source_ids, "source_ids", allow_empty=False)

        if not isinstance(self.capabilities, Mapping):
            raise EvidenceError("capabilities must be a mapping of Dimension to EvidenceStatus")
        if set(self.capabilities) != set(Dimension):
            raise EvidenceError(
                f"capabilities must state every dimension {[d.value for d in Dimension]}, "
                f"got {sorted(str(d) for d in self.capabilities)}")
        for dimension, status in self.capabilities.items():
            if not isinstance(dimension, Dimension) or not isinstance(status, EvidenceStatus):
                raise EvidenceError(f"capability {dimension!r}: {status!r} is not a status")
        object.__setattr__(self, "capabilities",
                           MappingProxyType({d: self.capabilities[d] for d in Dimension}))
        if not isinstance(self.capability_notes, Mapping):
            raise EvidenceError("capability_notes must be a mapping")
        for dimension, note in self.capability_notes.items():
            if not isinstance(dimension, Dimension):
                raise EvidenceError(f"capability note key {dimension!r} is not a Dimension")
            _text(note, f"capability note for {dimension}")
        object.__setattr__(self, "capability_notes", MappingProxyType(
            {d: self.capability_notes[d] for d in Dimension if d in self.capability_notes}))

        if self.kind is RecordKind.PROPELLANT and self.propellant is None:
            raise EvidenceError("a propellant record needs its propellant")
        if self.propellant is not None:
            if not isinstance(self.propellant, PropellantReference):
                raise EvidenceError(
                    f"propellant must be a PropellantReference or None, got {self.propellant!r}")
            undeclared = set(self.propellant.source_ids) - set(self.source_ids)
            if undeclared:
                raise EvidenceError(
                    f"propellant cites sources the record does not declare: {sorted(undeclared)}")

        _texts(self.comparison_case_ids, "comparison_case_ids")
        locked = [d for d, s in self.capabilities.items()
                  if s is EvidenceStatus.REGRESSION_LOCKED]
        if locked and not self.comparison_case_ids:
            raise EvidenceError(
                f"{self.record_id} is regression-locked in {[d.value for d in locked]} "
                "but names no comparison case that locks it")
        if self.executable_key is not None:
            _text(self.executable_key, "executable_key")
            if self.propellant is None:
                raise EvidenceError("an executable key documents a propellant; none is given")
        _texts(self.blockers, "blockers")
        if not isinstance(self.notes, str):
            raise EvidenceError("notes must be a string")

        for value in reported_values(self):
            if value.source_id not in self.source_ids:
                raise EvidenceError(
                    f"{self.record_id}: a value cites {value.source_id!r}, which the "
                    f"record does not declare (declared: {list(self.source_ids)})")


def reported_values(record: EvidenceRecord) -> tuple[ReportedValue, ...]:
    """Every reported value in a record, in a stable order."""
    if record.propellant is None:
        return ()
    return tuple(record.propellant.reported_values())


def validate_against_sources(record: EvidenceRecord,
                             sources: Mapping[str, SourceReference]) -> None:
    """Check a record against the source registry it will ship with.

    Every declared source must exist, and a value may be shipped only from a
    source whose policy allows values. A metadata-only, restricted, licensed or
    rights-pending source can be cited by a record, never quoted in it.
    """
    unknown = [sid for sid in record.source_ids if sid not in sources]
    if unknown:
        raise EvidenceError(f"{record.record_id}: unknown sources {unknown}")
    for value in reported_values(record):
        source = sources[value.source_id]
        if not source.values_may_ship:
            raise EvidenceError(
                f"{record.record_id}: a value is taken from {source.source_id}, whose "
                f"shipping policy is {source.shipping.value}; only metadata from it may ship")
