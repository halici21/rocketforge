"""Theoretical values printed in NASA solid-propellant reports -- imported, no verdict.

Two reports in the propulsion evidence corpus print theoretical performance
next to their test results: NASA TN D-7133 (theoretical c* per propellant
batch) and JPL Publication 79-29 (flame temperature and vacuum specific
impulse of the TP-H1148 baseline). Neither names a code version or its
thermodynamic data, and neither formulation is source-complete (the binders
are lumped or undefined), so RocketForge cannot reproduce them. They are held
as :attr:`~.cases.SourceKind.INDEPENDENT_CODE` cases, :attr:`~.cases.CaseOrigin.IMPORTED`:
a comparison reports differences and draws no verdict.

Hand-transcribed from the R1 evidence audit, which read each value from the
rendered page images of the NTRS copies; the evidence records
``DS-TND7133`` and ``DS-JPL-ALTPROP-BATES`` name these cases. A value a report
prints inconsistently is recorded as printed and not used as a quantity --
choosing one of two disagreeing printed numbers would correct the source.
"""

from __future__ import annotations

from .cases import CaseOrigin, ReferenceCase, ReferenceQuantity, SourceKind

__all__ = [
    "TND7133_THEORETICAL_CSTAR",
    "JPL_79_29_TP_H1148_THEORETICAL",
    "SOLID_REPORT_CASES",
]

_TND7133 = "NASA TN D-7133 (Northam and Sullivan, 1973), Table II (report p.9); NTRS 19730008048"
_TND7133_CODE = "not named in the source (theoretical c* program)"
_TND7133_MISSING = (
    "the program, its version and its thermodynamic data are not named",
    "the binder, curative and bonding agent are lumped in Table I, so the "
    "formulation cannot be reproduced",
)


def _tnd7133(batch: str, cstar_ft_s: int, printed_si: str) -> ReferenceCase:
    return ReferenceCase(
        case_id=f"tnd7133-{batch}-theoretical-cstar",
        title=f"NASA TN D-7133 batch {batch}, theoretical c*",
        source_kind=SourceKind.INDEPENDENT_CODE,
        benchmark_class="A",
        source=_TND7133,
        code=_TND7133_CODE,
        code_version="not stated",
        database_version="not stated",
        origin=CaseOrigin.IMPORTED,
        inputs={"batch": batch,
                "formulation": "Table I (report p.3); binder, curative and bonding agent lumped",
                "chamber_pressure": "the batch's average chamber pressure (report p.7)"},
        quantities=(ReferenceQuantity(
            "characteristic_velocity", cstar_ft_s, "ft/s", decimals=0,
            note=(f"Table II prints {cstar_ft_s} ft/s ({printed_si}); theoretical, "
                  "'evaluated at the average chamber pressures' (report p.7)")),),
        missing=_TND7133_MISSING,
        notes=("Imported reference, compared without a verdict. The delivered c* and c* "
               "efficiency in the same table are measurements and are not part of this case."),
    )


TND7133_THEORETICAL_CSTAR = (
    _tnd7133("72-16", 5095, "1553 m/s"),
    _tnd7133("72-17", 5073, "1546 m/s"),
    _tnd7133("72-18", 5084, "1550 m/s"),
)

_JPL = "JPL Publication 79-29 (Anderson and West, 1979), Table 2-2 (PDF p.22); NTRS 19790020174"

JPL_79_29_TP_H1148_THEORETICAL = ReferenceCase(
    case_id="jpl-79-29-tp-h1148-theoretical",
    title="JPL Publication 79-29, TP-H1148 baseline theoretical performance",
    source_kind=SourceKind.INDEPENDENT_CODE,
    benchmark_class="A",
    source=_JPL,
    code="JPL free-energy-minimisation program (name not reported)",
    code_version="not stated",
    database_version="not stated",
    origin=CaseOrigin.IMPORTED,
    inputs={"propellant": "TP-H1148 baseline, Table 2-1 (PDF p.21)",
            "expansion_ratio": "7.16, as the vacuum specific impulse is printed"},
    quantities=(
        ReferenceQuantity("chamber_temperature", 3471, "K", decimals=0,
                          note="Table 2-2 prints Tf, the theoretical flame temperature"),
        ReferenceQuantity("vacuum_specific_impulse", 2713.5, "N*s/kg", decimals=1,
                          note="Table 2-2 prints '2713.5 (276.7)' N-s/kg (s), at expansion ratio 7.16"),
    ),
    missing=(
        "characteristic_velocity: Table 2-2 prints '1371 (5155)' m/s (ft/s). 5155 ft/s is "
        "1571 m/s, so the printed SI and ft/s values disagree. Recorded as printed and "
        "not used as a quantity: choosing either value would correct the source",
        "the program's name, version and thermodynamic data are not reported",
        "the chamber pressure of the theoretical calculation is not recorded in the R1 audit",
        "the PBAN binder has no formula or enthalpy in the report",
    ),
    notes=("Imported reference, compared without a verdict. Delivered c*, Isp and total "
           "impulse per BATES firing are measurements, not part of this case, and never "
           "compared with an ideal value as an error."),
)

#: Every case in this module, for the evidence records that name them.
SOLID_REPORT_CASES = (*TND7133_THEORETICAL_CSTAR, JPL_79_29_TP_H1148_THEORETICAL)
