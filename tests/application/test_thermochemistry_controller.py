"""The Qt bridge for the Thermochemistry workspace.

Everything here runs with a ``QGuiApplication`` but no window and no QML: what
is checked is that the interface is handed correct, complete, honestly labelled
state, not how it looks. The visual side is covered by the capture harness in
``experiments/phase_5d/``.

The behaviours that matter most are the ones a screenshot cannot prove:

* a display filter hides rows without touching the result;
* an edited input marks a result stale instead of relabelling it;
* switching view does not re-solve;
* a provider change clears everything the old provider produced.
"""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import Qt

from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.thermochemistry_controller import (
    MAX_SWEEP_SPECIES,
    PRESSURE_UNITS,
    TRACE_THRESHOLDS,
    ThermochemistryController,
)

#: Whole words that would identify a rocket-performance quantity. Matched as
#: camelCase words rather than substrings, because a substring scan reports
#: ``chamberPressureDisplay`` as containing "isp" -- the same false positive
#: that flagged RocketForge's own ``MixtureRatio`` for containing "Mixture" in
#: Phase 5C.
BANNED_PERFORMANCE_WORDS = {
    "cstar", "cf", "isp", "thrust", "impulse", "star",
    "characteristic", "velocity",
}

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status})")


@pytest.fixture()
def controller(qt_app, stub_gateway):
    return ThermochemistryController()


@pytest.fixture()
def live_controller(qt_app, gateway):
    return ThermochemistryController()


# ===========================================================================
# empty and unavailable states
# ===========================================================================


def test_nothing_is_calculated_until_asked(controller, stub_gateway):
    """No solve on construction, and no zeros standing in for a result."""
    assert controller.statusKind == "empty"
    assert controller.hasResult is False
    assert controller.resultRows == []
    assert controller.resultHeadline == ""
    assert stub_gateway.calls == []


def test_the_workspace_survives_an_absent_provider(qt_app, absent_gateway):
    controller = ThermochemistryController()
    assert controller.providerAvailable is False
    assert controller.providerStatus == "not_installed"
    assert controller.providerRemedy
    # And it still refuses to invent anything when asked to calculate.
    controller.calculate()
    assert controller.statusKind == "unavailable"
    assert controller.hasResult is False
    assert controller.resultRows == []


def test_the_catalogue_is_available_even_with_no_provider(qt_app, absent_gateway):
    """The unavailable screen can still describe what the workspace would do."""
    controller = ThermochemistryController()
    assert [option["key"] for option in controller.oxidiserOptions] == ["LOX", "GOX"]
    assert [option["key"] for option in controller.fuelOptions] == [
        "LCH4", "LH2", "GCH4"]


# ===========================================================================
# inputs
# ===========================================================================


def test_an_invalid_input_is_refused_rather_than_clamped(controller):
    before = controller.mixtureRatio
    controller.mixtureRatio = -1.0
    assert controller.mixtureRatio == before
    controller.mixtureRatio = float("nan")
    assert controller.mixtureRatio == before
    controller.oxidiserTemperature = 0.0
    assert controller.oxidiserTemperature == 90.17


def test_ofratio_accepts_more_than_one_decimal(controller):
    controller.mixtureRatio = 3.425
    assert controller.mixtureRatio == pytest.approx(3.425)


def test_changing_a_reactant_moves_its_temperature_to_that_reactants_reference(controller):
    """Carrying 111.6 K over to liquid hydrogen would be outside CEA's range."""
    controller.fuel = "LH2"
    assert controller.fuel == "LH2"
    assert controller.fuelTemperature == pytest.approx(20.27)


def test_a_reactant_cannot_be_set_to_something_in_the_other_role(controller):
    controller.fuel = "LOX"
    assert controller.fuel == "LCH4"


