"""Every regime a C-D nozzle can be in, and the boundaries between them.

``03`` section 10.5 and the task's regime matrix. Classification is by
threshold, never by whether a root solve happened to converge, so each of these
tests names a back pressure and asserts the regime that back pressure defines.
"""

from __future__ import annotations

import numpy as np
import pytest

from rocketforge.core.errors import InputError
from rocketforge.core.result import Severity, Status
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import nozzle
from rocketforge.physics.compressible.types import NozzleRegime

AREA_RATIO = 2.0
GAMMAS = (1.2, 1.3, 1.4, 1.66)


def gas(gamma: float = 1.4) -> PerfectGas:
    return PerfectGas(gamma=gamma, gas_constant=287.05)


def criticals(gamma: float = 1.4, area_ratio: float = AREA_RATIO):
    return nozzle.critical_pressure_ratios(area_ratio, gas(gamma)).unwrap()


def regime_at(back: float, gamma: float = 1.4,
              area_ratio: float = AREA_RATIO) -> NozzleRegime:
    return nozzle.classify(area_ratio, back, gas(gamma)).unwrap().regime


# ---------------------------------------------------------------------------
# the eight cases of the matrix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_back_pressure_at_the_stagnation_pressure_is_not_a_regime(gamma):
    """pb = p0 means no flow, and no flow is not an operating regime."""
    with pytest.raises(InputError, match="no flow"):
        nozzle.classify(AREA_RATIO, 1.0, gas(gamma))


@pytest.mark.parametrize("gamma", GAMMAS)
def test_back_pressure_above_the_stagnation_pressure_is_refused(gamma):
    """The nozzle is not quietly run backwards."""
    with pytest.raises(InputError, match="backwards"):
        nozzle.classify(AREA_RATIO, 1.5, gas(gamma))


@pytest.mark.parametrize("gamma", GAMMAS)
def test_just_below_the_stagnation_pressure_the_nozzle_is_unchoked(gamma):
    assert regime_at(0.999, gamma) is NozzleRegime.UNCHOKED_SUBSONIC


@pytest.mark.parametrize("gamma", GAMMAS)
def test_above_the_first_critical_the_nozzle_is_unchoked(gamma):
    first = criticals(gamma).first_critical
    assert regime_at(first + 1e-3, gamma) is NozzleRegime.UNCHOKED_SUBSONIC


@pytest.mark.parametrize("gamma", GAMMAS)
def test_at_the_first_critical_the_throat_is_just_sonic(gamma):
    first = criticals(gamma).first_critical
    assert regime_at(first, gamma) is NozzleRegime.CHOKED_SUBSONIC_EXIT


@pytest.mark.parametrize("gamma", GAMMAS)
def test_just_below_the_first_critical_a_shock_appears_near_the_throat(gamma):
    first = criticals(gamma).first_critical
    result = nozzle.classify(AREA_RATIO, first - 1e-4, gas(gamma)).unwrap()
    assert result.regime is NozzleRegime.INTERNAL_NORMAL_SHOCK
    assert result.shock is not None
    assert result.shock.area_ratio_shock < 1.05


@pytest.mark.parametrize("gamma", GAMMAS)
def test_between_the_criticals_the_shock_stands_inside_the_nozzle(gamma):
    critical = criticals(gamma)
    middle = 0.5 * (critical.first_critical + critical.second_critical)
    result = nozzle.classify(AREA_RATIO, middle, gas(gamma)).unwrap()
    assert result.regime is NozzleRegime.INTERNAL_NORMAL_SHOCK
    assert 1.0 < result.shock.area_ratio_shock < AREA_RATIO


@pytest.mark.parametrize("gamma", GAMMAS)
def test_just_above_the_second_critical_the_shock_is_nearly_at_the_exit(gamma):
    critical = criticals(gamma)
    result = nozzle.classify(AREA_RATIO, critical.second_critical + 1e-6,
                             gas(gamma)).unwrap()
    assert result.regime is NozzleRegime.INTERNAL_NORMAL_SHOCK
    assert result.shock.area_ratio_shock == pytest.approx(AREA_RATIO, rel=1e-4)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_at_the_second_critical_the_shock_stands_in_the_exit_plane(gamma):
    critical = criticals(gamma)
    result = nozzle.classify(AREA_RATIO, critical.second_critical, gas(gamma)).unwrap()
    assert result.regime is NozzleRegime.SHOCK_AT_EXIT
    assert result.shock.area_ratio_shock == AREA_RATIO


