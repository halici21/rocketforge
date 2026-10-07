"""LIQ-5: the chamber geometry upstream of an accepted LIQ-4 throat.

* **Resolution.** Only an accepted, current LIQ-4 sizing is a throat basis, and
  a geometry needs L*, Ac/At and the half-angle all stated.
* **Computation.** The throat is LIQ-4's bit for bit; Vc = L* At closes; a
  refusal carries its reason everywhere.
* **Presentation.** Unit conversion happens once, in the service.
* **The controller.** Only Compute computes; changes upstream make a result
  stale without computing anything.
"""

from __future__ import annotations

import ast
import math
import pathlib
from dataclasses import replace

import pytest

from rocketforge.application.analysis import chamber_geometry_service as service
from rocketforge.application.analysis import chamber_sizing_service as sizing_service
from rocketforge.application.analysis import propellant_trade_service as trade_service
from rocketforge.application.analysis.chamber_geometry_controller import (
    ChamberGeometryController,
)
from rocketforge.application.analysis.chamber_sizing_controller import (
    ChamberSizingController,
)
from rocketforge.application.analysis.engine_requirement_controller import (
    EngineRequirementController,
)
from rocketforge.application.analysis.propellant_trade_controller import (
    PropellantTradeController,
)
from rocketforge.engine.chamber_geometry import (
    GEOMETRY_QUANTITIES,
    GeometryResult,
    GeometryStatus,
)
from rocketforge.engine.propellant_trade import PerformanceBasis
from rocketforge.engine.requirement import EngineRequirement
import rocketforge.engineering.chamber_geometry as chamber_package

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = EngineRequirement(thrust=1.0e6, burn_time=200.0)
IDEAL = trade_service.TradeSettings(
    chamber_pressure=10e6, mixture_ratio_mode="catalogue",
    performance_basis=PerformanceBasis.IDEAL_AREA_RATIO, area_ratio=40.0)
KEY = "sutton-o2-ch4"
STATED = service.GeometrySettings(characteristic_length=1.0, contraction_ratio=3.0,
                                  converging_half_angle_deg=25.0)


def sizing(settings=IDEAL, sizing_settings=sizing_service.SizingSettings()):
    definition, issues = trade_service.build_definition(BASE, settings)
    assert definition is not None, issues
    rows = tuple(trade_service.evaluate_candidate(definition, k) for k in definition.candidates)
    trade = trade_service.assemble_result(definition, rows).with_selection(KEY)
    point, _ = sizing_service.operating_point(trade, stale=False)
    sized_definition, _ = sizing_service.build_definition(point, sizing_settings)
    return sizing_service.solve_sizing(sized_definition)


def geometry(sized, settings=STATED):
    basis, issues = service.throat_basis(sized, stale=False)
    assert basis is not None, issues
    definition, issues = service.build_definition(basis, settings)
    assert definition is not None, issues
    return service.solve_geometry(definition)


def codes(sized, stale=False, settings=STATED):
    basis, issues = service.throat_basis(sized, stale)
    if basis is None:
        return [i.code for i in issues]
    return [i.code for i in service.build_definition(basis, settings)[1]]


# ===========================================================================
# resolution
# ===========================================================================


def test_only_an_accepted_current_sizing_is_a_throat(stub_gateway):
    sized = sizing()
    assert codes(None) == ["NO_SIZING"]
    assert codes(sized, stale=True) == ["SIZING_STALE"]
    refused = sizing(IDEAL.replace(chamber_pressure=1e6, area_ratio=5000.0))
    assert not refused.ok and codes(refused) == ["SIZING_REFUSED"]
    hollow = replace(sized, quantities={k: v for k, v in sized.quantities.items()
                                        if k not in ("throat_area", "throat_diameter")})
    assert codes(hollow) == ["SIZING_INCOMPLETE"]
    assert codes(sized) == []


def test_the_throat_is_liq4s_verbatim(stub_gateway):
    sized = sizing()
    basis, _ = service.throat_basis(sized, stale=False)
    assert basis.throat_area == sized.quantities["throat_area"]
    assert basis.throat_diameter == sized.quantities["throat_diameter"]
    assert basis.sizing_fingerprint == sized.definition.fingerprint
    assert basis.trade_fingerprint == sized.definition.point.trade_fingerprint
    assert basis.area_ratio == sized.definition.area_ratio == 40.0
    assert basis.sizing_provenance == dict(sized.provenance)
    assert basis.sizing_status == sized.status.value


