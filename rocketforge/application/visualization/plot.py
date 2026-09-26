"""Snapshots, probe differences and comparability -- no physics.

A pinned snapshot records an analytical view of a solved result. Three kinds
share one session and one freezing rule:

- ``plot`` (the default when ``kind`` is absent): the range looked at, the
  quantity, its unit, the axis mode, the series as they were;
- ``table``: a block of generated table rows exactly as shown -- the columns
  with their units, each row's engineering key (a Mach number, a station
  index) and its raw values beside the formatted text;
- ``subset``: a chosen set of evaluated design points of one study run, with
  the filter and the visible columns that framed it.

Each records the result identity it came from and whether that result was
current or stale when pinned. Nothing re-solves to make one, nothing mutates
one after it is pinned, and snapshots of different kinds are never compared.
"""
from __future__ import annotations

import copy
import json
import math

__all__ = ["REQUIRED_SNAPSHOT_KEYS", "REQUIRED_TABLE_KEYS", "REQUIRED_SUBSET_KEYS",
           "SNAPSHOT_KINDS", "SnapshotError", "freeze_snapshot", "snapshot_kind",
           "compatibility", "probe_delta", "nearest_sample", "series_delta", "table_delta"]

REQUIRED_SNAPSHOT_KEYS = ("source", "identity", "quantity", "quantityLabel", "unit",
                          "xQuantity", "xLabel", "xUnit", "xRange", "yRange",
                          "axisMode", "series", "stale")

#: A table block: ``columns`` [{key, label, unit}], ``rowKeys`` (one engineering
#: key per row), ``values`` (raw numbers, ``None`` where a cell has none),
#: ``text`` (the cells as shown) and ``rangeLabel`` ("M 1.80–2.20").
REQUIRED_TABLE_KEYS = ("source", "identity", "columns", "rowKeys", "values", "text",
                       "rangeLabel", "stale")

#: A design-point subset: ``runIdentity`` names the study run the indices
#: belong to; ``indices`` the chosen points; ``filter`` and ``columns`` the view
#: that framed them; ``rows`` their values as shown.
REQUIRED_SUBSET_KEYS = ("source", "identity", "runIdentity", "indices", "filter",
                        "columns", "rows", "stale")

SNAPSHOT_KINDS = {"plot": REQUIRED_SNAPSHOT_KEYS, "table": REQUIRED_TABLE_KEYS,
                  "subset": REQUIRED_SUBSET_KEYS}


class SnapshotError(ValueError):
    """A snapshot is missing something it must say."""


def _finite_range(value, name) -> list[float]:
    if not (isinstance(value, (list, tuple)) and len(value) == 2):
        raise SnapshotError(f"{name} must be [lo, hi]")
    lo, hi = float(value[0]), float(value[1])
    if not (math.isfinite(lo) and math.isfinite(hi) and hi > lo):
        raise SnapshotError(f"{name} must be finite with hi > lo")
    return [lo, hi]


def snapshot_kind(snapshot: dict) -> str:
    """``plot`` unless the snapshot says otherwise."""
    return str(snapshot.get("kind", "plot"))


def freeze_snapshot(snapshot: dict) -> dict:
    """A validated, independent, JSON-round-tripped copy of ``snapshot``.

    Round-tripping through JSON proves it serializable and severs every
    reference to the caller's objects, so a later change to the live view
    cannot reach the pinned one.
    """
    if not isinstance(snapshot, dict):
        raise SnapshotError("a snapshot is a mapping")
    kind = snapshot_kind(snapshot)
    if kind not in SNAPSHOT_KINDS:
        raise SnapshotError(f"unknown snapshot kind {kind!r}")
    missing = [k for k in SNAPSHOT_KINDS[kind] if k not in snapshot]
    if missing:
        raise SnapshotError("snapshot is missing " + ", ".join(missing))
    frozen = json.loads(json.dumps(copy.deepcopy(snapshot), allow_nan=False))
    if kind == "table":
        return _check_table(frozen)
    if kind == "subset":
        return _check_subset(frozen)
    frozen["xRange"] = _finite_range(frozen["xRange"], "xRange")
    frozen["yRange"] = _finite_range(frozen["yRange"], "yRange")
    if frozen["axisMode"] not in ("linear", "log"):
        raise SnapshotError("axisMode is linear or log")
    for series in frozen["series"]:
        for point in series.get("points", []):
            if not (math.isfinite(point["x"]) and math.isfinite(point["y"])):
                raise SnapshotError("a series point is not finite")
    return frozen


