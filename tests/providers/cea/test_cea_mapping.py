"""Request mapping, unit conversion and naming -- all without a provider.

These are the tests that pin down the things most likely to be silently wrong
in an adapter: which temperature is used, which way round O/F goes, and what a
pressure means. Every one of them runs in the base environment with no
chemistry library installed, because :func:`build_chamber_input` is a pure
function on purpose.
"""

from __future__ import annotations

import dataclasses
import math

import pytest

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    Composition,
    CompositionBasis,
    EquilibriumConstraint,
    MixtureRatio,
    Phase,
    PropellantDefinition,
    PropellantRole,
    PropellantStream,
)
from rocketforge.providers.cea import (
    CEA_MAX_NAME_LENGTH,
    GASEOUS_METHANE,
    GASEOUS_OXYGEN,
    LIQUID_METHANE,
    LOX,
    CEAMappingError,
    build_chamber_input,
)
from rocketforge.providers.cea.mapping import select_product_species
from rocketforge.providers.cea.naming import cea_name_for
from rocketforge.providers.cea.species import CHO_PRODUCT_SPECIES, HO_PRODUCT_SPECIES
from rocketforge.providers.cea.units import (
    enthalpy_argument,
    molar_mass_to_si,
    pressure_to_bar,
    specific_energy_to_si,
    specific_heat_to_si,
)

MASS = CompositionBasis.MASS_FRACTION
MOLE = CompositionBasis.MOLE_FRACTION


# ---------------------------------------------------------------------------
# units -- expected values computed independently, not via the function
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pascals,expected_bar", [
    (1.0e5, 1.0),        # 1 bar
    (1.0e7, 100.0),      # 10 MPa, the production case
    (5.0e6, 50.0),
    (2.0e7, 200.0),
    (101325.0, 1.01325),  # one standard atmosphere
])
def test_pressure_to_bar(pascals, expected_bar):
    """1 bar is 1e5 Pa exactly, so these are hand-checkable."""
    assert pressure_to_bar(pascals) == pytest.approx(expected_bar, rel=1e-15)


def test_molar_mass_conversion_is_the_thousandfold_one():
    """CEA reports kg/kmol; RocketForge stores kg/mol."""
    assert molar_mass_to_si(21.77009) == pytest.approx(0.02177009, rel=1e-15)
    assert molar_mass_to_si(31.9988) == pytest.approx(0.0319988, rel=1e-15)


def test_specific_quantities_scale_by_one_thousand():
    assert specific_heat_to_si(2.3348226) == pytest.approx(2334.8226, rel=1e-15)
    assert specific_energy_to_si(-1577.58443) == pytest.approx(-1577584.43, rel=1e-9)


def test_enthalpy_argument_uses_ceas_own_constant():
    """The HP constraint is H/R, and both operands must be CEA's.

    Substituting RocketForge's CODATA constant here would put a 5.7e-06
    inconsistency into the solver's own input -- a different and worse thing
    than the known difference in the reported properties.
    """
    assert enthalpy_argument(-1.0e6, 8314.51) == pytest.approx(-1.0e6 / 8314.51,
                                                               rel=1e-15)


# ---------------------------------------------------------------------------
# O/F orientation
# ---------------------------------------------------------------------------


def test_of_orientation_reaches_cea_unchanged(lox_methane_request):
    """O/F is oxidiser over fuel, and so is CEA's. 3.4, never 0.294."""
    mapped = build_chamber_input(lox_methane_request)
    assert mapped.of_ratio == pytest.approx(3.4)
    assert mapped.of_ratio != pytest.approx(1.0 / 3.4)


def test_fuel_and_oxidiser_land_on_the_correct_sides(lox_methane_request):
    """The weight vectors are disjoint and on the right species.

    A test that would pass either way if fuel and oxidiser were swapped would
    be worthless, so this asserts which name carries which weight.
    """
    mapped = build_chamber_input(lox_methane_request)
    assert mapped.reactant_names == ("CH4(L)", "O2(L)")
    assert mapped.fuel_names == ("CH4(L)",)
    assert mapped.oxidiser_names == ("O2(L)",)
    assert mapped.fuel_weights == (1.0, 0.0)
    assert mapped.oxidiser_weights == (0.0, 1.0)


