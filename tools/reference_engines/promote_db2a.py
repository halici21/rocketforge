"""Build the reference-engine corpus from DB-0.5 research, entry by entry, through the promotion gates.

The corpus is one file built from the DB-2A seed manifest (``db2a_manifest.py``)
and the DB-2B Wave 1 manifest (``db2b_wave1_manifest.py``), merged; every gate
applies to both.

Usage (from the repository root)::

    python tools/reference_engines/promote_db2a.py          # write the shipped file
    python tools/reference_engines/promote_db2a.py --check  # exit 1 if it would change

This is a build-time tool. It reads ``docs/research/engine_database/db05`` and
the manifests and writes ``rocketforge/data/evidence/engines/
reference_engines.json``. RocketForge never runs it and never reads research
files: the shipped JSON is the only thing the application loads.

Every gate below refuses; none repairs. A refusal names the entry and the rule,
and nothing is written.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import types
from dataclasses import dataclass

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rocketforge.evidence import (  # noqa: E402
    AccessClass,
    Missing,
    MissingReason,
    ShippingPolicy,
    SourceReference,
    ValueStatus,
)
from rocketforge.evidence.engines import (  # noqa: E402
    RIGHTS_IN_RECORD,
    Admissibility,
    Alias,
    AliasKind,
    Assertion,
    Completeness,
    ComponentType,
    Conditions,
    EdgeKind,
    EngineConfiguration,
    EngineEvidenceCorpus,
    EngineFamily,
    EngineSource,
    EngineVariant,
    EnumValue,
    Environment,
    IspBasis,
    MixtureRatioBasis,
    MixtureRatioForm,
    NumberValue,
    OperatingPoint,
    Ownership,
    PressureBasis,
    PressureStation,
    PropulsionUnit,
    PropulsionUnitKind,
    RightsNotice,
    RightsRecord,
    RightsReview,
    Schematic,
    SchematicProvenance,
    Setting,
    SourceAccess,
    SourceAuthority,
    SourcePrimacy,
    SubjectKind,
    SubjectRef,
    TextValue,
    TopologyEdge,
    TopologyEvidence,
    TopologyGraph,
    TopologyNode,
    UnitMember,
    ValueKind,
    corpus_to_json,
)
from rocketforge.evidence.engines.admission import admission_violations  # noqa: E402

DB05 = ROOT / "docs" / "research" / "engine_database" / "db05"
OUTPUT = ROOT / "rocketforge" / "data" / "evidence" / "engines" / "reference_engines.json"

#: DB-0.5 rights readings under which values may ship.
SHIPPABLE_DB05_RIGHTS = frozenset({"PUBLIC_DOMAIN_GOV", "VALUES_WITH_ATTRIBUTION"})
#: NTRS determinations that permit public use.
PUBLIC_USE = frozenset({"PUBLIC_USE_PERMITTED", "GOV_PUBLIC_USE_PERMITTED"})
_FIGURES = {"PUBLIC_DOMAIN_GOV": "VALUES_WITH_ATTRIBUTION", "VALUES_WITH_ATTRIBUTION": "VALUES_WITH_ATTRIBUTION",
            "RIGHTS_REVIEW_REQUIRED": "RIGHTS_REVIEW_REQUIRED"}

#: Words that mark a printed number as a boundary, not an operating value.
_LIMIT_WORDS = re.compile(r"(?i)\b(limit|maximum allowable|not to exceed|redline|overspeed|burst|proof)\b")

#: DB-0.5 component-type words and the production types they are.
COMPONENT_TYPES = {
    "ambient": ComponentType.AMBIENT_SINK, "check_valve": ComponentType.CHECK_VALVE,
    "combustion_chamber": ComponentType.COMBUSTION_CHAMBER, "cooling_jacket": ComponentType.COOLING_JACKET,
    "energy_store_start_tank": ComponentType.START_ENERGY_STORE, "engine_inlet": ComponentType.INTERFACE_PORT,
    "gas_generator": ComponentType.GAS_GENERATOR, "gearbox": ComponentType.GEARBOX,
    "heat_exchanger": ComponentType.HEAT_EXCHANGER, "hydraulic_pump": ComponentType.HYDRAULIC_PUMP,
    "igniter": ComponentType.IGNITER, "injector": ComponentType.INJECTOR,
    "nozzle_extension": ComponentType.NOZZLE_EXTENSION, "nozzle_injection_port": ComponentType.MANIFOLD,
    "orifice": ComponentType.ORIFICE, "pressurant_tank": ComponentType.PRESSURANT_TANK,
    "pump": ComponentType.PUMP, "regulator": ComponentType.REGULATOR, "tank": ComponentType.TANK,
    "tank_pressurization_port": ComponentType.INTERFACE_PORT, "turbine": ComponentType.TURBINE,
    "valve": ComponentType.VALVE, "venturi": ComponentType.VENTURI,
    "start_cartridge": ComponentType.START_ENERGY_STORE, "lubricant_blender": ComponentType.OTHER,
    "actuator": ComponentType.ACTUATOR, "actuator_supply": ComponentType.ACTUATOR,
}
OWNERS = {"engine": Ownership.ENGINE, "stage": Ownership.STAGE, "vehicle": Ownership.VEHICLE,
          "ambient": Ownership.AMBIENT}
_PREFIX = {"FAM-": SubjectKind.FAMILY, "VAR-": SubjectKind.VARIANT, "CFG-": SubjectKind.CONFIGURATION,
           "UNIT-": SubjectKind.PROPULSION_UNIT}


class PromotionError(Exception):
    """A manifest entry failed a promotion gate. Nothing is written."""

    def __init__(self, problems):
        self.problems = tuple(problems)
        super().__init__("reference-engine promotion refused:\n  " + "\n  ".join(self.problems))


@dataclass(frozen=True)
class Research:
    """The DB-0.5 records the gates read."""

    assertions: dict
    documents: dict
    conflicts: dict
    schematics: dict
    topologies: dict


def load_research(db05: pathlib.Path = DB05) -> Research:
    read = lambda name: json.loads((db05 / name).read_text(encoding="utf-8"))  # noqa: E731
    return Research(
        assertions={a["assertion_id"]: a for a in read("assertions.json")["assertions"]},
        documents={d["source_id"]: d for d in read("documents_opened.json")["documents"]},
        conflicts={c["conflict_id"]: c for c in read("conflicts.json")["conflicts"]},
        schematics={s["schematic_id"]: s for s in read("schematics_viewed.json")["schematics"]},
        topologies={p.stem: json.loads(p.read_text(encoding="utf-8"))
                    for p in sorted((db05 / "topology").glob("*.json"))})


#: Manifest collections merged across the DB-2A and DB-2B Wave 1 manifests.
_DICTS = ("SEED_SUBJECTS", "SOURCES", "WITHHELD_SOURCES", "WITHHELD_CONTENT_TERMS", "FIELD_RENAMES",
          "OPERATING_POINT_MAP", "CONFIGURATION_MAP", "CONFIGURATION_SOURCES", "NOT_PROMOTED",
          "RESEARCH_CONFLICTS", "CARRIER_GENERALISATIONS", "SCHEMATICS", "OWNER_DECISIONS", "OWNER_REVIEWS")
_TUPLES = ("SEED_ENGINES", "ACCOUNTED_ENGINES", "DISPOSITIONS", "FAMILIES", "VARIANTS", "CONFIGURATIONS",
           "OPERATING_POINTS", "UNITS", "ALIASES", "ASSERTIONS", "TOPOLOGIES")
MANIFESTS = ("db2a_manifest", "db2b_wave1_manifest")


def merge_manifests(*modules) -> types.SimpleNamespace:
    """One manifest from several. A key defined twice must be defined identically."""
    out: dict = {k: {} for k in _DICTS} | {k: () for k in _TUPLES}
    problems = []
    for mod in modules:
        for k in _DICTS:
            for key, val in getattr(mod, k, {}).items():
                if key in out[k] and out[k][key] != val:
                    problems.append(f"manifest {k}: {key!r} is defined twice, differently")
                out[k][key] = val
        for k in _TUPLES:
            out[k] += tuple(x for x in getattr(mod, k, ()) if not (k == "DISPOSITIONS" and x in out[k]))
    if problems:
        raise PromotionError(problems)
    return types.SimpleNamespace(**out)


def load_manifest():
    here = str(pathlib.Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    import importlib
    return merge_manifests(*(importlib.import_module(name) for name in MANIFESTS))


def _subject(ref: str) -> SubjectRef:
    for prefix, kind in _PREFIX.items():
        if ref.startswith(prefix):
            return SubjectRef(kind, ref)
    raise PromotionError([f"subject {ref!r} is not a FAM-, VAR-, CFG- or UNIT- id"])


# ------------------------------------------------------------------ gates


#: Wording that claims the owner reviewed, approved or accepted something.
_OWNER_REVIEW_WORDS = re.compile(r"(?i)\bowner[- ]?(review|approv|accept)|\b(reviewed|approved|accepted) by the owner")


def source_problems(sid: str, research: Research, manifest) -> list[str]:
    """Why this source may not supply shipped evidence."""
    out = []
    if sid in manifest.WITHHELD_SOURCES:
        return [f"{sid}: withheld ({manifest.WITHHELD_SOURCES[sid]['reason']})"]
    doc = research.documents.get(sid)
    if doc is None:
        return [f"{sid}: never opened in DB-0.5 (a search result or an unknown source is not evidence)"]
    if doc.get("read_level") != "READ_AND_MINED":
        out.append(f"{sid}: DB-0.5 access is {doc.get('read_level')}, not READ_AND_MINED")
    if not doc.get("sha256") or doc.get("http_status") != "200":
        out.append(f"{sid}: no recorded download (sha256 and HTTP 200) of the file that was read")
    spec = manifest.SOURCES.get(sid)
    if spec is None:
        return out + [f"{sid}: not in the manifest's source list"]
    reviewers = [k for k, r in getattr(manifest, "OWNER_REVIEWS", {}).items() if sid in r["sources"]]
    if _OWNER_REVIEW_WORDS.search(spec.get("review_note", "")) and not reviewers:
        out.append(f"{sid}: the rights note says owner-reviewed, but no OWNER_REVIEWS entry lists the source")
    if reviewers and not re.search(r"(?i)owner[- ]reviewed 2026-10-09", spec.get("review_note", "")):
        out.append(f"{sid}: listed by OWNER_REVIEWS {reviewers[0]}, but its rights note does not record the review")
    if spec.get("review", "NOT_REVIEWED") != "CONSISTENT":
        out.append(f"{sid}: rights review is {spec.get('review', 'NOT_REVIEWED')}; only a reviewed, "
                   "consistent rights reading ships values")
    if doc.get("rights_values") not in SHIPPABLE_DB05_RIGHTS:
        out.append(f"{sid}: DB-0.5 values rights {doc.get('rights_values')}")
    if spec["host"] == "NONE":
        if doc.get("ntrs_copyright_determination") is not None:
            out.append(f"{sid}: NTRS returned {doc['ntrs_copyright_determination']!r}; the manifest must record it")
    else:
        if doc.get("ntrs_copyright_determination") != spec["host"]:
            out.append(f"{sid}: host statement {spec['host']!r} is not what NTRS returned "
                       f"({doc.get('ntrs_copyright_determination')!r})")
        if spec["host"] not in PUBLIC_USE:
            out.append(f"{sid}: host statement {spec['host']} does not permit public use")
    if restrictive_notice(doc.get("rights_statement_checked", "")):
        out.append(f"{sid}: DB-0.5 recorded a restrictive printed notice: {doc['rights_statement_checked']}")
    return out


#: Words of a printed notice that reserves rights or forbids reuse.
_RESTRICTIVE = re.compile(r"(?i)not permitted|reproduction|copyright|proprietary|all (other )?rights (are )?reserved"
                          r"|\(c\)|\u00a9")


def restrictive_notice(statement: str) -> bool:
    """Whether a DB-0.5 rights statement records a restrictive printed notice.

    Only the explicit finding 'no copyright notice ...' is set aside; any other
    mention of copyright, reservation, proprietary marking or a reproduction
    restriction counts.
    """
    cleared, n = re.subn(r"(?i)\bno copyright notice(?: on (?:the )?(?:cover|pages read))?", "", statement or "")
    if n and re.search(r"(?i)\b(but|except|although|however|yet)\b", cleared):
        return True  # a finding of "no notice" qualified by an exception is not a clean finding
    return bool(_RESTRICTIVE.search(cleared))


def _db05_number(record) -> float | None:
    v = record["value"]
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _whole_numbers(text: str) -> set[float]:
    """Numbers as printed, thousands separators joined ('21 500', '230,000'); 0 and 1 dropped."""
    found = set()
    for m in re.finditer(r"\d{1,3}(?:[ ,]\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", text):
        value = float(m.group(0).replace(",", "").replace(" ", ""))
        if value not in (0.0, 1.0):
            found.add(value)
    return found


def withheld_tokens(manifest) -> tuple[str, ...]:
    return tuple(t for spec in manifest.WITHHELD_SOURCES.values() for t in spec["locator_tokens"])


def _printed_numbers(text: str) -> set[float]:
    found = set()
    for m in re.finditer(r"\d[\d, ]*(?:\.\d+)?", text):
        token = m.group(0).strip().rstrip(",")
        digits = token.replace(",", "").replace(" ", "")
        try:
            found.add(float(digits))
        except ValueError:
            pass
        for part in re.split(r"[ ,]", token):
            if part:
                try:
                    found.add(float(part))
                except ValueError:
                    pass
    return found


_ID = re.compile(r"AS-DB05-[A-Z0-9-]+-\d{3}")


def _ids(text: str) -> list[str]:
    return _ID.findall(text or "")


def op_basis_problems(research: Research, manifest) -> list[str]:
    """An operating point DB-0.5 does not state is grounded in a cited assertion: one DB-0.5
    places at that point, or a sibling from the same source and table promoted at that point."""
    out, entries = [], {e["db05_id"]: e for e in manifest.ASSERTIONS}
    for e in manifest.ASSERTIONS:
        r = research.assertions.get(e["db05_id"])
        if r is None or r["operating_point"] is not None or e["operating_point"] is None:
            continue
        for cited in _ids(e.get("op_basis", "")):
            c = research.assertions.get(cited)
            if c is None or cited == e["db05_id"]:
                continue
            mapped = manifest.OPERATING_POINT_MAP.get((c["engine_id"], c["operating_point"]))
            sibling = (cited in entries and entries[cited]["operating_point"] == e["operating_point"]
                       and c["source_id"] == r["source_id"] and c["locator"] == r["locator"])
            if mapped == e["operating_point"] or sibling:
                break
        else:
            out.append(f"{e['db05_id']}: op_basis cites no assertion that places it at {e['operating_point']}")
    return out


def assertion_problems(entry: dict, research: Research, manifest) -> list[str]:
    """Why this manifest entry may not be promoted from its DB-0.5 assertion."""
    aid = entry["db05_id"]
    record = research.assertions.get(aid)
    if record is None:
        return [f"{aid}: no such DB-0.5 assertion"]
    out = []
    engine = record["engine_id"]
    if engine not in manifest.SEED_ENGINES:
        return [f"{aid}: {engine} is not a DB-2A seed"]
    if entry["subject"] not in manifest.SEED_SUBJECTS[engine]:
        out.append(f"{aid}: subject {entry['subject']} is not an identity of {engine}")
    if record["disposition"] != "PROMOTED" or record["evidence_status"] != "SOURCE_VERIFIED":
        out.append(f"{aid}: DB-0.5 disposition {record['disposition']} ({record['evidence_status']})")
    if record["status"] == "INFERRED":
        out.append(f"{aid}: INFERRED in DB-0.5; an inferred value is never promoted, and never as REPORTED")
    elif record["status"] == "DIGITISED" and not entry.get("schematic_id"):
        out.append(f"{aid}: DIGITISED without the schematic it was read from")
    elif record["status"] not in ("REPORTED", "DIGITISED"):
        out.append(f"{aid}: DB-0.5 status {record['status']}")
    if record.get("access") != "fetched":
        out.append(f"{aid}: DB-0.5 access {record.get('access')!r}")
    out += [f"{aid}: {p}" for p in source_problems(record["source_id"], research, manifest)]
    if any(t in record["locator"] for t in withheld_tokens(manifest)):
        out.append(f"{aid}: locator names a withheld source")
    allowed = (record["field_path"], *manifest.FIELD_RENAMES.get(record["field_path"], ()))
    if entry["field_path"] not in allowed:
        out.append(f"{aid}: field {entry['field_path']} does not render DB-0.5 field {record['field_path']}")
    out += _value_problems(aid, entry, record)
    out += _scope_problems(aid, entry, record, manifest)
    out += _condition_problems(aid, entry, record)
    out += _kind_problems(aid, entry, record)
    return out


#: Value kinds and the printed words that justify them without a written reading.
_KIND_WORDS = {"AVERAGE": r"\baverage\b", "MAXIMUM": r"\bmaximum\b", "MINIMUM": r"\bminimum\b",
               "APPROXIMATE": r"\b(approximately|about|approx\.?)\b", "RATED": r"\brated\b",
               "DESIGN_VALUE": r"\b(design|requirement|specification)\b", "PREDICTION": r"\bpredict",
               "TEST_RESULT": r"\b(test|measured)\b"}


def _kind_problems(aid, entry, record) -> list[str]:
    kind = entry["value_kind"]
    # a word inside a compound modifier ("maximum-rated thrust", "minimum-throttle point")
    # describes the other noun, not this value
    printed = re.sub(r"\b\w+(?:-\w+)+\b", " ", record["value_as_printed"])
    label = re.sub(r"\b\w+(?:-\w+)+\b", " ", f"{record['conditions'].get('label', '')} {record['locator']}")
    if (re.search(r"(?i)\brequirements?\b", f"{record['value_as_printed']} {record['locator']}")
            and entry["value"][0] == "number" and kind != "DESIGN_VALUE"):
        return [f"{aid}: printed as a design requirement; promoted as {kind}, not DESIGN_VALUE"]
    if _LIMIT_WORDS.search(record["value_as_printed"]) and kind != "LIMIT":
        return [f"{aid}: printed as a limit; promoted as {kind}, which is an operating value"]
    if kind in _KIND_WORDS and not re.search(_KIND_WORDS[kind], f"{printed} {label}", re.I) and not entry["reading"]:
        return [f"{aid}: value kind {kind} is not what the source prints; say how it was read (reading)"]
    if kind == "NOMINAL" and entry["value"][0] == "number" and not entry["reading"]:
        for other, words in _KIND_WORDS.items():
            if other != "TEST_RESULT" and re.search(words, printed, re.I):
                return [f"{aid}: printed as {other.lower()}, promoted as NOMINAL"]
    return []


def _value_problems(aid, entry, record) -> list[str]:
    kind = entry["value"][0]
    if kind == "number":
        number = float(entry["value"][1])
        db05 = _db05_number(record)
        if db05 is not None:
            return [] if db05 == number else [f"{aid}: value {number} is not DB-0.5's {db05}"]
        if not entry["reading"]:
            return [f"{aid}: DB-0.5 holds {record['value']!r}; a number read from it says how (reading)"]
        if number not in _printed_numbers(record["value_as_printed"]):
            return [f"{aid}: {number} is not printed in {record['value_as_printed']!r}"]
        return []
    if kind == "enum":
        token = entry["value"][1]
        if str(record["value"]).upper() != token:
            return [f"{aid}: token {token} is not DB-0.5's value {record['value']!r}"]
        return []
    if kind == "text":
        return _excerpt_problems(aid, entry, record) if len(entry["value"]) > 1 else []
    return [f"{aid}: unknown value kind {kind!r}"]


def _excerpt_problems(aid, entry, record) -> list[str]:
    """A text value may ship some of the ``;``-separated statements its source prints, never a
    reworded or shortened one: whole statements, in printed order, and only statements that do
    not scope the others. Whether what is left keeps its meaning is the owner's call, so an
    excerpt also needs an owner decision that releases or carries it (``excerpt_owner_problems``)."""
    if isinstance(record["value"], (int, float)):
        return [f"{aid}: DB-0.5 holds a number ({record['value']!r}); an excerpt is for text values only"]
    printed = [p.strip() for p in record["value_as_printed"].split(";") if p.strip()]
    parts = [p.strip() for p in str(entry["value"][1]).split(";") if p.strip()]
    if not parts:
        return [f"{aid}: an empty excerpt"]
    not_whole = [p for p in parts if p not in printed]
    if not_whole:
        return [f"{aid}: excerpt {not_whole!r} is not a whole printed statement of {record['value_as_printed']!r} "
                "(a statement is shipped whole or not at all)"]
    if [p for p in printed if p in parts] != parts or len(set(parts)) != len(parts):
        return [f"{aid}: excerpt {parts!r} does not keep the printed order of {record['value_as_printed']!r}"]
    dropped = [p for p in printed if p not in parts]
    context = [p for p in dropped if ":" in p or not re.search(r"\d", p)]
    if context:
        return [f"{aid}: excerpt drops {context!r}, which reads as context for the statements kept "
                "(a heading or a statement without its own value)"]
    return []


def excerpt_owner_problems(manifest) -> list[str]:
    """An excerpt ships only where a recorded owner decision releases or carries the assertion."""
    owned = {i for d in manifest.RESEARCH_CONFLICTS.values() if _owner_text(d.get("owner_accepted")).strip()
             for i in (*d.get("owner_released", ()), *(d.get("touches", ()) if d.get("decision") == "CARRIED_NOT" else ()))}
    return [f"{e['db05_id']}: a text excerpt needs a recorded owner decision that releases or carries it"
            for e in manifest.ASSERTIONS
            if e["value"][0] == "text" and len(e["value"]) > 1 and e["db05_id"] not in owned]


#: DB-0.5 fields that describe a build, not a family or a variant in general.
_BUILD_FIELDS = ("performance.", "nozzle.", "propellants.mixture_ratio", "mechanical.mass")
#: DB-0.5 fields a propulsion unit (stage-level hardware) may carry.
_UNIT_FIELDS = ("pressurization.", "feed.", "tanks.")


#: (source, locator) of each DB-0.5 assertion, set by build_corpus for the scope gate.
_LOCATORS: dict[str, tuple[str, str]] = {}


def research_locator(aid: str) -> tuple[str, str] | None:
    return _LOCATORS.get(aid)


def _scope_problems(aid, entry, record, manifest) -> list[str]:
    out, engine = [], record["engine_id"]
    subject = _subject(entry["subject"])
    configured = record["conditions"].get("configuration")
    if subject.kind is SubjectKind.CONFIGURATION:
        if configured is not None and manifest.CONFIGURATION_MAP.get((engine, configured)) != subject.id:
            out.append(f"{aid}: printed for configuration {configured!r}, not {subject.id}")
    op = record["operating_point"]
    if op is not None:
        mapped = manifest.OPERATING_POINT_MAP.get((engine, op))
        if mapped is None or mapped != entry["operating_point"]:
            out.append(f"{aid}: DB-0.5 operating point {op} is not seed point {entry['operating_point']}")
    elif entry["operating_point"] is not None and not _ids(entry.get("op_basis", "")):
        out.append(f"{aid}: DB-0.5 states no operating point; placing it at {entry['operating_point']} "
                   "needs a basis (op_basis) citing the assertion that puts it there")
    if entry["operating_point"] is not None and subject.kind is not SubjectKind.CONFIGURATION:
        out.append(f"{aid}: an operating point belongs to a configuration subject")
    if subject.kind in (SubjectKind.FAMILY, SubjectKind.VARIANT):
        requirement = entry["value_kind"] == "DESIGN_VALUE"  # a programme requirement belongs above any build
        build_value = record["field_path"].startswith(_BUILD_FIELDS) or op is not None or configured is not None
        if build_value and not requirement:
            out.append(f"{aid}: a performance, geometry or mass value, or one printed for a build or point, is "
                       f"not filed on {subject.kind.value.lower()} {subject.id}")
        same_table = [e["db05_id"] for e in manifest.ASSERTIONS
                      if e["db05_id"] != aid and e["subject"].startswith("CFG-")
                      and research_locator(e["db05_id"]) == (record["source_id"], record["locator"])]
        if same_table and not requirement:
            out.append(f"{aid}: printed in the same place as configuration statements ({same_table[0]}); it is "
                       f"not filed on {subject.kind.value.lower()} {subject.id}")
    if subject.kind is SubjectKind.CONFIGURATION and re.search(
            r"(?i)\brequirements?\b", f"{record['value_as_printed']} {record['locator']}"):
        out.append(f"{aid}: a design requirement is not a value of configuration {subject.id}")
    if subject.kind is SubjectKind.PROPULSION_UNIT and not record["field_path"].startswith(_UNIT_FIELDS):
        out.append(f"{aid}: a propulsion unit carries pressurization, feed or tank statements, not "
                   f"{record['field_path']}")
    allowed = getattr(manifest, "CONFIGURATION_SOURCES", {}).get(subject.id)
    if allowed is not None and record["source_id"] not in allowed:
        out.append(f"{aid}: {subject.id} takes values from {', '.join(allowed)} only, not {record['source_id']}")
    return out


def _condition_problems(aid, entry, record) -> list[str]:
    out, cond, db05 = [], entry["conditions"], record["conditions"]
    final = entry["field_path"].rsplit(".", 1)[-1]
    if final.startswith("chamber_pressure"):
        station = "NOZZLE_STAGNATION" if db05.get("pc_station") == "nozzle stagnation" else "UNKNOWN"
        if cond.get("pressure_station") != station:
            out.append(f"{aid}: DB-0.5 station {db05.get('pc_station')!r} must be {station}, "
                       f"not {cond.get('pressure_station')}")
        unit = record["unit_as_printed"].strip().lower()
        basis = ("ABSOLUTE" if db05.get("pressure_basis") == "abs" or unit == "psia"
                 else "GAUGE" if unit == "psig" else "UNKNOWN")
        if cond.get("pressure_basis") != basis:
            out.append(f"{aid}: printed {record['unit_as_printed']!r}; pressure basis must be {basis}")
    if final.startswith(("thrust", "specific_impulse")) and not final.startswith("thrust_chamber"):
        env = {"vacuum": "VACUUM", "sea_level": "SEA_LEVEL"}.get(db05.get("environment"), "UNKNOWN")
        if cond.get("environment") != env:
            out.append(f"{aid}: DB-0.5 environment {db05.get('environment')!r} must be {env}")
    if cond.get("isp_basis", "UNKNOWN") != "UNKNOWN":
        out.append(f"{aid}: no DB-0.5 record states an Isp basis; it stays UNKNOWN")
    if "mixture_ratio" in cond:
        out.append(f"{aid}: a mixture-ratio setting is carried by the operating point, not added as a condition")
    stated = re.sub(r"(?i)inverse of O/F", "", f"{record['value_as_printed']} {db05.get('mr_basis', '')}")
    if record["field_path"].startswith("gg."):
        stated += " gas generator"  # the DB-0.5 field itself is the gas generator's
    form = cond.get("mixture_ratio_form")
    if form is not None:
        marks = {"OXIDIZER_TO_FUEL": ("O/F", "oxidizer-to-fuel", "oxidizer to fuel", "lox-to-fuel"),
                 "FUEL_TO_OXIDIZER": ("F/O", "fuel-to-oxidizer", "fuel to oxidizer", "fuel-to-lox")}[form]
        if not any(m.lower() in f"{stated} {_recorded_reading(entry, record)}".lower() for m in marks):
            out.append(f"{aid}: mixture ratio form {form} is not printed ({marks[0]}) nor in a DB-0.5 record "
                       "the reading cites or quotes")
    basis = cond.get("mixture_ratio_basis", "UNKNOWN")
    if basis != "UNKNOWN" and basis.lower().replace("_", " ") not in stated.lower():
        out.append(f"{aid}: mixture ratio basis {basis} is not printed; it stays UNKNOWN")
    return out


#: Every DB-0.5 assertion, set by build_corpus for gates that check a reading against the record.
_RESEARCH: dict[str, dict] = {}


def _recorded_reading(entry: dict, record: dict) -> str:
    """The parts of a reading that DB-0.5 records: the printed text of an assertion of the same
    engine the reading cites by id, and any quoted phrase printed by an assertion of the same
    source and page. The author's own words are not evidence."""
    reading = entry["reading"]
    out = [r["value_as_printed"] for aid, r in _RESEARCH.items()
           if aid in reading and r["engine_id"] == record["engine_id"]]
    pages = _pages(record["locator"]) or {record["locator"]}
    same_page = [r["value_as_printed"].lower() for r in _RESEARCH.values()
                 if r["source_id"] == record["source_id"] and (_pages(r["locator"]) or {r["locator"]}) & pages]
    out += [q for q in re.findall(r"'([^']+)'", reading) if any(q.lower() in p for p in same_page)]
    return " ".join(out)


