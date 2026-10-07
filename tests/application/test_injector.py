"""LIQ-6: injector hydraulics and branch feed pressure budgets.

* **Relations** (``engineering.injector``) against hand calculations from
  Sutton 9th ed. Eqs. 8-2 and 8-5, not against themselves.
* **Resolution.** Only an accepted, current LIQ-4 sizing drives a study; every
  hydraulic input of both branches must be stated.
* **Computation.** Each branch closes on LIQ-4's flows; the pair keeps O/F and
  total flow; the ledger never turns an unknown into zero.
* **Records.** Deterministic, JSON round-trip, fingerprint-checked.
* **The controller.** Only Compute computes; changes upstream make a result
  stale without computing anything.
"""

from __future__ import annotations

import ast
import json
import math
import pathlib
from dataclasses import replace

import pytest

from rocketforge.application.analysis import chamber_sizing_service as sizing_service
from rocketforge.application.analysis import injector_service as service
from rocketforge.application.analysis import propellant_trade_service as trade_service
from rocketforge.engine.injector import (
    LOSS_TERMS,
    Branch,
    DensitySource,
    HoleMode,
    InjectorResult,
    InjectorStatus,
    LossMode,
)
from rocketforge.engine.propellant_trade import PerformanceBasis
from rocketforge.engine.requirement import EngineRequirement, RequirementFormatError
from rocketforge.engineering import injector as relations
from rocketforge.engineering.injector import BudgetTerm, TermStatus, branch_budget

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = EngineRequirement(thrust=1.0e6, burn_time=200.0)
IDEAL = trade_service.TradeSettings(
    chamber_pressure=10e6, mixture_ratio_mode="catalogue",
    performance_basis=PerformanceBasis.IDEAL_AREA_RATIO, area_ratio=40.0)
KEY = "sutton-o2-ch4"
BAR = 1.0e5

OX = service.BranchSettings(pressure_drop=20 * BAR, discharge_coefficient=0.8,
                            density=1141.0)
FUEL = service.BranchSettings(pressure_drop=15 * BAR, discharge_coefficient=0.75,
                              density=422.6)


def sizing(settings=IDEAL):
    definition, issues = trade_service.build_definition(BASE, settings)
    assert definition is not None, issues
    rows = tuple(trade_service.evaluate_candidate(definition, k) for k in definition.candidates)
    trade = trade_service.assemble_result(definition, rows).with_selection(KEY)
    point, _ = sizing_service.operating_point(trade, stale=False)
    sized_definition, _ = sizing_service.build_definition(point, sizing_service.SizingSettings())
    return sizing_service.solve_sizing(sized_definition)


def study(sized, ox=OX, fuel=FUEL) -> InjectorResult:
    basis, issues = service.flow_basis(sized, stale=False)
    assert basis is not None, issues
    definition, issues = service.build_definition(basis, ox, fuel)
    assert definition is not None, issues
    return service.solve_injector(definition)


def codes(sized, ox=OX, fuel=FUEL, stale=False):
    basis, issues = service.flow_basis(sized, stale)
    if basis is None:
        return [i.code for i in issues]
    return [i.code for i in service.build_definition(basis, ox, fuel)[1]]


def losses(**modes):
    """BranchSettings loss fields: key=(mode, value)."""
    m = {key: LossMode.UNRESOLVED for key, _l, _b in LOSS_TERMS}
    v = {key: None for key, _l, _b in LOSS_TERMS}
    for key, (mode, value) in modes.items():
        m[key], v[key] = mode, value
    return {"loss_modes": m, "loss_values": v}


# ===========================================================================
# relations, against hand calculations
# ===========================================================================


def test_orifice_area_and_velocity_against_a_hand_calculation():
    # mdot 10 kg/s of water-like liquid, rho 1000, dp 10 bar, Cd 0.7:
    # A = 10 / (0.7 sqrt(2 * 1000 * 1e6)) = 10 / (0.7 * 44721.3595...) m^2
    o = relations.orifice_sizing(10.0, 1000.0, 1.0e6, 0.7).value
    assert o.flow_area == pytest.approx(10.0 / (0.7 * 44721.35954999579), rel=1e-15)
    assert o.flow_area == pytest.approx(3.194382824999699e-4, rel=1e-14)
    # v = 0.7 sqrt(2e6 / 1000) = 0.7 * 44.72135955 m/s
    assert o.injection_velocity == pytest.approx(31.304951684997057, rel=1e-15)
    assert o.volumetric_flow == 0.01 and o.effective_area == pytest.approx(0.7 * o.flow_area)
    assert abs(o.mass_flow_closure) < 1e-15 and abs(o.velocity_closure) < 1e-15


