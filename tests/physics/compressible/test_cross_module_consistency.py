"""Do the ten modules agree with each other?

Every other test file asks whether one module is right. This one asks whether
the subsystem is *one* library: whether the mass-flow parameter agrees with the
area relation, whether an oblique shock really is a normal shock in disguise,
whether the two states across a shock lie on a common Fanno line and a common
Rayleigh line, and whether the nozzle's stations satisfy the relations it
claims to have composed.

These identities are what let a future engineering module depend on
``rocketforge.physics.compressible`` as a whole rather than on ten separate
things that happen to live in one folder. They are the blocking gate of the
Phase 4G freeze.

The grids are canonical and shared, so a module cannot pass by being tested
only where it happens to be accurate.
"""

from __future__ import annotations

import numpy as np
import pytest

from rocketforge.physics.compressible import (
    AreaDistribution,
    FlowBranch,
    NozzleOperating,
    NozzleRegime,
    PerfectGas,
    ShockBranch,
    fanno,
    isentropic,
    mass_flow,
    normal_shock,
    nozzle,
    oblique_shock,
    prandtl_meyer,
    rayleigh,
)

# ---------------------------------------------------------------------------
# canonical grids -- 51 and 52
# ---------------------------------------------------------------------------

#: Every module is validated on the same gammas: diatomic air, the value used
#: for combustion products, and the ends of the advisory band.
GAMMAS = (1.2, 1.3, 1.4, 1.66)

#: Deliberately includes both sides of the sonic point and the sonic point
#: itself, because that is where every relation in the module is flattest.
SUBSONIC = (0.05, 0.2, 0.5, 0.8, 0.95, 0.999)
SUPERSONIC = (1.001, 1.05, 1.5, 2.0, 3.0, 5.0, 10.0)
ALL_MACH = SUBSONIC + (1.0,) + SUPERSONIC

#: A/A* values that are meaningful on both branches.
AREA_RATIOS = (1.0001, 1.05, 1.5, 2.0, 4.0, 10.0, 50.0)


def gas(gamma: float = 1.4) -> PerfectGas:
    return PerfectGas(gamma=gamma, gas_constant=287.05)


# ===========================================================================
# 27 -- the isentropic ratios are mutually consistent
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_isentropic_ratios_satisfy_the_ideal_gas_law(gamma):
    """p/p0 divided by rho/rho0 must be T/T0. Nothing else is possible."""
    air = gas(gamma)
    mach = np.array(ALL_MACH)
    pressure = np.asarray(isentropic.pressure_ratio(mach, air))
    density = np.asarray(isentropic.density_ratio(mach, air))
    temperature = np.asarray(isentropic.temperature_ratio(mach, air))
    assert np.allclose(pressure / density, temperature, rtol=1e-14)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_starred_ratios_are_the_stagnation_ratios_referred_to_sonic(gamma):
    air = gas(gamma)
    mach = np.array(ALL_MACH)
    for direct, star in ((isentropic.pressure_ratio, isentropic.pressure_ratio_star),
                         (isentropic.temperature_ratio,
                          isentropic.temperature_ratio_star),
                         (isentropic.density_ratio, isentropic.density_ratio_star)):
        expected = np.asarray(direct(mach, air)) / float(direct(1.0, air))
        assert np.allclose(np.asarray(star(mach, air)), expected, rtol=1e-13)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", ALL_MACH)
def test_the_aggregate_record_matches_the_individual_relations(gamma, mach):
    """``ratios_from_mach`` is a convenience, not a second implementation."""
    air = gas(gamma)
    record = isentropic.ratios_from_mach(mach, air)
    assert record.temperature_ratio == isentropic.temperature_ratio(mach, air)
    assert record.pressure_ratio == isentropic.pressure_ratio(mach, air)
    assert record.density_ratio == isentropic.density_ratio(mach, air)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", SUBSONIC + (1.0,) + SUPERSONIC[:4])
