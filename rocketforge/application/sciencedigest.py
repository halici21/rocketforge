"""A bit-exact digest of what RocketForge computes, for source/package parity.

``RocketForge.exe --selftest-science <out.json>`` in a packaged build and
``python main.py --selftest-science <out.json>`` from source run the same
representative cases through the same controllers the interface uses, and
write every published property with each float stored exactly (``float.hex``).
Two digests from the same commit must be identical, byte for byte, apart from
the ``build`` header, which says which build wrote the file.

Cases, one canonical case per workspace:

    compressible     the classic relations' tables and the nozzle back-pressure
                     sweep, at three gamma values
    thermochemistry  the validated LOX/LCH4 case, a mixture-ratio sweep, and the
                     bipropellant -> solid -> bipropellant round trip
    solid            NASA RP-1311 Example 5, in solid mode
    performance      the ideal rocket from that chamber
    trade study      a small two-variable study
    fluids, line     each controller's own default case

Two values measure wall-clock time, not physics, and are masked:
``sweepElapsedMs`` and the trade study's "Elapsed" summary row.
"""

from __future__ import annotations

import json
import math
import sys
import time

__all__ = ["SCIENCE_DIGEST_FLAG", "run_science_digest"]

SCIENCE_DIGEST_FLAG = "--selftest-science"

_MASKED = "<wall-clock, masked>"


def _encode(value, depth=0):
    """JSON-safe and exact: floats as hex, arrays flattened with their shape."""
    import numpy as np

    if depth > 12:
        return "<depth>"
    if isinstance(value, (bool, type(None), str)):
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return {"f": number.hex()} if math.isfinite(number) else {"f": repr(number)}
    if isinstance(value, np.ndarray):
        return {"shape": list(value.shape), "dtype": str(value.dtype),
                "data": [_encode(x, depth + 1) for x in value.ravel().tolist()]}
    if isinstance(value, dict):
        return {str(k): _encode(x, depth + 1) for k, x in value.items()}
    if isinstance(value, (list, tuple)):
        return [_encode(x, depth + 1) for x in value]
    if hasattr(value, "__dataclass_fields__"):
        return {k: _encode(getattr(value, k), depth + 1) for k in value.__dataclass_fields__}
    if hasattr(value, "value") and hasattr(value, "name"):          # enums
        return f"{type(value).__name__}.{value.name}"
    return f"<{type(value).__name__}>"


def _properties(obj) -> dict:
    meta = obj.metaObject()
    out = {}
    for i in range(1, meta.propertyCount()):         # 0 is QObject.objectName
        name = meta.property(i).name()
        try:
            out[name] = _encode(obj.property(name))
        except Exception as error:  # noqa: BLE001 -- recorded, not hidden
            out[name] = f"<error {type(error).__name__}>"
    return out


def _mask(published: dict) -> None:
    for section in published.values():
        if "sweepElapsedMs" in section:
            section["sweepElapsedMs"] = _MASKED
        for row in section.get("summaryRows") or []:
            if isinstance(row, dict) and row.get("label") == "Elapsed":
                row["value"] = _MASKED


