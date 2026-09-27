"""The shipped RP-1311 Example 5 evidence: sourced, in canonical form, and
consistent with the executable formulation it documents.

``RP1311_EXAMPLE5`` in ``rocketforge.providers.cea_solid`` stays the authority for
execution. These tests prove the evidence record says the same thing, field for
field -- they never adjust either side to make the other pass.
"""

from __future__ import annotations

import math
import pathlib
import subprocess
import sys

import pytest

from rocketforge.comparison import COMPARED, ObservedQuantity, SourceKind, compare
from rocketforge.comparison.rp1311 import RP1311_EXAMPLE5_PUBLISHED
from rocketforge.comparison.rp1311_historical import RP1311_EXAMPLE5_PRINT_1996
from rocketforge.evidence import (
    Dimension,
    EvidenceStatus,
    Missing,
    RecordKind,
    ShippingPolicy,
    ValueStatus,
    record_from_json,
    record_to_json,
    reported_values,
    sources_from_json,
    sources_to_json,
)
from rocketforge.providers.cea_solid import RP1311_EXAMPLE5

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / "rocketforge" / "data" / "evidence"
SOURCES_PATH = DATA / "sources.json"
RECORD_PATH = DATA / "records" / "DS-RP1311-E5.json"

CEA_SAMPLE = "S-NASA-CEA-334"
PRINT_1996 = "S-NASA-RP1311-P2-1996"


