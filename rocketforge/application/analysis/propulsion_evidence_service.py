"""The Propulsion Database, read-only: the shipped evidence corpus, as rows a view can show.

Everything here reads :mod:`rocketforge.evidence`, the accepted schema-version-1
records, and nothing else. It locates the shipped files, hands their text to the
evidence loader, filters the records a person asked for, and turns a record into
plain rows -- a stored value as its exact stored text, the unit as the source
printed it, the source and the place in it, and an explicit reason wherever a
field has no value. It imports no physics, no provider and no comparison code,
so browsing evidence can never solve anything.

Three things are deliberately not done here:

* **No conversion.** A value is shown as it is stored, in the unit the source
  printed. There is no SI column, because a converted number would be a second
  number, and evidence keeps one.
* **No verdict.** The four dimensions (VA thermochemistry, VB burn rate, VC
  internal ballistics, VD motor performance) stay four statuses. Nothing counts,
  ranks or combines them.
* **No execution.** A record's ``executable_key`` is stored metadata. Whether a
  formulation can be posed to a provider is a separate question, asked only
  when a person asks it, by :mod:`.evidence_cea_bridge`. Nothing here asks it:
  this module only holds the words a view uses for the answer, and the one
  part of it that needs no provider (the record gate, :func:`is_cea_target`).
"""

from __future__ import annotations

import pathlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from rocketforge.evidence import (
    CustomDefinition,
    Datum,
    Dimension,
    EvidenceError,
    EvidenceRecord,
    EvidenceStatus,
    Missing,
    RecordKind,
    ReportedValue,
    ShippingPolicy,
    SourceReference,
    record_from_json,
    reported_values,
    sources_from_json,
)

from ..data_paths import data_root

__all__ = [
    "DIMENSION_NAMES",
    "EvidenceCorpus",
    "RecordFilter",
    "evidence_root",
    "load_corpus",
    "filter_records",
    "filter_options",
    "shipping_policies",
    "stored_text",
    "datum_entries",
    "library_rows",
    "capability_rows",
    "composition_rows",
    "missing_rows",
    "rights_rows",
    "table_rows",
    "TABLE_COLUMNS",
    "payload_note",
    "record_readout",
    "datum_readout",
    "NOT_CHECKED",
    "NOT_A_CEA_TARGET",
    "NOT_EVALUATED",
    "is_cea_target",
    "compatibility_label",
    "compatibility_tone",
    "compatibility_meaning",
    "compatibility_section",
]

#: What each dimension is about, in words. The schema's own comments name them.
DIMENSION_NAMES = {
    Dimension.VA: "Thermochemistry",
    Dimension.VB: "Burn rate",
    Dimension.VC: "Internal ballistics",
    Dimension.VD: "Motor performance",
}

#: Library sections, one per record kind that is actually present.
_SECTION_NAMES = {RecordKind.PROPELLANT: "Propellants", RecordKind.REFERENCE: "References"}

#: What a shipping policy means for what this build shows. Worded from
#: ShippingPolicy's own definition: only VALUES_WITH_ATTRIBUTION lets a record
#: carry values; every other policy permits metadata only.
_SHIPPING_MEANING = {
    ShippingPolicy.VALUES_WITH_ATTRIBUTION: "values may ship, with attribution",
    ShippingPolicy.METADATA_ONLY: "metadata only: citation and locator, no values ship",
    ShippingPolicy.RESTRICTED_REFERENCE: ("restricted reference: public capability and "
                                          "access information only, no values ship"),
    ShippingPolicy.LICENSED_PROVIDER: ("licensed provider: not bundled with RocketForge, "
                                       "and no installation is detected or implied"),
    ShippingPolicy.RIGHTS_REVIEW_REQUIRED: ("rights not yet reviewed: values are withheld "
                                            "until they are"),
}

#: Statuses that say a dimension cannot be used as it stands. Shown as a
#: caution, never as an error: they describe the evidence, not a failure.
_CAUTION = {EvidenceStatus.UNDERDEFINED, EvidenceStatus.ACCESS_BLOCKED}


def evidence_root() -> pathlib.Path:
    """Where the shipped evidence lives: ``rocketforge/data/evidence``.

    Beside the published reference tables, and found the same way -- through
    :func:`~rocketforge.application.data_paths.data_root`, the application's
    rule for where a frozen build unpacks its data -- without importing
    anything that solves.
    """
    return data_root() / "evidence"


