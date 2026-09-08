"""RocketForge's normal-shock results against Anderson Appendix B.

The direction is fixed and it is the whole point of the file:

    published table  --compare-->  RocketForge computed value

Every one of the 1008 printed values is *recomputed* from the physics layer
and set beside its printed counterpart. Nothing is looked up, nothing is
interpolated, and no reference value is ever used as an input to the
calculation it is checking.

Two printed values disagree with round-to-nearest in their last digit. Both
were confirmed against the rendered page and against a 40-digit independent
evaluation, and both are recorded in the dataset under ``print_rounding_ties``.
They are asserted here as expected REVIEWs rather than being tolerated by a
widened tolerance -- so a *new* disagreement anywhere in the table fails.
"""

from __future__ import annotations

import json
import math
import pathlib
from decimal import Decimal, getcontext
from fractions import Fraction

import pytest

from rocketforge.application.analysis import reference_comparison as rc
from rocketforge.physics.compressible import PerfectGas
from rocketforge.physics.compressible import normal_shock as ns

TABLE = rc.load_normal_shock_reference()
GAS = PerfectGas(gamma=1.4)


# ---------------------------------------------------------------------------
# the dataset itself
# ---------------------------------------------------------------------------


def test_dataset_identifies_its_source():
    source = TABLE.source
    assert source["author"] == "John D. Anderson, Jr."
    assert source["title"] == "Fundamentals of Aerodynamics"
    assert source["edition"] == "6th Edition"
    assert source["appendix"].startswith("Appendix B")
    assert source["printed_pages"] == "1085-1088"
    assert "Appendix B" in TABLE.citation


def test_dataset_covers_the_printed_range():
    assert len(TABLE.rows) == 168
    assert TABLE.machs[0] == pytest.approx(1.0)
    assert TABLE.machs[-1] == pytest.approx(50.0)
    assert list(TABLE.machs) == sorted(TABLE.machs)
    assert TABLE.gamma == pytest.approx(1.4)


def test_every_column_is_recomputable():
    """A published column with no recipe would be a table we cannot check."""
    assert set(TABLE.quantities) == set(TABLE.spec.recipe)
    assert TABLE.mach_key == "mach1"


def test_gamma_was_established_from_the_table_not_assumed():
    payload = json.loads(rc.NORMAL_SHOCK_REFERENCE_PATH.read_text(encoding="utf-8"))
    assert "gamma_determination" in payload
    # The three asymptotes the dataset cites, re-derived here from its own rows.
    last = TABLE.rows[-1]
    assert last["rho2_over_rho1"] == pytest.approx(ns.density_ratio_limit(GAS), abs=0.02)
    assert last["mach2"] == pytest.approx(ns.mach_downstream_limit(GAS), abs=5e-4)
    sonic = TABLE.row_for(1.0)
    assert sonic["p02_over_p1"] == pytest.approx(1.893, abs=5e-4)


def test_the_source_is_internally_consistent_before_we_compare_to_it():
    """Screen the printed rows against constraints that use none of our equations.

    If the extraction were corrupt, this fails without ever consulting
    RocketForge -- which is what makes the comparison below meaningful.
    """
    for row in TABLE.rows:
        mach1 = row["mach1"]
        assert row["p2_over_p1"] >= 1.0, mach1
        assert row["rho2_over_rho1"] >= 1.0, mach1
        assert row["T2_over_T1"] >= 1.0, mach1
        assert 0.0 < row["p02_over_p01"] <= 1.0, mach1
        assert row["mach2"] <= 1.0, mach1
        assert row["p02_over_p1"] >= 1.0, mach1
        # The ideal gas law, from printed values alone. The tolerance is
        # propagated from the printed precision of the three values rather
        # than guessed: d(rho*T) = rho*dT + T*drho, plus the precision of
        # p2/p1 itself.
        pressure = row["p2_over_p1"]
        density = row["rho2_over_rho1"]
        temperature = row["T2_over_T1"]
        slack = (TABLE.tolerance_for(pressure)
                 + density * TABLE.tolerance_for(temperature)
                 + temperature * TABLE.tolerance_for(density))
        assert abs(pressure - density * temperature) <= slack, mach1


def test_printed_columns_are_monotonic_in_the_right_directions():
    """Another source-only screen: a shifted column would break these."""
    for previous, row in zip(TABLE.rows, TABLE.rows[1:]):
        assert row["p2_over_p1"] > previous["p2_over_p1"]
        assert row["rho2_over_rho1"] > previous["rho2_over_rho1"]
        assert row["T2_over_T1"] > previous["T2_over_T1"]
        assert row["p02_over_p01"] <= previous["p02_over_p01"]
        assert row["mach2"] <= previous["mach2"]


# ---------------------------------------------------------------------------
# the comparison
# ---------------------------------------------------------------------------