@pytest.fixture(scope="module")
def sources():
    return sources_from_json(SOURCES_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rp1311(sources):
    return record_from_json(RECORD_PATH.read_text(encoding="utf-8"), sources)


# ------------------------------------------------------------ the shipped files


def test_every_shipped_record_loads_against_the_shipped_registry(sources):
    records = sorted((DATA / "records").glob("*.json"))
    assert records, "no evidence records found"
    for path in records:
        loaded = record_from_json(path.read_text(encoding="utf-8"), sources)
        assert path.stem == loaded.record_id


def test_the_shipped_files_are_in_canonical_form(sources, rp1311):
    """Written by the canonical writer, so a re-save changes nothing and a diff
    of a record shows only what changed in it."""
    assert SOURCES_PATH.read_bytes().decode("utf-8") == sources_to_json(sources.values())
    assert RECORD_PATH.read_bytes().decode("utf-8") == record_to_json(rp1311)


def test_the_registry_holds_the_two_distinct_rp1311_sources(sources):
    assert set(sources) == {CEA_SAMPLE, PRINT_1996}
    assert sources[PRINT_1996].year == 1996
    assert sources[PRINT_1996].identifiers["ntrs_id"] == "19960044559"
    assert sources[CEA_SAMPLE].identifiers["release"] == "v3.3.4"
    assert all(s.shipping is ShippingPolicy.VALUES_WITH_ATTRIBUTION
               for s in sources.values())


# ---------------------------------------------------------------- provenance


def test_every_value_is_reported_located_and_shippable(sources, rp1311):
    values = reported_values(rp1311)
    assert len(values) == 13        # 5 fractions, 4 atoms, h, T_ref, M, T_initial
    for value in values:
        assert value.status is ValueStatus.REPORTED
        assert value.locator.strip()
        assert value.source_id in rp1311.source_ids
        assert sources[value.source_id].values_may_ship


def test_the_formulation_values_come_from_the_sample_the_executable_cites(rp1311):
    """The executable binder cites the cea 3.3.4 sample; so does every value here."""
    assert {v.source_id for v in reported_values(rp1311)} == {CEA_SAMPLE}
    assert "cea 3.3.4" in RP1311_EXAMPLE5.ingredients[1].custom.source
    assert all("samples/rp1311/example5.py" in v.locator for v in reported_values(rp1311))


def test_what_the_source_does_not_state_is_explicitly_missing(rp1311):
    assert isinstance(rp1311.propellant.density, Missing)


# ------------------------------------------------------------ identity and linkage


def test_the_record_identity_and_capabilities(rp1311):
    assert rp1311.record_id == "DS-RP1311-E5"
    assert rp1311.kind is RecordKind.PROPELLANT
    assert rp1311.executable_key == "rp1311-example5"
    assert rp1311.capabilities[Dimension.VA] is EvidenceStatus.REGRESSION_LOCKED
    for dimension in (Dimension.VB, Dimension.VC, Dimension.VD):
        assert rp1311.capabilities[dimension] is EvidenceStatus.NOT_APPLICABLE


def test_the_comparison_cases_it_names_exist_and_are_kept_apart(rp1311):
    cases = {c.case_id: c for c in (RP1311_EXAMPLE5_PUBLISHED, RP1311_EXAMPLE5_PRINT_1996)}
    assert rp1311.comparison_case_ids == tuple(cases)
    locked = cases["rp1311-example5-published"]
    assert locked.source_kind is SourceKind.NASA_PUBLISHED and locked.allows_verdict
    assert locked.code_version == "3.3.4"
    historical = cases["rp1311-example5-print-1996"]
    assert historical.source_kind is SourceKind.INDEPENDENT_CODE
    assert not historical.allows_verdict
    assert historical.tolerance_rel is None


def test_the_executable_key_is_the_one_the_application_offers():
    from rocketforge.application.analysis.thermochemistry_provider import (
        solid_formulation_templates,
    )
    assert solid_formulation_templates()["rp1311-example5"] is RP1311_EXAMPLE5


# ------------------------------------------------ consistency with the executable


def _library_name(item):
    return item.provider_name if item.custom is None else item.source_name


def test_ingredients_match_the_executable_formulation_in_order(rp1311):
    evidence = rp1311.propellant.ingredients
    executable = RP1311_EXAMPLE5.ingredients
    assert [_library_name(i) for i in evidence] == [i.name for i in executable]
    for ours, theirs in zip(evidence, executable):
        assert ours.fraction.unit == "mass fraction"
        assert ours.fraction.value == theirs.mass_fraction          # exact, as printed
        assert (ours.custom is None) is (theirs.custom is None)
        if ours.custom is None:
            assert ours.provider_name == ours.source_name == theirs.name


def test_the_custom_binder_matches_field_for_field(rp1311):
    ours = next(i for i in rp1311.propellant.ingredients if i.custom is not None).custom
    theirs = next(i for i in RP1311_EXAMPLE5.ingredients if i.custom is not None).custom
    assert {e: v.value for e, v in ours.formula.items()} == dict(theirs.formula)
    assert all(v.unit == "atoms per formula unit" for v in ours.formula.values())
    assert ours.enthalpy.value == theirs.heat_of_formation
    assert ours.enthalpy.unit == theirs.heat_of_formation_units
    assert ours.reference_temperature.value == theirs.reference_temperature
    assert ours.reference_temperature.unit == "K"
    assert ours.molecular_weight.value == theirs.molecular_weight
    assert ours.molecular_weight.unit == "g/mol"


def test_the_initial_temperature_and_basis_match(rp1311):
    assert rp1311.propellant.basis == "mass_fraction"
    assert rp1311.propellant.exact_formulation
    assert rp1311.propellant.initial_temperature.value == RP1311_EXAMPLE5.initial_temperature
    assert rp1311.propellant.initial_temperature.unit == "K"


def test_the_stated_fractions_close_without_normalisation(rp1311):
    """A fact about this source, not a rule the loader applies."""
    total = math.fsum(i.fraction.value for i in rp1311.propellant.ingredients)
    assert abs(total - 1.0) <= 1e-12


# ------------------------------------------------------------ the 1996 print


def test_the_1996_print_is_a_separate_case_with_the_transcribed_values():
    by_key = {q.key: q for q in RP1311_EXAMPLE5_PRINT_1996.quantities}
    assert by_key["chamber_temperature"].value == 2724.46
    assert by_key["molar_mass"].value == 22.282
    assert by_key["gamma_s"].value == 1.1945
    assert by_key["mole_fraction:AL2O3(L)"].value == 0.03691
    assert all(q.note.startswith("RP-1311 Part II printed p.13") for q in by_key.values())
    locked = {q.key: q.value for q in RP1311_EXAMPLE5_PUBLISHED.quantities}
    assert locked["chamber_temperature"] == 2723.021      # the lock is unchanged
    assert locked["chamber_temperature"] != by_key["chamber_temperature"].value


def test_the_1996_print_reports_differences_and_draws_no_verdict():
    """The locked 3.3.4 values, handed to the historical case: they differ
    beyond the 1996 printed precision, and the comparison still says only
    ``compared`` -- a data-era difference is not a RocketForge error."""
    observed = {q.key: ObservedQuantity(q.key, q.value, q.unit)
                for q in RP1311_EXAMPLE5_PUBLISHED.quantities}
    result = compare(RP1311_EXAMPLE5_PRINT_1996, observed)
    assert result.verdict == COMPARED
    assert {row.verdict for row in result.rows} == {COMPARED}
    assert not result.not_observed
    temperature = next(r for r in result.rows if r.key == "chamber_temperature")
    assert temperature.abs_diff == pytest.approx(2723.021 - 2724.46)
    assert temperature.bound is None


# ------------------------------------------------------------ purity


def test_loading_evidence_imports_no_physics_provider_comparison_or_qt():
    """Evidence is browsed without anything being solvable: loading the shipped
    data must not pull in a solver, a provider, the comparison layer or Qt."""
    code = (
        "import sys, pathlib\n"
        "from rocketforge.evidence import sources_from_json, record_from_json\n"
        f"d = pathlib.Path({str(DATA)!r})\n"
        "s = sources_from_json((d / 'sources.json').read_text(encoding='utf-8'))\n"
        "record_from_json((d / 'records' / 'DS-RP1311-E5.json').read_text(encoding='utf-8'), s)\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in ('cea', 'PySide6', 'CoolProp')"
        " or m.startswith(('rocketforge.physics', 'rocketforge.providers',"
        " 'rocketforge.comparison', 'rocketforge.application', 'rocketforge.engineering')))\n"
        "print(bad)\n")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.strip()
    assert out == "[]"
