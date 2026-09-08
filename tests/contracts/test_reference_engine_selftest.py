"""Does the reference comparison actually detect a mismatch?

A comparison engine that always reports PASS proves nothing, and would hide
every error the published tables exist to catch. So the engine is pointed at
deliberately corrupted copies of the real data and required to notice.

The shipped datasets are never touched: each mutation is applied to an
in-memory copy, and a final test asserts the real files are unchanged.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib

import pytest

from rocketforge.application.analysis.reference_comparison import (
    ReferenceTable,
    compare_table,
    load_normal_shock_reference,
    load_prandtl_meyer_reference,
    load_reference,
    reference_root,
)

DATASETS = ("anderson6_appendix_a_isentropic.json",
            "anderson6_appendix_b_normal_shock.json",
            "anderson6_appendix_c_prandtl_meyer.json",
            "fanno_nasa_tm_2006_214086.json",
            "rayleigh_nasa_tm_2006_214086.json",
            "nozzle_anderson6_constructed.json")


def digests() -> dict[str, str]:
    return {name: hashlib.sha256(
        (reference_root() / name).read_bytes()).hexdigest() for name in DATASETS}


BEFORE = digests()


# ---------------------------------------------------------------------------
# the engine notices
# ---------------------------------------------------------------------------


def mutated(table: ReferenceTable, quantity: str, factor: float) -> ReferenceTable:
    """A copy of a real table with one column nudged off its published value.

    The rows are plain dicts, so they are rebuilt rather than edited in place:
    the first version of this helper wrote ``row.values``, which on a dict is
    the *method*, and silently mutated nothing -- the vacuous self-test this
    file exists to prevent.
    """
    assert quantity in table.quantities, f"{quantity} is not a column of this table"
    rows = tuple({key: (value * factor if key == quantity else value)
                  for key, value in row.items()} for row in table.rows)
    changed = sum(1 for before, after in zip(table.rows, rows)
                  if before.get(quantity) != after.get(quantity))
    assert changed > 0, "the mutation changed nothing, so the test proves nothing"
    return dataclasses.replace(table, rows=rows)


def test_the_untouched_table_passes():
    """The control: without a mutation the comparison is clean apart from the
    two anomalies Phase 4B/4C already pinned and explained."""
    summary = compare_table(1.4)
    assert summary.values_compared > 800
    assert summary.review == 2, "the two known Appendix A anomalies, and no others"
    assert summary.passed == summary.values_compared - summary.review


@pytest.mark.parametrize("quantity", ["p0_over_p", "T0_over_T", "area_ratio"])
def test_a_single_corrupted_column_is_detected(quantity):
    """Perturb one published column by 1% and the engine must report it."""
    table = load_reference()
    corrupted = mutated(table, quantity, 1.01)
    summary = compare_table(1.4, reference=corrupted)
    assert summary.review > 2, (
        f"a 1% error in {quantity} went unnoticed; the comparison is not "
        "actually comparing")
    assert not summary.all_passed


def test_a_tiny_corruption_below_printed_precision_is_tolerated():
    """The other half of the same claim: the tolerance is not zero.

    A perturbation far below the printed precision must *not* raise REVIEW, or
    the comparison would be reporting rounding as error.
    """
    table = load_reference()
    corrupted = mutated(table, "p0_over_p", 1.0 + 1e-9)
    summary = compare_table(1.4, reference=corrupted)
    assert summary.review == 2


@pytest.mark.parametrize("loader", [load_normal_shock_reference,
                                    load_prandtl_meyer_reference])
def test_the_other_appendices_are_compared_too(loader):
    summary = compare_table(1.4, reference=loader())
    assert summary.values_compared > 0
    assert summary.passed > 0


def test_a_corrupted_normal_shock_column_is_detected():
    table = load_normal_shock_reference()
    corrupted = mutated(table, "p2_over_p1", 1.01)
    summary = compare_table(1.4, reference=corrupted)
    assert summary.review > 0
    assert not summary.all_passed


# ---------------------------------------------------------------------------
# the shipped data is exactly what it was
# ---------------------------------------------------------------------------


def test_every_reference_dataset_is_present():
    for name in DATASETS:
        assert (reference_root() / name).is_file(), name


def test_the_mutations_never_touched_the_shipped_files():
    assert digests() == BEFORE


@pytest.mark.parametrize("name", DATASETS)
def test_every_dataset_carries_its_provenance(name):
    """61: a user must be able to find out where a number came from."""
    payload = json.loads((reference_root() / name).read_text(encoding="utf-8"))
    source = payload.get("source")
    assert source, f"{name} has no source"
    text = json.dumps(source) if isinstance(source, dict) else str(source)
    assert len(text) > 40, f"{name} has a source but no detail"
    assert "tolerance_rule" in payload, f"{name} does not say how it is compared"


@pytest.mark.parametrize("name", DATASETS)
def test_no_dataset_is_still_pending(name):
    """57: a blocking reference case may not remain unconfirmed at freeze."""
    text = (reference_root() / name).read_text(encoding="utf-8").lower()
    for word in ("\"pending\"", "unconfirmed", "todo", "provisional"):
        assert word not in text, f"{name} still contains {word}"
