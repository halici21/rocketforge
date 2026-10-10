"""DB-2B Wave 2 promotion manifest: difficult and international targets, decided entry by entry.

Read with ``db2a_manifest.py`` and ``db2b_wave1_manifest.py``: the promotion script merges
the three into one production corpus and applies the same gates to all of them. Every
DB-0.5 assertion of the Wave 2 engines is either promoted below or listed in
``NOT_PROMOTED`` with a disposition and a reason.

Targets: RL10A-4-2, RL10B-2, RD-170, IPD, RS-68A, LR87 (only LR87AJ-11 is supported by an
opened document), Rutherford (sea level and vacuum). RL10A-4-2 and Rutherford ship nothing:
every document that states them carries a copyright notice.

No owner decision is recorded here. Where shipping a value would need one, it is withheld.
"""

from __future__ import annotations

from db2a_manifest import P

SEED_ENGINES = ("ENG-US-RL10A-4-2", "ENG-US-RL10B-2", "ENG-SU-RD-170", "ENG-US-IPD", "ENG-US-RS-68A",
                "ENG-US-LR87-AJ-11", "ENG-NZ-RUTHERFORD", "ENG-NZ-RUTHERFORD-VACUUM")
ACCOUNTED_ENGINES = SEED_ENGINES

#: Wave 2 adds two reasons the earlier vocabulary had no word for; both only withhold.
DISPOSITIONS = ("WITHHELD_CONFLICT", "WITHHELD_RIGHTS", "WRONG_CONFIGURATION", "WRONG_OPERATING_POINT",
                "SOURCE_SCOPE_TOO_BROAD", "SOURCE_NOT_OPENED", "MISSING_REQUIRED_SEMANTICS", "DUPLICATE",
                "NOT_NEEDED", "OWNER_DECISION_REQUIRED",
                "SECONDHAND_MANUFACTURER_VALUE",  # a manufacturer's value known only through a third party's transcription
                "INFERRED_ONLY",  # a third party's inference, not a reported value
                "DISCOVERY_ONLY_SOURCE")  # a blog or similar (DB-1 authority E): discovery or conflict context only

_RB2, _RD, _IPD = "CFG-RL10B-2-DIV", "CFG-RD-170", "CFG-IPD"
_R68A, _LR = "CFG-RS-68A", "CFG-LR87-AJ-11-T3E"

SEED_SUBJECTS = {
    "ENG-US-RL10B-2": ("FAM-RL10", "VAR-RL10B-2", _RB2),
    "ENG-SU-RD-170": ("FAM-RD170", "VAR-RD-170", _RD),
    "ENG-US-IPD": ("FAM-IPD", "VAR-IPD", _IPD),
    "ENG-US-RS-68A": ("FAM-RS68", "VAR-RS-68A", _R68A),
    "ENG-US-LR87-AJ-11": ("FAM-LR87", "VAR-LR87-AJ-11", _LR),
    # nothing of these ships (every source is copyrighted), so they have no production identity
    "ENG-US-RL10A-4-2": (),
    "ENG-NZ-RUTHERFORD": (),
    "ENG-NZ-RUTHERFORD-VACUUM": (),
}

#: Each configuration takes values only from the documents that describe it.
CONFIGURATION_SOURCES = {
    _RB2: ("SRC-ULA-DIV-INAUGURAL",),
    _RD: ("SRC-NTRS-19910018906", "SRC-DB05-NTRS-19950002748"),
    _IPD: ("SRC-NTRS-IPD-WPB", "SRC-DB05-NTRS-20050243602"),
    _R68A: ("SRC-DB05-NTRS-20090014109",),
    _LR: ("SRC-DB05-NTRS-19750004937",),
}

# ------------------------------------------------------------------ sources

_NO_NOTICE = "no copyright notice on pages read (extracted text of every page checked 2026-10-10)"