def claim_matches(conflict: dict, research: Research) -> list[set[str]]:
    """For each claim of a DB-0.5 conflict, the DB-0.5 assertions it is: same engine, same
    source, and a printed number in common."""
    out = []
    for text, sid, _ in conflict["claims"]:
        numbers = _whole_numbers(text)
        out.append({aid for aid, r in research.assertions.items()
                    if r["engine_id"] == conflict["engine_id"] and r["source_id"] == sid
                    and numbers & _whole_numbers(r["value_as_printed"])})
    return out


def _owner_text(decision) -> str:
    """One owner decision, or several recorded for the same conflict, as text."""
    return " ".join(decision) if isinstance(decision, tuple) else str(decision or "")


def _named_in(printed: str, text: str) -> bool:
    """Every number of a printed value appears, as printed, in the owner's text (or the whole
    printed text does, if it has no number)."""
    numbers = re.findall(r"\d[\d,]*(?:\.\d+)?", printed)
    if not numbers:
        return printed.strip().lower() in text.lower()
    return all(re.search(rf"(?<![\d.,]){re.escape(n)}(?![\d]|[.,]\d)", text) for n in numbers)


def conflict_problems(research: Research, manifest, promoted: set[str]) -> list[str]:
    out = []
    subjects = {e["db05_id"]: e["subject"] for e in manifest.ASSERTIONS}
    # values carried by an open conflict's recorded owner decision
    owner_carried = {i for d in manifest.RESEARCH_CONFLICTS.values()
                     if d.get("decision") == "CARRIED_NOT" and _owner_text(d.get("owner_accepted")).strip()
                     for i in d.get("touches", ())}
    seed = [c for c in research.conflicts.values() if c["engine_id"] in manifest.SEED_ENGINES]
    for c in seed:
        cid = c["conflict_id"]
        decision = manifest.RESEARCH_CONFLICTS.get(cid)
        if decision is None:
            out.append(f"{cid}: a DB-0.5 conflict on a seed engine has no decision in the manifest")
            continue
        recorded = getattr(manifest, "OWNER_DECISIONS", {})
        if "owner_accepted" in decision and decision["owner_accepted"] != recorded.get(cid):
            out.append(f"{cid}: owner_accepted is not the decision recorded in OWNER_DECISIONS")
        claims = claim_matches(c, research)
        matched = set().union(*claims) if claims else set()
        fields = re.findall(r"[A-Za-z][\w-]*(?:\.[\w-]+)+", c["field_path"])
        on_field = {aid for aid in promoted if aid in research.assertions
                    and research.assertions[aid]["engine_id"] == c["engine_id"]
                    and any(research.assertions[aid]["field_path"].startswith(f) for f in fields)}
        shipped = (matched | on_field) & promoted
        open_ = c["resolution"] in ("PARTIALLY_RESOLVED", "UNRESOLVED")
        released = set(decision.get("owner_released", ()))
        if released and not _owner_text(decision.get("owner_accepted")).strip():
            out.append(f"{cid}: owner_released needs the owner's recorded decision (owner_accepted)")
        out += [f"{cid}: owner_released {i} is a claim of the conflict; a claim is withheld or carried, "
                "never released" for i in sorted(released & matched)]
        places = {(research.assertions[i]["source_id"], research.assertions[i]["locator"])
                  for i in matched & set(decision.get("withhold", ())) if i in research.assertions}
        if released:
            # a value printed with a withheld claim, released for its configuration by the owner
            out += [f"{cid}: owner_released {i} is not a promoted assertion printed with a withheld claim"
                    for i in sorted(released) if i not in promoted or i not in research.assertions
                    or (research.assertions[i]["source_id"], research.assertions[i]["locator"]) not in places]
        if decision["decision"] == "WITHHOLD" and open_ and c["kind"] == "different_epoch":
            # an open rating epoch leaves every value of the table that prints it undefined
            # until the owner says which configuration the table describes
            mates = {aid for aid in promoted - matched if aid in research.assertions
                     and (research.assertions[aid]["source_id"], research.assertions[aid]["locator"]) in places}
            out += [f"{cid}: promoted {i} is printed in the same table as a withheld rating claim; it ships "
                    "only when released by the owner's recorded decision (owner_released) or carried by one"
                    for i in sorted(mates - released - owner_carried)]
        scope = decision.get("owner_scope")
        recorded_text = _owner_text(recorded.get(cid))
        entries = {e["db05_id"]: e for e in manifest.ASSERTIONS}
        named = set(re.findall(r"\bCFG-[A-Z0-9-]*[A-Z0-9]", recorded_text))
        if (released or named) and "owner_accepted" in decision:
            if scope is None or {scope} != named:
                out.append(f"{cid}: owner_scope {scope!r} is not the configuration the owner's decision names "
                           f"({', '.join(sorted(named)) or 'none'})")
            authorised = released | (set(decision.get("touches", ())) if decision["decision"] == "CARRIED_NOT" else set())
            out += [f"{cid}: {i} is authorised by the owner for {scope}, but is filed on {subjects.get(i)}"
                    for i in sorted(authorised) if subjects.get(i) != scope]
            # the owner's words name each value they admit, as printed
            admitted = {i: (_admitted_text(entries[i], research.assertions[i]) if i in entries
                           else research.assertions[i]["value_as_printed"])
                       for i in authorised if i in research.assertions}
            out += [f"{cid}: {i} ({text!r}) is not a value the owner's recorded decision names"
                    for i, text in sorted(admitted.items()) if not _named_in(text, recorded_text)]
        if decision["decision"] == "WITHHOLD":
            out += [f"{cid}: claim assertion {i} is not listed as withheld" for i in sorted(matched - set(decision["withhold"]))]
            out += [f"{cid}: withholds {i}, which is promoted" for i in decision["withhold"] if i in promoted]
            out += [f"{cid}: promoted {i} states the conflict's field {c['field_path']!r}"
                    for i in sorted(on_field - set(decision["withhold"]))]
        elif decision["decision"] == "CARRIED_NOT":
            if c["resolution"] == "UNRESOLVED":
                out.append(f"{cid}: UNRESOLVED, so its assertions can only be withheld")
            elif open_ and not _owner_text(decision.get("owner_accepted")).strip():
                out.append(f"{cid}: {c['resolution']} in DB-0.5; not carrying it needs the owner's recorded "
                           "decision (owner_accepted), otherwise withhold its claims")
            out += [f"{cid}: promoted claim assertion {i} is not listed in touches" for i in sorted(shipped - set(decision["touches"]))]
            out += [f"{cid}: touches {i}, which is not a promoted claim assertion" for i in decision["touches"] if i not in shipped]
            if c["resolution"] == "RESOLVED" and sum(1 for ids in claims if ids & promoted) > 1:
                out.append(f"{cid}: RESOLVED, yet promoted assertions come from more than one competing claim")
        else:
            out.append(f"{cid}: unknown decision {decision['decision']!r}")
    out += [f"{cid}: OWNER_DECISIONS records a decision its conflict does not use"
            for cid, text in getattr(manifest, "OWNER_DECISIONS", {}).items()
            if manifest.RESEARCH_CONFLICTS.get(cid, {}).get("owner_accepted") != text]
    for key, review in getattr(manifest, "OWNER_REVIEWS", {}).items():
        if not str(review.get("decision", "")).startswith("owner ("):
            out.append(f"OWNER_REVIEWS {key}: not a recorded owner decision")
        out += [f"OWNER_REVIEWS {key}: {sid} is not a shipped source" for sid in review["sources"]
                if sid not in manifest.SOURCES or sid in manifest.WITHHELD_SOURCES]
    out += [f"{cid}: decided in the manifest but not a DB-0.5 conflict on a seed engine"
            for cid in manifest.RESEARCH_CONFLICTS if cid not in {c['conflict_id'] for c in seed}]
    return out


