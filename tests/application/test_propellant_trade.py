"""LIQ-3: resolving, evaluating and presenting a liquid propellant trade.

Three layers of evidence:

* **Resolution.** :func:`build_definition` fills nothing in. Every way a LIQ-2
  requirement can leave an operating value open is checked to stay open until
  the user states it, and every stated requirement value is checked to win.
* **Evaluation, with a stub provider.** Deterministic in the base environment:
  failures stay in their own row, the nozzle-dependent tiers are unresolved
  without a stated area ratio, and the flow split is the definition applied.
* **Parity, with NASA CEA.** Each candidate's numbers are bit-identical to the
  production Thermochemistry -> Rocket Performance chain run by hand for the
  same case. Skipped where CEA is not installed.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from rocketforge.application.analysis import propellant_trade_service as service
from rocketforge.application.analysis import thermochemistry_presets as presets
from rocketforge.application.analysis import thermochemistry_provider as gateway_module
from rocketforge.application.analysis.engine_requirement_controller import (
    EngineRequirementController,
)
from rocketforge.application.analysis.propellant_trade_controller import (
    PropellantTradeController,
)
from rocketforge.engine.propellant_trade import (
    CandidateStatus,
    MixtureRatioSource,
    PerformanceBasis,
    PressureSource,
)
from rocketforge.engine.requirement import (
    AmbientMode,
    ChamberPressureMode,
    ChamberPressurePreference,
    CyclePreference,
    DesignEnvironment,
    EngineRequirement,
    FeedArchitecture,
    MixtureRatioMode,
    MixtureRatioPreference,
    PropellantMode,
    PropellantPreference,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXECUTABLE = tuple(p.key for p in presets.executable_presets())
BASE = EngineRequirement(thrust=1.0e6, burn_time=200.0)
STATED = service.TradeSettings(chamber_pressure=10e6, mixture_ratio_mode="catalogue")
IDEAL = STATED.replace(performance_basis=PerformanceBasis.IDEAL_AREA_RATIO, area_ratio=40.0)

_STATUS = gateway_module.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable, reason=f"NASA CEA provider unavailable ({_STATUS.status})")


def codes(requirement, settings=service.TradeSettings()):
    definition, issues = service.build_definition(requirement, settings)
    return definition, [issue.code for issue in issues]


def pair(key: str) -> PropellantPreference:
    return PropellantPreference(PropellantMode.EXPLICIT, key)


# ===========================================================================
# candidates and resolution
# ===========================================================================


def test_auto_evaluates_every_executable_pair_and_never_rfna():
    keys = service.candidate_keys(BASE)
    assert keys == EXECUTABLE and len(keys) == 12
    assert not {"sutton-rfna-rp1", "sutton-rfna-a50"} & set(keys)


def test_an_explicit_pair_is_the_only_candidate():
    assert service.candidate_keys(BASE.replace(propellant=pair("sutton-o2-h2"))) == (
        "sutton-o2-h2",)
    assert service.candidate_keys(BASE.replace(propellant=pair("sutton-rfna-rp1"))) == ()


def test_nothing_is_resolved_silently():
    definition, found = codes(BASE)
    assert definition is None
    assert found == ["CHAMBER_PRESSURE_UNRESOLVED", "MIXTURE_RATIO_UNRESOLVED"]


def test_an_upper_limit_is_not_an_operating_point():
    limited = BASE.replace(chamber_pressure=ChamberPressurePreference(
        ChamberPressureMode.UPPER_LIMIT, 12e6))
    _, found = codes(limited, service.TradeSettings(mixture_ratio_mode="catalogue"))
    assert found == ["CHAMBER_PRESSURE_UNRESOLVED"]
    _, found = codes(limited, STATED.replace(chamber_pressure=15e6))
    assert found == ["CHAMBER_PRESSURE_ABOVE_LIMIT"]
    definition, found = codes(limited, STATED)
    assert found == [] and definition.chamber_pressure == 10e6
    assert definition.pressure_source is PressureSource.STUDY


def test_a_stated_requirement_value_wins_over_the_study():
    target = BASE.replace(
        chamber_pressure=ChamberPressurePreference(ChamberPressureMode.TARGET, 7e6),
        mixture_ratio=MixtureRatioPreference(MixtureRatioMode.EXPLICIT, 2.7))
    definition, found = codes(target, STATED.replace(chamber_pressure=99e6,
                                                     mixture_ratio_mode="explicit",
                                                     mixture_ratio=9.0))
    assert found == []
    assert definition.chamber_pressure == 7e6
    assert definition.pressure_source is PressureSource.REQUIREMENT
    assert definition.mixture_ratio == 2.7
    assert definition.mixture_ratio_source is MixtureRatioSource.REQUIREMENT


def test_mixture_ratio_sources():
    definition, _ = codes(BASE, STATED)
    assert definition.mixture_ratio_source is MixtureRatioSource.CATALOGUE
    assert definition.mixture_ratio is None
    _, found = codes(BASE, STATED.replace(mixture_ratio_mode="explicit"))
    assert found == ["MIXTURE_RATIO_INVALID"]
    definition, _ = codes(BASE, STATED.replace(mixture_ratio_mode="explicit",
                                               mixture_ratio=2.0))
    assert definition.mixture_ratio_source is MixtureRatioSource.STUDY
    reference = BASE.replace(propellant=pair("sutton-o2-rp1"), mixture_ratio=
                             MixtureRatioPreference(MixtureRatioMode.PAIR_REFERENCE))
    definition, _ = codes(reference, service.TradeSettings(chamber_pressure=10e6))
    assert definition.mixture_ratio_source is MixtureRatioSource.CATALOGUE


def test_study_pressure_must_be_above_ambient_and_positive():
    _, found = codes(BASE, STATED.replace(chamber_pressure=50e3))
    assert found == ["CHAMBER_PRESSURE_NOT_ABOVE_AMBIENT"]
    _, found = codes(BASE, STATED.replace(chamber_pressure=-1.0))
    assert found == ["CHAMBER_PRESSURE_INVALID"]


def test_an_ideal_basis_needs_a_stated_area_ratio():
    _, found = codes(BASE, STATED.replace(performance_basis=PerformanceBasis.IDEAL_AREA_RATIO))
    assert found == ["AREA_RATIO_UNRESOLVED"]
    _, found = codes(BASE, IDEAL.replace(area_ratio=0.8))
    assert found == ["AREA_RATIO_UNRESOLVED"]


def test_an_incomplete_requirement_blocks_the_trade():
    _, found = codes(EngineRequirement(), STATED)
    assert found == ["REQUIREMENT_INCOMPLETE", "REQUIREMENT_INCOMPLETE"]
    _, found = codes(BASE.replace(propellant=pair("sutton-rfna-a50")), STATED)
    assert found == ["REQUIREMENT_INCOMPLETE"]


def test_feed_and_cycle_do_not_change_the_question():
    """Carried as intent in the snapshot; nothing evaluated reads them."""
    ffsc = BASE.with_feed(FeedArchitecture.PUMP_FED).replace(
        cycle=CyclePreference.FULL_FLOW_STAGED_COMBUSTION)
    a, _ = codes(BASE, IDEAL)
    b, _ = codes(ffsc, IDEAL)
    assert a.candidates == b.candidates and a.chamber_pressure == b.chamber_pressure
    source = (ROOT / "rocketforge" / "application" / "analysis"
              / "propellant_trade_service.py").read_text(encoding="utf-8")
    code = ast.unparse(ast.parse(source))
    assert ".cycle" not in code and ".feed" not in code


# ===========================================================================
# evaluation, with the stub provider
# ===========================================================================


def test_chamber_only_leaves_every_nozzle_quantity_unresolved(stub_gateway):
    definition, _ = codes(BASE, STATED)
    row = service.evaluate_candidate(definition, "sutton-o2-ch4")
    assert row.status is CandidateStatus.OK
    assert set(row.metrics) == {"chamber_temperature", "molar_mass", "gamma_frozen",
                                "gamma_equilibrium", "characteristic_velocity"}
    for key in ("specific_impulse", "thrust_coefficient", "mass_flow", "propellant_mass"):
        assert "No performance basis" in row.unresolved[key]
    assert row.oxidiser_fuel_ratio == presets.preset_named("sutton-o2-ch4").oxidiser_fuel_ratio
    assert (row.oxidiser_temperature, row.fuel_temperature) == (90.17, 111.643)


def test_the_flow_split_is_the_definition_applied(stub_gateway):
    definition, _ = codes(BASE, IDEAL.replace(gamma_basis="equilibrium"))
    row = service.evaluate_candidate(definition, "sutton-o2-ch4")
    m, r = row.metrics, row.oxidiser_fuel_ratio
    assert m["mass_flow"] == pytest.approx(1.0e6 / m["effective_exhaust_velocity"], rel=1e-15)
    assert m["oxidiser_mass_flow"] + m["fuel_mass_flow"] == pytest.approx(m["mass_flow"],
                                                                         rel=1e-14)
    assert m["oxidiser_mass_flow"] / m["fuel_mass_flow"] == pytest.approx(r, rel=1e-14)
    assert m["propellant_mass"] == pytest.approx(m["mass_flow"] * 200.0, rel=1e-15)


def test_a_nozzle_the_ideal_model_refuses_leaves_its_quantities_unresolved(stub_gateway):
    """Ae/At 5000 at sea level from 1 MPa holds an internal shock. The ideal
    model refuses it; the refusal is the reason on every nozzle and flow
    quantity, and the chamber quantities (c* included) stand."""
    definition, _ = codes(BASE, IDEAL.replace(chamber_pressure=1e6, area_ratio=5000.0))
    row = service.evaluate_candidate(definition, "sutton-o2-ch4")
    assert row.status is CandidateStatus.WARNING and row.ok
    assert "characteristic_velocity" in row.metrics
    for key in ("specific_impulse", "mass_flow", "propellant_mass"):
        assert row.unresolved[key].startswith("Ideal performance refused")
        assert "internal_normal_shock" in row.unresolved[key]


def test_a_failed_candidate_does_not_touch_the_others(stub_gateway, monkeypatch):
    """Fail one candidate's chamber; the rest are bit-identical to a clean run."""
    definition, _ = codes(BASE, IDEAL)
    clean = [service.evaluate_candidate(definition, k) for k in definition.candidates]
    from rocketforge.physics.thermochemistry import ProviderError

    original = stub_gateway.solve_chamber
    hydrogen = gateway_module.propellant_named("LH2").definition

    def failing(request):
        if request.fuel.propellant == hydrogen:
            raise ProviderError("injected failure")
        return original(request)

    monkeypatch.setattr(stub_gateway, "solve_chamber", failing)
    rows = [service.evaluate_candidate(definition, k) for k in definition.candidates]
    failed = [r for r in rows if not r.ok]
    assert {r.key for r in failed} == {"sutton-o2-h2", "sutton-f2-h2"}
    for row in failed:
        assert "injected failure" in row.message and not row.metrics
        assert row.chamber_pressure == 10e6 and row.oxidiser_fuel_ratio > 0
    for before, after in zip(clean, rows):
        if after.ok:
            assert after == before


