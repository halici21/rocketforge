"""The Qt bridge for the Fanno and Rayleigh pages.

These need a QGuiApplication but no window and no QML. What they check is that
the interface is handed correct, complete state -- and, just as importantly,
that nothing stale survives a change of mode, convention, gamma or range.

Two of these tests exist because of the two mistakes this phase most had to
avoid. The friction-convention test guards the factor of four between Darcy and
Fanning; the critical-point test guards the difference between the static and
stagnation temperature maxima, which sit at different Mach numbers and mean
different things.
"""

from __future__ import annotations

import math
import sys

import pytest
from PySide6.QtGui import QGuiApplication

from rocketforge.application.analysis.fanno_controller import FannoController
from rocketforge.application.analysis.isentropic_controller import IsentropicController
from rocketforge.application.analysis.mass_flow_controller import MassFlowController
from rocketforge.application.analysis.normal_shock_controller import NormalShockController
from rocketforge.application.analysis.oblique_shock_controller import ObliqueShockController
from rocketforge.application.analysis.prandtl_meyer_controller import PrandtlMeyerController
from rocketforge.application.analysis.rayleigh_controller import RayleighController
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import fanno, rayleigh

AIR = PerfectGas(gamma=1.4)


@pytest.fixture(scope="session")
def qt_app():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    yield app


@pytest.fixture()
def duct(qt_app):
    return FannoController()


@pytest.fixture()
def heat(qt_app):
    return RayleighController()


def value_of(rows, key):
    for row in rows:
        if row["key"] == key:
            return row
    raise AssertionError(f"{key} not in the readout")


# ===========================================================================
# Fanno
# ===========================================================================


def test_fanno_opens_computed(duct):
    assert duct.valid
    assert duct.results
    assert duct.tableRowCount > 0


def test_fanno_readout_matches_the_physics(duct):
    duct.setMachAndSolve(0.5)
    assert value_of(duct.results, "friction_parameter")["raw"] == pytest.approx(
        float(fanno.friction_parameter(0.5, AIR)), rel=1e-12)
    assert value_of(duct.results, "pressure_ratio")["raw"] == pytest.approx(
        float(fanno.pressure_ratio(0.5, AIR)), rel=1e-12)


def test_fanno_pins_the_published_friction_value(duct):
    """The one number that catches a Darcy/Fanning mix-up on sight."""
    duct.setMachAndSolve(0.5)
    assert value_of(duct.results, "friction_parameter")["raw"] == pytest.approx(
        1.0690603127, abs=5e-10)


def test_fanno_labels_never_say_a_bare_friction_factor(duct):
    """The interface contract bans it, because "f" alone is ambiguous."""
    for convention in ("fanning", "darcy"):
        duct.frictionConvention = convention
        assert duct.frictionSymbol in ("f_F", "f_D")
        assert duct.frictionSymbol in duct.frictionLabel
        assert duct.frictionLabel.strip() not in ("f", "friction factor", "Friction factor")
    for row in duct.results:
        assert row["label"] != "f"


def test_fanno_publishes_the_supersonic_ceiling(duct):
    assert duct.supersonicLimit == pytest.approx(0.8215081165, abs=5e-10)
    duct.gamma = 1.2
    assert duct.supersonicLimit == pytest.approx(
        float(fanno.friction_parameter_limit(PerfectGas(gamma=1.2))), rel=1e-12)


def test_fanno_marks_the_sonic_row(duct):
    assert duct.sonicRow >= 0
    assert duct.tableModel.machAt(duct.sonicRow) == pytest.approx(1.0)


def test_fanno_offers_no_invented_published_comparison(duct):
    assert duct.referenceAvailable is False
    assert "no Fanno or Rayleigh appendix" in duct.referenceMessage
    assert duct.validationStatus == "PASS"
    assert len(duct.validationChecks) >= 4
    assert "NASA/TM-2006-214086" in duct.validationCitation


# ---------------------------------------------------------------------------
# the friction convention, and the factor of four
# ---------------------------------------------------------------------------


