"""The Trade Study controller: workload preview, chunked execution, re-analysis.

Two claims here that the service tests cannot make, because they are claims
about the workspace rather than about the engine:

**The preview is the truth.** The point count and chamber-solve count shown
before Run are the numbers the run actually produces. A preview that were
merely indicative would be worse than none.

**A decision edit through the Qt surface costs zero provider calls.** The
service tests prove it for the functions; these prove it for the controls a
person actually touches.
"""

from __future__ import annotations

import pytest

from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.performance_controller import (
    RocketPerformanceController,
)
from rocketforge.application.analysis.thermochemistry_controller import (
    ThermochemistryController,
)
from rocketforge.application.analysis.trade_study_controller import (
    BEST_WORDING,
    TradeStudyController,
)
from rocketforge.engine.studies import MAX_STUDY_POINTS

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status})")


@pytest.fixture()
def controllers(qt_app, stub_gateway):
    thermo = ThermochemistryController()
    performance = RocketPerformanceController(thermo)
    study = TradeStudyController(thermo, performance)
    return thermo, performance, study


@pytest.fixture()
def study(controllers):
    _, _, controller = controllers
    controller.setVariableEnabled("oxidiser_fuel_ratio", True)
    controller.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 41)
    controller.setVariableEnabled("area_ratio", True)
    controller.setVariableRange("area_ratio", 10.0, 80.0, 4)
    return controller


def _run(controller) -> None:
    """Drive the chunked runner to completion, as the event loop would."""
    controller.runStudy()
    guard = 0
    while controller.busy and guard < 100_000:
        controller._advance()
        guard += 1
    assert not controller.busy


# ===========================================================================
# setup and preview
# ===========================================================================


def test_the_baseline_is_available_from_the_two_workspaces(controllers):
    _, _, controller = controllers
    assert controller.baselineAvailable
    assert "O/F" in controller.baselineHeadline


def test_a_controller_with_no_sources_has_no_baseline(qt_app):
    controller = TradeStudyController()
    assert not controller.baselineAvailable
    assert not controller.definitionValid
    assert controller.definitionCode == "NO_BASELINE"


def test_the_baseline_names_the_gamma_basis(controllers):
    """Two fronts on two bases are not comparable; the page must say which."""
    _, _, controller = controllers
    labels = " ".join(row["label"] for row in controller.baselineRows)
    assert "Gamma strategy and basis" in labels


def test_the_deferred_variables_are_published_with_their_reasons(controllers):
    _, _, controller = controllers
    rows = controller.deferredVariables
    assert rows
    for row in rows:
        assert row["label"] and len(row["reason"]) > 60


def test_the_workload_preview_matches_what_the_run_costs(study, stub_gateway):
    points = study.pointCount
    solves = study.chemistrySolveCount
    assert (points, solves) == (164, 41)

    _run(study)
    assert len(stub_gateway.calls) == solves
    summary = {row["label"]: row["value"] for row in study.summaryRows}
    assert summary["Design points"] == f"{points:,}"
    assert summary["Chamber solves"] == f"{solves:,}"


def test_the_preview_updates_without_running_anything(study, stub_gateway):
    """Editing a range must not cost a solve."""
    before = len(stub_gateway.calls)
    for count in (5, 11, 41, 80):
        study.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, count)
        assert study.chemistrySolveCount == count
    assert len(stub_gateway.calls) == before


def test_the_workload_note_says_what_the_planner_saved(study):
    note = study.workloadNote
    assert "164 design points" in note
    assert "41 unique chamber solves" in note
    assert "avoided" in note


def test_a_nozzle_only_study_costs_one_chamber_solve(study, stub_gateway):
    study.setVariableEnabled("oxidiser_fuel_ratio", False)
    assert study.chemistrySolveCount == 1
    _run(study)
    assert len(stub_gateway.calls) == 1


def test_the_point_cap_is_published(controllers):
    _, _, controller = controllers
    assert controller.maximumPoints == MAX_STUDY_POINTS


def test_an_oversized_study_is_refused_before_running(study, stub_gateway):
    study.setVariableEnabled("chamber_pressure", True)
    study.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 100)
    study.setVariableRange("chamber_pressure", 5.0e6, 20.0e6, 100)
    study.setVariableRange("area_ratio", 10.0, 80.0, 100)
    before = len(stub_gateway.calls)

    assert not study.definitionValid
    assert study.definitionCode == "STUDY_TOO_LARGE"
    study.runStudy()
    assert not study.busy
    assert len(stub_gateway.calls) == before


def test_an_ineffective_variable_is_refused_with_an_explanation(study):
    study.setOutputSelected("characteristic_velocity", False)
    study.setOutputSelected("chamber_temperature", True)
    study.removeObjective("specific_impulse")
    assert not study.definitionValid
    assert study.definitionCode == "INEFFECTIVE_DESIGN_VARIABLE"
    assert "identical rows" in study.definitionMessage


