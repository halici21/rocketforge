"""SYS-5: liquid propellant feed network.

* **Relations** (``engineering.propulsion_system.feed_network``) against
  independent oracles: Hagen-Poiseuille for a laminar pipe, a separately
  iterated Colebrook-White for a turbulent one, K ρv²/2 by hand, the sign of
  the static head, series summation and continuity.
* **Topology.** Empty, misplaced velocity head and out-of-domain components
  are refused; an unresolved component keeps the total unresolved.
* **Closure with LIQ-6, no double counting.** Feed-line and valve terms are
  never counted from LIQ-6; a carried dynamic head and a network velocity
  head together are refused; tank pressure − network = inlet requirement +
  margin to rounding.
* **Resolution.** Stale SYS-4 or LIQ-6, or a different sizing, is refused.
* **Records** round-trip.
"""

from __future__ import annotations

import itertools
import json
import math
from dataclasses import replace

import pytest

from rocketforge.application.analysis import feed_network_service as service
from rocketforge.engine.injector import LossMode
from rocketforge.engine.propulsion_system.feed_network import (
    FEED_SCHEMA,
    DensitySource,
    TermAssignment,
)
from rocketforge.engine.propulsion_system.records import StudyResult, StudyStatus
from rocketforge.engine.requirement import RequirementFormatError
from rocketforge.engineering.propulsion_system import feed_network as rel

import test_injector as injector_tests  # noqa: E402  (same directory)
from test_propellant_management import management  # noqa: E402
from test_tank_pressurization import BLOWDOWN, REGULATED  # noqa: E402
from test_tank_pressurization import study as pressurization_study  # noqa: E402

K = rel.ComponentKind
BAR = 1.0e5


def pipe(length, diameter, roughness=0.0):
    return rel.FeedComponent(K.PIPE, "pipe", length=length, diameter=diameter,
                             roughness=roughness)


def colebrook_by_fixed_point(re: float, relative_roughness: float) -> float:
    """An oracle independent of engineering.line's bracketed solve."""
    x = 0.02 ** -0.5
    for _ in range(200):
        x = -2.0 * math.log10(relative_roughness / 3.7 + 2.51 * x / re)
    return 1.0 / (x * x)


# ===========================================================================
# relations
# ===========================================================================


def test_laminar_pipe_against_hagen_poiseuille():
    mdot, rho, mu, length, d = 0.02, 1000.0, 0.05, 3.0, 0.02
    branch = rel.solve_feed_branch(mdot, rho, mu, [pipe(length, d)]).value
    q = mdot / rho
    assert branch.components[0].regime == "laminar"
    assert branch.total_drop == pytest.approx(128 * mu * length * q / (math.pi * d ** 4),
                                              rel=1e-13)


def test_turbulent_pipe_against_an_independent_colebrook():
    mdot, rho, mu, length, d, eps = 20.0, 1141.0, 1.9e-4, 12.0, 0.08, 1.5e-6
    c = rel.solve_feed_branch(mdot, rho, mu, [pipe(length, d, eps)]).value.components[0]
    v = mdot / (rho * math.pi * d * d / 4)
    re = rho * v * d / mu
    f = colebrook_by_fixed_point(re, eps / d)
    assert c.velocity == pytest.approx(v, rel=1e-15) and c.reynolds == pytest.approx(re,
                                                                                    rel=1e-15)
    assert c.friction_factor == pytest.approx(f, rel=1e-10)
    assert c.pressure_change == pytest.approx(f * length / d * rho * v * v / 2, rel=1e-10)


def test_local_loss_static_head_and_series_summation_by_hand():
    rho, mdot = 1000.0, 10.0
    parts = [rel.FeedComponent(K.LOCAL_LOSS, "elbow", loss_coefficient=0.3, diameter=0.05),
             rel.FeedComponent(K.VALVE, "valve", loss_coefficient=2.0, diameter=0.04),
             rel.FeedComponent(K.FILTER, "filter", pressure_drop=0.4 * BAR),
             rel.FeedComponent(K.STATIC_HEAD, "drop to engine", rise=-6.0, acceleration=30.0),
             rel.FeedComponent(K.VELOCITY_HEAD, "inlet", diameter=0.05)]
    b = rel.solve_feed_branch(mdot, rho, None, parts).value
    v5 = mdot / (rho * math.pi * 0.05 ** 2 / 4)
    v4 = mdot / (rho * math.pi * 0.04 ** 2 / 4)
    expected = [0.3 * rho * v5 ** 2 / 2, 2.0 * rho * v4 ** 2 / 2, 0.4 * BAR,
                -rho * 30.0 * 6.0, rho * v5 ** 2 / 2]
    for r, e in zip(b.components, expected):
        assert r.pressure_change == pytest.approx(e, rel=1e-14)
    assert b.total_drop == pytest.approx(math.fsum(expected), rel=1e-14)
    assert b.max_continuity_closure < 1e-15


