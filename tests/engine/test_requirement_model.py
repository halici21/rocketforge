"""LIQ-2: the liquid-engine requirement domain model.

Covers the states and rules of :mod:`rocketforge.engine.requirement`: what is
complete, what is an open decision, what is refused, how feed architecture and
power cycle stay separate, and that a requirement round-trips through its JSON
record exactly -- inconsistent ones included, because loading must never
repair what a file says.
"""

from __future__ import annotations

import dataclasses
import json
import math

import pytest

from rocketforge.engine.requirement import (
    SCHEMA,
    SCHEMA_VERSION,
    STANDARD_SEA_LEVEL_PRESSURE,
    AmbientMode,
    ChamberPressureMode,
    ChamberPressurePreference,
    CyclePreference,
    DesignEnvironment,
    DesignPriority,
    EngineRequirement,
    FeedArchitecture,
    MixtureRatioMode,
    MixtureRatioPreference,
    PropellantMode,
    PropellantPreference,
    RequirementFormatError,
    validate_requirement,
)


def codes(requirement: EngineRequirement) -> list[str]:
    return [issue.code for issue in validate_requirement(requirement)]


def complete(**changes) -> EngineRequirement:
    """A minimal complete requirement: stated quantities, every preference open."""
    base = EngineRequirement(thrust=100e3, burn_time=150.0)
    return base.replace(**changes)


FULL = EngineRequirement(
    name="Upper stage",
    thrust=1.0e6,
    environment=DesignEnvironment(AmbientMode.CUSTOM, 2.5e3),
    burn_time=380.0,
    propellant=PropellantPreference(PropellantMode.EXPLICIT, "sutton-o2-ch4"),
    chamber_pressure=ChamberPressurePreference(ChamberPressureMode.TARGET, 30e6),
    mixture_ratio=MixtureRatioPreference(MixtureRatioMode.PAIR_REFERENCE),
    feed=FeedArchitecture.PUMP_FED,
    cycle=CyclePreference.FULL_FLOW_STAGED_COMBUSTION,
    priority=DesignPriority.SPECIFIC_IMPULSE,
)


# ---------------------------------------------------------------------------
# the empty form and the minimal complete requirement
# ---------------------------------------------------------------------------


def test_the_default_requirement_states_nothing_and_decides_nothing():
    requirement = EngineRequirement()
    assert requirement.thrust is None and requirement.burn_time is None
    assert codes(requirement) == ["THRUST_MISSING", "BURN_TIME_MISSING"]
    assert not requirement.is_complete
    assert requirement.open_decisions() == (
        "propellant", "chamber_pressure", "mixture_ratio", "feed")
    assert requirement.cycle is None            # feed undecided: no cycle at all


def test_open_decisions_do_not_make_a_requirement_incomplete():
    requirement = complete()
    assert requirement.is_complete and requirement.issues() == ()
    assert len(requirement.open_decisions()) == 4


def test_a_fully_specified_requirement_is_complete_and_has_one_open_decision():
    assert FULL.is_complete, FULL.issues()
    assert FULL.open_decisions() == ()
    assert FULL.replace(cycle=CyclePreference.AUTO).open_decisions() == ("cycle",)


def test_the_requirement_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        FULL.thrust = 1.0                       # type: ignore[misc]


# ---------------------------------------------------------------------------
# quantities
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [0.0, -1.0, math.inf, math.nan])
def test_thrust_must_be_positive_and_finite(value):
    assert codes(complete(thrust=value)) == ["THRUST_INVALID"]


@pytest.mark.parametrize("value", [0.0, -5.0, math.inf, math.nan])
def test_burn_time_must_be_positive_and_finite(value):
    assert codes(complete(burn_time=value)) == ["BURN_TIME_INVALID"]


def test_the_environment_is_an_ambient_pressure():
    assert DesignEnvironment(AmbientMode.VACUUM, 7.0).ambient_pressure == 0.0
    assert DesignEnvironment(AmbientMode.SEA_LEVEL, 7.0).ambient_pressure == 101325.0
    assert DesignEnvironment(AmbientMode.CUSTOM, 7.0).ambient_pressure == 7.0
    assert STANDARD_SEA_LEVEL_PRESSURE == 101325.0
    # vacuum is the pressure zero, a valid custom value, not an error
    assert complete(environment=DesignEnvironment(AmbientMode.CUSTOM, 0.0)).is_complete


