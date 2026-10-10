"""DB-2B Wave 1 promotion manifest: six historical targets, decided entry by entry.

Read with ``db2a_manifest.py``: the promotion script merges the two into one
production corpus and applies the same gates to both. Nothing here is promoted by
a rule. Every DB-0.5 assertion of the six targets is either promoted below with
its subject, field, value, kind, operating point and conditions, or listed in
``NOT_PROMOTED`` with a disposition from ``DISPOSITIONS`` and a reason.

Targets: J-2S; F-1; H-1 188K (Saturn I SA-10); LM descent engine (final
design); Space Shuttle OMS engine; RS-25 / SSME (original-throat 1986 baseline,
Block II as of 2003, SLS-adapted). Block IIA ships no configuration: every
Block IIA statement DB-0.5 holds comes from a document stamped BOEING
PROPRIETARY.

Owner decisions of 2026-10-09, recorded after the wave was built, are in
``OWNER_DECISIONS`` (two F-1 conflicts) and ``OWNER_REVIEWS`` (rights readings,
DB-2A manifest metadata), written out as text. The DB-0.5 conflicts themselves
are unchanged.
"""

from __future__ import annotations

from db2a_manifest import P

#: The engines this wave accounts for, assertion by assertion.
SEED_ENGINES = ("ENG-US-J-2S", "ENG-US-F-1", "ENG-US-H-1-188K", "ENG-US-LMDE", "ENG-US-AJ10-190",
                "ENG-US-SSME-BLOCK-I", "ENG-US-SSME-BLOCK-IIA", "ENG-US-SSME-BLOCK-II")
ACCOUNTED_ENGINES = SEED_ENGINES

#: Why a DB-0.5 assertion of a Wave-1 target is not shipped.
DISPOSITIONS = ("WITHHELD_CONFLICT", "WITHHELD_RIGHTS", "WRONG_CONFIGURATION", "WRONG_OPERATING_POINT",
                "SOURCE_SCOPE_TOO_BROAD", "SOURCE_NOT_OPENED", "MISSING_REQUIRED_SEMANTICS", "DUPLICATE",
                "NOT_NEEDED", "OWNER_DECISION_REQUIRED")

SEED_SUBJECTS = {
    "ENG-US-J-2S": ("VAR-J2S", "CFG-J2S"),
    "ENG-US-F-1": ("FAM-F1", "VAR-F1", "CFG-F1"),
    "ENG-US-H-1-188K": ("FAM-H1", "VAR-H1", "CFG-H1-188K-SA10"),
    "ENG-US-LMDE": ("FAM-LMDE", "VAR-LMDE", "CFG-LMDE-FINAL", "UNIT-LM-DPS-FINAL"),
    "ENG-US-AJ10-190": ("FAM-OMS", "VAR-OMS", "CFG-OMS"),
    "ENG-US-SSME-BLOCK-I": ("FAM-RS25", "VAR-RS25", "CFG-RS25-SMALL-THROAT"),
    "ENG-US-SSME-BLOCK-IIA": ("FAM-RS25", "VAR-RS25"),
    "ENG-US-SSME-BLOCK-II": ("FAM-RS25", "VAR-RS25", "CFG-RS25-BLOCK-II", "CFG-RS25-SLS"),
}

#: Which sources may speak for which configuration. A configuration listed here
#: takes values from these sources only, so a statement about one RS-25 build
#: cannot be filed under another.
CONFIGURATION_SOURCES = {
    "CFG-RS25-SMALL-THROAT": ("SRC-NTRS-19860012108",),
    "CFG-RS25-BLOCK-II": ("SRC-IBIBLIO-SSMEOVERVIEW",),
    "CFG-RS25-SLS": ("SRC-NASA-RS25-FS2025", "SRC-NASA-RS25-FS2015"),
    "CFG-LMDE-FINAL": ("SRC-NASA-TND7143",),
}

# ------------------------------------------------------------------ sources

_NO_NOTICE = ("no copyright, proprietary or reproduction notice in the extracted text of any page "
              "(checked 2026-10-09)")


def _src(organization, authors, title, year, identifiers, source_type, host, figures, review_note,
         printed=_NO_NOTICE):
    return dict(organization=organization, authors=authors, title=title, year=year, identifiers=identifiers,
                source_type=source_type, authority="A", primacy="PRIMARY", host=host, printed=printed,
                review="CONSISTENT", figures=figures, review_note=review_note + _OWNER_REVIEWED)


#: Appended to every Wave-1 rights reading under the owner's review (OWNER_REVIEWS["WAVE1-RIGHTS"]).
_OWNER_REVIEWED = " Owner-reviewed 2026-10-09 (a RocketForge shipping-policy review, not a legal determination)."


SOURCES = {
    "SRC-DB05-NTRS-19940016798": _src(
        "Rockwell International, Rocketdyne Division (NASA contract NAS8-39210)", ("John Vilja", "Daniel Levack"),
        "Advanced Transportation System Studies, Technical Area 3, Alternate Propulsion Subsystem Concepts: "
        "J-2S Restart Study Task Final Report", 1993,
        {"NTRS": "19940016798", "NASA": "CR-193874", "DCN": "1-1-PP-02147"}, "NASA contractor report",
        "GOV_PUBLIC_USE_PERMITTED", "VALUES_WITH_ATTRIBUTION",
        "NTRS government public use; no notice in the text, nor on pages 1-16 viewed (the scan is rotated).",
        printed="no rights notice in the extracted text, nor on pages 1-16 viewed (checked 2026-10-09)"),
    "SRC-DB05-NTRS-20100027316": _src(
        "NASA (Remembering the Giants: Apollo Rocket Propulsion Development)", ("Robert Biggs",),
        "Rocketdyne - F-1 Saturn V First Stage Engine", 2009, {"NTRS": "20100027316"},
        "Rocketdyne engineer's programme history with Rocketdyne viewgraphs, printed by NASA",
        "PUBLIC_USE_PERMITTED", "RIGHTS_REVIEW_REQUIRED",
        "NTRS permits public use; no notice on the pages. The viewgraphs are Rocketdyne's, so figures are not "
        "shipped; values and graph structure are, with attribution, as for the DB-2A J-2 record."),
    "SRC-NTRS-19650013470": _src(
        "Chrysler Corporation Space Division (NASA contract NAS 8-4016)", (),
        "Saturn I Launch Vehicle SA-10 and Launch Complex 37B Functional Systems Description, Volume VIII: "
        "H-1 Engine and Hydraulic System", 1964,
        {"NTRS": "19650013470", "SDES": "64-415 Vol. VIII", "NASA": "CR-62503"}, "NASA contractor technical manual",
        "GOV_PUBLIC_USE_PERMITTED", "VALUES_WITH_ATTRIBUTION",
        "NTRS government public use; no notice in the text of any page."),
    "SRC-NASA-TND7143": _src(
        "NASA Manned Spacecraft Center", ("W. R. Hammock, Jr.", "E. C. Currie", "A. E. Fisher"),
        "Apollo Experience Report - Descent Propulsion System", 1973,
        {"NTRS": "19730011150", "NASA": "TN D-7143", "MSC": "S-349"}, "NASA technical note",
        "GOV_PUBLIC_USE_PERMITTED", "VALUES_WITH_ATTRIBUTION",
        "NTRS government public use; a NASA technical note with no notice on the pages."),
    "SRC-JSC-19950": _src(
        "NASA Lyndon B. Johnson Space Center", (), "Orbital Maneuvering System Orbiter Systems Training Manual",
        1995, {"JSC": "19950", "OMS": "2102"}, "NASA training manual", "NONE", "VALUES_WITH_ATTRIBUTION",
        "No repository statement: the copy read is an ibiblio.org mirror, not a NASA host. A NASA JSC "
        "training manual; DB-0.5 found no copyright notice on the cover, and no notice was found in the "
        "extracted text of its 62 pages (re-checked 2026-10-09); government work."),
    "SRC-DB05-NTRS-19850008634": _src(
        "NASA Lyndon B. Johnson Space Center", ("C. Gibson", "C. Humphries"),
        "Orbital Maneuvering System Design Evolution", 1985, {"NTRS": "19850008634"}, "NASA conference paper",
        "GOV_PUBLIC_USE_PERMITTED", "VALUES_WITH_ATTRIBUTION",
        "NTRS government public use; no notice on the pages."),
    "SRC-NTRS-19860012108": _src(
        "NASA Marshall Space Flight Center (Software and Engineering Associates, contractor)",
        ("G. R. Nickerson", "L. D. Dang"), "Performance Predictions for an SSME Configuration with an Enlarged Throat",
        1985, {"NTRS": "19860012108", "NASA": "CR-178740"}, "NASA contractor report",
        "GOV_PUBLIC_USE_PERMITTED", "VALUES_WITH_ATTRIBUTION",
        "NTRS government public use; no notice on the pages."),
    "SRC-IBIBLIO-SSMEOVERVIEW": _src(
        "NASA Lyndon B. Johnson Space Center", (), "Shuttle Booster Systems Brief: SSME Overview", 2003,
        {"JSC": "19041", "brief": "SB1.1, Basic Rev F, 07/07/03"}, "NASA training document", "NONE",
        "VALUES_WITH_ATTRIBUTION",
        "No repository statement: the copy read is an ibiblio.org mirror, not a NASA host. A NASA JSC "
        "systems brief; DB-0.5 found no copyright notice on the pages read, and no notice was found in the "
        "extracted text of its 284 pages (re-checked 2026-10-09); government work."),
    "SRC-NASA-RS25-FS2025": _src(
        "NASA Marshall Space Flight Center", (), "NASAfacts: SLS (Space Launch System) RS-25 Core Stage Engine",
        2025, {"NASA": "MSFC-03-2025-SLS-4963"}, "NASA fact sheet", "NONE", "VALUES_WITH_ATTRIBUTION",
        "No repository rights statement (a nasa.gov page download, not an NTRS record); a NASA publication "
        "with no notice; government work."),
}

