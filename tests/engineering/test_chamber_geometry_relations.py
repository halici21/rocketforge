"""LIQ-5 chamber geometry relations, checked against oracles the code does not use.

* **Hand values.** A case worked on paper: At = 0.01 m², L* = 1 m, Ac/At = 4,
  30°. With Ac/At = 4, Rc = 2 Rt, so the frustum volume is exactly
  (7/3) At L_conv and L_conv = Rt / tan 30° = Rt √3.
* **A second closed form.** Huzel & Huang write the convergent volume as
  ``(1/3) At Rt cot(theta) (eps^(3/2) - 1)``, from the cone's length and
  radii eliminated differently. It is not how the code computes it.
* **Frustum limits.** Equal radii are a cylinder (pi r² h), a zero radius a
  cone (pi r² h / 3). The printed Sutton Eq. 8-8, without its 1/3, fails the
  first: these limits are what decide the factor.
* **Invariants** over a grid, at 1e-13, and **sensitivity**: each input moves
  only the quantities it should.
"""

from __future__ import annotations

import itertools
import math

import pytest

from rocketforge.core.result import Severity, Status
from rocketforge.engineering.chamber_geometry import (
    conical_frustum_volume,
    converging_length,
    cylindrical_conical_chamber,
)
from rocketforge.engineering.chamber_geometry import (
    CONTRACTION_PRESSURE_LOSS_ADVISORY,
    TYPICAL_BIPROPELLANT_L_STAR,
)

DEG = math.pi / 180.0


def chamber(at=0.01, l_star=1.0, eps=4.0, angle_deg=30.0):
    return cylindrical_conical_chamber(at, l_star, eps, angle_deg * DEG)


def codes(solution):
    return [d.code for d in solution.diagnostics]


# ===========================================================================
# independent oracles
# ===========================================================================


def test_a_hand_worked_chamber():
    """At 0.01 m², L* 1 m, Ac/At 4, 30°. Worked on paper:

    Rt = sqrt(0.01/pi) = 0.05641895835 m;  Rc = 2 Rt = 0.1128379167 m
    L_conv = Rt sqrt(3) = 0.09772050238 m
    V_conv = (7/3)(0.01)(0.09772050238) = 0.002280145056 m³
    Vc = 0.01 m³;  V_cyl = 0.007719854944 m³;  L_cyl = V_cyl / 0.04 = 0.1929963736 m
    L_inj = 0.2907168760 m;  Dc = 0.2256758334 m
    """
    solution = chamber()
    g = solution.value
    assert solution.status is Status.OK and codes(solution) == []
    assert g.throat_radius == pytest.approx(0.05641895835, rel=1e-10)
    assert 2.0 * g.chamber_radius == pytest.approx(0.2256758334, rel=1e-10)
    assert g.chamber_volume == pytest.approx(0.01, rel=1e-15)
    assert g.chamber_area == pytest.approx(0.04, rel=1e-15)
    assert g.converging_length == pytest.approx(0.09772050238, rel=1e-10)
    assert g.converging_volume == pytest.approx(0.002280145056, rel=1e-10)
    assert g.cylinder_volume == pytest.approx(0.007719854944, rel=1e-10)
    assert g.cylinder_length == pytest.approx(0.1929963736, rel=1e-9)
    assert g.injector_to_throat_length == pytest.approx(0.2907168760, rel=1e-9)


