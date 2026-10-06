"""LIQ-3: the propellant trade data model.

A definition holds only resolved values and says where each came from; a
result holds one row per candidate in definition order, failures included;
selection is explicit and only of a successful row; everything round-trips.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.engine.propellant_trade import (
    TRADE_METRICS,
    CandidateResult,
    CandidateStatus,
    MixtureRatioSource,
    PerformanceBasis,
    PressureSource,
    TradeDefinition,
    TradeResult,
    metric_named,
)
from rocketforge.engine.requirement import EngineRequirement, RequirementFormatError

REQ = EngineRequirement(thrust=1e5, burn_time=100.0)


def definition(**changes) -> TradeDefinition:
    base = dict(requirement=REQ, candidates=("a", "b"), chamber_pressure=1e7,
                pressure_source=PressureSource.STUDY,
                mixture_ratio_source=MixtureRatioSource.CATALOGUE, mixture_ratio=None,
                performance_basis=PerformanceBasis.CHAMBER_ONLY, area_ratio=None,
                gamma_basis="frozen")
    base.update(changes)
    return TradeDefinition(**base)


def row(key: str, status=CandidateStatus.OK, **metrics) -> CandidateResult:
    unresolved = {} if status is not CandidateStatus.FAILED else \
        {m.key: "failed" for m in TRADE_METRICS}
    return CandidateResult(key=key, label=key.upper(), oxidiser="LOX", fuel="LCH4",
                           oxidiser_fuel_ratio=3.0, chamber_pressure=1e7,
                           oxidiser_temperature=90.17, fuel_temperature=111.643,
                           status=status, metrics=metrics, unresolved=unresolved,
                           message="boom" if status is CandidateStatus.FAILED else "")


def test_the_metric_catalogue_has_no_score():
    keys = [m.key for m in TRADE_METRICS]
    assert len(keys) == len(set(keys))
    assert not {k for k in keys if "score" in k or "rank" in k or "best" in k}
    assert {m.tier for m in TRADE_METRICS} == {"chamber", "performance", "flow"}
    assert metric_named("specific_impulse").unit == "s"
    assert metric_named("nope") is None


@pytest.mark.parametrize("changes", [
    {"candidates": ()},
    {"chamber_pressure": 0.0},
    {"chamber_pressure": math.nan},
    {"mixture_ratio": 3.0},                                     # catalogue carries none
    {"mixture_ratio_source": MixtureRatioSource.STUDY},         # study needs a number
    {"mixture_ratio_source": MixtureRatioSource.STUDY, "mixture_ratio": -1.0},
    {"performance_basis": PerformanceBasis.IDEAL_AREA_RATIO},   # needs an area ratio
    {"area_ratio": 40.0},                                       # chamber-only has none
    {"performance_basis": PerformanceBasis.IDEAL_AREA_RATIO, "area_ratio": 1.0},
    {"gamma_basis": "average"},
])
def test_a_definition_never_holds_an_unresolved_value(changes):
    with pytest.raises(ValueError):
        definition(**changes)


def test_the_fingerprint_follows_the_question_not_the_requirement_name():
    a = definition()
    assert a.fingerprint == definition(requirement=REQ.replace(name="x")).fingerprint
    assert a.fingerprint != definition(chamber_pressure=2e7).fingerprint
    assert a.fingerprint != definition(gamma_basis="equilibrium").fingerprint


def test_a_result_keeps_one_row_per_candidate_in_order_failures_included():
    d = definition()
    result = TradeResult(d, (row("a", chamber_temperature=3500.0),
                             row("b", CandidateStatus.FAILED)))
    assert [c.ok for c in result.candidates] == [True, False]
    with pytest.raises(ValueError):
        TradeResult(d, (row("b"), row("a")))
    with pytest.raises(ValueError):
        TradeResult(d, (row("a"),))


def test_a_metric_is_valued_or_unresolved_never_both_and_never_unknown():
    with pytest.raises(ValueError):
        CandidateResult(key="a", label="A", oxidiser="", fuel="", oxidiser_fuel_ratio=1.0,
                        chamber_pressure=1.0, oxidiser_temperature=None,
                        fuel_temperature=None, status=CandidateStatus.OK,
                        metrics={"chamber_temperature": 1.0},
                        unresolved={"chamber_temperature": "x"})
    with pytest.raises(ValueError):
        row("a", overall_score=1.0)


def test_selection_is_explicit_and_only_of_a_successful_candidate():
    result = TradeResult(definition(), (row("a"), row("b", CandidateStatus.FAILED)))
    assert result.selected == ""
    chosen = result.with_selection("a")
    assert chosen.selected == "a" and result.selected == ""        # immutable
    with pytest.raises(ValueError):
        result.with_selection("b")
    with pytest.raises(ValueError):
        result.with_selection("zzz")
    assert chosen.with_selection("").selected == ""


def test_round_trip_is_exact():
    d = definition(performance_basis=PerformanceBasis.IDEAL_AREA_RATIO, area_ratio=40.0,
                   mixture_ratio_source=MixtureRatioSource.STUDY, mixture_ratio=2.5)
    result = TradeResult(d, (row("a", chamber_temperature=3500.0, mass_flow=12.5),
                             row("b", CandidateStatus.FAILED)),
                         provenance={"chamber": "stub"}).with_selection("a")
    assert TradeResult.from_json(result.to_json()) == result
    assert result.to_dict()["definition_fingerprint"] == d.fingerprint


@pytest.mark.parametrize("text", ["{", "[]", '{"schema": "other"}',
                                  '{"schema": "rocketforge.liquid-propellant-trade", "version": 9}'])
def test_a_malformed_trade_record_is_refused(text):
    with pytest.raises(RequirementFormatError):
        TradeResult.from_json(text)
