"""The QObject the Feed Network page binds to (SYS-5).

It reads the Tank Pressurization and Injector controllers, holds each branch's
stated series of components and its density, viscosity and LIQ-6 term
assignments, and computes only from :meth:`compute`. Components are added and
removed through :meth:`invoke`. Lengths and rises are typed in m, diameters in
mm, roughness in µm, pressure drops in bar and viscosity in mPa·s.
"""

from __future__ import annotations

from dataclasses import replace

from rocketforge.engine.propulsion_system.feed_network import (
    CHOSEN_TERMS,
    DensitySource,
    TermAssignment,
)
from rocketforge.engine.propulsion_system.records import Branch

from . import feed_network_service as service
from .system_study_controller import SystemStudyController, choice_field, number_field

__all__ = ["FeedNetworkController"]

#: Component field -> (label, unit, SI per display unit).
_FIELD_UNITS = {"length": ("Length", "m", 1.0), "diameter": ("Inner diameter", "mm", 1.0e-3),
                "roughness": ("Absolute roughness", "µm", 1.0e-6),
                "loss_coefficient": ("Loss coefficient K", "", 1.0),
                "pressure_drop": ("Pressure drop", "bar", 1.0e5),
                "rise": ("Rise against the acceleration", "m", 1.0),
                "acceleration": ("Acceleration", "m/s²", 1.0)}
_DENSITY = [("", "Not stated"), ("injector", "LIQ-6 injector-inlet density"),
            ("stated", "Stated")]
_ASSIGN = [("", "Not stated"), ("carried", "Carried at the injector inlet"),
           ("replaced", "Replaced by the network")]
_TERM_LABELS = {"dynamic_head": "LIQ-6 dynamic head ½ρv²", "other_loss": "LIQ-6 other losses"}
_MPAS = 1.0e-3


