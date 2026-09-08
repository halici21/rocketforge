"""Prandtl-Meyer analysis, prepared for presentation.

The adapter between ``rocketforge.physics.compressible.prandtl_meyer`` and
whatever displays it. It owns no gas dynamics: every number here comes from a
physics call.

**This is where degrees exist.** The physics layer is radians throughout and a
name ending in ``_deg`` is forbidden there by the architecture test. An
engineer, a textbook and every published table use degrees, so the conversion
lives here -- at the boundary, in one place, applied on the way in and on the
way out. Nothing below this file ever sees a degree, and nothing above it ever
sees a radian.

Deliberately free of Qt, so all of it can be tested headlessly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ...core.errors import RocketForgeError
from ...core.result import Diagnostic, Severity
from ...physics.compressible import PerfectGas
from ...physics.compressible import isentropic as iso
from ...physics.compressible import prandtl_meyer as pm
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
    "solve",
    "expansion_turn",
    "generate_table",
    "columns_for",
    "TableConvention",
    "MAX_TABLE_ROWS",
    "nu_max_degrees",
]


def nu_max_degrees(gamma: float) -> float:
    """The maximum expansion for this gas, in degrees, for a caption.

    130.454 for air: the total turning available to expand to an infinite Mach
    number, and the hard ceiling on every inverse on this page.
    """
    return math.degrees(pm.nu_max(PerfectGas(gamma=float(gamma))))


class SolveMode(StrEnum):
    """What the user supplies, from which everything else follows."""

    MACH = "mach"
    #: The Prandtl-Meyer angle itself, in degrees. Inverted numerically.
    NU = "nu"


@dataclass(frozen=True, slots=True)
class SolveModeInfo:
    """How one solve mode presents itself and what it needs."""

    mode: SolveMode
    label: str
    symbol: str
    unit: str
    hint: str
    iterative: bool
    default_value: float


SOLVE_MODES: tuple[SolveModeInfo, ...] = (
    SolveModeInfo(SolveMode.MACH, "Mach number", "M", "",
                  "1 or greater", False, 2.0),
    SolveModeInfo(SolveMode.NU, "Prandtl-Meyer angle", "ν", "°",
                  "0 up to ν_max", True, 26.3797608134),
)

_MODE_INDEX = {info.mode: info for info in SOLVE_MODES}


def mode_info(mode: SolveMode | str) -> SolveModeInfo:
    """Descriptor for a solve mode."""
    return _MODE_INDEX[SolveMode(mode)]


# ---------------------------------------------------------------------------
# the state calculator
# ---------------------------------------------------------------------------


def _rows_for(mach: float, gas: PerfectGas) -> tuple[ResultRow, ...]:
    """Every displayed quantity at one Mach number, angles in degrees."""
    return (
        ResultRow("mach", "Mach number  M", mach, "", "Flow", emphasis=True),
        ResultRow("nu", "Prandtl-Meyer angle  ν", math.degrees(float(pm.nu(mach, gas))),
                  "°", "Flow", emphasis=True),
        ResultRow("mach_angle", "Mach angle  μ", math.degrees(float(pm.mach_angle(mach))),
                  "°", "Flow", emphasis=True),
        ResultRow("nu_max", "Maximum expansion  ν_max", math.degrees(pm.nu_max(gas)), "°",
                  "Flow"),
        ResultRow("nu_remaining", "Turning still available",
                  math.degrees(pm.nu_max(gas) - float(pm.nu(mach, gas))), "°", "Flow"),

        ResultRow("p_over_p0", "p/p₀", float(iso.pressure_ratio(mach, gas)), "",
                  "Stagnation state"),
        ResultRow("T_over_T0", "T/T₀", float(iso.temperature_ratio(mach, gas)), "",
                  "Stagnation state"),
        ResultRow("rho_over_rho0", "ρ/ρ₀", float(iso.density_ratio(mach, gas)), "",
                  "Stagnation state"),
        ResultRow("area_ratio", "A/A*", float(iso.area_ratio(mach, gas)), "",
                  "Stagnation state"),
    )


def _status_for(mach: float, diagnostics: tuple[Diagnostic, ...]) -> tuple[str, str]:
    """The compact state indicator and its one-line explanation."""
    if mach == 1.0:
        return "Sonic", (
            "At Mach 1 the Prandtl-Meyer angle is zero: this is the state every "
            "expansion is measured from."
        )
    if any(d.code == "NEAR_SONIC" for d in diagnostics):
        return "Near sonic", next(d.message for d in diagnostics if d.code == "NEAR_SONIC")
    if any(d.severity is Severity.WARNING for d in diagnostics):
        return "Supersonic", "; ".join(d.message for d in diagnostics)
    return "Supersonic", ""


def solve(mode: SolveMode | str, value: float, gamma: float) -> CalculatorResult:
    """Solve the Prandtl-Meyer state from one known quantity.

    Args:
        mode: Which quantity ``value`` is.
        value: The known quantity. **In degrees** when the mode is an angle.
        gamma: Ratio of specific heats.

    Returns:
        A :class:`CalculatorResult` whose angular rows are in degrees.
    """
    info = mode_info(mode)
    try:
        gas = PerfectGas(gamma=float(gamma))
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error))

    diagnostics: tuple[Diagnostic, ...] = gas.diagnostics

    try:
        number = float(value)
        if info.mode is SolveMode.MACH:
            mach = number
            pm.nu(mach, gas)                       # domain check
        else:
            solution = pm.mach_from_nu(math.radians(number), gas)
            if not solution.ok:
                return CalculatorResult(
                    False, None, (), "No solution",
                    "; ".join(d.message for d in solution.diagnostics),
                    solution.diagnostics,
                )
            mach = solution.unwrap()
            diagnostics = diagnostics + tuple(
                d for d in solution.diagnostics if d.code != "EXTRAPOLATED_GAMMA")
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)
    except (TypeError, ValueError) as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)

    try:
        rows = _rows_for(mach, gas)
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)

    status, message = _status_for(mach, diagnostics)
    return CalculatorResult(True, mach, rows, status, message, diagnostics)


# ---------------------------------------------------------------------------
# the expansion turn
# ---------------------------------------------------------------------------


def expansion_turn(mach1: float, turn_degrees: float, gamma: float) -> CalculatorResult:
    """Expand a supersonic stream through a convex corner.

    Args:
        mach1: Upstream Mach number.
        turn_degrees: The turn, **in degrees**, >= 0.
        gamma: Ratio of specific heats.

    Returns:
        A :class:`CalculatorResult`. ``mach`` carries the downstream Mach
        number, since that is what the reader came for.
    """
    try:
        gas = PerfectGas(gamma=float(gamma))
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error))

    try:
        solution = pm.expand(float(mach1), math.radians(float(turn_degrees)), gas)
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), gas.diagnostics)
    except (TypeError, ValueError) as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), gas.diagnostics)

    if not solution.ok:
        return CalculatorResult(
            False, None, (), "No solution",
            "; ".join(d.message for d in solution.diagnostics),
            solution.diagnostics,
        )

    result = solution.unwrap()
    rows = (
        ResultRow("mach1", "Upstream Mach  M₁", result.mach1, "", "Flow"),
        ResultRow("mach2", "Downstream Mach  M₂", result.mach2, "", "Flow", emphasis=True),
        ResultRow("turn_angle", "Turn  θ", math.degrees(result.turn_angle), "°", "Flow"),

        ResultRow("nu1", "ν₁", math.degrees(result.nu1), "°", "Turning"),
        ResultRow("nu2", "ν₂ = ν₁ + θ", math.degrees(result.nu2), "°", "Turning",
                  emphasis=True),
        ResultRow("mach_angle1", "μ₁", math.degrees(result.mach_angle1), "°", "Turning"),
        ResultRow("mach_angle2", "μ₂", math.degrees(result.mach_angle2), "°", "Turning"),
        ResultRow("fan_angle", "Fan width", math.degrees(result.fan_angle), "°", "Turning"),

        ResultRow("pressure_ratio", "p₂/p₁", result.pressure_ratio, "", "Static ratios",
                  emphasis=True),
        ResultRow("temperature_ratio", "T₂/T₁", result.temperature_ratio, "",
                  "Static ratios"),
        ResultRow("density_ratio", "ρ₂/ρ₁", result.density_ratio, "", "Static ratios"),

        # Stated as literals, because that is exactly what an isentropic
        # adiabatic turn does to them, and a computed 0.9999999 would invite
        # the reader to wonder whether something had been lost.
        ResultRow("stagnation_pressure_ratio", "p₀₂/p₀₁", 1.0, "", "Stagnation"),
        ResultRow("stagnation_temperature_ratio", "T₀₂/T₀₁", 1.0, "", "Stagnation"),
    )

    status = "Expansion"
    message = (
        "Isentropic: the flow accelerates, static pressure, temperature and density all "
        "fall, and stagnation pressure and temperature are unchanged. No shock, and no "
        "loss."
    )
    if any(d.code == "NEAR_SONIC" for d in solution.diagnostics):
        status = "Near sonic"
    return CalculatorResult(True, result.mach2, rows, status, message,
                            solution.diagnostics)


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------


class TableConvention(StrEnum):
    """Which columns the generated table prints.

    ``ANDERSON`` is column-for-column Appendix C -- M, ν, μ and nothing else --
    because that is what the reader has open beside the screen. ``EXTENDED``
    adds the isentropic ratios at the same Mach numbers, which the appendix
    deliberately leaves to Appendix A but a working calculation needs.
    """

    ANDERSON = "anderson"
    EXTENDED = "extended"


_ANDERSON_COLUMNS = (
    TableColumn("mach", "M", "", 4),
    TableColumn("nu", "ν", "°", 6),
    TableColumn("mach_angle", "μ", "°", 6),
)

_EXTENDED_COLUMNS = (
    TableColumn("mach", "M", "", 4),
    TableColumn("nu", "ν", "°", 6),
    TableColumn("mach_angle", "μ", "°", 6),
    TableColumn("p_over_p0", "p/p₀", "", 6),
    TableColumn("T_over_T0", "T/T₀", "", 6),
    TableColumn("area_ratio", "A/A*", "", 6),
)


def columns_for(convention: TableConvention | str) -> tuple[TableColumn, ...]:
    """The column set a convention prints."""
    return (_EXTENDED_COLUMNS if TableConvention(convention) is TableConvention.EXTENDED
            else _ANDERSON_COLUMNS)


def mach_grid(start: float, end: float, step: float) -> np.ndarray:
    """The Mach values a table will contain.

    A Prandtl-Meyer table starts at 1 and nowhere lower: below it there is no
    expansion fan and the relation is complex-valued. The floor is enforced
    here rather than left to produce a column of refusals.
    """
    if not np.isfinite([start, end, step]).all():
        raise ValueError("Mach range and step must be finite numbers.")
    if step <= 0.0:
        raise ValueError("Step must be greater than zero.")
    if start < 1.0:
        raise ValueError(
            "Start Mach must be 1 or greater: the Prandtl-Meyer function describes "
            "supersonic flow, and it is measured from the sonic condition."
        )
    if end <= start:
        raise ValueError("End Mach must be greater than start Mach.")

    count = int(np.floor((end - start) / step + 1e-9)) + 1
    if count > MAX_TABLE_ROWS:
        raise ValueError(
            f"That range and step would produce {count:,} rows, above the "
            f"{MAX_TABLE_ROWS:,} row limit. Increase the step or narrow the range."
        )
    return start + step * np.arange(count, dtype=np.float64)


def generate_table(
    gamma: float,
    start: float,
    end: float,
    step: float,
    convention: TableConvention | str = TableConvention.ANDERSON,
) -> TableData:
    """Compute a Prandtl-Meyer table over a Mach range.

    Every row is computed by the physics layer, vectorised, and converted to
    degrees once at the end. The published appendix is never read to produce a
    value here; it is only ever compared against.
    """
    gas = PerfectGas(gamma=float(gamma))
    grid = mach_grid(start, end, step)
    convention = TableConvention(convention)

    nu_degrees = np.degrees(np.asarray(pm.nu(grid, gas)))
    mu_degrees = np.degrees(np.asarray(pm.mach_angle(grid)))

    if convention is TableConvention.EXTENDED:
        block = np.column_stack([
            grid, nu_degrees, mu_degrees,
            np.asarray(iso.pressure_ratio(grid, gas)),
            np.asarray(iso.temperature_ratio(grid, gas)),
            np.asarray(iso.area_ratio(grid, gas)),
        ])
    else:
        block = np.column_stack([grid, nu_degrees, mu_degrees])

    return TableData(
        columns=columns_for(convention),
        values=block,
        gamma=gas.gamma,
        convention=convention,
        sonic_row=0 if np.isclose(grid[0], 1.0, atol=1e-12) else None,
        message="",
        metadata={
            "start": float(grid[0]),
            "end": float(grid[-1]),
            "step": float(step),
            "rows": int(grid.size),
            "model": "perfect_gas_prandtl_meyer_v1",
            "nu_max": math.degrees(pm.nu_max(gas)),
            "angle_units": "degrees",
        },
    )
