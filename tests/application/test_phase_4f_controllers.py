"""The nozzle service and controller: input modes, presets and stale state.

The physics is tested next door. What is tested here is everything the
interface can do *to* it -- switching how a pressure is stated, pressing a
threshold preset, walking from one regime into another -- and the single
property that matters most on this page: when the shock goes, everything about
it goes with it.
"""

from __future__ import annotations

import sys

import numpy as np
import pytest
from PySide6.QtGui import QGuiApplication

from rocketforge.application.analysis import nozzle_service as svc
from rocketforge.application.analysis.nozzle_controller import NozzleController
from rocketforge.physics.compressible.types import NozzleRegime


@pytest.fixture(scope="session")
def qt_app():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    yield app


@pytest.fixture()
def controller(qt_app):
    return NozzleController()


def thresholds(inputs: svc.NozzleInputs) -> dict:
    return svc.thresholds(inputs)


# ---------------------------------------------------------------------------
# the service
# ---------------------------------------------------------------------------


def test_the_service_solves_a_nozzle_and_names_its_regime():
    result = svc.solve(svc.NozzleInputs(back_pressure=7.0e5))
    assert result.ok
    assert result.branch_used == NozzleRegime.INTERNAL_NORMAL_SHOCK.value
    assert result.value_of("mass_flow") > 0.0


def test_the_service_reports_invalid_input_rather_than_raising():
    result = svc.solve(svc.NozzleInputs(back_pressure=2.0e6))
    assert not result.ok
    assert result.status == "invalid"
    assert "backwards" in result.message or "no flow" in result.message


def test_the_service_reports_an_impossible_geometry():
    result = svc.solve(svc.NozzleInputs(area_ratio_exit=1.0))
    assert not result.ok


def test_shock_rows_appear_only_when_a_shock_does():
    with_shock = svc.solve(svc.NozzleInputs(back_pressure=7.0e5))
    without = svc.solve(svc.NozzleInputs(back_pressure=1.0e5))
    assert any(row.key == "shock_area_ratio" for row in with_shock.rows)
    assert not any(row.key.startswith("shock") for row in without.rows)


def test_the_regime_bands_are_the_computed_criticals():
    inputs = svc.NozzleInputs()
    bands = svc.regime_bands(inputs)
    values = thresholds(inputs)
    by_key = {b["key"]: b for b in bands}
    assert by_key["unchoked_subsonic"]["from"] == values["first_critical"]
    assert by_key["internal_normal_shock"]["to"] == values["first_critical"]
    assert by_key["internal_normal_shock"]["from"] == values["second_critical"]
    assert by_key["overexpanded"]["from"] == values["third_critical"]


def test_the_ideal_band_is_a_point_and_says_so():
    """A zero-width band is the truth; widening it would be a lie."""
    bands = {b["key"]: b for b in svc.regime_bands(svc.NozzleInputs())}
    assert bands["ideally_expanded"]["point"] is True
    assert bands["ideally_expanded"]["from"] == bands["ideally_expanded"]["to"]
    assert bands["overexpanded"]["point"] is False


def test_the_bands_tile_the_axis_without_gaps():
    bands = svc.regime_bands(svc.NozzleInputs())
    edges = sorted({b["from"] for b in bands} | {b["to"] for b in bands})
    assert edges[0] == 0.0
    assert edges[-1] == 1.0


def test_the_back_pressure_sweep_visits_every_regime():
    seen = {point["regime"] for point in svc.back_pressure_sweep(svc.NozzleInputs(), 200)}
    assert seen == {r.value for r in NozzleRegime}


def test_the_shock_sweep_is_monotone_and_uses_the_real_solver():
    points = svc.shock_position_sweep(svc.NozzleInputs(), 40)
    assert len(points) > 10
    ratios = [p["area_ratio_shock"] for p in points]
    positions = [p["x"] for p in points]
    assert np.all(np.diff(ratios) < 0.0)      # ascending pb moves it upstream
    assert np.all(np.diff(positions) < 0.0)


def test_the_distribution_table_marks_throat_shock_and_exit():
    data = svc.distribution_table(svc.NozzleInputs(back_pressure=7.0e5))
    labels = set(data.markers.values())
    assert labels == {"THROAT · SONIC", "PRE SHOCK", "POST SHOCK", "EXIT"}


def test_the_unchoked_throat_is_not_labelled_sonic():
    """``122``: a subsonic throat must not claim to be sonic."""
    data = svc.distribution_table(svc.NozzleInputs(back_pressure=9.9e5))
    assert "THROAT" in data.markers.values()
    assert "THROAT · SONIC" not in data.markers.values()


