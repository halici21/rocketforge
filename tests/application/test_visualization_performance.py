"""The Rocket Performance 3D snapshot: made with the result, never from inputs.

The snapshot is built once per Calculate from the solved outcome. Editing an
input marks the result stale and leaves the snapshot alone; a result that is
cleared or refused leaves no drawable snapshot; and making or reading it
solves nothing.
"""
from __future__ import annotations

import math

import pytest

from rocketforge.application.analysis import performance_service
from rocketforge.application.analysis.performance_controller import RocketPerformanceController
from rocketforge.application.analysis.thermochemistry_controller import ThermochemistryController
from rocketforge.application.visualization.fidelity import Fidelity


@pytest.fixture()
def performance(qt_app, stub_gateway):
    thermo = ThermochemistryController()
    controller = RocketPerformanceController(thermo)
    thermo.calculate()
    return controller


def _station(snap, key):
    return next(s for s in snap["stations"] if s["key"] == key)


def test_no_snapshot_before_a_solve(performance):
    assert performance.viewport["valid"] is False


def test_the_snapshot_is_the_solved_area_ratio_as_a_schematic(performance):
    performance.calculate()
    assert performance.hasResult, performance.message
    snap = performance.viewport
    assert snap["valid"] and snap["fidelity"] == str(Fidelity.SCHEMATIC)
    ratio = (_station(snap, "exit")["r"] / _station(snap, "throat")["r"]) ** 2
    assert math.isclose(ratio, performance._outcome.result.exit.area_ratio, rel_tol=1e-12)
    assert snap["identity"] == performance.resultIdentity
    # LOX / LCH4 reactants are liquids: the feed cue is on; no condensed cue
    assert snap["flow"]["liquidInlet"] is True and snap["flow"]["condensed"] is False
    assert snap["hasShock"] is False and snap["choked"] is True


def test_an_edited_input_leaves_the_solved_snapshot_in_place(performance):
    performance.calculate()
    before = performance.viewport
    performance.areaRatio = performance.areaRatio * 1.5
    assert performance.resultStale
    assert performance.viewport == before


def test_reading_the_snapshot_solves_nothing(performance, monkeypatch):
    performance.calculate()
    calls = {"n": 0}
    original = performance_service.solve_performance

    def counting(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(performance_service, "solve_performance", counting)
    for _ in range(5):
        performance.viewport, performance.resultIdentity
    assert calls["n"] == 0
    performance.calculate()                     # control: the counter does see a solve
    assert calls["n"] == 1


def test_a_new_solve_is_a_new_identity_and_clearing_leaves_nothing_to_draw(performance):
    performance.calculate()
    first = performance.resultIdentity
    performance.calculate()
    assert performance.resultIdentity == first + 1
    performance.clearResult()
    assert performance.viewport["valid"] is False
