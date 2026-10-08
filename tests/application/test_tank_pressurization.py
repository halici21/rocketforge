"""SYS-4: tank pressurization foundation.

* **Relations** (``engineering.propulsion_system.pressurization``) against
  Sutton 9th ed. Eqs. 6-5 to 6-7 and Example 6-2, and against independent
  perfect-gas oracles: mass closure, isothermal and polytropic blowdown.
* **Service.** Regulated and blowdown branches side by side; the gas volumes
  are SYS-3's; an insufficient end-of-burn pressure is a warning with its
  number; an unresolved feed requirement stays unresolved; intent modes are
  recorded and computed nowhere; stale SYS-3 is refused.
* **Records** round-trip and are fingerprint-checked.
"""

from __future__ import annotations

import json
import math
from dataclasses import replace

import pytest

from rocketforge.application.analysis import tank_pressurization_service as service
from rocketforge.engine.propulsion_system.pressurization import (
    PRESSURIZATION_SCHEMA,
    PressurantReserve,
    PressurizationMode,
    RequiredSource,
    TankGasTemperature,
    UllageSource,
)
from rocketforge.engine.propulsion_system.records import Branch, StudyResult, StudyStatus
from rocketforge.engine.requirement import RequirementFormatError
from rocketforge.engineering.propulsion_system import pressurization as rel

from test_propellant_management import management  # noqa: E402  (same directory)

BAR = 1.0e5
HELIUM_R = 2077.1   # stated for the tests, as a user would; not a library value

REGULATED = service.BranchSettings(
    mode=PressurizationMode.REGULATED, gas_name="helium", gas_constant=HELIUM_R, exponent=1.0,
    required_source=RequiredSource.STATED, required_pressure=30 * BAR,
    tank_pressure=35 * BAR, tank_gas_temperature_mode=TankGasTemperature.BOTTLE_INITIAL,
    bottle_initial_pressure=300 * BAR, bottle_initial_temperature=290.0,
    bottle_final_pressure=40 * BAR, ullage_source=UllageSource.GROUND,
    reserve_mode=PressurantReserve.STATED_FRACTION, reserve_value=0.05)
BLOWDOWN = service.BranchSettings(
    mode=PressurizationMode.BLOWDOWN, gas_name="nitrogen", gas_constant=296.8, exponent=1.0,
    required_source=RequiredSource.STATED, required_pressure=10 * BAR,
    initial_pressure=40 * BAR, initial_temperature=290.0)


# ===========================================================================
# relations
# ===========================================================================


def test_sutton_example_6_2_isothermal():
    """250 kg of 90 % H2O2 (ρ 1388), p0 14 MPa, pp 3.40 MPa, 298 K, pg = pp.
    Sutton prints V0 = 0.0577 m³ and 1.30 kg helium, 9.16 kg nitrogen, from
    Vp rounded to 0.180 m³."""
    vp = 250.0 / 1388.0
    for r, mass in ((2079.0, 1.30), (296.7, 9.16)):
        g = rel.regulated_stored_gas(3.4e6, vp, 298.0, 14e6, 298.0, 3.4e6, r, 1.0).value
        assert g.bottle_volume == pytest.approx(3.4e6 * vp / (14e6 - 3.4e6), rel=1e-14)
        assert g.bottle_volume == pytest.approx(0.0577, abs=1.5e-4)
        assert g.initial_mass == pytest.approx(mass, abs=0.015)
        # Eq. 6-7 directly.
        assert g.initial_mass == pytest.approx(3.4e6 * vp / (r * 298.0) / (1 - 3.4 / 14),
                                               rel=1e-14)
        assert abs(g.mass_closure) < 1e-15


