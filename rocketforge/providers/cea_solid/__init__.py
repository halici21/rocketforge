"""NASA CEA: chamber equilibrium for a solid propellant formulation.

A sibling package to :mod:`rocketforge.providers.cea` rather than a module
inside it, for the same enforced reason its physics counterpart sits outside
the thermochemistry package: ``freeze_cea_provider_v1_1`` is checked both by
re-hashing every recorded file and by requiring the manifest to cover the whole
``rocketforge/providers/cea`` directory. A new module in there breaks the
contract on its own, before any frozen byte is touched.

Everything reusable from the frozen provider **is** reused, by import: the unit
converters, the raw-result snapshot type, the condensed-mass computation, the
molar-mass lookup, the phase classifier and the exception translator. See
``docs/engineering/design/SOLID_PROPELLANT_R1_ARCHITECTURE.md`` for what could
not be reused and why.
"""

from __future__ import annotations

from .formulations import (
    RP1311_EXAMPLE5,
    RP1311_EXAMPLE5_BINDER,
    RP1311_EXAMPLE5_OMIT,
    RP1311_EXAMPLE5_PRESSURES_BAR,
)
from .provider import (
    SolidChamberInput,
    build_solid_chamber_input,
    build_solid_species_table,
    check_condensed_count,
    library_species_available,
    solid_assigned_enthalpy_diagnostics,
    solid_phase_of_cea_name,
    solid_reactant_conditions,
    solve_solid_chamber,
    solve_solid_chamber_raw,
    to_solid_chamber_gas,
)

__all__ = [
    "SolidChamberInput",
    "solid_phase_of_cea_name",
    "build_solid_species_table",
    "build_solid_chamber_input",
    "solve_solid_chamber_raw",
    "to_solid_chamber_gas",
    "solve_solid_chamber",
    "solid_reactant_conditions",
    "solid_assigned_enthalpy_diagnostics",
    "check_condensed_count",
    "library_species_available",
    "RP1311_EXAMPLE5",
    "RP1311_EXAMPLE5_BINDER",
    "RP1311_EXAMPLE5_OMIT",
    "RP1311_EXAMPLE5_PRESSURES_BAR",
]