@pytest.mark.parametrize("value", [-1.0, math.inf, math.nan])
def test_a_custom_ambient_pressure_must_be_finite_and_not_negative(value):
    requirement = complete(environment=DesignEnvironment(AmbientMode.CUSTOM, value))
    assert codes(requirement) == ["AMBIENT_PRESSURE_INVALID"]


def test_a_named_environment_ignores_a_bad_stored_custom_value():
    """Switching to vacuum keeps what was typed, and does not judge it."""
    requirement = complete(environment=DesignEnvironment(AmbientMode.VACUUM, -1.0))
    assert requirement.is_complete


# ---------------------------------------------------------------------------
# preferences
# ---------------------------------------------------------------------------


def test_an_explicit_pair_needs_a_key():
    requirement = complete(propellant=PropellantPreference(PropellantMode.EXPLICIT, " "))
    assert codes(requirement) == ["PROPELLANT_PAIR_MISSING"]


def test_the_domain_does_not_judge_catalogue_membership():
    """The engine layer cannot see the LIQ-1 catalogue; the application checks it."""
    requirement = complete(propellant=PropellantPreference(PropellantMode.EXPLICIT, "nope"))
    assert requirement.is_complete


@pytest.mark.parametrize("mode", [ChamberPressureMode.TARGET, ChamberPressureMode.UPPER_LIMIT])
def test_a_chamber_pressure_intent_needs_a_value_above_ambient(mode):
    assert codes(complete(chamber_pressure=ChamberPressurePreference(mode))) == [
        "CHAMBER_PRESSURE_MISSING"]
    for bad in (0.0, -1.0, math.nan):
        assert codes(complete(chamber_pressure=ChamberPressurePreference(mode, bad))) == [
            "CHAMBER_PRESSURE_INVALID"]
    at_ambient = complete(chamber_pressure=ChamberPressurePreference(mode, 101325.0))
    assert codes(at_ambient) == ["CHAMBER_PRESSURE_NOT_ABOVE_AMBIENT"]
    in_vacuum = at_ambient.replace(environment=DesignEnvironment(AmbientMode.VACUUM))
    assert in_vacuum.is_complete


def test_auto_chamber_pressure_carries_no_value_requirement():
    requirement = complete(chamber_pressure=ChamberPressurePreference(
        ChamberPressureMode.AUTO, None))
    assert requirement.is_complete


def test_mixture_ratio_rules():
    explicit = MixtureRatioMode.EXPLICIT
    assert codes(complete(mixture_ratio=MixtureRatioPreference(explicit))) == [
        "MIXTURE_RATIO_MISSING"]
    assert codes(complete(mixture_ratio=MixtureRatioPreference(explicit, 0.0))) == [
        "MIXTURE_RATIO_INVALID"]
    assert complete(mixture_ratio=MixtureRatioPreference(explicit, 3.4)).is_complete
    reference = complete(mixture_ratio=MixtureRatioPreference(MixtureRatioMode.PAIR_REFERENCE))
    assert codes(reference) == ["MIXTURE_RATIO_REFERENCE_WITHOUT_PAIR"]


def test_a_pair_reference_stores_no_number():
    """The O/F stays the catalogue's; the requirement cannot hold a stale copy."""
    assert FULL.mixture_ratio.value is None
    assert FULL.to_dict()["mixture_ratio"] == {"mode": "pair_reference", "value": None}


# ---------------------------------------------------------------------------
# feed architecture and power cycle
# ---------------------------------------------------------------------------


def test_feed_architecture_and_cycle_are_separate_vocabularies():
    feeds = {member.value for member in FeedArchitecture}
    cycles = {member.value for member in CyclePreference}
    assert feeds == {"auto", "pressure_fed", "pump_fed"}
    assert cycles == {"auto", "gas_generator", "expander", "staged_combustion",
                      "full_flow_staged_combustion"}
    assert not any("pressure" in cycle for cycle in cycles), "pressure-fed is not a cycle"


def test_with_feed_keeps_the_cycle_consistent():
    pump = complete().with_feed(FeedArchitecture.PUMP_FED)
    assert pump.cycle is CyclePreference.AUTO and pump.is_complete
    chosen = pump.replace(cycle=CyclePreference.EXPANDER)
    assert chosen.with_feed(FeedArchitecture.PUMP_FED) is chosen     # no change, no reset
    for feed in (FeedArchitecture.PRESSURE_FED, FeedArchitecture.AUTO):
        left = chosen.with_feed(feed)
        assert left.cycle is None and left.is_complete


