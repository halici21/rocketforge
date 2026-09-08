"""Architecture rules for the thermochemistry package.

**Additive only.** The 41 rules in ``tests/test_architecture.py`` are not
touched and not weakened. Those already enforce the layer matrix, the Qt ban
below ``application``, the SciPy ban, and -- importantly for this phase -- that
``cea``, ``cantera``, ``rocketcea``, ``CoolProp`` and ``pyCEA`` may be imported
only inside ``providers``. Nothing here duplicates them.

What is added is what the global rules cannot express:

* ``compressible`` and ``thermochemistry`` are both in the ``physics`` layer,
  so the layer matrix permits an import between them. It must not happen.
* the new package must contain no equilibrium solver and no performance
  physics, which is a *content* rule rather than an import rule.
"""

from __future__ import annotations

import ast
import pathlib
import subprocess
import sys

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
PACKAGE = PROJECT_ROOT / "rocketforge" / "physics" / "thermochemistry"
COMPRESSIBLE = PROJECT_ROOT / "rocketforge" / "physics" / "compressible"


def modules() -> list[pathlib.Path]:
    return sorted(PACKAGE.rglob("*.py"))


def imports_of(path: pathlib.Path) -> list[str]:
    """Every dotted target imported by one module, relatives resolved."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package = "rocketforge.physics.thermochemistry"
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                found.append(package if node.module is None
                             else f"{package}.{node.module}")
            elif node.module:
                found.append(node.module)
    return found


def test_the_package_has_modules():
    """Guards against a checker that silently finds nothing."""
    assert len(modules()) >= 10


# ---------------------------------------------------------------------------
# import direction
# ---------------------------------------------------------------------------


def test_thermochemistry_imports_only_core_and_itself():
    offenders: list[str] = []
    for path in modules():
        for target in imports_of(path):
            if not target.startswith("rocketforge"):
                continue
            allowed = (target.startswith("rocketforge.core")
                       or target.startswith("rocketforge.physics.thermochemistry"))
            if not allowed:
                offenders.append(f"{path.name} imports {target}")
    assert not offenders, offenders


def test_thermochemistry_does_not_import_compressible():
    """The handshake between them is a data contract, not a call.

    That direction is what lets the frozen compressible module stay frozen
    while this layer evolves (08 section 5).
    """
    for path in modules():
        for target in imports_of(path):
            assert not target.startswith("rocketforge.physics.compressible"), (
                f"{path.name} imports {target}")


def test_compressible_does_not_import_thermochemistry():
    """The rule the global layer matrix cannot express.

    Both packages sit in the ``physics`` layer, so the matrix permits this
    edge. The frozen subsystem must keep working with thermochemistry absent.
    """
    for path in sorted(COMPRESSIBLE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = [node.module]
            for target in targets:
                assert "thermochemistry" not in target, (
                    f"{path.name}:{node.lineno} imports {target}; the frozen "
                    "compressible subsystem must not depend on thermochemistry")
    # A prose mention is fine and one exists: gas.py's docstring refers to the
    # form a thermochemistry provider will return. The rule is about imports.


def test_no_provider_or_banned_library_imports():
    """Belt and braces over the global rule, scoped to this package."""
    banned = {"cea", "cantera", "rocketcea", "CoolProp", "pyCEA", "coolprop",
              "scipy", "pandas", "sympy", "mpmath", "PySide6", "PyQt5",
              "PyQt6", "shiboken6"}
    for path in modules():
        for target in imports_of(path):
            root = target.split(".")[0]
            assert root not in banned, f"{path.name} imports {target}"


def test_package_does_not_import_numpy():
    """Not banned, but not needed either.

    Composition algebra over a handful of species is lighter as plain Python
    than as ndarray machinery, and keeping the dependency out makes the
    package's cost obvious (Phase 5B spec section 162).
    """
    for path in modules():
        assert "numpy" not in imports_of(path), f"{path.name} imports numpy"


def test_no_test_fixture_is_imported_by_production():
    for path in modules():
        source = path.read_text(encoding="utf-8")
        assert "conftest" not in source
        assert "\nimport pytest" not in source and "\nfrom pytest" not in source


# ---------------------------------------------------------------------------
# content: what this package is not allowed to implement
# ---------------------------------------------------------------------------


def test_no_equilibrium_solver_is_implemented():
    """ADR-19: the physics layer owns the contract, a provider owns the solution.

    Checked on *definitions*, so that a docstring explaining why there is no
    solver does not trip the rule.
    """
    forbidden = {"minimise_gibbs", "minimize_gibbs", "solve_equilibrium",
                 "equilibrate", "gibbs_minimisation", "gibbs_minimization",
                 "newton_equilibrium"}
    offenders: list[str] = []
    for path in modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.lower() in forbidden:
                    offenders.append(f"{path.name}:{node.lineno} defines {node.name}")
    assert not offenders, offenders


def test_no_rocket_performance_is_implemented():
    """No c*, Cf, Isp or thrust *definitions*. ADR-15 assigns them elsewhere.

    NASA CEA returns all three natively, and Phase 5B-0 recommended consuming
    them as oracle values -- which is not a reason to define them here.
    """
    forbidden = {"c_star", "cstar", "characteristic_velocity",
                 "thrust_coefficient", "coefficient_of_thrust", "cf",
                 "specific_impulse", "isp", "thrust", "exhaust_velocity"}
    offenders: list[str] = []
    for path in modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.lower() in forbidden:
                    offenders.append(f"{path.name}:{node.lineno} defines {node.name}")
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id.lower() in forbidden:
                    offenders.append(
                        f"{path.name}:{node.lineno} declares field {node.target.id}")
    assert not offenders, offenders


def test_no_chamber_geometry_fields():
    forbidden = {"l_star", "lstar", "chamber_volume", "chamber_length",
                 "throat_area", "contraction_ratio", "residence_time",
                 "injector_area", "orifice_diameter"}
    offenders: list[str] = []
    for path in modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id.lower() in forbidden:
                    offenders.append(
                        f"{path.name}:{node.lineno} declares {node.target.id}")
    assert not offenders, offenders


def test_no_public_field_is_named_after_one_vendor():
    """Provider identity belongs in provenance, not in field names.

    ``provider_id``, ``provider_names`` and ``provider_version`` are generic and
    allowed; a ``cea_name`` field would not be.
    """
    vendors = ("cea", "cantera", "rocketcea", "coolprop", "nasa")
    offenders: list[str] = []
    for path in modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                name = node.target.id.lower()
                if any(v in name for v in vendors):
                    offenders.append(f"{path.name}:{node.lineno} field {node.target.id}")
    assert not offenders, offenders


# ---------------------------------------------------------------------------
# public surface
# ---------------------------------------------------------------------------


def test_external_consumer_import_works():
    """Exactly how an outside module would use it.

    Phase 4G found a package-namespace defect that five phases of green tests
    missed, because nothing inside the project imported the way an outside
    consumer would. This is that import.
    """
    from rocketforge.physics.thermochemistry import (  # noqa: F401
        ChamberEquilibriumRequest, ChamberGas, Composition, CompositionBasis,
        ElementalComposition, GasStation, MixtureRatio, Phase,
        PropellantDefinition, PropellantStream, ProviderCapabilities,
        Species, ThermochemistryProvider, to_jsonable, validate_chamber_gas,
    )


def test_submodules_are_importable_directly():
    import importlib
    for name in ("types", "errors", "tolerances", "species", "composition",
                 "propellants", "provenance", "requests", "states",
                 "protocols", "validation", "serialization"):
        importlib.import_module(f"rocketforge.physics.thermochemistry.{name}")


def test_all_is_complete_and_honest():
    import rocketforge.physics.thermochemistry as tc

    assert tc.__all__, "the package must declare its exports"
    missing = [name for name in tc.__all__ if not hasattr(tc, name)]
    assert not missing, f"__all__ names that do not exist: {missing}"

    # Nothing private and nothing accidental. Submodules are legitimately
    # visible after import, and `annotations` is the __future__ import every
    # module in this project carries.
    import types as pytypes
    leaked = sorted(
        name for name in vars(tc)
        if not name.startswith("_")
        and name not in tc.__all__
        and name != "annotations"
        and not isinstance(vars(tc)[name], pytypes.ModuleType))
    assert not leaked, f"public but undeclared: {leaked}"


def test_no_helper_or_validator_private_names_are_exported():
    import rocketforge.physics.thermochemistry as tc
    for name in tc.__all__:
        assert not name.startswith("_")
        assert name not in {"math", "dataclass", "field", "Mapping"}


def test_public_api_is_documented_as_provisional():
    """It is a Phase 5B surface, not a frozen v1, and says so."""
    import rocketforge.physics.thermochemistry as tc
    assert "PROVISIONAL" in tc.__doc__


# ---------------------------------------------------------------------------
# headless operation
# ---------------------------------------------------------------------------


def test_package_works_with_qt_blocked():
    """Import and exercise the package in a process where PySide6 cannot load.

    Run in a subprocess so the block cannot leak into the rest of the suite.
    """
    script = """
