"""Bipropellant presets: the Sutton & Biblarz Table 5-5 combinations. Qt-free.

A preset is an **engineering convenience over the real model**, never a second
model. Choosing one sets three inputs the user could have set by hand -- the
oxidiser, the fuel and the O/F -- and moves each stream to its reactant's own
reference temperature, exactly as picking that reactant by hand does. It solves
nothing, carries no performance number, and owns no chemistry: what a reactant
*is* (its CEA identity, its mixture fractions and their basis) lives on the
reactant definition in ``rocketforge.providers.cea.propellants``.

**Source.** G. P. Sutton and O. Biblarz, *Rocket Propulsion Elements*, 9th ed.,
Wiley, 2017, Table 5-5, "Theoretical Chamber Performance of Liquid Rocket
Propellant Combinations" (1000 psia chamber, optimum expansion to 1 atm). The
table lists fourteen combinations. Only one number per combination is carried
here: the O/F, which the table notes is "for approximate maximum values of
Is". Where Table 5-5 gives two rows, the preset uses the row for
shifting-equilibrium Isp, because the chamber this workspace solves is an
equilibrium state. LF2/N2H4 is the one pair where Table 5-5 places its two Isp
values in the opposite columns from what CEA reproduces (its "shifting 334" at
O/F 1.83 is the frozen figure, its "frozen 365" at 2.30 the shifting one), so
its preset uses 2.30. The comparison against the rest of the table belongs to
the tests, not to runtime data.

**Two combinations are listed and not executable.** Red fuming nitric acid has
no composition in Table 5-5: Sutton describes RFNA only as nitric acid with "5
to 20 %" (Table 7-1, note a) or "5 to 27 %" (section 7.2) dissolved NO2, and
states no water content. NASA CEA's database holds no RFNA, and its ``IRFNA``
entry is the fluoride-inhibited acid Sutton names as a separate substance (its
record contains fluorine). Solving IRFNA and calling it RFNA would put a number
on a substance nobody specified, so both RFNA presets carry a blocker instead.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "BipropellantPreset",
    "SUTTON_TABLE_5_5",
    "SUTTON_SOURCE",
    "RFNA_BLOCKER",
    "catalogue_note",
    "preset_catalogue",
    "executable_presets",
    "preset_named",
    "preset_matching",
]

SUTTON_SOURCE = ("Sutton & Biblarz, Rocket Propulsion Elements, 9th ed. (2017), "
                 "Table 5-5")

RFNA_BLOCKER = (
    "Red fuming nitric acid has no stated composition in Sutton Table 5-5 "
    "(only 5-20 % or 5-27 % dissolved NO2, no water content), and NASA CEA "
    "3.3.4 holds no RFNA. Its IRFNA entry is the fluoride-inhibited acid, a "
    "different substance, and is not substituted.")


@dataclass(frozen=True, slots=True)
class BipropellantPreset:
    """One source combination, by name, and how to set it up -- if it can be.

    Attributes:
        key: Stable identifier.
        oxidiser_label / fuel_label: The source's own names for the pair.
        oxidiser / fuel: Catalogue keys of the reactant definitions, or empty
            for a blocked preset. Never a provider name: the definition owns
            that.
        oxidiser_fuel_ratio: O/F **by mass**, as the source states it, or
            ``None`` for a blocked preset.
        blocker: Why the combination cannot be represented, or empty.
        source: Where the combination and its O/F come from.
    """

    key: str
    oxidiser_label: str
    fuel_label: str
    oxidiser: str = ""
    fuel: str = ""
    oxidiser_fuel_ratio: float | None = None
    blocker: str = ""
    source: str = SUTTON_SOURCE

    @property
    def executable(self) -> bool:
        return not self.blocker

    @property
    def label(self) -> str:
        return f"{self.oxidiser_label} / {self.fuel_label}"


def _preset(key: str, ox_label: str, fuel_label: str, ox: str, fuel: str,
            of: float) -> BipropellantPreset:
    return BipropellantPreset(key=key, oxidiser_label=ox_label,
                              fuel_label=fuel_label, oxidiser=ox, fuel=fuel,
                              oxidiser_fuel_ratio=of)


#: The fourteen Table 5-5 combinations, in the table's own order.
SUTTON_TABLE_5_5: tuple[BipropellantPreset, ...] = (
    _preset("sutton-o2-ch4", "Oxygen", "Methane", "LOX", "LCH4", 3.00),
    _preset("sutton-o2-n2h4", "Oxygen", "Hydrazine", "LOX", "N2H4", 0.90),
    _preset("sutton-o2-h2", "Oxygen", "Hydrogen", "LOX", "LH2", 4.02),
    _preset("sutton-o2-rp1", "Oxygen", "RP-1", "LOX", "RP-1", 2.24),
    _preset("sutton-o2-udmh", "Oxygen", "UDMH", "LOX", "UDMH", 1.65),
    _preset("sutton-f2-n2h4", "Fluorine", "Hydrazine", "LF2", "N2H4", 2.30),
    _preset("sutton-f2-h2", "Fluorine", "Hydrogen", "LF2", "LH2", 7.60),
    _preset("sutton-nto-n2h4", "Nitrogen tetroxide", "Hydrazine",
            "NTO", "N2H4", 1.34),
    _preset("sutton-nto-a50", "Nitrogen tetroxide",
            "50 % UDMH + 50 % hydrazine", "NTO", "A-50", 2.00),
    _preset("sutton-nto-rp1", "Nitrogen tetroxide", "RP-1", "NTO", "RP-1", 3.4),
    _preset("sutton-nto-mmh", "Nitrogen tetroxide", "MMH", "NTO", "MMH", 2.15),
    BipropellantPreset(key="sutton-rfna-rp1",
                       oxidiser_label="Red fuming nitric acid", fuel_label="RP-1",
                       blocker=RFNA_BLOCKER),
    BipropellantPreset(key="sutton-rfna-a50",
                       oxidiser_label="Red fuming nitric acid",
                       fuel_label="50 % UDMH + 50 % hydrazine",
                       blocker=RFNA_BLOCKER),
    _preset("sutton-htp90-rp1", "Hydrogen peroxide (90 %)", "RP-1",
            "HTP-90", "RP-1", 7.0),
)


def preset_catalogue() -> tuple[BipropellantPreset, ...]:
    """Every source combination, executable or not, in source order."""
    return SUTTON_TABLE_5_5


def executable_presets() -> tuple[BipropellantPreset, ...]:
    """The combinations this build can actually solve."""
    return tuple(preset for preset in SUTTON_TABLE_5_5 if preset.executable)


def preset_named(key: str) -> BipropellantPreset | None:
    for preset in SUTTON_TABLE_5_5:
        if preset.key == key:
            return preset
    return None


def catalogue_note() -> str:
    """A short line for the selector: the source, and what it withholds.

    Short on purpose -- it sits in the input rail above the reactants. The
    full reason for each withheld pair is :data:`RFNA_BLOCKER`, shown on hover.
    """
    note = "Sutton & Biblarz Table 5-5 · O/F for approx. max Isp"
    if any(not preset.executable for preset in SUTTON_TABLE_5_5):
        note += " · RFNA pairs not offered (composition unstated)"
    return note


def preset_matching(oxidiser: str, fuel: str,
                    oxidiser_fuel_ratio: float) -> BipropellantPreset | None:
    """The executable preset a form currently describes, or ``None``.

    Exact: an O/F edited away from the preset's is a custom case, and the
    selector should say so rather than keep a name the inputs no longer match.
    """
    for preset in executable_presets():
        if (preset.oxidiser == oxidiser and preset.fuel == fuel
                and preset.oxidiser_fuel_ratio == oxidiser_fuel_ratio):
            return preset
    return None
