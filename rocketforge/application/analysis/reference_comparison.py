"""Comparison of computed results against a published reference table.

The direction of this dependency matters more than anything else in the file:

    published table  ──compare──▶  RocketForge computed value

never

    published table  ──lookup──▶  answer

The reference is a *check*, not a solver. Nothing in RocketForge reads a table
value to produce an engineering result, and no value is ever interpolated
between printed rows -- doing that would quietly turn the book into a second,
unvalidated calculator.

Tolerance comes from the source's own printed precision. A textbook prints four
significant figures, so a computed 8285.512 and a printed 8285 agree perfectly
well; requiring more would be requiring the book to be more precise than it is.

Qt-free, so the comparison can be run and tested headlessly.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from dataclasses import dataclass
from functools import lru_cache

from ...physics.compressible import PerfectGas
from ...physics.compressible import isentropic as iso
from ...physics.compressible import normal_shock as ns
from ...physics.compressible import prandtl_meyer as pm

__all__ = [
    "ReferenceDataset",
    "ReferenceTable",
    "QuantityComparison",
    "RowComparison",
    "ComparisonSummary",
    "load_reference",
    "compare_row",
    "compare_table",
    "DATASETS",
    "ISENTROPIC_DATASET",
    "NORMAL_SHOCK_DATASET",
    "PRANDTL_MEYER_DATASET",
    "reference_root",
    "REFERENCE_PATH",
    "NORMAL_SHOCK_REFERENCE_PATH",
    "PRANDTL_MEYER_REFERENCE_PATH",
    "load_normal_shock_reference",
    "load_prandtl_meyer_reference",
]

def reference_root() -> pathlib.Path:
    """Where the published reference tables live.

    Asked explicitly rather than derived from ``__file__`` alone, because a
    frozen build unpacks its data somewhere else entirely and says where
    through ``sys._MEIPASS``. Getting this wrong would not fail the tests --
    it would fail only in the shipped executable, with the comparison feature
    silently dead.
    """
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return pathlib.Path(bundled) / "rocketforge" / "data" / "reference"
    return pathlib.Path(__file__).resolve().parents[2] / "data" / "reference"


#: Dataset keys, as each file declares itself. The file says which dataset it
#: is; the registry below says how to reproduce it. Neither is inferred from a
#: filename, so a mis-named file fails loudly instead of being compared with
#: the wrong recipe.
ISENTROPIC_DATASET = "anderson6_appendix_a_isentropic"
NORMAL_SHOCK_DATASET = "anderson6_appendix_b_normal_shock"
PRANDTL_MEYER_DATASET = "anderson6_appendix_c_prandtl_meyer"

REFERENCE_PATH = reference_root() / "anderson6_appendix_a_isentropic.json"
NORMAL_SHOCK_REFERENCE_PATH = reference_root() / "anderson6_appendix_b_normal_shock.json"
PRANDTL_MEYER_REFERENCE_PATH = reference_root() / "anderson6_appendix_c_prandtl_meyer.json"


@dataclass(frozen=True, slots=True)
class ReferenceDataset:
    """How one published table maps onto RocketForge's own relations.

    ``recipe`` is the whole point: for every printed column there is a
    callable that *computes* the value from the physics layer. Adding a
    published table therefore means declaring how to recompute it, which is
    the opposite of reading it.
    """

    key: str
    path: pathlib.Path
    mach_key: str
    recipe: dict
    labels: dict


#: Appendix A. The reciprocals are representation transforms of the canonical
#: ratios, not alternative formulas.
_ISENTROPIC = ReferenceDataset(
    key=ISENTROPIC_DATASET,
    path=REFERENCE_PATH,
    mach_key="mach",
    recipe={
        "p0_over_p": lambda m, g: 1.0 / float(iso.pressure_ratio(m, g)),
        "rho0_over_rho": lambda m, g: 1.0 / float(iso.density_ratio(m, g)),
        "T0_over_T": lambda m, g: 1.0 / float(iso.temperature_ratio(m, g)),
        "area_ratio": lambda m, g: float(iso.area_ratio(m, g)),
    },
    labels={
        "p0_over_p": "p₀/p",
        "rho0_over_rho": "ρ₀/ρ",
        "T0_over_T": "T₀/T",
        "area_ratio": "A/A*",
    },
)

#: Appendix B. Every column is recomputed from ``normal_shock``; note that
#: ``T2/T1`` and ``p02/p1`` are themselves composed inside the physics module,
#: so this table checks those compositions against print as well.
_NORMAL_SHOCK = ReferenceDataset(
    key=NORMAL_SHOCK_DATASET,
    path=NORMAL_SHOCK_REFERENCE_PATH,
    mach_key="mach1",
    recipe={
        "p2_over_p1": lambda m, g: float(ns.pressure_ratio(m, g)),
        "rho2_over_rho1": lambda m, g: float(ns.density_ratio(m, g)),
        "T2_over_T1": lambda m, g: float(ns.temperature_ratio(m, g)),
        "p02_over_p01": lambda m, g: float(ns.stagnation_pressure_ratio(m, g)),
        "p02_over_p1": lambda m, g: float(ns.stagnation_pressure_over_upstream_static(m, g)),
        "mach2": lambda m, g: float(ns.mach_downstream(m, g)),
    },
    labels={
        "p2_over_p1": "p₂/p₁",
        "rho2_over_rho1": "ρ₂/ρ₁",
        "T2_over_T1": "T₂/T₁",
        "p02_over_p01": "p₀₂/p₀₁",
        "p02_over_p1": "p₀₂/p₁",
        "mach2": "M₂",
    },
)

#: Appendix C. The published columns are in **degrees** while the physics layer
#: works in radians throughout, so the conversion happens here -- in the
#: adapter, at the boundary -- and never inside a relation. The Mach-angle
#: column is recomputed from the isentropic module, which is the one place
#: asin(1/M) is defined.
_PRANDTL_MEYER = ReferenceDataset(
    key=PRANDTL_MEYER_DATASET,
    path=PRANDTL_MEYER_REFERENCE_PATH,
    mach_key="mach",
    recipe={
        "nu": lambda m, g: math.degrees(float(pm.nu(m, g))),
        "mach_angle": lambda m, g: math.degrees(float(iso.mach_angle(m))),
    },
    labels={
        "nu": "\u03bd [\u00b0]",
        "mach_angle": "\u03bc [\u00b0]",
    },
)

#: Every published table RocketForge knows how to check itself against.
DATASETS: dict = {
    ISENTROPIC_DATASET: _ISENTROPIC,
    NORMAL_SHOCK_DATASET: _NORMAL_SHOCK,
    PRANDTL_MEYER_DATASET: _PRANDTL_MEYER,
}

#: Mach values are matched numerically, not by row index, because a user's
#: generated grid need not align with the published one. The window is far
#: tighter than any spacing either table uses.
MACH_MATCH_TOLERANCE = 1e-9


@dataclass(frozen=True, slots=True)
class ReferenceTable:
    """An immutable published table, loaded once and never modified."""

    dataset: str
    citation: str
    gamma: float
    quantities: tuple[str, ...]
    machs: tuple[float, ...]
    rows: tuple[dict, ...]
    mantissa_digits: int
    source: dict
    mach_key: str = "mach"

    @property
    def spec(self) -> ReferenceDataset:
        """The recipe for recomputing this table's columns."""
        return DATASETS[self.dataset]

    def row_for(self, mach: float) -> dict | None:
        """The printed row at this Mach number, or None if it is not tabulated.

        No interpolation. A Mach number between two printed rows has no
        reference value, and saying so is the honest answer.
        """
        for index, tabulated in enumerate(self.machs):
            if abs(tabulated - mach) <= MACH_MATCH_TOLERANCE:
                return self.rows[index]
        return None

    def tolerance_for(self, printed: float) -> float:
        """Half a unit in the last printed digit of a value.

        The source prints a four-digit mantissa with a base-10 exponent, so its
        absolute precision scales with magnitude: 1.687 is stated to ±0.0005
        while 8285 is stated only to ±0.5.
        """
        if printed == 0.0:
            return 0.5 * 10.0 ** -self.mantissa_digits
        exponent = math.floor(math.log10(abs(printed))) + 1
        return 0.5 * 10.0 ** (exponent - self.mantissa_digits)


