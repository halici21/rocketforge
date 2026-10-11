"""What the Reference Engines workspace shows, prepared from the shipped catalog (DB-3A).

Pure presentation: every function here reads a loaded
:class:`~.reference_engine_catalog.ReferenceEngineCatalog` and returns plain
dicts and lists of display strings. No Qt, no provider, no physics, no network,
no unit conversion, and no value that the corpus does not hold. QML lays these
out; it never parses evidence or decides what a state means.

The rules this module keeps, because the evidence model makes them:

* A value is shown as the source printed it (``value_as_printed`` and
  ``unit_as_printed``). Nothing is converted, rounded or filled in.
* A condition the corpus records as UNKNOWN is shown as unknown. A condition
  the corpus does not carry (``None``) is not shown at all, never as unknown.
* What is recorded for a variant or family is context, never a value of the
  configuration, and is listed apart from it.
* The five capabilities are reported one by one in the backend's own words; no
  score, count or overall grade is made from them.
* A topology graph is drawn from its nodes and edges only. Where it sits on the
  screen is a RocketForge layout for readability (:func:`layout_graph`); the
  connectivity is the evidence.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from rocketforge.evidence import Missing
from rocketforge.evidence.engines import (
    Assertion,
    EdgeKind,
    EngineSource,
    EnumValue,
    NumberValue,
    SubjectKind,
    TextValue,
    TopologyGraph,
)
from rocketforge.evidence.engines.capabilities import Capability, CapabilityResult

from .reference_engine_catalog import ReferenceEngineCatalog

__all__ = [
    "CAPABILITY_ORDER", "CAPABILITY_NAMES", "STATUS_WORDS", "TABLE_COLUMNS", "CONNECTION_COLUMNS",
    "EngineFilter", "filter_options", "visible_entries", "library_rows", "filter_summary",
    "identity", "capability_rows", "capability_readout", "fact_groups", "missing_rows",
    "context_rows", "source_rows", "assertion_table", "assertion_readout", "source_readout",
    "configuration_readout", "graph_views", "layout_graph", "node_readout", "edge_readout",
    "graph_readout", "connection_table", "display_value", "reading", "condition_items", "FACT_GROUPS",
    "unit_assertions", "context_assertions",
]

CAPABILITY_ORDER = (Capability.IDENTITY, Capability.ARCHITECTURE, Capability.PERFORMANCE_REFERENCE,
                    Capability.TOPOLOGY, Capability.REGRESSION_CANDIDATE)
CAPABILITY_NAMES = {
    Capability.IDENTITY: "Identity",
    Capability.ARCHITECTURE: "Architecture",
    Capability.PERFORMANCE_REFERENCE: "Performance reference",
    Capability.TOPOLOGY: "Topology",
    Capability.REGRESSION_CANDIDATE: "Regression candidate",
}
#: What each capability means, in one line, so a status word is never read alone.
CAPABILITY_MEANINGS = {
    Capability.IDENTITY: "The record says which engine configuration this is.",
    Capability.ARCHITECTURE: "Propellants and cycle or feed are recorded for this configuration.",
    Capability.PERFORMANCE_REFERENCE: "Thrust, specific impulse, chamber pressure, mixture ratio and nozzle "
                                      "area ratio are recorded for this configuration.",
    Capability.TOPOLOGY: "A component graph of this configuration ships, and whether it rests on an "
                         "original drawing.",
    Capability.REGRESSION_CANDIDATE: "Eligibility only: whether the record could later be offered as a "
                                     "regression reference. No regression is accepted, locked or run.",
}
#: The backend's statuses, in words. Evidence states, not failures.
STATUS_WORDS = {"SUPPORTED": "Supported", "PARTIAL": "Partial", "NOT_SUPPORTED": "Not supported"}
#: A shape that carries the status without colour (filled, half, open).
STATUS_GLYPHS = {"SUPPORTED": "■", "PARTIAL": "◧", "NOT_SUPPORTED": "□"}

TABLE_COLUMNS = [
    {"key": "field", "label": "Field", "align": "left", "kind": "text"},
    {"key": "value", "label": "As printed", "align": "left", "kind": "text"},
    {"key": "recorded", "label": "Recorded as", "align": "left", "kind": "text"},
    {"key": "unit", "label": "Unit (as printed)", "align": "left", "kind": "text"},
    {"key": "kind", "label": "Value kind", "align": "left", "kind": "text"},
    {"key": "conditions", "label": "Conditions", "align": "left", "kind": "text"},
    {"key": "point", "label": "Operating point", "align": "left", "kind": "text"},
    {"key": "status", "label": "Status", "align": "left", "kind": "text"},
    {"key": "source", "label": "Source", "align": "left", "kind": "text"},
    {"key": "locator", "label": "Locator", "align": "left", "kind": "text"},
]
CONNECTION_COLUMNS = [
    {"key": "from", "label": "From", "align": "left", "kind": "text"},
    {"key": "to", "label": "To", "align": "left", "kind": "text"},
    {"key": "kind", "label": "Relationship", "align": "left", "kind": "text"},
    {"key": "carrier", "label": "Carrier", "align": "left", "kind": "text"},
    {"key": "role", "label": "Role (as recorded)", "align": "left", "kind": "text"},
    {"key": "evidence", "label": "Evidence", "align": "left", "kind": "text"},
    {"key": "locator", "label": "Locator", "align": "left", "kind": "text"},
]

_EDGE_WORDS = {
    EdgeKind.FLUID_FLOW: "Fluid flow",
    EdgeKind.MECHANICAL_SHAFT: "Mechanical shaft",
    EdgeKind.GEARED_DRIVE: "Geared drive",
    EdgeKind.MECHANICAL_LINKAGE: "Mechanical linkage",
    EdgeKind.CONTROL_ACTUATION: "Control actuation",
    EdgeKind.ELECTRICAL_POWER: "Electrical power",
}


def _carrier(edge) -> str:
    """What flows: recorded for a fluid edge; a shaft, linkage or signal carries no fluid."""
    if edge.carrier:
        return edge.carrier
    return "Not recorded" if edge.kind is EdgeKind.FLUID_FLOW else "Not applicable (no fluid)"


_OWNERSHIP_WORDS = {"ENGINE": "Engine", "STAGE": "Stage", "VEHICLE": "Vehicle", "AMBIENT": "Ambient"}
_EVIDENCE_WORDS = {"SHOWN_IN_SCHEMATIC": "Shown in the drawing", "REPORTED_IN_TEXT": "Stated in the text",
                   "DERIVED_FROM_BOTH": "Drawing and text together", "INFERRED": "Inferred"}
_PROVENANCE_WORDS = {
    "ORIGINAL_MANUFACTURER": "From the manufacturer's original drawing",
    "ORIGINAL_AGENCY": "From the agency's original drawing",
    "ORIGINAL_CONTRACTOR": "From a programme contractor's original drawing",
    "THIRD_PARTY_RECONSTRUCTION": "Third-party reconstruction, not an original drawing",
}
_KIND_WORDS = {"NOMINAL": "Nominal", "RATED": "Rated", "APPROXIMATE": "Approximate", "AVERAGE": "Average",
               "MINIMUM": "Minimum", "MAXIMUM": "Maximum", "DESIGN_VALUE": "Design value", "LIMIT": "Limit",
               "TEST_RESULT": "Test result", "PREDICTION": "Prediction", "OTHER": "Other"}
_CONDITION_LABELS = (("environment", "Environment"), ("power_level", "Power level"),
                     ("mixture_ratio", "Mixture ratio setting"), ("mixture_ratio_form", "Mixture ratio form"),
                     ("mixture_ratio_basis", "Mixture ratio basis"), ("pressure_basis", "Pressure basis"),
                     ("pressure_station", "Pressure station"), ("isp_basis", "Isp basis"))
_UNKNOWN = "Unknown (not stated by the source)"


def _words(token: str) -> str:
    """An enum token as words ('SEA_LEVEL' -> 'Sea level'), for display only."""
    text = str(token).replace("_", " ").strip().lower()
    return text[:1].upper() + text[1:]


def _fold(text: str) -> str:
    return unicodedata.normalize("NFKC", str(text)).casefold()


def _missing_text(value: Missing) -> str:
    reason = _words(value.reason.value)
    return f"{reason}: {value.note}" if value.note else reason


# ------------------------------------------------------------------ values and conditions


#: Enum tokens whose plain-words spelling would mangle a name (display only).
_TOKEN_WORDS = {"RP_1": "RP-1", "AEROZINE_50": "Aerozine 50"}
#: Words for an empty column, so no cell is ever blank and nothing reads as a zero.
NO_UNIT, NO_CONDITIONS, NO_POINT = "None printed", "None recorded", "Not tied to one"


def _token(token: str) -> str:
    return _TOKEN_WORDS.get(token, _words(token))


def display_value(a: Assertion) -> str:
    """What the value is, for a table cell: the printed excerpt, or the recorded enum in words."""
    if isinstance(a.value, EnumValue):
        return _token(a.value.token)
    if isinstance(a.value, Missing):
        return _missing_text(a.value)
    return a.value_as_printed


def reading(a: Assertion) -> str:
    """The printed excerpt, with its printed unit only where the excerpt is a bare number.

    '1,748,200' with 'lb' reads '1,748,200 lb'. An excerpt that carries words
    ('10 percent of the rated thrust', 'Duty-cycle life: 1000 sec', '... 475 psia
    and O/F = 5.0') or ends in its unit ('16:1') is shown exactly as printed: the
    unit stays in the Unit column and the Inspector, never glued onto a sentence.
    """
    printed, unit = a.value_as_printed.rstrip(), (a.unit_as_printed or "").strip()
    if isinstance(a.value, EnumValue) or not unit or printed.endswith(unit) or \
            any(ch.isalpha() for ch in printed):
        return printed
    return f"{printed} {unit}"


def _exact(number: float) -> str:
    """A stored number, exactly: never '%g', which rounds past six significant digits."""
    return str(int(number)) if float(number).is_integer() else repr(float(number))


def _setting(value) -> str:
    text = f"{_exact(value.value)} {value.unit}".strip()
    return f"{text} of {value.reference}" if value.reference else text


def condition_items(a: Assertion) -> list[tuple[str, str]]:
    """(label, value) for every condition the record carries. UNKNOWN stays visible as unknown."""
    out = []
    c = a.conditions
    for attr, label in _CONDITION_LABELS:
        value = getattr(c, attr)
        if value is None:
            continue
        if hasattr(value, "unit") and hasattr(value, "reference"):
            out.append((label, _setting(value)))
            continue
        token = getattr(value, "value", value)
        out.append((label, _UNKNOWN if str(token) == "UNKNOWN" else _words(token)))
    for q in c.qualifiers:
        out.append((_words(q.name), q.value))
    return out


def _conditions_line(a: Assertion) -> str:
    items = [(label, "Unknown" if value == _UNKNOWN else value) for label, value in condition_items(a)]
    return " · ".join(f"{label}: {value}" for label, value in items) or NO_CONDITIONS


def _kind_word(a: Assertion) -> str:
    return _KIND_WORDS.get(a.value_kind.value) or _words(a.value_kind.value)


# ------------------------------------------------------------------ library


@dataclass(frozen=True)
class EngineFilter:
    """What narrows the library. Every field empty means the whole corpus."""

    search: str = ""
    capability: str = ""  # a Capability value, with ``status``
    status: str = ""      # a status the backend returns
    cycle: str = ""       # a recorded architecture.cycle token, or "NOT_RECORDED"

    @property
    def active(self) -> bool:
        return bool(self.search.strip() or (self.capability and self.status) or self.cycle)


def _cycles(catalog: ReferenceEngineCatalog, cfg: str) -> tuple[str, ...]:
    return tuple(sorted({a.value.token for a in catalog.assertions(cfg)
                         if a.field_path == "architecture.cycle" and isinstance(a.value, EnumValue)}))


def _search_keys(catalog: ReferenceEngineCatalog, entry) -> list[str]:
    names = [entry.label, entry.designation, entry.family_name, entry.configuration_id, entry.variant_id]
    for alias in catalog.corpus.aliases:
        target = alias.target
        if (target.kind is SubjectKind.VARIANT and target.id == entry.variant_id) or \
                (target.kind is SubjectKind.FAMILY and target.id == entry.family_id) or \
                (target.kind is SubjectKind.CONFIGURATION and target.id == entry.configuration_id):
            names.append(alias.name)
    return [_fold(n) for n in names]


def _sorted_entries(catalog: ReferenceEngineCatalog):
    return sorted(catalog.entries(), key=lambda e: (_fold(e.family_name), _fold(e.label), e.configuration_id))


def filter_options(catalog: ReferenceEngineCatalog) -> dict:
    """The filter choices the corpus itself supports: no status or cycle nobody holds is offered."""
    statuses = sorted({r.status.value for e in catalog.entries() for r in catalog.capabilities(e.configuration_id)},
                      key=list(STATUS_WORDS).index)
    cycles = sorted({c for e in catalog.entries() for c in _cycles(catalog, e.configuration_id)})
    return {
        "capability": [{"key": c.value, "label": CAPABILITY_NAMES[c]} for c in CAPABILITY_ORDER],
        "status": [{"key": s, "label": STATUS_WORDS[s]} for s in statuses],
        "cycle": [{"key": c, "label": _words(c)} for c in cycles]
                 + [{"key": "NOT_RECORDED", "label": "No cycle recorded"}],
    }


def visible_entries(catalog: ReferenceEngineCatalog, f: EngineFilter) -> tuple:
    """The library in its fixed order (family, then label, then id), narrowed by the filter."""
    needle = _fold(f.search.strip())
    out = []
    for entry in _sorted_entries(catalog):
        cfg = entry.configuration_id
        if needle and not any(needle in key for key in _search_keys(catalog, entry)):
            continue
        if f.capability and f.status:
            if catalog.capability(cfg, Capability(f.capability)).status.value != f.status:
                continue
        if f.cycle:
            cycles = _cycles(catalog, cfg)
            if (f.cycle == "NOT_RECORDED" and cycles) or (f.cycle != "NOT_RECORDED" and f.cycle not in cycles):
                continue
        out.append(entry)
    return tuple(out)


def filter_summary(catalog: ReferenceEngineCatalog, f: EngineFilter, visible: int) -> str:
    total = len(catalog.entries())
    parts = []
    if f.search.strip():
        parts.append(f"name contains “{f.search.strip()}”")
    if f.capability and f.status:
        parts.append(f"{CAPABILITY_NAMES[Capability(f.capability)]}: {STATUS_WORDS.get(f.status, f.status)}")
    if f.cycle:
        parts.append("no cycle recorded" if f.cycle == "NOT_RECORDED" else f"cycle: {_words(f.cycle)}")
    head = f"{visible} of {total} configurations"
    return head + (" · " + "; ".join(parts) if parts else "")


def _capability_line(catalog: ReferenceEngineCatalog, cfg: str) -> str:
    words = []
    for r in catalog.capabilities(cfg):
        name = CAPABILITY_NAMES[r.capability]
        status = r.status.value
        if status == "SUPPORTED":
            words.append(name)
        elif status == "PARTIAL":
            words.append(f"{name} (partial)")
    return " · ".join(words) if words else "No capability supported"


def library_rows(catalog: ReferenceEngineCatalog, entries) -> list[dict]:
    rows, last = [], None
    for e in entries:
        rows.append(dict(
            configurationId=e.configuration_id,
            title=e.label,
            subtitle=f"{e.designation} · {e.family_name}" if e.designation != e.family_name else e.designation,
            section=e.family_name,
            sectionStart=e.family_name != last,
            capabilities=_capability_line(catalog, e.configuration_id),
        ))
        last = e.family_name
    return rows


# ------------------------------------------------------------------ the selected configuration


def identity(catalog: ReferenceEngineCatalog, cfg: str) -> dict:
    entry = catalog.entry(cfg)
    config = next(c for c in catalog.corpus.configurations if c.configuration_id == cfg)
    variant = next(v for v in catalog.corpus.variants if v.variant_id == entry.variant_id)
    family = next(f for f in catalog.corpus.families if f.family_id == entry.family_id)
    effective = (_missing_text(config.effective) if isinstance(config.effective, Missing) else str(config.effective))
    aliases = sorted({a.name for a in catalog.corpus.aliases
                      if a.target.id in (cfg, entry.variant_id, entry.family_id)})
    return dict(
        configurationId=cfg, label=entry.label, variantId=entry.variant_id, designation=entry.designation,
        familyId=entry.family_id, familyName=entry.family_name,
        lineage=f"Variant {entry.designation} · Family {entry.family_name}",
        effective=effective, effectiveKnown=not isinstance(config.effective, Missing),
        notes=config.notes, variantNotes=variant.notes, familyNotes=family.notes,
        aliases=", ".join(aliases),
        operatingPoints=[dict(pointId=p.operating_point_id, pointLabel=p.label, pointNotes=p.notes)
                         for p in entry.operating_points],
    )


def capability_rows(catalog: ReferenceEngineCatalog, cfg: str) -> list[dict]:
    rows = []
    for r in catalog.capabilities(cfg):
        status = r.status.value
        if status == "SUPPORTED":
            summary = r.caveats[0] if r.caveats else "Recorded for this configuration."
        else:
            summary = r.gaps[0] if r.gaps else ""
        if r.capability is Capability.REGRESSION_CANDIDATE:
            summary = ("Eligible only: no regression is accepted, locked or run from this record."
                       if status == "SUPPORTED" else (r.gaps[0] if r.gaps else summary))
        rows.append(dict(
            capability=r.capability.value, name=CAPABILITY_NAMES[r.capability], status=status,
            statusLabel=STATUS_WORDS[status], glyph=STATUS_GLYPHS[status],
            summary=summary, more=max(0, len(r.gaps) - (0 if status == "SUPPORTED" else 1)),
            meaning=CAPABILITY_MEANINGS[r.capability],
        ))
    return rows


#: The record's reading groups, in order, with what each one is and is not.
FACT_GROUPS = (
    ("performance", "Performance reference values",
     "The values the performance-reference evaluation counts for this configuration: operating values "
     "and nozzle geometry."),
    ("performanceOther", "Other performance statements",
     "Recorded, but not among the quantities the performance reference counts: for example flow rates, "
     "throttle points, minimums, design values and text statements."),
    ("architecture", "Architecture and propellants", ""),
    ("other", "Other recorded facts", "Hardware, life, history and dimensions: not performance."),
)


def _group_of(a: Assertion, operating: frozenset[str]) -> str:
    path = a.field_path
    if a.assertion_id in operating:
        return "performance"
    if path.startswith("performance."):
        return "performanceOther"
    if path.startswith(("architecture.", "propellants.")):
        return "architecture"
    return "other"


def _operating_ids(catalog: ReferenceEngineCatalog, cfg: str) -> frozenset[str]:
    return frozenset(catalog.capability(cfg, Capability.PERFORMANCE_REFERENCE).assertion_ids)


def _point_label(catalog: ReferenceEngineCatalog, point_id: str | None) -> str:
    if not point_id:
        return NO_POINT
    point = next((p for p in catalog.corpus.operating_points if p.operating_point_id == point_id), None)
    return point.label if point else point_id


def _fact_row(catalog: ReferenceEngineCatalog, a: Assertion) -> dict:
    return dict(
        assertionId=a.assertion_id, field=a.field_path, valueText=reading(a),
        unit=a.unit_as_printed or NO_UNIT, kind=_kind_word(a), nominal=a.value_kind.value == "NOMINAL",
        conditions=_conditions_line(a),
        point=_point_label(catalog, a.operating_point_id), hasPoint=bool(a.operating_point_id),
        status=_words(a.status.value),
        sourceId=a.source_id, recorded=_token(a.value.token) if isinstance(a.value, EnumValue) else "",
        hasConditions=bool(condition_items(a)), unitNote=_unit_note(a),
    )


def _unit_note(a: Assertion) -> str:
    """'Unit as printed: psia' when the excerpt shown does not itself carry the unit."""
    unit = (a.unit_as_printed or "").strip()
    if not unit or isinstance(a.value, EnumValue) or unit.casefold() in reading(a).casefold():
        return ""
    return f"Unit as printed: {unit}"


def fact_groups(catalog: ReferenceEngineCatalog, cfg: str) -> list[dict]:
    """The configuration's own assertions in reading groups; a group with nothing in it is left out."""
    operating = _operating_ids(catalog, cfg)
    rows: dict[str, list[dict]] = {key: [] for key, _, _ in FACT_GROUPS}
    for a in catalog.assertions(cfg):
        rows[_group_of(a, operating)].append(_fact_row(catalog, a))
    return [dict(key=key, title=title, note=note, rows=rows[key]) for key, title, note in FACT_GROUPS if rows[key]]


def missing_rows(catalog: ReferenceEngineCatalog, cfg: str) -> list[dict]:
    """What the performance reference lacks, in the backend's words: a gap is not a zero."""
    result = catalog.capability(cfg, Capability.PERFORMANCE_REFERENCE)
    rows = []
    for gap in result.gaps:
        quantity, _, reason = gap.partition(":")
        rows.append(dict(quantity=_words(quantity.strip()) if reason else "", reason=(reason or gap).strip()))
    return rows


def unit_assertions(catalog: ReferenceEngineCatalog, cfg: str) -> tuple[Assertion, ...]:
    """What is recorded for a propulsion unit this configuration is a member of."""
    units = {u.unit_id for u in catalog.corpus.units
             if any(m.member.kind is SubjectKind.CONFIGURATION and m.member.id == cfg for m in u.members)}
    return tuple(a for a in catalog.corpus.assertions
                 if a.subject.kind is SubjectKind.PROPULSION_UNIT and a.subject.id in units)


def context_assertions(catalog: ReferenceEngineCatalog, cfg: str) -> tuple[Assertion, ...]:
    """Context of the configuration: its variant, family and containing propulsion unit."""
    return (*catalog.context(cfg), *unit_assertions(catalog, cfg))


def context_rows(catalog: ReferenceEngineCatalog, cfg: str) -> list[dict]:
    """Recorded for the variant, family or propulsion unit: context, never a value of this configuration."""
    rows = []
    for a in context_assertions(catalog, cfg):
        row = _fact_row(catalog, a)
        row["level"] = _words(a.subject.kind.value)
        rows.append(row)
    return rows


def source_rows(catalog: ReferenceEngineCatalog, cfg: str) -> list[dict]:
    rows = []
    for s in catalog.sources(cfg):
        ref = s.reference
        rows.append(dict(sourceId=ref.source_id, title=ref.title,
                         line=f"{ref.organization}, {ref.year}" if ref.year else ref.organization,
                         authority=f"Authority {s.authority.value} · {_words(s.primacy.value)}",
                         shipping=f"Values: {_words(s.rights.values.value)}"))
    return rows


def _recorded_as(a: Assertion) -> str:
    """How the record holds the value: an enum token in words, a number, or the printed text itself."""
    if isinstance(a.value, EnumValue):
        return _token(a.value.token)
    if isinstance(a.value, NumberValue):
        return _exact(a.value.value)
    if isinstance(a.value, Missing):
        return _missing_text(a.value)
    return "Text, as printed"


def assertion_table(catalog: ReferenceEngineCatalog, cfg: str) -> tuple[list[str], list[tuple]]:
    keys, rows = [], []
    for a in catalog.assertions(cfg):
        keys.append(a.assertion_id)
        rows.append((a.field_path, a.value_as_printed, _recorded_as(a), a.unit_as_printed or NO_UNIT, _kind_word(a),
                     _conditions_line(a),
                     _point_label(catalog, a.operating_point_id), _words(a.status.value), a.source_id, a.locator))
    return keys, rows


# ------------------------------------------------------------------ inspector readouts


def _section(title: str, rows: list[tuple[str, str]]) -> dict:
    return {"title": title, "rows": [{"label": label, "value": value} for label, value in rows if value != ""]}


def _finished(build):
    """A readout never shows a heading with nothing under it."""
    def wrapper(*args, **kwargs):
        readout = build(*args, **kwargs)
        readout["sections"] = [s for s in readout["sections"] if s["rows"]]
        return readout
    wrapper.__name__, wrapper.__doc__ = build.__name__, build.__doc__
    return wrapper


def _notice_text(notice) -> str:
    if isinstance(notice, Missing):
        return _missing_text(notice)
    return f"“{notice.statement}” ({notice.where})"


def _rights_rows(s: EngineSource) -> list[tuple[str, str]]:
    r = s.rights
    host, printed = _notice_text(r.host_metadata), _notice_text(r.printed_notice)
    return [("Values", _words(r.values.value)), ("Figures", _words(r.figures.value)),
            ("Tables", _words(r.tables.value)), ("Running text", _words(r.text.value)),
            ("Repository statement", host), ("Printed notice", printed),
            ("Rights review", _words(r.review.value)), ("Review note", r.review_note),
            ("Notices disagree", "Yes" if r.notices_disagree else "")]


_SEPARATE = ("Technical authority and redistribution rights are separate: the authority grade says how close "
             "the source is to the hardware; the shipping policy says only what RocketForge may redistribute. "
             "An owner-reviewed reading is a RocketForge shipping-policy review, not a legal determination.")


@_finished
def source_readout(catalog: ReferenceEngineCatalog, source_id: str) -> dict:
    s = next(x for x in catalog.corpus.sources if x.source_id == source_id)
    ref = s.reference
    ids = "; ".join(f"{k} {v}" for k, v in sorted(ref.identifiers.items()))
    return {
        "kind": "source", "title": ref.title, "subtitle": ref.source_id,
        "sections": [
            _section("Source", [("Organization", ref.organization), ("Authors", ", ".join(ref.authors)),
                                ("Year", str(ref.year) if ref.year else ""), ("Identifiers", ids),
                                ("Type", ref.source_type), ("Location", ref.locator)]),
            _section("Technical authority", [("Authority", s.authority.value), ("Primacy", _words(s.primacy.value)),
                                             ("Access", _words(s.access.value)), ("Access note", s.access_note),
                                             ("Content hash (SHA-256)", s.content_sha256 or "")]),
            _section("Rights and shipping", _rights_rows(s)),
            _section("", [("", _SEPARATE)]),
        ],
    }


@_finished
def assertion_readout(catalog: ReferenceEngineCatalog, cfg: str, assertion_id: str) -> dict:
    a = next(x for x in (*catalog.assertions(cfg), *context_assertions(catalog, cfg))
             if x.assertion_id == assertion_id)
    s = next(x for x in catalog.corpus.sources if x.source_id == a.source_id)
    scope = f"{_words(a.subject.kind.value)} {a.subject.id}"
    is_context = a.subject.kind in (SubjectKind.VARIANT, SubjectKind.FAMILY, SubjectKind.PROPULSION_UNIT)
    point = next((p for p in catalog.corpus.operating_points if p.operating_point_id == a.operating_point_id), None)
    stored = ""
    if isinstance(a.value, NumberValue):
        stored = repr(a.value.value)
    elif isinstance(a.value, TextValue) and a.value.text != a.value_as_printed:
        stored = a.value.text
    elif isinstance(a.value, EnumValue):
        stored = a.value.token
    conditions = condition_items(a) or [("", "No condition is recorded for this value.")]
    return {
        "kind": "assertion", "title": a.field_path, "subtitle": a.assertion_id,
        "sections": [
            _section("Value", [("As printed", a.value_as_printed), ("Unit as printed", a.unit_as_printed or ""),
                               ("Recorded value", stored),
                               ("Value kind", _words(a.value_kind.value)), ("Evidence status", _words(a.status.value)),
                               ("Admissibility", _words(a.admissibility.value)),
                               ("Normalized value", "" if a.normalized is None else str(a.normalized))]),
            _section("Scope", [("Recorded for", scope),
                               ("Context", "Recorded for the variant or family: context, not a value of this "
                                           "configuration." if is_context else ""),
                               ("Operating point", f"{point.label} ({point.operating_point_id})" if point else
                                "None recorded for this value"),
                               ("Epoch", str(a.epoch) if a.epoch else "")]),
            _section("Conditions", conditions),
            _section("Where it is printed", [("Source", f"{s.reference.title} ({a.source_id})"),
                                             ("Locator", a.locator), ("Access", _words(a.access.value))]),
            _section("Source rights", [("Values", _words(s.rights.values.value)),
                                       ("Authority", f"{s.authority.value} · {_words(s.primacy.value)}"),
                                       ("Rights review", _words(s.rights.review.value))]),
            _section("Note", [("", a.note)]),
        ],
        "sourceId": a.source_id,
    }


@_finished
def capability_readout(catalog: ReferenceEngineCatalog, cfg: str, capability: str) -> dict:
    r: CapabilityResult = catalog.capability(cfg, Capability(capability))
    status = r.status.value
    return {
        "kind": "capability", "title": CAPABILITY_NAMES[r.capability],
        "subtitle": f"{STATUS_WORDS[status]} · evaluated from the shipped record",
        "sections": [
            _section("What it means", [("", CAPABILITY_MEANINGS[r.capability])]),
            _section("Not in the record", [("", g) for g in r.gaps] or [("", "Nothing listed.")]),
            _section("Caveats", [("", c) for c in r.caveats]),
            _section("Rests on", [("Assertions", ", ".join(r.assertion_ids)),
                                  ("Topology graphs", ", ".join(r.topology_ids))]),
        ],
    }


@_finished
def configuration_readout(catalog: ReferenceEngineCatalog, cfg: str) -> dict:
    ident = identity(catalog, cfg)
    sources = [(row["sourceId"], f"{row['title']} · {row['authority']} · {row['shipping']}")
               for row in source_rows(catalog, cfg)]
    points = [(p["pointId"], p["pointLabel"]) for p in ident["operatingPoints"]] or [
        ("", "No operating point is recorded for this configuration.")]
    return {
        "kind": "configuration", "title": ident["label"], "subtitle": cfg,
        "sections": [
            _section("Identity", [("Family", f"{ident['familyName']} ({ident['familyId']})"),
                                  ("Variant", f"{ident['designation']} ({ident['variantId']})"),
                                  ("Effective", ident["effective"]), ("Also called", ident["aliases"]),
                                  ("Notes", ident["notes"])]),
            _section("Operating points", points),
            _section("Cited sources", sources),
            _section("", [("", "Family and variant are the configuration's lineage only: no value recorded for "
                               "them is a value of this configuration.")]),
        ],
    }


# ------------------------------------------------------------------ topology

#: Layout constants, in device-independent pixels. Presentation only. Boxes sit
#: in columns and rows; every wire runs in the empty gaps between them.
NODE_W, NODE_H, COL_GAP, ROW_GAP = 168.0, 48.0, 96.0, 40.0
PAD_X, PAD_Y = COL_GAP + 12.0, ROW_GAP + 8.0
#: Where a wire leaves (upper third) and enters (lower third) a box: never the
#: same height, so one box's outgoing stub can never line up with the next box's
#: incoming stub and read as a connection between them.
EXIT_Y, ENTRY_Y = NODE_H * 0.36, NODE_H * 0.64
LANE_STEP = 6.0


@dataclass(frozen=True)
class _Laid:
    rank: dict[str, int] = field(default_factory=dict)
    row: dict[str, int] = field(default_factory=dict)


def layout_graph(graph: TopologyGraph) -> _Laid:
    """A deterministic RocketForge layout: columns from fluid-flow order, rows by neighbour order.

    Purely for reading. Back edges found by a depth-first pass in the graph's own
    node order are set aside for ranking only (they are still drawn). A node with
    no fluid edge sits beside a neighbour it has any edge with, else in column 0.
    Nothing is added, removed or merged.
    """
    order = [n.node_id for n in graph.nodes]
    index = {nid: i for i, nid in enumerate(order)}
    fluid = [(e.source, e.target) for e in graph.edges
             if e.kind is EdgeKind.FLUID_FLOW and e.source != e.target and e.source in index and e.target in index]
    succ: dict[str, list[str]] = {n: [] for n in order}
    indeg = {n: 0 for n in order}
    for s, t in fluid:
        succ[s].append(t)
        indeg[t] += 1
    state: dict[str, int] = {}
    back: set[tuple[str, str]] = set()

    def visit(u: str) -> None:
        state[u] = 1
        for v in sorted(succ[u], key=index.__getitem__):
            if state.get(v) == 1:
                back.add((u, v))
            elif v not in state:
                visit(v)
        state[u] = 2

    for root in [n for n in order if indeg[n] == 0] + [n for n in order if indeg[n] > 0]:
        if root not in state:
            visit(root)
    dag = [(s, t) for s, t in fluid if (s, t) not in back]
    rank = {n: 0 for n in order}
    for _ in range(len(order)):
        changed = False
        for s, t in dag:
            if rank[t] < rank[s] + 1:
                rank[t] = rank[s] + 1
                changed = True
        if not changed:
            break
    in_fluid = {n for edge in fluid for n in edge}
    for e in graph.edges:
        for here, there in ((e.source, e.target), (e.target, e.source)):
            if here in index and here not in in_fluid and there in index and there in in_fluid:
                rank[here] = rank[there]
                in_fluid.add(here)
    preds: dict[str, list[str]] = {n: [] for n in order}
    for s, t in dag:
        preds[t].append(s)
    rows: dict[str, int] = {}
    for column in sorted(set(rank.values())):
        members = [n for n in order if rank[n] == column]

        def centre(n: str) -> tuple[float, int]:
            placed = [rows[p] for p in preds[n] if p in rows]
            return (sum(placed) / len(placed) if placed else float(index[n]), index[n])

        for i, n in enumerate(sorted(members, key=centre)):
            rows[n] = i
    return _Laid(rank, rows)


def _lanes(segments: list[tuple[object, float, float]], half_width: float) -> dict:
    """Give overlapping segments in one gap their own lanes (interval colouring).

    ``segments`` are (key, low, high) along the gap. Two segments share a lane only
    when they do not overlap, so no two wires ever run on top of each other.
    Returns key -> offset from the gap's centre line: 0, +s, -s, +2s, ...
    """
    lane_end: list[float] = []
    assigned: dict = {}
    for key, low, high in sorted(segments, key=lambda s: (s[1], s[2], str(s[0]))):
        for lane, end in enumerate(lane_end):
            if low > end + LANE_STEP:
                lane_end[lane] = high
                break
        else:
            lane_end.append(high)
            lane = len(lane_end) - 1
        assigned[key] = lane
    count = max(len(lane_end), 1)
    step = min(LANE_STEP, (2 * half_width - 8.0) / max(count - 1, 1))
    return {key: ((lane + 1) // 2) * step * (1 if lane % 2 else -1) for key, lane in assigned.items()}


def _route(graph: TopologyGraph, laid: _Laid, where: dict) -> dict[str, list[tuple[float, float]]]:
    """Orthogonal wires that run only through the empty gaps between boxes.

    A wire leaves its source's right side, runs in the column gap after the
    source, crosses (when it must) along a row gap, comes down the column gap
    before its target, and enters the target's left side. Column gaps and row
    gaps hold no box, so a wire never passes under a component it does not
    connect; overlapping wires in one gap get separate lanes.
    """
    rows = max(laid.row.values(), default=0) + 1
    pitch_x, pitch_y = NODE_W + COL_GAP, NODE_H + ROW_GAP

    def gap_after(col: int) -> float:
        return PAD_X + col * pitch_x + NODE_W + COL_GAP / 2

    def channel(k: int) -> float:        # the row gap above row k (k == rows: below the last row)
        return PAD_Y + k * pitch_y - ROW_GAP / 2

    plans = {}
    for e in graph.edges:
        a, b = where[e.source], where[e.target]
        ca, cb = laid.rank[e.source], laid.rank[e.target]
        sy, ty = a["y"] + EXIT_Y, b["y"] + ENTRY_Y
        g1, g2 = ca, cb - 1                    # gap indices: after source, before target
        if g1 == g2:
            plans[e.edge_id] = (sy, ty, g1, None, None)
        else:
            mid = (sy + ty) / 2
            k = min(range(rows + 1), key=lambda i: (abs(channel(i) - mid), i))
            plans[e.edge_id] = (sy, ty, g1, g2, k)
    vertical: dict[int, list] = {}
    horizontal: dict[int, list] = {}
    for eid, (sy, ty, g1, g2, k) in plans.items():
        if k is None:
            vertical.setdefault(g1, []).append(((eid, 0), min(sy, ty), max(sy, ty)))
        else:
            cy = channel(k)
            vertical.setdefault(g1, []).append(((eid, 0), min(sy, cy), max(sy, cy)))
            vertical.setdefault(g2, []).append(((eid, 1), min(cy, ty), max(cy, ty)))
            x1, x2 = gap_after(g1), gap_after(g2)
            horizontal.setdefault(k, []).append((eid, min(x1, x2), max(x1, x2)))
    vlane = {key: off for segs in vertical.values() for key, off in _lanes(segs, COL_GAP / 2 - 8).items()}
    hlane = {key: off for segs in horizontal.values() for key, off in _lanes(segs, ROW_GAP / 2 - 6).items()}
    routes = {}
    for e in graph.edges:
        sy, ty, g1, g2, k = plans[e.edge_id]
        a, b = where[e.source], where[e.target]
        start, end = (a["x"] + NODE_W, sy), (b["x"], ty)
        x1 = gap_after(g1) + vlane[(e.edge_id, 0)]
        if k is None:
            routes[e.edge_id] = [start, (x1, sy), (x1, ty), end]
        else:
            cy = channel(k) + hlane[e.edge_id]
            x2 = gap_after(g2) + vlane[(e.edge_id, 1)]
            routes[e.edge_id] = [start, (x1, sy), (x1, cy), (x2, cy), (x2, ty), end]
    return routes


def graph_views(catalog: ReferenceEngineCatalog, cfg: str) -> list[dict]:
    """Every graph that ships for this configuration (or a unit that contains it), ready to draw."""
    views = []
    schematics = {s.schematic_id: s for s in catalog.corpus.schematics}
    for graph in catalog.topologies(cfg):
        laid = layout_graph(graph)
        drawn = [schematics[s] for s in graph.schematic_ids if s in schematics]
        provenance = sorted({s.provenance.value for s in drawn})
        reconstruction = "THIRD_PARTY_RECONSTRUCTION" in provenance
        provenance_text = "; ".join(_PROVENANCE_WORDS.get(p, _words(p)) for p in provenance) or \
            "No drawing: built from the text only"
        drawn_by = "; ".join(s.drawn_by for s in drawn if s.drawn_by)
        nodes = []
        for n in graph.nodes:
            x = PAD_X + laid.rank[n.node_id] * (NODE_W + COL_GAP)
            y = PAD_Y + laid.row[n.node_id] * (NODE_H + ROW_GAP)
            nodes.append(dict(nodeId=n.node_id, label=n.label, type=_words(n.component_type.value),
                              ownership=n.ownership.value, ownershipWord=_OWNERSHIP_WORDS.get(n.ownership.value,
                                                                                               n.ownership.value),
                              engineOwned=n.ownership.value == "ENGINE", evidence=n.evidence.value,
                              inferred=n.evidence.value == "INFERRED", x=x, y=y, w=NODE_W, h=NODE_H))
        where = {n["nodeId"]: n for n in nodes}
        labels = {n.node_id: n.label for n in graph.nodes}
        routes = _route(graph, laid, where)
        edges = []
        for e in graph.edges:
            points = routes[e.edge_id]
            # the handle sits on the wire's middle segment, which always lies in a gap
            (hx0, hy0), (hx1, hy1) = points[len(points) // 2 - 1], points[len(points) // 2]
            tip = points[-1]
            edges.append(dict(edgeId=e.edge_id, source=e.source, target=e.target, kind=e.kind.value,
                              kindWord=_EDGE_WORDS.get(e.kind, _words(e.kind.value)), carrier=e.carrier or "",
                              role=e.role, evidence=e.evidence.value, inferred=e.evidence.value == "INFERRED",
                              fromLabel=labels[e.source], toLabel=labels[e.target],
                              points=points, path=" ".join(f"{x:.1f} {y:.1f}" for x, y in points),
                              mx=(hx0 + hx1) / 2, my=(hy0 + hy1) / 2,
                              ax=tip[0] - 9, ay=tip[1] - 4.5, bx=tip[0] - 9, by=tip[1] + 4.5,
                              x3=tip[0], y3=tip[1]))
        columns = max(laid.rank.values(), default=0) + 1
        rows = max(laid.row.values(), default=0) + 1
        width = PAD_X + columns * (NODE_W + COL_GAP) + 12.0
        height = PAD_Y + rows * (NODE_H + ROW_GAP) + 8.0
        omissions = list(graph.completeness.known_omissions)
        views.append(dict(
            topologyId=graph.topology_id, label=graph.label,
            scope=f"{_words(graph.scope.kind.value)} {graph.scope.id}",
            unitGraph=graph.scope.kind is SubjectKind.PROPULSION_UNIT,
            reconstruction=reconstruction, provenanceText=provenance_text, drawnBy=drawn_by,
            declaredComplete=graph.completeness.declared_complete,
            completenessText=("Declared complete" if graph.completeness.declared_complete else
                              f"Incomplete by its own account · {len(omissions)} known omission"
                              + ("" if len(omissions) == 1 else "s")),
            omissions=omissions, nodes=nodes, edges=edges, width=width, height=height,
            kinds=sorted({e["kindWord"] for e in edges}),
            hasNonEngine=any(not n["engineOwned"] for n in nodes),
            hasInferred=any(n["inferred"] for n in nodes) or any(e["inferred"] for e in edges),
        ))
    return views


def _graph_of(catalog: ReferenceEngineCatalog, cfg: str, topology_id: str) -> TopologyGraph:
    return next(g for g in catalog.topologies(cfg) if g.topology_id == topology_id)


@_finished
def graph_readout(catalog: ReferenceEngineCatalog, cfg: str, topology_id: str) -> dict:
    g = _graph_of(catalog, cfg, topology_id)
    schematics = {s.schematic_id: s for s in catalog.corpus.schematics}
    drawings = []
    for sid in g.schematic_ids:
        s = schematics.get(sid)
        if s:
            drawings.append((sid, f"{_PROVENANCE_WORDS.get(s.provenance.value, s.provenance.value)}. "
                                  f"{s.title_as_printed} ({s.source_id}, {s.locator}). Drawn by {s.drawn_by}."))
    return {
        "kind": "graph", "title": g.label, "subtitle": g.topology_id,
        "sections": [
            _section("Graph", [("Scope", f"{_words(g.scope.kind.value)} {g.scope.id}"),
                               ("Built as", "RocketForge-derived graph: a RocketForge graph of the drawing "
                                            "and text below, drawn by RocketForge, not a copy of the figure"),
                               ("Completeness", "Declared complete" if g.completeness.declared_complete
                                else "Not declared complete")]),
            _section("Drawings it rests on", drawings or [("", "None: built from the text only.")]),
            _section("Text sources", [("", sid) for sid in g.text_source_ids]),
            _section("Known omissions", [("", o) for o in g.completeness.known_omissions]
                     or [("", "None listed.")]),
            _section("Layout", [("", "Node positions are a RocketForge layout chosen for readability. The "
                                     "connections are the evidence; where a node sits on screen is not.")]),
            _section("Notes", [("", g.notes)]),
        ],
    }


@_finished
def node_readout(catalog: ReferenceEngineCatalog, cfg: str, topology_id: str, node_id: str) -> dict:
    g = _graph_of(catalog, cfg, topology_id)
    n = next(x for x in g.nodes if x.node_id == node_id)
    labels = {x.node_id: x.label for x in g.nodes}
    inbound = [(_EDGE_WORDS.get(e.kind, e.kind.value), f"from {labels[e.source]}: {e.role}"
                + (f" ({e.carrier})" if e.carrier else "")) for e in g.edges if e.target == node_id]
    outbound = [(_EDGE_WORDS.get(e.kind, e.kind.value), f"to {labels[e.target]}: {e.role}"
                 + (f" ({e.carrier})" if e.carrier else "")) for e in g.edges if e.source == node_id]
    return {
        "kind": "node", "title": n.label, "subtitle": f"{node_id} · {g.topology_id}",
        "sections": [
            _section("Component", [("Type", _words(n.component_type.value)),
                                   ("Owned by", _OWNERSHIP_WORDS.get(n.ownership.value, n.ownership.value)),
                                   ("Evidence", _EVIDENCE_WORDS.get(n.evidence.value, _words(n.evidence.value))),
                                   ("Locator", n.locator)]),
            _section("Connections in", inbound or [("", "None recorded.")]),
            _section("Connections out", outbound or [("", "None recorded.")]),
        ],
    }


@_finished
def edge_readout(catalog: ReferenceEngineCatalog, cfg: str, topology_id: str, edge_id: str) -> dict:
    g = _graph_of(catalog, cfg, topology_id)
    e = next(x for x in g.edges if x.edge_id == edge_id)
    labels = {x.node_id: x.label for x in g.nodes}
    return {
        "kind": "edge", "title": f"{labels[e.source]} → {labels[e.target]}",
        "subtitle": f"{edge_id} · {g.topology_id}",
        "sections": [
            _section("Relationship", [("Kind", _EDGE_WORDS.get(e.kind, _words(e.kind.value))),
                                      ("Carrier", _carrier(e)), ("Role (as recorded)", e.role),
                                      ("Split group", e.split_group or ""), ("Merge group", e.merge_group or "")]),
            _section("Evidence", [("Evidence", _EVIDENCE_WORDS.get(e.evidence.value, _words(e.evidence.value))),
                                  ("Locator", e.locator)]),
            _section("Direction", [("From", f"{labels[e.source]} ({e.source})"),
                                   ("To", f"{labels[e.target]} ({e.target})")]),
        ],
    }


def connection_table(catalog: ReferenceEngineCatalog, cfg: str) -> tuple[list[tuple[str, str]], list[tuple]]:
    """Every edge of every shipped graph, for keyboard and table reading. Keys are (graph, edge)."""
    keys, rows = [], []
    for g in catalog.topologies(cfg):
        labels = {x.node_id: x.label for x in g.nodes}
        for e in g.edges:
            keys.append((g.topology_id, e.edge_id))
            rows.append((labels[e.source], labels[e.target], _EDGE_WORDS.get(e.kind, _words(e.kind.value)),
                         _carrier(e), e.role, _EVIDENCE_WORDS.get(e.evidence.value, e.evidence.value),
                         e.locator))
    return keys, rows
