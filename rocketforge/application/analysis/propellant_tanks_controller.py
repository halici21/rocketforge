"""The QObject the Tank Geometry & Packaging page binds to (SYS-2).

It reads the complete inventory in the Propellant Inventory controller, holds
what the user states for each tank, and computes only from :meth:`compute`.
Densities are typed in kg/m³, temperatures in K, pressures in bar, lengths in
m, volumes in L and fractions in percent; everything below is SI.
"""

from __future__ import annotations

from dataclasses import replace

from rocketforge.engine.propulsion_system.records import Branch
from rocketforge.engine.propulsion_system.tanks import (
    DensitySource,
    SizingMode,
    TankShape,
    UllageMode,
)

from . import propellant_tanks_service as service
from .system_study_controller import SystemStudyController, choice_field, number_field

__all__ = ["PropellantTanksController"]

_BAR = 1.0e5
_LITRE = 1.0e-3
_PERCENT = 0.01
#: Plain numbers: name -> (attribute, SI per display unit).
_NUMBERS = {"density": ("density", 1.0), "storage_temperature": ("storage_temperature", 1.0),
            "storage_pressure": ("storage_pressure", _BAR),
            "diameter": ("diameter", 1.0), "total_length": ("total_length", 1.0),
            "dome_ratio": ("dome_ratio", 1.0),
            "envelope_diameter": ("envelope_diameter", 1.0),
            "envelope_length": ("envelope_length", 1.0)}
_SHAPES = [("", "Not chosen"), ("sphere", "Sphere"),
           ("cylinder_hemispherical", "Cylinder, hemispherical domes"),
           ("cylinder_ellipsoidal", "Cylinder, ellipsoidal domes")]
_MODES = [("", "Not stated"), ("stated_diameter", "Diameter stated"),
          ("stated_length", "Length stated")]
_ULLAGE = [("", "Not stated"), ("fraction", "Fraction of the tank"), ("volume", "Volume")]
_DENSITY = [("stated", "Stated"), ("fluid_model", "Validated fluid model")]


