"""LIQ-1 reactants and their mapping onto NASA CEA -- no provider needed.

Everything here runs in the base environment: the reactant identities, the
mixture fractions and their basis, the product-set choice, the refusals. What
CEA does with them is ``test_liquid_live.py``.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    Composition,
    CompositionBasis,
    MixtureRatio,
    Phase,
    PropellantDefinition,
    PropellantRole,
    PropellantStream,
)
from rocketforge.providers.cea import (
    GASEOUS_METHANE,
    GASEOUS_OXYGEN,
    LIQUID_HYDROGEN,
    LIQUID_METHANE,
    LOX,
    PRODUCTION_PROPELLANTS,
    build_chamber_input,
)
from rocketforge.providers.cea.errors import CEAMappingError
from rocketforge.providers.cea.species import CEA_FORMULAS, CHO_PRODUCT_SPECIES, HO_PRODUCT_SPECIES
from rocketforge.providers.cea_liquid import (
    AEROZINE_50,
    CHON_PRODUCT_SPECIES,
    FORMULAS,
    HF_PRODUCT_SPECIES,
    HNF_PRODUCT_SPECIES,
    HON_PRODUCT_SPECIES,
    HYDRAZINE,
    HYDROGEN_PEROXIDE_90,
    LIQUID_FLUORINE,
    LIQUID_PROPELLANTS,
    LIQUID_REACTANT_TEMPERATURE_RANGES,
    MMH,
    NITROGEN_TETROXIDE,
    PRODUCT_SPECIES_BY_ELEMENTS,
    RP1,
    UDMH,
    check_liquid_reactant_temperatures,
    check_product_coverage,
    liquid_phase_of_cea_name,
    liquid_product_species,
    reactant_cea_names,
)


def _request(oxidiser, fuel, of=2.0, *, t_ox=None, t_fuel=None, products=None):
    return ChamberEquilibriumRequest(
        fuel=PropellantStream(fuel, t_fuel or fuel.reference_temperature),
        oxidiser=PropellantStream(oxidiser, t_ox or oxidiser.reference_temperature),
        oxidiser_fuel_ratio=MixtureRatio(of),
        chamber_pressure=6.894757e6,
        product_species=products)


# ---------------------------------------------------------------------------
# identities
# ---------------------------------------------------------------------------

#: The exact provider identity of every LIQ-1 reactant, as verified against
#: cea 3.3.4's thermo.lib. A change here is a change of chemistry.
EXPECTED_IDENTITIES = {
    "LF2": ("oxidiser", ("F2(L)",)),
    "NTO": ("oxidiser", ("N2O4(L)",)),
    "HTP-90": ("oxidiser", ("H2O(L)", "H2O2(L)")),
    "N2H4": ("fuel", ("N2H4(L)",)),
    "UDMH": ("fuel", ("C2H8N2(L),UDMH",)),
    "MMH": ("fuel", ("CH6N2(L)",)),
    "RP-1": ("fuel", ("RP-1",)),
    "A-50": ("fuel", ("C2H8N2(L),UDMH", "N2H4(L)")),
}


def test_the_liq1_catalogue_is_exactly_the_sutton_reactants():
    """Nothing outside Sutton Table 5-5: no advanced catalogue entry."""
    assert set(LIQUID_PROPELLANTS) == set(EXPECTED_IDENTITIES)
    assert not set(LIQUID_PROPELLANTS) & set(PRODUCTION_PROPELLANTS)


@pytest.mark.parametrize("key,expected", sorted(EXPECTED_IDENTITIES.items()))
def test_each_reactant_resolves_to_its_verified_cea_identity(key, expected):
    role, names = expected
    definition = LIQUID_PROPELLANTS[key]
    assert definition.role.value == role
    assert tuple(sorted(reactant_cea_names(definition))) == names
    assert definition.reference_phase is Phase.LIQUID
    for name in names:
        assert name in FORMULAS, name


def test_display_names_and_provider_names_stay_distinct():
    """The user picks "MMH"; CEA receives ``CH6N2(L)``. Never the reverse."""
    assert MMH.name == "MMH" and MMH.provider_names["cea"] == "CH6N2(L)"
    assert UDMH.name == "UDMH" and UDMH.provider_names["cea"] == "C2H8N2(L),UDMH"
    assert NITROGEN_TETROXIDE.name == "NTO"
    assert NITROGEN_TETROXIDE.provider_names["cea"] == "N2O4(L)"


def test_no_reactant_is_or_contains_irfna_or_nitric_acid():
    """RFNA is blocked, and IRFNA is not substituted for it under any name."""
    every_name = set()
    for definition in (*LIQUID_PROPELLANTS.values(), *PRODUCTION_PROPELLANTS.values()):
        every_name.update(reactant_cea_names(definition))
        every_name.add(definition.name)
    assert not {"IRFNA", "RFNA", "HNO3(L)", "HNO3"} & every_name
    assert not any("FNA" in name.upper() for name in every_name)


def test_ranges_are_recorded_for_every_reactant_that_declares_one():
    declared = {name for definition in LIQUID_PROPELLANTS.values()
                for name in reactant_cea_names(definition)} - {"H2O(L)"}
    assert set(LIQUID_REACTANT_TEMPERATURE_RANGES) == declared
    for definition in LIQUID_PROPELLANTS.values():
        for name in reactant_cea_names(definition):
            if name in LIQUID_REACTANT_TEMPERATURE_RANGES:
                low, high = LIQUID_REACTANT_TEMPERATURE_RANGES[name]
                assert low <= definition.reference_temperature <= high, name


def test_new_formulae_never_override_a_frozen_one():
    for name, formula in CEA_FORMULAS.items():
        assert FORMULAS[name] == formula


def test_rp1_is_ceas_own_pseudo_species():
    assert FORMULAS["RP-1"] == {"C": 1.0, "H": 1.95}
    assert RP1.is_surrogate and "C 1.00 H 1.95" in RP1.source


# ---------------------------------------------------------------------------
# mixtures: composition, basis, mass-vs-mole safety
# ---------------------------------------------------------------------------


def test_aerozine_50_is_a_mass_basis_mixture_of_two_real_species():
    composition = AEROZINE_50.composition
    assert composition.basis is CompositionBasis.MASS_FRACTION
    assert dict(composition.entries) == {"C2H8N2(L),UDMH": 0.5, "N2H4(L)": 0.5}
    assert AEROZINE_50.provider_names == {}      # no invented species name


def test_htp_90_is_ninety_percent_peroxide_by_mass_not_pure():
    composition = HYDROGEN_PEROXIDE_90.composition
    assert composition.basis is CompositionBasis.MASS_FRACTION
    assert dict(composition.entries) == {"H2O2(L)": 0.9, "H2O(L)": 0.1}
    assert HYDROGEN_PEROXIDE_90.provider_names == {}


@pytest.mark.parametrize("oxidiser,fuel,expected", [
    (NITROGEN_TETROXIDE, AEROZINE_50,
     {"C2H8N2(L),UDMH": 0.5, "N2H4(L)": 0.5}),
    (HYDROGEN_PEROXIDE_90, RP1, {"H2O2(L)": 0.9, "H2O(L)": 0.1}),
])
def test_mixture_fractions_reach_cea_as_the_stated_mass_weights(oxidiser, fuel, expected):
    """The general blend path: mass fractions pass straight through.

    No molar masses are supplied, so a mole-basis conversion would have raised;
    the weights arriving unchanged is the proof they were never reinterpreted.
    """
    request = _request(oxidiser, fuel, 2.0)
    prepared = replace(request, product_species=liquid_product_species(request))
    mapped = build_chamber_input(prepared)
    side = "fuel_weights" if fuel.is_blend else "oxidiser_weights"
    weights = {name: weight for name, weight
               in zip(mapped.reactant_names, getattr(mapped, side)) if weight}
    assert weights == pytest.approx(expected, rel=0, abs=0)
    assert mapped.of_ratio == 2.0


def test_a_mole_basis_reading_would_be_a_different_mixture():
    """Mass-vs-mole is not cosmetic: 50/50 by mole of UDMH and N2H4 is 65/35
    by mass. The definition must therefore state its basis, and does."""
    molar = {"C2H8N2(L),UDMH": 60.09832e-3, "N2H4(L)": 32.04516e-3}
    by_mole = PropellantDefinition(
        name="A-50 by mole (counterfactual)", role=PropellantRole.FUEL,
        composition=Composition.from_fractions(
            {"C2H8N2(L),UDMH": 0.5, "N2H4(L)": 0.5}, CompositionBasis.MOLE_FRACTION),
        reference_temperature=298.15, reference_phase=Phase.LIQUID)
    request = _request(NITROGEN_TETROXIDE, by_mole, 2.0)
    prepared = replace(request, product_species=liquid_product_species(request))
    mapped = build_chamber_input(prepared, molar_masses=molar)
    weights = dict(zip(mapped.reactant_names, mapped.fuel_weights))
    assert weights["C2H8N2(L),UDMH"] == pytest.approx(0.65219, abs=1e-4)
    with pytest.raises(CEAMappingError, match="mole basis"):
        build_chamber_input(prepared)


# ---------------------------------------------------------------------------
# product sets
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("oxidiser,fuel,expected", [
    (LOX, HYDRAZINE, HON_PRODUCT_SPECIES),
    (NITROGEN_TETROXIDE, HYDRAZINE, HON_PRODUCT_SPECIES),
    (LOX, UDMH, CHON_PRODUCT_SPECIES),
    (NITROGEN_TETROXIDE, AEROZINE_50, CHON_PRODUCT_SPECIES),
    (NITROGEN_TETROXIDE, RP1, CHON_PRODUCT_SPECIES),
    (NITROGEN_TETROXIDE, MMH, CHON_PRODUCT_SPECIES),
    (LIQUID_FLUORINE, LIQUID_HYDROGEN, HF_PRODUCT_SPECIES),
    (LIQUID_FLUORINE, HYDRAZINE, HNF_PRODUCT_SPECIES),
    (LOX, RP1, CHO_PRODUCT_SPECIES),
    (HYDROGEN_PEROXIDE_90, RP1, CHO_PRODUCT_SPECIES),
])
def test_each_sutton_pair_gets_the_product_set_for_its_elements(oxidiser, fuel, expected):
    assert liquid_product_species(_request(oxidiser, fuel)) is expected


@pytest.mark.parametrize("oxidiser,fuel", [
    (LOX, LIQUID_METHANE), (LOX, LIQUID_HYDROGEN),
    (GASEOUS_OXYGEN, GASEOUS_METHANE), (LOX, GASEOUS_METHANE),
])
def test_the_accepted_pairs_are_left_to_the_frozen_selection(oxidiser, fuel):
    """``None`` means the request reaches the frozen provider untouched."""
    assert liquid_product_species(_request(oxidiser, fuel)) is None


def test_rp1_is_never_handed_to_the_frozen_selection():
    """The frozen selection reads RP-1's key as element-free and would choose
    the H/O set; CEA then aborts the process on the missing carbon. RP-1 is
    therefore always given its set explicitly."""
    assert liquid_product_species(_request(LOX, RP1)) == CHO_PRODUCT_SPECIES
    assert "C" not in {e for name in HO_PRODUCT_SPECIES for e in FORMULAS[name]}


def test_an_element_system_with_no_curated_set_is_refused():
    """LF2 with a carbon fuel is not a Sutton pair and has no C/H/F/N set."""
    with pytest.raises(CEAMappingError, match="no curated product species"):
        liquid_product_species(_request(LIQUID_FLUORINE, MMH, 2.0))


def test_a_product_set_missing_a_reactant_element_is_refused_before_cea():
    """CEA aborts the process on this; RocketForge refuses instead."""
    request = _request(NITROGEN_TETROXIDE, HYDRAZINE, products=HO_PRODUCT_SPECIES)
    with pytest.raises(CEAMappingError, match="holds no"):
        check_product_coverage(request, request.product_species)


@pytest.mark.parametrize("elements,species", sorted(
    PRODUCT_SPECIES_BY_ELEMENTS.items(), key=lambda item: sorted(item[0])))
def test_every_product_set_covers_its_elements_and_has_formulae(elements, species):
    covered = set()
    for name in species:
        assert name in FORMULAS, name
        covered.update(FORMULAS[name])
    assert covered == set(elements)


@pytest.mark.parametrize("species", [HON_PRODUCT_SPECIES, CHON_PRODUCT_SPECIES,
                                     HF_PRODUCT_SPECIES, HNF_PRODUCT_SPECIES])
def test_new_product_sets_put_condensed_phases_last(species):
    """Measured: a condensed species among the gases gave a converged 758 K
    garbage chamber. Every new set lists gases first."""
    phases = [liquid_phase_of_cea_name(name).is_condensed for name in species]
    assert phases == sorted(phases)
    assert len(set(species)) == len(species)


@pytest.mark.parametrize("name,phase", [
    ("C2H8N2(L),UDMH", Phase.LIQUID), ("N2H4(L)", Phase.LIQUID),
    ("NH4F(cr)", Phase.SOLID), ("C3H6,cyclo-", Phase.GAS),
    ("HCHO,formaldehy", Phase.GAS),
])
def test_phase_reading_handles_comma_suffixed_names(name, phase):
    assert liquid_phase_of_cea_name(name) is phase


# ---------------------------------------------------------------------------
# temperature range refusal
# ---------------------------------------------------------------------------


def test_a_stream_outside_its_ceas_declared_range_is_refused():
    request = _request(NITROGEN_TETROXIDE, UDMH, t_fuel=350.0)
    with pytest.raises(CEAMappingError, match=r"C2H8N2\(L\),UDMH"):
        check_liquid_reactant_temperatures(request)


def test_a_stream_inside_its_range_is_accepted():
    check_liquid_reactant_temperatures(_request(NITROGEN_TETROXIDE, UDMH, t_fuel=300.0))
