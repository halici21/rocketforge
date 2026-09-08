"""Non-interactive self-tests, runnable from the shipped executable.

Exists for one reason: to make a claim about the *packaged* application
checkable rather than assumed. A provider that works from source and whose
files appear in ``dist/`` has not been shown to work when frozen -- the native
library has to load, and the thermodynamic database has to be found, from
inside the bundle.

Invoked as::

    RocketForge.exe --selftest-thermochemistry

It prints one JSON document and exits. There is no window, no menu entry and no
user-facing surface: this is a diagnostic, and the interface phase (5D) owns
anything a user is meant to see.

``application`` is the composition root, so it is the layer permitted to reach
a provider. Nothing below it does.
"""

from __future__ import annotations

import json
import sys

__all__ = ["SELFTEST_FLAG", "run_thermochemistry_selftest"]

#: The argument that triggers the thermochemistry self-test.
SELFTEST_FLAG = "--selftest-thermochemistry"


def run_thermochemistry_selftest() -> int:
    """Solve one chamber equilibrium and report what produced it.

    Returns 0 on success. Prints a JSON document describing the provider, the
    thermodynamic database actually used -- with its hash -- and the mapped
    result, so that a frozen run can be compared field by field against a
    source run.
    """
    payload: dict[str, object] = {
        "selftest": "thermochemistry",
        "frozen": bool(getattr(sys, "frozen", False)),
        "meipass": str(getattr(sys, "_MEIPASS", "") or ""),
        "python": sys.version.split()[0],
    }

    try:
        from rocketforge.providers.cea import (
            LIQUID_METHANE,
            LOX,
            CEAThermochemistryProvider,
            check_availability,
        )
        from rocketforge.physics.thermochemistry import (
            ChamberEquilibriumRequest,
            MixtureRatio,
            Phase,
            PropellantStream,
        )
    except Exception as exc:  # noqa: BLE001 - a diagnostic must not itself crash
        payload.update(status="import_failed", error=f"{type(exc).__name__}: {exc}")
        print(json.dumps(payload, indent=2))
        return 1

    availability = check_availability()
    payload["availability"] = {
        "status": availability.status.value,
        "version": availability.version,
        "library_version": availability.library_version,
        "detail": availability.detail,
    }
    if not availability.is_usable:
        payload["status"] = "provider_unavailable"
        print(json.dumps(payload, indent=2))
        return 1

    provider = CEAThermochemistryProvider()
    resources = provider.resources()
    payload["resources"] = {
        "thermo_path": resources.thermo_path,
        "thermo_bytes": resources.thermo_bytes,
        "thermo_sha256": resources.thermo_sha256,
        "frozen_bundle": resources.frozen,
    }

    # The canonical Phase 5C production case. Fixed here so that a frozen run
    # and a source run are answering exactly the same question.
    request = ChamberEquilibriumRequest(
        fuel=PropellantStream(LIQUID_METHANE, 111.643, phase=Phase.LIQUID),
        oxidiser=PropellantStream(LOX, 90.17, phase=Phase.LIQUID),
        oxidiser_fuel_ratio=MixtureRatio(3.4),
        chamber_pressure=10.0e6,
    )

    try:
        solution = provider.solve_chamber(request)
    except Exception as exc:  # noqa: BLE001
        payload.update(status="solve_failed", error=f"{type(exc).__name__}: {exc}")
        print(json.dumps(payload, indent=2))
        return 1

    payload["solution_status"] = solution.status.value
    if solution.value is None:
        payload["status"] = "no_solution"
        payload["diagnostics"] = [d.message for d in solution.diagnostics]
        print(json.dumps(payload, indent=2))
        return 1

    state = solution.value
    payload["status"] = "ok"
    payload["state"] = {
        "temperature_K": state.temperature,
        "pressure_Pa": state.pressure,
        "density_kg_per_m3": state.density,
        "molar_mass_kg_per_mol": state.molar_mass,
        "gas_constant_J_per_kgK": state.gas_constant,
        "cp_J_per_kgK": state.cp,
        "cv_J_per_kgK": state.cv,
        "gamma_s": state.gamma,
        "gamma_frozen": state.gamma_frozen,
        "enthalpy_J_per_kg": state.enthalpy,
        "entropy_J_per_kgK": state.entropy,
        "condensed_mass_fraction": state.condensed_mass_fraction,
        "species_count": len(state.composition.entries),
        "X": dict(state.composition.fractions),
    }
    payload["provenance"] = {
        "provider_id": state.provenance.provider_id,
        "provider_version": state.provenance.provider_version,
        "library_version": state.provenance.library_version,
        "database": state.provenance.database,
        "database_sha256": state.provenance.database_sha256,
        "chemistry_mode": state.provenance.chemistry_mode.value,
        "equilibrium_constraint": state.provenance.equilibrium_constraint.value,
        "species_set": list(state.provenance.species_set),
    }
    print(json.dumps(payload, indent=2))
    return 0
