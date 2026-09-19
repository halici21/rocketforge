"""The Qt facade for the Fluid Properties workspace.

The only file in this feature that imports Qt. It holds no equation, no
physical constant, no unit conversion and no provider import: every number it
publishes was computed by :mod:`fluid_property_service` from
``rocketforge.physics.fluids``, and every string it publishes was written
there.

Two behaviours worth reading the code for:

**The pressure field is an input, not a default.** Its starting value is
displayed, editable and travels into the request. Nothing substitutes a
pressure for a request that did not carry one, because at 95 K oxygen is a
liquid at 3 bar and a gas at 1 atm.

**An unavailable property is a row, not a gap.** Every property in the
vocabulary appears in the table with its status; a missing viscosity shows the
reason it is missing rather than an empty cell that reads as zero.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from . import fluid_property_provider as gateway
from . import fluid_property_service as service

__all__ = ["FluidPropertyController"]


class FluidPropertyController(QObject):
    """Backs the Fluid Properties page."""

    inputsChanged = Signal()
    resultChanged = Signal()
    availabilityChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._case = service.DEFAULT_CASE
        self._outcome = service.EMPTY
        self._availability: Any | None = None
        # Mirrors LineController/ThermochemistryController's own resultStale
        # pattern exactly: a plain flag, set whenever an input moves while a
        # result already exists, cleared only when a new result is adopted.
        self._stale = False

    # -- availability ------------------------------------------------------

    def _available(self) -> Any:
        if self._availability is None:
            self._availability = gateway.availability()
        return self._availability

    @Property(bool, notify=availabilityChanged)
    def providerAvailable(self) -> bool:
        """Whether high-fidelity properties can be computed in this build."""
        return bool(self._available().is_usable)

    @Property(str, notify=availabilityChanged)
    def providerLabel(self) -> str:
        return str(self._available().label)

    @Property(str, notify=availabilityChanged)
    def providerVersion(self) -> str:
        return str(self._available().library_version)

    @Property(str, notify=availabilityChanged)
    def providerBackend(self) -> str:
        return str(self._available().backend)

    @Property(str, notify=availabilityChanged)
    def providerDetail(self) -> str:
        return str(self._available().detail)

    # -- inputs ------------------------------------------------------------

    @Property("QVariantList", constant=True)
    def fluidOptions(self) -> list:
        """The fluids this build can evaluate."""
        return [{"name": option.name, "label": option.label,
                 "formula": option.formula}
                for option in gateway.fluid_options()]

    @Property(str, notify=inputsChanged)
    def fluidName(self) -> str:
        return self._case.fluid_name

    @Property(float, notify=inputsChanged)
    def temperature(self) -> float:
        return float(self._case.temperature)

    @Property(float, notify=inputsChanged)
    def pressure(self) -> float:
        return float(self._case.pressure)

    def _mark_dirty(self) -> None:
        """An input that defines the evaluation moved.

        Only marks stale if a result already exists -- editing the form
        before the first evaluation is not staleness, it is the normal act
        of setting up a case (identical guard to
        ThermochemistryController._on_input_changed and LineController's own
        _mark_dirty).
        """
        if self._outcome.state is not None or self._outcome.kind not in (
                "empty", "unavailable"):
            self._stale = True
        self.inputsChanged.emit()
        self.resultChanged.emit()

    @Slot(str)
    def setFluid(self, name: str) -> None:
        self._case = self._case.replace(fluid_name=str(name))
        self._mark_dirty()

    @Slot(float)
    def setTemperature(self, value: float) -> None:
        self._case = self._case.replace(temperature=float(value))
        self._mark_dirty()

    @Slot(float)
    def setPressure(self, value: float) -> None:
        self._case = self._case.replace(pressure=float(value))
        self._mark_dirty()

    # -- the calculation ---------------------------------------------------

    @Slot()
    def calculate(self) -> None:
        """Evaluate the current case. Never raises."""
        self._outcome = service.evaluate_case(self._case)
        self._stale = False
        self.resultChanged.emit()

    @Slot()
    def clear(self) -> None:
        self._outcome = service.EMPTY
        self._stale = False
        self.resultChanged.emit()

    @Property(bool, notify=resultChanged)
    def resultStale(self) -> bool:
        """Whether the inputs have moved since this result was produced."""
        return self._stale

    # -- results -----------------------------------------------------------

    @Property(bool, notify=resultChanged)
    def hasResult(self) -> bool:
        return bool(self._outcome.ok)

    @Property(str, notify=resultChanged)
    def statusLabel(self) -> str:
        return self._outcome.status_label

    @Property(str, notify=resultChanged)
    def statusTone(self) -> str:
        return self._outcome.status_tone

    @Property(str, notify=resultChanged)
    def message(self) -> str:
        return self._outcome.message

    @Property(str, notify=resultChanged)
    def phase(self) -> str:
        state = self._outcome.state
        if state is None:
            return ""
        return state.phase.value if state.phase is not None else "not determined"

    @Property("QVariantList", notify=resultChanged)
    def resultRows(self) -> list:
        """One entry per property, present or not."""
        return [{"label": row.label, "value": row.value, "unit": row.unit,
                 "status": row.status, "available": row.available}
                for row in service.result_rows(self._outcome)]

    @Property("QVariantList", notify=resultChanged)
    def provenanceRows(self) -> list:
        """Label/value pairs describing where the numbers came from."""
        return [{"label": label, "value": value}
                for label, value in service.provenance_rows(self._outcome)]

    @Property("QVariantList", notify=resultChanged)
    def diagnosticRows(self) -> list:
        """Whatever the provider said about this state."""
        return [{"code": d.code, "severity": str(d.severity.value),
                 "message": d.message}
                for d in self._outcome.diagnostics]
