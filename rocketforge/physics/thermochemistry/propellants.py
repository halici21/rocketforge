"""Propellants: what can be burned, and what is actually flowing.

Three concepts that are routinely confused and are kept apart here:

* :class:`PropellantDefinition` -- the *substance*. LOX as a material, with the
  reference condition its published data is stated at.
* :class:`PropellantStream` -- the *operating state*. LOX at 90.2 K in this
  engine, right now.
* :class:`PropellantPair` -- an oxidiser and a fuel considered together, with
  no performance attached.

A propellant is **not** a species. Methane maps to one molecule; RP-1,
Aerozine-50, MON-3 and 90 % hydrogen peroxide do not. So a definition holds a
:class:`~rocketforge.physics.thermochemistry.composition.Composition`, never a
single species name (``09`` section 4).

**Naming note, recorded rather than made silently.** Phase 5A ``09`` section 4.2
gave the definition a ``cea_name`` field. This module carries
:attr:`PropellantDefinition.provider_names` instead -- a mapping from provider
id to that provider's spelling. The intent is Phase 5A's (keep the translation
in one place, on the definition); the change is that a *generic* mapping does
not name one vendor in the domain model, which Phase 5B spec section 206
forbids, and it extends to Cantera and any future provider without a new field
each time.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .composition import Composition
from .errors import MixtureRatioError, PropellantError, PropellantRoleError
from .types import MixtureRatioBasis, Phase, PropellantRole

__all__ = [
    "PropellantDefinition",
    "PropellantStream",
    "MixtureRatio",
    "PropellantPair",
    "PropellantPairReferenceCase",
    "mixture_ratio_from_streams",
]


def _finite(value: object, what: str) -> float:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise PropellantError(f"{what} must be a real number, got {value!r}") from exc
    if not math.isfinite(number):
        raise PropellantError(f"{what} must be finite, got {number!r}")
    return number


# ---------------------------------------------------------------------------
# definition
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PropellantDefinition:
    """A substance usable as a reactant, at its reference condition.

    Attributes:
        name: RocketForge's canonical identifier, e.g. ``"LOX"``, ``"RP-1"``.
            Length is **not** restricted: NASA CEA caps reactant names at 15
            characters, but that is a provider limit and lives in the provider
            name mapping, not in the domain model (Phase 5B spec section 117).
        role: FUEL, OXIDISER or MONOPROPELLANT.
        composition: What the substance is made of. One species for methane,
            several for a blend. The composition carries its own basis, so a
            blend specified by mass stays a mass-basis record.
        reference_temperature: K. The temperature the *published data* is stated
            at -- not the temperature it is used at. See :class:`PropellantStream`.
        reference_phase: The phase at the reference condition.
        reference_pressure: Pa, optional. Some reference data is stated at a
            pressure and some is not.
        enthalpy_of_formation: J/mol at the reference condition, on the standard
            datum, when known for the substance as a whole.
        density_hint: kg/m3 at the reference condition. **Display and sizing
            only.** No calculation in this package reads it, and a test enforces
            that. Bulk density is ``physics.fluids``' answer, not this layer's
            (``09`` section 4.2).
        provider_names: ``{"cea": "RP-1", "cantera": "..."}``. Generic by
            design; see the module docstring.
        is_surrogate: True when the substance is modelled by a pseudo-species
            rather than being a single compound.
        source: Where the definition came from. Required for a surrogate.
    """

    name: str
    role: PropellantRole
    composition: Composition
    reference_temperature: float
    reference_phase: Phase
    reference_pressure: float | None = None
    enthalpy_of_formation: float | None = None
    density_hint: float | None = None
    provider_names: Mapping[str, str] = field(default_factory=dict)
    is_surrogate: bool = False
    source: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise PropellantError(
                f"propellant name must be a non-empty string, got {self.name!r}")
        if not isinstance(self.role, PropellantRole):
            raise PropellantError(
                f"role must be a PropellantRole member, got {self.role!r}")
        if not isinstance(self.composition, Composition):
            raise PropellantError(
                f"composition must be a Composition, got "
                f"{type(self.composition).__name__}")
        if not isinstance(self.reference_phase, Phase):
            raise PropellantError(
                f"reference_phase must be a Phase member, got {self.reference_phase!r}. "
                "There is no default: an unknown phase is never treated as GAS.")
        temperature = _finite(self.reference_temperature,
                              f"reference temperature of {self.name!r}")
        if temperature <= 0.0:
            raise PropellantError(
                f"reference temperature of {self.name!r} must be above 0 K, "
                f"got {temperature!r}. Temperatures in this package are kelvin.")
        if self.reference_pressure is not None:
            pressure = _finite(self.reference_pressure,
                               f"reference pressure of {self.name!r}")
            if pressure <= 0.0:
                raise PropellantError(
                    f"reference pressure of {self.name!r} must be above 0 Pa, "
                    f"got {pressure!r}")
        if self.enthalpy_of_formation is not None:
            _finite(self.enthalpy_of_formation,
                    f"enthalpy of formation of {self.name!r}")
        if self.density_hint is not None:
            density = _finite(self.density_hint, f"density hint of {self.name!r}")
            if density <= 0.0:
                raise PropellantError(
                    f"density hint of {self.name!r} must be above 0, got {density!r}")
        if not isinstance(self.provider_names, Mapping):
            raise PropellantError(
                f"provider_names must be a mapping of provider id to name, got "
                f"{type(self.provider_names).__name__}")
        for key, value in self.provider_names.items():
            if not isinstance(key, str) or not key:
                raise PropellantError(
                    f"provider id must be a non-empty string, got {key!r}")
            if not isinstance(value, str) or not value:
                raise PropellantError(
                    f"provider name for {key!r} must be a non-empty string, got {value!r}")
        if self.is_surrogate and not self.source.strip():
            raise PropellantError(
                f"surrogate propellant {self.name!r} must name its source: two "
                "different surrogate models are two different propellants and only "
                "provenance distinguishes them")

    @property
    def is_blend(self) -> bool:
        """Whether this substance is made of more than one species."""
        return len(self.composition.entries) > 1

    def provider_name(self, provider_id: str) -> str:
        """This propellant's name for one provider, falling back to :attr:`name`."""
        return self.provider_names.get(provider_id, self.name)