#: Sources whose content Wave 1 must not carry. Each prints a notice that reserves
#: rights or forbids reuse; the promotion also refuses them on that notice.
WITHHELD_SOURCES = {
    "SRC-USA-OMS21002": dict(
        reason="OMS Workbook OMS 21002 p.1 prints 'Copyright (c) 2004 by United Space Alliance ... All other "
               "rights are reserved by the copyright owner.'",
        locator_tokens=("USA006500", "OMS 21002")),
    "SRC-ENGINEHISTORY-SSMEORIENT-1998": dict(
        reason="BC98-04 SSME Orientation: every page stamped 'BOEING PROPRIETARY'; 'Use this data for "
               "training purposes only'",
        locator_tokens=("BC98-04", "BOEING", "slide 19")),
    "SRC-L3HARRIS-RS25-SPEC": dict(
        reason="RS-25 spec sheet: '(c) 2024 L3Harris Technologies', no reuse licence stated",
        locator_tokens=("L3Harris", "SPECIFICATIONS")),
    "SRC-AIAA-97-2687": dict(
        reason="AIAA 97-2687 p.1 prints 'Copyright 1997 by the AIAA, Inc. All rights reserved.'",
        locator_tokens=("AIAA 97-2687", "97PD-038")),
    "SRC-NTRS-20030005845": dict(
        reason="AIAA 2002-3581 p.2 prints '(c) 2002 AIAA' against an NTRS public-use flag: the two statements "
               "disagree and no review has settled it",
        locator_tokens=("20030005845",)),
}

#: Wording that would carry withheld content into a shipped record.
WITHHELD_CONTENT_TERMS = {
    # MSFC-MAN-503 alone gives these F-1 facts
    "CFG-F1": ("checkout", "helium", "exhaust igniter", "IFV", "375 psi", "dual ball valve", "on turbine exhaust",
               "heated by", "0.42"),
    # SA-10 schematic pressure callouts are withheld (operating point not stated)
    "CFG-H1-188K-SA10": ("callout",),
    # the development (fixed-area, helium-injection) engine is not the final design
    "CFG-LMDE-FINAL": ("helium injection", "helium-injection", "fixed-area", "fixed area", "Fig. 6", "Figure 6"),
    # BC98-04 (Block IIA, Boeing proprietary) and L3Harris values must not reach any RS-25 build
    **{cfg: ("Boeing", "BC98-04", "L3Harris", "34,311", "34311", "15,519", "22,250", "6.032", "2,994", "71,140",
             "23,260", "452.3", "6,276", "7,268", "7,774")
       for cfg in ("CFG-RS25-SMALL-THROAT", "CFG-RS25-BLOCK-II", "CFG-RS25-SLS")},
}

# ------------------------------------------------------------------ identity

FAMILIES = (
    ("FAM-F1", "F-1", ""),
    ("FAM-H1", "H-1", ""),
    ("FAM-LMDE", "LM descent engine", "The lunar module descent propulsion system engine."),
    ("FAM-OMS", "Space Shuttle OMS engine", "The Orbital Maneuvering System engine of the Space Shuttle orbiter."),
    ("FAM-RS25", "RS-25", ""),
)

VARIANTS = (
    ("VAR-J2S", "FAM-J2", "J-2S", "The J-2 Simplified (NTRS 19940016798 PDF p.8)."),
    ("VAR-F1", "FAM-F1", "F-1", ""),
    ("VAR-H1", "FAM-H1", "H-1", ""),
    ("VAR-LMDE", "FAM-LMDE", "LM descent engine", ""),
    ("VAR-OMS", "FAM-OMS", "OMS engine",
     "The opened sources name it 'OMS engine'; the AJ10-190 designation is not printed in them."),
    ("VAR-RS25", "FAM-RS25", "RS-25", "The Space Shuttle Main Engine (SSME)."),
)

