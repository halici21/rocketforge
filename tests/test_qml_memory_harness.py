"""Rules for the memory harness, because three of them lied to this project.

1. The visual pilot's probe read through psapi, returned a flat zero, and
   reported a clean 0.000 MB for a loop retaining hundreds of megabytes.
2. That same benchmark leaked seven page instances from its page-creation
   measurement into its memory measurement, inflating the figure roughly 10x.
3. Every harness, including this program's first version, drove Qt with
   processEvents() alone -- which never dispatches DeferredDelete, so no
   deleteLater() ever completed. That produced the entire reported defect.

The four allocator controls passed while (3) was broken. These rules exist so
that cannot happen quietly again.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ACCEPTANCE = ROOT / "acceptance" / "qml_memory"


def harness():
    path = ROOT / "experiments" / "qml_memory" / "harness.py"
    spec = importlib.util.spec_from_file_location("qml_harness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_probe_reports_two_independent_metrics():
    reading = harness().memory()
    assert reading["private_mb"] > 0
    assert reading["working_set_mb"] > 0


def test_the_probe_raises_rather_than_returning_zero():
    """The predecessor's failure mode was a silent 0.0, which reads as "no
    memory" and is indistinguishable from "no leak"."""
    import inspect

    source = inspect.getsource(harness().memory)
    assert "raise OSError" in source
    assert "return 0" not in source


def test_the_probe_sees_a_deliberate_allocation():
    result = harness().control_a_known_allocation(mb=20)
    assert result["seen"]["private_mb"] >= 16, result


def test_the_probe_measures_a_known_leak_slope():
    result = harness().control_c_intentional_leak(rounds=4, mb=4)
    assert result["pass"], result


def test_settle_dispatches_deferred_deletion():
    """The one control that would have caught the defect that wasn't."""
    import inspect

    source = inspect.getsource(harness().settle)
    assert "DeferredDelete" in source
    assert "sendPostedEvents" in source


def test_the_object_lifecycle_control_demonstrates_the_trap():
    from PySide6.QtCore import QCoreApplication
    import sys

    app = QCoreApplication.instance() or QCoreApplication(sys.argv[:1])
    result = harness().control_e_object_lifecycle(app)
    assert result["pass"], result
    # the point of the control: processEvents() alone leaves them all alive
    assert result["alive_before_dispatch"] == result["created_and_deleted"]
    assert result["alive_after_dispatch"] == 0


def test_every_measurement_script_dispatches_deferred_deletion():
    """A script that turns the event loop without completing deletions will
    report Qt's correct destruction as a leak."""
    scripts = ("measure.py", "soak.py", "isolate.py", "minimal_reproducer.py")
    for name in scripts:
        text = (ROOT / "experiments" / "qml_memory" / name).read_text(
            encoding="utf-8")
        assert ("DeferredDelete" in text or "settle as _settle" in text), name


def test_the_recorded_calibration_passed_all_five_controls():
    report = json.loads((ACCEPTANCE / "harness_calibration.json").read_text(
        encoding="utf-8"))
    assert report["verdict"] == "PASS"
    for key in ("control_a_known_allocation", "control_b_released_allocation",
                "control_c_intentional_leak", "control_e_object_lifecycle"):
        assert report[key]["pass"], key


def test_the_acceptance_criterion_was_registered_before_the_result():
    criterion = json.loads((ACCEPTANCE / "acceptance_criterion.json").read_text(
        encoding="utf-8"))
    assert criterion["registered_before_any_fix_measurement"] is True
    assert {c["id"] for c in criterion["criteria"]} == {
        "C1_plateau_slope", "C2_bounded_total", "C3_sublinear", "C4_no_masking"}


def test_the_root_cause_record_states_the_artifact():
    """The reported defect was a measurement artifact. The record must say so
    rather than claim a leak was fixed."""
    record = json.loads((ACCEPTANCE / "root_cause.json").read_text(
        encoding="utf-8"))
    assert "ARTIFACT" in record["verdict"].upper()
    assert record["change_kept"]["not_claimed"]
    assert record["open_finding"]["root_cause"] == "NOT ESTABLISHED"


def test_recalculation_is_bounded_on_both_trees():
    for label in ("baseline", "current"):
        report = json.loads((ACCEPTANCE / f"final_1000_{label}.json").read_text(
            encoding="utf-8"))
        series = [row["private_mb"] for row in report["series"]]
        half = len(series) // 2
        second = series[-1] - series[half - 1]
        assert second <= max(series[half - 1], 1.0), (label, second)


def test_the_row_models_lowered_the_plateau():
    before = json.loads((ACCEPTANCE / "final_1000_baseline.json").read_text(
        encoding="utf-8"))["private_total_mb"]
    after = json.loads((ACCEPTANCE / "final_1000_current.json").read_text(
        encoding="utf-8"))["private_total_mb"]
    assert after < before, (after, before)


@pytest.mark.parametrize("mode", ["lifecycle", "session"])
def test_the_soaks_retain_no_page_instances(mode):
    report = json.loads((ACCEPTANCE / f"soak_{mode}.json").read_text(
        encoding="utf-8"))
    assert report["page_instance_delta"] == 0, report["page_instance_series"]
    assert report["canonical_result_unchanged"] is True
    assert report["qt_warnings"] == []
