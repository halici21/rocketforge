"""The duplication audit, executable.

``docs/engineering/05_verification_and_validation_plan.md`` section 14 turns
the reuse rules into assertions, so that a future module cannot quietly grow
its own copy of a relation, a root finder, or a gas validation. The rule this
phase has to establish, before there are several modules to confuse: the
inverse is defined by the forward relation, and the solver comes from core.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from rocketforge.core.numerics import roots
from rocketforge.physics.compressible import FlowBranch, PerfectGas
from rocketforge.physics.compressible import gas as gas_module
from rocketforge.physics.compressible import isentropic as iso

MODULE_DIR = pathlib.Path(iso.__file__).parent
ISENTROPIC_SOURCE = pathlib.Path(iso.__file__).read_text(encoding="utf-8")


def functions_defined_in(source: str) -> set[str]:
    return {
        node.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


# ---------------------------------------------------------------------------
# one root solver
# ---------------------------------------------------------------------------


def test_the_inverse_defines_its_residual_from_the_forward_relation():
    """The inverse must solve the published relation, not a restatement of it.

    Replacing the forward relation must change what the inverse returns; if it
    does not, the inverse is using its own copy of the formula.
    """
    gas = PerfectGas(gamma=1.4)
    honest = iso.mach_from_area_ratio(4.0, gas, FlowBranch.SUPERSONIC).unwrap()

    original = iso.area_ratio
    try:
        # A deliberately shifted relation: the root must move with it.
        iso.area_ratio = lambda mach, g: original(mach, g) * 1.10
        shifted = iso.mach_from_area_ratio(4.0, gas, FlowBranch.SUPERSONIC).unwrap()
    finally:
        iso.area_ratio = original

    assert shifted != pytest.approx(honest, rel=1e-6), (
        "the area-Mach inverse does not go through area_ratio(), so it is "
        "carrying its own copy of the relation"
    )


def test_no_local_root_finder():
    """No private bisection, secant or Newton loop inside the physics module."""
    defined = functions_defined_in(ISENTROPIC_SOURCE)
    suspicious = {
        name for name in defined
        if any(word in name.lower() for word in ("bisect", "newton", "secant", "iterate", "root"))
    }
    assert not suspicious, f"looks like a private solver: {sorted(suspicious)}"
    assert "brent" in ISENTROPIC_SOURCE, "the shared solver should be the one in use"


def test_the_shared_solver_is_the_only_one_called(monkeypatch):
    calls = []
    original = roots.brent
    monkeypatch.setattr(iso, "brent", lambda *a, **k: (calls.append(1), original(*a, **k))[1])
    iso.mach_from_area_ratio(6.0, PerfectGas(gamma=1.3), FlowBranch.SUPERSONIC)
    assert len(calls) == 1


def test_analytic_inverses_use_no_solver_at_all():
    """Three of the four inverses are closed form, so nothing should iterate."""
    gas = PerfectGas(gamma=1.4)
    for inverse in (iso.mach_from_pressure_ratio,
                    iso.mach_from_temperature_ratio,
                    iso.mach_from_density_ratio):
        assert isinstance(inverse(0.4, gas), float)


# ---------------------------------------------------------------------------
# one copy of each relation
# ---------------------------------------------------------------------------


def test_the_common_isentropic_factor_is_computed_in_one_place():
    """1 + (gamma-1)/2 M^2 appears once, as _phi, not inline in four relations."""
    tree = ast.parse(ISENTROPIC_SOURCE)
    inline = 0
    for node in ast.walk(tree):
        # A multiplication by 0.5 against (gamma - 1) is the signature of the
        # factor being written out by hand.
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            source = ast.unparse(node)
            if "0.5" in source and "gamma - 1.0" in source and "mach" in source:
                inline += 1
    assert inline <= 2, (
        f"the recurring isentropic factor appears inline {inline} times; it should "
        "be computed once in _phi and once in the starred-state helper"
    )


def test_starred_ratios_are_consistent_with_the_stagnation_ratios():
    """X/X* must equal (X/X0)/(X*/X0) exactly, not be an independent formula."""
    for gamma in (1.2, 1.3, 1.4, 1.66):
        gas = PerfectGas(gamma=gamma)
        for mach in (0.1, 0.5, 1.0, 2.0, 5.0):
            assert iso.pressure_ratio_star(mach, gas) == pytest.approx(
                float(iso.pressure_ratio(mach, gas)) / float(iso.pressure_ratio(1.0, gas)),
                rel=1e-13,
            )


def test_gas_validation_happens_only_in_the_gas_model():
    """No relation re-checks gamma; there is one place that owns the domain."""
    relation_source = ISENTROPIC_SOURCE
    assert "InvalidGammaError" not in relation_source, (
        "the isentropic module is validating gamma itself; that belongs to PerfectGas"
    )
    assert "InvalidGammaError" in pathlib.Path(gas_module.__file__).read_text(encoding="utf-8")


def test_branch_enum_is_defined_once():
    """One vocabulary for branches, so later modules cannot invent another."""
    defining = []
    for path in MODULE_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ClassDef) and node.name == "FlowBranch":
                defining.append(path.name)
    assert defining == ["types.py"], f"FlowBranch defined in {defining}"


def test_area_ratio_is_the_only_area_relation():
    """One area-Mach relation, so the nozzle module later has one thing to call."""
    defined = functions_defined_in(ISENTROPIC_SOURCE)
    area_relations = {
        name for name in defined
        if name.startswith("area") and not name.startswith("_")
    }
    assert area_relations == {"area_ratio"}, f"more than one area relation: {area_relations}"


# ---------------------------------------------------------------------------
# reusable by the modules that come next
# ---------------------------------------------------------------------------


def test_relations_take_a_gas_rather_than_a_gamma_literal():
    """No air-like constant may appear in executable code in the relations.

    Later modules must be able to pass their own gas, including one derived
    from combustion chemistry with gamma near 1.2. Docstrings may of course
    discuss gamma = 1.4, so this looks at numeric literals in the AST rather
    than at the text.
    """
    air_like = {1.4, 1.40, 287.0528, 287.05, 287.0}
    offenders = [
        node.value
        for node in ast.walk(ast.parse(ISENTROPIC_SOURCE))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
        and float(node.value) in air_like
    ]
    assert not offenders, (
        f"air-like constants in the relations: {offenders}. A gamma literal here "
        "would bake air into physics that has to serve rocket exhaust too."
    )


def test_no_module_hardcodes_a_default_gas():
    for path in MODULE_DIR.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        if path.name == "gas.py":
            continue  # PerfectGas.air() is an explicit named constructor
        assert "DEFAULT_GAS" not in source and "AIR =" not in source, (
            f"{path.name} defines an implicit default gas"
        )