def disposition_problems(research: Research, manifest) -> list[str]:
    """Every not-promoted assertion of an accounted engine carries a disposition that checks out."""
    out = []
    accounted = set(getattr(manifest, "ACCOUNTED_ENGINES", ()))
    vocabulary = set(getattr(manifest, "DISPOSITIONS", ()))
    withheld_by_conflict = {i for d in manifest.RESEARCH_CONFLICTS.values() for i in d.get("withhold", ())}
    for aid, why in manifest.NOT_PROMOTED.items():
        record = research.assertions.get(aid)
        if record is None or record["engine_id"] not in accounted:
            continue
        if not (isinstance(why, tuple) and len(why) == 2 and why[0] in vocabulary and str(why[1]).strip()):
            out.append(f"{aid}: needs a (disposition, reason) pair from {sorted(vocabulary)}")
            continue
        disposition = why[0]
        if disposition in ("WITHHELD_CONFLICT", "OWNER_DECISION_REQUIRED") and aid not in withheld_by_conflict:
            out.append(f"{aid}: {disposition}, but no research-conflict decision withholds it")
        sid = record["source_id"]
        doc = research.documents.get(sid, {})
        withheld_for_rights = manifest.WITHHELD_SOURCES.get(sid, {}).get("rights", sid in manifest.WITHHELD_SOURCES)
        if sid in manifest.WITHHELD_SOURCES and not withheld_for_rights and (
                restrictive_notice(doc.get("rights_statement_checked", ""))
                or "RESTRICTED_REFERENCE" in (doc.get("rights_values"), doc.get("rights_figures"))
                or doc.get("rights_values") not in SHIPPABLE_DB05_RIGHTS):
            out.append(f"{sid}: withheld with rights=False, but its rights record is restrictive")
            withheld_for_rights = True
        refused_source = (withheld_for_rights or restrictive_notice(doc.get("rights_statement_checked", ""))
                          or (doc and doc.get("read_level") != "READ_AND_MINED"))
        if refused_source and disposition not in ("WITHHELD_RIGHTS", "SOURCE_NOT_OPENED"):
            out.append(f"{aid}: its source {sid} is refused for rights or access; the disposition must say so, "
                       f"not {disposition}")
        if disposition == "WITHHELD_RIGHTS" and not source_problems(record["source_id"], research, manifest):
            out.append(f"{aid}: WITHHELD_RIGHTS, but its source {record['source_id']} passes the rights gate")
        if disposition == "SOURCE_NOT_OPENED" and record["source_id"] in research.documents \
                and research.documents[record["source_id"]].get("read_level") == "READ_AND_MINED":
            out.append(f"{aid}: SOURCE_NOT_OPENED, but {record['source_id']} was read")
    return out


