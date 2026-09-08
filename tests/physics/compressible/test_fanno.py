"""Fanno flow: the forward relations, their limits and their physical direction.

Specified in ``docs/engineering/03_compressible_flow_specification.md`` section
8. The inverse, the duct problem and the friction convention are exercised in
``test_fanno_inverse.py``; the published-table comparison lives in
``test_phase_4e_reference_cases.py``.

The gamma set is the one every previous phase used -- 1.2, 1.3, 1.4, 1.66 --
so a relation that happens to work for air alone is caught here rather than in
a rocket-exhaust calculation later.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import fanno
from rocketforge.physics.compressible import isentropic as iso

GAMMAS = (1.2, 1.3, 1.4, 1.66)
SUBSONIC = (0.05, 0.2, 0.5, 0.8, 0.95, 0.999)
SUPERSONIC = (1.001, 1.05, 1.5, 2.0, 3.5, 8.0, 40.0)


def gas(gamma: float) -> PerfectGas:
    return PerfectGas(gamma=gamma)


# ---------------------------------------------------------------------------
# the sonic state, which every ratio is measured from
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_every_starred_ratio_is_exactly_one_at_the_sonic_state(gamma):
    """M = 1 is the definition of the star state, so each ratio is 1 there."""
    air = gas(gamma)
    assert fanno.temperature_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)
    assert fanno.pressure_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)
    assert fanno.density_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)
    assert fanno.velocity_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)
    assert fanno.stagnation_pressure_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_friction_parameter_is_exactly_zero_at_sonic(gamma):
    """No duct remains at the choking state, and the zero is exact.

    The expression is a difference of two terms that each vanish at M = 1, so
    left alone it returns a few ulp of cancellation noise. The duct logic reads
    the sign of this number, so the implementation forces it and this test
    holds it to that.
    """
    assert fanno.friction_parameter(1.0, gas(gamma)) == 0.0


# ---------------------------------------------------------------------------
# limits
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_friction_parameter_diverges_as_mach_approaches_zero(gamma):
    """An infinitely long subsonic duct. Growth is monotone and unbounded."""
    air = gas(gamma)
    values = [float(fanno.friction_parameter(m, air))
              for m in (1e-1, 1e-2, 1e-3, 1e-4)]
    assert all(np.isfinite(values))
    assert values == sorted(values)          # increasing as M falls
    assert values[-1] > 1e6


@pytest.mark.parametrize("gamma", GAMMAS)
def test_friction_parameter_approaches_its_finite_supersonic_limit(gamma):
    """As M grows the available duct tends to a finite ceiling, from below.

    A real physical statement rather than a numerical convenience: no
    supersonic Fanno duct longer than this can be run without a shock.
    """
    air = gas(gamma)
    limit = fanno.friction_parameter_limit(air)
    closed = fanno.friction_parameter_limit(air)
    expected = (-1.0 / gamma
                + (gamma + 1.0) / (2.0 * gamma) * math.log((gamma + 1.0) / (gamma - 1.0)))
    assert closed == pytest.approx(expected, rel=1e-14)

    approach = [float(fanno.friction_parameter(m, air)) for m in (5.0, 20.0, 100.0, 1e4)]
    assert all(v < limit for v in approach)
    assert approach == sorted(approach)
    assert approach[-1] == pytest.approx(limit, rel=1e-7)


def test_supersonic_limit_matches_the_specification_value_for_air():
    """0.8215081165 at gamma = 1.4, from ``03`` section 8.5."""
    assert fanno.friction_parameter_limit(gas(1.4)) == pytest.approx(
        0.8215081165, abs=5e-11)


# ---------------------------------------------------------------------------
# physical direction: friction drives both branches towards sonic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_friction_parameter_falls_monotonically_towards_sonic_on_both_branches(gamma):
    """The remaining duct shrinks as either branch approaches M = 1.

    This is the invariant the whole duct problem rests on: a duct of parameter
    L consumes L of what is available, so the coordinate has to be monotone on
    each branch separately.
    """
    air = gas(gamma)
    sub = [float(fanno.friction_parameter(m, air)) for m in SUBSONIC]
    assert sub == sorted(sub, reverse=True)

    sup = [float(fanno.friction_parameter(m, air)) for m in SUPERSONIC]
    assert sup == sorted(sup)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_subsonic_friction_accelerates_and_supersonic_friction_decelerates(gamma):
    """Both branches move towards sonic, so the static trends are opposite.

    Subsonic: p, T and rho fall while V rises. Supersonic: the reverse. Stated
    as a comparison between two stations at decreasing remaining duct length,
    which is the direction the flow actually travels.
    """
    air = gas(gamma)

    # Subsonic, moving downstream is moving up in Mach.
    up, down = 0.4, 0.7
    assert fanno.friction_parameter(down, air) < fanno.friction_parameter(up, air)
    assert fanno.pressure_ratio(down, air) < fanno.pressure_ratio(up, air)
    assert fanno.temperature_ratio(down, air) < fanno.temperature_ratio(up, air)
    assert fanno.density_ratio(down, air) < fanno.density_ratio(up, air)
    assert fanno.velocity_ratio(down, air) > fanno.velocity_ratio(up, air)

    # Supersonic, moving downstream is moving down in Mach.
    up, down = 3.0, 1.8
    assert fanno.friction_parameter(down, air) < fanno.friction_parameter(up, air)
    assert fanno.pressure_ratio(down, air) > fanno.pressure_ratio(up, air)
    assert fanno.temperature_ratio(down, air) > fanno.temperature_ratio(up, air)
    assert fanno.density_ratio(down, air) > fanno.density_ratio(up, air)
    assert fanno.velocity_ratio(down, air) < fanno.velocity_ratio(up, air)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", SUBSONIC + SUPERSONIC)
def test_stagnation_pressure_always_falls_towards_the_sonic_state(gamma, mach):
    """p0/p0* > 1 everywhere off sonic: friction is irreversible on both sides.

    Adiabatic is not isentropic. A Fanno duct loses stagnation pressure whether
    it is accelerating a subsonic stream or decelerating a supersonic one, and
    the minimum of the ratio is the sonic state itself.
    """
    if mach == 1.0:
        return
    assert fanno.stagnation_pressure_ratio(mach, gas(gamma)) > 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
def test_stagnation_temperature_is_constant_along_the_duct(gamma):
    """The adiabatic invariant, checked through the isentropic T0 relation.

    T0/T0* is identically 1 for Fanno flow, which is why the module does not
    carry it as a varying column. Computing T0 at two stations from the local
    static temperature and Mach number must give the same number.
    """
    air = gas(gamma)
    t_star = 1.0                                  # any reference works
    values = []
    for mach in (0.3, 0.6, 0.9, 1.0, 1.4, 2.5):
        static = float(fanno.temperature_ratio(mach, air)) * t_star
        values.append(static / float(iso.temperature_ratio(mach, air)))
    assert values == pytest.approx([values[0]] * len(values), rel=1e-14)


# ---------------------------------------------------------------------------
# internal consistency of the ratio family
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", SUBSONIC + SUPERSONIC)
def test_velocity_ratio_is_the_reciprocal_of_the_density_ratio(gamma, mach):
    """Continuity at constant area. Computed as its own relation, checked here."""
    air = gas(gamma)
    assert (float(fanno.velocity_ratio(mach, air))
            == pytest.approx(1.0 / float(fanno.density_ratio(mach, air)), rel=1e-14))


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", SUBSONIC + SUPERSONIC)
def test_pressure_ratio_equals_density_times_temperature(gamma, mach):
    """The ideal equation of state, in starred form: p/p* = (rho/rho*)(T/T*)."""
    air = gas(gamma)
    assert (float(fanno.pressure_ratio(mach, air))
            == pytest.approx(float(fanno.density_ratio(mach, air))
                             * float(fanno.temperature_ratio(mach, air)), rel=1e-14))


# ---------------------------------------------------------------------------
# the state record
# ---------------------------------------------------------------------------


def test_state_carries_every_relation_at_one_station():
    air = gas(1.4)
    record = fanno.state(0.5, air)
    assert record.mach == 0.5
    assert record.temperature_ratio == pytest.approx(float(fanno.temperature_ratio(0.5, air)))
    assert record.pressure_ratio == pytest.approx(float(fanno.pressure_ratio(0.5, air)))
    assert record.density_ratio == pytest.approx(float(fanno.density_ratio(0.5, air)))
    assert record.velocity_ratio == pytest.approx(float(fanno.velocity_ratio(0.5, air)))
    assert record.stagnation_pressure_ratio == pytest.approx(
        float(fanno.stagnation_pressure_ratio(0.5, air)))
    assert record.friction_parameter == pytest.approx(
        float(fanno.friction_parameter(0.5, air)))


def test_state_refuses_an_array():
    """A state record describes one station; an array would silently drop rows."""
    with pytest.raises(DomainError):
        fanno.state(np.array([0.5, 0.8]), gas(1.4))


# ---------------------------------------------------------------------------
# domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [0.0, -0.5, -1.0])
def test_mach_must_be_strictly_positive(bad):
    """Every starred ratio carries a 1/M, so rest is not on the Fanno line."""
    with pytest.raises(DomainError):
        fanno.temperature_ratio(bad, gas(1.4))


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_mach_is_refused(bad):
    with pytest.raises(DomainError):
        fanno.pressure_ratio(bad, gas(1.4))


def test_array_input_is_supported_and_elementwise():
    """The sweeps a chart needs, without a Python loop."""
    air = gas(1.4)
    grid = np.array([0.2, 0.5, 1.0, 2.0, 5.0])
    values = fanno.friction_parameter(grid, air)
    assert isinstance(values, np.ndarray)
    assert values.shape == grid.shape
    for i, mach in enumerate(grid):
        assert values[i] == pytest.approx(float(fanno.friction_parameter(float(mach), air)))


def test_array_input_rejects_a_bad_element():
    """One invalid entry refuses the whole call rather than returning a NaN."""
    with pytest.raises(DomainError):
        fanno.temperature_ratio(np.array([0.5, -1.0, 2.0]), gas(1.4))
