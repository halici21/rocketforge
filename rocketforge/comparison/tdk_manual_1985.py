"""Two engines, as the TDK manual's own samples printed them -- an independent code, no verdict (DB-4C).

The TDK engineering manual (NASA-CR-178628, NTRS 19860007470; G. R. Nickerson,
L. D. Dang and D. E. Coats, Software and Engineering Associates, April 1985)
runs, in its §7.2, the "Pratt and Whitney test engine for RL-10 OTV
propulsion": an expander cycle sized for 15,500 lbf vacuum thrust at 394 psia
and an expansion ratio of 205:1, with input prepared "from data provided by NASA
MSFC". Its first ODE calculation sets "the system enthalpy ... at the propellant
tank values". Table 7-2 (printed p.7-56, PDF p.448) is the input and Table 7-3
(printed p.7-58, PDF p.450) the summary. Both are printed sideways and were read
from pages rendered upright.

This is the manual whose complete three-zone sample (§7.1) settles what a
summary's ISP (ODE) and ISP (ODF) mean: vacuum values, ODF frozen at the chamber
composition (DB-4C §2). Here those conventions come from the same document,
though not from Table 7-3 itself.

Held as :attr:`~.cases.SourceKind.INDEPENDENT_CODE`, imported, as the SSME
printouts in :mod:`.ssme_tdk_1985` are, and for the same reason. The manual says
which data format the program reads, NASA SP-273's THERMO cards, and that
coefficients for many species are supplied with it (§6.1, PDF pp.304-305). It
does not say which data file the sample used.

The engine is an RL10 test engine at area ratio 205, linked to no catalog
configuration.

The manual's §7.3 (printed p.7-59, PDF p.451) runs the second sample, the
"Rocketdyne prototype advanced space engine for OTV propulsion" (the ASE): a
hydrogen expander cycle sized for 22,500 lbf vacuum thrust at 2300 psia and
400:1, again from MSFC data, with "the sequence of calculations ... the same as
given in subsection 7.1". Table 7-4 (PDF pp.454-455) is the input and Table 7-5
(printed p.7-64, PDF p.456) the summary. Table 7-8 (PDF p.459), a second run of
the same engine with the TDE option, prints the same three first-solution
values. A prototype, linked to no catalog configuration (DB-4C §16).

These cases change no engine evidence. NTRS lists the manual as public,
GOV_PUBLIC_USE_PERMITTED, and not export controlled.
"""

from __future__ import annotations

from .cases import CaseOrigin, ReferenceCase, SourceKind
from .tdk_1985 import CODE, CODE_VERSION, EXPANSION, FIRST_SOLUTION, TdkPoint, not_recorded, tdk_quantities

__all__ = [
    "RL10_OTV_CHAMBER_PRESSURE_PSIA",
    "RL10_OTV_OXIDISER_FUEL_RATIO",
    "RL10_OTV_AREA_RATIO",
    "TDK_MANUAL_1985_RL10_OTV",
    "RL10_OTV",
    "ASE_CHAMBER_PRESSURE_PSIA",
    "ASE_OXIDISER_FUEL_RATIO",
    "ASE_AREA_RATIO",
    "TDK_MANUAL_1985_ASE",
    "ASE",
    "POINTS",
]

#: Table 7-2 ``$ODE``: ``RKT=.TRUE., P(1)=394.3, PSIA=.TRUE.``, the stagnation pressure of the rocket problem.
RL10_OTV_CHAMBER_PRESSURE_PSIA = 394.3
#: Table 7-2 ``OFSKED(1)=5.035244``, oxidiser to fuel by mass. Table 7-3 prints 5.035244.
RL10_OTV_OXIDISER_FUEL_RATIO = 5.035244
#: Table 7-2: the ``ASUP`` schedule ends at 205.03. ``EPS=205.03376`` sets the contour's exit and Table 7-3
#: prints EP (NOZZLE) 205.0338; recorded, not used. The ``$ODK`` card is too faded to read beyond "205,".
RL10_OTV_AREA_RATIO = 205.03

