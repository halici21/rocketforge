"""Session-only analysis snapshots: pin, list, compare, drop.

Pinned snapshots -- plot views, table blocks and design-point subsets (see
``plot``) -- live for the session and nowhere else; this is not a project
history. Each is frozen when pinned (see ``plot.freeze_snapshot``), so the
live chart or table can be zoomed, re-solved or cleared without touching it.
One session holds every kind; a comparison across kinds is refused.
"""
from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from .plot import (SnapshotError, compatibility, freeze_snapshot, probe_delta, series_delta,
                   table_delta)

__all__ = ["AnalysisSession", "MAX_SNAPSHOTS"]

#: A comparison needs two; a short strip of recent views is useful; more is a
#: history this task does not build.
MAX_SNAPSHOTS = 6


class AnalysisSession(QObject):
    snapshotsChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._snapshots: list[dict] = []
        self._counter = 0
        self._last_error = ""

    @Slot("QVariantMap", result=str)
    def pin(self, snapshot) -> str:
        """Freeze and keep ``snapshot``; its id, or "" with ``lastError`` set."""
        try:
            frozen = freeze_snapshot(dict(snapshot))
        except (SnapshotError, TypeError, ValueError, KeyError) as error:
            self._last_error = str(error)
            return ""
        self._counter += 1
        frozen["id"] = f"S{self._counter}"
        self._snapshots.append(frozen)
        if len(self._snapshots) > MAX_SNAPSHOTS:
            self._snapshots.pop(0)
        self._last_error = ""
        self.snapshotsChanged.emit()
        return frozen["id"]

    @Property("QVariantList", notify=snapshotsChanged)
    def snapshots(self):
        # copies: a caller that edits what it was given edits nothing kept
        return [freeze_snapshot(s) | {"id": s["id"]} for s in self._snapshots]

    @Property(int, notify=snapshotsChanged)
    def count(self) -> int:
        return len(self._snapshots)

    @Property(str, notify=snapshotsChanged)
    def lastError(self) -> str:
        return self._last_error

    def _get(self, snapshot_id: str) -> dict | None:
        for s in self._snapshots:
            if s["id"] == snapshot_id:
                return s
        return None

    @Slot(str, result="QVariantMap")
    def snapshot(self, snapshot_id: str):
        s = self._get(snapshot_id)
        return {} if s is None else freeze_snapshot(s) | {"id": s["id"]}

    @Slot(str)
    def remove(self, snapshot_id: str) -> None:
        before = len(self._snapshots)
        self._snapshots = [s for s in self._snapshots if s["id"] != snapshot_id]
        if len(self._snapshots) != before:
            self.snapshotsChanged.emit()

    @Slot()
    def clear(self) -> None:
        if self._snapshots:
            self._snapshots = []
            self.snapshotsChanged.emit()

    @Slot(str, str, result="QVariantMap")
    def compare(self, a_id: str, b_id: str):
        a, b = self._get(a_id), self._get(b_id)
        if a is None or b is None:
            return {"compatible": False, "reason": "unknown snapshot"}
        return compatibility(a, b)

    @Slot(str, str, float, result="QVariantMap")
    def compareAt(self, a_id: str, b_id: str, x: float):
        a, b = self._get(a_id), self._get(b_id)
        if a is None or b is None:
            return {"compatible": False, "reason": "unknown snapshot"}
        return series_delta(a, b, x)

    @Slot(str, str, result="QVariantMap")
    def tableDelta(self, a_id: str, b_id: str):
        """Two table blocks, row-aligned by engineering key (``plot.table_delta``)."""
        a, b = self._get(a_id), self._get(b_id)
        if a is None or b is None:
            return {"compatible": False, "reason": "unknown snapshot"}
        return table_delta(a, b)

    @Slot("QVariantMap", "QVariantMap", result="QVariantMap")
    def probeDelta(self, a, b):
        return probe_delta(dict(a), dict(b))

    @Slot(str)
    def copyText(self, text: str) -> None:
        """Put text on the clipboard (Copy values). Presentation, no data change."""
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(str(text))
