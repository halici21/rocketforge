"""Validated stream densities, bulk propellant density, and density impulse.

**Not fundamental fluid physics.** ``physics.fluids`` answers "what is the
density of oxygen at 95 K and 3 bar". This module answers "what volume does a
tank of LOX and LCH4 at O/F 3.4 occupy, and how much impulse comes out of it" --
a derived propulsion/design metric that consumes a fluid state, a mixture
ratio and a RocketForge performance figure, and owns none of them.

**No ``density_hint`` anywhere.** ``PropellantDefinition.density_hint`` remains
display-only reference metadata by the Phase 5A/5B contract. Every number here
comes from a fluid-property provider at the stream's actual temperature,
pressure and phase, and a static audit asserts this module never reads the hint.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rocketforge.core.constants import STANDARD_GRAVITY
from rocketforge.core.errors import DomainError
from rocketforge.physics.fluids import (
    FluidProperty,
    FluidPropertyProvider,
    FluidState,
    FluidStateRequest,
)

from .mapping import PropellantFluidBinding

__all__ = [
    "StreamDensity",
    "BulkPropellantDensity",
    "DensityImpulse",
    "stream_density",
    "mixture_bulk_density",
    "density_impulse",
    "ADDITIVE_VOLUME_ASSUMPTIONS",
]

#: What the bulk density number does and does not mean. Travels with every
#: result, because "propellant density" is read as a physical property of a
#: mixture and it is not one.
ADDITIVE_VOLUME_ASSUMPTIONS = (
    "the two propellants are stored in separate volumes",
    "the tank volumes add: V = m_f/rho_f + m_ox/rho_ox",
    "no chemical mixing -- this is not the density of a LOX/fuel solution",
    "no ullage volume",
    "no tank structure, insulation or residuals",
    "no thermal stratification: one temperature per stream",
)


@dataclass(frozen=True, slots=True)
class StreamDensity:
    """One propellant stream's density, at the state it was evaluated at."""

    propellant_name: str
    fluid_name: str
    temperature: float
    pressure: float
    phase: str
    density: float
    provider_id: str
    provider_label: str
    library_version: str
    backend: str

    def as_mapping(self) -> dict[str, object]:
        """A JSON-safe view, units named."""
        return {
            "propellant": self.propellant_name,
            "fluid": self.fluid_name,
            "temperature_K": self.temperature,
            "pressure_Pa": self.pressure,
            "phase": self.phase,
            "density_kg_per_m3": self.density,
            "provider": self.provider_id,
            "provider_label": self.provider_label,
            "library_version": self.library_version,
            "backend": self.backend,
        }


def stream_density(provider: FluidPropertyProvider,
                   binding: PropellantFluidBinding,
                   temperature: float, pressure: float) -> StreamDensity:
    """Evaluate one stream's density at its own temperature and pressure.

    The pressure is the caller's and has no default. It is a **feed-system**
    state: the chamber pressure is a different state entirely, and using it
    here would evaluate liquid oxygen at 100 bar because that happened to be
    the number in scope.
    """
    solution = provider.evaluate(FluidStateRequest(
        fluid=binding.fluid, temperature=float(temperature),
        pressure=float(pressure),
        properties=(FluidProperty.DENSITY,),
        required_phase=binding.expected_phase))
    state: FluidState | None = solution.value
    if state is None:
        reasons = "; ".join(d.message for d in solution.diagnostics) \
            or "no reason given"
        raise DomainError(
            f"no validated density for {binding.propellant_name!r} at "
            f"{temperature} K and {pressure} Pa: {reasons}")
    provenance = state.provenance
    return StreamDensity(
        propellant_name=binding.propellant_name,
        fluid_name=binding.fluid.name,
        temperature=float(state.temperature),
        pressure=float(state.pressure),
        phase=state.phase.value if state.phase is not None else "unknown",
        density=float(state.density),
        provider_id=provenance.provider_id,
        provider_label=provenance.provider_label,
        library_version=provenance.library_version,
        backend=provenance.backend)


@dataclass(frozen=True, slots=True)
class BulkPropellantDensity:
    """The additive-volume bulk density of a propellant pair.

    ``1/rho_mix = w_f/rho_f + w_ox/rho_ox`` with ``w_ox = OF/(1+OF)`` and
    ``w_f = 1/(1+OF)``, which rearranges to

        rho_mix = (1 + OF) / (1/rho_f + OF/rho_ox)

    It is the mass of propellant divided by the volume it occupies in two
    separate tanks. It is **not** the density of a mixture of the two, which is
    not a thing that exists at these conditions, and
    :data:`ADDITIVE_VOLUME_ASSUMPTIONS` travels with every instance so the
    distinction cannot be lost downstream.
    """

    oxidiser_fuel_ratio: float
    fuel: StreamDensity
    oxidiser: StreamDensity
    fuel_mass_fraction: float
    oxidiser_mass_fraction: float
    density: float
    assumptions: tuple[str, ...] = ADDITIVE_VOLUME_ASSUMPTIONS

    def as_mapping(self) -> dict[str, object]:
        """A JSON-safe view, units named."""
        return {
            "oxidiser_fuel_ratio": self.oxidiser_fuel_ratio,
            "fuel": self.fuel.as_mapping(),
            "oxidiser": self.oxidiser.as_mapping(),
            "fuel_mass_fraction": self.fuel_mass_fraction,
            "oxidiser_mass_fraction": self.oxidiser_mass_fraction,
            "bulk_density_kg_per_m3": self.density,
            "formula": "rho_mix = (1 + OF) / (1/rho_f + OF/rho_ox)",
            "assumptions": list(self.assumptions),
        }


