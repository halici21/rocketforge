"""The line model: relations, laminar, turbulent, transition, refusals.

No provider anywhere in this file except where a real fluid state is needed,
and even then the line model only ever sees a ``FluidState``. Expected values
are hand-computed or produced by an independent oracle implemented here; the
production code is never used to generate its own expectation.
"""

from __future__ import annotations

import math
from decimal import Decimal, getcontext

import pytest

from rocketforge.core.errors import DomainError, InputError
from rocketforge.core.result import Status
from rocketforge.engineering.line import (
    COLEBROOK_REYNOLDS_MAX,
    MAX_RELATIVE_ROUGHNESS,
    REYNOLDS_LAMINAR_LIMIT,
    REYNOLDS_TURBULENT_ONSET,
    CircularLineRequest,
    FlowRegime,
    circular_area,
    colebrook_darcy_friction_factor,
    colebrook_residual,
    darcy_weisbach_pressure_drop,
    hagen_poiseuille_pressure_drop,
    laminar_darcy_friction_factor,
    mean_velocity,
    relative_roughness,
    reynolds_number,
    reynolds_number_from_mass_flow,
    solve_line,
    volumetric_flow,
)
from rocketforge.physics.fluids import (
    METHANE,
    FluidPhase,
    FluidProperty,
    FluidPropertyProvenance,
    FluidState,
    PropertyStatus,
)

PROVENANCE = FluidPropertyProvenance(provider_id="t", provider_label="Test",
                                     backend="test-model")


def fluid_state(density=422.6, viscosity=1.1725e-4, pressure=3.0e5,
                temperature=111.643, phase=FluidPhase.LIQUID, omit=()):
    values = {FluidProperty.DENSITY: density,
              FluidProperty.DYNAMIC_VISCOSITY: viscosity}
    for prop in omit:
        values.pop(prop, None)
    statuses = {p: (PropertyStatus.AVAILABLE if p in values
                    else PropertyStatus.NOT_SUPPORTED) for p in FluidProperty}
    return FluidState(fluid=METHANE, temperature=temperature,
                      pressure=pressure, phase=phase, provenance=PROVENANCE,
                      values=values, statuses=statuses)


def request_for(mass_flow=2.0, length=5.0, diameter=0.02, roughness=1.5e-6,
                **kwargs):
    return CircularLineRequest(fluid_state=fluid_state(**kwargs),
                               mass_flow=mass_flow, length=length,
                               inner_diameter=diameter,
                               absolute_roughness=roughness)


# ===========================================================================
# pure relations
# ===========================================================================

def test_circular_area_is_pi_d_squared_over_four():
    assert circular_area(0.02) == pytest.approx(math.pi * 0.0004 / 4.0, rel=0)


def test_area_of_a_two_metre_pipe_is_hand_computable():
    # D = 2 m -> A = pi. Written down, not produced by the code.
    assert circular_area(2.0) == pytest.approx(math.pi)


def test_volumetric_flow_is_mass_flow_over_density():
    assert volumetric_flow(422.6, 422.6) == pytest.approx(1.0)


def test_velocity_is_volumetric_flow_over_area():
    q = volumetric_flow(2.0, 422.6)
    assert mean_velocity(2.0, 422.6, 0.02) == pytest.approx(q / circular_area(0.02))


def test_the_two_reynolds_forms_agree_exactly_for_a_circular_pipe():
    """Re = rho V D / mu and Re = 4 mdot / (pi D mu) are the same number."""
    for mass_flow, diameter, density, viscosity in (
            (2.0, 0.02, 422.6, 1.1725e-4), (0.05, 0.005, 1141.0, 1.95e-4),
            (12.0, 0.1, 70.9, 1.33e-5)):
        velocity = mean_velocity(mass_flow, density, diameter)
        a = reynolds_number(density, velocity, diameter, viscosity)
        b = reynolds_number_from_mass_flow(mass_flow, diameter, viscosity)
        assert abs(a - b) / a < 1e-15