def test_the_normalized_table_swaps_columns_without_a_second_solve():
    dimensional = svc.distribution_table(svc.NozzleInputs(), normalized=False)
    normalized = svc.distribution_table(svc.NozzleInputs(), normalized=True)
    assert [c.key for c in normalized.columns] != [c.key for c in dimensional.columns]
    assert normalized.values.shape[0] == dimensional.values.shape[0]
    assert "p/p₀₁" in [c.label for c in normalized.columns]


# ---------------------------------------------------------------------------
# input modes
# ---------------------------------------------------------------------------


def test_the_two_pressure_modes_describe_the_same_pressure(controller):
    controller.setProperty("backPressureRatio", 0.6)
    assert controller.property("backPressure") == pytest.approx(0.6e6)
    controller.setProperty("backPressure", 3.0e5)
    assert controller.property("backPressureRatio") == pytest.approx(0.3)


def test_switching_pressure_mode_does_not_move_the_operating_point(controller):
    controller.setProperty("backPressureRatio", 0.42)
    before = controller.property("backPressure")
    regime = controller.property("regime")
    controller.setProperty("pressureMode", "absolute")
    assert controller.property("backPressure") == before
    assert controller.property("regime") == regime


def test_the_two_area_modes_describe_the_same_nozzle(controller):
    controller.setProperty("throatArea", 0.02)
    controller.setProperty("areaRatio", 3.0)
    assert controller.property("exitArea") == pytest.approx(0.06)
    controller.setProperty("exitArea", 0.08)
    assert controller.property("areaRatio") == pytest.approx(4.0)


def test_raising_the_reservoir_pressure_holds_the_ratio_when_the_ratio_was_typed(controller):
    controller.setProperty("pressureMode", "ratio")
    controller.setProperty("backPressureRatio", 0.5)
    controller.setProperty("stagnationPressure", 4.0e6)
    assert controller.property("backPressureRatio") == pytest.approx(0.5)
    assert controller.property("backPressure") == pytest.approx(2.0e6)


def test_raising_the_reservoir_pressure_holds_the_pressure_when_it_was_typed(controller):
    controller.setProperty("pressureMode", "absolute")
    controller.setProperty("backPressure", 5.0e5)
    controller.setProperty("stagnationPressure", 4.0e6)
    assert controller.property("backPressure") == pytest.approx(5.0e5)


@pytest.mark.parametrize("value", ["", "-", ".", "1e", "abc", None])
def test_a_half_typed_number_is_ignored_rather_than_crashing(controller, value):
    before = controller.property("areaRatio")
    controller.setProperty("areaRatio", value)
    assert controller.property("areaRatio") == before
    assert controller.property("valid")


def test_an_impossible_area_ratio_is_refused_without_breaking_the_page(controller):
    controller.setProperty("areaRatio", 0.5)
    assert controller.property("areaRatio") == 2.0
    assert controller.property("valid")


# ---------------------------------------------------------------------------
# presets
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("preset,regime", [
    ("choking", NozzleRegime.CHOKED_SUBSONIC_EXIT),
    ("shock_exit", NozzleRegime.SHOCK_AT_EXIT),
    ("ideal", NozzleRegime.IDEALLY_EXPANDED),
])
def test_a_preset_lands_exactly_on_its_boundary_regime(controller, preset, regime):
    """``116``, ``135``: the boundary regimes are reachable by a click."""
    controller.applyPreset(preset)
    assert controller.property("regime") == regime.value


def test_a_preset_uses_the_computed_threshold_rather_than_a_constant(controller):
    controller.setProperty("areaRatio", 3.7)
    controller.applyPreset("ideal")
    assert controller.property("backPressureRatio") == pytest.approx(
        controller.property("thirdCritical"), rel=1e-12)


def test_an_unknown_preset_changes_nothing(controller):
    before = controller.property("backPressure")
    controller.applyPreset("nonsense")
    assert controller.property("backPressure") == before


# ---------------------------------------------------------------------------
# no stale state
# ---------------------------------------------------------------------------


def test_leaving_the_shock_regime_clears_every_trace_of_the_shock(controller):
    """``132``: the single most important state rule on this page."""
    controller.setProperty("backPressureRatio", 0.7)
    assert controller.property("hasShock")
    assert any(row["key"] == "shock_area_ratio" for row in controller.property("results"))
    assert controller.property("preShockRow") >= 0
    assert any(m["label"] == "shock" for m in controller.markers())

    controller.setProperty("backPressureRatio", 0.3)
    assert controller.property("regime") == NozzleRegime.OVEREXPANDED.value
    assert not controller.property("hasShock")
    assert not any(row["key"].startswith("shock")
                   for row in controller.property("results"))
    assert controller.property("preShockRow") == -1
    assert controller.property("postShockRow") == -1
    assert not any(m["label"] == "shock" for m in controller.markers())
    assert "PRE SHOCK" not in controller.property("rowMarkers").values()