def test_the_closed_form_inverses_return_the_mach_they_came_from(gamma, mach):
    air = gas(gamma)
    for forward, inverse in (
        (isentropic.temperature_ratio, isentropic.mach_from_temperature_ratio),
        (isentropic.pressure_ratio, isentropic.mach_from_pressure_ratio),
        (isentropic.density_ratio, isentropic.mach_from_density_ratio),
    ):
        assert float(inverse(forward(mach, air), air)) == pytest.approx(mach, rel=1e-10)


# ===========================================================================
# 28 -- the area relation round trips on both branches
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", SUBSONIC + SUPERSONIC)
def test_area_mach_round_trips_on_its_own_branch(gamma, mach):
    air = gas(gamma)
    branch = FlowBranch.SUBSONIC if mach < 1.0 else FlowBranch.SUPERSONIC
    ratio = float(isentropic.area_ratio(mach, air))
    recovered = float(isentropic.mach_from_area_ratio(ratio, air, branch).unwrap())
    # Near sonic the relation is quadratically flat, so half the digits are
    # gone by construction -- 04 section 4 quantifies exactly this.
    tolerance = 1e-6 if abs(mach - 1.0) < 0.05 else 1e-9
    assert recovered == pytest.approx(mach, rel=tolerance)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("ratio", AREA_RATIOS)
def test_the_two_area_mach_branches_stay_apart(ratio, gamma):
    air = gas(gamma)
    subsonic = float(isentropic.mach_from_area_ratio(
        ratio, air, FlowBranch.SUBSONIC).unwrap())
    supersonic = float(isentropic.mach_from_area_ratio(
        ratio, air, FlowBranch.SUPERSONIC).unwrap())
    assert subsonic <= 1.0 <= supersonic
    # The area residual is the Mach residual amplified by dA/dM, which is
    # enormous at a large area ratio: the subsonic root of A/A* = 50 sits at
    # M = 0.012, where converging M to 1e-10 leaves A/A* good to about 1e-8.
    assert isentropic.area_ratio(subsonic, air) == pytest.approx(ratio, rel=1e-7)
    assert isentropic.area_ratio(supersonic, air) == pytest.approx(ratio, rel=1e-9)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("ratio", AREA_RATIOS)
def test_the_paired_request_returns_the_same_two_roots(ratio, gamma):
    air = gas(gamma)
    pair = isentropic.mach_from_area_ratio_both(ratio, air).unwrap()
    assert pair.subsonic == isentropic.mach_from_area_ratio(
        ratio, air, FlowBranch.SUBSONIC).unwrap()
    assert pair.supersonic == isentropic.mach_from_area_ratio(
        ratio, air, FlowBranch.SUPERSONIC).unwrap()


# ===========================================================================
# 29, 30 -- mass flow against the area relation
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_mass_flow_ratio_is_the_reciprocal_area_ratio(gamma):
    """mdot/mdot_choked = MFP/Gamma = A*/A -- the link between two modules."""
    air = gas(gamma)
    mach = np.array([m for m in ALL_MACH if m > 0.0])
    ratio = np.asarray(mass_flow.mass_flow_over_choked(mach, air))
    parameter = (np.asarray(mass_flow.mass_flow_parameter(mach, air))
                 / mass_flow.choked_mass_flow_coefficient(air))
    area = 1.0 / np.asarray(isentropic.area_ratio(mach, air))
    assert np.allclose(ratio, parameter, rtol=1e-13)
    assert np.allclose(ratio, area, rtol=1e-12)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_choked_mass_flow_is_the_mass_flow_at_mach_one(gamma):
    air = gas(gamma)
    area, p0, t0 = 0.01, 1.0e6, 3000.0
    direct = mass_flow.choked_mass_flow(air, area, p0, t0)
    through_relation = float(mass_flow.mass_flow(1.0, air, area, p0, t0))
    assert direct == pytest.approx(through_relation, rel=1e-14)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_mass_flux_is_the_mass_flow_per_unit_area(gamma):
    air = gas(gamma)
    p0, t0 = 1.0e6, 3000.0
    for mach in (0.3, 1.0, 2.5):
        flux = float(mass_flow.mass_flux(mach, air, p0, t0))
        flow = float(mass_flow.mass_flow(mach, air, 0.25, p0, t0))
        assert flow / 0.25 == pytest.approx(flux, rel=1e-14)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("branch", [FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC])
