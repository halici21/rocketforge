"""DB-2B Wave 5 promotion manifest: the rest of the DB-0.5 backlog, decided entry by entry.

Read with the DB-2A and earlier DB-2B manifests: the promotion script merges them into one production corpus and
applies the same gates to every entry. Every DB-0.5 assertion of a Wave 5 engine is either promoted below or listed
in ``NOT_PROMOTED`` with a disposition from the existing vocabulary and a reason.

One configuration ships: the RS-68 of Rocketdyne's 1999 slides, as a performance baseline before first flight. The
other nine engines ship nothing and have no production identity. Their figures are a proposed engine's, or sit on
pages with a copyright notice and no reuse licence, or have no source of their own, or sit in an open conflict.

The owner's decisions of 2026-11-06 are recorded as text. ``OWNER_REVIEWS`` accepts the RS-68 slides' rights reading
and keeps the NK-33 slides withheld. ``OWNER_DECISIONS`` ships the two RS-68 values the conflict CF-DB05-E-US_HIST-04
would otherwise hold. No gate was added or loosened.
"""

from __future__ import annotations

from db2a_manifest import P

_NASA95, _NASA01, _FACT = "SRC-DB05-NTRS-19950013232", "SRC-DB05-NTRS-20010067310", "SRC-SFN-RD180-2000"

SEED_ENGINES = ("ENG-US-RS-68", "ENG-RU-RD-180", "ENG-RU-RD-171M", "ENG-SU-NK-33", "ENG-SU-RD-0120", "ENG-US-H-1",
                "ENG-US-LR87-AJ-5", "ENG-US-LR87-AJ-7", "ENG-US-LR91-AJ-5", "ENG-US-SSME-FPL-PHASE-I")
ACCOUNTED_ENGINES = SEED_ENGINES

_R68 = "CFG-RS68-1999-BASELINE"
_R68OP = "OP-RS68-1999-RATED"
_M99 = "SRC-DB05-NTRS-20000025317"

SEED_SUBJECTS = {
    "ENG-US-RS-68": ("FAM-RS68", "VAR-RS-68", _R68),
    # nothing of these ships, so they have no production identity
    **{e: () for e in SEED_ENGINES if e != "ENG-US-RS-68"},
}

#: Each configuration takes values only from the document that describes it.
CONFIGURATION_SOURCES = {_R68: (_M99,)}

# ------------------------------------------------------------------ sources

#: Appended to the rights reading under the owner's review (OWNER_REVIEWS["WAVE5-RS68-RIGHTS"]).
_OWNER_REVIEWED = " Owner-reviewed 2026-11-06 (a RocketForge shipping-policy review, not a legal determination)."

SOURCES = {
    _M99: dict(
        organization="Rocketdyne Propulsion & Power, The Boeing Company", authors=("Terry Murphy",),
        title="Liquid Rocket Propulsion: RS-68 & Linear Aerospike", year=1999,
        identifiers={"NTRS": "20000025317"}, source_type="conference presentation", authority="B", primacy="PRIMARY",
        host="GOV_PUBLIC_USE_PERMITTED", printed="no copyright notice on pages read (all 64 slides viewed 2026-11-06)",
        review="CONSISTENT", figures="VALUES_WITH_ATTRIBUTION",
        review_note="NTRS government public use, not export controlled; the maker's slides for the 50th IAF Congress, "
                    "with the company's logo and no notice on them." + _OWNER_REVIEWED),
}

WITHHELD_SOURCES = {}
WITHHELD_CONTENT_TERMS = {}

# ------------------------------------------------------------------ identity

FAMILIES = ()

VARIANTS = (
    ("VAR-RS-68", "FAM-RS68", "RS-68", "Not the RS-68A, which is filed separately."),
)

