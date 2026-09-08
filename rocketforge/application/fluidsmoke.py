"""A non-interactive tour of the Fluid Properties workspace and the coupling.

Fifth and sixth of the diagnostics, and they exist for the reason the others
do: a claim about the *packaged* application cannot be checked by inspecting
``dist/``. Between them they answer the questions a screenshot cannot:

* does the packaged build perform a **real** property query, or merely import
  the module and render a page?
* does the packaged build reproduce the CEA reference state exactly under the
  corrected policy, and move away from it when the liquid temperature moves?
* does the packaged build compute a bulk density and a density impulse from
  those validated properties, and do the two spellings of density impulse
  still agree?

Invoked as::

    RocketForge.exe --selftest-fluid-properties [output directory]
    RocketForge.exe --selftest-reactant-enthalpy-coupling [output directory]

They drive the real controllers through the same slots the interface's own
controls call. **No synthetic desktop input**, and they run under the offscreen
platform plugin.
"""

from __future__ import annotations

import json
import sys

__all__ = [
    "FLUID_SMOKE_FLAG",
    "COUPLING_SMOKE_FLAG",
    "run_fluid_smoke",
    "run_coupling_smoke",
    "RESOLUTIONS",
]

FLUID_SMOKE_FLAG = "--selftest-fluid-properties"
COUPLING_SMOKE_FLAG = "--selftest-reactant-enthalpy-coupling"

#: The window sizes the visual gate is judged at, unchanged since Phase 4G.
RESOLUTIONS = ((2560, 1440), (1920, 1080), (1366, 768))

#: The states the tour evaluates. Chosen so the tour exercises a liquid, the
#: same liquid at a pressure where it is a gas, and a refusal.
TOUR_STATES = (
    ("OXYGEN", 90.17, 300000.0, "reference liquid"),
    ("OXYGEN", 95.0, 300000.0, "warmer liquid, still subcooled at 3 bar"),
    ("OXYGEN", 95.0, 101325.0, "the same temperature at 1 atm: a gas"),
    ("METHANE", 111.643, 300000.0, "liquid methane at its reference"),
    ("HYDROGEN", 20.27, 300000.0, "liquid hydrogen at its reference"),
    ("OXYGEN", 40.0, 300000.0, "below the triple point: refused"),
)


def _report_path(argv, default_dir, name):
    import pathlib

    directory = pathlib.Path(argv[0]) if argv else pathlib.Path(default_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory, directory / name


def run_fluid_smoke(argv, configure, build_engine, ui_dir) -> int:
    """Evaluate real fluid states through the real controller.

    Headless on purpose. The *visual* gate for this page is already covered by
    ``--selftest-workspaces``, which renders it at three resolutions in both
    themes; duplicating that here would add captures and prove nothing new.
    What this adds is the thing a capture cannot show: that a real query
    reached a real equation of state in the packaged build, rather than the
    page merely rendering.
    """
    _directory, report_path = _report_path(argv, "fluid_smoke",
                                           "fluid_smoke.json")

    from rocketforge.application.analysis.fluid_property_controller import (
        FluidPropertyController,
    )

    controller = FluidPropertyController()
    report: dict = {
        "status": "ok",
        "frozen": bool(getattr(sys, "frozen", False)),
        "python": sys.version.split()[0],
        "provider_available": bool(controller.providerAvailable),
        "provider_label": controller.providerLabel,
        "provider_version": controller.providerVersion,
        "provider_backend": controller.providerBackend,
        "states": [],
    }

    for fluid, temperature, pressure, note in TOUR_STATES:
        controller.setFluid(fluid)
        controller.setTemperature(temperature)
        controller.setPressure(pressure)
        controller.calculate()
        report["states"].append({
            "fluid": fluid, "temperature_K": temperature,
            "pressure_Pa": pressure, "note": note,
            "status": controller.statusLabel,
            "phase": controller.phase,
            "has_result": bool(controller.hasResult),
            "message": controller.message,
            "rows": [dict(row) for row in controller.resultRows],
            "provenance": [dict(row) for row in controller.provenanceRows],
        })

    # A real query, not an import: the reference liquid must have produced
    # numbers, so a packaged build that could only render cannot pass.
    first = report["states"][0]
    report["performed_a_real_query"] = bool(
        first["has_result"] and first["rows"]
        and first["rows"][0]["available"])
    # And the phase must actually respond to pressure, which no stub would do.
    report["phase_responds_to_pressure"] = (
        report["states"][1]["phase"] == "liquid"
        and report["states"][2]["phase"] == "gas")
    report["refused_the_out_of_range_state"] = (
        not report["states"][-1]["has_result"])

    ok = (report["performed_a_real_query"]
          and report["phase_responds_to_pressure"]
          and report["refused_the_out_of_range_state"])
    report["status"] = "ok" if ok else "failed"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[fluid-smoke] {len(report['states'])} states, real query: "
          f"{report['performed_a_real_query']}, phase responds to pressure: "
          f"{report['phase_responds_to_pressure']} -> {report_path}")
    return 0 if ok else 2


