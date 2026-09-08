"""Mass flow and choking, prepared for presentation.

The adapter between ``rocketforge.physics.compressible.mass_flow`` and whatever
displays it. It owns no gas dynamics: every number here comes from a physics
call. What it *does* own is the one thing a screen needs and the physics
deliberately does not provide -- the decision of which dimensional inputs are
present, and therefore which of the readouts can be filled in.

That distinction matters. The mass-flow parameter needs only gamma and a Mach
number; a mass flow in kg/s additionally needs R, an area, and a stagnation
state. Rather than invent defaults for the missing ones, this service reports
the dimensionless group and leaves the dimensional rows empty, so the interface
can show what is genuinely known instead of a plausible-looking fiction.

Deliberately free of Qt, so all of it can be tested headlessly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ...core.errors import RocketForgeError
from ...core.result import Diagnostic, Severity
from ...physics.compressible import FlowBranch, PerfectGas
from ...physics.compressible import isentropic as iso
from ...physics.compressible import mass_flow as mf
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
    "FlowState",
    "solve",
    "generate_table",
    "columns_for",
    "TableConvention",
    "MAX_TABLE_ROWS",
    "DEFAULT_STATE",
]


class SolveMode(StrEnum):
    """What the user supplies, from which everything else follows."""

    MACH = "mach"
    #: mdot / mdot_choked through the same area -- two branches, like A/A*.
    FLOW_RATIO = "flow_ratio"
    #: Static over stagnation pressure, which also answers the choking question.
    PRESSURE_RATIO = "p_over_p0"
    #: A mass flow in kg/s, against the choked flow the given area can pass.
    MASS_FLOW = "mass_flow"


@dataclass(frozen=True, slots=True)
class SolveModeInfo:
    """How one solve mode presents itself and what it needs."""

    mode: SolveMode
    label: str
    symbol: str
    unit: str
    hint: str
    needs_branch: bool
    needs_dimensions: bool
    default_value: float


SOLVE_MODES: tuple[SolveModeInfo, ...] = (
    SolveModeInfo(SolveMode.MACH, "Mach number", "M", "",
                  "0 or greater", False, False, 0.5),
    SolveModeInfo(SolveMode.FLOW_RATIO, "Flow fraction", "ṁ/ṁ*", "",
                  "0 to 1", True, False, 0.75),
    SolveModeInfo(SolveMode.PRESSURE_RATIO, "Pressure ratio", "p/p₀", "",
                  "0 to 1", False, False, 0.7),
    SolveModeInfo(SolveMode.MASS_FLOW, "Mass flow", "ṁ", "kg/s",
                  "greater than 0", True, True, 5.0),
)

_MODE_INDEX = {info.mode: info for info in SOLVE_MODES}


def mode_info(mode: SolveMode | str) -> SolveModeInfo:
    """Descriptor for a solve mode."""
    return _MODE_INDEX[SolveMode(mode)]


@dataclass(frozen=True, slots=True)
class FlowState:
    """The dimensional context a mass flow needs, in SI.

    ``gas_constant`` is separate from gamma because the two answer different
    questions: gamma alone fixes every ratio and the dimensionless parameter,
    while R, the area and the stagnation state are what turn those into
    kilograms per second.
    """

    area: float = 0.01                 # m²
    stagnation_pressure: float = 1.0e6  # Pa
    stagnation_temperature: float = 300.0  # K
    gas_constant: float = 287.0528     # J/(kg K)

    @property
    def complete(self) -> bool:
        """Whether a dimensional mass flow can be computed at all."""
        values = (self.area, self.stagnation_pressure,
                  self.stagnation_temperature, self.gas_constant)
        return all(np.isfinite(v) and v > 0.0 for v in values)


#: Air at a chamber-like state: enough to make the dimensional rows meaningful
#: on first open without implying the numbers came from anywhere authoritative.
DEFAULT_STATE = FlowState()


# ---------------------------------------------------------------------------
# calculator
# ---------------------------------------------------------------------------


def _rows_for(mach: float, gas: PerfectGas, state: FlowState) -> tuple[ResultRow, ...]:
    """Every displayed quantity at one Mach number.

    The dimensionless block is always filled. The dimensional block is filled
    only when the state supports it, and left as None otherwise -- never
    silently substituted.
    """
    parameter = float(mf.mass_flow_parameter(mach, gas))
    choked_coefficient = mf.choked_mass_flow_coefficient(gas)
    fraction = float(mf.mass_flow_over_choked(mach, gas))

    dimensional = state.complete
    if dimensional:
        sized = PerfectGas(gamma=gas.gamma, gas_constant=state.gas_constant)
        flow = float(mf.mass_flow(mach, sized, state.area,
                                  state.stagnation_pressure, state.stagnation_temperature))
        flux = float(mf.mass_flux(mach, sized, state.stagnation_pressure,
                                  state.stagnation_temperature))
        choked_flow = mf.choked_mass_flow(sized, state.area,
                                          state.stagnation_pressure,
                                          state.stagnation_temperature)
        throat = state.area * fraction        # A* = A * (mdot/mdot_choked)
    else:
        flow = flux = choked_flow = throat = None

    return (
        ResultRow("mach", "Mach number", mach, "", "Flow", emphasis=True),
        ResultRow("mass_flow_parameter", "MFP = ṁ√(RT₀)/(Ap₀)", parameter, "",
                  "Dimensionless", emphasis=True),
        ResultRow("flow_fraction", "ṁ/ṁ* (choked fraction)", fraction, "", "Dimensionless"),
        ResultRow("choked_coefficient", "Γ(γ)", choked_coefficient, "", "Dimensionless"),
        ResultRow("area_ratio", "A/A*", float(iso.area_ratio(mach, gas)), "", "Dimensionless"),

        ResultRow("p_over_p0", "p/p₀", float(iso.pressure_ratio(mach, gas)), "",
                  "Stagnation state"),
        ResultRow("T_over_T0", "T/T₀", float(iso.temperature_ratio(mach, gas)), "",
                  "Stagnation state"),
        ResultRow("rho_over_rho0", "ρ/ρ₀", float(iso.density_ratio(mach, gas)), "",
                  "Stagnation state"),

        ResultRow("critical_pressure_ratio", "p*/p₀", mf.critical_pressure_ratio(gas), "",
                  "Critical condition"),
        ResultRow("critical_temperature_ratio", "T*/T₀", mf.critical_temperature_ratio(gas), "",
                  "Critical condition"),

        ResultRow("mass_flow", "ṁ", flow, "kg/s", "Dimensional", emphasis=True),
        ResultRow("mass_flux", "G = ṁ/A", flux, "kg/(s·m²)", "Dimensional"),
        ResultRow("choked_mass_flow", "ṁ at choking", choked_flow, "kg/s", "Dimensional"),
        ResultRow("throat_area", "A* required", throat, "m²", "Dimensional"),
    )


def _status_for(mach: float, gas: PerfectGas,
                diagnostics: tuple[Diagnostic, ...]) -> tuple[str, str]:
    """The compact state indicator and its one-line explanation."""
    if mach == 1.0:
        return "Choked", (
            "The flow is sonic: this area passes the most mass it can for this "
            "stagnation state."
        )
    if mach > 1.0:
        return "Supersonic", (
            "Supersonic flow. The passage upstream must have had a throat, and it "
            "is that throat -- not this station -- that sets the mass flow."
        )
    if any(d.severity is Severity.WARNING for d in diagnostics):
        return "Subsonic", "; ".join(d.message for d in diagnostics)
    return "Subsonic", ""


def solve(
    mode: SolveMode | str,
    value: float,
    gamma: float,
    state: FlowState = DEFAULT_STATE,
    branch: FlowBranch | str = FlowBranch.SUBSONIC,
) -> CalculatorResult:
    """Solve the mass-flow state from one known quantity.

    Args:
        mode: Which quantity ``value`` is.
        value: The known quantity.
        gamma: Ratio of specific heats.
        state: The dimensional context. Only its completeness is consulted for
            the dimensionless modes.
        branch: Required for the flow-fraction and mass-flow modes, which have
            a subsonic and a supersonic answer; ignored otherwise.

    Returns:
        A :class:`CalculatorResult`.
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
            mf.mass_flow_parameter(mach, gas)              # domain check
        elif info.mode is SolveMode.PRESSURE_RATIO:
            # p/p0 fixes the Mach number outright -- one root, no branch, and
            # it is the isentropic inverse rather than a mass-flow-specific one.
            mach = float(iso.mach_from_pressure_ratio(number, gas))
        else:
            if info.mode is SolveMode.MASS_FLOW:
                if not state.complete:
                    return CalculatorResult(
                        False, None, (), "Invalid input",
                        "A mass flow in kg/s needs a positive area, stagnation "
                        "pressure, stagnation temperature and gas constant.",
                        diagnostics,
                    )
                sized = PerfectGas(gamma=gas.gamma, gas_constant=state.gas_constant)
                ceiling = mf.choked_mass_flow(sized, state.area,
                                              state.stagnation_pressure,
                                              state.stagnation_temperature)
                fraction = number / ceiling
            else:
                fraction = number

            wanted = FlowBranch(branch)
            if wanted is FlowBranch.BOTH:
                subsonic = mf.mach_from_mass_flow_ratio(
                    fraction, gas, FlowBranch.SUBSONIC).unwrap()
                supersonic = mf.mach_from_mass_flow_ratio(
                    fraction, gas, FlowBranch.SUPERSONIC).unwrap()
                both = (subsonic, supersonic)
                mach = supersonic
                branch_used = "both"
                solution = None
            else:
                solution = mf.mach_from_mass_flow_ratio(fraction, gas, wanted)
                if not solution.ok:
                    return CalculatorResult(
                        False, None, (), "Not converged",
                        "; ".join(d.message for d in solution.diagnostics),
                        solution.diagnostics,
                    )
                mach = solution.unwrap()
                branch_used = wanted.value
            if solution is not None:
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
        rows = _rows_for(mach, gas, state)
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), diagnostics)

    status, message = _status_for(mach, gas, diagnostics)
    return CalculatorResult(True, mach, rows, status, message, diagnostics, branch_used, both)


