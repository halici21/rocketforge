"""Fanno flow: adiabatic constant-area duct flow with wall friction.

Specified in ``docs/engineering/03_compressible_flow_specification.md``
section 8. Steady, one-dimensional, constant area, adiabatic, no shaft work,
calorically perfect gas. No variable area, no heat transfer, no chemistry, no
real-gas behaviour, and no boundary-layer profile model.

**The friction convention, fixed once and stated here.**

    RocketForge uses the FANNING friction factor, and the duct parameter

        4 f_Fanning L / D

    with     f_Darcy = 4 f_Fanning.

Every function in this file that mentions friction means that group and only
that group. :func:`darcy_to_fanning` and :func:`fanning_to_darcy` are the only
sanctioned way to move between conventions, and no relation is written twice to
accommodate the other one. The reference test pinning ``4fL*/D`` at M = 0.5,
gamma = 1.4 to 1.0690603127 exists precisely to catch the factor of four: under
a Darcy reading the same duct reads 0.2672650782.

**Two coincidences worth knowing about, and one trap.** The Fanno sonic state is
reached *by friction*, not isentropically, so it is a different state from the
isentropic A/A* reference. Nonetheless two quantities do coincide exactly, both
because the flow is adiabatic at fixed mass flow:

* ``temperature_ratio(M)`` equals ``isentropic.temperature_ratio_star(M)``,
  since T0 is constant in each case;
* ``stagnation_pressure_ratio(M)`` equals ``isentropic.area_ratio(M)``, since
  p0 A* is constant for a given mass flow and T0.

``p/p*``, ``rho/rho*`` and ``V/V*`` do **not** coincide. The reuse audit asserts
both the equalities and the inequalities, so a later tidy-up cannot quietly
merge the two families.
"""

from __future__ import annotations

import numpy as np

from ...core.errors import DomainError
from ...core.numerics.arrays import (
    as_float_array,
    describe_offender,
    require_above,
    require_finite,
    restore_scalar,
)
from ...core.numerics.roots import brent
from ...core.result import Convergence, Diagnostic, Severity, Solution, Status
from ...core.tolerances import DEFAULT_TOLERANCES, ToleranceSet
from .equations import MODEL_FANNO, REL_FANNO_FRICTION, REL_FANNO_RATIOS
from .gas import PerfectGas
from .types import FannoDuctResult, FannoState, FlowBranch

__all__ = [
    "temperature_ratio",
    "pressure_ratio",
    "density_ratio",
    "stagnation_pressure_ratio",
    "velocity_ratio",
    "friction_parameter",
    "friction_parameter_limit",
    "state",
    "mach_from_friction_parameter",
    "downstream_mach",
    "required_duct_parameter",
    "darcy_to_fanning",
    "fanning_to_darcy",
    "duct_parameter_from_geometry",
    "FannoState",
    "FannoDuctResult",
    "MODEL_FANNO",
]


# ---------------------------------------------------------------------------
# the friction convention, and the only sanctioned way across it
# ---------------------------------------------------------------------------


def darcy_to_fanning(darcy: float) -> float:
    """``f_Fanning = f_Darcy / 4``.

    The one place this division is written. Anywhere else it would be a second
    definition of the convention, and the second one is always the one that
    goes wrong.
    """
    array, was_scalar = as_float_array(darcy, "darcy friction factor")
    require_finite(array, "darcy friction factor")
    return restore_scalar(array / 4.0, was_scalar)


def fanning_to_darcy(fanning: float) -> float:
    """``f_Darcy = 4 f_Fanning``."""
    array, was_scalar = as_float_array(fanning, "fanning friction factor")
    require_finite(array, "fanning friction factor")
    return restore_scalar(4.0 * array, was_scalar)


