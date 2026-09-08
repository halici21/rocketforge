"""Fluid phases and the property vocabulary.

Two enumerations, both closed sets, both without a member that means "no
answer". Absence is expressed by ``None`` or by an explicit status, never by a
member that a required field would silently accept.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "FluidPhase",
    "FluidProperty",
    "PropertyStatus",
]


class FluidPhase(StrEnum):
    """The phase a fluid is actually in at a state.

    **There is deliberately no ``UNKNOWN`` member**, which is a documented
    departure from the brief's suggested member list and a deliberate match to
    the rule this project already applies to
    ``physics.thermochemistry.Phase``: an enum member meaning "unknown" is a
    value that silently satisfies a required field. Where the phase genuinely
    may be unknown the field is typed ``FluidPhase | None`` and ``None`` means
    unknown -- and *nothing in this package ever reads ``None`` as GAS*.

    ``TWO_PHASE`` is a real answer and not an absence, so it *is* a member. It
    exists so that a saturated state can be reported as what it is rather than
    collapsed into the liquid branch: a single density for a state that has two
    of them is the error this member prevents.
    """

    LIQUID = "liquid"
    GAS = "gas"
    SUPERCRITICAL = "supercritical"
    SOLID = "solid"
    TWO_PHASE = "two_phase"

    @property
    def is_single_phase(self) -> bool:
        """True for the phases that have one density, one enthalpy, one cp."""
        return self in (FluidPhase.LIQUID, FluidPhase.GAS,
                        FluidPhase.SUPERCRITICAL, FluidPhase.SOLID)

    @property
    def is_condensed(self) -> bool:
        """True for LIQUID and SOLID. Supercritical is neither."""
        return self in (FluidPhase.LIQUID, FluidPhase.SOLID)


class FluidProperty(StrEnum):
    """A property this package can carry, with its canonical SI unit.

    Five, chosen because the roadmap needs exactly these and no more: density
    and viscosity for the hydraulic components that come next, enthalpy and cp
    for reactant energy, thermal conductivity for the thermal work after that.

    Not an encyclopedia. Every additional property is another thing to
    validate, and an unvalidated property in a frozen contract is worse than an
    absent one.
    """

    DENSITY = "density"
    SPECIFIC_ENTHALPY = "specific_enthalpy"
    SPECIFIC_HEAT_CP = "specific_heat_cp"
    DYNAMIC_VISCOSITY = "dynamic_viscosity"
    THERMAL_CONDUCTIVITY = "thermal_conductivity"

    @property
    def unit(self) -> str:
        """The canonical SI unit. There is no other unit inside this package."""
        return _UNITS[self]


_UNITS = {
    FluidProperty.DENSITY: "kg/m^3",
    FluidProperty.SPECIFIC_ENTHALPY: "J/kg",
    FluidProperty.SPECIFIC_HEAT_CP: "J/(kg K)",
    FluidProperty.DYNAMIC_VISCOSITY: "Pa s",
    FluidProperty.THERMAL_CONDUCTIVITY: "W/(m K)",
}


class PropertyStatus(StrEnum):
    """Why a property is or is not present on a state.

    ``UNAVAILABLE`` is not zero, and the distinctions below are not cosmetic:
    "this provider has no viscosity model" and "this state is outside the
    viscosity model's range" lead a caller to different actions.
    """

    AVAILABLE = "available"
    NOT_REQUESTED = "not_requested"
    """The provider has it; this request did not ask for it. Distinct from
    NOT_SUPPORTED because one is a caller's choice and the other is a
    provider's limit, and confusing them would make a provider look poorer
    than it is."""
    NOT_SUPPORTED = "not_supported"
    """The provider does not declare this property at all."""
    OUT_OF_RANGE = "out_of_range"
    """Declared, but not valid at this state."""
    PHASE_UNSUPPORTED = "phase_unsupported"
    """Declared, but not defined for the phase found here."""
    TWO_PHASE_AMBIGUOUS = "two_phase_ambiguous"
    """The state is on the saturation boundary, where the property has two
    values and no single one is correct."""
    PROVIDER_FAILED = "provider_failed"
    """The provider raised or returned a non-finite number for it."""
