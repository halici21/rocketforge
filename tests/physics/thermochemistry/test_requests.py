"""Request validation: malformed input is refused before any provider runs.

Phase 5B-0 measured NASA CEA accepting a negative temperature and a negative
pressure without raising, and returning. Every guard in this file exists because
of that: if RocketForge does not refuse nonsense, a provider may not either, and
the result comes back looking plausible.
"""

from __future__ import annotations

import dataclasses

import pytest

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    ChemistryMode,
    EquilibriumConstraint,
    ExpansionMode,
    ExpansionRequest,
    FreezeLocation,
    MixtureRatio,
    PropellantError,
    PropellantRoleError,
    PropellantStream,
    ThermochemistryError,
)


@pytest.fixture
def request_(methane_stream, lox_stream) -> ChamberEquilibriumRequest:
    return ChamberEquilibriumRequest(
        fuel=methane_stream, oxidiser=lox_stream,
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)


# ---------------------------------------------------------------------------
# construction and defaults
# ---------------------------------------------------------------------------


def test_request_defaults_to_hp_equilibrium(request_):
    """HP, not UV or TP.

    A rocket chamber is a steady-flow device at a pressure set by the throat,
    so enthalpy and pressure are conserved. A UV calculation would give a
    noticeably higher temperature -- right for a bomb calorimeter, wrong here.
    """
    assert request_.equilibrium_constraint is EquilibriumConstraint.HP
    assert request_.chemistry_mode is ChemistryMode.EQUILIBRIUM


def test_only_the_two_constraints_phase_5a_uses_are_exposed():
    """Providers support TP, UV, TV and SV. Exposing them all would make this
    enum a description of CEA rather than of RocketForge."""
    assert {c.value for c in EquilibriumConstraint} == {"HP", "SP"}


def test_request_uses_the_actual_stream_temperature_not_the_reference(
        lox, liquid_methane):
    """A warmed regenerative fuel is at its stream temperature, not 111.6 K."""
    warm_fuel = PropellantStream(liquid_methane, 400.0, mass_flow=1.0)
    cold_ox = PropellantStream(lox, 90.17, mass_flow=3.4)
    req = ChamberEquilibriumRequest(
        fuel=warm_fuel, oxidiser=cold_ox,
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)
    assert req.reactant_conditions["fuel_temperature"] == 400.0
    assert liquid_methane.reference_temperature == pytest.approx(111.643)


def test_reactant_conditions_shape_for_provenance(request_):
    conditions = request_.reactant_conditions
    assert conditions["oxidiser_fuel_ratio"] == pytest.approx(3.4)
    assert conditions["chamber_pressure"] == 10.0e6
    assert set(conditions) >= {"fuel_temperature", "oxidiser_temperature",
                               "oxidiser_fuel_ratio", "chamber_pressure"}


def test_request_is_frozen(request_):
    with pytest.raises(dataclasses.FrozenInstanceError):
        request_.chamber_pressure = 1.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0.0, -1.0, -1.0e6, float("nan"), float("inf")])
def test_chamber_pressure_must_be_positive_and_finite(request_, bad):
    with pytest.raises(ThermochemistryError):
        dataclasses.replace(request_, chamber_pressure=bad)


def test_swapped_streams_are_refused(request_, methane_stream, lox_stream):
    with pytest.raises(PropellantRoleError, match="may be swapped"):
        ChamberEquilibriumRequest(
            fuel=lox_stream, oxidiser=methane_stream,
            oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)


def test_a_bare_float_is_not_an_acceptable_mixture_ratio(methane_stream, lox_stream):
    """A float would carry no basis and no orientation."""
    with pytest.raises(PropellantError, match="must be a MixtureRatio"):
        ChamberEquilibriumRequest(
            fuel=methane_stream, oxidiser=lox_stream,
            oxidiser_fuel_ratio=3.4,  # type: ignore[arg-type]
            chamber_pressure=10.0e6)


