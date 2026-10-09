"""DB-2A promotion manifest: exactly what moves from DB-0.5 research into shipped reference data.

Read this file to review the seed corpus. Nothing is promoted by a rule such as
"every SOURCE_VERIFIED assertion": every source, assertion, topology element and
research-conflict decision below is named one by one, with the reason. The
promotion script (``promote_db2a.py``) checks every entry against the DB-0.5
records and refuses the whole build if one fails a gate; it never fills a gap.

Three seeds, and only three:

* J-2 at the 230,000 lb nominal vacuum thrust rating, MR 5.5 calibration point;
* RL10A-3-3A at its 475 psia, O/F 5.0 point;
* Apollo SPS engine (AJ10-137), Block I.

Values are about the configuration the source prints them for. A statement a
source makes about "the J-2" or "the SPS engine" in general is promoted, when
it is promoted at all, as a statement about the *variant* -- context, never a
value of the configuration.
"""

from __future__ import annotations

SEED_ENGINES = ("ENG-US-J-2", "ENG-US-RL10A-3-3A", "ENG-US-AJ10-137")

#: The DB-0.5 engine id of each seed, and the identities its statements may be about.
SEED_SUBJECTS = {
    "ENG-US-J-2": ("FAM-J2", "VAR-J2", "CFG-J2-230K"),
    "ENG-US-RL10A-3-3A": ("FAM-RL10", "VAR-RL10A-3-3A", "CFG-RL10A-3-3A"),
    "ENG-US-AJ10-137": ("FAM-AJ10", "VAR-AJ10-137", "CFG-SPS-BLOCK-I", "UNIT-SPS-BLOCK-I"),
}

# ------------------------------------------------------------------ sources
#
# The rights reading per source. ``host`` is the repository's statement, copied
# from the NTRS record DB-0.5 fetched; ``printed`` records the page check. Every
# source below was searched (extracted text of every page, and the viewgraph
# pages viewed) for a copyright, proprietary or reproduction notice on
# 2026-10-09; none was found. The owner accepted these readings as reviewed on
# 2026-10-09; that acceptance changes no policy (values ship with attribution,
# never as public domain). Values ship with attribution. Figures are not
# shipped, so their policy is what DB-0.5 recorded; tables and running text are
# not shipped either and stay RIGHTS_REVIEW_REQUIRED.

_NO_NOTICE = ("no copyright, proprietary or reproduction notice in the extracted text of any page, "
              "nor on the pages viewed (checked 2026-10-09)")

SOURCES = {
    "SRC-NTRS-20100027318": dict(
        organization="NASA (Remembering the Giants: Apollo Rocket Propulsion Development)",
        authors=("Paul Coffman",), title="Rocketdyne - J-2 Saturn V 2nd & 3rd Stage Engine", year=2009,
        identifiers={"NTRS": "20100027318"},
        source_type="Rocketdyne engineer's programme history with Rocketdyne viewgraphs, printed by NASA",
        authority="A", primacy="PRIMARY", host="PUBLIC_USE_PERMITTED", printed=_NO_NOTICE, review="CONSISTENT",
        figures="RIGHTS_REVIEW_REQUIRED",
        review_note="NTRS permits public use; no notice on the pages. The viewgraphs are Rocketdyne's, "
                    "so figures are not shipped; values are, with attribution. Owner-reviewed 2026-10-09."),
    "SRC-NTRS-19950022693": dict(
        organization="NASA Lewis Research Center (NYMA, Inc., contract NAS 3-27186)",
        authors=("Michael P. Binder",), title="A Transient Model of the RL10A-3-3A Rocket Engine", year=1995,
        identifiers={"NTRS": "19950022693", "NASA": "CR-195478", "AIAA": "95-2968"},
        source_type="NASA contractor report", authority="A", primacy="PRIMARY",
        host="GOV_PUBLIC_USE_PERMITTED", printed=_NO_NOTICE, review="CONSISTENT", figures="VALUES_WITH_ATTRIBUTION",
        review_note="NTRS government public use; no notice on the pages. Owner-reviewed 2026-10-09."),
    "SRC-NTRS-19910018888": dict(
        organization="Pratt & Whitney (United Technologies), presented at the Space Transportation "
                     "Propulsion Technology Symposium",
        authors=("James R. Brown",), title="Cryogenic Upper Stage Propulsion: RL10 and Derivative Engines",
        year=1990, identifiers={"NTRS": "19910018888", "NASA accession": "N91-28202"},
        source_type="manufacturer viewgraphs, printed in NASA conference proceedings",
        authority="A", primacy="PRIMARY", host="GOV_PUBLIC_USE_PERMITTED", printed=_NO_NOTICE, review="CONSISTENT",
        figures="VALUES_WITH_ATTRIBUTION",
        review_note="NTRS government public use; no notice on the viewgraphs (all 25 pages viewed). Owner-reviewed 2026-10-09."),
    "SRC-NASA-TND7375": dict(
        organization="NASA Lyndon B. Johnson Space Center",
        authors=("C. R. Gibson", "J. A. Wood"),
        title="Apollo Experience Report - Service Propulsion Subsystem", year=1973,
        identifiers={"NTRS": "19730023031", "NASA": "TN D-7375", "JSC": "S-378"},
        source_type="NASA technical note", authority="A", primacy="PRIMARY",
        host="GOV_PUBLIC_USE_PERMITTED", printed=_NO_NOTICE, review="CONSISTENT", figures="VALUES_WITH_ATTRIBUTION",
        review_note="NTRS government public use; a NASA technical note with no notice on the pages. Owner-reviewed 2026-10-09."),
    "SRC-NTRS-20100027319": dict(
        organization="NASA (Remembering the Giants: Apollo Rocket Propulsion Development)",
        authors=("Clay Boyce",), title="Aerojet - AJ10-137 Apollo Service Module Engine", year=2009,
        identifiers={"NTRS": "20100027319"},
        source_type="Aerojet engineer's programme history, printed by NASA", authority="A",
        primacy="PRIMARY", host="PUBLIC_USE_PERMITTED", printed=_NO_NOTICE, review="CONSISTENT",
        figures="VALUES_WITH_ATTRIBUTION",
        review_note="NTRS permits public use; no notice on the pages. Speaker recollection: only the "
                    "propellant identity is promoted from it, at variant level. Owner-reviewed 2026-10-09."),
}

