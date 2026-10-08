"""SYS-1: propellant inventory.

* **Relations** (``engineering.propulsion_system.inventory``) against hand
  calculations and Sutton 9th ed. §6.2 / §11.1, not against themselves.
* **Resolution.** Only an accepted, current LIQ-4 sizing and the trade it
  extends drive an inventory, with the requirement's burn time.
* **Computation.** mdot × t closes exactly; the expulsion efficiency inverts;
  residual and branch/total masses are conserved; unresolved is never zero.
* **Records.** Deterministic, JSON round-trip, fingerprint-checked.
* **The controller.** Only Compute computes; an upstream change makes a result
  stale without computing anything.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
from dataclasses import replace

import pytest

from rocketforge.application.analysis import chamber_sizing_service as sizing_service
from rocketforge.application.analysis import propellant_inventory_service as service
from rocketforge.application.analysis import propellant_trade_service as trade_service
from rocketforge.engine.propellant_trade import PerformanceBasis
from rocketforge.engine.propulsion_system.inventory import (
    ALLOWANCE_TERMS,
    INVENTORY_SCHEMA,
    ReserveMode,
    ResidualMode,
    TermMode,
)
from rocketforge.engine.propulsion_system.records import Branch, StudyResult, StudyStatus
from rocketforge.engine.requirement import EngineRequirement, RequirementFormatError
from rocketforge.engineering.propulsion_system import inventory as rel

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = EngineRequirement(thrust=1.0e6, burn_time=200.0)
IDEAL = trade_service.TradeSettings(
    chamber_pressure=10e6, mixture_ratio_mode="catalogue",
    performance_basis=PerformanceBasis.IDEAL_AREA_RATIO, area_ratio=40.0)
KEY = "sutton-o2-ch4"
NA = {key: TermMode.NOT_APPLICABLE for key, _l, _b in ALLOWANCE_TERMS}
NONE = {key: None for key, _l, _b in ALLOWANCE_TERMS}

#: A complete branch: eta 0.98, reserve 2 % of usable, no allowances, no boil-off.
COMPLETE = service.BranchSettings(
    residual_mode=ResidualMode.EXPULSION_EFFICIENCY, expulsion_efficiency=0.98,
    reserve_mode=ReserveMode.STATED_FRACTION, reserve_value=0.02,
    allowance_modes=dict(NA), allowance_values=dict(NONE),
    boiloff_mode=TermMode.NOT_APPLICABLE)


def chain(requirement=BASE):
    definition, issues = trade_service.build_definition(requirement, IDEAL)
    assert definition is not None, issues
    rows = tuple(trade_service.evaluate_candidate(definition, k) for k in definition.candidates)
    trade = trade_service.assemble_result(definition, rows).with_selection(KEY)
    point, _ = sizing_service.operating_point(trade, stale=False)
    sized_definition, _ = sizing_service.build_definition(point, sizing_service.SizingSettings())
    return sizing_service.solve_sizing(sized_definition), trade


def inventory(ox=COMPLETE, fuel=COMPLETE, requirement=BASE) -> StudyResult:
    sized, trade = chain(requirement)
    basis, issues = service.inventory_basis(sized, False, trade, False)
    assert basis is not None, issues
    definition, issues = service.build_definition(basis, ox, fuel)
    assert definition is not None, issues
    return service.solve_inventory(definition)


def term(key, status, value=None):
    return rel.MassTerm(key, key, status, value)


R, NAP, U = rel.TermStatus.RESOLVED, rel.TermStatus.NOT_APPLICABLE, rel.TermStatus.UNRESOLVED


# ===========================================================================
# relations, against hand calculations
# ===========================================================================


def test_usable_is_mass_flow_times_burn_time_exactly():
    assert rel.usable_mass(12.5, 80.0) == 1000.0
    assert rel.usable_mass(321.7946324969412, 200.0) == 321.7946324969412 * 200.0


@pytest.mark.parametrize("mdot,t", [(0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (math.nan, 1.0),
                                    (1.0, math.inf), (True, 1.0)])
def test_usable_refuses_invalid_flows_and_times(mdot, t):
    with pytest.raises(ValueError):
        rel.usable_mass(mdot, t)


def test_expulsion_efficiency_inverts_exactly():
    # 980 kg must be expellable at eta 0.98: 1000 kg present, 20 kg residual.
    present = rel.present_from_expulsion_efficiency(980.0, 0.98)
    assert present == pytest.approx(1000.0, rel=1e-15)
    assert rel.expulsion_efficiency_from_residual(980.0, present - 980.0) == pytest.approx(
        0.98, rel=1e-15)
    for available, eta in itertools.product((1.0, 37.5, 6.4e4), (0.5, 0.9, 0.97, 0.997, 1.0)):
        p = rel.present_from_expulsion_efficiency(available, eta)
        assert rel.expulsion_efficiency_from_residual(available, p - available) == \
            pytest.approx(eta, rel=1e-14)


@pytest.mark.parametrize("eta", [0.0, -0.1, 1.0000001, math.nan, math.inf])
def test_invalid_expulsion_efficiency_is_refused(eta):
    with pytest.raises(ValueError):
        rel.present_from_expulsion_efficiency(10.0, eta)
    solution = rel.branch_inventory(1.0, 1.0, [], rel.ResidualMode.EXPULSION_EFFICIENCY, eta,
                                    [], term("boiloff", NAP))
    assert solution.value is None
    assert solution.diagnostics[0].code == "EXPULSION_EFFICIENCY_INVALID"


def test_sutton_example_11_1_budget_form():
    """Sutton 9th ed. Example 11-1 (p. 403): m = mdot t (1.00 + 0.01 + 0.06) for
    a 1 % residual and a 6 % reserve. As stated masses: residual 1 % and
    reserve 6 % of mdot t give exactly 1.07 mdot t."""
    mdot, t = 14.0, 150.0
    nominal = mdot * t
    solution = rel.branch_inventory(
        mdot, t, [term("reserve", R, 0.06 * nominal)], rel.ResidualMode.RESIDUAL_MASS, None,
        [term("tank", R, 0.01 * nominal), term("line", NAP)], term("boiloff", NAP))
    inv = solution.value
    assert inv.loaded == pytest.approx(1.07 * nominal, rel=1e-15)
    assert inv.residual == pytest.approx(0.01 * nominal, rel=1e-15)
    # eta follows from the definition: available / present.
    assert inv.expulsion_efficiency == pytest.approx(1.06 / 1.07, rel=1e-15)


def test_residual_and_balance_close_over_a_grid():
    for mdot, t, eta, reserve, chill, boil in itertools.product(
            (0.25, 3.0, 321.79), (1.0, 47.5, 600.0), (0.9, 0.98, 1.0), (0.0, 12.0),
            (0.0, 5.5), (0.0, 33.0)):
        inv = rel.branch_inventory(
            mdot, t, [term("chill", R, chill), term("reserve", R, reserve)],
            rel.ResidualMode.EXPULSION_EFFICIENCY, eta, [], term("boiloff", R, boil)).value
        usable = mdot * t
        available = usable + chill + reserve
        assert inv.available == pytest.approx(available, rel=1e-15)
        assert inv.present == pytest.approx(available / eta, rel=1e-15)
        assert inv.residual == pytest.approx(available / eta - available, rel=1e-12, abs=1e-12)
        assert inv.loaded == pytest.approx(available / eta + boil, rel=1e-15)
        assert abs(inv.balance_closure) < 5e-16 and abs(inv.efficiency_closure) < 5e-16
        assert inv.minimum_known_loaded == pytest.approx(inv.loaded, rel=1e-15)


def test_an_unresolved_term_is_never_zero():
    inv = rel.branch_inventory(10.0, 10.0, [term("start_stop", U), term("reserve", R, 5.0)],
                               rel.ResidualMode.EXPULSION_EFFICIENCY, 0.95, [],
                               term("boiloff", NAP)).value
    assert inv.available is None and inv.loaded is None and inv.residual is None
    assert inv.unresolved == ("start_stop",)
    # The minimum known load is the known available at eta: a lower bound.
    assert inv.minimum_known_loaded == pytest.approx(105.0 / 0.95, rel=1e-15)
    inv = rel.branch_inventory(10.0, 10.0, [], rel.ResidualMode.UNRESOLVED, None, [],
                               term("boiloff", U)).value
    assert inv.loaded is None and inv.unresolved == ("residual", "boiloff")
    assert inv.minimum_known_loaded == 100.0


def test_boiloff_is_not_divided_by_the_expulsion_efficiency():
    inv = rel.branch_inventory(1.0, 100.0, [], rel.ResidualMode.EXPULSION_EFFICIENCY, 0.8, [],
                               term("boiloff", R, 10.0)).value
    assert inv.present == pytest.approx(125.0) and inv.loaded == pytest.approx(135.0)


def test_malformed_terms_raise():
    with pytest.raises(ValueError):
        rel.MassTerm("a", "a", R, -1.0)
    with pytest.raises(ValueError):
        rel.MassTerm("a", "a", U, 1.0)
    with pytest.raises(ValueError):
        rel.MassTerm("a", "a", R, math.nan)
    with pytest.raises(ValueError):       # duplicate keys
        rel.branch_inventory(1.0, 1.0, [term("x", NAP), term("x", NAP)],
                             rel.ResidualMode.UNRESOLVED, None, [], term("b", NAP))


# ===========================================================================
# resolution
# ===========================================================================


def test_only_an_accepted_current_sizing_and_its_trade_drive_an_inventory(stub_gateway):
    sized, trade = chain()

    def code(*args):
        basis, issues = service.inventory_basis(*args)
        return basis, [i.code for i in issues]

    assert code(None, False, trade, False)[1] == ["NO_SIZING"]
    assert code(sized, True, trade, False)[1] == ["SIZING_STALE"]
    assert code(sized, False, trade, True)[1] == ["TRADE_MISMATCH"]
    assert code(sized, False, None, False)[1] == ["TRADE_MISMATCH"]
    _other_sized, other_trade = chain(EngineRequirement(thrust=2.0e6, burn_time=200.0))
    assert code(sized, False, other_trade, False)[1] == ["TRADE_MISMATCH"]
    basis, issues = code(sized, False, trade, False)
    assert basis is not None and issues == []


def test_a_requirement_without_burn_time_never_reaches_an_inventory(stub_gateway):
    """No burn time is assumed: LIQ-3 already refuses such a requirement, so
    no sizing, and so no inventory basis, can exist for it."""
    definition, issues = trade_service.build_definition(
        EngineRequirement(thrust=1.0e6, burn_time=None), IDEAL)
    assert definition is None and [i.field for i in issues] == ["burn_time"]


def test_the_basis_is_upstream_verbatim(stub_gateway):
    sized, trade = chain()
    basis, _ = service.inventory_basis(sized, False, trade, False)
    assert basis.sizing.gate == "LIQ-4"
    assert basis.sizing.fingerprint == sized.definition.fingerprint
    assert basis.oxidiser_mass_flow == sized.value("oxidiser_mass_flow")
    assert basis.fuel_mass_flow == sized.value("fuel_mass_flow")
    assert basis.mass_flow == sized.value("mass_flow")
    assert basis.burn_time == 200.0
    assert basis.requirement_fingerprint == trade.definition.requirement.fingerprint


def test_nothing_is_defaulted(stub_gateway):
    default = service.BranchSettings()
    assert default.residual_mode is ResidualMode.UNRESOLVED
    assert default.reserve_mode is ReserveMode.UNRESOLVED
    assert default.boiloff_mode is TermMode.UNRESOLVED
    assert all(m is TermMode.UNRESOLVED for m in default.allowance_modes.values())
    # An all-unresolved inventory still computes: usable, and the minimum known load.
    result = inventory(service.BranchSettings(), service.BranchSettings())
    assert result.status is StudyStatus.INCOMPLETE
    ox = result.oxidiser
    assert ox.value("loaded_mass") is None and "loaded_mass" in ox.unresolved
    assert ox.value("minimum_known_loaded") == ox.value("usable_mass")
    assert [line.status for line in ox.ledger][1:] == ["unresolved"] * 6


@pytest.mark.parametrize("change,code", [
    ({"expulsion_efficiency": None}, "EXPULSION_EFFICIENCY_UNRESOLVED"),
    ({"expulsion_efficiency": 0.0}, "EXPULSION_EFFICIENCY_INVALID"),
    ({"expulsion_efficiency": 1.2}, "EXPULSION_EFFICIENCY_INVALID"),
    ({"expulsion_efficiency": math.nan}, "EXPULSION_EFFICIENCY_INVALID"),
    ({"reserve_value": None}, "RESERVE_UNRESOLVED"),
    ({"reserve_value": -0.01}, "RESERVE_INVALID"),
    ({"boiloff_mode": TermMode.STATED, "boiloff": None}, "TERM_UNRESOLVED"),
    ({"boiloff_mode": TermMode.STATED, "boiloff": -5.0}, "TERM_INVALID"),
    ({"boiloff_mode": TermMode.STATED, "boiloff": math.inf}, "TERM_INVALID"),
])
def test_invalid_inputs_are_refused_not_clamped(stub_gateway, change, code):
    sized, trade = chain()
    basis, _ = service.inventory_basis(sized, False, trade, False)
    definition, issues = service.build_definition(basis, replace(COMPLETE, **change), COMPLETE)
    assert definition is None and [i.code for i in issues] == [code]


# ===========================================================================
# computation
# ===========================================================================


def test_each_branch_closes_on_mdot_times_burn_time(stub_gateway):
    result = inventory()
    basis = result.definition.basis
    for branch in Branch:
        b = result.branch(branch)
        usable = basis.mass_flow_of(branch) * 200.0
        assert b.value("usable_mass") == usable
        available = usable * 1.02
        assert b.value("available_mass") == pytest.approx(available, rel=1e-15)
        assert b.value("loaded_mass") == pytest.approx(available / 0.98, rel=1e-15)
        assert b.value("residual_mass") == pytest.approx(available / 0.98 - available, rel=1e-13)
        assert abs(b.value("balance_closure")) < 5e-16
        assert abs(b.value("efficiency_closure")) < 5e-16
    t = result.totals
    assert t["usable_total"] == pytest.approx(basis.mass_flow * 200.0, rel=1e-15)
    assert abs(t["usable_ratio_closure"]) < 1e-15 and abs(t["usable_total_closure"]) < 1e-15
    assert t["loaded_total"] == pytest.approx(
        result.oxidiser.value("loaded_mass") + result.fuel.value("loaded_mass"), rel=1e-15)
    assert result.status is StudyStatus.OK


def test_branches_stay_distinct_and_budgets_may_differ(stub_gateway):
    fuel = replace(COMPLETE, residual_mode=ResidualMode.RESIDUAL_MASS, expulsion_efficiency=None,
                   tank_residual_mode=TermMode.STATED, tank_residual=150.0,
                   trapped_line_mode=TermMode.STATED, trapped_line=25.0,
                   reserve_mode=ReserveMode.STATED_MASS, reserve_value=300.0,
                   boiloff_mode=TermMode.STATED, boiloff=40.0)
    result = inventory(COMPLETE, fuel)
    f = result.fuel
    usable = f.value("usable_mass")
    assert f.value("residual_mass") == 175.0
    assert f.value("loaded_mass") == pytest.approx(usable + 300.0 + 175.0 + 40.0, rel=1e-15)
    assert f.value("expulsion_efficiency") == pytest.approx(
        (usable + 300.0) / (usable + 475.0), rel=1e-15)
    ox = result.oxidiser
    assert ox.value("expulsion_efficiency") == 0.98
    assert "covered by the expulsion efficiency" in ox.unresolved["trapped_line"].lower()
    assert result.totals["loaded_oxidiser_fuel_ratio"] != result.totals[
        "usable_oxidiser_fuel_ratio"]


def test_an_unresolved_term_propagates_to_the_totals(stub_gateway):
    fuel = replace(COMPLETE, allowance_modes={**NA, "chilldown": TermMode.UNRESOLVED})
    result = inventory(COMPLETE, fuel)
    assert result.status is StudyStatus.INCOMPLETE
    assert result.fuel.status is StudyStatus.INCOMPLETE
    assert "chill-down" in result.fuel.unresolved["loaded_mass"]
    assert "loaded_total" in result.totals_unresolved
    assert result.totals["minimum_known_loaded_total"] > result.totals["usable_total"]
    chill = [line for line in result.fuel.ledger if line.key == "chilldown"][0]
    assert chill.status == "unresolved" and chill.value is None


def test_no_cycle_flow_is_added(stub_gateway):
    result = inventory()
    keys = set(result.oxidiser.quantities) | set(result.totals)
    assert not any(k for k in keys if "generator" in k or "bleed" in k or "turbine" in k)
    assert any("gas generator" in a for a in result.assumptions)


# ===========================================================================
# records
# ===========================================================================


def test_records_round_trip_and_are_deterministic(stub_gateway):
    result = inventory()
    text = result.to_json()
    again = StudyResult.from_json(text, INVENTORY_SCHEMA)
    assert again == result and again.to_json() == text
    assert inventory().to_json() == text
    payload = json.loads(text)
    assert payload["schema"] == INVENTORY_SCHEMA and payload["version"] == 1
    assert payload["definition"]["basis"]["sizing"]["gate"] == "LIQ-4"
    assert payload["provenance"]["requirement"].endswith("burn time 200 s")


def test_a_hand_edited_or_foreign_record_is_refused(stub_gateway):
    record = json.loads(inventory().to_json())
    record["definition"]["oxidiser"]["expulsion_efficiency"] = 0.99
    with pytest.raises(RequirementFormatError, match="fingerprint"):
        StudyResult.from_dict(record, INVENTORY_SCHEMA)
    record = json.loads(inventory().to_json())
    record["schema"] = "rocketforge.liquid-injector"
    with pytest.raises(RequirementFormatError):
        StudyResult.from_dict(record, INVENTORY_SCHEMA)
    with pytest.raises(RequirementFormatError):
        StudyResult.from_json("not json", INVENTORY_SCHEMA)


def test_display_units(stub_gateway):
    result = inventory()
    groups = service.branch_view(result.oxidiser)["groups"]
    rows = {r["key"]: r for g in groups for r in g["rows"]}
    assert rows["expulsion_efficiency"]["value"] == "98.0000"
    assert rows["expulsion_efficiency"]["unit"] == "%"
    assert rows["loaded_mass"]["unit"] == "kg"
    ledger = service.branch_view(result.oxidiser)["ledger"]
    assert [r["key"] for r in ledger] == ["usable_mass", "start_stop", "chilldown",
                                          "other_allowance", "reserve_mass", "residual_mass",
                                          "boiloff_mass"]


def test_no_verdict_or_invented_number_in_any_text():
    sources = [ROOT / "rocketforge/application/analysis/propellant_inventory_service.py",
               ROOT / "rocketforge/engine/propulsion_system/inventory.py",
               ROOT / "ui/pages/PropellantInventoryPage.qml"]
    for path in sources:
        text = path.read_text(encoding="utf-8")
        for word in ("Optimal", "Optimum", "Recommended", "Feasible", "typical value"):
            assert word not in text, f"{path.name}: {word}"


# ===========================================================================
# the controller
# ===========================================================================


def test_the_controller_computes_only_on_compute_and_goes_stale(stub_gateway, qt_app):
    from PySide6.QtCore import Property, QObject, Signal

    from rocketforge.application.analysis.propellant_inventory_controller import (
        PropellantInventoryController,
    )

    class Source(QObject):
        resultChanged = Signal()

        def __init__(self, value):
            super().__init__()
            self._value, self._stale = value, False

        def result(self):
            return self._value

        def _get_stale(self):
            return self._stale

        resultStale = Property(bool, _get_stale, notify=resultChanged)

    sized, trade = chain()
    sizing_source, trade_source = Source(sized), Source(trade)
    c = PropellantInventoryController(sizing_source, trade_source)
    assert c.property("hasBasis") and c.property("canCompute")  # incomplete still computes
    calls = []
    original = service.solve_inventory
    service.solve_inventory = lambda d: calls.append(d) or original(d)
    try:
        for branch in ("oxidiser", "fuel"):
            c.setChoice(f"{branch}.residual_mode", "expulsion_efficiency")
            c.setField(f"{branch}.expulsion_efficiency", "98")
            c.setChoice(f"{branch}.reserve_mode", "stated_fraction")
            c.setField(f"{branch}.reserve", "2")
            for key, _l, _b in ALLOWANCE_TERMS:
                c.setChoice(f"{branch}.{key}_mode", "not_applicable")
            c.setChoice(f"{branch}.boiloff_mode", "not_applicable")
        c.setField("oxidiser.expulsion_efficiency", "not a number")    # ignored
        assert calls == [] and c.property("canCompute")
        sections = c.property("inputSections")
        efficiency = [f for f in sections[0]["fields"] if f["key"] == "oxidiser.expulsion_efficiency"]
        assert efficiency[0]["text"] == "98" and efficiency[0]["unit"] == "%"
        c.compute()
        assert len(calls) == 1 and c.property("statusLabel") == "Computed"
        r = c.result()
        assert r.oxidiser.value("loaded_mass") == pytest.approx(
            r.oxidiser.value("usable_mass") * 1.02 / 0.98, rel=1e-15)
        # Upstream goes stale: announced, not computed.
        sizing_source._stale = True
        sizing_source.resultChanged.emit()
        assert len(calls) == 1
        assert c.property("resultStale") and c.property("statusLabel").startswith("Stale")
        assert [i["code"] for i in c.property("issues")] == ["SIZING_STALE"]
        assert not c.property("canCompute")
    finally:
        service.solve_inventory = original
