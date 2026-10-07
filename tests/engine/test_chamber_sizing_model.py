"""LIQ-4: the thrust-chamber sizing records. Validation and round trip only."""

from __future__ import annotations

import math

import pytest

from rocketforge.engine.chamber_sizing import (
    SIZING_QUANTITIES,
    SIZING_SCHEMA,
    AreaRatioSource,
    OperatingPoint,
    SizingDefinition,
    SizingResult,
    SizingStatus,
    quantity_named,
)
from rocketforge.engine.requirement import RequirementFormatError

POINT = OperatingPoint(
    trade_fingerprint="f" * 64, trade_provenance={"chamber": "NASA CEA 3.0"},
    requirement_fingerprint="r" * 64, pair_key="sutton-o2-ch4", pair_label="LOX / CH4",
    oxidiser="LOX", fuel="LCH4", oxidiser_fuel_ratio=3.2, mixture_ratio_source="catalogue",
    chamber_pressure=10e6, pressure_source="study", oxidiser_temperature=90.17,
    fuel_temperature=111.643, gamma_basis="frozen", ambient_pressure=101325.0,
    thrust=1.0e6, trade_area_ratio=40.0,
    recorded={"chamber_temperature": 3500.0, "characteristic_velocity": 1850.0})


def test_every_quantity_has_a_unique_key_and_a_group():
    keys = [q.key for q in SIZING_QUANTITIES]
    assert len(keys) == len(set(keys))
    assert {q.group for q in SIZING_QUANTITIES} == {
        "flow", "geometry", "performance", "exit", "thrust"}
    assert quantity_named("throat_diameter").unit == "m"
    assert quantity_named("nope") is None


@pytest.mark.parametrize("change", [
    {"chamber_pressure": 0.0}, {"thrust": -1.0}, {"oxidiser_fuel_ratio": math.nan},
    {"ambient_pressure": -1.0}, {"ambient_pressure": 20e6}, {"gamma_basis": "shifting"},
    {"trade_area_ratio": 1.0},
])
def test_an_operating_point_refuses_an_unresolved_value(change):
    from dataclasses import replace

    with pytest.raises(ValueError):
        replace(POINT, **change)


def test_a_trade_area_ratio_must_be_the_trades():
    assert SizingDefinition(POINT, 40.0, AreaRatioSource.TRADE).area_ratio == 40.0
    with pytest.raises(ValueError):
        SizingDefinition(POINT, 25.0, AreaRatioSource.TRADE)
    with pytest.raises(ValueError):
        SizingDefinition(POINT, 0.9, AreaRatioSource.SIZING)


def test_the_fingerprint_moves_with_every_input():
    a = SizingDefinition(POINT, 40.0, AreaRatioSource.TRADE)
    b = SizingDefinition(POINT, 40.0, AreaRatioSource.SIZING)
    from dataclasses import replace

    c = SizingDefinition(replace(POINT, pair_key="sutton-o2-h2"), 40.0, AreaRatioSource.TRADE)
    assert len({a.fingerprint, b.fingerprint, c.fingerprint}) == 3
    assert a.fingerprint == SizingDefinition(POINT, 40.0, AreaRatioSource.TRADE).fingerprint


def test_a_refusal_carries_no_numbers():
    definition = SizingDefinition(POINT, 40.0, AreaRatioSource.TRADE)
    with pytest.raises(ValueError):
        SizingResult(definition, SizingStatus.REFUSED, quantities={"mass_flow": 1.0})
    with pytest.raises(ValueError):
        SizingResult(definition, SizingStatus.OK, quantities={"mass_flow": 1.0},
                     unresolved={"mass_flow": "x"})
    with pytest.raises(ValueError):
        SizingResult(definition, SizingStatus.OK, quantities={"not_a_quantity": 1.0})


def test_the_record_round_trips_through_json():
    result = SizingResult(
        SizingDefinition(POINT, 40.0, AreaRatioSource.TRADE), SizingStatus.WARNING,
        quantities={"mass_flow": 300.25, "throat_area": 0.05, "pressure_thrust": -1234.5},
        unresolved={"exit_mach": "because"}, regime="overexpanded", notes=("n",),
        assumptions=("Ideal.",), provenance={"chamber": "x"})
    text = result.to_json()
    assert f'"schema": "{SIZING_SCHEMA}"' in text
    assert SizingResult.from_json(text) == result


def test_a_foreign_or_broken_record_is_refused():
    with pytest.raises(RequirementFormatError):
        SizingResult.from_json('{"schema": "rocketforge.liquid-propellant-trade"}')
    with pytest.raises(RequirementFormatError):
        SizingResult.from_json(f'{{"schema": "{SIZING_SCHEMA}", "version": 1}}')
    with pytest.raises(RequirementFormatError):
        SizingResult.from_json("not json")
