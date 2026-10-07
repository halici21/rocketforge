"""The QObject the Injector & Feed Pressure page binds to (LIQ-6).

It reads the accepted sizing in the Thrust Chamber Sizing controller, holds
what the user states for each propellant branch (injector pressure drop,
discharge coefficient, density or its source, holes, pressure terms), and
computes **only** from :meth:`computeInjector`. Opening the page, editing an
input, or a change upstream never computes: a change upstream only
re-announces this controller's state, and a result whose question has moved
is reported stale when it is next read.

Display units are converted here, at the boundary: pressures are typed in bar,
hole and line diameters in mm; everything below is SI.
"""

from __future__ import annotations

import math
import pathlib
from dataclasses import replace

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from rocketforge.engine.injector import (
    LOSS_TERMS,
    Branch,
    DensitySource,
    HoleMode,
    InjectorResult,
    LossMode,
)

from . import injector_service as service

__all__ = ["InjectorController"]

_BAR = 1.0e5
_MM = 1.0e-3
#: Typed field -> SI scale.
_SCALE = {"pressure_drop": _BAR, "discharge_coefficient": 1.0, "density": 1.0,
          "hole_count": 1.0, "hole_diameter": _MM}


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


def _text(value: float | None, scale: float = 1.0) -> str:
    return "" if value is None else f"{value / scale:.12g}"


def _branch(key: str) -> Branch | None:
    try:
        return Branch(str(key))
    except ValueError:
        return None


