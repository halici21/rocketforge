"""Evidence JSON, schema versions 1 and 2: strict parsing and one canonical form.

Version 1 is every record without a burn law, and the source registry. Version 2
is version 1 plus one field, ``burn_law``, and is written only for a record that
carries one -- so every version-1 file stays byte for byte what it was, and a
version-1 reader refuses a burn law instead of silently dropping it.

Parsing is strict on purpose. A field that is not recognised, a field that is
absent, a value of the wrong JSON type, a duplicated key, a ``NaN``, or a
``schema_version`` this build does not know -- each is refused with
:class:`~.values.EvidenceSchemaError`. Nothing is defaulted: every field in the
schema is written out, ``null`` included, because a reader cannot tell a
deliberate default from a forgotten field.

The loader takes text and returns records. It does not look for files, and it
does not consult a provider: where the data lives is the caller's business, and
whether a formulation can be solved is a later, separate question.

The canonical form (:func:`record_to_json`, :func:`sources_to_json`) is fixed
key order, two-space indentation, UTF-8 text and a final newline, so a record
round-trips byte for byte and a shipped file can be checked to be in it.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from enum import StrEnum
from typing import Any, TypeVar

from .burnlaw import BurnLawReference, BurnLawRegime
from .records import (
    CustomDefinition,
    EvidenceRecord,
    IngredientReference,
    PropellantReference,
    RecordKind,
    SourceReference,
    validate_against_sources,
)
from .values import (
    AccessClass,
    Datum,
    Dimension,
    EvidenceSchemaError,
    EvidenceStatus,
    Missing,
    MissingReason,
    ReportedValue,
    ShippingPolicy,
    ValueStatus,
)

__all__ = [
    "SCHEMA_VERSION",
    "BURN_LAW_SCHEMA_VERSION",
    "RECORD_SCHEMA_VERSIONS",
    "sources_from_json",
    "sources_to_json",
    "record_from_json",
    "record_to_json",
    "record_to_dict",
    "record_from_dict",
]

#: The base schema version: the source registry, and every record without a burn law.
SCHEMA_VERSION = 1

#: A record that carries a burn law: version 1 plus the ``burn_law`` field.
BURN_LAW_SCHEMA_VERSION = 2

#: Every record version this build reads.
RECORD_SCHEMA_VERSIONS = (SCHEMA_VERSION, BURN_LAW_SCHEMA_VERSION)

E = TypeVar("E", bound=StrEnum)

_REPORTED_REQUIRED = ("value", "unit", "source_id", "locator", "status")
_REPORTED_OPTIONAL = ("decimals", "significant_figures", "note")
_MISSING_KEYS = ("missing", "note")
_SOURCE_FIELDS = ("source_id", "organization", "authors", "title", "year",
                  "identifiers", "locator", "source_type", "access_class",
                  "rights_statement", "shipping", "tier")
_CUSTOM_FIELDS = ("formula", "enthalpy", "reference_temperature", "molecular_weight")
_INGREDIENT_FIELDS = ("source_name", "fraction", "provider_name", "custom")
_PROPELLANT_FIELDS = ("propellant_id", "source_ids", "family", "source_name",
                      "exact_formulation", "basis", "ingredients", "density",
                      "initial_temperature")
_RECORD_FIELDS = ("schema_version", "record_id", "title", "kind", "source_ids",
                  "capabilities", "capability_notes", "propellant",
                  "comparison_case_ids", "executable_key", "blockers", "notes")
_RECORD_FIELDS_V2 = _RECORD_FIELDS + ("burn_law",)
_BURN_LAW_FIELDS = ("law_id", "source_ids", "propellant_name", "form", "pressure_unit",
                    "rate_unit", "regimes", "temperature", "uncertainty")
_REGIME_FIELDS = ("pressure_min", "pressure_max", "a", "n")


# ---------------------------------------------------------------- parsing


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise EvidenceSchemaError(f"duplicate key {key!r}")
        out[key] = value
    return out


def _reject_constant(name: str) -> None:
    raise EvidenceSchemaError(f"{name} is not a value evidence can hold")


def _parse(text: str) -> Any:
    if not isinstance(text, str):
        raise EvidenceSchemaError(f"evidence must be JSON text, got {type(text).__name__}")
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicates,
                          parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise EvidenceSchemaError(f"not valid JSON: {exc}") from None


def _object(value: Any, where: str, required: Iterable[str],
            optional: Iterable[str] = ()) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceSchemaError(f"{where} must be a JSON object, got {type(value).__name__}")
    required, optional = tuple(required), tuple(optional)
    unknown = sorted(set(value) - set(required) - set(optional))
    if unknown:
        raise EvidenceSchemaError(f"{where}: unknown field(s) {unknown}")
    absent = [name for name in required if name not in value]
    if absent:
        raise EvidenceSchemaError(f"{where}: missing field(s) {absent}")
    return value


def _string(value: Any, where: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise EvidenceSchemaError(f"{where} must be a string, got {value!r}")
    return value


def _strings(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise EvidenceSchemaError(f"{where} must be a list of strings, got {value!r}")
    return tuple(_string(item, f"{where}[{i}]") for i, item in enumerate(value))


def _integer(value: Any, where: str, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise EvidenceSchemaError(f"{where} must be an integer, got {value!r}")
    return value


def _enum(kind: type[E], value: Any, where: str) -> E:
    try:
        return kind(value)
    except ValueError:
        raise EvidenceSchemaError(
            f"{where}: {value!r} is not one of {[m.value for m in kind]}") from None


def _schema_version(payload: dict[str, Any], where: str,
                    accepted: tuple[int, ...] = (SCHEMA_VERSION,)) -> int:
    if "schema_version" not in payload:
        raise EvidenceSchemaError(f"{where}: schema_version is required")
    version = payload["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise EvidenceSchemaError(f"{where}: schema_version must be an integer, got {version!r}")
    if version not in accepted:
        raise EvidenceSchemaError(
            f"{where}: schema_version {version} is not supported; this build reads "
            f"version {' or '.join(str(v) for v in accepted)} only")
    return version


def _datum_from(value: Any, where: str) -> Datum:
    if isinstance(value, dict) and "missing" in value:
        payload = _object(value, where, ("missing",), ("note",))
        return Missing(_enum(MissingReason, payload["missing"], f"{where}.missing"),
                       _string(payload.get("note", ""), f"{where}.note"))
    payload = _object(value, where, _REPORTED_REQUIRED, _REPORTED_OPTIONAL)
    number = payload["value"]
    if isinstance(number, bool) or not isinstance(number, (int, float)):
        raise EvidenceSchemaError(f"{where}.value must be a number, got {number!r}")
    return ReportedValue(
        value=number,
        unit=_string(payload["unit"], f"{where}.unit"),
        source_id=_string(payload["source_id"], f"{where}.source_id"),
        locator=_string(payload["locator"], f"{where}.locator"),
        status=_enum(ValueStatus, payload["status"], f"{where}.status"),
        decimals=_integer(payload.get("decimals"), f"{where}.decimals", nullable=True),
        significant_figures=_integer(payload.get("significant_figures"),
                                     f"{where}.significant_figures", nullable=True),
        note=_string(payload.get("note", ""), f"{where}.note"))


def _custom_from(value: Any, where: str) -> CustomDefinition:
    payload = _object(value, where, _CUSTOM_FIELDS)
    raw_formula = payload["formula"]
    formula: Mapping[str, ReportedValue] | Missing
    if isinstance(raw_formula, dict) and "missing" in raw_formula:
        formula = _datum_from(raw_formula, f"{where}.formula")
    else:
        if not isinstance(raw_formula, dict):
            raise EvidenceSchemaError(f"{where}.formula must be an object, got {raw_formula!r}")
        formula = {}
        for element, count in raw_formula.items():
            datum = _datum_from(count, f"{where}.formula.{element}")
            if not isinstance(datum, ReportedValue):
                raise EvidenceSchemaError(
                    f"{where}.formula.{element}: an atom count is reported or the whole "
                    "formula is missing, never one element")
            formula[element] = datum
    return CustomDefinition(
        formula=formula,
        enthalpy=_datum_from(payload["enthalpy"], f"{where}.enthalpy"),
        reference_temperature=_datum_from(payload["reference_temperature"],
                                          f"{where}.reference_temperature"),
        molecular_weight=_datum_from(payload["molecular_weight"], f"{where}.molecular_weight"))


def _ingredient_from(value: Any, where: str) -> IngredientReference:
    payload = _object(value, where, _INGREDIENT_FIELDS)
    custom = payload["custom"]
    return IngredientReference(
        source_name=_string(payload["source_name"], f"{where}.source_name"),
        fraction=_datum_from(payload["fraction"], f"{where}.fraction"),
        provider_name=_string(payload["provider_name"], f"{where}.provider_name", nullable=True),
        custom=None if custom is None else _custom_from(custom, f"{where}.custom"))


def _propellant_from(value: Any, where: str) -> PropellantReference:
    payload = _object(value, where, _PROPELLANT_FIELDS)
    exact = payload["exact_formulation"]
    if not isinstance(exact, bool):
        raise EvidenceSchemaError(f"{where}.exact_formulation must be true or false")
    ingredients = payload["ingredients"]
    if not isinstance(ingredients, list):
        raise EvidenceSchemaError(f"{where}.ingredients must be a list")
    return PropellantReference(
        propellant_id=_string(payload["propellant_id"], f"{where}.propellant_id"),
        source_ids=_strings(payload["source_ids"], f"{where}.source_ids"),
        family=_string(payload["family"], f"{where}.family"),
        source_name=_string(payload["source_name"], f"{where}.source_name"),
        exact_formulation=exact,
        basis=_string(payload["basis"], f"{where}.basis"),
        ingredients=tuple(_ingredient_from(item, f"{where}.ingredients[{i}]")
                          for i, item in enumerate(ingredients)),
        density=_datum_from(payload["density"], f"{where}.density"),
        initial_temperature=_datum_from(payload["initial_temperature"],
                                        f"{where}.initial_temperature"))


def _reported_from(value: Any, where: str) -> ReportedValue:
    datum = _datum_from(value, where)
    if not isinstance(datum, ReportedValue):
        raise EvidenceSchemaError(
            f"{where}: a burn-law limit or coefficient is reported, never missing")
    return datum


def _burn_law_from(value: Any, where: str) -> BurnLawReference:
    payload = _object(value, where, _BURN_LAW_FIELDS)
    regimes = payload["regimes"]
    if not isinstance(regimes, list):
        raise EvidenceSchemaError(f"{where}.regimes must be a list")
    parsed = []
    for i, item in enumerate(regimes):
        at = f"{where}.regimes[{i}]"
        regime = _object(item, at, _REGIME_FIELDS)
        parsed.append(BurnLawRegime(**{name: _reported_from(regime[name], f"{at}.{name}")
                                       for name in _REGIME_FIELDS}))
    return BurnLawReference(
        law_id=_string(payload["law_id"], f"{where}.law_id"),
        source_ids=_strings(payload["source_ids"], f"{where}.source_ids"),
        propellant_name=_string(payload["propellant_name"], f"{where}.propellant_name"),
        form=_string(payload["form"], f"{where}.form"),
        pressure_unit=_string(payload["pressure_unit"], f"{where}.pressure_unit"),
        rate_unit=_string(payload["rate_unit"], f"{where}.rate_unit"),
        regimes=tuple(parsed),
        temperature=_datum_from(payload["temperature"], f"{where}.temperature"),
        uncertainty=_datum_from(payload["uncertainty"], f"{where}.uncertainty"))


def _source_from(value: Any, where: str) -> SourceReference:
    payload = _object(value, where, _SOURCE_FIELDS)
    identifiers = payload["identifiers"]
    if not isinstance(identifiers, dict):
        raise EvidenceSchemaError(f"{where}.identifiers must be an object")
    return SourceReference(
        source_id=_string(payload["source_id"], f"{where}.source_id"),
        organization=_string(payload["organization"], f"{where}.organization"),
        authors=_strings(payload["authors"], f"{where}.authors"),
        title=_string(payload["title"], f"{where}.title"),
        year=_integer(payload["year"], f"{where}.year", nullable=True),
        identifiers={k: _string(v, f"{where}.identifiers.{k}") for k, v in identifiers.items()},
        locator=_string(payload["locator"], f"{where}.locator"),
        source_type=_string(payload["source_type"], f"{where}.source_type"),
        access_class=_enum(AccessClass, payload["access_class"], f"{where}.access_class"),
        rights_statement=_string(payload["rights_statement"], f"{where}.rights_statement"),
        shipping=_enum(ShippingPolicy, payload["shipping"], f"{where}.shipping"),
        tier=_integer(payload["tier"], f"{where}.tier"))


def _dimension_map(value: Any, where: str, read) -> dict[Dimension, Any]:
    if not isinstance(value, dict):
        raise EvidenceSchemaError(f"{where} must be an object keyed by dimension")
    return {_enum(Dimension, key, f"{where} key"): read(item, f"{where}.{key}")
            for key, item in value.items()}


def record_from_dict(payload: Any) -> EvidenceRecord:
    """An :class:`EvidenceRecord` from its parsed JSON object. Schema-checked,
    not source-checked; :func:`record_from_json` does both."""
    if not isinstance(payload, dict):
        raise EvidenceSchemaError("an evidence record must be a JSON object")
    version = _schema_version(payload, "record", RECORD_SCHEMA_VERSIONS)
    payload = _object(payload, "record",
                      _RECORD_FIELDS if version == SCHEMA_VERSION else _RECORD_FIELDS_V2)
    where = f"record {payload.get('record_id')!r}"
    propellant = payload["propellant"]
    burn_law = None
    if version == BURN_LAW_SCHEMA_VERSION:
        if payload["burn_law"] is None:
            raise EvidenceSchemaError(
                f"{where}: a schema-version-2 record carries a burn law; a record "
                "without one is written as version 1")
        burn_law = _burn_law_from(payload["burn_law"], f"{where}.burn_law")
    return EvidenceRecord(
        record_id=_string(payload["record_id"], f"{where}.record_id"),
        title=_string(payload["title"], f"{where}.title"),
        kind=_enum(RecordKind, payload["kind"], f"{where}.kind"),
        source_ids=_strings(payload["source_ids"], f"{where}.source_ids"),
        capabilities=_dimension_map(
            payload["capabilities"], f"{where}.capabilities",
            lambda v, w: _enum(EvidenceStatus, v, w)),
        capability_notes=_dimension_map(payload["capability_notes"],
                                        f"{where}.capability_notes", _string),
        propellant=None if propellant is None else _propellant_from(
            propellant, f"{where}.propellant"),
        comparison_case_ids=_strings(payload["comparison_case_ids"],
                                     f"{where}.comparison_case_ids"),
        executable_key=_string(payload["executable_key"], f"{where}.executable_key",
                               nullable=True),
        blockers=_strings(payload["blockers"], f"{where}.blockers"),
        notes=_string(payload["notes"], f"{where}.notes"),
        burn_law=burn_law)


def record_from_json(text: str, sources: Mapping[str, SourceReference]) -> EvidenceRecord:
    """Parse one record and check it against the source registry it ships with."""
    record = record_from_dict(_parse(text))
    validate_against_sources(record, sources)
    return record


def sources_from_json(text: str) -> dict[str, SourceReference]:
    """Parse a source registry, keyed by ``source_id``, in file order."""
    payload = _parse(text)
    if not isinstance(payload, dict):
        raise EvidenceSchemaError("a source registry must be a JSON object")
    _schema_version(payload, "source registry")
    payload = _object(payload, "source registry", ("schema_version", "sources"))
    if not isinstance(payload["sources"], list):
        raise EvidenceSchemaError("source registry: sources must be a list")
    out: dict[str, SourceReference] = {}
    for i, item in enumerate(payload["sources"]):
        source = _source_from(item, f"sources[{i}]")
        if source.source_id in out:
            raise EvidenceSchemaError(f"source {source.source_id!r} is listed twice")
        out[source.source_id] = source
    return out


# ---------------------------------------------------------------- writing


def _datum_to(datum: Datum) -> dict[str, Any]:
    if isinstance(datum, Missing):
        out: dict[str, Any] = {"missing": datum.reason.value}
        if datum.note:
            out["note"] = datum.note
        return out
    out = {"value": datum.value, "unit": datum.unit, "source_id": datum.source_id,
           "locator": datum.locator, "status": datum.status.value}
    if datum.decimals is not None:
        out["decimals"] = datum.decimals
    if datum.significant_figures is not None:
        out["significant_figures"] = datum.significant_figures
    if datum.note:
        out["note"] = datum.note
    return out


def _custom_to(custom: CustomDefinition) -> dict[str, Any]:
    formula = (_datum_to(custom.formula) if isinstance(custom.formula, Missing)
               else {element: _datum_to(count) for element, count in custom.formula.items()})
    return {"formula": formula,
            "enthalpy": _datum_to(custom.enthalpy),
            "reference_temperature": _datum_to(custom.reference_temperature),
            "molecular_weight": _datum_to(custom.molecular_weight)}


def _propellant_to(propellant: PropellantReference) -> dict[str, Any]:
    return {
        "propellant_id": propellant.propellant_id,
        "source_ids": list(propellant.source_ids),
        "family": propellant.family,
        "source_name": propellant.source_name,
        "exact_formulation": propellant.exact_formulation,
        "basis": propellant.basis,
        "ingredients": [{
            "source_name": item.source_name,
            "fraction": _datum_to(item.fraction),
            "provider_name": item.provider_name,
            "custom": None if item.custom is None else _custom_to(item.custom),
        } for item in propellant.ingredients],
        "density": _datum_to(propellant.density),
        "initial_temperature": _datum_to(propellant.initial_temperature),
    }


def _burn_law_to(law: BurnLawReference) -> dict[str, Any]:
    return {
        "law_id": law.law_id,
        "source_ids": list(law.source_ids),
        "propellant_name": law.propellant_name,
        "form": law.form,
        "pressure_unit": law.pressure_unit,
        "rate_unit": law.rate_unit,
        "regimes": [{name: _datum_to(getattr(r, name)) for name in _REGIME_FIELDS}
                    for r in law.regimes],
        "temperature": _datum_to(law.temperature),
        "uncertainty": _datum_to(law.uncertainty),
    }


def record_to_dict(record: EvidenceRecord) -> dict[str, Any]:
    """The record as a JSON object, in canonical key order.

    Version 1 unless the record carries a burn law; then version 2, with
    ``burn_law`` last.
    """
    out = _record_base(record)
    if record.burn_law is not None:
        out["schema_version"] = BURN_LAW_SCHEMA_VERSION
        out["burn_law"] = _burn_law_to(record.burn_law)
    return out


def _record_base(record: EvidenceRecord) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": record.record_id,
        "title": record.title,
        "kind": record.kind.value,
        "source_ids": list(record.source_ids),
        "capabilities": {d.value: s.value for d, s in record.capabilities.items()},
        "capability_notes": {d.value: n for d, n in record.capability_notes.items()},
        "propellant": None if record.propellant is None else _propellant_to(record.propellant),
        "comparison_case_ids": list(record.comparison_case_ids),
        "executable_key": record.executable_key,
        "blockers": list(record.blockers),
        "notes": record.notes,
    }


def _dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def record_to_json(record: EvidenceRecord) -> str:
    """Canonical JSON text for one record."""
    return _dump(record_to_dict(record))


def sources_to_json(sources: Iterable[SourceReference]) -> str:
    """Canonical JSON text for a source registry, in the order given."""
    return _dump({"schema_version": SCHEMA_VERSION, "sources": [{
        "source_id": s.source_id,
        "organization": s.organization,
        "authors": list(s.authors),
        "title": s.title,
        "year": s.year,
        "identifiers": dict(s.identifiers),
        "locator": s.locator,
        "source_type": s.source_type,
        "access_class": s.access_class.value,
        "rights_statement": s.rights_statement,
        "shipping": s.shipping.value,
        "tier": s.tier,
    } for s in sources]})
