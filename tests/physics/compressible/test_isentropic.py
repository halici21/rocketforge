"""Verification of the forward isentropic relations.

Covers the ratios, their sonic-reference forms, the Mach angle, the grouped
record, the domain rules of ``04`` section 7, and the physical invariants of
``05`` section 9. Reference values against printed tables live in
``test_reference_cases.py``.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]

# A deterministic Mach grid spanning stagnation, subsonic, sonic, supersonic
# and hypersonic, with the near-sonic region resolved on both sides.
MACH_GRID = np.array([
    0.0, 1e-8, 1e-6, 1e-4, 0.01, 0.1, 0.3, 0.5, 0.7, 0.9,
    0.99, 0.999, 0.9999, 1.0, 1.0001, 1.001, 1.01,
    1.1, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0,
])

STATIC_TO_STAGNATION = (
    ("temperature_ratio", iso.temperature_ratio),
    ("pressure_ratio", iso.pressure_ratio),
    ("density_ratio", iso.density_ratio),
)


# ---------------------------------------------------------------------------
# the defining relations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_temperature_ratio_matches_the_equation(gas):
    for mach in MACH_GRID:
        phi = 1.0 + 0.5 * (gas.gamma - 1.0) * mach**2
        assert iso.temperature_ratio(mach, gas) == pytest.approx(1.0 / phi, rel=1e-15)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_pressure_ratio_is_the_temperature_ratio_to_the_gamma_power(gas):
    """p/p0 = (T/T0)^(gamma/(gamma-1)) -- the isentropic link between them."""
    exponent = gas.gamma / (gas.gamma - 1.0)
    for mach in MACH_GRID:
        expected = float(iso.temperature_ratio(mach, gas)) ** exponent
        assert iso.pressure_ratio(mach, gas) == pytest.approx(expected, rel=1e-13)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_density_ratio_is_the_temperature_ratio_to_the_one_over_gamma_minus_one_power(gas):
    exponent = 1.0 / (gas.gamma - 1.0)
    for mach in MACH_GRID:
        expected = float(iso.temperature_ratio(mach, gas)) ** exponent
        assert iso.density_ratio(mach, gas) == pytest.approx(expected, rel=1e-13)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_ideal_gas_law_holds_between_the_ratios(gas):
    """p/p0 = (rho/rho0)(T/T0): the equation of state, satisfied by the ratios."""
    for mach in MACH_GRID:
        p = float(iso.pressure_ratio(mach, gas))
        rho = float(iso.density_ratio(mach, gas))
        t = float(iso.temperature_ratio(mach, gas))
        assert p == pytest.approx(rho * t, rel=1e-13)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_area_ratio_matches_the_equation(gas):
    gamma = gas.gamma
    exponent = (gamma + 1.0) / (2.0 * (gamma - 1.0))
    for mach in MACH_GRID[MACH_GRID > 0]:
        phi = 1.0 + 0.5 * (gamma - 1.0) * mach**2
        expected = (1.0 / mach) * ((2.0 / (gamma + 1.0)) * phi) ** exponent
        assert iso.area_ratio(mach, gas) == pytest.approx(expected, rel=1e-13)


# ---------------------------------------------------------------------------
# ratio orientation -- the classic sign-of-the-fraction bug
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("name,relation", STATIC_TO_STAGNATION)
def test_static_over_stagnation_ratios_never_exceed_one(gas, name, relation):
    """Static properties cannot exceed their stagnation values.

    If any of these came back above 1 the relation would be inverted -- the
    single easiest error to make and the hardest to see in a plot.
    """
    values = relation(MACH_GRID, gas)
    assert np.all(values > 0.0), f"{name} must stay positive"
    assert np.all(values <= 1.0), f"{name} is oriented static/stagnation and cannot exceed 1"


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_starred_ratios_are_above_one_subsonic_and_below_one_supersonic(gas):
    """T/T* > 1 below sonic and < 1 above it, so the orientation is unambiguous."""
    assert iso.temperature_ratio_star(0.5, gas) > 1.0
    assert iso.temperature_ratio_star(2.0, gas) < 1.0
    assert iso.pressure_ratio_star(0.5, gas) > 1.0
    assert iso.pressure_ratio_star(2.0, gas) < 1.0
    assert iso.density_ratio_star(0.5, gas) > 1.0
    assert iso.density_ratio_star(2.0, gas) < 1.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_starred_ratios_are_the_stagnation_ratios_normalised_at_sonic(gas):
    """X/X* = (X/X0) / (X*/X0), which is what "starred" means."""
    for mach in MACH_GRID:
        t_sonic = float(iso.temperature_ratio(1.0, gas))
        p_sonic = float(iso.pressure_ratio(1.0, gas))
        rho_sonic = float(iso.density_ratio(1.0, gas))
        assert iso.temperature_ratio_star(mach, gas) == pytest.approx(
            float(iso.temperature_ratio(mach, gas)) / t_sonic, rel=1e-13
        )
        assert iso.pressure_ratio_star(mach, gas) == pytest.approx(
            float(iso.pressure_ratio(mach, gas)) / p_sonic, rel=1e-13
        )
        assert iso.density_ratio_star(mach, gas) == pytest.approx(
            float(iso.density_ratio(mach, gas)) / rho_sonic, rel=1e-13
        )


# ---------------------------------------------------------------------------
# monotonicity and the area minimum
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("name,relation", STATIC_TO_STAGNATION)
def test_static_ratios_decrease_with_mach(gas, name, relation):
    grid = np.linspace(0.0, 20.0, 4001)
    values = relation(grid, gas)
    assert np.all(np.diff(values) < 0.0), f"{name} must fall monotonically with Mach"


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_area_ratio_is_never_below_one(gas):
    grid = np.concatenate([np.linspace(1e-4, 1.0, 2000), np.linspace(1.0, 20.0, 2000)])
    values = iso.area_ratio(grid, gas)
    assert np.all(values >= 1.0 - 1e-15)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_area_ratio_minimum_is_exactly_one_at_sonic(gas):
    """Not "the smallest sample on a grid": exactly 1, exactly at M = 1."""
    assert iso.area_ratio(1.0, gas) == pytest.approx(1.0, rel=1e-15)
    # Offsets large enough that the excess is representable -- see the
    # conditioning test below for why 1e-8 is not one of them.
    for offset in (1e-3, 1e-4, 1e-6):
        assert iso.area_ratio(1.0 - offset, gas) > 1.0
        assert iso.area_ratio(1.0 + offset, gas) > 1.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_area_ratio_excess_over_unity_is_quadratic_near_sonic(gas):
    """A/A* - 1 ~ [2/(gamma+1)] (M-1)^2, the coefficient derived in 04 section 4.

    This is the reason the inverse needs a sonic tolerance rather than a
    tighter one: the relation is quadratically flat at its minimum, so half the
    available precision is lost inverting it there.
    """
    coefficient = 2.0 / (gas.gamma + 1.0)
    for offset in (1e-2, 1e-3, 1e-4):
        excess = float(iso.area_ratio(1.0 + offset, gas)) - 1.0
        assert excess / offset**2 == pytest.approx(coefficient, rel=2e-2)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_area_ratio_cannot_resolve_offsets_below_the_float64_floor(gas):
    """At |M - 1| = 1e-8 the excess is ~1e-16 and is not representable.

    Asserting a strict inequality there would be asserting something double
    precision cannot deliver. The excess is 2/(gamma+1) * 1e-16, at or below
    one unit in the last place of 1.0, so the computed area ratio is 1.0 to
    within a couple of ulps -- which is exactly the limit quantified in 04
    section 4 and the justification for area_sonic_tol.
    """
    predicted_excess = 2.0 / (gas.gamma + 1.0) * 1e-16
    assert predicted_excess < 4.0 * np.finfo(float).eps
    for offset in (1e-8, -1e-8):
        assert iso.area_ratio(1.0 + offset, gas) == pytest.approx(1.0, abs=4.0 * np.finfo(float).eps)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_area_ratio_subsonic_branch_is_monotone_decreasing(gas):
    """Required for the inverse bracket to contain exactly one root."""
    grid = np.linspace(1e-3, 1.0 - 1e-9, 3000)
    values = iso.area_ratio(grid, gas)
    assert np.all(np.diff(values) < 0.0)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_area_ratio_supersonic_branch_is_monotone_increasing(gas):
    grid = np.linspace(1.0 + 1e-9, 25.0, 3000)
    values = iso.area_ratio(grid, gas)
    assert np.all(np.diff(values) > 0.0)


# ---------------------------------------------------------------------------
# limits
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_zero_mach_gives_static_equal_to_stagnation(gas):
    assert iso.temperature_ratio(0.0, gas) == 1.0
    assert iso.pressure_ratio(0.0, gas) == 1.0
    assert iso.density_ratio(0.0, gas) == 1.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_sonic_values_match_the_closed_form(gas):
    gamma = gas.gamma
    assert iso.temperature_ratio(1.0, gas) == pytest.approx(2.0 / (gamma + 1.0), rel=1e-15)
    assert iso.pressure_ratio(1.0, gas) == pytest.approx(
        (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0)), rel=1e-14
    )
    assert iso.density_ratio(1.0, gas) == pytest.approx(
        (2.0 / (gamma + 1.0)) ** (1.0 / (gamma - 1.0)), rel=1e-14
    )
    assert iso.area_ratio(1.0, gas) == pytest.approx(1.0, rel=1e-15)
    assert iso.temperature_ratio_star(1.0, gas) == pytest.approx(1.0, rel=1e-15)
    assert iso.pressure_ratio_star(1.0, gas) == pytest.approx(1.0, rel=1e-15)
    assert iso.density_ratio_star(1.0, gas) == pytest.approx(1.0, rel=1e-15)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach", [5.0, 10.0, 20.0, 50.0, 100.0])
def test_high_mach_values_stay_finite(gas, mach):
    """Finite and positive, never overflowing to inf or collapsing to zero."""
    for _, relation in STATIC_TO_STAGNATION:
        value = float(relation(mach, gas))
        assert math.isfinite(value) and value > 0.0
    assert math.isfinite(float(iso.area_ratio(mach, gas)))


def test_gamma_at_the_lower_limit_stays_finite_at_high_mach():
    """gamma = 1.001 drives the exponents past 1000; the result must still be finite.

    This is the case ``03`` section 2.2 uses to justify the hard lower limit,
    so it is the case that has to be checked.
    """
    gas = PerfectGas(gamma=1.001)
    for mach in (1.0, 5.0, 10.0):
        assert math.isfinite(float(iso.pressure_ratio(mach, gas)))
        assert math.isfinite(float(iso.density_ratio(mach, gas)))
        assert math.isfinite(float(iso.area_ratio(mach, gas)))
    assert float(iso.pressure_ratio(5.0, gas)) > 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_very_small_mach_approaches_the_stagnation_limit(gas):
    for mach in (1e-8, 1e-6, 1e-4):
        assert iso.temperature_ratio(mach, gas) == pytest.approx(1.0, abs=1e-6)
        assert iso.pressure_ratio(mach, gas) == pytest.approx(1.0, abs=1e-6)
        assert float(iso.area_ratio(mach, gas)) > 1.0


# ---------------------------------------------------------------------------
# Mach angle
# ---------------------------------------------------------------------------


def test_mach_angle_at_sonic_is_a_right_angle():
    assert iso.mach_angle(1.0) == pytest.approx(math.pi / 2, rel=1e-15)


@pytest.mark.parametrize("mach,degrees", [(1.0, 90.0), (2.0, 30.0), (3.0, 19.4712206), (5.0, 11.5369590)])
def test_mach_angle_reference_values(mach, degrees):
    """mu = arcsin(1/M); at M = 2 it is exactly 30 degrees."""
    assert math.degrees(float(iso.mach_angle(mach))) == pytest.approx(degrees, abs=1e-6)


def test_mach_angle_decreases_with_mach():
    grid = np.linspace(1.0, 30.0, 2000)
    assert np.all(np.diff(iso.mach_angle(grid)) < 0.0)


@pytest.mark.parametrize("bad", [0.0, 0.5, 0.999])
def test_mach_angle_rejects_subsonic(bad):
    with pytest.raises(DomainError):
        iso.mach_angle(bad)


def test_mach_angle_needs_no_gas_model():
    """It is geometry, not thermodynamics: the signature takes Mach alone."""
    assert iso.mach_angle(2.0) == pytest.approx(math.asin(0.5), rel=1e-15)


# ---------------------------------------------------------------------------
# grouped record
# ---------------------------------------------------------------------------


def test_ratios_from_mach_agrees_with_the_individual_relations():
    gas = PerfectGas(gamma=1.3)
    record = iso.ratios_from_mach(2.5, gas)
    assert record.mach == 2.5
    assert record.temperature_ratio == pytest.approx(float(iso.temperature_ratio(2.5, gas)), rel=1e-15)
    assert record.pressure_ratio == pytest.approx(float(iso.pressure_ratio(2.5, gas)), rel=1e-15)
    assert record.density_ratio == pytest.approx(float(iso.density_ratio(2.5, gas)), rel=1e-15)
    assert record.area_ratio == pytest.approx(float(iso.area_ratio(2.5, gas)), rel=1e-15)
    assert record.mach_angle == pytest.approx(float(iso.mach_angle(2.5)), rel=1e-15)


def test_ratios_from_mach_omits_what_does_not_apply():
    """Absent, not fabricated: no area ratio at rest, no Mach wave below sonic."""
    gas = PerfectGas(gamma=1.4)
    at_rest = iso.ratios_from_mach(0.0, gas)
    assert at_rest.area_ratio is None
    assert at_rest.mach_angle is None

    subsonic = iso.ratios_from_mach(0.5, gas)
    assert subsonic.area_ratio is not None
    assert subsonic.mach_angle is None

    supersonic = iso.ratios_from_mach(2.0, gas)
    assert supersonic.mach_angle is not None


def test_ratios_from_mach_leaves_prandtl_meyer_unset():
    """The field exists because the record's shape is fixed; the relation does not."""
    assert iso.ratios_from_mach(2.0, PerfectGas(gamma=1.4)).prandtl_meyer_angle is None


