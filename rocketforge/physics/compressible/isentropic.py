"""Isentropic relations for a calorically perfect gas.

Specified in ``docs/engineering/03_compressible_flow_specification.md``
section 3. Steady, adiabatic, reversible, calorically perfect: no chemistry,
no variable gamma, no losses, no shocks, and no geometry of its own -- the area
relation takes an area *ratio*, never a contour.

Every relation is built on one group,

    phi(M) = 1 + (gamma - 1)/2 * M**2 = T0/T

computed once per call and raised to the exponent each ratio needs. That is
both faster and better conditioned than repeating the bracket, and it means a
reader checking the code against the printed equation has one expression to
check rather than four.

Two tiers of API, per ADR-07:

* the ratios and the three analytic inverses are algebraic and total on their
  domain, so they return the bare number and accept scalars or arrays;
* the area-Mach inverse is branched and iterative, so it returns a
  :class:`~rocketforge.core.result.Solution` carrying the branch, the
  convergence record and any advisories.

Orientation is fixed and stated in every name: ``temperature_ratio`` is T/T0,
never T0/T. A reader should never have to open the source to learn which way
up a ratio is.
"""

from __future__ import annotations

import math
from typing import Callable

import numpy as np

from ...core.errors import AreaRatioError, DomainError
from ...core.numerics.arrays import (
    as_float_array,
    require_above,
    require_at_least,
    require_at_most,
    require_finite,
    restore_scalar,
)
from ...core.numerics.roots import RootReport, brent
from ...core.result import Convergence, Diagnostic, Severity, Solution, Status
from ...core.tolerances import DEFAULT_TOLERANCES, ToleranceSet
from .equations import (
    MODEL_ISENTROPIC,
    REL_AREA_RATIO,
    REL_DENSITY_RATIO,
    REL_MACH_ANGLE,
    REL_PRESSURE_RATIO,
    REL_STARRED_RATIOS,
    REL_TEMPERATURE_RATIO,
)
from .gas import PerfectGas
from .types import AreaMachSolutions, FlowBranch, IsentropicRatios

__all__ = [
    "temperature_ratio",
    "pressure_ratio",
    "density_ratio",
    "area_ratio",
    "temperature_ratio_star",
    "pressure_ratio_star",
    "density_ratio_star",
    "mach_angle",
    "ratios_from_mach",
    "mach_from_temperature_ratio",
    "mach_from_pressure_ratio",
    "mach_from_density_ratio",
    "mach_from_area_ratio",
    "mach_from_area_ratio_both",
    "mach_from_area_ratio_array",
    "MODEL_ISENTROPIC",
]


# ---------------------------------------------------------------------------
# internals
# ---------------------------------------------------------------------------


def _mach_array(mach: object, *, allow_zero: bool = True) -> tuple[np.ndarray, bool]:
    """Validate a Mach argument and return it as float64.

    Mach number here is a non-negative speed ratio. A negative value is a
    programming error, not a direction: it is rejected rather than having its
    magnitude taken, because silently accepting ``-2`` would hide the bug that
    produced it (``04`` section 8).
    """
    array, was_scalar = as_float_array(mach, "mach")
    require_finite(array, "mach")
    if allow_zero:
        require_at_least(array, 0.0, "mach")
    else:
        require_above(array, 0.0, "mach")
    return array, was_scalar


def _ratio_array(ratio: object, name: str) -> tuple[np.ndarray, bool]:
    """Validate a static-to-stagnation ratio, which lies in (0, 1]."""
    array, was_scalar = as_float_array(ratio, name)
    require_finite(array, name)
    require_above(array, 0.0, name)
    require_at_most(array, 1.0, name)
    return array, was_scalar


def _phi(mach: np.ndarray, gamma: float) -> np.ndarray:
    """The recurring group ``1 + (gamma-1)/2 M^2``, which is T0/T."""
    return 1.0 + 0.5 * (gamma - 1.0) * mach * mach


def _starred_bracket(mach: np.ndarray, gamma: float) -> np.ndarray:
    """``(gamma+1) / (2 + (gamma-1) M^2)``, which is T/T*."""
    return (gamma + 1.0) / (2.0 + (gamma - 1.0) * mach * mach)


def _area_ratio_exponent(gamma: float) -> float:
    """``(gamma+1) / (2 (gamma-1))``, the exponent of the area relation."""
    return (gamma + 1.0) / (2.0 * (gamma - 1.0))


