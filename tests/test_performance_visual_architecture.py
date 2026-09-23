"""Static rules for the Rocket Performance visual pilot.

The redesign moved a great deal of presentation into QML. These rules exist to
be sure it moved *only* presentation.
"""

from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
UI = ROOT / "ui"
PAGE_DIR = UI / "pages" / "rocketperformance"
PAGE = UI / "pages" / "RocketPerformancePage.qml"

#: Measurements and captures recorded on a developer machine by the pilot's own
#: harnesses (experiments/ui_visual_pilot/). They are evidence about that
#: machine, not contracts, so they stay in the untracked acceptance/ folder. A
#: fresh clone and CI do not have them: the tests that read them skip with that
#: reason, and every other test in this file still runs everywhere.
EVIDENCE = ROOT / "acceptance" / "ui_visual_pilot"


def local_evidence(name: str) -> pathlib.Path:
    path = EVIDENCE / name
    if not path.exists():
        pytest.skip(f"local evidence acceptance/ui_visual_pilot/{name} is not present: "
                    "recorded on a developer machine by experiments/ui_visual_pilot/ "
                    "and deliberately not tracked")
    return path


def performance_qml():
    files = [PAGE] if PAGE.is_file() else []
    files.extend(sorted(PAGE_DIR.glob("*.qml")))
    return files


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"//.*", "", text)


def test_the_comment_stripper_drops_prose_and_keeps_code():
    assert "gamma" not in strip_comments("// mentions gamma\nx = 1")
    assert "gamma" in strip_comments("var g = gamma * 2")


# --- no physics in QML ----------------------------------------------------
#
# The pilot added a Canvas. A canvas is allowed presentation geometry -- pixels,
# radii, bezier control points -- and nothing else. These names would only
# appear if a physical relation had been reimplemented in the view.

FORBIDDEN_PHYSICS = (
    "characteristic_velocity", "thrustCoefficient =", "specificImpulse =",
    "massFlow =", "areaMach", "pressureRatio =", "gammaRelation",
    "Math.pow(gamma", "/ g0", "9.80665", "8314", "vandenkerckhove",
)


@pytest.mark.parametrize("path", performance_qml(), ids=lambda p: p.name)
def test_no_performance_qml_implements_a_physical_relation(path):
    text = strip_comments(path.read_text(encoding="utf-8"))
    found = [token for token in FORBIDDEN_PHYSICS if token in text]
    assert not found, f"{path.name} contains {found}"


def test_the_physics_scan_would_catch_a_reimplementation():
    snippet = "var isp = ceff / 9.80665"
    assert [t for t in FORBIDDEN_PHYSICS if t in snippet]


def test_the_canvas_takes_no_root_of_its_own():
    """The canvas divides by a radius ratio it is handed; it derives nothing.

    An earlier draft computed ``exitR / Math.sqrt(ratio)`` in QML. The Phase 5E
    rule that the interface performs only layout arithmetic caught it, and the
    right answer was to publish r_e/r_t from the controller rather than to
    widen the rule.
    """
    text = strip_comments((PAGE_DIR / "PerfNozzleCanvas.qml").read_text(
        encoding="utf-8"))
    assert "Math.sqrt" not in text
    assert "root.drawnRatio" in text


def test_the_canvas_states_that_it_is_a_schematic():
    """The drawing must not imply a solved contour it does not have."""
    text = (PAGE_DIR / "PerfNozzleCanvas.qml").read_text(encoding="utf-8")
    assert "SCHEMATIC" in text
    assert "NOT A SOLVED CONTOUR" in text


@pytest.mark.parametrize("term", ["Rao", "bell contour", "half-angle",
                                  "conical angle", "Mach distribution",
                                  "pressure field", "contour solved"])
def test_the_canvas_claims_no_geometry_it_has_not_solved(term):
    """Comments are stripped first, and that is the point.

    The canvas docstring says RocketForge "has not solved a bell, a Rao
    profile, a cone half-angle". The first version of this rule flagged that
    disclaimer -- the same substring trap this project keeps meeting. What the
    rule is for is a *claim rendered on screen*, so it reads the code.
    """
    for path in performance_qml():
        assert term not in strip_comments(path.read_text(encoding="utf-8"))


def test_the_geometry_claim_scan_separates_a_claim_from_a_disclaimer():
    disclaimer = "// not a Rao profile\nx = 1"
    assert "Rao" not in strip_comments(disclaimer)
    assert "Rao" in strip_comments('text: "Rao contour"')


