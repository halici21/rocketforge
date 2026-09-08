"""The QObject the Fanno page binds to.

Thin by design: validate, call :mod:`fanno_service`, republish. No relation and
no friction-factor conversion lives here -- the conversion is the service's, one
layer down, where it is tested without Qt.

The Qt surface is declared in full rather than inherited, for the reason set
out in :mod:`analysis_behaviour`: PySide6 builds a corrupt metaobject when a
subclass property notifies with a base-class signal.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..formatting import format_engineering
from .reference_validation import fanno_validation
from .analysis_behaviour import MAX_TABLE_ROWS, AnalysisBehaviour
from .fanno_service import (
    FRICTION_CONVENTIONS,
    SOLVE_MODES,
    FrictionConvention,
    SolveMode,
    TableBranch,
    convert_friction_factor,
    duct_parameter_from_geometry,
    duct_segment,
    friction_limit,
    generate_table,
    mode_info,
    solve,
)

__all__ = ["FannoController"]


class FannoController(AnalysisBehaviour, QObject):
    """Application-side facade for the Fanno analysis page."""

    resultsChanged = Signal()
    inputsChanged = Signal()
    ductChanged = Signal()
    tableChanged = Signal()
    tableSettingsChanged = Signal()
    referenceChanged = Signal()
    requestTab = Signal(int)

    _export_name = "fanno"

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._init_analysis()

        # state calculator
        self._mode = SolveMode.MACH.value
        self._input = 0.5
        self._gamma = 1.4
        self._branch = "subsonic"

        # duct segment, a separate workflow rather than a mode: it has its own
        # inlet Mach number and its own duct, and folding the two forms into
        # one would make the reader guess which is being solved.
        self._segment_enabled = False
        self._segment_mach = 0.3
        self._duct_source = "parameter"          # parameter | geometry
        self._duct_parameter = 1.0
        self._convention = FrictionConvention.FANNING.value
        self._friction_factor = 0.005
        self._length = 3.0
        self._diameter = 0.1
        self._segment = None

        # table
        self._table_start = 0.10
        self._table_end = 4.00
        self._table_step = 0.05
        self._table_branch = TableBranch.BOTH.value

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
        # Move to the new quantity's own default rather than reinterpreting the
        # old number as something it is not: 0.5 is a sensible Mach number and a
        # different duct entirely as a friction parameter.
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

    @Property(float, notify=inputsChanged)
    def supersonicLimit(self) -> float:
        """The finite ceiling on 4f_F L*/D, for a caption and a guide line."""
        try:
            return friction_limit(self._gamma)
        except Exception:                                  # pragma: no cover
            return float("nan")

    # ==================================================================
    # the duct segment
    # ==================================================================

    @Property("QVariantList", constant=True)
    def frictionConventions(self):
        return [{"convention": i.convention.value, "label": i.label,
                 "symbol": i.symbol, "hint": i.hint, "relation": i.relation,
                 "default": i.default_value}
                for i in FRICTION_CONVENTIONS]

    def _get_segment_enabled(self) -> bool:
        return self._segment_enabled

    def _set_segment_enabled(self, value: bool) -> None:
        value = bool(value)
        if value == self._segment_enabled:
            return
        self._segment_enabled = value
        # Drop the previous outcome rather than leaving it on screen under a
        # workflow that is no longer running.
        self._segment = None
        self.ductChanged.emit()
        self._recalculate()

    segmentEnabled = Property(bool, _get_segment_enabled, _set_segment_enabled,
                              notify=ductChanged)

    def _get_segment_mach(self) -> float:
        return self._segment_mach

    def _set_segment_mach(self, value: float) -> None:
        value = float(value)
        if value == self._segment_mach:
            return
        self._segment_mach = value
        self.ductChanged.emit()
        self._recalculate()

    segmentMach = Property(float, _get_segment_mach, _set_segment_mach,
                           notify=ductChanged)

    def _get_duct_source(self) -> str:
        return self._duct_source

    def _set_duct_source(self, value: str) -> None:
        value = str(value)
        if value == self._duct_source:
            return
        self._duct_source = value
        self.ductChanged.emit()
        self._recalculate()

    ductSource = Property(str, _get_duct_source, _set_duct_source, notify=ductChanged)

    def _get_duct_parameter(self) -> float:
        return self._duct_parameter

    def _set_duct_parameter(self, value: float) -> None:
        value = float(value)
        if value == self._duct_parameter:
            return
        self._duct_parameter = value
        self.ductChanged.emit()
        self._recalculate()

    ductParameter = Property(float, _get_duct_parameter, _set_duct_parameter,
                             notify=ductChanged)

    def _get_convention(self) -> str:
        return self._convention

    def _set_convention(self, value: str) -> None:
        """Switch convention and convert the number, so the duct does not move.

        Policy A of ``07`` section 6: the displayed friction factor changes by
        the factor of four and the physical wall stays where it was. Keeping
        the number and quietly changing the duct instead would be precisely the
        ambiguity the convention rules exist to remove.
        """
        value = str(value)
        if value == self._convention:
            return
        self._friction_factor = convert_friction_factor(
            self._friction_factor, self._convention, value)
        self._convention = value
        self.ductChanged.emit()
        self._recalculate()

    frictionConvention = Property(str, _get_convention, _set_convention,
                                  notify=ductChanged)

    @Property(str, notify=ductChanged)
    def frictionSymbol(self) -> str:
        from .fanno_service import convention_info

        return convention_info(self._convention).symbol

    @Property(str, notify=ductChanged)
    def frictionLabel(self) -> str:
        from .fanno_service import convention_info

        info = convention_info(self._convention)
        return f"{info.label} friction factor  {info.symbol}"

    @Property(str, constant=True)
    def frictionRelation(self) -> str:
        return "f_D = 4 f_F"

    def _get_friction_factor(self) -> float:
        return self._friction_factor

    def _set_friction_factor(self, value: float) -> None:
        value = float(value)
        if value == self._friction_factor:
            return
        self._friction_factor = value
        self.ductChanged.emit()
        self._recalculate()

    frictionFactor = Property(float, _get_friction_factor, _set_friction_factor,
                              notify=ductChanged)

    def _get_length(self) -> float:
        return self._length

    def _set_length(self, value: float) -> None:
        value = float(value)
        if value == self._length:
            return
        self._length = value
        self.ductChanged.emit()
        self._recalculate()

    ductLength = Property(float, _get_length, _set_length, notify=ductChanged)

    def _get_diameter(self) -> float:
        return self._diameter

    def _set_diameter(self, value: float) -> None:
        value = float(value)
        if value == self._diameter:
            return
        self._diameter = value
        self.ductChanged.emit()
        self._recalculate()

    hydraulicDiameter = Property(float, _get_diameter, _set_diameter, notify=ductChanged)

    @Property(float, notify=ductChanged)
    def effectiveDuctParameter(self) -> float:
        """``4 f_F L/D`` actually handed to the physics, whichever form was used.

        Published so the interface can show the group it is solving, which is
        the number a reader can check against a table.
        """
        try:
            if self._duct_source == "geometry":
                return duct_parameter_from_geometry(
                    self._friction_factor, self._length, self._diameter,
                    self._convention)
            return float(self._duct_parameter)
        except Exception:
            return float("nan")

    @Property("QVariantList", notify=ductChanged)
    def segmentResults(self):
        """The segment readout, including the choked case.

        A choked duct still has rows worth showing -- the requested length, the
        length actually available, and the shortfall between them -- so they are
        published rather than blanked. What is *not* published is an outlet Mach
        number, because there is not one.
        """
        if self._segment is None:
            return []
        return [
            {"key": row.key, "label": row.label, "group": row.group,
             "value": format_engineering(row.value, self._precision),
             "raw": float("nan") if row.value is None else float(row.value),
             "unit": row.unit, "emphasis": row.emphasis,
             "available": row.value is not None}
            for row in self._segment.rows
        ]

    @Property(bool, notify=ductChanged)
    def segmentValid(self) -> bool:
        return bool(self._segment is not None and self._segment.ok)

    @Property(str, notify=ductChanged)
    def segmentStatus(self) -> str:
        return "" if self._segment is None else self._segment.status

    @Property(str, notify=ductChanged)
    def segmentMessage(self) -> str:
        return "" if self._segment is None else self._segment.message

    @Property(str, notify=ductChanged)
    def segmentTone(self) -> str:
        if self._segment is None:
            return "neutral"
        if not self._segment.ok:
            return "warning"
        if self._segment.status in ("Choked at outlet", "Near sonic"):
            return "accent"
        return "success"

    @Property(bool, notify=ductChanged)
    def segmentChoked(self) -> bool:
        """True when the duct is longer than the flow can sustain.

        Distinct from a malformed input: there is no outlet to report, and the
        interface should say the flow chokes rather than show a Mach number.
        """
        return bool(self._segment is not None and not self._segment.ok
                    and self._segment.status == "Choked")

    # ==================================================================
    # results
    # ==================================================================

    def _compute(self):
        return solve(self._mode, self._input, self._gamma, self._branch)

    def _recalculate(self) -> None:
        if self._segment_enabled:
            self._segment = duct_segment(self._segment_mach,
                                         self.effectiveDuctParameter, self._gamma)
        else:
            self._segment = None
        AnalysisBehaviour._recalculate(self)
        self.ductChanged.emit()

    def _get_precision(self) -> int:
        return self._precision

    def _set_precision(self, value: int) -> None:
        if self._set_precision_value(value):
            self.resultsChanged.emit()
            self.ductChanged.emit()

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

        return list(equations.record("fanno.friction_parameter.v1").assumptions)

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

    def _marker_text(self) -> str:
        return "SONIC · CHOKING LIMIT"

    def _table_caption(self) -> str:
        rows = self._table_model.rowCount()
        if not rows:
            return ""
        return (f"{rows:,} rows · γ = {self._table_gamma:g} · friction parameter is "
                f"4 f_F L*/D, Fanning · calculated by RocketForge")

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

    @Slot(str, result="QVariantList")
    def branchSeries(self, quantity: str):
        """The same data as two series, split at the sonic point.

        ``03`` section 8.7 requires this rather than one array containing
        M = 1: ``p/p*`` and ``4fL*/D`` have very different scales on the two
        sides, and a single series invites an autoscale that hides one branch
        inside the other. Each half is closed at the sonic point so the two
        curves meet there rather than leaving a visual gap.
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

    # ==================================================================
    # reference validation
    #
    # Not a row-by-row published comparison, because there is no published
    # Fanno appendix in the supplied volume. The panel says so and names
    # what does back the numbers instead.
    # ==================================================================

    @Property(bool, constant=True)
    def referenceAvailable(self) -> bool:
        """No published Fanno table exists here, and none is invented."""
        return False

    @Property(str, constant=True)
    def referenceMessage(self) -> str:
        return fanno_validation().message

    @Property(str, constant=True)
    def validationStatus(self) -> str:
        return fanno_validation().status

    @Property(str, constant=True)
    def validationCitation(self) -> str:
        return fanno_validation().citation

    @Property("QVariantList", constant=True)
    def validationChecks(self):
        return [{"name": check.name, "status": check.status, "detail": check.detail}
                for check in fanno_validation().checks]
