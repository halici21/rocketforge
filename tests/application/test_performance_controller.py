"""The Rocket Performance controller: the Qt surface and the invalidation rules.

Two things are checked here that the service tests cannot check, because they
are properties of the workspace rather than of the calculation:

* moving a control on this page costs zero chamber solves *through the real
  controller*, not just through the service function; and
* when the chamber underneath changes, the result on screen is marked as
  belonging to a superseded chamber instead of being silently recomputed or
  silently relabelled.
"""

from __future__ import annotations

import re

import pytest

from rocketforge.application.analysis import performance_service as service
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.performance_controller import (
    RocketPerformanceController,
)
from rocketforge.application.analysis.thermochemistry_controller import (
    ThermochemistryController,
)

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status})")


@pytest.fixture()
def thermo(qt_app, stub_gateway):
    """The upstream workspace, wired to a provider that records its calls."""
    return ThermochemistryController()


@pytest.fixture()
def controller(thermo):
    return RocketPerformanceController(thermo)


@pytest.fixture()
def solved(controller, thermo):
    """A controller with a chamber solved and a performance result computed."""
    thermo.calculate()
    controller.calculate()
    assert controller.hasResult, controller.message
    return controller


# ===========================================================================
# the upstream chamber
# ===========================================================================


def test_a_controller_with_no_source_reports_no_chamber(qt_app):
    controller = RocketPerformanceController()
    assert not controller.hasChamber
    assert controller.chamberRows == []
    assert "chamber equilibrium" in controller.chamberMissingMessage.lower()


def test_no_chamber_yet_says_where_to_get_one(controller):
    assert not controller.hasChamber
    message = controller.chamberMissingMessage
    assert message
    assert "estimated in its place" in message


def test_a_solved_chamber_becomes_available_without_being_asked(controller, thermo):
    assert not controller.hasChamber
    thermo.calculate()
    assert controller.hasChamber


def test_the_chamber_rows_show_both_gammas(controller, thermo):
    """A reader judging an Isp needs to see which exponent is on offer."""
    thermo.calculate()
    labels = " ".join(row["label"] for row in controller.chamberRows)
    assert "T_0" in labels
    assert "gamma_s" in labels
    assert "cp/cv" in labels


def test_the_chamber_headline_comes_from_the_upstream_case(controller, thermo):
    thermo.calculate()
    assert "O/F" in controller.chamberHeadline


def test_calculating_without_a_chamber_refuses_rather_than_crashing(controller):
    controller.calculate()
    assert controller.statusKind == service.OUTCOME_NO_CHAMBER
    assert not controller.hasResult
    assert controller.resultGroups == []


# ===========================================================================
# inputs
# ===========================================================================


def test_the_defaults_are_the_service_defaults(controller):
    assert controller.gammaStrategy == service.DEFAULT_PERFORMANCE_CASE.gamma_strategy.value
    assert controller.gammaBasis == service.DEFAULT_PERFORMANCE_CASE.gamma_basis.value
    assert controller.areaRatio == service.DEFAULT_PERFORMANCE_CASE.area_ratio
    assert controller.ambientMode == "vacuum"
    assert controller.scaleMode == "normalized"


def test_setting_the_area_ratio_takes_effect(controller):
    controller.areaRatio = 25.0
    assert controller.areaRatio == 25.0


@pytest.mark.parametrize("bad", [0.0, -3.0, float("nan"), float("inf")])
def test_a_bad_area_ratio_is_ignored_rather_than_stored(controller, bad):
    controller.areaRatio = bad
    assert controller.areaRatio == service.DEFAULT_PERFORMANCE_CASE.area_ratio


def test_an_unknown_gamma_basis_is_ignored(controller):
    controller.gammaBasis = "made-up"
    assert controller.gammaBasis == "frozen"


def test_the_gamma_basis_note_changes_with_the_basis(controller):
    frozen = controller.gammaBasisNote
    controller.gammaBasis = "equilibrium"
    assert controller.gammaBasisNote != frozen
    assert "shifting" in controller.gammaBasisNote.lower()