#: Sources whose content DB-2A must not carry, with the reason and the tokens by
#: which a locator would cite them. The promotion refuses any assertion, schematic
#: or text source from them, and any shipped locator containing a token.
WITHHELD_SOURCES = {
    "SRC-DB05-NTRS-19750063889": dict(
        reason="MSFC-MAN-503: NTRS says GOV_PUBLIC_USE_PERMITTED but p.A prints 'Reproduction for "
               "non-government use ... is not permitted without specific approval'; rights "
               "CONFLICT_UNRESOLVED, so its payload is withheld",
        locator_tokens=("MSFC", "19750063889", "Saturn V Flight Manual", "SA-503")),
    "SRC-NTRS-20120016414": dict(
        reason="J-2X paper: its J-2 column names no rating or configuration; not needed",
        locator_tokens=("20120016414", "J-2X", "System Engineering and Technical Challenges"),
        rights=False),
}

#: Words that would carry withheld content (what only MSFC-MAN-503 says about the
#: J-2) into a shipped label, role, omission or note of that configuration's
#: record. The promotion refuses them there.
WITHHELD_CONTENT_TERMS = {
    "CFG-J2-230K": ("hydraulic", "direct drive", "discharge-to-inlet", "discharge side", "PU valve",
                    "STDV", "servovalve", "exhaust duct", "fuel manifold"),
}

# ------------------------------------------------------------------ identity

FAMILIES = (
    ("FAM-J2", "J-2", ""),
    ("FAM-RL10", "RL10", ""),
    ("FAM-AJ10", "AJ10", "Aerojet AJ10 storable-propellant engines."),
)

VARIANTS = (
    ("VAR-J2", "FAM-J2", "J-2", ""),
    ("VAR-RL10A-3-3A", "FAM-RL10", "RL10A-3-3A", ""),
    ("VAR-AJ10-137", "FAM-AJ10", "AJ10-137", "The Apollo service module (SPS) engine."),
)

#: (configuration id, variant id, label, effective, notes). ``effective`` is
#: text, or ("MISSING", reason, note).
CONFIGURATIONS = (
    ("CFG-J2-230K", "VAR-J2", "J-2, 230,000 lb nominal vacuum thrust rating",
     ("MISSING", "UNKNOWN", "which flights used the 230,000 lb rating is not established by the opened "
                            "documents; Coffman's text (p.3) also names a 225,000 lb qualification version, "
                            "and the AEDC test reports could not be opened"),
     "Defined by Rocketdyne's 'J-2 Basic Engine Features' viewgraph (NTRS 20100027318 PDF p.14). "
     "The 225,000 lb version is a different configuration and is not part of this corpus."),
    ("CFG-RL10A-3-3A", "VAR-RL10A-3-3A", "RL10A-3-3A (Centaur)",
     ("MISSING", "NOT_AUDITED", "DB-0.5 did not transcribe an effectivity for this configuration"),
     "Centaur upper stage engine (CR-195478 abstract)."),
    ("CFG-SPS-BLOCK-I", "VAR-AJ10-137", "Apollo SPS engine, Block I",
     "the Block I vehicles (TN D-7375 p.3: 'The 2:1 ratio was used in the Block I vehicles')",
     "Block I as described in TN D-7375 pp.3-5. Block II (O/F 1.6:1) is a different configuration and "
     "is not part of this corpus."),
)

OPERATING_POINTS = (
    ("OP-J2-230K-MR55", "CFG-J2-230K", "engine mixture ratio calibration 5.5:1 (O/F)",
     "The one point of the 'Performance & Weight' table on the 230,000 lb viewgraph."),
    ("OP-RL10A-3-3A-475-OF5", "CFG-RL10A-3-3A", "475 psia, O/F 5.0",
     "The point of Pratt & Whitney's 'RL10A-3-3A ENGINE' table (NTRS 19910018888 p.3: chamber "
     "pressure 475 psia, mixture ratio 5:1, Isp 'at 5.0 O/F') and CR-195478's 'normal operating "
     "point of 475 psia and O/F = 5.0' (section 4.3)."),
    ("OP-SPS-BLOCK-I-OF2", "CFG-SPS-BLOCK-I", "Block I operation, O/F 2:1",
     "TN D-7375 p.3: 'The 2:1 ratio was used in the Block I vehicles'; p.5 gives the Block I engine's "
     "chamber pressure, vacuum thrust and average specific impulse."),
)

UNITS = (
    ("UNIT-SPS-BLOCK-I", "STAGE_PROPULSION", "Apollo service propulsion subsystem, Block I",
     (("CFG-SPS-BLOCK-I", 1, "rocket-engine assembly"),),
     "TN D-7375 p.3: the Block I subsystem consisted of a helium-pressurization assembly, a "
     "propellant-supply and propellant-distribution assembly, a propellant-utilization and "
     "propellant-gaging assembly, a rocket-engine assembly, instrumentation, and displays and controls."),
)

#: (alias id, name, kind, target, source ids)
ALIASES = (
    ("ALIAS-SPS-ENGINE", "SPS engine", "INFORMAL", "VAR-AJ10-137",
     ("SRC-NASA-TND7375", "SRC-NTRS-20100027319")),
)