def test_sutton_example_6_2_isentropic_and_its_helium_arithmetic():
    """Example 6-2's isentropic case: one gas mass from (p0, V0) to (pp, V0 + Vp),
    p0 V0^k = pp (V0 + Vp)^k. Nitrogen (k 1.40): Sutton prints 1.748 V0 = 0.180,
    V0 = 0.103 m³. Helium (k 1.68): 4.118^(1/1.68) − 1 = 1.322, not the printed
    1.334, so V0 = 0.1362 m³ rather than 0.135; the relation follows the
    equation, and the printed value is pinned as Sutton's arithmetic."""
    vp = 250.0 / 1388.0
    for r, k, printed_v0 in ((296.7, 1.40, 0.103), (2079.0, 1.68, 0.135)):
        tg = rel.polytropic_temperature(298.0, 14e6, 3.4e6, k)
        g = rel.regulated_stored_gas(3.4e6, vp, tg, 14e6, 298.0, 3.4e6, r, k).value
        exact = vp / ((14e6 / 3.4e6) ** (1.0 / k) - 1.0)
        assert g.bottle_volume == pytest.approx(exact, rel=1e-13)
        assert 14e6 * g.bottle_volume ** k == pytest.approx(
            3.4e6 * (g.bottle_volume + vp) ** k, rel=1e-12)
        if k == 1.40:
            assert g.bottle_volume == pytest.approx(printed_v0, abs=5e-4)
        else:
            assert (14 / 3.4) ** (1 / 1.68) - 1 == pytest.approx(1.322, abs=5e-4)
            assert g.bottle_volume == pytest.approx(0.1362, abs=5e-5)
            assert g.bottle_volume / printed_v0 - 1 == pytest.approx(0.009, abs=0.002)


def test_regulated_mass_closes_for_any_stated_temperatures():
    for n, tp in ((1.0, 250.0), (1.3, 310.0), (1.66, 140.0)):
        g = rel.regulated_stored_gas(20 * BAR, 3.0, tp, 280 * BAR, 300.0, 25 * BAR, 2077.0,
                                     n).value
        mp = 20 * BAR * 3.0 / (2077.0 * tp)
        assert g.delivered_mass == pytest.approx(mp, rel=1e-15)
        assert g.initial_mass == pytest.approx(g.residual_mass + mp, rel=1e-14)
        assert g.bottle_final_temperature == pytest.approx(
            300.0 * (25 / 280) ** ((n - 1) / n), rel=1e-14)
        assert g.regulator_drop_end == 5 * BAR


def test_blowdown_isothermal_and_polytropic_against_pv_n():
    iso = rel.blowdown(40 * BAR, 290.0, 0.5, 1.5, 296.8, 1.0).value
    assert iso.final_pressure == pytest.approx(40 * BAR * 0.5 / 2.0, rel=1e-15)
    assert iso.final_temperature == 290.0 and iso.blowdown_ratio == 4.0
    adi = rel.blowdown(40 * BAR, 290.0, 0.5, 1.5, 296.8, 1.4).value
    assert adi.final_pressure == pytest.approx(40 * BAR * 0.25 ** 1.4, rel=1e-15)
    assert adi.final_temperature == pytest.approx(290.0 * 0.25 ** 0.4, rel=1e-15)
    for s in adi.evolution:
        assert s.pressure * s.gas_volume ** 1.4 == pytest.approx(40 * BAR * 0.5 ** 1.4,
                                                                 rel=1e-13)
    assert [s.expelled_fraction for s in adi.evolution] == [0.0, 0.25, 0.5, 0.75, 1.0]
    assert adi.gas_mass == pytest.approx(40 * BAR * 0.5 / (296.8 * 290.0), rel=1e-15)
    assert abs(adi.mass_closure) < 1e-14 and abs(iso.mass_closure) < 1e-15


@pytest.mark.parametrize("kwargs,code", [
    ({"gas_constant": 0.0}, "GAS_CONSTANT_INVALID"),
    ({"gas_constant": math.nan}, "GAS_CONSTANT_INVALID"),
    ({"exponent": 0.9}, "EXPONENT_INVALID"),
    ({"exponent": math.inf}, "EXPONENT_INVALID"),
    ({"tank_gas_temperature": -1.0}, "TANK_GAS_TEMPERATURE_INVALID"),
    ({"bottle_final_pressure": 10 * BAR}, "BOTTLE_BELOW_TANK_PRESSURE"),
    ({"bottle_final_pressure": 300 * BAR}, "BOTTLE_PRESSURE_ORDER"),
    ({"bottle_initial_temperature": 0.0}, "BOTTLE_INITIAL_TEMPERATURE_INVALID"),
])
def test_invalid_gas_states_are_refused(kwargs, code):
    args = dict(tank_pressure=20 * BAR, fill_volume=1.0, tank_gas_temperature=290.0,
                bottle_initial_pressure=280 * BAR, bottle_initial_temperature=290.0,
                bottle_final_pressure=25 * BAR, gas_constant=2077.0, exponent=1.0)
    args.update(kwargs)
    solution = rel.regulated_stored_gas(**args)
    assert solution.value is None and solution.diagnostics[0].code == code


