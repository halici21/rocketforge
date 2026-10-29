"""DB-2B Wave 3 promotion manifest: Japan, Europe and China, decided entry by entry.

Read with the DB-2A, Wave 1 and Wave 2 manifests: the promotion script merges all four into one production
corpus and applies the same gates to every entry. Every DB-0.5 assertion of a Wave 3 engine is either promoted
below or listed in ``NOT_PROMOTED`` with a disposition from the existing vocabulary and a reason.

Targets: LE-7, LE-7A, LE-9 (Japan); Vulcain, Vulcain 2, Vinci (Europe); YF-75, YF-75D, YF-100 and, as the
conditional seventh target chosen from the DB-0 registry, YF-77 (China).

What ships is small, and the reasons are the evidence's, not the tooling's:

* Every Japanese, European and Chinese primary document opened carries a copyright notice or a host statement
  that restricts reuse (JAXA and ESA terms of use, the JAXA repository's copyright statement, IAF, MHI, BIT
  Press). They are research evidence and are withheld here.
* The 1997 NASDA paper hosted by MEXT is under the ministry's open terms only where the State holds the rights;
  NASDA's paper is third-party content under those terms. Its rights stay RIGHTS_REVIEW_REQUIRED: an owner
  decision, not a reading this wave may make.
* The two NTRS documents (US 1990 symposium reviews of Japanese and European programmes) are shippable sources
  (NTRS government public use, no notice; the shipped one's reading owner-reviewed 2026-10-12),
  but each engine's figures in them are a third party's summary of the developer's numbers, and their rating
  tables sit in open epoch conflicts. Only the LE-7 architecture, stated on a separate overview slide, ships.

The owner's decisions of 2026-10-12 are recorded as text in ``OWNER_REVIEWS``. None of them releases a value:
three keep material withheld, and one reviews the rights reading of the one new shipped source.
``OWNER_DECISIONS`` stays empty and no conflict carries ``owner_accepted`` or ``owner_released``.
"""

from __future__ import annotations

from db2a_manifest import P

SEED_ENGINES = ("ENG-JP-LE-7", "ENG-JP-LE-7A", "ENG-JP-LE-9", "ENG-FR-VULCAIN", "ENG-FR-VULCAIN-2", "ENG-FR-VINCI",
                "ENG-CN-YF-75", "ENG-CN-YF-75D", "ENG-CN-YF-100", "ENG-CN-YF-77")
ACCOUNTED_ENGINES = SEED_ENGINES

_LE7 = "CFG-LE7-H2-1990-REVIEW"

SEED_SUBJECTS = {
    "ENG-JP-LE-7": ("FAM-LE7", "VAR-LE-7", _LE7),
    # nothing of these ships, so they have no production identity
    **{e: () for e in SEED_ENGINES if e != "ENG-JP-LE-7"},
}

#: Each configuration takes values only from the documents that describe it.
CONFIGURATION_SOURCES = {_LE7: ("SRC-DB05-NTRS-19910018905",)}

# ------------------------------------------------------------------ sources

_NO_NOTICE = "no copyright notice on pages read (extracted text of every page checked 2026-10-11)"
#: Appended to the rights reading the owner reviewed (OWNER_REVIEWS["WAVE3-NTRS-RIGHTS"]).
_OWNER_REVIEWED = " Owner-reviewed 2026-10-12 (a RocketForge shipping-policy review, not a legal determination)."

SOURCES = {
    "SRC-DB05-NTRS-19910018905": dict(
        organization="Pennsylvania State University (for the NASA symposium)", authors=("Charles L. Merkle",),
        title="A review of liquid rocket propulsion programs in Japan", year=1991,
        identifiers={"NTRS": "19910018905"}, source_type="conference paper", authority="B", primacy="SECONDARY",
        host="GOV_PUBLIC_USE_PERMITTED", printed=_NO_NOTICE, review="CONSISTENT", figures="VALUES_WITH_ATTRIBUTION",
        review_note="NTRS government public use; no notice on the pages. A US panel's June 1990 review of Japanese "
                    "programmes (Space Transportation Propulsion Technology Symposium, Penn State), compiled from "
                    "the open literature and laboratory visits: secondary for any Japanese engine fact."
                    + _OWNER_REVIEWED),
}