# ===========================================================================
# running
# ===========================================================================


def test_a_completed_study_publishes_a_table(study, stub_gateway):
    _run(study)
    assert study.hasResult and study.resultComplete
    assert study.visibleRowCount == 164
    assert study.resultsModel.rowCount() == 164
    assert study.resultColumns


def test_the_table_columns_cover_variables_metrics_and_verdicts(study):
    _run(study)
    keys = {column["key"] for column in study.resultColumns}
    assert {"oxidiser_fuel_ratio", "area_ratio"} <= keys
    assert "specific_impulse" in keys
    assert {"status", "feasibility"} <= keys


def test_a_filter_hides_rows_without_removing_them(study):
    _run(study)
    total = study.visibleRowCount
    study.filterMode = "pareto"
    assert study.visibleRowCount <= total
    study.filterMode = "all"
    assert study.visibleRowCount == total


def test_editing_the_setup_marks_the_result_stale(study):
    _run(study)
    assert not study.resultStale
    study.setVariableRange("oxidiser_fuel_ratio", 2.0, 5.0, 41)
    assert study.resultStale


def test_cancelling_keeps_partial_results_and_no_decision_analysis(
        study, stub_gateway):
    study.runStudy()
    for _ in range(3):
        study._advance()
    study.cancelStudy()
    while study.busy:
        study._advance()

    assert study.studyStatus == "cancelled"
    assert not study.resultComplete
    assert study.visibleRowCount > 0
    assert not study.paretoAvailable
    assert "cancelled" in study.message.lower()


# ===========================================================================
# decision edits cost nothing
# ===========================================================================


def test_changing_an_objective_direction_costs_no_provider_call(study,
                                                                stub_gateway):
    _run(study)
    before = len(stub_gateway.calls)
    study.setObjectiveDirection("specific_impulse", "minimize")
    assert len(stub_gateway.calls) == before
    assert study.hasResult


def test_adding_an_objective_costs_no_provider_call(study, stub_gateway):
    _run(study)
    before = len(stub_gateway.calls)
    study.addObjective("chamber_temperature", "minimize")
    assert len(stub_gateway.calls) == before
    assert study.paretoAvailable


def test_adding_a_constraint_costs_no_provider_call(study, stub_gateway):
    _run(study)
    before = len(stub_gateway.calls)
    study.addConstraint("chamber_temperature", "<=", 3000.0)
    assert len(stub_gateway.calls) == before
    summary = {row["label"]: row["value"] for row in study.summaryRows}
    assert summary["Infeasible"] != "0"


def test_enabling_scoring_costs_no_provider_call_and_moves_no_front(
        study, stub_gateway):
    _run(study)
    study.addObjective("chamber_temperature", "minimize")
    before_front = tuple(
        row["index"] for row in study.paretoSeries[2]["points"])
    before = len(stub_gateway.calls)

    study.setProperty("scoringEnabled", True)
    study.setWeight("specific_impulse", 99.0)
    study.setWeight("chamber_temperature", 0.01)

    after_front = tuple(row["index"] for row in study.paretoSeries[2]["points"])
    assert len(stub_gateway.calls) == before
    assert after_front == before_front


def test_scoring_is_off_by_default(controllers):
    _, _, controller = controllers
    assert not controller.scoringEnabled


def test_the_scoring_note_says_the_score_is_population_relative(controllers):
    _, _, controller = controllers
    note = controller.scoringNote.lower()
    assert "relative to this" in note
    assert "never changes a raw value" in note


def test_the_weight_rows_show_the_typed_and_the_applied_weight(study):
    study.setProperty("scoringEnabled", True)
    study.setWeight("specific_impulse", 3.0)
    rows = {row["metric"]: row for row in study.weightRows}
    assert rows["specific_impulse"]["weight"] == 3.0
    assert rows["specific_impulse"]["effective"]


# ===========================================================================
# Pareto and best-point wording
# ===========================================================================


def test_one_objective_offers_no_front_and_says_why(study):
    _run(study)
    assert not study.paretoAvailable
    assert "no trade-off" in study.rankingNote.lower()


def test_two_objectives_produce_three_labelled_series(study):
    _run(study)
    study.addObjective("chamber_temperature", "minimize")
    series = study.paretoSeries
    assert [s["key"] for s in series] == ["dominated", "excluded", "efficient"]
    for entry in series:
        assert entry["label"] and entry["marker"]


def test_the_pareto_note_calls_the_points_samples(study):
    _run(study)
    study.addObjective("chamber_temperature", "minimize")
    note = study.paretoNote.lower()
    assert "sample" in note
    assert "not a point on a continuous curve" in note


def test_a_third_objective_makes_the_note_say_the_plot_is_a_projection(study):
    """The interpretation error this note exists to prevent."""
    _run(study)
    study.addObjective("chamber_temperature", "minimize")
    study.addObjective("thrust_coefficient", "maximize")
    note = study.paretoNote.lower()
    assert "all 3 objectives" in note
    assert "projection" in note or "look dominated" in note