#: Table 7-4 ``$ODE``: ``RKT=.TRUE., P(1)=2287, PSIA=.TRUE.``. Table 7-5 prints 2287.000; the text's 2300 psia is
#: the nominal design.
ASE_CHAMBER_PRESSURE_PSIA = 2287.0
#: Table 7-4 ``OFSKED(1)=6.3780``, oxidiser to fuel by mass. Table 7-5 prints 6.378000.
ASE_OXIDISER_FUEL_RATIO = 6.378
#: Table 7-4: the ``ASUP`` schedule ends at 400.7148 and ``$ODK`` sets ``EP=400.7148``. ``EPS=400.7248`` sets the
#: contour's exit and Table 7-5 prints EP (NOZZLE) 400.7248; recorded, not used.
ASE_AREA_RATIO = 400.7148

_CONVENTIONS = "read from the same manual's three-zone sample run (its §7.1), not from Table 7-3"
_ASE_CONVENTIONS = "read from the same manual's three-zone sample run (its §7.1), not from Table 7-5"
_TABLE = "Table 7-3 (printed p.7-58, PDF p.450), first TDK/BLM solution"
_ASE_TABLE = "Table 7-5 (printed p.7-64, PDF p.456), first TDK/BLM solution"
_MANUAL = ("G. R. Nickerson, L. D. Dang and D. E. Coats, 'Engineering and Programming Manual: Two-Dimensional "
           "Kinetic Reference Computer Program (TDK)', NASA-CR-178628, Software and Engineering Associates, "
           "April 1985; NTRS 19860007470")
_DATABASE_VERSION = ("not stated for the sample (the program reads NASA SP-273 THERMO cards and is supplied with "
                     "coefficients for many species, §6.1, PDF pp.304-305; which file the sample used is not said)")

TDK_MANUAL_1985_RL10_OTV = ReferenceCase(
    case_id="tdk-manual-1985-rl10-otv",
    title="RL-10 OTV test engine, TDK manual sample (1985), first solution",
    source_kind=SourceKind.INDEPENDENT_CODE,
    benchmark_class="B",
    source=_MANUAL + ", §7.2, Tables 7-2 and 7-3",
    code=CODE,
    code_version=CODE_VERSION,
    database_version=_DATABASE_VERSION,
    origin=CaseOrigin.IMPORTED,
    inputs={
        "chamber_pressure": "394.3 psia, the stagnation pressure of TDK's rocket problem (Table 7-2)",
        "oxidiser_fuel_ratio": "5.035244 by mass (Table 7-2 OFSKED; Table 7-3 prints 5.035244)",
        "area_ratio": ("205.03 (Table 7-2 ASUP; EPS 205.03376; Table 7-3 prints EP (NOZZLE) 205.0338; the $ODK card "
                       "is illegible beyond '205,')"),
        "fuel": "H2(L), -2154. cal/mol, 20.56 K (Table 7-2)",
        "oxidiser": "O2(L), -3102. cal/mol, 90.110 K (Table 7-2)",
        "expansion": EXPANSION,
        "solution": FIRST_SOLUTION,
        "engine": ("the 'Pratt and Whitney test engine for RL-10 OTV propulsion', an expander cycle, 15,500 lbf "
                   "nominal vacuum thrust at 394 psia and 205:1 (§7.2, printed p.7-53, PDF p.445); linked to no "
                   "catalog configuration"),
    },
    quantities=tdk_quantities(_TABLE, 5815.918, 477.5184, 456.1371),
    missing=(
        "the program version is not stated, nor which thermodynamic data file the sample used",
        "the ODE product species list is not printed",
        "whether ISP (ODE) and ISP (ODF) were evaluated at the scheduled 205.03 or at the nozzle's printed 205.0338",
        f"the vacuum and frozen-at-chamber conventions are {_CONVENTIONS}",
    ),
    notes=("Independent code, compared without a verdict (DB-4C §14). " + not_recorded("156.3460")
           + " The card temperatures, 20.56 K and 90.110 K, differ from the SSME cards' but the summary prints the "
           "same enthalpies, -2154.000 and -3102.000 cal/mol."),
)