def test_reynolds_number_is_dimensionless_by_construction():
    """A hand case: rho=1000, V=1, D=1, mu=1e-3 -> Re = 1e6."""
    assert reynolds_number(1000.0, 1.0, 1.0, 1.0e-3) == pytest.approx(1.0e6)


def test_relative_roughness_is_epsilon_over_d():
    assert relative_roughness(1.5e-5, 0.015) == pytest.approx(1.0e-3)


def test_a_smooth_pipe_has_zero_relative_roughness():
    assert relative_roughness(0.0, 0.02) == 0.0


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
def test_a_non_positive_or_non_finite_diameter_is_refused(bad):
    with pytest.raises(InputError):
        circular_area(bad)


def test_a_negative_roughness_is_refused_rather_than_made_absolute():
    with pytest.raises(InputError, match="must not be negative"):
        relative_roughness(-1e-6, 0.02)


# ===========================================================================
# laminar: the exact solution
# ===========================================================================

def test_laminar_friction_factor_is_sixty_four_over_reynolds():
    assert laminar_darcy_friction_factor(1000.0) == pytest.approx(0.064)
    assert laminar_darcy_friction_factor(64.0) == pytest.approx(1.0)


def test_darcy_weisbach_reproduces_hagen_poiseuille_exactly():
    """The independent laminar check, and the strongest one available.

    Hagen-Poiseuille is the closed-form laminar solution. Darcy-Weisbach with
    f_D = 64/Re must reproduce it, and the two are written independently in
    the production module precisely so this can be asserted.
    """
    for mass_flow, diameter, length, density, viscosity in (
            (0.001, 0.01, 1.0, 422.6, 1.1725e-4),
            (0.002, 0.008, 2.5, 1141.0, 1.95e-4),
            (0.00005, 0.004, 0.5, 70.9, 1.33e-5)):
        velocity = mean_velocity(mass_flow, density, diameter)
        reynolds = reynolds_number(density, velocity, diameter, viscosity)
        assert reynolds < REYNOLDS_LAMINAR_LIMIT, "fixture must be laminar"
        friction = laminar_darcy_friction_factor(reynolds)
        via_darcy = darcy_weisbach_pressure_drop(friction, length, diameter,
                                                 density, velocity)
        via_poiseuille = hagen_poiseuille_pressure_drop(
            viscosity, length, volumetric_flow(mass_flow, density), diameter)
        assert via_darcy == pytest.approx(via_poiseuille, rel=1e-12)


def test_laminar_pressure_drop_is_linear_in_length():
    base = solve_line(request_for(mass_flow=0.001, length=1.0, diameter=0.01)).value
    twice = solve_line(request_for(mass_flow=0.001, length=2.0, diameter=0.01)).value
    assert base.flow_regime is FlowRegime.LAMINAR
    assert twice.major_pressure_drop == pytest.approx(
        2.0 * base.major_pressure_drop, rel=1e-12)


def test_laminar_pressure_drop_is_linear_in_mass_flow():
    base = solve_line(request_for(mass_flow=0.0005, length=1.0, diameter=0.01)).value
    twice = solve_line(request_for(mass_flow=0.001, length=1.0, diameter=0.01)).value
    assert base.flow_regime is twice.flow_regime is FlowRegime.LAMINAR
    assert twice.major_pressure_drop == pytest.approx(
        2.0 * base.major_pressure_drop, rel=1e-12)


def test_laminar_pressure_drop_scales_as_one_over_diameter_to_the_fourth():
    """Hagen-Poiseuille: dp proportional to D^-4 at fixed Q."""
    narrow = solve_line(request_for(mass_flow=0.0005, length=1.0,
                                    diameter=0.005)).value
    wide = solve_line(request_for(mass_flow=0.0005, length=1.0,
                                  diameter=0.010)).value
    assert narrow.flow_regime is FlowRegime.LAMINAR
    assert narrow.major_pressure_drop == pytest.approx(
        16.0 * wide.major_pressure_drop, rel=1e-12)