def mixture_bulk_density(oxidiser_fuel_ratio: float, fuel: StreamDensity,
                         oxidiser: StreamDensity) -> BulkPropellantDensity:
    """Bulk propellant density from two validated stream densities."""
    of = float(oxidiser_fuel_ratio)
    if not math.isfinite(of) or of <= 0.0:
        raise DomainError(
            f"O/F must be positive and finite, got {oxidiser_fuel_ratio!r}")
    for label, stream in (("fuel", fuel), ("oxidiser", oxidiser)):
        if not isinstance(stream, StreamDensity):
            raise DomainError(f"{label} must be a StreamDensity record")
        if not math.isfinite(stream.density) or stream.density <= 0.0:
            raise DomainError(
                f"{label} density must be positive and finite, got "
                f"{stream.density!r} kg/m^3")
    return BulkPropellantDensity(
        oxidiser_fuel_ratio=of,
        fuel=fuel, oxidiser=oxidiser,
        fuel_mass_fraction=1.0 / (1.0 + of),
        oxidiser_mass_fraction=of / (1.0 + of),
        density=(1.0 + of) / (1.0 / fuel.density + of / oxidiser.density))


@dataclass(frozen=True, slots=True)
class DensityImpulse:
    """Volumetric impulse: ``rho_mix * c_eff``.

    Units ``kg/(m^2 s)``, equivalently ``N s / m^3`` -- impulse per unit of
    propellant *volume*, which is what makes it the metric for a
    volume-constrained stage.

    Two spellings of one quantity, and both are checked against each other on
    every instance:

        I_d = rho_mix * c_eff
        I_d = rho_mix * Isp * g0

    They agree because ``c_eff = Isp * g0`` by RocketForge's own definition.
    The record deliberately does **not** offer a second metric called
    ``rho * Isp``: that is a different quantity with different units, and one
    name for two things is how the two get confused.
    """

    bulk_density: BulkPropellantDensity
    effective_exhaust_velocity: float
    specific_impulse: float
    value: float
    residual: float
    unit: str = "kg/(m^2 s)"
    unit_alias: str = "N s / m^3"

    def as_mapping(self) -> dict[str, object]:
        """A JSON-safe view, units named."""
        return {
            "density_impulse": self.value,
            "unit": self.unit,
            "unit_alias": self.unit_alias,
            "bulk_density_kg_per_m3": self.bulk_density.density,
            "effective_exhaust_velocity_m_per_s":
                self.effective_exhaust_velocity,
            "specific_impulse_s": self.specific_impulse,
            "formula": "rho_mix * c_eff",
            "identity": "rho_mix * Isp * g0",
            "identity_residual": self.residual,
            "standard_gravity_m_per_s2": STANDARD_GRAVITY,
            "assumptions": list(self.bulk_density.assumptions),
        }


def density_impulse(bulk: BulkPropellantDensity,
                    effective_exhaust_velocity: float,
                    specific_impulse: float) -> DensityImpulse:
    """``rho_mix * c_eff``, with the ``rho_mix * Isp * g0`` identity checked.

    c_eff is the canonical input because density impulse is volumetric
    effective exhaust momentum; Isp is taken as well so the two spellings can
    be compared rather than assumed equal. Both come from RocketForge's own
    performance model -- never from a provider's native Isp.
    """
    if not isinstance(bulk, BulkPropellantDensity):
        raise DomainError("bulk must be a BulkPropellantDensity record")
    c_eff = float(effective_exhaust_velocity)
    isp = float(specific_impulse)
    for label, value in (("effective exhaust velocity", c_eff),
                         ("specific impulse", isp)):
        if not math.isfinite(value) or value <= 0.0:
            raise DomainError(
                f"{label} must be positive and finite, got {value!r}")
    value = bulk.density * c_eff
    via_isp = bulk.density * isp * STANDARD_GRAVITY
    return DensityImpulse(
        bulk_density=bulk,
        effective_exhaust_velocity=c_eff,
        specific_impulse=isp,
        value=value,
        residual=abs(value - via_isp) / value)
