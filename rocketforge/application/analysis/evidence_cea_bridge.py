"""Evidence to NASA CEA: can a recorded formulation be posed to the installed provider?

Gate D of the propulsion knowledge blueprint (R1 ``integration_blueprint.md``
section 4), as one function, :func:`assess`, which runs only when a person asks
for it. It reads an EV-1 evidence record exactly as stored, asks the installed
``thermo.lib`` -- through the provider gateway, never the provider package --
whether each library name the record cites is there, and builds the physics
formulation only when nothing blocks it. It solves nothing: no chamber state,
no c*, no provider solve of any kind.

The steps, in R1's order:

1. **Record gate.** No propellant, or VA not applicable: ``NOT_A_CEA_TARGET``.
   Pure evidence data; nothing is probed.
2. **Access gate** (:func:`access_gate`), separate from the assessment. A
   value the source states but this build withholds (``Missing(WITHHELD_RIGHTS)``)
   stops the check here: the answer carries an :class:`AccessDecision` naming
   each withheld datum, its scientific ``state`` is ``None`` -- not evaluated --
   and it holds no scientific blocker. Nothing is probed, nothing is solved,
   and nothing is said about the chemistry.
3. **Structure.** An exact formulation; every fraction reported, as a mass
   fraction; the stored fractions summing to one within the physics layer's own
   ``MASS_FRACTION_SUM_TOL``; a reported grain temperature. Otherwise
   ``UNDERDEFINED``. Nothing is normalised, completed or defaulted.
4. **Ingredients.** A provider name is probed verbatim; absent from this
   ``thermo.lib`` it is ``LIBRARY_SPECIES_ABSENT``, naming the name and the
   database hash. A source definition needs formula, enthalpy with its units and
   reference temperature, all reported; any missing is
   ``CUSTOM_THERMO_INCOMPLETE`` naming the field (``BLOCKED_INCOMPLETE_CUSTOM``).
   An ingredient with neither is ``UNDERDEFINED``.
5. **Build.** ``CustomReactant`` / ``SolidIngredient`` / ``SolidFormulation``,
   which re-validate. ``EXECUTABLE_VERIFIED`` when VA is regression-locked,
   else ``EXECUTABLE_SOURCE_COMPLETE``; ``PROVIDER_UNAVAILABLE`` when no
   provider could be asked, which is not a block.

Library names are probed once per process per ``thermo.lib`` identity (the
gateway's :func:`~.thermochemistry_provider.probe_solid_library_species`):
the answer is a fact about one database, which cannot change while the process
holds it. Only the name lookups are reused -- never an assessment, never a
record's answer. The normative statement of both rules is
``docs/engineering/EVIDENCE_CEA_COMPATIBILITY_CONTRACT.md``.

What it never does: substitute a surrogate for a binder (no HTPB, PBAN or GAP
stand-in), choose a phase or synonym for a name (``KNO3(cr)`` is not tried as
``KNO3(a)``), normalise fractions, read a ``Missing`` as zero, drop an
ingredient, convert a unit, or solve.

"Open in Thermochemistry" does not run from here either. An executable record
names a Thermochemistry case through ``executable_key``; :func:`assess` checks
that the formulation built from the evidence equals that case field for field,
and the case itself -- the provider constant -- stays the executable authority.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from rocketforge.evidence import (
    CustomDefinition,
    Datum,
    Dimension,
    EvidenceRecord,
    EvidenceStatus,
    Missing,
    MissingReason,
    PropellantReference,
    ReportedValue,
    SourceReference,
)
from rocketforge.physics.solid_propellant import (
    MASS_FRACTION_SUM_TOL,
    CustomReactant,
    SolidFormulation,
    SolidIngredient,
)
from rocketforge.physics.thermochemistry.errors import ThermochemistryError

from . import propulsion_evidence_service as evidence_service
from . import thermochemistry_provider as gateway

__all__ = [
    "CompatibilityState",
    "Blocker",
    "CompatibilityAssessment",
    "AccessRestriction",
    "AccessDecision",
    "access_gate",
    "access_rows",
    "assess",
    "formulation_differences",
    "blocker_rows",
    "identity_text",
    "MASS_FRACTION_UNIT",
]

#: The only fraction unit a schema-version-1 record's mass-fraction basis means.
MASS_FRACTION_UNIT = "mass fraction"

#: Temperatures are handed to CEA in kelvin; a temperature printed in another
#: unit is refused, never converted here.
_KELVIN = "K"

#: Molecular weight as CEA takes it. kg/kmol is numerically the same quantity.
_MOLECULAR_WEIGHT_UNITS = ("g/mol", "kg/kmol")


class CompatibilityState(StrEnum):
    """R1 section 4's answer, one per record, when someone asked."""

    NOT_A_CEA_TARGET = "NOT_A_CEA_TARGET"
    UNDERDEFINED = "UNDERDEFINED"
    BLOCKED_INCOMPLETE_CUSTOM = "BLOCKED_INCOMPLETE_CUSTOM"
    BLOCKED = "BLOCKED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    EXECUTABLE_VERIFIED = "EXECUTABLE_VERIFIED"
    EXECUTABLE_SOURCE_COMPLETE = "EXECUTABLE_SOURCE_COMPLETE"


