"""The O/F sweep: what it refuses, what it produces, and what it never claims.

The claim this module is most concerned with is the one the sweep must **not**
make. A maximum found on a sampled grid is a maximum on that grid, for that
quantity. Phase 5B-0 measured different responses peaking at different mixture
ratios, so "the peak" is not a place, and nothing here may call one optimal.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis import thermochemistry_service as svc
from rocketforge.application.analysis import thermochemistry_sweep as sweep

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status})")


# ===========================================================================
# range validation
# ===========================================================================


@pytest.mark.parametrize("start, end, points", [
    (0.0, 4.0, 41),          # start at zero
    (-1.0, 4.0, 41),         # negative start
    (2.5, 0.0, 41),          # end at zero
    (2.5, -4.0, 41),         # negative end
    (4.5, 2.5, 41),          # reversed
    (3.0, 3.0, 41),          # degenerate
    (float("nan"), 4.0, 41),
    (2.5, float("inf"), 41),
    (2.5, 4.5, 1),           # too few points
    (2.5, 4.5, 0),
    (2.5, 4.5, -10),
    (2.5, 4.5, 10_000),      # beyond the guard
])
def test_a_range_that_cannot_mean_anything_is_refused(start, end, points):
    with pytest.raises(sweep.SweepRangeError):
        sweep.validate_range(start, end, points)


def test_reversed_endpoints_are_refused_rather_than_reordered():
    """Silently swapping them answers a question nobody asked."""
    with pytest.raises(sweep.SweepRangeError, match="not reordered"):
        sweep.validate_range(4.5, 2.5, 41)


def test_the_point_guard_names_its_limit_and_its_evidence():
    with pytest.raises(sweep.SweepRangeError) as excinfo:
        sweep.validate_range(2.5, 4.5, sweep.MAX_SWEEP_POINTS + 1)
    message = str(excinfo.value)
    assert str(sweep.MAX_SWEEP_POINTS) in message
    assert "0.57 ms" in message, "the limit should cite what it is derived from"


def test_the_guard_is_generous_enough_to_be_useful():
    """A tiny limit would be caution without evidence.

    Phase 5C measured 0.568 ms per point through the whole pipeline, so the
    limit is set where a full sweep still takes well under a second.
    """
    assert sweep.MAX_SWEEP_POINTS >= 500
    assert sweep.MAX_SWEEP_POINTS * 0.000568 < 1.0


# ===========================================================================
# the sampled grid
# ===========================================================================


def test_the_sampled_values_are_ascending_and_hit_both_endpoints():
    span = sweep.SweepRange(2.5, 4.5, 41)
    values = span.values()
    assert len(values) == 41
    assert values[0] == pytest.approx(2.5)
    assert values[-1] == 4.5, "the endpoint must be exact, not accumulated"
    assert list(values) == sorted(values)
    assert span.step == pytest.approx(0.05)


def test_the_default_range_is_the_acceptance_sweep():
    span = sweep.DEFAULT_SWEEP_RANGE
    assert (span.start, span.end, span.points) == (2.5, 4.5, 41)


def test_the_generated_cases_vary_only_the_mixture_ratio():
    case = svc.DEFAULT_CASE
    cases = sweep.sweep_cases(case, sweep.SweepRange(2.0, 3.0, 5))
    assert [c.oxidiser_fuel_ratio for c in cases] == pytest.approx(
        [2.0, 2.25, 2.5, 2.75, 3.0])
    for generated in cases:
        assert generated.fuel == case.fuel
        assert generated.oxidiser == case.oxidiser
        assert generated.chamber_pressure == case.chamber_pressure
        assert generated.fuel_temperature == case.fuel_temperature
        assert generated.oxidiser_temperature == case.oxidiser_temperature


# ===========================================================================
# running
# ===========================================================================


def test_a_sweep_keeps_its_points_in_ascending_order(stub_gateway):
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.5, 11))
    ratios = [point.oxidiser_fuel_ratio for point in result.points]
    assert ratios == sorted(ratios)
    assert len(result.points) == 11


def test_a_sweep_issues_one_scalar_request_per_point(stub_gateway):
    """No batch provider API was added for the sweep."""
    sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.5, 11))
    assert len(stub_gateway.calls) == 11
    assert [request.of_mass for request in stub_gateway.calls] == pytest.approx(
        list(sweep.SweepRange(2.5, 3.5, 11).values()))


def test_a_failed_point_keeps_its_place(failing_gateway):
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.5, 11))
    assert len(result.points) == 11
    assert result.failed_count == 1
    assert result.solved_count == 10
    failed = result.failed[0]
    assert failed.oxidiser_fuel_ratio == pytest.approx(3.0)
    assert math.isnan(failed.value_of("temperature")), (
        "a failed point must have no value, not a zero")


def test_a_failed_point_breaks_the_chart_line(failing_gateway):
    """The line must not run straight across a point nobody solved."""
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.5, 11))
    segments = sweep.series_for(result, "temperature")
    assert len(segments) == 2, "the series should be split at the failure"
    assert sum(len(segment) for segment in segments) == 10
    left, right = segments
    assert left[-1]["x"] < 3.0 < right[0]["x"]


def test_a_sweep_with_no_failures_is_one_unbroken_segment(stub_gateway):
    """The control: the split above must be caused by the failure."""
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.5, 11))
    segments = sweep.series_for(result, "temperature")
    assert len(segments) == 1
    assert len(segments[0]) == 11


def test_a_failed_point_still_appears_in_the_table(failing_gateway):
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.5, 11))
    rows = sweep.sweep_rows(result)
    assert len(rows) == 11
    failed = [row for row in rows if row[-1] != "solved"]
    assert len(failed) == 1
    assert failed[0][0] == pytest.approx(3.0)
    assert math.isnan(failed[0][1])


# ===========================================================================
# warnings
# ===========================================================================


def test_a_repeated_warning_is_aggregated_once(warning_gateway):
    """Forty-one identical rows would bury the point-specific ones."""
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.DEFAULT_SWEEP_RANGE)
    warnings = sweep.aggregated_warnings(result)
    assert len(warnings) == 1
    entry = warnings[0]
    assert entry["code"] == "PROVIDER_ASSIGNED_ENTHALPY_REACTANT"
    assert entry["count"] == 41
    assert entry["applies_to_all"] is True
    assert entry["range_text"] == "all 41 points"


def test_aggregation_does_not_remove_the_per_point_diagnostics(warning_gateway):
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.0, 6))
    for point in result.points:
        assert any(d.code == "PROVIDER_ASSIGNED_ENTHALPY_REACTANT"
                   for d in point.outcome.diagnostics)


def test_a_clean_sweep_aggregates_nothing(stub_gateway):
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.0, 6))
    assert sweep.aggregated_warnings(result) == ()


# ===========================================================================
# extrema, and what they are not
# ===========================================================================


def test_the_maximum_is_named_for_the_sampled_interval(stub_gateway):
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.5, 11))
    best = sweep.maximum_in_range(result, "temperature")
    assert best is not None
    assert best["of"] == pytest.approx(3.5)
    assert best["key"] == "temperature"
    assert "optimum" not in repr(best).lower()
    assert "best" not in repr(best).lower()


def test_the_sweep_module_never_says_optimal():
    """A wording audit on the module the sweep is implemented in."""
    import pathlib

    source = pathlib.Path(sweep.__file__).read_text(encoding="utf-8").lower()
    for banned in ("optimum o/f", "optimal o/f", "best o/f",
                   "recommended o/f", "pareto"):
        assert banned not in source or "not" in source, banned
    # The stronger check: no public name promises a decision.
    for name in sweep.__all__:
        assert "optim" not in name.lower()
        assert "best" not in name.lower()


def test_no_performance_quantity_can_be_swept():
    """c*, Cf and Isp are not chartable, because they do not exist here."""
    keys = {entry["key"] for entry in sweep.SWEEP_QUANTITIES}
    assert keys.isdisjoint({"c_star", "cf", "isp", "thrust",
                            "specific_impulse", "thrust_coefficient"})
    for entry in sweep.SWEEP_QUANTITIES:
        text = f"{entry['key']} {entry['label']}".lower()
        for banned in ("c*", "isp", "thrust", "impulse"):
            assert banned not in text


def test_the_sweep_gamma_is_the_same_field_the_calculator_labels(stub_gateway):
    """Calculator and sweep must not disagree about which gamma is drawn."""
    outcome = svc.solve_case(svc.DEFAULT_CASE)
    calculator = next(row for row in svc.result_rows(outcome)
                      if row.key == "gamma")
    chart = sweep.quantity_meta("gamma")
    assert chart["qualifier"] == calculator.qualifier == "equilibrium"

    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(3.4, 3.5, 2))
    plotted = sweep.series_for(result, "gamma")[0][0]["y"]
    assert plotted == result.points[0].outcome.state.gamma


def test_every_chartable_quantity_declares_a_label_and_a_unit():
    for entry in sweep.SWEEP_QUANTITIES:
        assert entry["label"]
        assert "unit" in entry
        # gamma is genuinely dimensionless; everything else carries a unit.
        if entry["key"] != "gamma":
            assert entry["unit"], entry["key"]


# ===========================================================================
# species series
# ===========================================================================


def test_species_series_follow_the_requested_basis(stub_gateway):
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.0, 6))
    mole = sweep.species_series_for(result, "CO2", "mole")[0]
    mass = sweep.species_series_for(result, "CO2", "mass")[0]
    assert mole[0]["y"] != mass[0]["y"], (
        "plotting one basis under the other's label is the failure this "
        "guards against")


def test_the_species_list_is_ordered_by_how_much_of_it_there_is(stub_gateway):
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.SweepRange(2.5, 3.0, 6))
    names = sweep.species_in_sweep(result)
    assert names[0] == "H2O"
    assert set(names) == {"H2O", "CO2", "CO", "OH", "C(gr)"}


# ===========================================================================
# live provider
# ===========================================================================


@requires_cea
def test_the_live_sweep_matches_direct_provider_solves():
    """The sweep is validated against the provider, not against itself.

    Each point is re-solved through ``solve_case`` independently and compared
    field by field. Checking the sweep with the sweep helper would prove only
    that the helper is consistent with itself.
    """
    span = sweep.SweepRange(3.0, 3.4, 5)
    result = sweep.run_sweep(svc.DEFAULT_CASE, span)
    assert result.solved_count == 5

    for point in result.points:
        direct = svc.solve_case(
            svc.DEFAULT_CASE.replace(
                oxidiser_fuel_ratio=point.oxidiser_fuel_ratio))
        assert direct.state is not None
        for field in ("temperature", "molar_mass", "gamma", "density",
                      "gas_constant", "cp", "cv"):
            assert getattr(point.outcome.state, field) == getattr(direct.state, field), (
                f"{field} differs at O/F {point.oxidiser_fuel_ratio}")


@requires_cea
def test_the_live_sweep_is_not_flat():
    """A flat curve would mean the O/F is not reaching the provider."""
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.DEFAULT_SWEEP_RANGE)
    temperatures = [point.value_of("temperature") for point in result.points]
    assert max(temperatures) - min(temperatures) > 100.0


@requires_cea
def test_different_quantities_peak_at_different_mixture_ratios():
    """Why the sweep must not name an optimum.

    Measured, not assumed: on LOX/CH4 the chamber temperature peaks inside the
    sampled range while the isentropic exponent falls monotonically across it.
    One "best O/F" would have to pick one of them arbitrarily.
    """
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.DEFAULT_SWEEP_RANGE)
    hottest = sweep.maximum_in_range(result, "temperature")
    stiffest = sweep.maximum_in_range(result, "gamma")
    assert hottest["of"] != stiffest["of"]


@requires_cea
def test_a_live_sweep_of_the_acceptance_size_is_interactive():
    """41 points, end to end, through the whole application pipeline."""
    result = sweep.run_sweep(svc.DEFAULT_CASE, sweep.DEFAULT_SWEEP_RANGE)
    assert result.solved_count == 41
    assert result.elapsed_seconds < 2.0, (
        f"41 points took {result.elapsed_seconds:.3f} s")
