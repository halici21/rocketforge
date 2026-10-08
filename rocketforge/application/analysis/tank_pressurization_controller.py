"""The QObject the Tank Pressurization page binds to (SYS-4).

It reads the Propellant Management controller and, for a required pressure
taken from LIQ-6, the Injector controller. It holds each branch's stated
pressurization and computes only from :meth:`compute`. Pressures are typed in
bar, temperatures in K, the gas constant in J/(kg K), masses in kg and a
reserve fraction in percent; everything below is SI.
"""

from __future__ import annotations

from dataclasses import replace

from rocketforge.engine.propulsion_system.pressurization import (
    PressurantReserve,
    PressurizationMode,
    RequiredSource,
    TankGasTemperature,
    UllageSource,
)
from rocketforge.engine.propulsion_system.records import Branch

from . import tank_pressurization_service as service
from .system_study_controller import (
    SystemStudyController,
    choice_field,
    number_field,
    text_field,
)

__all__ = ["TankPressurizationController"]

_BAR = 1.0e5
_PERCENT = 0.01
_NUMBERS = {"gas_constant": 1.0, "exponent": 1.0, "required_pressure": _BAR,
            "tank_pressure": _BAR, "tank_gas_temperature": 1.0,
            "bottle_initial_pressure": _BAR, "bottle_initial_temperature": 1.0,
            "bottle_final_pressure": _BAR, "initial_pressure": _BAR,
            "initial_temperature": 1.0}
_MODES = [("", "Not stated"), ("regulated", "Regulated stored gas"), ("blowdown", "Blowdown"),
          ("autogenous_intent", "Autogenous (intent only)"),
          ("warm_gas_intent", "Warm / engine gas (intent only)")]
_REQUIRED = [("unresolved", "Unresolved"), ("stated", "Stated"),
             ("injector", "From the injector ledger (LIQ-6)")]
_TANK_GAS = [("", "Not stated"), ("stated", "Stated"),
             ("bottle_initial", "Tp = T0 (Eq. 6-7)"), ("bottle_final", "Tp = Tg (Example 6-2)")]
_ULLAGE = [("", "Not stated"), ("ground", "Pre-pressurized"), ("bottle", "Filled from the bottle")]
_RESERVE = [("unresolved", "Unresolved"), ("not_applicable", "Not applicable"),
            ("stated_mass", "Stated mass"), ("stated_fraction", "Fraction of m0")]


