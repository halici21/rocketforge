"""Reference validation, in three clearly separated levels.

The levels are not interchangeable and their counts are never merged, because
they are different strengths of evidence:

**Level A -- adapter regression.** Values recorded in Phase 5B-0 by driving the
same installed library directly. These prove the *mapping* has not changed:
units, orientation, species, provenance. They prove nothing about whether CEA
is right, because CEA produced them.

**Level B -- external validation.** A published NASA CEA case with its full
conditions, produced by a *different implementation* of the code (CEA 2002)
than the one under test (CEA v3.3.4). This is the only level here that is
genuinely independent of the installed library.

**Level C -- cross-provider.** Cantera, in ``test_cea_cantera_oracle.py``.
Independent model and independent thermodynamic database.

Tolerances are derived from each source's printed precision, before the
comparison is run -- never widened afterwards to make a value pass.
"""

from __future__ import annotations

import math

import pytest

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    ExpansionMode,
    MixtureRatio,
    Phase,
    PropellantStream,
)
from rocketforge.providers.cea import (
    LIQUID_HYDROGEN,
    LIQUID_METHANE,
    LOX,
    check_availability,
)

_AVAILABILITY = check_availability()
requires_cea = pytest.mark.skipif(
    not _AVAILABILITY.is_usable,
    reason=(f"NASA CEA provider unavailable ({_AVAILABILITY.status.value}): "
            f"{_AVAILABILITY.detail or 'install requirements-thermochemistry.txt'}"),
)

pytestmark = requires_cea

#: Pounds per square inch absolute, in pascals. Exact by the definition of the
#: pound-force and the inch.
PSIA = 6894.757293168361
#: Feet to metres. Exact.
FOOT = 0.3048
#: Standard gravity, for the seconds-to-m/s Isp convention.
G0 = 9.80665


# ===========================================================================
# LEVEL B -- external published NASA CEA case
# ===========================================================================
#
# Source: NASA CEA standard example output, header
#     "NASA-GLENN CHEMICAL EQUILIBRIUM PROGRAM CEA, OCTOBER 18, 2002,
#      BY BONNIE MCBRIDE AND SANFORD GORDON",
# which attributes the code to NASA RP-1311 Part I (1994) and Part II (1996).
# Retrieved from the RocketCEA v1.2.3 documentation, which reproduces the
# program's own printed output verbatim.
#
# Honest statement of what this is: the numbers were produced by NASA's CEA,
# not by RocketForge and not by the installed cea 3.3.4 package. They come from
# the **2002 Fortran implementation**, while the provider under test uses the
# modernised v3 re-implementation. Agreement between two implementations of the
# same method, on the same published case, is meaningful evidence; it is not a
# claim that either is experimentally correct.
#
# Conditions, complete and as published:
#     propellants     O2(L) / H2(L)
#     O/F             6.0 by mass
#     chamber pressure 1000.0 psia
#     area ratio      Ae/At = 40.0, supersonic
#     reactants       H2(L) at 20.27 K, O2(L) at 90.18 K
#     chemistry       equilibrium (shifting) throughout the expansion
#
# The 90.18 K published for O2(L) against the 90.17 K used here is immaterial:
# CEA models O2(L) with an assigned enthalpy, so neither value enters the
# calculation. That is itself a Phase 5C finding, and it is why the difference
# can be dismissed rather than hand-waved.

PUBLISHED_LOX_LH2 = {
    "chamber_temperature_K": 3483.35,      # 6 significant figures
    "molar_mass_kg_per_kmol": 13.458,      # 5 significant figures
    "c_star_ft_per_s": 7560.0,             # 5 significant figures
    "isp_seconds": 431.2,                  # 4 significant figures
    "gamma_exit": 1.2388,                  # 5 significant figures
}


def _rounding_box(value: float, significant_figures: int) -> float:
    """Relative half-width of the box a printed value could have come from.

    A number printed to N significant figures stands for anything within half a
    unit of its last digit. That, not a chosen constant, is what sets the
    tolerance for comparing against it.
    """
    exponent = math.floor(math.log10(abs(value)))
    half_ulp = 0.5 * 10.0 ** (exponent - significant_figures + 1)
    return half_ulp / abs(value)


