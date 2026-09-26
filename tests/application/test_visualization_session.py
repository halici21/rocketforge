"""Selection, pinned plot snapshots and probe arithmetic.

A pinned snapshot must be immutable (editing the live chart, or the dict the
caller passed, cannot reach it), JSON-serializable, and complete; comparison
and probe differences are offered only between compatible quantities.
"""
from __future__ import annotations

import math

import pytest

from rocketforge.application.visualization import plot
from rocketforge.application.visualization.selection import AnalysisSelection
from rocketforge.application.visualization.session import MAX_SNAPSHOTS, AnalysisSession


def _snapshot(quantity="p0_over_p", unit="", y=(1.0, 8.0), identity=1, points=None):
    return {
        "source": "isentropic", "identity": identity, "quantity": quantity,
        "quantityLabel": "p_0/p", "unit": unit, "xQuantity": "mach", "xLabel": "Mach number",
        "xUnit": "", "xRange": [1.6, 2.4], "yRange": list(y), "axisMode": "log",
        "series": [{"label": "p_0/p", "points": points or [
            {"x": 1.6, "y": 4.25}, {"x": 2.0, "y": 7.82445}, {"x": 2.4, "y": 14.62}]}],
        "stale": False, "provenance": "calculated by RocketForge, gamma 1.4",
    }


@pytest.fixture()
def session(qt_app):
    return AnalysisSession()


def test_a_pinned_snapshot_is_frozen_against_the_callers_later_edits(session):
    live = _snapshot()
    sid = session.pin(live)
    assert sid == "S1"
    live["xRange"][0] = 0.1                         # the live view keeps moving
    live["series"][0]["points"][0]["y"] = -1.0
    kept = session.snapshot(sid)
    assert kept["xRange"] == [1.6, 2.4]
    assert kept["series"][0]["points"][0]["y"] == 4.25
    # and a caller that edits what it read edits nothing kept
    kept["xRange"][1] = 99.0
    assert session.snapshot(sid)["xRange"] == [1.6, 2.4]


@pytest.mark.parametrize("broken", [
    {"xRange": [2.0, 1.0]},                  # inverted range
    {"yRange": [1.0, float("inf")]},         # not finite
    {"axisMode": "weird"},
])
def test_an_incomplete_or_invalid_snapshot_is_refused_with_a_reason(session, broken):
    snap = _snapshot(); snap.update(broken)
    assert session.pin(snap) == ""
    assert session.lastError and session.count == 0


def test_a_missing_field_is_refused(session):
    snap = _snapshot(); del snap["identity"]
    assert session.pin(snap) == "" and "identity" in session.lastError


def test_the_session_is_bounded(session):
    ids = [session.pin(_snapshot(identity=i)) for i in range(MAX_SNAPSHOTS + 2)]
    assert session.count == MAX_SNAPSHOTS
    assert [s["id"] for s in session.snapshots] == ids[2:]


def test_compatible_snapshots_compare_and_incompatible_ones_say_why(session):
    a = session.pin(_snapshot(identity=1))
    b = session.pin(_snapshot(identity=2, points=[{"x": 2.0, "y": 7.5}]))
    c = session.pin(_snapshot(quantity="T0_over_T", identity=3))
    assert session.compare(a, b) == {"compatible": True, "reason": ""}
    verdict = session.compare(a, c)
    assert verdict["compatible"] is False and "different quantities" in verdict["reason"]
    delta = session.compareAt(a, b, 2.0)
    assert delta["compatible"] and delta["a"] == {"x": 2.0, "y": 7.82445}
    assert math.isclose(delta["dy"], 7.5 - 7.82445)
    assert delta["sameStation"] is True
    assert session.compareAt(a, c, 2.0)["compatible"] is False


def test_probe_delta_offers_a_percentage_only_when_meaningful():
    a = {"x": 1.0, "y": 2.0, "quantity": "q", "unit": ""}
    b = {"x": 2.0, "y": 3.0, "quantity": "q", "unit": ""}
    d = plot.probe_delta(a, b)
    assert d == {"compatible": True, "dx": 1.0, "dy": 1.0, "percent": 50.0}
    zero = dict(a, y=0.0)
    assert plot.probe_delta(zero, b)["percent"] is None
    assert plot.probe_delta(a, dict(b, quantity="other"))["compatible"] is False


def test_nearest_sample_returns_a_real_sample_never_an_interpolation():
    pts = [{"x": 1.0, "y": 10.0}, {"x": 2.0, "y": 20.0}]
    assert plot.nearest_sample(pts, 1.4) == {"x": 1.0, "y": 10.0}
    assert plot.nearest_sample(pts, 1.6) == {"x": 2.0, "y": 20.0}
    assert plot.nearest_sample([], 1.0) is None


def test_selection_is_one_object_for_every_view(qt_app):
    sel = AnalysisSelection()
    seen = []
    sel.changed.connect(lambda: seen.append((sel.kind, sel.key, sel.x)))
    sel.select("station", "throat", 0.05, "Throat", "viewport")
    assert (sel.kind, sel.key, sel.x, sel.source, sel.active) == (
        "station", "throat", 0.05, "viewport", True)
    sel.selectPoint("plotPoint", "p0_over_p", 2.0, 7.82445, "p0/p", "chart")
    assert sel.y == 7.82445 and len(seen) == 2          # one signal per selection
    sel.clear()
    assert not sel.active and math.isnan(sel.x)
    with pytest.raises(ValueError):
        sel.select("pixel", "k", 1.0, "", "")
