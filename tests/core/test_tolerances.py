"""The tolerance set is immutable, validated, and matches the specification."""

from __future__ import annotations

import dataclasses

import pytest

from rocketforge.core.errors import InputError
from rocketforge.core.tolerances import DEFAULT_TOLERANCES, ToleranceSet


def test_defaults_match_the_specification():
    """Values transcribed from 04_numerical_methods_and_domain_policy section 5."""
    assert DEFAULT_TOLERANCES.rel_tol == 1e-12
    assert DEFAULT_TOLERANCES.abs_tol == 1e-14
    assert DEFAULT_TOLERANCES.residual_tol == 1e-10
    assert DEFAULT_TOLERANCES.max_iter == 100


def test_is_frozen():
    with pytest.raises(Exception):
        DEFAULT_TOLERANCES.rel_tol = 1e-6  # type: ignore[misc]


def test_replace_produces_a_new_set_without_touching_the_default():
    tighter = dataclasses.replace(DEFAULT_TOLERANCES, rel_tol=1e-14)
    assert tighter.rel_tol == 1e-14
    assert DEFAULT_TOLERANCES.rel_tol == 1e-12, "the shared default was mutated"
    assert tighter.max_iter == DEFAULT_TOLERANCES.max_iter


@pytest.mark.parametrize("field", ["rel_tol", "abs_tol", "residual_tol"])
@pytest.mark.parametrize("bad", [0.0, -1e-12, -1.0])
def test_non_positive_tolerances_rejected(field, bad):
    with pytest.raises(InputError) as excinfo:
        ToleranceSet(**{field: bad})
    assert field in str(excinfo.value)


@pytest.mark.parametrize("bad", [0, -1, 1.5, "100", None, True])
def test_invalid_max_iter_rejected(bad):
    with pytest.raises(InputError) as excinfo:
        ToleranceSet(max_iter=bad)
    assert "max_iter" in str(excinfo.value)


def test_equality_is_by_value():
    assert ToleranceSet() == ToleranceSet()
    assert ToleranceSet(rel_tol=1e-13) != ToleranceSet()


def test_field_set_is_exactly_what_the_implemented_relations_need():
    """The set grows one phase at a time, so adding a field is deliberate.

    Phase 4A defined the generic and root-finding fields; Phase 4B added the
    Mach, area, sonic and gamma-domain fields that the isentropic and
    area-Mach relations use; Phase 4D added the angular and Prandtl-Meyer
    fields that the oblique-shock and expansion relations use; Phase 4E added
    the Fanno and Rayleigh choking tolerances, and Phase 4F adds the last one
    of the full specification, ``pressure_tol``, together with the nozzle
    regime classifier that needs it. The set is now complete.
    """
    names = {f.name for f in dataclasses.fields(ToleranceSet)}
    assert names == {
        "rel_tol", "abs_tol", "residual_tol", "max_iter",
        "mach_abs_tol", "mach_rel_tol", "area_abs_tol", "area_rel_tol",
        "angle_abs_tol",
        "area_sonic_tol", "sonic_tol", "sonic_margin", "near_sonic_mach",
        "angle_tol", "angle_margin", "nu_tol", "near_theta_max",
        "fanno_tol", "rayleigh_tol", "pressure_tol",
        "mach_floor", "mach_ceiling",
        "gamma_min", "gamma_max", "gamma_advisory_min", "gamma_advisory_max",
    }
    not_yet: set[str] = set()
    assert not (names & not_yet), "a tolerance arrived before the relation that needs it"

    # The other half of the same rule: a tolerance is present only because a
    # relation uses it. Every field has now left `not_yet`, so every module
    # that justifies one must actually exist.
    import importlib

    for module in ("oblique_shock", "prandtl_meyer", "fanno", "rayleigh", "nozzle"):
        importlib.import_module(f"rocketforge.physics.compressible.{module}")


def test_phase_4b_defaults_match_the_specification():
    """Values transcribed from 04 section 5."""
    t = DEFAULT_TOLERANCES
    assert t.mach_abs_tol == 1e-10
    assert t.mach_rel_tol == 1e-12
    assert t.area_abs_tol == 1e-10
    assert t.area_rel_tol == 1e-12
    assert t.area_sonic_tol == 1e-11
    assert t.sonic_tol == 1e-9
    assert t.sonic_margin == 1e-9
    assert t.near_sonic_mach == 1e-3
    assert t.mach_floor == 1e-6
    assert t.mach_ceiling == 100.0
    assert t.gamma_min == 1.001
    assert t.gamma_max == 3.0


def test_gamma_limits_must_be_ordered():
    with pytest.raises(InputError):
        ToleranceSet(gamma_min=2.0, gamma_max=1.5)
    with pytest.raises(InputError):
        ToleranceSet(gamma_min=0.9)


def test_gamma_advisory_band_must_sit_inside_the_hard_limits():
    with pytest.raises(InputError):
        ToleranceSet(gamma_advisory_min=1.0005)
    with pytest.raises(InputError):
        ToleranceSet(gamma_advisory_max=4.0)
    with pytest.raises(InputError):
        ToleranceSet(gamma_advisory_min=1.8, gamma_advisory_max=1.2)


def test_mach_bracket_limits_must_straddle_sonic():
    with pytest.raises(InputError):
        ToleranceSet(mach_floor=1.5)
    with pytest.raises(InputError):
        ToleranceSet(mach_ceiling=0.5)


@pytest.mark.parametrize("field", ["mach_abs_tol", "area_sonic_tol", "sonic_margin",
                                   "near_sonic_mach", "mach_floor", "mach_ceiling"])
def test_new_tolerances_must_be_positive(field):
    with pytest.raises(InputError):
        ToleranceSet(**{field: 0.0})
