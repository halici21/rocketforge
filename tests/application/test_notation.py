"""The presentation-layer notation formatter, ui/theme/Notation.qml.

Every label that shows a quantity symbol passes through ``Notation.rich``. The
backend keeps plain labels -- they are test contracts and they reach exported
files -- so these tests are the contract for what the screen shows instead.
"""

from __future__ import annotations

import json
import pathlib

import pytest
from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

THEME = pathlib.Path(__file__).resolve().parents[2] / "ui" / "theme"


@pytest.fixture(scope="module")
def notation(qt_app):
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.setData(
        ("import QtQuick\nimport \"%s\"\nQtObject {\n"
         "  function rich(t) { return Notation.rich(t) }\n"
         "  function plain(t) { return Notation.plain(t) }\n"
         "  function isRich(t) { return Notation.isRich(t) }\n"
         "  function textFormat(t) { return Notation.textFormat(t) }\n"
         "  function runs(t) { return JSON.stringify(Notation.runs(t)) }\n"
         "  function sectionRich(t) { return Notation.sectionRich(t) }\n"
         "  function species(t) { return Notation.species(t) }\n"
         "}" % THEME.as_uri()).encode("utf-8"),
        QUrl("file:///notation_probe.qml"))
    obj = component.create()
    assert obj is not None, component.errorString()

    def call(name, text):
        return QMetaObject.invokeMethod(
            obj, name, Qt.DirectConnection,
            Q_RETURN_ARG("QVariant"), Q_ARG("QVariant", text))

    yield call
    obj.deleteLater()
    engine.deleteLater()


# ---------------------------------------------------------------------------
# ISO 80000-2: italic quantity, upright descriptive subscript
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("plain,expected", [
    ("Chamber pressure  p_c", "Chamber pressure  <i>p</i><sub>c</sub>"),
    ("Chamber temperature  T_0", "Chamber temperature  <i>T</i><sub>0</sub>"),
    ("Exit Mach number  M_e", "Exit Mach number  <i>M</i><sub>e</sub>"),
    ("Effective exhaust velocity  c_eff",
     "Effective exhaust velocity  <i>c</i><sub>eff</sub>"),
    ("Grain temperature  T_grain", "Grain temperature  <i>T</i><sub>grain</sub>"),
    ("Hydraulic diameter  D_h   [m]", "Hydraulic diameter  <i>D</i><sub>h</sub>   [m]"),
    ("Maximum deflection  θ_max", "Maximum deflection  <i>θ</i><sub>max</sub>"),
])
def test_a_descriptive_subscript_is_upright(notation, plain, expected):
    assert notation("rich", plain) == expected


@pytest.mark.parametrize("plain,expected", [
    ("Frozen specific heat  c_p,fr", "Frozen specific heat  <i>c</i><sub><i>p</i>,fr</sub>"),
    ("c_v", "<i>c</i><sub><i>v</i></sub>"),
    ("Frozen exponent cp/cv",
     "Frozen exponent <i>c</i><sub><i>p</i></sub>/<i>c</i><sub><i>v</i></sub>"),
])
def test_a_subscript_that_is_a_quantity_stays_italic(notation, plain, expected):
    """c_p: constant pressure. The p is a quantity, not a place."""
    assert notation("rich", plain) == expected


@pytest.mark.parametrize("plain,expected", [
    ("Specific impulse  Isp", "Specific impulse  <i>I</i><sub>sp</sub>"),
    ("Thrust coefficient  Cf", "Thrust coefficient  <i>C</i><sub>f</sub>"),
    ("Characteristic velocity  c*", "Characteristic velocity  <i>c</i>*"),
    ("Mass flow  mdot", "Mass flow  <i>ṁ</i>"),
    ("Area ratio  Ae/At", "Area ratio  <i>A</i><sub>e</sub>/<i>A</i><sub>t</sub>"),
    ("Isentropic exponent  gamma_s", "Isentropic exponent  <i>γ</i><sub>s</sub>"),
    ("Upstream Mach number  M₁", "Upstream Mach number  <i>M</i><sub>1</sub>"),
    ("back pressure  p_b/p₀", "back pressure  <i>p</i><sub>b</sub>/<i>p</i><sub>0</sub>"),
    ("4 f_F L/D", "4 <i>f</i><sub>F</sub> <i>L</i>/<i>D</i>"),
    ("Δp across the line", "Δ<i>p</i> across the line"),
])
def test_named_and_compound_forms(notation, plain, expected):
    assert notation("rich", plain) == expected


