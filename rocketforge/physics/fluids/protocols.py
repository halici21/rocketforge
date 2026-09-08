"""What a fluid-property provider must look like, and what it may be asked.

This module declares the abstraction. It implements no provider, imports no
property library, and never will: ``providers`` implements what ``physics``
declares, and the arrow points that way and not back (``06`` section 3).

The shape mirrors ``physics.thermochemistry.protocols`` deliberately. A second
provider boundary that worked differently from the first would be a second
thing to learn for no gain.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, runtime_checkable

from rocketforge.core.result import Solution

from .errors import FluidError, UnsupportedFluidPropertyError
from .provenance import FluidPropertyProvenance
from .requests import FluidStateRequest
from .states import FluidState
from .types import FluidPhase, FluidProperty

__all__ = [
    "FluidPropertyCapability",
    "FluidPropertyCapabilities",
    "FluidPropertyProvider",
    "capability_for",
]


class FluidPropertyCapability(StrEnum):
    """One thing a fluid-property provider can do.

    The five property capabilities mirror :class:`~.types.FluidProperty` one
    for one. ``PHASE_IDENTIFICATION`` and ``SATURATION_STATE`` are separate
    because a provider can return a density without being able to say whether
    the state was liquid, and because locating the saturation line is a
    distinct piece of information from being able to evaluate away from it.
    """

    DENSITY = "density"
    SPECIFIC_ENTHALPY = "specific_enthalpy"
    SPECIFIC_HEAT_CP = "specific_heat_cp"
    DYNAMIC_VISCOSITY = "dynamic_viscosity"
    THERMAL_CONDUCTIVITY = "thermal_conductivity"
    PHASE_IDENTIFICATION = "phase_identification"
    """Can say which phase a state is in, not only return numbers."""
    SATURATION_STATE = "saturation_state"
    """Can locate the saturation boundary, and therefore refuse a two-phase
    state rather than silently returning one branch of it."""
    TEMPERATURE_DEPENDENCE = "temperature_dependence"
    """Properties actually change with temperature. A constant-property model
    does **not** declare this, which is what stops it being mistaken for a real
    cryogenic model."""
    PRESSURE_DEPENDENCE = "pressure_dependence"
    """Properties actually change with pressure."""


_PROPERTY_CAPABILITY = {
    FluidProperty.DENSITY: FluidPropertyCapability.DENSITY,
    FluidProperty.SPECIFIC_ENTHALPY: FluidPropertyCapability.SPECIFIC_ENTHALPY,
    FluidProperty.SPECIFIC_HEAT_CP: FluidPropertyCapability.SPECIFIC_HEAT_CP,
    FluidProperty.DYNAMIC_VISCOSITY: FluidPropertyCapability.DYNAMIC_VISCOSITY,
    FluidProperty.THERMAL_CONDUCTIVITY:
        FluidPropertyCapability.THERMAL_CONDUCTIVITY,
}


def capability_for(prop: FluidProperty) -> FluidPropertyCapability:
    """The capability a property requires."""
    if not isinstance(prop, FluidProperty):
        raise FluidError(f"{prop!r} is not a FluidProperty member")
    return _PROPERTY_CAPABILITY[prop]


@dataclass(frozen=True, slots=True)
class FluidPropertyCapabilities:
    """What a provider declares it can do, and over what range.

    **Declared, never discovered.** A caller must be able to ask before
    calling, so the interface can present honest options instead of finding a
    limitation through an exception mid-calculation.

    Attributes:
        supported: The capabilities this provider declares.
        fluids: Canonical fluid names it has data for. Empty declares no
            restriction.
        temperature_range: ``(min, max)`` K, validated range.
        pressure_range: ``(min, max)`` Pa, validated range.
        phases: The phases it can evaluate. Empty declares none.
    """

    supported: frozenset[FluidPropertyCapability] = field(
        default_factory=frozenset)
    fluids: frozenset[str] = field(default_factory=frozenset)
    temperature_range: tuple[float, float] | None = None
    pressure_range: tuple[float, float] | None = None
    phases: frozenset[FluidPhase] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.supported, frozenset):
            raise FluidError("supported must be a frozenset of capabilities")
        for item in self.supported:
            if not isinstance(item, FluidPropertyCapability):
                raise FluidError(f"{item!r} is not a FluidPropertyCapability")
        if not isinstance(self.fluids, frozenset):
            raise FluidError("fluids must be a frozenset of canonical names")
        if not isinstance(self.phases, frozenset):
            raise FluidError("phases must be a frozenset of FluidPhase members")
        for item in self.phases:
            if not isinstance(item, FluidPhase):
                raise FluidError(f"{item!r} is not a FluidPhase member")
        for name in ("temperature_range", "pressure_range"):
            value = getattr(self, name)
            if value is None:
                continue
            if not isinstance(value, tuple) or len(value) != 2:
                raise FluidError(f"{name} must be a (min, max) tuple")
            low, high = float(value[0]), float(value[1])
            if not (math.isfinite(low) and math.isfinite(high)):
                raise FluidError(f"{name} bounds must be finite")
            if low <= 0.0 or high <= low:
                raise FluidError(
                    f"{name} must be a positive ascending range, got {value!r}")

    def supports(self, capability: FluidPropertyCapability) -> bool:
        """Whether this provider declares ``capability``."""
        if not isinstance(capability, FluidPropertyCapability):
            raise FluidError(f"{capability!r} is not a FluidPropertyCapability")
        return capability in self.supported

    def supports_property(self, prop: FluidProperty) -> bool:
        """Whether this provider declares one property."""
        return self.supports(capability_for(prop))

    def require_property(self, prop: FluidProperty,
                         provider_id: str = "") -> None:
        """Raise unless a property is declared.

        A declared-absent property raises rather than falling back. Returning
        zero for a viscosity nobody has would be a number that looks like an
        answer and is not one.
        """
        if not self.supports_property(prop):
            who = f"{provider_id!r} " if provider_id else ""
            raise UnsupportedFluidPropertyError(
                f"provider {who}does not declare {prop.value}. A declared-absent "
                "property raises rather than returning a default: an "
                "unavailable viscosity is not 0 Pa s.")

    def has_fluid(self, name: str) -> bool:
        """Whether this provider declares data for a canonical fluid name."""
        return not self.fluids or name in self.fluids

    def temperature_is_in_range(self, temperature: float) -> bool:
        """Whether a temperature lies in the declared validated range."""
        if self.temperature_range is None:
            return True
        low, high = self.temperature_range
        return low <= float(temperature) <= high

    def pressure_is_in_range(self, pressure: float) -> bool:
        """Whether a pressure lies in the declared validated range."""
        if self.pressure_range is None:
            return True
        low, high = self.pressure_range
        return low <= float(pressure) <= high


@runtime_checkable
class FluidPropertyProvider(Protocol):
    """The one thing a fluid-property provider must be able to do.

    ``evaluate`` returns a ``Solution``: a state the provider has no data for
    is an answer -- "outside this equation of state's range" -- not a bug, and
    it arrives with a diagnostic naming what was missing. Malformed input still
    raises, and a broken provider still raises.
    """

    provider_id: str

    @property
    def capabilities(self) -> FluidPropertyCapabilities:
        """What this provider declares it can do."""
        ...

    def provenance(self) -> FluidPropertyProvenance:
        """This provider's identity, for recording on a result."""
        ...

    def evaluate(self, request: FluidStateRequest) -> Solution[FluidState]:
        """Evaluate one fluid at one temperature and one pressure."""
        ...
