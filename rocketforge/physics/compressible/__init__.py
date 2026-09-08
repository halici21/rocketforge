"""Compressible flow for a calorically perfect gas.

The fundamental gas-dynamics layer: relations that are true of a flowing
perfect gas independently of any device. Nothing here knows what a rocket is.
Thrust, specific impulse, nozzle contours and chamber sizing belong to
``rocketforge.engineering``, which calls this module rather than restating it.

Implemented in this release:

* :class:`PerfectGas` -- constant gamma, constant R, with cp, cv and the speed
  of sound derived from them;
* the isentropic ratios, their sonic-reference forms, and the Mach angle;
* the three closed-form inverses, from T/T0, p/p0 and rho/rho0;
* the area-Mach relation and its two-branch numerical inverse;
* compressible mass flow, mass flux and the choked condition;
* the normal-shock jump relations, including the Rayleigh pitot ratio;
* the oblique-shock theta-beta-M relation and the Prandtl-Meyer expansion;
* Fanno flow (adiabatic, with friction) and Rayleigh flow (frictionless, with
  heat exchange), each with its starred ratios, its branch-aware inverse and
  its duct problem;
* the quasi-1D converging-diverging nozzle: its three critical pressure ratios,
  back-pressure regime classification, internal normal-shock location and the
  distributed solution along a supplied area distribution.

Everything a caller needs is reachable from this package. No normal use should
require importing a private module path.

Usable without Qt, from a script or a notebook:

    >>> from rocketforge.physics.compressible import PerfectGas, isentropic, FlowBranch
    >>> gas = PerfectGas(gamma=1.22, gas_constant=320.0)   # combustion products
    >>> exit_mach = isentropic.mach_from_area_ratio(12.4, gas, FlowBranch.SUPERSONIC)
    >>> round(exit_mach.unwrap(), 4)
    3.4938
"""

from __future__ import annotations

from . import (
    equations,
    fanno,
    gas,
    geometry,
    isentropic,
    mass_flow,
    normal_shock,
    nozzle,
    oblique_shock,
    prandtl_meyer,
    rayleigh,
)
from .gas import PerfectGas, speed_of_sound
from .geometry import AreaDistribution
from .normal_shock import NormalShockResult
from .prandtl_meyer import PrandtlMeyerResult
from .types import (
    AreaMachSolutions,
    CriticalPressureRatios,
    FannoDuctResult,
    FannoState,
    FlowBranch,
    FlowState,
    IsentropicRatios,
    NozzleOperating,
    NozzleRegime,
    NozzleRegimeResult,
    NozzleSolution,
    ObliqueShockPair,
    ObliqueShockResult,
    RayleighDuctResult,
    RayleighState,
    ShockBranch,
    ShockLocation,
    StagnationState,
    ThetaBetaCurve,
    ThetaMaxResult,
)

__all__ = [
    "PerfectGas",
    "speed_of_sound",
    "FlowBranch",
    "IsentropicRatios",
    "AreaMachSolutions",
    "NormalShockResult",
    "PrandtlMeyerResult",
    "ShockBranch",
    "ObliqueShockResult",
    "ObliqueShockPair",
    "ThetaMaxResult",
    "ThetaBetaCurve",
    "FannoState",
    "FannoDuctResult",
    "RayleighState",
    "RayleighDuctResult",
    "FlowState",
    "StagnationState",
    "AreaDistribution",
    "NozzleOperating",
    "NozzleRegime",
    "CriticalPressureRatios",
    "ShockLocation",
    "NozzleRegimeResult",
    "NozzleSolution",
    "isentropic",
    "mass_flow",
    "normal_shock",
    "oblique_shock",
    "prandtl_meyer",
    "fanno",
    "rayleigh",
    "nozzle",
    "geometry",
    "equations",
    "gas",
]