def _src(organization, authors, title, year, identifiers, source_type, host, figures, review_note, *,
         authority="A", primacy="PRIMARY", printed=_NO_NOTICE):
    return dict(organization=organization, authors=authors, title=title, year=year, identifiers=identifiers,
                source_type=source_type, authority=authority, primacy=primacy, host=host, printed=printed,
                review="CONSISTENT", figures=figures, review_note=review_note)


SOURCES = {
    "SRC-ULA-DIV-INAUGURAL": _src(
        "The Boeing Company", ("Michael D. Berglund", "Mark Wilkins"),
        "Critical Events of the Inaugural Launch of the Boeing Delta IV Expendable Launch Vehicle", 2003,
        {"host": "ulalaunch.com"}, "AIAA conference paper", "NONE", "VALUES_WITH_ATTRIBUTION",
        "No repository rights statement (a PDF hosted by ulalaunch.com). Each page carries the AIAA header; no "
        "copyright notice was found in the extracted text of its 9 pages (re-checked 2026-10-10).",
        authority="B"),
    "SRC-NTRS-19910018906": _src(
        "Rockwell International, Rocketdyne Division", (), "Space transportation propulsion USSR launcher technology, 1990",
        1991, {"NTRS": "19910018906"}, "contractor briefing", "GOV_PUBLIC_USE_PERMITTED", "VALUES_WITH_ATTRIBUTION",
        "NTRS government public use. A Western analysis of Soviet engines compiled from public-domain sources "
        "(p.12 lists them); its RD-170 schematic is a reconstruction from display photographs.",
        authority="B", primacy="SECONDARY"),
    "SRC-DB05-NTRS-19950002748": _src(
        "NASA Marshall Space Flight Center", ("Ten-See Wang", "Paul McConnaughey", "Saif Warsi", "Yen-Sen Chen"),
        "CFD assessment of the carbon monoxide and nitric oxide formation from RD-170 hot-fire testing", 1994,
        {"NTRS": "19950002748"}, "NASA conference paper", "GOV_PUBLIC_USE_PERMITTED", "VALUES_WITH_ATTRIBUTION",
        "NTRS government public use; no notice on the pages. A NASA analysis of an RD-170 test, not an engine "
        "document.", authority="B", primacy="SECONDARY"),
    "SRC-NTRS-IPD-WPB": _src(
        "NASA John C. Stennis Space Center", ("J. P. Sass", "N. G. Raines", "H. M. Ryan"),
        "Facility Activation and Characterization for IPD Workhorse Preburner and Oxidizer Turbopump Hot-Fire "
        "Testing at NASA Stennis Space Center", 2004, {"NTRS": "20040084662"}, "NASA conference paper",
        "GOV_PUBLIC_USE_PERMITTED", "VALUES_WITH_ATTRIBUTION",
        "NTRS government public use; no notice on the pages."),
    "SRC-DB05-NTRS-20050243602": _src(
        "NASA", ("Lawrence D. Huebner", "Naseem H. Saiyed", "Marion Shayne Swith"),
        "Advanced Development Projects for Constellation From The Next Generation Launch Technology Program "
        "Elements", 2005, {"NTRS": "20050243602"}, "NASA conference paper", "GOV_PUBLIC_USE_PERMITTED",
        "VALUES_WITH_ATTRIBUTION", "NTRS government public use; no notice on the pages."),
    "SRC-DB05-NTRS-20090014109": _src(
        "NASA Marshall Space Flight Center; Department of the Air Force",
        ("Steve Creech", "Jim Taylor", "Scott Bellamy", "Fritz Kuck"), "Ares V and RS-68B", 2008,
        {"NTRS": "20090014109"}, "conference paper", "PUBLIC_USE_PERMITTED", "VALUES_WITH_ATTRIBUTION",
        "NTRS permits public use; no notice on the pages. Describes the RS-68A relative to the RS-68.",
        primacy="SECONDARY"),
    "SRC-DB05-NTRS-19750004937": _src(
        "General Dynamics Convair Aerospace", (), "Titan IIIE/Centaur D-1T Systems Summary", 1973,
        {"NTRS": "19750004937", "report": "CASD-LVP73-007"}, "contractor report", "GOV_PUBLIC_USE_PERMITTED",
        "VALUES_WITH_ATTRIBUTION",
        "NTRS government public use; no notice on the pages. The programme's systems summary for NASA."),
}