CONFIGURATIONS = (
    ("CFG-J2S", "VAR-J2S", "J-2S, as described by Rocketdyne's 'J-2S Basic Engine Features' viewgraph",
     ("MISSING", "NOT_AUDITED", "the viewgraph names a production configuration but no effectivity"),
     "NTRS 19940016798 PDF p.9 (the 1993 restart study's baseline)."),
    ("CFG-F1", "VAR-F1", "F-1, as described by Rocketdyne's 'F-1 Engine Characteristics' and 'Basic Features' viewgraphs",
     ("MISSING", "UNKNOWN", "the viewgraphs print no rating epoch; research conflict CF-DB05-F1-RATING is UNRESOLVED"),
     "NTRS 20100027316 PDF p.16. By owner decision (2026-10-09) the 'F-1 Engine Characteristics' viewgraph "
     "defines this source-scoped configuration: its vacuum thrust, Isp and chamber pressure ship for it "
     "alone. This is not a canonical flight-rating epoch: the sea-level thrust rating stays withheld "
     "(CF-DB05-F1-RATING, UNRESOLVED), and so does every other value of that table the owner did not admit."),
    ("CFG-H1-188K-SA10", "VAR-H1", "H-1, 188,000 lb nominal sea-level rating, Saturn I SA-10",
     "Saturn I SA-10 S-I stage (SDES-64-415 Vol. VIII)",
     "Not the H-1 family in general: the SA-10 volume's 188,000 lb engine. The graph is the inboard engine; "
     "outboard engines add a hydraulic system and an aspirator."),
    ("CFG-LMDE-FINAL", "VAR-LMDE", "LM descent engine, final design (variable-area injector)",
     ("MISSING", "NOT_AUDITED", "TN D-7143 dates the selection (January 1965), not flight effectivity"),
     "The variable-area-injector design TN D-7143 describes as selected (January 1965); the other "
     "development throttling concept is not part of this record."),
    ("CFG-OMS", "VAR-OMS", "Space Shuttle OMS engine, flight configuration",
     ("MISSING", "NOT_AUDITED", "no effectivity is transcribed"),
     "The engine of the current OMS (NTRS 19850008634, 1985) and of the 1995 training manual JSC-19950."),
    ("CFG-RS25-SMALL-THROAT", "VAR-RS25", "RS-25 (SSME) with the original-throat main combustion chamber",
     "the 'current design' of NTRS 19860012108 (1985-86), before the large-throat MCC",
     "The baseline the 1986 enlarged-throat study starts from. Not Block IIA or Block II."),
    ("CFG-RS25-BLOCK-II", "VAR-RS25", "RS-25 (SSME) Block II, the Shuttle fleet engine of 2003",
     "2003 (JSC-19041: 'Currently (2003) there is one type of SSME in the fleet; Block II')",
     "As JSC-19041 describes it. Its Block IIA predecessor ships no configuration (rights)."),
    ("CFG-RS25-SLS", "VAR-RS25", "RS-25 SLS core-stage engine (shuttle-era flight engine adapted for SLS)",
     ("MISSING", "NOT_AUDITED", "first SLS flight Artemis I, November 2022, per FS-2025; not transcribed"),
     "Shuttle-program flight engines adapted with new controllers and insulation (NASA facts FS-2025). The "
     "fact sheets do not name the block."),
)

OPERATING_POINTS = (
    ("OP-J2S-MR55", "CFG-J2S", "engine mixture ratio calibration 5.5:1 (O/F)",
     "The one point of the viewgraph's 'Performance & Weight' table."),
    ("OP-RS25-SMALL-THROAT-109", "CFG-RS25-SMALL-THROAT", "109% power level", ""),
    ("OP-RS25-BII-RPL", "CFG-RS25-BLOCK-II", "rated power level (100%)", ""),
    ("OP-RS25-BII-104", "CFG-RS25-BLOCK-II", "104.5% of rated power level", ""),
    ("OP-RS25-SLS-109", "CFG-RS25-SLS", "109% (SLS operational thrust)", ""),
)

UNITS = (
    ("UNIT-LM-DPS-FINAL", "STAGE_PROPULSION", "LM descent propulsion system, final design",
     (("CFG-LMDE-FINAL", 1, "descent engine"),),
     "TN D-7143 Figure 3 'The final DPS design': the descent stage's supercritical-helium pressurization, "
     "tanks and feed, with the descent engine."),
)

ALIASES = (
    ("ALIAS-RS25-SSME", "SSME", "INFORMAL", "VAR-RS25", ("SRC-IBIBLIO-SSMEOVERVIEW",)),
)

# ------------------------------------------------------------------ assertions

_J2S, _J2SOP = "CFG-J2S", "OP-J2S-MR55"
_F1 = "CFG-F1"
_F1_TABLE = ("From the 'F-1 Engine Characteristics' viewgraph, which by owner decision (2026-10-09) defines this "
             "source-scoped configuration; not a canonical flight-rating epoch. The same table's sea-level thrust "
             "is withheld (CF-DB05-F1-RATING, UNRESOLVED).")
_H1 = "CFG-H1-188K-SA10"
_LM = "CFG-LMDE-FINAL"
_OMS = "CFG-OMS"
_ST, _STOP = "CFG-RS25-SMALL-THROAT", "OP-RS25-SMALL-THROAT-109"
_BII = "CFG-RS25-BLOCK-II"
_SLS = "CFG-RS25-SLS"


_REQ = ("listed under 'The basic design requirements for the descent engine' (TN D-7143 p.8): a programme "
        "requirement, filed on the variant")


def _j2s_basis(other):
    return f"AS-DB05-US-J-2S-{other}, printed in the same one-point 'Performance & Weight' table"


