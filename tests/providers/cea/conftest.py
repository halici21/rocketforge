"""Fixtures for the NASA CEA provider tests.

Two kinds of test live here and the split is deliberate:

* tests that need **no provider** -- request mapping, unit conversion, naming,
  availability reporting. These run in the base environment, which has no
  chemistry library, and they are where the O/F orientation and the
  temperature sourcing are actually pinned down.
* tests that need the **real library** -- everything from a live solve onward.
  These skip with an explicit reason when CEA is absent, following the SciPy
  oracle precedent already in this repository.

A skip is never allowed to stand in for a pass: the CEA-enabled suite is a
separate, blocking gate, and the Phase 5C report counts the two environments
separately.
"""

from __future__ import annotations

import pytest

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    MixtureRatio,
    Phase,
    PropellantStream,
)
from rocketforge.providers.cea import (
    LIQUID_METHANE,
    LOX,
    CEAThermochemistryProvider,
    check_availability,
)

#: Whether the live tests can run. Each test module recomputes this for its own
#: ``skipif`` marker, because the tests tree has no ``__init__.py`` and so a
#: module cannot import a name from conftest. The check is cheap.
CEA_AVAILABILITY = check_availability()
CEA_PRESENT = CEA_AVAILABILITY.is_usable


@pytest.fixture(scope="session")
def provider() -> CEAThermochemistryProvider:
    """One provider for the session.

    Reused deliberately: reuse is the production pattern -- the module is
    imported once and the species tables are cached -- so testing against a
    fresh instance every time would test something the application does not do.
    """
    if not CEA_PRESENT:
        pytest.skip("NASA CEA provider unavailable")
    return CEAThermochemistryProvider()


@pytest.fixture
def lox_stream() -> PropellantStream:
    """Liquid oxygen at its normal boiling point."""
    return PropellantStream(LOX, 90.17, pressure=3.0e6, phase=Phase.LIQUID)


@pytest.fixture
def methane_stream() -> PropellantStream:
    """Liquid methane at its normal boiling point."""
    return PropellantStream(LIQUID_METHANE, 111.643, pressure=3.0e6,
                            phase=Phase.LIQUID)


@pytest.fixture
def lox_methane_request(methane_stream, lox_stream) -> ChamberEquilibriumRequest:
    """The canonical Phase 5C production case.

    LOX / liquid methane, O/F 3.4 by mass, 10 MPa chamber pressure, both
    reactants at their normal boiling points, HP equilibrium. Every condition
    is explicit; nothing defaults to 298.15 K.
    """
    return ChamberEquilibriumRequest(
        fuel=methane_stream,
        oxidiser=lox_stream,
        oxidiser_fuel_ratio=MixtureRatio(3.4),
        chamber_pressure=10.0e6,
    )
