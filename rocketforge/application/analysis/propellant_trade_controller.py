"""The QObject the Propellant Trade page binds to (LIQ-3).

It reads the current LIQ-2 requirement from the Engine Requirement controller,
holds the user's study settings, and runs a trade **only** from
:meth:`runTrade`. Opening the page, editing a setting, sorting, selecting a
row or changing the requirement never solves and never probes the provider:
editing marks an existing result stale, nothing more.

Execution is serial: one candidate per event-loop turn on a zero-interval
timer, the same pattern the Trade Study workspace uses, so the interface stays
responsive without a concurrent provider call.

Selecting a candidate is the user's act. :meth:`applySelectionToRequirement`
writes the chosen pair -- and the operating values this study stated where the
requirement had left them open -- back into the Engine Requirement, which is
how the choice reaches the next design stage.
"""

from __future__ import annotations

import math
import pathlib

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot

from rocketforge.engine.propellant_trade import (
    TRADE_METRICS,
    CandidateResult,
    MixtureRatioSource,
    PerformanceBasis,
    PressureSource,
    TradeDefinition,
    TradeResult,
)
from rocketforge.engine.requirement import (
    ChamberPressureMode,
    ChamberPressurePreference,
    MixtureRatioMode,
    MixtureRatioPreference,
    PropellantMode,
    PropellantPreference,
)

from . import environment_service
from . import propellant_trade_service as service

__all__ = ["PropellantTradeController"]

_PRESSURE_SCALE = 1.0e6          # the form's chamber pressure is in MPa

# Two tables, not one: the enumerations share string values ("study",
# "requirement"), so one dict keyed by both would silently merge them.
_PRESSURE_SOURCE_TEXT = {
    PressureSource.REQUIREMENT: "requirement target",
    PressureSource.STUDY: "stated for this study",
}
_RATIO_SOURCE_TEXT = {
    MixtureRatioSource.REQUIREMENT: "requirement, every candidate",
    MixtureRatioSource.CATALOGUE: "each candidate's catalogue O/F",
    MixtureRatioSource.STUDY: "stated for this study, every candidate",
}


def _parse(text: str) -> tuple[bool, float | None]:
    text = str(text).strip()
    if not text:
        return True, None
    try:
        value = float(text)
    except ValueError:
        return False, None
    return math.isfinite(value), value


