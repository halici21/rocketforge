"""Fluid property inspection: case, outcome, display rows, provenance.

Qt-free, so every branch is testable headlessly. Never raises: an unsupported
state, an absent library and a two-phase point are all *outcomes*, each with
its own kind and its own message.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .fluid_property_provider import (
    CONSTANT_LABEL,
    HIGH_FIDELITY_LABEL,
    availability,
    fluid_named,
    property_provider,
)

__all__ = [
    "FluidCase",
    "FluidOutcome",
    "PropertyRow",
    "evaluate_case",
    "result_rows",
    "provenance_rows",
    "DEFAULT_CASE",
    "PROPERTY_ORDER",
]

#: The order properties are shown in: the two the rest of the stack consumes
#: first, then the transport pair the next roadmap step will.
PROPERTY_ORDER = ("density", "specific_enthalpy", "specific_heat_cp",
                  "dynamic_viscosity", "thermal_conductivity")


@dataclass(frozen=True, slots=True)
class FluidCase:
    """What the user asked for.

    ``pressure`` has no default that means "standard": the value below is the
    *starting value of an input field*, it is displayed, and it travels into
    the request. It is never silently supplied for a caller who omitted one.
    """

    fluid_name: str = "OXYGEN"
    temperature: float = 90.17
    pressure: float = 300000.0

    def replace(self, **changes: Any) -> "FluidCase":
        """A copy with fields changed."""
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class FluidOutcome:
    """The result of one evaluation, in a form the interface can render."""

    kind: str
    case: FluidCase
    state: Any = None
    message: str = ""
    diagnostics: tuple[Any, ...] = ()

    @property
    def ok(self) -> bool:
        """Whether there are numbers to show."""
        return self.state is not None

    @property
    def status_label(self) -> str:
        """A short status for the header."""
        return {
            "ok": "Evaluated",
            "warning": "Evaluated with warnings",
            "refused": "Refused",
            "unavailable": "Provider unavailable",
            "empty": "No result yet",
        }.get(self.kind, self.kind)

    @property
    def status_tone(self) -> str:
        """Which tone the header uses. Presentation only."""
        return {"ok": "positive", "warning": "caution", "refused": "negative",
                "unavailable": "neutral", "empty": "neutral"}.get(
                    self.kind, "neutral")


DEFAULT_CASE = FluidCase()

EMPTY = FluidOutcome(kind="empty", case=DEFAULT_CASE,
                     message="Enter a fluid, a temperature and a pressure.")


@dataclass(frozen=True, slots=True)
class PropertyRow:
    """One line of the results table."""

    label: str
    value: str
    unit: str
    status: str
    available: bool


def evaluate_case(case: FluidCase) -> FluidOutcome:
    """Evaluate one fluid state. Never raises."""
    if not isinstance(case, FluidCase):
        raise TypeError(f"expected a FluidCase, got {type(case).__name__}")

    state_of_provider = availability()
    if not state_of_provider.is_usable:
        return FluidOutcome(kind="unavailable", case=case,
                            message=state_of_provider.detail)

    from rocketforge.physics.fluids import FluidStateRequest

    try:
        fluid = fluid_named(case.fluid_name)
        request = FluidStateRequest(fluid=fluid,
                                    temperature=float(case.temperature),
                                    pressure=float(case.pressure))
    except Exception as exc:  # noqa: BLE001 - malformed input is an outcome here
        return FluidOutcome(kind="refused", case=case, message=str(exc))

    try:
        solution = property_provider().evaluate(request)
    except Exception as exc:  # noqa: BLE001
        return FluidOutcome(kind="refused", case=case, message=str(exc))

    if solution.value is None:
        message = "; ".join(d.message for d in solution.diagnostics) \
            or "the provider returned no state and gave no reason"
        return FluidOutcome(kind="refused", case=case, message=message,
                            diagnostics=tuple(solution.diagnostics))

    kind = "warning" if solution.diagnostics else "ok"
    return FluidOutcome(kind=kind, case=case, state=solution.value,
                        message="; ".join(d.message for d in solution.diagnostics),
                        diagnostics=tuple(solution.diagnostics))


def _format(value: float) -> str:
    magnitude = abs(value)
    if magnitude != 0.0 and (magnitude < 1e-3 or magnitude >= 1e6):
        return f"{value:.6e}"
    return f"{value:,.6g}"


def result_rows(outcome: FluidOutcome) -> tuple[PropertyRow, ...]:
    """One row per property, present or not. Absence is a row, not a gap."""
    from rocketforge.physics.fluids import FluidProperty

    if outcome.state is None:
        return ()
    labels = {
        "density": "Density",
        "specific_enthalpy": "Specific enthalpy",
        "specific_heat_cp": "Specific heat, cp",
        "dynamic_viscosity": "Dynamic viscosity",
        "thermal_conductivity": "Thermal conductivity",
    }
    rows: list[PropertyRow] = []
    for key in PROPERTY_ORDER:
        prop = FluidProperty(key)
        status = outcome.state.status_of(prop)
        available = outcome.state.has(prop)
        rows.append(PropertyRow(
            label=labels[key],
            value=_format(outcome.state.value_of(prop)) if available else "—",
            unit=prop.unit,
            status=status.value.replace("_", " "),
            available=available))
    return tuple(rows)


def provenance_rows(outcome: FluidOutcome) -> tuple[tuple[str, str], ...]:
    """Label/value pairs describing where the numbers came from."""
    if outcome.state is None:
        return ()
    state = outcome.state
    provenance = state.provenance
    rows = [
        ("Fluid", f"{state.fluid.name} ({state.fluid.formula})"),
        ("Phase", state.phase.value if state.phase is not None
         else "not determined"),
        ("Temperature", f"{state.temperature:g} K"),
        ("Pressure", f"{state.pressure:g} Pa"),
        ("Provider", provenance.provider_label),
        ("Library version", provenance.library_version or "—"),
        ("Backend", provenance.backend or "—"),
        ("Provider's name for this fluid", provenance.native_fluid_name or "—"),
        ("Model", provenance.model_notes or "—"),
    ]
    for approximation in provenance.approximations:
        rows.append(("Approximation", approximation))
    return tuple(rows)
