"""DB-4C: the ideal reference cases from 1985 TDK printouts, each run in two separate steps. Report only.

There are three points from two documents of one program: the SSME current
design and enlarged-throat design study from the 1985 TDK report
(:mod:`rocketforge.comparison.ssme_tdk_1985`), and the RL-10 OTV test engine from
the TDK manual's own sample (:mod:`rocketforge.comparison.tdk_manual_1985`).
Each is run on its own.

**Step A** compares the TDK printout with the same model class:

- the chamber temperature with RocketForge's chamber result, a CEA HP solve;
- the vacuum Isp, shifting and frozen at the chamber, with CEA's own rocket
  answer from :mod:`.performance_oracle`.

The case is an independent code, so every row is ``compared`` and no bound is
formed. A difference there is the code and the thermodynamic data, plus the
declared input differences, and is never a RocketForge defect.

**Step B** compares RocketForge's constant-gamma vacuum Isp, for each gamma basis,
with CEA's at the matching expansion, at the same point. The printout takes no
part. A difference is the reduction alone, labelled a model difference.

There is deliberately no row of RocketForge against the printout. That one number
would mix code, data and reduction, and would read as an error against a NASA
source. A reader who wants it adds the two steps and keeps the attribution. Nor
is there a row between any two points: each is set beside CEA, never beside
another.

All or nothing, per point: if any of a point's five computations fails, only the
reason is returned for that point. Never raises. Writes nothing. No test pins a
computed difference, and no rule may change in response to one
(DB4C_SSME_TDK_IDEAL_REFERENCE.md §8, §12, §14).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rocketforge.comparison.cases import ReferenceCase
from rocketforge.comparison.compare import CaseComparison, ObservedQuantity, compare
from rocketforge.comparison import ssme_tdk_1985, tdk_manual_1985
from rocketforge.comparison.ssme_tdk_1985 import CURRENT_DESIGN
from rocketforge.comparison.tdk_1985 import (
    KEY_CHAMBER_TEMPERATURE,
    KEY_VACUUM_ISP_EQUILIBRIUM,
    KEY_VACUUM_ISP_FROZEN,
    TdkPoint,
)
from rocketforge.comparison.units import to_canonical
from rocketforge.core.constants import STANDARD_GRAVITY

__all__ = ["KIND_OK", "KIND_REFUSED", "KIND_UNAVAILABLE", "FUEL", "OXIDISER", "PAIRINGS", "STEP_A_ORACLE_MODES",
           "POINTS", "declarations", "ReductionRow", "IdealCaseOutcome", "chamber_case", "run_ideal_case",
           "run_ideal_cases"]

#: Every point, in report order: the SSME report's two, then the manual's sample. No row compares any two.
POINTS: tuple[TdkPoint, ...] = (*ssme_tdk_1985.POINTS, *tdk_manual_1985.POINTS)

KIND_OK = "ok"
KIND_REFUSED = "refused"
KIND_UNAVAILABLE = "unavailable"

#: (model definition, inlet temperature in K). Both are CEA's reference temperatures for H2(L) and O2(L), where
#: RocketForge's enthalpy coupling adds exactly no increment, so CEA's assigned enthalpies are used (DB-4C §6). Every
#: point's summary prints the same reactant enthalpies, whatever its card temperatures, so all run with these (§14).
FUEL: tuple[str, float] = ("LH2", 20.27)
OXIDISER: tuple[str, float] = ("LOX", 90.17)

#: Step A: case key -> the oracle's expansion mode. Shifting with shifting, frozen-at-chamber with frozen-at-chamber.
STEP_A_ORACLE_MODES: dict[str, str] = {
    KEY_VACUUM_ISP_EQUILIBRIUM: "equilibrium",
    KEY_VACUUM_ISP_FROZEN: "frozen",
}

#: Step B: (RocketForge gamma basis, oracle expansion mode). Each basis with its matching expansion, both always.
PAIRINGS: tuple[tuple[str, str], ...] = (("frozen", "frozen"), ("equilibrium", "equilibrium"))

#: Declared on every point: what the case is and what its two steps mean (DB-4C §5).
_SHARED: tuple[str, ...] = (
    "source: independent code (TDK, 1985); every step A row is compared, none is judged",
    "step A differences are code and thermodynamic data (TDK 1985 against NASA CEA), plus the input differences "
    "below; never a RocketForge defect",
    "step B differences are RocketForge's constant-gamma, calorically perfect reduction against CEA at the same "
    "point; a model difference, not an error",
    "no row compares RocketForge with the printout directly",
)
_SPECIES = "product species: the source does not print TDK's; CEA runs with the provider's H/O set"


def declarations(point: TdkPoint = CURRENT_DESIGN) -> tuple[str, ...]:
    """Everything a point's result carries, in a fixed order. Nothing is corrected or estimated away."""
    return (
        *_SHARED,
        f"O2(L): the source prints -3102.000 cal/mol at {point.oxidiser_card_temperature} K; run at "
        f"{OXIDISER[1]:g} K with CEA's assigned -12979 J/mol (-3102.055 cal/mol)",
        f"H2(L): the source prints -2154.000 cal/mol at {point.fuel_card_temperature} K; run at {FUEL[1]:g} K "
        "with CEA's assigned -9012 J/mol (-2153.920 cal/mol)",
        f"area ratio: {point.area_ratio:g} as scheduled; the source prints {point.printed_nozzle_area_ratio} "
        "for the nozzle",
        _SPECIES,
        f"chamber pressure: {point.chamber_pressure_psia:g} psia, the stagnation pressure of TDK's rocket problem; "
        f"{point.catalog_link}",
        f"vacuum and frozen-at-chamber conventions: {point.conventions_source}",
    )