def test_a_one_meganewton_class_throat():
    """The LIQ-4 LOX/CH4 1 MN sea-level throat (At = 676.281 cm²), L* 1.0 m,
    Ac/At 3, 25°. By hand, with Rt = sqrt(At/pi) = 0.1467198 m:

    Rc = sqrt(3) Rt = 0.2541261 m;  L_conv = (Rc - Rt) / tan 25° = 0.2303336 m
    V_conv = At L (3 + sqrt 3 + 1) / 3 = 0.0297628 m³
    Vc = 0.0676281 m³;  L_cyl = (Vc - V_conv) / (3 At) = 0.1866351 m
    L_inj = 0.4169687 m
    (Cross-checked with the Huzel & Huang closed forms, not with this code.)
    """
    g = chamber(at=0.0676281, l_star=1.0, eps=3.0, angle_deg=25.0).value
    assert g.chamber_radius == pytest.approx(0.2541261, rel=1e-6)
    assert g.converging_length == pytest.approx(0.2303336, rel=1e-6)
    assert g.converging_volume == pytest.approx(0.0297628, rel=5e-6)
    assert g.cylinder_length == pytest.approx(0.1866351, rel=1e-6)
    assert g.injector_to_throat_length == pytest.approx(0.4169687, rel=1e-6)


@pytest.mark.parametrize("eps", [1.2, 2.0, 3.0, 4.0, 6.25, 10.0, 25.0])
@pytest.mark.parametrize("angle", [5.0, 15.0, 30.0, 45.0, 60.0, 80.0])
def test_the_convergent_matches_huzel_and_huangs_closed_form(eps, angle):
    at = 0.0123
    g = chamber(at=at, l_star=50.0, eps=eps, angle_deg=angle).value
    rt = math.sqrt(at / math.pi)
    cot = 1.0 / math.tan(angle * DEG)
    assert g.converging_volume == pytest.approx(at * rt * cot * (eps ** 1.5 - 1.0) / 3.0,
                                                rel=1e-13)
    assert g.converging_length == pytest.approx(rt * (math.sqrt(eps) - 1.0) * cot, rel=1e-13)


def test_frustum_limits_decide_the_one_third():
    r, h = 0.37, 1.9
    assert conical_frustum_volume(h, r, r) == pytest.approx(math.pi * r * r * h, rel=1e-15)
    assert conical_frustum_volume(h, r, 0.0) == pytest.approx(math.pi * r * r * h / 3.0,
                                                              rel=1e-15)
    assert conical_frustum_volume(h, 0.0, r) == conical_frustum_volume(h, r, 0.0)
    # Sutton's Eq. 8-8 as printed, A1 Lc (1 + sqrt(At/A1) + At/A1), at At = A1:
    a1 = math.pi * r * r
    printed = a1 * h * (1.0 + 1.0 + 1.0)
    assert printed == pytest.approx(3.0 * conical_frustum_volume(h, r, r), rel=1e-15)


def test_a_cone_from_its_slope():
    assert converging_length(0.2, 0.1, 45.0 * DEG) == pytest.approx(0.1, rel=1e-15)
    assert converging_length(0.2, 0.1, 30.0 * DEG) == pytest.approx(0.1 * math.sqrt(3.0),
                                                                    rel=1e-15)


# ===========================================================================
# invariants and sensitivity
# ===========================================================================

GRID = list(itertools.product([1e-4, 0.0123, 0.5], [0.6, 1.0, 3.0, 12.0],
                              [1.5, 3.0, 8.0], [10.0, 30.0, 60.0]))


@pytest.mark.parametrize("at,l_star,eps,angle", GRID)
def test_invariants_close_at_machine_precision(at, l_star, eps, angle):
    solution = chamber(at, l_star, eps, angle)
    if solution.value is None:
        assert codes(solution) == ["CONVERGING_SECTION_EXCEEDS_CHAMBER_VOLUME"]
        return
    g = solution.value
    assert g.chamber_volume == pytest.approx(l_star * at, rel=1e-15)
    assert g.chamber_volume / g.throat_area == pytest.approx(l_star, rel=1e-15)
    assert g.chamber_area / g.throat_area == pytest.approx(eps, rel=1e-15)
    assert math.pi * g.chamber_radius ** 2 == pytest.approx(g.chamber_area, rel=1e-14)
    assert math.pi * g.throat_radius ** 2 == pytest.approx(at, rel=1e-14)
    assert g.cylinder_volume + g.converging_volume == pytest.approx(g.chamber_volume,
                                                                    rel=1e-13)
    assert g.chamber_area * g.cylinder_length == pytest.approx(g.cylinder_volume, rel=1e-13)
    assert g.injector_to_throat_length == pytest.approx(g.cylinder_length
                                                        + g.converging_length, rel=1e-15)
    assert (g.chamber_radius - g.throat_radius) / g.converging_length == pytest.approx(
        math.tan(angle * DEG), rel=1e-13)
    assert abs(g.characteristic_length_closure) < 1e-13
    assert abs(g.contraction_closure) < 1e-13
    assert g.cylinder_length >= 0.0 and g.converging_length > 0.0


