"""Architecture rules for the CEA provider.

**Additive only.** The 41 original rules and the 18 Phase 5B rules are not
touched and not weakened. What is added is what those cannot express: that CEA
is confined to this package, that the domain still knows nothing about it, and
that no CEA type reaches a public result.

These run in **both** environments. Most are static AST checks that need no
provider at all.
"""

from __future__ import annotations

import ast
import pathlib
import subprocess
import sys

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
PACKAGE = PROJECT_ROOT / "rocketforge"
CEA_PACKAGE = PACKAGE / "providers" / "cea"
THERMO = PACKAGE / "physics" / "thermochemistry"
COMPRESSIBLE = PACKAGE / "physics" / "compressible"

#: Roots that may only be imported inside the provider package.
PROVIDER_ONLY = {"cea"}
#: Roots that must not appear in production at all.
BANNED = {"cantera", "rocketcea", "CoolProp", "coolprop", "scipy", "pandas"}


def modules_under(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(root.rglob("*.py"))


def imported_roots(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            roots.add(node.module.split(".")[0])
    return roots


def test_the_checker_finds_the_packages():
    """Guards against a rule that silently inspects nothing."""
    assert len(modules_under(CEA_PACKAGE)) >= 8
    assert len(modules_under(THERMO)) >= 10


def test_cea_is_imported_only_inside_the_provider_package():
    offenders: list[str] = []
    for path in modules_under(PACKAGE):
        if CEA_PACKAGE in path.parents or path.parent == CEA_PACKAGE:
            continue
        for root in imported_roots(path):
            if root in PROVIDER_ONLY:
                offenders.append(f"{path.relative_to(PROJECT_ROOT)} imports {root}")
    assert not offenders, offenders


def test_the_thermochemistry_domain_still_has_no_cea_imports():
    """The domain must remain provider-independent."""
    for path in modules_under(THERMO):
        roots = imported_roots(path)
        assert "cea" not in roots, f"{path.name} imports cea"
        assert not roots & BANNED, f"{path.name} imports {roots & BANNED}"


def test_the_domain_does_not_import_the_provider_package():
    """The arrow points from the adapter to the abstraction, never back."""
    for path in modules_under(THERMO):
        source = path.read_text(encoding="utf-8")
        assert "rocketforge.providers" not in source, path.name


def test_the_provider_imports_no_banned_library():
    """Cantera is an oracle, not a production dependency."""
    for path in modules_under(CEA_PACKAGE):
        roots = imported_roots(path)
        assert not roots & BANNED, f"{path.name} imports {roots & BANNED}"


def test_the_provider_has_no_qt():
    qt = {"PySide6", "PySide2", "PyQt5", "PyQt6", "shiboken6", "shiboken2"}
    for path in modules_under(CEA_PACKAGE):
        assert not imported_roots(path) & qt, path.name


def test_the_provider_does_not_import_upward():
    """Providers may import core and physics; nothing above."""
    forbidden = ("rocketforge.application", "rocketforge.engineering",
                 "rocketforge.engine")
    for path in modules_under(CEA_PACKAGE):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = [node.module]
            for target in targets:
                assert not target.startswith(forbidden), \
                    f"{path.name}:{node.lineno} imports {target}"


def test_compressible_is_untouched_by_the_provider():
    for path in modules_under(COMPRESSIBLE):
        source = path.read_text(encoding="utf-8")
        assert "providers" not in source or "provider will return" in source
        assert "import cea" not in source


def test_no_rocket_performance_is_implemented_in_the_provider():
    """CEA returns c*, Cf and Isp; RocketForge does not compute them.

    The oracle module *reads* them, which is why the check is on definitions:
    a function that computes a thrust coefficient would fail, a dataclass field
    that records CEA's is exactly what the oracle is for.
    """
    forbidden = {"characteristic_velocity", "compute_c_star", "compute_cf",
                 "compute_isp", "thrust", "nozzle_expansion", "area_mach"}
    offenders: list[str] = []
    for path in modules_under(CEA_PACKAGE):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                if node.name.lower() in forbidden:
                    offenders.append(f"{path.name}:{node.lineno} {node.name}")
    assert not offenders, offenders


def test_no_equilibrium_solver_is_implemented_in_the_provider():
    """The adapter adapts. The solving belongs to CEA."""
    forbidden = {"minimise_gibbs", "minimize_gibbs", "solve_equilibrium",
                 "gibbs_minimisation", "newton_equilibrium"}
    for path in modules_under(CEA_PACKAGE):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                assert node.name.lower() not in forbidden, f"{path.name} {node.name}"


def test_no_text_parsing_of_cea_output():
    """Phase 5B-0 proved the structured API suffices.

    A regex over formatted output, or an input-deck temp file, would be a major
    integration regression and is checked for rather than assumed absent.
    """
    for path in modules_under(CEA_PACKAGE):
        source = path.read_text(encoding="utf-8")
        assert "re.compile" not in source, f"{path.name} compiles a regex"
        assert "subprocess" not in source, f"{path.name} shells out"
        assert ".inp" not in source, f"{path.name} references an input deck"


def test_the_chamber_state_never_carries_performance():
    """Checked on the real dataclass, not on a docstring."""
    import dataclasses

    from rocketforge.physics.thermochemistry import ChamberGas

    names = {f.name for f in dataclasses.fields(ChamberGas)}
    assert not names & {"c_star", "cstar", "cf", "coefficient_of_thrust",
                        "isp", "Isp", "specific_impulse", "thrust"}


def test_no_public_domain_field_is_typed_as_a_cea_object():
    """A static scan for provider types leaking into the domain.

    Checked on **annotations and base classes**, not on raw text: the domain's
    prose legitimately mentions ``cea.__version__`` when explaining what a
    provenance field is for, and a grep would flag that. What must not exist is
    a field or a base actually typed as a provider object.
    """
    # Matched as whole identifiers, not substrings: RocketForge's own
    # ``MixtureRatio`` contains "Mixture", and a substring check would flag the
    # domain's own vocabulary as a provider leak.
    provider_names = {"EqSolution", "RocketSolution", "EqSolver",
                      "RocketSolver", "CEASolution", "Mixture", "Reactant"}

    def leaked(expression: ast.AST) -> str | None:
        for node in ast.walk(expression):
            if isinstance(node, ast.Name) and node.id in provider_names:
                return node.id
            if isinstance(node, ast.Attribute):
                value = node.value
                if isinstance(value, ast.Name) and value.id == "cea":
                    return f"cea.{node.attr}"
                if node.attr in provider_names:
                    return node.attr
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                # A string annotation, e.g. "EqSolution".
                if node.value.strip() in provider_names:
                    return node.value.strip()
        return None

    offenders: list[str] = []
    for path in modules_under(THERMO):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            expressions = []
            if isinstance(node, ast.AnnAssign) and node.annotation is not None:
                expressions.append(node.annotation)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.returns is not None:
                    expressions.append(node.returns)
                expressions.extend(a.annotation for a in node.args.args
                                   if a.annotation is not None)
            elif isinstance(node, ast.ClassDef):
                expressions.extend(node.bases)
            for expression in expressions:
                found = leaked(expression)
                if found:
                    offenders.append(
                        f"{path.name}:{node.lineno} -> {found}")
    assert not offenders, offenders


def test_the_provider_package_imports_without_cea_installed():
    """In a subprocess with the library blocked, to prove it is not luck."""
    script = """
import sys
import importlib.abc

# A real blocker. find_module was removed from the import protocol in Python
# 3.12, so a hook defining only that method is silently inert -- the test would
# pass without blocking anything.
class _Block(importlib.abc.MetaPathFinder):
    def __init__(self, blocked):
        self._blocked = set(blocked)

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in self._blocked:
            raise ImportError(f"{fullname} is blocked for this test")
        return None

sys.meta_path.insert(0, _Block({"cea"}))
for _name in [m for m in sys.modules if m.split(".")[0] == "cea"]:
    del sys.modules[_name]

import rocketforge.providers.cea as pkg
status = pkg.check_availability()
assert not status.is_usable, "a blocked library should not report usable"
provider = pkg.CEAThermochemistryProvider()
assert provider.provider_id == "cea"
assert not provider.is_available
print("BLOCKED_OK")
"""
    result = subprocess.run([sys.executable, "-c", script],
                            capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, result.stderr
    assert "BLOCKED_OK" in result.stdout


def test_the_provider_works_with_qt_blocked():
    """A real solve in a process where PySide6 cannot load.

    Skipped when CEA is absent; when present this is the proof that the
    scientific backend is genuinely headless.
    """
    from rocketforge.providers.cea import check_availability

    if not check_availability().is_usable:
        pytest.skip("NASA CEA provider unavailable")

    script = """
import sys
import importlib.abc

# A real blocker. find_module was removed from the import protocol in Python
# 3.12, so a hook defining only that method is silently inert -- the test would
# pass without blocking anything.
class _Block(importlib.abc.MetaPathFinder):
    def __init__(self, blocked):
        self._blocked = set(blocked)

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in self._blocked:
            raise ImportError(f"{fullname} is blocked for this test")
        return None

sys.meta_path.insert(0, _Block({"PySide6", "shiboken6"}))

from rocketforge.providers.cea import CEAThermochemistryProvider, LOX, LIQUID_METHANE
from rocketforge.physics.thermochemistry import (
    ChamberEquilibriumRequest, MixtureRatio, Phase, PropellantStream)

provider = CEAThermochemistryProvider()
solution = provider.solve_chamber(ChamberEquilibriumRequest(
    fuel=PropellantStream(LIQUID_METHANE, 111.643, phase=Phase.LIQUID),
    oxidiser=PropellantStream(LOX, 90.17, phase=Phase.LIQUID),
    oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6))
assert solution.ok, solution.status
assert 3000.0 < solution.unwrap().temperature < 4000.0
assert "PySide6" not in sys.modules, "Qt was imported"
print("HEADLESS_CEA_OK")
"""
    result = subprocess.run([sys.executable, "-c", script],
                            capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, result.stderr
    assert "HEADLESS_CEA_OK" in result.stdout


def test_base_requirements_do_not_contain_the_provider():
    """The library stays optional at the base level."""
    base = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
    lowered = "\n".join(line for line in base.splitlines()
                        if line.strip() and not line.strip().startswith("#"))
    assert "cea" not in lowered.lower().replace("essentials", "")
    profile = (PROJECT_ROOT / "requirements-thermochemistry.txt").read_text(
        encoding="utf-8")
    assert "cea==" in profile
    assert "cantera" not in profile.lower()


def test_normal_application_startup_does_not_import_the_provider():
    """The self-test entry point must not cost a normal launch anything.

    ``main.py`` imports ``rocketforge.application.selftest`` unconditionally so
    it can dispatch on the flag, but that module imports the provider *inside*
    the function. A normal launch therefore never loads CEA, never reads
    thermo.lib, and pays nothing for a feature it is not using.

    Checked statically on the module's own imports rather than by launching the
    application, so it holds regardless of what else a test session has loaded.
    """
    selftest = PACKAGE / "application" / "selftest.py"
    tree = ast.parse(selftest.read_text(encoding="utf-8"), filename=str(selftest))
    module_level: set[str] = set()
    for node in tree.body:                       # top level only
        if isinstance(node, ast.Import):
            module_level.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            module_level.add(node.module.split(".")[0])
    assert "cea" not in module_level
    assert "rocketforge" not in module_level, (
        "the self-test module must not import RocketForge packages at module "
        "level; a normal launch would then pay for the provider")


def test_the_selftest_flag_is_not_a_user_facing_surface():
    """A diagnostic, not a feature. No QML, no menu, no window."""
    selftest = (PACKAGE / "application" / "selftest.py").read_text(encoding="utf-8")
    assert "QObject" not in selftest
    assert "Signal" not in selftest
    assert "qmlRegister" not in selftest
    for qml in (PROJECT_ROOT / "ui").rglob("*.qml"):
        assert "selftest" not in qml.read_text(encoding="utf-8").lower(), qml.name