def test_darcy_and_fanning_describe_the_same_duct(duct):
    """The permanent guard on the factor of four.

    The same physical duct entered under either convention must produce the
    same canonical parameter and the same outlet -- to machine precision, not
    to a tolerance that a factor of four could hide in.
    """
    duct.segmentEnabled = True
    duct.segmentMach = 0.3
    duct.ductSource = "geometry"
    duct.ductLength = 1.0
    duct.hydraulicDiameter = 0.1

    duct.frictionConvention = "darcy"
    duct.frictionFactor = 0.02
    darcy_parameter = duct.effectiveDuctParameter
    darcy_outlet = value_of(duct.segmentResults, "mach2")["raw"]

    duct.frictionConvention = "fanning"
    duct.frictionFactor = 0.005
    assert duct.effectiveDuctParameter == pytest.approx(darcy_parameter, rel=1e-15)
    assert value_of(duct.segmentResults, "mach2")["raw"] == pytest.approx(
        darcy_outlet, rel=1e-15)

    # ...and the value itself is the Fanning group, not the Darcy one.
    assert darcy_parameter == pytest.approx(0.2, rel=1e-15)


def test_switching_convention_keeps_the_physical_duct(duct):
    """Policy A: the number in the field changes, the duct does not.

    The alternative -- keeping 0.02 and silently reinterpreting it -- would
    quadruple the friction the moment the user touched the control, which is
    the worst possible behaviour for exactly the mistake this page exists to
    prevent.
    """
    duct.segmentEnabled = True
    duct.ductSource = "geometry"
    duct.frictionConvention = "darcy"
    duct.frictionFactor = 0.02
    before = duct.effectiveDuctParameter

    duct.frictionConvention = "fanning"
    assert duct.frictionFactor == pytest.approx(0.005, rel=1e-15)
    assert duct.effectiveDuctParameter == pytest.approx(before, rel=1e-15)

    duct.frictionConvention = "darcy"
    assert duct.frictionFactor == pytest.approx(0.02, rel=1e-15)
    assert duct.effectiveDuctParameter == pytest.approx(before, rel=1e-15)


def test_the_relation_is_stated_on_the_page(duct):
    assert duct.frictionRelation.replace(" ", "") == "f_D=4f_F"


def test_geometry_scaling_leaves_the_answer_alone(duct):
    """Only the group 4 f L/D matters, not the individual lengths."""
    duct.segmentEnabled = True
    duct.segmentMach = 0.3
    duct.ductSource = "geometry"
    duct.frictionConvention = "fanning"

    duct.frictionFactor = 0.005
    duct.ductLength = 1.0
    duct.hydraulicDiameter = 0.1
    first = value_of(duct.segmentResults, "mach2")["raw"]

    duct.frictionFactor = 0.01
    duct.ductLength = 2.0
    duct.hydraulicDiameter = 0.8
    assert duct.effectiveDuctParameter == pytest.approx(0.1, rel=1e-15)

    duct.frictionFactor = 0.005
    duct.ductLength = 4.0
    duct.hydraulicDiameter = 0.4
    assert duct.effectiveDuctParameter == pytest.approx(0.2, rel=1e-15)
    assert value_of(duct.segmentResults, "mach2")["raw"] == pytest.approx(first, rel=1e-12)


# ---------------------------------------------------------------------------
# the duct segment
# ---------------------------------------------------------------------------


def test_a_zero_length_duct_leaves_the_flow_alone(duct):
    duct.segmentEnabled = True
    duct.segmentMach = 0.4
    duct.ductSource = "parameter"
    duct.ductParameter = 0.0
    assert value_of(duct.segmentResults, "mach2")["raw"] == pytest.approx(0.4, abs=1e-9)


def test_friction_drives_a_subsonic_duct_up_towards_sonic(duct):
    duct.segmentEnabled = True
    duct.segmentMach = 0.3
    duct.ductSource = "parameter"
    duct.ductParameter = 1.0
    outlet = value_of(duct.segmentResults, "mach2")["raw"]
    assert 0.3 < outlet < 1.0


def test_friction_drives_a_supersonic_duct_down_towards_sonic(duct):
    duct.segmentEnabled = True
    duct.segmentMach = 3.0
    duct.ductSource = "parameter"
    duct.ductParameter = 0.3
    outlet = value_of(duct.segmentResults, "mach2")["raw"]
    assert 1.0 < outlet < 3.0
    assert outlet == pytest.approx(1.7415765823, abs=5e-9)


