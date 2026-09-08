"""The Qt facade for the Line workspace.

The only file in this feature that imports Qt. It holds no equation, no
physical constant and no unit conversion: every number it publishes was
computed by :mod:`line_service` from ``rocketforge.engineering.line``, and every
string it publishes was written there.

Two behaviours worth reading the code for:

**The pressure field says what it is.** It is the line inlet / fluid-property
pressure — a feed-system state. Nothing here reads a chamber pressure, and the
label on the control says so rather than leaving it to be assumed.

**A result keeps the inputs that produced it.** The published rows come from
the stored outcome's own case, so editing a field marks the result stale rather
than relabelling it under conditions that did not produce it.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from . import fluid_property_provider as gateway
from . import line_service as service

__all__ = ["LineController"]


class LineController(QObject):
    """Backs the Line page."""

    inputsChanged = Signal()
    resultChanged = Signal()
    availabilityChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._case = service.DEFAULT_CASE
        self._outcome = service.EMPTY
        self._availability: Any | None = None

    # -- availability ------------------------------------------------------

    def _available(self) -> Any:
        if self._availability is None:
            self._availability = gateway.availability()
        return self._availability

    @Property(bool, notify=availabilityChanged)
    def providerAvailable(self) -> bool:
        return bool(self._available().is_usable)

    @Property(str, notify=availabilityChanged)
    def providerLabel(self) -> str:
        return str(self._available().label)

    @Property(str, notify=availabilityChanged)
    def providerDetail(self) -> str:
        return str(self._available().detail)

    # -- inputs ------------------------------------------------------------

    @Property("QVariantList", constant=True)
    def fluidOptions(self) -> list:
        """Only fluids with a recorded transport-validation envelope."""
        return [{"name": option.name, "label": option.label,
                 "formula": option.formula}
                for option in gateway.fluid_options()
                if option.name in service.TRANSPORT_ENVELOPE]

    @Property(str, notify=inputsChanged)
    def fluidName(self) -> str:
        return self._case.fluid_name

    @Property(float, notify=inputsChanged)
    def temperature(self) -> float:
        return float(self._case.temperature)

    @Property(float, notify=inputsChanged)
    def pressure(self) -> float:
        return float(self._case.pressure)

    @Property(float, notify=inputsChanged)
    def massFlow(self) -> float:
        return float(self._case.mass_flow)

    @Property(float, notify=inputsChanged)
    def length(self) -> float:
        return float(self._case.length)

    @Property(float, notify=inputsChanged)
    def innerDiameter(self) -> float:
        return float(self._case.inner_diameter)

    @Property(float, notify=inputsChanged)
    def absoluteRoughness(self) -> float:
        return float(self._case.absolute_roughness)

    @Slot(str)
    def setFluid(self, name: str) -> None:
        self._case = self._case.replace(fluid_name=str(name))
        self.inputsChanged.emit()

    @Slot(float)
    def setTemperature(self, value: float) -> None:
        self._case = self._case.replace(temperature=float(value))
        self.inputsChanged.emit()

    @Slot(float)
    def setPressure(self, value: float) -> None:
        self._case = self._case.replace(pressure=float(value))
        self.inputsChanged.emit()

    @Slot(float)
    def setMassFlow(self, value: float) -> None:
        self._case = self._case.replace(mass_flow=float(value))
        self.inputsChanged.emit()

    @Slot(float)
    def setLength(self, value: float) -> None:
        self._case = self._case.replace(length=float(value))
        self.inputsChanged.emit()

    @Slot(float)
    def setInnerDiameter(self, value: float) -> None:
        self._case = self._case.replace(inner_diameter=float(value))
        self.inputsChanged.emit()

    @Slot(float)
    def setAbsoluteRoughness(self, value: float) -> None:
        self._case = self._case.replace(absolute_roughness=float(value))
        self.inputsChanged.emit()

    # -- the calculation ---------------------------------------------------

    @Slot()
    def calculate(self) -> None:
        """Solve the current case. Never raises."""
        self._outcome = service.solve_case(self._case)
        self.resultChanged.emit()

    @Slot()
    def clear(self) -> None:
        self._outcome = service.EMPTY
        self.resultChanged.emit()

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

    @Property(bool, notify=resultChanged)
    def transportValidated(self) -> bool:
        """Whether viscosity is validated for this fluid at this state.

        Never true merely because a provider answered.
        """
        return bool(self._outcome.transport_validated)

    @Property(str, notify=resultChanged)
    def transportNote(self) -> str:
        return self._outcome.transport_note

    @Property(str, notify=resultChanged)
    def flowRegime(self) -> str:
        result = self._outcome.result
        return result.flow_regime.value.title() if result is not None else ""

    @Property(bool, notify=resultChanged)
    def isTransitional(self) -> bool:
        return self._outcome.kind == "transitional"

    @Property("QVariantList", notify=resultChanged)
    def resultRows(self) -> list:
        return [{"label": row.label, "value": row.value, "unit": row.unit,
                 "available": row.available}
                for row in service.result_rows(self._outcome)]

    @Property("QVariantList", notify=resultChanged)
    def provenanceRows(self) -> list:
        return [{"label": label, "value": value}
                for label, value in service.provenance_rows(self._outcome)]

    @Property("QVariantList", notify=resultChanged)
    def assumptionRows(self) -> list:
        """What the model assumed, shown rather than buried in a document."""
        result = self._outcome.result
        if result is None:
            return []
        return [{"text": item} for item in result.assumptions]