# --- the visual reads the solved snapshot, never the live inputs ----------

def test_the_canvas_is_driven_by_the_solved_snapshot():
    """Binding the drawing to the live input would animate the nozzle to a
    shape nobody has solved while the numbers still showed the old result."""
    text = (PAGE_DIR / "PerfCalculator.qml").read_text(encoding="utf-8")
    assert "radiusRatio: RocketPerformance.solvedRadiusRatio" in text
    assert "radiusRatio: RocketPerformance.areaRatio" not in text


def test_the_canvas_knows_when_the_result_is_stale():
    text = (PAGE_DIR / "PerfCalculator.qml").read_text(encoding="utf-8")
    assert "stale: RocketPerformance.resultStale" in text


# --- meaning is not carried by colour alone ------------------------------

def test_the_pressure_sign_is_carried_by_words_not_a_hue():
    """The relation is composed in the controller and rendered as text.

    Written as a literal in QML first; the Phase 5E rule against hard-coding a
    reference condition in the interface caught it, correctly.
    """
    from rocketforge.application.analysis.performance_controller import (
        RocketPerformanceController,
    )

    assert hasattr(RocketPerformanceController, "pressureRelationText")
    text = (PAGE_DIR / "PerfPressureRelation.qml").read_text(encoding="utf-8")
    assert "text: root.relationText" in text


def test_the_regime_is_stated_in_words():
    text = (PAGE_DIR / "PerfPressureRelation.qml").read_text(encoding="utf-8")
    assert "root.regimeLabel" in text


def test_stale_state_is_announced_in_text():
    text = (PAGE_DIR / "PerfCalculator.qml").read_text(encoding="utf-8")
    assert "Stale — recalculate" in text


def test_a_superseded_chamber_is_announced_in_text():
    text = (PAGE_DIR / "PerfCalculator.qml").read_text(encoding="utf-8")
    assert "Superseded chamber" in text


# --- the canvas must not animate while nothing is happening --------------

def test_the_canvas_has_no_timer_and_no_idle_animation():
    text = strip_comments((PAGE_DIR / "PerfNozzleCanvas.qml").read_text(
        encoding="utf-8"))
    assert "Timer" not in text
    assert "running: true" not in text
    assert "loops: Animation.Infinite" not in text


def test_the_canvas_repaints_only_on_change():
    text = (PAGE_DIR / "PerfNozzleCanvas.qml").read_text(encoding="utf-8")
    assert "requestPaint()" in text
    assert "onDrawnRatioChanged" in text


# --- the pilot stayed a pilot --------------------------------------------

def test_no_other_workspace_page_was_restyled_by_this_pilot():
    """The new primitives are local to the performance workspace."""
    local = {"PerfNozzleCanvas", "PerfMetricReadout", "PerfStationLabel",
             "PerfBreakdown", "PerfPressureRelation"}
    for path in (UI / "pages").rglob("*.qml"):
        if path.parent.name == "rocketperformance":
            continue
        text = path.read_text(encoding="utf-8")
        used = {name for name in local if name + " {" in text}
        assert not used, f"{path.name} uses pilot-local {sorted(used)}"


def test_the_pilot_added_no_image_or_font_asset():
    """The centrepiece is native vector geometry, not stock art."""
    for pattern in ("*.png", "*.jpg", "*.jpeg", "*.svg", "*.ttf", "*.otf",
                    "*.gif", "*.mp4"):
        assert not list(PAGE_DIR.glob(pattern))


# --- the drawing derivation, tested where it lives ------------------------

def test_the_radius_ratio_is_the_square_root_of_the_area_ratio():
    from rocketforge.application.analysis.performance_visual import (
        radius_ratio_for_drawing,
    )

    assert radius_ratio_for_drawing(1.0) == 1.0
    assert radius_ratio_for_drawing(4.0) == 2.0
    assert radius_ratio_for_drawing(100.0) == 10.0


def test_the_radius_ratio_draws_nothing_rather_than_raising():
    """Its caller is a paint routine; an unusable value must not interrupt a
    render."""
    from rocketforge.application.analysis.performance_visual import (
        radius_ratio_for_drawing,
    )

    for bad in (0.0, -1.0, float("nan"), float("inf"), None, "x"):
        assert radius_ratio_for_drawing(bad) == 0.0


