"""The SSME current design as the 1985 TDK program printed it -- an independent code, no verdict (DB-4C).

NASA-CR-178740 (NTRS 19860012108; G. R. Nickerson and L. D. Dang, Software and
Engineering Associates, for NASA MSFC, November 1985) runs the TDK program on
the Space Shuttle Main Engine "current design" at 109%. Its Figure 6 prints, for
the first solution, the chamber temperature and two one-dimensional ideal
specific impulses: ISP (ODE), an equilibrium expansion, and ISP (ODF), a frozen
one. The inputs are its Figure 3: the stagnation pressure, the mixture ratio,
the area ratio and the reactants' enthalpies at tank conditions.

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

Hand-transcribed from the rendered pages of the NTRS copy. Figure 3 is
printed p.17 (PDF p.23) and Figure 6 is printed p.20 (PDF p.26). The same
document is the engine record ``SRC-NTRS-19860012108`` of ``CFG-RS25-SMALL-THROAT``.
This case changes no engine evidence. Its chamber pressure is the case's own model
input and does not reinterpret ``AS-DB05-US-SSME-BLOCK-I-002``.
"""

from __future__ import annotations

from rocketforge.physics.thermochemistry import ExpansionMode

from .cases import CaseOrigin, ReferenceCase, ReferenceQuantity, SourceKind

__all__ = [
    "CHAMBER_PRESSURE_PSIA",
    "OXIDISER_FUEL_RATIO",
    "AREA_RATIO",
    "KEY_CHAMBER_TEMPERATURE",
    "KEY_VACUUM_ISP_EQUILIBRIUM",
    "KEY_VACUUM_ISP_FROZEN",
    "SSME_TDK_1985_CURRENT_DESIGN",
]

#: Figure 3 ``$ODE``: ``P = 3285., PSIA = T``. TDK's ``P`` is the stagnation
#: pressure of its rocket problem (manual PDF pp.334-335).
CHAMBER_PRESSURE_PSIA = 3285.0
#: Figure 3 ``OFSKED = 6.05485``, oxidiser to fuel by mass. Figure 6 prints 6.054850.
OXIDISER_FUEL_RATIO = 6.05485
#: Figure 3: the ``ASUP`` schedule ends at 77.5 and ``$ODK`` sets ``EP = 77.5``.
#: Figure 6 prints EP (NOZZLE) 77.50022 for the nozzle; recorded, not used.
AREA_RATIO = 77.5

KEY_CHAMBER_TEMPERATURE = "chamber_temperature"
#: The expansion model is part of the key, as a composition basis is part of a
#: fraction's: a shifting value can never be compared with a frozen one.
KEY_VACUUM_ISP_EQUILIBRIUM = f"vacuum_specific_impulse:{ExpansionMode.EQUILIBRIUM.value}"
KEY_VACUUM_ISP_FROZEN = f"vacuum_specific_impulse:{ExpansionMode.FROZEN.value}"

_FIG6 = "Figure 6 (printed p.20, PDF p.26), first TDK/BLM solution"

SSME_TDK_1985_CURRENT_DESIGN = ReferenceCase(
    case_id="ssme-tdk-1985-current-design",
    title="SSME current design at 109%, 1985 TDK printout, first solution",
    source_kind=SourceKind.INDEPENDENT_CODE,
    benchmark_class="B",
    source=("G. R. Nickerson and L. D. Dang, 'Performance Predictions for an SSME Configuration with an "
            "Enlarged Throat', NASA-CR-178740, Software and Engineering Associates for NASA MSFC, "
            "November 1985; NTRS 19860012108 (engine record SRC-NTRS-19860012108)"),
    code="TDK (Two-Dimensional Kinetics), ODE module; Software and Engineering Associates",
    code_version="not stated (the 1985 program with the shock option)",
    database_version="not stated (the thermodynamic data of that program; the report does not identify them)",
    origin=CaseOrigin.IMPORTED,
    inputs={
        "chamber_pressure": "3285 psia, the stagnation pressure of TDK's rocket problem (Figure 3)",
        "oxidiser_fuel_ratio": "6.05485 by mass (Figure 3 OFSKED; Figure 6 prints 6.054850)",
        "area_ratio": "77.5 (Figure 3 ASUP and $ODK EP; Figure 6 prints EP (NOZZLE) 77.50022)",
        "fuel": "H2(L), -2154. cal/mol, 20.27 K ('Tank Conditions CPIA 246', Figure 3)",
        "oxidiser": "O2(L), -3102. cal/mol, 90.180 K (Figure 3)",
        "expansion": ("one-dimensional, isentropic, vacuum; ODE in equilibrium, ODF frozen at the chamber "
                      "composition (DB-4C §2)"),
        "solution": "the first TDK/BLM solution: no heat added to the propellant (DELH = 0, DELH1 = 0)",
    },
    quantities=(
        ReferenceQuantity(KEY_CHAMBER_TEMPERATURE, 6543.192, "R", decimals=3,
                          note=_FIG6 + "; CHAMBER TEMP [R]"),
        ReferenceQuantity(KEY_VACUUM_ISP_EQUILIBRIUM, 465.1311, "lbf*s/lbm", decimals=4,
                          note=_FIG6 + "; ISP (ODE) [SECONDS], a vacuum value (DB-4C §2)"),
        ReferenceQuantity(KEY_VACUUM_ISP_FROZEN, 446.7661, "lbf*s/lbm", decimals=4,
                          note=_FIG6 + "; ISP (ODF) [SECONDS], a vacuum value, frozen at the chamber (DB-4C §2)"),
    ),
    missing=(
        "the program version and its thermodynamic data are not stated",
        "the ODE product species list is not printed",
        "whether ISP (ODE) and ISP (ODF) were evaluated at the scheduled 77.5 or at the nozzle's printed 77.50022",
        "the vacuum and frozen-at-chamber conventions are read from the 1985 TDK manual's sample run, not from "
        "the SSME pages",
    ),
    notes=("Independent code, compared without a verdict (DB-4C). Not recorded: ISP (ODK) (kinetics); "
           "ISP (TDK), ISP (TC), CSTAR (TDK), CF (TDK) and CD (two-dimensional flow and boundary layer); every "
           "second-solution value (regenerative heat added to the propellant, DELH1 118.7092 BTU/lb); "
           "HCHAM (ODE), an input consequence; and Figure 7, the enlarged-throat design."),
)