def test_bernoulli_oracle_independent_of_the_relation():
    """½ ρ (v/Cd)² = Δp: the ideal jet's dynamic pressure is the drop."""
    for rho, dp, cd in ((1141.0, 2.0e6, 0.8), (70.8, 3.0e5, 0.65), (807.0, 9.65e5, 1.0)):
        v = relations.orifice_sizing(1.0, rho, dp, cd).value.injection_velocity
        assert 0.5 * rho * (v / cd) ** 2 == pytest.approx(dp, rel=1e-14)


def test_sutton_section_8_9_example_omits_the_2_of_its_own_eq_8_2():
    """Sutton 9th ed. §8.9 (p. 337): thrust-chamber flows 10.749 kg/s LOX and
    4.387 kg/s RP-1, Δp 0.965 MPa, Cd 0.80, densities from Table 7-1 (specific
    gravity 1.14 and 0.807). It prints cumulative hole areas of 4.098 cm² and
    1.98 cm². Eq. 8-2 as printed gives areas smaller by √2: the example
    evidently computed m/(Cd √(ρΔp)). LIQ-6 follows Eqs. 8-1, 8-2 and 8-5 (and
    Bernoulli); the example's hole counts follow from its own areas."""
    ox = relations.orifice_sizing(10.749, 1140.0, 0.965e6, 0.80).value
    fuel = relations.orifice_sizing(4.387, 807.0, 0.965e6, 0.80).value
    assert ox.flow_area * 1e4 == pytest.approx(2.8645, abs=5e-4)
    assert fuel.flow_area * 1e4 == pytest.approx(1.3895, abs=5e-4)
    assert 4.098 / (ox.flow_area * 1e4) == pytest.approx(math.sqrt(2), rel=0.015)
    assert 1.98 / (fuel.flow_area * 1e4) == pytest.approx(math.sqrt(2), rel=0.015)
    # The example's own geometry: 65 oxidiser doublets of 2.00 mm holes fill its
    # 4.098 cm² (130 holes), 50 fuel doublets of 1.5 mm carry 90 % of its 1.98 cm².
    printed_ox = relations.orifice_sizing(10.749, 1140.0, 0.965e6, 0.80).value
    split = relations.holes_from_diameter(replace(printed_ox, flow_area=4.098e-4), 2.0e-3).value
    assert split.whole_hole_count == 131 and round(split.hole_count) == 130


def test_sutton_eq_8_2_forward_and_eq_8_5_close_over_a_grid():
    for mdot in (0.01, 1.0, 300.0):
        for rho in (70.8, 422.6, 1141.0, 1450.0):
            for dp in (1e4, 5e5, 3e6):
                for cd in (0.5, 0.7, 0.88, 1.0):
                    o = relations.orifice_sizing(mdot, rho, dp, cd).value
                    assert cd * o.flow_area * math.sqrt(2 * rho * dp) == pytest.approx(mdot,
                                                                                       rel=1e-14)
                    assert rho * o.injection_velocity * o.flow_area == pytest.approx(mdot,
                                                                                    rel=1e-14)
                    assert o.injection_velocity == pytest.approx(cd * math.sqrt(2 * dp / rho),
                                                                 rel=1e-15)


def test_scaling_invariants():
    base = relations.orifice_sizing(5.0, 800.0, 1e6, 0.8).value
    for k in (0.25, 2.0, 9.0):
        assert relations.orifice_sizing(5.0 * k, 800.0, 1e6, 0.8).value.flow_area == \
            pytest.approx(k * base.flow_area, rel=1e-14)            # A ~ mdot
        assert relations.orifice_sizing(5.0, 800.0, 1e6 * k, 0.8).value.flow_area == \
            pytest.approx(base.flow_area / math.sqrt(k), rel=1e-14)  # A ~ dp^-1/2
        assert relations.orifice_sizing(5.0, 800.0 * k, 1e6, 0.8).value.flow_area == \
            pytest.approx(base.flow_area / math.sqrt(k), rel=1e-14)  # A ~ rho^-1/2
        assert relations.orifice_sizing(5.0, 800.0, 1e6 * k, 0.8).value.injection_velocity == \
            pytest.approx(base.injection_velocity * math.sqrt(k), rel=1e-14)
    # v does not depend on the mass flow
    assert relations.orifice_sizing(50.0, 800.0, 1e6, 0.8).value.injection_velocity == \
        base.injection_velocity