#: Sources Wave 2 opened but does not carry. Each prints a copyright notice.
WITHHELD_SOURCES = {
    "SRC-NAP-11780": dict(
        reason="NRC (2006) web edition: '(c) National Academy of Sciences'; read online, not reproducible",
        locator_tokens=("NAP 11780", "NRC 2006", "Table D-2", "Table D-4")),
    "SRC-ULA-DIV-GPSIIISV02": dict(reason="ULA mission booklet: 'Copyright (c) 2019 United Launch Alliance' p.1",
                                   locator_tokens=("DCSS' paragraph",)),
    "SRC-ULA-CENTAUR-ICLT4": dict(reason="Lockheed Martin conference paper: 'Copyright 2002 Lockheed Martin "
                                         "Corporation' p.2", locator_tokens=("'Engine System'",)),
    "SRC-RL-PRESSKIT-2017": dict(reason="Rocket Lab press kit: '(c) Rocket Lab USA 2017' p.8",
                                 locator_tokens=("About Rutherford engine", "launch timeline")),
    "SRC-RL-500-TESTS": dict(reason="Rocket Lab release: '(c)2026 Rocket Lab USA' site footer",
                             locator_tokens=("release of 31 Jan 2018",)),
    "SRC-RKLB-PAYLOAD-INCREASE": dict(reason="Rocket Lab release: '(c)2026 Rocket Lab USA' site footer",
                                      locator_tokens=("release of 4 Aug 2020",)),
    "SRC-RL-ELECTRON-PAGE": dict(reason="Rocket Lab web page: '(c)2026 Rocket Lab USA' site footer",
                                 locator_tokens=("Electron page",)),
}

#: Wording that would carry withheld or conflicted content into a shipped record.
WITHHELD_CONTENT_TERMS = {
    # NAP (copyrighted) and the unresolved Pc/Isp pair
    _RB2: ("644", "633", "466.5", "465.5", "285:1", "National Academy"),
    # the RS-68 baseline and the conflicted thrust
    _R68A: ("650,000", "702,000", "705,000", "705,250", "L3Harris"),
    # the placard values, the unresolved mixture ratios and Rockwell's conversions
    _RD: ("740 t", "806 t", "308 s", "336 s", "kgs/cm2", "2.58", "2.47", "2.63", "3,556", "1,631,404", "1,776,908"),
    # a lower bound and a direction-less mixture ratio
    _LR: ("over 800", "1.915"),
}

# ------------------------------------------------------------------ identity

FAMILIES = (
    ("FAM-RD170", "RD-170", "The Energia booster engine; no manufacturer document was opened."),
    ("FAM-IPD", "Integrated Powerhead Demonstrator", "AFRL/NASA full-flow staged-combustion demonstrator programme."),
    ("FAM-RS68", "RS-68", ""),
    ("FAM-LR87", "LR87", "Aerojet Titan first-stage engines; only the LR87AJ-11 is supported by an opened document "
                         "here."),
)

VARIANTS = (
    ("VAR-RL10B-2", "FAM-RL10", "RL10B-2", "Not the RL10A-3-3A or RL10A-4 series."),
    ("VAR-RD-170", "FAM-RD170", "RD-170", ""),
    ("VAR-IPD", "FAM-IPD", "IPD", ""),
    ("VAR-RS-68A", "FAM-RS68", "RS-68A", "Not the RS-68: no RS-68 value is filed here."),
    ("VAR-LR87-AJ-11", "FAM-LR87", "LR87AJ-11", ""),
)

