"""The QObject the Isentropic Flow page binds to.

Thin by design. It validates what the interface sent, calls
:mod:`isentropic_service`, and republishes the answer as properties QML can
bind to. It contains no relation, no ratio algebra and no tolerance policy --
each of those lives one layer down, where it is tested without Qt.

This is the only file in the analysis stack that imports Qt.
"""

from __future__ import annotations

import pathlib

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication

from ...core.errors import RocketForgeError
from ...physics.compressible import FlowBranch
from ..formatting import EM_DASH, format_engineering
from ..visualization.selection import AnalysisSelection
from ..visualization.table import block_text, clamp_block, table_block
from . import reference_comparison as reference
from .engineering_table_model import EngineeringTableModel
from .isentropic_service import (
    MAX_TABLE_ROWS,
    SOLVE_MODES,
    SolveMode,
    TableConvention,
    columns_for,
    generate_table,
    solve,
)

__all__ = ["IsentropicController"]


def _column_dicts(columns) -> list[dict]:
    return [{"key": c.key, "label": c.label, "unit": c.unit,
             "decimals_hint": c.decimals_hint} for c in columns]


class IsentropicController(QObject):
    """Application-side facade for the Isentropic Flow analysis page."""

    resultsChanged = Signal()
    inputsChanged = Signal()
    tableChanged = Signal()
    tableSettingsChanged = Signal()
    referenceChanged = Signal()
    selectionReadoutChanged = Signal()
    requestTab = Signal(int)          # ask the page to switch section

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        # calculator state
        self._mode = SolveMode.MACH.value
        self._input = 2.0
        self._gamma = 1.4
        self._branch = FlowBranch.SUPERSONIC.value
        self._precision = 6
        self._result = None
        self._stale = False
        self._current_comparison: list = []

        # table state
        self._table_model = EngineeringTableModel(self)
        self._table_gamma = 1.4
        self._table_start = 0.02
        self._table_end = 5.0
        self._table_step = 0.02
        self._table_convention = TableConvention.ANDERSON.value
        self._table_precision = 6
        self._include_sonic = True
        self._table_message = ""
        self._sonic_row = -1
        # The gamma the current table was generated with. tableGamma is the
        # setting, which may be edited ahead of the next Generate; a curve
        # must be labelled with what it was computed from.
        self._plotted_gamma = float("nan")

        # reference state
        self._compare = False
        self._selected_row = -1
        self._summary: dict = {}
        # Row -> comparison, made with the table comparison (Compare on, a
        # regenerated table) so that selecting a row reads one instead of
        # re-running the relations because a row was clicked.
        self._row_comparisons: dict[int, list] = {}

        # Which solved state and which generated table the views show, and
        # one selection shared by the chart, the table and the inspector.
        self._identity = 0
        self._table_identity = 0
        self._selection = AnalysisSelection(self)
        self._selection.changed.connect(self.selectionReadoutChanged)
        self.tableChanged.connect(self.selectionReadoutChanged)
        self.resultsChanged.connect(self.selectionReadoutChanged)

        self._recalculate()
        self.regenerateTable()

    # ==================================================================
    # calculator
    # ==================================================================

    @Property("QVariantList", constant=True)
    def solveModes(self):
        """The menu of things the user may solve from."""
        return [
            {"key": info.mode.value, "label": info.label, "symbol": info.symbol,
             "hint": info.hint, "needsBranch": info.needs_branch,
             "defaultValue": info.default_value}
            for info in SOLVE_MODES
        ]

    def _get_mode(self) -> str:
        return self._mode

    def _set_mode(self, value: str) -> None:
        if value == self._mode:
            return
        self._mode = value
        # Offer a sensible starting value for the new quantity rather than
        # reinterpreting the previous one, which would usually be out of domain.
        for info in SOLVE_MODES:
            if info.mode.value == value:
                self._input = info.default_value
                break
        self.inputsChanged.emit()
        self._recalculate()

    mode = Property(str, _get_mode, _set_mode, notify=inputsChanged)

    def _get_input(self) -> float:
        return self._input

    def _set_input(self, value: float) -> None:
        if value == self._input:
            return
        self._input = float(value)
        self.inputsChanged.emit()
        self._recalculate()

    inputValue = Property(float, _get_input, _set_input, notify=inputsChanged)

    def _get_gamma(self) -> float:
        return self._gamma

    def _set_gamma(self, value: float) -> None:
        if value == self._gamma:
            return
        self._gamma = float(value)
        self.inputsChanged.emit()
        self._recalculate()

    gamma = Property(float, _get_gamma, _set_gamma, notify=inputsChanged)

    def _get_branch(self) -> str:
        return self._branch

    def _set_branch(self, value: str) -> None:
        if value == self._branch:
            return
        self._branch = value
        self.inputsChanged.emit()
        self._recalculate()

    branch = Property(str, _get_branch, _set_branch, notify=inputsChanged)

    def _get_precision(self) -> int:
        return self._precision

    def _set_precision(self, value: int) -> None:
        value = max(3, min(12, int(value)))
        if value == self._precision:
            return
        self._precision = value
        self.resultsChanged.emit()

    precision = Property(int, _get_precision, _set_precision, notify=resultsChanged)

    @Property(bool, notify=inputsChanged)
    def branchRequired(self) -> bool:
        """Whether the current mode needs a branch. Drives the control's visibility."""
        return any(i.mode.value == self._mode and i.needs_branch for i in SOLVE_MODES)

    def _recalculate(self) -> None:
        try:
            self._result = solve(self._mode, self._input, self._gamma, self._branch)
        except (RocketForgeError, ValueError) as error:   # defensive: solve() catches
            self._result = None
            self._table_message = str(error)
        # Keep the previous readout visible but marked stale rather than
        # blanking the page while someone is midway through typing.
        self._stale = self._result is not None and not self._result.ok
        # The reference check for this result, made with it rather than when
        # a view first reads it: opening the page must solve nothing.
        self._current_comparison = self.comparisonForCurrentMach()
        self._identity += 1
        self.resultsChanged.emit()
        self.referenceChanged.emit()

    @Property("QVariantList", notify=resultsChanged)
    def results(self):
        """Formatted readout rows, grouped for display."""
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

    @Property(bool, notify=resultsChanged)
    def valid(self) -> bool:
        return bool(self._result is not None and self._result.ok)

    @Property(bool, notify=resultsChanged)
    def stale(self) -> bool:
        """Results shown are from an earlier, valid input."""
        return self._stale

    @Property(str, notify=resultsChanged)
    def statusLabel(self) -> str:
        if self._result is None:
            return "Invalid input"
        return self._result.status

    @Property(str, notify=resultsChanged)
    def statusMessage(self) -> str:
        return "" if self._result is None else self._result.message

    # -- flow regime -------------------------------------------------------
    #
    # Decided here from the solved Mach number, never in QML. Only the three
    # regimes the model itself distinguishes: M < 1, M = 1, M > 1. "Transonic"
    # and "hypersonic" are conventions with no boundary in this model, so they
    # are not offered.

    def _regime(self) -> str:
        if self._result is None or not self._result.ok or self._result.mach is None:
            return ""
        if self._result.status == "Sonic":
            return "Sonic"
        return "Subsonic" if self._result.mach < 1.0 else "Supersonic"

    @Property(str, notify=resultsChanged)
    def flowRegime(self) -> str:
        return self._regime()

    @Property(str, notify=resultsChanged)
    def flowRegimeTone(self) -> str:
        return {"Subsonic": "success", "Sonic": "accent",
                "Supersonic": "accent"}.get(self._regime(), "neutral")

    @Property(str, notify=resultsChanged)
    def flowRegimeNote(self) -> str:
        """One line on what the regime means here, from values already solved."""
        regime = self._regime()
        if regime == "Subsonic":
            return "M < 1: no Mach wave; area and velocity change in opposite senses."
        if regime == "Sonic":
            return "M = 1: the sonic condition; the area is a minimum here."
        if regime == "Supersonic":
            angle = next((r for r in self._result.rows if r.key == "mach_angle"), None)
            if angle is not None and angle.value is not None:
                return (f"M > 1: Mach angle μ = "
                        f"{format_engineering(angle.value, self._precision)}°.")
            return "M > 1."
        return ""

    @Property(str, notify=resultsChanged)
    def statusTone(self) -> str:
        """Maps onto the existing chip tones; no new visual vocabulary."""
        if self._result is None or not self._result.ok:
            return "warning"
        if self._result.status in ("Sonic", "Near sonic"):
            return "accent"
        return "success"

    @Property("QVariantList", notify=resultsChanged)
    def diagnostics(self):
        if self._result is None:
            return []
        return [{"code": d.code, "severity": str(d.severity), "message": d.message}
                for d in self._result.diagnostics]

    @Property("QVariantList", notify=resultsChanged)
    def bothBranches(self):
        """Subsonic and supersonic roots, when the user asked for both."""
        if self._result is None or self._result.both is None:
            return []
        subsonic, supersonic = self._result.both
        return [
            {"label": "Subsonic M", "value": format_engineering(subsonic, self._precision),
             "raw": float(subsonic)},
            {"label": "Supersonic M", "value": format_engineering(supersonic, self._precision),
             "raw": float(supersonic)},
        ]

    @Property(float, notify=resultsChanged)
    def mach(self) -> float:
        if self._result is None or self._result.mach is None:
            return float("nan")
        return float(self._result.mach)

    @Property("QVariantList", constant=True)
    def assumptions(self):
        """The model's standing assumptions, from the physics registry."""
        from ...physics.compressible import equations

        record = equations.record("isentropic.pressure_ratio.v1")
        return list(record.assumptions)

    @Property(str, constant=True)
    def modelName(self) -> str:
        return "Calorically perfect gas"

    @Slot(float)
    def setMachAndSolve(self, mach: float) -> None:
        """Jump the calculator to a Mach number, used by the table."""
        self._mode = SolveMode.MACH.value
        self._input = float(mach)
        self.inputsChanged.emit()
        self._recalculate()

    # ==================================================================
    # table
    # ==================================================================

    @Property(QObject, constant=True)
    def tableModel(self) -> EngineeringTableModel:
        return self._table_model

    def _table_property(name, cast, signal_name="tableSettingsChanged"):  # noqa: N805
        attribute = f"_table_{name}"

        def getter(self):
            return getattr(self, attribute)

        def setter(self, value):
            value = cast(value)
            if value == getattr(self, attribute):
                return
            setattr(self, attribute, value)
            getattr(self, signal_name).emit()

        return getter, setter

    _g, _s = _table_property("gamma", float)
    tableGamma = Property(float, _g, _s, notify=tableSettingsChanged)
    _g, _s = _table_property("start", float)
    tableStart = Property(float, _g, _s, notify=tableSettingsChanged)
    _g, _s = _table_property("end", float)
    tableEnd = Property(float, _g, _s, notify=tableSettingsChanged)
    _g, _s = _table_property("step", float)
    tableStep = Property(float, _g, _s, notify=tableSettingsChanged)
    _g, _s = _table_property("convention", str)
    tableConvention = Property(str, _g, _s, notify=tableSettingsChanged)
    del _g, _s, _table_property

    def _get_table_precision(self) -> int:
        return self._table_precision

    def _set_table_precision(self, value: int) -> None:
        value = max(3, min(12, int(value)))
        if value == self._table_precision:
            return
        self._table_precision = value
        self._table_model.setPrecision(value)
        self.tableSettingsChanged.emit()

    tablePrecision = Property(int, _get_table_precision, _set_table_precision,
                              notify=tableSettingsChanged)

    def _get_include_sonic(self) -> bool:
        return self._include_sonic

    def _set_include_sonic(self, value: bool) -> None:
        if bool(value) == self._include_sonic:
            return
        self._include_sonic = bool(value)
        self.tableSettingsChanged.emit()

    includeSonic = Property(bool, _get_include_sonic, _set_include_sonic,
                            notify=tableSettingsChanged)

    @Slot()
    def regenerateTable(self) -> None:
        """Compute the table from the current settings."""
        try:
            data = generate_table(
                self._table_gamma, self._table_start, self._table_end,
                self._table_step, self._table_convention, self._include_sonic,
            )
        except (RocketForgeError, ValueError) as error:
            self._table_model.clear()
            self._table_message = str(error)
            self._sonic_row = -1
            self._plotted_gamma = float("nan")
            self._summary = {}
            self._row_comparisons = {}
            self._table_identity += 1
            self._drop_table_selection()
            self.tableChanged.emit()
            self.referenceChanged.emit()
            return

        self._table_model.set_table(
            _column_dicts(data.columns), data.values,
            marker_row=data.sonic_row, marker_text="SONIC",
            region_column=0, region_threshold=1.0,
        )
        self._table_model.setPrecision(self._table_precision)
        self._sonic_row = -1 if data.sonic_row is None else int(data.sonic_row)
        self._plotted_gamma = self._table_gamma
        self._table_message = ""
        self._selected_row = -1
        self._refresh_summary()
        self._table_identity += 1
        self._drop_table_selection()
        self.tableChanged.emit()
        self.referenceChanged.emit()

    @Property(int, notify=tableChanged)
    def tableRowCount(self) -> int:
        return self._table_model.rowCount()

    # ------------------------------------------------------------------
    # selection, shared by the chart, the table and the inspector
    # ------------------------------------------------------------------

    def _drop_table_selection(self) -> None:
        """A selected sample of the previous table means nothing in the new one."""
        if self._selection.kind in ("plotPoint", "tableRow", "tableRange"):
            self._selection.clear()

    @Property(int, notify=resultsChanged)
    def resultIdentity(self) -> int:
        return self._identity

    @Property(int, notify=tableChanged)
    def tableIdentity(self) -> int:
        return self._table_identity

    @Property(QObject, constant=True)
    def selection(self) -> QObject:
        return self._selection

    def _row_at(self, mach: float) -> int:
        """The generated row whose Mach number is exactly ``mach``, else -1."""
        row = self._table_model.rowNearest(mach)
        if row < 0 or self._table_model.machAt(row) != mach:
            return -1
        return row

    @Slot(int)
    def selectTableRow(self, row: int) -> None:
        """Select a generated row: the chart and the inspector follow it."""
        if not 0 <= row < self._table_model.rowCount():
            return
        mach = self._table_model.machAt(row)
        self._selection.select("tableRow", str(row), mach, f"row {row + 1}", "table")

    def _cell_text(self, row: int, column: int) -> str:
        value = self._table_model.data(self._table_model.index(row, column))
        return "" if value is None else str(value)

    @Slot(int, int)
    def selectTableRange(self, first: int, last: int) -> None:
        """Select a contiguous block of generated rows (the chart shows the interval)."""
        span = clamp_block(first, last, self._table_model.rowCount())
        if span is None:
            return
        a, b = span
        if a == b:
            self.selectTableRow(a)
            return
        label = f"M {self._cell_text(a, 0)}–{self._cell_text(b, 0)}"
        self._selection.selectRange("tableRange", f"rows:{a}-{b}", self._table_model.machAt(a),
                                    self._table_model.machAt(b), label, "table")

    @Slot(int, int, result="QVariantMap")
    def tableSnapshot(self, first: int, last: int):
        """Rows ``first``..``last`` as a table snapshot, exactly as shown."""
        model = self._table_model
        try:
            return table_block(source="isentropic.table", identity=self._table_identity,
                               columns=model.columns, values=model.values, text_at=self._cell_text,
                               first=first, last=last, key_symbol="M",
                               stale=self._table_gamma != self._plotted_gamma,
                               gamma=self._plotted_gamma, convention=self._table_convention,
                               precision=self._table_precision,
                               provenance=f"Generated by RocketForge at γ = {self._plotted_gamma:g}")
        except (ValueError, IndexError):
            return {}

    @Slot(int, int)
    def copyTableRows(self, first: int, last: int) -> None:
        span = clamp_block(first, last, self._table_model.rowCount())
        if span is None:
            return
        header = [c["label"] for c in self._table_model.columns]
        self.copyText(block_text(header, self._cell_text, span[0], span[1], len(header)))

    @Slot(float, result=int)
    def rowExactly(self, mach: float) -> int:
        """The row generated at exactly ``mach``, else -1 (no nearest-row guess)."""
        return self._row_at(mach)

    @Property("QVariantMap", notify=selectionReadoutChanged)
    def selectionReadout(self):
        """The inspector's reading of the selection -- the generated row, as shown.

        A point on the curve and a table row are the same thing, a sample of
        the generated table; both read back that row's own formatted values.
        The solved state reads the calculator's rows. Nothing is recomputed.
        """
        selection = self._selection
        model = self._table_model
        base = {"stale": self._table_gamma != self._plotted_gamma}
        if selection.kind in ("plotPoint", "tableRow"):
            row = self._row_at(selection.x)
            if row < 0:
                return {}
            rows = []
            for column, spec in enumerate(model.columns):
                rows.append({"label": spec["label"],
                             "value": model.data(model.index(row, column)),
                             "unit": spec.get("unit", "")})
            return dict(base, kind=selection.kind, key=str(row),
                        title=f"Table row {row + 1}",
                        note=(f"A generated sample at γ = {self._plotted_gamma:g}; "
                              "the curve is drawn through these samples."),
                        rows=rows, identity=self._table_identity,
                        fidelity="Calculated by RocketForge · calorically perfect gas")
        if selection.kind == "tableRange":
            a, b = self._row_at(selection.x), self._row_at(selection.x1)
            if a < 0 or b < 0:
                return {}
            rows = [{"label": spec["label"],
                     "value": f"{self._cell_text(a, c)}  →  {self._cell_text(b, c)}",
                     "unit": spec.get("unit", "")}
                    for c, spec in enumerate(model.columns)]
            return dict(base, kind="tableRange", key=selection.key,
                        title=f"Rows {a + 1}–{b + 1}  ·  {selection.label}",
                        note=(f"{b - a + 1} generated samples at γ = {self._plotted_gamma:g}; "
                              "first and last row of the range, as shown in the table."),
                        rows=rows, identity=self._table_identity,
                        fidelity="Calculated by RocketForge · calorically perfect gas")
        if selection.kind == "state":
            rows = [{"label": r["label"], "value": r["value"], "unit": r.get("unit", "")}
                    for r in self.results]
            if not rows:
                return {}
            return {"kind": "state", "key": "state", "title": "Solved state",
                    "note": self.flowRegime, "rows": rows, "identity": self._identity,
                    "fidelity": "Calculated by RocketForge · calorically perfect gas",
                    "stale": False}
        return {}

    @Property(str, notify=tableChanged)
    def tableMessage(self) -> str:
        return self._table_message

    @Property(int, notify=tableChanged)
    def sonicRow(self) -> int:
        return self._sonic_row

    @Property(int, constant=True)
    def maxTableRows(self) -> int:
        return MAX_TABLE_ROWS

    @Property("QVariantList", notify=tableChanged)
    def tableColumns(self):
        return [{"key": c["key"], "label": c["label"]} for c in self._table_model.columns]

    @Property(str, notify=tableChanged)
    def tableFooter(self) -> str:
        rows = self._table_model.rowCount()
        if not rows:
            return ""
        return (f"{rows:,} rows · γ = {self._table_gamma:g} · calorically perfect gas · "
                "calculated by RocketForge")

    # ==================================================================
    # reference comparison
    # ==================================================================

    def _get_compare(self) -> bool:
        return self._compare

    def _set_compare(self, value: bool) -> None:
        if bool(value) == self._compare:
            return
        self._compare = bool(value)
        self._refresh_summary()
        self.referenceChanged.emit()

    compareEnabled = Property(bool, _get_compare, _set_compare, notify=referenceChanged)

    @Property(bool, notify=tableChanged)
    def referenceAvailable(self) -> bool:
        """Whether the published table applies to the current gamma.

        A gamma = 1.22 calculation has nothing to check against a gamma = 1.4
        table, so comparison is switched off rather than shown as failing.
        """
        try:
            return abs(self._table_gamma - reference.load_reference().gamma) < 1e-12
        except OSError:
            return False

    @Property(float, constant=True)
    def referenceGamma(self) -> float:
        try:
            return reference.load_reference().gamma
        except OSError:
            return float("nan")

    @Property(str, constant=True)
    def referenceCitation(self) -> str:
        try:
            return reference.load_reference().citation
        except OSError:
            return ""

    @Property(str, notify=tableChanged)
    def referenceMessage(self) -> str:
        if self.referenceAvailable:
            return ""
        return (f"Appendix A is published for γ = {self.referenceGamma:g}. "
                f"Comparison is unavailable at γ = {self._table_gamma:g}.")

    def _refresh_summary(self) -> None:
        self._row_comparisons = {}
        if not (self._compare and self.referenceAvailable):
            self._summary = {}
            return
        self._row_comparisons = {row: self._compare_row(row)
                                 for row in range(self._table_model.rowCount())}
        machs = [self._table_model.machAt(r) for r in range(self._table_model.rowCount())]
        summary = reference.compare_table(self._table_gamma, machs)
        self._summary = {
            "rows": summary.rows_compared,
            "values": summary.values_compared,
            "pass": summary.passed,
            "review": summary.review,
            "passFraction": summary.pass_fraction,
            "maxAbsolute": format_engineering(summary.max_absolute_difference, 4),
            "maxRelative": format_engineering(summary.max_relative_difference, 4),
            "worst": summary.worst,
            "citation": summary.citation,
            "status": "PASS" if summary.all_passed else "REVIEW",
            "reviewMachs": [rc.mach for rc in summary.reviews],
        }

    @Property("QVariantMap", notify=referenceChanged)
    def comparisonSummary(self):
        return self._summary

    @Slot(int, result="QVariantList")
    def comparisonForRow(self, row: int):
        """Per-quantity comparison for one generated row.

        Read from the comparison made with the table while Compare is on;
        computed only when asked outside it (a script, a test).

        Returns an empty list when that Mach number is not tabulated in the
        source: no interpolated reference values, ever.
        """
        if not self.referenceAvailable:
            return []
        if row in self._row_comparisons:
            return self._row_comparisons[row]
        return self._compare_row(row)

    def _compare_row(self, row: int) -> list:
        mach = self._table_model.machAt(row)
        comparison = reference.compare_row(mach, self._table_gamma)
        if comparison is None:
            return []
        return [
            {"label": q.label,
             "computed": format_engineering(q.computed, 7),
             "reference": format_engineering(q.reference, 7),
             "difference": format_engineering(q.difference, 3),
             "relative": format_engineering(q.relative_difference, 3),
             "tolerance": format_engineering(q.tolerance, 3),
             "status": q.status}
            for q in comparison.quantities
        ]

    @Slot(int, result=bool)
    def hasReferenceRow(self, row: int) -> bool:
        if not self.referenceAvailable:
            return False
        return reference.compare_row(self._table_model.machAt(row), self._table_gamma) is not None

    @Property("QVariantList", notify=resultsChanged)
    def currentMachComparison(self):
        """:meth:`comparisonForCurrentMach` for the current result, held."""
        return self._current_comparison

    @Slot(result="QVariantList")
    def comparisonForCurrentMach(self):
        """Compare the calculator's current Mach against the published table."""
        if self._result is None or self._result.mach is None:
            return []
        if abs(self._gamma - self.referenceGamma) > 1e-12:
            return []
        comparison = reference.compare_row(self._result.mach, self._gamma)
        if comparison is None:
            return []
        return [
            {"label": q.label,
             "computed": format_engineering(q.computed, 7),
             "reference": format_engineering(q.reference, 7),
             "difference": format_engineering(q.difference, 3),
             "status": q.status}
            for q in comparison.quantities
        ]

    # ==================================================================
    # actions
    # ==================================================================

    @Slot(int)
    def selectRow(self, row: int) -> None:
        self._selected_row = int(row)
        self.referenceChanged.emit()

    @Property(int, notify=referenceChanged)
    def selectedRow(self) -> int:
        return self._selected_row

    @Slot(float, result=int)
    def rowNearest(self, mach: float) -> int:
        return self._table_model.rowNearest(mach)

    @Slot(str)
    def copyText(self, text: str) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)

    @Slot(int)
    def copyRow(self, row: int) -> None:
        self.copyText(self._table_model.headerAsText() + "\n" + self._table_model.rowAsText(row))

    @Slot()
    def copyTable(self) -> None:
        self.copyText(self._table_model.tableAsText())

    @Slot(str, result=str)
    def exportCsv(self, directory: str) -> str:
        """Write the generated table as CSV. Returns the path, or an empty string."""
        if not self._table_model.rowCount():
            return ""
        folder = pathlib.Path(directory) if directory else pathlib.Path.home()
        name = f"rocketforge_isentropic_gamma_{self._table_gamma:g}".replace(".", "p") + ".csv"
        target = folder / name
        try:
            target.write_text(self._table_model.to_csv(), encoding="utf-8")
        except OSError:
            return ""
        return str(target)

    @Property(float, notify=tableChanged)
    def plottedGamma(self) -> float:
        """The gamma of the generated table, NaN when there is none."""
        return self._plotted_gamma

    @Property("QVariantMap", notify=tableChanged)
    def chartData(self):
        """Quantity key -> :meth:`chartSeries` for every plotted column.

        A property, so a chart bound to it follows a regenerated table: a
        binding never re-calls a slot, and the Relation view once kept the
        previous table's curve beneath a caption naming the new gamma.
        Read from the generated block; nothing is solved.
        """
        keys = [c["key"] for c in self._table_model.columns if c["key"] != "mach"]
        return {key: self.chartSeries(key) for key in keys}

    @Slot(str, result="QVariantList")
    def chartSeries(self, quantity: str):
        """Points for a chart, taken from the generated table.

        The table and the charts read the same computed block, so the two can
        never disagree about what the physics said.
        """
        values = self._table_model.values
        if values.size == 0:
            return []
        keys = [c["key"] for c in self._table_model.columns]
        if quantity not in keys:
            return []
        column = keys.index(quantity)
        return [{"x": float(values[r, 0]), "y": float(values[r, column])}
                for r in range(values.shape[0])]
