"""R3-C: ``stored_property`` builds independent properties with their own signals.

Two layers:

1. **the helper alone**, on a small probe class: each property reads and writes its own
   attribute, emits its own notify signal and nothing else, converts as declared, ignores a
   write of the value it already holds, and recalculates only when asked to and only on a
   change.
2. **every property it builds in the seven compressible-flow controllers**: writing one
   distinct value changes that property and its own attribute, leaves every other
   helper-built property alone, emits that property's notify signal, and a repeat write of
   the same value emits nothing.

These are the failures a helper of this kind invites: a closure that reads the last
attribute of a loop, one signal shared by every property, a type or access that drifts.
The Qt-level surface (names, types, access, notify signals) is pinned separately, against a
frozen 3ec5f0f capture, in ``test_compressible_property_surface.py``.
"""
from __future__ import annotations

import importlib

import pytest
from PySide6.QtCore import QObject, Signal

from rocketforge.application.analysis import stored_property as helper_module
from rocketforge.application.analysis.stored_property import clamp_precision, stored_property

CONTROLLERS = {
    "IsentropicController": "isentropic_controller",
    "MassFlowController": "mass_flow_controller",
    "NormalShockController": "normal_shock_controller",
    "ObliqueShockController": "oblique_shock_controller",
    "PrandtlMeyerController": "prandtl_meyer_controller",
    "FannoController": "fanno_controller",
    "RayleighController": "rayleigh_controller",
}
#: A valid other value for the string inputs that recalculate (the table settings do not, so
#: any distinct string is safe there).
OTHER_STRING = {"subsonic": "supersonic", "supersonic": "subsonic", "parameter": "geometry",
                "ratio": "heat"}


@pytest.fixture(scope="module")
def app():
    from PySide6.QtGui import QGuiApplication

    return QGuiApplication.instance() or QGuiApplication([])


class Probe(QObject):
    aChanged = Signal()
    bChanged = Signal()
    textChanged = Signal()

    a = stored_property(float, "_a", aChanged, recalculate=True)
    b = stored_property(float, "_b", bChanged)
    raw = stored_property(str, "_raw", textChanged, coerce=None)
    digits = stored_property(int, "_digits", textChanged, coerce=clamp_precision)

    def __init__(self) -> None:
        super().__init__()
        self._a, self._b, self._raw, self._digits = 1.0, 2.0, "x", 4
        self.recalculations = 0

    def _recalculate(self) -> None:
        self.recalculations += 1


def _counter(obj, *names):
    counts = dict.fromkeys(names, 0)
    for name in names:
        getattr(obj, name).connect(lambda n=name: counts.__setitem__(n, counts[n] + 1))
    return counts


# ------------------------------------------------------------------ the helper alone


def test_each_property_reads_and_writes_its_own_attribute(app):
    p = Probe()
    p.a = 10.0
    assert (p.a, p._a, p.b, p._b) == (10.0, 10.0, 2.0, 2.0)
    p.b = 20.0
    assert (p.a, p._a, p.b, p._b) == (10.0, 10.0, 20.0, 20.0)


def test_each_property_emits_its_own_signal_only(app):
    p = Probe()
    counts = _counter(p, "aChanged", "bChanged", "textChanged")
    p.a = 3.0
    assert counts == {"aChanged": 1, "bChanged": 0, "textChanged": 0}
    p.b = 4.0
    assert counts == {"aChanged": 1, "bChanged": 1, "textChanged": 0}


def test_a_write_of_the_held_value_does_nothing(app):
    p = Probe()
    counts = _counter(p, "aChanged", "bChanged")
    p.a = 1.0
    p.a = 1                                   # converted first, so still the held value
    assert counts == {"aChanged": 0, "bChanged": 0} and p.recalculations == 0


def test_recalculate_runs_once_per_change_and_only_when_asked(app):
    p = Probe()
    p.a = 5.0
    p.a = 5.0
    p.b = 6.0                                 # b does not recalculate
    assert p.recalculations == 1


def test_values_are_converted_as_declared(app):
    p = Probe()
    p.a = 7                                   # float: converted
    assert type(p._a) is float and p._a == 7.0
    p.digits = 40                             # clamped
    assert p._digits == 12
    p.digits = "1"
    assert p._digits == 3
    p.raw = "y"                               # coerce=None: stored as given
    assert p._raw == "y"


def test_qt_sees_the_declared_type_access_and_notify_signal(app):
    meta = Probe.staticMetaObject
    seen = {}
    for i in range(meta.propertyOffset(), meta.propertyCount()):
        prop = meta.property(i)
        seen[prop.name()] = (prop.typeName(), prop.isWritable(),
                             bytes(prop.notifySignal().methodSignature()).decode())
    assert seen == {"a": ("double", True, "aChanged()"), "b": ("double", True, "bChanged()"),
                    "raw": ("QString", True, "textChanged()"), "digits": ("int", True, "textChanged()")}


def test_a_traceback_names_the_attribute():
    assert Probe.__dict__["a"].fget.__name__ == "get_a"
    assert Probe.__dict__["a"].fset.__name__ == "set_a"


# ------------------------------------------------------------------ the seven controllers


def _built(cls) -> dict:
    """The properties stored_property built on this class: QML name -> backing attribute."""
    out = {}
    for name, value in vars(cls).items():
        fget = getattr(value, "fget", None)
        if fget is not None and getattr(fget, "__module__", "") == helper_module.__name__:
            out[name] = "_" + fget.__name__.split("_", 1)[1]
    return out


def _distinct(current, type_name, name):
    if type_name == "bool":
        return not current
    if type_name == "int":
        return current - 1 if current >= 12 else current + 1
    if type_name == "QString":
        return OTHER_STRING.get(current, current + "-r3c")
    return float(current) * 1.07 + 0.05


def test_the_helper_builds_seventy_three_properties():
    counts = {name: len(_built(getattr(importlib.import_module(
        f"rocketforge.application.analysis.{module}"), name))) for name, module in CONTROLLERS.items()}
    assert counts == {"IsentropicController": 3, "MassFlowController": 15, "NormalShockController": 10,
                      "ObliqueShockController": 9, "PrandtlMeyerController": 8, "FannoController": 14,
                      "RayleighController": 14}


@pytest.mark.parametrize("name", sorted(CONTROLLERS))
def test_every_built_property_is_independent_and_notifies_on_its_own_signal(app, name):
    cls = getattr(importlib.import_module(f"rocketforge.application.analysis.{CONTROLLERS[name]}"), name)
    built = _built(cls)
    meta = cls.staticMetaObject
    for prop_name, attribute in sorted(built.items()):
        obj = cls()
        prop = meta.property(meta.indexOfProperty(prop_name))
        notify = bytes(prop.notifySignal().name()).decode()
        before = {other: getattr(obj, attr) for other, attr in built.items()}
        value = _distinct(obj.property(prop_name), prop.typeName(), prop_name)
        assert value != before[prop_name], prop_name
        counts = _counter(obj, notify)
        obj.setProperty(prop_name, value)
        stored = getattr(obj, attribute)
        assert obj.property(prop_name) == stored, prop_name
        assert stored == (clamp_precision(value) if prop_name == "precision" else value), prop_name
        assert counts[notify] >= 1, (prop_name, notify)
        for other, attr in built.items():
            if other != prop_name:
                assert getattr(obj, attr) == before[other], (prop_name, "moved", other)
        counts[notify] = 0
        obj.setProperty(prop_name, obj.property(prop_name))     # the held value: a no-op
        assert counts[notify] == 0, (prop_name, "re-emitted on the same value")
