"""The QObject the Nozzle page binds to.

Thin by design: validate, call :mod:`nozzle_service`, republish. No relation,
no threshold and no shock search lives here -- and none in QML either. What
this class adds over the service is the two input modes the interface offers
(absolute pressure or a ratio; two areas or an area ratio), which it converts
once, on the way in, so the layers below only ever see canonical SI.

The Qt surface is declared in full rather than inherited, for the reason set
out in :mod:`analysis_behaviour`: PySide6 builds a corrupt metaobject when a
subclass property notifies with a base-class signal.
"""

from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import Property, QObject, Signal, Slot

from ..formatting import format_engineering
from ..visualization.selection import AnalysisSelection
from ..visualization.viewport import nozzle_viewport
from .analysis_behaviour import MAX_TABLE_ROWS, AnalysisBehaviour
from .nozzle_service import (
    AREA_MODES,
    DEFAULT_RESOLUTION,
    MAX_RESOLUTION,
    PRESSURE_MODES,
    AreaMode,
    NozzleInputs,
    PressureMode,
    back_pressure_sweep,
    distribution_table,
    regime_bands,
    regime_info,
    shock_position_sweep,
    solve,
    solve_record,
    thresholds,
)
from .reference_validation import nozzle_validation

__all__ = ["NozzleController"]