_JAXA = "JAXA Terms of Use: use without permission only for press, research, education or private use"
_ESA = "ESA terms: personal non-commercial use only; no redistribution"
_IAF = "IAF archive: '(c) IAF 2006-2026 all rights reserved'"

#: Sources Wave 3 opened but does not carry. Each is restricted by a notice or by its host's terms.
WITHHELD_SOURCES = {
    "SRC-MEXT-SAC-1997": dict(
        reason="NASDA paper on mext.go.jp: the ministry's open terms exclude third-party content, which NASDA's paper "
               "is; rights review required (an owner decision)",
        locator_tokens=("委12-6", "MEXT", "主要諸元", "LE－7Aエンジンの開発概要")),
    "SRC-JAXA-PRESS-LE9-2017": dict(reason=_JAXA, locator_tokens=("資料37-3",)),
    "SRC-JAXA-AA1740298002": dict(reason="IHI journal in AIREX: items protected by copyright unless otherwise "
                                         "indicated", locator_tokens=("IHI技報",)),
    "SRC-JAXA-H2": dict(reason="'(c) 2003 Japan Aerospace Exploration Agency'; " + _JAXA,
                        locator_tokens=("H-II Launch Vehicle page",)),
    "SRC-MHI-LE7A": dict(reason="'(c) MITSUBISHI HEAVY INDUSTRIES, LTD.'", locator_tokens=("mhi.com LE-7A page",)),
    "SRC-MHI-LE9": dict(reason="'(c) MITSUBISHI HEAVY INDUSTRIES, LTD.'", locator_tokens=("mhi.com LE-9 page",)),
    "SRC-IAC-LE9-2017": dict(reason=_IAF, locator_tokens=("IAC-17,C4,1,4",)),
    "SRC-ESA-VULCAIN": dict(reason=_ESA, locator_tokens=("esa.int 'Vulcain engine'",)),
    "SRC-ESA-V2-TEST": dict(reason=_ESA, locator_tokens=("esa.int news 14 May 2004",)),
    "SRC-ESA-VINCI-60S": dict(reason=_ESA, locator_tokens=("27 July 2005",)),
    "SRC-ESA-A6ENGINES": dict(reason=_ESA, locator_tokens=("The engines of Ariane 6",)),
    "SRC-IAC-21-65631": dict(reason=_IAF, locator_tokens=("IAC-21,C4,1,5",)),
    "SRC-IAC-18-45921": dict(reason=_IAF, locator_tokens=("IAC-18,C4,1,4",)),
    "SRC-IAC13-18525": dict(reason=_IAF, locator_tokens=("IAC-13,C4,1,1",)),
    "SRC-IAC13-17679": dict(reason=_IAF, locator_tokens=("IAC-13,C4,1,2",)),
    "SRC-IAC15-LOXKERO-REVIEW": dict(reason=_IAF, locator_tokens=("IAC-15,C4,1,13",)),
    "SRC-IAC17-41028": dict(reason=_IAF, locator_tokens=("IAC-17,C4,5,13",)),
    "SRC-DB05-JDSE-2021-YF100": dict(reason="'Copyright (c) Beijing Institute of Technology Press'",
                                     locator_tokens=("深空探测学报",)),
}

#: Wording that would carry withheld or conflicted content into the shipped LE-7 record.
WITHHELD_CONTENT_TERMS = {
    _LE7: ("265,000", "451", "2133", "3439", "315 sec", "tonf", "445", "Development", "6.0", "110 ton"),
}

# ------------------------------------------------------------------ identity

FAMILIES = (
    ("FAM-LE7", "LE-7", "NASDA/JAXA first-stage LOX/LH2 engines (LE-7, LE-7A); only the LE-7 is carried, and only "
                        "its architecture."),
)

VARIANTS = (
    ("VAR-LE-7", "FAM-LE7", "LE-7", "The H-II first-stage engine. Not the LE-7A: no LE-7A statement is filed here."),
)