def test_the_drawing_helper_reaches_no_result():
    """It sizes a picture. It must not appear in the scientific path."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent / "rocketforge"
    users = []
    for path in root.rglob("*.py"):
        if path.name == "performance_visual.py":
            continue
        if "radius_ratio_for_drawing" in path.read_text(encoding="utf-8"):
            users.append(path.relative_to(root).as_posix())
    assert users == ["application/analysis/performance_controller.py"], users


# --- the unsolved outline cannot be mistaken for a solved one -------------

def test_the_placeholder_outline_is_internal_and_arbitrary():
    """The empty state draws a nozzle, and nothing has been solved.

    So the proportion it draws is invented. It is kept inside the canvas and
    made unreachable from outside, rather than passed in on ``radiusRatio`` --
    the property that otherwise only ever carries a solved result.
    """
    text = strip_comments((PAGE_DIR / "PerfNozzleCanvas.qml").read_text(
        encoding="utf-8"))
    assert "property bool placeholder: false" in text
    assert "readonly property real placeholderRatio" in text


def test_only_the_solved_canvas_is_ever_handed_a_ratio():
    page = strip_comments((PAGE_DIR / "PerfCalculator.qml").read_text(
        encoding="utf-8"))
    assigned = [m.strip() for m in re.findall(r"radiusRatio:\s*(\S+)", page)]
    assert assigned == ["RocketPerformance.solvedRadiusRatio"], assigned


def test_the_ratio_scan_would_catch_an_invented_one():
    snippet = "PerfNozzleCanvas { radiusRatio: 6.3 }"
    assert [m for m in re.findall(r"radiusRatio:\s*(\S+)", snippet)] == ["6.3"]


def test_the_placeholder_outline_carries_no_annotation():
    """It is a shape, not a reading. Station labels and their values are all
    gated on a real result."""
    text = (PAGE_DIR / "PerfNozzleCanvas.qml").read_text(encoding="utf-8")
    for block in re.findall(r"PerfStationLabel \{(.*?)\n        \}", text,
                            flags=re.DOTALL):
        assert "visible: root.hasResult" in block


def test_the_placeholder_does_not_borrow_the_solved_label():
    """The solved drawing says it shows an area expansion. The placeholder's
    expansion is invented, so it must not make that claim."""
    text = (PAGE_DIR / "PerfNozzleCanvas.qml").read_text(encoding="utf-8")
    assert "UNSOLVED OUTLINE" in text
    assert "NOT AN AREA RATIO" in text
    label = text[text.index("root.placeholder\n              ?"):]
    assert label.index("UNSOLVED OUTLINE") < label.index("SCHEMATIC")


# --- the hero is labelled by the result, never by the live form -----------

def test_the_canvas_header_states_the_result_not_the_inputs():
    """``caseHeadline`` is documented as what the inputs describe. Above a
    drawing of a solved expansion it would relabel the result: at epsilon 60
    typed but 40 solved, the header read 'Ae/At 60' over an Ae/At 40 nozzle."""
    page = strip_comments((PAGE_DIR / "PerfCalculator.qml").read_text(
        encoding="utf-8"))
    assert "RocketPerformance.resultHeadline" in page
    assert "RocketPerformance.caseHeadline" not in page


def test_the_canvas_chamber_label_comes_from_the_solved_chamber():
    page = strip_comments((PAGE_DIR / "PerfCalculator.qml").read_text(
        encoding="utf-8"))
    assert "chamberPressureText: RocketPerformance.solvedChamberPressureText" \
        in page
    # The rail may still show the LIVE chamber -- that is what it is
    # for. What the drawing may not do is take a label apart with string
    # surgery: the first version sliced chamberHeadline in QML and
    # printed "p_c p_c 100 bar".
    for path in performance_qml():
        assert ".split(" not in strip_comments(
            path.read_text(encoding="utf-8")), path.name


def test_the_solved_chamber_label_agrees_with_the_shared_headline():
    """It is a slice of the one headline the rest of the application shows, so
    a change to that format cannot make the two disagree silently."""
    from rocketforge.application.analysis.thermochemistry_service import (
        DEFAULT_CASE,
        case_headline,
    )

    tail = case_headline(DEFAULT_CASE).split("·")[-1].strip()
    assert tail == "p_c 100 bar", case_headline(DEFAULT_CASE)


def test_the_pilot_left_no_orphaned_component_behind():
    """The redesign replaced PerfResultHeader and PerfResultGroup and at first
    simply stopped using them, leaving two dead files in the directory. A
    workspace component that nothing instantiates is not neutral: it is the
    next reader's wrong answer about how this page is built."""
    used = set()
    for path in (UI / "pages").rglob("*.qml"):
        text = strip_comments(path.read_text(encoding="utf-8"))
        for candidate in PAGE_DIR.glob("*.qml"):
            if candidate.stem + " {" in text:
                used.add(candidate.stem)
    on_disk = {path.stem for path in PAGE_DIR.glob("*.qml")}
    orphans = on_disk - used - {"PerfCalculator"}
    assert not orphans, f"instantiated nowhere: {sorted(orphans)}"


