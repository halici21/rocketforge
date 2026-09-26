"""The shared revolver and the nozzle viewport snapshot.

Exact expectations come from the solver record itself: the throat, exit and
shock stations the 3D view marks must be the record's own, the radius must be
sqrt(A/pi) of the record's area at those stations, and a mesh must be finite,
bounded and well-indexed. Invalid geometry must fail, never clamp.
"""
from __future__ import annotations

import json
import math

import pytest

from rocketforge.application.analysis.nozzle_controller import NozzleController
from rocketforge.application.visualization import geometry as g
from rocketforge.application.visualization.fidelity import Fidelity, label
from rocketforge.application.visualization.viewport import (
    SCHEMATIC_LABEL, SUPPLIED_CONE_LABEL, nozzle_viewport, schematic_viewport)


# ---------------------------------------------------------------------------
# the revolver
# ---------------------------------------------------------------------------

CONE = g.profile_from_radius([0.0, 1.0, 2.5], [0.5, 0.25, 0.4])


def test_revolve_produces_a_finite_well_indexed_bounded_mesh():
    mesh = g.revolve(CONE, segments=24)
    assert mesh.rings == 3 and mesh.segments == 24
    assert mesh.vertex_count == 3 * 25
    assert mesh.triangle_count == 2 * 2 * 24
    assert all(math.isfinite(v) for v in mesh.positions + mesh.normals)
    assert all(0 <= i < mesh.vertex_count for i in mesh.indices)
    # no degenerate triangle
    p = mesh.positions
    for t in range(mesh.triangle_count):
        a, b, c = mesh.indices[3 * t:3 * t + 3]
        assert len({a, b, c}) == 3
        va = p[3 * a:3 * a + 3]; vb = p[3 * b:3 * b + 3]; vc = p[3 * c:3 * c + 3]
        ab = [vb[i] - va[i] for i in range(3)]; ac = [vc[i] - va[i] for i in range(3)]
        cross = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2],
                 ab[0] * ac[1] - ab[1] * ac[0])
        assert math.hypot(*cross) > 0.0
    assert mesh.bounds_min == (0.0, -0.5, -0.5) and mesh.bounds_max == (2.5, 0.5, 0.5)


def test_every_vertex_lies_on_the_wall_radius_of_its_station():
    mesh = g.revolve(CONE, segments=16)
    for k in range(mesh.vertex_count):
        x, y, z = mesh.positions[3 * k:3 * k + 3]
        assert math.isclose(math.hypot(y, z), g.radius_at(CONE, x), rel_tol=1e-12)
        nx, ny, nz = mesh.normals[3 * k:3 * k + 3]
        assert math.isclose(math.sqrt(nx * nx + ny * ny + nz * nz), 1.0, rel_tol=1e-12)


def test_the_cutaway_keeps_the_far_half_open_to_the_camera():
    half = g.revolve(CONE, segments=16, sweep_degrees=180)
    assert half.sweep_degrees == 180.0
    zs = half.positions[2::3]
    assert max(zs) <= 1e-12 and min(zs) < 0


def test_radius_is_sqrt_area_over_pi_and_exact_at_stations():
    profile = g.profile_from_area([0.0, 1.0, 2.0], [0.02, 0.01, 0.03])
    assert profile.r == tuple(math.sqrt(a / math.pi) for a in (0.02, 0.01, 0.03))
    assert g.radius_at(profile, 1.0) == profile.r[1]
    assert math.isclose(g.radius_at(profile, 1.5), 0.5 * (profile.r[1] + profile.r[2]))


def test_a_duplicated_shock_station_collapses_to_one_wall_station():
    profile = g.profile_from_area([0.0, 1.0, 1.0, 2.0], [0.02, 0.01, 0.01, 0.03])
    assert profile.x == (0.0, 1.0, 2.0)