# ---------------------------------------------------------------------------
# stream
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PropellantStream:
    """A propellant in its actual operating condition.

    The distinction from :class:`PropellantDefinition` is load-bearing. A
    definition says what published data exists and at what condition; a stream
    says what is really flowing. LOX at 90.17 K carries measurably less
    enthalpy than notional LOX at 298 K, and Phase 5B-0 measured that
    difference as **74.9 K of flame temperature** for LOX/CH4. A model that
    cannot express the difference cannot get the chamber right.

    Attributes:
        propellant: The substance.
        temperature: K, strictly positive and finite. Kelvin, never Celsius.
        pressure: Pa, strictly positive and finite when supplied.
        phase: The actual phase. ``None`` means unknown -- and unknown is never
            silently read as GAS. Callers that need a phase must check.
        mass_flow: kg/s, optional. Phase 5A ``09`` section 10 made this
            mandatory because it derives O/F from two streams; it is optional
            here because a chamber equilibrium needs only the *ratio*, not the
            absolute flow (Phase 5B spec section 192).
            :func:`mixture_ratio_from_streams` requires it and says so.

    Deliberately absent: injector geometry, feed pressure drop, orifice area.
    Those belong to ``engineering.injector``.
    """

    propellant: PropellantDefinition
    temperature: float
    pressure: float | None = None
    phase: Phase | None = None
    mass_flow: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.propellant, PropellantDefinition):
            raise PropellantError(
                f"propellant must be a PropellantDefinition, got "
                f"{type(self.propellant).__name__}")
        temperature = _finite(self.temperature,
                              f"stream temperature of {self.propellant.name!r}")
        if temperature <= 0.0:
            raise PropellantError(
                f"stream temperature of {self.propellant.name!r} must be above 0 K, "
                f"got {temperature!r}. This package works in kelvin; a Celsius "
                "value would be silently wrong rather than obviously wrong.")
        if self.pressure is not None:
            pressure = _finite(self.pressure,
                               f"stream pressure of {self.propellant.name!r}")
            if pressure <= 0.0:
                raise PropellantError(
                    f"stream pressure of {self.propellant.name!r} must be above 0 Pa, "
                    f"got {pressure!r}")
        if self.phase is not None and not isinstance(self.phase, Phase):
            raise PropellantError(
                f"phase must be a Phase member or None, got {self.phase!r}")
        if self.mass_flow is not None:
            flow = _finite(self.mass_flow,
                           f"mass flow of {self.propellant.name!r}")
            if flow <= 0.0:
                raise PropellantError(
                    f"mass flow of {self.propellant.name!r} must be above 0 kg/s, "
                    f"got {flow!r}")

    @property
    def role(self) -> PropellantRole:
        """The role this stream's propellant declares."""
        return self.propellant.role

    @property
    def is_at_reference_condition(self) -> bool:
        """Whether the actual temperature equals the definition's reference.

        Exists so a caller can tell the two apart explicitly rather than by
        comparing floats at the call site.
        """
        return self.temperature == self.propellant.reference_temperature

    @property
    def effective_phase(self) -> Phase | None:
        """The stream's phase if stated, otherwise ``None``.

        Deliberately does **not** fall back to the definition's reference phase.
        A propellant defined as a liquid may be flowing as a supercritical
        fluid, and inheriting the reference phase would assert something the
        caller never said (Phase 5B spec section 21).
        """
        return self.phase