@dataclass(frozen=True, slots=True)
class EvidenceCorpus:
    """The shipped sources and records, as the EV-1 loader returned them."""

    sources: Mapping[str, SourceReference]
    records: tuple[EvidenceRecord, ...]

    def record(self, record_id: str) -> EvidenceRecord | None:
        for record in self.records:
            if record.record_id == record_id:
                return record
        return None


def load_corpus(root: pathlib.Path | None = None) -> EvidenceCorpus:
    """Load ``sources.json`` and every ``records/*.json`` under ``root``.

    Strict, like the loader it calls: a malformed file raises
    :class:`~rocketforge.evidence.EvidenceError` rather than being skipped, and
    a record whose ``record_id`` differs from its file name is refused, so a
    mis-named file cannot pass as another record. Records come back sorted by
    ``record_id``. An absent ``records`` folder is an empty corpus, not an error.
    """
    root = evidence_root() if root is None else pathlib.Path(root)
    registry = root / "sources.json"
    if not registry.is_file():
        raise EvidenceError(f"no evidence source registry at {registry}")
    sources = sources_from_json(registry.read_text(encoding="utf-8"))
    records: list[EvidenceRecord] = []
    folder = root / "records"
    if folder.is_dir():
        for path in sorted(folder.glob("*.json")):
            record = record_from_json(path.read_text(encoding="utf-8"), sources)
            if record.record_id != path.stem:
                raise EvidenceError(
                    f"{path.name} holds record {record.record_id!r}; a record file is "
                    "named by its record_id")
            records.append(record)
    records.sort(key=lambda r: r.record_id)
    return EvidenceCorpus(sources=dict(sources), records=tuple(records))


# ------------------------------------------------------------------ filters


@dataclass(frozen=True, slots=True)
class RecordFilter:
    """What a person asked to see. ``None`` is "any".

    ``status`` matches a record whose capability, in ``dimension`` (or in any
    dimension when ``dimension`` is None), is exactly that status. ``shipping``
    matches a record that cites a source with that policy. A dimension on its
    own selects nothing: it only scopes the status.
    """

    dimension: Dimension | None = None
    status: EvidenceStatus | None = None
    shipping: ShippingPolicy | None = None

    @property
    def active(self) -> bool:
        return self.status is not None or self.shipping is not None


def shipping_policies(record: EvidenceRecord,
                      sources: Mapping[str, SourceReference]) -> tuple[ShippingPolicy, ...]:
    """The distinct shipping policies of the sources a record cites, in enum order."""
    present = {sources[sid].shipping for sid in record.source_ids if sid in sources}
    return tuple(policy for policy in ShippingPolicy if policy in present)


def filter_records(corpus: EvidenceCorpus, selection: RecordFilter) -> tuple[EvidenceRecord, ...]:
    """The records that match, in corpus order. Reads fields; changes nothing."""
    out = []
    for record in corpus.records:
        if selection.status is not None:
            scope = (selection.dimension,) if selection.dimension is not None else tuple(Dimension)
            if not any(record.capabilities[d] is selection.status for d in scope):
                continue
        if selection.shipping is not None and \
                selection.shipping not in shipping_policies(record, corpus.sources):
            continue
        out.append(record)
    return tuple(out)


def filter_options(corpus: EvidenceCorpus) -> dict[str, list[dict]]:
    """The choices a filter can offer, taken from the records that exist.

    The four dimensions are the schema's own, so all four are always offered;
    statuses and shipping policies are offered only when some record has them.
    """
    statuses = {s for r in corpus.records for s in r.capabilities.values()}
    policies = {p for r in corpus.records for p in shipping_policies(r, corpus.sources)}
    return {
        "dimension": [{"key": d.value, "label": f"{d.value} · {DIMENSION_NAMES[d]}"}
                      for d in Dimension],
        "status": [{"key": s.value, "label": status_label(s)}
                   for s in EvidenceStatus if s in statuses],
        "shipping": [{"key": p.value, "label": p.value} for p in ShippingPolicy if p in policies],
    }


# --------------------------------------------------------------- formatting


