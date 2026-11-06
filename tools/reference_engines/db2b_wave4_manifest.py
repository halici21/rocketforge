"""DB-2B Wave 4 promotion manifest: US design and test documents opened after Wave 3, decided entry by entry.

Read with the DB-2A and earlier DB-2B manifests: the promotion script merges them into one production corpus and
applies the same gates to every entry. Every DB-0.5 assertion of a Wave 4 engine is either promoted below or listed
in ``NOT_PROMOTED`` with a disposition from the existing vocabulary and a reason.

Targets: RL10A-3-3, LR91AJ-11, H-1 at the 200K rating, and F-1A. Each is one source's description of one engine,
not a flight record: the RL10A-3-3 values are Pratt & Whitney's 1966 design estimates, the H-1 values are the
average engine of one stage's logs, and the F-1A values are NASA MSFC's 2013 comparison slide.

No gate was added or loosened. The owner's decisions of 2026-11-06 are recorded as text in ``OWNER_REVIEWS``. None of
them releases a value: ``OWNER_DECISIONS`` stays empty here. The RL10A-3-3 chamber pressures stay withheld by the open
conflict CF-DB05-RL10A33-PC: the owner chose to ship two of them at their printed stations, and the frozen station gate
recognises only nozzle stagnation.
"""

from __future__ import annotations

from db2a_manifest import P

SEED_ENGINES = ("ENG-US-RL10A-3-3", "ENG-US-LR91-AJ-11", "ENG-US-H-1-200K", "ENG-US-F-1A")
ACCOUNTED_ENGINES = SEED_ENGINES

_RL, _RLOP = "CFG-RL10A-3-3-FR1769", "OP-RL10A-3-3-FR1769-OF5"
_LR = "CFG-LR91-AJ-11-T3E"
_H200 = "CFG-H1-200K-S-IB-4"
_F1A = "CFG-F1A-MSFC-2013"

SEED_SUBJECTS = {
    "ENG-US-RL10A-3-3": ("FAM-RL10", "VAR-RL10A-3-3", _RL),
    "ENG-US-LR91-AJ-11": ("FAM-LR91", "VAR-LR91-AJ-11", _LR),
    "ENG-US-H-1-200K": ("FAM-H1", "VAR-H1-200K", _H200),
    "ENG-US-F-1A": ("FAM-F1", "VAR-F1A", _F1A),
}

_FR1769 = "SRC-DB05-NTRS-19670005471"
_TITAN = "SRC-DB05-NTRS-19750004937"
_AS204 = "SRC-DB05-NTRS-19680003903"
_BETTS = "SRC-DB05-NTRS-20140011656"

#: Each configuration takes values only from the document that describes it.
CONFIGURATION_SOURCES = {_RL: (_FR1769,), _LR: (_TITAN,), _H200: (_AS204,), _F1A: (_BETTS,)}

# ------------------------------------------------------------------ sources

_NO_NOTICE = "no copyright notice on pages read (extracted text of every page checked 2026-11-06)"
#: Appended to every Wave 4 rights reading under the owner's review (OWNER_REVIEWS["WAVE4-NTRS-RIGHTS"]).
_OWNER_REVIEWED = " Owner-reviewed 2026-11-06 (a RocketForge shipping-policy review, not a legal determination)."

