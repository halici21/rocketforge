"""Scalar/array handling shared by the vectorised relations.

``docs/engineering/04_numerical_methods_and_domain_policy.md`` section 9 fixes
the policy: an algebraic relation accepts a scalar or an array and mirrors the
input type, so a notebook user gets a float back and a sweep gets an ndarray.
These helpers make that one decision instead of thirty.

The validation helpers exist because of section 8, "no silent clamping": an
invalid element must raise, naming its index, rather than becoming a NaN that
later shows up as a mysterious hole in a plot.
"""

from __future__ import annotations

import numpy as np

from ..errors import DomainError

__all__ = [
    "as_float_array",
    "restore_scalar",
    "require_finite",
    "require_above",
    "require_at_least",
    "require_at_most",
    "describe_offender",
]


def as_float_array(value: object, name: str) -> tuple[np.ndarray, bool]:
    """Coerce to a float64 array, reporting whether the input was scalar.

    Integer and float32 inputs are promoted to float64: the whole package is
    specified as double precision (ADR-11), and silently preserving a narrower
    dtype would hand back engineering results with seven significant figures
    while every tolerance in the module assumes fifteen.

    Returns:
        ``(array, was_scalar)``. ``was_scalar`` is True for a Python or NumPy
        scalar, so :func:`restore_scalar` can hand back a plain float.
    """
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise DomainError(f"{name} must be a real number or array of them, got {value!r}") from exc
    return array, array.ndim == 0


def restore_scalar(result: np.ndarray, was_scalar: bool) -> float | np.ndarray:
    """Return a float when the input was scalar, otherwise the array."""
    return float(result) if was_scalar else result


def describe_offender(mask: np.ndarray, array: np.ndarray) -> str:
    """Locate the first failing element, for a message that says where.

    Public because the relations sometimes need a domain check of their own --
    a denominator that must not vanish, say -- and their message should point
    at the offending element in exactly the same words as these helpers do.
    """
    if array.ndim == 0:
        return f"got {float(array)!r}"
    index = np.argmax(mask)
    position = np.unravel_index(index, array.shape)
    where = position[0] if array.ndim == 1 else position
    return f"first offending element at index {where}: {float(array[position])!r}"


def require_finite(array: np.ndarray, name: str) -> None:
    """Reject NaN and infinities before any arithmetic sees them."""
    bad = ~np.isfinite(array)
    if bad.any():
        raise DomainError(f"{name} must be finite; {describe_offender(bad, array)}")


def require_above(array: np.ndarray, bound: float, name: str) -> None:
    """Require every element strictly greater than ``bound``."""
    bad = ~(array > bound)
    if bad.any():
        raise DomainError(f"{name} must be > {bound}; {describe_offender(bad, array)}")


def require_at_least(array: np.ndarray, bound: float, name: str) -> None:
    """Require every element greater than or equal to ``bound``."""
    bad = ~(array >= bound)
    if bad.any():
        raise DomainError(f"{name} must be >= {bound}; {describe_offender(bad, array)}")


def require_at_most(array: np.ndarray, bound: float, name: str) -> None:
    """Require every element less than or equal to ``bound``."""
    bad = ~(array <= bound)
    if bad.any():
        raise DomainError(f"{name} must be <= {bound}; {describe_offender(bad, array)}")