def test_laminar_friction_factor_does_not_depend_on_roughness():
    """64/Re is exact and roughness-free; a dependence would be a leak."""
    smooth = solve_line(request_for(mass_flow=0.001, length=1.0, diameter=0.01,
                                    roughness=0.0)).value
    rough = solve_line(request_for(mass_flow=0.001, length=1.0, diameter=0.01,
                                   roughness=5.0e-5)).value
    assert smooth.flow_regime is FlowRegime.LAMINAR
    assert smooth.darcy_friction_factor == rough.darcy_friction_factor
    assert smooth.major_pressure_drop == rough.major_pressure_drop


# ===========================================================================
# turbulent: an independent oracle, and the correlation's own analytic limits
# ===========================================================================

def independent_colebrook(reynolds: float, roughness: float,
                          digits: int = 50) -> float:
    """A high-precision bisection on the Colebrook equation, in Decimal.

    Deliberately shares nothing with the production solver: different
    arithmetic, different variable, different algorithm, different bracket. A
    test that produced its expectation by calling the code under test would
    check only that the code agrees with itself.
    """
    getcontext().prec = digits
    re_d = Decimal(repr(reynolds))
    eps_d = Decimal(repr(roughness))
    two = Decimal(2)
    ten = Decimal(10)

    def residual(f: Decimal) -> Decimal:
        root = f.sqrt()
        inside = eps_d / Decimal("3.7") + Decimal("2.51") / (re_d * root)
        return Decimal(1) / root + two * (inside.ln() / ten.ln())

    low, high = Decimal("1e-6"), Decimal("1")
    assert residual(low) * residual(high) < 0, "bracket must straddle the root"
    for _ in range(400):
        mid = (low + high) / two
        if residual(low) * residual(mid) <= 0:
            high = mid
        else:
            low = mid
    return float((low + high) / two)


TURBULENT_CASES = [
    (4.0e3, 0.0), (1.0e4, 0.0), (1.0e5, 0.0), (1.0e6, 0.0), (1.0e8, 0.0),
    (1.0e4, 1.0e-4), (1.0e5, 1.0e-4), (1.0e6, 1.0e-4),
    (1.0e5, 1.0e-3), (1.0e6, 1.0e-3), (1.0e7, 1.0e-3),
    (1.0e5, 1.0e-2), (1.0e6, 1.0e-2), (1.0e8, 1.0e-2),
    (1.0e5, 5.0e-2), (1.0e8, 5.0e-2),
]


@pytest.mark.parametrize("reynolds,roughness", TURBULENT_CASES)
def test_the_solver_matches_an_independent_high_precision_oracle(
        reynolds, roughness):
    friction, _report = colebrook_darcy_friction_factor(reynolds, roughness)
    expected = independent_colebrook(reynolds, roughness)
    assert friction == pytest.approx(expected, rel=1e-11)


@pytest.mark.parametrize("reynolds,roughness", TURBULENT_CASES)
def test_every_accepted_turbulent_solve_satisfies_the_equation(
        reynolds, roughness):
    """The residual is evaluated independently of the solver's own stopping
    rule, because a converged bracket is not the same claim as a small
    residual."""
    friction, _report = colebrook_darcy_friction_factor(reynolds, roughness)
    assert abs(colebrook_residual(friction, reynolds, roughness)) < 1e-10


@pytest.mark.parametrize("reynolds,roughness", TURBULENT_CASES)
def test_every_turbulent_solve_converges_within_the_iteration_ceiling(
        reynolds, roughness):
    _friction, report = colebrook_darcy_friction_factor(reynolds, roughness)
    assert report.converged
    assert report.iterations <= 60


