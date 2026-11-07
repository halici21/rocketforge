"""DB-4C: the ideal reference case runner, at every point.

The rules are tested with injected solvers and made-up numbers. The CEA-gated tests assert structure and finiteness
only: no computed difference is pinned anywhere, and no rule may change in response to one.
"""

from __future__ import annotations

import dataclasses
import inspect
import math
import pathlib
import subprocess
import sys
from types import SimpleNamespace

import pytest

from rocketforge.application.analysis import reference_engine_regression as review
from rocketforge.application.analysis import reference_ideal_case as ideal
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.performance_oracle import ORACLE_FAILED, ORACLE_OK, ORACLE_UNAVAILABLE, OracleOutcome
from rocketforge.application.analysis.performance_service import AmbientMode
from rocketforge.application.analysis.reference_engine_catalog import load_reference_engines
from rocketforge.comparison.compare import COMPARED
from rocketforge.comparison.ssme_tdk_1985 import AREA_RATIO, CURRENT_DESIGN, LARGE_THROAT
from rocketforge.comparison.tdk_1985 import KEY_CHAMBER_TEMPERATURE, KEY_VACUUM_ISP_EQUILIBRIUM, KEY_VACUUM_ISP_FROZEN
from rocketforge.comparison.tdk_manual_1985 import ASE, RL10_OTV
from rocketforge.comparison.units import to_canonical
from rocketforge.core.constants import STANDARD_GRAVITY
from rocketforge.physics.thermochemistry import CompositionBasis
from rocketforge.physics.thermochemistry.types import GammaStrategy

ROOT = pathlib.Path(__file__).resolve().parents[2]
_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(not _STATUS.usable, reason=f"NASA CEA provider unavailable ({_STATUS.status})")
POINTS = ideal.POINTS
EACH_POINT = pytest.mark.parametrize("point", POINTS, ids=lambda p: p.case.case_id)
PSIA = 0.45359237 * 9.80665 / 0.0254 ** 2

# made-up numbers, chosen only to be distinguishable from one another
TC_K = 3000.0
ORACLE_ISP = {"equilibrium": 401.0, "frozen": 381.0}
REDUCED_ISP = {"equilibrium": 402.5, "frozen": 383.5}


def fake_state(temperature: float = TC_K) -> SimpleNamespace:
    composition = SimpleNamespace(basis=CompositionBasis.MOLE_FRACTION, species_names=("H2O",), fraction_of=lambda n: 1.0)
    return SimpleNamespace(temperature=temperature, pressure=1.0e6, molar_mass=0.013, gamma_equilibrium=1.15,
                           gamma_frozen=1.2, density=1.0, enthalpy=-1.0e6, entropy=1.0e4, cp_equilibrium=8000.0,
                           cp_frozen=4000.0, cv=3300.0, condensed_mass_fraction=0.0, composition=composition)


def fake_chamber(case, *, diagnostics=()):
    return SimpleNamespace(state=fake_state(), kind="ok", diagnostics=diagnostics, message="", case=case)


def fake_expansion(values=None, *, diagnostics=()):
    values = values or REDUCED_ISP

    def solve(chamber, case):
        return SimpleNamespace(result=SimpleNamespace(specific_impulse=values[case.gamma_basis.value]),
                               diagnostics=diagnostics, message="")
    return solve


def fake_oracle(values=None):
    values = values or ORACLE_ISP

    def run(case, area_ratio, mode):
        return OracleOutcome(kind=ORACLE_OK, case=case, area_ratio=area_ratio, mode=mode,
                             specific_impulse_vacuum=values[mode], specific_impulse=values[mode] - 10.0)
    return run


def solvers(**overrides):
    kwargs = dict(solve_chamber=fake_chamber, solve_expansion=fake_expansion(), oracle=fake_oracle())
    kwargs.update(overrides)
    return kwargs


def run(point=None, **overrides):
    if point is None:
        return ideal.run_ideal_case(**solvers(**overrides))
    return ideal.run_ideal_case(point, **solvers(**overrides))


# ------------------------------------------------------------------ one operating point per case


def test_without_a_point_the_current_design_runs():
    out = run()
    assert out.point is CURRENT_DESIGN and out.case is CURRENT_DESIGN.case
    assert out.chamber_case.chamber_pressure == pytest.approx(3285.0 * PSIA, rel=1e-15)
    assert AREA_RATIO == 77.5


