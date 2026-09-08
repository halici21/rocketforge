"""Rayleigh analysis, prepared for presentation.

The adapter between ``rocketforge.physics.compressible.rayleigh`` and whatever
displays it. It owns no gas dynamics: every number here comes from a physics
call.

**The presentation problem this file exists to solve.** Rayleigh flow has two
critical Mach numbers and they mean different things:

* ``M = 1`` is where ``T0/T0*`` peaks, which is the thermal choking limit;
* ``M = 1/sqrt(gamma)`` is where the *static* temperature peaks, and it is
  subsonic.

Between them the static temperature falls while heat is still going in. Showing
those two points with one label, or letting a coarse table step over the second,
would hide the single most instructive feature of the Rayleigh line -- so both
are surfaced explicitly, with separate labels, and the table inserts them.

Only one inverse exists, on ``T0/T0*``, with an explicit branch. ``T/T*`` is
not offered: it is two-valued on the subsonic branch, and ``03`` section 9.5
defers it rather than have the interface pick a root at random.

Deliberately free of Qt, so all of it can be tested headlessly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ...core.errors import RocketForgeError
from ...core.result import Diagnostic
from ...physics.compressible import FlowBranch, PerfectGas
from ...physics.compressible import rayleigh
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
    "mode_info",
    "HeatInput",
    "HEAT_INPUTS",
    "solve",
    "heat_transition",
    "critical_points",
    "generate_table",
    "columns_for",
    "TableBranch",
    "MAX_TABLE_ROWS",
]


# ---------------------------------------------------------------------------
# critical points
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CriticalPoints:
    """The two Mach numbers a Rayleigh page has to keep apart."""

    static_temperature_max_mach: float      # 1/sqrt(gamma)
    static_temperature_max_value: float     # (gamma+1)^2 / (4 gamma)
    sonic_mach: float                       # 1, where T0/T0* peaks at 1
    supersonic_t0_floor: float              # (gamma^2-1)/gamma^2


def critical_points(gamma: float) -> CriticalPoints:
    """Where the Rayleigh line turns, for captions, guides and table markers."""
    gas = PerfectGas(gamma=float(gamma))
    return CriticalPoints(
        static_temperature_max_mach=rayleigh.mach_at_maximum_temperature(gas),
        static_temperature_max_value=rayleigh.maximum_temperature_ratio(gas),
        sonic_mach=1.0,
        supersonic_t0_floor=rayleigh.stagnation_temperature_ratio_limit(gas),
    )


# ---------------------------------------------------------------------------
# solve modes
# ---------------------------------------------------------------------------


class SolveMode(StrEnum):
    """What the user supplies for the state calculator."""

    MACH = "mach"
    #: ``T0/T0*``, inverted numerically on an explicitly chosen branch. The
    #: only inverse in v1, and the one the heat question is built on.
    STAGNATION_TEMPERATURE = "stagnation_temperature_ratio"


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
    SolveModeInfo(SolveMode.STAGNATION_TEMPERATURE, "Stagnation temperature ratio",
                  "T₀/T₀*", "",
                  "0 to 1; the branch decides which duct", True, True, 0.6914),
)

_MODE_INDEX = {info.mode: info for info in SOLVE_MODES}


def mode_info(mode: SolveMode | str) -> SolveModeInfo:
    return _MODE_INDEX[SolveMode(mode)]


class HeatInput(StrEnum):
    """How the heat-transition workflow is posed."""

    RATIO = "ratio"          # T02/T01 directly
    HEAT = "heat"            # q [J/kg], needs R and T01


HEAT_INPUTS: tuple[tuple[str, str], ...] = (
    (HeatInput.RATIO.value, "Stagnation temperature ratio  T₀₂/T₀₁"),
    (HeatInput.HEAT.value, "Heat per unit mass  q"),
)


def _branch_of(value: FlowBranch | str) -> FlowBranch:
    return value if isinstance(value, FlowBranch) else FlowBranch(str(value))


# ---------------------------------------------------------------------------
# the state calculator
# ---------------------------------------------------------------------------


def _state_rows(mach: float, gas: PerfectGas) -> tuple[ResultRow, ...]:
    record = rayleigh.state(mach, gas)
    points = critical_points(gas.gamma)
    at_inlet = record.stagnation_temperature_ratio
    return (
        ResultRow("mach", "Mach number  M", record.mach, "", "Flow", emphasis=True),

        ResultRow("pressure_ratio", "p/p*", record.pressure_ratio, "",
                  "Starred state", emphasis=True),
        ResultRow("temperature_ratio", "T/T*", record.temperature_ratio, "",
                  "Starred state", emphasis=True),
        ResultRow("density_ratio", "ρ/ρ*", record.density_ratio, "", "Starred state"),
        ResultRow("stagnation_temperature_ratio", "T₀/T₀*",
                  record.stagnation_temperature_ratio, "", "Starred state",
                  emphasis=True),
        ResultRow("stagnation_pressure_ratio", "p₀/p₀*",
                  record.stagnation_pressure_ratio, "", "Starred state", emphasis=True),

        ResultRow("t_max_mach", "Static T maximum at  M = 1/√γ",
                  points.static_temperature_max_mach, "", "Critical points"),
        ResultRow("t_max_value", "(T/T*) at that maximum",
                  points.static_temperature_max_value, "", "Critical points"),
        ResultRow("sonic_mach", "Sonic / T₀ maximum at  M", points.sonic_mach, "",
                  "Critical points"),

        ResultRow("heat_margin", "T₀₂/T₀₁ still available before choking",
                  1.0 / at_inlet if at_inlet else None, "", "Heat / choking",
                  emphasis=True),
        ResultRow("t0_deficit", "1 − T₀/T₀*", 1.0 - at_inlet, "", "Heat / choking"),
    )


def _status_for(mach: float, gas: PerfectGas,
                diagnostics: tuple[Diagnostic, ...]) -> tuple[str, str]:
    points = critical_points(gas.gamma)
    peak = points.static_temperature_max_mach
    if mach == 1.0:
        return "Sonic", (
            "Thermal choking: T₀/T₀* is at its maximum of 1, and no further heat can "
            "be added on this Rayleigh line."
        )
    if any(d.code == "NEAR_SONIC" for d in diagnostics):
        return "Near sonic", next(d.message for d in diagnostics if d.code == "NEAR_SONIC")
    if mach < peak:
        return "Subsonic", (
            "Heating accelerates the flow towards M = 1. Below M = 1/√γ the static "
            "temperature is still rising with the heat added."
        )
    if mach < 1.0:
        return "Subsonic", (
            f"Between M = 1/√γ = {peak:.4f} and M = 1 the static temperature falls "
            "while heat is still being added: the flow is accelerating fast enough "
            "that the kinetic-energy rise outruns the heat. T₀ keeps rising throughout."
        )
    return "Supersonic", (
        "Heating decelerates the flow towards M = 1. Static pressure and temperature "
        "rise, and stagnation pressure falls -- the Rayleigh loss acts on both branches."
    )


def solve(mode: SolveMode | str, value: float, gamma: float,
          branch: FlowBranch | str = FlowBranch.SUBSONIC) -> CalculatorResult:
    """Solve the Rayleigh state from one known quantity.

    Args:
        mode: Whether ``value`` is a Mach number or ``T0/T0*``.
        value: The known quantity.
        gamma: Ratio of specific heats.
        branch: Which duct is meant. Used only by the ``T0/T0*`` mode, where
            the ratio rises to 1 from both sides and every attainable value has
            a subsonic and a supersonic root.
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
            rayleigh.temperature_ratio(mach, gas)          # domain check
            used = "subsonic" if mach < 1.0 else ("sonic" if mach == 1.0 else "supersonic")
        else:
            chosen = _branch_of(branch)
            solution = rayleigh.mach_from_stagnation_temperature_ratio(
                number, gas, chosen)
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

    status, message = _status_for(mach, gas, diagnostics)
    return CalculatorResult(True, mach, rows, status, message, diagnostics,
                            branch_used=used)