def test_table_ordering_is_a_view_of_one_column(stub_gateway):
    definition, _ = codes(BASE, IDEAL)
    rows = tuple(service.evaluate_candidate(definition, k) for k in definition.candidates)
    result = service.assemble_result(definition, rows)
    natural = [r["key"] for r in service.table_rows(result)]
    assert natural == list(definition.candidates)
    ordered = service.table_rows(result, "specific_impulse", descending=True)
    values = [result.candidate(r["key"]).value("specific_impulse") for r in ordered]
    assert values == sorted(values, reverse=True)
    assert all("score" not in r for r in ordered)
    assert service.table_rows(result, "not-a-metric") == service.table_rows(result)


def test_evaluation_is_deterministic(stub_gateway):
    definition, _ = codes(BASE, IDEAL)
    a = [service.evaluate_candidate(definition, k) for k in definition.candidates]
    b = [service.evaluate_candidate(definition, k) for k in definition.candidates]
    assert a == b


# ===========================================================================
# the controller
# ===========================================================================


@pytest.fixture()
def pair_of_controllers(qt_app):
    requirement = EngineRequirementController()
    requirement.set_requirement(BASE)
    return requirement, PropellantTradeController(requirement)


def test_editing_and_browsing_solve_nothing(pair_of_controllers, stub_gateway):
    requirement, trade = pair_of_controllers
    trade.setStudyPressure("10")
    trade.setRatioMode("catalogue")
    trade.setPerformanceBasis("ideal_area_ratio")
    trade.setAreaRatio("40")
    trade.sortBy("specific_impulse")
    assert trade.property("canRun") is True and trade.property("hasResult") is False
    assert stub_gateway.calls == []


