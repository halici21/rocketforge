"""Section 6: prove the harness can still tell memory apart, before it is
used to judge production code.

Four controls, each with a known answer. If any fails, the harness is fixed
before anything is diagnosed -- an untrusted meter cannot clear or convict.
"""
from __future__ import annotations
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "qml_memory"))
OUT = ROOT / "acceptance" / "analysis_r2_closure" / "memory"

from PySide6.QtGui import QGuiApplication
from harness import (control_a_known_allocation, control_b_released_allocation,
                     control_c_intentional_leak, control_d_no_op_noise,
                     control_e_object_lifecycle)

app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])

a = control_a_known_allocation()
b = control_b_released_allocation()
c = control_c_intentional_leak()
d = control_d_no_op_noise(app)
e = control_e_object_lifecycle(app)

report = {
    "control_a_known_allocation": {
        "expects": "memory grows by the amount allocated",
        "allocated_mb": a["allocated_mb"],
        "observed_private_mb": a["seen"]["private_mb"], "pass": a["pass"]},
    "control_b_released_allocation": {
        "expects": "memory stabilises after release",
        "retained_private_mb": b["retained"]["private_mb"], "pass": b["pass"]},
    "control_c_intentional_leak": {
        "expects": "a known retained allocation produces its own slope",
        "leaked_per_round_mb": c["leaked_per_round_mb"],
        "measured_slope_mb_per_round": c["measured_slope_mb_per_round"],
        "pass": c["pass"]},
    "control_d_no_op_noise": {
        "expects": "doing nothing does not report linear growth",
        "slope_mb_per_round": d["slope_mb_per_round"],
        "peak_to_peak_mb": d["peak_to_peak_mb"],
        "pass": abs(d["slope_mb_per_round"]) < 0.05},
    "control_e_object_lifecycle": {
        "expects": "destroyed QObjects actually die once DeferredDelete runs",
        "alive_before_dispatch": e["alive_before_dispatch"],
        "alive_after_dispatch": e["alive_after_dispatch"], "pass": e["pass"]},
}
report["verdict"] = ("PASS" if all(v["pass"] for v in report.values()
                                   if isinstance(v, dict)) else "FAIL")

for name, v in report.items():
    if name == "verdict":
        continue
    detail = {k: x for k, x in v.items() if k not in ("expects", "pass")}
    print("  %-28s pass=%-5s  %s" % (name.replace("control_", ""),
                                     v["pass"], detail))
print("HARNESS VERDICT:", report["verdict"])

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "harness_validation.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8")
sys.exit(0 if report["verdict"] == "PASS" else 1)
