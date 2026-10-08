"""Display rows for the propulsion-system studies (SYS gates). Qt-free.

Every SYS page shows the same shapes -- grouped branch quantities, a ledger,
named states, totals -- and converts units only here, at the boundary. A
gate supplies its quantity table, its groups and a display table
``key -> (unit, scale, format)``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from rocketforge.engine.propulsion_system.records import BranchOutcome, Quantity, StudyResult

__all__ = [
    "LEDGER_UNITS",
    "branch_groups",
    "display_value",
    "label_rows",
    "ledger_rows",
    "series_rows",
    "total_rows",
]

Display = Mapping[str, tuple[str, float, str]]

#: How a ledger line in an SI unit is shown.
LEDGER_UNITS: dict[str, tuple[str, float, str]] = {
    "kg": ("kg", 1.0, ",.4f"),
    "Pa": ("bar", 1.0e-5, ",.4f"),
    "m3": ("L", 1.0e3, ",.4f"),
}

_STATUS_WORDS = {"resolved": "", "not_applicable": "not applicable",
                 "unresolved": "UNRESOLVED", "excluded": "excluded"}


def display_value(display: Display, key: str, value: float | None) -> str:
    if value is None:
        return "—"
    _unit, scale, spec = display[key]
    return format(value * scale, spec)


def _row(display: Display, q: Quantity, value: float | None, reason: str) -> dict[str, str]:
    return {"key": q.key, "label": q.label, "unit": display[q.key][0], "note": q.note,
            "value": display_value(display, q.key, value), "reason": reason,
            "status": "resolved" if value is not None else "unresolved"}


def branch_groups(outcome: BranchOutcome, quantities: Sequence[Quantity],
                  groups: Sequence[tuple[str, str]], display: Display) -> list[dict[str, Any]]:
    """Every branch quantity, grouped for display, with unit, note and reason.
    A group with no row is left out."""
    out = []
    for key, title in groups:
        rows = [_row(display, q, outcome.value(q.key), outcome.unresolved.get(q.key, ""))
                for q in quantities if q.group == key]
        if rows:
            out.append({"key": key, "title": title, "rows": rows})
    return out


def ledger_rows(outcome: BranchOutcome) -> list[dict[str, str]]:
    rows = []
    for line in outcome.ledger:
        unit, scale, spec = LEDGER_UNITS.get(line.unit, (line.unit, 1.0, ",.6g"))
        rows.append({"key": line.key, "label": line.label, "status": line.status,
                     "value": (format(line.value * scale, spec) if line.value is not None
                               else _STATUS_WORDS[line.status]),
                     "unit": unit if line.value is not None else "",
                     "note": line.source, "reason": line.reason})
    return rows


def label_rows(outcome: BranchOutcome, labels: Sequence[tuple[str, str]]) -> list[dict[str, str]]:
    """Named states, in order: ``labels`` is (key, label)."""
    return [{"key": key, "label": label, "value": outcome.labels.get(key, "—"), "unit": "",
             "note": "", "reason": "", "status": "resolved"}
            for key, label in labels if key in outcome.labels]


def series_rows(outcome: BranchOutcome, columns: Sequence[tuple[str, str, float, str]]
                ) -> dict[str, Any]:
    """A short table: ``columns`` is (key, header, scale, format)."""
    return {"headers": [header for _k, header, _s, _f in columns],
            "rows": [[format(row[key] * scale, spec) if key in row else "—"
                      for key, _h, scale, spec in columns] for row in outcome.series]}


def total_rows(result: StudyResult, totals: Sequence[Quantity], display: Display
               ) -> list[dict[str, str]]:
    return [_row(display, q, result.totals.get(q.key), result.totals_unresolved.get(q.key, ""))
            for q in totals]
