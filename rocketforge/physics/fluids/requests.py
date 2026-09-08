"""What is being asked of a fluid-property provider.

One request type, with **temperature and pressure both required**. That is the
whole design decision, and it is the one this package exists to enforce.

A property model evaluated at an unstated pressure is not a property: liquid
oxygen at 95 K is a liquid at 3 bar and a gas at 1 atm, and a request that
omitted the pressure would silently pick one. So there is no default pressure,
no "standard condition" fallback, and nothing anywhere in this package that
substitutes 101325 Pa for a pressure the caller did not give.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .errors import FluidRequestError
from .identity import FluidDefinition
from .types import FluidPhase, FluidProperty

__all__ = ["FluidStateRequest"]


def _finite(value: object, what: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise FluidRequestError(
            f"{what} must be a real number, got {value!r}") from exc
    if not math.isfinite(number):
        raise FluidRequestError(f"{what} must be finite, got {number!r}")
    return number


@dataclass(frozen=True, slots=True)
class FluidStateRequest:
    """A fluid, a temperature, a pressure, and what is wanted of them.

    Attributes:
        fluid: The substance.
        temperature: K, strictly positive. Kelvin, always. A Celsius value
            would be silently wrong rather than obviously wrong, which is why
            the field is validated rather than converted.
        pressure: Pa, strictly positive. **Required.** See the module
            docstring: there is no default, and none may be added.
        properties: Which properties are wanted. Empty means all of the
            provider's declared set.
        required_phase: When set, the provider must find this phase at this
            state or the request is refused by name. Used by the reactant
            coupling, which is a liquid model and must not be handed a gas.
    """

    fluid: FluidDefinition
    temperature: float
    pressure: float
    properties: tuple[FluidProperty, ...] = ()
    required_phase: FluidPhase | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.fluid, FluidDefinition):
            raise FluidRequestError(
                f"fluid must be a FluidDefinition, got {type(self.fluid).__name__}")
        temperature = _finite(self.temperature,
                              f"temperature for {self.fluid.name!r}")
        if temperature <= 0.0:
            raise FluidRequestError(
                f"temperature for {self.fluid.name!r} must be above 0 K, got "
                f"{temperature!r}. This package works in kelvin.")
        pressure = _finite(self.pressure, f"pressure for {self.fluid.name!r}")
        if pressure <= 0.0:
            raise FluidRequestError(
                f"pressure for {self.fluid.name!r} must be above 0 Pa, got "
                f"{pressure!r}. There is no default pressure in this package: "
                "the phase, and therefore every property, depends on it.")
        if not isinstance(self.properties, tuple):
            raise FluidRequestError(
                f"properties must be a tuple of FluidProperty members, got "
                f"{type(self.properties).__name__}")
        for item in self.properties:
            if not isinstance(item, FluidProperty):
                raise FluidRequestError(
                    f"{item!r} is not a FluidProperty member")
        if len(set(self.properties)) != len(self.properties):
            raise FluidRequestError(
                f"properties contains a duplicate: {self.properties!r}")
        if self.required_phase is not None and not isinstance(
                self.required_phase, FluidPhase):
            raise FluidRequestError(
                f"required_phase must be a FluidPhase member or None, got "
                f"{self.required_phase!r}")

    @property
    def wants_everything(self) -> bool:
        """Whether the caller left the property list open."""
        return not self.properties

    def wants(self, prop: FluidProperty) -> bool:
        """Whether this request asks for one property."""
        if not isinstance(prop, FluidProperty):
            raise FluidRequestError(f"{prop!r} is not a FluidProperty member")
        return self.wants_everything or prop in self.properties