@pytest.mark.parametrize("args, code", [
    ((0.0, 1000.0, 1e6, 0.7), "MASS_FLOW_INVALID"),
    ((math.nan, 1000.0, 1e6, 0.7), "MASS_FLOW_INVALID"),
    ((1.0, 0.0, 1e6, 0.7), "DENSITY_INVALID"),
    ((1.0, -1.0, 1e6, 0.7), "DENSITY_INVALID"),
    ((1.0, math.inf, 1e6, 0.7), "DENSITY_INVALID"),
    ((1.0, 1000.0, 0.0, 0.7), "PRESSURE_DROP_INVALID"),
    ((1.0, 1000.0, -5.0, 0.7), "PRESSURE_DROP_INVALID"),
    ((1.0, 1000.0, math.nan, 0.7), "PRESSURE_DROP_INVALID"),
    ((1.0, 1000.0, 1e6, 0.0), "DISCHARGE_COEFFICIENT_INVALID"),
    ((1.0, 1000.0, 1e6, 1.0001), "DISCHARGE_COEFFICIENT_INVALID"),
    ((1.0, 1000.0, 1e6, math.nan), "DISCHARGE_COEFFICIENT_INVALID"),
    ((1.0, 1000.0, 1e6, True), "DISCHARGE_COEFFICIENT_INVALID"),
])
def test_relations_refuse_out_of_domain_inputs(args, code):
    solution = relations.orifice_sizing(*args)
    assert solution.value is None and solution.diagnostics[0].code == code


def test_hole_count_and_diameter_close_geometrically():
    o = relations.orifice_sizing(10.0, 1000.0, 1.0e6, 0.7).value
    by_count = relations.holes_from_count(o, 24).value
    assert by_count.hole_diameter == pytest.approx(math.sqrt(4 * o.flow_area / (math.pi * 24)),
                                                   rel=1e-15)
    assert 24 * math.pi * by_count.hole_diameter ** 2 / 4 == pytest.approx(o.flow_area, rel=1e-14)
    assert by_count.whole_hole_count == 24 and abs(by_count.hole_area_closure) < 1e-14
    assert by_count.whole_hole_pressure_drop == pytest.approx(1.0e6, rel=1e-13)
    # back again: that diameter gives 24 holes
    back = relations.holes_from_diameter(o, by_count.hole_diameter).value
    assert back.hole_count == pytest.approx(24.0, rel=1e-13) and back.whole_hole_count == 24


def test_a_fractional_count_rounds_up_and_lowers_the_drop_by_eq_8_2():
    o = relations.orifice_sizing(10.0, 1000.0, 1.0e6, 0.7).value
    d = 3.0e-3
    split = relations.holes_from_diameter(o, d).value
    exact = o.flow_area / (math.pi * d * d / 4)               # 45.19... holes
    assert split.hole_count == pytest.approx(exact, rel=1e-15)
    assert split.whole_hole_count == math.ceil(exact) == 46
    a_whole = 46 * math.pi * d * d / 4
    assert split.whole_hole_flow_area == pytest.approx(a_whole, rel=1e-15)
    dp_whole = split.whole_hole_pressure_drop
    assert dp_whole == pytest.approx(1.0e6 * (o.flow_area / a_whole) ** 2, rel=1e-14)
    # the same mass flow passes the whole-hole area at that drop (Eq. 8-2)
    assert 0.7 * a_whole * math.sqrt(2 * 1000 * dp_whole) == pytest.approx(10.0, rel=1e-14)


@pytest.mark.parametrize("count", [0, -3, 2.5, True, None])
def test_hole_count_refusals(count):
    o = relations.orifice_sizing(1.0, 1000.0, 1e6, 0.7).value
    assert relations.holes_from_count(o, count).diagnostics[0].code == "HOLE_COUNT_INVALID"


