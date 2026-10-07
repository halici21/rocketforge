"""The QObject the Combustion Chamber Geometry page binds to (LIQ-5).

It reads the accepted sizing in the Thrust Chamber Sizing controller, holds the
three geometry inputs the user states (L*, Ac/At, half-angle), and computes
**only** from :meth:`computeGeometry`. Opening the page, editing an input, or a
change in the sizing, the trade or the requirement never computes: a change
upstream only re-announces this controller's state, and a geometry whose
question has moved is reported stale when it is next read.
"""

from __future__ import annotations

import math
import pathlib

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from rocketforge.engine.chamber_geometry import GeometryResult

from . import chamber_geometry_service as service

__all__ = ["ChamberGeometryController"]


def _parse(text: str) -> tuple[bool, float | None]:
    """``(accepted, value)``. Empty text clears; text that is not a finite
    number is ignored, as in the other Liquid Engine pages."""
    text = str(text).strip()
    if not text:
        return True, None
    try:
        value = float(text)
    except ValueError:
        return False, None
    return math.isfinite(value), value


def _text(value: float | None) -> str:
    return "" if value is None else f"{value:.12g}"


class ChamberGeometryController(QObject):
    """Application-side facade for the Combustion Chamber Geometry page."""

    settingsChanged = Signal()
    resultChanged = Signal()

    def __init__(self, sizing_source, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._sizing = sizing_source
        self._settings = service.GeometrySettings()
        self._result: GeometryResult | None = None
        self._message = ""
        sizing_source.resultChanged.connect(self._on_inputs_changed)

    # -- inputs -------------------------------------------------------------

    def _basis(self):
        return service.throat_basis(self._sizing.result(),
                                    bool(self._sizing.property("resultStale")))

    def _definition(self):
        basis, issues = self._basis()
        if basis is None:
            return None, issues
        return service.build_definition(basis, self._settings)

    def _on_inputs_changed(self) -> None:
        # Announce only: nothing is computed here.
        self.settingsChanged.emit()
        self.resultChanged.emit()

    def _set(self, name: str, text: str) -> None:
        ok, value = _parse(text)
        if not ok:
            return
        from dataclasses import replace

        settings = replace(self._settings, **{name: value})
        if settings != self._settings:
            self._settings = settings
            self._on_inputs_changed()

    @Property(bool, notify=settingsChanged)
    def hasThroat(self) -> bool:
        return self._basis()[0] is not None

    @Property("QVariantList", notify=settingsChanged)
    def basisRows(self):
        """The LIQ-4 throat this geometry extends, as LIQ-4 sized it."""
        basis, _ = self._basis()
        return [] if basis is None else _basis_rows(basis)

    @Property(str, notify=settingsChanged)
    def characteristicLengthText(self) -> str:
        return _text(self._settings.characteristic_length)

    @Slot(str)
    def setCharacteristicLength(self, text: str) -> None:
        self._set("characteristic_length", text)

    @Property(str, notify=settingsChanged)
    def contractionRatioText(self) -> str:
        return _text(self._settings.contraction_ratio)

    @Slot(str)
    def setContractionRatio(self, text: str) -> None:
        self._set("contraction_ratio", text)

    @Property(str, notify=settingsChanged)
    def halfAngleText(self) -> str:
        return _text(self._settings.converging_half_angle_deg)

    @Slot(str)
    def setHalfAngle(self, text: str) -> None:
        self._set("converging_half_angle_deg", text)

    @Property("QVariantList", notify=settingsChanged)
    def issues(self):
        _, issues = self._definition()
        return [{"code": i.code, "field": i.field, "message": i.message} for i in issues]

    @Property(bool, notify=settingsChanged)
    def canCompute(self) -> bool:
        return self._definition()[0] is not None

    # -- computing ----------------------------------------------------------

    @Slot()
    def computeGeometry(self) -> None:
        """The only entry point that computes."""
        definition, issues = self._definition()
        if definition is None:
            self._message = issues[0].message if issues else "The geometry is not defined."
            self.resultChanged.emit()
            return
        self._result = service.solve_geometry(definition)
        self._message = ("Computed: L* "
                         f"{definition.characteristic_length:g} m, Ac/At "
                         f"{definition.contraction_ratio:g}, "
                         f"{math.degrees(definition.converging_half_angle):g}°"
                         if self._result.ok else self._result.message)
        self.settingsChanged.emit()
        self.resultChanged.emit()

    # -- results ------------------------------------------------------------

    def result(self) -> GeometryResult | None:
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
        return {"ok": "Computed", "warning": "Computed with advisories",
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

    @Property("QVariantList", notify=resultChanged)
    def groups(self):
        return [] if self._result is None else service.quantity_groups(self._result)

    @Property("QVariantList", notify=resultChanged)
    def profile(self):
        return [] if self._result is None else service.profile(self._result)

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


def _basis_rows(basis) -> list[dict[str, str]]:
    return [
        {"label": "Propellant", "value": f"{basis.pair_label} · trade"},
        {"label": "Chamber pressure", "value": f"{basis.chamber_pressure / 1.0e6:g} MPa · trade"},
        {"label": "Target thrust", "value": f"{basis.thrust / 1.0e3:g} kN · requirement"},
        {"label": "Nozzle", "value": f"Ae/At {basis.area_ratio:g} · sizing"},
        {"label": "Throat area At",
         "value": f"{service.display_value('throat_area', basis.throat_area)} cm² · sizing"},
        {"label": "Throat diameter Dt",
         "value": f"{service.display_value('throat_diameter', basis.throat_diameter)} mm · sizing"},
        {"label": "Sizing", "value": basis.sizing_fingerprint[:12]},
    ]
