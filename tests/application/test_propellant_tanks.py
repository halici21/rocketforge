"""SYS-2: propellant tank geometry and packaging.

* **Relations** (``engineering.propulsion_system.tank_geometry``) against
  independent hand calculations: sphere and spheroid volume and area by
  formula and by numerical integration, cylinder + dome closure, ullage and
  density/mass/volume closure, exact boundaries and refusals.
* **Grid.** Mass × density × ullage × diameter/length × shape, every closure
  at rounding level.
* **Resolution.** Only a current, complete SYS-1 inventory drives a study; no
  density, ullage, shape or dimension is defaulted.
* **Records** round-trip and are fingerprint-checked.
"""

from __future__ import annotations

import itertools
import json
import math
from dataclasses import replace

import pytest

from rocketforge.application.analysis import propellant_inventory_service as inv_service
from rocketforge.application.analysis import propellant_tanks_service as service
from rocketforge.engine.propulsion_system.records import StudyResult, StudyStatus
from rocketforge.engine.propulsion_system.tanks import (
    TANK_SCHEMA,
    DensitySource,
    SizingMode,
    TankShape,
    UllageMode,
)
from rocketforge.engine.requirement import RequirementFormatError
from rocketforge.engineering.propulsion_system import tank_geometry as rel

from test_propellant_inventory import COMPLETE, inventory  # noqa: E402  (same directory)

T = rel.TankShape
M = rel.SizingMode
K = math.sqrt(2.0) / 2.0

OX = service.BranchSettings(density=1141.0, ullage_mode=UllageMode.FRACTION, ullage_value=0.05,
                            shape=TankShape.SPHERE)
FUEL = service.BranchSettings(density=422.6, ullage_mode=UllageMode.VOLUME, ullage_value=2.0,
                              shape=TankShape.CYLINDER_ELLIPSOIDAL,
                              sizing_mode=SizingMode.STATED_DIAMETER, diameter=4.0,
                              dome_ratio=K)


def surface_of_revolution(radius: float, height: float, n: int = 20000) -> float:
    """Half-spheroid area by midpoint integration of 2πx ds: an oracle that
    shares no formula with the relation."""
    total, dt = 0.0, (math.pi / 2.0) / n
    for i in range(n):
        t = (i + 0.5) * dt
        x = radius * math.sin(t)
        total += 2.0 * math.pi * x * math.hypot(radius * math.cos(t), height * math.sin(t)) * dt
    return total


# ===========================================================================
# relations
# ===========================================================================


def test_sphere_volume_and_area_by_hand():
    g = rel.solve_tank_geometry(1.0, T.SPHERE, M.VOLUME).value
    r = (3.0 / (4.0 * math.pi)) ** (1.0 / 3.0)
    assert g.radius == pytest.approx(r, rel=1e-15) and g.diameter == pytest.approx(2 * r)
    assert g.surface_area == pytest.approx(4.0 * math.pi * r * r, rel=1e-15)
    assert g.total_length == g.diameter and g.barrel_length is None
    # A 1 m radius sphere, by hand: V = 4.18879 m³, A = 12.56637 m².
    g = rel.solve_tank_geometry(4.0 * math.pi / 3.0, T.SPHERE, M.VOLUME).value
    assert g.radius == pytest.approx(1.0, rel=1e-15)
    assert g.surface_area == pytest.approx(12.566370614359172, rel=1e-15)


def test_hemispherical_capsule_closes_by_hand():
    # D = 2 m: domes are a 1 m sphere (4.18879 m³); 10 m³ leaves a 1.84977 m barrel.
    g = rel.solve_tank_geometry(10.0, T.CYLINDER_HEMISPHERICAL, M.STATED_DIAMETER,
                                diameter=2.0).value
    assert g.barrel_length == pytest.approx((10.0 - 4.0 * math.pi / 3.0) / math.pi, rel=1e-15)
    assert g.barrel_length == pytest.approx(1.8497655285045735, rel=1e-14)
    assert g.dome_height == 1.0 and g.total_length == pytest.approx(g.barrel_length + 2.0)
    assert g.surface_area == pytest.approx(2 * math.pi * g.barrel_length + 4 * math.pi, rel=1e-15)
    assert abs(g.volume_closure) < 5e-16


