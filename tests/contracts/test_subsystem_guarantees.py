"""The promises the freeze makes about the subsystem as software, not physics.

Qt isolation, serialization, immutability, non-finite handling, the absence of
global state, and the reference-comparison engine's own self-test. Each of
these is a thing a future engineering module will assume without checking, so
each one is checked here.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import subprocess
import sys

import numpy as np
import pytest

from rocketforge.core.errors import DomainError, InputError
from rocketforge.core.result import Severity, Solution, Status
from rocketforge.physics.compressible import (
    AreaDistribution,
    FlowBranch,
    NozzleOperating,
    PerfectGas,
    ShockBranch,
    fanno,
    isentropic,
    mass_flow,
    normal_shock,
    nozzle,
    oblique_shock,
    prandtl_meyer,
    rayleigh,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
AIR = PerfectGas(gamma=1.4, gas_constant=287.05)


# ---------------------------------------------------------------------------
# 75 -- Qt isolation, over the whole subsystem
# ---------------------------------------------------------------------------


QT_ISOLATION_SCRIPT = """
import sys


class Block:
    def find_module(self, name, path=None):
        return self if name.split('.')[0] == 'PySide6' else None

    def load_module(self, name):
        raise ImportError('PySide6 is blocked in this process')


sys.meta_path.insert(0, Block())

import math
import numpy as np
from rocketforge.physics.compressible import (
    AreaDistribution, FlowBranch, NozzleOperating, PerfectGas, ShockBranch,
    fanno, isentropic, mass_flow, normal_shock, nozzle, oblique_shock,
    prandtl_meyer, rayleigh,
)

air = PerfectGas(gamma=1.4, gas_constant=287.05)
results = {}
results['gas'] = float(air.speed_of_sound(300.0))
results['isentropic'] = float(isentropic.pressure_ratio(2.0, air))
results['area_mach_sub'] = isentropic.mach_from_area_ratio(
    2.0, air, FlowBranch.SUBSONIC).unwrap()
results['area_mach_sup'] = isentropic.mach_from_area_ratio(
    2.0, air, FlowBranch.SUPERSONIC).unwrap()
results['mass_flow'] = mass_flow.choked_mass_flow(air, 0.01, 1e6, 3000.0)
results['normal_shock'] = normal_shock.solve(2.0, air).mach2
results['pm'] = prandtl_meyer.mach_from_nu(0.5, air).unwrap()
results['oblique_weak'] = oblique_shock.solve(
    3.0, math.radians(20.0), air, ShockBranch.WEAK).unwrap().beta
results['oblique_strong'] = oblique_shock.solve(
    3.0, math.radians(20.0), air, ShockBranch.STRONG).unwrap().beta
results['fanno'] = float(fanno.friction_parameter(0.5, air))
results['rayleigh'] = float(rayleigh.stagnation_temperature_ratio(0.5, air))
results['nozzle_shock'] = nozzle.shock_area_ratio(2.0, 0.7, air).unwrap().area_ratio_shock
geometry = AreaDistribution.conical(throat_area=0.01, area_ratio=2.0, n=41)
solution = nozzle.solve(geometry, NozzleOperating(1e6, 0.7e6, 3000.0), air).unwrap()
results['nozzle_solve'] = solution.mass_flow

assert 'PySide6' not in sys.modules, 'Qt leaked into the physics process'
import json
print(json.dumps(results))
"""


def test_the_whole_subsystem_runs_with_qt_blocked():
    """Every module, in one process, with PySide6 made unimportable."""
    completed = subprocess.run([sys.executable, "-c", QT_ISOLATION_SCRIPT],
                               cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert completed.returncode == 0, completed.stderr[-3000:]
    values = json.loads(completed.stdout.strip().splitlines()[-1])
    assert set(values) == {"gas", "isentropic", "area_mach_sub", "area_mach_sup",
                           "mass_flow", "normal_shock", "pm", "oblique_weak",
                           "oblique_strong", "fanno", "rayleigh", "nozzle_shock",
                           "nozzle_solve"}
    assert all(np.isfinite(v) for v in values.values())


def test_the_qt_free_results_equal_the_ordinary_ones():
    """Blocking Qt must change nothing about the numbers."""
    completed = subprocess.run([sys.executable, "-c", QT_ISOLATION_SCRIPT],
                               cwd=ROOT, capture_output=True, text=True, timeout=180)
    values = json.loads(completed.stdout.strip().splitlines()[-1])
    assert values["isentropic"] == float(isentropic.pressure_ratio(2.0, AIR))
    assert values["normal_shock"] == normal_shock.solve(2.0, AIR).mach2
    assert values["mass_flow"] == mass_flow.choked_mass_flow(AIR, 0.01, 1e6, 3000.0)


def test_physics_imports_no_qt_at_module_level():
    for module in (isentropic, mass_flow, normal_shock, prandtl_meyer,
                   oblique_shock, fanno, rayleigh, nozzle):
        source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
        assert "PySide6" not in source, module.__name__


# ---------------------------------------------------------------------------
# 66 -- serialization
# ---------------------------------------------------------------------------


def serializable(value):
    """The mapping a persistence or interchange layer would apply."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: serializable(getattr(value, f.name))
                for f in dataclasses.fields(value)}
    if isinstance(value, (Status, Severity, FlowBranch, ShockBranch)):
        return value.value
    if hasattr(value, "value") and hasattr(value, "name") and not isinstance(
            value, (int, float, str)):
        return value.value
    if isinstance(value, np.ndarray):
        return [float(x) for x in value.ravel()]
    if isinstance(value, (np.floating, np.integer)):
        return float(value)
    if isinstance(value, (list, tuple)):
        return [serializable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): serializable(v) for k, v in value.items()}
    if isinstance(value, PerfectGas):
        return {"gamma": value.gamma, "gas_constant": value.gas_constant}
    return value


