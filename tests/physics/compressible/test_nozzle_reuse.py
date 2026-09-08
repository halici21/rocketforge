"""Phase 4F is an integration, so this file audits the integration itself.

The nozzle module's whole claim is that it *composes* verified modules rather
than restating them. That claim is worth nothing unless a future developer
cannot quietly replace a call with a copied formula, so it is checked three
ways: the source is read for the formulas that must not appear, the call graph
is read for the modules that must be reached, and the results are compared
against the modules they are supposed to have come from.
"""

from __future__ import annotations

import ast
import inspect
import pathlib

import numpy as np
import pytest

from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import mass_flow as mf
from rocketforge.physics.compressible import normal_shock as shock
from rocketforge.physics.compressible import nozzle
from rocketforge.physics.compressible.geometry import AreaDistribution
from rocketforge.physics.compressible.types import FlowBranch, NozzleOperating

SOURCE = pathlib.Path(inspect.getfile(nozzle)).read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
P0, T0 = 1.0e6, 3000.0


def gas(gamma: float = 1.4) -> PerfectGas:
    return PerfectGas(gamma=gamma, gas_constant=287.05)


def geometry(area_ratio: float = 2.0, n: int = 101) -> AreaDistribution:
    return AreaDistribution.conical(throat_area=0.01, area_ratio=area_ratio, n=n)


def code_only() -> str:
    """The module's executable text, with every docstring removed.

    Necessary because the module *documents* what it deliberately does not do:
    the word "thrust" appears in its docstring precisely to say thrust is out
    of scope, and a naive text scan would read that sentence as a violation.
    """
    tree = ast.parse(SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return ast.unparse(ast.fix_missing_locations(tree))


CODE = code_only()


def called_names() -> set[str]:
    """Every attribute call in the module, as ``module.function``."""
    names = set()
    for node in ast.walk(TREE):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            target = node.func
            if isinstance(target.value, ast.Name):
                names.add(f"{target.value.id}.{target.attr}")
    return names


# ---------------------------------------------------------------------------
# the modules that must be reached
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("call", [
    "isentropic.mach_from_area_ratio",
    "isentropic.pressure_ratio",
    "isentropic.temperature_ratio",
    "isentropic.area_ratio",
    "isentropic.mach_from_pressure_ratio",
    "normal_shock.solve",
    "normal_shock.pressure_ratio",
    "mass_flow.choked_mass_flow",
    "mass_flow.mass_flow",
    "brent",
])
def test_the_nozzle_calls_the_module_that_owns_the_relation(call):
    calls = called_names()
    if call == "brent":
        assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                   and node.func.id == "brent" for node in ast.walk(TREE))
    else:
        assert call in calls, f"nozzle must reach {call} rather than restate it"


def test_the_shock_is_the_normal_shock_module_at_runtime(monkeypatch):
    """A runtime spy, because a static call can be bypassed by an alias."""
    seen = []
    original = shock.solve

    def spy(mach1, gas_model):
        seen.append(mach1)
        return original(mach1, gas_model)

    monkeypatch.setattr(nozzle.normal_shock, "solve", spy)
    critical = nozzle.critical_pressure_ratios(2.0, gas()).unwrap()
    middle = 0.5 * (critical.first_critical + critical.second_critical)
    located = nozzle.shock_area_ratio(2.0, middle, gas()).unwrap()
    assert seen, "the internal-shock solve never called normal_shock.solve"
    assert located.mach_upstream in seen


def test_the_area_relation_is_the_isentropic_module_at_runtime(monkeypatch):
    seen = []
    original = iso.mach_from_area_ratio

    def spy(ratio, gas_model, branch, *args, **kwargs):
        seen.append((float(ratio), branch))
        return original(ratio, gas_model, branch, *args, **kwargs)

    monkeypatch.setattr(nozzle.isentropic, "mach_from_area_ratio", spy)
    # The criticals are cached, so a warm cache would answer without calling
    # anything. Cleared here so the test observes the real computation.
    nozzle._criticals.cache_clear()
    nozzle.critical_pressure_ratios(2.0, gas())
    branches = {branch for _, branch in seen}
    assert branches == {FlowBranch.SUBSONIC, FlowBranch.SUPERSONIC}


def test_the_threshold_cache_cannot_return_another_nozzles_answer():
    """A cache is only safe because the function is pure. Checked, not assumed."""
    air = gas(1.4)
    other = gas(1.2)
    first_2 = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    first_4 = nozzle.critical_pressure_ratios(4.0, air).unwrap()
    first_2_again = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    other_gas = nozzle.critical_pressure_ratios(2.0, other).unwrap()

    assert first_2 == first_2_again
    assert first_4.first_critical != first_2.first_critical
    assert other_gas.first_critical != first_2.first_critical

    nozzle._criticals.cache_clear()
    assert nozzle.critical_pressure_ratios(2.0, air).unwrap() == first_2


