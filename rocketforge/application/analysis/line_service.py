"""Line analysis: case, outcome, display rows, transport-envelope gate.

Qt-free. Never raises: an unavailable provider, a state outside the validated
transport envelope, a transitional Reynolds number and an insufficient inlet
pressure are all *outcomes*, each with its own kind and message.

**The transport gate is here, not in `engineering.line`.** The line model is
generic and will solve any valid fluid state. Whether *this* fluid's viscosity
is validated at *this* state is a product claim, and product claims belong to
the composition root.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .fluid_property_provider import availability, fluid_named, property_provider

__all__ = [
    "LineCase",
    "LineOutcome",
    "LineRow",
    "solve_case",
    "result_rows",
    "provenance_rows",
    "DEFAULT_CASE",
    "EMPTY",
    "TRANSPORT_ENVELOPE",
    "transport_status",
]

#: The envelope methane viscosity was validated over, from
#: ``docs/engineering/METHANE_TRANSPORT_VALIDATION.md``. Density is validated
#: more widely; viscosity is the binding constraint and the one a line needs.
#:
#: Recorded here, in the application layer, rather than inside the frozen fluid
#: API: it is a statement about what RocketForge is willing to *claim*, and the
#: physics package's job is to compute, not to make claims.
TRANSPORT_ENVELOPE: dict[str, dict[str, Any]] = {
    "METHANE": {
        "temperature_K": (100.0, 125.0),
        "pressure_Pa": (5.0e5, 3.0e6),
        "phase": "liquid",
        "reference": ("Sotiriadou et al. 2025 evaluated correlation, 3 % "
                      "(k=2); Diller 1980 primary data, 2 %"),
        "worst_observed": 0.02885,
    },
    "OXYGEN": {
        "temperature_K": (80.0, 100.0),
        "pressure_Pa": (5.0e4, 3.0e6),
        "phase": "liquid",
        "reference": "NIST WebBook, same correlation lineage (Lemmon 2004)",
        "worst_observed": None,
    },
    "HYDROGEN": {
        "temperature_K": (15.0, 30.0),
        "pressure_Pa": (5.0e4, 3.0e6),
        "phase": "liquid",
        "reference": "NIST WebBook, same correlation lineage (Muzny 2013)",
        "worst_observed": None,
    },
}


@dataclass(frozen=True, slots=True)
class LineCase:
    """What the user asked for.

    ``pressure`` is the **line inlet / fluid-property pressure** — a feed-system
    state. It is never a chamber pressure, and nothing here reinterprets it as
    one. The value below is the starting value of an input field, it is
    displayed, and it travels into the request.
    """

    fluid_name: str = "METHANE"
    temperature: float = 111.643
    pressure: float = 1.0e6
    mass_flow: float = 2.0
    length: float = 5.0
    inner_diameter: float = 0.02
    absolute_roughness: float = 1.5e-6

    def replace(self, **changes: Any) -> "LineCase":
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class LineOutcome:
    """One line analysis, in a form the interface can render."""

    kind: str
    case: LineCase
    result: Any = None
    fluid_state: Any = None
    message: str = ""
    diagnostics: tuple[Any, ...] = ()
    transport_validated: bool = False
    transport_note: str = ""

    @property
    def ok(self) -> bool:
        return self.result is not None

    @property
    def status_label(self) -> str:
        return {
            "ok": "Solved",
            "transitional": "Transitional regime",
            "refused": "Refused",
            "outside_transport_envelope": "Outside validated transport envelope",
            "unavailable": "Provider unavailable",
            "empty": "No result yet",
        }.get(self.kind, self.kind)

    @property
    def status_tone(self) -> str:
        return {"ok": "positive", "transitional": "caution",
                "refused": "negative", "outside_transport_envelope": "caution",
                "unavailable": "neutral", "empty": "neutral"}.get(
                    self.kind, "neutral")


DEFAULT_CASE = LineCase()
EMPTY = LineOutcome(kind="empty", case=DEFAULT_CASE,
                    message="Enter a fluid state, a flow and a line geometry.")


def transport_status(fluid_name: str, temperature: float,
                     pressure: float) -> tuple[bool, str]:
    """Whether viscosity is validated for this fluid at this state."""
    envelope = TRANSPORT_ENVELOPE.get(str(fluid_name).upper())
    if envelope is None:
        return False, (f"{fluid_name} has no recorded transport-validation "
                       "envelope, so no production line result is offered for "
                       "it.")
    t_low, t_high = envelope["temperature_K"]
    p_low, p_high = envelope["pressure_Pa"]
    if not t_low <= float(temperature) <= t_high:
        return False, (
            f"{fluid_name} dynamic viscosity is validated over "
            f"{t_low:g}–{t_high:g} K; this state is at {temperature:g} K. "
            "Outside the validated envelope the provider still answers, but "
            "RocketForge does not present a production line result from it.")
    if not p_low <= float(pressure) <= p_high:
        return False, (
            f"{fluid_name} dynamic viscosity is validated over "
            f"{p_low / 1e5:g}–{p_high / 1e5:g} bar; this state is at "
            f"{pressure / 1e5:g} bar.")
    return True, (f"Dynamic viscosity validated over {t_low:g}–{t_high:g} K "
                  f"and {p_low / 1e5:g}–{p_high / 1e5:g} bar against "
                  f"{envelope['reference']}.")


def solve_case(case: LineCase) -> LineOutcome:
    """Evaluate one line. Never raises."""
    if not isinstance(case, LineCase):
        raise TypeError(f"expected a LineCase, got {type(case).__name__}")

    provider_state = availability()
    if not provider_state.is_usable:
        return LineOutcome(kind="unavailable", case=case,
                           message=provider_state.detail)

    from rocketforge.engineering.line import CircularLineRequest, solve_line
    from rocketforge.physics.fluids import FluidPhase, FluidStateRequest

    validated, note = transport_status(case.fluid_name, case.temperature,
                                       case.pressure)

    try:
        fluid = fluid_named(case.fluid_name)
        state_solution = property_provider().evaluate(FluidStateRequest(
            fluid=fluid, temperature=float(case.temperature),
            pressure=float(case.pressure),
            required_phase=FluidPhase.LIQUID))
    except Exception as exc:  # noqa: BLE001
        return LineOutcome(kind="refused", case=case, message=str(exc),
                           transport_validated=validated, transport_note=note)

    if state_solution.value is None:
        return LineOutcome(
            kind="refused", case=case,
            message="; ".join(d.message for d in state_solution.diagnostics),
            diagnostics=tuple(state_solution.diagnostics),
            transport_validated=validated, transport_note=note)

    state = state_solution.value
    if not validated:
        return LineOutcome(kind="outside_transport_envelope", case=case,
                           fluid_state=state, message=note,
                           transport_validated=False, transport_note=note)

    try:
        request = CircularLineRequest(
            fluid_state=state, mass_flow=float(case.mass_flow),
            length=float(case.length),
            inner_diameter=float(case.inner_diameter),
            absolute_roughness=float(case.absolute_roughness))
    except Exception as exc:  # noqa: BLE001
        return LineOutcome(kind="refused", case=case, fluid_state=state,
                           message=str(exc), transport_validated=True,
                           transport_note=note)

    solution = solve_line(request)
    if solution.value is None:
        return LineOutcome(
            kind="refused", case=case, fluid_state=state,
            message="; ".join(d.message for d in solution.diagnostics),
            diagnostics=tuple(solution.diagnostics),
            transport_validated=True, transport_note=note)

    from rocketforge.engineering.line import FlowRegime

    kind = ("transitional"
            if solution.value.flow_regime is FlowRegime.TRANSITIONAL else "ok")
    return LineOutcome(
        kind=kind, case=case, result=solution.value, fluid_state=state,
        message="; ".join(d.message for d in solution.diagnostics),
        diagnostics=tuple(solution.diagnostics),
        transport_validated=True, transport_note=note)


@dataclass(frozen=True, slots=True)
class LineRow:
    """One line of a results table."""

    label: str
    value: str
    unit: str
    available: bool


def _format(value: float) -> str:
    magnitude = abs(value)
    if magnitude != 0.0 and (magnitude < 1e-3 or magnitude >= 1e6):
        return f"{value:.6e}"
    return f"{value:,.6g}"


EM_DASH = "—"


def result_rows(outcome: LineOutcome) -> tuple[LineRow, ...]:
    """Fluid, flow, friction and pressure rows. Absence is a row, not a gap."""
    result = outcome.result
    if result is None:
        return ()
    rows = [
        LineRow("Density  ρ", _format(result.fluid.density), "kg/m³", True),
        LineRow("Dynamic viscosity  μ",
                _format(result.fluid.dynamic_viscosity), "Pa·s", True),
        LineRow("Flow area  A", _format(result.area), "m²", True),
        LineRow("Volumetric flow  Q", _format(result.volumetric_flow),
                "m³/s", True),
        LineRow("Mean velocity  V", _format(result.mean_velocity), "m/s", True),
        LineRow("Reynolds number  Re", _format(result.reynolds_number), "", True),
        LineRow("Flow regime", result.flow_regime.value.title(), "", True),
        LineRow("Relative roughness  ε/D",
                _format(result.relative_roughness), "", True),
    ]
    has_friction = result.darcy_friction_factor is not None
    rows.append(LineRow(
        "Darcy friction factor  f_D",
        _format(result.darcy_friction_factor) if has_friction else EM_DASH,
        "", has_friction))
    rows.append(LineRow("Dynamic pressure  q",
                        _format(result.dynamic_pressure), "Pa", True))
    has_drop = result.major_pressure_drop is not None
    rows.append(LineRow(
        "Friction pressure drop  Δp",
        _format(result.major_pressure_drop) if has_drop else EM_DASH,
        "Pa", has_drop))
    rows.append(LineRow("Line inlet pressure",
                        _format(result.inlet_pressure), "Pa", True))
    has_outlet = result.outlet_pressure is not None
    rows.append(LineRow(
        "Predicted outlet pressure",
        _format(result.outlet_pressure) if has_outlet else EM_DASH,
        "Pa", has_outlet))
    return tuple(rows)


def provenance_rows(outcome: LineOutcome) -> tuple[tuple[str, str], ...]:
    """Where the numbers came from, and what the model assumed."""
    result = outcome.result
    if result is None:
        return ()
    fluid = result.fluid
    rows = [
        ("Fluid", fluid.fluid_name),
        ("Phase", fluid.phase),
        ("Property state", f"{fluid.temperature:g} K, {fluid.pressure:g} Pa"),
        ("Property provider", fluid.provider_label),
        ("Library version", fluid.library_version or EM_DASH),
        ("Backend", fluid.backend or EM_DASH),
        ("Transport validation", outcome.transport_note),
        ("Friction convention", result.friction_convention),
    ]
    report = result.convergence
    if report is not None:
        rows.append(("Colebrook solve",
                     f"{report.method}, {report.iterations} iterations, "
                     f"residual {result.colebrook_residual:.3e}"))
    return tuple(rows)
