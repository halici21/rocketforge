"""DB-4C: the 1985 TDK printout of the SSME current design, as a case. No provider is needed.

What is pinned here is the source's own printed data and what the case is allowed to conclude: differences only,
never a verdict. No computed value appears in this file.
"""

from __future__ import annotations

import inspect

import pytest

from rocketforge.comparison import COMPARED, ObservedQuantity, SourceKind, compare, to_canonical
from rocketforge.comparison import ssme_tdk_1985 as module
from rocketforge.comparison.cases import VERDICT_KINDS, CaseOrigin
from rocketforge.core.constants import STANDARD_GRAVITY
from rocketforge.physics.thermochemistry import ExpansionMode

CASE = module.SSME_TDK_1985_CURRENT_DESIGN


def test_the_two_new_units_are_exact():
    assert to_canonical(1.0, "R") == (5.0 / 9.0, "K", "temperature")
    assert to_canonical(9.0, "R")[0] == 5.0
    assert to_canonical(1.0, "lbf*s/lbm") == (9.80665, "m/s", "velocity")
    assert STANDARD_GRAVITY == 9.80665
    # the same pound-force the psia factor is built from
    assert to_canonical(1.0, "psia")[0] == pytest.approx(0.45359237 * 9.80665 / 0.0254 ** 2, rel=1e-15)


def test_the_case_is_an_imported_independent_code_and_draws_no_verdict():
    assert CASE.source_kind is SourceKind.INDEPENDENT_CODE
    assert CASE.source_kind not in VERDICT_KINDS
    assert CASE.origin is CaseOrigin.IMPORTED
    assert not CASE.allows_verdict
    assert CASE.tolerance_rel is None
    assert CASE.benchmark_class == "B"
    assert CASE.code_version.startswith("not stated") and CASE.database_version.startswith("not stated")


def test_the_values_are_transcribed_as_printed():
    printed = {q.key: (q.value, q.unit, q.decimals) for q in CASE.quantities}
    assert printed == {
        "chamber_temperature": (6543.192, "R", 3),
        "vacuum_specific_impulse:equilibrium": (465.1311, "lbf*s/lbm", 4),
        "vacuum_specific_impulse:frozen": (446.7661, "lbf*s/lbm", 4),
    }
    assert (module.CHAMBER_PRESSURE_PSIA, module.OXIDISER_FUEL_RATIO, module.AREA_RATIO) == (3285.0, 6.05485, 77.5)
    assert "19860012108" in CASE.source and "SRC-NTRS-19860012108" in CASE.source


def test_the_expansion_model_is_part_of_the_key():
    assert module.KEY_VACUUM_ISP_EQUILIBRIUM == f"vacuum_specific_impulse:{ExpansionMode.EQUILIBRIUM.value}"
    assert module.KEY_VACUUM_ISP_FROZEN == f"vacuum_specific_impulse:{ExpansionMode.FROZEN.value}"
    assert module.KEY_VACUUM_ISP_EQUILIBRIUM != module.KEY_VACUUM_ISP_FROZEN


def test_only_the_three_ideal_quantities_are_recorded():
    keys = {q.key for q in CASE.quantities}
    assert keys == {module.KEY_CHAMBER_TEMPERATURE, module.KEY_VACUUM_ISP_EQUILIBRIUM, module.KEY_VACUUM_ISP_FROZEN}
    for kept_out in ("ISP (ODK)", "ISP (TDK)", "ISP (TC)", "second-solution", "Figure 7"):
        assert kept_out in CASE.notes, kept_out


def _observed(scale: float = 1.0) -> dict[str, ObservedQuantity]:
    return {q.key: ObservedQuantity(q.key, q.value * scale, q.unit) for q in CASE.quantities}


@pytest.mark.parametrize("scale", [1.0, 1.0 + 1e-9, 1.01, 0.5])
def test_every_row_is_compared_whatever_the_numbers(scale):
    """Made-up numbers, including an exact match: an independent code is never agreed or disagreed with."""
    result = compare(CASE, _observed(scale))
    assert result.verdict == COMPARED
    assert [r.verdict for r in result.rows] == [COMPARED] * 3
    assert all(r.bound is None for r in result.rows)


def test_a_shifting_value_cannot_stand_for_a_frozen_one():
    observed = {module.KEY_VACUUM_ISP_EQUILIBRIUM: ObservedQuantity(module.KEY_VACUUM_ISP_EQUILIBRIUM, 4500.0, "m/s")}
    result = compare(CASE, observed)
    assert [r.key for r in result.rows] == [module.KEY_VACUUM_ISP_EQUILIBRIUM]
    assert set(result.not_observed) == {module.KEY_CHAMBER_TEMPERATURE, module.KEY_VACUUM_ISP_FROZEN}


def test_rows_are_in_si_with_the_printed_values_converted_exactly():
    rows = {r.key: r for r in compare(CASE, _observed()).rows}
    assert rows["chamber_temperature"].unit == "K"
    assert rows["chamber_temperature"].reference == pytest.approx(6543.192 * 5.0 / 9.0, rel=1e-15)
    assert rows[module.KEY_VACUUM_ISP_FROZEN].unit == "m/s"
    assert rows[module.KEY_VACUUM_ISP_FROZEN].reference == pytest.approx(446.7661 * 9.80665, rel=1e-15)


def test_the_case_module_reaches_no_solver():
    source = inspect.getsource(module)
    for layer in ("rocketforge.providers", "rocketforge.engineering", "rocketforge.application", "rocketforge.evidence"):
        assert layer not in source, layer