def status_label(status: EvidenceStatus) -> str:
    """``REGRESSION_LOCKED`` -> ``Regression locked``: the enum's words, nothing added."""
    return status.value.replace("_", " ").capitalize()


def status_tone(status: EvidenceStatus) -> str:
    """The status chip's dot. Words carry the meaning; the dot never ranks.

    Every status that describes available evidence is neutral; a status that
    says the evidence cannot be used as it stands is a caution. NOT_APPLICABLE
    has no dot at all (``"none"``): it is not a state of the evidence but a
    statement that the dimension does not apply.
    """
    if status is EvidenceStatus.NOT_APPLICABLE:
        return "none"
    if status in _CAUTION:
        return "warning"
    return "neutral"


def stored_text(value: float) -> str:
    """A stored value exactly as stored: Python's shortest round-trip form.

    ``0.7206`` stays ``0.7206`` and ``1.0`` stays ``1.0``. No rounding to a
    display precision, which would claim a precision the source did not print.
    """
    return repr(float(value))


def missing_text(datum: Missing) -> str:
    return f"Missing · {datum.reason.value}"


def _precision_text(datum: ReportedValue) -> str:
    if datum.decimals is not None:
        return f"{datum.decimals} decimals as printed"
    if datum.significant_figures is not None:
        return f"{datum.significant_figures} significant figures as printed"
    return "not stated"


# ------------------------------------------------------------ datum entries


@dataclass(frozen=True, slots=True)
class DatumEntry:
    """One field of a record, with the path that names it."""

    key: str            # stable path, e.g. "ingredients[1].custom.enthalpy"
    label: str          # what a reader calls it
    datum: Datum


def datum_entries(record: EvidenceRecord) -> tuple[DatumEntry, ...]:
    """Every scientific field in a record, reported or missing, in a stable order."""
    propellant = record.propellant
    if propellant is None:
        return ()
    out: list[DatumEntry] = []
    for index, item in enumerate(propellant.ingredients):
        base = f"ingredients[{index}]"
        out.append(DatumEntry(f"{base}.fraction", f"{item.source_name} · fraction", item.fraction))
        if item.custom is not None:
            out.extend(_custom_entries(item.custom, f"{base}.custom", item.source_name))
    out.append(DatumEntry("density", "Density", propellant.density))
    out.append(DatumEntry("initial_temperature", "Initial temperature",
                          propellant.initial_temperature))
    return tuple(out)


def _custom_entries(custom: CustomDefinition, base: str, name: str) -> list[DatumEntry]:
    out: list[DatumEntry] = []
    if isinstance(custom.formula, Missing):
        out.append(DatumEntry(f"{base}.formula", f"{name} · formula", custom.formula))
    else:
        for element, count in custom.formula.items():
            out.append(DatumEntry(f"{base}.formula.{element}", f"{name} · atoms of {element}", count))
    out.append(DatumEntry(f"{base}.enthalpy", f"{name} · assigned enthalpy", custom.enthalpy))
    out.append(DatumEntry(f"{base}.reference_temperature", f"{name} · reference temperature",
                          custom.reference_temperature))
    out.append(DatumEntry(f"{base}.molecular_weight", f"{name} · molecular weight",
                          custom.molecular_weight))
    return out


def _entry(record: EvidenceRecord, key: str) -> DatumEntry | None:
    for entry in datum_entries(record):
        if entry.key == key:
            return entry
    return None


# --------------------------------------------------------------- row builders


def library_rows(records: Iterable[EvidenceRecord]) -> list[dict]:
    """The library list: one row per record, grouped by the kinds present."""
    rows = []
    previous = None
    for record in sorted(records, key=lambda r: (list(RecordKind).index(r.kind), r.record_id)):
        section = _SECTION_NAMES[record.kind]
        rows.append({
            "recordId": record.record_id,
            "title": record.title,
            "section": section,
            "sectionStart": section != previous,
            # non-breaking inside each dimension, so a line wraps between
            # dimensions and never through a status
            "capabilities": "  ·  ".join(
                f"{d.value} {status_label(record.capabilities[d])}".replace(" ", " ")
                for d in Dimension),
        })
        previous = section
    return rows