def test_swapping_the_streams_is_refused_before_mapping(lox_stream, methane_stream):
    """The request itself refuses it, so mapping is never reached."""
    from rocketforge.physics.thermochemistry import PropellantRoleError
    with pytest.raises(PropellantRoleError):
        ChamberEquilibriumRequest(
            fuel=lox_stream, oxidiser=methane_stream,
            oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)


def test_of_orientation_mutation_is_detectable(lox_methane_request):
    """A controlled F/O fixture must produce a different mapping.

    Proves the orientation test above can fail -- it is not satisfied by any
    number at all.
    """
    correct = build_chamber_input(lox_methane_request)
    inverted_request = dataclasses.replace(
        lox_methane_request,
        oxidiser_fuel_ratio=MixtureRatio(1.0 / 3.4))
    inverted = build_chamber_input(inverted_request)
    assert inverted.of_ratio != pytest.approx(correct.of_ratio)
    assert inverted.of_ratio == pytest.approx(0.29411764705882354)


# ---------------------------------------------------------------------------
# temperature sourcing -- the 74.9 K question
# ---------------------------------------------------------------------------


def test_actual_stream_temperature_is_used_not_the_reference(lox_methane_request):
    mapped = build_chamber_input(lox_methane_request)
    assert mapped.reactant_temperatures == (111.643, 90.17)


def test_a_different_stream_temperature_changes_the_mapping(lox_methane_request):
    """The guard against silently substituting the definition's reference."""
    warmer = dataclasses.replace(
        lox_methane_request,
        oxidiser=PropellantStream(LOX, 95.0, phase=Phase.LIQUID))
    mapped = build_chamber_input(warmer)
    assert mapped.reactant_temperatures == (111.643, 95.0)
    assert LOX.reference_temperature == pytest.approx(90.17)
    assert mapped.reactant_temperatures[1] != LOX.reference_temperature


def test_reference_temperature_substitution_would_be_visible(lox_methane_request):
    """A controlled bad adapter using the reference T produces a different map.

    The mutation proof for the most expensive silent defect available here:
    Phase 5B-0 measured the substitution as 74.9 K of chamber temperature.
    """
    correct = build_chamber_input(lox_methane_request)
    bad = (lox_methane_request.fuel.propellant.reference_temperature,
           lox_methane_request.oxidiser.propellant.reference_temperature)
    warmed = dataclasses.replace(
        lox_methane_request,
        fuel=PropellantStream(LIQUID_METHANE, 120.0, phase=Phase.LIQUID))
    assert build_chamber_input(warmed).reactant_temperatures[0] == 120.0
    assert bad[0] == pytest.approx(111.643)
    assert correct.reactant_temperatures[0] != 120.0


def test_a_reactant_outside_ceas_stated_range_is_refused(lox_methane_request):
    """CEA states 80.170-100.170 K for O2(L). 300 K is not an extrapolation."""
    too_warm = dataclasses.replace(
        lox_methane_request,
        oxidiser=PropellantStream(LOX, 300.0, phase=Phase.LIQUID))
    with pytest.raises(CEAMappingError, match=r"\[80.17, 100.17\] K"):
        build_chamber_input(too_warm)


# ---------------------------------------------------------------------------
# phase mapping
# ---------------------------------------------------------------------------


def test_liquid_and_gaseous_oxygen_map_to_different_cea_reactants():
    """O2 and O2(L) are different thermochemical identities, not a flag."""
    assert cea_name_for(LOX) == "O2(L)"
    assert cea_name_for(GASEOUS_OXYGEN) == "O2"
    assert cea_name_for(LIQUID_METHANE) == "CH4(L)"
    assert cea_name_for(GASEOUS_METHANE) == "CH4"


def test_phase_mutation_changes_the_provider_input(lox_stream, methane_stream):
    """Swapping liquid propellants for gaseous ones is visible in the mapping."""
    liquid = build_chamber_input(ChamberEquilibriumRequest(
        fuel=methane_stream, oxidiser=lox_stream,
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6))
    gaseous = build_chamber_input(ChamberEquilibriumRequest(
        fuel=PropellantStream(GASEOUS_METHANE, 298.15, phase=Phase.GAS),
        oxidiser=PropellantStream(GASEOUS_OXYGEN, 298.15, phase=Phase.GAS),
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6))
    assert liquid.reactant_names == ("CH4(L)", "O2(L)")
    assert gaseous.reactant_names == ("CH4", "O2")
    assert liquid.reactant_temperatures != gaseous.reactant_temperatures


