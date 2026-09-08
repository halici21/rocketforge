"""The in-tree constant-property provider.

Runs in the base environment. Its job is to prove the boundary works without a
library, and -- just as importantly -- to prove it cannot be mistaken for a
real cryogenic model.
"""

from __future__ import annotations

import pytest

from rocketforge.core.result import Severity, Status
from rocketforge.physics.fluids import (
    OXYGEN,
    FluidError,
    FluidPhase,
    FluidProperty,
    FluidPropertyCapability,
    FluidStateRequest,
    PropertyStatus,
)
from rocketforge.providers.fluid_properties import (
    CONSTANT_PROPERTY_APPROXIMATION,
    ConstantPropertyDefinition,
    ConstantPropertyProvider,
)

LOX_CONSTANTS = ConstantPropertyDefinition(
    phase=FluidPhase.LIQUID,
    values={FluidProperty.DENSITY: 1141.0,
            FluidProperty.SPECIFIC_HEAT_CP: 1699.0},
    temperature_range=(80.0, 100.0),
    pressure_range=(5.0e4, 1.0e6),
    source="a fixed value for tests, not a measurement")


@pytest.fixture
def provider():
    return ConstantPropertyProvider({"OXYGEN": LOX_CONSTANTS})


def request_at(temperature=90.0, pressure=101325.0, **kwargs):
    return FluidStateRequest(fluid=OXYGEN, temperature=temperature,
                             pressure=pressure, **kwargs)


# --- what it returns ------------------------------------------------------

def test_it_returns_exactly_the_values_it_was_given(provider):
    result = provider.evaluate(request_at()).value
    assert result.density == 1141.0
    assert result.specific_heat_cp == 1699.0


def test_the_values_do_not_move_with_temperature_or_pressure(provider):
    cold = provider.evaluate(request_at(82.0, 6.0e4)).value
    warm = provider.evaluate(request_at(98.0, 9.0e5)).value
    assert cold.density == warm.density


def test_a_property_it_was_not_given_is_not_supported_never_zero(provider):
    result = provider.evaluate(request_at()).value
    assert result.status_of(FluidProperty.DYNAMIC_VISCOSITY) \
        is PropertyStatus.NOT_SUPPORTED
    assert result.optional(FluidProperty.DYNAMIC_VISCOSITY) is None


def test_a_property_not_asked_for_is_not_requested_not_unsupported(provider):
    result = provider.evaluate(
        request_at(properties=(FluidProperty.DENSITY,))).value
    assert result.status_of(FluidProperty.SPECIFIC_HEAT_CP) \
        is PropertyStatus.NOT_REQUESTED


# --- what it declares -----------------------------------------------------

def test_it_does_not_declare_temperature_or_pressure_dependence(provider):
    capabilities = provider.capabilities
    assert not capabilities.supports(
        FluidPropertyCapability.TEMPERATURE_DEPENDENCE)
    assert not capabilities.supports(
        FluidPropertyCapability.PRESSURE_DEPENDENCE)


def test_it_does_not_claim_to_locate_a_saturation_line(provider):
    assert not provider.capabilities.supports(
        FluidPropertyCapability.SATURATION_STATE)


def test_it_declares_only_the_fluids_it_was_built_with(provider):
    assert provider.capabilities.fluids == frozenset({"OXYGEN"})


# --- how it says what it is ----------------------------------------------

def test_every_result_names_the_approximation_in_its_provenance(provider):
    result = provider.evaluate(request_at()).value
    assert CONSTANT_PROPERTY_APPROXIMATION in result.provenance.approximations


def test_every_result_carries_a_warning_saying_the_state_was_ignored(provider):
    solution = provider.evaluate(request_at())
    assert solution.status is Status.OK_WITH_WARNINGS
    codes = {d.code for d in solution.diagnostics}
    assert "CONSTANT_PROPERTY_APPROXIMATION" in codes
    assert all(d.severity is Severity.WARNING for d in solution.diagnostics)


# --- what it refuses ------------------------------------------------------

def test_a_state_outside_the_envelope_is_refused_not_extrapolated(provider):
    solution = provider.evaluate(request_at(temperature=120.0))
    assert solution.value is None
    assert solution.status is Status.NO_SOLUTION
    assert {d.code for d in solution.diagnostics} == {
        "FLUID_STATE_OUTSIDE_CONSTANT_ENVELOPE"}


def test_a_fluid_it_has_no_entry_for_is_refused(provider):
    from rocketforge.physics.fluids import METHANE
    solution = provider.evaluate(FluidStateRequest(
        fluid=METHANE, temperature=110.0, pressure=101325.0))
    assert solution.value is None
    assert {d.code for d in solution.diagnostics} == {"FLUID_NOT_IN_CONSTANT_TABLE"}


def test_a_phase_mismatch_is_refused(provider):
    solution = provider.evaluate(request_at(required_phase=FluidPhase.GAS))
    assert solution.value is None
    assert {d.code for d in solution.diagnostics} == {"FLUID_PHASE_MISMATCH"}


def test_a_production_definition_must_state_its_envelope():
    with pytest.raises(FluidError, match="claiming to be an equation of state"):
        ConstantPropertyDefinition(
            phase=FluidPhase.LIQUID,
            values={FluidProperty.DENSITY: 1141.0},
            source="somewhere")


def test_a_production_definition_must_name_its_source():
    with pytest.raises(FluidError, match="unattributed constant"):
        ConstantPropertyDefinition(
            phase=FluidPhase.LIQUID,
            values={FluidProperty.DENSITY: 1141.0},
            temperature_range=(80.0, 100.0), pressure_range=(1e4, 1e6))


def test_a_test_model_may_declare_no_envelope_but_must_say_so():
    definition = ConstantPropertyDefinition(
        phase=FluidPhase.LIQUID, values={FluidProperty.DENSITY: 1.0},
        is_test_model=True)
    assert definition.covers(1.0, 1.0)


def test_an_empty_provider_is_refused_at_construction():
    with pytest.raises(FluidError, match="at least one fluid"):
        ConstantPropertyProvider({})


# --- determinism ----------------------------------------------------------

def test_repeated_identical_queries_are_bit_identical(provider):
    first = provider.evaluate(request_at()).value
    for _ in range(5):
        again = provider.evaluate(request_at()).value
        assert again.density == first.density
        assert again.temperature == first.temperature


def test_the_definitions_table_is_read_only(provider):
    with pytest.raises(TypeError):
        provider.definitions["OXYGEN"] = LOX_CONSTANTS  # type: ignore[index]
