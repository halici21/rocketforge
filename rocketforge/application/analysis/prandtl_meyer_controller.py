"""The QObject the Prandtl-Meyer page binds to.

Thin by design: validate, call :mod:`prandtl_meyer_service`, republish. No
relation, no angle conversion and no tolerance policy lives here -- the
conversion is the service's, one layer down, where it is tested without Qt.

The Qt surface is declared in full rather than inherited, for the reason set
out in :mod:`analysis_behaviour`: PySide6 builds a corrupt metaobject when a
subclass property notifies with a base-class signal.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..formatting import format_engineering
from . import reference_comparison as reference
from .analysis_behaviour import MAX_TABLE_ROWS, AnalysisBehaviour
from .prandtl_meyer_service import (
    SOLVE_MODES,
    SolveMode,
    TableConvention,
    expansion_turn,
    generate_table,
    mode_info,
    nu_max_degrees,
    solve,
)

__all__ = ["PrandtlMeyerController"]


class PrandtlMeyerController(AnalysisBehaviour, QObject):
    """Application-side facade for the Prandtl-Meyer analysis page."""

    resultsChanged = Signal()
    inputsChanged = Signal()
    tableChanged = Signal()
    tableSettingsChanged = Signal()
    referenceChanged = Signal()
    requestTab = Signal(int)

    _export_name = "prandtl_meyer"

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._init_analysis()

        # state calculator
        self._mode = SolveMode.MACH.value
        self._input = 2.0
        self._gamma = 1.4

        # expansion turn, which is a separate workflow rather than a mode:
        # it has its own upstream Mach and its own turn angle, and mixing the
        # two forms into one would make the reader guess which is being solved.
        self._expansion_enabled = False
        self._expansion_mach = 2.0
        self._expansion_turn = 10.0
        self._expansion = None

        # table
        self._table_start = 1.0
        self._table_end = 5.0
        self._table_step = 0.02
        self._table_convention = TableConvention.ANDERSON.value

        # reference
        self._compare = False
        self._summary: dict = {}

        self._recalculate()
        self.regenerateTable()

    # ==================================================================
    # calculator inputs
    # ==================================================================

    @Property("QVariantList", constant=True)
    def solveModes(self):
        return [
            {"key": info.mode.value, "label": info.label, "symbol": info.symbol,
             "unit": info.unit, "hint": info.hint, "iterative": info.iterative,
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
    def inputUnit(self) -> str:
        return mode_info(self._mode).unit

    @Property(str, notify=inputsChanged)
    def inputHint(self) -> str:
        info = mode_info(self._mode)
        if info.mode is SolveMode.NU:
            return f"0 up to ν_max = {nu_max_degrees(self._gamma):.4f}°"
        return info.hint

    @Property(bool, notify=inputsChanged)
    def modeIsIterative(self) -> bool:
        """Whether the current mode is solved by iteration.

        Shown because it is true and useful: the forward relation is closed
        form and only the inverse iterates, and a reader should be able to see
        which produced the number in front of them.
        """
        return mode_info(self._mode).iterative

    @Property(float, notify=inputsChanged)
    def nuMax(self) -> float:
        """The maximum expansion for this gamma, in degrees."""
        return nu_max_degrees(self._gamma)

    # ------------------------------------------------------------------
    # the expansion turn
    # ------------------------------------------------------------------

    def _get_expansion_enabled(self) -> bool:
        return self._expansion_enabled

    def _set_expansion_enabled(self, value: bool) -> None:
        if bool(value) == self._expansion_enabled:
            return
        self._expansion_enabled = bool(value)
        self._recompute_expansion()

    expansionEnabled = Property(bool, _get_expansion_enabled, _set_expansion_enabled,
                                notify=inputsChanged)

    def _get_expansion_mach(self) -> float:
        return self._expansion_mach

    def _set_expansion_mach(self, value: float) -> None:
        if float(value) == self._expansion_mach:
            return
        self._expansion_mach = float(value)
        self._recompute_expansion()

    expansionMach = Property(float, _get_expansion_mach, _set_expansion_mach,
                             notify=inputsChanged)

    def _get_expansion_turn(self) -> float:
        return self._expansion_turn

    def _set_expansion_turn(self, value: float) -> None:
        if float(value) == self._expansion_turn:
            return
        self._expansion_turn = float(value)
        self._recompute_expansion()

    expansionTurn = Property(float, _get_expansion_turn, _set_expansion_turn,
                             notify=inputsChanged)

    def _recompute_expansion(self) -> None:
        self._expansion = (expansion_turn(self._expansion_mach, self._expansion_turn,
                                          self._gamma)
                           if self._expansion_enabled else None)
        self.inputsChanged.emit()
        self.resultsChanged.emit()

    @Property("QVariantList", notify=resultsChanged)
    def expansionResults(self):
        if self._expansion is None or not self._expansion.ok:
            return []
        return [
            {"key": row.key, "label": row.label, "group": row.group,
             "value": format_engineering(row.value, self._precision),
             "raw": float("nan") if row.value is None else float(row.value),
             "unit": row.unit, "emphasis": row.emphasis, "available": row.value is not None}
            for row in self._expansion.rows
        ]

    @Property(bool, notify=resultsChanged)
    def expansionValid(self) -> bool:
        return bool(self._expansion is not None and self._expansion.ok)

    @Property(str, notify=resultsChanged)
    def expansionMessage(self) -> str:
        return "" if self._expansion is None else self._expansion.message

    @Property(str, notify=resultsChanged)
    def expansionStatus(self) -> str:
        return "" if self._expansion is None else self._expansion.status

    # ==================================================================
    # results
    # ==================================================================

    def _compute(self):
        return solve(self._mode, self._input, self._gamma)

    def _recalculate(self) -> None:
        # Keep the expansion in step with gamma, which both workflows share.
        if self._expansion_enabled:
            self._expansion = expansion_turn(self._expansion_mach, self._expansion_turn,
                                             self._gamma)
        AnalysisBehaviour._recalculate(self)

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

    @Property("QVariantList", constant=True)
    def assumptions(self):
        from ...physics.compressible import equations

        return list(equations.record("prandtl_meyer.nu.v1").assumptions)

    @Property(str, constant=True)
    def modelName(self) -> str:
        return "Calorically perfect gas"

    @Slot(float)
    def setMachAndSolve(self, mach: float) -> None:
        self._mode = SolveMode.MACH.value
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

    tableEnd = Property(float, _get_table_end, _set_table_end, notify=tableSettingsChanged)

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
        return "SONIC"

    def _on_table_built(self, data) -> None:
        self._refresh_summary()

    def _on_table_cleared(self) -> None:
        self._summary = {}

    def _table_caption(self) -> str:
        rows = self._table_model.rowCount()
        if not rows:
            return ""
        return (f"{rows:,} rows · γ = {self._table_gamma:g} · angles in degrees · "
                f"ν_max = {nu_max_degrees(self._table_gamma):.4f}° · "
                "calculated by RocketForge")

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
    # reference comparison against Appendix C
    # ==================================================================

    def _reference_table(self):
        return reference.load_prandtl_meyer_reference()

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
        return (f"Appendix C is published for γ = {self.referenceGamma:g}. "
                f"Comparison is unavailable at γ = {self._table_gamma:g}.")

    def _refresh_summary(self) -> None:
        if not (self._compare and self.referenceAvailable):
            self._summary = {}
            return
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
        if not self.referenceAvailable:
            return []
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

    @Slot(result="QVariantList")
    def comparisonForCurrentMach(self):
        """Compare the calculator's current Mach against the published table."""
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
        """Published Appendix C values for one quantity, as discrete points.

        Drawn as dots and never joined: a published table is a set of printed
        values, not a continuous function.
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
