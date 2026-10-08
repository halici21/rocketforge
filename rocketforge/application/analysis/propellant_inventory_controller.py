"""The QObject the Propellant Inventory page binds to (SYS-1).

It reads the accepted sizing in the Thrust Chamber Sizing controller and the
trade in the Propellant Trade controller (for the requirement's burn time),
holds what the user states for each branch's budget, and computes only from
:meth:`compute`. Masses are typed in kg, the expulsion efficiency and a reserve
fraction in percent; everything below is SI and fractions.
"""

from __future__ import annotations

from dataclasses import replace

from rocketforge.engine.propulsion_system.inventory import (
    ALLOWANCE_TERMS,
    ReserveMode,
    ResidualMode,
    TermMode,
)
from rocketforge.engine.propulsion_system.records import Branch

from . import propellant_inventory_service as service
from .system_study_controller import SystemStudyController, choice_field, number_field

__all__ = ["PropellantInventoryController"]

_PERCENT = 0.01
_TERM_OPTIONS = [("unresolved", "Unresolved"), ("stated", "Stated"),
                 ("not_applicable", "Not applicable")]
_RESIDUAL_OPTIONS = [("unresolved", "Unresolved"),
                     ("expulsion_efficiency", "Expulsion efficiency"),
                     ("residual_mass", "Residual mass")]
_RESERVE_OPTIONS = [("unresolved", "Unresolved"), ("stated_mass", "Stated mass"),
                    ("stated_fraction", "Fraction of usable"),
                    ("not_applicable", "Not applicable")]
#: Mass terms with a mode and a value: name -> (mode attribute, value attribute, label).
_TERMS = {
    "tank_residual": ("tank_residual_mode", "tank_residual", "Tank residual"),
    "trapped_line": ("trapped_line_mode", "trapped_line", "Trapped in lines and valves"),
    "boiloff": ("boiloff_mode", "boiloff", "Boil-off before the burn"),
}


