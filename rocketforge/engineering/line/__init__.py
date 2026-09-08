"""Straight circular line: distributed wall friction for a single-phase liquid.

``06_future_module_dependency_map.md`` §8 **step 2**, and the first hydraulic
component in this project. It consumes ``physics.fluids`` and owns no property
model: a line asks nobody for a density.

**What it is.** Steady, single-phase liquid, straight circular pipe of constant
diameter, fully developed flow, constant properties from one fluid state,
distributed wall friction only, Darcy friction factor, explicit absolute
roughness, laminar and turbulent branches.

**What it is not.** No entrance length, no bends, no fittings, no valves, no
orifices, no minor losses, no elevation, no pumps, no heat transfer, no
compressible-gas piping, no two-phase flow, no cavitation, no transients, no
network solver, no variable-property integration along the line. Several of
those are the next roadmap steps, and hiding any of them here would make a
straight-line number quietly mean something else.

Imports ``core`` and ``physics.fluids``. No provider, no CEA, no CoolProp, no Qt.
"""

from __future__ import annotations

from .friction import (
    COLEBROOK_BRACKET,
    colebrook_darcy_friction_factor,
    colebrook_residual,
)
from .relations import (
    circular_area,
    darcy_weisbach_pressure_drop,
    dynamic_pressure,
    hagen_poiseuille_pressure_drop,
    laminar_darcy_friction_factor,
    mean_velocity,
    relative_roughness,
    reynolds_number,
    reynolds_number_from_mass_flow,
    volumetric_flow,
)
from .requests import (
    LINE_MODEL_ASSUMPTIONS,
    SUPPORTED_PHASES,
    CircularLineRequest,
)
from .results import LineFluidSnapshot, LineResult
from .solve import solve_line
from .types import (
    COLEBROOK_REYNOLDS_MAX,
    FRICTION_FACTOR_CONVENTION,
    MAX_RELATIVE_ROUGHNESS,
    REYNOLDS_LAMINAR_LIMIT,
    REYNOLDS_TURBULENT_ONSET,
    FlowRegime,
    classify,
)

__all__ = [
    "CircularLineRequest",
    "LineResult",
    "LineFluidSnapshot",
    "solve_line",
    "FlowRegime",
    "classify",
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
    "colebrook_darcy_friction_factor",
    "colebrook_residual",
    "COLEBROOK_BRACKET",
    "REYNOLDS_LAMINAR_LIMIT",
    "REYNOLDS_TURBULENT_ONSET",
    "COLEBROOK_REYNOLDS_MAX",
    "MAX_RELATIVE_ROUGHNESS",
    "FRICTION_FACTOR_CONVENTION",
    "LINE_MODEL_ASSUMPTIONS",
    "SUPPORTED_PHASES",
]
