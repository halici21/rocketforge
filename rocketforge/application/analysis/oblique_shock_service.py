"""Oblique shock analysis, prepared for presentation.

The adapter between ``rocketforge.physics.compressible.oblique_shock`` and
whatever displays it. It owns no gas dynamics: every number here comes from a
physics call, and every property ratio came, one layer further down, from the
normal-shock module.

**This is where degrees exist.** Radians below, degrees above, converted once
here, on the way in and on the way out.

Two things this service is careful about, because both are ways of being
subtly dishonest:

* a deflection past the attachment limit produces *no* result, not a
  substituted one. The calculator is told to clear, and told why;
* "weak" is not reported as "supersonic behind". The two coincide over most of
  the range and part company just below the maximum deflection, so the flag
  comes from the computed downstream Mach number.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ...core.errors import RocketForgeError
from ...core.result import Diagnostic, Severity
from ...physics.compressible import PerfectGas, ShockBranch
from ...physics.compressible import oblique_shock as obl
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
    "limits_for",
    "generate_table",
    "columns_for",
    "curve_data",
    "ShockBranch",
    "MAX_TABLE_ROWS",
]


class SolveMode(StrEnum):
    """What the user supplies.

    Two modes, and no more: the specification lists ``given theta, beta -> M1``
    as future work precisely because it is easy to misuse, and adding it here
    would be inventing scope.
    """

    #: Deflection in, wave angle out. Needs a branch; solved with Brent.
    THETA = "theta"
    #: Wave angle in, deflection out. Closed form, and no branch to choose.
    BETA = "beta"


@dataclass(frozen=True, slots=True)
class SolveModeInfo:
    """How one solve mode presents itself and what it needs."""

    mode: SolveMode
    label: str
    symbol: str
    hint: str
    needs_branch: bool
    iterative: bool
    default_value: float


SOLVE_MODES: tuple[SolveModeInfo, ...] = (
    SolveModeInfo(SolveMode.THETA, "Flow deflection", "θ",
                  "0 up to θ_max", True, True, 10.0),
    SolveModeInfo(SolveMode.BETA, "Shock wave angle", "β",
                  "between μ and 90°", False, False, 39.31393184),
)

_MODE_INDEX = {info.mode: info for info in SOLVE_MODES}


def mode_info(mode: SolveMode | str) -> SolveModeInfo:
    """Descriptor for a solve mode."""
    return _MODE_INDEX[SolveMode(mode)]


def limits_for(mach1: float, gamma: float) -> dict:
    """The three angles that bound the diagram, in degrees.

    The Mach angle, the maximum deflection with the wave angle that produces
    it, and the wave angle at which the flow behind turns sonic. Shown beside
    the result because they are what make a given answer intelligible.
    """
    try:
        gas = PerfectGas(gamma=float(gamma))
        limit = obl.theta_max(float(mach1), gas).unwrap()
        sonic = obl.beta_sonic(float(mach1), gas).unwrap()
    except (RocketForgeError, ValueError, TypeError):
        return {}
    return {
        "machAngle": math.degrees(limit.mach_angle),
        "thetaMax": math.degrees(limit.theta_max),
        "betaAtThetaMax": math.degrees(limit.beta_at_theta_max),
        "betaSonic": math.degrees(sonic),
    }


# ---------------------------------------------------------------------------
# calculator
# ---------------------------------------------------------------------------


def _rows_for(result, gas: PerfectGas) -> tuple[ResultRow, ...]:
    """Every displayed quantity for one shock, angles in degrees."""
    loss = 100.0 * (1.0 - result.stagnation_pressure_ratio)
    return (
        ResultRow("mach_angle", "Mach angle  μ",
                  math.degrees(math.asin(1.0 / result.mach1)), "°", "Geometry"),
        ResultRow("theta", "Flow deflection  θ", math.degrees(result.theta), "°",
                  "Geometry", emphasis=True),
        ResultRow("beta", "Shock angle  β", math.degrees(result.beta), "°",
                  "Geometry", emphasis=True),
        ResultRow("theta_max", "Maximum deflection  θ_max", math.degrees(result.theta_max),
                  "°", "Geometry"),

        ResultRow("mach1", "Upstream  M₁", result.mach1, "", "Flow"),
        ResultRow("mach_normal1", "Normal component  Mn₁", result.mach_normal1, "", "Flow"),
        ResultRow("mach_normal2", "Downstream normal  Mn₂", result.mach_normal2, "", "Flow"),
        ResultRow("mach2", "Downstream  M₂", result.mach2, "", "Flow", emphasis=True),

        ResultRow("pressure_ratio", "p₂/p₁", result.pressure_ratio, "", "Shock jump",
                  emphasis=True),
        ResultRow("density_ratio", "ρ₂/ρ₁", result.density_ratio, "", "Shock jump"),
        ResultRow("temperature_ratio", "T₂/T₁", result.temperature_ratio, "", "Shock jump"),

        ResultRow("stagnation_pressure_ratio", "p₀₂/p₀₁",
                  result.stagnation_pressure_ratio, "", "Total", emphasis=True),
        ResultRow("stagnation_pressure_loss", "Total-pressure loss", loss, "%", "Total"),
        ResultRow("stagnation_temperature_ratio", "T₀₂/T₀₁",
                  result.stagnation_temperature_ratio, "", "Total"),
        ResultRow("entropy_change", "Δs/R", result.entropy_change, "", "Total"),
    )


def _status_for(result, diagnostics: tuple[Diagnostic, ...]) -> tuple[str, str]:
    """The compact state indicator and its one-line explanation."""
    if any(d.code == "NEAR_THETA_MAX" for d in diagnostics):
        return "Near detachment", next(
            d.message for d in diagnostics if d.code == "NEAR_THETA_MAX")
    if result.branch is ShockBranch.STRONG:
        return "Strong branch", (
            "The strong solution satisfies the equations but is realised only when "
            "downstream conditions force it; an unconstrained external flow takes the "
            "weak branch."
        )
    if not result.downstream_supersonic:
        return "Weak, subsonic behind", (
            "Still the weak branch, but the flow behind this shock is subsonic: the "
            "sonic wave angle sits just below the angle of maximum deflection, so the "
            "last part of the weak branch is already subsonic."
        )
    if any(d.severity is Severity.WARNING for d in diagnostics):
        return "Attached", "; ".join(d.message for d in diagnostics)
    return "Attached", ""


def solve(
    mode: SolveMode | str,
    value: float,
    mach1: float,
    gamma: float,
    branch: ShockBranch | str = ShockBranch.WEAK,
) -> CalculatorResult:
    """Solve one oblique shock.

    Args:
        mode: Which quantity ``value`` is.
        value: The deflection or the wave angle, **in degrees**.
        mach1: Upstream Mach number.
        gamma: Ratio of specific heats.
        branch: Which wave angle is wanted; ignored in the ``BETA`` mode, where
            the branch is a consequence of the angle rather than a choice.

    Returns:
        A :class:`CalculatorResult` whose angular rows are in degrees. A
        deflection past the attachment limit produces ``ok=False`` with the
        status ``Detached`` -- never a substituted attached solution.
    """
    info = mode_info(mode)
    try:
        gas = PerfectGas(gamma=float(gamma))
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error))

    try:
        angle = math.radians(float(value))
        if info.mode is SolveMode.BETA:
            solution = obl.solve_from_beta(float(mach1), angle, gas)
            branch_used = ""
        else:
            wanted = ShockBranch(branch)
            if wanted is ShockBranch.BOTH:
                return _both(float(mach1), angle, gas)
            solution = obl.solve(float(mach1), angle, gas, wanted)
            branch_used = wanted.value
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), gas.diagnostics)
    except (TypeError, ValueError) as error:
        return CalculatorResult(False, None, (), "Invalid input", str(error), gas.diagnostics)

    if not solution.ok:
        detached = next((d for d in solution.diagnostics if d.code == "DETACHED_SHOCK"), None)
        if detached is not None:
            return CalculatorResult(False, None, (), "Detached", detached.message,
                                    solution.diagnostics)
        return CalculatorResult(False, None, (), "No solution",
                                "; ".join(d.message for d in solution.diagnostics),
                                solution.diagnostics)

    result = solution.unwrap()
    status, message = _status_for(result, solution.diagnostics)
    return CalculatorResult(True, result.mach2, _rows_for(result, gas), status, message,
                            solution.diagnostics, branch_used)


def _both(mach1: float, theta: float, gas: PerfectGas) -> CalculatorResult:
    """Both branches, as one result whose rows are tagged by branch.

    The two solutions are kept in separate groups rather than interleaved, so a
    reader can never mistake a weak row for a strong one.
    """
    solution = obl.solve_both(mach1, theta, gas)
    if not solution.ok:
        detached = next((d for d in solution.diagnostics if d.code == "DETACHED_SHOCK"), None)
        status = "Detached" if detached is not None else "No solution"
        message = (detached.message if detached is not None
                   else "; ".join(d.message for d in solution.diagnostics))
        return CalculatorResult(False, None, (), status, message, solution.diagnostics)

    pair = solution.unwrap()
    rows: list[ResultRow] = []
    for label, result in (("Weak solution", pair.weak), ("Strong solution", pair.strong)):
        prefix = "weak" if result.branch is ShockBranch.WEAK else "strong"
        rows.extend([
            ResultRow(f"{prefix}_beta", "Shock angle  β", math.degrees(result.beta), "°",
                      label, emphasis=True),
            ResultRow(f"{prefix}_mach2", "Downstream  M₂", result.mach2, "", label,
                      emphasis=True),
            ResultRow(f"{prefix}_pressure_ratio", "p₂/p₁", result.pressure_ratio, "", label),
            ResultRow(f"{prefix}_density_ratio", "ρ₂/ρ₁", result.density_ratio, "", label),
            ResultRow(f"{prefix}_temperature_ratio", "T₂/T₁", result.temperature_ratio, "",
                      label),
            ResultRow(f"{prefix}_stagnation_pressure_ratio", "p₀₂/p₀₁",
                      result.stagnation_pressure_ratio, "", label),
            ResultRow(f"{prefix}_loss", "Total-pressure loss",
                      100.0 * (1.0 - result.stagnation_pressure_ratio), "%", label),
        ])

    return CalculatorResult(
        True, pair.weak.mach2, tuple(rows), "Both branches",
        "Both wave angles turn the flow through the same deflection. The strong shock "
        "loses more stagnation pressure and always leaves subsonic flow behind it.",
        solution.diagnostics, "both",
        (pair.weak.beta, pair.strong.beta),
    )


# ---------------------------------------------------------------------------
# the parameter study
# ---------------------------------------------------------------------------


class TableConvention(StrEnum):
    """Which columns the generated study prints.

    ``BRANCH`` sweeps the deflection on one chosen branch and reports the full
    downstream state, which is readable. ``COMPARISON`` puts the two branches
    side by side with fewer columns each, for the question "how much worse is
    the strong solution".
    """

    BRANCH = "branch"
    COMPARISON = "comparison"


_BRANCH_COLUMNS = (
    TableColumn("theta", "θ", "°", 4),
    TableColumn("beta", "β", "°", 6),
    TableColumn("mach2", "M₂", "", 6),
    TableColumn("pressure_ratio", "p₂/p₁", "", 6),
    TableColumn("density_ratio", "ρ₂/ρ₁", "", 6),
    TableColumn("temperature_ratio", "T₂/T₁", "", 6),
    TableColumn("stagnation_pressure_ratio", "p₀₂/p₀₁", "", 6),
)

_COMPARISON_COLUMNS = (
    TableColumn("theta", "θ", "°", 4),
    TableColumn("beta_weak", "β weak", "°", 6),
    TableColumn("beta_strong", "β strong", "°", 6),
    TableColumn("mach2_weak", "M₂ weak", "", 6),
    TableColumn("mach2_strong", "M₂ strong", "", 6),
    TableColumn("p02_weak", "p₀₂/p₀₁ weak", "", 6),
    TableColumn("p02_strong", "p₀₂/p₀₁ strong", "", 6),
)


def columns_for(convention: TableConvention | str) -> tuple[TableColumn, ...]:
    """The column set a convention prints."""
    return (_COMPARISON_COLUMNS
            if TableConvention(convention) is TableConvention.COMPARISON
            else _BRANCH_COLUMNS)


def generate_table(
    mach1: float,
    gamma: float,
    start_degrees: float,
    end_degrees: float,
    step_degrees: float,
    convention: TableConvention | str = TableConvention.BRANCH,
    branch: ShockBranch | str = ShockBranch.WEAK,
) -> TableData:
    """Sweep the deflection for one upstream Mach number.

    The range is capped at the attachment limit rather than filled with fake
    rows: past it there is no attached shock, and a table of substituted values
    would be the worst possible way to say so. The cap is reported in the
    metadata so the interface can tell the user it happened.
    """
    gas = PerfectGas(gamma=float(gamma))
    value = float(mach1)
    limit = obl.theta_max(value, gas).unwrap()
    limit_degrees = math.degrees(limit.theta_max)

    if not np.isfinite([start_degrees, end_degrees, step_degrees]).all():
        raise ValueError("Deflection range and step must be finite numbers.")
    if step_degrees <= 0.0:
        raise ValueError("Step must be greater than zero.")
    if start_degrees < 0.0:
        raise ValueError("Start deflection cannot be negative.")
    if end_degrees <= start_degrees:
        raise ValueError("End deflection must be greater than the start deflection.")

    capped = min(float(end_degrees), limit_degrees)
    if capped <= start_degrees:
        raise ValueError(
            f"No attached shock exists above θ_max = {limit_degrees:.4f}°, so a sweep "
            f"starting at {start_degrees:g}° has nothing to compute for Mach {value:g}."
        )

    count = int(np.floor((capped - start_degrees) / step_degrees + 1e-9)) + 1
    if count > MAX_TABLE_ROWS:
        raise ValueError(
            f"That range and step would produce {count:,} rows, above the "
            f"{MAX_TABLE_ROWS:,} row limit. Increase the step or narrow the range."
        )
    grid = start_degrees + step_degrees * np.arange(count, dtype=np.float64)
    # The limit itself is worth a row: it is where the two branches merge.
    if abs(grid[-1] - limit_degrees) > 1e-9:
        grid = np.append(grid, limit_degrees)

    convention = TableConvention(convention)
    rows = []
    for theta_degrees in grid:
        theta = math.radians(float(theta_degrees))
        if convention is TableConvention.COMPARISON:
            pair = obl.solve_both(value, theta, gas)
            if not pair.ok:
                continue
            weak, strong = pair.unwrap().weak, pair.unwrap().strong
            rows.append([
                float(theta_degrees), math.degrees(weak.beta), math.degrees(strong.beta),
                weak.mach2, strong.mach2,
                weak.stagnation_pressure_ratio, strong.stagnation_pressure_ratio,
            ])
        else:
            solution = obl.solve(value, theta, gas, ShockBranch(branch))
            if not solution.ok:
                continue
            result = solution.unwrap()
            rows.append([
                float(theta_degrees), math.degrees(result.beta), result.mach2,
                result.pressure_ratio, result.density_ratio, result.temperature_ratio,
                result.stagnation_pressure_ratio,
            ])

    block = np.array(rows, dtype=np.float64) if rows else np.zeros((0, len(columns_for(convention))))
    marker = int(block.shape[0] - 1) if block.size else None

    return TableData(
        columns=columns_for(convention),
        values=block,
        gamma=gas.gamma,
        convention=convention,
        sonic_row=marker,
        message="",
        metadata={
            "mach1": value,
            "start": float(start_degrees),
            "end": float(capped),
            "requested_end": float(end_degrees),
            "capped_at_theta_max": bool(end_degrees > limit_degrees),
            "step": float(step_degrees),
            "rows": int(block.shape[0]),
            "model": "perfect_gas_oblique_shock_v1",
            "theta_max": limit_degrees,
            "beta_at_theta_max": math.degrees(limit.beta_at_theta_max),
            "mach_angle": math.degrees(limit.mach_angle),
            "branch": str(ShockBranch(branch).value),
            "angle_units": "degrees",
        },
    )


# ---------------------------------------------------------------------------
# diagram data
# ---------------------------------------------------------------------------


def curve_data(mach1: float, gamma: float, points: int = 400) -> dict:
    """The theta-beta-M curve for one Mach number, in degrees.

    Split at the wave angle of maximum deflection into the two branches the
    diagram draws separately, plus the three markers. The split happens here
    rather than in the interface because it is a physical boundary, not a
    drawing decision -- and because the same boundary decides which branch the
    calculator solved.
    """
    gas = PerfectGas(gamma=float(gamma))
    curve = obl.theta_beta_curve(float(mach1), gas, points).unwrap()

    beta = np.degrees(curve.beta)
    theta = np.degrees(curve.theta)
    peak = math.degrees(curve.beta_at_theta_max)
    weak = beta <= peak

    return {
        "mach1": curve.mach1,
        "weak": [{"x": float(t), "y": float(b)} for t, b in zip(theta[weak], beta[weak])],
        "strong": [{"x": float(t), "y": float(b)} for t, b in zip(theta[~weak], beta[~weak])],
        "thetaMax": math.degrees(curve.theta_max),
        "betaAtThetaMax": peak,
        "betaSonic": math.degrees(curve.beta_sonic),
        "machAngle": math.degrees(curve.mach_angle),
    }