def test_an_over_long_duct_reports_choking_and_clears_the_outlet(duct):
    """The specification's own case: no stale M2, and the request preserved."""
    duct.segmentEnabled = True
    duct.segmentMach = 0.3
    duct.ductSource = "parameter"
    duct.ductParameter = 1.0
    assert duct.segmentValid
    previous = value_of(duct.segmentResults, "mach2")["raw"]
    assert previous > 0.3

    duct.ductParameter = 10.0
    assert duct.segmentValid is False
    assert duct.segmentChoked is True
    assert duct.segmentStatus == "Choked"
    keys = {row["key"] for row in duct.segmentResults}
    assert "mach2" not in keys, "no outlet Mach may survive a duct that chokes"
    assert "available" in keys and "duct_parameter" in keys
    assert value_of(duct.segmentResults, "duct_parameter")["raw"] == pytest.approx(10.0)
    assert value_of(duct.segmentResults, "available")["raw"] == pytest.approx(
        float(fanno.friction_parameter(0.3, AIR)), rel=1e-12)

    # ...and a duct that fits brings the outlet back.
    duct.ductParameter = 1.0
    assert duct.segmentValid
    assert value_of(duct.segmentResults, "mach2")["raw"] == pytest.approx(previous, rel=1e-12)


def test_the_exact_choking_length_ends_sonic(duct):
    duct.segmentEnabled = True
    duct.segmentMach = 0.3
    duct.ductSource = "parameter"
    duct.ductParameter = float(fanno.friction_parameter(0.3, AIR))
    assert duct.segmentValid
    assert value_of(duct.segmentResults, "mach2")["raw"] == pytest.approx(1.0, abs=1e-9)


def test_the_segment_is_off_until_asked_for(duct):
    assert duct.segmentEnabled is False
    assert duct.segmentResults == []


# ===========================================================================
# Rayleigh
# ===========================================================================


def test_rayleigh_opens_computed(heat):
    assert heat.valid
    assert heat.results
    assert heat.tableRowCount > 0


def test_rayleigh_readout_matches_the_physics(heat):
    heat.setMachAndSolve(0.5)
    for key, relation in (("pressure_ratio", rayleigh.pressure_ratio),
                          ("temperature_ratio", rayleigh.temperature_ratio),
                          ("stagnation_temperature_ratio",
                           rayleigh.stagnation_temperature_ratio)):
        assert value_of(heat.results, key)["raw"] == pytest.approx(
            float(relation(0.5, AIR)), rel=1e-12), key


def test_rayleigh_publishes_both_critical_points_separately(heat):
    """The single most important thing this page has to get right."""
    assert heat.staticTemperatureMaxMach == pytest.approx(1.0 / math.sqrt(1.4), rel=1e-15)
    assert heat.staticTemperatureMaxMach == pytest.approx(0.8451542547, abs=5e-10)
    assert heat.staticTemperatureMaxValue == pytest.approx(36.0 / 35.0, rel=1e-15)
    assert heat.staticTemperatureMaxMach < 1.0, "the static maximum is not the sonic state"

    guides = heat.criticalGuides()
    assert len(guides) == 2
    labels = {g["label"] for g in guides}
    assert len(labels) == 2, "the two critical points must not share a label"
    values = sorted(g["value"] for g in guides)
    assert values[0] == pytest.approx(heat.staticTemperatureMaxMach, rel=1e-12)
    assert values[1] == pytest.approx(1.0)


def test_the_two_critical_rows_are_marked_as_different_things(heat):
    assert heat.sonicRow >= 0
    assert heat.staticTemperatureMaxRow >= 0
    assert heat.sonicRow != heat.staticTemperatureMaxRow
    assert heat.tableModel.machAt(heat.sonicRow) == pytest.approx(1.0)
    assert heat.tableModel.machAt(heat.staticTemperatureMaxRow) == pytest.approx(
        heat.staticTemperatureMaxMach, rel=1e-9)


def test_the_critical_rows_disappear_together_with_their_mach_numbers(heat):
    heat.tableStart = 1.2
    heat.regenerateTable()
    assert heat.sonicRow == -1
    assert heat.staticTemperatureMaxRow == -1


def test_the_static_temperature_falls_between_the_two_maxima(heat):
    """The behaviour a later tidy-up would be tempted to remove."""
    peak = heat.staticTemperatureMaxMach
    at_peak = float(rayleigh.temperature_ratio(peak, AIR))
    at_sonic = float(rayleigh.temperature_ratio(1.0, AIR))
    assert at_peak > at_sonic
    assert at_sonic == pytest.approx(1.0, rel=1e-15)


def test_rayleigh_publishes_the_supersonic_floor(heat):
    assert heat.supersonicT0Floor == pytest.approx(0.4897959184, abs=5e-10)


def test_rayleigh_offers_no_invented_published_comparison(heat):
    assert heat.referenceAvailable is False
    assert "no Fanno or Rayleigh appendix" in heat.referenceMessage
    assert heat.validationStatus == "PASS"
    assert "NASA/TM-2006-214086" in heat.validationCitation


# ---------------------------------------------------------------------------
# the heat transition
# ---------------------------------------------------------------------------