def test_the_mass_flow_inverse_inherits_the_area_mach_branch(gamma, branch):
    """A mass-flow ratio has two Mach roots for the same reason an area does."""
    air = gas(gamma)
    seed = 0.4 if branch is FlowBranch.SUBSONIC else 2.5
    target = float(mass_flow.mass_flow_over_choked(seed, air))
    recovered = float(mass_flow.mach_from_mass_flow_ratio(target, air, branch).unwrap())
    assert recovered == pytest.approx(seed, rel=1e-8)
    if branch is FlowBranch.SUBSONIC:
        assert recovered < 1.0
    else:
        assert recovered > 1.0


# ===========================================================================
# 31, 32 -- the normal shock against the perfect gas and the isentropic module
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_shock_temperature_ratio_follows_from_pressure_and_density(gamma):
    """T2/T1 = (p2/p1)/(rho2/rho1). The ideal gas law across a shock."""
    air = gas(gamma)
    mach = np.array(SUPERSONIC)
    pressure = np.asarray(normal_shock.pressure_ratio(mach, air))
    density = np.asarray(normal_shock.density_ratio(mach, air))
    temperature = np.asarray(normal_shock.temperature_ratio(mach, air))
    assert np.allclose(pressure / density, temperature, rtol=1e-13)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", SUPERSONIC)
def test_the_shock_total_pressure_ratio_is_reconstructible_from_isentropic(gamma, mach1):
    """p02/p01 = (p2/p1)(p01/p1)^-1(p02/p2) -- built from the other module."""
    air = gas(gamma)
    result = normal_shock.solve(mach1, air)
    upstream = float(isentropic.pressure_ratio(mach1, air))          # p1/p01
    downstream = float(isentropic.pressure_ratio(result.mach2, air))  # p2/p02
    reconstructed = result.pressure_ratio * upstream / downstream
    assert reconstructed == pytest.approx(result.stagnation_pressure_ratio, rel=1e-12)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", SUPERSONIC)
def test_the_shock_conserves_stagnation_temperature(gamma, mach1):
    air = gas(gamma)
    result = normal_shock.solve(mach1, air)
    assert result.stagnation_temperature_ratio == 1.0
    upstream = 1.0 / float(isentropic.temperature_ratio(mach1, air))
    downstream = 1.0 / float(isentropic.temperature_ratio(result.mach2, air))
    assert result.temperature_ratio * downstream / upstream == pytest.approx(1.0,
                                                                            rel=1e-13)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", SUPERSONIC)
def test_the_shock_sonic_area_ratio_is_the_stagnation_pressure_loss(gamma, mach1):
    """A2*/A1* = p01/p02, which is what makes the nozzle's downstream branch work."""
    air = gas(gamma)
    result = normal_shock.solve(mach1, air)
    assert result.area_star_ratio == pytest.approx(
        1.0 / result.stagnation_pressure_ratio, rel=1e-15)


