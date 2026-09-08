"""The internal normal shock: where it stands, how it moves, and what it costs.

``03`` section 10.6 and ``04`` section 3.7. The shock is *solved*, never
guessed, and it is solved in area rather than in x because area is the variable
the physics depends on.
"""

from __future__ import annotations

import numpy as np
import pytest

from rocketforge.core.result import Status
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import normal_shock as shock
from rocketforge.physics.compressible import nozzle
from rocketforge.physics.compressible.types import FlowBranch

AREA_RATIO = 2.0
GAMMAS = (1.2, 1.3, 1.4, 1.66)


def gas(gamma: float = 1.4) -> PerfectGas:
    return PerfectGas(gamma=gamma, gas_constant=287.05)


def criticals(gamma: float = 1.4, area_ratio: float = AREA_RATIO):
    return nozzle.critical_pressure_ratios(area_ratio, gas(gamma)).unwrap()


def shock_interval(gamma: float = 1.4, n: int = 25, area_ratio: float = AREA_RATIO):
    critical = criticals(gamma, area_ratio)
    return np.linspace(critical.second_critical * 1.0001,
                       critical.first_critical * 0.9999, n)


# ---------------------------------------------------------------------------
# the corrected Phase 3 example
# ---------------------------------------------------------------------------


def test_the_corrected_phase_3_shock_example():
    """``03`` section 10.6, with the erratum applied.

    The section's first four numbers are reproduced exactly. Its last two are
    wrong -- they lose 38% of the mass flow across the exit plane -- and the
    values here are the ones the section's *own* pseudocode (§12.4) produces.
    See ``docs/engineering/ERRATUM_PHASE_3_NOZZLE_SHOCK_EXAMPLE.md``.
    """
    air = gas()
    back = 0.7044519779
    located = nozzle.shock_area_ratio(AREA_RATIO, back, air).unwrap()
    assert located.area_ratio_shock == pytest.approx(1.5, abs=1e-9)
    assert located.mach_upstream == pytest.approx(1.8541235267, abs=5e-10)
    assert located.mach_downstream == pytest.approx(0.6048430465, abs=5e-10)
    assert located.stagnation_pressure_ratio == pytest.approx(0.7883594291, abs=5e-10)
    assert located.area_star_downstream_ratio == pytest.approx(1.2684569539, abs=5e-10)

    classified = nozzle.classify(AREA_RATIO, back, air).unwrap()
    assert classified.mach_exit == pytest.approx(0.4041969520, abs=5e-10)


def test_the_wrong_phase_3_example_values_are_not_reproduced():
    """A regression guard on the erratum: the old numbers must stay rejected."""
    air = gas()
    located = nozzle.shock_area_ratio(AREA_RATIO, 0.7584257377, air).unwrap()
    assert located.area_ratio_shock != pytest.approx(1.5, abs=1e-3)


def test_mass_is_conserved_across_the_corrected_example():
    """The check that decides which of the two candidate examples is physical."""
    air = gas()
    located = nozzle.shock_area_ratio(AREA_RATIO, 0.7044519779, air).unwrap()
    mach_exit = nozzle.classify(AREA_RATIO, 0.7044519779, air).unwrap().mach_exit
    exit_over_throat = (AREA_RATIO * located.stagnation_pressure_ratio
                        / iso.area_ratio(mach_exit, air))
    assert exit_over_throat == pytest.approx(1.0, rel=1e-9)