# ---------------------------------------------------------------------------
# mixture ratio
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MixtureRatio:
    """An oxidiser-to-fuel ratio.

    **O/F is oxidiser mass divided by fuel mass. Always.** This is the
    aerospace convention, it is what CEA's ``o/f`` means, and it is fixed in one
    place so no module ever has to guess (ADR-18, ``09`` section 6.1).

    Three neighbouring quantities exist, are useful, and are **not** this one.
    None of them is called ``mixture_ratio`` anywhere in this package:

    ================================  ==================================
    equivalence ratio phi             ``MR_stoich / MR``
    stoichiometric ratio MR_stoich    a property of the propellant pair
    F/O                               ``1 / MR``
    ================================  ==================================

    The inversion trap is why this class exists rather than a bare float.
    Rocket engines run fuel-rich, so a LOX/LH2 engine at O/F 6 against a
    stoichiometric 7.94 has phi around 1.32; a code that confuses O/F with F/O
    gets 0.167 instead of 6 and produces a temperature that is wrong but not
    absurd (``09`` section 6.3).

    Attributes:
        value: The ratio as supplied, on :attr:`basis`.
        basis: MASS is canonical. MOLAR is accepted and converted immediately;
            :attr:`stated_basis` remembers what the caller supplied so
            provenance can say so.
    """

    value: float
    basis: MixtureRatioBasis = MixtureRatioBasis.MASS

    def __post_init__(self) -> None:
        if not isinstance(self.basis, MixtureRatioBasis):
            raise MixtureRatioError(
                f"basis must be a MixtureRatioBasis member, got {self.basis!r}")
        try:
            number = float(self.value)
        except (TypeError, ValueError) as exc:
            raise MixtureRatioError(
                f"mixture ratio must be a real number, got {self.value!r}") from exc
        if not math.isfinite(number):
            raise MixtureRatioError(
                f"mixture ratio must be finite, got {number!r}")
        if number <= 0.0:
            raise MixtureRatioError(
                f"mixture ratio must be strictly positive, got {number!r}. "
                "Zero is not a mixture ratio: no oxidiser means a monopropellant "
                "or a decomposition problem, which has its own entry point rather "
                "than being computed as a limit.")

    @property
    def of_mass(self) -> float:
        """The canonical oxidiser-over-fuel ratio by mass.

        For a MASS-basis record this is :attr:`value`. A MOLAR-basis record
        cannot be converted without the two molar masses, so
        :meth:`to_mass_basis` takes them explicitly rather than this property
        guessing.
        """
        if self.basis is not MixtureRatioBasis.MASS:
            raise MixtureRatioError(
                f"this ratio is on a {self.basis.value} basis; call to_mass_basis() "
                "with the oxidiser and fuel molar masses to convert it. The "
                "conversion needs data this record does not carry, so it is not "
                "done implicitly.")
        return float(self.value)

    @property
    def stated_basis(self) -> MixtureRatioBasis:
        """The basis the caller originally supplied."""
        return self.basis

    def to_mass_basis(self, oxidiser_molar_mass: float,
                      fuel_molar_mass: float) -> "MixtureRatio":
        """Convert a molar-basis ratio to the canonical mass basis."""
        if self.basis is MixtureRatioBasis.MASS:
            return self
        ox = _finite(oxidiser_molar_mass, "oxidiser molar mass")
        fuel = _finite(fuel_molar_mass, "fuel molar mass")
        if ox <= 0.0 or fuel <= 0.0:
            raise MixtureRatioError("molar masses must be strictly positive")
        return MixtureRatio(value=float(self.value) * ox / fuel,
                            basis=MixtureRatioBasis.MASS)

    def equivalence_ratio(self, stoichiometric_of_mass: float) -> float:
        """Equivalence ratio ``phi = MR_stoich / MR``.

        The stoichiometric ratio must be supplied: there is no hidden constant,
        because it is a property of the propellant pair and not of this record
        (Phase 5B spec section 70).
        """
        stoich = _finite(stoichiometric_of_mass, "stoichiometric O/F")
        if stoich <= 0.0:
            raise MixtureRatioError(
                f"stoichiometric O/F must be strictly positive, got {stoich!r}")
        return stoich / self.of_mass

    def fuel_oxidiser_ratio(self) -> float:
        """``F/O = 1 / (O/F)``. Named so it can never be mistaken for O/F."""
        return 1.0 / self.of_mass