# ---------------------------------------------------------------------------
# forward relations
# ---------------------------------------------------------------------------


def temperature_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """Static over stagnation temperature, ``T/T0``.

    ``T/T0 = [1 + (gamma-1)/2 M^2]^-1``

    Args:
        mach: Mach number [-], >= 0. Scalar or array.
        gas: The gas model; only ``gamma`` is used.

    Returns:
        T/T0 [-], in (0, 1]. Exactly 1 at M = 0.

    Raises:
        DomainError: Mach is negative or not finite.
    """
    array, was_scalar = _mach_array(mach)
    return restore_scalar(1.0 / _phi(array, gas.gamma), was_scalar)


def pressure_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """Static over stagnation pressure, ``p/p0``.

    ``p/p0 = [1 + (gamma-1)/2 M^2]^(-gamma/(gamma-1))``

    Returns the static-over-stagnation orientation, which is bounded on (0, 1]
    and therefore both better conditioned and directly plottable; the
    reciprocal is the caller's to take.
    """
    array, was_scalar = _mach_array(mach)
    gamma = gas.gamma
    exponent = -gamma / (gamma - 1.0)
    return restore_scalar(_phi(array, gamma) ** exponent, was_scalar)


def density_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """Static over stagnation density, ``rho/rho0``.

    ``rho/rho0 = [1 + (gamma-1)/2 M^2]^(-1/(gamma-1))``
    """
    array, was_scalar = _mach_array(mach)
    gamma = gas.gamma
    exponent = -1.0 / (gamma - 1.0)
    return restore_scalar(_phi(array, gamma) ** exponent, was_scalar)


