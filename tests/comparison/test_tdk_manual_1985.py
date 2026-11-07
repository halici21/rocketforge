"""DB-4C §14: the TDK manual's RL-10 OTV sample as a case, and what every TDK case shares. No provider is needed.

What is pinned here is the source's own printed data and what the case is allowed to conclude: differences only,
never a verdict. No computed value appears in this file.
"""

from __future__ import annotations

import inspect

import pytest

from rocketforge.comparison import COMPARED, ObservedQuantity, SourceKind, compare
from rocketforge.comparison import ssme_tdk_1985 as ssme
from rocketforge.comparison import tdk_1985 as shared
from rocketforge.comparison import tdk_manual_1985 as module
from rocketforge.comparison.cases import VERDICT_KINDS, CaseOrigin

CASE = module.TDK_MANUAL_1985_RL10_OTV
ALL_POINTS = (*ssme.POINTS, *module.POINTS)


def test_the_case_is_an_imported_independent_code_and_draws_no_verdict():
    assert CASE.source_kind is SourceKind.INDEPENDENT_CODE
    assert CASE.source_kind not in VERDICT_KINDS
    assert CASE.origin is CaseOrigin.IMPORTED
    assert not CASE.allows_verdict
    assert CASE.tolerance_rel is None
    assert CASE.benchmark_class == "B"
    assert CASE.code == shared.CODE and CASE.code_version == shared.CODE_VERSION
    assert CASE.database_version.startswith("not stated") and "SP-273" in CASE.database_version


def test_the_sample_is_transcribed_as_printed():
    printed = {q.key: (q.value, q.unit, q.decimals) for q in CASE.quantities}
    assert printed == {
        "chamber_temperature": (5815.918, "R", 3),
        "vacuum_specific_impulse:equilibrium": (477.5184, "lbf*s/lbm", 4),
        "vacuum_specific_impulse:frozen": (456.1371, "lbf*s/lbm", 4),
    }
    assert (module.RL10_OTV_CHAMBER_PRESSURE_PSIA, module.RL10_OTV_OXIDISER_FUEL_RATIO,
            module.RL10_OTV_AREA_RATIO) == (394.3, 5.035244, 205.03)
    assert all("Table 7-3" in q.note for q in CASE.quantities)
    assert "19860007470" in CASE.source and "NASA-CR-178628" in CASE.source


def test_the_point_pairs_the_case_with_the_inputs_table_7_2_states():
    assert module.POINTS == (module.RL10_OTV,)
    point = module.RL10_OTV
    assert point.case is CASE
    assert (point.chamber_pressure_psia, point.oxidiser_fuel_ratio, point.area_ratio,
            point.printed_nozzle_area_ratio) == (394.3, 5.035244, 205.03, 205.0338)
    assert (point.fuel_card_temperature, point.oxidiser_card_temperature) == ("20.56", "90.110")
    assert "linked to no catalog configuration" in point.catalog_link
    assert "Table 7-3" in point.conventions_source and "SSME" not in point.conventions_source


def test_the_engine_is_linked_to_no_catalog_configuration():
    assert "linked to no catalog configuration" in CASE.inputs["engine"]
    assert "CFG-" not in " ".join(CASE.inputs.values())


@pytest.mark.parametrize("point", ALL_POINTS, ids=lambda p: p.case.case_id)
def test_every_point_states_its_inputs_as_its_case_does(point):
    inputs = point.case.inputs
    assert f"{point.chamber_pressure_psia:g} psia" in inputs["chamber_pressure"]
    assert inputs["oxidiser_fuel_ratio"].startswith(f"{point.oxidiser_fuel_ratio} by mass")
    assert f"{point.area_ratio:g}" in inputs["area_ratio"]
    assert str(point.printed_nozzle_area_ratio) in inputs["area_ratio"]
    assert str(point.printed_nozzle_area_ratio) in " ".join(point.case.missing)
    assert f"{point.fuel_card_temperature} K" in inputs["fuel"]
    assert f"{point.oxidiser_card_temperature} K" in inputs["oxidiser"]
    assert point.conventions_source in " ".join(point.case.missing)


@pytest.mark.parametrize("point", ALL_POINTS, ids=lambda p: p.case.case_id)
def test_every_point_prints_the_reactant_enthalpies_the_runner_is_built_for(point):
    """The runner runs every point at one inlet state, CEA's assigned enthalpies (DB-4C §6, §14). That holds only
    while every case's cards print these enthalpies; a point that does not would need its own inlet state."""
    assert point.case.inputs["fuel"].startswith("H2(L), -2154. cal/mol")
    assert point.case.inputs["oxidiser"].startswith("O2(L), -3102. cal/mol")


def test_the_points_are_distinct_cases():
    ids = [p.case.case_id for p in ALL_POINTS]
    assert len(set(ids)) == len(ids) == 3


def test_only_the_three_ideal_quantities_are_recorded():
    assert {q.key for q in CASE.quantities} == {
        shared.KEY_CHAMBER_TEMPERATURE, shared.KEY_VACUUM_ISP_EQUILIBRIUM, shared.KEY_VACUUM_ISP_FROZEN}
    for kept_out in ("ISP (ODK)", "ISP (TDK)", "ISP (TC)", "second-solution", "HCHAM (ODE)", "DELH1 156.3460"):
        assert kept_out in CASE.notes, kept_out
    assert "20.56 K and 90.110 K" in CASE.notes and "-2154.000 and -3102.000" in CASE.notes


@pytest.mark.parametrize("scale", [1.0, 1.0 + 1e-9, 1.01, 0.5])
def test_every_row_is_compared_whatever_the_numbers(scale):
    """Made-up numbers, including an exact match: an independent code is never agreed or disagreed with."""
    observed = {q.key: ObservedQuantity(q.key, q.value * scale, q.unit) for q in CASE.quantities}
    result = compare(CASE, observed)
    assert result.verdict == COMPARED
    assert [r.verdict for r in result.rows] == [COMPARED] * 3
    assert all(r.bound is None for r in result.rows)


def test_rows_are_in_si_with_the_printed_values_converted_exactly():
    observed = {q.key: ObservedQuantity(q.key, q.value, q.unit) for q in CASE.quantities}
    rows = {r.key: r for r in compare(CASE, observed).rows}
    assert rows["chamber_temperature"].reference == pytest.approx(5815.918 * 5.0 / 9.0, rel=1e-15)
    assert rows[shared.KEY_VACUUM_ISP_EQUILIBRIUM].reference == pytest.approx(477.5184 * 9.80665, rel=1e-15)
    assert rows[shared.KEY_VACUUM_ISP_FROZEN].reference == pytest.approx(456.1371 * 9.80665, rel=1e-15)


@pytest.mark.parametrize("source_module", [shared, module, ssme], ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_no_tdk_module_reaches_a_solver(source_module):
    source = inspect.getsource(source_module)
    for layer in ("rocketforge.providers", "rocketforge.engineering", "rocketforge.application", "rocketforge.evidence"):
        assert layer not in source, layer