@dataclass(frozen=True, slots=True)
class QuantityComparison:
    """One computed value set beside its published counterpart."""

    key: str
    label: str
    computed: float
    reference: float
    difference: float
    relative_difference: float
    tolerance: float
    status: str          # "PASS" | "REVIEW"

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


@dataclass(frozen=True, slots=True)
class RowComparison:
    """Every quantity compared at one Mach number."""

    mach: float
    quantities: tuple[QuantityComparison, ...]
    status: str

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


@dataclass(frozen=True, slots=True)
class ComparisonSummary:
    """The outcome of comparing a whole table against the reference."""

    rows_compared: int
    values_compared: int
    passed: int
    review: int
    max_absolute_difference: float
    max_relative_difference: float
    worst: str
    citation: str
    gamma: float
    reviews: tuple[RowComparison, ...] = ()

    @property
    def all_passed(self) -> bool:
        return self.review == 0

    @property
    def pass_fraction(self) -> float:
        return self.passed / self.values_compared if self.values_compared else 0.0


@lru_cache(maxsize=6)
def load_reference(path: str | None = None) -> ReferenceTable:
    """Load the published reference table.

    Cached because the file never changes at runtime: it is source data, and
    treating it as read-only is what keeps a computed result from ever leaking
    back into it. This is the one cache in the application, and it caches a
    file read rather than a calculation.
    """
    target = pathlib.Path(path) if path else REFERENCE_PATH
    payload = json.loads(target.read_text(encoding="utf-8"))
    key = payload["dataset"]
    if key not in DATASETS:
        raise KeyError(
            f"{target.name} declares dataset {key!r}, which RocketForge has no "
            "recipe for; a published table cannot be compared against unless "
            "every one of its columns can be recomputed"
        )
    spec = DATASETS[key]
    source = payload["source"]
    citation = (
        f"{source['author']}, {source['title']}, {source['edition']}, "
        f"{source['appendix']}, pp. {source['printed_pages']}"
    )
    rows = tuple(dict(row) for row in payload["rows"])
    return ReferenceTable(
        dataset=key,
        citation=citation,
        gamma=float(payload["gamma"]),
        quantities=tuple(k for k in payload["columns"] if k != spec.mach_key),
        machs=tuple(float(r[spec.mach_key]) for r in rows),
        rows=rows,
        mantissa_digits=int(payload["printed_significant_figures"]),
        source=source,
        mach_key=spec.mach_key,
    )