CONFIGURATIONS = (
    (_R68, "VAR-RS-68", "RS-68, performance baseline in Rocketdyne's 1999 slides",
     "The 'RS-68 Engine Performance Baseline' slide, October 1999, before first flight",
     "The maker's baseline before first flight, not the flown rating. The Isp is printed as an average. The mixture "
     "ratio is withheld: 'Engine mixture ratio 6.0' prints no direction."),
)

OPERATING_POINTS = (
    (_R68OP, _R68, "Rated", "The 'Rated' column of the 'RS-68 Engine Performance Baseline' slide."),
)
UNITS = ()
ALIASES = ()

# ------------------------------------------------------------------ assertions

_RATED = "the slide's 'Rated' column"

ASSERTIONS = (
    P("AS-DB05-US-RS-68-001", _R68, "performance.thrust_vac", ("number", 745), "RATED", op=_R68OP,
      op_basis=f"AS-DB05-US-RS-68-003 ({_RATED})", cond=dict(environment="VACUUM")),
    P("AS-DB05-US-RS-68-002", _R68, "performance.thrust_sl", ("number", 650), "RATED", op=_R68OP,
      op_basis=f"AS-DB05-US-RS-68-001 ({_RATED})", cond=dict(environment="SEA_LEVEL"),
      note="In research conflict CF-DB05-E-US_HIST-04 (PARTIALLY_RESOLVED); shipped for this configuration only, by "
           "owner decision, as the 1999 baseline and not the flown rating."),
    P("AS-DB05-US-RS-68-003", _R68, "performance.chamber_pressure", ("number", 1410), "RATED", op=_R68OP,
      op_basis=f"AS-DB05-US-RS-68-001 ({_RATED})", cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN"),
      note="The station is not printed. In research conflict CF-DB05-E-US_HIST-04 (PARTIALLY_RESOLVED); shipped for "
           "this configuration only, by owner decision, as the 1999 baseline and not the flown rating."),
    P("AS-DB05-US-RS-68-005", _R68, "performance.specific_impulse_vac", ("number", 410), "AVERAGE", op=_R68OP,
      op_basis=f"AS-DB05-US-RS-68-001 ({_RATED})", cond=dict(environment="VACUUM", isp_basis="UNKNOWN"),
      reading="Printed '410 Avg'", note="Engine or thrust-chamber basis not stated."),
    P("AS-DB05-US-RS-68-006", _R68, "nozzle.area_ratio", ("number", 21.5), "NOMINAL"),
    P("AS-DB05-US-RS-68-007", _R68, "mechanical.mass", ("text",), "OTHER",
      note="An upper bound as printed ('< 15,000'), with no definition of the weight. It is not an engine mass."),
)

FIELD_RENAMES = {}
OPERATING_POINT_MAP = {}
CONFIGURATION_MAP = {("ENG-US-RS-68", "RS-68 baseline (1999, before first flight)"): _R68}

# ------------------------------------------------------------------ not promoted

_US = "AS-DB05-US-"
_RD180, _RD171, _NK33, _RD0120 = "AS-DB05-RU-RD-180-", "AS-DB05-RU-RD-171M-", "AS-DB05-SU-NK-33-", "AS-DB05-SU-RD-0120-"

_PROPOSED = ("WRONG_CONFIGURATION", "MSFC's 1995 study of a proposed engine, written before the RD-180 existed; its "
                                    "figures are not the built engine's")
_2001 = ("WITHHELD_CONFLICT", "an unsourced bullet list in a 2001 test paper, in an open RD-180 conflict")
_SFN = ("WITHHELD_RIGHTS", "Spaceflight Now page: site copyright, no reuse licence")
_GLAV = ("WITHHELD_RIGHTS", "Glavkosmos page: terms of use, no reuse licence")