def mixture_ratio_from_streams(
    fuel: PropellantStream,
    oxidiser: PropellantStream,
) -> MixtureRatio:
    """Build the canonical O/F from a fuel stream and an oxidiser stream.

    The argument order is fuel-first while the result is oxidiser-over-fuel.
    That is deliberate: the roles are **checked**, not inferred from position,
    so a caller who swaps the arguments gets a
    :class:`~rocketforge.physics.thermochemistry.errors.PropellantRoleError`
    rather than a silently inverted ratio (``09`` section 10).
    """
    if not isinstance(fuel, PropellantStream) or not isinstance(oxidiser, PropellantStream):
        raise PropellantError("both arguments must be PropellantStream records")
    if fuel.role is not PropellantRole.FUEL:
        raise PropellantRoleError(
            f"the fuel argument is {fuel.propellant.name!r}, whose declared role is "
            f"{fuel.role.value}, not fuel. Arguments may be swapped.")
    if oxidiser.role is not PropellantRole.OXIDISER:
        raise PropellantRoleError(
            f"the oxidiser argument is {oxidiser.propellant.name!r}, whose declared "
            f"role is {oxidiser.role.value}, not oxidiser. Arguments may be swapped.")
    if fuel.mass_flow is None or oxidiser.mass_flow is None:
        raise PropellantError(
            "both streams must state a mass flow to derive a mixture ratio; "
            "supply MixtureRatio directly if only the ratio is known")
    return MixtureRatio(value=oxidiser.mass_flow / fuel.mass_flow,
                        basis=MixtureRatioBasis.MASS)


# ---------------------------------------------------------------------------
# pair
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PropellantPair:
    """An oxidiser and a fuel considered together.

    Carries **no performance whatsoever**. There is no ``isp``, no ``cstar``,
    no ``chamber_temperature`` and no ``optimal_of`` field, and none may be
    added. Every one of those depends on the operating condition and the
    chemistry model, so storing one on the pair would attach a number to a
    question that was never asked.

    ``optimal_of`` deserves its own sentence, because it is the most tempting.
    Phase 5B-0 swept LOX/CH4 from O/F 2.5 to 4.5 and found c* peaking at 2.85,
    chamber temperature at 3.75 and specific impulse at 3.30 -- three different
    maxima. "Optimum O/F" is undefined without stating the objective, so this
    class does not pretend otherwise (Phase 5B spec section 178).

    Attributes:
        oxidiser: The oxidising propellant. Role is checked.
        fuel: The fuel propellant. Role is checked.
        name: Optional display name, e.g. ``"LOX/CH4"``.
        stoichiometric_of_mass: Optional. The O/F at complete combustion, which
            *is* a property of the pair rather than of an operating point. Kept
            optional because computing it requires elemental bookkeeping the
            caller may not have done.
    """

    oxidiser: PropellantDefinition
    fuel: PropellantDefinition
    name: str = ""
    stoichiometric_of_mass: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.oxidiser, PropellantDefinition):
            raise PropellantError(
                f"oxidiser must be a PropellantDefinition, got "
                f"{type(self.oxidiser).__name__}")
        if not isinstance(self.fuel, PropellantDefinition):
            raise PropellantError(
                f"fuel must be a PropellantDefinition, got {type(self.fuel).__name__}")
        if self.oxidiser.role is not PropellantRole.OXIDISER:
            raise PropellantRoleError(
                f"{self.oxidiser.name!r} declares role {self.oxidiser.role.value}, "
                "not oxidiser")
        if self.fuel.role is not PropellantRole.FUEL:
            raise PropellantRoleError(
                f"{self.fuel.name!r} declares role {self.fuel.role.value}, not fuel")
        if self.stoichiometric_of_mass is not None:
            stoich = _finite(self.stoichiometric_of_mass, "stoichiometric O/F")
            if stoich <= 0.0:
                raise PropellantError(
                    f"stoichiometric O/F must be strictly positive, got {stoich!r}")

    @property
    def label(self) -> str:
        """Display label: :attr:`name` when set, else ``"OXIDISER/FUEL"``."""
        return self.name if self.name else f"{self.oxidiser.name}/{self.fuel.name}"


