"""The external NASA case: validate the oracle, then compare RocketForge to it.

Two comparisons, in this order and never merged:

1. **published vs the CEA oracle** -- two implementations of the same method on
   the same case. This is a validation, and its tolerance is the source's own
   rounding box.
2. **the oracle vs RocketForge** -- a shifting-equilibrium calorically
   imperfect calculation against a constant-property calorically perfect one.
   This is a model comparison, and calling its residual a RocketForge error
   would report a deliberate modelling choice as a defect.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rocketforge.application.analysis.performance_reference import (  # noqa: E402
    compare_published,
    overall_verdict,
    performance_reference_case,
)
from rocketforge.core.constants import STANDARD_GRAVITY  # noqa: E402
from rocketforge.engineering.chamber import (  # noqa: E402
    ChamberGammaBasis,
    reduce_chamber_gas,
)
from rocketforge.engineering.nozzle import (  # noqa: E402
    IdealPerformanceRequest,
    PerformanceScale,
    PerformanceScaleMode,
    solve_ideal_performance,
)
from rocketforge.physics.thermochemistry import (  # noqa: E402
    ChamberEquilibriumRequest,
    ExpansionMode,
    GammaStrategy,
    MixtureRatio,
    Phase,
    PropellantStream,
)


def main(out: Path) -> int:
    from rocketforge.providers.cea import (
        LIQUID_HYDROGEN,
        LOX,
        CEAThermochemistryProvider,
        check_availability,
    )
    from rocketforge.providers.cea.oracle import run_rocket_oracle
    from rocketforge.providers.cea.species import HO_PRODUCT_SPECIES

    if not check_availability().is_usable:
        print("CEA unavailable")
        return 1

    case = performance_reference_case()
    spec = case.case
    provider = CEAThermochemistryProvider()

    # ---- 1. the oracle, against the published source ---------------------
    oracle = run_rocket_oracle(
        provider._cea(), fuel_names=("H2(L)",), oxidiser_names=("O2(L)",),
        fuel_weights=(1.0,), oxidiser_weights=(1.0,),
        reactant_temperatures=(spec["fuel_temperature_K"],
                               spec["oxidiser_temperature_K"]),
        of_ratio=spec["oxidiser_fuel_ratio"],
        chamber_pressure=spec["chamber_pressure_Pa"],
        area_ratio=spec["area_ratio"],
        product_species=HO_PRODUCT_SPECIES,
        expansion_mode=ExpansionMode.EQUILIBRIUM)

    oracle_values = {
        "characteristic_velocity": oracle.c_star,
        "specific_impulse": oracle.specific_impulse / STANDARD_GRAVITY,
    }
    oracle_rows = compare_published(
        case, oracle_values, role="validation",
        source_of_computed="NASA CEA 3.3.4 rocket oracle, equilibrium")

    # ---- 2. RocketForge, against the same published numbers --------------
    chamber = provider.solve_chamber(ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_HYDROGEN, spec["fuel_temperature_K"],
                              phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, spec["oxidiser_temperature_K"],
                                  phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(spec["oxidiser_fuel_ratio"]),
        chamber_pressure=spec["chamber_pressure_Pa"])).unwrap()

    rocketforge_rows = {}
    rocketforge_values = {}
    for basis in (ChamberGammaBasis.FROZEN, ChamberGammaBasis.EQUILIBRIUM):
        reduced = reduce_chamber_gas(chamber, GammaStrategy.CHAMBER, basis).value
        vacuum = solve_ideal_performance(IdealPerformanceRequest(
            reduced=reduced, chamber_pressure=spec["chamber_pressure_Pa"],
            area_ratio=spec["area_ratio"], ambient_pressure=0.0,
            scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01),
        )).unwrap()
        # The published Isp is the optimum-expansion value, so RocketForge is
        # evaluated at the same reference condition: ambient set to the exit
        # pressure this nozzle produces. An identity, not a search.
        optimum = solve_ideal_performance(IdealPerformanceRequest(
            reduced=reduced, chamber_pressure=spec["chamber_pressure_Pa"],
            area_ratio=spec["area_ratio"],
            ambient_pressure=vacuum.exit.pressure,
            scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01),
        )).unwrap()
        values = {
            "characteristic_velocity": optimum.characteristic_velocity,
            "specific_impulse": optimum.specific_impulse,
        }
        rocketforge_values[basis.value] = {
            **values,
            "gamma": reduced.gamma,
            "isp_vacuum_seconds": vacuum.specific_impulse,
            "exit_mach": optimum.exit.mach,
            "exit_temperature": optimum.exit.temperature,
        }
        rocketforge_rows[basis.value] = compare_published(
            case, values, role="model comparison",
            source_of_computed=f"RocketForge ideal, {basis.value} basis")

    report = {
        "dataset": case.dataset,
        "title": case.title,
        "citation": case.citation,
        "conditions": case.conditions,
        "reference_condition_note": case.reference_condition_note,
        "validates": case.validates,
        "published": [{"key": q.key, "value": q.value, "unit": q.unit,
                       "si_value": q.si_value, "si_unit": q.si_unit,
                       "significant_figures": q.significant_figures,
                       "rounding_box": q.tolerance}
                      for q in case.published],
        "oracle": {
            "values": oracle_values,
            "verdict": overall_verdict(oracle_rows),
            "rows": [dataclasses.asdict(row) | {'verdict': row.verdict} for row in oracle_rows],
        },
        "rocketforge": {
            basis: {
                "values": rocketforge_values[basis],
                "verdict": overall_verdict(rows),
                "rows": [dataclasses.asdict(row) | {'verdict': row.verdict} for row in rows],
            }
            for basis, rows in rocketforge_rows.items()
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"{case.title}\n{case.citation}\n")
    print("1. published vs the NASA CEA oracle  [validation]")
    for row in oracle_rows:
        print(f"   {row.label:32s} published {row.published:12.4f} {row.unit:5s}"
              f"  oracle {row.computed:12.4f}"
              f"  rel {row.relative_difference:.3e}  box {row.tolerance:.3e}"
              f"  {row.verdict}")
    print(f"   verdict: {overall_verdict(oracle_rows)}\n")

    for basis, rows in rocketforge_rows.items():
        print(f"2. published vs RocketForge ({basis} basis)  [model comparison]"
              f"   gamma {rocketforge_values[basis]['gamma']:.6f}")
        for row in rows:
            print(f"   {row.label:32s} published {row.published:12.4f} {row.unit:5s}"
                  f"  RF {row.computed:12.4f}"
                  f"  rel {row.relative_difference:.3e}  box {row.tolerance:.3e}"
                  f"  {row.verdict}")
        print(f"   verdict: {overall_verdict(rows)}\n")
    return 0


if __name__ == "__main__":
    target = (Path(sys.argv[1]) if len(sys.argv) > 1
              else ROOT / "acceptance" / "phase_5e" / "nasa_performance_reference.json")
    sys.exit(main(target))
