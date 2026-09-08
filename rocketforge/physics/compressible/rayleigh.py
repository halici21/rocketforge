"""Rayleigh flow: frictionless constant-area duct flow with heat exchange.

Specified in ``docs/engineering/03_compressible_flow_specification.md``
section 9. Steady, one-dimensional, constant area, frictionless, no shaft work,
calorically perfect gas. Heat transfer enters only through the classical state
relation: there is no combustion model, no chemistry, no radiation and no
finite-rate transfer.

**This is the one family in the module whose behaviour is genuinely
counter-intuitive, and the module refuses to tidy it up.**

* ``T0/T0*`` has its maximum of exactly 1 at M = 1. Heat addition therefore
  drives *both* branches towards sonic, and the sonic state is the thermal
  choking limit.
* ``T/T*`` has its maximum at **M = 1/sqrt(gamma)**, not at M = 1, with the
  value (gamma+1)^2/(4 gamma) -- 1.0285714286 for air, at M = 0.8451542547.
* Between those two Mach numbers the static temperature *falls while heat is
  being added*. That is correct: the flow is accelerating fast enough there
  that the kinetic-energy rise exceeds the heat put in. A test pins it, because
  a later tidy-up might otherwise be tempted to make T/T* monotone.
* ``p0/p0*`` exceeds 1 on both sides with a minimum of 1 at sonic: heat
  addition always destroys stagnation pressure, on either branch.

**No coincidence with the isentropic or Fanno families.** Every Rayleigh
starred ratio differs from its counterpart -- including T/T*, which here is
M^2[(gamma+1)/(1+gamma M^2)]^2 while the isentropic and Fanno families share
(gamma+1)/(2+(gamma-1)M^2). A test asserts the difference, guarding against a
copy-paste between the modules.
"""

from __future__ import annotations

import numpy as np

from ...core.errors import DomainError, MissingGasConstantError
from ...core.numerics.arrays import (
    as_float_array,
    describe_offender,
    require_finite,
    restore_scalar,
)
from ...core.numerics.roots import brent
from ...core.result import Convergence, Diagnostic, Severity, Solution, Status
from ...core.tolerances import DEFAULT_TOLERANCES, ToleranceSet
from .equations import MODEL_RAYLEIGH, REL_RAYLEIGH_RATIOS, REL_RAYLEIGH_STAGNATION
from .gas import PerfectGas
from .types import FlowBranch, RayleighDuctResult, RayleighState

__all__ = [
    "temperature_ratio",
    "pressure_ratio",
    "density_ratio",
    "stagnation_temperature_ratio",
    "stagnation_pressure_ratio",
    "mach_at_maximum_temperature",
    "maximum_temperature_ratio",
    "stagnation_temperature_ratio_limit",
    "state",
    "mach_from_stagnation_temperature_ratio",
    "heat_addition",
    "specific_heat_addition",
    "RayleighState",
    "RayleighDuctResult",
    "MODEL_RAYLEIGH",
]


def _positive_mach(mach: object) -> tuple[np.ndarray, bool]:
    """Validate a Mach number for a Rayleigh relation.

    M > 0 strictly: ``rho/rho*`` carries a 1/M^2, so the flow at rest is not a
    limiting case but a state the Rayleigh line does not contain.
    """
    array, was_scalar = as_float_array(mach, "mach")
    require_finite(array, "mach")
    bad = ~(array > 0.0)
    if bad.any():
        raise DomainError(
            "mach must be greater than 0: the Rayleigh density ratio diverges at rest "
            f"and the line does not reach it; {describe_offender(bad, array)}"
        )
    return array, was_scalar


# ---------------------------------------------------------------------------
# the starred ratios
# ---------------------------------------------------------------------------


def pressure_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``p/p* = (gamma+1) / (1 + gamma M^2)``.

    Strictly decreasing on the whole domain, which is what makes it the one
    Rayleigh ratio that would be easy to invert -- and the specification still
    defers that inverse, because it is not how a Rayleigh problem is posed.
    """
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    return restore_scalar((gamma + 1.0) / (1.0 + gamma * array * array), was_scalar)


def temperature_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``T/T* = M^2 [(gamma+1) / (1 + gamma M^2)]^2``.

    **Not monotone.** It rises to a maximum at M = 1/sqrt(gamma) and falls
    thereafter, so a value below the maximum has two subsonic roots. See
    :func:`mach_at_maximum_temperature`.
    """
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    ratio = (gamma + 1.0) / (1.0 + gamma * array * array)
    return restore_scalar(array * array * ratio * ratio, was_scalar)