def test_heat_addition_drives_a_subsonic_duct_towards_sonic(heat):
    heat.heatEnabled = True
    heat.heatMach = 0.3
    heat.heatInput = "ratio"
    heat.temperatureRatio = 1.5
    outlet = value_of(heat.heatResults, "mach2")["raw"]
    assert 0.3 < outlet < 1.0


def test_heat_addition_drives_a_supersonic_duct_towards_sonic(heat):
    heat.heatEnabled = True
    heat.heatMach = 3.0
    heat.heatInput = "ratio"
    heat.temperatureRatio = 1.2
    outlet = value_of(heat.heatResults, "mach2")["raw"]
    assert 1.0 < outlet < 3.0


def test_the_published_heat_cases_reproduce(heat):
    heat.heatEnabled = True
    heat.heatInput = "ratio"
    heat.heatMach = 0.2
    heat.temperatureRatio = 2.0
    assert value_of(heat.heatResults, "mach2")["raw"] == pytest.approx(
        0.3001345550, abs=5e-9)
    heat.temperatureRatio = 4.0
    assert value_of(heat.heatResults, "mach2")["raw"] == pytest.approx(
        0.5019571678, abs=5e-9)


def test_excessive_heat_reports_choking_and_clears_the_outlet(heat):
    heat.heatEnabled = True
    heat.heatMach = 0.3
    heat.heatInput = "ratio"
    heat.temperatureRatio = 1.5
    assert heat.heatValid
    previous = value_of(heat.heatResults, "mach2")["raw"]

    heat.temperatureRatio = 10.0
    assert heat.heatValid is False
    assert heat.heatChoked is True
    assert heat.heatStatus == "Choked"
    keys = {row["key"] for row in heat.heatResults}
    assert "mach2" not in keys, "no outlet Mach may survive heat that chokes the flow"
    assert value_of(heat.heatResults, "requested_ratio")["raw"] == pytest.approx(10.0)
    assert value_of(heat.heatResults, "maximum_ratio")["raw"] == pytest.approx(
        1.0 / float(rayleigh.stagnation_temperature_ratio(0.3, AIR)), rel=1e-12)

    heat.temperatureRatio = 1.5
    assert heat.heatValid
    assert value_of(heat.heatResults, "mach2")["raw"] == pytest.approx(previous, rel=1e-12)


def test_dimensional_heat_uses_the_gas_model_cp(heat):
    heat.heatEnabled = True
    heat.heatInput = "heat"
    heat.heatMach = 0.3
    heat.gasConstant = 287.0528
    heat.inletStagnationTemperature = 300.0
    heat.heat = 100_000.0
    assert heat.heatValid
    gas = PerfectGas(gamma=heat.gamma, gas_constant=287.0528)
    expected_ratio = 1.0 + 100_000.0 / (gas.cp * 300.0)
    assert value_of(heat.heatResults, "stagnation_temperature_ratio_12")["raw"] == (
        pytest.approx(expected_ratio, rel=1e-12))


def test_the_heat_transition_is_off_until_asked_for(heat):
    assert heat.heatEnabled is False
    assert heat.heatResults == []


# ---------------------------------------------------------------------------
# nothing stale survives a change
# ---------------------------------------------------------------------------


def test_switching_fanno_mode_replaces_the_input(duct):
    duct.setMachAndSolve(0.5)
    assert duct.inputValue == 0.5
    duct.mode = "friction"
    assert duct.inputValue != 0.5
    assert duct.modeNeedsBranch is True
    duct.mode = "mach"
    assert duct.modeNeedsBranch is False


def test_switching_rayleigh_mode_replaces_the_input(heat):
    heat.setMachAndSolve(0.5)
    heat.mode = "stagnation_temperature_ratio"
    assert heat.inputValue != 0.5
    assert heat.modeNeedsBranch is True
    heat.mode = "mach"
    assert heat.modeNeedsBranch is False


def test_changing_gamma_recomputes_everything(duct, heat):
    before = value_of(duct.results, "friction_parameter")["raw"]
    duct.gamma = 1.2
    assert value_of(duct.results, "friction_parameter")["raw"] != before

    peak = heat.staticTemperatureMaxMach
    heat.gamma = 1.2
    assert heat.staticTemperatureMaxMach != peak
    assert heat.staticTemperatureMaxMach == pytest.approx(1.0 / math.sqrt(1.2), rel=1e-15)