def coverage_problems(research: Research, manifest) -> list[str]:
    """Every DB-0.5 assertion of a seed engine is either promoted or listed as not promoted, once."""
    promoted = [e["db05_id"] for e in manifest.ASSERTIONS]
    out = [f"{i}: promoted twice" for i in set(promoted) if promoted.count(i) > 1]
    out += [f"{i}: both promoted and listed as not promoted" for i in set(promoted) & set(manifest.NOT_PROMOTED)]
    seed = {a for a, r in research.assertions.items() if r["engine_id"] in manifest.SEED_ENGINES}
    out += [f"{i}: a DB-0.5 assertion of a seed engine is neither promoted nor listed as not promoted"
            for i in sorted(seed - set(promoted) - set(manifest.NOT_PROMOTED))]
    out += [f"{i}: listed but not a DB-0.5 assertion of a seed engine"
            for i in sorted((set(promoted) | set(manifest.NOT_PROMOTED)) - seed)]
    return out


# ------------------------------------------------------------------ builders


def build_source(sid: str, research: Research, manifest) -> EngineSource:
    doc, spec = research.documents[sid], manifest.SOURCES[sid]
    values = ShippingPolicy.VALUES_WITH_ATTRIBUTION
    url = doc.get("download_url") or doc["url_requested"]
    reference = SourceReference(
        sid, spec["organization"], tuple(spec["authors"]), spec["title"], spec["year"],
        dict(spec["identifiers"]), url, spec["source_type"], AccessClass.PUBLIC_OPEN,
        RIGHTS_IN_RECORD, values, 1)
    host = (Missing(MissingReason.NOT_REPORTED, f"no repository rights statement: not an NTRS record ({url})")
            if spec["host"] == "NONE" else
            RightsNotice(f"NTRS copyright determination: {spec['host']}",
                         f"NTRS citation API record (copyright.determinationType), retrieved {doc['retrieved_utc']}"))
    rights = RightsRecord(
        host,
        Missing(MissingReason.NOT_REPORTED, spec["printed"]),
        values, ShippingPolicy(spec["figures"]), ShippingPolicy.RIGHTS_REVIEW_REQUIRED,
        ShippingPolicy.RIGHTS_REVIEW_REQUIRED, False, RightsReview(spec["review"]), spec["review_note"])
    return EngineSource(reference, SourceAuthority(spec["authority"]), SourcePrimacy(spec["primacy"]),
                        SourceAccess.OPENED, doc["sha256"], None, rights,
                        f"downloaded {doc['retrieved_utc']} from {url}; read in DB-0.5")