EXPECTED = json.loads(rc.NORMAL_SHOCK_REFERENCE_PATH.read_text(encoding="utf-8"))[
    "expected_comparison_outcome"
]


def test_whole_appendix_b_compared_at_printed_precision():
    summary = rc.compare_table(1.4, reference=TABLE)
    assert summary.rows_compared == 168
    assert summary.values_compared == EXPECTED["values_compared"] == 1008
    assert summary.passed == EXPECTED["pass"] == 1006
    assert summary.review == EXPECTED["review"] == 2
    assert summary.pass_fraction > 0.998


def test_the_only_two_reviews_are_the_documented_rounding_ties():
    """Pinned by Mach number and column, so a new mismatch cannot hide."""
    summary = rc.compare_table(1.4, reference=TABLE)
    offenders = {
        (round(row.mach, 4), quantity.key)
        for row in summary.reviews
        for quantity in row.quantities
        if not quantity.passed
    }
    documented = {
        (round(tie["mach1"], 4), tie["column"])
        for tie in json.loads(rc.NORMAL_SHOCK_REFERENCE_PATH.read_text(encoding="utf-8"))[
            "print_rounding_ties"
        ]
    }
    assert offenders == documented == {(5.9, "p02_over_p01"), (6.9, "p02_over_p01")}


def test_the_rounding_ties_miss_by_a_hair_over_the_printed_precision():
    """Each REVIEW is barely outside tolerance -- the signature of a tie.

    A real physics defect would not land 1.001 half-units away; it would land
    somewhere arbitrary. Asserting the magnitude is what separates "the book
    rounded the other way" from "we are wrong".
    """
    summary = rc.compare_table(1.4, reference=TABLE)
    for row in summary.reviews:
        for quantity in row.quantities:
            if quantity.passed:
                continue
            half_units = abs(quantity.difference) / quantity.tolerance
            assert 1.0 < half_units < 1.01, (row.mach, quantity.key, half_units)


@pytest.mark.parametrize("mach1", ["5.9", "6.9"])
def test_an_independent_arbiter_sides_with_rocketforge_on_the_ties(mach1):
    """Settle the two ties with arithmetic that shares no code with the module.

    Exact rationals at gamma = 7/5 evaluated to 40 decimal digits. If this
    disagreed with ``normal_shock``, the ties would be our defect, not the
    book's rounding.
    """
    getcontext().prec = 40
    gamma = Fraction(7, 5)
    squared = Fraction(mach1) ** 2
    density = ((gamma + 1) * squared) / (2 + (gamma - 1) * squared)
    pressure = (gamma + 1) / (2 * gamma * squared - (gamma - 1))
    a = Decimal(density.numerator) / Decimal(density.denominator)
    b = Decimal(pressure.numerator) / Decimal(pressure.denominator)
    exact = (a.ln() * (Decimal(7) / Decimal(2)) + b.ln() * (Decimal(5) / Decimal(2))).exp()

    computed = float(ns.stagnation_pressure_ratio(float(mach1), GAS))
    assert computed == pytest.approx(float(exact), rel=1e-14)

    # ...and it lands just short of the boundary where the last digit rounds up.
    printed = TABLE.row_for(float(mach1))["p02_over_p01"]
    exponent = math.floor(math.log10(printed)) + 1
    half_unit = 0.5 * 10.0 ** (exponent - 4)
    boundary = printed - half_unit
    assert 0.0 < boundary - float(exact) < 1e-2 * half_unit


@pytest.mark.parametrize("mach1", [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0])
def test_named_reference_rows_value_by_value(mach1):
    """Spot rows an engineer would recognise, asserted one value at a time.

    The whole-table test above can only say "1006 passed"; this says which
    numbers, so a failure names the quantity rather than a count.
    """
    comparison = rc.compare_row(mach1, 1.4, TABLE)
    assert comparison is not None
    assert comparison.passed, [
        (q.key, q.computed, q.reference) for q in comparison.quantities if not q.passed
    ]
    for quantity in comparison.quantities:
        assert abs(quantity.difference) <= quantity.tolerance * (1.0 + 1e-9)


def test_the_classic_mach_two_row_matches_the_printed_values():
    """The row every gas-dynamics course works by hand."""
    row = TABLE.row_for(2.0)
    assert row["p2_over_p1"] == pytest.approx(4.500, abs=5e-4)
    assert row["rho2_over_rho1"] == pytest.approx(2.667, abs=5e-4)
    assert row["T2_over_T1"] == pytest.approx(1.687, abs=5e-4)
    assert row["p02_over_p01"] == pytest.approx(0.7209, abs=5e-5)
    assert row["p02_over_p1"] == pytest.approx(5.640, abs=5e-4)
    assert row["mach2"] == pytest.approx(0.5774, abs=5e-5)

    result = ns.solve(2.0, GAS)
    assert result.pressure_ratio == pytest.approx(4.5, rel=1e-12)
    assert result.density_ratio == pytest.approx(8.0 / 3.0, rel=1e-12)
    assert result.temperature_ratio == pytest.approx(1.6875, rel=1e-12)
    assert result.mach2 == pytest.approx(math.sqrt(1.0 / 3.0), rel=1e-12)