def capability_rows(record: EvidenceRecord) -> list[dict]:
    """The four dimensions, each on its own: never counted, never combined."""
    return [{
        "dimension": d.value,
        "dimensionName": DIMENSION_NAMES[d],
        "status": record.capabilities[d].value,
        "statusLabel": status_label(record.capabilities[d]),
        "tone": status_tone(record.capabilities[d]),
        "applicable": record.capabilities[d] is not EvidenceStatus.NOT_APPLICABLE,
        "note": record.capability_notes.get(d, ""),
    } for d in Dimension]


def composition_rows(record: EvidenceRecord) -> list[dict]:
    """Ingredients as the source lists them. The bar is the stored fraction itself.

    ``share`` is the stored mass fraction when it is reported (0..1 of the bar,
    never renormalised) and -1 when the fraction is missing, so a missing share
    draws no bar at all rather than a zero-width one.
    """
    propellant = record.propellant
    if propellant is None:
        return []
    rows = []
    for index, item in enumerate(propellant.ingredients):
        fraction = item.fraction
        reported = isinstance(fraction, ReportedValue)
        rows.append({
            "key": f"ingredients[{index}].fraction",
            "name": item.source_name,
            "definition": ("source-defined ingredient (formula, enthalpy and reference "
                           "temperature as the source states them)"
                           if item.custom is not None else ""),
            "valueText": stored_text(fraction.value) if reported else missing_text(fraction),
            "unit": fraction.unit if reported else "",
            "valueStatus": fraction.status.value if reported else fraction.reason.value,
            "missing": not reported,
            "share": fraction.value if reported and 0.0 <= fraction.value <= 1.0 else -1.0,
        })
    return rows


def missing_rows(record: EvidenceRecord) -> list[dict]:
    """Every field the record deliberately has no value for, with its reason."""
    return [{"key": e.key, "field": e.label, "reason": e.datum.reason.value,
             "note": e.datum.note}
            for e in datum_entries(record) if isinstance(e.datum, Missing)]


def rights_rows(record: EvidenceRecord, sources: Mapping[str, SourceReference]) -> list[dict]:
    """Each cited source whose policy withholds values, with what that means."""
    return [{"sourceId": sid, "policy": sources[sid].shipping.value,
             "meaning": _SHIPPING_MEANING[sources[sid].shipping]}
            for sid in record.source_ids
            if sid in sources and not sources[sid].values_may_ship]


#: The source-value table. Only columns every row can fill honestly.
TABLE_COLUMNS = [
    {"key": "field", "label": "Field", "align": "left", "kind": "text"},
    {"key": "value", "label": "Stored value", "kind": "text"},
    {"key": "unit", "label": "Unit (as printed)", "align": "left", "kind": "text"},
    {"key": "status", "label": "Status", "align": "left", "kind": "text"},
    {"key": "source", "label": "Source", "align": "left", "kind": "text"},
    {"key": "locator", "label": "Locator", "align": "left", "kind": "text"},
]


def table_rows(record: EvidenceRecord) -> tuple[list[str], list[tuple]]:
    """(keys, rows) for the source-value table: every field, reported or missing."""
    keys, rows = [], []
    for entry in datum_entries(record):
        datum = entry.datum
        keys.append(entry.key)
        if isinstance(datum, ReportedValue):
            rows.append((entry.label, stored_text(datum.value), datum.unit,
                         datum.status.value, datum.source_id, datum.locator))
        else:
            # no source and no locator: there is no value to locate. The
            # reason is the status; its note is in the inspector.
            rows.append((entry.label, "Missing", "", datum.reason.value, "", ""))
    return keys, rows


def payload_note(record: EvidenceRecord, sources: Mapping[str, SourceReference]) -> str:
    """Why the source-value table is empty, when it is. Empty when it is not."""
    if reported_values(record):
        return ""
    policies = shipping_policies(record, sources)
    withheld = [p for p in policies if p is not ShippingPolicy.VALUES_WITH_ATTRIBUTION]
    if record.propellant is None and not withheld:
        return "No numerical payload: this record describes a source, not a formulation."
    if withheld:
        return ("No redistributable numerical payload: "
                + "; ".join(f"{p.value}, {_SHIPPING_MEANING[p]}" for p in withheld) + ".")
    return "No reported values: every field of this record is missing, with its reason."


# ------------------------------------------------------------------ readouts