EXECUTABLE_STATES = frozenset({CompatibilityState.EXECUTABLE_VERIFIED,
                               CompatibilityState.EXECUTABLE_SOURCE_COMPLETE})

# blocker codes, grouped by the state they put a record in (first match wins)
NOT_EXACT_FORMULATION = "NOT_EXACT_FORMULATION"
VALUE_MISSING = "VALUE_MISSING"
MASS_FRACTION_SUM = "MASS_FRACTION_SUM"
NO_THERMO_DEFINITION = "NO_THERMO_DEFINITION"
AMBIGUOUS_THERMO_DEFINITION = "AMBIGUOUS_THERMO_DEFINITION"
CUSTOM_THERMO_INCOMPLETE = "CUSTOM_THERMO_INCOMPLETE"
LIBRARY_SPECIES_ABSENT = "LIBRARY_SPECIES_ABSENT"
UNIT_NOT_ACCEPTED = "UNIT_NOT_ACCEPTED"
PHYSICS_REFUSED = "PHYSICS_REFUSED"

#: The access gate's one restriction code: EV-1's own ``MissingReason`` value.
#: It is not a :class:`CompatibilityState` and never a :class:`Blocker` code.
WITHHELD_RIGHTS = "WITHHELD_RIGHTS"

_STATE_OF_CODE = {
    NOT_EXACT_FORMULATION: CompatibilityState.UNDERDEFINED,
    VALUE_MISSING: CompatibilityState.UNDERDEFINED,
    MASS_FRACTION_SUM: CompatibilityState.UNDERDEFINED,
    NO_THERMO_DEFINITION: CompatibilityState.UNDERDEFINED,
    AMBIGUOUS_THERMO_DEFINITION: CompatibilityState.UNDERDEFINED,
    CUSTOM_THERMO_INCOMPLETE: CompatibilityState.BLOCKED_INCOMPLETE_CUSTOM,
    LIBRARY_SPECIES_ABSENT: CompatibilityState.BLOCKED,
    UNIT_NOT_ACCEPTED: CompatibilityState.BLOCKED,
    PHYSICS_REFUSED: CompatibilityState.BLOCKED,
}
_STATE_ORDER = (CompatibilityState.UNDERDEFINED,
                CompatibilityState.BLOCKED_INCOMPLETE_CUSTOM,
                CompatibilityState.BLOCKED)


@dataclass(frozen=True, slots=True)
class Blocker:
    """One named reason a record cannot be posed to NASA CEA as it stands.

    Attributes:
        code: What kind of reason (``LIBRARY_SPECIES_ABSENT``, ...).
        detail: The reason in words, naming what it is about.
        category: ``evidence`` (what the source states), ``library`` (what
            the probed ``thermo.lib`` holds) or ``physics`` (what the
            formulation types accept). Never rights: an access restriction is
            the access gate's, not a blocker.
        field: The datum path it concerns, as the evidence service names it
            (``ingredients[1].custom.enthalpy``), when it concerns one.
        ingredient: The ingredient, as the source names it.
        name: The provider name probed, for a library blocker.
        database_sha256: The probed ``thermo.lib`` hash, for a library blocker.
    """

    code: str
    detail: str
    category: str = "evidence"
    field: str = ""
    ingredient: str = ""
    name: str = ""
    database_sha256: str = ""


