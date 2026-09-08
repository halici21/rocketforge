"""The reactant sensible-enthalpy correction: NASA CEA Provider v1.1.

The blocking properties, each asserted rather than described:

* at the reference state the increment is exactly zero and the corrected
  chamber is bit-identical to the native one;
* away from it the chamber moves, and native mode provably does not;
* a reactant CEA already varies with temperature is never corrected;
* no absolute fluid enthalpy ever reaches CEA.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.physics.fluids import METHANE, OXYGEN, FluidPhase
from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    MixtureRatio,
    Phase,
    PropellantStream,
)
from rocketforge.providers.cea.enthalpy_coupling import (
    CEA_REFERENCE_PRESSURE,
    ReactantEnthalpyPolicy,
    ReactantFluidBinding,
    mixture_enthalpy_correction,
    reactant_mass_fractions,
)
from rocketforge.providers.cea.errors import CEAMappingError
from rocketforge.providers.cea.mapping import CEAChamberInput, build_chamber_input
from rocketforge.providers.cea.propellants import (
    GASEOUS_METHANE,
    GASEOUS_OXYGEN,
    LIQUID_METHANE,
    LOX,
)
from rocketforge.providers.fluid_properties import (
    ConstantPropertyDefinition,
    ConstantPropertyProvider,
    coolprop_is_available,
    coolprop_provider,
)

from rocketforge.providers.cea import CEAThermochemistryProvider
from rocketforge.providers.cea.availability import check_availability

CEA_PRESENT = check_availability().is_usable

requires_both = pytest.mark.skipif(
    not (CEA_PRESENT and coolprop_is_available()),
    reason="the coupling needs both NASA CEA and CoolProp")

FEED = 3.0e5
CHAMBER = 1.0e7
T_REF_OX = 90.17
T_REF_FUEL = 111.643


def request_at(ox_t=T_REF_OX, fuel_t=T_REF_FUEL, pressure=FEED,
               ox=LOX, fuel=LIQUID_METHANE,
               ox_phase=Phase.LIQUID, fuel_phase=Phase.LIQUID):
    return ChamberEquilibriumRequest(
        fuel=PropellantStream(propellant=fuel, temperature=fuel_t,
                              pressure=pressure, phase=fuel_phase),
        oxidiser=PropellantStream(propellant=ox, temperature=ox_t,
                                  pressure=pressure, phase=ox_phase),
        oxidiser_fuel_ratio=MixtureRatio(3.4),
        chamber_pressure=CHAMBER)


def liquid_bindings(pressure=FEED):
    return {"O2(L)": ReactantFluidBinding(fluid=OXYGEN, pressure=pressure,
                                          required_phase=FluidPhase.LIQUID),
            "CH4(L)": ReactantFluidBinding(fluid=METHANE, pressure=pressure,
                                           required_phase=FluidPhase.LIQUID)}


# --- the arithmetic, with no provider at all ------------------------------

def test_mass_fractions_sum_to_one_and_match_the_of_split():
    fractions = reactant_mass_fractions((0.0, 1.0), (1.0, 0.0), 3.4)
    assert math.fsum(fractions) == pytest.approx(1.0, abs=1e-15)
    assert fractions[0] == pytest.approx(3.4 / 4.4)
    assert fractions[1] == pytest.approx(1.0 / 4.4)


def test_the_mixture_correction_is_the_mass_weighted_sum():
    assert mixture_enthalpy_correction((0.75, 0.25), (100.0, 200.0)) == 125.0


def test_a_zero_increment_gives_exactly_zero_whatever_the_weights():
    assert mixture_enthalpy_correction((0.7727, 0.2273), (0.0, 0.0)) == 0.0


def test_mismatched_lengths_are_refused():
    with pytest.raises(CEAMappingError):
        mixture_enthalpy_correction((0.5, 0.5), (1.0,))


# --- the v1.1 field is additive and defaults to v1.0 ----------------------

def test_the_correction_field_defaults_to_zero():
    chamber_input = build_chamber_input(request_at())
    assert chamber_input.enthalpy_correction == 0.0


def test_the_correction_field_is_last_so_v1_0_field_order_is_unchanged():
    names = list(CEAChamberInput.__dataclass_fields__)
    assert names[-1] == "enthalpy_correction"
    assert names[:-1] == ["reactant_names", "fuel_weights", "oxidiser_weights",
                          "reactant_temperatures", "of_ratio", "pressure_bar",
                          "product_species"]


def test_a_non_finite_correction_is_refused():
    with pytest.raises(CEAMappingError, match="finite"):
        build_chamber_input(request_at(), enthalpy_correction=float("nan"))


# --- the binding demands a pressure --------------------------------------

def test_a_binding_without_a_pressure_cannot_be_built():
    with pytest.raises(TypeError):
        ReactantFluidBinding(fluid=OXYGEN)  # type: ignore[call-arg]


def test_a_zero_pressure_binding_is_refused_and_names_the_chamber_trap():
    with pytest.raises(CEAMappingError, match="chamber pressure is a different"):
        ReactantFluidBinding(fluid=OXYGEN, pressure=0.0)


def test_the_reference_pressure_is_one_atmosphere_and_is_named():
    assert CEA_REFERENCE_PRESSURE == 101325.0


# --- a constant-property provider may not supply the increment ------------

def test_a_constant_property_provider_is_refused_for_the_correction():
    """The most dangerous possible failure, refused by name.

    A constant-property model returns the same enthalpy at both states, so the
    increment would be exactly zero -- indistinguishable from a correct
    reference-state result, and wrong everywhere else.
    """
    from rocketforge.providers.cea.enthalpy_coupling import (
        sensible_enthalpy_increment,
    )
    from rocketforge.physics.fluids import FluidProperty

    provider = ConstantPropertyProvider({"OXYGEN": ConstantPropertyDefinition(
        phase=FluidPhase.LIQUID,
        values={FluidProperty.SPECIFIC_ENTHALPY: -133398.0},
        temperature_range=(80.0, 100.0), pressure_range=(1e4, 1e6),
        source="test")})
    with pytest.raises(CEAMappingError, match="does not declare temperature"):
        sensible_enthalpy_increment(
            provider,
            ReactantFluidBinding(fluid=OXYGEN, pressure=FEED),
            "O2(L)", 95.0, 90.17)


# --- live: the blocking identities ---------------------------------------

@pytest.fixture
def coupled():
    return CEAThermochemistryProvider(), coolprop_provider()


@requires_both
def test_at_the_reference_state_every_increment_is_exactly_zero(coupled):
    provider, fluids = coupled
    solution = provider.solve_chamber(
        request_at(pressure=CEA_REFERENCE_PRESSURE),
        enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
        fluid_provider=fluids,
        reactant_bindings=liquid_bindings(CEA_REFERENCE_PRESSURE))
    corrections = [d.detail for d in solution.diagnostics
                   if d.code == "REACTANT_ENTHALPY_FLUID_CORRECTED"]
    assert len(corrections) == 2
    for detail in corrections:
        assert detail["delta_h_sensible_J_per_kg"] == 0.0


@requires_both
def test_at_the_reference_state_the_corrected_chamber_is_bit_identical(coupled):
    provider, fluids = coupled
    request = request_at(pressure=CEA_REFERENCE_PRESSURE)
    native = provider.solve_chamber(request).value
    corrected = provider.solve_chamber(
        request,
        enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
        fluid_provider=fluids,
        reactant_bindings=liquid_bindings(CEA_REFERENCE_PRESSURE)).value
    assert corrected.temperature == native.temperature
    assert corrected.gas_constant == native.gas_constant
    assert corrected.molar_mass == native.molar_mass
    assert corrected.gamma_frozen == native.gamma_frozen
    assert corrected.gamma_equilibrium == native.gamma_equilibrium


@requires_both
def test_native_mode_is_insensitive_to_the_liquid_temperature(coupled):
    provider, _ = coupled
    temperatures = {provider.solve_chamber(request_at(ox_t=t)).value.temperature
                    for t in (86.0, 90.17, 95.0, 98.0)}
    assert len(temperatures) == 1, (
        "this insensitivity is the limitation being closed; if it ever "
        "disappears on its own, something else is moving the answer")


@requires_both
def test_corrected_mode_responds_to_the_liquid_temperature(coupled):
    provider, fluids = coupled
    results = []
    for t in (86.0, 90.17, 95.0, 98.0):
        solution = provider.solve_chamber(
            request_at(ox_t=t),
            enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
            fluid_provider=fluids, reactant_bindings=liquid_bindings())
        results.append(solution.value.temperature)
    assert len(set(results)) == len(results)
    assert results == sorted(results), "warmer reactants, hotter chamber"


@requires_both
def test_a_warmer_liquid_gives_a_positive_increment(coupled):
    provider, fluids = coupled
    solution = provider.solve_chamber(
        request_at(ox_t=95.0),
        enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
        fluid_provider=fluids, reactant_bindings=liquid_bindings())
    oxidiser = next(d.detail for d in solution.diagnostics
                    if d.code == "REACTANT_ENTHALPY_FLUID_CORRECTED"
                    and d.detail["reactant"] == "O2(L)")
    assert oxidiser["delta_h_sensible_J_per_kg"] > 0.0


# --- no double counting ---------------------------------------------------

@requires_both
def test_a_gaseous_reactant_receives_no_correction_even_when_bound(coupled):
    provider, fluids = coupled
    request = request_at(ox_t=300.0, fuel_t=298.15, ox=GASEOUS_OXYGEN,
                         fuel=GASEOUS_METHANE, ox_phase=Phase.GAS,
                         fuel_phase=Phase.GAS)
    native = provider.solve_chamber(request).value
    corrected = provider.solve_chamber(
        request,
        enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
        fluid_provider=fluids,
        reactant_bindings={
            "O2": ReactantFluidBinding(fluid=OXYGEN, pressure=FEED,
                                       required_phase=FluidPhase.GAS),
            "CH4": ReactantFluidBinding(fluid=METHANE, pressure=FEED,
                                        required_phase=FluidPhase.GAS)}).value
    assert corrected.temperature == native.temperature, (
        "CEA already varies these reactants with temperature; correcting them "
        "would count the sensible term twice")


@requires_both
def test_a_gaseous_reactant_produces_no_correction_diagnostic(coupled):
    provider, fluids = coupled
    solution = provider.solve_chamber(
        request_at(ox_t=300.0, fuel_t=298.15, ox=GASEOUS_OXYGEN,
                   fuel=GASEOUS_METHANE, ox_phase=Phase.GAS,
                   fuel_phase=Phase.GAS),
        enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
        fluid_provider=fluids,
        reactant_bindings={
            "O2": ReactantFluidBinding(fluid=OXYGEN, pressure=FEED,
                                       required_phase=FluidPhase.GAS)})
    assert not [d for d in solution.diagnostics
                if d.code == "REACTANT_ENTHALPY_FLUID_CORRECTED"]


# --- the two policies stay distinct --------------------------------------

@requires_both
def test_native_mode_keeps_the_original_warning(coupled):
    provider, _ = coupled
    solution = provider.solve_chamber(request_at(ox_t=95.0))
    assert "PROVIDER_ASSIGNED_ENTHALPY_REACTANT" in {
        d.code for d in solution.diagnostics}


@requires_both
def test_corrected_mode_supersedes_that_warning_rather_than_dropping_it(coupled):
    provider, fluids = coupled
    solution = provider.solve_chamber(
        request_at(ox_t=95.0),
        enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
        fluid_provider=fluids, reactant_bindings=liquid_bindings())
    codes = {d.code for d in solution.diagnostics}
    assert "PROVIDER_ASSIGNED_ENTHALPY_REACTANT" not in codes
    assert "REACTANT_ENTHALPY_FLUID_CORRECTED" in codes


@requires_both
def test_the_policy_is_recorded_in_provenance_under_both_policies(coupled):
    provider, fluids = coupled
    native = provider.solve_chamber(request_at(ox_t=95.0))
    assert native.provenance[0].options["reactant_enthalpy_policy"] \
        == "provider_native"
    corrected = provider.solve_chamber(
        request_at(ox_t=95.0),
        enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
        fluid_provider=fluids, reactant_bindings=liquid_bindings())
    assert corrected.provenance[0].options["reactant_enthalpy_policy"] \
        == "fluid_sensible_correction"


# --- refusals -------------------------------------------------------------

@requires_both
def test_the_corrected_policy_without_a_fluid_provider_is_refused(coupled):
    provider, _ = coupled
    with pytest.raises(CEAMappingError, match="none was supplied"):
        provider.solve_chamber(
            request_at(),
            enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
            reactant_bindings=liquid_bindings())


@requires_both
def test_the_corrected_policy_without_bindings_is_refused(coupled):
    provider, fluids = coupled
    with pytest.raises(CEAMappingError, match="has no default"):
        provider.solve_chamber(
            request_at(),
            enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
            fluid_provider=fluids, reactant_bindings={})


@requires_both
def test_a_liquid_binding_at_a_pressure_where_it_is_a_gas_is_refused(coupled):
    provider, fluids = coupled
    with pytest.raises(CEAMappingError, match="could not evaluate"):
        provider.solve_chamber(
            request_at(ox_t=95.0, pressure=101325.0),
            enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
            fluid_provider=fluids, reactant_bindings=liquid_bindings(101325.0))


# --- the datum never crosses ---------------------------------------------

@requires_both
def test_the_two_enthalpy_data_are_far_apart_and_only_a_difference_crosses(coupled):
    provider, fluids = coupled
    solution = provider.solve_chamber(
        request_at(ox_t=95.0),
        enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
        fluid_provider=fluids, reactant_bindings=liquid_bindings())
    oxidiser = next(d.detail for d in solution.diagnostics
                    if d.code == "REACTANT_ENTHALPY_FLUID_CORRECTED"
                    and d.detail["reactant"] == "O2(L)")
    cea_assigned = -405608.96  # CEA's own O2(L) assigned enthalpy, J/kg
    assert abs(oxidiser["fluid_h_at_request_J_per_kg"] - cea_assigned) > 250_000.0, (
        "if these two data were ever close, an absolute injection could pass "
        "unnoticed; they differ by about 272 kJ/kg")
    assert abs(oxidiser["delta_h_sensible_J_per_kg"]) < 20_000.0, (
        "the increment is a sensible term, orders below either datum")
