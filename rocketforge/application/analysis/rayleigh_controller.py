"""The QObject the Rayleigh page binds to.

Thin by design: validate, call :mod:`rayleigh_service`, republish. No relation
lives here.

The Qt surface is declared in full rather than inherited, for the reason set
out in :mod:`analysis_behaviour`: PySide6 builds a corrupt metaobject when a
subclass property notifies with a base-class signal.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..formatting import format_engineering
from .reference_validation import rayleigh_validation
from .analysis_behaviour import MAX_TABLE_ROWS, AnalysisBehaviour
from .rayleigh_service import (
    HEAT_INPUTS,
    SOLVE_MODES,
    HeatInput,
    SolveMode,
    TableBranch,
    critical_points,
    generate_table,
    heat_transition,
    mode_info,
    solve,
)

__all__ = ["RayleighController"]


class RayleighController(AnalysisBehaviour, QObject):
    """Application-side facade for the Rayleigh analysis page."""

    resultsChanged = Signal()
    inputsChanged = Signal()
    heatChanged = Signal()
    tableChanged = Signal()
    tableSettingsChanged = Signal()
    referenceChanged = Signal()
    requestTab = Signal(int)

    _export_name = "rayleigh"

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._init_analysis()

        # state calculator
        self._mode = SolveMode.MACH.value
        self._input = 0.5
        self._gamma = 1.4
        self._branch = "subsonic"

        # heat transition
        self._heat_enabled = False
        self._heat_mach = 0.3
        self._heat_input = HeatInput.RATIO.value
        self._ratio = 1.5
        self._heat = 2.0e5
        self._gas_constant = 287.0528
        self._t01 = 300.0
        self._heat_result = None

        # table
        self._table_start = 0.10
        self._table_end = 4.00
        self._table_step = 0.05
        self._table_branch = TableBranch.BOTH.value

        self._static_temperature_max_row = -1

        self._recalculate()
        self.regenerateTable()

    # ==================================================================
    # calculator inputs
    # ==================================================================

    @Property("QVariantList", constant=True)
    def solveModes(self):
        return [{"mode": i.mode.value, "label": i.label, "symbol": i.symbol,
                 "unit": i.unit, "hint": i.hint, "iterative": i.iterative,
                 "needsBranch": i.needs_branch, "default": i.default_value}
                for i in SOLVE_MODES]

    def _get_mode(self) -> str:
        return self._mode

    def _set_mode(self, value: str) -> None:
        value = str(value)
        if value == self._mode:
            return
        self._mode = value
        self._input = mode_info(value).default_value
        self.inputsChanged.emit()
        self._recalculate()

    mode = Property(str, _get_mode, _set_mode, notify=inputsChanged)

    def _get_input(self) -> float:
        return self._input

    def _set_input(self, value: float) -> None:
        value = float(value)
        if value == self._input:
            return
        self._input = value
        self.inputsChanged.emit()
        self._recalculate()

    inputValue = Property(float, _get_input, _set_input, notify=inputsChanged)

    def _get_gamma(self) -> float:
        return self._gamma

    def _set_gamma(self, value: float) -> None:
        value = float(value)
        if value == self._gamma:
            return
        self._gamma = value
        self.inputsChanged.emit()
        self._recalculate()

    gamma = Property(float, _get_gamma, _set_gamma, notify=inputsChanged)

    def _get_branch(self) -> str:
        return self._branch

    def _set_branch(self, value: str) -> None:
        value = str(value)
        if value == self._branch:
            return
        self._branch = value
        self.inputsChanged.emit()
        self._recalculate()

    branch = Property(str, _get_branch, _set_branch, notify=inputsChanged)

    @Property(str, notify=inputsChanged)
    def inputSymbol(self) -> str:
        return mode_info(self._mode).symbol

    @Property(str, notify=inputsChanged)
    def inputUnit(self) -> str:
        return mode_info(self._mode).unit

    @Property(str, notify=inputsChanged)
    def inputHint(self) -> str:
        return mode_info(self._mode).hint

    @Property(bool, notify=inputsChanged)
    def modeIsIterative(self) -> bool:
        return mode_info(self._mode).iterative

    @Property(bool, notify=inputsChanged)
    def modeNeedsBranch(self) -> bool:
        return mode_info(self._mode).needs_branch

    # ---- the two critical points, kept apart ---------------------------

    @Property(float, notify=inputsChanged)
    def staticTemperatureMaxMach(self) -> float:
        """M = 1/sqrt(gamma). Subsonic, and *not* the choking point."""
        return critical_points(self._gamma).static_temperature_max_mach

    @Property(float, notify=inputsChanged)
    def staticTemperatureMaxValue(self) -> float:
        return critical_points(self._gamma).static_temperature_max_value

    @Property(float, notify=inputsChanged)
    def supersonicT0Floor(self) -> float:
        """(gamma^2-1)/gamma^2: how far a supersonic flow can be cooled."""
        return critical_points(self._gamma).supersonic_t0_floor

    # ==================================================================
    # the heat transition
    # ==================================================================

    @Property("QVariantList", constant=True)
    def heatInputs(self):
        return [{"mode": key, "label": label} for key, label in HEAT_INPUTS]

    def _get_heat_enabled(self) -> bool:
        return self._heat_enabled

    def _set_heat_enabled(self, value: bool) -> None:
        value = bool(value)
        if value == self._heat_enabled:
            return
        self._heat_enabled = value
        self._heat_result = None
        self.heatChanged.emit()
        self._recalculate()

    heatEnabled = Property(bool, _get_heat_enabled, _set_heat_enabled, notify=heatChanged)

    def _get_heat_mach(self) -> float:
        return self._heat_mach

    def _set_heat_mach(self, value: float) -> None:
        value = float(value)
        if value == self._heat_mach:
            return
        self._heat_mach = value
        self.heatChanged.emit()
        self._recalculate()

    heatMach = Property(float, _get_heat_mach, _set_heat_mach, notify=heatChanged)

    def _get_heat_input(self) -> str:
        return self._heat_input

    def _set_heat_input(self, value: str) -> None:
        value = str(value)
        if value == self._heat_input:
            return
        self._heat_input = value
        self.heatChanged.emit()
        self._recalculate()

    heatInput = Property(str, _get_heat_input, _set_heat_input, notify=heatChanged)

    def _get_ratio(self) -> float:
        return self._ratio

    def _set_ratio(self, value: float) -> None:
        value = float(value)
        if value == self._ratio:
            return
        self._ratio = value
        self.heatChanged.emit()
        self._recalculate()

    temperatureRatio = Property(float, _get_ratio, _set_ratio, notify=heatChanged)

    def _get_heat(self) -> float:
        return self._heat

    def _set_heat(self, value: float) -> None:
        value = float(value)
        if value == self._heat:
            return
        self._heat = value
        self.heatChanged.emit()
        self._recalculate()

    heat = Property(float, _get_heat, _set_heat, notify=heatChanged)

    def _get_gas_constant(self) -> float:
        return self._gas_constant

    def _set_gas_constant(self, value: float) -> None:
        value = float(value)
        if value == self._gas_constant:
            return
        self._gas_constant = value
        self.heatChanged.emit()
        self._recalculate()

    gasConstant = Property(float, _get_gas_constant, _set_gas_constant,
                           notify=heatChanged)

    def _get_t01(self) -> float:
        return self._t01

    def _set_t01(self, value: float) -> None:
        value = float(value)
        if value == self._t01:
            return
        self._t01 = value
        self.heatChanged.emit()
        self._recalculate()

    inletStagnationTemperature = Property(float, _get_t01, _set_t01, notify=heatChanged)

    @Property("QVariantList", notify=heatChanged)
    def heatResults(self):
        """The transition readout, including the choked case.

        A choked duct still has rows worth showing -- the requested ratio, the
        maximum the line can take, and the shortfall -- so they are published
        rather than blanked. What is not published is an outlet Mach number,
        because there is not one.
        """
        if self._heat_result is None:
            return []
        return [
            {"key": row.key, "label": row.label, "group": row.group,
             "value": format_engineering(row.value, self._precision),
             "raw": float("nan") if row.value is None else float(row.value),
             "unit": row.unit, "emphasis": row.emphasis,
             "available": row.value is not None}
            for row in self._heat_result.rows
        ]

    @Property(bool, notify=heatChanged)
    def heatValid(self) -> bool:
        return bool(self._heat_result is not None and self._heat_result.ok)

    @Property(str, notify=heatChanged)
    def heatStatus(self) -> str:
        return "" if self._heat_result is None else self._heat_result.status

    @Property(str, notify=heatChanged)
    def heatMessage(self) -> str:
        return "" if self._heat_result is None else self._heat_result.message

    @Property(str, notify=heatChanged)
    def heatTone(self) -> str:
        if self._heat_result is None:
            return "neutral"
        if not self._heat_result.ok:
            return "warning"
        if self._heat_result.status in ("Choked at outlet", "Near sonic"):
            return "accent"
        return "success"

    @Property(bool, notify=heatChanged)
    def heatChoked(self) -> bool:
        return bool(self._heat_result is not None and not self._heat_result.ok
                    and self._heat_result.status == "Choked")

    # ==================================================================
    # results
    # ==================================================================

    def _compute(self):
        return solve(self._mode, self._input, self._gamma, self._branch)

    def _recalculate(self) -> None:
        if self._heat_enabled:
            self._heat_result = heat_transition(
                self._heat_mach, self._gamma,
                heat_input=self._heat_input,
                ratio=self._ratio,
                heat=self._heat,
                gas_constant=self._gas_constant,
                stagnation_temperature_1=self._t01,
            )
        else:
            self._heat_result = None
        AnalysisBehaviour._recalculate(self)
        self.heatChanged.emit()

    def _get_precision(self) -> int:
        return self._precision

    def _set_precision(self, value: int) -> None:
        if self._set_precision_value(value):
            self.resultsChanged.emit()
            self.heatChanged.emit()

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

    @Property(str, notify=resultsChanged)
    def branchUsed(self) -> str:
        return "" if self._result is None else self._result.branch_used

    @Slot(str, result=float)
    def resultValue(self, key: str) -> float:
        return self._raw_result_value(key)

    @Property("QVariantList", constant=True)
    def assumptions(self):
        from ...physics.compressible import equations

        return list(equations.record("rayleigh.stagnation_ratios.v1").assumptions)

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

    def _get_table_branch(self) -> str:
        return self._table_branch

    def _set_table_branch(self, value: str) -> None:
        if self._set_table_setting("_table_branch", str(value)):
            self.tableSettingsChanged.emit()

    tableBranch = Property(str, _get_table_branch, _set_table_branch,
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
                              self._table_step, self._table_branch)

    def _on_table_built(self, data) -> None:
        """Remember where the static-temperature maximum landed.

        The service publishes a marker map; this picks out the second critical
        row so the table can label it as its own thing rather than as a second
        sonic row.
        """
        self._static_temperature_max_row = next(
            (row for row, label in getattr(data, "markers", {}).items()
             if "STATIC" in label), -1)

    def _on_table_cleared(self) -> None:
        self._static_temperature_max_row = -1

    def _marker_text(self) -> str:
        return "SONIC · T₀ MAX"

    def _table_caption(self) -> str:
        rows = self._table_model.rowCount()
        if not rows:
            return ""
        peak = critical_points(self._table_gamma).static_temperature_max_mach
        return (f"{rows:,} rows · γ = {self._table_gamma:g} · static T maximum at "
                f"M = {peak:.4f}, sonic at M = 1 · calculated by RocketForge")

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
    def staticTemperatureMaxRow(self) -> int:
        """The row where the *static* temperature peaks, if it is in range.

        Reported separately from :attr:`sonicRow` and never merged with it: the
        two are different Mach numbers and different physical statements, and a
        table that labelled them the same way would teach the reader the one
        thing about Rayleigh flow that is most commonly got wrong.
        """
        return self._static_temperature_max_row

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

    @Slot(str, result="QVariantList")
    def branchSeries(self, quantity: str):
        """The same data as two series, split at the sonic point.

        ``03`` section 9.6, as for Fanno: one array containing M = 1 invites an
        autoscale that flattens one branch against the other.
        """
        points = self._chart_series(quantity)
        if not points:
            return []
        subsonic = [p for p in points if p["x"] <= 1.0]
        supersonic = [p for p in points if p["x"] >= 1.0]
        series = []
        if len(subsonic) > 1:
            series.append({"points": subsonic, "label": "Subsonic", "dashed": False})
        if len(supersonic) > 1:
            series.append({"points": supersonic, "label": "Supersonic", "dashed": True})
        return series or [{"points": points, "label": "", "dashed": False}]

    @Slot(result="QVariantList")
    def temperatureComparisonSeries(self):
        """``T/T*`` and ``T0/T0*`` on one pair of axes.

        The single most instructive plot on the page: the two curves peak at
        *different* Mach numbers, and seeing them together is what makes the
        band where static temperature falls under heat addition obvious rather
        than surprising. ``03`` section 9.6 asks for exactly this.
        """
        static = self._chart_series("temperature_ratio")
        total = self._chart_series("stagnation_temperature_ratio")
        series = []
        if static:
            series.append({"points": static, "label": "T/T*", "dashed": False})
        if total:
            series.append({"points": total, "label": "T₀/T₀*", "dashed": True})
        return series

    @Slot(result="QVariantList")
    def criticalGuides(self):
        """Dashed verticals at the two critical Mach numbers, labelled apart.

        Naming them identically would be the most misleading thing this page
        could do: one is a static-temperature maximum on the subsonic branch,
        the other is the choking limit.
        """
        peak = critical_points(self._table_gamma).static_temperature_max_mach
        return [
            {"value": float(peak), "axis": "x", "label": "T max"},
            {"value": 1.0, "axis": "x", "label": "Sonic"},
        ]

    # ==================================================================
    # reference validation
    #
    # Not a row-by-row published comparison, because there is no published
    # Rayleigh appendix in the supplied volume. The panel says so and names
    # what does back the numbers instead.
    # ==================================================================

    @Property(bool, constant=True)
    def referenceAvailable(self) -> bool:
        """No published Rayleigh table exists here, and none is invented."""
        return False

    @Property(str, constant=True)
    def referenceMessage(self) -> str:
        return rayleigh_validation().message

    @Property(str, constant=True)
    def validationStatus(self) -> str:
        return rayleigh_validation().status

    @Property(str, constant=True)
    def validationCitation(self) -> str:
        return rayleigh_validation().citation

    @Property("QVariantList", constant=True)
    def validationChecks(self):
        return [{"name": check.name, "status": check.status, "detail": check.detail}
                for check in rayleigh_validation().checks]