CONFIGURATIONS = (
    (_LE7, "VAR-LE-7", "LE-7, H-II first-stage engine as a US panel described it in June 1990",
     ("MISSING", "NOT_AUDITED", "described during H-II development (June 1990 review); the flight effectivity of "
                                "the statement is not established"),
     "Architecture only, from the review's H-II overview slide (NTRS 19910018905 p.16). The same review's LE-7 "
     "figures (p.18) sit in the open epoch conflict CF-DB05-LE7-EPOCH and are a panel's summary of NASDA's numbers, "
     "so none ships; NASDA's own 1997 table is withheld pending a rights review."),
)

OPERATING_POINTS = ()
UNITS = ()
ALIASES = ()

# ------------------------------------------------------------------ assertions

ASSERTIONS = (
    P("AS-DB05-JP-LE-7-001", _LE7, "propellants.oxidizer", ("enum", "LIQUID_OXYGEN"), "NOMINAL",
      note="Printed 'LOX/LH2' under 'First Stage -- LE-7' on the review's H-II overview slide (secondary)."),
    P("AS-DB05-JP-LE-7-002", _LE7, "propellants.fuel", ("enum", "LIQUID_HYDROGEN"), "NOMINAL",
      note="Printed 'LOX/LH2' under 'First Stage -- LE-7' on the review's H-II overview slide (secondary)."),
    P("AS-DB05-JP-LE-7-003", _LE7, "architecture.cycle", ("enum", "STAGED_COMBUSTION"), "NOMINAL",
      note="Printed 'Staged Combustion' (secondary). No rich side is printed and none is inferred."),
)

FIELD_RENAMES = {}
OPERATING_POINT_MAP = {}
CONFIGURATION_MAP = {}

# ------------------------------------------------------------------ not promoted

_SECONDHAND = ("a US panel's 1990 summary of the developer's figures for an engine it did not build or test; a "
               "secondhand value is not carried (as Rockwell's RD-170 transcriptions are not)")
_MEXT = ("WITHHELD_RIGHTS", "NASDA paper hosted by MEXT: rights review required (third-party content under the "
                            "ministry's open terms); an owner decision")
_JAXA17 = ("WITHHELD_RIGHTS", "JAXA material under JAXA's terms of use (research, education, press or private use)")
_MHI = ("WITHHELD_RIGHTS", "MHI product page: '(c) MITSUBISHI HEAVY INDUSTRIES, LTD.'")
_IHI = ("WITHHELD_RIGHTS", "IHI journal in AIREX: protected by copyright unless otherwise indicated")
_ESAR = ("WITHHELD_RIGHTS", "ESA web page: personal non-commercial use only, no redistribution")
_IAFR = ("WITHHELD_RIGHTS", "IAF abstract page: '(c) IAF ... all rights reserved'")
_BIT = ("WITHHELD_RIGHTS", "journal page: 'Copyright (c) Beijing Institute of Technology Press'")
_RICE_TABLE = ("OWNER_DECISION_REQUIRED",
               "printed in the Vulcain table whose thrust is in the open epoch conflict CF-DB05-VULCAIN-THRUST "
               "(PARTIALLY_RESOLVED); a table-mate of a withheld rating ships only on the owner's release")
_RICE_NUMBER = (_RICE_TABLE[0], _RICE_TABLE[1] + "; and a number: " + _SECONDHAND)