SOURCES = {
    _FR1769: dict(
        organization="Pratt & Whitney Aircraft", authors=(), title="Design Report for RL10A-3-3 Rocket Engine",
        year=1966, identifiers={"NTRS": "19670005471", "report": "PWA FR-1769", "contract": "NAS8-15494"},
        source_type="contractor report", authority="A", primacy="PRIMARY", host="GOV_PUBLIC_USE_PERMITTED",
        printed=_NO_NOTICE, review="CONSISTENT", figures="VALUES_WITH_ATTRIBUTION",
        review_note="NTRS government public use; no notice on the cover or in the extracted text. The maker's design "
                    "report under a NASA contract: its values are design estimates, not test or flight data." + _OWNER_REVIEWED),
    _AS204: dict(
        organization="Chrysler Corporation Space Division", authors=(),
        title="Final Flight Performance Prediction for Saturn AS-204 LM Propulsion System, S-IB-4 Stage", year=1967,
        identifiers={"NTRS": "19680003903", "report": "TR-P&VE-67-58"}, source_type="contractor report",
        authority="A", primacy="PRIMARY", host="GOV_PUBLIC_USE_PERMITTED", printed=_NO_NOTICE, review="CONSISTENT",
        figures="VALUES_WITH_ATTRIBUTION",
        review_note="NTRS government public use; no restrictive notice on the pages read. The stage contractor's "
                    "report, whose Table 5 summarises Rocketdyne's engine logs." + _OWNER_REVIEWED),
    _BETTS: dict(
        organization="NASA Marshall Space Flight Center", authors=("Betts",),
        title="F-1 engine presentation (NASA MSFC ER21)", year=2013, identifiers={"NTRS": "20140011656"},
        source_type="presentation", authority="A", primacy="SECONDARY", host="GOV_PUBLIC_USE_PERMITTED",
        printed=_NO_NOTICE, review="CONSISTENT", figures="VALUES_WITH_ATTRIBUTION",
        review_note="NTRS government public use; no copyright notice on the slides read. A NASA comparison slide "
                    "that names no underlying document, so it is secondary for the F-1A." + _OWNER_REVIEWED),
}

WITHHELD_SOURCES = {}
WITHHELD_CONTENT_TERMS = {}

# ------------------------------------------------------------------ identity

FAMILIES = (
    ("FAM-LR91", "LR91", "Aerojet Titan second-stage engines; only the LR91AJ-11 is supported by an opened document "
                         "here."),
)

VARIANTS = (
    ("VAR-RL10A-3-3", "FAM-RL10", "RL10A-3-3", "Not the RL10A-3-3A, which is filed separately."),
    ("VAR-LR91-AJ-11", "FAM-LR91", "LR91AJ-11", ""),
    ("VAR-H1-200K", "FAM-H1", "H-1, 200K rating", "Named by its rating; the document prints no separate model name."),
    ("VAR-F1A", "FAM-F1", "F-1A", ""),
)

CONFIGURATIONS = (
    (_RL, "VAR-RL10A-3-3", "RL10A-3-3, as estimated in Pratt & Whitney's design report (PWA FR-1769, 1966)",
     ("MISSING", "NOT_AUDITED", "a design report printed before the engine's service; no flight effectivity is stated"),
     "The maker's estimates at 15,000 lb and mixture ratio 5.0, not test or flight data. The chamber pressures are "
     "withheld by CF-DB05-RL10A33-PC: the introduction's 400 psia names no station against the table's 385.2 and "
     "394.6 psia."),
    (_LR, "VAR-LR91-AJ-11", "LR91AJ-11, Titan IIIE stage II engine (General Dynamics Convair CASD-LVP73-007)",
     "Titan IIIE stage II, as of the September 1973 systems summary",
     "Thrust and Isp include the roll nozzle. No other LR91 variant is carried: none was read from a shippable "
     "document."),
    (_H200, "VAR-H1-200K", "H-1, 200K rating, average engine of Saturn IB stage S-IB-4 (AS-204)",
     "Saturn IB stage S-IB-4, flown on AS-204",
     "An average of eight engines' sea-level logs, not a rating: the 200K rating itself is printed only as an "
     "acceptance band in a report this configuration does not use. Not the 188,000 lb H-1 of SA-10."),
    (_F1A, "VAR-F1A", "F-1A, as NASA MSFC's 2013 comparison slide prints it",
     ("MISSING", "NOT_AUDITED", "the slide names no build, test or date for the F-1A column"),
     "One column of 'Engine Comparison, F-1 vs. F-1A'. The slide does not define the weight, and its 'ns' on chamber "
     "pressure has no legend."),
)

OPERATING_POINTS = (
    (_RLOP, _RL, "15,000 lb, O/F 5.0, 200,000 ft",
     "The point of the report's introduction (15,000 lb at 200,000 ft, oxidizer-to-fuel 5.0:1) and of the 5.0 column "
     "of Table V-1 'Estimated RL10A-3-3 Engine Design Data'."),
)
UNITS = ()
ALIASES = ()

