"""What every 1985 TDK printout held as a case shares (DB-4C): the keys, the point record, the code description.

TDK (Two-Dimensional Kinetics, Software and Engineering Associates) prints a
performance summary whose ISP (ODE) and ISP (ODF) are one-dimensional ideal
vacuum values, the second frozen at the chamber composition (DB-4C §2). A case
records three quantities of a summary's first solution, the one with no heat
added to the propellant. Each source module, :mod:`.ssme_tdk_1985` and
:mod:`.tdk_manual_1985`, holds its own cases and the numeric inputs they were
run at. No case here draws a verdict: TDK is an independent code.
"""

from __future__ import annotations

from dataclasses import dataclass

from rocketforge.physics.thermochemistry import ExpansionMode

from .cases import ReferenceCase, ReferenceQuantity

__all__ = [
    "KEY_CHAMBER_TEMPERATURE",
    "KEY_VACUUM_ISP_EQUILIBRIUM",
    "KEY_VACUUM_ISP_FROZEN",
    "CODE",
    "CODE_VERSION",
    "EXPANSION",
    "FIRST_SOLUTION",
    "not_recorded",
    "tdk_quantities",
    "TdkPoint",
]

KEY_CHAMBER_TEMPERATURE = "chamber_temperature"
#: The expansion model is part of the key, as a composition basis is part of a
#: fraction's: a shifting value can never be compared with a frozen one.
KEY_VACUUM_ISP_EQUILIBRIUM = f"vacuum_specific_impulse:{ExpansionMode.EQUILIBRIUM.value}"
KEY_VACUUM_ISP_FROZEN = f"vacuum_specific_impulse:{ExpansionMode.FROZEN.value}"

CODE = "TDK (Two-Dimensional Kinetics), ODE module; Software and Engineering Associates"
CODE_VERSION = "not stated (the 1985 program with the shock option)"
EXPANSION = ("one-dimensional, isentropic, vacuum; ODE in equilibrium, ODF frozen at the chamber "
             "composition (DB-4C §2)")
FIRST_SOLUTION = "the first TDK/BLM solution: no heat added to the propellant (DELH = 0, DELH1 = 0)"


def not_recorded(delh1_btu_per_lb: str) -> str:
    """What a TDK summary prints that a case leaves out, with the second solution's printed heat."""
    return ("Not recorded: ISP (ODK) (kinetics); ISP (TDK), ISP (TC), CSTAR (TDK), CF (TDK) and CD "
            "(two-dimensional flow and boundary layer); every second-solution value (regenerative heat added "
            f"to the propellant, DELH1 {delh1_btu_per_lb} BTU/lb); HCHAM (ODE), an input consequence.")


def tdk_quantities(where: str, temperature_r: float, isp_equilibrium: float, isp_frozen: float,
                   ) -> tuple[ReferenceQuantity, ...]:
    """The three quantities of a summary's first solution, as printed: CHAMBER TEMP, ISP (ODE), ISP (ODF)."""
    return (
        ReferenceQuantity(KEY_CHAMBER_TEMPERATURE, temperature_r, "R", decimals=3,
                          note=where + "; CHAMBER TEMP [R]"),
        ReferenceQuantity(KEY_VACUUM_ISP_EQUILIBRIUM, isp_equilibrium, "lbf*s/lbm", decimals=4,
                          note=where + "; ISP (ODE) [SECONDS], a vacuum value (DB-4C §2)"),
        ReferenceQuantity(KEY_VACUUM_ISP_FROZEN, isp_frozen, "lbf*s/lbm", decimals=4,
                          note=where + "; ISP (ODF) [SECONDS], a vacuum value, frozen at the chamber (DB-4C §2)"),
    )


@dataclass(frozen=True, slots=True)
class TdkPoint:
    """A case with the model inputs its summary was run at, in the source's units.

    ``printed_nozzle_area_ratio`` is the summary's EP (NOZZLE), and the two card
    temperatures are what the H2(L) and O2(L) reactant cards print beside their
    enthalpies, in K. All three are recorded and declared, never used.
    ``catalog_link`` says what the point is, or is not, in the engine catalog.
    ``conventions_source`` says where its vacuum and frozen-at-chamber readings
    come from.
    """

    case: ReferenceCase
    chamber_pressure_psia: float
    oxidiser_fuel_ratio: float
    area_ratio: float
    printed_nozzle_area_ratio: float
    fuel_card_temperature: str
    oxidiser_card_temperature: str
    catalog_link: str
    conventions_source: str
