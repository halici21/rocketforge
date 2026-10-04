"""The reactants the Sutton Table 5-5 liquid combinations need.

G. P. Sutton and O. Biblarz, *Rocket Propulsion Elements*, 9th ed. (2017),
Table 5-5 compares fourteen liquid bipropellant combinations. The frozen
provider already defines LOX, liquid methane and liquid hydrogen; this module
defines the rest -- and only the ones the shipped database represents
**exactly**. It is not a catalogue: nothing outside Table 5-5 is here.

Every CEA identity below was verified against cea 3.3.4's ``thermo.lib``
(sha256 ``8e5df1cc...``) with ``cea.Reactant`` and a one-species
``cea.Mixture``; each element formula was read from that database record, and
each range and enthalpy behaviour is the provider's own answer:

    CEA name         formula in thermo.lib   range (K)           enthalpy
    F2(L)            F 2                     75.02 .. 95.02      assigned at 85.02 K
    N2O4(L)          N 2  O 4                288.15 .. 308.15    assigned at 298.15 K
    N2H4(L)          N 2  H 4                100 .. 800          temperature-dependent
    C2H8N2(L),UDMH   C 2  H 8  N 2           288.15 .. 308.15    assigned at 298.15 K
    CH6N2(L)         C 1  H 6  N 2           288.15 .. 308.15    assigned at 298.15 K
    RP-1             C 1  H 1.95             288.15 .. 308.15    assigned at 298.15 K
    H2O2(L)          H 2  O 2                272.74 .. 6000      temperature-dependent
    H2O(L)           H 2  O 1                (none declared)     temperature-dependent

``H2O(L)`` is not listed by ``cea.Reactant`` but is accepted by ``cea.Mixture``
and responds to temperature there, so no range is recorded for it rather than
one being invented. The ``N2H4(L)`` and ``H2O2(L)`` ranges are recorded as the
provider states them, wide as they are.

Two Table 5-5 entries are **mixtures**, built from those species with the
existing blend mechanism -- never as an invented species:

* "50 % UDMH / 50 % hydrazine" is Aerozine-50, **by mass**: the convention
  ``docs/engineering/09`` section 4.3 fixes for it.
* "Hydrogen peroxide (90 %)" is 90 % H2O2 and 10 % water **by mass**, the
  weight-percent convention in which HTP concentrations are stated.

Both bases are also what Table 5-5 itself supports: by mass, CEA reproduces
the table's chamber temperature and molar mass to 13 K / 0.0 for HTP-90/RP-1
(2773 K, 21.70 against 2760 K, 21.7) and to 1 K / 0.04 for NTO/Aerozine-50 at
O/F 1.62; read as mole fractions instead, both miss by 89 to 124 K.

Red fuming nitric acid is **not** here. See
``rocketforge.application.analysis.thermochemistry_presets`` for why.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from rocketforge.physics.thermochemistry import (
    Composition,
    CompositionBasis,
    Phase,
    PropellantDefinition,
    PropellantRole,
)

__all__ = [
    "LIQUID_FLUORINE",
    "NITROGEN_TETROXIDE",
    "HYDROGEN_PEROXIDE_90",
    "HYDRAZINE",
    "UDMH",
    "MMH",
    "RP1",
    "AEROZINE_50",
    "LIQUID_PROPELLANTS",
    "LIQUID_REACTANT_TEMPERATURE_RANGES",
]

_SOURCE = ("NASA CEA 3.3.4 reactant library (cea/data/thermo.lib); "
           "valid temperature range read from cea.Reactant")
_SUTTON = "Sutton & Biblarz, Rocket Propulsion Elements, 9th ed., Table 5-5"

#: Storable propellants are stated at 298.15 K, which is also where CEA fixes
#: the assigned enthalpy of every storable entry above that has one.
_STORABLE = 298.15

#: Ranges CEA declares for these reactants, K, read from ``cea.Reactant``.
#: Checked before a solve so a stream outside one is refused with the range
#: named, as the frozen provider does for its own cryogens.
LIQUID_REACTANT_TEMPERATURE_RANGES: Mapping[str, tuple[float, float]] = MappingProxyType({
    "F2(L)": (75.020, 95.020),
    "N2O4(L)": (288.150, 308.150),
    "N2H4(L)": (100.000, 800.000),
    "C2H8N2(L),UDMH": (288.150, 308.150),
    "CH6N2(L)": (288.150, 308.150),
    "RP-1": (288.150, 308.150),
    "H2O2(L)": (272.740, 6000.000),
})

#: Liquid fluorine. CEA's assigned-enthalpy condition, its normal boiling point.
LIQUID_FLUORINE = PropellantDefinition(
    name="LF2",
    role=PropellantRole.OXIDISER,
    composition=Composition.pure("F2"),
    reference_temperature=85.02,
    reference_phase=Phase.LIQUID,
    provider_names={"cea": "F2(L)"},
    source=_SOURCE,
)

#: Nitrogen tetroxide, the pure substance -- not MON, which carries NO.
NITROGEN_TETROXIDE = PropellantDefinition(
    name="NTO",
    role=PropellantRole.OXIDISER,
    composition=Composition.pure("N2O4"),
    reference_temperature=_STORABLE,
    reference_phase=Phase.LIQUID,
    provider_names={"cea": "N2O4(L)"},
    source=_SOURCE,
)

#: 90 % hydrogen peroxide: 90 % H2O2 and 10 % water by mass. A solution, so a
#: two-species blend of CEA's own liquid entries; its keys are CEA names, which
#: is the frozen provider's documented blend mechanism.
HYDROGEN_PEROXIDE_90 = PropellantDefinition(
    name="HTP-90",
    role=PropellantRole.OXIDISER,
    composition=Composition.from_fractions(
        {"H2O2(L)": 0.90, "H2O(L)": 0.10}, CompositionBasis.MASS_FRACTION),
    reference_temperature=_STORABLE,
    reference_phase=Phase.LIQUID,
    source=f"{_SOURCE}; 90 % H2O2 / 10 % H2O by mass ({_SUTTON})",
)

#: Anhydrous hydrazine.
HYDRAZINE = PropellantDefinition(
    name="N2H4",
    role=PropellantRole.FUEL,
    composition=Composition.pure("N2H4"),
    reference_temperature=_STORABLE,
    reference_phase=Phase.LIQUID,
    provider_names={"cea": "N2H4(L)"},
    source=_SOURCE,
)

#: Unsymmetrical dimethylhydrazine, (CH3)2NNH2.
UDMH = PropellantDefinition(
    name="UDMH",
    role=PropellantRole.FUEL,
    composition=Composition.pure("C2H8N2"),
    reference_temperature=_STORABLE,
    reference_phase=Phase.LIQUID,
    provider_names={"cea": "C2H8N2(L),UDMH"},
    source=_SOURCE,
)

#: Monomethylhydrazine, CH3NHNH2: CEA's ``CH6N2(L)``.
MMH = PropellantDefinition(
    name="MMH",
    role=PropellantRole.FUEL,
    composition=Composition.pure("CH6N2"),
    reference_temperature=_STORABLE,
    reference_phase=Phase.LIQUID,
    provider_names={"cea": "CH6N2(L)"},
    source=_SOURCE,
)

#: RP-1, CEA's pseudo-species CH1.95. A surrogate, so its definition is named.
RP1 = PropellantDefinition(
    name="RP-1",
    role=PropellantRole.FUEL,
    composition=Composition.pure("RP-1"),
    reference_temperature=_STORABLE,
    reference_phase=Phase.LIQUID,
    provider_names={"cea": "RP-1"},
    is_surrogate=True,
    source=f"{_SOURCE}; CEA's own RP-1 pseudo-species, C 1.00 H 1.95",
)

#: Aerozine-50: 50 % UDMH and 50 % hydrazine by mass.
AEROZINE_50 = PropellantDefinition(
    name="A-50",
    role=PropellantRole.FUEL,
    composition=Composition.from_fractions(
        {"C2H8N2(L),UDMH": 0.50, "N2H4(L)": 0.50},
        CompositionBasis.MASS_FRACTION),
    reference_temperature=_STORABLE,
    reference_phase=Phase.LIQUID,
    source=f"{_SOURCE}; Aerozine-50, 50 % UDMH / 50 % N2H4 by mass ({_SUTTON})",
)

#: The LIQ-1 reactants, keyed by RocketForge name, in display order.
LIQUID_PROPELLANTS: Mapping[str, PropellantDefinition] = MappingProxyType({
    p.name: p for p in (LIQUID_FLUORINE, NITROGEN_TETROXIDE, HYDROGEN_PEROXIDE_90,
                        HYDRAZINE, UDMH, MMH, RP1, AEROZINE_50)
})