@pytest.mark.parametrize("diameter", [0.0, -1e-3, math.nan, math.inf])
def test_hole_diameter_refusals(diameter):
    o = relations.orifice_sizing(1.0, 1000.0, 1e6, 0.7).value
    assert relations.holes_from_diameter(o, diameter).diagnostics[0].code \
        == "HOLE_DIAMETER_INVALID"


def test_a_hole_larger_than_the_area_is_a_warning_not_a_change():
    o = relations.orifice_sizing(0.01, 1000.0, 1e6, 0.7).value
    split = relations.holes_from_diameter(o, 0.05)
    assert split.ok and split.diagnostics[0].code == "HOLE_LARGER_THAN_REQUIRED_AREA"
    assert split.value.whole_hole_count == 1 and split.value.hole_count < 1


def test_dynamic_head_against_a_hand_calculation():
    # 20 kg/s, rho 1000, D 50 mm: v = 20 / (1000 * pi * 0.025^2) = 10.1859 m/s
    head = relations.dynamic_head(20.0, 1000.0, 0.05).value
    v = 20.0 / (1000.0 * math.pi * 0.025 ** 2)
    assert head.line_velocity == pytest.approx(v, rel=1e-15)
    assert head.dynamic_head == pytest.approx(0.5 * 1000.0 * v * v, rel=1e-15)
    assert relations.dynamic_head(20.0, 1000.0, 0.0).diagnostics[0].code \
        == "LINE_DIAMETER_INVALID"


# -- the ledger --------------------------------------------------------------


def test_complete_ledger_sums_every_term():
    terms = [BudgetTerm("p1", "p1", TermStatus.RESOLVED, 7e6),
             BudgetTerm("inj", "inj", TermStatus.RESOLVED, 1.4e6),
             BudgetTerm("line", "line", TermStatus.RESOLVED, 2e5),
             BudgetTerm("jacket", "jacket", TermStatus.NOT_APPLICABLE, reason="not a coolant"),
             BudgetTerm("margin", "margin", TermStatus.RESOLVED, 5e5)]
    budget = branch_budget(terms)
    assert budget.complete and budget.required_pressure == 9.1e6
    assert budget.minimum_known_pressure == 9.1e6 and budget.unresolved == ()


def test_an_unresolved_term_is_not_zero():
    terms = [BudgetTerm("p1", "p1", TermStatus.RESOLVED, 7e6),
             BudgetTerm("inj", "inj", TermStatus.RESOLVED, 1.4e6),
             BudgetTerm("jacket", "jacket", TermStatus.UNRESOLVED, reason="unknown")]
    budget = branch_budget(terms)
    assert not budget.complete and budget.required_pressure is None
    assert budget.minimum_known_pressure == 8.4e6 and budget.unresolved == ("jacket",)


@pytest.mark.parametrize("make", [
    lambda: BudgetTerm("x", "x", TermStatus.RESOLVED, None),
    lambda: BudgetTerm("x", "x", TermStatus.RESOLVED, -1.0),
    lambda: BudgetTerm("x", "x", TermStatus.RESOLVED, math.nan),
    lambda: BudgetTerm("x", "x", TermStatus.UNRESOLVED, 0.0, reason="r"),
    lambda: BudgetTerm("x", "x", TermStatus.UNRESOLVED),            # no reason
    lambda: branch_budget([BudgetTerm("x", "x", TermStatus.RESOLVED, 1.0)] * 2),
])
def test_ledger_refuses_malformed_terms(make):
    with pytest.raises(ValueError):
        make()


# ===========================================================================
# resolution
# ===========================================================================


def test_only_an_accepted_current_sizing_drives_a_study(stub_gateway):
    sized = sizing()
    assert codes(None) == ["NO_SIZING"]
    assert codes(sized, stale=True) == ["SIZING_STALE"]
    refused = sizing(IDEAL.replace(chamber_pressure=1e6, area_ratio=5000.0))
    assert not refused.ok and codes(refused) == ["SIZING_REFUSED"]
    incomplete = replace(sized, quantities={k: v for k, v in sized.quantities.items()
                                            if k != "fuel_mass_flow"},
                         unresolved={**sized.unresolved, "fuel_mass_flow": "x"})
    assert codes(incomplete) == ["SIZING_INCOMPLETE"]
    assert codes(sized) == []


