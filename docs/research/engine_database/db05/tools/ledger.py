"""DB-0.5 evidence ledger: registries filled by ledger_<anchor>.py modules, emitted as JSON."""
import json
from pathlib import Path

HERE = Path(__file__).parent
DB0_DISPOSITIONS = []
DOCS, ASSERTIONS, SCHEMATICS, TOPOLOGIES, CONFLICTS, BLOCKED = {}, [], {}, {}, [], {}
_count = {}


def D(source_id, *, identifier, title, tier, rights_checked, rights_class, figures_rights=None, note=""):
    DOCS[source_id] = dict(source_id=source_id, identifier_verified=identifier, title_as_printed=title, tier=tier,
                           rights_statement_checked=rights_checked, rights_values=rights_class,
                           rights_figures=figures_rights or rights_class, note=note)


def BLOCK(source_id, reason, note=""):
    BLOCKED[source_id] = dict(source_id=source_id, status="ACCESS_BLOCKED", reason=reason, note=note)


def A(engine_id, field_path, op, printed, value, unit, conditions, source_id, locator, *, db0, status="REPORTED",
      disposition=None, note=""):
    key = engine_id.replace("ENG-", "")
    _count[key] = _count.get(key, 0) + 1
    if disposition is None:
        disposition = "PROMOTED"
    ASSERTIONS.append(dict(
        assertion_id=f"AS-DB05-{key}-{_count[key]:03d}", engine_id=engine_id, field_path=field_path, operating_point=op,
        value_as_printed=printed, value=value, unit_as_printed=unit, conditions=conditions, status=status,
        evidence_status="SOURCE_VERIFIED" if disposition == "PROMOTED" else "SOURCE_VERIFIED_NOT_PROMOTED",
        disposition=disposition, source_id=source_id, locator=locator, access="fetched",
        db0_link=None if db0 is None else dict(engine_id=db0[0], assertion_index=db0[1], outcome=db0[2]), note=note))


def S(schematic_id, *, engine_ids, source_id, locator, title, kind, viewed_how, legible, db0_schematic_id=None, note=""):
    SCHEMATICS[schematic_id] = dict(schematic_id=schematic_id, engine_ids=engine_ids, source_id=source_id, locator=locator,
                                    title_as_printed=title, kind=kind, verification="VERIFIED_VIEWED", viewed_how=viewed_how,
                                    legibility=legible, db0_schematic_id=db0_schematic_id, note=note)


def T(engine_id, *, configuration, schematic_ids, text_sources, nodes, edges, omissions, note=""):
    TOPOLOGIES[engine_id] = dict(engine_id=engine_id, configuration=configuration, schematic_ids=schematic_ids,
                                 text_sources=text_sources,
                                 completeness=dict(declared_complete=False, known_omissions=omissions),
                                 nodes=[dict(zip(["id", "component_type", "label", "subsystem", "evidence_status", "locator"], n)) for n in nodes],
                                 edges=[dict(zip(["from", "to", "fluid", "role", "evidence_status", "locator"], e)) for e in edges],
                                 note=note)


def C(conflict_id, *, engine_id, field_path, claims, resolution, kind=None, explanation="", db0_conflict_id=None):
    CONFLICTS.append(dict(conflict_id=conflict_id, db0_conflict_id=db0_conflict_id, engine_id=engine_id, field_path=field_path,
                          claims=claims, resolution=resolution, kind=kind, explanation=explanation))


def X(engine_id, index, outcome, evidence, note=""):
    """Disposition of one DB-0 anchor assertion after opening sources."""
    DB0_DISPOSITIONS.append(dict(engine_id=engine_id, db0_assertion_index=index, outcome=outcome, evidence=evidence, note=note))