def _conditions(spec: dict) -> Conditions:
    kw = {}
    for name, kind in (("environment", Environment), ("pressure_basis", PressureBasis),
                       ("pressure_station", PressureStation), ("isp_basis", IspBasis),
                       ("mixture_ratio_form", MixtureRatioForm), ("mixture_ratio_basis", MixtureRatioBasis)):
        if name in spec:
            kw[name] = kind(spec[name])
    if "mixture_ratio" in spec:
        s = spec["mixture_ratio"]
        kw["mixture_ratio"] = Setting(s["value"], s["unit"], s.get("reference", ""))
    return Conditions(**kw)


def _admitted_text(entry: dict, record: dict) -> str:
    """A text value as shipped: the printed text, or the printed parts the manifest admits."""
    text = entry["value"][0] == "text" and len(entry["value"]) > 1
    return str(entry["value"][1]) if text else record["value_as_printed"]


def build_assertion(entry: dict, research: Research) -> Assertion:
    record = research.assertions[entry["db05_id"]]
    kind = entry["value"][0]
    if kind == "number":
        value, unit = NumberValue(entry["value"][1]), record["unit_as_printed"]
    elif kind == "enum":
        value, unit = EnumValue(entry["value"][1]), ""
    else:
        value, unit = TextValue(_admitted_text(entry, record)), ""
    note = " ".join(x for x in (entry["note"], f"Read as: {entry['reading']}." if entry["reading"] else "") if x)
    return Assertion(
        entry["db05_id"], _subject(entry["subject"]), entry["field_path"], value, record["value_as_printed"],
        unit, _conditions(entry["conditions"]), ValueKind(entry["value_kind"]), ValueStatus(record["status"]),
        Admissibility.ADMITTED, record["source_id"], record["locator"], SourceAccess.OPENED,
        operating_point_id=entry["operating_point"], note=note)


