"""Phase 4E cross-validation: what Fanno and Rayleigh share, and what they must not.

Three separate jobs, all of which guard against the same class of mistake --
one relation quietly standing in for another.

1. **The shock as the Fanno-Rayleigh intersection.** A normal shock joins two
   states of equal mass flux and equal momentum flux, in a constant-area
   passage, adiabatically. Those are exactly the defining conditions of the
   Fanno line (constant area, adiabatic) and of the Rayleigh line (constant
   area, frictionless momentum balance). So the two states either side of a
   shock lie on the *same* Fanno line and on the *same* Rayleigh line, and
   every starred ratio must reproduce the shock jump. That is an independent
   check on eight of the nine Phase 4E relations which needs no Fanno or
   Rayleigh table -- and, since the normal-shock module is confirmed against
   NACA 1135, it is anchored to a printed table all the same.

2. **The two genuine Fanno coincidences** with the isentropic family, from
   ``03`` section 8.4 -- asserted so they are known rather than accidental.

3. **The absences**: the ratios that must *not* coincide. ``05`` section 9 asks
   for both halves, so that a later tidy-up cannot merge the families.
"""

from __future__ import annotations

import inspect

import pytest

from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import fanno
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import normal_shock as shock
from rocketforge.physics.compressible import rayleigh

GAMMAS = (1.2, 1.3, 1.4, 1.66)
SHOCK_MACHS = (1.2, 1.5, 2.0, 3.0, 5.0, 8.0)


def gas(gamma: float) -> PerfectGas:
    return PerfectGas(gamma=gamma)


# ---------------------------------------------------------------------------
# 1. the shock lies on both lines
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", SHOCK_MACHS)
@pytest.mark.parametrize("quantity", ["pressure_ratio", "temperature_ratio",
                                      "density_ratio", "stagnation_pressure_ratio"])
def test_the_fanno_line_reproduces_the_normal_shock_jump(gamma, mach1, quantity):
    """``fanno.X(M2)/fanno.X(M1)`` is the shock's own X, to machine precision."""
    air = gas(gamma)
    mach2 = float(shock.mach_downstream(mach1, air))
    relation = getattr(fanno, quantity)
    along_line = float(relation(mach2, air)) / float(relation(mach1, air))
    across_shock = float(getattr(shock, quantity)(mach1, air))
    assert along_line == pytest.approx(across_shock, rel=1e-12)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", SHOCK_MACHS)
@pytest.mark.parametrize("quantity", ["pressure_ratio", "temperature_ratio",
                                      "density_ratio", "stagnation_pressure_ratio"])
def test_the_rayleigh_line_reproduces_the_normal_shock_jump(gamma, mach1, quantity):
    air = gas(gamma)
    mach2 = float(shock.mach_downstream(mach1, air))
    relation = getattr(rayleigh, quantity)
    along_line = float(relation(mach2, air)) / float(relation(mach1, air))
    across_shock = float(getattr(shock, quantity)(mach1, air))
    assert along_line == pytest.approx(across_shock, rel=1e-12)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", SHOCK_MACHS)
def test_rayleigh_stagnation_temperature_is_equal_either_side_of_a_shock(gamma, mach1):
    """The ninth relation, checked by the same argument.

    A shock is adiabatic, so T0 is unchanged across it; both states sit on one
    Rayleigh line, so they share one T0*. The ratio must therefore be *equal*
    at the two states -- a strong constraint on the shape of T0/T0*, and one
    that no table was needed to state.
    """
    air = gas(gamma)
    mach2 = float(shock.mach_downstream(mach1, air))
    upstream = float(rayleigh.stagnation_temperature_ratio(mach1, air))
    downstream = float(rayleigh.stagnation_temperature_ratio(mach2, air))
    assert downstream == pytest.approx(upstream, rel=1e-12)


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach1", SHOCK_MACHS)
def test_a_shock_moves_along_both_lines_in_the_direction_entropy_allows(gamma, mach1):
    """Supersonic to subsonic, with a stagnation-pressure loss on both lines."""
    air = gas(gamma)
    mach2 = float(shock.mach_downstream(mach1, air))
    assert mach2 < 1.0 < mach1
    for module in (fanno, rayleigh):
        loss = (float(module.stagnation_pressure_ratio(mach2, air))
                / float(module.stagnation_pressure_ratio(mach1, air)))
        assert loss < 1.0