def test_the_basis_is_liq4_verbatim(stub_gateway):
    sized = sizing()
    basis, _ = service.flow_basis(sized, stale=False)
    point = sized.definition.point
    assert basis.oxidiser_mass_flow == sized.value("oxidiser_mass_flow")
    assert basis.fuel_mass_flow == sized.value("fuel_mass_flow")
    assert basis.mass_flow == sized.value("mass_flow")
    assert basis.chamber_pressure == point.chamber_pressure
    assert basis.oxidiser_fuel_ratio == point.oxidiser_fuel_ratio
    assert basis.sizing_fingerprint == sized.definition.fingerprint
    assert (basis.oxidiser, basis.fuel) == ("LOX", "LCH4")


def test_nothing_hydraulic_is_defaulted(stub_gateway):
    sized = sizing()
    found = codes(sized, service.BranchSettings(), service.BranchSettings())
    assert found.count("PRESSURE_DROP_UNRESOLVED") == 2
    assert found.count("DISCHARGE_COEFFICIENT_UNRESOLVED") == 2
    assert found.count("DENSITY_UNRESOLVED") == 2
    assert codes(sized, replace(OX, hole_mode=HoleMode.HOLE_COUNT)) == ["HOLE_COUNT_UNRESOLVED"]
    assert codes(sized, fuel=replace(FUEL, hole_mode=HoleMode.HOLE_DIAMETER)) == \
        ["HOLE_DIAMETER_UNRESOLVED"]


@pytest.mark.parametrize("change, code", [
    ({"pressure_drop": 0.0}, "PRESSURE_DROP_INVALID"),
    ({"pressure_drop": -1.0}, "PRESSURE_DROP_INVALID"),
    ({"pressure_drop": math.inf}, "PRESSURE_DROP_INVALID"),
    ({"discharge_coefficient": 0.0}, "DISCHARGE_COEFFICIENT_INVALID"),
    ({"discharge_coefficient": 1.2}, "DISCHARGE_COEFFICIENT_INVALID"),
    ({"discharge_coefficient": math.nan}, "DISCHARGE_COEFFICIENT_INVALID"),
    ({"density": 0.0}, "DENSITY_INVALID"),
    ({"density": -5.0}, "DENSITY_INVALID"),
    ({"hole_mode": HoleMode.HOLE_COUNT, "hole_count": 0.0}, "HOLE_COUNT_INVALID"),
    ({"hole_mode": HoleMode.HOLE_COUNT, "hole_count": 7.5}, "HOLE_COUNT_INVALID"),
    ({"hole_mode": HoleMode.HOLE_DIAMETER, "hole_diameter": 0.0}, "HOLE_DIAMETER_INVALID"),
    ({"hole_mode": HoleMode.HOLE_DIAMETER, "hole_diameter": -1e-3}, "HOLE_DIAMETER_INVALID"),
])
def test_invalid_inputs_are_refused_not_clamped(stub_gateway, change, code):
    assert codes(sizing(), replace(OX, **change)) == [code]


def test_stated_terms_need_values_and_non_negative_losses(stub_gateway):
    sized = sizing()
    assert codes(sized, replace(OX, **losses(feed_line_loss=(LossMode.STATED, None)))) == \
        ["TERM_UNRESOLVED"]
    assert codes(sized, replace(OX, **losses(feed_line_loss=(LossMode.STATED, -1.0)))) == \
        ["TERM_INVALID"]
    assert codes(sized, replace(OX, **losses(dynamic_head=(LossMode.LINE_DIAMETER, 0.0)))) == \
        ["LINE_DIAMETER_INVALID"]


def test_fluid_model_only_for_validated_propellants(stub_gateway):
    sized = sizing()
    assert service.fluid_model_supported("LOX") and service.fluid_model_supported("LCH4")
    for name in ("RP-1", "N2H4", "NTO", "MMH", "UDMH", "A-50", "HTP-90", "LF2"):
        assert not service.fluid_model_supported(name), name
    model = replace(OX, density_source=DensitySource.FLUID_MODEL, density=None)
    assert codes(sized, model) == []
    basis, _ = service.flow_basis(sized, stale=False)
    unmapped = replace(basis, oxidiser="NTO")
    _, issues = service.build_definition(unmapped, model, FUEL)
    assert [i.code for i in issues] == ["DENSITY_MODEL_UNSUPPORTED"]