def test_run_evaluates_once_per_candidate_and_marks_stale_on_edit(pair_of_controllers,
                                                                  stub_gateway):
    requirement, trade = pair_of_controllers
    trade.setStudyPressure("10")
    trade.setRatioMode("catalogue")
    trade.runTrade()
    trade.run_to_completion()
    assert len(stub_gateway.calls) == 12
    assert trade.property("hasResult") and not trade.property("resultStale")
    calls = len(stub_gateway.calls)
    trade.sortBy("chamber_temperature")
    trade.selectCandidate("sutton-o2-ch4")
    assert len(stub_gateway.calls) == calls                          # browsing is free
    trade.setGammaBasis("equilibrium")
    assert trade.property("resultStale") is True
    assert len(stub_gateway.calls) == calls                          # editing is free
    trade.setGammaBasis("frozen")
    assert trade.property("resultStale") is False                    # same question again


def test_an_explicit_pair_runs_one_solve(pair_of_controllers, stub_gateway):
    requirement, trade = pair_of_controllers
    requirement.setPair("sutton-nto-mmh")
    trade.setStudyPressure("10")
    trade.setRatioMode("catalogue")
    trade.runTrade()
    trade.run_to_completion()
    assert len(stub_gateway.calls) == 1
    assert [r["key"] for r in trade.property("rows")] == ["sutton-nto-mmh"]


