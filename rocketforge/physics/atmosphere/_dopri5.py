"""A small adaptive Dormand-Prince 5(4) integrator for smooth, short spans.

Used by the upper U.S. Standard Atmosphere to integrate its species equations
between nodes where every coefficient is smooth (the Standard's breakpoints are
nodes). Deterministic: the same call gives the same steps and the same result.
No SciPy at runtime (``01`` section 2).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

__all__ = ["integrate"]

_C = (0.0, 1 / 5, 3 / 10, 4 / 5, 8 / 9, 1.0, 1.0)
_A = (
    (),
    (1 / 5,),
    (3 / 40, 9 / 40),
    (44 / 45, -56 / 15, 32 / 9),
    (19372 / 6561, -25360 / 2187, 64448 / 6561, -212 / 729),
    (9017 / 3168, -355 / 33, 46732 / 5247, 49 / 176, -5103 / 18656),
    (35 / 384, 0.0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84),
)
_B5 = (35 / 384, 0.0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84, 0.0)
_B4 = (5179 / 57600, 0.0, 7571 / 16695, 393 / 640, -92097 / 339200, 187 / 2100, 1 / 40)
_E = tuple(b5 - b4 for b5, b4 in zip(_B5, _B4))


def integrate(f: Callable[[float, list[float]], list[float]], x0: float,
              y0: Sequence[float], x1: float, *, rtol: float = 1e-12,
              atol: float = 1e-12, first_step: float = 0.25,
              max_steps: int = 100000) -> list[float]:
    """y(x1) for y' = f(x, y), y(x0) = y0. Forward or backward.

    Raises RuntimeError when the step size collapses or ``max_steps`` is
    exceeded; the caller has a smooth problem, so either means a defect.
    """
    y = [float(v) for v in y0]
    if x1 == x0:
        return y
    direction = 1.0 if x1 > x0 else -1.0
    span = abs(x1 - x0)
    h = min(first_step, span)
    x = x0
    n = len(y)
    k1 = f(x, y)
    for _ in range(max_steps):
        remaining = abs(x1 - x)
        if remaining <= 1e-15 * max(1.0, abs(x1)):
            return y
        h = min(h, remaining)
        hs = direction * h
        ks = [k1]
        for stage in range(1, 7):
            yi = [y[j] + hs * sum(_A[stage][s] * ks[s][j] for s in range(stage))
                  for j in range(n)]
            ks.append(f(x + _C[stage] * hs, yi))
        y_new = [y[j] + hs * sum(_B5[s] * ks[s][j] for s in range(7)) for j in range(n)]
        err = 0.0
        for j in range(n):
            e = hs * sum(_E[s] * ks[s][j] for s in range(7))
            scale = atol + rtol * max(abs(y[j]), abs(y_new[j]))
            err = max(err, abs(e) / scale)
        if err <= 1.0:
            x = x + hs if h < remaining else x1
            y = y_new
            k1 = ks[6]                              # FSAL
            factor = 5.0 if err == 0.0 else min(5.0, 0.9 * err ** -0.2)
            h = h * factor
        else:
            h = h * max(0.2, 0.9 * err ** -0.25)
            if h < 1e-12 * span:
                raise RuntimeError("step size collapsed in the atmosphere integration")
    raise RuntimeError("too many steps in the atmosphere integration")
