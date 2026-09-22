"""Solve RP-1311 Example 5 through RocketForge, and compare three ways.

The three terms, and why each is needed:

* **official** -- the values NASA published, at the width they published them.
  The only completely independent check, and the only one that would catch this
  whole toolchain agreeing on a wrong answer.
* **direct** -- what the installed CEA actually returns, full precision, solved
  without RocketForge. Recorded by ``example5_direct.py``.
* **rocketforge** -- what the provider path returns.

Comparing only the first and last would confound two different questions: has
RocketForge mis-plumbed CEA, or does this build of CEA differ from the paper?
The middle term separates them.
"""

from __future__ import annotations

import json
import pathlib
import sys

import cea

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from rocketforge.physics.thermochemistry import ThermochemistryProvenance  # noqa: E402
from rocketforge.physics.solid_propellant import (  # noqa: E402
    SolidFormulationEquilibriumRequest,
)
from rocketforge.providers.cea_solid import solve_solid_chamber  # noqa: E402
from rocketforge.providers.cea_solid import (  # noqa: E402
    RP1311_EXAMPLE5,
    RP1311_EXAMPLE5_OMIT,
    RP1311_EXAMPLE5_PRESSURES_BAR,
)
from rocketforge.providers.cea.units import pressure_from_bar  # noqa: E402

#: The published table, Example 5, first pressure column.
OFFICIAL = {
    "P_atm": 34.023,
    "T_K": 2723.021,
    "MW": 22.290,
    "M_1_over_n": 23.140,
    "gamma_s": 1.1928,
    "density_g_per_cc": 3.523e-03,
    "AL2O3(L)_mole_fraction": 0.036724,
    "of_ratio": 0.000,
}


def build_request() -> SolidFormulationEquilibriumRequest:
    return SolidFormulationEquilibriumRequest(
        formulation=RP1311_EXAMPLE5,
        chamber_pressure=pressure_from_bar(RP1311_EXAMPLE5_PRESSURES_BAR[0]),
        product_species=None,          # derive from reactants, as the source does
        omit_species=RP1311_EXAMPLE5_OMIT,
    )


def base_provenance() -> ThermochemistryProvenance:
    from rocketforge.physics.thermochemistry import (
        ChemistryMode,
        EquilibriumConstraint,
    )
    return ThermochemistryProvenance(
        provider_id="nasa-cea",
        provider_version="solid-r1",
        library_version=getattr(cea, "__version__", ""),
        database="thermo.lib",
        chemistry_mode=ChemistryMode.EQUILIBRIUM,
        equilibrium_constraint=EquilibriumConstraint.HP,
    )


def compare(label: str, official: float, other: float) -> dict:
    absolute = other - official
    relative = absolute / official if official else float("nan")
    return {
        "quantity": label,
        "official": official,
        "value": other,
        "abs_diff": absolute,
        "rel_diff": relative,
    }


def main() -> None:
    here = pathlib.Path(__file__).parent
    direct = json.loads((here / "example5_direct.json").read_text(encoding="utf-8"))

    gas = solve_solid_chamber(cea, build_request(), provenance=base_provenance())

    # RocketForge reports SI; the published table reports CEA's own units.
    rf = {
        "T_K": gas.temperature,
        "MW": gas.molar_mass * 1000.0,          # kg/mol -> kg/kmol
        "gamma_s": gas.gamma,
        "density_g_per_cc": gas.density * 1.0e-3,
    }
    dc = {
        "T_K": direct["temperature_k"],
        "MW": direct["molar_mass_MW"],
        "gamma_s": direct["gamma_s"],
        "density_g_per_cc": direct["density"] * 1.0e-3,
    }

    print("THREE-WAY COMPARISON -- RP-1311 Example 5, 34.473652 bar\n")
    header = f"{'quantity':22s} {'official':>16s} {'direct CEA':>22s} {'RocketForge':>22s}"
    print(header)
    print("-" * len(header))
    rows = []
    for key in ("T_K", "MW", "gamma_s", "density_g_per_cc"):
        o = OFFICIAL[key]
        print(f"{key:22s} {o:16.6g} {dc[key]:22.16g} {rf[key]:22.16g}")
        rows.append({
            "official_vs_direct": compare(key, o, dc[key]),
            "direct_vs_rocketforge": compare(key, dc[key], rf[key]),
        })

    print()
    exact = all(dc[k] == rf[k] for k in dc)
    print(f"direct CEA == RocketForge, bit for bit : {exact}")
    for key in dc:
        if dc[key] != rf[key]:
            print(f"   MISMATCH {key}: {dc[key]!r} vs {rf[key]!r}")

    # Condensed reporting.
    al2o3_mole = gas.composition.fraction_of("AL2O3(L)")
    print()
    print(f"AL2O3(L) mole fraction  : {al2o3_mole!r}"
          f"   (official {OFFICIAL['AL2O3(L)_mole_fraction']})")
    print(f"AL2O3(L) mass fraction  : {direct['mass_fractions']['AL2O3(L)']!r}")
    print(f"condensed mass fraction : {gas.condensed_mass_fraction!r}")
    print(f"condensed candidates    : {direct['num_condensed_candidates']}"
          f"   actually present: "
          f"{sum(1 for n in direct['phase_report']['condensed'] if direct['mass_fractions'][n] > 0)}")
    print()
    print(f"request stored on result: {gas.request!r}")
    print(f"provenance formulation  : "
          f"{gas.provenance.options.get('solid_formulation')!r}")
    print(f"provenance reference    : "
          f"{gas.provenance.options.get('solid_formulation_reference')!r}")
    print(f"provenance ingredients  : "
          f"{ {k: v for k, v in gas.provenance.reactant_conditions.items()} }")

    out = here / "example5_threeway.json"
    out.write_text(json.dumps({
        "official": OFFICIAL,
        "direct": dc,
        "rocketforge": rf,
        "bitwise_identical": exact,
        "rows": rows,
        "al2o3_mole_fraction": al2o3_mole,
        "al2o3_mass_fraction": direct["mass_fractions"]["AL2O3(L)"],
        "condensed_mass_fraction": gas.condensed_mass_fraction,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"\nwritten -> {out}")


if __name__ == "__main__":
    main()