QUANTITIES = ("chamber_volume", "chamber_area", "chamber_radius", "converging_length",
              "converging_volume", "cylinder_length", "cylinder_volume",
              "injector_to_throat_length")


def changed(a, b):
    return {k for k in QUANTITIES if getattr(a, k) != getattr(b, k)}


def test_each_input_moves_only_what_it_should():
    base = chamber().value
    assert changed(base, chamber(l_star=1.3).value) == {
        "chamber_volume", "cylinder_length", "cylinder_volume", "injector_to_throat_length"}
    assert changed(base, chamber(angle_deg=40.0).value) == {
        "converging_length", "converging_volume", "cylinder_length", "cylinder_volume",
        "injector_to_throat_length"}
    assert changed(base, chamber(eps=5.0).value) == set(QUANTITIES) - {"chamber_volume"}
    # At x4 at fixed L*: Vc x4 (L* At), but the convergent is a similar cone
    # scaled by 2 in every length, so its volume goes x8.
    scaled = chamber(at=0.04).value
    assert scaled.chamber_volume == pytest.approx(4.0 * base.chamber_volume, rel=1e-15)
    assert scaled.converging_length == pytest.approx(2.0 * base.converging_length, rel=1e-15)
    assert scaled.converging_volume == pytest.approx(8.0 * base.converging_volume, rel=1e-14)


def test_directions_are_physical():
    base = chamber().value
    assert chamber(l_star=1.3).value.cylinder_length > base.cylinder_length
    steeper = chamber(angle_deg=45.0).value
    assert steeper.converging_length < base.converging_length
    assert steeper.cylinder_length > base.cylinder_length
    wider = chamber(eps=6.0).value
    assert wider.chamber_radius > base.chamber_radius
    assert wider.cylinder_length < base.cylinder_length


# ===========================================================================
# boundaries and refusals
# ===========================================================================


def test_a_convergent_larger_than_the_chamber_is_refused_with_the_minimum_l_star():
    """For Ac/At 4 at 30°, L*_min = V_conv/At = (7/3) Rt √3 = 0.2280145056 m (hand)."""
    solution = chamber(l_star=0.2)
    assert solution.status is Status.NO_SOLUTION and solution.value is None
    (diagnostic,) = solution.diagnostics
    assert diagnostic.code == "CONVERGING_SECTION_EXCEEDS_CHAMBER_VOLUME"
    assert diagnostic.severity is Severity.ERROR and diagnostic.field == "characteristic_length"
    assert diagnostic.detail["minimum_characteristic_length"] == pytest.approx(
        0.2280145056, rel=1e-9)
    assert "No input is changed" in diagnostic.message


def test_at_the_minimum_l_star_the_cylinder_vanishes():
    l_min = 7.0 / 3.0 * math.sqrt(0.01 / math.pi) * math.sqrt(3.0)
    g = chamber(l_star=l_min).value
    assert g is not None
    assert g.cylinder_length == pytest.approx(0.0, abs=1e-12 * g.converging_length)
    assert g.injector_to_throat_length == pytest.approx(g.converging_length, rel=1e-12)
    assert chamber(l_star=l_min * (1.0 - 1e-9)).value is None
    assert chamber(l_star=l_min * (1.0 + 1e-9)).value.cylinder_length > 0.0


