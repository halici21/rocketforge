"""The nozzle as a 3D view reads it: one immutable snapshot per solved state.

Made once, when the nozzle is solved, from the solution record -- the same
record the 2D drawing, the charts and the table read. It carries the revolved
profile, the stations a view marks (throat, exit and, only when the solution
has one, the quasi-1D shock station), each station's solved readings for the
inspector, and what the picture may claim. JSON-serializable: plain numbers,
strings, lists and dicts, never a QObject.

The shock station is a plane at the solved x. It is not a shock thickness and
not a resolved shock structure: the solver places a discontinuity at one
station of a quasi-one-dimensional flow, and that is all the plane says.
"""
from __future__ import annotations

import math

from ..formatting import format_engineering
from .fidelity import FLOW_LABEL, Fidelity
from .geometry import GeometryError, Profile, profile_from_area, radius_at

__all__ = ["nozzle_viewport", "EMPTY_VIEWPORT", "SUPPLIED_CONE_LABEL", "SHOCK_LABEL",
           "SCHEMATIC_LABEL", "schematic_viewport", "schematic_profile"]

SUPPLIED_CONE_LABEL = "SUPPLIED CONE, NOT A DESIGNED CONTOUR"
SHOCK_LABEL = "QUASI-1D NORMAL SHOCK STATION, NOT A RESOLVED SHOCK"
SCHEMATIC_LABEL = "SCHEMATIC GEOMETRY — AREA EXPANSION ONLY, NOT A SOLVED CONTOUR"

EMPTY_VIEWPORT: dict = {"identity": 0, "valid": False, "stations": [], "profile": {"x": [], "r": []}}


def _row(label: str, value: float | None, unit: str = "", precision: int = 6) -> dict:
    if value is None or not math.isfinite(float(value)):
        return {"label": label, "value": "—", "unit": unit, "raw": None}
    return {"label": label, "value": format_engineering(float(value), precision),
            "unit": unit, "raw": float(value)}


def _station(key: str, title: str, x: float, profile: Profile, rows: list[dict],
             note: str = "") -> dict:
    return {"key": key, "title": title, "x": float(x), "r": radius_at(profile, float(x)),
            "u": (float(x) - profile.x_min) / (profile.x_max - profile.x_min),
            "rows": rows, "note": note}


def nozzle_viewport(record, identity: int, precision: int = 6) -> dict:
    """The viewport snapshot of a solved nozzle (``NozzleSolution``)."""
    if record is None:
        return dict(EMPTY_VIEWPORT, identity=int(identity))
    try:
        profile = profile_from_area(record.x, record.area)
    except GeometryError as error:
        return dict(EMPTY_VIEWPORT, identity=int(identity), error=str(error))

    def at(array, index):
        return None if array is None else float(array[index])

    it = int(record.throat_index)
    ie = len(record.x) - 1
    stations = [
        _station("throat", "Throat", record.x[it], profile, [
            _row("M", at(record.mach, it), "", precision),
            _row("A/A_t", at(record.area_ratio, it), "", precision),
            _row("p/p_01", at(record.pressure_ratio, it), "", precision),
            _row("T/T_01", at(record.temperature_ratio, it), "", precision),
            _row("x", at(record.x, it), "m", precision),
        ], "sonic — the flow is choked" if record.choked else "subsonic — not choked"),
        _station("exit", "Exit plane", record.x[ie], profile, [
            _row("M_e", at(record.mach, ie), "", precision),
            _row("A_e/A_t", at(record.area_ratio, ie), "", precision),
            _row("p_e/p_01", at(record.pressure_ratio, ie), "", precision),
            _row("T_e/T_01", at(record.temperature_ratio, ie), "", precision),
            _row("x", at(record.x, ie), "m", precision),
        ]),
    ]
    shock = record.shock
    if shock is not None and shock.x is not None:
        stations.append(_station("shock", "Shock station", shock.x, profile, [
            _row("A_s/A_t", shock.area_ratio_shock, "", precision),
            _row("M_1", shock.mach_upstream, "", precision),
            _row("M_2", shock.mach_downstream, "", precision),
            _row("p_2/p_1", shock.pressure_ratio, "", precision),
            _row("p_02/p_01", shock.stagnation_pressure_ratio, "", precision),
            _row("x_s", shock.x, "m", precision),
        ], SHOCK_LABEL))
    return {
        "identity": int(identity),
        "valid": True,
        "fidelity": str(Fidelity.DERIVED),
        "label": SUPPLIED_CONE_LABEL,
        "profile": profile.to_dict(),
        "extent": {"xMin": profile.x_min, "xMax": profile.x_max, "rMax": profile.r_max,
                   "rThroat": radius_at(profile, float(record.x[it]))},
        "stations": stations,
        "hasShock": any(s["key"] == "shock" for s in stations),
        "choked": bool(record.choked),
        "flow": {"gas": True, "liquidInlet": False, "condensed": False,
                 "condensedFraction": None, "condensedLabel": "",
                 "speed": "uniform", "label": FLOW_LABEL},
    }


