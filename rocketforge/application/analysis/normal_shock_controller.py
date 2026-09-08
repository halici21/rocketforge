"""The QObject the Normal Shock page binds to.

Thin by design: validate, call :mod:`normal_shock_service`, republish. The one
thing it adds beyond the shared behaviour is the Appendix B comparison, which
follows the same rule as everywhere else in RocketForge -- the published table
is compared against, never read for an answer.

The behaviour is shared with the other analysis pages through
:class:`AnalysisBehaviour`; the Qt surface is declared here rather than
inherited, for the reason that module's docstring sets out.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..formatting import format_engineering
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

    @Property("QVariantMap", notify=inputsChanged)
    def strongShockLimits(self):
        """The two ceilings a strong shock approaches but never reaches."""
        density, mach = limits_for(self._gamma)
        return {
            "densityRatio": format_engineering(density, 6),
            "machDownstream": format_engineering(mach, 6),
            "caption": (
                f"However strong the shock, ρ₂/ρ₁ stays below "
                f"{format_engineering(density, 4)} and M₂ above "
                f"{format_engineering(mach, 4)} for γ = {self._gamma:g}."
            ),
        }

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
        self._refresh_summary()

    def _on_table_cleared(self) -> None:
        self._summary = {}

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
        """Per-quantity comparison for one generated row.

        Empty when that Mach number is not tabulated in the source: no
        interpolated reference values, ever.
        """
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