class PropellantInventoryController(SystemStudyController):
    """Application-side facade for the Propellant Inventory page."""

    def __init__(self, sizing_source, trade_source, parent=None) -> None:
        self._sizing = sizing_source
        self._trade = trade_source
        self._settings = {Branch.OXIDISER: service.BranchSettings(),
                          Branch.FUEL: service.BranchSettings()}
        SystemStudyController.__init__(self, (sizing_source, trade_source), parent)

    # -- the gate ------------------------------------------------------------

    def _basis(self):
        return service.inventory_basis(
            self._sizing.result(), bool(self._sizing.property("resultStale")),
            self._trade.result(), bool(self._trade.property("resultStale")))

    def _build(self, basis):
        return service.build_definition(basis, self._settings[Branch.OXIDISER],
                                        self._settings[Branch.FUEL])

    def _solve(self, definition):
        return service.solve_inventory(definition)

    def _update(self, branch: Branch, settings: service.BranchSettings) -> bool:
        if settings == self._settings[branch]:
            return False
        self._settings[branch] = settings
        return True

    def _apply_number(self, branch, name, value):
        if branch is None:
            return False
        s = self._settings[branch]
        if name == "expulsion_efficiency":
            return self._update(branch, replace(
                s, expulsion_efficiency=None if value is None else value * _PERCENT))
        if name == "reserve":
            scale = _PERCENT if s.reserve_mode is ReserveMode.STATED_FRACTION else 1.0
            return self._update(branch, replace(
                s, reserve_value=None if value is None else value * scale))
        if name in _TERMS:
            return self._update(branch, replace(s, **{_TERMS[name][1]: value}))
        if name in s.allowance_values:
            return self._update(branch, replace(
                s, allowance_values={**s.allowance_values, name: value}))
        return False

    def _apply_choice(self, branch, name, value):
        if branch is None:
            return False
        s = self._settings[branch]
        if name == "residual_mode" and value in {m.value for m in ResidualMode}:
            return self._update(branch, replace(s, residual_mode=ResidualMode(value)))
        if name == "reserve_mode" and value in {m.value for m in ReserveMode}:
            new = ReserveMode(value)
            # A mass and a fraction are not interchangeable.
            keep = s.reserve_value if new is s.reserve_mode else None
            return self._update(branch, replace(s, reserve_mode=new, reserve_value=keep))
        mode_key = name.removesuffix("_mode")
        if name.endswith("_mode") and value in {m.value for m in TermMode}:
            if mode_key in _TERMS:
                return self._update(branch, replace(s, **{_TERMS[mode_key][0]: TermMode(value)}))
            if mode_key in s.allowance_modes:
                return self._update(branch, replace(
                    s, allowance_modes={**s.allowance_modes, mode_key: TermMode(value)}))
        return False

    def _sections(self, basis):
        sections = []
        for branch in (Branch.OXIDISER, Branch.FUEL):
            s = self._settings[branch]
            b = branch.value
            propellant = basis.propellant_of(branch) if basis is not None else ""
            title = ("Oxidiser" if branch is Branch.OXIDISER else "Fuel") + (
                f" · {propellant}" if propellant else "")
            fields = [
                choice_field(f"{b}.residual_mode", "Unavailable propellant", _RESIDUAL_OPTIONS,
                             s.residual_mode.value,
                             note="Expulsion efficiency covers tank and piping (Sutton §6.2)"),
                number_field(f"{b}.expulsion_efficiency", "Expulsion efficiency η", "%",
                             s.expulsion_efficiency, _PERCENT,
                             visible=s.residual_mode is ResidualMode.EXPULSION_EFFICIENCY),
            ]
            residual = s.residual_mode is ResidualMode.RESIDUAL_MASS
            for name in ("tank_residual", "trapped_line"):
                mode_attr, value_attr, label = _TERMS[name]
                mode = getattr(s, mode_attr)
                fields.append(choice_field(f"{b}.{name}_mode", label, _TERM_OPTIONS,
                                           mode.value, visible=residual))
                fields.append(number_field(f"{b}.{name}", label, "kg", getattr(s, value_attr),
                                           visible=residual and mode is TermMode.STATED))
            fields.append(choice_field(f"{b}.reserve_mode", "Reserve", _RESERVE_OPTIONS,
                                       s.reserve_mode.value))
            fraction = s.reserve_mode is ReserveMode.STATED_FRACTION
            fields.append(number_field(
                f"{b}.reserve", "Reserve" + (" fraction" if fraction else " mass"),
                "%" if fraction else "kg", s.reserve_value, _PERCENT if fraction else 1.0,
                visible=s.reserve_mode in (ReserveMode.STATED_MASS,
                                           ReserveMode.STATED_FRACTION)))
            for key, label, _basis in ALLOWANCE_TERMS:
                mode = s.allowance_modes[key]
                fields.append(choice_field(f"{b}.{key}_mode", label, _TERM_OPTIONS, mode.value))
                fields.append(number_field(f"{b}.{key}", label, "kg", s.allowance_values[key],
                                           visible=mode is TermMode.STATED))
            mode_attr, value_attr, label = _TERMS["boiloff"]
            fields.append(choice_field(f"{b}.boiloff_mode", label, _TERM_OPTIONS,
                                       s.boiloff_mode.value))
            fields.append(number_field(f"{b}.boiloff", label, "kg", s.boiloff,
                                       visible=s.boiloff_mode is TermMode.STATED))
            sections.append({"key": b, "title": title, "wide": False,
                             "note": "Unresolved is never counted as zero.",
                             "fields": fields, "actions": []})
        return sections

    def _basis_rows(self, basis):
        return [
            {"label": "Propellant", "value": f"{basis.pair_label} · trade"},
            {"label": "O/F", "value": f"{basis.oxidiser_fuel_ratio:g} · trade"},
            {"label": "Oxidiser flow",
             "value": f"{basis.oxidiser_mass_flow:.5g} kg/s {basis.oxidiser} · sizing"},
            {"label": "Fuel flow",
             "value": f"{basis.fuel_mass_flow:.5g} kg/s {basis.fuel} · sizing"},
            {"label": "Burn time", "value": f"{basis.burn_time:g} s · requirement"},
            {"label": "Sizing", "value": basis.sizing.fingerprint[:12]},
        ]

    def _branch_view(self, outcome):
        return service.branch_view(outcome)

    def _total_rows(self, result):
        return service.total_rows(result)

    def _computed_message(self, definition, result):
        if result.status.value == "incomplete":
            return "Computed; the load waits on unresolved terms"
        return f"Computed for {definition.basis.burn_time:g} s"
