"""What the Reference Cases workspace shows, as text: the one place a DB-4C number becomes a string.

Pure: no Qt and no provider. It formats what :mod:`.reference_ideal_case` returns
and what the case modules print, and computes nothing. The controller hands its
rows to QML, which only places them (DB4C_IDEAL_REFERENCE_DISPLAY.md §6, §8).

What it keeps, from DB-4C and the display review:

- step A and step B are separate row sets, and no row sets RocketForge beside a
  printout or one point beside another;
- every difference is signed, names its operands in its column head, and has its
  absolute value beside its relative one;
- printed values keep their printed decimals, and computed values take the
  decimals of the printed value they stand beside;
- an absent value reads "not run" or "not formed", never zero.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from rocketforge.comparison import ssme_tdk_1985, tdk_manual_1985
from rocketforge.comparison.tdk_1985 import (
    KEY_CHAMBER_TEMPERATURE,
    KEY_VACUUM_ISP_EQUILIBRIUM,
    KEY_VACUUM_ISP_FROZEN,
    TdkPoint,
)
from rocketforge.core.constants import STANDARD_GRAVITY

__all__ = [
    "DOCUMENTS",
    "NOT_RUN",
    "NOT_FORMED",
    "STEP_A_HEADS",
    "STEP_B_HEADS",
    "STEP_A_NOTE",
    "STEP_B_NOTE",
    "CLASS_LINE",
    "STATE_WORDS",
    "PointText",
    "signed",
    "point_text",
    "browser_rows",
    "run_input_rows",
    "step_a_rows",
    "step_b_rows",
    "declaration_lines",
    "warning_lines",
    "stop_line",
]

NOT_RUN = "not run"
NOT_FORMED = "not formed"
MINUS = "−"

#: The points by document, in the runner's order. A test checks this is exactly ``POINTS``.
DOCUMENTS: tuple[tuple[str, tuple[TdkPoint, ...]], ...] = (
    ("NASA-CR-178740 · 1985 TDK report on the SSME", ssme_tdk_1985.POINTS),
    ("NASA-CR-178628 · 1985 TDK manual's samples", tdk_manual_1985.POINTS),
)

STEP_A_HEADS = ("Quantity", "TDK 1985, as printed", "NASA CEA", f"CEA {MINUS} TDK", "Kind")
STEP_B_HEADS = ("Gamma basis", "RocketForge, vacuum", "NASA CEA, vacuum, matching expansion",
                f"RocketForge {MINUS} CEA", "Kind")
STEP_A_NOTE = ("Two codes on the same inputs. A difference is code and thermodynamic data plus the declared input "
               "differences; it is never a RocketForge defect.")
STEP_B_NOTE = ("The same point; the printout takes no part. RocketForge holds gamma and R constant through the "
               "expansion, CEA does not: a model difference, not an error.")
CLASS_LINE = "Independent code: compared, never judged"

#: A point's or a run's state, as words. The word carries the meaning; a tone may only repeat it.
STATE_WORDS = {
    "not-run": "Not run",
    "ok": "Computed",
    "refused": "Refused",
    "unavailable": "Unavailable",
}

_QUANTITY_LABELS = {
    KEY_CHAMBER_TEMPERATURE: "Chamber temperature",
    KEY_VACUUM_ISP_EQUILIBRIUM: "Vacuum Isp, shifting equilibrium",
    KEY_VACUUM_ISP_FROZEN: "Vacuum Isp, frozen at the chamber",
}
_COMPUTED_BY = {
    KEY_CHAMBER_TEMPERATURE: "RocketForge's chamber, a CEA equilibrium solve",
    KEY_VACUUM_ISP_EQUILIBRIUM: "CEA",
    KEY_VACUUM_ISP_FROZEN: "CEA",
}
_MODE_WORDS = {"frozen": "frozen", "equilibrium": "shifting equilibrium"}


def _number(value: float, decimals: int) -> str:
    """A plain number at ``decimals``, with a true minus sign."""
    text = f"{value:.{decimals}f}"
    return text.replace("-", MINUS)


def signed(value: float, decimals: int) -> str:
    """A number that always carries its sign: ``+0.2654``, ``−0.4473``."""
    text = f"{value:+.{decimals}f}"
    return text.replace("-", MINUS)


def _relative(fraction: float | None) -> str:
    return NOT_FORMED if fraction is None else f"{signed(fraction * 100.0, 3)} %"


def _grouped(value: float, decimals: int) -> str:
    """Digits grouped in threes with thin spacing, as DB-4C writes a pressure in Pa."""
    whole, _, fraction = f"{value:.{decimals}f}".partition(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    return " ".join(groups) + ("." + fraction if fraction else "")


@dataclass(frozen=True, slots=True)
class PointText:
    """A point's fixed texts: they come from its case record and need no run."""

    key: str
    name: str
    document: str
    title: str
    citation: str
    code: str
    database: str
    inputs_line: str
    missing: tuple[str, ...]
    notes: str


def _document_of(point: TdkPoint) -> str:
    for label, points in DOCUMENTS:
        if point in points:
            return label
    raise ValueError(f"{point.case.case_id} belongs to no document")


