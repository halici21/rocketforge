"""RocketForge's ideal model against NASA CEA's three chemistry modes.

The question is **which comparison is like-for-like**, not "how close is
RocketForge to CEA". Two things have to be matched before a difference means
anything, and both were established by measurement rather than assumed:

**1. What CEA's Cf and Isp are referenced to.** Measured here, on all three
modes: ``Cf_reported + (pe/pc) * epsilon == Ivac / c*`` to 6e-09. So CEA's
``thrust_coefficient`` and ``specific_impulse`` are the *optimum-expansion*
values -- momentum only, pe = pa -- and ``specific_impulse_vacuum`` is the one
that carries the vacuum pressure term. Comparing RocketForge's vacuum Cf
against CEA's reported Cf would be a 5.6 % "error" that is entirely a
difference of reference condition.

**2. Which exponent RocketForge holds constant.** A chamber carries two, 5.6 %
apart. The frozen ratio cp/cv is the exponent of a genuinely
constant-composition isentropic process, which is what this model computes, so
it is the like-for-like partner of CEA's frozen-at-chamber expansion. The
equilibrium exponent gamma_s is defined for a shifting-composition expansion,
and holding it constant reproduces the equilibrium result near the throat while
drifting from it downstream.

Writes a JSON record; prints the tables.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rocketforge.core.constants import STANDARD_GRAVITY  # noqa: E402
from rocketforge.engineering.chamber import (  # noqa: E402
    ChamberGammaBasis,
    reduce_chamber_gas,
)
from rocketforge.engineering.nozzle import (  # noqa: E402
    IdealPerformanceRequest,
    PerformanceScale,
    PerformanceScaleMode,
    check_identities,
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

CASE = {
    "propellants": "LOX / LCH4",
    "of_ratio": 3.4,
    "chamber_pressure": 10.0e6,
    "area_ratio": 40.0,
    "oxidiser_temperature": 90.17,
    "fuel_temperature": 111.643,
    "throat_area": 0.01,
}

#: **No CEA mode is exactly like-for-like with RocketForge v1**, and saying so
#: is the point of this record.
#:
#: RocketForge's model is *calorically* perfect: cp, cv and therefore gamma are
#: constants. Every CEA mode is *thermally* perfect but calorically imperfect --
#: it evaluates cp at the local temperature from the NASA polynomials. That
#: difference exists in all three comparisons and no choice of chemistry mode
#: removes it.
#:
#: What can be matched is the **chemistry** assumption, and that is what picks
#: the nearest partner:
#:
#: * ``frozen`` basis vs ``frozen_at_chamber``: both hold the chamber
#:   composition fixed for the whole expansion. Only the caloric assumption
#:   differs.
#: * ``equilibrium`` basis vs ``equilibrium``: different chemistry -- one holds
#:   composition fixed, the other lets it shift -- but gamma_s is *defined* as
#:   the isentropic exponent of the shifting expansion, so holding it constant
#:   approximates it by construction.
#:
#: The classification is therefore per quantity, not per mode -- but every
#: quantity is a **cross-model** difference, because no pair of modes matches
#: both the chemistry and the caloric assumption. c* is set at the throat, a
#: short expansion from the chamber where the caloric mismatch has barely
#: accumulated, so for the matched chemistry pair it is the *closest* such
#: difference. Everything downstream of the throat accumulates the caloric
#: difference and is further away.
#:
#: "Validation residual" is deliberately not used here. It belongs to genuine
#: same-model checks -- c* against the independent perfect-gas analytic form,
#: and the internal identities against frozen Compressible -- and using it for
#: a cross-model comparison would claim agreement between two models as
#: evidence that one of them is correct.
MATCHED_MODE = {
    "frozen": {
        "mode": "frozen_at_chamber",
        "chemistry_matched": True,
        "caloric_matched": False,
        "reason": (
            "Both hold the chamber composition fixed from chamber to exit and "
            "use the specific-heat ratio of that fixed composition, so the "
            "chemistry assumption is the same. The caloric assumption is not: "
            "RocketForge holds cp constant, CEA evaluates it at the local "
            "temperature. That difference is absent at the throat and grows "
            "through the expansion."),
        "classification_by_quantity": {
            "c_star": "closest cross-model difference",
            "cf_optimum": "model difference",
            "cf_vacuum": "model difference",
            "isp_optimum_seconds": "model difference",
            "isp_vacuum_seconds": "model difference",
            "exit_mach": "model difference",
            "exit_temperature": "model difference",
        },
    },
    "equilibrium": {
        "mode": "equilibrium",
        "chemistry_matched": False,
        "caloric_matched": False,
        "reason": (
            "Different chemistry: RocketForge holds the composition fixed, CEA "
            "lets it shift. gamma_s is defined as the isentropic exponent of "
            "that shifting expansion, so holding it constant approximates the "
            "equilibrium result by construction -- which is why the agreement "
            "is close. Close agreement between different models is not "
            "validation."),
        "classification_by_quantity": {
            "c_star": "model difference",
            "cf_optimum": "model difference",
            "cf_vacuum": "model difference",
            "isp_optimum_seconds": "model difference",
            "isp_vacuum_seconds": "model difference",
            "exit_mach": "model difference",
            "exit_temperature": "model difference",
        },
    },
}


def main(out: Path) -> int:
    from rocketforge.providers.cea import (
        LIQUID_METHANE,
        LOX,
        CEAThermochemistryProvider,
        check_availability,
    )
    from rocketforge.providers.cea.oracle import run_rocket_oracle
    from rocketforge.providers.cea.species import CHO_PRODUCT_SPECIES

    if not check_availability().is_usable:
        print("CEA unavailable")
        return 1

    provider = CEAThermochemistryProvider()
    chamber = provider.solve_chamber(ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_METHANE, CASE["fuel_temperature"],
                              phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, CASE["oxidiser_temperature"],
                                  phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(CASE["of_ratio"]),
        chamber_pressure=CASE["chamber_pressure"])).unwrap()

    report: dict = {
        "case": dict(CASE),
        "chamber": {
            "stagnation_temperature": chamber.temperature,
            "molar_mass": chamber.molar_mass,
            "gas_constant": chamber.gas_constant,
            "gamma_equilibrium": chamber.gamma_equilibrium,
            "gamma_frozen": chamber.gamma_frozen,
            "gamma_separation_relative": abs(
                chamber.gamma_frozen - chamber.gamma_equilibrium)
            / chamber.gamma_equilibrium,
        },
        "reference_condition_probe": {},
        "rocketforge": {},
        "cea": {},
        "comparison": {},
        "matched_mode": MATCHED_MODE,
    }

    # ---- CEA, all three modes -------------------------------------------
    oracles = {}
    for label, mode in (("equilibrium", ExpansionMode.EQUILIBRIUM),
                        ("frozen_at_throat", ExpansionMode.FROZEN_AT_THROAT),
                        ("frozen_at_chamber", ExpansionMode.FROZEN)):
        oracle = run_rocket_oracle(
            provider._cea(), fuel_names=("CH4(L)",), oxidiser_names=("O2(L)",),
            fuel_weights=(1.0,), oxidiser_weights=(1.0,),
            reactant_temperatures=(CASE["fuel_temperature"],
                                   CASE["oxidiser_temperature"]),
            of_ratio=CASE["of_ratio"],
            chamber_pressure=CASE["chamber_pressure"],
            area_ratio=CASE["area_ratio"],
            product_species=CHO_PRODUCT_SPECIES, expansion_mode=mode)
        oracles[label] = oracle
        _, _, exit_station = oracle.stations
        pressure_term = (exit_station.pressure / CASE["chamber_pressure"]) * CASE["area_ratio"]
        report["reference_condition_probe"][label] = {
            "cf_reported": oracle.thrust_coefficient,
            "vacuum_pressure_term": pressure_term,
            "cf_reported_plus_pressure_term":
                oracle.thrust_coefficient + pressure_term,
            "cf_from_vacuum_isp": oracle.specific_impulse_vacuum / oracle.c_star,
            "residual": abs(oracle.thrust_coefficient + pressure_term
                            - oracle.specific_impulse_vacuum / oracle.c_star),
        }
        report["cea"][label] = {
            "c_star": oracle.c_star,
            "cf_optimum": oracle.thrust_coefficient,
            "cf_vacuum": oracle.specific_impulse_vacuum / oracle.c_star,
            "c_eff_optimum": oracle.specific_impulse,
            "c_eff_vacuum": oracle.specific_impulse_vacuum,
            "isp_optimum_seconds": oracle.specific_impulse / STANDARD_GRAVITY,
            "isp_vacuum_seconds": oracle.specific_impulse_vacuum / STANDARD_GRAVITY,
            "exit_mach": exit_station.mach,
            "exit_pressure": exit_station.pressure,
            "exit_temperature": exit_station.temperature,
            "exit_molar_mass": exit_station.molar_mass,
            "exit_gamma_s": exit_station.gamma_s,
        }

    # ---- RocketForge, on both bases, at both reference conditions --------
    for basis in (ChamberGammaBasis.FROZEN, ChamberGammaBasis.EQUILIBRIUM):
        reduced = reduce_chamber_gas(chamber, GammaStrategy.CHAMBER, basis).value
        scale = PerformanceScale(PerformanceScaleMode.THROAT_AREA,
                                 CASE["throat_area"])

        vacuum = solve_ideal_performance(IdealPerformanceRequest(
            reduced=reduced, chamber_pressure=CASE["chamber_pressure"],
            area_ratio=CASE["area_ratio"], ambient_pressure=0.0,
            scale=scale)).unwrap()
        # The optimum-expansion reference: ambient set to the exit pressure the
        # nozzle actually produces. No search, no optimiser -- an identity.
        optimum = solve_ideal_performance(IdealPerformanceRequest(
            reduced=reduced, chamber_pressure=CASE["chamber_pressure"],
            area_ratio=CASE["area_ratio"],
            ambient_pressure=vacuum.exit.pressure, scale=scale)).unwrap()

        report["rocketforge"][basis.value] = {
            "gamma": reduced.gamma,
            "gamma_source": reduced.gamma_source,
            "gas_constant": reduced.gas_constant,
            "stagnation_temperature": reduced.stagnation_temperature,
            "c_star": vacuum.characteristic_velocity,
            "cf_optimum": optimum.thrust_coefficient,
            "cf_vacuum": vacuum.thrust_coefficient,
            "c_eff_optimum": optimum.effective_exhaust_velocity,
            "c_eff_vacuum": vacuum.effective_exhaust_velocity,
            "isp_optimum_seconds": optimum.specific_impulse,
            "isp_vacuum_seconds": vacuum.specific_impulse,
            "exit_mach": vacuum.exit.mach,
            "exit_pressure": vacuum.exit.pressure,
            "exit_temperature": vacuum.exit.temperature,
            "exit_velocity": vacuum.exit.velocity,
            "mass_flow": vacuum.mass_flow,
            "total_thrust_vacuum": vacuum.thrust.total,
            "identities_passed": check_identities(vacuum).passed,
            "identity_worst_residual": check_identities(vacuum).worst.residual,
        }

    # ---- like-for-like and everything else -------------------------------
    keys = ("c_star", "cf_optimum", "cf_vacuum", "isp_optimum_seconds",
            "isp_vacuum_seconds", "exit_mach", "exit_temperature")
    for basis, rf in report["rocketforge"].items():
        report["comparison"][basis] = {}
        for label, cea in report["cea"].items():
            entry = {key: (rf[key] - cea[key]) / cea[key] for key in keys}
            nearest = MATCHED_MODE[basis]["mode"] == label
            by_quantity = MATCHED_MODE[basis]["classification_by_quantity"]
            entry["classification"] = {
                key: (by_quantity[key] if nearest else "model difference")
                for key in keys}
            entry["nearest_partner"] = nearest
            entry["chemistry_matched"] = (
                nearest and MATCHED_MODE[basis]["chemistry_matched"])
            report["comparison"][basis][label] = entry

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # ---- print ------------------------------------------------------------
    print(f"case  {CASE['propellants']}   O/F {CASE['of_ratio']}   "
          f"Pc {CASE['chamber_pressure']/1e6:g} MPa   Ae/At {CASE['area_ratio']:g}\n")

    print("what CEA's Cf is referenced to")
    for label, probe in report["reference_condition_probe"].items():
        print(f"  {label:18s} Cf_reported {probe['cf_reported']:.6f}"
              f"  + (pe/pc)eps {probe['vacuum_pressure_term']:.6f}"
              f"  = {probe['cf_reported_plus_pressure_term']:.6f}"
              f"  vs Ivac/c* {probe['cf_from_vacuum_isp']:.6f}"
              f"   residual {probe['residual']:.2e}")
    print("  -> CEA's Cf and Isp are the OPTIMUM-expansion values.\n")

    print(f"chamber   gamma_s {report['chamber']['gamma_equilibrium']:.6f}"
          f"   gamma_fr {report['chamber']['gamma_frozen']:.6f}"
          f"   apart {report['chamber']['gamma_separation_relative']*100:.2f} %\n")

    header = (f"  {'':22s} {'c* [m/s]':>11s} {'Cf opt':>9s} {'Cf vac':>9s} "
              f"{'Isp opt':>9s} {'Isp vac':>9s} {'Me':>8s} {'Te [K]':>9s}")
    print("NASA CEA")
    print(header)
    for label, cea in report["cea"].items():
        print(f"  {label:22s} {cea['c_star']:11.3f} {cea['cf_optimum']:9.5f}"
              f" {cea['cf_vacuum']:9.5f} {cea['isp_optimum_seconds']:9.3f}"
              f" {cea['isp_vacuum_seconds']:9.3f} {cea['exit_mach']:8.4f}"
              f" {cea['exit_temperature']:9.2f}")

    print("\nRocketForge ideal, constant-property")
    print(header)
    for basis, rf in report["rocketforge"].items():
        print(f"  {basis:22s} {rf['c_star']:11.3f} {rf['cf_optimum']:9.5f}"
              f" {rf['cf_vacuum']:9.5f} {rf['isp_optimum_seconds']:9.3f}"
              f" {rf['isp_vacuum_seconds']:9.3f} {rf['exit_mach']:8.4f}"
              f" {rf['exit_temperature']:9.2f}")

    print("\nNo CEA mode is exactly like-for-like: RocketForge is calorically\n"
          "perfect and every CEA mode is calorically imperfect. What can be\n"
          "matched is the chemistry assumption, and that is what 'nearest\n"
          "partner' below means.")
    for basis in report["comparison"]:
        matched = MATCHED_MODE[basis]["mode"]
        print(f"\nrelative difference, RocketForge({basis}) - CEA")
        print(f"  {'mode':22s} {'c*':>11s} {'Cf opt':>11s} {'Cf vac':>11s}"
              f" {'Isp opt':>11s} {'Te':>11s}   classification")
        for label, diff in report["comparison"][basis].items():
            mark = " <= nearest partner" if label == matched else ""
            print(f"  {label:22s} {diff['c_star']:11.3e}"
                  f" {diff['cf_optimum']:11.3e} {diff['cf_vacuum']:11.3e}"
                  f" {diff['isp_optimum_seconds']:11.3e}"
                  f" {diff['exit_temperature']:11.3e}"
                  f"   c*: {diff['classification']['c_star']}{mark}")
        print(f"    {MATCHED_MODE[basis]['reason']}")
    return 0


if __name__ == "__main__":
    target = (Path(sys.argv[1]) if len(sys.argv) > 1
              else ROOT / "acceptance" / "phase_5e" / "cea_oracle_comparison.json")
    sys.exit(main(target))
