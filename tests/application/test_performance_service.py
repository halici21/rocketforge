"""The performance application service: the handoff, and what it refuses.

The blocking property of this phase lives here. Ideal performance is algebra
over an already-solved chamber state, so changing a nozzle input must cost
**zero** chamber solves. The stub provider records every call it receives, and
the tests below assert on that count rather than on a timing or a cache hit.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.application.analysis import performance_service as service
from rocketforge.application.analysis.thermochemistry_service import (
    DEFAULT_CASE,
    ChamberOutcome,
    solve_case,
)
from rocketforge.engineering.chamber import ChamberGammaBasis
from rocketforge.engineering.nozzle import PerformanceScale, PerformanceScaleMode
from rocketforge.physics.thermochemistry import GammaStrategy


@pytest.fixture()
def chamber(stub_gateway):
    """A genuine ``ChamberOutcome``, produced by the real service.

    Built through ``solve_case`` rather than assembled by hand so that the
    handoff being tested is the one the application actually performs.
    """
    outcome = solve_case(DEFAULT_CASE)
    assert outcome.state is not None, outcome.message
    return outcome


@pytest.fixture()
def warned_chamber(warning_gateway):
    outcome = solve_case(DEFAULT_CASE)
    assert outcome.state is not None
    return outcome


# ===========================================================================
# ambient semantics
# ===========================================================================


def test_vacuum_is_zero_pascals_not_a_missing_value():
    ambient = service.AmbientCondition(service.AmbientMode.VACUUM)
    assert ambient.pressure == 0.0
    assert "0" in ambient.label


def test_sea_level_is_the_isa_value():
    ambient = service.AmbientCondition(service.AmbientMode.SEA_LEVEL)
    assert ambient.pressure == service.STANDARD_SEA_LEVEL_PRESSURE == 101325.0


def test_a_custom_ambient_uses_the_number_given():
    ambient = service.AmbientCondition(service.AmbientMode.CUSTOM, 5000.0)
    assert ambient.pressure == 5000.0


def test_a_preset_ignores_the_custom_field_rather_than_clearing_it():
    """Switching to a preset must not destroy what the user typed."""
    ambient = service.AmbientCondition(service.AmbientMode.VACUUM, 4321.0)
    assert ambient.pressure == 0.0
    assert ambient.custom_pressure == 4321.0


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
def test_a_custom_ambient_below_zero_or_not_finite_is_refused(bad):
    with pytest.raises(ValueError):
        service.AmbientCondition(service.AmbientMode.CUSTOM, bad)


def test_an_ambient_mode_must_be_the_enum():
    with pytest.raises(TypeError):
        service.AmbientCondition("vacuum")           # type: ignore[arg-type]


# ===========================================================================
# refusals
# ===========================================================================


def test_no_chamber_state_refuses_and_says_where_to_get_one():
    outcome = service.solve_performance(None, service.DEFAULT_PERFORMANCE_CASE)
    assert outcome.kind == service.OUTCOME_NO_CHAMBER
    assert outcome.result is None
    assert "thermochemistry" in outcome.message.lower()


def test_an_unsolved_chamber_outcome_refuses_too():
    empty = ChamberOutcome(kind="empty")
    outcome = service.solve_performance(empty, service.DEFAULT_PERFORMANCE_CASE)
    assert outcome.kind == service.OUTCOME_NO_CHAMBER
    assert outcome.result is None


def test_a_condensed_phase_refuses_the_reduction(condensed_gateway):
    """The single-phase precondition is enforced through this path too."""
    chamber = solve_case(DEFAULT_CASE)
    assert chamber.state is not None
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    assert outcome.kind == service.OUTCOME_REDUCTION_REFUSED
    assert outcome.result is None
    assert any(d.code == "CONDENSED_PHASE_PRESENT" for d in outcome.diagnostics)
    assert outcome.message


def test_an_area_ratio_at_or_below_one_is_refused_as_input(chamber):
    case = service.DEFAULT_PERFORMANCE_CASE.replace(area_ratio=0.5)
    outcome = service.solve_performance(chamber, case)
    assert outcome.kind == service.OUTCOME_INVALID_INPUT
    assert outcome.result is None


def test_a_regime_outside_the_ideal_model_is_refused_not_reported(chamber):
    """An internal shock is a different internal solution, not a worse one."""
    case = service.DEFAULT_PERFORMANCE_CASE.replace(
        ambient=service.AmbientCondition(service.AmbientMode.CUSTOM, 5.0e6))
    outcome = service.solve_performance(chamber, case)
    assert outcome.kind == service.OUTCOME_NOZZLE_REFUSED
    assert outcome.result is None
    assert outcome.message


def test_a_refusal_still_carries_the_case_and_the_chamber(chamber):
    case = service.DEFAULT_PERFORMANCE_CASE.replace(area_ratio=0.5)
    outcome = service.solve_performance(chamber, case)
    assert outcome.case is case
    assert outcome.chamber is chamber


# ===========================================================================
# the solved result
# ===========================================================================


def test_a_default_case_solves(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    assert outcome.kind in (service.OUTCOME_OK, service.OUTCOME_WARNING)
    assert outcome.result is not None
    assert outcome.ok


def test_the_result_holds_the_chamber_it_was_computed_from_by_identity(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    assert outcome.chamber is chamber


def test_the_headline_names_both_halves_of_the_question(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    headline = outcome.headline
    assert "O/F" in headline                       # the chamber half
    assert "Ae/At" in headline                     # the nozzle half
    assert "vacuum" in headline


def test_the_headline_comes_from_the_case_not_from_a_later_edit(chamber):
    """A result must not be relabelled by an input the user changed after it."""
    first = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    later = service.DEFAULT_PERFORMANCE_CASE.replace(area_ratio=200.0)
    assert "Ae/At 200" not in first.headline
    assert "Ae/At 200" in later.headline


def test_a_chamber_warning_propagates_into_the_performance_status(warned_chamber):
    outcome = service.solve_performance(warned_chamber,
                                        service.DEFAULT_PERFORMANCE_CASE)
    assert outcome.kind == service.OUTCOME_WARNING
    assert outcome.result is not None       # a warning does not withhold numbers


def test_the_assigned_enthalpy_caveat_survives_the_layer_boundary(warned_chamber):
    outcome = service.solve_performance(warned_chamber,
                                        service.DEFAULT_PERFORMANCE_CASE)
    inherited = service.inherited_diagnostics(outcome)
    codes = {row["code"] for row in inherited}
    assert "PROVIDER_ASSIGNED_ENTHALPY_REACTANT" in codes
    assert all(row["origin"] == "thermochemistry" for row in inherited)


def test_own_diagnostics_are_tagged_separately(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    assert all(row["origin"] == "performance"
               for row in service.own_diagnostics(outcome))


# ===========================================================================
# ambient pressure changes the right things and nothing else
# ===========================================================================


def _solved(chamber, **changes):
    case = service.DEFAULT_PERFORMANCE_CASE.replace(**changes)
    outcome = service.solve_performance(chamber, case)
    assert outcome.result is not None, outcome.message
    return outcome.result


def test_ambient_pressure_never_changes_characteristic_velocity(chamber):
    """c* is a chamber and throat quantity. This is the headline invariant."""
    vacuum = _solved(chamber)
    sea = _solved(chamber, ambient=service.AmbientCondition(
        service.AmbientMode.SEA_LEVEL))
    assert vacuum.characteristic_velocity == sea.characteristic_velocity


def test_ambient_pressure_never_changes_the_exit_state(chamber):
    """The internal solution is fixed by the area ratio and gamma alone."""
    vacuum = _solved(chamber)
    sea = _solved(chamber, ambient=service.AmbientCondition(
        service.AmbientMode.SEA_LEVEL))
    assert vacuum.exit.mach == sea.exit.mach
    assert vacuum.exit.pressure == sea.exit.pressure
    assert vacuum.exit.velocity == sea.exit.velocity


def test_ambient_pressure_changes_only_the_pressure_term(chamber):
    vacuum = _solved(chamber)
    sea = _solved(chamber, ambient=service.AmbientCondition(
        service.AmbientMode.SEA_LEVEL))
    assert vacuum.thrust_coefficient_momentum == sea.thrust_coefficient_momentum
    assert sea.thrust_coefficient_pressure < vacuum.thrust_coefficient_pressure


def test_an_overexpanded_pressure_term_stays_negative(chamber):
    """Never clamped. A nozzle at sea level really does lose thrust here."""
    sea = _solved(chamber, ambient=service.AmbientCondition(
        service.AmbientMode.SEA_LEVEL))
    assert sea.exit.pressure < service.STANDARD_SEA_LEVEL_PRESSURE
    assert sea.thrust_coefficient_pressure < 0.0


def test_specific_impulse_is_in_seconds_and_effective_velocity_in_metres(chamber):
    result = _solved(chamber)
    assert result.specific_impulse < result.effective_exhaust_velocity
    ratio = result.effective_exhaust_velocity / result.specific_impulse
    assert ratio == pytest.approx(9.80665, rel=1e-9)


def test_the_effective_exhaust_velocity_is_not_the_exit_velocity(chamber):
    """They coincide only at ideal expansion, and vacuum is not that."""
    result = _solved(chamber)
    assert result.effective_exhaust_velocity != result.exit.velocity


# ===========================================================================
# scale
# ===========================================================================


def test_an_unscaled_result_withholds_thrust_rather_than_zeroing_it(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    assert outcome.result is not None
    assert not outcome.is_scaled
    assert outcome.result.thrust is None
    assert service.thrust_rows(outcome) == ()


def test_scaling_by_throat_area_produces_the_engine_group(chamber):
    case = service.DEFAULT_PERFORMANCE_CASE.replace(
        scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    outcome = service.solve_performance(chamber, case)
    assert outcome.is_scaled
    rows = {row.key: row for row in service.thrust_rows(outcome)}
    assert set(rows) == {"throat_area", "exit_area", "mass_flow",
                         "momentum_thrust", "pressure_thrust", "total_thrust"}
    assert rows["throat_area"].value == pytest.approx(0.01)
    assert all(row.available for row in rows.values())


def test_the_two_scale_modes_describe_the_same_engine(chamber):
    """Sizing by mass flow must reproduce the throat area that produces it."""
    by_area = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE
                                        .replace(scale=PerformanceScale(
                                            PerformanceScaleMode.THROAT_AREA, 0.01)))
    mass_flow = by_area.result.mass_flow
    by_flow = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE
                                        .replace(scale=PerformanceScale(
                                            PerformanceScaleMode.MASS_FLOW, mass_flow)))
    assert by_flow.result.throat_area == pytest.approx(0.01, rel=1e-12)
    assert by_flow.result.thrust.total == pytest.approx(
        by_area.result.thrust.total, rel=1e-12)


def test_scale_never_changes_a_scale_free_quantity(chamber):
    plain = _solved(chamber)
    scaled = _solved(chamber, scale=PerformanceScale(
        PerformanceScaleMode.THROAT_AREA, 0.25))
    for name in ("characteristic_velocity", "thrust_coefficient",
                 "effective_exhaust_velocity", "specific_impulse"):
        assert getattr(plain, name) == getattr(scaled, name), name


# ===========================================================================
# display rows
# ===========================================================================


def test_every_performance_row_belongs_to_a_declared_group(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    groups = {group["key"] for group in service.PERFORMANCE_GROUPS}
    for row in service.performance_rows(outcome) + service.thrust_rows(outcome):
        assert row.group in groups, row.key


def test_characteristic_velocity_is_grouped_with_the_chamber_not_the_nozzle(chamber):
    """The grouping is what stops a reader taking c* for an exhaust velocity."""
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    rows = {row.key: row for row in service.performance_rows(outcome)}
    assert rows["c_star"].group == service.GROUP_CHAMBER
    assert rows["cf"].group == service.GROUP_NOZZLE
    assert rows["c_eff"].group == service.GROUP_TOTAL
    assert rows["isp"].group == service.GROUP_TOTAL


def test_every_row_carries_its_unit_and_the_dimensionless_ones_are_blank(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    rows = {row.key: row for row in service.performance_rows(outcome)}
    assert rows["c_star"].unit == "m/s"
    assert rows["isp"].unit == "s"
    assert rows["cf"].unit == ""
    assert rows["exit_mach"].unit == ""


def test_the_help_text_says_what_c_star_is_not(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    rows = {row.key: row for row in service.performance_rows(outcome)}
    assert "not the exhaust velocity" in rows["c_star"].help.lower()
    assert "second" in rows["isp"].help.lower()


def test_rows_carry_numbers_not_strings(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    for row in service.performance_rows(outcome):
        assert isinstance(row.value, float), row.key
        assert math.isfinite(row.value)


def test_no_rows_at_all_without_a_result():
    outcome = service.solve_performance(None, service.DEFAULT_PERFORMANCE_CASE)
    assert service.performance_rows(outcome) == ()
    assert service.thrust_rows(outcome) == ()
    assert service.reduction_rows(outcome) == ()
    assert service.identity_rows(outcome) == ()


def test_the_assumptions_are_available_before_any_result_exists():
    """A reader may want to know what the model claims before running it."""
    outcome = service.solve_performance(None, service.DEFAULT_PERFORMANCE_CASE)
    assumptions = service.assumption_rows(outcome)
    assert assumptions
    assert any("no efficiency factor" in text.lower() for text in assumptions)


def test_a_solved_result_adds_the_reduction_assumptions(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    before = set(service.assumption_rows(service.EMPTY_OUTCOME))
    after = set(service.assumption_rows(outcome))
    assert before < after


def test_the_reduction_is_shown_in_full(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    labels = {row["label"] for row in service.reduction_rows(outcome)}
    for expected in ("Gamma strategy", "Gamma basis", "Gamma used",
                     "Gamma taken from", "Nozzle regime",
                     "Condensed mass fraction accepted"):
        assert expected in labels


def test_every_identity_closes(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    rows = service.identity_rows(outcome)
    assert rows
    assert all(row["passed"] for row in rows), [r for r in rows if not r["passed"]]


def test_a_scaled_result_checks_more_identities_than_an_unscaled_one(chamber):
    plain = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    scaled = service.solve_performance(
        chamber, service.DEFAULT_PERFORMANCE_CASE.replace(
            scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01)))
    assert len(service.identity_rows(scaled)) > len(service.identity_rows(plain))


# ===========================================================================
# provenance
# ===========================================================================


def test_provenance_keeps_the_two_claims_apart(chamber):
    rows = service.performance_provenance(
        service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE))
    assert len(rows) == 2
    performance, chemistry = rows
    assert performance["computed_by"] == "RocketForge"
    assert chemistry["computed_by"] != "RocketForge"
    assert "stub" in chemistry["computed_by"].lower() or chemistry["detail"]


def test_the_rocketforge_row_does_not_name_a_chemistry_provider(chamber):
    """RocketForge's equations must never be attributed to the provider."""
    rows = service.performance_provenance(
        service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE))
    text = " ".join(str(value) for value in rows[0].values()).lower()
    for name in ("cea", "cantera", "coolprop", "stub"):
        assert name not in text, name