def test_ratios_from_mach_is_immutable():
    record = iso.ratios_from_mach(2.0, PerfectGas(gamma=1.4))
    with pytest.raises(Exception):
        record.mach = 3.0  # type: ignore[misc]


def test_ratios_from_mach_rejects_an_array():
    with pytest.raises(DomainError):
        iso.ratios_from_mach(np.array([1.0, 2.0]), PerfectGas(gamma=1.4))


# ---------------------------------------------------------------------------
# domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relation", [
    iso.temperature_ratio, iso.pressure_ratio, iso.density_ratio,
    iso.area_ratio, iso.temperature_ratio_star,
    iso.pressure_ratio_star, iso.density_ratio_star,
])
@pytest.mark.parametrize("bad", [-1e-12, -0.5, -2.0])
def test_negative_mach_rejected(relation, bad):
    """Never abs(), never clamped: a negative Mach is a caller bug."""
    with pytest.raises(DomainError):
        relation(bad, PerfectGas(gamma=1.4))


@pytest.mark.parametrize("relation", [
    iso.temperature_ratio, iso.pressure_ratio, iso.density_ratio,
    iso.area_ratio, iso.temperature_ratio_star,
])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_mach_rejected(relation, bad):
    with pytest.raises(DomainError):
        relation(bad, PerfectGas(gamma=1.4))


