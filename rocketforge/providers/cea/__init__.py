"""NASA CEA v3 thermochemistry provider.

The production chemical-equilibrium provider (ADR-31). Implements the
``ThermochemistryProvider`` protocol declared in
``rocketforge.physics.thermochemistry``; nothing in ``physics`` imports this
package, and nothing here imports Qt, ``engineering``, ``engine`` or
``application``.

**Importing this package does not import CEA.** The chemistry library is loaded
lazily, on first use, so provider discovery and availability reporting work on
a machine where nothing is installed::

    from rocketforge.providers.cea import CEAThermochemistryProvider, check_availability

    status = check_availability()
    if status.is_usable:
        provider = CEAThermochemistryProvider()
        solution = provider.solve_chamber(request)

Dependency: ``cea==3.3.4``, from ``requirements-thermochemistry.txt``. It is
deliberately not in ``requirements.txt`` -- the base library and the whole
provider-independent domain run and pass their tests without it. The official
RocketForge desktop executable is built from an environment that has it, so an
end user of the packaged application never runs pip.

What this provider returns is a chamber **thermochemical state**. NASA CEA can
also return c*, Cf and Isp, and this adapter deliberately does not put them on
``ChamberGas``: rocket performance belongs to ``engineering.nozzle`` (ADR-15).
Those native values remain reachable for validation and future cross-checking
through :mod:`rocketforge.providers.cea.oracle`.
"""

from __future__ import annotations

from .availability import (
    SUPPORTED_CEA_VERSIONS,
    CEAAvailability,
    CEAStatus,
    check_availability,
)
from .errors import CEAMappingError, CEAProviderError, CEASolveError
from .mapping import CEAChamberInput, CEARawChamberResult, build_chamber_input
from .naming import CEA_MAX_NAME_LENGTH, PROVIDER_ID
from .propellants import (
    GASEOUS_METHANE,
    GASEOUS_OXYGEN,
    LIQUID_HYDROGEN,
    LIQUID_METHANE,
    LOX,
    PRODUCTION_PROPELLANTS,
)
from .provider import CEA_CAPABILITIES, PROVIDER_VERSION, CEAThermochemistryProvider
from .resources import CEAResources, discover_resources
from .species import CHO_PRODUCT_SPECIES, HO_PRODUCT_SPECIES

__all__ = [
    # the provider
    "CEAThermochemistryProvider",
    "CEA_CAPABILITIES",
    "PROVIDER_ID",
    "PROVIDER_VERSION",
    # availability
    "CEAStatus",
    "CEAAvailability",
    "check_availability",
    "SUPPORTED_CEA_VERSIONS",
    # resources
    "CEAResources",
    "discover_resources",
    # mapping, exposed for tests and for inspection
    "CEAChamberInput",
    "CEARawChamberResult",
    "build_chamber_input",
    "CEA_MAX_NAME_LENGTH",
    # curated data
    "CHO_PRODUCT_SPECIES",
    "HO_PRODUCT_SPECIES",
    "LOX",
    "LIQUID_METHANE",
    "LIQUID_HYDROGEN",
    "GASEOUS_OXYGEN",
    "GASEOUS_METHANE",
    "PRODUCTION_PROPELLANTS",
    # errors
    "CEAProviderError",
    "CEAMappingError",
    "CEASolveError",
]