def duct_parameter_from_geometry(fanning: float, length: float,
                                 hydraulic_diameter: float) -> float:
    """``4 f_Fanning L / D_h`` for a real duct.

    Args:
        fanning: The **Fanning** friction factor, dimensionless. Convert a
            Darcy value with :func:`darcy_to_fanning` first.
        length: Duct length L [m], > 0.
        hydraulic_diameter: D_h [m], > 0. Hydraulic diameter, not diameter:
            nothing here assumes a circular passage.

    The friction factor is *supplied*. Nothing in this module computes one --
    no Colebrook, no Haaland, no Moody chart, no Reynolds number. That belongs
    to a fluid-system module and pretending otherwise here would hide a
    correlation inside a gas-dynamics relation.
    """
    values = {}
    for name, value in (("fanning friction factor", fanning), ("length", length),
                        ("hydraulic diameter", hydraulic_diameter)):
        array, _ = as_float_array(value, name)
        require_finite(array, name)
        require_above(array, 0.0, name)
        values[name] = float(array)
    return (4.0 * values["fanning friction factor"] * values["length"]
            / values["hydraulic diameter"])


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


def _positive_mach(mach: object) -> tuple[np.ndarray, bool]:
    """Validate a Mach number for a Fanno relation.

    M > 0 strictly. Every starred ratio carries a 1/M, so the flow at rest is
    not a limiting case to be evaluated carefully -- it is a state the Fanno
    line does not contain.
    """
    array, was_scalar = as_float_array(mach, "mach")
    require_finite(array, "mach")
    bad = ~(array > 0.0)
    if bad.any():
        raise DomainError(
            "mach must be greater than 0: every Fanno starred ratio diverges at "
            f"rest, and the Fanno line does not reach it; {describe_offender(bad, array)}"
        )
    return array, was_scalar


def _phi(mach: np.ndarray, gamma: float) -> np.ndarray:
    """``phi = 2 + (gamma-1) M^2``, the group every relation shares."""
    return 2.0 + (gamma - 1.0) * mach * mach


# ---------------------------------------------------------------------------
# the starred ratios
# ---------------------------------------------------------------------------


def temperature_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``T/T* = (gamma+1) / [2 + (gamma-1) M^2]``.

    Equal to the isentropic ``T/T*`` at the same Mach number, because the flow
    is adiabatic in both cases and T0 is therefore constant along each. That is
    a documented coincidence, not a shared implementation.
    """
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    return restore_scalar((gamma + 1.0) / _phi(array, gamma), was_scalar)


def pressure_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``p/p* = (1/M) sqrt[(gamma+1) / (2 + (gamma-1) M^2)]``.

    Above 1 subsonic, below 1 supersonic, and 1 at the sonic state. Does *not*
    coincide with the isentropic pressure ratio.
    """
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    return restore_scalar(
        np.sqrt((gamma + 1.0) / _phi(array, gamma)) / array, was_scalar)


def density_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``rho/rho* = (1/M) sqrt[(2 + (gamma-1) M^2) / (gamma+1)]``."""
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    return restore_scalar(
        np.sqrt(_phi(array, gamma) / (gamma + 1.0)) / array, was_scalar)


def velocity_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``V/V* = M sqrt[(gamma+1) / (2 + (gamma-1) M^2)]``.

    The reciprocal of the density ratio, as continuity at constant area
    requires -- and computed as the relation rather than as ``1/rho`` so the
    two can be checked against each other.
    """
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    return restore_scalar(
        array * np.sqrt((gamma + 1.0) / _phi(array, gamma)), was_scalar)