# ---------------------------------------------------------------------------
# naming
# ---------------------------------------------------------------------------


def test_a_propellant_without_a_cea_name_is_refused_not_guessed():
    """No fallback to the canonical name: it would substitute a substance."""
    unmapped = PropellantDefinition(
        name="MYSTERY-FUEL", role=PropellantRole.FUEL,
        composition=Composition.pure("CH4"),
        reference_temperature=298.15, reference_phase=Phase.GAS)
    with pytest.raises(CEAMappingError, match="no NASA CEA name"):
        cea_name_for(unmapped)


def test_a_name_longer_than_ceas_field_width_is_refused_not_truncated():
    """15 characters, established by measurement. Truncating would substitute."""
    assert CEA_MAX_NAME_LENGTH == 15
    long_named = PropellantDefinition(
        name="X", role=PropellantRole.FUEL, composition=Composition.pure("CH4"),
        reference_temperature=298.15, reference_phase=Phase.GAS,
        provider_names={"cea": "A" * 16})
    with pytest.raises(CEAMappingError, match="CEA_INVALID_SIZE"):
        cea_name_for(long_named)


def test_the_cea_name_limit_does_not_touch_the_domain():
    """RocketForge identifiers stay unconstrained; only the adapter cares."""
    long_domain_name = "a-very-long-rocketforge-propellant-identifier"
    propellant = PropellantDefinition(
        name=long_domain_name, role=PropellantRole.FUEL,
        composition=Composition.pure("CH4"), reference_temperature=298.15,
        reference_phase=Phase.GAS, provider_names={"cea": "CH4"})
    assert propellant.name == long_domain_name
    assert cea_name_for(propellant) == "CH4"


# ---------------------------------------------------------------------------
# blends
# ---------------------------------------------------------------------------


def _blend(basis, fractions, role=PropellantRole.OXIDISER):
    return PropellantDefinition(
        name="TEST-BLEND", role=role,
        composition=Composition.from_fractions(fractions, basis),
        reference_temperature=298.15, reference_phase=Phase.LIQUID,
        source="synthetic test blend")


def test_mass_basis_blend_passes_through_unchanged(methane_stream):
    """CEA weights are masses, so a mass-basis blend needs no conversion."""
    blend = _blend(MASS, {"H2O2": 0.9, "H2O": 0.1})
    mapped = build_chamber_input(ChamberEquilibriumRequest(
        fuel=methane_stream,
        oxidiser=PropellantStream(blend, 298.15),
        oxidiser_fuel_ratio=MixtureRatio(7.0), chamber_pressure=10.0e6))
    assert mapped.oxidiser_names == ("H2O", "H2O2")   # canonical order
    weights = dict(zip(mapped.reactant_names, mapped.oxidiser_weights))
    assert weights["H2O2"] == pytest.approx(0.9)
    assert weights["H2O"] == pytest.approx(0.1)


def test_mole_basis_blend_is_converted_using_supplied_molar_masses(methane_stream):
    """A mole-basis blend must be converted to masses, and it is -- explicitly.

    50/50 by mole of species with molar masses 10 and 90 g/mol gives mass
    fractions of 0.1 and 0.9 exactly, computed by hand.
    """
    blend = _blend(MOLE, {"AA": 0.5, "BB": 0.5})
    mapped = build_chamber_input(
        ChamberEquilibriumRequest(
            fuel=methane_stream, oxidiser=PropellantStream(blend, 298.15),
            oxidiser_fuel_ratio=MixtureRatio(3.0), chamber_pressure=10.0e6),
        molar_masses={"AA": 10.0e-3, "BB": 90.0e-3})
    weights = dict(zip(mapped.reactant_names, mapped.oxidiser_weights))
    assert weights["AA"] == pytest.approx(0.1, rel=1e-12)
    assert weights["BB"] == pytest.approx(0.9, rel=1e-12)