def test_the_orphan_scan_can_tell_used_from_unused():
    assert "PerfNozzleCanvas {" in strip_comments(
        (PAGE_DIR / "PerfCalculator.qml").read_text(encoding="utf-8"))
    assert "PerfResultGroup" not in strip_comments(
        (PAGE_DIR / "PerfCalculator.qml").read_text(encoding="utf-8"))


def test_a_rail_that_overflows_shows_that_it_overflows():
    """The shared scrollbar is invisible at rest, so at 1366x768 nothing said
    Ambient and Engine size were below the fold. The cue is switched on by the
    overflow itself, never left on: a bar that is always there is chrome."""
    text = strip_comments((PAGE_DIR / "PerfCalculator.qml").read_text(
        encoding="utf-8"))
    for rail in ("inputRail", "resultRail"):
        assert (f"policy: {rail}.contentHeight > {rail}.height") in text, rail
    assert text.count("ScrollBar.AlwaysOn : ScrollBar.AsNeeded") == 2


def test_the_overflow_cue_changed_no_shared_component():
    """It is a property override on the instance. RFScrollBar itself is used by
    every workspace and was not touched."""
    shared = (UI / "components" / "RFScrollBar.qml").read_text(encoding="utf-8")
    assert "policy: ScrollBar.AsNeeded" in shared
    assert "Perf" not in shared


# --- the parity check itself, put under a negative control ----------------

