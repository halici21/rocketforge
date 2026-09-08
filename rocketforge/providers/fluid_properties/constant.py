"""A dependency-free, in-tree fluid-property provider.

Its purpose is architectural, not scientific: it proves the provider boundary
without an external library, it gives the tests a deterministic fixture, and it
will give the hydraulic components that come next something to run against.

**It is not a cryogenic property model and must never be mistaken for one.** It
declares neither ``TEMPERATURE_DEPENDENCE`` nor ``PRESSURE_DEPENDENCE``, so a
caller can ask -- before calling -- whether the numbers it will get respond to
state at all. Every state it returns carries the approximation by name in its
provenance, and the reactant-enthalpy coupling refuses it outright, because a
sensible-enthalpy increment from a model with constant cp and no pressure term
would be a correction computed from an assumption.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from rocketforge.core.result import Diagnostic, Severity, Solution, Status
from rocketforge.physics.fluids import (
    FluidError,
    FluidPhase,
    FluidProperty,
    FluidPropertyCapabilities,
    FluidPropertyCapability,
    FluidPropertyProvenance,
    FluidState,
    FluidStateRequest,
    PropertyStatus,
    capability_for,
)

__all__ = [
    "ConstantPropertyDefinition",
    "ConstantPropertyProvider",
    "CONSTANT_PROPERTY_APPROXIMATION",
    "UNRESTRICTED_TEST_MODEL",
]

CONSTANT_PROPERTY_APPROXIMATION = (
    "CONSTANT_PROPERTY_APPROXIMATION: properties do not vary with temperature "
    "or pressure in this model")

UNRESTRICTED_TEST_MODEL = (
    "UNRESTRICTED_TEST_MODEL: a synthetic fluid with no validity envelope, for "
    "tests only; not a production substance")


@dataclass(frozen=True, slots=True)
class ConstantPropertyDefinition:
    """Fixed property values for one fluid, with the state they are valid at.

    Attributes:
        phase: The phase these values describe. Required: a density with no
            phase is a number, and the liquid and gas values differ by three
            orders of magnitude.
        values: Property to value, canonical SI. A property absent here is
            reported ``NOT_SUPPORTED``, never defaulted.
        temperature_range: ``(min, max)`` K over which these values are
            claimed. ``None`` is allowed **only** for a test model, which must
            then say so in :attr:`source`.
        pressure_range: ``(min, max)`` Pa, same rule.
        source: Where the numbers came from. Required for a production fluid.
        is_test_model: True for a synthetic fluid with no envelope.
    """

    phase: FluidPhase
    values: Mapping[FluidProperty, float]
    temperature_range: tuple[float, float] | None = None
    pressure_range: tuple[float, float] | None = None
    source: str = ""
    is_test_model: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.phase, FluidPhase):
            raise FluidError(
                f"phase must be a FluidPhase member, got {self.phase!r}")
        if not isinstance(self.values, Mapping) or not self.values:
            raise FluidError("a constant-property definition must carry values")
        for prop, value in self.values.items():
            if not isinstance(prop, FluidProperty):
                raise FluidError(f"{prop!r} is not a FluidProperty member")
            number = float(value)
            if not math.isfinite(number):
                raise FluidError(f"{prop.value} must be finite, got {value!r}")
        for name in ("temperature_range", "pressure_range"):
            bounds = getattr(self, name)
            if bounds is None:
                continue
            if not isinstance(bounds, tuple) or len(bounds) != 2:
                raise FluidError(f"{name} must be a (min, max) tuple")
            low, high = float(bounds[0]), float(bounds[1])
            if not (math.isfinite(low) and math.isfinite(high)) or low <= 0.0 \
                    or high <= low:
                raise FluidError(
                    f"{name} must be a positive ascending range, got {bounds!r}")
        if not self.is_test_model:
            if not self.source.strip():
                raise FluidError(
                    "a production constant-property definition must name its "
                    "source; an unattributed constant is an unfalsifiable number")
            if self.temperature_range is None or self.pressure_range is None:
                raise FluidError(
                    "a production constant-property definition must state the "
                    "envelope its values are claimed over. A constant that "
                    "claims validity everywhere is claiming to be an equation "
                    "of state.")
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def covers(self, temperature: float, pressure: float) -> bool:
        """Whether this definition claims validity at a state."""
        if self.temperature_range is not None:
            low, high = self.temperature_range
            if not low <= float(temperature) <= high:
                return False
        if self.pressure_range is not None:
            low, high = self.pressure_range
            if not low <= float(pressure) <= high:
                return False
        return True


class ConstantPropertyProvider:
    """Serves fixed property values for the fluids it was given.

    Constructed with an explicit table, never with a hidden built-in catalogue:
    the caller states which constants it is using, and those constants travel
    into the provenance of every state produced.
    """

    provider_id = "constant"

    def __init__(self, definitions: Mapping[str, ConstantPropertyDefinition],
                 *, label: str = "Constant properties",
                 version: str = "1.0") -> None:
        if not isinstance(definitions, Mapping) or not definitions:
            raise FluidError(
                "a constant-property provider needs at least one fluid; an "
                "empty one would refuse everything without saying why")
        table: dict[str, ConstantPropertyDefinition] = {}
        for name, definition in definitions.items():
            if not isinstance(name, str) or not name.strip():
                raise FluidError(f"fluid key must be a non-empty string, got {name!r}")
            if not isinstance(definition, ConstantPropertyDefinition):
                raise FluidError(
                    f"definition for {name!r} must be a "
                    f"ConstantPropertyDefinition, got {type(definition).__name__}")
            table[name] = definition
        self._definitions: Mapping[str, ConstantPropertyDefinition] = \
            MappingProxyType(table)
        self._label = str(label)
        self._version = str(version)

        properties: set[FluidProperty] = set()
        phases: set[FluidPhase] = set()
        for definition in table.values():
            properties.update(definition.values)
            phases.add(definition.phase)
        supported = {capability_for(p) for p in properties}
        # Phase is *declared* by each definition, so the provider can always
        # say which phase its numbers describe. It cannot locate a saturation
        # line, and it does not vary with state -- both absences are declared,
        # which is how a caller tells this apart from a real model.
        supported.add(FluidPropertyCapability.PHASE_IDENTIFICATION)
        self._capabilities = FluidPropertyCapabilities(
            supported=frozenset(supported),
            fluids=frozenset(table),
            phases=frozenset(phases))

    @property
    def definitions(self) -> Mapping[str, ConstantPropertyDefinition]:
        """Read-only view of the table this provider was built with."""
        return self._definitions

    @property
    def capabilities(self) -> FluidPropertyCapabilities:
        """What this provider declares it can do."""
        return self._capabilities

    def provenance(self, native_name: str = "") -> FluidPropertyProvenance:
        """This provider's identity, carrying the approximation by name."""
        return FluidPropertyProvenance(
            provider_id=self.provider_id,
            provider_label=self._label,
            provider_version=self._version,
            library_version="",
            backend="constant-property",
            native_fluid_name=native_name,
            model_notes=("fixed values; no equation of state, no temperature "
                         "or pressure dependence"),
            approximations=(CONSTANT_PROPERTY_APPROXIMATION,))

    def evaluate(self, request: FluidStateRequest) -> Solution[FluidState]:
        """Return the fixed values for this fluid, or say why not."""
        if not isinstance(request, FluidStateRequest):
            raise FluidError(
                f"expected a FluidStateRequest, got {type(request).__name__}")

        name = request.fluid.name
        definition = self._definitions.get(name)
        provenance = self.provenance(native_name=name)
        if definition is None:
            return Solution(
                value=None, status=Status.NO_SOLUTION,
                diagnostics=(Diagnostic(
                    code="FLUID_NOT_IN_CONSTANT_TABLE", severity=Severity.ERROR,
                    message=(f"this constant-property provider has no entry for "
                             f"{name!r}. It serves only the fluids it was "
                             f"constructed with: "
                             f"{', '.join(sorted(self._definitions))}."),
                    field="fluid"),))

        if not definition.covers(request.temperature, request.pressure):
            return Solution(
                value=None, status=Status.NO_SOLUTION,
                diagnostics=(Diagnostic(
                    code="FLUID_STATE_OUTSIDE_CONSTANT_ENVELOPE",
                    severity=Severity.ERROR,
                    message=(f"{name!r} at {request.temperature} K and "
                             f"{request.pressure} Pa is outside the envelope "
                             f"these constants are claimed over "
                             f"(T {definition.temperature_range}, "
                             f"p {definition.pressure_range}). The provider "
                             "refuses rather than extrapolating a constant."),
                    field="state",
                    detail={"temperature": float(request.temperature),
                            "pressure": float(request.pressure)}),),
                provenance=(provenance,))

        if request.required_phase is not None \
                and request.required_phase is not definition.phase:
            return Solution(
                value=None, status=Status.NO_SOLUTION,
                diagnostics=(Diagnostic(
                    code="FLUID_PHASE_MISMATCH", severity=Severity.ERROR,
                    message=(f"{name!r} is defined here as "
                             f"{definition.phase.value}, and the caller "
                             f"requires {request.required_phase.value}."),
                    field="phase"),),
                provenance=(provenance,))

        values: dict[FluidProperty, float] = {}
        statuses: dict[FluidProperty, PropertyStatus] = {}
        for prop in FluidProperty:
            if prop not in definition.values:
                statuses[prop] = PropertyStatus.NOT_SUPPORTED
                continue
            if not request.wants(prop):
                statuses[prop] = PropertyStatus.NOT_REQUESTED
                continue
            values[prop] = float(definition.values[prop])
            statuses[prop] = PropertyStatus.AVAILABLE

        state = FluidState(
            fluid=request.fluid,
            temperature=float(request.temperature),
            pressure=float(request.pressure),
            phase=definition.phase,
            provenance=provenance,
            values=values,
            statuses=statuses)

        return Solution(
            value=state, status=Status.OK_WITH_WARNINGS,
            diagnostics=(Diagnostic(
                code="CONSTANT_PROPERTY_APPROXIMATION",
                severity=Severity.WARNING,
                message=(f"These properties for {name!r} are fixed constants, "
                         f"not an equation of state: the requested "
                         f"{request.temperature} K and {request.pressure} Pa "
                         "did not change them. Source: "
                         f"{definition.source or 'test model'}."),
                field="provider"),),
            provenance=(provenance,))