def test_the_axis_selectors_are_bound_to_the_axes_they_control(study):
    """A control that shows option zero while the plot uses another lies."""
    _run(study)
    study.addObjective("chamber_temperature", "minimize")
    options = [row["key"] for row in study.objectiveAxisOptions]
    assert options[study.paretoXIndex] == study.paretoX
    assert options[study.paretoYIndex] == study.paretoY
    assert study.paretoX != study.paretoY


def test_the_axis_titles_are_labels_not_metric_keys(study):
    _run(study)
    study.addObjective("chamber_temperature", "minimize")
    assert study.paretoXTitle != study.paretoX
    assert "Isp" in study.paretoXTitle or "Isp" in study.paretoYTitle


def test_the_best_rows_never_claim_a_global_optimum(study):
    _run(study)
    rows = study.bestRows
    assert rows
    for row in rows:
        assert row["wording"] == BEST_WORDING
        assert "optimum" not in row["objective"].lower()
    assert "evaluated" in BEST_WORDING.lower()


def test_no_published_string_claims_a_global_optimum(study):
    """A wording audit over everything this controller publishes."""
    _run(study)
    study.addObjective("chamber_temperature", "minimize")
    meta = type(study).staticMetaObject
    banned = ("global optimum", "globally optimal", "optimal design",
              "the optimum", "guaranteed")
    for index in range(meta.propertyCount()):
        value = meta.property(index).read(study)
        text = str(value).lower()
        for phrase in banned:
            assert phrase not in text, (meta.property(index).name(), phrase)


# ===========================================================================
# compare
# ===========================================================================


def test_at_most_four_designs_can_be_compared(study):
    _run(study)
    for index in range(10):
        study.toggleSelection(index)
    assert len(study.selectedIndices) == study.maximumComparisons == 4


def test_a_compare_column_shows_raw_physics_above_the_score(study):
    _run(study)
    study.setProperty("scoringEnabled", True)
    study.toggleSelection(0)
    column = study.compareColumns[0]
    groups = [row["group"] for row in column["rows"]]
    assert groups.index("Physics") < groups.index("Decision")
    labels = [row["label"] for row in column["rows"]]
    assert "Specific impulse  Isp" in labels


def test_a_violated_constraint_is_reported_with_its_value(study):
    _run(study)
    study.addConstraint("chamber_temperature", "<=", 3000.0)
    for point in range(164):
        study.toggleSelection(point)
        if study.selectedViolations:
            break
    assert study.selectedViolations
    assert "3000" in study.selectedViolations[0]["text"]


# ===========================================================================
# audits
# ===========================================================================


def test_no_property_hands_qml_a_domain_object(study):
    """QML receives text, numbers, plain maps and the table model."""
    _run(study)
    from PySide6.QtCore import QObject

    meta = type(study).staticMetaObject
    allowed = (str, bool, int, float, list, dict, type(None), QObject)
    for index in range(meta.propertyCount()):
        value = meta.property(index).read(study)
        assert isinstance(value, allowed), meta.property(index).name()
        if isinstance(value, list):
            for item in value:
                assert isinstance(item, (str, dict, int)), \
                    meta.property(index).name()


def test_the_controller_holds_no_physics_constant():
    import ast
    import inspect

    from rocketforge.application.analysis import trade_study_controller

    source = inspect.getsource(trade_study_controller)
    for banned in ("9.80665", "8314", "101325", "math.sqrt", "math.pow"):
        assert banned not in source, banned
    tree = ast.parse(source)
    names = {node.attr for node in ast.walk(tree)
             if isinstance(node, ast.Attribute)}
    assert "sqrt" not in names


def test_the_controller_implements_no_decision_algorithm():
    """Pareto, scoring and constraint checking all live in engine.studies."""
    import ast
    import inspect

    from rocketforge.application.analysis import trade_study_controller

    tree = ast.parse(inspect.getsource(trade_study_controller))
    defined = {node.name for node in ast.walk(tree)
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for banned in ("dominates", "pareto_membership", "normalize_objective",
                   "score_points", "evaluate_constraints"):
        assert banned not in defined, banned


@requires_cea
def test_a_live_study_through_the_controller_costs_41_chamber_solves(qt_app):
    thermo = ThermochemistryController()
    performance = RocketPerformanceController(thermo)
    controller = TradeStudyController(thermo, performance)
    controller.setVariableRange("oxidiser_fuel_ratio", 2.5, 4.5, 41)
    controller.setVariableRange("area_ratio", 10.0, 80.0, 4)

    _run(controller)

    summary = {row["label"]: row["value"] for row in controller.summaryRows}
    assert summary["Design points"] == "164"
    assert summary["Chamber solves"] == "41"
    assert summary["Failed"] == "0"
