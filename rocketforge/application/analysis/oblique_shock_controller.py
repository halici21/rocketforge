"""The QObject the Oblique Shock page binds to.

Thin by design: validate, call :mod:`oblique_shock_service`, republish.

The one thing it adds is the theta-beta-M diagram's data, and it adds it by
asking the *same* service the calculator asks. A chart drawn from a second
implementation would be a second answer, and the two would eventually disagree.

The view state -- one selection shared by the deflection table, the sweep
curve and the inspector, table blocks for pinning and copying, and the view
data held for the inputs it was made from (the limits, the diagram's curve,
the overlay curves) -- is presentation over values that already exist.
Nothing a view reads here solves anything a second time: only an input edit,
Generate, or asking for the overlay curves does. The weak and strong branches
are never merged: a table row is read back with the branch it was generated on.
"""

from __future__ import annotations

import math

from PySide6.QtCore import Property, QObject, Signal, Slot

from ...core.errors import RocketForgeError
from ..formatting import format_engineering
from ..visualization.selection import AnalysisSelection
from ..visualization.table import block_text, clamp_block, table_block
from .analysis_behaviour import MAX_TABLE_ROWS, AnalysisBehaviour
from .oblique_shock_service import (
    SOLVE_MODES,
    ShockBranch,
    SolveMode,
    TableConvention,
    curve_data,
    generate_table,
    limits_for,
    mode_info,
    solve,
)

__all__ = ["ObliqueShockController"]


