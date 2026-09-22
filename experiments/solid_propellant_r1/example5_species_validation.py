"""Section 29 / section 3: species-level three-way validation, and the archive.

Archives, in ``acceptance/solid_propellant_r1/``:

* ``rp1311_example5_official_output.txt`` -- NASA's shipped ``example5.py``,
  run unmodified, stdout verbatim. This is the official reference artifact in
  this workspace: the RP-1311 printed table itself was not available offline,
  and the shipped example is NASA's own reproduction of it.
* ``rp1311_example5_input.json`` -- the exact direct-CEA input used.
* ``example5_validation.json`` -- every comparison, with exact absolute and
  relative differences.
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
from rocketforge.physics.solid_propellant import SolidFormulationEquilibriumRequest  # noqa: E402
from rocketforge.providers.cea.units import pressure_from_bar  # noqa: E402
from rocketforge.providers.cea_solid import (  # noqa: E402
    RP1311_EXAMPLE5,
    RP1311_EXAMPLE5_OMIT,
    RP1311_EXAMPLE5_PRESSURES_BAR,
    solve_solid_chamber,
)

MAJOR_SPECIES = ("H2", "CO", "H2O", "HCL", "N2", "CO2", "AL2O3(L)")


def official_output() -> str:
    script = pathlib.Path(cea.__file__).parent / "samples" / "rp1311" / "example5.py"
    return subprocess.run([sys.executable, str(script)], capture_output=True,
                          text=True, check=True).stdout


def parse_first_column(text: str) -> dict[str, float]:
    """The first-pressure column of the official printout, as printed."""
    values: dict[str, float] = {}
    in_fractions = False
    for line in text.splitlines():
        if line.startswith("MOLE FRACTIONS"):
            in_fractions = True
            continue
        if line.startswith("TRACE SPECIES"):
            break
        parts = line.split()
        if len(parts) < 2:
            continue
        if in_fractions:
            values[f"X:{parts[0]}"] = float(parts[1])
        else:
            label = line[:16].strip()
            try:
                values[label] = float(line[16:].split()[0])
            except (ValueError, IndexError):
                pass
    return values


def diff(reference: float, value: float) -> dict:
    absolute = value - reference
    return {"reference": reference, "value": value, "abs_diff": absolute,
            "rel_diff": absolute / reference if reference else None}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    text = official_output()
    (OUT / "rp1311_example5_official_output.txt").write_text(
        text, encoding="utf-8", newline="\n")
    official = parse_first_column(text)

    # Direct CEA, recorded by example5_direct.py with no RocketForge code in
    # the solve.
    direct = json.loads((ROOT / "experiments" / "solid_propellant_r1"
                         / "example5_direct.json").read_text(encoding="utf-8"))

    request = SolidFormulationEquilibriumRequest(
        formulation=RP1311_EXAMPLE5,
        chamber_pressure=pressure_from_bar(RP1311_EXAMPLE5_PRESSURES_BAR[0]),
        omit_species=RP1311_EXAMPLE5_OMIT)
    gas = solve_solid_chamber(cea, request, provenance=gateway.provider_provenance())
    # The composition is held on a mole basis, as CEA returned it.
    rf_mole = {n: gas.composition.fraction_of(n) for n in MAJOR_SPECIES}

    (OUT / "rp1311_example5_input.json").write_text(json.dumps({
        "source": "cea/samples/rp1311/example5.py (NASA, shipped with cea "
                  f"{getattr(cea, '__version__', '')})",
        "reactants": [
            {"name": i.name, "mass_fraction": i.mass_fraction,
             "temperature_K": RP1311_EXAMPLE5.initial_temperature,
             "custom": (None if i.custom is None else {
                 "formula": dict(i.custom.formula),
                 "molecular_weight": i.custom.molecular_weight,
                 "enthalpy": i.custom.enthalpy,
                 "enthalpy_units": i.custom.enthalpy_units,
                 "temperature": i.custom.temperature,
                 "source": i.custom.source})}
            for i in RP1311_EXAMPLE5.ingredients],
        "pressure_bar": RP1311_EXAMPLE5_PRESSURES_BAR[0],
        "problem": "HP equilibrium, EqSolver, products_from_reactants=True",
        "omit_species": list(RP1311_EXAMPLE5_OMIT),
        "database": gas.provenance.database,
        "database_sha256": gas.provenance.database_sha256,
    }, indent=2) + "\n", encoding="utf-8", newline="\n")

    scalars = {
        "T_K": ("T, K", direct["temperature_k"], gas.temperature),
        "MW": ("MW", direct["molar_mass_MW"], gas.molar_mass * 1000.0),
        "M_1_over_n": ("M, (1/n)", direct["molar_mass_M"], None),
        "gamma_s": ("Gamma_s", direct["gamma_s"], gas.gamma),
    }
    rows = {}
    for key, (label, dv, rv) in scalars.items():
        rows[key] = {"official_vs_direct": diff(official[label], dv)}
        if rv is not None:
            rows[key]["direct_vs_rocketforge"] = diff(dv, rv)
    species = {}
    for name in MAJOR_SPECIES:
        dv = direct["mole_fractions"][name]
        species[name] = {"official_vs_direct": diff(official[f"X:{name}"], dv),
                         "direct_vs_rocketforge": diff(dv, rf_mole[name])}

    result = {
        "note": "official = NASA's shipped example5.py, first pressure column, "
                "at the precision it prints (%10.3f / %10.4f for scalars, "
                "%10.5g for mole fractions)",
        "scalars": rows, "mole_fractions": species,
        "condensed": {
            "candidates_reported_by_cea": direct["num_condensed_candidates"],
            "present": sorted(n for n, v in direct["mass_fractions"].items()
                              if v > 0 and n in direct["phase_report"]["condensed"]),
            "AL2O3(L)_mass_fraction_direct": direct["mass_fractions"]["AL2O3(L)"],
            "condensed_mass_fraction_rocketforge": gas.condensed_mass_fraction,
        },
    }
    (OUT / "example5_validation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"{'quantity':12s} {'official':>12s} {'direct CEA':>24s} "
          f"{'off->direct rel':>16s} {'direct->RF abs':>15s}")
    for key, row in rows.items():
        o = row["official_vs_direct"]
        r = row.get("direct_vs_rocketforge", {}).get("abs_diff", "n/a")
        print(f"{key:12s} {o['reference']:12.6g} {o['value']:24.17g} "
              f"{o['rel_diff']:+16.2e} {r!s:>15s}")
    for name, row in species.items():
        o, r = row["official_vs_direct"], row["direct_vs_rocketforge"]
        print(f"X {name:10s} {o['reference']:12.6g} {o['value']:24.17g} "
              f"{o['rel_diff']:+16.2e} {r['abs_diff']!s:>15s}")
    c = result["condensed"]
    print(f"\ncondensed: {c['candidates_reported_by_cea']} candidates, present "
          f"{c['present']}, RocketForge condensed mass "
          f"{c['condensed_mass_fraction_rocketforge']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
