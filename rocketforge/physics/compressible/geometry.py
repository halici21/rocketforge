"""Quasi-1D duct geometry: area as a function of axial position.

Specified in ``docs/engineering/02_data_model_and_api_contracts.md`` section 1.6
and ``03`` section 10.2. This module carries **geometry only** -- no gas, no
pressure, no regime. It exists so the nozzle solver can be handed a contour it
did not invent, which is the boundary task section 61 asks for: RocketForge
analyses a supplied area distribution and never generates a design contour.

**Interpolation is shape-preserving monotone cubic (PCHIP).** A natural cubic
spline overshoots near a throat and can manufacture a second, spurious minimum
between two supplied stations -- which would silently break the regime
classifier, because the classifier's whole premise is that there is exactly one
sonic point. Fritsch-Carlson slope limiting cannot overshoot by construction, so
the interpolant has no extremum the supplied data does not have. That is the
reason for writing the algorithm out here rather than reaching for SciPy, quite
apart from SciPy being barred from the runtime.

**What is validated where.** The constructor accepts any physically meaningful
duct, including a monotone one: a converging nozzle is a real device and this
class describes it correctly. The extra requirement of a genuine
converging-diverging passage -- one interior minimum, exit area above throat
area -- is a requirement of the *C-D solver*, and is checked by
:meth:`AreaDistribution.require_converging_diverging`, which the nozzle module
calls. Keeping the two apart means the data model does not quietly refuse to
represent a duct that some other analysis might legitimately want.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ...core.errors import GeometryError, InputError
from ...core.numerics.arrays import as_float_array, restore_scalar

__all__ = ["AreaDistribution", "pchip_slopes", "pchip_evaluate"]


# ---------------------------------------------------------------------------
# monotone cubic interpolation
# ---------------------------------------------------------------------------


def pchip_slopes(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Fritsch-Carlson derivatives for shape-preserving cubic interpolation.

    The interior rule is the weighted harmonic mean of the two neighbouring
    secant slopes, which is zero whenever they differ in sign. That single
    property is what forbids overshoot: the interpolant cannot rise above the
    larger of two bracketing samples, so it cannot invent a minimum between two
    stations of a nozzle contour.

    Args:
        x: Strictly increasing abscissae, shape ``(n,)``, ``n >= 2``.
        y: Ordinates, shape ``(n,)``.

    Returns:
        Derivative at each sample, shape ``(n,)``.
    """
    h = np.diff(x)
    delta = np.diff(y) / h
    n = x.size
    slopes = np.zeros(n, dtype=float)

    if n == 2:
        slopes[:] = delta[0]
        return slopes

    # Interior: harmonic mean, weighted by the neighbouring intervals, and
    # exactly zero at a local extremum of the data.
    left, right = delta[:-1], delta[1:]
    turning = left * right <= 0.0
    w1 = 2.0 * h[1:] + h[:-1]
    w2 = h[1:] + 2.0 * h[:-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        harmonic = (w1 + w2) / (w1 / np.where(turning, 1.0, left)
                                + w2 / np.where(turning, 1.0, right))
    slopes[1:-1] = np.where(turning, 0.0, harmonic)

    slopes[0] = _edge_slope(h[0], h[1], delta[0], delta[1])
    slopes[-1] = _edge_slope(h[-1], h[-2], delta[-1], delta[-2])
    return slopes


def _edge_slope(h0: float, h1: float, delta0: float, delta1: float) -> float:
    """One-sided three-point derivative, clipped so the end cannot overshoot."""
    slope = ((2.0 * h0 + h1) * delta0 - h0 * delta1) / (h0 + h1)
    if slope * delta0 <= 0.0:
        return 0.0
    if delta0 * delta1 <= 0.0 and abs(slope) > abs(3.0 * delta0):
        return 3.0 * delta0
    return slope


def pchip_evaluate(x: np.ndarray, y: np.ndarray, slopes: np.ndarray,
                   query: np.ndarray) -> np.ndarray:
    """Evaluate the Hermite cubic defined by ``(x, y, slopes)`` at ``query``.

    Queries outside ``[x[0], x[-1]]`` are clamped to the end stations rather
    than extrapolated: a nozzle has no area beyond its own inlet and exit, and
    a cubic continued past the last point produces confident nonsense.
    """
    q = np.clip(np.asarray(query, dtype=float), x[0], x[-1])
    index = np.clip(np.searchsorted(x, q, side="right") - 1, 0, x.size - 2)

    h = x[index + 1] - x[index]
    t = (q - x[index]) / h
    t2, t3 = t * t, t * t * t

    h00 = 2.0 * t3 - 3.0 * t2 + 1.0
    h10 = t3 - 2.0 * t2 + t
    h01 = -2.0 * t3 + 3.0 * t2
    h11 = t3 - t2

    return (h00 * y[index] + h10 * h * slopes[index]
            + h01 * y[index + 1] + h11 * h * slopes[index + 1])


# ---------------------------------------------------------------------------
# the geometry itself
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AreaDistribution:
    """Quasi-1D duct area as a function of axial position. Geometry only.

    Attributes:
        x: Axial station positions [m], strictly increasing, at least three.
        area: Cross-sectional area at each station [m2], strictly positive.
        throat_index: Index of the minimum-area station. Computed, then
            validated -- never assumed.
    """

    x: np.ndarray
    area: np.ndarray
    throat_index: int = field(default=-1)

    def __post_init__(self) -> None:
        x, _ = as_float_array(self.x, "x")
        area, _ = as_float_array(self.area, "area")

        if x.ndim != 1 or area.ndim != 1:
            raise GeometryError("x and area must both be one-dimensional")
        if x.size != area.size:
            raise GeometryError(
                f"x and area must have the same length, got {x.size} and {area.size}")
        if x.size < 3:
            raise GeometryError(
                f"an area distribution needs at least three stations, got {x.size}")
        if not np.all(np.isfinite(x)) or not np.all(np.isfinite(area)):
            raise GeometryError("x and area must both be finite everywhere")
        if not np.all(np.diff(x) > 0.0):
            raise GeometryError(
                "x must be strictly increasing; a repeated or decreasing station "
                "makes the interpolation ambiguous")
        if not np.all(area > 0.0):
            raise GeometryError("every area must be strictly positive")

        throat = int(np.argmin(area))
        object.__setattr__(self, "x", _frozen(x))
        object.__setattr__(self, "area", _frozen(area))
        object.__setattr__(self, "throat_index", throat)

    # -- derived geometry ---------------------------------------------------

    @property
    def throat_area(self) -> float:
        """Minimum area [m2]."""
        return float(self.area[self.throat_index])

    @property
    def exit_area(self) -> float:
        """Area at the last station [m2]."""
        return float(self.area[-1])

    @property
    def inlet_area(self) -> float:
        """Area at the first station [m2]."""
        return float(self.area[0])

    @property
    def throat_x(self) -> float:
        """Axial position of the minimum-area station [m]."""
        return float(self.x[self.throat_index])

    @property
    def area_ratio_exit(self) -> float:
        """Ae/At [-]."""
        return self.exit_area / self.throat_area

    @property
    def area_ratio_inlet(self) -> float:
        """Ai/At [-]."""
        return self.inlet_area / self.throat_area

    @property
    def length(self) -> float:
        """Axial extent [m]."""
        return float(self.x[-1] - self.x[0])

    @property
    def has_interior_throat(self) -> bool:
        """Whether the minimum area falls strictly inside the duct."""
        return 0 < self.throat_index < self.x.size - 1

    @property
    def is_converging_diverging(self) -> bool:
        """Whether this passage can carry a C-D solution at all."""
        try:
            self.require_converging_diverging()
        except GeometryError:
            return False
        return True

    def require_converging_diverging(self) -> None:
        """Raise :class:`GeometryError` unless this is a genuine C-D passage.

        Four things are demanded, each because the solver would otherwise
        produce a confident wrong answer rather than an error:

        * an interior throat, since a monotone duct has no sonic point inside
          it and the classifier's thresholds would describe nothing;
        * a unique minimum, since two throats mean two candidate sonic points
          and the quasi-1D regime map is no longer single-valued;
        * area falling to the throat and rising after it, so that each side has
          one branch rather than a mixture;
        * an exit area strictly above the throat, since ``Ae = At`` has no
          diverging section and its supersonic branch is the sonic point
          itself.
        """
        if not self.has_interior_throat:
            raise GeometryError(
                "a converging-diverging solve needs the throat strictly inside "
                f"the duct; the minimum area is at station {self.throat_index} "
                f"of {self.x.size}, which is an end station. A monotone duct is "
                "a valid area distribution but has no internal sonic point.")

        minima = int(np.count_nonzero(self.area == self.area[self.throat_index]))
        if minima != 1:
            raise GeometryError(
                f"a converging-diverging solve needs exactly one minimum-area "
                f"station; {minima} stations share the minimum area")

        converging = self.area[: self.throat_index + 1]
        diverging = self.area[self.throat_index:]
        if not np.all(np.diff(converging) < 0.0):
            raise GeometryError(
                "the converging section must fall monotonically to the throat")
        if not np.all(np.diff(diverging) > 0.0):
            raise GeometryError(
                "the diverging section must rise monotonically from the throat")
        if not self.exit_area > self.throat_area:
            raise GeometryError(
                f"a converging-diverging nozzle needs an exit area above the "
                f"throat area, got Ae/At = {self.area_ratio_exit!r}")

    # -- interpolation ------------------------------------------------------

    def area_at(self, x: object) -> float | np.ndarray:
        """Area at an arbitrary axial position, by monotone cubic interpolation."""
        query, was_scalar = as_float_array(x, "x")
        values = pchip_evaluate(self.x, self.area, self._slopes(), query)
        return restore_scalar(values, was_scalar)

    def x_at_area(self, area: float, side: str = "diverging") -> float:
        """Axial position where the duct reaches ``area``, on one named side.

        The side must be named because a C-D passage reaches almost every area
        twice. Interpolation runs on ``x`` as a function of area over the
        chosen monotone segment, which is exactly the mapping ``03`` section
        3.7 asks for when a solved shock area ratio is turned into a position.

        Args:
            area: Target area [m2], within the range of the chosen side.
            side: ``"diverging"`` or ``"converging"``.

        Returns:
            Axial position [m].
        """
        if side not in ("diverging", "converging"):
            raise InputError(
                f"side must be 'diverging' or 'converging', got {side!r}")
        if not np.isfinite(area) or area <= 0.0:
            raise InputError(f"area must be finite and positive, got {area!r}")

        if side == "diverging":
            areas = self.area[self.throat_index:]
            positions = self.x[self.throat_index:]
        else:
            # Reversed so the abscissa increases, which the interpolant needs.
            areas = self.area[: self.throat_index + 1][::-1]
            positions = self.x[: self.throat_index + 1][::-1]

        if areas.size < 2:
            raise GeometryError(
                f"the {side} section has fewer than two stations, so no "
                "position can be interpolated")
        low, high = float(areas[0]), float(areas[-1])
        if not low - 1e-12 <= area <= high + 1e-12:
            raise InputError(
                f"area {area!r} is outside the {side} section, which spans "
                f"[{low!r}, {high!r}]")

        areas = np.ascontiguousarray(areas)
        positions = np.ascontiguousarray(positions)
        slopes = pchip_slopes(areas, positions)
        return float(pchip_evaluate(areas, positions, slopes,
                                    np.asarray(area, dtype=float)))

    def _slopes(self) -> np.ndarray:
        return pchip_slopes(self.x, self.area)

    # -- builders -----------------------------------------------------------

    @classmethod
    def from_area_ratios(cls, x: object, area_ratio: object,
                         throat_area: float = 1.0) -> "AreaDistribution":
        """Build from ``A/At`` values and a throat area.

        A dimensionless study passes ``throat_area = 1.0`` and gets areas that
        are numerically the ratios, which the classifier tolerates because it
        only ever uses ratios.
        """
        ratios, _ = as_float_array(area_ratio, "area_ratio")
        if not np.isfinite(throat_area) or throat_area <= 0.0:
            raise GeometryError(
                f"throat_area must be finite and positive, got {throat_area!r}")
        positions, _ = as_float_array(x, "x")
        return cls(x=positions, area=ratios * float(throat_area))

    @classmethod
    def conical(cls, throat_area: float, area_ratio: float,
                converging_ratio: float = 4.0,
                half_angle: float = np.pi / 12.0,
                converging_half_angle: float = np.pi / 6.0,
                n: int = 201) -> "AreaDistribution":
        """A plain straight-walled cone, for when only an area ratio is known.

        This exists so an area-ratio study has *something* to place a shock on,
        and it is deliberately a cone: a designed bell contour is
        ``engineering/nozzle/contour.py``, a module this phase does not write.
        Anything drawn from this profile should be labelled as the schematic it
        is.

        Args:
            throat_area: At [m2].
            area_ratio: Ae/At [-], above 1.
            converging_ratio: Ai/At [-], above 1.
            half_angle: Diverging wall half-angle [rad]. Radians, like every
                angle below the application layer; 15 degrees by default.
            converging_half_angle: Converging wall half-angle [rad].
            n: Total station count, at least 5.
        """
        for name, value in (("throat_area", throat_area),
                            ("area_ratio", area_ratio),
                            ("converging_ratio", converging_ratio),
                            ("half_angle", half_angle),
                            ("converging_half_angle", converging_half_angle)):
            if not np.isfinite(value) or value <= 0.0:
                raise GeometryError(f"{name} must be finite and positive, got {value!r}")
        if area_ratio <= 1.0:
            raise GeometryError(
                f"a converging-diverging cone needs area_ratio > 1, got {area_ratio!r}")
        if converging_ratio <= 1.0:
            raise GeometryError(
                f"the converging section needs converging_ratio > 1, got "
                f"{converging_ratio!r}")
        if half_angle >= np.pi / 2.0 or converging_half_angle >= np.pi / 2.0:
            raise GeometryError(
                "wall half-angles must be below a right angle, in radians")
        if not isinstance(n, int) or isinstance(n, bool) or n < 5:
            raise GeometryError(f"n must be an integer of at least 5, got {n!r}")

        throat_radius = float(np.sqrt(throat_area / np.pi))
        exit_radius = throat_radius * float(np.sqrt(area_ratio))
        inlet_radius = throat_radius * float(np.sqrt(converging_ratio))

        diverging_length = (exit_radius - throat_radius) / np.tan(half_angle)
        converging_length = (inlet_radius - throat_radius) / np.tan(
            converging_half_angle)

        # Split the stations by length so both walls are resolved evenly, and
        # put a station exactly at the throat rather than near it.
        total = converging_length + diverging_length
        n_converging = max(2, int(round((n - 1) * converging_length / total)))
        n_diverging = max(2, (n - 1) - n_converging)

        x_converging = np.linspace(-converging_length, 0.0, n_converging + 1)
        x_diverging = np.linspace(0.0, diverging_length, n_diverging + 1)[1:]
        x = np.concatenate([x_converging, x_diverging])

        radius = np.where(
            x <= 0.0,
            throat_radius + (-x) * np.tan(converging_half_angle),
            throat_radius + x * np.tan(half_angle),
        )
        return cls(x=x, area=np.pi * radius * radius)


def _frozen(values: np.ndarray) -> np.ndarray:
    """A contiguous copy that cannot be written through, so `frozen` means it."""
    copy = np.ascontiguousarray(values, dtype=float)
    copy.flags.writeable = False
    return copy
