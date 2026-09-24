"""The species display contract: an identifier is not a label.

Two concepts, kept apart everywhere:

* the CANONICAL PROVIDER IDENTIFIER -- exactly what NASA CEA returns ("HCL",
  "MgCL2", "AL2O3(L)"). It keys the composition, the sweep selection, the
  condensed list, the ingredient rows; it is what a result is compared by.
* the DISPLAY CHEMICAL NOTATION -- the label a person reads ("HCl", "MgCl2",
  "Al2O3(L)"), from ``species_label`` and ``Notation.species``.

These tests run the real provider (they skip without it) because the stub's
species happen to be written in chemical case already, and a contract that
only holds where the two strings are equal proves nothing.
"""

from __future__ import annotations

import pytest

from rocketforge.application.analysis.thermochemistry_controller import (
    ThermochemistryController,
)
from rocketforge.application.analysis.thermochemistry_service import species_rows
from rocketforge.application.species_notation import species_label


@pytest.fixture()
def solid(qt_app, gateway):
    if not gateway.availability().usable:
        pytest.skip("NASA CEA provider unavailable")
    controller = ThermochemistryController()
    controller.formulationKind = "solid"
    controller.loadSolidFormulation("rp1311-example5")
    controller.calculate()
    assert controller.hasResult, controller.statusMessage
    return controller


def test_the_solved_set_really_has_names_that_differ_from_their_labels(solid):
    """The premise: without such species the rest would be vacuous."""
    rows = species_rows(solid._outcome)
    differing = [r for r in rows if r.label != r.name]
    assert {"HCL", "CL", "MgCL2", "AL2O3(L)"} <= {r.name for r in differing}


def test_the_composition_is_keyed_by_identifier_never_by_label(solid):
    state = solid._outcome.state
    keys = set(dict(state.composition.fractions))
    for row in species_rows(solid._outcome):
        assert row.name in keys
        if row.label != row.name:
            assert row.label not in keys, (row.name, row.label)


def test_every_identity_the_controller_publishes_is_the_identifier(solid):
    names = {r.name for r in species_rows(solid._outcome)}
    leading = solid.leadingSpecies["rows"]
    assert all(row["name"] in names for row in leading)
    assert any(row["label"] != row["name"] for row in leading)       # Al2O3(L)
    assert set(solid.condensed["species"]) <= names
    assert "AL2O3(L)" in solid.condensed["species"]
    assert [row["name"] for row in solid.solidIngredients][:1] == ["NH4CLO4(I)"]
    assert set(solid.speciesSet) <= names | {""}


def test_the_sweep_chips_select_by_identifier_and_show_the_label():
    """The one QML place a species is both shown and used as a key."""
    import pathlib

    qml = (pathlib.Path(__file__).resolve().parents[2] / "ui" / "pages"
           / "thermochemistry" / "ThermoSweep.qml").read_text(encoding="utf-8")
    assert "Thermochemistry.sweepSpecies.indexOf(modelData)" in qml
    assert "Notation.species(modelData)" in qml


def test_copy_table_is_for_a_person(solid):
    text = solid.copyComposition()
    lines = text.splitlines()
    species = [line.split("\t")[0] for line in lines[1:]]
    assert "HCl" in species and "HCL" not in species
    assert "Al2O3(L)" in species and "AL2O3(L)" not in species
    # The numbers are the table's own display text, unchanged by the labels.
    model = solid.compositionModel
    first = lines[1].split("\t")
    assert first[2] == model.data(model.index(0, 2))


def test_the_label_is_a_pure_function_of_the_identifier():
    for name in ("HCL", "MgCL2", "AL2O3(L)", "NH4CLO4(I)", "CO", "HTPB"):
        assert species_label(name) == species_label(name)
        assert species_label(species_label(name)) == species_label(name)