# ---------------------------------------------------------------------------
# the shock itself
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_shock_always_stands_in_the_diverging_section(gamma):
    for back in shock_interval(gamma):
        located = nozzle.shock_area_ratio(AREA_RATIO, float(back), gas(gamma)).unwrap()
        assert 1.0 < located.area_ratio_shock <= AREA_RATIO


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_flow_is_supersonic_before_and_subsonic_after(gamma):
    for back in shock_interval(gamma, n=9):
        located = nozzle.shock_area_ratio(AREA_RATIO, float(back), gas(gamma)).unwrap()
        assert located.mach_upstream > 1.0
        assert located.mach_downstream < 1.0


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_shock_is_the_verified_normal_shock_module(gamma):
    """Every jump quantity must be bit-identical to normal_shock.solve."""
    air = gas(gamma)
    for back in shock_interval(gamma, n=9):
        located = nozzle.shock_area_ratio(AREA_RATIO, float(back), air).unwrap()
        independent = shock.solve(located.mach_upstream, air)
        assert located.mach_downstream == independent.mach2
        assert located.pressure_ratio == independent.pressure_ratio
        assert located.stagnation_pressure_ratio == independent.stagnation_pressure_ratio
        assert located.area_star_downstream_ratio == independent.area_star_ratio


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_upstream_mach_is_the_supersonic_area_mach_root(gamma):
    air = gas(gamma)
    for back in shock_interval(gamma, n=9):
        located = nozzle.shock_area_ratio(AREA_RATIO, float(back), air).unwrap()
        expected = iso.mach_from_area_ratio(
            located.area_ratio_shock, air, FlowBranch.SUPERSONIC).unwrap()
        assert located.mach_upstream == expected


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_downstream_sonic_area_is_larger_than_the_throat(gamma):
    """A shock destroys stagnation pressure, so A2* > A1*. Getting this
    backwards is the error the Phase 3 example made."""
    for back in shock_interval(gamma, n=9):
        located = nozzle.shock_area_ratio(AREA_RATIO, float(back), gas(gamma)).unwrap()
        assert located.area_star_downstream_ratio > 1.0
        assert located.area_star_downstream_ratio == pytest.approx(
            1.0 / located.stagnation_pressure_ratio, rel=1e-15)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_exit_pressure_matches_the_back_pressure(gamma):
    """The defining condition of the regime, checked on the returned solution."""
    air = gas(gamma)
    for back in shock_interval(gamma, n=13):
        result = nozzle.classify(AREA_RATIO, float(back), air).unwrap()
        assert result.pressure_ratio_exit == pytest.approx(float(back), rel=1e-9)


# ---------------------------------------------------------------------------
# movement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_lower_back_pressure_moves_the_shock_downstream(gamma):
    backs = shock_interval(gamma, n=40)[::-1]        # descending
    positions = [nozzle.shock_area_ratio(AREA_RATIO, float(b), gas(gamma))
                 .unwrap().area_ratio_shock for b in backs]
    assert np.all(np.diff(positions) > 0.0)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_a_shock_further_downstream_is_a_stronger_shock(gamma):
    backs = shock_interval(gamma, n=25)[::-1]
    located = [nozzle.shock_area_ratio(AREA_RATIO, float(b), gas(gamma)).unwrap()
               for b in backs]
    machs = [s.mach_upstream for s in located]
    losses = [s.stagnation_pressure_ratio for s in located]
    assert np.all(np.diff(machs) > 0.0)
    assert np.all(np.diff(losses) < 0.0)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_shock_vanishes_as_the_back_pressure_reaches_choking_onset(gamma):
    """Approaching the first critical, the supersonic pocket shrinks to nothing."""
    critical = criticals(gamma)
    previous = None
    for offset in (1e-3, 1e-4, 1e-5, 1e-6):
        located = nozzle.shock_area_ratio(
            AREA_RATIO, critical.first_critical - offset, gas(gamma)).unwrap()
        assert located.area_ratio_shock > 1.0
        assert located.mach_upstream > 1.0
        assert located.stagnation_pressure_ratio < 1.0
        if previous is not None:
            assert located.area_ratio_shock < previous.area_ratio_shock
            assert located.mach_upstream < previous.mach_upstream
            assert located.stagnation_pressure_ratio > previous.stagnation_pressure_ratio
        previous = located
    assert previous.area_ratio_shock == pytest.approx(1.0, abs=1e-3)
    assert previous.mach_upstream == pytest.approx(1.0, abs=1e-2)
    assert previous.stagnation_pressure_ratio == pytest.approx(1.0, abs=1e-5)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_shock_reaches_the_exit_as_the_back_pressure_reaches_the_second(gamma):
    critical = criticals(gamma)
    located = nozzle.shock_area_ratio(
        AREA_RATIO, critical.second_critical * (1 + 1e-9), gas(gamma)).unwrap()
    assert located.area_ratio_shock == pytest.approx(AREA_RATIO, rel=1e-5)
    assert located.mach_upstream == pytest.approx(critical.mach_exit_supersonic, rel=1e-5)


# ---------------------------------------------------------------------------
# boundaries are answered exactly, not by a degenerate root solve
# ---------------------------------------------------------------------------