def test_ellipsoidal_dome_against_independent_calculations():
    for ratio in (0.3, 0.5, K, 0.9, 0.999, 1.0):
        r = 1.7
        assert rel.dome_volume(r, ratio) == pytest.approx(
            2.0 / 3.0 * math.pi * r ** 3 * ratio, rel=1e-15)
        assert rel.dome_area(r, ratio) == pytest.approx(
            surface_of_revolution(r, ratio * r), rel=2e-9)
    # k = 1/√2, R = 1, by hand: e = 1/√2, A = π + (π/2) artanh(e)/e.
    e = 1.0 / math.sqrt(2.0)
    assert rel.dome_area(1.0, K) == pytest.approx(math.pi + 0.5 * math.pi * math.atanh(e) / e,
                                                  rel=1e-15)
    # Continuous into the hemisphere.
    assert rel.dome_area(1.0, 1.0) == pytest.approx(2.0 * math.pi, rel=1e-15)
    assert rel.dome_area(1.0, 1.0 - 1e-12) == pytest.approx(2.0 * math.pi, rel=1e-11)


def test_stated_length_solves_the_diameter_and_closes():
    g = rel.solve_tank_geometry(10.0, T.CYLINDER_ELLIPSOIDAL, M.STATED_LENGTH,
                                total_length=5.0, dome_ratio=K).value
    r = g.radius
    assert math.pi * r * r * 5.0 - 2.0 / 3.0 * math.pi * K * r ** 3 == pytest.approx(10.0,
                                                                                   rel=1e-14)
    assert g.total_length == pytest.approx(5.0, rel=1e-15)
    assert abs(g.volume_closure) < 1e-14


def test_exact_boundaries():
    # Diameter at which the two hemispheres are exactly the volume: L = 0.
    v = 4.0 / 3.0 * math.pi
    g = rel.solve_tank_geometry(v, T.CYLINDER_HEMISPHERICAL, M.STATED_DIAMETER, diameter=2.0)
    assert g.value.barrel_length == pytest.approx(0.0, abs=1e-15)
    # Longest volume a stated length holds: two domes, no barrel.
    lt, k = 3.0, 0.6
    v_max = math.pi * lt ** 3 / (6.0 * k * k)
    g = rel.solve_tank_geometry(v_max, T.CYLINDER_ELLIPSOIDAL, M.STATED_LENGTH, total_length=lt,
                                dome_ratio=k).value
    assert g.radius == pytest.approx(lt / (2.0 * k), rel=1e-15)
    assert g.barrel_length == pytest.approx(0.0, abs=1e-15)
    # Envelope exactly met is accepted.
    d = rel.solve_tank_geometry(1.0, T.SPHERE, M.VOLUME).value.diameter
    assert rel.solve_tank_geometry(1.0, T.SPHERE, M.VOLUME, envelope_diameter=d).ok