@pytest.mark.parametrize("name,record", [
    ("normal_shock", normal_shock.solve(2.0, AIR)),
    ("isentropic", isentropic.ratios_from_mach(2.0, AIR)),
    ("fanno", fanno.state(0.5, AIR)),
    ("rayleigh", rayleigh.state(0.5, AIR)),
    ("prandtl_meyer", prandtl_meyer.expand(2.0, 0.15, AIR).unwrap()),
    ("oblique", oblique_shock.solve(3.0, 0.3, AIR, ShockBranch.WEAK).unwrap()),
    ("nozzle_regime", nozzle.classify(2.0, 0.7, AIR).unwrap()),
    ("criticals", nozzle.critical_pressure_ratios(2.0, AIR).unwrap()),
])
def test_public_result_records_serialize_to_json(name, record):
    text = json.dumps(serializable(record))
    assert json.loads(text)
    assert "QObject" not in text
    assert "object at 0x" not in text, f"{name} leaked a repr into its payload"


def test_a_full_nozzle_solution_serializes_including_its_arrays():
    geometry = AreaDistribution.conical(throat_area=0.01, area_ratio=2.0, n=21)
    solution = nozzle.solve(geometry, NozzleOperating(1e6, 0.7e6, 3000.0),
                            AIR).unwrap()
    payload = json.loads(json.dumps(serializable(solution)))
    assert payload["regime"] == "internal_normal_shock"
    assert len(payload["mach"]) == solution.mach.size
    assert payload["shock"]["mach_upstream"] > 1.0


@pytest.mark.parametrize("outcome", [
    ("ok", lambda: nozzle.classify(2.0, 0.7, AIR)),
    ("warning", lambda: nozzle.classify(10.0, 0.05, AIR)),
    ("no_solution", lambda: fanno.downstream_mach(0.3, 99.0, AIR)),
])
def test_each_kind_of_outcome_serializes(outcome):
    """117: a success, a warning and a physical no-solution."""
    label, call = outcome
    solution = call()
    payload = {
        "status": solution.status.value,
        "value": serializable(solution.value),
        "diagnostics": [{"code": d.code, "severity": d.severity.value,
                         "message": d.message} for d in solution.diagnostics],
    }
    text = json.dumps(payload)
    assert json.loads(text)["status"] in {"ok", "warning", "no_solution"}
    if label == "no_solution":
        assert payload["value"] is None
        assert payload["diagnostics"]


# ---------------------------------------------------------------------------
# 67, 150 -- immutability and the absence of global state
# ---------------------------------------------------------------------------


def test_a_result_record_cannot_be_edited_by_whatever_displays_it():
    record = normal_shock.solve(2.0, AIR)
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.mach2 = 0.5


def test_the_gas_itself_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        AIR.gamma = 1.2


def test_there_is_no_current_gas_or_current_gamma_anywhere():
    """150: nothing in the subsystem remembers a previous call's gas."""
    for module in (isentropic, mass_flow, normal_shock, prandtl_meyer,
                   oblique_shock, fanno, rayleigh, nozzle):
        for name in dir(module):
            if name.startswith("_") or name.isupper():
                continue
            value = getattr(module, name)
            assert not isinstance(value, (list, dict, set)), (
                f"{module.__name__}.{name} is mutable module state")