# ------------------------------------------------------------------ assertions
#
# One entry per promoted DB-0.5 assertion; the production assertion keeps the
# DB-0.5 id, its value as printed, its unit as printed, its locator and its
# status. Each entry states the subject (a CFG-, VAR-, FAM- or UNIT- id), the
# production field path, the typed value, the value kind, the operating point
# and the conditions. ``("text",)`` means the value is the printed text itself.
# Where the printed text is not a bare number, ``reading`` says how the number
# was read from it.


def P(db05_id, subject, field, value, kind, *, op=None, op_basis="", cond=None, reading="", note=""):
    return dict(db05_id=db05_id, subject=subject, field_path=field, value=value, value_kind=kind,
                operating_point=op, op_basis=op_basis, conditions=cond or {}, reading=reading, note=note)


_J2, _J2OP = "CFG-J2-230K", "OP-J2-230K-MR55"
_RL, _RLOP = "CFG-RL10A-3-3A", "OP-RL10A-3-3A-475-OF5"
_SPS, _SPSOP = "CFG-SPS-BLOCK-I", "OP-SPS-BLOCK-I-OF2"

ASSERTIONS = (
    # J-2, 230,000 lb rating: the 'J-2 Basic Engine Features' viewgraph
    P("AS-DB05-US-J-2-001", _J2, "performance.thrust_vac", ("number", 230000), "NOMINAL", op=_J2OP,
      op_basis="AS-DB05-US-J-2-004 (the same table's engine mixture ratio calibration 5.5:1)",
      cond=dict(environment="VACUUM"),
      note="Printed as 'Nominal vacuum thrust (lb)'. In research conflict CF-DB05-J2-THRUST "
           "(PARTIALLY_RESOLVED); shipped for this configuration only, by owner decision."),
    P("AS-DB05-US-J-2-002", _J2, "performance.specific_impulse_vac", ("number", 425), "NOMINAL", op=_J2OP,
      op_basis="AS-DB05-US-J-2-004 (the same table's engine mixture ratio calibration 5.5:1)",
      cond=dict(environment="VACUUM", isp_basis="UNKNOWN"),
      note="Printed as 'Nominal vacuum specific impulse'; engine or thrust-chamber basis not stated."),
    P("AS-DB05-US-J-2-003", _J2, "performance.chamber_pressure", ("number", 717), "NOMINAL", op=_J2OP,
      op_basis="AS-DB05-US-J-2-004 (the same table's engine mixture ratio calibration 5.5:1)",
      cond=dict(pressure_basis="ABSOLUTE", pressure_station="NOZZLE_STAGNATION"),
      note="Printed as 'Chamber pressure (psia) (nozzle stagnation)'."),
    P("AS-DB05-US-J-2-004", _J2, "propellants.mixture_ratio", ("number", 5.5), "NOMINAL", op=_J2OP,
      op_basis="AS-DB05-US-J-2-003, printed in the same one-point table as this calibration",
      cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="ENGINE"),
      note="Printed as 'Engine mixture ratio calibration (O/F)'."),
    P("AS-DB05-US-J-2-005", _J2, "mechanical.mass_dry_basic", ("number", 2754), "NOMINAL",
      note="Printed as 'Basic engine dry weight (lb)'."),
    P("AS-DB05-US-J-2-006", _J2, "mechanical.mass_dry_with_accessories", ("number", 3492), "NOMINAL",
      note="Printed as 'Engine dry weight (lb) (including accessories)'."),
    P("AS-DB05-US-J-2-007", _J2, "nozzle.area_ratio", ("number", 27.5), "NOMINAL"),
    P("AS-DB05-US-J-2-024", _J2, "architecture.feed", ("enum", "PUMP_FED"), "NOMINAL"),
    P("AS-DB05-US-J-2-025", _J2, "propellants.oxidizer", ("enum", "LIQUID_OXYGEN"), "NOMINAL"),
    P("AS-DB05-US-J-2-026", _J2, "propellants.fuel", ("enum", "LIQUID_HYDROGEN"), "NOMINAL"),
    P("AS-DB05-US-J-2-027", _J2, "architecture.cycle", ("enum", "GAS_GENERATOR"), "NOMINAL",
      note="Printed as the turbine drive: 'gas generator burning main propellants'."),
    P("AS-DB05-US-J-2-028", _J2, "cooling.thrust_chamber", ("enum", "REGENERATIVE"), "NOMINAL"),
    P("AS-DB05-US-J-2-029", _J2, "turbomachinery.arrangement", ("text",), "OTHER"),
    # J-2 variant: Coffman's narrative speaks of 'the J-2', not a rating
    P("AS-DB05-US-J-2-009", "VAR-J2", "pumps.fuel.type", ("enum", "AXIAL"), "NOMINAL"),
    P("AS-DB05-US-J-2-010", "VAR-J2", "pumps.ox.type", ("enum", "CENTRIFUGAL"), "NOMINAL"),
    P("AS-DB05-US-J-2-011", "VAR-J2", "turbines.arrangement", ("text",), "OTHER"),
    P("AS-DB05-US-J-2-012", "VAR-J2", "cooling.tube_pattern", ("text",), "OTHER"),

    # RL10A-3-3A: P&W 'RL10A-3-3A ENGINE' table and CR-195478
    P("AS-DB05-US-RL10A-3-3A-009", _RL, "performance.thrust_vac", ("number", 16500), "NOMINAL", op=_RLOP,
      op_basis="P&W's 'RL10A-3-3A ENGINE' table prints this value with chamber pressure 475 psia and mixture ratio 5:1, the point CR-195478 calls 'the engine's normal operating point of 475 psia and O/F = 5.0' (AS-DB05-US-RL10A-3-3A-006)",
      cond=dict(environment="VACUUM"), note="Same table as the 475 psia chamber pressure and the 5:1 mixture ratio."),
    P("AS-DB05-US-RL10A-3-3A-010", _RL, "performance.specific_impulse", ("number", 444.4), "NOMINAL", op=_RLOP,
      op_basis="P&W's 'RL10A-3-3A ENGINE' table prints this value with chamber pressure 475 psia and mixture ratio 5:1, the point CR-195478 calls 'the engine's normal operating point of 475 psia and O/F = 5.0' (AS-DB05-US-RL10A-3-3A-006)",
      cond=dict(environment="UNKNOWN", isp_basis="UNKNOWN"),
      note="The table does not say vacuum or sea level for the specific impulse. Its mixture ratio is "
           "carried by the operating point, not restated as a condition."),
    P("AS-DB05-US-RL10A-3-3A-017", _RL, "performance.chamber_pressure", ("number", 475), "NOMINAL", op=_RLOP,
      op_basis="P&W's 'RL10A-3-3A ENGINE' table prints this value with chamber pressure 475 psia and mixture ratio 5:1, the point CR-195478 calls 'the engine's normal operating point of 475 psia and O/F = 5.0' (AS-DB05-US-RL10A-3-3A-006)",
      cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN")),
    P("AS-DB05-US-RL10A-3-3A-006", _RL, "performance.chamber_pressure", ("number", 475), "NOMINAL", op=_RLOP,
      cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN"),
      note="CR-195478 calls it 'the engine's normal operating point'."),
    P("AS-DB05-US-RL10A-3-3A-012", _RL, "propellants.mixture_ratio", ("number", 5.0), "NOMINAL", op=_RLOP,
      op_basis="P&W's 'RL10A-3-3A ENGINE' table prints this value with chamber pressure 475 psia and mixture ratio 5:1, the point CR-195478 calls 'the engine's normal operating point of 475 psia and O/F = 5.0' (AS-DB05-US-RL10A-3-3A-006)",
      cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="UNKNOWN"),
      reading="'Mixture ratio 5:1' is oxidizer to fuel: CR-195478 prints the same point as 'O/F = 5.0' "
              "(AS-DB05-US-RL10A-3-3A-006)"),
    P("AS-DB05-US-RL10A-3-3A-013", _RL, "nozzle.area_ratio", ("number", 61), "NOMINAL"),
    P("AS-DB05-US-RL10A-3-3A-011", _RL, "mechanical.mass", ("number", 305), "NOMINAL"),
    P("AS-DB05-US-RL10A-3-3A-014", _RL, "architecture.cycle", ("enum", "EXPANDER"), "NOMINAL"),
    P("AS-DB05-US-RL10A-3-3A-015", _RL, "propellants.oxidizer", ("enum", "OXYGEN"), "NOMINAL",
      note="Printed as 'hydrogen/oxygen'; the phase is not part of this statement."),
    P("AS-DB05-US-RL10A-3-3A-016", _RL, "propellants.fuel", ("enum", "HYDROGEN"), "NOMINAL",
      note="Printed as 'hydrogen/oxygen'; the phase is not part of this statement."),
    P("AS-DB05-US-RL10A-3-3A-001", _RL, "pumps.configuration", ("text",), "OTHER"),
    P("AS-DB05-US-RL10A-3-3A-002", _RL, "pumps.fuel.operating_point", ("text",), "NOMINAL", op=_RLOP),
    P("AS-DB05-US-RL10A-3-3A-003", _RL, "pumps.lox.operating_point", ("text",), "NOMINAL", op=_RLOP),
    P("AS-DB05-US-RL10A-3-3A-004", _RL, "pumps.fuel.speed_rpm", ("number", 32000), "NOMINAL", op=_RLOP),
    P("AS-DB05-US-RL10A-3-3A-005", _RL, "pumps.lox.speed_rpm", ("number", 12800), "NOMINAL", op=_RLOP),

    # Apollo SPS, Block I: TN D-7375 'Block I Configuration'
    P("AS-DB05-US-AJ10-137-001", _SPS, "performance.chamber_pressure", ("number", 102), "NOMINAL", op=_SPSOP,
      cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN"),
      note="In research conflict CF-DB05-SPS-THRUST (PARTIALLY_RESOLVED); shipped for Block I only, by owner decision, and not for Block II or the AJ10-137 in general."),
    P("AS-DB05-US-AJ10-137-002", _SPS, "performance.thrust_vac", ("number", 21500), "NOMINAL", op=_SPSOP,
      cond=dict(environment="VACUUM"),
      note="In research conflict CF-DB05-SPS-THRUST (PARTIALLY_RESOLVED); shipped for Block I only, by owner decision, and not for Block II or the AJ10-137 in general."),
    P("AS-DB05-US-AJ10-137-003", _SPS, "performance.specific_impulse", ("number", 309), "AVERAGE", op=_SPSOP,
      cond=dict(environment="UNKNOWN", isp_basis="UNKNOWN"),
      note="Printed as 'The average specific impulse'; vacuum or sea level is not stated for it. In research conflict CF-DB05-SPS-THRUST (PARTIALLY_RESOLVED); shipped for Block I only, by owner decision, and not for Block II or the AJ10-137 in general."),
    P("AS-DB05-US-AJ10-137-010", _SPS, "propellants.mixture_ratio", ("number", 2.0), "NOMINAL", op=_SPSOP,
      cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="UNKNOWN"),
      reading="'The 2:1 ratio was used in the Block I vehicles'; the same paragraph defines it as the "
              "'oxidizer-to-fuel weight ratio' (O/F)"),
    P("AS-DB05-US-AJ10-137-004", _SPS, "nozzle.area_ratio", ("number", 62.5), "NOMINAL",
      reading="the exit end of the radiation-cooled nozzle, which extends 'from an area ratio of "
              "approximately 6:1 to 62.5:1'"),
    P("AS-DB05-US-AJ10-137-023", _SPS, "architecture.feed", ("enum", "PRESSURE_FED"), "NOMINAL"),
    P("AS-DB05-US-AJ10-137-005", _SPS, "cooling.zones", ("text",), "OTHER"),
    P("AS-DB05-US-AJ10-137-006", _SPS, "life.starts_and_duration", ("text",), "OTHER", op=_SPSOP),
    P("AS-DB05-US-AJ10-137-007", _SPS, "ignition_start.method", ("enum", "HYPERGOLIC"), "NOMINAL"),
    P("AS-DB05-US-AJ10-137-008", _SPS, "control.bipropellant_valve", ("text",), "OTHER"),
    # AJ10-137 variant: the Aerojet chapter does not name a configuration
    P("AS-DB05-US-AJ10-137-018", "VAR-AJ10-137", "propellants.combination", ("text",), "OTHER",
      note="Configuration unstated in the source; recorded for the variant and not applied to Block I."),
)

