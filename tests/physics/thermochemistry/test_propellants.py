"""Propellant definitions, streams, mixture ratio and pairs."""

from __future__ import annotations

import dataclasses

import pytest

from rocketforge.physics.thermochemistry import (
    Composition,
    CompositionBasis,
    MixtureRatio,
    MixtureRatioBasis,
    MixtureRatioError,
    Phase,
    PropellantDefinition,
    PropellantError,
    PropellantPair,
    PropellantPairReferenceCase,
    PropellantRole,
    PropellantRoleError,
    PropellantStream,
    mixture_ratio_from_streams,
)

MASS = CompositionBasis.MASS_FRACTION
MOLE = CompositionBasis.MOLE_FRACTION


# ---------------------------------------------------------------------------
# definition is not a species, and not a stream
# ---------------------------------------------------------------------------


def test_a_propellant_holds_a_composition_not_a_single_species(blend_oxidiser):
    """RP-1, Aerozine-50, MON and 90 % peroxide are not single molecules."""
    assert blend_oxidiser.is_blend
    assert set(blend_oxidiser.composition.fractions) == {"H2O2", "H2O"}


def test_blend_basis_is_preserved(blend_oxidiser):
    """A specification stated by mass stays a mass-basis record."""
    assert blend_oxidiser.composition.basis is MASS
    assert blend_oxidiser.composition.fraction_of("H2O2") == pytest.approx(0.90)


def test_blend_round_trip_through_the_canonical_basis(realistic_table):
    """A mass-basis blend converts to mole basis and back unchanged."""
    table = {
        "A": dataclasses.replace(realistic_table["CO2"], name="A"),
        "B": dataclasses.replace(realistic_table["H2"], name="B"),
    }
    blend = Composition.from_fractions({"A": 0.7, "B": 0.3}, MASS)
    back = blend.to_basis(MOLE, table).to_basis(MASS, table)
    assert back.fraction_of("A") == pytest.approx(0.7, rel=1e-13)
    assert back.fraction_of("B") == pytest.approx(0.3, rel=1e-13)


def test_definition_is_frozen(lox):
    with pytest.raises(dataclasses.FrozenInstanceError):
        lox.reference_temperature = 300.0  # type: ignore[misc]


def test_reference_phase_is_required_and_typed():
    with pytest.raises(PropellantError, match="never treated as GAS"):
        PropellantDefinition("X", PropellantRole.FUEL, Composition.pure("X"),
                             300.0, "liquid")  # type: ignore[arg-type]


def test_provider_names_are_generic_not_vendor_fields(lox):
    """No field is named after one vendor; the mapping generalises.

    Phase 5B-0 found CEA's own spelling for liquid oxygen is ``O2(L)``, and
    that its reactant names are capped at 15 characters. Both are provider
    facts and live in this mapping, not in the domain model.
    """
    assert lox.provider_name("cea") == "O2(L)"
    assert lox.provider_name("cantera") == "LOX"       # falls back to our name
    assert not hasattr(lox, "cea_name")


def test_surrogate_definition_must_name_its_source():
    with pytest.raises(PropellantError, match="must name its source"):
        PropellantDefinition("RP-1", PropellantRole.FUEL,
                             Composition.pure("RP-1"), 298.15, Phase.LIQUID,
                             is_surrogate=True)


# ---------------------------------------------------------------------------
# stream: the actual condition
# ---------------------------------------------------------------------------


def test_cryogenic_streams_are_representable(lox_stream, methane_stream):
    """LOX at 90.17 K and liquid methane at 111.643 K, not 298 K gases.

    Phase 5B-0 measured the difference between using these and using gaseous
    reactants at 298.15 K as 74.9 K of chamber temperature. A data model that
    cannot express it cannot get the chamber right.
    """
    assert lox_stream.temperature == pytest.approx(90.17)
    assert lox_stream.phase is Phase.LIQUID
    assert methane_stream.temperature == pytest.approx(111.643)
    assert methane_stream.phase is Phase.LIQUID


def test_stream_actual_state_is_distinct_from_definition_reference(lox):
    """A stream at a different temperature keeps the definition's reference."""
    warmed = PropellantStream(propellant=lox, temperature=110.0)
    assert warmed.temperature == 110.0
    assert warmed.propellant.reference_temperature == pytest.approx(90.17)
    assert not warmed.is_at_reference_condition

    at_reference = PropellantStream(propellant=lox, temperature=90.17)
    assert at_reference.is_at_reference_condition


