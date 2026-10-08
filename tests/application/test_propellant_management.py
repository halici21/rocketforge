"""SYS-3: propellant management foundation.

* **Semantics** (``engineering.propulsion_system.propellant_management``):
  every mode × environment × settling intent gives a declaration with its
  basis, never a demonstration; a settled free surface in low gravity with no
  settling is refused; an unstated environment is unresolved.
* **Volumes** against hand calculations: liquid present, start and end gas,
  expelled and residual volume close on the tank.
* **Consistency with SYS-1/SYS-2**: the expulsion efficiency and residual are
  SYS-1's, unchanged; ullage + fill = 1.
* **Resolution**: stale or mismatched inventory and tanks are refused.
* **Records** round-trip, every mode serializes.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
from dataclasses import replace

import pytest

from rocketforge.application.analysis import propellant_management_service as service
from rocketforge.application.analysis import propellant_tanks_service as tank_service
from rocketforge.engine.propulsion_system.management import (
    MANAGEMENT_SCHEMA,
    Environment,
    ManagementMode,
    SettlingIntent,
)
from rocketforge.engine.propulsion_system.records import Branch, StudyResult, StudyStatus
from rocketforge.engine.requirement import RequirementFormatError
from rocketforge.engineering.propulsion_system import propellant_management as rel

from test_propellant_inventory import COMPLETE, inventory  # noqa: E402  (same directory)
from test_propellant_tanks import tank_study  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
RM, RE, RS, A = rel.ManagementMode, rel.Environment, rel.SettlingIntent, rel.Availability

OX = service.BranchSettings(mode=ManagementMode.SETTLED, environment=Environment.ACCELERATED,
                            settling=SettlingIntent.NOT_REQUIRED)
FUEL = service.BranchSettings(mode=ManagementMode.DIAPHRAGM, environment=Environment.LOW_GRAVITY,
                              settling=SettlingIntent.NOT_REQUIRED)


def chain():
    inv = inventory()
    tanks = tank_study(inv=inv)
    return inv, tanks


def management(ox=OX, fuel=FUEL, inv=None, tanks=None) -> StudyResult:
    if inv is None:
        inv, tanks = chain()
    basis, issues = service.management_basis(inv, False, tanks, False)
    assert basis is not None, issues
    definition, issues = service.build_definition(basis, ox, fuel)
    assert definition is not None, issues
    return service.solve_management(definition)


# ===========================================================================
# semantics
# ===========================================================================


def test_every_combination_is_a_declaration_or_an_explicit_refusal():
    seen = set()
    for mode, env, settling in itertools.product(RM, RE, RS):
        solution = rel.management_state(mode, env, settling)
        if solution.value is None:
            assert (mode, env, settling) == (RM.SETTLED, RE.LOW_GRAVITY, RS.NOT_REQUIRED)
            assert solution.diagnostics[0].code == "FREE_SURFACE_UNSETTLED"
            continue
        state = solution.value
        seen.add(state.availability)
        text = state.statement.lower()
        assert "not evaluated" in text or "not modelled" in text or "not stated" in text \
            or "unresolved" in text, state.statement
        assert "guarantee" not in text and "is available" not in text
    assert seen == set(A)


def test_settled_versus_low_gravity_semantics():
    assert rel.management_state(RM.SETTLED, RE.ACCELERATED,
                                RS.NOT_REQUIRED).value.availability is A.DECLARED_SETTLED
    assert rel.management_state(RM.SETTLED, RE.LOW_GRAVITY,
                                RS.REQUIRED).value.availability is A.REQUIRES_SETTLING
    assert rel.management_state(RM.SETTLED, RE.LOW_GRAVITY,
                                RS.UNRESOLVED).value.availability is A.UNRESOLVED
    assert rel.management_state(RM.SETTLED, RE.LOW_GRAVITY, RS.NOT_REQUIRED).value is None
    # A device is a declaration in either environment; low-gravity feed is never claimed.
    for env in (RE.ACCELERATED, RE.LOW_GRAVITY):
        for mode in (RM.DIAPHRAGM, RM.BLADDER, RM.PISTON, RM.BELLOWS):
            assert rel.management_state(mode, env, RS.UNRESOLVED).value.availability \
                is A.DECLARED_DEVICE
    pmd = rel.management_state(RM.SURFACE_TENSION, RE.LOW_GRAVITY, RS.NOT_REQUIRED).value
    assert pmd.availability is A.DECLARED_CAPILLARY and "not claimed" in pmd.statement
    accelerated = rel.management_state(RM.SURFACE_TENSION, RE.ACCELERATED, RS.UNRESOLVED).value
    assert accelerated.advisories and "low-acceleration" in accelerated.advisories[0]


def test_an_unstated_environment_is_unresolved_for_every_mode():
    for mode, settling in itertools.product(RM, RS):
        assert rel.management_state(mode, RE.UNRESOLVED, settling).value.availability \
            is A.UNRESOLVED


def test_management_volumes_by_hand():
    # 10 m³ tank, ρ 1000: loaded 9000 kg (boil-off 100), present 8900, available 8800,
    # residual 100 kg.
    v = rel.management_volumes(10.0, 1000.0, 9000.0, 8900.0, 8800.0, 100.0).value
    assert v.liquid_volume_loaded == 9.0 and v.liquid_volume_present == 8.9
    assert v.gas_volume_start == pytest.approx(1.1, rel=1e-14)
    assert v.expelled_volume == 8.8 and v.residual_volume == 0.1
    assert v.gas_volume_end == pytest.approx(9.9, rel=1e-15)
    assert v.ullage_fraction_end == pytest.approx(0.99, rel=1e-15)
    assert abs(v.volume_closure) < 1e-15


@pytest.mark.parametrize("args,code", [
    ((0.0, 1000.0, 1.0, 1.0, 1.0, 0.0), "TANK_VOLUME_INVALID"),
    ((1.0, math.nan, 1.0, 1.0, 1.0, 0.0), "DENSITY_INVALID"),
    ((1.0, 1000.0, 1.0, 1.0, 1.0, -1.0), "RESIDUAL_MASS_INVALID"),
    ((1.0, 1000.0, 2000.0, 2000.0, 1999.0, 1.0), "TANK_OVERFILLED"),
])
def test_invalid_or_impossible_volumes_are_refused(args, code):
    solution = rel.management_volumes(*args)
    assert solution.value is None and solution.diagnostics[0].code == code


# ===========================================================================
# resolution and consistency with SYS-1 / SYS-2
# ===========================================================================


def test_stale_or_mismatched_upstream_is_refused(stub_gateway):
    inv, tanks = chain()
    codes = lambda *a: [i.code for i in service.management_basis(*a)[1]]  # noqa: E731
    assert codes(None, False, tanks, False) == ["INVENTORY_INCOMPLETE"]
    assert codes(inv, True, tanks, False) == ["INVENTORY_STALE"]
    assert codes(inv, False, None, False) == ["NO_TANKS"]
    assert codes(inv, False, tanks, True) == ["TANKS_STALE"]
    other = inventory(replace(COMPLETE, expulsion_efficiency=0.97))
    assert codes(other, False, tanks, False) == ["TANKS_MISMATCH"]
    refused = tank_study(fuel=replace(tank_service.BranchSettings(
        density=422.6, ullage_mode=tank_service.UllageMode.FRACTION, ullage_value=0.05,
        shape=tank_service.TankShape.CYLINDER_HEMISPHERICAL,
        sizing_mode=tank_service.SizingMode.STATED_DIAMETER, diameter=50.0)), inv=inv)
    assert codes(inv, False, refused, False) == ["TANKS_REFUSED"]
    assert codes(inv, False, tanks, False) == []


def test_the_mode_has_no_default(stub_gateway):
    inv, tanks = chain()
    basis, _ = service.management_basis(inv, False, tanks, False)
    _d, issues = service.build_definition(basis, service.BranchSettings(), FUEL)
    assert [i.code for i in issues] == ["MODE_UNRESOLVED"]
    _d, issues = service.build_definition(basis, replace(OX, settling_acceleration=-1.0), FUEL)
    assert [i.code for i in issues] == ["SETTLING_ACCELERATION_INVALID"]


def test_residual_and_expulsion_are_sys1s_unchanged(stub_gateway):
    inv, tanks = chain()
    result = management(inv=inv, tanks=tanks)
    for branch in Branch:
        m, i, t = result.branch(branch), inv.branch(branch), tanks.branch(branch)
        assert m.value("expulsion_efficiency") == i.value("expulsion_efficiency")
        assert m.value("residual_mass") == i.value("residual_mass")
        rho = t.value("density")
        assert m.value("expelled_volume") == pytest.approx(i.value("available_mass") / rho,
                                                           rel=1e-15)
        assert m.value("gas_volume_end") + m.value("residual_volume") == pytest.approx(
            t.value("tank_volume"), rel=1e-14)
        assert abs(m.value("fill_ullage_closure")) < 1e-15
        assert abs(m.value("volume_closure")) < 1e-14
        assert abs(m.value("inventory_closure")) < 1e-15
        assert "SYS-1" in m.labels["expulsion_source"]


def test_settled_and_device_branches_and_a_refused_combination(stub_gateway):
    result = management()
    assert result.status is StudyStatus.OK
    assert result.oxidiser.labels["outlet_availability"].startswith("Declared: settled")
    assert result.fuel.labels["outlet_availability"].startswith("Declared: positive-expulsion")
    refused = management(fuel=replace(FUEL, mode=ManagementMode.SETTLED))
    assert refused.status is StudyStatus.REFUSED
    assert "nothing to keep the outlet covered" in refused.fuel.message


def test_an_unresolved_environment_makes_the_study_incomplete(stub_gateway):
    result = management(ox=replace(OX, environment=Environment.UNRESOLVED))
    assert result.status is StudyStatus.INCOMPLETE
    assert result.oxidiser.labels["outlet_availability"] == "UNRESOLVED"


# ===========================================================================
# records and wording
# ===========================================================================


@pytest.mark.parametrize("mode", list(ManagementMode))
def test_every_mode_serializes(stub_gateway, mode):
    env = Environment.LOW_GRAVITY if mode is not ManagementMode.SETTLED else \
        Environment.ACCELERATED
    result = management(ox=replace(OX, mode=mode, environment=env,
                                   settling=SettlingIntent.REQUIRED,
                                   settling_acceleration=0.05))
    text = result.to_json()
    again = StudyResult.from_json(text, MANAGEMENT_SCHEMA)
    assert again == result and again.definition.oxidiser.mode is mode
    assert again.oxidiser.value("settling_acceleration") == 0.05


def test_a_hand_edited_record_is_refused(stub_gateway):
    record = json.loads(management().to_json())
    record["definition"]["fuel"]["mode"] = "piston"
    with pytest.raises(RequirementFormatError, match="fingerprint"):
        StudyResult.from_dict(record, MANAGEMENT_SCHEMA)


def test_no_false_claim_of_availability():
    sources = [ROOT / "rocketforge/engineering/propulsion_system/propellant_management.py",
               ROOT / "rocketforge/application/analysis/propellant_management_service.py",
               ROOT / "ui/pages/PropellantManagementPage.qml"]
    for path in sources:
        text = path.read_text(encoding="utf-8").lower()
        for claim in ("guaranteed", "always available", "zero-g reliable", "is available at",
                      "slosh frequency", "damping ratio"):
            assert claim not in text, (path.name, claim)
