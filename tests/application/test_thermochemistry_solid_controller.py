"""The Thermochemistry workspace in solid mode.

These exist because a green suite is not a visual pass. The one defect this
feature actually rendered into a screenshot -- every condition row of a solid
result failing with ``'SolidCase' object has no attribute 'fuel'`` -- was
invisible to the service-level tests, because it lived in a controller property
the service never calls.

So these drive the controller the way a QML binding does: read every property a
binding reads, in both modes, and require none of them to raise.
"""

from __future__ import annotations

import pytest

from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.thermochemistry_controller import (
    ThermochemistryController,
)

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status})")

#: Every property a QML binding in the solid path reads. Enumerated rather than
#: discovered, so adding a binding without a test is a visible omission.
SOLID_BINDINGS = (
    "formulationKind", "isSolid", "modelBoundaryNote",
    "solidFormulationLabel", "solidFormulationReference", "solidReferenceNote",
    "solidIsReferenceCase", "solidFormulationOptions", "solidIngredients",
    "solidAddableIngredients", "solidMassTotalPercent", "solidMassTotalText",
    "solidMassBalanced", "solidEdited", "solidChamberPressureDisplay",
    "solidGrainTemperature", "solidConditions", "solidCStarShown",
    "solidCStarAvailable", "solidCStarText", "solidCStarRefusal",
    "solidCStarCondensedNote", "solidCStarLimitations",
)

#: Properties the result surfaces bind, shared by both modes. These are the
#: ones that broke: a solid result flows through every one of them.
SHARED_RESULT_BINDINGS = (
    "resultRows", "advancedRows", "resultHeadline", "resultConditions",
    "provenanceRows", "provenanceSummary", "speciesSet", "condensed",
    "diagnostics", "warnings", "warningCount", "statusKind", "hasResult",
    "assignedEnthalpyNotes",
)


@pytest.fixture()
def live(qt_app, gateway):
    return ThermochemistryController()


def read_all(controller, names):
    """Read every named property, reporting the ones that raise.

    A QML binding that raises does not crash the application -- it logs a
    metacall warning and renders nothing. That is exactly how an empty result
    rail reaches a screenshot while every test passes, so the failure has to be
    turned back into an exception here.
    """
    failures = {}
    for name in names:
        try:
            getattr(controller, name)
        except Exception as exc:  # noqa: BLE001
            failures[name] = f"{type(exc).__name__}: {exc}"
    return failures


# ===========================================================================
# mode switching
# ===========================================================================


@requires_cea
def test_the_workspace_opens_in_bipropellant_mode(live):
    assert live.formulationKind == "bipropellant"
    assert live.isSolid is False


@requires_cea
def test_switching_to_solid_offers_the_published_case(live):
    live.formulationKind = "solid"
    assert live.isSolid is True
    assert live.solidFormulationLabel == "RP-1311 Example 5"
    assert live.solidFormulationReference == "NASA RP-1311 Example 5"
    assert live.solidIsReferenceCase is True


@requires_cea
def test_an_unknown_mode_is_ignored(live):
    live.formulationKind = "hybrid"
    assert live.formulationKind == "bipropellant"


@requires_cea
def test_switching_mode_clears_the_previous_result(live):
    """A result belongs to the mode that produced it.

    Leaving a bipropellant result on screen under a solid form is the
    stale-vs-solved failure in its most literal form: the header and the inputs
    would each be individually correct and describe different cases.
    """
    live.calculate()
    assert live.hasResult is True
    live.formulationKind = "solid"
    assert live.hasResult is False
    assert live.resultRows == []


# ===========================================================================
# every binding, in both modes -- the regression this file exists for
# ===========================================================================


@requires_cea
def test_every_solid_binding_reads_without_raising_before_solving(live):
    live.formulationKind = "solid"
    assert read_all(live, SOLID_BINDINGS) == {}


