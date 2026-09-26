"""Axisymmetric surfaces from a radius distribution -- one path for every view.

A nozzle the solver describes by area at axial stations is drawn in 3D by
revolving ``r(x) = sqrt(A(x) / pi)`` about the axis. That is derived
presentation geometry: exactly the supplied distribution, turned into a
surface, with no curvature, bell or contour added that the case does not
carry. Nozzle Lab and Rocket Performance both build their surfaces here, so
there is one revolver and it is tested once.

Invalid geometry fails loudly (:class:`GeometryError`) rather than being
clamped into something drawable: a negative area or a non-finite station
means the input is wrong, and a picture of it would hide that.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = ["GeometryError", "Profile", "Mesh", "profile_from_area",
           "profile_from_radius", "radius_at", "revolve", "ring",
           "MAX_RINGS", "DEFAULT_SEGMENTS"]

#: Upper bound on axial rings in one mesh. A profile with more stations is
#: resampled at exactly this many of its own stations (always keeping the
#: first, last and every station a view marks), so a fine solver grid cannot
#: produce an unbounded mesh.
MAX_RINGS = 240

#: Segments around the circumference for a full revolution.
DEFAULT_SEGMENTS = 72


class GeometryError(ValueError):
    """The distribution cannot be drawn honestly."""


@dataclass(frozen=True, slots=True)
class Profile:
    """Wall radius at axial stations, ``x`` strictly increasing."""

    x: tuple[float, ...]
    r: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.x) != len(self.r):
            raise GeometryError("x and r differ in length")
        if len(self.x) < 2:
            raise GeometryError("a surface needs at least two stations")
        for value in self.x + self.r:
            if not math.isfinite(value):
                raise GeometryError("a station or radius is not finite")
        for a, b in zip(self.x, self.x[1:]):
            if not b > a:
                raise GeometryError("axial stations must increase strictly")
        for value in self.r:
            if not value > 0.0:
                raise GeometryError("every radius must be positive")

    @property
    def x_min(self) -> float:
        return self.x[0]

    @property
    def x_max(self) -> float:
        return self.x[-1]

    @property
    def r_max(self) -> float:
        return max(self.r)

    def to_dict(self) -> dict:
        return {"x": list(self.x), "r": list(self.r)}


def profile_from_radius(x, r) -> Profile:
    """A profile from explicit radii."""
    return Profile(tuple(float(v) for v in x), tuple(float(v) for v in r))


def profile_from_area(x, area) -> Profile:
    """A profile from area at stations, ``r = sqrt(A / pi)``.

    A solved nozzle carries one duplicated station where a shock stands (the
    pre- and post-shock states at the same ``x``); the wall is the same wall
    on both sides, so exactly-equal consecutive stations with equal area
    collapse to one. Equal ``x`` with different area is a geometry error.
    """
    xs, rs = [], []
    for xi, ai in zip(x, area):
        xi, ai = float(xi), float(ai)
        if not math.isfinite(ai) or ai <= 0.0:
            raise GeometryError("every area must be positive and finite")
        ri = math.sqrt(ai / math.pi)
        if xs and xi == xs[-1]:
            if ri != rs[-1]:
                raise GeometryError("two different areas at the same station")
            continue
        xs.append(xi)
        rs.append(ri)
    return Profile(tuple(xs), tuple(rs))


def radius_at(profile: Profile, x: float) -> float:
    """Wall radius at ``x``: exact at a supplied station, linear between.

    Between two supplied stations of a straight-walled (conical) section the
    wall is straight, so linear interpolation of r is the wall itself there.
    Outside the profile is an error, not an extrapolation.
    """
    if not math.isfinite(x) or x < profile.x_min or x > profile.x_max:
        raise GeometryError("station outside the profile")
    xs, rs = profile.x, profile.r
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    if x == xs[lo]:
        return rs[lo]
    if x == xs[hi]:
        return rs[hi]
    t = (x - xs[lo]) / (xs[hi] - xs[lo])
    return rs[lo] + t * (rs[hi] - rs[lo])


@dataclass(frozen=True, slots=True)
class Mesh:
    """Interleaved-ready triangle mesh of a surface of revolution about +x."""

    positions: tuple[float, ...]     # x, y, z per vertex
    normals: tuple[float, ...]       # unit outward normal per vertex
    indices: tuple[int, ...]         # three per triangle
    rings: int
    segments: int
    sweep_degrees: float
    bounds_min: tuple[float, float, float]
    bounds_max: tuple[float, float, float]

    @property
    def vertex_count(self) -> int:
        return len(self.positions) // 3

    @property
    def triangle_count(self) -> int:
        return len(self.indices) // 3


def _resample(profile: Profile, keep: tuple[float, ...]) -> Profile:
    n = len(profile.x)
    if n <= MAX_RINGS:
        return profile
    wanted = {0, n - 1}
    for value in keep:
        for i, xi in enumerate(profile.x):
            if xi == value:
                wanted.add(i)
    budget = MAX_RINGS - len(wanted)
    step = (n - 1) / max(1, budget + 1)
    k = 1
    while len(wanted) < MAX_RINGS and k * step < n - 1:
        wanted.add(int(round(k * step)))
        k += 1
    order = sorted(wanted)
    return Profile(tuple(profile.x[i] for i in order), tuple(profile.r[i] for i in order))


def revolve(profile: Profile, segments: int = DEFAULT_SEGMENTS,
            sweep_degrees: float = 360.0, keep: tuple[float, ...] = (),
            cap_start: bool = False) -> Mesh:
    """Revolve ``profile`` about the +x axis.

    ``sweep_degrees`` below 360 gives the half-revolution cutaway (180): the
    open side faces the viewer's default iso camera so the centreline and the
    stations on it are visible. ``keep`` lists axial stations that survive
    any resampling. ``cap_start`` closes the first station with a flat disc
    facing -x (a chamber's closed face), swept like the wall.
    """
    if segments < 3:
        raise GeometryError("a revolution needs at least three segments")
    if not 0.0 < sweep_degrees <= 360.0:
        raise GeometryError("sweep must be in (0, 360] degrees")
    p = _resample(profile, keep)
    sweep = math.radians(sweep_degrees)
    # A part-revolution keeps the far half (z <= 0 for 180 degrees), so the
    # open side faces a camera on the +z side and shows the axis.
    start = math.pi if sweep_degrees < 360.0 else 0.0
    cols = segments + 1
    rings = len(p.x)
    positions: list[float] = []
    normals: list[float] = []
    for i in range(rings):
        x, r = p.x[i], p.r[i]
        x0, r0 = p.x[max(i - 1, 0)], p.r[max(i - 1, 0)]
        x1, r1 = p.x[min(i + 1, rings - 1)], p.r[min(i + 1, rings - 1)]
        dx, dr = x1 - x0, r1 - r0
        length = math.hypot(dx, dr)
        nx, nr = -dr / length, dx / length
        for j in range(cols):
            a = start + sweep * j / segments
            c, s = math.cos(a), math.sin(a)
            positions += (x, r * c, r * s)
            normals += (nx, nr * c, nr * s)
    indices: list[int] = []
    for i in range(rings - 1):
        for j in range(segments):
            a = i * cols + j
            b = a + cols
            indices += (a, b, a + 1, a + 1, b, b + 1)
    if cap_start:
        # Own vertices, so the disc shades flat instead of borrowing the
        # wall's normals: a centre and one ring at the first station.
        centre = rings * cols
        x, r = p.x[0], p.r[0]
        positions += (x, 0.0, 0.0)
        normals += (-1.0, 0.0, 0.0)
        for j in range(cols):
            a = start + sweep * j / segments
            positions += (x, r * math.cos(a), r * math.sin(a))
            normals += (-1.0, 0.0, 0.0)
        for j in range(segments):
            indices += (centre, centre + 2 + j, centre + 1 + j)
    rmax = p.r_max
    return Mesh(tuple(positions), tuple(normals), tuple(indices), rings, segments,
                float(sweep_degrees), (p.x_min, -rmax, -rmax), (p.x_max, rmax, rmax))


def ring(radius: float, tube: float, segments: int = DEFAULT_SEGMENTS, sides: int = 10) -> Mesh:
    """A thin torus in the y-z plane at x = 0: a station ring on the wall.

    ``radius`` is the wall radius at the station, ``tube`` the drawn line
    weight. It marks where a station is; it has no physical thickness.
    """
    if not (math.isfinite(radius) and radius > 0.0 and math.isfinite(tube) and tube > 0.0):
        raise GeometryError("a ring needs a positive radius and tube")
    if segments < 3 or sides < 3:
        raise GeometryError("a ring needs at least three segments and sides")
    positions: list[float] = []
    normals: list[float] = []
    for j in range(segments + 1):
        theta = 2 * math.pi * j / segments
        ct, st = math.cos(theta), math.sin(theta)
        for i in range(sides + 1):
            phi = 2 * math.pi * i / sides
            cp, sp = math.cos(phi), math.sin(phi)
            positions += (tube * sp, (radius + tube * cp) * ct, (radius + tube * cp) * st)
            normals += (sp, cp * ct, cp * st)
    indices: list[int] = []
    cols = sides + 1
    for j in range(segments):
        for i in range(sides):
            a = j * cols + i
            b = a + cols
            indices += (a, b, a + 1, a + 1, b, b + 1)
    extent = radius + tube
    return Mesh(tuple(positions), tuple(normals), tuple(indices), segments + 1, sides,
                360.0, (-tube, -extent, -extent), (tube, extent, extent))