def density_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``rho/rho* = (1/M^2) (1 + gamma M^2) / (gamma+1)``."""
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    return restore_scalar(
        (1.0 + gamma * array * array) / ((gamma + 1.0) * array * array), was_scalar)


def stagnation_temperature_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``T0/T0* = (gamma+1) M^2 [2 + (gamma-1) M^2] / (1 + gamma M^2)^2``.

    The heat-addition coordinate, and the one that matters most: it rises to
    exactly 1 at M = 1 from both sides, so adding heat drives either branch
    towards sonic and the sonic state is the thermal choking limit.
    """
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    squared = array * array
    denominator = 1.0 + gamma * squared
    value = ((gamma + 1.0) * squared * (2.0 + (gamma - 1.0) * squared)
             / (denominator * denominator))
    return restore_scalar(value, was_scalar)


def stagnation_pressure_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """``p0/p0* = [(gamma+1)/(1 + gamma M^2)] [(2 + (gamma-1)M^2)/(gamma+1)]^(gamma/(gamma-1))``.

    Above 1 on both sides with a minimum of exactly 1 at sonic. Heat addition
    therefore always costs stagnation pressure, whichever branch the duct is on:
    the Rayleigh loss.
    """
    array, was_scalar = _positive_mach(mach)
    gamma = gas.gamma
    squared = array * array
    exponent = gamma / (gamma - 1.0)
    value = ((gamma + 1.0) / (1.0 + gamma * squared)
             * ((2.0 + (gamma - 1.0) * squared) / (gamma + 1.0)) ** exponent)
    return restore_scalar(value, was_scalar)


# ---------------------------------------------------------------------------
# the two critical points, which are not the same point
# ---------------------------------------------------------------------------


def mach_at_maximum_temperature(gas: PerfectGas) -> float:
    """The Mach number of maximum **static** temperature: ``1/sqrt(gamma)``.

    0.8451542547 for air -- subsonic, and distinctly not the sonic state. This
    is the single most instructive feature of the Rayleigh line, and the reason
    the module refuses to describe heat addition as "temperature rises".
    """
    return float(1.0 / np.sqrt(gas.gamma))


def maximum_temperature_ratio(gas: PerfectGas) -> float:
    """The value of ``T/T*`` at that maximum: ``(gamma+1)^2 / (4 gamma)``.

    1.0285714286 for air, which is exactly 36/35.
    """
    gamma = gas.gamma
    return float((gamma + 1.0) ** 2 / (4.0 * gamma))


def stagnation_temperature_ratio_limit(gas: PerfectGas) -> float:
    """The supersonic limit of ``T0/T0*`` as M -> infinity: ``(gamma^2 - 1)/gamma^2``.

    0.4897959184 for air. Finite, so a supersonic Rayleigh flow can only be
    *cooled* so far, and a request below it has no solution on that branch.
    """
    gamma = gas.gamma
    return float((gamma * gamma - 1.0) / (gamma * gamma))


def state(mach: float, gas: PerfectGas) -> RayleighState:
    """Every Rayleigh ratio at one Mach number, as one record."""
    array, was_scalar = _positive_mach(mach)
    if not was_scalar:
        raise DomainError("state describes a single station; pass a scalar Mach number")
    value = float(array)
    return RayleighState(
        mach=value,
        temperature_ratio=float(temperature_ratio(value, gas)),
        pressure_ratio=float(pressure_ratio(value, gas)),
        density_ratio=float(density_ratio(value, gas)),
        stagnation_temperature_ratio=float(stagnation_temperature_ratio(value, gas)),
        stagnation_pressure_ratio=float(stagnation_pressure_ratio(value, gas)),
    )


# ---------------------------------------------------------------------------
# the one inverse the specification approves
# ---------------------------------------------------------------------------


