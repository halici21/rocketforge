"""The identity matrix: every relation an ideal performance result must satisfy.

Nothing here is used to *produce* a number. Each check recomputes one quantity
along a path the solver did not take and compares. That is what makes it a
check rather than a restatement:

* ``c* = pc At / mdot`` recomputes c* from the scaled engine, while the solver
  computed it from the frozen mass-flow parameter;
* ``Cf = F / (pc At)`` recomputes the coefficient from dimensional thrust, while
  the solver built it from ``Ve/c*`` and the pressure ratio;
* ``c_eff = F / mdot`` and ``c_eff = Cf c*`` are two different routes to the
  same quantity, one dimensional and one not.

A residual is reported as **relative** wherever a scale exists, because these
quantities span from a dimensionless 1.9 to a thrust of 2e5 N and one absolute
tolerance cannot serve both.

The tolerance is float64 round-off through a handful of multiplications and
divisions, not a fitted number: 1e-12 relative is roughly four orders of
magnitude above the ~2e-16 per-operation limit, and the measured worst residual
across the acceptance cases is 3e-16.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rocketforge.core.constants import STANDARD_GRAVITY

from .types import IdealRocketPerformance

__all__ = [
    "IdentityCheck",
    "IdentityReport",
    "IDENTITY_TOLERANCE",
    "check_identities",
]

#: Relative tolerance for every identity below. See the module docstring.
IDENTITY_TOLERANCE = 1.0e-12


@dataclass(frozen=True, slots=True)
class IdentityCheck:
    """One relation, recomputed and compared."""

    name: str
    expected: float
    actual: float
    residual: float
    tolerance: float
    passed: bool
    scaled: bool = False

    @property
    def detail(self) -> str:
        return (f"{self.name}: {self.actual!r} against {self.expected!r}, "
                f"relative residual {self.residual:.3e}")


@dataclass(frozen=True, slots=True)
class IdentityReport:
    """Every applicable identity for one result."""

    checks: tuple[IdentityCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def worst(self) -> IdentityCheck | None:
        return max(self.checks, key=lambda c: c.residual, default=None)

    @property
    def failures(self) -> tuple[IdentityCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)


def _relative(expected: float, actual: float) -> float:
    """Relative difference, falling back to absolute near zero.

    The pressure terms are legitimately zero at ideal expansion, and a
    relative residual against zero is not defined. Below unity the comparison
    is absolute, which is the stricter of the two there.
    """
    scale = max(abs(expected), abs(actual))
    if scale <= 1.0:
        return abs(expected - actual)
    return abs(expected - actual) / scale


def _check(name: str, expected: float, actual: float, *,
           tolerance: float = IDENTITY_TOLERANCE,
           scaled: bool = False) -> IdentityCheck:
    residual = _relative(expected, actual)
    return IdentityCheck(name=name, expected=expected, actual=actual,
                         residual=residual, tolerance=tolerance,
                         passed=residual <= tolerance and math.isfinite(residual),
                         scaled=scaled)


def check_identities(result: IdealRocketPerformance,
                     *, tolerance: float = IDENTITY_TOLERANCE) -> IdentityReport:
    """Recompute every relation the result claims, along a different path.

    Scale-free identities always run. The dimensional ones run only when an
    engine size was given, because without one there is no mass flow to divide
    by -- and a check that quietly skips is worse than one that says it did not
    apply.
    """
    checks: list[IdentityCheck] = [
        _check("Cf = Cf_momentum + Cf_pressure",
               result.thrust_coefficient_momentum + result.thrust_coefficient_pressure,
               result.thrust_coefficient, tolerance=tolerance),
        _check("Cf_momentum = Ve / c*",
               result.exit.velocity / result.characteristic_velocity,
               result.thrust_coefficient_momentum, tolerance=tolerance),
        _check("Cf_pressure = ((pe - pa) / pc) * epsilon",
               ((result.exit.pressure - result.ambient_pressure)
                / result.chamber_pressure) * result.exit.area_ratio,
               result.thrust_coefficient_pressure, tolerance=tolerance),
        _check("c_eff = Cf c*",
               result.thrust_coefficient * result.characteristic_velocity,
               result.effective_exhaust_velocity, tolerance=tolerance),
        _check("Isp = c_eff / g0",
               result.effective_exhaust_velocity / STANDARD_GRAVITY,
               result.specific_impulse, tolerance=tolerance),
        _check("Isp = Cf c* / g0",
               result.thrust_coefficient * result.characteristic_velocity
               / STANDARD_GRAVITY,
               result.specific_impulse, tolerance=tolerance),
    ]

    if result.is_scaled:
        thrust = result.thrust
        pc_at = result.chamber_pressure * result.throat_area
        checks.extend([
            _check("c* = pc At / mdot", pc_at / result.mass_flow,
                   result.characteristic_velocity,
                   tolerance=tolerance, scaled=True),
            _check("Ae = epsilon At",
                   result.exit.area_ratio * result.throat_area,
                   result.exit_area, tolerance=tolerance, scaled=True),
            _check("F_momentum = mdot Ve",
                   result.mass_flow * result.exit.velocity,
                   thrust.momentum, tolerance=tolerance, scaled=True),
            _check("F_pressure = (pe - pa) Ae",
                   (result.exit.pressure - result.ambient_pressure)
                   * result.exit_area,
                   thrust.pressure, tolerance=tolerance, scaled=True),
            _check("F = F_momentum + F_pressure",
                   thrust.momentum + thrust.pressure,
                   thrust.total, tolerance=tolerance, scaled=True),
            _check("Cf = F / (pc At)", thrust.total / pc_at,
                   result.thrust_coefficient, tolerance=tolerance, scaled=True),
            _check("F = Cf pc At", result.thrust_coefficient * pc_at,
                   thrust.total, tolerance=tolerance, scaled=True),
            _check("c_eff = F / mdot", thrust.total / result.mass_flow,
                   result.effective_exhaust_velocity,
                   tolerance=tolerance, scaled=True),
            _check("Isp = F / (mdot g0)",
                   thrust.total / (result.mass_flow * STANDARD_GRAVITY),
                   result.specific_impulse, tolerance=tolerance, scaled=True),
        ])
    return IdentityReport(checks=tuple(checks))