def test_no_interpolation_between_printed_rows():
    """A Mach number the book does not print has no reference value."""
    assert TABLE.row_for(2.005) is None
    assert rc.compare_row(2.005, 1.4, TABLE) is None


def test_a_different_gamma_is_not_compared_against_a_gamma_1_4_table():
    assert rc.compare_row(2.0, 1.3, TABLE) is None
    assert rc.compare_table(1.3, reference=TABLE).values_compared == 0


# ---------------------------------------------------------------------------
# the detector: a corrupted copy must be caught
# ---------------------------------------------------------------------------


def _fixture_copy(tmp_path: pathlib.Path) -> tuple[pathlib.Path, dict]:
    payload = json.loads(rc.NORMAL_SHOCK_REFERENCE_PATH.read_text(encoding="utf-8"))
    path = tmp_path / "perturbed_appendix_b.json"
    return path, payload


def test_a_perturbed_reference_value_is_detected(tmp_path):
    """Deliberately corrupt a *copy* and require the comparison to notice.

    A comparison that cannot fail proves nothing. The real dataset is never
    touched -- the last assertion checks that.
    """
    original_bytes = rc.NORMAL_SHOCK_REFERENCE_PATH.read_bytes()
    path, payload = _fixture_copy(tmp_path)

    for row in payload["rows"]:
        if abs(row["mach1"] - 3.0) < 1e-9:
            row["p2_over_p1"] = 10.50          # printed value is 10.33
            break
    else:                                       # pragma: no cover
        pytest.fail("M1 = 3 row not present")

    path.write_text(json.dumps(payload), encoding="utf-8")
    table = rc.load_reference.__wrapped__(str(path))     # bypass the cache

    comparison = rc.compare_row(3.0, 1.4, table)
    assert comparison is not None
    assert comparison.status == "REVIEW"
    offending = [q for q in comparison.quantities if not q.passed]
    assert [q.key for q in offending] == ["p2_over_p1"]
    assert offending[0].computed == pytest.approx(10.33333333, rel=1e-6)
    assert offending[0].reference == 10.50

    summary = rc.compare_table(1.4, reference=table)
    assert summary.review == 3          # the perturbation plus the two known ties
    assert not summary.all_passed

    assert rc.NORMAL_SHOCK_REFERENCE_PATH.read_bytes() == original_bytes


def test_a_perturbation_inside_the_printed_precision_is_not_flagged(tmp_path):
    """The detector must also not cry wolf.

    Moving a value by a third of the last printed digit is indistinguishable
    from the book's own rounding, and flagging it would make every REVIEW
    meaningless.
    """
    path, payload = _fixture_copy(tmp_path)
    for row in payload["rows"]:
        if abs(row["mach1"] - 3.0) < 1e-9:
            row["p2_over_p1"] = row["p2_over_p1"] + 0.003
            break
    path.write_text(json.dumps(payload), encoding="utf-8")
    table = rc.load_reference.__wrapped__(str(path))

    comparison = rc.compare_row(3.0, 1.4, table)
    assert comparison is not None and comparison.passed


def test_a_shifted_column_is_detected(tmp_path):
    """The failure mode that actually threatens a column-extracted table.

    One row losing a value shifts every later column left. That is the defect
    the Appendix A extraction nearly shipped, so it is asserted here.
    """
    path, payload = _fixture_copy(tmp_path)
    columns = ["p2_over_p1", "rho2_over_rho1", "T2_over_T1",
               "p02_over_p01", "p02_over_p1", "mach2"]
    for row in payload["rows"]:
        if abs(row["mach1"] - 4.0) < 1e-9:
            values = [row[c] for c in columns]
            for key, value in zip(columns, values[1:] + [values[0]]):
                row[key] = value
            break
    path.write_text(json.dumps(payload), encoding="utf-8")
    table = rc.load_reference.__wrapped__(str(path))

    comparison = rc.compare_row(4.0, 1.4, table)
    assert comparison is not None
    assert comparison.status == "REVIEW"
    assert sum(1 for q in comparison.quantities if not q.passed) >= 5


def test_a_file_declaring_an_unknown_dataset_is_refused(tmp_path):
    """No recipe means no way to recompute, and a table we cannot recompute
    is a lookup table -- exactly what this project forbids."""
    path, payload = _fixture_copy(tmp_path)
    payload["dataset"] = "some_table_we_have_no_recipe_for"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(KeyError, match="no"):
        rc.load_reference.__wrapped__(str(path))
