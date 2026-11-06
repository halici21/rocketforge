"""DB-4B: which shipped engines may form an engine-level Isp ratio, and running one.

:func:`eligibility` reads the catalog and runs nothing. :func:`run_isp_ratio` solves
one chamber equilibrium and expands it under both gamma bases. Neither writes, neither
draws a verdict, and no test pins a real engine's ratio. The ratio is non-locking: it
is a reading, and no model or rule may change in response to it.

The DB-4A review (:mod:`.reference_engine_regression`) is not relaxed. Its evidence
checks are reused here, and its answer about every quantity stays what it was: an engine
mixture ratio still does not stand for a thrust chamber's. This comparison uses one
openly, says so on the result, and calls itself engine-level.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rocketforge.comparison.engine_isp_ratio import GAMMA_BASES, EngineIspRatio, engine_isp_ratio
from rocketforge.comparison.units import UnitError, to_canonical
from rocketforge.evidence.engines import Assertion, NumberValue
from rocketforge.evidence.engines.capabilities import configuration_assertions
from rocketforge.evidence.engines.vocabulary import (
    MixtureRatioBasis,
    MixtureRatioForm,
    PressureBasis,
    PressureStation,
)

from .reference_engine_catalog import ReferenceEngineCatalog
from .reference_engine_regression import _KNOWN_ENVIRONMENTS, _evidence_blockers, _own, source_semantic

__all__ = ["KIND_OK", "KIND_NOT_ELIGIBLE", "KIND_REFUSED", "KIND_UNAVAILABLE", "PROPELLANTS", "IspRatioInputs",
           "IspRatioEligibility", "IspRatioOutcome", "eligibility", "eligible_configurations", "run_isp_ratio"]

KIND_OK = "ok"
KIND_NOT_ELIGIBLE = "not_eligible"
KIND_REFUSED = "refused"
KIND_UNAVAILABLE = "unavailable"

#: Recorded propellant token -> (model definition, inlet temperature in K). No source prints the inlet state: these
#: are the definitions' normal boiling points, fixed before any ratio was computed. A token not here is refused.
PROPELLANTS: dict[str, tuple[str, float]] = {
    "LIQUID_OXYGEN": ("LOX", 90.17),
    "LIQUID_HYDROGEN": ("LH2", 20.27),
}

_ISP_UNITS = frozenset({"s", "sec"})
_MIXTURE_BASES = frozenset({MixtureRatioBasis.ENGINE, MixtureRatioBasis.THRUST_CHAMBER})
_QUANTITIES = ("specific_impulse", "chamber_pressure", "mixture_ratio", "area_ratio")
_RUNNING = ("specific_impulse", "chamber_pressure", "mixture_ratio")


@dataclass(frozen=True, slots=True)
class IspRatioInputs:
    """What a run takes, each value as its record states it, with pressure in pascals."""

    printed_isp_s: float
    environment: str
    chamber_pressure_pa: float
    oxidiser_fuel_ratio: float
    area_ratio: float
    oxidiser: str
    oxidiser_temperature_k: float
    fuel: str
    fuel_temperature_k: float
    declarations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IspRatioEligibility:
    """Either the inputs, or every reason there are none. Never both."""

    configuration_id: str
    inputs: IspRatioInputs | None
    refusals: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IspRatioOutcome:
    """A ratio, or what stopped it. ``kind`` says which; nothing is substituted."""

    kind: str
    configuration_id: str
    result: EngineIspRatio | None = None
    message: str = ""
    refusals: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def _number(a: Assertion) -> float:
    return float(a.value.value)  # type: ignore[union-attr]  # checked by _evidence_blockers


def _propellant(catalog: ReferenceEngineCatalog, cfg: str, field: str, refusals: list[str]) -> tuple[str, float] | None:
    found = [a for a in configuration_assertions(catalog.corpus, cfg) if a.field_path == field and a.value is not None]
    if len(found) != 1:
        refusals.append(f"{field}: {len(found)} recorded for the configuration; one is needed")
        return None
    token = getattr(found[0].value, "token", None)
    if token not in PROPELLANTS:
        refusals.append(f"{found[0].assertion_id}: propellant {token!r} has no model definition here")
        return None
    return PROPELLANTS[token]


def eligibility(catalog: ReferenceEngineCatalog, cfg: str) -> IspRatioEligibility:
    """Check one configuration against DB-4B §3. Every reason is reported, not only the first."""
    refusals: list[str] = []
    found: dict[str, Assertion] = {}
    for quantity in _QUANTITIES:
        claims = _own(catalog, cfg, quantity)
        if len(claims) != 1:
            refusals.append(f"{quantity}: {len(claims)} recorded for the configuration; this comparison takes one")
            continue
        conflict, rights, semantics = _evidence_blockers(catalog, claims[0])
        refusals += [*conflict, *rights, *semantics]
        found[quantity] = claims[0]

    isp = found.get("specific_impulse")
    if isp is not None:
        if isp.conditions.environment not in _KNOWN_ENVIRONMENTS:
            refusals.append(f"{isp.assertion_id}: environment not stated as vacuum or sea level")
        if isp.unit_as_printed not in _ISP_UNITS:
            refusals.append(f"{isp.assertion_id}: unit {isp.unit_as_printed!r} is not seconds")
        if source_semantic(isp) != "DELIVERED":
            refusals.append(f"{isp.assertion_id}: not a printed engine rating or measurement")

    pressure, pressure_pa = found.get("chamber_pressure"), None
    if pressure is not None:
        if pressure.conditions.pressure_station is not PressureStation.NOZZLE_STAGNATION:
            refusals.append(f"{pressure.assertion_id}: pressure station is not the nozzle stagnation pressure")
        if pressure.conditions.pressure_basis is not PressureBasis.ABSOLUTE:
            refusals.append(f"{pressure.assertion_id}: pressure basis is not absolute")
        if isinstance(pressure.value, NumberValue):
            try:
                pressure_pa = to_canonical(_number(pressure), pressure.unit_as_printed)[0]
            except UnitError as error:
                refusals.append(f"{pressure.assertion_id}: {error}")

    mixture = found.get("mixture_ratio")
    if mixture is not None:
        if mixture.conditions.mixture_ratio_form is not MixtureRatioForm.OXIDIZER_TO_FUEL:
            refusals.append(f"{mixture.assertion_id}: direction O/F is not printed")
        if mixture.conditions.mixture_ratio_basis not in _MIXTURE_BASES:
            refusals.append(f"{mixture.assertion_id}: not stated as an engine or a thrust-chamber ratio")

    points = {found[q].operating_point_id for q in _RUNNING if q in found}
    if len(points) > 1 or None in points:
        refusals.append("Isp, chamber pressure and mixture ratio are not stated at one operating point")

    oxidiser = _propellant(catalog, cfg, "propellants.oxidizer", refusals)
    fuel = _propellant(catalog, cfg, "propellants.fuel", refusals)

    if refusals:
        return IspRatioEligibility(cfg, None, tuple(refusals))
    return IspRatioEligibility(cfg, _inputs(found, pressure_pa, oxidiser, fuel), ())


def _inputs(found: dict[str, Assertion], pressure_pa: float, oxidiser: tuple[str, float],
            fuel: tuple[str, float]) -> IspRatioInputs:
    isp, mixture = found["specific_impulse"], found["mixture_ratio"]
    declarations = (
        "an engine-level ratio, not a thrust-chamber efficiency; a ratio above 1 is not a defect on either side",
        f"Isp basis as recorded: {isp.conditions.isp_basis.value if isp.conditions.isp_basis else 'not recorded'}",
        f"mixture ratio basis as recorded: {mixture.conditions.mixture_ratio_basis.value}; "
        "the model is evaluated at this ratio",
        f"inlet state assumed, not printed: {oxidiser[0]} at {oxidiser[1]:g} K, {fuel[0]} at {fuel[1]:g} K",
        "gamma strategy: chamber; both gamma bases shown because no source prints one",
        "model: NASA CEA HP chamber equilibrium, one constant gamma, frozen ideal nozzle, no losses",
        "values from: " + ", ".join(found[q].assertion_id for q in _QUANTITIES),
    )
    return IspRatioInputs(
        printed_isp_s=_number(isp), environment=isp.conditions.environment.value, chamber_pressure_pa=pressure_pa,
        oxidiser_fuel_ratio=_number(mixture), area_ratio=_number(found["area_ratio"]), oxidiser=oxidiser[0],
        oxidiser_temperature_k=oxidiser[1], fuel=fuel[0], fuel_temperature_k=fuel[1], declarations=declarations)


def eligible_configurations(catalog: ReferenceEngineCatalog) -> tuple[str, ...]:
    """The configurations that pass :func:`eligibility`, in the catalog's order."""
    return tuple(e.configuration_id for e in catalog.entries() if eligibility(catalog, e.configuration_id).inputs)


