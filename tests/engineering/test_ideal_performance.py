"""Ideal rocket performance: the equations, and the independent check of each.

The oracle in this module is :func:`independent_performance` -- the whole chain
rewritten from the textbook relations with nothing but ``math``, including its
own bisection for the area-Mach inverse. It shares no code with the
implementation, so agreeing with it is evidence rather than tautology.

Everything else is an identity, an invariance or a sign. Those catch the errors
an oracle cannot: an ambient pressure leaking into c*, a pressure term clamped
positive, a scale factor applied to the wrong group of quantities.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.core.constants import STANDARD_GRAVITY
from rocketforge.core.result import Status
from rocketforge.engineering.chamber import (
    ChamberGammaBasis,
    reduce_chamber_gas,
)
from rocketforge.engineering.nozzle import (
    IDEAL_MODEL_ASSUMPTIONS,
    IDENTITY_TOLERANCE,
    IdealPerformanceRequest,
    PerformanceScale,
    PerformanceScaleMode,
    characteristic_velocity,
    check_identities,
    solve_ideal_performance,
)
from rocketforge.physics.compressible import PerfectGas, isentropic
from rocketforge.physics.thermochemistry import GammaStrategy


# ===========================================================================
# the independent oracle
# ===========================================================================


def independent_mach_from_area_ratio(area_ratio: float, gamma: float) -> float:
    """Supersonic Mach from Ae/At, by bisection on the area-Mach relation.

    Written out longhand and solved with a bisection of its own, so that
    nothing about the frozen module's Brent solver, its bracketing or its
    tolerances is shared with the value being checked.
    """
    exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0))

    def area(mach: float) -> float:
        phi = 1.0 + 0.5 * (gamma - 1.0) * mach * mach
        return (1.0 / mach) * ((2.0 / (gamma + 1.0)) * phi) ** exponent

    low, high = 1.0 + 1e-12, 2.0
    while area(high) < area_ratio:
        high *= 2.0
        if high > 1.0e6:
            raise RuntimeError("no supersonic solution found")
    for _ in range(400):
        middle = 0.5 * (low + high)
        if area(middle) < area_ratio:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def independent_performance(*, gamma: float, gas_constant: float,
                            stagnation_temperature: float,
                            chamber_pressure: float, area_ratio: float,
                            ambient_pressure: float,
                            throat_area: float | None = None) -> dict:
    """The whole chain, from the textbook, with ``math`` and nothing else."""
    g, r, t0 = gamma, gas_constant, stagnation_temperature
    vandenkerckhove = math.sqrt(g) * (2.0 / (g + 1.0)) ** (
        (g + 1.0) / (2.0 * (g - 1.0)))
    c_star = math.sqrt(r * t0) / vandenkerckhove

    mach_exit = independent_mach_from_area_ratio(area_ratio, g)
    phi = 1.0 + 0.5 * (g - 1.0) * mach_exit * mach_exit
    exit_pressure = chamber_pressure * phi ** (-g / (g - 1.0))
    exit_temperature = t0 / phi
    exit_velocity = mach_exit * math.sqrt(g * r * exit_temperature)

    cf_momentum = exit_velocity / c_star
    cf_pressure = ((exit_pressure - ambient_pressure) / chamber_pressure) * area_ratio
    cf_total = cf_momentum + cf_pressure
    c_eff = cf_total * c_star

    result = {
        "c_star": c_star,
        "mach_exit": mach_exit,
        "exit_pressure": exit_pressure,
        "exit_temperature": exit_temperature,
        "exit_velocity": exit_velocity,
        "cf_momentum": cf_momentum,
        "cf_pressure": cf_pressure,
        "cf_total": cf_total,
        "c_eff": c_eff,
        "isp": c_eff / STANDARD_GRAVITY,
    }
    if throat_area is not None:
        exit_area = area_ratio * throat_area
        mdot = vandenkerckhove * throat_area * chamber_pressure / math.sqrt(r * t0)
        momentum = mdot * exit_velocity
        pressure = (exit_pressure - ambient_pressure) * exit_area
        result.update(mass_flow=mdot, exit_area=exit_area,
                      momentum_thrust=momentum, pressure_thrust=pressure,
                      total_thrust=momentum + pressure)
    return result


def solve(reduced, *, area_ratio=40.0, ambient=0.0, chamber_pressure=10.0e6,
          scale=None):
    """Shorthand: one performance solve, unwrapped, asserting it succeeded."""
    request = IdealPerformanceRequest(
        reduced=reduced, chamber_pressure=chamber_pressure,
        area_ratio=area_ratio, ambient_pressure=ambient,
        scale=scale or PerformanceScale())
    solution = solve_ideal_performance(request)
    assert solution.value is not None, [d.code for d in solution.diagnostics]
    return solution.value


# ===========================================================================
# characteristic velocity
# ===========================================================================


@pytest.mark.parametrize("gamma, gas_constant, temperature", [
    (1.1325915, 381.9214, 3598.2854),      # the LOX/CH4 shape
    (1.2000000, 350.0000, 3500.0000),
    (1.1400000, 420.0000, 3300.0000),      # hydrogen-rich: high R
    (1.2600000, 280.0000, 3000.0000),
    (1.4000000, 287.0500, 1000.0000),      # air, for a non-rocket check
])
def test_cstar_matches_the_independent_analytic_form(gamma, gas_constant,
                                                     temperature):
    """The production path reuses frozen choked-flow physics; this does not.

    ``c* = sqrt(R T0 / gamma) * ((gamma+1)/2)^((gamma+1)/(2(gamma-1)))``
    """
    gas = PerfectGas(gamma=gamma, gas_constant=gas_constant)
    computed = characteristic_velocity(gas, temperature)
    analytic = (math.sqrt(gas_constant * temperature / gamma)
                * ((gamma + 1.0) / 2.0) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0))))
    assert computed == pytest.approx(analytic, rel=1.0e-14)


def test_cstar_closes_the_definition_it_is_named_for(reduced_gas):
    """c* = pc At / mdot, recomputed from a scaled engine."""
    result = solve(reduced_gas,
                   scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    definition = (result.chamber_pressure * result.throat_area) / result.mass_flow
    assert result.characteristic_velocity == pytest.approx(definition, rel=1e-14)


def test_cstar_is_not_the_exhaust_velocity(reduced_gas):
    """They differ by nearly a factor of two, and the docstring says so."""
    result = solve(reduced_gas)
    assert result.characteristic_velocity < 0.6 * result.exit.velocity
    assert "not the exhaust velocity" in characteristic_velocity.__doc__.lower()


def test_cstar_needs_a_gas_constant():
    gas = PerfectGas(gamma=1.2)
    with pytest.raises(ValueError, match="gas constant"):
        characteristic_velocity(gas, 3000.0)


@pytest.mark.parametrize("temperature", [0.0, -1.0, float("nan"), float("inf")])
def test_cstar_refuses_an_impossible_temperature(temperature):
    gas = PerfectGas(gamma=1.2, gas_constant=350.0)
    with pytest.raises(ValueError):
        characteristic_velocity(gas, temperature)


# ===========================================================================
# c* invariance -- the chamber/nozzle distinction, protected
# ===========================================================================


@pytest.mark.parametrize("area_ratio", [5.0, 10.0, 20.0, 40.0, 80.0])
def test_cstar_does_not_move_with_area_ratio(reduced_gas, area_ratio):
    """c* is set at the throat. A c* that moved with the nozzle would mean the
    chamber and the nozzle had been confused for each other."""
    baseline = solve(reduced_gas, area_ratio=40.0).characteristic_velocity
    assert solve(reduced_gas,
                 area_ratio=area_ratio).characteristic_velocity == baseline


@pytest.mark.parametrize("ambient", [0.0, 1.0e3, 20.0e3, 101325.0])
def test_cstar_does_not_move_with_ambient_pressure(reduced_gas, ambient):
    baseline = solve(reduced_gas, ambient=0.0).characteristic_velocity
    assert solve(reduced_gas,
                 ambient=ambient).characteristic_velocity == baseline


@pytest.mark.parametrize("throat_area", [0.001, 0.01, 0.5])
def test_cstar_does_not_move_with_engine_size(reduced_gas, throat_area):
    baseline = solve(reduced_gas).characteristic_velocity
    scaled = solve(reduced_gas,
                   scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA,
                                          throat_area))
    assert scaled.characteristic_velocity == baseline


# ===========================================================================
# the independent oracle, end to end
# ===========================================================================


@pytest.mark.parametrize("area_ratio", [5.0, 10.0, 25.0, 40.0, 80.0])
@pytest.mark.parametrize("ambient", [0.0, 101325.0])
def test_every_output_matches_the_independent_reimplementation(
        reduced_gas, area_ratio, ambient):
    throat_area = 0.02
    result = solve(reduced_gas, area_ratio=area_ratio, ambient=ambient,
                   scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA,
                                          throat_area))
    expected = independent_performance(
        gamma=reduced_gas.gamma, gas_constant=reduced_gas.gas_constant,
        stagnation_temperature=reduced_gas.stagnation_temperature,
        chamber_pressure=10.0e6, area_ratio=area_ratio,
        ambient_pressure=ambient, throat_area=throat_area)

    # The bisection above converges to about 1e-12 in Mach, which propagates
    # into everything downstream; that sets the tolerance, not a wish.
    assert result.characteristic_velocity == pytest.approx(expected["c_star"], rel=1e-13)
    assert result.exit.mach == pytest.approx(expected["mach_exit"], rel=1e-9)
    assert result.exit.pressure == pytest.approx(expected["exit_pressure"], rel=1e-9)
    assert result.exit.temperature == pytest.approx(expected["exit_temperature"], rel=1e-9)
    assert result.exit.velocity == pytest.approx(expected["exit_velocity"], rel=1e-9)
    assert result.thrust_coefficient_momentum == pytest.approx(
        expected["cf_momentum"], rel=1e-9)
    assert result.thrust_coefficient_pressure == pytest.approx(
        expected["cf_pressure"], rel=1e-9, abs=1e-12)
    assert result.thrust_coefficient == pytest.approx(expected["cf_total"], rel=1e-9)
    assert result.effective_exhaust_velocity == pytest.approx(expected["c_eff"], rel=1e-9)
    assert result.specific_impulse == pytest.approx(expected["isp"], rel=1e-9)
    assert result.mass_flow == pytest.approx(expected["mass_flow"], rel=1e-13)
    assert result.exit_area == pytest.approx(expected["exit_area"], rel=1e-15)
    assert result.thrust.momentum == pytest.approx(expected["momentum_thrust"], rel=1e-9)
    assert result.thrust.pressure == pytest.approx(expected["pressure_thrust"], rel=1e-9)
    assert result.thrust.total == pytest.approx(expected["total_thrust"], rel=1e-9)


def test_the_oracle_disagrees_when_it_should(reduced_gas):
    """The negative control: the oracle is sensitive to what it is given."""
    base = independent_performance(
        gamma=1.2, gas_constant=350.0, stagnation_temperature=3500.0,
        chamber_pressure=10.0e6, area_ratio=40.0, ambient_pressure=0.0)
    hotter = independent_performance(
        gamma=1.2, gas_constant=350.0, stagnation_temperature=3600.0,
        chamber_pressure=10.0e6, area_ratio=40.0, ambient_pressure=0.0)
    assert hotter["c_star"] > base["c_star"]
    assert hotter["isp"] > base["isp"]


def test_the_exit_mach_satisfies_the_area_mach_relation_forwards(reduced_gas):
    """Inverse checked against forward, in the frozen module's own terms."""
    result = solve(reduced_gas, area_ratio=25.0)
    forward = float(isentropic.area_ratio(result.exit.mach, reduced_gas.gas))
    assert forward == pytest.approx(25.0, rel=1e-10)