@pytest.mark.parametrize("gamma", GAMMAS)
def test_just_below_the_second_critical_there_is_no_internal_shock(gamma):
    """The single most important discrimination this module makes."""
    critical = criticals(gamma)
    result = nozzle.classify(AREA_RATIO, critical.second_critical - 1e-6,
                             gas(gamma)).unwrap()
    assert result.regime is NozzleRegime.OVEREXPANDED
    assert result.shock is None


@pytest.mark.parametrize("gamma", GAMMAS)
def test_at_the_third_critical_the_nozzle_is_ideally_expanded(gamma):
    critical = criticals(gamma)
    result = nozzle.classify(AREA_RATIO, critical.third_critical, gas(gamma)).unwrap()
    assert result.regime is NozzleRegime.IDEALLY_EXPANDED
    assert result.pressure_ratio_exit == pytest.approx(result.pressure_ratio_back,
                                                       rel=1e-12)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_below_the_third_critical_the_nozzle_is_underexpanded(gamma):
    critical = criticals(gamma)
    result = nozzle.classify(AREA_RATIO, 0.5 * critical.third_critical,
                             gas(gamma)).unwrap()
    assert result.regime is NozzleRegime.UNDEREXPANDED
    assert result.shock is None
    assert result.pressure_ratio_exit > result.pressure_ratio_back


# ---------------------------------------------------------------------------
# what each regime claims about the exit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_matched_regimes_put_the_exit_pressure_on_the_back_pressure(gamma):
    """Unchoked, internal shock and shock-at-exit all satisfy pe = pb."""
    critical = criticals(gamma)
    backs = (0.99,
             0.5 * (critical.first_critical + 1.0),
             0.5 * (critical.first_critical + critical.second_critical),
             critical.second_critical)
    for back in backs:
        result = nozzle.classify(AREA_RATIO, back, gas(gamma)).unwrap()
        assert result.pressure_ratio_exit == pytest.approx(back, rel=1e-9), result.regime


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_unmatched_regimes_do_not_force_the_exit_onto_the_back_pressure(gamma):
    """Overexpanded and underexpanded exits are *not* matched, and must not pretend."""
    critical = criticals(gamma)
    over = 0.5 * (critical.second_critical + critical.third_critical)
    under = 0.5 * critical.third_critical
    over_result = nozzle.classify(AREA_RATIO, over, gas(gamma)).unwrap()
    under_result = nozzle.classify(AREA_RATIO, under, gas(gamma)).unwrap()
    assert over_result.pressure_ratio_exit < over_result.pressure_ratio_back
    assert under_result.pressure_ratio_exit > under_result.pressure_ratio_back
    assert over_result.pressure_ratio_exit == pytest.approx(critical.third_critical)
    assert under_result.pressure_ratio_exit == pytest.approx(critical.third_critical)


@pytest.mark.parametrize("gamma", GAMMAS)
def test_the_three_supersonic_regimes_share_one_exit_state(gamma):
    """They differ only outside the exit plane, which this model does not compute."""
    critical = criticals(gamma)
    machs = set()
    for back in (0.5 * (critical.second_critical + critical.third_critical),
                 critical.third_critical,
                 0.5 * critical.third_critical):
        machs.add(nozzle.classify(AREA_RATIO, back, gas(gamma)).unwrap().mach_exit)
    assert len(machs) == 1
    assert machs.pop() == pytest.approx(critical.mach_exit_supersonic)


# ---------------------------------------------------------------------------
# diagnostics: what the user is told
# ---------------------------------------------------------------------------


def test_the_unchoked_regime_says_it_is_not_choked():
    result = nozzle.classify(AREA_RATIO, 0.99, gas())
    assert any(d.code == "NOT_CHOKED" for d in result.diagnostics)


def test_overexpansion_reports_external_compression():
    critical = criticals()
    back = 0.5 * (critical.second_critical + critical.third_critical)
    result = nozzle.classify(AREA_RATIO, back, gas())
    assert any(d.code == "EXTERNAL_COMPRESSION" for d in result.diagnostics)


def test_underexpansion_reports_external_expansion():
    result = nozzle.classify(AREA_RATIO, 0.5 * criticals().third_critical, gas())
    assert any(d.code == "EXTERNAL_EXPANSION" for d in result.diagnostics)