@pytest.mark.parametrize("x, area", [
    ([0.0, 1.0], [0.01, -0.01]),               # negative area
    ([0.0, 1.0], [0.01, float("nan")]),        # not finite
    ([0.0, 0.0], [0.01, 0.02]),                # same station, different area
    ([1.0, 0.0], [0.01, 0.02]),                # decreasing x
    ([0.0], [0.01]),                           # one station
])
def test_invalid_geometry_fails_rather_than_clamping(x, area):
    with pytest.raises(g.GeometryError):
        g.profile_from_area(x, area)


def test_a_station_outside_the_profile_is_an_error_not_an_extrapolation():
    with pytest.raises(g.GeometryError):
        g.radius_at(CONE, 3.0)


def test_a_fine_grid_is_bounded_and_keeps_marked_stations():
    xs = [i * 0.001 for i in range(2001)]
    rs = [0.2 + 0.1 * abs(x - 1.0) for x in xs]
    profile = g.profile_from_radius(xs, rs)
    keep = (0.137, 1.0)
    mesh = g.revolve(profile, segments=8, keep=keep)
    assert mesh.rings == g.MAX_RINGS
    ring_x = {round(mesh.positions[3 * (i * 9)], 12) for i in range(mesh.rings)}
    assert 0.137 in ring_x and 1.0 in ring_x and 0.0 in ring_x and 2.0 in ring_x


def test_revolve_is_deterministic():
    assert g.revolve(CONE) == g.revolve(CONE)


# ---------------------------------------------------------------------------
# the nozzle viewport snapshot, against the solver's own record
# ---------------------------------------------------------------------------


@pytest.fixture()
def nozzle(qt_app):
    return NozzleController()


def _station(snapshot, key):
    return next((s for s in snapshot["stations"] if s["key"] == key), None)


def test_viewport_stations_are_the_records_own(nozzle):
    record = nozzle._record
    snap = nozzle_viewport(record, identity=7)
    assert snap["identity"] == 7 and snap["valid"]
    assert snap["fidelity"] == str(Fidelity.DERIVED)
    assert snap["label"] == SUPPLIED_CONE_LABEL
    throat = _station(snap, "throat")
    assert throat["x"] == float(record.x[record.throat_index])
    assert throat["r"] == math.sqrt(float(record.area[record.throat_index]) / math.pi)
    exit_ = _station(snap, "exit")
    assert exit_["x"] == float(record.x[-1])
    assert math.isclose(exit_["r"], math.sqrt(float(record.area[-1]) / math.pi), rel_tol=1e-15)
    # the default operating point has an internal shock
    assert record.shock is not None
    shock = _station(snap, "shock")
    assert shock["x"] == float(record.shock.x)
    rows = {r["label"]: r["raw"] for r in shock["rows"]}
    assert rows["M_1"] == record.shock.mach_upstream
    assert rows["M_2"] == record.shock.mach_downstream
    assert rows["p_02/p_01"] == record.shock.stagnation_pressure_ratio
    assert rows["A_s/A_t"] == record.shock.area_ratio_shock


def test_no_shock_station_without_a_solved_shock(nozzle):
    nozzle.backPressureRatio = 0.05              # underexpanded: no internal shock
    assert not nozzle.hasShock
    snap = nozzle_viewport(nozzle._record, identity=1)
    assert _station(snap, "shock") is None and snap["hasShock"] is False


def test_a_choked_throat_is_a_normal_state_not_a_warning(nozzle):
    snap = nozzle_viewport(nozzle._record, identity=1)
    throat = _station(snap, "throat")
    assert snap["choked"] is True
    assert throat["note"].startswith("sonic") and "warning" not in throat["note"].lower()
    mach = next(r for r in throat["rows"] if r["label"] == "M")
    assert math.isclose(mach["raw"], 1.0, rel_tol=1e-9)


def test_the_snapshot_is_json_serializable_and_carries_no_objects(nozzle):
    snap = nozzle_viewport(nozzle._record, identity=3)
    assert json.loads(json.dumps(snap, allow_nan=False)) == snap


