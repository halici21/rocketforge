"""The Qt-free half of the Thermochemistry workspace.

Covers the chain from a ``ChamberCase`` to a display-ready ``ChamberOutcome``:
request construction, the seven outcome kinds, the readout rows, the
composition rows and the condensed-phase verdict.

Two kinds of test live here and they are kept apart on purpose:

* **stub tests** exercise the logic and run everywhere, including the base
  environment with no chemistry library. They prove nothing about chemistry;
* **``requires_cea`` tests** run the real provider and are the ones that mean
  something scientifically.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.application.analysis import thermochemistry_service as svc
from rocketforge.application.analysis import thermochemistry_provider as gateway

# The provider package imports without the library installed, so this check is
# safe in the base environment; it is what routes the live tests.
_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status}): "
           f"{_STATUS.detail or 'install requirements-thermochemistry.txt'}")


# ===========================================================================
# the case and the request
# ===========================================================================


def test_the_default_case_is_the_validated_demonstration_point():
    """LOX/LCH4 at O/F 3.4 and 10 MPa, the case Phase 5C checked end to end."""
    case = svc.DEFAULT_CASE
    assert case.oxidiser == "LOX"
    assert case.fuel == "LCH4"
    assert case.oxidiser_fuel_ratio == pytest.approx(3.4)
    assert case.chamber_pressure == pytest.approx(10.0e6)


def test_the_default_reactant_temperatures_are_not_a_hidden_298_K():
    """A cryogenic example at 298 K would be a different, wrong calculation.

    Phase 5B-0 measured LOX at 90.17 K against notional LOX at 298 K as worth
    **74.9 K of chamber temperature**, so a default of 298 K for a liquid is
    not a harmless placeholder.
    """
    case = svc.DEFAULT_CASE
    assert case.oxidiser_temperature == pytest.approx(90.17)
    assert case.fuel_temperature == pytest.approx(111.643)

    for key, temperature in (("LOX", case.oxidiser_temperature),
                             ("LCH4", case.fuel_temperature)):
        option = gateway.propellant_named(key)
        assert option is not None
        assert temperature == pytest.approx(option.reference_temperature), (
            "the default must be the production definition's own reference "
            "condition, not a number chosen here")


def test_a_request_carries_the_actual_stream_temperatures():
    request = svc.build_request(svc.DEFAULT_CASE)
    assert request.fuel.temperature == pytest.approx(111.643)
    assert request.oxidiser.temperature == pytest.approx(90.17)
    assert request.of_mass == pytest.approx(3.4)
    assert request.chamber_pressure == pytest.approx(10.0e6)


def test_a_request_uses_the_oxidiser_over_fuel_orientation():
    """O/F is oxidiser mass over fuel mass, and the request says so."""
    case = svc.DEFAULT_CASE.replace(oxidiser_fuel_ratio=6.0)
    request = svc.build_request(case)
    assert request.oxidiser_fuel_ratio.of_mass == pytest.approx(6.0)


def test_an_unknown_propellant_is_refused_by_name():
    with pytest.raises(LookupError, match="NOT_A_PROPELLANT"):
        svc.build_request(svc.DEFAULT_CASE.replace(fuel="NOT_A_PROPELLANT"))


def test_the_catalogue_is_the_providers_production_set():
    """No propellant is offered that the backend cannot map.

    The set is small on purpose: Phase 5C validated five definitions end to
    end, and offering a sixth would be offering something with no provider
    name behind it.
    """
    options = gateway.propellant_options()
    assert {option.key for option in options} == {
        "LOX", "LCH4", "LH2", "GOX", "GCH4"}
    for option in options:
        assert option.provider_name, f"{option.key} has no CEA identity"


# ===========================================================================
# outcome kinds
# ===========================================================================


def test_no_provider_gives_an_unavailable_outcome_and_no_state(absent_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    assert outcome.kind == svc.OUTCOME_UNAVAILABLE
    assert outcome.state is None
    assert svc.result_rows(outcome) == ()
    assert svc.species_rows(outcome) == ()


def test_a_malformed_case_is_refused_before_the_provider(stub_gateway):
    """A negative O/F never reaches the provider.

    Phase 5B-0 measured NASA CEA accepting a negative temperature and a
    negative pressure without complaint, so "the provider will catch it" is
    not true. The spy on the stub is what makes this a proof rather than a
    hope.
    """
    outcome = svc.solve_case(svc.DEFAULT_CASE.replace(oxidiser_fuel_ratio=-1.0))
    assert outcome.kind == svc.OUTCOME_INVALID_INPUT
    assert outcome.state is None
    assert stub_gateway.calls == [], "a malformed request reached the provider"


def test_the_spy_does_see_a_legitimate_call(stub_gateway):
    """The negative control for the test above, so it cannot pass vacuously."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    assert outcome.kind == svc.OUTCOME_OK
    assert len(stub_gateway.calls) == 1


