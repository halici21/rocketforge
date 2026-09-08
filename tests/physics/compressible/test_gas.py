"""Verification of the calorically perfect gas model.

Contracts under test come from
``docs/engineering/03_compressible_flow_specification.md`` section 2 (the gamma
and R domains, the advisory band) and ``02`` section 1.2 (immutability, the
optional gas constant, the derived specific heats).
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT
from rocketforge.core.errors import (
    DomainError,
    GasModelError,
    InvalidGammaError,
    InvalidGasConstantError,
    MissingGasConstantError,
)
from rocketforge.core.result import Severity
from rocketforge.core.tolerances import DEFAULT_TOLERANCES
from rocketforge.physics.compressible import PerfectGas, speed_of_sound

GAMMA_MIN = DEFAULT_TOLERANCES.gamma_min
GAMMA_MAX = DEFAULT_TOLERANCES.gamma_max
ADVISORY_MIN = DEFAULT_TOLERANCES.gamma_advisory_min
ADVISORY_MAX = DEFAULT_TOLERANCES.gamma_advisory_max

# Gases spanning the range RocketForge actually cares about: air, a
# diatomic-ish rocket exhaust, a heavy combustion product, and a monatomic gas.
GAMMAS = (1.2, 1.3, 1.4, 1.66)


# ---------------------------------------------------------------------------
# construction
# ---------------------------------------------------------------------------


def test_constructs_with_gamma_and_gas_constant():
    gas = PerfectGas(gamma=1.4, gas_constant=287.0528)
    assert gas.gamma == 1.4
    assert gas.gas_constant == 287.0528
    assert gas.is_dimensional


def test_constructs_without_a_gas_constant():
    """The dimensionless half of the module needs only gamma."""
    gas = PerfectGas(gamma=1.22)
    assert gas.gas_constant is None
    assert gas.is_dimensional is False


def test_air_named_constructor():
    air = PerfectGas.air()
    assert air.gamma == 1.4
    assert air.gas_constant == pytest.approx(287.0528, abs=1e-4)


def test_from_molar_mass():
    """R = R_universal / M, with M in kg/mol."""
    gas = PerfectGas.from_molar_mass(gamma=1.4, molar_mass=28.9644e-3)
    assert gas.gas_constant == pytest.approx(UNIVERSAL_GAS_CONSTANT / 28.9644e-3, rel=1e-15)
    # Sanity: this must land near the air value from the standard atmosphere.
    assert gas.gas_constant == pytest.approx(287.06, abs=0.05)


@pytest.mark.parametrize("bad", [0.0, -1.0, math.nan, math.inf, -math.inf, "28"])
def test_from_molar_mass_rejects_bad_molar_mass(bad):
    with pytest.raises(InvalidGasConstantError):
        PerfectGas.from_molar_mass(gamma=1.4, molar_mass=bad)


def test_is_immutable():
    """A gas model is a fixed description; changing one means making another."""
    gas = PerfectGas(gamma=1.4, gas_constant=287.0)
    with pytest.raises(Exception):
        gas.gamma = 1.3  # type: ignore[misc]
    with pytest.raises(Exception):
        gas.gas_constant = 300.0  # type: ignore[misc]


def test_replace_makes_a_new_gas():
    gas = PerfectGas(gamma=1.4, gas_constant=287.0)
    other = dataclasses.replace(gas, gamma=1.2)
    assert other.gamma == 1.2
    assert gas.gamma == 1.4


def test_equality_is_by_value():
    assert PerfectGas(gamma=1.4, gas_constant=287.0) == PerfectGas(gamma=1.4, gas_constant=287.0)
    assert PerfectGas(gamma=1.4) != PerfectGas(gamma=1.4, gas_constant=287.0)


# ---------------------------------------------------------------------------
# gamma domain
# ---------------------------------------------------------------------------


def test_gamma_at_the_lower_hard_limit_is_accepted():
    gas = PerfectGas(gamma=GAMMA_MIN)
    assert gas.gamma == GAMMA_MIN


def test_gamma_at_the_upper_hard_limit_is_accepted():
    gas = PerfectGas(gamma=GAMMA_MAX)
    assert gas.gamma == GAMMA_MAX


@pytest.mark.parametrize("bad", [1.0, 0.9, 0.0, -1.4, 1.0009, GAMMA_MIN - 1e-6])
def test_gamma_below_the_hard_limit_rejected(bad):
    with pytest.raises(InvalidGammaError):
        PerfectGas(gamma=bad)


@pytest.mark.parametrize("bad", [GAMMA_MAX + 1e-6, 3.5, 10.0])
def test_gamma_above_the_hard_limit_rejected(bad):
    with pytest.raises(InvalidGammaError):
        PerfectGas(gamma=bad)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_gamma_rejected(bad):
    with pytest.raises(InvalidGammaError):
        PerfectGas(gamma=bad)


@pytest.mark.parametrize("bad", ["1.4", None, [1.4], True])
def test_non_numeric_gamma_rejected(bad):
    with pytest.raises(InvalidGammaError):
        PerfectGas(gamma=bad)


def test_gamma_error_explains_the_limit():
    with pytest.raises(InvalidGammaError) as excinfo:
        PerfectGas(gamma=1.0)
    message = str(excinfo.value)
    assert str(GAMMA_MIN) in message and str(GAMMA_MAX) in message


# ---------------------------------------------------------------------------
# gamma advisory band -- a warning, never an error
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", [ADVISORY_MIN, 1.2, 1.4, 1.66, ADVISORY_MAX])
def test_gamma_inside_the_advisory_band_produces_no_diagnostic(gamma):
    assert PerfectGas(gamma=gamma).diagnostics == ()


@pytest.mark.parametrize("gamma", [GAMMA_MIN, 1.02, ADVISORY_MIN - 1e-9, ADVISORY_MAX + 1e-9, 2.5, GAMMA_MAX])
def test_gamma_outside_the_advisory_band_warns_but_still_computes(gamma):
    """Mathematically valid, physically stretched: a warning, not a refusal."""
    gas = PerfectGas(gamma=gamma)
    assert gas.gamma == gamma, "the gas must still be constructible"
    diagnostics = gas.diagnostics
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "EXTRAPOLATED_GAMMA"
    assert diagnostics[0].severity is Severity.WARNING
    assert diagnostics[0].field == "gamma"
    assert diagnostics[0].detail["gamma"] == gamma


def test_advisory_band_sits_inside_the_hard_limits():
    assert GAMMA_MIN < ADVISORY_MIN < ADVISORY_MAX < GAMMA_MAX


def test_advisory_is_data_not_a_python_warning(recwarn):
    """Diagnostics are machine-readable records; nothing is printed or warned."""
    gas = PerfectGas(gamma=2.5)
    assert gas.diagnostics
    assert len(recwarn) == 0


# ---------------------------------------------------------------------------
# gas constant domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", [1e-6, 1.0, 287.0528, 4124.2, 1e6])
def test_positive_gas_constant_accepted(value):
    assert PerfectGas(gamma=1.4, gas_constant=value).gas_constant == value


@pytest.mark.parametrize("bad", [0.0, -1.0, -287.0])
def test_non_positive_gas_constant_rejected(bad):
    with pytest.raises(InvalidGasConstantError):
        PerfectGas(gamma=1.4, gas_constant=bad)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_gas_constant_rejected(bad):
    with pytest.raises(InvalidGasConstantError):
        PerfectGas(gamma=1.4, gas_constant=bad)


@pytest.mark.parametrize("bad", ["287", [287.0], True])
def test_non_numeric_gas_constant_rejected(bad):
    with pytest.raises(InvalidGasConstantError):
        PerfectGas(gamma=1.4, gas_constant=bad)


def test_gas_model_errors_share_a_base():
    assert issubclass(InvalidGammaError, GasModelError)
    assert issubclass(InvalidGasConstantError, GasModelError)
    assert issubclass(MissingGasConstantError, GasModelError)


# ---------------------------------------------------------------------------
# specific heats
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("r", [287.0528, 320.0, 2077.0])
def test_cp_over_cv_equals_gamma(gamma, r):
    """The defining identity of the model, for every gas it accepts."""
    gas = PerfectGas(gamma=gamma, gas_constant=r)
    assert gas.cp / gas.cv == pytest.approx(gamma, rel=1e-15)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("r", [287.0528, 320.0, 2077.0])
def test_cp_minus_cv_equals_the_gas_constant(gamma, r):
    """Mayer's relation. Holds exactly because cp and cv are derived, not stored."""
    gas = PerfectGas(gamma=gamma, gas_constant=r)
    assert gas.cp - gas.cv == pytest.approx(r, rel=1e-12)