def point_text(point: TdkPoint) -> PointText:
    case = point.case
    return PointText(
        key=case.case_id,
        name=case.title.split(",")[0],
        document=_document_of(point),
        title=case.title,
        citation=case.source,
        code=f"{case.code}; version {case.code_version}",
        database=f"Thermodynamic data: {case.database_version}",
        inputs_line=(f"{point.chamber_pressure_psia:g} psia · O/F {point.oxidiser_fuel_ratio} · "
                     f"area ratio {point.area_ratio}"),
        missing=tuple(case.missing),
        notes=case.notes,
    )


def browser_rows(points: Sequence[TdkPoint], states: Sequence[str]) -> list[dict[str, Any]]:
    """One row per point: name, document, inputs and run state. Never a difference."""
    rows, previous = [], None
    for point, state in zip(points, states, strict=True):
        text = point_text(point)
        rows.append({
            "pointKey": text.key,
            "pointName": text.name,
            "section": text.document,
            "sectionStart": text.document != previous,
            "inputsLine": text.inputs_line,
            "pointState": state,
            "pointStateWord": STATE_WORDS[state],
        })
        previous = text.document
    return rows


def run_input_rows(run: Any, point: TdkPoint) -> list[dict[str, str]]:
    """What is (or will be) run, from the runner's own run record: ``chamber_case(point)`` or an outcome's."""
    return [
        {"inputLabel": "Fuel", "inputText": f"{run.fuel}, {run.fuel_temperature:g} K"},
        {"inputLabel": "Oxidiser", "inputText": f"{run.oxidiser}, {run.oxidiser_temperature:g} K"},
        {"inputLabel": "Mixture ratio", "inputText": f"O/F {run.oxidiser_fuel_ratio} by mass"},
        {"inputLabel": "Chamber pressure",
         "inputText": f"{point.chamber_pressure_psia:g} psia ({_grouped(run.chamber_pressure, 3)} Pa)"},
        {"inputLabel": "Area ratio", "inputText": f"{point.area_ratio}, vacuum"},
    ]


def _printed(quantity: Any, key: str) -> tuple[str, int]:
    """The printed value in the display unit, with the decimals that stand for it."""
    if key == KEY_CHAMBER_TEMPERATURE:
        kelvin = quantity.value * 5.0 / 9.0
        return (f"{_number(kelvin, quantity.decimals)} K ({_number(quantity.value, quantity.decimals)} R as printed)",
                quantity.decimals)
    return f"{_number(quantity.value, quantity.decimals)} s (lbf·s/lbm as printed)", quantity.decimals


def step_a_rows(point: TdkPoint, comparison: Any | None) -> list[dict[str, str]]:
    """Step A: the printout beside CEA. Before a run, the printed values with "not run" beside them."""
    rows_by_key = {row.key: row for row in comparison.rows} if comparison is not None else {}
    rows = []
    for quantity in point.case.quantities:
        printed, decimals = _printed(quantity, quantity.key)
        row = rows_by_key.get(quantity.key)
        if row is None:
            computed = difference = NOT_RUN
            kind = ""
        else:
            temperature = quantity.key == KEY_CHAMBER_TEMPERATURE
            scale, unit = (1.0, "K") if temperature else (1.0 / STANDARD_GRAVITY, "s")
            computed = f"{_number(row.observed * scale, decimals)} {unit}, {_COMPUTED_BY[quantity.key]}"
            difference = f"{signed(row.abs_diff * scale, decimals)} {unit} ({_relative(row.rel_diff)})"
            kind = row.verdict
        rows.append({"quantity": _QUANTITY_LABELS[quantity.key], "printed": printed, "computed": computed,
                     "difference": difference, "kind": kind})
    return rows


def step_b_rows(step_b: Sequence[Any]) -> list[dict[str, str]]:
    """Step B: RocketForge's reduction beside CEA, both bases, never one highlighted. Empty before a run."""
    rows = []
    for row in step_b:
        absolute = row.rocketforge_isp_s - row.cea_isp_s
        rows.append({
            "basis": row.gamma_basis,
            "rocketforge": f"{_number(row.rocketforge_isp_s, 4)} s",
            "cea": f"{_number(row.cea_isp_s, 4)} s ({_MODE_WORDS.get(row.oracle_mode, row.oracle_mode)})",
            "difference": f"{signed(absolute, 4)} s ({_relative(row.relative_difference)})",
            "kind": row.kind,
            "reference": row.reference,
        })
    return rows


def declaration_lines(declarations: Sequence[str]) -> list[dict[str, str]]:
    return [{"line": line} for line in declarations]


def warning_lines(warnings: Sequence[str] | None) -> list[dict[str, str]]:
    """The provider's warnings verbatim; "none" when a run raised none; nothing before a run."""
    if warnings is None:
        return []
    return [{"line": line} for line in warnings] or [{"line": "none"}]


def stop_line(kind: str, message: str) -> str:
    """Why a point stopped, with its kind. It replaces both step tables, never sits beside one."""
    return f"{STATE_WORDS.get(kind, kind)}: {message}"
