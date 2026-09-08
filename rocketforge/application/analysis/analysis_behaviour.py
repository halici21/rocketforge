"""Shared behaviour for an analysis page controller.

Every analysis page needs the same scaffolding: a precision setting, a table
model, range settings that regenerate on change, copy and CSV export, and
chart series pulled from the same computed block the table shows. None of that
is physics, and writing it three times would give three chances to get it
subtly different.

**Why this is a plain mixin and not a QObject base class.** It was a QObject
base class first. PySide6 builds a corrupt metaobject when a *subclass*
declares ``Property(..., notify=Base.someSignal)``: the notify index points
into the base's metaobject, and the first QML access to that object segfaults
the process -- no exception, no warning. The Qt surface of each controller is
therefore declared in the controller itself, where its signals live, and only
the behaviour is shared from here.

That leaves each controller with a visible block of property boilerplate. That
is the honest cost of the constraint, and it is preferable to a base class that
crashes when someone adds one more property to a subclass.

A class mixing this in must be a QObject and must declare these signals:
``resultsChanged``, ``tableChanged``, ``tableSettingsChanged``,
``referenceChanged`` and ``requestTab``; and must implement ``_compute`` and
``_build_table``.
"""

from __future__ import annotations

import pathlib

from PySide6.QtGui import QGuiApplication

from ..formatting import format_engineering
from .engineering_table_model import EngineeringTableModel
from .presentation import MAX_TABLE_ROWS

__all__ = ["AnalysisBehaviour", "column_dicts", "MAX_TABLE_ROWS"]


def column_dicts(columns) -> list[dict]:
    """Table columns as the plain dicts the model and QML both expect."""
    return [{"key": c.key, "label": c.label, "unit": c.unit,
             "decimals_hint": c.decimals_hint} for c in columns]