# ===========================================================================
# the identity matrix
# ===========================================================================


@pytest.mark.parametrize("scale", [
    PerformanceScale(),
    PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01),
    PerformanceScale(PerformanceScaleMode.MASS_FLOW, 50.0),
])
@pytest.mark.parametrize("ambient", [0.0, 30.0e3, 101325.0])
def test_every_identity_closes(reduced_gas, scale, ambient):
    result = solve(reduced_gas, ambient=ambient, scale=scale)
    report = check_identities(result)
    assert report.passed, [c.detail for c in report.failures]
    assert report.worst.residual <= IDENTITY_TOLERANCE


def test_the_scaled_identities_only_run_when_a_scale_exists(reduced_gas):
    """A check that quietly skips is worse than one that says it did not apply."""
    normalized = check_identities(solve(reduced_gas))
    scaled = check_identities(
        solve(reduced_gas,
              scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01)))
    assert not any(check.scaled for check in normalized.checks)
    assert len(scaled.checks) > len(normalized.checks)
    assert {"c* = pc At / mdot", "F = Cf pc At", "Isp = F / (mdot g0)"} <= {
        check.name for check in scaled.checks}


# ===========================================================================
# mutation proofs
# ===========================================================================


@pytest.mark.parametrize("field, factor", [
    ("characteristic_velocity", 1.01),
    ("thrust_coefficient_momentum", 1.01),
    ("thrust_coefficient_pressure", 1.5),
    ("thrust_coefficient", 1.01),
    ("effective_exhaust_velocity", 1.01),
    ("specific_impulse", 1.01),
    ("mass_flow", 1.01),
    ("throat_area", 1.01),
    ("exit_area", 1.01),
])
def test_a_mutated_result_fails_the_identity_matrix(reduced_gas, field, factor):
    """Every validator gets a mutation proof, with the change asserted first."""
    from dataclasses import replace

    good = solve(reduced_gas, ambient=50.0e3,
                 scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    assert check_identities(good).passed

    original = getattr(good, field)
    mutated = replace(good, **{field: original * factor})
    assert getattr(mutated, field) != original, "the fixture did not change"
    assert not check_identities(mutated).passed, (
        f"mutating {field} by x{factor} did not break any identity")


@pytest.mark.parametrize("field, factor", [
    ("momentum", 1.01),
    ("pressure", 1.5),
    ("total", 1.01),
])
def test_a_mutated_thrust_breakdown_fails_the_identity_matrix(reduced_gas,
                                                              field, factor):
    from dataclasses import replace

    good = solve(reduced_gas, ambient=50.0e3,
                 scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    original = getattr(good.thrust, field)
    mutated = replace(good, thrust=replace(good.thrust,
                                           **{field: original * factor}))
    assert getattr(mutated.thrust, field) != original, "the fixture did not change"
    assert not check_identities(mutated).passed


@pytest.mark.parametrize("field, factor", [
    ("velocity", 1.01),
    ("pressure", 1.20),
    ("area_ratio", 1.01),
])
def test_a_mutated_exit_state_fails_the_identity_matrix(reduced_gas, field, factor):
    from dataclasses import replace

    good = solve(reduced_gas, ambient=50.0e3,
                 scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    original = getattr(good.exit, field)
    mutated = replace(good, exit=replace(good.exit, **{field: original * factor}))
    assert getattr(mutated.exit, field) != original, "the fixture did not change"
    assert not check_identities(mutated).passed


def test_a_mutated_ambient_pressure_fails_the_identity_matrix(reduced_gas):
    from dataclasses import replace

    good = solve(reduced_gas, ambient=50.0e3,
                 scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    mutated = replace(good, ambient_pressure=good.ambient_pressure * 1.2)
    assert mutated.ambient_pressure != good.ambient_pressure
    assert not check_identities(mutated).passed


def test_the_identity_matrix_is_not_vacuous(reduced_gas):
    """It has to actually be looking at something."""
    result = solve(reduced_gas,
                   scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    report = check_identities(result)
    assert len(report.checks) == 15
    assert all(math.isfinite(check.expected) for check in report.checks)


# ===========================================================================
# ambient pressure and the pressure term
# ===========================================================================


def test_raising_ambient_reduces_thrust_and_leaves_cstar_alone(reduced_gas):
    """The chamber/nozzle split, as a monotonic sweep.

    Fixed at an area ratio and chamber pressure where every ambient value
    stays in the shock-free supersonic regime, so the comparison is between
    like internal solutions rather than across a regime change.
    """
    previous = None
    baseline_cstar = None
    for ambient in (0.0, 10.0e3, 30.0e3, 60.0e3, 101325.0):
        result = solve(reduced_gas, area_ratio=25.0, ambient=ambient,
                       scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA,
                                              0.01))
        if previous is not None:
            assert result.thrust_coefficient_pressure < previous.thrust_coefficient_pressure
            assert result.thrust_coefficient < previous.thrust_coefficient
            assert result.effective_exhaust_velocity < previous.effective_exhaust_velocity
            assert result.specific_impulse < previous.specific_impulse
            assert result.thrust.total < previous.thrust.total
            assert result.characteristic_velocity == baseline_cstar
            # And the momentum half is untouched by ambient.
            assert result.thrust.momentum == previous.thrust.momentum
        else:
            baseline_cstar = result.characteristic_velocity
        previous = result


def test_vacuum_is_ambient_zero_and_needs_no_special_equation(reduced_gas):
    result = solve(reduced_gas, ambient=0.0,
                   scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    assert result.ambient_pressure == 0.0
    assert result.thrust.pressure == pytest.approx(
        result.exit.pressure * result.exit_area, rel=1e-14)


def test_the_pressure_term_is_positive_when_the_nozzle_underexpands(reduced_gas):
    result = solve(reduced_gas, area_ratio=25.0, ambient=1.0e3)
    assert result.exit.pressure > result.ambient_pressure
    assert result.thrust_coefficient_pressure > 0.0


def test_the_pressure_term_is_negative_when_the_nozzle_overexpands(reduced_gas):
    """Negative is correct, and is never clamped away."""
    result = solve(reduced_gas, area_ratio=25.0, ambient=60.0e3,
                   scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    assert result.exit.pressure < result.ambient_pressure
    assert result.thrust_coefficient_pressure < 0.0
    assert result.thrust.pressure < 0.0
    assert result.thrust.total < result.thrust.momentum
    assert "OVEREXPANDED_PRESSURE_THRUST" in [d.code for d in result.diagnostics]


def test_the_pressure_term_vanishes_at_ideal_expansion(reduced_gas):
    """pe = pa exactly: the optimum-expansion identity.

    The ambient pressure is set to the exit pressure the nozzle actually
    produces, so this is an identity rather than a search -- nothing here looks
    for an optimum area ratio.
    """
    probe = solve(reduced_gas, area_ratio=25.0, ambient=0.0)
    matched = solve(reduced_gas, area_ratio=25.0, ambient=probe.exit.pressure,
                    scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    assert matched.exit.pressure == pytest.approx(matched.ambient_pressure, rel=1e-15)
    assert matched.thrust_coefficient_pressure == pytest.approx(0.0, abs=1e-15)
    assert matched.thrust.pressure == pytest.approx(0.0, abs=1e-6)
    assert matched.effective_exhaust_velocity == pytest.approx(
        matched.exit.velocity, rel=1e-12)


def test_c_eff_differs_from_the_exit_velocity_away_from_ideal_expansion(reduced_gas):
    """They are not synonyms, and the difference is exactly the pressure term."""
    result = solve(reduced_gas, area_ratio=25.0, ambient=0.0,
                   scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    assert result.effective_exhaust_velocity != result.exit.velocity
    difference = result.effective_exhaust_velocity - result.exit.velocity
    assert difference == pytest.approx(
        result.thrust.pressure / result.mass_flow, rel=1e-12)


# ===========================================================================
# scale
# ===========================================================================


def test_normalized_results_carry_no_absolute_quantity(reduced_gas):
    """None, never zero: zero thrust is a claim about an engine."""
    result = solve(reduced_gas)
    assert result.is_scaled is False
    assert result.thrust is None
    assert result.mass_flow is None
    assert result.throat_area is None
    assert result.exit_area is None
    # while everything that does not need a size is present
    for value in (result.characteristic_velocity, result.thrust_coefficient,
                  result.effective_exhaust_velocity, result.specific_impulse,
                  result.exit.mach, result.exit.pressure):
        assert math.isfinite(value)


def test_doubling_the_throat_area_doubles_the_engine_and_nothing_else(reduced_gas):
    small = solve(reduced_gas, ambient=50.0e3,
                  scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    large = solve(reduced_gas, ambient=50.0e3,
                  scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.02))

    for field in ("characteristic_velocity", "thrust_coefficient",
                  "thrust_coefficient_momentum", "thrust_coefficient_pressure",
                  "effective_exhaust_velocity", "specific_impulse"):
        assert getattr(large, field) == getattr(small, field), field
    assert large.exit.mach == small.exit.mach
    assert large.exit.pressure == small.exit.pressure

    for field in ("mass_flow", "throat_area", "exit_area"):
        assert getattr(large, field) == pytest.approx(
            2.0 * getattr(small, field), rel=1e-14), field
    for field in ("momentum", "pressure", "total"):
        assert getattr(large.thrust, field) == pytest.approx(
            2.0 * getattr(small.thrust, field), rel=1e-13), field


def test_the_mass_flow_scale_recovers_the_same_engine(reduced_gas):
    """Two ways of stating one size must produce one answer."""
    by_area = solve(reduced_gas, ambient=50.0e3,
                    scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    by_flow = solve(reduced_gas, ambient=50.0e3,
                    scale=PerformanceScale(PerformanceScaleMode.MASS_FLOW,
                                           by_area.mass_flow))
    assert by_flow.throat_area == pytest.approx(by_area.throat_area, rel=1e-13)
    assert by_flow.thrust.total == pytest.approx(by_area.thrust.total, rel=1e-13)
    assert by_flow.specific_impulse == pytest.approx(by_area.specific_impulse,
                                                     rel=1e-14)


def test_a_scale_mode_and_value_that_disagree_are_refused():
    with pytest.raises(ValueError, match="carries no engine size"):
        PerformanceScale(PerformanceScaleMode.NORMALIZED, 0.01)
    with pytest.raises(ValueError, match="needs a value"):
        PerformanceScale(PerformanceScaleMode.THROAT_AREA)


@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf")])
def test_an_impossible_scale_value_is_refused(value):
    with pytest.raises(ValueError):
        PerformanceScale(PerformanceScaleMode.THROAT_AREA, value)


# ===========================================================================
# the request's own domain
# ===========================================================================


@pytest.mark.parametrize("field, value", [
    ("chamber_pressure", 0.0),
    ("chamber_pressure", -1.0e6),
    ("chamber_pressure", float("nan")),
    ("area_ratio", 1.0),
    ("area_ratio", 0.5),
    ("area_ratio", float("inf")),
    ("ambient_pressure", -1.0),
    ("ambient_pressure", float("nan")),
])
def test_an_invalid_request_is_refused_not_clamped(reduced_gas, field, value):
    kwargs = {"reduced": reduced_gas, "chamber_pressure": 10.0e6,
              "area_ratio": 40.0, "ambient_pressure": 0.0}
    kwargs[field] = value
    with pytest.raises((ValueError, TypeError)):
        IdealPerformanceRequest(**kwargs)


def test_ambient_pressure_of_exactly_zero_is_accepted(reduced_gas):
    """Zero is vacuum, not a missing value."""
    request = IdealPerformanceRequest(
        reduced=reduced_gas, chamber_pressure=10.0e6, area_ratio=40.0,
        ambient_pressure=0.0)
    assert request.ambient_pressure == 0.0


def test_a_raw_chamber_state_is_not_a_reduced_gas(chamber_state):
    """The reduction is a decision, not a conversion the solver can do itself."""
    with pytest.raises(TypeError, match="explicit gas reduction"):
        IdealPerformanceRequest(
            reduced=chamber_state, chamber_pressure=10.0e6,   # type: ignore[arg-type]
            area_ratio=40.0, ambient_pressure=0.0)


# ===========================================================================
# nozzle regimes
# ===========================================================================


def test_the_three_supported_regimes_are_reached_and_reported(reduced_gas):
    """Each is a different relationship between pe and pa, one internal solution."""
    probe = solve(reduced_gas, area_ratio=25.0, ambient=0.0)
    exit_pressure = probe.exit.pressure

    assert solve(reduced_gas, area_ratio=25.0,
                 ambient=exit_pressure * 0.5).exit.regime == "underexpanded"
    assert solve(reduced_gas, area_ratio=25.0,
                 ambient=exit_pressure).exit.regime == "ideally_expanded"
    assert solve(reduced_gas, area_ratio=25.0,
                 ambient=exit_pressure * 2.0).exit.regime == "overexpanded"


def test_a_shock_inside_the_nozzle_is_refused_by_name(reduced_gas):
    """Never mislabelled as an ideal fully supersonic expansion."""
    request = IdealPerformanceRequest(
        reduced=reduced_gas, chamber_pressure=1.0e6, area_ratio=100.0,
        ambient_pressure=101325.0)
    solution = solve_ideal_performance(request)
    assert solution.value is None
    assert solution.status is Status.NO_SOLUTION
    codes = [d.code for d in solution.diagnostics]
    assert "NOZZLE_REGIME_UNSUPPORTED" in codes
    message = next(d.message for d in solution.diagnostics
                   if d.code == "NOZZLE_REGIME_UNSUPPORTED")
    assert "internal_normal_shock" in message


def test_an_ambient_above_the_chamber_pressure_is_refused(reduced_gas):
    request = IdealPerformanceRequest(
        reduced=reduced_gas, chamber_pressure=1.0e5, area_ratio=10.0,
        ambient_pressure=2.0e5)
    solution = solve_ideal_performance(request)
    assert solution.value is None
    assert "NOZZLE_REGIME_UNSUPPORTED" in [d.code for d in solution.diagnostics]


def test_the_frozen_separation_warning_reaches_the_result(reduced_gas):
    """The frozen classifier's own caveat is carried, not suppressed."""
    request = IdealPerformanceRequest(
        reduced=reduced_gas, chamber_pressure=10.0e6, area_ratio=40.0,
        ambient_pressure=101325.0)
    solution = solve_ideal_performance(request)
    assert solution.value is not None
    assert solution.status is Status.OK_WITH_WARNINGS
    assert "MODEL_LIMIT_SEPARATION" in [d.code for d in solution.diagnostics]


# ===========================================================================
# the ideal boundary, and determinism
# ===========================================================================


def test_the_result_states_what_the_ideal_model_claims(reduced_gas):
    result = solve(reduced_gas)
    joined = " ".join(result.assumptions).lower()
    assert result.assumptions == IDEAL_MODEL_ASSUMPTIONS
    for absent in ("efficiency", "divergence", "viscous", "boundary-layer",
                   "separation", "finite-rate"):
        assert absent in joined, f"the assumptions never mention {absent}"


def test_no_efficiency_factor_exists_anywhere_in_the_package():
    """Phase 5E is the ideal baseline; losses need their own ownership."""
    import pathlib

    from rocketforge.engineering import nozzle

    package = pathlib.Path(nozzle.__file__).parent
    for path in package.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for banned in ("eta_", "efficiency_factor", "divergence_loss",
                       "viscous_loss", "nozzle_efficiency"):
            assert banned not in source, f"{path.name} defines {banned}"


def test_the_solve_is_deterministic(reduced_gas):
    scale = PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.0123)
    first = solve(reduced_gas, ambient=42.0e3, scale=scale)
    second = solve(reduced_gas, ambient=42.0e3, scale=scale)
    for field in ("characteristic_velocity", "thrust_coefficient",
                  "effective_exhaust_velocity", "specific_impulse",
                  "mass_flow", "throat_area", "exit_area"):
        assert getattr(first, field) == getattr(second, field)
    assert first.thrust.total == second.thrust.total


def test_the_solver_does_not_mutate_its_request(reduced_gas):
    request = IdealPerformanceRequest(
        reduced=reduced_gas, chamber_pressure=10.0e6, area_ratio=40.0,
        ambient_pressure=50.0e3,
        scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    before = (request.chamber_pressure, request.area_ratio,
              request.ambient_pressure, request.scale.value,
              request.reduced.gamma)
    solve_ideal_performance(request)
    after = (request.chamber_pressure, request.area_ratio,
             request.ambient_pressure, request.scale.value,
             request.reduced.gamma)
    assert before == after


# ===========================================================================
# CEA-free operation -- BLOCKING
# ===========================================================================


def test_the_performance_core_imports_no_provider_and_no_qt():
    """Blocking: these equations are RocketForge's, not a provider's."""
    import ast
    import pathlib

    from rocketforge.engineering import nozzle

    package = pathlib.Path(nozzle.__file__).parent
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        for name in names:
            head = name.split(".")[0]
            assert head not in ("cea", "cantera", "PySide6", "CoolProp"), (
                f"{path.name} imports {name}")
            assert "providers" not in name, f"{path.name} imports {name}"
            assert "application" not in name, f"{path.name} imports {name}"


def _chemistry_modules(modules) -> set[str]:
    """The chemistry-library entries in a ``sys.modules`` snapshot."""
    return {name for name in modules
            if name.split(".")[0] in ("cea", "cantera", "CoolProp")}


def test_a_full_performance_solve_imports_no_chemistry_library(reduced_gas):
    """Blocking: the whole chain, from a provider-independent fixture.

    Measured as a **delta** rather than as an absolute reading of
    ``sys.modules``. The absolute form asserts "nothing anywhere in this pytest
    session has imported a chemistry library", which is a property of the
    collection order and not of this code -- an application test that
    legitimately exercises the provider makes it false without anything here
    changing. The delta says what is meant: solving imported nothing new.

    The absolute statement is made in a clean interpreter by the test below.
    """
    import sys

    before = _chemistry_modules(sys.modules)

    result = solve(reduced_gas, ambient=0.0,
                   scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    assert result.characteristic_velocity > 0.0
    assert result.thrust_coefficient > 0.0
    assert result.specific_impulse > 0.0
    assert result.thrust.total > 0.0
    assert check_identities(result).passed

    after = _chemistry_modules(sys.modules)
    assert after == before, f"solving imported {sorted(after - before)}"


#: The chain, run in a clean interpreter. Kept as source rather than as a
#: helper module so that what the subprocess imports is visible here in full.
_CLEAN_PROCESS_PROGRAM = """
import sys

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.engineering.chamber import ChamberGammaBasis, reduce_chamber_gas
from rocketforge.engineering.nozzle import (
    IdealPerformanceRequest, PerformanceScale, PerformanceScaleMode,
    check_identities, solve_ideal_performance,
)
from rocketforge.physics.thermochemistry import (
    ChamberGas, ChemistryMode, Composition, CompositionBasis,
    EquilibriumConstraint, GammaStrategy, ThermochemistryProvenance,
)

molar_mass = 0.0217700886
state = ChamberGas(
    temperature=3598.2854, gamma=1.1325915, gamma_equilibrium=1.1325915,
    gamma_frozen=1.1955675,
    gas_constant=UNIVERSAL_GAS_CONSTANT / molar_mass, molar_mass=molar_mass,
    composition=Composition.from_fractions(
        {"H2O": 0.5, "CO": 0.2, "CO2": 0.2, "H2": 0.1},
        CompositionBasis.MOLE_FRACTION),
    pressure=10.0e6, condensed_mass_fraction=0.0,
    provenance=ThermochemistryProvenance(
        provider_id="subprocess:phase5e",
        chemistry_mode=ChemistryMode.EQUILIBRIUM,
        equilibrium_constraint=EquilibriumConstraint.HP))

reduced = reduce_chamber_gas(state, GammaStrategy.CHAMBER,
                             ChamberGammaBasis.FROZEN).value
assert reduced is not None
result = solve_ideal_performance(IdealPerformanceRequest(
    reduced=reduced, chamber_pressure=10.0e6, area_ratio=40.0,
    ambient_pressure=0.0,
    scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))).value
assert result is not None
assert result.characteristic_velocity > 0.0
assert result.thrust.total > 0.0
assert check_identities(result).passed

loaded = sorted(name for name in sys.modules
                if name.split(".")[0] in ("cea", "cantera", "CoolProp"))
assert loaded == [], "a chemistry library was loaded: " + repr(loaded)
print("OK", round(result.specific_impulse, 3))
"""


def test_the_whole_chain_runs_in_an_interpreter_that_never_loads_chemistry():
    """The absolute form of the claim, in a process nothing else has touched.

    This is the promise the phase actually makes: a build with no chemistry
    library installed can still compute ideal rocket performance. Run in a
    subprocess because that is the only place ``sys.modules`` means what the
    assertion wants it to mean.
    """
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [sys.executable, "-c", _CLEAN_PROCESS_PROGRAM],
        cwd=str(root), capture_output=True, text=True, timeout=120)
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.startswith("OK"), completed.stdout


# ===========================================================================
# several chamber states, so nothing is tailored to one propellant
# ===========================================================================


@pytest.mark.parametrize("gamma, molar_mass, temperature, chamber_pressure", [
    (1.1325915, 0.0217700886, 3598.3, 10.0e6),    # LOX/CH4 shape
    (1.1400000, 0.0134581000, 3483.4, 6.895e6),   # LOX/LH2 shape: light products
    (1.2200000, 0.0250000000, 3000.0, 5.0e6),
    (1.2600000, 0.0300000000, 2500.0, 2.0e6),
])
def test_the_model_is_not_tuned_to_one_propellant(
        make_chamber_state, gamma, molar_mass, temperature, chamber_pressure):
    # gamma_frozen is set to the parametrised value so the frozen basis and the
    # independent oracle are speaking about the same gas.
    state = make_chamber_state(gamma=gamma, gamma_frozen=gamma,
                               molar_mass=molar_mass, temperature=temperature,
                               pressure=chamber_pressure)
    reduced = reduce_chamber_gas(state, GammaStrategy.CHAMBER,
                                 ChamberGammaBasis.FROZEN).value
    assert reduced is not None

    result = solve(reduced, area_ratio=40.0, ambient=0.0,
                   chamber_pressure=chamber_pressure,
                   scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))
    assert check_identities(result).passed

    expected = independent_performance(
        gamma=gamma, gas_constant=reduced.gas_constant,
        stagnation_temperature=temperature, chamber_pressure=chamber_pressure,
        area_ratio=40.0, ambient_pressure=0.0, throat_area=0.01)
    assert result.characteristic_velocity == pytest.approx(
        expected["c_star"], rel=1e-13)
    assert result.specific_impulse == pytest.approx(expected["isp"], rel=1e-9)
    # A sanity band, not a validation: these are all plausible chemical rockets.
    assert 150.0 < result.specific_impulse < 500.0