NOT_PROMOTED = {
    f"{_US}RS-68-004": ("MISSING_REQUIRED_SEMANTICS", "printed 'Engine mixture ratio 6.0' without a direction (O/F or "
                                                      "F/O); deriving it is not print"),
    **{f"{_RD180}{i:03d}": _PROPOSED for i in range(1, 9)},
    **{f"{_RD180}{i:03d}": _2001 for i in range(9, 12)},
    **{f"{_RD180}{i:03d}": _SFN for i in range(12, 21)},
    **{f"{_RD180}{i:03d}": _GLAV for i in range(21, 26)},
    f"{_RD180}026": ("WITHHELD_RIGHTS", "news site under its copyright; a certification margin, not a rating"),
    f"{_RD171}001": _GLAV,
    f"{_RD171}002": _GLAV,
    f"{_RD171}003": ("WITHHELD_RIGHTS", "IAF archive abstract: metadata only, the paper was not opened"),
    **{f"{_NK33}{i:03d}": ("WITHHELD_RIGHTS", "Aerojet slides on a National Academies page; the owner kept them "
                                              "withheld (2026-11-06)") for i in range(1, 10)},
    f"{_RD0120}001": ("WITHHELD_RIGHTS", "enthusiast page: 'All Rights Reserved'"),
    f"{_RD0120}002": ("WITHHELD_RIGHTS", "RussianSpaceWeb page under its author's copyright"),
    **{f"{_US}H-1-{i:03d}": ("DISCOVERY_ONLY_SOURCE", "a Purdue table with no source, rating name or date; it names "
                                                      "no H-1 configuration") for i in range(1, 7)},
    f"{_US}LR87-AJ-5-001": ("WITHHELD_RIGHTS", "hobby site, an unattributed transcription with no licence"),
    f"{_US}LR87-AJ-5-002": ("WITHHELD_RIGHTS", "Encyclopedia Astronautica: its copyright, no reuse licence"),
    f"{_US}LR87-AJ-7-001": ("WITHHELD_RIGHTS", "Encyclopedia Astronautica: its copyright, no reuse licence"),
    f"{_US}LR91-AJ-5-001": ("WITHHELD_RIGHTS", "hobby site, an unattributed transcription with no licence"),
    **{f"{_US}SSME-FPL-PHASE-I-{i:03d}": ("WITHHELD_RIGHTS", "Biggs 1992: printed AAS copyright, reprinted with "
                                                             "permission") for i in range(1, 6)},
}

# ------------------------------------------------------------------ owner decisions (2026-11-06)

_R68_EPOCH = ("owner (Cemil Eray), 2026-11-06: ship RS-68 sea-level thrust 650 klbf and chamber pressure 1410 psia for "
              "CFG-RS68-1999-BASELINE only, as the 1999 rated baseline before first flight; measurement station "
              "UNKNOWN. The throttled column (836 psia) is not admitted. The research conflict stays "
              "PARTIALLY_RESOLVED.")

OWNER_DECISIONS = {"CF-DB05-E-US_HIST-04": _R68_EPOCH}

OWNER_REVIEWS = {
    "WAVE5-RS68-RIGHTS": dict(
        decision="owner (Cemil Eray), 2026-11-06: RS-68 1999 slides' rights reading: ACCEPT as Owner-reviewed "
                 "2026-11-06. This is a RocketForge shipping-policy review, not a legal determination. It changes no "
                 "source tier.",
        sources=(_M99,)),
    "2026-11-06-NK33-RIGHTS": dict(
        decision="owner (Cemil Eray), 2026-11-06: NK-33 Aerojet slides: KEEP WITHHELD. A company presentation on a "
                 "National Academies page carries no government public-use determination.",
        sources=()),
}

# ------------------------------------------------------------------ research conflicts


def _rd180(*numbers):
    return tuple(f"{_RD180}{i:03d}" for i in numbers)


