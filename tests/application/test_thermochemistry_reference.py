"""The reference comparison, and the boundary it deliberately stops at.

The dataset is a published NASA CEA case. Three things about it are load
bearing and each has a test:

* the comparison **reads the shipped dataset** rather than repeating numbers in
  code, so a change to the data changes the verdict;
* the tolerance is the **source's own rounding box**, derived from its printed
  precision before the comparison runs;
* the source carries c\\*, Isp and an exit gamma, and Phase 5D loads **no value**
  for any of them, because RocketForge owns none of them yet.
"""

from __future__ import annotations

import copy
import json

import pytest

from rocketforge.application.analysis import thermochemistry_provider as gateway
from rocketforge.application.analysis import thermochemistry_reference as ref

_STATUS = gateway.availability()
requires_cea = pytest.mark.skipif(
    not _STATUS.usable,
    reason=f"NASA CEA provider unavailable ({_STATUS.status})")


@pytest.fixture()
def payload():
    """A private copy of the shipped dataset, safe to mutate in a test."""
    return copy.deepcopy(ref.load_reference())


# ===========================================================================
# the dataset
# ===========================================================================


def test_the_dataset_ships_with_the_application():
    """Read through ``reference_root``, which knows about the frozen bundle."""
    from rocketforge.application.analysis.reference_comparison import reference_root

    path = reference_root() / ref.THERMOCHEMISTRY_REFERENCE
    assert path.exists(), path
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["kind"] == "thermochemistry_chamber"


def test_a_dataset_of_the_wrong_kind_is_refused(tmp_path, monkeypatch):
    """A mis-filed file fails loudly rather than being compared wrongly."""
    from rocketforge.application.analysis import thermochemistry_reference as module

    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"kind": "compressible_table"}), encoding="utf-8")
    monkeypatch.setattr(module, "reference_root", lambda: tmp_path)
    module.load_reference.cache_clear()
    try:
        with pytest.raises(ValueError, match="not a thermochemistry"):
            module.load_reference("wrong.json")
    finally:
        module.load_reference.cache_clear()


def test_the_case_is_the_published_one(payload):
    case = ref.reference_case(payload)
    assert case.case.oxidiser == "LOX"
    assert case.case.fuel == "LH2"
    assert case.case.oxidiser_fuel_ratio == pytest.approx(6.0)
    # 1000 psia, converted with the exact definitions of the pound-force and
    # the inch.
    assert case.case.chamber_pressure == pytest.approx(1000.0 * 6894.757293168361)
    assert case.case.fuel_temperature == pytest.approx(20.27)


def test_the_source_is_identified_and_its_independence_stated(payload):
    case = ref.reference_case(payload)
    assert "NASA" in case.citation
    assert "2002" in case.citation
    assert "McBride" in case.citation
    independence = case.source["independence"]
    assert "2002 Fortran" in independence
    assert "v3" in independence


def test_the_source_rows_carry_the_conditions_not_just_a_verdict(payload):
    rows = {row["label"]: row["value"] for row in ref.source_rows(
        ref.reference_case(payload))}
    assert rows["Propellants"] == "O2(L) / H2(L)"
    assert rows["Chamber Pressure"] == "1000.0 psia"
    assert "equilibrium" in rows["Chemistry"]


# ===========================================================================
# tolerance
# ===========================================================================


def test_the_tolerance_is_the_sources_printed_precision(payload):
    case = ref.reference_case(payload)
    temperature = next(q for q in case.quantities if q.key == "chamber_temperature")
    # 3483.35 printed to six significant figures: half a unit in the last
    # digit is 0.005, relative 1.435e-06.
    assert temperature.significant_figures == 6
    assert temperature.tolerance == pytest.approx(0.005 / 3483.35, rel=1e-9)


def test_the_rounding_box_widens_as_precision_falls():
    assert ref.rounding_box(431.2, 4) > ref.rounding_box(431.2, 6)


def test_the_published_values_convert_into_si(payload):
    case = ref.reference_case(payload)
    molar_mass = next(q for q in case.quantities if q.key == "chamber_molar_mass")
    assert molar_mass.unit == "kg/kmol"
    assert molar_mass.si_unit == "kg/mol"
    assert molar_mass.si_value == pytest.approx(0.013458)


# ===========================================================================
# the performance boundary
# ===========================================================================


def test_no_performance_value_is_loaded_at_all(payload):
    """Not hidden -- absent. A value never read cannot leak into a display."""
    for entry in payload["not_compared"]:
        assert "value" not in entry, entry
        assert entry["reason"]
    for entry in payload["published"]:
        assert entry["key"] in ("chamber_temperature", "chamber_molar_mass")


def test_the_comparison_model_exposes_no_performance_quantity(payload):
    case = ref.reference_case(payload)
    for quantity in case.quantities:
        text = f"{quantity.key} {quantity.label} {quantity.state_field}".lower()
        for banned in ("c*", "cstar", "isp", "thrust", "impulse", "cf"):
            assert banned not in text, quantity.key
        # And the field it reads is a chamber-state field, not a performance one.
        assert quantity.state_field in ("temperature", "molar_mass")