def run_science_digest(argv, build_summary) -> int:
    """``<out.json>``. Returns 0 when every case was computed."""
    from pathlib import Path

    from PySide6.QtCore import QCoreApplication, QEvent
    from PySide6.QtGui import QGuiApplication

    out = Path(argv[0]) if argv else Path.cwd() / "rocketforge_science_digest.json"
    app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])

    def settle(rounds=40):
        for _ in range(rounds):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            time.sleep(0.005)

    def wait_idle(obj, limit=300.0):
        start = time.perf_counter()
        while time.perf_counter() - start < limit:
            settle(2)
            if obj.metaObject().indexOfProperty("busy") < 0 or not obj.property("busy"):
                return

    from rocketforge.application.analysis import (
        fanno_service, isentropic_service, mass_flow_service, normal_shock_service,
        nozzle_service, oblique_shock_service, prandtl_meyer_service, rayleigh_service)

    raw = {}
    for gamma in (1.4, 1.2, 1.1325915):
        g = f"g{gamma}"
        raw[f"isentropic/{g}"] = isentropic_service.generate_table(gamma, 0.01, 10.0, 0.01).values
        raw[f"mass_flow/{g}"] = mass_flow_service.generate_table(gamma, 0.01, 5.0, 0.01).values
        raw[f"normal_shock/{g}"] = normal_shock_service.generate_table(gamma, 1.0, 10.0, 0.01).values
        raw[f"prandtl_meyer/{g}"] = prandtl_meyer_service.generate_table(gamma, 1.0, 10.0, 0.01).values
        raw[f"fanno/{g}"] = fanno_service.generate_table(gamma, 0.05, 5.0, 0.01).values
        raw[f"rayleigh/{g}"] = rayleigh_service.generate_table(gamma, 0.05, 5.0, 0.01).values
        raw[f"oblique_table/{g}"] = oblique_shock_service.generate_table(2.0, gamma, 0.5, 22.5, 0.5).values
        for m1 in (1.5, 2.0, 5.0):
            raw[f"oblique_curve/{g}/M{m1}"] = oblique_shock_service.curve_data(m1, gamma, 400)
    raw["nozzle/back_pressure_sweep"] = nozzle_service.back_pressure_sweep(
        nozzle_service.NozzleInputs(), 400)

    from rocketforge.application.analysis.fluid_property_controller import FluidPropertyController
    from rocketforge.application.analysis.line_controller import LineController
    from rocketforge.application.analysis.nozzle_controller import NozzleController
    from rocketforge.application.analysis.performance_controller import RocketPerformanceController
    from rocketforge.application.analysis.thermochemistry_controller import ThermochemistryController
    from rocketforge.application.analysis.thermochemistry_solid_service import (
        solid_formulation_options)
    from rocketforge.application.analysis.trade_study_controller import TradeStudyController

    published = {}
    thermo = ThermochemistryController()
    perf = RocketPerformanceController(thermo)
    study = TradeStudyController(thermo, perf)
    settle()
    thermo.calculate(); wait_idle(thermo)
    published["thermochemistry/biprop"] = _properties(thermo)
    perf.calculate(); wait_idle(perf)
    published["performance"] = _properties(perf)
    study.addObjective("thrust_coefficient", "maximize")
    study.setVariableEnabled("area_ratio", True)
    study.setVariableRange("area_ratio", 20.0, 80.0, 5)
    study.setVariableRange("oxidiser_fuel_ratio", 2.6, 4.2, 6)
    study.runStudy(); wait_idle(study)
    published["trade_study"] = _properties(study)
    thermo.runSweep(); wait_idle(thermo)
    published["thermochemistry/sweep"] = _properties(thermo)

    # Bipropellant -> solid -> bipropellant: solid mode is really entered (loading
    # a formulation does not switch it), and leaving it restores the case exactly.
    thermo.resetInputs(); settle()
    thermo.calculate(); wait_idle(thermo)
    published["thermochemistry/A_before_solid"] = _properties(thermo)
    thermo.setProperty("formulationKind", "solid"); settle()
    solid_ok = True
    for option in solid_formulation_options():
        thermo.loadSolidFormulation(option.key); settle()
        thermo.calculate(); wait_idle(thermo)
        solid_ok &= (thermo.property("formulationKind") == "solid"
                     and bool(thermo.property("hasResult")))
        published[f"thermochemistry/solid/{option.key}"] = _properties(thermo)
    thermo.setProperty("formulationKind", "bipropellant"); settle()
    thermo.resetInputs(); settle()
    thermo.calculate(); wait_idle(thermo)
    published["thermochemistry/A_after_solid"] = _properties(thermo)

    fluid = FluidPropertyController(); settle(); fluid.calculate(); settle()
    published["fluid_properties"] = _properties(fluid)
    line = LineController(); settle(); line.calculate(); settle()
    published["line"] = _properties(line)
    published["nozzle"] = _properties(NozzleController())

    _mask(published)
    import numpy as np
    digest = {
        "build": build_summary,
        "numpy": np.__version__,
        "raw": {key: _encode(value) for key, value in raw.items()},
        "published": published,
        "checks": {
            "solid_mode_solved": solid_ok,
            "biprop_restored_after_solid":
                published["thermochemistry/A_before_solid"]
                == published["thermochemistry/A_after_solid"],
        },
    }
    out.write_text(json.dumps(digest, indent=0, sort_keys=True), encoding="utf-8")
    return 0 if all(digest["checks"].values()) else 1
