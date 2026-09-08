"""Fluid properties: what a substance is doing at a temperature and a pressure.

``06_future_module_dependency_map.md`` §8 step 1, and the only remaining
unimplemented L1 physics module. It owns the fluid-property *domain*: an
identity, a state request, a state, a phase, a capability model, provenance,
and the provider protocol. It owns no property correlation of its own, no
device equation, and no provider.

**What this package deliberately does not have**

* No equation of state. The models live behind ``FluidPropertyProvider``.
* No default pressure. Liquid oxygen at 95 K is a liquid at 3 bar and a gas at
  1 atm; a package that supplied a pressure would be choosing which.
* No ``UNKNOWN`` phase member. Unknown is ``None``, and ``None`` is never read
  as GAS.
* No device correlation -- no line, valve, orifice, injector, pump or channel.
  Those are the next roadmap step and are not started here.
* No absolute-enthalpy claim. Enthalpy's zero is a provider convention, so it
  is consumed only as a difference between two states of one fluid from one
  provider. See ``REACTANT_ENTHALPY_COUPLING_CONTRACT.md``.

Imports ``rocketforge.core`` and nothing else in the project. No Qt, no
provider, no application, no chemistry library.
"""

from __future__ import annotations

from .errors import (
    FluidError,
    FluidIdentityError,
    FluidPhaseError,
    FluidProviderError,
    FluidProviderUnavailableError,
    FluidRequestError,
    FluidStateError,
    UnsupportedFluidError,
    UnsupportedFluidPropertyError,
)
from .identity import HYDROGEN, METHANE, OXYGEN, FluidDefinition
from .protocols import (
    FluidPropertyCapabilities,
    FluidPropertyCapability,
    FluidPropertyProvider,
    capability_for,
)
from .provenance import FluidPropertyProvenance
from .requests import FluidStateRequest
from .states import FluidState
from .types import FluidPhase, FluidProperty, PropertyStatus

__all__ = [
    # identity
    "FluidDefinition",
    "OXYGEN",
    "METHANE",
    "HYDROGEN",
    # vocabulary
    "FluidPhase",
    "FluidProperty",
    "PropertyStatus",
    # records
    "FluidStateRequest",
    "FluidState",
    "FluidPropertyProvenance",
    # provider boundary
    "FluidPropertyProvider",
    "FluidPropertyCapabilities",
    "FluidPropertyCapability",
    "capability_for",
    # errors
    "FluidError",
    "FluidIdentityError",
    "FluidRequestError",
    "FluidStateError",
    "FluidPhaseError",
    "FluidProviderError",
    "FluidProviderUnavailableError",
    "UnsupportedFluidPropertyError",
    "UnsupportedFluidError",
]