class TankPressurizationController(SystemStudyController):
    """Application-side facade for the Tank Pressurization page."""

    def __init__(self, management_source, injector_source, parent=None) -> None:
        self._management = management_source
        self._injector = injector_source
        self._settings = {Branch.OXIDISER: service.BranchSettings(),
                          Branch.FUEL: service.BranchSettings()}
        SystemStudyController.__init__(self, (management_source, injector_source), parent)

    def _basis(self):
        return service.pressurization_basis(self._management.result(),
                                            bool(self._management.property("resultStale")))

    def _build(self, basis):
        return service.build_definition(basis, self._settings[Branch.OXIDISER],
                                        self._settings[Branch.FUEL], self._injector.result(),
                                        bool(self._injector.property("resultStale")))

    def _solve(self, definition):
        return service.solve_pressurization(definition)

    def _update(self, branch, settings) -> bool:
        if settings == self._settings[branch]:
            return False
        self._settings[branch] = settings
        return True

    def _apply_number(self, branch, name, value):
        if branch is None:
            return False
        s = self._settings[branch]
        if name == "reserve":
            scale = _PERCENT if s.reserve_mode is PressurantReserve.STATED_FRACTION else 1.0
            return self._update(branch, replace(
                s, reserve_value=None if value is None else value * scale))
        if name in _NUMBERS:
            return self._update(branch, replace(
                s, **{name: None if value is None else value * _NUMBERS[name]}))
        return False

    def _apply_text(self, branch, name, text):
        if branch is None or name != "gas_name":
            return False
        return self._update(branch, replace(self._settings[branch], gas_name=text))

    def _apply_choice(self, branch, name, value):
        if branch is None:
            return False
        s = self._settings[branch]
        enums = {"mode": (PressurizationMode, _MODES, True),
                 "required_source": (RequiredSource, _REQUIRED, False),
                 "tank_gas_temperature_mode": (TankGasTemperature, _TANK_GAS, True),
                 "ullage_source": (UllageSource, _ULLAGE, True),
                 "reserve_mode": (PressurantReserve, _RESERVE, False)}
        if name not in enums:
            return False
        kind, options, optional = enums[name]
        if value not in {k for k, _l in options}:
            return False
        new = kind(value) if value else None
        changes = {name: new}
        if name == "reserve_mode" and new is not s.reserve_mode:
            changes["reserve_value"] = None        # a mass and a fraction differ
        return self._update(branch, replace(s, **changes))

    def _sections(self, basis):
        sections = []
        for branch in (Branch.OXIDISER, Branch.FUEL):
            s = self._settings[branch]
            b = branch.value
            regulated = s.mode is PressurizationMode.REGULATED
            blowdown = s.mode is PressurizationMode.BLOWDOWN
            executable = regulated or blowdown
            fraction = s.reserve_mode is PressurantReserve.STATED_FRACTION
            fields = [
                choice_field(f"{b}.mode", "Pressurization", _MODES,
                             s.mode.value if s.mode else ""),
                choice_field(f"{b}.required_source", "Required tank pressure", _REQUIRED,
                             s.required_source.value),
                number_field(f"{b}.required_pressure", "Required tank pressure", "bar",
                             s.required_pressure, _BAR,
                             visible=s.required_source is RequiredSource.STATED),
                text_field(f"{b}.gas_name", "Pressurant", s.gas_name, visible=executable,
                           note="Named as stated; no gas is assumed."),
                number_field(f"{b}.gas_constant", "Gas constant R", "J/(kg·K)", s.gas_constant,
                             visible=executable),
                number_field(f"{b}.exponent", "Expansion exponent n", "", s.exponent,
                             visible=executable, note="1 is isothermal; at most k (Sutton §6.5)"),
                number_field(f"{b}.tank_pressure", "Regulated tank pressure pp", "bar",
                             s.tank_pressure, _BAR, visible=regulated),
                choice_field(f"{b}.tank_gas_temperature_mode", "Tank gas temperature",
                             _TANK_GAS, (s.tank_gas_temperature_mode.value
                                         if s.tank_gas_temperature_mode else ""),
                             visible=regulated),
                number_field(f"{b}.tank_gas_temperature", "Tank gas temperature Tp", "K",
                             s.tank_gas_temperature,
                             visible=regulated and s.tank_gas_temperature_mode
                             is TankGasTemperature.STATED),
                number_field(f"{b}.bottle_initial_pressure", "Bottle pressure p0", "bar",
                             s.bottle_initial_pressure, _BAR, visible=regulated),
                number_field(f"{b}.bottle_initial_temperature", "Bottle temperature T0", "K",
                             s.bottle_initial_temperature, visible=regulated),
                number_field(f"{b}.bottle_final_pressure", "Bottle pressure at the end pg",
                             "bar", s.bottle_final_pressure, _BAR, visible=regulated),
                choice_field(f"{b}.ullage_source", "Start ullage", _ULLAGE,
                             s.ullage_source.value if s.ullage_source else "",
                             visible=regulated),
                choice_field(f"{b}.reserve_mode", "Pressurant reserve", _RESERVE,
                             s.reserve_mode.value, visible=regulated),
                number_field(f"{b}.reserve", "Reserve" + (" fraction" if fraction else " mass"),
                             "%" if fraction else "kg", s.reserve_value,
                             _PERCENT if fraction else 1.0,
                             visible=regulated and s.reserve_mode in (
                                 PressurantReserve.STATED_MASS,
                                 PressurantReserve.STATED_FRACTION)),
                number_field(f"{b}.initial_pressure", "Initial tank pressure", "bar",
                             s.initial_pressure, _BAR, visible=blowdown),
                number_field(f"{b}.initial_temperature", "Initial gas temperature", "K",
                             s.initial_temperature, visible=blowdown),
            ]
            propellant = basis.propellant_of(branch) if basis is not None else ""
            title = ("Oxidiser tank" if branch is Branch.OXIDISER else "Fuel tank") + (
                f" · {propellant}" if propellant else "")
            sections.append({"key": b, "title": title, "wide": False,
                             "note": "Perfect gas; autogenous and warm gas are intent only.",
                             "fields": fields, "actions": []})
        return sections

    def _basis_rows(self, basis):
        rows = [{"label": "Propellant", "value": basis.pair_label}]
        for branch, word in ((Branch.OXIDISER, "Oxidiser"), (Branch.FUEL, "Fuel")):
            g = basis.gas_of(branch)
            rows.append({"label": f"{word} gas",
                         "value": f"{g.gas_volume_start:,.5f} → {g.gas_volume_end:,.5f} m³"
                                  " · management"})
        rows.append({"label": "Management", "value": basis.management.fingerprint[:12]})
        return rows

    def _branch_view(self, outcome):
        return service.branch_view(outcome)

    def _total_rows(self, result):
        return service.total_rows(result)

    def _computed_message(self, definition, result):
        return {"warning": "Computed; a tank pressure is below its requirement",
                "incomplete": "Computed; a term is unresolved or intent only"}.get(
                    result.status.value, "Computed")
