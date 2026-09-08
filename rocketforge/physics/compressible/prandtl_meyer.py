"""Prandtl-Meyer expansion for a calorically perfect gas.

Specified in ``docs/engineering/03_compressible_flow_specification.md``
section 7. Steady, two-dimensional, isentropic, centred expansion around a
convex corner. No viscosity, no finite-rate chemistry, no variable gamma, no
boundary layer, no finite-thickness fan.

**Angles are radians, everywhere in this file.** Degrees exist only above the
application boundary, and a name ending in ``_deg`` is forbidden at this layer
by the architecture test. The published tables print degrees; converting them is
the reference adapter's job, not this module's.

Two things this module deliberately does not own:

* the Mach angle. ``mu = arcsin(1/M)`` is geometry, it is already implemented
  and tested in :mod:`isentropic`, and it is imported from there rather than
  written a second time;
* the static ratios across an expansion. The expansion is isentropic, so
  ``p2/p1`` is the quotient of two isentropic ``p/p0`` values and nothing else.
  :func:`expand` calls :mod:`isentropic` for them.

What that leaves is one relation, its inverse, and the geometry of the fan.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ...core.errors import DomainError, SubsonicExpansionError
from ...core.numerics.arrays import (
    as_float_array,
    describe_offender,
    require_at_least,
    require_finite,
    restore_scalar,
)
from ...core.numerics.roots import brent
from ...core.result import Convergence, Diagnostic, Severity, Solution, Status
from ...core.tolerances import DEFAULT_TOLERANCES, ToleranceSet
from .equations import MODEL_PRANDTL_MEYER, REL_PRANDTL_MEYER
from .gas import PerfectGas
from .isentropic import mach_angle
from . import isentropic as iso

__all__ = [
    "nu",
    "nu_max",
    "mach_angle",
    "mach_from_nu",
    "mach_from_nu_array",
    "expand",
    "compress",
    "PrandtlMeyerResult",
    "MODEL_PRANDTL_MEYER",
]


def _supersonic(mach: object) -> tuple[np.ndarray, bool]:
    """Validate a Mach number for an expansion relation.

    M >= 1 is required and the refusal is specific: below Mach 1 the two
    ``sqrt(M^2 - 1)`` terms are imaginary, so this is not a case of an
    unphysical-but-computable answer -- there is nothing to compute.
    """
    array, was_scalar = as_float_array(mach, "mach")
    require_finite(array, "mach")
    bad = ~(array >= 1.0)
    if bad.any():
        raise SubsonicExpansionError(
            "mach must be >= 1: a Prandtl-Meyer expansion is a supersonic "
            f"phenomenon and the relation is complex-valued below Mach 1; "
            f"{describe_offender(bad, array)}"
        )
    return array, was_scalar


# ---------------------------------------------------------------------------
# the relation
# ---------------------------------------------------------------------------


def nu(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """The Prandtl-Meyer function ``nu(M)`` [rad].

    ``nu = sqrt((g+1)/(g-1)) * arctan sqrt((g-1)/(g+1) (M^2-1)) - arctan sqrt(M^2-1)``

    Args:
        mach: Mach number [-], >= 1. Scalar or array.
        gas: The gas model; only ``gamma`` is used.

    Returns:
        The turning angle in **radians** required to expand from Mach 1 to this
        Mach number. Exactly 0 at M = 1, strictly increasing above it, and
        bounded above by :func:`nu_max`.

    Raises:
        SubsonicExpansionError: M < 1.

    Written with ``M^2 - 1`` as the shared subexpression so the sonic value is
    exactly zero rather than a difference of two nearly equal arctangents.
    """
    array, was_scalar = _supersonic(mach)
    gamma = gas.gamma
    ratio = (gamma + 1.0) / (gamma - 1.0)
    root = np.sqrt(ratio)
    excess = array * array - 1.0
    value = root * np.arctan(np.sqrt(excess / ratio)) - np.arctan(np.sqrt(excess))
    return restore_scalar(value, was_scalar)


def nu_max(gas: PerfectGas) -> float:
    """The finite supremum of ``nu`` as M -> infinity [rad].

    ``nu_max = (pi/2) (sqrt((g+1)/(g-1)) - 1)``

    130.4540768505 degrees for air. This is the total turning available to
    expand to an infinite Mach number, and it is a hard ceiling on the inverse:
    a turn asking for more of it has no perfect-gas solution at all, which is a
    statement about the model rather than about the arithmetic.
    """
    gamma = gas.gamma
    return 0.5 * np.pi * (np.sqrt((gamma + 1.0) / (gamma - 1.0)) - 1.0)


def _derivative(mach: float, gas: PerfectGas) -> float:
    """``dnu/dM = sqrt(M^2-1) / (M (1 + (g-1)/2 M^2))``.

    Not part of the public API -- Brent needs no derivative. It exists because
    the monotonicity the inverse relies on is a property worth being able to
    assert directly, and because it is zero at M = 1, which is exactly why
    Newton is not used here.
    """
    gamma = gas.gamma
    return float(np.sqrt(mach * mach - 1.0)
                 / (mach * (1.0 + 0.5 * (gamma - 1.0) * mach * mach)))


# ---------------------------------------------------------------------------
# the inverse
# ---------------------------------------------------------------------------


def _upper_bracket(nu_target: float, gas: PerfectGas, tolerances: ToleranceSet) -> float:
    """A Mach number known to sit above the root, in closed form.

    From the large-M asymptote of the two arctangents (``04`` section 3.2):

        nu_max - nu(M) -> 2 / ((gamma-1) M)   =>   M_seed = 2 / ((g-1)(nu_max - nu))

    Verified in Phase 3 to *over*estimate M at every point tested, by a factor
    between 1.001 and 1.96, so it is always a valid upper end and always above
    1. Capped at the Mach ceiling regardless: past it the answer is a modelling
    error rather than a numerical one.
    """
    gap = nu_max(gas) - nu_target
    seed = 2.0 / ((gas.gamma - 1.0) * gap)
    return float(min(max(seed, 1.0 + tolerances.sonic_margin), tolerances.mach_ceiling))


def mach_from_nu(
    nu_value: float,
    gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]:
    """Mach number from a Prandtl-Meyer angle.

    Args:
        nu_value: The turning angle from sonic, in **radians**, in [0, nu_max).
        gas: The gas model.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying the Mach number, or ``NO_SOLUTION`` with a
        ``NU_EXCEEDS_MAX`` diagnostic when the requested angle is at or beyond
        the maximum expansion for this gamma.

    Raises:
        DomainError: ``nu_value`` is negative or not a finite scalar.

    Solved with Brent from the exact bracket ``[1, M_seed]``. Newton is
    tempting because ``dnu/dM`` is closed form, but it is zero at M = 1 --
    precisely where users start -- so the first Newton step from the sonic
    point is undefined. Brent has no such problem.
    """
    array, was_scalar = as_float_array(nu_value, "nu")
    if not was_scalar:
        raise DomainError(
            "mach_from_nu solves one angle; pass a scalar or use mach_from_nu_array"
        )
    require_finite(array, "nu")
    require_at_least(array, 0.0, "nu (a Prandtl-Meyer angle is measured from sonic and "
                                 "cannot be negative)")
    target = float(array)
    inputs = {"nu": target, "gamma": gas.gamma}

    if target <= tolerances.nu_tol:
        # The sonic endpoint, answered exactly. Iterating on a residual that is
        # already zero would only manufacture solver noise.
        return Solution(
            value=1.0,
            status=Status.OK_WITH_WARNINGS if gas.diagnostics else Status.OK,
            diagnostics=gas.diagnostics + (
                Diagnostic(
                    code="SONIC_EXACT",
                    severity=Severity.INFO,
                    message="nu = 0 is the sonic condition; M = 1 exactly.",
                    field="nu",
                ),
            ),
            provenance=(REL_PRANDTL_MEYER,),
            inputs=inputs,
        )

    ceiling = nu_max(gas)
    if target >= ceiling - tolerances.nu_tol:
        return Solution(
            value=None,
            status=Status.NO_SOLUTION,
            diagnostics=gas.diagnostics + (
                Diagnostic(
                    code="NU_EXCEEDS_MAX",
                    severity=Severity.ERROR,
                    message=(
                        f"A turn of {np.degrees(target):.4f} degrees reaches or exceeds the "
                        f"maximum expansion {np.degrees(ceiling):.4f} degrees available at "
                        f"gamma = {gas.gamma:g}; the flow would have to reach an infinite "
                        "Mach number."
                    ),
                    field="nu",
                    detail={"nu": target, "nu_max": ceiling, "gamma": gas.gamma},
                ),
            ),
            provenance=(REL_PRANDTL_MEYER,),
            inputs=inputs,
        )

    def residual(mach: float) -> float:
        return float(nu(mach, gas)) - target

    low = 1.0
    high = _upper_bracket(target, gas, tolerances)
    # A safety net that the verified seed means never runs; kept because a
    # bracket that silently fails is worse than one that widens.
    while residual(high) < 0.0 and high < tolerances.mach_ceiling:
        high = min(2.0 * high, tolerances.mach_ceiling)

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
                    f"The Prandtl-Meyer inversion did not converge within "
                    f"{report.iterations} iterations; the value returned is the best "
                    "estimate found and should not be used without checking."
                ),
                field="nu",
                detail={"residual": report.residual, "iterations": float(report.iterations)},
            ),
        )

    solution: Solution[float] = Solution(
        value=root,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_PRANDTL_MEYER,),
        convergence=Convergence.from_report(report),
        inputs=inputs,
    )
    return solution.with_diagnostics(*gas.diagnostics)


def _near_sonic_diagnostic(mach: float, tolerances: ToleranceSet) -> tuple[Diagnostic, ...]:
    """Advise when the Mach number is less determined than the angle.

    Near sonic, nu ~ (M-1)^(3/2), so a relative error eps in nu becomes
    eps^(2/3) in (M-1). That is *better* conditioned than the area-Mach inverse
    (which loses a half power), but it is still a loss, and a user reading six
    figures of Mach from a tiny turn angle should be told that the last of them
    are not there.
    """
    excess = mach - 1.0
    if excess <= tolerances.sonic_tol:
        return ()
    if excess >= tolerances.near_sonic_mach:
        return ()
    return (
        Diagnostic(
            code="NEAR_SONIC",
            severity=Severity.WARNING,
            message=(
                "Close to the sonic point the Prandtl-Meyer function varies as "
                "(M-1)^(3/2), so the Mach number is less precisely determined than the "
                "angle it was solved from: roughly two thirds of the digits carry over."
            ),
            field="nu",
            detail={"mach": mach},
        ),
    )


def mach_from_nu_array(nu_value: np.ndarray, gas: PerfectGas,
                       tolerances: ToleranceSet = DEFAULT_TOLERANCES) -> np.ndarray:
    """Mach numbers for an array of Prandtl-Meyer angles.

    A convenience for sweeps and charts. Each element is solved by the same
    scalar inverse -- there is no vectorised root finder here and pretending
    otherwise would hide the per-element diagnostics. Elements with no solution
    come back as NaN, which is honest for a plot: the curve simply stops.
    """
    array, _ = as_float_array(nu_value, "nu")
    require_finite(array, "nu")
    out = np.empty(array.shape, dtype=np.float64)
    flat = array.reshape(-1)
    result = out.reshape(-1)
    for index, value in enumerate(flat):
        solution = mach_from_nu(float(value), gas, tolerances)
        result[index] = solution.value if solution.ok else np.nan
    return out


# ---------------------------------------------------------------------------
# the expansion turn
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PrandtlMeyerResult:
    """One expansion (or isentropic compression) turn, as one record.

    Angles in radians. ``fan_angle`` is the angular width of the centred fan:
    the leading Mach line lies at ``mach_angle1`` from the upstream direction
    and the trailing line at ``mach_angle2`` from the downstream direction, so
    the fan spans ``mu1 - mu2 + turn``. That is geometry, not new physics.
    """

    mach1: float
    mach2: float
    nu1: float
    nu2: float
    turn_angle: float
    pressure_ratio: float
    temperature_ratio: float
    density_ratio: float
    mach_angle1: float
    mach_angle2: float
    fan_angle: float


def _turn(mach1: float, turn_angle: float, gas: PerfectGas, tolerances: ToleranceSet,
          sign: float, extra: tuple[Diagnostic, ...]) -> Solution[PrandtlMeyerResult]:
    """The machinery shared by :func:`expand` and :func:`compress`.

    ``sign`` is +1 for an expansion and -1 for an isentropic compression. Both
    are the same three steps -- nu, add or subtract, invert -- and writing them
    twice would let the two drift.
    """
    upstream, was_scalar = _supersonic(mach1)
    if not was_scalar:
        raise SubsonicExpansionError(
            "an expansion turn describes a single flow; pass a scalar Mach number"
        )
    angle_array, angle_scalar = as_float_array(turn_angle, "turn_angle")
    if not angle_scalar:
        raise DomainError("turn_angle must be a scalar angle in radians")
    require_finite(angle_array, "turn_angle")
    require_at_least(angle_array, 0.0, "turn_angle (the magnitude of the turn; "
                                       "expand() and compress() fix its direction)")

    m1 = float(upstream)
    turn = float(angle_array)
    nu1 = float(nu(m1, gas))
    nu2 = nu1 + sign * turn
    inputs = {"mach1": m1, "turn_angle": turn, "gamma": gas.gamma}

    if nu2 < -tolerances.nu_tol:
        return Solution(
            value=None,
            status=Status.NO_SOLUTION,
            diagnostics=gas.diagnostics + extra + (
                Diagnostic(
                    code="NU_BELOW_ZERO",
                    severity=Severity.ERROR,
                    message=(
                        f"An isentropic compression of {np.degrees(turn):.4f} degrees from "
                        f"M = {m1:g} would take the flow below Mach 1, where the "
                        "Prandtl-Meyer relation does not apply. The available turn is "
                        f"{np.degrees(nu1):.4f} degrees."
                    ),
                    field="turn_angle",
                    detail={"nu1": nu1, "turn_angle": turn},
                ),
            ),
            provenance=(REL_PRANDTL_MEYER,),
            inputs=inputs,
        )

    downstream = mach_from_nu(max(nu2, 0.0), gas, tolerances)
    if not downstream.ok:
        # Carry the inverse's own diagnostic through: it already says whether
        # the turn exceeded the maximum expansion, and restating it here in
        # different words would give the same fact two voices.
        return Solution(
            value=None,
            status=downstream.status,
            diagnostics=downstream.diagnostics + extra,
            provenance=(REL_PRANDTL_MEYER,),
            inputs=inputs,
        )

    m2 = downstream.unwrap()

    # Isentropic, so p0 and T0 are unchanged and every static ratio is the
    # quotient of two isentropic values. No expansion-specific formula exists
    # in this module, and the reuse audit asserts it.
    pressure = float(iso.pressure_ratio(m2, gas)) / float(iso.pressure_ratio(m1, gas))
    temperature = float(iso.temperature_ratio(m2, gas)) / float(iso.temperature_ratio(m1, gas))
    density = float(iso.density_ratio(m2, gas)) / float(iso.density_ratio(m1, gas))

    mu1 = float(mach_angle(m1))
    mu2 = float(mach_angle(m2))

    result = PrandtlMeyerResult(
        mach1=m1,
        mach2=m2,
        nu1=nu1,
        nu2=float(nu(m2, gas)),
        turn_angle=sign * turn,
        pressure_ratio=pressure,
        temperature_ratio=temperature,
        density_ratio=density,
        mach_angle1=mu1,
        mach_angle2=mu2,
        fan_angle=mu1 - mu2 + sign * turn,
    )

    diagnostics = gas.diagnostics + extra + tuple(
        d for d in downstream.diagnostics if d.code not in ("EXTRAPOLATED_GAMMA",)
    )
    status = Status.OK_WITH_WARNINGS if any(
        d.severity is Severity.WARNING for d in diagnostics) else Status.OK
    return Solution(
        value=result,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_PRANDTL_MEYER,),
        convergence=downstream.convergence,
        inputs=inputs,
    )


def expand(mach1: float, turn_angle: float, gas: PerfectGas,
           tolerances: ToleranceSet = DEFAULT_TOLERANCES) -> Solution[PrandtlMeyerResult]:
    """Expand a supersonic stream through a convex corner.

    Args:
        mach1: Upstream Mach number [-], >= 1.
        turn_angle: The turn, in **radians**, >= 0. A negative value is refused
            rather than quietly routed into a compression: this module solves
            expansions, and a compression turn is an oblique shock.
        gas: The gas model.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying a :class:`PrandtlMeyerResult`, or
        ``NO_SOLUTION`` when ``nu1 + turn`` reaches the maximum expansion.
    """
    return _turn(mach1, turn_angle, gas, tolerances, +1.0, ())


def compress(mach1: float, turn_angle: float, gas: PerfectGas,
             tolerances: ToleranceSet = DEFAULT_TOLERANCES) -> Solution[PrandtlMeyerResult]:
    """Compress a supersonic stream isentropically through a concave turn.

    The same machinery with ``nu2 = nu1 - turn``, and the same requirement that
    the result stay supersonic.

    It carries a standing advisory, because the idealisation matters: a real
    finite concave turn does not compress isentropically. Its Mach waves
    converge and coalesce into an oblique shock, across which stagnation
    pressure is lost. This result is the limit of a turn made through
    infinitely many infinitesimal steps, which is a useful bound and not a
    description of a wedge.
    """
    advisory = (
        Diagnostic(
            code="ISENTROPIC_COMPRESSION",
            severity=Severity.WARNING,
            message=(
                "An isentropic compression is an idealisation: the Mach waves from a "
                "real concave turn converge and coalesce into an oblique shock, which "
                "loses stagnation pressure. Use the Oblique Shock module for a wedge."
            ),
            field="turn_angle",
        ),
    )
    return _turn(mach1, turn_angle, gas, tolerances, -1.0, advisory)