@pytest.mark.parametrize("roughness", [1.0e-4, 1.0e-3, 1.0e-2, 5.0e-2])
def test_the_high_reynolds_limit_is_the_von_karman_rough_pipe_law(roughness):
    """As Re grows the Colebrook viscous term vanishes and the equation
    collapses to a closed form: f_D = 1/(2 log10(3.7/(eps/D)))^2.

    An analytic limit of the correlation itself, not an independent
    measurement -- and recorded as such.
    """
    friction, _report = colebrook_darcy_friction_factor(1.0e8, roughness)
    fully_rough = 1.0 / (2.0 * math.log10(3.7 / roughness)) ** 2
    assert friction == pytest.approx(fully_rough, rel=2e-3)


@pytest.mark.parametrize("reynolds", [1.0e5, 1.0e6, 1.0e7])
def test_the_smooth_pipe_case_satisfies_the_prandtl_law(reynolds):
    """With eps = 0 the Colebrook equation reduces exactly to

        1/sqrt(f) = 2 log10(Re sqrt(f)) - 2 log10(2.51)

    and 2 log10(2.51) = 0.79934..., which is what the textbook Prandtl law
    rounds to 0.8. The exact reduction is asserted to machine precision; the
    rounded classical form is checked separately and loosely, because the
    difference is the rounding and not the model.
    """
    friction, _report = colebrook_darcy_friction_factor(reynolds, 0.0)
    root = math.sqrt(friction)
    exact = 2.0 * math.log10(reynolds * root) - 2.0 * math.log10(2.51)
    assert 1.0 / root == pytest.approx(exact, rel=1e-12)

    classical = 2.0 * math.log10(reynolds * root) - 0.8
    assert 1.0 / root == pytest.approx(classical, rel=1e-3)


def test_blasius_is_a_sanity_comparison_and_not_the_oracle():
    """Blasius approximates Colebrook for smooth pipes at moderate Re.

    Close, deliberately not equal: it is an explicit approximation *to* the
    equation the production path solves, and asserting equality would make an
    approximation the acceptance criterion.
    """
    friction, _report = colebrook_darcy_friction_factor(1.0e5, 0.0)
    blasius = 0.316 / 1.0e5 ** 0.25
    assert friction == pytest.approx(blasius, rel=0.05)
    assert friction != blasius


def test_a_rougher_pipe_has_a_larger_friction_factor_at_fixed_reynolds():
    previous = 0.0
    for roughness in (0.0, 1.0e-4, 1.0e-3, 1.0e-2, 5.0e-2):
        friction, _ = colebrook_darcy_friction_factor(1.0e6, roughness)
        assert friction > previous
        previous = friction


# ===========================================================================
# Darcy versus Fanning: the factor-of-four mutation
# ===========================================================================

def test_using_the_fanning_factor_in_darcy_weisbach_is_wrong_by_exactly_four():
    """The classic implementation error, proved detectable.

    f_D = 4 f_F. Substituting Fanning into Darcy-Weisbach underpredicts the
    loss by exactly four, and any check worth having must fail loudly on it.
    """
    result = solve_line(request_for()).value
    darcy = result.darcy_friction_factor
    fanning = darcy / 4.0

    correct = darcy_weisbach_pressure_drop(
        darcy, result.length, result.inner_diameter,
        result.fluid.density, result.mean_velocity)
    mutated = darcy_weisbach_pressure_drop(
        fanning, result.length, result.inner_diameter,
        result.fluid.density, result.mean_velocity)

    assert correct == pytest.approx(result.major_pressure_drop, rel=1e-15)
    assert mutated == pytest.approx(correct / 4.0, rel=1e-15)
    assert abs(mutated - correct) / correct > 0.7


def test_the_result_states_the_friction_convention_it_used():
    result = solve_line(request_for()).value
    assert "Darcy" in result.friction_convention
    assert "f_D = 4 f_F" in result.friction_convention