def mach_from_stagnation_temperature_ratio(
    ratio: float,
    gas: PerfectGas,
    branch: FlowBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]:
    """Mach number from ``T0/T0*`` on an explicitly chosen branch.

    Args:
        ratio: ``T0/T0*`` [-], in (0, 1].
        gas: The gas model.
        branch: ``FlowBranch.SUBSONIC`` or ``FlowBranch.SUPERSONIC``. Required:
            the ratio rises to 1 from both sides, so every attainable value has
            a subsonic and a supersonic root and the equations cannot say which
            duct is meant.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying the Mach number, ``NO_SOLUTION`` with
        ``THERMALLY_CHOKED`` above 1, or ``NO_SOLUTION`` with ``RAYLEIGH_LIMIT``
        below the finite supersonic floor.

    **This is the only Rayleigh inverse implemented.** ``T/T*`` is deliberately
    *not* invertible here: it is not monotone on the subsonic branch, so a
    value below its maximum has two subsonic roots either side of
    1/sqrt(gamma). Inverting it needs a three-way interval selector rather than
    the two-way branch, which is more interface than the question earns; the
    specification defers it with that reason recorded, and this module does not
    add it casually just because a root finder is available.

    Both brackets are closed form. The subsonic side rises from 0 at rest to 1
    at sonic, and the supersonic side falls from 1 to the finite limit -- so
    neither needs a bracket search, and checking the target against that limit
    *before* bracketing turns what would be a spurious non-convergence into a
    correct physical answer.
    """
    array, was_scalar = as_float_array(ratio, "stagnation temperature ratio")
    if not was_scalar:
        raise DomainError(
            "mach_from_stagnation_temperature_ratio solves one station; pass a scalar")
    require_finite(array, "stagnation temperature ratio (T0/T0*)")
    target = float(array)
    if target <= 0.0:
        raise DomainError(
            "stagnation temperature ratio (T0/T0*) must be greater than 0, got "
            f"{target!r}"
        )
    if not isinstance(branch, FlowBranch):
        raise ValueError(
            f"branch must be a FlowBranch, got {branch!r}. T0/T0* rises to 1 from both "
            "sides of the sonic point, so the caller must state which duct is meant."
        )
    if branch is FlowBranch.BOTH:
        raise ValueError(
            "branch=BOTH is not supported here: a subsonic and a supersonic duct are "
            "different physical problems, so call this once per branch."
        )

    inputs = {"stagnation_temperature_ratio": target, "gamma": gas.gamma,
              "branch": branch.value}

    if target > 1.0 + tolerances.rayleigh_tol:
        return Solution(
            value=None,
            status=Status.NO_SOLUTION,
            diagnostics=gas.diagnostics + (
                Diagnostic(
                    code="THERMALLY_CHOKED",
                    severity=Severity.ERROR,
                    message=(
                        f"T0/T0* cannot exceed 1: the sonic state carries the maximum "
                        f"stagnation temperature on a Rayleigh line, and {target:.10f} "
                        "was requested. Adding that much heat chokes the flow and the "
                        "upstream condition must change."
                    ),
                    field="stagnation_temperature_ratio",
                    detail={"requested": target, "maximum": 1.0},
                ),
            ),
            provenance=(REL_RAYLEIGH_STAGNATION,),
            inputs=inputs,
        )

    if abs(target - 1.0) <= tolerances.rayleigh_tol:
        return Solution(
            value=1.0,
            status=Status.OK_WITH_WARNINGS if gas.diagnostics else Status.OK,
            diagnostics=gas.diagnostics + (
                Diagnostic(
                    code="SONIC_EXACT",
                    severity=Severity.INFO,
                    message="T0/T0* = 1 is the thermal choking state; M = 1 exactly.",
                    field="stagnation_temperature_ratio",
                ),
            ),
            provenance=(REL_RAYLEIGH_STAGNATION,),
            inputs=inputs,
        )

    if branch is FlowBranch.SUPERSONIC:
        limit = stagnation_temperature_ratio_limit(gas)
        if target < limit + tolerances.rayleigh_tol:
            return Solution(
                value=None,
                status=Status.NO_SOLUTION,
                diagnostics=gas.diagnostics + (
                    Diagnostic(
                        code="RAYLEIGH_LIMIT",
                        severity=Severity.ERROR,
                        message=(
                            f"A supersonic Rayleigh flow cannot be cooled below "
                            f"T0/T0* = {limit:.10f} at gamma = {gas.gamma:g}, however "
                            f"fast it runs; {target:.10f} was requested."
                        ),
                        field="stagnation_temperature_ratio",
                        detail={"requested": target, "limit": limit},
                    ),
                ),
                provenance=(REL_RAYLEIGH_STAGNATION,),
                inputs=inputs,
            )
        low, high = 1.0 + tolerances.sonic_margin, tolerances.mach_ceiling
    else:
        low, high = tolerances.mach_floor, 1.0 - tolerances.sonic_margin

    def residual(mach: float) -> float:
        return float(stagnation_temperature_ratio(mach, gas)) - target

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
                    f"The Rayleigh inversion did not converge within {report.iterations} "
                    "iterations; the value returned is the best estimate found and "
                    "should not be used without checking."
                ),
                field="stagnation_temperature_ratio",
                detail={"residual": report.residual, "iterations": float(report.iterations)},
            ),
        )

    solution: Solution[float] = Solution(
        value=root,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_RAYLEIGH_STAGNATION,),
        convergence=Convergence.from_report(report),
        inputs=inputs,
    )
    return solution.with_diagnostics(*gas.diagnostics)


