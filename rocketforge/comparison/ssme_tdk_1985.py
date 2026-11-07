"""The SSME at two design points, as the 1985 TDK program printed them -- an independent code, no verdict (DB-4C).

NASA-CR-178740 (NTRS 19860012108; G. R. Nickerson and L. D. Dang, Software and
Engineering Associates, for NASA MSFC, November 1985) runs the TDK program on
two designs of the Space Shuttle Main Engine at 109%: the "current design", and
a "Large Throat" design whose combustion chamber is modified for a larger throat
while the nozzle assembly is unchanged. For the first solution of each, its
Figures 6 and 7 print the chamber temperature and two one-dimensional ideal
specific impulses: ISP (ODE), an equilibrium expansion, and ISP (ODF), a frozen
one. The inputs are its Figures 3 and 4: the stagnation pressure, the mixture
ratio, the area ratio and the reactants' enthalpies at tank conditions.

What the printed values mean is read from the program's own output, not
assumed (DB-4C §2). In the TDK engineering manual's complete sample run
(NASA-CR-178628, NTRS 19860007470), the summary's ISP (ODE) and ISP (ODF) are the
mass averages of the zones' vacuum (IVAC) columns. The values with exit pressure
equal to ambient are about 60 s lower there. ODF is frozen at the chamber
composition. Those conventions come from the manual of the same program and
year, not from the SSME pages.

Held as :attr:`~.cases.SourceKind.INDEPENDENT_CODE`, imported, for the reason
:mod:`.rp1311_historical` gives for an older printout. Here the program is a
different one and its thermodynamic data are not identified. A difference from
it is information about two codes, never a RocketForge defect. Held as a NASA
printout, it would be judged at half its last printed digit, which the source
does not meet against itself. Its Figures 6 and 7 print -422.3787 and -422.3749
BTU/lb of chamber enthalpy for the same inputs.

Hand-transcribed from the rendered pages of the NTRS copy: Figure 3 is printed
p.17 (PDF p.23), Figure 4 printed p.18 (PDF p.24), Figure 6 printed p.20 (PDF
p.26) and Figure 7 printed p.21 (PDF p.27). The same document is the engine
record ``SRC-NTRS-19860012108`` of ``CFG-RS25-SMALL-THROAT``, the current design.
The enlarged throat is a 1985 design study and is linked to no catalog
configuration. These cases change no engine evidence. The current design's
chamber pressure is the case's own model input and does not reinterpret
``AS-DB05-US-SSME-BLOCK-I-002``.
"""

from __future__ import annotations

from dataclasses import dataclass

from rocketforge.physics.thermochemistry import ExpansionMode

from .cases import CaseOrigin, ReferenceCase, ReferenceQuantity, SourceKind

__all__ = [
    "CHAMBER_PRESSURE_PSIA",
    "OXIDISER_FUEL_RATIO",
    "AREA_RATIO",
    "LARGE_THROAT_CHAMBER_PRESSURE_PSIA",
    "LARGE_THROAT_AREA_RATIO",
    "KEY_CHAMBER_TEMPERATURE",
    "KEY_VACUUM_ISP_EQUILIBRIUM",
    "KEY_VACUUM_ISP_FROZEN",
    "SSME_TDK_1985_CURRENT_DESIGN",
    "SSME_TDK_1985_LARGE_THROAT",
    "TdkPoint",
    "CURRENT_DESIGN",
    "LARGE_THROAT",
    "POINTS",
]

#: Figure 3 ``$ODE``: ``P = 3285., PSIA = T``. TDK's ``P`` is the stagnation
#: pressure of its rocket problem (manual PDF pp.334-335).
CHAMBER_PRESSURE_PSIA = 3285.0
#: Figures 3 and 4 ``OFSKED = 6.05485``, oxidiser to fuel by mass. Figures 6 and 7 print 6.054850.
OXIDISER_FUEL_RATIO = 6.05485
#: Figure 3: the ``ASUP`` schedule ends at 77.5 and ``$ODK`` sets ``EP = 77.5``.
#: Figure 6 prints EP (NOZZLE) 77.50022 for the nozzle; recorded, not used.
AREA_RATIO = 77.5

