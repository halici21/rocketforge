"""Engine-evidence JSON, schema version 1: strict in, canonical out.

The same rules as the solid-propellant evidence files
(:mod:`rocketforge.evidence.load`), whose parser helpers this module reuses:
an unknown or absent field, a duplicated key, a ``NaN``, a value of the wrong
JSON type, an unknown enumeration value or an unsupported ``schema_version``
is refused with :class:`~rocketforge.evidence.EvidenceSchemaError`. Every field
is written, ``null`` included, so a reader can never mistake a forgotten field
for a default. Loading never supplies a value: a field the file does not hold
is an error, not a physical default.

The document carries ``"format": "rocketforge.engine_evidence"`` beside its
schema version, so a solid-propellant evidence file is never read as engine
evidence or the other way round.

The canonical text is two-space indented UTF-8 with a final newline, so a
corpus round-trips byte for byte. :func:`corpus_fingerprint` is the SHA-256 of
the compact sorted-key JSON of the same dictionary -- the fingerprint
convention used across RocketForge (e.g. ``rocketforge.engine.chamber_sizing``).
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any

from ..load import _enum, _integer, _object, _parse, _string, _strings
from ..records import SourceReference
from ..values import (
    AccessClass,
    EvidenceError,
    EvidenceSchemaError,
    Missing,
    MissingReason,
    ShippingPolicy,
    ValueStatus,
)
from .assertions import (
    Assertion,
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
from .corpus import EngineEvidenceCorpus
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
from .sources import EngineSource, RightsNotice, RightsRecord
from .topology import (
    AbsenceStatement,
    Completeness,
    Component,
    Schematic,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)
from .vocabulary import (
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

__all__ = ["ENGINE_EVIDENCE_FORMAT", "ENGINE_EVIDENCE_SCHEMA_VERSION", "corpus_from_json",
           "corpus_from_dict", "corpus_to_dict", "corpus_to_json", "corpus_fingerprint"]

ENGINE_EVIDENCE_FORMAT = "rocketforge.engine_evidence"
ENGINE_EVIDENCE_SCHEMA_VERSION = 1

_COLLECTIONS = ("sources", "families", "variants", "configurations", "operating_points",
                "units", "aliases", "lineage", "components", "schematics", "topologies",
                "assertions", "conflicts")
_TOP = ("format", "schema_version") + _COLLECTIONS
_REFERENCE = ("source_id", "organization", "authors", "title", "year", "identifiers",
              "locator", "source_type", "access_class", "rights_statement", "shipping", "tier")


# ---------------------------------------------------------------- small readers


def _opt_string(value: Any, where: str) -> str | None:
    return _string(value, where, nullable=True)


def _number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceSchemaError(f"{where} must be a number, got {value!r}")
    return value


def _bool(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceSchemaError(f"{where} must be true or false, got {value!r}")
    return value


def _list(value: Any, where: str) -> list:
    if not isinstance(value, list):
        raise EvidenceSchemaError(f"{where} must be a list, got {type(value).__name__}")
    return value


def _opt_enum(kind, value: Any, where: str):
    return None if value is None else _enum(kind, value, where)


def _missing_from(value: Any, where: str) -> Missing:
    payload = _object(value, where, ("missing",), ("note",))
    return Missing(_enum(MissingReason, payload["missing"], f"{where}.missing"),
                   _string(payload.get("note", ""), f"{where}.note"))


def _missing_to(m: Missing) -> dict[str, Any]:
    out: dict[str, Any] = {"missing": m.reason.value}
    if m.note:
        out["note"] = m.note
    return out


def _ref_from(value: Any, where: str) -> SubjectRef:
    p = _object(value, where, ("kind", "id"))
    return SubjectRef(_enum(SubjectKind, p["kind"], f"{where}.kind"), _string(p["id"], f"{where}.id"))


def _ref_to(r: SubjectRef) -> dict[str, Any]:
    return {"kind": r.kind.value, "id": r.id}


# ---------------------------------------------------------------- sources


def _notice_from(value: Any, where: str) -> RightsNotice | Missing:
    if isinstance(value, dict) and "missing" in value:
        return _missing_from(value, where)
    p = _object(value, where, ("statement", "where"))
    return RightsNotice(_string(p["statement"], f"{where}.statement"), _string(p["where"], f"{where}.where"))


def _notice_to(n: RightsNotice | Missing) -> dict[str, Any]:
    return _missing_to(n) if isinstance(n, Missing) else {"statement": n.statement, "where": n.where}


_RIGHTS = ("host_metadata", "printed_notice", "values", "figures", "tables", "text",
           "notices_disagree", "review", "review_note")


def _rights_from(value: Any, where: str) -> RightsRecord:
    p = _object(value, where, _RIGHTS)
    return RightsRecord(
        host_metadata=_notice_from(p["host_metadata"], f"{where}.host_metadata"),
        printed_notice=_notice_from(p["printed_notice"], f"{where}.printed_notice"),
        **{k: _enum(ShippingPolicy, p[k], f"{where}.{k}") for k in ("values", "figures", "tables", "text")},
        notices_disagree=_bool(p["notices_disagree"], f"{where}.notices_disagree"),
        review=_enum(RightsReview, p["review"], f"{where}.review"),
        review_note=_string(p["review_note"], f"{where}.review_note"))


def _rights_to(r: RightsRecord) -> dict[str, Any]:
    return {"host_metadata": _notice_to(r.host_metadata), "printed_notice": _notice_to(r.printed_notice),
            "values": r.values.value, "figures": r.figures.value, "tables": r.tables.value,
            "text": r.text.value, "notices_disagree": r.notices_disagree, "review": r.review.value,
            "review_note": r.review_note}


_SOURCE = ("reference", "authority", "primacy", "access", "content_sha256", "same_document_as",
           "rights", "access_note")


def _source_from(value: Any, where: str) -> EngineSource:
    p = _object(value, where, _SOURCE)
    r = _object(p["reference"], f"{where}.reference", _REFERENCE)
    ids = r["identifiers"]
    if not isinstance(ids, dict):
        raise EvidenceSchemaError(f"{where}.reference.identifiers must be an object")
    reference = SourceReference(
        source_id=_string(r["source_id"], f"{where}.source_id"),
        organization=_string(r["organization"], f"{where}.organization"),
        authors=_strings(r["authors"], f"{where}.authors"),
        title=_string(r["title"], f"{where}.title"),
        year=_integer(r["year"], f"{where}.year", nullable=True),
        identifiers={k: _string(v, f"{where}.identifiers.{k}") for k, v in ids.items()},
        locator=_string(r["locator"], f"{where}.locator"),
        source_type=_string(r["source_type"], f"{where}.source_type"),
        access_class=_enum(AccessClass, r["access_class"], f"{where}.access_class"),
        rights_statement=_string(r["rights_statement"], f"{where}.rights_statement"),
        shipping=_enum(ShippingPolicy, r["shipping"], f"{where}.shipping"),
        tier=_integer(r["tier"], f"{where}.tier"))
    return EngineSource(
        reference=reference,
        authority=_enum(SourceAuthority, p["authority"], f"{where}.authority"),
        primacy=_enum(SourcePrimacy, p["primacy"], f"{where}.primacy"),
        access=_enum(SourceAccess, p["access"], f"{where}.access"),
        content_sha256=_opt_string(p["content_sha256"], f"{where}.content_sha256"),
        same_document_as=_opt_string(p["same_document_as"], f"{where}.same_document_as"),
        rights=_rights_from(p["rights"], f"{where}.rights"),
        access_note=_string(p["access_note"], f"{where}.access_note"))


def _source_to(s: EngineSource) -> dict[str, Any]:
    ref = s.reference
    return {
        "reference": {"source_id": ref.source_id, "organization": ref.organization,
                      "authors": list(ref.authors), "title": ref.title, "year": ref.year,
                      "identifiers": dict(ref.identifiers), "locator": ref.locator,
                      "source_type": ref.source_type, "access_class": ref.access_class.value,
                      "rights_statement": ref.rights_statement, "shipping": ref.shipping.value,
                      "tier": ref.tier},
        "authority": s.authority.value, "primacy": s.primacy.value, "access": s.access.value,
        "content_sha256": s.content_sha256, "same_document_as": s.same_document_as,
        "rights": _rights_to(s.rights), "access_note": s.access_note,
    }


# ---------------------------------------------------------------- identity


def _family_from(v: Any, w: str) -> EngineFamily:
    p = _object(v, w, ("family_id", "name", "notes"))
    return EngineFamily(_string(p["family_id"], w), _string(p["name"], w), _string(p["notes"], w))


def _variant_from(v: Any, w: str) -> EngineVariant:
    p = _object(v, w, ("variant_id", "family_id", "designation", "notes"))
    return EngineVariant(*(_string(p[k], f"{w}.{k}") for k in ("variant_id", "family_id", "designation", "notes")))


def _configuration_from(v: Any, w: str) -> EngineConfiguration:
    p = _object(v, w, ("configuration_id", "variant_id", "label", "effective", "notes"))
    eff = p["effective"]
    effective = _missing_from(eff, f"{w}.effective") if isinstance(eff, dict) else _string(eff, f"{w}.effective")
    return EngineConfiguration(_string(p["configuration_id"], w), _string(p["variant_id"], w),
                               _string(p["label"], w), effective, _string(p["notes"], w))


def _point_from(v: Any, w: str) -> OperatingPoint:
    p = _object(v, w, ("operating_point_id", "configuration_id", "label", "notes"))
    return OperatingPoint(*(_string(p[k], f"{w}.{k}") for k in ("operating_point_id", "configuration_id", "label", "notes")))


def _unit_from(v: Any, w: str) -> PropulsionUnit:
    p = _object(v, w, ("unit_id", "kind", "designation", "members", "notes"))
    members = []
    for i, m in enumerate(_list(p["members"], f"{w}.members")):
        mp = _object(m, f"{w}.members[{i}]", ("member", "count", "role"))
        count = mp["count"]
        members.append(UnitMember(
            _ref_from(mp["member"], f"{w}.members[{i}].member"),
            _missing_from(count, f"{w}.members[{i}].count") if isinstance(count, dict)
            else _integer(count, f"{w}.members[{i}].count"),
            _string(mp["role"], f"{w}.members[{i}].role")))
    return PropulsionUnit(_string(p["unit_id"], w), _enum(PropulsionUnitKind, p["kind"], f"{w}.kind"),
                          _string(p["designation"], w), tuple(members), _string(p["notes"], w))


def _alias_from(v: Any, w: str) -> Alias:
    p = _object(v, w, ("alias_id", "name", "kind", "target", "source_ids", "ambiguous", "notes"))
    return Alias(_string(p["alias_id"], w), _string(p["name"], w), _enum(AliasKind, p["kind"], f"{w}.kind"),
                 _ref_from(p["target"], f"{w}.target"), _strings(p["source_ids"], f"{w}.source_ids"),
                 _bool(p["ambiguous"], f"{w}.ambiguous"), _string(p["notes"], w))


def _lineage_from(v: Any, w: str) -> LineageEdge:
    p = _object(v, w, ("lineage_id", "kind", "source", "target", "source_ids", "notes"))
    return LineageEdge(_string(p["lineage_id"], w), _enum(LineageKind, p["kind"], f"{w}.kind"),
                       _ref_from(p["source"], f"{w}.source"), _ref_from(p["target"], f"{w}.target"),
                       _strings(p["source_ids"], f"{w}.source_ids"), _string(p["notes"], w))


# ---------------------------------------------------------------- topology


def _component_from(v: Any, w: str) -> Component:
    p = _object(v, w, ("component_id", "scope", "component_type", "label", "ownership", "part_ids", "notes"))
    return Component(_string(p["component_id"], w), _ref_from(p["scope"], f"{w}.scope"),
                     _enum(ComponentType, p["component_type"], f"{w}.component_type"),
                     _string(p["label"], w), _enum(Ownership, p["ownership"], f"{w}.ownership"),
                     _strings(p["part_ids"], f"{w}.part_ids"), _string(p["notes"], w))


def _schematic_from(v: Any, w: str) -> Schematic:
    p = _object(v, w, ("schematic_id", "source_id", "locator", "title_as_printed", "provenance",
                       "drawn_by", "legibility", "notes"))
    return Schematic(_string(p["schematic_id"], w), _string(p["source_id"], w), _string(p["locator"], w),
                     _string(p["title_as_printed"], w),
                     _enum(SchematicProvenance, p["provenance"], f"{w}.provenance"),
                     _string(p["drawn_by"], w), _string(p["legibility"], w), _string(p["notes"], w))


_NODE = ("node_id", "component_type", "label", "ownership", "evidence", "locator", "component_id")
_EDGE = ("edge_id", "source", "target", "kind", "carrier", "role", "evidence", "locator",
         "split_group", "merge_group")


def _topology_from(v: Any, w: str) -> TopologyGraph:
    p = _object(v, w, ("topology_id", "scope", "label", "provenance", "schematic_ids",
                       "text_source_ids", "completeness", "nodes", "edges", "notes"))
    cp = _object(p["completeness"], f"{w}.completeness", ("declared_complete", "known_omissions", "absences"))
    absences = []
    for i, a in enumerate(_list(cp["absences"], f"{w}.completeness.absences")):
        ap = _object(a, f"{w}.absences[{i}]", ("component_type", "statement", "source_id", "locator"))
        absences.append(AbsenceStatement(_enum(ComponentType, ap["component_type"], f"{w}.absences[{i}]"),
                                         _string(ap["statement"], w), _string(ap["source_id"], w),
                                         _string(ap["locator"], w)))
    nodes = []
    for i, n in enumerate(_list(p["nodes"], f"{w}.nodes")):
        np_ = _object(n, f"{w}.nodes[{i}]", _NODE)
        nodes.append(TopologyNode(
            _string(np_["node_id"], w), _enum(ComponentType, np_["component_type"], f"{w}.nodes[{i}]"),
            _string(np_["label"], w), _enum(Ownership, np_["ownership"], f"{w}.nodes[{i}].ownership"),
            _enum(TopologyEvidence, np_["evidence"], f"{w}.nodes[{i}].evidence"),
            _string(np_["locator"], w), _opt_string(np_["component_id"], w)))
    edges = []
    for i, e in enumerate(_list(p["edges"], f"{w}.edges")):
        ep = _object(e, f"{w}.edges[{i}]", _EDGE)
        edges.append(TopologyEdge(
            _string(ep["edge_id"], w), _string(ep["source"], w), _string(ep["target"], w),
            _enum(EdgeKind, ep["kind"], f"{w}.edges[{i}].kind"), _opt_string(ep["carrier"], w),
            _string(ep["role"], w), _enum(TopologyEvidence, ep["evidence"], f"{w}.edges[{i}].evidence"),
            _string(ep["locator"], w), _opt_string(ep["split_group"], w), _opt_string(ep["merge_group"], w)))
    return TopologyGraph(
        _string(p["topology_id"], w), _ref_from(p["scope"], f"{w}.scope"), _string(p["label"], w),
        _enum(SchematicProvenance, p["provenance"], f"{w}.provenance"),
        _strings(p["schematic_ids"], f"{w}.schematic_ids"), _strings(p["text_source_ids"], f"{w}.text_source_ids"),
        Completeness(_bool(cp["declared_complete"], f"{w}.declared_complete"),
                     _strings(cp["known_omissions"], f"{w}.known_omissions"), tuple(absences)),
        tuple(nodes), tuple(edges), _string(p["notes"], w))


def _topology_to(t: TopologyGraph) -> dict[str, Any]:
    return {
        "topology_id": t.topology_id, "scope": _ref_to(t.scope), "label": t.label,
        "provenance": t.provenance.value, "schematic_ids": list(t.schematic_ids),
        "text_source_ids": list(t.text_source_ids),
        "completeness": {"declared_complete": t.completeness.declared_complete,
                         "known_omissions": list(t.completeness.known_omissions),
                         "absences": [{"component_type": a.component_type.value, "statement": a.statement,
                                       "source_id": a.source_id, "locator": a.locator}
                                      for a in t.completeness.absences]},
        "nodes": [{"node_id": n.node_id, "component_type": n.component_type.value, "label": n.label,
                   "ownership": n.ownership.value, "evidence": n.evidence.value, "locator": n.locator,
                   "component_id": n.component_id} for n in t.nodes],
        "edges": [{"edge_id": e.edge_id, "source": e.source, "target": e.target, "kind": e.kind.value,
                   "carrier": e.carrier, "role": e.role, "evidence": e.evidence.value, "locator": e.locator,
                   "split_group": e.split_group, "merge_group": e.merge_group} for e in t.edges],
        "notes": t.notes,
    }


# ---------------------------------------------------------------- assertions


def _value_from(v: Any, w: str):
    if not isinstance(v, dict) or "type" not in v:
        raise EvidenceSchemaError(f"{w} must be an object with a 'type'")
    kind = v["type"]
    if kind == "number":
        p = _object(v, w, ("type", "value"))
        return NumberValue(_number(p["value"], f"{w}.value"))
    if kind == "range":
        p = _object(v, w, ("type", "low", "high"))
        return RangeValue(_number(p["low"], f"{w}.low"), _number(p["high"], f"{w}.high"))
    if kind == "enum":
        p = _object(v, w, ("type", "token"))
        return EnumValue(_string(p["token"], f"{w}.token"))
    if kind == "text":
        p = _object(v, w, ("type", "text"))
        return TextValue(_string(p["text"], f"{w}.text"))
    if kind == "missing":
        p = _object(v, w, ("type", "missing"), ("note",))
        return Missing(_enum(MissingReason, p["missing"], f"{w}.missing"), _string(p.get("note", ""), f"{w}.note"))
    raise EvidenceSchemaError(f"{w}.type {kind!r} is not number, range, enum, text or missing")


def _value_to(v) -> dict[str, Any]:
    if isinstance(v, NumberValue):
        return {"type": "number", "value": v.value}
    if isinstance(v, RangeValue):
        return {"type": "range", "low": v.low, "high": v.high}
    if isinstance(v, EnumValue):
        return {"type": "enum", "token": v.token}
    if isinstance(v, TextValue):
        return {"type": "text", "text": v.text}
    return {"type": "missing", **_missing_to(v)}


_CONDITIONS = ("environment", "power_level", "mixture_ratio", "mixture_ratio_form",
               "mixture_ratio_basis", "pressure_basis", "pressure_station", "isp_basis", "qualifiers")


def _setting_from(v: Any, w: str) -> Setting | None:
    if v is None:
        return None
    p = _object(v, w, ("value", "unit", "reference"))
    return Setting(_number(p["value"], f"{w}.value"), _string(p["unit"], f"{w}.unit"),
                   _string(p["reference"], f"{w}.reference"))


def _setting_to(s: Setting | None) -> dict[str, Any] | None:
    return None if s is None else {"value": s.value, "unit": s.unit, "reference": s.reference}


def _conditions_from(v: Any, w: str) -> Conditions:
    p = _object(v, w, _CONDITIONS)
    quals = []
    for i, q in enumerate(_list(p["qualifiers"], f"{w}.qualifiers")):
        qp = _object(q, f"{w}.qualifiers[{i}]", ("name", "value"))
        quals.append(Qualifier(_string(qp["name"], w), _string(qp["value"], w)))
    return Conditions(
        environment=_opt_enum(Environment, p["environment"], f"{w}.environment"),
        power_level=_setting_from(p["power_level"], f"{w}.power_level"),
        mixture_ratio=_setting_from(p["mixture_ratio"], f"{w}.mixture_ratio"),
        mixture_ratio_form=_opt_enum(MixtureRatioForm, p["mixture_ratio_form"], f"{w}.mixture_ratio_form"),
        mixture_ratio_basis=_opt_enum(MixtureRatioBasis, p["mixture_ratio_basis"], f"{w}.mixture_ratio_basis"),
        pressure_basis=_opt_enum(PressureBasis, p["pressure_basis"], f"{w}.pressure_basis"),
        pressure_station=_opt_enum(PressureStation, p["pressure_station"], f"{w}.pressure_station"),
        isp_basis=_opt_enum(IspBasis, p["isp_basis"], f"{w}.isp_basis"),
        qualifiers=tuple(quals))


def _ev(e) -> str | None:
    return None if e is None else e.value


def _conditions_to(c: Conditions) -> dict[str, Any]:
    return {"environment": _ev(c.environment), "power_level": _setting_to(c.power_level),
            "mixture_ratio": _setting_to(c.mixture_ratio), "mixture_ratio_form": _ev(c.mixture_ratio_form),
            "mixture_ratio_basis": _ev(c.mixture_ratio_basis), "pressure_basis": _ev(c.pressure_basis),
            "pressure_station": _ev(c.pressure_station), "isp_basis": _ev(c.isp_basis),
            "qualifiers": [{"name": q.name, "value": q.value} for q in c.qualifiers]}


_ASSERTION = ("assertion_id", "subject", "field_path", "value", "value_as_printed", "unit_as_printed",
              "conditions", "value_kind", "status", "admissibility", "source_id", "locator", "access",
              "operating_point_id", "epoch", "normalized", "first_stated_by", "schematic_id",
              "derivation", "note")


def _assertion_from(v: Any, w: str) -> Assertion:
    p = _object(v, w, _ASSERTION)
    norm = p["normalized"]
    normalized = None
    if norm is not None:
        np_ = _object(norm, f"{w}.normalized", ("value", "unit", "method"))
        normalized = NormalizedQuantity(_value_from(np_["value"], f"{w}.normalized.value"),
                                        _string(np_["unit"], w), _string(np_["method"], w))
    der = p["derivation"]
    derivation = None
    if der is not None:
        dp = _object(der, f"{w}.derivation", ("input_assertion_ids", "method"))
        derivation = Derivation(_strings(dp["input_assertion_ids"], f"{w}.derivation"), _string(dp["method"], w))
    try:
        return Assertion(
            assertion_id=_string(p["assertion_id"], f"{w}.assertion_id"),
            subject=_ref_from(p["subject"], f"{w}.subject"),
            field_path=_string(p["field_path"], f"{w}.field_path"),
            value=_value_from(p["value"], f"{w}.value"),
            value_as_printed=_string(p["value_as_printed"], w),
            unit_as_printed=_string(p["unit_as_printed"], w),
            conditions=_conditions_from(p["conditions"], f"{w}.conditions"),
            value_kind=_enum(ValueKind, p["value_kind"], f"{w}.value_kind"),
            status=_opt_enum(ValueStatus, p["status"], f"{w}.status"),
            admissibility=_enum(Admissibility, p["admissibility"], f"{w}.admissibility"),
            source_id=_string(p["source_id"], w), locator=_string(p["locator"], w),
            access=_enum(SourceAccess, p["access"], f"{w}.access"),
            operating_point_id=_opt_string(p["operating_point_id"], w),
            epoch=_opt_string(p["epoch"], w), normalized=normalized,
            first_stated_by=_opt_string(p["first_stated_by"], w),
            schematic_id=_opt_string(p["schematic_id"], w), derivation=derivation,
            note=_string(p["note"], w))
    except EvidenceSchemaError:
        raise
    except EvidenceError as exc:
        raise EvidenceError(f"{w}: {exc}") from None


def _assertion_to(a: Assertion) -> dict[str, Any]:
    return {
        "assertion_id": a.assertion_id, "subject": _ref_to(a.subject), "field_path": a.field_path,
        "value": _value_to(a.value), "value_as_printed": a.value_as_printed,
        "unit_as_printed": a.unit_as_printed, "conditions": _conditions_to(a.conditions),
        "value_kind": a.value_kind.value, "status": _ev(a.status), "admissibility": a.admissibility.value,
        "source_id": a.source_id, "locator": a.locator, "access": a.access.value,
        "operating_point_id": a.operating_point_id, "epoch": a.epoch,
        "normalized": None if a.normalized is None else {
            "value": _value_to(a.normalized.value), "unit": a.normalized.unit, "method": a.normalized.method},
        "first_stated_by": a.first_stated_by, "schematic_id": a.schematic_id,
        "derivation": None if a.derivation is None else {
            "input_assertion_ids": list(a.derivation.input_assertion_ids), "method": a.derivation.method},
        "note": a.note,
    }


def _conflict_from(v: Any, w: str) -> Conflict:
    p = _object(v, w, ("conflict_id", "field_path", "assertion_ids", "resolution", "categories",
                       "explanation", "preferred_assertion_id"))
    return Conflict(
        _string(p["conflict_id"], w), _string(p["field_path"], w), _strings(p["assertion_ids"], w),
        _enum(ConflictResolution, p["resolution"], f"{w}.resolution"),
        tuple(_enum(ConflictCategory, x, f"{w}.categories") for x in _list(p["categories"], f"{w}.categories")),
        _string(p["explanation"], w), _opt_string(p["preferred_assertion_id"], w))


# ---------------------------------------------------------------- corpus


_READERS = {
    "sources": _source_from, "families": _family_from, "variants": _variant_from,
    "configurations": _configuration_from, "operating_points": _point_from, "units": _unit_from,
    "aliases": _alias_from, "lineage": _lineage_from, "components": _component_from,
    "schematics": _schematic_from, "topologies": _topology_from, "assertions": _assertion_from,
    "conflicts": _conflict_from,
}


def corpus_from_dict(payload: Any) -> EngineEvidenceCorpus:
    """A corpus from its parsed JSON object: schema-checked, then cross-checked."""
    if not isinstance(payload, dict):
        raise EvidenceSchemaError("engine evidence must be a JSON object")
    if payload.get("format") != ENGINE_EVIDENCE_FORMAT:
        raise EvidenceSchemaError(
            f"not engine evidence: format must be {ENGINE_EVIDENCE_FORMAT!r}, got {payload.get('format')!r}")
    version = payload.get("schema_version")
    if isinstance(version, bool) or version != ENGINE_EVIDENCE_SCHEMA_VERSION:
        raise EvidenceSchemaError(
            f"engine evidence schema_version {version!r} is not supported; this build reads "
            f"version {ENGINE_EVIDENCE_SCHEMA_VERSION} only")
    payload = _object(payload, "engine evidence", _TOP)
    parts = {}
    for name in _COLLECTIONS:
        items = _list(payload[name], name)
        parts[name] = tuple(_READERS[name](item, f"{name}[{i}]") for i, item in enumerate(items))
    return EngineEvidenceCorpus(**parts)


def corpus_from_json(text: str) -> EngineEvidenceCorpus:
    """Parse and validate an engine-evidence document."""
    return corpus_from_dict(_parse(text))


def corpus_to_dict(corpus: EngineEvidenceCorpus) -> dict[str, Any]:
    """The corpus as a JSON object, collections and fields in canonical order."""
    def simple(item, fields):
        out = {}
        for f in fields:
            v = getattr(item, f)
            if isinstance(v, Missing):
                v = _missing_to(v)
            elif isinstance(v, StrEnum):
                v = v.value
            elif isinstance(v, tuple):
                v = list(v)
            out[f] = v
        return out

    return {
        "format": ENGINE_EVIDENCE_FORMAT,
        "schema_version": ENGINE_EVIDENCE_SCHEMA_VERSION,
        "sources": [_source_to(s) for s in corpus.sources],
        "families": [simple(x, ("family_id", "name", "notes")) for x in corpus.families],
        "variants": [simple(x, ("variant_id", "family_id", "designation", "notes")) for x in corpus.variants],
        "configurations": [simple(x, ("configuration_id", "variant_id", "label", "effective", "notes"))
                           for x in corpus.configurations],
        "operating_points": [simple(x, ("operating_point_id", "configuration_id", "label", "notes"))
                             for x in corpus.operating_points],
        "units": [{"unit_id": u.unit_id, "kind": u.kind.value, "designation": u.designation,
                   "members": [{"member": _ref_to(m.member),
                                "count": _missing_to(m.count) if isinstance(m.count, Missing) else m.count,
                                "role": m.role} for m in u.members],
                   "notes": u.notes} for u in corpus.units],
        "aliases": [{"alias_id": a.alias_id, "name": a.name, "kind": a.kind.value, "target": _ref_to(a.target),
                     "source_ids": list(a.source_ids), "ambiguous": a.ambiguous, "notes": a.notes}
                    for a in corpus.aliases],
        "lineage": [{"lineage_id": e.lineage_id, "kind": e.kind.value, "source": _ref_to(e.source),
                     "target": _ref_to(e.target), "source_ids": list(e.source_ids), "notes": e.notes}
                    for e in corpus.lineage],
        "components": [{"component_id": x.component_id, "scope": _ref_to(x.scope),
                        "component_type": x.component_type.value, "label": x.label,
                        "ownership": x.ownership.value, "part_ids": list(x.part_ids), "notes": x.notes}
                       for x in corpus.components],
        "schematics": [simple(x, ("schematic_id", "source_id", "locator", "title_as_printed", "provenance",
                                  "drawn_by", "legibility", "notes")) for x in corpus.schematics],
        "topologies": [_topology_to(t) for t in corpus.topologies],
        "assertions": [_assertion_to(a) for a in corpus.assertions],
        "conflicts": [{"conflict_id": x.conflict_id, "field_path": x.field_path,
                       "assertion_ids": list(x.assertion_ids), "resolution": x.resolution.value,
                       "categories": [k.value for k in x.categories], "explanation": x.explanation,
                       "preferred_assertion_id": x.preferred_assertion_id} for x in corpus.conflicts],
    }


def corpus_to_json(corpus: EngineEvidenceCorpus) -> str:
    """Canonical JSON text: two-space indent, UTF-8, final newline."""
    return json.dumps(corpus_to_dict(corpus), indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def corpus_fingerprint(corpus: EngineEvidenceCorpus) -> str:
    """SHA-256 of the compact, sorted-key JSON of :func:`corpus_to_dict`."""
    payload = json.dumps(corpus_to_dict(corpus), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