@requires_cea
def test_every_shared_result_binding_reads_on_a_solid_result(live):
    """The exact regression: ``resultConditions`` read ``case.fuel``.

    A solid case has no fuel stream, so the binding raised, Qt logged a
    metacall warning, and the condition rail rendered empty in a screenshot
    while every service-level test stayed green.
    """
    live.formulationKind = "solid"
    live.calculate()
    assert live.hasResult is True
    assert read_all(live, SHARED_RESULT_BINDINGS) == {}


@requires_cea
def test_every_shared_result_binding_still_reads_on_a_bipropellant_result(live):
    live.calculate()
    assert live.hasResult is True
    assert read_all(live, SHARED_RESULT_BINDINGS) == {}


@requires_cea
def test_the_solid_condition_rail_is_not_empty(live):
    """Silently empty content is the failure a parity check cannot see."""
    live.formulationKind = "solid"
    live.calculate()
    labels = [row["label"] for row in live.resultConditions]
    assert "Formulation" in labels
    assert "Total mass" in labels
    assert "NH4CLO4(I)" in labels
    assert len(live.resultConditions) >= 8


@requires_cea
def test_the_solid_conditions_never_show_an_of_ratio(live):
    """CEA reports o/f = 0.000 for a solid; the absence is the honest form.

    A printed zero invites being read as a measured value.
    """
    live.formulationKind = "solid"
    live.calculate()
    for row in live.resultConditions:
        assert "O/F" not in row["label"]
        assert "Oxidiser" != row["label"]
        assert "Fuel" != row["label"]


# ===========================================================================
# the formulation editor
# ===========================================================================


@requires_cea
def test_the_published_grain_closes_at_one_hundred_percent(live):
    live.formulationKind = "solid"
    assert live.solidMassTotalText == "100.000 %"
    assert live.solidMassBalanced is True
    assert live.solidEdited is False


@requires_cea
def test_the_ingredient_rows_show_percent_and_mark_the_custom_reactant(live):
    live.formulationKind = "solid"
    rows = live.solidIngredients
    assert [row["name"] for row in rows] == [
        "NH4CLO4(I)", "CHOS-Binder", "AL(cr)", "MgO(cr)", "H2O(L)"]
    binder = rows[1]
    assert binder["isCustom"] is True
    assert binder["representation"] == "custom · assigned enthalpy"
    assert binder["assignedTemperatureText"] == "298.15 K"
    assert rows[0]["representation"] == "thermo.lib · solid"
    assert rows[4]["representation"] == "thermo.lib · liquid"
    assert binder["percentText"] == "18.580"
    # percent is presentation; the fraction is what the physics layer gets
    assert binder["fraction"] == pytest.approx(0.1858, rel=1e-12)


@requires_cea
def test_editing_one_fraction_does_not_rescale_the_others(live):
    """Renormalising would change inputs the user did not touch."""
    live.formulationKind = "solid"
    before = [row["fraction"] for row in live.solidIngredients]
    live.setSolidMassPercent(2, 12.0)
    after = [row["fraction"] for row in live.solidIngredients]
    assert after[2] == pytest.approx(0.12)
    for index in (0, 1, 3, 4):
        assert after[index] == before[index]
    assert live.solidMassTotalText == "103.000 %"
    assert live.solidMassBalanced is False
    assert live.solidEdited is True


@requires_cea
def test_a_grain_that_does_not_close_is_refused_not_normalised(live):
    live.formulationKind = "solid"
    live.setSolidMassPercent(2, 12.0)
    live.calculate()
    assert live.hasResult is False
    assert live.statusKind == "invalid_input"
    assert live.resultRows == []


@requires_cea
def test_a_percent_outside_the_valid_range_is_ignored(live):
    live.formulationKind = "solid"
    before = live.solidIngredients[0]["fraction"]
    for bad in (-5.0, 120.0, float("nan")):
        live.setSolidMassPercent(0, bad)
        assert live.solidIngredients[0]["fraction"] == before


@requires_cea
def test_restoring_returns_the_published_composition(live):
    live.formulationKind = "solid"
    live.setSolidMassPercent(2, 12.0)
    live.resetSolidFormulation()
    assert live.solidMassTotalText == "100.000 %"
    assert live.solidEdited is False
    live.calculate()
    assert live.hasResult is True