def test_the_mass_flow_is_the_mass_flow_module_at_runtime(monkeypatch):
    seen = []
    original = mf.choked_mass_flow

    def spy(*args, **kwargs):
        seen.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(nozzle.mass_flow, "choked_mass_flow", spy)
    nozzle.solve(geometry(), NozzleOperating(P0, 0.2 * P0, T0), gas())
    assert seen, "a choked nozzle must take its mass flow from the mass_flow module"


def test_every_area_mach_inversion_names_its_branch():
    """``70``: the branch is mandatory by design, and nothing defeats that."""
    for node in ast.walk(TREE):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "mach_from_area_ratio"):
            assert len(node.args) >= 3, (
                "mach_from_area_ratio must be called with an explicit branch")


# ---------------------------------------------------------------------------
# the formulas that must not appear
# ---------------------------------------------------------------------------


def test_the_nozzle_contains_no_gas_dynamic_exponent():
    """The signature of a copied relation is an exponent built from gamma."""
    forbidden = ("gamma + 1", "gamma - 1", "gamma+1", "gamma-1",
                 "gas.gamma +", "gas.gamma -")
    for token in forbidden:
        assert token not in CODE, f"a gamma expression appeared in nozzle.py: {token}"
    assert "**" not in CODE, "an exponent in nozzle.py means a relation was restated"


def test_the_nozzle_contains_no_square_root():
    """Speeds of sound and shock relations both come from other modules."""
    assert "sqrt" not in CODE


def test_the_nozzle_uses_no_root_finder_of_its_own():
    """``164``: exactly one root finder in the codebase, and this is not it."""
    for banned in ("newton", "secant", "bisect", "scipy", "fsolve", "minimize"):
        assert banned not in CODE.lower(), banned
    assert CODE.count("brent(") == 1, "one shock root solve, and only one"


def test_the_nozzle_does_not_use_fanno_or_rayleigh():
    """``163``: this model is inviscid and adiabatic, so neither belongs."""
    assert "fanno" not in CODE.lower()
    assert "rayleigh" not in CODE.lower()


def test_the_nozzle_computes_no_performance_quantity():
    """``208``: thrust and its relatives belong to engineering/nozzle.

    Scanned over code only. The docstring names every one of them, which is
    the point -- the module states what it is not, and that sentence must not
    read as a violation.
    """
    lowered = CODE.lower()
    for banned in ("thrust", "c_f", "cstar", "c_star", "isp", "specific_impulse"):
        assert banned not in lowered, f"{banned} is out of scope for Phase 4F"
    assert "thrust" in SOURCE.lower(), "the docstring should still say it is absent"


def test_the_nozzle_imports_nothing_from_outside_the_permitted_set():
    imported = set()
    for node in ast.walk(TREE):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[-1])
        elif isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
    assert "scipy" not in imported
    assert "pandas" not in imported
    assert "PySide6" not in imported


# ---------------------------------------------------------------------------
# results compared against the modules they came from
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("gamma", [1.2, 1.3, 1.4, 1.66])
def test_the_shock_at_exit_state_is_the_normal_shock_module(gamma):
    """``90``: machine-level identity, not merely close agreement."""
    air = gas(gamma)
    critical = nozzle.critical_pressure_ratios(2.0, air).unwrap()
    result = nozzle.classify(2.0, critical.second_critical, air).unwrap()
    independent = shock.solve(critical.mach_exit_supersonic, air)
    assert result.shock.mach_upstream == critical.mach_exit_supersonic
    assert result.shock.mach_downstream == independent.mach2
    assert result.shock.pressure_ratio == independent.pressure_ratio
    assert result.shock.stagnation_pressure_ratio == independent.stagnation_pressure_ratio


def test_every_distributed_pressure_is_the_isentropic_relation():
    air = gas()
    solution = nozzle.solve(geometry(), NozzleOperating(P0, 0.7 * P0, T0), air).unwrap()
    expected = (np.asarray(iso.pressure_ratio(solution.mach, air))
                * solution.stagnation_pressure)
    assert np.allclose(solution.pressure, expected, rtol=1e-12)


def test_every_distributed_temperature_is_the_isentropic_relation():
    air = gas()
    solution = nozzle.solve(geometry(), NozzleOperating(P0, 0.7 * P0, T0), air).unwrap()
    expected = np.asarray(iso.temperature_ratio(solution.mach, air)) * T0
    assert np.allclose(solution.temperature, expected, rtol=1e-12)


def test_the_speed_of_sound_is_the_gas_model():
    air = gas()
    solution = nozzle.solve(geometry(), NozzleOperating(P0, 0.2 * P0, T0), air).unwrap()
    assert np.allclose(solution.speed_of_sound,
                       np.asarray(air.speed_of_sound(solution.temperature)), rtol=0.0)


def test_the_density_is_the_ideal_gas_relation():
    air = gas()
    solution = nozzle.solve(geometry(), NozzleOperating(P0, 0.2 * P0, T0), air).unwrap()
    expected = solution.pressure / (air.gas_constant * solution.temperature)
    assert np.allclose(solution.density, expected, rtol=1e-15)
