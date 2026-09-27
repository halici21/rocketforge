"""NASA RP-1311 Example 5 as printed in 1996 -- a historical reference, not a verdict.

RP-1311 Part II (McBride and Gordon, 1996) prints Example 5's output from the
Fortran CEA program of that time, with the thermodynamic data of that time.
RocketForge's regression lock, :data:`.rp1311.RP1311_EXAMPLE5_PUBLISHED`, is a
different printout: NASA's shipped cea 3.3.4 sample of the same problem. The
two do not agree to printed precision -- 2724.46 K against 2723.021 K in
chamber temperature, 22.282 against 22.290 in molecular weight. The
difference is attributed to revisions of the thermodynamic data between the
two, which has not been verified record by record; either way it is not a
RocketForge defect, because RocketForge reproduces cea 3.3.4 bit for bit.

So this case is recorded as an **independent code** (``SourceKind.INDEPENDENT_CODE``):
a comparison against it reports the differences and draws no verdict. Held as
``NASA_PUBLISHED`` it would "differ" against every correct cea 3.3.4 result and
read as a RocketForge error, which it is not.

Hand-transcribed, not generated: the printed table is a scanned page, not a
runnable script. Every value below was read from the rendered page images of
the NTRS copy (NTRS 19960044559), printed pages 132 (scalars) and 133 (mole
fractions), which are PDF pages 138 and 139, and is recorded in the evidence
record ``DS-RP1311-E5`` under source ``S-NASA-RP1311-P2-1996``.
"""

from __future__ import annotations

from .cases import ReferenceCase, ReferenceQuantity, SourceKind

__all__ = ["RP1311_EXAMPLE5_PRINT_1996"]

_PAGE_132 = "RP-1311 Part II printed p.132 (NTRS PDF p.138), first column"
_PAGE_133 = "RP-1311 Part II printed p.133 (NTRS PDF p.139), MOLE FRACTIONS, first column"

RP1311_EXAMPLE5_PRINT_1996 = ReferenceCase(
    case_id="rp1311-example5-print-1996",
    title="NASA RP-1311 Part II (1996) Example 5 printed table, first pressure column",
    source_kind=SourceKind.INDEPENDENT_CODE,
    benchmark_class="A",
    source=("NASA RP-1311 Part II (McBride and Gordon, 1996), Example 5 printed "
            "output; NTRS 19960044559"),
    code="NASA CEA (Fortran program documented in RP-1311 Part II, 1996)",
    code_version="not stated",
    inputs={"example": 5, "column": "first printed column",
            "chamber_pressure": "500 psia, printed as 34.023 atm",
            "reactants": "NH4CLO4(I) 72.06, CHOS-Binder 18.58, AL(cr) 9, MgO(s) 0.2, "
                         "H2O(L) 0.16 wt%, all at 298.15 K"},
    quantities=(
        ReferenceQuantity("chamber_pressure", 34.023, "atm", decimals=3, note=_PAGE_132),
        ReferenceQuantity("chamber_temperature", 2724.46, "K", decimals=2, note=_PAGE_132),
        ReferenceQuantity("density", 3.5209e-03, "g/cm^3", significant_figures=5,
                          note=_PAGE_132),
        ReferenceQuantity("enthalpy", -484.76, "cal/g", decimals=2, note=_PAGE_132),
        ReferenceQuantity("molar_mass", 22.282, "kg/kmol", decimals=3,
                          note=_PAGE_132 + "; printed 'MW, MOL WT'"),
        ReferenceQuantity("gamma_s", 1.1945, "1", decimals=4,
                          note=_PAGE_132 + "; printed 'GAMMAs'"),
        ReferenceQuantity("mole_fraction:CO", 0.26445, "1", decimals=5, note=_PAGE_133),
        ReferenceQuantity("mole_fraction:HCL", 0.13214, "1", decimals=5, note=_PAGE_133),
        ReferenceQuantity("mole_fraction:H2", 0.32150, "1", decimals=5, note=_PAGE_133),
        ReferenceQuantity("mole_fraction:H2O", 0.14659, "1", decimals=5, note=_PAGE_133),
        ReferenceQuantity("mole_fraction:AL2O3(L)", 0.03691, "1", decimals=5,
                          note=_PAGE_133),
    ),
    missing=(
        "the program version and the thermodynamic database behind the print are not stated",
        "the binder molecular weight is not printed (the cea 3.3.4 sample states 14.6652984484)",
    ),
    notes=("Historical reference, compared without a verdict. A subset of the printed "
           "column is transcribed; M (1/n) 23.136 is printed but RocketForge reports "
           "MW, not M. The print names the magnesium oxide reactant MgO(s); the cea "
           "3.3.4 sample names it MgO(cr)."),
)