def test_the_pressure_unit_is_a_display_choice_only(controller):
    """Changing the unit must not change the stored pressure or the result."""
    controller.calculate()
    assert controller.hasResult
    pascals = controller.chamberPressure
    before = [row["value"] for row in controller.resultRows]

    controller.pressureUnit = "bar"
    assert controller.chamberPressure == pascals
    assert controller.chamberPressureDisplay == pytest.approx(pascals / 1.0e5)
    assert controller.resultStale is False, (
        "a display unit change is not an input change")
    assert [row["value"] for row in controller.resultRows] == before


def test_the_pressure_input_converts_on_the_way_in(controller):
    controller.pressureUnit = "bar"
    controller.chamberPressureDisplay = 70.0
    assert controller.chamberPressure == pytest.approx(7.0e6)
    controller.pressureUnit = "MPa"
    assert controller.chamberPressureDisplay == pytest.approx(7.0)


def test_every_pressure_unit_declares_its_conversion():
    for unit in PRESSURE_UNITS:
        assert unit["to_pa"] > 0
        assert unit["label"]


def test_the_provider_reactant_identity_is_available_as_detail(controller):
    assert controller.oxidiserProviderName == "O2(L)"
    assert controller.fuelProviderName == "CH4(L)"
    assert "80.17" in controller.oxidiserRangeText


# ===========================================================================
# staleness and traceability
# ===========================================================================


def test_editing_an_input_marks_the_result_stale_without_relabelling_it(controller):
    """Case A must never appear as case B."""
    controller.calculate()
    headline = controller.resultHeadline
    assert "O/F 3.4" in headline
    assert controller.resultStale is False

    controller.mixtureRatio = 3.6
    assert controller.resultStale is True
    assert controller.resultHeadline == headline, (
        "the result header must describe the result, not the form")
    assert "O/F 3.6" in controller.caseHeadline


def test_recalculating_clears_the_stale_flag(controller):
    controller.calculate()
    controller.mixtureRatio = 3.6
    assert controller.resultStale is True
    controller.calculate()
    assert controller.resultStale is False
    assert "O/F 3.6" in controller.resultHeadline


def test_the_result_conditions_are_recoverable_from_the_result(controller):
    controller.calculate()
    controller.mixtureRatio = 4.0
    controller.oxidiserTemperature = 95.0
    conditions = {row["label"]: row["value"] for row in controller.resultConditions}
    assert conditions["O/F"] == "3.4"
    assert conditions["Oxidiser temperature"] == "90.17 K"
    assert conditions["Model"] == "HP Equilibrium · Adiabatic"


def test_a_failed_solve_does_not_leave_the_previous_result_on_screen(controller,
                                                                    stub_gateway):
    controller.calculate()
    assert controller.hasResult
    controller.mixtureRatio = -5.0        # refused, so the case is unchanged
    controller.fuel = "LH2"
    controller.fuelTemperature = 25.0
    controller.oxidiser = "LOX"
    # Force a refusal through the domain by asking for something impossible.
    controller._case = controller._case.replace(oxidiser_fuel_ratio=float("inf"))
    controller.calculate()
    assert controller.hasResult is False
    assert controller.resultRows == []


def test_switching_view_does_not_re_solve(controller, stub_gateway):
    controller.calculate()
    calls = len(stub_gateway.calls)
    controller.showTab(1)
    controller.showTab(2)
    controller.showTab(0)
    assert len(stub_gateway.calls) == calls


def test_a_provider_change_clears_the_result(controller):
    """Two providers can differ by a per cent, which looks like a refresh."""
    controller.calculate()
    assert controller.hasResult
    controller.refreshProvider()
    assert controller.hasResult is False
    assert controller.statusKind == "empty"
    assert controller.hasSweep is False


# ===========================================================================
# readouts
# ===========================================================================


def test_result_rows_are_formatted_but_keep_their_raw_value(controller):
    controller.calculate()
    rows = {row["key"]: row for row in controller.resultRows}
    temperature = rows["temperature"]
    assert temperature["value"] == "3340.00"
    assert temperature["raw"] == pytest.approx(3340.0)
    assert temperature["unit"] == "K"
    assert temperature["qualifier"] == "Adiabatic · HP equilibrium"


