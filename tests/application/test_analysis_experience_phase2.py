"""Analysis Experience Phase 2: the views read what was solved, and solve nothing.

Two defects shaped these tests, both found by looking at the running page:

* A QML binding re-reads a *property* when its signal fires, but never re-calls
  a *slot*. The Nozzle Lab drawing, its guides, the regime-map shock curve and
  the Isentropic relation curve were all bound to slot calls, so each kept the
  previous solve on screen -- a stale shock drawn in a shock-free nozzle, a
  curve for the old area ratio -- while every number beside it was current.
* A slot called from a binding runs whenever a view is created, so opening a
  page re-ran physics: the regime map's 80-point shock sweep, the Isentropic
  reference check, the Rocket Performance identity checks.

The fixes publish the same data as properties, computed with the solve. These
tests hold both halves: the property equals what the slot returns, it follows
every solve, and reading it -- as a view does -- costs no solve.
"""

from __future__ import annotations

import math
import pathlib
import re

import pytest

from rocketforge.application.analysis import isentropic_controller as isentropic_module
from rocketforge.application.analysis import nozzle_controller as nozzle_module
from rocketforge.application.analysis import performance_service
from rocketforge.application.analysis.isentropic_controller import IsentropicController
from rocketforge.application.analysis.nozzle_controller import NozzleController
from rocketforge.application.analysis.performance_controller import (
    RocketPerformanceController,
)
from rocketforge.application.analysis.thermochemistry_controller import (
    LEADING_SPECIES,
    ThermochemistryController,
)
from rocketforge.application.analysis.thermochemistry_service import species_rows
from rocketforge.application.formatting import format_engineering

UI = pathlib.Path(__file__).resolve().parents[2] / "ui"


class _Counter:
    """Wrap a function, count its calls, call through."""

    def __init__(self, original):
        self.original = original
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.original(*args, **kwargs)


# ===========================================================================
# Nozzle Lab
# ===========================================================================


@pytest.fixture()
def nozzle(qt_app):
    return NozzleController()


def _assert_nozzle_properties_match_slots(controller):
    assert controller.contour == controller.contourSeries()
    assert controller.stationMarkers == controller.markers()
    for quantity in controller.chartQuantities:
        assert controller.distribution[quantity["key"]] == controller.series(quantity["key"])


def test_nozzle_presentation_properties_are_the_slots_results(nozzle):
    _assert_nozzle_properties_match_slots(nozzle)
    assert nozzle.shockCurve == nozzle.shockPositionSeries()


@pytest.mark.parametrize("name, value", [("backPressureRatio", 0.8),
                                         ("backPressureRatio", 0.05),
                                         ("areaRatio", 3.0),
                                         ("gamma", 1.3)])
def test_nozzle_presentation_properties_follow_every_solve(nozzle, name, value):
    before = nozzle.stationMarkers
    setattr(nozzle, name, value)
    _assert_nozzle_properties_match_slots(nozzle)
    assert nozzle.shockCurve == nozzle.shockPositionSeries()
    assert nozzle.stationMarkers != before or name == "gamma"


def test_a_shock_free_operating_point_has_no_shock_station(nozzle):
    nozzle.backPressureRatio = 0.05
    assert not nozzle.hasShock
    assert [m["label"] for m in nozzle.stationMarkers] == ["throat"]


def test_the_regime_map_is_solved_with_the_nozzle_not_with_the_view(nozzle, monkeypatch):
    sweep = _Counter(nozzle_module.shock_position_sweep)
    criticals = _Counter(nozzle_module.thresholds)
    monkeypatch.setattr(nozzle_module, "shock_position_sweep", sweep)
    monkeypatch.setattr(nozzle_module, "thresholds", criticals)

    # Reading, as every view binding does: no solve at all.
    for _ in range(5):
        nozzle.shockCurve, nozzle.regimeBands, nozzle.firstCritical
        nozzle.secondCritical, nozzle.thirdCritical, nozzle.designExitMach
        nozzle.contour, nozzle.stationMarkers, nozzle.distribution
    assert (sweep.calls, criticals.calls) == (0, 0)

    # The back pressure does not move the map: not re-solved.
    nozzle.backPressureRatio = 0.6
    assert (sweep.calls, criticals.calls) == (0, 0)

    # The nozzle does: solved once, with the operating point.
    nozzle.areaRatio = 2.5
    assert (sweep.calls, criticals.calls) == (1, 1)
    inputs = nozzle._inputs()
    assert nozzle.firstCritical == nozzle_module.thresholds.original(inputs)["first_critical"]


