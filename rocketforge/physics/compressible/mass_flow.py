"""Compressible mass flow and the choked condition.

Specified in ``docs/engineering/03_compressible_flow_specification.md``
section 4. Steady, one-dimensional flow of a calorically perfect gas through a
known area, with the stagnation-to-static conversion taken from the isentropic
relations this module reuses rather than restates.

**Canonical normalisation.** Textbooks normalise mass flow half a dozen
different ways, so the one RocketForge uses is stated here and nowhere else:

    MFP(M, gamma)  =  mdot * sqrt(R * T0) / (A * p0)
                   =  sqrt(gamma) * M * [1 + (gamma-1)/2 * M^2] ^ (-(gamma+1)/(2(gamma-1)))

It is dimensionless, depends only on Mach number and gamma, and is what
:func:`mass_flow_parameter` returns. Every dimensional quantity in this module
is that group rearranged; there is no second definition anywhere.

What this module is not: there is no discharge coefficient, no boundary-layer
correction, no injector or valve behaviour and no nozzle efficiency. Those are
*device* corrections that multiply this ideal result, and they belong to the
engineering layer.
"""

from __future__ import annotations

import numpy as np

from ...core.errors import DomainError
from ...core.result import Solution
from ...core.tolerances import DEFAULT_TOLERANCES, ToleranceSet
from ...core.numerics.arrays import (
    as_float_array,
    require_above,
    require_at_least,
    require_finite,
    restore_scalar,
)
from .equations import MODEL_MASS_FLOW
from .gas import PerfectGas
from .types import FlowBranch
from . import isentropic as iso

__all__ = [
    "mass_flow_parameter",
    "mach_from_mass_flow_ratio",
    "choked_mass_flow_coefficient",
    "mass_flow",
    "mass_flux",
    "choked_mass_flow",
    "choked_mass_flux",
    "critical_pressure_ratio",
    "critical_temperature_ratio",
    "is_choked",
    "mass_flow_over_choked",
    "MODEL_MASS_FLOW",
]


def _mach_array(mach: object) -> tuple[np.ndarray, bool]:
    array, was_scalar = as_float_array(mach, "mach")
    require_finite(array, "mach")
    require_at_least(array, 0.0, "mach")
    return array, was_scalar


def _positive(value: object, name: str) -> float:
    array, _ = as_float_array(value, name)
    require_finite(array, name)
    require_above(array, 0.0, name)
    if array.ndim:
        raise DomainError(f"{name} must be a scalar")
    return float(array)


# ---------------------------------------------------------------------------
# dimensionless
# ---------------------------------------------------------------------------


def mass_flow_parameter(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """The dimensionless mass-flow parameter ``mdot sqrt(R T0) / (A p0)``.

    ``MFP = sqrt(gamma) M [1 + (gamma-1)/2 M^2]^(-(gamma+1)/(2(gamma-1)))``

    Args:
        mach: Mach number [-], >= 0. Scalar or array.
        gas: The gas model; only ``gamma`` is used, so no gas constant is
            needed for this dimensionless form.

    Returns:
        MFP [-]. Exactly 0 at M = 0, rising to its maximum at M = 1 and falling
        thereafter.

    The expression is written with M as a factor rather than as a division, so
    M = 0 gives exactly zero with no singular form to guard.
    """
    array, was_scalar = _mach_array(mach)
    gamma = gas.gamma
    exponent = -(gamma + 1.0) / (2.0 * (gamma - 1.0))
    phi = 1.0 + 0.5 * (gamma - 1.0) * array * array
    return restore_scalar(np.sqrt(gamma) * array * phi**exponent, was_scalar)


def choked_mass_flow_coefficient(gas: PerfectGas) -> float:
    """``Gamma(gamma)``, the value of the mass-flow parameter at Mach 1.

    ``Gamma = sqrt(gamma) (2/(gamma+1))^((gamma+1)/(2(gamma-1)))``

    Known in the propulsion literature as the vandenkerckhove function. It is
    the maximum of :func:`mass_flow_parameter`, which is why choking exists.
    """
    gamma = gas.gamma
    return float(np.sqrt(gamma) * (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0))))


def mass_flow_over_choked(mach: object, gas: PerfectGas) -> float | np.ndarray:
    """Mass flow as a fraction of the choked value at the same station.

    ``MFP(M) / Gamma(gamma)``, which is 1 at Mach 1 and below 1 everywhere
    else. A presentation-friendly normalisation, derived from the two functions
    above rather than from a third formula.
    """
    array, was_scalar = _mach_array(mach)
    ratio = np.asarray(mass_flow_parameter(array, gas)) / choked_mass_flow_coefficient(gas)
    return restore_scalar(ratio, was_scalar)


# ---------------------------------------------------------------------------
# dimensional
# ---------------------------------------------------------------------------


def mass_flow(
    mach: object,
    gas: PerfectGas,
    area: float,
    stagnation_pressure: float,
    stagnation_temperature: float,
) -> float | np.ndarray:
    """Mass flow rate through a known area.

    ``mdot = MFP(M, gamma) * A * p0 / sqrt(R * T0)``

    Args:
        mach: Mach number [-], >= 0. Scalar or array.
        gas: The gas model. Must carry a gas constant.
        area: Cross-sectional area [m²], > 0.
        stagnation_pressure: p0 [Pa], > 0.
        stagnation_temperature: T0 [K], > 0.

    Returns:
        Mass flow [kg/s].

    Scales linearly with area and with stagnation pressure, and inversely with
    the square root of stagnation temperature -- all three asserted by tests,
    because they are the dependencies an engineer actually reasons with.
    """
    r = gas._require_gas_constant("mass flow")
    area = _positive(area, "area [m2]")
    p0 = _positive(stagnation_pressure, "stagnation_pressure [Pa]")
    t0 = _positive(stagnation_temperature, "stagnation_temperature [K]")
    array, was_scalar = _mach_array(mach)
    parameter = np.asarray(mass_flow_parameter(array, gas))
    return restore_scalar(parameter * area * p0 / np.sqrt(r * t0), was_scalar)