CONFIGURATIONS = (
    (_RB2, "VAR-RL10B-2", "RL10B-2, Delta IV second-stage engine (inaugural launch, 2002)",
     "Delta IV second stage, all configurations, as of the 20 November 2002 inaugural launch",
     "As the Boeing inaugural-launch paper describes it. The NAP compilation (copyrighted) and the ULA mission "
     "booklets (copyrighted) are not carried, so chamber pressure, Isp and area ratio are missing."),
    (_RD, "VAR-RD-170", "RD-170, Energia booster engine, as described in Western analyses",
     ("MISSING", "NOT_AUDITED", "no manufacturer document was opened; effectivity unknown"),
     "Every statement is secondary: a Rockwell briefing (1991) and a NASA MSFC analysis (1994). The display-placard "
     "values Rockwell transcribed are not carried, and the graph is Rockwell's reconstruction from photographs."),
    (_IPD, "VAR-IPD", "Integrated Powerhead Demonstrator as installed and tested at SSC E-1 (2004-2005)",
     "installed at SSC E-1 Cell 3 on 15 October 2004; start-sequence tests in 2005 (NTRS 20050243602 p.6)",
     "The demonstrator engine, not its workhorse test articles. The key AFRL and DTIC papers are blocked."),
    (_R68A, "VAR-RS-68A", "RS-68A, as NASA MSFC describes it against the RS-68 (Ares V and RS-68B, 2008)",
     ("MISSING", "NOT_AUDITED", "the paper describes the upgrade programme, not a flight effectivity"),
     "What the RS-68A changes from the RS-68, as text. No RS-68A value ships: the one thrust value opened is in a "
     "launch-day NASA blog (discovery only) and in an unresolved conflict."),
    (_LR, "VAR-LR87-AJ-11", "LR87AJ-11, Titan IIIE stage I engine (General Dynamics Convair CASD-LVP73-007)",
     "Titan IIIE stage I, as of the September 1973 systems summary",
     "A pair of identical subassemblies on one frame (report p.6-19). No other LR87 variant is carried: none was "
     "supported by an opened document."),
)

OPERATING_POINTS = ()
UNITS = ()
ALIASES = ()

# ------------------------------------------------------------------ assertions

