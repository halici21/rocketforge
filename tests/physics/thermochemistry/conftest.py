"""Shared fixtures for the thermochemistry tests.

**Every chemical record here is a TEST FIXTURE, not production data.** Nothing
in this file is imported by ``rocketforge`` and nothing in it is a catalogue.
Phase 5A deferred catalogue population deliberately, and Phase 5B ships the
schema rather than the data (Phase 5B spec sections 64, 166).

Two kinds of fixture, kept apart on purpose:

* **synthetic** species with round molar masses, used wherever a test asserts
  an exact hand-computable value. Their numbers are chosen for arithmetic, not
  for chemistry, and they are named so nobody mistakes them for real substances.
* **realistic** species with molar masses close to the real ones, used where a
  test needs a plausible mixture. Their molar masses are stated to the digits
  used and are not claimed to be authoritative; no test compares them against a
  published value.
"""

from __future__ import annotations

import pytest

from rocketforge.physics.thermochemistry import (
    Composition,
    CompositionBasis,
    ElementalComposition,
    Phase,
    PropellantDefinition,
    PropellantRole,
    PropellantStream,
    Species,
)


# ---------------------------------------------------------------------------
# synthetic species -- round numbers, exact arithmetic, obviously not real
# ---------------------------------------------------------------------------


@pytest.fixture
def light() -> Species:
    """A synthetic species of 10 g/mol with one atom of element ``L``."""
    return Species(name="LIGHT", phase=Phase.GAS, molar_mass=10.0e-3,
                   formula=ElementalComposition.from_mapping({"L": 1.0}),
                   source="synthetic test fixture")


@pytest.fixture
def heavy() -> Species:
    """A synthetic species of 90 g/mol with one atom of element ``H_``."""
    return Species(name="HEAVY", phase=Phase.GAS, molar_mass=90.0e-3,
                   formula=ElementalComposition.from_mapping({"H_": 1.0}),
                   source="synthetic test fixture")


@pytest.fixture
def synthetic_table(light: Species, heavy: Species) -> dict[str, Species]:
    return {light.name: light, heavy.name: heavy}


# ---------------------------------------------------------------------------
# realistic species -- plausible molar masses, never compared to a publication
# ---------------------------------------------------------------------------


def _sp(name: str, phase: Phase, molar_mass_g_per_mol: float,
        atoms: dict[str, float]) -> Species:
    return Species(name=name, phase=phase,
                   molar_mass=molar_mass_g_per_mol * 1.0e-3,
                   formula=ElementalComposition.from_mapping(atoms),
                   source="test fixture; molar mass to the digits shown")


@pytest.fixture
def realistic_table() -> dict[str, Species]:
    """A small CHO species set, keyed by name.

    Keys are plain names because every species here is a gas. Where two phases
    of one substance coexist a test keys on ``Species.canonical_id`` instead.
    """
    return {
        "CH4": _sp("CH4", Phase.GAS, 16.04246, {"C": 1.0, "H": 4.0}),
        "O2": _sp("O2", Phase.GAS, 31.9988, {"O": 2.0}),
        "CO": _sp("CO", Phase.GAS, 28.0101, {"C": 1.0, "O": 1.0}),
        "CO2": _sp("CO2", Phase.GAS, 44.0095, {"C": 1.0, "O": 2.0}),
        "H2O": _sp("H2O", Phase.GAS, 18.01528, {"H": 2.0, "O": 1.0}),
        "H2": _sp("H2", Phase.GAS, 2.01588, {"H": 2.0}),
        "OH": _sp("OH", Phase.GAS, 17.00734, {"O": 1.0, "H": 1.0}),
        "H": _sp("H", Phase.GAS, 1.00794, {"H": 1.0}),
        "O": _sp("O", Phase.GAS, 15.9994, {"O": 1.0}),
    }


@pytest.fixture
def water_gas() -> Species:
    return _sp("H2O", Phase.GAS, 18.01528, {"H": 2.0, "O": 1.0})


@pytest.fixture
def water_liquid() -> Species:
    """Liquid water. Same formula and molar mass, different phase.

    The pair exists so tests can prove that phase participates in identity.
    """
    return Species(name="H2O", phase=Phase.LIQUID, molar_mass=18.01528e-3,
                   formula=ElementalComposition.from_mapping({"H": 2.0, "O": 1.0}),
                   source="test fixture")


@pytest.fixture
def condensed_carbon() -> Species:
    return Species(name="C(gr)", phase=Phase.SOLID, molar_mass=12.0107e-3,
                   formula=ElementalComposition.from_mapping({"C": 1.0}),
                   source="test fixture")


# ---------------------------------------------------------------------------
# propellants and streams
# ---------------------------------------------------------------------------


@pytest.fixture
def lox() -> PropellantDefinition:
    """Liquid oxygen at its normal boiling point as the reference condition."""
    return PropellantDefinition(
        name="LOX", role=PropellantRole.OXIDISER,
        composition=Composition.pure("O2"),
        reference_temperature=90.17, reference_phase=Phase.LIQUID,
        density_hint=1141.0,
        provider_names={"cea": "O2(L)"},
        source="test fixture",
    )


@pytest.fixture
def liquid_methane() -> PropellantDefinition:
    return PropellantDefinition(
        name="CH4", role=PropellantRole.FUEL,
        composition=Composition.pure("CH4"),
        reference_temperature=111.643, reference_phase=Phase.LIQUID,
        density_hint=422.6,
        provider_names={"cea": "CH4(L)"},
        source="test fixture",
    )


@pytest.fixture
def lox_stream(lox: PropellantDefinition) -> PropellantStream:
    return PropellantStream(propellant=lox, temperature=90.17,
                            pressure=3.0e6, phase=Phase.LIQUID, mass_flow=3.4)


@pytest.fixture
def methane_stream(liquid_methane: PropellantDefinition) -> PropellantStream:
    return PropellantStream(propellant=liquid_methane, temperature=111.643,
                            pressure=3.0e6, phase=Phase.LIQUID, mass_flow=1.0)


@pytest.fixture
def blend_oxidiser() -> PropellantDefinition:
    """A 90 % / 10 % blend stated on a MASS basis, as such specifications are."""
    return PropellantDefinition(
        name="H2O2-90", role=PropellantRole.OXIDISER,
        composition=Composition.from_fractions(
            {"H2O2": 0.90, "H2O": 0.10}, CompositionBasis.MASS_FRACTION),
        reference_temperature=298.15, reference_phase=Phase.LIQUID,
        source="test fixture",
    )
