"""Fluid-property errors.

Deliberately few, and derived from :mod:`rocketforge.core.errors` so that
``except RocketForgeError`` still catches the whole project. The governing
policy is Phase 4A's and is unchanged here:

    Raise for invalid input; report for unattainable physics.

A request with a negative pressure is a malformed argument and raises. A state
the provider has no data for is a :class:`~rocketforge.core.result.Solution`
with ``NO_SOLUTION`` and a diagnostic naming what was missing -- because "your
oxygen is outside the equation of state's range" is an answer, not a bug.
"""

from __future__ import annotations

from rocketforge.core.errors import DomainError, InputError, RocketForgeError

__all__ = [
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


class FluidError(RocketForgeError):
    """Base class for every error this package raises deliberately."""


class FluidIdentityError(FluidError, InputError):
    """A fluid identity record is malformed."""


class FluidRequestError(FluidError, InputError):
    """A fluid state request is malformed."""


class FluidStateError(FluidError, DomainError):
    """A fluid state record is internally inconsistent."""


class FluidPhaseError(FluidError, DomainError):
    """A caller required one phase and the state is another.

    Its own class because the failure is specific and the consequence is large:
    evaluating a liquid correlation on a gas, or averaging across a two-phase
    state, produces a number rather than an error.
    """


class FluidProviderError(FluidError):
    """A fluid-property provider failed for a reason of its own."""


class FluidProviderUnavailableError(FluidProviderError):
    """The provider's backing library or data is not installed.

    Distinct from :class:`FluidProviderError`: "not installed" is a deployment
    fact the interface can act on, and "the equation of state diverged" is not.
    """


class UnsupportedFluidPropertyError(FluidProviderError):
    """A property was asked of a provider that does not declare it.

    Raised immediately and always. A provider that cannot supply a viscosity
    must never return zero, and must never quietly return a property it does
    have instead.
    """


class UnsupportedFluidError(FluidProviderError):
    """The provider has no data for this fluid at all."""