def test_invalid_stream_temperature_is_caught_at_the_stream(lox):
    """The guard sits on the stream, so it fires before a request exists."""
    with pytest.raises(PropellantError):
        PropellantStream(lox, -50.0)


@pytest.mark.parametrize("bad", [0.0, 1.0, 1.5, -0.1])
def test_trace_threshold_must_be_a_proper_fraction(request_, bad):
    with pytest.raises(ThermochemistryError, match="strictly between 0 and 1"):
        dataclasses.replace(request_, trace_threshold=bad)


def test_product_species_may_be_none_meaning_provider_chooses(request_):
    """A real capability: CEA can derive products from reactants."""
    assert request_.product_species is None
    explicit = dataclasses.replace(request_, product_species=("CO", "CO2", "H2O"))
    assert explicit.product_species == ("CO", "CO2", "H2O")
    with pytest.raises(ThermochemistryError):
        dataclasses.replace(request_, product_species=())


# ---------------------------------------------------------------------------
# nothing provider-specific, nothing device-specific
# ---------------------------------------------------------------------------


def test_request_carries_no_mass_flow(request_):
    """A chamber equilibrium is set by the ratio, not the absolute rate."""
    names = {f.name for f in dataclasses.fields(request_)}
    assert "mass_flow" not in names
    assert "mdot" not in names


def test_request_carries_no_provider_flags(request_):
    """No n_frz, no iac, no ac_at, no **kwargs.

    Those are NASA CEA's control vocabulary. Phase 5B-0 catalogued them
    precisely so they could be kept in the adapter rather than leaking here.
    """
    names = {f.name for f in dataclasses.fields(request_)}
    for leaked in ("n_frz", "iac", "ac_at", "subar", "supar", "pi_p",
                   "kwargs", "options", "extra"):
        assert leaked not in names


def test_request_carries_no_geometry(request_):
    names = {f.name for f in dataclasses.fields(request_)}
    for forbidden in ("area_ratio", "throat_area", "contraction_ratio",
                      "chamber_length", "l_star"):
        assert forbidden not in names


# ---------------------------------------------------------------------------
# expansion request: a data contract only
# ---------------------------------------------------------------------------


def test_expansion_requires_exactly_one_condition():
    with pytest.raises(ThermochemistryError, match="exactly one"):
        ExpansionRequest(mode=ExpansionMode.EQUILIBRIUM)
    with pytest.raises(ThermochemistryError, match="exactly one"):
        ExpansionRequest(mode=ExpansionMode.EQUILIBRIUM,
                         pressure=1.0e5, area_ratio=40.0)
    assert ExpansionRequest(mode=ExpansionMode.EQUILIBRIUM,
                            pressure=1.0e5).pressure == 1.0e5


def test_freeze_location_is_explicit_not_a_boolean():
    """A boolean cannot express the difference, and the difference is real:
    freezing at the chamber and at the throat give different exit states."""
    assert ExpansionRequest(mode=ExpansionMode.FROZEN,
                            pressure=1.0e5).freeze_location is FreezeLocation.CHAMBER
    assert ExpansionRequest(
        mode=ExpansionMode.FROZEN_AT_THROAT,
        pressure=1.0e5).freeze_location is FreezeLocation.THROAT
    assert ExpansionRequest(mode=ExpansionMode.EQUILIBRIUM,
                            pressure=1.0e5).freeze_location is None


def test_area_ratio_below_one_is_refused():
    with pytest.raises(ThermochemistryError, match="at least 1"):
        ExpansionRequest(mode=ExpansionMode.EQUILIBRIUM, area_ratio=0.5)


def test_frozen_is_not_constant_gamma_documented():
    """The contract states it, because the confusion is common and costly.

    A frozen mixture still has a temperature-dependent cp, so gamma still
    varies along the expansion.
    """
    assert "not constant gamma" in ExpansionMode.__doc__.lower().replace(
        "is not constant gamma", "not constant gamma")
