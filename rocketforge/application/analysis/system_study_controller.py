"""The QObject base every propulsion-system page (SYS gates) binds to.

A SYS page is one generic view (``ui/components/RFSystemWorkspace.qml``) over a
controller of this shape:

* ``inputSections`` -- what the user states, as sections of fields. A field is
  a number (typed in its display unit), a choice or a text, keyed
  ``"<branch>.<name>"``. The page writes back through :meth:`setField`,
  :meth:`setChoice` and :meth:`setText`, and list actions through
  :meth:`invoke`;
* ``basisRows`` and ``issues`` -- the upstream result being read, and every
  reason the study cannot be computed yet;
* the result -- per-branch views, totals, notes, assumptions, provenance and
  the JSON record.

It computes **only** from :meth:`compute`. Opening the page, editing an input
or a change upstream never computes: a change upstream only re-announces this
controller's state, and a result whose question has moved is reported stale
when it is next read.

A gate subclasses this and supplies :meth:`_basis`, :meth:`_build`,
:meth:`_solve`, :meth:`_sections`, the setters, and the presentation hooks.
"""

from __future__ import annotations

import math
import pathlib
from typing import Any

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from rocketforge.engine.propulsion_system.records import Branch, StudyResult

__all__ = ["SystemStudyController", "choice_field", "number_field", "parse_number",
           "text_field"]


def parse_number(text: str) -> tuple[bool, float | None]:
    """``(accepted, value)``. Empty text clears; text that is not a finite
    number is ignored, as on the Liquid Engine pages."""
    text = str(text).strip()
    if not text:
        return True, None
    try:
        value = float(text)
    except ValueError:
        return False, None
    return math.isfinite(value), value


def _text(value: float | None, scale: float) -> str:
    return "" if value is None else f"{value / scale:.12g}"


def number_field(key: str, label: str, unit: str, value: float | None, scale: float = 1.0,
                 visible: bool = True, note: str = "") -> dict[str, Any]:
    """A number typed in its display unit; ``value`` is SI and ``scale`` is
    SI per display unit."""
    return {"key": key, "label": label, "kind": "number", "unit": unit,
            "text": _text(value, scale), "visible": visible, "note": note,
            "options": [], "value": ""}


def choice_field(key: str, label: str, options: list[tuple[str, str]], value: str,
                 visible: bool = True, note: str = "") -> dict[str, Any]:
    return {"key": key, "label": label, "kind": "choice", "unit": "", "text": "",
            "visible": visible, "note": note,
            "options": [{"key": k, "label": text} for k, text in options], "value": value}


def text_field(key: str, label: str, text: str, visible: bool = True,
               note: str = "") -> dict[str, Any]:
    return {"key": key, "label": label, "kind": "text", "unit": "", "text": text,
            "visible": visible, "note": note, "options": [], "value": ""}


def _branch(key: str) -> Branch | None:
    try:
        return Branch(str(key))
    except ValueError:
        return None