# ===========================================================================
# Isentropic
# ===========================================================================


@pytest.fixture()
def isentropic(qt_app):
    return IsentropicController()


def test_isentropic_chart_data_is_the_generated_table(isentropic):
    keys = [c["key"] for c in isentropic.tableColumns if c["key"] != "mach"]
    assert sorted(isentropic.chartData) == sorted(keys)
    for key in keys:
        assert isentropic.chartData[key] == isentropic.chartSeries(key)


def test_the_plotted_gamma_is_the_generated_tables_not_the_setting(isentropic):
    assert isentropic.plottedGamma == 1.4
    isentropic.tableGamma = 1.3                 # edited, not generated
    assert isentropic.plottedGamma == 1.4
    isentropic.regenerateTable()
    assert isentropic.plottedGamma == 1.3
    assert isentropic.chartData["p0_over_p"] == isentropic.chartSeries("p0_over_p")


def test_the_reference_check_is_made_with_the_result(isentropic, monkeypatch):
    assert isentropic.currentMachComparison == isentropic.comparisonForCurrentMach()
    compare = _Counter(isentropic_module.reference.compare_row)
    monkeypatch.setattr(isentropic_module.reference, "compare_row", compare)
    for _ in range(5):
        isentropic.currentMachComparison
    assert compare.calls == 0                   # reading solves nothing
    isentropic.inputValue = 3.0
    assert compare.calls == 1                   # the solve makes it, once
    assert isentropic.currentMachComparison == isentropic.comparisonForCurrentMach()


def test_both_branch_roots_carry_their_values(isentropic):
    isentropic.mode = "area_ratio"
    isentropic.inputValue = 2.0
    isentropic.branch = "both"
    rows = isentropic.bothBranches
    assert len(rows) == 2
    subsonic, supersonic = isentropic._result.both
    assert rows[0]["raw"] == subsonic and rows[1]["raw"] == supersonic
    assert rows[0]["value"] == format_engineering(subsonic, isentropic.precision)


# ===========================================================================
# Rocket Performance
# ===========================================================================


@pytest.fixture()
def performance(qt_app, stub_gateway):
    thermo = ThermochemistryController()
    controller = RocketPerformanceController(thermo)
    thermo.calculate()
    return controller


def test_identity_checks_run_once_per_outcome(performance, monkeypatch):
    identities = _Counter(performance_service.identity_rows)
    monkeypatch.setattr(performance_service, "identity_rows", identities)
    performance.calculate()
    assert performance.hasResult, performance.message
    after_solve = identities.calls
    assert after_solve == 1
    for _ in range(5):                          # the Model view reading them
        performance.identitySummary, performance.identitiesPassed, performance.identityRows
    assert identities.calls == after_solve
    rows = identities.original(performance._outcome)
    assert performance.identitiesPassed == (bool(rows) and all(r["passed"] for r in rows))
    performance.calculate()                     # a new outcome: checked again
    assert identities.calls == after_solve + 1


def test_a_stale_edit_does_not_re_solve_the_reference_conditions(performance, monkeypatch):
    """The oracle table re-read on the stale signal must not re-solve the nozzle."""
    conditions = _Counter(performance_service.reference_condition_results)
    monkeypatch.setattr(performance_service, "reference_condition_results", conditions)
    performance.calculate()
    assert performance.hasResult, performance.message
    after_solve = conditions.calls
    assert after_solve == 1
    performance.areaRatio = performance.areaRatio + 5.0        # an edit, no Calculate
    assert performance.resultStale
    performance.oracleComparisonRows
    upstream = performance._source
    upstream.mixtureRatio = upstream.mixtureRatio + 0.25       # an upstream edit
    performance.oracleComparisonRows
    assert conditions.calls == after_solve
    performance.calculate()                                    # a new outcome
    assert conditions.calls == after_solve + 1