def test_unknown_stream_phase_is_not_silently_gas(lox):
    """`None` means unknown and never falls back to the reference phase."""
    stream = PropellantStream(propellant=lox, temperature=90.17)
    assert stream.phase is None
    assert stream.effective_phase is None
    assert stream.propellant.reference_phase is Phase.LIQUID


@pytest.mark.parametrize("bad", [0.0, -1.0, -273.15, float("nan"), float("inf")])
def test_stream_temperature_must_be_positive_and_finite(lox, bad):
    """Kelvin, never Celsius. A Celsius value would be silently wrong."""
    with pytest.raises(PropellantError):
        PropellantStream(propellant=lox, temperature=bad)


@pytest.mark.parametrize("bad", [0.0, -1.0e5, float("nan"), float("inf")])
def test_stream_pressure_must_be_positive_and_finite(lox, bad):
    """RocketForge rejects this before any provider sees it.

    Phase 5B-0 measured NASA CEA silently accepting a negative pressure and
    returning without raising, so the guard has to be here.
    """
    with pytest.raises(PropellantError):
        PropellantStream(propellant=lox, temperature=90.17, pressure=bad)


def test_stream_carries_no_device_geometry(lox_stream):
    for forbidden in ("orifice_area", "injector_diameter", "pressure_drop",
                      "discharge_coefficient"):
        assert not hasattr(lox_stream, forbidden)


# ---------------------------------------------------------------------------
# mixture ratio: orientation
# ---------------------------------------------------------------------------


def test_of_is_oxidiser_over_fuel_by_mass(methane_stream, lox_stream):
    """Asymmetric masses, so an inversion cannot hide.

    fuel 1.0 kg/s, oxidiser 3.4 kg/s.  O/F = 3.4.  F/O = 0.294...
    A test with equal flows would pass either way, which is why these differ.
    """
    ratio = mixture_ratio_from_streams(methane_stream, lox_stream)
    assert ratio.of_mass == pytest.approx(3.4)
    assert ratio.fuel_oxidiser_ratio() == pytest.approx(1.0 / 3.4)
    assert ratio.of_mass != pytest.approx(ratio.fuel_oxidiser_ratio())


def test_swapping_the_arguments_raises_rather_than_inverting(methane_stream,
                                                             lox_stream):
    """The roles are checked, not inferred from position.

    A silently inverted O/F gives 0.294 instead of 3.4 and produces a
    temperature that is wrong but not absurd.
    """
    with pytest.raises(PropellantRoleError, match="may be swapped"):
        mixture_ratio_from_streams(lox_stream, methane_stream)


def test_mixture_ratio_needs_mass_flows_and_says_so(lox, liquid_methane):
    fuel = PropellantStream(liquid_methane, 111.643)
    oxidiser = PropellantStream(lox, 90.17)
    with pytest.raises(PropellantError, match="must state a mass flow"):
        mixture_ratio_from_streams(fuel, oxidiser)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
def test_mixture_ratio_domain(bad):
    with pytest.raises(MixtureRatioError):
        MixtureRatio(bad)


def test_zero_is_not_a_mixture_ratio_for_a_monopropellant():
    """A monopropellant is not O/F = 0; it needs its own entry point."""
    with pytest.raises(MixtureRatioError, match="monopropellant"):
        MixtureRatio(0.0)


def test_large_and_small_ratios_are_not_clamped():
    """Sweeps legitimately run far from stoichiometric."""
    assert MixtureRatio(0.01).of_mass == 0.01
    assert MixtureRatio(500.0).of_mass == 500.0


def test_molar_basis_will_not_silently_pretend_to_be_mass():
    molar = MixtureRatio(3.4, MixtureRatioBasis.MOLAR)
    with pytest.raises(MixtureRatioError, match="to_mass_basis"):
        molar.of_mass
    converted = molar.to_mass_basis(oxidiser_molar_mass=32.0e-3,
                                    fuel_molar_mass=16.0e-3)
    assert converted.of_mass == pytest.approx(3.4 * 2.0)
    assert converted.basis is MixtureRatioBasis.MASS


def test_equivalence_ratio_requires_an_explicit_stoichiometric_value():
    """No hidden stoichiometric constant lives in this class."""
    ratio = MixtureRatio(6.0)
    assert ratio.equivalence_ratio(7.94) == pytest.approx(7.94 / 6.0)
    with pytest.raises(MixtureRatioError):
        ratio.equivalence_ratio(0.0)


# ---------------------------------------------------------------------------
# pair
# ---------------------------------------------------------------------------