@pytest.mark.parametrize("plain,expected", [
    ("Flow deflection  θ  [deg]", "Flow deflection  <i>θ</i>  [deg]"),
    ("Density  ρ", "Density  <i>ρ</i>"),
    ("Mach number  M", "Mach number  <i>M</i>"),
    ("Specific gas constant  R", "Specific gas constant  <i>R</i>"),
    ("M = 1  ·  choking", "<i>M</i> = 1  ·  choking"),
])
def test_a_lone_symbol_is_italic(notation, plain, expected):
    assert notation("rich", plain) == expected


# ---------------------------------------------------------------------------
# what must not change
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("plain", [
    "Mixture ratio  O/F",          # an abbreviation, not two quantities
    "thrust_coefficient",          # an identifier
    "Condensed products",
    "Reference / validation case",
])
def test_non_notation_is_left_alone(notation, plain):
    assert notation("rich", plain) == plain
    assert notation("isRich", plain) is False


def test_markup_is_never_injected_from_plain_text(notation):
    """In RichText a literal "<" opens a tag: "p < p_crit" rendered as "p". Measured."""
    out = notation("rich", "p < p_crit & x > 0")
    assert out == "p &lt; <i>p</i><sub>crit</sub> &amp; x &gt; 0"


def test_already_rich_text_passes_through(notation):
    authored = "Chamber pressure  <i>p</i><sub>c</sub>"
    assert notation("rich", authored) == authored


def test_plain_labels_keep_plain_text_and_its_eliding(notation):
    """RichText does not elide, so it is used only where notation needs it."""
    plain_format = notation("textFormat", "Mixture ratio  O/F")
    rich_format = notation("textFormat", "Chamber pressure  p_c")
    assert plain_format != rich_format


# ---------------------------------------------------------------------------
# Canvas runs and plain text
# ---------------------------------------------------------------------------


def test_runs_split_italic_and_subscript_for_a_canvas(notation):
    runs = json.loads(notation("runs", "Specific impulse  Isp [s]"))
    assert [(r["text"], r["italic"], r["sub"]) for r in runs] == [
        ("Specific impulse  ", False, False),
        ("I", True, False),
        ("sp", False, True),
        (" [s]", False, False),
    ]


def test_runs_decode_escaped_characters(notation):
    runs = json.loads(notation("runs", "p < 1"))
    assert "".join(r["text"] for r in runs) == "p < 1"


def test_plain_is_readable_without_markup(notation):
    assert notation("plain", "Specific impulse  Isp") == "Specific impulse  Isp"


@pytest.mark.parametrize("authored", [
    "<b>Isentropic</b> relations",       # the Equation Library writes <b>
    "first line<br>second line",
])
def test_any_authored_markup_passes_through_unescaped(notation, authored):
    """Escaping authored markup would print its tags on screen."""
    assert notation("rich", authored) == authored


@pytest.mark.parametrize("plain", ["a < b", "O/F & pressure", "values > 0"])
def test_plain_text_without_notation_is_returned_unescaped(notation, plain):
    """It is shown as PlainText, where "&lt;" would print as four characters."""
    assert notation("rich", plain) == plain
    runs = json.loads(notation("runs", plain))
    assert "".join(r["text"] for r in runs) == plain


@pytest.mark.parametrize("plain,expected", [
    ("Constant-property gas: gamma and R fixed", "Constant-property gas: <i>γ</i> and R fixed"),
    ("Cf = Cf_momentum + Cf_pressure",
     "<i>C</i><sub>f</sub> = <i>C</i><sub>f,momentum</sub> + <i>C</i><sub>f,pressure</sub>"),
])
def test_prose_gamma_and_thrust_coefficient_terms(notation, plain, expected):
    assert notation("rich", plain) == expected


def test_a_code_identifier_is_left_exactly_as_written(notation):
    """Provenance names a real field; renaming it would point at nothing."""
    assert notation("rich", "ChamberGas.gamma_frozen") == "ChamberGas.gamma_frozen"