def _near_sonic_diagnostic(mach: float, tolerances: ToleranceSet) -> tuple[Diagnostic, ...]:
    """Advise when the Mach number is less determined than the heat.

    ``1 - T0/T0*`` goes as [4/(gamma+1)^2](M-1)^2 near sonic, so a relative
    error eps in the stagnation-temperature ratio becomes sqrt(eps) in (M-1).
    Close to thermal choking, a little more heat moves the outlet Mach a great
    deal -- a real engineering statement as much as a numerical one.
    """
    excess = abs(mach - 1.0)
    if excess <= tolerances.sonic_tol or excess >= tolerances.near_sonic_mach:
        return ()
    return (
        Diagnostic(
            code="NEAR_SONIC",
            severity=Severity.WARNING,
            message=(
                "Close to thermal choking T0/T0* varies as (M-1)^2, so the Mach number "
                "is less precisely determined than the heat it was solved from: about "
                "half the digits carry over."
            ),
            field="stagnation_temperature_ratio",
            detail={"mach": mach},
        ),
    )


# ---------------------------------------------------------------------------
# the duct problem
# ---------------------------------------------------------------------------


def specific_heat_addition(mach1: float, mach2: float, gas: PerfectGas,
                           stagnation_temperature_1: float) -> float:
    """``q = cp (T02 - T01)`` [J/kg] between two stations on a Rayleigh line.

    Args:
        mach1: Inlet Mach number.
        mach2: Outlet Mach number.
        gas: The gas model; ``cp`` is taken from it and is not recomputed here.
        stagnation_temperature_1: T01 [K], > 0.

    Imposed heat transfer, and nothing more: no combustion, no reaction, no
    species. Positive for heating and negative for cooling.
    """
    if gas.gas_constant is None:
        raise MissingGasConstantError(
            "a heat per unit mass needs cp, which needs the specific gas constant R; "
            "construct the PerfectGas with one"
        )
    array, was_scalar = as_float_array(stagnation_temperature_1, "stagnation temperature")
    require_finite(array, "stagnation temperature")
    if not was_scalar or float(array) <= 0.0:
        raise DomainError(
            "stagnation temperature must be a positive scalar in kelvin, got "
            f"{stagnation_temperature_1!r}"
        )
    first = float(stagnation_temperature_ratio(mach1, gas))
    second = float(stagnation_temperature_ratio(mach2, gas))
    t01 = float(array)
    # T02/T01 is the ratio of the two starred ratios: T0* is common to both.
    t02 = t01 * second / first
    return float(gas.cp * (t02 - t01))