@dataclass(frozen=True, slots=True)
class ReductionRow:
    """One step B row: RocketForge's vacuum Isp beside CEA's, both in seconds. No verdict, no tolerance."""

    gamma_basis: str
    oracle_mode: str
    rocketforge_isp_s: float
    cea_isp_s: float
    relative_difference: float | None
    reference: str
    kind: str


@dataclass(frozen=True, slots=True)
class IdealCaseOutcome:
    """Both steps for one point, or what stopped them. ``kind`` says which; nothing is substituted."""

    kind: str
    point: TdkPoint
    chamber_case: Any = None
    step_a: CaseComparison | None = None
    step_b: tuple[ReductionRow, ...] = ()
    declarations: tuple[str, ...] = ()
    message: str = ""
    warnings: tuple[str, ...] = ()

    @property
    def case(self) -> ReferenceCase:
        return self.point.case


def chamber_case(point: TdkPoint = CURRENT_DESIGN) -> Any:
    """The one operating point both steps use, in SI."""
    from .thermochemistry_service import ChamberCase

    pressure_pa = to_canonical(point.chamber_pressure_psia, "psia")[0]
    return ChamberCase(fuel=FUEL[0], oxidiser=OXIDISER[0], oxidiser_fuel_ratio=point.oxidiser_fuel_ratio,
                       chamber_pressure=pressure_pa, fuel_temperature=FUEL[1], oxidiser_temperature=OXIDISER[1])


def _warnings(diagnostics: tuple[Any, ...]) -> tuple[str, ...]:
    return tuple(str(d.message) for d in diagnostics if str(getattr(d, "severity", "")) == "warning")


def run_ideal_case(point: TdkPoint = CURRENT_DESIGN, *, solve_chamber: Callable[[Any], Any] | None = None,
                   solve_expansion: Callable[[Any, Any], Any] | None = None,
                   oracle: Callable[[Any, float, str], Any] | None = None) -> IdealCaseOutcome:
    """Solve one point once and report both steps. The three solvers can be injected so the rules are tested
    with no provider and no real value."""
    # Local on purpose: importing this module must not load the performance chain or a provider.
    from rocketforge.comparison.extract import observed_from_chamber
    from rocketforge.engineering.chamber.handshake import ChamberGammaBasis
    from rocketforge.physics.thermochemistry.types import GammaStrategy

    from .performance_oracle import ORACLE_UNAVAILABLE, oracle_comparison_rows, run_oracle
    from .performance_service import AmbientCondition, AmbientMode, PerformanceCase, solve_performance
    from .thermochemistry_service import OUTCOME_UNAVAILABLE, solve_case

    run = chamber_case(point)
    declared = declarations(point)

    def stopped(kind: str, message: str) -> IdealCaseOutcome:
        return IdealCaseOutcome(kind, point, run, declarations=declared, message=message)

    chamber = (solve_chamber or solve_case)(run)
    if chamber.state is None:
        return stopped(KIND_UNAVAILABLE if chamber.kind == OUTCOME_UNAVAILABLE else KIND_REFUSED,
                       f"chamber: {chamber.message}")
    warnings = list(_warnings(tuple(chamber.diagnostics)))

    oracles: dict[str, Any] = {}
    for mode in sorted({m for _, m in PAIRINGS} | set(STEP_A_ORACLE_MODES.values())):
        outcome = (oracle or run_oracle)(run, point.area_ratio, mode)
        if not outcome.ok:
            return stopped(KIND_UNAVAILABLE if outcome.kind == ORACLE_UNAVAILABLE else KIND_REFUSED,
                           f"CEA {mode} expansion: {outcome.message}")
        oracles[mode] = outcome

    reduced: dict[str, float] = {}
    for basis, _ in PAIRINGS:
        outcome = (solve_expansion or solve_performance)(chamber, PerformanceCase(
            gamma_strategy=GammaStrategy.CHAMBER, gamma_basis=ChamberGammaBasis(basis),
            area_ratio=point.area_ratio, ambient=AmbientCondition(mode=AmbientMode.VACUUM)))
        if outcome.result is None:
            return stopped(KIND_REFUSED, f"{basis} basis: {outcome.message}")
        reduced[basis] = outcome.result.specific_impulse
        warnings += [w for w in _warnings(tuple(outcome.diagnostics)) if w not in warnings]

    observed = {KEY_CHAMBER_TEMPERATURE: observed_from_chamber(chamber.state)[KEY_CHAMBER_TEMPERATURE]}
    for key, mode in STEP_A_ORACLE_MODES.items():
        observed[key] = ObservedQuantity(key, oracles[mode].specific_impulse_vacuum * STANDARD_GRAVITY, "N*s/kg")
    step_a = compare(point.case, observed)

    step_b = []
    for basis, mode in PAIRINGS:
        row = next(r for r in oracle_comparison_rows({"isp_vacuum": reduced[basis]}, oracles[mode])
                   if r["key"] == "isp_vacuum")
        step_b.append(ReductionRow(basis, mode, float(row["rocketforge"]), float(row["provider"]),
                                   row["difference"], row["reference"], row["kind"]))
    return IdealCaseOutcome(KIND_OK, point, run, step_a=step_a, step_b=tuple(step_b), declarations=declared,
                            warnings=tuple(warnings))


def run_ideal_cases(*, solve_chamber: Callable[[Any], Any] | None = None,
                    solve_expansion: Callable[[Any, Any], Any] | None = None,
                    oracle: Callable[[Any, float, str], Any] | None = None) -> tuple[IdealCaseOutcome, ...]:
    """Every point, in :data:`POINTS` order, each on its own: one point's failure does not hide another's result."""
    return tuple(run_ideal_case(point, solve_chamber=solve_chamber, solve_expansion=solve_expansion, oracle=oracle)
                 for point in POINTS)