def test_a_cycle_without_a_pump_fed_engine_is_refused():
    for feed in (FeedArchitecture.PRESSURE_FED, FeedArchitecture.AUTO):
        requirement = complete(feed=feed, cycle=CyclePreference.GAS_GENERATOR)
        assert codes(requirement) == ["CYCLE_WITHOUT_PUMP_FEED"]


def test_a_pump_fed_engine_needs_a_cycle_preference_even_if_auto():
    assert codes(complete(feed=FeedArchitecture.PUMP_FED)) == ["CYCLE_MISSING"]


def test_full_flow_staged_combustion_is_recordable_intent():
    """Recorded like any cycle: valid, round-trips, and no model is implied."""
    assert FULL.cycle is CyclePreference.FULL_FLOW_STAGED_COMBUSTION and FULL.is_complete
    assert EngineRequirement.from_json(FULL.to_json()).cycle is \
        CyclePreference.FULL_FLOW_STAGED_COMBUSTION
    fields = {field.name for field in dataclasses.fields(EngineRequirement)}
    assert not fields & {"preburner", "turbine_power", "mass_flow", "throat_area",
                         "expansion_ratio", "pump_power"}


# ---------------------------------------------------------------------------
# serialisation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("requirement", [
    EngineRequirement(),
    complete(),
    FULL,
    complete(feed=FeedArchitecture.PRESSURE_FED, cycle=CyclePreference.EXPANDER),
    complete(thrust=-3.0, environment=DesignEnvironment(AmbientMode.CUSTOM, -2.0)),
])
def test_round_trip_is_exact(requirement):
    assert EngineRequirement.from_dict(requirement.to_dict()) == requirement
    text = requirement.to_json()
    assert EngineRequirement.from_json(text) == requirement
    assert json.loads(text)["schema"] == SCHEMA
    assert json.loads(text)["version"] == SCHEMA_VERSION


def test_loading_reports_an_inconsistent_record_rather_than_repairing_it():
    record = complete().to_dict()
    record["feed"] = "pressure_fed"
    record["cycle"] = "gas_generator"
    loaded = EngineRequirement.from_dict(record)
    assert loaded.cycle is CyclePreference.GAS_GENERATOR
    assert codes(loaded) == ["CYCLE_WITHOUT_PUMP_FEED"]


def test_the_record_is_plain_json_in_si_units():
    record = FULL.to_dict()
    assert record["thrust_N"] == 1.0e6 and record["burn_time_s"] == 380.0
    assert record["chamber_pressure"]["value_Pa"] == 30e6
    assert record["environment"] == {"mode": "custom", "custom_pressure_Pa": 2.5e3}
    assert record["propellant"] == {"mode": "explicit", "pair_key": "sutton-o2-ch4"}
    json.dumps(record, allow_nan=False)


@pytest.mark.parametrize("mutate, fragment", [
    (lambda r: r.update(schema="something.else"), "schema"),
    (lambda r: r.update(version=2), "version"),
    (lambda r: r.update(feed="turbo"), "FeedArchitecture"),
    (lambda r: r.update(cycle="nuclear"), "CyclePreference"),
    (lambda r: r["environment"].update(mode="mars"), "AmbientMode"),
    (lambda r: r.update(thrust_N="lots"), "thrust_N"),
    (lambda r: r.update(thrust_N=True), "thrust_N"),
    (lambda r: r.pop("propellant"), "propellant"),
    (lambda r: r.update(environment=3), "environment"),
    (lambda r: r["propellant"].update(pair_key=7), "pair_key"),
])
def test_a_malformed_record_is_refused(mutate, fragment):
    record = FULL.to_dict()
    mutate(record)
    with pytest.raises(RequirementFormatError, match=fragment):
        EngineRequirement.from_dict(record)


def test_text_that_is_not_json_is_refused():
    with pytest.raises(RequirementFormatError):
        EngineRequirement.from_json("{not json")
    with pytest.raises(RequirementFormatError):
        EngineRequirement.from_json("[1, 2]")


def test_the_fingerprint_follows_content_not_the_name():
    assert FULL.fingerprint == FULL.replace(name="Renamed").fingerprint
    assert FULL.fingerprint != FULL.replace(thrust=1.1e6).fingerprint
    assert "name" not in FULL.canonical()
    assert len(FULL.fingerprint) == 64