#: Figure 4 ``$ODE``: ``P = 3010., PSIA = T, DELH = 0``; the report's text gives the
#: same fall "from 3285 (109% power level) to 3010 psia" (printed p.2, PDF p.8).
LARGE_THROAT_CHAMBER_PRESSURE_PSIA = 3010.0
#: Figure 4: the ``ASUP`` schedule ends at 69.5 and ``$ODK`` sets ``EP = 69.5``.
#: Figure 7 prints EP (NOZZLE) 69.48698 for the nozzle; recorded, not used.
LARGE_THROAT_AREA_RATIO = 69.5

KEY_CHAMBER_TEMPERATURE = "chamber_temperature"
#: The expansion model is part of the key, as a composition basis is part of a
#: fraction's: a shifting value can never be compared with a frozen one.
KEY_VACUUM_ISP_EQUILIBRIUM = f"vacuum_specific_impulse:{ExpansionMode.EQUILIBRIUM.value}"
KEY_VACUUM_ISP_FROZEN = f"vacuum_specific_impulse:{ExpansionMode.FROZEN.value}"

_SOURCE = ("G. R. Nickerson and L. D. Dang, 'Performance Predictions for an SSME Configuration with an Enlarged "
           "Throat', NASA-CR-178740, Software and Engineering Associates for NASA MSFC, November 1985; "
           "NTRS 19860012108 (engine record SRC-NTRS-19860012108)")
_CODE = "TDK (Two-Dimensional Kinetics), ODE module; Software and Engineering Associates"
_CODE_VERSION = "not stated (the 1985 program with the shock option)"
_DATABASE_VERSION = "not stated (the thermodynamic data of that program; the report does not identify them)"
_EXPANSION = ("one-dimensional, isentropic, vacuum; ODE in equilibrium, ODF frozen at the chamber "
              "composition (DB-4C §2)")
_FIRST_SOLUTION = "the first TDK/BLM solution: no heat added to the propellant (DELH = 0, DELH1 = 0)"
_CONVENTIONS_MISSING = ("the vacuum and frozen-at-chamber conventions are read from the 1985 TDK manual's sample run, "
                        "not from the SSME pages")
_NOT_RECORDED = ("Not recorded: ISP (ODK) (kinetics); ISP (TDK), ISP (TC), CSTAR (TDK), CF (TDK) and CD "
                 "(two-dimensional flow and boundary layer); every second-solution value (regenerative heat added "
                 "to the propellant, DELH1 {delh1} BTU/lb); HCHAM (ODE), an input consequence.")


def _quantities(figure: str, temperature_r: float, isp_equilibrium: float, isp_frozen: float,
                ) -> tuple[ReferenceQuantity, ...]:
    return (
        ReferenceQuantity(KEY_CHAMBER_TEMPERATURE, temperature_r, "R", decimals=3,
                          note=figure + "; CHAMBER TEMP [R]"),
        ReferenceQuantity(KEY_VACUUM_ISP_EQUILIBRIUM, isp_equilibrium, "lbf*s/lbm", decimals=4,
                          note=figure + "; ISP (ODE) [SECONDS], a vacuum value (DB-4C §2)"),
        ReferenceQuantity(KEY_VACUUM_ISP_FROZEN, isp_frozen, "lbf*s/lbm", decimals=4,
                          note=figure + "; ISP (ODF) [SECONDS], a vacuum value, frozen at the chamber (DB-4C §2)"),
    )


SSME_TDK_1985_CURRENT_DESIGN = ReferenceCase(
    case_id="ssme-tdk-1985-current-design",
    title="SSME current design at 109%, 1985 TDK printout, first solution",
    source_kind=SourceKind.INDEPENDENT_CODE,
    benchmark_class="B",
    source=_SOURCE,
    code=_CODE,
    code_version=_CODE_VERSION,
    database_version=_DATABASE_VERSION,
    origin=CaseOrigin.IMPORTED,
    inputs={
        "chamber_pressure": "3285 psia, the stagnation pressure of TDK's rocket problem (Figure 3)",
        "oxidiser_fuel_ratio": "6.05485 by mass (Figure 3 OFSKED; Figure 6 prints 6.054850)",
        "area_ratio": "77.5 (Figure 3 ASUP and $ODK EP; Figure 6 prints EP (NOZZLE) 77.50022)",
        "fuel": "H2(L), -2154. cal/mol, 20.27 K ('Tank Conditions CPIA 246', Figure 3)",
        "oxidiser": "O2(L), -3102. cal/mol, 90.180 K (Figure 3)",
        "expansion": _EXPANSION,
        "solution": _FIRST_SOLUTION,
    },
    quantities=_quantities("Figure 6 (printed p.20, PDF p.26), first TDK/BLM solution", 6543.192, 465.1311, 446.7661),
    missing=(
        "the program version and its thermodynamic data are not stated",
        "the ODE product species list is not printed",
        "whether ISP (ODE) and ISP (ODF) were evaluated at the scheduled 77.5 or at the nozzle's printed 77.50022",
        _CONVENTIONS_MISSING,
    ),
    notes=("Independent code, compared without a verdict (DB-4C). " + _NOT_RECORDED.format(delh1="118.7092")
           + " Figure 7, the enlarged-throat design, is its own case (DB-4C §12)."),
)