def choking_report(receiver_pressure_ratio: float, gamma: float) -> tuple[bool, str]:
    """Whether a convergent passage is choked, and why, in one sentence.

    Args:
        receiver_pressure_ratio: ``p_receiver / p0``, in (0, 1].
        gamma: Ratio of specific heats.

    Scoped exactly as :func:`mass_flow.is_choked` is scoped: a convergent
    passage discharging to a receiver. It is not, and must not become, a
    converging-diverging nozzle regime classifier.
    """
    gas = PerfectGas(gamma=float(gamma))
    critical = mf.critical_pressure_ratio(gas)
    choked = mf.is_choked(float(receiver_pressure_ratio), gas)
    if choked:
        return True, (
            f"Choked: the receiver is at or below the critical ratio p*/p₀ = "
            f"{critical:.4f}, so the exit is sonic and lowering the receiver "
            "pressure further cannot increase the flow."
        )
    return False, (
        f"Not choked: the receiver is above the critical ratio p*/p₀ = "
        f"{critical:.4f}, so the exit is subsonic and the flow still responds "
        "to the receiver pressure."
    )


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------


class TableConvention(StrEnum):
    """Which set of columns the generated table prints.

    Two views of the same physics: ``DIMENSIONLESS`` is what a textbook plots
    and is independent of any particular hardware; ``DIMENSIONAL`` applies the
    current stagnation state and area, and is what an engineer sizing a duct
    actually wants to read.
    """

    DIMENSIONLESS = "dimensionless"
    DIMENSIONAL = "dimensional"