def _warnings(diagnostics: tuple[Any, ...]) -> tuple[str, ...]:
    return tuple(str(d.message) for d in diagnostics if str(getattr(d, "severity", "")) == "warning")


def run_isp_ratio(catalog: ReferenceEngineCatalog, cfg: str, *, solve_chamber: Callable[[Any], Any] | None = None,
                  solve_expansion: Callable[[Any, Any], Any] | None = None) -> IspRatioOutcome:
    """Solve one chamber, expand it under both gamma bases, and form the ratio. Never raises.

    Both bases or nothing: if either is refused, no ratio is returned, because one basis alone would be
    a pick. Without a provider it reports that and substitutes nothing. The two solvers can be injected so
    the rules can be tested with no provider and no real value.
    """
    # Local on purpose: reading eligibility must not load the performance chain.
    from .performance_service import AmbientCondition, AmbientMode, PerformanceCase, solve_performance
    from .thermochemistry_service import OUTCOME_UNAVAILABLE, ChamberCase, solve_case
    from rocketforge.engineering.chamber.handshake import ChamberGammaBasis
    from rocketforge.physics.thermochemistry.types import GammaStrategy

    checked = eligibility(catalog, cfg)
    if checked.inputs is None:
        return IspRatioOutcome(KIND_NOT_ELIGIBLE, cfg, refusals=checked.refusals)
    inputs = checked.inputs

    chamber = (solve_chamber or solve_case)(ChamberCase(
        fuel=inputs.fuel, oxidiser=inputs.oxidiser, oxidiser_fuel_ratio=inputs.oxidiser_fuel_ratio,
        chamber_pressure=inputs.chamber_pressure_pa, fuel_temperature=inputs.fuel_temperature_k,
        oxidiser_temperature=inputs.oxidiser_temperature_k))
    if chamber.state is None:
        kind = KIND_UNAVAILABLE if chamber.kind == OUTCOME_UNAVAILABLE else KIND_REFUSED
        return IspRatioOutcome(kind, cfg, message=chamber.message)

    mode = AmbientMode.VACUUM if inputs.environment == "VACUUM" else AmbientMode.SEA_LEVEL
    warnings = list(_warnings(tuple(chamber.diagnostics)))
    ideal: dict[str, float] = {}
    for basis in GAMMA_BASES:
        outcome = (solve_expansion or solve_performance)(chamber, PerformanceCase(
            gamma_strategy=GammaStrategy.CHAMBER, gamma_basis=ChamberGammaBasis(basis),
            area_ratio=inputs.area_ratio, ambient=AmbientCondition(mode=mode)))
        if outcome.result is None:
            return IspRatioOutcome(KIND_REFUSED, cfg, message=f"{basis} basis: {outcome.message}")
        ideal[basis] = outcome.result.specific_impulse
        warnings += [w for w in _warnings(tuple(outcome.diagnostics)) if w not in warnings]

    result = engine_isp_ratio(cfg, inputs.printed_isp_s, ideal, inputs.declarations)
    return IspRatioOutcome(KIND_OK, cfg, result=result, warnings=tuple(warnings))
