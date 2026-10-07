"""LIQ-4: sizing the ideal thrust chamber and nozzle at a selected trade candidate.

Three layers of evidence:

* **Resolution.** Only a selected, current LIQ-3 candidate is an operating
  point, and a sizing needs a stated area ratio: the trade's, or the user's.
* **Sizing, with a stub provider.** Deterministic in the base environment:
  thrust closes on the target, the geometry is the accepted relations applied,
  the trade's own numbers are reproduced exactly, and the ideal model's
  refusals and signed pressure thrust come through unchanged.
* **Parity, with NASA CEA.** The sizing equals the production Thermochemistry
  -> Rocket Performance chain run by hand, scaled to the same mass flow.
"""

from __future__ import annotations

import ast
import math
import pathlib
from dataclasses import replace

import pytest

from rocketforge.application.analysis import chamber_sizing_service as service
from rocketforge.application.analysis import propellant_trade_service as trade_service
from rocketforge.application.analysis import thermochemistry_provider as gateway_module
from rocketforge.application.analysis.chamber_sizing_controller import (
    ChamberSizingController,
)
from rocketforge.application.analysis.engine_requirement_controller import (
    EngineRequirementController,
)
from rocketforge.application.analysis.propellant_trade_controller import (
    PropellantTradeController,
)
from rocketforge.engine.chamber_sizing import (
    SIZING_QUANTITIES,
    AreaRatioSource,
    SizingResult,
    SizingStatus,
)
from rocketforge.engine.propellant_trade import PerformanceBasis
from rocketforge.engine.requirement import (
    AmbientMode,
    CyclePreference,
    DesignEnvironment,
    EngineRequirement,
    FeedArchitecture,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = EngineRequirement(thrust=1.0e6, burn_time=200.0)          # sea-level design ambient
VACUUM = BASE.replace(environment=DesignEnvironment(AmbientMode.VACUUM))
CHAMBER_ONLY = trade_service.TradeSettings(chamber_pressure=10e6, mixture_ratio_mode="catalogue")
IDEAL = CHAMBER_ONLY.replace(performance_basis=PerformanceBasis.IDEAL_AREA_RATIO,
                             area_ratio=40.0)
KEY = "sutton-o2-ch4"

_STATUS = gateway_module.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable, reason=f"NASA CEA provider unavailable ({_STATUS.status})")


def trade(requirement=BASE, settings=IDEAL, selected=KEY):
    definition, issues = trade_service.build_definition(requirement, settings)
    assert definition is not None, issues
    rows = tuple(trade_service.evaluate_candidate(definition, k) for k in definition.candidates)
    result = trade_service.assemble_result(definition, rows)
    return result.with_selection(selected) if selected else result


def sized(result, settings=service.SizingSettings()):
    point, issues = service.operating_point(result, stale=False)
    assert point is not None, issues
    definition, issues = service.build_definition(point, settings)
    assert definition is not None, issues
    return service.solve_sizing(definition)


def codes(result, stale=False, settings=service.SizingSettings()):
    point, issues = service.operating_point(result, stale)
    if point is None:
        return [i.code for i in issues]
    return [i.code for i in service.build_definition(point, settings)[1]]


# ===========================================================================
# resolution
# ===========================================================================


def test_only_a_selected_current_candidate_is_an_operating_point(stub_gateway):
    assert codes(None) == ["NO_TRADE"]
    assert codes(trade(selected="")) == ["NO_SELECTION"]
    assert codes(trade(), stale=True) == ["TRADE_STALE"]
    assert codes(trade()) == []


def test_a_failed_selection_is_not_an_operating_point(stub_gateway):
    """The trade never lets a failed candidate be selected; a record built
    around that guard is still refused here, not sized."""
    result = trade()
    failed = replace(result.candidate(KEY), status=trade_service.CandidateStatus.FAILED,
                     metrics={}, message="injected")
    candidates = tuple(failed if c.key == KEY else c for c in result.candidates)
    assert codes(replace(result, candidates=candidates)) == ["SELECTION_FAILED"]