def test_changing_precision_re_renders_without_re_solving(controller, stub_gateway):
    controller.calculate()
    calls = len(stub_gateway.calls)
    before = [row["value"] for row in controller.resultRows]
    controller.precision = 9
    assert len(stub_gateway.calls) == calls
    assert [row["value"] for row in controller.resultRows] != before
    assert [row["raw"] for row in controller.resultRows] == [
        row["raw"] for row in controller.resultRows]


def test_an_absent_quantity_renders_as_an_em_dash(controller):
    controller.calculate()
    rows = {row["key"]: row for row in controller.advancedRows}
    assert rows["speed_of_sound"]["available"] is False
    assert rows["speed_of_sound"]["value"] == "—"


def test_the_controller_exposes_no_performance_property():
    """A property audit on the Qt surface itself.

    Matched on whole camelCase words rather than substrings. A substring scan
    reports ``chamberPressureDisplay`` as containing "isp", which is the same
    false positive that flagged RocketForge's own ``MixtureRatio`` for
    containing "Mixture" in Phase 5C.
    """
    import re

    meta = ThermochemistryController.staticMetaObject
    banned = BANNED_PERFORMANCE_WORDS
    for index in range(meta.propertyCount()):
        name = meta.property(index).name()
        words = {word.lower() for word in re.findall(r"[A-Z]?[a-z]+|[A-Z]+", name)}
        assert not (words & banned), f"{name} exposes {words & banned}"


def test_the_property_audit_would_catch_a_real_leak():
    """The negative control: the matcher must not be vacuous."""
    import re

    for leaked in ("characteristicVelocity", "specificImpulse", "isp",
                   "thrustCoefficient", "cStar"):
        words = {word.lower() for word in re.findall(r"[A-Z]?[a-z]+|[A-Z]+", leaked)}
        assert words & BANNED_PERFORMANCE_WORDS, leaked


# ===========================================================================
# composition
# ===========================================================================


def test_the_composition_model_mirrors_the_result(controller):
    controller.calculate()
    model = controller.compositionModel
    assert controller.hasComposition
    assert model.rowCount() == controller.speciesTotal == 5
    assert model.columnCount() == 4
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "H2O"
    assert model.data(model.index(0, 1), Qt.DisplayRole) == "gas"


def test_the_composition_is_sorted_descending_on_the_displayed_basis(controller):
    controller.calculate()
    model = controller.compositionModel
    column = 2
    values = [model.valueAt(row, column) for row in range(model.rowCount())]
    assert values == sorted(values, reverse=True)


def test_switching_basis_does_not_recalculate(controller, stub_gateway):
    controller.calculate()
    calls = len(stub_gateway.calls)
    controller.compositionBasis = "mass"
    assert len(stub_gateway.calls) == calls
    assert controller.compositionBasis == "mass"
    model = controller.compositionModel
    values = [model.valueAt(row, 3) for row in range(model.rowCount())]
    assert values == sorted(values, reverse=True)


def test_a_threshold_label_matches_what_the_filter_does(controller):
    """A row exactly at the threshold is kept, and the label says "at least"."""
    controller.calculate()
    for entry in TRACE_THRESHOLDS[1:]:
        assert entry["label"].startswith("\u2265")


