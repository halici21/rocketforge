"""What is being asked of the line model.

One immutable request. It carries a fluid *state*, not a fluid name and not a
provider: the composition happens above this layer, and ``engineering.line``
never asks anyone for a property.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from rocketforge.core.errors import InputError
from rocketforge.physics.fluids import FluidPhase, FluidProperty, FluidState

__all__ = ["CircularLineRequest", "LINE_MODEL_ASSUMPTIONS", "SUPPORTED_PHASES"]

#: What a line result means, carried with every one of them.
LINE_MODEL_ASSUMPTIONS: tuple[str, ...] = (
    "steady flow",
    "single-phase liquid",
    "straight circular line of constant inner diameter",
    "fully developed flow -- no entrance length",
    "constant properties: one density and one viscosity along the whole line",
    "distributed wall friction only",
    "no fittings, bends, elbows, tees or other minor losses",
    "no valves and no orifices -- separate components",
    "no elevation or head term",
    "no heat transfer and no wall heating",
    "no cavitation, flashing or two-phase pressure drop",
    "no compressible-gas piping model",
)

#: v1 is a liquid model. A gas line is a compressible problem with its own
#: equations, and applying an incompressible relation to it silently would be a
#: different model wearing this one's name.
SUPPORTED_PHASES = (FluidPhase.LIQUID,)


@dataclass(frozen=True, slots=True)
class CircularLineRequest:
    """A fluid state, a flow, and a straight circular pipe.

    Attributes:
        fluid_state: The stream, already evaluated. Its **pressure is the line
            inlet / property-evaluation pressure** -- a feed-system state. It
            is not a chamber pressure, and nothing here reinterprets it as one.
        mass_flow: kg/s, strictly positive.
        length: m, strictly positive.
        inner_diameter: m, strictly positive.
        absolute_roughness: m, non-negative. Zero is a hydraulically smooth
            pipe and is supported.
    """

    fluid_state: FluidState
    mass_flow: float
    length: float
    inner_diameter: float
    absolute_roughness: float

    def __post_init__(self) -> None:
        if not isinstance(self.fluid_state, FluidState):
            raise InputError(
                f"fluid_state must be a FluidState, got "
                f"{type(self.fluid_state).__name__}. The line model consumes a "
                "provider-independent state; it never queries a provider.")
        for name in ("mass_flow", "length", "inner_diameter"):
            value = getattr(self, name)
            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise InputError(
                    f"{name} must be a real number, got {value!r}") from exc
            if not math.isfinite(number) or number <= 0.0:
                raise InputError(
                    f"{name} must be finite and strictly positive, got "
                    f"{value!r}. Nothing here is clamped or made absolute, and "
                    "a zero-flow or zero-length line is not solved as a "
                    "degenerate case: the friction correlations are undefined "
                    "there and a zero pressure drop would be an answer to a "
                    "question nobody asked.")
        roughness = float(self.absolute_roughness)
        if not math.isfinite(roughness) or roughness < 0.0:
            raise InputError(
                f"absolute_roughness must be finite and non-negative, got "
                f"{self.absolute_roughness!r}")

    @property
    def inlet_pressure(self) -> float:
        """Pa. The state's own pressure, named for what it is here."""
        return float(self.fluid_state.pressure)

    def usable_fluid(self) -> tuple[bool, str]:
        """Whether this state can drive the model, and why not if it cannot."""
        state = self.fluid_state
        if state.phase is None:
            return False, (
                f"{state.fluid.name} has no identified phase at "
                f"{state.temperature} K and {state.pressure} Pa. An "
                "unidentified phase is not assumed to be liquid.")
        if state.phase not in SUPPORTED_PHASES:
            return False, (
                f"{state.fluid.name} is {state.phase.value} at "
                f"{state.temperature} K and {state.pressure} Pa. Line v1 is a "
                "single-phase liquid model; a gas line is a compressible "
                "problem with different equations, and a two-phase line has no "
                "single density or viscosity at all.")
        for prop in (FluidProperty.DENSITY, FluidProperty.DYNAMIC_VISCOSITY):
            if not state.has(prop):
                return False, (
                    f"{prop.value} of {state.fluid.name} is not available "
                    f"({state.status_of(prop).value}). The line model needs "
                    "both density and dynamic viscosity, and neither is "
                    "defaulted or estimated.")
        return True, ""
