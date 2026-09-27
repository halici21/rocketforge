"""The QObject the Normal Shock page binds to.

Thin by design: validate, call :mod:`normal_shock_service`, republish. The one
thing it adds beyond the shared behaviour is the Appendix B comparison, which
follows the same rule as everywhere else in RocketForge -- the published table
is compared against, never read for an answer.

The behaviour is shared with the other analysis pages through
:class:`AnalysisBehaviour`; the Qt surface is declared here rather than
inherited, for the reason that module's docstring sets out.

The view state -- one selection shared by the table, the relation chart and
the inspector, table blocks for pinning and copying, and the view data made
*with* a result or a table (the reference check of the solved M₁, the chart
series) -- is presentation over values that already exist. Nothing a view
reads here solves anything; only an input edit or Generate does.
"""

from __future__ import annotations

import math

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..formatting import format_engineering
from ..visualization.selection import AnalysisSelection
from ..visualization.table import block_text, clamp_block, table_block
from . import reference_comparison as reference
from .analysis_behaviour import MAX_TABLE_ROWS, AnalysisBehaviour
from .normal_shock_service import (
    SOLVE_MODES,
    SolveMode,
    TableConvention,
    UpstreamState,
    generate_table,
    limits_for,
    mode_info,
    solve,
)

__all__ = ["NormalShockController"]


