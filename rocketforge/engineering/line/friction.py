"""The turbulent friction factor: Colebrook-White, solved with a bracket.

    1/sqrt(f_D) = -2 log10( epsilon/(3.7 D) + 2.51 / (Re sqrt(f_D)) )

Colebrook, *Turbulent flow in pipes, with particular reference to the
transition region between the smooth and rough pipe laws*, J. Inst. Civ. Eng.
**11** (1939) 133; the domain is the turbulent zone of the Moody chart, Moody,
*Friction factors for pipe flow*, Trans. ASME **66** (1944) 671.

**Darcy, not Fanning.** ``f_D = 4 f_F``. Every factor in this module is Darcy,
and Darcy-Weisbach requires Darcy; substituting Fanning underpredicts a
pressure drop by exactly four.

**Solved, never approximated.** Haaland, Swamee-Jain and Blasius are explicit
approximations *to* this equation. They are legitimate as test comparisons and
are not the production path, because an approximation silently substituted for
the model a result claims to use is a different model wearing its name.
"""

from __future__ import annotations

import math

from rocketforge.core.errors import InputError
from rocketforge.core.numerics.roots import RootReport, brent

from .types import (
    COLEBROOK_REYNOLDS_MAX,
    MAX_RELATIVE_ROUGHNESS,
    REYNOLDS_TURBULENT_ONSET,
)

__all__ = [
    "colebrook_residual",
    "colebrook_darcy_friction_factor",
    "COLEBROOK_BRACKET",
    "COLEBROOK_XTOL",
    "COLEBROOK_RTOL",
    "COLEBROOK_MAX_ITER",
]

#: The solve is posed in ``x = 1/sqrt(f_D)`` rather than in ``f_D``.
#:
#: In that variable the residual is
#: ``g(x) = x + 2 log10(A + B x)`` with ``A = epsilon/(3.7 D) >= 0`` and
#: ``B = 2.51/Re > 0``, whose derivative ``1 + (2/ln10) B/(A + B x)`` is
#: strictly positive. So ``g`` is monotonically increasing and has exactly one
#: root, which is what makes a fixed bracket safe rather than lucky.
#:
#: The bracket spans ``f_D`` from 1.0 down to about 1.1e-3, which contains the
#: whole Moody turbulent zone (roughly 0.008 to 0.075) with a wide margin on
#: both sides. A test sweeps the declared domain and asserts the sign change.
COLEBROOK_BRACKET = (1.0, 30.0)

COLEBROOK_XTOL = 1.0e-13
COLEBROOK_RTOL = 1.0e-14
COLEBROOK_MAX_ITER = 100


def colebrook_residual(friction_factor: float, reynolds: float,
                       relative_roughness: float) -> float:
    """``1/sqrt(f) + 2 log10(eps/(3.7D) + 2.51/(Re sqrt(f)))``.

    Zero at the solution. Evaluated independently of the solver so an accepted
    result can be checked against the equation it claims to satisfy.
    """
    f = float(friction_factor)
    if not math.isfinite(f) or f <= 0.0:
        raise InputError(
            f"friction factor must be positive and finite, got {f!r}")
    root_f = math.sqrt(f)
    inside = (float(relative_roughness) / 3.7
              + 2.51 / (float(reynolds) * root_f))
    if inside <= 0.0:
        raise InputError(
            "the Colebrook logarithm argument is not positive; the state is "
            "outside the correlation's domain")
    return 1.0 / root_f + 2.0 * math.log10(inside)


def _check_domain(reynolds: float, relative_roughness: float) -> None:
    if not math.isfinite(reynolds) or reynolds < REYNOLDS_TURBULENT_ONSET:
        raise InputError(
            f"Colebrook-White is a turbulent correlation and is not applied "
            f"below Re = {REYNOLDS_TURBULENT_ONSET:g}; got {reynolds!r}. Below "
            "the transition the laminar branch applies, and inside it this "
            "model reports no friction factor at all.")
    if reynolds > COLEBROOK_REYNOLDS_MAX:
        raise InputError(
            f"Re = {reynolds!r} is above the Moody chart's turbulent zone "
            f"({COLEBROOK_REYNOLDS_MAX:g}); the correlation is not "
            "extrapolated there.")
    if not math.isfinite(relative_roughness) or relative_roughness < 0.0:
        raise InputError(
            f"relative roughness must be finite and non-negative, got "
            f"{relative_roughness!r}")
    if relative_roughness > MAX_RELATIVE_ROUGHNESS:
        raise InputError(
            f"relative roughness {relative_roughness!r} is above the "
            f"{MAX_RELATIVE_ROUGHNESS:g} the Moody chart covers; the "
            "correlation is not extrapolated beyond the data it was fitted to.")


def colebrook_darcy_friction_factor(
    reynolds: float, relative_roughness: float,
) -> tuple[float, RootReport]:
    """Solve Colebrook-White for the **Darcy** friction factor.

    Returns ``(f_D, report)``. The report carries the iteration count, the
    residual and the bracket, and it travels into the line result: a number
    produced by an iteration should be able to say how it was produced.

    A non-converged solve is **not** silently replaced by an approximation or
    by the last iterate. The caller is told, and decides.
    """
    reynolds = float(reynolds)
    relative_roughness = float(relative_roughness)
    _check_domain(reynolds, relative_roughness)

    a = relative_roughness / 3.7
    b = 2.51 / reynolds

    def g(x: float) -> float:
        return x + 2.0 * math.log10(a + b * x)

    low, high = COLEBROOK_BRACKET
    root, report = brent(g, low, high, xtol=COLEBROOK_XTOL,
                         rtol=COLEBROOK_RTOL, max_iter=COLEBROOK_MAX_ITER)
    friction_factor = 1.0 / (root * root)
    return friction_factor, report