def test_cp_reference_value_for_air():
    """cp of dry air, about 1005 J/(kg K), is a number an engineer recognises."""
    air = PerfectGas.air()
    assert air.cp == pytest.approx(1004.68, abs=0.01)
    assert air.cv == pytest.approx(717.63, abs=0.01)


def test_cp_requires_a_gas_constant():
    gas = PerfectGas(gamma=1.4)
    with pytest.raises(MissingGasConstantError) as excinfo:
        _ = gas.cp
    assert "cp" in str(excinfo.value)


def test_cv_requires_a_gas_constant():
    gas = PerfectGas(gamma=1.4)
    with pytest.raises(MissingGasConstantError) as excinfo:
        _ = gas.cv
    assert "cv" in str(excinfo.value)


# ---------------------------------------------------------------------------
# speed of sound
# ---------------------------------------------------------------------------


def test_speed_of_sound_standard_sea_level():
    """288.15 K in dry air gives 340.29 m/s, the standard sea-level value.

    An independent check of the constant, the relation and the arithmetic
    together: the US Standard Atmosphere, 1976 tabulates 340.294 m/s at this
    temperature, and nothing in RocketForge produced that number.
    """
    air = PerfectGas.air()
    assert speed_of_sound(288.15, air) == pytest.approx(340.294, abs=5e-3)
    assert air.speed_of_sound(288.15) == pytest.approx(340.294, abs=5e-3)