#: The 2D performance canvas's proportions, in exit radii: chamber from 0 to
#: CHAMBER_END, contraction to THROAT_X, expansion to EXIT_X. Arbitrary axial
#: scale, as on the canvas; only the throat radius comes from a solved number.
CHAMBER_END = 0.856
THROAT_X = 1.833
EXIT_X = 5.011


def _bezier(p0, p1, p2, p3, n):
    out = []
    for k in range(n + 1):
        s = k / n
        u = 1.0 - s
        x = u ** 3 * p0[0] + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s ** 3 * p3[0]
        r = u ** 3 * p0[1] + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s ** 3 * p3[1]
        out.append((x, r))
    return out


def schematic_profile(radius_ratio: float, samples: int = 32) -> Profile:
    """The Rocket Performance schematic, exactly as its 2D canvas draws it.

    Exit radius 1 and throat radius 1 / radius_ratio (r_e/r_t = sqrt of the
    solved area ratio); a cylindrical chamber and two Bezier walls with the
    canvas's own control points. A schematic of area expansion, not a contour.
    """
    if not (math.isfinite(radius_ratio) and radius_ratio >= 1.0):
        raise ValueError("a radius ratio of at least 1 is needed")
    exit_r = 1.0
    throat_r = exit_r / radius_ratio
    chamber_r = min(throat_r * 2.8, exit_r * 0.80)
    pts = [(0.0, chamber_r)]
    pts += _bezier((CHAMBER_END, chamber_r),
                   (CHAMBER_END + (THROAT_X - CHAMBER_END) * 0.55, chamber_r),
                   (THROAT_X - (THROAT_X - CHAMBER_END) * 0.35, throat_r),
                   (THROAT_X, throat_r), samples)
    pts += _bezier((THROAT_X, throat_r),
                   (THROAT_X + (EXIT_X - THROAT_X) * 0.22, throat_r),
                   (THROAT_X + (EXIT_X - THROAT_X) * 0.45, exit_r * 0.86),
                   (EXIT_X, exit_r), samples)[1:]
    xs, rs = [], []
    for x, r in pts:
        if xs and x <= xs[-1]:
            continue
        xs.append(x)
        rs.append(r)
    return Profile(tuple(xs), tuple(rs))


def schematic_viewport(area_ratio: float, identity: int, *, liquid_inlet: bool,
                       condensed_fraction: float | None, condensed_label: str) -> dict:
    """A schematic nozzle for a case whose result carries no contour.

    Rocket Performance solves the ideal expansion from a chamber state and an
    area ratio; it has no wall. The shape here is the one its 2D canvas draws
    -- a fixed exit radius with the throat set by the solved area ratio -- and
    it is labelled schematic. Only the area ratio is a solved number.
    """
    if not (math.isfinite(area_ratio) and area_ratio >= 1.0):
        return dict(EMPTY_VIEWPORT, identity=int(identity), error="no solved area ratio")
    profile = schematic_profile(math.sqrt(area_ratio))
    throat_r = radius_at(profile, THROAT_X)
    stations = [
        {"key": "throat", "title": "Throat", "x": THROAT_X, "r": throat_r,
         "u": THROAT_X / EXIT_X, "rows": [], "note": "sonic \u2014 the flow is choked"},
        {"key": "exit", "title": "Exit plane", "x": EXIT_X, "r": 1.0, "u": 1.0,
         "rows": [_row("A_e/A_t", area_ratio)], "note": ""},
    ]
    has_condensed = condensed_fraction is not None and condensed_fraction > 0.0
    return {
        "identity": int(identity),
        "valid": True,
        "fidelity": str(Fidelity.SCHEMATIC),
        "label": SCHEMATIC_LABEL,
        "profile": profile.to_dict(),
        "extent": {"xMin": 0.0, "xMax": EXIT_X, "rMax": profile.r_max, "rThroat": throat_r},
        # The 2D canvas closes the chamber at its face; so does the 3D one.
        "capStart": True,
        "stations": stations,
        "hasShock": False,
        "choked": True,
        "flow": {"gas": True, "liquidInlet": bool(liquid_inlet), "condensed": has_condensed,
                 "condensedFraction": condensed_fraction if has_condensed else None,
                 "condensedLabel": condensed_label if has_condensed else "",
                 "speed": "uniform", "label": FLOW_LABEL},
    }