# ------------------------------------------------------------------ assertions

_INTRO = "AS-DB05-US-RL10A-3-3-003 (the introduction's mixture ratio, printed with this value)"
_ESTIMATE = "Table V-1 is headed 'Estimated RL10A-3-3 Engine Design Data'"
_FLOWS = "AS-DB05-US-RL10A-3-3-015 (Table V-1, column 5.0)"
_V2 = "AS-DB05-US-RL10A-3-3-019 (Table V-1 continued, column 5.0)"

ASSERTIONS = (
    # RL10A-3-3: the design report's introduction
    P("AS-DB05-US-RL10A-3-3-001", _RL, "performance.thrust_vac", ("number", 15000), "RATED", op=_RLOP, op_basis=_INTRO,
      cond=dict(environment="UNKNOWN"), note="Printed 'at an altitude of 200,000 ft'; the report does not call it vacuum."),
    P("AS-DB05-US-RL10A-3-3-002", _RL, "performance.specific_impulse", ("number", 444), "NOMINAL", op=_RLOP,
      op_basis=_INTRO, cond=dict(environment="UNKNOWN", isp_basis="UNKNOWN")),
    P("AS-DB05-US-RL10A-3-3-003", _RL, "propellants.mixture_ratio", ("number", 5.0), "NOMINAL", op=_RLOP,
      op_basis="AS-DB05-US-RL10A-3-3-001 (the rated thrust, printed with this value)",
      cond=dict(mixture_ratio_form="OXIDIZER_TO_FUEL", mixture_ratio_basis="UNKNOWN")),
    P("AS-DB05-US-RL10A-3-3-005", _RL, "nozzle.area_ratio", ("number", 57), "NOMINAL"),
    P("AS-DB05-US-RL10A-3-3-006", _RL, "life.starts_and_duration", ("text",), "OTHER"),
    P("AS-DB05-US-RL10A-3-3-007", _RL, "life.spec", ("number", 4000), "DESIGN_VALUE",
      reading="Printed 'shall be': the report's specified service life, not a demonstrated one"),
    P("AS-DB05-US-RL10A-3-3-008", _RL, "architecture.feed", ("enum", "PUMP_FED"), "NOMINAL"),
    P("AS-DB05-US-RL10A-3-3-009", _RL, "cooling.thrust_chamber", ("enum", "REGENERATIVE"), "NOMINAL"),
    # Table IV-1, weights
    P("AS-DB05-US-RL10A-3-3-011", _RL, "mechanical.mass_dry_basic", ("number", 289.79), "MAXIMUM",
      note="A 3-sigma maximum estimate; the specification is 290.00 lb."),
    P("AS-DB05-US-RL10A-3-3-012", _RL, "mechanical.mass", ("number", 301.19), "NOMINAL",
      note="Basic engine plus nonchargeable instrumentation, brackets and nonflight items."),
    # Table V-1, the 5.0 column
    P("AS-DB05-US-RL10A-3-3-015", _RL, "performance.mass_flow_fuel", ("number", 5.63), "DESIGN_VALUE", op=_RLOP,
      op_basis="AS-DB05-US-RL10A-3-3-016 (the same column's oxidizer flow)", reading=_ESTIMATE),
    P("AS-DB05-US-RL10A-3-3-016", _RL, "performance.mass_flow_oxidizer", ("number", 28.16), "DESIGN_VALUE", op=_RLOP,
      op_basis=_FLOWS, reading=_ESTIMATE),
    P("AS-DB05-US-RL10A-3-3-017", _RL, "pumps.fuel.speed_rpm", ("number", 30250), "DESIGN_VALUE", op=_RLOP,
      op_basis=_V2, reading=_ESTIMATE),
    P("AS-DB05-US-RL10A-3-3-018", _RL, "pumps.lox.speed_rpm", ("number", 12100), "DESIGN_VALUE", op=_RLOP,
      op_basis=_FLOWS, reading=_ESTIMATE),
    P("AS-DB05-US-RL10A-3-3-019", _RL, "performance.cstar", ("number", 7626), "DESIGN_VALUE", op=_RLOP,
      op_basis="AS-DB05-US-RL10A-3-3-017 (Table V-1 continued, column 5.0)", reading=_ESTIMATE,
      note="Printed as c* (actual), 98.6 percent of shifting."),
    P("AS-DB05-US-RL10A-3-3-020", _RL, "chamber.throat_diameter", ("number", 5.14), "DESIGN_VALUE", reading=_ESTIMATE),
    P("AS-DB05-US-RL10A-3-3-021", _RL, "chamber.lstar", ("number", 38.7), "DESIGN_VALUE", reading=_ESTIMATE),
    P("AS-DB05-US-RL10A-3-3-022", _RL, "nozzle.area_ratio", ("number", 57.1), "DESIGN_VALUE", reading=_ESTIMATE,
      note="Printed as the effective expansion ratio; the introduction's nominal figure is 57:1."),
    # LR91AJ-11
    P("AS-DB05-US-LR91-AJ-11-003", _LR, "performance.thrust_vac", ("number", 101000), "NOMINAL",
      cond=dict(environment="VACUUM"), note="Printed as including the roll nozzle."),
    P("AS-DB05-US-LR91-AJ-11-004", _LR, "performance.specific_impulse_vac", ("number", 318.7), "NOMINAL",
      cond=dict(environment="VACUUM", isp_basis="UNKNOWN"), note="Printed as including the roll nozzle."),
    P("AS-DB05-US-LR91-AJ-11-005", _LR, "performance.mass_flow_total", ("number", 317), "NOMINAL"),
    P("AS-DB05-US-LR91-AJ-11-006", _LR, "nozzle.area_ratio", ("number", 49.2), "NOMINAL"),
    # H-1, 200K rating: the average engine of Table 5
    P("AS-DB05-US-H-1-200K-002", _H200, "performance.thrust_sl", ("number", 200.53), "AVERAGE",
      cond=dict(environment="SEA_LEVEL"), note="An average of eight engines' logs, not the 200K rating."),
    P("AS-DB05-US-H-1-200K-003", _H200, "performance.specific_impulse_sl", ("number", 262.6), "AVERAGE",
      cond=dict(environment="SEA_LEVEL", isp_basis="UNKNOWN")),
    # F-1A: one column of the comparison slide
    P("AS-DB05-US-F-1A-001", _F1A, "performance.chamber_pressure", ("number", 1161), "NOMINAL",
      cond=dict(pressure_basis="ABSOLUTE", pressure_station="UNKNOWN"),
      note="The slide's 'ns' has no legend, so the station stays unknown."),
    P("AS-DB05-US-F-1A-002", _F1A, "performance.thrust_sl", ("number", 1800000), "NOMINAL",
      cond=dict(environment="SEA_LEVEL")),
    P("AS-DB05-US-F-1A-003", _F1A, "performance.specific_impulse_sl", ("number", 269.7), "NOMINAL",
      cond=dict(environment="SEA_LEVEL", isp_basis="UNKNOWN")),
    P("AS-DB05-US-F-1A-005", _F1A, "nozzle.area_ratio", ("number", 16), "NOMINAL"),
    P("AS-DB05-US-F-1A-006", _F1A, "mechanical.mass", ("number", 19000), "NOMINAL",
      note="The slide does not define the weight (dry, burnout or wet)."),
)