def _source_rows(source: SourceReference) -> list[dict]:
    rows = [
        {"label": "Title", "value": source.title},
        {"label": "Organization", "value": source.organization},
    ]
    if source.authors:
        rows.append({"label": "Authors", "value": "; ".join(source.authors)})
    rows.append({"label": "Year", "value": str(source.year) if source.year is not None
                 else "not stated"})
    for kind, ident in source.identifiers.items():
        rows.append({"label": kind.replace("_", " ").capitalize(), "value": ident})
    rows += [
        {"label": "Locator", "value": source.locator},
        {"label": "Source type", "value": source.source_type},
        {"label": "Access", "value": source.access_class.value},
        {"label": "Shipping", "value": f"{source.shipping.value} · {_SHIPPING_MEANING[source.shipping]}"},
        {"label": "Rights", "value": source.rights_statement},
        {"label": "Tier", "value": str(source.tier)},
    ]
    return rows


def record_readout(record: EvidenceRecord, sources: Mapping[str, SourceReference]) -> dict:
    """The record itself, for the inspector: identity, sources, notes."""
    sections = [{"title": "Record", "rows": [
        {"label": "Record id", "value": record.record_id},
        {"label": "Kind", "value": record.kind.value},
        {"label": "Sources", "value": ", ".join(record.source_ids)},
    ] + ([{"label": "Comparison cases", "value": ", ".join(record.comparison_case_ids)}]
         if record.comparison_case_ids else []) + ([{
             "label": "Executable key",
             "value": f"{record.executable_key} (stored reference to an existing executable "
                      "case; browsing never assesses or runs it)"}]
             if record.executable_key else [])}]
    if record.propellant is not None:
        p = record.propellant
        sections.append({"title": "Formulation", "rows": [
            {"label": "Source name", "value": p.source_name},
            {"label": "Family", "value": p.family},
            {"label": "Basis", "value": p.basis},
            {"label": "Exact formulation", "value": "yes" if p.exact_formulation else "no"},
            {"label": "Cites", "value": ", ".join(p.source_ids)},
        ]})
    for sid in record.source_ids:
        if sid in sources:
            sections.append({"title": sid, "rows": _source_rows(sources[sid])})
    if record.notes:
        sections.append({"title": "Notes", "rows": [{"label": "", "value": record.notes}]})
    return {"kind": "record", "key": "", "title": record.title, "subtitle": record.record_id,
            "sections": sections}


def datum_readout(record: EvidenceRecord, sources: Mapping[str, SourceReference],
                  key: str) -> dict:
    """One field, for the inspector: its stored value and everything about where it is from."""
    entry = _entry(record, key)
    if entry is None:
        return {}
    datum = entry.datum
    if isinstance(datum, Missing):
        rows = [{"label": "Value", "value": "none -- this field is explicitly missing"},
                {"label": "Missing reason", "value": datum.reason.value}]
        if datum.note:
            rows.append({"label": "Note", "value": datum.note})
        return {"kind": "datum", "key": key, "title": entry.label, "subtitle": record.record_id,
                "sections": [{"title": "Missing", "rows": rows}]}
    rows = [
        {"label": "Stored value", "value": stored_text(datum.value)},
        {"label": "Unit (as printed)", "value": datum.unit},
        {"label": "Value status", "value": datum.status.value},
        {"label": "Printed precision", "value": _precision_text(datum)},
        {"label": "Locator", "value": datum.locator},
    ]
    if datum.note:
        rows.append({"label": "Note", "value": datum.note})
    sections = [{"title": "Value", "rows": rows}]
    if datum.source_id in sources:
        sections.append({"title": datum.source_id, "rows": _source_rows(sources[datum.source_id])})
    return {"kind": "datum", "key": key, "title": entry.label, "subtitle": record.record_id,
            "sections": sections}


# ------------------------------------------------------- CEA compatibility (EV-3)
#
# The words for the answer to "can NASA CEA take this formulation?". The answer
# itself is computed only on request, by evidence_cea_bridge.assess(), which
# probes the installed library; nothing in this module probes anything. What is
# here is the vocabulary (R1 integration blueprint section 4) and the one step
# that needs no provider: the record gate.

#: A CEA-target record nobody has asked about yet. Neutral: no claim either way.
NOT_CHECKED = "NOT_CHECKED"

#: R1 section 4, step 1: no formulation, or thermochemistry does not apply.
NOT_A_CEA_TARGET = "NOT_A_CEA_TARGET"