# ===========================================================================
# the solved result, and what it must not claim
# ===========================================================================


@requires_cea
def test_the_solid_result_reproduces_the_published_chamber_state(live):
    live.formulationKind = "solid"
    live.calculate()
    values = {row["label"]: row["raw"] for row in live.resultRows}
    temperature = next(v for k, v in values.items() if "temperature" in k.lower())
    assert temperature == pytest.approx(2723.021, abs=5e-4)


@requires_cea
def test_the_solid_result_reports_the_condensed_phase(live):
    live.formulationKind = "solid"
    live.calculate()
    condensed = live.condensed
    assert condensed["present"] is True
    assert condensed["fraction"] == pytest.approx(0.16798697793, rel=1e-9)
    assert list(condensed["species"]) == ["AL2O3(L)"]
    assert condensed["state"] == "present"
    # 44 condensed candidates, one actually present: the condensed mass is
    # read from the composition, never from the candidate counter.
    assert condensed["fractionText"] == "0.167987"


@requires_cea
def test_the_headline_comes_from_the_result_not_the_live_form(live):
    """Editing an input must not relabel a result that is already on screen."""
    live.formulationKind = "solid"
    live.calculate()
    before = live.resultHeadline
    live.solidGrainTemperature = 320.0
    assert live.resultHeadline == before
    assert "298.15" in before


@requires_cea
def test_no_performance_quantity_appears_in_a_solid_result(live):
    """Section 7: solid reference performance is deferred to R1.1.

    Matched on whole words, because a substring scan reports
    ``chamberPressureDisplay`` as containing "isp".
    """
    banned = {"cstar", "isp", "thrust", "impulse", "characteristic"}
    live.formulationKind = "solid"
    live.calculate()
    texts = [row["label"] for row in live.resultRows + live.advancedRows]
    texts += [row["label"] for row in live.resultConditions]
    for text in texts:
        words = {w.strip("·").lower() for w in text.replace("_", " ").split()}
        assert not (words & banned), text


@requires_cea
def test_the_model_boundary_is_stated_rather_than_implied(live):
    note = live.modelBoundaryNote
    # Section 26's wording: chamber thermochemistry only, and the two things a
    # reader might otherwise assume -- a motor, and delivered performance.
    assert note.startswith("Chamber thermochemistry only.")
    assert "internal-ballistics" in note
    assert "delivered performance" in note
    assert "not modelled" in note
    live.formulationKind = "solid"
    live.calculate()
    notes = " ".join(row.get("note", "") for row in live.resultConditions)
    assert "not modelled" in notes


# ===========================================================================
# section 27 -- stale-vs-solved
# ===========================================================================


@requires_cea
def test_editing_after_a_solve_keeps_the_result_and_marks_it_stale(live):
    """The required fixture: solve Example 5, change AP, do NOT recalculate.

    The chamber state and products stay those of the solve. The form shows the
    edit. The result is unmistakably stale, and no live formulation value leaks
    into the solved result's own record.
    """
    live.formulationKind = "solid"
    live.calculate()
    solved_values = [r["value"] for r in live.resultRows]
    solved_headline = live.resultHeadline
    solved_fraction = live.condensed["fraction"]

    live.setSolidMassPercent(0, 73.06)

    assert live.resultStale is True
    assert live.hasResult is True
    assert [r["value"] for r in live.resultRows] == solved_values
    assert live.resultHeadline == solved_headline
    assert live.condensed["fraction"] == solved_fraction
    # the form shows the edit ...
    assert live.solidIngredients[0]["percentText"] == "73.060"
    assert live.solidFormulationLabel == "Edited from RP-1311 Example 5"
    # ... and the result's own record does not
    ap = [r["value"] for r in live.resultConditions if r["label"] == "NH4CLO4(I)"]
    assert ap == ["72.060 %"]
    formulation = [r["value"] for r in live.resultConditions
                   if r["label"] == "Formulation"]
    assert formulation == ["RP-1311 Example 5"]


