"""The real, temperature- and pressure-dependent fluid provider.

Skips with an explicit reason when CoolProp is absent -- the base environment
is *meant* to be without it, and that absence is itself asserted below. A skip
never stands in for a pass: the fluid-enabled suite is a separate gate.
"""

from __future__ import annotations

import pytest

from rocketforge.physics.fluids import (
    HYDROGEN,
    METHANE,
    OXYGEN,
    FluidError,
    FluidPhase,
    FluidProperty,
    FluidPropertyCapability,
    FluidProviderUnavailableError,
    FluidStateRequest,
    PropertyStatus,
)
from rocketforge.providers.fluid_properties import (
    coolprop_is_available,
    coolprop_provider,
)
from rocketforge.providers.fluid_properties.coolprop import (
    COOLPROP_FLUID_NAMES,
    CoolPropFluidProvider,
)

COOLPROP_PRESENT = coolprop_is_available()
requires_coolprop = pytest.mark.skipif(
    not COOLPROP_PRESENT,
    reason="CoolProp is not installed; the high-fidelity provider is optional")

ATM = 101325.0
FEED = 3.0e5


@pytest.fixture
def provider():
    return coolprop_provider()


def at(fluid, temperature, pressure=ATM, **kwargs):
    return FluidStateRequest(fluid=fluid, temperature=temperature,
                             pressure=pressure, **kwargs)


# --- optionality ----------------------------------------------------------

def test_the_adapter_module_imports_without_the_library_installed():
    import rocketforge.providers.fluid_properties.coolprop as module

    assert module.COOLPROP_BACKEND == "HEOS"


def test_availability_is_a_question_that_never_raises():
    assert coolprop_is_available() in (True, False)


@pytest.mark.skipif(COOLPROP_PRESENT,
                    reason="this test describes the CoolProp-absent world")
def test_without_the_library_the_failure_is_named_not_an_import_error():
    with pytest.raises(FluidProviderUnavailableError, match="not installed"):
        coolprop_provider().evaluate(at(OXYGEN, 90.0))