# ===========================================================================
# the transition band
# ===========================================================================

def transitional_request():
    """A state whose Reynolds number lands between the two boundaries."""
    for mass_flow in (0.0026, 0.0028, 0.0030, 0.0032):
        candidate = request_for(mass_flow=mass_flow, diameter=0.01)
        reynolds = reynolds_number_from_mass_flow(mass_flow, 0.01, 1.1725e-4)
        if REYNOLDS_LAMINAR_LIMIT <= reynolds < REYNOLDS_TURBULENT_ONSET:
            return candidate, reynolds
    raise AssertionError("no transitional fixture found")


def test_a_transitional_line_reports_no_friction_factor():
    request, reynolds = transitional_request()
    solution = solve_line(request)
    result = solution.value
    assert result.flow_regime is FlowRegime.TRANSITIONAL
    assert result.darcy_friction_factor is None
    assert result.major_pressure_drop is None
    assert result.outlet_pressure is None


def test_a_transitional_line_still_reports_the_geometry_and_reynolds_number():
    request, reynolds = transitional_request()
    result = solve_line(request).value
    assert result.reynolds_number == pytest.approx(reynolds, rel=1e-12)
    assert result.mean_velocity > 0.0
    assert result.area > 0.0


def test_the_transitional_diagnostic_says_why_and_names_both_boundaries():
    request, _ = transitional_request()
    solution = solve_line(request)
    assert solution.status is Status.OK_WITH_WARNINGS
    diagnostic = solution.diagnostics[0]
    assert diagnostic.code == "LINE_TRANSITIONAL_REGIME_UNSUPPORTED"
    assert "invent" in diagnostic.message
    assert diagnostic.detail["laminar_limit"] == REYNOLDS_LAMINAR_LIMIT
    assert diagnostic.detail["turbulent_onset"] == REYNOLDS_TURBULENT_ONSET


def test_nothing_interpolates_across_the_transition_band():
    """A friction factor here would sit between 64/Re and Colebrook and look
    entirely plausible. The result object refuses to hold one."""
    from rocketforge.engineering.line.results import LineResult

    request, _ = transitional_request()
    result = solve_line(request).value
    with pytest.raises(DomainError, match="invented"):
        LineResult(**{**{f: getattr(result, f)
                         for f in LineResult.__dataclass_fields__},
                      "darcy_friction_factor": 0.04})


# ===========================================================================
# the fluid handshake
# ===========================================================================

def test_a_gas_state_is_refused_rather_than_solved_as_a_liquid():
    solution = solve_line(request_for(phase=FluidPhase.GAS))
    assert solution.value is None
    assert solution.diagnostics[0].code == "LINE_FLUID_STATE_UNUSABLE"
    assert "compressible" in solution.diagnostics[0].message


def test_a_two_phase_state_is_refused():
    solution = solve_line(request_for(phase=FluidPhase.TWO_PHASE))
    assert solution.value is None
    assert "two-phase" in solution.diagnostics[0].message


def test_an_unknown_phase_is_refused_and_never_assumed_liquid():
    solution = solve_line(request_for(phase=None))
    assert solution.value is None
    assert "not assumed to be liquid" in solution.diagnostics[0].message


def test_a_state_without_viscosity_is_refused_not_defaulted():
    solution = solve_line(
        request_for(omit=(FluidProperty.DYNAMIC_VISCOSITY,)))
    assert solution.value is None
    assert "dynamic_viscosity" in solution.diagnostics[0].message


def test_the_line_uses_the_states_own_density_and_viscosity():
    result = solve_line(request_for()).value
    assert result.fluid.density == 422.6
    assert result.fluid.dynamic_viscosity == 1.1725e-4


def test_the_line_records_the_property_providers_identity():
    result = solve_line(request_for()).value
    assert result.fluid.provider_id == "t"
    assert result.fluid.backend == "test-model"