def load_normal_shock_reference() -> ReferenceTable:
    """Anderson Appendix B, loaded through the same path-aware machinery."""
    return load_reference(str(NORMAL_SHOCK_REFERENCE_PATH))


def load_prandtl_meyer_reference() -> ReferenceTable:
    """Anderson Appendix C, loaded through the same path-aware machinery."""
    return load_reference(str(PRANDTL_MEYER_REFERENCE_PATH))


def compare_row(mach: float, gamma: float, reference: ReferenceTable | None = None
                ) -> RowComparison | None:
    """Compare RocketForge's computed values at one Mach against the source.

    Returns None when the Mach number is not tabulated: no interpolation, and
    no invented reference value.
    """
    table = reference or load_reference()
    if not math.isclose(gamma, table.gamma, rel_tol=1e-12):
        return None
    row = table.row_for(mach)
    if row is None:
        return None

    gas = PerfectGas(gamma=gamma)
    spec = table.spec
    quantities = []
    for key in table.quantities:
        # The computed value is always recalculated here. The reference is
        # never used as an input to the calculation it is checking.
        computed = spec.recipe[key](mach, gas)
        printed = float(row[key])
        difference = computed - printed
        tolerance = table.tolerance_for(printed)
        # A hair of slack for the binary representation of a decimal: a value
        # sitting exactly on the half-unit boundary should not fail because
        # 1.687 is not exactly representable.
        within = abs(difference) <= tolerance * (1.0 + 1e-9)
        quantities.append(QuantityComparison(
            key=key,
            label=spec.labels.get(key, key),
            computed=computed,
            reference=printed,
            difference=difference,
            # A printed zero is a real value in Appendix C (nu at Mach 1), and
            # a zero difference against it is perfect agreement, not an
            # undefined ratio. Only a *nonzero* difference from zero is
            # genuinely unbounded.
            relative_difference=(difference / printed if printed
                                 else (0.0 if difference == 0.0 else math.inf)),
            tolerance=tolerance,
            status="PASS" if within else "REVIEW",
        ))

    status = "PASS" if all(q.passed for q in quantities) else "REVIEW"
    return RowComparison(mach=mach, quantities=tuple(quantities), status=status)


def compare_table(gamma: float, machs=None, reference: ReferenceTable | None = None
                  ) -> ComparisonSummary:
    """Compare every tabulated Mach number (or a given subset) against the source.

    Args:
        gamma: Must match the reference gamma; otherwise nothing is compared,
            because checking a gamma = 1.22 calculation against a gamma = 1.4
            table would be meaningless.
        machs: Restrict to these Mach numbers. Values absent from the reference
            are skipped rather than interpolated.
    """
    table = reference or load_reference()
    if not math.isclose(gamma, table.gamma, rel_tol=1e-12):
        return ComparisonSummary(0, 0, 0, 0, 0.0, 0.0, "", table.citation, table.gamma)

    candidates = table.machs if machs is None else [
        m for m in machs if table.row_for(float(m)) is not None
    ]

    rows_compared = values = passed = review = 0
    max_absolute = max_relative = 0.0
    worst = ""
    reviews: list[RowComparison] = []

    for mach in candidates:
        comparison = compare_row(float(mach), gamma, table)
        if comparison is None:
            continue
        rows_compared += 1
        for quantity in comparison.quantities:
            values += 1
            if quantity.passed:
                passed += 1
            else:
                review += 1
            max_absolute = max(max_absolute, abs(quantity.difference))
            if abs(quantity.relative_difference) > max_relative:
                max_relative = abs(quantity.relative_difference)
                worst = f"{quantity.label} at M = {mach:g}"
        if not comparison.passed:
            reviews.append(comparison)

    return ComparisonSummary(
        rows_compared=rows_compared,
        values_compared=values,
        passed=passed,
        review=review,
        max_absolute_difference=max_absolute,
        max_relative_difference=max_relative,
        worst=worst,
        citation=table.citation,
        gamma=table.gamma,
        reviews=tuple(reviews),
    )
