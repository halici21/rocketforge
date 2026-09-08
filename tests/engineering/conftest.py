"""Fixtures for the engineering layer.

The important one is :func:`chamber_state`: a **provider-independent**
``ChamberGas``, built from nothing but the domain records. It exists so the
whole Phase 5E chain -- reduction, c*, nozzle coupling, thrust, Isp -- can be
exercised on a machine with no chemistry library installed. That is not a
convenience; it is the property being tested.

Its numbers are the shape of a real LOX/CH4 chamber so the results are
recognisable, but nothing here is a validated chemistry result and no artifact
may present one as such.
"""

from __future__ import annotations

import pytest

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.physics.thermochemistry import (
    ChamberGas,
    ChemistryMode,
    Composition,
    CompositionBasis,
    EquilibriumConstraint,
    ThermochemistryProvenance,
)

#: Mean molar mass [kg/mol]. R follows from it, so the P4 identity closes by
#: construction rather than by a number chosen to pass.
FIXTURE_MOLAR_MASS = 0.0217700886

#: The gas constant every fixture uses. Derived, never typed in twice.
FIXTURE_GAS_CONSTANT = UNIVERSAL_GAS_CONSTANT / FIXTURE_MOLAR_MASS


def _make_chamber_state(
    *,
    temperature: float = 3598.2854,
    gamma: float = 1.1325915,
    molar_mass: float = FIXTURE_MOLAR_MASS,
    gas_constant: float | None = None,
    gamma_frozen: float | None = 1.1955675,
    pressure: float | None = 10.0e6,
    condensed_mass_fraction: float | None = 6.24e-08,
    chemistry_mode: ChemistryMode | None = ChemistryMode.EQUILIBRIUM,
    provider_id: str = "fixture:phase5e",
) -> ChamberGas:
    """A chamber state built from the domain alone, with one knob per rule.

    Every parameter exists because some precondition or mutation proof needs to
    move exactly one thing and leave the rest valid.
    """
    provenance = ThermochemistryProvenance(
        provider_id=provider_id,
        chemistry_mode=chemistry_mode,
        equilibrium_constraint=EquilibriumConstraint.HP,
    )
    return ChamberGas(
        temperature=temperature,
        gamma=gamma,
        gamma_equilibrium=gamma,
        gamma_frozen=gamma_frozen,
        gas_constant=(UNIVERSAL_GAS_CONSTANT / molar_mass
                      if gas_constant is None else gas_constant),
        molar_mass=molar_mass,
        composition=Composition.from_fractions(
            {"H2O": 0.50, "CO": 0.20, "CO2": 0.20, "H2": 0.10},
            CompositionBasis.MOLE_FRACTION),
        pressure=pressure,
        condensed_mass_fraction=condensed_mass_fraction,
        provenance=provenance,
    )


@pytest.fixture()
def make_chamber_state():
    """The factory itself, as a fixture.

    Handed over rather than imported: ``tests/`` has no ``__init__.py``, so a
    relative import from a conftest fails and a plain ``import conftest``
    resolves to whichever conftest pytest loaded first -- a trap this project
    has already been caught by once.
    """
    return _make_chamber_state


@pytest.fixture()
def chamber_state() -> ChamberGas:
    """The canonical provider-independent chamber state."""
    return _make_chamber_state()


@pytest.fixture()
def reduced_gas(chamber_state):
    """The canonical state reduced on the frozen basis.

    Frozen rather than equilibrium because that is the reduction this model
    actually performs: composition is held fixed from chamber to exit, and
    cp/cv is the exponent of a constant-composition isentropic process. It is
    also what makes the comparison against a provider's frozen-at-chamber
    expansion like-for-like.
    """
    from rocketforge.engineering.chamber import ChamberGammaBasis, reduce_chamber_gas
    from rocketforge.physics.thermochemistry import GammaStrategy

    solution = reduce_chamber_gas(chamber_state, GammaStrategy.CHAMBER,
                                  ChamberGammaBasis.FROZEN)
    assert solution.value is not None, solution.diagnostics
    return solution.value