class PropellantTradeController(QObject):
    """Application-side facade for the Propellant Trade page."""

    settingsChanged = Signal()
    resultChanged = Signal()
    progressChanged = Signal()

    def __init__(self, requirement_source, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._source = requirement_source
        self._settings = service.TradeSettings()
        self._result: TradeResult | None = None
        self._stale = False
        self._message = ""
        self._sort_key = ""
        self._descending = True
        self._busy = False
        self._pending: list[str] = []
        self._done: list[CandidateResult] = []
        self._running: TradeDefinition | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self._advance)
        requirement_source.requirementChanged.connect(self._on_inputs_changed)

    # -- inputs -------------------------------------------------------------

    def _requirement(self):
        return self._source.requirement()

    def _definition(self):
        return service.build_definition(self._requirement(), self._settings)

    def settings(self) -> service.TradeSettings:
        return self._settings

    def _set(self, **changes) -> None:
        settings = self._settings.replace(**changes)
        if settings == self._settings:
            return
        self._settings = settings
        self._on_inputs_changed()

    def _on_inputs_changed(self) -> None:
        if self._result is not None:
            definition, _ = self._definition()
            self._stale = (definition is None
                           or definition.fingerprint != self._result.definition.fingerprint)
        self.settingsChanged.emit()
        self.resultChanged.emit()

    @Property("QVariantList", notify=settingsChanged)
    def candidateLabels(self):
        """What a run would evaluate. From the catalogue; nothing is solved."""
        keys = service.candidate_keys(self._requirement())
        return [service.presets.preset_named(key).label for key in keys]

    @Property(bool, notify=settingsChanged)
    def pressureNeeded(self) -> bool:
        return service.operating_needs(self._requirement())["chamber_pressure"]

    @Property(bool, notify=settingsChanged)
    def ratioNeeded(self) -> bool:
        return service.operating_needs(self._requirement())["mixture_ratio"]

    @Property(str, notify=settingsChanged)
    def studyPressureText(self) -> str:
        value = self._settings.chamber_pressure
        return "" if value is None else f"{value / _PRESSURE_SCALE:.12g}"

    @Slot(str)
    def setStudyPressure(self, text: str) -> None:
        ok, value = _parse(text)
        if ok:
            self._set(chamber_pressure=None if value is None else value * _PRESSURE_SCALE)

    @Property(str, notify=settingsChanged)
    def ratioMode(self) -> str:
        return self._settings.mixture_ratio_mode

    @Slot(str)
    def setRatioMode(self, mode: str) -> None:
        if mode in ("", "catalogue", "explicit"):
            self._set(mixture_ratio_mode=mode)

    @Property(str, notify=settingsChanged)
    def studyRatioText(self) -> str:
        value = self._settings.mixture_ratio
        return "" if value is None else f"{value:.12g}"

    @Slot(str)
    def setStudyRatio(self, text: str) -> None:
        ok, value = _parse(text)
        if ok:
            self._set(mixture_ratio=value)

    @Property(str, notify=settingsChanged)
    def performanceBasis(self) -> str:
        return self._settings.performance_basis.value

    @Slot(str)
    def setPerformanceBasis(self, basis: str) -> None:
        try:
            self._set(performance_basis=PerformanceBasis(str(basis)))
        except ValueError:
            return

    @Property(str, notify=settingsChanged)
    def areaRatioText(self) -> str:
        value = self._settings.area_ratio
        return "" if value is None else f"{value:.12g}"

    @Slot(str)
    def setAreaRatio(self, text: str) -> None:
        ok, value = _parse(text)
        if ok:
            self._set(area_ratio=value)

    @Property(str, notify=settingsChanged)
    def gammaBasis(self) -> str:
        return self._settings.gamma_basis

    @Slot(str)
    def setGammaBasis(self, basis: str) -> None:
        if basis in service.GAMMA_BASES:
            self._set(gamma_basis=basis)

    @Property("QVariantList", notify=settingsChanged)
    def issues(self):
        _, issues = self._definition()
        return [{"code": i.code, "field": i.field, "message": i.message} for i in issues]

    @Property(bool, notify=settingsChanged)
    def canRun(self) -> bool:
        definition, _ = self._definition()
        return definition is not None and not self._busy

    @Property(str, notify=settingsChanged)
    def ambientText(self) -> str:
        pressure = environment_service.ambient_pressure(self._requirement().environment)
        return f"{pressure / 1.0e3:g} kPa (design environment)"

    # -- running ------------------------------------------------------------

    @Property(bool, notify=progressChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=progressChanged)
    def progressText(self) -> str:
        if not self._busy or self._running is None:
            return ""
        return f"{len(self._done)} of {len(self._running.candidates)} candidates"

    @Slot()
    def runTrade(self) -> None:
        """The only entry point that solves. Serial, one candidate per turn."""
        if self._busy:
            return
        definition, issues = self._definition()
        if definition is None:
            self._message = issues[0].message if issues else "The trade is not defined."
            self.resultChanged.emit()
            return
        from .thermochemistry_provider import availability

        state = availability()
        if not state.usable:
            self._message = ("No thermochemistry provider is available in this "
                             f"build: {state.detail}".rstrip(": "))
            self.resultChanged.emit()
            return
        self._running = definition
        self._pending = list(definition.candidates)
        self._done = []
        self._busy = True
        self._message = ""
        self.progressChanged.emit()
        self.settingsChanged.emit()
        self._timer.start()

    def _advance(self) -> None:
        if not self._pending or self._running is None:
            self._finish()
            return
        key = self._pending.pop(0)
        self._done.append(service.evaluate_candidate(self._running, key))
        self.progressChanged.emit()
        if not self._pending:
            self._finish()

    def _finish(self) -> None:
        self._timer.stop()
        definition, self._running = self._running, None
        self._busy = False
        if definition is not None:
            self._result = service.assemble_result(definition, tuple(self._done))
            self._stale = False
            failed = sum(1 for c in self._result.candidates if not c.ok)
            self._message = (f"{len(self._result.candidates)} evaluated"
                             + (f", {failed} failed" if failed else ""))
        self._done = []
        self.progressChanged.emit()
        self.settingsChanged.emit()
        self.resultChanged.emit()

    def run_to_completion(self) -> None:
        """Drain a started run synchronously. For tests and harnesses."""
        while self._busy:
            self._advance()

    # -- results ------------------------------------------------------------

    def result(self) -> TradeResult | None:
        return self._result

    @Property(bool, notify=resultChanged)
    def hasResult(self) -> bool:
        return self._result is not None

    @Property(bool, notify=resultChanged)
    def resultStale(self) -> bool:
        return self._stale

    @Property(str, notify=resultChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=resultChanged)
    def statusLabel(self) -> str:
        if self._result is None:
            return "Not run"
        return "Stale — run again" if self._stale else "Evaluated"

    @Property("QVariantList", constant=True)
    def metricColumns(self):
        return [{"key": m.key, "label": m.label, "unit": service.DISPLAY[m.key][0],
                 "tier": m.tier, "note": m.note} for m in TRADE_METRICS]

    @Property(str, notify=resultChanged)
    def sortKey(self) -> str:
        return self._sort_key

    @Property(bool, notify=resultChanged)
    def sortDescending(self) -> bool:
        return self._descending

    @Slot(str)
    def sortBy(self, key: str) -> None:
        """Order rows by one displayed metric; again to reverse; empty for
        catalogue order. A view only -- the result is unchanged."""
        key = str(key)
        if key == self._sort_key and key:
            self._descending = not self._descending
        else:
            self._sort_key, self._descending = key, True
        self.resultChanged.emit()

    @Property("QVariantList", notify=resultChanged)
    def rows(self):
        if self._result is None:
            return []
        return service.table_rows(self._result, self._sort_key, self._descending)

    @Property("QVariantList", notify=resultChanged)
    def assumptionRows(self):
        """The operating point and basis every row was computed at, with sources."""
        if self._result is None:
            return []
        d = self._result.definition
        r = d.requirement
        ratio = ("per candidate" if d.mixture_ratio is None else f"{d.mixture_ratio:g}")
        nozzle = ("none stated: chamber quantities only"
                  if d.area_ratio is None
                  else f"ideal, Ae/At {d.area_ratio:g}, single gamma (chamber, {d.gamma_basis})")
        flow = ("unresolved without a nozzle" if d.area_ratio is None
                else f"F {r.thrust / 1.0e3:g} kN, t_b {r.burn_time:g} s")
        return [
            {"label": "Chamber pressure",
             "value": f"{d.chamber_pressure / 1.0e6:g} MPa · "
                      f"{_PRESSURE_SOURCE_TEXT[d.pressure_source]}"},
            {"label": "O/F", "value": f"{ratio} · {_RATIO_SOURCE_TEXT[d.mixture_ratio_source]}"},
            {"label": "Design ambient",
             "value": f"{environment_service.ambient_pressure(r.environment) / 1.0e3:g} kPa · requirement"},
            {"label": "Nozzle basis", "value": nozzle},
            {"label": "c* gas reduction", "value": f"single gamma, {d.gamma_basis} basis"},
            {"label": "Mass flow basis", "value": flow},
            {"label": "Reactants", "value": "each at its catalogue reference temperature"},
            {"label": "Feed / cycle",
             "value": f"{r.feed.value} / {r.cycle.value if r.cycle else 'none'} · "
                      "intent only, not evaluated"},
        ]

    @Property("QVariantList", notify=resultChanged)
    def provenanceRows(self):
        if self._result is None:
            return []
        return [{"label": k, "value": v} for k, v in self._result.provenance.items()]

    @Property(str, notify=resultChanged)
    def resultJson(self) -> str:
        return "" if self._result is None else self._result.to_json()

    # -- selection ------------------------------------------------------------

    @Property(str, notify=resultChanged)
    def selectedKey(self) -> str:
        return "" if self._result is None else self._result.selected

    @Property(str, notify=resultChanged)
    def selectedLabel(self) -> str:
        if self._result is None or not self._result.selected:
            return ""
        candidate = self._result.candidate(self._result.selected)
        return f"{candidate.label}, O/F {candidate.oxidiser_fuel_ratio:g}"

    @Slot(str, result=bool)
    def selectCandidate(self, key: str) -> bool:
        """Choose one successful candidate. Empty clears the choice."""
        if self._result is None:
            return False
        try:
            self._result = self._result.with_selection(str(key))
        except ValueError:
            return False
        self.resultChanged.emit()
        return True

    @Slot(result=bool)
    def applySelectionToRequirement(self) -> bool:
        """Write the chosen pair and the study's stated operating values into
        the Engine Requirement. Refused on a stale result: a choice made
        against another requirement is not carried over."""
        result = self._result
        if result is None or not result.selected or self._stale:
            return False
        d = result.definition
        candidate = result.candidate(result.selected)
        requirement = self._requirement()
        changes = {"propellant": PropellantPreference(PropellantMode.EXPLICIT, candidate.key)}
        if d.mixture_ratio_source is MixtureRatioSource.CATALOGUE:
            if requirement.mixture_ratio.mode is MixtureRatioMode.AUTO:
                changes["mixture_ratio"] = MixtureRatioPreference(
                    MixtureRatioMode.PAIR_REFERENCE)
        elif d.mixture_ratio_source is MixtureRatioSource.STUDY:
            changes["mixture_ratio"] = MixtureRatioPreference(
                MixtureRatioMode.EXPLICIT, d.mixture_ratio)
        if (d.pressure_source is PressureSource.STUDY
                and requirement.chamber_pressure.mode is ChamberPressureMode.AUTO):
            changes["chamber_pressure"] = ChamberPressurePreference(
                ChamberPressureMode.TARGET, d.chamber_pressure)
        self._source.set_requirement(requirement.replace(**changes))
        self._message = f"{candidate.label} applied to the Engine Requirement"
        self.resultChanged.emit()
        return True

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
