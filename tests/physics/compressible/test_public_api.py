"""The module as a standalone engineering library.

``docs/engineering/01_engineering_architecture.md`` sections 2 and 9 require
the physics layer to be usable from a script, a notebook or a future optimiser
with no Qt in the process and no global state anywhere. These tests exercise it
the way such a user would, and check the provenance contract that makes a
result explainable.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from rocketforge.core.provenance import EquationRecord, RelationRef
from rocketforge.physics.compressible import (
    AreaMachSolutions,
    FlowBranch,
    IsentropicRatios,
    PerfectGas,
    equations,
    isentropic as iso,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# a realistic session
# ---------------------------------------------------------------------------


def test_a_nozzle_sizing_session_reads_naturally():
    """The sequence a user would actually write, start to finish.

    Combustion products, not air: gamma 1.22 and a gas constant more than twice
    that of air, which is the case the API has to serve just as naturally.
    """
    gas = PerfectGas(gamma=1.22, gas_constant=320.0)

    # Chamber conditions are stagnation conditions.
    chamber_temperature = 3300.0  # K

    # Exit Mach number from the nozzle area ratio, supersonic branch.
    solution = iso.mach_from_area_ratio(12.4, gas, FlowBranch.SUPERSONIC)
    assert solution.ok
    exit_mach = solution.unwrap()
    assert 3.0 < exit_mach < 4.0

    # The full state at that Mach number.
    ratios = iso.ratios_from_mach(exit_mach, gas)
    assert 0.0 < ratios.pressure_ratio < 0.01
    assert ratios.area_ratio == pytest.approx(12.4, rel=1e-8)

    # Dimensional follow-through.
    exit_temperature = chamber_temperature * ratios.temperature_ratio
    assert 900.0 < exit_temperature < 1600.0, "a plausible exhaust temperature, K"
    exit_speed_of_sound = gas.speed_of_sound(exit_temperature)
    exit_velocity = exit_mach * exit_speed_of_sound
    assert 2000.0 < exit_velocity < 3000.0, "a plausible exhaust velocity, m/s"


def test_the_same_call_works_for_air():
    """Gas-agnostic: nothing about the API assumes a propulsion context."""
    air = PerfectGas.air()
    solution = iso.mach_from_area_ratio(2.0, air, FlowBranch.SUBSONIC)
    assert solution.unwrap() == pytest.approx(0.30590383, rel=1e-6)


def test_public_names_are_exported():
    """What a user is expected to import is importable from the package root."""
    from rocketforge.physics import compressible

    for name in ("PerfectGas", "speed_of_sound", "FlowBranch",
                 "IsentropicRatios", "AreaMachSolutions", "isentropic"):
        assert hasattr(compressible, name), name


def test_types_are_the_documented_ones():
    gas = PerfectGas(gamma=1.4)
    assert isinstance(iso.ratios_from_mach(2.0, gas), IsentropicRatios)
    assert isinstance(iso.mach_from_area_ratio_both(2.0, gas).unwrap(), AreaMachSolutions)
    assert isinstance(FlowBranch.SUBSONIC, FlowBranch)


# ---------------------------------------------------------------------------
# no Qt, no globals
# ---------------------------------------------------------------------------


def test_usable_in_a_process_with_qt_blocked():
    """The acceptance criterion, checked by running it rather than asserting it."""
    script = textwrap.dedent(
        """
        import sys

        BLOCKED = {'PySide6', 'PySide2', 'PyQt5', 'PyQt6', 'shiboken6'}

        class Blocker:
            def find_spec(self, fullname, path=None, target=None):
                if fullname.split('.')[0] in BLOCKED:
                    raise ImportError(fullname + ' is blocked for this test')
                return None

        sys.meta_path.insert(0, Blocker())

        from rocketforge.physics.compressible import PerfectGas, FlowBranch
        from rocketforge.physics.compressible import isentropic as iso

        gas = PerfectGas(gamma=1.4, gas_constant=287.0528)
        assert abs(float(iso.pressure_ratio(2.0, gas)) - 0.1278045255) < 1e-9
        assert abs(iso.mach_from_area_ratio(1.6875, gas, FlowBranch.SUPERSONIC).unwrap() - 2.0) < 1e-8
        assert abs(gas.speed_of_sound(288.15) - 340.294) < 5e-3
        assert not [m for m in sys.modules if m.split('.')[0] in BLOCKED]
        print('OK')
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=PROJECT_ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"
    assert "OK" in result.stdout


def test_no_module_level_mutable_state():
    """Repeated identical calls must not drift, in any order."""
    gas = PerfectGas(gamma=1.4)
    first = float(iso.pressure_ratio(2.0, gas))
    iso.mach_from_area_ratio(9.0, gas, FlowBranch.SUPERSONIC)
    iso.ratios_from_mach(0.3, PerfectGas(gamma=1.2))
    assert float(iso.pressure_ratio(2.0, gas)) == first


def test_results_do_not_share_mutable_structure():
    """Two solutions must not be able to affect one another."""
    gas = PerfectGas(gamma=1.4)
    a = iso.mach_from_area_ratio(2.0, gas, FlowBranch.SUBSONIC)
    b = iso.mach_from_area_ratio(2.0, gas, FlowBranch.SUBSONIC)
    assert a is not b
    assert a.diagnostics is not b.diagnostics or a.diagnostics == ()


# ---------------------------------------------------------------------------
# provenance
# ---------------------------------------------------------------------------


def test_every_registered_equation_is_complete():
    """Structural contract, not exact prose."""
    assert equations.EQUATIONS
    for identifier, record in equations.EQUATIONS.items():
        assert isinstance(record, EquationRecord)
        assert record.identifier == identifier
        assert record.name and record.group
        assert record.latex and record.html
        assert record.description
        assert record.variables
        assert record.assumptions
        assert record.domain
        assert record.source


def test_equation_identifiers_are_versioned_and_unique():
    identifiers = list(equations.EQUATIONS)
    assert len(identifiers) == len(set(identifiers))
    for identifier in identifiers:
        assert identifier.endswith(".v1"), f"{identifier} carries no model version"


def test_related_identifiers_resolve():
    for record in equations.EQUATIONS.values():
        for related in record.related:
            assert related in equations.EQUATIONS, f"{record.identifier} points at missing {related}"


def test_relation_reference_carries_the_model_identifier():
    reference = equations.REL_AREA_RATIO
    assert isinstance(reference, RelationRef)
    assert reference.identifier == "isentropic.area_ratio.v1"
    assert reference.model == "perfect_gas_isentropic_v1"
    assert "NACA" in reference.source or "Anderson" in reference.source
    assert any("perfect gas" in a.lower() for a in reference.assumptions)


def test_variables_name_both_the_symbol_and_the_code_name():
    """The mapping a reader needs to check code against a printed equation."""
    record = equations.record("isentropic.area_ratio.v1")
    code_names = {variable.code_name for variable in record.variables}
    assert {"mach", "gamma"} <= code_names
    for variable in record.variables:
        assert variable.symbol and variable.name and variable.code_name


def test_unknown_identifier_is_reported():
    with pytest.raises(KeyError):
        equations.record("isentropic.not_a_relation.v1")


def test_html_form_uses_the_markup_the_interface_renders():
    """The Equation Library page renders entity-based HTML, not LaTeX."""
    record = equations.record("isentropic.pressure_ratio.v1")
    assert "<i>" in record.html and "<sub>" in record.html
    assert "\\frac" in record.latex