def stagnation_pressure_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``p0/p0* = (1/M) [(2 + (gamma-1) M^2) / (gamma+1)] ^ [(gamma+1)/(2(gamma-1))]``.

    Above 1 on both branches with a minimum of 1 at the sonic state: friction
    is irreversible, so stagnation pressure falls in the direction of flow
    whichever branch the duct is on. Adiabatic does not mean isentropic.

    Numerically equal to the isentropic ``A/A*`` at the same Mach number,
    because p0 A* is constant for a given mass flow and stagnation temperature.
    """
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0))
    return restore_scalar(
        (_phi(array, gamma) / (gamma + 1.0)) ** exponent / array, was_scalar)


def friction_parameter(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``4 f L*/D`` -- the duct still available before the flow chokes.

    ``4 f L*/D = (1 - M^2)/(gamma M^2) + [(gamma+1)/(2 gamma)] ln[(gamma+1)M^2 / phi]``

    with **f the Fanning friction factor**.

    Args:
        mach: Mach number [-], > 0. Scalar or array.
        gas: The gas model; only ``gamma`` is used.

    Returns:
        The *remaining* nondimensional duct length to the sonic state. Zero at
        M = 1, diverging as M -> 0, and approaching a finite limit as M grows --
        see :func:`friction_parameter_limit`.

    It decreases monotonically along the duct on both branches, because both
    branches move towards sonic under friction. That is what makes it the
    natural coordinate for the duct problem: a duct of parameter L consumes L
    of the available length.
    """
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    squared = array * array
    phi = _phi(array, gamma)
    value = ((1.0 - squared) / (gamma * squared)
             + (gamma + 1.0) / (2.0 * gamma) * np.log((gamma + 1.0) * squared / phi))
    # The sonic value is exactly zero, and the expression above is a difference
    # of two terms that individually vanish there; make it exact rather than a
    # few ulp of cancellation, since the duct logic reads its sign.
    value = np.where(np.abs(array - 1.0) <= 0.0, 0.0, value)
    return restore_scalar(value, was_scalar)


def friction_parameter_limit(gas: PerfectGas) -> float:
    """The finite supersonic limit of ``4 f L*/D`` as M -> infinity.

    ``-1/gamma + [(gamma+1)/(2 gamma)] ln[(gamma+1)/(gamma-1)]``

    0.8215081165 for air. A real physical statement rather than a numerical
    convenience: no supersonic Fanno duct longer than this ratio can be run
    without a shock, however fast the inlet flow. It is also the natural upper
    end of the supersonic bracket, and checking a target against it *before*
    bracketing turns what would be a spurious non-convergence into a correct
    physical answer.
    """
    gamma = gas.gamma
    return float(-1.0 / gamma
                 + (gamma + 1.0) / (2.0 * gamma) * np.log((gamma + 1.0) / (gamma - 1.0)))


def state(mach: float, gas: PerfectGas) -> FannoState:
    """Every Fanno ratio at one Mach number, as one record.

    Scalar only: the record describes a single station. Use the individual
    relations for sweeps.
    """
    array, was_scalar = _positive_mach(mach)
    if not was_scalar:
        raise DomainError("state describes a single station; pass a scalar Mach number")
    value = float(array)
    return FannoState(
        mach=value,
        temperature_ratio=float(temperature_ratio(value, gas)),
        pressure_ratio=float(pressure_ratio(value, gas)),
        density_ratio=float(density_ratio(value, gas)),
        stagnation_pressure_ratio=float(stagnation_pressure_ratio(value, gas)),
        velocity_ratio=float(velocity_ratio(value, gas)),
        friction_parameter=float(friction_parameter(value, gas)),
    )


# ---------------------------------------------------------------------------
# the inverse
# ---------------------------------------------------------------------------


def _subsonic_bracket(target: float, gas: PerfectGas,
                      tolerances: ToleranceSet) -> tuple[float, float]:
    """A bracket for the subsonic root, seeded from the small-M asymptote.

    As M -> 0 the parameter behaves as ``1/(gamma M^2)``, so ``M ~ 1/sqrt(gamma L)``
    is a good first guess at the low end. It is then halved while the residual
    has not changed sign, and floored at the model's Mach floor: past that the
    answer is a modelling statement rather than a numerical one.
    """
    gamma = gas.gamma
    low = float(min(1.0 / np.sqrt(gamma * target), 1.0 - tolerances.sonic_margin))
    low = max(low, tolerances.mach_floor)
    while (float(friction_parameter(low, gas)) < target
           and low > tolerances.mach_floor):
        low = max(0.5 * low, tolerances.mach_floor)
    return low, 1.0 - tolerances.sonic_margin