class SystemStudyController(QObject):
    """Application-side facade shared by the SYS pages."""

    settingsChanged = Signal()
    resultChanged = Signal()

    #: What the empty result panel says, per gate.
    computed_word = "Computed"

    def __init__(self, sources: tuple[QObject, ...], parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._sources = sources
        self._result: StudyResult | None = None
        self._message = ""
        for source in sources:
            source.resultChanged.connect(self._on_inputs_changed)

    # -- what a gate supplies -------------------------------------------------

    def _basis(self):                       # -> (basis | None, issues)
        raise NotImplementedError

    def _build(self, basis):                # -> (definition | None, issues)
        raise NotImplementedError

    def _solve(self, definition) -> StudyResult:
        raise NotImplementedError

    def _sections(self, basis) -> list[dict[str, Any]]:
        raise NotImplementedError

    def _apply_number(self, branch: Branch | None, name: str, value: float | None) -> bool:
        return False

    def _apply_choice(self, branch: Branch | None, name: str, value: str) -> bool:
        return False

    def _apply_text(self, branch: Branch | None, name: str, text: str) -> bool:
        return False

    def _apply_action(self, branch: Branch | None, name: str, argument: str) -> bool:
        return False

    def _basis_rows(self, basis) -> list[dict[str, str]]:
        return []

    def _branch_view(self, outcome) -> dict[str, Any]:
        raise NotImplementedError

    def _total_rows(self, result: StudyResult) -> list[dict[str, str]]:
        return []

    def _computed_message(self, definition, result: StudyResult) -> str:
        return self.computed_word

    # -- inputs -------------------------------------------------------------

    def _definition(self):
        basis, issues = self._basis()
        if basis is None:
            return None, issues
        return self._build(basis)

    def _on_inputs_changed(self) -> None:
        # Announce only: nothing is computed here.
        self.settingsChanged.emit()
        self.resultChanged.emit()

    def _changed(self, changed: bool) -> None:
        if changed:
            self._on_inputs_changed()

    @staticmethod
    def _split(key: str) -> tuple[Branch | None, str] | None:
        head, _, name = str(key).partition(".")
        if not name:
            return None
        if head == "study":
            return None, name
        branch = _branch(head)
        return None if branch is None else (branch, name)

    @Slot(str, str)
    def setField(self, key: str, text: str) -> None:
        """A number, typed in its display unit."""
        target = self._split(key)
        ok, value = parse_number(text)
        if target is not None and ok:
            self._changed(self._apply_number(target[0], target[1], value))

    @Slot(str, str)
    def setChoice(self, key: str, value: str) -> None:
        target = self._split(key)
        if target is not None:
            self._changed(self._apply_choice(target[0], target[1], str(value)))

    @Slot(str, str)
    def setText(self, key: str, text: str) -> None:
        target = self._split(key)
        if target is not None:
            self._changed(self._apply_text(target[0], target[1], str(text)))

    @Slot(str, str)
    def invoke(self, key: str, argument: str) -> None:
        """A list action: add or remove a row."""
        target = self._split(key)
        if target is not None:
            self._changed(self._apply_action(target[0], target[1], str(argument)))

    @Property("QVariantList", notify=settingsChanged)
    def inputSections(self):
        basis, _ = self._basis()
        return self._sections(basis)

    @Property(bool, notify=settingsChanged)
    def hasBasis(self) -> bool:
        return self._basis()[0] is not None

    @Property("QVariantList", notify=settingsChanged)
    def basisRows(self):
        basis, _ = self._basis()
        return [] if basis is None else self._basis_rows(basis)

    @Property("QVariantList", notify=settingsChanged)
    def issues(self):
        _, issues = self._definition()
        return [{"code": i.code, "field": i.field, "message": i.message} for i in issues]

    @Property(bool, notify=settingsChanged)
    def canCompute(self) -> bool:
        return self._definition()[0] is not None

    # -- computing ----------------------------------------------------------

    @Slot()
    def compute(self) -> None:
        """The only entry point that computes."""
        definition, issues = self._definition()
        if definition is None:
            self._message = issues[0].message if issues else "The study is not defined."
            self.resultChanged.emit()
            return
        self._result = self._solve(definition)
        self._message = (self._computed_message(definition, self._result)
                         if self._result.ok else self._result.message)
        self.settingsChanged.emit()
        self.resultChanged.emit()

    # -- results ------------------------------------------------------------

    def result(self) -> StudyResult | None:
        return self._result

    @Property(bool, notify=resultChanged)
    def hasResult(self) -> bool:
        return self._result is not None

    @Property(bool, notify=resultChanged)
    def resultStale(self) -> bool:
        if self._result is None:
            return False
        definition, _ = self._definition()
        return (definition is None
                or definition.fingerprint != self._result.definition.fingerprint)

    @Property(bool, notify=resultChanged)
    def resultOk(self) -> bool:
        return self._result is not None and self._result.ok

    @Property(str, notify=resultChanged)
    def statusLabel(self) -> str:
        if self._result is None:
            return "Not computed"
        if self.resultStale:
            return "Stale — compute again"
        return {"ok": "Computed", "incomplete": "Computed · incomplete",
                "warning": "Computed with advisories",
                "refused": "Refused"}[self._result.status.value]

    @Property(str, notify=resultChanged)
    def statusTone(self) -> str:
        if self._result is None:
            return "neutral"
        if self.resultStale or self._result.status.value != "ok":
            return "warning"
        return "success"

    @Property(str, notify=resultChanged)
    def message(self) -> str:
        return self._message

    @Property("QVariantList", notify=resultChanged)
    def resultBranches(self):
        if self._result is None:
            return []
        views = []
        for outcome, title in ((self._result.oxidiser, "Oxidiser"),
                               (self._result.fuel, "Fuel")):
            view = {"branch": outcome.branch.value, "title": title, "ok": outcome.ok,
                    "message": outcome.message, "groups": [], "ledger": [], "labels": [],
                    "series": {"headers": [], "rows": []}}
            view.update(self._branch_view(outcome))
            views.append(view)
        return views

    @Property("QVariantList", notify=resultChanged)
    def totalRows(self):
        return [] if self._result is None else self._total_rows(self._result)

    @Property("QVariantList", notify=resultChanged)
    def noteRows(self):
        if self._result is None:
            return []
        return list(self._result.oxidiser.notes + self._result.fuel.notes)

    @Property("QVariantList", notify=resultChanged)
    def modelAssumptions(self):
        return [] if self._result is None else list(self._result.assumptions)

    @Property("QVariantList", notify=resultChanged)
    def provenanceRows(self):
        if self._result is None:
            return []
        return [{"label": k, "value": v} for k, v in self._result.provenance.items() if v]

    @Property(str, notify=resultChanged)
    def resultJson(self) -> str:
        return "" if self._result is None else self._result.to_json()

    @Slot(str, result=bool)
    def saveResult(self, location: str) -> bool:
        if self._result is None:
            return False
        url = QUrl(str(location))
        path = pathlib.Path(url.toLocalFile() if url.isLocalFile() else str(location))
        try:
            path.write_text(self._result.to_json(), encoding="utf-8")
        except OSError as error:
            self._message = f"Not saved: {error}"
            self.resultChanged.emit()
            return False
        return True