_DIMENSIONLESS_COLUMNS = (
    TableColumn("mach", "M", "", 4),
    TableColumn("mass_flow_parameter", "MFP", "", 6),
    TableColumn("flow_fraction", "ṁ/ṁ*", "", 6),
    TableColumn("area_ratio", "A/A*", "", 6),
    TableColumn("p_over_p0", "p/p₀", "", 6),
    TableColumn("T_over_T0", "T/T₀", "", 6),
)

_DIMENSIONAL_COLUMNS = (
    TableColumn("mach", "M", "", 4),
    TableColumn("mass_flow", "ṁ", "kg/s", 6),
    TableColumn("mass_flux", "G", "kg/(s·m²)", 4),
    TableColumn("flow_fraction", "ṁ/ṁ*", "", 6),
    TableColumn("throat_area", "A*", "m²", 8),
    TableColumn("p_over_p0", "p/p₀", "", 6),
)


def columns_for(convention: TableConvention | str) -> tuple[TableColumn, ...]:
    """The column set a convention prints."""
    return (_DIMENSIONAL_COLUMNS
            if TableConvention(convention) is TableConvention.DIMENSIONAL
            else _DIMENSIONLESS_COLUMNS)


def mach_grid(start: float, end: float, step: float, include_sonic: bool = True) -> np.ndarray:
    """The Mach values a table will contain.

    Unlike the isentropic table this one may begin at exactly zero: the
    mass-flow parameter is zero at rest and perfectly well defined there. It is
    ``A/A*`` in the companion column that is unbounded, and that column is
    reported as infinity rather than allowed to veto the row.
    """
    if not np.isfinite([start, end, step]).all():
        raise ValueError("Mach range and step must be finite numbers.")
    if step <= 0.0:
        raise ValueError("Step must be greater than zero.")
    if start < 0.0:
        raise ValueError("Start Mach cannot be negative.")
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
    convention: TableConvention | str = TableConvention.DIMENSIONLESS,
    state: FlowState = DEFAULT_STATE,
    include_sonic: bool = True,
) -> TableData:
    """Compute a mass-flow table over a Mach range.

    Every row is computed by the physics layer, vectorised: one call per
    quantity rather than a Python loop per row.
    """
    gas = PerfectGas(gamma=float(gamma))
    grid = mach_grid(start, end, step, include_sonic)
    convention = TableConvention(convention)

    if convention is TableConvention.DIMENSIONAL and not state.complete:
        raise ValueError(
            "A dimensional table needs a positive area, stagnation pressure, "
            "stagnation temperature and gas constant."
        )

    parameter = np.asarray(mf.mass_flow_parameter(grid, gas))
    fraction = np.asarray(mf.mass_flow_over_choked(grid, gas))
    pressure = np.asarray(iso.pressure_ratio(grid, gas))

    with np.errstate(divide="ignore"):
        # A/A* is infinite at rest. Reported as such, not hidden and not
        # silently dropped: the row is real, that one entry is unbounded.
        area = np.where(grid > 0.0, np.asarray(iso.area_ratio(np.where(grid > 0.0, grid, 1.0), gas)),
                        np.inf)

    if convention is TableConvention.DIMENSIONAL:
        sized = PerfectGas(gamma=gas.gamma, gas_constant=state.gas_constant)
        flow = np.asarray(mf.mass_flow(grid, sized, state.area,
                                       state.stagnation_pressure,
                                       state.stagnation_temperature))
        flux = np.asarray(mf.mass_flux(grid, sized, state.stagnation_pressure,
                                       state.stagnation_temperature))
        block = np.column_stack([grid, flow, flux, fraction, state.area * fraction, pressure])
    else:
        temperature = np.asarray(iso.temperature_ratio(grid, gas))
        block = np.column_stack([grid, parameter, fraction, area, pressure, temperature])

    sonic = np.flatnonzero(np.isclose(grid, 1.0, atol=1e-12))
    return TableData(
        columns=columns_for(convention),
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
            "model": "perfect_gas_mass_flow_v1",
            "choked_coefficient": mf.choked_mass_flow_coefficient(gas),
            "critical_pressure_ratio": mf.critical_pressure_ratio(gas),
            "area": state.area,
            "stagnation_pressure": state.stagnation_pressure,
            "stagnation_temperature": state.stagnation_temperature,
            "gas_constant": state.gas_constant,
        },
    )