def mass_flux(
    mach: object,
    gas: PerfectGas,
    stagnation_pressure: float,
    stagnation_temperature: float,
) -> float | np.ndarray:
    """Mass flow per unit area, ``rho V``.

    ``mdot / A = MFP(M, gamma) * p0 / sqrt(R * T0)``

    Returns:
        Mass flux [kg/(m² s)].

    Distinct from :func:`mass_flow`: this one carries no area at all, which is
    exactly why the two have different names.
    """
    return mass_flow(mach, gas, 1.0, stagnation_pressure, stagnation_temperature)


def choked_mass_flow(
    gas: PerfectGas,
    throat_area: float,
    stagnation_pressure: float,
    stagnation_temperature: float,
) -> float:
    """The maximum mass flow a passage of this area can pass.

    ``mdot_max = Gamma(gamma) * A* * p0 / sqrt(R * T0)``

    Args:
        gas: The gas model. Must carry a gas constant.
        throat_area: The minimum area, A* [m²].
        stagnation_pressure: p0 [Pa].
        stagnation_temperature: T0 [K].

    Returns:
        Choked mass flow [kg/s].

    This is :func:`mass_flow` evaluated at Mach 1, and is implemented as such
    rather than as a separate closed form.
    """
    return float(mass_flow(1.0, gas, throat_area, stagnation_pressure, stagnation_temperature))


def choked_mass_flux(
    gas: PerfectGas,
    stagnation_pressure: float,
    stagnation_temperature: float,
) -> float:
    """The maximum mass flux, ``Gamma p0 / sqrt(R T0)`` [kg/(m² s)]."""
    return float(mass_flux(1.0, gas, stagnation_pressure, stagnation_temperature))


# ---------------------------------------------------------------------------
# the critical condition
# ---------------------------------------------------------------------------


def critical_pressure_ratio(gas: PerfectGas) -> float:
    """``p*/p0``, the static-to-stagnation pressure ratio at Mach 1.

    Delegated to the isentropic module rather than restated, so there is one
    value of this constant in the codebase and not two that round differently.
    """
    return float(iso.pressure_ratio(1.0, gas))


def critical_temperature_ratio(gas: PerfectGas) -> float:
    """``T*/T0`` at Mach 1, likewise delegated to the isentropic relations."""
    return float(iso.temperature_ratio(1.0, gas))


def is_choked(pressure_ratio: float, gas: PerfectGas) -> bool:
    """Whether a simple convergent passage is choked at this pressure ratio.

    Args:
        pressure_ratio: Receiver static pressure over upstream stagnation
            pressure, ``p_receiver / p0`` [-], in (0, 1].
        gas: The gas model.

    Returns:
        True when ``p_receiver/p0 <= p*/p0``.

    Deliberately narrow, per ``03`` section 4.3. This answers one question
    about one geometry: a convergent passage discharging to a receiver. It is
    **not** a nozzle regime classifier -- a converging-diverging nozzle can be
    choked at its throat while its exit pressure sits anywhere across a wide
    band, and deciding that needs the area ratio and a shock analysis that
    belong to the nozzle module.
    """
    array, _ = as_float_array(pressure_ratio, "pressure_ratio")
    require_finite(array, "pressure_ratio")
    require_above(array, 0.0, "pressure_ratio")
    if float(array) > 1.0:
        raise DomainError(
            f"pressure_ratio is p_receiver/p0 and cannot exceed 1, got {float(array)!r}"
        )
    return bool(float(array) <= critical_pressure_ratio(gas))


# ---------------------------------------------------------------------------
# inverse
# ---------------------------------------------------------------------------


def mach_from_mass_flow_ratio(
    ratio: float,
    gas: PerfectGas,
    branch: FlowBranch,
    tolerances: ToleranceSet = DEFAULT_TOLERANCES,
) -> Solution[float]:
    """Mach number from ``mdot / mdot_choked`` on an explicitly chosen branch.

    Args:
        ratio: Mass flow as a fraction of the choked mass flow through the same
            area at the same stagnation state, in (0, 1].
        gas: The gas model.
        branch: Which of the two roots is wanted. Required, for the same reason
            the area-ratio inverse requires it.
        tolerances: Numerical tolerances.

    Returns:
        A :class:`Solution` carrying the Mach number.

    Solved through an identity rather than as a second root problem. For a
    fixed area and stagnation state,

        mdot / mdot_choked  =  MFP(M) / Gamma  =  A* / A  =  1 / (A/A*),

    because the same mass flow passes both the station and its own sonic
    throat. The mass-flow inverse therefore *is* the area-Mach inverse, and
    calling it here inherits every bracket, tolerance and near-sonic diagnostic
    already verified for :func:`isentropic.mach_from_area_ratio`, instead of
    introducing a second, separately conditioned solve of the same curve.
    """
    array, _ = as_float_array(ratio, "mass flow ratio")
    require_finite(array, "mass flow ratio")
    require_above(array, 0.0, "mass flow ratio (mdot/mdot_choked)")
    value = float(array)
    if value > 1.0 + tolerances.area_sonic_tol:
        raise DomainError(
            "mass flow ratio (mdot/mdot_choked) cannot exceed 1: the choked value is "
            f"the most a given area can pass, got {value!r}"
        )
    return iso.mach_from_area_ratio(1.0 / min(value, 1.0), gas, branch, tolerances)
