"""The shapes an analysis hands to whatever displays it.

Three services -- isentropic, mass flow, normal shock -- all answer the same
two questions: "what are the numbers at this one condition" and "give me a
table over a range". They differ in physics, not in the shape of the answer,
so the shape lives here once.

Deliberately free of Qt, and free of gas dynamics. Nothing in this file knows
what a Mach number is; it knows what a labelled value is.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ...core.result import Diagnostic

__all__ = [
    "ResultRow",
    "CalculatorResult",
    "TableColumn",
    "TableData",
    "MAX_TABLE_ROWS",
]

#: Guard against a step of 1e-9 across a range of 5 allocating tens of millions
#: of rows. Chosen so that the largest sensible table -- the full 0.01 to 50
#: range at a step of 0.005 -- still fits with room to spare, while an
#: accidental step keeps the application responsive instead of hanging it.
MAX_TABLE_ROWS = 20_000


@dataclass(frozen=True, slots=True)
class ResultRow:
    """One labelled quantity in a calculator readout."""

    key: str
    label: str
    value: float | None
    unit: str = ""
    group: str = ""
    emphasis: bool = False


@dataclass(frozen=True, slots=True)
class CalculatorResult:
    """Everything a calculator produced from one set of inputs.

    ``ok`` is False for invalid input rather than an exception reaching the
    interface: a half-typed number is an ordinary event on screen, not a fault.
    The physics still raises; the service is the only place that catches.
    """

    ok: bool
    mach: float | None
    rows: tuple[ResultRow, ...]
    status: str                       # valid | sonic | near sonic | invalid
    message: str
    diagnostics: tuple[Diagnostic, ...] = ()
    branch_used: str = ""
    both: tuple[float, float] | None = None   # (subsonic, supersonic) when asked

    def value_of(self, key: str) -> float | None:
        """One readout by key, or None if this result does not carry it."""
        for row in self.rows:
            if row.key == key:
                return row.value
        return None


@dataclass(frozen=True, slots=True)
class TableColumn:
    """One column of a generated engineering table."""

    key: str
    label: str
    unit: str = ""
    decimals_hint: int = 6


@dataclass(frozen=True, slots=True)
class TableData:
    """A generated table: columns, a numeric block, and how it was made."""

    columns: tuple[TableColumn, ...]
    values: np.ndarray                # shape (rows, columns), float64
    gamma: float
    convention: object = None
    sonic_row: int | None = None
    #: Row index -> label, for tables with more than one critical row. A
    #: Rayleigh table marks the static-temperature maximum as well as the sonic
    #: state, and conflating the two would be the single most misleading thing
    #: that page could do.
    markers: dict = field(default_factory=dict)
    message: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return int(self.values.shape[0])

    @property
    def column_count(self) -> int:
        return int(self.values.shape[1])