ASSERTIONS = (
    # RL10B-2: the Boeing inaugural-launch paper
    P("AS-DB05-US-RL10B-2-009", _RB2, "performance.thrust", ("number", 24750), "NOMINAL", cond=dict(environment="UNKNOWN"),
      note="Printed as 'Producing 24,750 lb of thrust'; the environment is not printed."),
    P("AS-DB05-US-RL10B-2-011", _RB2, "propellants.combination", ("text",), "OTHER"),
    P("AS-DB05-US-RL10B-2-012", _RB2, "propellants.oxidizer", ("enum", "LIQUID_OXYGEN"), "NOMINAL"),
    P("AS-DB05-US-RL10B-2-013", _RB2, "propellants.fuel", ("enum", "LIQUID_HYDROGEN"), "NOMINAL"),
    P("AS-DB05-US-RL10B-2-014", _RB2, "nozzle.extension", ("text",), "OTHER"),
    # RD-170: secondary descriptions
    P("AS-DB05-SU-RD-170-010", _RD, "architecture.layout", ("text",), "OTHER",
      note="A NASA analyst's description (secondary)."),
    P("AS-DB05-SU-RD-170-011", _RD, "propellants.oxidizer", ("enum", "LIQUID_OXYGEN"), "NOMINAL"),
    P("AS-DB05-SU-RD-170-012", _RD, "propellants.fuel", ("enum", "KEROSENE"), "NOMINAL",
      note="Printed 'Kerosene'; not filed as RP-1."),
    # IPD
    P("AS-DB05-US-IPD-013", "VAR-IPD", "performance.thrust", ("number", 250000), "DESIGN_VALUE",
      cond=dict(environment="UNKNOWN"),
      reading="printed as the programme's goal: 'the goal of designing, fabricating, and testing a 250k-lb-thrust "
              "... engine'",
      note="The demonstrator programme's design goal, not a value the tested engine reached (about 90% power at the "
           "peak of a start transient by 2005)."),
    P("AS-DB05-US-IPD-002", _IPD, "architecture.cycle", ("enum", "FULL_FLOW_STAGED_COMBUSTION"), "NOMINAL"),
    P("AS-DB05-US-IPD-010", _IPD, "propellants.oxidizer", ("enum", "LIQUID_OXYGEN"), "NOMINAL",
      note="Printed 'cryogenic hydrogen/oxygen engine'."),
    P("AS-DB05-US-IPD-011", _IPD, "propellants.fuel", ("enum", "LIQUID_HYDROGEN"), "NOMINAL",
      note="Printed 'cryogenic hydrogen/oxygen engine'."),
    P("AS-DB05-US-IPD-006", "VAR-IPD", "identity.programme", ("text",), "OTHER"),
    P("AS-DB05-US-IPD-007", "VAR-IPD", "identity.contractors", ("text",), "OTHER",
      note="As of the 2005 paper ('Currently')."),
    P("AS-DB05-US-IPD-008", _IPD, "turbomachinery.components", ("text",), "OTHER"),
    P("AS-DB05-US-IPD-009", _IPD, "test_history.engine", ("text",), "OTHER", note="Status as of the 2005 paper."),
    # RS-68A
    P("AS-DB05-US-RS-68A-003", _R68A, "changes.turbine_nozzles", ("text",), "OTHER",
      note="A change relative to the RS-68, not an RS-68A thrust value."),
    P("AS-DB05-US-RS-68A-004", _R68A, "changes.injector", ("text",), "OTHER"),
    P("AS-DB05-US-RS-68A-005", _R68A, "changes.reliability", ("text",), "OTHER"),
    # LR87AJ-11
    P("AS-DB05-US-LR87-AJ-11-001", _LR, "performance.thrust", ("number", 520000), "RATED",
      cond=dict(environment="UNKNOWN"),
      note="Printed as 'Rated Thrust'; the engine section prints the same 520,000 as 'Altitude Thrust' (p.6-21)."),
    P("AS-DB05-US-LR87-AJ-11-002", _LR, "performance.specific_impulse_vac", ("number", 301.1), "RATED",
      cond=dict(environment="VACUUM", isp_basis="UNKNOWN")),
    P("AS-DB05-US-LR87-AJ-11-003", _LR, "propellants.fuel", ("enum", "AEROZINE_50"), "NOMINAL"),
    P("AS-DB05-US-LR87-AJ-11-004", _LR, "propellants.oxidizer", ("enum", "NITROGEN_TETROXIDE"), "NOMINAL"),
    P("AS-DB05-US-LR87-AJ-11-005", _LR, "architecture.cooling_feed", ("text",), "OTHER"),
    P("AS-DB05-US-LR87-AJ-11-006", _LR, "architecture.layout", ("text",), "OTHER"),
    P("AS-DB05-US-LR87-AJ-11-007", _LR, "turbines.drive_source", ("text",), "OTHER"),
    P("AS-DB05-US-LR87-AJ-11-008", _LR, "architecture.feed", ("enum", "PUMP_FED"), "NOMINAL"),
    P("AS-DB05-US-LR87-AJ-11-009", _LR, "architecture.cycle", ("enum", "GAS_GENERATOR"), "NOMINAL"),
    P("AS-DB05-US-LR87-AJ-11-010", _LR, "control.method", ("text",), "OTHER"),
    P("AS-DB05-US-LR87-AJ-11-014", _LR, "performance.mass_flow_total", ("number", 1727), "NOMINAL"),
    P("AS-DB05-US-LR87-AJ-11-015", _LR, "performance.mass_flow_oxidizer", ("number", 1135), "NOMINAL"),
    P("AS-DB05-US-LR87-AJ-11-016", _LR, "performance.mass_flow_fuel", ("number", 592), "NOMINAL"),
    P("AS-DB05-US-LR87-AJ-11-018", _LR, "performance.operating_cycle", ("number", 165), "NOMINAL",
      note="Printed as 'Operating Cycle, sec' in the engine performance summary: the engine's rating, not the "
           "Titan IIIE flight burn (the report gives about 146 s for that, p.2-3)."),
    P("AS-DB05-US-LR87-AJ-11-019", _LR, "nozzle.area_ratio", ("number", 15), "NOMINAL"),
)

