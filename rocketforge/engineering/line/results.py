"""What a line solve produces.

Immutable, and it carries the state it was solved from -- so a stored result
can never be relabelled with inputs that did not produce it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from rocketforge.core.errors import DomainError

from .types import FRICTION_FACTOR_CONVENTION, FlowRegime

__all__ = ["LineResult", "LineFluidSnapshot"]


@dataclass(frozen=True, slots=True)
class LineFluidSnapshot:
    """The fluid values the solve actually used, and where they came from.

    Recorded rather than re-read: a result must be able to say which density
    and which viscosity produced it, and prove they were the state's own.
    """

    fluid_name: str
    temperature: float
    pressure: float
    phase: str
    density: float
    dynamic_viscosity: float
    provider_id: str
    provider_label: str
    library_version: str
    backend: str

    def as_mapping(self) -> dict[str, object]:
        """A JSON-safe view, units named."""
        return {
            "fluid": self.fluid_name,
            "temperature_K": self.temperature,
            "pressure_Pa": self.pressure,
            "phase": self.phase,
            "density_kg_per_m3": self.density,
            "dynamic_viscosity_Pa_s": self.dynamic_viscosity,
            "provider": self.provider_id,
            "provider_label": self.provider_label,
            "library_version": self.library_version,
            "backend": self.backend,
        }


@dataclass(frozen=True, slots=True)
class LineResult:
    """Steady single-phase liquid flow through one straight circular line.

    ``darcy_friction_factor``, ``major_pressure_drop`` and ``outlet_pressure``
    are ``None`` in the transitional regime -- **not zero, and not
    interpolated**. A number there would be a fabrication wearing the authority
    of the two correlations it sits between.
    """

    fluid: LineFluidSnapshot
    mass_flow: float
    length: float
    inner_diameter: float
    absolute_roughness: float

    area: float
    volumetric_flow: float
    mean_velocity: float
    reynolds_number: float
    reynolds_number_from_mass_flow: float
    relative_roughness: float
    dynamic_pressure: float
    flow_regime: FlowRegime

    darcy_friction_factor: float | None = None
    major_pressure_drop: float | None = None
    inlet_pressure: float | None = None
    outlet_pressure: float | None = None
    colebrook_residual: float | None = None
    convergence: Any = None
    assumptions: tuple[str, ...] = ()
    friction_convention: str = FRICTION_FACTOR_CONVENTION

    def __post_init__(self) -> None:
        for name in ("area", "volumetric_flow", "mean_velocity",
                     "reynolds_number", "dynamic_pressure"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value <= 0.0:
                raise DomainError(
                    f"{name} of a line result must be finite and positive, "
                    f"got {value!r}")
        if self.flow_regime is FlowRegime.TRANSITIONAL:
            if self.darcy_friction_factor is not None \
                    or self.major_pressure_drop is not None:
                raise DomainError(
                    "a transitional line result must carry no friction factor "
                    "and no pressure drop; this model reports neither there, "
                    "and a value would be invented rather than computed")
        elif self.darcy_friction_factor is None:
            raise DomainError(
                f"a {self.flow_regime.value} result must carry a friction "
                "factor")

    @property
    def reynolds_identity_residual(self) -> float:
        """Relative disagreement between the two Reynolds forms."""
        return (abs(self.reynolds_number - self.reynolds_number_from_mass_flow)
                / self.reynolds_number)

    def as_mapping(self) -> dict[str, object]:
        """A JSON-safe view, units named."""
        report = self.convergence
        return {
            "fluid": self.fluid.as_mapping(),
            "mass_flow_kg_per_s": self.mass_flow,
            "length_m": self.length,
            "inner_diameter_m": self.inner_diameter,
            "absolute_roughness_m": self.absolute_roughness,
            "area_m2": self.area,
            "volumetric_flow_m3_per_s": self.volumetric_flow,
            "mean_velocity_m_per_s": self.mean_velocity,
            "reynolds_number": self.reynolds_number,
            "reynolds_number_from_mass_flow": self.reynolds_number_from_mass_flow,
            "reynolds_identity_residual": self.reynolds_identity_residual,
            "relative_roughness": self.relative_roughness,
            "flow_regime": self.flow_regime.value,
            "darcy_friction_factor": self.darcy_friction_factor,
            "friction_convention": self.friction_convention,
            "dynamic_pressure_Pa": self.dynamic_pressure,
            "major_pressure_drop_Pa": self.major_pressure_drop,
            "inlet_pressure_Pa": self.inlet_pressure,
            "outlet_pressure_Pa": self.outlet_pressure,
            "colebrook_residual": self.colebrook_residual,
            "convergence": (None if report is None else {
                "converged": bool(report.converged),
                "iterations": int(report.iterations),
                "residual": float(report.residual),
                "method": str(report.method),
            }),
            "assumptions": list(self.assumptions),
        }
