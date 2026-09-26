"""One selection per workspace, shared by every view of it.

A throat picked in the 3D view, the throat guide clicked on a chart and the
throat row of a table are one engineering object; they share one selection
rather than three incompatible ``selectedThing`` properties. A selection is
identified by engineering coordinates -- a station key, an axial position, a
table row, a plot x -- never by a pixel.

Selecting is presentation over results that already exist: it emits
``changed`` and nothing else. No slot here reaches a solver.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Property, QObject, Signal, Slot

__all__ = ["AnalysisSelection", "KINDS"]

#: What can be selected.
KINDS = ("station", "plotPoint", "tableRow", "probe", "roi", "state")


class AnalysisSelection(QObject):
    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._kind = ""
        self._key = ""
        self._x = math.nan
        self._y = math.nan
        self._label = ""
        self._source = ""
        self._revision = 0

    def _assign(self, kind: str, key: str, x: float, y: float, label: str, source: str) -> None:
        if kind not in KINDS:
            raise ValueError(f"unknown selection kind {kind!r}")
        self._kind, self._key = kind, str(key)
        self._x, self._y = float(x), float(y)
        self._label, self._source = str(label), str(source)
        self._revision += 1
        self.changed.emit()

    @Slot(str, str, float, str, str)
    def select(self, kind: str, key: str, x: float, label: str, source: str) -> None:
        """Select ``key`` of ``kind`` at engineering coordinate ``x``."""
        self._assign(kind, key, x, math.nan, label, source)

    @Slot(str, str, float, float, str, str)
    def selectPoint(self, kind: str, key: str, x: float, y: float, label: str,
                    source: str) -> None:
        """Select a plotted point: an x and the y read at it."""
        self._assign(kind, key, x, y, label, source)

    @Slot()
    def clear(self) -> None:
        if self._kind == "" and self._key == "":
            return
        self._kind = self._key = self._label = self._source = ""
        self._x = self._y = math.nan
        self._revision += 1
        self.changed.emit()

    @Property(str, notify=changed)
    def kind(self) -> str:
        return self._kind

    @Property(str, notify=changed)
    def key(self) -> str:
        return self._key

    @Property(float, notify=changed)
    def x(self) -> float:
        return self._x

    @Property(float, notify=changed)
    def y(self) -> float:
        return self._y

    @Property(str, notify=changed)
    def label(self) -> str:
        return self._label

    @Property(str, notify=changed)
    def source(self) -> str:
        return self._source

    @Property(int, notify=changed)
    def revision(self) -> int:
        return self._revision

    @Property(bool, notify=changed)
    def active(self) -> bool:
        return self._kind != ""
