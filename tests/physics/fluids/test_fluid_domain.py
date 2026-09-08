"""The fluid-property domain: identity, request, state, phase, capabilities.

No provider anywhere in this file. Everything here runs in the base
environment, with no CoolProp and no CEA installed, which is the point: the
domain is the part that must work without either.
"""

from __future__ import annotations

import pytest

from rocketforge.physics.fluids import (
    HYDROGEN,
    METHANE,
    OXYGEN,
    FluidDefinition,
    FluidIdentityError,
    FluidPhase,
    FluidPhaseError,
    FluidProperty,
    FluidPropertyCapabilities,
    FluidPropertyCapability,
    FluidPropertyProvenance,
    FluidRequestError,
    FluidState,
    FluidStateError,
    FluidStateRequest,
    PropertyStatus,
    UnsupportedFluidPropertyError,
    capability_for,
)

PROVENANCE = FluidPropertyProvenance(provider_id="t", provider_label="Test")


def state(values=None, statuses=None, phase=FluidPhase.LIQUID, **kwargs):
    values = {FluidProperty.DENSITY: 1141.0} if values is None else values
    if statuses is None:
        statuses = {p: (PropertyStatus.AVAILABLE if p in values
                        else PropertyStatus.NOT_SUPPORTED)
                    for p in FluidProperty}
    return FluidState(fluid=kwargs.pop("fluid", OXYGEN),
                      temperature=kwargs.pop("temperature", 90.17),
                      pressure=kwargs.pop("pressure", 101325.0),
                      phase=phase, provenance=PROVENANCE,
                      values=values, statuses=statuses)


# --- identity -------------------------------------------------------------

def test_the_three_production_fluids_carry_molar_mass_in_kg_per_mol():
    assert OXYGEN.molar_mass == pytest.approx(0.0319988)
    assert METHANE.molar_mass == pytest.approx(0.0160425)
    assert HYDROGEN.molar_mass == pytest.approx(0.00201588)


def test_a_molar_mass_in_grams_per_mole_is_refused_by_name():
    with pytest.raises(FluidIdentityError, match="g/mol"):
        FluidDefinition(name="OXYGEN", formula="O2", molar_mass=31.9988)


def test_a_lower_case_name_is_refused_so_one_substance_has_one_record():
    with pytest.raises(FluidIdentityError, match="upper case"):
        FluidDefinition(name="Oxygen", formula="O2", molar_mass=0.0319988)


def test_a_fluid_definition_carries_no_density_or_boiling_point():
    fields = set(FluidDefinition.__dataclass_fields__)
    assert fields == {"name", "formula", "molar_mass", "source"}, (
        "a definition that carried a property would be a second source of "
        "truth competing with the provider")


def test_fluid_definitions_are_immutable():
    with pytest.raises(Exception):
        OXYGEN.molar_mass = 1.0  # type: ignore[misc]


# --- phase ----------------------------------------------------------------

def test_there_is_no_unknown_phase_member():
    assert "UNKNOWN" not in FluidPhase.__members__, (
        "unknown is None, never an enum member that a required field would "
        "silently accept")


def test_two_phase_is_a_member_because_it_is_an_answer_not_an_absence():
    assert FluidPhase.TWO_PHASE in FluidPhase
    assert not FluidPhase.TWO_PHASE.is_single_phase


def test_phase_members_are_exactly_these_five():
    assert set(FluidPhase) == {
        FluidPhase.LIQUID, FluidPhase.GAS, FluidPhase.SUPERCRITICAL,
        FluidPhase.SOLID, FluidPhase.TWO_PHASE}


def test_supercritical_is_not_condensed():
    assert not FluidPhase.SUPERCRITICAL.is_condensed
    assert FluidPhase.LIQUID.is_condensed


# --- units ----------------------------------------------------------------

def test_every_property_states_its_canonical_si_unit():
    assert FluidProperty.DENSITY.unit == "kg/m^3"
    assert FluidProperty.SPECIFIC_ENTHALPY.unit == "J/kg"
    assert FluidProperty.SPECIFIC_HEAT_CP.unit == "J/(kg K)"
    assert FluidProperty.DYNAMIC_VISCOSITY.unit == "Pa s"
    assert FluidProperty.THERMAL_CONDUCTIVITY.unit == "W/(m K)"


def test_the_property_vocabulary_is_exactly_five():
    assert len(list(FluidProperty)) == 5


# --- request --------------------------------------------------------------

def test_a_request_requires_a_pressure():
    with pytest.raises(TypeError):
        FluidStateRequest(fluid=OXYGEN, temperature=90.0)  # type: ignore[call-arg]


def test_a_zero_pressure_is_refused_and_says_there_is_no_default():
    with pytest.raises(FluidRequestError, match="no default pressure"):
        FluidStateRequest(fluid=OXYGEN, temperature=90.0, pressure=0.0)


def test_a_celsius_looking_negative_temperature_is_refused():
    with pytest.raises(FluidRequestError, match="kelvin"):
        FluidStateRequest(fluid=OXYGEN, temperature=-183.0, pressure=101325.0)


def test_a_request_with_no_property_list_wants_everything():
    request = FluidStateRequest(fluid=OXYGEN, temperature=90.0, pressure=1e5)
    assert request.wants_everything
    assert all(request.wants(p) for p in FluidProperty)


def test_a_duplicated_property_is_refused():
    with pytest.raises(FluidRequestError, match="duplicate"):
        FluidStateRequest(fluid=OXYGEN, temperature=90.0, pressure=1e5,
                          properties=(FluidProperty.DENSITY,
                                      FluidProperty.DENSITY))


