"""Normal shock relations for a calorically perfect gas.

Specified in ``docs/engineering/03_compressible_flow_specification.md``
section 5. Steady, one-dimensional, adiabatic, no work, calorically perfect
gas, and a discontinuity of zero thickness. No viscosity, no finite shock
structure, no chemistry, no variable gamma.

All of it is algebraic: nothing here iterates, and the root solver is not
imported. Orientation is downstream over upstream throughout, and every public
name says so.

Two relations are computed by composition rather than by their own closed
form, deliberately:

* ``T2/T1`` is ``(p2/p1) / (rho2/rho1)``, which makes the ideal gas law hold
  between the three to machine precision instead of only to round-off;
* ``p02/p1`` -- the Rayleigh pitot ratio -- is the stagnation-pressure ratio
  times the upstream isentropic ``p0/p``, so it reuses two verified relations
  instead of introducing a third.

A stated resolution limit, so it is never mistaken for a defect: the
stagnation-pressure loss of a weak shock goes as ``(M1^2-1)^3``, specifically

    1 - p02/p01  ->  [2 gamma / (3 (gamma+1)^2)] (M1^2 - 1)^3,

which for M1 - 1 below roughly 1e-5 is smaller than the spacing of double
precision numbers near 1. In that band ``p02/p01`` rounds to 1 give or take an
ulp -- occasionally an ulp *above* 1 -- and the entropy rise rounds to zero.
The relations are not clamped to hide this: the loss really is unresolvable
there, and a shock that weak is a Mach wave. Outside the band, from
M1 - 1 = 1e-4 upward, the computed loss follows the cubic law above and the
invariants hold strictly. Tests assert exactly that, band included.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ...core.errors import DomainError, SubsonicShockError
from ...core.numerics.arrays import (
    as_float_array,
    describe_offender,
    require_above,
    require_at_least,
    require_at_most,
    require_finite,
    restore_scalar,
)
from ...core.numerics.roots import brent
from ...core.result import Convergence, Diagnostic, Severity, Solution, Status
from ...core.tolerances import DEFAULT_TOLERANCES, ToleranceSet
from .equations import MODEL_NORMAL_SHOCK, REL_NORMAL_SHOCK
from .gas import PerfectGas
from . import isentropic as iso

__all__ = [
    "mach_downstream",
    "pressure_ratio",
    "density_ratio",
    "temperature_ratio",
    "stagnation_pressure_ratio",
    "stagnation_pressure_over_upstream_static",
    "entropy_change",
    "area_star_ratio",
    "mach_upstream_from_pressure_ratio",
    "mach_upstream_from_density_ratio",
    "mach_upstream_from_downstream_mach",
    "mach_upstream_from_stagnation_pressure_ratio",
    "density_ratio_limit",
    "mach_downstream_limit",
    "solve",
    "NormalShockResult",
    "MODEL_NORMAL_SHOCK",
]


#: Named once so every relation refuses subsonic upstream flow in the same words.
_SUBSONIC_REASON = (
    "mach1 (a normal shock requires supersonic upstream flow; below Mach 1 the "
    "relations describe an entropy-decreasing expansion shock)"
)


def _validate(mach1: object) -> tuple[np.ndarray, bool]:
    """Validate the upstream Mach number of a shock.

    M1 >= 1 is required. The relations are algebraically defined below 1, but
    the states they describe there have decreasing entropy, which the second
    law forbids -- an expansion shock. Nothing in the arithmetic complains, so
    this check is the only thing standing between a caller and a physically
    impossible answer.

    The bound failure is re-raised as :class:`SubsonicShockError` -- a
    ``DomainError`` subclass, so generic handlers still catch it, while a
    caller that wants to say "that is an expansion shock" can tell this apart
    from an ordinary out-of-range input. Only the bound check is wrapped: a
    non-finite or non-numeric input is not a subsonic shock and keeps its own
    error type.
    """
    array, was_scalar = as_float_array(mach1, "mach1")
    require_finite(array, "mach1")
    try:
        require_at_least(array, 1.0, _SUBSONIC_REASON)
    except DomainError as error:
        raise SubsonicShockError(str(error)) from None
    return array, was_scalar


# ---------------------------------------------------------------------------
# the jump relations
# ---------------------------------------------------------------------------


def mach_downstream(mach1: object, gas: PerfectGas) -> float | np.ndarray:
    """Downstream Mach number ``M2``.

    ``M2^2 = [1 + (gamma-1)/2 M1^2] / [gamma M1^2 - (gamma-1)/2]``

    Always subsonic for M1 > 1, and exactly 1 at M1 = 1.
    """
    array, was_scalar = _validate(mach1)
    gamma = gas.gamma
    half = 0.5 * (gamma - 1.0)
    squared = array * array
    return restore_scalar(np.sqrt((1.0 + half * squared) / (gamma * squared - half)), was_scalar)


def pressure_ratio(mach1: object, gas: PerfectGas) -> float | np.ndarray:
    """Static pressure jump ``p2/p1``.

    ``p2/p1 = 1 + 2 gamma/(gamma+1) (M1^2 - 1)``

    Written in this form rather than as a difference of large terms, so the
    weak-shock limit approaches 1 cleanly instead of by cancellation.
    """
    array, was_scalar = _validate(mach1)
    gamma = gas.gamma
    return restore_scalar(
        1.0 + 2.0 * gamma / (gamma + 1.0) * (array * array - 1.0), was_scalar
    )


def density_ratio(mach1: object, gas: PerfectGas) -> float | np.ndarray:
    """Density jump ``rho2/rho1``.

    ``rho2/rho1 = (gamma+1) M1^2 / [2 + (gamma-1) M1^2]``

    Bounded above by ``(gamma+1)/(gamma-1)`` however strong the shock -- 6 for
    air. See :func:`density_ratio_limit`.
    """
    array, was_scalar = _validate(mach1)
    gamma = gas.gamma
    squared = array * array
    return restore_scalar((gamma + 1.0) * squared / (2.0 + (gamma - 1.0) * squared), was_scalar)


def temperature_ratio(mach1: object, gas: PerfectGas) -> float | np.ndarray:
    """Static temperature jump ``T2/T1``.

    Computed as ``(p2/p1) / (rho2/rho1)`` rather than from an independent
    closed form. That guarantees ``p2/p1 = (rho2/rho1)(T2/T1)`` exactly -- the
    ideal gas law across the shock -- which a separately coded formula would
    satisfy only to round-off.
    """
    array, was_scalar = _validate(mach1)
    ratio = np.asarray(pressure_ratio(array, gas)) / np.asarray(density_ratio(array, gas))
    return restore_scalar(ratio, was_scalar)


def stagnation_pressure_ratio(mach1: object, gas: PerfectGas) -> float | np.ndarray:
    """Stagnation pressure ratio ``p02/p01``.

    ``p02/p01 = [(gamma+1) M1^2 / (2 + (gamma-1) M1^2)]^(gamma/(gamma-1))
                x [(gamma+1) / (2 gamma M1^2 - (gamma-1))]^(1/(gamma-1))``

    Always below 1 for M1 > 1: a shock is irreversible, and this ratio is the
    measure of that loss. It falls monotonically as the shock strengthens.
    """
    array, was_scalar = _validate(mach1)
    gamma = gas.gamma
    squared = array * array
    first = (gamma + 1.0) * squared / (2.0 + (gamma - 1.0) * squared)
    second = (gamma + 1.0) / (2.0 * gamma * squared - (gamma - 1.0))
    value = first ** (gamma / (gamma - 1.0)) * second ** (1.0 / (gamma - 1.0))
    return restore_scalar(value, was_scalar)


def stagnation_pressure_over_upstream_static(mach1: object, gas: PerfectGas) -> float | np.ndarray:
    """``p02/p1`` -- downstream stagnation over *upstream static* pressure.

    The Rayleigh pitot ratio: what a pitot probe in supersonic flow actually
    measures, since the probe sits behind its own bow shock. Anderson's
    Appendix B tabulates it, and it is a genuinely classical output rather than
    a column copied for its own sake.

    Composed from two verified relations,
    ``(p02/p01) x (p01/p1)``, and not given a closed form of its own.
    """
    array, was_scalar = _validate(mach1)
    upstream_stagnation = 1.0 / np.asarray(iso.pressure_ratio(array, gas))
    value = np.asarray(stagnation_pressure_ratio(array, gas)) * upstream_stagnation
    return restore_scalar(value, was_scalar)


def entropy_change(mach1: object, gas: PerfectGas) -> float | np.ndarray:
    """Entropy rise across the shock, ``(s2 - s1) / R`` [-].

    ``(s2 - s1)/R = -ln(p02/p01)``

    Dimensionless, so it needs no gas constant. Positive for every M1 > 1 and
    zero at M1 = 1: this is the second law made arithmetic, and it is the
    reason the subsonic branch is refused.
    """
    array, was_scalar = _validate(mach1)
    return restore_scalar(-np.log(np.asarray(stagnation_pressure_ratio(array, gas))), was_scalar)


def area_star_ratio(mach1: object, gas: PerfectGas) -> float | np.ndarray:
    """``A2*/A1*``, the growth of the sonic reference area across the shock.

    Equal to ``p01/p02``, because mass flow and stagnation temperature are both
    unchanged while stagnation pressure falls. This is what lets a nozzle
    solver continue downstream of an internal shock, and it is computed from
    the stagnation-pressure ratio rather than derived again.
    """
    array, was_scalar = _validate(mach1)
    return restore_scalar(1.0 / np.asarray(stagnation_pressure_ratio(array, gas)), was_scalar)


# ---------------------------------------------------------------------------
# inverse and limits
# ---------------------------------------------------------------------------


def mach_upstream_from_pressure_ratio(pressure_ratio_12: float, gas: PerfectGas) -> float:
    """Upstream Mach number from a measured static pressure jump.

    ``M1 = sqrt(1 + (gamma+1)/(2 gamma) (p2/p1 - 1))``

    Closed form, so no iteration: inverting the pressure relation is a single
    rearrangement. Requires ``p2/p1 >= 1``.
    """
    array, was_scalar = as_float_array(pressure_ratio_12, "pressure_ratio")
    require_finite(array, "pressure_ratio (p2/p1)")
    require_at_least(array, 1.0, "pressure_ratio (p2/p1); a shock compresses, so it cannot be below 1")
    gamma = gas.gamma
    value = np.sqrt(1.0 + (gamma + 1.0) / (2.0 * gamma) * (array - 1.0))
    return restore_scalar(value, was_scalar)


def density_ratio_limit(gas: PerfectGas) -> float:
    """The strong-shock density limit ``(gamma+1)/(gamma-1)``.

    6 for air. However strong the shock, a calorically perfect gas cannot be
    compressed further than this across it -- one of the clearest statements of
    where the perfect-gas model stops describing reality, since real air
    dissociates and compresses further.
    """
    return float((gas.gamma + 1.0) / (gas.gamma - 1.0))


def mach_downstream_limit(gas: PerfectGas) -> float:
    """The strong-shock limit of the downstream Mach number.

    ``sqrt((gamma-1)/(2 gamma))``, which is 0.37796 for air.
    """
    return float(np.sqrt((gas.gamma - 1.0) / (2.0 * gas.gamma)))


#: How far a vanishing denominator must stand clear of its own rounding error
#: before its reciprocal is trusted. The two inverses below both divide by a
#: difference that goes to zero at the strong-shock limit; at 1e-8 of the terms
#: being subtracted, the quotient still carries about eight significant digits,
#: and beyond it the answer is mostly cancellation. Chosen for that reason, not
#: tuned to make any particular input pass or fail.
_CANCELLATION_FLOOR = 1e-8


def mach_upstream_from_density_ratio(density_ratio_12: object, gas: PerfectGas) -> float | np.ndarray:
    """Upstream Mach number from a measured density jump.

    ``M1^2 = 2 r / [(gamma+1) - (gamma-1) r]``, with ``r = rho2/rho1``

    Closed form. The denominator vanishes as ``r`` approaches the strong-shock
    limit ``(gamma+1)/(gamma-1)``, which is the algebra restating that no finite
    Mach number reaches that compression.

    The refusal tests the denominator rather than comparing ``r`` against the
    limit, deliberately. ``(gamma+1)/(gamma-1)`` inherits the rounding of
    ``gamma - 1``: for air it evaluates to 6.000000000000001, so a user entering
    the textbook value of exactly 6.0 would slip under a ``>= limit`` test and be
    handed 1.6e8 as though it were a Mach number. Requiring the denominator to
    stand clear of its own round-off catches that, and refuses nothing whose
    answer would have been worth reporting.
    """
    array, was_scalar = as_float_array(density_ratio_12, "density_ratio")
    require_finite(array, "density_ratio (rho2/rho1)")
    require_at_least(
        array, 1.0,
        "density_ratio (rho2/rho1); a shock compresses, so it cannot be below 1",
    )
    gamma = gas.gamma
    limit = density_ratio_limit(gas)
    denominator = (gamma + 1.0) - (gamma - 1.0) * array
    scale = (gamma + 1.0) + (gamma - 1.0) * array
    if np.any(denominator <= _CANCELLATION_FLOOR * scale):
        raise DomainError(
            f"density_ratio (rho2/rho1) is at or past the strong-shock limit "
            f"{limit:.6g} for gamma = {gas.gamma}, where no finite upstream Mach "
            "number reaches that compression; "
            f"{describe_offender(denominator <= _CANCELLATION_FLOOR * scale, array)}"
        )
    value = np.sqrt(2.0 * array / denominator)
    return restore_scalar(value, was_scalar)


def mach_upstream_from_downstream_mach(mach2: object, gas: PerfectGas) -> float | np.ndarray:
    """Upstream Mach number from the downstream one.

    The M1-M2 relation is an involution: solving

        M2^2 = [1 + (gamma-1)/2 M1^2] / [gamma M1^2 - (gamma-1)/2]

    for M1 returns the *same* expression with the two swapped. So this is
    :func:`mach_downstream` evaluated at M2, and it is written that way rather
    than as a separately derived formula -- one relation, used both ways.

    The domain is the other half of the same curve: M2 lies above the
    strong-shock limit ``sqrt((gamma-1)/(2 gamma))`` and at or below 1. As in
    :func:`mach_upstream_from_density_ratio`, the lower end is guarded by
    testing the denominator against its own round-off rather than by comparing
    against a limit that carries round-off of its own.
    """
    array, was_scalar = as_float_array(mach2, "mach2")
    require_finite(array, "mach2")
    require_at_most(array, 1.0, "mach2 (the flow behind a shock is subsonic)")
    gamma = gas.gamma
    limit = mach_downstream_limit(gas)
    half = 0.5 * (gamma - 1.0)
    squared = array * array
    denominator = gamma * squared - half
    scale = gamma * squared + half
    if np.any(denominator <= _CANCELLATION_FLOOR * scale):
        raise DomainError(
            f"mach2 is at or below the strong-shock limit {limit:.6g} for gamma = "
            f"{gas.gamma}, where no shock produces that downstream Mach number; "
            f"{describe_offender(denominator <= _CANCELLATION_FLOOR * scale, array)}"
        )
    return restore_scalar(np.sqrt((1.0 + half * squared) / denominator), was_scalar)


def mach_upstream_from_stagnation_pressure_ratio(
    stagnation_ratio: float,
    gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]:
    """Upstream Mach number from a measured stagnation-pressure loss.

    Args:
        stagnation_ratio: ``p02/p01`` in (0, 1].
        gas: The gas model.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying the upstream Mach number.

    The one relation in this module with no closed-form inverse, so the one
    place it iterates. It is the easy kind of root problem: ``p02/p01`` falls
    strictly and smoothly from 1 at M1 = 1, so the root is unique and the
    bracket is the physical domain itself. The upper end starts at the Mach
    ceiling and is widened only while the residual has not changed sign, which
    keeps a loss of 1e-9 solvable without pretending Mach 3000 is meaningful.
    """
    array, _ = as_float_array(stagnation_ratio, "stagnation_ratio")
    require_finite(array, "stagnation_ratio (p02/p01)")
    require_above(array, 0.0, "stagnation_ratio (p02/p01)")
    value = float(array)
    if value > 1.0:
        raise DomainError(
            "stagnation_ratio (p02/p01) cannot exceed 1: a shock destroys stagnation "
            f"pressure, it never creates it, got {value!r}"
        )

    def residual(mach: float) -> float:
        return float(stagnation_pressure_ratio(mach, gas)) - value

    if value == 1.0:
        # The degenerate zero-strength shock. Answered exactly rather than by
        # iterating on a residual that is already zero.
        return Solution(
            value=1.0,
            status=Status.OK_WITH_WARNINGS if gas.diagnostics else Status.OK,
            diagnostics=gas.diagnostics,
            provenance=(REL_NORMAL_SHOCK,),
            inputs={"stagnation_pressure_ratio": value, "gamma": gas.gamma},
        )

    low, high = 1.0, tolerances.mach_ceiling
    while residual(high) > 0.0 and high < 1.0e5:
        high *= 4.0

    root, report = brent(
        residual,
        low,
        high,
        xtol=tolerances.mach_abs_tol,
        rtol=tolerances.mach_rel_tol,
        max_iter=tolerances.max_iter,
    )

    diagnostics: tuple[Diagnostic, ...] = ()
    if report.converged:
        status = Status.OK
    else:
        status = Status.NOT_CONVERGED
        diagnostics = (
            Diagnostic(
                code="NOT_CONVERGED",
                severity=Severity.ERROR,
                message=(
                    "The stagnation-pressure inversion did not converge within "
                    f"{report.iterations} iterations; the value returned is the best "
                    "estimate found and should not be used without checking."
                ),
                field="stagnation_pressure_ratio",
                detail={"residual": report.residual, "iterations": float(report.iterations)},
            ),
        )

    solution: Solution[float] = Solution(
        value=root,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_NORMAL_SHOCK,),
        convergence=Convergence.from_report(report),
        inputs={"stagnation_pressure_ratio": value, "gamma": gas.gamma},
    )
    return solution.with_diagnostics(*gas.diagnostics)


# ---------------------------------------------------------------------------
# grouped result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NormalShockResult:
    """Every normal-shock quantity at one upstream Mach number.

    Orientation is downstream over upstream throughout, stated in each name.

    Attributes:
        mach1: Upstream Mach number [-].
        mach2: Downstream Mach number [-]. Subsonic for any M1 > 1.
        pressure_ratio: p₂/p₁ [-], > 1.
        density_ratio: ρ₂/ρ₁ [-], > 1 and below (gamma+1)/(gamma-1).
        temperature_ratio: T₂/T₁ [-], > 1.
        stagnation_pressure_ratio: p₀₂/p₀₁ [-], in (0, 1].
        stagnation_pressure_over_upstream_static: p₀₂/p₁ [-], the pitot ratio.
        stagnation_temperature_ratio: T₀₂/T₀₁, exactly 1.0 for this adiabatic
            model -- a literal, not a computation that could drift.
        entropy_change: (s₂ − s₁)/R [-], >= 0.
        area_star_ratio: A₂*/A₁* [-], = p₀₁/p₀₂.
        sonic_limit: True at M1 = 1, where the shock has zero strength and
            every ratio is 1. Not a shock, a limit.
    """

    mach1: float
    mach2: float
    pressure_ratio: float
    density_ratio: float
    temperature_ratio: float
    stagnation_pressure_ratio: float
    stagnation_pressure_over_upstream_static: float
    stagnation_temperature_ratio: float
    entropy_change: float
    area_star_ratio: float
    sonic_limit: bool = False


def solve(mach1: float, gas: PerfectGas) -> NormalShockResult:
    """Every normal-shock quantity at one upstream Mach number.

    Scalar only: the record describes a single shock. Use the individual
    relations for sweeps, which are vectorised.

    Raises:
        SubsonicShockError: M1 < 1.
    """
    array, was_scalar = _validate(mach1)
    if not was_scalar:
        raise SubsonicShockError(
            "solve describes a single shock; pass a scalar Mach number or call "
            "the individual relations for an array"
        )
    value = float(array)
    return NormalShockResult(
        mach1=value,
        mach2=float(mach_downstream(value, gas)),
        pressure_ratio=float(pressure_ratio(value, gas)),
        density_ratio=float(density_ratio(value, gas)),
        temperature_ratio=float(temperature_ratio(value, gas)),
        stagnation_pressure_ratio=float(stagnation_pressure_ratio(value, gas)),
        stagnation_pressure_over_upstream_static=float(
            stagnation_pressure_over_upstream_static(value, gas)
        ),
        # Adiabatic: stagnation temperature is conserved across the shock. A
        # literal 1.0 rather than a computed ratio, so it cannot drift.
        stagnation_temperature_ratio=1.0,
        entropy_change=float(entropy_change(value, gas)),
        area_star_ratio=float(area_star_ratio(value, gas)),
        sonic_limit=abs(value - 1.0) <= DEFAULT_TOLERANCES.sonic_tol,
    )
