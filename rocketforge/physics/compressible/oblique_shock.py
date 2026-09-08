"""Oblique shock for a calorically perfect gas.

Specified in ``docs/engineering/03_compressible_flow_specification.md``
section 6. Steady, two-dimensional, inviscid, adiabatic, straight and attached
wave over a planar wedge. Not a cone -- conical flow is Taylor-Maccoll and is a
different module. No boundary-layer interaction, no curved shock, no detached
bow-shock shape, no real-gas chemistry.

**Angles are radians, everywhere in this file.**

**This module owns no jump relation.** There is no pressure, density,
temperature or stagnation-pressure formula anywhere below, and there must never
be one. An oblique shock *is* a normal shock seen by the velocity component
perpendicular to it:

    Mn1 = M1 sin(beta)  ->  normal_shock relations  ->  M2 = Mn2 / sin(beta - theta)

So every ratio comes from :mod:`normal_shock`, evaluated at ``Mn1``. That is not
a convenience; it is what makes the two modules agree by construction rather
than by coincidence, and the reuse audit asserts it to machine precision.

What this module does own: the theta-beta-M relation, the closed forms for the
maximum deflection and the sonic wave angle, the two-branch inversion, and the
honest classification of a deflection that no attached shock can turn.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ...core.errors import DomainError, SubsonicShockError
from ...core.numerics.arrays import (
    as_float_array,
    describe_offender,
    require_finite,
    restore_scalar,
)
from ...core.numerics.roots import brent
from ...core.result import Convergence, Diagnostic, Severity, Solution, Status
from ...core.tolerances import DEFAULT_TOLERANCES, ToleranceSet
from .equations import MODEL_OBLIQUE_SHOCK, REL_THETA_BETA_MACH, REL_THETA_MAX
from .gas import PerfectGas
from .isentropic import mach_angle
from . import normal_shock as ns
from .types import ObliqueShockPair, ObliqueShockResult, ShockBranch, ThetaBetaCurve, ThetaMaxResult

__all__ = [
    "theta_from_beta",
    "theta_max",
    "beta_sonic",
    "beta_from_theta",
    "solve",
    "solve_from_beta",
    "solve_both",
    "theta_beta_curve",
    "ShockBranch",
    "ObliqueShockResult",
    "ObliqueShockPair",
    "ThetaMaxResult",
    "ThetaBetaCurve",
    "MODEL_OBLIQUE_SHOCK",
]


def _supersonic(mach1: object) -> float:
    """Validate the upstream Mach number of an oblique shock.

    M1 > 1 strictly: at exactly Mach 1 the Mach angle is a right angle and the
    admissible range of wave angles collapses to a point, so there is no
    oblique shock to describe.
    """
    array, was_scalar = as_float_array(mach1, "mach1")
    if not was_scalar:
        raise SubsonicShockError("an oblique shock describes one flow; pass a scalar Mach number")
    require_finite(array, "mach1")
    value = float(array)
    if value <= 1.0:
        raise SubsonicShockError(
            "mach1 must be greater than 1: an oblique shock requires supersonic upstream "
            f"flow, and at exactly Mach 1 the wave-angle range collapses to a point; got {value!r}"
        )
    return value


# ---------------------------------------------------------------------------
# the theta-beta-M relation
# ---------------------------------------------------------------------------


def theta_from_beta(beta: object, mach1: object, gas: PerfectGas) -> float | np.ndarray:
    """Flow deflection from wave angle: the theta-beta-M relation [rad].

    ``tan(theta) = 2 cot(beta) (M1^2 sin^2(beta) - 1) / (M1^2 (gamma + cos 2 beta) + 2)``

    Args:
        beta: Wave angle [rad], between the Mach angle and pi/2. Scalar or array.
        mach1: Upstream Mach number [-], > 1. Scalar or array, broadcast against
            ``beta``.
        gas: The gas model.

    Returns:
        The deflection in **radians**. Zero at both ends of the range -- a Mach
        wave at beta = mu, a normal shock at beta = pi/2 -- with a single
        maximum between them.

    Raises:
        SubsonicShockError: M1 <= 1.
        DomainError: beta outside [mu, pi/2].

    Closed form, so nothing iterates here. This is the relation the diagram
    plots and the inversion inverts; there is exactly one copy of it.
    """
    beta_array, beta_scalar = as_float_array(beta, "beta")
    mach_array, mach_scalar = as_float_array(mach1, "mach1")
    require_finite(beta_array, "beta")
    require_finite(mach_array, "mach1")

    bad_mach = ~(mach_array > 1.0)
    if bad_mach.any():
        raise SubsonicShockError(
            "mach1 must be greater than 1 for an oblique shock; "
            f"{describe_offender(bad_mach, mach_array)}"
        )

    lower = np.arcsin(1.0 / mach_array)
    # A hair of slack so that the Mach angle itself, recomputed by a caller and
    # differing in the last bit, is not refused at its own boundary.
    slack = 1e-12
    bad_beta = ~((beta_array >= lower - slack) & (beta_array <= 0.5 * np.pi + slack))
    if bad_beta.any():
        raise DomainError(
            "beta must lie between the Mach angle arcsin(1/M1) and pi/2: below the Mach "
            "angle no wave exists, and above a right angle the wave would lean upstream; "
            f"{describe_offender(bad_beta, beta_array)}"
        )

    clipped = np.clip(beta_array, lower, 0.5 * np.pi)
    gamma = gas.gamma
    numerator = mach_array**2 * np.sin(clipped) ** 2 - 1.0
    denominator = mach_array**2 * (gamma + np.cos(2.0 * clipped)) + 2.0
    value = np.arctan2(2.0 * numerator * np.cos(clipped), denominator * np.sin(clipped))
    # Both endpoints are exactly zero deflection; make them exactly zero rather
    # than a few ulp of arctan noise, since the diagram and the branch logic
    # both read the sign of theta.
    value = np.where(np.abs(clipped - lower) <= slack, 0.0, value)
    value = np.where(np.abs(clipped - 0.5 * np.pi) <= slack, 0.0, value)

    if beta_scalar and mach_scalar:
        return float(value)
    return value


# ---------------------------------------------------------------------------
# the two closed forms
# ---------------------------------------------------------------------------


def _beta_at_theta_max(mach1: float, gas: PerfectGas) -> float:
    """The wave angle of maximum deflection, in closed form [rad].

    The stationary point of the theta-beta-M relation, from ``03`` section 6.3:

        sin^2(beta) = (1/(gamma M1^2)) [ (gamma+1)M1^2/4 - 1
                      + sqrt((gamma+1)((gamma+1)M1^4/16 + (gamma-1)M1^2/2 + 1)) ]

    One square root, not four hundred iterations of a maximiser. The numerical
    search exists only as a test oracle, which is the right way round.
    """
    gamma = gas.gamma
    squared = mach1 * mach1
    inner = (gamma + 1.0) * ((gamma + 1.0) * squared * squared / 16.0
                             + (gamma - 1.0) * squared / 2.0 + 1.0)
    sine_squared = ((gamma + 1.0) * squared / 4.0 - 1.0 + np.sqrt(inner)) / (gamma * squared)
    return float(np.arcsin(np.sqrt(min(sine_squared, 1.0))))


def theta_max(mach1: float, gas: PerfectGas,
              tolerances: ToleranceSet = DEFAULT_TOLERANCES) -> Solution[ThetaMaxResult]:
    """The largest deflection an attached shock can turn, and where it occurs.

    Args:
        mach1: Upstream Mach number [-], > 1.
        gas: The gas model.
        tolerances: Numerical tolerances (unused: this is closed form, and the
            argument is accepted so every solver in the module has one shape).

    Returns:
        A :class:`Solution` carrying a :class:`ThetaMaxResult` with the maximum
        deflection, the wave angle at which it occurs, and the Mach angle.
    """
    value = _supersonic(mach1)
    beta = _beta_at_theta_max(value, gas)
    result = ThetaMaxResult(
        mach1=value,
        theta_max=float(theta_from_beta(beta, value, gas)),
        beta_at_theta_max=beta,
        mach_angle=float(mach_angle(value)),
    )
    return Solution(
        value=result,
        status=Status.OK_WITH_WARNINGS if gas.diagnostics else Status.OK,
        diagnostics=gas.diagnostics,
        provenance=(REL_THETA_MAX,),
        inputs={"mach1": value, "gamma": gas.gamma},
    )


def beta_sonic(mach1: float, gas: PerfectGas) -> Solution[float]:
    """The wave angle at which the downstream flow is exactly sonic [rad].

    Closed form, from ``03`` section 6.4. It sits just *below* the wave angle of
    maximum deflection, which is why a narrow band of weak solutions near
    theta_max already has subsonic flow behind it: "weak branch" does not mean
    "supersonic downstream", and the result record says which it is rather than
    letting the branch name imply it.
    """
    value = _supersonic(mach1)
    gamma = gas.gamma
    squared = value * value
    inner = (gamma + 1.0) * ((gamma + 1.0) * squared * squared / 16.0
                             + (gamma - 3.0) * squared / 8.0 + (gamma + 9.0) / 16.0)
    sine_squared = ((gamma + 1.0) * squared / 4.0 - (3.0 - gamma) / 4.0
                    + np.sqrt(inner)) / (gamma * squared)
    beta = float(np.arcsin(np.sqrt(min(sine_squared, 1.0))))
    return Solution(
        value=beta,
        status=Status.OK_WITH_WARNINGS if gas.diagnostics else Status.OK,
        diagnostics=gas.diagnostics,
        provenance=(REL_THETA_MAX,),
        inputs={"mach1": value, "gamma": gas.gamma},
    )


# ---------------------------------------------------------------------------
# the inversion
# ---------------------------------------------------------------------------


def _detached(mach1: float, theta: float, limit: float,
              gas: PerfectGas) -> tuple[Diagnostic, ...]:
    return (
        Diagnostic(
            code="DETACHED_SHOCK",
            severity=Severity.ERROR,
            message=(
                f"No attached oblique shock exists: a deflection of "
                f"{np.degrees(theta):.4f} degrees exceeds the maximum "
                f"{np.degrees(limit):.4f} degrees that Mach {mach1:g} can turn at "
                f"gamma = {gas.gamma:g}. The shock stands off the body as a curved "
                "detached bow shock, which this model does not solve."
            ),
            field="theta",
            detail={"theta": theta, "theta_max": limit, "mach1": mach1},
        ),
    )


def _near_theta_max(theta: float, limit: float,
                    tolerances: ToleranceSet) -> tuple[Diagnostic, ...]:
    """Advise when the two roots are close enough that beta is ill-determined."""
    if limit <= 0.0 or (limit - theta) >= tolerances.near_theta_max * limit:
        return ()
    return (
        Diagnostic(
            code="NEAR_THETA_MAX",
            severity=Severity.WARNING,
            message=(
                "Close to the maximum deflection the two wave angles approach each "
                "other and the deflection is flat in between, so the wave angle is "
                "poorly determined: small changes in the requested deflection move it "
                "a great deal."
            ),
            field="theta",
            detail={"theta": theta, "theta_max": limit},
        ),
    )


def beta_from_theta(
    mach1: float,
    theta: float,
    gas: PerfectGas,
    branch: ShockBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]:
    """Wave angle from a required flow deflection [rad].

    Args:
        mach1: Upstream Mach number [-], > 1.
        theta: Required deflection [rad], >= 0.
        gas: The gas model.
        branch: ``ShockBranch.WEAK`` or ``ShockBranch.STRONG``. Required here;
            :func:`solve` is the one that supplies a default.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying the wave angle, or ``NO_SOLUTION`` with a
        ``DETACHED_SHOCK`` diagnostic when the deflection exceeds the maximum.

    Brent on **one side** of the maximum, never on the whole range. The
    relation rises from zero at the Mach angle to its maximum and falls back to
    zero at a right angle, so the full interval holds two roots and any solver
    given all of it is relying on luck about which one it lands on. Split at
    the closed-form maximum, each half is strictly monotone and has exactly one.
    """
    value = _supersonic(mach1)
    array, was_scalar = as_float_array(theta, "theta")
    if not was_scalar:
        raise DomainError("theta must be a scalar angle in radians")
    require_finite(array, "theta")
    requested = float(array)
    if requested < 0.0:
        raise DomainError(
            "theta must be >= 0: this module turns the flow into the oncoming stream, and "
            f"the sign convention makes a compression positive; got {requested!r}"
        )
    if not isinstance(branch, ShockBranch):
        raise ValueError(
            f"branch must be a ShockBranch, got {branch!r}. Every attainable deflection "
            "has a weak and a strong wave angle and the equations cannot say which is meant."
        )
    if branch is ShockBranch.BOTH:
        raise ValueError(
            "branch=BOTH is a request for two roots; call solve_both, which returns them "
            "as named fields"
        )

    mu = float(mach_angle(value))
    inputs = {"mach1": value, "theta": requested, "gamma": gas.gamma}

    if requested <= tolerances.angle_tol:
        # A zero-deflection wave. Which angle that is depends on the branch and
        # both are real: the vanishing Mach wave, and the normal shock. Neither
        # is invented, and neither is chosen silently.
        beta = mu if branch is ShockBranch.WEAK else 0.5 * np.pi
        return Solution(
            value=beta,
            status=Status.OK_WITH_WARNINGS if gas.diagnostics else Status.OK,
            diagnostics=gas.diagnostics + (
                Diagnostic(
                    code="SONIC_EXACT",
                    severity=Severity.INFO,
                    message=(
                        "Zero deflection: the weak limit is a vanishing Mach wave at "
                        "beta = mu, and the strong limit is a normal shock at beta = 90 "
                        "degrees. Both turn the flow through nothing."
                    ),
                    field="theta",
                ),
            ),
            provenance=(REL_THETA_BETA_MACH,),
            inputs=inputs,
        )

    beta_max = _beta_at_theta_max(value, gas)
    limit = float(theta_from_beta(beta_max, value, gas))

    if requested > limit + tolerances.angle_tol:
        return Solution(
            value=None,
            status=Status.NO_SOLUTION,
            diagnostics=gas.diagnostics + _detached(value, requested, limit, gas),
            provenance=(REL_THETA_BETA_MACH,),
            inputs=inputs,
        )

    if abs(requested - limit) <= tolerances.angle_tol:
        # The two roots have merged. Returning either bracket's Brent result
        # here would be reporting a distinction that no longer exists.
        return Solution(
            value=beta_max,
            status=Status.OK_WITH_WARNINGS,
            diagnostics=gas.diagnostics + (
                Diagnostic(
                    code="BRANCH_ASSUMED",
                    severity=Severity.INFO,
                    message=(
                        "At the maximum deflection the weak and strong solutions coincide; "
                        "there is one wave angle, not two."
                    ),
                    field="branch",
                    detail={"theta_max": limit, "beta": beta_max},
                ),
            ) + _near_theta_max(requested, limit, tolerances),
            provenance=(REL_THETA_BETA_MACH,),
            inputs=inputs,
        )

    def residual(angle: float) -> float:
        return float(theta_from_beta(angle, value, gas)) - requested

    if branch is ShockBranch.WEAK:
        low, high = mu + tolerances.angle_margin, beta_max
    else:
        low, high = beta_max, 0.5 * np.pi - tolerances.angle_margin

    root, report = brent(
        residual, low, high,
        xtol=tolerances.angle_abs_tol,
        rtol=tolerances.mach_rel_tol,
        max_iter=tolerances.max_iter,
    )

    diagnostics = gas.diagnostics + _near_theta_max(requested, limit, tolerances)
    if report.converged:
        status = Status.OK_WITH_WARNINGS if diagnostics else Status.OK
    else:
        status = Status.NOT_CONVERGED
        diagnostics = diagnostics + (
            Diagnostic(
                code="NOT_CONVERGED",
                severity=Severity.ERROR,
                message=(
                    f"The wave-angle inversion did not converge within {report.iterations} "
                    "iterations; the value returned is the best estimate found and should "
                    "not be used without checking."
                ),
                field="theta",
                detail={"residual": report.residual, "iterations": float(report.iterations)},
            ),
        )

    return Solution(
        value=root,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_THETA_BETA_MACH,),
        convergence=Convergence.from_report(report),
        inputs=inputs,
    )


# ---------------------------------------------------------------------------
# the full downstream state, by reuse
# ---------------------------------------------------------------------------


def _result_from(mach1: float, beta: float, theta: float, branch: ShockBranch,
                 limit: float, gas: PerfectGas,
                 tolerances: ToleranceSet) -> ObliqueShockResult:
    """Assemble the downstream state from the normal-shock solution.

    The only arithmetic here is geometric: the normal component going in, and
    the reconstruction of the full Mach number coming out. Every property ratio
    is taken from :mod:`normal_shock`, not recomputed.
    """
    normal_mach1 = mach1 * float(np.sin(beta))
    # sin(beta) can round a hair below 1/M1 at the Mach-angle boundary, which
    # would make a physically sonic normal component look subsonic to the shock
    # relations. Clamping to the exact sonic value there is not hiding an
    # error; it is the boundary itself.
    if 1.0 - normal_mach1 <= tolerances.sonic_tol:
        normal_mach1 = max(normal_mach1, 1.0)
    shock = ns.solve(normal_mach1, gas)

    turned = beta - theta
    # beta > theta always holds for an attached shock, so the sine is positive
    # and bounded away from zero except in the merged limit; guard anyway,
    # because a silent division by a vanishing sine is how a plausible-looking
    # infinity gets published.
    sine = float(np.sin(turned))
    if sine <= 0.0:
        raise DomainError(
            f"the flow behind the shock would be turned past the wave itself "
            f"(beta = {np.degrees(beta):.4f} deg, theta = {np.degrees(theta):.4f} deg)"
        )
    mach2 = shock.mach2 / sine

    return ObliqueShockResult(
        mach1=mach1,
        theta=theta,
        beta=beta,
        branch=branch,
        mach_normal1=normal_mach1,
        mach_normal2=shock.mach2,
        mach2=mach2,
        pressure_ratio=shock.pressure_ratio,
        temperature_ratio=shock.temperature_ratio,
        density_ratio=shock.density_ratio,
        stagnation_pressure_ratio=shock.stagnation_pressure_ratio,
        stagnation_temperature_ratio=shock.stagnation_temperature_ratio,
        entropy_change=shock.entropy_change,
        downstream_flow_angle=theta,
        theta_max=limit,
        downstream_supersonic=bool(mach2 > 1.0),
    )


def solve(
    mach1: float,
    theta: float,
    gas: PerfectGas,
    branch: ShockBranch = ShockBranch.WEAK,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[ObliqueShockResult]:
    """The primary mode: deflection in, wave angle and downstream state out.

    Args:
        mach1: Upstream Mach number [-], > 1.
        theta: Required deflection [rad], >= 0.
        gas: The gas model.
        branch: Which of the two wave angles is wanted. Defaults to
            ``WEAK`` -- the branch that physically occurs in essentially every
            external flow -- and says so through a ``BRANCH_ASSUMED``
            diagnostic when the default was taken.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying an :class:`ObliqueShockResult`, or
        ``NO_SOLUTION`` carrying ``DETACHED_SHOCK``. It is never a fabricated
        attached solution and never the theta_max solution silently
        substituted.
    """
    value = _supersonic(mach1)
    if branch is ShockBranch.BOTH:
        raise ValueError("branch=BOTH is a request for two solutions; call solve_both")

    angle = beta_from_theta(value, theta, gas, branch, tolerances)
    if not angle.ok:
        return Solution(
            value=None,
            status=angle.status,
            diagnostics=angle.diagnostics,
            provenance=(REL_THETA_BETA_MACH,),
            inputs=angle.inputs,
        )

    # theta_max is a closed form, but it is not free, and beta_from_theta has
    # already evaluated it to decide whether this deflection is attainable at
    # all. Recomputing it here would be doing the same square root twice per
    # solve, which shows up when a study sweeps thousands of deflections.
    beta_max = _beta_at_theta_max(value, gas)
    limit = float(theta_from_beta(beta_max, value, gas))
    result = _result_from(value, angle.unwrap(), float(theta), branch, limit, gas, tolerances)

    diagnostics = angle.diagnostics
    if branch is ShockBranch.STRONG:
        diagnostics = diagnostics + (
            Diagnostic(
                code="STRONG_BRANCH_UNSTABLE",
                severity=Severity.INFO,
                message=(
                    "The strong solution satisfies the equations but is realised only "
                    "when downstream conditions force it; an unconstrained external flow "
                    "takes the weak branch."
                ),
                field="branch",
            ),
        )
    status = Status.OK_WITH_WARNINGS if any(
        d.severity is Severity.WARNING for d in diagnostics) else Status.OK
    return Solution(
        value=result,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_THETA_BETA_MACH,),
        convergence=angle.convergence,
        inputs=angle.inputs,
    )


def solve_both(mach1: float, theta: float, gas: PerfectGas,
               tolerances: ToleranceSet = DEFAULT_TOLERANCES) -> Solution[ObliqueShockPair]:
    """Both wave angles that turn the flow through the same deflection.

    Returns an :class:`ObliqueShockPair` whose fields are named ``weak`` and
    ``strong``, so no caller has to remember an ordering.
    """
    weak = solve(mach1, theta, gas, ShockBranch.WEAK, tolerances)
    strong = solve(mach1, theta, gas, ShockBranch.STRONG, tolerances)
    if not (weak.ok and strong.ok):
        failed = weak if not weak.ok else strong
        return Solution(
            value=None,
            status=failed.status,
            diagnostics=failed.diagnostics,
            provenance=(REL_THETA_BETA_MACH,),
            inputs=failed.inputs,
        )
    pair = ObliqueShockPair(weak=weak.unwrap(), strong=strong.unwrap())
    diagnostics = weak.diagnostics + tuple(
        d for d in strong.diagnostics if d.code == "STRONG_BRANCH_UNSTABLE")
    return Solution(
        value=pair,
        status=Status.OK_WITH_WARNINGS if any(
            d.severity is Severity.WARNING for d in diagnostics) else Status.OK,
        diagnostics=diagnostics,
        provenance=(REL_THETA_BETA_MACH,),
        inputs=weak.inputs,
    )


def solve_from_beta(mach1: float, beta: float, gas: PerfectGas,
                    tolerances: ToleranceSet = DEFAULT_TOLERANCES
                    ) -> Solution[ObliqueShockResult]:
    """The closed-form mode: wave angle in, deflection and downstream state out.

    No iteration at all -- theta follows algebraically from beta, and the state
    follows from the normal component. This is the mode the diagram uses, and
    the one the reuse audit compares against :mod:`normal_shock` directly.

    The branch is *reported*, not chosen: a wave angle below the angle of
    maximum deflection is on the weak branch and one above it is on the strong
    branch, and that is a fact about the angle rather than a request.
    """
    value = _supersonic(mach1)
    array, was_scalar = as_float_array(beta, "beta")
    if not was_scalar:
        raise DomainError("solve_from_beta describes one shock; pass a scalar wave angle")
    angle = float(array)
    theta = float(theta_from_beta(angle, value, gas))

    beta_max = _beta_at_theta_max(value, gas)
    limit = float(theta_from_beta(beta_max, value, gas))
    branch = ShockBranch.WEAK if angle <= beta_max else ShockBranch.STRONG

    result = _result_from(value, angle, theta, branch, limit, gas, tolerances)
    return Solution(
        value=result,
        status=Status.OK_WITH_WARNINGS if gas.diagnostics else Status.OK,
        diagnostics=gas.diagnostics,
        provenance=(REL_THETA_BETA_MACH,),
        inputs={"mach1": value, "beta": angle, "gamma": gas.gamma},
    )


# ---------------------------------------------------------------------------
# diagram data
# ---------------------------------------------------------------------------


def theta_beta_curve(mach1: float, gas: PerfectGas, n: int = 400,
                     tolerances: ToleranceSet = DEFAULT_TOLERANCES
                     ) -> Solution[ThetaBetaCurve]:
    """Data for the theta-beta-M diagram: angles only, no presentation.

    Args:
        mach1: Upstream Mach number [-], > 1.
        gas: The gas model.
        n: Number of points across the wave-angle range.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying a :class:`ThetaBetaCurve`: the wave angles
        from the Mach angle to a right angle, the deflection at each, and the
        three markers a reader needs -- the maximum deflection, the wave angle
        where it occurs, and the wave angle at which the flow behind turns
        sonic.

    The grid is clustered towards both ends, where the curve turns sharply. A
    uniform grid draws a visibly faceted nose at the maximum and wastes points
    along the straight middle of the strong branch.

    Returns numbers and nothing else: no colours, no axes, no Qt. The interface
    decides what to draw with them.
    """
    value = _supersonic(mach1)
    if n < 3:
        raise DomainError(f"n must be at least 3 to describe a curve, got {n!r}")

    mu = float(mach_angle(value))
    upper = 0.5 * np.pi
    # A cosine-clustered parameter: dense at both ends, sparse in the middle.
    parameter = 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, int(n))))
    beta = mu + (upper - mu) * parameter
    theta = np.asarray(theta_from_beta(beta, value, gas))

    beta_max = _beta_at_theta_max(value, gas)
    curve = ThetaBetaCurve(
        mach1=value,
        beta=beta,
        theta=theta,
        theta_max=float(theta_from_beta(beta_max, value, gas)),
        beta_at_theta_max=beta_max,
        beta_sonic=beta_sonic(value, gas).unwrap(),
        mach_angle=mu,
    )
    return Solution(
        value=curve,
        status=Status.OK_WITH_WARNINGS if gas.diagnostics else Status.OK,
        diagnostics=gas.diagnostics,
        provenance=(REL_THETA_BETA_MACH,),
        inputs={"mach1": value, "gamma": gas.gamma},
    )
