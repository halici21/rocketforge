"""The pure relations. One owner each, no state, no provider, no Qt.

Small functions a caller can use directly and a test can check in isolation,
following the two-tier shape the rest of this project already uses: pure
relations here, regime and iteration logic in :mod:`solve`.
"""

from __future__ import annotations

import math

from rocketforge.core.errors import InputError

__all__ = [
    "circular_area",
    "volumetric_flow",
    "mean_velocity",
    "reynolds_number",
    "reynolds_number_from_mass_flow",
    "relative_roughness",
    "dynamic_pressure",
    "laminar_darcy_friction_factor",
    "darcy_weisbach_pressure_drop",
    "hagen_poiseuille_pressure_drop",
]


def _positive(value: object, what: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise InputError(f"{what} must be a real number, got {value!r}") from exc
    if not math.isfinite(number):
        raise InputError(f"{what} must be finite, got {number!r}")
    if number <= 0.0:
        raise InputError(
            f"{what} must be strictly positive, got {number!r}. This model "
            "does not clamp, take an absolute value, or treat zero as a "
            "degenerate case.")
    return number


def _non_negative(value: object, what: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise InputError(f"{what} must be a real number, got {value!r}") from exc
    if not math.isfinite(number):
        raise InputError(f"{what} must be finite, got {number!r}")
    if number < 0.0:
        raise InputError(f"{what} must not be negative, got {number!r}")
    return number


def circular_area(diameter: float) -> float:
    """``A = pi D^2 / 4``, m^2. The single owner of this geometry."""
    d = _positive(diameter, "inner diameter")
    return math.pi * d * d / 4.0


def volumetric_flow(mass_flow: float, density: float) -> float:
    """``Q = mdot / rho``, m^3/s, for a constant-density stream."""
    return _positive(mass_flow, "mass flow") / _positive(density, "density")


def mean_velocity(mass_flow: float, density: float, diameter: float) -> float:
    """``V = Q / A = mdot / (rho A)``, m/s."""
    return (volumetric_flow(mass_flow, density)
            / circular_area(diameter))


def reynolds_number(density: float, velocity: float, diameter: float,
                    viscosity: float) -> float:
    """``Re = rho V D / mu``. Dimensionless. The canonical definition."""
    return (_positive(density, "density") * _positive(velocity, "velocity")
            * _positive(diameter, "inner diameter")
            / _positive(viscosity, "dynamic viscosity"))


def reynolds_number_from_mass_flow(mass_flow: float, diameter: float,
                                   viscosity: float) -> float:
    """``Re = 4 mdot / (pi D mu)``, the circular mass-flow form.

    Algebraically identical to :func:`reynolds_number` for a circular pipe, and
    kept as a separate function precisely so the two can be compared. Density
    cancels, which is why this form needs no density argument -- and a
    disagreement between the two is a defect in one of them.
    """
    return (4.0 * _positive(mass_flow, "mass flow")
            / (math.pi * _positive(diameter, "inner diameter")
               * _positive(viscosity, "dynamic viscosity")))


def relative_roughness(absolute_roughness: float, diameter: float) -> float:
    """``epsilon / D``. Dimensionless. Zero for a hydraulically smooth pipe."""
    return (_non_negative(absolute_roughness, "absolute roughness")
            / _positive(diameter, "inner diameter"))


def dynamic_pressure(density: float, velocity: float) -> float:
    """``q = rho V^2 / 2``, Pa."""
    v = _positive(velocity, "velocity")
    return 0.5 * _positive(density, "density") * v * v


def laminar_darcy_friction_factor(reynolds: float) -> float:
    """``f_D = 64 / Re`` for fully developed laminar flow in a circular pipe.

    Exact, not a correlation: it follows from the Hagen-Poiseuille solution.
    **Independent of roughness**, which is asserted by a test -- a laminar
    friction factor that moved with roughness would mean the roughness had
    leaked into the wrong branch.
    """
    return 64.0 / _positive(reynolds, "Reynolds number")


def darcy_weisbach_pressure_drop(friction_factor: float, length: float,
                                 diameter: float, density: float,
                                 velocity: float) -> float:
    """``dp = f_D (L/D) rho V^2 / 2``, Pa. Distributed wall friction only.

    No entrance effect, no fitting, no bend, no valve, no elevation. Those are
    separate components and separate roadmap steps; hiding any of them here
    would make a straight-line number quietly mean something else.
    """
    return (_positive(friction_factor, "Darcy friction factor")
            * _positive(length, "length") / _positive(diameter, "inner diameter")
            * dynamic_pressure(density, velocity))


def hagen_poiseuille_pressure_drop(viscosity: float, length: float,
                                   volumetric: float, diameter: float) -> float:
    """``dp = 128 mu L Q / (pi D^4)``, Pa.

    The exact laminar solution, written independently of Darcy-Weisbach so the
    two can be compared. It is **not** the production path: the production path
    is Darcy-Weisbach with ``f_D = 64/Re``, and this exists to prove that path
    reproduces the closed-form answer.
    """
    d = _positive(diameter, "inner diameter")
    return (128.0 * _positive(viscosity, "dynamic viscosity")
            * _positive(length, "length") * _positive(volumetric, "volumetric flow")
            / (math.pi * d ** 4))
