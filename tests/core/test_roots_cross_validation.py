"""Independent cross-validation of the root solver against SciPy.

RocketForge implements its own Brent solver (ADR-09), so the implementation
needs an oracle it did not write. ``scipy.optimize.brentq`` is a long-standing,
independently-developed implementation of the same method and is used here for
exactly that -- and for nothing else:

* SciPy is **not** a runtime dependency. ``tests/test_architecture.py`` fails
  the build if any module under ``rocketforge/`` imports it.
* There is **no** fallback path. If our solver fails, the test fails; it does
  not quietly defer to SciPy.
* If SciPy is not installed these tests skip, and the correctness of the solver
  is still covered in full by ``test_roots.py``, which depends on nothing.

Cases come from deterministic parameter grids -- no randomness, seeded or
otherwise -- so any failure is reproducible from its identifier alone. Every
case has an analytically known simple root inside a sign-changing bracket, so
"which root" is never ambiguous.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import pytest

from rocketforge.core.numerics.roots import brent

scipy_optimize = pytest.importorskip(
    "scipy.optimize",
    reason="SciPy is a development-only cross-validation oracle; see requirements-dev.txt",
)

XTOL = 1e-12
RTOL = 1e-14
MAX_ITER = 200


@dataclass(frozen=True)
class Case:
    """One generated cross-validation problem with a known analytic root."""

    identifier: str
    f: Callable[[float], float]
    a: float
    b: float
    root: float


# Deterministic grids. Chosen to span sign, magnitude and scale rather than to
# be numerous for its own sake.
ROOTS = (
    -1234.5, -500.0, -12.25, -1.0, -0.5, -0.03125, 0.0,
    0.015625, 0.75, 3.0, 4.5, 31.0, 97.0, 2048.0,
)
PARAMS = (1e-6, 0.125, 1.0, 8.0, 1e6)
BRACKET_SHAPES = (
    (-1.0, 1.0),      # symmetric
    (-0.125, 3.5),    # root near the low end
    (-6.0, 0.25),     # root near the high end
)


def _build(family: str, root: float, param: float, lo: float, hi: float) -> Case | None:
    """Construct one case, or None when the combination is not admissible."""
    span_lo, span_hi = lo, hi
    effective = param  # the parameter the function really uses, after clamping

    if family == "linear":
        f = lambda x: param * (x - root)  # noqa: E731
    elif family == "cubic_plus_linear":
        # Simple root: the derivative at the root is param, never zero.
        f = lambda x: param * ((x - root) ** 3 + (x - root))  # noqa: E731
    elif family == "exponential_offset":
        k = min(param, 8.0)  # keep the exponent far from overflow
        # expm1, not exp(...) - 1.0: the naive difference cancels away every
        # significant digit near the root for small k, leaving a function that
        # cannot locate its own zero. That would be a defect in the test
        # problem, not in the solver, and it is the same reasoning as the
        # conditioning checklist in 04 section 11.
        f = lambda x: math.expm1(k * (x - root))  # noqa: E731
        effective = k
    elif family == "arctangent":
        f = lambda x: param * math.atan(x - root)  # noqa: E731
    elif family == "hyperbolic_tangent":
        k = min(param, 8.0)
        f = lambda x: math.tanh(k * (x - root))  # noqa: E731
        effective = k
    elif family == "trigonometric":
        # Monotone on the bracket only if it stays inside a half period.
        span_lo, span_hi = max(lo, -1.4), min(hi, 1.4)
        if span_hi - span_lo < 0.2:
            return None
        f = lambda x: param * math.sin(x - root)  # noqa: E731
    elif family == "logarithmic":
        # Needs a strictly positive root and a strictly positive bracket.
        if root <= 0.0:
            return None
        f = lambda x: param * math.log(x / root)  # noqa: E731
        span_lo, span_hi = -0.6 * root, 1.5 * root
    elif family == "rational":
        # Monotone within |x - root| < 1, so clamp the bracket to that.
        span_lo, span_hi = max(lo, -0.9), min(hi, 0.9)
        if span_hi - span_lo < 0.2:
            return None
        f = lambda x: param * (x - root) / (1.0 + (x - root) ** 2)  # noqa: E731
    else:  # pragma: no cover - guards a typo in the family list
        raise AssertionError(f"unknown family {family}")

    a = root + span_lo
    b = root + span_hi
    if not (a < root < b):
        return None

    try:
        fa, fb = f(a), f(b)
    except (ValueError, OverflowError):
        return None
    if not (math.isfinite(fa) and math.isfinite(fb)):
        return None
    if fa == 0.0 or fb == 0.0 or (fa > 0.0) == (fb > 0.0):
        return None

    # Built from the effective problem, not the requested one: two grid points
    # that clamp to the same function and bracket are one case, not two.
    identifier = f"{family}|root={root!r}|param={effective!r}|bracket=({a!r},{b!r})"
    return Case(identifier, f, a, b, root)


FAMILIES = (
    "linear",
    "cubic_plus_linear",
    "exponential_offset",
    "arctangent",
    "hyperbolic_tangent",
    "trigonometric",
    "logarithmic",
    "rational",
)


def build_cases() -> list[Case]:
    """Every admissible, distinct case from the deterministic grid."""
    seen: dict[str, Case] = {}
    for family in FAMILIES:
        for root in ROOTS:
            for param in PARAMS:
                for lo, hi in BRACKET_SHAPES:
                    case = _build(family, root, param, lo, hi)
                    if case is not None:
                        seen.setdefault(case.identifier, case)
    return sorted(seen.values(), key=lambda c: c.identifier)


CASES = build_cases()


def test_case_generation_is_large_enough():
    """The cross-validation set must be substantial, and every case admissible."""
    assert len(CASES) >= 1000, f"only {len(CASES)} valid cases generated"
    identifiers = {c.identifier for c in CASES}
    assert len(identifiers) == len(CASES), "case identifiers are not unique"
    for case in CASES:
        assert case.a < case.root < case.b
        assert (case.f(case.a) > 0.0) != (case.f(case.b) > 0.0)


def test_agrees_with_scipy_over_the_whole_grid():
    """Root, convergence and residual must agree on every generated case."""
    disagreements: list[str] = []
    worst_gap = 0.0
    worst_case = ""

    for case in CASES:
        ours, report = brent(case.f, case.a, case.b, xtol=XTOL, rtol=RTOL, max_iter=MAX_ITER)
        theirs, info = scipy_optimize.brentq(
            case.f, case.a, case.b, xtol=XTOL, rtol=RTOL, maxiter=MAX_ITER, full_output=True
        )

        # Both are solving to the same accuracy, so the two answers may differ
        # by up to the sum of their windows. A generous multiple of that is
        # still far tighter than any engineering requirement, and catches a
        # genuine algorithmic disagreement rather than last-bit noise.
        allowed = 4.0 * (XTOL + RTOL * abs(case.root))
        gap = abs(ours - theirs)
        if gap > worst_gap:
            worst_gap, worst_case = gap, case.identifier

        problems = []
        if not report.converged:
            problems.append("RocketForge did not converge")
        if not info.converged:
            problems.append("SciPy did not converge")
        if gap > allowed:
            problems.append(f"roots differ by {gap:.3e} > {allowed:.3e}")
        if abs(ours - case.root) > allowed:
            problems.append(f"RocketForge is {abs(ours - case.root):.3e} from the analytic root")
        if abs(theirs - case.root) > allowed:
            problems.append(f"SciPy is {abs(theirs - case.root):.3e} from the analytic root")

        if problems:
            disagreements.append(
                f"\n  case      : {case.identifier}"
                f"\n  bracket   : [{case.a!r}, {case.b!r}]"
                f"\n  analytic  : {case.root!r}"
                f"\n  RocketForge: {ours!r}  (iterations {report.iterations},"
                f" calls {report.function_calls}, residual {report.residual:.3e})"
                f"\n  SciPy      : {theirs!r}  (iterations {info.iterations},"
                f" calls {info.function_calls})"
                f"\n  problems  : " + "; ".join(problems)
            )

    assert not disagreements, (
        f"{len(disagreements)} of {len(CASES)} cases disagree:" + "".join(disagreements[:10])
    )
    # Recorded so a future regression in agreement is visible, not silent.
    assert worst_gap < 1e-6, f"worst gap {worst_gap:.3e} on {worst_case}"


def test_effort_is_comparable_to_scipy():
    """Not a race, but a wild difference would mean a defective step rule."""
    ours_total = 0
    theirs_total = 0
    for case in CASES:
        _, report = brent(case.f, case.a, case.b, xtol=XTOL, rtol=RTOL, max_iter=MAX_ITER)
        _, info = scipy_optimize.brentq(
            case.f, case.a, case.b, xtol=XTOL, rtol=RTOL, maxiter=MAX_ITER, full_output=True
        )
        ours_total += report.function_calls
        theirs_total += info.function_calls

    ratio = ours_total / theirs_total
    assert 0.5 <= ratio <= 2.0, (
        f"function-call ratio {ratio:.2f} (ours {ours_total}, SciPy {theirs_total}) "
        "suggests the step or acceptance rule differs materially"
    )


def test_scipy_agrees_on_an_endpoint_root():
    """The endpoint shortcut must not change the answer, only the effort."""
    f = lambda x: x - 2.0  # noqa: E731
    ours, report = brent(f, 2.0, 5.0, xtol=XTOL, rtol=RTOL, max_iter=MAX_ITER)
    theirs = scipy_optimize.brentq(f, 2.0, 5.0, xtol=XTOL, rtol=RTOL, maxiter=MAX_ITER)
    assert ours == theirs == 2.0
    assert report.function_calls == 1