# ---------------------------------------------------------------------------
# reference case
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PropellantPairReferenceCase:
    """A published performance observation, bound to its conditions.

    This is a record of what *a source* reported under *stated* conditions. It
    is not a RocketForge calculation and must never be presented as one, and it
    is not a lookup table to be interpolated: the standing rule is that a
    published table is never the solver.

    The separation of identity, conditions and observations is the point. A
    chamber temperature with no O/F, no chamber pressure, no reactant
    temperatures and no chemistry mode is not a datum; it is a number.

    Attributes:
        pair: Which propellants.
        source: Publication, e.g. ``"NASA RP-1311 Part II"``.
        source_location: Table, page or example number within the source.
        oxidiser_fuel_ratio: The O/F the case was run at.
        chamber_pressure: Pa.
        oxidiser_temperature: K, when the source states it.
        fuel_temperature: K, when the source states it.
        oxidiser_phase / fuel_phase: When the source states them.
        exit_pressure: Pa, for an expansion case.
        area_ratio: Ae/At, for an expansion case.
        chemistry_mode: The source's chemistry assumption, as a free string
            because a historical source may not map onto this package's enums.
        observations: Reported values, keyed by quantity name, in SI. These are
            **source observations**, not computed fields -- which is why they
            live in a mapping rather than as typed attributes: giving them
            attribute names would make this record look like a result.
        observation_units: The unit each observation is stated in.
        source_precision: How many significant figures the source printed,
            which is what a later comparison derives its tolerance from.
        notes: Anything a later reader needs, such as a surrogate definition.
    """

    pair: PropellantPair
    source: str
    source_location: str = ""
    oxidiser_fuel_ratio: MixtureRatio | None = None
    chamber_pressure: float | None = None
    oxidiser_temperature: float | None = None
    fuel_temperature: float | None = None
    oxidiser_phase: Phase | None = None
    fuel_phase: Phase | None = None
    exit_pressure: float | None = None
    area_ratio: float | None = None
    chemistry_mode: str = ""
    observations: Mapping[str, float] = field(default_factory=dict)
    observation_units: Mapping[str, str] = field(default_factory=dict)
    source_precision: int | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.pair, PropellantPair):
            raise PropellantError(
                f"pair must be a PropellantPair, got {type(self.pair).__name__}")
        if not isinstance(self.source, str) or not self.source.strip():
            raise PropellantError(
                "a reference case must name its source; an unattributed published "
                "value is the hardest kind of error to find later")
        for name, value in (("chamber_pressure", self.chamber_pressure),
                            ("oxidiser_temperature", self.oxidiser_temperature),
                            ("fuel_temperature", self.fuel_temperature),
                            ("exit_pressure", self.exit_pressure),
                            ("area_ratio", self.area_ratio)):
            if value is not None:
                number = _finite(value, name)
                if number <= 0.0:
                    raise PropellantError(f"{name} must be above zero, got {number!r}")
        if self.oxidiser_fuel_ratio is not None and not isinstance(
                self.oxidiser_fuel_ratio, MixtureRatio):
            raise PropellantError(
                "oxidiser_fuel_ratio must be a MixtureRatio or None")
        if not isinstance(self.observations, Mapping):
            raise PropellantError("observations must be a mapping")
        if not isinstance(self.observation_units, Mapping):
            raise PropellantError("observation_units must be a mapping")
        for key, value in self.observations.items():
            if not isinstance(key, str) or not key:
                raise PropellantError(f"observation key must be a string, got {key!r}")
            _finite(value, f"observation {key!r}")
            if key not in self.observation_units:
                raise PropellantError(
                    f"observation {key!r} has no stated unit; a published number "
                    "without its unit is not a usable reference")
        if self.source_precision is not None:
            if not isinstance(self.source_precision, int) or self.source_precision < 1:
                raise PropellantError(
                    f"source_precision must be a positive integer number of "
                    f"significant figures, got {self.source_precision!r}")

    @property
    def observed(self) -> Mapping[str, float]:
        """Read-only view of the reported values."""
        return MappingProxyType(dict(self.observations))

    def unit_of(self, quantity: str) -> str:
        """The unit a reported quantity is stated in."""
        try:
            return self.observation_units[quantity]
        except KeyError:
            raise PropellantError(
                f"no unit recorded for observation {quantity!r}") from None