def test_importing_the_fluids_domain_does_not_import_coolprop():
    import subprocess
    import sys

    code = ("import sys; import rocketforge.physics.fluids; "
            "print('CoolProp' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                         text=True, check=True)
    assert out.stdout.strip() == "False"


# --- identity mapping -----------------------------------------------------

def test_no_provider_native_name_is_a_domain_identity():
    assert set(COOLPROP_FLUID_NAMES) == {"OXYGEN", "METHANE", "HYDROGEN"}
    assert COOLPROP_FLUID_NAMES["OXYGEN"] == "Oxygen"


def test_an_unmapped_fluid_is_refused_rather_than_guessed(provider):
    from rocketforge.physics.fluids import FluidDefinition

    argon = FluidDefinition(name="ARGON", formula="Ar", molar_mass=0.039948)
    with pytest.raises(FluidError, match="not guessed at"):
        provider.evaluate(at(argon, 90.0))


@requires_coolprop
def test_the_native_name_appears_in_provenance_and_not_in_the_domain(provider):
    result = provider.evaluate(at(OXYGEN, 90.17)).value
    assert result.provenance.native_fluid_name == "Oxygen"
    assert result.fluid.name == "OXYGEN"


# --- what it declares -----------------------------------------------------

def test_it_declares_temperature_and_pressure_dependence(provider):
    capabilities = provider.capabilities
    assert capabilities.supports(FluidPropertyCapability.TEMPERATURE_DEPENDENCE)
    assert capabilities.supports(FluidPropertyCapability.PRESSURE_DEPENDENCE)
    assert capabilities.supports(FluidPropertyCapability.SATURATION_STATE)


def test_it_declares_all_five_properties(provider):
    for prop in FluidProperty:
        assert provider.capabilities.supports_property(prop)


# --- the three production cryogens ---------------------------------------

@requires_coolprop
@pytest.mark.parametrize("fluid,temperature,expected_density", [
    (OXYGEN, 90.17, 1141.0),
    (METHANE, 111.643, 422.4),
    (HYDROGEN, 20.27, 71.0),
])
def test_each_cryogen_is_a_liquid_at_its_reference_state(
        provider, fluid, temperature, expected_density):
    result = provider.evaluate(at(fluid, temperature,
                                  required_phase=FluidPhase.LIQUID)).value
    assert result.phase is FluidPhase.LIQUID
    assert result.density == pytest.approx(expected_density, rel=2e-3)


@requires_coolprop
def test_properties_actually_move_with_temperature(provider):
    cold = provider.evaluate(at(OXYGEN, 88.0, FEED)).value
    warm = provider.evaluate(at(OXYGEN, 95.0, FEED)).value
    assert warm.density < cold.density
    assert warm.specific_enthalpy > cold.specific_enthalpy


@requires_coolprop
def test_properties_move_with_pressure_too_and_are_not_reduced_to_h_of_t(provider):
    low = provider.evaluate(at(OXYGEN, 90.17, ATM)).value
    high = provider.evaluate(at(OXYGEN, 90.17, FEED)).value
    assert high.specific_enthalpy != low.specific_enthalpy
    assert high.density != low.density


# --- phase behaviour, which is the whole reason pressure is required ------

@requires_coolprop
def test_oxygen_at_95_kelvin_is_a_gas_at_one_atmosphere(provider):
    result = provider.evaluate(at(OXYGEN, 95.0, ATM)).value
    assert result.phase is FluidPhase.GAS


@requires_coolprop
def test_the_same_oxygen_at_95_kelvin_is_a_liquid_at_three_bar(provider):
    result = provider.evaluate(at(OXYGEN, 95.0, FEED)).value
    assert result.phase is FluidPhase.LIQUID, (
        "this pair is why a fluid request has no default pressure")


@requires_coolprop
def test_a_phase_mismatch_refusal_says_how_to_fix_itself(provider):
    solution = provider.evaluate(
        at(OXYGEN, 95.0, ATM, required_phase=FluidPhase.LIQUID))
    assert solution.value is None
    diagnostic = solution.diagnostics[0]
    assert diagnostic.code == "FLUID_PHASE_MISMATCH"
    assert "liquid above" in diagnostic.message
    assert diagnostic.detail["saturation_pressure_Pa"] > ATM


@requires_coolprop
def test_a_two_phase_state_reports_ambiguity_and_no_single_value(provider):
    saturation = provider.saturation_pressure("OXYGEN", 95.0)
    solution = provider.evaluate(at(OXYGEN, 95.0, saturation))
    state = solution.value
    if state.phase is not FluidPhase.TWO_PHASE:
        pytest.skip("this state did not land exactly on the saturation line")
    assert state.values == {}
    assert all(state.status_of(p) is PropertyStatus.TWO_PHASE_AMBIGUOUS
               for p in FluidProperty)
    assert "FLUID_STATE_IS_TWO_PHASE" in {d.code for d in solution.diagnostics}


@requires_coolprop
def test_a_two_phase_state_never_silently_returns_the_liquid_branch(provider):
    saturation = provider.saturation_pressure("OXYGEN", 95.0)
    solution = provider.evaluate(at(OXYGEN, 95.0, saturation))
    state = solution.value
    if state.phase is not FluidPhase.TWO_PHASE:
        pytest.skip("this state did not land exactly on the saturation line")
    with pytest.raises(Exception):
        state.density


# --- refusals -------------------------------------------------------------

@requires_coolprop
def test_a_state_below_the_triple_point_is_refused_not_extrapolated(provider):
    solution = provider.evaluate(at(OXYGEN, 40.0, ATM))
    assert solution.value is None
    assert {d.code for d in solution.diagnostics} == {
        "FLUID_STATE_OUTSIDE_EQUATION_OF_STATE"}


@requires_coolprop
def test_the_out_of_range_refusal_names_the_range(provider):
    solution = provider.evaluate(at(OXYGEN, 40.0, ATM))
    detail = solution.diagnostics[0].detail
    assert detail["t_min"] > 0.0
    assert detail["t_max"] > detail["t_min"]


# --- units, checked by mutation ------------------------------------------

@requires_coolprop
@pytest.mark.parametrize("prop,low,high", [
    (FluidProperty.DENSITY, 1000.0, 1300.0),
    (FluidProperty.SPECIFIC_HEAT_CP, 1500.0, 1900.0),
    (FluidProperty.DYNAMIC_VISCOSITY, 1.0e-4, 3.0e-4),
    (FluidProperty.THERMAL_CONDUCTIVITY, 0.10, 0.20),
])
def test_each_property_is_in_the_si_magnitude_band_for_liquid_oxygen(
        provider, prop, low, high):
    """A x1000 or /1000 unit slip leaves this band immediately.

    The bands are wide on purpose: this is a unit check, not an accuracy check,
    and the accuracy check is the external reference comparison.
    """
    value = provider.evaluate(at(OXYGEN, 90.17)).value.value_of(prop)
    assert low < value < high
    assert not (low < value * 1000.0 < high), "the x1000 mutation must fail"
    assert not (low < value / 1000.0 < high), "the /1000 mutation must fail"


@requires_coolprop
def test_swapping_two_fluids_changes_the_answer(provider):
    """Identity mutation: the provider must not be indifferent to which fluid."""
    oxygen = provider.evaluate(at(OXYGEN, 111.643, FEED)).value
    methane = provider.evaluate(at(METHANE, 111.643, FEED)).value
    assert oxygen.density != methane.density
    assert abs(oxygen.density - methane.density) > 100.0


@requires_coolprop
def test_a_pressure_given_in_bar_by_mistake_changes_the_phase(provider):
    """1e5 Pa is 1 bar; 3.0 would be 3 Pa. The mistake must not pass silently."""
    solution = provider.evaluate(at(OXYGEN, 90.17, 3.0))
    state = solution.value
    assert state is None or state.phase is not FluidPhase.LIQUID


# --- determinism and state ------------------------------------------------

@requires_coolprop
def test_repeated_identical_queries_are_bit_identical(provider):
    first = provider.evaluate(at(OXYGEN, 90.17, FEED)).value
    for _ in range(5):
        again = provider.evaluate(at(OXYGEN, 90.17, FEED)).value
        for prop in FluidProperty:
            assert again.value_of(prop) == first.value_of(prop)


@requires_coolprop
def test_no_state_leaks_between_fluids(provider):
    a1 = provider.evaluate(at(OXYGEN, 90.17, FEED)).value.density
    b1 = provider.evaluate(at(METHANE, 111.643, FEED)).value.density
    a2 = provider.evaluate(at(OXYGEN, 90.17, FEED)).value.density
    b2 = provider.evaluate(at(METHANE, 111.643, FEED)).value.density
    a3 = provider.evaluate(at(OXYGEN, 90.17, FEED)).value.density
    assert a1 == a2 == a3
    assert b1 == b2
    assert a1 != b1, "three equal answers would also come from a stuck cache"


@requires_coolprop
def test_a_fresh_provider_agrees_with_a_used_one(provider):
    for temperature in range(85, 100):
        provider.evaluate(at(OXYGEN, float(temperature), FEED))
    used = provider.evaluate(at(OXYGEN, 90.17, FEED)).value.density
    fresh = CoolPropFluidProvider().evaluate(at(OXYGEN, 90.17, FEED)).value.density
    assert used == fresh
