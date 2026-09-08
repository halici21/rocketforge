"""Rayleigh flow: the forward relations and the extrema that make it awkward.

Specified in ``docs/engineering/03_compressible_flow_specification.md`` section
9. This is the one family in the module whose qualitative behaviour is
genuinely counter-intuitive, and the specification is explicit that it must not
be tidied up:

* ``T0/T0*`` peaks at exactly 1 at M = 1 -- the thermal choking limit;
* ``T/T*`` peaks at **M = 1/sqrt(gamma)**, which is *not* sonic;
* between those two Mach numbers the static temperature falls while heat is
  still being added.

The last point is the one a future refactor would be tempted to "fix", so it is
pinned here from several directions at once.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import rayleigh

GAMMAS = (1.2, 1.3, 1.4, 1.66)
SUBSONIC = (0.05, 0.2, 0.5, 0.8, 0.95, 0.999)
SUPERSONIC = (1.001, 1.05, 1.5, 2.0, 3.5, 8.0, 40.0)


def gas(gamma: float) -> PerfectGas:
    return PerfectGas(gamma=gamma)


# ---------------------------------------------------------------------------
# the sonic state
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_every_starred_ratio_is_one_at_the_sonic_state(gamma):
    air = gas(gamma)
    assert rayleigh.temperature_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)
    assert rayleigh.pressure_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)
    assert rayleigh.density_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)
    assert rayleigh.stagnation_temperature_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)
    assert rayleigh.stagnation_pressure_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)


# ---------------------------------------------------------------------------
# T0/T0*: maximum at sonic, which is what thermal choking means
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", SUBSONIC + SUPERSONIC)
def test_stagnation_temperature_ratio_never_exceeds_one(gamma, mach):
    """Blocking invariant: the sonic state is the most heat the line can take."""
    assert rayleigh.stagnation_temperature_ratio(mach, gas(gamma)) <= 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
def test_stagnation_temperature_ratio_is_exactly_one_only_at_sonic(gamma):
    air = gas(gamma)
    assert rayleigh.stagnation_temperature_ratio(1.0, air) == pytest.approx(1.0, abs=1e-15)
    for mach in (0.9, 0.99, 1.01, 1.1):
        assert rayleigh.stagnation_temperature_ratio(mach, air) < 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
def test_heating_drives_both_branches_towards_sonic(gamma):
    """T0/T0* rises towards 1 from below on the subsonic side and from below
    on the supersonic side, so adding heat moves either branch towards M = 1."""
    air = gas(gamma)
    sub = [float(rayleigh.stagnation_temperature_ratio(m, air)) for m in SUBSONIC]
    assert sub == sorted(sub)                       # increasing towards sonic

    sup = [float(rayleigh.stagnation_temperature_ratio(m, air)) for m in SUPERSONIC]
    assert sup == sorted(sup, reverse=True)         # decreasing away from sonic


@pytest.mark.parametrize("gamma", GAMMAS)
def test_stagnation_temperature_ratio_has_a_finite_supersonic_floor(gamma):
    """(gamma^2 - 1)/gamma^2 as M -> infinity: a supersonic flow can only be
    cooled so far before it runs out of Rayleigh line."""
    air = gas(gamma)
    limit = rayleigh.stagnation_temperature_ratio_limit(air)
    assert limit == pytest.approx((gamma * gamma - 1.0) / (gamma * gamma), rel=1e-14)

    approach = [float(rayleigh.stagnation_temperature_ratio(m, air))
                for m in (10.0, 100.0, 1e4)]
    assert all(v > limit for v in approach)
    assert approach == sorted(approach, reverse=True)
    assert approach[-1] == pytest.approx(limit, rel=1e-7)


def test_supersonic_floor_matches_the_specification_value_for_air():
    """0.4897959184 at gamma = 1.4, from ``03`` section 9.2."""
    assert rayleigh.stagnation_temperature_ratio_limit(gas(1.4)) == pytest.approx(
        0.4897959184, abs=5e-11)


# ---------------------------------------------------------------------------
# T/T*: the extremum that is not at sonic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_static_temperature_peaks_at_one_over_root_gamma(gamma):
    air = gas(gamma)
    peak = rayleigh.mach_at_maximum_temperature(air)
    assert peak == pytest.approx(1.0 / math.sqrt(gamma), rel=1e-15)
    assert peak < 1.0                                # always subsonic


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_value_at_the_static_temperature_peak(gamma):
    """(gamma+1)^2 / (4 gamma), and it exceeds 1: hotter than the sonic state."""
    air = gas(gamma)
    peak = rayleigh.mach_at_maximum_temperature(air)
    expected = (gamma + 1.0) ** 2 / (4.0 * gamma)
    assert rayleigh.maximum_temperature_ratio(air) == pytest.approx(expected, rel=1e-15)
    assert float(rayleigh.temperature_ratio(peak, air)) == pytest.approx(expected, rel=1e-14)
    assert expected > 1.0


def test_static_temperature_peak_matches_the_specification_values_for_air():
    """M = 0.8451542547 and T/T* = 1.0285714286, from ``03`` section 9.2."""
    air = gas(1.4)
    assert rayleigh.mach_at_maximum_temperature(air) == pytest.approx(
        0.8451542547, abs=5e-11)
    assert rayleigh.maximum_temperature_ratio(air) == pytest.approx(
        1.0285714286, abs=5e-11)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_derivative_of_the_static_temperature_ratio_vanishes_at_the_peak(gamma):
    """A central difference, at a step chosen for the round-off floor.

    ``05`` section 9 asks for this to be checked properly rather than by
    eyeballing a coarse grid: a maximum found only by comparing three tabulated
    points would survive a formula that put the peak in slightly the wrong
    place.
    """
    air = gas(gamma)
    peak = rayleigh.mach_at_maximum_temperature(air)
    h = 1e-5
    forward = float(rayleigh.temperature_ratio(peak + h, air))
    backward = float(rayleigh.temperature_ratio(peak - h, air))
    derivative = (forward - backward) / (2.0 * h)
    assert abs(derivative) < 1e-9

    # And it really is a maximum, not a saddle: the second difference is negative.
    centre = float(rayleigh.temperature_ratio(peak, air))
    second = (forward - 2.0 * centre + backward) / (h * h)
    assert second < 0.0


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_peak_beats_every_neighbour_on_a_fine_grid(gamma):
    air = gas(gamma)
    peak = rayleigh.mach_at_maximum_temperature(air)
    best = float(rayleigh.temperature_ratio(peak, air))
    grid = np.linspace(max(1e-3, peak - 0.3), peak + 0.3, 2001)
    values = np.asarray(rayleigh.temperature_ratio(grid, air))
    assert best >= values.max() - 1e-14


@pytest.mark.parametrize("gamma", GAMMAS)
def test_static_temperature_falls_between_its_peak_and_sonic(gamma):
    """The counter-intuitive band, pinned.

    Heat is still going in across this interval and the static temperature is
    going *down*, because the flow is accelerating fast enough that the
    kinetic-energy rise outruns it. A "tidy-up" that made T/T* monotone would
    break here, which is the entire point of the test.
    """
    air = gas(gamma)
    peak = rayleigh.mach_at_maximum_temperature(air)
    grid = np.linspace(peak, 1.0, 200)
    values = np.asarray(rayleigh.temperature_ratio(grid, air))
    assert np.all(np.diff(values) <= 1e-15)

    # Heat is genuinely still being added across that same interval.
    heat = np.asarray(rayleigh.stagnation_temperature_ratio(grid, air))
    assert np.all(np.diff(heat) >= -1e-15)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_static_temperature_rises_below_the_peak_and_falls_above_sonic(gamma):
    air = gas(gamma)
    peak = rayleigh.mach_at_maximum_temperature(air)
    rising = np.asarray(rayleigh.temperature_ratio(np.linspace(0.05, peak, 200), air))
    assert np.all(np.diff(rising) >= -1e-15)
    falling = np.asarray(rayleigh.temperature_ratio(np.linspace(1.0, 6.0, 200), air))
    assert np.all(np.diff(falling) <= 1e-15)


# ---------------------------------------------------------------------------
# pressure, density and the stagnation-pressure loss
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_pressure_ratio_falls_monotonically_with_mach(gamma):
    """p/p* = (gamma+1)/(1 + gamma M^2): above 1 subsonic, below 1 supersonic."""
    air = gas(gamma)
    values = [float(rayleigh.pressure_ratio(m, air)) for m in SUBSONIC + SUPERSONIC]
    assert values == sorted(values, reverse=True)
    assert float(rayleigh.pressure_ratio(0.5, air)) > 1.0
    assert float(rayleigh.pressure_ratio(2.0, air)) < 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
def test_density_ratio_falls_monotonically_with_mach(gamma):
    air = gas(gamma)
    values = [float(rayleigh.density_ratio(m, air)) for m in SUBSONIC + SUPERSONIC]
    assert values == sorted(values, reverse=True)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", SUBSONIC + SUPERSONIC)
def test_heat_addition_always_destroys_stagnation_pressure(gamma, mach):
    """p0/p0* > 1 off sonic on both branches, with its minimum of 1 at M = 1.

    The Rayleigh loss. Worth surfacing in the interface, and worth a test here
    so that it cannot quietly invert.
    """
    assert rayleigh.stagnation_pressure_ratio(mach, gas(gamma)) > 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", SUBSONIC + SUPERSONIC)
def test_pressure_equals_density_times_temperature(gamma, mach):
    """The equation of state in starred form, as an internal consistency check."""
    air = gas(gamma)
    assert (float(rayleigh.pressure_ratio(mach, air))
            == pytest.approx(float(rayleigh.density_ratio(mach, air))
                             * float(rayleigh.temperature_ratio(mach, air)), rel=1e-13))


# ---------------------------------------------------------------------------
# the state record and the domain
# ---------------------------------------------------------------------------


def test_state_carries_every_relation_at_one_station():
    air = gas(1.4)
    record = rayleigh.state(0.5, air)
    assert record.mach == 0.5
    for name, fn in (("temperature_ratio", rayleigh.temperature_ratio),
                     ("pressure_ratio", rayleigh.pressure_ratio),
                     ("density_ratio", rayleigh.density_ratio),
                     ("stagnation_temperature_ratio",
                      rayleigh.stagnation_temperature_ratio),
                     ("stagnation_pressure_ratio",
                      rayleigh.stagnation_pressure_ratio)):
        assert getattr(record, name) == pytest.approx(float(fn(0.5, air)))


def test_state_refuses_an_array():
    with pytest.raises(DomainError):
        rayleigh.state(np.array([0.5, 0.8]), gas(1.4))


@pytest.mark.parametrize("bad", [0.0, -0.5])
def test_mach_must_be_strictly_positive(bad):
    with pytest.raises(DomainError):
        rayleigh.temperature_ratio(bad, gas(1.4))


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_mach_is_refused(bad):
    with pytest.raises(DomainError):
        rayleigh.pressure_ratio(bad, gas(1.4))


def test_array_input_is_supported_and_elementwise():
    air = gas(1.4)
    grid = np.array([0.2, 0.5, 1.0, 2.0, 5.0])
    values = rayleigh.stagnation_temperature_ratio(grid, air)
    assert isinstance(values, np.ndarray)
    for i, mach in enumerate(grid):
        assert values[i] == pytest.approx(
            float(rayleigh.stagnation_temperature_ratio(float(mach), air)))