@pytest.mark.parametrize("kwargs,code", [
    ({"volume": 10.0, "shape": T.CYLINDER_HEMISPHERICAL, "mode": M.STATED_DIAMETER,
      "diameter": 3.0}, "DIAMETER_TOO_LARGE"),
    ({"volume": 50.0, "shape": T.CYLINDER_ELLIPSOIDAL, "mode": M.STATED_LENGTH,
      "total_length": 2.0, "dome_ratio": 0.5}, "LENGTH_TOO_SHORT"),
    ({"volume": 1.0, "shape": T.SPHERE, "mode": M.VOLUME, "envelope_diameter": 1.2},
     "ENVELOPE_DIAMETER_EXCEEDED"),
    ({"volume": 10.0, "shape": T.CYLINDER_HEMISPHERICAL, "mode": M.STATED_DIAMETER,
      "diameter": 1.0, "envelope_length": 5.0}, "ENVELOPE_LENGTH_EXCEEDED"),
    ({"volume": 0.0, "shape": T.SPHERE, "mode": M.VOLUME}, "VOLUME_INVALID"),
    ({"volume": math.nan, "shape": T.SPHERE, "mode": M.VOLUME}, "VOLUME_INVALID"),
    ({"volume": math.inf, "shape": T.SPHERE, "mode": M.VOLUME}, "VOLUME_INVALID"),
    ({"volume": 1.0, "shape": T.CYLINDER_HEMISPHERICAL, "mode": M.STATED_DIAMETER,
      "diameter": -1.0}, "DIAMETER_INVALID"),
    ({"volume": 1.0, "shape": T.CYLINDER_HEMISPHERICAL, "mode": M.STATED_DIAMETER,
      "diameter": math.nan}, "DIAMETER_INVALID"),
    ({"volume": 1.0, "shape": T.CYLINDER_ELLIPSOIDAL, "mode": M.STATED_LENGTH,
      "total_length": math.inf, "dome_ratio": 0.5}, "LENGTH_INVALID"),
    ({"volume": 1.0, "shape": T.CYLINDER_ELLIPSOIDAL, "mode": M.STATED_DIAMETER,
      "diameter": 1.0, "dome_ratio": 1.5}, "DOME_RATIO_INVALID"),
    ({"volume": 1.0, "shape": T.CYLINDER_ELLIPSOIDAL, "mode": M.STATED_DIAMETER,
      "diameter": 1.0, "dome_ratio": 0.0}, "DOME_RATIO_INVALID"),
    ({"volume": 1.0, "shape": T.SPHERE, "mode": M.VOLUME, "envelope_length": -2.0},
     "ENVELOPE_LENGTH_INVALID"),
])
def test_impossible_packaging_and_invalid_geometry_are_refused(kwargs, code):
    solution = rel.solve_tank_geometry(**kwargs)
    assert solution.value is None and solution.diagnostics[0].code == code


def test_ullage_and_density_mass_volume_closure_by_hand():
    v = rel.tank_volumes(1141.0, 1141.0, ullage_fraction=0.05).value
    assert v.liquid_volume == 1.0
    assert v.tank_volume == pytest.approx(1.0 / 0.95, rel=1e-15)
    assert v.ullage_volume == pytest.approx(1.0 / 0.95 - 1.0, rel=1e-14)
    assert v.fill_fraction == pytest.approx(0.95, rel=1e-15)
    v = rel.tank_volumes(845.2, 422.6, ullage_volume=0.25).value
    assert v.liquid_volume == 2.0 and v.tank_volume == 2.25
    assert v.ullage_fraction == pytest.approx(0.25 / 2.25, rel=1e-15)
    assert v.mass_closure == 0.0 and v.ullage_closure == 0.0
    assert rel.tank_volumes(1.0, 1.0, ullage_fraction=0.0).value.tank_volume == 1.0


@pytest.mark.parametrize("args,code", [
    ((0.0, 1.0), {"ullage_fraction": 0.1}),
    ((1.0, -1.0), {"ullage_fraction": 0.1}),
    ((1.0, 1.0), {"ullage_fraction": 1.0}),
    ((1.0, 1.0), {"ullage_fraction": -0.01}),
    ((1.0, 1.0), {"ullage_fraction": math.nan}),
    ((1.0, 1.0), {"ullage_volume": -1.0}),
    ((math.inf, 1.0), {"ullage_volume": 1.0}),
])
def test_invalid_volumes_are_refused(args, code):
    assert rel.tank_volumes(*args, **code).value is None


def test_ullage_is_stated_exactly_once():
    with pytest.raises(ValueError):
        rel.tank_volumes(1.0, 1.0)
    with pytest.raises(ValueError):
        rel.tank_volumes(1.0, 1.0, ullage_fraction=0.1, ullage_volume=0.1)


