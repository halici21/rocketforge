"""A table model for tables whose columns are not all numbers.

``EngineeringTableModel`` holds a float64 block and serves the compressible
pages perfectly. Two Phase 5D tables do not fit it: a composition table has a
species name and a phase, and a sweep table has a per-row status. Both of those
are text, and encoding text as a float code so it could live in a numeric block
would be worse than having a second model.

So: one model, mixed columns, used by both. Numbers stay numbers -- the display
string is produced by :func:`format_engineering` on the way out and never
stored, so copy and export carry values rather than rendered text.

``RowKindRole`` lets a view style a row that means something -- a condensed
species, a sweep point that did not solve -- without the model knowing why it is
special, which is the same separation ``EngineeringTableModel`` already keeps.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, Slot

from ..formatting import EM_DASH, format_engineering

__all__ = ["ThermoTableModel"]


class ThermoTableModel(QAbstractTableModel):
    """Rows of mixed text and numeric cells with labelled columns.

    A column declares ``kind`` as ``"text"`` or ``"number"``. Text cells are
    passed through; numeric cells are formatted at the display precision, and a
    non-finite number renders as an em dash -- never as zero, which would be a
    different claim entirely.
    """

    ValueRole = Qt.UserRole + 1        # the raw cell value
    RowKindRole = Qt.UserRole + 2      # "", "condensed", "failed", "warning"
    RowLabelRole = Qt.UserRole + 3     # short annotation for the row gutter

    precisionChanged = Signal()
    tableReset = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._columns: list[dict] = []
        self._rows: list[tuple] = []
        self._kinds: list[str] = []
        self._labels: list[str] = []
        self._precision = 6

    # -- population -------------------------------------------------------

    def set_table(self, columns, rows, kinds=None, labels=None) -> None:
        """Replace the whole table in one reset.

        A full reset rather than incremental signals, for the same reason the
        numeric model does it: these tables are rebuilt wholesale whenever the
        result or the display filter changes.
        """
        self.beginResetModel()
        self._columns = [dict(column) for column in columns]
        self._rows = [tuple(row) for row in rows]
        self._kinds = list(kinds) if kinds is not None else [""] * len(self._rows)
        self._labels = list(labels) if labels is not None else [""] * len(self._rows)
        if len(self._kinds) != len(self._rows):
            self._kinds = [""] * len(self._rows)
        if len(self._labels) != len(self._rows):
            self._labels = [""] * len(self._rows)
        self.endResetModel()
        self.tableReset.emit()

    def clear(self) -> None:
        self.set_table([], [])

    # -- Qt model interface ----------------------------------------------

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, column = index.row(), index.column()
        if not (0 <= row < len(self._rows) and 0 <= column < len(self._columns)):
            return None

        if role == self.RowKindRole:
            return self._kinds[row]
        if role == self.RowLabelRole:
            return self._labels[row]

        value = self._rows[row][column]
        if role == self.ValueRole:
            return value
        if role != Qt.DisplayRole:
            return None

        if self._columns[column].get("kind") == "text":
            return "" if value is None else str(value)
        return self._format(value, self._columns[column])

    def _format(self, value, column) -> str:
        if value is None:
            return EM_DASH
        try:
            number = float(value)
        except (TypeError, ValueError):
            return EM_DASH
        if not math.isfinite(number):
            return EM_DASH
        digits = int(column.get("decimals_hint", self._precision))
        return format_engineering(number, min(self._precision, max(3, digits)))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self._columns):
            return self._columns[section]["label"]
        if orientation == Qt.Vertical:
            return section + 1
        return None

    def roleNames(self):
        return {
            Qt.DisplayRole: b"display",
            self.ValueRole: b"value",
            self.RowKindRole: b"rowKind",
            self.RowLabelRole: b"rowLabel",
        }

    # -- presentation -----------------------------------------------------

    @Slot(int)
    def setPrecision(self, digits: int) -> None:
        """Change display precision. The stored values are untouched."""
        digits = max(3, min(12, int(digits)))
        if digits == self._precision:
            return
        self.beginResetModel()
        self._precision = digits
        self.endResetModel()
        self.precisionChanged.emit()

    @Slot(result=int)
    def precision(self) -> int:
        return self._precision

    @Slot(int, int, result=float)
    def valueAt(self, row: int, column: int) -> float:
        """One numeric cell, unformatted. NaN for a text or missing cell."""
        if not (0 <= row < len(self._rows) and 0 <= column < len(self._columns)):
            return float("nan")
        try:
            return float(self._rows[row][column])
        except (TypeError, ValueError):
            return float("nan")

    @Slot(int, result=str)
    def rowAsText(self, row: int) -> str:
        """One row, tab separated, at display precision."""
        if not (0 <= row < len(self._rows)):
            return ""
        return "\t".join(
            str(self.data(self.index(row, column), Qt.DisplayRole) or "")
            for column in range(len(self._columns)))

    @Slot(result=str)
    def headerAsText(self) -> str:
        return "\t".join(column["label"] for column in self._columns)

    @Slot(result=str)
    def tableAsText(self) -> str:
        lines = [self.headerAsText()]
        lines.extend(self.rowAsText(row) for row in range(len(self._rows)))
        return "\n".join(lines)

    def to_csv(self, include_header: bool = True) -> str:
        """Full-precision CSV. Export writes stored values, not display text."""
        lines: list[str] = []
        if include_header:
            lines.append(",".join(column["key"] for column in self._columns))
        for row in self._rows:
            cells = []
            for value, column in zip(row, self._columns):
                if column.get("kind") == "text":
                    cells.append("" if value is None else str(value))
                else:
                    try:
                        cells.append(repr(float(value)))
                    except (TypeError, ValueError):
                        cells.append("")
            lines.append(",".join(cells))
        return "\n".join(lines)

    @property
    def rows(self) -> list[tuple]:
        return list(self._rows)

    @property
    def columns(self) -> list[dict]:
        return [dict(column) for column in self._columns]
