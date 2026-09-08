"""The duplication audit, executable.

Specified in ``05`` section 14. Two claims are being enforced, and both are
architectural rather than numerical:

* **Oblique shock reuses Normal Shock.** Every property ratio an oblique shock
  reports must equal the normal-shock relation at ``M1 sin(beta)`` to *machine*
  precision. Machine precision and not 1e-10 is the whole point: a carefully
  re-derived duplicate formula would agree to about 1e-12 and fail here, which
  is exactly the outcome wanted.
* **Prandtl-Meyer expansion reuses Isentropic.** Likewise for the static
  ratios across a fan.

Plus a static source check, which catches a duplicate before it can be
numerically indistinguishable.
"""

from __future__ import annotations

import ast
import math
import pathlib

import numpy as np
import pytest

from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import normal_shock as ns
from rocketforge.physics.compressible import oblique_shock as obl
from rocketforge.physics.compressible import prandtl_meyer as pm

GAMMAS = (1.2, 1.3, 1.4, 1.66)
GASES = [PerfectGas(gamma=g) for g in GAMMAS]
GAS_IDS = [f"gamma={g}" for g in GAMMAS]
AIR = PerfectGas(gamma=1.4)

PHYSICS = pathlib.Path(obl.__file__).parent


# ---------------------------------------------------------------------------
# oblique shock is a normal shock seen edge-on
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", [1.5, 2.0, 3.0, 5.0])
def test_every_oblique_ratio_is_the_normal_shock_at_the_normal_component(gas, mach1):
    """The blocking reuse test, at rtol = 1e-15 across the whole wave-angle range."""
    mu = float(iso.mach_angle(mach1))
    for beta in np.linspace(mu + 1e-4, 0.5 * math.pi, 60):
        oblique = obl.solve_from_beta(mach1, float(beta), gas).unwrap()
        normal = ns.solve(mach1 * math.sin(float(beta)), gas)

        assert oblique.mach_normal1 == pytest.approx(normal.mach1, rel=1e-15)
        assert oblique.mach_normal2 == pytest.approx(normal.mach2, rel=1e-15)
        assert oblique.pressure_ratio == pytest.approx(normal.pressure_ratio, rel=1e-15)
        assert oblique.density_ratio == pytest.approx(normal.density_ratio, rel=1e-15)
        assert oblique.temperature_ratio == pytest.approx(normal.temperature_ratio, rel=1e-15)
        assert oblique.stagnation_pressure_ratio == pytest.approx(
            normal.stagnation_pressure_ratio, rel=1e-15)
        assert oblique.stagnation_temperature_ratio == normal.stagnation_temperature_ratio
        assert oblique.entropy_change == pytest.approx(normal.entropy_change, rel=1e-15)


def test_the_oblique_solver_actually_calls_the_normal_shock_solver(monkeypatch):
    """A runtime spy, so the reuse is a fact about execution and not a comment.

    Coupled to one name -- ``normal_shock.solve`` -- and nothing finer, so a
    refactor inside either module does not make this brittle.
    """
    from rocketforge.physics.compressible import oblique_shock as module

    calls = []
    original = ns.solve

    def spy(mach1, gas):
        calls.append(mach1)
        return original(mach1, gas)

    monkeypatch.setattr(module.ns, "solve", spy)
    result = obl.solve_from_beta(3.0, 0.9, AIR).unwrap()
    assert calls, "the oblique solver must reach normal_shock.solve"
    assert calls[0] == pytest.approx(3.0 * math.sin(0.9), rel=1e-15)
    assert result.mach_normal1 == pytest.approx(calls[0], rel=1e-15)


def test_the_full_solve_reuses_it_too(monkeypatch):
    from rocketforge.physics.compressible import oblique_shock as module

    calls = []
    original = ns.solve
    monkeypatch.setattr(module.ns, "solve",
                        lambda m, g: (calls.append(m), original(m, g))[1])
    obl.solve(3.0, math.radians(15.0), AIR).unwrap()
    assert calls