@dataclass(frozen=True, slots=True)
class AccessRestriction:
    """One datum the check needs that this build does not ship.

    Attributes:
        code: ``WITHHELD_RIGHTS`` (EV-1's ``MissingReason``).
        detail: The restriction in words, naming the datum.
        field: The datum path, as the evidence service names it.
        ingredient: The ingredient, as the source names it.
        policies: The cited sources that withhold values, with their policy.
    """

    code: str
    detail: str
    field: str = ""
    ingredient: str = ""
    policies: str = ""


@dataclass(frozen=True, slots=True)
class AccessDecision:
    """The access gate's answer: may the check use this record's values at all."""

    permitted: bool
    restrictions: tuple[AccessRestriction, ...] = ()


@dataclass(frozen=True, slots=True)
class CompatibilityAssessment:
    """The answer for one record, and everything it rests on.

    Attributes:
        record_id: The record it answers for. An answer is never shown for
            another record.
        state: :class:`CompatibilityState`, or ``None`` when the access gate
            stopped the check and compatibility was not evaluated.
        blockers: Every named scientific reason, in record order. Empty when
            executable, not a target, not evaluated, or when only the provider
            was missing.
        access: The access gate's decision, when the gate ran (every target
            record); ``None`` for a record that is not a CEA target.
        probe: The gateway's :class:`~.thermochemistry_provider.LibrarySpeciesProbe`
            -- which provider, library version and ``thermo.lib`` hash answered
            -- or ``None`` when nothing was probed.
        formulation: The physics formulation built from the evidence, only in
            an executable state.
        notes: What the answer assumes that a reader should know.
        thermochemistry_key: The Thermochemistry case the formulation equals
            field for field, when there is one; the only thing "Open in
            Thermochemistry" may load.
        thermochemistry_note: Why there is none, for an executable record.
    """

    record_id: str
    state: CompatibilityState | None
    blockers: tuple[Blocker, ...] = ()
    probe: Any = None
    formulation: SolidFormulation | None = None
    notes: tuple[str, ...] = ()
    thermochemistry_key: str | None = None
    thermochemistry_note: str = ""
    access: AccessDecision | None = None

    @property
    def evaluated(self) -> bool:
        """Scientific compatibility was assessed (the access gate let it through)."""
        return self.state is not None

    @property
    def executable(self) -> bool:
        return self.state in EXECUTABLE_STATES


# ------------------------------------------------------------------ helpers


def _fraction_path(index: int) -> str:
    return f"ingredients[{index}].fraction"


def _custom_path(index: int, part: str) -> str:
    return f"ingredients[{index}].custom.{part}"


def _custom_data(custom: CustomDefinition) -> tuple[tuple[str, Datum], ...]:
    """The four parts of a source definition, the formula as one datum when missing."""
    formula: Datum
    if isinstance(custom.formula, Missing):
        formula = custom.formula
    else:
        formula = next(iter(custom.formula.values()))      # reported; never Missing
    return (("formula", formula), ("enthalpy", custom.enthalpy),
            ("reference_temperature", custom.reference_temperature),
            ("molecular_weight", custom.molecular_weight))


def _thermo_data(propellant: PropellantReference) -> Iterable[tuple[str, str, str, Datum]]:
    """(path, ingredient, label, datum) for every value a CEA input would need."""
    for index, item in enumerate(propellant.ingredients):
        yield _fraction_path(index), item.source_name, f"{item.source_name} · fraction", \
            item.fraction
        if item.custom is not None:
            for part, datum in _custom_data(item.custom):
                yield (_custom_path(index, part), item.source_name,
                       f"{item.source_name} · {part.replace('_', ' ')}", datum)
    yield "initial_temperature", "", "Initial temperature", propellant.initial_temperature


def _withholding_policies(record: EvidenceRecord,
                          sources: Mapping[str, SourceReference] | None) -> str:
    if not sources:
        return ""
    held = [f"{sid} {sources[sid].shipping.value}" for sid in record.source_ids
            if sid in sources and not sources[sid].values_may_ship]
    return "; ".join(held)


# ------------------------------------------------------------------ the gates


def access_gate(record: EvidenceRecord,
                sources: Mapping[str, SourceReference] | None = None) -> AccessDecision:
    """May the check use this record's values? Pure evidence data; asks no provider.

    Refused when any datum the assessment needs is ``Missing(WITHHELD_RIGHTS)``:
    the source states it, and this build does not ship it. That is a limit on
    what ships, not a finding about the chemistry, so it is never turned into a
    scientific blocker.
    """
    if record.propellant is None:
        return AccessDecision(True)
    policies = _withholding_policies(record, sources)
    where = f" (cited sources that withhold values: {policies})" if policies else ""
    out = []
    for path, ingredient, label, datum in _thermo_data(record.propellant):
        if isinstance(datum, Missing) and datum.reason is MissingReason.WITHHELD_RIGHTS:
            out.append(AccessRestriction(
                WITHHELD_RIGHTS,
                f"{label}: the source states it, and this build withholds it by shipping "
                f"policy{where}.",
                field=path, ingredient=ingredient, policies=policies))
    return AccessDecision(not out, tuple(out))