FIELD_RENAMES = {
    # the sentence describes the turbine-nozzle change and the thrust it adds, not a thrust value
    "changes.thrust": ("changes.turbine_nozzles",),
}
OPERATING_POINT_MAP = {}
CONFIGURATION_MAP = {}

_NAP = ("WITHHELD_RIGHTS", "NRC (2006) web edition: (c) National Academy of Sciences, read online, not reproducible")
_LM = ("WITHHELD_RIGHTS", "Lockheed Martin conference paper: printed copyright")
_RKLB = ("WITHHELD_RIGHTS", "Rocket Lab material: printed copyright")
_PLACARD = ("SECONDHAND_MANUFACTURER_VALUE",
            "the 1989 display placard's value as Rockwell transcribed it; the placard itself was not opened, so the "
            "manufacturer's statement is not carried second-hand")

NOT_PROMOTED = {
    # RL10A-4-2: every source is copyrighted
    **{f"AS-DB05-US-RL10A-4-2-00{i}": _NAP for i in range(1, 9)},
    "AS-DB05-US-RL10A-4-2-009": _LM,
    "AS-DB05-US-RL10A-4-2-010": _LM,
    # RL10B-2
    **{f"AS-DB05-US-RL10B-2-00{i}": _NAP for i in range(1, 9)},
    "AS-DB05-US-RL10B-2-010": ("WITHHELD_RIGHTS", "ULA mission booklet: 'Copyright (c) 2019 United Launch Alliance'"),
    # RD-170
    **{f"AS-DB05-SU-RD-170-00{i}": _PLACARD for i in range(1, 5)},
    "AS-DB05-SU-RD-170-005": ("WITHHELD_CONFLICT", "placard chamber pressure in PARTIALLY_RESOLVED CF-DB05-RD170-PC "
                                                   "(and known only through Rockwell's transcription)"),
    "AS-DB05-SU-RD-170-006": ("WITHHELD_CONFLICT", "Rockwell's layout sentence; the conflict gate matches it to "
                                                   "CF-DB05-RD170-PC (the '2' of 'kgs/cm2' against its '2 preburners'), "
                                                   "so it is withheld; the NASA description (AS-DB05-SU-RD-170-010) "
                                                   "carries the four-chamber layout and the graph shows the preburners"),
    "AS-DB05-SU-RD-170-007": ("INFERRED_ONLY", "Rockwell's inference of the shaft order from display photographs"),
    "AS-DB05-SU-RD-170-008": ("WITHHELD_CONFLICT", "mixture ratio in UNRESOLVED intra-document conflict CF-DB05-RD170-MR"),
    "AS-DB05-SU-RD-170-009": ("WITHHELD_CONFLICT", "mixture ratio in UNRESOLVED intra-document conflict CF-DB05-RD170-MR"),
    # IPD
    "AS-DB05-US-IPD-001": ("MISSING_REQUIRED_SEMANTICS", "printed as the demonstrator's thrust class ('a 250K lbf "
                                                         "... thrust ... technology demonstrator') with no design, "
                                                         "goal or rating word; AS-DB05-US-IPD-013 carries the goal "
                                                         "from the document that prints it as one"),
    "AS-DB05-US-IPD-003": ("WRONG_CONFIGURATION", "the workhorse preburner test article, not the IPD engine"),
    "AS-DB05-US-IPD-004": ("NOT_NEEDED", "component test counts of workhorse test articles; the engine's own test "
                                         "status (AS-DB05-US-IPD-009) is carried"),
    "AS-DB05-US-IPD-005": ("WRONG_CONFIGURATION", "the igniter of the workhorse preburner test, not of the IPD engine"),
    "AS-DB05-US-IPD-012": ("DUPLICATE", "the cycle again (NTRS 20060004818); AS-DB05-US-IPD-002 carries it"),
    # RS-68A
    "AS-DB05-US-RS-68A-001": ("DISCOVERY_ONLY_SOURCE", "a launch-day NASA blog (DB-1 authority E): discovery or "
                                                         "conflict context only"),
    "AS-DB05-US-RS-68A-002": ("WITHHELD_CONFLICT", "702,000 lb in PARTIALLY_RESOLVED CF-DB05-RS68A-THRUST; environment "
                                                   "not printed"),
    "AS-DB05-US-RS-68A-006": ("MISSING_REQUIRED_SEMANTICS", "printed in 2009 as 'expected to be included in the RS-68A "
                                                            "certification program': whether the certified engine has "
                                                            "it is not stated"),
    # LR87AJ-11
    "AS-DB05-US-LR87-AJ-11-011": ("MISSING_REQUIRED_SEMANTICS", "printed 'over 800 psia': a lower bound, not an "
                                                                "operating chamber pressure"),
    "AS-DB05-US-LR87-AJ-11-012": ("DUPLICATE", "the same 520,000 lb printed as 'Altitude Thrust'; "
                                               "AS-DB05-US-LR87-AJ-11-001 carries it"),
    "AS-DB05-US-LR87-AJ-11-013": ("DUPLICATE", "the same 301.1 s printed as 'Altitude Specific Impulse'; "
                                               "AS-DB05-US-LR87-AJ-11-002 (vacuum) carries it"),
    "AS-DB05-US-LR87-AJ-11-017": ("MISSING_REQUIRED_SEMANTICS", "printed 'Mixture Ratio 1.915' without a direction "
                                                                "(O/F or F/O); deriving it from the flows is not print"),
    # Rutherford: every source is copyrighted
    **{f"AS-DB05-NZ-RUTHERFORD-{i:03d}": _RKLB for i in range(1, 11)},
    **{f"AS-DB05-NZ-RUTHERFORD-VACUUM-{i:03d}": _RKLB for i in range(1, 5)},
}