# ---------------------------------------------------------------------------
# 2. the two genuine Fanno coincidences
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", [0.2, 0.5, 0.9, 1.0, 1.5, 3.0])
def test_fanno_temperature_ratio_equals_the_isentropic_starred_form(gamma, mach):
    """Both are (gamma+1)/(2+(gamma-1)M^2), because T0 is constant in each.

    Documented in ``03`` section 8.4 as a coincidence rather than a shared
    implementation: the two families reach their sonic states by entirely
    different processes.
    """
    air = gas(gamma)
    assert (float(fanno.temperature_ratio(mach, air))
            == pytest.approx(float(iso.temperature_ratio_star(mach, air)), rel=1e-14))


@pytest.mark.parametrize("gamma", GAMMAS)
@pytest.mark.parametrize("mach", [0.2, 0.5, 0.9, 1.0, 1.5, 3.0])
def test_fanno_stagnation_pressure_ratio_equals_the_isentropic_area_ratio(gamma, mach):
    """p0/p0* == A/A*, because p0 A* is fixed by the mass flow and T0."""
    air = gas(gamma)
    assert (float(fanno.stagnation_pressure_ratio(mach, air))
            == pytest.approx(float(iso.area_ratio(mach, air)), rel=1e-14))


# ---------------------------------------------------------------------------
# 3. the absences
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mach", [0.5, 2.0])
def test_fanno_pressure_and_density_do_not_coincide_with_the_isentropic_forms(mach):
    """The other half of the rule: only two ratios coincide, and these are not
    among them. A refactor that merged the families would trip here."""
    air = gas(1.4)
    assert (float(fanno.pressure_ratio(mach, air))
            != pytest.approx(float(iso.pressure_ratio_star(mach, air)), rel=1e-6))
    assert (float(fanno.density_ratio(mach, air))
            != pytest.approx(float(iso.density_ratio_star(mach, air)), rel=1e-6))


@pytest.mark.parametrize("mach", [0.5, 2.0])
def test_no_rayleigh_ratio_coincides_with_its_isentropic_or_fanno_counterpart(mach):
    """``03`` section 9.4: none. T/T* is the one worth naming -- Rayleigh has
    M^2[(gamma+1)/(1+gamma M^2)]^2 where the other two families share
    (gamma+1)/(2+(gamma-1)M^2) -- and a copy-paste between the modules would
    show up here immediately."""
    air = gas(1.4)
    assert (float(rayleigh.temperature_ratio(mach, air))
            != pytest.approx(float(fanno.temperature_ratio(mach, air)), rel=1e-6))
    assert (float(rayleigh.temperature_ratio(mach, air))
            != pytest.approx(float(iso.temperature_ratio_star(mach, air)), rel=1e-6))
    assert (float(rayleigh.pressure_ratio(mach, air))
            != pytest.approx(float(fanno.pressure_ratio(mach, air)), rel=1e-6))
    assert (float(rayleigh.stagnation_pressure_ratio(mach, air))
            != pytest.approx(float(fanno.stagnation_pressure_ratio(mach, air)), rel=1e-6))


# ---------------------------------------------------------------------------
# the root solver is the shared one
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module", [fanno, rayleigh], ids=["fanno", "rayleigh"])
def test_the_inverses_use_the_phase_4a_brent_and_not_a_local_one(module):
    """``04``: one root finder in the codebase.

    Checked structurally rather than by trusting the import line: the name the
    module binds must be the very function object from
    ``rocketforge.core.numerics.roots``.
    """
    from rocketforge.core.numerics import roots

    assert module.brent is roots.brent

    source = inspect.getsource(module)
    for banned in ("def bisect", "def newton", "def secant", "scipy"):
        assert banned not in source, f"{module.__name__} carries its own {banned}"


@pytest.mark.parametrize("module", [fanno, rayleigh], ids=["fanno", "rayleigh"])
def test_the_modules_do_not_restate_the_gas_model(module):
    """cp, cv and the speed of sound come from PerfectGas, once."""
    source = inspect.getsource(module)
    for banned in ("def cp", "def cv", "def speed_of_sound"):
        assert banned not in source