RL10_OTV = TdkPoint(
    case=TDK_MANUAL_1985_RL10_OTV,
    chamber_pressure_psia=RL10_OTV_CHAMBER_PRESSURE_PSIA,
    oxidiser_fuel_ratio=RL10_OTV_OXIDISER_FUEL_RATIO,
    area_ratio=RL10_OTV_AREA_RATIO,
    printed_nozzle_area_ratio=205.0338,
    fuel_card_temperature="20.56",
    oxidiser_card_temperature="90.110",
    catalog_link="an RL10 test engine, linked to no catalog configuration",
    conventions_source=_CONVENTIONS,
)

TDK_MANUAL_1985_ASE = ReferenceCase(
    case_id="tdk-manual-1985-ase",
    title="Rocketdyne prototype Advanced Space Engine (ASE), TDK manual sample (1985), first solution",
    source_kind=SourceKind.INDEPENDENT_CODE,
    benchmark_class="B",
    source=_MANUAL + ", §7.3, Tables 7-4 and 7-5",
    code=CODE,
    code_version=CODE_VERSION,
    database_version=_DATABASE_VERSION,
    origin=CaseOrigin.IMPORTED,
    inputs={
        "chamber_pressure": ("2287 psia, the stagnation pressure of TDK's rocket problem (Table 7-4; Table 7-5 prints "
                             "2287.000; the text's 2300 psia is the nominal design)"),
        "oxidiser_fuel_ratio": "6.378 by mass (Table 7-4 OFSKED 6.3780; Table 7-5 prints 6.378000)",
        "area_ratio": ("400.7148 (Table 7-4 ASUP and $ODK EP; EPS 400.7248; Table 7-5 prints EP (NOZZLE) 400.7248; "
                       "the source does not say why the two differ)"),
        "fuel": "H2(L), -2154. cal/mol, 20.27 K (Table 7-4)",
        "oxidiser": "O2(L), -3102. cal/mol, 90.180 K (Table 7-4)",
        "expansion": EXPANSION,
        "solution": FIRST_SOLUTION,
        "engine": ("the 'Rocketdyne prototype advanced space engine for OTV propulsion', a hydrogen expander cycle, "
                   "22,500 lbf nominal vacuum thrust at 2300 psia and 400:1 (§7.3, printed p.7-59, PDF p.451); a "
                   "prototype, linked to no catalog configuration"),
    },
    quantities=tdk_quantities(_ASE_TABLE, 6556.935, 485.5364, 457.5597),
    missing=(
        "the program version is not stated, nor which thermodynamic data file the sample used",
        "the ODE product species list is not printed",
        "whether ISP (ODE) and ISP (ODF) were evaluated at the scheduled 400.7148 or at the nozzle's printed 400.7248",
        f"the vacuum and frozen-at-chamber conventions are {_ASE_CONVENTIONS}",
    ),
    notes=("Independent code, compared without a verdict (DB-4C §16). " + not_recorded("174.5418")
           + " Table 7-7, the TDE gas table, is not recorded either. Table 7-8 (printed p.7-67, PDF p.459), a second "
           "run of the same engine with the TDE option, prints the same first-solution CHAMBER TEMP 6556.935, "
           "ISP (ODE) 485.5364 and ISP (ODF) 457.5597: the same point, not a further one."),
)

ASE = TdkPoint(
    case=TDK_MANUAL_1985_ASE,
    chamber_pressure_psia=ASE_CHAMBER_PRESSURE_PSIA,
    oxidiser_fuel_ratio=ASE_OXIDISER_FUEL_RATIO,
    area_ratio=ASE_AREA_RATIO,
    printed_nozzle_area_ratio=400.7248,
    fuel_card_temperature="20.27",
    oxidiser_card_temperature="90.180",
    catalog_link="a prototype engine, linked to no catalog configuration",
    conventions_source=_ASE_CONVENTIONS,
)

#: The manual's two samples in its own order. Each is set beside CEA on its own, never beside another point.
POINTS: tuple[TdkPoint, ...] = (RL10_OTV, ASE)
