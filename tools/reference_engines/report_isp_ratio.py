"""Print the DB-4B engine-level Isp ratios. Run by hand, in the CEA environment:

    .venv-cea\\Scripts\\python.exe tools\\reference_engines\\report_isp_ratio.py

Writes nothing. The test suite does not run this and pins none of its numbers: a ratio is a reading, not a
pass or fail, and no model or rule may change in response to one (DB4B_ENGINE_ISP_RATIO_COMPARISON.md §6).
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from rocketforge.application.analysis.reference_engine_catalog import load_reference_engines  # noqa: E402
from rocketforge.application.analysis.reference_engine_isp_ratio import (  # noqa: E402
    KIND_OK,
    eligibility,
    eligible_configurations,
    run_isp_ratio,
)


def main() -> int:
    catalog = load_reference_engines()
    status = 0
    for cfg in eligible_configurations(catalog):
        inputs = eligibility(catalog, cfg).inputs
        outcome = run_isp_ratio(catalog, cfg)
        print(f"\n{cfg}: {catalog.entry(cfg).label}")
        print(f"  printed Isp {inputs.printed_isp_s:g} s, {inputs.environment}; Pc {inputs.chamber_pressure_pa:.6g} Pa; "
              f"O/F {inputs.oxidiser_fuel_ratio:g}; area ratio {inputs.area_ratio:g}")
        if outcome.kind != KIND_OK:
            print(f"  {outcome.kind}: {outcome.message}")
            status = 2
            continue
        for cell in outcome.result.cells:
            print(f"  {cell.gamma_basis:12} ideal Isp {cell.ideal_isp_s:8.2f} s   ratio {cell.ratio:.4f}")
        for line in outcome.result.declarations:
            print(f"  - {line}")
        for line in outcome.warnings:
            print(f"  warning: {line}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