# ===========================================================================
# 33, 34 -- the shock lies on a common Fanno line and a common Rayleigh line
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", (1.2, 1.5, 2.0, 3.0, 5.0))
def test_the_two_shock_states_lie_on_one_fanno_line(gamma, mach1):
    """Constant area and adiabatic: the defining conditions of a Fanno line."""
    air = gas(gamma)
    result = normal_shock.solve(mach1, air)
    mach2 = result.mach2
    for name, relation, expected in (
        ("T2/T1", fanno.temperature_ratio, result.temperature_ratio),
        ("p2/p1", fanno.pressure_ratio, result.pressure_ratio),
        ("p02/p01", fanno.stagnation_pressure_ratio, result.stagnation_pressure_ratio),
    ):
        across = float(relation(mach2, air)) / float(relation(mach1, air))
        assert across == pytest.approx(expected, rel=1e-12), name


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", (1.2, 1.5, 2.0, 3.0, 5.0))
def test_the_two_shock_states_lie_on_one_rayleigh_line(gamma, mach1):
    """Constant area and the frictionless momentum balance: a Rayleigh line."""
    air = gas(gamma)
    result = normal_shock.solve(mach1, air)
    mach2 = result.mach2
    for name, relation, expected in (
        ("p2/p1", rayleigh.pressure_ratio, result.pressure_ratio),
        ("T2/T1", rayleigh.temperature_ratio, result.temperature_ratio),
        ("rho2/rho1", rayleigh.density_ratio, result.density_ratio),
    ):
        across = float(relation(mach2, air)) / float(relation(mach1, air))
        assert across == pytest.approx(expected, rel=1e-12), name


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_fanno_coincidences_with_the_isentropic_family_still_hold(gamma):
    """Two exact equalities, and the ratios that must *not* coincide."""
    air = gas(gamma)
    mach = np.array([m for m in ALL_MACH if m > 0.0])
    assert np.allclose(np.asarray(fanno.temperature_ratio(mach, air)),
                       np.asarray(isentropic.temperature_ratio_star(mach, air)),
                       rtol=1e-14)
    assert np.allclose(np.asarray(fanno.stagnation_pressure_ratio(mach, air)),
                       np.asarray(isentropic.area_ratio(mach, air)), rtol=1e-13)
    # And the ones that are different families, asserted so a tidy-up cannot
    # quietly merge them.
    assert not np.allclose(np.asarray(fanno.pressure_ratio(mach, air)),
                           np.asarray(isentropic.pressure_ratio_star(mach, air)))
    assert not np.allclose(np.asarray(rayleigh.temperature_ratio(mach, air)),
                           np.asarray(fanno.temperature_ratio(mach, air)))


# ===========================================================================
# 35, 36 -- Prandtl-Meyer against the isentropic module
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", (1.05, 1.5, 2.0, 3.0))
def test_an_expansion_is_isentropic_and_its_ratios_prove_it(gamma, mach1):
    air = gas(gamma)
    turn = np.radians(10.0)
    result = prandtl_meyer.expand(mach1, turn, air).unwrap()
    # nu2 is recomputed from the Mach number actually returned, not stored as
    # the requested sum -- so the record is self-consistent with mach2, and the
    # residual here is the inversion tolerance carried through dnu/dM. That
    # derivative is smallest just above sonic, which is where this is loosest.
    assert result.nu2 == pytest.approx(result.nu1 + turn, rel=1e-9)
    assert float(prandtl_meyer.nu(result.mach2, air)) == result.nu2

    for relation, field in ((isentropic.pressure_ratio, "pressure_ratio"),
                            (isentropic.temperature_ratio, "temperature_ratio"),
                            (isentropic.density_ratio, "density_ratio")):
        expected = (float(relation(result.mach2, air))
                    / float(relation(result.mach1, air)))
        assert getattr(result, field) == pytest.approx(expected, rel=1e-11)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_an_expansion_preserves_both_stagnation_quantities(gamma):
    """Isentropic and adiabatic: p0 and T0 both survive the fan.

    The record carries static ratios, so the stagnation ones are reconstructed
    from the isentropic module -- which is the cross-module claim in any case.
    """
    air = gas(gamma)
    result = prandtl_meyer.expand(2.0, np.radians(15.0), air).unwrap()
    upstream_p = float(isentropic.pressure_ratio(result.mach1, air))
    downstream_p = float(isentropic.pressure_ratio(result.mach2, air))
    assert result.pressure_ratio * upstream_p / downstream_p == pytest.approx(1.0,
                                                                             rel=1e-11)
    upstream_t = float(isentropic.temperature_ratio(result.mach1, air))
    downstream_t = float(isentropic.temperature_ratio(result.mach2, air))
    assert result.temperature_ratio * upstream_t / downstream_t == pytest.approx(
        1.0, rel=1e-11)