@EACH_POINT
def test_one_point_is_solved_once_and_used_by_every_computation(point):
    calls = {"chamber": [], "expansion": [], "oracle": []}

    def chamber(case):
        calls["chamber"].append(case)
        return fake_chamber(case)

    def expansion(state, case):
        calls["expansion"].append((state, case))
        return fake_expansion()(state, case)

    def oracle(case, area_ratio, mode):
        calls["oracle"].append((case, area_ratio, mode))
        return fake_oracle()(case, area_ratio, mode)

    out = run(point, solve_chamber=chamber, solve_expansion=expansion, oracle=oracle)
    assert out.kind == ideal.KIND_OK, out.message
    assert out.point is point and out.case is point.case
    (solved,) = calls["chamber"]
    assert (solved.fuel, solved.fuel_temperature, solved.oxidiser, solved.oxidiser_temperature) == ("LH2", 20.27, "LOX", 90.17)
    assert solved.oxidiser_fuel_ratio == point.oxidiser_fuel_ratio
    assert solved.chamber_pressure == pytest.approx(point.chamber_pressure_psia * PSIA, rel=1e-15)
    assert sorted(mode for _, _, mode in calls["oracle"]) == ["equilibrium", "frozen"]
    assert all(case is solved and area == point.area_ratio for case, area, _ in calls["oracle"])
    assert sorted(c.gamma_basis.value for _, c in calls["expansion"]) == ["equilibrium", "frozen"]
    for state, c in calls["expansion"]:
        assert state.case is solved
        assert c.gamma_strategy is GammaStrategy.CHAMBER and c.area_ratio == point.area_ratio
        assert c.ambient.mode is AmbientMode.VACUUM


def test_the_points_are_the_ssme_reports_two_then_the_manuals_two_samples():
    assert POINTS == (CURRENT_DESIGN, LARGE_THROAT, RL10_OTV, ASE)


def test_the_points_are_run_at_their_own_inputs():
    runs = [ideal.chamber_case(p) for p in POINTS]
    assert [r.chamber_pressure for r in runs] == pytest.approx(
        [3285.0 * PSIA, 3010.0 * PSIA, 394.3 * PSIA, 2287.0 * PSIA], rel=1e-15)
    assert [r.oxidiser_fuel_ratio for r in runs] == [6.05485, 6.05485, 5.035244, 6.378]
    assert {(r.fuel_temperature, r.oxidiser_temperature) for r in runs} == {(20.27, 90.17)}
    seen = []
    ideal.run_ideal_cases(**solvers(oracle=lambda case, area, mode: seen.append(area) or fake_oracle()(case, area, mode)))
    assert sorted(set(seen)) == [69.5, 77.5, 205.03, 400.7148]


# ------------------------------------------------------------------ step A: compared, never judged


@EACH_POINT
def test_step_a_compares_every_quantity_and_judges_none(point):
    out = run(point)
    assert out.step_a.verdict == COMPARED and not out.step_a.not_observed
    assert out.step_a.case is point.case
    assert [r.verdict for r in out.step_a.rows] == [COMPARED] * 3
    assert all(r.bound is None for r in out.step_a.rows)


def test_step_a_pairs_shifting_with_shifting_and_frozen_with_frozen():
    rows = {r.key: r for r in run().step_a.rows}
    assert rows[KEY_CHAMBER_TEMPERATURE].observed == TC_K
    assert rows[KEY_VACUUM_ISP_EQUILIBRIUM].observed == pytest.approx(ORACLE_ISP["equilibrium"] * STANDARD_GRAVITY)
    assert rows[KEY_VACUUM_ISP_FROZEN].observed == pytest.approx(ORACLE_ISP["frozen"] * STANDARD_GRAVITY)


def test_step_a_uses_the_vacuum_figure_not_the_optimum_one():
    rows = {r.key: r for r in run().step_a.rows}
    for key, mode in ideal.STEP_A_ORACLE_MODES.items():
        assert rows[key].observed != pytest.approx((ORACLE_ISP[mode] - 10.0) * STANDARD_GRAVITY)


# ------------------------------------------------------------------ step B: a model difference, the printout absent


@EACH_POINT
def test_step_b_pairs_each_gamma_basis_with_its_expansion(point):
    rows = run(point).step_b
    assert [(r.gamma_basis, r.oracle_mode) for r in rows] == [("frozen", "frozen"), ("equilibrium", "equilibrium")]
    for r in rows:
        assert r.rocketforge_isp_s == REDUCED_ISP[r.gamma_basis]
        assert r.cea_isp_s == ORACLE_ISP[r.oracle_mode]
        assert r.relative_difference == pytest.approx((r.rocketforge_isp_s - r.cea_isp_s) / r.cea_isp_s)
        assert r.kind == "model difference" and "vacuum" in r.reference


@EACH_POINT
def test_no_row_puts_rocketforge_beside_the_printout(point):
    out = run(point)
    step_a_values = {r.observed for r in out.step_a.rows}
    assert not step_a_values & {v * STANDARD_GRAVITY for v in REDUCED_ISP.values()}
    printed = {q.value for q in out.case.quantities}
    assert not printed & {v for r in out.step_b for v in (r.rocketforge_isp_s, r.cea_isp_s)}
    assert "no row compares RocketForge with the printout directly" in out.declarations