import sys
import importlib.abc


class _Blocker(importlib.abc.MetaPathFinder):
    '''A real blocker.

    ``find_module`` was removed from the import protocol in Python 3.12, so a
    hook defining only that method is silently inert and the test would pass
    without blocking anything.
    '''

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"PySide6", "shiboken6"}:
            raise ImportError(f"{fullname} is blocked for this test")
        return None


sys.meta_path.insert(0, _Blocker())

from rocketforge.physics.thermochemistry import (
    Composition, CompositionBasis, ElementalComposition, Phase, Species,
    PropellantDefinition, PropellantRole, PropellantStream, MixtureRatio,
    ChamberEquilibriumRequest, ChamberGas, validate_chamber_gas, to_jsonable,
)

ch4 = Species("CH4", Phase.GAS, 16.04246e-3,
              ElementalComposition.from_mapping({"C": 1.0, "H": 4.0}))
o2 = Species("O2", Phase.GAS, 31.9988e-3,
             ElementalComposition.from_mapping({"O": 2.0}))
table = {"CH4": ch4, "O2": o2}

comp = Composition.from_fractions({"CH4": 0.5, "O2": 0.5},
                                  CompositionBasis.MOLE_FRACTION)
assert comp.mean_molar_mass(table) > 0.0
assert comp.specific_gas_constant(table) > 0.0
assert comp.elemental(table).elements["C"] == 0.5