def mach_from_friction_parameter(
    parameter: float,
    gas: PerfectGas,
    branch: FlowBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]:
    """Mach number from ``4 f L*/D`` on an explicitly chosen branch.

    Args:
        parameter: ``4 f L*/D`` [-], >= 0, with f the Fanning friction factor.
        gas: The gas model.
        branch: ``FlowBranch.SUBSONIC`` or ``FlowBranch.SUPERSONIC``. Required,
            with no default: the parameter falls to zero from both sides of the
            sonic point and the equations cannot say which duct is meant.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying the Mach number, or ``NO_SOLUTION`` with a
        ``FANNO_LIMIT`` diagnostic when a supersonic length beyond the finite
        limit is requested.

    Raises:
        DomainError: negative or non-finite parameter, or a non-branch argument.

    Brent on one branch at a time. The subsonic side falls from infinity to
    zero and the supersonic side rises from zero to a finite limit, so each is
    strictly monotone and has exactly one root; the whole range does not.
    """
    array, was_scalar = as_float_array(parameter, "friction parameter")
    if not was_scalar:
        raise DomainError(
            "mach_from_friction_parameter solves one duct; pass a scalar parameter")
    require_finite(array, "friction parameter (4 f L*/D)")
    target = float(array)
    if target < 0.0:
        raise DomainError(
            "friction parameter (4 f L*/D) cannot be negative: it is the duct length "
            f"still available before choking, got {target!r}"
        )
    if not isinstance(branch, FlowBranch):
        raise ValueError(
            f"branch must be a FlowBranch, got {branch!r}. The friction parameter falls "
            "to zero from both sides of the sonic point, so the caller must state which "
            "duct is meant."
        )
    if branch is FlowBranch.BOTH:
        raise ValueError(
            "branch=BOTH is not supported here: the subsonic and supersonic ducts are "
            "different physical problems rather than two roots of one, so call this "
            "once per branch."
        )

    inputs = {"friction_parameter": target, "gamma": gas.gamma, "branch": branch.value}

    if target <= tolerances.fanno_tol:
        # No duct left: the flow is already at the choking state.
        return Solution(
            value=1.0,
            status=Status.OK_WITH_WARNINGS if gas.diagnostics else Status.OK,
            diagnostics=gas.diagnostics + (
                Diagnostic(
                    code="SONIC_EXACT",
                    severity=Severity.INFO,
                    message="4 f L*/D = 0 is the sonic state itself; M = 1 exactly.",
                    field="friction_parameter",
                ),
            ),
            provenance=(REL_FANNO_FRICTION,),
            inputs=inputs,
        )

    if branch is FlowBranch.SUPERSONIC:
        limit = friction_parameter_limit(gas)
        if target > limit - tolerances.fanno_tol:
            return Solution(
                value=None,
                status=Status.NO_SOLUTION,
                diagnostics=gas.diagnostics + (
                    Diagnostic(
                        code="FANNO_LIMIT",
                        severity=Severity.ERROR,
                        message=(
                            f"A supersonic Fanno duct cannot be longer than "
                            f"4 f L*/D = {limit:.10f} at gamma = {gas.gamma:g}, however "
                            f"fast the inlet flow; {target:.10f} was requested. A longer "
                            "duct cannot be run without a shock."
                        ),
                        field="friction_parameter",
                        detail={"friction_parameter": target, "limit": limit},
                    ),
                ),
                provenance=(REL_FANNO_FRICTION,),
                inputs=inputs,
            )
        low, high = 1.0 + tolerances.sonic_margin, tolerances.mach_ceiling
    else:
        low, high = _subsonic_bracket(target, gas, tolerances)

    def residual(mach: float) -> float:
        return float(friction_parameter(mach, gas)) - target

    root, report = brent(
        residual, low, high,
        xtol=tolerances.mach_abs_tol,
        rtol=tolerances.mach_rel_tol,
        max_iter=tolerances.max_iter,
    )

    diagnostics = _near_sonic_diagnostic(root, tolerances)
    if report.converged:
        status = Status.OK_WITH_WARNINGS if diagnostics else Status.OK
    else:
        status = Status.NOT_CONVERGED
        diagnostics = diagnostics + (
            Diagnostic(
                code="NOT_CONVERGED",
                severity=Severity.ERROR,
                message=(
                    f"The Fanno inversion did not converge within {report.iterations} "
                    "iterations; the value returned is the best estimate found and "
                    "should not be used without checking."
                ),
                field="friction_parameter",
                detail={"residual": report.residual, "iterations": float(report.iterations)},
            ),
        )

    solution: Solution[float] = Solution(
        value=root,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_FANNO_FRICTION,),
        convergence=Convergence.from_report(report),
        inputs=inputs,
    )
    return solution.with_diagnostics(*gas.diagnostics)