def test_every_input_is_stated_never_assumed(stub_gateway):
    sized = sizing()
    assert codes(sized, settings=service.GeometrySettings()) == [
        "CHARACTERISTIC_LENGTH_UNRESOLVED", "CONTRACTION_RATIO_UNRESOLVED",
        "CONVERGING_HALF_ANGLE_UNRESOLVED"]
    assert codes(sized, settings=replace(STATED, characteristic_length=0.0)) == [
        "CHARACTERISTIC_LENGTH_INVALID"]
    assert codes(sized, settings=replace(STATED, contraction_ratio=1.0)) == [
        "CONTRACTION_RATIO_INVALID"]
    for angle in (0.0, 90.0, -5.0):
        assert codes(sized, settings=replace(STATED, converging_half_angle_deg=angle)) == [
            "CONVERGING_HALF_ANGLE_INVALID"]
    assert codes(sized, settings=replace(STATED, characteristic_length=math.inf)) == [
        "CHARACTERISTIC_LENGTH_INVALID"]


@pytest.mark.parametrize("name,values", [
    ("characteristic_length", [-1.0, 0.0, 5e-324, 1e-300, 0.5, math.inf, math.nan]),
    ("contraction_ratio", [0.0, 1.0, 1.0 + 2.2e-16, 1.0000001, 3.0, math.inf]),
    ("converging_half_angle_deg", [-1.0, 0.0, 1e-300, 1e-9, 45.0, 89.99999999999999,
                                   90.0, 90.0000001, math.nan]),
])
def test_the_service_and_the_relations_agree_on_every_domain_boundary(name, values):
    """The page flags an invalid input before Compute; the relation guards it
    again. The two must never disagree, in degrees or radians."""
    import rocketforge.engineering.chamber_geometry as relations

    basis = service.ThroatBasis(
        sizing_fingerprint="a" * 64, sizing_status="ok", sizing_provenance={},
        trade_fingerprint="b" * 64, pair_key="k", pair_label="k", chamber_pressure=1e7,
        thrust=1e6, area_ratio=40.0, throat_area=0.01, throat_diameter=math.sqrt(0.04 / math.pi))
    for value in values:
        settings = replace(STATED, **{"characteristic_length": 100.0, name: value})
        definition, issues = service.build_definition(basis, settings)
        solution = relations.cylindrical_conical_chamber(
            0.01, settings.characteristic_length, settings.contraction_ratio,
            math.radians(settings.converging_half_angle_deg))
        relation_invalid = any(d.code.endswith("_INVALID") for d in solution.diagnostics)
        assert (definition is None) == relation_invalid, (name, value, issues)


def test_no_cycle_feed_or_later_stage_is_read():
    for name in ("chamber_geometry_service.py", "chamber_geometry_controller.py"):
        code = ast.unparse(ast.parse(
            (ROOT / "rocketforge" / "application" / "analysis" / name).read_text("utf-8")))
        assert ".cycle" not in code and ".feed" not in code, name
        assert "thermochemistry_provider" not in code, name     # no provider is reached
    source = (ROOT / "rocketforge" / "engineering" / "chamber_geometry" / "relations.py").read_text("utf-8")
    for word in ("orifice", "atomi", "wall_thickness", "heat_flux", "coolant", "pump"):
        assert word not in source


# ===========================================================================
# computation
# ===========================================================================


def test_the_chamber_closes_on_l_star_from_the_liq4_throat(stub_gateway):
    sized = sizing()
    result = geometry(sized)
    q = result.quantities
    at = sized.quantities["throat_area"]
    assert result.status is GeometryStatus.OK and set(q) == {g.key for g in GEOMETRY_QUANTITIES}
    assert q["throat_area"] == at and q["throat_diameter"] == sized.quantities["throat_diameter"]
    assert q["chamber_volume"] == pytest.approx(1.0 * at, rel=1e-15)
    assert q["chamber_area"] == pytest.approx(3.0 * at, rel=1e-15)
    assert math.pi * q["chamber_diameter"] ** 2 / 4.0 == pytest.approx(q["chamber_area"],
                                                                      rel=1e-14)
    assert q["chamber_diameter"] / q["throat_diameter"] == pytest.approx(math.sqrt(3.0),
                                                                         rel=1e-13)
    assert q["cylinder_volume"] + q["converging_volume"] == pytest.approx(
        q["chamber_volume"], rel=1e-14)
    assert q["injector_to_throat_length"] == pytest.approx(
        q["cylinder_length"] + q["converging_length"], rel=1e-15)
    assert abs(q["characteristic_length_closure"]) < 1e-13
    assert abs(q["contraction_closure"]) < 1e-13
    assert q["converging_volume_fraction"] == pytest.approx(
        q["converging_volume"] / q["chamber_volume"], rel=1e-15)
    assert (q["characteristic_length"], q["contraction_ratio"],
            q["converging_half_angle"]) == (1.0, 3.0, math.radians(25.0))