def test_there_is_exactly_one_mach_angle_implementation():
    """36: Prandtl-Meyer re-exports the isentropic function, it does not copy it."""
    assert prandtl_meyer.mach_angle is isentropic.mach_angle


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", (1.001, 1.5, 3.0, 10.0))
def test_the_prandtl_meyer_inverse_returns_its_own_mach(gamma, mach):
    air = gas(gamma)
    angle = float(prandtl_meyer.nu(mach, air))
    recovered = float(prandtl_meyer.mach_from_nu(angle, air).unwrap())
    tolerance = 1e-5 if mach < 1.01 else 1e-9
    assert recovered == pytest.approx(mach, rel=tolerance)


# ===========================================================================
# 37, 38, 39 -- the oblique shock is a normal shock in disguise
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", (1.5, 2.0, 3.0, 5.0))
def test_an_oblique_shock_is_the_normal_shock_at_its_normal_component(gamma, mach1):
    air = gas(gamma)
    result = oblique_shock.solve(mach1, np.radians(10.0), air, ShockBranch.WEAK).unwrap()
    normal_component = mach1 * np.sin(result.beta)
    assert result.mach_normal1 == pytest.approx(normal_component, rel=1e-12)

    independent = normal_shock.solve(result.mach_normal1, air)
    assert result.pressure_ratio == independent.pressure_ratio
    assert result.density_ratio == independent.density_ratio
    assert result.temperature_ratio == independent.temperature_ratio
    assert result.stagnation_pressure_ratio == independent.stagnation_pressure_ratio
    assert result.mach_normal2 == independent.mach2


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", (1.5, 2.0, 3.0, 5.0))
def test_a_normal_wave_angle_reduces_the_oblique_shock_to_a_normal_shock(gamma, mach1):
    """38: at beta = 90 degrees the two modules must agree exactly."""
    air = gas(gamma)
    result = oblique_shock.solve_from_beta(mach1, 0.5 * np.pi, air).unwrap()
    independent = normal_shock.solve(mach1, air)
    assert result.theta == pytest.approx(0.0, abs=1e-15)
    assert result.mach_normal1 == pytest.approx(mach1, rel=1e-15)
    assert result.pressure_ratio == independent.pressure_ratio
    assert result.stagnation_pressure_ratio == independent.stagnation_pressure_ratio
    assert result.mach2 == pytest.approx(independent.mach2, rel=1e-12)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", (1.5, 2.0, 3.0, 5.0))
def test_a_mach_wave_carries_no_jump_at_all(gamma, mach1):
    """39: as beta approaches the Mach angle the shock vanishes."""
    air = gas(gamma)
    result = oblique_shock.solve_from_beta(
        mach1, float(isentropic.mach_angle(mach1)), air).unwrap()
    assert result.theta == pytest.approx(0.0, abs=1e-12)
    assert result.pressure_ratio == pytest.approx(1.0, rel=1e-12)
    assert result.stagnation_pressure_ratio == pytest.approx(1.0, rel=1e-12)
    assert result.mach2 == pytest.approx(mach1, rel=1e-12)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", (2.0, 3.0, 5.0))
def test_the_weak_root_is_always_the_shallower_of_the_two(gamma, mach1):
    air = gas(gamma)
    pair = oblique_shock.solve_both(mach1, np.radians(10.0), air).unwrap()
    assert pair.weak.beta < pair.strong.beta
    assert pair.weak.stagnation_pressure_ratio > pair.strong.stagnation_pressure_ratio
    assert pair.weak.mach2 > pair.strong.mach2