RESEARCH_CONFLICTS = {
    "CF-DB05-RL10A42-THRUST-ISP": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-RL10A-4-2-001", "AS-DB05-US-RL10A-4-2-002", "AS-DB05-US-RL10A-4-2-007"),
        argument="PARTIALLY_RESOLVED: the A-4-1/A-4-2 column attribution is ambiguous, and the source is "
                 "copyrighted anyway."),
    "CF-DB05-RL10B2-PC-ISP": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-RL10B-2-002", "AS-DB05-US-RL10B-2-003", "AS-DB05-US-RL10B-2-004", "AS-DB05-US-RL10B-2-005"),
        argument="UNRESOLVED intra-document pair (644/633 psia, 466.5/465.5 s); no opened document explains it."),
    "CF-DB05-RL10B2-THRUST": dict(decision="CARRIED_NOT", touches=("AS-DB05-US-RL10B-2-009",),
        competing={"AS-DB05-US-RL10B-2-010": "ULA booklet (copyrighted), agrees", "AS-DB05-US-RL10B-2-001": "NAP "
                   "(copyrighted), agrees"},
        argument="RESOLVED in DB-0.5: three opened sources print 24,750; only the uncopyrighted one is carried."),
    "CF-DB05-RD170-PB": dict(decision="CARRIED_NOT", touches=(), competing={},
        argument="CONFIRMED_SECONDARY: two preburners is Rockwell's reading of display photographs. No claim "
                 "assertion is carried (the layout sentence is withheld under CF-DB05-RD170-PC); the graph, a "
                 "third-party reconstruction, draws the two preburner boxes."),
    "CF-DB05-RD170-MR": dict(decision="WITHHOLD", withhold=("AS-DB05-SU-RD-170-008", "AS-DB05-SU-RD-170-009"),
        argument="UNRESOLVED: two values in one document; neither is attributed to the manufacturer."),
    "CF-DB05-RD170-PC": dict(decision="WITHHOLD", withhold=("AS-DB05-SU-RD-170-005", "AS-DB05-SU-RD-170-006"),
        argument="PARTIALLY_RESOLVED: a unit question on a value known only through a transcription."),
    "CF-DB05-RS68A-THRUST": dict(decision="WITHHOLD", withhold=("AS-DB05-US-RS-68A-002",),
        argument="PARTIALLY_RESOLVED: a NASA blog's 702,000 lb (no environment) against a manufacturer figure seen "
                 "only in a search excerpt. Neither is shippable evidence of an RS-68A rating."),
    "CF-DB05-RUTHERFORD-SL-THRUST": dict(decision="CARRIED_NOT", touches=(), competing={},
        argument="EXPLAINED (two epochs); no Rutherford value is carried (rights)."),
    "CF-DB05-RUTHERFORD-VAC-THRUST": dict(decision="WITHHOLD",
        withhold=("AS-DB05-NZ-RUTHERFORD-VACUUM-002", "AS-DB05-NZ-RUTHERFORD-VACUUM-003",
                  "AS-DB05-NZ-RUTHERFORD-VACUUM-004"),
        argument="PARTIALLY_RESOLVED epochs; and the sources are copyrighted."),
}

