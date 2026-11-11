"""The Qt facade for the Reference Cases workspace (QML singleton ``ReferenceCases``, DB-4C display).

It shows DB-4C's four ideal reference points: what each 1985 TDK printout
prints, and, after an explicit Run, step A (the printout beside NASA CEA) and
step B (RocketForge's constant-gamma reduction beside CEA). It computes only on
:meth:`run`, through :func:`.reference_ideal_case.run_ideal_cases`, and keeps
nothing between runs. Every word and number comes from :mod:`.reference_case_view`;
QML only places them (DB4C_IDEAL_REFERENCE_DISPLAY.md).

At module level this imports the runner, the view and the row model: no
provider. The provider's availability is read the first time the page asks for
it, not when the application starts.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..rowmodel import RowListModel
from . import reference_case_view as view
from . import reference_ideal_case as ideal

__all__ = ["ReferenceCaseController"]


class ReferenceCaseController(QObject):
    """Backs the Reference Cases page."""

    runChanged = Signal()
    selectionChanged = Signal()
    providerChanged = Signal()

    def __init__(self, parent: QObject | None = None, *,
                 runner: Callable[[], tuple[Any, ...]] | None = None,
                 availability: Callable[[], Any] | None = None) -> None:
        super().__init__(parent)
        self._runner = runner or ideal.run_ideal_cases
        self._availability_source = availability
        self._availability: Any = None
        self._points = ideal.POINTS
        self._outcomes: tuple[Any, ...] | None = None
        self._selected = 0
        self._busy = False

        self._browser = RowListModel(("pointKey", "pointName", "section", "sectionStart", "inputsLine",
                                      "pointState", "pointStateWord"), self)
        self._inputs = RowListModel(("inputLabel", "inputText"), self)
        self._step_a = RowListModel(("quantity", "printed", "computed", "difference", "kind"), self)
        self._step_b = RowListModel(("basis", "rocketforge", "cea", "difference", "kind", "reference"), self)
        self._declarations = RowListModel(("line",), self)
        self._warnings = RowListModel(("line",), self)
        self._missing = RowListModel(("line",), self)
        self._publish()

    # ------------------------------------------------------------ provider

    def _provider(self) -> Any:
        if self._availability is None:
            if self._availability_source is not None:
                self._availability = self._availability_source()
            else:
                from .thermochemistry_provider import availability
                self._availability = availability()
        return self._availability

    @Property(bool, notify=providerChanged)
    def providerUsable(self) -> bool:
        return bool(self._provider().usable)

    @Property(str, notify=providerChanged)
    def providerLine(self) -> str:
        status = self._provider()
        if status.usable:
            return f"{status.headline} available"
        reason = " ".join(part for part in (status.detail, status.remedy) if part)
        return f"{status.headline}: {reason}" if reason else status.headline

    # ------------------------------------------------------------ run

    @Property(bool, notify=runChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=runChanged)
    def hasRun(self) -> bool:
        return self._outcomes is not None

    @Property(str, notify=runChanged)
    def runSummary(self) -> str:
        if self._outcomes is None:
            return "Not run. The printed values are shown; nothing has been computed."
        counts: dict[str, int] = {}
        for outcome in self._outcomes:
            counts[outcome.kind] = counts.get(outcome.kind, 0) + 1
        parts = [f"{counts[k]} {view.STATE_WORDS[k].lower()}" for k in ("ok", "refused", "unavailable") if k in counts]
        return f"Last run: {', '.join(parts)} of {len(self._outcomes)} points. Each run recomputes every point."

    @Slot()
    def run(self) -> None:
        """Compute all four points, both steps, now. Nothing from an earlier run is kept."""
        if self._busy:
            return
        self._busy = True
        self._outcomes = None
        self._publish()
        self.runChanged.emit()
        try:
            self._outcomes = tuple(self._runner())
        finally:
            self._busy = False
        # A run is also the moment the provider was last asked: read its state afresh.
        self._availability = None
        self._publish()
        self.runChanged.emit()
        self.selectionChanged.emit()
        self.providerChanged.emit()

    # ------------------------------------------------------------ selection

    @Property(QObject, constant=True)
    def browser(self) -> QObject:
        return self._browser

    @Property(int, notify=selectionChanged)
    def selectedIndex(self) -> int:
        return self._selected

    @Slot(int)
    def select(self, index: int) -> None:
        if not 0 <= index < len(self._points) or index == self._selected:
            return
        self._selected = index
        self._publish()
        self.selectionChanged.emit()

    def _point(self):
        return self._points[self._selected]

    def _outcome(self) -> Any | None:
        return None if self._outcomes is None else self._outcomes[self._selected]

    def _state(self, index: int) -> str:
        return "not-run" if self._outcomes is None else self._outcomes[index].kind

    # ------------------------------------------------------------ the selected point

    @Property(str, notify=selectionChanged)
    def pointTitle(self) -> str:
        return view.point_text(self._point()).title

    @Property(str, notify=selectionChanged)
    def pointDocument(self) -> str:
        return view.point_text(self._point()).document

    @Property(str, notify=selectionChanged)
    def citation(self) -> str:
        return view.point_text(self._point()).citation

    @Property(str, notify=selectionChanged)
    def codeLine(self) -> str:
        return view.point_text(self._point()).code

    @Property(str, notify=selectionChanged)
    def databaseLine(self) -> str:
        return view.point_text(self._point()).database

    @Property(str, constant=True)
    def classLine(self) -> str:
        return view.CLASS_LINE

    @Property(str, notify=selectionChanged)
    def notes(self) -> str:
        return view.point_text(self._point()).notes

    @Property(str, notify=selectionChanged)
    def pointState(self) -> str:
        return self._state(self._selected)

    @Property(str, notify=selectionChanged)
    def pointStateWord(self) -> str:
        return view.STATE_WORDS[self._state(self._selected)]

    @Property(str, notify=selectionChanged)
    def inputsHeading(self) -> str:
        outcome = self._outcome()
        return "Run at" if outcome is not None else "To be run at"

    @Property(bool, notify=selectionChanged)
    def stopped(self) -> bool:
        outcome = self._outcome()
        return outcome is not None and outcome.kind != ideal.KIND_OK

    @Property(str, notify=selectionChanged)
    def stopMessage(self) -> str:
        outcome = self._outcome()
        if outcome is None or outcome.kind == ideal.KIND_OK:
            return ""
        return view.stop_line(outcome.kind, outcome.message)

    @Property(str, constant=True)
    def stepANote(self) -> str:
        return view.STEP_A_NOTE

    @Property(str, constant=True)
    def stepBNote(self) -> str:
        return view.STEP_B_NOTE

    @Property("QStringList", constant=True)
    def stepAHeads(self) -> list[str]:
        return list(view.STEP_A_HEADS)

    @Property("QStringList", constant=True)
    def stepBHeads(self) -> list[str]:
        return list(view.STEP_B_HEADS)

    @Property(QObject, constant=True)
    def runInputs(self) -> QObject:
        return self._inputs

    @Property(QObject, constant=True)
    def stepA(self) -> QObject:
        return self._step_a

    @Property(QObject, constant=True)
    def stepB(self) -> QObject:
        return self._step_b

    @Property(QObject, constant=True)
    def declarations(self) -> QObject:
        return self._declarations

    @Property(QObject, constant=True)
    def warnings(self) -> QObject:
        return self._warnings

    @Property(QObject, constant=True)
    def missing(self) -> QObject:
        return self._missing

    # ------------------------------------------------------------ publication

    def rows(self) -> dict[str, list[dict]]:
        """Everything the models hold, for tests and the parity check. QML binds the models."""
        return {"browser": self._browser_rows, "inputs": self._input_rows, "step_a": self._step_a_rows,
                "step_b": self._step_b_rows, "declarations": self._declaration_rows,
                "warnings": self._warning_rows, "missing": self._missing_rows}

    def _publish(self) -> None:
        point, outcome = self._point(), self._outcome()
        states = [self._state(i) for i in range(len(self._points))]
        self._browser_rows = view.browser_rows(self._points, states)
        run = outcome.chamber_case if outcome is not None and outcome.chamber_case is not None \
            else ideal.chamber_case(point)
        self._input_rows = view.run_input_rows(run, point)
        ok = outcome is not None and outcome.kind == ideal.KIND_OK
        stopped = outcome is not None and not ok
        # A stopped point shows its reason in place of both tables: no partial row, printed or computed.
        self._step_a_rows = [] if stopped else view.step_a_rows(point, outcome.step_a if ok else None)
        self._step_b_rows = view.step_b_rows(outcome.step_b) if ok else []
        self._declaration_rows = view.declaration_lines(
            outcome.declarations if outcome is not None else ideal.declarations(point))
        self._warning_rows = view.warning_lines(outcome.warnings if ok else None)
        self._missing_rows = [{"line": line} for line in view.point_text(point).missing]
        for model, rows in ((self._browser, self._browser_rows), (self._inputs, self._input_rows),
                            (self._step_a, self._step_a_rows), (self._step_b, self._step_b_rows),
                            (self._declarations, self._declaration_rows), (self._warnings, self._warning_rows),
                            (self._missing, self._missing_rows)):
            model.set_rows(rows)