# ===========================================================================
# pressure semantics
# ===========================================================================

def test_the_inlet_pressure_is_the_fluid_states_own_pressure():
    result = solve_line(request_for(pressure=4.5e5)).value
    assert result.inlet_pressure == 4.5e5
    assert result.fluid.pressure == 4.5e5


def test_outlet_pressure_is_inlet_minus_the_friction_loss():
    result = solve_line(request_for()).value
    assert result.outlet_pressure == pytest.approx(
        result.inlet_pressure - result.major_pressure_drop, rel=1e-15)


def test_a_loss_exceeding_the_inlet_pressure_is_refused_not_clamped():
    solution = solve_line(request_for(mass_flow=8.0, length=200.0,
                                      diameter=0.01, pressure=2.0e5))
    assert solution.value is None
    diagnostic = solution.diagnostics[0]
    assert diagnostic.code == "LINE_INSUFFICIENT_INLET_PRESSURE"
    assert "Nothing is clamped" in diagnostic.message
    assert diagnostic.detail["major_pressure_drop"] > diagnostic.detail["inlet_pressure"]


# ===========================================================================
# mutation proofs
# ===========================================================================

def test_a_viscosity_off_by_a_thousand_changes_the_regime_and_the_answer():
    """mu in mPa.s instead of Pa.s moves Re by three decades and flips the
    regime. Checked on the relation, because the mutated line's friction loss
    exceeds its inlet pressure and is refused outright -- which is itself the
    model noticing, and is asserted below."""
    honest_re = reynolds_number_from_mass_flow(2.0, 0.02, 1.1725e-4)
    mutated_re = reynolds_number_from_mass_flow(2.0, 0.02, 1.1725e-4 * 1000.0)
    assert mutated_re == pytest.approx(honest_re / 1000.0, rel=1e-12)
    from rocketforge.engineering.line import classify

    assert classify(honest_re) is FlowRegime.TURBULENT
    assert classify(mutated_re) is FlowRegime.LAMINAR

    solution = solve_line(request_for(viscosity=1.1725e-4 * 1000.0))
    assert solution.value is None
    assert solution.diagnostics[0].code == "LINE_INSUFFICIENT_INLET_PRESSURE"


def test_a_density_off_by_a_thousand_changes_velocity_and_pressure_drop():
    """rho in g/cm3 instead of kg/m3 raises the velocity by three decades."""
    honest_v = mean_velocity(2.0, 422.6, 0.02)
    mutated_v = mean_velocity(2.0, 0.4226, 0.02)
    assert mutated_v == pytest.approx(1000.0 * honest_v, rel=1e-12)

    from rocketforge.engineering.line import dynamic_pressure

    assert dynamic_pressure(0.4226, mutated_v) > 1.0e6 * dynamic_pressure(
        422.6, honest_v) / 1.0e3


def test_halving_the_diameter_changes_area_roughness_and_reynolds_together():
    """A diameter that moved without the quantities derived from it following
    would be an internally inconsistent result."""
    wide = solve_line(request_for(mass_flow=0.2, diameter=0.02,
                                  roughness=2.0e-5)).value
    narrow = solve_line(request_for(mass_flow=0.2, diameter=0.01,
                                    roughness=2.0e-5)).value
    assert narrow.area == pytest.approx(wide.area / 4.0, rel=1e-12)
    assert narrow.relative_roughness == pytest.approx(
        2.0 * wide.relative_roughness, rel=1e-12)
    assert narrow.reynolds_number == pytest.approx(
        2.0 * wide.reynolds_number, rel=1e-12)


def test_a_pressure_given_in_bar_instead_of_pascal_is_caught_by_the_model():
    """3 bar is 3e5 Pa. Supplying 3.0 leaves nothing to drive the flow."""
    solution = solve_line(request_for(pressure=3.0))
    assert solution.value is None
    assert solution.diagnostics[0].code == "LINE_INSUFFICIENT_INLET_PRESSURE"