NOT_PROMOTED = {
    # LE-7: the review's engine table (p.18), and the agency's restricted pages
    "AS-DB05-JP-LE-7-004": ("DUPLICATE", "the cycle again, in the p.18 table held by CF-DB05-LE7-EPOCH; "
                                         "AS-DB05-JP-LE-7-003 (p.16) carries it"),
    "AS-DB05-JP-LE-7-005": ("DUPLICATE", "the oxidizer again (p.18 table); AS-DB05-JP-LE-7-001 carries it"),
    "AS-DB05-JP-LE-7-006": ("DUPLICATE", "the fuel again (p.18 table); AS-DB05-JP-LE-7-002 carries it"),
    "AS-DB05-JP-LE-7-007": ("WITHHELD_CONFLICT", "265,000 lbf vac in UNRESOLVED CF-DB05-LE7-EPOCH; " + _SECONDHAND),
    "AS-DB05-JP-LE-7-008": ("OWNER_DECISION_REQUIRED", "table-mate of the withheld rating (CF-DB05-LE7-EPOCH); "
                                                       "direction (O/F or F/O) not printed; " + _SECONDHAND),
    "AS-DB05-JP-LE-7-009": ("WITHHELD_CONFLICT", "451 sec in UNRESOLVED CF-DB05-LE7-EPOCH; environment not printed"),
    "AS-DB05-JP-LE-7-010": ("OWNER_DECISION_REQUIRED", "table-mate of the withheld rating; station not printed; "
                                                       + _SECONDHAND),
    "AS-DB05-JP-LE-7-011": ("OWNER_DECISION_REQUIRED", "table-mate of the withheld rating; " + _SECONDHAND),
    "AS-DB05-JP-LE-7-012": ("OWNER_DECISION_REQUIRED", "table-mate of the withheld rating; " + _SECONDHAND),
    "AS-DB05-JP-LE-7-013": ("OWNER_DECISION_REQUIRED", "table-mate of the withheld rating; definition of the weight "
                                                       "not printed; " + _SECONDHAND),
    "AS-DB05-JP-LE-7-014": ("OWNER_DECISION_REQUIRED", "the p.18 table's status line; table-mate of the withheld "
                                                       "rating"),
    **{f"AS-DB05-JP-LE-7-0{i}": _MEXT for i in range(15, 23)},
    "AS-DB05-JP-LE-7-023": ("WITHHELD_RIGHTS", "JAXA web page: '(c) 2003 Japan Aerospace Exploration Agency'"),
    # LE-7A: NASDA (MEXT-hosted), JAXA and MHI
    **{f"AS-DB05-JP-LE-7A-0{i:02d}": _MEXT for i in range(1, 12)},
    **{f"AS-DB05-JP-LE-7A-0{i:02d}": _JAXA17 for i in range(12, 22)},
    **{f"AS-DB05-JP-LE-7A-0{i:02d}": _MHI for i in range(22, 27)},
    # LE-9: JAXA, IAF, IHI and MHI
    **{f"AS-DB05-JP-LE-9-0{i:02d}": _JAXA17 for i in range(1, 13)},
    "AS-DB05-JP-LE-9-013": _IAFR, "AS-DB05-JP-LE-9-014": _IAFR,
    "AS-DB05-JP-LE-9-015": _IHI, "AS-DB05-JP-LE-9-016": _IHI,
    **{f"AS-DB05-JP-LE-9-0{i:02d}": _MHI for i in range(17, 23)},
    # Vulcain: the 1990 briefing's table (held by an open epoch conflict) and ESA's restricted page
    "AS-DB05-FR-VULCAIN-001": _RICE_TABLE, "AS-DB05-FR-VULCAIN-002": _RICE_TABLE,
    "AS-DB05-FR-VULCAIN-003": _RICE_TABLE, "AS-DB05-FR-VULCAIN-004": _RICE_TABLE,
    "AS-DB05-FR-VULCAIN-005": ("WITHHELD_CONFLICT", "1025 kN in PARTIALLY_RESOLVED CF-DB05-VULCAIN-THRUST "
                                                    "(pre-growth June 1990 figure); " + _SECONDHAND),
    "AS-DB05-FR-VULCAIN-006": _RICE_NUMBER, "AS-DB05-FR-VULCAIN-007": _RICE_NUMBER,
    "AS-DB05-FR-VULCAIN-008": _RICE_NUMBER, "AS-DB05-FR-VULCAIN-009": _RICE_NUMBER,
    **{f"AS-DB05-FR-VULCAIN-0{i}": ("WITHHELD_CONFLICT", "turbine speed or power in UNRESOLVED "
                                                         "CF-DB05-VULCAIN-TURBOPUMPS; " + _SECONDHAND)
       for i in range(10, 14)},
    "AS-DB05-FR-VULCAIN-014": ("MISSING_REQUIRED_SEMANTICS", "presented in June 1990, its July and December 1990 "
                                                             "'1st ignition' and '1st full power firing' are a "
                                                             "schedule, not a record"),
    "AS-DB05-FR-VULCAIN-015": ("NOT_NEEDED", "a programme statement ('performance improvements underway'); no "
                                             "Vulcain configuration ships for it to describe"),
    **{f"AS-DB05-FR-VULCAIN-0{i}": _ESAR for i in range(16, 21)},
    "AS-DB05-FR-VULCAIN-2-001": _ESAR, "AS-DB05-FR-VULCAIN-2-002": _ESAR,
    # Vinci: ESA and IAF
    "AS-DB05-FR-VINCI-001": _ESAR, "AS-DB05-FR-VINCI-002": _ESAR, "AS-DB05-FR-VINCI-003": _ESAR,
    "AS-DB05-FR-VINCI-004": _ESAR,
    "AS-DB05-FR-VINCI-005": _IAFR, "AS-DB05-FR-VINCI-006": _IAFR, "AS-DB05-FR-VINCI-007": _IAFR,
    # China: IAF abstracts and the BIT Press journal
    "AS-DB05-CN-YF-75-001": _IAFR, "AS-DB05-CN-YF-75D-001": _IAFR,
    **{f"AS-DB05-CN-YF-77-00{i}": _IAFR for i in range(1, 8)},
    "AS-DB05-CN-YF-100-001": _IAFR, "AS-DB05-CN-YF-100-002": _IAFR, "AS-DB05-CN-YF-100-003": _IAFR,
    "AS-DB05-CN-YF-100-004": _BIT, "AS-DB05-CN-YF-100-005": _BIT,
}