def run_coupling_smoke(argv, configure, build_engine, ui_dir) -> int:
    """Prove the packaged build corrects reactant enthalpy, and by how much."""
    _directory, report_path = _report_path(argv, "coupling_smoke",
                                           "coupling_smoke.json")

    from rocketforge.engineering.propellants import (
        PRODUCTION_FLUID_MAPPING,
        density_impulse,
        mixture_bulk_density,
        stream_density,
    )
    from rocketforge.physics.fluids import FluidPhase
    from rocketforge.physics.thermochemistry import (
        ChamberEquilibriumRequest,
        MixtureRatio,
        Phase,
        PropellantStream,
    )
    from rocketforge.providers.cea import CEAThermochemistryProvider
    from rocketforge.providers.cea.enthalpy_coupling import (
        CEA_REFERENCE_PRESSURE,
        ReactantEnthalpyPolicy,
        ReactantFluidBinding,
    )
    from rocketforge.providers.cea.propellants import LIQUID_METHANE, LOX
    from rocketforge.providers.fluid_properties import coolprop_provider

    feed = 300000.0
    chamber_pressure = 10_000_000.0
    provider = CEAThermochemistryProvider()
    fluids = coolprop_provider()

    def request(ox_t, fuel_t, pressure):
        return ChamberEquilibriumRequest(
            fuel=PropellantStream(propellant=LIQUID_METHANE,
                                  temperature=fuel_t, pressure=pressure,
                                  phase=Phase.LIQUID),
            oxidiser=PropellantStream(propellant=LOX, temperature=ox_t,
                                      pressure=pressure, phase=Phase.LIQUID),
            oxidiser_fuel_ratio=MixtureRatio(3.4),
            chamber_pressure=chamber_pressure)

    def bindings(pressure):
        return {
            "O2(L)": ReactantFluidBinding(fluid=PRODUCTION_FLUID_MAPPING
                                          .require("LOX").fluid,
                                          pressure=pressure,
                                          required_phase=FluidPhase.LIQUID),
            "CH4(L)": ReactantFluidBinding(fluid=PRODUCTION_FLUID_MAPPING
                                           .require("LCH4").fluid,
                                           pressure=pressure,
                                           required_phase=FluidPhase.LIQUID),
        }

    def corrected(req, pressure):
        return provider.solve_chamber(
            req,
            enthalpy_policy=ReactantEnthalpyPolicy.FLUID_SENSIBLE_CORRECTION,
            fluid_provider=fluids, reactant_bindings=bindings(pressure))

    report: dict = {
        "status": "ok",
        "frozen": bool(getattr(sys, "frozen", False)),
        "python": sys.version.split()[0],
    }

    # 1. at the reference state, bit-identical
    reference = request(90.17, 111.643, CEA_REFERENCE_PRESSURE)
    native_reference = provider.solve_chamber(reference).value
    corrected_reference = corrected(reference, CEA_REFERENCE_PRESSURE).value
    report["reference_state"] = {
        "native_T": float(native_reference.temperature),
        "corrected_T": float(corrected_reference.temperature),
        "bit_identical": (corrected_reference.temperature
                          == native_reference.temperature),
    }

    # 2. away from it, the chamber moves
    sweep = []
    for ox_t in (86.0, 90.17, 95.0, 98.0):
        req = request(ox_t, 111.643, feed)
        native = provider.solve_chamber(req).value
        result = corrected(req, feed)
        increment = next(
            (d.detail["delta_h_sensible_J_per_kg"] for d in result.diagnostics
             if d.code == "REACTANT_ENTHALPY_FLUID_CORRECTED"
             and d.detail["reactant"] == "O2(L)"), None)
        sweep.append({"oxidiser_temperature_K": ox_t,
                      "native_T": float(native.temperature),
                      "corrected_T": float(result.value.temperature),
                      "oxidiser_delta_h_J_per_kg": increment})
    report["temperature_sweep"] = sweep
    report["native_is_insensitive"] = len({s["native_T"] for s in sweep}) == 1
    report["corrected_is_sensitive"] = len({s["corrected_T"] for s in sweep}) == len(sweep)

    # 3. validated density and density impulse from the same stream states
    fuel = stream_density(fluids, PRODUCTION_FLUID_MAPPING.require("LCH4"),
                          111.643, feed)
    oxidiser = stream_density(fluids, PRODUCTION_FLUID_MAPPING.require("LOX"),
                              90.17, feed)
    bulk = mixture_bulk_density(3.4, fuel, oxidiser)
    metric = density_impulse(bulk, 3400.0, 3400.0 / 9.80665)
    report["density"] = {
        "fuel": fuel.as_mapping(), "oxidiser": oxidiser.as_mapping(),
        "bulk": bulk.as_mapping(), "density_impulse": metric.as_mapping(),
        "identity_residual": metric.residual,
    }

    ok = (report["reference_state"]["bit_identical"]
          and report["native_is_insensitive"]
          and report["corrected_is_sensitive"]
          and metric.residual < 1e-12)
    report["status"] = "ok" if ok else "failed"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[coupling-smoke] reference bit-identical: "
          f"{report['reference_state']['bit_identical']}, "
          f"corrected sensitive: {report['corrected_is_sensitive']}, "
          f"density impulse residual: {metric.residual:.3g} -> {report_path}")
    return 0 if ok else 2
