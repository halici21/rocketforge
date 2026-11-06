"""DB-4B: the engine-level Isp ratio's rules. No test here pins a real engine's ratio, on purpose.

Each hazard changes one evidence record through the frozen types (never the shipped file) and checks that eligibility
refuses it. The run's rules are tested with injected solvers and made-up numbers. The one test that runs NASA CEA checks
only that both bases come back, because a pinned value would make this comparison lock the model.
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import math
import pathlib
import subprocess
import sys
from types import SimpleNamespace

import pytest

from rocketforge.application.analysis import reference_engine_isp_ratio as ratio
from rocketforge.application.analysis import reference_engine_regression as review
from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis.reference_engine_catalog import ReferenceEngineCatalog, load_reference_engines
from rocketforge.comparison.cases import SourceKind, VERDICT_KINDS
from rocketforge.comparison.engine_isp_ratio import (
    GAMMA_BASES,
    EngineIspRatio,
    EngineIspRatioError,
    IspRatioCell,
    engine_isp_ratio,
)
from rocketforge.evidence.engines import Conflict, TextValue
from rocketforge.evidence.engines.assertions import Qualifier
from rocketforge.evidence.engines.vocabulary import (
    ConflictResolution,
    Environment,
    IspBasis,
    MixtureRatioBasis,
    MixtureRatioForm,
    PressureBasis,
    PressureStation,
    ValueKind,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHIPPED = ROOT / "rocketforge" / "data" / "evidence" / "engines" / "reference_engines.json"
J2, J2S = "CFG-J2-230K", "CFG-J2S"
ISP, PC, MR, AR = (f"AS-DB05-US-J-2-00{i}" for i in (2, 3, 4, 7))
_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(not _STATUS.usable, reason=f"NASA CEA provider unavailable ({_STATUS.status})")


@pytest.fixture(scope="module")
def catalog():
    return load_reference_engines()


def edit(catalog, aid, **changes):
    corpus = catalog.corpus
    assertions = tuple(dataclasses.replace(a, **changes) if a.assertion_id == aid else a for a in corpus.assertions)
    return ReferenceEngineCatalog(dataclasses.replace(corpus, assertions=assertions), catalog.fingerprint)


def cond(catalog, aid, **changes):
    return edit(catalog, aid, conditions=dataclasses.replace(catalog.corpus.assertion_map[aid].conditions, **changes))


def refusals(catalog, cfg=J2):
    return " | ".join(ratio.eligibility(catalog, cfg).refusals)


def fake_chamber(case):
    return SimpleNamespace(state=object(), kind="ok", diagnostics=(), message="", case=case)


def fake_expansion(values):
    def solve(chamber, case):
        return SimpleNamespace(result=SimpleNamespace(specific_impulse=values[case.gamma_basis.value]),
                               diagnostics=(), message="")
    return solve


# ------------------------------------------------------------------ who qualifies


def test_exactly_the_two_j2_engines_qualify(catalog):
    assert set(ratio.eligible_configurations(catalog)) == {J2, J2S}


def test_every_other_configuration_says_why_not(catalog):
    for e in catalog.entries():
        checked = ratio.eligibility(catalog, e.configuration_id)
        assert bool(checked.inputs) != bool(checked.refusals), e.configuration_id


@pytest.mark.parametrize("cfg, printed, pc_psia, of, ar", [(J2, 425, 717, 5.5, 27.5), (J2S, 436, 1200, 5.5, 40)])
def test_the_inputs_are_the_records_as_printed(catalog, cfg, printed, pc_psia, of, ar):
    i = ratio.eligibility(catalog, cfg).inputs
    assert (i.printed_isp_s, i.oxidiser_fuel_ratio, i.area_ratio, i.environment) == (printed, of, ar, "VACUUM")
    assert i.chamber_pressure_pa == pytest.approx(pc_psia * 6894.757293168361)
    assert (i.oxidiser, i.oxidiser_temperature_k, i.fuel, i.fuel_temperature_k) == ("LOX", 90.17, "LH2", 20.27)


@pytest.mark.parametrize("cfg", [J2, J2S])
def test_the_result_declares_what_it_rests_on(catalog, cfg):
    text = " | ".join(ratio.eligibility(catalog, cfg).inputs.declarations)
    for word in ("not a thrust-chamber efficiency", "Isp basis as recorded: UNKNOWN", "mixture ratio basis as recorded: ENGINE",
                 "inlet state assumed, not printed", "both gamma bases", "no losses"):
        assert word in text


# ------------------------------------------------------------------ one refusal per rule


@pytest.mark.parametrize("environment", [Environment.UNKNOWN, Environment.ALTITUDE])
def test_an_isp_environment_must_be_known(catalog, environment):
    assert "environment not stated" in refusals(cond(catalog, ISP, environment=environment))


@pytest.mark.parametrize("kind", [ValueKind.AVERAGE, ValueKind.APPROXIMATE, ValueKind.DESIGN_VALUE, ValueKind.LIMIT])
@pytest.mark.parametrize("aid", [ISP, PC, MR, AR])
def test_every_input_must_be_a_point_value(catalog, aid, kind):
    assert "not a point value" in refusals(edit(catalog, aid, value_kind=kind))


def test_an_isp_in_other_units_is_refused(catalog):
    assert "is not seconds" in refusals(edit(catalog, ISP, unit_as_printed="N*s/kg"))


def test_a_source_ideal_value_is_not_a_printed_rating(catalog):
    a = catalog.corpus.assertion_map[ISP]
    changed = cond(catalog, ISP, qualifiers=(*a.conditions.qualifiers, Qualifier("performance_basis", "ideal")))
    assert "not a printed engine rating" in refusals(changed)


@pytest.mark.parametrize("station", [PressureStation.UNKNOWN, PressureStation.THROAT, PressureStation.INJECTOR_FACE])
def test_chamber_pressure_must_be_at_the_nozzle_stagnation_station(catalog, station):
    assert "nozzle stagnation" in refusals(cond(catalog, PC, pressure_station=station))


def test_chamber_pressure_must_be_absolute(catalog):
    assert "not absolute" in refusals(cond(catalog, PC, pressure_basis=PressureBasis.GAUGE))


def test_chamber_pressure_in_an_unknown_unit_is_refused(catalog):
    assert "unknown unit" in refusals(edit(catalog, PC, unit_as_printed="kgf/cm2a"))


def test_the_mixture_ratio_direction_must_be_printed(catalog):
    changed = cond(catalog, MR, mixture_ratio_form=MixtureRatioForm.FUEL_TO_OXIDIZER)
    assert "direction O/F is not printed" in refusals(changed)


@pytest.mark.parametrize("basis", [MixtureRatioBasis.UNKNOWN, MixtureRatioBasis.GAS_GENERATOR, MixtureRatioBasis.PREBURNER])
def test_the_mixture_ratio_must_be_an_engine_or_chamber_ratio(catalog, basis):
    assert "engine or a thrust-chamber ratio" in refusals(cond(catalog, MR, mixture_ratio_basis=basis))


def test_all_running_values_must_share_an_operating_point(catalog):
    assert "one operating point" in refusals(edit(catalog, PC, operating_point_id=None))


def test_a_propellant_without_a_model_definition_is_refused(catalog):
    aid = "AS-DB05-US-J-2-026"
    value = dataclasses.replace(catalog.corpus.assertion_map[aid].value, token="RP_1")
    assert "has no model definition" in refusals(edit(catalog, aid, value=value))


def test_a_value_that_is_not_one_number_is_refused(catalog):
    assert "not a single number" in refusals(edit(catalog, AR, value=TextValue("about 27"), unit_as_printed=""))


def test_an_open_conflict_still_blocks_the_value(catalog):
    corpus = catalog.corpus
    other = catalog.corpus.assertion_map["AS-DB05-US-J-2-001"].assertion_id
    conflict = Conflict("CF-TEST", "performance.specific_impulse_vac", (ISP, other), ConflictResolution.UNRESOLVED, (), "test")
    changed = ReferenceEngineCatalog(dataclasses.replace(corpus, conflicts=(*corpus.conflicts, conflict)), catalog.fingerprint)
    assert "conflict" in refusals(changed)


# ------------------------------------------------------------------ DB-4A is not relaxed


def test_the_db4a_review_still_refuses_the_engine_mixture_ratio(catalog):
    q = next(q for q in review.review_candidate(catalog, J2S).quantities if q.quantity == "mixture_ratio")
    assert q.result == review.BLOCKED_SEMANTICS
    assert any("engineering inference" in b for b in q.blockers)


def test_the_hard_and_validation_totals_stay_zero(catalog):
    results = {q.result for r in review.review_all(catalog) for q in r.quantities}
    assert not results & {review.HARD_REGRESSION_ELIGIBLE, review.VALIDATION_COMPARISON_ELIGIBLE}
    assert VERDICT_KINDS == {SourceKind.CEA_DIRECT, SourceKind.NASA_PUBLISHED}


# ------------------------------------------------------------------ the record has no verdict


def test_the_arithmetic_on_made_up_numbers():
    r = engine_isp_ratio("X", 300.0, {"frozen": 400.0, "equilibrium": 250.0}, ("declared",))
    assert [(c.gamma_basis, c.ideal_isp_s, c.ratio) for c in r.cells] == [("frozen", 400.0, 0.75), ("equilibrium", 250.0, 1.2)]


@pytest.mark.parametrize("record", [EngineIspRatio, IspRatioCell, ratio.IspRatioOutcome])
def test_no_record_can_carry_a_verdict_or_a_tolerance(record):
    names = {f.name for f in dataclasses.fields(record)}
    for word in ("verdict", "passed", "failed", "tolerance", "preferred", "average", "mean", "efficiency"):
        assert not [n for n in names if word in n], record


@pytest.mark.parametrize("ideal", [{"frozen": 400.0}, {"equilibrium": 400.0},
                                   {"frozen": 400.0, "equilibrium": 400.0, "chamber": 400.0}])
def test_both_bases_are_required_and_only_those(ideal):
    with pytest.raises(EngineIspRatioError):
        engine_isp_ratio("X", 300.0, ideal, ("declared",))


@pytest.mark.parametrize("bad", [0.0, -1.0, math.inf, math.nan])
def test_values_must_be_finite_and_positive(bad):
    with pytest.raises(EngineIspRatioError):
        engine_isp_ratio("X", bad, {"frozen": 400.0, "equilibrium": 400.0}, ("declared",))
    with pytest.raises(EngineIspRatioError):
        engine_isp_ratio("X", 300.0, {"frozen": bad, "equilibrium": 400.0}, ("declared",))


def test_a_ratio_with_nothing_declared_is_refused():
    with pytest.raises(EngineIspRatioError):
        engine_isp_ratio("X", 300.0, {"frozen": 400.0, "equilibrium": 400.0}, ())


# ------------------------------------------------------------------ the run


def test_a_run_solves_one_chamber_and_expands_it_under_both_bases(catalog):
    chambers, cases = [], []

    def expansion(chamber, case):
        cases.append(case)
        return SimpleNamespace(result=SimpleNamespace(specific_impulse=500.0), diagnostics=(), message="")

    def chamber(case):
        chambers.append(case)
        return fake_chamber(case)

    out = ratio.run_isp_ratio(catalog, J2, solve_chamber=chamber, solve_expansion=expansion)
    assert out.kind == ratio.KIND_OK and [c.gamma_basis for c in out.result.cells] == list(GAMMA_BASES)
    assert len(chambers) == 1 and (chambers[0].fuel, chambers[0].oxidiser) == ("LH2", "LOX")
    assert [c.gamma_basis.value for c in cases] == list(GAMMA_BASES)
    assert {c.gamma_strategy.value for c in cases} == {"chamber"}
    assert {c.ambient.pressure for c in cases} == {0.0} and {c.area_ratio for c in cases} == {27.5}


def test_a_ratio_above_one_is_returned_and_not_flagged(catalog):
    out = ratio.run_isp_ratio(catalog, J2, solve_chamber=fake_chamber,
                              solve_expansion=fake_expansion({"frozen": 100.0, "equilibrium": 100.0}))
    assert out.kind == ratio.KIND_OK and out.result.cells[0].ratio == 4.25 and out.warnings == ()


def test_one_refused_basis_leaves_no_ratio(catalog):
    def expansion(chamber, case):
        ok = case.gamma_basis.value == "frozen"
        return SimpleNamespace(result=SimpleNamespace(specific_impulse=400.0) if ok else None, diagnostics=(), message="no")

    out = ratio.run_isp_ratio(catalog, J2, solve_chamber=fake_chamber, solve_expansion=expansion)
    assert out.kind == ratio.KIND_REFUSED and out.result is None and "equilibrium basis" in out.message


def test_no_provider_is_reported_and_nothing_is_substituted(catalog):
    def absent(case):
        return SimpleNamespace(state=None, kind="unavailable", diagnostics=(), message="not installed")

    out = ratio.run_isp_ratio(catalog, J2, solve_chamber=absent, solve_expansion=fake_expansion({}))
    assert (out.kind, out.result, out.message) == (ratio.KIND_UNAVAILABLE, None, "not installed")


def test_a_refused_chamber_is_a_refusal(catalog):
    def refused(case):
        return SimpleNamespace(state=None, kind="no_solution", diagnostics=(), message="did not converge")

    out = ratio.run_isp_ratio(catalog, J2, solve_chamber=refused, solve_expansion=fake_expansion({}))
    assert (out.kind, out.result, out.message) == (ratio.KIND_REFUSED, None, "did not converge")


def test_an_ineligible_configuration_runs_nothing(catalog):
    def never(*_):
        raise AssertionError("no solver may run")

    out = ratio.run_isp_ratio(catalog, "CFG-F1", solve_chamber=never, solve_expansion=never)
    assert out.kind == ratio.KIND_NOT_ELIGIBLE and out.result is None and out.refusals


def test_warnings_are_carried_once(catalog):
    warning = SimpleNamespace(severity="warning", message="watch this")
    chamber = SimpleNamespace(state=object(), kind="warning", diagnostics=(warning,), message="")

    def expansion(chamber, case):
        return SimpleNamespace(result=SimpleNamespace(specific_impulse=400.0), diagnostics=(warning,), message="")

    out = ratio.run_isp_ratio(catalog, J2, solve_chamber=lambda case: chamber, solve_expansion=expansion)
    assert out.warnings == ("watch this",)


# ------------------------------------------------------------------ with NASA CEA: both bases, no value pinned


@requires_cea
@pytest.mark.parametrize("cfg", [J2, J2S])
def test_a_real_run_returns_both_bases(catalog, cfg):
    out = ratio.run_isp_ratio(catalog, cfg)
    assert out.kind == ratio.KIND_OK, out.message
    assert [c.gamma_basis for c in out.result.cells] == list(GAMMA_BASES)
    assert all(math.isfinite(c.ratio) and c.ratio > 0.0 for c in out.result.cells)


@requires_cea
def test_the_inlet_assumptions_are_the_definitions_reference_temperatures():
    for key, temperature in ratio.PROPELLANTS.values():
        assert gateway.propellant_named(key).definition.reference_temperature == temperature


@requires_cea
def test_the_throat_strategy_gives_the_chamber_strategys_isp(catalog):
    """Why the design fixes one strategy: in this model the two are one exponent, for either basis."""
    from rocketforge.application.analysis.performance_service import PerformanceCase, solve_performance
    from rocketforge.application.analysis.thermochemistry_service import ChamberCase, solve_case
    from rocketforge.engineering.chamber.handshake import ChamberGammaBasis
    from rocketforge.physics.thermochemistry.types import GammaStrategy

    i = ratio.eligibility(catalog, J2).inputs
    chamber = solve_case(ChamberCase(i.fuel, i.oxidiser, i.oxidiser_fuel_ratio, i.chamber_pressure_pa,
                                     i.fuel_temperature_k, i.oxidiser_temperature_k))
    for basis in ChamberGammaBasis:
        isp = {s: solve_performance(chamber, PerformanceCase(gamma_strategy=s, gamma_basis=basis,
                                                             area_ratio=i.area_ratio)).result.specific_impulse
               for s in (GammaStrategy.CHAMBER, GammaStrategy.THROAT)}
        assert isp[GammaStrategy.CHAMBER] == isp[GammaStrategy.THROAT]


# ------------------------------------------------------------------ what it does not touch


def test_the_comparison_module_reaches_no_solver():
    from rocketforge.comparison import engine_isp_ratio as module

    source = inspect.getsource(module)
    for layer in ("rocketforge.providers", "rocketforge.engineering", "rocketforge.application", "rocketforge.evidence"):
        assert layer not in source, layer


@pytest.mark.parametrize("module", ["rocketforge.comparison.engine_isp_ratio",
                                    "rocketforge.application.analysis.reference_engine_isp_ratio"])
def test_no_write_path(module):
    source = inspect.getsource(sys.modules.get(module) or __import__(module, fromlist=["x"]))
    for forbidden in ("open(", "write_text", "write_bytes", "json.dump", "unlink", "shutil"):
        assert forbidden not in source, forbidden


def test_reading_eligibility_does_not_load_the_performance_chain():
    code = ("import sys\n"
            "from rocketforge.application.analysis.reference_engine_catalog import load_reference_engines\n"
            "from rocketforge.application.analysis import reference_engine_isp_ratio as r\n"
            "c = load_reference_engines(); assert r.eligible_configurations(c)\n"
            "names = ('rocketforge.application.analysis.performance_service', 'rocketforge.providers.cea')\n"
            "assert not [n for n in names if n in sys.modules], names\n")
    run = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT, timeout=120)
    assert run.returncode == 0, run.stderr


def test_the_corpus_is_unchanged_by_a_run(catalog):
    before = hashlib.sha256(SHIPPED.read_bytes()).hexdigest()
    corpus = catalog.corpus
    ratio.run_isp_ratio(catalog, J2, solve_chamber=fake_chamber, solve_expansion=fake_expansion({"frozen": 400.0, "equilibrium": 400.0}))
    assert catalog.corpus is corpus and hashlib.sha256(SHIPPED.read_bytes()).hexdigest() == before