# ------------------------------------------------------------------ research conflicts (none is decided by owner)

RESEARCH_CONFLICTS = {
    "CF-DB05-LE7-EPOCH": dict(decision="WITHHOLD",
        withhold=("AS-DB05-JP-LE-7-007", "AS-DB05-JP-LE-7-008", "AS-DB05-JP-LE-7-009", "AS-DB05-JP-LE-7-010",
                  "AS-DB05-JP-LE-7-011", "AS-DB05-JP-LE-7-012", "AS-DB05-JP-LE-7-013", "AS-DB05-JP-LE-7-014",
                  "AS-DB05-JP-LE-7-015", "AS-DB05-JP-LE-7-016", "AS-DB05-JP-LE-7-017", "AS-DB05-JP-LE-7-023"),
        argument="UNRESOLVED: a June 1990 development summary against NASDA's 1997 table and JAXA's page; no "
                 "opened document records what changed. Its table-mates wait for the owner."),
    "CF-DB05-LE7A-EPOCH": dict(decision="WITHHOLD",
        withhold=("AS-DB05-JP-LE-7A-003", "AS-DB05-JP-LE-7A-006", "AS-DB05-JP-LE-7A-010", "AS-DB05-JP-LE-7A-013",
                  "AS-DB05-JP-LE-7A-014", "AS-DB05-JP-LE-7A-016", "AS-DB05-JP-LE-7A-023", "AS-DB05-JP-LE-7A-024",
                  "AS-DB05-JP-LE-7A-026"),
        argument="UNRESOLVED: development-era (1997) and flying-engine (2017, manufacturer) figures; every source is "
                 "restricted anyway."),
    "CF-DB05-LE9-THRUST-LEVEL": dict(decision="CARRIED_NOT", touches=(), competing={},
        argument="EXPLAINED: '1 500 kN level' is a class statement; nothing of LE-9 ships (rights)."),
    "CF-DB05-VULCAIN-THRUST": dict(decision="WITHHOLD",
        withhold=("AS-DB05-FR-VULCAIN-001", "AS-DB05-FR-VULCAIN-002", "AS-DB05-FR-VULCAIN-003",
                  "AS-DB05-FR-VULCAIN-004", "AS-DB05-FR-VULCAIN-005", "AS-DB05-FR-VULCAIN-006",
                  "AS-DB05-FR-VULCAIN-007", "AS-DB05-FR-VULCAIN-008", "AS-DB05-FR-VULCAIN-009",
                  "AS-DB05-FR-VULCAIN-016"),
        argument="PARTIALLY_RESOLVED: the June 1990 briefing says thrust growth was under way; the flown value is "
                 "known only from ESA's restricted page. The briefing table's other statements wait for the owner."),
    "CF-DB05-VULCAIN-TURBOPUMPS": dict(decision="WITHHOLD",
        withhold=("AS-DB05-FR-VULCAIN-001", "AS-DB05-FR-VULCAIN-003", "AS-DB05-FR-VULCAIN-004",
                  "AS-DB05-FR-VULCAIN-010", "AS-DB05-FR-VULCAIN-011", "AS-DB05-FR-VULCAIN-012",
                  "AS-DB05-FR-VULCAIN-013", "AS-DB05-FR-VULCAIN-017", "AS-DB05-FR-VULCAIN-018",
                  "AS-DB05-FR-VULCAIN-019"),
        argument="UNRESOLVED: development-era and later figures differ; epoch or rounding not established. The "
                 "number matcher also ties the briefing's 'LH2' statements and ESA's dimensions to these claims; "
                 "all are withheld anyway."),
    "CF-DB05-VINCI-EPOCH": dict(decision="WITHHOLD",
        withhold=("AS-DB05-FR-VINCI-002", "AS-DB05-FR-VINCI-004"),
        argument="PARTIALLY_RESOLVED in DB-0.5: NASA's 2011 table puts 180 kN in vacuum; the 2005 18 t stays unexplained. "
                 "Neither ESA figure is shippable (rights)."),
    # DB-0 conflict backlog pass (2026-10-28)
    "CF-DB05-LE9-ISP": dict(decision="CARRIED_NOT", touches=(), competing={"SRC-WIKI-LE9 426 s / 432 s": "search result, never opened"},
        argument="RESOLVED: JAXA, MHI and IAC print 425 s; nothing of LE-9 ships (rights)."),
    "CF-DB05-VULCAIN-MASS": dict(decision="WITHHOLD",
        withhold=("AS-DB05-FR-VULCAIN-009", "AS-DB05-FR-VULCAIN-017", "AS-DB05-FR-VULCAIN-018"),
        argument="UNRESOLVED: 1990 development mass against ESA's later page, both for the first Vulcain (the "
                 "matcher also ties ESA's LOX pump line, '3 MW'); neither "
                 "shippable anyway."),
    "CF-DB05-VINCI-IGNITIONS": dict(decision="WITHHOLD", withhold=("AS-DB05-FR-VINCI-003",),
        argument="PARTIALLY_RESOLVED: four ignitions (ESA 2024) against an earlier untranscribed 'five'; ESA page "
                 "withheld for rights anyway."),
    "CF-DB05-W-R2_ASIA-R2A-5": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED in DB-0.5: fan page only; the IHI pump label is illegible; nothing of LE-9 ships."),
    "CF-DB05-W-R2_ASIA-R2A-14": dict(decision="WITHHOLD", withhold=(),
        argument="UNRESOLVED in DB-0.5: the cited article gave no text; no YF-100 throttle range ships."),
    "CF-DB05-W-R2_ASIA-R2A-15": dict(decision="CARRIED_NOT", touches=(), competing={},
        argument="RESOLVED in DB-0.5: the developing institute's 2021 paper prints 1 200 kN sea level; no YF-100 "
                 "sea-level thrust assertion exists, so nothing ships."),
    "CF-DB05-W-ASIA_OTHER-10": dict(decision="WITHHOLD", withhold=(),
        argument="UNRESOLVED in DB-0.5: two encyclopedia renderings; no YF-75D value ships."),
    "CF-DB05-W-ASIA_OTHER-11": dict(decision="WITHHOLD", withhold=(),
        argument="UNRESOLVED in DB-0.5: two encyclopedia renderings; no YF-77 Isp ships."),
    "CF-DB05-W-R2_ASIA-R2A-20": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED in DB-0.5: ESA's 2000 table gives 320 kg/s, matching neither claim; no "
                 "Vulcain 2 flow ships."),
    "CF-DB05-W-ANCHOR_EU_ASIA-1": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED in DB-0.5: Arianespace's user's manual prints 1,390 kN maximum vacuum against "
                 "secondary 1,359 kN; no manufacturer datasheet reached, and no Vulcain 2 thrust ships."),
    "CF-DB05-W-ANCHOR_EU_ASIA-4": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED in DB-0.5: ESA's 2000 Bulletin gives 44.9 kg/s H2, matching neither claim; no "
                 "Vulcain 2 flow ships."),
    # DB-0 conflict encyclopedia pass (2026-10-28)
    "CF-DB05-E-R2_ASIA-R2A-2": dict(decision="CARRIED_NOT", touches=(),
        competing={"AS-DB05-JP-LE-7A-018": "JAXA 2017 12.3MPa; the LE-7A is not carried (only the LE-7 ships)"},
        argument="RESOLVED in DB-0.5: JAXA, MHI and a 2010 JAXA engine firing print 12.3 MPa; 12.0 MPa and 121 bar are "
                 "secondary values. No LE-7A value ships."),
    "CF-DB05-E-ASIA_OTHER-1": dict(decision="CARRIED_NOT", touches=(),
        competing={"AS-DB05-JP-LE-7A-018": "JAXA 2017 12.3MPa; the LE-7A is not carried (only the LE-7 ships)"},
        argument="RESOLVED in DB-0.5: same claims as CF-DB05-E-R2_ASIA-R2A-2. No LE-7A value ships."),
    "CF-DB05-E-R2_ASIA-R2A-3": dict(decision="CARRIED_NOT", touches=(), competing={},
        argument="EXPLAINED in DB-0.5: two revisions of one encyclopedia article; nothing ships from these sources."),
    "CF-DB05-E-ASIA_OTHER-3": dict(decision="CARRIED_NOT", touches=(), competing={},
        argument="EXPLAINED in DB-0.5: two revisions of one encyclopedia article; nothing ships from these sources."),
    "CF-DB05-E-R2_ASIA-R2A-13": dict(decision="WITHHOLD", withhold=(),
        argument="UNRESOLVED in DB-0.5: infobox against prose of one encyclopedia article; nothing ships from these sources."),
    "CF-DB05-E-EUROPE-3": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED in DB-0.5: NASA's 2011 table prints 301,243 lbf (1,340 kN); 1,359 kN has no primary. "
                 "Nothing ships from these sources."),
    "CF-DB05-E-EUROPE-4": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED in DB-0.5: ESA's 2000 table prints 115 bar; 117.3 bar has no primary. Nothing ships."),
    "CF-DB05-E-ANCHOR_EU_ASIA-2": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED in DB-0.5: ESA's 2000 table prints 115 bar; 117.3 bar has no primary. Nothing ships."),
    "CF-DB05-E-ANCHOR_EU_ASIA-3": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED in DB-0.5: ESA's 2000 table prints section ratio 58.5; 58.2 has no primary. "
                 "Nothing ships."),
}