# ===========================================================================
# domain refusals
# ===========================================================================

def test_colebrook_is_not_applied_below_the_turbulent_onset():
    with pytest.raises(InputError, match="turbulent correlation"):
        colebrook_darcy_friction_factor(REYNOLDS_TURBULENT_ONSET - 1.0, 0.0)


def test_colebrook_is_not_extrapolated_above_the_moody_chart():
    with pytest.raises(InputError, match="turbulent zone"):
        colebrook_darcy_friction_factor(COLEBROOK_REYNOLDS_MAX * 10.0, 0.0)


def test_a_relative_roughness_beyond_the_chart_is_refused():
    with pytest.raises(InputError, match="not extrapolated"):
        colebrook_darcy_friction_factor(1.0e6, MAX_RELATIVE_ROUGHNESS * 2.0)


def test_an_out_of_domain_line_reports_rather_than_raises():
    solution = solve_line(request_for(mass_flow=2.0, diameter=0.02,
                                      roughness=0.02))
    assert solution.value is None
    assert solution.diagnostics[0].code == "LINE_OUTSIDE_MODEL_DOMAIN"


@pytest.mark.parametrize("field,bad", [
    ("mass_flow", 0.0), ("mass_flow", -1.0), ("length", 0.0),
    ("inner_diameter", 0.0), ("mass_flow", float("nan")),
    ("length", float("inf")),
])
def test_invalid_geometry_or_flow_raises_rather_than_being_clamped(field, bad):
    kwargs = {"mass_flow": 1.0, "length": 1.0, "diameter": 0.01,
              "roughness": 0.0}
    kwargs[{"inner_diameter": "diameter"}.get(field, field)] = bad
    with pytest.raises(InputError):
        request_for(**kwargs)


def test_a_negative_absolute_roughness_is_refused():
    with pytest.raises(InputError):
        request_for(roughness=-1.0e-6)


# ===========================================================================
# determinism and state
# ===========================================================================

def test_repeated_identical_solves_are_bit_identical():
    first = solve_line(request_for()).value
    for _ in range(5):
        again = solve_line(request_for()).value
        assert again.darcy_friction_factor == first.darcy_friction_factor
        assert again.major_pressure_drop == first.major_pressure_drop
        assert again.reynolds_number == first.reynolds_number


def test_no_state_leaks_between_laminar_and_turbulent_solves():
    a1 = solve_line(request_for(mass_flow=0.001, diameter=0.01)).value
    b1 = solve_line(request_for()).value
    a2 = solve_line(request_for(mass_flow=0.001, diameter=0.01)).value
    b2 = solve_line(request_for()).value
    a3 = solve_line(request_for(mass_flow=0.001, diameter=0.01)).value
    assert a1.darcy_friction_factor == a2.darcy_friction_factor \
        == a3.darcy_friction_factor
    assert b1.darcy_friction_factor == b2.darcy_friction_factor
    assert a1.flow_regime is FlowRegime.LAMINAR
    assert b1.flow_regime is FlowRegime.TURBULENT


def test_a_canonical_case_is_unchanged_after_every_failure_mode():
    before = solve_line(request_for()).value
    solve_line(request_for(phase=FluidPhase.GAS))
    solve_line(request_for(pressure=3.0))
    solve_line(request_for(roughness=0.02))
    transitional, _ = transitional_request()
    solve_line(transitional)
    after = solve_line(request_for()).value
    assert after.darcy_friction_factor == before.darcy_friction_factor
    assert after.major_pressure_drop == before.major_pressure_drop


def test_the_reynolds_identity_closes_on_every_result():
    for mass_flow in (0.001, 0.01, 0.5, 2.0, 6.0):
        solution = solve_line(request_for(mass_flow=mass_flow))
        if solution.value is None:
            continue
        assert solution.value.reynolds_identity_residual < 1e-14
