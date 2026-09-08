"""Normal shock analysis, prepared for presentation.

The adapter between ``rocketforge.physics.compressible.normal_shock`` and
whatever displays it. It owns no gas dynamics: every number comes from a
physics call, and the only arithmetic here is applying a user's upstream static
pressure and temperature to ratios the physics already produced.

Four ways in. An engineer rarely knows M1 directly -- they know what a probe
read. So the pressure jump, the density jump, the downstream Mach number and
the stagnation-pressure loss are all accepted as inputs, each mapped onto the
inverse the physics layer provides. Three are closed form; only the
stagnation-pressure route iterates, and it says so in its convergence record.

Deliberately free of Qt, so all of it can be tested headlessly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ...core.errors import RocketForgeError
from ...core.result import Diagnostic, Severity
from ...physics.compressible import PerfectGas
from ...physics.compressible import isentropic as iso
from ...physics.compressible import normal_shock as ns
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
    "UpstreamState",
    "solve",
    "generate_table",
    "columns_for",
    "TableConvention",
    "MAX_TABLE_ROWS",
    "DEFAULT_UPSTREAM",
]


class SolveMode(StrEnum):
    """What the user supplies, from which the whole shock follows.

    Every mode is a quantity something actually measures, and every one maps
    onto a verified inverse. There is no mode here the physics cannot answer.
    """

    MACH_UPSTREAM = "mach1"
    PRESSURE_RATIO = "p2_over_p1"
    DENSITY_RATIO = "rho2_over_rho1"
    MACH_DOWNSTREAM = "mach2"
    STAGNATION_PRESSURE_RATIO = "p02_over_p01"


@dataclass(frozen=True, slots=True)
class SolveModeInfo:
    """How one solve mode presents itself and what it needs."""

    mode: SolveMode
    label: str
    symbol: str
    hint: str
    iterative: bool
    default_value: float


SOLVE_MODES: tuple[SolveModeInfo, ...] = (
    SolveModeInfo(SolveMode.MACH_UPSTREAM, "Upstream Mach number", "M₁",
                  "1 or greater", False, 2.0),
    SolveModeInfo(SolveMode.PRESSURE_RATIO, "Static pressure jump", "p₂/p₁",
                  "1 or greater", False, 4.5),
    SolveModeInfo(SolveMode.DENSITY_RATIO, "Density jump", "ρ₂/ρ₁",
                  "1 up to (γ+1)/(γ−1)", False, 2.666666667),
    SolveModeInfo(SolveMode.MACH_DOWNSTREAM, "Downstream Mach number", "M₂",
                  "between the strong-shock limit and 1", False, 0.5773502692),
    SolveModeInfo(SolveMode.STAGNATION_PRESSURE_RATIO, "Stagnation pressure loss", "p₀₂/p₀₁",
                  "0 to 1", True, 0.7208738615),
)

_MODE_INDEX = {info.mode: info for info in SOLVE_MODES}


def mode_info(mode: SolveMode | str) -> SolveModeInfo:
    """Descriptor for a solve mode."""
    return _MODE_INDEX[SolveMode(mode)]


@dataclass(frozen=True, slots=True)
class UpstreamState:
    """Optional upstream conditions, in SI.

    Supplying them turns every ratio into a downstream value in Pa and K. They
    are optional because the shock relations are complete without them: a
    dimensional state is a convenience, not a prerequisite, and when it is
    absent the dimensional rows stay empty rather than being invented.
    """

    pressure: float = 101325.0        # Pa
    temperature: float = 288.15       # K

    @property
    def complete(self) -> bool:
        values = (self.pressure, self.temperature)
        return all(np.isfinite(v) and v > 0.0 for v in values)


#: Sea-level static air: a recognisable upstream condition, chosen so the
#: dimensional rows mean something on first open.
DEFAULT_UPSTREAM = UpstreamState()


# ---------------------------------------------------------------------------
# calculator
# ---------------------------------------------------------------------------


def _rows_for(mach1: float, gas: PerfectGas, upstream: UpstreamState) -> tuple[ResultRow, ...]:
    """Every displayed quantity for one shock."""
    shock = ns.solve(mach1, gas)

    if upstream.complete:
        p2 = upstream.pressure * shock.pressure_ratio
        t2 = upstream.temperature * shock.temperature_ratio
        p01 = upstream.pressure / float(iso.pressure_ratio(mach1, gas))
        p02 = p01 * shock.stagnation_pressure_ratio
        t0 = upstream.temperature / float(iso.temperature_ratio(mach1, gas))
    else:
        p2 = t2 = p01 = p02 = t0 = None

    return (
        ResultRow("mach1", "Upstream Mach M₁", shock.mach1, "", "Flow", emphasis=True),
        ResultRow("mach2", "Downstream Mach M₂", shock.mach2, "", "Flow", emphasis=True),

        ResultRow("p2_over_p1", "p₂/p₁", shock.pressure_ratio, "", "Static jump", emphasis=True),
        ResultRow("rho2_over_rho1", "ρ₂/ρ₁", shock.density_ratio, "", "Static jump"),
        ResultRow("T2_over_T1", "T₂/T₁", shock.temperature_ratio, "", "Static jump"),

        ResultRow("p02_over_p01", "p₀₂/p₀₁", shock.stagnation_pressure_ratio, "",
                  "Stagnation", emphasis=True),
        ResultRow("T02_over_T01", "T₀₂/T₀₁", shock.stagnation_temperature_ratio, "", "Stagnation"),
        ResultRow("p02_over_p1", "p₀₂/p₁ (pitot)", shock.stagnation_pressure_over_upstream_static,
                  "", "Stagnation"),
        ResultRow("area_star_ratio", "A₂*/A₁*", shock.area_star_ratio, "", "Stagnation"),
        ResultRow("entropy_change", "Δs/R", shock.entropy_change, "", "Stagnation"),

        ResultRow("p2", "p₂", p2, "Pa", "Downstream state"),
        ResultRow("T2", "T₂", t2, "K", "Downstream state"),
        ResultRow("p01", "p₀₁", p01, "Pa", "Downstream state"),
        ResultRow("p02", "p₀₂", p02, "Pa", "Downstream state"),
        ResultRow("T0", "T₀ (unchanged)", t0, "K", "Downstream state"),
    )


def _status_for(mach1: float, gas: PerfectGas,
                diagnostics: tuple[Diagnostic, ...]) -> tuple[str, str]:
    """The compact state indicator and its one-line explanation."""
    if ns.solve(mach1, gas).sonic_limit:
        return "Sonic limit", (
            "M₁ = 1 is the vanishing shock: every ratio is 1 and no stagnation "
            "pressure is lost. Below the resolution of double precision, the loss "
            "of a very weak shock cannot be represented at all."
        )
    if mach1 >= 10.0:
        return "Strong shock", (
            "A very strong shock. The perfect-gas assumption is the limitation "
            "here, not the arithmetic: real air dissociates and ionises well "
            "before these ratios are reached."
        )
    if any(d.severity is Severity.WARNING for d in diagnostics):
        return "Valid", "; ".join(d.message for d in diagnostics)
    return "Valid", ""


def solve(
    mode: SolveMode | str,
    value: float,
    gamma: float,
    upstream: UpstreamState = DEFAULT_UPSTREAM,
) -> CalculatorResult:
    """Solve a normal shock from one known quantity.

    Args:
        mode: Which quantity ``value`` is.
        value: The known quantity.
        gamma: Ratio of specific heats.
        upstream: Optional dimensional upstream conditions.

    Returns:
        A :class:`CalculatorResult`. Unlike the isentropic area-ratio inverse,
        no branch is ever needed: each of these relations is one-to-one on the
        supersonic side.
    """
    info = mode_info(mode)
    try:
        gas = PerfectGas(gamma=float(gamma))
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error))

    diagnostics: tuple[Diagnostic, ...] = gas.diagnostics

    try:
        number = float(value)
        if info.mode is SolveMode.MACH_UPSTREAM:
            mach1 = number
            ns.pressure_ratio(mach1, gas)                  # domain check
        elif info.mode is SolveMode.PRESSURE_RATIO:
            mach1 = float(ns.mach_upstream_from_pressure_ratio(number, gas))
        elif info.mode is SolveMode.DENSITY_RATIO:
            mach1 = float(ns.mach_upstream_from_density_ratio(number, gas))
        elif info.mode is SolveMode.MACH_DOWNSTREAM:
            mach1 = float(ns.mach_upstream_from_downstream_mach(number, gas))
        else:
            solution = ns.mach_upstream_from_stagnation_pressure_ratio(number, gas)
            if not solution.ok:
                return CalculatorResult(
                    False, None, (), "Not converged",
                    "; ".join(d.message for d in solution.diagnostics),
                    solution.diagnostics,
                )
            mach1 = solution.unwrap()
            diagnostics = diagnostics + tuple(
                d for d in solution.diagnostics if d.code != "EXTRAPOLATED_GAMMA"
            )
    except ZeroDivisionError:
        return CalculatorResult(False, None, (), "Invalid input",
                                f"{info.symbol} cannot be zero.")
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)
    except (TypeError, ValueError) as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)

    try:
        rows = _rows_for(mach1, gas, upstream)
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)

    status, message = _status_for(mach1, gas, diagnostics)
    return CalculatorResult(True, mach1, rows, status, message, diagnostics)


def limits_for(gamma: float) -> tuple[float, float]:
    """The two strong-shock limits, for a caption that states the ceiling.

    Returns ``(rho2/rho1 limit, M2 limit)``. Shown beside the results because
    "6" and "0.378" for air are the two numbers that make a strong shock
    intelligible: however hard you push, the gas compresses no further and the
    flow behind slows no more.
    """
    gas = PerfectGas(gamma=float(gamma))
    return ns.density_ratio_limit(gas), ns.mach_downstream_limit(gas)


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------


class TableConvention(StrEnum):
    """Which set of columns the generated table prints.

    ``ANDERSON`` is column-for-column the published appendix, so a reader can
    set the two side by side. ``EXTENDED`` adds the entropy rise and the sonic
    area growth, which the appendix omits but a nozzle calculation needs.
    """

    ANDERSON = "anderson"
    EXTENDED = "extended"


_ANDERSON_COLUMNS = (
    TableColumn("mach1", "M₁", "", 4),
    TableColumn("p2_over_p1", "p₂/p₁", "", 6),
    TableColumn("rho2_over_rho1", "ρ₂/ρ₁", "", 6),
    TableColumn("T2_over_T1", "T₂/T₁", "", 6),
    TableColumn("p02_over_p01", "p₀₂/p₀₁", "", 6),
    TableColumn("p02_over_p1", "p₀₂/p₁", "", 6),
    TableColumn("mach2", "M₂", "", 6),
)

_EXTENDED_COLUMNS = (
    TableColumn("mach1", "M₁", "", 4),
    TableColumn("mach2", "M₂", "", 6),
    TableColumn("p2_over_p1", "p₂/p₁", "", 6),
    TableColumn("T2_over_T1", "T₂/T₁", "", 6),
    TableColumn("p02_over_p01", "p₀₂/p₀₁", "", 6),
    TableColumn("entropy_change", "Δs/R", "", 6),
    TableColumn("area_star_ratio", "A₂*/A₁*", "", 6),
)


def columns_for(convention: TableConvention | str) -> tuple[TableColumn, ...]:
    """The column set a convention prints."""
    return (_EXTENDED_COLUMNS if TableConvention(convention) is TableConvention.EXTENDED
            else _ANDERSON_COLUMNS)


def mach_grid(start: float, end: float, step: float) -> np.ndarray:
    """The upstream Mach values a table will contain.

    A normal-shock table starts at 1 and nowhere lower: below it there is no
    shock to tabulate. The floor is enforced here rather than left to produce a
    column of refusals.
    """
    if not np.isfinite([start, end, step]).all():
        raise ValueError("Mach range and step must be finite numbers.")
    if step <= 0.0:
        raise ValueError("Step must be greater than zero.")
    if start < 1.0:
        raise ValueError(
            "Start Mach must be 1 or greater: a normal shock requires supersonic "
            "upstream flow."
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
    """Compute a normal-shock table over a range of upstream Mach numbers.

    Every row is computed by the physics layer, vectorised. The published
    appendix is never read to produce a value here; it is only ever compared
    against, in :mod:`reference_comparison`.
    """
    gas = PerfectGas(gamma=float(gamma))
    grid = mach_grid(start, end, step)
    convention = TableConvention(convention)

    pressure = np.asarray(ns.pressure_ratio(grid, gas))
    density = np.asarray(ns.density_ratio(grid, gas))
    temperature = np.asarray(ns.temperature_ratio(grid, gas))
    stagnation = np.asarray(ns.stagnation_pressure_ratio(grid, gas))
    downstream = np.asarray(ns.mach_downstream(grid, gas))

    if convention is TableConvention.ANDERSON:
        pitot = np.asarray(ns.stagnation_pressure_over_upstream_static(grid, gas))
        block = np.column_stack(
            [grid, pressure, density, temperature, stagnation, pitot, downstream])
    else:
        entropy = np.asarray(ns.entropy_change(grid, gas))
        area = np.asarray(ns.area_star_ratio(grid, gas))
        block = np.column_stack(
            [grid, downstream, pressure, temperature, stagnation, entropy, area])

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
            "model": "perfect_gas_normal_shock_v1",
            "density_ratio_limit": ns.density_ratio_limit(gas),
            "mach_downstream_limit": ns.mach_downstream_limit(gas),
        },
    )