def test_invalid_blowdown_states_are_refused():
    for args in ((0.0, 290.0, 1.0, 1.0, 296.8, 1.0), (1e6, 290.0, 0.0, 1.0, 296.8, 1.0),
                 (1e6, 290.0, 1.0, 1.0, 296.8, 0.5), (1e6, math.nan, 1.0, 1.0, 296.8, 1.0)):
        assert rel.blowdown(*args).value is None


# ===========================================================================
# service
# ===========================================================================


def study(ox=REGULATED, fuel=BLOWDOWN, mgmt=None, injector=None, injector_stale=False):
    mgmt = mgmt or management()
    basis, issues = service.pressurization_basis(mgmt, False)
    assert basis is not None, issues
    definition, issues = service.build_definition(basis, ox, fuel, injector, injector_stale)
    assert definition is not None, issues
    return service.solve_pressurization(definition)


def test_stale_or_refused_management_is_refused(stub_gateway):
    mgmt = management()
    codes = lambda *a: [i.code for i in service.pressurization_basis(*a)[1]]  # noqa: E731
    assert codes(None, False) == ["NO_MANAGEMENT"]
    assert codes(mgmt, True) == ["MANAGEMENT_STALE"]
    assert codes(mgmt, False) == []


def test_separate_regulated_and_blowdown_branches(stub_gateway):
    mgmt = management()
    result = study(mgmt=mgmt)
    ox, fu = result.oxidiser, result.fuel
    gas_ox = mgmt.oxidiser
    # Regulated, isothermal with Tp = T0 and a pre-pressurized ullage: Eq. 6-7.
    vp = gas_ox.value("expelled_volume")
    assert ox.value("fill_volume") == vp
    assert ox.value("bottle_volume") == pytest.approx(35 * BAR * vp / (300 * BAR - 40 * BAR),
                                                      rel=1e-14)
    m0 = ox.value("initial_mass")
    assert m0 == pytest.approx(35 * BAR * vp / (HELIUM_R * 290.0) / (1 - 40 / 300), rel=1e-14)
    assert ox.value("reserve_mass") == pytest.approx(0.05 * m0, rel=1e-15)
    assert ox.value("loaded_pressurant") == pytest.approx(1.05 * m0, rel=1e-15)
    assert ox.value("bottle_volume_with_reserve") == pytest.approx(
        1.05 * ox.value("bottle_volume"), rel=1e-14)
    assert ox.value("pressure_margin") == 5 * BAR
    # Blowdown, isothermal, from SYS-3's start and end gas volumes.
    gas_fu = mgmt.fuel
    vi, vf = gas_fu.value("gas_volume_start"), gas_fu.value("gas_volume_end")
    assert fu.value("final_pressure") == pytest.approx(40 * BAR * vi / vf, rel=1e-14)
    assert fu.value("blowdown_ratio") == pytest.approx(vf / vi, rel=1e-14)
    assert len(fu.series) == 5 and fu.series[-1]["gas_volume"] == pytest.approx(vf, rel=1e-14)
    assert result.totals["pressurant_total"] == pytest.approx(
        ox.value("loaded_pressurant") + fu.value("gas_mass"), rel=1e-15)


def test_insufficient_end_of_burn_pressure_is_a_warning_with_its_number(stub_gateway):
    result = study()
    fu = result.fuel
    assert fu.value("final_pressure") < 10 * BAR
    assert result.status is StudyStatus.WARNING
    assert fu.labels["feed_check"].startswith("INSUFFICIENT")
    assert fu.value("margin_end") < 0 < fu.value("margin_start")
    assert any("below the required tank pressure" in n for n in fu.notes)


def test_an_unresolved_feed_requirement_stays_unresolved(stub_gateway):
    result = study(ox=replace(REGULATED, required_source=RequiredSource.UNRESOLVED,
                              required_pressure=None))
    ox = result.oxidiser
    assert "required_pressure" in ox.unresolved and "pressure_margin" in ox.unresolved
    assert ox.labels["feed_check"].startswith("UNRESOLVED")
    assert ox.status is StudyStatus.INCOMPLETE