# ---------------------------------------------------------------------------
# the heat transition
# ---------------------------------------------------------------------------


def heat_transition(mach1: float, gamma: float, *,
                    heat_input: HeatInput | str = HeatInput.RATIO,
                    ratio: float = 1.0,
                    heat: float = 0.0,
                    gas_constant: float = 287.0528,
                    stagnation_temperature_1: float = 300.0) -> CalculatorResult:
    """Heat (or cool) a duct from an inlet Mach number and report the outlet.

    Args:
        mach1: Inlet Mach number.
        gamma: Ratio of specific heats.
        heat_input: Whether the heat is given as ``T02/T01`` or as ``q``.
        ratio: ``T02/T01`` when that is the input. Above 1 heats, below 1 cools.
        heat: ``q`` in J/kg when that is the input. Positive heats.
        gas_constant: R, needed only to turn ``q`` into a temperature rise.
        stagnation_temperature_1: T01 in kelvin, needed for the same reason.

    Heat beyond the choking limit returns ``ok=False`` with the requested and
    maximum ratios preserved. That is a real engineering answer -- the flow
    chokes and the upstream condition must change -- and is never silently
    clamped to the sonic value or solved on the other branch.
    """
    heat_input = HeatInput(heat_input)
    try:
        gas = (PerfectGas(gamma=float(gamma), gas_constant=float(gas_constant))
               if heat_input is HeatInput.HEAT else PerfectGas(gamma=float(gamma)))
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error))

    # q -> T02/T01 through cp, which comes from the gas model and is not
    # restated here. No combustion, no chemistry: imposed heat transfer only.
    if heat_input is HeatInput.HEAT:
        t01 = float(stagnation_temperature_1)
        if not np.isfinite(t01) or t01 <= 0.0:
            return CalculatorResult(False, None, (), "Invalid input",
                                    "Inlet stagnation temperature must be positive.",
                                    gas.diagnostics)
        try:
            requested_ratio = 1.0 + float(heat) / (gas.cp * t01)
        except RocketForgeError as error:
            return CalculatorResult(False, None, (), "Invalid input", str(error),
                                    gas.diagnostics)
    else:
        requested_ratio = float(ratio)

    try:
        solution = rayleigh.heat_addition(float(mach1), requested_ratio, gas)
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error),
                                gas.diagnostics)
    except (TypeError, ValueError) as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error),
                                gas.diagnostics)

    if not solution.ok:
        choked = next((d for d in solution.diagnostics
                       if d.code == "THERMALLY_CHOKED"), None)
        rows: tuple[ResultRow, ...] = ()
        if choked is not None:
            detail = choked.detail or {}
            requested = float(detail.get("requested", requested_ratio))
            maximum = float(detail.get("maximum", float("nan")))
            rows = (
                ResultRow("mach1", "Inlet Mach  M₁", float(mach1), "", "Flow"),
                ResultRow("requested_ratio", "Requested T₀₂/T₀₁", requested, "",
                          "Heat / choking", emphasis=True),
                ResultRow("maximum_ratio", "Maximum before M = 1", maximum, "",
                          "Heat / choking", emphasis=True),
                ResultRow("excess_ratio", "Excess", requested - maximum, "",
                          "Heat / choking"),
                ResultRow("fraction", "Requested / maximum",
                          requested / maximum if maximum else None, "", "Heat / choking"),
            )
            if heat_input is HeatInput.HEAT:
                t01 = float(stagnation_temperature_1)
                rows = rows + (
                    ResultRow("requested_heat", "Requested q", float(heat), "J/kg",
                              "Heat / choking"),
                    ResultRow("maximum_heat", "Maximum q before choking",
                              gas.cp * t01 * (maximum - 1.0), "J/kg",
                              "Heat / choking", emphasis=True),
                )
        return CalculatorResult(
            False, None, rows, "Choked",
            "; ".join(d.message for d in solution.diagnostics),
            solution.diagnostics,
        )

    result = solution.unwrap()
    upstream, downstream = result.upstream, result.downstream
    at_inlet = upstream.stagnation_temperature_ratio
    maximum_ratio = 1.0 / at_inlet if at_inlet else float("nan")

    rows = (
        ResultRow("mach1", "Inlet Mach  M₁", upstream.mach, "", "Flow"),
        ResultRow("mach2", "Outlet Mach  M₂", downstream.mach, "", "Flow", emphasis=True),
        ResultRow("stagnation_temperature_ratio_12", "T₀₂/T₀₁",
                  result.stagnation_temperature_ratio_12, "", "Flow"),

        ResultRow("pressure_ratio_12", "p₂/p₁", result.pressure_ratio_12, "",
                  "Change across the duct", emphasis=True),
        ResultRow("temperature_ratio_12", "T₂/T₁", result.temperature_ratio_12, "",
                  "Change across the duct"),
        ResultRow("stagnation_pressure_ratio_12", "p₀₂/p₀₁",
                  result.stagnation_pressure_ratio_12, "", "Change across the duct",
                  emphasis=True),

        ResultRow("inlet_t0_ratio", "T₀₁/T₀* at inlet", at_inlet, "", "Heat / choking"),
        ResultRow("outlet_t0_ratio", "T₀₂/T₀* at outlet",
                  downstream.stagnation_temperature_ratio, "", "Heat / choking"),
        ResultRow("maximum_ratio", "Maximum T₀₂/T₀₁ before choking", maximum_ratio, "",
                  "Heat / choking", emphasis=True),
        ResultRow("margin", "Margin still available",
                  maximum_ratio - result.stagnation_temperature_ratio_12, "",
                  "Heat / choking"),
    )

    if heat_input is HeatInput.HEAT:
        t01 = float(stagnation_temperature_1)
        rows = rows + (
            ResultRow("heat", "Heat added  q", float(heat), "J/kg", "Dimensional heat",
                      emphasis=True),
            ResultRow("cp", "cp", gas.cp, "J/(kg·K)", "Dimensional heat"),
            ResultRow("t01", "T₀₁", t01, "K", "Dimensional heat"),
            ResultRow("t02", "T₀₂", t01 * result.stagnation_temperature_ratio_12, "K",
                      "Dimensional heat"),
            ResultRow("maximum_heat", "Maximum q before choking",
                      gas.cp * t01 * (maximum_ratio - 1.0), "J/kg", "Dimensional heat"),
        )

    if result.thermally_choked:
        status = "Choked at outlet"
        message = ("Exactly the choking heat: the flow reaches M = 1 at the outlet and "
                   "no more can be added on this line.")
    elif result.stagnation_temperature_ratio_12 < 1.0:
        status = "Cooled"
        message = ("Cooling moves the flow away from sonic: subsonic towards M = 0, "
                   "supersonic towards higher Mach.")
    elif downstream.mach < 1.0:
        status = "Subsonic"
        message = ("Heating has accelerated the flow towards sonic. Stagnation "
                   "pressure has fallen: the Rayleigh loss.")
    else:
        status = "Supersonic"
        message = ("Heating has decelerated the flow towards sonic. Stagnation "
                   "pressure has fallen: the Rayleigh loss acts on this branch too.")
    if any(d.code == "NEAR_SONIC" for d in solution.diagnostics):
        status = "Near sonic"

    return CalculatorResult(True, downstream.mach, rows, status, message,
                            solution.diagnostics)


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------