ASSERTIONS = (
    # J-2S: 'J-2S Basic Engine Features' (NTRS 19940016798 PDF p.9)
    P("AS-DB05-US-J-2S-001", _J2S, "performance.thrust_vac", ("number", 265000), "NOMINAL", op=_J2SOP,
      op_basis=_j2s_basis("004"), cond=dict(environment="VACUUM"), note="Printed as 'Nominal vacuum thrust (lb)'."),
    P("AS-DB05-US-J-2S-002", _J2S, "performance.specific_impulse_vac", ("number", 436), "NOMINAL", op=_J2SOP,
      op_basis=_j2s_basis("004"), cond=dict(environment="VACUUM", isp_basis="UNKNOWN"),
      note="Printed as 'Nominal vacuum specific impulse (sec)'; engine or thrust-chamber basis not stated."),
    P("AS-DB05-US-J-2S-003", _J2S, "performance.chamber_pressure", ("number", 1200), "NOMINAL", op=_J2SOP,
      op_basis=_j2s_basis("004"), cond=dict(pressure_basis="ABSOLUTE", pressure_station="NOZZLE_STAGNATION"),
      note="Printed as 'Chamber pressure (psia) (nozzle stagnation)'."),
    P("AS-DB05-US-J-2S-004", _J2S, "propellants.mixture_ratio", ("number", 5.5), "NOMINAL", op=_J2SOP,
      op_basis=_j2s_basis("003"), cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="ENGINE"),
      note="Printed as 'Engine mixture ratio calibration O/F'."),
    P("AS-DB05-US-J-2S-005", _J2S, "mechanical.mass_dry_basic", ("number", 3235), "NOMINAL"),
    P("AS-DB05-US-J-2S-006", _J2S, "mechanical.mass_dry_with_accessories", ("number", 3800), "NOMINAL"),
    P("AS-DB05-US-J-2S-007", _J2S, "architecture.cycle", ("enum", "TAP_OFF"), "NOMINAL",
      note="Printed as 'Tap-off turbine drive cycle'."),
    P("AS-DB05-US-J-2S-008", _J2S, "nozzle.area_ratio", ("number", 40), "NOMINAL"),
    P("AS-DB05-US-J-2S-010", _J2S, "operating_modes.idle", ("text",), "OTHER"),
    P("AS-DB05-US-J-2S-021", _J2S, "architecture.feed", ("enum", "PUMP_FED"), "NOMINAL"),
    P("AS-DB05-US-J-2S-022", _J2S, "propellants.oxidizer", ("enum", "LIQUID_OXYGEN"), "NOMINAL"),
    P("AS-DB05-US-J-2S-023", _J2S, "propellants.fuel", ("enum", "LIQUID_HYDROGEN"), "NOMINAL"),
    P("AS-DB05-US-J-2S-024", _J2S, "cooling.thrust_chamber", ("enum", "REGENERATIVE"), "NOMINAL"),

    # F-1: 'F-1 Engine Characteristics' (F1-6) and 'F-1 Engine Basic Features' (F1-7)
    P("AS-DB05-US-F-1-011", _F1, "nozzle.area_ratio", ("number", 16), "NOMINAL"),
    # F-1 'Engine Characteristics' table: owner decisions of 2026-10-09 (CF-DB05-F1-RATING, CF-DB05-F1-PC)
    P("AS-DB05-US-F-1-002", _F1, "performance.thrust_vac", ("number", 1748200), "NOMINAL",
      cond=dict(environment="VACUUM"), note=_F1_TABLE),
    P("AS-DB05-US-F-1-003", _F1, "performance.specific_impulse_sl", ("number", 265.4), "NOMINAL",
      cond=dict(environment="SEA_LEVEL", isp_basis="UNKNOWN"), note=_F1_TABLE),
    P("AS-DB05-US-F-1-004", _F1, "performance.specific_impulse_vac", ("number", 304.1), "NOMINAL",
      cond=dict(environment="VACUUM", isp_basis="UNKNOWN"), note=_F1_TABLE),
    P("AS-DB05-US-F-1-005", _F1, "performance.chamber_pressure", ("number", 1125), "NOMINAL",
      cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN"),
      note="Printed as 'Chamber pressure (psia)'; the station is not printed. In research conflict CF-DB05-F1-PC "
           "(PARTIALLY_RESOLVED); shipped for this configuration only, by owner decision, and not for the F-1 "
           "variant or family."),
    P("AS-DB05-US-F-1-008", _F1, "mechanical.dimensions", ("text",), "OTHER"),
    P("AS-DB05-US-F-1-012", _F1, "pumps.configuration", ("text",), "OTHER"),
    P("AS-DB05-US-F-1-015", _F1, "ignition_start.method", ("text",), "OTHER"),
    P("AS-DB05-US-F-1-016", _F1, "fluids.rp1_multipurpose", ("text",), "OTHER"),
    P("AS-DB05-US-F-1-025", _F1, "architecture.feed", ("enum", "PUMP_FED"), "NOMINAL"),
    P("AS-DB05-US-F-1-026", _F1, "propellants.oxidizer", ("enum", "LIQUID_OXYGEN"), "NOMINAL"),
    P("AS-DB05-US-F-1-027", _F1, "propellants.fuel", ("enum", "RP_1"), "NOMINAL"),
    P("AS-DB05-US-F-1-028", _F1, "architecture.cycle", ("enum", "GAS_GENERATOR"), "NOMINAL",
      note="Printed as 'Turbine drive power from gas generator Burning main propellants'."),
    # F-1 variant: Biggs's narrative speaks of the F-1, not of a rating
    P("AS-DB05-US-F-1-013", "VAR-F1", "pumps.shaft_order", ("text",), "OTHER"),
    P("AS-DB05-US-F-1-014", "VAR-F1", "cooling.zones", ("text",), "OTHER"),

    # H-1 188K, Saturn I SA-10: SDES-64-415 Vol. VIII
    P("AS-DB05-US-H-1-188K-001", _H1, "performance.thrust_sl", ("number", 188000), "NOMINAL",
      cond=dict(environment="SEA_LEVEL"), note="Printed as the 'nominal rating' at sea level."),
    P("AS-DB05-US-H-1-188K-002", _H1, "identity.start_mode", ("text",), "OTHER"),
    P("AS-DB05-US-H-1-188K-003", _H1, "thrust_chamber.tube_count", ("number", 292), "NOMINAL"),
    P("AS-DB05-US-H-1-188K-004", _H1, "cooling.path", ("text",), "OTHER"),
    P("AS-DB05-US-H-1-188K-005", _H1, "injector.baffles", ("text",), "OTHER"),
    P("AS-DB05-US-H-1-188K-006", _H1, "turbines.power_speed", ("text",), "OTHER"),
    P("AS-DB05-US-H-1-188K-007", _H1, "pumps.gearbox", ("number", 6537), "APPROXIMATE"),
    P("AS-DB05-US-H-1-188K-008", _H1, "pumps.type", ("text",), "OTHER"),
    P("AS-DB05-US-H-1-188K-010", _H1, "ignition_start.spgg", ("text",), "OTHER"),
    P("AS-DB05-US-H-1-188K-011", _H1, "gg.mixture_ratio", ("number", 2.924), "APPROXIMATE",
      cond=dict(mixture_ratio_form="FUEL_TO_OXIDIZER", mixture_ratio_basis="GAS_GENERATOR"),
      note="Printed fuel-to-LOX; the liquid propellant gas generator's ratio, not the engine's."),
    P("AS-DB05-US-H-1-188K-012", _H1, "lubrication.fabu", ("number", 2.75), "APPROXIMATE"),
    P("AS-DB05-US-H-1-188K-026", _H1, "propellants.oxidizer", ("enum", "LIQUID_OXYGEN"), "NOMINAL",
      note="Printed as 'LOX'."),
    P("AS-DB05-US-H-1-188K-027", _H1, "propellants.fuel", ("enum", "RP_1"), "NOMINAL"),
    P("AS-DB05-US-H-1-188K-028", _H1, "architecture.cycle", ("enum", "GAS_GENERATOR"), "NOMINAL",
      note="The liquid propellant gas generator drives the turbine (section 1.2.1.4)."),

    # LM descent engine: TN D-7143 'basic design requirements' (the programme) ...
    P("AS-DB05-US-LMDE-001", "VAR-LMDE", "performance.throttle_ratio", ("number", 10), "DESIGN_VALUE",
      reading=_REQ,
      note="A design requirement for the descent engine, not a measured value."),
    P("AS-DB05-US-LMDE-002", "VAR-LMDE", "performance.thrust_max", ("number", 10500), "DESIGN_VALUE",
      reading=_REQ,
      cond=dict(environment="UNKNOWN"), note="A design requirement ('Maximum-rated thrust')."),
    P("AS-DB05-US-LMDE-003", "VAR-LMDE", "mechanical.gimbal", ("number", 6), "DESIGN_VALUE"),
    P("AS-DB05-US-LMDE-004", "VAR-LMDE", "life.duty_cycle", ("number", 1000), "DESIGN_VALUE"),
    P("AS-DB05-US-LMDE-006", "VAR-LMDE", "propellants.combination", ("text",), "OTHER",
      note="From the descent engine's design requirements; stated for the programme, not a build."),
    P("AS-DB05-US-LMDE-007", "VAR-LMDE", "performance.specific_impulse", ("number", 305), "DESIGN_VALUE",
      reading=_REQ,
      cond=dict(environment="UNKNOWN", isp_basis="UNKNOWN"),
      note="A design requirement, 'end of duty cycle'; vacuum or sea level is not printed."),
    # ... and the final design
    P("AS-DB05-US-LMDE-008", _LM, "performance.fixed_throttle_point", ("number", 92.5), "NOMINAL",
      note="Printed as 'FTP was optimized at 92.5 percent of maximum-rated thrust (10 500 lb)', in the text "
           "that follows the selection of the variable-area injector."),
    P("AS-DB05-US-LMDE-009", _LM, "performance.min_throttle", ("number", 10), "MINIMUM",
      reading="printed as 'The minimum-throttle point was 10 percent of the rated thrust': the bottom of the "
              "throttle range"),
    P("AS-DB05-US-LMDE-010", _LM, "cooling.zones", ("text",), "OTHER"),
    P("AS-DB05-US-LMDE-011", _LM, "control.shutoff_valves", ("text",), "OTHER"),
    P("AS-DB05-US-LMDE-012", _LM, "control.throttle_actuator", ("text",), "OTHER"),
    P("AS-DB05-US-LMDE-013", "UNIT-LM-DPS-FINAL", "pressurization.she", ("text",), "OTHER"),
    P("AS-DB05-US-LMDE-014", "UNIT-LM-DPS-FINAL", "pressurization.regulation", ("text",), "OTHER"),

    # Space Shuttle OMS engine: JSC-19950 and NTRS 19850008634
    P("AS-DB05-US-AJ10-190-003", _OMS, "performance.thrust", ("number", 6000), "NOMINAL",
      cond=dict(environment="UNKNOWN"), note="Vacuum or sea level is not printed."),
    P("AS-DB05-US-AJ10-190-004", _OMS, "performance.specific_impulse", ("number", 313), "NOMINAL",
      cond=dict(environment="UNKNOWN", isp_basis="UNKNOWN"), note="Vacuum or sea level is not printed."),
    P("AS-DB05-US-AJ10-190-008", _OMS, "cooling.channels", ("number", 120), "NOMINAL"),
    P("AS-DB05-US-AJ10-190-009", _OMS, "nozzle.area_ratio", ("number", 55), "NOMINAL",
      reading="the nozzle 'extended from the regeneratively cooled interface to an area ratio of 55:1'; 6:1 "
              "is the end of the regeneratively cooled chamber"),
    P("AS-DB05-US-AJ10-190-010", _OMS, "nozzle.extension", ("text",), "OTHER"),
    P("AS-DB05-US-AJ10-190-011", _OMS, "injector.type", ("text",), "OTHER"),
    P("AS-DB05-US-AJ10-190-012", _OMS, "thrust_chamber.geometry", ("number", 15.9), "NOMINAL"),
    P("AS-DB05-US-AJ10-190-013", _OMS, "propellants.oxidizer", ("enum", "NITROGEN_TETROXIDE"), "NOMINAL",
      note="Printed for the pods of the current OMS, whose engine this record is."),
    P("AS-DB05-US-AJ10-190-014", _OMS, "propellants.fuel", ("enum", "MONOMETHYLHYDRAZINE"), "NOMINAL",
      note="Printed for the pods of the current OMS, whose engine this record is."),

    # RS-25 original-throat baseline: NTRS 19860012108 p.8
    P("AS-DB05-US-SSME-BLOCK-I-001", _ST, "nozzle.area_ratio", ("number", 77.5), "NOMINAL"),
    P("AS-DB05-US-SSME-BLOCK-I-002", _ST, "performance.chamber_pressure", ("number", 3285), "NOMINAL", op=_STOP,
      cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN")),
    # RS-25 Block II (2003): JSC-19041
    P("AS-DB05-US-SSME-BLOCK-II-025", _BII, "identity.block_definition", ("text",), "OTHER"),
    P("AS-DB05-US-SSME-BLOCK-II-027", _BII, "performance.chamber_pressure", ("number", 2870), "APPROXIMATE",
      op="OP-RS25-BII-104", cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN")),
    P("AS-DB05-US-SSME-BLOCK-II-028", _BII, "performance.chamber_pressure", ("number", 2747), "APPROXIMATE",
      op="OP-RS25-BII-RPL", cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN")),
    P("AS-DB05-US-SSME-BLOCK-II-030", _BII, "cooling.coolant", ("text",), "OTHER"),
    P("AS-DB05-US-SSME-BLOCK-II-031", _BII, "performance.throttle_range_shuttle", ("text",), "OTHER"),
    P("AS-DB05-US-SSME-BLOCK-II-032", _BII, "mechanical.gimbal", ("text",), "OTHER"),
    P("AS-DB05-US-SSME-BLOCK-II-034", _BII, "performance.thrust_vac", ("number", 470000), "APPROXIMATE",
      op="OP-RS25-BII-RPL", cond=dict(environment="VACUUM")),
    # RS-25 SLS-adapted: NASA facts FS-2025
    P("AS-DB05-US-SSME-BLOCK-II-016", _SLS, "performance.thrust_vac", ("number", 512300), "NOMINAL",
      op="OP-RS25-SLS-109", cond=dict(environment="VACUUM"),
      note="DB-0.5 places it at 109%, the SLS operational thrust level of the same fact sheet."),
)

FIELD_RENAMES = {
    "performance.isp_sl": ("performance.specific_impulse_sl",),
    "identity.block_IIA_change": ("identity.block_iia_change",),  # DB-1 field paths are lowercase
}

OPERATING_POINT_MAP = {
    ("ENG-US-SSME-BLOCK-I", "OP-109"): _STOP,
    ("ENG-US-SSME-BLOCK-II", "OP-RPL"): "OP-RS25-BII-RPL",
    ("ENG-US-SSME-BLOCK-II", "OP-104.5"): "OP-RS25-BII-104",
    ("ENG-US-SSME-BLOCK-II", "OP-109"): "OP-RS25-SLS-109",
}

CONFIGURATION_MAP = {
    ("ENG-US-SSME-BLOCK-I", "pre-large-throat MCC"): _ST,
    ("ENG-US-H-1-188K", "Saturn I SA-10 S-I stage"): _H1,
}

_MSFC = ("WITHHELD_RIGHTS", "MSFC-MAN-503: rights conflict unresolved, payload withheld")
_USA = ("WITHHELD_RIGHTS", "OMS Workbook OMS 21002: printed copyright, all other rights reserved")
_BOEING = ("WITHHELD_RIGHTS", "BC98-04: every page stamped BOEING PROPRIETARY")
_L3H = ("WITHHELD_RIGHTS", "L3Harris spec sheet: printed copyright, no reuse licence")
_HAER = ("SOURCE_SCOPE_TOO_BROAD", "HAER TX-116 gives fleet-history approximations with no configuration")
_CALLOUT = ("MISSING_REQUIRED_SEMANTICS", "a schematic pressure callout: operating point not stated, line "
                                          "assignment by callout position")

NOT_PROMOTED = {
    # J-2S
    "AS-DB05-US-J-2S-009": ("WRONG_OPERATING_POINT", "the 5.0 and 4.5 mixture ratios are other operating points"),
    "AS-DB05-US-J-2S-011": ("NOT_NEEDED", "test history, not an engine property"),
    "AS-DB05-US-J-2S-012": ("SOURCE_SCOPE_TOO_BROAD", "J-2X paper: its J-2S column states no configuration"),
    "AS-DB05-US-J-2S-013": ("SOURCE_SCOPE_TOO_BROAD", "J-2X paper: its J-2S column states no configuration"),
    "AS-DB05-US-J-2S-014": ("NOT_NEEDED", "the J-2X paper names the J-2S Mk. 29 turbopump as its point of departure"),
    **{f"AS-DB05-US-J-2S-0{i}": ("WITHHELD_CONFLICT", "timeline date in PARTIALLY_RESOLVED conflict CF-DB05-J2S-DATES")
       for i in range(15, 21)},
    # F-1
    "AS-DB05-US-F-1-001": ("WITHHELD_CONFLICT", "sea-level thrust in UNRESOLVED rating-epoch conflict CF-DB05-F1-RATING"),
    **{f"AS-DB05-US-F-1-0{i}": ("NOT_NEEDED", "recorded as a text basis of the F-1 graph; not shipped as a value")
       for i in (29, 30, 31, 32)},
    "AS-DB05-US-F-1-006": ("MISSING_REQUIRED_SEMANTICS",
                           "printed 'Engine mixture ratio 2.27' without a direction (O/F or F/O)"),
    "AS-DB05-US-F-1-007": ("WITHHELD_CONFLICT", "mass in UNRESOLVED conflict CF-DB05-F1-MASS"),
    "AS-DB05-US-F-1-009": ("NOT_NEEDED", "production deliveries, not an engine property"),
    "AS-DB05-US-F-1-010": ("OWNER_DECISION_REQUIRED",
                           "qualification life printed in the 'F-1 Engine Characteristics' table, whose rating epoch "
                           "is the UNRESOLVED CF-DB05-F1-RATING; the owner's decision of 2026-10-09 admits the "
                           "table's vacuum thrust and Isp, not this value"),
    "AS-DB05-US-F-1-017": ("WRONG_CONFIGURATION", "1.8 million lb is the F-1A (footnote 4: 'F-1A was rated at 1.8 "
                                                  "million pounds force')"),
    **{f"AS-DB05-US-F-1-0{i}": _MSFC for i in range(18, 25)},
    # H-1
    "AS-DB05-US-H-1-188K-009": ("NOT_NEEDED", "accessory drive of the outboard engines' hydraulic pump"),
    "AS-DB05-US-H-1-188K-013": ("NOT_NEEDED", "a start-sequence threshold"),
    "AS-DB05-US-H-1-188K-014": ("NOT_NEEDED", "a start-sequence threshold"),
    "AS-DB05-US-H-1-188K-015": ("NOT_NEEDED", "the SA-10 flight's burn time, not an engine property"),
    "AS-DB05-US-H-1-188K-016": ("NOT_NEEDED", "gimbal range of the outboard engines only"),
    **{f"AS-DB05-US-H-1-188K-0{i}": _CALLOUT for i in range(17, 26)},
    # LM descent engine
    "AS-DB05-US-LMDE-005": ("NOT_NEEDED", "a stage pressurization requirement and its later change"),
    # OMS
    "AS-DB05-US-AJ10-190-001": _USA,
    "AS-DB05-US-AJ10-190-002": _USA,
    "AS-DB05-US-AJ10-190-005": _USA,
    "AS-DB05-US-AJ10-190-006": _USA,
    "AS-DB05-US-AJ10-190-007": _USA,
    # RS-25 Block IIA: every statement is from BC98-04
    **{f"AS-DB05-US-SSME-BLOCK-IIA-0{i:02d}": _BOEING for i in range(1, 20)},
    # RS-25 Block II / SLS / fleet
    **{f"AS-DB05-US-SSME-BLOCK-II-0{i:02d}": _L3H for i in range(1, 14)},
    "AS-DB05-US-SSME-BLOCK-II-014": ("DUPLICATE", "FS-2015's rounded '512,000 pounds' of the 109% vacuum rating "
                                                  "FS-2025 prints as 512,300 lb"),
    "AS-DB05-US-SSME-BLOCK-II-015": ("WITHHELD_CONFLICT", "mass in UNRESOLVED conflict CF-DB05-RS25-MASS"),
    "AS-DB05-US-SSME-BLOCK-II-017": ("WITHHELD_CONFLICT", "sea-level thrust in UNRESOLVED conflict CF-DB05-RS25-SLTHRUST"),
    "AS-DB05-US-SSME-BLOCK-II-018": ("WITHHELD_CONFLICT", "mass in UNRESOLVED conflict CF-DB05-RS25-MASS"),
    "AS-DB05-US-SSME-BLOCK-II-019": ("SOURCE_SCOPE_TOO_BROAD", "the shuttle fleet in flight at 104.5%; no block"),
    "AS-DB05-US-SSME-BLOCK-II-020": ("SOURCE_SCOPE_TOO_BROAD", "the shuttle fleet tested up to 111%; no block"),
    "AS-DB05-US-SSME-BLOCK-II-021": ("WITHHELD_CONFLICT", "pump power in UNRESOLVED conflict CF-DB05-RS25-PUMPPOWER"),
    "AS-DB05-US-SSME-BLOCK-II-022": ("WITHHELD_CONFLICT", "pump power in UNRESOLVED conflict CF-DB05-RS25-PUMPPOWER"),
    "AS-DB05-US-SSME-BLOCK-II-023": ("WITHHELD_RIGHTS", "AIAA 2002-3581: printed copyright against NTRS public use, unresolved"),
    "AS-DB05-US-SSME-BLOCK-II-024": ("WITHHELD_RIGHTS", "AIAA 2002-3581: printed copyright against NTRS public use, unresolved"),
    "AS-DB05-US-SSME-BLOCK-II-029": ("NOT_NEEDED", "a generic round number in an overview, not a measured preburner pressure"),
    "AS-DB05-US-SSME-BLOCK-II-026": ("WRONG_CONFIGURATION", "the larger-throat MCC is the Block IIA change; Block IIA is "
                                     "withheld (Boeing proprietary), and filing it on the RS-25 variant would generalise "
                                     "a build statement printed beside the Block II definition"),
    "AS-DB05-US-SSME-BLOCK-II-033": ("WRONG_CONFIGURATION", "the pre-large-throat 77.5:1, printed stale in a Block II brief "
                                                            "(rejected in DB-0.5)"),
    "AS-DB05-US-SSME-BLOCK-II-035": ("WITHHELD_CONFLICT", "sea-level thrust in UNRESOLVED conflict CF-DB05-RS25-SLTHRUST"),
    "AS-DB05-US-SSME-BLOCK-II-036": ("WITHHELD_CONFLICT", "HPOTP speed limit in PARTIALLY_RESOLVED conflict "
                                                          "CF-DB05-RS25-HPOTPSPEED"),
    **{f"AS-DB05-US-SSME-BLOCK-II-0{i}": _HAER for i in range(37, 43)},
    "AS-DB05-US-SSME-BLOCK-II-043": ("WRONG_CONFIGURATION", "the 1986 study's enlarged-throat design, not a flown block"),
    "AS-DB05-US-SSME-BLOCK-II-044": ("WRONG_CONFIGURATION", "a predicted value for the 1986 study's enlarged-throat design"),
}

# ------------------------------------------------------------------ owner decisions (2026-10-09)
#
# Written out as text. An ``owner_accepted`` must equal its entry here; a rights
# note that says "Owner-reviewed" must belong to a source an OWNER_REVIEWS entry lists.

_F1_RATING = ("owner (Cemil Eray), 2026-10-09: accept the 'F-1 Engine Characteristics' viewgraph as defining the "
              "source-scoped CFG-F1 production configuration; admit 1,748,200 lb vacuum thrust, 265.4 s sea-level "
              "Isp and 304.1 s vacuum Isp. Not a canonical historical flight-rating epoch; the unresolved "
              "sea-level-thrust rating conflict stays withheld.")
_F1_PC = ("owner (Cemil Eray), 2026-10-09: accept F-1 chamber pressure 1,125 psia for CFG-F1 only; measurement "
          "station UNKNOWN; no family, variant or general F-1 inheritance. The research conflict stays "
          "PARTIALLY_RESOLVED as recorded in DB-0.5.")

OWNER_DECISIONS = {
    "CF-DB05-F1-RATING": _F1_RATING,
    "CF-DB05-F1-PC": _F1_PC,
}

OWNER_REVIEWS = {
    "DB2A-RIGHTS": dict(
        decision="owner (Cemil Eray), 2026-10-09: accept the five DB-2A rights readings as reviewed; no policy "
                 "upgrade (values ship with attribution, never as public domain).",
        sources=("SRC-NTRS-20100027318", "SRC-NTRS-19950022693", "SRC-NTRS-19910018888", "SRC-NASA-TND7375",
                 "SRC-NTRS-20100027319")),
    "WAVE1-RIGHTS": dict(
        decision="owner (Cemil Eray), 2026-10-09: accept the Wave-1 rights readings as owner-reviewed. This is a "
                 "RocketForge shipping-policy review, not a legal determination. All host metadata, printed "
                 "notices and per-content shipping restrictions are kept; no restrictive source is upgraded "
                 "because of the review.",
        sources=("SRC-DB05-NTRS-19940016798", "SRC-DB05-NTRS-20100027316", "SRC-NTRS-19650013470",
                 "SRC-NASA-TND7143", "SRC-JSC-19950", "SRC-DB05-NTRS-19850008634", "SRC-NTRS-19860012108",
                 "SRC-IBIBLIO-SSMEOVERVIEW", "SRC-NASA-RS25-FS2025")),
    "DB2A-MANIFEST-METADATA": dict(
        decision="owner (Cemil Eray), 2026-10-09: re-approve the DB-2A manifest metadata changes (text_basis, "
                 "NOT_PROMOTED metadata, literal OWNER_DECISIONS). DB-2A shipped production data stays "
                 "item-for-item unchanged.",
        sources=()),
}

RESEARCH_CONFLICTS = {
    "CF-DB05-J2S-DATES": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-J-2S-015", "AS-DB05-US-J-2S-016", "AS-DB05-US-J-2S-017", "AS-DB05-US-J-2S-018", "AS-DB05-US-J-2S-019", "AS-DB05-US-J-2S-020",),
                              argument="PARTIALLY_RESOLVED: the timeline dates are not shipped."),
    "CF-DB05-J2S-CYCLE": dict(decision="CARRIED_NOT", touches=("AS-DB05-US-J-2S-007",), competing={},
                              argument="RESOLVED in DB-0.5: tap-off, Tier A."),
    "CF-DB05-F1-RATING": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-F-1-001", "AS-DB05-US-F-1-018", "AS-DB05-US-F-1-010"),
        owner_released=("AS-DB05-US-F-1-002", "AS-DB05-US-F-1-003", "AS-DB05-US-F-1-004"),
        owner_accepted=_F1_RATING, owner_scope="CFG-F1",
                              argument="UNRESOLVED: three primary sea-level ratings with no established epochs; "
                                       "they stay withheld. The same table's vacuum thrust and sea-level and "
                                       "vacuum Isp are released by the owner's decision for CFG-F1 only."),
    "CF-DB05-F1-PC": dict(decision="CARRIED_NOT", touches=("AS-DB05-US-F-1-005",),
        owner_accepted=_F1_PC, owner_scope="CFG-F1",
        competing={"SRC-WIKI-F1 70 bar (1,015 psi)": "search result, never opened",
                   "SRC-PURDUE-F1 982 psi": "search result, never opened"},
                          argument="PARTIALLY_RESOLVED in DB-0.5: the manufacturer's 1,125 psia (station unstated) "
                                   "against secondary values that may be nozzle-stagnation figures. Shipped for "
                                   "CFG-F1 only, station UNKNOWN, by owner decision."),
    "CF-DB05-F1-MASS": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-F-1-007",),
                            argument="UNRESOLVED: 18,616 lb has no printed definition."),
    "CF-DB05-LMDE-REPORTNO": dict(decision="CARRIED_NOT", touches=(), competing={},
                                  argument="RESOLVED in DB-0.5 (report number verified); no value involved."),
    "CF-DB05-OMS-ISP": dict(decision="CARRIED_NOT", touches=("AS-DB05-US-AJ10-190-004",),
                            competing={"AS-DB05-US-AJ10-190-002": "the same 313 s in the rights-withheld workbook",
                                       "SRC-WIKI-OMS 316 s": "search result, never opened"},
                            argument="RESOLVED in DB-0.5: 313 s in two Tier A manuals; 316 s has no primary support."),
    "CF-DB05-OMS-PCBAND": dict(decision="CARRIED_NOT", touches=(), competing={},
                               argument="EXPLAINED; no chamber pressure ships."),
    "CF-DB05-RS25-AREARATIO": dict(decision="CARRIED_NOT", touches=(), competing={},
                                   argument="EXPLAINED (configuration); the original-throat 77.5:1 ships for its "
                                            "own configuration from another DB-0.5 record."),
    "CF-DB05-RS25-PC": dict(decision="CARRIED_NOT",
                            touches=("AS-DB05-US-SSME-BLOCK-II-027", "AS-DB05-US-SSME-BLOCK-II-028"), competing={},
                            argument="EXPLAINED: the values differ by power level and throat; each ships at its own "
                                     "configuration and point."),
    "CF-DB05-RS25-THRUSTREF": dict(decision="CARRIED_NOT",
                                   touches=("AS-DB05-US-SSME-BLOCK-II-016", "AS-DB05-US-SSME-BLOCK-II-034"),
                                   competing={},
                                   argument="EXPLAINED: the values differ by power level (RPL, 104.5%, 109%)."),
    "CF-DB05-RS25-MASS": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-SSME-BLOCK-II-012", "AS-DB05-US-SSME-BLOCK-II-015", "AS-DB05-US-SSME-BLOCK-II-018",), argument="UNRESOLVED: definitions not printed."),
    "CF-DB05-RS25-PUMPPOWER": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-SSME-BLOCK-II-007", "AS-DB05-US-SSME-BLOCK-II-008", "AS-DB05-US-SSME-BLOCK-II-021", "AS-DB05-US-SSME-BLOCK-II-022",), argument="UNRESOLVED: no power level printed."),
    "CF-DB05-RS25-HPOTPSPEED": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-SSME-BLOCK-II-036",),
                                    argument="PARTIALLY_RESOLVED: no Block II operating speed among opened documents."),
    "CF-DB05-RS25-HPFTSPEED": dict(decision="WITHHOLD", withhold=(),
                                   argument="UNRESOLVED: only the Block IIA (withheld) value exists."),
    "CF-DB05-RS25-SLTHRUST": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-SSME-BLOCK-II-001", "AS-DB05-US-SSME-BLOCK-II-011", "AS-DB05-US-SSME-BLOCK-II-017", "AS-DB05-US-SSME-BLOCK-II-035", "AS-DB05-US-SSME-BLOCK-II-037", "AS-DB05-US-SSME-BLOCK-II-039", "AS-DB05-US-SSME-BLOCK-II-041",),
                                  argument="UNRESOLVED: approximations and single-configuration values."),
}