def _edge_kind(fluid: str, role: str) -> tuple[EdgeKind, str | None]:
    role = role.lower()
    if "actuation" in role:
        return EdgeKind.CONTROL_ACTUATION, fluid
    if fluid == "none":
        if "gear" in role:
            return EdgeKind.GEARED_DRIVE, None
        if "linkage" in role:
            return EdgeKind.MECHANICAL_LINKAGE, None
        return EdgeKind.MECHANICAL_SHAFT, None
    return EdgeKind.FLUID_FLOW, fluid


def _group(role: str, kind: str) -> str | None:
    m = re.search(rf"{kind}_group (\w+)", role)
    return m.group(1) if m else None


def _parts(locator: str) -> set[str]:
    return {p.strip() for p in locator.split(";") if p.strip()}


def citable_locators(spec: dict, research: Research) -> set[str]:
    """Locators a restated graph element may cite: any locator part already in the DB-0.5 graph,
    or the locator (or a part of it) of a DB-0.5 assertion from one of the graph's text sources."""
    raw = research.topologies[spec["engine"]]
    out: set[str] = set()
    for x in (*raw["nodes"], *raw["edges"]):
        out |= _parts(str(x.get("locator", "")))
    for a in research.assertions.values():
        if a["source_id"] in spec["text_source_ids"]:
            out |= {a["locator"]} | _parts(a["locator"])
    return out


def topology_problems(spec: dict, research: Research, manifest, sources: set[str]) -> list[str]:
    tid, raw = spec["topology_id"], research.topologies.get(spec["engine"])
    if raw is None:
        return [f"{tid}: no DB-0.5 topology for {spec['engine']}"]
    out = []
    if spec["scope"][1] not in manifest.SEED_SUBJECTS.get(spec["engine"], ()):
        out.append(f"{tid}: scope {spec['scope'][1]} is not an identity of {spec['engine']}, whose graph this is")
    out += [f"{tid}: schematic {s} is not one the DB-0.5 graph rests on"
            for s in spec["schematic_ids"] if s not in raw["schematic_ids"]]
    out += [f"{tid}: text source {s} is not one the DB-0.5 graph rests on"
            for s in spec["text_source_ids"] if s not in raw["text_sources"]]
    nodes = {n["id"]: n for n in raw["nodes"]}
    for nid in (*spec["withhold_nodes"], *spec["restate_nodes"]):
        if nid not in nodes:
            out.append(f"{tid}: {nid} is not a node of the DB-0.5 graph")
    for i in (*spec["withhold_edges"], *spec["restate_edges"]):
        if not 0 <= i < len(raw["edges"]):
            out.append(f"{tid}: E{i:02d} is not an edge of the DB-0.5 graph")
    for i, e in enumerate(raw["edges"]):
        if i in spec["withhold_edges"]:
            continue
        for end in (e.get("from"), e.get("to")):
            if not end or end not in nodes:
                out.append(f"{tid}: E{i:02d} has an endpoint {end!r} that is not a node")
            elif end in spec["withhold_nodes"]:
                out.append(f"{tid}: E{i:02d} keeps withheld node {end}; withhold the edge too")
        if not e.get("evidence_status") or not str(e.get("locator", "")).strip():
            out.append(f"{tid}: E{i:02d} has no evidence status or locator")
    for n in raw["nodes"]:
        if not n.get("evidence_status") or not str(n.get("locator", "")).strip():
            out.append(f"{tid}: {n['id']} has no evidence status or locator")
        if n["component_type"] not in COMPONENT_TYPES and n["id"] not in spec["withhold_nodes"]:
            out.append(f"{tid}: {n['id']} has an unmapped component type {n['component_type']!r}")
    citable = citable_locators(spec, research)
    for key, what in spec["restate_nodes"].items():
        if key in nodes:
            out += _restate_problems(f"{tid}: {key}", nodes[key], what, citable, manifest)
            out += _text_basis_problems(f"{tid}: {key}", nodes[key], what, spec, research)
    for key, what in spec["restate_edges"].items():
        if 0 <= key < len(raw["edges"]):
            out += _restate_problems(f"{tid}: E{key:02d}", raw["edges"][key], what, citable, manifest)
            out += _text_basis_problems(f"{tid}: E{key:02d}", raw["edges"][key], what, spec, research)
    omissions = raw["completeness"]["known_omissions"]
    for old, new in spec.get("restate_omissions", {}).items():
        if old not in omissions:
            out.append(f"{tid}: omission {old!r} is not in the DB-0.5 graph")
        elif new != NEUTRAL_OMISSION and not (old.startswith(new) and len(new) < len(old)
                                               and old[len(new)] in " ,;(" and new.strip()):
            out.append(f"{tid}: omission {old!r} can only be cut at a word boundary or replaced by the neutral wording")
    for sid in spec["schematic_ids"]:
        sch = research.schematics.get(sid)
        if sch is None:
            out.append(f"{tid}: schematic {sid} was not viewed in DB-0.5")
            continue
        figures = research.documents.get(sch["source_id"], {}).get("rights_figures")
        if figures == "RESTRICTED_REFERENCE":
            out.append(f"{tid}: schematic {sid} is in a source whose figures are RESTRICTED_REFERENCE")
        if sch["source_id"] in manifest.WITHHELD_SOURCES or sch["source_id"] not in manifest.SOURCES:
            out.append(f"{tid}: schematic {sid} is in {sch['source_id']}, which is not a promoted source")
        drawn = manifest.SCHEMATICS.get(sid, {}).get("provenance")
        third = re.search(r"(?i)third.party|reconstruct", f"{sch.get('kind', '')} {sch.get('note', '')}")
        if third and drawn != "THIRD_PARTY_RECONSTRUCTION":
            out.append(f"{tid}: schematic {sid} is a third-party reconstruction in DB-0.5, not {drawn}")
    for sid in spec["text_source_ids"]:
        if sid in manifest.WITHHELD_SOURCES or sid not in manifest.SOURCES:
            out.append(f"{tid}: text source {sid} is not a promoted source")
    return out