class ObliqueShockController(AnalysisBehaviour, QObject):
    """Application-side facade for the Oblique Shock analysis page."""

    resultsChanged = Signal()
    inputsChanged = Signal()
    tableChanged = Signal()
    tableSettingsChanged = Signal()
    referenceChanged = Signal()
    curveChanged = Signal()
    selectionReadoutChanged = Signal()
    tableStaleChanged = Signal()
    requestTab = Signal(int)

    _export_name = "oblique_shock"

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._init_analysis()

        # calculator
        self._mode = SolveMode.THETA.value
        self._input = 10.0
        self._mach1 = 2.0
        self._gamma = 1.4
        self._branch = ShockBranch.WEAK.value

        # study
        self._table_start = 0.0
        self._table_end = 40.0
        self._table_step = 0.5
        self._table_convention = TableConvention.BRANCH.value
        self._table_mach1 = 2.0
        self._table_branch = ShockBranch.WEAK.value
        self._table_capped = False

        # diagram
        self._curve_points = 400

        # view state: the view data held for the inputs it was made from, the
        # settings the table on screen was generated with, and one selection
        # shared by the table, the sweep curve and the inspector.
        self._limits_memo: tuple | None = None
        self._curve_memo: tuple | None = None
        self._overlay_memo: tuple | None = None
        self._identity = 0
        self._table_identity = 0
        self._generated: dict = {}
        self._selection = AnalysisSelection(self)
        self._selection.changed.connect(self.selectionReadoutChanged)
        self.tableChanged.connect(self.selectionReadoutChanged)
        self.resultsChanged.connect(self.selectionReadoutChanged)
        self.tableChanged.connect(self.tableStaleChanged)
        self.tableSettingsChanged.connect(self.tableStaleChanged)

        self._recalculate()
        self.regenerateTable()
        self._limits()
        self._curve_data()

    # ==================================================================
    # calculator inputs
    # ==================================================================

    @Property("QVariantList", constant=True)
    def solveModes(self):
        return [
            {"key": info.mode.value, "label": info.label, "symbol": info.symbol,
             "hint": info.hint, "needsBranch": info.needs_branch,
             "iterative": info.iterative, "defaultValue": info.default_value}
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

    def _get_mach1(self) -> float:
        return self._mach1

    def _set_mach1(self, value: float) -> None:
        if float(value) == self._mach1:
            return
        self._mach1 = float(value)
        self.inputsChanged.emit()
        self.curveChanged.emit()
        self._recalculate()

    mach1 = Property(float, _get_mach1, _set_mach1, notify=inputsChanged)

    def _get_gamma(self) -> float:
        return self._gamma

    def _set_gamma(self, value: float) -> None:
        if float(value) == self._gamma:
            return
        self._gamma = float(value)
        self.inputsChanged.emit()
        self.curveChanged.emit()
        self._recalculate()

    gamma = Property(float, _get_gamma, _set_gamma, notify=inputsChanged)

    def _get_branch(self) -> str:
        return self._branch

    def _set_branch(self, value: str) -> None:
        if value == self._branch:
            return
        self._branch = value
        self.inputsChanged.emit()
        self.curveChanged.emit()
        self._recalculate()

    branch = Property(str, _get_branch, _set_branch, notify=inputsChanged)

    @Property(bool, notify=inputsChanged)
    def branchRequired(self) -> bool:
        """Only the deflection mode has two roots to choose between.

        In the wave-angle mode the branch is a *consequence* of the angle, so
        offering a control would imply a choice that does not exist.
        """
        return mode_info(self._mode).needs_branch

    @Property(bool, notify=inputsChanged)
    def modeIsIterative(self) -> bool:
        return mode_info(self._mode).iterative

    @Property(str, notify=inputsChanged)
    def inputSymbol(self) -> str:
        return mode_info(self._mode).symbol

    def _limits(self) -> dict:
        """:func:`limits_for` at the current M₁ and gamma, held until either changes.

        The service already answers a refused state with an empty mapping, so
        what is held is exactly what a fresh call would return.
        """
        key = (self._mach1, self._gamma)
        if self._limits_memo is None or self._limits_memo[0] != key:
            self._limits_memo = (key, limits_for(self._mach1, self._gamma))
        return self._limits_memo[1]

    @Property(str, notify=inputsChanged)
    def inputHint(self) -> str:
        info = mode_info(self._mode)
        limits = self._limits()
        if not limits:
            return info.hint
        if info.mode is SolveMode.THETA:
            return f"0 up to θ_max = {limits['thetaMax']:.4f}°"
        return f"between μ = {limits['machAngle']:.4f}° and 90°"

    @Property("QVariantMap", notify=inputsChanged)
    def limits(self):
        """The three angles that bound the problem, in degrees."""
        return dict(self._limits())

    # ==================================================================
    # results
    # ==================================================================

    def _compute(self):
        return solve(self._mode, self._input, self._mach1, self._gamma, self._branch)

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
        """A detached request is a warning, not an error in the arithmetic."""
        if self._result is not None and self._result.status == "Detached":
            return "warning"
        return self._status_tone()

    @Property(bool, notify=resultsChanged)
    def detached(self) -> bool:
        """Whether the requested deflection has no attached solution.

        Bound by the page so it can clear the previous wave angle and ratios
        rather than leaving them on screen looking current.
        """
        return bool(self._result is not None and self._result.status == "Detached")

    @Property("QVariantList", notify=resultsChanged)
    def diagnostics(self):
        return self._diagnostic_dicts()

    @Property(float, notify=resultsChanged)
    def mach(self) -> float:
        return self._mach_value()

    @Slot(str, result=float)
    def resultValue(self, key: str) -> float:
        return self._raw_result_value(key)

    @Property(str, notify=resultsChanged)
    def branchUsed(self) -> str:
        return "" if self._result is None else self._result.branch_used

    @Property("QVariantList", notify=resultsChanged)
    def resultGroups(self):
        """The readout groups in order, so the page need not hard-code them.

        The groups differ between the single-branch and both-branches results,
        and a page holding a fixed list would silently show nothing when the
        other one arrived.
        """
        if self._result is None or not self._result.ok:
            return []
        seen = []
        for row in self._result.rows:
            if row.group and row.group not in seen:
                seen.append(row.group)
        return seen

    @Property("QVariantMap", notify=resultsChanged)
    def operatingPoint(self):
        """Where the current solution sits on the diagram, in degrees.

        Empty when there is no attached solution, so the marker disappears
        rather than lingering at the last valid answer.
        """
        if self._result is None or not self._result.ok:
            return {}
        if self._result.branch_used == "both" and self._result.both is not None:
            weak, strong = self._result.both
            return {
                "theta": self._input if mode_info(self._mode).mode is SolveMode.THETA
                         else float("nan"),
                "betaWeak": math.degrees(weak),
                "betaStrong": math.degrees(strong),
                "both": True,
            }
        theta = self._result.value_of("theta")
        beta = self._result.value_of("beta")
        if theta is None or beta is None:
            return {}
        return {"theta": theta, "beta": beta, "both": False,
                "branch": self._result.branch_used}

    @Property("QVariantList", constant=True)
    def assumptions(self):
        from ...physics.compressible import equations

        return list(equations.record("oblique_shock.theta_beta_mach.v1").assumptions)

    @Property(str, constant=True)
    def modelName(self) -> str:
        return "Calorically perfect gas"

    def _recalculate(self) -> None:
        """The shared recalculation, counted: views name the solved state they show."""
        self._identity += 1
        AnalysisBehaviour._recalculate(self)

    @Property(int, notify=resultsChanged)
    def resultIdentity(self) -> int:
        return self._identity

    @Slot(float)
    def setDeflectionAndSolve(self, theta_degrees: float) -> None:
        """Jump the calculator to a deflection, used by the study table."""
        self._mode = SolveMode.THETA.value
        self._input = float(theta_degrees)
        self.inputsChanged.emit()
        self._recalculate()

    # ==================================================================
    # the study table
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

    def _get_table_mach1(self) -> float:
        return self._table_mach1

    def _set_table_mach1(self, value: float) -> None:
        if self._set_table_setting("_table_mach1", float(value)):
            self.tableSettingsChanged.emit()

    tableMach1 = Property(float, _get_table_mach1, _set_table_mach1,
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
        return generate_table(self._table_mach1, self._table_gamma, self._table_start,
                              self._table_end, self._table_step, self._table_convention,
                              self._table_branch)

    def _marker_text(self) -> str:
        return "θ_max"

    def _on_table_built(self, data) -> None:
        self._table_capped = bool(data.metadata.get("capped_at_theta_max"))
        self._table_limit = float(data.metadata.get("theta_max", float("nan")))
        self._generated = dict(self._settings_now(), capped=self._table_capped,
                               thetaMax=self._table_limit)
        self._table_identity += 1
        self._drop_table_selection()

    def _on_table_cleared(self) -> None:
        self._table_capped = False
        self._generated = {}
        self._table_identity += 1
        self._drop_table_selection()

    def _settings_now(self) -> dict:
        return {"mach1": float(self._table_mach1), "gamma": float(self._table_gamma),
                "start": float(self._table_start), "end": float(self._table_end),
                "step": float(self._table_step), "convention": str(self._table_convention),
                "branch": str(self._table_branch)}

    def _generated_branch_words(self) -> str:
        """Which branch the generated rows are on, in words, from the generated settings."""
        if self._generated.get("convention") == "comparison":
            return "weak and strong side by side"
        return f"{self._generated.get('branch', '')} branch"

    def _table_caption(self) -> str:
        rows = self._table_model.rowCount()
        if not rows:
            return ""
        caption = (f"{rows:,} rows · M₁ = {self._table_mach1:g} · γ = {self._table_gamma:g} · "
                   f"{self._table_branch} branch · angles in degrees · "
                   "calculated by RocketForge")
        if self._table_capped:
            caption += f" · capped at θ_max = {self._table_limit:.4f}°"
        return caption

    @Property(bool, notify=tableChanged)
    def tableCapped(self) -> bool:
        """Whether the requested range ran past the attachment limit."""
        return self._table_capped

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

        ``mach1``, ``gamma``, ``start``, ``end``, ``step``, ``convention``,
        ``branch``, plus ``capped`` and ``thetaMax`` from the generated sweep.
        The settings fields may be edited ahead of the next Generate; anything
        that names the table on screen names it from here.
        """
        return dict(self._generated)

    @Property(str, notify=tableChanged)
    def generatedCaption(self) -> str:
        """The line under the sweep, from the settings it was generated with.

        :attr:`tableFooter` reads the settings fields (and names the branch
        setting even for a weak-versus-strong sweep); this names the sweep on
        screen: its M₁, gamma and branch as generated.
        """
        rows = self._table_model.rowCount()
        g = self._generated
        if not rows or not g:
            return ""
        caption = (f"{rows:,} rows · M₁ = {g['mach1']:g} · γ = {g['gamma']:g} · "
                   f"{self._generated_branch_words()} · angles in degrees · "
                   "calculated by RocketForge")
        if g.get("capped"):
            caption += f" · capped at θ_max = {g['thetaMax']:.4f}°"
        return caption

    @Property(bool, notify=tableStaleChanged)
    def tableStale(self) -> bool:
        """A setting was edited since the table on screen was generated."""
        if not self._generated:
            return False
        now = self._settings_now()
        return any(now[key] != self._generated[key] for key in now)

    @Property("QVariantMap", notify=tableChanged)
    def chartData(self):
        """Quantity key -> :meth:`chartSeries` for every plotted column.

        Read from the generated block; nothing is solved.
        """
        keys = [c["key"] for c in self._table_model.columns[1:]]
        return {key: self._chart_series(key) for key in keys}

    # ------------------------------------------------------------------
    # selection, shared by the table, the sweep curve and the inspector
    # ------------------------------------------------------------------

    def _drop_table_selection(self) -> None:
        """A selected row of the previous sweep means nothing in the new one."""
        if self._selection.kind in ("plotPoint", "tableRow", "tableRange"):
            self._selection.clear()

    @Property(int, notify=tableChanged)
    def tableIdentity(self) -> int:
        return self._table_identity

    @Property(QObject, constant=True)
    def selection(self) -> QObject:
        return self._selection

    def _row_at(self, theta: float) -> int:
        """The generated row whose θ is exactly ``theta``, else -1."""
        row = self._table_model.rowNearest(theta)
        if row < 0 or self._table_model.machAt(row) != theta:
            return -1
        return row

    def _cell_text(self, row: int, column: int) -> str:
        value = self._table_model.data(self._table_model.index(row, column))
        return "" if value is None else str(value)

    @Slot(int)
    def selectTableRow(self, row: int) -> None:
        """Select a generated row: the sweep curve and the inspector follow it."""
        if not 0 <= row < self._table_model.rowCount():
            return
        theta = self._table_model.machAt(row)
        self._selection.select("tableRow", str(row), theta, f"row {row + 1}", "table")

    @Slot(int, int)
    def selectTableRange(self, first: int, last: int) -> None:
        """Select a contiguous block of generated rows (the curve shows the interval)."""
        span = clamp_block(first, last, self._table_model.rowCount())
        if span is None:
            return
        a, b = span
        if a == b:
            self.selectTableRow(a)
            return
        label = f"θ {self._cell_text(a, 0)}–{self._cell_text(b, 0)}°"
        self._selection.selectRange("tableRange", f"rows:{a}-{b}", self._table_model.machAt(a),
                                    self._table_model.machAt(b), label, "table")

    @Slot(float, result=int)
    def rowExactly(self, theta: float) -> int:
        """The row generated at exactly ``theta``, else -1 (no nearest-row guess)."""
        return self._row_at(theta)

    @Slot(int, int, result="QVariantMap")
    def tableSnapshot(self, first: int, last: int):
        """Rows ``first``..``last`` as a table snapshot, exactly as shown.

        The block names the upstream Mach number and the branch it was
        generated on, so two blocks are never read as one solution.
        """
        model = self._table_model
        if not self._generated:
            return {}
        g = self._generated
        words = self._generated_branch_words()
        try:
            return table_block(source="oblique_shock.table", identity=self._table_identity,
                               columns=model.columns, values=model.values,
                               text_at=self._cell_text, first=first, last=last,
                               key_symbol="θ", stale=self.tableStale, gamma=g["gamma"],
                               mach1=g["mach1"], branch=g["branch"],
                               convention=g["convention"], regime=f"M₁ {g['mach1']:g} · {words}",
                               precision=self._table_precision,
                               provenance=(f"Generated by RocketForge at M₁ = {g['mach1']:g}, "
                                           f"γ = {g['gamma']:g}, {words}; angles in degrees"))
        except (ValueError, IndexError):
            return {}

    @Slot("QVariantMap", result="QVariantList")
    def restorableRange(self, snapshot):
        """The rows of the table on screen a pinned block names, else [].

        The block's own rows when it was pinned from this very table; else the
        rows generated at exactly its deflections -- but only when the table on
        screen was generated at the same M₁, gamma, columns and branch. The
        same θ on another branch or another Mach number is a different shock.
        """
        try:
            keys = [float(k) for k in snapshot.get("rowKeys", [])]
            if not keys or not self._generated:
                return []
            if int(snapshot.get("identity", -1)) == self._table_identity:
                a, b = int(snapshot["firstRow"]), int(snapshot["lastRow"])
            else:
                g = self._generated
                if (float(snapshot.get("mach1", math.nan)) != g["mach1"]
                        or float(snapshot.get("gamma", math.nan)) != g["gamma"]
                        or snapshot.get("convention") != g["convention"]
                        or snapshot.get("branch") != g["branch"]):
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

        A row is read back with the M₁, gamma and branch it was generated on;
        a weak-versus-strong row keeps its two branches in their own labelled
        columns. The θ_max row is where the two branches merge, and says so.
        The solved state reads the calculator's rows. Nothing is recomputed.
        """
        selection = self._selection
        model = self._table_model
        fidelity = "Calculated by RocketForge · calorically perfect gas"
        base = {"stale": self.tableStale}
        g = self._generated
        context = (f"M₁ = {g.get('mach1', math.nan):g}, γ = {g.get('gamma', math.nan):g}, "
                   f"{self._generated_branch_words()}")
        if selection.kind in ("plotPoint", "tableRow"):
            row = self._row_at(selection.x)
            if row < 0:
                return {}
            rows = [{"label": spec["label"], "value": self._cell_text(row, column),
                     "unit": spec.get("unit", "")}
                    for column, spec in enumerate(model.columns)]
            note = f"A generated sample at {context}; angles in degrees."
            if row == self._marker_row:
                note += " θ_max: the weak and strong solutions merge at this deflection."
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
                        note=(f"{b - a + 1} generated samples at {context}; "
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
    # the theta-beta-M diagram
    # ==================================================================

    @Slot(result="QVariantMap")
    def curve(self):
        """The diagram's data for the current M₁ and gamma, in degrees.

        From the same service the calculator uses, so the curve and the answer
        can never disagree about what the physics said.
        """
        try:
            return curve_data(self._mach1, self._gamma, self._curve_points)
        except (ArithmeticError, ValueError, TypeError):
            return {}

    @Slot(float, result="QVariantMap")
    def curveFor(self, mach1: float):
        """One comparison curve, for an overlay at another Mach number."""
        try:
            return curve_data(float(mach1), self._gamma, self._curve_points)
        except (ArithmeticError, ValueError, TypeError):
            return {}

    @Property("QVariantList", constant=True)
    def comparisonMachs(self):
        """The Mach numbers the diagram may overlay for context."""
        return [1.5, 2.0, 3.0, 5.0]

    def _curve_data(self) -> dict:
        """:meth:`curve` at the current M₁ and gamma, held until either changes.

        A state the service refuses (a subsonic M₁, a bad gamma) is held as an
        empty curve, so the diagram draws nothing rather than a previous one.
        """
        key = (self._mach1, self._gamma, self._curve_points)
        if self._curve_memo is None or self._curve_memo[0] != key:
            try:
                data = curve_data(self._mach1, self._gamma, self._curve_points)
            except (RocketForgeError, ArithmeticError, ValueError, TypeError):
                data = {}
            self._curve_memo = (key, data)
        return self._curve_memo[1]

    @Property("QVariantMap", notify=curveChanged)
    def curveData(self):
        """The diagram's data -- :meth:`curve` -- made once per M₁ and gamma.

        A property rather than a slot, so the diagram follows M₁ and gamma
        and a view that is opened again reads the curve already made.
        """
        return self._curve_data()

    @Property("QVariantList", notify=curveChanged)
    def comparisonCurves(self):
        """The overlay curves, one per :attr:`comparisonMachs`, at the current gamma.

        Made the first time the overlay is asked for and held until gamma
        changes; a Mach number the service refuses is left out, not drawn.
        The view skips the one equal to the current M₁.
        """
        key = (self._gamma, self._curve_points)
        if self._overlay_memo is None or self._overlay_memo[0] != key:
            curves = []
            for mach in self.comparisonMachs:
                try:
                    data = curve_data(float(mach), self._gamma, self._curve_points)
                except (RocketForgeError, ArithmeticError, ValueError, TypeError):
                    continue
                curves.append({"mach1": float(mach), "weak": data["weak"],
                               "strong": data["strong"]})
            self._overlay_memo = (key, curves)
        return self._overlay_memo[1]

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
    def rowNearest(self, value: float) -> int:
        return self._table_model.rowNearest(value)

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
        """Anderson publishes no oblique-shock table, and none is invented.

        Appendix C covers Prandtl-Meyer; there is no appendix of wave angles.
        The oblique-shock relations are validated instead against the worked
        reference cases in the project specification and, more strongly, by
        agreeing with the *published* normal-shock appendix at beta = 90°.
        """
        return False

    @Property(str, constant=True)
    def referenceMessage(self) -> str:
        return (
            "Anderson's Fundamentals of Aerodynamics publishes no oblique-shock table, "
            "so there is no printed table to compare against here. The relations are "
            "validated instead against worked reference cases, and against Appendix B "
            "itself: at β = 90° an oblique shock is a normal shock, and RocketForge "
            "reproduces the published normal-shock values exactly."
        )