# --- state ----------------------------------------------------------------

def test_every_property_carries_a_status_even_when_absent():
    result = state()
    assert set(result.statuses) == set(FluidProperty)
    assert result.status_of(FluidProperty.DYNAMIC_VISCOSITY) \
        is PropertyStatus.NOT_SUPPORTED


def test_an_unavailable_property_is_not_zero_it_is_a_refusal_naming_the_reason():
    result = state()
    with pytest.raises(UnsupportedFluidPropertyError, match="not_supported"):
        result.dynamic_viscosity


def test_optional_returns_none_for_a_caller_that_handles_absence():
    assert state().optional(FluidProperty.DYNAMIC_VISCOSITY) is None


def test_a_zero_density_is_refused_because_unknown_is_not_zero():
    with pytest.raises(FluidStateError, match="Unknown is not zero"):
        state(values={FluidProperty.DENSITY: 0.0})


def test_a_negative_viscosity_is_refused():
    with pytest.raises(FluidStateError, match="not physically possible"):
        state(values={FluidProperty.DYNAMIC_VISCOSITY: -1.0})


def test_a_negative_enthalpy_is_accepted_because_its_zero_is_a_convention():
    result = state(values={FluidProperty.SPECIFIC_ENTHALPY: -133398.0})
    assert result.specific_enthalpy == -133398.0


def test_a_non_finite_property_is_refused_rather_than_stored():
    with pytest.raises(FluidStateError, match="non-finite"):
        state(values={FluidProperty.DENSITY: float("nan")})


def test_a_value_with_a_non_available_status_is_refused():
    with pytest.raises(FluidStateError, match="nobody can interpret"):
        state(values={FluidProperty.DENSITY: 1141.0},
              statuses={p: PropertyStatus.OUT_OF_RANGE for p in FluidProperty})


def test_an_available_status_with_no_value_is_refused():
    with pytest.raises(FluidStateError, match="no value"):
        state(values={},
              statuses={p: PropertyStatus.AVAILABLE for p in FluidProperty})


def test_a_missing_status_is_refused():
    with pytest.raises(FluidStateError, match="no status recorded"):
        state(values={FluidProperty.DENSITY: 1141.0},
              statuses={FluidProperty.DENSITY: PropertyStatus.AVAILABLE})


def test_state_mappings_are_read_only_after_construction():
    result = state()
    with pytest.raises(TypeError):
        result.values[FluidProperty.DENSITY] = 1.0  # type: ignore[index]
    with pytest.raises(TypeError):
        result.statuses[FluidProperty.DENSITY] = PropertyStatus.AVAILABLE  # type: ignore[index]


def test_a_state_must_carry_provenance():
    with pytest.raises(FluidStateError, match="provenance"):
        FluidState(fluid=OXYGEN, temperature=90.0, pressure=1e5,
                   phase=FluidPhase.LIQUID, provenance=None,  # type: ignore[arg-type]
                   values={}, statuses={p: PropertyStatus.NOT_SUPPORTED
                                        for p in FluidProperty})


# --- phase enforcement ----------------------------------------------------

def test_require_phase_passes_on_a_match():
    state().require_phase(FluidPhase.LIQUID)


def test_require_phase_refuses_a_gas_where_a_liquid_is_needed():
    with pytest.raises(FluidPhaseError, match="is gas"):
        state(phase=FluidPhase.GAS).require_phase(FluidPhase.LIQUID)


def test_an_unknown_phase_is_refused_and_never_assumed_to_be_the_wanted_one():
    with pytest.raises(FluidPhaseError, match="no identified phase"):
        state(phase=None).require_phase(FluidPhase.LIQUID)


def test_a_two_phase_state_does_not_satisfy_a_liquid_requirement():
    with pytest.raises(FluidPhaseError, match="is two_phase"):
        state(phase=FluidPhase.TWO_PHASE).require_phase(FluidPhase.LIQUID)


# --- capabilities ---------------------------------------------------------

def test_a_declared_absent_property_raises_rather_than_returning_zero():
    capabilities = FluidPropertyCapabilities(
        supported=frozenset({FluidPropertyCapability.DENSITY}))
    capabilities.require_property(FluidProperty.DENSITY, "t")
    with pytest.raises(UnsupportedFluidPropertyError, match="not 0 Pa s"):
        capabilities.require_property(FluidProperty.DYNAMIC_VISCOSITY, "t")


def test_each_property_maps_to_exactly_one_capability():
    mapped = {capability_for(p) for p in FluidProperty}
    assert len(mapped) == len(list(FluidProperty))


def test_an_undeclared_range_is_an_absence_of_information_not_a_claim():
    capabilities = FluidPropertyCapabilities()
    assert capabilities.temperature_is_in_range(1.0e6)
    assert capabilities.pressure_is_in_range(1.0e12)


def test_a_descending_range_is_refused():
    from rocketforge.physics.fluids import FluidError
    with pytest.raises(FluidError, match="ascending"):
        FluidPropertyCapabilities(temperature_range=(300.0, 100.0))


# --- the serialisable view ------------------------------------------------

def test_as_mapping_names_the_unit_of_every_value():
    view = dict(state().as_mapping())
    assert view["units"]["density"] == "kg/m^3"
    assert view["phase"] == "liquid"
    assert view["provenance"]["provider_id"] == "t"


def test_as_mapping_reports_an_unknown_phase_as_none_not_as_gas():
    assert dict(state(phase=None).as_mapping())["phase"] is None