FIELD_RENAMES = {}
OPERATING_POINT_MAP = {}
CONFIGURATION_MAP = {("ENG-US-LR91-AJ-11", "Titan IIIE Stage II (LR91AJ-11)"): _LR}

# ------------------------------------------------------------------ not promoted

_NO_DIRECTION = "without a direction (O/F or F/O); deriving it is not print"
_PC = ("WITHHELD_CONFLICT", "chamber pressure in PARTIALLY_RESOLVED CF-DB05-RL10A33-PC; see OWNER_REVIEWS "
                            "2026-11-06-RL10A33-PC")

NOT_PROMOTED = {
    "AS-DB05-US-RL10A-3-3-004": _PC, "AS-DB05-US-RL10A-3-3-013": _PC, "AS-DB05-US-RL10A-3-3-014": _PC,
    "AS-DB05-US-RL10A-3-3-010": ("INFERRED_ONLY", "the report never prints 'expander': DB-0.5 read the closed cycle "
                                                  "from the function list and the piping list"),
    "AS-DB05-US-LR91-AJ-11-001": ("DISCOVERY_ONLY_SOURCE", "a Purdue table with no source and no rating name; the "
                                                           "systems summary is the document"),
    "AS-DB05-US-LR91-AJ-11-002": ("WITHHELD_CONFLICT", "printed 'Mixture Ratio 1.79' " + _NO_DIRECTION),
    "AS-DB05-US-H-1-200K-001": ("MISSING_REQUIRED_SEMANTICS", "an acceptance band ('within the specified limits of "
                                                              "200K +/- 3 percent') with no environment stated, not "
                                                              "an operating value"),
    "AS-DB05-US-H-1-200K-004": ("MISSING_REQUIRED_SEMANTICS", "printed '2.2168' " + _NO_DIRECTION),
    "AS-DB05-US-F-1A-004": ("MISSING_REQUIRED_SEMANTICS", "printed 'Engine Mixture Ratio 2.27' " + _NO_DIRECTION),
}