#: Production field paths allowed for each DB-0.5 field path (DB-1 canonical names).
FIELD_RENAMES = {
    "performance.pc": ("performance.chamber_pressure",),
    "performance.isp_vac": ("performance.specific_impulse_vac", "performance.specific_impulse"),
    "propellants": ("propellants.combination",),
}

#: DB-0.5 operating-point labels and the seed operating point each one is.
OPERATING_POINT_MAP = {
    ("ENG-US-RL10A-3-3A", "OP-NOMINAL"): _RLOP,
    ("ENG-US-AJ10-137", "OP-BLOCK-I"): _SPSOP,
}

#: DB-0.5 ``conditions.configuration`` labels and the seed configuration each one is.
CONFIGURATION_MAP = {
    ("ENG-US-AJ10-137", "Block I"): _SPS,
}

#: Every DB-0.5 assertion of a seed engine that is NOT promoted, and why.
NOT_PROMOTED = {
    "AS-DB05-US-J-2-030": "recorded as the text basis of the J-2 graph's start tank; not shipped as a value",
    "AS-DB05-US-J-2-031": "recorded as the text basis of the J-2 graph's heat exchanger; not shipped as a value",
    "AS-DB05-US-J-2-032": "recorded as the text basis of the J-2 graph's igniter; not shipped as a value",
    "AS-DB05-US-J-2-033": "recorded as the text basis of the J-2 graph's gas generator; not shipped as a value",
    "AS-DB05-US-J-2-034": "recorded as the text basis of the J-2 graph's nozzle exhaust dump; not shipped as a value",
    "AS-DB05-US-AJ10-137-024": "recorded as the text basis of the SPS graph's injector; not shipped as a value",
    "AS-DB05-US-J-2-008": "the 4.5:1 alternate mixture ratio is another operating point, not seeded",
    "AS-DB05-US-J-2-013": "programme history (production count), not an engine property",
    "AS-DB05-US-J-2-014": "the 225,000 lb version is another configuration, not seeded",
    "AS-DB05-US-J-2-015": "J-2X paper: configuration of its J-2 column not stated",
    "AS-DB05-US-J-2-016": "J-2X paper: configuration of its J-2 column not stated",
    "AS-DB05-US-J-2-017": "J-2X paper: configuration of its J-2 column not stated",
    "AS-DB05-US-J-2-018": "MSFC-MAN-503: rights conflict unresolved, payload withheld",
    "AS-DB05-US-J-2-019": "MSFC-MAN-503: rights conflict unresolved, payload withheld",
    "AS-DB05-US-J-2-020": "MSFC-MAN-503: rights conflict unresolved, payload withheld",
    "AS-DB05-US-J-2-021": "MSFC-MAN-503: rights conflict unresolved, payload withheld",
    "AS-DB05-US-J-2-022": "MSFC-MAN-503: rights conflict unresolved, payload withheld",
    "AS-DB05-US-J-2-023": "MSFC-MAN-503: rights conflict unresolved, payload withheld",
    "AS-DB05-US-RL10A-3-3A-007": "stated for 'all models' (family level); the configuration's own cycle "
                                 "statement (-014) is promoted instead",
    "AS-DB05-US-RL10A-3-3A-008": "rejected in DB-0.5: a model-tuning parameter, not a hardware fact",
    "AS-DB05-US-AJ10-137-009": "Block II value; Block II is not seeded",
    "AS-DB05-US-AJ10-137-011": "in UNRESOLVED conflict CF-DB05-SPS-REG",
    "AS-DB05-US-AJ10-137-012": "vehicle pressurization detail beside the unresolved regulator conflict; not needed",
    "AS-DB05-US-AJ10-137-013": "Block II value; Block II is not seeded",
    "AS-DB05-US-AJ10-137-014": "Aerojet chapter: configuration not stated",
    "AS-DB05-US-AJ10-137-015": "Aerojet chapter: configuration not stated",
    "AS-DB05-US-AJ10-137-016": "Aerojet chapter: configuration not stated",
    "AS-DB05-US-AJ10-137-017": "Aerojet chapter: configuration not stated",
    "AS-DB05-US-AJ10-137-019": "Aerojet chapter: configuration not stated",
    "AS-DB05-US-AJ10-137-020": "Aerojet chapter: configuration not stated",
    "AS-DB05-US-AJ10-137-021": "Aerojet chapter: configuration not stated (a specification, not Block I)",
    "AS-DB05-US-AJ10-137-022": "Aerojet chapter: configuration not stated",
}

