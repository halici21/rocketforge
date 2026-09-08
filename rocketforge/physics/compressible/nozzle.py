"""Quasi-1D converging-diverging nozzle: regimes, internal shock, distribution.

Specified in ``docs/engineering/03_compressible_flow_specification.md``
section 10. **This module restates no relation.** Every number it produces comes
from :mod:`isentropic`, :mod:`normal_shock` or :mod:`mass_flow`, and the point
of the module is the composition, not the algebra. If a formula from one of
those three appears in this file, that is a defect, and the reuse tests exist to
catch it.

**Assumptions:** steady, quasi-one-dimensional, adiabatic, calorically perfect,
isentropic everywhere except across an infinitely thin normal shock, area
varying slowly enough that the flow is locally one-dimensional.

**What this module is not.** It is fundamental gas dynamics, not rocket nozzle
design (ADR-15). Thrust, Cf, c*, Isp, contour generation, divergence loss,
efficiency factors, film cooling and wall heat transfer are absent by design and
belong to ``engineering/nozzle/``, which will call this module rather than
duplicate it.

**Two levels of access, deliberately separate.**

* *Dimensionless* -- :func:`critical_pressure_ratios`, :func:`classify` and
  :func:`shock_area_ratio` need only Ae/A* and pb/p0. They answer which regime,
  and where the shock sits in area, with no contour at all.
* *Distributed* -- :func:`solve` needs the full A(x) and returns arrays. A shock
  gets a physical position only here, because an area ratio alone fixes the
  shock's area and says nothing about where that area occurs.

**Why the shock is solved in area rather than in x.** Area is the variable the
physics depends on; x enters only through the geometry. Solving in As keeps the
residual smooth even on a coarse or unevenly spaced grid, and it is what makes
the dimensionless API possible. The conversion As -> xs is a monotone
interpolation on the diverging side afterwards, and is the only place where the
geometry resolution matters at all.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from ...core.errors import GeometryError, InputError
from ...core.numerics.roots import brent
from ...core.result import Convergence, Diagnostic, Severity, Solution, Status
from ...core.tolerances import DEFAULT_TOLERANCES, ToleranceSet
from . import isentropic, mass_flow, normal_shock
from .equations import (
    MODEL_NORMAL_SHOCK,
    REL_AREA_RATIO,
    REL_CHOKED_MASS_FLOW,
    REL_MASS_FLOW_PARAMETER,
    REL_NORMAL_SHOCK,
    REL_PRESSURE_RATIO,
    REL_TEMPERATURE_RATIO,
)
from .gas import PerfectGas
from .geometry import AreaDistribution
from .types import (
    CriticalPressureRatios,
    FlowBranch,
    FlowState,
    NozzleOperating,
    NozzleRegime,
    NozzleRegimeResult,
    NozzleSolution,
    ShockLocation,
    StagnationState,
)

__all__ = [
    "critical_pressure_ratios",
    "classify",
    "shock_area_ratio",
    "solve",
    "NozzleRegime",
    "NozzleOperating",
    "CriticalPressureRatios",
    "ShockLocation",
    "NozzleRegimeResult",
    "NozzleSolution",
]

#: The relations a nozzle result is built from. Every one of them belongs to
#: another module: this tuple is the provenance of a composition.
_PROVENANCE = (REL_AREA_RATIO, REL_PRESSURE_RATIO, REL_TEMPERATURE_RATIO,
               REL_NORMAL_SHOCK, REL_MASS_FLOW_PARAMETER, REL_CHOKED_MASS_FLOW)

#: Overexpansion beyond which real nozzles are commonly observed to separate.
#: A *flagging* threshold for a presentation warning, not a prediction: quasi-1D
#: theory says nothing about separation, and the diagnostic says so.
_SEPARATION_FLAG = 0.4


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


def _validate_area_ratio(area_ratio_exit: object) -> float:
    value = float(area_ratio_exit) if np.isscalar(area_ratio_exit) else float("nan")
    if not np.isfinite(value):
        raise GeometryError(
            f"the exit area ratio must be a finite number, got {area_ratio_exit!r}")
    if value < 1.0:
        raise GeometryError(
            f"Ae/A* must be at least 1 for a converging-diverging nozzle, got {value!r}")
    if value == 1.0:
        raise GeometryError(
            "Ae/A* = 1 is a converging nozzle with no diverging section: its "
            "supersonic branch is the sonic point itself, and the three "
            "criticals collapse onto one. A C-D solve needs Ae/A* > 1.")
    return value


def _validate_back_ratio(pressure_ratio_back: object) -> float:
    value = float(pressure_ratio_back) if np.isscalar(pressure_ratio_back) else float("nan")
    if not np.isfinite(value):
        raise InputError(
            f"pb/p0 must be a finite number, got {pressure_ratio_back!r}")
    if value <= 0.0:
        raise InputError(
            f"pb/p0 must be strictly positive, got {value!r}; a perfect vacuum is "
            "the limit of the underexpanded regime, not a member of it")
    if value >= 1.0:
        raise InputError(
            f"pb/p0 must be below 1, got {value!r}. At pb = p0 there is no flow, "
            "and above it the flow would run backwards through the nozzle -- "
            "which this model does not describe.")
    return value


# ---------------------------------------------------------------------------
# the three critical pressure ratios
# ---------------------------------------------------------------------------


@lru_cache(maxsize=256)
def _criticals(ratio: float, gas: PerfectGas,
               tolerances: ToleranceSet) -> tuple[float, float, float, float, float]:
    """The five numbers behind the three criticals, computed once per nozzle.

    Cached because they are a pure function of the area ratio, the gas and the
    tolerances -- and because a back-pressure sweep asks for exactly the same
    three thresholds at every one of its points, each costing two bracketed
    inversions. Caching a pure function changes no answer: determinism requires
    that a result depend on nothing but its arguments, and this depends on
    nothing else.
    """
    subsonic = isentropic.mach_from_area_ratio(
        ratio, gas, FlowBranch.SUBSONIC, tolerances)
    supersonic = isentropic.mach_from_area_ratio(
        ratio, gas, FlowBranch.SUPERSONIC, tolerances)
    mach_sub = float(subsonic.unwrap())
    mach_sup = float(supersonic.unwrap())
    first = float(isentropic.pressure_ratio(mach_sub, gas))
    third = float(isentropic.pressure_ratio(mach_sup, gas))
    second = third * float(normal_shock.pressure_ratio(mach_sup, gas))
    return mach_sub, mach_sup, first, second, third


def critical_pressure_ratios(
    area_ratio_exit: object,
    gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[CriticalPressureRatios]:
    """The three back-pressure thresholds of a C-D nozzle, as pb/p0.

    Each one is the exit pressure of a *different* internal solution:

    ================ =====================================================
    first critical   the throat is exactly sonic and the diverging section
                     is subsonic -- the highest back pressure at which the
                     nozzle chokes
    second critical  a normal shock stands exactly in the exit plane
    third critical   shock-free supersonic expansion, p_e = p_b: design
    ================ =====================================================

    Args:
        area_ratio_exit: Ae/A* [-], above 1.
        gas: The gas model; only gamma is used.
        tolerances: Numerical tolerances.

    Returns:
        ``Solution[CriticalPressureRatios]``.

    Raises:
        GeometryError: Ae/A* below or equal to 1.
    """
    ratio = _validate_area_ratio(area_ratio_exit)

    mach_sub, mach_sup, first, second, third = _criticals(ratio, gas, tolerances)

    diagnostics: tuple[Diagnostic, ...] = ()
    if not third < second < first < 1.0:
        # Not an assertion that can be switched off: a violation means one of
        # the three was computed on the wrong branch, and every regime built on
        # them would be wrong in a way no downstream test would localise.
        diagnostics = (Diagnostic(
            code="CRITICAL_ORDER",
            severity=Severity.ERROR,
            message=(
                "the three critical pressure ratios are out of order: "
                f"third={third!r}, second={second!r}, first={first!r}. They must "
                "satisfy third < second < first < 1 for every valid geometry."),
            detail={"area_ratio_exit": ratio, "gamma": gas.gamma},
        ),)
        return Solution(None, Status.NO_SOLUTION, diagnostics, _PROVENANCE)

    record = CriticalPressureRatios(
        area_ratio_exit=ratio,
        first_critical=first,
        second_critical=second,
        third_critical=third,
        mach_exit_subsonic=mach_sub,
        mach_exit_supersonic=mach_sup,
    )
    return Solution(record, Status.OK, diagnostics, _PROVENANCE)


# ---------------------------------------------------------------------------
# regime classification
# ---------------------------------------------------------------------------


def classify(
    area_ratio_exit: object,
    pressure_ratio_back: object,
    gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[NozzleRegimeResult]:
    """Which regime the nozzle is in, and the exit condition that follows.

    Classification is by *threshold*, never by whether some root solve happened
    to converge, and it is deterministic: the same float64 inputs always give
    the same regime, with no dependence on how finely anything is sampled. The
    supplied back-pressure ratio is carried through untouched -- a value near a
    boundary is classified by the documented tolerance, not clamped onto it.

    Args:
        area_ratio_exit: Ae/A* [-], above 1.
        pressure_ratio_back: pb/p0 [-], in (0, 1).
        gas: The gas model.
        tolerances: Numerical tolerances; ``pressure_tol`` sets the width of a
            boundary regime.

    Returns:
        ``Solution[NozzleRegimeResult]``. The shock field is populated only for
        ``INTERNAL_NORMAL_SHOCK`` and ``SHOCK_AT_EXIT``.
    """
    ratio = _validate_area_ratio(area_ratio_exit)
    back = _validate_back_ratio(pressure_ratio_back)

    criticals = critical_pressure_ratios(ratio, gas, tolerances)
    if criticals.value is None:
        return Solution(None, criticals.status, criticals.diagnostics, _PROVENANCE)
    critical = criticals.value

    first, second, third = (critical.first_critical, critical.second_critical,
                            critical.third_critical)
    # ``04`` section 5 specifies pressure_tol as a *relative* width on the
    # regime boundaries, so each threshold carries its own window rather than
    # one absolute number that would be generous at the first critical and
    # tight at the third.
    tol_first = tolerances.pressure_tol * first
    tol_second = tolerances.pressure_tol * second
    tol_third = tolerances.pressure_tol * third

    diagnostics: list[Diagnostic] = []
    shock: ShockLocation | None = None

    if back > first + tol_first:
        regime = NozzleRegime.UNCHOKED_SUBSONIC
        mach_exit = float(isentropic.mach_from_pressure_ratio(back, gas))
        pressure_ratio_exit = back
        diagnostics.append(Diagnostic(
            code="NOT_CHOKED",
            severity=Severity.INFO,
            message=(
                "The throat is not sonic: the whole nozzle is subsonic and the "
                "exit pressure equals the back pressure. Mass flow depends on "
                "the pressure ratio here, unlike every choked regime."),
            detail={"pressure_ratio_back": back, "first_critical": first},
        ))
    elif abs(back - first) <= tol_first:
        regime = NozzleRegime.CHOKED_SUBSONIC_EXIT
        mach_exit = critical.mach_exit_subsonic
        pressure_ratio_exit = first
    elif back > second + tol_second:
        regime = NozzleRegime.INTERNAL_NORMAL_SHOCK
        located = shock_area_ratio(ratio, back, gas, tolerances)
        if located.value is None:
            return Solution(None, located.status,
                            tuple(diagnostics) + located.diagnostics, _PROVENANCE)
        shock = located.value
        mach_exit = float(isentropic.mach_from_area_ratio(
            ratio / shock.area_star_downstream_ratio, gas,
            FlowBranch.SUBSONIC, tolerances).unwrap())
        pressure_ratio_exit = (float(isentropic.pressure_ratio(mach_exit, gas))
                               * shock.stagnation_pressure_ratio)
        diagnostics.extend(located.diagnostics)
    elif abs(back - second) <= tol_second:
        regime = NozzleRegime.SHOCK_AT_EXIT
        shock = _shock_at_exit(critical, gas, tolerances)
        mach_exit = shock.mach_downstream
        pressure_ratio_exit = second
    elif back > third + tol_third:
        regime = NozzleRegime.OVEREXPANDED
        mach_exit = critical.mach_exit_supersonic
        pressure_ratio_exit = third
        diagnostics.append(Diagnostic(
            code="EXTERNAL_COMPRESSION",
            severity=Severity.INFO,
            message=(
                "The exit pressure is below the back pressure, so the flow is "
                "compressed by oblique shocks standing outside the exit plane. "
                "The internal solution is shock-free and supersonic; the "
                "external wave pattern is not part of this model."),
            detail={"pressure_ratio_exit": third, "pressure_ratio_back": back},
        ))
        if third / back < _SEPARATION_FLAG:
            diagnostics.append(Diagnostic(
                code="MODEL_LIMIT_SEPARATION",
                severity=Severity.WARNING,
                message=(
                    "Substantially overexpanded. Real nozzles at this condition "
                    f"commonly separate from the wall; pe/pb = {third / back:.3f} "
                    "is a rule-of-thumb flag for that, not a prediction. Quasi-1D "
                    "theory contains no separation criterion, and this model does "
                    "not predict whether or where separation occurs."),
                detail={"pressure_ratio_exit_over_back": third / back,
                         "flag_threshold": _SEPARATION_FLAG},
            ))
    elif abs(back - third) <= tol_third:
        regime = NozzleRegime.IDEALLY_EXPANDED
        mach_exit = critical.mach_exit_supersonic
        pressure_ratio_exit = third
    else:
        regime = NozzleRegime.UNDEREXPANDED
        mach_exit = critical.mach_exit_supersonic
        pressure_ratio_exit = third
        diagnostics.append(Diagnostic(
            code="EXTERNAL_EXPANSION",
            severity=Severity.INFO,
            message=(
                "The exit pressure is above the back pressure, so the flow "
                "continues to expand through fans standing off the exit plane. "
                "The internal solution is shock-free and supersonic; the "
                "external plume is not part of this model."),
            detail={"pressure_ratio_exit": third, "pressure_ratio_back": back},
        ))

    near = _near_boundary(back, critical, tolerances.pressure_tol)
    if near is not None:
        diagnostics.append(near)

    record = NozzleRegimeResult(
        regime=regime,
        critical=critical,
        pressure_ratio_back=back,
        mach_exit=mach_exit,
        pressure_ratio_exit=pressure_ratio_exit,
        shock=shock,
    )
    status = (Status.OK_WITH_WARNINGS
              if any(d.severity is Severity.WARNING for d in diagnostics)
              else Status.OK)
    return Solution(record, status, tuple(diagnostics), _PROVENANCE)


def _near_boundary(back: float, critical: CriticalPressureRatios,
                   tol: float) -> Diagnostic | None:
    """Advise when an operating point sits just outside a boundary regime.

    Honest reporting of resolution, not an error: a user who typed a rounded
    number a hair off a threshold should be told that the neighbouring regime
    is within round-off, rather than silently given one side of it.
    """
    for name, value in (("first critical", critical.first_critical),
                        ("second critical", critical.second_critical),
                        ("third critical", critical.third_critical)):
        distance = abs(back - value)
        if tol * value < distance <= tol * value * 1e3:
            return Diagnostic(
                code="NEAR_REGIME_BOUNDARY",
                severity=Severity.INFO,
                message=(
                    f"pb/p0 is within {distance:.2e} of the {name} "
                    f"({value:.10f}); the neighbouring regime is close enough "
                    "that a rounded input could sit on either side."),
                detail={"boundary": name, "value": value, "distance": distance},
            )
    return None


# ---------------------------------------------------------------------------
# internal shock location
# ---------------------------------------------------------------------------


def _shock_state(area_ratio_shock: float, gas: PerfectGas,
                 tolerances: ToleranceSet):
    """The normal shock standing at As/A1*, entirely from other modules."""
    mach_upstream = float(isentropic.mach_from_area_ratio(
        area_ratio_shock, gas, FlowBranch.SUPERSONIC, tolerances).unwrap())
    return mach_upstream, normal_shock.solve(mach_upstream, gas)


def _exit_pressure_ratio_for_shock(area_ratio_shock: float, area_ratio_exit: float,
                                   gas: PerfectGas, tolerances: ToleranceSet) -> float:
    """pe/p01 when a normal shock stands at ``area_ratio_shock``.

    The chain, each step owned by another module: supersonic area-Mach to the
    shock, the normal shock itself, a **new sonic area** A2* = A1*·p01/p02
    downstream, subsonic area-Mach from there to the exit, and the isentropic
    pressure ratio on the reduced stagnation pressure.
    """
    _, shock = _shock_state(area_ratio_shock, gas, tolerances)
    area_star_downstream = shock.area_star_ratio          # A2*/A1* = p01/p02
    mach_exit = float(isentropic.mach_from_area_ratio(
        area_ratio_exit / area_star_downstream, gas,
        FlowBranch.SUBSONIC, tolerances).unwrap())
    return (float(isentropic.pressure_ratio(mach_exit, gas))
            * shock.stagnation_pressure_ratio)


def shock_area_ratio(
    area_ratio_exit: object,
    pressure_ratio_back: object,
    gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[ShockLocation]:
    """Where a normal shock must stand for the exit to match the back pressure.

    The residual is ``F(As/A1*) = pe(As)/p01 - pb/p01``, which is strictly
    decreasing: a shock further downstream sits at a higher area ratio, so it is
    stronger, p02/p01 is smaller, A2* is larger, Ae/A2* is smaller, Me is larger
    and pe is lower. The root is therefore unique, and the bracket needs no
    search because its two ends evaluate exactly to the first and second
    criticals -- so ``F(1+) > 0 > F(Ae/A*)`` for any back pressure strictly
    between them.

    Args:
        area_ratio_exit: Ae/A* [-], above 1.
        pressure_ratio_back: pb/p0 [-], strictly between the second and first
            criticals. Outside that interval there is no internal shock, and
            the returned solution says so rather than producing one.
        gas: The gas model.
        tolerances: Numerical tolerances.

    Returns:
        ``Solution[ShockLocation]`` with ``x = None``: an area ratio alone
        cannot say where that area occurs. :func:`solve` fills x in from a
        supplied geometry.
    """
    ratio = _validate_area_ratio(area_ratio_exit)
    back = _validate_back_ratio(pressure_ratio_back)

    criticals = critical_pressure_ratios(ratio, gas, tolerances)
    if criticals.value is None:
        return Solution(None, criticals.status, criticals.diagnostics, _PROVENANCE)
    critical = criticals.value
    tol_first = tolerances.pressure_tol * critical.first_critical
    tol_second = tolerances.pressure_tol * critical.second_critical

    if (back > critical.first_critical + tol_first
            or back < critical.second_critical - tol_second):
        return Solution(None, Status.NO_SOLUTION, (Diagnostic(
            code="NO_INTERNAL_SHOCK",
            severity=Severity.ERROR,
            message=(
                f"pb/p0 = {back!r} is outside the internal-shock interval "
                f"({critical.second_critical:.10f}, {critical.first_critical:.10f}). "
                "Above it the nozzle is unchoked or just choked; below it the "
                "flow is supersonic to the exit and any adjustment happens "
                "outside the nozzle."),
            detail={"pressure_ratio_back": back,
                     "second_critical": critical.second_critical,
                     "first_critical": critical.first_critical},
        ),), _PROVENANCE)

    # The two endpoint regimes are exact, so they are answered exactly rather
    # than handed to a root finder that would be resolving a degenerate root.
    if abs(back - critical.second_critical) <= tol_second:
        return Solution(_shock_at_exit(critical, gas, tolerances), Status.OK,
                        (Diagnostic(
                            code="SHOCK_AT_EXIT",
                            severity=Severity.INFO,
                            message=("The shock stands exactly in the exit plane; "
                                     "the pre-shock state is the shock-free "
                                     "supersonic exit."),
                            detail={"area_ratio_shock": ratio},
                        ),), _PROVENANCE)

    if abs(back - critical.first_critical) <= tol_first:
        # Choking onset: the supersonic pocket has zero extent. There is no
        # finite shock to place, and pretending otherwise would put a
        # zero-strength shock at the throat as though it were a real one.
        return Solution(None, Status.NO_SOLUTION, (Diagnostic(
            code="NO_INTERNAL_SHOCK",
            severity=Severity.INFO,
            message=(
                "At the first critical the throat is just sonic and the "
                "diverging section is subsonic throughout: the supersonic "
                "pocket has zero extent, so there is no shock to locate."),
            detail={"pressure_ratio_back": back},
        ),), _PROVENANCE)

    def residual(candidate: float) -> float:
        return _exit_pressure_ratio_for_shock(candidate, ratio, gas, tolerances) - back

    lower = 1.0 + tolerances.sonic_margin
    root, report = brent(residual, lower, ratio,
                         xtol=tolerances.area_abs_tol,
                         rtol=tolerances.area_rel_tol,
                         max_iter=tolerances.max_iter)

    mach_upstream, shock = _shock_state(root, gas, tolerances)
    location = ShockLocation(
        area_ratio_shock=root,
        x=None,
        mach_upstream=mach_upstream,
        mach_downstream=shock.mach2,
        pressure_ratio=shock.pressure_ratio,
        stagnation_pressure_ratio=shock.stagnation_pressure_ratio,
        area_star_downstream_ratio=shock.area_star_ratio,
    )
    return Solution(location, Status.OK, (), _PROVENANCE,
                    convergence=Convergence.from_report(report))


def _shock_at_exit(critical: CriticalPressureRatios, gas: PerfectGas,
                   tolerances: ToleranceSet) -> ShockLocation:
    """The exact shock-at-exit state: the supersonic exit, then a normal shock."""
    shock = normal_shock.solve(critical.mach_exit_supersonic, gas)
    return ShockLocation(
        area_ratio_shock=critical.area_ratio_exit,
        x=None,
        mach_upstream=critical.mach_exit_supersonic,
        mach_downstream=shock.mach2,
        pressure_ratio=shock.pressure_ratio,
        stagnation_pressure_ratio=shock.stagnation_pressure_ratio,
        area_star_downstream_ratio=shock.area_star_ratio,
    )




# ---------------------------------------------------------------------------
# the distributed solution
# ---------------------------------------------------------------------------


def _mach_along(area_ratios: np.ndarray, gas: PerfectGas, branch: FlowBranch,
                tolerances: ToleranceSet) -> np.ndarray:
    """Invert the area relation at every station on one branch.

    Delegates to the isentropic module's own array entry point, which loops
    over the scalar solver deliberately: a batched iteration would converge
    element by element at different rates and make a station's answer depend on
    the batch it was computed in, which the determinism rule forbids.
    """
    return isentropic.mach_from_area_ratio_array(
        np.asarray(area_ratios, dtype=float), gas, branch, tolerances)


def _duplicate_station(values: np.ndarray, index: int) -> np.ndarray:
    """Insert a copy of station ``index`` immediately after it."""
    return np.insert(values, index + 1, values[index])


def solve(
    geometry: AreaDistribution,
    operating: NozzleOperating,
    gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[NozzleSolution]:
    """The full distributed quasi-1D solution on the supplied grid.

    The output grid is the caller's own x grid -- no resampling, no smoothing,
    because the caller chose the resolution -- plus one duplicated station when
    a shock exists, carrying the pre-shock state and then the post-shock state
    at the same x.

    Branch assignment is explicit at every station and never guessed:

    ============================ =========================================
    unchoked                     subsonic throughout, referred to a virtual
                                 A\\* smaller than the throat
    choked, shock-free           subsonic to the throat, M = 1 exactly at
                                 it, supersonic after
    choked, internal shock       subsonic, sonic, supersonic to the shock,
                                 then subsonic on the *new* sonic area A2\\*
    ============================ =========================================

    Args:
        geometry: The supplied area distribution. Must be a genuine C-D duct.
        operating: p0, pb and optionally T0.
        gas: The gas model. R is needed for the dimensional arrays.
        tolerances: Numerical tolerances.

    Returns:
        ``Solution[NozzleSolution]``. Dimensional arrays are None together when
        T0 or R is missing, with a diagnostic saying so rather than a fabricated
        reservoir temperature.

    Raises:
        GeometryError: The duct is not converging-diverging.
        InputError: pb/p0 outside (0, 1), or a non-positive pressure.
    """
    if not isinstance(geometry, AreaDistribution):
        raise InputError(
            "solve needs an AreaDistribution; the dimensionless entry points "
            "are critical_pressure_ratios, classify and shock_area_ratio")
    geometry.require_converging_diverging()

    for name, value in (("stagnation_pressure", operating.stagnation_pressure),
                        ("back_pressure", operating.back_pressure)):
        if not np.isfinite(value) or value <= 0.0:
            raise InputError(f"{name} must be finite and positive, got {value!r}")
    if operating.stagnation_temperature is not None:
        if (not np.isfinite(operating.stagnation_temperature)
                or operating.stagnation_temperature <= 0.0):
            raise InputError(
                "stagnation_temperature must be finite and positive, got "
                f"{operating.stagnation_temperature!r}")

    area_ratio_exit = geometry.area_ratio_exit
    back = _validate_back_ratio(operating.pressure_ratio_back)

    classified = classify(area_ratio_exit, back, gas, tolerances)
    if classified.value is None:
        return Solution(None, classified.status, classified.diagnostics, _PROVENANCE)
    regime_result = classified.value
    regime = regime_result.regime
    diagnostics = list(classified.diagnostics)

    throat_index = geometry.throat_index
    area = np.array(geometry.area, dtype=float)
    x = np.array(geometry.x, dtype=float)
    throat_area = geometry.throat_area

    shock: ShockLocation | None = None
    shock_index: int | None = None

    if regime is NozzleRegime.UNCHOKED_SUBSONIC:
        # The exit is matched directly to the back pressure, because a subsonic
        # exit can communicate with the downstream reservoir. The sonic area
        # that follows is virtual and smaller than the throat -- continuing to
        # use the throat here is the classic error, and it produces a throat
        # Mach number of exactly 1 in a regime where the throat is not sonic.
        mach_exit = float(isentropic.mach_from_pressure_ratio(back, gas))
        area_star = geometry.exit_area / float(isentropic.area_ratio(mach_exit, gas))
        mach = _mach_along(area / area_star, gas, FlowBranch.SUBSONIC, tolerances)
        mach[-1] = mach_exit
        stagnation_ratio = np.ones(mach.size, dtype=float)
        choked = False

    elif regime is NozzleRegime.CHOKED_SUBSONIC_EXIT:
        area_star = throat_area
        mach = _mach_along(area / area_star, gas, FlowBranch.SUBSONIC, tolerances)
        mach[throat_index] = 1.0
        stagnation_ratio = np.ones(mach.size, dtype=float)
        choked = True

    elif regime in (NozzleRegime.INTERNAL_NORMAL_SHOCK, NozzleRegime.SHOCK_AT_EXIT):
        area_star = throat_area
        shock = regime_result.shock
        assert shock is not None            # guaranteed by classify for these two
        shock_area = shock.area_ratio_shock * throat_area
        shock_x = geometry.x_at_area(shock_area, side="diverging")
        shock = ShockLocation(
            area_ratio_shock=shock.area_ratio_shock,
            x=shock_x,
            mach_upstream=shock.mach_upstream,
            mach_downstream=shock.mach_downstream,
            pressure_ratio=shock.pressure_ratio,
            stagnation_pressure_ratio=shock.stagnation_pressure_ratio,
            area_star_downstream_ratio=shock.area_star_downstream_ratio,
        )

        # Insert the shock station itself, then duplicate it: one sample either
        # side of the discontinuity, sharing an x. 03 section 10.8.
        insert_at = int(np.searchsorted(x, shock_x, side="left"))
        insert_at = max(throat_index + 1, min(insert_at, x.size))
        if insert_at < x.size and np.isclose(x[insert_at], shock_x, rtol=0.0,
                                             atol=1e-15 * max(1.0, abs(shock_x))):
            shock_index = insert_at
        else:
            x = np.insert(x, insert_at, shock_x)
            area = np.insert(area, insert_at, shock_area)
            shock_index = insert_at
        x = _duplicate_station(x, shock_index)
        area = _duplicate_station(area, shock_index)

        area_star_downstream = throat_area * shock.area_star_downstream_ratio
        mach = np.empty(x.size, dtype=float)
        stagnation_ratio = np.empty(x.size, dtype=float)

        upstream = slice(0, shock_index + 1)
        downstream = slice(shock_index + 1, x.size)

        converging = slice(0, throat_index + 1)
        supersonic = slice(throat_index, shock_index + 1)
        mach[converging] = _mach_along(area[converging] / area_star, gas,
                                       FlowBranch.SUBSONIC, tolerances)
        mach[supersonic] = _mach_along(area[supersonic] / area_star, gas,
                                       FlowBranch.SUPERSONIC, tolerances)
        mach[throat_index] = 1.0
        mach[shock_index] = shock.mach_upstream
        mach[downstream] = _mach_along(area[downstream] / area_star_downstream, gas,
                                       FlowBranch.SUBSONIC, tolerances)
        mach[shock_index + 1] = shock.mach_downstream

        stagnation_ratio[upstream] = 1.0
        stagnation_ratio[downstream] = shock.stagnation_pressure_ratio
        choked = True

    else:   # OVEREXPANDED, IDEALLY_EXPANDED, UNDEREXPANDED
        # One internal solution for all three: they differ only outside the
        # exit plane. A test asserts the three produce identical arrays.
        area_star = throat_area
        mach = np.empty(x.size, dtype=float)
        converging = slice(0, throat_index + 1)
        diverging = slice(throat_index, x.size)
        mach[converging] = _mach_along(area[converging] / area_star, gas,
                                       FlowBranch.SUBSONIC, tolerances)
        mach[diverging] = _mach_along(area[diverging] / area_star, gas,
                                      FlowBranch.SUPERSONIC, tolerances)
        mach[throat_index] = 1.0
        stagnation_ratio = np.ones(mach.size, dtype=float)
        choked = True

    # -- ratios, which gamma alone supplies --------------------------------
    area_ratio = area / throat_area
    pressure_ratio = np.asarray(isentropic.pressure_ratio(mach, gas)) * stagnation_ratio
    temperature_ratio = np.asarray(isentropic.temperature_ratio(mach, gas))

    # -- dimensional fill-in, only when the reservoir is fully known -------
    p0 = operating.stagnation_pressure
    t0 = operating.stagnation_temperature
    has_dimensional = t0 is not None and gas.gas_constant is not None
    if not has_dimensional:
        diagnostics.append(Diagnostic(
            code="DIMENSIONLESS_ONLY",
            severity=Severity.INFO,
            message=(
                "T0 or the gas constant was not supplied, so temperature, "
                "density, velocity and mass flow are not computed. The ratios "
                "and the regime need only gamma and are unaffected."),
            field="stagnation_temperature",
        ))
        pressure = temperature = density = sound = velocity = None
        stagnation_pressure_dim = stagnation_temperature_dim = None
        mass_flow_rate = None
    else:
        pressure = pressure_ratio * p0
        temperature = temperature_ratio * t0
        density = pressure / (gas.gas_constant * temperature)
        sound = np.asarray(gas.speed_of_sound(temperature))
        velocity = mach * sound
        stagnation_pressure_dim = stagnation_ratio * p0
        # Adiabatic: T0 is constant everywhere, shock included. Filled with the
        # supplied value rather than recomputed, so it cannot drift.
        stagnation_temperature_dim = np.full(mach.size, float(t0))
        mass_flow_rate = (
            mass_flow.choked_mass_flow(gas, throat_area, p0, t0) if choked
            else float(mass_flow.mass_flow(mach[throat_index], gas, throat_area, p0, t0)))

    def station(index: int) -> FlowState:
        return FlowState(
            mach=float(mach[index]),
            gas=gas,
            pressure=None if pressure is None else float(pressure[index]),
            temperature=None if temperature is None else float(temperature[index]),
            density=None if density is None else float(density[index]),
            stagnation=StagnationState(
                stagnation_pressure=float(stagnation_ratio[index] * p0),
                stagnation_temperature=None if t0 is None else float(t0),
            ),
        )

    record = NozzleSolution(
        regime=regime,
        critical=regime_result.critical,
        shock=shock,
        choked=choked,
        mass_flow=mass_flow_rate,
        throat=station(throat_index),
        exit=station(x.size - 1),
        x=x,
        area=area,
        area_ratio=area_ratio,
        mach=mach,
        pressure_ratio=pressure_ratio,
        temperature_ratio=temperature_ratio,
        stagnation_pressure_ratio=stagnation_ratio,
        pressure=pressure,
        temperature=temperature,
        density=density,
        speed_of_sound=sound,
        velocity=velocity,
        stagnation_pressure=stagnation_pressure_dim,
        stagnation_temperature=stagnation_temperature_dim,
        shock_index=shock_index,
        throat_index=throat_index,
    )
    status = (Status.OK_WITH_WARNINGS
              if any(d.severity is Severity.WARNING for d in diagnostics)
              else Status.OK)
    return Solution(record, status, tuple(diagnostics), _PROVENANCE,
                    convergence=classified.convergence)