@requires_cea
def test_recalculating_clears_the_stale_flag(live):
    live.formulationKind = "solid"
    live.calculate()
    live.setSolidMassPercent(0, 72.06)       # the same value: not an edit
    assert live.resultStale is False
    live.solidGrainTemperature = 300.0
    assert live.resultStale is True
    live.calculate()
    assert live.resultStale is False


# ===========================================================================
# section 22 -- add, remove, select
# ===========================================================================


@requires_cea
def test_the_catalogue_offers_only_what_this_build_can_model(live):
    live.formulationKind = "solid"
    offered = {o["key"] for o in live.solidAddableIngredients}
    assert "B(b)" in offered and "NH4NO3(I)" in offered
    # absent from this thermo.lib, so never offered
    assert not offered & {"KNO3(cr)", "KCLO4(cr)"}
    # no generic binder presets: none has an independently sourced definition
    assert not any("HTPB" in k or "PBAN" in k for k in offered)


@requires_cea
def test_an_added_ingredient_arrives_at_zero_and_does_not_move_the_total(live):
    live.formulationKind = "solid"
    live.addSolidIngredient("B(b)")
    rows = live.solidIngredients
    assert rows[-1]["name"] == "B(b)" and rows[-1]["fraction"] == 0.0
    assert live.solidMassTotalText == "100.000 %"
    assert "B(b)" not in {o["key"] for o in live.solidAddableIngredients}
    live.calculate()
    assert live.hasResult is True


@requires_cea
def test_removing_an_ingredient_does_not_rescale_the_others(live):
    live.formulationKind = "solid"
    before = [r["fraction"] for r in live.solidIngredients]
    live.removeSolidIngredient(4)                     # H2O(L), 0.16 %
    after = [r["fraction"] for r in live.solidIngredients]
    assert after == before[:4]
    assert live.solidMassTotalText == "99.840 %"
    assert live.solidMassBalanced is False


@requires_cea
def test_the_last_ingredient_cannot_be_removed(live):
    live.formulationKind = "solid"
    for _ in range(10):
        live.removeSolidIngredient(0)
    assert len(live.solidIngredients) == 1


# ===========================================================================
# the assigned-enthalpy hazard, and the reference-case label
# ===========================================================================


@requires_cea
def test_a_grain_temperature_the_binder_cannot_follow_is_reported(live):
    """CEA holds the custom binder at its assigned 298.15 K whatever is asked.

    Measured: a binder-only mixture has the same enthalpy at 250, 298.15 and
    320 K. So a 320 K grain is solved with the binder at 298.15 K, and saying
    "T_grain 320 K" without that caveat would misdescribe the calculation.
    """
    live.formulationKind = "solid"
    live.solidGrainTemperature = 320.0
    live.calculate()
    assert live.statusKind == "warning"
    notes = live.assignedEnthalpyNotes
    assert [(n["reactant"], n["requestedText"], n["assignedText"])
            for n in notes] == [("CHOS-Binder", "320 K", "298.15 K")]
    flags = [r["temperatureIgnored"] for r in live.solidIngredients]
    assert flags == [False, True, False, False, False]


@requires_cea
def test_the_published_grain_at_its_published_point_raises_no_warning(live):
    live.formulationKind = "solid"
    live.calculate()
    assert live.statusKind == "ok"
    assert live.assignedEnthalpyNotes == []


@requires_cea
def test_only_a_published_operating_point_is_called_a_validation_case(live):
    live.formulationKind = "solid"
    assert live.solidIsReferenceCase is True
    assert live.solidReferenceNote.startswith("Reference / validation case")
    live.solidGrainTemperature = 320.0
    assert live.solidIsReferenceCase is False
    assert "differs from the published one" in live.solidReferenceNote
    live.resetSolidFormulation()
    live.setSolidMassPercent(0, 73.06)
    assert live.solidIsReferenceCase is False
    assert live.solidReferenceNote == ""