class TableBranch(StrEnum):
    BOTH = "both"
    SUBSONIC = "subsonic"
    SUPERSONIC = "supersonic"


_COLUMNS = (
    TableColumn("mach", "M", "", 4),
    TableColumn("pressure_ratio", "p/p*", "", 6),
    TableColumn("temperature_ratio", "T/T*", "", 6),
    TableColumn("density_ratio", "ρ/ρ*", "", 6),
    TableColumn("stagnation_pressure_ratio", "p₀/p₀*", "", 6),
    TableColumn("stagnation_temperature_ratio", "T₀/T₀*", "", 6),
)


def columns_for(_branch: TableBranch | str = TableBranch.BOTH) -> tuple[TableColumn, ...]:
    return _COLUMNS


def mach_grid(gamma: float, start: float, end: float, step: float,
              branch: TableBranch | str = TableBranch.BOTH) -> np.ndarray:
    """The Mach values a Rayleigh table contains, with both critical points in.

    ``03`` section 9.6 is explicit that the static-temperature maximum must not
    be stepped over: it is the most instructive feature of the line, and a grid
    that misses it makes T/T* look monotone. Both M = 1 and M = 1/sqrt(gamma)
    are therefore inserted when the range spans them.
    """
    if not np.isfinite([start, end, step]).all():
        raise ValueError("Mach range and step must be finite numbers.")
    if step <= 0.0:
        raise ValueError("Step must be greater than zero.")
    if start <= 0.0:
        raise ValueError("Start Mach must be greater than zero.")
    if end <= start:
        raise ValueError("End Mach must be greater than start Mach.")

    count = int(np.floor((end - start) / step + 1e-9)) + 1
    if count > MAX_TABLE_ROWS:
        raise ValueError(
            f"That range and step would produce {count:,} rows, above the "
            f"{MAX_TABLE_ROWS:,} row limit. Increase the step or narrow the range."
        )
    grid = start + step * np.arange(count, dtype=np.float64)

    peak = 1.0 / np.sqrt(float(gamma))
    for critical in (peak, 1.0):
        if grid[0] < critical < grid[-1] and not np.any(
                np.isclose(grid, critical, atol=1e-12)):
            grid = np.append(grid, critical)
    grid = np.unique(np.sort(grid))

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
    """Compute a Rayleigh table over a Mach range, entirely from the physics layer.

    The two critical rows are marked *differently*. Labelling both "critical"
    would suggest they are the same kind of point, when one is the choking
    limit and the other is a static-temperature maximum that is not choked at
    all.
    """
    gas = PerfectGas(gamma=float(gamma))
    grid = mach_grid(gas.gamma, start, end, step, branch)

    block = np.column_stack([
        grid,
        np.asarray(rayleigh.pressure_ratio(grid, gas)),
        np.asarray(rayleigh.temperature_ratio(grid, gas)),
        np.asarray(rayleigh.density_ratio(grid, gas)),
        np.asarray(rayleigh.stagnation_pressure_ratio(grid, gas)),
        np.asarray(rayleigh.stagnation_temperature_ratio(grid, gas)),
    ])

    points = critical_points(gas.gamma)
    markers: dict[int, str] = {}
    sonic = np.flatnonzero(np.isclose(grid, 1.0, atol=1e-12))
    sonic_row = int(sonic[0]) if sonic.size else None
    if sonic_row is not None:
        markers[sonic_row] = "SONIC · T₀ MAX"
    peak = np.flatnonzero(np.isclose(grid, points.static_temperature_max_mach,
                                     atol=1e-12))
    if peak.size:
        markers[int(peak[0])] = "STATIC T MAX"

    return TableData(
        columns=columns_for(branch),
        values=block,
        gamma=gas.gamma,
        convention=TableBranch(branch),
        sonic_row=sonic_row,
        markers=markers,
        message="",
        metadata={
            "start": float(grid[0]),
            "end": float(grid[-1]),
            "step": float(step),
            "rows": int(grid.size),
            "model": "perfect_gas_rayleigh_v1",
            "static_temperature_max_mach": points.static_temperature_max_mach,
            "static_temperature_max_value": points.static_temperature_max_value,
            "supersonic_t0_floor": points.supersonic_t0_floor,
        },
    )