def test_static_head_sign_convention():
    climb = rel.static_head(1000.0, 9.80665, 2.0)
    assert climb == pytest.approx(19613.3) and rel.static_head(1000.0, 9.80665, -2.0) == -climb


def test_unresolved_and_transitional_components_stay_unresolved():
    parts = [pipe(1.0, 0.05), rel.FeedComponent(K.UNRESOLVED, "unknown valve"),
             rel.FeedComponent(K.FILTER, "filter", pressure_drop=1000.0)]
    b = rel.solve_feed_branch(1.0, 1000.0, 1e-3, parts).value
    assert b.total_drop is None and b.unresolved == (1,)
    assert b.known_drop == pytest.approx(b.components[0].pressure_change + 1000.0, rel=1e-15)
    # Re = 4 mdot / (π D μ) = 3000: the transition band has no friction factor.
    mdot = 3000 * math.pi * 0.05 * 1e-3 / 4
    t = rel.solve_feed_branch(mdot, 1000.0, 1e-3, [pipe(1.0, 0.05)]).value
    assert t.total_drop is None and "transition" in t.components[0].reason
    no_mu = rel.solve_feed_branch(1.0, 1000.0, None, [pipe(1.0, 0.05)]).value
    assert no_mu.total_drop is None and "viscosity" in no_mu.components[0].reason


@pytest.mark.parametrize("parts,code", [
    ([], "NETWORK_EMPTY"),
    ([rel.FeedComponent(K.VELOCITY_HEAD, "", diameter=0.05),
      rel.FeedComponent(K.FILTER, "", pressure_drop=1.0)], "TOPOLOGY_INVALID"),
    ([rel.FeedComponent(K.LOCAL_LOSS, "", loss_coefficient=-0.1, diameter=0.05)],
     "COMPONENT_INVALID"),
    ([pipe(0.0, 0.05)], "COMPONENT_INVALID"),
    ([pipe(1.0, math.nan)], "COMPONENT_INVALID"),
    ([rel.FeedComponent(K.STATIC_HEAD, "", rise=1.0, acceleration=0.0)], "COMPONENT_INVALID"),
    ([rel.FeedComponent(K.FILTER, "", pressure_drop=math.inf)], "COMPONENT_INVALID"),
])
def test_invalid_topology_and_components_are_refused(parts, code):
    solution = rel.solve_feed_branch(1.0, 1000.0, 1e-3, parts)
    assert solution.value is None and solution.diagnostics[0].code == code


def test_a_component_states_exactly_its_fields():
    with pytest.raises(ValueError):
        rel.FeedComponent(K.PIPE, "", length=1.0, diameter=0.05)
    with pytest.raises(ValueError):
        rel.FeedComponent(K.FILTER, "", pressure_drop=1.0, diameter=0.05)


def test_parameter_grid_conserves_mass_and_sums_in_series():
    count = 0
    for mdot, d, eps, k, rise in itertools.product((0.5, 8.0, 300.0), (0.02, 0.1, 0.3),
                                                   (0.0, 1.5e-6, 4.5e-5), (0.0, 0.8, 5.0),
                                                   (-10.0, 0.0, 4.0)):
        parts = [pipe(5.0, d, eps),
                 rel.FeedComponent(K.VALVE, "", loss_coefficient=k, diameter=d),
                 rel.FeedComponent(K.STATIC_HEAD, "", rise=rise, acceleration=20.0)]
        b = rel.solve_feed_branch(mdot, 1000.0, 1e-3, parts).value
        assert b.max_continuity_closure < 5e-16
        resolved = [r.pressure_change for r in b.components if r.pressure_change is not None]
        assert b.known_drop == pytest.approx(math.fsum(resolved), rel=1e-15, abs=1e-12)
        count += 1
    assert count == 243


