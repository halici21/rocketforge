"""Print the DB-4C SSME ideal reference case. Run by hand, in the CEA environment:

    .venv-cea\\Scripts\\python.exe tools\\reference_engines\\report_ideal_case.py

Writes nothing. The test suite does not run this and pins none of its numbers. A difference here is a reading, never
a pass or fail, and no rule, input or pairing may change in response to one (DB4C_SSME_TDK_IDEAL_REFERENCE.md §8).
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from rocketforge.application.analysis.reference_ideal_case import KIND_OK, run_ideal_case  # noqa: E402
from rocketforge.core.constants import STANDARD_GRAVITY  # noqa: E402


def _shown(key: str, value_si: float) -> tuple[float, str]:
    """Isp in seconds, temperature in kelvin: the units the rows are read in."""
    return (value_si / STANDARD_GRAVITY, "s") if key.startswith("vacuum_specific_impulse") else (value_si, "K")


def main() -> int:
    out = run_ideal_case()
    case, point = out.case, out.chamber_case
    print(f"{case.title}\n  source: {case.source}\n  code: {case.code}; {case.code_version}")
    print(f"  run: {point.fuel} {point.fuel_temperature:g} K, {point.oxidiser} {point.oxidiser_temperature:g} K, "
          f"O/F {point.oxidiser_fuel_ratio:g}, Pc {point.chamber_pressure:.3f} Pa")
    if out.kind != KIND_OK:
        print(f"  {out.kind}: {out.message}")
        return 2

    print(f"\nStep A: the printout against the same model class ({out.step_a.verdict}, no verdict)")
    for row in out.step_a.rows:
        ref, unit = _shown(row.key, row.reference)
        seen, _ = _shown(row.key, row.observed)
        diff, _ = _shown(row.key, row.abs_diff)
        print(f"  {row.key:38} TDK {ref:10.4f} {unit}   computed {seen:10.4f} {unit}   "
              f"difference {diff:+9.4f} {unit} ({row.rel_diff:+.3%})   {row.verdict}")
    if out.step_a.not_observed:
        print(f"  not observed: {', '.join(out.step_a.not_observed)}")

    print("\nStep B: RocketForge's constant-gamma reduction against CEA, same point (the printout takes no part)")
    for row in out.step_b:
        print(f"  {row.gamma_basis:12} basis vs CEA {row.oracle_mode:12} RocketForge {row.rocketforge_isp_s:9.4f} s   "
              f"CEA {row.cea_isp_s:9.4f} s   ({row.relative_difference:+.3%})   {row.kind}; {row.reference}")

    print("\nDeclarations:")
    for line in out.declarations:
        print(f"  - {line}")
    for line in out.warnings:
        print(f"  warning: {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
