"""NASA CEA: the Sutton Table 5-5 liquid reactants (LIQ-1).

A sibling package to :mod:`rocketforge.providers.cea`, for the reason
:mod:`rocketforge.providers.cea_solid` is one: ``freeze_cea_provider_v1_1``
byte-freezes every module of the provider package and requires its manifest to
cover the whole directory, so new reactants cannot be added inside it.

Nothing here is a second thermochemistry pipeline. The reactants are ordinary
``PropellantDefinition`` records; :class:`CEALiquidProvider` is the frozen
provider with nitrogen- and fluorine-bearing product sets and their formulae
added in front of it, and every step of the solve is the frozen provider's.
"""

from __future__ import annotations

from .propellants import (
    AEROZINE_50,
    HYDRAZINE,
    HYDROGEN_PEROXIDE_90,
    LIQUID_FLUORINE,
    LIQUID_PROPELLANTS,
    LIQUID_REACTANT_TEMPERATURE_RANGES,
    MMH,
    NITROGEN_TETROXIDE,
    RP1,
    UDMH,
)
from .provider import (
    CEALiquidProvider,
    check_liquid_reactant_temperatures,
    check_product_coverage,
    liquid_product_species,
    reactant_cea_names,
)
from .species import (
    CHON_PRODUCT_SPECIES,
    FORMULAS,
    HF_PRODUCT_SPECIES,
    HNF_PRODUCT_SPECIES,
    HON_PRODUCT_SPECIES,
    LIQUID_FORMULAS,
    PRODUCT_SPECIES_BY_ELEMENTS,
    build_liquid_species_table,
    liquid_phase_of_cea_name,
)

__all__ = [
    "CEALiquidProvider",
    "reactant_cea_names",
    "liquid_product_species",
    "check_liquid_reactant_temperatures",
    "check_product_coverage",
    "LIQUID_PROPELLANTS",
    "LIQUID_REACTANT_TEMPERATURE_RANGES",
    "LIQUID_FLUORINE",
    "NITROGEN_TETROXIDE",
    "HYDROGEN_PEROXIDE_90",
    "HYDRAZINE",
    "UDMH",
    "MMH",
    "RP1",
    "AEROZINE_50",
    "LIQUID_FORMULAS",
    "FORMULAS",
    "HON_PRODUCT_SPECIES",
    "CHON_PRODUCT_SPECIES",
    "HF_PRODUCT_SPECIES",
    "HNF_PRODUCT_SPECIES",
    "PRODUCT_SPECIES_BY_ELEMENTS",
    "liquid_phase_of_cea_name",
    "build_liquid_species_table",
]