# ===========================================================================
# 40, 41 -- Fanno's two conventions and its choking limit
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
def test_darcy_and_fanning_describe_the_same_duct(gamma):
    """f_D = 4 f_F, so the two groups are one number stated two ways."""
    air = gas(gamma)
    fanning = 0.005
    darcy = fanno.fanning_to_darcy(fanning)
    assert darcy == pytest.approx(4.0 * fanning, rel=1e-15)
    assert fanno.darcy_to_fanning(darcy) == pytest.approx(fanning, rel=1e-15)

    length, diameter = 5.0, 0.1
    from_fanning = fanno.duct_parameter_from_geometry(fanning, length, diameter)
    from_darcy = fanno.duct_parameter_from_geometry(
        fanno.darcy_to_fanning(darcy), length, diameter)
    assert from_fanning == pytest.approx(from_darcy, rel=1e-15)
    # The group is 4 f_F L/D, so it equals f_D L/D under the Darcy reading.
    assert from_fanning == pytest.approx(darcy * length / diameter, rel=1e-14)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", (0.2, 0.5, 0.9, 1.5, 3.0))
def test_the_remaining_friction_length_takes_the_flow_exactly_to_sonic(gamma, mach):
    """41: spend the whole available duct and the outlet is M = 1, either branch."""
    air = gas(gamma)
    available = float(fanno.friction_parameter(mach, air))
    result = fanno.downstream_mach(mach, available, air)
    assert result.value is not None
    assert result.value.downstream.mach == pytest.approx(1.0, abs=2e-5)
    assert result.value.remaining_to_choking == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", (0.3, 0.7, 1.5, 3.0))
def test_a_duct_past_the_limit_does_not_cross_the_sonic_point(gamma, mach):
    air = gas(gamma)
    available = float(fanno.friction_parameter(mach, air))
    result = fanno.downstream_mach(mach, available * 1.001, air)
    assert result.value is None
    assert any(d.code == "FRICTION_CHOKED" for d in result.diagnostics)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("branch", [FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC])
def test_the_fanno_inverse_stays_on_the_branch_it_was_given(gamma, branch):
    air = gas(gamma)
    seed = 0.4 if branch is FlowBranch.SUBSONIC else 2.5
    target = float(fanno.friction_parameter(seed, air))
    recovered = float(fanno.mach_from_friction_parameter(target, air, branch).unwrap())
    assert recovered == pytest.approx(seed, rel=1e-8)
    assert (recovered < 1.0) is (branch is FlowBranch.SUBSONIC)


# ===========================================================================
# 42, 43 -- Rayleigh's two maxima and its choking limit
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_two_rayleigh_maxima_sit_at_different_mach_numbers(gamma):
    """42: the static maximum is at 1/sqrt(gamma), the stagnation one at 1."""
    air = gas(gamma)
    peak = rayleigh.mach_at_maximum_temperature(air)
    assert peak == pytest.approx(1.0 / np.sqrt(gamma), rel=1e-15)
    assert peak < 1.0

    mach = np.linspace(0.05, 0.999, 400)
    static = np.asarray(rayleigh.temperature_ratio(mach, air))
    assert mach[int(np.argmax(static))] == pytest.approx(peak, abs=3e-3)
    assert static.max() <= rayleigh.maximum_temperature_ratio(air) * (1 + 1e-12)

    total = np.asarray(rayleigh.stagnation_temperature_ratio(mach, air))
    assert np.all(np.diff(total) > 0.0)              # still rising at the T peak
    assert float(rayleigh.stagnation_temperature_ratio(1.0, air)) == 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", (0.2, 0.5, 0.9, 1.5, 3.0))
def test_the_available_heat_takes_the_flow_exactly_to_sonic(gamma, mach):
    """43: add the whole available stagnation-temperature rise, land on M = 1."""
    air = gas(gamma)
    available = 1.0 / float(rayleigh.stagnation_temperature_ratio(mach, air))
    result = rayleigh.heat_addition(mach, available, air)
    assert result.value is not None
    assert result.value.downstream.mach == pytest.approx(1.0, abs=2e-5)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", (0.3, 0.7, 1.5, 3.0))