# ===========================================================================
# computation
# ===========================================================================


def test_each_branch_closes_on_the_liq4_flow(stub_gateway):
    sized = sizing()
    result = study(sized)
    assert result.ok and result.status is InjectorStatus.OK
    for branch, s, key in ((Branch.OXIDISER, OX, "oxidiser_mass_flow"),
                           (Branch.FUEL, FUEL, "fuel_mass_flow")):
        b = result.branch(branch)
        mdot = sized.value(key)
        assert b.value("mass_flow") == mdot
        a = mdot / (s.discharge_coefficient * math.sqrt(2 * s.density * s.pressure_drop))
        assert b.value("flow_area") == pytest.approx(a, rel=1e-15)
        assert b.value("injection_velocity") == pytest.approx(
            s.discharge_coefficient * math.sqrt(2 * s.pressure_drop / s.density), rel=1e-15)
        assert abs(b.value("mass_flow_closure")) < 1e-14
        assert abs(b.value("velocity_closure")) < 1e-14
        assert b.value("pressure_drop_ratio") == s.pressure_drop / 10e6


def test_the_pair_keeps_liq4_o_f_and_total_flow(stub_gateway):
    sized = sizing()
    result = study(sized)
    p = result.pair
    assert p["oxidiser_fuel_ratio"] == pytest.approx(
        sized.definition.point.oxidiser_fuel_ratio, rel=1e-13)
    assert abs(p["oxidiser_fuel_ratio_closure"]) < 1e-13
    assert abs(p["total_mass_flow_closure"]) < 1e-13
    assert p["total_mass_flow"] == pytest.approx(sized.value("mass_flow"), rel=1e-13)


def test_minimum_pressure_is_pc_plus_dp_when_nothing_else_is_known(stub_gateway):
    result = study(sizing())
    ox = result.oxidiser
    assert ox.value("minimum_known_pressure") == 10e6 + 20 * BAR
    assert ox.value("required_pressure") is None
    assert "unresolved" in ox.unresolved["required_pressure"].lower()
    lines = {line.key: line for line in ox.ledger}
    assert [line.key for line in ox.ledger] == [
        "chamber_pressure", "injector_pressure_drop", "feed_line_loss", "valve_loss",
        "cooling_jacket_loss", "dynamic_head", "other_loss", "margin"]
    for key in ("feed_line_loss", "valve_loss", "cooling_jacket_loss", "dynamic_head",
                "other_loss", "margin"):
        assert lines[key].status == "unresolved" and lines[key].value is None
        assert "not assumed to be zero" in lines[key].reason


def test_a_complete_ledger_gives_the_required_pressure(stub_gateway):
    fuel = replace(FUEL, **losses(
        feed_line_loss=(LossMode.STATED, 2 * BAR), valve_loss=(LossMode.STATED, 1.5 * BAR),
        cooling_jacket_loss=(LossMode.STATED, 12 * BAR),
        dynamic_head=(LossMode.LINE_DIAMETER, 0.05), other_loss=(LossMode.NOT_APPLICABLE, None),
        margin=(LossMode.STATED, 5 * BAR)))
    sized = sizing()
    result = study(sized, fuel=fuel)
    f = result.fuel
    mdot = sized.value("fuel_mass_flow")
    v = mdot / (422.6 * math.pi * 0.025 ** 2)
    head = 0.5 * 422.6 * v * v
    expected = 10e6 + 15 * BAR + 2 * BAR + 1.5 * BAR + 12 * BAR + head + 5 * BAR
    assert f.value("required_pressure") == pytest.approx(expected, rel=1e-15)
    assert f.value("minimum_known_pressure") == f.value("required_pressure")
    assert f.value("line_velocity") == pytest.approx(v, rel=1e-15)
    lines = {line.key: line for line in f.ledger}
    assert lines["other_loss"].status == "not_applicable" and lines["other_loss"].value is None
    # the oxidiser branch is independent: still incomplete
    assert result.oxidiser.value("required_pressure") is None


