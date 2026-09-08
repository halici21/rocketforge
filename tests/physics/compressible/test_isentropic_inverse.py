"""Verification of the closed-form isentropic inverses.

``T/T0 -> M``, ``p/p0 -> M`` and ``rho/rho0 -> M`` all have exact algebraic
inverses, so ``04`` section 3.6 requires that none of them iterate. Covers the
inverse relations, their domains, the round trips of ``05`` section 10, and the
conditioning of the near-stagnation limit.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from rocketforge.core.errors import DomainError
from rocketforge.core.numerics import roots
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]

# Forward relation paired with its inverse and the name of the ratio.
PAIRS = (
    ("T/T0", iso.temperature_ratio, iso.mach_from_temperature_ratio),
    ("p/p0", iso.pressure_ratio, iso.mach_from_pressure_ratio),
    ("rho/rho0", iso.density_ratio, iso.mach_from_density_ratio),
)

ROUND_TRIP_MACH = np.array([
    1e-6, 1e-4, 0.01, 0.1, 0.3, 0.5, 0.8, 0.95, 0.999, 1.0,
    1.001, 1.05, 1.5, 2.0, 3.0, 5.0, 8.0, 10.0,
])


# ---------------------------------------------------------------------------
# the inverses are analytic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name,forward,inverse", PAIRS, ids=[p[0] for p in PAIRS])
def test_inverse_does_not_call_the_root_solver(monkeypatch, name, forward, inverse):
    """A closed form must not iterate: it would be slower and less accurate.

    Guards the requirement directly rather than by inspection, by making any
    call to the shared solver fail.
    """
    def forbidden(*args, **kwargs):  # pragma: no cover - only runs on failure
        raise AssertionError(f"{name} inverse must be closed form, but it called brent()")

    monkeypatch.setattr(roots, "brent", forbidden)
    monkeypatch.setattr(iso, "brent", forbidden)
    gas = PerfectGas(gamma=1.4)
    assert inverse(0.5, gas) > 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_analytic_inverse_agrees_with_a_numerical_solve(gas):
    """The closed form must give what a bracketed solve of the forward relation does.

    Both validates the algebra and documents the equivalence -- the numerical
    route is the oracle here, not the implementation.
    """
    for mach in (0.2, 0.7, 1.0, 2.5, 6.0):
        target = float(iso.pressure_ratio(mach, gas))
        numerical, report = roots.brent(
            lambda m: float(iso.pressure_ratio(m, gas)) - target,
            1e-9, 50.0, xtol=1e-13, rtol=1e-15, max_iter=200,
        )
        assert report.converged
        analytic = float(iso.mach_from_pressure_ratio(target, gas))
        assert analytic == pytest.approx(numerical, rel=1e-9, abs=1e-12)


# ---------------------------------------------------------------------------
# round trips
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("name,forward,inverse", PAIRS, ids=[p[0] for p in PAIRS])
def test_round_trip_recovers_the_mach_number(gas, name, forward, inverse):
    for mach in ROUND_TRIP_MACH:
        ratio = float(forward(float(mach), gas))
        recovered = float(inverse(ratio, gas))
        assert recovered == pytest.approx(float(mach), rel=1e-9, abs=1e-9), (
            f"{name} round trip failed at M = {mach} for gamma = {gas.gamma}"
        )


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("name,forward,inverse", PAIRS, ids=[p[0] for p in PAIRS])
def test_round_trip_is_tight_away_from_stagnation(gas, name, forward, inverse):
    """Away from M = 0 the round trip is good to nearly machine precision."""
    for mach in (0.3, 0.7, 1.0, 2.0, 5.0):
        ratio = float(forward(mach, gas))
        assert float(inverse(ratio, gas)) == pytest.approx(mach, rel=1e-13)


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_round_trip_conditioning_near_stagnation(gas):
    """Near M = 0 the ratios are flat, so the inverse loses precision -- by how much.

    T/T0 - 1 ~ -(gamma-1)/2 M^2, so a ratio known to a relative accuracy d
    fixes M only to about sqrt(d). At M = 1e-6 the ratio differs from 1 by
    ~1e-12, leaving only a few digits of Mach number recoverable. The test
    records that limit rather than pretending it is not there.
    """
    for mach, tolerance in ((1e-3, 1e-9), (1e-4, 1e-7), (1e-6, 1e-3)):
        ratio = float(iso.temperature_ratio(mach, gas))
        recovered = float(iso.mach_from_temperature_ratio(ratio, gas))
        assert recovered == pytest.approx(mach, rel=tolerance)


def test_pressure_inverse_uses_a_stable_form_near_stagnation():
    """expm1 keeps digits that the naive difference throws away.

    At p/p0 = 1 - 1e-13 the naive ``(p0/p)**((g-1)/g) - 1`` cancels to almost
    nothing, while the implemented form still resolves the Mach number.
    """
    gas = PerfectGas(gamma=1.4)
    ratio = 1.0 - 1e-13
    recovered = float(iso.mach_from_pressure_ratio(ratio, gas))
    expected = math.sqrt(2.0 / 0.4 * (1e-13 * (0.4 / 1.4)))
    assert recovered == pytest.approx(expected, rel=1e-3)
    assert recovered > 0.0


# ---------------------------------------------------------------------------
# exact endpoints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("name,forward,inverse", PAIRS, ids=[p[0] for p in PAIRS])
def test_ratio_of_one_returns_zero_mach(gas, name, forward, inverse):
    """Static equal to stagnation means the flow is at rest."""
    assert inverse(1.0, gas) == 0.0


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
def test_sonic_ratios_invert_to_exactly_one(gas):
    for forward, inverse in ((iso.pressure_ratio, iso.mach_from_pressure_ratio),
                             (iso.temperature_ratio, iso.mach_from_temperature_ratio),
                             (iso.density_ratio, iso.mach_from_density_ratio)):
        sonic_ratio = float(forward(1.0, gas))
        assert float(inverse(sonic_ratio, gas)) == pytest.approx(1.0, rel=1e-13)


# ---------------------------------------------------------------------------
# domain
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name,forward,inverse", PAIRS, ids=[p[0] for p in PAIRS])
@pytest.mark.parametrize("bad", [1.0 + 1e-12, 1.5, 2.0, 100.0])
def test_ratio_above_one_rejected(name, forward, inverse, bad):
    """A static value above its stagnation value is not a flow state.

    Rejected, never clamped to 1: 1.0000001 usually means the caller computed
    the ratio the other way up.
    """
    with pytest.raises(DomainError):
        inverse(bad, PerfectGas(gamma=1.4))


@pytest.mark.parametrize("name,forward,inverse", PAIRS, ids=[p[0] for p in PAIRS])
@pytest.mark.parametrize("bad", [0.0, -1e-12, -0.5])
def test_ratio_at_or_below_zero_rejected(name, forward, inverse, bad):
    with pytest.raises(DomainError):
        inverse(bad, PerfectGas(gamma=1.4))


@pytest.mark.parametrize("name,forward,inverse", PAIRS, ids=[p[0] for p in PAIRS])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_ratio_rejected(name, forward, inverse, bad):
    with pytest.raises(DomainError):
        inverse(bad, PerfectGas(gamma=1.4))


def test_inverse_array_with_one_bad_element_raises_and_names_it():
    with pytest.raises(DomainError) as excinfo:
        iso.mach_from_pressure_ratio(np.array([0.5, 0.3, 1.7]), PerfectGas(gamma=1.4))
    assert "index 2" in str(excinfo.value)


# ---------------------------------------------------------------------------
# scalar / array
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name,forward,inverse", PAIRS, ids=[p[0] for p in PAIRS])
def test_inverse_scalar_returns_float(name, forward, inverse):
    assert isinstance(inverse(0.5, PerfectGas(gamma=1.4)), float)


@pytest.mark.parametrize("name,forward,inverse", PAIRS, ids=[p[0] for p in PAIRS])
def test_inverse_array_round_trips(name, forward, inverse):
    gas = PerfectGas(gamma=1.4)
    grid = np.array([0.2, 0.5, 0.8, 0.95])
    recovered = inverse(forward(inverse(grid, gas), gas), gas)
    assert isinstance(recovered, np.ndarray)
    assert np.allclose(recovered, inverse(grid, gas), rtol=1e-12)


def test_inverse_is_monotone_decreasing_in_the_ratio():
    """A smaller ratio means a faster flow."""
    gas = PerfectGas(gamma=1.4)
    ratios = np.linspace(0.01, 1.0, 500)
    machs = iso.mach_from_pressure_ratio(ratios, gas)
    assert np.all(np.diff(machs) < 0.0)
