"""Rocket nozzle engineering: performance, not gas dynamics.

ADR-15 splits these two apart. Quasi-1D area/Mach/shock behaviour is
fundamental gas dynamics and belongs to ``physics.compressible``, which this
package imports and never restates. Thrust, thrust coefficient, characteristic
velocity, effective exhaust velocity and specific impulse are rocket device
design and belong here.

Phase 5E implements the ideal performance model. Contour generation, divergence
loss, efficiency factors and separation correlations are this package's other
responsibilities (``06`` section 2) and are not implemented -- an ideal figure
is an upper bound, and this package says so on every result rather than
quietly applying a factor.

Usable with no chemistry library installed, from a script::

    >>> from rocketforge.engineering.nozzle import characteristic_velocity
    >>> from rocketforge.physics.compressible import PerfectGas
    >>> gas = PerfectGas(gamma=1.20, gas_constant=350.0)
    >>> round(characteristic_velocity(gas, 3500.0), 2)
    1706.62
"""

from __future__ import annotations

from .performance import (
    SUPPORTED_NOZZLE_REGIMES,
    characteristic_velocity,
    solve_ideal_performance,
)
from .validation import (
    IDENTITY_TOLERANCE,
    IdentityCheck,
    IdentityReport,
    check_identities,
)
from .types import (
    IDEAL_MODEL_ASSUMPTIONS,
    IdealPerformanceRequest,
    IdealRocketPerformance,
    NozzleExitState,
    PerformanceScale,
    PerformanceScaleMode,
    ThrustBreakdown,
)

__all__ = [
    "characteristic_velocity",
    "solve_ideal_performance",
    "SUPPORTED_NOZZLE_REGIMES",
    "IdealPerformanceRequest",
    "IdealRocketPerformance",
    "NozzleExitState",
    "PerformanceScale",
    "PerformanceScaleMode",
    "ThrustBreakdown",
    "IDEAL_MODEL_ASSUMPTIONS",
    "check_identities",
    "IdentityCheck",
    "IdentityReport",
    "IDENTITY_TOLERANCE",
]