def test_provenance_is_present_even_with_no_chamber():
    rows = service.performance_provenance(
        service.solve_performance(None, service.DEFAULT_PERFORMANCE_CASE))
    assert len(rows) == 2
    assert rows[0]["computed_by"] == "RocketForge"


# ===========================================================================
# reference conditions
# ===========================================================================


def test_the_optimum_reference_has_no_pressure_term(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    reference = service.reference_condition_results(outcome)
    assert reference["optimum"].thrust_coefficient_pressure == pytest.approx(
        0.0, abs=1e-12)
    assert reference["optimum"].is_ideally_expanded


def test_the_vacuum_reference_is_the_larger_of_the_two(chamber):
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    reference = service.reference_condition_results(outcome)
    assert (reference["vacuum"].specific_impulse
            > reference["optimum"].specific_impulse)


def test_both_references_use_the_same_gas_as_the_result(chamber):
    """They re-solve the nozzle, never the chemistry."""
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    reference = service.reference_condition_results(outcome)
    for key in ("vacuum", "optimum"):
        assert reference[key].reduced is outcome.result.reduced
        assert (reference[key].characteristic_velocity
                == outcome.result.characteristic_velocity)


def test_reference_conditions_are_empty_without_a_result():
    reference = service.reference_condition_results(service.EMPTY_OUTCOME)
    assert reference == {"vacuum": None, "optimum": None}


# ===========================================================================
# ZERO CHEMISTRY RE-SOLVE -- the blocking property of this phase
# ===========================================================================


def test_solving_the_chamber_once_costs_exactly_one_provider_call(stub_gateway):
    """The baseline the counts below are measured against."""
    assert stub_gateway.calls == []
    solve_case(DEFAULT_CASE)
    assert len(stub_gateway.calls) == 1


def test_a_first_performance_solve_costs_no_provider_call(stub_gateway):
    chamber = solve_case(DEFAULT_CASE)
    before = len(stub_gateway.calls)
    service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    assert len(stub_gateway.calls) == before


@pytest.mark.parametrize("changes", [
    pytest.param({"area_ratio": 5.0}, id="area-ratio"),
    pytest.param({"area_ratio": 120.0}, id="area-ratio-large"),
    pytest.param({"ambient": service.AmbientCondition(
        service.AmbientMode.SEA_LEVEL)}, id="ambient-sea-level"),
    pytest.param({"ambient": service.AmbientCondition(
        service.AmbientMode.CUSTOM, 12345.0)}, id="ambient-custom"),
    pytest.param({"scale": PerformanceScale(
        PerformanceScaleMode.THROAT_AREA, 0.02)}, id="scale-throat-area"),
    pytest.param({"scale": PerformanceScale(
        PerformanceScaleMode.MASS_FLOW, 40.0)}, id="scale-mass-flow"),
    pytest.param({"gamma_basis": ChamberGammaBasis.EQUILIBRIUM},
                 id="gamma-basis"),
    pytest.param({"gamma_strategy": GammaStrategy.THROAT}, id="gamma-strategy"),
])
def test_changing_a_performance_input_costs_zero_chamber_solves(stub_gateway,
                                                                changes):
    """Section 80, the blocking requirement, one input at a time."""
    chamber = solve_case(DEFAULT_CASE)
    baseline = len(stub_gateway.calls)
    assert baseline == 1

    case = service.DEFAULT_PERFORMANCE_CASE
    for _ in range(5):
        case = case.replace(**changes)
        outcome = service.solve_performance(chamber, case)
        assert outcome.result is not None, outcome.message
    assert len(stub_gateway.calls) == baseline


def test_a_long_sequence_of_input_changes_costs_zero_chamber_solves(stub_gateway):
    """The realistic case: a user moving several controls in a row."""
    chamber = solve_case(DEFAULT_CASE)
    baseline = len(stub_gateway.calls)
    case = service.DEFAULT_PERFORMANCE_CASE
    for ratio in (5.0, 10.0, 20.0, 40.0, 80.0):
        for pressure in (0.0, 101325.0, 50000.0):
            case = case.replace(
                area_ratio=ratio,
                ambient=service.AmbientCondition(
                    service.AmbientMode.CUSTOM, pressure))
            service.solve_performance(chamber, case)
    assert len(stub_gateway.calls) == baseline


def test_the_reference_conditions_cost_zero_chamber_solves(stub_gateway):
    """The oracle comparison re-solves the nozzle, never the chemistry."""
    chamber = solve_case(DEFAULT_CASE)
    outcome = service.solve_performance(chamber, service.DEFAULT_PERFORMANCE_CASE)
    baseline = len(stub_gateway.calls)
    service.reference_condition_results(outcome)
    assert len(stub_gateway.calls) == baseline


def test_the_spy_would_notice_a_real_chemistry_re_solve(stub_gateway):
    """The negative control: the counter is not vacuously constant."""
    solve_case(DEFAULT_CASE)
    baseline = len(stub_gateway.calls)
    solve_case(DEFAULT_CASE.replace(oxidiser_fuel_ratio=3.6))
    assert len(stub_gateway.calls) == baseline + 1


def _imported_modules(module) -> set[str]:
    """Every module name this module imports, at any nesting depth.

    Read from the syntax tree rather than by scanning text: the docstrings here
    discuss the provider at length in order to explain why it is *not*
    imported, and a substring scan reports exactly those sentences. That is the
    same false positive that flagged ``chamberPressureDisplay`` for containing
    "isp" three separate times in Phase 5D.
    """
    import ast
    import inspect

    names: set[str] = set()
    for node in ast.walk(ast.parse(inspect.getsource(module))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


#: The only door to a chemistry provider in the application layer.
PROVIDER_GATEWAY = "thermochemistry_provider"


def test_the_service_module_never_reaches_a_provider():
    """The structural half of the zero-re-solve guarantee.

    It is not a cache and not a flag. This module imports neither a provider
    package nor the gateway that resolves one, so there is no expression in it
    that could start a chemistry solve. The behavioural half -- that a
    performance solve costs zero provider calls -- is the spy above.
    """
    for name in _imported_modules(service):
        assert "providers" not in name, name
        assert PROVIDER_GATEWAY not in name, name


def test_the_import_audit_would_catch_a_real_provider_reference():
    """The negative control: the matcher is not vacuous.

    The oracle module is the contrast. It exists to call the provider, so it
    imports the gateway -- and it is deliberately not imported by the
    performance chain.
    """
    from rocketforge.application.analysis import performance_oracle

    imported = _imported_modules(performance_oracle)
    assert any(PROVIDER_GATEWAY in name for name in imported), imported


def test_the_performance_chain_does_not_import_the_oracle():
    """The oracle is reachable from the controller, never from the model.

    A provider's c*, Cf and Isp must not be able to reach a RocketForge
    performance field even by accident, and the simplest guarantee of that is
    that the module computing those fields cannot see them.
    """
    for name in _imported_modules(service):
        assert "performance_oracle" not in name, name