#: The evidence a DB-0.5 element may be restated with: the same, or less.
_LOWER = {"DERIVED_FROM_BOTH": {"DERIVED_FROM_BOTH", "SHOWN_IN_SCHEMATIC", "REPORTED_IN_TEXT", "INFERRED"},
          "SHOWN_IN_SCHEMATIC": {"SHOWN_IN_SCHEMATIC", "INFERRED"},
          "REPORTED_IN_TEXT": {"REPORTED_IN_TEXT", "INFERRED"}, "INFERRED": {"INFERRED"}}
_RESTATABLE = {"evidence", "locator", "label", "carrier", "role", "removes", "reason", "text_basis"}


def _text_basis_problems(where: str, original: dict, change: dict, spec: dict, research: Research) -> list[str]:
    """A restated locator that keeps a text basis cites the DB-0.5 transcription of that text."""
    if "locator" not in change:
        return []
    evidence = change.get("evidence", original["evidence_status"])
    if evidence not in ("DERIVED_FROM_BOTH", "REPORTED_IN_TEXT"):
        return []
    basis = tuple(change.get("text_basis", ()))
    if not basis:
        return [f"{where}: a restated locator with a text basis names the DB-0.5 assertions that record that "
                "text (text_basis)"]
    out = []
    records = []
    for aid in basis:
        r = research.assertions.get(aid)
        if r is None or r["source_id"] not in spec["text_source_ids"]:
            out.append(f"{where}: text basis {aid} is not a DB-0.5 assertion from one of the graph's text sources")
        elif aid in _WITHHELD_BASIS:
            out.append(f"{where}: text basis {aid} is withheld or not shippable ({_WITHHELD_BASIS[aid]})")
        else:
            records.append(r)
    if not records:
        return out
    added = [p for p in _parts(change["locator"]) if p not in _parts(original.get("locator", ""))]
    for part in added:
        cited = _pages(part)
        if cited and not any(cited & _pages(r["locator"]) for r in records):
            out.append(f"{where}: the restated locator cites {part!r}, but no text basis is from that page")
    quotes = re.findall(r"'([^']{12,})'", change.get("reason", ""))
    printed = " ".join(_norm_quote(r["value_as_printed"]) for r in records)
    if quotes and not any(all(_norm_quote(f) in printed for f in q.split("...") if f.strip()) for q in quotes):
        out.append(f"{where}: none of the passages the reason quotes is in its text basis")
    return out


#: Text bases that may not be cited (filled by build_corpus): withheld or rights-refused assertions.
_WITHHELD_BASIS: dict[str, str] = {}


def _pages(locator: str) -> set[int]:
    pages = set()
    for a, b in re.findall(r"pp?\.\s*(\d+)(?:\s*-\s*(\d+))?", locator):
        pages |= set(range(int(a), int(b or a) + 1))
    return pages


def _norm_quote(text: str) -> str:
    text = re.sub(r"\s+", " ", text.lower()).strip()
    return re.sub(r"^(a|an|the) ", "", text)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\(\s*\)", "", text)).strip(" ,;:")


def _restate_problems(where: str, original: dict, change: dict, citable: set[str], manifest) -> list[str]:
    """A restatement may only lower evidence, narrow a locator, shorten a label, generalise a
    carrier by the manifest's list, and strip withheld wording from a role."""
    out = []
    if not str(change.get("reason", "")).strip():
        out.append(f"{where}: the change gives no reason")
    out += [f"{where}: {k!r} cannot be restated" for k in change if k not in _RESTATABLE]
    before = original["evidence_status"]
    if "evidence" in change and change["evidence"] not in _LOWER.get(before, set()):
        out.append(f"{where}: {before} in DB-0.5 can only keep or lower its evidence, not become {change['evidence']}")
    if "locator" in change:
        parts = [p.strip() for p in change["locator"].split(";") if p.strip()]
        bad = [p for p in parts if p not in _parts(original["locator"]) and p not in citable]
        if not parts or bad:
            out.append(f"{where}: locator parts {bad or parts} are neither whole parts of the DB-0.5 locator "
                       "nor locators the DB-0.5 graph or its text sources' assertions already use")
    if "label" in change:
        label, new = original.get("label", ""), change["label"].strip()
        head = label.split("(", 1)[0].strip()
        if new != head:
            out.append(f"{where}: a label can only be cut to the words before its parenthesis ({head!r})")
    if "carrier" in change:
        allowed = manifest.CARRIER_GENERALISATIONS.get(original.get("fluid"))
        if allowed is None or allowed[0] != change["carrier"]:
            out.append(f"{where}: carrier {original.get('fluid')!r} -> {change['carrier']!r} is not a listed generalisation")
    if "role" in change:
        removes, expected = tuple(change.get("removes", ())), original.get("role", "")
        for token in removes:
            expected = expected.replace(token, "")
        if not removes or any(tok not in original.get("role", "") for tok in removes) \
                or _norm(change["role"]) != _norm(expected):
            out.append(f"{where}: a role changes only by deleting the withheld wording it names (removes); "
                       f"expected {_norm(expected)!r}")
    return out


#: The one wording that may replace a DB-0.5 omission naming withheld content.
NEUTRAL_OMISSION = "an element known only from a rights-withheld source (not recorded)"


def build_topology(spec: dict, research: Research) -> TopologyGraph:
    raw = research.topologies[spec["engine"]]
    nodes = []
    for n in raw["nodes"]:
        if n["id"] in spec["withhold_nodes"]:
            continue
        change = spec["restate_nodes"].get(n["id"], {})
        nodes.append(TopologyNode(
            n["id"], COMPONENT_TYPES[n["component_type"]], change.get("label", n["label"]), OWNERS[n["subsystem"]],
            TopologyEvidence(change.get("evidence", n["evidence_status"])), change.get("locator", n["locator"])))
    edges = []
    for i, e in enumerate(raw["edges"]):
        if i in spec["withhold_edges"]:
            continue
        change = spec["restate_edges"].get(i, {})
        role = change.get("role", e["role"])
        kind, carrier = _edge_kind(e["fluid"], e["role"])
        carrier = change.get("carrier", carrier)
        edges.append(TopologyEdge(
            f"E{i:02d}", e["from"], e["to"], kind, carrier, role,
            TopologyEvidence(change.get("evidence", e["evidence_status"])), change.get("locator", e["locator"]),
            _group(e["role"], "split"), _group(e["role"], "merge")))
    restated = spec.get("restate_omissions", {})
    omissions = (*(restated.get(o, o) for o in raw["completeness"]["known_omissions"]), *spec["withhold_nodes"].values(),
                 *dict.fromkeys(spec["withhold_edges"].values()), *spec["extra_omissions"])
    return TopologyGraph(
        spec["topology_id"], SubjectRef(SubjectKind(spec["scope"][0]), spec["scope"][1]), spec["label"],
        SchematicProvenance.ROCKETFORGE_DERIVED_GRAPH, tuple(spec["schematic_ids"]), tuple(spec["text_source_ids"]),
        Completeness(False, tuple(dict.fromkeys(omissions))), tuple(nodes), tuple(edges), spec["notes"])