def test_hole_modes_through_the_service(stub_gateway):
    result = study(sizing(), replace(OX, hole_mode=HoleMode.HOLE_COUNT, hole_count=120.0),
                   replace(FUEL, hole_mode=HoleMode.HOLE_DIAMETER, hole_diameter=2.0e-3))
    ox, fu = result.oxidiser, result.fuel
    assert ox.value("hole_count") == 120.0 and ox.value("whole_hole_count") == 120.0
    assert 120 * math.pi * ox.value("hole_diameter") ** 2 / 4 == pytest.approx(
        ox.value("flow_area"), rel=1e-14)
    assert fu.value("hole_count") == pytest.approx(
        fu.value("flow_area") / (math.pi * 1e-6), rel=1e-14)
    assert fu.value("whole_hole_count") == math.ceil(fu.value("hole_count"))
    area_only = study(sizing()).oxidiser
    assert area_only.value("hole_count") is None and "total area only" in \
        area_only.unresolved["hole_count"]


def test_a_branch_without_its_fluid_model_is_refused_with_the_reason(stub_gateway, monkeypatch):
    from rocketforge.application.analysis import fluid_property_provider as gateway

    monkeypatch.setattr(gateway, "availability", lambda: gateway.FluidProviderAvailability(
        installed=False, label="CoolProp", library_version="", backend="",
        detail=gateway.NOT_INSTALLED_REMEDY))
    result = study(sizing(), replace(OX, density_source=DensitySource.FLUID_MODEL, density=None))
    assert result.status is InjectorStatus.REFUSED and not result.oxidiser.ok
    assert result.fuel.ok                                  # the other branch is independent
    assert "No validated fluid model is installed" in result.oxidiser.message
    assert result.pair == {} and not result.oxidiser.quantities


def _coolprop() -> bool:
    from rocketforge.application.analysis.fluid_property_provider import availability

    return availability().is_usable


@pytest.mark.skipif(not _coolprop(), reason="CoolProp not installed in this environment")
def test_fluid_model_density_is_at_the_stream_temperature_and_injector_inlet(stub_gateway):
    from rocketforge.application.analysis.fluid_property_provider import property_provider
    from rocketforge.engineering.propellants import PRODUCTION_FLUID_MAPPING, stream_density

    # Inlet pressures below the critical pressures of O2 (5.04 MPa) and CH4
    # (4.60 MPa): the validated bindings are for the liquid phase.
    sized = sizing(IDEAL.replace(chamber_pressure=3e6))
    ox = replace(OX, pressure_drop=10 * BAR, density_source=DensitySource.FLUID_MODEL,
                 density=None)
    fuel = replace(FUEL, pressure_drop=10 * BAR, density_source=DensitySource.FLUID_MODEL,
                   density=None)
    result = study(sized, ox, fuel)
    assert result.ok, result.message
    point = sized.definition.point
    for branch, name, temperature, dp in (
            (result.oxidiser, "LOX", point.oxidiser_temperature, ox.pressure_drop),
            (result.fuel, "LCH4", point.fuel_temperature, fuel.pressure_drop)):
        expected = stream_density(property_provider(), PRODUCTION_FLUID_MAPPING.require(name),
                                  temperature, point.chamber_pressure + dp).density
        assert branch.value("density") == expected
        assert branch.density_provenance["phase"] == "liquid"
        assert float(branch.density_provenance["pressure_Pa"]) == point.chamber_pressure + dp
    assert 1000 < result.oxidiser.value("density") < 1300       # LOX near 90 K
    assert 380 < result.fuel.value("density") < 460              # LCH4 near 111 K


@pytest.mark.skipif(not _coolprop(), reason="CoolProp not installed in this environment")
def test_above_the_critical_pressure_the_liquid_binding_refuses_rather_than_guess(stub_gateway):
    """At 10 MPa + dp, LOX at 90 K is above oxygen's critical pressure. The
    validated binding is for the liquid phase, so the density is refused and
    the branch asks for a stated one; the fuel branch is unaffected."""
    ox = replace(OX, density_source=DensitySource.FLUID_MODEL, density=None)
    result = study(sizing(), ox)
    assert not result.oxidiser.ok and result.fuel.ok
    assert "supercritical" in result.oxidiser.message
    assert "State the density instead" in result.oxidiser.message


# ===========================================================================
# records and presentation
# ===========================================================================