def test_the_operating_point_is_the_trade_candidate_verbatim(stub_gateway):
    result = trade()
    point, _ = service.operating_point(result, stale=False)
    candidate = result.candidate(KEY)
    assert (point.pair_key, point.oxidiser, point.fuel) == (KEY, candidate.oxidiser,
                                                            candidate.fuel)
    assert point.oxidiser_fuel_ratio == candidate.oxidiser_fuel_ratio
    assert point.chamber_pressure == candidate.chamber_pressure == 10e6
    assert (point.oxidiser_temperature, point.fuel_temperature) == (
        candidate.oxidiser_temperature, candidate.fuel_temperature)
    assert point.gamma_basis == result.definition.gamma_basis
    assert point.ambient_pressure == BASE.environment.ambient_pressure
    assert point.thrust == BASE.thrust
    assert point.trade_fingerprint == result.definition.fingerprint
    assert point.recorded == dict(candidate.metrics)
    assert point.trade_provenance == dict(result.provenance)


def test_the_area_ratio_is_stated_never_assumed(stub_gateway):
    assert codes(trade(settings=CHAMBER_ONLY)) == ["AREA_RATIO_UNRESOLVED"]
    assert codes(trade(settings=CHAMBER_ONLY),
                 settings=service.SizingSettings(area_ratio=1.0)) == ["AREA_RATIO_INVALID"]
    point, _ = service.operating_point(trade(), stale=False)
    definition, _ = service.build_definition(point, service.SizingSettings())
    assert (definition.area_ratio, definition.area_ratio_source) == (40.0, AreaRatioSource.TRADE)
    definition, _ = service.build_definition(point, service.SizingSettings(area_ratio=25.0))
    assert (definition.area_ratio, definition.area_ratio_source) == (25.0,
                                                                     AreaRatioSource.SIZING)


def test_feed_and_cycle_are_not_read():
    """Intent only. The sizing chain has no reference to them, and an FFSC
    requirement gives the same operating point as an unstated one."""
    for name in ("chamber_sizing_service.py", "chamber_sizing_controller.py"):
        source = (ROOT / "rocketforge" / "application" / "analysis" / name).read_text("utf-8")
        code = ast.unparse(ast.parse(source))
        assert ".cycle" not in code and ".feed" not in code, name


def test_an_ffsc_requirement_sizes_identically(stub_gateway):
    ffsc = BASE.with_feed(FeedArchitecture.PUMP_FED).replace(
        cycle=CyclePreference.FULL_FLOW_STAGED_COMBUSTION)
    a, b = sized(trade(BASE)), sized(trade(ffsc))
    assert a.quantities == b.quantities


# ===========================================================================
# sizing, with the stub provider
# ===========================================================================


def test_thrust_closes_on_the_target(stub_gateway):
    for requirement in (BASE, VACUUM):
        result = sized(trade(requirement))
        q = result.quantities
        assert result.ok
        assert abs(q["thrust_closure"]) <= 1e-12
        assert q["thrust"] == pytest.approx(1.0e6, rel=1e-12)
        assert q["momentum_thrust"] + q["pressure_thrust"] == q["thrust"]
        assert q["thrust"] == pytest.approx(q["mass_flow"] * q["effective_exhaust_velocity"],
                                            rel=1e-12)
        assert q["thrust"] == pytest.approx(q["thrust_coefficient"] * 10e6 * q["throat_area"],
                                            rel=1e-12)


def test_the_geometry_is_the_accepted_relations_applied(stub_gateway):
    q = sized(trade()).quantities
    assert q["throat_area"] == pytest.approx(
        q["mass_flow"] * q["characteristic_velocity"] / 10e6, rel=1e-15)
    assert q["exit_area"] == pytest.approx(40.0 * q["throat_area"], rel=1e-15)
    assert q["area_ratio"] == 40.0
    assert math.pi * q["throat_diameter"] ** 2 / 4.0 == pytest.approx(q["throat_area"], rel=1e-14)
    assert math.pi * q["exit_diameter"] ** 2 / 4.0 == pytest.approx(q["exit_area"], rel=1e-14)
    assert q["exit_diameter"] / q["throat_diameter"] == pytest.approx(math.sqrt(40.0), rel=1e-14)
    assert q["oxidiser_mass_flow"] + q["fuel_mass_flow"] == pytest.approx(q["mass_flow"],
                                                                         rel=1e-14)
    r = trade().candidate(KEY).oxidiser_fuel_ratio
    assert q["oxidiser_mass_flow"] / q["fuel_mass_flow"] == pytest.approx(r, rel=1e-14)
    assert set(q) == {quantity.key for quantity in SIZING_QUANTITIES}