def test_ambient_presets_report_the_pressure_they_will_use(controller):
    assert controller.effectiveAmbientPressure == 0.0
    controller.ambientMode = "sea_level"
    assert controller.effectiveAmbientPressure == 101325.0
    controller.ambientMode = "custom"
    controller.ambientPressure = 2500.0
    assert controller.effectiveAmbientPressure == 2500.0


def test_switching_to_a_preset_keeps_the_typed_custom_value(controller):
    controller.ambientMode = "custom"
    controller.ambientPressure = 4321.0
    controller.ambientMode = "vacuum"
    assert controller.effectiveAmbientPressure == 0.0
    assert controller.ambientPressure == 4321.0


def test_a_negative_ambient_pressure_is_ignored(controller):
    controller.ambientMode = "custom"
    controller.ambientPressure = -1.0
    assert controller.ambientPressure >= 0.0


def test_zero_is_an_accepted_ambient_pressure(controller):
    """Vacuum is a value, not a missing input."""
    controller.ambientMode = "custom"
    controller.ambientPressure = 0.0
    assert controller.ambientPressure == 0.0
    assert controller.effectiveAmbientPressure == 0.0


def test_choosing_a_scale_mode_offers_a_starting_size(controller):
    assert not controller.scaleNeedsValue
    controller.scaleMode = "throat_area"
    assert controller.scaleNeedsValue
    assert controller.scaleValue > 0.0
    assert controller.scaleUnit == "m²"


def test_returning_to_normalized_drops_the_size(controller):
    controller.scaleMode = "throat_area"
    controller.scaleMode = "normalized"
    assert not controller.scaleNeedsValue
    assert controller.scaleUnit == ""


def test_the_scale_value_is_ignored_while_normalized(controller):
    controller.scaleValue = 5.0
    assert controller.scaleValue == 0.0


def test_resetting_restores_every_input(controller):
    controller.areaRatio = 7.0
    controller.ambientMode = "sea_level"
    controller.scaleMode = "mass_flow"
    controller.resetInputs()
    assert controller.areaRatio == service.DEFAULT_PERFORMANCE_CASE.area_ratio
    assert controller.ambientMode == "vacuum"
    assert controller.scaleMode == "normalized"


def test_every_option_list_is_non_empty_and_carries_a_note(controller):
    for options in (controller.gammaStrategyOptions, controller.gammaBasisOptions,
                    controller.ambientOptions, controller.scaleOptions,
                    controller.oracleModes):
        assert options
        for option in options:
            assert option["key"] and option["label"] and option["note"]


# ===========================================================================
# results
# ===========================================================================


def test_a_solved_result_publishes_grouped_rows(solved):
    groups = solved.resultGroups
    assert len(groups) >= 3
    titles = [group["title"] for group in groups]
    assert service.GROUP_CHAMBER in titles
    assert service.GROUP_TOTAL in titles
    for group in groups:
        assert group["note"]
        assert group["rows"]


def test_every_published_row_is_a_string_not_a_number(solved):
    """Formatting happens once, here, and QML receives text."""
    for group in solved.resultGroups:
        for row in group["rows"]:
            assert isinstance(row["value"], str), row["label"]


def test_the_unscaled_result_has_no_engine_group_and_says_why(solved):
    titles = [group["title"] for group in solved.resultGroups]
    assert service.GROUP_ENGINE not in titles
    assert "withheld rather than defaulted" in solved.unscaledNote


def test_scaling_adds_the_engine_group(solved):
    solved.scaleMode = "throat_area"
    solved.scaleValue = 0.01
    solved.calculate()
    titles = [group["title"] for group in solved.resultGroups]
    assert service.GROUP_ENGINE in titles
    assert solved.scaled
    assert solved.unscaledNote == ""


def test_the_identity_panel_reports_a_count_and_a_verdict(solved):
    assert solved.identitiesPassed
    assert re.match(r"^\d+ of \d+", solved.identitySummary)
    assert solved.identityRows
    assert all(row["passed"] for row in solved.identityRows)