def test_the_oblique_module_writes_no_jump_relation():
    """A static read of the source: no gas-dynamic exponent may appear.

    A re-derived pressure or stagnation ratio needs ``gamma/(gamma-1)`` or
    ``(gamma+1)/(2(gamma-1))`` somewhere. Crude, and effective: those exponents
    have no other reason to exist in a module that only handles angles.
    """
    source = (PHYSICS / "oblique_shock.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            text = ast.get_source_segment(source, node) or ""
            if "gamma" in text.replace(" ", "") and "/" in text:
                offenders.append(text)
    assert not offenders, f"a gas-dynamic exponent appeared in oblique_shock.py: {offenders}"


def test_the_oblique_module_names_no_thermodynamic_property_of_its_own():
    """It may *report* ratios; it may not compute them.

    Every ratio in the result is assigned from a ``shock.<field>``, so the
    right-hand side of each of those assignments is checked to be exactly that.
    """
    source = (PHYSICS / "oblique_shock.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    builder = next(node for node in ast.walk(tree)
                   if isinstance(node, ast.FunctionDef) and node.name == "_result_from")
    assigned = {}
    for node in ast.walk(builder):
        if isinstance(node, ast.keyword) and node.arg in (
                "pressure_ratio", "density_ratio", "temperature_ratio",
                "stagnation_pressure_ratio", "stagnation_temperature_ratio",
                "entropy_change", "mach_normal2"):
            assigned[node.arg] = ast.get_source_segment(source, node.value)
    assert assigned, "the result builder was not found"
    for name, expression in assigned.items():
        assert expression.startswith("shock."), (
            f"{name} is computed rather than taken from the normal-shock result: {expression}")


# ---------------------------------------------------------------------------
# the expansion is isentropic, and says so by reuse
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gas", GASES, ids=GAS_IDS)
@pytest.mark.parametrize("mach1", [1.0, 1.5, 2.0, 4.0])
def test_every_expansion_ratio_is_an_isentropic_quotient(gas, mach1):
    for turn_deg in (0.5, 5.0, 15.0, 30.0):
        solution = pm.expand(mach1, math.radians(turn_deg), gas)
        if not solution.ok:
            continue
        result = solution.unwrap()
        m1, m2 = result.mach1, result.mach2
        assert result.pressure_ratio == pytest.approx(
            float(iso.pressure_ratio(m2, gas)) / float(iso.pressure_ratio(m1, gas)), rel=1e-15)
        assert result.temperature_ratio == pytest.approx(
            float(iso.temperature_ratio(m2, gas)) / float(iso.temperature_ratio(m1, gas)),
            rel=1e-15)
        assert result.density_ratio == pytest.approx(
            float(iso.density_ratio(m2, gas)) / float(iso.density_ratio(m1, gas)), rel=1e-15)


def test_the_expansion_actually_calls_the_isentropic_relations(monkeypatch):
    from rocketforge.physics.compressible import prandtl_meyer as module

    calls = []
    original = iso.pressure_ratio
    monkeypatch.setattr(module.iso, "pressure_ratio",
                        lambda m, g: (calls.append(m), original(m, g))[1])
    pm.expand(2.0, math.radians(10.0), AIR).unwrap()
    assert len(calls) >= 2, "both stations must be evaluated by the isentropic module"


def test_the_prandtl_meyer_module_writes_no_isentropic_ratio():
    source = (PHYSICS / "prandtl_meyer.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            text = ast.get_source_segment(source, node) or ""
            if "gamma" in text.replace(" ", "") and "/" in text:
                offenders.append(text)
    assert not offenders, f"a gas-dynamic exponent appeared in prandtl_meyer.py: {offenders}"


def test_the_mach_angle_is_imported_rather_than_redefined():
    """One definition of asin(1/M) in the package, imported by the rest."""
    for name in ("prandtl_meyer.py", "oblique_shock.py"):
        source = (PHYSICS / name).read_text(encoding="utf-8")
        assert "from .isentropic import mach_angle" in source
        tree = ast.parse(source)
        defined = {node.name for node in ast.walk(tree)
                   if isinstance(node, ast.FunctionDef)}
        assert "mach_angle" not in defined, f"{name} redefines the Mach angle"


# ---------------------------------------------------------------------------
# neither module reaches for Qt or SciPy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["prandtl_meyer.py", "oblique_shock.py"])
def test_no_forbidden_import(name):
    source = (PHYSICS / name).read_text(encoding="utf-8")
    for forbidden in ("scipy", "PySide6", "pandas", "matplotlib"):
        assert forbidden not in source, f"{name} mentions {forbidden}"