def test_the_trades_numbers_are_reproduced_exactly(stub_gateway):
    """At the trade's own nozzle, c*, Cf, c_eff, Isp, exit pressure and mass
    flow are the trade's numbers, bit for bit."""
    result = trade()
    recorded = result.candidate(KEY).metrics
    q = sized(result).quantities
    for key in ("characteristic_velocity", "thrust_coefficient", "effective_exhaust_velocity",
                "specific_impulse", "exit_pressure", "mass_flow", "oxidiser_mass_flow",
                "fuel_mass_flow"):
        assert q[key] == recorded[key], key


def test_a_stated_area_ratio_resizes_the_nozzle_not_the_chamber(stub_gateway):
    result = trade()
    a = sized(result)
    b = sized(result, service.SizingSettings(area_ratio=20.0))
    assert b.definition.area_ratio_source is AreaRatioSource.SIZING
    assert b.quantities["characteristic_velocity"] == a.quantities["characteristic_velocity"]
    assert b.quantities["exit_mach"] < a.quantities["exit_mach"]
    assert abs(b.quantities["thrust_closure"]) <= 1e-12


def test_a_chamber_only_trade_sizes_at_a_stated_ratio(stub_gateway):
    result = sized(trade(settings=CHAMBER_ONLY), service.SizingSettings(area_ratio=40.0))
    reference = sized(trade())
    assert result.ok and result.definition.area_ratio_source is AreaRatioSource.SIZING
    assert result.quantities == reference.quantities


def test_an_internal_shock_is_refused_not_patched(stub_gateway):
    """Ae/At 5000 at sea level from 1 MPa holds an internal shock: the ideal
    model refuses, and the refusal is the reason on every quantity."""
    result = sized(trade(settings=IDEAL.replace(chamber_pressure=1e6, area_ratio=5000.0)))
    assert result.status is SizingStatus.REFUSED and not result.ok
    assert result.quantities == {}
    assert "internal_normal_shock" in result.message
    assert all(reason == result.message for reason in result.unresolved.values())
    assert set(result.unresolved) == {q.key for q in SIZING_QUANTITIES}


def test_an_overexpanded_nozzle_keeps_its_signed_pressure_thrust(stub_gateway):
    result = sized(trade(settings=IDEAL.replace(chamber_pressure=3e6, area_ratio=40.0)))
    q = result.quantities
    assert result.ok and result.regime == "overexpanded"
    assert q["exit_pressure"] < 101325.0
    assert q["pressure_thrust"] < 0.0 and q["thrust_coefficient_pressure"] < 0.0
    assert any("below the ambient" in note for note in result.notes)
    assert abs(q["thrust_closure"]) <= 1e-12


def test_a_replay_that_does_not_reproduce_the_trade_is_refused(stub_gateway):
    point, _ = service.operating_point(trade(), stale=False)
    for key in ("chamber_temperature", "molar_mass", "characteristic_velocity",
                "specific_impulse", "mass_flow"):
        recorded = dict(point.recorded)
        recorded[key] = recorded[key] * (1.0 + 1e-12)
        definition, _ = service.build_definition(replace(point, recorded=recorded),
                                                 service.SizingSettings())
        result = service.solve_sizing(definition)
        assert result.status is SizingStatus.REFUSED, key
        assert "does not reproduce the propellant trade" in result.message


def test_a_failed_chamber_is_refused(stub_gateway, monkeypatch):
    from rocketforge.physics.thermochemistry import ProviderError

    point, _ = service.operating_point(trade(), stale=False)
    definition, _ = service.build_definition(point, service.SizingSettings())

    def failing(request):
        raise ProviderError("injected failure")

    monkeypatch.setattr(stub_gateway, "solve_chamber", failing)
    result = service.solve_sizing(definition)
    assert result.status is SizingStatus.REFUSED and "injected failure" in result.message


def test_sizing_is_deterministic_and_serialisable(stub_gateway):
    result = trade()
    a, b = sized(result), sized(result)
    assert a == b
    assert SizingResult.from_json(a.to_json()) == a
    assert a.provenance["trade"].endswith(KEY)
    assert any("Ideal" in text for text in a.assumptions)