def test_the_liq6_requirement_propagates_as_unresolved_when_its_ledger_is(stub_gateway):
    from test_injector import study as injector_study  # noqa: E402

    injector = injector_study(__import__("test_injector").sizing())
    ox = replace(REGULATED, required_source=RequiredSource.INJECTOR, required_pressure=None)
    result = study(ox=ox, injector=injector)
    o = result.oxidiser
    assert "required_pressure" in o.unresolved and o.unresolved["required_pressure"].startswith(
        "LIQ-6")
    assert result.definition.oxidiser.required_upstream.gate == "LIQ-6"
    mgmt = management()
    basis, _ = service.pressurization_basis(mgmt, False)
    _d, issues = service.build_definition(basis, ox, BLOWDOWN, injector, True)
    assert [i.code for i in issues] == ["INJECTOR_STALE"]
    _d, issues = service.build_definition(basis, ox, BLOWDOWN, None, False)
    assert [i.code for i in issues] == ["NO_INJECTOR"]


def test_intent_modes_are_recorded_and_computed_nowhere(stub_gateway):
    calls = []
    original = rel.regulated_stored_gas
    rel.regulated_stored_gas = lambda *a, **k: calls.append(a) or original(*a, **k)
    try:
        result = study(ox=service.BranchSettings(mode=PressurizationMode.AUTOGENOUS_INTENT),
                       fuel=service.BranchSettings(mode=PressurizationMode.WARM_GAS_INTENT))
    finally:
        rel.regulated_stored_gas = original
    assert calls == []
    assert result.status is StudyStatus.INCOMPLETE
    for b in (result.oxidiser, result.fuel):
        assert "Intent recorded only" in b.unresolved["bottle_volume"]
        assert "do not exist yet" in b.labels["intent"]
    assert "pressurant_total" in result.totals_unresolved


def test_nothing_is_defaulted(stub_gateway):
    basis, _ = service.pressurization_basis(management(), False)
    _d, issues = service.build_definition(basis, service.BranchSettings(), BLOWDOWN)
    assert [i.code for i in issues] == ["MODE_UNRESOLVED"]
    _d, issues = service.build_definition(
        basis, service.BranchSettings(mode=PressurizationMode.REGULATED), BLOWDOWN)
    codes = {i.code for i in issues}
    assert {"GAS_UNRESOLVED", "GAS_CONSTANT_UNRESOLVED", "EXPONENT_UNRESOLVED",
            "TANK_PRESSURE_UNRESOLVED", "BOTTLE_PRESSURE_UNRESOLVED",
            "BOTTLE_TEMPERATURE_UNRESOLVED", "BOTTLE_FINAL_PRESSURE_UNRESOLVED",
            "TANK_GAS_TEMPERATURE_UNRESOLVED", "ULLAGE_SOURCE_UNRESOLVED"} == codes
    default = service.BranchSettings()
    assert default.gas_constant is None and default.exponent is None and not default.gas_name


def test_a_regulator_that_cannot_deliver_refuses_the_branch(stub_gateway):
    result = study(ox=replace(REGULATED, bottle_final_pressure=30 * BAR))
    assert result.status is StudyStatus.REFUSED
    assert "regulator cannot deliver" in result.oxidiser.message


def test_records_round_trip_and_are_fingerprint_checked(stub_gateway):
    result = study()
    text = result.to_json()
    assert StudyResult.from_json(text, PRESSURIZATION_SCHEMA) == result
    record = json.loads(text)
    assert record["definition"]["basis"]["management"]["gate"] == "SYS-3"
    record["definition"]["oxidiser"]["exponent"] = 1.2
    with pytest.raises(RequirementFormatError, match="fingerprint"):
        StudyResult.from_dict(record, PRESSURIZATION_SCHEMA)


def test_bottle_filling_the_start_ullage_adds_its_volume(stub_gateway):
    mgmt = management()
    a = study(mgmt=mgmt).oxidiser
    b = study(ox=replace(REGULATED, ullage_source=UllageSource.BOTTLE), mgmt=mgmt).oxidiser
    assert b.value("fill_volume") == pytest.approx(
        a.value("fill_volume") + mgmt.oxidiser.value("gas_volume_start"), rel=1e-15)
    assert b.value("bottle_volume") / a.value("bottle_volume") == pytest.approx(
        b.value("fill_volume") / a.value("fill_volume"), rel=1e-14)


def test_branches_keep_their_identity(stub_gateway):
    result = study()
    assert result.oxidiser.branch is Branch.OXIDISER and result.fuel.branch is Branch.FUEL
    assert result.oxidiser.labels["gas"].startswith("helium")
    assert result.fuel.labels["gas"].startswith("nitrogen")