def test_a_non_converged_solve_is_a_no_solution_with_no_numbers(failing_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE.replace(oxidiser_fuel_ratio=3.0))
    assert outcome.kind == svc.OUTCOME_NO_SOLUTION
    assert outcome.state is None
    assert svc.result_rows(outcome) == ()
    assert "did not converge" in outcome.message


def test_no_solution_states_which_check_failed(gateway):
    """A converged result that RocketForge rejected says so, specifically.

    "The provider converged, but RocketForge rejected the result: element
    conservation ..." is scientifically different from "chemistry failed", and
    the distinction survives into the message.
    """
    from rocketforge.core.result import Diagnostic, Severity

    outcome = svc.ChamberOutcome(
        kind=svc.OUTCOME_NO_SOLUTION,
        diagnostics=(Diagnostic(
            code="ELEMENT_BALANCE_VIOLATED", severity=Severity.ERROR,
            message="the products do not conserve the reactants' atoms"),))
    message = svc._no_solution_message(outcome.diagnostics)
    assert "converged" in message
    assert "rejected" in message
    assert "conserve" in message


def test_a_non_convergence_is_not_reported_as_a_rejection():
    from rocketforge.core.result import Diagnostic, Severity

    diagnostics = (Diagnostic(code="PROVIDER_NOT_CONVERGED",
                              severity=Severity.ERROR,
                              message="did not converge"),)
    message = svc._no_solution_message(diagnostics)
    assert "did not converge" in message
    assert "rejected" not in message


def test_every_outcome_kind_has_a_label_and_a_tone():
    for kind in (svc.OUTCOME_EMPTY, svc.OUTCOME_OK, svc.OUTCOME_WARNING,
                 svc.OUTCOME_NO_SOLUTION, svc.OUTCOME_UNAVAILABLE,
                 svc.OUTCOME_INVALID_INPUT, svc.OUTCOME_PROVIDER_ERROR):
        outcome = svc.ChamberOutcome(kind=kind)
        assert outcome.status_label != "Unknown"
        assert outcome.status_tone in ("neutral", "success", "warning", "error")


def test_the_seven_kinds_are_distinct():
    """Phase 5D forbids collapsing every failure into "calculation failed"."""
    kinds = {svc.OUTCOME_EMPTY, svc.OUTCOME_OK, svc.OUTCOME_WARNING,
             svc.OUTCOME_NO_SOLUTION, svc.OUTCOME_UNAVAILABLE,
             svc.OUTCOME_INVALID_INPUT, svc.OUTCOME_PROVIDER_ERROR}
    assert len(kinds) == 7


# ===========================================================================
# readouts
# ===========================================================================


