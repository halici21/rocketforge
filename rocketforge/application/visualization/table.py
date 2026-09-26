"""Table blocks: a contiguous run of generated rows, as a snapshot or as text.

The shared table contract's data side. A block is read from a table that has
already been generated -- its stored values and the text the view shows for
them -- and nothing is recomputed, reformatted or re-solved to make it. Pure:
no Qt, so a controller hands in its values and a way to read a cell's text.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Sequence

__all__ = ["table_block", "block_text", "clamp_block"]


def clamp_block(first: int, last: int, rows: int) -> tuple[int, int] | None:
    """``(first, last)`` ordered and inside ``rows``, or None when empty."""
    if rows <= 0:
        return None
    a, b = sorted((int(first), int(last)))
    a, b = max(0, a), min(rows - 1, b)
    return None if b < a else (a, b)


def _number(value) -> float | None:
    v = float(value)
    return v if math.isfinite(v) else None


def table_block(*, source: str, identity: int, columns: Sequence[dict],
                values: Sequence[Sequence[float]], text_at: Callable[[int, int], str],
                first: int, last: int, key_column: int = 0, key_symbol: str = "",
                stale: bool = False, **extra) -> dict:
    """A ``kind: "table"`` snapshot of rows ``first`` to ``last`` inclusive.

    ``rowKeys`` are the stored values of ``key_column`` (a Mach number, a
    station position), so a comparison aligns rows by what they are, not by
    where they sit. ``text`` is what the view showed, cell for cell.
    """
    span = clamp_block(first, last, len(values))
    if span is None:
        raise ValueError("no rows in this block")
    a, b = span
    width = len(columns)
    keys = [float(values[r][key_column]) for r in range(a, b + 1)]
    block = {
        "kind": "table", "source": source, "identity": int(identity),
        "columns": [{"key": str(c.get("key", "")), "label": str(c.get("label", "")),
                     "unit": str(c.get("unit", ""))} for c in columns],
        "rowKeys": keys,
        "values": [[_number(values[r][c]) for c in range(width)] for r in range(a, b + 1)],
        "text": [[str(text_at(r, c)) for c in range(width)] for r in range(a, b + 1)],
        "rangeLabel": (f"{key_symbol} {text_at(a, key_column)}–{text_at(b, key_column)}").strip(),
        "firstRow": a, "lastRow": b, "stale": bool(stale),
    }
    block.update(extra)
    return block


def block_text(header: Sequence[str], text_at: Callable[[int, int], str],
               first: int, last: int, width: int) -> str:
    """Rows ``first``..``last`` as tab-separated text, header first."""
    lines = ["\t".join(header)]
    for r in range(first, last + 1):
        lines.append("\t".join(str(text_at(r, c)) for c in range(width)))
    return "\n".join(lines)