def area_ratio(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """Duct area over sonic reference area, ``A/A*``.

    ``A/A* = (1/M) [ (2/(gamma+1)) (1 + (gamma-1)/2 M^2) ]^((gamma+1)/(2(gamma-1)))``

    Args:
        mach: Mach number [-], strictly positive. Scalar or array.
        gas: The gas model; only ``gamma`` is used.

    Returns:
        A/A* [-], >= 1, with its minimum of exactly 1 at M = 1.

    Raises:
        DomainError: Mach is zero, negative, or not finite. M = 0 is rejected
            rather than returning infinity: the area ratio is genuinely
            unbounded there, and an ``inf`` would propagate silently into a
            plot axis or a downstream sum.
    """
    array, was_scalar = _mach_array(mach, allow_zero=False)
    gamma = gas.gamma
    inner = (2.0 / (gamma + 1.0)) * _phi(array, gamma)
    return restore_scalar(inner ** _area_ratio_exponent(gamma) / array, was_scalar)


def temperature_ratio_star(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """Static temperature over its sonic value, ``T/T*``.

    ``T/T* = (gamma+1) / (2 + (gamma-1) M^2)``

    Note the orientation: this is T over T-star, so it is greater than 1 below
    the sonic point and less than 1 above it, and equals 1 exactly at M = 1.
    """
    array, was_scalar = _mach_array(mach)
    return restore_scalar(_starred_bracket(array, gas.gamma), was_scalar)


def pressure_ratio_star(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """Static pressure over its sonic value, ``p/p*``.

    ``p/p* = [ (gamma+1) / (2 + (gamma-1) M^2) ]^(gamma/(gamma-1))``
    """
    array, was_scalar = _mach_array(mach)
    gamma = gas.gamma
    return restore_scalar(
        _starred_bracket(array, gamma) ** (gamma / (gamma - 1.0)), was_scalar
    )


def density_ratio_star(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """Static density over its sonic value, ``rho/rho*``.

    ``rho/rho* = [ (gamma+1) / (2 + (gamma-1) M^2) ]^(1/(gamma-1))``
    """
    array, was_scalar = _mach_array(mach)
    gamma = gas.gamma
    return restore_scalar(
        _starred_bracket(array, gamma) ** (1.0 / (gamma - 1.0)), was_scalar
    )


def mach_angle(mach: object) -> float | np.ndarray:
    """Mach angle ``mu = arcsin(1/M)`` [rad].

    Args:
        mach: Mach number [-], >= 1. Scalar or array.

    Returns:
        The Mach angle in **radians**. Degrees exist only above the application
        boundary; a name ending in ``_deg`` is forbidden in this layer.

    Raises:
        DomainError: M < 1, where no Mach wave exists.

    Takes no gas model: the Mach angle is geometry, independent of gamma.
    """
    array, was_scalar = as_float_array(mach, "mach")
    require_finite(array, "mach")
    require_at_least(array, 1.0, "mach (a Mach wave exists only in supersonic flow)")
    return restore_scalar(np.arcsin(1.0 / array), was_scalar)


def ratios_from_mach(mach: float, gas: PerfectGas) -> IsentropicRatios:
    """Every isentropic ratio at one Mach number, as one record.

    Scalar only: the record describes a single flow state. Use the individual
    relations for sweeps.

    ``area_ratio`` is None at M = 0 and ``mach_angle`` is None below M = 1,
    rather than being filled with a placeholder -- a field that does not apply
    is absent, not fabricated.
    """
    array, was_scalar = _mach_array(mach)
    if not was_scalar:
        raise DomainError(
            "ratios_from_mach describes a single state; pass a scalar Mach number "
            "or call the individual relations for an array"
        )
    value = float(array)
    return IsentropicRatios(
        mach=value,
        temperature_ratio=float(temperature_ratio(value, gas)),
        pressure_ratio=float(pressure_ratio(value, gas)),
        density_ratio=float(density_ratio(value, gas)),
        area_ratio=float(area_ratio(value, gas)) if value > 0.0 else None,
        temperature_ratio_star=float(temperature_ratio_star(value, gas)),
        pressure_ratio_star=float(pressure_ratio_star(value, gas)),
        density_ratio_star=float(density_ratio_star(value, gas)),
        mach_angle=float(mach_angle(value)) if value >= 1.0 else None,
        # Populated when the Prandtl-Meyer module lands; see types.py.
        prandtl_meyer_angle=None,
    )


# ---------------------------------------------------------------------------
# analytic inverses
# ---------------------------------------------------------------------------
#
# Three of the four inverses are closed form and must never be solved
# numerically: an iteration here would be slower, less accurate, and would
# invent a convergence question where none exists.


def mach_from_temperature_ratio(ratio: object, gas: PerfectGas) -> float | np.ndarray:
    """Mach number from ``T/T0``.

    ``M = sqrt( 2/(gamma-1) * (T0/T - 1) )``

    Args:
        ratio: T/T0 [-], in (0, 1]. Scalar or array.
        gas: The gas model.

    Returns:
        Mach number [-]. Exactly 0 when the ratio is exactly 1.

    Raises:
        DomainError: Ratio is not finite, is <= 0, or exceeds 1. A ratio above
            1 would mean a static temperature above stagnation, which is not a
            flow state; it is rejected, never clamped.
    """
    array, was_scalar = _ratio_array(ratio, "temperature_ratio (T/T0)")
    gamma = gas.gamma
    return restore_scalar(np.sqrt(2.0 / (gamma - 1.0) * (1.0 / array - 1.0)), was_scalar)


def mach_from_pressure_ratio(ratio: object, gas: PerfectGas) -> float | np.ndarray:
    """Mach number from ``p/p0``.

    ``M = sqrt( 2/(gamma-1) * [ (p0/p)^((gamma-1)/gamma) - 1 ] )``

    Evaluated as ``expm1(-(gamma-1)/gamma * log(p/p0))`` rather than as the
    difference written above. The two are algebraically identical, but as
    p/p0 approaches 1 the bracket is the difference of two nearly equal
    numbers: at p/p0 = 0.999 the naive form has already lost about three
    significant figures, while ``expm1`` loses none (``04`` section 11).
    """
    array, was_scalar = _ratio_array(ratio, "pressure_ratio (p/p0)")
    gamma = gas.gamma
    inner = np.expm1(-(gamma - 1.0) / gamma * np.log(array))
    return restore_scalar(np.sqrt(2.0 / (gamma - 1.0) * inner), was_scalar)


def mach_from_density_ratio(ratio: object, gas: PerfectGas) -> float | np.ndarray:
    """Mach number from ``rho/rho0``.

    ``M = sqrt( 2/(gamma-1) * [ (rho0/rho)^(gamma-1) - 1 ] )``

    Uses ``expm1`` for the same conditioning reason as
    :func:`mach_from_pressure_ratio`.
    """
    array, was_scalar = _ratio_array(ratio, "density_ratio (rho/rho0)")
    gamma = gas.gamma
    inner = np.expm1(-(gamma - 1.0) * np.log(array))
    return restore_scalar(np.sqrt(2.0 / (gamma - 1.0) * inner), was_scalar)


# ---------------------------------------------------------------------------
# area-Mach inverse
# ---------------------------------------------------------------------------


def _validate_area_ratio(value: object, tolerances: ToleranceSet) -> float:
    """Validate a scalar area ratio against the sonic-tolerance policy."""
    array, was_scalar = as_float_array(value, "area_ratio")
    if not was_scalar:
        raise DomainError(
            "mach_from_area_ratio takes a scalar; use mach_from_area_ratio_array for a sweep"
        )
    ratio = float(array)
    if not math.isfinite(ratio):
        raise DomainError(f"area_ratio must be finite, got {ratio!r}")
    if ratio < 1.0 - tolerances.area_sonic_tol:
        raise AreaRatioError(
            f"area_ratio must be >= 1, got {ratio!r}. A/A* is the duct area divided by "
            "the area at which the same flow would be sonic, so it has a minimum of "
            "exactly 1 at M = 1. The value is not clamped."
        )
    return ratio


def _sonic_solution(
    ratio: float, branch: FlowBranch, gas: PerfectGas, tolerances: ToleranceSet
) -> Solution[float]:
    """The exact answer inside the sonic window: M = 1, with no iteration.

    Asking the root finder to resolve this would be worse than pointless: at
    the minimum the derivative of A/A* vanishes, so the relation is
    quadratically flat and an area ratio within 1e-11 of unity pins the Mach
    number only to about 3.5e-6 either side. Returning exactly 1 is the most
    accurate answer available, and the diagnostic says so.
    """
    solution: Solution[float] = Solution(
        value=1.0,
        status=Status.OK,
        diagnostics=(
            Diagnostic(
                code="SONIC_EXACT",
                severity=Severity.INFO,
                message=(
                    "Area ratio is within the sonic tolerance of unity, so Mach 1 is "
                    "returned exactly for either branch."
                ),
                field="area_ratio",
                detail={"area_ratio": ratio, "area_sonic_tol": tolerances.area_sonic_tol},
            ),
        ),
        provenance=(REL_AREA_RATIO,),
        convergence=Convergence(
            converged=True,
            iterations=0,
            residual=abs(ratio - 1.0),
            tolerance=tolerances.area_sonic_tol,
            bracket=None,
            method="analytic",
        ),
        inputs={"area_ratio": ratio, "gamma": gas.gamma},
    )
    return solution.with_diagnostics(*gas.diagnostics)


def _subsonic_bracket(ratio: float, gas: PerfectGas, tolerances: ToleranceSet,
                      residual: Callable[[float], float]) -> tuple[float, float]:
    """Bracket the subsonic root, seeded from the M -> 0 asymptote.

    As M -> 0 the area relation tends to ``(1/M) (2/(gamma+1))^k`` with
    ``k = (gamma+1)/(2(gamma-1))``, which inverts exactly:
    ``M ~ (2/(gamma+1))^k / (A/A*)``. Halving that guarantees the residual is
    positive there; the loop is a safety net that almost never runs.
    """
    gamma = gas.gamma
    k = _area_ratio_exponent(gamma)
    seed = 0.5 * (2.0 / (gamma + 1.0)) ** k / ratio
    low = min(max(seed, tolerances.mach_floor), 1.0 - tolerances.sonic_margin)
    while residual(low) < 0.0 and low > tolerances.mach_floor:
        low = max(low * 0.5, tolerances.mach_floor)
    return low, 1.0 - tolerances.sonic_margin


def _supersonic_bracket(ratio: float, gas: PerfectGas, tolerances: ToleranceSet,
                        residual: Callable[[float], float]) -> tuple[float, float]:
    """Bracket the supersonic root, seeded from the M -> infinity asymptote.

    As M -> infinity the area relation tends to
    ``M^(2/(gamma-1)) * ((gamma-1)/(gamma+1))^k`` with
    ``k = (gamma+1)/(2(gamma-1))``, so
    ``M ~ [ (A/A*) ((gamma+1)/(gamma-1))^k ]^((gamma-1)/2)``.

    ERRATUM-4B-01: ``04`` section 3.1 prints this asymptote with the exponent
    ``(gamma+1)/(gamma-1)`` on M and ``(gamma-1)/(gamma+1)`` on the inversion.
    Both are wrong; the correct exponents are ``2/(gamma-1)`` and
    ``(gamma-1)/2``. Check at gamma = 1.4, M = 100: the correct form gives
    ``100^5 / 216 = 4.63e7`` against the true 4.6366e7, while the printed form
    gives ``100^6 / 216 = 4.63e9``, a factor of 100 out. The corrected form is
    implemented here and the erratum is recorded in the Phase 4B note.
    """
    gamma = gas.gamma
    k = _area_ratio_exponent(gamma)
    seed = (ratio * ((gamma + 1.0) / (gamma - 1.0)) ** k) ** ((gamma - 1.0) * 0.5)
    high = min(max(2.0 * seed, 1.0 + tolerances.sonic_margin), tolerances.mach_ceiling)
    while residual(high) < 0.0 and high < tolerances.mach_ceiling:
        high = min(high * 2.0, tolerances.mach_ceiling)
    return 1.0 + tolerances.sonic_margin, high


def _near_sonic_diagnostic(mach: float, tolerances: ToleranceSet, gamma: float) -> tuple[Diagnostic, ...]:
    """Advise when the solved Mach number is close enough to sonic to matter."""
    if abs(mach - 1.0) > tolerances.near_sonic_mach:
        return ()
    return (
        Diagnostic(
            code="NEAR_SONIC",
            severity=Severity.WARNING,
            message=(
                "The solution lies close to the sonic point, where A/A* is "
                "quadratically flat: an area ratio known to a relative accuracy d "
                "fixes the Mach number only to about sqrt((gamma+1)/2 * d), so the "
                "Mach number is less well determined than the area ratio."
            ),
            field="area_ratio",
            detail={"mach": mach, "near_sonic_mach": tolerances.near_sonic_mach, "gamma": gamma},
        ),
    )


def _convergence(report: RootReport) -> Convergence:
    """Map the root solver's report onto the physics-layer record."""
    return Convergence.from_report(report)


def mach_from_area_ratio(
    area_ratio_value: object,
    gas: PerfectGas,
    branch: FlowBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]:
    """Mach number from ``A/A*`` on an explicitly chosen branch.

    Args:
        area_ratio_value: A/A* [-], >= 1. Scalar.
        gas: The gas model; only ``gamma`` is used.
        branch: ``FlowBranch.SUBSONIC`` or ``FlowBranch.SUPERSONIC``. Required,
            with no default: the relation has two roots for every area ratio
            above one and the equations cannot say which the caller means.
            Use :func:`mach_from_area_ratio_both` to get both.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying the Mach number, the convergence record,
        and any advisories -- ``SONIC_EXACT`` inside the sonic window,
        ``NEAR_SONIC`` just outside it, ``EXTRAPOLATED_GAMMA`` from the gas.

    Raises:
        AreaRatioError: The area ratio is below 1 and outside the sonic window.
        DomainError: The area ratio is not a finite scalar.
        ValueError: ``branch`` is ``BOTH`` or not a :class:`FlowBranch`.

    The relation is not invertible in closed form, so this is solved with the
    project's own bracketed root finder. The bracket is derived from the
    asymptotic behaviour of the relation rather than guessed, and each branch
    is solved on its own interval, which is what makes the root unique.
    """
    if not isinstance(branch, FlowBranch):
        raise ValueError(
            f"branch must be a FlowBranch, got {branch!r}. The area-Mach relation has "
            "two roots and the caller must state which is wanted."
        )
    if branch is FlowBranch.BOTH:
        raise ValueError(
            "branch=BOTH is a request for two roots; call mach_from_area_ratio_both, "
            "which returns them as named fields"
        )

    ratio = _validate_area_ratio(area_ratio_value, tolerances)
    if abs(ratio - 1.0) <= tolerances.area_sonic_tol:
        return _sonic_solution(ratio, branch, gas, tolerances)

    def residual(mach: float) -> float:
        return float(area_ratio(mach, gas)) - ratio

    if branch is FlowBranch.SUBSONIC:
        low, high = _subsonic_bracket(ratio, gas, tolerances, residual)
    else:
        low, high = _supersonic_bracket(ratio, gas, tolerances, residual)

    root, report = brent(
        residual,
        low,
        high,
        xtol=tolerances.mach_abs_tol,
        rtol=tolerances.mach_rel_tol,
        max_iter=tolerances.max_iter,
    )

    diagnostics = _near_sonic_diagnostic(root, tolerances, gas.gamma)
    if report.converged:
        status = Status.OK_WITH_WARNINGS if diagnostics else Status.OK
    else:
        status = Status.NOT_CONVERGED
        diagnostics = diagnostics + (
            Diagnostic(
                code="NOT_CONVERGED",
                severity=Severity.ERROR,
                message=(
                    f"The area-Mach inversion did not converge within "
                    f"{report.iterations} iterations; the value returned is the best "
                    "estimate found and should not be used without checking."
                ),
                field="area_ratio",
                detail={"residual": report.residual, "iterations": float(report.iterations)},
            ),
        )

    solution: Solution[float] = Solution(
        value=root,
        status=status,
        diagnostics=diagnostics,
        provenance=(REL_AREA_RATIO,),
        convergence=_convergence(report),
        inputs={"area_ratio": ratio, "gamma": gas.gamma},
    )
    return solution.with_diagnostics(*gas.diagnostics)


def mach_from_area_ratio_both(
    area_ratio_value: object,
    gas: PerfectGas,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[AreaMachSolutions]:
    """Both Mach numbers that share an area ratio.

    Returns a :class:`Solution` wrapping :class:`AreaMachSolutions`, whose
    fields are named ``subsonic`` and ``supersonic`` so no caller has to
    remember an ordering. Inside the sonic window both are exactly 1 and
    ``sonic`` is True.
    """
    subsonic = mach_from_area_ratio(area_ratio_value, gas, FlowBranch.SUBSONIC, tolerances)
    supersonic = mach_from_area_ratio(area_ratio_value, gas, FlowBranch.SUPERSONIC, tolerances)

    ratio = float(subsonic.inputs["area_ratio"]) if subsonic.inputs else float("nan")
    sonic = abs(ratio - 1.0) <= tolerances.area_sonic_tol

    # Deduplicate diagnostics: both branches report the same gas advisory and,
    # inside the sonic window, the same SONIC_EXACT remark.
    seen: dict[str, Diagnostic] = {}
    for diagnostic in subsonic.diagnostics + supersonic.diagnostics:
        seen.setdefault(diagnostic.code, diagnostic)

    if subsonic.ok and supersonic.ok:
        status = Status.OK_WITH_WARNINGS if any(
            d.severity is not Severity.INFO for d in seen.values()
        ) else Status.OK
        value = AreaMachSolutions(
            area_ratio=ratio,
            subsonic=float(subsonic.value),  # type: ignore[arg-type]
            supersonic=float(supersonic.value),  # type: ignore[arg-type]
            sonic=sonic,
        )
    else:
        status = Status.NOT_CONVERGED
        value = None  # type: ignore[assignment]

    return Solution(
        value=value,
        status=status,
        diagnostics=tuple(seen.values()),
        provenance=(REL_AREA_RATIO,),
        convergence=supersonic.convergence,
        inputs={"area_ratio": ratio, "gamma": gas.gamma},
    )


def mach_from_area_ratio_array(
    area_ratio_values: object,
    gas: PerfectGas,
    branch: FlowBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> np.ndarray:
    """Vectorised area-Mach inversion on one branch.

    Args:
        area_ratio_values: Array of A/A* [-], each >= 1.
        gas: The gas model.
        branch: The branch, required as for the scalar form.
        tolerances: Numerical tolerances.

    Returns:
        A float64 array of Mach numbers, the same shape as the input.

    Raises:
        AreaRatioError: Any element is below 1 outside the sonic window.
        RuntimeError: Any element failed to converge. The whole call fails
            rather than returning a NaN for that element: a NaN in a plotted
            series is a silent hole that looks like a rendering fault.

    A Python-level loop over the scalar solver, deliberately. A vectorised
    iteration would converge element by element at different rates and make the
    result depend on the batch it was computed in, which the determinism rule
    forbids. At a few thousand points the loop costs milliseconds.
    """
    array, _ = as_float_array(area_ratio_values, "area_ratio")
    require_finite(array, "area_ratio")
    flat = np.atleast_1d(array).ravel()
    out = np.empty_like(flat)
    for index, value in enumerate(flat):
        solution = mach_from_area_ratio(float(value), gas, branch, tolerances)
        if not solution.ok or solution.value is None:
            raise RuntimeError(
                f"area-Mach inversion failed at index {index} (A/A* = {float(value)!r}): "
                + "; ".join(f"[{d.code}] {d.message}" for d in solution.diagnostics)
            )
        out[index] = solution.value
    return out.reshape(array.shape) if array.ndim else out.reshape(())