def test_the_same_call_twice_gives_the_same_answer():
    first = nozzle.classify(2.0, 0.7, AIR).unwrap()
    other_gas = nozzle.classify(2.0, 0.7, PerfectGas(gamma=1.2, gas_constant=320.0))
    second = nozzle.classify(2.0, 0.7, AIR).unwrap()
    assert first.regime is second.regime
    assert first.shock.area_ratio_shock == second.shock.area_ratio_shock
    assert other_gas.unwrap().regime is not None


# ---------------------------------------------------------------------------
# 152, 153 -- the one cache in the subsystem
# ---------------------------------------------------------------------------


def test_the_threshold_cache_is_keyed_on_everything_that_changes_the_answer():
    nozzle._criticals.cache_clear()
    baseline = nozzle.critical_pressure_ratios(2.0, AIR).unwrap()
    for area_ratio, gas_model in ((4.0, AIR), (2.0, PerfectGas(gamma=1.2,
                                                               gas_constant=320.0))):
        other = nozzle.critical_pressure_ratios(area_ratio, gas_model).unwrap()
        assert other.first_critical != baseline.first_critical
    assert nozzle.critical_pressure_ratios(2.0, AIR).unwrap() == baseline


def test_a_cold_cache_and_a_warm_cache_agree_exactly():
    """153: caching is a performance decision and changes no result."""
    nozzle._criticals.cache_clear()
    cold = nozzle.critical_pressure_ratios(3.5, AIR).unwrap()
    warm = nozzle.critical_pressure_ratios(3.5, AIR).unwrap()
    assert cold == warm
    nozzle._criticals.cache_clear()
    again = nozzle.critical_pressure_ratios(3.5, AIR).unwrap()
    assert again == cold


def test_the_cached_value_cannot_be_mutated_by_a_caller():
    nozzle._criticals.cache_clear()
    record = nozzle.critical_pressure_ratios(2.0, AIR).unwrap()
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.first_critical = 0.5


# ---------------------------------------------------------------------------
# 69 -- non-finite input
# ---------------------------------------------------------------------------


NON_FINITE = (float("nan"), float("inf"), float("-inf"))


@pytest.mark.parametrize("value", NON_FINITE)
@pytest.mark.parametrize("call", [
    lambda v: isentropic.pressure_ratio(v, AIR),
    lambda v: isentropic.area_ratio(v, AIR),
    lambda v: isentropic.mach_from_area_ratio(v, AIR, FlowBranch.SUBSONIC),
    lambda v: mass_flow.mass_flow_parameter(v, AIR),
    lambda v: normal_shock.solve(v, AIR),
    lambda v: prandtl_meyer.nu(v, AIR),
    lambda v: fanno.friction_parameter(v, AIR),
    lambda v: rayleigh.stagnation_temperature_ratio(v, AIR),
    lambda v: nozzle.critical_pressure_ratios(v, AIR),
    lambda v: nozzle.classify(2.0, v, AIR),
])
def test_a_non_finite_input_fails_deterministically(call, value):
    """No NaN propagation, no silent undefined answer."""
    try:
        result = call(value)
    except (DomainError, InputError, ValueError) as error:
        assert str(error)
        return
    # If it returned instead of raising, it must be an explicit no-solution --
    # never a NaN dressed up as an answer.
    assert isinstance(result, Solution)
    assert result.value is None
    assert result.status is not Status.OK


@pytest.mark.parametrize("value", NON_FINITE)
def test_a_non_finite_gamma_is_refused_at_construction(value):
    with pytest.raises(Exception):
        PerfectGas(gamma=value, gas_constant=287.05)


def test_an_array_with_one_bad_element_fails_as_a_whole():
    """A NaN in a plotted series is a silent hole that looks like a render bug."""
    values = np.array([0.5, float("nan"), 2.0])
    with pytest.raises((DomainError, InputError, ValueError)):
        isentropic.pressure_ratio(values, AIR)


# ---------------------------------------------------------------------------
# 68 -- scalar in, scalar out
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relation", [
    isentropic.pressure_ratio, isentropic.temperature_ratio,
    isentropic.density_ratio, isentropic.area_ratio,
    mass_flow.mass_flow_parameter, normal_shock.pressure_ratio,
    fanno.temperature_ratio, rayleigh.pressure_ratio,
])
def test_a_forward_relation_preserves_scalar_and_array_shape(relation):
    scalar = relation(2.0, AIR)
    assert isinstance(scalar, float)

    array = relation(np.array([1.5, 2.0, 3.0]), AIR)
    assert isinstance(array, np.ndarray)
    assert array.shape == (3,)
    assert array.dtype == np.float64
    assert array[1] == scalar

    grid = relation(np.array([[1.5, 2.0], [3.0, 4.0]]), AIR)
    assert grid.shape == (2, 2)
