"""JSON-safe encoding of every public record.

Encoding only: the backend has no DTO decoding framework yet, and Phase 5B spec
section 122 permits encoding-only on that condition. What is tested is that the
encoding is complete, stable, lossless in precision, and free of ``repr()``
fallbacks.
"""

from __future__ import annotations

import json
import math

import pytest

from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest,
    ChamberGas,
    ChemistryMode,
    Composition,
    CompositionBasis,
    ElementalComposition,
    ElementalInventoryBasis,
    EquilibriumConstraint,
    ExpansionMode,
    ExpansionRequest,
    GasStation,
    MixtureRatio,
    Phase,
    PolynomialForm,
    PropellantPair,
    PropellantPairReferenceCase,
    ProviderCapabilities,
    ProviderCapability,
    Species,
    ThermoPolynomial,
    ThermochemistryProvenance,
    compare_elemental_inventories,
    to_jsonable,
    validate_chamber_gas,
)
from rocketforge.physics.thermochemistry.serialization import SERIALISABLE_TYPES

MOLE = CompositionBasis.MOLE_FRACTION


def roundtrip(value):
    """Encode, then prove the result survives ``json.dumps``/``loads``."""
    encoded = to_jsonable(value)
    return json.loads(json.dumps(encoded))


# ---------------------------------------------------------------------------
# coverage
# ---------------------------------------------------------------------------


def test_every_declared_serialisable_type_is_actually_covered(
        lox, liquid_methane, lox_stream, methane_stream, realistic_table):
    """The claim in SERIALISABLE_TYPES is proved, not asserted.

    One instance of every declared type is built and encoded. A type added to
    the list without an encoding path fails here rather than in production.
    """
    composition = Composition.from_fractions({"CO2": 0.4, "H2O": 0.6}, MOLE)
    inventory = composition.elemental(realistic_table)
    request = ChamberEquilibriumRequest(
        fuel=methane_stream, oxidiser=lox_stream,
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)
    chamber = ChamberGas(temperature=3500.0, gamma=1.14, gas_constant=346.0,
                         molar_mass=0.024, composition=composition)
    pair = PropellantPair(oxidiser=lox, fuel=liquid_methane)

    instances = {
        ElementalComposition: ElementalComposition.from_mapping({"C": 1.0}),
        ThermoPolynomial: ThermoPolynomial(
            form=PolynomialForm.NASA7, temperature_ranges=((200.0, 1000.0),),
            coefficients=(tuple([1.0] * 7),)),
        Species: realistic_table["CO2"],
        Composition: composition,
        type(inventory): inventory,
        type(compare_elemental_inventories(inventory, inventory)):
            compare_elemental_inventories(inventory, inventory),
        type(lox): lox,
        type(lox_stream): lox_stream,
        MixtureRatio: MixtureRatio(3.4),
        PropellantPair: pair,
        PropellantPairReferenceCase: PropellantPairReferenceCase(
            pair=pair, source="synthetic"),
        ChamberEquilibriumRequest: request,
        ExpansionRequest: ExpansionRequest(mode=ExpansionMode.FROZEN,
                                           pressure=1.0e5),
        ThermochemistryProvenance: ThermochemistryProvenance(provider_id="stub:x"),
        ProviderCapabilities: ProviderCapabilities(
            supported=frozenset({ProviderCapability.HP_EQUILIBRIUM})),
        ChamberGas: chamber,
        GasStation: GasStation(pressure=1.0e5, temperature=1500.0, gamma=1.2),
    }
    report = validate_chamber_gas(chamber)
    instances[type(report)] = report
    instances[type(report.checks[0])] = report.checks[0]

    missing = [t.__name__ for t in SERIALISABLE_TYPES if t not in instances]
    assert not missing, f"no instance built for: {missing}"
    for declared in SERIALISABLE_TYPES:
        encoded = roundtrip(instances[declared])
        assert encoded is not None, declared.__name__


def test_unknown_types_are_refused_rather_than_repr_ed():
    """No ``repr()`` fallback: an unencodable object is a bug, not a string."""
    class Foreign:
        pass

    with pytest.raises(TypeError, match="no JSON-safe encoding"):
        to_jsonable(Foreign())


# ---------------------------------------------------------------------------
# shape and stability
# ---------------------------------------------------------------------------


def test_enums_encode_as_their_values():
    assert to_jsonable(Phase.LIQUID) == "liquid"
    assert to_jsonable(CompositionBasis.MASS_FRACTION) == "mass_fraction"
    assert to_jsonable(ChemistryMode.EQUILIBRIUM) == "equilibrium"
    assert to_jsonable(EquilibriumConstraint.HP) == "HP"
    assert to_jsonable(ElementalInventoryBasis.PER_KILOGRAM_OF_MIXTURE) == \
        "per_kilogram_of_mixture"


