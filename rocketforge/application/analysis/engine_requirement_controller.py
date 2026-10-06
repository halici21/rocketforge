"""The QObject the Engine Requirement page binds to.

Holds one immutable :class:`EngineRequirement` and republishes it as display
values. Every setter replaces the requirement and emits one signal; **none of
them solves anything**, because there is nothing to solve -- a requirement is
intent, and the LIQ-2 gate deliberately stops before sizing, trading or cycle
analysis. No provider, physics or engineering function is called from here.

Persistence is the requirement's own JSON record: ``stateJson`` publishes it,
:meth:`loadStateJson` reads one back, and the clipboard and file slots move
that text. Reading never repairs a record; an inconsistent one loads as
written and its issues are shown.
"""

from __future__ import annotations

import math
import pathlib

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication

from rocketforge.engine.requirement import (
    AmbientMode,
    ChamberPressureMode,
    ChamberPressurePreference,
    CyclePreference,
    DesignEnvironment,
    DesignPriority,
    EngineRequirement,
    FeedArchitecture,
    MixtureRatioMode,
    MixtureRatioPreference,
    PropellantMode,
    PropellantPreference,
    RequirementFormatError,
)

from . import engine_requirement_service as service

__all__ = ["EngineRequirementController"]


def _text(quantity: str, value: float | None) -> str:
    """A stored SI value as the form's display text; empty when not stated."""
    shown = service.to_display(quantity, value)
    if shown is None:
        return ""
    return f"{shown:.12g}"


def _parse(text: str) -> tuple[bool, float | None]:
    """``(ok, value)`` for what a field holds. Empty text means "not stated"."""
    text = str(text).strip()
    if not text:
        return True, None
    try:
        value = float(text)
    except ValueError:
        return False, None
    return (math.isfinite(value), value)