def test_parameter_grid_closes_everywhere():
    count = 0
    for mass, rho, u, shape in itertools.product(
            (5.0, 820.0, 6.4e4), (70.8, 422.6, 1141.0, 1440.0), (0.0, 0.03, 0.1, 0.45),
            ("sphere", "hemi_d", "hemi_l", "ell_d", "ell_l")):
        v = rel.tank_volumes(mass, rho, ullage_fraction=u).value
        assert abs(v.mass_closure) < 5e-16 and abs(v.ullage_closure) < 5e-16
        vol = v.tank_volume
        r_sphere = (3 * vol / (4 * math.pi)) ** (1 / 3)
        if shape == "sphere":
            g = rel.solve_tank_geometry(vol, T.SPHERE, M.VOLUME)
        elif shape.endswith("_d"):
            # A diameter 0.8 x the equal-volume sphere's always leaves a barrel.
            g = rel.solve_tank_geometry(vol, T.CYLINDER_HEMISPHERICAL if shape == "hemi_d"
                                        else T.CYLINDER_ELLIPSOIDAL, M.STATED_DIAMETER,
                                        diameter=1.6 * r_sphere,
                                        dome_ratio=None if shape == "hemi_d" else 0.6)
        else:
            g = rel.solve_tank_geometry(vol, T.CYLINDER_HEMISPHERICAL if shape == "hemi_l"
                                        else T.CYLINDER_ELLIPSOIDAL, M.STATED_LENGTH,
                                        total_length=3.0 * r_sphere,
                                        dome_ratio=None if shape == "hemi_l" else 0.6)
        g = g.value
        assert abs(g.volume_closure) < 2e-14, (mass, rho, u, shape)
        if g.barrel_length is not None:
            assert g.barrel_length >= 0.0
            assert g.total_length == pytest.approx(g.barrel_length + 2 * g.dome_height, rel=1e-14)
        count += 1
    assert count == 240


# ===========================================================================
# resolution, computation, records
# ===========================================================================


def tank_study(ox=OX, fuel=FUEL, inv=None) -> StudyResult:
    inv = inv or inventory()
    basis, issues = service.tanks_basis(inv, False)
    assert basis is not None, issues
    definition, issues = service.build_definition(basis, ox, fuel)
    assert definition is not None, issues
    return service.solve_tanks(definition)


def test_only_a_current_complete_inventory_drives_tanks(stub_gateway):
    complete = inventory()
    codes = lambda *a: [i.code for i in service.tanks_basis(*a)[1]]    # noqa: E731
    assert codes(None, False) == ["NO_INVENTORY"]
    assert codes(complete, True) == ["INVENTORY_STALE"]
    incomplete = inventory(inv_service.BranchSettings(), COMPLETE)
    assert codes(incomplete, False) == ["INVENTORY_INCOMPLETE"]
    basis, issues = service.tanks_basis(complete, False)
    assert issues == () and basis.oxidiser_loaded_mass == complete.oxidiser.value("loaded_mass")
    assert basis.inventory.gate == "SYS-1"
    assert basis.inventory.fingerprint == complete.definition.fingerprint


def test_nothing_is_defaulted(stub_gateway):
    basis, _ = service.tanks_basis(inventory(), False)
    definition, issues = service.build_definition(basis, service.BranchSettings(),
                                                  service.BranchSettings())
    codes = {i.code for i in issues}
    assert definition is None
    assert {"DENSITY_UNRESOLVED", "ULLAGE_UNRESOLVED", "SHAPE_UNRESOLVED"} <= codes
    _d, issues = service.build_definition(
        basis, replace(OX, shape=TankShape.CYLINDER_HEMISPHERICAL), FUEL)
    assert [i.code for i in issues] == ["SIZING_MODE_UNRESOLVED"]


