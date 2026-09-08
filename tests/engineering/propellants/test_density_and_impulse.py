"""Bulk propellant density and density impulse.

The arithmetic is checked against values computed by hand, written down here,
and never produced by the code under test.
"""

from __future__ import annotations

import pytest

from rocketforge.core.constants import STANDARD_GRAVITY
from rocketforge.core.errors import DomainError
from rocketforge.engineering.propellants import (
    ADDITIVE_VOLUME_ASSUMPTIONS,
    PRODUCTION_FLUID_MAPPING,
    StreamDensity,
    UnmappedPropellantError,
    density_impulse,
    mixture_bulk_density,
)


def stream(name, density):
    return StreamDensity(propellant_name=name, fluid_name=name,
                         temperature=90.0, pressure=3.0e5, phase="liquid",
                         density=density, provider_id="t",
                         provider_label="Test", library_version="",
                         backend="test")


# --- the mapping ----------------------------------------------------------

def test_only_the_three_cryogens_have_a_validated_fluid_model():
    assert set(PRODUCTION_FLUID_MAPPING.bindings) == {"LOX", "LCH4", "LH2"}


def test_rp1_is_unsupported_and_says_so_rather_than_taking_a_surrogate():
    with pytest.raises(UnmappedPropellantError, match="surrogate is not sub"):
        PRODUCTION_FLUID_MAPPING.require("RP-1")


def test_a_gaseous_propellant_has_no_bulk_liquid_binding():
    assert not PRODUCTION_FLUID_MAPPING.has("GOX")


def test_every_binding_names_its_source_and_its_phase():
    for binding in PRODUCTION_FLUID_MAPPING.bindings.values():
        assert binding.source.strip()
        assert binding.expected_phase is not None


def test_the_mapping_table_is_read_only():
    with pytest.raises(TypeError):
        PRODUCTION_FLUID_MAPPING.bindings["X"] = None  # type: ignore[index]


# --- bulk density, hand-computed -----------------------------------------

def test_bulk_density_matches_a_hand_computed_case():
    """rho_f = 400, rho_ox = 1200, O/F = 3.

    w_f  = 1/4 = 0.25 -> 0.25/400  = 6.25e-4 m3/kg
    w_ox = 3/4 = 0.75 -> 0.75/1200 = 6.25e-4 m3/kg
    1/rho = 1.25e-3 -> rho = 800 kg/m3, written down before running anything.
    """
    bulk = mixture_bulk_density(3.0, stream("F", 400.0), stream("O", 1200.0))
    assert bulk.density == 800.0
    assert bulk.fuel_mass_fraction == 0.25
    assert bulk.oxidiser_mass_fraction == 0.75


def test_equal_densities_give_that_density_whatever_the_ratio():
    for of in (0.5, 1.0, 3.4, 20.0):
        bulk = mixture_bulk_density(of, stream("F", 500.0), stream("O", 500.0))
        assert bulk.density == pytest.approx(500.0)


def test_bulk_density_lies_between_the_two_component_densities():
    bulk = mixture_bulk_density(3.4, stream("F", 422.4), stream("O", 1141.0))
    assert 422.4 < bulk.density < 1141.0


def test_the_assumptions_travel_with_every_result():
    bulk = mixture_bulk_density(3.0, stream("F", 400.0), stream("O", 1200.0))
    assert bulk.assumptions == ADDITIVE_VOLUME_ASSUMPTIONS
    joined = " ".join(bulk.assumptions)
    assert "separate volumes" in joined
    assert "not the density of a LOX/fuel solution" in joined


def test_a_zero_density_is_refused():
    with pytest.raises(DomainError, match="positive and finite"):
        mixture_bulk_density(3.0, stream("F", 0.0), stream("O", 1200.0))


def test_a_zero_mixture_ratio_is_refused():
    with pytest.raises(DomainError, match="positive and finite"):
        mixture_bulk_density(0.0, stream("F", 400.0), stream("O", 1200.0))


# --- density impulse, hand-computed --------------------------------------

def test_density_impulse_matches_a_hand_computed_case():
    """rho_mix = 800 kg/m3, c_eff = 3000 m/s -> 2.4e6 kg/(m2 s)."""
    bulk = mixture_bulk_density(3.0, stream("F", 400.0), stream("O", 1200.0))
    result = density_impulse(bulk, 3000.0, 3000.0 / STANDARD_GRAVITY)
    assert result.value == 2_400_000.0
    assert result.unit == "kg/(m^2 s)"
    assert result.unit_alias == "N s / m^3"


def test_the_two_spellings_of_density_impulse_agree():
    bulk = mixture_bulk_density(3.4, stream("F", 422.4), stream("O", 1141.0))
    isp = 348.6575
    result = density_impulse(bulk, isp * STANDARD_GRAVITY, isp)
    assert result.residual == pytest.approx(0.0, abs=1e-15)
    assert result.value == pytest.approx(bulk.density * isp * STANDARD_GRAVITY)


def test_density_impulse_scales_linearly_with_bulk_density():
    light = mixture_bulk_density(1.0, stream("F", 400.0), stream("O", 400.0))
    heavy = mixture_bulk_density(1.0, stream("F", 800.0), stream("O", 800.0))
    a = density_impulse(light, 3000.0, 3000.0 / STANDARD_GRAVITY).value
    b = density_impulse(heavy, 3000.0, 3000.0 / STANDARD_GRAVITY).value
    assert b == pytest.approx(2.0 * a)


def test_a_zero_exhaust_velocity_is_refused():
    bulk = mixture_bulk_density(3.0, stream("F", 400.0), stream("O", 1200.0))
    with pytest.raises(DomainError, match="positive and finite"):
        density_impulse(bulk, 0.0, 300.0)


def test_the_record_names_its_formula_its_identity_and_its_unit():
    bulk = mixture_bulk_density(3.0, stream("F", 400.0), stream("O", 1200.0))
    view = density_impulse(bulk, 3000.0, 3000.0 / STANDARD_GRAVITY).as_mapping()
    assert view["formula"] == "rho_mix * c_eff"
    assert view["identity"] == "rho_mix * Isp * g0"
    assert view["unit"] == "kg/(m^2 s)"
    assert view["standard_gravity_m_per_s2"] == STANDARD_GRAVITY


def test_there_is_no_second_metric_called_rho_times_isp():
    """rho*Isp and rho*Isp*g0 differ by 9.8 and would be confused by one name."""
    from rocketforge.engineering.propellants import DensityImpulse

    fields = set(DensityImpulse.__dataclass_fields__)
    assert not {f for f in fields if "rho_isp" in f or "density_isp" in f}