def _near_sonic_diagnostic(mach: float, tolerances: ToleranceSet) -> tuple[Diagnostic, ...]:
    """Advise when the Mach number is less determined than the duct length.

    ``4 f L*/D`` is quadratic in (M - 1) near sonic, so a relative error eps in
    the length becomes sqrt(eps) in (M - 1). Close to choking a duct a hair
    longer moves the outlet Mach a great deal, which is a real engineering
    statement as much as a numerical one.
    """
    excess = abs(mach - 1.0)
    if excess <= tolerances.sonic_tol or excess >= tolerances.near_sonic_mach:
        return ()
    return (
        Diagnostic(
            code="NEAR_SONIC",
            severity=Severity.WARNING,
            message=(
                "Close to choking the available duct length varies as (M-1)^2, so the "
                "Mach number is less precisely determined than the length it was solved "
                "from: about half the digits carry over."
            ),
            field="friction_parameter",
            detail={"mach": mach},
        ),
    )


# ---------------------------------------------------------------------------
# the duct problem
# ---------------------------------------------------------------------------


def required_duct_parameter(mach1: float, mach2: float, gas: PerfectGas) -> float:
    """The ``4 f L/D`` needed to take the flow from M1 to M2.

    A difference of two closed forms, so no iteration. Both stations must lie
    on the same side of sonic: a continuous constant-area duct cannot carry the
    flow through M = 1.
    """
    first = float(friction_parameter(mach1, gas))
    second = float(friction_parameter(mach2, gas))
    if (float(mach1) - 1.0) * (float(mach2) - 1.0) < 0.0:
        raise DomainError(
            f"M1 = {float(mach1):g} and M2 = {float(mach2):g} are on opposite sides of "
            "the sonic point: a continuous Fanno duct never crosses M = 1, so no duct "
            "length connects them."
        )
    return first - second