CARRIER_GENERALISATIONS = {}
SCHEMATICS = {}
TOPOLOGIES = ()

# ------------------------------------------------------------------ owner decisions (2026-10-12), as written

#: No conflict decision is made by the owner: nothing is released or carried.
OWNER_DECISIONS = {}

OWNER_REVIEWS = {
    "WAVE3-MEXT-NASDA-1997": dict(
        decision="owner (Cemil Eray), 2026-10-12: MEXT-hosted NASDA 1997 source: DO NOT CLEAR FOR SHIPPING. Keep the "
                 "current rights-review-required / non-shippable status. MEXT hosting is not sufficient evidence of "
                 "redistribution permission. Do not ship its values, tables or figures without explicit rights "
                 "evidence.",
        sources=()),
    "WAVE3-1990-TABLE-MATES": dict(
        decision="owner (Cemil Eray), 2026-10-12: Vulcain and LE-7 1990 review table-mate values: KEEP WITHHELD. Do "
                 "not add owner_released. Their position beside conflicted rows does not justify production "
                 "admission, and the 1990 review sources remain secondary evidence.",
        sources=()),
    "WAVE3-1990-SECONDARY-VALUES": dict(
        decision="owner (Cemil Eray), 2026-10-12: 1990 secondary performance values: KEEP WITHHELD FROM PRODUCTION "
                 "PERFORMANCE. Preserve them in research with their provenance/conflicts. Apply the same conservative "
                 "precedent used for RD-170 secondary values.",
        sources=()),
    "WAVE3-NTRS-RIGHTS": dict(
        decision="owner (Cemil Eray), 2026-10-12: New NTRS source rights reading: ACCEPT as Owner-reviewed "
                 "2026-10-12. This is a RocketForge shipping-policy review, not a legal determination. Preserve source "
                 "tier, authority, printed notices and all per-content policies. Do not upgrade secondary evidence to "
                 "primary/manufacturer evidence.",
        sources=("SRC-DB05-NTRS-19910018905",)),
}