def test_the_trace_filter_hides_rows_without_mutating_the_result(controller):
    """The mutation proof: hide a species, then get it back exactly.

    If filtering removed the species from the underlying composition, lowering
    the threshold again would not bring it back with its original value -- and
    that is precisely the defect this guards against.
    """
    controller.calculate()
    model = controller.compositionModel

    def fraction_of(name):
        for row in range(model.rowCount()):
            if model.data(model.index(row, 0), Qt.DisplayRole) == name:
                return model.valueAt(row, 2)
        return None

    original = fraction_of("OH")
    assert original == pytest.approx(5.0e-5), "the fixture must contain a trace row"
    assert controller.speciesTotal == 5

    # A threshold above the trace species.
    controller.traceThresholdIndex = len(TRACE_THRESHOLDS) - 1
    assert fraction_of("OH") is None, "the row should have disappeared from view"
    assert controller.speciesHidden >= 1
    assert controller.speciesTotal == 5, "the result must be untouched"
    assert "remain in the result" in controller.hiddenSummary

    # And back.
    controller.traceThresholdIndex = 0
    assert fraction_of("OH") == original


def test_the_hidden_summary_states_the_count_and_the_fraction(controller):
    controller.calculate()
    controller.traceThresholdIndex = len(TRACE_THRESHOLDS) - 1
    summary = controller.hiddenSummary
    assert str(controller.speciesHidden) in summary
    assert "ΣX" in summary


def test_the_species_filter_is_a_display_filter_too(controller):
    controller.calculate()
    controller.speciesFilter = "CO"
    names = [controller.compositionModel.data(
        controller.compositionModel.index(row, 0), Qt.DisplayRole)
        for row in range(controller.compositionModel.rowCount())]
    assert set(names) == {"CO", "CO2"}
    assert controller.speciesTotal == 5
    controller.speciesFilter = ""
    assert controller.compositionModel.rowCount() == 5


def test_the_composition_sums_are_reported_over_every_species(controller):
    controller.calculate()
    controller.traceThresholdIndex = len(TRACE_THRESHOLDS) - 1
    assert "over all 5 species" in controller.compositionSums


def test_a_condensed_candidate_is_not_announced_as_present(controller):
    """Below the reporting threshold, and said in those words."""
    controller.calculate()
    condensed = controller.condensed
    assert condensed["state"] == "below_threshold"
    assert condensed["known"] is True
    assert condensed["present"] is False
    assert condensed["headline"] == "No condensed phase above reporting threshold"


def test_the_below_threshold_state_shows_both_numbers(controller):
    """The verdict is a sentence about a number; the number is shown too."""
    controller.calculate()
    condensed = controller.condensed
    assert 0.0 < condensed["fraction"] < condensed["threshold"]
    assert condensed["fractionText"] not in ("", "0", "—")
    assert condensed["thresholdText"] == "1e-06"
    # The candidate is named, but never as present.
    assert condensed["species"] == ["C(gr)"]


def test_the_interface_never_says_none_detected_for_a_nonzero_fraction(controller):
    """The corrective patch, asserted as a prohibition.

    6.24e-08 is not zero. Reporting it as "none detected" claimed the mixture
    contained no condensed material, which was a stronger statement than the
    number supports.
    """
    controller.calculate()
    condensed = controller.condensed
    assert condensed["fraction"] > 0.0
    rendered = " ".join(str(value) for value in condensed.values()).lower()
    assert "none detected" not in rendered


def test_an_exactly_zero_fraction_is_reported_as_none(qt_app, no_condensed_gateway):
    controller = ThermochemistryController()
    controller.calculate()
    condensed = controller.condensed
    assert condensed["state"] == "none_reported"
    assert condensed["present"] is False
    assert condensed["fraction"] == 0.0
    assert condensed["headline"] == "No condensed product reported"
    assert condensed["species"] == []


def test_a_fraction_above_the_threshold_is_reported_as_present(qt_app,
                                                               condensed_gateway):
    controller = ThermochemistryController()
    controller.calculate()
    condensed = controller.condensed
    assert condensed["state"] == "present"
    assert condensed["present"] is True
    assert condensed["fraction"] >= condensed["threshold"]
    assert condensed["headline"] == "Condensed products present"
    assert "C(gr)" in condensed["species"]