# ------------------------------------------------------------------ research conflicts
#
# Every DB-0.5 conflict on a seed engine, decided. The promotion matches each
# conflict's claims to DB-0.5 assertions (same source, a printed number in common)
# and checks the decision against what it finds.
#
# WITHHOLD: every assertion the conflict's claims match is not promoted.
# CARRIED_NOT: the conflict is not carried into the seed corpus. ``touches`` must
# list every promoted assertion its claims match. Allowed for RESOLVED (all
# promoted matches from one claim) and EXPLAINED conflicts. An UNRESOLVED or
# PARTIALLY_RESOLVED conflict is WITHHOLD unless ``owner_accepted`` records the
# owner's decision (who and when). Two entries below carry one, recorded from the
# owner's DB-2A decisions of 2026-10-09; the DB-0.5 conflicts themselves are unchanged.

RESEARCH_CONFLICTS = {
    "CF-DB05-SPS-REG": dict(decision="WITHHOLD", withhold=("AS-DB05-US-AJ10-137-011",),
                            argument="Regulated helium pressure is in UNRESOLVED conflict; not promoted."),
    "CF-DB05-J2-PC": dict(decision="CARRIED_NOT", touches=("AS-DB05-US-J-2-003",),
                          competing={"Coffman text p.2 'a little over 700 psia'": "not transcribed as an assertion; consistent with 717",
                                     "SRC-WIKI-J2 763 psi": "search result, never opened"},
                          argument="RESOLVED in DB-0.5 in favour of 717 psia at nozzle stagnation."),
    "CF-DB05-J2-MASS": dict(decision="CARRIED_NOT", touches=("AS-DB05-US-J-2-005", "AS-DB05-US-J-2-006"),
                            competing={"AS-DB05-US-J-2-017": "not promoted (J-2X paper)",
                                       "SRC-WIKI-J2 / SRC-PURDUE-J2 / SRC-ASTRONAUTIX-J2": "search results, never opened"},
                            argument="EXPLAINED: the two promoted values are two printed definitions "
                                     "(basic, and including accessories), kept as two field paths."),
    "CF-DB05-J2-THRUST": dict(
        decision="CARRIED_NOT", touches=("AS-DB05-US-J-2-001",),
        owner_accepted="owner (Cemil Eray), 2026-10-09: accept the thrust re-scoping for the DB-2A 230,000 lbf / MR 5.5 "
                       "configuration only. The research conflict stays as recorded in DB-0.5.",
        competing={"AS-DB05-US-J-2-014": "225,000 lb version: a different configuration, not seeded",
                   "AS-DB05-US-J-2-015": "not promoted; it agrees (230 klbf)",
                   "SRC-WIKI-J2 232,250 lbf": "search result, never opened; configuration unknown"},
        argument="PARTIALLY_RESOLVED in DB-0.5 because flight effectivity of the two ratings and the "
                 "232,250 lbf figure are not established. Re-scoping (owner-accepted): the seed configuration "
                 "is defined by the 230,000 lb rating itself and no opened source gives another value for it, "
                 "so the open part is effectivity, recorded as the configuration's 'effective' = "
                 "Missing(UNKNOWN). The competing claims (225,000 lb, J-2X paper, search result) stay "
                 "unpromoted."),
    "CF-DB05-RL10A33A-MR-ISP": dict(
        decision="CARRIED_NOT",
        touches=("AS-DB05-US-RL10A-3-3A-006", "AS-DB05-US-RL10A-3-3A-010", "AS-DB05-US-RL10A-3-3A-012"),
        competing={"SRC-NAP-11780 Table D-2": "not a seed source; 444 s agrees, 442 is the RL10A-3-3",
                   "DB-0 Purdue 442.4 s at 5.5:1": "search result; mixes variants"},
        argument="EXPLAINED (different variant)."),
    "CF-DB05-SPS-THRUST": dict(
        decision="CARRIED_NOT",
        touches=("AS-DB05-US-AJ10-137-001", "AS-DB05-US-AJ10-137-002", "AS-DB05-US-AJ10-137-003"),
        owner_accepted="owner (Cemil Eray), 2026-10-09: accept the Block I re-scoping; ship 21,500 lbf vacuum thrust, 102 psia "
                       "and 309 s for Block I only, never for Block II or the SPS family. The research "
                       "conflict stays as recorded in DB-0.5.",
        competing={"AS-DB05-US-AJ10-137-014": "Aerojet 'general configuration' 20,000 lb; configuration "
                                              "not stated, not promoted",
                   "SRC-WIKI-AJ10 20,500 lbf": "search result, never opened"},
        argument="PARTIALLY_RESOLVED in DB-0.5 because no Block II flight rating was found. Its Block I "
                 "claim (21 500 lb, 102 psia, 309 s) stands against Aerojet's configuration-unstated 20,000 lb, "
                 "100 psi, 314.5 s. Re-scoping (owner-accepted): the Block I values are printed in TN D-7375's "
                 "Block I section and Aerojet states no configuration; Aerojet's values stay unpromoted."),
}