def test_severe_overexpansion_flags_separation_without_predicting_it():
    """The flag is a presentation choice; the message says so."""
    critical = nozzle.critical_pressure_ratios(10.0, gas()).unwrap()
    back = 0.5 * (critical.second_critical + critical.third_critical)
    result = nozzle.classify(10.0, back, gas())
    flags = [d for d in result.diagnostics if d.code == "MODEL_LIMIT_SEPARATION"]
    assert flags, "a strongly overexpanded nozzle must carry the separation flag"
    assert flags[0].severity is Severity.WARNING
    assert "does not predict" in flags[0].message
    assert result.status is Status.OK_WITH_WARNINGS


def test_a_mild_overexpansion_carries_no_separation_flag():
    """Mild means *close to design*, which is just above the third critical.

    Overexpansion is most severe at the second critical, where pe/pb is
    smallest, and vanishes as the back pressure falls to the design value.
    """
    critical = criticals()
    back = critical.third_critical * 1.05
    result = nozzle.classify(AREA_RATIO, back, gas())
    assert result.unwrap().regime is NozzleRegime.OVEREXPANDED
    assert not any(d.code == "MODEL_LIMIT_SEPARATION" for d in result.diagnostics)


def test_the_separation_flag_follows_the_severity_of_the_overexpansion():
    """It fires near the shock-at-exit end and clears as the design point nears."""
    critical = criticals()
    severe = nozzle.classify(AREA_RATIO, critical.second_critical - 1e-3, gas())
    mild = nozzle.classify(AREA_RATIO, critical.third_critical * 1.05, gas())
    assert any(d.code == "MODEL_LIMIT_SEPARATION" for d in severe.diagnostics)
    assert not any(d.code == "MODEL_LIMIT_SEPARATION" for d in mild.diagnostics)


def test_an_operating_point_near_a_boundary_is_told_so():
    critical = criticals()
    result = nozzle.classify(AREA_RATIO, critical.second_critical + 1e-8, gas())
    assert any(d.code == "NEAR_REGIME_BOUNDARY" for d in result.diagnostics)


# ---------------------------------------------------------------------------
# determinism and honesty about the input
# ---------------------------------------------------------------------------


def test_the_requested_back_pressure_is_never_clamped_onto_a_boundary():
    critical = criticals()
    back = critical.second_critical + 1e-8
    result = nozzle.classify(AREA_RATIO, back, gas()).unwrap()
    assert result.pressure_ratio_back == back


def test_classification_is_deterministic():
    """The same float64 in, the same regime out. Every time."""
    backs = np.linspace(0.01, 0.99, 200)
    first = [regime_at(float(b)) for b in backs]
    second = [regime_at(float(b)) for b in backs]
    assert first == second


def test_every_regime_is_reachable_on_one_sweep():
    """No regime may hide inside a generic 'choked'."""
    critical = criticals()
    backs = [0.99,
             critical.first_critical,
             0.5 * (critical.first_critical + critical.second_critical),
             critical.second_critical,
             0.5 * (critical.second_critical + critical.third_critical),
             critical.third_critical,
             0.5 * critical.third_critical]
    seen = {regime_at(b) for b in backs}
    assert seen == set(NozzleRegime)


def test_the_regime_sequence_is_monotone_in_back_pressure():
    """Descending back pressure walks the seven regimes in order, once each."""
    order = [NozzleRegime.UNCHOKED_SUBSONIC, NozzleRegime.CHOKED_SUBSONIC_EXIT,
             NozzleRegime.INTERNAL_NORMAL_SHOCK, NozzleRegime.SHOCK_AT_EXIT,
             NozzleRegime.OVEREXPANDED, NozzleRegime.IDEALLY_EXPANDED,
             NozzleRegime.UNDEREXPANDED]
    critical = criticals()
    backs = np.concatenate([
        np.linspace(0.99, critical.first_critical + 1e-6, 20),
        [critical.first_critical],
        np.linspace(critical.first_critical - 1e-6, critical.second_critical + 1e-6, 40),
        [critical.second_critical],
        np.linspace(critical.second_critical - 1e-6, critical.third_critical + 1e-9, 20),
        [critical.third_critical],
        np.linspace(critical.third_critical - 1e-9, 1e-4, 10),
    ])
    positions = [order.index(regime_at(float(b))) for b in backs]
    assert positions == sorted(positions)