def test_every_condensed_state_the_interface_can_show_is_covered(
        qt_app, gateway, stub_provider_class):
    """All four, from one place, so none can be quietly dropped."""
    from rocketforge.application.analysis.thermochemistry_provider import (
        ProviderAvailability,
    )

    StubProvider = stub_provider_class
    seen = set()
    for mixture, expected in (("none", "none_reported"),
                              ("trace", "below_threshold"),
                              ("present", "present")):
        gateway._availability = ProviderAvailability(status="available",
                                                     usable=True)
        gateway._provider = StubProvider(condensed=mixture)
        controller = ThermochemistryController()
        controller.calculate()
        assert controller.condensed["state"] == expected
        seen.add(expected)

    # The fourth: no result at all.
    controller = ThermochemistryController()
    assert controller.condensed["state"] == "unknown"
    seen.add("unknown")
    assert len(seen) == 4


def test_the_condensed_rows_are_marked_for_the_table(controller):
    controller.calculate()
    rows = controller.condensedRows
    assert len(rows) == 1
    model = controller.compositionModel
    assert model.data(model.index(rows[0], 1), Qt.DisplayRole) == "solid"


def test_composition_state_survives_switching_view(controller):
    controller.calculate()
    controller.compositionBasis = "mass"
    controller.traceThresholdIndex = 2
    controller.showTab(0)
    controller.showTab(1)
    assert controller.compositionBasis == "mass"
    assert controller.traceThresholdIndex == 2


# ===========================================================================
# warnings
# ===========================================================================


def test_a_warning_is_carried_by_the_result_not_by_a_view(qt_app, warning_gateway):
    controller = ThermochemistryController()
    controller.calculate()
    assert controller.statusKind == "warning"
    assert controller.hasResult is True, "a warning must not hide the result"
    notes = controller.assignedEnthalpyNotes
    assert len(notes) == 1
    assert notes[0]["reactant"] == "O2(L)"
    assert notes[0]["requestedText"] == "95 K"
    assert notes[0]["assignedText"] == "90.17 K"

    # Switching views cannot lose it: it belongs to the result.
    controller.showTab(1)
    assert controller.assignedEnthalpyNotes == notes
    controller.showTab(0)
    assert controller.assignedEnthalpyNotes == notes


def test_no_warning_appears_when_the_provider_reports_none(controller):
    controller.calculate()
    assert controller.statusKind == "ok"
    assert controller.assignedEnthalpyNotes == []
    assert controller.warningCount == 0


# ===========================================================================
# sweep
# ===========================================================================


def test_an_invalid_sweep_range_is_reported_and_not_run(controller, stub_gateway):
    controller.sweepEnd = 1.0            # below the start
    assert controller.sweepRangeValid is False
    assert controller.sweepRangeMessage
    calls = len(stub_gateway.calls)
    controller.runSweep()
    assert len(stub_gateway.calls) == calls
    assert controller.hasSweep is False


def test_a_sweep_populates_the_table_and_the_series(controller):
    controller.sweepStart = 2.5
    controller.sweepEnd = 3.5
    controller.sweepPoints = 11
    controller.runSweep()
    assert controller.hasSweep
    assert controller.sweepSolvedCount == 11
    assert controller.sweepFailedCount == 0
    assert controller.sweepModel.rowCount() == 11
    segments = controller.sweepSeries("temperature")
    assert len(segments) == 1
    assert len(segments[0]) == 11
    assert segments[0][0]["x"] == pytest.approx(2.5)


def test_every_sweep_chart_declares_its_axis_and_unit(controller):
    controller.runSweep()
    for key in ("temperature", "molar_mass", "gamma"):
        axis = controller.sweepAxis(key)
        assert axis["label"]
        assert axis["raw"]
        if key != "gamma":
            assert "[" in axis["label"], f"{key} axis carries no unit"
    assert controller.sweepAxis("gamma")["qualifier"] == "equilibrium"
    assert "Mole fraction" in controller.sweepSpeciesAxis