def _structural_blockers(propellant: PropellantReference) -> list[Blocker]:
    out = []
    if not propellant.exact_formulation:
        out.append(Blocker(
            NOT_EXACT_FORMULATION,
            "The source does not give an exact formulation. Nothing is completed, "
            "estimated or normalised to make one."))
    fractions = []
    for index, item in enumerate(propellant.ingredients):
        datum, path = item.fraction, _fraction_path(index)
        if isinstance(datum, Missing):
            out.append(Blocker(
                VALUE_MISSING,
                f"{item.source_name} · fraction: Missing · {datum.reason.value}"
                + (f" ({datum.note})" if datum.note else "")
                + ". It is not read as zero and the ingredient is not dropped.",
                field=path, ingredient=item.source_name))
        elif datum.unit != MASS_FRACTION_UNIT:
            out.append(Blocker(
                UNIT_NOT_ACCEPTED,
                f"{item.source_name} · fraction is printed in {datum.unit!r}, not "
                f"{MASS_FRACTION_UNIT!r}. It is not converted.",
                field=path, ingredient=item.source_name))
        else:
            fractions.append(datum.value)
    if len(fractions) == len(propellant.ingredients):
        total = math.fsum(fractions)
        if abs(total - 1.0) > MASS_FRACTION_SUM_TOL:
            out.append(Blocker(
                MASS_FRACTION_SUM,
                f"The stored mass fractions sum to {total!r}, not 1 within "
                f"{MASS_FRACTION_SUM_TOL:g} (off by {total - 1.0:+.3e}). Refused, not "
                "normalised: a formulation that does not close is more often a missing "
                "ingredient than a deliberate basis."))
    temperature = propellant.initial_temperature
    if isinstance(temperature, Missing):
        out.append(Blocker(
            VALUE_MISSING,
            f"Initial temperature: Missing · {temperature.reason.value}. No grain "
            "temperature is assumed in its place.",
            field="initial_temperature"))
    elif temperature.unit != _KELVIN:
        out.append(Blocker(
            UNIT_NOT_ACCEPTED,
            f"Initial temperature is printed in {temperature.unit!r}, not K. It is not "
            "converted.", field="initial_temperature"))
    return out


def _definition_blockers(propellant: PropellantReference) -> list[Blocker]:
    out = []
    for index, item in enumerate(propellant.ingredients):
        name = item.source_name
        if item.provider_name is not None and item.custom is not None:
            out.append(Blocker(
                AMBIGUOUS_THERMO_DEFINITION,
                f"{name}: both a provider name ({item.provider_name}) and a source "
                "definition are recorded. Neither is chosen automatically.",
                ingredient=name))
            continue
        if item.provider_name is None and item.custom is None:
            out.append(Blocker(
                NO_THERMO_DEFINITION,
                f"{name}: no reviewed provider name and no source definition. No library "
                "species or surrogate is substituted for it.",
                ingredient=name))
            continue
        if item.custom is None:
            continue
        for part, datum in _custom_data(item.custom):
            path = _custom_path(index, part)
            if isinstance(datum, Missing):
                if part == "molecular_weight":
                    continue                 # optional: CEA derives it (noted on build)
                out.append(Blocker(
                    CUSTOM_THERMO_INCOMPLETE,
                    f"{name}: {part.replace('_', ' ')} is Missing · {datum.reason.value}. "
                    "A source-defined ingredient needs its formula, its enthalpy with "
                    "units and its reference temperature.",
                    field=path, ingredient=name))
            elif part == "reference_temperature" and datum.unit != _KELVIN:
                out.append(Blocker(
                    UNIT_NOT_ACCEPTED,
                    f"{name}: reference temperature is printed in {datum.unit!r}, not K. "
                    "It is not converted.", field=path, ingredient=name))
            elif part == "molecular_weight" and datum.unit not in _MOLECULAR_WEIGHT_UNITS:
                out.append(Blocker(
                    UNIT_NOT_ACCEPTED,
                    f"{name}: molecular weight is printed in {datum.unit!r}, not g/mol. "
                    "It is not converted.", field=path, ingredient=name))
    return out


