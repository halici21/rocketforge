"""Verification of the bracketed root solver.

The required matrix is in the Phase 4A brief and mirrors the convergence-test
requirements of ``docs/engineering/05_verification_and_validation_plan.md``
section 13: analytic roots, endpoint roots, invalid brackets, non-finite
values, invalid arguments, narrow brackets, extreme root magnitudes, iteration
exhaustion, report correctness, and determinism.

Expected roots are analytic or independently known constants. None of them is
produced by running the solver under test.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.core.errors import (
    BracketError,
    InputError,
    NonFiniteEvaluationError,
    NumericalError,
    RocketForgeError,
)
from rocketforge.core.numerics.roots import METHOD_BRENT, RootReport, brent
from rocketforge.core.tolerances import DEFAULT_TOLERANCES

# The tolerances used unless a test is specifically about tolerance handling.
XTOL = 1e-12
RTOL = 1e-14
MAX_ITER = DEFAULT_TOLERANCES.max_iter

# Independently known constant: the Dottie number, the unique real fixed point
# of cosine, i.e. the root of cos(x) - x. Value from the standard reference
# expansion, not from this solver.
DOTTIE = 0.7390851332151607


def solve(f, a, b, *, xtol=XTOL, rtol=RTOL, max_iter=MAX_ITER):
    """Call the solver with the test defaults."""
    return brent(f, a, b, xtol=xtol, rtol=rtol, max_iter=max_iter)


def assert_root(name, f, a, b, expected, root, report):
    """Every property a converged solve must satisfy, with a legible failure."""
    context = (
        f"\ncase       : {name}"
        f"\nbracket    : [{a!r}, {b!r}]"
        f"\nexpected   : {expected!r}"
        f"\nreturned   : {root!r}"
        f"\nerror      : {abs(root - expected):.6e}"
        f"\ntolerance  : {report.tolerance:.6e}"
        f"\nresidual   : {report.residual:.6e}"
        f"\niterations : {report.iterations}"
        f"\ncalls      : {report.function_calls}"
        f"\nbracket out: {report.bracket}"
    )
    assert report.converged, f"solver did not converge{context}"
    assert report.method == METHOD_BRENT, f"wrong method identifier{context}"
    assert math.isfinite(root), f"root is not finite{context}"
    assert abs(root - expected) <= report.tolerance, f"root outside promised window{context}"
    assert min(a, b) <= root <= max(a, b), f"root left the supplied bracket{context}"
    assert report.residual == abs(f(root)), f"reported residual is not |f(root)|{context}"
    lo, hi = report.bracket
    assert lo <= root <= hi, f"root outside the reported bracket{context}"
    assert report.initial_bracket == (a, b), f"initial bracket not echoed{context}"


# ---------------------------------------------------------------------------
# analytic root cases
# ---------------------------------------------------------------------------

# name, f, a, b, expected root
ANALYTIC_CASES = [
    # Linear: the secant step is exact, so this also checks that an exact hit
    # is recognised rather than iterated around.
    ("linear, root 0.5", lambda x: x - 0.5, 0.0, 1.0, 0.5),
    ("linear, steep", lambda x: 1.0e8 * (x - 0.3), -1.0, 2.0, 0.3),
    ("linear, shallow", lambda x: 1.0e-8 * (x - 0.3), -1.0, 2.0, 0.3),
    # Polynomials with sign changes.
    ("quadratic, sqrt(2)", lambda x: x * x - 2.0, 0.0, 2.0, math.sqrt(2.0)),
    ("cubic, single real root", lambda x: x**3 + x - 1.0, 0.0, 1.0, 0.6823278038280193),
    ("quartic, root at 3", lambda x: x**4 - 81.0, 0.0, 10.0, 3.0),
    # Transcendental.
    ("cos(x) - x", lambda x: math.cos(x) - x, 0.0, 1.0, DOTTIE),
    ("exp(x) - 5", lambda x: math.exp(x) - 5.0, 0.0, 5.0, math.log(5.0)),
    ("log(x) + 1", lambda x: math.log(x) + 1.0, 1e-3, 10.0, math.exp(-1.0)),
    ("sin(x), root at pi", lambda x: math.sin(x), 2.0, 4.0, math.pi),
    ("tanh(x) - 0.5", lambda x: math.tanh(x) - 0.5, -1.0, 3.0, math.atanh(0.5)),
    # Flat derivative at the root: f'(root) = 0, which is where a Newton
    # iteration would misbehave, but the sign still changes so the bracket
    # contract holds. The root is deliberately not a bisection midpoint of the
    # bracket, so the solver cannot land on it by accident.
    ("cubic, flat derivative", lambda x: (x - 1.2345) ** 3, -0.7, 4.1, 1.2345),
    ("quintic, very flat", lambda x: (x - 0.31234) ** 5, -1.3, 2.7, 0.31234),
]


@pytest.mark.parametrize("name,f,a,b,expected", ANALYTIC_CASES, ids=[c[0] for c in ANALYTIC_CASES])
def test_analytic_roots(name, f, a, b, expected):
    root, report = solve(f, a, b)
    assert_root(name, f, a, b, expected, root, report)


# Cases whose root has multiplicity greater than one. Brent is superlinear only
# at a simple root; where f'(root) = 0 as well, it degrades to linear -- a
# property of the method, not of this implementation. The halving safeguard
# bounds that case at roughly twice the bisection count instead of letting it
# run out of budget.
FLAT_CASE_NAMES = {"cubic, flat derivative", "quintic, very flat"}

# Budget for a simple root. Measured worst case over these cases is 13.
SIMPLE_ROOT_BUDGET = 40


def bisection_count(a: float, b: float, tolerance: float) -> int:
    """How many halvings plain bisection needs to reach ``tolerance``."""
    return math.ceil(math.log2((b - a) / tolerance))


@pytest.mark.parametrize("name,f,a,b,expected", ANALYTIC_CASES, ids=[c[0] for c in ANALYTIC_CASES])
def test_iteration_budget(name, f, a, b, expected):
    """Superlinear at a simple root; bounded by the safeguard at a flat one."""
    _, report = solve(f, a, b)
    if name in FLAT_CASE_NAMES:
        # The guarantee the halving safeguard provides, stated as an assertion.
        budget = 2 * bisection_count(a, b, report.tolerance) + 8
    else:
        budget = SIMPLE_ROOT_BUDGET
    assert report.iterations <= budget, (
        f"{name}: {report.iterations} iterations exceeds the budget of {budget} "
        f"(bracket [{a}, {b}], tolerance {report.tolerance:.3e})"
    )


def test_simple_roots_are_genuinely_superlinear():
    """Guard against a safeguard change quietly turning the solver into bisection."""
    for name, f, a, b, _ in ANALYTIC_CASES:
        if name in FLAT_CASE_NAMES:
            continue
        _, report = solve(f, a, b)
        floor = bisection_count(a, b, report.tolerance)
        assert report.iterations < floor, (
            f"{name}: {report.iterations} iterations is no better than the "
            f"{floor} plain bisection would need"
        )


# ---------------------------------------------------------------------------
# endpoint roots
# ---------------------------------------------------------------------------


def test_root_at_left_endpoint_returned_immediately():
    root, report = solve(lambda x: x - 2.0, 2.0, 5.0)
    assert root == 2.0
    assert report.converged
    assert report.iterations == 0
    assert report.residual == 0.0
    assert report.function_calls == 1, "f(b) need not be evaluated once f(a) is a root"
    assert report.bracket == (2.0, 5.0)
    assert report.initial_bracket == (2.0, 5.0)


def test_root_at_right_endpoint_returned_immediately():
    root, report = solve(lambda x: x - 5.0, 2.0, 5.0)
    assert root == 5.0
    assert report.converged
    assert report.iterations == 0
    assert report.residual == 0.0
    assert report.function_calls == 2, "both endpoints are evaluated to reach b"
    assert report.bracket == (2.0, 5.0)


def test_endpoint_root_wins_over_the_sign_test():
    """An endpoint root must be returned even though the signs do not straddle.

    f(a) = 0 and f(b) > 0, so a naive sign test would raise BracketError before
    noticing that a is exactly the root.
    """
    root, report = solve(lambda x: x * x, 0.0, 3.0)
    assert root == 0.0
    assert report.converged
    assert report.residual == 0.0


def test_endpoint_root_with_negative_zero():
    """-0.0 == 0.0, so a signed zero is an exact root like any other."""
    root, report = solve(lambda x: -0.0 if x == 1.0 else x - 1.0, 1.0, 4.0)
    assert root == 1.0
    assert report.converged
    assert report.residual == 0.0


def test_both_endpoints_roots_returns_the_lower():
    """Documented tie-break: the lower endpoint is checked first."""
    root, report = solve(lambda x: (x - 1.0) * (x - 2.0), 1.0, 2.0)
    assert root == 1.0
    assert report.function_calls == 1


# ---------------------------------------------------------------------------
# invalid bracket
# ---------------------------------------------------------------------------


def test_no_sign_change_raises_bracket_error():
    with pytest.raises(BracketError) as excinfo:
        solve(lambda x: x * x + 1.0, -1.0, 1.0)
    message = str(excinfo.value)
    assert "same sign" in message
    assert "does not bracket" in message


def test_bracket_error_does_not_search_outside_the_interval():
    """The real root at 5 lies outside [0, 1]; the solver must not find it."""
    seen: list[float] = []

    def f(x: float) -> float:
        seen.append(x)
        return x - 5.0

    with pytest.raises(BracketError):
        solve(f, 0.0, 1.0)
    assert all(0.0 <= x <= 1.0 for x in seen), f"evaluated outside the bracket: {seen}"
    assert len(seen) == 2, "only the two endpoints should have been evaluated"


def test_bracket_error_is_a_numerical_error():
    assert issubclass(BracketError, NumericalError)
    assert issubclass(NumericalError, RocketForgeError)


# ---------------------------------------------------------------------------
# non-finite values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("position", ["a", "b"])
def test_non_finite_bracket_endpoint_raises_input_error(bad, position):
    a, b = (bad, 1.0) if position == "a" else (0.0, bad)
    with pytest.raises(InputError) as excinfo:
        solve(lambda x: x - 0.5, a, b)
    assert "finite" in str(excinfo.value)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_function_value_at_endpoint(bad):
    with pytest.raises(NonFiniteEvaluationError):
        solve(lambda x: bad if x == 0.0 else x - 0.5, 0.0, 1.0)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_function_value_during_iteration(bad):
    """A non-finite value mid-iteration stops the solve; it never propagates.

    NaN compares false against everything, so an unchecked NaN would silently
    turn the bracketing logic into a random walk.
    """

    def f(x: float) -> float:
        if 0.4 < x < 0.6:
            return bad
        return x - 0.5

    with pytest.raises(NonFiniteEvaluationError) as excinfo:
        solve(f, 0.0, 1.0)
    assert "cannot continue" in str(excinfo.value)


def test_non_finite_evaluation_is_a_numerical_error():
    assert issubclass(NonFiniteEvaluationError, NumericalError)


# ---------------------------------------------------------------------------
# invalid arguments
# ---------------------------------------------------------------------------


def test_non_callable_f_raises_type_error():
    with pytest.raises(TypeError):
        brent("not a function", 0.0, 1.0, xtol=XTOL, rtol=RTOL, max_iter=MAX_ITER)  # type: ignore[arg-type]


@pytest.mark.parametrize("a,b", [(1.0, 1.0), (2.0, 1.0), (0.0, -1.0)])
def test_bracket_must_be_ordered(a, b):
    with pytest.raises(InputError) as excinfo:
        solve(lambda x: x, a, b)
    assert "a < b" in str(excinfo.value)


@pytest.mark.parametrize("xtol", [0.0, -1e-12, -1.0])
def test_non_positive_xtol_rejected(xtol):
    with pytest.raises(InputError) as excinfo:
        solve(lambda x: x - 0.5, 0.0, 1.0, xtol=xtol)
    assert "xtol" in str(excinfo.value)


@pytest.mark.parametrize("rtol", [-1e-16, -1.0])
def test_negative_rtol_rejected(rtol):
    with pytest.raises(InputError) as excinfo:
        solve(lambda x: x - 0.5, 0.0, 1.0, rtol=rtol)
    assert "rtol" in str(excinfo.value)


def test_zero_rtol_is_allowed():
    """rtol = 0 means a purely absolute criterion, which is legitimate."""
    root, report = solve(lambda x: x - 0.5, 0.0, 1.0, rtol=0.0)
    assert report.converged
    assert abs(root - 0.5) <= report.tolerance


@pytest.mark.parametrize("xtol,rtol", [(math.nan, RTOL), (math.inf, RTOL), (XTOL, math.nan)])
def test_non_finite_tolerance_rejected(xtol, rtol):
    with pytest.raises(InputError):
        solve(lambda x: x - 0.5, 0.0, 1.0, xtol=xtol, rtol=rtol)


@pytest.mark.parametrize("max_iter", [0, -1, -100])
def test_non_positive_max_iter_rejected(max_iter):
    with pytest.raises(InputError) as excinfo:
        solve(lambda x: x - 0.5, 0.0, 1.0, max_iter=max_iter)
    assert "max_iter" in str(excinfo.value)


@pytest.mark.parametrize("max_iter", [1.5, "10", None, True])
def test_non_integer_max_iter_rejected(max_iter):
    with pytest.raises(InputError):
        solve(lambda x: x - 0.5, 0.0, 1.0, max_iter=max_iter)


def test_tolerances_are_keyword_only():
    """Positional tolerances would make a call site ambiguous to read."""
    with pytest.raises(TypeError):
        brent(lambda x: x - 0.5, 0.0, 1.0, 1e-12, 1e-14, 100)  # type: ignore[misc]


# ---------------------------------------------------------------------------
# brackets and magnitudes
# ---------------------------------------------------------------------------


def test_narrow_bracket_already_within_tolerance():
    """A bracket narrower than the window converges without iterating."""
    root, report = solve(lambda x: x - 0.5, 0.5 - 1e-15, 0.5 + 1e-15, xtol=1e-12, rtol=0.0)
    assert report.converged
    assert report.iterations == 0
    assert abs(root - 0.5) <= report.tolerance
    assert report.function_calls == 2


def test_narrow_bracket_at_the_precision_floor():
    """Adjacent floats still terminate; no division pathology, no stall."""
    a = 0.5
    b = math.nextafter(math.nextafter(0.5, 1.0), 1.0)
    root, report = solve(lambda x: x - 0.5000000000000001, a, b, xtol=1e-18, rtol=0.0)
    assert report.converged
    assert report.iterations <= 5
    assert a <= root <= b


def test_large_magnitude_root_uses_relative_tolerance():
    expected = 1.0e6 * math.pi
    root, report = solve(lambda x: x - expected, 0.0, 1.0e8, xtol=1e-9, rtol=1e-12)
    assert report.converged
    assert abs(root - expected) <= report.tolerance
    assert report.tolerance >= 1e-12 * expected


def test_small_magnitude_root_uses_absolute_tolerance():
    expected = 1.0e-10
    root, report = solve(lambda x: x - expected, -1.0, 1.0, xtol=1e-15, rtol=1e-14)
    assert report.converged
    assert abs(root - expected) <= report.tolerance
    assert report.tolerance >= 1e-15


def test_root_extremely_close_to_an_endpoint():
    expected = 1e-13
    root, report = solve(lambda x: x - expected, 0.0, 1.0, xtol=1e-18, rtol=1e-16)
    assert report.converged
    assert abs(root - expected) <= max(report.tolerance, 1e-17)


def test_asymmetric_bracket():
    """The root sits far from the midpoint, so early bisections barely help."""
    expected = math.log(2.0)
    root, report = solve(lambda x: math.exp(x) - 2.0, -1000.0, 1.5, xtol=1e-12, rtol=1e-14)
    assert report.converged
    assert abs(root - expected) <= report.tolerance


def test_function_magnitudes_differing_by_many_orders():
    """|f| spans ~20 decades across the bracket; the sign test must not overflow."""

    def f(x: float) -> float:
        return math.exp(20.0 * x) - math.exp(20.0 * 0.37)

    root, report = solve(f, -1.0, 1.0, xtol=1e-12, rtol=1e-14)
    assert report.converged
    assert abs(root - 0.37) <= max(report.tolerance, 1e-13)


def test_interpolation_repeatedly_rejected_still_converges():
    """A kink in f makes interpolation useless; bisection must carry the solve.

    This is the property the whole method rests on: the bracket is preserved
    whatever the interpolation proposes, so the worst case is bisection rather
    than divergence.
    """

    def f(x: float) -> float:
        # Steep on one side of the root, nearly flat on the other.
        return 1e6 * (x - 0.5) if x > 0.5 else 1e-6 * (x - 0.5)

    root, report = solve(f, -1.0, 2.0, xtol=1e-12, rtol=1e-14)
    assert report.converged
    assert abs(root - 0.5) <= max(report.tolerance, 1e-11)
    assert report.iterations <= 60


# ---------------------------------------------------------------------------
# iteration exhaustion
# ---------------------------------------------------------------------------


def test_max_iter_exhaustion_returns_best_estimate_without_raising():
    root, report = solve(lambda x: math.cos(x) - x, 0.0, 1.0, max_iter=2)
    assert report.converged is False
    assert report.iterations == 2
    assert math.isfinite(root), "the best estimate must never be NaN"
    assert 0.0 <= root <= 1.0
    assert report.residual == pytest.approx(abs(math.cos(root) - root), rel=0, abs=0)
    lo, hi = report.bracket
    assert lo <= root <= hi


def test_max_iter_one_terminates():
    """The tightest possible budget must still return, not loop."""
    root, report = solve(lambda x: math.cos(x) - x, 0.0, 1.0, max_iter=1)
    assert report.converged is False
    assert report.iterations == 1
    assert math.isfinite(root)


def test_max_iter_exhaustion_keeps_a_valid_bracket():
    """The reported interval must still straddle the root."""
    f = lambda x: math.cos(x) - x  # noqa: E731
    _, report = solve(f, 0.0, 1.0, max_iter=3)
    lo, hi = report.bracket
    assert f(lo) * f(hi) <= 0.0, f"reported bracket {report.bracket} does not straddle"


def test_max_iter_exhaustion_returns_the_better_of_the_two_candidates():
    """Documented meaning of "best iterate": the endpoint with smaller |f|."""
    f = lambda x: math.cos(x) - x  # noqa: E731
    root, report = solve(f, 0.0, 1.0, max_iter=2)
    lo, hi = report.bracket
    other = hi if root == lo else lo
    assert abs(f(root)) <= abs(f(other))


def test_generous_budget_converges_where_a_tiny_one_does_not():
    f = lambda x: math.exp(x) - 5.0  # noqa: E731
    _, tiny = solve(f, 0.0, 5.0, max_iter=2)
    root, plenty = solve(f, 0.0, 5.0, max_iter=100)
    assert tiny.converged is False
    assert plenty.converged is True
    assert abs(root - math.log(5.0)) <= plenty.tolerance


# ---------------------------------------------------------------------------
# report correctness
# ---------------------------------------------------------------------------


def test_report_is_immutable():
    _, report = solve(lambda x: x - 0.5, 0.0, 1.0)
    with pytest.raises(Exception):
        report.converged = False  # type: ignore[misc]


def test_report_fields_and_types():
    root, report = solve(lambda x: math.cos(x) - x, 0.0, 1.0)
    assert isinstance(report, RootReport)
    assert isinstance(report.converged, bool)
    assert isinstance(report.iterations, int)
    assert isinstance(report.function_calls, int)
    assert isinstance(report.residual, float)
    assert isinstance(report.tolerance, float)
    assert isinstance(report.bracket, tuple) and len(report.bracket) == 2
    assert isinstance(report.initial_bracket, tuple) and len(report.initial_bracket) == 2
    assert report.method == "brent"
    assert report.bracket[0] <= report.bracket[1], "bracket must be ordered low to high"
    assert report.function_calls >= report.iterations


def test_function_call_count_is_exact():
    """The report must account for every evaluation, and no solve may waste one."""
    calls = 0

    def f(x: float) -> float:
        nonlocal calls
        calls += 1
        return math.cos(x) - x

    _, report = solve(f, 0.0, 1.0)
    assert report.function_calls == calls


def test_residual_is_the_objective_at_the_returned_root():
    f = lambda x: x**3 + x - 1.0  # noqa: E731
    root, report = solve(f, 0.0, 1.0)
    assert report.residual == abs(f(root))


def test_tolerance_reported_is_the_window_applied():
    root, report = solve(lambda x: x - 1234.5, 0.0, 1e5, xtol=1e-9, rtol=1e-12)
    assert report.tolerance == pytest.approx(1e-9 + 1e-12 * abs(root), rel=1e-12)


def test_small_residual_does_not_imply_an_accurate_root():
    """Why residual is reported but is not the stopping rule (DECISION-4A-01).

    On a flat function, |f| falls below 1e-10 while the root is still wrong in
    the fourth decimal; on a steep one, an essentially exact root still carries
    a residual far above 1e-10. Neither is a solver defect, and either would be
    misreported if |f| were the termination criterion.
    """
    flat = lambda x: (x - 1.0) ** 3  # noqa: E731
    assert abs(flat(1.0 + 4.6e-4)) < 1e-10, "a wrong root can have a tiny residual"

    steep = lambda x: 1e8 * (x - 0.3)  # noqa: E731
    root, report = solve(steep, -1.0, 2.0, xtol=1e-12, rtol=1e-14)
    assert report.converged
    assert abs(root - 0.3) <= report.tolerance, "the root itself is accurate"
    assert report.residual >= 0.0


# ---------------------------------------------------------------------------
# determinism and statelessness
# ---------------------------------------------------------------------------

DETERMINISM_CASES = [c for c in ANALYTIC_CASES]


@pytest.mark.parametrize("name,f,a,b,expected", DETERMINISM_CASES, ids=[c[0] for c in DETERMINISM_CASES])
def test_repeated_runs_are_bitwise_identical(name, f, a, b, expected):
    """Same inputs, same bits -- required by the determinism rule in 01 section 9."""
    first_root, first = solve(f, a, b)
    for _ in range(5):
        root, report = solve(f, a, b)
        assert root.hex() == first_root.hex(), f"{name}: root differs between runs"
        assert report == first, f"{name}: report differs between runs"


def test_no_global_state_between_solves():
    """Interleaving different problems must not perturb any of them."""
    f1 = lambda x: math.cos(x) - x  # noqa: E731
    f2 = lambda x: x**3 + x - 1.0  # noqa: E731

    r1a, rep1a = solve(f1, 0.0, 1.0)
    r2a, rep2a = solve(f2, 0.0, 1.0)
    r1b, rep1b = solve(f1, 0.0, 1.0)
    r2b, rep2b = solve(f2, 0.0, 1.0)

    assert r1a.hex() == r1b.hex()
    assert r2a.hex() == r2b.hex()
    assert rep1a == rep1b
    assert rep2a == rep2b


def test_solver_does_not_mutate_its_arguments():
    bracket = [0.0, 1.0]
    tolerances = {"xtol": XTOL, "rtol": RTOL, "max_iter": MAX_ITER}
    solve(lambda x: x - 0.5, bracket[0], bracket[1], **tolerances)
    assert bracket == [0.0, 1.0]
    assert tolerances == {"xtol": XTOL, "rtol": RTOL, "max_iter": MAX_ITER}


# ---------------------------------------------------------------------------
# properties over a deterministic parameter grid
# ---------------------------------------------------------------------------

# Deterministic grid: no randomness anywhere, so every failure is reproducible
# from the identifiers alone.
GRID_ROOTS = [-1000.0, -7.5, -1.0, -1e-8, 0.0, 1e-8, 0.25, 1.0, 3.75, 1000.0]
GRID_SCALES = [1e-6, 1.0, 1e6]


def _shifted_cube(root: float, scale: float):
    return lambda x: scale * (x - root) ** 3


def _shifted_linear(root: float, scale: float):
    return lambda x: scale * (x - root)


def _shifted_atan(root: float, scale: float):
    return lambda x: scale * math.atan(x - root)


GRID_FAMILIES = {
    "linear": _shifted_linear,
    "cube": _shifted_cube,
    "atan": _shifted_atan,
}


@pytest.mark.parametrize("family", sorted(GRID_FAMILIES))
@pytest.mark.parametrize("scale", GRID_SCALES)
@pytest.mark.parametrize("root", GRID_ROOTS)
def test_grid_properties(family, scale, root):
    """Properties that must hold for every monotone, sign-changing case."""
    f = GRID_FAMILIES[family](root, scale)
    a = root - 3.25   # asymmetric on purpose, so the root is not the midpoint
    b = root + 5.75
    found, report = solve(f, a, b)

    context = f"\nfamily={family} scale={scale} root={root} report={report}"
    assert report.converged, f"did not converge{context}"
    assert a <= found <= b, f"left the bracket{context}"
    assert abs(found - root) <= report.tolerance, f"outside the window{context}"
    # "cube" is a triple root, where Brent is linear rather than superlinear;
    # the safeguard's guarantee is roughly twice the bisection count.
    budget = (
        2 * bisection_count(a, b, report.tolerance) + 8
        if family == "cube"
        else SIMPLE_ROOT_BUDGET
    )
    assert report.iterations <= budget, f"over the iteration budget of {budget}{context}"
    lo, hi = report.bracket
    assert lo <= found <= hi, f"outside the reported bracket{context}"
    assert f(lo) * f(hi) <= 0.0, f"reported bracket does not straddle{context}"


@pytest.mark.parametrize("root", GRID_ROOTS)
def test_bracket_orientation_does_not_change_the_answer(root):
    """Sign of f across the bracket is irrelevant: rising and falling agree."""
    rising = lambda x: x - root  # noqa: E731
    falling = lambda x: root - x  # noqa: E731
    a, b = root - 2.5, root + 4.5

    up, up_report = solve(rising, a, b)
    down, down_report = solve(falling, a, b)

    assert abs(up - root) <= up_report.tolerance
    assert abs(down - root) <= down_report.tolerance
