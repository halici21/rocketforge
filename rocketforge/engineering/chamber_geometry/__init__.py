"""Combustion-chamber geometry (LIQ-5): L*, contraction ratio, convergent.

``06`` section 2 assigns chamber sizing to ``engineering.chamber``. That
package is frozen as part of the Rocket Performance API v1
(``tests/acceptance``), so the geometry is its own package beside it, as
``engineering.line`` and ``engineering.propellants`` are. It depends on
nothing in ``engineering.chamber``.
"""

from __future__ import annotations

from .relations import (
    CONTRACTION_PRESSURE_LOSS_ADVISORY,
    CYLINDER_VOLUME_TOLERANCE,
    TYPICAL_BIPROPELLANT_L_STAR,
    ChamberGeometry,
    conical_frustum_volume,
    converging_length,
    cylindrical_conical_chamber,
)

__all__ = [
    "CONTRACTION_PRESSURE_LOSS_ADVISORY",
    "CYLINDER_VOLUME_TOLERANCE",
    "TYPICAL_BIPROPELLANT_L_STAR",
    "ChamberGeometry",
    "conical_frustum_volume",
    "converging_length",
    "cylindrical_conical_chamber",
]
