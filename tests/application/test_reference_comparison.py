"""Verification of the published-reference dataset and the comparison it feeds.

Two things are under test and they are different:

* the **extraction** -- that the numbers in the dataset really are the numbers
  printed in Anderson Appendix A, parsed correctly from a notation that is easy
  to misread;
* the **comparison** -- that RocketForge recomputes every compared value, that
  the tolerance comes from the source's printed precision, and that a genuine
  disagreement is reported rather than absorbed.

The last of those is checked by deliberately corrupting a copy of the fixture
and requiring the comparison to notice. A comparison system that cannot fail is
not a check.
"""

from __future__ import annotations

import dataclasses
import json
import math

import pytest

from rocketforge.application.analysis import reference_comparison as rc
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso

REFERENCE = rc.load_reference()
AIR = PerfectGas(gamma=1.4)


# ---------------------------------------------------------------------------
# the extracted dataset
# ---------------------------------------------------------------------------


def test_source_metadata_is_complete():
    """A reference without provenance is an unattributed number."""
    source = REFERENCE.source
    for field in ("author", "title", "edition", "appendix", "printed_pages",
                  "notation", "extracted", "extraction_method"):
        assert source.get(field), f"missing source metadata: {field}"
    assert "Anderson" in REFERENCE.citation
    assert "Appendix A" in REFERENCE.citation


def test_gamma_is_determined_from_the_table_not_assumed():
    """The sonic row fixes gamma: T0/T at M = 1 is (gamma+1)/2.

    Printed as 1.200, which gives gamma = 1.4 exactly. This is checked rather
    than taken on faith, because comparing against a table whose gamma we
    guessed would be worse than not comparing at all.
    """
    sonic = REFERENCE.row_for(1.0)
    assert sonic is not None
    implied_gamma = 2.0 * sonic["T0_over_T"] - 1.0
    assert implied_gamma == pytest.approx(1.4, abs=5e-4)
    assert REFERENCE.gamma == pytest.approx(1.4)


def test_row_count_and_range():
    assert len(REFERENCE.rows) == 217
    assert REFERENCE.machs[0] == pytest.approx(0.02)
    assert REFERENCE.machs[-1] == pytest.approx(50.0)


def test_mach_column_is_strictly_increasing_and_unique():
    machs = list(REFERENCE.machs)
    assert all(b > a for a, b in zip(machs, machs[1:]))
    assert len(set(machs)) == len(machs)


def test_every_value_is_finite_and_physical():
    for row in REFERENCE.rows:
        for key in REFERENCE.quantities:
            value = row[key]
            assert math.isfinite(value) and value > 0.0
        assert row["area_ratio"] >= 1.0 - 1e-12, f"A/A* < 1 at M = {row['mach']}"
        assert row["p0_over_p"] >= 1.0 - 1e-12
        assert row["T0_over_T"] >= 1.0 - 1e-12


def test_sonic_row_has_unit_area_ratio():
    sonic = REFERENCE.row_for(1.0)
    assert sonic["area_ratio"] == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("mach,expected", [
    # Rows read visually from the rendered pages of the supplied PDF, in the
    # order p0/p, rho0/rho, T0/T, A/A*.
    (0.5, (1.186, 1.130, 1.050, 1.340)),
    (1.0, (1.893, 1.577, 1.200, 1.000)),
    (2.0, (7.824, 4.347, 1.800, 1.687)),
    (3.0, (36.73, 13.12, 2.800, 4.235)),
    (5.0, (529.1, 88.18, 6.000, 25.00)),
])
def test_manual_extraction_checkpoints(mach, expected):
    """The parser is checked against the printed page, not against itself.

    The notation is the trap: values print as '0.5229 + 02', and some extract
    with spaces around the decimal point. A regex that misses those silently
    shifts every remaining value in the row one column to the left.
    """
    row = REFERENCE.row_for(mach)
    assert row is not None, f"no reference row at M = {mach}"
    got = tuple(row[k] for k in ("p0_over_p", "rho0_over_rho", "T0_over_T", "area_ratio"))
    assert got == pytest.approx(expected, rel=1e-9)