def downstream_mach(
    mach1: float,
    duct_parameter: float,
    gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[FannoDuctResult]:
    """Outlet state of a duct of ``4 f L/D``, given the inlet Mach number.

    Args:
        mach1: Inlet Mach number [-], > 0.
        duct_parameter: ``4 f L/D`` of the actual duct [-], >= 0, Fanning.
        gas: The gas model.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying a :class:`FannoDuctResult`, or
        ``NO_SOLUTION`` with a ``FRICTION_CHOKED`` diagnostic when the duct is
        longer than the available length to choking.

    The whole method in three lines: the inlet has ``L_max = 4 f L*/D`` of duct
    available, the real duct consumes ``duct_parameter`` of it, and the outlet
    is whatever Mach number has the remainder still available -- **on the same
    branch**. A subsonic inlet stays subsonic and a supersonic inlet stays
    supersonic, because the Fanno solution does not cross M = 1 inside a
    continuous duct.

    A duct longer than ``L_max`` is a genuine engineering answer rather than a
    failure: the flow chokes, and the upstream condition has to change. It is
    reported as such, with the requested and available lengths both preserved,
    and never as a silently truncated duct or a root found on the other branch.
    """
    inlet_array, was_scalar = _positive_mach(mach1)
    if not was_scalar:
        raise DomainError("downstream_mach solves one duct; pass a scalar Mach number")
    inlet = float(inlet_array)

    array, scalar = as_float_array(duct_parameter, "duct parameter")
    if not scalar:
        raise DomainError("duct_parameter must be a scalar 4 f L/D")
    require_finite(array, "duct parameter (4 f L/D)")
    available_request = float(array)
    if available_request < 0.0:
        raise DomainError(
            "duct parameter (4 f L/D) cannot be negative: friction acts in the "
            f"direction of flow, got {available_request!r}"
        )

    if abs(inlet - 1.0) <= tolerances.sonic_tol:
        raise DomainError(
            "a duct cannot start at M = 1: the flow is already choked there, so any "
            "further length has no solution on either branch"
        )

    branch = FlowBranch.SUBSONIC if inlet < 1.0 else FlowBranch.SUPERSONIC
    maximum = float(friction_parameter(inlet, gas))
    inputs = {"mach1": inlet, "duct_parameter": available_request, "gamma": gas.gamma}

    if available_request > maximum + tolerances.fanno_tol:
        return Solution(
            value=None,
            status=Status.NO_SOLUTION,
            diagnostics=gas.diagnostics + (
                Diagnostic(
                    code="FRICTION_CHOKED",
                    severity=Severity.ERROR,
                    message=(
                        f"The duct is longer than the flow can sustain: 4 f L/D = "
                        f"{available_request:.10f} was requested but only "
                        f"{maximum:.10f} is available before M = 1 at an inlet Mach of "
                        f"{inlet:g}. The flow chokes inside the duct and the upstream "
                        "condition must change; there is no attached solution to report."
                    ),
                    field="duct_parameter",
                    detail={"duct_parameter": available_request,
                            "available": maximum, "mach1": inlet},
                ),
            ),
            provenance=(REL_FANNO_FRICTION,),
            inputs=inputs,
        )

    choked = abs(available_request - maximum) <= tolerances.fanno_tol
    if not choked and available_request <= tolerances.fanno_tol:
        # A duct of no length is the identity, and saying so exactly is better
        # than asking Brent to rediscover the inlet to eleven digits and
        # returning 0.39999999998 for an inlet of 0.4.
        outlet = inlet
        outlet_diagnostics: tuple[Diagnostic, ...] = ()
        convergence = None
    elif choked:
        outlet = 1.0
        outlet_diagnostics = (
            Diagnostic(
                code="SONIC_EXACT",
                severity=Severity.INFO,
                message=(
                    "The duct is exactly the choking length: the flow reaches M = 1 at "
                    "the outlet, and no further length can be added."
                ),
                field="duct_parameter",
            ),
        )
        convergence = None
    else:
        remaining = maximum - available_request
        solution = mach_from_friction_parameter(remaining, gas, branch, tolerances)
        if not solution.ok:
            return Solution(
                value=None,
                status=solution.status,
                diagnostics=solution.diagnostics,
                provenance=(REL_FANNO_FRICTION,),
                inputs=inputs,
            )
        outlet = solution.unwrap()
        outlet_diagnostics = tuple(
            d for d in solution.diagnostics if d.code != "EXTRAPOLATED_GAMMA")
        convergence = solution.convergence

    upstream = state(inlet, gas)
    downstream = state(outlet, gas)
    result = FannoDuctResult(
        upstream=upstream,
        downstream=downstream,
        duct_parameter=available_request,
        remaining_to_choking=downstream.friction_parameter,
        choked=choked,
        pressure_ratio_12=downstream.pressure_ratio / upstream.pressure_ratio,
        temperature_ratio_12=downstream.temperature_ratio / upstream.temperature_ratio,
        stagnation_pressure_ratio_12=(downstream.stagnation_pressure_ratio
                                      / upstream.stagnation_pressure_ratio),
    )

    diagnostics = gas.diagnostics + outlet_diagnostics
    status = Status.OK_WITH_WARNINGS if any(
        d.severity is Severity.WARNING for d in diagnostics) else Status.OK
    return Solution(
        value=result,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_FANNO_RATIOS, REL_FANNO_FRICTION),
        convergence=convergence,
        inputs=inputs,
    )