@pytest.mark.parametrize("controller_name", ["duct", "heat"])
def test_a_refused_range_clears_the_table(controller_name, duct, heat):
    controller = duct if controller_name == "duct" else heat
    assert controller.tableRowCount > 0
    controller.tableStep = 0.0
    controller.regenerateTable()
    assert controller.tableRowCount == 0
    assert controller.tableMessage
    assert controller.chartSeries("mach") == []

    controller.tableStep = 0.05
    controller.regenerateTable()
    assert controller.tableRowCount > 0
    assert controller.tableMessage == ""


@pytest.mark.parametrize("controller_name", ["duct", "heat"])
def test_regenerating_drops_the_previous_selection(controller_name, duct, heat):
    controller = duct if controller_name == "duct" else heat
    controller.selectRow(4)
    assert controller.selectedRow == 4
    controller.regenerateTable()
    assert controller.selectedRow == -1


@pytest.mark.parametrize("controller_name", ["duct", "heat"])
def test_an_invalid_input_keeps_the_reading_but_marks_it_stale(controller_name, duct, heat):
    controller = duct if controller_name == "duct" else heat
    controller.setMachAndSolve(0.5)
    assert controller.valid and not controller.stale
    controller.inputValue = -1.0
    assert not controller.valid
    assert controller.stale
    assert controller.results == []


@pytest.mark.parametrize("controller_name", ["duct", "heat"])
def test_the_table_and_the_charts_read_the_same_block(controller_name, duct, heat):
    controller = duct if controller_name == "duct" else heat
    keys = [c["key"] for c in controller.tableColumns]
    quantity = keys[1]
    series = controller.chartSeries(quantity)
    values = controller.tableModel.values
    column = keys.index(quantity)
    by_mach = {round(float(values[r, 0]), 9): float(values[r, column])
               for r in range(values.shape[0])}
    for point in series:
        assert by_mach[round(point["x"], 9)] == pytest.approx(point["y"])


@pytest.mark.parametrize("controller_name", ["duct", "heat"])
def test_the_two_branches_are_separate_series(controller_name, duct, heat):
    """Specification requirement: one array containing M = 1 invites a
    misleading autoscale, because the two sides differ in scale."""
    controller = duct if controller_name == "duct" else heat
    keys = [c["key"] for c in controller.tableColumns]
    branches = controller.branchSeries(keys[1])
    assert len(branches) == 2
    labels = {b["label"] for b in branches}
    assert labels == {"Subsonic", "Supersonic"}
    for branch in branches:
        machs = [p["x"] for p in branch["points"]]
        assert machs, branch["label"]
        if branch["label"] == "Subsonic":
            assert max(machs) <= 1.0 + 1e-9
        else:
            assert min(machs) >= 1.0 - 1e-9


# ---------------------------------------------------------------------------
# the metaobject, and the earlier modules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("controller_class", [
    FannoController, RayleighController, PrandtlMeyerController, ObliqueShockController,
    IsentropicController, MassFlowController, NormalShockController,
])
def test_every_property_has_a_usable_notify_signal(qt_app, controller_class):
    """Regression for a segfault, not a wrong answer.

    A property whose notify index points outside its own metaobject crashes the
    process the first time QML binds to it.
    """
    meta = controller_class.staticMetaObject
    for index in range(meta.propertyOffset(), meta.propertyCount()):
        prop = meta.property(index)
        if prop.isConstant():
            continue
        assert prop.hasNotifySignal(), prop.name()
        signal_index = prop.notifySignalIndex()
        assert 0 <= signal_index < meta.methodCount(), (prop.name(), signal_index)
        assert meta.method(signal_index).name().data()


@pytest.mark.parametrize("controller_class", [FannoController, RayleighController])
def test_controllers_declare_their_own_signals(qt_app, controller_class):
    for name in ("resultsChanged", "inputsChanged", "tableChanged",
                 "tableSettingsChanged", "referenceChanged"):
        assert name in vars(controller_class), (
            f"{controller_class.__name__} must declare {name} itself")


def test_the_earlier_pages_still_work(qt_app):
    """Phase 4E generalised the shared table component, so this is the guard."""
    isentropic = IsentropicController()
    isentropic.compareEnabled = True
    assert isentropic.comparisonSummary["review"] == 0

    massflow = MassFlowController()
    assert massflow.valid and massflow.tableRowCount > 0

    shock = NormalShockController()
    shock.compareEnabled = True
    assert shock.comparisonSummary["review"] == 0

    expansion = PrandtlMeyerController()
    expansion.compareEnabled = True
    assert expansion.comparisonSummary["review"] == 0

    oblique = ObliqueShockController()
    assert oblique.valid and oblique.curve()["weak"]