def test_reference_is_effectively_read_only():
    """A computed result must never be able to modify the source table."""
    assert dataclasses.is_dataclass(REFERENCE)
    with pytest.raises(Exception):
        REFERENCE.gamma = 1.3  # type: ignore[misc]


# ---------------------------------------------------------------------------
# tolerance policy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("printed,expected", [
    (1.186, 5e-4),
    (1.000, 5e-4),
    (36.73, 5e-3),
    (529.1, 5e-2),
    (8285.0, 5e-1),
])
def test_tolerance_scales_with_the_printed_magnitude(printed, expected):
    """Four significant figures means ±0.0005 at 1.186 but only ±0.5 at 8285."""
    assert REFERENCE.tolerance_for(printed) == pytest.approx(expected, rel=1e-12)


# ---------------------------------------------------------------------------
# the comparison itself
# ---------------------------------------------------------------------------


def test_comparison_recalculates_rather_than_echoing_the_reference():
    """The computed column must come from physics, not from the fixture."""
    comparison = rc.compare_row(2.0, 1.4)
    assert comparison is not None
    by_key = {q.key: q for q in comparison.quantities}
    assert by_key["p0_over_p"].computed == pytest.approx(
        1.0 / float(iso.pressure_ratio(2.0, AIR)), rel=1e-15)
    assert by_key["area_ratio"].computed == pytest.approx(
        float(iso.area_ratio(2.0, AIR)), rel=1e-15)
    # And it must not merely be the printed value handed back.
    assert by_key["p0_over_p"].computed != by_key["p0_over_p"].reference


def test_book_convention_is_the_reciprocal_of_the_rocketforge_convention():
    """The orientation test this whole feature depends on.

    Anderson prints p0/p; RocketForge computes p/p0. If these ever drift apart
    the comparison would silently be checking the wrong thing.
    """
    reciprocal_pairs = {
        "p0_over_p": iso.pressure_ratio,
        "rho0_over_rho": iso.density_ratio,
        "T0_over_T": iso.temperature_ratio,
    }
    for mach in (0.5, 1.0, 2.0, 3.0):
        row = REFERENCE.row_for(mach)
        for key, relation in reciprocal_pairs.items():
            expected = 1.0 / float(relation(mach, AIR))
            # The source's own precision, not an arbitrary number: 1.129726
            # prints as 1.130, and demanding better would be demanding the book
            # be more precise than it states itself to be.
            assert row[key] == pytest.approx(
                expected, abs=REFERENCE.tolerance_for(row[key]) * (1 + 1e-9)), key
        # A/A* is not a ratio pair: both print it the same way up.
        assert row["area_ratio"] == pytest.approx(
            float(iso.area_ratio(mach, AIR)),
            abs=REFERENCE.tolerance_for(row["area_ratio"]) * (1 + 1e-9))

        # And the orientation really is inverted: at any supersonic Mach the
        # published value and the canonical ratio sit on opposite sides of 1.
        if mach > 1.0:
            assert row["p0_over_p"] > 1.0
            assert float(iso.pressure_ratio(mach, AIR)) < 1.0


def test_untabulated_mach_has_no_reference_row():
    """No interpolation. A Mach between printed rows has no published value."""
    assert REFERENCE.row_for(1.234567) is None
    assert rc.compare_row(1.234567, 1.4) is None


def test_rows_are_matched_by_mach_not_by_index():
    """A user's grid need not align with the published one."""
    assert rc.compare_row(2.0, 1.4) is not None
    assert rc.compare_row(2.0 + 1e-12, 1.4) is not None
    assert rc.compare_row(2.001, 1.4) is None


def test_mismatched_gamma_compares_nothing():
    assert rc.compare_row(2.0, 1.22) is None
    summary = rc.compare_table(1.22)
    assert summary.values_compared == 0
    assert summary.rows_compared == 0


