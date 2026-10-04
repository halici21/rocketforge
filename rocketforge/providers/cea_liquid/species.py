"""Product species and element formulae for the LIQ-1 liquid propellants.

The frozen provider curates formulae and product sets for carbon, hydrogen and
oxygen only (``rocketforge.providers.cea.species``). The Sutton Table 5-5
storable and fluorine propellants bring nitrogen and fluorine into the
products, which no curated set there can hold -- and an N-bearing reactant
solved against H/O products cannot conserve nitrogen. This module adds what is
missing and **reuses** everything the frozen module already curates, unchanged.

**How each set was chosen** -- by measurement against CEA's own
``products_from_reactants`` selection on the shipped ``thermo.lib`` (cea
3.3.4, sha256 ``8e5df1cc...``), the same way the C/H/O set was:

* H/O/N, H/F and H/N/F: CEA's full selection is small (32, 11 and 30 species)
  and is used **whole**, in CEA's own order, so the truncation cost is zero by
  construction.
* C/H/O/N: CEA selects 161 species. The curated set is every species that
  reached a mole fraction of 1e-10 at any station (chamber, throat, exit) of a
  shifting expansion of O2/UDMH, N2O4/Aerozine-50, N2O4/RP-1 or N2O4/MMH,
  swept over 5 to 200 bar and 0.5x to 2x of Sutton's mixture ratios: 74 gases
  plus three condensed phases, 77 in all. At Sutton's own conditions it reproduces the
  full selection to dTc <= 1.2e-07 K and dIsp/Isp <= 1.3e-10.

**Condensed species come last in every set here.** Measured on this build:
with ``H2O(L)`` placed among the gases, CEA reported ``converged = True`` for
O2/UDMH and returned a 758 K "chamber". Gases first, condensed phases after,
is the order CEA's own selection uses. (The frozen C/H/O set places ``C(gr)``
mid-list; that is a measured 4.4e-04 K at O2/RP-1, below its documented
truncation cost, and that set is reused exactly as accepted.)

Formulae are integers except RP-1's, which is CEA's own pseudo-species record
(C 1.00, H 1.95). Every reactant formula below was read from its record in the
shipped ``thermo.lib``, and every formula is checked against CEA's own molar
mass by ``tests/providers/cea_liquid``.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType, ModuleType

from rocketforge.physics.thermochemistry import (
    ElementalComposition,
    Phase,
    Species,
)
from rocketforge.providers.cea.errors import CEAMappingError
from rocketforge.providers.cea.species import (
    CEA_FORMULAS,
    CHO_PRODUCT_SPECIES,
    HO_PRODUCT_SPECIES,
    cea_molar_masses,
    phase_of_cea_name,
)
from rocketforge.providers.cea.units import molar_mass_to_si

__all__ = [
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

#: Formulae this package adds. None of these names is in the frozen table.
LIQUID_FORMULAS: Mapping[str, Mapping[str, float]] = MappingProxyType({
    # --- reactants (Sutton Table 5-5), read from their thermo.lib records --
    "RP-1": {"C": 1.0, "H": 1.95},
    "N2H4(L)": {"N": 2.0, "H": 4.0},
    "C2H8N2(L),UDMH": {"C": 2.0, "H": 8.0, "N": 2.0},
    "CH6N2(L)": {"C": 1.0, "H": 6.0, "N": 2.0},
    "F2(L)": {"F": 2.0},
    "N2O4(L)": {"N": 2.0, "O": 4.0},
    "H2O2(L)": {"H": 2.0, "O": 2.0},
    # --- H/O/N products --------------------------------------------------
    "N": {"N": 1.0},
    "N2": {"N": 2.0},
    "N3": {"N": 3.0},
    "NH": {"N": 1.0, "H": 1.0},
    "NH2": {"N": 1.0, "H": 2.0},
    "NH3": {"N": 1.0, "H": 3.0},
    "N2H2": {"N": 2.0, "H": 2.0},
    "N2H4": {"N": 2.0, "H": 4.0},
    "N3H": {"N": 3.0, "H": 1.0},
    "NO": {"N": 1.0, "O": 1.0},
    "NO2": {"N": 1.0, "O": 2.0},
    "NO3": {"N": 1.0, "O": 3.0},
    "N2O": {"N": 2.0, "O": 1.0},
    "N2O3": {"N": 2.0, "O": 3.0},
    "N2O4": {"N": 2.0, "O": 4.0},
    "N2O5": {"N": 2.0, "O": 5.0},
    "HNO": {"H": 1.0, "N": 1.0, "O": 1.0},
    "HNO2": {"H": 1.0, "N": 1.0, "O": 2.0},
    "HNO3": {"H": 1.0, "N": 1.0, "O": 3.0},
    "NH2OH": {"N": 1.0, "H": 3.0, "O": 1.0},
    "NH2NO2": {"N": 2.0, "H": 2.0, "O": 2.0},
    # --- C/H/O/N products ------------------------------------------------
    "CN": {"C": 1.0, "N": 1.0},
    "HCN": {"H": 1.0, "C": 1.0, "N": 1.0},
    "HNC": {"H": 1.0, "N": 1.0, "C": 1.0},
    "NCO": {"N": 1.0, "C": 1.0, "O": 1.0},
    "HNCO": {"H": 1.0, "N": 1.0, "C": 1.0, "O": 1.0},
    "C2N2": {"C": 2.0, "N": 2.0},
    "OCCN": {"O": 1.0, "C": 2.0, "N": 1.0},
    "CH3CN": {"C": 2.0, "H": 3.0, "N": 1.0},
    "C2H2,vinylidene": {"C": 2.0, "H": 2.0},
    "C2H3,vinyl": {"C": 2.0, "H": 3.0},
    "C2H4": {"C": 2.0, "H": 4.0},
    "C2H5": {"C": 2.0, "H": 5.0},
    "C2H6": {"C": 2.0, "H": 6.0},
    "C2H5OH": {"C": 2.0, "H": 6.0, "O": 1.0},
    "CH2CO,ketene": {"C": 2.0, "H": 2.0, "O": 1.0},
    "CH3CO,acetyl": {"C": 2.0, "H": 3.0, "O": 1.0},
    "CH3CHO,ethanal": {"C": 2.0, "H": 4.0, "O": 1.0},
    "CH3COOH": {"C": 2.0, "H": 4.0, "O": 2.0},
    "C3H3,2-propynl": {"C": 3.0, "H": 3.0},
    "C3H4,allene": {"C": 3.0, "H": 4.0},
    "C3H4,propyne": {"C": 3.0, "H": 4.0},
    "C3H5,allyl": {"C": 3.0, "H": 5.0},
    "C3H6,cyclo-": {"C": 3.0, "H": 6.0},
    "C3H6,propylene": {"C": 3.0, "H": 6.0},
    "C3H8": {"C": 3.0, "H": 8.0},
    "C3H6O,acetone": {"C": 3.0, "H": 6.0, "O": 1.0},
    "C3H6O,propanal": {"C": 3.0, "H": 6.0, "O": 1.0},
    "C3O2": {"C": 3.0, "O": 2.0},
    "C4H2,butadiyne": {"C": 4.0, "H": 2.0},
    "C4H6,butadiene": {"C": 4.0, "H": 6.0},
    "C4H8,1-butene": {"C": 4.0, "H": 8.0},
    # --- F/H and F/H/N products ------------------------------------------
    "F": {"F": 1.0},
    "F2": {"F": 2.0},
    "HF": {"H": 1.0, "F": 1.0},
    "H2F2": {"H": 2.0, "F": 2.0},
    "H3F3": {"H": 3.0, "F": 3.0},
    "H4F4": {"H": 4.0, "F": 4.0},
    "H5F5": {"H": 5.0, "F": 5.0},
    "H6F6": {"H": 6.0, "F": 6.0},
    "H7F7": {"H": 7.0, "F": 7.0},
    "NF": {"N": 1.0, "F": 1.0},
    "NF2": {"N": 1.0, "F": 2.0},
    "NF3": {"N": 1.0, "F": 3.0},
    "N2F2": {"N": 2.0, "F": 2.0},
    "N2F4": {"N": 2.0, "F": 4.0},
    "NHF": {"N": 1.0, "H": 1.0, "F": 1.0},
    "NHF2": {"N": 1.0, "H": 1.0, "F": 2.0},
    "NH2F": {"N": 1.0, "H": 2.0, "F": 1.0},
    "NH4F(L)": {"N": 1.0, "H": 4.0, "F": 1.0},
    "NH4F(cr)": {"N": 1.0, "H": 4.0, "F": 1.0},
})

#: The frozen table and this one together. Disjoint by construction (asserted
#: at import), so no frozen formula is ever overridden here.
if set(CEA_FORMULAS) & set(LIQUID_FORMULAS):
    raise ImportError("cea_liquid would override a frozen CEA formula: "
                      f"{sorted(set(CEA_FORMULAS) & set(LIQUID_FORMULAS))}")
FORMULAS: Mapping[str, Mapping[str, float]] = MappingProxyType(
    {**CEA_FORMULAS, **LIQUID_FORMULAS})

#: Hydrogen/oxygen/nitrogen: LOX or N2O4 with hydrazine. CEA's complete
#: selection, in its own order (condensed last).
HON_PRODUCT_SPECIES: tuple[str, ...] = (
    "H", "H2", "H2O", "H2O2", "HNO", "HNO2", "HNO3", "HO2", "N", "N2",
    "N2H2", "N2H4", "N2O", "N2O3", "N2O4", "N2O5", "N3", "N3H", "NH", "NH2",
    "NH2NO2", "NH2OH", "NH3", "NO", "NO2", "NO3", "O", "O2", "O3", "OH",
    "H2O(L)", "H2O(cr)",
)

#: Carbon/hydrogen/oxygen/nitrogen: the curated 1e-10 set described above.
#: Gases alphabetical, condensed phases last.
CHON_PRODUCT_SPECIES: tuple[str, ...] = (
    "C", "C2H2,acetylene", "C2H2,vinylidene", "C2H3,vinyl", "C2H4", "C2H5",
    "C2H5OH", "C2H6", "C2N2", "C2O", "C3H3,2-propynl", "C3H4,allene",
    "C3H4,propyne", "C3H5,allyl", "C3H6,cyclo-", "C3H6,propylene",
    "C3H6O,acetone", "C3H6O,propanal", "C3H8", "C3O2", "C4H2,butadiyne",
    "C4H6,butadiene", "C4H8,1-butene", "CH", "CH2", "CH2CO,ketene", "CH2OH",
    "CH3", "CH3CHO,ethanal", "CH3CN", "CH3CO,acetyl", "CH3COOH", "CH3O",
    "CH3OH", "CH4", "CN", "CO", "CO2", "COOH", "H", "H2", "H2O", "H2O2",
    "HCCO", "HCHO,formaldehy", "HCN", "HCO", "HCOOH", "HNC", "HNCO", "HNO",
    "HNO2", "HNO3", "HO2", "N", "N2", "N2H2", "N2O", "N2O3", "N3", "N3H",
    "NCO", "NH", "NH2", "NH2OH", "NH3", "NO", "NO2", "NO3", "O", "O2", "O3",
    "OCCN", "OH",
    "C(gr)", "H2O(L)", "H2O(cr)",
)

#: Hydrogen/fluorine: LF2/LH2. CEA's complete selection, in its own order.
HF_PRODUCT_SPECIES: tuple[str, ...] = (
    "F", "F2", "H", "H2", "H2F2", "H3F3", "H4F4", "H5F5", "H6F6", "H7F7",
    "HF",
)

#: Hydrogen/nitrogen/fluorine: LF2/hydrazine. CEA's complete selection, in
#: its own order (condensed last).
HNF_PRODUCT_SPECIES: tuple[str, ...] = (
    "F", "F2", "H", "H2", "H2F2", "H3F3", "H4F4", "H5F5", "H6F6", "H7F7",
    "HF", "N", "N2", "N2F2", "N2F4", "N2H2", "N2H4", "N3", "N3H", "NF",
    "NF2", "NF3", "NH", "NH2", "NH2F", "NH3", "NHF", "NHF2",
    "NH4F(L)", "NH4F(cr)",
)

#: The product set for every element system a reactant pair can span. The
#: H/O and C/H/O entries are the frozen provider's own sets, by reference. A
#: system absent from this table has no curated set and is refused.
PRODUCT_SPECIES_BY_ELEMENTS: Mapping[frozenset[str], tuple[str, ...]] = MappingProxyType({
    frozenset({"H", "O"}): HO_PRODUCT_SPECIES,
    frozenset({"C", "H", "O"}): CHO_PRODUCT_SPECIES,
    frozenset({"H", "N", "O"}): HON_PRODUCT_SPECIES,
    frozenset({"C", "H", "N", "O"}): CHON_PRODUCT_SPECIES,
    frozenset({"F", "H"}): HF_PRODUCT_SPECIES,
    frozenset({"F", "H", "N"}): HNF_PRODUCT_SPECIES,
})


def liquid_phase_of_cea_name(name: str) -> Phase:
    """The phase a CEA name declares, including comma-suffixed names.

    Some names carry a common name after a comma -- ``C2H8N2(L),UDMH``,
    ``C3H6,cyclo-`` -- and the phase marker, when there is one, sits before the
    comma. The frozen classifier reads the whole name, which would call liquid
    UDMH a gas; this reads the part before the first comma and hands it to the
    frozen classifier, so the marker vocabulary stays the frozen one.
    """
    return phase_of_cea_name(name.split(",", 1)[0])


def build_liquid_species_table(
    cea_module: ModuleType,
    names: tuple[str, ...],
    *,
    database: str = "",
    database_version: str = "",
) -> dict[str, Species]:
    """``Species`` records over the combined formula table.

    The frozen ``build_species_table``, widened to :data:`FORMULAS` and to
    comma-suffixed phase markers. Molar masses come from CEA itself, through
    the frozen ``cea_molar_masses``. A name with no curated formula is refused,
    never dropped: a missing species breaks element conservation silently.
    """
    missing = [name for name in names if name not in FORMULAS]
    if missing:
        raise CEAMappingError(
            f"no curated elemental formula for CEA species {missing!r}. They "
            "are not dropped, because a missing species breaks element "
            "conservation silently.")
    masses = cea_molar_masses(cea_module, names)
    return {
        name: Species(
            name=name,
            phase=liquid_phase_of_cea_name(name),
            molar_mass=molar_mass_to_si(masses[name]),
            formula=ElementalComposition.from_mapping(FORMULAS[name]),
            source=(f"NASA CEA {database or 'thermo.lib'}"
                    f"{(' ' + database_version) if database_version else ''}; "
                    "molar mass from the provider, formula curated in "
                    "rocketforge.providers.cea_liquid.species"),
        )
        for name in names
    }
