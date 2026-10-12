"""R3-B: one pressure display-unit table, offered on Thermochemistry, Fluid Properties and Line.

A display unit changes what a field shows, never what the case holds: the case stays in pascals,
a unit change neither re-evaluates nor marks a result stale, and a value typed in a unit lands in
pascals exactly once.
"""
from __future__ import annotations

import pytest

from rocketforge.application.analysis import pressure_units
from rocketforge.application.analysis import thermochemistry_controller


@pytest.fixture(scope="module")
def app():
    from PySide6.QtGui import QGuiApplication

    return QGuiApplication.instance() or QGuiApplication([])


def _controllers():
    from rocketforge.application.analysis.fluid_property_controller import FluidPropertyController
    from rocketforge.application.analysis.line_controller import LineController

    return (FluidPropertyController, LineController)


def test_one_table_for_every_page():
    assert thermochemistry_controller.PRESSURE_UNITS is pressure_units.PRESSURE_UNITS
    assert [u["key"] for u in pressure_units.PRESSURE_UNITS] == ["Pa", "bar", "MPa"]
    assert pressure_units.to_pa("bar") == 1.0e5 and pressure_units.to_pa("MPa") == 1.0e6
    assert pressure_units.unit_info("no such unit")["key"] == "Pa"


@pytest.mark.parametrize("index", [0, 1])
def test_the_case_keeps_pascals_and_the_field_shows_the_unit(app, index):
    controller = _controllers()[index]()
    start = controller.pressure
    assert controller.pressureUnit == "Pa" and controller.pressureDisplay == start   # default unchanged
    controller.pressureUnit = "bar"
    assert controller.pressure == start                                              # display only
    assert controller.pressureDisplay == pytest.approx(start / 1.0e5, rel=1e-15)
    controller.setPressureDisplay(12.5)
    assert controller.pressure == pytest.approx(12.5e5, rel=1e-15)
    controller.pressureUnit = "MPa"
    assert controller.pressureDisplay == pytest.approx(1.25, rel=1e-15)
    assert controller.pressureUnitInfo["decimals"] == 4
    controller.pressureUnit = "furlongs"                                             # refused
    assert controller.pressureUnit == "MPa"


def test_the_field_reformats_when_its_unit_changes_and_never_writes_back(app):
    """A unit switch moves the value and the decimals together. Whichever arrives first, the
    field must end up showing the value at the new decimals (0.35 MPa is "0.3500", not "0"),
    and the switch itself must not emit an edit. A stale "0" was later stepped from, writing a
    wrong pressure (R3-B review).
    """
    import pathlib

    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    components = (pathlib.Path(__file__).resolve().parents[2] / "ui" / "components").as_uri()
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.setData(
        ('import QtQuick\nimport "%s"\n' % components
         + "Item {\n"
         + "  property real pa: 350000\n"
         + "  property real factor: 1\n"
         + "  property int places: 0\n"
         + "  property int edits: 0\n"
         + "  property alias shown: field.text\n"
         + "  property real lastEdit: 0\n"
         + "  RFBoundNumberField { id: field; value: pa / factor; digits: places; step: 0.1;\n"
         + "      onValueEdited: function (v) { edits += 1; lastEdit = v } }\n"
         + "  function toUnit(f, d) { factor = f; places = d }\n"
         + "  function toUnitDecimalsFirst(f, d) { places = d; factor = f }\n"
         + "  function stepUp() { field.nudge(1) }\n"
         + "}\n").encode(), QUrl("file:///r3b_unit_probe.qml"))
    root = component.create()
    assert root is not None, component.errorString()
    assert root.property("shown") == "350000"
    for factor, places, expected in ((1.0e6, 4, "0.3500"), (1.0e5, 3, "3.500"), (1.0, 0, "350000")):
        root.toUnit(factor, places)            # value first, then the decimals
        app.processEvents()
        assert root.property("shown") == expected, (factor, root.property("shown"))
    assert root.property("edits") == 0         # a display change is never an edit
    for factor, places, expected in ((1.0e6, 4, "0.3500"), (1.0e5, 3, "3.500"), (1.0, 0, "350000")):
        root.toUnitDecimalsFirst(factor, places)
        app.processEvents()
        assert root.property("shown") == expected, ("decimals first", factor, root.property("shown"))
    assert root.property("edits") == 0
    # a step is written at the field's precision: 0.4321 MPa + 0.1 is 0.5321, not 0.532
    root.setProperty("pa", 432100.0)
    root.toUnit(1.0e6, 4)
    app.processEvents()
    assert root.property("shown") == "0.4321"
    root.stepUp()
    app.processEvents()
    assert root.property("shown") == "0.5321" and root.property("lastEdit") == pytest.approx(0.5321)


@pytest.mark.parametrize("index", [0, 1])
def test_a_unit_change_neither_evaluates_nor_stales(app, index, monkeypatch):
    controller = _controllers()[index]()
    calls = []
    service = __import__(type(controller).__module__, fromlist=["service"]).service
    for name in ("evaluate_case", "solve_case"):
        if hasattr(service, name):
            original = getattr(service, name)
            monkeypatch.setattr(service, name, lambda *a, _o=original, **k: (calls.append(1), _o(*a, **k))[1])
    # Marking a result stale goes through _mark_dirty, which emits resultChanged; a display
    # unit must emit inputsChanged only.
    results, inputs = [], []
    controller.resultChanged.connect(lambda: results.append(1))
    controller.inputsChanged.connect(lambda: inputs.append(1))
    stale = controller._stale
    for unit in ("bar", "MPa", "Pa"):
        controller.pressureUnit = unit
    assert calls == [] and results == [] and controller._stale is stale
    assert len(inputs) == 3                                   # the field does re-render
    # positive control: a real pressure edit does go through _mark_dirty
    controller.setPressureDisplay(2.0)
    assert results