def heat_addition(
    mach1: float,
    stagnation_temperature_ratio_12: float,
    gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[RayleighDuctResult]:
    """Outlet state after heating (or cooling) a duct, given ``T02/T01``.

    Args:
        mach1: Inlet Mach number [-], > 0.
        stagnation_temperature_ratio_12: ``T02/T01`` [-], > 0. Above 1 is
            heating, below 1 is cooling.
        gas: The gas model.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying a :class:`RayleighDuctResult`, or
        ``NO_SOLUTION`` with ``THERMALLY_CHOKED`` when the heat requested would
        take the flow past sonic.

    Three lines again: the inlet sits at ``T01/T0*``, the heat multiplies it to
    ``T02/T0*``, and the outlet is whatever Mach number has that value -- **on
    the same branch**. A subsonic inlet stays subsonic and a supersonic inlet
    stays supersonic; the Rayleigh solution does not cross M = 1 inside a
    continuous duct.

    Heat beyond the choking limit is a real engineering answer rather than a
    failure: the flow chokes and the upstream condition must change. The
    requested ratio is preserved in the diagnostic beside the maximum, and is
    never silently clamped to the sonic value.
    """
    inlet_array, was_scalar = _positive_mach(mach1)
    if not was_scalar:
        raise DomainError("heat_addition solves one duct; pass a scalar Mach number")
    inlet = float(inlet_array)

    array, scalar = as_float_array(stagnation_temperature_ratio_12,
                                   "stagnation temperature ratio")
    if not scalar:
        raise DomainError("stagnation_temperature_ratio_12 must be a scalar T02/T01")
    require_finite(array, "stagnation temperature ratio (T02/T01)")
    requested = float(array)
    if requested <= 0.0:
        raise DomainError(
            "stagnation temperature ratio (T02/T01) must be greater than 0, got "
            f"{requested!r}"
        )

    if abs(inlet - 1.0) <= tolerances.sonic_tol:
        raise DomainError(
            "a duct cannot start at M = 1: the flow is already thermally choked there, "
            "so any further heat has no solution on either branch"
        )

    branch = FlowBranch.SUBSONIC if inlet < 1.0 else FlowBranch.SUPERSONIC
    inlet_ratio = float(stagnation_temperature_ratio(inlet, gas))
    outlet_ratio = inlet_ratio * requested
    maximum_ratio = 1.0 / inlet_ratio
    inputs = {"mach1": inlet, "stagnation_temperature_ratio_12": requested,
              "gamma": gas.gamma}

    if outlet_ratio > 1.0 + tolerances.rayleigh_tol:
        return Solution(
            value=None,
            status=Status.NO_SOLUTION,
            diagnostics=gas.diagnostics + (
                Diagnostic(
                    code="THERMALLY_CHOKED",
                    severity=Severity.ERROR,
                    message=(
                        f"That much heat would choke the flow: T02/T01 = {requested:.10f} "
                        f"was requested, but only {maximum_ratio:.10f} can be added "
                        f"before M = 1 at an inlet Mach of {inlet:g}. The flow chokes "
                        "inside the duct and the upstream condition must change; there "
                        "is no downstream state to report."
                    ),
                    field="stagnation_temperature_ratio_12",
                    detail={"requested": requested, "maximum": maximum_ratio,
                            "mach1": inlet},
                ),
            ),
            provenance=(REL_RAYLEIGH_STAGNATION,),
            inputs=inputs,
        )

    choked = abs(outlet_ratio - 1.0) <= tolerances.rayleigh_tol
    if not choked and abs(requested - 1.0) <= tolerances.rayleigh_tol:
        # No heat is the identity, and saying so exactly beats asking Brent to
        # rediscover the inlet to eleven digits.
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
                    "Exactly the choking heat: the flow reaches M = 1 at the outlet, "
                    "and no further heat can be added."
                ),
                field="stagnation_temperature_ratio_12",
            ),
        )
        convergence = None
    else:
        solution = mach_from_stagnation_temperature_ratio(
            outlet_ratio, gas, branch, tolerances)
        if not solution.ok:
            return Solution(
                value=None,
                status=solution.status,
                diagnostics=solution.diagnostics,
                provenance=(REL_RAYLEIGH_STAGNATION,),
                inputs=inputs,
            )
        outlet = solution.unwrap()
        outlet_diagnostics = tuple(
            d for d in solution.diagnostics if d.code != "EXTRAPOLATED_GAMMA")
        convergence = solution.convergence

    upstream = state(inlet, gas)
    downstream = state(outlet, gas)
    result = RayleighDuctResult(
        upstream=upstream,
        downstream=downstream,
        stagnation_temperature_ratio_12=requested,
        pressure_ratio_12=downstream.pressure_ratio / upstream.pressure_ratio,
        temperature_ratio_12=downstream.temperature_ratio / upstream.temperature_ratio,
        stagnation_pressure_ratio_12=(downstream.stagnation_pressure_ratio
                                      / upstream.stagnation_pressure_ratio),
        thermally_choked=choked,
    )

    diagnostics = gas.diagnostics + outlet_diagnostics
    status = Status.OK_WITH_WARNINGS if any(
        d.severity is Severity.WARNING for d in diagnostics) else Status.OK
    return Solution(
        value=result,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_RAYLEIGH_RATIOS, REL_RAYLEIGH_STAGNATION),
        convergence=convergence,
        inputs=inputs,
    )
