"""Propellant-level engineering metrics: fluid bindings, density, density impulse.

L2. Consumes ``physics.fluids`` and ``physics.thermochemistry``; owns no
property model, no chemistry and no nozzle. Density impulse lives here rather
than in ``physics.fluids`` because it is a design metric about a stage, not a
property of a substance.
"""

from __future__ import annotations

from .density import (
    ADDITIVE_VOLUME_ASSUMPTIONS,
    BulkPropellantDensity,
    DensityImpulse,
    StreamDensity,
    density_impulse,
    mixture_bulk_density,
    stream_density,
)
from .mapping import (
    PRODUCTION_FLUID_MAPPING,
    PropellantFluidBinding,
    PropellantFluidMapping,
    UnmappedPropellantError,
)

__all__ = [
    "PropellantFluidBinding",
    "PropellantFluidMapping",
    "PRODUCTION_FLUID_MAPPING",
    "UnmappedPropellantError",
    "StreamDensity",
    "BulkPropellantDensity",
    "DensityImpulse",
    "stream_density",
    "mixture_bulk_density",
    "density_impulse",
    "ADDITIVE_VOLUME_ASSUMPTIONS",
]
