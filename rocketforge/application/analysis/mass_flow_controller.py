"""The QObject the Mass Flow page binds to.

Thin by design. It validates what the interface sent, calls
:mod:`mass_flow_service`, and republishes the answer as properties QML can bind
to. No relation, no ratio algebra and no tolerance policy lives here -- each of
those is one or two layers down, where it is tested without Qt.

The behaviour is shared with the other analysis pages through
:class:`AnalysisBehaviour`; the Qt surface is declared here rather than
inherited, for the reason that module's docstring sets out.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from ...physics.compressible import FlowBranch
from ..formatting import format_engineering
from .analysis_behaviour import MAX_TABLE_ROWS, AnalysisBehaviour
from .mass_flow_service import (
    SOLVE_MODES,
    FlowState,
    SolveMode,
    TableConvention,
    choking_report,
    generate_table,
    mode_info,
    solve,
)

__all__ = ["MassFlowController"]


class MassFlowController(AnalysisBehaviour, QObject):
    """Application-side facade for the Mass Flow analysis page."""

    resultsChanged = Signal()
    inputsChanged = Signal()
    stateChanged = Signal()
    tableChanged = Signal()
    tableSettingsChanged = Signal()
    referenceChanged = Signal()
    requestTab = Signal(int)

    _export_name = "mass_flow"

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._init_analysis()

        # calculator state
        self._mode = SolveMode.MACH.value
        self._input = 0.5
        self._gamma = 1.4
        self._branch = FlowBranch.SUBSONIC.value

        # the dimensional context
        self._area = 0.01
        self._stagnation_pressure = 1.0e6
        self._stagnation_temperature = 300.0
        self._gas_constant = 287.0528

        # choking check, which is its own question and not part of the readout
        self._receiver_ratio = 0.4

        # table state
        self._table_start = 0.0
        self._table_end = 5.0
        self._table_step = 0.02
        self._table_convention = TableConvention.DIMENSIONLESS.value
        self._include_sonic = True

        self._recalculate()
        self.regenerateTable()

    # ==================================================================
    # calculator inputs
    # ==================================================================

    @Property("QVariantList", constant=True)
    def solveModes(self):
        """The menu of things the user may solve from."""
        return [
            {"key": info.mode.value, "label": info.label, "symbol": info.symbol,
             "unit": info.unit, "hint": info.hint, "needsBranch": info.needs_branch,
             "needsDimensions": info.needs_dimensions,
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

    def _get_branch(self) -> str:
        return self._branch

    def _set_branch(self, value: str) -> None:
        if value == self._branch:
            return
        self._branch = value
        self.inputsChanged.emit()
        self._recalculate()

    branch = Property(str, _get_branch, _set_branch, notify=inputsChanged)

    @Property(bool, notify=inputsChanged)
    def branchRequired(self) -> bool:
        """Whether the current mode needs a branch. Drives the control's visibility."""
        return mode_info(self._mode).needs_branch

    @Property(str, notify=inputsChanged)
    def inputSymbol(self) -> str:
        return mode_info(self._mode).symbol

    @Property(str, notify=inputsChanged)
    def inputUnit(self) -> str:
        return mode_info(self._mode).unit

    @Property(str, notify=inputsChanged)
    def inputHint(self) -> str:
        return mode_info(self._mode).hint

    # ------------------------------------------------------------------
    # the dimensional context
    # ------------------------------------------------------------------

    def _state(self) -> FlowState:
        return FlowState(
            area=self._area,
            stagnation_pressure=self._stagnation_pressure,
            stagnation_temperature=self._stagnation_temperature,
            gas_constant=self._gas_constant,
        )

    def _get_area(self) -> float:
        return self._area

    def _set_area(self, value: float) -> None:
        if float(value) == self._area:
            return
        self._area = float(value)
        self.stateChanged.emit()
        self._recalculate()

    area = Property(float, _get_area, _set_area, notify=stateChanged)

    def _get_p0(self) -> float:
        return self._stagnation_pressure

    def _set_p0(self, value: float) -> None:
        if float(value) == self._stagnation_pressure:
            return
        self._stagnation_pressure = float(value)
        self.stateChanged.emit()
        self._recalculate()

    stagnationPressure = Property(float, _get_p0, _set_p0, notify=stateChanged)

    def _get_t0(self) -> float:
        return self._stagnation_temperature

    def _set_t0(self, value: float) -> None:
        if float(value) == self._stagnation_temperature:
            return
        self._stagnation_temperature = float(value)
        self.stateChanged.emit()
        self._recalculate()

    stagnationTemperature = Property(float, _get_t0, _set_t0, notify=stateChanged)

    def _get_r(self) -> float:
        return self._gas_constant

    def _set_r(self, value: float) -> None:
        if float(value) == self._gas_constant:
            return
        self._gas_constant = float(value)
        self.stateChanged.emit()
        self._recalculate()

    gasConstant = Property(float, _get_r, _set_r, notify=stateChanged)

    @Property(bool, notify=stateChanged)
    def dimensionalAvailable(self) -> bool:
        """Whether a mass flow in kg/s can be produced at all.

        Bound by the page so the dimensional readouts are shown as unavailable
        rather than as zero when the state is incomplete.
        """
        return self._state().complete

    @Property(str, notify=stateChanged)
    def dimensionalMessage(self) -> str:
        if self._state().complete:
            return ""
        return ("Enter a positive area, stagnation pressure, stagnation temperature "
                "and gas constant to obtain a mass flow in kg/s. The dimensionless "
                "results above do not need them.")

    # ------------------------------------------------------------------
    # choking check
    # ------------------------------------------------------------------

    def _get_receiver_ratio(self) -> float:
        return self._receiver_ratio

    def _set_receiver_ratio(self, value: float) -> None:
        if float(value) == self._receiver_ratio:
            return
        self._receiver_ratio = float(value)
        self.inputsChanged.emit()

    receiverPressureRatio = Property(float, _get_receiver_ratio, _set_receiver_ratio,
                                     notify=inputsChanged)

    @Property("QVariantMap", notify=inputsChanged)
    def chokingCheck(self):
        """Whether a convergent passage would choke at the entered ratio.

        Scoped exactly as the physics is scoped: a convergent passage
        discharging to a receiver, and not a nozzle regime classifier.
        """
        try:
            choked, message = choking_report(self._receiver_ratio, self._gamma)
        except (ArithmeticError, ValueError, TypeError) as error:
            return {"valid": False, "choked": False, "message": str(error),
                    "tone": "warning", "label": "Invalid"}
        return {
            "valid": True,
            "choked": choked,
            "message": message,
            "tone": "accent" if choked else "success",
            "label": "Choked" if choked else "Not choked",
        }

    # ==================================================================
    # results
    # ==================================================================

    def _compute(self):
        return solve(self._mode, self._input, self._gamma, self._state(), self._branch)

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
        """Results shown are from an earlier, valid input."""
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

    @Property("QVariantList", notify=resultsChanged)
    def bothBranches(self):
        """Subsonic and supersonic roots, when the user asked for both."""
        if self._result is None or self._result.both is None:
            return []
        subsonic, supersonic = self._result.both
        return [
            {"label": "Subsonic M", "value": format_engineering(subsonic, self._precision)},
            {"label": "Supersonic M", "value": format_engineering(supersonic, self._precision)},
        ]

    @Property("QVariantList", constant=True)
    def assumptions(self):
        """The model's standing assumptions, from the physics registry."""
        from ...physics.compressible import equations

        return list(equations.record("mass_flow.parameter.v1").assumptions)

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

    def _get_include_sonic(self) -> bool:
        return self._include_sonic

    def _set_include_sonic(self, value: bool) -> None:
        if self._set_table_setting("_include_sonic", bool(value)):
            self.tableSettingsChanged.emit()

    includeSonic = Property(bool, _get_include_sonic, _set_include_sonic,
                            notify=tableSettingsChanged)

    def _build_table(self):
        return generate_table(
            self._table_gamma, self._table_start, self._table_end, self._table_step,
            self._table_convention, self._state(), self._include_sonic,
        )

    def _marker_text(self) -> str:
        return "CHOKED"

    def _table_caption(self) -> str:
        rows = self._table_model.rowCount()
        if not rows:
            return ""
        base = (f"{rows:,} rows · γ = {self._table_gamma:g} · calorically perfect gas · "
                "calculated by RocketForge")
        if self._table_convention == TableConvention.DIMENSIONAL.value:
            base += (f" · A = {self._area:g} m² · p₀ = {self._stagnation_pressure:g} Pa · "
                     f"T₀ = {self._stagnation_temperature:g} K · "
                     f"R = {self._gas_constant:g} J/(kg·K)")
        return base

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
    # reference
    # ==================================================================

    @Property(bool, constant=True)
    def referenceAvailable(self) -> bool:
        """Anderson publishes no mass-flow appendix, and none is invented.

        Stated as a property rather than left as a silent absence, so the page
        can say why the comparison panel the other modules have is missing
        here. The mass-flow results are validated instead by the identity
        MFP/Γ = A*/A against the isentropic area ratio, which *is* tabulated,
        and by dimensional checks in the test suite.
        """
        return False

    @Property(str, constant=True)
    def referenceMessage(self) -> str:
        return (
            "Anderson's Fundamentals of Aerodynamics publishes no mass-flow "
            "appendix, so there is no printed table to compare against here. "
            "The mass-flow relations are verified instead against the identity "
            "ṁ/ṁ* = A*/A, whose area ratio is checked value-by-value against "
            "Appendix A on the Isentropic page."
        )
