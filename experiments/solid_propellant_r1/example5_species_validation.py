"""Section 29 / section 3: Example 5 validated through the comparison layer.

Archives, in ``acceptance/solid_propellant_r1/`` (gitignored; this script
regenerates everything there):

* ``rp1311_example5_official_output.txt`` -- NASA's shipped ``example5.py``,
  run unmodified, stdout verbatim.
* ``rp1311_example5_input.json`` -- the exact input.
* ``example5_validation.json`` -- every comparison row, from
  :mod:`rocketforge.comparison`: against NASA's printout (at its printed
  precision) and against direct CEA (bit for bit).

The comparisons themselves are no longer computed here. They come from the
same code the test suite exercises, so this archive and the tests cannot
disagree about what was compared or how.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "acceptance" / "solid_propellant_r1"

import cea  # noqa: E402

from rocketforge.application.analysis import thermochemistry_provider as gateway  # noqa: E402
from rocketforge.comparison import (  # noqa: E402
    ReferenceCase,
    ReferenceQuantity,
    SourceKind,
    compare,
    observed_from_chamber,
)
from rocketforge.comparison.rp1311 import RP1311_EXAMPLE5_PUBLISHED  # noqa: E402
from rocketforge.physics.solid_propellant import SolidFormulationEquilibriumRequest  # noqa: E402
from rocketforge.providers.cea.units import pressure_from_bar  # noqa: E402
from rocketforge.providers.cea_solid import (  # noqa: E402
    RP1311_EXAMPLE5,
    RP1311_EXAMPLE5_OMIT,
    RP1311_EXAMPLE5_PRESSURES_BAR,
    solve_solid_chamber,
    solve_solid_equilibrium_cstar,
)


def official_output() -> str:
    script = pathlib.Path(cea.__file__).parent / "samples" / "rp1311" / "example5.py"
    return subprocess.run([sys.executable, str(script)], capture_output=True,
                          text=True, check=True).stdout


def direct_case() -> ReferenceCase:
    """Example 5 from CEA alone, recorded by example5_direct.py."""
    direct = json.loads((ROOT / "experiments" / "solid_propellant_r1"
                         / "example5_direct.json").read_text(encoding="utf-8"))
    quantities = [
        ReferenceQuantity("chamber_temperature", direct["temperature_k"], "K"),
        ReferenceQuantity("molar_mass", direct["molar_mass_MW"], "kg/kmol"),
        ReferenceQuantity("gamma_s", direct["gamma_s"], "1"),
    ]
    quantities += [ReferenceQuantity(f"mole_fraction:{name}", value, "1")
                   for name, value in sorted(direct["mole_fractions"].items())]
    return ReferenceCase(
        case_id="rp1311-example5-direct", title="Example 5, direct CEA",
        source_kind=SourceKind.CEA_DIRECT, benchmark_class="A",
        source="experiments/solid_propellant_r1/example5_direct.json",
        code="NASA CEA", code_version=getattr(cea, "__version__", "not stated"),
        inputs={"pressure_bar": direct["pressure_bar"]}, tolerance_rel=0.0,
        quantities=tuple(quantities))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rp1311_example5_official_output.txt").write_text(
        official_output(), encoding="utf-8", newline="\n")

    request = SolidFormulationEquilibriumRequest(
        formulation=RP1311_EXAMPLE5,
        chamber_pressure=pressure_from_bar(RP1311_EXAMPLE5_PRESSURES_BAR[0]),
        omit_species=RP1311_EXAMPLE5_OMIT)
    chamber = solve_solid_chamber(cea, request, provenance=gateway.provider_provenance())
    cstar = solve_solid_equilibrium_cstar(cea, request, chamber)
    observed = observed_from_chamber(chamber, characteristic_velocity=cstar.value)

    (OUT / "rp1311_example5_input.json").write_text(json.dumps({
        "source": "cea/samples/rp1311/example5.py (NASA, shipped with cea "
                  f"{getattr(cea, '__version__', '')})",
        "reactants": [
            {"name": i.name, "mass_fraction": i.mass_fraction,
             "temperature_K": RP1311_EXAMPLE5.initial_temperature,
             "custom": (None if i.custom is None else {
                 "formula": dict(i.custom.formula),
                 "heat_of_formation": i.custom.heat_of_formation,
                 "heat_of_formation_units": i.custom.heat_of_formation_units,
                 "reference_temperature": i.custom.reference_temperature,
                 "molecular_weight": i.custom.molecular_weight,
                 "molecular_weight_origin": i.custom.molecular_weight_origin,
                 "source": i.custom.source})}
            for i in RP1311_EXAMPLE5.ingredients],
        "pressure_bar": RP1311_EXAMPLE5_PRESSURES_BAR[0],
        "problem": "HP equilibrium, EqSolver, products_from_reactants=True",
        "omit_species": list(RP1311_EXAMPLE5_OMIT),
        "database": chamber.provenance.database,
        "database_sha256": chamber.provenance.database_sha256,
    }, indent=2) + "\n", encoding="utf-8", newline="\n")

    results = {case.case_id: compare(case, observed)
               for case in (RP1311_EXAMPLE5_PUBLISHED, direct_case())}
    (OUT / "example5_validation.json").write_text(json.dumps({
        case_id: {"source_kind": r.case.source_kind.value,
                  "benchmark_class": r.case.benchmark_class,
                  "verdict": r.verdict, "not_observed": list(r.not_observed),
                  "rows": r.as_records()}
        for case_id, r in results.items()
    }, indent=2) + "\n", encoding="utf-8", newline="\n")

    for case_id, r in results.items():
        tight = max((abs(x.abs_diff) / x.bound for x in r.rows if x.bound),
                    default=0.0)
        print(f"{case_id:32s} {r.verdict:9s} {len(r.rows):4d} quantities; "
              f"largest |diff|/bound {tight:.3f}")
    print(f"equilibrium c*: {cstar.value!r} m/s ({cstar.basis})")
    return 0 if all(r.verdict == "agrees" for r in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