SCHEMATICS = {
    "SCH-DB05-F1-BIGGS-SCHEM": dict(provenance="ORIGINAL_MANUFACTURER",
                                    drawn_by="Rocketdyne (viewgraph 'F-1 Engine Schematic'), as printed by NASA"),
    "SCH-DB05-H1-SA10-F31": dict(provenance="ORIGINAL_CONTRACTOR",
                                 drawn_by="Chrysler Corporation Space Division (NASA contract NAS 8-4016), as printed "
                                          "in SDES-64-415 Vol. VIII"),
    "SCH-DB05-LMDE-TND7143-F3": dict(provenance="ORIGINAL_AGENCY", drawn_by="NASA, as printed in TN D-7143"),
    "SCH-DB05-LMDE-TND7143-F7": dict(provenance="ORIGINAL_AGENCY", drawn_by="NASA, as printed in TN D-7143"),
}

_NEUTRAL = "an element known only from a rights-withheld source (not recorded)"
_F1S = "NTRS 20100027316 slide 'F-1 Engine Schematic'"
_F1T = "NTRS 20100027316 text pp.4-5"
_F17 = "NTRS 20100027316 PDF p.16, slide 'F-1 Engine Basic Features' (F1-7.ppt)"
_M = "MSFC-MAN-503 is withheld (rights conflict unresolved)"

