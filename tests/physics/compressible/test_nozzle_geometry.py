"""The geometry contract: what an area distribution accepts, and what it refuses.

``02`` section 1.6 and ``03`` section 10.2. Two layers are deliberately
separate and both are tested here: the constructor accepts any physically
meaningful duct, including a monotone one, while the C-D solver's extra
requirements -- one interior throat, an exit above the throat -- are checked by
``require_converging_diverging``. A monotone converging duct is a real device;
it simply has no internal sonic point.
"""

from __future__ import annotations

import numpy as np
import pytest

from rocketforge.core.errors import GeometryError, InputError
from rocketforge.physics.compressible.geometry import (
    AreaDistribution,
    pchip_evaluate,
    pchip_slopes,
)


def cd_profile(n: int = 41, area_ratio: float = 2.0) -> AreaDistribution:
    return AreaDistribution.conical(throat_area=0.01, area_ratio=area_ratio, n=n)


# ---------------------------------------------------------------------------
# construction
# ---------------------------------------------------------------------------


def test_a_conical_profile_is_a_valid_converging_diverging_duct():
    geometry = cd_profile()
    geometry.require_converging_diverging()
    assert geometry.is_converging_diverging
    assert geometry.has_interior_throat


def test_the_throat_is_found_not_assumed():
    geometry = cd_profile()
    assert geometry.throat_index == int(np.argmin(geometry.area))
    assert geometry.throat_area == pytest.approx(geometry.area.min())


def test_the_exit_and_inlet_are_the_end_stations():
    geometry = cd_profile()
    assert geometry.exit_area == geometry.area[-1]
    assert geometry.inlet_area == geometry.area[0]
    assert geometry.area_ratio_exit == pytest.approx(2.0, rel=1e-12)


def test_arrays_are_not_writable_so_frozen_means_frozen():
    geometry = cd_profile()
    with pytest.raises(ValueError):
        geometry.area[0] = 1.0
    with pytest.raises(ValueError):
        geometry.x[0] = 1.0


def test_from_area_ratios_scales_by_the_throat_area():
    x = np.linspace(-1.0, 1.0, 21)
    ratios = 1.0 + x ** 2
    geometry = AreaDistribution.from_area_ratios(x, ratios, throat_area=0.02)
    assert geometry.throat_area == pytest.approx(0.02)
    assert geometry.area_ratio_exit == pytest.approx(2.0)


def test_a_dimensionless_geometry_is_allowed():
    """throat_area = 1 makes the areas numerically the ratios."""
    x = np.linspace(-1.0, 1.0, 21)
    geometry = AreaDistribution.from_area_ratios(x, 1.0 + x ** 2)
    assert geometry.throat_area == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# refusals
# ---------------------------------------------------------------------------


def test_non_increasing_x_is_refused():
    with pytest.raises(GeometryError, match="strictly increasing"):
        AreaDistribution(x=np.array([0.0, 1.0, 1.0]), area=np.array([2.0, 1.0, 2.0]))


def test_non_positive_area_is_refused():
    with pytest.raises(GeometryError, match="strictly positive"):
        AreaDistribution(x=np.array([0.0, 1.0, 2.0]), area=np.array([2.0, 0.0, 2.0]))


def test_two_stations_are_not_enough():
    with pytest.raises(GeometryError, match="at least three"):
        AreaDistribution(x=np.array([0.0, 1.0]), area=np.array([2.0, 1.0]))


def test_a_non_finite_area_is_refused():
    with pytest.raises(GeometryError, match="finite"):
        AreaDistribution(x=np.array([0.0, 1.0, 2.0]),
                         area=np.array([2.0, np.nan, 2.0]))


def test_mismatched_lengths_are_refused():
    with pytest.raises(GeometryError, match="same length"):
        AreaDistribution(x=np.array([0.0, 1.0, 2.0]), area=np.array([2.0, 1.0]))


def test_a_monotone_duct_constructs_but_is_not_converging_diverging():
    """A converging nozzle is a real device; it just has no internal throat."""
    geometry = AreaDistribution(x=np.array([0.0, 1.0, 2.0]),
                                area=np.array([3.0, 2.0, 1.0]))
    assert not geometry.has_interior_throat
    with pytest.raises(GeometryError, match="strictly inside"):
        geometry.require_converging_diverging()


def test_two_throats_are_refused_rather_than_one_of_them_chosen():
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    area = np.array([2.0, 1.0, 1.5, 1.0, 2.0])
    geometry = AreaDistribution(x=x, area=area)
    with pytest.raises(GeometryError, match="exactly one minimum"):
        geometry.require_converging_diverging()