def test_whole_table_comparison_is_computed_not_asserted():
    summary = rc.compare_table(1.4)
    assert summary.rows_compared == 217
    assert summary.values_compared == 868
    assert summary.passed + summary.review == summary.values_compared
    assert summary.citation
    assert 0.0 <= summary.pass_fraction <= 1.0


def test_the_two_known_source_discrepancies_are_reported_not_hidden():
    """Two printed values fall outside their own stated precision.

    Both were investigated before anything was changed, and RocketForge's
    physics was left alone in both cases:

    * M = 16, T0/T -- the book prints 52.29 where the relation gives exactly
      1 + 0.2 * 16^2 = 52.2. The neighbouring rows at M = 15, 17 and 18 are all
      exact, so this is a misprint rather than a modelling difference.
    * M = 7.8, p0/p -- the computed 8285.512 differs from the printed 8285 by
      0.512 units in the last digit, just past the half unit the four-figure
      mantissa implies. A rounding artefact in the source.

    They surface as REVIEW, which is what that status is for.
    """
    summary = rc.compare_table(1.4)
    review_machs = sorted(row.mach for row in summary.reviews)
    assert review_machs == [7.8, 16.0]
    assert summary.review == 2
    assert summary.passed == 866

    # The M = 16 case is arithmetic anyone can check by hand.
    assert 1.0 + 0.2 * 16.0 ** 2 == 52.2
    assert float(1.0 / iso.temperature_ratio(16.0, AIR)) == pytest.approx(52.2, rel=1e-14)


def test_almost_every_published_value_agrees():
    """866 of 868 within the source's own printed precision."""
    summary = rc.compare_table(1.4)
    assert summary.pass_fraction > 0.99
    assert summary.max_relative_difference < 2e-3


def test_status_is_pass_only_when_inside_the_printed_tolerance():
    comparison = rc.compare_row(1.0, 1.4)
    for quantity in comparison.quantities:
        assert quantity.status == "PASS"
        assert abs(quantity.difference) <= quantity.tolerance * (1 + 1e-9)


# ---------------------------------------------------------------------------
# the comparison must be able to fail
# ---------------------------------------------------------------------------


def test_a_corrupted_reference_value_is_detected(tmp_path):
    """Perturb one fixture value and require the comparison to notice.

    Written to a temporary copy: the shipped dataset is source data and is
    never modified, least of all by a test.
    """
    original = json.loads(rc.REFERENCE_PATH.read_text(encoding="utf-8"))
    corrupted = json.loads(json.dumps(original))          # deep copy
    for row in corrupted["rows"]:
        if abs(row["mach"] - 2.0) < 1e-12:
            row["p0_over_p"] = row["p0_over_p"] * 1.01    # 1% off: far outside precision
            break
    else:
        raise AssertionError("no M = 2 row to corrupt")

    path = tmp_path / "corrupted.json"
    path.write_text(json.dumps(corrupted), encoding="utf-8")
    table = rc.load_reference.__wrapped__(str(path))      # bypass the cache

    comparison = rc.compare_row(2.0, 1.4, table)
    assert comparison.status == "REVIEW"
    failed = [q for q in comparison.quantities if not q.passed]
    assert [q.key for q in failed] == ["p0_over_p"]
    assert abs(failed[0].relative_difference) == pytest.approx(0.01, rel=0.02)

    summary = rc.compare_table(1.4, reference=table)
    assert summary.review >= 1
    assert not summary.all_passed

    # And the shipped dataset is untouched by all of that.
    assert json.loads(rc.REFERENCE_PATH.read_text(encoding="utf-8")) == original


def test_the_shipped_dataset_still_passes_after_the_corruption_test():
    """Guard against a test leaking state into the cached reference."""
    summary = rc.compare_table(1.4)
    assert summary.rows_compared == 217
    assert summary.review == 2