def test_heat_past_the_limit_does_not_cross_the_sonic_point(gamma, mach):
    air = gas(gamma)
    available = 1.0 / float(rayleigh.stagnation_temperature_ratio(mach, air))
    result = rayleigh.heat_addition(mach, available * 1.001, air)
    assert result.value is None
    assert any(d.code == "THERMALLY_CHOKED" for d in result.diagnostics)


# ===========================================================================
# 44 to 50 -- the nozzle against everything it composes
# ===========================================================================


P0, T0 = 1.0e6, 3000.0


def duct(area_ratio: float = 2.0, n: int = 81) -> AreaDistribution:
    return AreaDistribution.conical(throat_area=0.01, area_ratio=area_ratio, n=n)


def solved(back_ratio: float, gamma: float = 1.4, area_ratio: float = 2.0):
    return nozzle.solve(duct(area_ratio),
                        NozzleOperating(P0, back_ratio * P0, T0),
                        gas(gamma)).unwrap()


@pytest.mark.parametrize("gamma", GAMMAS)
def test_every_nozzle_station_satisfies_the_area_relation_it_claims(gamma):
    """44: with the *right* sonic area -- the throat upstream, A2* downstream."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    back = 0.5 * (critical.first_critical + critical.second_critical)
    solution = solved(back, gamma)
    throat_area = duct().throat_area
    downstream_area = throat_area * solution.shock.area_star_downstream_ratio

    for index, (area, mach) in enumerate(zip(solution.area, solution.mach)):
        reference = (downstream_area if index > solution.shock_index else throat_area)
        assert float(isentropic.area_ratio(mach, air)) == pytest.approx(
            area / reference, rel=1e-8)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_nozzle_mass_flow_is_the_mass_flow_module(gamma):
    """45: the link between nozzle, mass flow, PerfectGas and isentropic."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    expected = mass_flow.choked_mass_flow(air, duct().throat_area, P0, T0)
    for back in (critical.first_critical, 0.5 * critical.third_critical):
        solution = solved(back, gamma)
        assert solution.mass_flow == expected
        local = solution.density * solution.area * solution.velocity
        assert np.allclose(local, expected, rtol=1e-7)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_nozzle_conserves_stagnation_temperature_across_its_shock(gamma):
    """46: adiabatic, so T01 = T02 at the shock and everywhere else."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    solution = solved(0.5 * (critical.first_critical + critical.second_critical), gamma)
    local = solution.temperature + solution.velocity ** 2 / (2.0 * air.cp)
    assert np.allclose(local, T0, rtol=1e-10)
    index = solution.shock_index
    assert local[index] == pytest.approx(local[index + 1], rel=1e-12)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_nozzle_loses_stagnation_pressure_only_at_its_shock(gamma):
    """47: exactly one level without a shock, exactly two with one."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    shockless = solved(0.5 * critical.third_critical, gamma)
    assert len(np.unique(np.round(shockless.stagnation_pressure, 6))) == 1

    with_shock = solved(0.5 * (critical.first_critical + critical.second_critical),
                        gamma)
    levels = np.unique(np.round(with_shock.stagnation_pressure, 6))
    assert levels.size == 2
    assert np.all(np.diff(with_shock.stagnation_pressure) <= 1e-9)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_nozzle_shock_is_the_normal_shock_module(gamma):
    """48: every common field, bit-identical."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    solution = solved(0.5 * (critical.first_critical + critical.second_critical), gamma)
    independent = normal_shock.solve(solution.shock.mach_upstream, air)
    assert solution.shock.mach_downstream == independent.mach2
    assert solution.shock.pressure_ratio == independent.pressure_ratio
    assert solution.shock.stagnation_pressure_ratio == independent.stagnation_pressure_ratio
    assert solution.shock.area_star_downstream_ratio == independent.area_star_ratio


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_nozzle_thresholds_are_the_modules_they_come_from(gamma):
    """The three criticals, each rebuilt from its owning module."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    assert critical.first_critical == isentropic.pressure_ratio(
        critical.mach_exit_subsonic, air)
    assert critical.third_critical == isentropic.pressure_ratio(
        critical.mach_exit_supersonic, air)
    assert critical.second_critical == pytest.approx(
        critical.third_critical
        * float(normal_shock.pressure_ratio(critical.mach_exit_supersonic, air)),
        rel=1e-15)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_three_supersonic_regimes_share_one_internal_solution(gamma):
    """50: only the back pressure and the label differ."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    solutions = [solved(back, gamma) for back in (
        0.5 * (critical.second_critical + critical.third_critical),
        critical.third_critical,
        0.5 * critical.third_critical)]
    assert {s.regime for s in solutions} == {NozzleRegime.OVEREXPANDED,
                                             NozzleRegime.IDEALLY_EXPANDED,
                                             NozzleRegime.UNDEREXPANDED}
    reference = solutions[0]
    for other in solutions[1:]:
        assert np.array_equal(reference.mach, other.mach)
        assert np.array_equal(reference.pressure, other.pressure)
        assert np.array_equal(reference.stagnation_pressure, other.stagnation_pressure)
        assert reference.mass_flow == other.mass_flow


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_nozzle_regime_does_not_depend_on_the_station_count(gamma):
    """49: classification is a threshold decision, not a sampling artefact."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    back = 0.5 * (critical.first_critical + critical.second_critical)
    regimes, positions = set(), set()
    for n in (21, 81, 321):
        solution = nozzle.solve(duct(2.0, n), NozzleOperating(P0, back * P0, T0),
                                air).unwrap()
        regimes.add(solution.regime)
        positions.add(round(solution.shock.area_ratio_shock, 9))
    assert len(regimes) == 1
    assert len(positions) == 1