def test_area_ratio_rejects_zero_mach():
    """A/A* is unbounded at rest; returning inf would leak into a plot axis."""
    with pytest.raises(DomainError):
        iso.area_ratio(0.0, PerfectGas(gamma=1.4))


def test_array_with_one_bad_element_raises_and_names_the_index():
    with pytest.raises(DomainError) as excinfo:
        iso.pressure_ratio(np.array([0.5, 1.0, -2.0, 3.0]), PerfectGas(gamma=1.4))
    assert "index 2" in str(excinfo.value)


# ---------------------------------------------------------------------------
# scalar / array policy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relation", [
    iso.temperature_ratio, iso.pressure_ratio, iso.density_ratio, iso.area_ratio,
])
def test_scalar_input_returns_a_float(relation):
    assert isinstance(relation(2.0, PerfectGas(gamma=1.4)), float)


@pytest.mark.parametrize("relation", [
    iso.temperature_ratio, iso.pressure_ratio, iso.density_ratio, iso.area_ratio,
])
def test_array_input_returns_an_array_of_the_same_shape(relation):
    gas = PerfectGas(gamma=1.4)
    grid = np.array([[1.0, 2.0], [3.0, 4.0]])
    result = relation(grid, gas)
    assert isinstance(result, np.ndarray)
    assert result.shape == grid.shape