# ------------------------------------------------------------------ research conflicts (none is decided by owner)

OWNER_DECISIONS = {}

OWNER_REVIEWS = {
    "2026-11-06-RL10A33-PC": dict(
        decision="owner (Cemil Eray), 2026-11-06: RL10A-3-3 chamber pressure: 385.2 psia (throat total) and 394.6 psia "
                 "(injector face static) are to ship at their own stations for this configuration; 400 psia stays "
                 "withheld. Not shipped yet: the frozen station gate recognises only nozzle stagnation.",
        sources=()),
    "2026-11-06-RS68A-THRUST": dict(
        decision="owner (Cemil Eray), 2026-11-06: RS-68A thrust: the NASA blog's 702,000 lb stays withheld. The ULA "
                 "guide's 705,250 lbf sea-level value goes to Wave 5, subject to that guide's rights reading.",
        sources=()),
    "2026-11-06-F1-MR": dict(
        decision="owner (Cemil Eray), 2026-11-06: F-1 mixture ratio: a direction printed in one document is not carried "
                 "to a value in another. 2.27 stays withheld for CFG-F1.",
        sources=()),
    "2026-11-06-F1-SL-THRUST": dict(
        decision="owner (Cemil Eray), 2026-11-06: F-1 sea-level thrust stays withheld: the documents do not establish "
                 "which flights carried which rating.",
        sources=()),
    "2026-11-06-RS25-PUMPPOWER": dict(
        decision="owner (Cemil Eray), 2026-11-06: RS-25 pump power stays withheld until a document prints its power "
                 "level.",
        sources=()),
    "2026-11-06-LMDE-LM10": dict(
        decision="owner (Cemil Eray), 2026-11-06: LMDE LM-10 area ratio: confirm the decision of 2026-10-28. 54.0:1 stays "
                 "a note and no conflict is filed.",
        sources=()),
    "WAVE4-NTRS-RIGHTS": dict(
        decision="owner (Cemil Eray), 2026-11-06: Rights readings of the three new NTRS sources: ACCEPT as "
                 "Owner-reviewed 2026-11-06. This is a RocketForge shipping-policy review, not a legal determination. "
                 "It releases no withheld value and changes no source tier.",
        sources=(_FR1769, _AS204, _BETTS)),
}

RESEARCH_CONFLICTS = {
    "CF-DB05-RL10A33-PC": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-RL10A-3-3-004", "AS-DB05-US-RL10A-3-3-013", "AS-DB05-US-RL10A-3-3-014"),
        argument="PARTIALLY_RESOLVED: the introduction's 400 psia names no station; Table V-1's 385.2 and 394.6 psia "
                 "name theirs. Which one is the engine's chamber pressure is the owner's call."),
    "CF-DB05-LR91-AJ11-MR": dict(decision="WITHHOLD",
        withhold=("AS-DB05-US-LR91-AJ-11-001", "AS-DB05-US-LR91-AJ-11-002"),
        argument="RESOLVED in DB-0.5 to 1.79, but no document prints the direction, so neither side ships."),
}
