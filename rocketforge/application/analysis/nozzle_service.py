"""Nozzle analysis, prepared for presentation.

The adapter between ``rocketforge.physics.compressible.nozzle`` and whatever
displays it. It owns no gas dynamics: every number here comes from a physics
call, and the regime decisions are the physics layer's own enum rather than
strings chosen here.

What this file *does* own is the translation between how an engineer states a
nozzle problem and how the solver states it -- absolute back pressure or a
ratio, exit area or an area ratio -- and the shaping of a solved nozzle into
rows, a distribution table, chart series and a regime map. Deliberately free of
Qt, so all of it can be tested headlessly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from ...core.errors import RocketForgeError
from ...core.result import Diagnostic
from ...physics.compressible import PerfectGas
from ...physics.compressible import nozzle
from ...physics.compressible.geometry import AreaDistribution
from ...physics.compressible.types import (
    NozzleOperating,
    NozzleRegime,
    NozzleSolution,
)
from .presentation import (
    MAX_TABLE_ROWS,
    CalculatorResult,
    ResultRow,
    TableColumn,
    TableData,
)

__all__ = [
    "PressureMode",
    "AreaMode",
    "PRESSURE_MODES",
    "AREA_MODES",
    "ModeInfo",
    "NozzleInputs",
    "REGIME_INFO",
    "regime_info",
    "solve",
    "regime_bands",
    "back_pressure_sweep",
    "shock_position_sweep",
    "distribution_table",
    "columns_for",
    "MAX_TABLE_ROWS",
    "DEFAULT_RESOLUTION",
    "MAX_RESOLUTION",
]

#: Stations in the generated contour. A few hundred draws a smooth chart, and
#: the relations are algebraic along area, so there is nothing to gain from
#: thousands -- ``66`` asks for a guard rather than a million QML rows.
DEFAULT_RESOLUTION = 161
MAX_RESOLUTION = 2001


# ---------------------------------------------------------------------------
# how the problem is stated
# ---------------------------------------------------------------------------


class PressureMode(StrEnum):
    """Whether the back pressure is typed absolutely or as a fraction of p0."""

    ABSOLUTE = "absolute"
    RATIO = "ratio"


class AreaMode(StrEnum):
    """Whether the nozzle is given by two areas or by throat area and ratio."""

    AREAS = "areas"
    RATIO = "ratio"


@dataclass(frozen=True, slots=True)
class ModeInfo:
    key: str
    label: str
    hint: str


PRESSURE_MODES: tuple[ModeInfo, ...] = (
    ModeInfo(PressureMode.ABSOLUTE, "Absolute  p_b", "the ambient pressure, in Pa"),
    ModeInfo(PressureMode.RATIO, "Ratio  p_b/p₀",
             "the same pressure as a fraction of the reservoir"),
)

AREA_MODES: tuple[ModeInfo, ...] = (
    ModeInfo(AreaMode.AREAS, "A_t and A_e", "throat and exit area, in m²"),
    ModeInfo(AreaMode.RATIO, "A_t and A_e/A_t", "throat area and the area ratio"),
)


@dataclass(frozen=True, slots=True)
class NozzleInputs:
    """One complete statement of a nozzle problem, in SI.

    The interface may collect these in either of two ways per quantity; by the
    time they reach here they are canonical, which is why the solver never sees
    a mode flag.
    """

    gamma: float = 1.4
    gas_constant: float = 287.05
    stagnation_pressure: float = 1.0e6         # Pa
    stagnation_temperature: float = 3000.0     # K
    throat_area: float = 0.01                  # m²
    area_ratio_exit: float = 2.0               # Ae/At
    back_pressure: float = 5.0e5               # Pa
    resolution: int = DEFAULT_RESOLUTION

    @property
    def exit_area(self) -> float:
        return self.throat_area * self.area_ratio_exit

    @property
    def pressure_ratio_back(self) -> float:
        return self.back_pressure / self.stagnation_pressure

    def gas(self) -> PerfectGas:
        return PerfectGas(gamma=self.gamma, gas_constant=self.gas_constant)

    def geometry(self) -> AreaDistribution:
        """A plain cone at the stated areas.

        Explicitly a schematic: the module analyses a supplied contour and does
        not design one, so anything drawn from this must be labelled as the
        straight-walled cone it is. Only the area distribution matters to the
        physics; the wall angles set how that area is spread along x.
        """
        return AreaDistribution.conical(
            throat_area=self.throat_area,
            area_ratio=self.area_ratio_exit,
            n=int(np.clip(self.resolution, 5, MAX_RESOLUTION)))


# ---------------------------------------------------------------------------
# how a regime is described
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RegimeInfo:
    """The words that go with one regime, and the tone it is shown in."""

    regime: NozzleRegime
    label: str
    short: str
    tone: str                 # neutral | success | warning
    note: str
    external: str = ""        # what happens outside the exit plane, if anything


REGIME_INFO: tuple[RegimeInfo, ...] = (
    RegimeInfo(
        NozzleRegime.UNCHOKED_SUBSONIC, "Unchoked subsonic", "Unchoked", "neutral",
        "The throat never reaches Mach 1. The nozzle behaves as a venturi: the "
        "flow accelerates to the throat, decelerates in the diverging section, "
        "and leaves at the back pressure. Mass flow still depends on how hard "
        "the nozzle is being driven.",
    ),
    RegimeInfo(
        NozzleRegime.CHOKED_SUBSONIC_EXIT, "Choking onset", "Choking", "neutral",
        "The highest back pressure at which the throat is sonic. The diverging "
        "section is still subsonic all the way to the exit, and the supersonic "
        "pocket has zero extent -- there is no shock to find yet. Mass flow has "
        "reached its maximum and stops responding to back pressure from here down.",
    ),
    RegimeInfo(
        NozzleRegime.INTERNAL_NORMAL_SHOCK, "Internal normal shock", "Shock", "warning",
        "A normal shock stands inside the diverging section, at the one position "
        "where the subsonic flow behind it leaves at exactly the back pressure. "
        "Lower the back pressure and the shock moves downstream and strengthens.",
    ),
    RegimeInfo(
        NozzleRegime.SHOCK_AT_EXIT, "Shock at exit", "Shock at exit", "warning",
        "The shock has reached the exit plane. The flow inside the nozzle is now "
        "the full shock-free supersonic solution, and the jump happens at the very "
        "last station.",
    ),
    RegimeInfo(
        NozzleRegime.OVEREXPANDED, "Overexpanded", "Overexpanded", "neutral",
        "The flow is supersonic all the way to the exit with no internal shock, "
        "and leaves at a pressure below the ambient.",
        "Oblique shocks stand outside the exit plane and compress the jet. That "
        "external structure is not part of this model.",
    ),
    RegimeInfo(
        NozzleRegime.IDEALLY_EXPANDED, "Ideally expanded", "Ideal", "success",
        "The design point: the exit pressure equals the back pressure exactly, so "
        "the jet leaves without any external adjustment at all.",
    ),
    RegimeInfo(
        NozzleRegime.UNDEREXPANDED, "Underexpanded", "Underexpanded", "neutral",
        "The flow is supersonic to the exit with no internal shock, and leaves at "
        "a pressure above the ambient.",
        "Expansion fans stand off the exit plane and the jet keeps expanding. "
        "That external structure is not part of this model.",
    ),
)

_REGIME_INDEX = {info.regime: info for info in REGIME_INFO}


def regime_info(regime: NozzleRegime | str) -> RegimeInfo:
    return _REGIME_INDEX[NozzleRegime(regime)]


# ---------------------------------------------------------------------------
# the calculator
# ---------------------------------------------------------------------------


def _rows_for(record: NozzleSolution, inputs: NozzleInputs) -> tuple[ResultRow, ...]:
    critical = record.critical
    # The regime itself is not a row: it is the page's headline, stated in the
    # header chip and the regime panel. A row whose "value" is a word would
    # read as a missing number in a column of numbers.
    rows: list[ResultRow] = [
        ResultRow("pressure_ratio_back", "p_b/p₀", inputs.pressure_ratio_back, "",
                  "Regime", emphasis=True),
        ResultRow("pressure_ratio_exit", "p_e/p₀",
                  float(record.pressure_ratio[-1]), "", "Regime", emphasis=True),
        ResultRow("pressure_ratio_exit_over_back", "p_e/p_b",
                  float(record.pressure_ratio[-1]) / inputs.pressure_ratio_back, "",
                  "Regime"),

        ResultRow("mass_flow", "Mass flow  ṁ", record.mass_flow, "kg/s",
                  "Flow", emphasis=True),
        ResultRow("mach_throat", "Throat Mach  M_t", record.throat.mach, "",
                  "Flow", emphasis=True),
        ResultRow("mach_exit", "Exit Mach  M_e", record.exit.mach, "",
                  "Flow", emphasis=True),

        ResultRow("pressure_exit", "Exit pressure  p_e",
                  record.exit.pressure, "Pa", "Exit state"),
        ResultRow("temperature_exit", "Exit temperature  T_e",
                  record.exit.temperature, "K", "Exit state"),
        ResultRow("velocity_exit", "Exit velocity  V_e",
                  record.exit.velocity, "m/s", "Exit state"),
        ResultRow("density_exit", "Exit density  ρ_e",
                  record.exit.density, "kg/m³", "Exit state"),

        ResultRow("first_critical", "Choking onset   p_b/p₀",
                  critical.first_critical, "", "Thresholds", emphasis=True),
        ResultRow("second_critical", "Shock at exit   p_b/p₀",
                  critical.second_critical, "", "Thresholds", emphasis=True),
        ResultRow("third_critical", "Ideal expansion  p_b/p₀",
                  critical.third_critical, "", "Thresholds", emphasis=True),
        ResultRow("mach_exit_supersonic", "Design exit Mach",
                  critical.mach_exit_supersonic, "", "Thresholds"),
    ]

    if record.shock is not None:
        shock = record.shock
        rows.extend((
            ResultRow("shock_area_ratio", "Shock station  A_s/A_t",
                      shock.area_ratio_shock, "", "Shock", emphasis=True),
            ResultRow("shock_x", "Shock position  x_s", shock.x, "m", "Shock"),
            ResultRow("shock_mach_upstream", "Upstream  M₁",
                      shock.mach_upstream, "", "Shock", emphasis=True),
            ResultRow("shock_mach_downstream", "Downstream  M₂",
                      shock.mach_downstream, "", "Shock", emphasis=True),
            ResultRow("shock_pressure_ratio", "p₂/p₁", shock.pressure_ratio, "",
                      "Shock"),
            ResultRow("shock_stagnation_ratio", "p₀₂/p₀₁",
                      shock.stagnation_pressure_ratio, "", "Shock", emphasis=True),
            ResultRow("shock_total_pressure_loss", "Total-pressure loss",
                      1.0 - shock.stagnation_pressure_ratio, "", "Shock"),
            ResultRow("area_star_downstream", "Downstream  A₂*/A₁*",
                      shock.area_star_downstream_ratio, "", "Shock"),
        ))
    return tuple(rows)


def _status_for(record: NozzleSolution) -> tuple[str, str]:
    info = regime_info(record.regime)
    message = info.note
    if info.external:
        message = f"{message} {info.external}"
    tone = {"neutral": "valid", "success": "valid", "warning": "warning"}[info.tone]
    return tone, message


def solve(inputs: NozzleInputs) -> CalculatorResult:
    """Solve one nozzle and shape it for a readout.

    Invalid input is reported, never raised: a half-typed number is an ordinary
    event on screen. The physics still raises; this is the only place that
    catches.
    """
    try:
        solution = nozzle.solve(inputs.geometry(),
                                NozzleOperating(inputs.stagnation_pressure,
                                                inputs.back_pressure,
                                                inputs.stagnation_temperature),
                                inputs.gas())
    except RocketForgeError as error:
        return CalculatorResult(False, None, (), "invalid", str(error))

    record = solution.value
    if record is None:
        message = solution.diagnostics[0].message if solution.diagnostics else \
            "the nozzle could not be solved"
        return CalculatorResult(False, None, (), "invalid", message,
                                diagnostics=solution.diagnostics)

    status, message = _status_for(record)
    return CalculatorResult(
        ok=True,
        mach=record.exit.mach,
        rows=_rows_for(record, inputs),
        status=status,
        message=message,
        diagnostics=solution.diagnostics,
        branch_used=record.regime.value,
    )


def solve_record(inputs: NozzleInputs) -> NozzleSolution | None:
    """The raw solution, for the table, the charts and the regime map."""
    try:
        solution = nozzle.solve(inputs.geometry(),
                                NozzleOperating(inputs.stagnation_pressure,
                                                inputs.back_pressure,
                                                inputs.stagnation_temperature),
                                inputs.gas())
    except RocketForgeError:
        return None
    return solution.value


# ---------------------------------------------------------------------------
# the regime map
# ---------------------------------------------------------------------------


def regime_bands(inputs: NozzleInputs) -> list[dict]:
    """The seven regimes as bands on the p_b/p₀ axis.

    The band edges are the computed criticals, so the map is a picture of this
    nozzle rather than an authored illustration. Ideal expansion is a single
    point, not a range, and is returned with equal edges so a renderer can
    decide how to show a zero-width band -- rather than being widened into a
    lie.
    """
    try:
        critical = nozzle.critical_pressure_ratios(
            inputs.area_ratio_exit, inputs.gas()).unwrap()
    except RocketForgeError:
        return []

    first, second, third = (critical.first_critical, critical.second_critical,
                            critical.third_critical)
    spans = (
        (NozzleRegime.UNCHOKED_SUBSONIC, first, 1.0),
        (NozzleRegime.CHOKED_SUBSONIC_EXIT, first, first),
        (NozzleRegime.INTERNAL_NORMAL_SHOCK, second, first),
        (NozzleRegime.SHOCK_AT_EXIT, second, second),
        (NozzleRegime.OVEREXPANDED, third, second),
        (NozzleRegime.IDEALLY_EXPANDED, third, third),
        (NozzleRegime.UNDEREXPANDED, 0.0, third),
    )
    bands = []
    for regime, low, high in spans:
        info = regime_info(regime)
        bands.append({
            "key": regime.value,
            "label": info.label,
            "short": info.short,
            "tone": info.tone,
            "from": float(low),
            "to": float(high),
            "point": low == high,
            "note": info.note,
        })
    return bands


def thresholds(inputs: NozzleInputs) -> dict:
    """The three criticals, for the presets and the threshold panel."""
    try:
        critical = nozzle.critical_pressure_ratios(
            inputs.area_ratio_exit, inputs.gas()).unwrap()
    except RocketForgeError:
        return {}
    return {
        "first_critical": critical.first_critical,
        "second_critical": critical.second_critical,
        "third_critical": critical.third_critical,
        "mach_exit_subsonic": critical.mach_exit_subsonic,
        "mach_exit_supersonic": critical.mach_exit_supersonic,
    }


def back_pressure_sweep(inputs: NozzleInputs, count: int = 240) -> list[dict]:
    """Regime, exit Mach and mass flow across the whole back-pressure range.

    Classification is cheap -- no distributed solution is generated -- which is
    what makes a sweep of a few hundred points a sensible thing for a page to
    ask for.
    """
    gas = inputs.gas()
    try:
        critical = nozzle.critical_pressure_ratios(inputs.area_ratio_exit, gas).unwrap()
    except RocketForgeError:
        return []

    # Sampled uniformly, then with the three thresholds inserted exactly, so a
    # plot of the sweep shows the boundaries where they actually are.
    grid = np.linspace(0.999, 0.001, max(8, int(count)))
    grid = np.unique(np.concatenate([grid, [critical.first_critical,
                                            critical.second_critical,
                                            critical.third_critical]]))[::-1]
    out = []
    for back in grid:
        try:
            result = nozzle.classify(inputs.area_ratio_exit, float(back), gas).unwrap()
        except RocketForgeError:
            continue
        out.append({
            "pressure_ratio_back": float(back),
            "regime": result.regime.value,
            "mach_exit": float(result.mach_exit),
            "pressure_ratio_exit": float(result.pressure_ratio_exit),
            "shock_area_ratio": (float(result.shock.area_ratio_shock)
                                 if result.shock is not None else float("nan")),
            "choked": result.regime is not NozzleRegime.UNCHOKED_SUBSONIC,
        })
    return out


def shock_position_sweep(inputs: NozzleInputs, count: int = 120) -> list[dict]:
    """Where the shock stands, against the back pressure that puts it there.

    Solved with the same shock solver the calculator uses -- a second
    implementation for the plot would be a second thing to be wrong.
    """
    gas = inputs.gas()
    try:
        critical = nozzle.critical_pressure_ratios(inputs.area_ratio_exit, gas).unwrap()
    except RocketForgeError:
        return []

    geometry = inputs.geometry()
    span = np.linspace(critical.second_critical, critical.first_critical,
                       max(8, int(count)))
    out = []
    for back in span[1:-1]:
        located = nozzle.shock_area_ratio(inputs.area_ratio_exit, float(back), gas)
        if located.value is None:
            continue
        shock = located.value
        area = shock.area_ratio_shock * geometry.throat_area
        out.append({
            "pressure_ratio_back": float(back),
            "area_ratio_shock": float(shock.area_ratio_shock),
            "x": float(geometry.x_at_area(area, side="diverging")),
            "mach_upstream": float(shock.mach_upstream),
            "stagnation_pressure_ratio": float(shock.stagnation_pressure_ratio),
        })
    return out


# ---------------------------------------------------------------------------
# the distribution table
# ---------------------------------------------------------------------------


DIMENSIONAL_COLUMNS: tuple[TableColumn, ...] = (
    TableColumn("x", "x", "m", 5),
    TableColumn("area_ratio", "A/A_t", "", 5),
    TableColumn("mach", "M", "", 5),
    TableColumn("pressure", "p", "Pa", 4),
    TableColumn("temperature", "T", "K", 4),
    TableColumn("density", "ρ", "kg/m³", 5),
    TableColumn("velocity", "V", "m/s", 4),
    TableColumn("stagnation_pressure", "p₀", "Pa", 4),
)

NORMALIZED_COLUMNS: tuple[TableColumn, ...] = (
    TableColumn("x", "x", "m", 5),
    TableColumn("area_ratio", "A/A_t", "", 5),
    TableColumn("mach", "M", "", 5),
    TableColumn("pressure_ratio", "p/p₀₁", "", 6),
    TableColumn("temperature_ratio", "T/T₀₁", "", 6),
    TableColumn("stagnation_pressure_ratio", "p₀/p₀₁", "", 6),
)


def columns_for(normalized: bool) -> tuple[TableColumn, ...]:
    return NORMALIZED_COLUMNS if normalized else DIMENSIONAL_COLUMNS


def distribution_table(inputs: NozzleInputs, normalized: bool = False) -> TableData:
    """The solved distribution as a numeric block, with its critical rows marked.

    The two shock stations are kept as two rows sharing an x. Merging them, or
    interpolating between them, would erase the discontinuity the page exists
    to show.
    """
    columns = columns_for(normalized)
    record = solve_record(inputs)
    if record is None:
        return TableData(columns, np.empty((0, len(columns))), inputs.gamma,
                         message="The nozzle could not be solved for these inputs.")

    if not normalized and record.pressure is None:
        return TableData(columns, np.empty((0, len(columns))), inputs.gamma,
                         message=("Dimensional columns need a reservoir temperature "
                                  "and a gas constant."))

    source = {
        "x": record.x,
        "area_ratio": record.area_ratio,
        "mach": record.mach,
        "pressure": record.pressure,
        "temperature": record.temperature,
        "density": record.density,
        "velocity": record.velocity,
        "stagnation_pressure": record.stagnation_pressure,
        "pressure_ratio": record.pressure_ratio,
        "temperature_ratio": record.temperature_ratio,
        "stagnation_pressure_ratio": record.stagnation_pressure_ratio,
    }
    values = np.column_stack([np.asarray(source[c.key], dtype=float) for c in columns])

    markers: dict[int, str] = {}
    markers[record.throat_index] = "THROAT · SONIC" if record.choked else "THROAT"
    if record.shock_index is not None:
        markers[record.shock_index] = "PRE SHOCK"
        markers[record.shock_index + 1] = "POST SHOCK"
    markers[values.shape[0] - 1] = "EXIT"

    info = regime_info(record.regime)
    caption = (f"{values.shape[0]} stations · {info.label} · "
               f"A_e/A_t = {inputs.area_ratio_exit:g} · calculated by RocketForge")
    return TableData(columns, values, inputs.gamma,
                     sonic_row=record.throat_index if record.choked else None,
                     markers=markers, message=caption,
                     metadata={"regime": record.regime.value,
                               "shock_index": record.shock_index,
                               "throat_index": record.throat_index,
                               "normalized": normalized})