class NozzleController(AnalysisBehaviour, QObject):
    """Application-side facade for the nozzle analysis page."""

    resultsChanged = Signal()
    inputsChanged = Signal()
    tableChanged = Signal()
    tableSettingsChanged = Signal()
    referenceChanged = Signal()
    shockCurveChanged = Signal()
    selectionReadoutChanged = Signal()
    requestTab = Signal(int)

    _export_name = "nozzle"

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._init_analysis()

        self._gamma = 1.4
        self._gas_constant = 287.05
        self._stagnation_pressure = 1.0e6
        self._stagnation_temperature = 3000.0
        self._throat_area = 0.01
        self._area_ratio = 2.0
        self._back_pressure = 7.0e5
        self._resolution = DEFAULT_RESOLUTION

        self._pressure_mode = PressureMode.RATIO.value
        self._area_mode = AreaMode.RATIO.value
        self._normalized = False

        self._record = None
        # What depends on the nozzle and the gas but not on the back pressure:
        # the criticals, the regime bands and the shock-station curve. Solved
        # with the operating point, only when one of those inputs moved, so
        # opening a view reads them instead of solving them.
        self._map_key = None
        self._thresholds: dict = {}
        self._bands: list = []
        self._shock_curve: list = []
        self._presented = None
        # Which solved state the views are showing: every solve gets the next
        # number, so a pinned snapshot or the inspector can say which one it is.
        self._identity = 0
        # One selection for every view of the nozzle -- the drawing's
        # stations, the axial charts and the table -- and the inspector
        # readout of it, read from the solved snapshot, never solved for.
        self._selection = AnalysisSelection(self)
        self._selection.changed.connect(self.selectionReadoutChanged)
        self.resultsChanged.connect(self.selectionReadoutChanged)
        self._recalculate()
        self._regenerate_table()

    # ------------------------------------------------------------------
    # inputs
    # ------------------------------------------------------------------

    def _inputs(self) -> NozzleInputs:
        return NozzleInputs(
            gamma=self._gamma,
            gas_constant=self._gas_constant,
            stagnation_pressure=self._stagnation_pressure,
            stagnation_temperature=self._stagnation_temperature,
            throat_area=self._throat_area,
            area_ratio_exit=self._area_ratio,
            back_pressure=self._back_pressure,
            resolution=self._resolution,
        )

    def _compute(self):
        inputs = self._inputs()
        result = solve(inputs)
        self._record = solve_record(inputs) if result.ok else None
        self._presented = None
        self._identity += 1
        self._solve_map(inputs)
        self._drop_vanished_selection()
        return result

    def _drop_vanished_selection(self) -> None:
        """A selected station the new solution no longer has is deselected.

        The shock is the case: moving to a shock-free back pressure removes
        the station, and a selection pointing at it would point at nothing.
        """
        selection = self._selection
        if selection.kind != "station":
            return
        present = {"throat", "exit"}
        record = self._record
        if record is not None and record.shock is not None and record.shock.x is not None:
            present.add("shock")
        if record is None or selection.key not in present:
            selection.clear()

    def _solve_map(self, inputs: NozzleInputs) -> None:
        key = (inputs.gamma, inputs.gas_constant, inputs.throat_area,
               inputs.area_ratio_exit, inputs.resolution)
        if key == self._map_key:
            return
        self._map_key = key
        self._thresholds = thresholds(inputs)
        self._bands = regime_bands(inputs)
        # The same 80-point sweep shockPositionSeries() draws.
        self._shock_curve = [{"x": p["pressure_ratio_back"], "y": p["area_ratio_shock"]}
                             for p in shock_position_sweep(inputs, 80)]
        self.shockCurveChanged.emit()

    def _build_table(self):
        return distribution_table(self._inputs(), self._normalized)

    def _marker_text(self) -> str:
        return "THROAT"

    def _set_input(self, attribute: str, value, minimum: float = 0.0) -> bool:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        if not np.isfinite(number) or number <= minimum:
            return False
        if getattr(self, attribute) == number:
            return False
        setattr(self, attribute, number)
        return True

    def _republish(self) -> None:
        self._recalculate()
        self.inputsChanged.emit()
        self._regenerate_table()

    # -- gas ------------------------------------------------------------

    @Property(float, notify=inputsChanged)
    def gamma(self) -> float:
        return self._gamma

    @gamma.setter
    def gamma(self, value: float) -> None:
        if self._set_input("_gamma", value, minimum=1.0):
            self._republish()

    @Property(float, notify=inputsChanged)
    def gasConstant(self) -> float:
        return self._gas_constant

    @gasConstant.setter
    def gasConstant(self, value: float) -> None:
        if self._set_input("_gas_constant", value):
            self._republish()

    # -- reservoir ------------------------------------------------------

    @Property(float, notify=inputsChanged)
    def stagnationPressure(self) -> float:
        return self._stagnation_pressure

    @stagnationPressure.setter
    def stagnationPressure(self, value: float) -> None:
        """Changing p0 holds the *ratio* when the ratio is what was typed.

        Otherwise typing a new reservoir pressure would silently move the
        operating point into another regime, which is the opposite of what a
        user adjusting the chamber expects.
        """
        try:
            number = float(value)
        except (TypeError, ValueError):
            return
        if not np.isfinite(number) or number <= 0.0 or number == self._stagnation_pressure:
            return
        ratio = self._back_pressure / self._stagnation_pressure
        self._stagnation_pressure = number
        if self._pressure_mode == PressureMode.RATIO.value:
            self._back_pressure = ratio * number
        self._republish()

    @Property(float, notify=inputsChanged)
    def stagnationTemperature(self) -> float:
        return self._stagnation_temperature

    @stagnationTemperature.setter
    def stagnationTemperature(self, value: float) -> None:
        if self._set_input("_stagnation_temperature", value):
            self._republish()

    # -- geometry -------------------------------------------------------

    @Property(float, notify=inputsChanged)
    def throatArea(self) -> float:
        return self._throat_area

    @throatArea.setter
    def throatArea(self, value: float) -> None:
        if self._set_input("_throat_area", value):
            self._republish()

    @Property(float, notify=inputsChanged)
    def areaRatio(self) -> float:
        return self._area_ratio

    @areaRatio.setter
    def areaRatio(self, value: float) -> None:
        if self._set_input("_area_ratio", value, minimum=1.0):
            self._republish()

    @Property(float, notify=inputsChanged)
    def exitArea(self) -> float:
        return self._throat_area * self._area_ratio

    @exitArea.setter
    def exitArea(self, value: float) -> None:
        """The exit area is stored as a ratio, so the two modes cannot drift."""
        try:
            number = float(value)
        except (TypeError, ValueError):
            return
        if not np.isfinite(number) or number <= self._throat_area:
            return
        ratio = number / self._throat_area
        if ratio != self._area_ratio:
            self._area_ratio = ratio
            self._republish()

    @Property(str, notify=inputsChanged)
    def areaMode(self) -> str:
        return self._area_mode

    @areaMode.setter
    def areaMode(self, value: str) -> None:
        mode = AreaMode(value).value
        if mode != self._area_mode:
            self._area_mode = mode
            self.inputsChanged.emit()

    @Property("QVariantList", constant=True)
    def areaModes(self):
        return [{"mode": m.key.value if hasattr(m.key, "value") else m.key,
                 "label": m.label, "hint": m.hint} for m in AREA_MODES]

    # -- back pressure --------------------------------------------------

    @Property(float, notify=inputsChanged)
    def backPressure(self) -> float:
        return self._back_pressure

    @backPressure.setter
    def backPressure(self, value: float) -> None:
        if self._set_input("_back_pressure", value):
            self._republish()

    @Property(float, notify=inputsChanged)
    def backPressureRatio(self) -> float:
        return self._back_pressure / self._stagnation_pressure

    @backPressureRatio.setter
    def backPressureRatio(self, value: float) -> None:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return
        if not np.isfinite(number) or number <= 0.0:
            return
        target = number * self._stagnation_pressure
        if target != self._back_pressure:
            self._back_pressure = target
            self._republish()

    @Property(str, notify=inputsChanged)
    def pressureMode(self) -> str:
        return self._pressure_mode

    @pressureMode.setter
    def pressureMode(self, value: str) -> None:
        """Switching how the pressure is stated must not move the pressure."""
        mode = PressureMode(value).value
        if mode != self._pressure_mode:
            self._pressure_mode = mode
            self.inputsChanged.emit()

    @Property("QVariantList", constant=True)
    def pressureModes(self):
        return [{"mode": m.key.value if hasattr(m.key, "value") else m.key,
                 "label": m.label, "hint": m.hint} for m in PRESSURE_MODES]

    # -- resolution -----------------------------------------------------

    @Property(int, notify=inputsChanged)
    def resolution(self) -> int:
        return self._resolution

    @resolution.setter
    def resolution(self, value: int) -> None:
        try:
            count = int(value)
        except (TypeError, ValueError):
            return
        count = int(np.clip(count, 11, MAX_RESOLUTION))
        if count != self._resolution:
            self._resolution = count
            self._republish()

    @Property(int, constant=True)
    def maxResolution(self) -> int:
        return MAX_RESOLUTION

    # ------------------------------------------------------------------
    # results
    # ------------------------------------------------------------------

    @Property("QVariantList", notify=resultsChanged)
    def results(self):
        return self._result_rows()

    @Property(bool, notify=resultsChanged)
    def valid(self) -> bool:
        return self._is_valid()

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

    @Property(str, notify=resultsChanged)
    def regime(self) -> str:
        return self._result.branch_used if self._result and self._result.ok else ""

    @Property(str, notify=resultsChanged)
    def regimeLabel(self) -> str:
        if not (self._result and self._result.ok):
            return ""
        return regime_info(self._result.branch_used).label

    @Property(str, notify=resultsChanged)
    def regimeTone(self) -> str:
        if not (self._result and self._result.ok):
            return "neutral"
        return regime_info(self._result.branch_used).tone

    @Property(str, notify=resultsChanged)
    def regimeNote(self) -> str:
        if not (self._result and self._result.ok):
            return ""
        return regime_info(self._result.branch_used).note

    @Property(str, notify=resultsChanged)
    def externalContext(self) -> str:
        """What happens outside the exit plane, when anything does.

        Empty for every regime whose jet needs no external adjustment, so the
        page shows the sentence only where it is true.
        """
        if not (self._result and self._result.ok):
            return ""
        return regime_info(self._result.branch_used).external

    @Property(bool, notify=resultsChanged)
    def hasShock(self) -> bool:
        """Whether an internal shock exists *now*.

        Every shock readout, row and marker is bound to this, so leaving one
        regime for another cannot leave a stale shock on screen.
        """
        return self._record is not None and self._record.shock is not None

    @Property(bool, notify=resultsChanged)
    def choked(self) -> bool:
        return self._record is not None and self._record.choked

    @Property("QVariantList", notify=resultsChanged)
    def resultGroups(self):
        """Group names in the order the rows first mention them."""
        groups: list[str] = []
        for row in self._result_rows():
            if row["group"] and row["group"] not in groups:
                groups.append(row["group"])
        return groups

    @Slot(str, result=float)
    def rawValue(self, key: str) -> float:
        return self._raw_result_value(key)

    @Slot(str, result=str)
    def formatted(self, key: str) -> str:
        value = self._raw_result_value(key)
        return "—" if value != value else format_engineering(value, self._precision)

    # ------------------------------------------------------------------
    # thresholds, presets and the regime map
    # ------------------------------------------------------------------

    @Property("QVariantList", notify=inputsChanged)
    def regimeBands(self):
        return self._bands

    @Property(float, notify=inputsChanged)
    def firstCritical(self) -> float:
        return self._thresholds.get("first_critical", float("nan"))

    @Property(float, notify=inputsChanged)
    def secondCritical(self) -> float:
        return self._thresholds.get("second_critical", float("nan"))

    @Property(float, notify=inputsChanged)
    def thirdCritical(self) -> float:
        return self._thresholds.get("third_critical", float("nan"))

    @Property(float, notify=inputsChanged)
    def designExitMach(self) -> float:
        return self._thresholds.get("mach_exit_supersonic", float("nan"))

    @Slot(str)
    def applyPreset(self, which: str) -> None:
        """Set the back pressure exactly to one computed threshold.

        Nothing here is hard-coded: the value comes from the same threshold
        calculation the map is drawn from, which is what makes the boundary
        regimes reachable by a click rather than by a lucky drag.
        """
        values = thresholds(self._inputs())
        key = {"choking": "first_critical",
               "shock_exit": "second_critical",
               "ideal": "third_critical"}.get(which)
        if key is None or key not in values:
            return
        self._back_pressure = values[key] * self._stagnation_pressure
        self._republish()

    @Slot(int, result="QVariantList")
    def backPressureSweep(self, count: int):
        return back_pressure_sweep(self._inputs(), count)

    @Slot(int, result="QVariantList")
    def shockPositionSweep(self, count: int):
        return shock_position_sweep(self._inputs(), count)

    @Slot(result="QVariantList")
    def shockPositionSeries(self):
        """As/At against pb/p0, ready for a chart."""
        # 80 points draws a smooth curve for about a fifth of a second of
        # solving; each one is a bracketed shock location, not a table lookup.
        points = shock_position_sweep(self._inputs(), 80)
        return [{"x": p["pressure_ratio_back"], "y": p["area_ratio_shock"]}
                for p in points]

    @Property("QVariantList", notify=shockCurveChanged)
    def shockCurve(self):
        """As/At against pb/p0 for this nozzle, solved with the operating point.

        The same points :meth:`shockPositionSeries` returns, held rather than
        re-solved, so a view that draws the curve never solves it.
        """
        return self._shock_curve

    @Slot(result="QVariantList")
    def shockAxialSeries(self):
        """x_s against pb/p0 -- meaningful only because a real profile exists."""
        points = shock_position_sweep(self._inputs(), 80)
        return [{"x": p["pressure_ratio_back"], "y": p["x"]} for p in points]

    # ------------------------------------------------------------------
    # the distribution and its charts
    # ------------------------------------------------------------------

    @Property(bool, notify=tableSettingsChanged)
    def normalized(self) -> bool:
        return self._normalized

    @normalized.setter
    def normalized(self, value: bool) -> None:
        flag = bool(value)
        if flag != self._normalized:
            self._normalized = flag
            self.tableSettingsChanged.emit()
            self._regenerate_table()

    @Property(QObject, constant=True)
    def tableModel(self) -> QObject:
        return self._table_model

    @Property("QVariantList", notify=tableChanged)
    def tableColumns(self):
        return self._table_model.columns

    @Property(int, notify=tableChanged)
    def rowCount(self) -> int:
        return self._table_model.rowCount()

    @Property(str, notify=tableChanged)
    def tableCaption(self) -> str:
        return self._table_message

    @Property("QVariantMap", notify=tableChanged)
    def rowMarkers(self):
        """Row index -> marker label, as strings QML can key on."""
        return {str(index): text for index, text in self._row_markers.items()}

    @Property(int, notify=tableChanged)
    def throatRow(self) -> int:
        return self._throat_row

    @Property(int, notify=tableChanged)
    def preShockRow(self) -> int:
        return self._pre_shock_row

    @Property(int, notify=tableChanged)
    def postShockRow(self) -> int:
        return self._post_shock_row

    @Property(int, notify=tableChanged)
    def exitRow(self) -> int:
        return self._table_model.rowCount() - 1

    def _on_table_built(self, data) -> None:
        self._row_markers = dict(getattr(data, "markers", {}) or {})
        metadata = getattr(data, "metadata", {}) or {}
        self._throat_row = int(metadata.get("throat_index", -1))
        shock_index = metadata.get("shock_index")
        self._pre_shock_row = -1 if shock_index is None else int(shock_index)
        self._post_shock_row = -1 if shock_index is None else int(shock_index) + 1

    def _on_table_cleared(self) -> None:
        self._row_markers = {}
        self._throat_row = -1
        self._pre_shock_row = -1
        self._post_shock_row = -1

    @Slot()
    def regenerateTable(self) -> None:
        self._regenerate_table()

    @Slot(int)
    def selectRow(self, row: int) -> None:
        self._selected_row = row

    @Slot(int, result="QVariantList")
    def stationAt(self, row: int):
        """One station, as labelled rows for the inspector."""
        if row < 0 or row >= self._table_model.rowCount():
            return []
        values = self._table_model.values
        return [{"key": column["key"], "label": column["label"],
                 "unit": column["unit"],
                 "value": float(values[row, index]),
                 "text": format_engineering(float(values[row, index]),
                                            self._table_precision)}
                for index, column in enumerate(self._table_model.columns)]

    @Slot(str, result="QVariantList")
    def series(self, quantity: str):
        """One distributed quantity against x, split at the shock.

        Two series rather than one: joining them would draw a line across the
        discontinuity, and the jump is the thing worth seeing.
        """
        record = self._record
        if record is None:
            return []
        source = {
            "mach": record.mach,
            "pressure": record.pressure,
            "temperature": record.temperature,
            "density": record.density,
            "velocity": record.velocity,
            "stagnation_pressure": record.stagnation_pressure,
            "pressure_ratio": record.pressure_ratio,
            "temperature_ratio": record.temperature_ratio,
            "stagnation_pressure_ratio": record.stagnation_pressure_ratio,
            "area_ratio": record.area_ratio,
        }.get(quantity)
        if source is None:
            return []

        x = np.asarray(record.x, dtype=float)
        y = np.asarray(source, dtype=float)
        index = record.shock_index
        if index is None:
            return [{"label": "", "points": _points(x, y)}]
        return [
            {"label": "upstream", "points": _points(x[:index + 1], y[:index + 1])},
            {"label": "downstream", "points": _points(x[index + 1:], y[index + 1:])},
        ]

    @Slot(result="QVariantList")
    def contourSeries(self):
        """The nozzle wall as a radius, for the geometry overlay.

        A straight-walled cone, and the page says so: this module analyses a
        supplied area distribution and does not design a contour.
        """
        record = self._record
        if record is None:
            return []
        x = np.asarray(record.x, dtype=float)
        radius = np.sqrt(np.asarray(record.area, dtype=float) / np.pi)
        return [{"label": "wall", "points": _points(x, radius)},
                {"label": "mirror", "points": _points(x, -radius)}]

    @Slot(result="QVariantList")
    def markers(self):
        """Vertical guides for the distribution charts.

        The shock marker exists only while a shock does, so switching to an
        overexpanded back pressure removes the line rather than stranding it.
        """
        record = self._record
        if record is None:
            return []
        out = [{"value": float(record.x[record.throat_index]), "axis": "x",
                "label": "throat"}]
        if record.shock is not None and record.shock.x is not None:
            out.append({"value": float(record.shock.x), "axis": "x", "label": "shock"})
        return out

    # -- the same readings as properties -------------------------------
    #
    # A binding re-reads a property when its signal fires; it never re-calls a
    # slot. Views bind to these, so the drawing, the guides and the charts
    # follow every solve. All of them read the solved record; none solves.

    def _presentation(self) -> dict:
        if self._presented is None:
            self._presented = {
                "contour": self.contourSeries(),
                "stations": self.markers(),
                "distribution": {q["key"]: self.series(q["key"])
                                 for q in self.chartQuantities},
                "viewport": nozzle_viewport(self._record, self._identity, self._precision),
            }
        return self._presented

    @Property(int, notify=resultsChanged)
    def resultIdentity(self) -> int:
        """The number of the solved state every view is showing."""
        return self._identity

    @Property("QVariantMap", notify=resultsChanged)
    def viewport(self):
        """This solution's stations and extent (``visualization.viewport``): what
        the drawing, the charts and the inspector select by."""
        return self._presentation()["viewport"]

    @Property(QObject, constant=True)
    def selection(self) -> QObject:
        return self._selection

    @Property("QVariantMap", notify=selectionReadoutChanged)
    def selectionReadout(self):
        """The inspector's reading of the selection, from the solved snapshot.

        A station reads its own solved rows; a plotted point reads back the x
        and y the chart supplied. Nothing is recomputed to answer it.
        """
        selection = self._selection
        viewport = self._presentation()["viewport"]
        base = {"identity": self._identity, "fidelity": viewport.get("label", "")}
        if selection.kind == "station":
            for station in viewport.get("stations", []):
                if station["key"] == selection.key:
                    return dict(base, kind="station", key=station["key"],
                                title=station["title"], note=station["note"],
                                rows=station["rows"])
            return {}
        if selection.kind == "plotPoint":
            rows = [{"label": "x", "value": format_engineering(selection.x, self._precision),
                     "unit": "m", "raw": selection.x}]
            if not math.isnan(selection.y):
                rows.append({"label": selection.label,
                             "value": format_engineering(selection.y, self._precision),
                             "unit": "", "raw": selection.y})
            return dict(base, kind="plotPoint", key=selection.key,
                        title=selection.label or "Plotted point", note="a solved station of the distribution",
                        rows=rows)
        return {}

    @Property("QVariantList", notify=resultsChanged)
    def contour(self):
        return self._presentation()["contour"]

    @Property("QVariantList", notify=resultsChanged)
    def stationMarkers(self):
        return self._presentation()["stations"]

    @Property("QVariantMap", notify=resultsChanged)
    def distribution(self):
        """Quantity key -> the series :meth:`series` returns for it."""
        return self._presentation()["distribution"]

    @Property("QVariantList", constant=True)
    def chartQuantities(self):
        return [
            {"key": "mach", "label": "Mach  M", "unit": ""},
            {"key": "pressure", "label": "Static pressure  p", "unit": "Pa"},
            {"key": "temperature", "label": "Static temperature  T", "unit": "K"},
            {"key": "density", "label": "Density  ρ", "unit": "kg/m³"},
            {"key": "velocity", "label": "Velocity  V", "unit": "m/s"},
            {"key": "stagnation_pressure", "label": "Stagnation pressure  p₀",
             "unit": "Pa"},
        ]

    # ------------------------------------------------------------------
    # precision, copy, export
    # ------------------------------------------------------------------

    @Property(int, notify=resultsChanged)
    def precision(self) -> int:
        return self._precision

    @precision.setter
    def precision(self, value: int) -> None:
        if self._set_precision_value(value):
            self._recalculate()

    @Property(int, notify=tableSettingsChanged)
    def tablePrecision(self) -> int:
        return self._table_precision

    @tablePrecision.setter
    def tablePrecision(self, value: int) -> None:
        if self._set_table_precision_value(value):
            self._regenerate_table()

    @Slot()
    def copyTable(self) -> None:
        self._copy_text(self._table_model.tableAsText())

    @Slot(int)
    def copyRow(self, row: int) -> None:
        self._copy_row(row)

    @Slot(str, result=str)
    def exportCsv(self, directory: str) -> str:
        return self._export_csv(directory)

    # ------------------------------------------------------------------
    # reference validation
    # ------------------------------------------------------------------

    @Property(bool, constant=True)
    def referenceAvailable(self) -> bool:
        """No published nozzle appendix exists here, and none is invented."""
        return False

    @Property(str, constant=True)
    def referenceMessage(self) -> str:
        return nozzle_validation().message

    @Property(str, constant=True)
    def validationStatus(self) -> str:
        return nozzle_validation().status

    @Property(str, constant=True)
    def validationCitation(self) -> str:
        return nozzle_validation().citation

    @Property("QVariantList", constant=True)
    def validationChecks(self):
        return [{"name": check.name, "status": check.status, "detail": check.detail}
                for check in nozzle_validation().checks]


def _points(x: np.ndarray, y: np.ndarray) -> list:
    return [{"x": float(a), "y": float(b)} for a, b in zip(x, y)]
