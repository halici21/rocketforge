"""DB-4C: the 1985 TDK printouts of two SSME designs, as cases. No provider is needed.

What is pinned here is the source's own printed data and what the cases are allowed to conclude: differences only,
never a verdict. No computed value appears in this file.
"""

from __future__ import annotations

import inspect

import pytest

from rocketforge.comparison import COMPARED, ObservedQuantity, SourceKind, compare, to_canonical
from rocketforge.comparison import ssme_tdk_1985 as module
from rocketforge.comparison import tdk_1985 as shared
from rocketforge.comparison.cases import VERDICT_KINDS, CaseOrigin
from rocketforge.core.constants import STANDARD_GRAVITY
from rocketforge.physics.thermochemistry import ExpansionMode

CASE = module.SSME_TDK_1985_CURRENT_DESIGN
LARGE = module.SSME_TDK_1985_LARGE_THROAT
CASES = pytest.mark.parametrize("case", [CASE, LARGE], ids=["current-design", "large-throat"])


def test_the_two_new_units_are_exact():
    assert to_canonical(1.0, "R") == (5.0 / 9.0, "K", "temperature")
    assert to_canonical(9.0, "R")[0] == 5.0
    assert to_canonical(1.0, "lbf*s/lbm") == (9.80665, "m/s", "velocity")
    assert STANDARD_GRAVITY == 9.80665
    # the same pound-force the psia factor is built from
    assert to_canonical(1.0, "psia")[0] == pytest.approx(0.45359237 * 9.80665 / 0.0254 ** 2, rel=1e-15)


@CASES
def test_each_case_is_an_imported_independent_code_and_draws_no_verdict(case):
    assert case.source_kind is SourceKind.INDEPENDENT_CODE
    assert case.source_kind not in VERDICT_KINDS
    assert case.origin is CaseOrigin.IMPORTED
    assert not case.allows_verdict
    assert case.tolerance_rel is None
    assert case.benchmark_class == "B"
    assert case.code_version.startswith("not stated") and case.database_version.startswith("not stated")


def test_the_current_design_is_transcribed_as_printed():
    printed = {q.key: (q.value, q.unit, q.decimals) for q in CASE.quantities}
    assert printed == {
        "chamber_temperature": (6543.192, "R", 3),
        "vacuum_specific_impulse:equilibrium": (465.1311, "lbf*s/lbm", 4),
        "vacuum_specific_impulse:frozen": (446.7661, "lbf*s/lbm", 4),
    }
    assert (module.CHAMBER_PRESSURE_PSIA, module.OXIDISER_FUEL_RATIO, module.AREA_RATIO) == (3285.0, 6.05485, 77.5)
    assert "19860012108" in CASE.source and "SRC-NTRS-19860012108" in CASE.source
    assert all("Figure 6" in q.note for q in CASE.quantities)


def test_the_large_throat_is_transcribed_as_printed():
    printed = {q.key: (q.value, q.unit, q.decimals) for q in LARGE.quantities}
    assert printed == {
        "chamber_temperature": (6526.882, "R", 3),
        "vacuum_specific_impulse:equilibrium": (463.2604, "lbf*s/lbm", 4),
        "vacuum_specific_impulse:frozen": (444.7228, "lbf*s/lbm", 4),
    }
    assert (module.LARGE_THROAT_CHAMBER_PRESSURE_PSIA, module.LARGE_THROAT_AREA_RATIO) == (3010.0, 69.5)
    assert all("Figure 7" in q.note for q in LARGE.quantities)
    assert "linked to no catalog configuration" in LARGE.inputs["design"]


def test_the_two_cases_come_from_one_report_and_one_set_of_reactant_cards():
    assert LARGE.source == CASE.source and LARGE.code == CASE.code
    assert LARGE.case_id != CASE.case_id
    for reactant, card in (("fuel", "H2(L), -2154. cal/mol, 20.27 K"), ("oxidiser", "O2(L), -3102. cal/mol, 90.180 K")):
        assert CASE.inputs[reactant].startswith(card) and LARGE.inputs[reactant].startswith(card)
    assert CASE.inputs["expansion"] == LARGE.inputs["expansion"]
    assert CASE.inputs["solution"] == LARGE.inputs["solution"]