def test_the_identity_summary_does_not_claim_agreement_with_reality(solved):
    """Internal consistency is not validation, and the wording says so."""
    assert "not a check against reality" in solved.identitySummary


def test_the_provenance_keeps_two_rows(solved):
    rows = solved.provenanceRows
    assert len(rows) == 2
    assert rows[0]["computed_by"] == "RocketForge"
    assert rows[1]["computed_by"] != "RocketForge"


def test_clearing_removes_the_result_but_not_the_chamber(solved):
    solved.clearResult()
    assert not solved.hasResult
    assert solved.hasChamber
    assert solved.resultGroups == []


def test_editing_an_input_marks_the_result_stale_without_changing_it(solved):
    before = solved.resultGroups
    solved.areaRatio = 12.0
    assert solved.resultStale
    assert solved.resultGroups == before      # the numbers did not move


def test_the_result_headline_is_not_relabelled_by_a_later_edit(solved):
    before = solved.resultHeadline
    solved.areaRatio = 12.0
    assert solved.resultHeadline == before
    assert "Ae/At 12" not in solved.resultHeadline
    assert "Ae/At 12" in solved.caseHeadline    # the form did move


def test_recalculating_clears_the_stale_flag(solved):
    solved.areaRatio = 12.0
    assert solved.resultStale
    solved.calculate()
    assert not solved.resultStale
    assert "Ae/At 12" in solved.resultHeadline


# ===========================================================================
# upstream invalidation
# ===========================================================================


def test_a_fresh_result_is_not_superseded(solved):
    assert not solved.chamberSuperseded


def test_a_new_chamber_supersedes_the_result_without_recomputing_it(solved, thermo):
    before = solved.resultGroups
    thermo.mixtureRatio = 3.8
    thermo.calculate()
    assert solved.chamberSuperseded
    assert solved.resultGroups == before          # not silently recomputed
    assert solved.hasResult                       # not silently discarded


def test_a_superseded_result_keeps_its_own_chamber_in_the_headline(solved, thermo):
    before = solved.resultHeadline
    thermo.mixtureRatio = 3.8
    thermo.calculate()
    assert solved.resultHeadline == before


def test_recalculating_adopts_the_new_chamber(solved, thermo):
    thermo.mixtureRatio = 3.8
    thermo.calculate()
    solved.calculate()
    assert not solved.chamberSuperseded
    assert "O/F 3.8" in solved.resultHeadline


def test_clearing_the_chamber_supersedes_the_result(solved, thermo):
    thermo.clearResult()
    assert solved.chamberSuperseded
    assert not solved.hasChamber
    assert solved.hasResult          # the old answer is kept, and marked


def test_an_upstream_change_emits_the_signals_the_view_binds_to(solved, thermo):
    seen = []
    solved.resultChanged.connect(lambda: seen.append("result"))
    solved.chamberChanged.connect(lambda: seen.append("chamber"))
    thermo.calculate()
    assert "result" in seen and "chamber" in seen


# ===========================================================================
# ZERO CHEMISTRY RE-SOLVE, through the real controller
# ===========================================================================


def test_the_first_chamber_solve_is_the_only_one_the_baseline_counts(
        controller, thermo, stub_gateway):
    assert stub_gateway.calls == []
    thermo.calculate()
    assert len(stub_gateway.calls) == 1


@pytest.mark.parametrize("apply", [
    pytest.param(lambda c: setattr(c, "areaRatio", 8.0), id="area-ratio"),
    pytest.param(lambda c: setattr(c, "ambientMode", "sea_level"),
                 id="ambient-mode"),
    pytest.param(lambda c: setattr(c, "ambientPressure", 7000.0),
                 id="ambient-pressure"),
    pytest.param(lambda c: setattr(c, "scaleMode", "throat_area"), id="scale-mode"),
    pytest.param(lambda c: setattr(c, "gammaBasis", "equilibrium"),
                 id="gamma-basis"),
    pytest.param(lambda c: setattr(c, "gammaStrategy", "throat"),
                 id="gamma-strategy"),
])
def test_changing_an_input_and_recalculating_costs_zero_chamber_solves(
        solved, stub_gateway, apply):
    """Section 80, the blocking requirement, through the Qt surface."""
    baseline = len(stub_gateway.calls)
    assert baseline == 1
    apply(solved)
    solved.calculate()
    assert len(stub_gateway.calls) == baseline