@pytest.mark.parametrize("change,code", [
    ({"density": -1.0}, "DENSITY_INVALID"),
    ({"density": math.nan}, "DENSITY_INVALID"),
    ({"ullage_value": 1.0}, "ULLAGE_INVALID"),
    ({"ullage_value": None}, "ULLAGE_UNRESOLVED"),
    ({"envelope_diameter": 0.0}, "ENVELOPE_INVALID"),
    ({"density_source": DensitySource.FLUID_MODEL}, "STORAGE_TEMPERATURE_UNRESOLVED"),
])
def test_invalid_inputs_are_refused_not_clamped(stub_gateway, change, code):
    basis, _ = service.tanks_basis(inventory(), False)
    _d, issues = service.build_definition(basis, replace(OX, **change), FUEL)
    assert code in [i.code for i in issues]


def test_tanks_hold_the_loaded_masses(stub_gateway):
    inv = inventory()
    result = tank_study(inv=inv)
    assert result.status is StudyStatus.OK
    ox, fu = result.oxidiser, result.fuel
    mo = inv.oxidiser.value("loaded_mass")
    assert ox.value("liquid_volume") == pytest.approx(mo / 1141.0, rel=1e-15)
    assert ox.value("tank_volume") == pytest.approx(mo / 1141.0 / 0.95, rel=1e-15)
    assert ox.value("diameter") == pytest.approx(
        2 * (3 * mo / 1141.0 / 0.95 / (4 * math.pi)) ** (1 / 3), rel=1e-15)
    assert "barrel_length" in ox.unresolved and ox.labels["shape"] == "Sphere"
    mf = inv.fuel.value("loaded_mass")
    vt = mf / 422.6 + 2.0
    assert fu.value("tank_volume") == pytest.approx(vt, rel=1e-15)
    barrel = (vt - 4.0 / 3.0 * math.pi * K * 8.0) / (math.pi * 4.0)
    assert fu.value("barrel_length") == pytest.approx(barrel, rel=1e-13)
    assert result.totals["tank_volume_total"] == pytest.approx(
        ox.value("tank_volume") + vt, rel=1e-15)


def test_a_tank_that_cannot_hold_the_load_refuses_the_study(stub_gateway):
    result = tank_study(fuel=replace(FUEL, diameter=40.0))
    assert result.status is StudyStatus.REFUSED and not result.totals
    assert "domes alone" in result.fuel.message
    assert result.oxidiser.ok


def test_fluid_model_density_needs_a_validated_binding(stub_gateway, monkeypatch):
    from rocketforge.application.analysis import fluid_property_provider as gateway

    class Absent:
        is_usable = False
        detail = "CoolProp is not installed."

    monkeypatch.setattr(gateway, "availability", lambda: Absent())
    ox = replace(OX, density_source=DensitySource.FLUID_MODEL, density=None,
                 storage_temperature=90.0, storage_pressure=3.0e5)
    result = tank_study(ox=ox)
    assert result.status is StudyStatus.REFUSED
    assert "No validated fluid model" in result.oxidiser.message


def test_records_round_trip_and_are_fingerprint_checked(stub_gateway):
    result = tank_study()
    text = result.to_json()
    assert StudyResult.from_json(text, TANK_SCHEMA) == result
    assert tank_study().to_json() == text
    record = json.loads(text)
    assert record["definition"]["basis"]["inventory"]["gate"] == "SYS-1"
    record["definition"]["fuel"]["diameter_m"] = 4.5
    with pytest.raises(RequirementFormatError, match="fingerprint"):
        StudyResult.from_dict(record, TANK_SCHEMA)


def test_display_units(stub_gateway):
    rows = {r["key"]: r for g in service.branch_view(tank_study().oxidiser)["groups"]
            for r in g["rows"]}
    assert rows["ullage_fraction"]["value"] == "5.0000" and rows["ullage_fraction"]["unit"] == "%"
    assert rows["tank_volume"]["unit"] == "m³"