def test_the_exact_boundary_is_not_refused_by_rounding():
    """Built from the code's own convergent volume, so ``Vc - V_conv`` is
    rounding only. Either sign of that residual reads as a zero-length cylinder."""
    probe = chamber(l_star=100.0).value
    l_min = probe.converging_volume / probe.throat_area
    solution = chamber(l_star=l_min)
    assert solution.value is not None
    assert solution.value.cylinder_length <= 1e-12 * solution.value.converging_length


@pytest.mark.parametrize("kwargs,code", [
    ({"l_star": 0.0}, "CHARACTERISTIC_LENGTH_INVALID"),
    ({"l_star": -1.0}, "CHARACTERISTIC_LENGTH_INVALID"),
    ({"l_star": math.nan}, "CHARACTERISTIC_LENGTH_INVALID"),
    ({"l_star": math.inf}, "CHARACTERISTIC_LENGTH_INVALID"),
    ({"eps": 1.0}, "CONTRACTION_RATIO_INVALID"),
    ({"eps": 0.5}, "CONTRACTION_RATIO_INVALID"),
    ({"eps": math.nan}, "CONTRACTION_RATIO_INVALID"),
    ({"angle_deg": 0.0}, "CONVERGING_HALF_ANGLE_INVALID"),
    ({"angle_deg": 90.0}, "CONVERGING_HALF_ANGLE_INVALID"),
    ({"angle_deg": -10.0}, "CONVERGING_HALF_ANGLE_INVALID"),
    ({"angle_deg": 120.0}, "CONVERGING_HALF_ANGLE_INVALID"),
    ({"at": 0.0}, "THROAT_AREA_INVALID"),
    ({"at": math.nan}, "THROAT_AREA_INVALID"),
])
def test_invalid_inputs_are_refused_not_clamped(kwargs, code):
    solution = chamber(**kwargs)
    assert solution.value is None and codes(solution) == [code]


def test_near_limit_inputs_are_computed_not_refused():
    assert chamber(eps=1.0 + 1e-9).value.converging_length < 1e-5
    assert chamber(angle_deg=89.999).value.converging_length < 1e-5
    long = chamber(l_star=50.0, angle_deg=0.5).value
    assert long.converging_length == pytest.approx(
        math.sqrt(0.01 / math.pi) / math.tan(0.5 * DEG), rel=1e-13)


# ===========================================================================
# advisories
# ===========================================================================


def test_a_contraction_below_three_is_a_warning_not_a_refusal():
    solution = chamber(eps=2.5)
    assert solution.value is not None and solution.status is Status.OK_WITH_WARNINGS
    assert codes(solution) == ["CONTRACTION_BELOW_PRESSURE_LOSS_ADVISORY"]
    assert "advisory" in solution.diagnostics[0].message.lower()
    assert codes(chamber(eps=CONTRACTION_PRESSURE_LOSS_ADVISORY)) == []


def test_an_unusual_l_star_is_information_only():
    low, high = TYPICAL_BIPROPELLANT_L_STAR
    for value in (0.5, 4.0):
        solution = chamber(l_star=value)
        assert solution.status is Status.OK
        assert codes(solution) == ["CHARACTERISTIC_LENGTH_OUTSIDE_TYPICAL"]
        assert solution.diagnostics[0].severity is Severity.INFO
        assert "not a validity limit" in solution.diagnostics[0].message
    assert codes(chamber(l_star=low)) == [] and codes(chamber(l_star=high)) == []


def test_no_message_claims_completeness_or_stability():
    for solution in (chamber(), chamber(eps=2.0, l_star=5.0), chamber(l_star=0.2)):
        for d in solution.diagnostics:
            text = d.message.lower()
            assert "complete combustion" not in text and "is stable" not in text
            assert "optimum" not in text and "recommended" not in text
