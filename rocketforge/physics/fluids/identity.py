"""What a fluid *is*, independently of who can compute it.

A fluid's domain identity is not a provider's spelling of it. CoolProp calls
liquid oxygen ``"Oxygen"`` and would also answer to ``"O2"`` and
``"HEOS::Oxygen"``; NASA CEA calls it ``"O2(L)"`` and means something different
by ``"O2"``. If any of those strings were the canonical identity, changing
provider would change the substance.

So the domain says ``OXYGEN``, and the mapping from that to a provider's
spelling lives inside the provider -- the same arrangement
``PropellantDefinition.provider_names`` already uses for thermochemistry.
"""

from __future__ import annotations

import math

from dataclasses import dataclass

from .errors import FluidIdentityError

__all__ = [
    "FluidDefinition",
    "OXYGEN",
    "METHANE",
    "HYDROGEN",
]


@dataclass(frozen=True, slots=True)
class FluidDefinition:
    """A pure fluid, named canonically.

    Attributes:
        name: RocketForge's canonical identifier, upper case, e.g. ``"OXYGEN"``.
            A *substance*, with no phase attached: phase belongs to a state.
        formula: The chemical formula, e.g. ``"O2"``. Recorded for provenance
            and for a caller that needs to reason about elements; it is **not**
            an identity that a provider is looked up by.
        molar_mass: kg/mol. Carried because a mass-basis package that has to
            reach for a molar mass at the call site invites the mole/mass
            confusion this package exists to avoid.
        source: Where the molar mass came from.

    Deliberately absent: a density, a boiling point, a critical point, a
    viscosity. Those are *properties at a state*, and a definition that carried
    one would be a second source of truth competing with the provider.
    """

    name: str
    formula: str
    molar_mass: float
    source: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise FluidIdentityError(
                f"fluid name must be a non-empty string, got {self.name!r}")
        if self.name != self.name.upper():
            raise FluidIdentityError(
                f"fluid name {self.name!r} must be upper case. The canonical "
                "identity is a domain constant, and a case-varying one invites "
                "two records for one substance.")
        if not isinstance(self.formula, str) or not self.formula.strip():
            raise FluidIdentityError(
                f"fluid {self.name!r} must state a formula")
        try:
            mass = float(self.molar_mass)
        except (TypeError, ValueError) as exc:
            raise FluidIdentityError(
                f"molar mass of {self.name!r} must be a real number, "
                f"got {self.molar_mass!r}") from exc
        if not math.isfinite(mass) or mass <= 0.0:
            raise FluidIdentityError(
                f"molar mass of {self.name!r} must be finite and above zero, "
                f"got {mass!r}. This package works in kg/mol; a value near 32 "
                "would be g/mol and wrong by a thousand.")
        if mass > 1.0:
            raise FluidIdentityError(
                f"molar mass of {self.name!r} is {mass!r} kg/mol, which is "
                "above 1 kg/mol. This is almost certainly g/mol: the unit here "
                "is kg/mol, so oxygen is 0.0319988, not 31.9988.")


_CODATA = ("IUPAC/CIAAW standard atomic weights 2021, combined to the "
           "molecular formula")

#: Oxygen. The oxidiser in every production propellant pair this project ships.
OXYGEN = FluidDefinition(name="OXYGEN", formula="O2",
                         molar_mass=0.0319988, source=_CODATA)

#: Methane.
METHANE = FluidDefinition(name="METHANE", formula="CH4",
                          molar_mass=0.0160425, source=_CODATA)

#: Hydrogen.
HYDROGEN = FluidDefinition(name="HYDROGEN", formula="H2",
                           molar_mass=0.00201588, source=_CODATA)
