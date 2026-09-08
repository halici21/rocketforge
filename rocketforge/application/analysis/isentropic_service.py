"""Isentropic analysis, prepared for presentation.

The adapter between the verified physics of
``rocketforge.physics.compressible`` and whatever displays it. It owns no gas
dynamics: every number here comes from a physics call, and the only arithmetic
performed is the reciprocal that turns RocketForge's canonical
static-over-stagnation ratios into the stagnation-over-static orientation the
classical tables print.

That reciprocal is a *representation* transform, not a second implementation.
``p0/p`` is ``1 / pressure_ratio(M, gas)`` and nothing else; there is no
second-opinion formula anywhere in this file.

Deliberately free of Qt, so the whole of it can be tested headlessly and reused
by a script or a report generator.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ...core.errors import RocketForgeError
from ...core.result import Diagnostic, Severity, Status
from ...core.tolerances import DEFAULT_TOLERANCES
from ...physics.compressible import FlowBranch, PerfectGas
from ...physics.compressible import isentropic as iso
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
    "TableConvention",
    "ResultRow",
    "CalculatorResult",
    "TableColumn",
    "TableData",
    "solve",
    "generate_table",
    "MAX_TABLE_ROWS",
]

class SolveMode(StrEnum):
    """What the user supplies, from which everything else follows.

    Every mode maps onto a relation that Phase 4B implemented and verified.
    There are no modes here that the physics layer cannot answer.
    """

    MACH = "mach"
    PRESSURE_RATIO = "p_over_p0"
    PRESSURE_RATIO_INVERSE = "p0_over_p"
    TEMPERATURE_RATIO = "T_over_T0"
    TEMPERATURE_RATIO_INVERSE = "T0_over_T"
    DENSITY_RATIO = "rho_over_rho0"
    DENSITY_RATIO_INVERSE = "rho0_over_rho"
    AREA_RATIO = "area_ratio"


@dataclass(frozen=True, slots=True)
class SolveModeInfo:
    """How one solve mode presents itself and what it needs."""

    mode: SolveMode
    label: str
    symbol: str
    hint: str
    reciprocal: bool          # user value must be inverted before the physics call
    needs_branch: bool
    default_value: float


#: The ordered menu the interface offers. Reciprocal modes exist because that
#: is how the classical tables are written, and a user reading from one should
#: not have to invert by hand.
SOLVE_MODES: tuple[SolveModeInfo, ...] = (
    SolveModeInfo(SolveMode.MACH, "Mach number", "M",
                  "0 or greater", False, False, 2.0),
    SolveModeInfo(SolveMode.PRESSURE_RATIO, "Pressure ratio", "p/p₀",
                  "0 to 1", False, False, 0.1278045255),
    SolveModeInfo(SolveMode.PRESSURE_RATIO_INVERSE, "Pressure ratio", "p₀/p",
                  "1 or greater", True, False, 7.824),
    SolveModeInfo(SolveMode.TEMPERATURE_RATIO, "Temperature ratio", "T/T₀",
                  "0 to 1", False, False, 0.5555555556),
    SolveModeInfo(SolveMode.TEMPERATURE_RATIO_INVERSE, "Temperature ratio", "T₀/T",
                  "1 or greater", True, False, 1.8),
    SolveModeInfo(SolveMode.DENSITY_RATIO, "Density ratio", "ρ/ρ₀",
                  "0 to 1", False, False, 0.2300481458),
    SolveModeInfo(SolveMode.DENSITY_RATIO_INVERSE, "Density ratio", "ρ₀/ρ",
                  "1 or greater", True, False, 4.347),
    SolveModeInfo(SolveMode.AREA_RATIO, "Area ratio", "A/A*",
                  "1 or greater", False, True, 2.0),
)

_MODE_INDEX = {info.mode: info for info in SOLVE_MODES}


def mode_info(mode: SolveMode | str) -> SolveModeInfo:
    """Descriptor for a solve mode."""
    return _MODE_INDEX[SolveMode(mode)]


class TableConvention(StrEnum):
    """Which way up the generated table prints its ratios.

    Two conventions for the same physics. ``ANDERSON`` matches the classical
    textbook appendices, which a reader will want to compare against;
    ``STANDARD`` matches RocketForge's canonical orientation.
    """

    ANDERSON = "anderson"
    STANDARD = "standard"


# ---------------------------------------------------------------------------
# calculator
# ---------------------------------------------------------------------------


def _rows_for(mach: float, gas: PerfectGas) -> tuple[ResultRow, ...]:
    """Every displayed quantity at one Mach number.

    All from the physics layer. The reciprocals are computed here, once each,
    from the canonical ratio -- never from a separate formula.
    """
    ratios = iso.ratios_from_mach(mach, gas)
    t, p, r = ratios.temperature_ratio, ratios.pressure_ratio, ratios.density_ratio
    angle = ratios.mach_angle

    return (
        ResultRow("mach", "Mach number", ratios.mach, "", "Flow", emphasis=True),
        ResultRow("mach_angle", "Mach angle μ",
                  None if angle is None else np.degrees(angle), "°", "Flow"),

        ResultRow("T_over_T0", "T/T₀", t, "", "Static / stagnation"),
        ResultRow("T0_over_T", "T₀/T", 1.0 / t, "", "Static / stagnation"),
        ResultRow("p_over_p0", "p/p₀", p, "", "Static / stagnation"),
        ResultRow("p0_over_p", "p₀/p", 1.0 / p, "", "Static / stagnation"),
        ResultRow("rho_over_rho0", "ρ/ρ₀", r, "", "Static / stagnation"),
        ResultRow("rho0_over_rho", "ρ₀/ρ", 1.0 / r, "", "Static / stagnation"),

        ResultRow("T_over_Tstar", "T/T*", ratios.temperature_ratio_star, "", "Sonic reference"),
        ResultRow("p_over_pstar", "p/p*", ratios.pressure_ratio_star, "", "Sonic reference"),
        ResultRow("rho_over_rhostar", "ρ/ρ*", ratios.density_ratio_star, "", "Sonic reference"),

        ResultRow("area_ratio", "A/A*", ratios.area_ratio, "", "Geometric", emphasis=True),
    )


def _status_for(mach: float, diagnostics: tuple[Diagnostic, ...]) -> tuple[str, str]:
    """The compact state indicator and its one-line explanation."""
    codes = {d.code for d in diagnostics}
    if "SONIC_EXACT" in codes or mach == 1.0:
        return "Sonic", "Flow is exactly at the sonic condition."
    if "NEAR_SONIC" in codes:
        return "Near sonic", (
            "Close to the sonic point, where the area relation is flat: the Mach "
            "number is less precisely determined than the area ratio."
        )
    if any(d.severity is Severity.WARNING for d in diagnostics):
        return "Valid", "; ".join(d.message for d in diagnostics)
    return "Valid", ""


def solve(
    mode: SolveMode | str,
    value: float,
    gamma: float,
    branch: FlowBranch | str = FlowBranch.SUBSONIC,
) -> CalculatorResult:
    """Solve the isentropic state from one known quantity.

    Args:
        mode: Which quantity ``value`` is.
        value: The known quantity, in the orientation the mode names.
        gamma: Ratio of specific heats.
        branch: Required when ``mode`` is the area ratio; ignored otherwise.
            ``FlowBranch.BOTH`` returns both roots.

    Returns:
        A :class:`CalculatorResult`. Invalid input produces ``ok=False`` with a
        readable message rather than an exception, because a partially-typed
        number is an ordinary event in a live interface -- but the underlying
        physics still raises, and this function is the only place that catches.
    """
    info = mode_info(mode)
    try:
        gas = PerfectGas(gamma=float(gamma))
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error))

    diagnostics: tuple[Diagnostic, ...] = gas.diagnostics
    both: tuple[float, float] | None = None
    branch_used = ""

    try:
        number = float(value)
        if info.mode is SolveMode.MACH:
            mach = number
            iso.temperature_ratio(mach, gas)          # domain check
        elif info.mode is SolveMode.AREA_RATIO:
            wanted = FlowBranch(branch)
            if wanted is FlowBranch.BOTH:
                solution = iso.mach_from_area_ratio_both(number, gas)
                pair = solution.unwrap()
                both = (pair.subsonic, pair.supersonic)
                mach = pair.supersonic
                branch_used = "both"
            else:
                solution = iso.mach_from_area_ratio(number, gas, wanted)
                if not solution.ok:
                    return CalculatorResult(
                        False, None, (), "Not converged",
                        "; ".join(d.message for d in solution.diagnostics),
                        solution.diagnostics,
                    )
                mach = solution.unwrap()
                branch_used = wanted.value
            diagnostics = diagnostics + tuple(
                d for d in solution.diagnostics if d.code != "EXTRAPOLATED_GAMMA"
            )
        else:
            # The reciprocal modes are a display convention, so the inversion
            # happens here and the canonical ratio is what reaches the physics.
            canonical = 1.0 / number if info.reciprocal else number
            if info.mode in (SolveMode.PRESSURE_RATIO, SolveMode.PRESSURE_RATIO_INVERSE):
                mach = float(iso.mach_from_pressure_ratio(canonical, gas))
            elif info.mode in (SolveMode.TEMPERATURE_RATIO, SolveMode.TEMPERATURE_RATIO_INVERSE):
                mach = float(iso.mach_from_temperature_ratio(canonical, gas))
            else:
                mach = float(iso.mach_from_density_ratio(canonical, gas))
    except ZeroDivisionError:
        return CalculatorResult(False, None, (), "Invalid input",
                                f"{info.symbol} cannot be zero.")
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)
    except (TypeError, ValueError) as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)

    if mach == 0.0 and info.mode is not SolveMode.MACH:
        rows = _rows_for(0.0, gas)
    else:
        try:
            rows = _rows_for(mach, gas)
        except RocketForgeError as error:
            return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)

    status, message = _status_for(mach, diagnostics)
    return CalculatorResult(True, mach, rows, status, message, diagnostics, branch_used, both)


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------

_ANDERSON_COLUMNS = (
    TableColumn("mach", "M", "", 4),
    TableColumn("p0_over_p", "p₀/p", "", 6),
    TableColumn("rho0_over_rho", "ρ₀/ρ", "", 6),
    TableColumn("T0_over_T", "T₀/T", "", 6),
    TableColumn("area_ratio", "A/A*", "", 6),
)

_STANDARD_COLUMNS = (
    TableColumn("mach", "M", "", 4),
    TableColumn("p_over_p0", "p/p₀", "", 6),
    TableColumn("rho_over_rho0", "ρ/ρ₀", "", 6),
    TableColumn("T_over_T0", "T/T₀", "", 6),
    TableColumn("area_ratio", "A/A*", "", 6),
)


def columns_for(convention: TableConvention | str) -> tuple[TableColumn, ...]:
    """The column set a convention prints."""
    return (_ANDERSON_COLUMNS if TableConvention(convention) is TableConvention.ANDERSON
            else _STANDARD_COLUMNS)


def mach_grid(start: float, end: float, step: float, include_sonic: bool = True) -> np.ndarray:
    """The Mach values a table will contain.

    Args:
        start: First Mach number, > 0. The area ratio is unbounded at rest, so
            a table cannot begin at exactly zero.
        end: Last Mach number.
        step: Spacing.
        include_sonic: Whether to insert M = 1 when it falls inside the range
            but the step would step over it.

    M = 1 is inserted rather than left out because it is the one row every
    reader looks for, and a grid of 0.02 steps starting at 0.03 would otherwise
    miss it entirely. The insertion is explicit and reported, never silent.
    """
    if not np.isfinite([start, end, step]).all():
        raise ValueError("Mach range and step must be finite numbers.")
    if step <= 0.0:
        raise ValueError("Step must be greater than zero.")
    if start <= 0.0:
        raise ValueError("Start Mach must be greater than zero: A/A* is unbounded at rest.")
    if end <= start:
        raise ValueError("End Mach must be greater than start Mach.")

    count = int(np.floor((end - start) / step + 1e-9)) + 1
    if count > MAX_TABLE_ROWS:
        raise ValueError(
            f"That range and step would produce {count:,} rows, above the "
            f"{MAX_TABLE_ROWS:,} row limit. Increase the step or narrow the range."
        )
    grid = start + step * np.arange(count, dtype=np.float64)

    if include_sonic and start < 1.0 < end and not np.any(np.isclose(grid, 1.0, atol=1e-12)):
        grid = np.sort(np.append(grid, 1.0))
    return grid


def generate_table(
    gamma: float,
    start: float,
    end: float,
    step: float,
    convention: TableConvention | str = TableConvention.ANDERSON,
    include_sonic: bool = True,
) -> TableData:
    """Compute an isentropic table over a Mach range.

    Every row is computed by the physics layer, vectorised: no table is ever
    read to produce a value here. Published tables are for comparison only.
    """
    gas = PerfectGas(gamma=float(gamma))
    grid = mach_grid(start, end, step, include_sonic)
    convention = TableConvention(convention)
    columns = columns_for(convention)

    # One vectorised call per quantity, not a Python loop per row.
    temperature = iso.temperature_ratio(grid, gas)
    pressure = iso.pressure_ratio(grid, gas)
    density = iso.density_ratio(grid, gas)
    area = iso.area_ratio(grid, gas)

    if convention is TableConvention.ANDERSON:
        block = np.column_stack([grid, 1.0 / pressure, 1.0 / density, 1.0 / temperature, area])
    else:
        block = np.column_stack([grid, pressure, density, temperature, area])

    sonic = np.flatnonzero(np.isclose(grid, 1.0, atol=1e-12))
    return TableData(
        columns=columns,
        values=block,
        gamma=gas.gamma,
        convention=convention,
        sonic_row=int(sonic[0]) if sonic.size else None,
        message="",
        metadata={
            "start": float(grid[0]),
            "end": float(grid[-1]),
            "step": float(step),
            "rows": int(grid.size),
            "model": "perfect_gas_isentropic_v1",
            "sonic_inserted": bool(
                include_sonic and start < 1.0 < end
                and not np.any(np.isclose(start + step * np.arange(
                    int(np.floor((end - start) / step + 1e-9)) + 1), 1.0, atol=1e-12))
            ),
        },
    )
