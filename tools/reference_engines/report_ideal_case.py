"""Print the DB-4C ideal reference cases, one point after the other. Run by hand, in the CEA environment:

    .venv-cea\\Scripts\\python.exe tools\\reference_engines\\report_ideal_case.py

Writes nothing. The test suite does not run this and pins none of its numbers. A difference here is a reading, never
a pass or fail, and no rule, input or pairing may change in response to one (DB4C_SSME_TDK_IDEAL_REFERENCE.md §8).
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from rocketforge.application.analysis.reference_ideal_case import (  # noqa: E402
    KIND_OK,
    IdealCaseOutcome,
    run_ideal_cases,
)
from rocketforge.core.constants import STANDARD_GRAVITY  # noqa: E402


def _shown(key: str, value_si: float) -> tuple[float, str]:
    """Isp in seconds, temperature in kelvin: the units the rows are read in."""
    return (value_si / STANDARD_GRAVITY, "s") if key.startswith("vacuum_specific_impulse") else (value_si, "K")


def _report(out: IdealCaseOutcome) -> None:
    case, point, run = out.case, out.point, out.chamber_case
    print(f"\n=== {case.title} ({case.case_id})")
    print(f"  source: {case.source}")
    print(f"  run: {run.fuel} {run.fuel_temperature:g} K, {run.oxidiser} {run.oxidiser_temperature:g} K, "
          f"O/F {run.oxidiser_fuel_ratio}, Pc {run.chamber_pressure:.3f} Pa ({point.chamber_pressure_psia:g} psia), "
          f"area ratio {point.area_ratio}")
    if out.kind != KIND_OK:
        print(f"  {out.kind}: {out.message}")
        return

    print(f"\n  Step A: the printout against the same model class ({out.step_a.verdict}, no verdict)")
    for row in out.step_a.rows:
        ref, unit = _shown(row.key, row.reference)
        seen, _ = _shown(row.key, row.observed)
        diff, _ = _shown(row.key, row.abs_diff)
        print(f"    {row.key:38} TDK {ref:10.4f} {unit}   computed {seen:10.4f} {unit}   "
              f"difference {diff:+9.4f} {unit} ({row.rel_diff:+.3%})   {row.verdict}")
    if out.step_a.not_observed:
        print(f"    not observed: {', '.join(out.step_a.not_observed)}")

    print("\n  Step B: RocketForge's constant-gamma reduction against CEA, same point (the printout takes no part)")
    for row in out.step_b:
        print(f"    {row.gamma_basis:12} basis vs CEA {row.oracle_mode:12} RocketForge {row.rocketforge_isp_s:9.4f} s   "
              f"CEA {row.cea_isp_s:9.4f} s   ({row.relative_difference:+.3%})   {row.kind}; {row.reference}")

    print("\n  Declarations:")
    for line in out.declarations:
        print(f"    - {line}")
    for line in out.warnings:
        print(f"    warning: {line}")


def main() -> int:
    outcomes = run_ideal_cases()
    first = outcomes[0].case
    print(f"DB-4C ideal reference cases, {len(outcomes)} points\ncode: {first.code}; {first.code_version}")
    print("Each point is set beside CEA on its own; no row compares any two points.")
    for out in outcomes:
        _report(out)
    return 0 if all(out.kind == KIND_OK for out in outcomes) else 2


if __name__ == "__main__":
    raise SystemExit(main())
