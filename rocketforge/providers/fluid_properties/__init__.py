"""Fluid-property provider implementations.

``physics.fluids`` declares the boundary; this package implements it. Nothing
here is imported by ``physics``, and nothing here imports ``application``.

Two providers, and the difference between them is the point:

* :class:`~.constant.ConstantPropertyProvider` -- in-tree, dependency-free,
  fixed values. Proves the boundary and gives the tests something deterministic
  to run against. Declares no temperature or pressure dependence.
* :class:`~.coolprop.CoolPropFluidProvider` -- the real equation-of-state path.
  Optional at import time: the base environment runs without it.

The real provider is **not** imported here. Importing this package must not
require CoolProp to be installed, so the adapter is reached through
:func:`coolprop_provider`, which raises a named error when the library is
absent rather than failing at import.
"""

from __future__ import annotations

from .constant import (
    CONSTANT_PROPERTY_APPROXIMATION,
    UNRESTRICTED_TEST_MODEL,
    ConstantPropertyDefinition,
    ConstantPropertyProvider,
)

__all__ = [
    "ConstantPropertyDefinition",
    "ConstantPropertyProvider",
    "CONSTANT_PROPERTY_APPROXIMATION",
    "UNRESTRICTED_TEST_MODEL",
    "coolprop_provider",
    "coolprop_is_available",
]


def coolprop_is_available() -> bool:
    """Whether the CoolProp adapter can be constructed in this environment.

    A question, not an attempt: the interface asks this before offering the
    high-fidelity provider, so a missing optional dependency is presented as a
    choice that is unavailable rather than as an error mid-calculation.
    """
    from .coolprop import coolprop_is_available as _available

    return _available()


def coolprop_provider(**kwargs):
    """Build the CoolProp-backed provider.

    Raises
    ------
    FluidProviderUnavailableError
        When CoolProp is not installed. Named, so the caller can distinguish a
        deployment fact from an equation of state that diverged.
    """
    from .coolprop import CoolPropFluidProvider

    return CoolPropFluidProvider(**kwargs)
