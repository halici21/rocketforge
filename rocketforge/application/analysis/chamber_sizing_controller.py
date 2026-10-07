"""The QObject the Thrust Chamber Sizing page binds to (LIQ-4).

It reads the candidate selected in the Propellant Trade controller, holds the
one sizing input the user states (the area ratio), and sizes **only** from
:meth:`runSizing`. Opening the page, editing the area ratio, a change in the
trade or the requirement never solves and never probes the provider: a change
upstream only re-announces this controller's state, and a sizing whose
question has moved is reported stale when it is next read.
"""

from __future__ import annotations

import math
import pathlib

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from rocketforge.engine.chamber_sizing import AreaRatioSource, SizingResult

from . import chamber_sizing_service as service

__all__ = ["ChamberSizingController"]

_PRESSURE_SOURCE_TEXT = {"requirement": "requirement target", "study": "stated in the trade"}
_RATIO_SOURCE_TEXT = {"requirement": "requirement", "catalogue": "catalogue O/F of the pair",
                      "study": "stated in the trade"}
_AREA_SOURCE_TEXT = {AreaRatioSource.TRADE: "the trade's nozzle",
                     AreaRatioSource.SIZING: "stated for this sizing"}


class ChamberSizingController(QObject):
    """Application-side facade for the Thrust Chamber Sizing page."""

    settingsChanged = Signal()
    resultChanged = Signal()

    def __init__(self, trade_source, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._trade = trade_source
        self._settings = service.SizingSettings()
        self._result: SizingResult | None = None
        self._message = ""
        trade_source.resultChanged.connect(self._on_inputs_changed)

    # -- inputs -------------------------------------------------------------

    def _point(self):
        return service.operating_point(self._trade.result(),
                                       bool(self._trade.property("resultStale")))

    def _definition(self):
        point, issues = self._point()
        if point is None:
            return None, issues
        return service.build_definition(point, self._settings)

    def _on_inputs_changed(self) -> None:
        # Announce only. Nothing below the application layer is called here:
        # staleness is worked out when a binding reads it.
        self.settingsChanged.emit()
        self.resultChanged.emit()

    @Property(bool, notify=settingsChanged)
    def hasOperatingPoint(self) -> bool:
        return self._point()[0] is not None

    @Property("QVariantList", notify=settingsChanged)
    def operatingRows(self):
        """The selected LIQ-3 operating point, as the trade resolved it."""
        point, _ = self._point()
        return [] if point is None else _point_rows(point)

    @Property(str, notify=settingsChanged)
    def areaRatioText(self) -> str:
        value = self._settings.area_ratio
        return "" if value is None else f"{value:.12g}"

    @Slot(str)
    def setAreaRatio(self, text: str) -> None:
        text = str(text).strip()
        if text:
            try:
                value = float(text)
            except ValueError:
                return
            if not math.isfinite(value):
                return
        else:
            value = None
        settings = service.SizingSettings(area_ratio=value)
        if settings != self._settings:
            self._settings = settings
            self._on_inputs_changed()

    @Property(str, notify=settingsChanged)
    def tradeAreaRatioText(self) -> str:
        point, _ = self._point()
        if point is None:
            return ""
        if point.trade_area_ratio is None:
            return "The trade was chamber-only: state Ae/At to size at."
        return (f"Empty: the trade's Ae/At {point.trade_area_ratio:g}. "
                "A stated value is used instead.")

    @Property("QVariantList", notify=settingsChanged)
    def issues(self):
        _, issues = self._definition()
        return [{"code": i.code, "field": i.field, "message": i.message} for i in issues]

    @Property(bool, notify=settingsChanged)
    def canSize(self) -> bool:
        return self._definition()[0] is not None

    # -- running ------------------------------------------------------------

    @Slot()
    def runSizing(self) -> None:
        """The only entry point that solves: one chamber solve, then algebra."""
        definition, issues = self._definition()
        if definition is None:
            self._message = issues[0].message if issues else "The sizing is not defined."
            self.resultChanged.emit()
            return
        from .thermochemistry_provider import availability

        state = availability()
        if not state.usable:
            self._message = ("No thermochemistry provider is available in this "
                             f"build: {state.detail}".rstrip(": "))
            self.resultChanged.emit()
            return
        self._result = service.solve_sizing(definition)
        self._message = (f"Sized: {definition.point.pair_label}, Ae/At "
                         f"{definition.area_ratio:g}" if self._result.ok
                         else self._result.message)
        self.settingsChanged.emit()
        self.resultChanged.emit()

    # -- results ------------------------------------------------------------

    def result(self) -> SizingResult | None:
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
            return "Not sized"
        if self.resultStale:
            return "Stale — size again"
        return {"ok": "Sized", "warning": "Sized with notes",
                "refused": "Refused"}[self._result.status.value]

    @Property(str, notify=resultChanged)
    def statusTone(self) -> str:
        if self._result is None:
            return "neutral"
        if self.resultStale or not self._result.ok:
            return "warning"
        return "success"

    @Property(str, notify=resultChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=resultChanged)
    def regime(self) -> str:
        return "" if self._result is None else self._result.regime.replace("_", " ")

    @Property("QVariantList", notify=resultChanged)
    def groups(self):
        return [] if self._result is None else service.quantity_groups(self._result)

    @Property("QVariantList", notify=resultChanged)
    def assumptionRows(self):
        """The basis every number was computed at, with its source."""
        if self._result is None:
            return []
        d = self._result.definition
        rows = _point_rows(d.point)
        rows.insert(rows.index(next(r for r in rows if r["label"] == "Design ambient")) + 1,
                    {"label": "Nozzle basis",
                     "value": f"ideal, Ae/At {d.area_ratio:g} · "
                              f"{_AREA_SOURCE_TEXT[d.area_ratio_source]}"})
        return rows

    @Property(str, notify=resultChanged)
    def nozzleBasisText(self) -> str:
        """The nozzle the result was sized at. The rest of its basis is the
        operating point, shown beside the inputs."""
        if self._result is None:
            return ""
        d = self._result.definition
        return f"ideal, Ae/At {d.area_ratio:g} · {_AREA_SOURCE_TEXT[d.area_ratio_source]}"

    @Property("QVariantList", notify=resultChanged)
    def noteRows(self):
        return [] if self._result is None else list(self._result.notes)

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


def _point_rows(point) -> list[dict[str, str]]:
    return [
        {"label": "Propellant", "value": f"{point.pair_label} · selected in the trade"},
        {"label": "O/F", "value": f"{point.oxidiser_fuel_ratio:g} · "
                                  f"{_RATIO_SOURCE_TEXT.get(point.mixture_ratio_source, '')}"},
        {"label": "Chamber pressure",
         "value": f"{point.chamber_pressure / 1.0e6:g} MPa · "
                  f"{_PRESSURE_SOURCE_TEXT.get(point.pressure_source, '')}"},
        {"label": "Target thrust", "value": f"{point.thrust / 1.0e3:g} kN · requirement"},
        {"label": "Design ambient",
         "value": f"{point.ambient_pressure / 1.0e3:g} kPa · requirement"},
        {"label": "Gamma basis", "value": f"single gamma, chamber, {point.gamma_basis} · trade"},
        {"label": "Reactants",
         "value": f"{point.oxidiser} {point.oxidiser_temperature:g} K, "
                  f"{point.fuel} {point.fuel_temperature:g} K · trade"},
        {"label": "Trade", "value": point.trade_fingerprint[:12]},
    ]
