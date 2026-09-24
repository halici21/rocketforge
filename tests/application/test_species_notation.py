"""Species labels in chemical case -- the names themselves untouched.

NASA CEA writes ``HCL``, ``AL2O3(L)``, ``NH4CLO4(I)`` and ``MgCL2``; the
interface shows HCl, Al2O3(L), NH4ClO4(I) and MgCl2. Two implementations carry
the rule -- ``rocketforge.application.species_notation.species_label`` for text
built in Python (table rows, copied text, condition rows) and
``Notation.species`` in QML for names drawn directly -- and these tests hold
them to the same answer, name by name.
"""

from __future__ import annotations

import pathlib
import re

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from rocketforge.application.species_notation import species_label

THEME = pathlib.Path(__file__).resolve().parents[2] / "ui" / "theme"

#: CEA name -> label. The representative set named for this change, then the
#: rest of what a solid (RP-1311 Example 5) and a LOX/LCH4 product set carry.
RECASED = [
    ("CL", "Cl"),
    ("HCL", "HCl"),
    ("MgCL2", "MgCl2"),
    ("AL2O3(L)", "Al2O3(L)"),
    ("NH4CLO4(I)", "NH4ClO4(I)"),
    ("AL(cr)", "Al(cr)"),
    ("AL2O3(a)", "Al2O3(a)"),
    ("MgCL", "MgCl"),
    ("CL2", "Cl2"),
    ("ALCL", "AlCl"),
    ("ALCL2", "AlCl2"),
    ("ALCL3", "AlCl3"),
    ("ALOH", "AlOH"),
    ("ALOHCL", "AlOHCl"),
    ("ALOHCL2", "AlOHCl2"),
    ("ALOCL", "AlOCl"),
    ("ALHCL2", "AlHCl2"),
    ("AL(OH)2CL", "Al(OH)2Cl"),
    ("AL(OH)2", "Al(OH)2"),
    ("AL(OH)3", "Al(OH)3"),
    ("NACL", "NaCl"),
    ("CACL2", "CaCl2"),
    ("HBR", "HBr"),
    ("BR2", "Br2"),
    ("SCL2", "SCl2"),
    ("CL-", "Cl-"),
]

#: Shown exactly as written: already in chemical case, a pair that would also
#: read as two one-letter elements, or not a formula at all.
UNCHANGED = [
    "H2O", "CO", "CO2", "*CO2", "NO", "NO2", "N2O4", "OH", "HO2", "HCO", "HCN",
    "COS", "CS2", "SO2", "H2S", "NH3", "CH4", "O2", "H2", "N2", "e-", "NO+",
    "Mg", "Mg(OH)2", "MgOH", "MgSO4(II)", "C8H18,isooctane", "NH4NO3(I)",
    "HCl", "MgCl2", "Al2O3(L)", "SIO2", "C(gr)",
    "HTPB", "HTPB R45M", "RP-1", "CHOS-Binder", "AP", "TAGN", "PETN", "MMH",
    "UDMH", "RDX", "HMX",
]


@pytest.mark.parametrize("name,expected", RECASED)
def test_a_cea_name_is_labelled_in_chemical_case(name, expected):
    assert species_label(name) == expected


@pytest.mark.parametrize("name", UNCHANGED)
def test_a_name_that_needs_no_recasing_or_cannot_be_read_is_left_alone(name):
    assert species_label(name) == name


@pytest.mark.parametrize("name,_expected", RECASED)
def test_the_label_is_idempotent(name, _expected):
    once = species_label(name)
    assert species_label(once) == once


def test_carbon_monoxide_is_never_cobalt():
    """The reason for the ambiguity guard, stated as a test."""
    assert species_label("CO") == "CO"
    assert species_label("NO") == "NO"
    assert species_label("HO2") == "HO2"
    assert species_label("COS") == "COS"


# ---------------------------------------------------------------------------
# QML: the same answer, plus formula subscripts
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def qml_species(qt_app):
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.setData(
        ("import QtQuick\nimport \"%s\"\nQtObject {\n"
         "  function species(t) { return Notation.species(t) }\n"
         "}" % THEME.as_uri()).encode("utf-8"),
        QUrl("file:///species_probe.qml"))
    obj = component.create()
    assert obj is not None, component.errorString()

    def call(text):
        return QMetaObject.invokeMethod(
            obj, "species", Qt.DirectConnection,
            Q_RETURN_ARG("QVariant"), Q_ARG("QVariant", text))

    yield call
    obj.deleteLater()
    engine.deleteLater()


def _plain(rich: str) -> str:
    return re.sub(r"</?sub>", "", rich).replace("&amp;", "&").replace(
        "&lt;", "<").replace("&gt;", ">")


@pytest.mark.parametrize("name", [n for n, _ in RECASED] + UNCHANGED)
def test_qml_and_python_show_the_same_label(qml_species, name):
    assert _plain(qml_species(name)) == species_label(name)


@pytest.mark.parametrize("name,expected", [
    ("CL", "Cl"),
    ("HCL", "HCl"),
    ("MgCL2", "MgCl<sub>2</sub>"),
    ("AL2O3(L)", "Al<sub>2</sub>O<sub>3</sub>(L)"),
    ("NH4CLO4(I)", "NH<sub>4</sub>ClO<sub>4</sub>(I)"),
    ("AL(OH)2CL", "Al(OH)<sub>2</sub>Cl"),
    ("Mg(OH)2", "Mg(OH)<sub>2</sub>"),
])
def test_qml_subscripts_counts_including_after_a_group(qml_species, name, expected):
    assert qml_species(name) == expected


# ---------------------------------------------------------------------------
# the identity is untouched where it is a key
# ---------------------------------------------------------------------------


def test_a_species_row_keeps_its_name_and_labels_it_in_chemical_case():
    from rocketforge.application.analysis.thermochemistry_service import SpeciesRow

    row = SpeciesRow(name="MgCL2", phase="gas", mole_fraction=0.001,
                     mass_fraction=0.004, display_name=species_label("MgCL2"))
    assert row.name == "MgCL2"
    assert row.label == "MgCl2"


def test_a_live_solid_solve_labels_rows_without_renaming_them(qt_app, gateway):
    """Through the real provider: names as CEA returns them, labels recased."""
    from rocketforge.application.analysis import thermochemistry_solid_service as solid
    from rocketforge.application.analysis.thermochemistry_service import species_rows

    if not gateway.availability().usable:
        pytest.skip("NASA CEA provider unavailable")
    option = solid.solid_formulation_named("rp1311-example5")
    case = solid.default_solid_case()
    outcome = solid.solve_solid_case(case)
    rows = {row.name: row for row in species_rows(outcome)}
    assert option is not None and rows, outcome
    for name, expected in (("HCL", "HCl"), ("CL", "Cl"), ("MgCL2", "MgCl2"),
                           ("AL2O3(L)", "Al2O3(L)")):
        if name in rows:
            assert rows[name].name == name
            assert rows[name].label == expected