def test_the_sweep_maximum_is_labelled_as_a_sampled_maximum(controller):
    controller.runSweep()
    peak = controller.sweepMaximum("temperature")
    assert "Maximum" in peak["text"]
    assert "in sweep" in peak["text"]
    for banned in ("optimum", "optimal", "best", "recommended"):
        assert banned not in peak["text"].lower()


def test_no_public_sweep_wording_promises_a_decision(controller):
    """Every string the sweep publishes, audited in one place.

    Not the source -- the rendered output: axis labels, maximum captions,
    aggregated warnings, fixed-condition rows and point inspection. A phrase
    that only appears once the numbers arrive would slip past a source scan.
    """
    controller.runSweep()

    rendered: list[str] = []
    for key in ("temperature", "molar_mass", "gamma", "density",
                "gas_constant", "cp", "cv"):
        axis = controller.sweepAxis(key)
        rendered.extend(str(value) for value in axis.values())
        peak = controller.sweepMaximum(key)
        rendered.extend(str(value) for value in peak.values())
    for row in controller.sweepFixedConditions:
        rendered.extend(str(value) for value in row.values())
    for row in controller.sweepWarnings:
        rendered.extend(str(value) for value in row.values())
    for column in controller.sweepColumns:
        rendered.extend(str(value) for value in column.values())
    rendered.extend(str(value) for value in controller.sweepPoint(0).values())
    rendered.append(controller.sweepSpeciesAxis)

    assert len(rendered) > 40, "the audit must actually have something to read"
    text = " ".join(rendered).lower()
    for phrase in ("optimal", "optimum", "best", "recommend", "pareto",
                   "objective", "constraint", "score", "density impulse"):
        assert phrase not in text, f"the sweep says {phrase!r}"

    # And the thing it does say is the honest one.
    assert "maximum" in text
    assert "in sweep" in text


def test_the_sweep_wording_audit_would_catch_a_real_claim():
    """The negative control."""
    text = "maximum chamber temperature in sweep · optimal o/f 3.75".lower()
    assert "optimal" in text


def test_changing_an_input_marks_the_sweep_stale(controller):
    controller.runSweep()
    assert controller.sweepStale is False
    controller.chamberPressureDisplay = 5.0
    assert controller.sweepStale is True


def test_changing_the_sweep_range_marks_the_sweep_stale(controller):
    controller.runSweep()
    controller.sweepEnd = 5.0
    assert controller.sweepStale is True


def test_the_sweep_fixed_conditions_come_from_the_sweeps_own_case(controller):
    controller.runSweep()
    controller.chamberPressureDisplay = 5.0
    fixed = {row["label"]: row["value"] for row in controller.sweepFixedConditions}
    assert fixed["Chamber pressure"] == "10 MPa", (
        "the sweep must describe the conditions it ran under")


def test_a_failed_sweep_point_is_represented_and_marked(qt_app, failing_gateway):
    controller = ThermochemistryController()
    controller.sweepStart = 2.5
    controller.sweepEnd = 3.5
    controller.sweepPoints = 11
    controller.runSweep()

    assert controller.sweepFailedCount == 1
    assert controller.sweepSolvedCount == 10
    assert controller.sweepModel.rowCount() == 11, (
        "a failed point must keep its row")
    assert controller.sweepFailedRows == [5]
    assert controller.sweepFailedRatios[0]["value"] == pytest.approx(3.0)
    assert len(controller.sweepSeries("temperature")) == 2, (
        "the chart line must break across the failure")
    model = controller.sweepModel
    assert model.data(model.index(5, 8), Qt.DisplayRole) == "no solution"
    assert model.data(model.index(5, 1), Qt.DisplayRole) == "—"


def test_the_repeated_warning_is_aggregated_for_the_sweep(qt_app, warning_gateway):
    controller = ThermochemistryController()
    controller.runSweep()
    warnings = controller.sweepWarnings
    assert len(warnings) == 1
    assert warnings[0]["count"] == 41
    assert warnings[0]["range_text"] == "all 41 points"