def test_pair_checks_roles(lox, liquid_methane):
    pair = PropellantPair(oxidiser=lox, fuel=liquid_methane)
    assert pair.label == "LOX/CH4"
    with pytest.raises(PropellantRoleError):
        PropellantPair(oxidiser=liquid_methane, fuel=lox)


def test_pair_stores_no_performance(lox, liquid_methane):
    """No isp, no cstar, no chamber temperature, and no optimal_of.

    Phase 5B-0 swept LOX/CH4 and found c* peaking at O/F 2.85, chamber
    temperature at 3.75 and Isp at 3.30 -- three different maxima. "Optimum
    O/F" is undefined without an objective, so the pair does not carry one.
    """
    pair = PropellantPair(oxidiser=lox, fuel=liquid_methane)
    for forbidden in ("isp", "Isp", "cstar", "c_star", "cf", "thrust",
                      "chamber_temperature", "optimal_of", "optimum_of"):
        assert not hasattr(pair, forbidden)
    assert set(f.name for f in dataclasses.fields(pair)) == {
        "oxidiser", "fuel", "name", "stoichiometric_of_mass"}


def test_stoichiometric_ratio_is_a_property_of_the_pair(lox, liquid_methane):
    """Legitimately on the pair: it does not depend on the operating point."""
    pair = PropellantPair(oxidiser=lox, fuel=liquid_methane,
                          stoichiometric_of_mass=3.989)
    assert pair.stoichiometric_of_mass == pytest.approx(3.989)


# ---------------------------------------------------------------------------
# reference case
# ---------------------------------------------------------------------------


def test_reference_case_binds_values_to_conditions(lox, liquid_methane):
    """A published number with no conditions is not a datum."""
    pair = PropellantPair(oxidiser=lox, fuel=liquid_methane)
    case = PropellantPairReferenceCase(
        pair=pair,
        source="synthetic test source",
        source_location="table 1",
        oxidiser_fuel_ratio=MixtureRatio(3.4),
        chamber_pressure=10.0e6,
        oxidiser_temperature=90.17,
        fuel_temperature=111.643,
        oxidiser_phase=Phase.LIQUID,
        fuel_phase=Phase.LIQUID,
        area_ratio=40.0,
        chemistry_mode="equilibrium",
        observations={"chamber_temperature": 3598.33, "c_star": 1846.90},
        observation_units={"chamber_temperature": "K", "c_star": "m/s"},
        source_precision=6,
    )
    assert case.observed["c_star"] == pytest.approx(1846.90)
    assert case.unit_of("c_star") == "m/s"
    assert case.chamber_pressure == 10.0e6


def test_reference_case_requires_a_source(lox, liquid_methane):
    pair = PropellantPair(oxidiser=lox, fuel=liquid_methane)
    with pytest.raises(PropellantError, match="must name its source"):
        PropellantPairReferenceCase(pair=pair, source="   ")


def test_every_observation_must_state_its_unit(lox, liquid_methane):
    pair = PropellantPair(oxidiser=lox, fuel=liquid_methane)
    with pytest.raises(PropellantError, match="no stated unit"):
        PropellantPairReferenceCase(
            pair=pair, source="synthetic",
            observations={"c_star": 1800.0}, observation_units={})


def test_reference_case_observations_are_not_computed_fields(lox, liquid_methane):
    """They live in a mapping so the record cannot be mistaken for a result."""
    pair = PropellantPair(oxidiser=lox, fuel=liquid_methane)
    case = PropellantPairReferenceCase(pair=pair, source="synthetic")
    assert not hasattr(case, "c_star")
    assert not hasattr(case, "isp")
    assert case.observed == {}


# ---------------------------------------------------------------------------
# density hint is display-only
# ---------------------------------------------------------------------------


def test_density_hint_is_never_read_by_this_package(lox):
    """A documented display-only field becomes a physics input the moment
    someone needs a density and it is right there. A grep is the only thing
    that stops it, so this test is that grep."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[3] / "rocketforge"
    package = root / "physics" / "thermochemistry"
    offenders = []
    for path in package.rglob("*.py"):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "density_hint" not in line:
                continue
            stripped = line.strip()
            # The declaration, its validation and its documentation are fine.
            if (stripped.startswith("#") or stripped.startswith("*")
                    or "density_hint:" in stripped
                    or "self.density_hint" in stripped
                    or "density hint" in stripped.lower()):
                continue
            offenders.append(f"{path.name}:{number}: {stripped}")
    assert not offenders, (
        "density_hint is display-only and must not feed a calculation:\n"
        + "\n".join(offenders))
    assert lox.density_hint == pytest.approx(1141.0)
