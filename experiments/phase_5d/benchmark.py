"""Phase 5D performance: how long the interface actually waits.

Measured through the **controller**, not through the provider, because the
number that matters is the one a user experiences: the solve plus the mapping
plus the table and series population. Solver time and interface-update time are
reported separately, so that if the interface dominates the fix is in the
interface rather than in the chemistry.

Usage::

    .venv-cea\\Scripts\\python.exe experiments\\phase_5d\\benchmark.py <outfile>
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QGuiApplication  # noqa: E402


def main(out: Path) -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    report: dict = {}

    t0 = time.perf_counter()
    from rocketforge.application.analysis.thermochemistry_controller import (
        ThermochemistryController,
    )
    report["controller_import_ms"] = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    controller = ThermochemistryController()
    report["controller_construction_ms"] = (time.perf_counter() - t0) * 1000.0

    # Availability is the first thing that touches the provider package.
    t0 = time.perf_counter()
    available = bool(controller.providerAvailable)
    report["first_availability_check_ms"] = (time.perf_counter() - t0) * 1000.0
    report["provider_available"] = available
    if not available:
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0

    # ---- single calculation ------------------------------------------
    t0 = time.perf_counter()
    controller.calculate()
    report["first_calculate_ms"] = (time.perf_counter() - t0) * 1000.0

    warm = []
    for _ in range(50):
        t0 = time.perf_counter()
        controller.calculate()
        warm.append((time.perf_counter() - t0) * 1000.0)
    report["warm_calculate_ms"] = {
        "median": statistics.median(warm),
        "mean": statistics.fmean(warm),
        "max": max(warm),
    }

    # How much of that is reading the result out for the interface?
    t0 = time.perf_counter()
    for _ in range(50):
        _ = controller.resultRows
        _ = controller.advancedRows
        _ = controller.diagnostics
        _ = controller.provenanceRows
    report["readout_publication_ms"] = (time.perf_counter() - t0) * 1000.0 / 50.0

    # ---- sweeps --------------------------------------------------------
    def sweep(points: int) -> dict:
        controller.sweepStart = 2.5
        controller.sweepEnd = 4.5
        controller.sweepPoints = points
        t = time.perf_counter()
        controller.runSweep()
        total = (time.perf_counter() - t) * 1000.0
        solver = float(controller.sweepElapsedMs)
        # What the interface then reads back, once per chart and table.
        t = time.perf_counter()
        for key in ("temperature", "molar_mass", "gamma"):
            _ = controller.sweepSeries(key)
            _ = controller.sweepAxis(key)
            _ = controller.sweepMaximum(key)
        _ = controller.sweepSpeciesSeries
        _ = controller.sweepWarnings
        _ = controller.sweepFixedConditions
        readback = (time.perf_counter() - t) * 1000.0
        return {
            "points": points,
            "solved": int(controller.sweepSolvedCount),
            "total_ms": total,
            "solver_ms": solver,
            "ui_build_ms": total - solver,
            "chart_readback_ms": readback,
            "per_point_ms": total / points,
        }

    report["sweep_41"] = sweep(41)
    report["sweep_101"] = sweep(101)

    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    report["sweep_max"] = sweep(controller.maxSweepPoints)
    after, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    report["sweep_max"]["retained_MB"] = (after - before) / 1e6
    report["sweep_max"]["peak_MB"] = peak / 1e6
    report["sweep_max"]["warning_rows"] = len(controller.sweepWarnings)

    # A second run of the same size, to show nothing accumulates.
    report["sweep_max_repeat"] = sweep(controller.maxSweepPoints)

    # ---- reference -----------------------------------------------------
    t0 = time.perf_counter()
    controller.runReference()
    report["reference_case_ms"] = (time.perf_counter() - t0) * 1000.0
    report["reference_verdict"] = controller.referenceVerdict

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    target = (Path(sys.argv[1]) if len(sys.argv) > 1
              else ROOT / "acceptance" / "phase_5d" / "ui_performance.json")
    sys.exit(main(target))