SSME_TDK_1985_LARGE_THROAT = ReferenceCase(
    case_id="ssme-tdk-1985-large-throat",
    title="SSME 'Large Throat' design study at 109%, 1985 TDK printout, first solution",
    source_kind=SourceKind.INDEPENDENT_CODE,
    benchmark_class="B",
    source=_SOURCE,
    code=_CODE,
    code_version=_CODE_VERSION,
    database_version=_DATABASE_VERSION,
    origin=CaseOrigin.IMPORTED,
    inputs={
        "chamber_pressure": "3010 psia, the stagnation pressure of TDK's rocket problem (Figure 4)",
        "oxidiser_fuel_ratio": "6.05485 by mass (Figure 4 OFSKED; Figure 7 prints 6.054850)",
        "area_ratio": "69.5 (Figure 4 ASUP and $ODK EP; Figure 7 prints EP (NOZZLE) 69.48698)",
        "fuel": "H2(L), -2154. cal/mol, 20.27 K (Figure 4, the current design's card)",
        "oxidiser": "O2(L), -3102. cal/mol, 90.180 K (Figure 4)",
        "expansion": _EXPANSION,
        "solution": _FIRST_SOLUTION,
        "design": ("the report's 'Large Throat' design: the combustion chamber modified for a larger throat, the "
                   "nozzle assembly unchanged (printed p.2, PDF p.8); a 1985 design study, linked to no catalog "
                   "configuration"),
    },
    quantities=_quantities("Figure 7 (printed p.21, PDF p.27), first TDK/BLM solution", 6526.882, 463.2604, 444.7228),
    missing=(
        "the program version and its thermodynamic data are not stated",
        "the ODE product species list is not printed",
        "whether ISP (ODE) and ISP (ODF) were evaluated at the scheduled 69.5 or at the nozzle's printed 69.48698",
        _CONVENTIONS_MISSING,
    ),
    notes="Independent code, compared without a verdict (DB-4C §12). " + _NOT_RECORDED.format(delh1="116.6856"),
)


@dataclass(frozen=True, slots=True)
class TdkPoint:
    """A case with the model inputs its figure was run at, in the source's units.

    ``printed_nozzle_area_ratio`` is the figure's EP (NOZZLE): recorded and
    declared, never used. ``catalog_link`` says what the point is, or is not, in
    the engine catalog.
    """

    case: ReferenceCase
    chamber_pressure_psia: float
    oxidiser_fuel_ratio: float
    area_ratio: float
    printed_nozzle_area_ratio: float
    catalog_link: str


CURRENT_DESIGN = TdkPoint(
    case=SSME_TDK_1985_CURRENT_DESIGN,
    chamber_pressure_psia=CHAMBER_PRESSURE_PSIA,
    oxidiser_fuel_ratio=OXIDISER_FUEL_RATIO,
    area_ratio=AREA_RATIO,
    printed_nozzle_area_ratio=77.50022,
    catalog_link="the engine assertion AS-DB05-US-SSME-BLOCK-I-002 is not reinterpreted",
)

LARGE_THROAT = TdkPoint(
    case=SSME_TDK_1985_LARGE_THROAT,
    chamber_pressure_psia=LARGE_THROAT_CHAMBER_PRESSURE_PSIA,
    oxidiser_fuel_ratio=OXIDISER_FUEL_RATIO,
    area_ratio=LARGE_THROAT_AREA_RATIO,
    printed_nozzle_area_ratio=69.48698,
    catalog_link="a 1985 design study, linked to no catalog configuration",
)

#: The current design first, then the enlarged throat. Each is set beside CEA on its own, never beside the other.
POINTS: tuple[TdkPoint, ...] = (CURRENT_DESIGN, LARGE_THROAT)