def test_records_round_trip_and_are_deterministic(stub_gateway):
    sized = sizing()
    full = replace(FUEL, hole_mode=HoleMode.HOLE_COUNT, hole_count=36.0, **losses(
        feed_line_loss=(LossMode.STATED, 2 * BAR), dynamic_head=(LossMode.LINE_DIAMETER, 0.04),
        cooling_jacket_loss=(LossMode.NOT_APPLICABLE, None)))
    result = study(sized, fuel=full)
    text = result.to_json()
    assert InjectorResult.from_json(text) == result
    assert study(sized, fuel=full).to_json() == text
    record = json.loads(text)
    assert record["schema"] == "rocketforge.liquid-injector" and record["version"] == 1
    branch = record["definition"]["fuel"]
    assert branch["pressure_drop_Pa"] == 15 * BAR and branch["hole_count"] == 36
    assert branch["losses"]["dynamic_head"] == {"mode": "line_diameter", "value": 0.04}
    assert record["definition"]["flow_basis"]["fuel_mass_flow_kg_s"] == \
        sized.value("fuel_mass_flow")
    assert {line["status"] for line in record["fuel"]["ledger"]} == {
        "resolved", "not_applicable", "unresolved"}
    assert "Sutton" in record["provenance"]["hydraulics"]
    assert record["provenance"]["sizing"].startswith("LIQ-4 sizing ")


def test_a_hand_edited_record_is_refused(stub_gateway):
    record = json.loads(study(sizing()).to_json())
    record["definition"]["oxidiser"]["pressure_drop_Pa"] = 1.0
    with pytest.raises(RequirementFormatError):
        InjectorResult.from_dict(record)
    with pytest.raises(RequirementFormatError):
        InjectorResult.from_json("{not json")


def test_display_units_are_converted_once(stub_gateway):
    result = study(sizing())
    groups = {g["key"]: {r["key"]: r for r in g["rows"]}
              for g in service.branch_groups(result.oxidiser)}
    assert groups["orifice"]["pressure_drop"]["value"] == "20.0000"
    assert groups["orifice"]["pressure_drop"]["unit"] == "bar"
    assert groups["orifice"]["flow_area"]["unit"] == "mm²"
    assert groups["orifice"]["flow_area"]["value"] == \
        f"{result.oxidiser.value('flow_area') * 1e6:,.4f}"
    assert groups["budget"]["required_pressure"]["value"] == "—"
    assert groups["budget"]["required_pressure"]["reason"].startswith("Not complete")
    ledger = service.ledger_rows(result.oxidiser)
    assert ledger[0]["value"] == "100.0000" and ledger[0]["unit"] == "bar"
    assert ledger[2]["value"] == "UNRESOLVED" and ledger[2]["unit"] == ""


def test_no_stability_or_feasibility_claim_in_any_text():
    forbidden = ("is stable", "stable combustion", "feasible", "Feasible", "optimal",
                 "Optimal", "recommended", "Recommended")
    texts = list(service.ASSUMPTIONS) + [q.note for q in
                                         __import__("rocketforge.engine.injector",
                                                    fromlist=["x"]).BRANCH_QUANTITIES]
    for text in texts:
        for word in forbidden:
            assert word not in text, (word, text)


# ===========================================================================
# boundaries
# ===========================================================================


def test_layers_and_no_provider_outside_compute():
    """The engineering package reaches nothing above it; the service reaches
    the fluid provider only inside the density step of solve_injector."""
    package = ROOT / "rocketforge" / "engineering" / "injector"
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                assert node.module.startswith(("rocketforge.core", "__future__",
                                               "dataclasses", "collections", "enum",
                                               "math", "typing")), (path.name, node.module)
    source = (ROOT / "rocketforge/application/analysis/injector_service.py").read_text(
        encoding="utf-8")
    tree = ast.parse(source)
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        body = ast.unparse(fn)
        if "fluid_property_provider" in body or "thermochemistry" in body:
            assert fn.name == "_density", fn.name
    assert "thermochemistry_provider" not in source


def test_the_engine_record_module_imports_no_relation():
    source = (ROOT / "rocketforge/engine/injector.py").read_text(encoding="utf-8")
    assert "engineering" not in "".join(
        line for line in source.splitlines() if line.startswith(("import", "from")))