def test_a_whole_session_of_control_changes_costs_zero_chamber_solves(
        solved, stub_gateway):
    baseline = len(stub_gateway.calls)
    solved.scaleMode = "throat_area"
    for ratio in (5.0, 15.0, 45.0):
        for mode in ("vacuum", "sea_level"):
            solved.areaRatio = ratio
            solved.ambientMode = mode
            solved.scaleValue = ratio / 1000.0
            solved.calculate()
            assert solved.hasResult, solved.message
    assert len(stub_gateway.calls) == baseline


def test_reading_every_published_property_costs_zero_chamber_solves(
        solved, stub_gateway):
    """No property getter may lazily solve anything."""
    baseline = len(stub_gateway.calls)
    meta = type(solved).staticMetaObject
    for index in range(meta.propertyCount()):
        meta.property(index).read(solved)
    assert len(stub_gateway.calls) == baseline


def test_the_spy_would_notice_a_real_chemistry_re_solve(solved, thermo,
                                                        stub_gateway):
    """The negative control: the counter is not vacuously constant."""
    baseline = len(stub_gateway.calls)
    thermo.calculate()
    assert len(stub_gateway.calls) == baseline + 1


# ===========================================================================
# the provider's own performance -- explicit, and never the implementation
# ===========================================================================


def test_the_oracle_does_not_run_by_itself(solved, stub_gateway):
    assert solved.oracleStatus == "empty"
    assert solved.oracleRows == []
    assert solved.oracleComparisonRows == []


def test_running_the_oracle_without_a_chamber_does_nothing(controller):
    controller.runOracle()
    assert controller.oracleStatus == "empty"


def test_an_unknown_oracle_mode_is_ignored(controller):
    controller.oracleMode = "made-up"
    assert controller.oracleMode == "equilibrium"


def test_every_oracle_mode_is_offered_with_its_meaning(controller):
    keys = {option["key"] for option in controller.oracleModes}
    assert keys == {"equilibrium", "frozen", "frozen_at_throat"}
    for option in controller.oracleModes:
        assert "model difference" in option["note"] or option["note"]


@requires_cea
def test_the_oracle_returns_the_providers_own_numbers(qt_app):
    thermo = ThermochemistryController()
    thermo.calculate()
    controller = RocketPerformanceController(thermo)
    controller.calculate()
    controller.runOracle()
    assert controller.oracleStatus == "ok", controller.oracleMessage
    labels = [row["label"] for row in controller.oracleRows]
    assert any("c*" in label for label in labels)
    assert any("Isp" in label for label in labels)


@requires_cea
def test_the_comparison_is_labelled_a_model_difference_not_an_error(qt_app):
    thermo = ThermochemistryController()
    thermo.calculate()
    controller = RocketPerformanceController(thermo)
    controller.calculate()
    controller.runOracle()
    rows = controller.oracleComparisonRows
    assert rows
    for row in rows:
        assert row["kind"] == "model difference"
        assert row["reference"]
    note = controller.oracleComparisonNote.lower()
    assert "model difference" in note
    assert "error" in note                 # it says what it is *not*


@requires_cea
def test_the_comparison_matches_the_reference_condition_on_both_sides(qt_app):
    """A vacuum figure beside an optimum-expansion one is wrong by the
    whole pressure term -- larger than any model difference shown here."""
    thermo = ThermochemistryController()
    thermo.calculate()
    controller = RocketPerformanceController(thermo)
    controller.calculate()
    controller.runOracle()
    references = {row["label"]: row["reference"]
                  for row in controller.oracleComparisonRows}
    assert any("optimum expansion" in text for text in references.values())
    assert any("vacuum" in text for text in references.values())
    for label, text in references.items():
        if "c*" not in label:
            assert "both" in text, (label, text)