def _identities(manifest):
    families = tuple(EngineFamily(*f) for f in manifest.FAMILIES)
    variants = tuple(EngineVariant(*v) for v in manifest.VARIANTS)
    configurations = []
    for cid, vid, label, effective, notes in manifest.CONFIGURATIONS:
        if isinstance(effective, tuple):
            effective = Missing(MissingReason(effective[1]), effective[2])
        configurations.append(EngineConfiguration(cid, vid, label, effective, notes))
    points = tuple(OperatingPoint(*p) for p in manifest.OPERATING_POINTS)
    units = tuple(PropulsionUnit(uid, PropulsionUnitKind(kind), designation,
                                 tuple(UnitMember(_subject(m), count, role) for m, count, role in members), notes)
                  for uid, kind, designation, members, notes in manifest.UNITS)
    aliases = tuple(Alias(aid, name, AliasKind(kind), _subject(target), tuple(sids))
                    for aid, name, kind, target, sids in manifest.ALIASES)
    return families, variants, tuple(configurations), points, units, aliases


def leak_problems(corpus: EngineEvidenceCorpus, manifest) -> list[str]:
    """Withheld sources cited by a shipped locator, or withheld content in shipped words."""
    tokens = withheld_tokens(manifest)
    located = [(a.assertion_id, a.locator) for a in corpus.assertions]
    located += [(s.schematic_id, s.locator) for s in corpus.schematics]
    located += [(f"{t.topology_id}.{getattr(x, 'node_id', None) or x.edge_id}", x.locator)
                for t in corpus.topologies for x in (*t.nodes, *t.edges)]
    out = [f"{where}: locator cites a withheld source ({text})" for where, text in located
           if any(tok in text for tok in tokens)]
    for cfg, terms in manifest.WITHHELD_CONTENT_TERMS.items():
        terms = tuple(t.lower() for t in terms)
        units = {u.unit_id for u in corpus.units
                 if SubjectRef(SubjectKind.CONFIGURATION, cfg) in {m.member for m in u.members}}
        worded = [(a.assertion_id, f"{a.value_as_printed} {a.note}") for a in corpus.assertions
                  if corpus.configuration_of(a.subject) == cfg or a.subject.kind is SubjectKind.VARIANT
                  or (a.subject.kind is SubjectKind.PROPULSION_UNIT and a.subject.id in units)]
        worded += [(c.configuration_id, f"{c.label} {c.notes}") for c in corpus.configurations
                   if c.configuration_id == cfg]
        config = next((c for c in corpus.configurations if c.configuration_id == cfg), None)
        if config is not None:
            variant = next(v for v in corpus.variants if v.variant_id == config.variant_id)
            family = next(f for f in corpus.families if f.family_id == variant.family_id)
            worded += [(variant.variant_id, f"{variant.designation} {variant.notes}"),
                       (family.family_id, f"{family.name} {family.notes}")]
        worded += [(u.unit_id, f"{u.designation} {u.notes}") for u in corpus.units if u.unit_id in units]
        for t in corpus.topologies:
            if t.scope != SubjectRef(SubjectKind.CONFIGURATION, cfg) and not (
                    t.scope.kind is SubjectKind.PROPULSION_UNIT and t.scope.id in units):
                continue
            worded.append((t.topology_id, " ".join((t.label, t.notes, *t.completeness.known_omissions))))
            worded += [(f"{t.topology_id}.{n.node_id}", n.label) for n in t.nodes]
            worded += [(f"{t.topology_id}.{e.edge_id}", f"{e.role} {e.carrier or ''}") for e in t.edges]
        out += [f"{where}: carries withheld wording {term!r}" for where, text in worded
                for term in terms if term in text.lower()]
    return out


def build_corpus(research: Research | None = None, manifest=None) -> EngineEvidenceCorpus:
    """The seed corpus, or :class:`PromotionError` naming every entry that failed a gate."""
    research = load_research() if research is None else research
    manifest = load_manifest() if manifest is None else manifest
    _RESEARCH.clear()
    _RESEARCH.update(research.assertions)
    _WITHHELD_BASIS.clear()
    for d in manifest.RESEARCH_CONFLICTS.values():
        _WITHHELD_BASIS.update({i: "withheld by a conflict decision" for i in d.get("withhold", ())})
    for i, why in manifest.NOT_PROMOTED.items():
        if isinstance(why, tuple) and why[0] not in ("NOT_NEEDED", "DUPLICATE"):
            _WITHHELD_BASIS[i] = why[0]
    _LOCATORS.clear()
    _LOCATORS.update({aid: (r["source_id"], r["locator"]) for aid, r in research.assertions.items()})
    problems = coverage_problems(research, manifest) + disposition_problems(research, manifest)
    for entry in manifest.ASSERTIONS:
        problems += assertion_problems(entry, research, manifest)
    promoted = {e["db05_id"] for e in manifest.ASSERTIONS}
    problems += conflict_problems(research, manifest, promoted)
    problems += excerpt_owner_problems(manifest)
    problems += op_basis_problems(research, manifest)
    used = {research.assertions[i]["source_id"] for i in promoted if i in research.assertions}
    for spec in manifest.TOPOLOGIES:
        used |= set(spec["text_source_ids"])
        used |= {research.schematics[s]["source_id"] for s in spec["schematic_ids"] if s in research.schematics}
    for _, _, _, _, sids in manifest.ALIASES:
        used |= set(sids)
    for sid in sorted(used):
        problems += source_problems(sid, research, manifest)
    problems += [f"{sid}: listed in the manifest but nothing promoted uses it"
                 for sid in sorted(set(manifest.SOURCES) - used)]
    for spec in manifest.TOPOLOGIES:
        problems += topology_problems(spec, research, manifest, used)
    if problems:
        raise PromotionError(problems)

    sources = tuple(build_source(sid, research, manifest) for sid in sorted(used))
    schematics = []
    for spec in manifest.TOPOLOGIES:
        for sid in spec["schematic_ids"]:
            sch, drawn = research.schematics[sid], manifest.SCHEMATICS[sid]
            schematics.append(Schematic(sid, sch["source_id"], sch["locator"], sch["title_as_printed"],
                                        SchematicProvenance(drawn["provenance"]), drawn["drawn_by"],
                                        sch["legibility"],
                                        " ".join(x for x in (sch.get("note", ""), drawn.get("notes", "")) if x)))
    topologies = tuple(build_topology(spec, research) for spec in manifest.TOPOLOGIES)
    families, variants, configurations, points, units, aliases = _identities(manifest)
    corpus = EngineEvidenceCorpus(
        sources=sources, families=families, variants=variants, configurations=configurations,
        operating_points=points, units=units, aliases=aliases, lineage=(), components=(),
        schematics=tuple(schematics), topologies=topologies,
        assertions=tuple(build_assertion(e, research) for e in manifest.ASSERTIONS), conflicts=())
    leaks = leak_problems(corpus, manifest)
    if leaks:
        raise PromotionError(leaks)
    violations = admission_violations(corpus)
    if violations:
        raise PromotionError(violations)
    return corpus


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the shipped file would change")
    args = parser.parse_args(argv)
    text = corpus_to_json(build_corpus())
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if current != text:
            print(f"{OUTPUT.relative_to(ROOT)} is out of date; run without --check")
            return 1
        print(f"{OUTPUT.relative_to(ROOT)} is up to date")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