def test_no_record_gives_an_empty_invalid_snapshot():
    snap = nozzle_viewport(None, identity=4)
    assert snap["valid"] is False and snap["stations"] == []


def test_the_schematic_viewport_is_labelled_schematic_and_uses_only_the_area_ratio():
    snap = schematic_viewport(40.0, 1, liquid_inlet=True, condensed_fraction=None,
                              condensed_label="")
    assert snap["fidelity"] == str(Fidelity.SCHEMATIC) and snap["label"] == SCHEMATIC_LABEL
    throat, exit_ = _station(snap, "throat"), _station(snap, "exit")
    assert math.isclose((exit_["r"] / throat["r"]) ** 2, 40.0, rel_tol=1e-12)
    assert snap["flow"]["condensed"] is False and snap["flow"]["liquidInlet"] is True
    solid = schematic_viewport(10.0, 2, liquid_inlet=False, condensed_fraction=0.168,
                               condensed_label="Al2O3(L)")
    assert solid["flow"]["condensed"] and solid["flow"]["condensedFraction"] == 0.168


def test_every_fidelity_class_has_a_label():
    assert {label(k) for k in Fidelity} == {
        "Supplied geometry", "Derived presentation geometry", "Schematic geometry",
        "Qualitative flow cues"}


# ---------------------------------------------------------------------------
# the chamber face, and the Rocket Performance schematic
# ---------------------------------------------------------------------------

def test_a_capped_start_closes_the_first_station_with_a_flat_disc():
    open_ = g.revolve(CONE, segments=16)
    capped = g.revolve(CONE, segments=16, cap_start=True)
    # the wall is untouched; the disc adds a centre, one ring and a fan
    assert capped.positions[:len(open_.positions)] == open_.positions
    assert capped.vertex_count == open_.vertex_count + 1 + 17
    assert capped.triangle_count == open_.triangle_count + 16
    for k in range(open_.vertex_count, capped.vertex_count):
        x, y, z = capped.positions[3 * k:3 * k + 3]
        assert x == CONE.x[0] and math.hypot(y, z) <= CONE.r[0] * (1 + 1e-12)
        assert capped.normals[3 * k:3 * k + 3] == (-1.0, 0.0, 0.0)
    half = g.revolve(CONE, segments=16, sweep_degrees=180, cap_start=True)
    assert max(half.positions[2::3]) <= 1e-12        # the cutaway cuts the face too


def test_the_schematic_profile_is_the_2d_canvas_shape():
    from rocketforge.application.visualization.viewport import (
        EXIT_X, THROAT_X, schematic_profile)
    for ratio in (1.5, math.sqrt(40.0), 12.0):
        p = schematic_profile(ratio)
        assert all(b > a for a, b in zip(p.x, p.x[1:]))
        assert p.x[0] == 0.0 and p.x[-1] == EXIT_X and p.r[-1] == 1.0
        assert math.isclose(g.radius_at(p, THROAT_X), 1.0 / ratio, rel_tol=1e-12)
        assert math.isclose(min(p.r), 1.0 / ratio, rel_tol=1e-12)    # the throat is the minimum
        assert math.isclose(p.r[0], min(2.8 / ratio, 0.8), rel_tol=1e-12)
    with pytest.raises(ValueError):
        schematic_profile(0.9)


def test_the_schematic_snapshot_closes_the_chamber_and_the_supplied_cone_does_not(nozzle):
    snap = schematic_viewport(40.0, 1, liquid_inlet=False, condensed_fraction=None,
                              condensed_label="")
    assert snap["capStart"] is True
    assert nozzle_viewport(nozzle._record, identity=1).get("capStart", False) is False
    assert schematic_viewport(0.5, 3, liquid_inlet=False, condensed_fraction=None,
                              condensed_label="")["valid"] is False
