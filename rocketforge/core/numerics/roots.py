"""Bracketed scalar root finding.

Implements the Brent-Dekker method chosen in
``docs/engineering/04_numerical_methods_and_domain_policy.md`` section 2 as the
baseline for every inverse relation in RocketForge: area-Mach inversion,
Prandtl-Meyer inversion, oblique-shock wave angle, Fanno and Rayleigh
inversions, and the internal nozzle shock location.

Why this method, restated from the specification so the choice is visible where
the code is: all of those inverses are scalar, continuous and strictly monotone
on a physically bounded interval. Brent combines inverse quadratic
interpolation, the secant rule and bisection, taking a fast step only when it
provably stays inside the maintained bracket and falling back to bisection
otherwise. It therefore converges superlinearly on smooth problems while never
being slower than bisection in the worst case, and -- unlike Newton -- it cannot
leave the domain. That last property is decisive here: ``dA/dM`` and ``dnu/dM``
both vanish at ``M = 1``, so a Newton step taken anywhere near sonic divides by
a near-zero derivative and lands outside the physical branch, returning a wrong
answer rather than an error.

The implementation is RocketForge's own, written from the published description
of the algorithm. It is not derived from SciPy, which is deliberately not a
runtime dependency (ADR-09); SciPy is used only as an independent oracle in
``tests/core/test_roots_cross_validation.py``.

Scope, and what this function deliberately does *not* do:

* It never widens, shifts or searches outside the supplied bracket. Deriving a
  physically meaningful bracket belongs to the caller -- in RocketForge, to the
  physics module that knows which monotone branch it is inverting.
* It finds *a* root in a sign-changing bracket. It does not enumerate roots and
  it makes no claim about which root it returns if the caller supplies an
  interval containing several.
* It requires a sign change. A root of even multiplicity, such as ``(x-1)**2``,
  does not produce one and is outside the contract unless it happens to sit on
  an endpoint.
* It never raises on failure to converge. Running out of iterations returns the
  best estimate with ``converged=False`` so the caller can decide whether that
  is a warning or an error.

Function side effects are unsupported. The solver evaluates ``f`` only where it
needs to and makes no guarantee about the order or number of evaluations beyond
what :class:`RootReport` records; RocketForge's own physics functions are pure.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from typing import Callable, Final

from ..errors import BracketError, InputError, NonFiniteEvaluationError

__all__ = ["brent", "RootReport", "METHOD_BRENT"]

#: Stable identifier for the algorithm, recorded in :attr:`RootReport.method`
#: and carried onward into the physics layer's ``Convergence`` record and from
#: there into result provenance. It names the algorithm, never a transient
#: implementation detail, so it is safe to store and compare.
METHOD_BRENT: Final = "brent"

#: How many times the bracket may fail to halve before the solver stops
#: trusting interpolation to shrink it and bisects on every pass. See the
#: halving safeguard in :func:`brent`.
_STALL_ESCALATION: Final = 2


@dataclass(frozen=True, slots=True)
class RootReport:
    """What happened during a root solve.

    Immutable, and built from plain floats and tuples so it can be stored,
    compared, serialised or handed to another thread. It maps directly onto the
    physics layer's ``Convergence`` record (``02`` section 2.3): the first six
    fields are that record, in that order.

    Attributes:
        converged: True when the bracket was refined to within
            :attr:`tolerance`, or an exact zero of ``f`` was found. False only
            when the iteration ceiling was reached.
        iterations: Iterations performed. Zero for a root found at a bracket
            endpoint or for a bracket already narrower than the tolerance.
        residual: ``|f(x)|`` at the returned root. Reported, never used as a
            termination criterion -- see :func:`brent`.
        tolerance: The accuracy window actually applied at the returned root:
            ``xtol + rtol * |root|``, widened to a few units in the last place
            if the request was tighter than the floating-point grid can
            resolve. On convergence the true root lies within this distance of
            the returned value.
        bracket: The final maintained interval, ordered low to high. Its
            endpoints straddle a root, except where the returned value is
            itself an exact zero.
        method: :data:`METHOD_BRENT`.
        function_calls: Total evaluations of ``f``, including the endpoints.
            Deterministic for a given problem.
        initial_bracket: The interval as supplied, ordered low to high.
    """

    converged: bool
    iterations: int
    residual: float
    tolerance: float
    bracket: tuple[float, float]
    method: str
    function_calls: int
    initial_bracket: tuple[float, float]


def brent(
    f: Callable[[float], float],
    a: float,
    b: float,
    *,
    xtol: float,
    rtol: float,
    max_iter: int,
) -> tuple[float, RootReport]:
    """Find a root of ``f`` in the bracketing interval ``[a, b]``.

    Args:
        f: The objective. Called with a single float and must return a finite
            real number. The variable is whatever the caller is solving for and
            carries no units of its own; RocketForge's convention is that any
            quantity crossing this boundary is already in SI, and angles in
            radians.
        a: Lower bracket endpoint. Must be finite and strictly less than ``b``.
        b: Upper bracket endpoint. Must be finite.
        xtol: Absolute accuracy required in the root. Must be finite and
            strictly positive.
        rtol: Relative accuracy required in the root. Must be finite and
            non-negative.
        max_iter: Iteration ceiling, at least 1.

    Returns:
        ``(root, report)``. On convergence the true root lies within
        ``report.tolerance`` of the returned value -- that is
        ``xtol + rtol * |root|``, or a few units in the last place if the
        request was tighter than double precision can resolve. On exhaustion
        the value is the best estimate found and ``report.converged`` is False.

    Raises:
        TypeError: ``f`` is not callable, or an argument is not a real number.
        InputError: A bracket endpoint or tolerance is not finite, ``a >= b``,
            ``xtol <= 0``, ``rtol < 0``, or ``max_iter < 1``.
        BracketError: ``f(a)`` and ``f(b)`` share a sign and neither endpoint is
            a root. The interval is not widened.
        NonFiniteEvaluationError: ``f`` returned NaN or an infinity.

    Termination is on the *root*, not on the residual: iteration stops when the
    maintained bracket is narrower than ``xtol + rtol * |b|``, or when an exact
    zero is found. ``residual_tol`` from the tolerance set is an acceptance
    criterion for callers, not a stopping rule, because a small residual does
    not imply an accurate root -- on a flat function such as ``(x-1)**3``,
    ``|f| <= 1e-10`` is already satisfied at ``|x-1| = 4.6e-4``, so stopping
    there would return four correct digits while claiming ten. Both numbers are
    reported and the caller applies whichever criterion its problem needs.

    Example:
        >>> root, report = brent(lambda x: x * x - 2.0, 0.0, 2.0,
        ...                      xtol=1e-12, rtol=1e-14, max_iter=100)
        >>> report.converged
        True
        >>> abs(root - 2.0 ** 0.5) < 1e-12
        True
    """
    if not callable(f):
        raise TypeError(f"f must be callable, got {type(f).__name__}")

    a = _finite_argument(a, "a")
    b = _finite_argument(b, "b")
    xtol = _finite_argument(xtol, "xtol")
    rtol = _finite_argument(rtol, "rtol")

    if a >= b:
        raise InputError(
            f"the bracket must satisfy a < b, got a={a!r}, b={b!r}. "
            "The solver does not reorder the interval: a bracket in the wrong "
            "order usually means the caller derived it incorrectly."
        )
    if xtol <= 0.0:
        raise InputError(f"xtol must be strictly positive, got {xtol!r}")
    if rtol < 0.0:
        raise InputError(f"rtol must be non-negative, got {rtol!r}")
    if isinstance(max_iter, bool) or not isinstance(max_iter, int):
        raise InputError(f"max_iter must be an int, got {type(max_iter).__name__}")
    if max_iter < 1:
        raise InputError(f"max_iter must be at least 1, got {max_iter}")

    initial_bracket = (a, b)
    calls = 0

    def evaluate(x: float) -> float:
        """Call the objective, counting the call and rejecting non-finite values."""
        nonlocal calls
        value = float(f(x))
        calls += 1
        if not math.isfinite(value):
            raise NonFiniteEvaluationError(
                f"f({x!r}) returned {value!r}; the root solver cannot continue "
                "because comparisons against a non-finite value are meaningless. "
                "Restrict the bracket to the region where f is finite."
            )
        return value

    # Endpoints are checked for an exact zero before the sign test, so a caller
    # whose bracket happens to start or end on the root gets it back rather
    # than a BracketError. Signed zero needs no special case: -0.0 == 0.0.
    fa = evaluate(a)
    if fa == 0.0:
        return a, _report(True, 0, 0.0, a, (a, b), calls, initial_bracket, xtol, rtol)

    fb = evaluate(b)
    if fb == 0.0:
        return b, _report(True, 0, 0.0, b, (a, b), calls, initial_bracket, xtol, rtol)

    if not _straddles(fa, fb):
        raise BracketError(
            f"f(a) and f(b) have the same sign, so [{a!r}, {b!r}] does not bracket "
            f"a root: f(a)={fa!r}, f(b)={fb!r}. The solver does not widen the "
            "interval or search outside it; supply a bracket that straddles the root."
        )

    # b holds the current best estimate, a the contrapoint, c the previous
    # iterate. The invariants maintained at the top of every pass are:
    #   * f(b) and f(c) have opposite signs, so [b, c] brackets a root;
    #   * |f(b)| <= |f(c)|, so b is the better of the two estimates.
    if abs(fa) < abs(fb):
        a, b = b, a
        fa, fb = fb, fa

    c, fc = a, fa
    step = previous_step = b - a
    iteration = 0

    # Bracket widths from the two previous passes, and how often the halving
    # safeguard has had to intervene. Seeded with the initial width so the
    # first passes are free to interpolate.
    width_previous = width_two_ago = abs(c - b)
    stalls = 0

    # One extra pass so that an exhausted budget still ends with the invariants
    # restored and the convergence test applied to the final iterate.
    for iteration in range(max_iter + 1):
        if fb == 0.0:
            return b, _report(True, iteration, 0.0, b, _ordered(b, c), calls,
                              initial_bracket, xtol, rtol)

        if _same_sign(fb, fc):
            # c stopped straddling the root; the other endpoint still does.
            c, fc = a, fa
            step = previous_step = b - a
        if abs(fc) < abs(fb):
            # c is the better estimate: rotate so b is always the best one.
            a, fa = b, fb
            b, fb = c, fc
            c, fc = a, fa

        window = _window(b, xtol, rtol)  # the accuracy applied at this iterate
        tol = 0.5 * window               # half-window, compared against half-widths
        half_width = 0.5 * (c - b)       # signed; its magnitude is half the bracket

        if abs(half_width) <= tol:
            return b, _report(True, iteration, abs(fb), b, _ordered(b, c), calls,
                              initial_bracket, xtol, rtol)

        if iteration == max_iter:
            break

        # Halving safeguard, in two tiers.
        #
        # Interpolation can converge on the root from one side while the far
        # endpoint never moves. The estimate improves but the *bracket* does
        # not, and since termination is a statement about the bracket the solve
        # stalls. A root of multiplicity greater than one does this reliably.
        #
        # Tier one asks only that the interval halve every second pass, which
        # costs nothing on well-behaved problems -- measured over the analytic
        # cases in tests/core/test_roots.py it never fires. Once it has fired
        # twice the problem is evidently one of the awkward ones, so tier two
        # demands halving on every pass; that converts a solve that would run
        # out of budget into one that finishes in a little over the bisection
        # count. Both tiers only ever *force bisection*, so neither can affect
        # correctness -- only how many evaluations the answer costs.
        width = 2.0 * abs(half_width)
        if stalls >= _STALL_ESCALATION:
            force_bisection = iteration >= 1 and width > 0.5 * width_previous
        else:
            force_bisection = iteration >= 2 and width > 0.5 * width_two_ago
        if force_bisection:
            stalls += 1
        width_two_ago, width_previous = width_previous, width

        if force_bisection or abs(previous_step) < tol or abs(fa) <= abs(fb):
            # Either the safeguard fired, the last step was already at the
            # noise floor, or the contrapoint is no worse than the current
            # best: interpolation has nothing to offer, so halve the interval.
            step = previous_step = half_width
        else:
            candidate = _interpolate(a, b, c, fa, fb, fc, half_width)
            if candidate is None or not _acceptable(candidate, half_width, tol, previous_step):
                step = previous_step = half_width
            else:
                previous_step = step
                step = candidate

        a, fa = b, fb  # the old best becomes the new contrapoint
        if abs(step) > tol:
            b = b + step
        else:
            # Never take a step smaller than the noise floor, or the iteration
            # can stall without the bracket ever shrinking. |half_width| > tol
            # here, so this stays strictly inside the bracket.
            b = b + (tol if half_width > 0.0 else -tol)
        fb = evaluate(b)

    # Iteration ceiling reached. b is the best estimate available: the
    # invariants above keep |f(b)| <= |f(c)|, and b is an endpoint of the
    # maintained bracket, so it is both the smallest residual of the two
    # candidates and consistent with the interval being reported.
    return b, _report(False, iteration, abs(fb), b, _ordered(b, c), calls,
                      initial_bracket, xtol, rtol)


# ---------------------------------------------------------------------------
# internals
# ---------------------------------------------------------------------------


#: Machine epsilon for the float64 arithmetic the whole package uses.
_EPS: Final = sys.float_info.epsilon


def _window(root: float, xtol: float, rtol: float) -> float:
    """The accuracy window actually applied at ``root``.

    ``xtol + rtol * |root|`` as requested, but never narrower than a few units
    in the last place. No bracketing method can resolve below the spacing of
    the floating-point grid, so a request tighter than that would otherwise
    exhaust the iteration budget and report a failure that is really just an
    impossible demand. Reporting the applied window rather than the requested
    one keeps :attr:`RootReport.tolerance` truthful.
    """
    return max(xtol + rtol * abs(root), 4.0 * _EPS * abs(root))


def _finite_argument(value: float, name: str) -> float:
    """Coerce to float and reject NaN and infinities."""
    number = float(value)  # raises TypeError for anything not numeric
    if not math.isfinite(number):
        raise InputError(f"{name} must be finite, got {number!r}")
    return number


def _straddles(fa: float, fb: float) -> bool:
    """True when two non-zero values have opposite signs.

    Compared by sign rather than by the product ``fa * fb``, which can overflow
    to infinity or underflow to zero when the two magnitudes are extreme and
    would then answer the wrong question. Callers must have excluded exact
    zeros first.
    """
    return (fa > 0.0) != (fb > 0.0)


def _same_sign(x: float, y: float) -> bool:
    """True when two non-zero values share a sign."""
    return (x > 0.0) == (y > 0.0)


def _ordered(x: float, y: float) -> tuple[float, float]:
    """The pair as a low-to-high interval."""
    return (x, y) if x <= y else (y, x)


def _interpolate(
    a: float,
    b: float,
    c: float,
    fa: float,
    fb: float,
    fc: float,
    half_width: float,
) -> float | None:
    """Propose a step from b using interpolation, or None if it is unsafe.

    Uses inverse quadratic interpolation through the three points when they are
    distinct, and the secant rule when only two are. Returns None whenever a
    denominator vanishes or the arithmetic produces a non-finite value, so the
    caller falls back to bisection instead of propagating a NaN.
    """
    if fa == 0.0 or fc == 0.0:
        return None

    ratio = fb / fa
    if not math.isfinite(ratio):
        return None

    if a == c:
        # Only two distinct abscissae: linear (secant) interpolation.
        numerator = 2.0 * half_width * ratio
        denominator = 1.0 - ratio
    else:
        # Three distinct abscissae: inverse quadratic interpolation.
        q = fa / fc
        r = fb / fc
        if not (math.isfinite(q) and math.isfinite(r)):
            return None
        numerator = ratio * (2.0 * half_width * q * (q - r) - (b - a) * (r - 1.0))
        denominator = (q - 1.0) * (r - 1.0) * (ratio - 1.0)

    if not (math.isfinite(numerator) and math.isfinite(denominator)) or denominator == 0.0:
        return None

    # Carry the sign on the denominator so the magnitude test below can work
    # with a non-negative numerator, following the classical formulation.
    if numerator > 0.0:
        denominator = -denominator
    numerator = abs(numerator)

    step = numerator / denominator
    if not math.isfinite(step):
        return None
    return step


def _acceptable(step: float, half_width: float, tol: float, previous_step: float) -> bool:
    """Whether an interpolated step may be taken instead of bisecting.

    Two conditions, both classical and both about protecting the bracket rather
    than about speed:

    * the step must stay comfortably inside the current interval. The bracket
      runs from ``b`` to ``c``, a distance of ``2 * half_width``; the limit of
      ``1.5 * half_width`` (less half the tolerance floor) keeps the new
      iterate at no more than three quarters of the way across, so the sign
      change is never stepped over;
    * it must be no larger than half the step before last, which is what stops
      interpolation from stalling on a badly-behaved function.

    Failing either, the caller bisects -- and it is that fallback, not the
    interpolation, that makes the method robust.
    """
    if not math.isfinite(step) or step == 0.0:
        return False
    if (step > 0.0) != (half_width > 0.0):
        return False  # a step away from the bracketed side is never safe
    inside_bracket = 1.5 * abs(half_width) - 0.5 * tol
    not_stalling = 0.5 * abs(previous_step)
    return abs(step) < min(inside_bracket, not_stalling)


def _report(
    converged: bool,
    iterations: int,
    residual: float,
    root: float,
    bracket: tuple[float, float],
    function_calls: int,
    initial_bracket: tuple[float, float],
    xtol: float,
    rtol: float,
) -> RootReport:
    """Assemble the immutable report."""
    return RootReport(
        converged=converged,
        iterations=iterations,
        residual=residual,
        tolerance=_window(root, xtol, rtol),
        bracket=bracket,
        method=METHOD_BRENT,
        function_calls=function_calls,
        initial_bracket=initial_bracket,
    )