def test_one_sizing_is_one_chamber_solve(stub_gateway):
    result = trade()
    before = len(stub_gateway.calls)
    sized(result)
    assert len(stub_gateway.calls) == before + 1


def test_display_groups_carry_units_and_reasons(stub_gateway):
    groups = service.quantity_groups(sized(trade()))
    rows = {row["key"]: row for group in groups for row in group["rows"]}
    assert rows["throat_diameter"]["unit"] == "mm" and rows["throat_area"]["unit"] == "cm²"
    assert rows["thrust"]["unit"] == "kN"
    refused = service.quantity_groups(
        sized(trade(settings=IDEAL.replace(chamber_pressure=1e6, area_ratio=5000.0))))
    assert all(row["value"] == "—" and row["reason"]
               for group in refused for row in group["rows"])


# ===========================================================================
# the controller
# ===========================================================================


@pytest.fixture()
def chain(qt_app):
    requirement = EngineRequirementController()
    requirement.set_requirement(BASE)
    trade_controller = PropellantTradeController(requirement)
    return requirement, trade_controller, ChamberSizingController(trade_controller)


def run_trade(trade_controller, key=KEY, ideal=True):
    trade_controller.setStudyPressure("10")
    trade_controller.setRatioMode("catalogue")
    if ideal:
        trade_controller.setPerformanceBasis("ideal_area_ratio")
        trade_controller.setAreaRatio("40")
    trade_controller.runTrade()
    trade_controller.run_to_completion()
    if key:
        assert trade_controller.selectCandidate(key)


def test_the_sizing_waits_for_a_selected_candidate(chain, stub_gateway):
    _, trade_controller, sizing = chain
    assert sizing.property("canSize") is False
    assert [i["code"] for i in sizing.property("issues")] == ["NO_TRADE"]
    run_trade(trade_controller, key="")
    assert [i["code"] for i in sizing.property("issues")] == ["NO_SELECTION"]
    trade_controller.selectCandidate(KEY)
    assert sizing.property("canSize") is True and sizing.property("issues") == []


def test_editing_and_browsing_solve_nothing(chain, stub_gateway):
    _, trade_controller, sizing = chain
    run_trade(trade_controller)
    calls = len(stub_gateway.calls)
    sizing.setAreaRatio("25")
    sizing.setAreaRatio("")
    for name in ("operatingRows", "issues", "canSize", "statusLabel", "groups",
                 "tradeAreaRatioText", "resultStale"):
        sizing.property(name)
    assert len(stub_gateway.calls) == calls
    assert sizing.property("hasResult") is False


def test_size_is_the_only_solve_and_marks_stale_on_change(chain, stub_gateway):
    requirement, trade_controller, sizing = chain
    run_trade(trade_controller)
    calls = len(stub_gateway.calls)
    sizing.runSizing()
    assert len(stub_gateway.calls) == calls + 1
    assert sizing.property("hasResult") and sizing.property("statusLabel") in (
        "Sized", "Sized with notes")
    assert sizing.property("resultStale") is False
    sizing.setAreaRatio("25")
    assert sizing.property("resultStale") is True
    sizing.setAreaRatio("")
    assert sizing.property("resultStale") is False                  # same question again
    trade_controller.selectCandidate("sutton-o2-h2")
    assert sizing.property("resultStale") is True                   # another candidate
    trade_controller.selectCandidate(KEY)
    assert sizing.property("resultStale") is False
    requirement.setThrust("2000")
    assert sizing.property("resultStale") is True                   # trade went stale
    assert sizing.property("canSize") is False
    assert [i["code"] for i in sizing.property("issues")] == ["TRADE_STALE"]
    assert len(stub_gateway.calls) == calls + 1                     # none of it solved


def test_a_refused_sizing_is_shown_as_refused(chain, stub_gateway):
    _, trade_controller, sizing = chain
    run_trade(trade_controller)
    sizing.setAreaRatio("5000")
    trade_controller.setStudyPressure("1")
    trade_controller.runTrade()
    trade_controller.run_to_completion()
    trade_controller.selectCandidate(KEY)
    sizing.runSizing()
    assert sizing.property("statusLabel") == "Refused"
    assert "internal_normal_shock" in sizing.property("message")