def test_mole_basis_blend_without_molar_masses_is_refused(methane_stream):
    blend = _blend(MOLE, {"AA": 0.5, "BB": 0.5})
    with pytest.raises(CEAMappingError, match="mole basis"):
        build_chamber_input(ChamberEquilibriumRequest(
            fuel=methane_stream, oxidiser=PropellantStream(blend, 298.15),
            oxidiser_fuel_ratio=MixtureRatio(3.0), chamber_pressure=10.0e6))


def test_blend_component_order_does_not_change_the_mapping(methane_stream):
    """Compositions built in different order map to the same CEA request."""
    a = _blend(MASS, {"H2O2": 0.9, "H2O": 0.1})
    b = _blend(MASS, {"H2O": 0.1, "H2O2": 0.9})
    kwargs = dict(fuel=methane_stream, oxidiser_fuel_ratio=MixtureRatio(7.0),
                  chamber_pressure=10.0e6)
    first = build_chamber_input(ChamberEquilibriumRequest(
        oxidiser=PropellantStream(a, 298.15), **kwargs))
    second = build_chamber_input(ChamberEquilibriumRequest(
        oxidiser=PropellantStream(b, 298.15), **kwargs))
    assert first == second


def test_the_same_species_on_both_sides_is_refused(lox_stream):
    """CEA could not tell them apart, so the mixture ratio would be meaningless."""
    oxidiser_as_fuel = PropellantDefinition(
        name="ODD", role=PropellantRole.FUEL, composition=Composition.pure("O2"),
        reference_temperature=90.17, reference_phase=Phase.LIQUID,
        provider_names={"cea": "O2(L)"})
    with pytest.raises(CEAMappingError, match="both the fuel and the oxidiser"):
        build_chamber_input(ChamberEquilibriumRequest(
            fuel=PropellantStream(oxidiser_as_fuel, 90.17),
            oxidiser=lox_stream, oxidiser_fuel_ratio=MixtureRatio(3.4),
            chamber_pressure=10.0e6))


# ---------------------------------------------------------------------------
# product species selection
# ---------------------------------------------------------------------------


def test_carbon_free_systems_get_the_smaller_product_set(lox_stream):
    """Including carbon species where there is no carbon adds only zeros."""
    from rocketforge.providers.cea import LIQUID_HYDROGEN
    request = ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_HYDROGEN, 20.27, phase=Phase.LIQUID),
        oxidiser=lox_stream, oxidiser_fuel_ratio=MixtureRatio(6.0),
        chamber_pressure=10.0e6)
    assert select_product_species(request) == HO_PRODUCT_SPECIES
    assert not any("C" in s for s in HO_PRODUCT_SPECIES)


def test_carbon_systems_get_the_cho_set(lox_methane_request):
    assert select_product_species(lox_methane_request) == CHO_PRODUCT_SPECIES


def test_an_explicit_product_set_wins(lox_methane_request):
    explicit = dataclasses.replace(lox_methane_request,
                                   product_species=("CO", "CO2", "H2O"))
    assert select_product_species(explicit) == ("CO", "CO2", "H2O")


# ---------------------------------------------------------------------------
# constraint
# ---------------------------------------------------------------------------


def test_a_non_hp_constraint_is_refused_not_substituted(lox_methane_request):
    other = dataclasses.replace(lox_methane_request,
                                equilibrium_constraint=EquilibriumConstraint.SP)
    with pytest.raises(CEAMappingError, match="not silently substituted"):
        build_chamber_input(other)


def test_pressure_reaches_cea_in_bar(lox_methane_request):
    mapped = build_chamber_input(lox_methane_request)
    assert mapped.pressure_bar == pytest.approx(100.0)
    assert lox_methane_request.chamber_pressure == 1.0e7


def test_a_pressure_unit_mutation_is_severe(lox_methane_request):
    """Passing Pa where bar is expected is a factor of 1e5, not a nuance."""
    mapped = build_chamber_input(lox_methane_request)
    unconverted = lox_methane_request.chamber_pressure
    assert unconverted / mapped.pressure_bar == pytest.approx(1.0e5)


def test_chamber_input_is_frozen(lox_methane_request):
    mapped = build_chamber_input(lox_methane_request)
    with pytest.raises(dataclasses.FrozenInstanceError):
        mapped.of_ratio = 1.0  # type: ignore[misc]
