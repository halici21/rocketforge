"""The Reference Cases display (DB4C_IDEAL_REFERENCE_DISPLAY.md): the texts the page shows. No provider is needed.

The outcomes here are built from made-up numbers. What is pinned is how a
number becomes text -- its sign, its decimals, its operands, its kind -- and what
the page may never say. No computed reference value appears in this file.
"""

from __future__ import annotations

import re

import pytest

from rocketforge.application.analysis import reference_case_view as view
from rocketforge.application.analysis import reference_ideal_case as ideal
from rocketforge.application.analysis.reference_ideal_case import ReductionRow
from rocketforge.comparison import ObservedQuantity, compare
from rocketforge.comparison.ssme_tdk_1985 import CURRENT_DESIGN
from rocketforge.comparison.tdk_manual_1985 import ASE
from rocketforge.core.constants import STANDARD_GRAVITY

POINTS = ideal.POINTS
EACH_POINT = pytest.mark.parametrize("point", POINTS, ids=lambda p: p.case.case_id)
#: Words no displayed text may apply to a row (display review §2).
FORBIDDEN = ("error", "accuracy", "efficiency", "loss", "pass", "fail", "agree", "validated", "verified",
             "better", "worse", "score")
NUMBER = re.compile(r"[+−-]?\d+(?:\.\d+)?")


def made_up_comparison(point, scale: float):
    """The printout's own values, scaled: a run's shape with numbers nobody computed."""
    observed = {q.key: ObservedQuantity(q.key, q.value * scale, q.unit) for q in point.case.quantities}
    return compare(point.case, observed)


def made_up_step_b(rf_frozen=470.0, cea_frozen=458.0, rf_eq=501.0, cea_eq=485.0):
    return (ReductionRow("frozen", "frozen", rf_frozen, cea_frozen, rf_frozen / cea_frozen - 1.0,
                         "both in vacuum, p_a = 0", "model difference"),
            ReductionRow("equilibrium", "equilibrium", rf_eq, cea_eq, rf_eq / cea_eq - 1.0,
                         "both in vacuum, p_a = 0", "model difference"))


def numbers(text: str) -> list[float]:
    return [float(n.replace("−", "-")) for n in NUMBER.findall(text)]


# ------------------------------------------------------------------ the points and their documents


def test_the_documents_hold_exactly_the_runners_points_in_its_order():
    assert tuple(p for _, points in view.DOCUMENTS for p in points) == POINTS


def test_the_browser_shows_inputs_and_state_never_a_difference():
    rows = view.browser_rows(POINTS, ["not-run"] * 4)
    assert [r["pointKey"] for r in rows] == [p.case.case_id for p in POINTS]
    assert [r["sectionStart"] for r in rows] == [True, False, True, False]
    assert {r["pointStateWord"] for r in rows} == {"Not run"}
    assert rows[3]["inputsLine"] == "2287 psia · O/F 6.378 · area ratio 400.7148"
    assert rows[0]["pointName"] == "SSME current design at 109%"
    for row in view.browser_rows(POINTS, ["ok", "refused", "unavailable", "ok"]):
        text = " ".join(str(v) for k, v in row.items() if k != "pointName")   # a name may say "at 109%"
        assert "%" not in text and "−" not in text and "+" not in text


@EACH_POINT
def test_the_run_inputs_are_the_runners_own_and_never_rounded(point):
    rows = {r["inputLabel"]: r["inputText"] for r in view.run_input_rows(ideal.chamber_case(point), point)}
    assert rows["Fuel"] == "LH2, 20.27 K" and rows["Oxidiser"] == "LOX, 90.17 K"
    assert rows["Mixture ratio"] == f"O/F {point.oxidiser_fuel_ratio} by mass"
    assert rows["Area ratio"] == f"{point.area_ratio}, vacuum"
    assert rows["Chamber pressure"].startswith(f"{point.chamber_pressure_psia:g} psia (")


def test_a_pressure_in_pascals_is_grouped_not_rounded():
    rows = {r["inputLabel"]: r["inputText"] for r in view.run_input_rows(ideal.chamber_case(ASE), ASE)}
    pascals = ideal.chamber_case(ASE).chamber_pressure
    assert rows["Chamber pressure"] == f"2287 psia ({view._grouped(pascals, 3)} Pa)"
    assert view._grouped(15768309.9294, 3) == "15 768 309.929"


# ------------------------------------------------------------------ step A


def test_before_a_run_step_a_shows_the_printout_and_not_run_never_zero():
    rows = view.step_a_rows(CURRENT_DESIGN, None)
    assert [r["printed"] for r in rows] == ["3635.107 K (6543.192 R as printed)",
                                            "465.1311 s (lbf·s/lbm as printed)",
                                            "446.7661 s (lbf·s/lbm as printed)"]
    assert {r["computed"] for r in rows} == {view.NOT_RUN} == {r["difference"] for r in rows}
    assert {r["kind"] for r in rows} == {""}