# ===========================================================================
# section 9 -- a solid chamber never reaches the gas-only performance model
# ===========================================================================


@requires_cea
def test_rocket_performance_refuses_a_solid_chamber(live):
    """Including a grain with no condensed products at all.

    The reduction's condensed-phase gate already stops Example 5 (0.168
    condensed). A non-metalised grain carries none, and before the explicit
    gate it passed straight through and returned an ideal-rocket result -- an
    unvalidated solid performance claim, which R1 does not make.
    """
    from rocketforge.application.analysis import performance_service as perf

    live.formulationKind = "solid"
    for index in (4, 3, 2):                  # drop H2O(L), MgO(cr), AL(cr)
        live.removeSolidIngredient(index)
    live.setSolidMassPercent(0, 81.42)       # AP 81.42 + binder 18.58
    live.calculate()
    assert live.hasResult is True
    assert live.condensed["present"] is False

    outcome = perf.solve_performance(live.chamber_outcome(),
                                     perf.DEFAULT_PERFORMANCE_CASE)
    assert outcome.result is None
    assert "solid" in outcome.message.lower()


# ===========================================================================
# CEA equilibrium characteristic velocity (decisions D2 and D4)
# ===========================================================================


@requires_cea
def test_cstar_is_shown_for_a_solid_result_and_not_for_a_bipropellant(live):
    live.calculate()
    assert live.solidCStarShown is False           # its c* lives elsewhere
    live.formulationKind = "solid"
    live.calculate()
    assert live.solidCStarShown is True
    assert live.solidCStarAvailable is True
    assert live.solidCStarText == "1525.68"


@requires_cea
def test_cstar_never_shows_more_than_six_significant_figures(live):
    """CEA's solver-path sensitivity is 2.1e-06; a seventh figure is noise."""
    live.formulationKind = "solid"
    live.calculate()
    live.precision = 12
    assert live.solidCStarText == "1525.68"


@requires_cea
def test_cstar_carries_its_limitations_and_the_condensed_assumption(live):
    live.formulationKind = "solid"
    live.calculate()
    limits = " ".join(live.solidCStarLimitations).lower()
    assert "not a motor specific impulse" in limits
    assert "no nozzle expansion" in limits
    assert "internal-ballistic" in limits
    note = live.solidCStarCondensedNote
    assert "no particle lag" in note
    assert "16.8 %" in note


@requires_cea
def test_cstar_is_not_presented_as_performance(live):
    """D2: never under a generic "Performance" heading or wording."""
    live.formulationKind = "solid"
    live.calculate()
    for text in (live.solidCStarRefusal, live.solidCStarCondensedNote,
                 *live.solidCStarLimitations):
        assert "performance" not in text.lower()


@requires_cea
def test_a_refused_cstar_is_shown_as_refused_never_as_a_number(live, monkeypatch):
    """D4. The provider-level test drives CEA's real non-converged solve; this
    one checks the interface: dash, reason, and no number anywhere."""
    from rocketforge.application.analysis import thermochemistry_solid_service as svc
    from rocketforge.providers.cea_solid import SolidCharacteristicVelocity

    refusal = ("NASA CEA did not converge the c* solve (converged=False, error "
               "code 8). It returns a number regardless; that number is not used.")
    monkeypatch.setattr(svc, "solve_solid_equilibrium_cstar",
                        lambda request, chamber: SolidCharacteristicVelocity(
                            value=None, refusal=refusal,
                            condensed_mass_fraction=chamber.condensed_mass_fraction))
    live.formulationKind = "solid"
    live.calculate()
    assert live.hasResult is True                  # the chamber result stands
    assert live.solidCStarAvailable is False
    assert live.solidCStarText == "—"
    assert live.solidCStarRefusal == refusal


@requires_cea
def test_a_stale_result_keeps_the_cstar_of_the_case_that_produced_it(live):
    live.formulationKind = "solid"
    live.calculate()
    live.setSolidMassPercent(2, 12.0)
    assert live.resultStale is True
    assert live.solidCStarText == "1525.68"