RESEARCH_CONFLICTS = {
    "CF-DB05-E-US_HIST-04": dict(decision="CARRIED_NOT", touches=(f"{_US}RS-68-002", f"{_US}RS-68-003"),
        owner_accepted=_R68_EPOCH, owner_scope=_R68,
        competing={"SRC-WIKI-RS68 663,000 lbf and 660,000 lbf": "encyclopedia, a later rating with no primary opened",
                   "SRC-L3H-RS68A-DS 1580 psia": "the RS-68A, not the RS-68"},
        argument="PARTIALLY_RESOLVED in DB-0.5: the 1999 baseline against later figures. Shipped for this "
                 "configuration only, by owner decision."),
    "CF-DB05-RD180-PC": dict(decision="WITHHOLD", withhold=_rd180(5, 9, 16, 23, 26),
        argument="PARTIALLY_RESOLVED: the maker's value is on pages this corpus cannot ship; 3,734 psia is unexplained."),
    "CF-DB05-RD180-MASS": dict(decision="WITHHOLD", withhold=_rd180(8, 11, 20, 24),
        argument="UNRESOLVED: which mass belongs to which build or scope is not stated."),
    "CF-DB05-RD180-THROTTLE": dict(decision="WITHHOLD", withhold=_rd180(7, 10, 19, 25),
        argument="UNRESOLVED: three floors, none said to be qualified, demonstrated or a flight limit."),
    "CF-DB05-RD180-MR": dict(decision="WITHHOLD", withhold=_rd180(6, 18),
        argument="EXPLAINED in DB-0.5, but neither side's source ships."),
    "CF-DB05-RD180-THRUST": dict(decision="WITHHOLD", withhold=_rd180(1, 2, 12, 13, 21),
        argument="EXPLAINED in DB-0.5, but neither side's source ships."),
    "CF-DB05-RD180-AREA-RATIO": dict(decision="WITHHOLD", withhold=_rd180(17),
        argument="UNRESOLVED: no second maker value."),
    "CF-DB05-RD171M-PC": dict(decision="WITHHOLD", withhold=(f"{_RD171}001", f"{_RD171}003"),
        argument="EXPLAINED in DB-0.5, but neither side's source ships."),
    "CF-DB05-RD171M-MASS": dict(decision="WITHHOLD", withhold=(f"{_RD171}002",),
        argument="PARTIALLY_RESOLVED; the source does not ship."),
    "CF-DB05-NK33-PC-THRUST": dict(decision="WITHHOLD", withhold=(f"{_NK33}001", f"{_NK33}002", f"{_NK33}005"),
        argument="PARTIALLY_RESOLVED; the owner kept the source withheld."),
    "CF-DB05-RD0120-THRUST-GIMBAL": dict(decision="WITHHOLD", withhold=(f"{_RD0120}001", f"{_RD0120}002"),
        argument="PARTIALLY_RESOLVED; neither source ships."),
    "CF-DB05-H1-THRUST": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED; nothing of this engine ships."),
    "CF-DB05-H1-ISP-MASS": dict(decision="WITHHOLD", withhold=(f"{_US}H-1-001", f"{_US}H-1-002", f"{_US}H-1-003"),
        argument="PARTIALLY_RESOLVED; the source names no configuration."),
    "CF-DB05-LR87-GIMBAL": dict(decision="WITHHOLD", withhold=(f"{_US}LR87-AJ-5-001",),
        argument="EXPLAINED in DB-0.5, but the source does not ship."),
    "CF-DB05-LR87-7-PC": dict(decision="WITHHOLD", withhold=(f"{_US}LR87-AJ-7-001",),
        argument="PARTIALLY_RESOLVED; the source does not ship."),
    "CF-DB05-W-R2_US_CLASSIC-LR-2": dict(decision="WITHHOLD", withhold=(),
        argument="EXPLAINED in DB-0.5; nothing of this engine ships."),
    "CF-DB05-W-R2_USSR-R2-5": dict(decision="WITHHOLD", withhold=(),
        argument="CONFIRMED_SECONDARY; nothing of this engine ships."),
    "CF-DB05-E-R2_USSR-R2-6": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED; nothing of this engine ships."),
    "CF-DB05-E-USSR-12": dict(decision="WITHHOLD", withhold=(),
        argument="PARTIALLY_RESOLVED; nothing of this engine ships."),
}