@EACH_POINT
@pytest.mark.parametrize("scale", [0.99, 1.0, 1.003])
def test_step_a_texts_are_the_comparisons_values_at_the_printed_decimals(point, scale):
    comparison = made_up_comparison(point, scale)
    rows = view.step_a_rows(point, comparison)
    for quantity, source, row in zip(point.case.quantities, comparison.rows, rows, strict=True):
        factor = 1.0 if quantity.key == "chamber_temperature" else 1.0 / STANDARD_GRAVITY
        computed, *_ = numbers(row["computed"])
        absolute, relative = numbers(row["difference"])
        assert computed == round(source.observed * factor, quantity.decimals)
        assert absolute == pytest.approx(round(source.abs_diff * factor, quantity.decimals), abs=1e-12)
        assert relative == pytest.approx(round(source.rel_diff * 100.0, 3), abs=1e-12)
        assert row["kind"] == "compared"
        assert row["difference"][0] in "+−"


def test_a_changed_digit_is_seen_negative_control():
    """The parity check above can tell: a comparison one digit off yields different text."""
    base = view.step_a_rows(CURRENT_DESIGN, made_up_comparison(CURRENT_DESIGN, 1.001))
    nudged = view.step_a_rows(CURRENT_DESIGN, made_up_comparison(CURRENT_DESIGN, 1.001 + 1e-6))
    assert [r["computed"] for r in base] != [r["computed"] for r in nudged]


def test_a_difference_names_its_operands_and_carries_its_sign():
    assert view.STEP_A_HEADS[3] == "CEA − TDK"
    assert view.STEP_B_HEADS[3] == "RocketForge − CEA"
    assert view.signed(0.25, 4) == "+0.2500" and view.signed(-0.25, 4) == "−0.2500"
    rows = view.step_a_rows(CURRENT_DESIGN, made_up_comparison(CURRENT_DESIGN, 0.99))
    assert all(r["difference"].startswith("−") and "%" in r["difference"] for r in rows)


# ------------------------------------------------------------------ step B


def test_step_b_shows_both_bases_with_absolute_and_relative_differences():
    rows = view.step_b_rows(made_up_step_b())
    assert [r["basis"] for r in rows] == ["frozen", "equilibrium"]
    assert rows[0]["rocketforge"] == "470.0000 s"
    assert rows[0]["cea"] == "458.0000 s (frozen)" and rows[1]["cea"] == "485.0000 s (shifting equilibrium)"
    assert rows[0]["difference"] == f"+12.0000 s (+{(470.0 / 458.0 - 1.0) * 100:.3f} %)"
    assert {r["kind"] for r in rows} == {"model difference"}
    assert view.step_b_rows(()) == []


def test_a_relative_difference_that_was_not_formed_says_so():
    row = ReductionRow("frozen", "frozen", 1.0, 0.0, None, "both in vacuum, p_a = 0", "model difference")
    assert view.step_b_rows((row,))[0]["difference"].endswith(f"({view.NOT_FORMED})")


# ------------------------------------------------------------------ what the page may say


def test_no_displayed_text_judges_a_row():
    texts = [*view.STEP_A_HEADS, *view.STEP_B_HEADS, view.CLASS_LINE, *view.STATE_WORDS.values()]
    for point in POINTS:
        texts += [v for r in view.step_a_rows(point, made_up_comparison(point, 1.01)) for v in r.values()]
        texts += [v for r in view.browser_rows(POINTS, ["ok"] * 4) for v in map(str, r.values())]
    texts += [v for r in view.step_b_rows(made_up_step_b()) for v in r.values()]
    joined = " ".join(texts).lower()
    for word in FORBIDDEN:
        assert re.search(rf"\b{word}", joined) is None, word
    # The step notes name what a difference is *not*; that is their job, and the only place "error" may appear.
    assert "not an error" in view.STEP_B_NOTE and "never a RocketForge defect" in view.STEP_A_NOTE


def test_warnings_are_verbatim_none_after_a_clean_run_and_absent_before_one():
    assert view.warning_lines(None) == []
    assert view.warning_lines(()) == [{"line": "none"}]
    assert view.warning_lines(("a", "b")) == [{"line": "a"}, {"line": "b"}]


def test_a_stop_names_its_kind_and_reason():
    assert view.stop_line("refused", "chamber: no") == "Refused: chamber: no"
    assert view.stop_line("unavailable", "CEA frozen expansion: x") == "Unavailable: CEA frozen expansion: x"


def test_the_view_imports_no_qt_and_no_provider():
    import inspect
    source = inspect.getsource(view)
    for name in ("PySide6", "rocketforge.providers", "thermochemistry_provider", "performance_oracle"):
        assert name not in source, name