class PropellantTanksController(SystemStudyController):
    """Application-side facade for the Tank Geometry & Packaging page."""

    def __init__(self, inventory_source, parent=None) -> None:
        self._inventory = inventory_source
        self._settings = {Branch.OXIDISER: service.BranchSettings(),
                          Branch.FUEL: service.BranchSettings()}
        SystemStudyController.__init__(self, (inventory_source,), parent)

    def _basis(self):
        return service.tanks_basis(self._inventory.result(),
                                   bool(self._inventory.property("resultStale")))

    def _build(self, basis):
        return service.build_definition(basis, self._settings[Branch.OXIDISER],
                                        self._settings[Branch.FUEL])

    def _solve(self, definition):
        return service.solve_tanks(definition)

    def _update(self, branch, settings) -> bool:
        if settings == self._settings[branch]:
            return False
        self._settings[branch] = settings
        return True

    def _apply_number(self, branch, name, value):
        if branch is None:
            return False
        s = self._settings[branch]
        if name == "ullage":
            scale = _PERCENT if s.ullage_mode is UllageMode.FRACTION else _LITRE
            return self._update(branch, replace(
                s, ullage_value=None if value is None else value * scale))
        if name in _NUMBERS:
            attribute, scale = _NUMBERS[name]
            return self._update(branch, replace(
                s, **{attribute: None if value is None else value * scale}))
        return False

    def _apply_choice(self, branch, name, value):
        if branch is None:
            return False
        s = self._settings[branch]
        if name == "density_source" and value in {d.value for d in DensitySource}:
            return self._update(branch, replace(s, density_source=DensitySource(value)))
        if name == "ullage_mode" and value in ("", "fraction", "volume"):
            new = UllageMode(value) if value else None
            # A fraction and a volume are not interchangeable.
            keep = s.ullage_value if new is s.ullage_mode else None
            return self._update(branch, replace(s, ullage_mode=new, ullage_value=keep))
        if name == "shape" and value in {k for k, _l in _SHAPES}:
            return self._update(branch, replace(s, shape=TankShape(value) if value else None))
        if name == "sizing_mode" and value in ("", "stated_diameter", "stated_length"):
            return self._update(branch, replace(
                s, sizing_mode=SizingMode(value) if value else None))
        return False

    def _sections(self, basis):
        sections = []
        for branch in (Branch.OXIDISER, Branch.FUEL):
            s = self._settings[branch]
            b = branch.value
            propellant = basis.propellant_of(branch) if basis is not None else ""
            supported = bool(propellant) and service.fluid_model_supported(propellant)
            fluid = s.density_source is DensitySource.FLUID_MODEL
            cylinder = s.shape in (TankShape.CYLINDER_HEMISPHERICAL,
                                   TankShape.CYLINDER_ELLIPSOIDAL)
            fraction = s.ullage_mode is UllageMode.FRACTION
            fields = [
                choice_field(f"{b}.density_source", "Storage density", _DENSITY,
                             s.density_source.value,
                             note=("" if not fluid else
                                   "Evaluated on Compute at the stated storage state; refused "
                                   "if that state is not liquid." if supported else
                                   f"No validated fluid model for {propellant}: state the "
                                   "density.")),
                number_field(f"{b}.density", "Density ρ", "kg/m³", s.density, visible=not fluid),
                number_field(f"{b}.storage_temperature", "Storage temperature", "K",
                             s.storage_temperature, visible=fluid),
                number_field(f"{b}.storage_pressure", "Storage pressure", "bar",
                             s.storage_pressure, _BAR, visible=fluid),
                choice_field(f"{b}.ullage_mode", "Ullage", _ULLAGE,
                             s.ullage_mode.value if s.ullage_mode else ""),
                number_field(f"{b}.ullage", "Ullage" + (" fraction" if fraction else " volume"),
                             "%" if fraction else "L", s.ullage_value,
                             _PERCENT if fraction else _LITRE,
                             visible=s.ullage_mode is not None),
                choice_field(f"{b}.shape", "Shape", _SHAPES, s.shape.value if s.shape else ""),
                choice_field(f"{b}.sizing_mode", "Fixed by", _MODES,
                             s.sizing_mode.value if s.sizing_mode else "", visible=cylinder),
                number_field(f"{b}.diameter", "Internal diameter", "m", s.diameter,
                             visible=cylinder and s.sizing_mode is SizingMode.STATED_DIAMETER),
                number_field(f"{b}.total_length", "Total internal length", "m", s.total_length,
                             visible=cylinder and s.sizing_mode is SizingMode.STATED_LENGTH),
                number_field(f"{b}.dome_ratio", "Dome height / radius k", "", s.dome_ratio,
                             visible=s.shape is TankShape.CYLINDER_ELLIPSOIDAL,
                             note="0 < k ≤ 1; k = 1 is a hemisphere"),
                number_field(f"{b}.envelope_diameter", "Envelope diameter (optional)", "m",
                             s.envelope_diameter),
                number_field(f"{b}.envelope_length", "Envelope length (optional)", "m",
                             s.envelope_length),
            ]
            title = ("Oxidiser tank" if branch is Branch.OXIDISER else "Fuel tank") + (
                f" · {propellant}" if propellant else "")
            sections.append({"key": b, "title": title, "wide": False,
                             "note": "Internal geometry only: no wall, mass or insulation.",
                             "fields": fields, "actions": []})
        return sections

    def _basis_rows(self, basis):
        return [
            {"label": "Propellant", "value": f"{basis.pair_label}"},
            {"label": "Oxidiser load",
             "value": f"{basis.oxidiser_loaded_mass:,.4f} kg {basis.oxidiser} · inventory"},
            {"label": "Fuel load",
             "value": f"{basis.fuel_loaded_mass:,.4f} kg {basis.fuel} · inventory"},
            {"label": "Inventory", "value": basis.inventory.fingerprint[:12]},
        ]

    def _branch_view(self, outcome):
        return service.branch_view(outcome)

    def _total_rows(self, result):
        return service.total_rows(result)

    def _computed_message(self, definition, result):
        return "Computed"
