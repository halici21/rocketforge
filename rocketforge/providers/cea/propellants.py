"""The minimal production propellant set Phase 5C validates.

**Four definitions, not a catalogue.** Phase 5A deferred catalogue population
deliberately and Phase 5B shipped the schema rather than the data; Phase 5C
adds only what it actually validates end to end. A broad propellant library is
a data-curation effort with its own provenance requirements, not a side effect
of writing an adapter (5C brief §209).

Every entry records the CEA identity it maps to and the valid temperature range
CEA states for it, because "LOX" is not a scientific identity: ``O2`` and
``O2(L)`` carry different thermochemical reference data, and choosing between
them is worth 74.9 K of chamber temperature.

The valid temperature ranges below were read from the provider itself, through
``cea.Reactant(name).get_valid_temperature_range()``, in Phase 5B-0:

    O2(L)    80.170 .. 100.170 K
    CH4(L)  101.643 .. 121.643 K
    H2(L)    10.270 ..  30.270 K
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from rocketforge.physics.thermochemistry import (
    Composition,
    Phase,
    PropellantDefinition,
    PropellantRole,
)

__all__ = [
    "LOX",
    "LIQUID_METHANE",
    "LIQUID_HYDROGEN",
    "GASEOUS_OXYGEN",
    "GASEOUS_METHANE",
    "PRODUCTION_PROPELLANTS",
    "CEA_REACTANT_TEMPERATURE_RANGES",
]

_SOURCE = ("NASA CEA 3.3.4 reactant library (cea/data/thermo.lib); "
           "valid temperature range read from cea.Reactant")

#: Temperature ranges CEA declares for its liquid reactants, K. Used to refuse
#: a stream outside the range with a message naming it, rather than letting CEA
#: extrapolate or fail obscurely.
CEA_REACTANT_TEMPERATURE_RANGES: Mapping[str, tuple[float, float]] = MappingProxyType({
    "O2(L)": (80.170, 100.170),
    "CH4(L)": (101.643, 121.643),
    "H2(L)": (10.270, 30.270),
})

#: Liquid oxygen. Reference condition is its normal boiling point.
LOX = PropellantDefinition(
    name="LOX",
    role=PropellantRole.OXIDISER,
    composition=Composition.pure("O2"),
    reference_temperature=90.17,
    reference_phase=Phase.LIQUID,
    density_hint=1141.0,
    provider_names={"cea": "O2(L)"},
    source=_SOURCE,
)

#: Liquid methane. Reference condition is its normal boiling point.
LIQUID_METHANE = PropellantDefinition(
    name="LCH4",
    role=PropellantRole.FUEL,
    composition=Composition.pure("CH4"),
    reference_temperature=111.643,
    reference_phase=Phase.LIQUID,
    density_hint=422.6,
    provider_names={"cea": "CH4(L)"},
    source=_SOURCE,
)

#: Liquid hydrogen. Reference condition is its normal boiling point.
LIQUID_HYDROGEN = PropellantDefinition(
    name="LH2",
    role=PropellantRole.FUEL,
    composition=Composition.pure("H2"),
    reference_temperature=20.27,
    reference_phase=Phase.LIQUID,
    density_hint=70.85,
    provider_names={"cea": "H2(L)"},
    source=_SOURCE,
)

#: Gaseous oxygen at the standard reference temperature. Present because the
#: gaseous/liquid pair is what makes the cryogenic sensitivity test meaningful.
GASEOUS_OXYGEN = PropellantDefinition(
    name="GOX",
    role=PropellantRole.OXIDISER,
    composition=Composition.pure("O2"),
    reference_temperature=298.15,
    reference_phase=Phase.GAS,
    provider_names={"cea": "O2"},
    source=_SOURCE,
)

#: Gaseous methane at the standard reference temperature.
GASEOUS_METHANE = PropellantDefinition(
    name="GCH4",
    role=PropellantRole.FUEL,
    composition=Composition.pure("CH4"),
    reference_temperature=298.15,
    reference_phase=Phase.GAS,
    provider_names={"cea": "CH4"},
    source=_SOURCE,
)

#: Everything this phase validates, keyed by RocketForge name.
PRODUCTION_PROPELLANTS: Mapping[str, PropellantDefinition] = MappingProxyType({
    p.name: p for p in (LOX, LIQUID_METHANE, LIQUID_HYDROGEN,
                        GASEOUS_OXYGEN, GASEOUS_METHANE)
})