def test_a_geometry_the_convergent_cannot_fit_is_refused(stub_gateway):
    result = geometry(sizing(), replace(STATED, characteristic_length=0.2))
    assert result.status is GeometryStatus.REFUSED and not result.ok
    assert result.quantities == {}
    assert "smallest L*" in result.message and "No input is changed" in result.message
    at = result.definition.basis.throat_area
    assert f"allows {at * 0.2 * 1e6:,.1f} cm³" in result.message      # page units, not m³
    assert "m³" not in result.message.replace("cm³", "")
    assert set(result.unresolved) == {q.key for q in GEOMETRY_QUANTITIES}
    assert all(reason == result.message for reason in result.unresolved.values())
    assert service.profile(result) == []
    assert all(row["value"] == "—" and row["reason"]
               for group in service.quantity_groups(result) for row in group["rows"])


def test_advisories_are_kept_as_notes(stub_gateway):
    result = geometry(sizing(), replace(STATED, contraction_ratio=2.0, characteristic_length=5.0))
    assert result.status is GeometryStatus.WARNING and result.ok
    assert any("three times the throat area" in n for n in result.notes)
    assert any("not a validity limit" in n for n in result.notes)
    assert any("does not establish combustion completeness" in a for a in result.assumptions)


def test_deterministic_and_serialisable(stub_gateway):
    sized = sizing()
    a, b = geometry(sized), geometry(sized)
    assert a == b and a.to_json() == b.to_json()
    assert GeometryResult.from_json(a.to_json()) == a
    assert a.provenance["sizing"].startswith(f"LIQ-4 sizing {sized.definition.fingerprint[:12]}")
    assert "8-9" in a.provenance["source"]


# ===========================================================================
# presentation
# ===========================================================================


def test_units_convert_once_and_correctly():
    assert service.display_value("chamber_volume", 0.0123456) == "12,345.6"            # cm³
    assert service.display_value("converging_volume", 1.0e-6) == "1.0"
    assert service.display_value("chamber_area", 0.0123456) == "123.46"                # cm²
    assert service.display_value("throat_area", 0.0676281) == "676.281"
    assert service.display_value("chamber_diameter", 0.2541261) == "254.13"            # mm
    assert service.display_value("injector_to_throat_length", 1.2345678) == "1,234.57"
    assert service.display_value("characteristic_length", 1.1) == "1.1000"             # m
    for angle in (0.5, 15.0, 25.0, 30.0, 45.0, 60.0, 89.0):                          # rad -> deg
        assert service.display_value("converging_half_angle", math.radians(angle)) == f"{angle:g}"
    assert service.display_value("converging_volume_fraction", 0.4401) == "44.01"      # %
    assert service.display_value("characteristic_length_closure", -1.1e-16) == "-1.1e-16"
    assert service.display_value("chamber_volume", None) == "—"
    units = {k: u for k, (u, _s, _f) in service.DISPLAY.items()}
    assert set(units) == {q.key for q in GEOMETRY_QUANTITIES}
    assert units["chamber_volume"] == "cm³" and units["cylinder_length"] == "mm"


def test_the_profile_is_the_results_own_numbers(stub_gateway):
    q = geometry(sizing()).quantities
    points = service.profile(geometry(sizing()))
    assert [p["x"] for p in points] == [0.0, 0.0, q["cylinder_length"] * 1e3,
                                        q["injector_to_throat_length"] * 1e3]
    assert points[1]["r"] == points[2]["r"] == pytest.approx(q["chamber_diameter"] * 500.0)
    assert points[3]["r"] == pytest.approx(q["throat_diameter"] * 500.0)


# ===========================================================================
# the controller
# ===========================================================================


@pytest.fixture()
def chain(qt_app):
    requirement = EngineRequirementController()
    requirement.set_requirement(BASE)
    trade = PropellantTradeController(requirement)
    sizer = ChamberSizingController(trade)
    return requirement, trade, sizer, ChamberGeometryController(sizer)


