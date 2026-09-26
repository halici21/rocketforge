"""Presentation adapters for interactive engineering views.

Everything here turns a result that has already been solved into something a
view draws: a revolved nozzle surface, the stations on it, a plot range, a
pinned snapshot. Nothing here solves, and nothing here may: a view that
orbits, zooms or selects reads what these produce and never asks for more.

The layer boundary is the one the rest of ``application`` keeps: the pure
modules (``fidelity``, ``geometry``, ``viewport``, ``plot``) import no Qt, so
they are tested on their own; ``selection`` and ``session`` are the QObjects
QML binds to; ``geometry_qml`` is the one module that needs Qt Quick 3D, and
it is imported only when that module is installed.
"""
