"""The API v1 freeze, enforced.

Phase 4G declared the fundamental compressible surface stable. This file is
what makes that declaration mean something: it compares the live package
against the recorded contract and fails on any drift.

**A failure here is not a bug in the test.** It means the published API moved.
The correct response is either to restore the symbol, or to make a deliberate
decision -- a version bump or an erratum -- and update the contract in the same
commit, so the change is visible in review rather than discovered by a
downstream module.

What is pinned: the package namespace, each module's ``__all__``, public
function parameter names and order, the field order of frozen result records,
and enum values. What is not: docstrings, private helpers, implementation.
"""

from __future__ import annotations

import dataclasses
import enum
import inspect
import json
import pathlib

import pytest

from rocketforge.core.tolerances import DEFAULT_TOLERANCES
from rocketforge.physics import compressible as pkg

CONTRACT_PATH = pathlib.Path(__file__).with_name("compressible_api_v1.json")
CONTRACT = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
MODULE_NAMES = sorted(CONTRACT["modules"])


def module(name: str):
    return __import__(f"rocketforge.physics.compressible.{name}", fromlist=[name])


def signature_of(func) -> str:
    """Must match the generator in the contract builder, term for term."""
    raw = inspect.signature(func)
    parts = []
    for name, param in raw.parameters.items():
        if param.default is inspect.Parameter.empty:
            parts.append(name)
        elif param.default is DEFAULT_TOLERANCES:
            parts.append(f"{name}=DEFAULT_TOLERANCES")
        else:
            parts.append(f"{name}={param.default!r}")
    return "(" + ", ".join(parts) + ")"


# ---------------------------------------------------------------------------
# the namespace
# ---------------------------------------------------------------------------


def test_the_package_exports_exactly_what_the_contract_records():
    assert sorted(pkg.__all__) == CONTRACT["package_exports"]


def test_every_exported_name_actually_exists():
    missing = [name for name in pkg.__all__ if not hasattr(pkg, name)]
    assert missing == []


def test_every_module_is_reachable_from_the_package():
    """118: normal use must never require a private module path."""
    for name in ("isentropic", "mass_flow", "normal_shock", "prandtl_meyer",
                 "oblique_shock", "fanno", "rayleigh", "nozzle", "geometry"):
        assert hasattr(pkg, name), f"{name} is not reachable from the package"
        assert name in pkg.__all__, f"{name} is importable but not exported"


def test_the_public_types_are_importable_from_the_package_root():
    """A caller should never have to reach into `.types` to name a result."""
    for name in ("PerfectGas", "FlowBranch", "ShockBranch", "NozzleRegime",
                 "NormalShockResult", "PrandtlMeyerResult", "ObliqueShockResult",
                 "FannoState", "RayleighState", "NozzleSolution", "FlowState",
                 "AreaDistribution", "NozzleOperating", "CriticalPressureRatios",
                 "ShockLocation"):
        assert hasattr(pkg, name), name


# ---------------------------------------------------------------------------
# per-module surface
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_the_module_exports_exactly_what_the_contract_records(name):
    recorded = CONTRACT["modules"][name]["exports"]
    assert sorted(getattr(module(name), "__all__", [])) == recorded


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_public_signatures_are_unchanged(name):
    live = module(name)
    for symbol, recorded in CONTRACT["modules"][name]["functions"].items():
        function = getattr(live, symbol)
        assert signature_of(function) == recorded, (
            f"{name}.{symbol} changed signature: the published contract says "
            f"{recorded}, the code says {signature_of(function)}")


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_result_records_keep_their_fields_and_their_order(name):
    live = module(name)
    for symbol, recorded in CONTRACT["modules"][name]["records"].items():
        record = getattr(live, symbol)
        assert dataclasses.is_dataclass(record)
        fields = [f.name for f in dataclasses.fields(record)]
        assert fields == recorded["fields"], f"{name}.{symbol} field set changed"
        assert bool(record.__dataclass_params__.frozen) is recorded["frozen"]


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_enum_values_are_unchanged(name):
    live = module(name)
    for symbol, recorded in CONTRACT["modules"][name]["enums"].items():
        members = getattr(live, symbol)
        assert issubclass(members, enum.Enum)
        assert [m.value for m in members] == recorded, (
            f"{name}.{symbol} enum values changed, which changes stored data "
            "and any serialized result")


# ---------------------------------------------------------------------------
# the promises behind the contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_every_module_declares_what_it_publishes(name):
    """No module may leak its namespace by omitting __all__."""
    assert hasattr(module(name), "__all__"), f"{name} has no __all__"


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_no_private_name_is_exported(name):
    for symbol in getattr(module(name), "__all__", []):
        assert not symbol.startswith("_"), f"{name} exports a private name: {symbol}"


@pytest.mark.parametrize("name", MODULE_NAMES)
def test_every_public_result_record_is_immutable(name):
    """67: a physics result may not be mutated by whatever displays it."""
    live = module(name)
    for symbol in getattr(live, "__all__", []):
        obj = getattr(live, symbol)
        if dataclasses.is_dataclass(obj) and isinstance(obj, type):
            assert obj.__dataclass_params__.frozen, (
                f"{name}.{symbol} is a mutable public result record")


def test_no_ambiguous_inverse_acquired_a_default_branch():
    """148: explicit branch selection is part of what v1 promises."""
    from rocketforge.physics.compressible import fanno, isentropic, mass_flow, rayleigh
    ambiguous = [
        (isentropic.mach_from_area_ratio, "branch"),
        (mass_flow.mach_from_mass_flow_ratio, "branch"),
        (fanno.mach_from_friction_parameter, "branch"),
        (rayleigh.mach_from_stagnation_temperature_ratio, "branch"),
    ]
    for function, parameter in ambiguous:
        default = inspect.signature(function).parameters[parameter].default
        assert default is inspect.Parameter.empty, (
            f"{function.__module__}.{function.__name__} grew a default branch; "
            "an inverse with two physical roots must keep asking")


def test_no_relation_acquired_a_hidden_air_default():
    """149: gamma is never assumed. The caller states the gas."""
    for name in MODULE_NAMES:
        live = module(name)
        for symbol in getattr(live, "__all__", []):
            function = getattr(live, symbol)
            if not inspect.isfunction(function):
                continue
            parameter = inspect.signature(function).parameters.get("gas")
            if parameter is not None:
                assert parameter.default is inspect.Parameter.empty, (
                    f"{name}.{symbol} grew a default gas")


def test_the_contract_file_is_small_enough_to_review():
    """114: a contract nobody can read in a diff protects nothing."""
    assert CONTRACT_PATH.stat().st_size < 64 * 1024
    assert "docstring" not in CONTRACT_PATH.read_text(encoding="utf-8").lower()