def test_no_provider_means_no_trade(pair_of_controllers, absent_gateway):
    _, trade = pair_of_controllers
    trade.setStudyPressure("10")
    trade.setRatioMode("catalogue")
    trade.runTrade()
    assert trade.property("busy") is False and trade.property("hasResult") is False
    assert "No thermochemistry provider" in trade.property("message")


def test_selection_reaches_the_requirement_explicitly(pair_of_controllers, stub_gateway):
    requirement, trade = pair_of_controllers
    trade.setStudyPressure("10")
    trade.setRatioMode("catalogue")
    trade.runTrade()
    trade.run_to_completion()
    assert trade.applySelectionToRequirement() is False             # nothing chosen
    assert trade.selectCandidate("sutton-o2-h2") is True
    assert requirement.requirement() == BASE                         # choosing alone writes nothing
    assert trade.applySelectionToRequirement() is True
    updated = requirement.requirement()
    assert updated.propellant == pair("sutton-o2-h2")
    assert updated.mixture_ratio.mode is MixtureRatioMode.PAIR_REFERENCE
    assert updated.chamber_pressure == ChamberPressurePreference(ChamberPressureMode.TARGET, 10e6)
    assert (updated.thrust, updated.burn_time) == (BASE.thrust, BASE.burn_time)
    assert trade.property("resultStale") is True                    # the question changed
    assert trade.applySelectionToRequirement() is False             # never from a stale result


def test_an_upper_limit_survives_applying_a_selection(qt_app, stub_gateway):
    requirement = EngineRequirementController()
    limited = BASE.replace(chamber_pressure=ChamberPressurePreference(
        ChamberPressureMode.UPPER_LIMIT, 12e6))
    requirement.set_requirement(limited)
    trade = PropellantTradeController(requirement)
    trade.setStudyPressure("10")
    trade.setRatioMode("explicit")
    trade.setStudyRatio("2.5")
    trade.runTrade()
    trade.run_to_completion()
    trade.selectCandidate("sutton-o2-ch4")
    trade.applySelectionToRequirement()
    updated = requirement.requirement()
    assert updated.chamber_pressure == limited.chamber_pressure
    assert updated.mixture_ratio == MixtureRatioPreference(MixtureRatioMode.EXPLICIT, 2.5)