#: The owner's recorded decisions. An ``owner_accepted`` in any manifest must
#: equal the entry here; the promotion refuses any other.
OWNER_DECISIONS = {
    "CF-DB05-J2-THRUST": ("owner (Cemil Eray), 2026-10-09: accept the thrust re-scoping for the DB-2A 230,000 lbf / MR 5.5 "
                       "configuration only. The research conflict stays as recorded in DB-0.5."),
    "CF-DB05-SPS-THRUST": ("owner (Cemil Eray), 2026-10-09: accept the Block I re-scoping; ship 21,500 lbf vacuum thrust, 102 psia "
                       "and 309 s for Block I only, never for Block II or the SPS family. The research "
                       "conflict stays as recorded in DB-0.5."),
}

# ------------------------------------------------------------------ schematics and topology

#: The only carrier changes a restatement may make, and why.
CARRIER_GENERALISATIONS = {
    "A-50": ("fuel", "TN D-7375 names the oxidizer but never the fuel; 'A-50' came from the Aerojet chapter, "
                     "which states no configuration"),
    "N2O4 + A-50": ("N2O4 + fuel", "as for 'A-50'"),
}

#: Who drew each schematic a seed graph rests on.
SCHEMATICS = {
    "SCH-DB05-J2-COFFMAN-S4": dict(provenance="ORIGINAL_MANUFACTURER",
                                   drawn_by="Rocketdyne (viewgraph CP6_0450_J2-4.ppt), as printed by NASA"),
    "SCH-DB05-RL10A33A-CR195478-F1": dict(provenance="ORIGINAL_CONTRACTOR",
                                          drawn_by="as printed in NASA CR-195478 (NYMA, Inc., under NASA "
                                                   "contract NAS 3-27186); the draftsman is not stated",
                                          notes="ORIGINAL_CONTRACTOR accepted by the owner 2026-10-09: an "
                                                "original drawing in a NASA contractor report. It is not "
                                                "ORIGINAL_MANUFACTURER; it is not a Pratt & Whitney drawing."),
    "SCH-DB05-SPS-TND7375-F2": dict(provenance="ORIGINAL_AGENCY",
                                    drawn_by="NASA, as printed in TN D-7375"),
}