def test_each_point_pairs_its_case_with_the_inputs_its_figure_states():
    assert module.POINTS == (module.CURRENT_DESIGN, module.LARGE_THROAT)
    current, large = module.POINTS
    assert current.case is CASE and large.case is LARGE
    assert (current.chamber_pressure_psia, current.oxidiser_fuel_ratio, current.area_ratio,
            current.printed_nozzle_area_ratio) == (3285.0, 6.05485, 77.5, 77.50022)
    assert (large.chamber_pressure_psia, large.oxidiser_fuel_ratio, large.area_ratio,
            large.printed_nozzle_area_ratio) == (3010.0, 6.05485, 69.5, 69.48698)
    assert "AS-DB05-US-SSME-BLOCK-I-002" in current.catalog_link
    assert "linked to no catalog configuration" in large.catalog_link
    for point in module.POINTS:
        assert f"{point.area_ratio:g}" in point.case.inputs["area_ratio"]
        assert f"{point.chamber_pressure_psia:g} psia" in point.case.inputs["chamber_pressure"]
        assert str(point.printed_nozzle_area_ratio) in point.case.inputs["area_ratio"]
        assert str(point.printed_nozzle_area_ratio) in " ".join(point.case.missing)


def test_the_expansion_model_is_part_of_the_key():
    assert shared.KEY_VACUUM_ISP_EQUILIBRIUM == f"vacuum_specific_impulse:{ExpansionMode.EQUILIBRIUM.value}"
    assert shared.KEY_VACUUM_ISP_FROZEN == f"vacuum_specific_impulse:{ExpansionMode.FROZEN.value}"
    assert shared.KEY_VACUUM_ISP_EQUILIBRIUM != shared.KEY_VACUUM_ISP_FROZEN


@CASES
def test_only_the_three_ideal_quantities_are_recorded(case):
    keys = {q.key for q in case.quantities}
    assert keys == {shared.KEY_CHAMBER_TEMPERATURE, shared.KEY_VACUUM_ISP_EQUILIBRIUM, shared.KEY_VACUUM_ISP_FROZEN}
    for kept_out in ("ISP (ODK)", "ISP (TDK)", "ISP (TC)", "second-solution", "HCHAM (ODE)"):
        assert kept_out in case.notes, kept_out


def test_each_case_notes_its_own_second_solution_heat():
    assert "DELH1 118.7092" in CASE.notes and "DELH1 116.6856" in LARGE.notes
    assert "Figure 7, the enlarged-throat design, is its own case" in CASE.notes


def _observed(case, scale: float = 1.0) -> dict[str, ObservedQuantity]:
    return {q.key: ObservedQuantity(q.key, q.value * scale, q.unit) for q in case.quantities}


@CASES
@pytest.mark.parametrize("scale", [1.0, 1.0 + 1e-9, 1.01, 0.5])
def test_every_row_is_compared_whatever_the_numbers(case, scale):
    """Made-up numbers, including an exact match: an independent code is never agreed or disagreed with."""
    result = compare(case, _observed(case, scale))
    assert result.verdict == COMPARED
    assert [r.verdict for r in result.rows] == [COMPARED] * 3
    assert all(r.bound is None for r in result.rows)


def test_a_shifting_value_cannot_stand_for_a_frozen_one():
    observed = {shared.KEY_VACUUM_ISP_EQUILIBRIUM: ObservedQuantity(shared.KEY_VACUUM_ISP_EQUILIBRIUM, 4500.0, "m/s")}
    result = compare(CASE, observed)
    assert [r.key for r in result.rows] == [shared.KEY_VACUUM_ISP_EQUILIBRIUM]
    assert set(result.not_observed) == {shared.KEY_CHAMBER_TEMPERATURE, shared.KEY_VACUUM_ISP_FROZEN}


def test_rows_are_in_si_with_the_printed_values_converted_exactly():
    rows = {r.key: r for r in compare(CASE, _observed(CASE)).rows}
    assert rows["chamber_temperature"].unit == "K"
    assert rows["chamber_temperature"].reference == pytest.approx(6543.192 * 5.0 / 9.0, rel=1e-15)
    assert rows[shared.KEY_VACUUM_ISP_FROZEN].unit == "m/s"
    assert rows[shared.KEY_VACUUM_ISP_FROZEN].reference == pytest.approx(446.7661 * 9.80665, rel=1e-15)
    rows = {r.key: r for r in compare(LARGE, _observed(LARGE)).rows}
    assert rows["chamber_temperature"].reference == pytest.approx(6526.882 * 5.0 / 9.0, rel=1e-15)
    assert rows[shared.KEY_VACUUM_ISP_EQUILIBRIUM].reference == pytest.approx(463.2604 * 9.80665, rel=1e-15)


def test_the_case_module_reaches_no_solver():
    source = inspect.getsource(module)
    for layer in ("rocketforge.providers", "rocketforge.engineering", "rocketforge.application", "rocketforge.evidence"):
        assert layer not in source, layer
