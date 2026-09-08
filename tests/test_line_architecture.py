"""Static rules for engineering.line.

Every scan has a negative control beside it. A scan that passes because it is
looking in the wrong place is worse than no scan.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE_ROOT = PROJECT_ROOT / "rocketforge"
LINE = PACKAGE_ROOT / "engineering" / "line"
UI = PROJECT_ROOT / "ui"


def modules():
    return sorted(p for p in LINE.rglob("*.py") if "__pycache__" not in p.parts)


def absolute_import_roots(source: str) -> set[str]:
    """Top-level package of every absolute import. Relative imports skipped."""
    roots: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            if node.module:
                roots.add(node.module.split(".")[0])
    return roots


def dotted_paths(source: str) -> set[str]:
    paths: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and not node.level and node.module:
            paths.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                paths.add(alias.name)
    return paths


def attribute_reads(source: str, name: str) -> list[int]:
    """Lines where ``name`` is read as a value. Prose does not count."""
    lines: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and node.attr == name:
            lines.append(node.lineno)
        elif isinstance(node, ast.Name) and node.id == name:
            lines.append(node.lineno)
    return lines


# --- the scanners are checked first --------------------------------------

def test_the_import_scan_sees_a_function_local_import():
    assert "CoolProp" in absolute_import_roots(
        "def f():\n    import CoolProp\n    return CoolProp")


def test_the_import_scan_ignores_relative_imports():
    assert absolute_import_roots("from .relations import circular_area") == set()


def test_the_attribute_scan_ignores_prose_but_catches_a_read():
    assert attribute_reads('"""never read density_hint."""\nx = 1\n',
                           "density_hint") == []
    assert attribute_reads("rho = p.density_hint\n", "density_hint") == [1]


# --- the layer -----------------------------------------------------------

FORBIDDEN = {"PySide6", "PySide2", "PyQt5", "PyQt6", "shiboken6", "CoolProp",
             "cea", "cantera", "rocketcea", "scipy", "pandas"}


@pytest.mark.parametrize("path", modules(), ids=lambda p: p.name)
def test_the_line_package_imports_no_provider_no_qt_and_no_library(path):
    roots = absolute_import_roots(path.read_text(encoding="utf-8"))
    assert not (roots & FORBIDDEN), sorted(roots & FORBIDDEN)


@pytest.mark.parametrize("path", modules(), ids=lambda p: p.name)
def test_the_line_package_reaches_only_core_and_physics_fluids(path):
    for dotted in dotted_paths(path.read_text(encoding="utf-8")):
        if not dotted.startswith("rocketforge"):
            continue
        assert (dotted.startswith("rocketforge.core")
                or dotted.startswith("rocketforge.physics.fluids")), (
            f"{path.name} imports {dotted}; a line depends on core and the "
            "fluid domain, and on nothing else in the project")


@pytest.mark.parametrize("path", modules(), ids=lambda p: p.name)
def test_the_line_package_never_imports_the_application_layer(path):
    for dotted in dotted_paths(path.read_text(encoding="utf-8")):
        assert not dotted.startswith("rocketforge.application")


@pytest.mark.parametrize("path", modules(), ids=lambda p: p.name)
def test_the_line_package_uses_only_the_public_fluids_api(path):
    for dotted in dotted_paths(path.read_text(encoding="utf-8")):
        if dotted.startswith("rocketforge.physics.fluids"):
            assert dotted == "rocketforge.physics.fluids", (
                f"{path.name} reaches into {dotted}; the line consumes the "
                "package's public API, not its internals")


def test_the_forbidden_set_would_catch_a_violation():
    assert absolute_import_roots("import CoolProp") & FORBIDDEN


# --- density_hint --------------------------------------------------------

@pytest.mark.parametrize("path", modules(), ids=lambda p: p.name)
def test_no_line_module_reads_density_hint(path):
    hits = attribute_reads(path.read_text(encoding="utf-8"), "density_hint")
    assert not hits, f"{path.name} reads density_hint at {hits}"


def test_the_line_reads_density_from_the_fluid_state():
    source = (LINE / "solve.py").read_text(encoding="utf-8")
    assert "FluidProperty.DENSITY" in source
    assert "FluidProperty.DYNAMIC_VISCOSITY" in source


# --- chamber pressure is not line pressure -------------------------------

@pytest.mark.parametrize("path", modules(), ids=lambda p: p.name)
def test_no_line_module_mentions_a_chamber_pressure(path):
    hits = attribute_reads(path.read_text(encoding="utf-8"), "chamber_pressure")
    assert not hits, f"{path.name} reads chamber_pressure at {hits}"


def test_the_chamber_pressure_scan_would_catch_a_substitution():
    assert attribute_reads("p = request.chamber_pressure\n",
                           "chamber_pressure") == [1]


# --- scope ---------------------------------------------------------------

@pytest.mark.parametrize("name", ["valve", "orifice", "injector", "pump",
                                  "turbine", "cooling", "tank",
                                  "heat_exchanger"])
def test_no_neighbouring_component_was_created(name):
    assert not (PACKAGE_ROOT / "engineering" / name).exists()
    assert not (PACKAGE_ROOT / "engineering" / f"{name}.py").exists()


def test_no_minor_loss_vocabulary_appears_in_the_line_package():
    """Minor losses belong to the components that own them, not hidden here."""
    forbidden = {"minor_loss", "loss_coefficient", "k_factor", "cv", "kv",
                 "discharge_coefficient", "elevation_head", "pump_head",
                 "entrance_loss", "bend_loss"}
    for path in modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        assert not (names & forbidden), f"{path.name}: {names & forbidden}"


def test_the_minor_loss_scan_would_catch_one():
    tree = ast.parse("def loss_coefficient(k):\n    return k\n")
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "loss_coefficient" in names


# --- QML holds no line physics -------------------------------------------
#
# Scoped to the Line page, and looking for the *equation*, not for tokens.
#
# The first version of this rule scanned every QML file for substrings and
# flagged four innocents: three drawing primitives using ``Math.PI *`` for arcs,
# and the Fanno page, whose ``frictionFactor`` lines are a property binding and
# a setter -- a display of a value its own backend computed. That is the exact
# substring trap this project has hit before, so the rule now names the file it
# governs and looks for the constants that only appear in the correlation.

#: Constants that appear in the Colebrook equation and nowhere in a layout.
COLEBROOK_CONSTANTS = ("2.51", "3.7)", "/ 3.7", "64 /", "64/")

LINE_PAGE = UI / "pages" / "LinePage.qml"


def line_qml_files():
    files = [LINE_PAGE] if LINE_PAGE.is_file() else []
    directory = UI / "pages" / "line"
    if directory.is_dir():
        files.extend(sorted(directory.rglob("*.qml")))
    return files


def strip_qml_comments(text: str) -> str:
    """Remove // and /* */ comments.

    Needed, and found out the hard way: the Line page's own header comment
    explains that nothing interpolates "between 64/Re and Colebrook", and the
    first version of this rule flagged that sentence. A scan that cannot tell
    an explanation from an equation is the substring trap again.
    """
    import re

    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", text)


@pytest.mark.skipif(not LINE_PAGE.is_file(), reason="the Line page does not exist yet")
def test_the_line_page_contains_no_colebrook_constant():
    for path in line_qml_files():
        text = strip_qml_comments(path.read_text(encoding="utf-8"))
        found = [c for c in COLEBROOK_CONSTANTS if c in text]
        assert not found, f"{path.name} contains {found}"


def test_the_comment_stripper_keeps_code_and_drops_prose():
    line_comment = "// mentions 2.51 in prose\nx = 1"
    block_comment = "/* 2.51 */\nx = 1"
    assert "2.51" not in strip_qml_comments(line_comment)
    assert "2.51" not in strip_qml_comments(block_comment)
    assert "2.51" in strip_qml_comments("var a = 2.51 / re")


@pytest.mark.skipif(not LINE_PAGE.is_file(), reason="the Line page does not exist yet")
def test_the_line_page_defines_no_javascript_function():
    """A layout binds and formats. A function in it is a place for physics."""
    for path in line_qml_files():
        text = path.read_text(encoding="utf-8")
        assert "function " not in text or "onValueEdited: function" in text, (
            f"{path.name} defines a JavaScript function")


def test_the_colebrook_constant_scan_would_catch_an_equation():
    snippet = "var x = -2 * Math.log10(eps / 3.7 + 2.51 / (re * Math.sqrt(f)))"
    assert [c for c in COLEBROOK_CONSTANTS if c in snippet]


def test_the_scan_does_not_fire_on_drawing_geometry_or_a_binding():
    """The two false positives the first version of this rule produced."""
    assert not [c for c in COLEBROOK_CONSTANTS
                if c in "ctx.arc(x, y, r, 0, Math.PI * 2)"]
    assert not [c for c in COLEBROOK_CONSTANTS
                if c in "value: Fanno.frictionFactor"]


# --- QML must not reference a singleton that does not exist --------------
#
# Added because two pages shipped bindings to ``Palette.textMuted``. There is
# no ``Palette`` singleton -- the theme singleton is ``Theme`` -- so every one
# of those bindings was undefined. Nothing caught it, because the workspace
# tour renders those pages *empty*, and an unevaluated binding is silent.
#
# Two rules follow: name only singletons that exist, and make the tour
# populate the pages so their delegates are actually evaluated.

THEME_SINGLETONS = {"Theme", "Metrics", "Typography", "Motion"}


def qml_singleton_prefixes(text: str) -> set[str]:
    """Capitalised dotted prefixes used as value sources in a QML file."""
    import re

    return set(re.findall(r"\b([A-Z][A-Za-z0-9]*)\.[a-z][A-Za-z0-9]*", text))


def project_component_names() -> set[str]:
    """Every QML component this project defines, by file name.

    Structural rather than enumerated: a hand-written allowlist goes stale the
    first time someone adds a component, and a stale allowlist is a rule that
    fails for the wrong reason.
    """
    return {p.stem for p in UI.rglob("*.qml")}


#: Types and singletons that come from Qt itself rather than from this project.
QT_PROVIDED = {
    "Qt", "Text", "Layout", "Component", "Math", "JSON", "Object", "Number",
    "String", "Date", "Array", "Boolean", "Item", "Image", "Shape", "Canvas",
    "ShapePath", "PathAngleArc", "Behavior", "NumberAnimation",
    "ColorAnimation", "Repeater", "Connections", "Binding", "Screen", "Window",
    "Keys", "ScrollBar", "Flickable", "ListView", "GridView", "MouseArea",
    "Rectangle", "Column", "Row", "Grid", "Loader", "Timer", "Gradient",
    "GradientStop", "FontMetrics", "TextMetrics", "TextInput", "TextEdit",
}

#: Controllers registered as QML singletons in ``main.py``.
CONTROLLER_SINGLETONS = {
    "App", "Navigation", "Thermochemistry", "RocketPerformance", "TradeStudy",
    "FluidProperties", "Line", "Isentropic", "MassFlow", "NormalShock",
    "ObliqueShock", "Fanno", "PrandtlMeyer", "Rayleigh", "Nozzle", "MockData",
}


def test_no_page_references_an_unknown_singleton():
    """Two pages shipped bindings to a ``Palette`` singleton that does not
    exist, and nothing noticed because the tour never rendered the delegates
    that used it."""
    known = (THEME_SINGLETONS | QT_PROVIDED | CONTROLLER_SINGLETONS
             | project_component_names())
    offenders = []
    for path in (UI / "pages").rglob("*.qml"):
        text = strip_qml_comments(path.read_text(encoding="utf-8"))
        for prefix in qml_singleton_prefixes(text):
            if prefix not in known:
                offenders.append((path.name, prefix))
    assert not offenders, offenders


def test_the_singleton_scan_would_catch_the_defect_it_was_written_for():
    assert "Palette" in qml_singleton_prefixes("color: Palette.textMuted")
    known = (THEME_SINGLETONS | QT_PROVIDED | CONTROLLER_SINGLETONS
             | project_component_names())
    assert "Palette" not in known
    assert "Theme" in qml_singleton_prefixes("color: Theme.textMuted")