@pytest.fixture(scope="module")
def published_case(provider):
    """Solve the published case through the whole RocketForge pipeline."""
    from rocketforge.providers.cea.oracle import run_rocket_oracle
    from rocketforge.providers.cea.species import HO_PRODUCT_SPECIES

    pressure = 1000.0 * PSIA
    request = ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_HYDROGEN, 20.27, phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, 90.17, phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(6.0), chamber_pressure=pressure)
    state = provider.solve_chamber(request).unwrap()
    oracle = run_rocket_oracle(
        provider._cea(),
        fuel_names=("H2(L)",), oxidiser_names=("O2(L)",),
        fuel_weights=(1.0,), oxidiser_weights=(1.0,),
        reactant_temperatures=(20.27, 90.17), of_ratio=6.0,
        chamber_pressure=pressure, area_ratio=40.0,
        product_species=HO_PRODUCT_SPECIES,
        expansion_mode=ExpansionMode.EQUILIBRIUM)
    return state, oracle


def test_published_chamber_temperature(published_case):
    """Measured 6.0e-07 against a source printed to six figures."""
    state, _ = published_case
    published = PUBLISHED_LOX_LH2["chamber_temperature_K"]
    tolerance = _rounding_box(published, 6)
    relative = abs(state.temperature - published) / published
    assert relative <= tolerance, (
        f"Tc {state.temperature:.4f} K against published {published} K: "
        f"{relative:.2e} exceeds the source's rounding box {tolerance:.2e}")


def test_published_chamber_molar_mass(published_case):
    state, _ = published_case
    published = PUBLISHED_LOX_LH2["molar_mass_kg_per_kmol"]
    tolerance = _rounding_box(published, 5)
    ours = state.molar_mass * 1000.0          # kg/mol -> kg/kmol for comparison
    relative = abs(ours - published) / published
    assert relative <= tolerance, (
        f"M {ours:.5f} against published {published}: {relative:.2e} exceeds "
        f"{tolerance:.2e}")


def test_published_characteristic_velocity(published_case):
    """c* published in ft/s; converted with the exact definition of the foot."""
    _, oracle = published_case
    published = PUBLISHED_LOX_LH2["c_star_ft_per_s"] * FOOT
    tolerance = _rounding_box(PUBLISHED_LOX_LH2["c_star_ft_per_s"], 5)
    relative = abs(oracle.c_star - published) / published
    assert relative <= tolerance, (
        f"c* {oracle.c_star:.4f} m/s against published {published:.4f} m/s: "
        f"{relative:.2e} exceeds {tolerance:.2e}")


def test_published_specific_impulse(published_case):
    """Isp published in seconds; CEA v3 returns m/s. Converted with g0."""
    _, oracle = published_case
    published = PUBLISHED_LOX_LH2["isp_seconds"]
    tolerance = _rounding_box(published, 4)
    relative = abs(oracle.specific_impulse_seconds - published) / published
    assert relative <= tolerance, (
        f"Isp {oracle.specific_impulse_seconds:.4f} s against published "
        f"{published} s: {relative:.2e} exceeds {tolerance:.2e}")


def test_published_exit_gamma(published_case):
    _, oracle = published_case
    published = PUBLISHED_LOX_LH2["gamma_exit"]
    tolerance = _rounding_box(published, 5)
    relative = abs(oracle.exit.gamma_s - published) / published
    assert relative <= tolerance, (
        f"gamma_exit {oracle.exit.gamma_s:.6f} against published {published}: "
        f"{relative:.2e} exceeds {tolerance:.2e}")


