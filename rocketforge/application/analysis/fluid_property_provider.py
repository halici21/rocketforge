"""The application's only door to a fluid-property provider.

The same two responsibilities as the thermochemistry gateway, and the same
deliberate absence of a third: say whether a provider can be used, and own the
instance. Nothing above this module imports
:mod:`rocketforge.providers.fluid_properties`.

**Every provider import here is function-local, on purpose**, for the reason
Phase 5C established and Phase 5D kept: constructing a controller at start-up
must not pull in a native library for a workspace nobody has opened. An
architecture test holds the line.

Qt-free, so the "nothing installed" branch is testable headlessly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "FluidProviderAvailability",
    "FluidOption",
    "availability",
    "property_provider",
    "fluid_options",
    "fluid_named",
    "reset_fluid_provider_state",
    "HIGH_FIDELITY_LABEL",
    "CONSTANT_LABEL",
    "NOT_INSTALLED_REMEDY",
]

#: What the interface calls the real provider. The machine id stays "coolprop".
HIGH_FIDELITY_LABEL = "CoolProp (HEOS reference equations of state)"

#: And the approximation, which is never presented as its equal.
CONSTANT_LABEL = "Constant properties (approximation)"

NOT_INSTALLED_REMEDY = (
    "Install the fluid-property dependency profile "
    "(requirements-fluids.txt) into this environment, or use the packaged "
    "RocketForge application, which ships the provider.")

_PROVIDER: Any | None = None


@dataclass(frozen=True, slots=True)
class FluidProviderAvailability:
    """Whether high-fidelity fluid properties can be used here."""

    installed: bool
    label: str
    library_version: str
    backend: str
    detail: str

    @property
    def is_usable(self) -> bool:
        """Whether a real property query will succeed."""
        return self.installed


@dataclass(frozen=True, slots=True)
class FluidOption:
    """One fluid the interface may offer."""

    name: str
    formula: str
    molar_mass: float
    label: str


def availability() -> FluidProviderAvailability:
    """Whether the high-fidelity provider is present. Never raises."""
    from rocketforge.providers.fluid_properties import coolprop_is_available

    if not coolprop_is_available():
        return FluidProviderAvailability(
            installed=False, label=HIGH_FIDELITY_LABEL, library_version="",
            backend="", detail=NOT_INSTALLED_REMEDY)
    provider = property_provider()
    # Touch the library once so the version is real rather than declared.
    provenance = provider.provenance()
    if not provenance.library_version:
        provider.saturation_pressure("OXYGEN", 90.0)
        provenance = provider.provenance()
    return FluidProviderAvailability(
        installed=True, label=HIGH_FIDELITY_LABEL,
        library_version=provenance.library_version,
        backend=provenance.backend,
        detail="High-fidelity fluid properties are available.")


def property_provider() -> Any:
    """The one provider instance, constructed once and reused."""
    global _PROVIDER
    if _PROVIDER is None:
        from rocketforge.providers.fluid_properties import coolprop_provider

        _PROVIDER = coolprop_provider()
    return _PROVIDER


def reset_fluid_provider_state() -> None:
    """Drop the cached instance. For tests, and for nothing else."""
    global _PROVIDER
    _PROVIDER = None


def fluid_options() -> tuple[FluidOption, ...]:
    """The fluids this build can evaluate, for a selector."""
    from rocketforge.physics.fluids import HYDROGEN, METHANE, OXYGEN

    return tuple(
        FluidOption(name=f.name, formula=f.formula, molar_mass=f.molar_mass,
                    label=f"{f.name.title()} ({f.formula})")
        for f in (OXYGEN, METHANE, HYDROGEN))


def fluid_named(name: str) -> Any:
    """The :class:`FluidDefinition` for a canonical name."""
    from rocketforge.physics.fluids import HYDROGEN, METHANE, OXYGEN

    table = {f.name: f for f in (OXYGEN, METHANE, HYDROGEN)}
    try:
        return table[str(name).upper()]
    except KeyError:
        raise KeyError(
            f"no fluid named {name!r}; this build evaluates "
            f"{', '.join(sorted(table))}") from None
