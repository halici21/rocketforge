"""The answer: a fluid at a state, with its properties and their status.

Every property in the vocabulary has a :class:`~.types.PropertyStatus` on every
state, whether or not it has a value. That is the point of the record: a
missing viscosity is a *reason*, not an absence, and certainly not a zero.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .errors import FluidPhaseError, FluidStateError, UnsupportedFluidPropertyError
from .identity import FluidDefinition
from .provenance import FluidPropertyProvenance
from .types import FluidPhase, FluidProperty, PropertyStatus

__all__ = ["FluidState"]

#: Properties that cannot be negative for any physically meaningful state.
_STRICTLY_POSITIVE = (
    FluidProperty.DENSITY,
    FluidProperty.SPECIFIC_HEAT_CP,
    FluidProperty.DYNAMIC_VISCOSITY,
    FluidProperty.THERMAL_CONDUCTIVITY,
)


@dataclass(frozen=True, slots=True)
class FluidState:
    """A fluid evaluated at one temperature and one pressure.

    Attributes:
        fluid: The substance.
        temperature: K, as evaluated.
        pressure: Pa, as evaluated.
        phase: The phase the provider found, or ``None`` when it does not
            identify phases. ``None`` is never read as GAS anywhere.
        provenance: Which model produced this.
        values: The properties that are actually available, in canonical SI.
        statuses: One status per property in the whole vocabulary. A property
            absent from :attr:`values` must have a status explaining why.

    Specific enthalpy is deliberately **not** in
    :data:`_STRICTLY_POSITIVE`: it is negative for every one of the cryogens
    this project ships, because its zero is a convention rather than a floor.
    That convention is exactly why enthalpy is only ever consumed here as a
    *difference* -- see ``REACTANT_ENTHALPY_COUPLING_CONTRACT.md``.
    """

    fluid: FluidDefinition
    temperature: float
    pressure: float
    phase: FluidPhase | None
    provenance: FluidPropertyProvenance
    values: Mapping[FluidProperty, float]
    statuses: Mapping[FluidProperty, PropertyStatus]

    def __post_init__(self) -> None:
        if not isinstance(self.fluid, FluidDefinition):
            raise FluidStateError(
                f"fluid must be a FluidDefinition, got {type(self.fluid).__name__}")
        for name in ("temperature", "pressure"):
            value = getattr(self, name)
            number = float(value)
            if not math.isfinite(number) or number <= 0.0:
                raise FluidStateError(
                    f"{name} of a fluid state must be finite and above zero, "
                    f"got {value!r}")
        if self.phase is not None and not isinstance(self.phase, FluidPhase):
            raise FluidStateError(
                f"phase must be a FluidPhase member or None, got {self.phase!r}. "
                "None means unknown and is never read as GAS.")
        if not isinstance(self.provenance, FluidPropertyProvenance):
            raise FluidStateError(
                "a fluid state must carry provenance; an unattributed property "
                "cannot be checked against its source later")
        if not isinstance(self.values, Mapping) or not isinstance(
                self.statuses, Mapping):
            raise FluidStateError("values and statuses must both be mappings")

        for prop, value in self.values.items():
            if not isinstance(prop, FluidProperty):
                raise FluidStateError(f"{prop!r} is not a FluidProperty member")
            number = float(value)
            if not math.isfinite(number):
                raise FluidStateError(
                    f"{prop.value} of {self.fluid.name!r} is {value!r}. A "
                    "non-finite property is reported through its status, never "
                    "stored as a value.")
            if prop in _STRICTLY_POSITIVE and number <= 0.0:
                raise FluidStateError(
                    f"{prop.value} of {self.fluid.name!r} is {number!r}, which "
                    f"is not physically possible. Unknown is not zero: an "
                    "unavailable property is omitted and given a status.")
        for prop in FluidProperty:
            status = self.statuses.get(prop)
            if not isinstance(status, PropertyStatus):
                raise FluidStateError(
                    f"no status recorded for {prop.value}. Every property in "
                    "the vocabulary carries a status on every state, so that a "
                    "missing one is always a stated reason.")
            has_value = prop in self.values
            if status is PropertyStatus.AVAILABLE and not has_value:
                raise FluidStateError(
                    f"{prop.value} is marked available but carries no value")
            if status is not PropertyStatus.AVAILABLE and has_value:
                raise FluidStateError(
                    f"{prop.value} carries a value but its status is "
                    f"{status.value}; a value with a non-available status is "
                    "a number nobody can interpret")

        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
        object.__setattr__(self, "statuses",
                           MappingProxyType(dict(self.statuses)))

    # -- access ------------------------------------------------------------

    def status_of(self, prop: FluidProperty) -> PropertyStatus:
        """Why this property is or is not present."""
        if not isinstance(prop, FluidProperty):
            raise FluidStateError(f"{prop!r} is not a FluidProperty member")
        return self.statuses[prop]

    def has(self, prop: FluidProperty) -> bool:
        """Whether this property has a usable value here."""
        return self.status_of(prop) is PropertyStatus.AVAILABLE

    def optional(self, prop: FluidProperty) -> float | None:
        """The value, or ``None`` when it is not available.

        For a caller that genuinely handles absence. A caller that does not
        should use :meth:`value_of`, which refuses with the reason.
        """
        return self.values.get(prop)

    def value_of(self, prop: FluidProperty) -> float:
        """The value, or a refusal that names why there isn't one."""
        if self.has(prop):
            return float(self.values[prop])
        raise UnsupportedFluidPropertyError(
            f"{prop.value} of {self.fluid.name!r} at {self.temperature} K and "
            f"{self.pressure} Pa is not available: "
            f"{self.status_of(prop).value}. Provider "
            f"{self.provenance.provider_label!r}.")

    @property
    def density(self) -> float:
        """kg/m^3."""
        return self.value_of(FluidProperty.DENSITY)

    @property
    def specific_enthalpy(self) -> float:
        """J/kg, on the provider's own enthalpy datum.

        **Only meaningful as a difference against another state of the same
        fluid from the same provider.** The zero is a convention, and mixing
        two conventions is the single largest error this package can make.
        """
        return self.value_of(FluidProperty.SPECIFIC_ENTHALPY)

    @property
    def specific_heat_cp(self) -> float:
        """J/(kg K)."""
        return self.value_of(FluidProperty.SPECIFIC_HEAT_CP)

    @property
    def dynamic_viscosity(self) -> float:
        """Pa s."""
        return self.value_of(FluidProperty.DYNAMIC_VISCOSITY)

    @property
    def thermal_conductivity(self) -> float:
        """W/(m K)."""
        return self.value_of(FluidProperty.THERMAL_CONDUCTIVITY)

    # -- phase -------------------------------------------------------------

    def require_phase(self, phase: FluidPhase) -> None:
        """Refuse unless the state is in ``phase``.

        Used wherever a model is defined for one phase only. An unknown phase
        refuses too: a model that needs a liquid must not proceed on a state
        that never said what it was.
        """
        if not isinstance(phase, FluidPhase):
            raise FluidStateError(f"{phase!r} is not a FluidPhase member")
        if self.phase is phase:
            return
        if self.phase is None:
            raise FluidPhaseError(
                f"{self.fluid.name!r} at {self.temperature} K and "
                f"{self.pressure} Pa has no identified phase, and this "
                f"calculation requires {phase.value}. An unidentified phase is "
                "not assumed to be the one that was wanted.")
        raise FluidPhaseError(
            f"{self.fluid.name!r} at {self.temperature} K and {self.pressure} "
            f"Pa is {self.phase.value}, and this calculation requires "
            f"{phase.value}.")

    @property
    def is_single_phase(self) -> bool:
        """Whether the state has one value of each property."""
        return self.phase is not None and self.phase.is_single_phase

    def as_mapping(self) -> Mapping[str, object]:
        """A JSON-safe view for artifacts and for the interface."""
        return MappingProxyType({
            "fluid": self.fluid.name,
            "formula": self.fluid.formula,
            "temperature_K": float(self.temperature),
            "pressure_Pa": float(self.pressure),
            "phase": self.phase.value if self.phase is not None else None,
            "values": {p.value: float(v) for p, v in self.values.items()},
            "units": {p.value: p.unit for p in self.values},
            "statuses": {p.value: s.value for p, s in self.statuses.items()},
            "provenance": dict(self.provenance.as_mapping()),
        })