def _library_blockers(propellant: PropellantReference, probe: Any) -> list[Blocker]:
    if not probe.usable:
        return []
    out = []
    for item in propellant.ingredients:
        if item.custom is None and item.provider_name in probe.absent:
            out.append(Blocker(
                LIBRARY_SPECIES_ABSENT,
                f"{item.source_name}: {item.provider_name!r} is not in the installed "
                f"{probe.database or 'thermo.lib'} (sha256 {probe.database_sha256}). No "
                "other name, phase or synonym is tried in its place.",
                category="library", ingredient=item.source_name,
                name=item.provider_name, database_sha256=probe.database_sha256))
    return out


def _state_of(blockers: Iterable[Blocker]) -> CompatibilityState | None:
    states = {_STATE_OF_CODE[b.code] for b in blockers}
    for state in _STATE_ORDER:
        if state in states:
            return state
    return None


# ------------------------------------------------------------------- build


def _custom_source(record: EvidenceRecord, custom: CustomDefinition) -> str:
    enthalpy = custom.enthalpy
    return (f"Evidence record {record.record_id}: {enthalpy.source_id}, "
            f"{enthalpy.locator}")


def _build(record: EvidenceRecord) -> SolidFormulation:
    """The physics formulation, from reported values only. Physics re-validates."""
    propellant = record.propellant
    ingredients = []
    for item in propellant.ingredients:
        if item.custom is None:
            ingredients.append(SolidIngredient(item.provider_name, item.fraction.value))
            continue
        custom = item.custom
        weight = custom.molecular_weight
        ingredients.append(SolidIngredient(item.source_name, item.fraction.value,
                                           custom=CustomReactant(
            formula={element: count.value for element, count in custom.formula.items()},
            heat_of_formation=custom.enthalpy.value,
            heat_of_formation_units=custom.enthalpy.unit,
            reference_temperature=custom.reference_temperature.value,
            source=_custom_source(record, custom),
            molecular_weight=weight.value if isinstance(weight, ReportedValue) else None)))
    return SolidFormulation(name=propellant.source_name, ingredients=tuple(ingredients),
                            initial_temperature=propellant.initial_temperature.value,
                            reference=f"evidence record {record.record_id}")


def _build_notes(propellant: PropellantReference) -> tuple[str, ...]:
    notes = []
    for item in propellant.ingredients:
        if item.custom is not None and isinstance(item.custom.molecular_weight, Missing):
            notes.append(
                f"{item.source_name}: the source states no molecular weight "
                f"({item.custom.molecular_weight.reason.value}); NASA CEA would derive it "
                "from the formula.")
    return tuple(notes)


def formulation_differences(ours: SolidFormulation, theirs: SolidFormulation) -> tuple[str, ...]:
    """Every scientific field in which two formulations differ; empty when equal.

    Compares what a solve consumes -- ingredient order, names, mass fractions,
    each custom reactant's formula, enthalpy and its units, reference
    temperature and molecular weight, and the grain temperature -- exactly, with
    no tolerance. Names, references and source strings are provenance text and
    are not compared.
    """
    out = []
    if ours.names != theirs.names:
        return (f"ingredients {list(ours.names)} differ from {list(theirs.names)}",)
    for mine, other in zip(ours.ingredients, theirs.ingredients):
        if mine.mass_fraction != other.mass_fraction:
            out.append(f"{mine.name} mass fraction {mine.mass_fraction!r} vs "
                       f"{other.mass_fraction!r}")
        if (mine.custom is None) != (other.custom is None):
            out.append(f"{mine.name} is {'custom' if mine.custom else 'a library species'} "
                       f"here and {'custom' if other.custom else 'a library species'} there")
            continue
        if mine.custom is None:
            continue
        a, b = mine.custom, other.custom
        for label, x, y in (("formula", dict(a.formula), dict(b.formula)),
                            ("enthalpy", a.heat_of_formation, b.heat_of_formation),
                            ("enthalpy units", a.heat_of_formation_units,
                             b.heat_of_formation_units),
                            ("reference temperature", a.reference_temperature,
                             b.reference_temperature),
                            ("molecular weight", a.molecular_weight, b.molecular_weight)):
            if x != y:
                out.append(f"{mine.name} {label} {x!r} vs {y!r}")
    if ours.initial_temperature != theirs.initial_temperature:
        out.append(f"initial temperature {ours.initial_temperature!r} vs "
                   f"{theirs.initial_temperature!r}")
    return tuple(out)