# ===========================================================================
# service: closure with LIQ-6, without double counting
# ===========================================================================

INJECTOR_LEDGER = injector_tests.losses(
    feed_line_loss=(LossMode.STATED, 5 * BAR), valve_loss=(LossMode.STATED, 2 * BAR),
    cooling_jacket_loss=(LossMode.NOT_APPLICABLE, None),
    dynamic_head=(LossMode.STATED, 0.5 * BAR), other_loss=(LossMode.NOT_APPLICABLE, None),
    margin=(LossMode.STATED, 1 * BAR))
NETWORK = (("pipe", (("diameter", 0.05), ("length", 4.0), ("roughness", 1.5e-6))),
           ("valve", (("diameter", 0.05), ("loss_coefficient", 1.5))),
           ("filter", (("pressure_drop", 0.3 * BAR),)),
           ("static_head", (("acceleration", 20.0), ("rise", -3.0))),
           ("velocity_head", (("diameter", 0.05),)))
FEED = service.BranchSettings(
    density_source=DensitySource.INJECTOR, viscosity=2e-4, components=NETWORK,
    assignments={"dynamic_head": TermAssignment.REPLACED, "other_loss": TermAssignment.CARRIED})
#: Tank pressures high enough for the sizing's chamber pressure.
REG = replace(REGULATED, tank_pressure=200 * BAR, bottle_final_pressure=210 * BAR,
              required_pressure=150 * BAR)
BLOW = replace(BLOWDOWN, initial_pressure=400 * BAR, required_pressure=150 * BAR)


def upstream(ledger=INJECTOR_LEDGER):
    sized = injector_tests.sizing()
    ox = replace(injector_tests.OX, **ledger)
    fuel = replace(injector_tests.FUEL, **ledger)
    injector = injector_tests.study(sized, ox, fuel)
    pressurization = pressurization_study(REG, BLOW, mgmt=management())
    return pressurization, injector


def feed(ox=FEED, fuel=FEED, ups=None) -> StudyResult:
    pressurization, injector = ups or upstream()
    basis, issues = service.feed_basis(pressurization, False, injector, False)
    assert basis is not None, issues
    definition, issues = service.build_definition(basis, ox, fuel)
    assert definition is not None, issues
    return service.solve_feed_network(definition)


def test_stale_or_mismatched_upstream_is_refused(stub_gateway):
    pressurization, injector = upstream()
    codes = lambda *a: [i.code for i in service.feed_basis(*a)[1]]  # noqa: E731
    assert codes(None, False, injector, False) == ["NO_PRESSURIZATION"]
    assert codes(pressurization, True, injector, False) == ["PRESSURIZATION_STALE"]
    assert codes(pressurization, False, None, False) == ["NO_INJECTOR"]
    assert codes(pressurization, False, injector, True) == ["INJECTOR_STALE"]
    other = injector_tests.study(injector_tests.sizing(replace(
        injector_tests.IDEAL, area_ratio=25.0)))
    assert codes(pressurization, False, other, False) == ["INJECTOR_MISMATCH"]
    assert codes(pressurization, False, injector, False) == []


def test_liq6_feed_terms_are_replaced_never_counted_twice(stub_gateway):
    result = feed()
    ox = result.oxidiser
    lines = {line.key: line for line in ox.ledger}
    for key in ("liq6_feed_line_loss", "liq6_valve_loss", "liq6_dynamic_head"):
        assert lines[key].status == "excluded" and lines[key].value is None
        assert "Replaced by the network" in lines[key].reason
    basis = result.definition.basis.oxidiser_basis
    terms = {t.key: t.value for t in basis.ledger}
    inlet = terms["chamber_pressure"] + terms["injector_pressure_drop"] + 1 * BAR
    assert ox.value("inlet_required") == pytest.approx(inlet, rel=1e-15)
    assert ox.value("tank_required") == pytest.approx(inlet + ox.value("network_drop"),
                                                      rel=1e-15)
    # LIQ-6's own requirement counted 5 + 2 + 0.5 bar of feed terms that are not counted here.
    assert ox.value("liq6_required") == pytest.approx(inlet + 7.5 * BAR, rel=1e-15)