#: A check that stopped at the access gate: values it needs are withheld by
#: shipping policy, so compatibility was not evaluated. A presentation state,
#: like NOT_CHECKED -- not one of the bridge's scientific states.
NOT_EVALUATED = "NOT_EVALUATED"

#: state -> (label, tone, meaning). The label and the meaning carry the state;
#: the tone drives a status dot only, so colour never carries it alone.
_COMPATIBILITY_WORDS = {
    NOT_CHECKED: (
        "Not checked", "none",
        "Nothing has been probed. A check asks the NASA CEA library of this "
        "environment, if there is one, whether this formulation can be posed to "
        "it. It solves nothing."),
    NOT_A_CEA_TARGET: (
        "Not a CEA target", "none",
        "There is no formulation to pose to NASA CEA: the record states no "
        "propellant, or thermochemistry (VA) does not apply to it."),
    "UNDERDEFINED": (
        "Underdefined", "warning",
        "The evidence does not define the formulation completely. Nothing is "
        "completed, normalised or substituted."),
    "BLOCKED_INCOMPLETE_CUSTOM": (
        "Blocked · incomplete custom thermochemistry", "warning",
        "A source-defined ingredient lacks thermochemical data NASA CEA needs. "
        "Nothing is substituted for it."),
    "BLOCKED": (
        "Blocked", "warning",
        "The formulation is defined, but not in a form the installed NASA CEA "
        "library takes as stated."),
    NOT_EVALUATED: (
        "Not evaluated · access restricted", "neutral",
        "The check stopped at the access gate: values it needs are withheld by "
        "shipping policy. NASA CEA compatibility was not evaluated -- nothing was "
        "probed, and this says nothing about the chemistry."),
    "PROVIDER_UNAVAILABLE": (
        "Provider unavailable", "neutral",
        "NASA CEA is not usable in this environment, so no library name was "
        "checked. Nothing in the record blocks it."),
    "EXECUTABLE_VERIFIED": (
        "Executable · verified", "success",
        "Every ingredient is a library species in the probed thermo.lib or a "
        "source-complete custom reactant, and the record is regression-locked "
        "against a published case."),
    "EXECUTABLE_SOURCE_COMPLETE": (
        "Executable · source complete", "success",
        "Every ingredient is a library species in the probed thermo.lib or a "
        "source-complete custom reactant. The record is not regression-locked "
        "against a published case."),
}


def is_cea_target(record: EvidenceRecord) -> bool:
    """R1 section 4, step 1, from the record alone: a formulation, and VA applies.

    Pure evidence data -- no provider is asked -- so a view may state
    NOT_A_CEA_TARGET before any check, and offer no check for it.
    """
    return (record.propellant is not None
            and record.capabilities[Dimension.VA] is not EvidenceStatus.NOT_APPLICABLE)


def compatibility_label(state: str) -> str:
    return _COMPATIBILITY_WORDS.get(state, (state, "none", ""))[0]


def compatibility_tone(state: str) -> str:
    return _COMPATIBILITY_WORDS.get(state, (state, "none", ""))[1]


def compatibility_meaning(state: str) -> str:
    return _COMPATIBILITY_WORDS.get(state, (state, "none", ""))[2]


def compatibility_section(state: str, *, blockers: Iterable[Mapping] = (),
                          identity: str = "", notes: Iterable[str] = (),
                          open_note: str = "",
                          restrictions: Iterable[Mapping] = ()) -> dict:
    """The Inspector's "CEA compatibility" section, from prepared words only.

    ``blockers`` are rows with ``code`` and ``text``; ``identity`` is the
    provider and database actually probed (empty when nothing was).
    """
    rows = [{"label": "State", "value": compatibility_label(state)},
            {"label": "Meaning", "value": compatibility_meaning(state)}]
    rows += [{"label": "Access", "value": row["text"]} for row in restrictions]
    rows += [{"label": row["code"].replace("_", " ").capitalize(), "value": row["text"]}
             for row in blockers]
    if identity:
        rows.append({"label": "Provider", "value": identity})
    rows += [{"label": "Note", "value": note} for note in notes]
    if open_note:
        rows.append({"label": "Thermochemistry", "value": open_note})
    return {"title": "CEA compatibility", "rows": rows}