def test_no_row_puts_one_point_beside_the_other():
    """Each point's rows hold its own printed values and nothing else."""
    for out in ideal.run_ideal_cases(**solvers()):
        assert out.step_a.case is out.case
        own = {q.key: to_canonical(q.value, q.unit)[0] for q in out.case.quantities}
        assert {r.key: r.reference for r in out.step_a.rows} == pytest.approx(own, rel=1e-15)


@pytest.mark.parametrize("record", [ideal.ReductionRow, ideal.IdealCaseOutcome])
def test_no_record_can_carry_a_verdict_or_a_tolerance(record):
    names = {f.name for f in dataclasses.fields(record)}
    assert not names & {"verdict", "passed", "tolerance", "bound", "total", "combined"}


# ------------------------------------------------------------------ declarations


def test_the_current_design_declares_its_input_differences():
    text = " | ".join(run().declarations)
    for needed in ("90.180", "90.17", "-3102.000", "-3102.055", "-2154.000", "-2153.920", "77.5 as scheduled",
                   "77.50022", "species", "3285 psia", "AS-DB05-US-SSME-BLOCK-I-002", "sample run"):
        assert needed in text, needed


def test_the_large_throat_declares_its_own_area_ratio_and_no_engine_assertion():
    text = " | ".join(run(LARGE_THROAT).declarations)
    for needed in ("90.180", "-3102.055", "-2153.920", "69.5 as scheduled", "69.48698", "species", "3010 psia",
                   "linked to no catalog configuration", "sample run"):
        assert needed in text, needed
    assert "AS-DB05" not in text and "77.5" not in text and "3285" not in text


def test_the_rl10_otv_declares_its_own_cards_inputs_and_conventions():
    text = " | ".join(run(RL10_OTV).declarations)
    for needed in ("-3102.000 cal/mol at 90.110 K", "run at 90.17 K", "-3102.055", "-2154.000 cal/mol at 20.56 K",
                   "run at 20.27 K", "-2153.920", "205.03 as scheduled", "205.0338", "species", "394.3 psia",
                   "an RL10 test engine, linked to no catalog configuration", "three-zone sample", "not from Table 7-3"):
        assert needed in text, needed
    for absent in ("AS-DB05", "SSME", "90.180", "77.5", "69.5", "3285", "3010"):
        assert absent not in text, absent


def test_the_ase_declares_its_own_inputs_and_conventions_and_the_unrounded_area_ratio():
    text = " | ".join(run(ASE).declarations)
    for needed in ("-3102.000 cal/mol at 90.180 K", "run at 90.17 K", "-3102.055", "-2154.000 cal/mol at 20.27 K",
                   "run at 20.27 K", "-2153.920", "400.7148 as scheduled", "400.7248", "species", "2287 psia",
                   "a prototype engine, linked to no catalog configuration", "three-zone sample", "not from Table 7-5"):
        assert needed in text, needed
    for absent in ("AS-DB05", "SSME", "400.715 ", "2300", "77.5", "205.03", "3285"):
        assert absent not in text, absent


def _differing(a: tuple[str, ...], b: tuple[str, ...]) -> list[str]:
    return [x.split(":")[0] for x, y in zip(a, b, strict=True) if x != y]


def test_the_points_differ_only_in_their_own_inputs():
    current, large, otv, ase = (ideal.declarations(p) for p in POINTS)
    assert len(current) == len(large) == len(otv) == len(ase) == 10
    assert _differing(current, large) == ["area ratio", "chamber pressure"]
    assert _differing(current, otv) == ["O2(L)", "H2(L)", "area ratio", "chamber pressure",
                                        "vacuum and frozen-at-chamber conventions"]
    assert _differing(current, ase) == ["area ratio", "chamber pressure", "vacuum and frozen-at-chamber conventions"]
    assert ideal.declarations() == current


# ------------------------------------------------------------------ all or nothing per point, never raises


def test_no_provider_is_reported_and_nothing_is_substituted():
    out = run(solve_chamber=lambda case: SimpleNamespace(state=None, kind="unavailable", diagnostics=(), message="x"))
    assert out.kind == ideal.KIND_UNAVAILABLE and out.step_a is None and out.step_b == ()
    assert out.declarations == ideal.declarations(CURRENT_DESIGN)


def test_a_refused_chamber_is_a_refusal():
    out = run(LARGE_THROAT,
              solve_chamber=lambda case: SimpleNamespace(state=None, kind="no_solution", diagnostics=(), message="no"))
    assert out.kind == ideal.KIND_REFUSED and out.step_a is None and out.step_b == ()
    assert out.point is LARGE_THROAT and out.declarations == ideal.declarations(LARGE_THROAT)