@pytest.mark.parametrize("relation", [iso.temperature_ratio, iso.pressure_ratio])
def test_list_input_is_accepted(relation):
    result = relation([0.5, 1.0, 2.0], PerfectGas(gamma=1.4))
    assert isinstance(result, np.ndarray) and result.shape == (3,)


def test_scalar_and_array_paths_agree_elementwise():
    gas = PerfectGas(gamma=1.4)
    vector = iso.pressure_ratio(MACH_GRID, gas)
    for index, mach in enumerate(MACH_GRID):
        assert vector[index] == pytest.approx(float(iso.pressure_ratio(float(mach), gas)), rel=1e-15)


def test_integer_input_is_promoted_to_float64():
    """float64 is the specified baseline; a narrower dtype would silently lose digits."""
    gas = PerfectGas(gamma=1.4)
    result = iso.pressure_ratio(np.array([1, 2, 3], dtype=np.int64), gas)
    assert result.dtype == np.float64


def test_float32_input_is_promoted_to_float64():
    gas = PerfectGas(gamma=1.4)
    result = iso.pressure_ratio(np.array([0.5, 2.0], dtype=np.float32), gas)
    assert result.dtype == np.float64


# ---------------------------------------------------------------------------
# no hidden gas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relation", [
    iso.temperature_ratio, iso.pressure_ratio, iso.density_ratio, iso.area_ratio,
])
def test_every_relation_requires_an_explicit_gas(relation):
    """Nothing defaults to air. Rocket exhaust is not gamma = 1.4."""
    with pytest.raises(TypeError):
        relation(2.0)  # type: ignore[call-arg]


def test_results_differ_between_gases():
    """Proof that gamma is actually used rather than assumed."""
    light = PerfectGas(gamma=1.66)
    heavy = PerfectGas(gamma=1.2)
    assert iso.pressure_ratio(2.0, light) != iso.pressure_ratio(2.0, heavy)
    assert iso.area_ratio(2.0, light) != iso.area_ratio(2.0, heavy)
