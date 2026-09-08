"""Composition: what a mixture is made of, and the algebra over it.

No chemistry is solved here. This module knows how to *hold* a composition, how
to convert between mole and mass bases, what a mixture's mean molar mass is,
and how to count atoms. It does not know how a composition came to be.

**Naming note, recorded rather than made silently.** Phase 5A ``09`` section 5.1
sketched this concept as ``Mixture``, storing mole fractions with an implicit
basis. The class here is called :class:`Composition` and carries its basis as an
explicit field. The change is deliberate and strictly stronger: an implicit
basis is exactly the ambiguity that ``09`` section 4.3 forbids for
``SpeciesAmount``, and it would be inconsistent to forbid it there and rely on
it here. Everything else from ``09`` section 5.1 -- mole fractions canonical,
the database identity travelling with the keys, completeness, deterministic
ordering -- is preserved.

Canonical basis: **mole fraction** (ADR-18). Mass fractions are derived on
request, never stored alongside, because two stored representations of one fact
can disagree.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from types import MappingProxyType

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT

from .errors import (
    CompositionBasisError,
    CompositionError,
    CompositionSumError,
    UnknownSpeciesError,
)
from .species import ElementalComposition, Species
from .tolerances import DEFAULT_THERMO_TOLERANCES, ThermochemistryTolerances
from .types import CompositionBasis

__all__ = [
    "Composition",
    "ElementalInventoryBasis",
    "ElementalInventory",
    "ElementBalanceReport",
    "mole_to_mass_fractions",
    "mass_to_mole_fractions",
    "mean_molar_mass",
    "specific_gas_constant",
    "elemental_inventory",
    "compare_elemental_inventories",
]


def _finite(value: object, what: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise CompositionError(f"{what} must be a real number, got {value!r}") from exc
    if not math.isfinite(number):
        raise CompositionError(f"{what} must be finite, got {number!r}")
    return number


def _lookup(name: str, species: Mapping[str, Species]) -> Species:
    try:
        found = species[name]
    except KeyError:
        raise UnknownSpeciesError(
            f"no species record supplied for {name!r}; a missing species treated as "
            "absent would break element conservation while the fractions still "
            "summed to one"
        ) from None
    if not isinstance(found, Species):
        raise UnknownSpeciesError(
            f"entry for {name!r} must be a Species, got {type(found).__name__}")
    return found


# ---------------------------------------------------------------------------
# composition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Composition:
    """What a mixture is made of, on a declared basis.

    Attributes:
        entries: ``(species_name, fraction)`` pairs, sorted by name so that
            equality and serialisation never depend on insertion order.
        basis: Whether the fractions are by mole or by mass. **Always
            explicit**; there is no constructor that lets a caller omit it.
        database: Name of the species set the keys belong to, e.g.
            ``"nasa_gas.yaml"`` or ``"cea:thermo.lib"``. Species keys are
            meaningless without it: a composition from one database and one from
            another are not interchangeable just because both contain ``"OH"``.
        database_version: Version or content hash of that species set.
        canonicalised_from_sum: The sum the caller actually supplied, when it
            differed from exactly 1 and was corrected. ``None`` when the input
            summed to 1 exactly. A corrected composition is never presented as
            though the caller had supplied it exactly (``09`` section 5,
            Phase 5B spec section 185).

    A composition is **complete** as constructed. Truncating trace species for
    display happens above the physics boundary and produces a view, not a
    ``Composition`` -- a truncated fraction set would no longer sum to one
    (``09`` section 5.2).
    """

    entries: tuple[tuple[str, float], ...]
    basis: CompositionBasis
    database: str = ""
    database_version: str = ""
    canonicalised_from_sum: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.basis, CompositionBasis):
            raise CompositionBasisError(
                f"basis must be a CompositionBasis member, got {self.basis!r}. "
                "A composition never guesses whether 0.5 means moles or mass.")
        if not self.entries:
            raise CompositionError("a composition needs at least one species")
        seen: set[str] = set()
        for item in self.entries:
            if not isinstance(item, tuple) or len(item) != 2:
                raise CompositionError(
                    f"each entry must be a (species, fraction) pair, got {item!r}")
            name, value = item
            if not isinstance(name, str) or not name:
                raise CompositionError(
                    f"species key must be a non-empty string, got {name!r}")
            if name in seen:
                raise CompositionError(f"duplicate species key {name!r}")
            seen.add(name)
            if not isinstance(value, float) or not math.isfinite(value):
                raise CompositionError(
                    f"fraction for {name!r} must be a finite float, got {value!r}")
        if list(self.entries) != sorted(self.entries, key=lambda kv: kv[0]):
            raise CompositionError(
                "entries must be sorted by species name; use from_fractions()")

    # -- constructors ------------------------------------------------------

    @classmethod
    def from_fractions(
        cls,
        fractions: Mapping[str, float],
        basis: CompositionBasis,
        *,
        database: str = "",
        database_version: str = "",
        tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
    ) -> "Composition":
        """Build from fractions that are expected to sum to one.

        A sum inside ``tolerances.composition_sum_tol`` of 1 is canonicalised to
        exactly 1 and the original sum is recorded. A sum outside that window
        raises :class:`CompositionSumError` -- it is **not** normalised, because
        rescaling ``{"O2": 0.8, "N2": 0.8}`` into a valid composition would
        invent a mixture the caller never described. Callers who genuinely hold
        unnormalised relative amounts use :meth:`from_weights` and say so.

        Negative fractions are refused. ``tolerances.fraction_negative_tol`` is
        0 by default, so nothing is clamped; a provider adapter that must absorb
        solver noise raises that tolerance explicitly at its own boundary.
        """
        if not isinstance(basis, CompositionBasis):
            raise CompositionBasisError(
                f"basis must be a CompositionBasis member, got {basis!r}")
        if not isinstance(fractions, Mapping):
            raise CompositionError(
                f"fractions must be a mapping, got {type(fractions).__name__}")
        if not fractions:
            raise CompositionError("a composition needs at least one species")

        cleaned: dict[str, float] = {}
        for name, raw in fractions.items():
            if not isinstance(name, str) or not name:
                raise CompositionError(
                    f"species key must be a non-empty string, got {name!r}")
            value = _finite(raw, f"fraction for {name!r}")
            if value < -tolerances.fraction_negative_tol:
                raise CompositionError(
                    f"fraction for {name!r} is {value!r}; negative fractions are refused "
                    f"(fraction_negative_tol = {tolerances.fraction_negative_tol})")
            # The one clamp in this package, and it is opt-in. With the default
            # fraction_negative_tol of 0 the check above has already raised, so
            # this line is unreachable unless a caller deliberately widened the
            # tolerance to absorb a provider's solver noise. Phase 5B spec
            # section 36 permits canonicalisation only under exactly that
            # explicit policy.
            cleaned[name] = max(value, 0.0) if value < 0.0 else value

        total = math.fsum(cleaned.values())
        if total <= 0.0:
            raise CompositionSumError(
                f"fractions sum to {total!r}; a composition needs positive content")
        deviation = abs(total - 1.0)
        canonicalised_from: float | None = None
        if deviation != 0.0:
            if deviation > tolerances.composition_sum_tol:
                raise CompositionSumError(
                    f"fractions sum to {total!r}, which differs from 1 by {deviation:.3e}, "
                    f"beyond composition_sum_tol = {tolerances.composition_sum_tol}. "
                    "Use Composition.from_weights() if these are relative amounts "
                    "rather than fractions.")
            canonicalised_from = total
            cleaned = {name: value / total for name, value in cleaned.items()}

        return cls(
            entries=tuple(sorted(cleaned.items(), key=lambda kv: kv[0])),
            basis=basis,
            database=database,
            database_version=database_version,
            canonicalised_from_sum=canonicalised_from,
        )

    @classmethod
    def from_weights(
        cls,
        weights: Mapping[str, float],
        basis: CompositionBasis,
        *,
        database: str = "",
        database_version: str = "",
        tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
    ) -> "Composition":
        """Build from arbitrary positive relative amounts, normalising them.

        This is the *explicit* normalising constructor. ``{"O2": 20, "N2": 80}``
        is a legitimate way to state a mixture, and normalising it is correct
        here precisely because the caller declared these are weights rather than
        fractions. The distinction is what lets :meth:`from_fractions` refuse to
        rescale silently (Phase 5B spec section 38).
        """
        if not isinstance(basis, CompositionBasis):
            raise CompositionBasisError(
                f"basis must be a CompositionBasis member, got {basis!r}")
        if not isinstance(weights, Mapping) or not weights:
            raise CompositionError("weights must be a non-empty mapping")
        cleaned: dict[str, float] = {}
        for name, raw in weights.items():
            if not isinstance(name, str) or not name:
                raise CompositionError(
                    f"species key must be a non-empty string, got {name!r}")
            value = _finite(raw, f"weight for {name!r}")
            if value < 0.0:
                raise CompositionError(
                    f"weight for {name!r} must be non-negative, got {value!r}")
            cleaned[name] = value
        total = math.fsum(cleaned.values())
        if total <= 0.0:
            raise CompositionSumError(
                f"weights sum to {total!r}; a composition needs positive content")
        return cls(
            entries=tuple(sorted(((name, value / total)
                                  for name, value in cleaned.items()),
                                 key=lambda kv: kv[0])),
            basis=basis,
            database=database,
            database_version=database_version,
            canonicalised_from_sum=None,
        )

    @classmethod
    def pure(
        cls,
        species_name: str,
        basis: CompositionBasis = CompositionBasis.MOLE_FRACTION,
        *,
        database: str = "",
        database_version: str = "",
    ) -> "Composition":
        """A composition of one species at fraction 1.

        Pure in either basis: for a single species the mole and mass fractions
        are both exactly 1, so the basis is a statement about intent rather than
        about the number.
        """
        return cls(entries=((species_name, 1.0),), basis=basis,
                   database=database, database_version=database_version)

    # -- views -------------------------------------------------------------

    @property
    def fractions(self) -> Mapping[str, float]:
        """Read-only mapping of species name to fraction, on :attr:`basis`."""
        return MappingProxyType(dict(self.entries))

    @property
    def species_names(self) -> tuple[str, ...]:
        """Species keys, in canonical order."""
        return tuple(name for name, _ in self.entries)

    @property
    def was_canonicalised(self) -> bool:
        """Whether the supplied fractions were corrected to sum to one."""
        return self.canonicalised_from_sum is not None

    def fraction_of(self, species_name: str) -> float:
        """The fraction of one species, or 0.0 if it is not present."""
        for name, value in self.entries:
            if name == species_name:
                return value
        return 0.0

    def sum(self) -> float:
        """The sum of the stored fractions. Exactly 1 for a valid composition."""
        return math.fsum(value for _, value in self.entries)

    # -- basis conversion --------------------------------------------------

    def to_basis(self, basis: CompositionBasis,
                 species: Mapping[str, Species]) -> "Composition":
        """This composition expressed on another basis.

        Returns ``self`` unchanged when the basis already matches, so a
        round trip through the current basis is exactly the identity.
        """
        if not isinstance(basis, CompositionBasis):
            raise CompositionBasisError(
                f"basis must be a CompositionBasis member, got {basis!r}")
        if basis is self.basis:
            return self
        masses = {name: _lookup(name, species).molar_mass
                  for name in self.species_names}
        if self.basis is CompositionBasis.MOLE_FRACTION:
            converted = mole_to_mass_fractions(self.fractions, masses)
        else:
            converted = mass_to_mole_fractions(self.fractions, masses)
        return replace(
            self,
            entries=tuple(sorted(converted.items(), key=lambda kv: kv[0])),
            basis=basis,
        )

    def mole_fractions(self, species: Mapping[str, Species]) -> Mapping[str, float]:
        """Mole fractions, converting from mass basis if necessary."""
        return self.to_basis(CompositionBasis.MOLE_FRACTION, species).fractions

    def mass_fractions(self, species: Mapping[str, Species]) -> Mapping[str, float]:
        """Mass fractions, converting from mole basis if necessary."""
        return self.to_basis(CompositionBasis.MASS_FRACTION, species).fractions

    # -- derived quantities ------------------------------------------------

    def mean_molar_mass(self, species: Mapping[str, Species]) -> float:
        """Mean molar mass of the mixture, kg/mol."""
        return mean_molar_mass(self, species)

    def specific_gas_constant(self, species: Mapping[str, Species]) -> float:
        """Specific gas constant ``R = Ru / M``, J/(kg K)."""
        return specific_gas_constant(self.mean_molar_mass(species))

    def condensed_mass_fraction(self, species: Mapping[str, Species]) -> float:
        """Mass fraction in LIQUID or SOLID phases.

        Computed from the composition itself, which is the only trustworthy
        way. Phase 5B-0 found that a provider's condensed-species *counter* can
        report a nonzero count while every condensed species is present at
        exactly zero, because the counter describes the candidate product list
        rather than the solution (ADR-28).
        """
        mass = self.to_basis(CompositionBasis.MASS_FRACTION, species)
        return math.fsum(
            value for name, value in mass.entries
            if _lookup(name, species).phase.is_condensed)

    def elemental(
        self,
        species: Mapping[str, Species],
        basis: "ElementalInventoryBasis | None" = None,
    ) -> "ElementalInventory":
        """Elemental inventory of this composition on an explicit basis.

        The default is per mole of mixture. It is a default on a *view*, not on
        stored data, and the basis it chose is carried in the returned record.
        """
        chosen = (ElementalInventoryBasis.PER_MOLE_OF_MIXTURE
                  if basis is None else basis)
        return elemental_inventory(self, species, chosen)


# ---------------------------------------------------------------------------
# basis conversion, as free functions
# ---------------------------------------------------------------------------


def mole_to_mass_fractions(
    mole_fractions: Mapping[str, float],
    molar_masses: Mapping[str, float],
) -> dict[str, float]:
    """Convert mole fractions to mass fractions.

    ``Y_i = X_i M_i / sum_j(X_j M_j)``

    Molar masses may be in any consistent unit: the ratio is dimensionless, so
    kg/mol and kg/kmol give identical answers. This is deliberate -- it makes
    the function usable by an adapter that has not yet converted units.
    """
    if not mole_fractions:
        raise CompositionError("mole fractions must not be empty")
    weighted: dict[str, float] = {}
    for name, x in mole_fractions.items():
        value = _finite(x, f"mole fraction of {name!r}")
        try:
            mass = float(molar_masses[name])
        except KeyError:
            raise UnknownSpeciesError(f"no molar mass supplied for {name!r}") from None
        if not math.isfinite(mass) or mass <= 0.0:
            raise CompositionError(
                f"molar mass of {name!r} must be positive and finite, got {mass!r}")
        weighted[name] = value * mass
    total = math.fsum(weighted.values())
    if total <= 0.0:
        raise CompositionError(
            f"sum of X_i M_i is {total!r}; cannot convert to a mass basis")
    return {name: value / total for name, value in weighted.items()}


def mass_to_mole_fractions(
    mass_fractions: Mapping[str, float],
    molar_masses: Mapping[str, float],
) -> dict[str, float]:
    """Convert mass fractions to mole fractions.

    ``X_i = (Y_i / M_i) / sum_j(Y_j / M_j)``
    """
    if not mass_fractions:
        raise CompositionError("mass fractions must not be empty")
    moles: dict[str, float] = {}
    for name, y in mass_fractions.items():
        value = _finite(y, f"mass fraction of {name!r}")
        try:
            mass = float(molar_masses[name])
        except KeyError:
            raise UnknownSpeciesError(f"no molar mass supplied for {name!r}") from None
        if not math.isfinite(mass) or mass <= 0.0:
            raise CompositionError(
                f"molar mass of {name!r} must be positive and finite, got {mass!r}")
        moles[name] = value / mass
    total = math.fsum(moles.values())
    if total <= 0.0:
        raise CompositionError(
            f"sum of Y_i / M_i is {total!r}; cannot convert to a mole basis")
    return {name: value / total for name, value in moles.items()}


def mean_molar_mass(composition: Composition,
                    species: Mapping[str, Species]) -> float:
    """Mean molar mass of a mixture, kg/mol.

    On a mole basis this is ``M = sum(X_i M_i)``; on a mass basis it is
    ``1 / M = sum(Y_i / M_i)``. Both paths describe the same quantity and must
    agree; :func:`~rocketforge.physics.thermochemistry.validation.check_mean_molar_mass_paths`
    is the check that they do.
    """
    if not isinstance(composition, Composition):
        raise CompositionError(
            f"expected a Composition, got {type(composition).__name__}")
    masses = {name: _lookup(name, species).molar_mass
              for name in composition.species_names}
    if composition.basis is CompositionBasis.MOLE_FRACTION:
        return math.fsum(x * masses[name] for name, x in composition.entries)
    reciprocal = math.fsum(y / masses[name] for name, y in composition.entries)
    if reciprocal <= 0.0:
        raise CompositionError(
            f"sum of Y_i / M_i is {reciprocal!r}; mean molar mass is undefined")
    return 1.0 / reciprocal


def specific_gas_constant(mean_molar_mass_value: float) -> float:
    """``R = Ru / M``, J/(kg K), from a mean molar mass in kg/mol.

    Uses :data:`rocketforge.core.constants.UNIVERSAL_GAS_CONSTANT`, which is
    8.31446261815324 J/(mol K), exact since the 2019 SI redefinition. That value
    is **not** adjusted to match any provider's historical convention: Phase
    5B-0 measured NASA CEA using a pre-2019 value, and that difference belongs
    to the CEA adapter's comparison tolerance, not to RocketForge's constants.
    """
    mass = _finite(mean_molar_mass_value, "mean molar mass")
    if mass <= 0.0:
        raise CompositionError(
            f"mean molar mass must be strictly positive, got {mass!r}")
    return UNIVERSAL_GAS_CONSTANT / mass


# ---------------------------------------------------------------------------
# elemental inventory
# ---------------------------------------------------------------------------


class ElementalInventoryBasis(StrEnum):
    """What one unit of an elemental inventory refers to.

    Never omitted. An untagged mapping of element to number is exactly the
    ambiguity that makes conservation checks meaningless (Phase 5B spec s. 49).
    """

    PER_MOLE_OF_MIXTURE = "per_mole_of_mixture"
    """Moles of each element per mole of mixture. Dimensionless ratio."""

    PER_KILOGRAM_OF_MIXTURE = "per_kilogram_of_mixture"
    """Moles of each element per kilogram of mixture, mol/kg."""


@dataclass(frozen=True, slots=True)
class ElementalInventory:
    """How many atoms of each element a mixture contains, on a stated basis."""

    amounts: ElementalComposition
    basis: ElementalInventoryBasis

    def __post_init__(self) -> None:
        if not isinstance(self.amounts, ElementalComposition):
            raise CompositionError(
                f"amounts must be an ElementalComposition, got "
                f"{type(self.amounts).__name__}")
        if not isinstance(self.basis, ElementalInventoryBasis):
            raise CompositionError(
                f"basis must be an ElementalInventoryBasis member, got {self.basis!r}")

    @property
    def elements(self) -> Mapping[str, float]:
        """Read-only mapping of element symbol to amount."""
        return self.amounts.atoms

    def total(self) -> float:
        """Sum of all element amounts, useful as a normalisation scale."""
        return math.fsum(value for _, value in self.amounts.entries)


def elemental_inventory(
    composition: Composition,
    species: Mapping[str, Species],
    basis: ElementalInventoryBasis = ElementalInventoryBasis.PER_MOLE_OF_MIXTURE,
) -> ElementalInventory:
    """Count the atoms in a composition, without solving any chemistry.

    Every species referenced must have an elemental formula; a species without
    one cannot take part in a balance, and silently skipping it would make the
    inventory wrong in a way no later check could catch.
    """
    if not isinstance(basis, ElementalInventoryBasis):
        raise CompositionError(
            f"basis must be an ElementalInventoryBasis member, got {basis!r}")

    totals: dict[str, float] = {}
    if basis is ElementalInventoryBasis.PER_MOLE_OF_MIXTURE:
        mole = composition.to_basis(CompositionBasis.MOLE_FRACTION, species)
        for name, x in mole.entries:
            record = _lookup(name, species)
            if not record.has_formula:
                raise CompositionError(
                    f"{name!r} has no elemental formula, so an elemental inventory "
                    "cannot be computed; supply a formula or exclude the species "
                    "explicitly")
            for symbol, count in record.formula.entries:
                totals[symbol] = totals.get(symbol, 0.0) + x * count
    else:
        mass = composition.to_basis(CompositionBasis.MASS_FRACTION, species)
        for name, y in mass.entries:
            record = _lookup(name, species)
            if not record.has_formula:
                raise CompositionError(
                    f"{name!r} has no elemental formula, so an elemental inventory "
                    "cannot be computed; supply a formula or exclude the species "
                    "explicitly")
            for symbol, count in record.formula.entries:
                totals[symbol] = totals.get(symbol, 0.0) + y / record.molar_mass * count

    return ElementalInventory(
        amounts=ElementalComposition.from_mapping(totals), basis=basis)


@dataclass(frozen=True, slots=True)
class ElementBalanceReport:
    """The outcome of comparing two elemental inventories.

    Reports rather than raises: measuring a discrepancy is the job, and a
    caller that wants a hard failure checks :attr:`balanced`.

    Attributes:
        balanced: Whether every element's residual is within tolerance.
        residuals: Per element, ``|b - a| / scale``, where ``scale`` is the
            larger of ``|a|`` and a floor derived from the inventories' own
            magnitude. Scale-aware so that a trace element is not judged on an
            absolute threshold, and division by zero cannot occur for an element
            absent from both sides (Phase 5B spec section 187).
        max_residual: The largest of those, or 0.0 for two empty inventories.
        worst_element: Which element carries ``max_residual``.
        tolerance: The relative tolerance applied.
        basis: The basis both inventories were on.
    """

    balanced: bool
    residuals: tuple[tuple[str, float], ...]
    max_residual: float
    worst_element: str | None
    tolerance: float
    basis: ElementalInventoryBasis

    @property
    def residual_map(self) -> Mapping[str, float]:
        return MappingProxyType(dict(self.residuals))


def compare_elemental_inventories(
    reactants: ElementalInventory,
    products: ElementalInventory,
    *,
    tolerances: ThermochemistryTolerances = DEFAULT_THERMO_TOLERANCES,
) -> ElementBalanceReport:
    """Check that chemistry rearranged atoms without creating or destroying any.

    This is the single most valuable check available to this layer, because it
    is **provider-independent, propellant-independent and reference-free**: it
    needs no published table and no oracle, and it catches the largest class of
    real defects -- a mis-parsed formula, a dropped species, an inverted mixture
    ratio, a units slip in the mass basis (``09`` section 3.2).

    It solves nothing. It compares two inventories the caller already has.
    """
    if not isinstance(reactants, ElementalInventory) or not isinstance(
            products, ElementalInventory):
        raise CompositionError("both arguments must be ElementalInventory records")
    if reactants.basis is not products.basis:
        raise CompositionError(
            f"cannot compare inventories on different bases: {reactants.basis.value} "
            f"vs {products.basis.value}")

    left = reactants.elements
    right = products.elements
    symbols = sorted(set(left) | set(right))

    # A scale-aware denominator: the element's own reactant amount where that is
    # meaningful, otherwise the inventory's overall magnitude, so that an element
    # absent from the reactants but invented by the products still registers.
    overall = max(reactants.total(), products.total())
    residuals: list[tuple[str, float]] = []
    for symbol in symbols:
        a = left.get(symbol, 0.0)
        b = right.get(symbol, 0.0)
        difference = abs(b - a)
        scale = max(abs(a), abs(b), overall)
        residuals.append((symbol, 0.0 if scale == 0.0 else difference / scale))

    if residuals:
        worst_element, max_residual = max(residuals, key=lambda kv: kv[1])
    else:
        worst_element, max_residual = None, 0.0

    return ElementBalanceReport(
        balanced=max_residual <= tolerances.element_balance_rel_tol,
        residuals=tuple(residuals),
        max_residual=max_residual,
        worst_element=worst_element if max_residual > 0.0 else None,
        tolerance=tolerances.element_balance_rel_tol,
        basis=reactants.basis,
    )