def test_the_shock_at_exit_boundary_is_exact():
    air = gas()
    critical = criticals()
    located = nozzle.shock_area_ratio(AREA_RATIO, critical.second_critical, air)
    assert located.value.area_ratio_shock == AREA_RATIO
    assert located.value.mach_upstream == critical.mach_exit_supersonic
    assert located.convergence is None, "an exact boundary is not an iteration"
    independent = shock.solve(critical.mach_exit_supersonic, air)
    assert located.value.mach_downstream == independent.mach2


def test_choking_onset_reports_that_there_is_no_shock_to_place():
    critical = criticals()
    located = nozzle.shock_area_ratio(AREA_RATIO, critical.first_critical, gas())
    assert located.value is None
    assert located.status is Status.NO_SOLUTION
    assert any(d.code == "NO_INTERNAL_SHOCK" for d in located.diagnostics)


@pytest.mark.parametrize("back", [0.99, 0.2, 0.05])
def test_a_back_pressure_outside_the_interval_has_no_internal_shock(back):
    located = nozzle.shock_area_ratio(AREA_RATIO, back, gas())
    assert located.value is None
    assert located.status is Status.NO_SOLUTION
    assert any(d.code == "NO_INTERNAL_SHOCK" for d in located.diagnostics)


# ---------------------------------------------------------------------------
# the solver's own report
# ---------------------------------------------------------------------------


def test_the_root_report_survives_into_the_result():
    """``100``: numerical provenance is not discarded."""
    critical = criticals()
    middle = 0.5 * (critical.first_critical + critical.second_critical)
    located = nozzle.shock_area_ratio(AREA_RATIO, middle, gas())
    assert located.convergence is not None
    assert located.convergence.converged
    assert located.convergence.iterations > 0
    assert located.convergence.bracket is not None
    assert abs(located.convergence.residual) < 1e-9


def test_the_bracket_ends_are_the_two_criticals_so_no_search_is_needed():
    """``04`` section 3.7: the closed-form bracket always brackets the root.

    The claim is about the *objective*, not about the interval the solver
    happens to finish on, so it is checked where it lives: at the throat end
    the predicted exit pressure is the first critical, at the exit end it is
    the second, and the residual therefore changes sign for every back
    pressure strictly between them.
    """
    air = gas()
    critical = criticals()
    tolerances = nozzle.DEFAULT_TOLERANCES
    at_throat = nozzle._exit_pressure_ratio_for_shock(
        1.0 + tolerances.sonic_margin, AREA_RATIO, air, tolerances)
    at_exit = nozzle._exit_pressure_ratio_for_shock(
        AREA_RATIO, AREA_RATIO, air, tolerances)
    # Not bit-identical, and not expected to be: the residual runs two nested
    # area-Mach inversions where the critical runs one, and each is converged
    # to mach_abs_tol. Agreement to a few parts in 1e12 is what that costs.
    assert at_throat == pytest.approx(critical.first_critical, rel=1e-6)
    assert at_exit == pytest.approx(critical.second_critical, rel=1e-9)

    for back in shock_interval(n=9):
        assert (at_throat - back) > 0.0 > (at_exit - back)


def test_the_final_bracket_contains_the_root():
    critical = criticals()
    middle = 0.5 * (critical.first_critical + critical.second_critical)
    located = nozzle.shock_area_ratio(AREA_RATIO, middle, gas())
    low, high = located.convergence.bracket
    assert low <= located.value.area_ratio_shock <= high
    assert high - low < 1e-8


def test_the_residual_is_the_exit_pressure_error():
    """The objective is physically interpretable, which is why it is testable."""
    air = gas()
    critical = criticals()
    middle = 0.5 * (critical.first_critical + critical.second_critical)
    located = nozzle.shock_area_ratio(AREA_RATIO, middle, air).unwrap()
    predicted = nozzle._exit_pressure_ratio_for_shock(
        located.area_ratio_shock, AREA_RATIO, air, nozzle.DEFAULT_TOLERANCES)
    assert predicted == pytest.approx(middle, rel=1e-9)


@pytest.mark.parametrize("area_ratio", [1.2, 2.0, 5.0, 20.0])
def test_the_solver_works_across_a_wide_range_of_nozzles(area_ratio):
    critical = criticals(area_ratio=area_ratio)
    middle = 0.5 * (critical.first_critical + critical.second_critical)
    located = nozzle.shock_area_ratio(area_ratio, middle, gas()).unwrap()
    assert 1.0 < located.area_ratio_shock < area_ratio
