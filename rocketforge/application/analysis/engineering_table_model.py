"""A generic numeric table model for engineering tables.

Knows nothing about compressible flow. It holds a column definition, a float64
block of values and a display precision, and it is what any future table --
normal shock, Prandtl-Meyer, Fanno, Rayleigh -- will reuse without change.

The values stay numeric. Only :meth:`data` formats, and only for display, so
comparison and export always work from full precision (task section 93).
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, Slot

from ..formatting import EM_DASH, format_engineering

__all__ = ["EngineeringTableModel"]


class EngineeringTableModel(QAbstractTableModel):
    """Rows of numbers with labelled columns.

    Roles beyond ``DisplayRole`` exist because the view needs to distinguish a
    physically special row -- the sonic line -- without the model knowing why
    it is special.
    """

    ValueRole = Qt.UserRole + 1        # the unformatted float
    MarkerRole = Qt.UserRole + 2       # row marker, e.g. "sonic"
    RegionRole = Qt.UserRole + 3       # "subsonic" | "sonic" | "supersonic"

    precisionChanged = Signal()
    tableReset = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._columns: list[dict] = []
        self._values: np.ndarray = np.empty((0, 0), dtype=np.float64)
        self._precision = 6
        self._markers: dict[int, str] = {}
        self._region_column = 0
        self._region_threshold = 1.0

    # -- population -------------------------------------------------------

    def set_table(
        self,
        columns: list[dict],
        values: np.ndarray,
        marker_row: int | None = None,
        marker_text: str = "",
        markers: dict[int, str] | None = None,
        region_column: int = 0,
        region_threshold: float = 1.0,
    ) -> None:
        """Replace the whole table in one reset.

        A full reset rather than incremental signals: the table is regenerated
        wholesale whenever an input changes, and pretending otherwise would
        cost more than it saves.

        ``markers`` labels critical rows. Most tables have one -- the sonic row
        -- and pass it as ``marker_row``/``marker_text``. A Rayleigh table has
        two, at M = 1 and at M = 1/sqrt(gamma), and they mean entirely
        different things, so the mapping form exists to let each carry its own
        label rather than sharing one.
        """
        self.beginResetModel()
        self._columns = list(columns)
        self._values = np.ascontiguousarray(values, dtype=np.float64)
        self._markers = dict(markers) if markers else {}
        if marker_row is not None and marker_text:
            self._markers.setdefault(int(marker_row), marker_text)
        self._region_column = region_column
        self._region_threshold = region_threshold
        self.endResetModel()
        self.tableReset.emit()

    def clear(self) -> None:
        self.set_table([], np.empty((0, 0), dtype=np.float64))

    # -- Qt model interface ----------------------------------------------

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else int(self._values.shape[0])

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, column = index.row(), index.column()
        if not (0 <= row < self.rowCount() and 0 <= column < self.columnCount()):
            return None

        value = float(self._values[row, column])
        if role == Qt.DisplayRole:
            digits = self._columns[column].get("decimals_hint", self._precision)
            return format_engineering(value, min(self._precision, max(3, digits)))
        if role == self.ValueRole:
            return value
        if role == self.MarkerRole:
            return self._markers.get(row, "")
        if role == self.RegionRole:
            independent = float(self._values[row, self._region_column])
            if abs(independent - self._region_threshold) < 1e-12:
                return "sonic"
            return "subsonic" if independent < self._region_threshold else "supersonic"
        return None

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
            self.MarkerRole: b"marker",
            self.RegionRole: b"region",
        }

    # -- presentation -----------------------------------------------------

    @Slot(int)
    def setPrecision(self, digits: int) -> None:
        """Change display precision. The stored numbers are untouched."""
        digits = max(3, min(12, int(digits)))
        if digits == self._precision:
            return
        # A full reset rather than dataChanged: every displayed string changes,
        # and the view's delegates re-evaluate their text bindings on rebuild.
        self.beginResetModel()
        self._precision = digits
        self.endResetModel()
        self.precisionChanged.emit()

    @Slot(result=int)
    def precision(self) -> int:
        return self._precision

    @Slot(int, result=float)
    def machAt(self, row: int) -> float:
        """The independent-variable value of a row, unformatted."""
        if 0 <= row < self.rowCount():
            return float(self._values[row, self._region_column])
        return float("nan")

    @Slot(float, result=int)
    def rowNearest(self, value: float) -> int:
        """Index of the row whose independent variable is closest to ``value``."""
        if not self.rowCount():
            return -1
        column = self._values[:, self._region_column]
        return int(np.argmin(np.abs(column - float(value))))

    @Slot(int, result=str)
    def rowAsText(self, row: int) -> str:
        """One row as tab-separated text, at display precision.

        Tab-separated because that is what pastes correctly into a spreadsheet,
        MATLAB and a Python session alike.
        """
        if not (0 <= row < self.rowCount()):
            return ""
        return "\t".join(
            format_engineering(float(self._values[row, c]), self._precision)
            for c in range(self.columnCount())
        )

    @Slot(result=str)
    def headerAsText(self) -> str:
        return "\t".join(column["label"] for column in self._columns)

    @Slot(result=str)
    def tableAsText(self) -> str:
        """The whole table as tab-separated text, header included."""
        lines = [self.headerAsText()]
        lines.extend(self.rowAsText(row) for row in range(self.rowCount()))
        return "\n".join(lines)

    def to_csv(self, include_header: bool = True) -> str:
        """Full-precision CSV.

        Export writes the stored numbers, not the display strings: a value
        rounded for the screen should not become the value someone analyses.
        """
        lines = []
        if include_header:
            lines.append(",".join(column["key"] for column in self._columns))
        for row in range(self.rowCount()):
            lines.append(",".join(repr(float(self._values[row, c]))
                                  for c in range(self.columnCount())))
        return "\n".join(lines)

    @property
    def values(self) -> np.ndarray:
        return self._values

    @property
    def columns(self) -> list[dict]:
        return list(self._columns)