@pytest.fixture()
def counted(monkeypatch):
    """Counts calls to the one geometry relation the service uses."""
    calls = []
    original = chamber_package.cylindrical_conical_chamber

    def counting(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(chamber_package, "cylindrical_conical_chamber", counting)
    return calls


def size(trade, sizer, key=KEY):
    trade.setStudyPressure("10")
    trade.setRatioMode("catalogue")
    trade.setPerformanceBasis("ideal_area_ratio")
    trade.setAreaRatio("40")
    trade.runTrade()
    trade.run_to_completion()
    assert trade.selectCandidate(key)
    sizer.runSizing()
    assert sizer.property("resultOk")


def state(geo):
    geo.setCharacteristicLength("1")
    geo.setContractionRatio("3")
    geo.setHalfAngle("25")


def test_the_geometry_waits_for_an_accepted_sizing(chain, stub_gateway):
    _, trade, sizer, geo = chain
    state(geo)
    assert [i["code"] for i in geo.property("issues")] == ["NO_SIZING"]
    assert geo.property("canCompute") is False and geo.property("hasThroat") is False
    size(trade, sizer)
    assert geo.property("issues") == [] and geo.property("canCompute") is True
    rows = {r["label"]: r["value"] for r in geo.property("basisRows")}
    assert rows["Throat area At"].endswith("cm² · sizing")
    assert rows["Nozzle"] == "Ae/At 40 · sizing"


def test_editing_and_browsing_compute_nothing(chain, stub_gateway, counted):
    _, trade, sizer, geo = chain
    size(trade, sizer)
    provider_calls = len(stub_gateway.calls)
    for text in ("1", "", "abc", "2.5"):
        geo.setCharacteristicLength(text)
    geo.setContractionRatio("3")
    geo.setHalfAngle("25")
    for name in ("basisRows", "issues", "canCompute", "statusLabel", "groups", "profile",
                 "resultStale", "hasThroat", "characteristicLengthText"):
        geo.property(name)
    assert counted == [] and len(stub_gateway.calls) == provider_calls
    assert geo.property("hasResult") is False
    assert geo.property("characteristicLengthText") == "2.5"         # "abc" was ignored


def test_compute_is_the_only_computation_and_staleness_follows_upstream(
        chain, stub_gateway, counted):
    requirement, trade, sizer, geo = chain
    size(trade, sizer)
    state(geo)
    provider_calls = len(stub_gateway.calls)
    geo.computeGeometry()
    assert len(counted) == 1 and len(stub_gateway.calls) == provider_calls
    assert geo.property("statusLabel") == "Computed" and geo.property("resultStale") is False
    assert len(geo.property("profile")) == 4

    geo.setCharacteristicLength("1.2")
    assert geo.property("resultStale") is True
    geo.setCharacteristicLength("1")
    assert geo.property("resultStale") is False                     # the same question again

    sizer.setAreaRatio("25")                                        # LIQ-4 result now stale
    assert geo.property("resultStale") is True
    assert [i["code"] for i in geo.property("issues")] == ["SIZING_STALE"]
    sizer.setAreaRatio("")
    assert geo.property("resultStale") is False

    trade.selectCandidate("sutton-o2-h2")                           # another operating point
    assert geo.property("resultStale") is True and geo.property("canCompute") is False
    trade.selectCandidate(KEY)
    assert geo.property("resultStale") is False

    requirement.setThrust("2000")                                   # trade, then sizing, stale
    assert geo.property("resultStale") is True
    assert geo.property("statusLabel").startswith("Stale")
    assert len(counted) == 1                                        # none of it computed


def test_resizing_the_same_question_keeps_the_geometry_current(chain, stub_gateway):
    _, trade, sizer, geo = chain
    size(trade, sizer)
    state(geo)
    geo.computeGeometry()
    sizer.runSizing()                                               # same question, same throat
    assert geo.property("resultStale") is False
    sizer.setAreaRatio("25")
    sizer.runSizing()                                               # a new sizing
    assert geo.property("resultStale") is True and geo.property("canCompute") is True


def test_a_refused_geometry_is_shown_as_refused(chain, stub_gateway):
    _, trade, sizer, geo = chain
    size(trade, sizer)
    state(geo)
    geo.setCharacteristicLength("0.2")
    geo.computeGeometry()
    assert geo.property("statusLabel") == "Refused" and geo.property("resultOk") is False
    assert "smallest L*" in geo.property("message")
    assert geo.property("profile") == []


def test_compute_without_a_definition_says_why(chain, stub_gateway, counted):
    _, trade, sizer, geo = chain
    size(trade, sizer)
    geo.computeGeometry()
    assert counted == [] and geo.property("hasResult") is False
    assert "L*" in geo.property("message")


def test_the_record_saves_and_reloads(chain, stub_gateway, tmp_path):
    _, trade, sizer, geo = chain
    size(trade, sizer)
    state(geo)
    geo.computeGeometry()
    assert GeometryResult.from_json(geo.property("resultJson")) == geo.result()
    target = tmp_path / "geometry.json"
    assert geo.saveResult(str(target))
    assert GeometryResult.from_json(target.read_text("utf-8")) == geo.result()
    assert geo.saveResult(str(tmp_path / "missing" / "x.json")) is False
    assert geo.property("message").startswith("Not saved")