class FeedNetworkController(SystemStudyController):
    """Application-side facade for the Feed Network page."""

    def __init__(self, pressurization_source, injector_source, parent=None) -> None:
        self._pressurization = pressurization_source
        self._injector = injector_source
        self._settings = {Branch.OXIDISER: service.BranchSettings(),
                          Branch.FUEL: service.BranchSettings()}
        SystemStudyController.__init__(self, (pressurization_source, injector_source), parent)

    def _basis(self):
        return service.feed_basis(
            self._pressurization.result(), bool(self._pressurization.property("resultStale")),
            self._injector.result(), bool(self._injector.property("resultStale")))

    def _build(self, basis):
        return service.build_definition(basis, self._settings[Branch.OXIDISER],
                                        self._settings[Branch.FUEL])

    def _solve(self, definition):
        return service.solve_feed_network(definition)

    def _update(self, branch, settings) -> bool:
        if settings == self._settings[branch]:
            return False
        self._settings[branch] = settings
        return True

    def _apply_number(self, branch, name, value):
        if branch is None:
            return False
        s = self._settings[branch]
        if name == "density":
            return self._update(branch, replace(s, density=value))
        if name == "viscosity":
            return self._update(branch, replace(
                s, viscosity=None if value is None else value * _MPAS))
        head, _, field_name = name.partition(".")
        if not (head.startswith("c") and head[1:].isdigit()):
            return False
        index = int(head[1:])
        if index >= len(s.components) or field_name not in _FIELD_UNITS:
            return False
        kind, values = s.components[index]
        if field_name not in service.COMPONENT_FIELDS[kind]:
            return False
        scale = _FIELD_UNITS[field_name][2]
        updated = dict(values)
        updated[field_name] = None if value is None else value * scale
        components = list(s.components)
        components[index] = (kind, tuple(sorted(updated.items())))
        return self._update(branch, replace(s, components=tuple(components)))

    def _apply_choice(self, branch, name, value):
        if branch is None:
            return False
        s = self._settings[branch]
        if name == "density_source" and value in ("", "injector", "stated"):
            return self._update(branch, replace(
                s, density_source=DensitySource(value) if value else None))
        if name in CHOSEN_TERMS and value in ("", "carried", "replaced"):
            return self._update(branch, replace(s, assignments={
                **s.assignments, name: TermAssignment(value) if value else None}))
        return False

    def _apply_action(self, branch, name, argument):
        if branch is None:
            return False
        s = self._settings[branch]
        if name == "add" and argument in service.COMPONENT_FIELDS:
            blank = tuple((f, None) for f in service.COMPONENT_FIELDS[argument])
            return self._update(branch, replace(s, components=s.components
                                                + ((argument, blank),)))
        if name == "remove" and s.components:
            return self._update(branch, replace(s, components=s.components[:-1]))
        return False

    def _sections(self, basis):
        kinds = dict(service.COMPONENT_KINDS)
        sections = []
        for branch in (Branch.OXIDISER, Branch.FUEL):
            s = self._settings[branch]
            b = branch.value
            fields = [
                choice_field(f"{b}.density_source", "Liquid density", _DENSITY,
                             s.density_source.value if s.density_source else ""),
                number_field(f"{b}.density", "Density ρ", "kg/m³", s.density,
                             visible=s.density_source is DensitySource.STATED),
                number_field(f"{b}.viscosity", "Dynamic viscosity μ", "mPa·s", s.viscosity,
                             _MPAS, note="Needed by pipes; none is assumed."),
            ]
            for key in CHOSEN_TERMS:
                value = s.assignments.get(key)
                fields.append(choice_field(f"{b}.{key}", _TERM_LABELS[key], _ASSIGN,
                                           value.value if value else ""))
            for i, (kind, values) in enumerate(s.components):
                given = dict(values)
                for n, field_name in enumerate(service.COMPONENT_FIELDS[kind]):
                    label, unit, scale = _FIELD_UNITS[field_name]
                    fields.append(number_field(
                        f"{b}.c{i}.{field_name}", f"{i + 1}. {kinds[kind]} · {label}", unit,
                        given.get(field_name), scale))
                if not service.COMPONENT_FIELDS[kind]:
                    fields.append({"key": f"{b}.c{i}.none", "label": f"{i + 1}. {kinds[kind]}",
                                   "kind": "note", "unit": "", "text": "", "visible": True,
                                   "note": "Declared without data; its drop stays unresolved.",
                                   "options": [], "value": ""})
            propellant = basis.propellant_of(branch) if basis is not None else ""
            title = ("Oxidiser feed" if branch is Branch.OXIDISER else "Fuel feed") + (
                f" · {propellant}" if propellant else "")
            actions = [{"key": f"{b}.add", "argument": k, "label": f"+ {label}"}
                       for k, label in service.COMPONENT_KINDS]
            actions.append({"key": f"{b}.remove", "argument": "last",
                            "label": "Remove the last component"})
            sections.append({"key": b, "title": title, "wide": False,
                             "note": "Components in series, from the tank outlet to the "
                                     "injector inlet. LIQ-6's feed-line and valve terms are "
                                     "always replaced by this network.",
                             "fields": fields, "actions": actions})
        return sections

    def _basis_rows(self, basis):
        rows = [{"label": "Propellant", "value": basis.pair_label}]
        for branch, word in ((Branch.OXIDISER, "Oxidiser"), (Branch.FUEL, "Fuel")):
            b = basis.of(branch)
            pressures = ", ".join(f"{k} {v / 1e5:.5g} bar" for k, v in b.tank_pressures.items())
            rows.append({"label": f"{word} tank",
                         "value": (pressures or "no tank pressure") + " · pressurization"})
            rows.append({"label": f"{word} flow",
                         "value": f"{b.mass_flow:.5g} kg/s, ρ {b.injector_density:.5g} kg/m³"
                                  " · injector"})
        return rows

    def _branch_view(self, outcome):
        return service.branch_view(outcome)

    def _computed_message(self, definition, result):
        return {"warning": "Computed; a tank pressure falls short of its feed requirement",
                "incomplete": "Computed; a term or component is unresolved"}.get(
                    result.status.value, "Computed")
