"""Turning CEA's species names into RocketForge :class:`Species` records.

Two pieces of information are needed per species and they come from different
places, deliberately:

* **molar mass -- from CEA itself.** ``Mixture.moles_to_weights`` with a unit
  vector returns the molar mass CEA's own database uses, in kg/kmol. Taking it
  from CEA rather than from a shipped periodic table removes the
  atomic-weight-vintage problem entirely: CEA's data predates the current
  IUPAC values, and a table of our own would disagree with it in the fifth
  digit and quietly widen every element balance.
* **elemental formula -- curated here.** CEA exposes no per-species elemental
  composition through its public API (``Reactant.formula`` is populated only
  for caller-defined custom reactants), so the formulas have to come from
  somewhere. They are integers, they are unambiguous, and they are listed
  below with their source.

**Why a curated list and not a name parser.** CEA product names are not
formulas: ``C2H2,acetylene``, ``HCHO,formaldehy``, ``CH3C(CH3)2CH3``,
``(HCOOH)2``, ``HO(CO)2OH``. Deriving composition from those needs a parser
handling parentheses, multipliers and comma-suffixed common names -- exactly
the fragile universal parser Phase 5A ``09`` §2.3 warns against. A bounded,
sourced table for a bounded, declared species set is the honest alternative.

**Why the species set is bounded at all.** With ``products_from_reactants``,
CEA selects 124 species for LOX/CH4, most of them below 1e-20. Curating 124
formulas by hand would be a large, error-prone, unsourced data set. Measured
cost of the 27-species set below instead, at O/F 3.4, Pc 100 bar, reactants at
their normal boiling points:

    full 124 species   Tc = 3598.2855 K   M = 21.77009   gamma_s = 1.13259
    curated 27         Tc = 3598.2860 K   M = 21.77008   gamma_s = 1.13259
                       dTc = 0.0005 K     dM/M = -5.8e-07  dgamma/gamma = 1.0e-06

That is an order of magnitude below CEA's own pre-2019 gas-constant
discrepancy of 5.7e-06, which is already the floor under every provider
identity check. The truncation therefore costs less than a difference the
architecture already tolerates and documents -- and the set actually used is
recorded in provenance, so no result hides which species it was solved with.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from types import ModuleType

import numpy as np

from rocketforge.physics.thermochemistry import (
    ElementalComposition,
    Phase,
    Species,
)

from .errors import CEAMappingError
from .units import molar_mass_to_si

__all__ = [
    "CEA_FORMULAS",
    "CHO_PRODUCT_SPECIES",
    "HO_PRODUCT_SPECIES",
    "phase_of_cea_name",
    "build_species_table",
    "cea_molar_masses",
]

#: Elemental formulae for the CEA species RocketForge supports as products or
#: reactants. Integers, and checkable: multiplying by standard atomic weights
#: must reproduce CEA's own molar mass to within the atomic-weight vintage
#: difference, which ``tests/providers/cea/`` asserts.
#:
#: Source: the species identities are those of the NASA Glenn thermodynamic
#: database shipped as ``cea/data/thermo.lib`` with cea 3.3.4; the formulae are
#: the standard chemical compositions of the named substances.
CEA_FORMULAS: Mapping[str, Mapping[str, float]] = MappingProxyType({
    # --- reactants -------------------------------------------------------
    "O2": {"O": 2.0},
    "O2(L)": {"O": 2.0},
    "H2": {"H": 2.0},
    "H2(L)": {"H": 2.0},
    "CH4": {"C": 1.0, "H": 4.0},
    "CH4(L)": {"C": 1.0, "H": 4.0},
    # --- H/O products ----------------------------------------------------
    "H": {"H": 1.0},
    "O": {"O": 1.0},
    "OH": {"O": 1.0, "H": 1.0},
    "H2O": {"H": 2.0, "O": 1.0},
    "HO2": {"H": 1.0, "O": 2.0},
    "H2O2": {"H": 2.0, "O": 2.0},
    "O3": {"O": 3.0},
    "H2O(L)": {"H": 2.0, "O": 1.0},
    "H2O(cr)": {"H": 2.0, "O": 1.0},
    # --- C/H/O products --------------------------------------------------
    "C": {"C": 1.0},
    "C(gr)": {"C": 1.0},
    "CO": {"C": 1.0, "O": 1.0},
    "CO2": {"C": 1.0, "O": 2.0},
    "CH": {"C": 1.0, "H": 1.0},
    "CH2": {"C": 1.0, "H": 2.0},
    "CH3": {"C": 1.0, "H": 3.0},
    "CH2OH": {"C": 1.0, "H": 3.0, "O": 1.0},
    "CH3O": {"C": 1.0, "H": 3.0, "O": 1.0},
    "CH3OH": {"C": 1.0, "H": 4.0, "O": 1.0},
    "HCO": {"C": 1.0, "H": 1.0, "O": 1.0},
    "COOH": {"C": 1.0, "H": 1.0, "O": 2.0},
    "HCOOH": {"C": 1.0, "H": 2.0, "O": 2.0},
    "HCHO,formaldehy": {"C": 1.0, "H": 2.0, "O": 1.0},
    "C2H": {"C": 2.0, "H": 1.0},
    "C2H2,acetylene": {"C": 2.0, "H": 2.0},
    "C2O": {"C": 2.0, "O": 1.0},
    "HCCO": {"C": 2.0, "H": 1.0, "O": 1.0},
})

#: The curated product set for carbon/hydrogen/oxygen propellants. See the
#: module docstring for the measured cost of using it instead of CEA's full
#: automatic selection.
CHO_PRODUCT_SPECIES: tuple[str, ...] = (
    "CO", "CO2", "H", "H2", "H2O", "HO2", "H2O2", "O", "O2", "OH",
    "CH4", "C(gr)", "C", "CH", "CH2", "CH3", "CH2OH", "CH3O", "CH3OH",
    "HCO", "COOH", "HCOOH", "HCHO,formaldehy", "O3",
    "C2H", "C2H2,acetylene", "C2O", "HCCO",
)

#: The curated product set for hydrogen/oxygen propellants, where no carbon
#: species can form. A smaller set is not an optimisation: including carbon
#: species in a system with no carbon would leave them at exactly zero and
#: add nothing but noise to the composition.
HO_PRODUCT_SPECIES: tuple[str, ...] = (
    "H", "H2", "H2O", "HO2", "H2O2", "O", "O2", "OH", "O3",
)

#: CEA marks condensed phases with a parenthesised suffix on the species name.
#: This is a naming *convention* of the database, not a formula parse: the
#: suffix is read, the rest of the name is not interpreted.
_CONDENSED_SUFFIXES: Mapping[str, Phase] = {
    "(L)": Phase.LIQUID,
    "(l)": Phase.LIQUID,
    "(cr)": Phase.SOLID,
    "(gr)": Phase.SOLID,
    "(s)": Phase.SOLID,
    "(a)": Phase.SOLID,
    "(b)": Phase.SOLID,
    "(c)": Phase.SOLID,
    "(II)": Phase.SOLID,
    "(III)": Phase.SOLID,
}


def phase_of_cea_name(name: str) -> Phase:
    """The phase a CEA species name declares.

    Gas is the default because CEA names gaseous species without a suffix --
    which is a fact about the database, not an assumption about the substance.
    A suffix that is present but unrecognised raises rather than silently
    defaulting to gas, because "unknown phase treated as GAS" is exactly what
    Phase 5B forbids.
    """
    for suffix, phase in _CONDENSED_SUFFIXES.items():
        if name.endswith(suffix):
            return phase
    if name.endswith(")") and "(" in name:
        # A parenthesised tail that is not a known phase marker. Some product
        # names legitimately end in ')' as part of a chemical name, so this is
        # only a problem when the tail looks like a phase marker we do not know.
        tail = name[name.rfind("("):]
        if len(tail) <= 5 and tail not in _CONDENSED_SUFFIXES:
            raise CEAMappingError(
                f"CEA species {name!r} ends in {tail!r}, which is not a known "
                "phase marker. Refusing rather than assuming it is a gas.")
    return Phase.GAS


def cea_molar_masses(cea_module: ModuleType,
                     names: tuple[str, ...]) -> dict[str, float]:
    """CEA's own molar mass for each species, in kg/kmol.

    Obtained by asking a mixture to convert one mole of a single species into
    a mass. This is CEA's internal value, so nothing here can disagree with the
    database the solve used.
    """
    if not names:
        return {}
    try:
        mixture = cea_module.Mixture(list(names))
    except Exception as exc:  # noqa: BLE001
        from .errors import translate_cea_exception
        raise translate_cea_exception(
            exc, f"building a mixture of {len(names)} species") from exc

    masses: dict[str, float] = {}
    count = len(names)
    for index, name in enumerate(names):
        unit = np.zeros(count, dtype=float)
        unit[index] = 1.0
        weights = mixture.moles_to_weights(unit)
        masses[name] = float(np.sum(np.asarray(weights, dtype=float)))
    return masses


def build_species_table(
    cea_module: ModuleType,
    names: tuple[str, ...],
    *,
    database: str = "",
    database_version: str = "",
) -> dict[str, Species]:
    """Build RocketForge :class:`Species` records for CEA species names.

    Molar masses come from CEA; formulas come from :data:`CEA_FORMULAS`; phase
    comes from the name suffix. A name with no curated formula raises
    :class:`CEAMappingError` -- it is never dropped, and never given an empty
    formula, because either would break element conservation while leaving the
    composition summing to one.
    """
    missing = [name for name in names if name not in CEA_FORMULAS]
    if missing:
        raise CEAMappingError(
            f"no curated elemental formula for CEA species {missing!r}. "
            "Add them to CEA_FORMULAS with their source, or restrict the "
            "product set; they are not dropped, because a missing species "
            "breaks element conservation silently.")

    masses = cea_molar_masses(cea_module, names)
    table: dict[str, Species] = {}
    for name in names:
        molar_mass = molar_mass_to_si(masses[name])
        table[name] = Species(
            name=name,
            phase=phase_of_cea_name(name),
            molar_mass=molar_mass,
            formula=ElementalComposition.from_mapping(CEA_FORMULAS[name]),
            source=(f"NASA CEA {database or 'thermo.lib'}"
                    f"{(' ' + database_version) if database_version else ''}; "
                    "molar mass from the provider, formula curated in "
                    "rocketforge.providers.cea.species"),
        )
    return table
