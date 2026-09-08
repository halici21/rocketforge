"""Rules for the stable row model and the publication pattern it replaced.

The model was written as a fix for a memory leak that turned out not to exist
(see QML_MEMORY_ROOT_CAUSE.md). It is kept because it lowers a real plateau and
because it is the pattern the visual rollout needs. These rules pin the
behaviour either way.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from PySide6.QtCore import Qt

from rocketforge.application.rowmodel import RowListModel

ROOT = pathlib.Path(__file__).resolve().parent.parent


def role_of(model: RowListModel, name: str) -> int:
    for key, value in model.roleNames().items():
        if bytes(value).decode() == name:
            return key
    raise AssertionError(f"no role {name}")


def read(model: RowListModel, row: int, name: str):
    return model.data(model.index(row, 0), role_of(model, name))


def test_rows_are_addressable_by_role_name():
    model = RowListModel(("label", "value"))
    model.set_rows([{"label": "Isp", "value": "348.658"}])
    assert model.rowCount() == 1
    assert read(model, 0, "label") == "Isp"
    assert read(model, 0, "value") == "348.658"


def test_a_missing_field_reads_as_empty_not_undefined():
    """A delegate must not have to guard against a key one result omitted."""
    model = RowListModel(("label", "unit"))
    model.set_rows([{"label": "Isp"}])
    assert read(model, 0, "unit") == ""


def test_a_bool_survives_as_a_bool():
    """`primary` was stringified to "True" once, which is truthy either way --
    so `primary: false` would silently have meant true."""
    model = RowListModel(("primary",))
    model.set_rows([{"primary": False}, {"primary": True}])
    assert read(model, 0, "primary") is False
    assert read(model, 1, "primary") is True


def test_a_role_may_be_named_differently_from_its_key():
    """A delegate cannot redeclare a property its own type already defines.
    Binding a PerfMetricReadout to roles called value/unit/primary collided
    with the component's own properties and the readout rendered EMPTY while
    every scientific field still compared equal."""
    model = RowListModel(((("rowValue"), "value"), ("rowUnit", "unit")))
    model.set_rows([{"value": "1.5", "unit": "s"}])
    assert read(model, 0, "rowValue") == "1.5"
    assert read(model, 0, "rowUnit") == "s"


def test_a_same_length_update_does_not_reset_the_model():
    """Resetting destroys and rebuilds every delegate. Updating in place is the
    entire point of the model."""
    model = RowListModel(("value",))
    model.set_rows([{"value": "1"}, {"value": "2"}])
    resets = []
    changes = []
    model.modelAboutToBeReset.connect(lambda: resets.append(1))
    model.dataChanged.connect(lambda *a: changes.append(a))
    model.set_rows([{"value": "9"}, {"value": "2"}])
    assert not resets
    assert changes
    assert read(model, 0, "value") == "9"


def test_a_changed_length_does_reset():
    model = RowListModel(("value",))
    model.set_rows([{"value": "1"}])
    resets = []
    model.modelAboutToBeReset.connect(lambda: resets.append(1))
    model.set_rows([{"value": "1"}, {"value": "2"}])
    assert resets


def test_an_identical_update_emits_nothing():
    model = RowListModel(("value",))
    model.set_rows([{"value": "1"}])
    changes = []
    model.dataChanged.connect(lambda *a: changes.append(a))
    model.set_rows([{"value": "1"}])
    assert not changes


def test_an_out_of_range_index_reads_none_rather_than_raising():
    model = RowListModel(("value",))
    model.set_rows([{"value": "1"}])
    assert model.data(model.index(5, 0), role_of(model, "value")) is None
    assert model.data(model.index(-1, 0), role_of(model, "value")) is None


def test_a_model_needs_at_least_one_role():
    with pytest.raises(ValueError):
        RowListModel(())


# --- the interface binds models, not lists --------------------------------

PAGE_DIR = ROOT / "ui" / "pages" / "rocketperformance"


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", text)


LIST_PROPERTIES = ("headlineMetrics", "thrustCoefficientBreakdown",
                   "thrustBreakdown", "exitStateRows", "traceRows",
                   "chamberRows", "reductionRows", "identityRows",
                   "provenanceRows", "oracleRows", "oracleComparisonRows")


@pytest.mark.parametrize("name", LIST_PROPERTIES)
def test_no_qml_binds_a_list_property(name):
    """These still exist and are still correct -- Python reads them, and a read
    from Python costs nothing. What the interface must not do is re-read them
    from a binding on every publication."""
    for path in PAGE_DIR.glob("*.qml"):
        text = strip_comments(path.read_text(encoding="utf-8"))
        assert f"RocketPerformance.{name}" not in text, path.name


def test_the_scan_would_catch_a_reintroduced_list_binding():
    snippet = "model: RocketPerformance.headlineMetrics"
    assert "RocketPerformance.headlineMetrics" in strip_comments(snippet)


def test_every_bound_model_exists_on_the_controller():
    from rocketforge.application.analysis.performance_controller import (
        RocketPerformanceController,
    )

    bound = set()
    for path in PAGE_DIR.glob("*.qml"):
        text = strip_comments(path.read_text(encoding="utf-8"))
        bound.update(re.findall(r"RocketPerformance\.(\w+Model)\b", text))
    assert bound, "no models are bound at all"
    for name in sorted(bound):
        assert hasattr(RocketPerformanceController, name), name