def test_composition_encodes_as_an_object_with_its_basis():
    comp = Composition.from_fractions({"B": 0.25, "A": 0.75}, MOLE)
    encoded = roundtrip(comp)
    assert encoded["fractions"] == {"A": 0.75, "B": 0.25}
    assert encoded["basis"] == "mole_fraction"


def test_basis_is_always_present_in_the_encoding():
    """A serialised composition can never be read without its basis."""
    for basis in CompositionBasis:
        encoded = roundtrip(Composition.from_fractions({"A": 1.0}, basis))
        assert encoded["basis"] == basis.value


def test_encoding_is_order_stable():
    a = to_jsonable(Composition.from_fractions({"B": 0.25, "A": 0.75}, MOLE))
    b = to_jsonable(Composition.from_fractions({"A": 0.75, "B": 0.25}, MOLE))
    assert json.dumps(a) == json.dumps(b)


def test_capability_sets_encode_deterministically():
    caps = ProviderCapabilities(supported=frozenset({
        ProviderCapability.SP_EQUILIBRIUM, ProviderCapability.HP_EQUILIBRIUM,
        ProviderCapability.COMPOSITION}))
    first = json.dumps(to_jsonable(caps))
    second = json.dumps(to_jsonable(caps))
    assert first == second
    assert to_jsonable(caps)["supported"] == sorted(
        to_jsonable(caps)["supported"])


def test_canonicalisation_is_visible_in_the_encoding():
    """A corrected composition says so when it is written down."""
    comp = Composition.from_fractions({"A": 0.5, "B": 0.5 + 1.0e-11}, MOLE)
    encoded = roundtrip(comp)
    assert "canonicalised_from_sum" in encoded
    exact = roundtrip(Composition.from_fractions({"A": 0.5, "B": 0.5}, MOLE))
    assert "canonicalised_from_sum" not in exact


# ---------------------------------------------------------------------------
# precision and numeric hygiene
# ---------------------------------------------------------------------------


def test_floats_are_not_rounded():
    """Display precision belongs to the interface, not to storage."""
    value = 1.0 / 3.0
    comp = Composition.from_weights({"A": 1.0, "B": 2.0}, MOLE)
    encoded = roundtrip(comp)
    assert encoded["fractions"]["A"] == pytest.approx(value, rel=0.0, abs=0.0)
    assert repr(encoded["fractions"]["A"]) == repr(value)


def test_negative_zero_is_normalised_but_real_negatives_are_not():
    assert to_jsonable(-0.0) == 0.0
    assert not math.copysign(1.0, to_jsonable(-0.0)) < 0.0
    assert to_jsonable(-1.5) == -1.5


def test_nonfinite_values_are_refused():
    """A NaN should never have reached a validated record in the first place."""
    with pytest.raises(ValueError, match="not representable in JSON"):
        to_jsonable(float("nan"))
    with pytest.raises(ValueError):
        to_jsonable(float("inf"))


def test_none_encodes_as_null_and_is_not_replaced_by_a_default():
    station = GasStation(pressure=1.0e5, temperature=1500.0, gamma=1.2)
    encoded = roundtrip(station)
    assert encoded["composition"] is None
    assert encoded["condensed_mass_fraction"] is None


def test_nested_records_encode_all_the_way_down(methane_stream, lox_stream):
    request = ChamberEquilibriumRequest(
        fuel=methane_stream, oxidiser=lox_stream,
        oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)
    encoded = roundtrip(request)
    assert encoded["fuel"]["propellant"]["name"] == "CH4"
    assert encoded["fuel"]["propellant"]["reference_phase"] == "liquid"
    assert encoded["fuel"]["temperature"] == pytest.approx(111.643)
    assert encoded["oxidiser_fuel_ratio"]["value"] == pytest.approx(3.4)
    assert encoded["oxidiser_fuel_ratio"]["basis"] == "mass"
    assert encoded["equilibrium_constraint"] == "HP"


def test_provenance_encodes_its_data_identity():
    provenance = ThermochemistryProvenance(
        provider_id="cea", library_version="3.3.4", database="thermo.lib",
        database_sha256="8e5df1cca92d4a48663d1ee5a1372e6508c59cddc2247ceeca32f041a03ec52a",
        chemistry_mode=ChemistryMode.EQUILIBRIUM)
    encoded = roundtrip(provenance)
    assert encoded["provider_id"] == "cea"
    assert encoded["database_sha256"].startswith("8e5df1cc")
    assert encoded["chemistry_mode"] == "equilibrium"