def test_the_result_is_serialisable_and_saved_read_only(pair_of_controllers, stub_gateway,
                                                        tmp_path):
    from rocketforge.engine.propellant_trade import TradeResult

    _, trade = pair_of_controllers
    trade.setStudyPressure("10")
    trade.setRatioMode("catalogue")
    trade.runTrade()
    trade.run_to_completion()
    text = trade.property("resultJson")
    assert TradeResult.from_json(text) == trade.result()
    assert trade.saveResult(str(tmp_path / "trade.json"))
    assert TradeResult.from_json((tmp_path / "trade.json").read_text("utf-8")) == trade.result()


def test_the_assumptions_name_every_source(pair_of_controllers, stub_gateway):
    _, trade = pair_of_controllers
    trade.setStudyPressure("10")
    trade.setRatioMode("catalogue")
    trade.runTrade()
    trade.run_to_completion()
    rows = {r["label"]: r["value"] for r in trade.property("assumptionRows")}
    assert rows["Chamber pressure"] == "10 MPa · stated for this study"
    assert rows["O/F"] == "per candidate · each candidate's catalogue O/F"
    assert rows["Nozzle basis"].startswith("none stated")
    assert "intent only" in rows["Feed / cycle"]


# ===========================================================================
# parity with the production chain, under NASA CEA
# ===========================================================================


@requires_cea
@pytest.mark.parametrize("key", EXECUTABLE)
def test_each_candidate_matches_the_production_chain_exactly(key):
    from rocketforge.application.analysis import performance_service as performance
    from rocketforge.application.analysis.thermochemistry_provider import propellant_named
    from rocketforge.application.analysis.thermochemistry_service import (
        ChamberCase,
        solve_case,
    )
    from rocketforge.engineering.chamber import ChamberGammaBasis
    from rocketforge.physics.thermochemistry import GammaStrategy

    requirement = BASE.replace(environment=DesignEnvironment(AmbientMode.VACUUM))
    definition, _ = service.build_definition(requirement, IDEAL)
    row = service.evaluate_candidate(definition, key)

    preset = presets.preset_named(key)
    ox, fu = propellant_named(preset.oxidiser), propellant_named(preset.fuel)
    chamber = solve_case(ChamberCase(fuel=fu.key, oxidiser=ox.key,
                                     oxidiser_fuel_ratio=preset.oxidiser_fuel_ratio,
                                     chamber_pressure=10e6,
                                     fuel_temperature=fu.reference_temperature,
                                     oxidiser_temperature=ox.reference_temperature))
    perf = performance.solve_performance(chamber, performance.PerformanceCase(
        gamma_strategy=GammaStrategy.CHAMBER, gamma_basis=ChamberGammaBasis.FROZEN,
        area_ratio=40.0, ambient=performance.AmbientCondition(performance.AmbientMode.VACUUM)))
    assert row.ok, row.message
    assert row.metrics["chamber_temperature"] == chamber.state.temperature
    assert row.metrics["molar_mass"] == chamber.state.molar_mass
    assert row.metrics["characteristic_velocity"] == perf.result.characteristic_velocity
    assert row.metrics["specific_impulse"] == perf.result.specific_impulse
    assert row.metrics["mass_flow"] == 1.0e6 / perf.result.effective_exhaust_velocity


@requires_cea
def test_chamber_only_c_star_equals_the_performance_path_c_star():
    chamber_only, _ = service.build_definition(BASE, STATED)
    ideal, _ = service.build_definition(BASE, IDEAL)
    for key in ("sutton-o2-ch4", "sutton-nto-mmh"):
        a = service.evaluate_candidate(chamber_only, key).metrics["characteristic_velocity"]
        b = service.evaluate_candidate(ideal, key).metrics["characteristic_velocity"]
        assert a == b


@requires_cea
def test_lox_lh2_is_reported_against_its_sutton_ratio():
    """One familiar number, so a reader can sanity-check the table: LOX/LH2 at
    Sutton's O/F 4.02, 1000 psia, vacuum Ae/At 40 lands in the 4xx s band."""
    requirement = BASE.replace(environment=DesignEnvironment(AmbientMode.VACUUM),
                               propellant=pair("sutton-o2-h2"))
    definition, _ = service.build_definition(requirement, IDEAL.replace(chamber_pressure=6.895e6))
    row = service.evaluate_candidate(definition, "sutton-o2-h2")
    assert row.oxidiser_fuel_ratio == 4.02
    assert 420.0 < row.metrics["specific_impulse"] < 470.0
