"""Propellant management: what keeps liquid at the tank outlet, and the volumes.

Sutton & Biblarz, *Rocket Propulsion Elements*, 9th ed., section 6.2
(pp. 199-203):

* "In the gravity-free environment of space, stored liquids will float around
  in a partly emptied tank and may not always cover the tank outlet";
* the remedies are "positive expulsion devices" -- "movable pistons,
  inflatable flexible bladders, or thin movable and flexible metal
  diaphragms" -- and "surface tension devices", which "work best in
  relatively low-acceleration environments"; "Alternatively, a small
  acceleration may be applied in a zero-g space environment (using
  supplementary thrusters) in order to orient the liquid propellant";
* Table 6-2 compares the devices qualitatively ("Excellent", "Very good",
  "Good", "Poor") for one application, hydrazine spacecraft tanks.

**This module states intent and checks it for consistency. It proves
nothing.** No device performance is computed: no expulsion efficiency is
derived from a device type (Table 6-2 is qualitative and application-bound),
no capillary retention, screen bubble point, diaphragm stress or settling time
is evaluated, and no slosh dynamics are modelled. An outlet-availability state
here is a declaration with its basis, never a demonstration; in low gravity
nothing here claims the outlet is covered.

**Volumes** (one tank, one storage density rho)::

    V_present  = m_present / rho          liquid at the start of the burn
    V_gas,0    = V_tank - V_present       gas at the start (ullage + boil-off space)
    V_expelled = m_available / rho        leaves the tank during the burn
    V_gas,end  = V_gas,0 + V_expelled     = V_tank - m_residual / rho
    V_residual = m_residual / rho         taken to remain in the tank

SI: kg, kg/m^3, m^3, m/s^2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from rocketforge.core.result import Diagnostic, Severity, Solution, Status

__all__ = [
    "Availability",
    "Environment",
    "ManagementMode",
    "ManagementState",
    "ManagementVolumes",
    "SettlingIntent",
    "management_state",
    "management_volumes",
]


class ManagementMode(StrEnum):
    SETTLED = "settled"                  # free surface, settled by acceleration
    DIAPHRAGM = "diaphragm"
    BLADDER = "bladder"
    PISTON = "piston"
    BELLOWS = "bellows"
    SURFACE_TENSION = "surface_tension"  # screens, vanes, sumps: a PMD

    @property
    def positive_expulsion(self) -> bool:
        return self in (ManagementMode.DIAPHRAGM, ManagementMode.BLADDER,
                        ManagementMode.PISTON, ManagementMode.BELLOWS)


class Environment(StrEnum):
    ACCELERATED = "accelerated"          # thrust or another acceleration acts throughout
    LOW_GRAVITY = "low_gravity"          # coast or zero-g phases before or between burns
    UNRESOLVED = "unresolved"


class SettlingIntent(StrEnum):
    REQUIRED = "required"                # settling acceleration is part of the design intent
    NOT_REQUIRED = "not_required"
    UNRESOLVED = "unresolved"


class Availability(StrEnum):
    """Outlet coverage as declared. Never a demonstration."""

    DECLARED_DEVICE = "declared_device"            # a positive-expulsion device separates gas
    DECLARED_SETTLED = "declared_settled"          # free surface under a stated acceleration
    REQUIRES_SETTLING = "requires_settling"        # covered only while settling acts
    DECLARED_CAPILLARY = "declared_capillary"      # retained by a PMD, not evaluated
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class ManagementState:
    availability: Availability
    statement: str                       # what the declaration rests on
    advisories: tuple[str, ...]


def management_state(mode: ManagementMode, environment: Environment,
                     settling: SettlingIntent) -> Solution[ManagementState]:
    """The outlet-availability declaration for a stated mode and environment.

    A free surface in low gravity with no settling intended is a contradiction
    and is refused: nothing would keep the outlet covered.
    """
    for value, kind in ((mode, ManagementMode), (environment, Environment),
                        (settling, SettlingIntent)):
        if not isinstance(value, kind):
            raise ValueError(f"{value!r} is not a {kind.__name__}")
    advisories: list[str] = []
    if environment is Environment.UNRESOLVED:
        return Solution(value=ManagementState(
            Availability.UNRESOLVED,
            "The acceleration environment is not stated, so outlet coverage is unresolved.",
            ()), status=Status.OK)
    if mode is ManagementMode.SETTLED:
        if environment is Environment.ACCELERATED:
            if settling is SettlingIntent.REQUIRED:
                advisories.append("Settling is stated as required although the stated "
                                  "environment is accelerated throughout; both are recorded.")
            return Solution(value=ManagementState(
                Availability.DECLARED_SETTLED,
                "Free surface settled by the stated acceleration; slosh and vortexing, which "
                "Sutton §6.2 notes can uncover the outlet, are not modelled.",
                tuple(advisories)), status=Status.OK)
        if settling is SettlingIntent.NOT_REQUIRED:
            return Solution(value=None, status=Status.NO_SOLUTION, diagnostics=(Diagnostic(
                code="FREE_SURFACE_UNSETTLED", severity=Severity.ERROR,
                message=("A settled free surface in low gravity with no settling acceleration "
                         "has nothing to keep the outlet covered (Sutton §6.2). State settling "
                         "as required, or a propellant-management device."),
                field="settling"),))
        if settling is SettlingIntent.UNRESOLVED:
            return Solution(value=ManagementState(
                Availability.UNRESOLVED,
                "A free surface in low gravity needs a settling acceleration, and whether one "
                "is intended is not stated.", ()), status=Status.OK)
        return Solution(value=ManagementState(
            Availability.REQUIRES_SETTLING,
            "The outlet is covered only while a settling acceleration acts (Sutton §6.2); its "
            "magnitude and duration are not evaluated.", ()), status=Status.OK)
    if mode.positive_expulsion:
        return Solution(value=ManagementState(
            Availability.DECLARED_DEVICE,
            f"A {mode.value} separates the pressurant from the liquid (Sutton §6.2, Table 6-2). "
            "Its expulsion performance, stress and fatigue are not evaluated.", ()),
            status=Status.OK)
    if environment is Environment.ACCELERATED:
        advisories.append("Surface-tension devices work best in relatively low-acceleration "
                          "environments (Sutton §6.2); retention under the stated acceleration "
                          "is not evaluated.")
    return Solution(value=ManagementState(
        Availability.DECLARED_CAPILLARY,
        "Retention by a surface-tension device is declared. Capillary retention, screen bubble "
        "point and gallery design are not evaluated, and low-gravity feed is not claimed.",
        tuple(advisories)), status=Status.OK)


@dataclass(frozen=True, slots=True)
class ManagementVolumes:
    tank_volume: float
    liquid_volume_loaded: float
    liquid_volume_present: float
    gas_volume_start: float
    expelled_volume: float
    gas_volume_end: float
    residual_volume: float
    ullage_fraction_start: float
    ullage_fraction_end: float
    volume_closure: float          # (V_gas,end + V_residual) / V_tank - 1


def _finite(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def management_volumes(tank_volume: float, density: float, loaded_mass: float,
                       present_mass: float, available_mass: float, residual_mass: float
                       ) -> Solution[ManagementVolumes]:
    """The liquid and gas volumes from loading through the end of the burn."""
    for name, value in (("tank_volume", tank_volume), ("density", density),
                        ("loaded_mass", loaded_mass), ("present_mass", present_mass),
                        ("available_mass", available_mass)):
        if not (_finite(value) and value > 0.0):
            return Solution(value=None, status=Status.NO_SOLUTION, diagnostics=(Diagnostic(
                code=f"{name.upper()}_INVALID", severity=Severity.ERROR,
                message=f"The {name.replace('_', ' ')} must be finite and above zero.",
                field=name),))
    if not (_finite(residual_mass) and residual_mass >= 0.0):
        return Solution(value=None, status=Status.NO_SOLUTION, diagnostics=(Diagnostic(
            code="RESIDUAL_MASS_INVALID", severity=Severity.ERROR,
            message="The residual mass must be finite and at or above zero.",
            field="residual_mass"),))
    if present_mass > loaded_mass * (1.0 + 1e-12):
        raise ValueError("more propellant present than loaded")
    loaded_v = loaded_mass / density
    if loaded_v > tank_volume * (1.0 + 1e-12):
        return Solution(value=None, status=Status.NO_SOLUTION, diagnostics=(Diagnostic(
            code="TANK_OVERFILLED", severity=Severity.ERROR,
            message="The loaded liquid does not fit the tank volume.",
            field="tank_volume"),))
    present_v = present_mass / density
    gas_start = tank_volume - present_v
    expelled = available_mass / density
    residual_v = residual_mass / density
    gas_end = gas_start + expelled
    return Solution(value=ManagementVolumes(
        tank_volume=tank_volume, liquid_volume_loaded=loaded_v, liquid_volume_present=present_v,
        gas_volume_start=gas_start, expelled_volume=expelled, gas_volume_end=gas_end,
        residual_volume=residual_v, ullage_fraction_start=gas_start / tank_volume,
        ullage_fraction_end=gas_end / tank_volume,
        volume_closure=(gas_end + residual_v) / tank_volume - 1.0), status=Status.OK)
