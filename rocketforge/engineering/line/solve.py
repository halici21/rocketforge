"""The line solve: regime, friction factor, pressure loss.

Never raises for a physical situation the model cannot represent. A
transitional Reynolds number, a gas state and an insufficient inlet pressure
are all *answers*, reported through ``Solution`` with a named diagnostic.
Malformed input still raises.
"""

from __future__ import annotations

from rocketforge.core.result import Diagnostic, Severity, Solution, Status
from rocketforge.physics.fluids import FluidProperty

from . import relations as rel
from .friction import colebrook_darcy_friction_factor, colebrook_residual
from .requests import LINE_MODEL_ASSUMPTIONS, CircularLineRequest
from .results import LineFluidSnapshot, LineResult
from .types import (
    REYNOLDS_LAMINAR_LIMIT,
    REYNOLDS_TURBULENT_ONSET,
    FlowRegime,
    classify,
)

__all__ = ["solve_line"]


def _snapshot(request: CircularLineRequest) -> LineFluidSnapshot:
    state = request.fluid_state
    provenance = state.provenance
    return LineFluidSnapshot(
        fluid_name=state.fluid.name,
        temperature=float(state.temperature),
        pressure=float(state.pressure),
        phase=state.phase.value if state.phase is not None else "unknown",
        density=state.value_of(FluidProperty.DENSITY),
        dynamic_viscosity=state.value_of(FluidProperty.DYNAMIC_VISCOSITY),
        provider_id=provenance.provider_id,
        provider_label=provenance.provider_label,
        library_version=provenance.library_version,
        backend=provenance.backend)


def solve_line(request: CircularLineRequest) -> Solution[LineResult]:
    """Solve one straight circular line."""
    if not isinstance(request, CircularLineRequest):
        raise TypeError(
            f"expected a CircularLineRequest, got {type(request).__name__}")

    usable, why = request.usable_fluid()
    if not usable:
        return Solution(
            value=None, status=Status.NO_SOLUTION,
            diagnostics=(Diagnostic(
                code="LINE_FLUID_STATE_UNUSABLE", severity=Severity.ERROR,
                message=why, field="fluid_state"),))

    fluid = _snapshot(request)
    density = fluid.density
    viscosity = fluid.dynamic_viscosity
    diameter = float(request.inner_diameter)

    area = rel.circular_area(diameter)
    volumetric = rel.volumetric_flow(request.mass_flow, density)
    velocity = rel.mean_velocity(request.mass_flow, density, diameter)
    reynolds = rel.reynolds_number(density, velocity, diameter, viscosity)
    reynolds_mass = rel.reynolds_number_from_mass_flow(
        request.mass_flow, diameter, viscosity)
    roughness = rel.relative_roughness(request.absolute_roughness, diameter)
    q_dynamic = rel.dynamic_pressure(density, velocity)
    regime = classify(reynolds)

    common = dict(
        fluid=fluid, mass_flow=float(request.mass_flow),
        length=float(request.length), inner_diameter=diameter,
        absolute_roughness=float(request.absolute_roughness),
        area=area, volumetric_flow=volumetric, mean_velocity=velocity,
        reynolds_number=reynolds,
        reynolds_number_from_mass_flow=reynolds_mass,
        relative_roughness=roughness, dynamic_pressure=q_dynamic,
        flow_regime=regime, inlet_pressure=request.inlet_pressure,
        assumptions=LINE_MODEL_ASSUMPTIONS)

    if regime is FlowRegime.TRANSITIONAL:
        return Solution(
            value=LineResult(**common),
            status=Status.OK_WITH_WARNINGS,
            diagnostics=(Diagnostic(
                code="LINE_TRANSITIONAL_REGIME_UNSUPPORTED",
                severity=Severity.WARNING,
                message=(
                    f"Re = {reynolds:.6g} lies between the laminar limit "
                    f"({REYNOLDS_LAMINAR_LIMIT:g}) and the turbulent onset "
                    f"({REYNOLDS_TURBULENT_ONSET:g}). No friction factor is "
                    "reported: 64/Re no longer holds, Colebrook-White does not "
                    "yet apply, and interpolating between them would invent a "
                    "number rather than compute one. The velocity, Reynolds "
                    "number and geometry above are still valid."),
                field="reynolds_number",
                detail={"reynolds_number": reynolds,
                        "laminar_limit": REYNOLDS_LAMINAR_LIMIT,
                        "turbulent_onset": REYNOLDS_TURBULENT_ONSET}),))

    report = None
    residual = None
    if regime is FlowRegime.LAMINAR:
        friction = rel.laminar_darcy_friction_factor(reynolds)
    else:
        try:
            friction, report = colebrook_darcy_friction_factor(
                reynolds, roughness)
        except Exception as exc:  # noqa: BLE001 - a domain refusal is an answer
            return Solution(
                value=None, status=Status.NO_SOLUTION,
                diagnostics=(Diagnostic(
                    code="LINE_OUTSIDE_MODEL_DOMAIN", severity=Severity.ERROR,
                    message=str(exc), field="reynolds_number"),))
        if not report.converged:
            return Solution(
                value=None, status=Status.NO_SOLUTION,
                diagnostics=(Diagnostic(
                    code="LINE_FRICTION_FACTOR_NOT_CONVERGED",
                    severity=Severity.ERROR,
                    message=(
                        "the Colebrook-White solve did not converge in "
                        f"{report.iterations} iterations. No approximation is "
                        "substituted and the last iterate is not returned: an "
                        "unconverged friction factor would carry the authority "
                        "of a converged one."),
                    field="darcy_friction_factor"),))
        residual = colebrook_residual(friction, reynolds, roughness)

    pressure_drop = rel.darcy_weisbach_pressure_drop(
        friction, request.length, diameter, density, velocity)

    inlet = request.inlet_pressure
    if pressure_drop >= inlet:
        return Solution(
            value=None, status=Status.NO_SOLUTION,
            diagnostics=(Diagnostic(
                code="LINE_INSUFFICIENT_INLET_PRESSURE",
                severity=Severity.ERROR,
                message=(
                    f"the friction loss over this line is {pressure_drop:.6g} "
                    f"Pa and the inlet pressure is {inlet:.6g} Pa, so the "
                    "outlet pressure would be zero or negative. That is not a "
                    "hydraulic solution: it says this flow cannot be driven "
                    "through this line. Nothing is clamped."),
                field="major_pressure_drop",
                detail={"major_pressure_drop": pressure_drop,
                        "inlet_pressure": inlet}),))

    return Solution(
        value=LineResult(darcy_friction_factor=friction,
                         major_pressure_drop=pressure_drop,
                         outlet_pressure=inlet - pressure_drop,
                         colebrook_residual=residual, convergence=report,
                         **common),
        status=Status.OK)