def test_a_non_monotone_diverging_section_is_refused():
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    area = np.array([3.0, 1.0, 2.0, 1.8, 2.5])
    with pytest.raises(GeometryError, match="diverging section"):
        AreaDistribution(x=x, area=area).require_converging_diverging()


def test_an_exit_at_the_throat_area_is_refused():
    """Ae = At has no diverging section, so there is no C-D problem to solve."""
    x = np.array([0.0, 1.0, 2.0])
    area = np.array([2.0, 1.0, 1.0])
    with pytest.raises(GeometryError):
        AreaDistribution(x=x, area=area).require_converging_diverging()


@pytest.mark.parametrize("area_ratio", [0.5, 1.0])
def test_conical_refuses_a_non_diverging_area_ratio(area_ratio):
    with pytest.raises(GeometryError, match="area_ratio"):
        AreaDistribution.conical(throat_area=0.01, area_ratio=area_ratio)


# ---------------------------------------------------------------------------
# interpolation
# ---------------------------------------------------------------------------


def test_interpolation_reproduces_the_supplied_stations():
    geometry = cd_profile(n=51)
    got = geometry.area_at(geometry.x)
    assert np.allclose(got, geometry.area, rtol=1e-12, atol=0.0)


def test_interpolation_does_not_overshoot_near_the_throat():
    """The reason PCHIP is specified: a natural spline invents a second minimum."""
    geometry = cd_profile(n=21)
    dense = np.linspace(geometry.x[0], geometry.x[-1], 2001)
    area = geometry.area_at(dense)
    assert area.min() >= geometry.throat_area - 1e-12
    # exactly one interior minimum survives the refinement
    interior = area[1:-1]
    assert int(np.count_nonzero(interior <= area.min() + 1e-12)) <= 2


def test_interpolation_is_clamped_rather_than_extrapolated():
    geometry = cd_profile()
    assert geometry.area_at(geometry.x[0] - 5.0) == pytest.approx(geometry.inlet_area)
    assert geometry.area_at(geometry.x[-1] + 5.0) == pytest.approx(geometry.exit_area)


def test_x_at_area_inverts_the_diverging_side():
    geometry = cd_profile(n=101)
    target = 1.5 * geometry.throat_area
    x = geometry.x_at_area(target, side="diverging")
    assert x > geometry.throat_x
    assert geometry.area_at(x) == pytest.approx(target, rel=1e-8)


def test_x_at_area_inverts_the_converging_side():
    geometry = cd_profile(n=101)
    target = 1.5 * geometry.throat_area
    x = geometry.x_at_area(target, side="converging")
    assert x < geometry.throat_x
    # Looser than the diverging side, and honestly so: the converging wall is
    # shorter, so it carries fewer stations, and x(A) is a square root rather
    # than a polynomial. The next test shows this is interpolation error.
    assert geometry.area_at(x) == pytest.approx(target, rel=1e-6)


def test_the_area_position_round_trip_converges_with_the_grid():
    """Proof that the residual above is interpolation error and not a defect."""
    errors = []
    for n in (51, 201):
        geometry = cd_profile(n=n)
        target = 1.5 * geometry.throat_area
        for side in ("converging", "diverging"):
            x = geometry.x_at_area(target, side=side)
            errors.append((n, side, abs(geometry.area_at(x) / target - 1.0)))
    for side in ("converging", "diverging"):
        coarse = next(e for n, s, e in errors if n == 51 and s == side)
        fine = next(e for n, s, e in errors if n == 201 and s == side)
        assert fine < coarse


def test_x_at_area_needs_a_named_side():
    """A C-D duct reaches almost every area twice, so the side is not optional."""
    geometry = cd_profile()
    with pytest.raises(InputError, match="side must be"):
        geometry.x_at_area(1.5 * geometry.throat_area, side="either")


def test_x_at_area_refuses_an_area_the_side_never_reaches():
    geometry = cd_profile()
    with pytest.raises(InputError, match="outside"):
        geometry.x_at_area(50.0 * geometry.throat_area, side="diverging")


def test_pchip_is_exact_on_a_straight_line():
    x = np.array([0.0, 1.0, 2.5, 4.0])
    y = 3.0 * x + 1.0
    slopes = pchip_slopes(x, y)
    query = np.linspace(0.0, 4.0, 17)
    assert np.allclose(pchip_evaluate(x, y, slopes, query), 3.0 * query + 1.0)


def test_pchip_flattens_at_an_interior_extremum():
    """Zero slope at a turning point is what forbids the overshoot."""
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([1.0, 0.0, 1.0])
    assert pchip_slopes(x, y)[1] == pytest.approx(0.0)