TOPOLOGIES = (
    dict(engine="ENG-US-F-1", topology_id="TOPO-F1", scope=("CONFIGURATION", _F1),
         label="F-1 engine flow (Rocketdyne 'F-1 Engine Schematic')",
         schematic_ids=("SCH-DB05-F1-BIGGS-SCHEM",), text_source_ids=("SRC-DB05-NTRS-20100027316",),
         withhold_nodes={"N-STAGE-PRESS": _NEUTRAL},
         withhold_edges={
             14: "turbine exhaust routing to the nozzle extension: Biggs (text p.4) puts the exhaust into the "
                 "nozzle at 10:1; the route between turbine and extension is not recorded",
             15: "turbine exhaust routing to the nozzle extension: Biggs (text p.4) puts the exhaust into the "
                 "nozzle at 10:1; the route between turbine and extension is not recorded",
             18: _NEUTRAL},
         restate_nodes={
             "N-TP-TURB": dict(text_basis=("AS-DB05-US-F-1-029", "AS-DB05-US-F-1-012",), locator=f"{_F1S}; {_F1T}", reason=f"{_M}; the slide draws the turbopump, Biggs "
                                                                 "text p.4 'It took the single turbine to run the two pumps'"),
             "N-GG": dict(label="Gas Generator", reason="the slide labels it 'Gas Generator'; 'with dual ball valve' "
                                                        "is not in the slide or Biggs's text"),
             "N-HEX": dict(evidence="SHOWN_IN_SCHEMATIC", label="Heat Exchanger",
                           reason="drawn and labelled on the slide; no Biggs text describes it, and 'on turbine "
                                  "exhaust' came from MSFC-MAN-503 (withheld)"),
             "N-HYP": dict(text_basis=("AS-DB05-US-F-1-031",), locator=f"{_F1S}; {_F1T}", reason="text basis restated: Biggs text p.5 'The hypergol "
                                                             "cartridge ... would automatically ignite as it got into the chamber'"),
             "N-TC-COOL": dict(locator=_F1T, text_basis=("AS-DB05-US-F-1-030", "AS-DB05-US-F-1-014",), reason=f"{_M}; Biggs text p.4 'tube-wall down to the 10:1 expansion'"),
             "N-NOZEXT": dict(text_basis=("AS-DB05-US-F-1-014",), locator=_F1T, reason=f"{_M}; Biggs text p.4 'double-wall, hot, gas-cooled nozzle extension'"),
             "N-AMB": dict(text_basis=("AS-DB05-US-F-1-014",), locator=_F1T, reason=_M),
             "N-HYDRAULIC": dict(text_basis=("AS-DB05-US-F-1-016",), locator=_F17, reason=f"{_M}; the 'Basic Features' viewgraph: 'Hydraulic power for "
                                                      "engine valve actuators and vehicle thrust vector control actuators'"),
         },
         restate_edges={
             7: dict(locator=f"{_F1S}; {_F1T}", text_basis=("AS-DB05-US-F-1-030",), reason=f"{_M}; Biggs text p.5 'The fuel for the thrust chamber went "
                                                       "into the middle manifold, then went down the tubes to cool the tubes'"),
             8: dict(locator=f"{_F1S}; {_F1T}", text_basis=("AS-DB05-US-F-1-030",), reason=f"{_M}; Biggs text p.5, as E07"),
             9: dict(text_basis=("AS-DB05-US-F-1-030",), locator=_F1T, reason=f"{_M}; Biggs text p.5, back through the other half of the tubes"),
             11: dict(locator=f"{_F1S}; {_F1T}", text_basis=("AS-DB05-US-F-1-032",), reason=f"{_M}; Biggs text p.5 'the igniter fuel valve would open, "
                                                        "allowing the fuel to go into the chamber'"),
             12: dict(locator=f"{_F1S}; {_F1T}", text_basis=("AS-DB05-US-F-1-031",), reason=f"{_M}; Biggs text p.5, hypergol ignites in the chamber"),
             13: dict(text_basis=("AS-DB05-US-F-1-028",), locator=f"{_F1S}; {_F17}", reason=f"{_M}; 'Turbine drive power from gas generator'"),
             16: dict(locator=_F1T, text_basis=("AS-DB05-US-F-1-014",), reason=_M),
             17: dict(text_basis=("AS-DB05-US-F-1-014",), locator=_F1T, reason=_M),
             19: dict(text_basis=("AS-DB05-US-F-1-016",), locator=_F17, reason=_M),
         },
         restate_omissions={
             "helium supply to the heat exchanger (stage)": _NEUTRAL,
             "4-way control valve and checkout valve": "4-way control valve",
             "gas generator igniters and exhaust igniters": _NEUTRAL,
         },
         extra_omissions=(),
         notes="Rests on Rocketdyne's 'F-1 Engine Schematic' viewgraph and Biggs's text only. MSFC-MAN-503, which "
               "DB-0.5 also used, is withheld for rights; the elements that rested on it alone are left out and "
               "listed as omissions."),
    dict(engine="ENG-US-H-1-188K", topology_id="TOPO-H1-188K-SA10", scope=("CONFIGURATION", _H1),
         label="H-1 inboard engine, Saturn I SA-10 (SDES-64-415 Vol. VIII Figure 3-1)",
         schematic_ids=("SCH-DB05-H1-SA10-F31",), text_source_ids=("SRC-NTRS-19650013470",),
         withhold_nodes={}, withhold_edges={},
         restate_nodes={},
         restate_edges={
             0: dict(role="fuel discharge", removes=(" (968 -> 930 psia callouts)",),
                     reason="the schematic's pressure callouts are withheld (operating point not stated)"),
             11: dict(role="LOX discharge", removes=(" (880 psia callout)",),
                      reason="the schematic's pressure callouts are withheld (operating point not stated)"),
             12: dict(role="LOX dome and injector", removes=(" (830 psia callout downstream)",),
                      reason="the schematic's pressure callouts are withheld (operating point not stated)"),
             16: dict(role="fuel bootstrap line from fuel manifold via orifice B32", removes=(" (728 psia callout)",),
                      reason="the schematic's pressure callouts are withheld (operating point not stated)"),
         },
         restate_omissions={},
         extra_omissions=(),
         notes="The inboard engine panel of the SA-10 mechanical schematic. Outboard engines add the closed-loop "
               "hydraulic system and the turbine exhaust aspirator, which are not modelled."),
    dict(engine="ENG-US-LMDE", topology_id="TOPO-LM-DPS-FINAL", scope=("PROPULSION_UNIT", "UNIT-LM-DPS-FINAL"),
         label="LM descent propulsion system, final design (TN D-7143 Figures 3 and 7)",
         schematic_ids=("SCH-DB05-LMDE-TND7143-F3", "SCH-DB05-LMDE-TND7143-F7"), text_source_ids=("SRC-NASA-TND7143",),
         withhold_nodes={}, withhold_edges={}, restate_nodes={}, restate_edges={}, restate_omissions={},
         extra_omissions=(),
         notes="The final DPS design only: the descent stage's pressurization, tanks and feed (vehicle-owned) and "
               "the engine's flow-control valves, actuator, shutoff valves, variable-area injector, chamber and "
               "nozzle extension (engine-owned)."),
)