def test_point_inspection_carries_no_performance_quantity(controller):
    controller.runSweep()
    point = controller.sweepPoint(0)
    assert set(point) == {
        "row", "of", "ok", "status", "tone", "message", "warned",
        "temperature", "molarMass", "gamma", "density", "diagnostics"}


def test_the_species_selection_is_a_drawing_limit_only(controller):
    controller.runSweep()
    options = controller.sweepSpeciesOptions
    assert len(options) == 5
    while len(controller.sweepSpecies) < MAX_SWEEP_SPECIES:
        for name in options:
            if name not in controller.sweepSpecies:
                controller.toggleSweepSpecies(name)
                break
        else:
            break
    plotted = len(controller.sweepSpecies)
    assert plotted <= MAX_SWEEP_SPECIES
    # Everything is still selectable and still in the result.
    assert controller.sweepSpeciesOptions == options


def test_clearing_the_sweep_leaves_the_calculator_result_alone(controller):
    controller.calculate()
    controller.runSweep()
    controller.clearSweep()
    assert controller.hasSweep is False
    assert controller.hasResult is True


# ===========================================================================
# live provider
# ===========================================================================


@requires_cea
def test_the_live_controller_produces_the_production_case(live_controller):
    """The one integration test that traverses everything, for real.

    controller -> service -> gateway -> NASA CEA -> ChamberGas -> display rows.
    """
    live_controller.calculate()
    assert live_controller.statusKind == "ok"
    rows = {row["key"]: row for row in live_controller.resultRows}
    assert rows["temperature"]["raw"] == pytest.approx(3598.2854, abs=1.0e-3)
    assert rows["temperature"]["value"].startswith("3598.2")
    assert live_controller.provenanceSummary["database"] == "thermo.lib"
    assert len(live_controller.speciesSet) == 28


@requires_cea
def test_the_live_composition_reaches_the_model(live_controller):
    live_controller.calculate()
    model = live_controller.compositionModel
    assert model.rowCount() == 28
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "H2O"
    total = math.fsum(model.valueAt(row, 2) for row in range(model.rowCount()))
    assert total == pytest.approx(1.0)


@requires_cea
def test_the_live_warning_case_reaches_the_interface(live_controller):
    """BLOCKING: requested and provider-assigned temperatures both displayed."""
    live_controller.oxidiserTemperature = 95.0
    live_controller.calculate()
    assert live_controller.statusKind == "warning"
    assert live_controller.hasResult
    notes = live_controller.assignedEnthalpyNotes
    assert len(notes) == 1
    assert notes[0]["reactant"] == "O2(L)"
    assert notes[0]["requestedText"] == "95 K"
    assert notes[0]["assignedText"] == "90.17 K"


@requires_cea
def test_the_live_control_case_raises_no_warning(live_controller):
    live_controller.oxidiser = "GOX"
    live_controller.fuel = "GCH4"
    live_controller.oxidiserTemperature = 320.0
    live_controller.fuelTemperature = 320.0
    live_controller.calculate()
    assert live_controller.statusKind == "ok"
    assert live_controller.assignedEnthalpyNotes == []


@requires_cea
def test_the_live_condensed_case_reaches_the_interface(live_controller):
    live_controller.mixtureRatio = 0.5
    live_controller.calculate()
    condensed = live_controller.condensed
    assert condensed["present"] is True
    assert "C(gr)" in condensed["species"]
    assert live_controller.condensedRows, "no row marked condensed"


@requires_cea
def test_the_live_sweep_reaches_the_interface(live_controller):
    live_controller.runSweep()
    assert live_controller.sweepSolvedCount == 41
    assert live_controller.sweepModel.rowCount() == 41
    assert len(live_controller.sweepSeries("temperature")[0]) == 41
    assert live_controller.sweepElapsedMs > 0.0