@pytest.mark.parametrize("kind, expected", [(ORACLE_UNAVAILABLE, ideal.KIND_UNAVAILABLE),
                                            (ORACLE_FAILED, ideal.KIND_REFUSED)])
@pytest.mark.parametrize("failing", ["equilibrium", "frozen"])
def test_one_failed_cea_expansion_leaves_nothing(kind, expected, failing):
    good = fake_oracle()

    def oracle(case, area_ratio, mode):
        return OracleOutcome(kind=kind, message="no") if mode == failing else good(case, area_ratio, mode)

    out = run(oracle=oracle)
    assert out.kind == expected and failing in out.message
    assert out.step_a is None and out.step_b == ()


@pytest.mark.parametrize("failing", ["equilibrium", "frozen"])
def test_one_refused_basis_leaves_nothing(failing):
    def expansion(chamber, case):
        ok = case.gamma_basis.value != failing
        return SimpleNamespace(result=SimpleNamespace(specific_impulse=400.0) if ok else None, diagnostics=(),
                               message="refused")

    out = run(solve_expansion=expansion)
    assert out.kind == ideal.KIND_REFUSED and failing in out.message
    assert out.step_a is None and out.step_b == ()


@pytest.mark.parametrize("failing", range(4))
def test_one_points_failure_does_not_hide_the_others_results(failing):
    good = fake_oracle()
    failing_area = POINTS[failing].area_ratio

    def oracle(case, area_ratio, mode):
        return OracleOutcome(kind=ORACLE_FAILED, message="no") if area_ratio == failing_area else good(case, area_ratio, mode)

    outcomes = ideal.run_ideal_cases(**solvers(oracle=oracle))
    assert [o.point for o in outcomes] == list(POINTS)
    for i, out in enumerate(outcomes):
        if i == failing:
            assert out.kind == ideal.KIND_REFUSED and out.step_a is None and out.step_b == ()
        else:
            assert out.kind == ideal.KIND_OK and len(out.step_a.rows) == 3


def test_warnings_are_carried_once():
    warning = SimpleNamespace(severity="warning", message="watch this")
    out = run(solve_chamber=lambda case: fake_chamber(case, diagnostics=(warning,)),
              solve_expansion=fake_expansion(diagnostics=(warning,)))
    assert out.warnings == ("watch this",)


# ------------------------------------------------------------------ what it does not touch


def test_the_hard_and_validation_totals_stay_zero():
    results = {q.result for r in review.review_all(load_reference_engines()) for q in r.quantities}
    assert not results & {review.HARD_REGRESSION_ELIGIBLE, review.VALIDATION_COMPARISON_ELIGIBLE}


def test_no_write_path():
    names = ("ssme_tdk_1985", "tdk_1985", "tdk_manual_1985")
    for module in (ideal, *(sys.modules[f"rocketforge.comparison.{name}"] for name in names)):
        source = inspect.getsource(module)
        for forbidden in ("open(", "write_text", "write_bytes", "json.dump", "unlink", "shutil"):
            assert forbidden not in source, (module.__name__, forbidden)


def test_importing_the_runner_loads_no_performance_chain_or_provider():
    code = ("import sys\n"
            "from rocketforge.application.analysis import reference_ideal_case\n"
            "names = ('rocketforge.application.analysis.performance_service', 'rocketforge.providers.cea')\n"
            "assert not [n for n in names if n in sys.modules], [n for n in names if n in sys.modules]\n")
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert result.returncode == 0, result.stderr


# ------------------------------------------------------------------ with NASA CEA: complete and unjudged, nothing pinned


@requires_cea
def test_a_real_run_of_every_point_is_complete_and_unjudged():
    outcomes = ideal.run_ideal_cases()
    assert [o.point for o in outcomes] == list(POINTS)
    for out in outcomes:
        assert out.kind == ideal.KIND_OK, out.message
        assert out.step_a.verdict == COMPARED and not out.step_a.not_observed
        assert all(r.verdict == COMPARED and math.isfinite(r.observed) and r.observed > 0.0 for r in out.step_a.rows)
        assert [(r.gamma_basis, r.oracle_mode) for r in out.step_b] == list(ideal.PAIRINGS)
        assert all(math.isfinite(r.rocketforge_isp_s) and math.isfinite(r.cea_isp_s) for r in out.step_b)


@requires_cea
def test_the_inlet_temperatures_are_the_definitions_reference_temperatures():
    for key, temperature in (ideal.FUEL, ideal.OXIDISER):
        assert gateway.propellant_named(key).definition.reference_temperature == temperature