# ===========================================================================
# the sonic point, agreed across every module
# ===========================================================================


@pytest.mark.parametrize("gamma", GAMMAS)
def test_every_module_agrees_about_the_sonic_state(gamma):
    """One sonic point, ten modules. Nothing may disagree about M = 1."""
    air = gas(gamma)
    assert float(isentropic.area_ratio(1.0, air)) == pytest.approx(1.0, rel=1e-15)
    assert float(mass_flow.mass_flow_over_choked(1.0, air)) == pytest.approx(1.0,
                                                                            rel=1e-15)
    assert float(fanno.friction_parameter(1.0, air)) == 0.0
    assert float(fanno.temperature_ratio(1.0, air)) == pytest.approx(1.0, rel=1e-15)
    assert float(rayleigh.stagnation_temperature_ratio(1.0, air)) == 1.0
    assert float(rayleigh.temperature_ratio(1.0, air)) == pytest.approx(1.0, rel=1e-15)
    assert float(prandtl_meyer.nu(1.0, air)) == 0.0
    assert float(isentropic.mach_angle(1.0)) == pytest.approx(0.5 * np.pi, rel=1e-15)

    shock = normal_shock.solve(1.0, air)
    assert shock.mach2 == pytest.approx(1.0, rel=1e-14)
    assert shock.pressure_ratio == pytest.approx(1.0, rel=1e-14)
    assert shock.stagnation_pressure_ratio == pytest.approx(1.0, rel=1e-14)
    assert shock.sonic_limit


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_critical_pressure_ratio_is_the_isentropic_sonic_ratio(gamma):
    air = gas(gamma)
    assert mass_flow.critical_pressure_ratio(air) == pytest.approx(
        float(isentropic.pressure_ratio(1.0, air)), rel=1e-15)
    assert mass_flow.critical_temperature_ratio(air) == pytest.approx(
        float(isentropic.temperature_ratio(1.0, air)), rel=1e-15)