# ===========================================================================
# Thermochemistry
# ===========================================================================


@pytest.fixture()
def thermo(qt_app, stub_gateway):
    return ThermochemistryController()


def test_no_leading_species_before_a_solve(thermo):
    assert thermo.leadingSpecies["rows"] == []
    assert thermo.leadingSpecies["shown"] == 0


def test_leading_species_are_the_solved_sets_own_order(thermo):
    thermo.calculate()
    assert thermo.hasResult
    expected = species_rows(thermo._outcome)[:LEADING_SPECIES]
    leading = thermo.leadingSpecies
    assert [r["name"] for r in leading["rows"]] == [r.name for r in expected]
    assert [r["fraction"] for r in leading["rows"]] == [r.mole_fraction for r in expected]
    assert leading["total"] == len(species_rows(thermo._outcome))
    assert leading["sumText"] == format_engineering(
        math.fsum(r.mole_fraction for r in expected), thermo.precision)


def test_leading_species_ignore_the_composition_views_settings(thermo):
    thermo.calculate()
    before = thermo.leadingSpecies
    thermo.speciesFilter = "zzz-no-such-species"
    thermo.compositionBasis = "mass"
    thermo.traceThresholdIndex = len(thermo.traceThresholds) - 1
    assert thermo.leadingSpecies == before


# ===========================================================================
# the stale-view defect class, guarded at the source
# ===========================================================================

#: Slot calls that once sat in bindings and froze a view on an earlier solve.
#: Each has a property now; the slot stays for scripts and tests.
_SLOT_BINDINGS = (
    r"Nozzle\.contourSeries\(\)",
    r"Nozzle\.markers\(\)",
    r"Nozzle\.shockPositionSeries\(\)",
    r"Nozzle\.shockAxialSeries\(\)",
    r"Nozzle\.series\(",
    r"Isentropic\.chartSeries\(",
    r"Isentropic\.comparisonForCurrentMach\(\)",
)


def test_no_view_binds_a_solved_quantity_through_a_slot():
    offenders = []
    for path in sorted(UI.rglob("*.qml")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("//", 1)[0]
            for pattern in _SLOT_BINDINGS:
                if re.search(pattern, code):
                    offenders.append(f"{path.relative_to(UI)}:{number}: {line.strip()}")
    assert offenders == [], "\n".join(offenders)


# ===========================================================================
# the Isentropic column contract (Analysis Experience Phase 2 visual closure)
# ===========================================================================


@pytest.mark.parametrize("convention", ["anderson", "standard"])
def test_the_isentropic_columns_are_distinct_quantities(convention):
    """Two headers once read as "p0/p" twice. The model never said so."""
    from rocketforge.application.analysis.isentropic_service import columns_for

    columns = columns_for(convention)
    keys = [c.key for c in columns]
    labels = [c.label for c in columns]
    assert len(set(keys)) == len(keys)
    assert len(set(labels)) == len(labels)
    pressure = [c for c in columns if c.key.startswith("p")]
    density = [c for c in columns if c.key.startswith("rho")]
    assert len(pressure) == 1 and len(density) == 1
    assert "p" in pressure[0].label and "ρ" not in pressure[0].label
    assert "ρ" in density[0].label and "p" not in density[0].label


def test_every_plotted_column_has_a_word_of_its_own(isentropic):
    """The words the headers and the selector show come from the backend."""
    captions = {m["key"]: m["label"] for m in isentropic.solveModes}
    plotted = [c["key"] for c in isentropic.tableColumns]
    words = [captions.get(key, "") for key in plotted]
    assert all(words), dict(zip(plotted, words))
    assert len(set(words)) == len(words)