_MSFC = "MSFC-MAN-503 is withheld (rights conflict unresolved)"
_S = "AS-DB05-US-AJ10-137-0"
#: The TN D-7375 transcriptions each restated SPS engine element rests on.
_SPS_BASIS = {"N-BIPROP": (_S + "08",), "N-INJ": (_S + "24",), "N-TC": (_S + "05",), "N-NOZ": (_S + "05", _S + "04"),
              "N-AMB": (_S + "05",)}
_C2 = "NTRS 20100027318 slide J2-4; NTRS 20100027318 text p.2"  # both parts are DB-0.5 graph locators

#: One entry per seed graph. Node ids, component types, ownership, edge order
#: (edge ids are E<DB-0.5 index>), carriers, roles and locators are copied
#: from DB-0.5 except where an entry below says otherwise, with its reason.
#: ``withhold_nodes`` / ``withhold_edges`` leave an element out and add its
#: omission; nothing is ever recorded as absent. A restatement may only keep or
#: lower an element's evidence; cite only locator parts the DB-0.5 graph or its
#: text sources' DB-0.5 assertions already use; cut its label to the words before
#: its parenthesis; generalise a carrier by ``CARRIER_GENERALISATIONS``; and
#: change a role only by deleting the withheld wording it names in ``removes``.
TOPOLOGIES = (
    dict(engine="ENG-US-J-2", topology_id="TOPO-J2-230K", scope=("CONFIGURATION", _J2),
         label="J-2 engine flow (Rocketdyne J-2 Engine Schematic, same viewgraph set as the 230,000 lb table)",
         schematic_ids=("SCH-DB05-J2-COFFMAN-S4",), text_source_ids=("SRC-NTRS-20100027318",),
         withhold_nodes={"N-HYD-PUMP": "one component known only from a rights-withheld source (not recorded)"},
         withhold_edges={
             5: "mixture ratio control valve flow connections (not described in the sources used)",
             6: "mixture ratio control valve flow connections (not described in the sources used)",
             25: "turbine-to-pump drive of each turbopump: shaft or gear not stated in the sources used",
             26: "turbine-to-pump drive of each turbopump: shaft or gear not stated in the sources used",
             27: "one drive relation known only from a rights-withheld source (not recorded)"},
         restate_nodes={
             "N-OTP-P": dict(text_basis=("AS-DB05-US-J-2-010",), locator=_C2, reason="text basis restated: Coffman text p.2 'The oxidizer turbopump was a fairly conventional centrifugal device'"),
             "N-FTP-P": dict(text_basis=("AS-DB05-US-J-2-009",), locator=_C2, reason="text basis restated: Coffman text p.2 'The fuel turbopump was an axial machine'"),
             "N-OTP-T": dict(text_basis=("AS-DB05-US-J-2-011",), locator=_C2, reason=f"{_MSFC}; slide draws the turbopump's hot-gas inlet, text p.2 gives the series turbines"),
             "N-FTP-T": dict(text_basis=("AS-DB05-US-J-2-011",), locator=_C2, reason=f"{_MSFC}; slide draws the turbopump's hot-gas inlet, text p.2 gives the series turbines"),
             "N-MRCV": dict(evidence="SHOWN_IN_SCHEMATIC", locator="NTRS 20100027318 slide J2-4",
                            label="Mixture ratio control valve",
                            reason="no Coffman text describes it; the text basis and the label's '(PU valve)' "
                                   "came from MSFC-MAN-503 (withheld); label reduced to the slide's own words"),
             "N-GG": dict(locator=_C2, text_basis=("AS-DB05-US-J-2-033",), reason="text basis restated: Coffman text p.2 'The gas generator drove the turbomachinery'"),
             "N-OTBV": dict(text_basis=("AS-DB05-US-J-2-011",), locator=_C2, reason="text basis restated: Coffman text p.2 'with a bypass for calibration'"),
             "N-HEX": dict(locator=_C2, text_basis=("AS-DB05-US-J-2-031",), label="Heat exchanger",
                           reason=f"{_MSFC}; label reduced to the slide's 'Heat Exchanger' (its location in the oxidizer turbine exhaust duct was MSFC's); text p.2 'a heat exchanger to heat up oxygen for tank pressurization'"),
             "N-STANK": dict(text_basis=("AS-DB05-US-J-2-030",), locator=_C2, reason="text basis restated: Coffman text p.2 'this start tank that would discharge cold hydrogen through the two turbines'"),
             "N-TC-COOL": dict(locator=_C2, text_basis=("AS-DB05-US-J-2-012",), reason=f"{_MSFC}; slide draws the tubular chamber, text p.2 'a fully tubular thrust chamber'"),
             "N-NOZ-DUMP": dict(text_basis=("AS-DB05-US-J-2-011", "AS-DB05-US-J-2-034"), locator="NTRS 20100027318 text p.2", reason=f"{_MSFC}; text p.2 'used the opening at the 2:1 split to dump the hot gas into the nozzle'"),
             "N-LOX-TANK-PRESS": dict(text_basis=("AS-DB05-US-J-2-031",), locator=_C2, reason="text basis restated: Coffman text p.2 'heat up oxygen for tank pressurization'"),
             "N-LH2-TANK-PRESS": dict(evidence="SHOWN_IN_SCHEMATIC", locator="NTRS 20100027318 slide J2-4",
                                      reason="no Coffman text describes it; the text basis was MSFC-MAN-503 (withheld)"),
             "N-ASI": dict(text_basis=("AS-DB05-US-J-2-032",), locator="NTRS 20100027318 text p.4", reason=f"{_MSFC}; text p.4 'ignited by an augmented spark igniter'"),
         },
         restate_edges={
             7: dict(locator=_C2, text_basis=("AS-DB05-US-J-2-031",), reason=f"{_MSFC}; text p.2 'a heat exchanger to heat up oxygen for tank pressurization'"),
             8: dict(locator=_C2, text_basis=("AS-DB05-US-J-2-031",), reason=f"{_MSFC}; text p.2 'a heat exchanger to heat up oxygen for tank pressurization'"),
             13: dict(evidence="SHOWN_IN_SCHEMATIC", locator="NTRS 20100027318 slide J2-4",
                      role="tap", removes=(" from thrust chamber fuel manifold",),
                      reason=f"{_MSFC}; the 'thrust chamber fuel manifold' wording was MSFC's"),
             15: dict(locator=_C2, text_basis=("AS-DB05-US-J-2-030",), role="spin start through series turbine drive",
                      removes=(" (via STDV)",),
                      reason=f"{_MSFC} (the STDV is named there); text p.2 'this start tank that would discharge cold hydrogen through the two turbines'"),
             18: dict(locator=_C2, text_basis=("AS-DB05-US-J-2-011",), reason=f"{_MSFC}; text p.2 'with a bypass for calibration'"),
             19: dict(locator=_C2, text_basis=("AS-DB05-US-J-2-011",), reason=f"{_MSFC}; text p.2 gives the hot-gas path through the heat exchanger before the dump"),
         },
         extra_omissions=(),
         notes="Rests on Rocketdyne's viewgraph and Coffman's text only. MSFC-MAN-503, which DB-0.5 also "
               "used, is withheld for rights, so the elements that rested on it alone are left out and "
               "listed as omissions. The schematic slide states no rating; it belongs to the same viewgraph "
               "set as the 230,000 lb table, and Coffman's narrative speaks of the J-2 in general."),
    dict(engine="ENG-US-RL10A-3-3A", topology_id="TOPO-RL10A-3-3A", scope=("CONFIGURATION", _RL),
         label="RL10A-3-3A engine system (CR-195478 Figure 1)",
         schematic_ids=("SCH-DB05-RL10A33A-CR195478-F1",), text_source_ids=("SRC-NTRS-19950022693",),
         withhold_nodes={},
         withhold_edges={18: "igniter to thrust chamber (drawn): DB-1 has no edge kind for ignition "
                             "energy, and it is not forced into a fluid-flow edge"},
         restate_nodes={}, restate_edges={}, extra_omissions=(),
         notes="Full expander: all turbine and bypass hydrogen goes to the injector; only the cooldown "
               "valves vent overboard (start and shutdown)."),
    dict(engine="ENG-US-AJ10-137", topology_id="TOPO-SPS-BLOCK-I", scope=("PROPULSION_UNIT", "UNIT-SPS-BLOCK-I"),
         label="Apollo SPS Block I: service-module pressurization and feed with the engine assembly",
         schematic_ids=("SCH-DB05-SPS-TND7375-F2",), text_source_ids=("SRC-NASA-TND7375",),
         withhold_nodes={}, withhold_edges={},
         restate_nodes={**{n: dict(text_basis=_SPS_BASIS[n], locator="TN D-7375 p.5 'Block I Configuration - Engine assembly' (PDF p.9)",
                                   reason="page range narrowed to the Block I engine-assembly paragraph, which "
                                          "names the ablative-cooled thrust chamber, radiation-cooled nozzle, "
                                          "bolt-on aluminum injector and bipropellant valve")
                           for n in ("N-BIPROP", "N-INJ", "N-TC", "N-NOZ", "N-AMB")},
                        "N-HE-TANK": dict(label="Helium tanks",
                                          reason="the 4400 psia in the DB-0.5 label is the value of AS-DB05-US-AJ10-137-011, "
                                                 "withheld by the UNRESOLVED regulator conflict")},
         restate_edges={
             8: dict(carrier="fuel", reason="TN D-7375 does not name the fuel; 'A-50' came from the Aerojet "
                                            "chapter, which states no configuration"),
             11: dict(carrier="fuel", reason="TN D-7375 does not name the fuel; 'A-50' came from the Aerojet "
                                             "chapter, which states no configuration"),
             12: dict(text_basis=(_S + "08",), carrier="N2O4 + fuel", locator="TN D-7375 p.5 'Block I Configuration - Engine assembly' (PDF p.9)",
                      reason="TN D-7375 does not name the fuel; page range narrowed"),
             13: dict(text_basis=(_S + "07",), locator="TN D-7375 p.5 'Block I Configuration - Engine assembly' (PDF p.9)", reason="page range narrowed"),
             14: dict(text_basis=(_S + "05",), locator="TN D-7375 p.5 'Block I Configuration - Engine assembly' (PDF p.9)", reason="page range narrowed"),
             15: dict(text_basis=(_S + "05",), locator="TN D-7375 p.5 'Block I Configuration - Engine assembly' (PDF p.9)", reason="page range narrowed"),
         },
         extra_omissions=(),
         notes="Feed and pressurization belong to the service module (vehicle); the engine owns the "
               "bipropellant valve, injector, chamber and nozzle. Pressure-fed, no turbomachinery. The "
               "oxidizer is N2O4 (TN D-7375 p.13); the fuel is not named in TN D-7375."),
)
