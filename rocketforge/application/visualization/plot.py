"""Plot snapshots, probe differences and comparability -- no physics.

A pinned snapshot records an analytical view of a solved result: the range
looked at, the quantity, its unit, the axis mode, the series as they were, the
result identity it came from and whether that result was current or stale
when pinned. Nothing re-solves to make one, and nothing mutates one after it
is pinned.
"""
from __future__ import annotations

import copy
import json
import math

__all__ = ["REQUIRED_SNAPSHOT_KEYS", "SnapshotError", "freeze_snapshot",
           "compatibility", "probe_delta", "nearest_sample", "series_delta"]

REQUIRED_SNAPSHOT_KEYS = ("source", "identity", "quantity", "quantityLabel", "unit",
                          "xQuantity", "xLabel", "xUnit", "xRange", "yRange",
                          "axisMode", "series", "stale")


class SnapshotError(ValueError):
    """A snapshot is missing something it must say."""


def _finite_range(value, name) -> list[float]:
    if not (isinstance(value, (list, tuple)) and len(value) == 2):
        raise SnapshotError(f"{name} must be [lo, hi]")
    lo, hi = float(value[0]), float(value[1])
    if not (math.isfinite(lo) and math.isfinite(hi) and hi > lo):
        raise SnapshotError(f"{name} must be finite with hi > lo")
    return [lo, hi]


def freeze_snapshot(snapshot: dict) -> dict:
    """A validated, independent, JSON-round-tripped copy of ``snapshot``.

    Round-tripping through JSON proves it serializable and severs every
    reference to the caller's objects, so a later change to the live view
    cannot reach the pinned one.
    """
    if not isinstance(snapshot, dict):
        raise SnapshotError("a snapshot is a mapping")
    missing = [k for k in REQUIRED_SNAPSHOT_KEYS if k not in snapshot]
    if missing:
        raise SnapshotError("snapshot is missing " + ", ".join(missing))
    frozen = json.loads(json.dumps(copy.deepcopy(snapshot), allow_nan=False))
    frozen["xRange"] = _finite_range(frozen["xRange"], "xRange")
    frozen["yRange"] = _finite_range(frozen["yRange"], "yRange")
    if frozen["axisMode"] not in ("linear", "log"):
        raise SnapshotError("axisMode is linear or log")
    for series in frozen["series"]:
        for point in series.get("points", []):
            if not (math.isfinite(point["x"]) and math.isfinite(point["y"])):
                raise SnapshotError("a series point is not finite")
    return frozen


def compatibility(a: dict, b: dict) -> dict:
    """Whether two snapshots can be overlaid and differenced, and why not."""
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
