"""Which fluid model stands behind which propellant.

A propellant is not a fluid. ``LOX`` is a *propellant*: a role, a composition,
a reference condition, a provider spelling. ``OXYGEN`` is a *fluid*: a
substance whose density and enthalpy an equation of state can produce. They map
one-to-one for the cryogens this project ships and they will not always: RP-1
is a propellant with no pure-fluid model at all, and a blend is a propellant
whose fluid behaviour is not any single component's.

So the association is an explicit, provenance-bearing record rather than a
name-matching rule. **No string-prefix inference**: nothing here asks whether
``"O2" in name``, because that would map ``O2(L)``, ``GOX`` and a hypothetical
``O2/N2`` blend to the same fluid and be wrong about the third.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from rocketforge.core.errors import DomainError
from rocketforge.physics.fluids import (
    HYDROGEN,
    METHANE,
    OXYGEN,
    FluidDefinition,
    FluidPhase,
)
from rocketforge.physics.thermochemistry import Phase, PropellantDefinition

__all__ = [
    "PropellantFluidBinding",
    "PropellantFluidMapping",
    "PRODUCTION_FLUID_MAPPING",
    "UnmappedPropellantError",
]


class UnmappedPropellantError(DomainError):
    """This propellant has no validated fluid model.

    Raised rather than guessed. A propellant with no fluid model has no
    validated density and no sensible-enthalpy correction, and saying so is the
    whole point: a surrogate chosen at the call site would be a physical claim
    made by a naming coincidence.
    """


@dataclass(frozen=True, slots=True)
class PropellantFluidBinding:
    """One propellant's fluid model, with the phase it is expected in.

    Attributes:
        propellant_name: RocketForge's propellant identifier, e.g. ``"LOX"``.
        fluid: The canonical fluid.
        expected_phase: The phase this binding is validated for. A request that
            finds another phase is refused, not converted.
        source: Why this association is believed. Required.
    """

    propellant_name: str
    fluid: FluidDefinition
    expected_phase: FluidPhase
    source: str

    def __post_init__(self) -> None:
        if not isinstance(self.propellant_name, str) or not self.propellant_name:
            raise DomainError("a binding must name its propellant")
        if not isinstance(self.fluid, FluidDefinition):
            raise DomainError(
                f"binding for {self.propellant_name!r} must carry a "
                f"FluidDefinition, got {type(self.fluid).__name__}")
        if not isinstance(self.expected_phase, FluidPhase):
            raise DomainError(
                f"binding for {self.propellant_name!r} must state the phase it "
                "is validated for; a density with no phase differs by three "
                "orders of magnitude between the two candidates")
        if not isinstance(self.source, str) or not self.source.strip():
            raise DomainError(
                f"binding for {self.propellant_name!r} must state its source")


class PropellantFluidMapping:
    """A read-only table of propellant-to-fluid bindings."""

    def __init__(self, bindings: Mapping[str, PropellantFluidBinding]) -> None:
        table: dict[str, PropellantFluidBinding] = {}
        for key, binding in bindings.items():
            if not isinstance(binding, PropellantFluidBinding):
                raise DomainError(
                    f"binding for {key!r} must be a PropellantFluidBinding")
            if binding.propellant_name != key:
                raise DomainError(
                    f"binding filed under {key!r} names itself "
                    f"{binding.propellant_name!r}")
            table[key] = binding
        self._table: Mapping[str, PropellantFluidBinding] = MappingProxyType(table)

    @property
    def bindings(self) -> Mapping[str, PropellantFluidBinding]:
        """Read-only view of the table."""
        return self._table

    def has(self, propellant: PropellantDefinition | str) -> bool:
        """Whether a validated fluid model exists for this propellant."""
        name = propellant if isinstance(propellant, str) else propellant.name
        return name in self._table

    def require(self, propellant: PropellantDefinition | str
                ) -> PropellantFluidBinding:
        """The binding, or a refusal naming what is unsupported."""
        name = propellant if isinstance(propellant, str) else propellant.name
        try:
            return self._table[name]
        except KeyError:
            raise UnmappedPropellantError(
                f"{name!r} has no validated fluid model, so it has no "
                f"validated density and no sensible-enthalpy correction. "
                f"Mapped propellants: {', '.join(sorted(self._table))}. A "
                "surrogate is not substituted: choosing one would be a "
                "physical claim, and it needs its own contract and its own "
                "validation.") from None


_SOURCE = ("CoolProp reference equations of state, validated in "
           "acceptance/fluids_foundation/fluid_external_reference.json; the "
           "propellant is a pure substance so the association is an identity, "
           "not a surrogate")

#: The propellants that have a validated fluid model. Three of the five
#: production propellants, and the two gaseous ones deliberately: their CEA
#: entries are already temperature-dependent, so they need no correction, and
#: a gaseous propellant is not stored as a bulk liquid volume.
PRODUCTION_FLUID_MAPPING = PropellantFluidMapping({
    "LOX": PropellantFluidBinding(
        propellant_name="LOX", fluid=OXYGEN,
        expected_phase=FluidPhase.LIQUID, source=_SOURCE),
    "LCH4": PropellantFluidBinding(
        propellant_name="LCH4", fluid=METHANE,
        expected_phase=FluidPhase.LIQUID, source=_SOURCE),
    "LH2": PropellantFluidBinding(
        propellant_name="LH2", fluid=HYDROGEN,
        expected_phase=FluidPhase.LIQUID, source=_SOURCE),
})
