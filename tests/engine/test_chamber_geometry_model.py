"""LIQ-5 data: the throat basis, the definition and the persisted record."""

from __future__ import annotations

import json
import math
from dataclasses import replace

import pytest

from rocketforge.engine.chamber_geometry import (
    GEOMETRY_QUANTITIES,
    GEOMETRY_SCHEMA,
    GeometryDefinition,
    GeometryResult,
    GeometryStatus,
    ThroatBasis,
)
from rocketforge.engine.requirement import RequirementFormatError

BASIS = ThroatBasis(
    sizing_fingerprint="a" * 64, sizing_status="warning",
    sizing_provenance={"chamber": "NASA CEA 3.0"}, trade_fingerprint="b" * 64,
    pair_key="sutton-o2-ch4", pair_label="Oxygen / Methane", chamber_pressure=10e6,
    thrust=1e6, area_ratio=40.0, throat_area=0.0676281, throat_diameter=0.293440)
DEFINITION = GeometryDefinition(BASIS, 1.0, 3.0, math.radians(25.0))


def result(**changes):
    values = {q.key: float(i) + 0.125 for i, q in enumerate(GEOMETRY_QUANTITIES)}
    base = GeometryResult(definition=DEFINITION, status=GeometryStatus.OK, quantities=values,
                          notes=("n",), assumptions=("a",), provenance={"geometry": "x"})
    return replace(base, **changes)


def test_every_quantity_has_a_unique_key_and_a_group():
    keys = [q.key for q in GEOMETRY_QUANTITIES]
    assert len(keys) == len(set(keys))
    assert {q.group for q in GEOMETRY_QUANTITIES} == {
        "inputs", "chamber", "converging", "lengths", "closure"}


@pytest.mark.parametrize("change", [
    {"throat_area": 0.0}, {"throat_area": math.nan}, {"throat_diameter": -1.0},
    {"thrust": 0.0}, {"chamber_pressure": math.inf}, {"area_ratio": 1.0},
    {"sizing_status": "refused"},
])
def test_a_throat_basis_refuses_what_an_accepted_sizing_cannot_hold(change):
    with pytest.raises(ValueError):
        replace(BASIS, **change)


@pytest.mark.parametrize("name", ["characteristic_length", "contraction_ratio",
                                  "converging_half_angle"])
def test_a_definition_refuses_a_value_that_is_not_a_number(name):
    with pytest.raises(ValueError):
        replace(DEFINITION, **{name: math.nan})


def test_the_fingerprint_moves_with_every_input_and_the_throat():
    seen = {DEFINITION.fingerprint}
    for changed in (replace(DEFINITION, characteristic_length=1.1),
                    replace(DEFINITION, contraction_ratio=3.5),
                    replace(DEFINITION, converging_half_angle=math.radians(30.0)),
                    replace(DEFINITION, basis=replace(BASIS, throat_area=0.07)),
                    replace(DEFINITION, basis=replace(BASIS, sizing_fingerprint="c" * 64))):
        assert changed.fingerprint not in seen
        seen.add(changed.fingerprint)
    assert GeometryDefinition(BASIS, 1.0, 3.0, math.radians(25.0)).fingerprint == DEFINITION.fingerprint


def test_a_refusal_carries_no_numbers():
    with pytest.raises(ValueError):
        result(status=GeometryStatus.REFUSED)
    refused = GeometryResult(definition=DEFINITION, status=GeometryStatus.REFUSED,
                             unresolved={q.key: "why" for q in GEOMETRY_QUANTITIES},
                             message="why")
    assert not refused.ok and refused.value("chamber_volume") is None
    with pytest.raises(ValueError):
        result(unresolved={"chamber_volume": "x"})
    with pytest.raises(ValueError):
        result(quantities={"wall_thickness": 1.0})


def test_the_record_round_trips_deterministically():
    record = result()
    text = record.to_json()
    assert GeometryResult.from_json(text) == record
    assert GeometryResult.from_json(text).to_json() == text
    payload = json.loads(text)
    assert payload["schema"] == GEOMETRY_SCHEMA and payload["version"] == 1
    assert payload["definition_fingerprint"] == DEFINITION.fingerprint
    assert payload["definition"]["throat_basis"]["throat_area_m2"] == 0.0676281
    assert payload["definition"]["converging_half_angle_rad"] == math.radians(25.0)
    assert payload["definition"]["throat_basis"]["sizing_provenance"] == {
        "chamber": "NASA CEA 3.0"}


def test_a_foreign_broken_or_tampered_record_is_refused():
    payload = json.loads(result().to_json())
    for broken in ({**payload, "schema": "rocketforge.liquid-thrust-chamber-sizing"},
                   {**payload, "version": 2},
                   {k: v for k, v in payload.items() if k != "definition"}):
        with pytest.raises(RequirementFormatError):
            GeometryResult.from_dict(broken)
    tampered = json.loads(json.dumps(payload))
    tampered["definition"]["characteristic_length_m"] = 2.0
    with pytest.raises(RequirementFormatError, match="fingerprint"):
        GeometryResult.from_dict(tampered)
    with pytest.raises(RequirementFormatError):
        GeometryResult.from_json("not json")
    with pytest.raises(RequirementFormatError):
        GeometryResult.from_json("[]")
