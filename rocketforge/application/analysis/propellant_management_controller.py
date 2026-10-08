"""The QObject the Propellant Management page binds to (SYS-3).

It reads the Propellant Inventory and Tank Geometry & Packaging controllers,
holds each branch's stated management intent, and computes only from
:meth:`compute`.
"""

from __future__ import annotations

from dataclasses import replace

from rocketforge.engine.propulsion_system.management import (
    Environment,
    ManagementMode,
    SettlingIntent,
)
from rocketforge.engine.propulsion_system.records import Branch

from . import propellant_management_service as service
from .system_study_controller import SystemStudyController, choice_field, number_field

__all__ = ["PropellantManagementController"]

_MODES = [("", "Not stated"), ("settled", "Settled free surface"), ("diaphragm", "Diaphragm"),
          ("bladder", "Bladder"), ("piston", "Piston"), ("bellows", "Bellows"),
          ("surface_tension", "Surface-tension device (PMD)")]
_ENVIRONMENTS = [("unresolved", "Unresolved"), ("accelerated", "Accelerated throughout"),
                 ("low_gravity", "Low-gravity phases")]
_SETTLING = [("unresolved", "Unresolved"), ("required", "Required"),
             ("not_required", "Not required")]


class PropellantManagementController(SystemStudyController):
    """Application-side facade for the Propellant Management page."""

    def __init__(self, inventory_source, tanks_source, parent=None) -> None:
        self._inventory = inventory_source
        self._tanks = tanks_source
        self._settings = {Branch.OXIDISER: service.BranchSettings(),
                          Branch.FUEL: service.BranchSettings()}
        SystemStudyController.__init__(self, (inventory_source, tanks_source), parent)

    def _basis(self):
        return service.management_basis(
            self._inventory.result(), bool(self._inventory.property("resultStale")),
            self._tanks.result(), bool(self._tanks.property("resultStale")))

    def _build(self, basis):
        return service.build_definition(basis, self._settings[Branch.OXIDISER],
                                        self._settings[Branch.FUEL])

    def _solve(self, definition):
        return service.solve_management(definition)

    def _update(self, branch, settings) -> bool:
        if settings == self._settings[branch]:
            return False
        self._settings[branch] = settings
        return True

    def _apply_number(self, branch, name, value):
        if branch is None or name != "settling_acceleration":
            return False
        return self._update(branch, replace(self._settings[branch],
                                            settling_acceleration=value))

    def _apply_choice(self, branch, name, value):
        if branch is None:
            return False
        s = self._settings[branch]
        if name == "mode" and value in {k for k, _l in _MODES}:
            return self._update(branch, replace(s, mode=ManagementMode(value) if value else None))
        if name == "environment" and value in {e.value for e in Environment}:
            return self._update(branch, replace(s, environment=Environment(value)))
        if name == "settling" and value in {i.value for i in SettlingIntent}:
            return self._update(branch, replace(s, settling=SettlingIntent(value)))
        return False

    def _sections(self, basis):
        sections = []
        for branch in (Branch.OXIDISER, Branch.FUEL):
            s = self._settings[branch]
            b = branch.value
            propellant = basis.propellant_of(branch) if basis is not None else ""
            fields = [
                choice_field(f"{b}.mode", "Propellant management", _MODES,
                             s.mode.value if s.mode else "",
                             note="No expulsion efficiency is taken from the device type."),
                choice_field(f"{b}.environment", "Acceleration environment", _ENVIRONMENTS,
                             s.environment.value),
                choice_field(f"{b}.settling", "Settling acceleration", _SETTLING,
                             s.settling.value),
                number_field(f"{b}.settling_acceleration", "Settling acceleration (optional)",
                             "m/s²", s.settling_acceleration,
                             note="Recorded intent; settling is not evaluated."),
            ]
            title = ("Oxidiser" if branch is Branch.OXIDISER else "Fuel") + (
                f" · {propellant}" if propellant else "")
            sections.append({"key": b, "title": title, "wide": False,
                             "note": "Intent and bookkeeping only: no slosh dynamics.",
                             "fields": fields, "actions": []})
        return sections

    def _basis_rows(self, basis):
        rows = [{"label": "Propellant", "value": basis.pair_label}]
        for branch, word in ((Branch.OXIDISER, "Oxidiser"), (Branch.FUEL, "Fuel")):
            s = basis.storage_of(branch)
            rows.append({"label": f"{word} tank",
                         "value": f"{s.tank_volume:,.6f} m³, ullage {s.ullage_fraction:.2%}"
                                  " · tanks"})
            rows.append({"label": f"{word} residual",
                         "value": f"{s.residual_mass:,.4f} kg, η {s.expulsion_efficiency:.6g}"
                                  " · inventory"})
        return rows

    def _branch_view(self, outcome):
        return service.branch_view(outcome)

    def _computed_message(self, definition, result):
        if result.status.value == "incomplete":
            return "Computed; outlet coverage is unresolved for a branch"
        return "Computed"
