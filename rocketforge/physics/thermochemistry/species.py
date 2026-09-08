"""Chemical species and their elemental composition.

A :class:`Species` is one chemical substance in one phase, together with the
thermodynamic data needed to use it as a reactant or a product. Phase is part
of its identity, not a label on it.

Units, fixed once and never negotiable inside this package:

======================  ==========================================
molar mass              kg/mol
enthalpy of formation   J/mol
temperature             K
pressure                Pa
======================  ==========================================

Molar mass is **kg/mol**, following ``09`` section 2.1. Providers report
kg/kmol; converting is the adapter's job, at the adapter boundary, where the
factor of 1000 is visible.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType

from rocketforge.core.constants import UNIVERSAL_GAS_CONSTANT

from .errors import ElementalCompositionError, SpeciesError
from .tolerances import DEFAULT_THERMO_TOLERANCES
from .types import Phase

__all__ = [
    "ElementalComposition",
    "PolynomialForm",
    "ThermoPolynomial",
    "Species",
    "STANDARD_STATE_TEMPERATURE",
    "STANDARD_STATE_PRESSURE",
]

#: The datum every enthalpy in this package is referenced to: elements in their
#: reference states at 298.15 K and 1 bar (ADR-25, ``09`` section 3.4).
#:
#: This is not a free choice. Reaction energy *is* the difference between
#: product and reactant formation enthalpies, so every value must sit on one
#: absolute datum. A ``FluidState`` enthalpy from CoolProp or ``physics.fluids``
#: is on a different, arbitrary datum and must never be added to a value from
#: this package.
STANDARD_STATE_TEMPERATURE: float = 298.15
STANDARD_STATE_PRESSURE: float = 1.0e5


def _require_finite(value: object, what: str) -> float:
    """Return ``value`` as a float, refusing NaN and infinities."""
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise SpeciesError(f"{what} must be a real number, got {value!r}") from exc
    if not math.isfinite(number):
        raise SpeciesError(f"{what} must be finite, got {number!r}")
    return number


# ---------------------------------------------------------------------------
# elemental composition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ElementalComposition:
    """Atoms per unit of a species or mixture.

    Stored as a sorted tuple of ``(symbol, count)`` pairs so the record is
    hashable and its equality and serialisation do not depend on the insertion
    order of whatever mapping built it.

    Counts are ``float``, not ``int``, for two reasons: a *mixture's* elemental
    content per kilogram is not integral, and an empirical surrogate formula
    such as RP-1's is fractional by construction (``09`` sections 3.1, 4.5).

    Element symbols are not restricted to C, H, O and N. Anything hashable as a
    non-empty string is accepted, so fluorine, chlorine, metals and future
    ionic labels need no change to the balance algorithm (Phase 5B spec s. 51).
    """

    entries: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for item in self.entries:
            if not isinstance(item, tuple) or len(item) != 2:
                raise ElementalCompositionError(
                    f"each entry must be a (symbol, count) pair, got {item!r}")
            symbol, count = item
            if not isinstance(symbol, str) or not symbol:
                raise ElementalCompositionError(
                    f"element symbol must be a non-empty string, got {symbol!r}")
            if symbol in seen:
                raise ElementalCompositionError(f"duplicate element symbol {symbol!r}")
            seen.add(symbol)
            if not isinstance(count, float) or not math.isfinite(count):
                raise ElementalCompositionError(
                    f"atom count for {symbol!r} must be a finite float, got {count!r}")
            if count < 0.0:
                raise ElementalCompositionError(
                    f"atom count for {symbol!r} must be non-negative, got {count!r}")
        if list(self.entries) != sorted(self.entries, key=lambda kv: kv[0]):
            raise ElementalCompositionError(
                "entries must be sorted by element symbol; use from_mapping()")

    @classmethod
    def from_mapping(cls, atoms: Mapping[str, float]) -> "ElementalComposition":
        """Build from ``{"C": 1.0, "H": 4.0}``, normalising order and type."""
        if not isinstance(atoms, Mapping):
            raise ElementalCompositionError(
                f"atoms must be a mapping of symbol to count, got {type(atoms).__name__}")
        normalised: list[tuple[str, float]] = []
        for symbol, count in atoms.items():
            if not isinstance(symbol, str) or not symbol:
                raise ElementalCompositionError(
                    f"element symbol must be a non-empty string, got {symbol!r}")
            try:
                value = float(count)
            except (TypeError, ValueError) as exc:
                raise ElementalCompositionError(
                    f"atom count for {symbol!r} must be a real number, got {count!r}"
                ) from exc
            if not math.isfinite(value):
                raise ElementalCompositionError(
                    f"atom count for {symbol!r} must be finite, got {value!r}")
            normalised.append((symbol, value))
        return cls(entries=tuple(sorted(normalised, key=lambda kv: kv[0])))

    @property
    def atoms(self) -> Mapping[str, float]:
        """A read-only mapping view of the element counts."""
        return MappingProxyType(dict(self.entries))

    @property
    def symbols(self) -> tuple[str, ...]:
        """Element symbols present, in canonical order."""
        return tuple(symbol for symbol, _ in self.entries)

    def count(self, symbol: str) -> float:
        """Atoms of ``symbol`` per unit, or 0.0 if the element is absent."""
        for name, value in self.entries:
            if name == symbol:
                return value
        return 0.0

    def scaled(self, factor: float) -> "ElementalComposition":
        """This composition multiplied by a non-negative finite ``factor``."""
        value = _require_finite(factor, "scale factor")
        if value < 0.0:
            raise ElementalCompositionError(
                f"scale factor must be non-negative, got {value!r}")
        return ElementalComposition(
            entries=tuple((symbol, count * value) for symbol, count in self.entries))

    def __add__(self, other: "ElementalComposition") -> "ElementalComposition":
        """Element-wise sum, union of both element sets."""
        if not isinstance(other, ElementalComposition):
            return NotImplemented
        merged: dict[str, float] = dict(self.entries)
        for symbol, count in other.entries:
            merged[symbol] = merged.get(symbol, 0.0) + count
        return ElementalComposition.from_mapping(merged)

    def is_empty(self) -> bool:
        """True when no element is present with a positive count."""
        return all(count == 0.0 for _, count in self.entries)


# ---------------------------------------------------------------------------
# thermodynamic polynomials
# ---------------------------------------------------------------------------


class PolynomialForm(StrEnum):
    """Which NASA polynomial convention a coefficient set follows."""

    NASA7 = "nasa7"
    """Seven coefficients ``a1..a7``, the classic CHEMKIN form."""

    NASA9 = "nasa9"
    """Nine coefficients ``a1..a7, b1, b2``, the NASA Glenn form. Includes
    ``T**-2`` and ``T**-1`` terms, so it fits a wider temperature range."""


@dataclass(frozen=True, slots=True)
class ThermoPolynomial:
    """A piecewise NASA polynomial fit, with its validity range.

    Evaluation is pure algebra on **caller-supplied** coefficients. This class
    invents no thermodynamic data and knows no species: it cannot tell you the
    cp of methane, only the cp of the coefficients you hand it
    (Phase 5B spec section 86).

    Attributes:
        form: Which coefficient convention the tuples follow.
        temperature_ranges: One ``(T_min, T_max)`` per coefficient set, in K,
            ascending and contiguous.
        coefficients: One coefficient tuple per range. Length must match
            ``form`` -- 7 for NASA7, 9 for NASA9.

    Out-of-range evaluation **raises**. A least-squares fit evaluated 500 K past
    its top range can return a negative cp, and a number outside the model's
    domain is not a number the model may return. This is the same rule the
    compressible module applies to a Prandtl-Meyer turn beyond nu_max
    (``09`` section 2.3).

    Range joins are matched in **value** and generally not in slope. Tests
    check value continuity and deliberately do not check derivative
    continuity, because that is a property the published data does not have.
    """

    form: PolynomialForm
    temperature_ranges: tuple[tuple[float, float], ...]
    coefficients: tuple[tuple[float, ...], ...]

    def __post_init__(self) -> None:
        if not self.temperature_ranges:
            raise SpeciesError("a thermo polynomial needs at least one temperature range")
        if len(self.temperature_ranges) != len(self.coefficients):
            raise SpeciesError(
                f"{len(self.temperature_ranges)} temperature ranges but "
                f"{len(self.coefficients)} coefficient sets")
        expected = 7 if self.form is PolynomialForm.NASA7 else 9
        previous_high: float | None = None
        for (low, high), coeffs in zip(self.temperature_ranges, self.coefficients):
            low_f = _require_finite(low, "range lower bound")
            high_f = _require_finite(high, "range upper bound")
            if low_f <= 0.0:
                raise SpeciesError(f"range lower bound must be above 0 K, got {low_f!r}")
            if not high_f > low_f:
                raise SpeciesError(f"range ({low_f}, {high_f}) is not ascending")
            if previous_high is not None and low_f < previous_high:
                raise SpeciesError("temperature ranges must be ascending and non-overlapping")
            previous_high = high_f
            if len(coeffs) != expected:
                raise SpeciesError(
                    f"{self.form.value} needs {expected} coefficients, got {len(coeffs)}")
            for index, value in enumerate(coeffs):
                _require_finite(value, f"coefficient {index}")

    @property
    def temperature_bounds(self) -> tuple[float, float]:
        """The overall ``(T_min, T_max)`` this fit covers."""
        return self.temperature_ranges[0][0], self.temperature_ranges[-1][1]

    def covers(self, temperature: float) -> bool:
        """Whether ``temperature`` lies inside the overall validity range."""
        low, high = self.temperature_bounds
        return low <= temperature <= high

    def _coefficients_at(self, temperature: float) -> tuple[float, ...]:
        value = _require_finite(temperature, "temperature")
        for (low, high), coeffs in zip(self.temperature_ranges, self.coefficients):
            if low <= value <= high:
                return coeffs
        low, high = self.temperature_bounds
        raise SpeciesError(
            f"temperature {value} K is outside the fit's validity range "
            f"[{low}, {high}] K; this polynomial is not extrapolated")

    def cp_molar(self, temperature: float) -> float:
        """Molar heat capacity at constant pressure, J/(mol K)."""
        a = self._coefficients_at(temperature)
        t = float(temperature)
        if self.form is PolynomialForm.NASA7:
            ratio = a[0] + a[1] * t + a[2] * t**2 + a[3] * t**3 + a[4] * t**4
        else:
            ratio = (a[0] / t**2 + a[1] / t + a[2] + a[3] * t
                     + a[4] * t**2 + a[5] * t**3 + a[6] * t**4)
        return ratio * UNIVERSAL_GAS_CONSTANT

    def enthalpy_molar(self, temperature: float) -> float:
        """Molar enthalpy, J/mol, on the datum of ``STANDARD_STATE_TEMPERATURE``.

        This is **formation plus sensible**, not sensible alone. A NASA fit
        already includes the formation term; the contract records it so nobody
        "fixes" it later (``09`` section 3.4).
        """
        a = self._coefficients_at(temperature)
        t = float(temperature)
        if self.form is PolynomialForm.NASA7:
            ratio = (a[0] + a[1] * t / 2.0 + a[2] * t**2 / 3.0
                     + a[3] * t**3 / 4.0 + a[4] * t**4 / 5.0 + a[5] / t)
        else:
            ratio = (-a[0] / t**2 + a[1] * math.log(t) / t + a[2] + a[3] * t / 2.0
                     + a[4] * t**2 / 3.0 + a[5] * t**3 / 4.0 + a[6] * t**4 / 5.0
                     + a[7] / t)
        return ratio * UNIVERSAL_GAS_CONSTANT * t

    def entropy_molar(self, temperature: float,
                      pressure: float = STANDARD_STATE_PRESSURE) -> float:
        """Molar entropy, J/(mol K), including the pressure term.

        ``s(T, p) = s0(T) - R ln(p / p_ref)`` with ``p_ref`` the standard state
        pressure of 1 bar.
        """
        a = self._coefficients_at(temperature)
        t = float(temperature)
        p = _require_finite(pressure, "pressure")
        if p <= 0.0:
            raise SpeciesError(f"pressure must be above zero, got {p!r}")
        if self.form is PolynomialForm.NASA7:
            ratio = (a[0] * math.log(t) + a[1] * t + a[2] * t**2 / 2.0
                     + a[3] * t**3 / 3.0 + a[4] * t**4 / 4.0 + a[6])
        else:
            ratio = (-a[0] / (2.0 * t**2) - a[1] / t + a[2] * math.log(t)
                     + a[3] * t + a[4] * t**2 / 2.0 + a[5] * t**3 / 3.0
                     + a[6] * t**4 / 4.0 + a[8])
        return UNIVERSAL_GAS_CONSTANT * (ratio - math.log(p / STANDARD_STATE_PRESSURE))


# ---------------------------------------------------------------------------
# species
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Species:
    """One chemical species in one phase.

    Attributes:
        name: The database key, e.g. ``"H2O"``, ``"CO2"``, ``"AL2O3(L)"``. This
            is the machine name a composition refers to; it is not a display
            label. **Not restricted in length**: NASA CEA limits reactant names
            to 15 characters, but that is a provider constraint and belongs in
            the CEA adapter's name mapping, not in RocketForge's domain model
            (Phase 5B spec section 117).
        phase: Part of the species' identity. ``H2O`` in ``GAS`` and ``H2O`` in
            ``LIQUID`` are two different species with different formation
            enthalpies and they never compare equal.
        molar_mass: kg/mol, strictly positive and finite.
        formula: Atoms per mole of species. May be empty only for a species
            whose elemental content is genuinely unknown, which then cannot
            take part in an element balance.
        enthalpy_of_formation: J/mol at ``reference_temperature``, on the
            standard datum. ``None`` when not supplied -- never a guessed zero.
        thermo: Optional polynomial fit. ``None`` when a provider owns the
            thermodynamic data, which is the normal case; the field exists for
            the in-tree verification set.
        reference_temperature: K, the temperature ``enthalpy_of_formation`` is
            stated at. Defaults to the standard 298.15 K.
        display_name: Optional human-facing label, e.g. ``"H₂O"``. Separate
            from ``name`` so that a presentation choice can never change a
            machine identity (Phase 5B spec section 19).
        is_surrogate: True when this record is a pseudo-species standing in for
            a substance that is not a single molecule -- RP-1, a kerosene cut, a
            binder. Requires a non-empty ``source``.
        source: Where the data came from. Required for a surrogate, because two
            different RP-1 fits are two different species and only their
            provenance distinguishes them (``09`` section 4.5).

    Molar mass is stored, not derived from ``formula``. Deriving it would bind
    every species to one atomic-weight table, and published thermodynamic data
    sets carry their own. A species is trusted to state its own molar mass; a
    validator may cross-check it against the formula, but nothing silently
    overrides either (``09`` section 2.2, Phase 5B spec section 27).
    """

    name: str
    phase: Phase
    molar_mass: float
    formula: ElementalComposition = field(
        default_factory=lambda: ElementalComposition(entries=()))
    enthalpy_of_formation: float | None = None
    thermo: ThermoPolynomial | None = None
    reference_temperature: float = STANDARD_STATE_TEMPERATURE
    display_name: str | None = None
    is_surrogate: bool = False
    source: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise SpeciesError(f"species name must be a non-empty string, got {self.name!r}")
        if not isinstance(self.phase, Phase):
            raise SpeciesError(
                f"phase must be a Phase member, got {self.phase!r}. There is no default: "
                "an unknown phase is never silently treated as GAS.")
        mass = _require_finite(self.molar_mass, f"molar mass of {self.name!r}")
        tol = DEFAULT_THERMO_TOLERANCES
        if mass <= 0.0:
            raise SpeciesError(
                f"molar mass of {self.name!r} must be strictly positive, got {mass!r}")
        if not (tol.molar_mass_floor <= mass <= tol.molar_mass_ceiling):
            raise SpeciesError(
                f"molar mass of {self.name!r} is {mass!r} kg/mol, outside the admissible "
                f"range [{tol.molar_mass_floor}, {tol.molar_mass_ceiling}] kg/mol. "
                "Molar mass in this package is kg/mol; providers report kg/kmol.")
        if not isinstance(self.formula, ElementalComposition):
            raise SpeciesError(
                f"formula must be an ElementalComposition, got {type(self.formula).__name__}")
        if self.enthalpy_of_formation is not None:
            _require_finite(self.enthalpy_of_formation,
                            f"enthalpy of formation of {self.name!r}")
        reference = _require_finite(self.reference_temperature,
                                    f"reference temperature of {self.name!r}")
        if reference <= 0.0:
            raise SpeciesError(
                f"reference temperature of {self.name!r} must be above 0 K, got {reference!r}")
        if self.thermo is not None and not isinstance(self.thermo, ThermoPolynomial):
            raise SpeciesError(
                f"thermo must be a ThermoPolynomial or None, got {type(self.thermo).__name__}")
        if self.is_surrogate and not self.source.strip():
            raise SpeciesError(
                f"surrogate species {self.name!r} must name its source: two different "
                "surrogate fits are two different species and only provenance "
                "distinguishes them")

    @property
    def canonical_id(self) -> str:
        """Stable machine identity, e.g. ``"H2O:gas"``.

        Combines name and phase because phase is part of identity. Use this as
        a dictionary key when species from different phases may coexist.
        """
        return f"{self.name}:{self.phase.value}"

    @property
    def label(self) -> str:
        """The display label: ``display_name`` when set, otherwise ``name``."""
        return self.display_name if self.display_name else self.name

    @property
    def has_formula(self) -> bool:
        """Whether this species can take part in an element balance."""
        return bool(self.formula.entries) and not self.formula.is_empty()

    def elemental_mass_fractions(self) -> Mapping[str, float]:
        """Mass of each element per unit mass of this species, kg/kg.

        Requires a formula. Uses this species' *stored* molar mass as the
        denominator, so the result is consistent with the record rather than
        with an external atomic-weight table.
        """
        if not self.has_formula:
            raise SpeciesError(
                f"{self.name!r} has no elemental formula, so its elemental mass "
                "fractions are undefined")
        return MappingProxyType(
            {symbol: count / self.molar_mass for symbol, count in self.formula.entries})

    def formula_molar_mass(self, atomic_weights: Mapping[str, float]) -> float:
        """Molar mass implied by the formula and a supplied atomic-weight table.

        Provided for *cross-checking* the stored value, which is what ``13``
        section 4 asks for. It never replaces :attr:`molar_mass`, and the
        atomic weights must be supplied by the caller: this package ships no
        periodic table, because whose periodic table is exactly the question
        (``09`` section 2.2).
        """
        total = 0.0
        for symbol, count in self.formula.entries:
            if symbol not in atomic_weights:
                raise SpeciesError(
                    f"no atomic weight supplied for element {symbol!r} of {self.name!r}")
            total += count * float(atomic_weights[symbol])
        return total