def test_no_provider_means_no_sizing(chain, stub_gateway, monkeypatch):
    _, trade_controller, sizing = chain
    run_trade(trade_controller)
    from rocketforge.application.analysis.thermochemistry_provider import ProviderAvailability

    monkeypatch.setattr(gateway_module, "_availability", ProviderAvailability(
        status="not_installed", usable=False, detail="the 'cea' distribution is not installed"))
    sizing.runSizing()
    assert sizing.property("hasResult") is False
    assert "No thermochemistry provider" in sizing.property("message")


def test_the_basis_names_every_source(chain, stub_gateway, tmp_path):
    _, trade_controller, sizing = chain
    run_trade(trade_controller)
    sizing.runSizing()
    rows = {r["label"]: r["value"] for r in sizing.property("assumptionRows")}
    assert rows["Chamber pressure"] == "10 MPa · stated in the trade"
    assert rows["Nozzle basis"] == "ideal, Ae/At 40 · the trade's nozzle"
    assert rows["Target thrust"] == "1000 kN · requirement"
    assert rows["Design ambient"] == "101.325 kPa · requirement"
    assert SizingResult.from_json(sizing.property("resultJson")) == sizing.result()
    assert sizing.saveResult(str(tmp_path / "sizing.json"))
    assert SizingResult.from_json((tmp_path / "sizing.json").read_text("utf-8")) == sizing.result()


# ===========================================================================
# parity with the production chain, under NASA CEA
# ===========================================================================


@requires_cea
@pytest.mark.parametrize("key", ["sutton-o2-ch4", "sutton-o2-h2", "sutton-nto-mmh"])
@pytest.mark.parametrize("requirement", [BASE, VACUUM], ids=["sea_level", "vacuum"])
def test_sizing_matches_the_production_chain_exactly(key, requirement):
    from rocketforge.application.analysis import performance_service as performance
    from rocketforge.application.analysis.thermochemistry_service import (
        ChamberCase,
        solve_case,
    )
    from rocketforge.engineering.chamber import ChamberGammaBasis
    from rocketforge.engineering.nozzle import PerformanceScale, PerformanceScaleMode
    from rocketforge.physics.thermochemistry import GammaStrategy

    result = trade(requirement, selected=key)
    candidate = result.candidate(key)
    sizing = sized(result)
    assert sizing.ok, sizing.message

    chamber = solve_case(ChamberCase(
        fuel=candidate.fuel, oxidiser=candidate.oxidiser,
        oxidiser_fuel_ratio=candidate.oxidiser_fuel_ratio, chamber_pressure=10e6,
        fuel_temperature=candidate.fuel_temperature,
        oxidiser_temperature=candidate.oxidiser_temperature))
    case = performance.PerformanceCase(
        gamma_strategy=GammaStrategy.CHAMBER, gamma_basis=ChamberGammaBasis.FROZEN,
        area_ratio=40.0, ambient=performance.AmbientCondition(
            performance.AmbientMode.CUSTOM, requirement.environment.ambient_pressure))
    mdot = 1.0e6 / performance.solve_performance(chamber, case).result.effective_exhaust_velocity
    by_hand = performance.solve_performance(chamber, case.replace(
        scale=PerformanceScale(PerformanceScaleMode.MASS_FLOW, mdot))).result

    q = sizing.quantities
    assert q["mass_flow"] == mdot == candidate.metrics["mass_flow"]
    assert q["throat_area"] == by_hand.throat_area
    assert q["exit_area"] == by_hand.exit_area
    assert q["specific_impulse"] == by_hand.specific_impulse
    assert q["exit_temperature"] == by_hand.exit.temperature
    assert q["thrust"] == by_hand.thrust.total
    assert abs(q["thrust_closure"]) <= 1e-12


@requires_cea
def test_a_one_meganewton_lox_methane_throat_is_the_right_size():
    """A sanity anchor a reader can check: 1 MN in vacuum from 10 MPa,
    LOX/CH4 at Sutton's O/F, Ae/At 40 -> c_eff near 3.6 km/s, so under
    300 kg/s, and At = mdot c*/pc puts the throat diameter in the 25-35 cm band."""
    q = sized(trade(VACUUM)).quantities
    assert 250.0 < q["mass_flow"] < 400.0
    assert 0.25 < q["throat_diameter"] < 0.35