def test_a_carried_dynamic_head_with_a_velocity_head_component_is_refused(stub_gateway):
    pressurization, injector = upstream()
    basis, _ = service.feed_basis(pressurization, False, injector, False)
    double = replace(FEED, assignments={**FEED.assignments,
                                        "dynamic_head": TermAssignment.CARRIED})
    _d, issues = service.build_definition(basis, double, FEED)
    assert [i.code for i in issues] == ["DOUBLE_COUNTED"]
    unstated = replace(FEED, assignments={"dynamic_head": None, "other_loss": None})
    _d, issues = service.build_definition(basis, unstated, FEED)
    assert [i.code for i in issues] == ["ASSIGNMENT_UNRESOLVED"] * 2


def test_branch_pressure_closure(stub_gateway):
    result = feed()
    for b in (result.oxidiser, result.fuel):
        assert abs(b.value("pressure_closure")) < 1e-14
    ox, fu = result.oxidiser, result.fuel
    assert ox.value("margin_regulated") == pytest.approx(
        200 * BAR - ox.value("tank_required"), rel=1e-14)
    assert fu.value("margin_start") == pytest.approx(400 * BAR - fu.value("tank_required"),
                                                     rel=1e-14)
    assert fu.value("tank_pressure_end") == result.definition.basis.fuel_basis.tank_pressures[
        "end"]
    # The node series runs down from the tank pressure, component by component.
    assert ox.series[-1]["pressure"] == pytest.approx(200 * BAR - ox.value("network_drop"),
                                                      rel=1e-14)


def test_an_unresolved_component_or_liq6_term_propagates(stub_gateway):
    with_unknown = replace(FEED, components=NETWORK[:2] + (("unresolved", ()),) + NETWORK[2:])
    result = feed(with_unknown, FEED)
    ox = result.oxidiser
    assert ox.status is StudyStatus.INCOMPLETE
    assert "network_drop" in ox.unresolved and "margin_regulated" in ox.unresolved
    assert ox.value("network_known_drop") > 0
    ledger = injector_tests.losses(feed_line_loss=(LossMode.STATED, 5 * BAR),
                                   margin=(LossMode.UNRESOLVED, None))
    result = feed(ups=upstream(ledger))
    assert "inlet_required" in result.oxidiser.unresolved


def test_a_short_tank_pressure_is_a_warning(stub_gateway):
    low = upstream()
    pressurization, injector = low
    result = feed(ups=(pressurization_study(replace(REG, tank_pressure=60 * BAR,
                                                    bottle_final_pressure=70 * BAR,
                                                    required_pressure=50 * BAR), BLOW,
                                            mgmt=management()), injector))
    assert result.status is StudyStatus.WARNING
    assert result.oxidiser.labels["feed_check"].startswith("INSUFFICIENT")


def test_nothing_is_defaulted(stub_gateway):
    pressurization, injector = upstream()
    basis, _ = service.feed_basis(pressurization, False, injector, False)
    _d, issues = service.build_definition(basis, service.BranchSettings(), FEED)
    assert {i.code for i in issues} == {"DENSITY_SOURCE_UNRESOLVED", "NETWORK_EMPTY",
                                        "ASSIGNMENT_UNRESOLVED"}
    no_mu = replace(FEED, viscosity=None)
    _d, issues = service.build_definition(basis, no_mu, FEED)
    assert [i.code for i in issues] == ["VISCOSITY_UNRESOLVED"]
    blank = replace(FEED, components=(("pipe", (("diameter", None), ("length", 1.0),
                                                ("roughness", 0.0))),))
    _d, issues = service.build_definition(basis, blank, FEED)
    assert [i.code for i in issues] == ["COMPONENT_UNRESOLVED"]


def test_records_round_trip_and_are_fingerprint_checked(stub_gateway):
    result = feed()
    text = result.to_json()
    assert StudyResult.from_json(text, FEED_SCHEMA) == result
    record = json.loads(text)
    assert record["definition"]["basis"]["injector"]["gate"] == "LIQ-6"
    record["definition"]["oxidiser"]["components"][0]["length"] = 5.0
    with pytest.raises(RequirementFormatError, match="fingerprint"):
        StudyResult.from_dict(record, FEED_SCHEMA)
