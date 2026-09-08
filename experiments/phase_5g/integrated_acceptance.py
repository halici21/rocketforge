"""The integrated acceptance harness: the whole chain, end to end, headless.

Seven canonical cases that walk

    ChamberCase -> provider -> ChamberGas -> gamma reduction
                -> frozen Compressible -> IdealRocketPerformance
                -> trade study -> constraints -> Pareto -> score

using the same services the interface uses. There is no parallel scientific
path here: every number comes from `thermochemistry_service`,
`performance_service` and `trade_study_service`, which is what makes this
evidence about the product rather than about the harness.

Deterministic, and no synthetic desktop input.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "acceptance" / "phase_5g"

from rocketforge.application.analysis import performance_service as perf  # noqa: E402
from rocketforge.application.analysis import thermochemistry_provider as gateway  # noqa: E402
from rocketforge.application.analysis import thermochemistry_service as thermo  # noqa: E402
from rocketforge.application.analysis import trade_study_service as ts  # noqa: E402
from rocketforge.application.analysis.trade_study_domain import (  # noqa: E402
    STAGE_PERFORMANCE,
    STAGE_THERMOCHEMISTRY,
    build_variable,
)
from rocketforge.core.constants import STANDARD_GRAVITY  # noqa: E402
from rocketforge.engine.studies import (  # noqa: E402
    ComparisonOperator,
    ConstraintDefinition,
    ExplicitNumericVariable,
    Feasibility,
    ObjectiveDefinition,
    ObjectiveDirection,
    WeightedScoreDefinition,
)
from rocketforge.engineering.nozzle import (  # noqa: E402
    PerformanceScale,
    PerformanceScaleMode,
    check_identities,
)

MAX_ISP = ObjectiveDefinition("specific_impulse", ObjectiveDirection.MAXIMIZE)
MIN_TC = ObjectiveDefinition("chamber_temperature", ObjectiveDirection.MINIMIZE)

#: The integrated reference condition. LOX/LCH4 at the Phase 5C validated
#: operating point, on the frozen gamma basis, expanded to Ae/At 40 in vacuum.
CANONICAL_CASE = thermo.DEFAULT_CASE
CANONICAL_PERFORMANCE = perf.DEFAULT_PERFORMANCE_CASE


def write(name: str, payload: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  -> {name}")


def chamber_record(outcome) -> dict:
    state = outcome.state
    provenance = outcome.provenance
    return {
        "status": outcome.kind,
        "temperature_K": state.temperature,
        "molar_mass_kg_per_mol": state.molar_mass,
        "gas_constant_J_per_kgK": state.gas_constant,
        "gamma_equilibrium": state.gamma_equilibrium,
        "gamma_frozen": state.gamma_frozen,
        "cp_frozen": state.cp_frozen,
        "cp_equilibrium": state.cp_equilibrium,
        "condensed_mass_fraction": state.condensed_mass_fraction,
        "pressure_Pa": state.pressure,
        "species_count": len(state.composition.entries),
        "top_species": [{"name": n, "fraction": x} for n, x in
                        sorted(state.composition.entries,
                               key=lambda e: -e[1])[:6]],
        "diagnostics": [{"code": d.code, "severity": str(d.severity),
                         "message": d.message} for d in outcome.diagnostics],
        "provenance": {
            "provider_id": provenance.provider_id if provenance else None,
            "library_version": provenance.library_version if provenance else None,
            "database": provenance.database if provenance else None,
            "database_sha256": provenance.database_sha256 if provenance else None,
            "chemistry_mode": str(provenance.chemistry_mode) if provenance else None,
            "constraint": str(provenance.equilibrium_constraint)
                          if provenance else None,
        },
    }


def performance_record(outcome) -> dict:
    result = outcome.result
    thrust = result.thrust
    return {
        "status": outcome.kind,
        "gamma_strategy": result.reduced.strategy.value,
        "gamma_basis": result.reduced.basis.value,
        "gamma_used": result.reduced.gamma,
        "characteristic_velocity_m_per_s": result.characteristic_velocity,
        "thrust_coefficient_momentum": result.thrust_coefficient_momentum,
        "thrust_coefficient_pressure": result.thrust_coefficient_pressure,
        "thrust_coefficient": result.thrust_coefficient,
        "exit_mach": result.exit.mach,
        "exit_pressure_Pa": result.exit.pressure,
        "exit_temperature_K": result.exit.temperature,
        "exit_velocity_m_per_s": result.exit.velocity,
        "regime": result.exit.regime,
        "effective_exhaust_velocity_m_per_s": result.effective_exhaust_velocity,
        "specific_impulse_s": result.specific_impulse,
        "ambient_pressure_Pa": result.ambient_pressure,
        "scale": result.scale.label,
        "mass_flow_kg_per_s": result.mass_flow,
        "throat_area_m2": result.throat_area,
        "exit_area_m2": result.exit_area,
        "momentum_thrust_N": thrust.momentum if thrust else None,
        "pressure_thrust_N": thrust.pressure if thrust else None,
        "total_thrust_N": thrust.total if thrust else None,
        "diagnostics": [{"code": d.code, "severity": str(d.severity)}
                        for d in outcome.diagnostics],
    }


def identity_record(result) -> dict:
    report = check_identities(result)
    return {
        "checks": len(report.checks),
        "passed": report.passed,
        "worst_residual": report.worst.residual if report.worst else None,
        "worst_name": report.worst.name if report.worst else None,
        "rows": [{"name": c.name, "residual": c.residual,
                  "tolerance": c.tolerance, "passed": c.passed}
                 for c in report.checks],
    }


# ===========================================================================
# CASE 1 — the canonical integrated state
# ===========================================================================


def case_1_canonical() -> dict:
    chamber = thermo.solve_case(CANONICAL_CASE)
    outcome = perf.solve_performance(chamber, CANONICAL_PERFORMANCE)
    result = outcome.result

    # The identity chain, recomputed here from the published fields rather
    # than trusted from the validator, so this artifact is independent evidence.
    isp_from_ceff = result.effective_exhaust_velocity / STANDARD_GRAVITY
    isp_from_cf_cstar = (result.thrust_coefficient
                         * result.characteristic_velocity / STANDARD_GRAVITY)
    ceff_from_cf_cstar = (result.thrust_coefficient
                          * result.characteristic_velocity)

    return {
        "case": "LOX/LCH4, O/F 3.4, p_c 10 MPa, Ae/At 40, vacuum, frozen basis",
        "chamber_case": {
            "fuel": CANONICAL_CASE.fuel,
            "oxidiser": CANONICAL_CASE.oxidiser,
            "oxidiser_fuel_ratio": CANONICAL_CASE.oxidiser_fuel_ratio,
            "chamber_pressure_Pa": CANONICAL_CASE.chamber_pressure,
            "fuel_temperature_K": CANONICAL_CASE.fuel_temperature,
            "oxidiser_temperature_K": CANONICAL_CASE.oxidiser_temperature,
        },
        "thermochemistry": chamber_record(chamber),
        "performance": performance_record(outcome),
        "identities": identity_record(result),
        "identity_chain_recomputed": {
            "Isp_from_c_eff": isp_from_ceff,
            "Isp_from_Cf_cstar": isp_from_cf_cstar,
            "Isp_published": result.specific_impulse,
            "c_eff_from_Cf_cstar": ceff_from_cf_cstar,
            "c_eff_published": result.effective_exhaust_velocity,
            "agree": (abs(isp_from_ceff - result.specific_impulse) < 1e-9
                      and abs(isp_from_cf_cstar - result.specific_impulse) < 1e-9
                      and abs(ceff_from_cf_cstar
                              - result.effective_exhaust_velocity) < 1e-9),
        },
    }


# ===========================================================================
# CASE 2 — the same state, scaled
# ===========================================================================


def case_2_scaled() -> dict:
    chamber = thermo.solve_case(CANONICAL_CASE)
    normalized = perf.solve_performance(chamber, CANONICAL_PERFORMANCE)
    sized = perf.solve_performance(
        chamber, CANONICAL_PERFORMANCE.replace(
            scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01)))
    doubled = perf.solve_performance(
        chamber, CANONICAL_PERFORMANCE.replace(
            scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.02)))
    by_flow = perf.solve_performance(
        chamber, CANONICAL_PERFORMANCE.replace(
            scale=PerformanceScale(PerformanceScaleMode.MASS_FLOW,
                                   sized.result.mass_flow)))

    invariant = {
        name: {
            "normalized": getattr(normalized.result, name),
            "sized": getattr(sized.result, name),
            "doubled": getattr(doubled.result, name),
            "identical": (getattr(normalized.result, name)
                          == getattr(sized.result, name)
                          == getattr(doubled.result, name)),
        }
        for name in ("characteristic_velocity", "thrust_coefficient",
                     "effective_exhaust_velocity", "specific_impulse")
    }

    return {
        "case": "scale invariance and the mass-flow round trip",
        "normalized": performance_record(normalized),
        "throat_area_0p01": performance_record(sized),
        "throat_area_0p02": performance_record(doubled),
        "scale_free_invariants": invariant,
        "absolutes_scale_linearly": {
            "mass_flow_ratio": doubled.result.mass_flow / sized.result.mass_flow,
            "thrust_ratio": doubled.result.thrust.total / sized.result.thrust.total,
            "exit_area_ratio": doubled.result.exit_area / sized.result.exit_area,
        },
        "mass_flow_round_trip": {
            "requested_mass_flow": sized.result.mass_flow,
            "recovered_throat_area": by_flow.result.throat_area,
            "expected_throat_area": 0.01,
            "relative_error": abs(by_flow.result.throat_area - 0.01) / 0.01,
        },
        "identities_sized": identity_record(sized.result),
    }


# ===========================================================================
# CASE 3 — the ambient matrix and the pressure-thrust sign matrix
# ===========================================================================


def case_3_ambient() -> dict:
    chamber = thermo.solve_case(CANONICAL_CASE)
    sized = CANONICAL_PERFORMANCE.replace(
        scale=PerformanceScale(PerformanceScaleMode.THROAT_AREA, 0.01))

    vacuum = perf.solve_performance(chamber, sized)
    exit_pressure = vacuum.result.exit.pressure

    rows = []
    for label, ambient in (
        ("vacuum", 0.0),
        ("below exit pressure", exit_pressure * 0.5),
        ("exactly the exit pressure", exit_pressure),
        ("above exit pressure", exit_pressure * 2.0),
        ("sea level", 101325.0),
    ):
        outcome = perf.solve_performance(
            chamber, sized.replace(ambient=perf.AmbientCondition(
                perf.AmbientMode.CUSTOM, ambient)))
        result = outcome.result
        rows.append({
            "label": label,
            "ambient_Pa": ambient,
            "exit_pressure_Pa": result.exit.pressure,
            "characteristic_velocity": result.characteristic_velocity,
            "exit_mach": result.exit.mach,
            "exit_velocity": result.exit.velocity,
            "Cf_momentum": result.thrust_coefficient_momentum,
            "Cf_pressure": result.thrust_coefficient_pressure,
            "Cf": result.thrust_coefficient,
            "pressure_thrust_N": result.thrust.pressure,
            "total_thrust_N": result.thrust.total,
            "c_eff": result.effective_exhaust_velocity,
            "Isp_s": result.specific_impulse,
            "regime": result.exit.regime,
            "pressure_thrust_sign": ("positive" if result.thrust.pressure > 0
                                     else "zero" if result.thrust.pressure == 0
                                     else "negative"),
        })

    cstar = {row["characteristic_velocity"] for row in rows}
    mach = {row["exit_mach"] for row in rows}
    monotone = all(a["Isp_s"] > b["Isp_s"]
                   for a, b in zip(rows, rows[1:]))

    return {
        "case": "one chamber, one nozzle, five ambient pressures",
        "rows": rows,
        "c_star_invariant": len(cstar) == 1,
        "exit_state_invariant": len(mach) == 1,
        "isp_decreases_monotonically_with_ambient": monotone,
        "pressure_thrust_signs": [row["pressure_thrust_sign"] for row in rows],
        "clamping_detected": any(row["pressure_thrust_N"] == 0.0
                                 and row["ambient_Pa"] != row["exit_pressure_Pa"]
                                 for row in rows),
    }


# ===========================================================================
# CASE 4 — the assigned-enthalpy chain
# ===========================================================================


def case_4_assigned_enthalpy() -> dict:
    requested = 95.0
    case = CANONICAL_CASE.replace(oxidiser_temperature=requested)
    chamber = thermo.solve_case(case)
    outcome = perf.solve_performance(chamber, CANONICAL_PERFORMANCE)

    setup = ts.TradeStudySetup(chamber=case, performance=CANONICAL_PERFORMANCE)
    of = build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=5)
    definition = ts.build_definition(setup, [of], objectives=(MAX_ISP,))
    study = ts.run_trade_study(definition, setup)

    code = "PROVIDER_ASSIGNED_ENTHALPY_REACTANT"
    chamber_hit = [d for d in chamber.diagnostics if d.code == code]
    performance_inherited = [row for row in perf.inherited_diagnostics(outcome)
                             if row["code"] == code]
    study_hit = [d for d in study.diagnostics if d.code == code]

    return {
        "case": "LOX requested at 95 K; CEA models it with an assigned enthalpy",
        "requested_oxidiser_temperature_K": requested,
        "catalogue_reference_temperature_K":
            CANONICAL_CASE.oxidiser_temperature,
        "diagnostic_code": code,
        "thermochemistry": {
            "present": bool(chamber_hit),
            "severity": str(chamber_hit[0].severity) if chamber_hit else None,
            "message": chamber_hit[0].message if chamber_hit else None,
            "detail": {k: float(v) for k, v in
                       (chamber_hit[0].detail or {}).items()} if chamber_hit
                      else None,
            "status": chamber.kind,
        },
        "performance": {
            "inherited": bool(performance_inherited),
            "origin": performance_inherited[0]["origin"]
                      if performance_inherited else None,
            "status": outcome.kind,
            "still_produced_a_result": outcome.result is not None,
        },
        "trade_study": {
            "aggregated": bool(study_hit),
            "count": study_hit[0].count if study_hit else 0,
            "total": study_hit[0].total if study_hit else 0,
            "origin": study_hit[0].origin if study_hit else None,
            "points_still_feasible": study.feasible_count,
            "points_failed": study.failed_count,
        },
        "verdict": "PASS" if (chamber_hit and performance_inherited and study_hit
                              and str(chamber_hit[0].severity) == "warning"
                              and outcome.result is not None
                              and study.failed_count == 0) else "FAIL",
        "limitation": "not solved in this phase; deferred to reactant enthalpy "
                      "/ fluid-property coupling",
    }


# ===========================================================================
# CASE 5 — the condensed chain
# ===========================================================================


def case_5_condensed() -> dict:
    rows = []
    for label, of_ratio in (("trace, below the reporting threshold", 3.4),
                            ("fuel-rich, condensed carbon present", 0.5)):
        case = CANONICAL_CASE.replace(oxidiser_fuel_ratio=of_ratio)
        chamber = thermo.solve_case(case)
        summary = thermo.condensed_summary(chamber)
        outcome = perf.solve_performance(chamber, CANONICAL_PERFORMANCE)

        setup = ts.TradeStudySetup(chamber=case,
                                   performance=CANONICAL_PERFORMANCE)
        tc_only = ts.build_definition(
            setup, [], outputs=("chamber_temperature",))
        isp_needed = ts.build_definition(setup, [], objectives=(MAX_ISP,))
        tc_study = ts.run_trade_study(tc_only, setup)
        isp_study = ts.run_trade_study(isp_needed, setup)

        rows.append({
            "label": label,
            "oxidiser_fuel_ratio": of_ratio,
            "condensed_mass_fraction": chamber.state.condensed_mass_fraction,
            "reporting_state": summary.get("state"),
            "reporting_text": summary.get("text"),
            "performance_status": outcome.kind,
            "performance_produced_a_result": outcome.result is not None,
            "performance_message": outcome.message[:200],
            "chamber_temperature_available":
                tc_study.points[0].metrics.get("chamber_temperature") is not None,
            "chamber_temperature_study_status":
                tc_study.points[0].status.value,
            "isp_study_status": isp_study.points[0].status.value,
            "isp_study_feasibility": isp_study.points[0].feasibility.value,
        })

    return {
        "case": "the four condensed reporting states, and the stage-aware "
                "consequence for a study",
        "rows": rows,
        "stage_aware": "a chamber the ideal model refuses still yields valid "
                       "thermochemistry metrics; only a study that requires a "
                       "performance metric is unevaluable there",
    }


# ===========================================================================
# CASE 6 and 7 — the trade studies
# ===========================================================================


def case_6_and_7_studies() -> dict:
    setup = ts.TradeStudySetup(chamber=CANONICAL_CASE,
                               performance=CANONICAL_PERFORMANCE)
    of = build_variable("oxidiser_fuel_ratio", start=2.5, end=4.5, count=41)
    eps = ExplicitNumericVariable(key="area_ratio", label="Area ratio  Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(10.0, 20.0, 40.0, 80.0))

    single = ts.build_definition(
        setup, [of, eps], outputs=("chamber_temperature",),
        objectives=(MAX_ISP,),
        constraints=(ConstraintDefinition("chamber_temperature",
                                          ComparisonOperator.LE, 3500.0),),
        title="canonical single-objective study")
    started = time.perf_counter()
    a = ts.run_trade_study(single, setup)
    a_seconds = time.perf_counter() - started

    two = single.replace(objectives=(MAX_ISP, MIN_TC),
                         scoring=WeightedScoreDefinition(
                             weights={"specific_impulse": 3.0,
                                      "chamber_temperature": 1.0}),
                         title="canonical two-objective study")
    started = time.perf_counter()
    b = ts.run_trade_study(two, setup)
    b_seconds = time.perf_counter() - started

    def best(result, objective):
        chosen, value = None, None
        for point in result.points:
            if not point.eligible_for_decision:
                continue
            current = point.metric(objective.metric)
            if current is None:
                continue
            if value is None or objective.is_better(current, value):
                chosen, value = point, current
        return None if chosen is None else {
            "index": chosen.index,
            "variables": dict(chosen.point.values),
            "value": value,
            "wording": "best evaluated feasible point",
        }

    return {
        "case_6_single_objective": {
            "title": single.title,
            "fingerprint": single.fingerprint,
            "design_points": len(a.points),
            "stage_solves": dict(a.counts.stage_solves),
            "seconds": round(a_seconds, 3),
            "evaluated": a.evaluated_count,
            "failed": a.failed_count,
            "feasible": a.feasible_count,
            "infeasible": a.infeasible_count,
            "ranking_length": len(a.ranking),
            "best": best(a, MAX_ISP),
        },
        "case_7_multi_objective": {
            "title": two.title,
            "fingerprint": two.fingerprint,
            "design_points": len(b.points),
            "stage_solves": dict(b.counts.stage_solves),
            "seconds": round(b_seconds, 3),
            "feasible": b.feasible_count,
            "infeasible": b.infeasible_count,
            "pareto_count": len(b.pareto_indices),
            "pareto_front": [
                {"index": i,
                 "variables": dict(b.by_index(i).point.values),
                 "specific_impulse": b.by_index(i).metric("specific_impulse"),
                 "chamber_temperature":
                     b.by_index(i).metric("chamber_temperature"),
                 "score": b.by_index(i).score}
                for i in b.pareto_indices],
            "scored": b.scored,
            "best_per_objective": {
                "maximize specific_impulse": best(b, MAX_ISP),
                "minimize chamber_temperature": best(b, MIN_TC),
            },
            "every_pareto_point_is_feasible": all(
                b.by_index(i).feasibility is Feasibility.FEASIBLE
                for i in b.pareto_indices),
        },
        "wording": "no global optimum is claimed anywhere; the best rows are "
                   "best evaluated feasible points over the grid that was run",
    }


# ===========================================================================
# the provenance chain
# ===========================================================================


def provenance_chain() -> dict:
    setup = ts.TradeStudySetup(chamber=CANONICAL_CASE,
                               performance=CANONICAL_PERFORMANCE)
    of = build_variable("oxidiser_fuel_ratio", start=3.0, end=4.0, count=3)
    eps = ExplicitNumericVariable(key="area_ratio", label="Ae/At",
                                  stage=STAGE_PERFORMANCE,
                                  entries=(20.0, 40.0))
    definition = ts.build_definition(
        setup, [of, eps], outputs=("chamber_temperature",),
        objectives=(MAX_ISP,),
        constraints=(ConstraintDefinition("chamber_temperature",
                                          ComparisonOperator.LE, 3600.0),),
        title="provenance reconstruction")
    result = ts.run_trade_study(definition, setup)

    point = result.points[3]
    record = result.provenance
    evaluator = ts.RocketForgeEvaluator(setup)
    chamber_case = evaluator.chamber_case(point.values)
    performance_case = evaluator.performance_case(point.values)

    # Reconstruct that one point from the recorded provenance alone.
    rebuilt_chamber = thermo.solve_case(chamber_case)
    rebuilt = perf.solve_performance(rebuilt_chamber, performance_case)

    return {
        "purpose": "reconstruct one study point from its recorded provenance",
        "point_index": point.index,
        "design_variables": dict(point.values),
        "chain": {
            "1_study_definition_fingerprint":
                record["definition_fingerprint"],
            "2_design_point": dict(point.values),
            "3_thermochemistry_request": {
                "fuel": chamber_case.fuel,
                "oxidiser": chamber_case.oxidiser,
                "oxidiser_fuel_ratio": chamber_case.oxidiser_fuel_ratio,
                "chamber_pressure_Pa": chamber_case.chamber_pressure,
                "fuel_temperature_K": chamber_case.fuel_temperature,
                "oxidiser_temperature_K": chamber_case.oxidiser_temperature,
            },
            "4_provider": record["provider"],
            "5_database_sha256":
                rebuilt_chamber.provenance.database_sha256
                if rebuilt_chamber.provenance else None,
            "6_chamber_state": {
                "temperature_K": rebuilt_chamber.state.temperature,
                "gas_constant": rebuilt_chamber.state.gas_constant,
                "gamma_frozen": rebuilt_chamber.state.gamma_frozen,
            },
            "7_gamma_reduction": {
                "strategy": record["performance_model"]["gamma_strategy"],
                "basis": record["performance_model"]["gamma_basis"],
                "gamma_used": rebuilt.result.reduced.gamma,
            },
            "8_performance_model": record["performance_model"]["model"],
            "9_nozzle_and_condition": {
                "area_ratio": performance_case.area_ratio,
                "ambient_pressure_Pa": performance_case.ambient.pressure,
                "scale": performance_case.scale.label,
            },
            "10_raw_metrics": dict(point.metrics),
            "11_decision": {
                "objectives": record["objectives"],
                "constraints": record["constraints"],
                "scoring": record["scoring"],
                "feasibility": point.feasibility.value,
                "constraint_outcomes": [o.describe()
                                        for o in point.constraint_outcomes],
            },
            "12_oracle_used": record["oracle_used"],
        },
        "reconstruction_matches": {
            key: point.metrics.get(key) == value
            for key, value in {
                "chamber_temperature": rebuilt_chamber.state.temperature,
                "specific_impulse": rebuilt.result.specific_impulse,
            }.items()
        },
        "verdict": "PASS" if (
            point.metrics.get("chamber_temperature")
            == rebuilt_chamber.state.temperature
            and point.metrics.get("specific_impulse")
            == rebuilt.result.specific_impulse) else "FAIL",
    }


def main() -> int:
    if not gateway.availability().usable:
        write("integrated_acceptance.json",
              {"status": "skipped", "reason": "no chemistry provider"})
        return 1

    print("Phase 5G integrated acceptance")
    write("canonical_case_lox_lch4.json", case_1_canonical())
    write("canonical_scaled_case.json", case_2_scaled())
    write("ambient_matrix.json", case_3_ambient())
    write("assigned_enthalpy_chain.json", case_4_assigned_enthalpy())
    write("condensed_chain.json", case_5_condensed())
    write("integrated_trade_studies.json", case_6_and_7_studies())
    write("provenance_chain.json", provenance_chain())
    return 0


if __name__ == "__main__":
    sys.exit(main())
