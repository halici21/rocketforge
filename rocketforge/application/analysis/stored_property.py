"""One stored, writable Qt property of a compressible-flow controller.

The seven compressible-flow controllers (Isentropic, Mass Flow, Normal and
Oblique Shock, Prandtl-Meyer, Fanno, Rayleigh) wrote most of their inputs and
table settings as the same three members, by hand::

    def _get_gamma(self) -> float:
        return self._gamma

    def _set_gamma(self, value: float) -> None:
        value = float(value)
        if value == self._gamma:
            return
        self._gamma = value
        self.inputsChanged.emit()
        self._recalculate()

    gamma = Property(float, _get_gamma, _set_gamma, notify=inputsChanged)

``stored_property`` builds exactly that, once, at class-definition time::

    gamma = stored_property(float, "_gamma", inputsChanged, recalculate=True)

The setter converts the value, does nothing if it equals what is stored,
otherwise stores it, emits the notify signal, and (only with
``recalculate=True``) calls the controller's ``_recalculate()`` -- in that
order, which is the order every replaced setter used. A property whose setter
does anything else (resets another field, emits a second signal, converts
between conventions) stays written out by hand, so its extra behaviour stays
visible where it is declared.
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Property, Signal

__all__ = ["stored_property", "clamp_precision"]

#: ``coerce`` left at this means "convert with the property's own type".
_OWN_TYPE: Any = object()


def clamp_precision(value) -> int:
    """A readout or table precision, as every one of these controllers clamps it: 3 to 12 digits."""
    return max(3, min(12, int(value)))


def stored_property(qt_type: type, attribute: str, notify: Signal, *,
                    recalculate: bool = False,
                    coerce: Callable[[Any], Any] | None = _OWN_TYPE) -> Property:
    """A read-write Qt property stored in ``self.<attribute>`` and notified by ``notify``.

    Args:
        qt_type: The property's Qt type (``float``, ``int``, ``bool`` or ``str``).
        attribute: The instance attribute that holds the value, e.g. ``"_gamma"``.
        notify: The class's notify ``Signal``; it is emitted on the instance when
            the value changes, and it is the property's notify signal for QML.
        recalculate: Call ``self._recalculate()`` after notifying.
        coerce: How a written value is converted before it is compared and
            stored. By default ``qt_type`` itself; ``None`` stores it as given
            (the setters that compared and stored the raw value).
    """
    convert = qt_type if coerce is _OWN_TYPE else coerce

    def getter(self):
        return getattr(self, attribute)

    def setter(self, value) -> None:
        if convert is not None:
            value = convert(value)
        if value == getattr(self, attribute):
            return
        setattr(self, attribute, value)
        notify.__get__(self, type(self)).emit()      # the Signal, bound to this instance
        if recalculate:
            self._recalculate()

    # Named after the attribute, so a traceback says which property it was.
    getter.__name__ = getter.__qualname__ = f"get{attribute}"
    setter.__name__ = setter.__qualname__ = f"set{attribute}"
    return Property(qt_type, getter, setter, notify=notify)