def _thermochemistry_case(record: EvidenceRecord,
                          formulation: SolidFormulation) -> tuple[str | None, str]:
    key = record.executable_key
    if key is None:
        return None, ("This build has no Thermochemistry case for this formulation: the "
                      "record names no executable case, and none is created from evidence.")
    template = gateway.solid_formulation_templates().get(key)
    if template is None:
        return None, (f"The record's executable key {key!r} names no Thermochemistry case "
                      "in this build.")
    differences = formulation_differences(formulation, template)
    if differences:
        return None, (f"The formulation built from the evidence differs from the "
                      f"Thermochemistry case {key!r} ({'; '.join(differences)}). The case "
                      "is not opened in its place.")
    return key, ""


# ------------------------------------------------------------------ assess


def assess(record: EvidenceRecord,
           sources: Mapping[str, SourceReference] | None = None) -> CompatibilityAssessment:
    """R1 section 4 for one record. Probes the installed library; solves nothing.

    ``sources`` is the registry the record shipped with; when given, an access
    restriction also names the cited sources that withhold values. Never mutates
    the record, and never raises for anything a record can hold.
    """
    rid = record.record_id
    if not evidence_service.is_cea_target(record):
        return CompatibilityAssessment(rid, CompatibilityState.NOT_A_CEA_TARGET)
    propellant = record.propellant

    access = access_gate(record, sources)
    if not access.permitted:
        return CompatibilityAssessment(
            rid, None, access=access,
            notes=("Compatibility was not evaluated: the check stops at the access "
                   "gate, probes nothing and says nothing about the chemistry.",))

    blockers = _structural_blockers(propellant) + _definition_blockers(propellant)
    names = [item.provider_name for item in propellant.ingredients
             if item.custom is None and item.provider_name is not None]
    probe = gateway.probe_solid_library_species(names)
    blockers += _library_blockers(propellant, probe)
    state = _state_of(blockers)
    if state is not None:
        return CompatibilityAssessment(rid, state, tuple(blockers), probe, access=access)

    try:
        formulation = _build(record)
    except ThermochemistryError as error:
        return CompatibilityAssessment(rid, CompatibilityState.BLOCKED, (Blocker(
            PHYSICS_REFUSED, f"The formulation was refused when built: {error}",
            category="physics"),), probe, access=access)
    notes = _build_notes(propellant)
    if not probe.usable:
        return CompatibilityAssessment(rid, CompatibilityState.PROVIDER_UNAVAILABLE,
                                       probe=probe, notes=notes, access=access)
    state = (CompatibilityState.EXECUTABLE_VERIFIED
             if record.capabilities[Dimension.VA] is EvidenceStatus.REGRESSION_LOCKED
             else CompatibilityState.EXECUTABLE_SOURCE_COMPLETE)
    key, note = _thermochemistry_case(record, formulation)
    return CompatibilityAssessment(rid, state, (), probe, formulation, notes, key, note,
                                   access=access)


# ------------------------------------------------------------ presentation


def blocker_rows(assessment: CompatibilityAssessment) -> list[dict]:
    """The blockers as view rows: code, category, field, ingredient, name, text."""
    return [{"code": b.code, "category": b.category, "field": b.field,
             "ingredient": b.ingredient, "name": b.name, "text": b.detail}
            for b in assessment.blockers]


def access_rows(assessment: CompatibilityAssessment) -> list[dict]:
    """The access gate's restrictions as view rows, kept apart from blockers."""
    access = assessment.access
    if access is None:
        return []
    return [{"code": r.code, "field": r.field, "ingredient": r.ingredient,
             "policies": r.policies, "text": r.detail} for r in access.restrictions]


def identity_text(probe: Any) -> str:
    """The provider and database that actually answered; empty when none was asked."""
    if probe is None:
        return ""
    if not probe.usable:
        detail = f": {probe.detail}" if probe.detail else ""
        return f"{probe.provider} unavailable ({probe.status}){detail}"
    return (f"Probed: {probe.provider} {probe.library_version} · "
            f"{probe.database or 'thermo.lib'} sha256 {probe.database_sha256}")
