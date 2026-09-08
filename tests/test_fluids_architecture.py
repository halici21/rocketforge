"""Static rules for the fluids foundation and the reactant coupling.

Every scan here is an AST walk with a **negative control** beside it: a scan
that passes because it is looking in the wrong place is worse than no scan, and
Phase 5G found four of those in its own audit code. Each rule below is
therefore paired with a fixture the rule must reject.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE_ROOT = PROJECT_ROOT / "rocketforge"

FLUIDS_DOMAIN = PACKAGE_ROOT / "physics" / "fluids"
FLUID_PROVIDERS = PACKAGE_ROOT / "providers" / "fluid_properties"
PROPELLANT_METRICS = PACKAGE_ROOT / "engineering" / "propellants"
COUPLING = PACKAGE_ROOT / "providers" / "cea" / "enthalpy_coupling.py"


def modules_under(root: pathlib.Path) -> list[pathlib.Path]:
    if root.is_file():
        return [root]
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def absolute_import_roots(source: str) -> set[str]:
    """Top-level package of every **absolute** import in a module.

    Relative imports are skipped deliberately. ``from .analysis import x``
    records ``analysis`` in ``node.module`` with ``level`` 1, and a scan that
    ignores the level reports every sibling module as a third-party
    dependency -- which is exactly the defect Phase 5G found in its own
    dependency audit.
    """
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
    """Every absolute ``from a.b.c import`` module path in a module."""
    paths: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and not node.level and node.module:
            paths.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                paths.add(alias.name)
    return paths


# --- the import-scan helper is itself checked ----------------------------

def test_the_import_scan_finds_an_absolute_import():
    assert "CoolProp" in absolute_import_roots("import CoolProp")
    assert "PySide6" in absolute_import_roots("from PySide6.QtCore import QObject")


def test_the_import_scan_ignores_relative_imports():
    assert absolute_import_roots("from .states import FluidState") == set()
    assert absolute_import_roots("from ..core import x") == set()


def test_the_import_scan_sees_a_function_local_import():
    source = "def f():\n    import CoolProp\n    return CoolProp"
    assert "CoolProp" in absolute_import_roots(source)


# --- physics.fluids is the fundamental layer -----------------------------

FORBIDDEN_IN_DOMAIN = {"PySide6", "PySide2", "PyQt5", "PyQt6", "shiboken6",
                       "CoolProp", "cea", "cantera", "rocketcea", "scipy",
                       "pandas"}


@pytest.mark.parametrize("path", modules_under(FLUIDS_DOMAIN),
                         ids=lambda p: p.name)
def test_the_fluid_domain_imports_no_provider_no_qt_and_no_library(path):
    roots = absolute_import_roots(path.read_text(encoding="utf-8"))
    assert not (roots & FORBIDDEN_IN_DOMAIN), (
        f"{path.name} imports {sorted(roots & FORBIDDEN_IN_DOMAIN)}")


@pytest.mark.parametrize("path", modules_under(FLUIDS_DOMAIN),
                         ids=lambda p: p.name)
def test_the_fluid_domain_reaches_no_further_than_core(path):
    for dotted in dotted_paths(path.read_text(encoding="utf-8")):
        if not dotted.startswith("rocketforge"):
            continue
        assert dotted.startswith("rocketforge.core"), (
            f"{path.name} imports {dotted}; physics.fluids depends on core "
            "and nothing else in the project")


def test_the_forbidden_set_would_actually_catch_a_violation():
    assert absolute_import_roots("import CoolProp") & FORBIDDEN_IN_DOMAIN


# --- providers implement, they do not compose ----------------------------

@pytest.mark.parametrize("path", modules_under(FLUID_PROVIDERS),
                         ids=lambda p: p.name)
def test_a_fluid_provider_never_imports_the_application_layer(path):
    for dotted in dotted_paths(path.read_text(encoding="utf-8")):
        assert not dotted.startswith("rocketforge.application"), (
            f"{path.name} imports {dotted}; the composition root is a leaf")


@pytest.mark.parametrize("path", modules_under(FLUID_PROVIDERS),
                         ids=lambda p: p.name)
def test_a_fluid_provider_imports_no_qt(path):
    roots = absolute_import_roots(path.read_text(encoding="utf-8"))
    assert not (roots & {"PySide6", "PySide2", "PyQt5", "PyQt6"})


def test_coolprop_is_imported_lazily_and_never_at_module_scope():
    source = (FLUID_PROVIDERS / "coolprop.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = {a.name.split(".")[0] for a in node.names}
            if isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
            assert "CoolProp" not in names, (
                "a module-scope CoolProp import would make the base "
                "environment unable to import this adapter at all")


def test_the_lazy_import_scan_would_catch_a_module_scope_import():
    tree = ast.parse("import CoolProp\ndef f():\n    pass\n")
    found = any(isinstance(n, ast.Import)
                and any(a.name == "CoolProp" for a in n.names)
                for n in tree.body)
    assert found, "the negative control must detect what the rule forbids"


# --- density_hint stays display-only -------------------------------------

NEW_MODULES = (modules_under(FLUIDS_DOMAIN) + modules_under(FLUID_PROVIDERS)
               + modules_under(PROPELLANT_METRICS) + modules_under(COUPLING))


def density_hint_reads(source: str) -> list[int]:
    """Lines where ``density_hint`` is *read as a value*, not merely named.

    Attribute access and subscripts count. A string, a comment and a docstring
    do not: the first version of this scan in Phase 5F flagged its own
    disclaimer, which is why the rule now looks at the syntax tree.
    """
    lines: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and node.attr == "density_hint":
            lines.append(node.lineno)
        elif isinstance(node, ast.Name) and node.id == "density_hint":
            lines.append(node.lineno)
    return lines


@pytest.mark.parametrize("path", NEW_MODULES, ids=lambda p: p.name)
def test_no_new_module_reads_density_hint(path):
    hits = density_hint_reads(path.read_text(encoding="utf-8"))
    assert not hits, (
        f"{path.name} reads density_hint at line(s) {hits}; validated density "
        "comes from a fluid provider at the stream state, never from the hint")


def test_the_density_hint_scan_ignores_prose_but_catches_a_read():
    prose = '"""density_hint is display-only."""\nx = 1\n'
    assert density_hint_reads(prose) == []
    comment = "# never read density_hint here\nx = 1\n"
    assert density_hint_reads(comment) == []
    real = "rho = propellant.density_hint\n"
    assert density_hint_reads(real) == [1]
    bare = "density_hint = 5\nrho = density_hint\n"
    assert density_hint_reads(bare) == [1, 2]


def test_the_hint_still_exists_on_the_definition_as_display_metadata():
    from rocketforge.providers.cea.propellants import LOX

    assert LOX.density_hint == 1141.0, (
        "the hint is not deleted -- it stays as reference metadata; the rule "
        "is that no calculation reads it")


# --- chamber pressure is not feed pressure -------------------------------

def pressure_arguments(source: str) -> list[tuple[int, str]]:
    """``pressure=<name>`` keyword arguments, with the identifier passed."""
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg not in ("pressure", "reference_pressure"):
                continue
            value = keyword.value
            if isinstance(value, ast.Name):
                found.append((value.lineno, value.id))
            elif isinstance(value, ast.Attribute):
                found.append((value.lineno, value.attr))
    return found


@pytest.mark.parametrize("path", NEW_MODULES, ids=lambda p: p.name)
def test_no_fluid_pressure_is_taken_from_a_chamber_pressure(path):
    offenders = [(line, name) for line, name
                 in pressure_arguments(path.read_text(encoding="utf-8"))
                 if "chamber_pressure" in name or name == "pressure_bar"]
    assert not offenders, (
        f"{path.name} passes a chamber pressure as a fluid property pressure "
        f"at {offenders}. Liquid feed pressure is a different state, and "
        "until feed-system physics exists it must be an explicit input.")


def test_the_chamber_pressure_scan_would_catch_the_substitution():
    bad = "evaluate(FluidStateRequest(fluid=f, temperature=t, pressure=chamber_pressure))"
    assert ("chamber_pressure" in {name for _, name in pressure_arguments(bad)})
    good = "evaluate(FluidStateRequest(fluid=f, temperature=t, pressure=feed_pressure))"
    assert "chamber_pressure" not in {name for _, name in pressure_arguments(good)}


# --- scope: the next roadmap step is not started -------------------------

#: ``line`` was in this list when the fluids foundation was accepted, and has
#: been removed because the next roadmap step -- `06` §8 step 2 -- implemented
#: it, gated on the methane transport validation the fluids foundation left
#: open. The rule is narrowed to the components that are *still* out of scope,
#: not weakened: everything else it forbade, it still forbids.
@pytest.mark.parametrize("name", ["valve", "orifice", "injector",
                                  "pump", "turbine", "cooling", "tank"])
def test_no_fluid_device_module_was_created(name):
    assert not (PACKAGE_ROOT / "engineering" / name).exists(), (
        f"engineering.{name} is a later roadmap step and is out of scope here")
    assert not (PACKAGE_ROOT / "engineering" / f"{name}.py").exists()


def test_the_line_component_exists_and_is_the_step_that_created_it():
    """The counterpart to the narrowing above: line is present, deliberately."""
    assert (PACKAGE_ROOT / "engineering" / "line").is_dir()


def test_no_device_correlation_vocabulary_appears_in_the_new_modules():
    forbidden = ("friction_factor", "darcy", "reynolds_number", "discharge_coefficient",
                 "pressure_drop", "nusselt", "bartz")
    for path in NEW_MODULES:
        source = path.read_text(encoding="utf-8")
        names = {node.name for node in ast.walk(ast.parse(source))
                 if isinstance(node, ast.FunctionDef)}
        assert not (names & set(forbidden)), (
            f"{path.name} defines {sorted(names & set(forbidden))}")


# --- the frozen compressible module is untouched -------------------------

def test_no_new_module_imports_a_private_compressible_symbol():
    for path in NEW_MODULES:
        for dotted in dotted_paths(path.read_text(encoding="utf-8")):
            if dotted.startswith("rocketforge.physics.compressible"):
                tail = dotted.split(".")[-1]
                assert not tail.startswith("_"), f"{path.name} -> {dotted}"
