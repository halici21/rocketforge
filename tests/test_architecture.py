"""Enforcement of the backend layer boundaries.

``docs/engineering/01_engineering_architecture.md`` section 4 requires the
dependency direction to be enforced by a test rather than by convention,
because the coupling this architecture exists to prevent does not appear on day
one -- it appears months later, when some module "just needs" a helper from a
layer above it.

The checker parses each module's AST rather than importing it, so a violation
is caught even in a module that cannot currently execute, and no import side
effect is triggered by running the suite.

Its own parsing logic is exercised against synthetic sources further down, so
that a checker which silently stopped finding anything could not pass as a
placebo. Violations are demonstrated with source strings held in this file --
never by adding a deliberately broken module to the shipped package.

Known limitation: static analysis sees ``import`` statements. A dynamic import
through ``importlib`` or ``__import__`` would not be detected. Nothing in
RocketForge uses those, and adding a runtime import graph would cost far more
than it catches at this stage.
"""

from __future__ import annotations

import ast
import pathlib
import subprocess
import sys
import textwrap
from dataclasses import dataclass

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE_NAME = "rocketforge"
PACKAGE_ROOT = PROJECT_ROOT / PACKAGE_NAME

#: The layers, lowest first.
LAYERS = ("core", "physics", "engineering", "engine", "providers", "comparison",
          "application")

#: Which layers each layer may import from, transcribed from the table in
#: ``01_engineering_architecture.md`` section 2. A layer may always import
#: itself.
#:
#: ``providers`` is the one entry that is not a simple vertical rule: providers
#: implement protocols *declared in* ``physics``, so the dependency arrow points
#: from the concrete adapter down to the abstraction, and nothing below
#: ``application`` may import ``providers`` in return.
ALLOWED_IMPORTS: dict[str, frozenset[str]] = {
    "core": frozenset({"core"}),
    "physics": frozenset({"core", "physics"}),
    "engineering": frozenset({"core", "physics", "engineering"}),
    "engine": frozenset({"core", "physics", "engineering", "engine"}),
    "providers": frozenset({"core", "physics", "providers"}),
    # Compares results it is handed; it may not reach a solver or a provider,
    # so a comparison can never quietly produce the number it is checking.
    "comparison": frozenset({"core", "physics", "comparison"}),
    "application": frozenset(LAYERS),
}

#: Qt is permitted only in ``application``, which is where the QObject
#: controllers exposed to QML will live. Everything below it must remain
#: importable and runnable in a process with no Qt at all.
QT_ROOTS = frozenset({"PySide6", "PySide2", "PyQt5", "PyQt6", "shiboken6", "shiboken2"})
QT_ALLOWED_LAYERS = frozenset({"application"})

#: External engineering libraries enter through ``providers`` and nowhere else
#: (``01`` section 2, hard rules).
EXTERNAL_LIBRARY_ROOTS = frozenset({"CoolProp", "rocketcea", "cantera", "cea", "pyCEA"})
EXTERNAL_LIBRARY_ALLOWED_LAYERS = frozenset({"providers"})

#: SciPy is deliberately not a runtime dependency (ADR-09): the bracketed
#: solvers are RocketForge's own, and SciPy appears only as a test oracle. This
#: rule is what stops it drifting into production as a convenience.
BANNED_RUNTIME_ROOTS = frozenset({"scipy"})


@dataclass(frozen=True)
class ImportRecord:
    """One import statement found in one module."""

    module: str          # the dotted name of the module doing the importing
    target: str          # the dotted name being imported, relatives resolved
    lineno: int
    type_checking: bool  # inside an `if TYPE_CHECKING:` block

    @property
    def root(self) -> str:
        return self.target.split(".")[0]


# ---------------------------------------------------------------------------
# discovery and parsing
# ---------------------------------------------------------------------------


def python_files() -> list[pathlib.Path]:
    """Every module in the backend package."""
    return sorted(PACKAGE_ROOT.rglob("*.py"))


