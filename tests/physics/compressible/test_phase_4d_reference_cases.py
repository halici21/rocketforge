"""RocketForge's Prandtl-Meyer results against Anderson Appendix C.

The direction is fixed and it is the whole point of the file:

    published table  --compare-->  RocketForge computed value

Every one of the 336 printed values is *recomputed* from the physics layer and
set beside its printed counterpart. Nothing is looked up, nothing is
interpolated, and no reference value is ever used as an input to the
calculation it is checking.

Appendix C prints degrees; the physics layer works in radians. The conversion
happens in the reference adapter, at the boundary -- never inside a relation,
and never by a second implementation of the relation in degrees.
"""

from __future__ import annotations

import json
import math
import pathlib

import pytest

from rocketforge.application.analysis import reference_comparison as rc
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import isentropic as iso
from rocketforge.physics.compressible import prandtl_meyer as pm

TABLE = rc.load_prandtl_meyer_reference()
AIR = PerfectGas(gamma=1.4)
PAYLOAD = json.loads(rc.PRANDTL_MEYER_REFERENCE_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# the dataset itself
# ---------------------------------------------------------------------------


def test_dataset_identifies_its_source():
    source = TABLE.source
    assert source["author"] == "John D. Anderson, Jr."
    assert source["title"] == "Fundamentals of Aerodynamics"
    assert source["edition"] == "6th Edition"
    assert source["appendix"].startswith("Appendix C")
    assert source["printed_pages"] == "1089-1091"
    assert "Appendix C" in TABLE.citation


def test_dataset_covers_the_printed_range():
    assert len(TABLE.rows) == 168
    assert TABLE.machs[0] == pytest.approx(1.0)
    assert TABLE.machs[-1] == pytest.approx(50.0)
    assert list(TABLE.machs) == sorted(TABLE.machs)
    assert TABLE.gamma == pytest.approx(1.4)


def test_the_angle_units_are_recorded_and_are_degrees():
    """The physics is radians; the source is degrees; the file says which."""
    assert PAYLOAD["angle_units"] == "degrees"
    assert "asin(1/M)" in PAYLOAD["angle_units_determination"]
    sonic = TABLE.row_for(1.0)
    assert sonic["mach_angle"] == 90.0, "a right angle in degrees, not pi/2"


def test_every_column_is_recomputable():
    assert set(TABLE.quantities) == set(TABLE.spec.recipe) == {"nu", "mach_angle"}


def test_gamma_was_established_from_the_table_not_assumed():
    """The determination is recorded, and re-derived here from the rows."""
    assert "gamma_determination" in PAYLOAD
    worst = {}
    for gamma in (1.2, 1.3, 1.4, 1.66):
        gas = PerfectGas(gamma=gamma)
        worst[gamma] = max(abs(math.degrees(float(pm.nu(row["mach"], gas))) - row["nu"])
                           for row in TABLE.rows[1:])
    assert worst[1.4] < 0.06
    assert min(worst, key=worst.get) == 1.4
    assert worst[min(g for g in worst if g != 1.4)] > 10.0 * worst[1.4]

    # The largest printed nu must also sit under the ceiling for this gamma.
    assert max(r["nu"] for r in TABLE.rows) < math.degrees(pm.nu_max(AIR))


def test_the_source_is_internally_consistent_before_we_compare_to_it():
    """Screens that use none of our gas dynamics.

    The Mach-angle column is pure geometry, so it can be checked without any
    choice of gamma at all -- which makes it an independent witness for the
    extraction of two of the three columns.
    """
    for row in TABLE.rows:
        mach = row["mach"]
        assert mach >= 1.0
        assert row["nu"] >= 0.0
        assert 0.0 < row["mach_angle"] <= 90.0
        expected = math.degrees(math.asin(min(1.0, 1.0 / mach)))
        assert row["mach_angle"] == pytest.approx(
            expected, abs=TABLE.tolerance_for(row["mach_angle"]) * (1.0 + 1e-9)), mach


def test_printed_columns_are_monotonic_in_the_right_directions():
    """A shifted column would break these without any physics being consulted."""
    for previous, row in zip(TABLE.rows, TABLE.rows[1:]):
        assert row["mach"] > previous["mach"]
        assert row["nu"] >= previous["nu"]
        assert row["mach_angle"] <= previous["mach_angle"]


def test_the_sonic_row_is_the_one_every_reader_checks_first():
    sonic = TABLE.row_for(1.0)
    assert sonic["nu"] == 0.0
    assert sonic["mach_angle"] == 90.0


# ---------------------------------------------------------------------------
# the comparison
# ---------------------------------------------------------------------------


def test_whole_appendix_c_compared_at_printed_precision():
    summary = rc.compare_table(1.4, reference=TABLE)
    assert summary.rows_compared == 168
    assert summary.values_compared == 336
    assert summary.passed == 336
    assert summary.review == 0
    assert summary.all_passed


def test_no_source_anomaly_was_found():
    """Recorded as a fact about this extraction, not assumed.

    Appendices A and B each needed a correction or carried a rounding tie.
    Appendix C needed neither, and saying so explicitly is what makes the
    other two credible.
    """
    assert PAYLOAD["extraction_corrections"] == []
    assert "print_rounding_ties" not in PAYLOAD
    assert rc.compare_table(1.4, reference=TABLE).review == 0


@pytest.mark.parametrize("mach", [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0])
def test_named_reference_rows_value_by_value(mach):
    comparison = rc.compare_row(mach, 1.4, TABLE)
    assert comparison is not None
    assert comparison.passed, [
        (q.key, q.computed, q.reference) for q in comparison.quantities if not q.passed]
    for quantity in comparison.quantities:
        assert abs(quantity.difference) <= quantity.tolerance * (1.0 + 1e-9)


@pytest.mark.parametrize("checkpoint", PAYLOAD["verified_checkpoints"],
                         ids=[str(c["mach"]) for c in PAYLOAD["verified_checkpoints"]])
def test_the_visually_confirmed_checkpoints_hold(checkpoint):
    """The rows read off the rendered pages, re-asserted against the physics."""
    assert checkpoint["confirmed"] is True
    mach = checkpoint["mach"]
    read = checkpoint["read_from_page_image"]
    row = TABLE.row_for(mach)
    assert row["nu"] == pytest.approx(read["nu"], abs=1e-9)
    assert row["mach_angle"] == pytest.approx(read["mach_angle"], abs=1e-9)
    assert math.degrees(float(pm.nu(mach, AIR))) == pytest.approx(
        read["nu"], abs=TABLE.tolerance_for(max(read["nu"], 1e-4)) * (1.0 + 1e-9))
    assert math.degrees(float(iso.mach_angle(mach))) == pytest.approx(
        read["mach_angle"], abs=TABLE.tolerance_for(read["mach_angle"]) * (1.0 + 1e-9))


def test_no_interpolation_between_printed_rows():
    assert TABLE.row_for(2.005) is None
    assert rc.compare_row(2.005, 1.4, TABLE) is None


def test_a_different_gamma_is_not_compared_against_a_gamma_1_4_table():
    assert rc.compare_row(2.0, 1.3, TABLE) is None
    assert rc.compare_table(1.3, reference=TABLE).values_compared == 0


def test_a_printed_zero_is_agreement_and_not_an_infinite_relative_difference():
    """nu = 0 at Mach 1 is the first legitimate printed zero in any dataset here.

    Dividing by it produced an infinite "maximum relative difference" that the
    summary then displayed. A zero difference from a printed zero is exact
    agreement, and now reports as such.
    """
    comparison = rc.compare_row(1.0, 1.4, TABLE)
    nu_row = next(q for q in comparison.quantities if q.key == "nu")
    assert nu_row.reference == 0.0
    assert nu_row.difference == 0.0
    assert nu_row.relative_difference == 0.0
    assert math.isfinite(rc.compare_table(1.4, reference=TABLE).max_relative_difference)


# ---------------------------------------------------------------------------
# the detector
# ---------------------------------------------------------------------------


def _fixture_copy(tmp_path):
    payload = json.loads(rc.PRANDTL_MEYER_REFERENCE_PATH.read_text(encoding="utf-8"))
    return tmp_path / "perturbed_appendix_c.json", payload


def test_a_perturbed_reference_value_is_detected(tmp_path):
    """A comparison that cannot fail proves nothing.

    The real dataset is never touched -- the last assertion checks that.
    """
    original_bytes = rc.PRANDTL_MEYER_REFERENCE_PATH.read_bytes()
    path, payload = _fixture_copy(tmp_path)

    for row in payload["rows"]:
        if abs(row["mach"] - 2.0) < 1e-9:
            row["nu"] = 27.50            # printed value is 26.38
            break
    else:                                 # pragma: no cover
        pytest.fail("M = 2 row not present")

    path.write_text(json.dumps(payload), encoding="utf-8")
    table = rc.load_reference.__wrapped__(str(path))

    comparison = rc.compare_row(2.0, 1.4, table)
    assert comparison is not None
    assert comparison.status == "REVIEW"
    offending = [q for q in comparison.quantities if not q.passed]
    assert [q.key for q in offending] == ["nu"]
    assert offending[0].computed == pytest.approx(26.3797608134, abs=1e-6)

    assert rc.compare_table(1.4, reference=table).review == 1
    assert rc.PRANDTL_MEYER_REFERENCE_PATH.read_bytes() == original_bytes


def test_a_perturbation_inside_the_printed_precision_is_not_flagged(tmp_path):
    """The detector must not cry wolf, or every REVIEW becomes meaningless."""
    path, payload = _fixture_copy(tmp_path)
    for row in payload["rows"]:
        if abs(row["mach"] - 2.0) < 1e-9:
            row["nu"] = row["nu"] + 0.003
            break
    path.write_text(json.dumps(payload), encoding="utf-8")
    table = rc.load_reference.__wrapped__(str(path))
    assert rc.compare_row(2.0, 1.4, table).passed


def test_a_shifted_row_is_detected(tmp_path):
    """The failure mode that threatens a column-extracted table.

    Swapping nu and mu on one row is what a lost token looks like.
    """
    path, payload = _fixture_copy(tmp_path)
    for row in payload["rows"]:
        if abs(row["mach"] - 3.0) < 1e-9:
            row["nu"], row["mach_angle"] = row["mach_angle"], row["nu"]
            break
    path.write_text(json.dumps(payload), encoding="utf-8")
    table = rc.load_reference.__wrapped__(str(path))

    comparison = rc.compare_row(3.0, 1.4, table)
    assert comparison.status == "REVIEW"
    assert len([q for q in comparison.quantities if not q.passed]) == 2


def test_a_file_declaring_an_unknown_dataset_is_refused(tmp_path):
    path, payload = _fixture_copy(tmp_path)
    payload["dataset"] = "some_table_we_have_no_recipe_for"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(KeyError):
        rc.load_reference.__wrapped__(str(path))


def test_the_three_appendices_are_independent_datasets():
    """A, B and C load side by side, each with its own recipe and Mach key."""
    a = rc.load_reference()
    b = rc.load_normal_shock_reference()
    c = rc.load_prandtl_meyer_reference()
    assert {a.dataset, b.dataset, c.dataset} == {
        rc.ISENTROPIC_DATASET, rc.NORMAL_SHOCK_DATASET, rc.PRANDTL_MEYER_DATASET}
    assert (a.mach_key, b.mach_key, c.mach_key) == ("mach", "mach1", "mach")


def test_each_appendix_meets_its_own_pinned_outcome():
    """Whole-table comparison of all three, against counts recorded in the data.

    Comparing Appendix A over its *whole* range -- which nothing did before this
    phase, the Isentropic page's default table stopping at M = 5 -- surfaced two
    source anomalies that are now recorded beside the rows. Pinning the counts
    here means a new disagreement fails rather than joining an approved total.
    """
    for table in (rc.load_reference(), rc.load_normal_shock_reference(),
                  rc.load_prandtl_meyer_reference()):
        payload = json.loads(pathlib.Path(table.spec.path).read_text(encoding="utf-8"))
        expected = payload["expected_comparison_outcome"]
        summary = rc.compare_table(1.4, reference=table)
        assert summary.rows_compared == expected.get("rows_compared", summary.rows_compared)
        assert summary.values_compared == expected["values_compared"], table.dataset
        assert summary.passed == expected["pass"], table.dataset
        assert summary.review == expected["review"], table.dataset


def test_the_appendix_a_anomalies_are_the_two_that_are_documented():
    """Pinned by Mach and column, with the misprint identified as such."""
    table = rc.load_reference()
    payload = json.loads(rc.REFERENCE_PATH.read_text(encoding="utf-8"))
    documented = {(round(a["mach"], 4), a["column"]) for a in payload["source_anomalies"]}
    offenders = {
        (round(row.mach, 4), quantity.key)
        for row in rc.compare_table(1.4, reference=table).reviews
        for quantity in row.quantities if not quantity.passed
    }
    assert offenders == documented == {(7.8, "p0_over_p"), (16.0, "T0_over_T")}

    misprint = next(a for a in payload["source_anomalies"] if a["mach"] == 16.0)
    assert misprint["classification"] == "suspected_misprint"
    # The identity that settles it needs no solver and no gamma exponent.
    assert 1.0 + 0.2 * 16.0 ** 2 == 52.2
    assert misprint["exact_value"] == 52.2
    assert table.row_for(16.0)["T0_over_T"] == pytest.approx(52.29, abs=1e-9), (
        "the printed value is preserved")