def test_the_published_case_is_not_self_validation(published_case):
    """Stated as a test so the claim cannot quietly rot.

    The reference values were produced by NASA's 2002 Fortran CEA. The provider
    under test uses the v3 re-implementation. Neither number in the comparison
    was produced by the other.
    """
    state, _ = published_case
    assert state.provenance.library_version.startswith("3."), (
        "the installed library should be CEA v3, distinct from the CEA 2002 "
        "implementation that produced the reference values")


# ===========================================================================
# LEVEL A -- adapter regression against Phase 5B-0 raw values
# ===========================================================================
#
# These were recorded in Phase 5B-0 by driving the installed library directly,
# with no RocketForge code in the path. They are NOT independent validation:
# their purpose is to fail loudly if the mapping changes -- a unit, an
# orientation, a species set, a gamma choice.

#: LOX/CH4, O/F 3.4, Pc 100 bar, reactants at their normal boiling points,
#: recorded in Phase 5B-0 from cea 3.3.4 with thermo.lib 8e5df1cc...
PHASE_5B0_LOX_CH4 = {
    "chamber_temperature_K": 3598.28548,
    "c_star_m_per_s": 1846.90,
    "isp_equilibrium_m_per_s": 3434.60,
}


def test_adapter_regression_chamber_temperature(provider):
    """The mapping still produces what Phase 5B-0 recorded.

    Tight, because nothing here should have changed: same library, same
    database, same conditions. A failure means the adapter moved, not that
    chemistry did.
    """
    request = ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_METHANE, 111.643, phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, 90.17, phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=100.0 * 1.0e5)
    state = provider.solve_chamber(request).unwrap()
    recorded = PHASE_5B0_LOX_CH4["chamber_temperature_K"]
    assert state.temperature == pytest.approx(recorded, rel=1e-6), (
        f"adapter regression: Tc {state.temperature} against the recorded "
        f"{recorded}")


def test_adapter_regression_rocket_oracle(provider):
    """c* and Isp still match Phase 5B-0's direct-library values."""
    from rocketforge.providers.cea.oracle import run_rocket_oracle
    from rocketforge.providers.cea.species import CHO_PRODUCT_SPECIES

    oracle = run_rocket_oracle(
        provider._cea(),
        fuel_names=("CH4(L)",), oxidiser_names=("O2(L)",),
        fuel_weights=(1.0,), oxidiser_weights=(1.0,),
        reactant_temperatures=(111.643, 90.17), of_ratio=3.4,
        chamber_pressure=100.0 * 1.0e5, area_ratio=40.0,
        product_species=CHO_PRODUCT_SPECIES,
        expansion_mode=ExpansionMode.EQUILIBRIUM)
    assert oracle.c_star == pytest.approx(
        PHASE_5B0_LOX_CH4["c_star_m_per_s"], rel=1e-4)
    assert oracle.specific_impulse == pytest.approx(
        PHASE_5B0_LOX_CH4["isp_equilibrium_m_per_s"], rel=1e-4)


def test_the_reference_comparator_can_actually_fail(provider):
    """Mutation proof for the comparison itself.

    A reference test that cannot fail is the Phase 4G defect in a new costume.
    A deliberately wrong expected value must be rejected.
    """
    request = ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_METHANE, 111.643, phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, 90.17, phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=100.0 * 1.0e5)
    state = provider.solve_chamber(request).unwrap()

    recorded = PHASE_5B0_LOX_CH4["chamber_temperature_K"]
    mutated = recorded * 1.001               # 0.1 %, ~3.6 K
    assert mutated != recorded, "the mutation must bite"
    assert state.temperature != pytest.approx(mutated, rel=1e-6), (
        "the comparator accepted a value it should have rejected")


def test_the_rounding_box_helper_is_correct():
    """Hand-checkable: 3483.35 to six figures stands for +/- 0.005."""
    assert _rounding_box(3483.35, 6) == pytest.approx(0.005 / 3483.35, rel=1e-12)
    assert _rounding_box(1.2388, 5) == pytest.approx(0.00005 / 1.2388, rel=1e-12)
    assert _rounding_box(431.2, 4) == pytest.approx(0.05 / 431.2, rel=1e-12)