class AnalysisBehaviour:
    """Everything an analysis controller does that is not Qt declaration."""

    #: Used to name an exported CSV. Overridden by each controller.
    _export_name = "analysis"

    def _init_analysis(self) -> None:
        """Set up the shared state. Called from the controller's ``__init__``."""
        self._precision = 6
        self._result = None
        self._stale = False

        self._table_model = EngineeringTableModel(self)
        self._table_gamma = 1.4
        self._table_start = 1.0
        self._table_end = 5.0
        self._table_step = 0.05
        self._table_precision = 6
        self._table_message = ""
        self._marker_row = -1
        self._selected_row = -1

    # ------------------------------------------------------------------
    # what a controller provides
    # ------------------------------------------------------------------

    def _compute(self):
        """Call the service and return a ``CalculatorResult``."""
        raise NotImplementedError

    def _build_table(self):
        """Call the service and return a ``TableData``."""
        raise NotImplementedError

    def _marker_text(self) -> str:
        """The label for the highlighted row, if the table has one."""
        return "SONIC"

    def _table_caption(self) -> str:
        """The line printed under the table."""
        rows = self._table_model.rowCount()
        if not rows:
            return ""
        return (f"{rows:,} rows · γ = {self._table_gamma:g} · calorically perfect gas · "
                "calculated by RocketForge")

    def _on_table_built(self, data) -> None:
        """Hook for a controller that keeps state derived from the table."""

    def _on_table_cleared(self) -> None:
        """Hook for a controller that must drop state when the table is refused."""

    # ------------------------------------------------------------------
    # calculator
    # ------------------------------------------------------------------

    def _set_precision_value(self, value: int) -> bool:
        """Clamp and store the readout precision. True if it changed."""
        value = max(3, min(12, int(value)))
        if value == self._precision:
            return False
        self._precision = value
        return True

    def _recalculate(self) -> None:
        self._result = self._compute()
        # Keep the previous readout visible but marked stale rather than
        # blanking the page while someone is midway through typing.
        self._stale = self._result is not None and not self._result.ok
        self.resultsChanged.emit()
        self.referenceChanged.emit()

    def _result_rows(self) -> list:
        """Formatted readout rows, grouped for display.

        ``available`` is False for a quantity this result genuinely does not
        carry -- a mass flow with no area given, say. The interface shows it as
        blank rather than as zero, which would be a different claim entirely.
        """
        if self._result is None or not self._result.ok:
            return []
        return [
            {"key": row.key, "label": row.label, "group": row.group,
             "value": format_engineering(row.value, self._precision),
             "raw": float("nan") if row.value is None else float(row.value),
             "unit": row.unit, "emphasis": row.emphasis,
             "available": row.value is not None}
            for row in self._result.rows
        ]

    def _is_valid(self) -> bool:
        return bool(self._result is not None and self._result.ok)

    def _status_label(self) -> str:
        if self._result is None:
            return "Invalid input"
        return self._result.status

    def _status_message(self) -> str:
        return "" if self._result is None else self._result.message

    def _status_tone(self) -> str:
        """Maps onto the existing chip tones; no new visual vocabulary."""
        if self._result is None or not self._result.ok:
            return "warning"
        if self._result.status in ("Sonic", "Near sonic", "Choked", "Sonic limit",
                                   "Strong shock"):
            return "accent"
        return "success"

    def _diagnostic_dicts(self) -> list:
        if self._result is None:
            return []
        return [{"code": d.code, "severity": str(d.severity), "message": d.message}
                for d in self._result.diagnostics]

    def _mach_value(self) -> float:
        if self._result is None or self._result.mach is None:
            return float("nan")
        return float(self._result.mach)

    def _raw_result_value(self, key: str) -> float:
        """One raw readout by key, for a chart marker or a caption."""
        if self._result is None or not self._result.ok:
            return float("nan")
        value = self._result.value_of(key)
        return float("nan") if value is None else float(value)

    # ------------------------------------------------------------------
    # table
    # ------------------------------------------------------------------

    def _set_table_setting(self, attribute: str, value) -> bool:
        """Store one table setting. True if it changed, so the caller can notify."""
        if getattr(self, attribute) == value:
            return False
        setattr(self, attribute, value)
        return True

    def _set_table_precision_value(self, value: int) -> bool:
        value = max(3, min(12, int(value)))
        if value == self._table_precision:
            return False
        self._table_precision = value
        self._table_model.setPrecision(value)
        return True

    def _regenerate_table(self) -> None:
        """Compute the table from the current settings.

        A refused range clears the model and reports why. It never leaves the
        previous table on screen under the new settings, which would be showing
        one thing while claiming another.
        """
        try:
            data = self._build_table()
        except (ArithmeticError, ValueError, TypeError) as error:
            self._table_model.clear()
            self._table_message = str(error)
            self._marker_row = -1
            self._selected_row = -1
            self._on_table_cleared()
            self.tableChanged.emit()
            self.referenceChanged.emit()
            return

        self._table_model.set_table(
            column_dicts(data.columns), data.values,
            marker_row=data.sonic_row, marker_text=self._marker_text(),
            markers=getattr(data, "markers", None),
            region_column=0, region_threshold=1.0,
        )
        self._table_model.setPrecision(self._table_precision)
        self._marker_row = -1 if data.sonic_row is None else int(data.sonic_row)
        self._table_message = ""
        self._selected_row = -1
        self._on_table_built(data)
        self.tableChanged.emit()
        self.referenceChanged.emit()

    def _column_labels(self) -> list:
        return [{"key": c["key"], "label": c["label"]} for c in self._table_model.columns]

    # ------------------------------------------------------------------
    # actions
    # ------------------------------------------------------------------

    def _copy_text(self, text: str) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)

    def _copy_row(self, row: int) -> None:
        self._copy_text(self._table_model.headerAsText() + "\n"
                        + self._table_model.rowAsText(row))

    def _export_csv(self, directory: str) -> str:
        """Write the generated table as CSV. Returns the path, or an empty string."""
        if not self._table_model.rowCount():
            return ""
        folder = pathlib.Path(directory) if directory else pathlib.Path.home()
        stem = f"rocketforge_{self._export_name}_gamma_{self._table_gamma:g}"
        target = folder / (stem.replace(".", "p") + ".csv")
        try:
            target.write_text(self._table_model.to_csv(), encoding="utf-8")
        except OSError:
            return ""
        return str(target)

    def _chart_series(self, quantity: str) -> list:
        """Points for a chart, taken from the generated table.

        The table and the charts read the same computed block, so the two can
        never disagree about what the physics said. Non-finite entries are
        dropped rather than plotted: an unbounded A/A* at rest is a real value
        the table prints, and a gap is the honest way to draw it.
        """
        values = self._table_model.values
        if values.size == 0:
            return []
        keys = [c["key"] for c in self._table_model.columns]
        if quantity not in keys:
            return []
        column = keys.index(quantity)
        points = []
        for row in range(values.shape[0]):
            y = float(values[row, column])
            if y != y or y in (float("inf"), float("-inf")):
                continue
            points.append({"x": float(values[row, 0]), "y": y})
        return points