def _check_table(frozen: dict) -> dict:
    n = len(frozen["rowKeys"])
    width = len(frozen["columns"])
    if n == 0:
        raise SnapshotError("a table snapshot holds at least one row")
    if len(frozen["values"]) != n or len(frozen["text"]) != n:
        raise SnapshotError("rowKeys, values and text must have one entry per row")
    for key in frozen["rowKeys"]:
        if not (isinstance(key, (int, float)) and math.isfinite(key)):
            raise SnapshotError("a row key is not a finite number")
    for row in frozen["values"]:
        if len(row) != width:
            raise SnapshotError("a row does not have one value per column")
        for v in row:
            if v is not None and not (isinstance(v, (int, float)) and math.isfinite(v)):
                raise SnapshotError("a table value is not finite")
    for column in frozen["columns"]:
        if "key" not in column or "label" not in column:
            raise SnapshotError("a column needs a key and a label")
    return frozen


def _check_subset(frozen: dict) -> dict:
    indices = frozen["indices"]
    if not indices:
        raise SnapshotError("a subset holds at least one design point")
    if any(not isinstance(i, int) or i < 0 for i in indices):
        raise SnapshotError("design-point indices are non-negative integers")
    if len(set(indices)) != len(indices):
        raise SnapshotError("a design point appears twice")
    if len(frozen["rows"]) != len(indices):
        raise SnapshotError("one row of values per design point")
    return frozen


def compatibility(a: dict, b: dict) -> dict:
    """Whether two snapshots can be overlaid and differenced, and why not."""
    if snapshot_kind(a) != snapshot_kind(b):
        return {"compatible": False, "reason": "different snapshot kinds"}
    if snapshot_kind(a) == "table":
        return _table_compatibility(a, b)
    if snapshot_kind(a) == "subset":
        return _subset_compatibility(a, b)
    reasons = []
    if a.get("quantity") != b.get("quantity"):
        reasons.append("different quantities")
    if a.get("unit") != b.get("unit"):
        reasons.append("different units")
    if a.get("xQuantity") != b.get("xQuantity") or a.get("xUnit") != b.get("xUnit"):
        reasons.append("different x axes")
    return {"compatible": not reasons, "reason": "; ".join(reasons)}


def probe_delta(a: dict, b: dict) -> dict:
    """Differences between two probes on compatible series.

    The percentage is only offered when the reference value is not zero; a
    percentage of zero is not a number.
    """
    if a.get("quantity") != b.get("quantity") or a.get("unit") != b.get("unit"):
        return {"compatible": False, "reason": "probes read different quantities"}
    dx = float(b["x"]) - float(a["x"])
    dy = float(b["y"]) - float(a["y"])
    ya = float(a["y"])
    pct = None if ya == 0.0 else dy / abs(ya) * 100.0
    return {"compatible": True, "dx": dx, "dy": dy, "percent": pct}


def nearest_sample(points: list[dict], x: float) -> dict | None:
    """The supplied point nearest ``x`` -- a real sample, never interpolated."""
    best, best_d = None, math.inf
    for p in points:
        d = abs(float(p["x"]) - x)
        if d < best_d:
            best, best_d = p, d
    return None if best is None else {"x": float(best["x"]), "y": float(best["y"])}


