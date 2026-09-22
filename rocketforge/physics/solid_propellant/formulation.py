"""Solid propellant formulations: what is loaded into the case, by mass.

A solid motor's chamber is posed to CEA differently from a bipropellant's, and
the difference is not cosmetic. A bipropellant chamber is set by a *ratio* of
two streams; a solid grain is a single pre-mixed material whose ingredients are
fixed at manufacture. There is no oxidiser stream, no fuel stream, and no O/F --
CEA itself reports ``o/f = 0.000`` for a solid case.

So this module does not reuse
:class:`~rocketforge.physics.thermochemistry.requests.ChamberEquilibriumRequest`.
That request requires a ``PropellantStream`` in the fuel role, a
``PropellantStream`` in the oxidiser role, and a ``MixtureRatio``; satisfying it
for a solid would mean inventing all three. An invented O/F is not a harmless
placeholder, because it is exactly the kind of value a reader would later quote.

**Why this lives outside** :mod:`rocketforge.physics.thermochemistry`.
``freeze_thermochemistry_api_v1`` byte-freezes every module in that package and
separately requires its manifest to cover the directory exactly, so a module
placed in there breaks the contract without a single frozen byte changing. See
``docs/engineering/design/SOLID_PROPELLANT_R1_ARCHITECTURE.md``.

Deliberately absent, and deferred to R1.1: every performance quantity. No c*,
no Cf, no Isp, no expansion of any kind. This module describes what is in the
chamber, not what the nozzle does with it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from rocketforge.physics.thermochemistry.errors import (
    PropellantError,
    ThermochemistryError,
)

__all__ = [
    "SolidFormulationError",
    "MassFractionSumError",
    "CustomReactant",
    "SolidIngredient",
    "SolidFormulation",
    "SolidFormulationEquilibriumRequest",
    "MASS_FRACTION_SUM_TOL",
]

#: How far a formulation's mass fractions may sum from 1.0 before it is refused.
#: Tight on purpose: this catches a typo, not a rounding artefact. NASA RP-1311
#: Example 5's five published fractions sum to exactly 1.0.
MASS_FRACTION_SUM_TOL = 1e-9

#: Enthalpy units CEA accepts for an assigned-enthalpy reactant.
_ENTHALPY_UNITS = ("cal/mol", "kcal/mol", "J/mol", "kJ/mol")


class SolidFormulationError(PropellantError):
    """A solid formulation or one of its ingredients is malformed."""


class MassFractionSumError(SolidFormulationError):
    """Ingredient mass fractions do not sum to one.

    Refused rather than normalised, for the same reason
    :class:`~rocketforge.physics.thermochemistry.errors.CompositionSumError`
    refuses: a formulation summing to 0.98 is far more likely to be a missing
    ingredient than a deliberate basis, and silently scaling it up would hide
    the omission behind a plausible chamber temperature.
    """


def _finite(value: object, what: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise SolidFormulationError(
            f"{what} must be a real number, got {value!r}") from exc
    if not math.isfinite(number):
        raise SolidFormulationError(f"{what} must be finite, got {number!r}")
    return number


@dataclass(frozen=True, slots=True)
class CustomReactant:
    """An ingredient defined by its elemental formula and assigned enthalpy.

    NASA's own solid examples define their binder this way, because a real
    polymer binder is not a library species and has no tabulated thermodynamic
    record. CEA accepts it as a reactant given a formula, a molecular weight,
    and a heat of formation assigned at a stated temperature.

    Attributes:
        formula: Element symbol -> atoms per formula unit. Fractional counts are
            normal here and not an error: a binder's formula is an average over
            a polymer, so ``H: 1.86955`` is meaningful.
        molecular_weight: g/mol of that formula unit.
        enthalpy: The assigned enthalpy, in :attr:`enthalpy_units`. Negative for
            almost every real ingredient and not checked for sign.
        enthalpy_units: The units ``enthalpy`` is stated in. Recorded rather
            than converted, because CEA takes the units alongside the value and
            converting here would add a rounding step nobody asked for.
        temperature: K. The temperature the enthalpy is assigned at. CEA uses
            the enthalpy at this temperature whatever reactant temperature a
            solve requests -- verified: a binder-only mixture returns the same
            enthalpy at 250, 298.15 and 320 K -- so a request at any other
            temperature is reported, never silently accepted.
        source: Where the definition comes from. Required: a custom reactant is
            thermochemical data RocketForge did not compute, and a result built
            on it is only as traceable as this string.
    """

    formula: Mapping[str, float]
    molecular_weight: float
    enthalpy: float
    enthalpy_units: str
    temperature: float
    source: str

    def __post_init__(self) -> None:
        if not isinstance(self.formula, Mapping) or not self.formula:
            raise SolidFormulationError(
                "a custom reactant needs a non-empty elemental formula; without "
                "one CEA has no way to balance the reaction")
        cleaned: dict[str, float] = {}
        for element, count in self.formula.items():
            if not isinstance(element, str) or not element.strip():
                raise SolidFormulationError(
                    f"element symbol must be a non-empty string, got {element!r}")
            atoms = _finite(count, f"atom count for {element!r}")
            if atoms <= 0.0:
                raise SolidFormulationError(
                    f"atom count for {element!r} must be strictly positive, got "
                    f"{atoms!r}. An element present at zero is an element the "
                    "formula should omit.")
            cleaned[element.strip()] = atoms
        object.__setattr__(self, "formula", MappingProxyType(cleaned))

        mw = _finite(self.molecular_weight, "molecular weight")
        if mw <= 0.0:
            raise SolidFormulationError(
                f"molecular weight must be strictly positive, got {mw!r} g/mol")
        object.__setattr__(self, "molecular_weight", mw)
        object.__setattr__(self, "enthalpy", _finite(self.enthalpy, "enthalpy"))

        if self.enthalpy_units not in _ENTHALPY_UNITS:
            raise SolidFormulationError(
                f"enthalpy_units must be one of {_ENTHALPY_UNITS}, got "
                f"{self.enthalpy_units!r}")

        temperature = _finite(self.temperature, "assigned-enthalpy temperature")
        if temperature <= 0.0:
            raise SolidFormulationError(
                f"assigned-enthalpy temperature must be strictly positive, got "
                f"{temperature!r} K")
        object.__setattr__(self, "temperature", temperature)

        if not isinstance(self.source, str) or not self.source.strip():
            raise SolidFormulationError(
                "a custom reactant must name its source. Its formula and "
                "assigned enthalpy are data RocketForge did not compute; "
                "without a source they cannot be checked or reproduced.")
        object.__setattr__(self, "source", self.source.strip())


@dataclass(frozen=True, slots=True)
class SolidIngredient:
    """One constituent of a solid grain, with the mass fraction it occupies.

    Attributes:
        name: The CEA library name (``"NH4CLO4(I)"``, ``"AL(cr)"``), or the
            label for a custom reactant. Kept verbatim: a phase suffix like
            ``(cr)`` or ``(I)`` is part of the identity, not decoration, and
            stripping it would change which record CEA looks up.
        mass_fraction: In ``[0, 1]``. A mass fraction, never a percent --
            percent is a presentation concern and is divided out at the UI
            boundary. Zero is allowed: an ingredient being dialled out of a
            grain is a legitimate intermediate state, and the formulation's
            own sum check still refuses a grain that does not close.
        custom: The assigned-enthalpy definition, when this ingredient is not a
            library species. ``None`` means "look this name up in CEA's library".
    """

    name: str
    mass_fraction: float
    custom: CustomReactant | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise SolidFormulationError(
                f"ingredient name must be a non-empty string, got {self.name!r}")
        object.__setattr__(self, "name", self.name.strip())

        fraction = _finite(self.mass_fraction, f"mass fraction for {self.name!r}")
        if not 0.0 <= fraction <= 1.0:
            raise SolidFormulationError(
                f"mass fraction for {self.name!r} must lie in [0, 1], got "
                f"{fraction!r}. A value above 1 is almost always a percent "
                "that was not divided by 100.")
        object.__setattr__(self, "mass_fraction", fraction)

        if self.custom is not None and not isinstance(self.custom, CustomReactant):
            raise SolidFormulationError(
                f"custom must be a CustomReactant or None, got "
                f"{type(self.custom).__name__}")

    @property
    def is_custom(self) -> bool:
        """Whether this ingredient carries its own assigned-enthalpy definition."""
        return self.custom is not None


@dataclass(frozen=True, slots=True)
class SolidFormulation:
    """A complete solid propellant grain composition, by mass.

    Ordering is part of the value. CEA takes the reactant list and the weight
    vector as two positional arrays, so the two must stay paired; holding the
    ingredients in a tuple is what makes that pairing impossible to disturb.

    Attributes:
        name: What this formulation is called.
        ingredients: Every constituent, summing to 1.0 by mass.
        initial_temperature: K. The grain's bulk temperature before ignition,
            which sets the reactant enthalpy the chamber balance starts from.
        reference: The published source, when this formulation is taken from
            one. Recorded so a validation case can cite where its numbers came
            from rather than appearing to be authored here.
    """

    name: str
    ingredients: tuple[SolidIngredient, ...]
    initial_temperature: float = 298.15
    reference: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise SolidFormulationError(
                f"formulation name must be a non-empty string, got {self.name!r}")
        object.__setattr__(self, "name", self.name.strip())

        if not isinstance(self.ingredients, tuple) or not self.ingredients:
            raise SolidFormulationError(
                "a formulation needs a non-empty tuple of ingredients")
        for item in self.ingredients:
            if not isinstance(item, SolidIngredient):
                raise SolidFormulationError(
                    f"every ingredient must be a SolidIngredient, got "
                    f"{type(item).__name__}")

        seen: set[str] = set()
        for item in self.ingredients:
            if item.name in seen:
                raise SolidFormulationError(
                    f"ingredient {item.name!r} appears twice. Two entries for one "
                    "reactant would be summed by CEA but reported separately here, "
                    "so they are refused rather than merged.")
            seen.add(item.name)

        total = math.fsum(item.mass_fraction for item in self.ingredients)
        if abs(total - 1.0) > MASS_FRACTION_SUM_TOL:
            raise MassFractionSumError(
                f"ingredient mass fractions must sum to 1.0 within "
                f"{MASS_FRACTION_SUM_TOL:g}, got {total!r} (off by "
                f"{total - 1.0:+.3e}). Refused rather than normalised: a "
                "formulation that does not close is more often a missing "
                "ingredient than a deliberate basis.")

        temperature = _finite(self.initial_temperature, "initial temperature")
        if temperature <= 0.0:
            raise SolidFormulationError(
                f"initial temperature must be strictly positive, got "
                f"{temperature!r} K")
        object.__setattr__(self, "initial_temperature", temperature)

        if self.reference is not None and (
                not isinstance(self.reference, str) or not self.reference.strip()):
            raise SolidFormulationError(
                f"reference must be a non-empty string or None, got "
                f"{self.reference!r}")

    @property
    def mass_fractions(self) -> tuple[float, ...]:
        """The weight vector, in ingredient order, as CEA wants it."""
        return tuple(item.mass_fraction for item in self.ingredients)

    @property
    def names(self) -> tuple[str, ...]:
        """The reactant names, in ingredient order."""
        return tuple(item.name for item in self.ingredients)

    @property
    def custom_ingredients(self) -> tuple[SolidIngredient, ...]:
        """Only the ingredients carrying their own assigned enthalpy."""
        return tuple(item for item in self.ingredients if item.is_custom)


@dataclass(frozen=True, slots=True)
class SolidFormulationEquilibriumRequest:
    """A request for the equilibrium chamber state of a solid formulation.

    The solid counterpart to
    :class:`~rocketforge.physics.thermochemistry.requests.ChamberEquilibriumRequest`,
    and deliberately *not* a subclass of it: the two share no substitutable
    contract, because that one's fuel stream, oxidiser stream and mixture ratio
    have no solid meaning. ``chamber_pressure`` carries the same name and the
    same units in both, so a call site reads the same way.

    Attributes:
        formulation: The grain composition.
        chamber_pressure: Pa, strictly positive and finite.
        product_species: Optional explicit product set. ``None`` means "derive
            the products from the reactants", which is what NASA's own solid
            examples do and is a real capability rather than a fallback.
        omit_species: Products to exclude. Published examples routinely omit
            species that are known not to form, and reproducing a published
            number requires reproducing its omissions.
        include_ions: Whether ionised products are considered. Off by default;
            a chamber at a few thousand kelvin has negligible ionisation.
    """

    formulation: SolidFormulation
    chamber_pressure: float
    product_species: tuple[str, ...] | None = None
    omit_species: tuple[str, ...] = ()
    include_ions: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.formulation, SolidFormulation):
            raise SolidFormulationError(
                f"formulation must be a SolidFormulation, got "
                f"{type(self.formulation).__name__}")

        pressure = _finite(self.chamber_pressure, "chamber pressure")
        if pressure <= 0.0:
            raise ThermochemistryError(
                f"chamber pressure must be strictly positive, got {pressure!r} Pa. "
                "This is checked here because a provider may accept a negative "
                "pressure without complaint and return a plausible-looking number.")
        object.__setattr__(self, "chamber_pressure", pressure)

        for label, value in (("product_species", self.product_species),
                             ("omit_species", self.omit_species)):
            if value is None:
                continue
            if not isinstance(value, tuple):
                raise ThermochemistryError(
                    f"{label} must be a tuple of names, or None")
            for name in value:
                if not isinstance(name, str) or not name.strip():
                    raise ThermochemistryError(
                        f"{label} entries must be non-empty strings, got {name!r}")

        if self.product_species is not None and not self.product_species:
            raise ThermochemistryError(
                "product_species must be a non-empty tuple, or None to let the "
                "provider derive products from the reactants")

        if not isinstance(self.include_ions, bool):
            raise ThermochemistryError(
                f"include_ions must be a bool, got {self.include_ions!r}")
