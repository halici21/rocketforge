"""A packaged diagnostic for the Line workspace.

Answers what a capture cannot: does the *packaged* build solve a real line from
a real validated fluid state, or does it merely render a page?

    RocketForge.exe --selftest-line [output directory]

It drives the real controller through the same slots the interface's own
controls call. No synthetic desktop input.
"""

from __future__ import annotations

import json
import sys

__all__ = ["LINE_SMOKE_FLAG", "run_line_smoke"]

LINE_SMOKE_FLAG = "--selftest-line"

#: The cases the tour runs. Chosen so it exercises a turbulent solve, a laminar
#: solve, the transition refusal, and the transport-envelope gate.
TOUR = (
    ("turbulent", dict(temperature=111.643, pressure=1.0e6, mass_flow=2.0,
                       length=5.0, inner_diameter=0.02,
                       absolute_roughness=1.5e-6)),
    ("laminar", dict(temperature=111.643, pressure=1.0e6, mass_flow=0.001,
                     length=1.0, inner_diameter=0.01,
                     absolute_roughness=0.0)),
    ("transitional", dict(temperature=111.643, pressure=1.0e6,
                          mass_flow=0.0028, length=1.0, inner_diameter=0.01,
                          absolute_roughness=0.0)),
    ("outside transport envelope",
     dict(temperature=130.0, pressure=1.0e6, mass_flow=2.0, length=5.0,
          inner_diameter=0.02, absolute_roughness=1.5e-6)),
)


def run_line_smoke(argv, configure, build_engine, ui_dir) -> int:
    """Solve real lines through the real controller and report."""
    import pathlib

    directory = pathlib.Path(argv[0]) if argv else pathlib.Path("line_smoke")
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / "line_smoke.json"

    from rocketforge.application.analysis.line_controller import LineController

    controller = LineController()
    report: dict = {
        "status": "ok",
        "frozen": bool(getattr(sys, "frozen", False)),
        "python": sys.version.split()[0],
        "provider_available": bool(controller.providerAvailable),
        "provider_label": controller.providerLabel,
        "cases": [],
    }

    for label, case in TOUR:
        controller.setFluid("METHANE")
        controller.setTemperature(case["temperature"])
        controller.setPressure(case["pressure"])
        controller.setMassFlow(case["mass_flow"])
        controller.setLength(case["length"])
        controller.setInnerDiameter(case["inner_diameter"])
        controller.setAbsoluteRoughness(case["absolute_roughness"])
        controller.calculate()
        rows = {row["label"]: row["value"]
                for row in controller.resultRows}
        report["cases"].append({
            "case": label,
            "inputs": case,
            "status": controller.statusLabel,
            "regime": controller.flowRegime,
            "transport_validated": bool(controller.transportValidated),
            "transport_note": controller.transportNote,
            "has_result": bool(controller.hasResult),
            "message": controller.message,
            "rows": rows,
            "provenance": [dict(row) for row in controller.provenanceRows],
        })

    by_case = {entry["case"]: entry for entry in report["cases"]}

    turbulent = by_case["turbulent"]
    report["solved_a_real_turbulent_line"] = bool(
        turbulent["has_result"] and turbulent["regime"] == "Turbulent"
        and turbulent["transport_validated"]
        and turbulent["rows"].get("Darcy friction factor  f_D") not in (None, "—"))
    report["solved_a_real_laminar_line"] = bool(
        by_case["laminar"]["has_result"]
        and by_case["laminar"]["regime"] == "Laminar")
    report["transition_withholds_the_friction_factor"] = (
        by_case["transitional"]["rows"].get("Darcy friction factor  f_D") == "—")
    report["envelope_gate_refused_the_outside_state"] = (
        not by_case["outside transport envelope"]["has_result"])

    ok = (report["solved_a_real_turbulent_line"]
          and report["solved_a_real_laminar_line"]
          and report["transition_withholds_the_friction_factor"]
          and report["envelope_gate_refused_the_outside_state"])
    report["status"] = "ok" if ok else "failed"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[line-smoke] turbulent solved: "
          f"{report['solved_a_real_turbulent_line']}, laminar solved: "
          f"{report['solved_a_real_laminar_line']}, transition withheld: "
          f"{report['transition_withholds_the_friction_factor']}, envelope "
          f"gate: {report['envelope_gate_refused_the_outside_state']} "
          f"-> {report_path}")
    return 0 if ok else 2