def series_delta(a: dict, b: dict, x: float) -> dict:
    """Snapshot B against A at the samples nearest ``x`` on each.

    Offered only for compatible snapshots, and only as a difference of real
    samples; when the nearest samples sit at different x the result says so
    rather than pretending they are one station.
    """
    if snapshot_kind(a) != "plot" or snapshot_kind(b) != "plot":
        return {"compatible": False, "reason": "not plot snapshots"}
    verdict = compatibility(a, b)
    if not verdict["compatible"]:
        return verdict
    pa = nearest_sample(a["series"][0]["points"], x) if a["series"] else None
    pb = nearest_sample(b["series"][0]["points"], x) if b["series"] else None
    if pa is None or pb is None:
        return {"compatible": True, "reason": "a snapshot has no samples"}
    delta = probe_delta({"x": pa["x"], "y": pa["y"], "quantity": a["quantity"], "unit": a["unit"]},
                        {"x": pb["x"], "y": pb["y"], "quantity": b["quantity"], "unit": b["unit"]})
    delta.update({"a": pa, "b": pb, "sameStation": pa["x"] == pb["x"]})
    return delta


def _column_signature(snapshot: dict) -> list[tuple[str, str]]:
    return [(str(c["key"]), str(c.get("unit", ""))) for c in snapshot["columns"]]


def _table_compatibility(a: dict, b: dict) -> dict:
    reasons = []
    if a.get("source") != b.get("source"):
        reasons.append("different tables")
    if _column_signature(a) != _column_signature(b):
        reasons.append("different columns or units")
    return {"compatible": not reasons, "reason": "; ".join(reasons)}


def _subset_compatibility(a: dict, b: dict) -> dict:
    reasons = []
    if a.get("source") != b.get("source"):
        reasons.append("different studies")
    elif a.get("runIdentity") != b.get("runIdentity"):
        # Design point 12 of one run is not design point 12 of another.
        reasons.append("different study runs")
    if _column_signature(a) != _column_signature(b):
        reasons.append("different columns or units")
    return {"compatible": not reasons, "reason": "; ".join(reasons)}


def table_delta(a: dict, b: dict) -> dict:
    """Table block B against A, row by row where their row keys are equal.

    Rows are aligned by their engineering key (the Mach number of a generated
    row, a station position), never by position: row 3 of one block is not
    row 3 of another. A key a block holds twice -- the pre- and post-shock
    rows of a nozzle distribution share one x -- is matched occurrence by
    occurrence, so the two sides of a shock are never merged. A row whose key
    the other block does not hold is counted, not matched to a neighbour. The
    first column is the key itself and carries no difference.
    """
    verdict = compatibility(a, b)
    if not verdict["compatible"]:
        return verdict
    if snapshot_kind(a) != "table":
        return {"compatible": False, "reason": "not table snapshots"}
    def occurrences(keys):
        seen, out = {}, []
        for k in keys:
            n = seen.get(float(k), 0)
            seen[float(k)] = n + 1
            out.append((float(k), n))
        return out

    index_b = {pair: j for j, pair in enumerate(occurrences(b["rowKeys"]))}
    rows = []
    for i, pair in enumerate(occurrences(a["rowKeys"])):
        key = pair[0]
        j = index_b.get(pair)
        if j is None:
            continue
        deltas = []
        for va, vb in zip(a["values"][i], b["values"][j]):
            deltas.append(None if va is None or vb is None else float(vb) - float(va))
        rows.append({"key": float(key), "deltas": deltas})
    width = len(a["columns"])
    max_abs = []
    for c in range(width):
        column = [abs(r["deltas"][c]) for r in rows if r["deltas"][c] is not None]
        max_abs.append(max(column) if column and c > 0 else None)
    return {"compatible": True, "reason": "", "matched": len(rows), "maxAbs": max_abs,
            "unmatchedA": len(a["rowKeys"]) - len(rows),
            "unmatchedB": len(b["rowKeys"]) - len(rows),
            "columns": [c["key"] for c in a["columns"]], "rows": rows}