def _parity_module():
    import importlib.util

    path = ROOT / "experiments" / "ui_visual_pilot" / "scientific_parity.py"
    spec = importlib.util.spec_from_file_location("scientific_parity", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_parity_check_reaches_the_values_a_reader_actually_sees():
    """Comparing the nested snapshots whole is just as strict, but it would
    report only that 'resultGroups differs'. This one names the row."""
    leaves = _parity_module().leaves
    state = {"resultGroups": [{"rows": [{"value": "348.658"}]}], "ok": True}
    flat = dict(leaves(state, "state"))
    assert flat["state.resultGroups[0].rows[0].value"] == "348.658"
    assert flat["state.ok"] is True
    assert flat["state.resultGroups.length"] == 1


def test_the_parity_check_would_notice_a_changed_number():
    """A comparison nobody has seen fail is not evidence."""
    leaves = _parity_module().leaves
    before = dict(leaves({"rows": [{"value": "348.658"}]}, "s"))
    after = dict(leaves({"rows": [{"value": "348.659"}]}, "s"))
    assert before != after
    changed = [k for k in before if before[k] != after.get(k)]
    assert changed == ["s.rows[0].value"]


def test_the_parity_check_would_notice_a_dropped_row():
    leaves = _parity_module().leaves
    before = dict(leaves({"rows": [{"v": 1}, {"v": 2}]}, "s"))
    after = dict(leaves({"rows": [{"v": 1}]}, "s"))
    assert before["s.rows.length"] != after["s.rows.length"]
    assert "s.rows[1].v" in before and "s.rows[1].v" not in after


def test_the_parity_result_on_record_is_a_pass_over_real_captures():
    import json

    report = json.loads(local_evidence("scientific_parity.json").read_text(
                             encoding="utf-8"))
    assert report["verdict"] == "PASS"
    assert report["differences"] == []
    assert report["captures_compared"] == 27
    assert report["fields_compared"] > 5000
    assert report["chemistry_solves_after"] == report[
        "chemistry_solves_before"]


# --- accessibility decisions, pinned where they were made -----------------

def test_the_honesty_label_is_readable():
    """It was drawn in textDisabled, which measures 2.43:1 against the page.
    The one label that stops the drawing being read as a solved contour is not
    allowed to be the least readable text on screen."""
    text = (PAGE_DIR / "PerfNozzleCanvas.qml").read_text(encoding="utf-8")
    label = text[text.index("NOT A SOLVED CONTOUR"):]
    assert "color: Theme.textSecondary" in label[:400]


def test_no_pilot_component_puts_meaning_in_the_dimmest_token():
    """textDisabled is 2.43:1 (dark) and 2.19:1 (light). Nothing a reader has
    to read may be drawn in it."""
    added = ("PerfNozzleCanvas", "PerfMetricReadout", "PerfStationLabel",
             "PerfBreakdown", "PerfPressureRelation")
    for name in added:
        text = strip_comments((PAGE_DIR / f"{name}.qml").read_text(
            encoding="utf-8"))
        assert "Theme.textDisabled" not in text, name


def test_a_stale_value_is_still_a_readable_value():
    """It is the last result that was actually solved, so it is dimmed rather
    than hidden -- and staleness is carried by the chip and the header, not by
    making the number illegible."""
    text = strip_comments((PAGE_DIR / "PerfMetricReadout.qml").read_text(
        encoding="utf-8"))
    assert "root.stale ? Theme.textMuted" in text


def test_the_accessibility_result_on_record_is_clean_for_the_pilot():
    import json

    report = json.loads(local_evidence("accessibility.json").read_text(encoding="utf-8"))
    assert report["pilot_owned_failures"] == []
    assert report["pilot_scope_verdict"] == "PASS"
    # every remaining shortfall is the one shared token, and it is on record
    assert report["shared_theme_findings"]
    assert all("textMuted on background" in f
               for f in report["shared_theme_findings"])
    for label, ok in report["not_colour_only"].items():
        assert ok, label
    for label, ok in report["keyboard"]["required"].items():
        assert ok, label
    assert report["keyboard"]["distinct_stops"] > 20


# --- what the redesign costs at runtime -----------------------------------

def _perf(label: str) -> dict:
    import json

    path = local_evidence(f"performance_{label}.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_the_workspace_still_opens_and_publishes_cheaply():
    results = _perf("after")["results"]
    budgets = _perf("after")["budgets"]
    for name, budget in budgets.items():
        assert results[name] <= budget, f"{name} {results[name]} > {budget}"


def test_the_canvas_costs_nothing_while_nothing_happens():
    """A canvas with an idle animation would show up here as CPU spent on an
    unchanging picture."""
    assert _perf("after")["results"]["idle_ms_per_second"] < 60.0


def test_the_memory_probe_was_proven_before_it_was_trusted():
    """It first read through psapi, returned a flat zero, and reported a clean
    0.000 MB for a loop that actually retained hundreds. A leak check that
    cannot see a deliberate 40 MB is not evidence of anything."""
    for label in ("before", "after"):
        assert _perf(label)["results"]["memory_probe_saw_mb"] > 20.0


def test_the_redesign_retains_less_than_the_design_it_replaced():
    """Repeated recalculation retains memory in the QML layer on both designs.
    It is pre-existing and recorded as a finding; what the pilot owes is not
    making it worse."""
    regression = _perf("after")["memory_regression"]
    assert regression["pass"], regression
    assert regression["after_mb"] < regression["before_mb"]


def test_the_redesign_publishes_a_result_faster_than_the_old_one():
    before = _perf("before")["results"]["solved_publication_ms"]
    after = _perf("after")["results"]["solved_publication_ms"]
    assert after < before, (after, before)


# --- the packaged workspace shows what the source one shows ---------------

def test_the_packaged_workspace_matches_the_source_build():
    import json

    report = json.loads(local_evidence("source_packaged_parity.json").read_text(
                             encoding="utf-8"))
    assert report["verdict"] == "PASS"
    assert report["differences"] == []
    assert report["captures_source"] == report["captures_frozen"]
    assert report["fields_compared"] > 5000
    assert report["qt_warnings_frozen"] == 0
    assert report["chamber_solves_source"] == report["chamber_solves_frozen"]


def test_the_before_baseline_is_marked_unreproducible():
    """Its UI tree was destroyed by the clean rebuild. The measurement stands
    as a record; saying it could be re-derived would be false."""
    import json

    report = json.loads(local_evidence("performance_before.json").read_text(
                             encoding="utf-8"))
    assert report["reproducible"] is False
    assert "cannot be regenerated" in report["provenance"].lower()


def test_the_scientific_baseline_survived_that_rebuild():
    """The captures the parity claim rests on survived the clean rebuild: they
    live in the local acceptance/ evidence, not in dist/, so the rebuild could
    not touch them. They are not tracked; see local_evidence()."""
    before = local_evidence("before")
    assert (before / "capture_matrix.json").is_file()
    assert len(list(before.glob("*.png"))) == 27