def module_name(path: pathlib.Path) -> str:
    """Dotted module name for a file inside the package."""
    relative = path.relative_to(PROJECT_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def layer_of(dotted: str) -> str | None:
    """The layer a dotted module belongs to, or None if it is not in one.

    ``rocketforge`` itself and anything outside the package return None.
    """
    parts = dotted.split(".")
    if len(parts) < 2 or parts[0] != PACKAGE_NAME:
        return None
    return parts[1] if parts[1] in ALLOWED_IMPORTS else None


def resolve_relative(module: str, level: int, tail: str | None) -> str:
    """Resolve a relative import to an absolute dotted name.

    ``level`` 1 means "the package containing this module", 2 means its parent,
    and so on -- the same rule the interpreter applies. Getting this wrong is
    the easy way to write an architecture checker that misses every relative
    import, which is how the physics layer would smuggle in a dependency.

    Returns "" when the level walks past the top-level package, which the
    interpreter would reject anyway; returning the bare tail there would make
    an unresolvable relative import look like an external one.
    """
    package_parts = module.split(".")[:-1]  # the containing package
    if level > len(package_parts):
        return ""
    if level > 1:
        package_parts = package_parts[: len(package_parts) - (level - 1)]
    return ".".join(package_parts + ([tail] if tail else []))


def imports_in(source: str, module: str) -> list[ImportRecord]:
    """Every import in ``source``, with relative imports resolved.

    Imports guarded by ``if TYPE_CHECKING:`` are reported like any other and
    are subject to the same rules. They are not executed, but they express the
    same conceptual coupling: a physics module that needs an engineering type
    to describe its own signature has an engineering dependency whether or not
    the interpreter ever follows it.
    """
    tree = ast.parse(source, filename=module)
    records: list[ImportRecord] = []

    def is_type_checking_test(node: ast.expr) -> bool:
        if isinstance(node, ast.Name) and node.id == "TYPE_CHECKING":
            return True
        return isinstance(node, ast.Attribute) and node.attr == "TYPE_CHECKING"

    def visit(node: ast.AST, type_checking: bool) -> None:
        for child in ast.iter_child_nodes(node):
            child_tc = type_checking
            if isinstance(node, ast.If) and node.test is not child:
                # already inside the If; body/orelse inherit the flag
                pass
            if isinstance(child, ast.Import):
                for alias in child.names:
                    records.append(ImportRecord(module, alias.name, child.lineno, type_checking))
            elif isinstance(child, ast.ImportFrom):
                base = (
                    resolve_relative(module, child.level, child.module)
                    if child.level
                    else (child.module or "")
                )
                if base and (base == PACKAGE_NAME or child.module is None):
                    # `from rocketforge import physics` and `from .. import
                    # physics` both name the layer in the alias, not in the
                    # module part. Resolving the alias is what makes those
                    # forms enforceable rather than invisible.
                    for alias in child.names:
                        records.append(
                            ImportRecord(
                                module, f"{base}.{alias.name}", child.lineno, type_checking
                            )
                        )
                elif base:
                    records.append(ImportRecord(module, base, child.lineno, type_checking))
            elif isinstance(child, ast.If) and is_type_checking_test(child.test):
                visit(child, True)
                continue
            visit(child, child_tc)

    visit(tree, False)
    return records


def all_imports() -> list[ImportRecord]:
    """Every internal and external import across the backend package."""
    records: list[ImportRecord] = []
    for path in python_files():
        records.extend(imports_in(path.read_text(encoding="utf-8"), module_name(path)))
    return records


def describe(record: ImportRecord, rule: str) -> str:
    """A failure message that says what to change and why it is a rule."""
    guard = " (inside `if TYPE_CHECKING:`)" if record.type_checking else ""
    return (
        f"\n  module    : {record.module}"
        f"\n  line      : {record.lineno}{guard}"
        f"\n  imports   : {record.target}"
        f"\n  rule      : {rule}"
        f"\n  reference : docs/engineering/01_engineering_architecture.md section 2"
    )


# ---------------------------------------------------------------------------
# the checker is looking at something real
# ---------------------------------------------------------------------------


def test_package_exists():
    assert PACKAGE_ROOT.is_dir(), f"backend package not found at {PACKAGE_ROOT}"


def test_every_layer_is_present():
    for layer in LAYERS:
        assert (PACKAGE_ROOT / layer / "__init__.py").is_file(), (
            f"layer package {layer} is missing; the architecture rules would "
            "silently stop covering it"
        )


def test_checker_discovers_the_real_modules():
    """Guard against a checker that quietly finds nothing and passes."""
    modules = {module_name(p) for p in python_files()}
    assert "rocketforge.core.numerics.roots" in modules
    assert "rocketforge.core.errors" in modules
    assert len(modules) >= 8, f"only found {len(modules)} modules: {sorted(modules)}"


def test_checker_finds_real_import_edges():
    """The real package must contain at least one internal edge to check."""
    internal = [r for r in all_imports() if r.root == PACKAGE_NAME]
    assert internal, "no internal imports found at all -- the checker is not working"
    targets = {r.target for r in internal}
    assert "rocketforge.core.errors" in targets, (
        "expected roots.py to import the error hierarchy; if that changed, this "
        f"test needs updating. Found: {sorted(targets)}"
    )


# ---------------------------------------------------------------------------
# the rules
# ---------------------------------------------------------------------------


def test_no_forbidden_layer_imports():
    violations = []
    for record in all_imports():
        if record.root != PACKAGE_NAME:
            continue
        source_layer = layer_of(record.module)
        target_layer = layer_of(record.target)
        if source_layer is None or target_layer is None:
            continue
        if target_layer not in ALLOWED_IMPORTS[source_layer]:
            violations.append(
                describe(
                    record,
                    f"layer '{source_layer}' may import "
                    f"{sorted(ALLOWED_IMPORTS[source_layer])}, but not '{target_layer}'",
                )
            )
    assert not violations, "forbidden layer dependencies:" + "".join(violations)


def test_no_qt_below_application():
    violations = []
    for record in all_imports():
        if record.root not in QT_ROOTS:
            continue
        layer = layer_of(record.module)
        if layer not in QT_ALLOWED_LAYERS:
            violations.append(
                describe(
                    record,
                    "Qt may only be imported in 'application'; the backend must "
                    "stay importable and runnable with no Qt in the process",
                )
            )
    assert not violations, "Qt imported below the application layer:" + "".join(violations)


def test_external_property_libraries_only_in_providers():
    violations = []
    for record in all_imports():
        if record.root not in EXTERNAL_LIBRARY_ROOTS:
            continue
        layer = layer_of(record.module)
        if layer not in EXTERNAL_LIBRARY_ALLOWED_LAYERS:
            violations.append(
                describe(
                    record,
                    "external property libraries enter through 'providers' and "
                    "nowhere else, so physics stays importable without them",
                )
            )
    assert not violations, "external library leakage:" + "".join(violations)


def test_scipy_is_not_a_runtime_dependency():
    violations = [
        describe(
            record,
            "SciPy is a test oracle only (ADR-09); the bracketed solvers are "
            "RocketForge's own and must not fall back to it",
        )
        for record in all_imports()
        if record.root in BANNED_RUNTIME_ROOTS
    ]
    assert not violations, "banned runtime dependency:" + "".join(violations)


def defined_names(source: str) -> list[tuple[str, int]]:
    """Names bound by assignment, annotation, argument or definition."""
    tree = ast.parse(source)
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for sub in ast.walk(target):
                    if isinstance(sub, ast.Name):
                        found.append((sub.id, node.lineno))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            found.append((node.target.id, node.lineno))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append((node.name, node.lineno))
            args = node.args
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
                found.append((arg.arg, arg.lineno))
        elif isinstance(node, ast.ClassDef):
            found.append((node.name, node.lineno))
    return found


def test_no_degree_named_values_below_application():
    """Angles are radians below the application layer (``01`` section 8).

    A ``_deg`` suffix is how a degree-valued quantity is marked, and it may
    only exist where conversion happens. Making the naming rule executable is
    what stops a degree value drifting into a trigonometric relation.
    """
    violations = []
    for path in python_files():
        module = module_name(path)
        layer = layer_of(module)
        if layer is None or layer == "application":
            continue
        for name, lineno in defined_names(path.read_text(encoding="utf-8")):
            if name.endswith("_deg"):
                violations.append(
                    f"\n  module: {module}\n  line  : {lineno}\n  name  : {name}"
                    "\n  rule  : angles are radians below 'application'; a _deg name"
                    " may only exist in application code or a view model"
                )
    assert not violations, "degree-named values below the application layer:" + "".join(violations)


# ---------------------------------------------------------------------------
# the checker itself
# ---------------------------------------------------------------------------


def test_parses_absolute_imports():
    records = imports_in("import rocketforge.physics.compressible\n", "rocketforge.core.x")
    assert [r.target for r in records] == ["rocketforge.physics.compressible"]


def test_parses_from_imports():
    records = imports_in("from rocketforge.engine import solver\n", "rocketforge.core.x")
    assert [r.target for r in records] == ["rocketforge.engine"]


def test_parses_package_level_from_import():
    """`from rocketforge import physics` names the layer in the alias."""
    records = imports_in("from rocketforge import physics, core\n", "rocketforge.core.x")
    assert sorted(r.target for r in records) == ["rocketforge.core", "rocketforge.physics"]


@pytest.mark.parametrize(
    "module,statement,expected",
    [
        ("rocketforge.core.numerics.roots", "from ..errors import BracketError", "rocketforge.core.errors"),
        ("rocketforge.core.numerics.roots", "from . import models", "rocketforge.core.numerics.models"),
        ("rocketforge.physics.compressible.gas", "from ...core.numerics.roots import brent", "rocketforge.core.numerics.roots"),
        ("rocketforge.physics.compressible.gas", "from ..fluids import interfaces", "rocketforge.physics.fluids"),
        ("rocketforge.engineering.nozzle.thrust", "from ...engine import solver", "rocketforge.engine"),
        ("rocketforge.core.x", "from .. import physics", "rocketforge.physics"),
    ],
)
def test_resolves_relative_imports(module, statement, expected):
    """Relative imports must resolve, or every rule below is unenforced."""
    records = imports_in(statement + "\n", module)
    assert [r.target for r in records] == [expected]


def test_type_checking_imports_are_reported():
    source = textwrap.dedent(
        """
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from rocketforge.engineering import injector
        """
    )
    records = imports_in(source, "rocketforge.physics.x")
    guarded = [r for r in records if r.target == "rocketforge.engineering"]
    assert guarded, "a TYPE_CHECKING import was missed entirely"
    assert guarded[0].type_checking is True


def test_type_checking_import_still_violates_the_layer_rule():
    """Decision: guarded imports count. They express the same coupling."""
    source = textwrap.dedent(
        """
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from rocketforge.engineering import injector
        """
    )
    record = next(
        r for r in imports_in(source, "rocketforge.physics.x") if r.root == PACKAGE_NAME
    )
    source_layer = layer_of(record.module)
    target_layer = layer_of(record.target)
    assert target_layer not in ALLOWED_IMPORTS[source_layer]


@pytest.mark.parametrize(
    "module,statement",
    [
        ("rocketforge.core.thing", "from rocketforge.physics import gas"),
        ("rocketforge.core.thing", "import rocketforge.application.controllers"),
        ("rocketforge.physics.gas", "from rocketforge.engineering import nozzle"),
        ("rocketforge.physics.gas", "from ..providers.coolprop import provider"),
        ("rocketforge.engineering.pump", "from rocketforge.engine import solver"),
        ("rocketforge.engineering.pump", "from ..application import controllers"),
        ("rocketforge.engine.cycle", "from rocketforge.application import formatting"),
        ("rocketforge.physics.gas", "from ..engine.balances import mass"),
        # the comparison layer must not reach a solver, nor be reached from below
        ("rocketforge.comparison.compare", "from rocketforge.providers.cea_solid import cstar"),
        ("rocketforge.comparison.compare", "from ..application import controllers"),
        ("rocketforge.physics.gas", "from rocketforge.comparison import compare"),
    ],
)
def test_checker_detects_synthetic_layer_violations(module, statement):
    """The rules must actually reject the edges they claim to reject.

    Synthetic sources, never files added to the shipped package.
    """
    record = next(r for r in imports_in(statement + "\n", module) if r.root == PACKAGE_NAME)
    source_layer = layer_of(record.module)
    target_layer = layer_of(record.target)
    assert source_layer is not None and target_layer is not None
    assert target_layer not in ALLOWED_IMPORTS[source_layer], (
        f"{module} importing {record.target} should be forbidden but was allowed"
    )


@pytest.mark.parametrize(
    "module,statement",
    [
        ("rocketforge.physics.gas", "from ..core.errors import DomainError"),
        ("rocketforge.engineering.pump", "from rocketforge.physics import fluids"),
        ("rocketforge.engine.cycle", "from rocketforge.engineering import pump"),
        ("rocketforge.providers.coolprop", "from rocketforge.physics.fluids import interfaces"),
        ("rocketforge.application.controllers", "from rocketforge.engine import solver"),
        ("rocketforge.core.numerics.roots", "from ..errors import BracketError"),
    ],
)
def test_checker_accepts_legitimate_edges(module, statement):
    """The rules must not reject the architecture they are meant to describe."""
    record = next(r for r in imports_in(statement + "\n", module) if r.root == PACKAGE_NAME)
    source_layer = layer_of(record.module)
    target_layer = layer_of(record.target)
    assert target_layer in ALLOWED_IMPORTS[source_layer], (
        f"{module} importing {record.target} is legitimate but was rejected"
    )


def test_checker_detects_synthetic_qt_violation():
    record = next(
        r for r in imports_in("from PySide6.QtCore import QObject\n", "rocketforge.physics.gas")
    )
    assert record.root in QT_ROOTS
    assert layer_of(record.module) not in QT_ALLOWED_LAYERS


def test_checker_allows_qt_in_application():
    record = next(
        r
        for r in imports_in(
            "from PySide6.QtCore import QObject\n", "rocketforge.application.controllers"
        )
    )
    assert layer_of(record.module) in QT_ALLOWED_LAYERS


def test_checker_ignores_the_standard_library_and_numpy():
    source = "import math\nimport numpy as np\nfrom dataclasses import dataclass\nfrom pathlib import Path\n"
    records = imports_in(source, "rocketforge.core.x")
    roots = {r.root for r in records}
    assert roots == {"math", "numpy", "dataclasses", "pathlib"}
    assert not any(r.root == PACKAGE_NAME for r in records)
    assert not any(r.root in QT_ROOTS or r.root in BANNED_RUNTIME_ROOTS for r in records)


def test_checker_detects_degree_named_definitions():
    source = textwrap.dedent(
        """
        theta_deg = 12.0

        def turn(angle_deg: float) -> float:
            return angle_deg
        """
    )
    names = {name for name, _ in defined_names(source)}
    assert "theta_deg" in names
    assert "angle_deg" in names


# ---------------------------------------------------------------------------
# Qt isolation, proved by running it
# ---------------------------------------------------------------------------


def test_import_rocketforge_is_cheap_and_qt_free():
    """`import rocketforge` must not drag in Qt or start anything."""
    script = textwrap.dedent(
        """
        import sys
        import rocketforge
        assert rocketforge.__version__
        loaded = [m for m in sys.modules if m.split('.')[0] in
                  {'PySide6', 'PySide2', 'PyQt5', 'PyQt6', 'shiboken6', 'scipy'}]
        assert not loaded, loaded
        # the top-level package must stay empty: no eager submodule imports
        eager = [m for m in sys.modules if m.startswith('rocketforge.')]
        assert not eager, eager
        print('OK')
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    assert "OK" in result.stdout


def test_backend_runs_with_qt_blocked():
    """Every backend module must import and work with Qt made unimportable.

    A meta path finder refuses PySide6 outright, so this fails if any backend
    module below ``application`` reaches for Qt at import time -- the check the
    architecture calls an acceptance criterion rather than a preference.
    """
    script = textwrap.dedent(
        """
        import importlib
        import pkgutil
        import sys

        BLOCKED = {'PySide6', 'PySide2', 'PyQt5', 'PyQt6', 'shiboken6', 'shiboken2'}

        class Blocker:
            def find_spec(self, fullname, path=None, target=None):
                if fullname.split('.')[0] in BLOCKED:
                    raise ImportError(f'{fullname} is blocked for this test')
                return None

        sys.meta_path.insert(0, Blocker())

        import rocketforge

        # 'application' is the one layer allowed to hold Qt adapters, so it is
        # excluded from the sweep rather than being expected to import here.
        skipped = 'rocketforge.application'
        for info in pkgutil.walk_packages(rocketforge.__path__, 'rocketforge.'):
            if info.name == skipped or info.name.startswith(skipped + '.'):
                continue
            importlib.import_module(info.name)

        from rocketforge.core.numerics.roots import brent
        root, report = brent(lambda x: x * x - 2.0, 0.0, 2.0,
                             xtol=1e-12, rtol=1e-14, max_iter=100)
        assert report.converged, report
        assert abs(root - 1.4142135623730951) < 1e-11, root
        assert not [m for m in sys.modules if m.split('.')[0] in BLOCKED]
        print('OK')
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    assert "OK" in result.stdout


def test_backend_does_not_import_the_ui():
    """Nothing in the package may reach into the QML application."""
    offenders = [
        f"{r.module}:{r.lineno} imports {r.target}"
        for r in all_imports()
        if r.root in {"ui", "main"}
    ]
    assert not offenders, "backend reaching into the application: " + "; ".join(offenders)