@pytest.mark.parametrize("gamma,r,temperature,expected", [
    (1.4, 287.0528, 288.15, math.sqrt(1.4 * 287.0528 * 288.15)),
    (1.22, 320.0, 3300.0, math.sqrt(1.22 * 320.0 * 3300.0)),
    (1.66, 2077.0, 300.0, math.sqrt(1.66 * 2077.0 * 300.0)),
])
def test_speed_of_sound_matches_the_relation(gamma, r, temperature, expected):
    gas = PerfectGas(gamma=gamma, gas_constant=r)
    assert speed_of_sound(temperature, gas) == pytest.approx(expected, rel=1e-15)


def test_speed_of_sound_scales_as_the_square_root_of_temperature():
    air = PerfectGas.air()
    assert speed_of_sound(4 * 300.0, air) == pytest.approx(2 * speed_of_sound(300.0, air), rel=1e-15)


def test_speed_of_sound_accepts_arrays():
    air = PerfectGas.air()
    result = speed_of_sound(np.array([200.0, 288.15, 1000.0]), air)
    assert isinstance(result, np.ndarray)
    assert result.shape == (3,)
    assert result[1] == pytest.approx(340.294, abs=5e-3)


def test_speed_of_sound_returns_a_float_for_scalar_input():
    assert isinstance(speed_of_sound(288.15, PerfectGas.air()), float)


@pytest.mark.parametrize("bad", [0.0, -1.0, -300.0])
def test_speed_of_sound_rejects_non_positive_temperature(bad):
    """Kelvin, always. 20 would be 20 K, not room temperature, so refuse rather than guess."""
    with pytest.raises(DomainError):
        speed_of_sound(bad, PerfectGas.air())


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_speed_of_sound_rejects_non_finite_temperature(bad):
    with pytest.raises(DomainError):
        speed_of_sound(bad, PerfectGas.air())


def test_speed_of_sound_rejects_one_bad_element_in_an_array():
    """No silent NaN: an invalid element fails the call and names its index."""
    with pytest.raises(DomainError) as excinfo:
        speed_of_sound(np.array([300.0, -5.0, 400.0]), PerfectGas.air())
    assert "index 1" in str(excinfo.value)


def test_speed_of_sound_requires_a_gas_constant():
    with pytest.raises(MissingGasConstantError):
        speed_of_sound(288.15, PerfectGas(gamma=1.4))
