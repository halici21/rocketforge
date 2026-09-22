"""Solid propellant formulations: what is loaded into the case, by mass.

A separate package from :mod:`rocketforge.physics.thermochemistry` rather than a
module inside it, and that placement is enforced rather than stylistic. The
thermochemistry package is byte-frozen by ``freeze_thermochemistry_api_v1``, and
the freeze is checked two ways: every recorded file is re-hashed, *and* the
manifest is required to cover the package's whole directory. So a new module
placed in there breaks the contract even without touching a single frozen byte.

The split is honest on its own terms. A solid grain is not a variation on a
bipropellant chamber request -- it has no fuel stream, no oxidiser stream, and
no O/F -- so it was never going to share that package's vocabulary.

Deferred to R1.1 and deliberately absent: every performance quantity. No c*,
no Cf, no Isp, no expansion. This package describes what is in the chamber,
not what a nozzle does with it.
"""

from __future__ import annotations

from .formulation import (
    MASS_FRACTION_SUM_TOL,
    CustomReactant,
    MassFractionSumError,
    SolidFormulation,
    SolidFormulationEquilibriumRequest,
    SolidFormulationError,
    SolidIngredient,
)

__all__ = [
    "SolidFormulationError",
    "MassFractionSumError",
    "CustomReactant",
    "SolidIngredient",
    "SolidFormulation",
    "SolidFormulationEquilibriumRequest",
    "MASS_FRACTION_SUM_TOL",
]
