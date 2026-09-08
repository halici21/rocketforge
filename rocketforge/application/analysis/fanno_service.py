"""Fanno analysis, prepared for presentation.

The adapter between ``rocketforge.physics.compressible.fanno`` and whatever
displays it. It owns no gas dynamics: every number here comes from a physics
call.

**This is where the friction convention is negotiated.** The physics layer
speaks one language and only one -- ``4 f_Fanning L / D``. An engineer may hold
either convention in their head, and a pipe-flow table will usually quote
Darcy, so the interface offers both and this file converts. The conversion
happens exactly once, on the way in, through the physics module's own
:func:`darcy_to_fanning`; no relation is written twice to accommodate the other
convention, because two copies of a definition is how the factor of four gets
in.

Deliberately free of Qt, so all of it can be tested headlessly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ...core.errors import RocketForgeError
from ...core.result import Diagnostic, Severity
from ...physics.compressible import FlowBranch, PerfectGas
from ...physics.compressible import fanno
from .presentation import (
    MAX_TABLE_ROWS,
    CalculatorResult,
    ResultRow,
    TableColumn,
    TableData,
)

__all__ = [
    "SolveMode",
    "SOLVE_MODES",
    "SolveModeInfo",
    "FrictionConvention",
    "FRICTION_CONVENTIONS",
    "ConventionInfo",
    "convention_info",
    "mode_info",
    "solve",
    "duct_segment",
    "duct_parameter_from_geometry",
    "convert_friction_factor",
    "friction_limit",
    "generate_table",
    "columns_for",
    "TableBranch",
    "MAX_TABLE_ROWS",
]


# ---------------------------------------------------------------------------
# the friction convention
# ---------------------------------------------------------------------------


class FrictionConvention(StrEnum):
    """Which friction factor the user is quoting.

    Both describe the same wall. ``f_Darcy = 4 f_Fanning``, and RocketForge
    stores the Fanning form because that is what ``03`` section 8.2 fixed.
    """

    FANNING = "fanning"
    DARCY = "darcy"


@dataclass(frozen=True, slots=True)
class ConventionInfo:
    """How one friction convention labels itself.

    The bare symbol "f" is banned in labels by ``07`` section 6: it is the one
    thing that makes a factor of four invisible.
    """

    convention: FrictionConvention
    label: str
    symbol: str
    hint: str
    relation: str
    default_value: float


FRICTION_CONVENTIONS: tuple[ConventionInfo, ...] = (
    ConventionInfo(FrictionConvention.FANNING, "Fanning", "f_F",
                   "wall shear over dynamic pressure", "f_D = 4 f_F", 0.005),
    ConventionInfo(FrictionConvention.DARCY, "Darcy", "f_D",
                   "the pipe-flow convention, four times the Fanning value",
                   "f_D = 4 f_F", 0.02),
)

_CONVENTION_INDEX = {info.convention: info for info in FRICTION_CONVENTIONS}


def convention_info(convention: FrictionConvention | str) -> ConventionInfo:
    return _CONVENTION_INDEX[FrictionConvention(convention)]


def convert_friction_factor(value: float,
                            source: FrictionConvention | str,
                            target: FrictionConvention | str) -> float:
    """The same physical wall, quoted in the other convention.

    Used when the interface switches convention: the displayed number changes
    so that the duct does not. ``07`` section 6 wanted one of two policies
    stated and kept, and this is policy A -- convert the value, hold the
    physics still. The alternative, keeping the number and silently changing
    the duct by a factor of four, is exactly the confusion the convention rules
    exist to prevent.
    """
    source = FrictionConvention(source)
    target = FrictionConvention(target)
    if source is target:
        return float(value)
    if target is FrictionConvention.FANNING:
        return float(fanno.darcy_to_fanning(float(value)))
    return float(fanno.fanning_to_darcy(float(value)))


def _to_fanning(value: float, convention: FrictionConvention | str) -> float:
    """Whatever the user quoted, as the Fanning factor the physics wants."""
    return convert_friction_factor(value, convention, FrictionConvention.FANNING)


def duct_parameter_from_geometry(friction_factor: float, length: float,
                                 hydraulic_diameter: float,
                                 convention: FrictionConvention | str) -> float:
    """``4 f_Fanning L / D_h`` from a dimensional duct in either convention.

    Hydraulic diameter, not diameter: nothing here assumes a circular passage.
    The friction factor is supplied by the user -- no Colebrook, no Haaland, no
    Moody chart and no Reynolds number, which belong to a fluid-system module
    and would be a correlation hidden inside a gas-dynamics answer.
    """
    return float(fanno.duct_parameter_from_geometry(
        _to_fanning(friction_factor, convention), float(length),
        float(hydraulic_diameter)))


def friction_limit(gamma: float) -> float:
    """The finite supersonic ceiling on ``4fL*/D``, for a caption."""
    return fanno.friction_parameter_limit(PerfectGas(gamma=float(gamma)))


# ---------------------------------------------------------------------------
# solve modes
# ---------------------------------------------------------------------------


class SolveMode(StrEnum):
    """What the user supplies for the state calculator."""

    MACH = "mach"
    #: ``4 f L*/D``, inverted numerically on an explicitly chosen branch.
    FRICTION = "friction"


@dataclass(frozen=True, slots=True)
class SolveModeInfo:
    mode: SolveMode
    label: str
    symbol: str
    unit: str
    hint: str
    iterative: bool
    needs_branch: bool
    default_value: float


SOLVE_MODES: tuple[SolveModeInfo, ...] = (
    SolveModeInfo(SolveMode.MACH, "Mach number", "M", "",
                  "greater than 0", False, False, 0.5),
    SolveModeInfo(SolveMode.FRICTION, "Friction parameter", "4f_F L*/D", "",
                  "0 or greater; the branch decides which duct",
                  True, True, 1.0690603127),
)

_MODE_INDEX = {info.mode: info for info in SOLVE_MODES}


def mode_info(mode: SolveMode | str) -> SolveModeInfo:
    return _MODE_INDEX[SolveMode(mode)]


def _branch_of(value: FlowBranch | str) -> FlowBranch:
    return value if isinstance(value, FlowBranch) else FlowBranch(str(value))


# ---------------------------------------------------------------------------
# the state calculator
# ---------------------------------------------------------------------------


def _state_rows(mach: float, gas: PerfectGas) -> tuple[ResultRow, ...]:
    record = fanno.state(mach, gas)
    limit = fanno.friction_parameter_limit(gas)
    supersonic = mach > 1.0
    return (
        ResultRow("mach", "Mach number  M", record.mach, "", "Flow", emphasis=True),

        ResultRow("temperature_ratio", "T/T*", record.temperature_ratio, "",
                  "Starred state", emphasis=True),
        ResultRow("pressure_ratio", "p/p*", record.pressure_ratio, "",
                  "Starred state", emphasis=True),
        ResultRow("density_ratio", "ρ/ρ*", record.density_ratio, "", "Starred state"),
        ResultRow("velocity_ratio", "V/V*", record.velocity_ratio, "", "Starred state"),
        ResultRow("stagnation_pressure_ratio", "p₀/p₀*",
                  record.stagnation_pressure_ratio, "", "Starred state", emphasis=True),
        # Stated as a literal because that is exactly what an adiabatic duct
        # does to stagnation temperature. A computed 0.9999999 would invite the
        # reader to wonder whether something had been lost.
        ResultRow("stagnation_temperature_ratio", "T₀/T₀*", 1.0, "", "Starred state"),

        ResultRow("friction_parameter", "4f_F L*/D to sonic",
                  record.friction_parameter, "", "Choking limit", emphasis=True),
        # The same number, and deliberately so: 4 f_F L*/D and f_D L*/D are one
        # group. A reader holding a Darcy friction factor can use the value
        # directly, and saying so here is cheaper than letting them divide by
        # four out of caution.
        ResultRow("darcy_parameter", "f_D L*/D to sonic  (identical group)",
                  record.friction_parameter, "", "Choking limit"),
        ResultRow("supersonic_limit", "Supersonic ceiling on 4f_F L*/D",
                  limit if supersonic else None, "", "Choking limit"),
    )


def _status_for(mach: float, diagnostics: tuple[Diagnostic, ...]) -> tuple[str, str]:
    if mach == 1.0:
        return "Sonic", (
            "The choking state: no duct remains, and friction cannot take the flow "
            "past it."
        )
    if any(d.code == "NEAR_SONIC" for d in diagnostics):
        return "Near sonic", next(d.message for d in diagnostics if d.code == "NEAR_SONIC")
    if mach < 1.0:
        return "Subsonic", (
            "Friction accelerates the flow towards M = 1: p, T and ρ fall, V rises, "
            "and stagnation pressure is lost."
        )
    return "Supersonic", (
        "Friction decelerates the flow towards M = 1: p, T and ρ rise, V falls, and "
        "stagnation pressure is still lost -- adiabatic is not isentropic."
    )


def solve(mode: SolveMode | str, value: float, gamma: float,
          branch: FlowBranch | str = FlowBranch.SUBSONIC) -> CalculatorResult:
    """Solve the Fanno state from one known quantity.

    Args:
        mode: Whether ``value`` is a Mach number or ``4 f L*/D``.
        value: The known quantity.
        gamma: Ratio of specific heats.
        branch: Which duct is meant. Used only by the friction-parameter mode,
            where the parameter falls to zero from both sides of sonic and the
            equations cannot say which root the caller wants.
    """
    info = mode_info(mode)
    try:
        gas = PerfectGas(gamma=float(gamma))
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error))

    diagnostics: tuple[Diagnostic, ...] = gas.diagnostics
    used = ""

    try:
        number = float(value)
        if info.mode is SolveMode.MACH:
            mach = number
            fanno.temperature_ratio(mach, gas)          # domain check
            used = "subsonic" if mach < 1.0 else ("sonic" if mach == 1.0 else "supersonic")
        else:
            chosen = _branch_of(branch)
            solution = fanno.mach_from_friction_parameter(number, gas, chosen)
            if not solution.ok:
                return CalculatorResult(
                    False, None, (), "No solution",
                    "; ".join(d.message for d in solution.diagnostics),
                    solution.diagnostics, branch_used=str(chosen),
                )
            mach = solution.unwrap()
            used = str(chosen)
            diagnostics = diagnostics + tuple(
                d for d in solution.diagnostics if d.code != "EXTRAPOLATED_GAMMA")
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)
    except (TypeError, ValueError) as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)

    try:
        rows = _state_rows(mach, gas)
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)

    status, message = _status_for(mach, diagnostics)
    return CalculatorResult(True, mach, rows, status, message, diagnostics,
                            branch_used=used)


# ---------------------------------------------------------------------------
# the duct segment
# ---------------------------------------------------------------------------


def duct_segment(mach1: float, duct_parameter: float, gamma: float) -> CalculatorResult:
    """Run a duct of ``4 f L/D`` from an inlet Mach number and report the outlet.

    Args:
        mach1: Inlet Mach number.
        duct_parameter: ``4 f_Fanning L / D`` of the real duct. Callers holding
            a dimensional duct should build this with
            :func:`duct_parameter_from_geometry` first.
        gamma: Ratio of specific heats.

    A duct longer than the flow can sustain returns ``ok=False`` with the
    requested and available lengths both preserved in the message. It is a
    genuine engineering answer -- the flow chokes and the upstream condition
    must change -- and is never reported as a truncated duct or as an outlet on
    the other branch.
    """
    try:
        gas = PerfectGas(gamma=float(gamma))
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error))

    try:
        solution = fanno.downstream_mach(float(mach1), float(duct_parameter), gas)
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error),
                                gas.diagnostics)
    except (TypeError, ValueError) as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error),
                                gas.diagnostics)

    if not solution.ok:
        choked = next((d for d in solution.diagnostics
                       if d.code == "FRICTION_CHOKED"), None)
        rows: tuple[ResultRow, ...] = ()
        if choked is not None:
            detail = choked.detail or {}
            requested = float(detail.get("duct_parameter", float(duct_parameter)))
            available = float(detail.get("available", float("nan")))
            rows = (
                ResultRow("mach1", "Inlet Mach  M₁", float(mach1), "", "Flow"),
                ResultRow("duct_parameter", "Requested 4f_F L/D", requested, "",
                          "Choking limit", emphasis=True),
                ResultRow("available", "Available before M = 1", available, "",
                          "Choking limit", emphasis=True),
                ResultRow("excess", "Excess length", requested - available, "",
                          "Choking limit"),
                ResultRow("fraction", "Requested / available",
                          requested / available if available else None, "",
                          "Choking limit"),
            )
        return CalculatorResult(
            False, None, rows, "Choked",
            "; ".join(d.message for d in solution.diagnostics),
            solution.diagnostics,
        )

    result = solution.unwrap()
    upstream, downstream = result.upstream, result.downstream
    rows = (
        ResultRow("mach1", "Inlet Mach  M₁", upstream.mach, "", "Flow"),
        ResultRow("mach2", "Outlet Mach  M₂", downstream.mach, "", "Flow", emphasis=True),
        ResultRow("duct_parameter", "Duct 4f_F L/D", result.duct_parameter, "", "Flow"),

        ResultRow("pressure_ratio_12", "p₂/p₁", result.pressure_ratio_12, "",
                  "Change across the duct", emphasis=True),
        ResultRow("temperature_ratio_12", "T₂/T₁", result.temperature_ratio_12, "",
                  "Change across the duct"),
        ResultRow("stagnation_pressure_ratio_12", "p₀₂/p₀₁",
                  result.stagnation_pressure_ratio_12, "", "Change across the duct",
                  emphasis=True),
        ResultRow("stagnation_temperature_ratio_12", "T₀₂/T₀₁", 1.0, "",
                  "Change across the duct"),

        ResultRow("available", "4f_F L*/D available at inlet",
                  upstream.friction_parameter, "", "Choking limit"),
        ResultRow("remaining", "4f_F L*/D still available at outlet",
                  result.remaining_to_choking, "", "Choking limit", emphasis=True),
        ResultRow("used_fraction", "Fraction of the available length used",
                  (result.duct_parameter / upstream.friction_parameter
                   if upstream.friction_parameter else None), "", "Choking limit"),
    )

    if result.choked:
        status = "Choked at outlet"
        message = ("The duct is exactly the choking length: the flow reaches M = 1 at "
                   "the outlet and no further length can be added.")
    elif downstream.mach < 1.0:
        status = "Subsonic"
        message = ("Friction has accelerated the flow towards sonic. Stagnation "
                   "pressure has fallen; stagnation temperature has not changed.")
    else:
        status = "Supersonic"
        message = ("Friction has decelerated the flow towards sonic. Stagnation "
                   "pressure has fallen; stagnation temperature has not changed.")
    if any(d.code == "NEAR_SONIC" for d in solution.diagnostics):
        status = "Near sonic"

    return CalculatorResult(True, downstream.mach, rows, status, message,
                            solution.diagnostics)


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------


class TableBranch(StrEnum):
    """Which side of sonic a generated table covers."""

    BOTH = "both"
    SUBSONIC = "subsonic"
    SUPERSONIC = "supersonic"


_COLUMNS = (
    TableColumn("mach", "M", "", 4),
    TableColumn("temperature_ratio", "T/T*", "", 6),
    TableColumn("pressure_ratio", "p/p*", "", 6),
    TableColumn("density_ratio", "ρ/ρ*", "", 6),
    TableColumn("stagnation_pressure_ratio", "p₀/p₀*", "", 6),
    TableColumn("friction_parameter", "4f_F L*/D", "", 6),
)


def columns_for(_branch: TableBranch | str = TableBranch.BOTH) -> tuple[TableColumn, ...]:
    """The column set. One set: the branch changes which rows appear, not which
    quantities are printed."""
    return _COLUMNS


def mach_grid(start: float, end: float, step: float,
              branch: TableBranch | str = TableBranch.BOTH) -> np.ndarray:
    """The Mach values a Fanno table contains.

    The sonic point is inserted if the range spans it and the step misses it:
    ``4fL*/D`` is zero there and it is the choking limit the whole page is
    about, so a table that steps straight over it is missing its most important
    row. ``03`` section 8.7 asks for the two branches to be distinguishable,
    which the branch filter does by selection rather than by hiding the sonic
    state.
    """
    if not np.isfinite([start, end, step]).all():
        raise ValueError("Mach range and step must be finite numbers.")
    if step <= 0.0:
        raise ValueError("Step must be greater than zero.")
    if start <= 0.0:
        raise ValueError(
            "Start Mach must be greater than zero: every Fanno starred ratio diverges "
            "at rest, and the Fanno line does not reach it."
        )
    if end <= start:
        raise ValueError("End Mach must be greater than start Mach.")

    count = int(np.floor((end - start) / step + 1e-9)) + 1
    if count > MAX_TABLE_ROWS:
        raise ValueError(
            f"That range and step would produce {count:,} rows, above the "
            f"{MAX_TABLE_ROWS:,} row limit. Increase the step or narrow the range."
        )
    grid = start + step * np.arange(count, dtype=np.float64)

    if grid[0] < 1.0 < grid[-1] and not np.any(np.isclose(grid, 1.0, atol=1e-12)):
        grid = np.sort(np.append(grid, 1.0))

    branch = TableBranch(branch)
    if branch is TableBranch.SUBSONIC:
        grid = grid[grid <= 1.0 + 1e-12]
    elif branch is TableBranch.SUPERSONIC:
        grid = grid[grid >= 1.0 - 1e-12]
    if grid.size == 0:
        raise ValueError(
            f"No {branch.value} rows fall in M = {start:g} to {end:g}. Widen the range "
            "or change the branch filter."
        )
    return grid


def generate_table(gamma: float, start: float, end: float, step: float,
                   branch: TableBranch | str = TableBranch.BOTH) -> TableData:
    """Compute a Fanno table over a Mach range, entirely from the physics layer.

    Vectorised: one call per column rather than one per row. The published
    table is never read to produce a value here; it is only ever compared
    against.
    """
    gas = PerfectGas(gamma=float(gamma))
    grid = mach_grid(start, end, step, branch)

    block = np.column_stack([
        grid,
        np.asarray(fanno.temperature_ratio(grid, gas)),
        np.asarray(fanno.pressure_ratio(grid, gas)),
        np.asarray(fanno.density_ratio(grid, gas)),
        np.asarray(fanno.stagnation_pressure_ratio(grid, gas)),
        np.asarray(fanno.friction_parameter(grid, gas)),
    ])

    sonic = np.flatnonzero(np.isclose(grid, 1.0, atol=1e-12))
    sonic_row = int(sonic[0]) if sonic.size else None

    return TableData(
        columns=columns_for(branch),
        values=block,
        gamma=gas.gamma,
        convention=TableBranch(branch),
        sonic_row=sonic_row,
        markers={sonic_row: "SONIC · CHOKING LIMIT"} if sonic_row is not None else {},
        message="",
        metadata={
            "start": float(grid[0]),
            "end": float(grid[-1]),
            "step": float(step),
            "rows": int(grid.size),
            "model": "perfect_gas_fanno_v1",
            "friction_convention": "Fanning, 4 f_F L*/D",
            "supersonic_limit": fanno.friction_parameter_limit(gas),
        },
    )