def test_result_rows_carry_units_and_raw_values(stub_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    rows = {row.key: row for row in svc.result_rows(outcome)}
    dimensional = ("temperature", "pressure", "density", "molar_mass",
                   "gas_constant", "cp", "cv")
    for key in dimensional:
        assert rows[key].unit, f"{key} is displayed without a unit"
        assert rows[key].value is not None
    # gamma is genuinely dimensionless, and an invented unit would be worse
    # than none.
    assert rows["gamma"].unit == ""


def test_the_chamber_temperature_carries_its_model(stub_gateway):
    """Never "flame temperature" on its own."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    row = next(r for r in svc.result_rows(outcome) if r.key == "temperature")
    assert "Chamber temperature" in row.label
    assert "Adiabatic" in row.qualifier
    assert "HP equilibrium" in row.qualifier
    assert "wall temperature" in row.help


def test_cp_and_cv_are_labelled_frozen(stub_gateway):
    """The pair on the primary readout is the frozen one, and says so.

    Only the frozen pair satisfies cp - cv = R; the equilibrium heat capacity
    does not and is not meant to. Displaying one under the other's name would
    be a silent error.
    """
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    rows = {row.key: row for row in svc.result_rows(outcome)}
    assert rows["cp"].qualifier == "frozen"
    assert rows["cv"].qualifier == "frozen"
    assert rows["cp_equilibrium"].group == svc.GROUP_ADVANCED
    assert "does not satisfy" in rows["cp_equilibrium"].qualifier


def test_cp_cv_and_gamma_map_from_the_right_state_fields(stub_gateway):
    """No accidental field swaps between the state and the display."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    state = outcome.state
    rows = {row.key: row.value for row in svc.result_rows(outcome)}
    assert rows["cp"] == state.cp
    assert rows["cv"] == state.cv
    assert rows["gamma"] == state.gamma
    assert rows["gamma_frozen"] == state.gamma_frozen
    assert rows["cp_equilibrium"] == state.cp_equilibrium
    assert rows["temperature"] == state.temperature
    assert rows["molar_mass"] == state.molar_mass
    assert rows["gas_constant"] == state.gas_constant
    assert rows["density"] == state.density


def test_the_primary_gamma_is_the_equilibrium_isentropic_exponent(stub_gateway):
    """Phase 5C carries two gammas; the primary readout names which one."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    rows = {row.key: row for row in svc.result_rows(outcome)}
    assert rows["gamma"].qualifier == "equilibrium"
    assert rows["gamma"].value == outcome.state.gamma_equilibrium
    assert rows["gamma_frozen"].value == outcome.state.gamma_frozen
    assert rows["gamma"].value != rows["gamma_frozen"].value


def test_a_quantity_the_state_does_not_carry_is_unavailable_not_zero(stub_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    row = next(r for r in svc.result_rows(outcome) if r.key == "speed_of_sound")
    assert row.value is None
    assert not row.available


#: Whole words that would name a rocket-performance quantity. Matched as
#: words, never as substrings -- "display" contains "isp", which has now
#: produced a false positive in three separate audits in this project,
#: including the one this constant replaces.
BANNED_PERFORMANCE_WORDS = {
    "cstar", "c_star", "cf", "isp", "thrust", "impulse",
    "characteristic", "velocity",
}


def _words(text: str) -> set[str]:
    import re

    return {word.lower() for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)}


def test_no_performance_quantity_is_ever_a_result_row(stub_gateway):
    """RocketForge owns no c*, Cf, Isp or thrust, so none may be displayed."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    for row in svc.result_rows(outcome):
        text = f"{row.key} {row.label} {row.qualifier} {row.help}"
        leaked = _words(text) & BANNED_PERFORMANCE_WORDS
        assert not leaked, f"{row.key} mentions {leaked}"
        assert "c*" not in text.lower(), row.key


def test_the_readout_audit_would_catch_a_real_leak():
    """The negative control, so the scan above cannot be vacuous."""
    assert _words("specific impulse Isp") & BANNED_PERFORMANCE_WORDS
    assert _words("characteristic velocity c_star") & BANNED_PERFORMANCE_WORDS
    assert not (_words("a display reporting threshold")
                & BANNED_PERFORMANCE_WORDS)


# ===========================================================================
# composition
# ===========================================================================


def test_species_rows_are_complete_and_sorted_by_mole_fraction(stub_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    rows = svc.species_rows(outcome)
    assert len(rows) == len(outcome.state.composition.entries)
    fractions = [row.mole_fraction for row in rows]
    assert fractions == sorted(fractions, reverse=True)


def test_species_rows_carry_both_bases_and_a_phase(stub_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    rows = {row.name: row for row in svc.species_rows(outcome)}
    assert rows["H2O"].phase == "gas"
    assert rows["C(gr)"].phase == "solid"
    assert rows["C(gr)"].is_condensed
    assert not rows["H2O"].is_condensed
    assert math.fsum(row.mole_fraction for row in rows.values()) == pytest.approx(1.0)
    assert math.fsum(row.mass_fraction for row in rows.values()) == pytest.approx(1.0)


def test_the_two_bases_actually_differ(stub_gateway):
    """A mole/mass switch that changed nothing would be a broken conversion."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    rows = {row.name: row for row in svc.species_rows(outcome)}
    assert rows["CO2"].mass_fraction != rows["CO2"].mole_fraction


def test_the_mass_basis_matches_the_domain_conversion(stub_gateway):
    """The application does not implement its own mole-to-mass algebra."""
    from rocketforge.physics.thermochemistry import CompositionBasis

    outcome = svc.solve_case(svc.DEFAULT_CASE)
    species = svc.species_table(outcome)
    expected = dict(outcome.state.composition.to_basis(
        CompositionBasis.MASS_FRACTION, species).fractions)
    for row in svc.species_rows(outcome):
        assert row.mass_fraction == expected[row.name]


# ===========================================================================
# condensed phases
# ===========================================================================


def test_a_fraction_below_the_reporting_threshold_is_not_called_none(stub_gateway):
    """A measured 6e-08 is not zero, and the interface must not say it is.

    The stub carries solid carbon at a mole fraction of 1e-08, the same shape
    as the canonical Phase 5C production case. "Condensed products present"
    would be false there -- and so would "none detected", because something is
    genuinely there. The state between them is what gets reported.
    """
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    summary = svc.condensed_summary(outcome)
    assert summary["state"] == svc.CONDENSED_BELOW_THRESHOLD
    assert summary["known"] is True
    assert summary["present"] is False
    assert summary["fraction"] > 0.0, (
        "the fixture must actually contain a condensed candidate, or this "
        "test proves nothing")
    assert summary["fraction"] < summary["threshold"]

    assert summary["headline"] == "No condensed phase above reporting threshold"
    assert "none detected" not in summary["headline"].lower()
    assert "none detected" not in summary["detail"].lower()
    # Both numbers the verdict is about are carried.
    assert f"{summary['fraction']:.3e}" in summary["detail"]
    assert "reporting threshold" in summary["detail"]


def test_a_fraction_of_exactly_zero_is_reported_as_none(no_condensed_gateway):
    """The state below-threshold is *not*: nothing is there at all."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    summary = svc.condensed_summary(outcome)
    assert summary["state"] == svc.CONDENSED_NONE_REPORTED
    assert summary["known"] is True
    assert summary["present"] is False
    assert summary["fraction"] == 0.0
    assert summary["headline"] == "No condensed product reported"
    assert summary["species"] == ()


def test_a_fraction_at_or_above_the_threshold_is_reported_as_present(
        condensed_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    summary = svc.condensed_summary(outcome)
    assert summary["state"] == svc.CONDENSED_PRESENT
    assert summary["present"] is True
    assert summary["fraction"] >= summary["threshold"]
    assert summary["headline"] == "Condensed products present"
    assert "C(gr)" in [row.name for row in summary["species"]]


def test_the_four_condensed_states_are_distinct():
    assert len({svc.CONDENSED_UNKNOWN, svc.CONDENSED_NONE_REPORTED,
                svc.CONDENSED_BELOW_THRESHOLD, svc.CONDENSED_PRESENT}) == 4


def test_the_reporting_threshold_is_a_reporting_threshold():
    """It decides a sentence. It must not decide any number.

    Nothing in the domain or the provider may read it, and the modules that do
    read it must be describing a result rather than producing one.
    """
    import pathlib

    from rocketforge.application.analysis import thermochemistry_controller

    assert svc.CONDENSED_REPORTING_THRESHOLD == 1.0e-6

    package = pathlib.Path(svc.__file__).resolve().parents[3] / "rocketforge"
    for area in ("physics", "providers", "core", "engineering"):
        for path in (package / area).rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            assert "CONDENSED_REPORTING_THRESHOLD" not in source, path
            assert "reporting threshold" not in source.lower(), path

    # And the state is derived from the fraction, not the other way round.
    assert "condensed_mass_fraction" not in thermochemistry_controller.__doc__


def test_an_unknown_condensed_fraction_is_not_reported_as_absent(stub_gateway):
    """"The provider did not say" is not "there is none", either."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    blind = svc.ChamberOutcome(
        kind=outcome.kind,
        case=outcome.case,
        state=_without_condensed(outcome.state),
        diagnostics=outcome.diagnostics,
        provenance=outcome.provenance)
    summary = svc.condensed_summary(blind)
    assert summary["state"] == svc.CONDENSED_UNKNOWN
    assert summary["known"] is False
    assert summary["present"] is False
    assert "Unknown is not the same as none" in summary["detail"]


def _without_condensed(state):
    from dataclasses import replace

    return replace(state, condensed_mass_fraction=None)


# ===========================================================================
# diagnostics
# ===========================================================================


def test_a_warning_reaches_the_diagnostic_rows(warning_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    assert outcome.kind == svc.OUTCOME_WARNING
    assert outcome.state is not None, "a warning must not hide the result"
    rows = svc.diagnostic_rows(outcome, include_info=False)
    assert [row.code for row in rows] == ["PROVIDER_ASSIGNED_ENTHALPY_REACTANT"]
    assert rows[0].severity == "warning"


def test_the_assigned_enthalpy_note_carries_all_three_numbers(warning_gateway):
    notes = svc.assigned_enthalpy_notes(svc.solve_case(svc.DEFAULT_CASE))
    assert len(notes) == 1
    assert notes[0]["reactant"] == "O2(L)"
    assert notes[0]["requested"] == pytest.approx(95.0)
    assert notes[0]["assigned"] == pytest.approx(90.17)


def test_an_unrecognised_diagnostic_code_still_reaches_the_display():
    """A backend that adds a code this build never heard of must not vanish."""
    from rocketforge.core.result import Diagnostic, Severity

    outcome = svc.ChamberOutcome(
        kind=svc.OUTCOME_WARNING,
        diagnostics=(Diagnostic(code="SOME_FUTURE_CODE",
                                severity=Severity.WARNING,
                                message="something new happened"),))
    rows = svc.diagnostic_rows(outcome)
    assert len(rows) == 1
    assert rows[0].known is False
    assert "SOME_FUTURE_CODE" in rows[0].title
    assert rows[0].message == "something new happened"


def test_severity_is_carried_through_unchanged():
    from rocketforge.core.result import Diagnostic, Severity

    outcome = svc.ChamberOutcome(
        kind=svc.OUTCOME_WARNING,
        diagnostics=(
            Diagnostic(code="A", severity=Severity.INFO, message="i"),
            Diagnostic(code="B", severity=Severity.ERROR, message="e"),
            Diagnostic(code="C", severity=Severity.WARNING, message="w"),
        ))
    rows = svc.diagnostic_rows(outcome)
    assert [row.severity for row in rows] == ["error", "warning", "info"]


# ===========================================================================
# provenance
# ===========================================================================


def test_provenance_comes_from_the_result_not_from_the_environment(stub_gateway):
    """A result keeps the identity of whatever produced it.

    Checked with a stub precisely because the installed library is something
    else: if the display read the environment, this would say 3.3.4.
    """
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    summary = svc.provenance_summary(outcome)
    assert "0.0-stub" in summary["provider"]
    assert summary["database"] == "stub.lib"
    rows = {row["label"]: row["value"] for row in svc.provenance_details(outcome)}
    assert rows["Provider id"] == "stub:phase5d"
    assert rows["Heat-loss assumption"] == "Adiabatic"


def test_provenance_details_name_the_provider_reactants(stub_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    rows = {row["label"]: row["value"] for row in svc.provenance_details(outcome)}
    assert rows["Oxidiser (provider name)"] == "O2(L)"
    assert rows["Fuel (provider name)"] == "CH4(L)"


def test_the_case_headline_describes_the_result_not_the_form(stub_gateway):
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    headline = svc.case_headline(outcome.case)
    assert "LOX / LCH4" in headline
    assert "O/F 3.4" in headline
    assert "100 bar" in headline


# ===========================================================================
# live provider
# ===========================================================================


@requires_cea
def test_the_live_pipeline_solves_the_production_case():
    """application -> provider -> ChamberGas -> display rows, for real."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    assert outcome.kind == svc.OUTCOME_OK
    rows = {row.key: row.value for row in svc.result_rows(outcome)}
    # Phase 5C's canonical value for this case.
    assert rows["temperature"] == pytest.approx(3598.2854, abs=1.0e-3)
    assert rows["molar_mass"] == pytest.approx(0.021770088, rel=1.0e-6)
    assert rows["gas_constant"] == pytest.approx(381.9214, rel=1.0e-6)


@requires_cea
def test_the_live_state_satisfies_cp_minus_cv_equals_R():
    """The pair the interface labels "frozen" is the one that closes."""
    state = svc.solve_case(svc.DEFAULT_CASE).state
    assert state.cp - state.cv == pytest.approx(state.gas_constant, rel=1.0e-5)


@requires_cea
def test_the_live_gammas_are_measurably_different():
    """One field cannot carry both, which is why the labels matter."""
    state = svc.solve_case(svc.DEFAULT_CASE).state
    relative = abs(state.gamma_frozen - state.gamma) / state.gamma
    assert relative > 0.01, (
        "the two gammas should differ by percent-level amounts on a real "
        "LOX/CH4 chamber")


@requires_cea
def test_the_live_composition_is_complete_and_sums_to_one():
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    rows = svc.species_rows(outcome)
    assert len(rows) == 28
    assert math.fsum(row.mole_fraction for row in rows) == pytest.approx(1.0)
    assert math.fsum(row.mass_fraction for row in rows) == pytest.approx(1.0)


@requires_cea
def test_the_live_condensed_candidate_is_not_reported_as_present():
    """The Phase 5C trap, at the application boundary.

    The canonical case has condensed species among the *candidates* and
    6.24e-08 of mass actually present. The workspace must not announce
    condensed material -- and must not claim there is none either.
    """
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    summary = svc.condensed_summary(outcome)
    assert summary["state"] == svc.CONDENSED_BELOW_THRESHOLD
    assert summary["present"] is False
    assert 0.0 < summary["fraction"] < svc.CONDENSED_REPORTING_THRESHOLD
    assert "none detected" not in (
        summary["headline"] + summary["detail"]).lower()
    carbon = [row for row in svc.species_rows(outcome) if row.name == "C(gr)"]
    assert carbon and carbon[0].is_condensed, (
        "the candidate must really be in the composition, or this proves "
        "nothing")


@requires_cea
def test_the_live_fuel_rich_case_does_report_real_condensed_carbon():
    """The other half of the pair: genuine solid carbon at O/F 0.5."""
    outcome = svc.solve_case(svc.DEFAULT_CASE.replace(oxidiser_fuel_ratio=0.5))
    summary = svc.condensed_summary(outcome)
    assert summary["state"] == svc.CONDENSED_PRESENT
    assert summary["present"] is True
    assert summary["fraction"] > 1.0e-3
    assert "C(gr)" in [row.name for row in summary["species"]]


@requires_cea
def test_the_live_assigned_enthalpy_warning_reaches_the_application():
    """BLOCKING for Phase 5D: the caveat must not be swallowed."""
    outcome = svc.solve_case(svc.DEFAULT_CASE.replace(oxidiser_temperature=95.0))
    assert outcome.kind == svc.OUTCOME_WARNING
    assert outcome.state is not None
    notes = svc.assigned_enthalpy_notes(outcome)
    assert len(notes) == 1
    assert notes[0]["reactant"] == "O2(L)"
    assert notes[0]["requested"] == pytest.approx(95.0)
    assert notes[0]["assigned"] == pytest.approx(90.17)


@requires_cea
def test_a_temperature_dependent_reactant_raises_no_such_warning():
    """The negative control. Gaseous reactants respond to temperature."""
    case = svc.ChamberCase(fuel="GCH4", oxidiser="GOX",
                           oxidiser_fuel_ratio=3.4, chamber_pressure=10.0e6,
                           fuel_temperature=320.0, oxidiser_temperature=320.0)
    outcome = svc.solve_case(case)
    assert outcome.kind == svc.OUTCOME_OK
    assert svc.assigned_enthalpy_notes(outcome) == ()


@requires_cea
def test_a_gaseous_reactant_temperature_actually_changes_the_answer():
    """Proves the control above is a control and not an accident."""
    warm = svc.ChamberCase(fuel="GCH4", oxidiser="GOX",
                           oxidiser_fuel_ratio=3.4, chamber_pressure=10.0e6,
                           fuel_temperature=320.0, oxidiser_temperature=320.0)
    cool = warm.replace(fuel_temperature=298.15, oxidiser_temperature=298.15)
    assert (svc.solve_case(warm).state.temperature
            != svc.solve_case(cool).state.temperature)


@requires_cea
def test_a_stream_outside_the_providers_range_is_refused_with_the_range():
    outcome = svc.solve_case(svc.DEFAULT_CASE.replace(oxidiser_temperature=200.0))
    assert outcome.kind == svc.OUTCOME_PROVIDER_ERROR
    assert outcome.state is None
    assert "80.17" in outcome.message and "100.17" in outcome.message


@requires_cea
def test_an_of_outside_the_providers_range_is_refused_with_the_range():
    outcome = svc.solve_case(svc.DEFAULT_CASE.replace(oxidiser_fuel_ratio=500.0))
    assert outcome.kind == svc.OUTCOME_PROVIDER_ERROR
    assert "0.01" in outcome.message and "100.0" in outcome.message


@requires_cea
def test_the_live_provenance_names_the_bundled_database():
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    summary = svc.provenance_summary(outcome)
    assert summary["database"] == "thermo.lib"
    assert summary["sha"].startswith("8e5df1cc")
    assert "3.3.4" in summary["provider"]