class InjectorController(QObject):
    """Application-side facade for the Injector & Feed Pressure page."""

    settingsChanged = Signal()
    resultChanged = Signal()

    def __init__(self, sizing_source, parent: QObject | None = None) -> None:
        QObject.__init__(self, parent)
        self._sizing = sizing_source
        self._settings = {Branch.OXIDISER: service.BranchSettings(),
                          Branch.FUEL: service.BranchSettings()}
        self._result: InjectorResult | None = None
        self._message = ""
        sizing_source.resultChanged.connect(self._on_inputs_changed)

    # -- inputs -------------------------------------------------------------

    def _basis(self):
        return service.flow_basis(self._sizing.result(),
                                  bool(self._sizing.property("resultStale")))

    def _definition(self):
        basis, issues = self._basis()
        if basis is None:
            return None, issues
        return service.build_definition(basis, self._settings[Branch.OXIDISER],
                                        self._settings[Branch.FUEL])

    def _on_inputs_changed(self) -> None:
        # Announce only: nothing is computed here.
        self.settingsChanged.emit()
        self.resultChanged.emit()

    def _update(self, branch: Branch, settings: service.BranchSettings) -> None:
        if settings != self._settings[branch]:
            self._settings[branch] = settings
            self._on_inputs_changed()

    @Slot(str, str, str)
    def setValue(self, branch: str, name: str, text: str) -> None:
        """A hydraulic input, typed in display units."""
        b = _branch(branch)
        ok, value = _parse(text)
        if b is None or name not in _SCALE or not ok:
            return
        self._update(b, replace(self._settings[b],
                                **{name: None if value is None else value * _SCALE[name]}))

    @Slot(str, str)
    def setDensitySource(self, branch: str, key: str) -> None:
        b = _branch(branch)
        if b is not None and key in {s.value for s in DensitySource}:
            self._update(b, replace(self._settings[b], density_source=DensitySource(key)))

    @Slot(str, str)
    def setHoleMode(self, branch: str, key: str) -> None:
        b = _branch(branch)
        if b is not None and key in {m.value for m in HoleMode}:
            self._update(b, replace(self._settings[b], hole_mode=HoleMode(key)))

    @Slot(str, str, str)
    def setLossMode(self, branch: str, term: str, mode: str) -> None:
        b = _branch(branch)
        if b is None or term not in self._settings[b].loss_modes \
                or mode not in {m.value for m in LossMode}:
            return
        new = LossMode(mode)
        if new is LossMode.LINE_DIAMETER and term != "dynamic_head":
            return
        s = self._settings[b]
        values = dict(s.loss_values)
        if new is not s.loss_modes[term]:
            values[term] = None          # a pressure and a diameter are not interchangeable
        self._update(b, replace(s, loss_modes={**s.loss_modes, term: new}, loss_values=values))

    @Slot(str, str, str)
    def setLossValue(self, branch: str, term: str, text: str) -> None:
        b = _branch(branch)
        ok, value = _parse(text)
        if b is None or not ok or term not in self._settings[b].loss_values:
            return
        s = self._settings[b]
        scale = _MM if s.loss_modes[term] is LossMode.LINE_DIAMETER else _BAR
        self._update(b, replace(s, loss_values={
            **s.loss_values, term: None if value is None else value * scale}))

    def _state(self, branch: Branch) -> dict:
        s = self._settings[branch]
        basis, _ = self._basis()
        propellant = basis.propellant_of(branch) if basis is not None else ""
        losses = []
        for key, label, source in LOSS_TERMS:
            mode = s.loss_modes[key]
            diameter = mode is LossMode.LINE_DIAMETER
            losses.append({"key": key, "label": label, "source": source, "mode": mode.value,
                           "valueText": _text(s.loss_values[key], _MM if diameter else _BAR),
                           "unit": "mm" if diameter else "bar",
                           "editable": mode in (LossMode.STATED, LossMode.LINE_DIAMETER)})
        return {
            "branch": branch.value,
            "title": "Oxidiser" if branch is Branch.OXIDISER else "Fuel",
            "propellant": propellant,
            "fluidModelSupported": bool(propellant) and service.fluid_model_supported(propellant),
            "pressureDropText": _text(s.pressure_drop, _BAR),
            "dischargeCoefficientText": _text(s.discharge_coefficient),
            "densitySource": s.density_source.value,
            "densityText": _text(s.density),
            "holeMode": s.hole_mode.value,
            "holeCountText": _text(s.hole_count),
            "holeDiameterText": _text(s.hole_diameter, _MM),
            "losses": losses,
        }

    @Property("QVariantMap", notify=settingsChanged)
    def oxidiserState(self):
        return self._state(Branch.OXIDISER)

    @Property("QVariantMap", notify=settingsChanged)
    def fuelState(self):
        return self._state(Branch.FUEL)

    @Property("QVariantList", constant=True)
    def densityOptions(self):
        return [{"key": "stated", "label": "Stated"},
                {"key": "fluid_model", "label": "Validated fluid model"}]

    @Property("QVariantList", constant=True)
    def holeModeOptions(self):
        return [{"key": "area", "label": "Total area"},
                {"key": "hole_count", "label": "Hole count"},
                {"key": "hole_diameter", "label": "Hole diameter"}]

    @Property("QVariantList", constant=True)
    def lossModeOptions(self):
        return [{"key": "unresolved", "label": "Unresolved"},
                {"key": "stated", "label": "Stated"},
                {"key": "not_applicable", "label": "Not applicable"},
                {"key": "line_diameter", "label": "From line diameter"}]

    @Property(bool, notify=settingsChanged)
    def hasFlows(self) -> bool:
        return self._basis()[0] is not None

    @Property("QVariantList", notify=settingsChanged)
    def basisRows(self):
        """The LIQ-4 flows this study injects, as LIQ-4 sized them."""
        basis, _ = self._basis()
        return [] if basis is None else _basis_rows(basis)

    @Property("QVariantList", notify=settingsChanged)
    def issues(self):
        _, issues = self._definition()
        return [{"code": i.code, "field": i.field, "message": i.message} for i in issues]

    @Property(bool, notify=settingsChanged)
    def canCompute(self) -> bool:
        return self._definition()[0] is not None

    # -- computing ----------------------------------------------------------

    @Slot()
    def computeInjector(self) -> None:
        """The only entry point that computes."""
        definition, issues = self._definition()
        if definition is None:
            self._message = issues[0].message if issues else "The study is not defined."
            self.resultChanged.emit()
            return
        self._result = service.solve_injector(definition)
        self._message = ("Computed: Δp oxidiser "
                         f"{definition.oxidiser.pressure_drop / _BAR:g} bar, fuel "
                         f"{definition.fuel.pressure_drop / _BAR:g} bar"
                         if self._result.ok else self._result.message)
        self.settingsChanged.emit()
        self.resultChanged.emit()

    # -- results ------------------------------------------------------------

    def result(self) -> InjectorResult | None:
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

    def _branch_view(self, branch: Branch) -> dict:
        if self._result is None:
            return {"ok": False, "message": "", "groups": [], "ledger": [], "density": []}
        b = self._result.branch(branch)
        return {"ok": b.ok, "message": b.message,
                "groups": service.branch_groups(b), "ledger": service.ledger_rows(b),
                "density": [{"label": k, "value": v} for k, v in b.density_provenance.items()]}

    @Property("QVariantMap", notify=resultChanged)
    def oxidiserResult(self):
        return self._branch_view(Branch.OXIDISER)

    @Property("QVariantMap", notify=resultChanged)
    def fuelResult(self):
        return self._branch_view(Branch.FUEL)

    @Property("QVariantList", notify=resultChanged)
    def pairRows(self):
        return [] if self._result is None else service.pair_rows(self._result)

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


def _basis_rows(basis) -> list[dict[str, str]]:
    return [
        {"label": "Propellant", "value": f"{basis.pair_label} · trade"},
        {"label": "Chamber pressure", "value": f"{basis.chamber_pressure / _BAR:g} bar · trade"},
        {"label": "O/F", "value": f"{basis.oxidiser_fuel_ratio:g} · trade"},
        {"label": "Mass flow", "value": f"{basis.mass_flow:.5g} kg/s · sizing"},
        {"label": "Oxidiser flow",
         "value": f"{basis.oxidiser_mass_flow:.5g} kg/s {basis.oxidiser} · sizing"},
        {"label": "Fuel flow", "value": f"{basis.fuel_mass_flow:.5g} kg/s {basis.fuel} · sizing"},
        {"label": "Sizing", "value": basis.sizing_fingerprint[:12]},
    ]
