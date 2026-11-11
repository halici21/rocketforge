"""The Reference Cases controller: it computes only on Run, keeps nothing, and publishes what the view formats.

The runner and the provider's availability are injected, so the states are
tested with no provider and no real value. One CEA-gated test runs the real
four points and checks structure only; no computed value is pinned (DB-4C §8).
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from rocketforge.application.analysis import reference_case_controller as module
from rocketforge.application.analysis import reference_case_view as view
from rocketforge.application.analysis import reference_ideal_case as ideal
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.reference_case_controller import ReferenceCaseController
from rocketforge.application.analysis.reference_ideal_case import IdealCaseOutcome, ReductionRow
from rocketforge.comparison import ObservedQuantity, compare

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(not _STATUS.usable, reason=f"NASA CEA provider unavailable ({_STATUS.status})")
POINTS = ideal.POINTS
USABLE = SimpleNamespace(usable=True, headline="NASA CEA 3.0", detail="", remedy="")
MISSING = SimpleNamespace(usable=False, headline="NASA CEA unavailable", detail="not installed",
                          remedy="install the cea package")


def ok_outcome(point, scale=1.01):
    observed = {q.key: ObservedQuantity(q.key, q.value * scale, q.unit) for q in point.case.quantities}
    step_b = (ReductionRow("frozen", "frozen", 470.0, 458.0, 470.0 / 458.0 - 1, "both in vacuum, p_a = 0",
                           "model difference"),
              ReductionRow("equilibrium", "equilibrium", 501.0, 485.0, 501.0 / 485.0 - 1,
                           "both in vacuum, p_a = 0", "model difference"))
    return IdealCaseOutcome(ideal.KIND_OK, point, ideal.chamber_case(point), step_a=compare(point.case, observed),
                            step_b=step_b, declarations=ideal.declarations(point), warnings=())


def stopped_outcome(point, kind=ideal.KIND_REFUSED, message="chamber: refused for the test"):
    return IdealCaseOutcome(kind, point, ideal.chamber_case(point), declarations=ideal.declarations(point),
                            message=message)


def controller(outcomes=None, availability=USABLE):
    calls = []

    def runner():
        calls.append(1)
        return outcomes if outcomes is not None else tuple(ok_outcome(p) for p in POINTS)

    return ReferenceCaseController(runner=runner, availability=lambda: availability), calls


def test_nothing_is_computed_until_run():
    ctl, calls = controller()
    assert calls == [] and not ctl.hasRun
    rows = ctl.rows()
    assert {r["pointState"] for r in rows["browser"]} == {"not-run"}
    assert {r["computed"] for r in rows["step_a"]} == {view.NOT_RUN}
    assert rows["step_b"] == [] and rows["warnings"] == []
    assert ctl.inputsHeading == "To be run at"
    assert ctl.runSummary.startswith("Not run")
    for _ in range(len(POINTS)):
        ctl.select((ctl.selectedIndex + 1) % len(POINTS))
    assert calls == []


def test_before_a_run_every_points_printout_and_declarations_are_shown():
    ctl, _ = controller()
    for index, point in enumerate(POINTS):
        ctl.select(index)
        rows = ctl.rows()
        assert len(rows["step_a"]) == 3 and all("as printed" in r["printed"] for r in rows["step_a"])
        assert [r["line"] for r in rows["declarations"]] == list(ideal.declarations(point))
        assert [r["line"] for r in rows["missing"]] == list(point.case.missing)
        assert ctl.pointTitle == point.case.title and ctl.citation == point.case.source
        assert ctl.notes == point.case.notes


def test_run_computes_every_point_once_and_publishes_both_steps():
    ctl, calls = controller()
    ctl.run()
    assert calls == [1] and ctl.hasRun and not ctl.busy
    rows = ctl.rows()
    assert {r["pointState"] for r in rows["browser"]} == {"ok"}
    assert {r["kind"] for r in rows["step_a"]} == {"compared"}
    assert [r["basis"] for r in rows["step_b"]] == ["frozen", "equilibrium"]
    assert rows["warnings"] == [{"line": "none"}]
    assert ctl.inputsHeading == "Run at" and not ctl.stopped and ctl.stopMessage == ""
    assert ctl.runSummary.startswith("Last run: 4 computed of 4 points")


def test_each_run_recomputes_and_keeps_nothing_from_the_last():
    first = tuple(ok_outcome(p, 1.01) for p in POINTS)
    second = tuple(ok_outcome(p, 0.98) for p in POINTS)
    batches = iter((first, second))
    ctl = ReferenceCaseController(runner=lambda: next(batches), availability=lambda: USABLE)
    ctl.run()
    before = ctl.rows()["step_a"]
    ctl.run()
    after = ctl.rows()["step_a"]
    assert [r["computed"] for r in before] != [r["computed"] for r in after]
    assert after == view.step_a_rows(POINTS[0], second[0].step_a)


@pytest.mark.parametrize("failing", range(4))
def test_a_stopped_point_shows_its_reason_in_place_of_both_tables(failing):
    outcomes = tuple(stopped_outcome(p) if i == failing else ok_outcome(p) for i, p in enumerate(POINTS))
    ctl, _ = controller(outcomes)
    ctl.run()
    for index in range(len(POINTS)):
        ctl.select(index)
        rows = ctl.rows()
        if index == failing:
            assert ctl.stopped and ctl.stopMessage == "Refused: chamber: refused for the test"
            assert rows["step_a"] == [] and rows["step_b"] == [] and rows["warnings"] == []
            assert rows["declarations"], "declarations stay visible"
        else:
            assert not ctl.stopped and len(rows["step_a"]) == 3 and len(rows["step_b"]) == 2
    assert [r["pointState"] for r in ctl.rows()["browser"]] == [
        "refused" if i == failing else "ok" for i in range(len(POINTS))]
    assert "3 computed, 1 refused" in ctl.runSummary


def test_an_unavailable_provider_is_named_and_the_printout_stays():
    outcomes = tuple(stopped_outcome(p, ideal.KIND_UNAVAILABLE, "CEA frozen expansion: not installed")
                     for p in POINTS)
    ctl, _ = controller(outcomes, MISSING)
    assert not ctl.providerUsable
    assert ctl.providerLine == "NASA CEA unavailable: not installed install the cea package"
    ctl.run()
    assert ctl.pointStateWord == "Unavailable" and ctl.stopMessage.startswith("Unavailable: ")
    assert ctl.rows()["inputs"], "what would be run is still stated"


def test_availability_is_not_asked_until_the_page_reads_it():
    asked = []
    ctl = ReferenceCaseController(runner=lambda: (), availability=lambda: asked.append(1) or USABLE)
    assert asked == []
    assert ctl.providerUsable and asked == [1]
    assert ctl.providerLine == "NASA CEA 3.0 available" and asked == [1]


def test_selection_ignores_an_index_out_of_range():
    ctl, _ = controller()
    ctl.select(7)
    ctl.select(-1)
    assert ctl.selectedIndex == 0


def test_the_controller_imports_no_provider_at_module_level():
    source = inspect.getsource(module)
    head = source.split("class ReferenceCaseController", 1)[0]
    for name in ("rocketforge.providers", "thermochemistry_provider", "performance_oracle"):
        assert name not in head, name


@requires_cea
def test_a_real_run_of_every_point_is_published_complete_and_unjudged():
    ctl = ReferenceCaseController()
    ctl.run()
    assert {r["pointState"] for r in ctl.rows()["browser"]} == {"ok"}
    for index in range(len(POINTS)):
        ctl.select(index)
        rows = ctl.rows()
        assert {r["kind"] for r in rows["step_a"]} == {"compared"}
        assert {r["kind"] for r in rows["step_b"]} == {"model difference"}
        assert all(view.NOT_RUN not in r["computed"] for r in rows["step_a"])