class EngineRequirementController(QObject):
    """Application-side facade for the Engine Requirement page."""

    requirementChanged = Signal()
    messageChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._requirement = service.DEFAULT_REQUIREMENT
        self._message = ""

    # -- the requirement itself (Python side) --------------------------------

    def requirement(self) -> EngineRequirement:
        return self._requirement

    def set_requirement(self, requirement: EngineRequirement) -> None:
        if requirement == self._requirement:
            return
        self._requirement = requirement
        self.requirementChanged.emit()

    def _update(self, **changes) -> None:
        self.set_requirement(self._requirement.replace(**changes))

    def _say(self, message: str) -> None:
        if message != self._message:
            self._message = message
            self.messageChanged.emit()

    # -- vocabulary ---------------------------------------------------------

    @Property("QVariantList", constant=True)
    def ambientOptions(self):
        return list(service.AMBIENT_OPTIONS)

    @Property("QVariantList", constant=True)
    def chamberPressureOptions(self):
        return list(service.CHAMBER_PRESSURE_OPTIONS)

    @Property("QVariantList", constant=True)
    def mixtureRatioOptions(self):
        return list(service.MIXTURE_RATIO_OPTIONS)

    @Property("QVariantList", constant=True)
    def feedOptions(self):
        return list(service.FEED_OPTIONS)

    @Property("QVariantList", constant=True)
    def cycleOptions(self):
        return list(service.CYCLE_OPTIONS)

    @Property("QVariantList", constant=True)
    def priorityOptions(self):
        return list(service.PRIORITY_OPTIONS)

    @Property("QVariantList", constant=True)
    def pairOptions(self):
        """Executable catalogue pairs, in source order. Choosing one is the
        only way a pair enters the requirement."""
        return [option for option in service.pair_options() if option["executable"]]

    @Property("QVariantList", constant=True)
    def blockedPairs(self):
        return [option for option in service.pair_options() if not option["executable"]]

    @Property(str, constant=True)
    def pairNote(self) -> str:
        """The catalogue's source, and which of its pairs are withheld."""
        return service.presets.catalogue_note()

    @Property(str, constant=True)
    def scopeNote(self) -> str:
        return service.SCOPE_NOTE

    @Property("QVariantMap", constant=True)
    def units(self):
        return {key: spec["unit"] for key, spec in service.UNITS.items()}

    # -- fields -------------------------------------------------------------

    @Property(str, notify=requirementChanged)
    def name(self) -> str:
        return self._requirement.name

    @Slot(str)
    def setName(self, value: str) -> None:
        self._update(name=str(value).strip())

    @Property(str, notify=requirementChanged)
    def thrustText(self) -> str:
        return _text("thrust", self._requirement.thrust)

    @Slot(str)
    def setThrust(self, text: str) -> None:
        ok, value = _parse(text)
        if ok:
            self._update(thrust=service.from_display("thrust", value))

    @Property(str, notify=requirementChanged)
    def burnTimeText(self) -> str:
        return _text("burn_time", self._requirement.burn_time)

    @Slot(str)
    def setBurnTime(self, text: str) -> None:
        ok, value = _parse(text)
        if ok:
            self._update(burn_time=service.from_display("burn_time", value))

    @Property(str, notify=requirementChanged)
    def ambientMode(self) -> str:
        return self._requirement.environment.mode.value

    @Slot(str)
    def setAmbientMode(self, mode: str) -> None:
        try:
            mode = AmbientMode(str(mode))
        except ValueError:
            return
        environment = self._requirement.environment
        self._update(environment=DesignEnvironment(mode, environment.custom_pressure))

    @Property(str, notify=requirementChanged)
    def ambientPressureText(self) -> str:
        """The ambient pressure the form shows: the custom value in Custom
        mode, otherwise the named pressure the mode stands for."""
        environment = self._requirement.environment
        return _text("ambient_pressure", environment.ambient_pressure)

    @Slot(str)
    def setAmbientPressure(self, text: str) -> None:
        ok, value = _parse(text)
        if not ok or value is None:
            return
        self._update(environment=DesignEnvironment(
            AmbientMode.CUSTOM, service.from_display("ambient_pressure", value)))

    @Property(str, notify=requirementChanged)
    def pairKey(self) -> str:
        """The chosen pair's key, or empty while the pair is Auto."""
        propellant = self._requirement.propellant
        return propellant.pair_key if propellant.is_explicit else ""

    @Slot(str)
    def setPair(self, key: str) -> None:
        """Choose one catalogue pair; an empty key leaves the pair open."""
        key = str(key)
        if not key:
            # A pair-reference O/F is kept as chosen and reported as an issue
            # rather than silently reset: the user decides what replaces it.
            self._update(propellant=PropellantPreference())
            return
        self._update(propellant=PropellantPreference(PropellantMode.EXPLICIT, key))

    @Property(str, notify=requirementChanged)
    def pairLabel(self) -> str:
        preset = service.resolved_pair(self._requirement)
        return preset.label if preset is not None else ""

    @Property(str, notify=requirementChanged)
    def chamberPressureMode(self) -> str:
        return self._requirement.chamber_pressure.mode.value

    @Slot(str)
    def setChamberPressureMode(self, mode: str) -> None:
        try:
            mode = ChamberPressureMode(str(mode))
        except ValueError:
            return
        current = self._requirement.chamber_pressure
        value = None if mode is ChamberPressureMode.AUTO else current.value
        self._update(chamber_pressure=ChamberPressurePreference(mode, value))

    @Property(str, notify=requirementChanged)
    def chamberPressureText(self) -> str:
        return _text("chamber_pressure", self._requirement.chamber_pressure.value)

    @Slot(str)
    def setChamberPressure(self, text: str) -> None:
        ok, value = _parse(text)
        current = self._requirement.chamber_pressure
        if not ok or current.mode is ChamberPressureMode.AUTO:
            return
        self._update(chamber_pressure=ChamberPressurePreference(
            current.mode, service.from_display("chamber_pressure", value)))

    @Property(str, notify=requirementChanged)
    def mixtureRatioMode(self) -> str:
        return self._requirement.mixture_ratio.mode.value

    @Slot(str)
    def setMixtureRatioMode(self, mode: str) -> None:
        try:
            mode = MixtureRatioMode(str(mode))
        except ValueError:
            return
        if (mode is MixtureRatioMode.PAIR_REFERENCE
                and not self._requirement.propellant.is_explicit):
            return
        value = (self._requirement.mixture_ratio.value
                 if mode is MixtureRatioMode.EXPLICIT else None)
        self._update(mixture_ratio=MixtureRatioPreference(mode, value))

    @Property(str, notify=requirementChanged)
    def mixtureRatioText(self) -> str:
        value = self._requirement.mixture_ratio.value
        return "" if value is None else f"{value:.12g}"

    @Slot(str)
    def setMixtureRatio(self, text: str) -> None:
        ok, value = _parse(text)
        if not ok or self._requirement.mixture_ratio.mode is not MixtureRatioMode.EXPLICIT:
            return
        self._update(mixture_ratio=MixtureRatioPreference(MixtureRatioMode.EXPLICIT, value))

    @Property(str, notify=requirementChanged)
    def referenceMixtureRatioText(self) -> str:
        """The catalogue O/F a pair reference points at, read now, or empty."""
        value = service.reference_mixture_ratio(self._requirement)
        return "" if value is None else f"{value:g}"

    @Property(str, notify=requirementChanged)
    def feed(self) -> str:
        return self._requirement.feed.value

    @Slot(str)
    def setFeed(self, feed: str) -> None:
        try:
            feed = FeedArchitecture(str(feed))
        except ValueError:
            return
        self.set_requirement(self._requirement.with_feed(feed))

    @Property(bool, notify=requirementChanged)
    def cycleApplicable(self) -> bool:
        return self._requirement.feed is FeedArchitecture.PUMP_FED

    @Property(str, notify=requirementChanged)
    def cycle(self) -> str:
        cycle = self._requirement.cycle
        return "" if cycle is None else cycle.value

    @Slot(str)
    def setCycle(self, cycle: str) -> None:
        """Only a pump-fed engine takes a cycle; anything else is refused here
        rather than recorded and flagged."""
        if self._requirement.feed is not FeedArchitecture.PUMP_FED:
            return
        try:
            self._update(cycle=CyclePreference(str(cycle)))
        except ValueError:
            return

    @Property(str, notify=requirementChanged)
    def cycleNote(self) -> str:
        cycle = self._requirement.cycle
        if cycle is None:
            return ""
        for option in service.CYCLE_OPTIONS:
            if option["key"] == cycle.value:
                return option["note"]
        return ""

    @Property(str, notify=requirementChanged)
    def priority(self) -> str:
        return self._requirement.priority.value

    @Slot(str)
    def setPriority(self, priority: str) -> None:
        try:
            self._update(priority=DesignPriority(str(priority)))
        except ValueError:
            return

    # -- state --------------------------------------------------------------

    @Property("QVariantList", notify=requirementChanged)
    def issues(self):
        return [{"code": issue.code, "field": issue.field, "message": issue.message}
                for issue in service.requirement_issues(self._requirement)]

    @Property(bool, notify=requirementChanged)
    def isComplete(self) -> bool:
        return not service.requirement_issues(self._requirement)

    @Property("QVariantList", notify=requirementChanged)
    def openDecisions(self):
        return service.open_decision_labels(self._requirement)

    @Property("QVariantList", notify=requirementChanged)
    def summaryRows(self):
        return service.summary_rows(self._requirement)

    @Property(str, notify=requirementChanged)
    def statusLabel(self) -> str:
        count = len(service.requirement_issues(self._requirement))
        if count == 0:
            return "Requirement complete"
        return f"{count} item{'s' if count != 1 else ''} to resolve"

    @Property(str, notify=requirementChanged)
    def fingerprint(self) -> str:
        return self._requirement.fingerprint[:12]

    @Property(str, notify=messageChanged)
    def message(self) -> str:
        return self._message

    # -- persistence ----------------------------------------------------------

    @Property(str, notify=requirementChanged)
    def stateJson(self) -> str:
        return self._requirement.to_json()

    @Slot(str, result=bool)
    def loadStateJson(self, text: str) -> bool:
        """Adopt a serialised requirement. A malformed one changes nothing."""
        try:
            requirement = EngineRequirement.from_json(str(text))
        except RequirementFormatError as error:
            self._say(f"Not loaded: {error}")
            return False
        self.set_requirement(requirement)
        self._say("Requirement loaded")
        return True

    @Slot()
    def reset(self) -> None:
        self.set_requirement(service.DEFAULT_REQUIREMENT)
        self._say("")

    @Slot()
    def copyToClipboard(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._requirement.to_json())
            self._say("Requirement copied as JSON")

    @Slot(result=bool)
    def pasteFromClipboard(self) -> bool:
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return False
        return self.loadStateJson(clipboard.text())

    @staticmethod
    def _path(location: str) -> pathlib.Path:
        url = QUrl(str(location))
        if url.isLocalFile():
            return pathlib.Path(url.toLocalFile())
        return pathlib.Path(str(location))

    @Slot(str, result=bool)
    def saveToFile(self, location: str) -> bool:
        path = self._path(location)
        try:
            path.write_text(self._requirement.to_json(), encoding="utf-8")
        except OSError as error:
            self._say(f"Not saved: {error}")
            return False
        self._say(f"Saved to {path.name}")
        return True

    @Slot(str, result=bool)
    def loadFromFile(self, location: str) -> bool:
        path = self._path(location)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            self._say(f"Not loaded: {error}")
            return False
        return self.loadStateJson(text)