class NormalShockController(AnalysisBehaviour, QObject):
    """Application-side facade for the Normal Shock analysis page."""

    resultsChanged = Signal()
    inputsChanged = Signal()
    stateChanged = Signal()
    tableChanged = Signal()
    tableSettingsChanged = Signal()
    referenceChanged = Signal()
    selectionReadoutChanged = Signal()
    tableStaleChanged = Signal()
    requestTab = Signal(int)

    _export_name = "normal_shock"

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._init_analysis()

        # calculator state
        self._mode = SolveMode.MACH_UPSTREAM.value
        self._input = 2.0
        self._gamma = 1.4

        # optional upstream conditions
        self._upstream_pressure = 101325.0
        self._upstream_temperature = 288.15

        # table state
        self._table_start = 1.0
        self._table_end = 5.0
        self._table_step = 0.02
        self._table_convention = TableConvention.ANDERSON.value

        # reference state
        self._compare = False
        self._summary: dict = {}
        # Row -> comparison, made with the table comparison (Compare on, a
        # regenerated table) so that selecting a row reads one instead of
        # re-running the relations because a row was clicked.
        self._row_comparisons: dict[int, list] = {}

        # view state: which solved state and which generated table the views
        # show, the settings that table was generated with, and one selection
        # shared by the table, the chart and the inspector.
        self._identity = 0
        self._table_identity = 0
        self._generated: dict = {}
        self._current_comparison: list = []
        self._limits_memo: tuple | None = None
        self._selection = AnalysisSelection(self)
        self._selection.changed.connect(self.selectionReadoutChanged)
        self.tableChanged.connect(self.selectionReadoutChanged)
        self.resultsChanged.connect(self.selectionReadoutChanged)
        self.tableChanged.connect(self.tableStaleChanged)
        self.tableSettingsChanged.connect(self.tableStaleChanged)

        self._recalculate()
        self.regenerateTable()

    # ==================================================================
    # calculator inputs
    # ==================================================================

    @Property("QVariantList", constant=True)
    def solveModes(self):
        return [
            {"key": info.mode.value, "label": info.label, "symbol": info.symbol,
             "hint": info.hint, "iterative": info.iterative,
             "defaultValue": info.default_value}
            for info in SOLVE_MODES
        ]

    def _get_mode(self) -> str:
        return self._mode

    def _set_mode(self, value: str) -> None:
        if value == self._mode:
            return
        self._mode = value
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
        if float(value) == self._input:
            return
        self._input = float(value)
        self.inputsChanged.emit()
        self._recalculate()

    inputValue = Property(float, _get_input, _set_input, notify=inputsChanged)

    def _get_gamma(self) -> float:
        return self._gamma

    def _set_gamma(self, value: float) -> None:
        if float(value) == self._gamma:
            return
        self._gamma = float(value)
        self.inputsChanged.emit()
        self._recalculate()

    gamma = Property(float, _get_gamma, _set_gamma, notify=inputsChanged)

    @Property(str, notify=inputsChanged)
    def inputSymbol(self) -> str:
        return mode_info(self._mode).symbol

    @Property(str, notify=inputsChanged)
    def inputHint(self) -> str:
        return mode_info(self._mode).hint

    @Property(bool, notify=inputsChanged)
    def modeIsIterative(self) -> bool:
        """Whether the current mode is solved by iteration.

        Shown in the interface because it is true and useful: four of the five
        inverses are closed form, and a reader should be able to tell which
        answer came from a root solve.
        """
        return mode_info(self._mode).iterative

    # ------------------------------------------------------------------
    # optional upstream conditions
    # ------------------------------------------------------------------

    def _upstream(self) -> UpstreamState:
        return UpstreamState(pressure=self._upstream_pressure,
                             temperature=self._upstream_temperature)

    def _get_upstream_pressure(self) -> float:
        return self._upstream_pressure

    def _set_upstream_pressure(self, value: float) -> None:
        if float(value) == self._upstream_pressure:
            return
        self._upstream_pressure = float(value)
        self.stateChanged.emit()
        self._recalculate()

    upstreamPressure = Property(float, _get_upstream_pressure, _set_upstream_pressure,
                                notify=stateChanged)

    def _get_upstream_temperature(self) -> float:
        return self._upstream_temperature

    def _set_upstream_temperature(self, value: float) -> None:
        if float(value) == self._upstream_temperature:
            return
        self._upstream_temperature = float(value)
        self.stateChanged.emit()
        self._recalculate()

    upstreamTemperature = Property(float, _get_upstream_temperature,
                                   _set_upstream_temperature, notify=stateChanged)

    @Property(bool, notify=stateChanged)
    def dimensionalAvailable(self) -> bool:
        return self._upstream().complete

    @Property(str, notify=stateChanged)
    def dimensionalMessage(self) -> str:
        if self._upstream().complete:
            return ""
        return ("Enter a positive upstream static pressure and temperature to obtain "
                "downstream values in Pa and K. The ratios above do not need them.")

    # ==================================================================
    # results
    # ==================================================================

    def _compute(self):
        return solve(self._mode, self._input, self._gamma, self._upstream())

    def _recalculate(self) -> None:
        """The shared recalculation, plus the view data made with the result.

        The same four steps as :meth:`AnalysisBehaviour._recalculate`; the
        reference check of the solved M₁ and the strong-shock limits are made
        here, with the result, rather than when a view first reads them:
        opening the page, or coming back to it, must solve nothing.
        """
        self._result = self._compute()
        self._stale = self._result is not None and not self._result.ok
        try:
            self._current_comparison = self.comparisonForCurrentMach()
        except OSError:                      # the appendix could not be read
            self._current_comparison = []
        self._identity += 1
        self._strong_shock_limits(quiet=True)
        self.resultsChanged.emit()
        self.referenceChanged.emit()

    def _get_precision(self) -> int:
        return self._precision

    def _set_precision(self, value: int) -> None:
        if self._set_precision_value(value):
            self.resultsChanged.emit()

    precision = Property(int, _get_precision, _set_precision, notify=resultsChanged)

    @Property("QVariantList", notify=resultsChanged)
    def results(self):
        return self._result_rows()

    @Property(bool, notify=resultsChanged)
    def valid(self) -> bool:
        return self._is_valid()

    @Property(bool, notify=resultsChanged)
    def stale(self) -> bool:
        return self._stale

    @Property(str, notify=resultsChanged)
    def statusLabel(self) -> str:
        return self._status_label()

    @Property(str, notify=resultsChanged)
    def statusMessage(self) -> str:
        return self._status_message()

    @Property(str, notify=resultsChanged)
    def statusTone(self) -> str:
        return self._status_tone()

    @Property("QVariantList", notify=resultsChanged)
    def diagnostics(self):
        return self._diagnostic_dicts()

    @Property(float, notify=resultsChanged)
    def mach(self) -> float:
        return self._mach_value()

    @Slot(str, result=float)
    def resultValue(self, key: str) -> float:
        return self._raw_result_value(key)

    def _strong_shock_limits(self, quiet: bool = False):
        """The limits for the current gamma, held until gamma changes.

        A refused gamma is not held: reading it raises exactly as before, and
        ``quiet`` (the recalculation warming it) only swallows that refusal.
        """
        memo = self._limits_memo
        if memo is not None and memo[0] == self._gamma:
            return memo[1]
        try:
            density, mach = limits_for(self._gamma)
        except Exception:
            if quiet:
                return None
            raise
        value = {
            "densityRatio": format_engineering(density, 6),
            "machDownstream": format_engineering(mach, 6),
            "caption": (
                f"However strong the shock, ρ₂/ρ₁ stays below "
                f"{format_engineering(density, 4)} and M₂ above "
                f"{format_engineering(mach, 4)} for γ = {self._gamma:g}."
            ),
        }
        self._limits_memo = (self._gamma, value)
        return value

    @Property("QVariantMap", notify=inputsChanged)
    def strongShockLimits(self):
        """The two ceilings a strong shock approaches but never reaches."""
        return dict(self._strong_shock_limits())

    @Property("QVariantList", constant=True)
    def assumptions(self):
        from ...physics.compressible import equations

        return list(equations.record("normal_shock.jump.v1").assumptions)

    @Property(str, constant=True)
    def modelName(self) -> str:
        return "Calorically perfect gas"

    @Slot(float)
    def setMachAndSolve(self, mach: float) -> None:
        self._mode = SolveMode.MACH_UPSTREAM.value
        self._input = float(mach)
        self.inputsChanged.emit()
        self._recalculate()

    # ==================================================================
    # table
    # ==================================================================

    @Property(QObject, constant=True)
    def tableModel(self):
        return self._table_model

    def _get_table_gamma(self) -> float:
        return self._table_gamma

    def _set_table_gamma(self, value: float) -> None:
        if self._set_table_setting("_table_gamma", float(value)):
            self.tableSettingsChanged.emit()

    tableGamma = Property(float, _get_table_gamma, _set_table_gamma,
                          notify=tableSettingsChanged)

    def _get_table_start(self) -> float:
        return self._table_start

    def _set_table_start(self, value: float) -> None:
        if self._set_table_setting("_table_start", float(value)):
            self.tableSettingsChanged.emit()

    tableStart = Property(float, _get_table_start, _set_table_start,
                          notify=tableSettingsChanged)

    def _get_table_end(self) -> float:
        return self._table_end

    def _set_table_end(self, value: float) -> None:
        if self._set_table_setting("_table_end", float(value)):
            self.tableSettingsChanged.emit()

    tableEnd = Property(float, _get_table_end, _set_table_end,
                        notify=tableSettingsChanged)

    def _get_table_step(self) -> float:
        return self._table_step

    def _set_table_step(self, value: float) -> None:
        if self._set_table_setting("_table_step", float(value)):
            self.tableSettingsChanged.emit()

    tableStep = Property(float, _get_table_step, _set_table_step,
                         notify=tableSettingsChanged)

    def _get_table_convention(self) -> str:
        return self._table_convention

    def _set_table_convention(self, value: str) -> None:
        if self._set_table_setting("_table_convention", str(value)):
            self.tableSettingsChanged.emit()

    tableConvention = Property(str, _get_table_convention, _set_table_convention,
                               notify=tableSettingsChanged)

    def _get_table_precision(self) -> int:
        return self._table_precision

    def _set_table_precision(self, value: int) -> None:
        if self._set_table_precision_value(value):
            self.tableSettingsChanged.emit()

    tablePrecision = Property(int, _get_table_precision, _set_table_precision,
                              notify=tableSettingsChanged)

    def _build_table(self):
        return generate_table(self._table_gamma, self._table_start, self._table_end,
                              self._table_step, self._table_convention)

    def _marker_text(self) -> str:
        return "M₁ = 1"

    def _on_table_built(self, data) -> None:
        self._generated = {"gamma": float(self._table_gamma), "start": float(self._table_start),
                           "end": float(self._table_end), "step": float(self._table_step),
                           "convention": str(self._table_convention)}
        self._refresh_summary()
        self._table_identity += 1
        self._drop_table_selection()

    def _on_table_cleared(self) -> None:
        self._summary = {}
        self._row_comparisons = {}
        self._generated = {}
        self._table_identity += 1
        self._drop_table_selection()

    @Slot()
    def regenerateTable(self) -> None:
        self._regenerate_table()

    @Property(int, notify=tableChanged)
    def tableRowCount(self) -> int:
        return self._table_model.rowCount()

    @Property(str, notify=tableChanged)
    def tableMessage(self) -> str:
        return self._table_message

    @Property(int, notify=tableChanged)
    def sonicRow(self) -> int:
        return self._marker_row

    @Property(int, constant=True)
    def maxTableRows(self) -> int:
        return MAX_TABLE_ROWS

    @Property("QVariantList", notify=tableChanged)
    def tableColumns(self):
        return self._column_labels()

    @Property(str, notify=tableChanged)
    def tableFooter(self) -> str:
        return self._table_caption()

    @Property("QVariantMap", notify=tableChanged)
    def tableGenerated(self):
        """The settings the table on screen was generated with; empty when none.

        The settings fields may be edited ahead of the next Generate; anything
        that names the table on screen (a drawer summary, a chart caption, a
        pinned block) names it from here.
        """
        return dict(self._generated)

    @Property(str, notify=tableChanged)
    def generatedCaption(self) -> str:
        """The line under the table, from the settings it was generated with.

        :attr:`tableFooter` reads the settings fields, which may have been
        edited since; a view opened again after such an edit must still name
        the table it shows.
        """
        rows = self._table_model.rowCount()
        if not rows or not self._generated:
            return ""
        return (f"{rows:,} rows · γ = {self._generated['gamma']:g} · calorically perfect gas · "
                "calculated by RocketForge")

    @Property(float, notify=tableChanged)
    def plottedGamma(self) -> float:
        """The gamma of the generated table, NaN when there is none."""
        return float(self._generated.get("gamma", math.nan))

    def _settings_now(self) -> dict:
        return {"gamma": float(self._table_gamma), "start": float(self._table_start),
                "end": float(self._table_end), "step": float(self._table_step),
                "convention": str(self._table_convention)}

    @Property(bool, notify=tableStaleChanged)
    def tableStale(self) -> bool:
        """A setting was edited since the table on screen was generated."""
        return bool(self._generated) and self._settings_now() != self._generated

    @Property("QVariantMap", notify=tableChanged)
    def chartData(self):
        """Quantity key -> :meth:`chartSeries` for every plotted column.

        A property, so a chart bound to it follows a regenerated table. Read
        from the generated block; nothing is solved.
        """
        keys = [c["key"] for c in self._table_model.columns[1:]]
        return {key: self._chart_series(key) for key in keys}

    # ------------------------------------------------------------------
    # selection, shared by the table, the chart and the inspector
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
        """The generated row whose M₁ is exactly ``mach``, else -1."""
        row = self._table_model.rowNearest(mach)
        if row < 0 or self._table_model.machAt(row) != mach:
            return -1
        return row

    def _cell_text(self, row: int, column: int) -> str:
        value = self._table_model.data(self._table_model.index(row, column))
        return "" if value is None else str(value)

    @Slot(int)
    def selectTableRow(self, row: int) -> None:
        """Select a generated row: the chart and the inspector follow it."""
        if not 0 <= row < self._table_model.rowCount():
            return
        mach = self._table_model.machAt(row)
        self._selection.select("tableRow", str(row), mach, f"row {row + 1}", "table")

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
        label = f"M₁ {self._cell_text(a, 0)}–{self._cell_text(b, 0)}"
        self._selection.selectRange("tableRange", f"rows:{a}-{b}", self._table_model.machAt(a),
                                    self._table_model.machAt(b), label, "table")

    @Slot(float, result=int)
    def rowExactly(self, mach: float) -> int:
        """The row generated at exactly ``mach``, else -1 (no nearest-row guess)."""
        return self._row_at(mach)

    @Slot(int, int, result="QVariantMap")
    def tableSnapshot(self, first: int, last: int):
        """Rows ``first``..``last`` as a table snapshot, exactly as shown."""
        model = self._table_model
        if not self._generated:
            return {}
        gamma = self._generated["gamma"]
        try:
            return table_block(source="normal_shock.table", identity=self._table_identity,
                               columns=model.columns, values=model.values,
                               text_at=self._cell_text, first=first, last=last,
                               key_symbol="M₁", stale=self.tableStale, gamma=gamma,
                               convention=self._generated["convention"],
                               precision=self._table_precision,
                               provenance=f"Generated by RocketForge at γ = {gamma:g}")
        except (ValueError, IndexError):
            return {}

    @Slot("QVariantMap", result="QVariantList")
    def restorableRange(self, snapshot):
        """The rows of the table on screen a pinned block names, else [].

        The block's own rows when it was pinned from this very table; else the
        rows generated at exactly its keys -- but only when the table on screen
        was generated with the same gamma and columns. Never a nearest row.
        """
        try:
            keys = [float(k) for k in snapshot.get("rowKeys", [])]
            if not keys or not self._generated:
                return []
            if int(snapshot.get("identity", -1)) == self._table_identity:
                a, b = int(snapshot["firstRow"]), int(snapshot["lastRow"])
            else:
                if (float(snapshot.get("gamma", math.nan)) != self._generated["gamma"]
                        or snapshot.get("convention") != self._generated["convention"]):
                    return []
                a, b = self._row_at(keys[0]), self._row_at(keys[-1])
        except (TypeError, ValueError, KeyError):
            return []
        if a < 0 or b < 0 or b - a + 1 != len(keys):
            return []
        return [a, b]

    @Slot(int, int)
    def copyTableRows(self, first: int, last: int) -> None:
        span = clamp_block(first, last, self._table_model.rowCount())
        if span is None:
            return
        header = [c["label"] for c in self._table_model.columns]
        self._copy_text(block_text(header, self._cell_text, span[0], span[1], len(header)))

    @Property("QVariantMap", notify=selectionReadoutChanged)
    def selectionReadout(self):
        """The inspector's reading of the selection -- the generated row, as shown.

        A point on the relation and a table row are the same thing, a sample
        of the generated table; both read back that row's own formatted
        values, upstream M₁ and every jump across the shock together. The
        solved state reads the calculator's rows. Nothing is recomputed.
        """
        selection = self._selection
        model = self._table_model
        fidelity = "Calculated by RocketForge · calorically perfect gas"
        base = {"stale": self.tableStale}
        gamma = self._generated.get("gamma", math.nan)
        if selection.kind in ("plotPoint", "tableRow"):
            row = self._row_at(selection.x)
            if row < 0:
                return {}
            rows = [{"label": spec["label"], "value": self._cell_text(row, column),
                     "unit": spec.get("unit", "")}
                    for column, spec in enumerate(model.columns)]
            note = f"A generated sample at γ = {gamma:g}; the curve is drawn through these samples."
            if row == self._marker_row:
                note += " M₁ = 1 is the vanishing shock: every ratio is 1."
            return dict(base, kind=selection.kind, key=str(row), title=f"Table row {row + 1}",
                        note=note, rows=rows, identity=self._table_identity, fidelity=fidelity)
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
                        note=(f"{b - a + 1} generated samples at γ = {gamma:g}; "
                              "first and last row of the range, as shown in the table."),
                        rows=rows, identity=self._table_identity, fidelity=fidelity)
        if selection.kind == "state":
            rows = [{"label": r["label"], "value": r["value"], "unit": r.get("unit", "")}
                    for r in self._result_rows()]
            if not rows:
                return {}
            return {"kind": "state", "key": "state", "title": "Solved shock",
                    "note": self._status_label(), "rows": rows, "identity": self._identity,
                    "fidelity": fidelity, "stale": False}
        return {}

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
        self._copy_text(text)

    @Slot(int)
    def copyRow(self, row: int) -> None:
        self._copy_row(row)

    @Slot()
    def copyTable(self) -> None:
        self._copy_text(self._table_model.tableAsText())

    @Slot(str, result=str)
    def exportCsv(self, directory: str) -> str:
        return self._export_csv(directory)

    @Slot(str, result="QVariantList")
    def chartSeries(self, quantity: str):
        return self._chart_series(quantity)

    # ==================================================================
    # reference comparison against Appendix B
    # ==================================================================

    def _reference_table(self):
        return reference.load_normal_shock_reference()

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

        A γ = 1.2 calculation has nothing to check against a γ = 1.4 appendix,
        so the comparison is switched off rather than shown as failing.
        """
        try:
            return abs(self._table_gamma - self._reference_table().gamma) < 1e-12
        except OSError:
            return False

    @Property(float, constant=True)
    def referenceGamma(self) -> float:
        try:
            return self._reference_table().gamma
        except OSError:
            return float("nan")

    @Property(str, constant=True)
    def referenceCitation(self) -> str:
        try:
            return self._reference_table().citation
        except OSError:
            return ""

    @Property(str, notify=tableChanged)
    def referenceMessage(self) -> str:
        if self.referenceAvailable:
            return ""
        return (f"Appendix B is published for γ = {self.referenceGamma:g}. "
                f"Comparison is unavailable at γ = {self._table_gamma:g}.")

    def _refresh_summary(self) -> None:
        self._row_comparisons = {}
        if not (self._compare and self.referenceAvailable):
            self._summary = {}
            return
        self._row_comparisons = {row: self._compare_row(row)
                                 for row in range(self._table_model.rowCount())}
        machs = [self._table_model.machAt(r) for r in range(self._table_model.rowCount())]
        summary = reference.compare_table(self._table_gamma, machs, self._reference_table())
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
            "reviewMachs": [row.mach for row in summary.reviews],
        }

    @Property("QVariantMap", notify=referenceChanged)
    def comparisonSummary(self):
        return self._summary

    @Slot(int, result="QVariantList")
    def comparisonForRow(self, row: int):
        """Per-quantity comparison for one generated row.

        Read from the comparison made with the table while Compare is on;
        computed only when asked outside it (a script, a test).

        Empty when that Mach number is not tabulated in the source: no
        interpolated reference values, ever.
        """
        if not self.referenceAvailable:
            return []
        if row in self._row_comparisons:
            return self._row_comparisons[row]
        return self._compare_row(row)

    def _compare_row(self, row: int) -> list:
        mach = self._table_model.machAt(row)
        comparison = reference.compare_row(mach, self._table_gamma, self._reference_table())
        if comparison is None:
            return []
        return self._comparison_rows(comparison)

    @Slot(int, result=bool)
    def hasReferenceRow(self, row: int) -> bool:
        if not self.referenceAvailable:
            return False
        mach = self._table_model.machAt(row)
        return reference.compare_row(mach, self._table_gamma,
                                     self._reference_table()) is not None

    @Property("QVariantList", notify=resultsChanged)
    def currentMachComparison(self):
        """:meth:`comparisonForCurrentMach` for the current result, held."""
        return self._current_comparison

    @Slot(result="QVariantList")
    def comparisonForCurrentMach(self):
        """Compare the calculator's current M₁ against the published table."""
        if self._result is None or self._result.mach is None:
            return []
        if abs(self._gamma - self.referenceGamma) > 1e-12:
            return []
        comparison = reference.compare_row(self._result.mach, self._gamma,
                                           self._reference_table())
        if comparison is None:
            return []
        return self._comparison_rows(comparison)

    @Slot(str, result="QVariantList")
    def referenceSeries(self, quantity: str):
        """Published Appendix B values for one quantity, as discrete points.

        Returned only inside the generated table's own Mach range, and only at
        Mach numbers the appendix actually prints. The chart draws them as dots
        and never joins them: a published table is a set of printed values, not
        a continuous function, and a line through them would imply a curve
        nobody published.
        """
        if not self.referenceAvailable:
            return []
        table = self._reference_table()
        if quantity not in table.quantities:
            return []
        low, high = self._table_start, self._table_end
        return [
            {"x": float(row[table.mach_key]), "y": float(row[quantity])}
            for row in table.rows
            if low - 1e-12 <= float(row[table.mach_key]) <= high + 1e-12
        ]

    @staticmethod
    def _comparison_rows(comparison):
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

    @Property(str, constant=True)
    def referenceNote(self) -> str:
        """Why two of the 1008 published values are reported as REVIEW.

        Said on the page rather than buried in a test, because a user who
        compares the whole appendix will see the two and deserves to know they
        were investigated rather than tolerated.
        """
        return (
            "Two of the 1008 printed values — p₀₂/p₀₁ at M₁ = 5.9 and 6.9 — differ "
            "from RocketForge in the last printed digit. Both were checked against "
            "the rendered page and against an independent 40-digit evaluation: the "
            "exact values sit a fraction of a rounding unit below the boundary where "
            "that digit rounds up, so the source rounded one way and round-to-nearest "
            "goes the other. Neither the equations nor the tolerance are adjusted."
        )