def test_what_the_source_publishes_but_this_phase_omits_is_stated(payload):
    case = ref.reference_case(payload)
    labels = " ".join(entry["label"] for entry in case.not_compared)
    assert "c*" in labels
    assert "Isp" in labels
    reasons = " ".join(entry["reason"] for entry in case.not_compared)
    assert "Phase 5E" in reasons or "not implemented" in reasons


# ===========================================================================
# the comparison
# ===========================================================================


def test_a_result_without_the_quantity_fails_rather_than_disappearing(payload):
    from rocketforge.application.analysis.thermochemistry_service import (
        OUTCOME_NO_SOLUTION,
        ChamberOutcome,
    )

    case = ref.reference_case(payload)
    rows = ref.compare(case, ChamberOutcome(kind=OUTCOME_NO_SOLUTION))
    assert len(rows) == len(case.quantities)
    assert all(not row.passed for row in rows)
    assert all(row.computed is None for row in rows)
    assert ref.overall_verdict(rows) == "FAIL"


def test_the_overall_verdict_gives_no_partial_credit():
    from rocketforge.application.analysis.thermochemistry_reference import (
        ReferenceComparison,
    )

    good = ReferenceComparison(key="a", label="A", published=1.0,
                               published_unit="K", computed=1.0, unit="K",
                               relative_difference=0.0, tolerance=1e-6,
                               passed=True)
    bad = ReferenceComparison(key="b", label="B", published=1.0,
                              published_unit="K", computed=2.0, unit="K",
                              relative_difference=1.0, tolerance=1e-6,
                              passed=False)
    assert ref.overall_verdict((good, good)) == "PASS"
    assert ref.overall_verdict((good, bad)) == "FAIL"
    assert ref.overall_verdict(()) == "NOT RUN"


# ===========================================================================
# live provider
# ===========================================================================


@requires_cea
def test_the_pipeline_reproduces_the_published_case(payload):
    case = ref.reference_case(payload)
    outcome = ref.run_reference(case)
    rows = ref.compare(case, outcome)
    assert ref.overall_verdict(rows) == "PASS"
    for row in rows:
        assert row.relative_difference <= row.tolerance, (
            f"{row.label}: {row.relative_difference:.3e} exceeds the source's "
            f"rounding box {row.tolerance:.3e}")


@requires_cea
def test_the_agreement_is_close_but_not_suspiciously_exact(payload):
    """Two implementations of the same method, not one number copied twice."""
    case = ref.reference_case(payload)
    rows = ref.compare(case, ref.run_reference(case))
    assert all(row.relative_difference > 0.0 for row in rows), (
        "an exact match would suggest the reference is being read rather "
        "than compared against")


@requires_cea
def test_the_reference_case_ignores_the_calculator_inputs(payload):
    """Whatever is in the form, the reference runs its stored conditions."""
    case = ref.reference_case(payload)
    outcome = ref.run_reference(case)
    assert outcome.case.oxidiser_fuel_ratio == pytest.approx(6.0)
    assert outcome.case.fuel == "LH2"


@requires_cea
def test_a_modified_reference_value_changes_the_verdict(payload):
    """The mutation proof. Without it the comparison could be vacuous.

    The fixture is asserted to have actually changed before the verdict is
    checked, so a no-op edit cannot pass this test.
    """
    case = ref.reference_case(payload)
    outcome = ref.run_reference(case)
    assert ref.overall_verdict(ref.compare(case, outcome)) == "PASS"

    mutated = copy.deepcopy(payload)
    entry = next(e for e in mutated["published"]
                 if e["key"] == "chamber_temperature")
    original = entry["value"]
    entry["value"] = original * 1.01          # 1 %, far outside a rounding box
    assert entry["value"] != original, "the fixture did not change"

    mutated_case = ref.reference_case(mutated)
    assert mutated_case.quantities[0].value != case.quantities[0].value, (
        "the unpacked case did not pick up the change")

    rows = ref.compare(mutated_case, outcome)
    assert ref.overall_verdict(rows) == "FAIL"
    failed = next(row for row in rows if row.key == "chamber_temperature")
    assert failed.relative_difference > failed.tolerance


@requires_cea
def test_a_widened_tolerance_would_have_to_be_declared(payload):
    """Tolerance comes from the data, so it cannot be quietly loosened.

    Changing the declared significant figures is the only way to widen the
    box, and it changes the published dataset -- which is exactly the intent.
    """
    mutated = copy.deepcopy(payload)
    entry = next(e for e in mutated["published"]
                 if e["key"] == "chamber_temperature")
    entry["significant_figures"] = 3
    case = ref.reference_case(mutated)
    assert case.quantities[0].tolerance > ref.reference_case(payload).quantities[0].tolerance
