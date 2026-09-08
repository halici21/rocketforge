"""Layer 1 -- provider-independent thermochemistry.

The domain language through which every future thermochemistry provider talks
to RocketForge. It knows what a species is, what a phase is, what a composition
is, what a propellant is, what O/F means, what a chamber state contains and what
a provider is allowed to return.

It solves no chemistry. There is no equilibrium solver here and there will not
be one: the physics layer owns the *contract*, a provider owns the *solution*
(ADR-19). It computes no performance: c*, Cf, Isp and thrust belong to
``engineering.nozzle`` (ADR-15).

**Status: PROVISIONAL.** This is a Phase 5B public surface, not a frozen v1. It
is expected to change when the first provider adapter is written in Phase 5C.
Compare ``docs/engineering/COMPRESSIBLE_FLOW_API_V1.md``, which *is* frozen;
this one is documented in ``THERMOCHEMISTRY_CORE_API_DRAFT.md``.

Import rules this package obeys, enforced by ``tests/test_architecture.py``:

* it imports ``rocketforge.core`` and the standard library, nothing else from
  the project;
* it never imports ``physics.compressible`` -- the handshake between them is a
  data contract performed one layer up, not a call (``08`` section 5);
* it never imports ``providers``, ``engineering``, ``engine`` or
  ``application``;
* it never imports Qt, and never imports ``cea``, ``cantera``, ``rocketcea``,
  ``CoolProp`` or SciPy.

Units, without exception::

    temperature            K
    pressure               Pa
    density                kg/m3
    molar mass             kg/mol
    specific gas constant  J/(kg K)
    cp, cv                 J/(kg K)
    enthalpy               J/kg      (specific)  or  J/mol  (molar, on Species)
    entropy                J/(kg K)  (specific)
    velocity, sound speed  m/s
    mass flow              kg/s

Canonical conventions:

* composition is stored as **mole fractions**, and every set of fractions
  carries its basis explicitly;
* **O/F is oxidiser mass divided by fuel mass**, always;
* every enthalpy sits on one datum: elements in their reference states at
  298.15 K and 1 bar.

A worked, provider-free example::

    from rocketforge.physics.thermochemistry import (
        Composition, CompositionBasis, ElementalComposition, Phase, Species,
    )

    ch4 = Species("CH4", Phase.GAS, 16.04246e-3,
                  ElementalComposition.from_mapping({"C": 1.0, "H": 4.0}))
    o2 = Species("O2", Phase.GAS, 31.9988e-3,
                 ElementalComposition.from_mapping({"O": 2.0}))
    table = {"CH4": ch4, "O2": o2}

    mixture = Composition.from_fractions(
        {"CH4": 0.5, "O2": 0.5}, CompositionBasis.MOLE_FRACTION)
    mixture.mean_molar_mass(table)       # kg/mol
    mixture.specific_gas_constant(table) # J/(kg K)
    mixture.elemental(table)             # atoms per mole of mixture

No provider is involved in any of that, and none is installed.
"""

from __future__ import annotations

from .composition import (
    Composition,
    ElementBalanceReport,
    ElementalInventory,
    ElementalInventoryBasis,
    compare_elemental_inventories,
    elemental_inventory,
    mass_to_mole_fractions,
    mean_molar_mass,
    mole_to_mass_fractions,
    specific_gas_constant,
)
from .errors import (
    CompositionBasisError,
    CompositionError,
    CompositionSumError,
    ElementalCompositionError,
    MixtureRatioError,
    PropellantError,
    PropellantRoleError,
    ProviderDomainError,
    ProviderError,
    ProviderUnavailableError,
    SpeciesError,
    StateConsistencyError,
    ThermochemistryError,
    UnknownSpeciesError,
    UnsupportedCapabilityError,
)
from .propellants import (
    MixtureRatio,
    PropellantDefinition,
    PropellantPair,
    PropellantPairReferenceCase,
    PropellantStream,
    mixture_ratio_from_streams,
)
from .protocols import (
    ProviderCapabilities,
    ProviderCapability,
    ThermochemistryProvider,
)
from .provenance import ThermochemistryProvenance
from .requests import ChamberEquilibriumRequest, ExpansionRequest
from .serialization import to_jsonable
from .species import (
    STANDARD_STATE_PRESSURE,
    STANDARD_STATE_TEMPERATURE,
    ElementalComposition,
    PolynomialForm,
    Species,
    ThermoPolynomial,
)
from .states import ChamberGas, GasStation
from .tolerances import DEFAULT_THERMO_TOLERANCES, ThermochemistryTolerances
from .types import (
    ChemistryMode,
    CompositionBasis,
    EquilibriumConstraint,
    ExpansionMode,
    FreezeLocation,
    GammaStrategy,
    MixtureRatioBasis,
    Phase,
    PropellantRole,
)
from .validation import (
    IdentityCheck,
    ValidationReport,
    check_composition_round_trip,
    check_composition_sum,
    check_cp_cv_relation,
    check_element_balance,
    check_gamma_definition,
    check_gas_constant,
    check_ideal_gas,
    check_mean_molar_mass_paths,
    check_provenance_completeness,
    validate_chamber_gas,
    validate_gas_station,
)

__all__ = [
    # enums
    "Phase",
    "CompositionBasis",
    "PropellantRole",
    "MixtureRatioBasis",
    "ChemistryMode",
    "ExpansionMode",
    "FreezeLocation",
    "EquilibriumConstraint",
    "GammaStrategy",
    # species
    "ElementalComposition",
    "PolynomialForm",
    "ThermoPolynomial",
    "Species",
    "STANDARD_STATE_TEMPERATURE",
    "STANDARD_STATE_PRESSURE",
    # composition
    "Composition",
    "ElementalInventoryBasis",
    "ElementalInventory",
    "ElementBalanceReport",
    "mole_to_mass_fractions",
    "mass_to_mole_fractions",
    "mean_molar_mass",
    "specific_gas_constant",
    "elemental_inventory",
    "compare_elemental_inventories",
    # propellants
    "PropellantDefinition",
    "PropellantStream",
    "MixtureRatio",
    "PropellantPair",
    "PropellantPairReferenceCase",
    "mixture_ratio_from_streams",
    # requests
    "ChamberEquilibriumRequest",
    "ExpansionRequest",
    # states
    "ChamberGas",
    "GasStation",
    # provider contract
    "ThermochemistryProvider",
    "ProviderCapability",
    "ProviderCapabilities",
    "ThermochemistryProvenance",
    # validation
    "IdentityCheck",
    "ValidationReport",
    "check_composition_sum",
    "check_composition_round_trip",
    "check_mean_molar_mass_paths",
    "check_gas_constant",
    "check_cp_cv_relation",
    "check_gamma_definition",
    "check_ideal_gas",
    "check_element_balance",
    "check_provenance_completeness",
    "validate_chamber_gas",
    "validate_gas_station",
    # tolerances
    "ThermochemistryTolerances",
    "DEFAULT_THERMO_TOLERANCES",
    # serialization
    "to_jsonable",
    # errors
    "ThermochemistryError",
    "SpeciesError",
    "UnknownSpeciesError",
    "ElementalCompositionError",
    "CompositionError",
    "CompositionBasisError",
    "CompositionSumError",
    "PropellantError",
    "PropellantRoleError",
    "MixtureRatioError",
    "StateConsistencyError",
    "ProviderError",
    "ProviderUnavailableError",
    "ProviderDomainError",
    "UnsupportedCapabilityError",
]