@pytest.mark.parametrize("plain,expected", [
    ("T/T*", "<i>T</i>/<i>T</i>*"),
    ("p/p*", "<i>p</i>/<i>p</i>*"),
    ("ρ/ρ*", "<i>ρ</i>/<i>ρ</i>*"),
    ("p₀/p₀*", "<i>p</i><sub>0</sub>/<i>p</i><sub>0</sub>*"),
    ("T₀/T₀*", "<i>T</i><sub>0</sub>/<i>T</i><sub>0</sub>*"),
    ("p₀₂/p₁", "<i>p</i><sub>02</sub>/<i>p</i><sub>1</sub>"),
    ("Δs/R", "Δ<i>s</i>/<i>R</i>"),
])
def test_starred_and_shock_ratios(notation, plain, expected):
    assert notation("rich", plain) == expected


@pytest.mark.parametrize("name,expected", [
    ("H2O", "H<sub>2</sub>O"),
    ("CO2", "CO<sub>2</sub>"),
    ("*CO2", "*CO<sub>2</sub>"),
    ("AL2O3(L)", "Al<sub>2</sub>O<sub>3</sub>(L)"),
    ("AL2O3(a)", "Al<sub>2</sub>O<sub>3</sub>(a)"),
    ("NH4CLO4(I)", "NH<sub>4</sub>ClO<sub>4</sub>(I)"),
    ("MgSO4(II)", "MgSO<sub>4</sub>(II)"),
    ("C8H18,isooctane", "C<sub>8</sub>H<sub>18</sub>,isooctane"),
])
def test_a_species_name_gets_chemical_case_and_formula_subscripts(notation, name, expected):
    """The label is in chemical case; the phase suffix is never recased.

    (Until Analysis Experience Phase 2 the label kept CEA's own case -- "AL2O3",
    "NH4CLO4". The name still does, everywhere it is an identity; only what is
    shown changed. See rocketforge/application/species_notation.py.)
    """
    assert notation("species", name) == expected


@pytest.mark.parametrize("name", ["HTPB", "HTPB R45M", "RP-1", "e-", "AP"])
def test_a_name_that_is_not_a_counted_formula_is_unchanged(notation, name):
    assert notation("species", name) == name


def test_an_uncounted_formula_is_recased_but_not_subscripted(notation):
    assert notation("species", "AL(cr)") == "Al(cr)"


@pytest.mark.parametrize("plain", [
    "thermo.lib 8e5df1cc",           # a provenance hash
    "3.44737e6",                     # a number
    "H2O",                           # a species outside a species column
    "AL2O3(L)",
    "NH4CLO4(I)",
])
def test_general_labels_never_get_chemistry_rewriting(notation, plain):
    """Formula subscripts live in species columns only; a label keeps its digits."""
    assert notation("rich", plain) == plain


@pytest.mark.parametrize("plain,expected", [
    ("Normal component  Mn₁", "Normal component  <i>M</i><sub>n,1</sub>"),
    ("MFP = ṁ√(RT₀)/(Ap₀)",
     "MFP = <i>ṁ</i>√(<i>R</i><i>T</i><sub>0</sub>)/(<i>A</i><i>p</i><sub>0</sub>)"),
    ("value (γ+1)²/(4γ)", "value (<i>γ</i>+1)²/(4<i>γ</i>)"),
])
def test_normal_mach_products_and_coefficients(notation, plain, expected):
    assert notation("rich", plain) == expected


def test_a_line_break_survives_rich_text(notation):
    """RichText collapses a newline into a space; the Pareto readout is multi-line."""
    assert notation("rich", "Point 3\nSpecific impulse  Isp") == \
        "Point 3<br>Specific impulse  <i>I</i><sub>sp</sub>"


@pytest.mark.parametrize("plain,expected", [
    ("p₀/p  versus  M", "<i>p</i><sub>0</sub>/<i>p</i>  VERSUS  <i>M</i>"),
    ("Maximum attached θ_max", "MAXIMUM ATTACHED <i>θ</i><sub>max</sub>"),
    ("4f_F L*/D  versus  M", "4 <i>f</i><sub>F</sub> <i>L</i>*/<i>D</i>  VERSUS  <i>M</i>"),
])
def test_a_section_label_uppercases_prose_and_never_a_symbol(notation, plain, expected):
    """Font.AllUppercase would turn the quantity p into P and θ into Θ."""
    assert notation("sectionRich", plain) == expected


def test_a_section_label_without_notation_is_left_to_the_component(notation):
    assert notation("sectionRich", "Stagnation state and geometry") == \
        "Stagnation state and geometry"