CARRIER_GENERALISATIONS = {}

SCHEMATICS = {
    "SCH-DB05-LR87AJ11-GD-F620": dict(provenance="ORIGINAL_CONTRACTOR",
                                      drawn_by="General Dynamics Convair Aerospace, as printed in its Titan "
                                               "IIIE/Centaur D-1T systems summary (CASD-LVP73-007)"),
    "SCH-DB05-RD170-RKWL-P19": dict(provenance="THIRD_PARTY_RECONSTRUCTION",
                                    drawn_by="Rockwell International, Rocketdyne Division, reconstructed from "
                                             "photographs of the 1989 Paris Air Show display"),
}

TOPOLOGIES = (
    dict(engine="ENG-US-LR87-AJ-11", topology_id="TOPO-LR87-AJ-11", scope=("CONFIGURATION", _LR),
         label="LR87AJ-11 subassembly 1 (CASD-LVP73-007 Figure 6-20)",
         schematic_ids=("SCH-DB05-LR87AJ11-GD-F620",), text_source_ids=("SRC-DB05-NTRS-19750004937",),
         withhold_nodes={}, withhold_edges={}, restate_nodes={}, restate_edges={}, restate_omissions={},
         extra_omissions=(),
         notes="One of the two identical subassemblies, from the programme contractor's fill-and-bleed schematic "
               "and the report's text. The regenerative cooling path, the lube-oil circuit, the gas cooler and "
               "the valve sequencing are not drawn as edges."),
    dict(engine="ENG-SU-RD-170", topology_id="TOPO-RD-170", scope=("CONFIGURATION", _RD),
         label="RD-170 flow as reconstructed by Rockwell from display photographs (one of four chambers)",
         schematic_ids=("SCH-DB05-RD170-RKWL-P19",), text_source_ids=("SRC-NTRS-19910018906",),
         withhold_nodes={}, withhold_edges={}, restate_nodes={}, restate_edges={}, restate_omissions={},
         extra_omissions=(),
         notes="A third party's reconstruction, not a manufacturer drawing: every edge is 'shown' only in the sense "
               "that Rockwell drew it, with question marks on uncertain paths."),
)