def test_going_from_a_shock_to_an_unchoked_nozzle_clears_it_too(controller):
    controller.setProperty("backPressureRatio", 0.7)
    choked_flow = controller.rawValue("mass_flow")
    controller.setProperty("backPressureRatio", 0.99)
    assert controller.property("regime") == NozzleRegime.UNCHOKED_SUBSONIC.value
    assert not controller.property("hasShock")
    assert not controller.property("choked")
    assert controller.rawValue("mach_throat") < 1.0
    assert controller.rawValue("mass_flow") < choked_flow


def test_walking_across_the_ideal_point_changes_only_the_label(controller):
    """``134``: the internal solution is the same on both sides."""
    controller.setProperty("areaRatio", 2.0)
    third = controller.property("thirdCritical")

    controller.setProperty("backPressureRatio", third * 1.5)
    over = np.array([p["y"] for p in controller.series("mach")[0]["points"]])
    over_regime = controller.property("regime")

    controller.setProperty("backPressureRatio", third * 0.5)
    under = np.array([p["y"] for p in controller.series("mach")[0]["points"]])
    under_regime = controller.property("regime")

    assert over_regime == NozzleRegime.OVEREXPANDED.value
    assert under_regime == NozzleRegime.UNDEREXPANDED.value
    assert np.array_equal(over, under)


def test_the_external_context_appears_only_where_it_applies(controller):
    controller.applyPreset("ideal")
    assert controller.property("externalContext") == ""
    controller.setProperty("backPressureRatio",
                           controller.property("thirdCritical") * 0.5)
    assert "expansion fans" in controller.property("externalContext").lower()
    controller.setProperty("backPressureRatio",
                           controller.property("thirdCritical") * 1.5)
    assert "oblique shocks" in controller.property("externalContext").lower()


def test_changing_the_geometry_moves_the_thresholds_and_the_regime(controller):
    controller.setProperty("backPressureRatio", 0.2)
    before = controller.property("regime")
    controller.setProperty("areaRatio", 8.0)
    assert controller.property("regime") != before
    assert controller.property("thirdCritical") < 0.02


# ---------------------------------------------------------------------------
# the distribution the page shows
# ---------------------------------------------------------------------------


def test_the_series_are_split_at_the_shock_and_joined_without_one(controller):
    """``49``, ``142``: the jump is drawn as a jump, not interpolated across."""
    controller.setProperty("backPressureRatio", 0.7)
    split = controller.series("pressure")
    assert len(split) == 2
    assert {s["label"] for s in split} == {"upstream", "downstream"}
    assert split[0]["points"][-1]["x"] == split[1]["points"][0]["x"]
    assert split[1]["points"][0]["y"] > split[0]["points"][-1]["y"]

    controller.setProperty("backPressureRatio", 0.05)
    assert len(controller.series("pressure")) == 1


def test_the_station_inspector_returns_one_row_per_column(controller):
    controller.setProperty("backPressureRatio", 0.7)
    station = controller.stationAt(controller.property("throatRow"))
    assert len(station) == len(controller.property("tableColumns"))
    mach = next(row for row in station if row["key"] == "mach")
    assert mach["value"] == pytest.approx(1.0)


def test_an_out_of_range_station_is_empty_rather_than_an_error(controller):
    assert controller.stationAt(-1) == []
    assert controller.stationAt(10 ** 6) == []


def test_the_contour_is_two_mirrored_walls(controller):
    contour = controller.contourSeries()
    assert [s["label"] for s in contour] == ["wall", "mirror"]
    upper = np.array([p["y"] for p in contour[0]["points"]])
    lower = np.array([p["y"] for p in contour[1]["points"]])
    assert np.allclose(upper, -lower)
    assert upper.min() > 0.0


def test_the_resolution_is_guarded_at_both_ends(controller):
    controller.setProperty("resolution", 5)
    assert controller.property("resolution") == 11
    controller.setProperty("resolution", 10 ** 7)
    assert controller.property("resolution") == controller.property("maxResolution")


def test_the_table_follows_the_resolution(controller):
    controller.setProperty("resolution", 61)
    small = controller.property("rowCount")
    controller.setProperty("resolution", 241)
    assert controller.property("rowCount") > small


# ---------------------------------------------------------------------------
# validation panel
# ---------------------------------------------------------------------------


def test_the_page_says_there_is_no_published_nozzle_table(controller):
    assert not controller.property("referenceAvailable")
    assert "no nozzle appendix" in controller.property("referenceMessage")
    assert controller.property("validationStatus") == "PASS"


def test_the_validation_panel_names_its_checks(controller):
    checks = controller.property("validationChecks")
    assert len(checks) >= 5
    assert any("rediscovers" in c["name"] for c in checks)
    assert any(c["status"] == "NOTE" for c in checks), (
        "the specification erratum should be reported, not hidden")