@requires_cea
def test_the_oracle_goes_stale_when_the_area_ratio_moves(qt_app):
    thermo = ThermochemistryController()
    thermo.calculate()
    controller = RocketPerformanceController(thermo)
    controller.calculate()
    controller.runOracle()
    assert not controller.oracleStale
    controller.areaRatio = 12.0
    assert controller.oracleStale


def test_the_oracle_reports_an_absent_provider_without_failing(controller, thermo,
                                                               absent_gateway):
    """The workspace still works with no chemistry library installed."""
    controller.runOracle()
    assert controller.oracleStatus in ("empty", "unavailable")


# ===========================================================================
# audits
# ===========================================================================


def test_no_property_hands_qml_a_physics_object(controller, thermo):
    """QML receives text, numbers, plain maps, and row models. Never a domain
    record.

    Row models were added when it was established that re-reading a
    QVariantList property from a binding retains memory unboundedly (see
    QML_MEMORY_ROOT_CAUSE.md). A RowListModel is a presentation adapter holding
    formatted strings, not a physics object -- so it is admitted by NAME AND
    TYPE rather than by relaxing this rule to "any QObject", and its contents
    are checked by the same standard as a list property's. A ChamberOutcome
    hidden inside a model would still fail.
    """
    from rocketforge.application.rowmodel import RowListModel

    thermo.calculate()
    controller.calculate()
    meta = type(controller).staticMetaObject
    allowed = (str, bool, int, float, list, dict, type(None))
    for index in range(meta.propertyCount()):
        name = meta.property(index).name()
        value = meta.property(index).read(controller)
        if isinstance(value, RowListModel):
            assert name.endswith("Model"), name
            for row in value.rows():
                assert isinstance(row, dict), name
                for field in row.values():
                    assert isinstance(field, (str, bool, int, float,
                                              type(None))), (name, field)
            continue
        assert isinstance(value, allowed), name
        if isinstance(value, list):
            for item in value:
                assert isinstance(item, (str, dict)), name


def test_that_rule_still_rejects_a_domain_record_inside_a_model():
    """The negative control for the exemption above: admitting RowListModel
    must not become a hole a physics object can be carried through."""
    from rocketforge.application.rowmodel import RowListModel

    model = RowListModel(("label", "value"))
    model.set_rows([{"label": "chamber", "value": object()}])
    offending = [field for row in model.rows() for field in row.values()
                 if not isinstance(field, (str, bool, int, float,
                                           type(None)))]
    assert offending, "the content check would not have noticed"


def test_every_row_model_is_named_so_the_rule_can_find_it():
    from rocketforge.application.rowmodel import RowListModel

    meta = RocketPerformanceController.staticMetaObject
    for index in range(meta.propertyCount()):
        name = meta.property(index).name()
        if name.endswith("Model"):
            assert meta.property(index).typeName() in ("QObject*", "QObject"),                 name


def test_the_chamber_outcome_is_not_reachable_from_qml():
    """The handoff is a Python method, so no ChamberGas crosses into the view."""
    meta = ThermochemistryController.staticMetaObject
    names = {meta.property(i).name() for i in range(meta.propertyCount())}
    assert "chamberOutcome" not in names
    assert not any(name.lower() == "chamberoutcome" for name in names)
    methods = {meta.method(i).name().data().decode()
               for i in range(meta.methodCount())}
    assert "chamber_outcome" not in methods


def test_the_controller_holds_no_equation_and_no_constant():
    """Every number it publishes was computed somewhere it can be tested."""
    import ast
    import inspect

    from rocketforge.application.analysis import performance_controller

    source = inspect.getsource(performance_controller)
    tree = ast.parse(source)
    literals = [node.value for node in ast.walk(tree)
                if isinstance(node, ast.Constant)
                and isinstance(node.value, float)]
    # The only floats present are interface defaults -- a starting throat area
    # and a starting mass flow -- and neither enters a calculation.
    assert set(literals) <= {0.01, 10.0, 0.0, 100.0}, literals
    for banned in ("9.80665", "101325", "8314", "math.sqrt", "math.pow"):
        assert banned not in source, banned