fuel = PropellantDefinition("CH4", PropellantRole.FUEL,
                            Composition.pure("CH4"), 111.643, Phase.LIQUID)
ox = PropellantDefinition("LOX", PropellantRole.OXIDISER,
                          Composition.pure("O2"), 90.17, Phase.LIQUID)
req = ChamberEquilibriumRequest(
    fuel=PropellantStream(fuel, 111.643),
    oxidiser=PropellantStream(ox, 90.17),
    oxidiser_fuel_ratio=MixtureRatio(3.4), chamber_pressure=10.0e6)
M_BAR = 0.024
R_SPEC = 8.31446261815324 / M_BAR
state = ChamberGas(temperature=3500.0, gamma=1.14, gas_constant=R_SPEC,
                   molar_mass=M_BAR, composition=comp, request=req)
assert validate_chamber_gas(state).valid
assert to_jsonable(state)["temperature"] == 3500.0

assert "PySide6" not in sys.modules, "Qt was imported"
print("HEADLESS_OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
        cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, result.stderr
    assert "HEADLESS_OK" in result.stdout


def test_compressible_still_works_without_thermochemistry():
    """The frozen subsystem must not have acquired a dependency."""
    script = """
import sys
from rocketforge.physics.compressible import PerfectGas, isentropic
gas = PerfectGas(gamma=1.4, gas_constant=287.05)
assert abs(float(isentropic.area_ratio(2.0, gas)) - 1.6875) < 1e-4
assert not any(m.startswith("rocketforge.physics.thermochemistry")
               for m in sys.modules), "compressible pulled in thermochemistry"
print("COMPRESSIBLE_INDEPENDENT_OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
        cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, result.stderr
    assert "COMPRESSIBLE_INDEPENDENT_OK" in result.stdout
