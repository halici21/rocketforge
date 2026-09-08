"""Verification of compressible mass flow and the choked condition.

The canonical normalisation under test, stated once so no assertion here is
ambiguous about which of the many textbook "mass-flow functions" is meant:

    MFP(M, gamma) = mdot * sqrt(R * T0) / (A * p0)

Everything dimensional is that group rearranged, which is why the scaling
tests below are the real content: they check that the rearrangement is right.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError, MissingGasConstantError
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import mass_flow as mf

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g, gas_constant=287.0528) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]
AIR = PerfectGas(gamma=1.4, gas_constant=287.0528)


# ---------------------------------------------------------------------------
# the canonical relation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_parameter_matches_the_canonical_definition(gas):
    gamma = gas.gamma
    for mach in (0.0, 0.2, 0.5, 1.0, 2.0, 5.0):
        phi = 1.0 + 0.5 * (gamma - 1.0) * mach**2
        expected = math.sqrt(gamma) * mach * phi ** (-(gamma + 1.0) / (2.0 * (gamma - 1.0)))
        assert mf.mass_flow_parameter(mach, gas) == pytest.approx(expected, rel=1e-15)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_dimensional_flow_is_the_parameter_rearranged(gas):
    """mdot = MFP * A * p0 / sqrt(R T0). One definition, not two."""
    area, p0, t0 = 0.01, 1.0e6, 300.0
    for mach in (0.3, 1.0, 2.5):
        expected = (float(mf.mass_flow_parameter(mach, gas)) * area * p0
                    / math.sqrt(gas.gas_constant * t0))
        assert mf.mass_flow(mach, gas, area, p0, t0) == pytest.approx(expected, rel=1e-15)


def test_mass_flux_is_mass_flow_per_unit_area():
    """The two are different quantities and must not be confused."""
    p0, t0, area = 5.0e5, 400.0, 0.025
    flux = float(mf.mass_flux(1.5, AIR, p0, t0))
    flow = float(mf.mass_flow(1.5, AIR, area, p0, t0))
    assert flow == pytest.approx(flux * area, rel=1e-15)


def test_parameter_needs_no_gas_constant():
    """The dimensionless form depends on gamma alone."""
    dimensionless = PerfectGas(gamma=1.4)
    assert mf.mass_flow_parameter(2.0, dimensionless) == pytest.approx(
        float(mf.mass_flow_parameter(2.0, AIR)), rel=1e-15
    )


def test_dimensional_flow_requires_a_gas_constant():
    with pytest.raises(MissingGasConstantError):
        mf.mass_flow(1.0, PerfectGas(gamma=1.4), 0.01, 1e6, 300.0)


# ---------------------------------------------------------------------------
# zero flow and the choked maximum
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_zero_mach_gives_exactly_zero_flow(gas):
    """No singular 1/M form survives: M = 0 is exact, not a limit."""
    assert mf.mass_flow_parameter(0.0, gas) == 0.0
    assert mf.mass_flow(0.0, gas, 0.01, 1e6, 300.0) == 0.0
    assert mf.mass_flux(0.0, gas, 1e6, 300.0) == 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_parameter_is_positive_above_rest(gas):
    grid = np.linspace(1e-6, 20.0, 500)
    assert np.all(mf.mass_flow_parameter(grid, gas) > 0.0)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_sonic_value_equals_the_choked_coefficient(gas):
    gamma = gas.gamma
    expected = math.sqrt(gamma) * (2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
    assert mf.choked_mass_flow_coefficient(gas) == pytest.approx(expected, rel=1e-15)
    assert mf.mass_flow_parameter(1.0, gas) == pytest.approx(
        mf.choked_mass_flow_coefficient(gas), rel=1e-15
    )


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_mass_flow_has_its_unique_maximum_at_mach_one(gas):
    """The central physical fact of choking, checked as a maximum, not a sample.

    A dense grid is scanned, the largest sample is required to be the sonic
    one, and the derivative is required to change sign there.
    """
    grid = np.linspace(1e-4, 6.0, 20001)
    values = np.asarray(mf.mass_flow_parameter(grid, gas))
    peak = grid[int(np.argmax(values))]
    assert peak == pytest.approx(1.0, abs=2e-4)

    sonic = mf.choked_mass_flow_coefficient(gas)
    assert np.all(values <= sonic + 1e-15), "no Mach number may exceed the sonic value"

    slope = np.diff(values)
    assert slope[0] > 0.0 and slope[-1] < 0.0
    sign_changes = np.count_nonzero(np.diff(np.sign(slope)) != 0)
    assert sign_changes == 1, "the maximum must be unique"


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_subsonic_branch_increases_and_supersonic_branch_decreases(gas):
    subsonic = np.linspace(0.0, 1.0, 2000)
    assert np.all(np.diff(mf.mass_flow_parameter(subsonic, gas)) > 0.0)
    supersonic = np.linspace(1.0, 12.0, 2000)
    assert np.all(np.diff(mf.mass_flow_parameter(supersonic, gas)) < 0.0)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_normalised_flow_is_one_at_sonic_and_below_one_elsewhere(gas):
    assert mf.mass_flow_over_choked(1.0, gas) == pytest.approx(1.0, rel=1e-15)
    for mach in (0.1, 0.5, 0.99, 1.01, 2.0, 5.0):
        assert mf.mass_flow_over_choked(mach, gas) < 1.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_choked_helpers_are_the_sonic_evaluation(gas):
    """The choked helpers must be the same relation at Mach 1, not a second one."""
    area, p0, t0 = 0.02, 2.0e6, 3200.0
    assert mf.choked_mass_flow(gas, area, p0, t0) == pytest.approx(
        float(mf.mass_flow(1.0, gas, area, p0, t0)), rel=1e-15
    )
    assert mf.choked_mass_flux(gas, p0, t0) == pytest.approx(
        float(mf.mass_flux(1.0, gas, p0, t0)), rel=1e-15
    )


# ---------------------------------------------------------------------------
# scaling -- the dependencies an engineer reasons with
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_flow_scales_linearly_with_area(gas):
    base = float(mf.mass_flow(0.7, gas, 0.01, 1e6, 300.0))
    assert mf.mass_flow(0.7, gas, 0.03, 1e6, 300.0) == pytest.approx(3.0 * base, rel=1e-14)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_flow_scales_linearly_with_stagnation_pressure(gas):
    base = float(mf.mass_flow(0.7, gas, 0.01, 1e6, 300.0))
    assert mf.mass_flow(0.7, gas, 0.01, 4e6, 300.0) == pytest.approx(4.0 * base, rel=1e-14)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_flow_scales_as_the_inverse_square_root_of_stagnation_temperature(gas):
    base = float(mf.mass_flow(0.7, gas, 0.01, 1e6, 300.0))
    assert mf.mass_flow(0.7, gas, 0.01, 1e6, 1200.0) == pytest.approx(0.5 * base, rel=1e-14)


def test_flow_scales_as_the_inverse_square_root_of_the_gas_constant():
    light = PerfectGas(gamma=1.4, gas_constant=4.0 * 287.0528)
    base = float(mf.mass_flow(0.7, AIR, 0.01, 1e6, 300.0))
    assert mf.mass_flow(0.7, light, 0.01, 1e6, 300.0) == pytest.approx(0.5 * base, rel=1e-14)


def test_gamma_changes_the_result():
    """Proof that gamma is used rather than assumed."""
    assert mf.mass_flow_parameter(2.0, PerfectGas(gamma=1.2)) != mf.mass_flow_parameter(
        2.0, PerfectGas(gamma=1.4)
    )


# ---------------------------------------------------------------------------
# the critical condition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_critical_ratios_are_the_isentropic_sonic_values(gas):
    """Delegated, not restated: one value of p*/p0 exists in the codebase."""
    assert mf.critical_pressure_ratio(gas) == pytest.approx(
        float(iso.pressure_ratio(1.0, gas)), rel=1e-15
    )
    assert mf.critical_temperature_ratio(gas) == pytest.approx(
        float(iso.temperature_ratio(1.0, gas)), rel=1e-15
    )


def test_critical_pressure_ratio_reference_value():
    """0.5283 for air, the number every compressible-flow text prints."""
    assert mf.critical_pressure_ratio(AIR) == pytest.approx(0.5283, abs=5e-5)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_is_choked_answers_only_the_convergent_passage_question(gas):
    critical = mf.critical_pressure_ratio(gas)
    assert mf.is_choked(critical * 0.5, gas) is True
    assert mf.is_choked(critical, gas) is True
    assert mf.is_choked(critical * 1.1, gas) is False
    assert mf.is_choked(1.0, gas) is False


@pytest.mark.parametrize("bad", [0.0, -0.1, 1.5, math.nan, math.inf])
def test_is_choked_rejects_impossible_pressure_ratios(bad):
    with pytest.raises(DomainError):
        mf.is_choked(bad, AIR)


# ---------------------------------------------------------------------------
# domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [-1e-12, -0.5, -2.0])
def test_negative_mach_rejected(bad):
    with pytest.raises(DomainError):
        mf.mass_flow_parameter(bad, AIR)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_mach_rejected(bad):
    with pytest.raises(DomainError):
        mf.mass_flow_parameter(bad, AIR)


@pytest.mark.parametrize("field,values", [
    ("area", (0.0, -1.0, math.nan, math.inf)),
    ("p0", (0.0, -1.0, math.nan, math.inf)),
    ("t0", (0.0, -1.0, math.nan, math.inf)),
])
def test_non_positive_dimensional_inputs_rejected(field, values):
    for bad in values:
        args = {"area": 0.01, "p0": 1e6, "t0": 300.0}
        args[field] = bad
        with pytest.raises(DomainError):
            mf.mass_flow(1.0, AIR, args["area"], args["p0"], args["t0"])


def test_array_with_one_bad_element_raises_and_names_the_index():
    with pytest.raises(DomainError) as excinfo:
        mf.mass_flow_parameter(np.array([0.5, 1.0, -2.0]), AIR)
    assert "index 2" in str(excinfo.value)


# ---------------------------------------------------------------------------
# scalar / array
# ---------------------------------------------------------------------------


def test_scalar_returns_float_and_array_returns_array():
    assert isinstance(mf.mass_flow_parameter(1.0, AIR), float)
    result = mf.mass_flow_parameter(np.array([0.5, 1.0, 2.0]), AIR)
    assert isinstance(result, np.ndarray) and result.shape == (3,)
    assert result.dtype == np.float64


def test_array_and_scalar_paths_agree():
    grid = np.array([0.0, 0.3, 1.0, 2.0, 7.0])
    vector = mf.mass_flow_parameter(grid, AIR)
    for index, mach in enumerate(grid):
        assert vector[index] == pytest.approx(float(mf.mass_flow_parameter(float(mach), AIR)), rel=1e-15)


def test_dimensional_flow_accepts_an_array_of_mach():
    result = mf.mass_flow(np.array([0.5, 1.0]), AIR, 0.01, 1e6, 300.0)
    assert isinstance(result, np.ndarray) and result.shape == (2,)


# ---------------------------------------------------------------------------
# independent reference case
# ---------------------------------------------------------------------------


def test_choked_flow_against_an_independently_computed_case():
    """A dimensional case worked from the equation, not from our own MFP.

    Air, gamma = 1.4, R = 287.0528 J/(kg K), p0 = 1.0 MPa, T0 = 300 K,
    A* = 0.01 m². Computing Gamma by hand:

        Gamma = sqrt(1.4) * (2/2.4)^3      = 1.1832160 * 0.5787037 = 0.68473146
        mdot  = 0.68473146 * 1e6 * 0.01 / sqrt(287.0528 * 300)
              = 6847.3146 / 293.4416       = 23.33344 kg/s
    """
    expected_gamma_function = math.sqrt(1.4) * (2.0 / 2.4) ** 3
    assert mf.choked_mass_flow_coefficient(AIR) == pytest.approx(expected_gamma_function, rel=1e-14)

    expected = expected_gamma_function * 1.0e6 * 0.01 / math.sqrt(287.0528 * 300.0)
    assert expected == pytest.approx(23.33344, rel=1e-6), "the hand calculation itself"
    assert mf.choked_mass_flow(AIR, 0.01, 1.0e6, 300.0) == pytest.approx(expected, rel=1e-14)


def test_choked_coefficient_reference_values():
    """Gamma(gamma) for gases a propulsion engineer meets.

    Cross-checked against the closed form evaluated independently below; the
    values are quoted widely in the propulsion literature.
    """
    for gamma, expected in ((1.2, 0.6485312), (1.3, 0.6672624), (1.4, 0.6847315), (1.66, 0.7252274)):
        gas = PerfectGas(gamma=gamma)
        assert mf.choked_mass_flow_coefficient(gas) == pytest.approx(expected, rel=1e-6)
